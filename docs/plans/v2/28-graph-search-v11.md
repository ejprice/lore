# 28 — Graph/search v1.1 upgrades (formerly PKT-17)
size ~0.35 wu · wave F (parallel-safe) · depends: v1.0
law: DESIGN-LAW §2 (map semantics — LAW), §3 (pre-registered rules), §4 (graph invariants) · DEPLOY: yes

## Mission
The performance/depth items MASTER-PLAN §6 P9 batches, plus the graph findings routed
here. Measure-then-adopt discipline throughout — every candidate ships behind its
pre-registered rule or not at all.

## Scope IN
- **Materialized PageRank** rank column (on-demand per-scope stays the fallback) +
  **one-query graph-enriched search** (RRF+RELATE single query) + **materialized
  RELATE edge** evaluation — each adopted only if measured better on the standing bar.
- **Docstring as separate weighted BM25 field** (+ llm_summary weighting if packet 30 landed).
- **Markdown outbound-link extractor** → refers edges (shares the future Odoo-XML
  extractor seam).
- **Finding #70**: depth>1 channel honesty on impact rollups.
- **Finding #155** (slotted 2026-07-22): the LIVE `graph_surreal.tests_for` friction
  recorded only in `test_impact.py:812`'s docstring — adjudicate and fix or pin the bound
  here with the other graph candidates.
- **Finding #3** (attribute-access reference granularity — engine-level astroid
  attribute edges): OPERATOR SCOPE GRANT REQUIRED before building; present cost first.
- **Relative-score fusion** (Weaviate relativeScoreFusion / Qdrant DBSF analogue) —
  evaluate against the floor machinery under a pre-registered rule (ledgered follow-up
  from the weak-match validation); source-concentration + pool-size signals likewise.
- **Personalized PageRank seeding (operator-directed 2026-07-11 — "borrow this")**:
  graph centrality seeded from the query's hit set/focus symbols (the Spectron
  per-query-seeding idea, code-graph edition). Plus a keyword-bridge evaluation for
  prose-heavy corpora. Both under pre-registered adoption rules.
  **DISCLOSURE CONSTRAINT (operator-ruled 2026-07-11, DESIGN-LAW §3): no covert
  re-ranking.** Two compliant shapes to evaluate: (1) similarity order untouched +
  a labeled separate lane ("graph-central near your query: …") — preferred prior;
  (2) re-rank only with per-hit `graph-boosted` disclosure and raw cosine still
  rendered. Adoption gate = transcript-graded client metrics on the 35-pair bar,
  NOT raw hit@k — hit-rate cannot see the false-confidence failure this guards.
- **detail_level reshape** (`detail: refs|signatures|source`) — ONLY if the operator
  places it here (INDEX pool item 6).

## Scope OUT
- Any map/impact SEMANTIC change (DESIGN-LAW §2 — fresh consult required).
- Reranker adoption without an A/B accuracy win (config seam exists; default off).

## Entry check
`lore_findings` → #70, #3 states; re-run the 35-pair bar BEFORE (the packet's own
baseline) — every adoption here must hold or improve it.

## Exit
Full gates + cold audit; deploy BOTH; the 35-pair bar re-run AFTER with receipts
(client metrics hold or improve); findings resolved/granted/deferred with notes;
INDEX row + Log.
