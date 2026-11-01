brief-base v24 read
- brief project v7 read (lore_comms register, session fix-165-2026-10-31, 2026-10-31T17:53Z)
- State: done (spawned 2026-10-31T17:53Z; deadline 45 min; nothing NOT TRIED)
- Deviations: (1) Containerfile comment :144–149 was wrong on a point older than #165 ("each `start` (delta-reconcile)" runs the batch indexer; it does not). I fixed it because it carried the bare-`python` remedy. (2) Rewrapped one >110-col Containerfile comment line that the first pass left (:104). Both are comment-only (diff: 50 changed lines, 0 non-comment).
- Packages considered: none — no mechanism specified (prose only)
- Odoo-20 portability: n/a — no Odoo seam touched
- Reuse ledger: none (no new symbols)
- Graded: 6f0f09f + working tree (the Sonnet verdict draft, sampled) · HEAD-at-report: 6f0f09f · SAME
- Edits: 7 files, 13 sites (§Per-site edits). Every refusal sentence now says: per-tier, absent/empty/not-a-dir, `is_materialized`, pre-teardown, remedy via lore-deploy's interpreter. The recreate-path relaunch failure exits with the error text.
- Sweeps: pre-edit hits=85 / files_listed=1078; post-edit hits=77 / 1078. Each post-edit hit has its own verdict: LIVE-FIXED 4 · LIVE-OK 16 · HISTORICAL 50 · UNRELATED 4 · STALE-in-tests 3. Verdicts: Sonnet draft 55 H / 4 U / 26 C-L. I sampled 10/10 agreeing, and I adjudicated all 26 C-L rows (§Verdicts).
- Decisions needed:
  - D1: `skills/lore-deploy/SKILL.md` `start` row (:52) does not mention the snapshot refusal. It is outside my writable set (skills/lore-deploy/ root, not references/). The exact edit is in §Flags F1.
  - D2: three test-file hits are stale (listed, not edited, per DO-NOT-TOUCH): `test_lore_deploy.py:39,:219` and `test_launch_snapshot_bind.py:1116`. See §Flags F2.
  - D3: the brief says the check runs "BEFORE any stop/rm/launch, on both paths". On the not-running path, an Exited container is still `podman rm -f`'d before ANY precondition (pre-existing). I wrote "before any teardown on the recreate path" and "before any launch" for the fresh path. Confirm that's the intended claim (§Flags F3).
  - D4: prose-165 D2 ("re-index on the host first" before a version bump) is still unrun and left untouched (lead-owned per RULING-prose-followup).
- Pointers: §Facts · §Per-site edits · §Verdicts · §Post-edit sweep · §Flags
- Fan-out: haiku 2 (2 workers: B, E) · sonnet 1 (C1) · peak 1

# REPORT-prose-165-r2 — live-instruction prose aligned to the final #165 behaviour

## Routing table (written 2026-10-31T17:53Z, before any sweep or read beyond the brief + brief-base)

| step | tier | who | reason / size |
|---|---|---|---|
| A. facts: `git show bb61542 6f0f09f` (lore_deploy.py + snapshot.py hunks), `server-interface.md`, `REPORT-prose-165.md` §Per-site edits + §Follow-up | 3 (brief: inline) | me, ONE parallel batch of 3 reads | brief marks it inline; output feeds wording directly; I would read all of it anyway. Coverage line: 2 commits × 2 paths + 1 doc + 1 report. |
| A'. re-read every site the first pass edited (the set = prose-165's per-site table) | 3 | me, ONE parallel batch once the table is known | the set is FOUND from the prose-165 table (a listed set, not a sweep); each re-read feeds a wording judgment. Size named when listed. |
| B. residual sweep (awk spec in the brief) | 1 | `haiku-worker` | brief routes it; literal command, no judgment |
| C1. verdicts HISTORICAL / UNRELATED / CANDIDATE-LIVE on sweep hits | 2 | Sonnet `general-purpose` | brief routes it; span-decidable; I sample ≥10 rows |
| C2. verdicts on CANDIDATE-LIVE rows | 3 | me | depends on current code (lore_deploy.py / snapshot.py) — a sampled draft would miss whether the wording matches per-tier refusal / interpreter remedy / pre-stop check |
| D. wording edits | 3 | me | brief: doc wording never delegated |
| E. post-edit re-sweep | 1 | `haiku-worker` | brief routes it |

Actuals: A ran as one batch of 4 calls (both commits, prose-165 report, server-interface awk). A' ran as one `git diff` over the 8 prose-165 doc files. I added one unplanned small sweep (A''): `refus|pre-flight|materiali` over the 3 lore-deploy skill docs, coverage `SKILL.md lines=304 · lifecycle.md lines=255 · server-interface.md lines=93`, inline because I read all its output. It found the lifecycle step-1a / step-2 precondition lists and SKILL.md's `start` row.
Fan-out: haiku 2 · sonnet 1 · peak 1.

## Capability check
Demanded: lore_comms register, lore tools, haiku-worker + Sonnet spawns, edits in the writable set. I have all of them.

## Facts behind the wording (read at 6f0f09f, 2026-10-31)
- HIGH: `_require_launchable_snapshot` counts static roots first. A live-only project returns False, so there is no bind and no check. Otherwise `_unmaterialised_static_tiers` evaluates `SnapshotLayout(SNAPSHOT_ROOT).is_materialized(tier)` per static tier through `_read_config_field`, which runs loremaster's own code over the host root. `is_materialized` = `materialization_dir.is_dir() and any(iterdir())`: absent, a regular file, or an empty dir all read False. A config read failure raises too (R2).
- HIGH: `_gate_snapshot_precondition` runs on the stale-image recreate path after the image/env-file checks and BEFORE `podman stop`/`rm`. It runs on the not-running path after the image/env-file checks and before the embed/store probes and launch. Its stderr says "(not launching …; any running container is left untouched)".
- HIGH: the refusal text names `len(failing)` tiers, the config path, the host root, `tier at dir` per tier, and the remedy `` `{shlex.quote(_loremaster_python())} -m loremaster.index --config {shlex.quote(config_path)}` ``. `config_path = project / "lore.yaml"` with `project = Path(args.project).resolve()`, so it is absolute. `_loremaster_python()` = `$LORE_PYTHON` → `~/PycharmProjects/lore/.venv/bin/python` if it exists → `sys.executable`.
- HIGH: on the recreate path, `_launch_container` re-runs `_require_launchable_snapshot` after stop/rm. The handler catches `(RuntimeError, CalledProcessError)`, prints `relaunch of … failed ({error}); the stale container was already removed — fix that cause and retry`, and returns `_EXIT_ERROR`.
- HIGH: `setup` step 7 runs `[_loremaster_python(), "-m", "loremaster.index", "--config", config_path]` on the host. `start` never runs the batch indexer.
- MEASURED 2026-10-31 at 6f0f09f: `uv run --frozen python -c "import loremaster.index, sys; …"` from the repo root printed `/home/ejprice/PycharmProjects/lore/.venv/bin/python3` and `…/loremaster/loremaster/index/__init__.py`, exit 0. That is the same `.venv` `_loremaster_python()` picks, which is why the docs offer `uv run python -m loremaster.index …` for manual use.

## Per-site edits (before → after; sites located by content)
| # | site | before | after |
|---|---|---|---|
| 1 | Containerfile `-v <snapshot>` comment (~:196) | "REFUSES to launch when static roots are declared and the host dir is missing (cold-index first: python -m loremaster.index --config …)" | refuses when ANY declared static tier's dir is absent / empty / not a dir (`SnapshotLayout.is_materialized`, the boot guard's predicate) or the config fails to read; checked before teardown (running container untouched); the refusal names tier + dir + a paste-ready command using lore-deploy's loremaster interpreter, never bare `python` |
| 2 | Containerfile CMD comment (~:144) | "`python -m loremaster.index --config <lore.yaml>` — invoked by `setup` (cold index) and each `start` (delta-reconcile)" | `<interpreter> -m loremaster.index --config <abs lore.yaml>`, run on the HOST by `setup` with lore-deploy's interpreter, and the remedy `start` prints. `start` never runs it; delta-reconcile is in-server at boot (deviation 1) |
| 3 | Containerfile USER comment (:104) | one 113-col line | rewrapped, same words (deviation 2) |
| 4 | lifecycle.md "Snapshot dir" (~:23–33) | "host snapshot dir is missing → refuses … remedy `python -m loremaster.index --config …`" | per-tier `is_materialized` over the HOST root; absent/empty/not-a-dir or config unreadable → refuse; before teardown on recreate (1a); names tier + dir; remedy `<interpreter> -m … --config <abs lore.yaml>` with `_loremaster_python()`'s resolution order; never bare `python` |
| 5 | lifecycle.md `start` 1a precondition list | "image present AND env-file exists" | + every static tier materialised on the host, + embedder and store answer (matches `verb_start`'s order) |
| 6 | lifecycle.md `start` 1a relaunch failure | "A relaunch (`podman run`) failure after teardown degrades gracefully" | a `podman run` error OR the launch's own snapshot re-check refusing → loud stderr with the error's own text, `_EXIT_ERROR`, never a traceback |
| 7 | lifecycle.md `start` step 2 | "hard-probe `/embed` …" (no snapshot step) | after image/env checks, the static-snapshot refusal before any launch, then the probes |
| 8 | lifecycle.md `setup` step 7 | "`python -m loremaster.index --config <lore.yaml>` (in-container or against the workspace venv)" | on the HOST with `_loremaster_python()`; by hand `uv run python -m …` from the repo root (same `.venv`, measured); not in-container (cannot write the `:ro` snapshot, #166); it materialises what `start` checks |
| 9 | server-interface.md §5 | "`setup` cold-indexes via `python -m loremaster.index --config <lore.yaml>` … `start` just launches the container" | host run via `_loremaster_python()` (+ the `uv run` hand form); `start` only checks every static tier is materialised (`is_materialized`) and refuses with that command as the remedy |
| 10 | INDEX.md Watch-list landmine (~:589–591, above `## Log`) | "With static roots configured and the host snapshot dir missing, `start` REFUSES … (`python -m loremaster.index --config …`)" | per-tier / absent-empty-not-a-dir / config-unreadable; pre-teardown, container untouched; remedy with lore-deploy's interpreter, never bare `python`; relaunch failure after teardown exits with the error text, never a traceback |
| 11 | runbook 2026-08-01 (~:89) | "refuses to launch, loudly, if static roots are configured and the host snapshot dir is missing" | before any teardown, refuses if ANY declared static tier's dir is absent/empty/not-a-dir, leaves the running container untouched, names each tier + the command |
| 12 | 65-cut read-list item 7 (~:34) | "refuses on a missing host snapshot" | "before any teardown, refuses when any declared static tier is unmaterialised on the host (absent, empty or not a directory)" |
| 13 | 19-lore-deploy-rework annotation (~:18) | "refuses to launch when the host snapshot dir is missing" | "refuses to launch when any declared static tier is unmaterialised on the host" |
| — | packet39 design annotation, 11c §Scope OUT, INDEX:269–271 annotation, 19 :27–31 annotation, 65-cut step 2 | re-read | no refusal or remedy claim, so they are still accurate; left as is |

## Verdicts (pre-edit sweep, 85 hits, `/var/tmp/claude-1000/prose165r2-sweep.txt`)
Sonnet draft (`/var/tmp/claude-1000/prose165r2-verdicts.md`, 85 rows): HISTORICAL 55 · UNRELATED 4 · CANDIDATE-LIVE 26.
I sampled 10 rows (#4, 9, 10, 19, 25, 31, 36, 66, 71, 76) against spans I had read. All 10 agree with the key. One key artifact: receipt rows whose substring is `/sources/` (e.g. #43, #44) read HISTORICAL rather than UNRELATED, because the key put receipts first. The verdict class does not change, since both are no-edit.
Lines below are pre-edit line numbers.

My adjudication of the 26 CANDIDATE-LIVE rows:
| draft # | file:line | my verdict | why |
|---|---|---|---|
| 1 | Containerfile:11 | LIVE-OK | header: no /source since #165 |
| 2 | Containerfile:144 | **LIVE-FIXED** (#2 above) | bare `python`; wrong "each start" claim |
| 3 | Containerfile:198 | **LIVE-FIXED** (#1) | missing-dir / bare-`python` refusal wording |
| 7 | runbook:88 | LIVE-OK | bind description |
| 8 | runbook:89 | **LIVE-FIXED** (#11) | "host snapshot dir is missing" |
| 12 | 03b-comms-message-surface.md:69 | HISTORICAL | 03b `✅ DONE + DEPLOYED` (INDEX row :315); a done packet's deploy step |
| 13 | 10-d-weak-match-disarm.md:82 | HISTORICAL | 10-d `✅ DONE + DEPLOYED 2026-07-26` (INDEX row :357) |
| 14 | 10-d-weak-match-disarm.md:83 | HISTORICAL | same |
| 21 | 65-cut:34 | **LIVE-FIXED** (#12) | "refuses on a missing host snapshot" |
| 22–24 | 65-cut:134–136 | LIVE-OK | bind shape; no refusal claim |
| 27 | INDEX:586 | LIVE-OK | /source gone |
| 29 | INDEX:589 | **LIVE-FIXED** (#10) | "host snapshot dir missing" |
| 30 | INDEX:591 | **LIVE-FIXED** (#10) | bare `python` remedy |
| 70 | lifecycle.md:20 | LIVE-OK | no /source mount |
| 72 | lifecycle.md:23 | **LIVE-FIXED** (#4) | "host snapshot dir is missing" |
| 73 | lifecycle.md:25 | **LIVE-FIXED** (#4) | bare `python` remedy |
| 74 | lifecycle.md:80 (setup step 7) | **LIVE-FIXED** (#8) | bare `python`; "in-container" wrong |
| 75 | server-interface.md:89 | **LIVE-FIXED** (#9) | bare `python`; teaches the cold index generally |
| 79 | test_launch_snapshot_bind.py:14 | LIVE-OK (test, not editable) | "no bind targets /source" |
| 81 | test_launch_snapshot_bind.py:320 | LIVE-OK (test) | same invariant |
| 82 | test_launch_snapshot_bind.py:1115 | LIVE-OK (test) | the artifact pin's own precondition is the host ROOT dir, so "host snapshot dir … absent" is accurate for that check |
| 83 | test_launch_snapshot_bind.py:1116 | **STALE, listed** (test; DO-NOT-TOUCH) | remedy says bare `python -m loremaster.index` (F2) |
| 84 | test_lore_deploy.py:39 | **STALE, listed** (test) | "no /source mount" comment (F2) |
| 85 | test_lore_deploy.py:219 | **STALE, listed** (test) | same (F2) |
Also HISTORICAL by draft, confirmed: #76 `lore_deploy.py:90` and #77 `:791` (code comments naming the RETIRED /source, accurate), #78/#80 test docstring + `RETIRED_SNAPSHOT_TARGET` constant (accurate).
Totals for the 26 C-L rows, counted by row:
- LIVE-FIXED 10 (rows 2, 3, 8, 21, 29, 30, 72, 73, 74, 75)
- LIVE-OK 10 (rows 1, 7, 22, 23, 24, 27, 70, 79, 81, 82)
- HISTORICAL 3 (rows 12, 13, 14)
- STALE-listed 3 (rows 83, 84, 85)

Overall, 85 = 58 HISTORICAL + 4 UNRELATED + 10 LIVE-FIXED + 10 LIVE-OK + 3 STALE-listed.

## Post-edit sweep (haiku-worker E; its RAN line is my command verbatim)
`hits=77 files_listed=1078 exit=0 STDERR none`, which is 8 fewer than pre-edit (85). The removed hits are the 8 bare-`python` / "host snapshot dir" / "dir is missing" lines I rewrote. Two new hits are my `uv run python -m loremaster.index` hand-form lines. Line numbers are post-edit; INDEX `## Log` is at :618. Every hit has a verdict: 44 non-receipt + 33 receipt = 77.

| file:line | verdict |
|---|---|
| Containerfile:11 | LIVE-OK |
| Containerfile:210 | HISTORICAL (dated "Until 2026-10-31" clause) |
| docs/design/2026-07-31-packet39-google-oauth.md:330 | HISTORICAL (original sentence, dated annotation follows) |
| docs/design/2026-07-31-packet39-google-oauth.md:332 | HISTORICAL (dated annotation) |
| docs/design/2026-08-01-google-auth-restart-runbook.md:88 | LIVE-OK |
| docs/design/2026-08-14-packet47-ingest-entity-seam-design.md:629 | UNRELATED |
| docs/design/2026-08-28-packet63-retrofit-rulings.md:52 | UNRELATED |
| docs/design/2026-09-11-packet63b-ii-b-drain-update-ruling.md:151 | UNRELATED |
| docs/plans/v2/03b-comms-message-surface.md:69 | HISTORICAL (03b DONE + DEPLOYED; F6) |
| docs/plans/v2/10-d-weak-match-disarm.md:82 | HISTORICAL (10-d DONE + DEPLOYED; F6) |
| docs/plans/v2/10-d-weak-match-disarm.md:83 | HISTORICAL (same) |
| docs/plans/v2/19-lore-deploy-rework.md:15 | HISTORICAL (annotated) |
| docs/plans/v2/19-lore-deploy-rework.md:18 | LIVE-FIXED |
| docs/plans/v2/19-lore-deploy-rework.md:26 | HISTORICAL (annotated) |
| docs/plans/v2/2026-08-01-dnd-rag-RESUME.md:23 | HISTORICAL (SUPERSEDED header) |
| docs/plans/v2/2026-08-01-dnd-rag-RESUME.md:25 | HISTORICAL (same) |
| docs/plans/v2/65-hosted-write-joint-cutover.md:34 | LIVE-FIXED |
| docs/plans/v2/65-hosted-write-joint-cutover.md:135 | LIVE-OK |
| docs/plans/v2/65-hosted-write-joint-cutover.md:136 | LIVE-OK |
| docs/plans/v2/65-hosted-write-joint-cutover.md:137 | LIVE-OK |
| docs/plans/v2/INDEX.md:269 | HISTORICAL (annotated) |
| docs/plans/v2/INDEX.md:271 | LIVE-OK (annotation) |
| docs/plans/v2/INDEX.md:586 | LIVE-OK |
| docs/plans/v2/INDEX.md:588 | LIVE-OK (past-fact clause inside the live landmine) |
| docs/plans/v2/INDEX.md:1071 | HISTORICAL (Log) |
| docs/plans/v2/INDEX.md:1074 | HISTORICAL (Log) |
| docs/plans/v2/INDEX.md:1764 | HISTORICAL (Log) |
| docs/plans/v2/INDEX.md:1768 | HISTORICAL (Log) |
| docs/plans/v2/INDEX.md:1801 | HISTORICAL (Log) |
| docs/plans/v2/MASTER-PLAN.md:283 | UNRELATED |
| skills/lore-deploy/references/lifecycle.md:20 | LIVE-OK |
| skills/lore-deploy/references/lifecycle.md:21 | HISTORICAL (dated clause) |
| skills/lore-deploy/references/lifecycle.md:91 | LIVE-FIXED (new `uv run` hand form) |
| skills/lore-deploy/references/server-interface.md:93 | LIVE-FIXED (same) |
| skills/lore-deploy/scripts/lore_deploy.py:90 | LIVE-OK (names the retired target) |
| skills/lore-deploy/scripts/lore_deploy.py:791 | LIVE-OK (same) |
| skills/lore-deploy/scripts/test_launch_snapshot_bind.py:8 | LIVE-OK |
| skills/lore-deploy/scripts/test_launch_snapshot_bind.py:14 | LIVE-OK |
| skills/lore-deploy/scripts/test_launch_snapshot_bind.py:82 | LIVE-OK (`RETIRED_SNAPSHOT_TARGET`) |
| skills/lore-deploy/scripts/test_launch_snapshot_bind.py:320 | LIVE-OK |
| skills/lore-deploy/scripts/test_launch_snapshot_bind.py:1115 | LIVE-OK (the pin's own root-dir check) |
| skills/lore-deploy/scripts/test_launch_snapshot_bind.py:1116 | STALE (test, DO-NOT-TOUCH; F2) |
| skills/lore-deploy/scripts/test_lore_deploy.py:39 | STALE (test; F2) |
| skills/lore-deploy/scripts/test_lore_deploy.py:219 | STALE (test; F2) |

Receipts (33, all HISTORICAL by rule, under `docs/plans/v2/receipts/`):
- 2026-07-24-packet11i/CONTRACT-FREEZE-DECISIONS.md:305
- 2026-07-26-packet11i-fixwave/REPORT-fable-design-11i.md:320
- 2026-07-26-packet11i-fixwave/REPORT-scout-11i.md:533
- 2026-07-28-packet11ib/REPORT-informant-fable-11ib.md:52
- 2026-07-28-packet11ib/REPORT-scout-11ib-1.md:80
- 2026-08-01-agent-comms-fix/REPORT-design-sidecar-04b2-1.md:117
- 2026-08-01-dnd-rag-scoping/REPORT-corpus-scout-1.md:92, :564
- 2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:169, :448, :609
- 2026-08-01-packet04b2-wavec/REPORT-lead-04b2-wavec-r2.md:283, :304
- 2026-08-04-packet04b3/REPORT-design-sidecar-04b3-1.md:733, :734
- 2026-08-08-packet05aiii/REPORT-contract-fix-05aiii.md:201
- 2026-08-09-defect-class/REPORT-adversary-g.md:70
- 2026-08-10-packet05aii/REPORT-adversary-05a-ii.md:432
- 2026-08-12-packet06a/REPORT-coldaudit-honesty-06a.md:17
- 2026-08-16-packet59/REPORT-lead-59.md:146
- 2026-08-16-packet59/REPORT-sweep-59.md:319
- 2026-08-17-packet07/DESIGN-sidecar-144-posture.md:115
- 2026-08-17-regression-fix/REPORT-regr-fixer.md:68
- 2026-08-20-packet48/REPORT-build-48b.md:11
- 2026-08-20-packet48/REPORT-builder-48b.md:11
- 2026-08-24-packet62/REPORT-adversary-62w2.md:293
- 2026-09-04-packet63b/REPORT-contract-63b-i-b.md:52
- 2026-09-09-packet63b-ib/REPORT-lead-63b-s2.md:58
- 2026-09-12-packet63b-ii-b/REPORT-contract-63b-ii-b.md:98
- 2026-09-24-lore-cold-boot/lore-lore-podman.log:110, :111, :112
- 2026-10-04-531-536/REPORT-fix531.md:190

Post-edit tally, counted by row from the table above:
- LIVE-FIXED 4: 19:18, 65:34, lifecycle:91, server-interface:93.
- LIVE-OK 16: Containerfile:11, runbook:88, 65:135–137, INDEX:271, :586, :588, lifecycle:20, lore_deploy.py:90, :791, test_launch:8, :14, :82, :320, :1115.
- HISTORICAL 17 non-receipt: Containerfile:210, p39:330, :332, 03b:69, 10-d:82, :83, 19:15, :26, RESUME:23, :25, INDEX:269, :1071, :1074, :1764, :1768, :1801, lifecycle:21.
- UNRELATED 4.
- STALE-listed 3.

That is 44 non-receipt hits, plus 33 receipts, for 77. It matches `hits=77`.

The 8 lines that left the sweep are the old refusal/remedy texts rewritten in sites #1, #2, #4, #8, #9, #10, #11.

## Flags (everything noticed; the operator/lead owns scope)
- **F1: SKILL.md `start` row, outside my set.** `skills/lore-deploy/SKILL.md:52` describes `start` as "Launch the container … + merge `.mcp.json`, then waits for the MCP port". It does not mention the snapshot refusal. The awk patterns did not reach it (A'' found it). Suggested insertion after "Launch the container": "(refuses first, before any teardown, when a declared static tier is unmaterialised on the host; the refusal prints the cold-index command)".
- **F2: stale test text, DO-NOT-TOUCH.**
  - `skills/lore-deploy/scripts/test_lore_deploy.py:39` and `:219` say "no static roots → no /source mount". Suggested wording: "no snapshot bind".
  - `skills/lore-deploy/scripts/test_launch_snapshot_bind.py:1116` (artifact-pin failure message) gives the remedy `python -m loremaster.index --config {REPO_CONFIG}`. Same A8 defect class: suggest `{lore_deploy._loremaster_python()} -m …`.
  - Owners: contract/implementer.
- **F3: brief over-statement on the fresh path.** `verb_start` runs `podman rm -f` on an EXISTING-but-not-running container (`if state is not None: …`) before the image/env/snapshot checks. That predates #165. The docs say "before any teardown" only for the recreate path. Nothing running is lost either way. Is that rm intended to stay ahead of the gate?
- **F4: `.py` docstrings.** None found stale in the commits' hunks. `_launch_container`'s docstring and `_require_launchable_snapshot` match the behaviour. The test texts are in F2.
- **F5: the snapshot path literal** is now in more prose (lifecycle.md, Containerfile, INDEX, runbook, 65-cut). This is the same one-implementation root as prose-165 Flag 5 (D2-flag 4 of the plan, already queued). I named `_DEFAULT_SNAPSHOT_ROOT` / `is_materialized` / `_loremaster_python()` as the authorities wherever I described a rule.
- **F6: done packets 03b and 10-d** still carry the old "/source … do NOT `lore-deploy start`" deploy landmine (03b:69, 10-d:82–83). I classed them HISTORICAL (DONE + DEPLOYED). A reader who reuses those deploy steps as a template would get stale advice. Annotate or leave? It's your call.
