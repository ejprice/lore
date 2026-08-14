# REPORT — fable-precedence-1 (edition-precedence proposal + packet-47 rulings fold)

brief-base v14 read
brief project v7 read

## Summary block
- **state:** done — two deliverables (rulings folded into the 47 design doc; the precedence proposal
  drafted). Standing by.
- **deliverables:**
  1. `docs/design/2026-08-14-packet47-ingest-entity-seam-design.md` — the two operator rulings folded
     (Status line + §Q2.2 Reading B RATIFIED + §Q3.2 rewritten FULL-SWEEP-ONLY + §Q6 cross-book fixture
     reframed + §8/§9 + the seam docstring). Swept clean of contradicting text.
  2. `docs/design/2026-08-14-edition-precedence-mechanism.md` — the ~2-page decision-shaped proposal.
- **deviations:** none. Writable set = the two docs. No live probe. Store/corpus facts CITED.
- **Packages considered:** none — no external-package-eligible mechanism; the proposal specifies a
  lore-side config map + a resolver accessor (domain-internal policy), not a library candidate.
- **Reuse ledger:** no new code symbols (design only). The proposal's load-bearing DRY constraint is
  that the resolver AND the ranker read ONE `book_precedence` accessor (ONE IMPLEMENTATION, prove-by-
  mutation) — a reuse REQUIREMENT, not a new symbol.
- **Graded:** grounded at HEAD `5770439` · HEAD-at-report `5770439` · SAME.
- **decisions-needed (operator):** Fork A (storage: lore-side config [rec] vs node-baked field) · Fork B
  (granularity: book-level total order [rec] vs edition-coarse) · Fork C (ties: none-by-construction
  [rec] vs secondary tiebreak). Combined rec: **A1+B1+C1**.
- **receipt pointers:** precedence doc §0 (load-bearing dep) · §1 (recommendation) · §2 (resolve steps)
  · §3 (two-point/one-source enforcement) · §4 (build placement table) · §5 (the forks) · 47 doc §Q3.2
  (full-sweep-only) · §Q2.2 (Reading B ratified).

---

## Part 1 — the two rulings folded into the 47 design doc

1. **SPLIT 47/47a CONFIRMED + Reading B RATIFIED** → Status line + §Q2.2 marked RULED; §8 split re-stated.
2. **Phase-2 edge resolution is FULL-SWEEP-ONLY; D&D uses NO incremental file watcher** → §Q3.2 fully
   rewritten as a **PINNED NON-FEATURE**: the watcher purges NODES on delete (edges cascade) but does
   NOT incrementally re-resolve edges; edges re-resolve only at full-sweep completion. This **dissolves
   adversary F1 by construction** (every full re-crawl re-resolves ALL edges against ALL current nodes —
   no cross-book edge is ever orphaned), and it is ALSO the "newer wins" enforcement mechanism. The
   `resolve_edges` seam retains `changed_scopes` (reserved for the non-feature; framework passes only
   `None`; a pin asserts the sole call site uses `None`). §Q6 cross-book fixture reframed to pin
   "full-sweep re-resolution correctly re-points a cross-book edge at a newly-added newer-edition node"
   + the pinned non-feature. §8 item 5, §9 residual R2 (now CLOSED), and the seam docstring updated.
   Re-open trigger recorded: a future extension wants live per-file edge resolution.

Swept the doc: no surviving "A-full / best-effort / incremental per-scope" text contradicts the ruling.

## Part 2 — the edition-precedence proposal (recommendation + forks)

**Recommendation (A1+B1+C1): a LORE-SIDE `book_precedence` config/table mapping each `source_book →
integer rank` (a book-level TOTAL ORDER, no ties).** The node carries only `source_book` (provenance —
already present as half the composite id `[source_book, slug]`, wave-d §7); LORE carries the rank
(policy). `resolve(kind, slug)` canonicalizes the slug via the 59-row rename-alias FIRST, gathers all
nodes for the canonical slug (F6 slug-leading index), orders by `book_precedence[source_book]`, returns
the newest — reference's own edition ignored (wave-d §7). The 2014-gap → dangling tombstone (named
bound). Enforced at TWO points reading ONE source: full-sweep edge re-resolution (materializes "newer
wins" in the graph) + retrieval ranking (all versions newest-first, each book named — graph-scout §6.4).

**Why this shape:**
- Book-level total order **subsumes** "2024>2014" and also handles two-2024-books / errata / reprints /
  Core-vs-supplement, matching the data's natural `source_book` key.
- Lore-side config makes precedence **operator-re-assignable without a re-scrape** (policy belongs in
  config per rulings §7's derive-from-the-2024-rules rider), avoids a per-node second source of truth,
  and — the scope win — means **packet 55 (scraper) needs NO precedence change**.

**Hard flags (per the brief):**
- **⚠ LOAD-BEARING DEPENDENCY:** the mechanism keys on `source_book`, which the machine tier MUST emit
  per record. wave-d §7 says it does (composite id); I could NOT confirm the exact transmute record
  fields — `transmute/records.py` lives in the SCRAPER repo (`dndlorescraper`), unindexed here. 52a
  ingest must ASSERT `source_book` present per record (loud reject if missing). Whether a distinct
  `edition` field is also emitted is unconfirmed — irrelevant under A1 (source_book suffices), required
  under A2.
- **⚠ PACKET 55 (scraper, possibly mid-build ∥-safe):** my recommendation (A1 lore-side config) forces
  **NO change to 55**. The alternative (A2 node-baked edition) WOULD force 55 to emit an `edition` field
  + 51 to store it + a re-scrape to re-rank — a change to a sequenced, possibly-mid-build packet. This
  makes A1 the scraper-safe choice, and is a decision driver, not just a preference.
- **`class:druid` edition-scoping** (graph-scout §6.4, explicitly surfaced-for-operator): under B1 the
  2014 and 2024 druid are distinct source_book rows under one canonical slug; resolve returns the
  highest-ranked, search returns both. If the operator wants them MERGED into one entity, that's a
  different modelling choice (a merge, not a precedence pick) — flagged, not assumed.

**Scope boundary (packet 47 stays generic):** 47 exposes only the resolver hook + the slug-leading
index, NO edition logic; `book_precedence` + `resolve` live in the dnd extension (51/52b); ranking +
the downrank VALUES are 50/53 (50's rider derives values from the 2024 rules text). Full table in the
proposal §4.

## lore-first / fallback disclosure
lore-first for symbols; the corpus/ruling facts were read from the ruled docs directly (rulings §7,
wave-d §7, graph-scout §6.4). One grep fallback (design-doc consistency sweep — a textual seam, dogfood
§3). The transmute records module is genuinely out of reach (different repo, unindexed) — flagged as the
load-bearing dependency rather than guessed. No lore friction to file.
