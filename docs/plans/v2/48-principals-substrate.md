# 48 — Principals substrate: `build_store(config)` extraction + the `principal` table (wave-D mint, 2026-08-02)
size 0.20–0.25 wu · wave D · depends: 45 (can run ∥ 46/47) · DEPLOY: no (49/39 serve it)
FIRST READ (store law): docs/reference/surrealdb-31-capabilities.md · spec: docs/design/2026-08-01-multi-user-lore-proposal.md §Part 1A (the whole design — this file only points)

## Mission
The identity substrate for keys (49) and packet 39's auth. Two halves, in order:
1. **Extract `build_store(config)` FIRST** — the store-construction recipe is copy-pasted
   in three places today (spec names them); a fourth copy is the ONE IMPLEMENTATION
   violation this repo has the most receipts against. Extract, then use it at all sites.
   Prove sharing by MUTATION (every caller's pin reddens).
2. **The `principal` table** — named `principal`, NEVER `user` (SurrealQL collision +
   rename-sweep cost, spec §1A). Schema per the floor/lease slice recipe; fields, closed
   domains, and migration clauses per spec §1A (store-reference §1.1 binds: TABLE
   IF NOT EXISTS · FIELD OVERWRITE · INDEX IF NOT EXISTS; ALTER is a trap).

## Scope IN
- Ledger-actor strings (`created_by`, `actor`, `owner`) are NOT retro-fitted — `principal`
  is the HUMAN vocabulary; state this in the module docstring (spec §1A's standing-law
  clause).
- On-record Log override (2026-07-31): users-in-the-DB is R12's roster-file re-open
  trigger firing — multi-user proposal fork 2 (principal REPLACES the roster file) is the
  working premise; 39's contract re-cut consumes it.

## Scope OUT
- CLI + keys (49). Scoped memory (Part 3 — STRUCK for this track). Auth wiring (39).

## Entry check
45 landed. Store reference read. `lore_index(reconcile=True)` if the session edited.

## Exit
Full gates + adversary + cold audit. Three-legged store idiom (offline DDL pin · live
round-trip on :18000 · dirty-store migration pin — legacy row written under OLD DDL).
Mutation proof on the extraction (change the shared recipe → every consumer pin reddens).
