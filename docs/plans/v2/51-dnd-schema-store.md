# 51 — dnd schema slice + domain store (wave-D mint, 2026-08-02)
size ~0.25 wu · wave D · depends: 50 ruled · DEPLOY: no (54 lights it)
FIRST READ (store law): docs/reference/surrealdb-31-capabilities.md · DDL frame: 50's ruled doc, extending the archived graph report §5 (receipts/2026-08-01-dnd-rag-scoping/REPORT-graph-scout-1.md)

## Mission
The dnd extension's store: schema slice for the seven families' node/edge tables + a
domain store owner (`SpellStore`-family, ledger pattern: own connection, `_txn` driver —
`SurrealStore` deliberately has no arbitrary-query verb).

## Scope IN
- DDL per 50's frame: every relation `ENFORCED` + `UNIQUE(in,out)` + `source_book` scope
  column FROM BIRTH (ruled; the existing code graph's gap is a ledgered hazard, not a
  model). Scalars (level, ritual, school, CR, type) as indexed FIELDS — a traversal never
  uses a secondary index; array containment indexes use the `.*` element path (both
  PROBED, store reference §2/§4).
- Composite ids `[source_book, slug]` (D2: editions distinct by construction); never mint
  numeric-looking string ids (probed SDK trap, reference §7).
- Re-ingest = purge-by-scope + re-RELATE in ONE transaction via the packet-47 seam.
- **Lift the graph scout's probe scripts verbatim into `scripts/`** (deferred with this
  packet as its named decision point since the 2026-08-01 scoping session) — they are the
  schema's natural regression probes.

## Scope OUT
- Extractors (52-series). Tools (53). Instance config (54).

## Entry check
50 ruled. Store reference read. Probes target :18000 ONLY (never :18500).

## Exit
Full gates + adversary + cold audit. Three-legged idiom per table family (offline DDL pin ·
live round-trip · dirty-store migration pin with the legacy row under OLD DDL). Mutation
proof: drop the `ENFORCED` clause → the dangling-edge pin reddens (declared set first).
