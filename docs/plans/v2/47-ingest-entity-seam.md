# 47 — The twelfth seam: extension ingest entity-fragment (DESIGN + build) (wave-D mint, 2026-08-02)
size ~0.15 design + build (split at kickoff if the design prices it over) · wave D · depends: 46 · DEPLOY: no
FIRST READ (store law): docs/reference/surrealdb-31-capabilities.md · spec: docs/design/2026-08-01-dnd-rules-rag-proposal.md §4-C item 3 + §2 (the gap row)
⚠ DESIGN PACKET under roster law: the central requirement is a property to INVENT — an Opus
author who ATTACKS ITS OWN DESIGN (or the Fable sidecar), operator rules the doc, adversary
before any builder. It never reaches a builder as "figure out the general form".

## Mission
The one seam the extension framework's eleven do not include: a per-tier,
extension-contributed ingest fragment — typed entity records + `RELATE` edges composed
into the SAME per-file `store.apply(fragments)` transaction as chunks, so entities and
chunks commit or roll back together, and purge-by-scope rides the existing
`replace_file`/`delete_by_tier` semantics.

## Design questions the doc must settle (then contract → adversary → build → cold audit)
- Fragment shape: multi-node-type + cross-entity edges (the seven ruled families need
  monster/feature/subclass/condition/item nodes — see rulings doc §2), not a spell-only
  shape.
- Transactionality: one file's chunks + entities = one transaction; failure teaches.
- Re-ingest: purge-by-scope + re-RELATE in ONE transaction (the graph scout PROBED both
  corruption directions — DELETE+CREATE loses edges, UPDATE keeps stale ones; archived
  2026-08-01-dnd-rag-scoping graph report §6).
- Cross-FILE edges (a spell in one file, its class list in another): resolution timing —
  the design's hardest question; name it explicitly.
- The store driver boundary: fragments execute via `_txn` (`execute_transaction`), never
  a private query path (ONE IMPLEMENTATION).

## Scope OUT
- The dnd extractor itself (52-series), the dnd schema (51), extraction grammars (50).

## Entry check
46 landed. Store reference read (its DDL/migration/RELATE law binds the design).

## Exit
Ruled design doc + built seam; full gates; adversary + cold audit; mutation proof on the
transactionality pin (entity write fails ⇒ chunk write rolled back — constructed, with a
positive control).
