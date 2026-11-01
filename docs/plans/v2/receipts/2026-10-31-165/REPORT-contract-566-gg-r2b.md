# REPORT-contract-566-gg-r2b — #566 contract amendment (tdd-light Phase 1, #165 wave)

## SUMMARY (2026-10-31; contract edits uncommitted on top of `eba0a46`)
brief-base v25 read · brief project v7 read
- **State:** done. All brief steps run; nothing NOT TRIED except a second self-built mutant (refused, role boundary).
- **Deviations:** none. (S1 handled the stronger way: measured, then turned into a live oracle pin. See §1.)
- **Pins → wrong build:** 3 NESTED rows in `_CONFTESTS_PYTEST_LOADS` (C2) · `test_the_load_tables_are_what_pytest_itself_loads` (S1, re-measures pytest every run) · `TestTheCollectorKeyAgreesWithTheExecutionVerdict` ×14 (C3 sharing). Audit wrong build M2 "drop the under leg" (it passed all 329 pins at `eba0a46`) now dies on 6 pins.
- **Declared vs observed (M2, scratch):** 6 declared from `--collect-only` = 6 observed, both directions, `mutation_proof` exit 0, PROOF HELD; `6 failed, 341 passed`; restored md5 `d0566de4…` = real tree.
- **Build leg:** `347 passed in 38.14s`, EXIT=0, against committed `scripts/gated_ground.py` (md5 `d0566de4…`).
- **Provenance:** scratch `loremaster.__file__ = /var/tmp/claude-1000/gg566r2b-scratch/loremaster/loremaster/__init__.py`; `scratch_copy.sh` EXIT=0.
- **Gates:** ruff on the file clean · currency `--legs typecheck,ruff`: typecheck RED_ADJUDICATED (83, owned by packet-58 / packet-64b-i contracts), ruff GREEN, **0 RED_ORPHANED**, 0 mypy lines on the file (pytest NOT_RUN is the `--legs` subset, #565).
- **Packages considered:** none. No mechanism specified (the oracle runs the installed pytest itself).
- **Odoo-20 portability:** n/a. No Odoo seam touched.
- **Reuse ledger:** 1 new test-side helper `_conftest_chain_repository` (the fixture body made reusable, no copy) + 3 constants. All in-file, all dispositioned.
- **Graded:** n/a. This is an author report; the only verdict is on my own pins (`eba0a46` is HEAD at report).
- **Decisions needed:** none open. F1 ruled keep; F2 ruled option (a) and pinned in §7 (4 pins RED at the committed build, by design, for the C3 builder).
- **Pointers:** changes §1 · oracle (verbatim) §2 · receipts §3 · forks §4 · pre-flight §5 · realism §6.

## Routing table (written before the first sweep, per brief-base §3)
| step | tier | who | reason |
|---|---|---|---|
| extended pytest oracle (S1 + nested cases) | 1 | inline | ~20-line probe I wrote. It is on the critical path (its result decides the pin rows) and I read its whole output; a Haiku spawn would cost more than the run |
| scratch copy `scratch_copy.sh` | 1 | inline, background | one command; the provenance assertion is in the tool |
| contract design / pin text | 3 | me | contract authorship (never Haiku; lore pins authors to Opus) |
| build-leg run of the file | 1 | haiku-runner | test run |
| mutation proof in scratch | 1 | haiku-runner | test run; I keep the verdict (declared vs observed) and read the log myself |
| ruff + currency `--legs typecheck,ruff` | 1 | haiku-runner (currency); inline (one-file ruff, ~1 s, read whole) | gate run; I read the verdicts |
Fan-out: haiku 3 · sonnet 0 · peak 3. I checked each runner's `RAN:` line against my command and re-read every log's head, count and EXIT lines myself.

## 1. What changed (`scripts/test_gated_ground.py`, section 11b; uncommitted on top of `eba0a46`)
- **C2 (nested pins).** `_CONFTESTS_PYTEST_LOADS` gains three NESTED rows, each reachable ONLY by
  the "under a testpath" leg:
  `loremaster/tests/store/conftest.py` (one level in the first testpath),
  `loremaster/tests/store/lease/conftest.py` (two levels: kills "immediate subdirectory only" /
  `parent.parent == testpath` builds), `skills/lore-deploy/tests/unit/conftest.py` (inside the
  SECOND testpath: kills "under leg on the first entry only"). Each nested directory carries a test
  module (`_CONFTEST_CHAIN_NESTED_TEST_MODULES`) so it is a live collection target, as in the real
  tree. A comment on the `loremaster/tests/conftest.py` row says why the testpath-ROOT conftest
  cannot discriminate (both legs cover it; `is_under` is reflexive). The ANCESTOR leg was already
  load-bearing (the root, `loremaster/`, `skills/`, `skills/lore-deploy/` rows: no under leg
  reaches them), so each leg now has rows only it covers.
- **S1 (comment over-claim) — MEASURED, then the claim kept and made self-maintaining.** I re-ran
  the oracle with the three never-placed negatives (`lore/`, `skills/lore/`, `skills/otherskill/`)
  plus the nested placements (§2): all six negatives are measured unloaded, all nested placements
  loaded. Then, rather than another once-recorded claim, the oracle became a pin:
  `TestAConftestIsCoveredWherePytestLoadsIt::test_the_load_tables_are_what_pytest_itself_loads`
  builds every row of both tables with a self-recording conftest, runs the installed pytest
  (`sys.executable -m pytest --collect-only`, `PYTEST_*` env stripped), asserts a positive control
  (every chain directory's test module was collected), then asserts loaded == the LOADS table
  exactly. The table comment now says "measured on every run" and names that test. This is a
  measurement of the dependency (pytest), the same shape as the file's existing
  `test_the_declared_default_matches_what_pytest_itself_declares`; it is not a source scanner or
  meta-suite.
- **C3 (sharing pin).** New class `TestTheCollectorKeyAgreesWithTheExecutionVerdict`, one case per
  row of BOTH tables (14): in a repository tracking no conftest, an UNTRACKED silencer conftest is
  written at the placement and the memo fingerprint (`_collector_input_fingerprint`) is compared;
  then the file is given the ordinary body, staged, and classified. Asserts
  `(key moved, verdict COVERED) == (pytest loads it, pytest loads it)`. Behaviour, not spelling: it
  never inspects how `_collector_input_paths` assembles its set, only whether the key the memo uses
  moves, and the fate the verdict serves. Refactor: the fixture body became
  `_conftest_chain_repository(tmp_path, *, tracked_conftests=...)`; `conftest_chain_repository`
  calls it with every placement (unchanged behaviour for the existing pins).

## 2. The oracle (instrument, verbatim per brief-base §1; first run 2026-10-31, pytest 9.0.3, HEAD `eba0a46`)
```bash
#!/usr/bin/env bash
# Oracle for #566 r2b: which conftest.py files does pytest LOAD for testpaths
# ["loremaster/tests", "skills/lore-deploy/tests"]? Each conftest appends its own
# repo-relative path to $LOADED on import. Extends the #566 oracle with the three
# negatives it never placed (lore/, skills/lore/, skills/otherskill/) and NESTED
# placements inside each testpath. usage: oracle566r2b.sh <python> <throwaway-root>
set -euo pipefail
PY="$1"; ROOT="$2"; rm -rf "$ROOT"; mkdir -p "$ROOT"; cd "$ROOT"
cat > pyproject.toml <<'T'
[tool.pytest.ini_options]
testpaths = ["loremaster/tests", "skills/lore-deploy/tests"]
T
for d in . loremaster loremaster/tests loremaster/tests/store loremaster/tests/store/lease \
         loremaster/tests/conftest_only loremaster/tests/build loremaster/tests/.hidden \
         loremaster/tes lore skills skills/lore skills/otherskill skills/lore-deploy \
         skills/lore-deploy/tests skills/lore-deploy/tests/unit skills-old docs/consult tools tools/probes; do
  mkdir -p "$d"
  printf 'import os, pathlib\nwith open(os.environ["LOADED"], "a") as f: f.write(str(pathlib.Path(__file__).resolve().relative_to(pathlib.Path(os.environ["ROOT"]).resolve())) + "\\n")\n' > "$d/conftest.py"
done
printf 'def test_a():\n    assert True\n' > loremaster/tests/test_a.py
printf 'def test_s():\n    assert True\n' > loremaster/tests/store/test_s.py
printf 'def test_l():\n    assert True\n' > loremaster/tests/store/lease/test_l.py
printf 'def test_bd():\n    assert True\n' > loremaster/tests/build/test_bd.py
printf 'def test_b():\n    assert True\n' > skills/lore-deploy/tests/test_b.py
printf 'def test_u():\n    assert True\n' > skills/lore-deploy/tests/unit/test_u.py
printf 'def test_c():\n    assert True\n' > skills-old/test_c.py
printf 'def test_o():\n    assert True\n' > skills/otherskill/test_o.py
printf 'def test_l2():\n    assert True\n' > lore/test_l2.py
export LOADED="$ROOT/loaded.txt" ROOT; : > "$LOADED"
"$PY" -m pytest --collect-only -q -p no:cacheprovider > collect.log 2>&1; echo "PYTEST_EXIT=$?"
"$PY" -m pytest --version
echo "--- loaded:"; sort -u "$LOADED"
echo "--- NOT loaded:"; find . -name conftest.py | sed 's|^\./||' | sort | comm -23 - <(sort -u "$LOADED")
echo "--- collected:"; grep '::' collect.log
```
Output (PYTEST_EXIT=0, pytest 9.0.3):
- **loaded:** `conftest.py`, `loremaster/conftest.py`, `loremaster/tests/conftest.py`,
  `loremaster/tests/store/conftest.py`, `loremaster/tests/store/lease/conftest.py`,
  `loremaster/tests/conftest_only/conftest.py` (no test module beside it, still loaded),
  `skills/conftest.py`, `skills/lore-deploy/conftest.py`, `skills/lore-deploy/tests/conftest.py`,
  `skills/lore-deploy/tests/unit/conftest.py`.
- **NOT loaded:** `lore/`, `skills/lore/`, `skills/otherskill/` (the three S1 never measured),
  `loremaster/tes/`, `skills-old/`, `docs/consult/`, `tools/`, `tools/probes/`, and
  **`loremaster/tests/build/`, `loremaster/tests/.hidden/`** (pytest's default `norecursedirs`) —
  see F2.
- Collected: only the five modules under the testpaths (none from `lore/`, `skills/otherskill/`,
  `skills-old/`, `build/`).
The same measurement now runs inside the suite on every gate run (§1, S1).

## 3. Gate receipts
| gate | exact command | log | EXIT | count | TREE |
|---|---|---|---|---|---|
| build leg | `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q scripts/test_gated_ground.py -n 8 --timeout=300 -p no:cacheprovider -rfE` (repo root) | `/var/tmp/claude-1000/gg566r2b-build.log` | 0 | `347 passed in 38.14s` | `b90f3fad…7ba6` |
| M2 mutation proof | `/var/tmp/claude-1000/gg566r2b-mutation.sh` (verbatim below; `mutation_proof.py --file scripts/gated_ground.py --anchor 'is_under(path, testpath) or is_under(testpath, directory)' --replacement 'is_under(testpath, directory)'` + 6 `--expect-red`) | `/var/tmp/claude-1000/gg566r2b-mutation.log` | 0 (PROOF HELD) | `6 failed, 341 passed in 55.35s` | scratch `ec336eb7…12aa` |
| currency typecheck,ruff | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | `/var/tmp/claude-1000/gg566r2b-currency.log` | 1 (the unrun-pytest-leg FAIL, #565; I read the verdicts) | typecheck RED_ADJUDICATED 83 · ruff GREEN · RED_ORPHANED 0 | `b90f3fad…7ba6` |
| ruff (file) | `uv run ruff check scripts/test_gated_ground.py` | `/var/tmp/claude-1000/gg566r2b-ruff.log` | 0 | `All checks passed!` | (run before the citation sed; the currency ruff leg covers the final content) |
- **`TREE=` bound:** `tree_id.sh` hashes the content of dirty files, so it includes this untracked report. I re-measured `TREE=b90f3fad…` after the build run, and it was unchanged then. This report's final rewrite moves it, though `scripts/test_gated_ground.py` is unchanged since both runs. An auditor should compare the test file's content, or re-measure with the reports archived.
- **Declared set:** taken from `.venv/bin/python -m pytest --collect-only -q scripts/test_gated_ground.py` in the scratch root (ids relative to that cwd, #560) BEFORE the run, into `/var/tmp/claude-1000/gg566r2b-declared.txt`: the 3 nested ids of `test_a_conftest_pytest_loads_is_execution_covered` + the 3 nested ids of `test_the_memo_key_and_the_verdict_give_one_answer_per_placement`. (The log's `declared=12/2` line is 12 argv words = 6 ids.)
- **Runs used:** 3 pytest runs (build leg; M2; the live oracle runs inside both) + 1 collect-only + 1 currency. No RED-at-HEAD run: this amendment adds pins the committed build already satisfies (that is C2's point). The M2 run is the discrimination receipt the brief asked for.
- Driver, verbatim:
```bash
#!/usr/bin/env bash
# #566 r2b mutation proof: the Phase 5 audit's wrong build M2 ("drop the under leg").
set -uo pipefail
SCRATCH=/var/tmp/claude-1000/gg566r2b-scratch
cd "$SCRATCH"
export LORE_PYTHON="$SCRATCH/.venv/bin/python"
~/.claude/orchestration/tree_id.sh "$SCRATCH"
"$LORE_PYTHON" -c "import loremaster; print('loremaster.__file__ =', loremaster.__file__)"
expect=()
while IFS= read -r id; do expect+=(--expect-red "$id"); done < /var/tmp/claude-1000/gg566r2b-declared.txt
echo "declared=${#expect[@]}/2 ids"
"$LORE_PYTHON" scripts/mutation_proof.py --file scripts/gated_ground.py \
  --anchor 'is_under(path, testpath) or is_under(testpath, directory)' \
  --replacement 'is_under(testpath, directory)' \
  "${expect[@]}" \
  -- systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 \
     "$LORE_PYTHON" -m pytest -q scripts/test_gated_ground.py -n 8 --timeout=300 -p no:cacheprovider -rfE
echo "EXIT=$?"
md5sum "$SCRATCH/scripts/gated_ground.py" /home/ejprice/PycharmProjects/lore/scripts/gated_ground.py
```
- **Role boundary:** I built no wrong implementation of my own. M2 is the audit's mutant, run because the brief asked for it. So the C3 pin's key leg is **NOT TRIED** against a wrong build. A mutant that drops the chain loop from `_collector_input_paths` would test it (prediction: the agreement pins for `loremaster/`, `skills/` and `skills/lore-deploy/` go red, plus the existing `test_an_untracked_conftest_in_an_ANCESTOR_of_a_collection_root_moves_the_key`). That run belongs to the adversary/audit.

## 4. Forks and flags
- **F1 — C3 pin, the converse direction (decision for lead-165).** The pin asserts agreement BOTH ways, as the brief asked: a loaded conftest moves the key, AND a non-loaded one does NOT move it. Only the first direction protects trust, because a key blind to a loaded silencer serves a stale healthy verdict. The second is about precision: an over-broad key only costs a cache miss. A safe, simpler C3 build, e.g. hashing every `conftest.py` in the tree, would fail the converse leg. **Recommendation:** keep it. Its job is to stop the merged predicate and the key from drifting apart, and the current build satisfies it. If the C3 builder picks the over-broad design, relax the pin to one direction and do not keep the predicate merge. **Surface:** the pin calls `gg._collector_input_fingerprint`, which is private but already contracted (the existing memo pins call it and `_collector_input_paths`). It observes the key's behaviour, not how the address set is built. So it is not a spelling test. A builder who renames the fingerprint function breaks the existing pins as well.
- **F2 — finding #569 (new, filed): a norecursedirs false clear.** Measured in §2: pytest does NOT load `loremaster/tests/build/conftest.py` or `loremaster/tests/.hidden/conftest.py`, yet the "under" leg calls a TRACKED one there execution-COVERED. Test modules are unaffected, because the collector measures them. Likelihood is low. The rule's docstring ("pytest loads it") over-claims. I did not pin it: a red pin would force a production change this round does not own. **Options:** (a) the C3 builder folds pytest's `norecursedirs` (default plus ini) into the one merged predicate, and a `build/` row goes into `_CONFTESTS_PYTEST_DOES_NOT_LOAD`; the live oracle pin then re-measures it on every run. (b) Ledger it as a named bound in the `conftest-collection-hooks` text. Recommendation: (a), because it is cheap while the predicate is being merged anyway.
- **Noticed:** a conftest in a nested directory with NO test module (`loremaster/tests/conftest_only/`) is still loaded by pytest 9.0.3. The rule agrees. Not pinned as its own row: the tree holds no such shape.

## 5. Adversarial pre-flight → coverage
| break | covered by |
|---|---|
| drop the under leg (M2) | 3 nested LOADS rows + 3 agreement rows (proof held) |
| under leg only one level deep / `parent.parent` | `loremaster/tests/store/lease/conftest.py` rows |
| under leg applied to the first testpath only | `skills/lore-deploy/tests/unit/conftest.py` rows |
| drop the ancestor leg | existing root / `loremaster/` / `skills/` / `skills/lore-deploy/` rows |
| string-prefix ancestry, cousin, sibling-prefix, typecheck-root ancestry | existing DOES_NOT_LOAD rows, now all measured (§2) |
| the tables drift from pytest (S1 class) | `test_the_load_tables_are_what_pytest_itself_loads`, every run, with a collected-set positive control |
| C3 merge changes the verdict or the key alone | agreement pin ×14 |
| oracle passes for a fixture reason (a directory not collected) | the positive control asserts all 5 test modules were collected |
| inherited `PYTEST_ADDOPTS` / `-n` reaching the oracle subprocess | the env is stripped of `PYTEST_*` |
| norecursedirs directories | **not pinned → F2 / #569** |

## 6. Realism and independence
- ☑ Production-realistic inputs: the placements mirror the real tree's shape (`loremaster/tests`, `skills/lore-deploy/tests`, nested store/lease dirs). Nothing is read from a live DB.
- ☑ Independent expected values: they come from the installed pytest's own behaviour, measured in-test and in §2, never from `_pytest_loads_conftest`.
- ☑ Seam coverage: the agreement pin crosses the verdict↔memo-key seam on every row, with the real fingerprint.
- ☐ Magnitude bound: not applicable; the outputs are enum fates and booleans.
- ☑ Shared conventions: `gg.pytest_testpaths` / `gg.tracked_python_files` feed the fingerprint, the same readers production uses.
- ☐ Hostile rendered text: not applicable; the change renders nothing new.
- ☑ Input accounting: every tracked file's fate is checked by the existing `assert_every_tracked_file_is_accounted_for` in each new case.

## 7. Round 2 — #569 pinned (lead ruling 2026-10-31: F1 keep the converse leg; F2 option (a))
**State: done.** Two rows were added to `_CONFTESTS_PYTEST_DOES_NOT_LOAD`, and both are TRACKED in `conftest_chain_repository`:
`("loremaster/tests/build/conftest.py", "under a testpath, in a default `norecursedirs` dir")` and
`("loremaster/tests/.hidden/conftest.py", "under a testpath, in a hidden (`.*`) directory")`. They
flow automatically into `_EVERY_CONFTEST_PLACEMENT`, so each gets three pins: the verdict pin, the C3 agreement pin, and the live oracle.
- **The live oracle re-measures them: yes.** `test_the_load_tables_are_what_pytest_itself_loads`
  plants every row of BOTH tables, these two included, and asserts loaded == the LOADS table. It
  PASSES at HEAD, so the installed pytest 9.0.3 does not load either file (it would go red if pytest did).
  The same set is loaded under the repo's `--import-mode=importlib` addopts (probe:
  `/var/tmp/claude-1000/gg566r2b-oracle-importlib.sh`, the §2 oracle with that one line added).
- **New node ids (declared from `--collect-only` before the run, into `/var/tmp/claude-1000/gg566r2b-declared-569.txt`):**
  - `scripts/test_gated_ground.py::TestAConftestIsCoveredWherePytestLoadsIt::test_a_conftest_pytest_never_loads_stays_execution_ungated[loremaster/tests/build/conftest.py]`
  - `scripts/test_gated_ground.py::TestAConftestIsCoveredWherePytestLoadsIt::test_a_conftest_pytest_never_loads_stays_execution_ungated[loremaster/tests/.hidden/conftest.py]`
  - `scripts/test_gated_ground.py::TestTheCollectorKeyAgreesWithTheExecutionVerdict::test_the_memo_key_and_the_verdict_give_one_answer_per_placement[loremaster/tests/build/conftest.py]`
  - `scripts/test_gated_ground.py::TestTheCollectorKeyAgreesWithTheExecutionVerdict::test_the_memo_key_and_the_verdict_give_one_answer_per_placement[loremaster/tests/.hidden/conftest.py]`
  - plus one more parametrized run of the existing oracle pin, which covers the two placements (green).
- **RED at the committed `gated_ground.py` (md5 `d0566de445b3c7aed9f5408b1772949c`), behavioural:** `4 failed, 347 passed in 51.39s`,
  EXIT=1. The observed FAILED set is exactly the 4 declared ids. The assertions:
  - verdict pins: `assert <Fate.COVERED> is <Fate.UNGATED>`;
  - agreement pins: `assert (True, True) == (False, False)`, i.e. the key moved AND the verdict covered a file pytest never loads.

  The other 347 pass, the original 345 plus the oracle and the types-axis pin.
  Ruff clean (RUFF_EXIT=0). Log `/var/tmp/claude-1000/gg566r2b-red569b.log`, head `TREE=7f8f8bb3…4661`.
  **Content receipt:** `scripts/test_gated_ground.py` md5 `6f55815ee33cc565c7dc0f80df4c02b2`, unchanged since that run.
  `TREE=` has moved since the run (`074d962b…`) only because other dirty files in the shared tree
  changed; my writable file did not.
- **Runs used this round:** 2. The first RED run (`gg566r2b-red569.log`: the same 4 failed and 347 passed)
  exposed my own wording defect. For the new rows, the never-loads failure message said "on no testpath's
  chain", but these rows ARE under a testpath, so the message claimed a reason the assertion was not checking.
  I reworded it to cite the oracle pin and `norecursedirs`, then re-ran (`…red569b.log`, the receipt above).
- **Earlier receipts (§3):** the build-leg (347 passed) and M2 (proof held) runs graded the file
  BEFORE these rows. Neither row touches the nested rows M2 kills.
- **Does the ini's own `norecursedirs` add directories the builder must honour?** Not in this
  repository today. `pyproject.toml` `[tool.pytest.ini_options]` sets no `norecursedirs`
  (grep; there is no `pytest.ini`, `tox.ini`, `setup.cfg` or `.pytest.ini` at the root). So pytest's default list is in
  force: `*.egg .* _darcs build CVS dist node_modules venv {arch}` (read from
  `_pytest.main.pytest_addoption`, pytest 9.0.3). **What the builder must honour anyway, measured:**
  1. **An ini value REPLACES the defaults; it does not add to them.** With `norecursedirs = ["store"]`, pytest loaded
     `build/` and `.hidden/` again and stopped loading `store/` (probe
     `/var/tmp/claude-1000/gg566r2b-oracle-nrd.sh`). So the predicate reads the ini, falls back to the
     defaults, and never takes the union of the two.
  2. **Pruning covers the subtree:** `store/lease/conftest.py` was not loaded either. Every directory
     component between the testpath and the conftest is tested against the patterns.
  3. Other directory skips in `_pytest.main.pytest_ignore_collect` (read, pytest 9.0.3) that the predicate
     will meet: `__pycache__`, and virtualenv directories (`_in_venv`, unless `--collect-in-virtualenv`).
     `collect_ignore` / `collect_ignore_glob` / `--ignore` remain the stated `conftest-collection-hooks` bound.
     None of these is pinned (no row was asked for). Venv and `__pycache__` conftests are planted-data edges.
  4. **Consequence of the F1 ruling, for the builder:** the agreement pin's converse leg now requires
     the memo key NOT to move for these two conftests. Today `_collector_input_paths` walks every
     `.py` under a testpath, so the merged predicate has to filter the conftests in that walk too. Non-conftest
     `.py` files in a pruned directory are not pinned either way, and an untracked helper there can still
     be imported by a collected test, so keeping them in the key is the safe choice.
- **⚠ Adjudication needed (outside my writable set):** the 4 reds are intentional; they are waiting for the C3 builder.
  They need an owner entry in `scripts/pending_contracts.yaml` (owner: the C3 merge builder; trigger: #569
  folded into the merged conftest predicate). Otherwise the packet's close-out currency run reads them as
  RED_ORPHANED. The `--legs typecheck,ruff` currency run cannot see pytest reds, so its 0 RED_ORPHANED says nothing about them.
