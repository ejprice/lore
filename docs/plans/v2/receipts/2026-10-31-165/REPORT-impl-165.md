# REPORT-impl-165: lore #165 GREEN (tdd-light implementer), 2026-10-31

## SUMMARY
brief-base v24 read · brief project v7 read (lore_comms impl-165, session fix-165-2026-10-31)
- **State:** done. Capability check: everything the brief demanded was available. One Bash grep was DENIED by the repo's live-index hook and re-routed to lore_get_symbol, with no fallback grep.
- **Deviations:** none. No test or out-of-set file touched. Prose-wave docstring edits in snapshot.py/indexer.py were kept in place.
- **Packages considered:** none: no mechanism specified (stdlib `pathlib` predicate + the existing `_read_config_field` seam).
- **Odoo-20 portability:** n/a: no Odoo seam touched.
- **Reuse ledger:** 8 new symbols, all dispositioned (§DRY ledger). The predicate MOVED to `SnapshotLayout.is_materialized`; `Indexer._snapshot_materialized` delegates; lore_deploy evaluates it through `_read_config_field`.
- **Graded:** 26c3a20 (working tree on top) · HEAD-at-report: 26c3a20 · SAME.
- **GREEN, measured 2026-10-31 ~17:20Z.**
  - RAN (haiku-runner, `RAN:` checked = mine): base scope + 3 added files.
  - Log `/var/tmp/claude-1000/impl165-green-final.log`, tail read by me: **`234 passed in 11.81s`, EXIT=0**, 0 failed, no collection errors.
  - Base-scope run alone: `198 passed` (= RED's 17F + 181P at 26c3a20; log `impl165-green-r1.log`). The real-image pin 2 passed in both runs.
- **Added covering-test files (step C):** `loremaster/tests/test_static_snapshot_reacquire.py`, `test_indexer_bulk_sweep.py`, `test_graph_wiring.py`. That is 234 − 198 = 36 added tests.
- **Gates (haiku-runner, log `/var/tmp/claude-1000/impl165-gates.log`, read by me):**
  - ruff on the 3 files: `All checks passed!`.
  - typecheck: 83 `error:` lines (loremaster 82 + scripts 1). That equals the 83 RED_ADJUDICATED residuals, so **0 added**. 0 lines name my 3 files, and the `skills` leg (lore_deploy) is OK.
- **Fan-out:** haiku 3 (2 test runs, 1 gate run) · sonnet 0 · peak 2.
- **Decisions needed:** none blocking. Flags F1–F6 are in §Noticed.
- **Pointers:** §Routing table · §Step C (covering-test derivation + its bound, finding #559) · §Files changed · §DRY ledger · §Noticed.
- **NOT TRIED:** the optional comparison against the reference build `/var/tmp/claude-1000/c165-r2-scratch` (the brief says MAY). Mutation proof and audit are not mine (brief).


brief-base v24 read · brief project v7 read · registered lore_comms impl-165 (fix-165-2026-10-31)

## Routing table (written 2026-10-31T16:48Z, before any read beyond the brief + brief-base)
| step | tier | who | reason |
|---|---|---|---|
| A. Lookups: read the 3 reuse sites (`SnapshotLayout`, `Indexer._snapshot_materialized`, `lore_deploy._read_config_field`/`_loremaster_python`/`_schema_load_snippet`), `_launch_container`, `verb_start` (pre-teardown block + R3 handler), the contract test file, and the 3 ruling docs + plan §The change | inline, ONE parallel batch (~10 reads) | me | brief routes inline; small, on the critical path, read in full — a Haiku summary would drop exact call shapes/stub behaviour I must code against |
| B. Implementation | 3 (inline) | me | judgment; brief routes inline |
| C. Covering-test derivation (`lore_index(reconcile=True)` + 4× `lore_impact`) | inline, 5 lore calls as one batch | me | brief routes inline |
| D. Test runs | 1 | haiku-runner | brief routes it |
| E. Gates (ruff + typecheck) | 1 | haiku-runner, parallel with final D | brief routes it |

## Step A receipts (2026-10-31 ~16:55Z, HEAD 26c3a20)
Batch: 4 Reads (contract file, snapshot.py, rulings, amendment/plan) + 6 `lore_get_symbol` (Indexer._snapshot_materialized, _launch_container, verb_start, _read_config_field, _schema_load_snippet, _loremaster_python) + 1 Read (lore_deploy.py constants 1-130) + 2 lore_search (LoreConfig.effective_roots, _RecreatePathFixture). Coverage: 13/13 reads returned content.
Note: one Bash grep was DENIED by the repo's PreToolUse hook ("lore main checkout is live-indexed"); re-routed to lore_get_symbol, no fallback grep.
- `effective_roots` returns `roots` verbatim when non-empty and synthesises a LIVE root otherwise, so the static set is identical over `c.roots`; I keep `c.roots` to match the existing count expression.

## Step B: implementation (2026-10-31 ~17:05Z)
## Step D r1 (base scope), measured 2026-10-31 ~17:10Z on the working tree over HEAD 26c3a20
RAN (haiku-runner; RAN line checked = my command): `cd skills/lore-deploy/scripts && systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q . ../tests ../../../loremaster/tests/test_indexer.py ../../../loremaster/tests/test_source.py --timeout=300 -p no:cacheprovider -n 8 -rf`
Log `/var/tmp/claude-1000/impl165-green-r1.log`, tail read by me: `198 passed in 10.51s` · EXIT=0 · no skips, no collection errors. (RED at 26c3a20 over the same scope: 17 failed, 181 passed = 198.)

## Step C: covering-test derivation (2026-10-31 ~17:12Z)
`lore_index(reconcile=True)` ran (sweep at 16:55:27Z; the watcher had already indexed my edits: `lore_impact SnapshotLayout.is_materialized` resolves its one consumer, `Indexer._snapshot_materialized`). Workspace root `/workspace` @ `feat/surreal-unification` 26c3a20, the same tree.
| target | lore_impact covering tests → FILES |
|---|---|
| `SnapshotLayout` | 244, **+229 elided**, shown are all `test_indexer` (in scope) |
| `Indexer._snapshot_materialized` | "41 across 1 file": `test_launch_snapshot_bind.py` (in scope) |
| `_launch_container` / `verb_start` | 108 (+93) / 172 (+157) elided; shown are all skill-dir tests, covered by `.` + `../tests` |
| `SnapshotLayout.is_materialized` (new) | 0 tests (heuristic) |
| `loremaster.source.snapshot` (module) | rode the bare-name `snapshot` fallback; unioned with store-snapshot test helpers, so I discarded it as noise |
| guard consumers `_index_static_tier` / `_prepare_static_tier_for_collect` | 0 / 0 → went one level up |
| `Indexer._collect_sweep_pending` | "49 across 1 file": **`test_indexer_bulk_sweep.py` → ADDED** |
| `Indexer.index_tier` | 100 (+85 elided), shown are `test_graph_wiring` → **ADDED** |
| (lore_search, because impact cannot trace indirect coverage) | **`test_static_snapshot_reacquire.py` → ADDED**. It is the FP-05 behaviour suite of the very guard I delegated, and NO lore_impact view named it |
**Added files:** `loremaster/tests/test_static_snapshot_reacquire.py`, `loremaster/tests/test_indexer_bulk_sweep.py`, `loremaster/tests/test_graph_wiring.py`.
**Bound (stated):** the elided covering-test entries (229/93/157/85) cannot be listed; no knob widens `max_covering_tests=15`. Filed as **finding #559**. Files hidden behind those elisions are NOT in my scope; the cold audit's full suite covers them.

## Files changed (working tree over 26c3a20; prose-wave uncommitted docstring edits kept in place)
- `loremaster/loremaster/source/snapshot.py`: NEW `SnapshotLayout.is_materialized(tier)`. RULING-S1-S2 puts the "present and non-empty" chokepoint on the module that owns tier→dir.
- `loremaster/loremaster/index/indexer.py`: `Indexer._snapshot_materialized` body now delegates to `self._snapshot_layout.is_materialized(tier)`. The docstring is unchanged, so its meaning is kept (the brief requires that).
- `skills/lore-deploy/scripts/lore_deploy.py`:
  - `_SNAPSHOT_SUBPATH` + `CONTAINER_SNAPSHOT_ROOT`: one subpath feeds the host `SNAPSHOT_ROOT` and the container target `/home/lore/docker/mcp/lore-snapshot`. The dispatcher is stdlib-only and cannot import `loremaster.server._DEFAULT_SNAPSHOT_ROOT`; pins 1 and 2 hold the agreement.
  - `_STATIC_ROOT_COUNT_EXPR` (the existing count expression, now named and shared) + `_COLD_INDEX_MODULE`.
  - NEW `_unmaterialised_static_tiers(config_path)`: evaluates `SnapshotLayout.is_materialized` over the HOST root, inside the loremaster venv, THROUGH `_read_config_field`. It returns `{tier: dir}` for failing tiers.
  - NEW `_require_launchable_snapshot(config_path) -> bool`: the ONE R1 decision + message. It counts static roots FIRST and runs the per-tier check only when count > 0 (the existing-stub constraint from the brief). It raises `RuntimeError` naming each failing tier + dir, the host root, and `` `python -m loremaster.index --config <real path>` ``. A malformed config raises from `_read_config_field` (R2).
  - NEW `_gate_snapshot_precondition(config_path, container_name) -> int`: the ONE verb_start try/print block, in the `_probe_embed`-style `rc` idiom.
  - `_launch_container`: calls `_require_launchable_snapshot` before building/issuing anything. It binds `{SNAPSHOT_ROOT}:{CONTAINER_SNAPSHOT_ROOT}:ro` and never `/source`. The silent `SNAPSHOT_ROOT.exists()` skip is gone. The docstring is rewritten.
  - `verb_start`: `_gate_snapshot_precondition` runs on the recreate path after the env-file check and BEFORE the embed/store probes and stop/rm, and on the fresh path after the env-file check, before the probes and the launch.
  - R3: the relaunch `CalledProcessError` message now interpolates `{error}`, which carries the command and exit status.

## DRY ledger (brief-base §6)
| new symbol | where I looked | what it returned | disposition |
|---|---|---|---|
| `SnapshotLayout.is_materialized` | brief (named owner); `lore_get_symbol Indexer._snapshot_materialized`; `lore_search "directory exists and is non-empty any(iterdir()) materialised snapshot tier check"` | the only body was the Indexer guard; no other copy in the top hits (3 of 11 shown, the rest elided by budget) | **EXTENDED `SnapshotLayout`**: the rule MOVED from `Indexer._snapshot_materialized`, which now delegates. No second copy remains |
| `_unmaterialised_static_tiers` | brief: `_read_config_field` / `_schema_load_snippet` / `_loremaster_python` | the seam runs one expression over `c` in the loremaster venv | **REUSED `_read_config_field`** (+ `SnapshotLayout.materialization_dir`/`is_materialized` inside the expression); no host-side `is_dir`/`iterdir` |
| `_require_launchable_snapshot` | brief (R1 says build one); the old inline count in `_launch_container` | the count expression existed inline | **EXTENDED**: the existing count is now a named constant inside the one R1 helper |
| `_gate_snapshot_precondition` | `lore_search` over lore_deploy.py for a precondition/gate helper; existing `_probe_embed`/`_probe_surreal` | no generic "RuntimeError → stderr → _EXIT_ERROR" wrapper exists; probes return rc themselves | **HAND-ROLLED** in the existing rc idiom; it is the single try/print block (the reference build duplicated it, and the brief forbids that) |
| `_SNAPSHOT_SUBPATH`, `CONTAINER_SNAPSHOT_ROOT` | `loremaster.server._DEFAULT_SNAPSHOT_ROOT` (the owner) | importable only in the loremaster venv; this dispatcher is stdlib-only (its module docstring) | **HAND-ROLLED** mirror. Pin 1 derives the target from the server constant and pin 2 runs it in the real image, so drift goes RED |
| `_STATIC_ROOT_COUNT_EXPR`, `_COLD_INDEX_MODULE` | the existing inline literal | — | **EXTENDED** (named the existing literal) / new constant for the remedy text |

Packages considered: none: no mechanism specified (a path predicate + a subprocess seam that already exists; `pathlib` is the stdlib owner of `is_dir`/`iterdir`).
Odoo-20 portability: n/a: no Odoo seam touched.

## Step D final + E (2026-10-31 ~17:20Z)
- D final RAN: `cd skills/lore-deploy/scripts && systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q . ../tests ../../../loremaster/tests/test_indexer.py ../../../loremaster/tests/test_source.py ../../../loremaster/tests/test_static_snapshot_reacquire.py ../../../loremaster/tests/test_indexer_bulk_sweep.py ../../../loremaster/tests/test_graph_wiring.py --timeout=300 -p no:cacheprovider -n 8 -rf` → `234 passed in 11.81s`, EXIT=0.
- E RAN: `uv run ruff check <3 files>; ./scripts/typecheck.sh`.
  - ruff `All checks passed!` RUFF_EXIT=0.
  - typecheck legs: lorerunes OK · lorescribe OK · loresigil OK · **loremaster FAILED, 82 errors in 31 files** · skills OK (14 files) · docs/eval OK · **scripts FAILED, 1 error** (`scripts/test_forgery_door_sweep.py:42` SupersedeResult) · shellcheck OK.
  - 82 + 1 = 83 = the adjudicated residual count, with 0 in my files. Per finding #555 I did not use the `--currency` verdict line.

## Noticed (raised, not dropped)
- **F1. Two readings of "evaluate THROUGH this seam" (I picked A).**
  - A: an expression over `c`, passed to the unchanged `_read_config_field`, which imports `SnapshotLayout` via `__import__(...)` inside the expression.
  - B: extend `_read_config_field` / `_schema_load_snippet` with an imports parameter.
  - A keeps the seam's signature and callers untouched; its cost is a dense expression string. B is more readable but widens a shared helper. A refactor-phase call.
- **F2. Double evaluation.**
  - `verb_start` gates (count + per-tier: 2 venv subprocesses), then `_launch_container` re-checks (2 more) per start.
  - It is deliberate: the ruling needs both levels to refuse, and the re-check closes the TOCTOU gap between the gate and the launch.
  - Cost: ~4 short subprocesses per `start`. If that matters, the decision could be passed down, but that changes `_launch_container`'s signature, which the contract calls positionally.
- **F3. Fresh-path order (pre-existing).** `podman rm -f` of an EXITED container runs before every fresh-path precondition, mine included. A refused start still removes an exited (non-serving) container. That is not an outage, but it is a side effect of a refused start. Unchanged; raised for the lead.
- **F4. Remedy path is printed as given.**
  - The remedy prints `config_path` as `verb_start` builds it (`project / "lore.yaml"`). If `main` passes a relative `project`, the paste-ready command is relative, so it is only paste-ready from the same cwd.
  - Confidence MEDIUM: I did not read `main`'s path handling.
- **F5. Known bound, untouched (ruled, #166).** The version-stamp leg of the boot guard is not checked pre-launch.
- **F6. Docs outside my set.**
  - `skills/lore-deploy/references/lifecycle.md` (prose-wave modified) and `docs/plans/v2/19-lore-deploy-rework.md` may need to describe the new refusal and its teaching text.
  - I did not open or edit them: they are outside my writable set and in the DO NOT TOUCH list. Flagged for the lead.
- **Contract-side note (not a defect today).**
  - `_assert_teaches_every_failing_tier`'s "healthy dir not named" check is a substring test. If one static tier name were a prefix of another (e.g. `surrealdb` vs `surrealdb-docs`), a correct refusal would read as naming the healthy dir.
  - The repo's current tiers do not collide. It is a fixture bound for the contract author, not mine to change.
- **Finding #559 filed:** lore_impact covering-test elision (no widen knob) + the guard's own FP-05 suite invisible to every impact view.

## Routing retro (lead-165 question, 2026-10-31 ~17:30Z)
1. Yes: step C. The brief sized it "inline: 5 lore calls"; it grew to 12 + 1 search and I never re-routed or added a row. That is a miss on my side. The mechanical leg (run impact on named targets + one consumer hop, dedupe modules → files, report elision counts) was haiku-worker work. Only the noise calls needed me: discarding the bare-name `snapshot` union and climbing past the 0-test consumers. Those were a Sonnet-draftable key at most. The cost was ~12 large impact dumps in my context.
2. Partly. "5 lore calls" read as a ceiling estimate that I silently exceeded. The brief also implied that `lore_impact`'s module list yields the file set; it does not, because of the elision and the indirect-coverage blind spot. The decisive file (`test_static_snapshot_reacquire.py`) came only from lore_search.
3. Route C as "haiku-worker: impact on these targets + 1 consumer hop → deduped files + elision counts; you adjudicate", and add: "if impact elides or reports 0 tests, lore_search for the changed guard's behaviour suite".
