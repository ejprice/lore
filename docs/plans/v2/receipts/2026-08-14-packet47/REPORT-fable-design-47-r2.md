# REPORT — fable-design-47 (R2: folding the Opus adversary pass)

brief-base v14 read
brief project v7 read

## Summary block
- **state:** done — design doc revised in place; all 8 adversary findings folded; standing by.
- **deliverable:** `docs/design/2026-08-14-packet47-ingest-entity-seam-design.md` (REVISED; +210 lines,
  now 816). R2 changes carry inline `[R2: Fn]` markers + a disposition table at the top (the "R2
  revision log" section).
- **deviations:** none. Writable set honored (design doc only). No live probe run — every store fact
  CITED from `surrealdb-31-capabilities.md`.
- **Packages considered:** none — no external-package-eligible mechanism specified (domain-internal glue
  reusing `compose`/`execute_transaction`/`Extension` ABC; `IngestBackend` is a stdlib `typing.Protocol`).
- **Reuse ledger:** no new code symbols (design only). Recommended symbols clone cited precedents
  (unchanged from r1: `_entity_fragment`←`_graph_fragment`, etc.). F5's fix REMOVES a proposed
  hand-list in favor of the existing `delete_by_tier` sink (more reuse, not less).
- **Graded:** design doc revised at HEAD `5770439` · HEAD-at-report `5770439` · SAME. Every code fact
  the R2 edits rest on was re-verified live at `5770439` (F3: `LoreServer.registry`→`ChunkerRegistry`,
  extensions at `server._extensions`; F4: two teardown blocks + `AppContext.aclose` hardcoded list; F5:
  `delete_by_tier` has 5 prod callers). I did NOT take the adversary's code claims on faith.
- **decisions-needed (operator):**
  1. Ratify the F1 named bound (cross-book edge correctness rides the FULL-SWEEP path; incremental
     per-scope is best-effort intra-book). This REPLACES my r1 "A-full correct everywhere" — which was
     FALSE.
  2. Transactionality Reading B (unchanged from r1) — still recommended.
  3. SPLIT 47/47a — still recommended (reinforced; build rose to ~0.32–0.38).
- **receipt pointers:** doc "R2 revision log" (disposition table) · §Q3.2 (F1 rewrite) · §Q3.1 (F2/F7) ·
  §Q1.2 (F3) · §Q4 (F4) · §7 (F5 sink) · §Q6 (F6/F8/F1/F2 fixtures) · §Q1.3 (R3 reduced).

---

## Per-finding disposition

**All 8 findings ACCEPTED. R3 (my own r1 residual) REDUCED to a non-issue on the adversary's reasoning.**
A CONFIRMED finding needs a real rebuttal to reject — I found none worth making; each survived my own
re-verification against source.

| # | sev | disposition | what changed in the doc | verified-by-me? |
|---|---|---|---|---|
| **F1** | HIGH | **ACCEPT** | §Q3.2 fully rewritten: per-`source_book` scope is INCORRECT for cross-book edges on any incremental path (a cross-book edge carries one scope but is cascade-vulnerable in BOTH endpoint books). Only the full-sweep path (`changed_scopes=None`) is correct; incremental = best-effort intra-book + a NAMED BOUND. Added the cross-book fixture (§Q6). My r1 "both directions covered / A-full correct everywhere" is retracted as FALSE. | logic re-derived against store §2/§4 cascade + graph-scout §6.1 |
| **F2** | HIGH | **ACCEPT** | resolve-or-drop is now a REQUIREMENT of `resolve_edges` (§Q3.1) — an unresolvable endpoint is dropped/tombstoned BEFORE the RELATE, never passed through (one bad endpoint would abort the whole scope's txn — store §3/§4, the DD-3.c denial). Added the partial-resolvability fixture (§Q6). | store §3/§4 |
| **F3** | MED | **ACCEPT** | §Q1.2 rewritten: `server.registry`→`ChunkerRegistry` (NOT extensions); the Indexer gains a NEW `extensions` param threaded through the 4 construction sites (`build_app_context` passes `server.extensions`, + cli/scout/comms_consumer_eval). r1's "already holds registry=server.registry" was wrong. | **confirmed live**: `LoreServer.registry` (server.py:573)→`ChunkerRegistry`; `Indexer.__init__` param `registry: ChunkerRegistry`; `server._extensions` at :380 |
| **F4** | MED | **ACCEPT** | §Q4 rewritten: `build_app_context` has TWO teardown blocks; phase-2 runs in the initial sweep (block 2), whose hardcoded teardown + `AppContext.aclose` omit the ingest backends → leak. Fix: build `ExtensionContext` EARLY (r1's "already assembles" was false — it's built at :9280, after block 1); add ingest backends to block-2 + `aclose`; unwind pin extended to a block-2 failure. | **confirmed live**: block-1 except @9250, block-2 except @9490 (hardcoded @9502-9519), `aclose` @8580-8598, phase-2 in `run_sweep` @9447, `extension_ctx` @9280 |
| **F5** | MED | **ACCEPT** | §7 rewritten: my r1 "derived-reach pin" was ITSELF a 3-method-name hand-list (the antipattern I cited) AND my caller enumeration was 2 short. Fix: co-locate the entity tier-purge INSIDE `delete_by_tier` (the sink — all 5 callers covered, no reach to enumerate); derive from the DATA operation, not the API surface. | **confirmed live**: `delete_by_tier` has 5 prod callers (lore_impact @5770439), incl. the 2 static-tier paths I missed |
| **F6** | MED | **ACCEPT** | §Q6 DDL: `UNIQUE(slug, source_book)` (slug-LEADING) — r1's `UNIQUE(source_book, slug)` inverts the store §2 lookup-key-leading idiom (a slug-only predicate would TableScan; breaks 52b's book-agnostic slug resolution). §2 citation corrected. | store §2 (leading-column-only; `UNIQUE(name, source_book)` idiom) |
| **F7** | LOW | **ACCEPT** | §Q3.1: phase-2 loop error semantics specified — per-scope isolation (a bad book doesn't deny all books), surfaced LOUDLY in `IndexSummary` (`scopes_failed`), never swallowed. Partial-failure fixture added (§Q6). | store §3 |
| **F8** | LOW | **ACCEPT** | §Q6 DDL sketches rewritten leading-clause (`DEFINE TABLE OVERWRITE …` / `DEFINE TABLE IF NOT EXISTS …`) — a trailing clause is a parse error. | store §1.1/§4 BNF |
| **R3** | — | **REDUCED** (my own r1 residual) | §Q1.3: claim-exclusivity + per-scope-separate applies mean no two extensions ever share a `compose()` call → cross-extension `xt_` collision is architecturally IMPOSSIBLE; only intra-extension self-collision remains (compose catches loudly). Charset constraint is now optional hygiene, not required. | reasoning confirmed against claim-exclusivity (§Q1.2) + `compose` fail-loud (_txn.py) |

**Rejections: none.** Every finding was real. The two HIGH findings (F1, F2) are the priority and both
are correct — F1 in particular retracts a FALSE correctness claim my r1 shipped ("A-full correct
everywhere"), which is exactly the corruption the packet exists to prevent, so accepting it is not
optional.

## Frontier refinements folded (beyond F1–F8)
- Frontier #1: added the **conjunction pin** (a claimed file yields `n_chunks=0` AND entity rows — §Q2.3).
- Frontier #2: the mutation pin asserts **"no INDEXED row"** (a `FAILED` manifest row may exist via the
  fault-isolation path), and notes the FAILED-file re-index caveat (§Q2.3).
- Frontier #3: the phase-window bound wording corrected — **minutes not seconds**, and a
  **partially-cascaded inconsistent set** during phase-1, not "nodes with no edges" (§Q3.3).

## Split re-confirmation
**SPLIT holds, reinforced.** Every finding added pins or wiring (cross-book fixture, resolve-or-drop
pin, the 4-site Indexer extension-list thread, the two-block teardown + its pin, the in-`delete_by_tier`
purge, phase-2 partial-failure pin) — the build only grew. Design ~0.15; build ~0.32–0.38; total
~0.47–0.53 ≫ 0.25. (Doc §8.)

## Self-critique (I graded my own r1, so I name where it failed)
My r1 shipped one FALSE correctness claim (F1 — "A-full correct everywhere") and committed the very
reach-attack antipattern it cited (F5 — a 3-method-name hand-list), with a wrong caller count inside
it. Both are the CLAUDE.md classes I quoted at the operator. The adversary earned its keep: a contract
built verbatim from r1 would have asserted the false claim and mis-wired the Indexer (F3). r2 closes
all of it, with every code fact re-verified live rather than taken on the adversary's word.

## lore-first / fallback disclosure
lore-first throughout (lore_get_symbol / lore_impact / lore_read grounded F3/F4/F5). One grep fallback,
disclosed: the block-2 teardown region + `extension_ctx` construction line (a construction-code textual
seam + line-anchored region — the sanctioned non-symbol / cross-cutting case, CLAUDE.md dogfood §3). No
lore friction to file — the index was fresh and every symbol resolved first try.
