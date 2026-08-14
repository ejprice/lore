# REPORT — fable-design-47 (packet 47 design sidecar)

brief-base v14 read
brief project v7 read

## Summary block
- **state:** done — ruled design doc delivered; standing by for follow-ups.
- **deliverable:** `docs/design/2026-08-14-packet47-ingest-entity-seam-design.md` (the RULED design
  for the twelfth seam — framework only; dnd domain scope-OUT). This report is the digest + pointers.
- **deviations:** none. Writable set honored (design doc only; no code/test/other-doc touched). No live
  probe run — every store fact is CITED from `surrealdb-31-capabilities.md` (docs-first law; the
  ENFORCED/relation-table facts were already probed and recorded there, §1.1/§4).
- **Packages considered:** none — no external-package-eligible mechanism specified. The design is
  domain-internal glue that REUSES existing machinery (`compose`/`execute_transaction`/`TxnFragment`,
  the `Extension` ABC, the `write_stack_readied` rail); the one new type (`IngestBackend`) is a stdlib
  `typing.Protocol`, not a library candidate.
- **Reuse ledger:** no new code symbols (design only). Every recommended symbol CLONES a cited
  precedent: `_entity_fragment`←`Indexer._graph_fragment`; `entity_fragment`←`build_file_graph_fragment`;
  `entity_purge_fragment`←`purge_file_fragment`; the ingest backend duck-type←`code_graph`/`manifest` on
  `write_stack_readied`; `FakeDomainStore`←`SurrealCodeGraph`/`FloorCalibrationStore`. No hand-rolled
  policy proposed.
- **Graded:** grounded against HEAD `5770439` · HEAD-at-report `5770439` · SAME. (Design doc, not a
  verdict on another artifact; sha recorded because the doc cites live symbols. All symbols in §Q1–§Q7
  were resolved live via lore/Read at this sha.)
- **decisions-needed (operator/adversary):**
  1. Ratify the post-reframe transactionality pin (Reading B) — see §Q2.2 below.
  2. Watcher incremental fork: A-full vs A-sweep+named-bound (§Q3.2). I recommend A-full.
  3. SPLIT 47(design)/47a(build)? — I recommend SPLIT (design prices build ≫0.25).
  4. Residuals R1/R3/R5 (§9 of the doc) — phase-gap marker, `name` charset, claim exclusivity.
- **receipt pointers:** doc §Q1 (seams/composition/namespacing) · §Q2.2 (ambiguity flag) · §Q3
  (two-phase edges — the hardest) · §Q3.4 (the #107 dirty-store false clear) · §Q4 (ordering rail) ·
  §7 (the reach-attack: delete_by_tier is a 5th purge site) · §8 (split pricing) · §9 (self-attack).

---

## The six design questions — settled answers (digest; full text in the doc, cited by store-ref §)

**Q1 — Fragment shape.** Seam 12 = five inert-default `Extension` methods: `claims(tier,path)->bool` ·
`entity_fragment(tier,path,text,ctx)->TxnFragment|None` (pure, NODES only, params `xt_<name>_`) ·
`entity_purge_fragment(tier,path)->TxnFragment|None` · `resolve_edges(ctx,changed_scopes)->list[TxnFragment]`
(phase 2, async) · `ingest_backends(ctx)->list[IngestBackend]` (phase 0 — the readiable domain store).
Composition mirrors `_graph_fragment`'s None-gate: a new `_entity_fragment` helper in
`_compose_file_fragments` asks each extension `claims()` (≤1 claimant per file, else loud error); a
claimed file gets `records=[]` so `replace_file_fragment` composes a bare chunk-purge DELETE and the
manifest is `n_chunks=0` (chunk-skip and entity-compose key off the SAME claim result). **Namespacing:
NO central registry to edit — `compose` detects collisions dynamically (`TxnParamCollisionError`,
fail-loud); the five prefixes are `st_/ft_/mf_/gr_/sn_`; `xt_<name>_` is guaranteed distinct + a
namespacing pin.** Multi-node-type + edges (not spell-only) per rulings §2. Store ref §3/§4.

**Q2 — Transactionality.** `store.apply` composes all a claimed file's producers into ONE
`execute_transaction` (every statement checked — store ref §3); entity failure rolls back the manifest
row → file never `INDEXED`. The atomicity WITNESS is the manifest row (phase-1); phase-2 edges are a
SEPARATE transaction by necessity (ENFORCED needs committed endpoints).

**Q3 — Cross-file edges (the hardest).** Two-phase forced by `ENFORCED` (store ref §4: RELATE needs both
endpoints to exist; the graph's name-record dangling trick does NOT transfer to typed entity nodes).
Phase-1 = per-file NODE fragment (atomic with the file). Phase-2 = per-`source_book` **purge-then-RELATE
in ONE txn** (the measured corruption mitigation — DELETE loses edges, UPDATE keeps stale ones; store
ref §2). **Trigger:** the clean completion point of `_sweep_two_pass` (after `_summarize`, before
return), NOT `on_startup`. **Incremental/watcher fork (escalated):** (A) re-resolve the changed file's
book scope on any watched change — RECOMMENDED; (B) defer to next sweep as a NAMED PINNED BOUND (re-open
trigger: incremental non-recrawl production updates) — cheaper, a trust window. I recommend A-full;
operator right-sizes. **§Q3.4 mandatory pin:** ENFORCED migrated with `IF NOT EXISTS` is a SILENT NO-OP
(#107 shape, store ref §1.1/§4) → relation tables use `DEFINE TABLE OVERWRITE … ENFORCED`; the dirty-store
migration pin (OLD ddl → dangling row → NEW ddl via OVERWRITE → guard took AND old row survived) is the
one pin no virgin-DB fixture can produce (store ref §1.6).

**Q4 — Ordering rail.** The ingest backend's `ensure_ready` (DDL) is awaited + appended to
`write_stack_readied` right after `code_graph` and before the `Indexer` is constructed, INSIDE the
`try` whose `BaseException` closes readied collaborators newest-first — so a partial-ready failure
unwinds (`TestWriteStackUnwindIncludesCommsLedgers` pattern). Grounded live at `build_app_context`
(~server.py:9095 `write_stack_readied`, code_graph ~:9131, Indexer ~:9258 at HEAD 5770439).

**Q5 — One implementation.** All entity writes (phase 1 composed; phase 2 applied by the indexer) ride
`store.apply`→`compose`→`execute_transaction` — never a private query path; the domain store's own
connection is READ-only (endpoint resolution + 53 tools). RELATE uses bound-RecordID form; ENFORCED
guards both endpoints; dedupe before RELATE (UNIQUE(in,out) is a backstop). PROVE BY MUTATION that the
ENTITY path flows through `compose` (routing ≠ sharing — #102/#120), and that the mutation reaches
entities specifically (R6).

**Q6 — Fixture extension.** `FakeIngestExtension` (name `"fake"`, injected via `EXTENSION_REGISTRY`
monkeypatch, the packet-46 fake-registry analog) claims `.fake` files, emits ≥2 node kinds + ≥1
ENFORCED relation edge; `FakeDomainStore` clones `SurrealCodeGraph` (own connection,
`execute_transaction`, `ensure_ready`/`close`) with DDL under store law (plain table + fields OVERWRITE
+ indexes IF NOT EXISTS + `fake_link` relation table via OVERWRITE ENFORCED UNIQUE(in,out)). Exercised
on spike-surreal `:18000` ONLY. Includes the dirty-store migration case + the corruption-direction pin.

---

## Flags (surfaced, not silently resolved)

- **TRANSACTIONALITY AMBIGUITY (settled + flagged, brief-mandated).** Packet file Exit line pins
  *"entity write fails ⇒ chunk write rolled back"* (PRE-transmute); wave-d §4 rules a claimed file
  SKIPS chunking, so chunks+entities never coexist and that literal pin is **unrepresentable**. Both
  readings are in doc §Q2.2. **Recommended (Reading B):** entity failure ⇒ the file's manifest/file_text
  roll back together; nothing recorded `INDEXED`; positive control = clean ingest commits entity rows +
  manifest atomically. I could find no case where a file is both prose-chunked and machine-entity-bearing
  (the transmute tiers are separate trees), so Reading A is rejected on the ruled input.

- **THE "FOUR PURGE SITES" LIST IS ALREADY INCOMPLETE (reach-attack survivor, doc §7).**
  `SurrealStore.delete_by_tier` is a FIFTH site — it purges chunks by tier but not entity rows; the
  mission's own words ("rides replace_file/**delete-by-tier** semantics") require it purge entities too.
  A hardcoded four-site pin silently exempts it. → the purge-coverage invariant must be DERIVED (enumerate
  every slice-removal call site; RED when the derived set grows but observed doesn't), never a hand-list
  (CLAUDE.md INSTRUMENT 0 / #344/#345).

- **SPLIT RECOMMENDATION: SPLIT 47(design ~0.15) / 47a(build ~0.30–0.35).** 7–8 production files, a novel
  two-phase ENFORCED edge lifecycle (property-to-invent, not a mechanical clone), a from-scratch
  fake-domain store with a dirty-store migration pin, ~10 load-bearing pins on spike-surreal. Total
  ~0.42–0.47 ≫ 0.25 → split. Doc §8.

## Self-attack residuals (for the contract-adversary; full list doc §9)
R1 phase-1↔phase-2 read window (named bound; marker deferred to 52a/52b) · R2 watcher fork (A-full rec) ·
R3 `Extension.name` charset (fail-loud via compose, but boot-crash for two adversarial names — recommend
charset constraint) · R4 file_text for claimed files (recommend write) · R5 claim exclusivity (≤1 per
file, loud error) · R6 the ONE-IMPLEMENTATION mutation must reach the ENTITY path, not only chunk/graph.

## lore-first / fallback disclosure (dogfood protocol)
lore-first throughout (lore_get_symbol / lore_read / lore_search grounded every symbol). TWO grep
fallbacks, disclosed: (1) the `write_stack_readied` region — semantic search would not land it, so
`grep -n "readied" server.py` + a direct Read (a construction-code textual seam, not a symbol);
(2) the fragment-prefix constants + the four/five purge sites — a cross-cutting multi-file textual sweep
(`grep FRAGMENT_PARAM_PREFIX` / `purge_file_fragment|delete_by_tier`). Both are the sanctioned
non-symbol / cross-cutting grep cases (CLAUDE.md dogfood protocol §3). No lore weakness worth a finding —
the misses were mine (line numbers in the ruled input were stale, as warned).
