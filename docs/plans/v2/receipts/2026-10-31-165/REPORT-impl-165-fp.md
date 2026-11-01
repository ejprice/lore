# REPORT-impl-165-fp — fresh-path parity GREEN (lore #165, RULING-fresh-path items 1+2)

brief-base v24 read · brief project v7 read
- **State:** done. GREEN measured 2026-10-31 on HEAD `1b8887d` + this uncommitted diff to `skills/lore-deploy/scripts/lore_deploy.py` (only file touched besides this report).
- **Deviations:** none. Capability: grep is hook-denied on this checkout (even over /var/tmp logs) → lore_impact / Read / tail used instead; filed as finding #562.
- **Packages considered:** none — no mechanism specified (reorder + extracted try/except).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 3 new symbols (`_launch_or_exit_loudly`, `_LAUNCH_FAILURES`, `_LAUNCH_RETRY_REMEDY`), all EXTRACTED from the A1 recreate handler; both paths call the one helper (§DRY ledger).
- **Graded:** `1b8887d` · HEAD-at-report: `1b8887d` · SAME.
- **GREEN:** brief's scope `227 passed`, EXIT=0, 0 failed (`/var/tmp/claude-1000/impl165fp-green.log`); class-only `TestVerbStartFreshPathParity` **9 passed** by node id (`/var/tmp/claude-1000/impl165fp-class.log`). RED baseline (lead): 9 failed / 162 passed.
- **Gates:** ruff exit 0; typecheck 83 `error:` = baseline, 0 in lore_deploy.py.
- **Decisions needed:** (1) fresh-launch failure message omits "the exited container was already removed" — plain form picked, conditional alternative written in §Anything noticed #1; (2) `_LAUNCH_FAILURES` hand-mirrors `_launch_container`'s `Raises:` with no matching test (#2).
- **NOT TRIED:** the mutation proof that both paths share `_LAUNCH_FAILURES` (refactor/audit phase).
- **Pointers:** §The diff · §DRY ledger · §Removed-behaviour inventory · §GREEN + gates · §Anything noticed.
- Fan-out: haiku 3 · sonnet 0 · peak 2 (the third runner was the class-only confirmation run).

## Routing table (written before any read beyond brief + brief-base)

| step | tier | who | reason |
|---|---|---|---|
| A. Lookups: `verb_start` both paths, `_launch_container`, recreate-path handler (A1), `TestVerbStartFreshPathParity` 9 pins, RULING-fresh-path.md | 3-feeding lookups, run as ONE parallel batch | self | brief routes it; set size = 4 spans (lore_deploy.py verb_start region, test class, ruling, recreate handler) — small, I read all of it, on critical path |
| B. Implementation (reorder + shared error helper) | 3 | self | brief: inline; design of the shared helper is judgment |
| C. Test run (brief's exact command) | 1 | haiku-runner | brief routes it |
| D. Gates ruff + typecheck | 1 | haiku-runner | brief routes it; parallel with final C |
| E. Coverage sweep: other `_launch_container` / `podman rm -f` call sites in lore_deploy.py | 1-sized, inline grep (literal, non-symbol textual) | self | one grep, output ~few lines, read whole; grep fallback said out loud |

Coverage line for row A: 4 spans read whole — `RULING-fresh-path.md` (25 lines), `verb_start` (lore_get_symbol, index at `1b8887d`), `_FreshPathArrangement` + `TestVerbStartFreshPathParity` (test_lore_deploy.py, working tree, Read), `_launch_container` (Read). Row E ran as `lore_impact(_launch_container)` instead of grep: grep on the main checkout is hook-denied ("lore main checkout is live-indexed"), so the lore route was the only one; result `direct_consumers: [verb_start]`, 1 prod ref.
| F. Class-only confirmation run (`TestVerbStartFreshPathParity`, -v) | 1 | haiku-runner | added after C: shows the 9 pins are collected and PASSED by node id, not just "0 failed" in a superset |

Fan-out: haiku 3 · sonnet 0 · peak 2

## The diff (`skills/lore-deploy/scripts/lore_deploy.py`, symbols not lines)
- NEW `_LAUNCH_FAILURES` (module constant): `(RuntimeError, subprocess.CalledProcessError)` — the `Raises:` set of `_launch_container`, one tuple for both paths.
- NEW `_LAUNCH_RETRY_REMEDY` (module constant): the shared message tail "fix that cause and retry `start`."
- NEW `_launch_or_exit_loudly(project, config_path, env_file, *, launch_label, aftermath) -> int`: calls `_launch_container`; on `_LAUNCH_FAILURES` prints `start: {launch_label} of lore-<slug> failed ({error}); {aftermath}` to stderr and returns `_EXIT_ERROR`; else `_EXIT_OK`. This IS the A1 handler, moved out of `verb_start` (One Implementation).
- `verb_start` recreate path: inline A1 try/except replaced by a call with `launch_label="relaunch"`, `aftermath=f"the stale container was already removed — {_LAUNCH_RETRY_REMEDY}"` — composes to the same bytes as before.
- `verb_start` fresh path (item 1): `if state is not None: _run(["podman","rm","-f",…])` moved from BEFORE the image check to AFTER `_probe_surreal`, immediately before the launch.
- `verb_start` fresh path (item 2): bare `_launch_container(...)` replaced by `_launch_or_exit_loudly(..., launch_label="launch", aftermath=_LAUNCH_RETRY_REMEDY)`; non-OK returns `rc`.

## DRY ledger (brief-base §6)
| new symbol | where I looked | what it returned | disposition |
|---|---|---|---|
| `_launch_or_exit_loudly` | brief-named owner (A1 handler, `6f0f09f`); `lore_search` "launches the container and turns RuntimeError or CalledProcessError into _EXIT_ERROR" scoped to lore_deploy.py; `lore_impact(_launch_container)` | the only owner is the inline A1 block inside `verb_start`'s recreate branch; search returned no other helper; `_launch_container` has one prod consumer (`verb_start`) | EXTENDED the A1 handler: extracted it to a function and parameterised the two words that differ (subject, aftermath). Both paths now call it; no second copy. |
| `_LAUNCH_FAILURES` | same | the tuple existed only inline in A1 | EXTRACTED from A1 (same members) |
| `_LAUNCH_RETRY_REMEDY` | same | the string existed only inline in A1's message | EXTRACTED from A1 (same bytes) |

Sharing proof: both paths route through `_launch_or_exit_loudly`; the recreate pins (A1) and the fresh pins (`test_a_failed_fresh_launch_exits_loudly_with_the_errors_text`) both exercise it. A mutation run (e.g. dropping `CalledProcessError` from `_LAUNCH_FAILURES` must redden BOTH paths' CalledProcessError pins) was NOT TRIED — it is the refactor/audit phase's proof per §6, not run here.

Packages considered: none — no mechanism specified (a reorder + an extracted try/except; nothing a package does).

## Removed-behaviour inventory
1. **Fresh path, exited container removal moved later.** Before: `podman rm -f lore-<slug>` ran first, so every refusal (image, env file, snapshot, config read, embed, store) still destroyed the exited container. After: it runs only when all six pass, right before launch. Adjudication: changed-deliberately, RULING-fresh-path item 1; pinned by the 6-way parametrised `test_a_refused_fresh_start_leaves_the_exited_container_in_place` + the positive control.
2. **Fresh path, launch failure no longer raises.** Before: a `RuntimeError`/`CalledProcessError` from `_launch_container` propagated raw to the dispatcher. After: `_EXIT_ERROR` + stderr. Ruling item 2; pinned by both parametrised cases.
3. **Recreate path message:** unchanged bytes (composition verified in the diff). Preserved; its A1 pins are in the run scope.
4. **New fresh-path stderr text:** `start: launch of lore-<slug> failed (<error>); fix that cause and retry \`start\`.` — new surface, no prior text existed (it used to be a traceback).
5. Side effect order on the fresh path otherwise unchanged: image → env → snapshot gate (incl. config read) → embed → store → [rm] → launch → bind → artifact gates → merge.

## GREEN + gates (measured 2026-10-31 ~14:28-04:00 on the working tree over HEAD `1b8887d` + this diff)
- **C, targeted run** (haiku-runner; its `RAN:` matched the brief's command byte-for-byte). Log `/var/tmp/claude-1000/impl165fp-green.log` (10 lines; I read the tail): `227 passed in 11.94s` · `EXIT=0` · 0 failed, 0 errors.
  - Scope: `. ../tests` (the lead's RED scope: 9 failed + 162 passed = 171 at `1b8887d`) + `loremaster/tests/{test_indexer,test_source,test_static_snapshot_reacquire}.py`. The 56 extra are attributed to those three files — ⚠ inferred, per-file split not measured.
- **F, class-only run** (haiku-runner; `RAN:` matched). Log `/var/tmp/claude-1000/impl165fp-class.log`, tail read by me: `9 passed in 0.24s` · `EXIT=0`; all six `[precondition]` params, the positive control, and both `[launch_error]` params PASSED by node id.
- **D, gates** (haiku-runner; `RAN:` matched). Log `/var/tmp/claude-1000/impl165fp-gates.log`: `RUFF_EXIT=0`; `TC_EXIT=1` with **83 `error:` lines = the brief's baseline**, **0 in lore_deploy.py** (82 in `loremaster/tests/*`, 1 in `scripts/test_forgery_door_sweep.py:42` — all pre-existing per the baseline, none in my writable set).

## Anything noticed / decisions (forks written down, per brief-base §2)
1. **Fresh-path failure wording, two readings.** If a fresh start had an EXITED container, it is now removed just before the launch; if the launch then fails, my message says only `…failed (<error>); fix that cause and retry \`start\`.` and does NOT say the exited container was removed. Alternative: when `state is not None`, use `aftermath=f"the exited container was already removed — {_LAUNCH_RETRY_REMEDY}"` (mirrors the recreate message). I picked the plain form because no test or ruling sentence asks for the conditional and the implementer law says no untested behavior. Under the Trust doctrine the alternative is arguably more honest (a consumer could believe the old exited container — and its logs — still exist). **Recommend the refactor phase or the lead rule on it**; a one-expression change in `verb_start`.
2. **`_LAUNCH_FAILURES` is a hand-mirror of `_launch_container`'s `Raises:` docstring.** Global law: "any hand-list gets a test that it matches its source of truth". No such test exists (and I may not write one). It is at least now ONE list instead of one inline per path. Flagging, not fixing.
3. **Pre-existing, outside scope: typecheck is RED (83 errors) in `loremaster/tests/*` and `scripts/test_forgery_door_sweep.py`** — names like `TaskLedger._guarded_append_fragment`, `loremaster.tasks.SupersedeResult`, `GovernedVerbSpec` that mypy says do not exist. The brief names 83 as the baseline, so it is presumably adjudicated in `scripts/pending_contracts.yaml`; I did not verify that adjudication. Do you want it checked?
4. **Tooling friction:** the PreToolUse hook denies `grep` even over `/var/tmp` log files (not the indexed tree), so log inspection had to go through `tail`/Read. Filed below as a lore finding.
5. `verb_start`'s docstring still lists "NOT running → standard launch path" without the new order; accurate but silent on item 1. Left as is (the refactor phase owns prose).
6. A2/A4 (RULING "Also in this round") NOT TOUCHED — brief assigns them to the refactor phase.
