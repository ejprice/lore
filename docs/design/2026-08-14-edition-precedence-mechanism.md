# Edition-precedence mechanism — how "newer wins" is DETERMINED and ENFORCED

**Status: RULED (operator, 2026-08-14).** Author: `fable-design-47`. The operator chose to rule this
mechanism NOW rather than defer the policy to packet 50, and ratified the combined recommendation in
full — **A1 + B1 + C1 + distinct-nodes** (§5). Scope: the MECHANISM (key, representation, resolve-order,
enforcement, build-placement) — NOT the final downrank *values*, which rulings §7's rider assigns to
packet 50 ("READ the 2024 rules for how they say to evaluate older material and derive the policy from
that text").

**Consuming packets:** 47 (generic seam hook + the F6 slug-leading index — NO edition logic) · 51
(schema — NO new field under A1) · 52b (the resolver) · 50/53 (retrieval ranking + the downrank VALUES)
· 55 (scraper — NO change).

**Grounded in (read first, cited never re-transcribed):** rulings §7 (`2026-08-02-dnd-graph-scope-rulings.md`
— "2024 supersedes 2014… downrank 5.0"; the read-the-2024-rules rider; the 2014-base-rules NAMED
BOUND) · wave-d §7 (`2026-08-03-wave-d-architecture.md` — the 52b resolver: prefer 5.5/Core → 59-row
2014→2024 rename-alias → 5.0 → dangling tombstone; the reference's own edition IGNORED; composite ids
`[source_book, slug]`) · graph-scout §6.4 (`…/2026-08-01-dnd-rag-scoping/REPORT-graph-scout-1.md` —
`UNIQUE(name)` REJECTS the 2nd book's Fireball; `UNIQUE(name, source_book)` admits both; TARGET-3 is
N-valued; **"`class:druid` is edition-scoped too… a design question, not a scout's: surfaced for the
operator"** — this proposal answers exactly that surfaced question).

---

## 0. ⚠ THE LOAD-BEARING DEPENDENCY (flag first — the mechanism can only key on a field the DATA carries)

Precedence must key on a per-record field the machine tier actually emits. **`source_book` IS carried**:
wave-d §7 (packet 51) makes it half the composite id `[source_book, slug]` and gives every relation a
`source_book` scope from birth; it is the record's provenance. **A distinct `edition` field ('5.0' /
'5.5') is REFERENCED by rulings §7 ("downrank `edition: '5.0'`") but NOT confirmed as an emitted
per-record field** — the transmute `records.py` module the 52a spec mirrors lives in the SCRAPER repo
(`dndlorescraper`), which is not indexed here, so I could not read its exact field set.

**Consequence for the fork below:** if precedence keys on `source_book` (my recommendation), the data
already carries it and **no scraper change is needed**. If it keys on a distinct `edition` field, the
transmute records MUST emit one — a change to packet 55, which may be mid-build (∥-safe). **52a's
ingest must CONFIRM `source_book` is present on every record** (a per-record assertion; a missing
`source_book` is a loud reject, never a silent default) — that confirmation is the precondition this
whole mechanism rests on.

---

## 1. THE RULED MECHANISM (one paragraph) — A1 + B1 + C1 + distinct-nodes (§5)

**Key precedence on `source_book` at BOOK granularity, via a LORE-SIDE `book_precedence` config/table
that maps each `source_book → integer rank` (a total order). The NODE carries only `source_book`
(provenance, already present); LORE carries the rank (policy). `resolve(kind, slug)` canonicalizes the
slug through the 59-row rename-alias FIRST, gathers all nodes for the canonical slug across books,
orders them by `book_precedence[source_book]`, and returns the highest — the reference's own edition
ignored (wave-d §7). The SAME `book_precedence` accessor is read by BOTH enforcement points — full-sweep
edge re-resolution (52b, materializing "newer wins" in the graph) and retrieval ranking (50/53,
newest-first, every book named) — so precedence is encoded ONCE (ONE IMPLEMENTATION).** Provenance lives
in the data; policy lives in operator-owned config; they join at resolve time.

**Why book-level total order over edition-coarse:** it *subsumes* "2024 > 2014" (assign every 2024 book
a higher rank than every 2014 book and the coarse rule falls out) while also expressing what coarse
cannot — two 2024 books (PHB'24 vs a later '24 splat), Core-vs-supplement, errata, reprints — and it
matches the data's natural key (`source_book`, which graph-scout §6.4 shows is already the multi-book
uniqueness key and the "one row per book" render key).

**Why lore-side config over a node-baked field:** precedence is a POLICY (rulings §7 hands the operator
the authority to derive it from the 2024 rules), and policy in config is **operator-re-assignable
without a re-scrape** — add a book, re-rank on errata, promote a reprint, all by editing a lore-side
map. A rank baked on every node is a second source of truth (DRY hazard) and forces a re-crawl to
change. Crucially, **the lore-side choice means packet 55 (scraper) needs NO precedence change** — it
already emits `source_book` as provenance — which is the safe choice for a possibly-mid-build packet.

---

## 2. HOW `resolve(kind, slug)` PICKS (the mechanism, step by step)

1. **Canonicalize the slug** through the 59-row 2014→2024 rename-alias table FIRST (wave-d §7), so
   `oldname@2014` and `newname@2024` are gathered as the SAME entity. (The alias table is itself a
   machine-tier record family — wave-d §7.)
2. **Gather all candidate nodes** for the canonical slug across every book: `SELECT … WHERE slug =
   $canonical` (served by the F6 slug-LEADING index `UNIQUE(slug, source_book)` — 47 design §Q6; the
   leading-column rule, store ref §2). This legitimately returns N rows (graph-scout §6.4 — one per
   book).
3. **Order by `book_precedence[source_book]` descending; return the highest** (newest). The
   **reference's own edition is IGNORED** (wave-d §7) — a 5.0 link resolves to the 5.5 row when one
   exists, which is what makes wrong-edition targeting unrepresentable rather than merely caught.
4. **TIE handling:** a total order has **no ties by construction** — the `book_precedence` map is a
   BIJECTION `book → rank`, validated at load (two books sharing a rank is a **loud config error**, not
   a silent pick). This is the recommended path (fork B1/C1). *(If the operator picks edition-coarse —
   fork B2 — same-edition collisions need a documented deterministic secondary tiebreak, e.g.
   Core > supplement then lexical book id; a total order avoids the extra rule.)*
5. **The 2014-GAP interaction (the NAMED BOUND, rulings §7):** if NO version of the slug exists in any
   available book (the corpus has no 2014 PHB/MM), `resolve` returns a **dangling tombstone with the
   href preserved** (wave-d §7) — rendered as a named bound on 2014-mechanic queries, NEVER silently
   dropped. The tombstone is a first-class result, not an error.

---

## 3. ENFORCEMENT — TWO points, ONE precedence source (ONE IMPLEMENTATION)

Precedence is enforced at exactly two places, and they MUST read the same `book_precedence` accessor —
encoding it twice is the #102/#120 "routing ≠ sharing" defect waiting to happen.

1. **Full-sweep edge re-resolution (47 seam → 52b resolver).** Every full re-crawl re-resolves ALL
   edges against ALL current nodes (47 design §Q3.2, RULED full-sweep-only). Each edge is re-pointed at
   `resolve(kind, slug)` = the newest node. **This is where "newer wins" is MATERIALIZED in the graph:**
   after a crawl that adds a newer book, a cross-edition edge points at the new node, and the stale
   target is no longer referenced. It is not a separate supersession pass — it is what full-sweep
   re-resolution DOES.
2. **Retrieval ranking (packets 50/53).** A search for a slug returns ALL versions (N rows — graph-scout
   §6.4), ordered newest-first by the same precedence, **each book named** (trust doctrine — never "the"
   Fireball over an N-row result, graph-scout §6.4 / CLAUDE.md). Packet 50's read-the-2024-rules rider
   derives the concrete downrank policy (rulings §7) — but it feeds the SAME `book_precedence` source
   this proposal defines; the rider sets the VALUES, this sets the MECHANISM.

**ONE IMPLEMENTATION pin:** the resolver and the ranker call the SAME `book_precedence` accessor. Prove
by MUTATION — change one book's rank and BOTH the resolved edge target AND the search order must change;
if only one moves, precedence was encoded twice.

---

## 4. WHERE EACH PIECE IS BUILT (scope boundary — packet 47 stays generic)

| packet | builds | edition logic? |
|---|---|---|
| **47** (this seam) | exposes the phase-2 resolver HOOK (`resolve_edges` calls the extension's `resolve`) + the F6 slug-LEADING index. | **NONE** — a generic framework seam; `book_precedence` + `resolve` live in the dnd extension, never lore core. |
| **51** (schema) | nodes carry `source_book` (already, in the composite id). | Under the recommendation (lore-side config): **NO new field.** *(Under node-baked edition — fork A2: adds an `edition`/`rank` field.)* |
| **52b** (resolver) | `resolve(kind, slug)`: rename-alias canonicalize → `book_precedence` order → newest / dangling tombstone. Reads the `book_precedence` map. | **owns the resolve mechanism.** |
| **50 / 53** (tools) | retrieval ranking: all versions newest-first, book-named; reads the SAME `book_precedence`. 50's rider derives the downrank VALUES from the 2024 rules text. | **owns the ranking + the policy values.** |
| **55** (scraper) | emits `source_book` per record (provenance — already does). | Under the recommendation: **NO precedence change.** *(Under fork A2: MUST emit `edition` — a change to a possibly-mid-build packet.)* |

**Scope guarantee:** packet 47 carries no edition logic; it only routes `resolve_edges` to the
extension's resolver and provides the slug-leading index. The precedence mechanism is entirely 51/52b/
50/53 (dnd extension) + a lore-side config map. This keeps 47 a generic seam, as ruled.

---

## 5. THE RULING (operator, 2026-08-14 — A1 + B1 + C1 + distinct-nodes)

The operator ratified the combined recommendation in full. Each fork's resolution is now RULED
mechanism, not a choice:

- **A1 — RULED: precedence lives in a LORE-SIDE `book_precedence` config/table** (`source_book → rank`),
  read by the resolver AND the ranker. **NOT a node-baked field.** Operator-re-assignable without a
  re-scrape; policy stays out of scraped data; **packet 55 (scraper) needs NO change**; one source of
  truth. *(Rejected A2 — an `edition`/`rank` field on every node — for baking policy into data and
  forcing a 55 emit + 51 store + a re-scrape to re-rank.)*
- **B1 — RULED: book-level TOTAL ORDER** — each `source_book` gets a UNIQUE integer rank. Subsumes
  "2024 > 2014" (all 2024 books rank above all 2014 books); also expresses two-2024-books /
  Core-vs-supplement / errata / reprints; matches the data's natural `source_book` key. *(Rejected B2 —
  edition-level coarse — as unable to express intra-edition precedence.)*
- **C1 — RULED: NO ties by construction.** The `book_precedence` map is a BIJECTION `book → rank`,
  validated at load; two books sharing a rank is a **loud load-time config error**, never a silent pick.
  *(C2's secondary tiebreak is unneeded — a total order has no ties.)*
- **Same-name model — RULED: DISTINCT nodes per `(source_book, slug)`.** The 2014 druid and the 2024
  druid are SEPARATE nodes under one canonical slug — **NOT merged into one entity.** `resolve(kind,
  slug)` returns the **highest-ranked** node (newest wins); a search for the slug returns **ALL versions
  newest-first, each book named** (trust doctrine — never "the" X over an N-row result, graph-scout
  §6.4). This RULES the graph-scout §6.4 "`class:druid` is edition-scoped" question: **distinct, not
  merged.**

The ruled mechanism, in one line: *distinct nodes per book under a canonical slug; a lore-side total
order over books picks the newest at resolve time; every full re-crawl re-materializes "newest" into the
graph edges; search surfaces all versions newest-first, each book named — the resolver and the ranker
reading the ONE `book_precedence` source.*

---

## 6. Residual flags for the operator / packet 50
- **The downrank VALUES are packet 50's** (the read-the-2024-rules rider, rulings §7) — this proposal
  fixes the mechanism and the accessor, not the numbers. 50 populates `book_precedence` from the 2024
  rules text.
- **CONFIRM `source_book` on every machine-tier record at 52a ingest** (§0) — the mechanism's
  precondition; a missing `source_book` is a loud reject.
- **The 2014-base-rules NAMED BOUND** (rulings §7) rides through unchanged: a slug with no version in
  any available book resolves to a dangling tombstone (href preserved), rendered as the bound.
- **`class:druid` edition-scoping** (graph-scout §6.4) — **RULED: DISTINCT, not merged** (§5). The 2014
  and 2024 druid are separate `(source_book, slug)` nodes under one canonical slug; `resolve` returns
  the highest-ranked, search returns both newest-first, each book named. The merge alternative was
  considered and rejected — it is a different modelling choice, not a precedence pick.
