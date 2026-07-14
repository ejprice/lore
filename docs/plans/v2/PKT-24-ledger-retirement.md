# PKT-24 — SQLite ledger retirement (singular-store ruling, 2026-07-11)
size ~0.20 wu · wave M, FIRST (re-waved 2026-07-14; MUST land before PKT-12 finalizes and PKT-13 ships) · depends: none
law: DESIGN-LAW §14 (the ruling), §9 (memory contract), §7 (non-destructive until retire) · DEPLOY: yes

## Mission
Operator ruling (2026-07-11): **SurrealDB is the singular durable store for lore data.**
Retire the SQLite write-through memory ledger in ALL modes — the v1.0 "one ACID store"
claim becomes literally true. Memories join the durability class tasks/findings/traces
already live in: the store plus store-level backups.

## Scope IN
- **Parity receipt FIRST**: one final backfill/compare sweep — every ledger row present
  in the store (count parity + spot recalls) before anything is removed. No receipt,
  no retirement.
- **Delete the writer**: the write-through side-write and the boot backfill path in the
  memory backend. Memory writes are store-only and FAIL LOUD on store failure — no
  silent durability fallback. Lifecycle tests updated (degradation: store down during
  remember → loud error, clean recovery after).
- **Preserve the reader for migration only**: PKT-12's N3 driver imports v0.3
  `<slug>.memory.db` ledgers — move/keep a standalone ledger READER there. v2 never
  writes ledger files again.
- **Freeze, don't delete**: existing `.memory.db` files stay in place (rename
  `.retired` acceptable) until post-soak operator confirmation (INDEX pool item 3
  rides the same soak).
- **Resilient-open honesty**: the corrupt-dir move-aside path can no longer ledger-
  restore memories. It must NOT recreate-and-serve-healthy while memories sit in the
  moved-aside dir — boot surfaces an explicit memories-unrecovered status naming the
  moved-aside path; recovery = store backup restore, documented.
- **Backup posture, per mode**: document REQUIRED store-level backups — single-node:
  state-dir ZFS snapshot / `surreal export`; split: PVC snapshots / managed backups.
  Provide the mechanism: a lore-deploy `backup`/`export` verb (coordinate the seam with
  PKT-11 — build it here, PKT-11 inherits it).
- **Docs truth**: README/positioning may now claim the singular store outright
  (coordinates with PKT-03's positioning pass).

## Scope OUT
- Deleting v0.3 ledger files (migration source; post-soak, operator-confirmed).
- Object-store journal — dead option, ruled out with the fork.

## Entry check
- Parity tooling: a public memory count/health read (overlaps PKT-12's N2 — if N2
  isn't built yet, build the minimal count here and PKT-12 reuses it).
- `lore_recall` spot-check list drawn from the live instance before the sweep.

## Exit
Full gates + cold audit; deploy BOTH; smoke: remember→recall round-trip with NO SQLite
file touched; boot with no ledger present is clean; a simulated store-down remember
fails loud; parity receipt + backup-verb receipt committed; INDEX row + Log.
