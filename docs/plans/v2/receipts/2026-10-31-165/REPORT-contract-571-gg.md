brief-base v25 read

BRIEF CONFLICT: the brief's "Discrimination" clause (apply the audit's W2 mutant via `mutation_proof.py` and diff declared vs observed) is a wrong build that a grader wrote, replayed by the contract author to confirm it now dies. brief-base §2 ROLE BOUNDARY forbids that transfer, and the brief quotes no operator grant. **I saw the conflict only after the run had finished, so I did NOT refuse it.** The receipt below is real, but it is the author grading its own pins. Treat it as a self-check, not a grade. W3, W4 and W5 were not built, per the same clause. An independent re-grade of this contract (adversary or cold audit) is still owed.

# REPORT-contract-571-gg: tdd-light Phase 1 amendment for #571 + #570 (#165 wave)

## SUMMARY
- **State: DONE.** The new pins are in `scripts/test_gated_ground.py` (md5 `c312b0fca19c6a506f48f92c9979a295`, measured 2026-10-31 against `scripts/gated_ground.py` at `5da0891`, md5 `329f3be4…`, unmodified). That file is my only repo edit.
- **Build leg, against the committed module:** **365 passed, 0 failed** in 34.97s, EXIT 0. The same file at `5da0891` collects 352 tests, so this adds 13 new node ids. Log: `/var/tmp/claude-1000/gg571-build.log`.
- **Which pin kills which wrong build:**
  - **W2** (leaf-only pruning, the audit's mutant): **killed, run.** 4 reds, and they are exactly the declared set.
  - **First-component-only pruning:** killed by the `store/dist` row. Reasoned, not run.
  - **W3** (ini ∪ defaults): killed by the `[store]` case, because `build/` and `.hidden/` would stay UNGATED. Reasoned, not run.
  - **W4** (ignore the ini): killed by the `[store]` case, because `store/` would stay COVERED and `build/` UNGATED. Reasoned, not run.
  - **W5** (also prune the testpath's own components): killed by the `[tests]` case, because everything under both testpaths would read UNGATED. Reasoned, not run.
  - **Closing #570:** the `test_the_guard_still_reads_it_covered[collect_ignore|virtualenv]` pins would go red with the KNOWN BOUND message. Reasoned.
- **Mutation W2 (see the BRIEF CONFLICT above), declared vs observed:**
  - I declared 4 ids from `--collect-only` BEFORE the run, in `/var/tmp/claude-1000/gg571-declared-w2.txt`.
  - Observed: `4 failed, 361 passed`, and `PROOF HELD — the declared RED set fired EXACTLY`.
  - Nothing was declared that stayed green, and nothing went red that was not declared. `mutation LANDED (anchor matched exactly once)`. The tree was restored byte-exact (md5 `329f3be4…`).
  - Log: `/var/tmp/claude-1000/gg571-mutation.log`. Runner: `/var/tmp/claude-1000/gg571-mutation.sh`.
- **Provenance:** `loremaster.__file__=/var/tmp/claude-1000/gg571-scratch/loremaster/loremaster/__init__.py`. `scratch_copy.sh` gave EXIT 0, and `--verify-only` gave 0 before the run. Before the run, the scratch and original `gated_ground.py`/`test_gated_ground.py` md5s were identical. Scratch `TREE=fdd9f81c…382b`, `HEAD=5da0891`.
- **Gates:**
  - ruff on the file: `All checks passed!`, EXIT 0.
  - `--currency --legs typecheck,ruff`: ruff GREEN. typecheck is RED_ORPHANED with 2 residuals, **neither of which is in my file**; see Outside this change.
- **No build defect found:** no new pin fails on the committed module.
- **Fan-out:** haiku 3 · sonnet 0 · peak 2. Every runner's `RAN:` line matched my command, and I re-read every count line from its log myself.
- **Durable addresses:** `lore_comms` registered as contract-571-gg (session fix-165-2026-10-31). `brief project v7 read`. No tool calls were DENIED.

## Routing table (written before first read beyond brief + base)
| step | tier | who | reason |
|---|---|---|---|
| read audit c3 / contract r2b §2,§7 / module rule / existing #569 pins | 3 | self | contract design input; ~4 targeted reads, I read all output |
| pytest-semantics probes (subtree, ini-replaces, collect_ignore, venv) | 3 | self | probe design + control is judgment; output tiny, on critical path |
| write pins | 3 | self | contract authorship (never Haiku) |
| collect-only for declared ids | 1 | self inline | one command, <20 lines, on critical path, read whole |
| build-leg pytest run + ruff | 1 | haiku-runner | test run |
| W2 mutation run (scratch) | 1 | haiku-runner | test run; verdict stays with me |

What actually ran:
- No separate probe step: the probes became the in-suite live oracle, so pytest itself measures every expectation on every run.
- ruff ran inline, because it was a quick check on my own file.
- A third haiku-runner ran the currency legs.

## The pins (all in `scripts/test_gated_ground.py`)
1. **#571, subtree pruning.** Two rows were added to `_CONFTESTS_PYTEST_DOES_NOT_LOAD`. Each one automatically gets the verdict pin, the memo-key agreement pin, and a place in the live oracle `test_the_load_tables_are_what_pytest_itself_loads`.
   - `loremaster/tests/build/sub/conftest.py`: the leaf `sub` matches nothing, and its parent `build` is pruned. This row kills W2.
   - `loremaster/tests/store/dist/conftest.py`: a pruned dir nested below a loaded one. This row kills "test only the first component below the testpath".
   - The oracle passed with both rows planted, so pytest 9.0.3 measurably loads neither (2026-10-31).
2. **#571, configured `norecursedirs`.** New class `TestAConfiguredNorecursedirsReplacesTheDefaults`, parametrized over `_CONFIGURED_NORECURSEDIRS_CASES`:
   - `[store]`: as measured, `build/`, `build/sub/` and `.hidden/` are COVERED again, and `store/`, `store/lease/` and `store/dist/` are UNGATED.
   - `[tests]`: the pattern equals each testpath's own last component, and nothing under either testpath is pruned.

   Each case has three pins:
   - `test_pytest_loads_what_the_case_table_says`: the live oracle, now able to take an ini value, so **the expectation is measured, not asserted**;
   - `test_the_execution_verdict_follows_the_configured_list`: every placement, in one tracked repo;
   - `test_the_memo_key_follows_the_configured_list`: every placement, as an untracked silencer.

   The expected set is derived in one place, `_expected_loads_under_configured_norecursedirs`, from the default LOADS table minus `_PLACEMENTS_UNDER_A_TESTPATH`.
3. **#570, pinned miss.** New class `TestAConftestPytestSkipsByIgnoreOrVirtualenvIsAKnownBound`:
   - `test_pytest_does_not_load_either_conftest`: the live oracle shows pytest does NOT load `loremaster/tests/vendored/conftest.py` (the parent conftest sets `collect_ignore = ["vendored"]`) or `loremaster/tests/fixture_env/conftest.py` (its dir holds `pyvenv.cfg`).
     - Positive control: the parent conftest itself loaded.
     - The pin goes red if pytest's skip rules change, in which case the "miss" is no longer a miss.
   - `test_the_guard_still_reads_it_covered[collect_ignore|virtualenv]`: asserts the guard reads both as COVERED. If not, it fails with "this is a KNOWN BOUND (#570) — if you closed it deliberately, delete this pin and say so."
   - The class docstring names the re-open trigger: a tracked conftest appears under an ignored or virtualenv directory (or the operator rules to close the venv leg).
4. **Refactor, no behaviour change:**
   - The oracle body was extracted into `_pytest_loaded_conftests(work_dir, *, norecursedirs, conftests, conftest_appendix, plain_files)`, so there is one oracle and not three copies. The existing oracle pin now calls it.
   - `_conftest_chain_repository` gained a **required** `pytest_ini_extra`. It has no default, because the guard branches on it (CLAUDE.md fixture-default law), and both existing call sites now pass `None` explicitly.

## Package line
No mechanism is specified. The oracle is pytest itself, run in a subprocess, and everything else is stdlib. Odoo-20 portability: n/a, no Odoo seam is touched.

## Adversarial pre-flight → coverage
- Pruned component is not the leaf → `build/sub` row.
- Pruned component is not the first below the testpath → `store/dist` row.
- A configured list is unioned with the defaults → `[store]` case. `build` and `.hidden` must be COVERED.
- A configured list is ignored → `[store]` case.
- A pattern matching a testpath's own component → `[tests]` case.
- The verdict and the memo key disagree under a configured list → per-case memo pin.
- pytest semantics drift (pytest starts loading, or stops) → every expectation goes through the live oracle, never a recorded table alone.
- `collect_ignore` and venv skips → #570 pins (the bound, plus proof that the bound is real).
- `--ignore`/`--ignore-glob`, `__pycache__`, `conda-meta/history` venvs: **scoped out without an operator ruling, so this is a question.** They are the same bound class as #570 and the brief named only two shapes. Do you want rows for them?
- Symlinked dirs (audit F6): scoped out. It is LOW and unmeasured, and the brief did not ask for it.

## Realism clauses
- ☑ **Production-realistic inputs.** The paths are the repo's own testpath shapes, and the pattern values (`build`, `dist`, `.*`) come from pytest's real default list. `store` is a real subdirectory name in this repo's tests.
- ☑ **Independent expected values.** Every expectation is measured live from the installed pytest. None is derived from `gated_ground.py`.
- ☑ **Seam coverage.** The ini is written to `pyproject.toml` and read back by the guard's own reader, the seam where #571 lives. Both consumers of the rule (verdict and key) are pinned.
- ☐ **Magnitude bounds:** not applicable, because the outputs are enum fates and booleans, with no derived numeric output.
- ☑ **Shared conventions.** Testpaths come from `_CONFTEST_CHAIN_TESTPATHS`, and the default list stays pinned to pytest by the existing drift pin.
- ☐ **Hostile rendered text:** not applicable, because this change renders no stored free text.
- ☑ **Input accounting:** the existing `assert_every_tracked_file_is_accounted_for` helper runs in every new verdict pin.

## Runs used
1. Build leg at the committed module: 365 passed.
2. W2 mutation in scratch: 4 failed, 361 passed, PROOF HELD.

Plus one non-pytest currency-legs run (typecheck, ruff) and inline ruff. That makes 2 pytest runs.

## Outside this change (surfaced, not acted on)
- **typecheck RED_ORPHANED, 2 residuals, in a sibling's untracked file:**
  - `skills/lore-deploy/scripts/test_scaffold_slug.py:867` and `:886`: `Missing named argument "owner" for "_write_manifest" [call-arg]`.
  - These have no owner in `scripts/pending_contracts.yaml`, and they are not mine. They are probably the #568 slug contract's intended reds; the lead should adjudicate them or route them to that author.
- **The currency gate with `--legs typecheck,ruff` renders `pytest NOT_RUN` as an ORPHAN and prints `CURRENCY: FAIL`.**
  - CLAUDE.md describes `--legs typecheck,ruff` as a per-round run that should read RED_ORPHANED 0. Counting a deliberately skipped leg as an orphan means a per-round run can never pass.
  - Possible instrument defect; not filed. Should I file a `lore_findings` row?
- **Audit S2 is still open in my writable file.** The failure message of `test_the_conftest_bound_does_not_claim_a_mechanism_the_collector_catches` asserts "The collector catches every silencing mechanism". For conftests, #570 shows that is false.
  - The brief did not route it, so I left it. The fix is a one-line message edit. Do you want it in this file?
- **Scratch hygiene:** I left a stray `scripts/test_gated_ground_head_unused.py.txt` in `/var/tmp/claude-1000/gg571-scratch` (a `.txt` copy of the `5da0891` test file, which pytest does not collect). It was there during the mutation run, and it is harmless to that run. The scratch copy is left in place.
