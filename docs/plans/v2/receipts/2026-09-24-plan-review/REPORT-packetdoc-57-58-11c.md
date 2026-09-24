brief-base v16 read · brief project v7 read

# REPORT — packetdoc-57-58-11c (plan review 2026-09-24, prose only)
- **State:** done. **Deviations:** none. No code, tests, or git operations. I wrote only the 4 files in my writable set.
- **Packages considered:** none. No mechanism was specified; the packets defer mechanisms to their contracts.
- **Odoo-20 portability:** n/a (no Odoo seam touched). **Reuse ledger:** none (no symbols). **Graded:** n/a (authoring, not grading). I read the code at HEAD `d237ad7`.
- **Capability check:** all tools present. A PreToolUse hook blocks `grep` in the main checkout, so I used lore tools plus `Read`/`awk`. I used `awk` for INDEX rows, the report outline, and the `TXN_STATEMENT_*` constants. lore cannot return a module constant, so I filed that as **#476**.
- **Decisions needed:** see "Contradictions" (C1–C6) below. C1, C3 and C4 change what a contract would build.
- **Receipts:** the 3 packet files below. Each has a "What exists today" section, and each fact there cites a symbol.

## Files written
- `docs/plans/v2/57-task-coordination-substrate.md` (120 lines)
- `docs/plans/v2/58-supersede-reanchor.md` (107 lines)
- `docs/plans/v2/11c-index-boot-reconcile-honesty.md` (134 lines, header MINTED per the 16a precedent)

## Verified vs UNVERIFIED
- **57, verified with lore_verify/get_symbol/read:**
  - The `LEGAL_TRANSITIONS` 11 edges: there is no unclaim edge and no out-edge from `done`.
  - `_claim_fragment` guards.
  - `_is_blocked` is terminal-only.
  - `AppContext._heartbeat_is_stale` has 1 production consumer (`lore_impact`).
  - `RetiredAgentError`, and the absence of an agent hard-delete (by search).
  - The 63c ruling §0 Q1/Q4b.
  - #352 #357 #363 #372 #412 bodies.
- **57, UNVERIFIED:** the symbol home of the `overdue` predicate. Whether 64 has started (INDEX says PLANNED).
- **58, verified:**
  - `supersede_task` signature with the #174 sentinel.
  - `_supersede_fragment` body: it does nothing to dependents.
  - `direct_dependents`, `_relate_fragment` and `_refuse_a_cycle` exist.
  - `FindingLedger._guarded_append_fragment` exists. The task-side one is not_found.
  - `_backfill_blocks_edges` runs every boot, and R10(ii) is in its docstring.
  - `_candidate_statement` has no `superseded_by` clause, so #130 is live at the ledger level.
  - Compose caps are 5000 and 800.
- **58, UNVERIFIED:**
  - Whether the claim-LOSS render now names supersession.
  - Whether a ledger row exists for the cross-module DRY item. The entry check mints it.
  - The exact statement count per dependent. The design's "~3N" is carried forward as an estimate.
- **11c, verified:**
  - `reconcile_store_divergence` has no logger call on the purge path.
  - Both `_periodic_reconcile` clones exist.
  - `_mark_file_failed` and `_resolve_individually` exist.
  - The #355/#338/#383/#434/#366 bodies and task `f4e3b63f…`.
  - `lore_index()` gives `files_failed: 1`.
  - The receipt README, and investigate-472 §2/§5.
- **11c, UNVERIFIED:**
  - What `tiers_rebuilt` means (MEDIUM, from a test, not from the populating code).
  - Whether the 150 s eager boot is still true on a no-purge boot.

## Contradictions (INDEX rows / design docs / brief / code)
- **C1 — the STALE vocabulary is stale.** INDEX row 57, the design §2B and the brief all say "STALE". #360 retired the `⚠ STALE` glyph, and the fleet now renders `overdue (declared …)` from the declared cadence. The task surface's liveness vocabulary is an open fork (57 F-A).
- **C2 — location.** The brief puts `_heartbeat_is_stale` in `agents.py`. It is `AppContext._heartbeat_is_stale` in `server.py`. The brief also puts `reconcile_store_divergence` in `index/`. It is in `server.py`.
- **C3 — "reap" means two things.** The design's `reap` releases a TASK row. #352, #363, #372 and #412 use "reap" for retiring or killing an AGENT. The brief's #412 line, "a `reap` verb IS that path", conflates the two: a task-release verb deletes no agent. It is an entry gate only if agent-reap is ruled as hard-delete (57 F-B).
- **C4 — the brief's 11c EXIT instrument would give a false clear.** `test_reconcile.py::test_summary_spans_live_and_static_roots` pins a live tier in `tiers_rebuilt` with `files_purged == 0`. The investigate-472 §5.3 sweeps also printed `["lore"]` while indexing 0 files. So `tiers_rebuilt: []` is neither necessary nor sufficient for "no purge". I rewrote the EXIT to key on the new decision log line (`action=none`), plus a positive control. I kept the entry check's `tiers_rebuilt` leg, as the brief directs, but paired it with a purge-proving signal.
- **C5 — sequencing between 58 and 64.** The brief says to sequence 58 after 64 or to state the hazard. The new sibling `64-governed-retrofit-tasks-findings.md` scopes 58 OUT, says "64's supersede must not make it harder", and puts supersede on 64a-i's write side. I recommend **58 BEFORE 64**, because one extracted shell leaves 64 fewer write paths to govern. This is left for the operator to rule. If 58 lands after 64, a new question opens: can a supersede rewire a dependent in a scope the superseder cannot write? (58 F-3.)
- **C6 — 64 and 57 disagree about "owner".** 64 adds `owner_principal`/`owner_agent` on `task` beside the claim `owner`. 57 adds `assignee`. 64 (its line ~152) already warns that "owner" must not mean two things. Whichever packet contracts second must reconcile three owner-ish columns. Also, 64 says it does NOT depend on 63c, while the brief says 57 must follow 63c. These are consistent, but 57's owner→registry resolve reads governed agent rows (57 F-A, design fork 3).
- **Minor:**
  - `reconcile_store_divergence`'s docstring claims a graph-count comparison against the manifest. The code only checks the graph count `== 0`.
  - 11c borders the open 11a/11b (the #171 diff-driven reconciler). 11c F-5 exists so that nobody builds two reconcilers.
  - #366's own body names wave S 36–38 as its home. 11c takes it, and flags the race.
- The tree had other uncommitted, untracked sibling outputs (`INDEX.md` modified, `REPORT-packetdoc-64/65`, the `64`/`65` packet files). They are not mine and I did not touch them.
