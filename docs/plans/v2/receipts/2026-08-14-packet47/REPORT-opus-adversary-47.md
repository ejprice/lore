# REPORT-opus-adversary-47 — adversary pass on the packet-47 ingest-entity-seam design

brief-base v14 read
brief project v7 read

## Summary block
- **state:** done
- **role:** independent Opus-4.8 adversary (fresh frame; author was `fable-design-47`). EDITED NOTHING but this report.
- **artifact graded:** `docs/design/2026-08-14-packet47-ingest-entity-seam-design.md` (untracked working-tree file, 606 lines).
- **Graded:** working-tree design doc (git-untracked, `??`) · HEAD-at-report: `5770439` · SAME — every production symbol my verdicts rest on (`compose`, `execute_transaction`, `SurrealStore.apply`, `_compose_file_fragments`, `_graph_fragment`, `_commit_batch_file`, `_sweep_two_pass`, `build_app_context`, `delete_by_tier`, `LoreServer.registry`, `register_extension`, `Extension`, `ExtensionContext`) resolved at `5770439`.
- **Packages considered:** none — this is an advisory audit; I specified/built no mechanism.
- **Reuse ledger:** none — no new symbols introduced.
- **Graded verdict:** **SHIP-WITH-FIXES.** The design is well-grounded on the CORE hard problems (per-file atomicity, the ENFORCED dirty-store #107-shape, the two-phase forcing function, most store-law citations). But it ships **one HIGH corruption gap the packet exists to prevent** (F1), a HIGH denial-shape (F2), and four MED wiring/pin defects (F3–F6). None require a rewrite; they require pins + two operator forks reframed. A contract built verbatim from this doc as-is would assert a FALSE correctness claim ("both directions covered") and mis-wire the Indexer.
- **decisions-needed (operator/contract-adversary):**
  1. **F1 reframes R2:** per-`source_book` scope is provably insufficient for CROSS-BOOK edges on ANY incremental path (A-full included). Ratify that cross-book edge correctness DEPENDS on full-sweep re-resolution (`changed_scopes=None`), or fund reverse-dependency re-resolution. "A-full = correct everywhere" is false.
  2. **F2:** ratify that `resolve_edges` MUST resolve-or-drop each endpoint BEFORE the RELATE (one unresolved endpoint aborts the whole scope's purge+RELATE — store §3/§4), with a partial-resolvability fixture pin.
- **receipt pointers:** F1 → store §2/§4 cascade + graph-scout §6.1 (`docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-graph-scout-1.md:466-486`) + design §Q3.2/§Q3.3; F2 → store §3/§4 + design §Q3.1/§Q5; F3 → `LoreServer.registry` (server.py:573) + `Indexer.__init__` (indexer.py:391); F4 → `build_app_context` second `except BaseException` (server.py, the hardcoded-handle teardown after `indexer = Indexer(...)`); F5 → `delete_by_tier` impact (5 prod callers) + design §7; F6 → store §2 leading-column rule + design §Q6.

---

## Verdict: SHIP-WITH-FIXES

A strong ruled input. The transactionality spine is CONFIRMED sound against source. But the cross-file edge model has a corruption gap the design actively denies, and three lifecycle/wiring claims are factually wrong about the code they cite. Fixes are targeted (added pins + two reframed forks), not a rewrite.

---

## Findings (severity-ranked, most severe first)

### F1 — [HIGH · CONFIRMED] Per-`source_book` purge scope cannot restore CROSS-BOOK edges; "both directions covered" is FALSE, and the fixture is structurally blind to it

**This is the exact corruption the packet exists to prevent (graph-scout §6.1: "DELETE+CREATE loses edges silently"), reintroduced at the cross-book boundary on every incremental path — including the A-full option the author recommends as "correct everywhere."**

**The mechanism (verified against primary sources):**
- 52b's supersession is DELIBERATELY cross-edition: a 5.0 spell link → a 5.5 class row (wave-d §7; the reference's own edition is ignored). So a real edge `spell(book A) → class(book B)` exists, with `out` in a DIFFERENT book from `in`.
- Deleting EITHER endpoint cascades the edge away, SILENTLY — store ref §2 ("graph RELATION edges self-delete when an endpoint node is deleted") and §4 ("Endpoint-delete cascade … cascades the edge away … for a recreated endpoint, an absent endpoint, and an `in`-side delete alike"). Graph-scout §6.1 measured it: `DELETE spell:blight` cascaded its 2 edges; re-`CREATE` did NOT bring them back.
- A single-file (or single-book) re-ingest of **book B** purges-and-recreates book B's nodes. The `out=class(B)` node replacement **cascade-deletes the edge `A→B`** during phase 1.
- Phase 2 (`resolve_edges(changed_scopes={B})`) runs `DELETE edge WHERE source_book=$B; RELATE …book-B's-edges`. The edge `A→B` has `source_book = A` (book A declared it). It is **neither purged nor restored by scope B**. Book A is not re-scraped, so book A's phase-2 never runs. **The edge is gone, silently, until the next FULL sweep.**

**Why no `source_book` assignment fixes it (this is fundamental, not a labeling choice):** a cross-book edge is cascade-vulnerable to node changes in BOTH endpoint books, but carries exactly ONE scope. If `source_book`=declaring book (A), a re-scrape of endpoint book B loses it (above). If `source_book`=endpoint book (B), then a re-scrape of book A (the subject/`in` side) cascades A→B *and* A→C but `resolve_edges(changed_scopes={A})` finds no `source_book=A` edges to restore — worse. The only correct incremental handling is re-resolving the changed book **plus every book whose edges point INTO it** (reverse-deps), which the per-scope model does not do. **`changed_scopes=None` (the full-sweep path) is the only correct path**, because it re-resolves every scope — which is precisely why wave-d §8's "dnd re-scrapes are FULL re-crawls" is load-bearing for CORRECTNESS, not merely the performance argument the design uses it for in §Q3.2.

**The design's own claim is false.** §Q3.2 option-A row: *"correct … both directions covered (edges from AND into the changed file are in-scope)."* An edge pointing INTO book B but DECLARED by book A is not in book B's `source_book` scope. "into the changed file" (topological) ≠ "`source_book`==changed file's book" (scope). The two coincide only for intra-book edges.

**The fixture cannot see it (small-N/monoculture trap — CLAUDE.md).** §Q6's fixture uses `edge A→B` / `A→C` resolved "by exact slug" — all INTRA-book. No fixture edge crosses a book boundary, so the corruption-direction pin (§Q6) and the "both directions covered" claim are never tested against a cross-book edge. A wrong build that only ever handles intra-book scope passes the entire contract.

**This is DISTINCT from named residuals R1 (phase window) and R2 (watcher A-full vs A-sweep).** R2 is about WHETHER to resolve incrementally; F1 is that per-declaring-book scope is INCORRECT for cross-book edges on *any* incremental path. The design never identifies the scope insufficiency.

**Fix:** (a) reframe R2 — the named bound must be "cross-book edges are correct only after a full-sweep re-resolution; an incremental single-book re-ingest may silently drop a cross-book edge until the next full sweep," with the re-open trigger being incremental (non-full-recrawl) production updates; OR (b) fund reverse-dependency re-resolution. Either way, **add a fixture with a genuine cross-book edge** (an edge whose `out` node lives in a different `source_book` than the edge's own `source_book`), re-ingest the endpoint's book, and assert the edge's fate — the pin the design is missing.

---

### F2 — [HIGH · CONFIRMED] ENFORCED + one-txn-per-scope: a single unresolvable endpoint aborts the WHOLE scope's edge update (the DD-3.c denial shape)

**Store ref §3 + §4, verified:** within one `BEGIN…COMMIT`, once any statement fails the COMMIT also errors and the whole txn rolls back (§3); ENFORCED reports "ONE bad endpoint per attempt, as untyped prose, only AFTER the write is attempted, **aborting the whole txn**" (§4). Phase-2 for a scope is ONE fragment = `DELETE edge WHERE source_book=$scope; RELATE …N edges…` composed into ONE `store.apply` (design §Q3.1/§Q3.3, confirmed `apply`→`compose`→`execute_transaction`). Therefore **a single RELATE to a non-existent endpoint rejects the entire scope's purge+RELATE** — the DELETE rolls back too, so ALL of that scope's edges stay stale, and the caller gets one SurrealStoreError.

This is the **exact packet-03b DD-3.c pattern CLAUDE.md flags**: "a single legacy over-cap edge fails that statement and the agent cannot drain ANY of its inbox (total denial)." Here: one unresolvable reference in a book denies that book's ENTIRE edge set from updating.

**The design implies the mitigation but never pins it.** §Q5 says the app-level resolve step "only RELATEs endpoints it just read as existing" — good, that's the resolve-or-drop discipline. But: (a) it is not stated as a REQUIREMENT of `resolve_edges` (drop/tombstone an unresolved intent BEFORE the RELATE, never pass it through); (b) 52b's real semantics tombstone a dangling reference (wave-d §7), but the §Q6 FIXTURE "resolves edge intents by exact slug" with NO specified behavior for an unresolvable slug — a fixture that emits a RELATE for a missing slug would abort its whole scope; (c) there is no pin proving that an unresolvable intent leaves the scope's OTHER edges committed. **Add a fixture case: a scope with one resolvable + one UNRESOLVABLE edge intent; assert the resolvable edge commits and the unresolvable one is dropped/tombstoned — never that the whole scope aborts.** Without this pin, a build that passes every unresolved intent to RELATE is green on the happy-path fixture and denies whole scopes in production.

---

### F3 — [MED · CONFIRMED] The Indexer↔extension wiring is mis-typed: `server.registry` is the ChunkerRegistry, NOT the extension list

Design §Q1.2: *"`_entity_fragment` consults `self._registry`'s extensions (the Indexer already holds `registry=server.registry`)… It asks each registered extension `claims(tier, path)`."* Design §Q4 pseudocode: `for ext in server.registry:  # the registered extensions`.

**Both are wrong about the type.** `LoreServer.registry` (server.py:573) is `@property → ChunkerRegistry` ("The composed chunker registry"). `Indexer.__init__` (indexer.py:391) types the param `registry: ChunkerRegistry` and `build_app_context` passes `registry=server.registry` (the chunker registry). **The Indexer holds chunkers, not `Extension` objects** — it has no path to `claims()` / `entity_fragment()`. Iterating `server.registry` yields chunkers, which have no `claims` method.

The extension list lives at `server._extensions` (appended by `register_extension`, server.py:627). `build_app_context` can reach it via `server`, but the **Indexer cannot** — the phase-1 gating mechanism as described is unwired. This needs a NEW Indexer constructor parameter (the extension list, or a claims-dispatching accessor), threaded through the four production Indexer construction sites (wave-d §3 names them: `from_config`, index/cli.py, scout.py, comms_consumer_eval.py — all via `__init__`). The design glosses a real wiring change as "already holds," and the mis-citation is exactly the natural-language-surface-no-gate-checks class. **Fix:** specify the Indexer's extension-list parameter and its wiring at all construction sites; correct the "already holds registry=server.registry" claim.

---

### F4 — [MED · CONFIRMED] The ordering-rail unwind is analyzed for only ONE of `build_app_context`'s TWO teardown blocks — ingest backends leak on a startup/sweep failure (and on normal shutdown)

`build_app_context` (server.py:8973+) has **two** `except BaseException` teardowns:
1. The **write-stack ready guard** (`write_stack_readied` list, closed newest-first). The design's Q4 wiring (ready each ingest backend here, append to `write_stack_readied`) is CORRECT and its unwind pin (fault-inject `ingest_backends[i].ensure_ready` → earlier collaborators `.close()`d) tests exactly this block. ✓
2. A **second guard around the startup hooks + initial sweep + schema rebuild** (`await server.run_startup_hooks(...)` … `await watcher.run_sweep()` …). This block's `except` closes a **HARDCODED handle list** (`memory_backend, task_ledger, finding_ledger, agent_registry, brief_ledger, snapshot_stamper, diff_engine, manifest, code_graph, write_store`) — it does **not** iterate `write_stack_readied`, and it names no ingest backend.

**Consequence:** the ingest backends are readied in block 1 (survive), but **phase-2 `resolve_edges` runs inside the initial `watcher.run_sweep()` — i.e. inside block 2** (design §Q3.1: phase-2 fires at `_sweep_two_pass` completion). A phase-2 failure (or a failing startup hook, or a watcher that won't start) triggers block 2's teardown, which closes everything EXCEPT the ingest backends → **leaked domain-store connection on the startup-failure path.** The design's unwind pin (which only fault-injects the backend's OWN `ensure_ready`, failing in block 1) cannot see this — the exact "the rider is part of the ruling" gap: the pin tests the block that already unwinds and never the block that doesn't.

Separately, `AppContext` (the normal-shutdown aclose path) is constructed with a fixed collaborator set; the design does not thread the ingest backends into it either, so a clean shutdown also never closes them. **Fix:** add the ingest backends to block 2's teardown AND to `AppContext`'s normal close; extend the unwind pin to fault-inject a block-2 failure (e.g. a failing phase-2 apply during the initial sweep) and assert the ingest backend was `.close()`d.

**Also (MED, same family): the ExtensionContext ordering.** §Q4's pseudocode reads `ingest_ctx = <the ExtensionContext build_app_context already assembles>` — but `extension_ctx` is constructed AFTER block 1 closes and after `indexer = Indexer(...)`. At the block-1 insertion point (right after `code_graph`), that context does not yet exist. The builder must either move the `ExtensionContext` build earlier (its inputs — `write_store, embedder, config, count_tokens, manifest` — are all ready by then) or pass a partial context to `ingest_backends`. The design must specify which; "already assembles" is false at that point.

---

### F5 — [MED · CONFIRMED] The derived-reach purge pin is STILL a method-name hand-list — the INSTRUMENT-0 antipattern the design cites against itself

§7 correctly catches the 5th site (`delete_by_tier`) and correctly demands a DERIVED set. But its proposed derivation keys on *"every call site of `code_graph.purge_file_fragment` / `delete_file_graph` / `delete_by_tier`."* **That is a hand-list of three receiver names** — precisely the shape CLAUDE.md's instrument-lesson table records as defeated ("SDK gate keyed on 3 method names → defeated by the other 30"; "2 receiver names → six other doors"). A slice-removal that does not route through one of those three names escapes the "derived" set — and `delete_by_tier` ITSELF is a raw `DELETE {CHUNK_TABLE} WHERE tier = $tier` (surreal.py:1191), proving slice-removal can happen with no "purge" method at all. When a future `delete_something_by_tier` raw-DELETEs chunks, the name-keyed set does NOT grow, the pin stays GREEN, and the entity slice orphans — the seventh defeat.

**Grounding the fragility in the design's own text:** `delete_by_tier` has **5** production callers (lore_impact, HEAD `5770439`): `_index_static_tier`, `_prepare_static_tier_for_collect`, `_purge_tier_for_rebuild`, `_rebuild_all_realtime`, `reconcile_store_divergence`. The design §7 enumerates only three (`_purge_tier_for_rebuild`, `_rebuild_all`, "the reconcile tier purge") — **its own hand-list is already 2 sites short**, and two of the missed callers are STATIC-TIER paths (`_index_static_tier`, `_prepare_static_tier_for_collect`) — exactly where a claimed machine-tier file is processed.

**Fix:** (a) put the tier-entity-purge INSIDE `delete_by_tier` (or a sibling both callers invoke) — ONE IMPLEMENTATION, all 5 callers covered without enumerating them (the design leaves this as "a `delete_entities_by_tier` analog, or the extension contributes a tier-purge fragment" — pick the in-function form); (b) derive the reach from the DATA operation ("removes/replaces a claimed tier's chunk or manifest rows"), not the API surface (three method names). Note also: `delete_by_tier` runs via a single-statement `_query` (its own private path) and any co-located entity tier-purge would be a SEPARATE statement/txn — the design should state whether chunk-tier-purge and entity-tier-purge need to be atomic (probably not for a wholesale rebuild, but say so).

---

### F6 — [MED · CONFIRMED] The fixture `fake_node` UNIQUE index column order contradicts the store-law idiom it cites; it will NOT serve the exact-slug lookup the design claims

§Q6: *"`UNIQUE(source_book, slug)` index `IF NOT EXISTS` (§1.1, **and the leading-column serves exact-slug lookup** — store ref §2)."*

Store ref §2 (verified): composite indexes are **leading-column only**; a trailing-column-only predicate TableScans. Its idiom is *"ONE `UNIQUE(name, source_book)` serves both cross-book uniqueness and the **leading-column exact-name lookup**"* — the LOOKUP KEY (name/slug) is LEADING. The design **inverted it** to `UNIQUE(source_book, slug)` — `source_book` leading, `slug` trailing — so a `slug`-only predicate **TableScans**, not IndexScans. The design's parenthetical "the leading-column serves exact-slug lookup" is false: the leading column is `source_book`, not `slug`.

**Why it matters beyond the fixture:** cross-edition resolution (52b) resolves a slug to a node **book-agnostically** (prefer 5.5 → alias → 5.0), i.e. it needs to find ALL rows with a given slug across books — a slug-LEADING lookup. `UNIQUE(source_book, slug)` cannot serve that. Per the "a reference pattern is a defect generator" law, the fixture's index shape will be cloned into packet 51's real schema (wave-d §7: "composite ids `[source_book, slug]`; scalars as indexed FIELDS") and break real cross-edition resolution. For the fixture alone the TableScan is a correctness non-issue (small N), but the store-law CLAIM is wrong and the pattern propagates. **Fix:** either `UNIQUE(slug, source_book)` (slug-leading, still unique) or a separate slug-leading lookup index; correct the §2 citation.

---

### F7 — [LOW · PLAUSIBLE] Partial phase-2 error handling is unspecified — a false-clear risk

Phase-2 applies each scope's fragment in a SEPARATE `store.apply` (§Q3.1: "one scope = one atomic purge+RELATE txn"). The design does not specify what happens when scope k's apply raises mid-loop: are scopes 1..k-1 (committed) left resolved while k..N are not, silently? Is the error propagated (→ leaks per F4) or logged-and-continued (→ silent partial edge resolution)? A dirty store carrying a prior version's edges for the un-run scopes is a false clear whose bytes look "healthy" (nodes present, some edges present). **Fix:** specify phase-2 loop error semantics and pin a partial-failure case (force scope 2's apply to fail; assert scope 1 committed, scope 3 still attempted or the whole thing marked incomplete — and that the failure is LOUD, not swallowed).

---

### F8 — [LOW · CONFIRMED] DDL sketches place `OVERWRITE` / `IF NOT EXISTS` TRAILING (parse error if literal)

§Q6: `DEFINE TABLE fake_node TYPE NORMAL SCHEMAFULL` **`IF NOT EXISTS`** and `DEFINE TABLE fake_link TYPE RELATION … SCHEMAFULL` **`OVERWRITE`** — both clauses appended at the END. Store ref §1.1 / §4 "Shape to ship" and the vendor BNF put the clause immediately after `DEFINE TABLE`: `DEFINE TABLE [OVERWRITE | IF NOT EXISTS] @name …`. A trailing clause is a parse error. The design's §Q3.4 gets it right (`DEFINE TABLE OVERWRITE …`); §Q6's sketches are inconsistent with it. Low impact (a builder reading store law places them correctly) but it is the natural-language-DDL-surface class the repo keeps getting bitten by. **Fix:** write the sketches in leading-clause form.

---

## Frontier coverage (the brief's floor + my own)

| # | Frontier | Verdict |
|---|---|---|
| 1 | Wrong-build survivability | §9 self-attack is thorough (7 pins). Gaps I add: no pin that a claimed file yields BOTH n_chunks=0 AND entity rows (a build that composes entities but forgets the chunk-skip is unpinned); F1's cross-book build survives; F2's pass-unresolved-to-RELATE build survives. |
| 2 | Quantifier law (per-file atomicity) | **SOUND — CONFIRMED.** `apply`→`compose`→`execute_transaction` puts all phase-1 producers in ONE `BEGIN…COMMIT`; a domain rejection raises `SurrealStoreError` LOUDLY (store §3, not a statement[0]-only silent partial). Witness = manifest row is correct. Refinement: the fault-isolation path (`_commit_batch_file` / realtime) CATCHES `SurrealStoreError` and writes a manifest **FAILED** row — so the pin must assert "no INDEXED row" (the design's wording, correct), not "no manifest row." "re-indexes next pass" is optimistic for an unchanged FAILED file (inherited mtime fast-path); worth a note but inherited behavior. |
| 3 | Phase-1↔phase-2 window | Named as a bound (R1) with a re-open trigger; acceptable given the dark tier. Two refinements: (a) "seconds" understates a full re-crawl's phase-1 (minutes for a large corpus); (b) mid-sweep the edge set is not "nodes with no edges" but a PARTIALLY-cascaded/inconsistent set (progressive cascade during phase-1). Bound still acceptable. |
| 4 | Edge scope vs cross-book/cross-edition | **F1 (HIGH).** The prime suspect confirmed — per-`source_book` scope cannot restore cascade-deleted cross-book edges on any incremental path. |
| 5 | Reach-attack closed? | **F5 (MED).** Derivation is still a 3-method-name hand-list; design's own caller enumeration is 2 sites short (5 real). |
| 6 | ONE IMPLEMENTATION | **SOUND — CONFIRMED** for the write path: phase-1 and phase-2 both ride `store.apply`→`compose`→`execute_transaction`. §Q5's prove-by-mutation (move `TXN_STATEMENT_HARD_CAP`, a real constant checked in `compose`) is a valid pin, and R6 correctly demands the mutation reach the ENTITY path. Note: phase-2 READS ride the domain store's own connection (fine — reads need no txn driver; same DB sees committed nodes). |
| 7 | False clear | Dirty-store ENFORCED #107-shape (Q3.4) is the key one and is **well-handled** (OVERWRITE-lands-ENFORCED confirmed store §1.1/§4; the migration pin is exactly right). Additional false clears: F1 (dirty store carrying a prior version's cross-book edges), F7 (partial phase-2). |
| 8 | Ordering-rail unwind | **F4 (MED).** Block-1 wiring is correct; block-2 teardown + normal-shutdown close omit the ingest backends, and the unwind pin only tests block 1. |
| 9 | Transactionality ambiguity (Reading A vs B) | **SOUND.** Reading B (manifest witness) is correctly adopted; Reading A's rejection is well-argued against wave-d §1 R-A (prose XOR machine tiers, separate file trees) — no file is both chunked and entity-bearing in the ruled corpus. |

## Notes that REDUCE a residual (design is more robust than it claims)
- **R3 (Extension.name charset) is over-stated.** The `xt_{name}_` cross-extension collision the design frets about requires two extensions to contribute params to the SAME file's transaction. Claim-exclusivity (§Q1.2, at most one `claims()` per file) + per-scope-separate phase-2 applies mean **no two extensions ever compose into one transaction** — so a cross-extension `xt_` collision is architecturally impossible, not merely fail-loud. The only residual is an INTRA-extension self-collision (one extension's own two params colliding after prefixing), which `compose` catches loudly (`TxnParamCollisionError`, confirmed at _txn.py:314). A charset constraint is still fine defensively, but "two adversarially-named extensions crash at boot" is not reachable given the architecture. The adversary confirms: no silent-drop path exists (compose is fail-loud) — R3's core question answered YES-safe.

## Store-law verification (primary sources, not the design's word)
All CONFIRMED against `docs/reference/surrealdb-31-capabilities.md` (read in full) and live symbols at `5770439`:
- ENFORCED lands only via `DEFINE TABLE OVERWRITE`; `IF NOT EXISTS` is a silent no-op on an existing edge table — §1.1 (TABLE RELATION row) + §4 (migration row). Design Q3.4 correct.
- `RELATE` bound-RecordID form; dangling-edge hazard; endpoint-delete cascade on either endpoint — §4. Underpins F1.
- `execute_transaction` verifies every statement; whole-txn rollback on any failure — §3 + `execute_transaction` (_txn.py:1238). Underpins F2 and frontier #2.
- Composite index leading-column-only; lookup-key-leading idiom — §2. Underpins F6.
- Corruption directions (DELETE+CREATE loses / UPDATE keeps stale) — graph-scout §6.1 (`…REPORT-graph-scout-1.md:466-486`). Underpins F1.

No lore friction to file — the index was fresh (last_sync ~4min, watching `/workspace`@`5770439`) and every symbol/span resolved first try. No grep fallback was needed.
