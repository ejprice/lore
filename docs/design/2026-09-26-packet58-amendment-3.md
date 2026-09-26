# Packet 58 — ruling amendment 3 (sidecar-64, 2026-09-26): adversary-58's five decisions — my amendment-2 chunk sizing is DEFECTIVE (erratum), fail-open vs FAILS_LOUD reconciled + the heal's order, the claim-loss log level, a legacy loop under re-anchor, a phantom chain head at boot; the SAT defects for the reviser

Rules `REPORT-adversary-58.md` (verdict INSUFFICIENT; §AM2, §MISSING PINS, §SAT, §RESIDUALS — graded
against amendment 2 `e0760fd`, constructions PR17–PR20, WB1–WB18, K16/K17). Amends
`…packet58-amendment-2.md` §(b) and `…packet58-amendment-1.md` §FORK-C (the heal), and the kickoff §6.
**Operator scope: NONE of the five is MAJOR** — each is a HOW inside 58's ruled scope; (2) re-affirms a
standing repo invariant rather than changing one; (3) is a log level. Stated so the lead need not route
them. The contract revision (contract-58-r2) lands these rulings + the 14 missing pins + the 3 SAT
defects.

## 0. The rulings in one screen

| # | decision | ruling |
|---|---|---|
| **1** | heal chunk-size source (§AM2 #1, PR18/PR19) | **ERRATUM, mine.** Chunks are sized by the HEAL's OWN composed statement count — a greedy packer that BUILDS each row's fragments, counts the statements they add (rewrite shell ×2, the edge DELETE(s), the RELATE), and closes the chunk when the next row would exceed `TXN_STATEMENT_HARD_CAP`. The shared CONSTANT is the cap; the DERIVATION is per operation (the supersede's accessor and the heal's packer are two consumers of ONE counting function). The one-blocker pin is RE-KEYED to the packer's own count, never a literal chunk number; a multi-blocker population (≥ 6 distinct superseded blockers, cap+1 rows) is the discriminating fixture. §1 |
| **2** | fail-OPEN vs `ensure_ready`'s FAILS_LOUD sweep; D12's order (§AM2 #2, SD2) | **The standing invariant WINS; my "the boot never fails on a heal fault" is NARROWED to what it meant:** a STORE fault at any heal door (the straggler read, a chunk's apply) RAISES — loud, as every `ensure_ready` door must; only a chunk's DOMAIN rejection (a row-level THROW — a raced supersede, an ENFORCED refusal the packer did not pre-empt) is isolated + WARNING + continue. A `compose` cap refusal is a PACKER BUG and RAISES (never "retry forever"). **Order RULED: backfill → heal** (D12's pinned order is the ruled one; K17 is the correct world). The FAILS_LOUD sweep stays UNEDITED and green. §2 |
| **3** | the claim-loss ERROR log (MP14) | A routine claim LOSS is not an error. The claim shell's THROW carries a typed marker (`claim_lost:<id>`, the `governed_conflict:` precedent) the driver classifies into a typed `TxnClaimLostError` and logs at **DEBUG**; the ledger catches the TYPE, never the text. A rollback whose root cause is any other THROW logs at WARNING (a domain decision); ERROR stays for engine faults. Pin: an 8-way claim race emits ZERO ERROR/WARNING records for its 7 losers. §3 |
| **4** | a dependent already on a LEGACY loop (MP8, WB9) | Refuse ONLY a cycle the supersede INTRODUCES — one passing through X'. `minted = {new_id}` for the refusal predicate; the rewired dependents enter the GRAPH (so `Y → X' → … → Y` is found) but are NOT minted (their pre-existing loops are the backfill's recorded data defects, stepped over exactly as `_refuse_a_cycle` already steps over legacy loops). Pin: a Y on a legacy loop through its OTHER blocker Z → supersede(X) SUCCEEDS, Y re-anchored, the loop untouched + recorded; control: X' explicitly blocked_by [Y] → refused. §4 |
| **5** | a phantom chain head at boot (MP5, WB6/PR17) | The heal resolves every straggler's chain HEAD through the shared row-existence policy (`resolve_existing_rows` — the backfill's own phantom step) BEFORE building: a phantom head ⇒ that row is SKIPPED and RECORDED (`task.backfill.straggler_phantom_head`, WARNING, naming row · blocker · the phantom head), never a chunk failure and never a boot failure; excluded from `count`; re-recorded every boot until healed by hand (the backfill's phantom posture — a recorded bound stays visible). §5 |
| **SAT** | for contract-58-r2 | SD1 `≥ N+1` shell outputs (spy on `compose`, not the shell); SD2 pins the RULED order (backfill → heal); SD3 `_GUARDED_CAS_DOORS` gains `tasks.py::claim_task` (a DUAL row — routing claim through the THROW shell makes it a guarded-CAS door); the enumerator's two reach bounds (helper-indirected re-reads; tuple `except`) are the reviser's residuals to FILE. §6 |

## 1. Decision 1 — the heal chunk: sized by its OWN composed count (erratum against amendment 2 §(b))

- **The defect, named:** amendment 2 wrote *"chunks of `max_reanchor_dependents(0)` rows — the SAME derived
  accessor F-1 uses (one constant, one derivation)"*. The accessor derives the SUPERSEDE's per-dependent
  cost (one shared `DELETE blocks WHERE in = $old` for the whole operation); a heal chunk spans MANY
  superseded blockers, so it carries one DELETE per DISTINCT blocker (or one per row, depending on the
  builder's shape) — a different statement shape under the same accessor. A full chunk over ≥ 6
  distinct blockers composes > 5000, `compose` refuses it at build time, and "the next boot is the
  retry" retries a deterministic refusal forever (PR19: 1 of 1666 healed). **THE QUANTIFIER LAW, mine,
  again:** a property derived on one member (the supersede) stated over the set the ruling governs (every
  guarded re-anchor). And the pin I wrote (cap+1 rows of ONE blocker, `chunks == 2`) is the arithmetic-
  aligned fixture that cannot see it — it PASSES the defective build and REDS a correct packer that
  fits 4999 statements in one chunk (PR18). Same shape as am-14's lesson: I wrote the admitted shape
  before enumerating the correct builds it must admit.
- **Ruling:** ONE statement-counting function (`TaskLedger._composed_statement_count(fragments)` — the
  count `compose` itself performs, exposed; or `compose` spied — the builder chooses, the contract pins
  that the supersede's accessor and the heal's packer BOTH consume it). The heal packer is GREEDY: build
  the next row's fragments → if `current + added > TXN_STATEMENT_HARD_CAP` close the chunk → append. A
  single row that alone exceeds the cap (impossible for any real row — 2 + DELETEs + 1 — but pinned as
  a refusal, not an infinite chunk) RAISES a typed packer error (a store-class fault at boot: loud, §2).
  The supersede's `max_reanchor_dependents(k)` keeps its shape (its layout IS one shared DELETE) but
  its receipt now says so in the docstring, and WB2's bound is closed there too: the accessor takes the
  successor's K into account by BUILDING the fixed part for THAT call (PR16: at K=3 a 1664-dependent
  supersede composed 5001 — the accessor must count the real fixed part, never a sampled constant).
- **Pin it like this:** (i) the multi-blocker population — cap+1 stragglers spread over ≥ 6 distinct
  superseded blockers (PR19's shape) → ALL healed in ONE boot, `count == cap+1`, second boot silent;
  (ii) the one-blocker population STAYS but asserts `chunks == <the packer's own predicted chunk count
  for that population>` (read from the same counting function in the test — never a literal), so AM2C's
  single chunk is GREEN and AM2L's two-chunks-then-refuse is RED; (iii) `chunks × statements` sums to the
  composed total observed at the `_apply` spy, every chunk ≤ the cap; (iv) the supersede accessor at
  K ∈ {0, 1, 2, 3, per, per+1} (PR2/PR16's set) — cap+1 dependents at each K refused with the teaching,
  cap succeeds, and the served count equals `compose`'s; (v) mutation: pad the shell by one statement →
  the packer's chunk boundary AND the accessor move (two consumers of one count); a literal cap or chunk
  anywhere reds.
- **Cost:** the packer builds fragments it may then carry to the next chunk — bounded by one row's
  fragments (carry the built row, never rebuild).

## 2. Decision 2 — a heal STORE fault is LOUD; a chunk's DOMAIN rejection is isolated; the order is backfill → heal

- **What amendment 2 meant, and what it said:** it said *"the boot itself never fails on a heal fault"*
  — over-broad by one word. The intent was that ONE BAD ROW must not stop the sweep. The standing 04b-1
  instrument (`test_every_store_door_in_ensure_ready_over_a_legacy_store_FAILS_LOUD`) exists because a
  SWALLOWED store failure at boot is a false clear the fleet runs on for months (#131's class), and it is
  right. Ruling, by fault CLASS at each heal door:
  - the straggler READ (`SELECT … WHERE superseded_by IS NOT NONE` + the dependents scan): a store
    fault (`SurrealConnectionError`, `TxnContentionExhaustedError`, any `SurrealStoreError`) **RAISES**;
  - a chunk's APPLY: a **transport / engine fault RAISES**; a **domain rejection** (`TxnDomainRejection
    Error` — a row's CAS THROW because a supersede raced it, an ENFORCED refusal the packer did not
    pre-empt) is **isolated**: WARNING `task.backfill.straggler_chunk_rejected` naming the chunk index +
    its row ids, the sweep continues with the next chunk, the next boot re-heals the rows (idempotent);
  - a `compose` cap refusal is NOT a domain rejection — it is a packer bug, and it **RAISES**.
  This keeps the sweep's invariant exact: injecting a store fault at EVERY heal door still fails the
  boot loud; the sweep's door enumeration gains the heal's doors (read + apply) and pins them RAISE.
- **Order RULED: `_backfill_blocks_edges` THEN `_reanchor_stragglers`.** The backfill establishes
  `edge ≡ blocked_by` for every row including the stragglers' current `X→Y` edges (so the heal's
  per-row DELETE always finds the edge it retires — a heal-first world deletes nothing on a legacy row
  whose edge was never minted and then RELATEs a second truth); the backfill's phantom and cycle records
  precede the heal's, so the heal's own phantom-head record (§5) is the ONLY new class in the log.
  D12's edit pins this order for the ruled reason; K17 (heal after backfill, 20/20) is the correct world.
- **Pin it like this:** the FAILS_LOUD sweep, UNEDITED, green over the heal's doors (derived by fault
  injection — its own idiom); a chunk domain rejection (inject a raced supersede on one row of chunk k)
  → chunk k's rows byte-identical, chunk k+1 healed, one WARNING, the boot completes, the next boot heals
  chunk k's rows; a transport fault at chunk k → the boot RAISES (the sweep's own leg); the order pin:
  the heal's read observes edges the backfill minted in the SAME boot (a straggler seeded with NO edge
  → after boot: exactly one `head→Y` edge, no `X→Y`).

## 3. Decision 3 — a claim LOSS is DEBUG, typed, never ERROR

- **The defect:** routing claim through the THROW shell (kickoff §4, ruled) makes every ordinary loss
  a rolled-back transaction, and the driver's `_log_rollback` records rollbacks at ERROR — the fleet's
  most common contention outcome becomes an ERROR-level alarm on the normal path, which is how an
  alarm gets switched off (the switched-off-scanner law).
- **Ruling:** the claim's `throw_message` is a typed marker `claim_lost:<task id>` — the SAME mechanism
  the driver already has for `governed_conflict:<t>:<id>` (a THROW marker classified into a typed
  `TxnGovernedConflictError`), extended by CALL SET, not cloned: `_txn` maps `claim_lost:` →
  `TxnClaimLostError` and `_log_rollback` logs a rollback whose root cause is that class at **DEBUG**
  (the claim outcome is served as a `ClaimResult`; the store log is not its channel). `claim_task`
  catches the TYPE (never matches text — ROUTING IS NOT SHARING) and runs its post-CAS owner read as
  today. Every OTHER THROW-rooted rollback (transition/supersede lost races, R1's straggler, the heal's
  chunk) logs at **WARNING** (a domain decision, worth seeing, not an engine fault); ERROR stays for
  engine faults. The knob I rejected (a no-THROW shell variant) stays rejected.
- **Pin it like this:** an 8-way claim race → 1 winner, 7 `ClaimResult(claimed=False)`, ZERO log records
  at ERROR or WARNING from the driver for the losers (a `caplog` leg at the `_txn` logger); mutation:
  remove the marker → the losers log at WARNING → RED; a transition lost race still logs at WARNING
  (control); the marker→type mapping lives ONCE in `_txn` (an AST pin: `claim_lost` appears in
  `tasks.py` only as the throw_message constant and in `_txn` only in the classifier).

## 4. Decision 4 — a legacy loop through another blocker does not block the supersede

- **The defect (WB9):** a cycle check with `minted = {new_id} ∪ rewired dependents` refuses the
  supersede when ANY rewired Y already sits on a pre-existing loop (Y ⇄ Z through Y's OTHER blocker) —
  a loop the rewire did not close and no verb can edit, so X becomes un-supersedable forever.
- **Ruling:** the refusal predicate is *"a cycle THROUGH X'"* — `minted = {new_id}`; the rewired rows
  enter the graph under their POST-rewrite `blocked_by` (so a cycle `Y → X' → … → Y` closed by X''s
  own dependencies IS found and refused), and their pre-existing loops are stepped over by the SAME
  drop-loop `_refuse_a_cycle` already uses for legacy loops (R6 — a different loop through the same rows
  still surfaces). The backfill's cycle record already names the legacy loop; the supersede does not
  re-record it.
- **Pin it like this:** Y blocked_by [X, Z], Z blocked_by [Y] (a legacy loop seeded raw) → supersede(X)
  SUCCEEDS, Y re-anchored to X', Z untouched; CONTROL: X' with explicit `blocked_by=[Y]` → refused as a
  cycle through X', rolled back whole (the existing pin); a legacy loop that the rewrite would EXTEND
  (Y → X' → Y via X''s inherited blocked_by that already named Y) → refused (the inherited case).

## 5. Decision 5 — a phantom chain head is SKIPPED and RECORDED, never a boot failure

- **The defect (WB6/PR17):** a straggler whose `superseded_by` chain ends at a row that does not exist
  (a legacy data defect) makes the heal RELATE to a phantom; `ENFORCED` rejects it; under amendment 1
  the whole heal txn fails (the boot fails); under amendment 2 that chunk fails every boot.
- **Ruling:** before building, the heal resolves every straggler's chain to its HEAD and passes the
  head set through `resolve_existing_rows` (the shared row-existence policy the backfill uses for
  phantom blockers — L3, one implementation); a row whose head is a phantom is SKIPPED, RECORDED at
  WARNING (`task.backfill.straggler_phantom_head`, extra: `task_id`, `blocker_id`, `phantom_head_id`),
  excluded from `count`, and re-recorded at every boot until an operator heals the data (the backfill's
  own recorded-bound posture: a skipped straggler is a SCOPE BOUND on what the heal covers, and an
  unrecorded bound is one nobody can meet). A chain that CYCLES (`superseded_by` loops — corrupt data)
  is treated the same way, recorded as `straggler_chain_cycle`.
- **Pin it like this:** WB6's construction (a straggler whose head names no row) + one healable
  straggler → the boot COMPLETES, the healable row re-anchored, the phantom-headed row byte-identical,
  exactly one WARNING naming the three ids, `count == 1`; second boot → the healable row silent, the
  phantom WARNING repeated; CONTROL: fix the phantom by hand (create the head) → next boot heals it.

## 6. The SAT defects and the reviser's residuals (contract-58-r2)

- **SD1** `G::TestParamNamesDoNotCollideAcrossComposedShells`: assert `≥ N+1` shell outputs REACHED
  `compose` (spy on `compose`, not on the shell) — a build that derives the cap by building real
  fragments is the ruled mechanism and must be GREEN.
- **SD2** D12 (`scripts/test_forgery_door_sweep.py`): keeps its edit, now pinning the RULED order
  (backfill → heal) with §2's reason in the docstring; the UNEDITED `FAILS_LOUD` pin stays as is and is
  green under §2's fault-class rule.
- **SD3** `test_retry_seam.py` canonical `_GUARDED_CAS_DOORS` gains `tasks.py::claim_task` — a DUAL row
  (the door is NEW: claim's rollback handler now re-reads state); the enumerator's two reach bounds
  (a re-read through a HELPER escapes the inline-call match; a tuple `except (A, B)` is not recognised)
  are FILED by the reviser as findings against the enumerator (the reach class), not fixed in 58.
- **The 14 missing pins** land as the adversary specified (each probe pasted in its §INSTRUMENTS is a
  graded pin — landed AST-EQUAL where possible, am-17's rule); my rulings above re-key the am-2 pins
  (PR18/PR19) and add §2–§5's.
- **My two errata this packet** (amendment-2 (b)'s chunk source; amendment-1's "never fails" wording)
  are the same class: a rule derived on one operation and stated over two. The askable form, again:
  *"does this constant/claim hold on every statement shape it now governs, or only the one I derived it
  on?"* — the contract-adversary's construction is the instrument that answers it; my construction-free
  ruling was not.

## Riders roll-up

| pin | where | RED when |
|---|---|---|
| multi-blocker heal (≥ 6 blockers, cap+1 rows) in one boot; one-blocker chunks == the packer's own prediction; chunk sums ≤ cap; accessor at K ∈ {0,1,2,3,per,per+1}; one counting function (mutation) | `test_supersede_reanchor_58.py` (r2) | AM2L's literal chunk; a K-blind accessor; two counters |
| heal store fault RAISES (the FAILS_LOUD sweep, unedited, over the heal's doors); a chunk domain rejection isolated + WARNING + continue; order backfill → heal | `scripts/test_forgery_door_sweep.py` (D12 as ruled) + the heal pins | a swallowed store fault; a heal-first build; a compose refusal retried forever |
| 8-way claim race: 0 ERROR/WARNING for losers; `claim_lost:` typed once in `_txn`; transition lost race still WARNING | `test_task_guarded_shell_58.py` (r2) | ERROR on a routine loss; text matching in the ledger |
| legacy loop through another blocker: supersede succeeds; cycle through X' refused (two controls) | `test_supersede_reanchor_58.py` (r2) | `minted` includes rewired rows |
| phantom head: skipped + recorded + re-recorded; healable sibling healed; hand-fix control | the boot-heal pins (r2) | a chunk/boot failure on a phantom |
| SD1/SD2/SD3 as §6 | `G`, D12, `test_retry_seam.py` DUAL row | a correct build red |

## Discipline
- Store law: §3 (every chunk verified; a THROW is a domain rejection, classified semantically), §4
  (`ENFORCED` rejects a phantom endpoint — the reason §5 exists), §5 (no hand-rolled retry; the driver's
  classify-and-signal seam is extended by call, never cloned).
- Packages considered: none (the packer is arithmetic over `compose`'s own count; the marker
  classification is the driver's existing mechanism).
- No code/tests/store touched; this doc only; no attribution trailer.
