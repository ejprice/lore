# 11c — Index boot/reconcile honesty: the unlogged whole-tier purge, the unindexable file, the lying event
size ~0.20 wu (→split at kickoff if #355's root-cause hunt prices it over) · wave L ∥ (independent) ·
depends: none · DEPLOY: **yes** (changes boot behaviour). It can RIDE the packet-65 joint cutover, but its
value is highest if it lands BEFORE 65: every lore-lore recreate costs a multi-hour MCP outage today.
FIRST READ (store law — MANDATORY): `docs/reference/surrealdb-31-capabilities.md` (the store-side count and
`delete_by_tier` semantics this packet reads and changes)
Ground truth: `docs/plans/v2/receipts/2026-09-24-lore-cold-boot/README.md` (timeline + Resolutions) + its
`lore-lore-podman.log`; `REPORT-investigate-472.md` §2, §5.2, §5.3 (archived with packet 63c — cite the
archived path once it moves). Recall: `lore_recall("DEPLOY LANDMINE #355")`.

**Provenance: MINTED 2026-09-24 by the plan review; operator may strike/re-home at kickoff** (the
packet-16a precedent). It homes index/boot findings that no open packet owns. ⚠ It borders 11a/11b (the
#171 embedding-schema reconciler, both still open) and wave S 36–38 (role wiring, #366's suggested home).
See Hazards.

## Mission
A recreate on an in-sync store boots in the budgeted time. Any purge it does is LOGGED with its trigger
and scope. No file is permanently unindexable because of its size. No log event reports a data loss that
did not happen.

## What exists today (read 2026-09-24 at `d237ad7` — cite symbols, not lines)
- `reconcile_store_divergence` is in **`loremaster/loremaster/server.py`** (not `index/`). It runs at BOOT
  only. It purges (`store.delete_by_tier` + `manifest.reset_tier`) a live tier on ANY
  `store.count(tier) != manifest.expected_chunks(tier)`, or when the graph is wiped with no indexer. The
  purge path has **no logger call** (read). Its docstring says it compares
  `code_graph.indexed_file_count()` against the manifest, but the code only tests the graph count `== 0`
  (docstring/code drift, surfaced).
- Uvicorn does not bind until the boot reconcile finishes. The 2026-09-24 boot took **3h48m**
  (`reconcile.summary duration_ms 13,586,943`, `tiers_rebuilt ["lore"]`, 1218 indexed / 1 failed).
  Earlier recurrences: ~94 min (05a-ii deploy, #355 body) and ~3 h / 865 files (06a deploy, lore memory).
  Repo `CLAUDE.md` §Deploy still says *"lore-lore boots ~150s (eager)"*. That number is true only on
  a boot that purges nothing, and it may be stale even there (UNVERIFIED).
- **The #383 count-leg hypothesis is REFUTED** (investigate-472 §5.3). `SurrealManifest.expected_chunks`
  sums `indexed` rows only, and on prod Σ indexed = 28108 = the store count. **The trigger of the
  2026-09-24 purge is UNKNOWN.** Open leads: the graph leg, and the fact that the 17:16/17:36 periodic
  sweeps ALSO printed `tiers_rebuilt ["lore"]` while indexing 0–2 files.
- ⚠ **`tiers_rebuilt` does not mean "purged".** `test_reconcile.py::test_summary_spans_live_and_static_roots`
  asserts a live tier IS in `tiers_rebuilt` with `files_purged == 0`, which makes it a "tiers swept" label
  (MEDIUM: read from the pinning test, not from the populating code). So **`tiers_rebuilt: []` is not a
  valid exit instrument.** A healthy sweep can list the tier, and an empty list proves nothing about a purge.
- `store/_txn.compose` refuses more than `TXN_STATEMENT_HARD_CAP = 5000` statements (warns above 800).
  `Indexer._index_chunks` composes ALL of a file's fragments into ONE transaction, so
  `loremaster/tests/test_comms_tool.py` (505 chunks, over 5000 statements) is permanently `failed`. Every
  sweep re-embeds all 505 chunks and then drops them (#383 cost-amplifier annotation). `lore_index()` on
  2026-09-24 showed `files_failed: 1`. ⚠ That file is also under active 63c edit.
- `loresigil.resilient.ResilientEmbedder.embed_texts` logs ERROR `embed.permanent_failure` when a
  BATCH exhausts its retries. It then recovers per-text via `_resolve_individually` → `_embed_single`,
  and a successful recovery logs nothing (the whole source of #472, resolved benign).
- The periodic reconcile daemon exists twice: `loremaster.scout.Scout._periodic_reconcile` and
  `loremaster.server._periodic_reconcile`. Both call `run_sweep()`, and both carry 06b's trace-GC purge gate.

## Scope IN
1. **#355, observability FIRST.** Add ONE structured log event at the heal decision: tier, live count,
   expected count, graph count, which leg fired, and the action taken (purge / regraph / none). Add it
   BEFORE any behaviour change. Then deploy or boot on a copy of the production store's shape and READ
   the trigger. **The fix is chosen from the measured trigger, not in advance** (measure-then-tune,
   with a named decision point: the first logged boot).
2. **#355, the fix** (after 1): narrow the purge to diverged FILES, never the whole tier on any delta, OR
   the operator-ruled alternative (Fork F-1). The heal stays idempotent (the existing "HEALTHY tier is
   NEVER purged" contract holds). Divergence detection moves off boot-only if F-2 rules so.
3. **#338 + #383** (duplicates; resolve both): a file larger than the cap indexes. Either chunked compose
   (split one file's fragments across ≤cap transactions, keeping the per-file atomicity the manifest
   relies on, or stating the new bound) or a per-file statement budget (Fork F-3). Also stop the
   every-sweep re-embed of an unchanged failed file (investigate-472 §5.2's direction).
4. **#474 + ledger task `f4e3b63f7cad4f8faaf7e995dc74fd70`**: rename the batch event (e.g.
   `embed.batch_exhausted`, WARNING). Log the fallback outcome (`n_texts`/`n_recovered`/`n_failed`). Keep
   `embed.permanent_failure` for a per-input `None` only. Sweep log consumers and prose for the old name
   with a bare, anchor-free pattern. That task's own TODO (1)–(4) is the spec.
5. **#434**: `lore_index(reconcile=True)` exceeds the 300 s MCP tool-idle limit. Make it
   progress-emitting or async (return a handle; status via `lore_index()`), OR teach the bound in the
   served description (Fork F-4). The served surface must never time out silently.
6. **#366**: ONE `_periodic_reconcile` helper that both daemons call. Prove the sharing by mutation:
   perturb the helper and both the scout and the server pins go red, including the trace-GC purge gate.
7. **The boot budget**: re-derive the eager-boot time on a no-purge boot, state it with its receipt, and
   correct `CLAUDE.md` §Deploy (in scope at build time).

## Scope OUT (surface to operator if encountered)
- The #171 embedding-schema reconciler (11a/11b). The floor calibration (11-i/11-ii). TEI capacity
  (the investigate-472 §5.1 429 storm, ledger if not already filed). #339 (lore-lore not restart-managed),
  #165/#166 (the hand-rolled `/source` mount), and the quadlet digest pin (#336/#341 → packet 16).

## FINDINGS / TASKS OWNED (IN / bound / fork)
- **#355**: IN. The log line is deliverable #1. The fix waits on the measured trigger (F-1/F-2).
- **#338 / #383**: IN (F-3). The test file is a 63c hazard: coordinate if 63c is still open.
- **#434**: IN (F-4).
- **#474 + task `f4e3b63f…`**: IN. Claim the task at start and drive it to done.
- **#366**: IN. Bound: a THIRD daemon is its named re-open trigger. If wave S (36–38) has started,
  coordinate so there is one extraction and no race.

## FORKS (questions: operator rules at kickoff, or after deliverable #1 where noted)
- **F-1 (after the log lands):** per-file heal, or keep the tier purge but only above a divergence
  threshold, or refuse-to-boot-and-teach? Rec: per-file. Its overlap with 11b's diff-driven reconciler
  is F-5.
- **F-2:** detect divergence mid-life (periodic tick, logged, per-file heal) or keep it boot-only? Rec:
  mid-life, because latent drift detonating at the next recreate is the outage shape.
- **F-3:** split one file across transactions (a partially-written file becomes possible: name the
  bound, keep the manifest `indexed` only after the LAST txn) or raise the cap (needs a store-side
  measurement) or a per-file statement budget that refuses loudly? Rec: split, with the manifest row as
  the commit marker.
- **F-4:** async reconcile with a status handle, or progress notifications, or document the timeout?
- **F-5:** does 11c's per-file heal land before 11a/11b and 11b consume it, or does 11b's reconciler
  subsume #355 and 11c ship only items 1, 3, 4, 5, 6 and 7? The operator decides; never build two
  reconcilers.
- **Deploy paradox:** the recreate that deploys 11c can itself trigger the unknown purge. Budget that
  window. Item 1's log line is what makes it informative rather than wasted.

## Hazards
- `test_comms_tool.py` is under uncommitted 63c edit at this writing: start from a fetched, committed base.
- Landmines (MEMORY.md): do NOT `lore-deploy start` lore-lore (hand-rolled mount). Capture
  `podman inspect --format '{{.Config.CreateCommand}}'` before `rm`. Rebuild and recreate, never restart.
  Tests never touch `:18500`.

## Entry check (RELATIVE facts only)
1. `lore_index()` shows `files_failed ≥ 1`, and the failed file is `loremaster/tests/test_comms_tool.py`
   (confirm by name from the reconcile log or the manifest row).
2. The cold-boot receipt directory exists, and its README has the Resolutions section.
3. The last recreate's podman log `reconcile.summary` has a non-empty `tiers_rebuilt`. ⚠ Per the finding
   above, this shows only that a sweep ran. Pair it with a PURGE-proving signal (`files_purged`, or a
   `delete_by_tier` trace) before treating #355 as reproduced.
4. Premise probe: `reconcile_store_divergence` still has no logger call on the purge path (read it).
5. Suite green at HEAD. `pending_contract_gate.py --currency` shows 0 RED_ORPHANED. Check that 11a/11b
   have not started (INDEX).

## Exit
**contract → contract-adversary (MANDATORY) → build → cold REFUTE audit → commit.** Gates: scoped pytest,
the full suite ALONE with `-n 12` (never `-n auto`, #466), `scripts/typecheck.sh`, `uv run ruff check .`,
and `uv run python scripts/pending_contract_gate.py --currency` with 0 RED_ORPHANED. Exit adds:
(a) a recreate on the test-store shape, or a measured production boot, shows **no purge on an in-sync
manifest, proven by the new decision log line reading `action=none` (NOT by `tiers_rebuilt: []`)**, and
a LOGGED trigger and scope whenever a heal fires, with a constructed-divergence positive control;
(b) `test_comms_tool.py` indexes (`lore_index()` `files_failed: 0`, or a named different file);
(c) the boot budget is re-measured and `CLAUDE.md` §Deploy is corrected;
(d) mutation proofs on the log line, the fallback outcome line, and the shared periodic helper.
Findings are resolved with receipts, and the INDEX gets a row and a Log line.
