# RULING S1/S2: per-tier refusal through one shared predicate (operator, 2026-10-31)

Source: REPORT-contract-165.md §Inventory, spec-silent S1 and S2. Ruled by the operator at the approval prompt
(both recommended options taken).

## S1: refuse per tier, using ONE shared check
The launch refuses whenever ANY static tier the config declares would fail the server's boot guard on the dir
leg: its materialisation dir under the HOST snapshot root is absent, or present but empty. Today's root-level
check becomes one case of this.

- **The chokepoint:** the "is this tier materialised (dir present and non-empty)" decision moves into
  `loremaster.source.snapshot.SnapshotLayout`, the one module that already owns tier→dir layout.
  `Indexer._snapshot_materialized` delegates to it. `lore_deploy`'s launch precondition (the F1/R1 shared check)
  evaluates THAT predicate over the host `SNAPSHOT_ROOT`, for every static tier, through the loremaster venv, the
  same way `_read_config_field` already runs loremaster code from the host. Neither side keeps its own copy of the
  rule.
- **Refusal text:** it names each failing tier and its dir, plus the cold-index remedy
  (`python -m loremaster.index --config …`).
- **Pins (the rider; build them):**
  1. Per-tier refusal at both levels (`_launch_container` and `verb_start`, fresh and recreate paths, before
     teardown). Extend the R1 matrix with "root present, one tier dir absent" and "root present, one tier dir
     empty" cells.
  2. **Agreement by behaviour:** over one fixture set (absent, empty, non-empty, a file instead of a dir), the
     deploy precondition refuses a tier iff the server's `Indexer._snapshot_materialized` reads False for it. Both
     are driven from the same fixtures, never each from its own.
  3. The existing covering tests of `Indexer._snapshot_materialized` stay green (scope via `lore_impact`).
  4. The audit proves the sharing by MUTATION (change the predicate; both sides must change), as a run, not a
     standing test.
- **Still out (named bound, #166):** the version-stamp leg of the guard lives in the store and is not checked
  pre-launch. A tier whose stamp mismatches still re-acquires, and so still crashes boot.

## S2: a regular file at the snapshot root is refused
`is_dir`-based. S1 covers it automatically: no tier dir can exist under a file. Pin it once, in the R1 matrix's
file cell, which now asserts REFUSE rather than mere agreement.
