# PLAN — #165 stopgap: lore-deploy binds the snapshot where the server reads it

Lead: lore-fix session (2026-10-31). Read with: `lead-base v11`, `brief-base v23`.
Evidence: the source-trace / source-history reports (r1–r3) in this directory, all three runs in agreement.

## Rulings already made (operator, 2026-10-31)
- **Cycle:** tdd-light, **contract-adversary WAIVED** for this fix only (project law normally requires one).
- **Pin 4 IN:** refuse to launch when static roots are configured but the host snapshot is missing.
- **`/source`:** REPLACE, don't add. Three independent runs: 0 readers, no dependents (#165 option A).
- **Timing:** ship now, ahead of packet 19. Packet 19 still owns removing the underlying cause (#166).

## The change (production)
`skills/lore-deploy/scripts/lore_deploy.py::_launch_container`:
1. Replace `-v {SNAPSHOT_ROOT}:/source:ro` with `-v {SNAPSHOT_ROOT}:{CONTAINER_HOME}/docker/mcp/lore-snapshot:ro`.
2. Static roots configured AND `SNAPSHOT_ROOT` absent on the host → refuse the launch loudly. Today the bind
   is silently skipped, and that becomes the same boot crash. The error names the missing host path and the
   cold-index remedy (`python -m loremaster.index --config …`). No `podman run` is issued.
3. Fix the docstring.

## Contract (pins)
1. **Derived target.** With ≥1 static root, the bind target equals `CONTAINER_HOME` +
   `loremaster.server._DEFAULT_SNAPSHOT_ROOT.relative_to(Path.home())`, imported from loremaster, never retyped,
   so it goes RED if the server's path moves. Discovery confirms the skill test env imports loremaster.
2. **Artifact pin (the instrument #165 says is owed).** Capture the exact command `_launch_container` builds
   and run it against the REAL image as `--rm --network=none` with a python entrypoint. Assert
   `Indexer._snapshot_materialized` is True for every static tier of `lore.yaml`, with a POSITIVE CONTROL
   (the same guard pointed at an unbound path reads False). Probe design: REPORT-source-trace-165-r3
   §Execution probe. If podman or the image is missing, FAIL LOUD; never skip silently.
3. **No static roots → no snapshot bind** (today's behaviour, preserved).
4. **Missing host snapshot + static roots → launch refused**, with a teaching error, and no `podman run` call.

## Removed-behaviour inventory
| behaviour | verdict |
|---|---|
| `/source:ro` bind | dropped deliberately: 0 readers at HEAD and in image `4312207128bb` (r1–r3 sweeps + in-image probes) |
| silent skip of the bind when the host snapshot is missing | dropped deliberately → loud refusal (pin 4) |
| docstrings/comments claiming the server reads `/source` | old-bug (false since `407d7f7`), corrected |

## Live prose to correct (from the r3 history report §Q5; LIVE-INSTRUCTION rows)
- Containerfile comments: lines 8, 102, 167, 186.
- `skills/lore-deploy/references/lifecycle.md` 18, 19, 146.
- `lore_deploy.py` 662 (docstring) and the deploy-test comments at 39 and 219.
- Docstrings: `loremaster/source/snapshot.py` 6 and 70, `index/indexer.py` 395, and `server.py::build_app_context`
  ("also the read-file static base", which is stale). Also `tests/test_source.py:6`.
- `docs/plans/v2/65-hosted-write-joint-cutover.md:130`: the "`/source:ro` ×2" check would flag a correct
  container. Rewrite it for the single-bind shape.
- `INDEX.md:581` (standing landmine) gets rewritten; `INDEX.md:269` and `19-lore-deploy-rework.md:15,22` get an
  annotation, not a rewrite.
- `docs/design/2026-08-01-google-auth-restart-runbook.md:87`.
- Off-repo: the `MEMORY.md` landmine ("do NOT lore-deploy start lore-lore") gets updated, and the lore memory
  gotcha notes get `lore_remember` successors.
- Dated INDEX Log entries and receipts are HISTORICAL; leave them.

## Pipeline (each step's routing per lead-base v11)
| # | step | who | routed work |
|---|---|---|---|
| 0 | discovery: `lore_impact(_launch_container)` covering tests; confirm the skill test env imports loremaster | lead | — |
| 1 | contract: pins 1–4 | `tdd-light-contract` (Opus) | test runs → `haiku-runner`, exact capped command |
| 2 | stub + confirmed RED | `tdd-stub` with per-call `model: opus` (lore roster) | RED run → `haiku-runner` |
| 3 | GREEN | `tdd-implementer` with **per-call `model: opus`**. The global definition pins sonnet, and lore's project overrides were deleted (#556, `26c3a20`). Read the resolved model off the child transcript | test runs → `haiku-runner` |
| 4 | prose corrections | code docstrings: implementer; doc and runbook wording: an `opus55-worker` (wording is never Haiku) | exact-string edits the lead fully specifies → `haiku-worker` |
| 5 | audit (fresh context) | `tdd-refactorer` with per-call `model: opus` (tdd-light rule; global pin is sonnet) | gate runs → `haiku-runner` |
| 6 | acceptance: `lore_deploy.py stop` + `start` on lore-lore (~3 min down) | lead | boot log must show `index.tier.skip` ×3 + Uvicorn bound on 9202; `lore_index()` smoke. Rollback = the saved CreateCommand in the session scratchpad |
| 7 | close-out | lead | below |

**Test scope (lore law):** targeted only, never `-n auto`.
- Run the skill idiom `cd skills/lore-deploy/scripts && uv run python -m pytest -q . ../tests`, plus the
  `lore_impact` covering tests for each edited docstring file.
- Wrap every run as `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 …` with `-n 8` or fewer.
  A green claim needs the passed count.
- Gates: `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` (no pytest), which
  must show RED_ORPHANED 0.

## Close-out
- Commits, one concern each, with **no AI attribution** (global rule): (a) fix + tests; (b) prose; (c) receipts.
  The receipts commit archives every `REPORT-source-*-165*.md` plus this plan into this directory.
- Ledger:
  - Resolve **#165** and **#186**, with a note that the stopgap shipped and packet 19 still owns #166.
  - Name the bound left open: an in-container re-acquire can never succeed (unmounted corpora, `:ro` snapshot).
    A version bump or `rebuild_all` still crashes boot.
- INDEX Log line; MEMORY.md landmine update.
- Leave **#548** (the retry warning has no exc_info) and **#339** (no restart policy) open; they are not this fix.

## Open decisions for the operator
- **D1 full suite:** recommend NOT running it. The loremaster edits are docstring-only and the behaviour
  change is in the skill. Targeted tests + typecheck/ruff currency.
- **D2 file the four flags from the r2/r3 runs:**
  - lore_search can't exclude a path (prior reports leak into "independent" runs);
  - `lore-demand_intelligence` is on an old image and was stopped uncleanly;
  - a legacy SQLite `lore.db` open at boot;
  - the snapshot-root path is hardcoded in 4 places (the ONE-IMPLEMENTATION root of #165).

## Amendments (2026-10-31)
- F1 ruled: `RULING-F1-pin4.md` (refusal at both levels, before teardown; R1 one predicate; R2 malformed config).
- S1/S2 ruled by the operator: `RULING-S1-S2.md` (per-tier refusal via ONE loremaster-owned materialisation predicate;
  a regular file at the root is refused).
- #556: project agent overrides deleted; builder roles take per-call `model: opus`.
