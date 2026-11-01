brief-base v24 read · brief project v7 read

## SUMMARY (2026-10-31, graded at HEAD `308251f`, contract file uncommitted on top)
- **State:** done-with-deviations. RED and satisfiability results are in §5 and §6.
- **Deviation 1 (PROMINENT):** an EXISTING pin contradicted the ruled property and is revised.
  `TestMembershipDiscriminatesAtEveryCallSite::test_repository_root_level_python_is_ordinary_committed_ground`
  asserted that the root `conftest.py` was execution-UNGATED in `workspace_shaped_repository`, a
  fixture with nested testpaths. That is the #566 false positive itself, pinned. It now asserts
  COVERED, with a #566 comment. Under the reference fix it would otherwise be a third red. The
  fixture's misleading comment was updated too.
- **Deviation 2:** the first RED and satisfiability runs carried a fixture defect. The new fixture
  had no archived-receipts file, so the guard refused it as `GuardIsBlind`. I fixed it and re-ran
  both, for 4 full runs instead of 2 (§5).
- **Packages considered:** none. No mechanism is specified; this is domain logic (pytest's
  conftest-loading rule). The rule was MEASURED with a pytest 9.0.3 oracle (§2), not assumed.
- **Odoo-20 portability:** n/a. No Odoo seam is touched.
- **Reuse ledger:** none. No production symbols. The reference fix reuses `gg.is_under`, and the
  test helpers reuse `FixtureRepository`, `assert_every_tracked_file_is_accounted_for`,
  `fates_of` and `findings_of`.
- **Graded:** n/a (author, not grader). Contract written at HEAD `308251f`.
- **Pins → wrong build:** see §3. Twelve new node ids in 1 class, plus 1 revised pin.
- **RED (HEAD `308251f`):** 7 failed / 322 passed (§5). All 7 are AssertionErrors: 4 new
  ancestor pins, the revised pin, and the 2 known live pins.
- **Satisfiability (scratch + reference):** 329 passed / 0 failed over the whole file (§6). Provenance:
  `loremaster.__file__ = /var/tmp/claude-1000/gg566-scratch/loremaster/loremaster/__init__.py`.
- **Decisions needed:** none blocking. One flag for the builder, §8 F1: the reference touches only
  `_execution_fate`. Docstrings and stated bounds were not swept.
- **Gates:** ruff (file) clean · currency `--legs typecheck,ruff`: typecheck RED_ADJUDICATED (83
  residuals, unchanged), ruff GREEN, pytest NOT_RUN (by design for this leg set, #565). No
  RED_ORPHANED verdict on the legs that ran.

## Routing table (written before the first read beyond the brief, per brief-base §3)
| step | tier | who |
|---|---|---|
| read the contract file's house rules and the FixtureRepository idiom | 3 (fixture design judgment) | self |
| write pins (i)–(iv) plus the prefix-ancestry fixtures | 3 (contract) | self |
| RED run at HEAD | 1 | haiku-runner |
| scratch copy plus reference fix | 3 (a wrong reference seals itself) | self |
| satisfiability run in scratch | 1 | haiku-runner |
| ruff, currency typecheck/ruff | 1 | self (two short commands with tiny output; a spawn would cost more than it reads) |

Delegated: 4 full-file pytest runs to haiku-runners. For each I checked the `RAN:` line against my
command and read the count line in the log myself. Everything else was done by me.

## 1. The property (brief, ruled option (a))
A tracked `conftest.py` is execution-covered iff pytest LOADS it for some testpath. That holds when
it lies UNDER a testpath, OR when its directory is a path-component ANCESTOR of a testpath, within
the repository root. The negative leg: every other conftest stays UNGATED.

## 2. The oracle: the property is measured, not assumed
pytest 9.0.3 (the lore `.venv`), 2026-10-31. Every conftest records its own import; pytest is run
with `--collect-only` and no args from a root whose `testpaths = ["loremaster/tests",
"skills/lore-deploy/tests"]`.
**Loaded:** `conftest.py`, `loremaster/conftest.py`, `loremaster/tests/conftest.py`,
`skills/conftest.py`, `skills/lore-deploy/conftest.py`, `skills/lore-deploy/tests/conftest.py`.
**Not loaded:** `loremaster/tes/`, `skills-old/`, `docs/consult/`, `tools/`. The contract's
loads / does-not-load tables follow this oracle. Instrument, verbatim (brief-base §1):
```bash
#!/usr/bin/env bash
# Oracle for #566: which conftest.py files does pytest LOAD for a given testpaths list?
# Each conftest appends its own repo-relative path to $LOADED on import.
# usage: oracle.sh <python> <throwaway-root>
set -euo pipefail
PY="$1"; ROOT="$2"; rm -rf "$ROOT"; mkdir -p "$ROOT"; cd "$ROOT"
cat > pyproject.toml <<'T'
[tool.pytest.ini_options]
testpaths = ["loremaster/tests", "skills/lore-deploy/tests"]
T
for d in . loremaster loremaster/tests loremaster/tes skills skills/lore-deploy skills/lore-deploy/tests skills-old docs/consult tools; do
  mkdir -p "$d"
  printf 'import os, pathlib\nwith open(os.environ["LOADED"], "a") as f: f.write(str(pathlib.Path(__file__).resolve().relative_to(pathlib.Path(os.environ["ROOT"]).resolve())) + "\\n")\n' > "$d/conftest.py"
done
printf 'def test_a():\n    assert True\n' > loremaster/tests/test_a.py
printf 'def test_b():\n    assert True\n' > skills/lore-deploy/tests/test_b.py
printf 'def test_c():\n    assert True\n' > skills-old/test_c.py
export LOADED="$ROOT/loaded.txt" ROOT; : > "$LOADED"
"$PY" -m pytest --collect-only -q -p no:cacheprovider > collect.log 2>&1; echo "PYTEST_EXIT=$?"
echo "--- loaded:"; sort -u "$LOADED"; echo "--- collected:"; grep '::' collect.log
```
Bound: the oracle measures pytest invoked with no args (testpaths in force). An explicit-path
invocation also loads that path's ancestor chain. The guard models testpaths only, which is the
property as ruled.

## 3. Pins (`scripts/test_gated_ground.py`, class `TestAConftestIsCoveredWherePytestLoadsIt` and fixture `conftest_chain_repository`)
The fixture has testpaths `("loremaster/tests", "skills/lore-deploy/tests")`, with the DEEP entry
listed SECOND. Its MEMBERS are `("loremaster", "skills", "tools/probes")`. It is built
`git init`-from-empty by `FixtureRepository`, and every case runs through the ∀-inputs
accounting helper.

| pin | file | expect | wrong build it kills |
|---|---|---|---|
| (i) `…loads_is_execution_covered[conftest.py]` | root | COVERED | HEAD's under-only rule; "the root's dirname `.` is never an ancestor" |
| (ii) `…[loremaster/conftest.py]` | parent of the 1st testpath | COVERED | "only the root is special-cased" |
| (ii) `…[skills/conftest.py]` | GRANDPARENT of the 2nd testpath | COVERED | "parent only, one level up"; "only the first testpath is walked"; "root only" |
| (ii) `…[skills/lore-deploy/conftest.py]` | parent of the 2nd testpath | COVERED | "root only"; ancestry tested against the conftest FILE path rather than its directory |
| (iv) `…[loremaster/tests/conftest.py]` | under a testpath | COVERED | a rewrite that keeps only the ancestor leg and drops the under leg. NOT pinned before this change (checked: no prior conftest-COVERED assertion existed) |
| (iii) `…never_loads_stays_execution_ungated[lore/conftest.py]` | `"loremaster/tests".startswith("lore")` | UNGATED | **string-prefix ancestry**, top level |
| (iii) `…[skills/lore/conftest.py]` | `"skills/lore-deploy/tests".startswith("skills/lore")` | UNGATED | **string-prefix ancestry**, nested (the brief's `skills` vs `skills-old` class, in the direction an ancestry check actually takes) |
| (iii) `…[skills/otherskill/conftest.py]` | a cousin under the `skills` ancestor | UNGATED | "shares a top-level component"; "under SOME ancestor of a testpath" |
| (iii) `…[skills-old/conftest.py]` | a sibling-prefix of `skills` | UNGATED | `startswith` against the ancestor directory (the brief's example) |
| (iii) `…[docs/consult/conftest.py]` | a plain sibling | UNGATED | "every conftest is covered" |
| (iii) `…[tools/conftest.py]` | an ancestor of a MEMBERS root only | UNGATED | ancestry taken against the TYPE gate's roots instead of the testpaths |
| `test_the_ancestor_rule_does_not_leak_onto_the_types_axis` | root conftest, TYPES | UNGATED | "a pytest-loaded conftest is covered on BOTH axes" (the per-axis law) |
| revised: `TestMembershipDiscriminatesAtEveryCallSite::test_repository_root_level_python_is_ordinary_committed_ground` | root conftest in `workspace_shaped_repository` | COVERED (was UNGATED) | the old-world pin (Deviation 1) |

Each negative also asserts that the path is in the SERVED execution findings, not only that its
fate is UNGATED.

An already-existing pin covers "apply the ancestor rule to every test-shaped file":
`TestMembershipDiscriminatesAtEveryCallSite::test_an_ancestor_of_a_testpath_is_not_covered_by_it`
(`skills/test_workspace_probe.py`). It is cited in the class docstring and not duplicated.

**These wrong builds are DESIGNED, NOT BUILT.** Building them is the adversary's job, and brief-base
§2 ROLE BOUNDARY forbids it to me.

## 4. Adversarial pre-flight → coverage
- Wrong anchor (ancestry against the type gate's roots, not testpaths): `tools/conftest.py`.
- String vs component ancestry: `lore/`, `skills/lore/`, `skills-old/`.
- Boundary (root, empty parts): `conftest.py`, plus the TYPES-leak pin.
- Depth (parent vs grandparent; first vs non-first testpath): `skills/conftest.py`.
- Over-broad fix: the 6 negatives and the existing ancestor-test-file pin.
- Producer↔consumer seam (testpaths reader → `_execution_fate`): exercised end-to-end through
  `gg.classify` on a real `pyproject.toml` parsed by the production reader.
- Real-tree seam: the two live pins (`TestTheRealRepositoryIsFullyGated…`,
  `…test_the_table_lands_EMPTY…`) over this checkout's real root `conftest.py`.
- Scoped out: an ancestor ABOVE the repository root. No tracked file can sit there (git ls-files
  is root-relative). Planted-data only.
- Scoped out: testpaths spelled `loremaster/tests/` (trailing slash) or `./x`. The testpaths reader
  already normalises or refuses those spellings under existing pins (`WHOLE_TREE_SCOPE_SPELLINGS`),
  so they are not re-pinned here. NOT verified for trailing-slash specifically; flagged as F2.
- Scoped out: a conftest under a testpath but in a `norecursedirs`-silenced subtree. pytest would
  NOT load it, yet registration says COVERED. This is the existing STATED bound
  `conftest-collection-hooks`, not a #566 regression.

## 5. RED at HEAD `308251f`
- Run 1 (haiku-runner, `RAN:` checked; log `/var/tmp/claude-1000/gg566-red.log`): **15 failed,
  314 passed**. The 2 known live pins and the revised pin failed with AssertionError. The 12 new
  pins failed with `GuardIsBlind` (receipts-class-matches-nothing), a FIXTURE reason, which is
  Deviation 2.
- Inline probe after the fixture fix (new class only): 4 failed, 8 passed. The 4 are AssertionError
  `UNGATED is not COVERED`: `conftest.py`, `loremaster/conftest.py`, `skills/conftest.py`,
  `skills/lore-deploy/conftest.py`.
- Run 2 (full file, fixed fixture; haiku-runner, `RAN:` checked; log
  `/var/tmp/claude-1000/gg566-red2.log`, header `HEAD=308251f… TREE=e5b9bdb4…`; contract md5
  `96ec4cc8e8430a3ae7015f6c0fb0781e`): **7 failed, 322 passed, PYTEST_EXIT=1**. There were 0
  `GuardIsBlind`, 0 ImportError and 0 ERROR lines, and every failure is an AssertionError:
  - 4 new pins: `…loads_is_execution_covered[conftest.py | loremaster/conftest.py | skills/conftest.py | skills/lore-deploy/conftest.py]`;
  - the revised `…test_repository_root_level_python_is_ordinary_committed_ground`;
  - the 2 known live pins, `TestTheRealRepositoryIsFullyGated::test_no_committed_python_is_ungated_on_either_axis`
    and `TestTheExemptionTableIsAnAllowlistOfTheSafe::test_the_table_lands_EMPTY_and_the_emptiness_is_a_fact_about_the_TREE`,
    left as they were.
- Expected and behavioural: the 4 ancestor pins, the revised pin and the 2 known live pins are red.
  (iv), the 6 negatives and the TYPES-leak pin are GREEN at HEAD BY DESIGN. HEAD is
  under-inclusive, so these pins guard against an OVER-broad fix and cannot be red at HEAD.

## 6. Satisfiability (scratch `/var/tmp/claude-1000/gg566-scratch`, via `scratch_copy.sh`, provenance asserted; `LORE_PYTHON` exported)
`loremaster.__file__ = /var/tmp/claude-1000/gg566-scratch/loremaster/loremaster/__init__.py`.
- Run 1 (stale fixture; log `/var/tmp/claude-1000/gg566-sat.log`): 12 failed, 317 passed. All 12
  were `GuardIsBlind` in the new class (0 failures outside it). **The 2 live pins and the revised
  pin PASSED under the reference.**
- Run 2 (fixed fixture; haiku-runner, `RAN:` checked; log `/var/tmp/claude-1000/gg566-sat2.log`,
  header `HEAD=308251f… TREE=747ab945…`; scratch contract md5 `96ec4cc8…` = the real tree's):
  **329 passed, 0 failed, PYTEST_EXIT=0** over the WHOLE `scripts/test_gated_ground.py`. That
  includes both live pins, the revised pin and all 12 new ones. There were 0 ImportError and 0
  `GuardIsBlind`. The real tree's `scripts/gated_ground.py` is untouched (`git diff --quiet`).

**Reference diff: a SATISFIABILITY BUILD ONLY, not the fix. A builder writes the real one.**
```diff
@@ -1417,7 +1417,13 @@ def _execution_fate(path: str, *, scopes: _Scopes, exemptions: Sequence[Exemptio
     if not _is_test_shaped(path, scopes.test_file_patterns, repo_root=scopes.repo_root):
         return Fate.NOT_APPLICABLE
     if PurePosixPath(path).name == CONFTEST_FILENAME:
-        if any(is_under(path, testpath) for testpath in scopes.testpaths):
+        # pytest loads every conftest on the rootdir -> testpath chain (#566): a conftest is
+        # covered when it lies under a testpath OR its directory is an ancestor of one.
+        directory = str(PurePosixPath(path).parent)
+        if any(
+            is_under(path, testpath) or is_under(testpath, directory)
+            for testpath in scopes.testpaths
+        ):
             return Fate.COVERED
     elif path in scopes.collected:
         return Fate.COVERED
```
(The root conftest's parent is `.`, and `PurePosixPath(x).is_relative_to(".")` is True for every
relative x. That is why the root case needs no special-casing.)

## 7. Realism and independence clauses
- ☑ **Production-realistic inputs:** the fixture paths mirror this checkout's real layout
  (`loremaster/tests`, `skills/lore-deploy/tests`, the real root conftest shape). The prefix decoys
  are names a real tree could carry (`skills/lore`, `lore/`, `skills-old`).
- ☑ **Independent expected values:** the expected fates come from the pytest 9.0.3 oracle (§2), a
  measured reference output. They are not taken from the guard.
- ☑ **Seam coverage:** pyproject → testpaths reader → classify, end-to-end. The real-tree pins
  cover the production root conftest.
- ☐ **Magnitude bound:** not applicable because the outputs are enum fates, not derived numbers.
- ☑ **Shared conventions:** the testpaths are read by the production reader from a real
  `pyproject.toml`. The receipts root comes from the same constant the guard uses (the fixture
  file sits under `docs/plans/v2/receipts`, which matches `_minimal_repository`).
- **Hostile fixtures:** not applicable because no stored free text is rendered.
- **Input accounting:** ☑. Every case runs through `assert_every_tracked_file_is_accounted_for`,
  and both fates (COVERED and UNGATED) are FORCED by fixtures.

## 8. Flags / noticed
- **F1 (builder):** the reference changes only `_execution_fate`. I did not sweep the module's
  docstrings, the `STATED_BOUNDS` prose or the failure message for an "under a testpath" claim that
  #566 makes false. The rename/reshape sweep law says such prose is where defects hide, so the
  builder should grep `gated_ground.py` for `conftest` (19 hits at HEAD) and adjudicate each one.
- **F2:** the trailing-slash testpath spelling (`"loremaster/tests/"`) was not verified to be
  normalised before `is_under(testpath, directory)`. `PurePosixPath` strips trailing slashes, so I
  rate it LOW risk (reasoned, not run).
- **F3 (process):** CLAUDE.md now asks for a `tree_id.sh` `TREE=` line in gate-log headers. Every full
  run carries it except RED run 1, which predates my noticing the change. The inline new-class
  probe (§5) also lacks it; it is a probe, not a receipt.
- **F4:** `-rfE` summary lines carry node ids only, so the runner took the reasons from the `E`
  lines. This is noise, not a defect.
