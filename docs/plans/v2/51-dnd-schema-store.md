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
- **Closed-vocab MULTI-TAG fields are `array<string>` indexed on the ELEMENT PATH
  `FIELDS <f>.*` — habitat, creature_subtype** (2026-08-24 operator ruling: habitat is a
  FIELD, reversing rulings-doc F3's edge model). Member queries use `<f> CONTAINSANY $set`
  (or a same-field `INSIDE`-OR — both `UnionIndexScan`; the `IN`-in-`OR` TableScan trap does
  NOT extend to array-containment disjuncts). Member-exact by construction ('Forest' ∌ the
  element 'Foresthome') — NEVER a joined string (substring false-match). ⚠ The emitter MUST
  omit the clause when `$set` is empty (`CONTAINSANY []` TableScans). The wildcard `Any`
  habitat is a reserved SENTINEL vocab member, expanded at read (`CONTAINSANY [<terrain>,
  'Any']`). All PROBED 2026-08-24 on 3.2.4 — `scripts/probe_dnd_multitag_schema.py`, store
  reference §2.
- **Plane taxonomy** (un-deferred 2026-08-24 operator ruling, reversing rulings-doc ruling 5):
  a small SEPARATE reference graph — `plane` node + `is_part_of TYPE RELATION IN plane OUT
  plane ENFORCED` with `UNIQUE(in,out)` + its OWN `out` index. Two-step read: expand the query
  tag against the ontology (up `WHERE in=$specific` leading col · down `WHERE out=$group` own
  index — both IndexScan) then indexed `planes CONTAINSANY $expanded`; NEVER a
  traversal-in-`FROM` (reference §6.6 item 13). The transmute producer ships flat
  source-truthful plane tags + the containment mapping as reference data; upward
  denormalization (specific→groupings) is a safe optional shortcut, downward is not truthfully
  materializable. Deeper-than-two-level taxonomies: native `@.{1..N+collect}` recursion (nested
  `[[..]]` shape, `TIMEOUT`, silent 256 truncation → serve an honest floor). PROBED (same probe).
- Composite ids `[source_book, slug]` (D2: editions distinct by construction); never mint
  numeric-looking string ids (probed SDK trap, reference §7).
- Re-ingest = purge-by-scope + re-RELATE in ONE transaction via the packet-47 seam.
- **Lift the graph scout's probe scripts verbatim into `scripts/`** (deferred with this
  packet as its named decision point since the 2026-08-01 scoping session) — they are the
  schema's natural regression probes. `scripts/probe_dnd_multitag_schema.py` (committed
  2026-08-24) already covers the multi-tag/taxonomy slice; pin its facts as a regression.

## Scope OUT
- Extractors (52-series). Tools (53). Instance config (54).

## Entry check
50 ruled. Store reference read. Probes target :18000 ONLY (never :18500).

## Exit
Full gates + adversary + cold audit. Three-legged idiom per table family (offline DDL pin ·
live round-trip · dirty-store migration pin with the legacy row under OLD DDL). Mutation
proof: drop the `ENFORCED` clause → the dangling-edge pin reddens (declared set first).
