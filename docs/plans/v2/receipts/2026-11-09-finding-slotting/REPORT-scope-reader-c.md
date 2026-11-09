brief-base v26 read

SCOPE-C — packet scope summaries for finding slotting
Measured 2026-11-09 against the working tree on branch feat/surreal-unification (HEAD e1593d7, clean).
Landmine recall returned 6 rows (fewer than k=50, so the set is complete).
Method: I extracted finding numbers with `python3 -I` using re `#(\d+)\b`, once over each packet file and once over its INDEX `| NN |` row. Code facts come from reading skills/lore-deploy/scripts/lore_deploy.py and loremaster/loremaster/server.py directly. Confidence is HIGH unless a line says otherwise.

=== 19 — deploy-architecture DESIGN ===
Status: open. Redesignated 2026-07-22; urgency raised 2026-07-25 (#186, #165 recurred). Design only: it mints the 19b+ build packets, each ≤0.25.
Scope IN:
- The one-toolchain ruling (#166): run all four loremaster shell-outs IN the container, kill the hardcoded host venv path, define what a public user needs (podman + script + image).
- #165 dissolution as a design consequence, plus a verification receipt. The 2026-10-31 stopgap shipped; the in-container re-acquire bound is still 19's.
- An incremental-add/refresh verb for static tiers.
- Snapshot and boot-check keying: decide whether to key on the store (file_text) or on disk.
- Partition the old rework into 19b+ builds: finding #13 (the status verb reads the legacy SQLite manifest), the `_scaffold_lore_yaml` fix (emits qdrant:/no surreal:), all-mode verbs/roles, the git_sync pattern, dropping the Qdrant verbs.
- Routed via the INDEX row (not in the file): #339 (no restart policy, not systemd-managed), #340 (pids.max task-leak), #382/#386 (conformance harness truth), #299 (fixed `lore` server name).
Findings — file: #13 #24 #140 #165 #166 #186. INDEX row adds: #299 #339 #340 #382 #386.
Fits here: the lore-deploy skill (skills/lore-deploy/scripts/lore_deploy.py and its tests) and container/deploy topology: mounts, snapshot root, image toolchain, verbs, scaffold, restart/systemd posture.
Q answers:
- `_loremaster_python`: YES. It is #166's hardcoded `~/PycharmProjects/lore/.venv` path. The file cites `lore_deploy.py:369-388`, which is stale: the function now sits at ~L393 and the hardcode at ~L405.
- Snapshot-root path: YES, via #165/#166 (`SNAPSHOT_ROOT` / `_SNAPSHOT_SUBPATH`, `_require_launchable_snapshot`).
- Host `<slug>.db` manifest: PARTIAL. 19 names only finding #13 (the status verb reading the legacy SQLite manifest). Measured today, `<slug>.db` is lore-deploy's own `Ledger` (slug owner `project_path` + provisioned marker, "RULING-572-ledger"). It is no longer an index manifest, so #13's premise may be stale. MEDIUM.
- Port allocation (`_free_port`, `_probe_mcp_port`): NOT NAMED anywhere in 19. Every "port" hit is a substring of another word. It fits 19 by subsystem, but 19 does not own it.

=== 18 — SQLite ledger retirement ===
Status: open. Wave M, FIRST; it must land before 20 finalizes and before 22 ships. The INDEX row carries no finding numbers.
Scope IN:
- A parity receipt (ledger rows vs store) before anything is removed.
- Delete the memory write-through side-write and the boot backfill. Memory writes become store-only and fail loud. Lifecycle tests.
- Keep a standalone ledger READER for packet 20's N3 import of v0.3 `<slug>.memory.db`.
- Freeze, don't delete, the existing `.memory.db` files (`.retired` is acceptable).
- Resilient-open honesty: no recreate-and-serve-healthy; a memories-unrecovered status names the moved-aside path.
- Backup posture per mode, plus a lore-deploy `backup`/`export` verb. 18 builds it and 19 inherits it.
- Docs claim the singular store.
Findings — file: #107 (only as the store-law citation). Owns no finding by number.
Fits here: loremaster's memory backend (memory/ledger.py `MemoryLedger`, index/sqlite_resilient.py, the server.py boot wiring), plus the new deploy backup verb.
Q answers:
- Legacy SQLite open at server boot: YES, in substance. There is no literal `lore.db` in loremaster. At boot, server.py `build_app_context` opens `MemoryLedger(manifest_path.with_name(f"{slug}.memory.db"))` (FP-06 write-through). That is exactly 18's writer and backfill. The `<slug>.db` passed as `manifest_path` is only a path anchor; its docstring says the manifest lives in SurrealDB.
- `<slug>.db` deploy manifest: NO. 18 never mentions it. That file is lore-deploy's slug-ownership ledger, the 19/#13 territory above.

=== 17 — worktree-overlay DESIGN (+ 23 BUILD) ===
Status 17: open (design, wave L; "the parallelism enabler"; #136 fixed 2026-07-14).
Status 23: open (build, wave O; depends on 17 being ruled; must land before 26 completes).
Scope IN (17): a delta-only ephemeral overlay tier (git diff vs merge-base), overlay-shadows-base serving per file, auto-reap.
- v1 serves graph-over-the-delta: a changed-symbol inventory, a changed-set search filter, and batched base-served impact behind a numbered caveat.
- Rules out a textual-diff re-serve and a git-ref mode on `lore_diff` (#232).
- Trust riders: three identities rendered, per-file committed/uncommitted, age, loud refusal.
- Hosted riders: the view identity tuple, a single writer per view, declared sessions, a scout heartbeat, two isolation legs, the lifetime taxonomy. The seam is named for 39.
- Open questions OQ1–6: registration, addressing, freshness, reap, coexistence, caveat wording.
- Tooling debt to disposition: #185.
Scope IN (23): build per 17's ruling. Invariants: delta-only, base results byte-identical with and without an overlay, hostile fixtures on the caveat render, a deleted-file and a renamed-file fixture, smoke on a real worktree.
Findings — 17 file: #102 #125 #131 #134 #185 #232. 17 INDEX row adds: #136 #284. 23 file: #107 #125. 23 row: #125.
Fits here: indexing and serving of non-base git trees (overlay tier, view registration, reap, worktree-aware renders), plus worktree-safety of the scratch/mutation tooling.
Q answer (scratch_copy.sh git isolation, #185/#284): 17 owns it, as a disposition: "isolate a worktree-sourced copy or REFUSE it loudly". #185 is in the 17 file. #284 appears only in the INDEX row ("routed 2026-09-24"), not in the file. 23 does not mention scratch_copy at all, so the actual fix's build home is unassigned unless 17's ruling mints it.

=== 58 — supersede re-anchors dependents ===
Status: open. Minted 2026-08-11; file minted 2026-09-24. Pool item 30 RULED 58 BEFORE 64 (2026-09-26).
Scope IN:
- Inside the supersede txn, for each dependent Y: rewrite `blocked_by` X→X', DELETE the old `blocks` edge, RELATE the new one, append a `dependency_reanchored` provenance event, and refuse a cycle (rolling back the whole supersede).
- Extract a TASK-side guarded-append shell used by `_transition_fragment`, the supersede stamp and the re-anchor note (`_claim_fragment` too, or a stated reason). Mutation-proven.
- A HUB bound (~1+3N statements vs the 800/5000 caps), pinned; F-1 rules its shape.
- #130: `_candidate_statement` claimable partition agrees with the claim CAS, and the claim-loss render names supersession.
- Ledger (not build) the cross-module findings+tasks shell unification.
Findings — file: #105 #130 #174 #256 #356 #466. Owns IN: #356 #130. #256 is a cited precedent; #105 #174 #466 are citations.
Fits here: loremaster/tasks.py `TaskLedger` write fragments (supersede/transition/claim), dependency-edge consistency, and the claimable-query partition.
Q answer: ONLY supersede re-anchoring (+ shell extraction + #130). It does not own the lore_tasks rollup cursor or stamp paging: "rollup", "cursor" and "updated_at" have zero hits in 58. Such a finding has no owner among these six packets. 57 mentions rollup only as the surface for its liveness enrichment.

=== 57 — task-coordination substrate ===
Status: open. Minted 2026-08-11; file 2026-09-24. Contract only after 63c closes; F-4 sequences the shell extraction vs 58.
Scope IN:
- An `assign` verb plus an `assignee option<string>` field distinct from `owner`, with a dirty-store migration pin.
- An owner-guarded task-release verb ("reap", whose name fork F-B may split).
- An ownership↔liveness surface on task query/rollup: owner→registry via 63c's `read_filter`, through the shared predicate; unresolvable and foreign owners render identically, never "alive".
- Auto-release on `retired` only.
- Findings: #352 #372 (retire teaches TaskStop; the lead-base edit is flagged to the operator, not written), #357 (fork F-C, reopen edge), #363 (fork F-B, phantom agent rows), #412 (entry gate: agent reap = retire-status vs hard-delete).
Findings — file: #262 #352 #356 #357 #360 #363 #372 #412 #466. Owns: #352 #357 #363 #372 #412. #262 is the root it dissolves. #356 is scoped OUT (it belongs to 58). #360 and #466 are context.
Fits here: tasks.py ownership/assignment/release verbs and the task↔agent-registry liveness join (tasks.py + the server.py `_heartbeat_is_stale` / overdue predicate consumers). Not 63c's agent DDL, and not 64's governance.

=== POOL (INDEX "## Operator decision pool", items 1–31) ===
1. Packet 12 fork: prose-ish suspect flag, in-text vs metadata.
2. Packet 20 entry gate: migration §8 Q1–Q4, the v1.0-critical ruling.
3. Packet 22: Shape-D GO/NO-GO, retire confirm, Qdrant orphan cleanup.
4. RULED: SurrealDB is the singular store; the SQLite ledger retires (packet 18).
5. RULED: #49 instructions sizing overage ACCEPTED; 35-pair bar re-run owed.
6. detail_level reshape (refs|signatures|source): place in 28 or reject.
7. T7 budget 1100→1600, T8 memories= param, T9 re-expose tools.
8. D4 rename served `score` → `fusion_rank` (packet 09 if approved).
9. Air-gapped opt-out for the hard Anthropic-key boot requirement.
10. Verify rebuild-caveat: a harder gate than caveat-during-rebuild?
11. Watcher skip-path posture ack (store blip kills the watcher worker).
12. Spectron re-decision: docs now indexed; run the spike list.
13. DI doc-content import (DECISIONS/GOTCHAS → memories), ad hoc.
14. CLOSED: #55/#292/#298 lore tools missing for allowlist agents; residue #334.
15. Upstream report of the mcp-builder TextContent serialization bug.
16. RULED: render memoization dropped; summary reuse promoted to packet 34.
17. Packet 33 autonomy ruling: flag / propose / auto-apply per action class.
18. Retrieval-liveness as a dead-code corroborator (rides packet 35).
19. SCHEDULED: Odoo onboarding became packet 25 + 26a+.
20. #73 eval-fixture maintenance: ground truths go stale as the tree grows.
21. #111 typed conflict check once surrealdb-py 3.0.0 ships.
22. #154/#157/#218 legacy citation debt: mini-packet or accept (DUE now).
23. #156/#200/#224 process-instrument design cluster (exemption/provenance/count-scope).
24. RULED: message id = ULID (implemented 13da377).
25. #242 connection-glue extraction: design WITH a redesigned discovery gate.
26. #285 the repo has no CI: mint a CI packet or accept dev-shell gates.
27. #299 rename the MCP server to a fixed `lore`; decide at 65-pre.
28. RULED YES: a lead may run the production data migration unattended.
29. RULED: 11c BEFORE the 65 cutover (hard dependency).
30. RULED: 58 before 64; 64 design/contract may run ahead of 63c.
31. 65-pre P1: hosted-write enablement is UNDESIGNED; schedule a Fable design.

=== WATCH LIST (INDEX "## Watch list", entry → #numbers) ===
- No worktrees until worktrees work → #125 #134 #136
- #140: a cp -a copy never runs its own code → #140
- #124 engine first-write race, rediagnosis pending → #109 #124 #144
- #159 non-passing tests, evidence destroyed by tail echo → #159 #241
- #236 pre-existing dangling-edge cleanup deferred (localhost-only) → #138 #236
- #239 SurrealDB 4.0 upgrade break (RELATE deterministic ids) → #239 #349 (#349 is a vendor release-note number, not a lore finding)
- #265 one drain timeout under concurrent load → #159 #265
- #184 fastmcp standalone migration refused for 03b → #184
- #202 `_txn.retry_on_conflict` third hand-roll (tenacity) → #202 #207
- #185 LANDMINE: scratch_copy.sh doesn't git-isolate worktree copies → #185
- lore-lore snapshot mount: #165 stopgap; #166 open (packet 19) → #165 #166
- Open research note: score display to LLM consumers → (none)
- Graph composition / hot-row mint / two-step recreate in DESIGN-LAW → (none)
- scratchpad/ at repo root is corpus pollution → #72
- #466 pytest isolates DBs, not ports or RAM → #466
- #385 two-source SDK-await-boundary error tuple → #385
- :18500 "no close frame" WS-drop class → #379 #380 #409 #422 #433 #463 #468

=== GAPS NOTICED (for the lead's slotting; not acted on) ===
- No packet among these six owns lore_tasks rollup cursor/stamp paging (the `updated_at` tiebreak).
- No packet among these six owns lore-deploy port allocation (`_free_port`, `_probe_mcp_port`).
- #284 is routed to 17 only in the INDEX row; 17's file names #185 alone.
- 19's citation `lore_deploy.py:369-388` is stale (the function is now ~L393). Symbol: `_loremaster_python`.
- 19's finding #13 premise (status verb reads the "legacy SQLite manifest") may no longer hold: `<slug>.db` was repurposed as lore-deploy's slug-ownership Ledger. MEDIUM; I did not check #13's live body.
