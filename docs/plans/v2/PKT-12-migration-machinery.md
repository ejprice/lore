# PKT-12 — Fleet-migration machinery (Shape D, ledger #11)
size ~0.30 wu · wave E · depends: **operator answers to §8 Q1–Q4** (INDEX pool item 2)
law: DESIGN-LAW §7 (I1–I4, endpoint-swap-last) · spec: docs/design/2026-07-04-migration-concurrency.md §7 (:275-313) + Shape D runbook (:165-271)

## Mission
Build the v0.3→v2 migration machinery per the ruled Shape D design. The only
non-derivable data is the memory store; its durable source of truth is the
`<slug>.memory.db` write-through ledger. PKT-13 executes; this packet only builds.

## Scope IN (the §7 numbered machinery)
- **N1 — RESHAPED by the singular-store ruling (2026-07-11, DESIGN-LAW §14):** v2 boot
  replay no longer exists (PKT-24 retires it) — build the skip-and-log replay + the
  pre-flight embed dry-run INTO the N3 driver's ledger import instead. Q1's substance
  (never fail-closed on one bad row; dry-run embeds before the freeze window) carries
  over; only the venue changed.
- **N2** — public `count()`/health read on LocalMemoryBackend (parity receipts need it).
- **N3** — `scripts/lore_migrate.py` driver: both stores against the shared ledger;
  final `backfill_ledger_from_store` sweep → count-parity receipt → replay into the v2
  `memory` table via `restore_from_ledger` (uuid5 idempotent; legacy rows default
  kind=fact, trust=experiential, valid_until=null) → verify (parity + spot recalls).
- **N6** — the `lore.yaml` additive upgrader (surreal block per Q2: namespace/database
  only, shared server; preserve every project-specific setting; back up the prior file
  beside it) + the `start` refuse-and-point guard (never silently start v2 over an
  unmigrated v0.3 state dir: "run migrate first").
- The `lore-deploy migrate` verb driving Shape D phases A→C + receipts (operator owns
  GO/NO-GO, retire, session reload).

## Recorded non-scope (do not re-raise)
- **N4 explicitly NOT built** (uuid5 id-diffing already makes catch-up incremental).
- **N5** v0.3 read-only flag — optional and NOT recommended (Q3 default: accept the
  seconds-long Phase-B freeze).

## Entry check
§8 Q1–Q4 answers recorded in the spec doc's ruling section; PKT-11's skill rework
landed (the migrate verb hangs off it).

## Exit
Full gates + cold audit; dry-run the whole Shape D ladder against a THROWAWAY v0.3
fixture (never DI) with parity receipts; PKT-13 unblocked; INDEX row + Log.
