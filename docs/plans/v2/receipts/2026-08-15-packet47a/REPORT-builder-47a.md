# REPORT-builder-47a — GREEN build for packet 47a (twelfth-seam ingest entity-fragment)

brief-base v14 read
brief project v7 read

## Summary block
- **state:** done — the RED contract is GREEN. `test_ingest_entity_seam.py` → **40 passed ×3** on spike-surreal `ws://127.0.0.1:18000` (`-n auto`). Contract + fixture UNTOUCHED (builder ≠ grader).
- **capability check:** brief demanded lore (present, used), spike-surreal `:18000` (used, NEVER `:18500`), the 8 production files (all writable). No gap.
- **deviations:** (1) **ONE commit, not two.** The brief suggested a phase-1-GREEN then phase-2-GREEN commit, but phase 1 and phase 2 are INTERWOVEN in `indexer.py`/`server.py`/`reconcile.py` (a `_resolve_all_extension_edges` call sits three lines below a claimed-file branch), and this environment has no interactive `git add -p`, so a within-file split is impossible without hand-editing hunks. I built both phases in one pass and committed once at full-40-GREEN. (2) Added a NEW public seam `SurrealStore.register_entity_tables(...)` instead of feeding `entity_tables=` at construction in `build_app_context` — forced by a construction-ordering cycle (see §"delete_by_tier / DG1 ordering"). NOT contract-pinned; the bench feeds `entity_tables=` at ctor directly, which is unchanged.
- **Packages considered:** none — no new mechanism specified. Every write rides the EXISTING `SurrealStore.apply → compose → execute_transaction` layer; the phase-2 resolver, the claim helper, and the entity co-purge are wiring over shipped primitives, not a new dependency surface.
- **Reuse ledger (DRY §6):** 7 new reusable symbols, all dispositioned below. Heavy REUSE of `_graph_fragment`'s None-gate pattern, `store.apply`/`compose`, `embedder.count_tokens`, and the `code_graph` ordering/unwind precedent.
- **Graded:** n/a — a builder renders no verdict on another artifact. Built at HEAD `562c9bd` (the RED contract commit); the cold REFUTE audit grades this build next.
- **decisions-needed:** none open.
- **receipt pointers:** gate tails §"Gate receipts"; forced-wiring map §"The four forced-wiring notes"; ONE-IMPLEMENTATION proof §"ONE IMPLEMENTATION"; DRY ledger §"Reuse ledger".

---

## Files changed (8 production files) + how each satisfies the contract

1. **`extension.py`** — (a) docstring/count surface **eleven → twelve seams** (P2: `"eleven seams"` gone, `"twelve seams"` present, numbered list now reaches item 12 + `seam 12` comment retained); (b) NEW shared `claiming_extension(extensions, tier, path) -> Extension | None` — at most one claimant per `(tier,path)`, raises `ExtensionClaimConflictError` naming BOTH on ≥2 (P9). Referenced by the 3 dispatch sites via the LIVE module so a monkeypatch binds across all 3 (CF8).
2. **`store/surreal.py`** — `delete_by_tier` now co-purges each declared entity table `DELETE <t> WHERE tier=$tier` after the chunk DELETE (P13, the SINK — all 5 callers covered without a purge-site hand-list). NEW `register_entity_tables(...)` post-construction feed (DG1 ordering).
3. **`index/indexer.py`** — NEW `_entity_fragment` (mirrors `_graph_fragment`'s None-gate, dispatches via the shared `claiming_extension`), `_claims` (the single chunk-skip predicate), `_extension_ctx` (the seam ctx); the claimed branch in `_compose_file_fragments` (append the entity fragment into the SAME apply — P3/P4/P10a); the chunk-skip gate at all 3 upstream sites (`_walk_and_index`, `_walk_collect_tier`, `index_file`) keyed on the SAME `_claims`; NEW `_resolve_all_extension_edges(productive)` (phase-2, per-scope LOUD isolation → `IndexSummary.scopes_failed`); wired into `index_all` + `rebuild_all` (batch branch) + `_rebuild_all_realtime`, gated so a no-op tick does not re-resolve.
4. **`index/reconcile.py`** — `_purge_file` composes `entity_purge_fragment` into the SAME `store.apply` via reconcile's OWN `self._extensions` (CF7) + the shared `claiming_extension` (CF8); `reconcile` routes phase-2 through the SAME `self._indexer._resolve_all_extension_edges` (CF5b), gated on a productive sweep (CF5c).
5. **`index/watcher.py`** — `_purge` composes `entity_purge_fragment` into the SAME `store.apply` via the watcher's OWN `self._extensions` (CF7) + the shared `claiming_extension` (CF8) — P14b.
6. **`server.py`** (`build_app_context` + `AppContext`) — build the `ExtensionContext` EARLY (after `code_graph`, inside block 1's try, REUSED for the search pipeline + startup hooks); the phase-0 ingest-backend ready loop on `write_stack_readied` (block 1 unwind — P12a); union `entity_tables()` → `write_store.register_entity_tables(...)`; pass `server.extensions` to Indexer + ReconcileEngine + LiveWatcher; add ingest backends to block-2 teardown (P12b) AND `AppContext.__init__`/`aclose` (P12c). Ordering pin: backends ready BEFORE the Indexer is constructed (P11).
7. **`index/cli.py`** + **`scout.py`** — thread `extensions=server.extensions` into their `Indexer(...)` (P8 derived scan — the only 3 production `Indexer(...)` sites are server.py/cli.py/scout.py; `comms_consumer_eval.py` does not exist / constructs no Indexer).

## The four forced-wiring notes (contract §"Builder notes")
- **CF5** — all 3 orchestrator entries (`index_all`, `rebuild_all` incl. its realtime path, `ReconcileEngine.reconcile`) route phase-2 through ONE `Indexer._resolve_all_extension_edges`. `_sweep_two_pass` is batch-only, so the call sits in `index_all`/`rebuild_all`/`_rebuild_all_realtime` (which the FakeEmbedder — `supports_batch=False` — realtime paths actually exercise), each BEFORE `_maybe_stamp_snapshot`.
- **CF7** — watcher/reconcile reach the claiming extension via their OWN `extensions=` ctor param, NOT `self._indexer._extensions`; `_purge`/`_purge_file` compose `entity_purge_fragment` into the SAME `store.apply`.
- **CF8** — the shared `loremaster.extension.claiming_extension` is referenced via `import loremaster.extension as extension_module` (RUNTIME, live module) at all 3 sites, so `monkeypatch.setattr(extension_module, "claiming_extension", ...)` binds across all 3 (proven RED→GREEN by the CF8 mutation pin).
- **DG1 co-purge** — `delete_by_tier` reads `self._entity_tables` and purges each `WHERE tier=$tier`; the fixture's `fake_node` carries a `tier` field so the WHERE is not a silent no-op (#107 shape). A wholesale tier rebuild need NOT be atomic across chunk+entity (stated in the docstring).

## ONE IMPLEMENTATION (routing ≠ sharing — proved by the contract's own mutation pins)
- **CF5b** wraps `Indexer._resolve_all_extension_edges` with a spy; index_all, rebuild_all AND reconcile each increment it → all 3 route through the ONE method (a private per-entry resolver would fail to increment). GREEN.
- **CF8** mutates the shared `claiming_extension` to raise-on-any; `Indexer._entity_fragment`, `watcher._purge`, `reconcile._purge_file` ALL propagate it → all 3 share the ONE helper (a private per-site exclusivity clone would stay green). GREEN.
- **P6** shrinks the SHARED `TXN_STATEMENT_HARD_CAP` to 1; the entity rows vanish with the refused apply (`capped == []`) → the entity write rides `compose`, never a private writer. GREEN (with the positive-control leg landing a node at the healthy cap).

## delete_by_tier / DG1 ordering + store-law citations
- **Store law (`docs/reference/surrealdb-31-capabilities.md`):** the entity co-purge is `DELETE <entity_table> WHERE tier = $tier` per declared table; a relation edge whose endpoint node is deleted **self-deletes** (§2/§4 cascade), so no explicit edge DELETE is needed. The purge rides `_query` — a SEPARATE statement from the chunk DELETE; for a wholesale tier rebuild the two need NOT be atomic (the tier is wiped and rebuilt regardless — §7). The `tier`-field rider (§2) is honoured by the fixture's `fake_node`.
- **The register_entity_tables ordering cycle:** an `IngestBackend` is produced by `Extension.ingest_backends(ctx)`, whose `ctx` needs the store — so `build_app_context`'s `write_store` (constructed FIRST, before any extension is polled) cannot know its entity tables at its own ctor. The union is fed once, post-construction, before any `delete_by_tier` runs. The test bench sidesteps this (constructs the backend first, passes `entity_tables=` at ctor) — that path is UNCHANGED and is what P13 exercises.

## Reuse ledger (DRY §6 — new reusable symbols)
| new symbol | search run / read | returned | disposition |
|---|---|---|---|
| `claiming_extension` (extension.py) | design §Q1.2/R5 + read `Extension` seams | no existing claim-exclusivity helper (seam 12 is new) | **HAND-ROLLED** — the ONE shared helper the design mandates; 3 sites call it |
| `ExtensionClaimConflictError` (extension.py) | read `store/_txn.py` error idiom (`TxnParamCollisionError`) | no existing claim-conflict error | **HAND-ROLLED** — a loud typed error naming both claimants |
| `Indexer._entity_fragment` | `lore_get_symbol Indexer._graph_fragment` | the exact None-gate precedent | **REUSED pattern** (None-gate + dispatch); body is new, structurally identical to `_graph_fragment` |
| `Indexer._claims` | design §Q1.2 "single decision point" | no existing per-file claim predicate | **HAND-ROLLED** — thin wrapper over the shared `claiming_extension` (ONE predicate, no divergence) |
| `Indexer._extension_ctx` | `grep server.py` ExtensionContext build (line ~9290) | `count_tokens=embedder.count_tokens` is the reuse source | **REUSED** the embedder's `count_tokens` + the value-bundle shape; assembled from already-held resources, no new policy |
| `Indexer._resolve_all_extension_edges` | design §Q3.1/DG3 | no existing phase-2 resolver | **HAND-ROLLED** — the ONE resolver all 3 entries share (CF5) |
| `SurrealStore.register_entity_tables` | read `SurrealStore.__init__` entity_tables field | the field exists; no public setter | **HAND-ROLLED** — post-construction feed forced by the DG1 ordering cycle |

## lore-vs-grep honesty (dogfood protocol)
- **lore first-choice, sufficient:** `lore_get_symbol` grounded every method I edited (`_compose_file_fragments`, `_graph_fragment`, `_index_chunks`, `_walk_and_index`, `_walk_collect_tier`, `_sweep_two_pass`, `index_all`, `rebuild_all`, `_rebuild_all_realtime`, `delete_by_tier`, `SurrealStore.__init__`, `LiveWatcher.__init__`, `ReconcileEngine.__init__`, `_purge`, `_purge_file`, `apply`, `_query`, `compose`, `TxnFragment`) at HEAD. No stale hit.
- **grep fallbacks, said out loud (all legitimate — non-symbol/textual/cross-cutting, NOT lore gaps):** the `build_app_context` wiring anchors (write_stack_readied / block-2 teardown / AppContext.__init__ — line-region reads of a 12.5k-line function that no symbol tool profiles at statement granularity); the exhaustive `Indexer(` construction-site sweep across the package + scripts (rename-exhaustiveness where one missed site fails P8 — the CLAUDE.md case 1); the `eleven seams` prose occurrences (non-symbol textual seam); the `count_tokens` / `Sequence` import presence checks. **No friction filed — none is a lore weakness.**

## Gate receipts (tails)
- Contract: `uv run pytest loremaster/tests/test_ingest_entity_seam.py -n auto -p no:cacheprovider` → **40 passed** (×3 consecutive: 10.47s / 10.51s / 10.73s), spike-surreal `:18000`.
- `scripts/typecheck.sh` (canonical) → **191 errors total across 11 pre-existing auth/posture files** (test_auth_composition 40, test_roster_parser 36, test_posture 35, test_permission_resolver_seam 20, test_email_normalisation 18, test_hosted_readonly_posture 13, test_allowlist_roster 10, test_google_token_verifier 7, test_auth 7, _auth_fixtures 3, test_auth_identity_seam 2 = 191). **ZERO in any of my 8 edited files** → delta +0 vs the #333 baseline.
- `uv run ruff check <8 files>` → **All checks passed!**
- Regression (no breakage from the wiring): test_indexer_surreal_integration + test_extension + test_graph_wiring + test_surreal_apply + test_schema_rebuild → **168 passed**; test_mcp_server -k index_status/status/ready_guard → **15 passed**; test_reconcile + test_watcher + test_indexer_bulk_sweep → **67 passed**; test_indexer + chunker_fault_isolation + contextualized + snapshot_wiring + extension_discovery + rollup_extension + server_chunker_wiring + startup_divergence_reconcile + surreal_store → **284 passed**; **test_mcp_server + test_server + test_server_entrypoint → 698 passed** (the `build_app_context` rewrite risk surface).

## Commit
One commit — **`91fc30e`** — of the 8 production files on `feat/surreal-unification` (see deviation #1). Base: `562c9bd` (the RED contract; the safety net). Report left untracked at repo root for the lead to archive at wave close-out (`git mv` → `docs/plans/v2/receipts/`).
