# PKT-27 — Odoo-scale ingest + resumability certification (gap 6, operator-directed 2026-07-11)
size ~0.30 wu · wave F (parallel-safe; operator may pull earlier — it only reads the target corpus) · depends: PKT-05 recommended (detection routes Odoo's file zoo); v1.0 core
law: DESIGN-LAW §6 (measure, never assume), §12 · driver: **lore's declared target — replace the odoo-code MCP** · DEPLOY: receipts + red-first fixes

## Mission
Every resumability/scale claim lore makes has been exercised at ≤600 files; the target
corpus is Odoo 15 core+Enterprise+custom+OCA (~20k+ files, ~53k chunks). Certify — or
fix red-first — the ingestion, boot, and serving story at that scale, BEFORE the Odoo
onboarding packet exists. External-review gap 6 ("repository-state resumability, not
workflow resumability") is answered with receipts, not positioning.

## Scope IN (each item = a measured receipt)
- **Cold ingest, full Odoo tree**: wall-clock, RSS, store size, rows/s per stage
  (chunk / graph-derive / embed / snapshot). Embedder per policy: cloud voyage-4-large
  via the P5 **Batch path** — job-id re-attach exercised for real, plus its failure
  classes (429, timeout, orphaned job → re-attach on restart).
  **Operator note (2026-07-11): do NOT inherit the local-TEI bottleneck profile —
  voyage-4-large cloud batch/concurrency may be FASTER than self-hosted nano.**
  Measure batch and concurrent-request throughput before naming the bottleneck; if
  embedding isn't it, the certification's attention shifts to derivation and
  store-write throughput.
- **Kill-and-resume drills per stage**: kill -9 mid-chunking, mid-derivation,
  mid-embed, mid-enrich; receipt = manifest-state audit proving only in-flight files
  redo work. Repeat once with the store connection cut instead of the process.
- **Warm-boot cost at scale**: boot with zero staleness must be near-constant, not
  tree-linear — if any eager path (graph re-derivation, fingerprint sweep, PageRank)
  scales with corpus size rather than delta, that is a DEFECT fixed in this packet.
- **HNSW warm + degraded honesty**: measure index build time at 53k×dim; verify the
  BM25-only degraded contract serves honestly for the whole warm window.
- **Serving latency at scale**: map (PageRank over the full graph), impact depth 1–4,
  search p50/p95 — against the interactive envelope; Matryoshka dim reduction is the
  pre-approved lever if RSS/latency miss.
- **Parity matrix vs odoo-code MCP** (operator strikes it): code-side tools lore must
  cover vs the live-DB introspection surface (fields_get / search_read / call_kw)
  that stays with odoo-dev BY DESIGN — the replacement boundary written down.
- **MRO + ORM metadata assessment (operator-flagged 2026-07-11):** measure what plain
  astroid gets WRONG on the real tree — Python MRO / super()-chain dispatch (astroid
  can resolve; do we capture it?), and Odoo's string-keyed framework inheritance:
  `_name`/`_inherit`/`_inherits` effective-model merges across modules, field-string
  references (`compute=`, `depends`, `related="a.b"`). Same defect class as the XML-id
  gap: string/framework-mediated references invisible to the current graph — these
  decide whether impact/dead-code verdicts on Odoo are trustworthy. Deliverable:
  concrete wrong-verdict examples + a graph-requirements section that DEFINES the
  onboarding packet's scope (pool item 19). Assess here; build there.
- **Docs line**: resumability described as what the drills prove (manifest-grained,
  batch-job re-attach) — never as workflow/LangGraph checkpointing.

## Scope OUT (sequenced after certification — the Odoo onboarding packet)
- The XML reference extractor (framework-mediated calls; dead-code truth on Odoo),
  manifest/csv chunker extensions, tier layout (odoo15-core static / custom live),
  actual cutover from odoo-code. Pool item 19 schedules it.

## Entry check
Detection layer state (what routes Odoo's .xml/.po/.csv/manifest zoo today); Voyage
key + Batch quota; a host with disk/RAM headroom for the drill store (NEVER the
production instances — dedicated throwaway container per the drill-store rule).

## Exit
Certification receipts committed (a docs/design record with every number); defects
found → red-first fixes + findings; parity matrix operator-struck; INDEX row + Log.
