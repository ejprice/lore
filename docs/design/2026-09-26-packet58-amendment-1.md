# Packet 58 — ruling amendment 1 (sidecar-64, 2026-09-26): FORK-A (a terminal predecessor) and FORK-C ("strand impossible" under concurrency)

Rules `REPORT-contract-58.md` §FORKS (FORK-A, FORK-C; the author proceeds on its picks meanwhile).
Amends `docs/design/2026-09-26-packet58-kickoff-rulings.md` (`c8d3241`) §2, §6, §7. Facts: the kickoff's
symbol reads (`_claim_fragment`'s `$clm_resolved` = blockers in a TERMINAL status; `supersede_task` has
no status guard on X; `_backfill_blocks_edges` runs at EVERY boot, idempotent against the store's edge
set, recording what it skips; `direct_dependents` = `WHERE blocked_by CONTAINS $id` over an UN-INDEXED
array column; `_render_claim_result`'s R10(iii) branch names a superseded blocker and teaches *"block on
the successor instead"*), plus store-ref §2 (an array column is containment-indexable ONLY via the
element path `<field>.*`; measured `CONTAINS`/`CONTAINSANY` IndexScan on it) and §5 (hot-row law).
Neither fork is a MAJOR scope change: A is the mission's letter; C adds one guard statement and one
boot-time heal in the backfill's own shape. Both are FYI to the operator, not forks.

## FORK-A — RULING: A1, re-anchor ∀ dependents whatever X's status; the render NAMES the re-blocking

- **Ruling.** Superseding a `done`/`wontfix` X re-anchors its dependents to the OPEN successor X' —
  one class of rows, one statement shape, no status branch (F-2's reasoning: a second class of
  dependents is a second truth). The domain agrees: a supersede of a terminal X says *"that completion
  was wrong; the work continues in X'"* (it is today's ONLY reopen path — 57's #357 `done→in_progress`
  edge is still illegal), and a dependent that was unblocked by a WRONG completion SHOULD wait for the
  real one. A2 (refuse, or skip when terminal) either blocks the only reopen or manufactures the F-2
  drift; A2's status guard would also need a stamp-CAS conjunct racing a concurrent `→done`.
- **Rider — Leg 1, the consequence is SERVED, never silent:** `SupersedeResult` carries, beside
  `reanchored`, the subset `reblocked` — the re-anchored dependents that were CLAIMABLE before (status
  `open`, unowned, every OTHER blocker terminal) and are blocked by X' after; the render adds ONE line
  when it is non-empty: *"⚠ K of them were claimable and are now blocked on X' (it is open): …ids"*.
  Derived from the ledger's pre-write read of each dependent (the same read that feeds the rewrite),
  never re-computed post-write. A `claimed`/`in_progress` dependent keeps working (`blocked_by` gates
  CLAIMS only — stated in the docstring, pinned).
- **Pins:** the author's `TestSupersedeOfATerminalPredecessor` STANDS (A1); add: a `done` X with one
  `open` unowned Y (claimable before) and one `claimed` Z → after supersede, Y is unclaimable
  (`query blocked=False` excludes it; a claim LOSES naming X' as the unresolved blocker — the existing
  loss render), Z's status untouched, the render's K line names Y and not Z; N=0 reblocked → the line is
  absent (byte-identical to the plain re-anchor render).
- **Re-open trigger:** *"the first operator request to supersede a done task WITHOUT re-blocking its
  dependents"* → that is a different verb (an editorial `annotate` on tasks, #256's twin), not a
  status branch in this one.

## FORK-C — RULING: R1 is CLOSED in-transaction; R2 (write-skew) is a NAMED bound HEALED at boot, taught in-window, never a hand-rolled retry

- **R1 (constructible — a create of Y blocked_by X commits between supersede's dependents read and its
  transaction): CLOSE, as the author proposes.** The composed supersede ends with ONE closing guard:
  `IF (SELECT count() FROM task WHERE blocked_by CONTAINS $old GROUP ALL)[0].count > 0 { THROW
  '<straggler>' }` — under the transaction's snapshot a dependent that committed BEFORE the txn began
  is visible to the guard, so the txn rolls back whole (X un-stamped, no X', nothing rewired). The
  ledger classifies the rollback as a typed, TEACHING refusal (*"a task blocked on X was created while
  this supersede was being prepared — nothing changed; retry the supersede"*) — NEVER an automatic
  retry loop in the ledger (a hand-rolled retry is the #102 class; the store driver's `can be retried`
  marker is for engine conflicts and must not be forged). The derived cap absorbs the +1 statement.
  **Pin:** the R1 construction (inject the create between the pre-read and the apply, via the
  injected-handle idiom) → the refusal, `SELECT *` before == after on X, Y and the edge table; a second
  `supersede_task` call succeeds and re-anchors Y too (positive control).
- **R2 (write-skew: a create whose R10(ii) pre-check saw X live commits AFTER the supersede's
  transaction; two snapshot-isolated txns writing disjoint keys never conflict): a NAMED, PINNED
  bound — closed by an in-window teaching that already exists and a boot-time heal, not by a hot-row
  write on every create.** The two closing shapes and why each is rejected here: (i) the create txn
  TOUCHES each blocker row (`UPDATE X SET updated_at = updated_at WHERE superseded_by IS NONE` +
  THROW) so it conflicts with the supersede's stamp — correct by construction but it puts a guarded
  WRITE on the fleet's most common write path for every blocker (a hub X serialises every concurrent
  create that names it — store-ref §5's hot-row shape, bought for a race no one has observed); (ii)
  supersede re-scans at commit (R1's guard) — under snapshot isolation it cannot see the concurrent
  create either. So: the window is REAL and it is [the race → the next boot], and inside it the
  consumer is TOLD THE TRUTH — a claim on the stranded Y loses with R10(iii)'s render (*"X → X' — a
  SUPERSEDED blocker can never resolve; block on the successor"*): a true sentence naming the exact
  state, which is what the trust doctrine requires of a bound.
- **The heal (58 builds it — the backfill's own shape, ONE sibling, idempotent, recorded):**
  `_reanchor_stragglers()` runs beside `_backfill_blocks_edges` at every boot: `SELECT id, superseded_by
  FROM task WHERE superseded_by IS NOT NONE` (bounded by the superseded population; the `task_status`
  index does not serve it — see the index rider below) → for every straggler row whose `blocked_by`
  names a superseded X (`WHERE blocked_by CONTAINS $x`), the SAME re-anchor fragment the supersede uses
  (rewrite + edge DELETE/RELATE + a `dependency_reanchored` note with `actor: "boot-heal"` and the
  reason `"straggler"`) in ONE transaction, through the ONE shell; a chain X→X'→X'' re-anchors to the
  HEAD (follow `superseded_by` to its end — bounded, the chain is finite by the supersede CAS);
  `logger.info("task.backfill.stragglers_reanchored", extra={"count": N})`, and 0 → silent (the
  mirror's own idiom). ⚠ Legacy pre-58 strands on `:18500` are healed by the SAME statement at the 65
  boot — the fleet's existing stranded rows (the #356 population) become claimable at the cutover; the
  cutover smoke NAMES the count (kickoff §7 item 10's "legacy strands" render path stays for the
  in-window case only).
- **Pins:** seed a stranded Y RAW (a dependent naming a superseded X with successor X' — the only
  door), boot → Y names X', one `X'→blocks→Y` edge, no `X→blocks→Y`, one `straggler` note, count
  logged 1; second boot → 0, silent; a 3-hop chain X→X'→X'' → Y names X''; a straggler whose X' is
  ITSELF superseded but whose head is `done` → re-anchored to the head (and, per FORK-A, its
  claimability follows the head's status); the in-window render pin (kickoff §5 (c)) STANDS.
- **The finding (filed this session — the bound's ledger row, with the trigger):** *"the R2 write-skew
  window on supersede vs a concurrent create naming the same blocker; healed at the next boot; re-open
  trigger: a strand observed on `:18500` whose blocker was superseded AFTER 58 deployed AND the
  operator judges the boot window too long"* — at which point shape (i) (the blocker touch) is the
  designed close, costed above.
- **Index rider (RECOMMENDED, held integration patch — `surreal_schema.py` is 63c-shared):**
  `_plain_index(TASK_TABLE, "task_blocked_by", ("blocked_by.*",))` — the element-path index store-ref §2
  measured serving `CONTAINS`/`CONTAINSANY` — turns `direct_dependents`, R1's closing guard, the
  straggler heal and 64d-ii's delete-obj pre-check from TableScans into IndexScans; `IF NOT EXISTS`,
  builds once at the 65 boot (bounded by the task table). Pin: an EXPLAIN over the real `_task_
  statements` DDL with the index → `IndexScan` for `blocked_by CONTAINS $x`, C+ control without it →
  TableScan (the `probe_read_filter_63.py` walker). Not blocking 58's build; without it every one of
  those reads is a bounded TableScan of the task table, which is today's cost.

## Riders roll-up

| pin | where | RED when |
|---|---|---|
| A1: terminal X re-anchors ∀; `reblocked` subset served (K line present iff non-empty); claimed Z untouched | `test_supersede_reanchor_58.py` + the held-patch render pin | a status branch; a silent re-block |
| R1: closing guard → typed teaching refusal, byte-inert, second call succeeds | `test_supersede_reanchor_58.py` (injected handle) | a straggler left behind; an auto-retry |
| R2 heal: raw straggler → re-anchored at boot, noted `straggler`, counted; idempotent; chain to head | a boot-time test beside the backfill pins | a heal that leaves the old edge; one that re-runs every boot |
| in-window truth: R10(iii) render on a stranded claim | kickoff §5 (c) pin | — |
| index rider EXPLAIN + C+ | schema pins (held patch) | a TableScan with the index present |
| the finding's trigger text | finding body | — |

## Discipline
- Store law: §2 (element-path index; `CONTAINS` on a plain index is a silent `[]`), §3 (all statements
  verified — the closing guard is one more), §5 (no hand-rolled retry; hot-row cost named), §4 (edge
  DELETE/RELATE, ENFORCED).
- Packages considered: none — every mechanism extends a shipped seam (`_backfill_blocks_edges`, the
  shell, `_render_claim_result`).
- No code/tests/store touched; this doc only; no attribution trailer.
