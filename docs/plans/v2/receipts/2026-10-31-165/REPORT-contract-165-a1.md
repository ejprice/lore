brief-base v24 read
brief project v7 read

BRIEF CONFLICT: step D(ii)/D4 ("apply a substring-matching healthy-dir wrong build over the reference … Expected: the T1 prefix-pair test goes RED") — refused per role boundary (brief-base v24 §2: a contract author never builds wrong implementations; no dated operator grant quoted). Everything else was done.

## Summary
- **State:** done-with-deviations (D4 refused; T1 discrimination shown by construction, not by a run).
- **Deviations:** D4 refused (above). 6 runs instead of ~2: runs 5–6 re-prove 1–2 after a ruff-only rewrap. Step A ran as lore MCP reads, not grep (hook denies grep on any lore-named path).
- **Packages considered:** none — no mechanism specified.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 4 rows of new test-side symbols, all dispositioned (§DRY ledger).
- **Graded:** bb61542 (+ my uncommitted contract edits) · HEAD-at-report: bb61542 · SAME. HEAD moved during the run from 26c3a20 (spawn) to bb61542 (the #165 build commit); `lore_deploy.py` is byte-identical to the uncommitted build I read at spawn.
- **Tests:** in `skills/lore-deploy/scripts/test_launch_snapshot_bind.py`. A1: one ∀ test over 3 post-teardown doors. A8: the shared remedy helper now derives the interpreter from `_loremaster_python()`, plus an autouse distinct-`LORE_PYTHON` fixture and one runs-as-pasted test. T1: whole-token matchers on BOTH directions of the tier-naming helper, plus a 2-cell `surrealdb`/`surrealdb-docs` prefix-pair test.
- **RED at bb61542:** 11 failed / 58 passed (69). All 11 are behavioural: 9 A8 remedy failures (incl. both T1 cells, whose tier/dir assertions PASS and which fail only on the shared remedy line) and 2 A1 `RuntimeError` escapes (`config_unreadable`, `snapshot_vanishes`). The A1 `podman_run_fails` cell is green, as expected.
- **Satisfiability at the scratch reference:** 152 passed / 0 over `. ../tests` (and 69/0 after the rewrap). `loremaster.__file__` = `/var/tmp/claude-1000/c165a1-scratch/loremaster/loremaster/__init__.py`; `lore_deploy.__file__` = `/var/tmp/claude-1000/c165a1-scratch/skills/lore-deploy/scripts/lore_deploy.py`.
- **ruff:** clean after rewrapping 4 lines over 110 characters.
- **Decisions needed:** (1) does A1's "ANY launch failure" include the undocumented `OSError` (podman binary gone)? (2) should the remedy `shlex.quote` its paths? (3) should a grader run the refused D4 wrong build? (§Anything noticed 1–2, §T1 discrimination.)
- **Pointers:** §Runs; RED classification; Reference diff; §The new / changed tests; §Adversarial pre-flight; §Anything noticed.

# REPORT-contract-165-a1 — A1 / A8 / T1 pins (tdd-light follow-up, lore #165)


## Routing table (written FIRST, before any read beyond the brief + brief-base)

| step | tier | who | reason |
|---|---|---|---|
| A. Lookups (recreate handler, `_launch_container` Raises, `_loremaster_python`, `_assert_teaches_every_failing_tier`, the R3 test) | 1 (parallel batch) | me, ONE parallel batch of reads (size: 2 files — `lore_deploy.py` spans + `test_launch_snapshot_bind.py`) | brief routes it so; small, on critical path, I read all of it to write pins |
| B. Pins | 3 | me | contract authorship (never Haiku; lore pins contract authors to Opus) |
| C. RED run | 1 | `haiku-runner` | test run |
| D1. scratch copy | 1 | `haiku-worker` (spawned at once, parallel with A) | mechanical command |
| D2. reference fix in scratch | 3 | me | a reference build's correctness is judgment; it is a satisfiability instrument, not a grade |
| D3. satisfiability run | 1 | `haiku-runner` | test run |
| D4. substring wrong build + rerun | 1 run / 3 edit | me edit, `haiku-runner` run | ONE wrong build named by the brief for T1 discrimination only (see role note) |
| E. ruff | 1 | `haiku-runner` | lint gate |

Routing note (D4): **refused** — see BRIEF CONFLICT in the summary. No wrong build was made.
Fan-out: haiku 7 (1 worker: scratch copy; 6 runners: RED ×2, satisfiability ×2, ruff ×2) · sonnet 0 · peak 3.
Routing note (A): `grep` was denied by the PreToolUse hook even in the scratch copy (it keys on the
path), so the lookups ran as ONE parallel batch of `lore_get_symbol` / `lore_read` calls: 9 symbols
(`_launch_container`, `_loremaster_python`, `_require_launchable_snapshot`, `verb_start`,
`_unmaterialised_static_tiers`, `_gate_snapshot_precondition`, `_read_config_field`, `_run`,
`SnapshotLayout`) + `snapshot.py` 1-130 + `test_lore_deploy._RecreatePathFixture` span + the contract
file (911 lines, read whole) + `lore.yaml`. Coverage: 9/9 symbols resolved, `candidate_count` 1 each
(except `_run`: 3 candidates, disambiguated by module path). Fallback to lore was the hook's
requirement, not a lore weakness; nothing to file.

## The new / changed tests, each with the wrong build it catches

All in `skills/lore-deploy/scripts/test_launch_snapshot_bind.py`. No existing assertion was weakened
(see T1 for the one assertion whose matching changed, and why it is strictly a false-fail removal plus
a strengthening).

### A8 — the remedy runs as pasted
- **`_cold_index_command`** (shared helper, used by every refusal assertion through
  `_assert_teaches_every_failing_tier`): expected remedy is now
  `f"{lore_deploy._loremaster_python()} -m loremaster.index --config {config_path}"` — the interpreter is
  DERIVED from production, never retyped (ruling A8).
- **`_distinct_loremaster_interpreter`** (new autouse fixture): sets production's documented override
  `LORE_PYTHON` to a `/bin/sh` wrapper in `tmp_path` that `exec`s whatever `_loremaster_python()` resolved
  before the fixture (so a scratch copy's own `LORE_PYTHON` still wins and the real config reader keeps
  working). WHY: under `uv run`, `sys.executable`, the workspace `.venv` default and even PATH's `python`
  all resolve to the same venv interpreter, so without a distinct spelling a remedy built from any of
  them is indistinguishable from the correct one (fixture monoculture). Catches: bare `python`;
  `sys.executable`; a hardcoded `~/PycharmProjects/lore/.venv/bin/python`.
- **`TestRefusalRemedyRunsAsPasted::test_remedy_interpreter_is_the_deploy_interpreter_and_resolves_the_cold_index_module`**
  (new): parses the ONE backticked command out of the real refusal, `shlex.split`s it, asserts
  `argv[0] == _loremaster_python()` and `argv[1:] == ["-m", "loremaster.index", "--config", <config>]`, then
  RUNS `argv[0]` with `importlib.util.find_spec("loremaster.index")` — the "runs as pasted" leg.
  Catches: any interpreter other than the deploy's own; a remedy for the wrong config; a remedy with no
  backticked command or two of them; an interpreter path that does not exist or cannot import loremaster.
- Existing tests that now carry A8 through the helper: pin 4 (`TestMissingHostSnapshotRefusesLaunch`),
  `TestVerbStartRefusesMissingSnapshotBeforeTeardown` (fresh + recreate), the refusing cells of
  `TestDeployPreconditionAgreesWithServerGuard` (absent / empty / file), and the new T1 cells.

### A1 — after teardown, every documented launch failure degrades to `_EXIT_ERROR`
- **`TestRecreateFailureAfterTeardownDegradesToExitError::test_post_teardown_launch_failure_returns_exit_error_with_its_text`**,
  parametrised over `_POST_TEARDOWN_DOORS` — the ∀ over the failure TYPES `_launch_container` documents:
  - `snapshot_vanishes` (RuntimeError from the REAL launch's precondition re-check: the first static
    tier's host dir is removed when `podman rm` runs — a concurrent cold-index re-materialise or an
    operator `rm` in the window);
  - `config_unreadable` (RuntimeError from the REAL config read: `watch: statc` written at `podman rm`);
  - `podman_run_fails` (CalledProcessError from `_run(check=True)` on `podman run`, exit 125 with podman's
    stderr shape).
  Each cell drives the REAL `_launch_container` (only observed, so the test can name the error), and
  asserts, in order: stop+rm happened (the cell really is post-teardown); the real launch raised exactly
  one error of the documented type (step-N-no-op guard: the door really fired); `verb_start` returned
  `_EXIT_ERROR` with no raise; `str(error)` is on stderr.
  Catches: a handler that catches only `CalledProcessError` (the current tree); one that catches only
  `RuntimeError`; one that swallows the error and prints a generic line without its text; one that
  catches and then proceeds to bind-wait/merge (`_EXIT_OK`); one that re-raises.
  Not catching (named bound): `OSError` from `_run` when the podman binary vanishes — not a type
  `_launch_container` documents, so outside the ruled ∀ (see Anything noticed).

### T1 — a tier that prefixes another cannot misfire
- **`_names_path` / `_names_tier`** (new matchers) replace the substring checks inside
  `_assert_teaches_every_failing_tier`. A name ends at end-of-text, whitespace, `; , : ' " \` ) ]`, or a
  sentence-final period; `-`, `/`, word characters and `.`+word continue it. Applied to BOTH directions:
  - healthy check (`not _names_path(text, healthy_dir)`): removes the false-fail where `<root>/surrealdb`
    is a substring of a named `<root>/surrealdb-docs`;
  - failing check (`_names_tier(text, tier) and _names_path(text, tier_dir)`): STRENGTHENED — the old
    substring check was vacuously satisfied for failing `surrealdb` by a text naming only
    `surrealdb-docs` (the class one level up from the ruled item; same defect, other direction).
- **`TestRefusalNamesTiersByWholePathComponent::test_prefix_pair_refusal_names_only_the_failing_tier`**
  (new), parametrised `failing_tier ∈ {surrealdb, surrealdb-docs}`: a config derived from the real
  `lore.yaml` with static tiers `surrealdb-docs` and `surrealdb` (both fall back to `<root>/<tier>` in
  production `SnapshotLayout`); the fixture asserts the dirs really are a string-prefix pair and the REAL
  server guard reads only the failing tier unmaterialised, then pins the real refusal through the helper.
  Catches: a refusal that names both tiers (lists every static tier, or matches failing tiers by name
  prefix); a refusal that names the prefixed tier when only the prefix tier fails.
  By construction (NOT a run): the OLD substring helper, given orientation `failing=surrealdb-docs` on a
  correct build, evaluates `"<root>/surrealdb" not in "...<root>/surrealdb-docs..."` → False → RED. That is
  the false-fail T1 names; the new matcher passes it.

## Runs (receipts; all measured 2026-10-31)

| # | label | tree | command scope | result |
|---|---|---|---|---|
| 1 | RED at HEAD tree (bb61542, whose `lore_deploy.py` is byte-identical to the uncommitted build read at spawn — `cmp` vs the scratch backup) | main | `test_launch_snapshot_bind.py test_lore_deploy.py` | **11 failed, 58 passed** in 32.58s; no ERROR / ImportError. Log `/var/tmp/claude-1000/c165a1-red.log` |
| 2 | GREEN at reference (scratch, D2 diff below) | `/var/tmp/claude-1000/c165a1-scratch` | `. ../tests -n 8` (brief's D3 command) | **152 passed**, 0 failed, EXIT 0. `loremaster.__file__` = `/var/tmp/claude-1000/c165a1-scratch/loremaster/loremaster/__init__.py`; `lore_deploy.__file__` = `/var/tmp/claude-1000/c165a1-scratch/skills/lore-deploy/scripts/lore_deploy.py`. Log `/var/tmp/claude-1000/c165a1-sat.log` |
| 3 | ruff | main | contract file | 4 × E501 (lines >110) → rewrapped, no logic change |
| 4 | ruff re-run after rewrap | main | contract file | `All checks passed!`, exit 0 |
| 5 | RED re-run after the lint rewrap | main | as #1 | **11 failed, 58 passed** in 32.35s, PYTEST_EXIT=1; failing set IDENTICAL to run 1 (`diff` of sorted `FAILED` lines). Log `/var/tmp/claude-1000/c165a1-red2.log` |
| 6 | reference re-run after the lint rewrap | scratch | contract file + `test_lore_deploy.py`, `-n 8` | **69 passed**, 0 failed, PYTEST_EXIT=0; same two `__file__` lines inside the copy. Log `/var/tmp/claude-1000/c165a1-sat2.log` |

Runs 5–6 exist only because the ruff fix rewrapped lines after runs 1–2; they prove the rewrap moved no
verdict. That is more than "about 2"; the reason is the lint fix.

**RED classification (run 1), every failure BEHAVIOURAL** (read from the log's `E` lines, not the runner's summary):
- A8 remedy, 9 tests — `refusal must carry the paste-ready remedy `<tmp>/loremaster-interpreter/lore-python -m
  loremaster.index --config …`; got '… retry: `python -m loremaster.index --config …`'`:
  pin 4; verb_start [fresh], [recreate]; S1 agreement [absent], [empty], [file]; T1 [surrealdb],
  [surrealdb-docs]; and the dedicated A8 test (`got 'python'` on the `argv[0]` assert).
  The 2 T1 cells reach the remedy line only after the helper's tier/dir checks PASS (the helper checks
  failing-tier naming, then healthy-dir non-naming, then the remedy), so the T1 assertions are green on the
  current build, as the brief expected; the cells are red solely through the shared A8 remedy.
- A1, 2 cells — `Failed: config_unreadable: a launch failure after teardown must return _EXIT_ERROR, not
  raise; raised RuntimeError('failed to read "sum(1 for r in c.roots if r.watch == 'static')" …')` and the
  same for `snapshot_vanishes` with `RuntimeError('refusing to launch: 1 static tier(s) …')`. The
  `podman_run_fails` cell is GREEN on the current build (the handler already catches CalledProcessError) —
  expected for the ∀ form: it pins the type already handled so a fix that swaps one catch for the other
  goes red.

**Reference diff (D2), applied only in the scratch copy** — a satisfiability instrument, NOT a build for
the implementer to copy:
```diff
@@ _require_launchable_snapshot
-            f"retry: `python -m {_COLD_INDEX_MODULE} --config {config_path}`"
+            f"retry: `{_loremaster_python()} -m {_COLD_INDEX_MODULE} --config {config_path}`"
@@ verb_start, recreate branch, after the existing `except subprocess.CalledProcessError` block
+            except RuntimeError as error:
+                print(
+                    f"start: relaunch of {container_name} refused ({error}); the stale "
+                    f"container was already removed — fix the cause and retry `start`.",
+                    file=sys.stderr,
+                )
+                return _EXIT_ERROR
```

## T1 discrimination (step D4) — NOT TRIED, refused (BRIEF CONFLICT)
The brief asks for ONE substring-matching wrong build to show the T1 pin goes RED. brief-base v24 §2
ROLE BOUNDARY (non-overridable) forbids a contract author building wrong implementations; the brief
quotes no dated operator grant. So no wrong build was made. Two readings of "a build whose healthy-dir
check is a substring match" exist and would give different work:
- (a) the TEST's healthy-dir check is a substring match (the old helper): shown RED **by construction**
  above (`"<root>/surrealdb" not in "…<root>/surrealdb-docs…"` is False) on a correct build — this is the
  T1 smell itself, and needs no wrong production build;
- (b) a PRODUCTION build that picks/names tiers by substring or prefix (e.g. names every static tier whose
  name is a prefix of a failing one): caught by the new healthy-dir assertion in the
  `failing_tier=surrealdb-docs` cell (it would name `<root>/surrealdb` as a whole path). Not executed.
  I would pick (b) as the brief's intent. It belongs to a grader (`contract-adversary`) or to a lead
  holding an operator grant.

## Adversarial pre-flight

| entry | covering case / note |
|---|---|
| Wrong anchor/scale: n/a — no numeric output | scoped out: the unit emits exit codes and prose |
| Producer↔consumer seam: the refusal prose → an operator's shell (A8) | dedicated A8 test RUNS the parsed interpreter (`find_spec`) |
| Interpreter monoculture (`sys.executable` == venv default == PATH python under `uv run`) | autouse `LORE_PYTHON` wrapper, so the three spell differently |
| Post-teardown failure through the re-check (TOCTOU: snapshot wiped in the window) | A1 `snapshot_vanishes` |
| Post-teardown failure through the config read | A1 `config_unreadable` |
| Post-teardown `podman run` failure | A1 `podman_run_fails` (and existing R3) |
| A green cell where the failure never fired | each A1 cell asserts stop+rm happened AND the real launch raised the documented type |
| Prefix-pair tier names (healthy false-fail) | T1 cell `failing=surrealdb-docs` |
| Prefix-pair tier names (failing check vacuous) | T1 cell `failing=surrealdb` + `_names_tier`/`_names_path` on the failing leg |
| Sentence-final `.` after the last dir in the tier list | `_NAME_END` accepts `.` only when followed by whitespace/end, so `<dir>.x` still continues the name |
| `OSError` (podman binary vanishes) after teardown | NOT pinned — not a documented type; flagged below as a spec-silent fork |
| Interpreter path containing spaces (remedy not paste-ready unless quoted) | NOT pinned — spec-silent; flagged below. The test's `shlex.split` would surface it if `tmp_path` had spaces; it does not |
| Hostile stored text | n/a — the refusal renders config-derived tier names and host paths, not stored free text |

## Realism & independence clauses
- ☑ Production-realistic inputs: configs derived from the real `lore.yaml`; podman exit 125 with podman's
  stderr shape; the TOCTOU door is a real concurrent re-materialise; `LORE_PYTHON` is the production override.
- ☑ Independent expected values: the remedy's interpreter comes from production `_loremaster_python()` per
  the ruling (a derived convention, not the formula under test); the module and argv shape come from the
  ruling text; A1 expects `str(the raised error)`, captured from the real launch, never re-composed.
- ☑ Seam coverage: the A8 test crosses refusal-prose → interpreter by executing it; A1 drives the REAL
  `_launch_container` inside the REAL `verb_start`, only podman recorded.
- ☐ Magnitude bound: not applicable because no numeric output is derived.
- ☑ Shared conventions: tier dirs from production `SnapshotLayout`; the interpreter from production
  `_loremaster_python()`; the static-root count through the real reader.
- Hostile fixtures for rendered stored text: not applicable (no stored free text rendered).
- Input accounting for collection transforms: not applicable (the refusal maps config tiers to verdicts;
  the per-tier agreement pin `TestDeployPreconditionAgreesWithServerGuard` already covers that set).

## Packages considered
none — no mechanism specified (the matchers are a 2-line `re.search` over the stdlib; `shlex` parses the
pasted command).

## DRY ledger (new test-side symbols)
| new symbol | where I looked | what it returned | disposition |
|---|---|---|---|
| `_distinct_loremaster_interpreter` | the contract file (read whole), `test_lore_deploy._RecreatePathFixture` | no interpreter fixture | HAND-ROLLED (test fixture; production override reused) |
| `_names_path`, `_names_tier`, `_NAME_START`, `_NAME_END` | the contract file; `loremaster.search._sanitise_line` is the repo's render seam, not a matcher | no path/token matcher in either test file | HAND-ROLLED (test-side) |
| `_POST_TEARDOWN_DOORS`, `PODMAN_SETUP_FAILED_*` | `_RecreatePathFixture.install_failing_launch` (exit 125) | that fixture STUBS the launch; A1 needs the REAL one | HAND-ROLLED; same exit code reused |
| `_BACKTICKED_COMMAND`, `PREFIX_TIER`, `PREFIXED_TIER` | the contract file | none | HAND-ROLLED |

## Anything noticed (raised, not decided)
1. **Spec-silent fork — `OSError` after teardown.** `_run` lets `FileNotFoundError` escape if `podman`
   vanishes from PATH between the pre-teardown checks and the relaunch. The ruling's ∀ is over the
   DOCUMENTED types, so this is outside it; the ruling's property sentence ("ANY launch failure after
   teardown") would include it. Two readings, different code: catch the documented two (pinned), or catch
   `Exception` broadly. I would keep the documented two and ask the operator; not pinned.
2. **Spec-silent — remedy quoting.** `<interpreter> -m …` is not paste-ready if the interpreter or the
   config path contains a space or a shell metacharacter. A `shlex.quote` in production would fix it;
   the A8 pin would then still pass for ordinary paths. Ruling needed if it matters.
3. **Lead-owned residue:** the artifact pin's preflight message (`_preflight`) still teaches bare
   `python -m loremaster.index`. It is test prose, not a served remedy; left unchanged (outside the three
   items; one-line edit if wanted). The ruling also defers the prose docs (`references/lifecycle.md` shows
   `M` in `git status` — someone is already editing it).
4. **HEAD moved during this run** (26c3a20 at spawn → bb61542, the #165 build commit). The deploy script
   is byte-identical to what I read; the contract file's diff vs bb61542 is exactly my edits
   (260+/4−, `git diff --stat`).
5. `grep` is blocked by the hook on ANY path containing the lore checkout name, including a scratch copy
   under `/var/tmp` invoked with `cd …/skills/lore-deploy/…`; a plain `grep` over a log under
   `/var/tmp/claude-1000` works. Worth knowing for briefs that tell agents to grep their scratch copies.
