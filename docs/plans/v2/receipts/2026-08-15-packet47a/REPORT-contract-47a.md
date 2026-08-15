# REPORT-contract-47a (r2) — RED contract for packet 47a (twelfth-seam ingest entity-fragment)

brief-base v14 read
brief project v7 read

## Summary block
- **state:** done (revision r2 — folded the consolidated revision brief + the adversary INSUFFICIENT verdict)
- **what changed vs r1:** all 3 adversary C-DEFs FIXED (P6, P13, P20) + the missing quantifier pin ADDED (CF2) + the P8 reach gap CLOSED (CF3) + CF5/CF6/CF7/CF8 folded. Two operator-APPROVED seam-surface additions (DG1/DG2) are new inert production stubs.
- **deviations:** 26 pins → **40 tests** (several pins map to >1 test; the new CF2/CF5/CF8/P14-watcher legs added 7). No pin dropped.
- **Packages considered:** none — no new mechanism specified; DG1/DG2 add typed seam surface + wire the EXISTING `_txn` compose/apply layer. (The adversary's independent P-PKG survey AGREED with `none`.)
- **Reuse ledger:** 3 new reusable symbols dispositioned (below); heavy REUSE of harness/scaffold/discovery/graph-wiring precedents.
- **Graded:** n/a (a CONTRACT renders no verdict). Authored + revised at HEAD `0bdc6116`; every production symbol grounded live.
- **RED count:** **31 RED (behavioral), 9 GREEN (inert-default/guard/wrong-build-catcher), 0 errors** vs spike-surreal `ws://127.0.0.1:18000`, `-n auto`. Ruff clean on all 7 touched files; typecheck **191 total = the exact baseline, 0 in my 7 files** (canonical `scripts/typecheck.sh`).
- **decisions-needed:** none open — both r1 author-flags were adjudicated by the adversary + resolved here (P14 → CF7 own `extensions=` param; P20 → DG2 identifier reading, seam changed to carry the scope). Two builder-facing NOTES remain (§Builder notes): CF8's mutation binds only if `claiming_extension` is called via the live module reference (the EXTENSION_REGISTRY idiom); CF5's `_resolve_all_extension_edges` is the single method all 3 orchestrator entries must route through.
- **receipt pointers:** pin map §"Revised pin map"; C-DEF fixes §"How the 3 C-DEFs + missing pin were closed"; gate tails §"Gate receipts"; adversary receipts `REPORT-adversary-47a.md` Probe-3/4/5/6/7.

---

## Operator-approved seam-surface additions (DG1 / DG2 — new inert stubs)

These are the two seam changes the **operator APPROVED** (per the revision brief); they add typed surface, NOT logic (the wiring stays the builder's job):

- **DG1 — the entity-table channel (fixes the P13 C-DEF).** A bare `SurrealStore` cannot tell a `TYPE NORMAL` entity table from a chunk table, so `delete_by_tier` orphans entities (adversary Probe-4: purged ONLY when told `entity_tables=("fake_node",)`). Added: `IngestBackend.entity_tables() -> Sequence[str]` (Protocol method) + `SurrealStore.__init__(entity_tables: Sequence[str] = ())` (signature+store, NO co-purge). The fixture's `fake_node` carries a **`tier` field** (Fable's rider) so `DELETE fake_node WHERE tier` is not a silent no-op (#107 shape).
- **DG2 — scope-labelled resolve_edges (fixes the P20 C-DEF).** `resolve_edges -> list[TxnFragment]` returned UNLABELED fragments, so the indexer saw position `'1'`, never scope `'B'` (adversary Probe-5). Added: a frozen pydantic model `ResolvedScope(scope: str, fragment: TxnFragment)`; the seam now returns `list[ResolvedScope]`; `IndexSummary` gains `scopes_failed: list[str] = Field(default_factory=list)` (the default keeps every existing ctor site + `index_status` green — verified: 9 index_status/status pins pass).

## Full inert-stub set (production — no wiring/logic)
`extension.py`: `IngestBackend` (`ensure_ready`/`close`/**`entity_tables`**), `ResolvedScope`, the 5 seam methods, `resolve_edges -> list[ResolvedScope]`; docstring still "eleven seams" (P2 RED). · `index/indexer.py`: `Indexer.__init__(extensions=())`, `IndexSummary.scopes_failed`. · `store/surreal.py`: `SurrealStore.__init__(entity_tables=())`. · `index/watcher.py` + `index/reconcile.py`: `__init__(extensions: Sequence[Extension] = ())` → `self._extensions` (CF7, the code_graph precedent). No `_entity_fragment`, `claiming_extension`, `_resolve_all_extension_edges`, `delete_by_tier` co-purge, phase-2 trigger, or claimed branch — all BUILDER logic, all kept RED.

## Store-law grounding (probed LIVE before authoring — docs-first + verify, #107)
Unchanged from r1: DDL lands (`array<string>`, slug-leading UNIQUE index, `ENFORCED`-via-`OVERWRITE`); composite-id CREATE + bound-RecordID RELATE land; node-delete cascades edges; dangling RELATE under ENFORCED is REJECTED. Store law CITED by § (§1.1/§1.6/§2/§3/§4). Fixture oracle validated end-to-end (cross-book/newest-wins/corruption/resolve-or-drop) before the contract depended on it.

---

## How the 3 C-DEFs + the missing pin + the reach gap were closed

| adversary finding | fix | pin(s) now |
|---|---|---|
| **P6 C-DEF** — `pytest.raises` around `index_file` contradicts §Q2.3 fault-isolation (it CATCHES→FAILED, never raises; Probe-3) | **CF1** — dropped `pytest.raises`; `capped == []` is the SOLE discriminator (Probe-7: passes correct, reddens private-writer) | #11 RED-on-unbuilt (via positive-control leg) |
| **P13 C-DEF** — no seam feeds the store its entity tables (Probe-4) | **DG1** — `IngestBackend.entity_tables()` + `SurrealStore(entity_tables=)`; bench feeds it from the backend; `fake_node` has a `tier` field | #22 RED (co-purge unwired) |
| **P20 C-DEF** — unlabeled fragments, indexer can't name scope `'B'` (Probe-5) | **DG2** — `ResolvedScope(scope, fragment)` + `IndexSummary.scopes_failed`; `assert "B" in set(summary.scopes_failed)` now satisfiable | #34 RED (per-scope loop unwired) |
| **MISSING PIN** — atomicity pinned one direction only; a non-atomic separate-apply build survives P3/P4/P5 (Probe-6, QUANTIFIER LAW) | **CF2** — a claimed file with a VALID entity fragment but a POISONED FRAMEWORK fragment must leave NO orphan entity rows ∧ not INDEXED | #9 (catcher, GREEN now) + #10 (positive control, RED) |
| **REACH gap** — P8 reach = hidden `loremaster/loremaster/` constant, `scripts/` exempt (Probe-2 leg B) | **CF3** — `_production_python_roots()` derives package + every `scripts/` tree; anti-vacuity `assert sites` kept | #13 RED (widened reach) |
| CF5/DG3 — `_sweep_two_pass` is batch-only; correct union = index_all+rebuild_all+reconcile | one shared `Indexer._resolve_all_extension_edges`; rebuild_all pin + 3-site share-mutation + no-op-tick gate | #29/#30 RED, #31 GREEN-guard |
| CF6 — P15 passed via the non-claimed markdown path | require `n_chunks==0` (CLAIMED) ∧ file_text present | #25 RED |
| CF7 — P14 forced the wrong indexer-reach | watcher/reconcile own `extensions=` param (code_graph precedent); clone `test_watcher_delete_purges_graph_slice` | #23/#24 RED |
| CF8 — claim-exclusivity is policy at 3 sites | one shared `claiming_extension(extensions,tier,path)`; prove all 3 route through it by mutation | #14/#15 RED |

---

## Revised pin map (pin → design § → node # → verdict now)

PHASE 1 (nodes #1–#25):
| pin | § | node# | now |
|---|---|---|---|
| P1 inert defaults | Q1.1 | 1,2,3 | **GREEN** |
| P2 seam-count twelve | Q1.1 | 4 | RED |
| P3 claimed composition | Q1.2 | 5 | RED |
| P4 conjunction | Q2.3-f1 | 6 | RED |
| P5 transactionality (entity-fail dir) | Q2.3 | 7,8 | RED |
| **CF2 framework-atomicity (∀-dir)** | Q2.3/QUANTIFIER | 9 (**GREEN** catcher), 10 (RED ctrl) | |
| P6 ONE-IMPL mutation (CF1) | Q5/R6 | 11 | RED |
| P7 namespacing (≥2 names) | Q1.3 | 12 | RED |
| P8 derived scan (+scripts, CF3) | F3/Q1.2 | 13 | RED |
| P9+CF8 shared exclusivity helper | Q1.2/R5·D1 | 14 (helper), 15 (3-site mutation) | RED |
| P10 batch branch | Q1.2 | 16 (RED), 17 (**GREEN** guard) | |
| P11 ordering rail | Q4 | 18 | RED |
| P12 unwind (both blocks+normal) | F4 | 19,20,21 | RED |
| P13 sink purge (DG1) | F5/§7 | 22 | RED |
| P14 per-file purge (CF7 reconcile+watcher) | §7 | 23,24 | RED |
| P15 file_text CLAIMED-discriminating (CF6) | Q1.4/R4 | 25 | RED (non-blocking) |

PHASE 2 (nodes #26–#40):
| pin | § | node# | now |
|---|---|---|---|
| P16 two-phase (nodes only) | Q3.0 | 26 | RED |
| P17 phase-2 trigger (index_all) | Q3.1 | 27 | RED |
| P18 changed_scopes=None-only | Q3.2 | 28 | RED |
| **CF5 orchestrator union** | Q3.1/DG3 | 29 (rebuild_all RED), 30 (share-mutation RED), 31 (no-op gate **GREEN**) | |
| P19 resolve-or-drop | F2/Q3.1 | 32,33 | RED |
| P20 partial-failure loud (DG2) | F7/Q6 | 34 | RED |
| P21 corruption-direction | Q3.3 | 35 | RED |
| P22 cross-book newer-wins | F1/Q6 | 36 | RED |
| P23 pinned NON-FEATURE | Q3.2/Q6 | 37 | **GREEN** guard |
| P24 RELATE form + dedupe | Q5/Q6 | 38 | RED |
| P25 dirty-store ENFORCED migration | Q3.4/Q6 | 39 | **GREEN** #107 guard |
| P26 slug-leading index | F6/Q6 | 40 | **GREEN** F6 guard |

**Expected-RED node ids (declared from `--collect-only` BEFORE the run, #194):** the 31 RED = ALL nodes EXCEPT the 9 GREEN {1,2,3,9,17,31,37,39,40}. Verified BEHAVIOURAL (missing rows / missing seam method / `no shared <helper>` / not-INDEXED / DID-NOT-happen), zero collection or fixture errors. Diffed both ways: no unexpected GREEN, no RED-for-the-wrong-reason.

**inert-default/guard (pass now) vs behavior (RED now):** the 9 GREEN = the inert seam defaults (P1×3), the ONE-IMPLEMENTATION regression guards (P10b delegation, CF5c no-op-tick gate, P23 non-feature), the store-law guards the fixture already honours (P25 dirty-store, P26 slug-leading), and the CF2 wrong-build-CATCHER (framework-poison — GREEN on correct/pre-build, RED on the non-atomic build). The 31 RED each exercise wiring the builder has not written.

---

## "What WRONG build still passes this?" (load-bearing pins, incl. the new ones)

- **P4 conjunction** — `.fake→markdown` ⇒ a non-claimed `.fake` yields `n_chunks≥1`, so the chunk-skip leg rejects a forgot-skip build; the entity leg rejects a no-entity build.
- **P5 (entity-fail dir) + CF2 (framework-fail dir)** — TOGETHER pin atomicity ∀ over BOTH sides of the transaction (the QUANTIFIER LAW). P5 alone let a non-atomic separate-apply build survive (Probe-6); CF2 poisons the framework fragment with a VALID entity fragment and asserts no orphan rows — a separate-apply build leaves them.
- **P6 (CF1)** — with the cap at 1 the file's apply is refused; a compose-routed build lands NO entity rows, a private-writer build leaves them (`capped==[]`, sole discriminator; Probe-7 validated both directions).
- **P8 (CF3)** — reach spans package + `scripts/`; an `Indexer(...)` in `scripts/` that omits `extensions=` is no longer silently exempt; `assert sites` blocks vacuity.
- **P13 (DG1)** — the store is TOLD `fake_node` via the backend channel; a build that purges chunks only (or misses the table) leaves the seeded rows (Probe-4 two-way).
- **CF5 share-mutation** — wrapping `_resolve_all_extension_edges` with a spy: each of index_all/rebuild_all/reconcile must increment it; a private per-entry resolver fails to increment (routing≠sharing).
- **CF8 3-site mutation** — mutating the shared `claiming_extension` to raise-on-any: all 3 claim sites must propagate it; a private per-site exclusivity clone stays green (routing≠sharing).
- **P19 resolve-or-drop** — one resolvable + one unresolvable: the resolvable commits, the unresolvable drops (never a whole-scope abort); positive control commits two.
- **P20 (DG2)** — scope B's apply fails: A committed, C attempted, `"B" in scopes_failed` (names WHICH — satisfiable only because `ResolvedScope` carries the label).
- **P22 cross-book** — a GENUINE cross-book edge (edge `source_book`≠`out`-node book); a re-crawl re-points to the newer book, never silently drops.
- **P25 dirty-store** — legacy dangling row written UNDER the OLD un-enforced DDL (§1.4 trap), flip via OVERWRITE, fresh dangler REJECTED ∧ old row SURVIVES — no virgin-DB fixture can produce it.

## Builder notes (forced wiring the contract pins)
- **CF5:** all 3 orchestrator entries (index_all, rebuild_all, ReconcileEngine.reconcile) MUST route phase-2 through ONE `Indexer._resolve_all_extension_edges(...)`; `_sweep_two_pass` alone (the design's literal location) is batch-only and fails P17/rebuild_all.
- **CF7:** watcher/reconcile reach the claiming extension via their OWN `extensions=` param (now stubbed), NOT `self._indexer._extensions`; `_purge`/`_purge_file` compose `entity_purge_fragment` into the SAME `store.apply`.
- **CF8:** the shared `loremaster.extension.claiming_extension` must be referenced via the LIVE module (the EXTENSION_REGISTRY idiom) so the mutation binds across all 3 sites — that IS the ONE-IMPLEMENTATION guarantee.
- **DG1 co-purge:** `delete_by_tier` reads `self._entity_tables` and purges each `WHERE tier=$tier` (safe because `fake_node` carries a `tier` field); a wholesale tier rebuild need NOT be atomic across chunk+entity (state it).

## Reuse ledger (§6 — new reusable symbols; DRY)
| new symbol | lore query / read | returned | disposition |
|---|---|---|---|
| `entity_param_prefix(name)` (fixture) | read `store/surreal.py` prefixes | 5 literal producer prefixes; no central helper (design §Q1.3) | **HAND-ROLLED** — new `xt_<name>_` convention, derived from name |
| `_find_indexer_construction_sites` / `_production_python_roots` (contract) | read `scripts/registration_sites.py` | derives member-registration sites, not `Indexer(...)` calls | **HAND-ROLLED** — distinct property; same reach-law spirit (derive, never hand-list) |
| `_claiming_extension_helper` (contract) | — | test accessor reading the live module attr | **HAND-ROLLED** — the EXTENSION_REGISTRY live-read idiom, for the CF8 mutation |
| REUSED: `register_in_discovery`, `_surreal_harness`, `_enforced_relations_scaffold` (`apply_ddl`/`ghost_id`/`migration_db`), `FakeEmbedder`, `graph_roots`, `manifest.replace`, the `test_watcher_delete_purges_graph_slice` clone | — | existing | **REUSED** (cited in-file) |

## lore-vs-grep honesty (dogfood protocol)
lore first-choice + sufficient for structure: `lore_get_symbol` grounded every new stub target (`SurrealStore.__init__`, `LiveWatcher.__init__`, `ReconcileEngine.__init__`, `TxnFragment`, `IndexSummary`) at HEAD. grep fallbacks, said out loud (all legitimate — non-symbol/textual/cross-cutting, NOT lore gaps): the `test_graph_wiring.py` clone target + `rebuild_all(` call form (test-corpus lookup), the `Field`/`Sequence` import presence checks, and chunker-key config strings. No friction filed — none is a lore weakness.

## Gate receipts (tails)
- `uv run ruff check <5 prod + 2 test files>` → `All checks passed!`
- `scripts/typecheck.sh` (canonical) → **191 errors total = the exact pre-existing auth/posture baseline; 0 in my 7 files** (delta +0).
- Contract: `-n auto` → **31 failed, 9 passed, 0 errors** (behavioural REDs; node ids above).
- Regression (existing suites, no breakage from the stubs): `test_indexer_surreal_integration + test_extension + test_graph_wiring + test_surreal_apply` → 117 passed; `test_schema_rebuild + test_indexer_bulk_sweep -k status/rebuild/summary` → 52 passed; `test_mcp_server -k index_status/status/ready_guard` → 9 passed.

Not committed — the lead commits at natural boundaries. A delta-adversary re-runs next (no revision skips the adversary).
