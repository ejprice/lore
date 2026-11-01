# #165 wave state, lead-165 (snapshot 2026-11-01 00:05Z, written before the 2nd compaction)

lead-base v13 · brief-base **v25** (changed by ANOTHER session at 19:44Z; no v24 backup; operator asked whether it
was intended, no answer yet) · lore_comms session `fix-165-2026-10-31` · progress cron `eac1b6d8` (CronDelete it at
close-out). HEAD `99c2b8e`.

## Commits this wave (feat/surreal-unification, no AI attribution in any)
| sha | what |
|---|---|
| 4d6d038, 26c3a20 | agent overrides re-synced, then deleted (#556) |
| bb61542, 6f0f09f, 4f6c244, 1b8887d, e49d0cb, 14372d1, 4e615b5 | #165 fix + A1/A8/T1 + prose + T8 fake + CLAUDE.md TEST SCOPE + fresh-path parity + docs |
| 8d8b2fa | root `conftest.py` :18500 guard + contract `skills/lore-deploy/tests/test_prod_store_guard.py` |
| c99210b | guard: every-phase pins (fixture scopes, collection, skip/xfail) |
| 308251f | guard audit fixes: 0.0.0.0/::/alias/bytes refused, reuse `lorerunes.posture.host_is_loopback`, "made while" wording; `conftest.py` is a typecheck root |
| eba0a46 | guard: destination-spelling pins (91); #567 xdist flake fixed (SO_REUSEPORT stubs) |
| ef56833, 08acd90 | #566 gated_ground: an ancestor conftest of a testpath is execution-covered |
| 699b058, 169539d, 7356fdf, 5da0891, 3c0869d | #566 C2/C3 + #569: ONE `_pytest_loads_conftest` for verdict + memo key, norecursedirs (ini replaces defaults, whole subtree), drift pin, docs, #570 KNOWN BOUND pin, #571 subtree/configured pins |
| 0c7477c | #568 contract `skills/lore-deploy/scripts/test_scaffold_slug.py` + fixture alignment in test_lore_deploy.py |
| 7d79115 | #572 build CHECKPOINT (impl-572-ledger, retired): lead re-run 419P/0F, sha256 ad23a318… matches. Forks: F-A (b), F-B stop/status only, F-C status exit 0. Flags 1/3/5 → residual finding; flag 2 docs + flag 4 record() → audit |
| 94d3a0d | #572 contract r2 (test_ledger_572.py + 7 C-DEF rewrites + C1–C6): lead re-run RED 57F/362P all AssertionError; SAT 419P/0F (author). F-1 (a), F-2 (a) accept re-index (cost unmeasured → operator) |
| f247deb | #568 audit fixes (GO): lazy slugify, scaffold mode 0644, --project help. Audit routed C1–C6 → #572 contract (RULING-572-addendum-568-audit.md, directive #18019); A7 accepted residual |
| 99c2b8e | #568 build: `loremaster.config.derive_project_slug` (python-slugify, `_`), `lore_deploy._project_slug` resolver at all 8 sites, collision refusal, `project_path` meta row, backfill. CHECKPOINT before its audit |

## Live agents (both started ~23:59Z; spawns start only at the lead's next turn, see feedback draft)
- RETIRED: `audit-568-slug` (tdd-refactorer, opus, Phase 5 of 99c2b8e). Report `REPORT-audit-568-slug.md`.
  - Brief: cold review first; make the slugify import LAZY (the server must not need it at boot); judge the
    builder's 2 readings; one mutation.
  - Directive #18018: "stop on unreadable config". `stop` now refuses when lore.yaml is unreadable; judge,
    fix or route.
- `audit-572-ledger` (tdd-refactorer opus, ~00:33Z, 90 min; writable lore_deploy.py + 3 skill docs). RETIRED: `impl-572-ledger` (tdd-implementer opus, spawned ~00:25Z, deadline 2h; writable lore_deploy.py only). RETIRED: `contract-572-ledger` (tdd-light-contract). Report `REPORT-contract-572-ledger.md`. Pins per
  `RULING-572-ledger.md`:
  - the provisioned marker is written only after a successful index;
  - "provisioned" follows the marker;
  - status shows no ledger-derived counts and points at the store.
- Both write NEW files only; they share lore_deploy.py via the audit's writable set.

## Remaining steps, in order
1. DONE 00:10Z: audit-568 verified (348 passed re-run, md5 match), committed f247deb, retired.
2. Verify the #572 contract RED + satisfiability → commit → `tdd-implementer` (opus, `impl-572-ledger`) → verify →
   commit → a short Phase 5 audit (tdd-refactorer opus) → commit.
3. **The packet's ONE full suite** (the root conftest + gated_ground + slug changed after the last full run):
   - run it under `flock /tmp/lore-full-suite.lock`, `-n 12`;
   - set-diff it against `/var/tmp/claude-1000/a165-full-failed-ids.txt` (530 ids; normalise with
     `awk '{print $1}'`, because the baseline truncates at whitespace);
   - expected: 530 owned packet-58/64b reds, plus 0 new.
4. Close-out:
   - Lore writes BEFORE acceptance:
     - resolve #165, #186 (with the #166 bound note), #566, #567, #569, #571 and #568;
     - #570 stays open as a pinned bound; #572 stays open (SurrealManifest move);
     - `lore_remember` successors of the "lore-lore hand-rolled mount" gotcha.
   - File one residual finding for the LOWs:
     - #564 items;
     - the S2 over-claiming failure message in test_gated_ground.py;
     - the private-API `python_files` drift helper;
     - `--ignore` / `__pycache__` / conda shapes (#570 class);
     - the F6 symlinks;
     - the predicted-not-run guard pins (no adversary in tdd-light);
     - the trailing-slash testpath;
     - `TEST_STORE_PORT` not derived.
   - `git mv` every root `REPORT-*.md` from this wave into this dir, plus the gate logs already here, and commit.
     NOT `REPORT-builder-63c-i-a-fix.md` or `REPORT-sidecar-63c.md`: they belong to another wave. Ask the operator.
   - INDEX Log line.
   - MEMORY.md landmine: "do NOT lore-deploy start lore-lore" becomes "safe since bb61542; #166 bound".
   - Retire lead-165; CronDelete `eac1b6d8`.
5. **ACCEPTANCE, LAST (operator):** `lore_deploy.py stop` + `start` on lore-lore, on the CURRENT image (deploys are
   pre-authorized). It recreates the container, and 11c is open, so the ~3h48m cold reindex (#355) may fire.
   - Capture `podman inspect lore-lore --format '{{.Config.CreateCommand}}'` first.
   - Pass:
     - the boot log shows `index.tier.skip` ×3;
     - Uvicorn binds 9202;
     - the `lore_index()` smoke works;
     - Mounts show ONE snapshot bind at /home/lore/docker/mcp/lore-snapshot (no /source).
   - Note: the current image runs OLD baked code, so slugify is not needed in it.
6. Ask the operator:
   - the scratch dirs under /var/tmp/claude-1000 (*-scratch; my rm -rf is denied);
   - the stale `source-trace-165-r3` / `source-history-165-r3` panes still listed by ListAgents;
   - brief-base v25;
   - the hook-indexed CLAUDE.md line;
   - the image rebuild timing;
   - and end with: "There are 530 failing tests unrelated to our present scope. Do you want to examine them more
     closely?" (re-count from the full suite).

## Rulings (files in this dir)
- RULING-F1-pin4, S1-S2, A1-A8-T1, fresh-path, prose-followup, AMENDMENT-contract-r2 (earlier rounds).
- RULING-guard-forks.md (+ Addendum: D1–D3 kept, the ∀ phase property).
- RULING-568-slug.md (F1–F5, Addendum F4b (b), class lift, backfill correction).
- RULING-572-ledger.md (operator: deploy-side ledger now).
- Lead rulings recorded in commits/reports:
  - #570 as a pinned bound;
  - D-1 `host_is_loopback` is not lowercased;
  - F1/F2 of guard-r2;
  - C6 root cause accepted.

## Findings filed this wave
#551–#555, #556 (resolved), #557, #558, #559→#563, #560, #561/#562 (resolved), #564, #565 (currency --legs prints FAIL),
#566, #567, #568, #569, #570, #571, #572.

## Operator answers this wave (post-first-compaction)
Guard at the repo root · fix #568 this wave · acceptance last · F4 refuse loudly · #572 deploy-side ledger now.

## Added after the 2nd compaction
- #573 filed: wire_test_*.memory.db strays in the real ~/.local/state/lore (2026-09-26); ask operator whether in scope.
- A7 accepted residual (goes into the LOWs finding).
- Residual-finding additions: `_validate_config_schema` child traceback (builder flag 1); permission-denied ledger READ unpinned (flag 3); F-2 re-index cost unmeasured (operator).
