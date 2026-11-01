brief-base v24 read · brief project v7 read
# REPORT-audit-165-fp: tdd-light Phase 5 REFACTOR + AUDIT, lore #165 fresh-path parity (2026-10-31)

## Summary
- **State:** done-with-deviations. **VERDICT: GO** for the builder's fresh-path diff plus my refactor (measured 2026-10-31 on the working tree over `1b8887d`).
- **Graded:** `1b8887d` + uncommitted `lore_deploy.py` md5 `0037f8bd12c52729fd39ebc69c38ec1e` · HEAD-at-report: `1b8887d` · SAME. File after my refactor: md5 `e7fb230231c4f1f31dbfaa4c87666be8`. Pre-refactor backup: `/var/tmp/claude-1000/afp-real.lore_deploy.py.pre-refactor`.
- **Operator grant used:** audit+fix in place, 2026-09-27 "Keep it" (quoted in the brief). No BRIEF CONFLICT.
- **Deviations:**
  - D1: I added MF1b, the CalledProcessError leg of MF1. It surfaced a 4th RED I had not declared (an older recreate pin). Declaration miss, see §Mutations.
  - D2: builder decision (1) was ROUTED, not fixed. It is a behaviour change with no RED test, and this lens cannot write tests.
- **Packages considered:** none — no mechanism specified (a reorder plus a merged config-read expression).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 2 new symbols, both dispositioned (§DRY ledger). The builder's 3 new symbols were checked for prior art (§Prior art).
- **Mutations (all killed; both-ways diff empty except MF1b +1 undeclared):**
  - MF1 3/3.
  - MF1b 3 declared, 4 observed.
  - MF2 7/7.
  - MF3 3/3, run on the refactored file. Deploy agreement pin + server guard + R1 anchor all moved, so sharing survives the A2 merge.
  - Every mutated file was restored. md5 proven equal to its backup.
- **R5 targeted re-run (after refactor):** `227 passed in 10.81s`, EXIT=0. Same count as the builder's 227. Log `/var/tmp/claude-1000/afp-final.log`.
- **R6 gates:** ruff RUFF_EXIT=0 ("All checks passed!"). typecheck TC_EXIT=1 with 83 `error:` lines, matching the brief's baseline. 0 in `skills/`: 82 in loremaster/tests, 1 in scripts.
- **No full suite:** this packet's one full suite ran at the first audit (`bb61542`). Every change since touches only `skills/lore-deploy`, whose tests are all in R5's scope.
- **Refactors done:**
  - A4: `WATCH_STATIC` through `_WATCH_STATIC_EXPR`; the stale stub-blaming comment was rewritten.
  - A2: ONE read, `_static_snapshot_status` → (count, failing tiers). It replaces `_unmaterialised_static_tiers` + the separate count read. The `'static'` literal in the per-tier expression is gone too.
  - F4: `verb_start` docstring.
- **Decisions needed (ROUTED, one line each):**
  - F1: the fresh-launch failure message omits "the exited container was already removed". Recommended code and pin are in §Findings.
  - F2: `_LAUNCH_FAILURES` hand-mirror. Class fix: `_launch_container` raises ONE documented type. Interim bound: each member is mutation-proven on both paths.
  - F3: the `_gate_snapshot_precondition` wording says "running" only.
  - F6: A2+A4 make the config-unreadable stderr quote a 479-char expression (48 before). Suggest `_read_config_field` names a short label.
- **Fan-out:** haiku 7 (1 worker, 6 runners) · sonnet 0 · peak 3.
- **Pointers:** §Cold findings · §Mutations · §Refactor · §DRY ledger · §Prior art · §Deletion inventory · §Anything noticed.

## Routing table (written before any sweep or read beyond the brief + brief-base)
| step | tier | who | reason |
|---|---|---|---|
| R1 cold diff read + findings | 3 | self (inline, brief-routed) | audit judgment |
| R2 prior-art: lore_index reconcile + lore_search per new symbol | 1-size batch | self, ONE parallel batch (size named in §Prior art) | small, on critical path, I read all of it |
| R3 scratch copies afp-m1..m3 | 1 | haiku-worker | mechanical, exit codes + provenance lines |
| R4 mutation edits | 3 | self, in scratch | mutation design |
| R4 mutation runs | 1 | haiku-runner ×3 | test runs |
| R4 declared-RED sets (collect-only) | 1 | self inline (part of mutation design; the set must be fixed by me before the run) | declaring is judgment; the collect output is short |
| refactors A4/A2 + builder decisions | 3 | self | code edits under operator grant (2026-09-27 "Keep it") |
| R5 targeted re-run | 1 | haiku-runner | test run |
| R6 gates | 1 | haiku-runner | lint/type gate |
| mutation verdicts, final verdict | 3 | self | never Haiku |

## Cold findings (written 2026-10-31 ~14:40-04:00, BEFORE any edit to the real tree; graded file md5 0037f8bd12c52729fd39ebc69c38ec1e on HEAD 1b8887d)
| id | sev | file:symbol | finding | disposition |
|---|---|---|---|---|
| F1 | LOW | lore_deploy.py:verb_start (fresh-path `_launch_or_exit_loudly` call) | The fresh path passes `aftermath=_LAUNCH_RETRY_REMEDY` even when an EXITED container was just removed (`state is not None`). That breaks the helper's own parameter contract ("aftermath: the state the failure leaves behind plus the remedy"). Trust Leg 1: a consumer reading "launch of lore-x failed (...); fix that cause and retry" cannot tell the old exited container (and its `podman logs`) is gone. No test reaches it: both launch-error cells run with `state=None`. | ROUTED (contract). Not fixed here: it changes served behaviour with no RED test first (global TDD law; this lens may not write tests). Recommended code after the pin: `aftermath=(f"the exited container was already removed — {_LAUNCH_RETRY_REMEDY}" if state is not None else _LAUNCH_RETRY_REMEDY)`. Pin wanted: `state="exited"` + failing launch → stderr names the removal; `state=None` → it does not. Other reading of the brief's "fix or route": fix now, pin later. Rejected because it ships a branch no test can see. |
| F2 | LOW | lore_deploy.py:`_LAUNCH_FAILURES` | A hand-mirror of `_launch_container`'s `Raises:`. Each CURRENT member is pinned by behaviour on BOTH paths (MF1 + MF1b below). What no test catches is a NEW raise type. Measured doors the docstring omits, by reading the code: `OSError`/`FileNotFoundError` from `_run` → `subprocess.run` when the podman or loremaster interpreter binary is absent; `ValueError` (`json.JSONDecodeError`) in the per-tier read if the reader's stdout is not JSON. Both need a dependency to vanish or misbehave mid-verb, so they are not doors an honest edit opens today. | ROUTED. Simplest closing rule (removes the responsibility): `_launch_container` wraps its failures into ONE documented exception type at its own boundary, so the catch names one type and nothing is mirrored. That is a design change plus a contract change, so not done here. Interim bound: the tuple is ONE list, and each member is mutation-proven on both paths. Re-open trigger: any new raise or new subprocess call inside `_launch_container` or `_require_launchable_snapshot`. A docstring-parsing test would be a spelling scanner, which needs operator approval, so it is not recommended. |
| F3 | INFO | lore_deploy.py:`_gate_snapshot_precondition` | Its stderr says "any running container is left untouched". On the fresh path the container left in place is an EXITED one. True but narrow since this diff. | ROUTED with F1 (served-text change; same no-test reason). Suggested: "any existing container is left untouched". |
| F4 | INFO | lore_deploy.py:verb_start docstring | "NOT running → standard launch path" is silent on item 1's order (builder #5). | FIXED here (prose only, no behaviour). |
| F5 | — | diff as a whole | Item 1 order and item 2 catch are correct. The recreate message bytes are preserved (composition `f"…already removed — {_LAUNCH_RETRY_REMEDY}"` == old literal). `podman rm -f` keeps `check=False`; a failed rm surfaces as `podman run --name` collision → CalledProcessError → caught, loud. | no defect |

## Declared RED sets (written BEFORE each run; ids from `pytest --collect-only -q` run in skills/lore-deploy/scripts, 227 collected, saved at /var/tmp/claude-1000/afp-collect.txt)
- MF1 `_LAUNCH_FAILURES=(CalledProcessError,)`: fresh `…FreshPathParity::test_a_failed_fresh_launch_exits_loudly_with_the_errors_text[runtime_error_refusal]`; recreate `…RecreateFailureAfterTeardownDegradesToExitError::…[config_unreadable]`, `…[snapshot_vanishes]`.
- MF1b `_LAUNCH_FAILURES=(RuntimeError,)` (added by me, the other leg): fresh `…[called_process_error_podman_run]`; recreate `…RecreateFailureAfterTeardown…[podman_run_fails]`, `…RecreateLaunchFailureCarriesTheErrorText::test_called_process_error_exit_code_and_command_reach_stderr`.
- MF2 rm-before-preconditions: the 6 `test_a_refused_fresh_start_leaves_the_exited_container_in_place[*]` + `test_the_exited_container_is_removed_after_every_precondition_and_before_launch` (7). NOT `TestVerbStartRefusesMissingSnapshotBeforeTeardown[fresh]` (its state is None, so no rm happens).
- MF3 (on the REFACTORED lore_deploy.py, md5 e7fb2302…) `SnapshotLayout.is_materialized` → `return True` after `is_dir()`: `TestDeployPreconditionAgreesWithServerGuard::…[empty]`, `TestOneLaunchPreconditionDecidesBothLevels::…[3-tier_empty]`, `loremaster/tests/test_static_snapshot_reacquire.py::TestStaticSnapshotReacquire::test_matching_stamp_reacquires_when_snapshot_dir_empty`.

## Mutations (measured 2026-10-31 in scratch copies via `scripts/scratch_copy.sh`, each EXIT=0)
Provenance, printed per copy (`lore_deploy.__file__` · `loremaster.__file__` · the spawned `_loremaster_python()` interpreter's `loremaster.__file__`):
- afp-m1: `/var/tmp/claude-1000/afp-m1/skills/lore-deploy/scripts/lore_deploy.py` · `/var/tmp/claude-1000/afp-m1/loremaster/loremaster/__init__.py` · spawned `/var/tmp/claude-1000/afp-m1/.venv/bin/python` → `/var/tmp/claude-1000/afp-m1/loremaster/loremaster/__init__.py`.
- afp-m2 and afp-m3: same shape, each inside its own copy.

Runs were plain capped pytest by haiku-runner, using the brief's R4 command, with LORE_PYTHON set to the copy's venv. I checked every runner's RAN: line against my command and read each log tail myself.

| mutation | declared RED | observed RED | declared−observed | observed−declared | log |
|---|---|---|---|---|---|
| MF1 `_LAUNCH_FAILURES=(CalledProcessError,)` | fresh `[runtime_error_refusal]`; recreate A1 `[config_unreadable]`, `[snapshot_vanishes]` | same 3 · `3 failed, 224 passed` EXIT=1 | ∅ | ∅ | afp-m1.log |
| MF1b `_LAUNCH_FAILURES=(RuntimeError,)` | fresh `[called_process_error_podman_run]`; recreate A1 `[podman_run_fails]`; `TestRecreateLaunchFailureCarriesTheErrorText::test_called_process_error_exit_code_and_command_reach_stderr` | those 3 + `test_lore_deploy.py::TestVerbStartRecreateValidatesBeforeTeardown::test_recreate_launch_failure_is_reported_not_raised` · `4 failed, 223 passed` EXIT=1 | ∅ | +1 (an older recreate pin of the same property; I missed it when declaring, a declaration miss, not a dead-code signal) | afp-m1b.log |
| MF2 fresh `podman rm -f` moved back before preconditions | 6 × `test_a_refused_fresh_start_leaves_the_exited_container_in_place[*]` + ordering control | same 7 · `7 failed, 220 passed` EXIT=1 | ∅ | ∅ | afp-m2.log |
| MF3 (on REFACTORED lore_deploy.py `e7fb2302…`) `SnapshotLayout.is_materialized` → `return True` after `is_dir()` | `TestDeployPreconditionAgreesWithServerGuard[empty]`, `TestOneLaunchPreconditionDecidesBothLevels[3-tier_empty]`, `test_static_snapshot_reacquire.py::…test_matching_stamp_reacquires_when_snapshot_dir_empty` | same 3 · `3 failed, 224 passed` EXIT=1 | ∅ | ∅ | afp-m3.log |

Readings:
- MF1 + MF1b: `_LAUNCH_FAILURES` is SHARED. Removing either member reddens both the fresh path and the recreate path.
- MF2: item 1's order is pinned for all 6 preconditions, plus the positive control.
- MF3: after the A2 merge, the deploy precondition still evaluates the server's own predicate. The server guard's empty-dir behaviour and the deploy's verdict moved together, and the anchored cells caught both.

Restores, md5 equal to backups:
- `lore_deploy.py` m1/m2: `0037f8bd…`.
- `snapshot.py` m3: `247bccfb…`, equal to the real tree's.

## Refactor (real tree; diff vs `/var/tmp/claude-1000/afp-real.lore_deploy.py.pre-refactor`, 65 changed lines)
- **A4:**
  - NEW `_WATCH_STATIC_EXPR` = `__import__('loremaster.config', fromlist=['WATCH_STATIC']).WATCH_STATIC`.
  - `_STATIC_ROOT_COUNT_EXPR` is now built from it. The test `test_both_readers_raise_runtime_error_on_an_invalid_config` still references the constant, and it is still a live production component (below).
  - The false comment ("the expr-substring config-reader stubs misread…") is replaced. It has been false since T8 `1b8887d` (`ConfigReaderFake` execs the real expression).
- **A2:**
  - `_unmaterialised_static_tiers` → `_static_snapshot_status(config_path) -> tuple[int, dict[str, str]]`. It is ONE `_read_config_field` call evaluating `json.dumps([<_STATIC_ROOT_COUNT_EXPR>, <failing-tier comprehension>])`, with the comprehension now gated on `_WATCH_STATIC_EXPR`, not `'static'`.
  - `_require_launchable_snapshot`: `static_root_count, failing = _static_snapshot_status(...)`; `== 0` → False; failing → the same RuntimeError text as before; else True.
  - The docstring now says "no tier is checked on disk". The old "never consults the snapshot at all" became false in the narrow sense: the merged read imports `loremaster.source.snapshot` and builds a `SnapshotLayout` (`os.path.abspath` only, no fs access) even for a live-only config.
  - **Clearer? Yes, net.**
    - One parse answers both questions, which removes a two-read window where the config could change between the count and the per-tier read.
    - Interpreter starts per static-root `start` drop from 4 to 2 (gate + launch re-check).
    - One function fewer.
    - Cost: F6.
- **F4:** the `verb_start` docstring states item 1/2 for the NOT-running path.
- Not touched: `_launch_or_exit_loudly`, `_LAUNCH_FAILURES`, `_LAUNCH_RETRY_REMEDY`, the verb_start bodies. Builder code is unchanged apart from the docstring.

## DRY ledger (my new symbols)
| new symbol | where I looked | what it returned | disposition |
|---|---|---|---|
| `_WATCH_STATIC_EXPR` | `loremaster/loremaster/config.py` (awk literal `WATCH_STATIC`, 1 file); `lore_search` "WATCH_STATIC constant" | `config.py:WATCH_STATIC: Literal["static"]`, the owner | REUSED `loremaster.config.WATCH_STATIC`; the new symbol is only the in-expression import of it |
| `_static_snapshot_status` | `lore_impact(_unmaterialised_static_tiers)` (1 prod consumer, `_require_launchable_snapshot`); the existing count constant | the two halves already existed, split across two reads | EXTENDED `_unmaterialised_static_tiers` (renamed; now also returns the count, composed from `_STATIC_ROOT_COUNT_EXPR`). The predicate stays `SnapshotLayout.is_materialized` (MF3 proves it) |

## Prior art for the builder's new symbols (R2; batch of 4: `lore_index(reconcile=True)` + 3 `lore_search`)
- `lore_index(reconcile=True)`: 4040 files, 1 failed, workspace root `/workspace` @ `feat/surreal-unification` `1b8887d`. It indexes the working tree, so the uncommitted diff was visible: the search returned `_launch_or_exit_loudly` at `lore_deploy.py:828`.
- `_launch_or_exit_loudly`: query "catch a container launch failure and print it to stderr returning an error exit code". Top hit is the helper itself; 10 elided below sim 0.68. No other owner: the old A1 inline block is gone, and this is it extracted.
- `_LAUNCH_FAILURES`: query "tuple of exception types a launch or subprocess call may raise". Top hit is a test (`test_launch_snapshot_bind.py:786`). No production twin.
- `_LAUNCH_RETRY_REMEDY`: same searches. A string constant extracted from A1, with no other copy (the awk sweep for "already removed" in skill tests hit only test prose).
- ⚠ lore_search budget elision hid 10 entries per query. I accepted the top hit plus the impact graph as sufficient for 3 private constants and a helper in one module. Bound: a twin elsewhere in the tree whose semantics differ enough to rank below the top 1 would be missed.

## Deletion inventory (removed-behaviour, per item)
1. `_unmaterialised_static_tiers` (function) → folded into `_static_snapshot_status`. Its only consumer was `_require_launchable_snapshot` (lore_impact, 1 prod / 0 test). Preserved-with-pin: `TestConfigReaderFakeOracle::test_snapshot_precondition_reads_agree_*` (real subprocess, both tier states), `TestDeployPreconditionAgreesWithServerGuard` (4 cells), `TestOneLaunchPreconditionDecidesBothLevels` (9 cells). All in R5 green.
2. The separate count read and its `("", "0")` check → `== 0` on a JSON int. The `""` arm was unreachable: `print(sum(...))` always prints an int. Dropped deliberately; nothing could produce `""`.
3. "Live-only never imports the snapshot module" → now it does (import + abspath, no fs). Spec-silent. RULING-F1-pin4 R1 says the snapshot is not consulted, and on disk it still is not. Flagged here. If an import failure of `loremaster.source.snapshot` should not block a live-only start, that is an operator ruling. I'd rate it implausible: same package, and the image bakes it.
4. The `'static'` literal (2 sites) → `WATCH_STATIC`. Preserved: behaviour is identical while `WATCH_STATIC == "static"`; the R5 static-root cells exercise it.
5. The comment blaming the substring stubs → removed; false since `1b8887d`.

## Anything noticed
- **F6 (INFO, ROUTED):** `_read_config_field`'s error text quotes `{expr!r}`. With A4 + A2, a config that fails validation now produces `start: failed to read "<479-char expression>" from …/lore.yaml: <pydantic error> (not launching …)`. Before, the expression was the 48-char `sum(1 for r in c.roots if r.watch == 'static')` (measured with a capture stub, 2026-10-31). The pydantic diagnosis is still there, just buried. Suggested fix (behaviour change, so it needs a contract): give `_read_config_field` an optional short `label` for the message. No pin asserts the expression text (R5 green).
- **Typecheck baseline:** 83 errors (82 loremaster/tests, 1 scripts). The brief names it as the baseline. I did not verify its adjudication in `scripts/pending_contracts.yaml`. Do you want it checked?
- The builder's report says its R5 scope added 56 tests beyond `. ../tests`. Not re-derived; the 227 total is measured (afp-collect.txt: `227 tests collected`).
- Hook friction: a `sleep` + check chain was blocked (use Monitor). The tooling worked as designed, so nothing was filed.
- Worktrees: none created. Scratch copies `/var/tmp/claude-1000/afp-m{1,2,3}` are restored to their pre-mutation bytes and disposable.
