brief-base v25 read · brief project v7 read

## SUMMARY
- **State:** done. **Verdict on `08acd90`: GO**, with 2 routed residuals and no NO-GO defect in the build.
- **Deviations:** none to the writable set. I made no edit to `gated_ground.py`: no nit qualified (§4).
  I ran the collect-only id derivation inline rather than through a runner (routing note at the end).
- **Packages considered:** none. No mechanism was specified, since I audited existing domain logic.
- **Odoo-20 portability:** n/a. No Odoo seam was touched.
- **Reuse ledger:** 0 new symbols from me. In the graded diff, `_pytest_loads_conftest` REUSES `is_under`
  correctly, but it DUPLICATES pytest's conftest-chain rule that `_collector_input_paths` already
  encodes (C3, routed; they agree today: 0/28 disagreements, §3b).
- **Graded:** `08acd90` · HEAD-at-report: `08acd90` · SAME
- **Findings:** C2 is a contract gap. **The wrong build "drop the under leg" passes all 329** (M2, §3a).
  It fails only on a conftest NESTED inside a testpath, which pytest loads (oracle-proved). → contract
  author: add a nested-conftest row to `_CONFTESTS_PYTEST_LOADS`. · C3 DRY → follow-up builder. ·
  S1: a test comment over-claims its oracle (3 negatives were never measured) → contract author.
  · C1: `is_under(tp, ".")` is true by design (`is_relative_to` with `.` ∈ parents; testpaths refuse `.`).
  · C4: no false docstring or stated-bound sentence.
- **Mutation:** M1 `startswith`: declared 6 = observed 6, PROOF HELD, restored byte-exact. M2: 0 reds,
  as predicted (the C2 survivor). Scratch `loremaster.__file__` =
  `/var/tmp/claude-1000/gg566-audit-scratch/loremaster/loremaster/__init__.py`.
- **Gates (TREE `33a61751…`, HEAD `08acd90`):** pytest 329 passed, EXIT=0 · mypy clean · ruff clean.
- **Decisions needed:** whether C2's missing pin and C3's de-duplication are taken in this packet or
  ledgered. That is the lead's or operator's call.
- **Pointers:** §1 (C1–C5), §2 (smells), §3/§3a (mutations), §3b (probe, pasted), Gate receipts.

## Routing table (written before the sweeps, per brief-base §3)
| step | tier | who | reason |
|---|---|---|---|
| cold review of `_pytest_loads_conftest` + contract (wrong-build search, `is_under` on `.`, docstring truth) | 3 | self | audit verdict: an error here seals itself |
| prior-art search (`lore_search`) + `git ls-files` conftest inventory + `conftest` prose grep in gated_ground.py | 1 | self, ONE parallel batch | 3 small lookups, output tiny, I read all of it |
| scratch copy (`scratch_copy.sh`) | 1 | self | single command on my critical path; its provenance assert is what I judge |
| `--collect-only` id derivation + mutation_proof.py runs | 1 | haiku-runner | test-run output; I declare ids and judge the diff |
| final gates (pytest file, mypy, ruff) | 1 | haiku-runner (pytest); self (mypy/ruff: two short commands, tiny output) | |

## 1. Cold review (written before any edit)
Graded commit `08acd90` (fix) on contract `ef56833`. Review written 2026-10-31 ~20:05Z, before any edit.

**C1 — `is_under(testpath, ".")` for the repository root: BY DESIGN, not by accident (HIGH).**
`is_under` is `PurePosixPath(path).is_relative_to(PurePosixPath(tree))`. A bare filename's
`PurePosixPath("conftest.py").parent` is `PurePosixPath(".")`, and in Python ≥3.12
`is_relative_to` is `other == self or other in self.parents`. `PurePosixPath(".")` is the last
element of every relative path's `.parents`. Probed on the repo venv (Python 3.14.7):
`is_under("loremaster/tests", ".")` is True, `is_under("a", ".")` is True,
`is_under("loremaster/tests", "lore")` is False, `str(PurePosixPath("./conftest.py").parent)` is `'.'`.
`is_under`'s docstring states the component-wise contract, and the new docstring names the root case
explicitly. What keeps it sound: `pytest_testpaths` refuses entries that widen to the whole tree
(empty, `.`, absolute, `..`; `_widens_to_whole_tree`), so `testpath` is always a normalised relative
path below the root. Bound (unchanged by this commit): it models pytest's `confcutdir` as the repo
root. That holds while `pyproject.toml` (the inifile) sits at the root, because pytest then defaults
confcutdir to the inifile's directory. It is not modelled if someone sets `--confcutdir`.

**C2 — WRONG BUILD THAT SURVIVES THE CONTRACT: drop the "under" leg (predicted; measured in §3).**
`is_under(path, testpath) or is_under(testpath, directory)` → `is_under(testpath, directory)`.
The contract's only conftest under a testpath is `loremaster/tests/conftest.py`, which sits AT the
testpath root, where `directory == testpath`. There, `is_relative_to` of an equal path is True, so
the ancestor leg alone covers it. Every other conftest fixture in the file
(`loremaster/tests/conftest.py` in the hook/import pins) has the same shape. The real tree's tracked
conftests are `conftest.py`, `loremaster/tests/conftest.py`, `lorescribe/tests/conftest.py` and
`loresigil/tests/conftest.py`, all at a testpath root or above one. So nothing in the contract or the
tree pins a conftest NESTED inside a testpath (`loremaster/tests/sub/conftest.py`), which pytest
loads when it recurses. The wrong build reports that file as execution-UNGATED: a false positive on
honest code, the #566 class itself. This is a contract gap → ROUTED to the contract author (a role
boundary: I do not write tests). Missing pin: add
`("loremaster/tests/store/conftest.py", "NESTED inside a testpath: only the under leg covers it")` to
`_CONFTESTS_PYTEST_LOADS`. It also needs an oracle leg, since the §2 oracle did not place a nested
conftest.

**C3 — DRY: pytest's conftest-loading rule is now encoded TWICE in `gated_ground.py` (MEDIUM, routed).**
`_collector_input_paths` builds "the conftest.py CHAIN from repo_root down to each collection root"
constructively (root conftest, plus `ancestor/conftest.py` for every prefix of each testpath, plus
every `.py` under it). `_pytest_loads_conftest` decides the same rule as a predicate. Today they agree
(probe in §3b). They are two places to be wrong if the model ever grows (confcutdir, an explicit-path
invocation, `rootdir` ≠ repo root). One owner would be a `_conftest_chain(testpaths)` both call. That
restructures the memo-key derivation, which has its own pins. That is beyond "quality nits only" in my
brief, so it is NOT fixed here. Recommendation: a follow-up builder, with the shared-chain mutation
proof (change the chain, and both the memo-key pins and the #566 pins must redden).
Prior-art search: `lore_search("is a path an ancestor of another path, component-wise…")` returned
only `test_no_raw_listener_in_test_trees.py::_under`, which is a test-side string-prefix helper, not an
owner. The `conftest` grep over `gated_ground.py` found `_collector_input_paths` (above). No other
owner. `is_under` is correctly REUSED on both legs.

**C4 — docstrings and stated bounds: no false sentence found.**
- `_pytest_loads_conftest` docstring: true. "the repository root included, whose parent `.` is an
  ancestor of every relative path" matches C1. Its ancestry is against the testpaths only, and
  `tools/conftest.py` pins that.
- `_execution_fate` docstring: true.
- Module docstring `conftest-collection-hooks`: the new sentence is true. The `StatedBound` row's
  `summary` is unchanged ("…bounded by registration."). The pin `bound.summary in gg.__doc__` still
  holds, and `gated_ground.py` itself renders no `.summary` (grep `\.summary`: 0 hits), so the
  registry row's lack of a #566 clause is not a served lie. Its `reopen_trigger` stays true.
- Module docstring `collector-memoisation` and the `_collector_input_paths` docstring still describe
  the chain correctly. This commit does not touch them.

**C5 — other wrong builds the contract KILLS (reasoned from the fixture tables; M1 measured in §3):**
string-prefix ancestry (`lore/conftest.py`, `skills/lore/conftest.py`, plus the root, because
`"x".startswith(".")` is False) · immediate-parent-only (`skills/conftest.py`, a grandparent) ·
first-testpath-only (the second-testpath rows) · ancestry against typecheck roots (`tools/conftest.py`)
· shared-top-component (`skills/otherskill/conftest.py`) · every-conftest-covered (all 6 negatives) ·
root-only special case (`loremaster/conftest.py`) · both-axes leak (the TYPES pin) · ancestor rule
applied to every test-shaped file (`test_an_ancestor_of_a_testpath_is_not_covered_by_it`).

## 2. Test-smell list (REPORTED, not patched)
- **S1 — comment over-claims its oracle (drift-prone).** The comment on `_CONFTESTS_PYTEST_LOADS`
  says the pytest 9.0.3 oracle "loaded exactly these and none of the negatives below". The oracle
  script pasted in the contract report places conftests at `. loremaster loremaster/tests
  loremaster/tes skills skills/lore-deploy skills/lore-deploy/tests skills-old docs/consult tools`.
  It placed none at `lore/`, `skills/lore/` or `skills/otherskill/`, three of the six negatives. Those
  three are reasoned, not measured. pytest semantics make them plainly unloaded, so the risk is
  wording, not behaviour. Fix: re-run the oracle with those three directories, or narrow the comment.
- **S2 — unrepresentative fixture on one axis (= C2):** every "under a testpath" conftest sits at the
  testpath ROOT, so the under leg is never independently exercised.
- **S3 — none found for tautology:** every new pin drives `assert_every_tracked_file_is_accounted_for`
  over a real `git init` fixture and checks the served fate, plus findings membership on the negative
  leg. No pin restates the implementation.

## 3. Mutations, declared BEFORE the run (ids from `--collect-only -q`, cwd = scratch root, 329 collected)
Scratch: `/var/tmp/claude-1000/gg566-audit-scratch` (`scratch_copy.sh` EXIT=0). `loremaster.__file__` =
`/var/tmp/claude-1000/gg566-audit-scratch/loremaster/loremaster/__init__.py`. Sources byte-equal to the
real tree (`cmp` on `gated_ground.py` and `test_gated_ground.py`).

**M1 (brief):** `is_under(testpath, directory)` → `testpath.startswith(directory)`. Declared RED (6):
1. `…TestAConftestIsCoveredWherePytestLoadsIt::test_a_conftest_pytest_loads_is_execution_covered[conftest.py]`:
   `"loremaster/tests".startswith(".")` is False, so the root loses coverage.
2. `…::test_a_conftest_pytest_never_loads_stays_execution_ungated[lore/conftest.py]`: string-prefix leak.
3. `…::test_a_conftest_pytest_never_loads_stays_execution_ungated[skills/lore/conftest.py]`: nested leak.
4. `…TestMembershipDiscriminatesAtEveryCallSite::test_repository_root_level_python_is_ordinary_committed_ground`: root.
5. `…TestTheRealRepositoryIsFullyGated::test_no_committed_python_is_ungated_on_either_axis`: the real root `conftest.py`.
6. `…TestTheExemptionTableIsAnAllowlistOfTheSafe::test_the_table_lands_EMPTY_and_the_emptiness_is_a_fact_about_the_TREE`: same real root.
Predicted GREEN under M1: `loremaster/conftest.py`, `skills/conftest.py` and `skills/lore-deploy/conftest.py`,
because the string prefix happens to agree there. The other 4 negatives stay green too.

**M2 (my probe, C2):** `is_under(path, testpath) or is_under(testpath, directory)` → `is_under(testpath, directory)`.
Declared RED: **none**. `mutation_proof.py` requires ≥1 `--expect-red`, so I pass the sentinel id
`scripts/test_gated_ground.py::NO_PIN_EXISTS_FOR_A_NESTED_CONFTEST`. The expected outcome is EXIT 4,
with the sentinel listed as declared-but-green and **zero unexpected reds**. That records "the
contract has no pin for this wrong build".

### 3a. Mutation results (run 2026-10-31 ~20:12Z; log `/var/tmp/claude-1000/gg566-mutations.log`)
| mutant | landed | count | declared vs observed | restored | `mutation_proof` exit |
|---|---|---|---|---|---|
| M1 `startswith` | anchor matched exactly once | 6 failed, 323 passed | **PROOF HELD**: the 6 declared = the 6 observed, both directions | md5 `d0566de4…` | 0 |
| M2 drop the under leg | anchor matched exactly once | **329 passed** | declared sentinel stayed green; **observed: [] (0 unexpected reds)** | md5 `d0566de4…` | 4 (as predicted) |
After both runs the real tree's `scripts/gated_ground.py` md5 = the scratch md5 = `d0566de4…`.
The M2 positive control (so the survivor is a REAL wrong build, not an equivalent mutant) used
pytest 9.0.3 oracle root `/var/tmp/claude-1000/gg566-probe/nested-oracle.zNFj`,
`testpaths=["loremaster/tests"]`, PYTEST_EXIT=0. pytest **loaded** both
`loremaster/tests/conftest.py` and `loremaster/tests/store/conftest.py`. The correct build
`_pytest_loads_conftest("loremaster/tests/store/conftest.py", ["loremaster/tests"])` returns True; the
M2 build returns False. So M2 reports a conftest pytest really loads as execution-UNGATED. That is a
false positive, and the contract cannot see it. → **C2 confirmed, routed to the contract author.**

### 3b. C3 agreement probe (instrument committed nowhere, pasted verbatim per brief-base §1)
Result: 14 candidates × {the real testpaths (8), the contract's testpaths (2)} → `disagreements=[]` both times.
```python
"""C3 probe: _pytest_loads_conftest vs the conftest chain _collector_input_paths derives."""
import sys
from pathlib import Path, PurePosixPath
sys.path.insert(0, "scripts")
import gated_ground as gg

repo = Path(".").resolve()
real_testpaths = gg.pytest_testpaths(repo)
contract_testpaths = ["loremaster/tests", "skills/lore-deploy/tests"]
candidates = [
    "conftest.py", "loremaster/conftest.py", "skills/conftest.py", "skills/lore-deploy/conftest.py",
    "loremaster/tests/conftest.py", "loremaster/tests/store/conftest.py", "lore/conftest.py",
    "skills/lore/conftest.py", "skills/otherskill/conftest.py", "skills-old/conftest.py",
    "docs/consult/conftest.py", "tools/conftest.py", "scripts/conftest.py", "lorerunes/conftest.py",
]
for testpaths in (real_testpaths, contract_testpaths):
    chain = {gg.CONFTEST_FILENAME}
    for testpath in testpaths:
        ancestor = PurePosixPath()
        for component in PurePosixPath(testpath).parts:
            ancestor = ancestor / component
            chain.add(str(ancestor / gg.CONFTEST_FILENAME))
    disagreements = []
    for path in candidates:
        constructive = path in chain or any(gg.is_under(path, tp) for tp in testpaths)
        predicate = gg._pytest_loads_conftest(path, testpaths)
        if constructive != predicate:
            disagreements.append((path, constructive, predicate))
    print(f"testpaths={testpaths} candidates={len(candidates)} disagreements={disagreements}")
```
(The chain is re-derived here the way `_collector_input_paths` does it. That is a copy of its loop, not
a call: the function returns absolute `Path`s mixed with every tracked `.py`, so the chain is not
separately addressable. That is C3's point.)

## 4. Fix in place
**None.** I found no quality nit in `_pytest_loads_conftest` or in the two docstrings it touched.
The names are descriptive, it is typed, the docstring is true, it reuses `is_under`, it uses no
f-string-worthy formatting, and it has no magic values (`CONFTEST_FILENAME` already exists). The two
real issues are a contract gap (C2) and a design-level DRY (C3). Neither is a nit, and both are routed.
`scripts/gated_ground.py` is byte-unchanged from `08acd90` (`git diff --quiet 08acd90 -- scripts/gated_ground.py`).

## Gate receipts
| gate | command | log | EXIT | count | TREE |
|---|---|---|---|---|---|
| pytest | `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q scripts/test_gated_ground.py -n 8 --timeout=300 -p no:cacheprovider -rfE` (haiku-runner; `RAN:` checked, log read by me) | `/var/tmp/claude-1000/gg566-audit-gate-pytest.log` | 0 | 329 passed in 34.61s (0 ImportError/GuardIsBlind) | `33a61751…` |
| mypy | `MYPYPATH=scripts uv run mypy scripts/gated_ground.py` | `/var/tmp/claude-1000/gg566-audit-gate-mypy.log` | 0 | Success: no issues found in 1 source file | `33a61751…` |
| ruff | `uv run ruff check scripts/gated_ground.py` | `/var/tmp/claude-1000/gg566-audit-gate-ruff.log` | 0 | All checks passed! | `33a61751…` |
⚠ `TREE=` hashes untracked files too, and my own later appends to this report moved it to
`c58d3ab3…` (re-measured after the runs). `git diff --quiet HEAD -- scripts/` is clean and HEAD is
still `08acd90`, so every gated input is byte-identical to the receipts' tree. Only this report moved.
Logs are under `/var/tmp/claude-1000/` (outside the repo and not `/tmp`). They are not committed; the
lead may archive them.

Fan-out: haiku 2 · sonnet 0 · peak 2. Routing deviation: I ran the `--collect-only` id derivation
myself (one short command, grepped to 15 lines) instead of through a runner. I needed the exact ids
on my critical path to declare M1/M2 before any run.
