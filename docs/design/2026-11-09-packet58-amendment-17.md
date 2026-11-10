# Packet 58 — Amendment 17: the heal chunk that outlives its request timeout — the cause is a per-straggler table scan plus a transaction cost that grows with the square of its size; the packer's bound drops to the house WARN threshold

brief-base v27 read · brief project v7 read

**Author:** sidecar-58-2 (Fable design sidecar and fork ruler for packet 58; successor to sidecar-58-1, lost in a lead
session restart) · **Date:** 2026-11-09 (local) · HEAD `60b51c4` + builder-58-1's uncommitted tree
**Authority:** operator grant 2026-11-09 via lead-58 (forks and design questions go to the sidecar); the operator may
overturn. **Answers:** lead-58's question on the am-16 §8 trigger, parts (a)–(e) (builder-58-1's measurement,
`REPORT-builder-58-1.md` §HEAL-TIMING, lore_comms #20046).
**Amends:** am-15 §2 (the packer's `max_size`; the heal's edge DELETE), am-15 §1.3 (the supersede band, re-measured on
the real schema), am-16 §3 R-1 and §8 (the measure-then-tune decision, now taken; the interim WARN instrument retired),
am-16 §5 (the loop cap: one new property, one scoped delta grade).
**Read:** am-15 §0–§3, am-16 whole, `REPORT-builder-58-1.md` whole, `sdk3-rulings.md` R8 F11–F17 / R9 / R12 (F12, F19,
F21), the store reference's header, §0b, §0a, §0, §1.1, §3, §4, §5 (NOT read: §1.2–§2, §6–§10 — no DDL or DML idiom is
changed here), `tasks.py::_reanchor_stragglers` / `_plan_heal_rows` / `_pack_heal_chunks` / `_apply_heal_chunks` /
`_reanchor_fragments`, `_txn.py`'s row constants and `long_operation`, `surreal_schema.py::_task_statements`' tail.

## SUMMARY BLOCK
- **State:** done.
- **Deviations:** none. (Probes ran on the TEST store `:18000` only, throwaway databases, each dropped.)
- **Packages considered:** `more_itertools.constrained_batches` — KEEP (am-8 / am-15 verdict; only its `max_size`
  argument changes, the call is read at `tasks.py::_pack_heal_chunks`). No new mechanism.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 0 new production symbols. The bound is two existing `_txn` constants read live.
- **Graded:** n/a (a ruling). Measurements taken on builder-58-1's uncommitted tree over HEAD `60b51c4`.
- **Decisions needed (the operator may overturn; none blocks):** (1) §4 — the supersede's time-out band starts near
  5,700 dependents on the real schema, not 12,000; I keep it an accepted bound and name the move that would close it;
  (2) §6 — am-17 adds ONE new property, so the loop re-opens for ONE delta grade scoped to this amendment; the cheaper
  route is named there; (3) §7 — a store-reference line and a committed probe, both outside my writable set.
- **Pointers:** §0 rulings · §1 measurements · §2 (a) the bound · §3 the DELETE · §4 (b) the supersede · §5 (c) the
  hazard · §6 (d) pins and the loop · §7 (e) who changes what · §8 surfaced · §INSTRUMENT.

Fallbacks said out loud (brief-base §4): `grep` for every statement naming the `blocks` table inside f-strings, for the
`F12`/`F19`/`F21` ruling ids in prose, and for the test legs that read `TXN_ROW_HARD_CAP` — all three are textual seams,
the sanctioned case. No lore tool missed; no friction finding. Finding #618 filed (§8).

## ROUTING TABLE (written before the first probe)
| step | tier | who | reason |
|---|---|---|---|
| read the rulings, the builder report, the store reference, the heal code | 3 | self | the ruling rests on them |
| sweep: every production statement naming `blocks` | 1 | self, one grep (7 hits, 1 file) | on the critical path, read whole |
| sweep: 58 test legs that read the hard cap for the heal | 1 | self, one grep (13 files opened, 8 hits) | sizes the contract churn; read whole |
| timing probes on `:18000` (parts A–F) | 1 | self, inline shell, serial | not a pass/fail verdict on code; concurrent runs would perturb the timings they measure |
| the ruling | 3 | self | design |

Fan-out: haiku 0 · sonnet 0 · peak 0.

## 0. The rulings in one screen

| # | question | ruling |
|---|---|---|
| **(a)** | the heal chunk's size bound | `max_size = min(_txn.TXN_ROW_WARN_THRESHOLD, _txn.TXN_ROW_HARD_CAP)`, both read when the heal runs; weight stays `_txn.fragment_rows`; `strict=True` stays. No new constant, no statement cap, one counting function. Measured at that bound: 7.25 s per chunk. |
| **(a′)** | what the bound alone does not fix | The heal's per-straggler `DELETE blocks WHERE in = … AND out = …` scans the whole un-indexed `blocks` table once per straggler. It becomes `DELETE $dependent<-blocks WHERE in = $old` (same edge set, cost bounded by the dependent's own blocker count). Without this, no chunk bound limits the chunk's time. |
| **(b)** | the supersede hub cap | Not touched by the DELETE defect (it issues ONE scan). But the real schema moves am-15 §1.3's band: 3,332 dependents commit in 10.2 s, 6,000 time out at 30 s. The band starts near 5,700, not 12,000. Still an accepted bound, with the corrected numbers; the closing move is named for the operator. |
| **(c)** | deterministic refusal forever | Closed for every straggler POPULATION (a chunk is at most 10,000 rows, measured 41× inside its 300 s budget, and no longer depends on the size of `blocks`). What remains is one named bound: a single row heavier than the chunk bound, which is am-8 F10's existing loud refusal at a lower weight. |
| **(d)** | pins and the loop cap | The bound is a RE-KEY of a pinned property. "The heal's time does not grow with unrelated edges" is a NEW PROPERTY. One scoped delta grade (§6). |
| **(e)** | who changes what | Builder: two production edits and two docstrings. Contract author (r5.3): re-key six legs, add four. §7. |

**Where I chose between readings (brief-base §2):**
1. *F12: "`TXN_ROW_HARD_CAP` is the one bound; packet 58's packer … re-size by rows"* — reading A: the packer's
   `max_size` must BE the hard cap; reading B: the packer sizes by rows, keeps no statement cap, and never exceeds the
   one bound. I pick **B**. No straggler POPULATION is refused below the hard cap: a chunk target below it
   only splits the same stragglers over more transactions. A SINGLE row heavier than the chunk bound IS refused
   (§5, §11); the earlier wording here ("a chunk target below it refuses nothing") over-claimed and is withdrawn. am-15 §2 fixed `max_size` at the hard cap under
   reading A without a real-schema measurement; this amends it.
2. *am-16 §8: "above 150 s … the packer's `max_size` re-opens"* — reading A: tune only `max_size`; reading B: find why
   the chunk is slow first. I pick **B**: the measured cause (§1.1) is one a smaller `max_size` cannot bound.

## 1. Measurements

All on 2026-11-09, TEST store `ws://127.0.0.1:18000`, engine 3.3.5, SDK 3.0.0, the REAL task schema via
`TaskLedger.ensure_ready`, builder-58-1's tree (`loremaster.__file__` printed:
`/home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`), one run per cell, a quiet host. Instrument:
§INSTRUMENT. Every stragglers world is the hub-shaped worst case the builder measured: all stragglers name ONE
superseded blocker with ONE open head.

### 1.1 The heal's edge DELETE alone (n statements in one transaction; `blocks` holds n edges)
| shape | n = 1,000 | n = 2,000 | n = 4,000 |
|---|---|---|---|
| V1 `DELETE blocks WHERE in = $i AND out = $o` (the heal's shape today) | 5.32 s | 20.21 s | 76.48 s |
| V2 `DELETE $i->blocks WHERE out = $o` (anchored at the superseded blocker) | 12.69 s | 52.40 s | 258.52 s |
| V3 `DELETE $o<-blocks WHERE in = $i` (anchored at the dependent) | 0.40 s | — | 1.63 s |
| V4 = V1 plus a plain index on `blocks.out` | 0.48 s | — | 2.27 s |

- Controls, every cell: a pair that does not exist deleted nothing; after the run the n target edges are gone. For V3
  and V4 a second blocker's edge into the same dependent SURVIVED (so the delete is pair-exact, not dependent-wide).
- V1 and V2 quadruple when n doubles. `blocks` has no index (`surreal_schema.py::_task_statements`' docstring: "NO
  `DEFINE FIELD` and NO index"), so each V1 statement reads every edge: about 4.8 µs per edge per statement. V2 walks
  the blocker's n outgoing edges per statement. V3 walks the dependent's incoming edges, which is its blocker count.
- So today's chunk time is about `stragglers × |blocks| × 4.8 µs` for the DELETEs alone. It depends on the total edge
  count, which the packer does not see. The builder's 12,500-straggler chunk needs about 750 s of DELETEs.

### 1.2 The whole boot heal, one chunk (the built ledger's own heal)
| stragglers | rows | today (V1) | with V3 swapped in at `_apply` |
|---|---|---|---|
| 500 | 2,000 | 2.21 s | — |
| 1,000 | 4,000 | 7.61 s | — |
| 2,000 | 8,000 | 28.21 s | — |
| 2,500 | 10,000 | — | **7.25 s** |
| 4,000 | 16,000 | 110.15 s | 21.29 s |
| 8,000 | 32,000 | — | 95.91 s |
| 12,500 | 50,000 | > 300 s, boot raised (builder-58-1) | 228.87 s |

- Every V3 run healed: every straggler on the head, zero edges left on the superseded blocker, the edge count unchanged.
- **Even with the scan removed, a transaction's time grows with the square of its row count** (10,000 → 16,000 rows is
  2.9× the time; 16,000 → 32,000 is 4.5×): about `0.9e-7 × rows²` seconds here. am-15 §1.3's own table shows the same
  curve on a schemaless table (8,000 → 16,665 dependents: 12.6 s → 53.7 s). The cause is NOT established (candidates:
  the per-statement cost of a transaction that carries tens of thousands of bound parameters, or the write set). It is
  a measured property of a statement-per-row transaction on this engine and SDK.
- A full 50,000-row chunk therefore takes 229 s with the scan fixed: over am-16 §8's 150 s line on its own.

### 1.3 The ruled build, emulated end to end (V3 + the packer bound at the WARN threshold)
12,500 stragglers, in a store that also holds 20,000 unrelated edges: **5 chunks of 10,000 rows, 35.25 s, all healed.**
Splitting is also cheaper in total, as the square law predicts (229 s in one chunk).

### 1.4 A real `supersede_task` of a hub, under the served 30 s timeout
| dependents | rows | wall-clock | outcome |
|---|---|---|---|
| 1,665 | 5,000 | 2.82 s | committed, 0 rows left on the hub |
| 3,332 | 10,001 | 10.15 s | committed, 0 rows left on the hub |
| 6,000 | 18,005 | 30.34 s | `SurrealOutcomeUnknownError`; all 6,000 rows still on the hub (nothing committed) |

## 2. (a) The heal chunk's size bound

- **Ruling.** `_pack_heal_chunks` packs with
  `max_size = min(_txn.TXN_ROW_WARN_THRESHOLD, _txn.TXN_ROW_HARD_CAP)`, both read from the module at call time.
  `get_len` stays the stored `fragment_rows` weight and `strict=True` stays, so `StragglerHealPackerError.row_cap`
  serves this bound.
- **Derived how.** It is a timing-justified row budget that needs no number of its own:
  - Heal chunks are independent (am-8 §2: each atomic, convergence intact), so nothing is gained by packing to the
    largest transaction the store accepts, and §1.2 shows something is lost: time grows with the square of the size.
  - The house already has a row count it calls unusually large, `TXN_ROW_WARN_THRESHOLD` (R9 D2). A heal that never
    composes a transaction the house itself would warn about is the rule; 10,000 is that constant's value today.
  - Measured at it: 7.25 s per chunk on the real schema (§1.2), 41× inside `ensure_ready_operation`'s 300 s and 4×
    inside the default 30 s.
  - `min(…, hard cap)` because a chunk must never exceed what `compose` accepts; it matters only in a world where the
    two constants are set the other way round (the contract's in-test shrinks are such worlds).
- **F12** (no second statement cap): none is kept. The packer sizes by ROWS; the hard cap is still the only refusal
  size; the WARN threshold is the row constant R9 D2 already created. No new constant is introduced.
- **F21** (read live): both constants are read as `_txn.<name>` when the heal runs.
- **am-3 / am-15 §2** (one counting function): unchanged. The weight is `_txn.fragment_rows`.
- **Why not a fraction of the hard cap, or a new `HEAL_CHUNK_ROWS`:** either is a number nobody derived, which is what
  am-15 §1.3 refused for the hub. Why not a longer timeout: a quadratic cost outgrows any fixed timeout.
- **What changes for a consumer:** nothing served. The boot's `task.backfill.stragglers_reanchored` record shows more
  `chunks` for a population over 10,000 rows.

## 3. (a′) The heal's edge DELETE becomes degree-bounded

- **The class** (one level up from "the chunk is too big"):
  - SHOULDN'T BE DOING: a row-capped transaction issuing, per row, a statement whose cost is the size of a whole table.
  - OTHER CONSEQUENCES: the row count stops being a strain measure for that transaction (each scan is priced as one
    row); a store with many healthy edges and few stragglers is slow too; the same boot fails the same way next time.
  - SIMPLEST CLOSING RULE: remove the scan. Then a row costs what a row costs, and §2's bound means what it says.
- **Ruling.** In `_plan_heal_rows`, each `DELETE blocks WHERE in = $<old> AND out = $<dependent>` becomes
  `DELETE $<dependent><-blocks WHERE in = $<old>`: still one statement per superseded blocker of the row, same
  parameters, same deleted set (§1.1 controls). Weights, `fixed` and `per` do not move, so no existing count pin moves.
- **Why V3 and not the index (V4):** V4 is a schema change on a table whose docstring records a decision to carry no
  index, it adds a write to every `RELATE`, and it grows the DDL exact-set pins. V3 changes one statement. Both
  measure the same.
- **Bound, named:** V3 costs the dependent's incoming edge count per statement. A task with thousands of blockers pays
  for them. Trigger: a `blocked_by` column longer than about 1,000 entries (none exists; production holds 234 tasks per the 2026-11-08 export — corrected from 116 by the packet 58 cold audit, sharing F-2).
- **Not changed:** the supersede's `DELETE blocks WHERE in = $old` (`tasks.py`, the `$ssx_old_rec` fragment). It is ONE
  scan per supersede, about 4.8 µs per edge in the store: 1 s at 200,000 edges. See §8.

## 4. (b) The supersede hub cap, re-checked on the real schema

- **Is it hit by the same defect? No.** The supersede deletes the old blocker's edges with one statement. Its
  per-dependent statements are the guarded UPDATE, its THROW guard and one RELATE; none scans a table.
- **Is am-15 §1.3's band where it said? No — I correct it.** §1.3 placed the band at "roughly 12,000 dependents
  upward", interpolated from a schemaless table and labelled a lower bound. On the real schema (§1.4) 3,332 dependents
  commit in 10.2 s and 6,000 time out. Interpolating the square law between them puts the 30 s line near 5,700
  dependents (NOT measured at that point). So between about 5,700 and the cap of 16,665 dependents a supersede is not
  refused with the teaching error: it times out, loud, and commits nothing (measured at 6,000).
- **§1.3's trigger sentence over-claimed and is corrected:** the WARN (`row_count > 10,000` ≈ 3,332 dependents) fires
  at 10.2 s, a factor of 3 in time before the band, not "an order of magnitude".
- **Ruling: the bound stays ACCEPTED, with these numbers.** am-15's reasons stand, and one is now sharper: the moves
  that close it either refuse work that succeeds today or re-open the graded shell.
- **The closing move, named for the operator (Decision 1), not taken:** price `max_reanchor_dependents` against the
  same `min(WARN, hard)` bound. The hub cap becomes 3,332 dependents (10.2 s, 3× inside the timeout), the band
  disappears, and no constant is added. Cost: hubs of 3,333 to about 5,700 dependents, which commit today, would be
  refused; the refusal sentence, its four typed facts, L1, L2 and the WARN pin (a supersede over the threshold must
  SUCCEED and warn) all change, in the half of the contract that r5.2 closed. I do not take it for a population about 14×
  production's whole task table (234 tasks in the 2026-11-08 export; "29×" used the stale 116, cold audit sharing F-2). **Trigger, unchanged:** the first `store.apply.large_transaction` record from a
  supersede.
- **Rider — and pin it like this:** `max_reanchor_dependents`'s docstring (BC-r5-3) states the corrected band (§1.4's
  three rows, the date, this section). The cold audit reads it. No test: the timing is a receipt (F19).

## 5. (c) Deterministic refusal forever

- **By population: closed.** With §2 and §3 a chunk is at most 10,000 rows and its time no longer depends on the size
  of `blocks`. Measured: 7.25 s for a full chunk; 35.25 s for 12,500 stragglers beside 20,000 unrelated edges.
- **What "closed" rests on, stated as facts:** the hub-shaped world (one blocker, one head) on this host, engine 3.3.5,
  SDK 3.0.0. Not measured: production's hardware, a store under concurrent load, stragglers with several superseded
  blockers each (their weight is higher, so fewer fit a chunk; the row bound still holds).
- **What remains, a named bound:** ONE row whose own weight exceeds the chunk bound makes `constrained_batches` raise,
  and the boot fails loud with `StragglerHealPackerError` on every boot. That is am-8 F10's accepted behaviour; the
  weight at which it happens drops from 50,000 rows to 10,000 (a task naming roughly 2,500 superseded blockers).
- **Re-open trigger, with its instrument in the same bullet:** the boot's `task.backfill.stragglers_reanchored` record
  with `chunks >= 2` on production (more than 10,000 rows of stragglers in one boot), or a boot that raises
  `SurrealOutcomeUnknownError` from the heal. Either one re-runs §INSTRUMENT part E on that store's shape.
- **am-16 §8's interim instrument is RETIRED:** "a heal chunk over 10,000 rows emits the size WARN" can no longer
  happen, because no heal chunk is over 10,000 rows.
- **am-16 §3 R-1's trigger is re-keyed:** "a heal `chunks` log above 1 on a population under 50,000 rows" becomes
  "under `min(WARN, hard)` rows".

## 6. (d) The pins owed, and the loop cap

### 6.1 The bound — a pinned property, re-keyed (contract-author work)
The property "every heal transaction's `fragment_rows` is at most the packer's live bound, and the chunk count is the
greedy packer's" is pinned. Its constant changes. One support helper states the ruled rule once for the tests
(`min(_txn.TXN_ROW_WARN_THRESHOLD, _txn.TXN_ROW_HARD_CAP)`, read live); the legs derive `fit` from it.
- **Legs that re-key** (the sweep's 8 hits over 13 files; the author confirms each by a run):
  `test_reanchor_58_r2_am2.py::test_PR18r2_cap_plus_one_of_ONE_blocker_heals_in_the_PACKERS_predicted_chunks`,
  the two `predicted_chunks` / `fit` sites in `test_reanchor_58_r2_rulings.py`,
  `test_reanchor_58_r3_convergence.py::test_one_boot_heals_the_whole_population_in_the_predicted_chunks` (and its
  `_cap()`), `test_reanchor_58_r3_probes.py`'s `rows <= _txn.TXN_ROW_HARD_CAP` assertion, and the over-weight single
  row leg (am-15 §2, last bullet). `test_reanchor_58_r4_state.py`'s `_HEAL_DRIVER_FIT` legs shrink the hard cap below
  the WARN threshold, so `min` leaves them unchanged — that is the leg that kills a packer reading the WARN threshold
  alone.
- **Pin it like this (new legs, each at a shrunk value per F19, each naming the wrong build it kills):**
  1. *WARN below hard* (the F-RB-5 fixture's world, 800 under 5,000): a `2·fit + 1` population, `fit` from the helper →
     every heal chunk's `fragment_rows` ≤ 800 and the chunk count equals `predicted_chunks`. Kills a packer still at
     the hard cap (one chunk of more than 800 rows).
  2. *Live read:* shrink `TXN_ROW_WARN_THRESHOLD` by `per·d` → `fit` drops by exactly `d` (am-15 L4's form). Kills a
     copied value.
  3. *Hard below WARN:* the existing `_HEAL_DRIVER_FIT` leg (9 stragglers, 3 chunks), unchanged, cited as this fate's
     pin.
  4. *The real constants, once:* with nothing monkeypatched, 2,501 one-blocker stragglers → `spy.heal_rows() ==
     [fit·per + fixed, …]` in exactly 2 chunks, the first of `fit = (10,000 − fixed) // per` rows. About 10 s. Every
     other leg runs under shrunk constants; this is the one that proves the shipped values. L3 (1,251 stragglers in
     ONE transaction at the unpatched constants) stays as it is and still kills a surviving 5,000.
- `StragglerHealPackerError.row_cap`'s pin (am-16 §2.1 sibling) re-keys from `_txn.TXN_ROW_HARD_CAP` to the helper.

### 6.2 The DELETE — a NEW property
> **SUPERSEDED IN PART by §9.4 (same day):** the timing leg below is REPLACED by an EXPLAIN leg (deterministic, and it
> also kills V2, so this section's named bound closes). The property and its NEW-PROPERTY status stand.

*The heal's time does not grow with edges that are not its own.* No contract round has stated it.
- **Pin it like this (one leg, two worlds, by behaviour):** world A holds n stragglers; world B holds the same n
  stragglers plus E unrelated edges seeded with `bulk_seed_dependents` under another blocker. Boot each once and time
  the boot. Assert `t_B < t_A + 10 s`, with n = 300 and E = 30,000.
  - On a correct build both boots are sub-second and differ by the cost of nothing.
  - On a build that keeps the table-anchored DELETE, B costs about `300 × 30,000 × 4.8 µs` = 43 s more (§1.1's rate).
  - So the margin is about 4× on both sides: a false red needs a 10 s stall on a sub-second boot, a false green needs
    the scan to run 4× faster than measured.
  - Non-vacuity in the same leg: both worlds healed all n (so B's boot did the heal), and `blocks` in B holds at
    least E edges before the boot.
  - It is a timing assertion, and the property is a timing property; a check on the statement's text would be a
    spelling check. If this leg ever reds on a correct build under load, that is a STOP to me, not a retry.
- **Bound, named and accepted:** the leg kills "scans `blocks` per straggler". It does not kill V2 (anchored at the
  superseded blocker), whose cost follows that blocker's degree, not E; at n = 300 V2 costs about 1 s and passes.
  Killing it needs a hub-shaped world of several thousand stragglers, which is the slow fixture F19 rules out. V2 is
  a shape nobody has a reason to write. Trigger: any edit to the heal's DELETE statement re-runs §INSTRUMENT part D.

### 6.3 Does this re-open the closed loop cap? Yes, once, scoped
- am-16 §5: after the r5.2 replay, "only a NEW PROPERTY reopens the loop". §6.2 is one. §6.1 is not, but it rides the
  same pass.
- **Ruling: contract r5.3 → ONE adversary delta grade → the builder's two edits → the cold audit.** The grade's
  scope, exhaustive:
  1. SAT of r5.3's new and re-keyed legs on a reference = builder-58-1's tree plus §7's two production edits, built
     by the adversary in a `scratch_copy.sh` copy (`loremaster.__file__` printed);
  2. five named wrong builds, each must die by the leg named: packer at the hard cap (§6.1 leg 1); packer at the WARN
     threshold with no `min` (leg 3); a copied 10,000 (leg 2); a surviving 5,000 (L3); the table-anchored DELETE kept
     (§6.2);
  3. its own "what wrong build passes?" enumeration limited to these two families (the packer's bound; the heal's
     DELETE). No other part of the contract is re-graded.
  After it the cap is closed again on am-16 §5's terms (a pin that is simply wrong: author corrects, lead verifies the
  one replay).
- **Cost for the operator:** am-16 §5 counted 4 adversary and 6 author runs before r5.2, and r5.2 added one of each
  (its replay was interrupted by the session restart and finished by a respawn, `60b51c4`). This adds one more of
  each, both small.
- **The cheaper route, named so the operator can choose it (Decision 2):** skip the adversary; r5.3 lands, the builder
  applies §7, and the COLD AUDIT runs the five wrong builds above as declared-RED mutation proofs
  (`scripts/mutation_proof.py`, ids from `--collect-only`). It saves one adversary run. I do not rule it because this
  repo's two receipts against skipping the adversary on a "small" delta are both from this year, and am-16 §5 refused
  the same shortcut for r5.2.

## 7. (e) Who changes what

**Builder (production; `tasks.py` only):**
1. `_pack_heal_chunks`: the bound of §2. *Rider:* its docstring states the bound, that it is the WARN threshold by
   ruling (am-17 §2), the measured 7.25 s, and §5's trigger. `StragglerHealPackerError` is raised with that bound as
   `row_cap`.
2. `_plan_heal_rows`: the DELETE of §3. *Rider:* a comment on the statement naming the constraint the code cannot
   show ("`blocks` has no index: a table-anchored DELETE scans it once per straggler — am-17 §3"), and the probe's
   path.
3. `max_reanchor_dependents`'s docstring: §4's corrected band (replaces the am-15 §1.3 numbers BC-r5-3 had it state).
4. Build close-out receipt (replaces am-16 §8's): §INSTRUMENT part E's real heal, unmodified this time, at 2,500 and
   12,500 stragglers on the built tree — expected about 7 s in 1 chunk and about 35 s in 5. A result over 30 s per
   chunk comes to me.
5. The builder writes no test and edits none. Legs that go red from edits 1–2 before r5.3 lands are r5.3's.

**Contract author (r5.3; test files and `_reanchor_58_support.py` only):**
1. the support helper and the re-keyed legs of §6.1; 2. §6.1's four pins; 3. §6.2's leg; 4. `red_nodeids` updated in
the same change (every new leg is RED on builder-58-1's present tree: the packer is at the hard cap and the DELETE
scans) and `--currency --legs typecheck,ruff` at RED_ORPHANED 0; 5. the author builds no wrong build (role boundary).

**Lead:** commit §INSTRUMENT as `scripts/probe_heal_curve_58.py` (outside my writable set; same class as am-15 §6
item 9's `probe_hub_txn_58.py`), with the house probe sign-in if that convention applies to it.

## 8. Surfaced, not ruled

1. **A transaction's time is quadratic in its row count for statement-per-row composers** (§1.2, §1.4; am-15 §1.3's
   table shows it too). `TXN_ROW_HARD_CAP = 50,000` therefore admits an un-annotated transaction of about 230 s on the
   task schema. In `loremaster` only 58's two composers reach that size today; the index writer's rows ride batched
   `INSERT`s, which this measurement does not cover. Filed as finding #618. Whether the
   store reference should carry it is the lead's call; the line I would add to §3: *"[MEASURED 2026-11-09, 3.3.5 + SDK
   3.0.0, am-17 §1] one `BEGIN … COMMIT` of n one-row statements costs about `1e-7 × n²` s on the task schema (10,000
   rows ≈ 7–10 s; 50,000 ≈ 230 s); cause not established. Split work that need not be atomic."*
2. **The supersede's one `DELETE blocks WHERE in = $old` is a table scan** (§3). Linear in the store's edge count, 1 s
   at about 200,000 edges, inside a served verb with a 30 s budget. Not a defect at any size this store will see soon.
   Do you want it changed to `DELETE $old->blocks` (bounded by the hub's own degree)? It edits the graded supersede
   transaction, so I did not rule it.
3. **`blocks` has no index at all.** Every other reader traverses from a record (`<-blocks<-task`), which needs none.
   The two table-anchored statements above were the only ones (sweep: 7 hits in `tasks.py`, coverage 1 file of the 2
   that name the table; `surreal_schema.py` only defines it).
4. `REPORT-builder-58-1.md` §HEAL-TIMING concludes "a store with > ~12k stragglers would fail boot loud". On its tree
   the threshold is lower and moves with the edge count: 4,000 stragglers already take 110 s (§1.2).

## §INSTRUMENT — `probe_heal_curve_58.py`, pasted verbatim (run 2026-11-09 from the repo root, `uv run python <file> A|B|C|D|E|F`)

Parts D–F were appended as the earlier parts' results came in; the file is pasted as run. Part E's default sizes were
overridden on the command line (`E 2500,4000,8000,12500 V3`). It reads the TEST store's address and credentials from
the test harness and prints neither.

```python
"""am-17: the boot heal's cost CURVE on the REAL schema (TEST store :18000 only), and what drives it.

A  heal wall-clock for ONE chunk of n one-blocker stragglers, n in A_SIZES (the built ledger's own heal).
B  the per-straggler edge DELETE alone, n statements in one transaction over a `blocks` table of n edges:
   V1 = the heal's shape (`DELETE blocks WHERE in = $i AND out = $o`), V2 = the graph-anchored shape
   (`DELETE $i->blocks WHERE out = $o`); control: edges remaining after each == 0, and a V2 on a pair that
   does not exist deletes nothing.
C  a real `supersede_task` of a hub with N dependents under the served 30 s timeout, N in C_SIZES.
Run from the repo root: `uv run python <this file> A|B|C`.
"""
import asyncio
import sys
import time

sys.path.insert(0, "/home/ejprice/PycharmProjects/lore/loremaster/tests")
import _reanchor_58_support as s  # noqa: E402
from _surreal_harness import drop_database, make_env, unique_database  # noqa: E402
from loremaster.store import _txn  # noqa: E402
from loremaster.store._txn import TxnFragment, ensure_ready_operation  # noqa: E402
from surrealdb import RecordID  # noqa: E402

A_SIZES = (500, 1000, 2000, 4000)
B_SIZES = (1000, 2000, 4000)
C_SIZES = (1665, 3332, 6000)


async def fresh():
    env = make_env(database=unique_database(), dim=s.PRODUCTION_DIM)
    assert ":18000" in env.url, "TEST store only"
    ledger = s.new_ledger(env)
    await ledger.ensure_ready()
    return env, ledger


async def edge_count(ledger) -> int:
    rows = await s.raw(ledger, "SELECT count() AS n FROM blocks GROUP ALL")
    rows = rows if isinstance(rows, list) else [rows]
    return int(rows[0]["n"]) if rows else 0


async def part_a() -> None:
    for n in A_SIZES:
        env, ledger = await fresh()
        try:
            await s.seed_stragglers(ledger, n, 1, "c")
            edges = await edge_count(ledger)
            spy = s.ComposeSpy()
            t = time.monotonic()
            with spy.installed():
                try:
                    await s.boot(env)
                    outcome = "ok"
                except Exception as e:  # noqa: BLE001 - a probe reports what it saw
                    outcome = f"RAISED {type(e).__name__}"
            wall = time.monotonic() - t
            print(f"A n={n} edges_before={edges} heal_rows={spy.heal_rows()} wall={wall:.2f}s "
                  f"outcome={outcome} edges_after={await edge_count(ledger)}", flush=True)
        finally:
            await ledger.close()
            await drop_database(env)


@ensure_ready_operation
async def _apply_long(ledger, fragments) -> None:
    await ledger._apply(fragments)  # noqa: SLF001 - the heal's own write door


async def part_b() -> None:
    shapes = {
        "V1 table-anchored": "DELETE blocks WHERE in = $i{k} AND out = $o{k}",
        "V2 graph-anchored": "DELETE $i{k}->blocks WHERE out = $o{k}",
    }
    for n in B_SIZES:
        for name, shape in shapes.items():
            env, ledger = await fresh()
            try:
                await s.raw_seed_row(ledger, "hubx", blocked_by=[])
                ids = await s.bulk_seed_dependents(ledger, "hubx", n, "d")
                before = await edge_count(ledger)
                params = {}
                for k, dep in enumerate(ids):
                    params[f"i{k}"] = RecordID("task", "hubx")
                    params[f"o{k}"] = RecordID("task", dep)
                # control first: a pair that does not exist deletes nothing
                await _apply_long(ledger, [TxnFragment(
                    statements=[shape.format(k="c")],
                    params={"ic": RecordID("task", ids[0]), "oc": RecordID("task", "hubx")})])
                control = await edge_count(ledger)
                frag = TxnFragment(statements=[shape.format(k=k) for k in range(n)], params=params)
                t = time.monotonic()
                try:
                    await _apply_long(ledger, [frag])
                    outcome = "ok"
                except Exception as e:  # noqa: BLE001
                    outcome = f"RAISED {type(e).__name__}: {str(e)[:120]}"
                wall = time.monotonic() - t
                print(f"B {name} n={n} edges_before={before} after_control={control} wall={wall:.2f}s "
                      f"outcome={outcome} edges_after={await edge_count(ledger)}", flush=True)
            finally:
                await ledger.close()
                await drop_database(env)


async def part_c() -> None:
    for n in C_SIZES:
        env, ledger = await fresh()
        try:
            hub = await s.create(ledger, "hub")
            await s.bulk_seed_dependents(ledger, hub, n, "h")
            spy = s.ComposeSpy()
            t = time.monotonic()
            with spy.installed():
                try:
                    await s.supersede(ledger, hub)
                    outcome = "ok"
                except Exception as e:  # noqa: BLE001
                    outcome = f"RAISED {type(e).__name__}"
            wall = time.monotonic() - t
            moved = await s.raw(ledger, "SELECT count() AS n FROM task WHERE blocked_by CONTAINS $h GROUP ALL",
                                {"h": hub})
            print(f"C dependents={n} rows={spy.rows[-1] if spy.rows else None} wall={wall:.2f}s "
                  f"outcome={outcome} still_on_hub={moved}", flush=True)
        finally:
            await ledger.close()
            await drop_database(env)


if __name__ == "__main__":
    print(f"cap={_txn.TXN_ROW_HARD_CAP} request_timeout={_txn.SURREAL_REQUEST_TIMEOUT_SECONDS}", flush=True)
    if sys.argv[1] in ("A", "B", "C"):
        asyncio.run({"A": part_a, "B": part_b, "C": part_c}[sys.argv[1]]())


# ---- parts D / E (added after part B showed V1 and V2 both quadratic) -------------------------------------
import dataclasses  # noqa: E402
import re  # noqa: E402

from loremaster.tasks import TaskLedger  # noqa: E402

D_SIZES = (1000, 4000)
E_SIZES = tuple(int(x) for x in (sys.argv[2] if len(sys.argv) > 2 else "4000,12500").split(","))
INDEX_DDL = "DEFINE INDEX IF NOT EXISTS blocks_out ON blocks FIELDS out"
_HEAL_DELETE = re.compile(r"DELETE blocks WHERE in = (\$\w+) AND out = (\$\w+)")


async def part_d() -> None:
    """The edge DELETE alone again: V3 anchored at the DEPENDENT (its in-degree is its blocker count), and
    V4 = the heal's own shape with a plain index on `blocks.out`. Controls as part B, plus a V3/V4 leg where
    the dependent has a SECOND blocker whose edge must survive."""
    shapes = {
        "V3 dependent-anchored": ("DELETE $o{k}<-blocks WHERE in = $i{k}", False),
        "V4 table-anchored+index(out)": ("DELETE blocks WHERE in = $i{k} AND out = $o{k}", True),
    }
    for n in D_SIZES:
        for name, (shape, index) in shapes.items():
            env, ledger = await fresh()
            try:
                if index:
                    await s.raw(ledger, INDEX_DDL)
                await s.raw_seed_row(ledger, "hubx", blocked_by=[])
                await s.raw_seed_row(ledger, "otherhub", blocked_by=[])
                ids = await s.bulk_seed_dependents(ledger, "hubx", n, "d")
                await s.raw_relate(ledger, "otherhub", ids[0])  # must SURVIVE the delete of (hubx, ids[0])
                before = await edge_count(ledger)
                params = {}
                for k, dep in enumerate(ids):
                    params[f"i{k}"] = RecordID("task", "hubx")
                    params[f"o{k}"] = RecordID("task", dep)
                await _apply_long(ledger, [TxnFragment(
                    statements=[shape.format(k="c")],
                    params={"ic": RecordID("task", ids[0]), "oc": RecordID("task", "hubx")})])
                control = await edge_count(ledger)
                frag = TxnFragment(statements=[shape.format(k=k) for k in range(n)], params=params)
                t = time.monotonic()
                try:
                    await _apply_long(ledger, [frag])
                    outcome = "ok"
                except Exception as e:  # noqa: BLE001
                    outcome = f"RAISED {type(e).__name__}: {str(e)[:160]}"
                wall = time.monotonic() - t
                survivor = await s.raw(ledger, "SELECT in, out FROM blocks")
                print(f"D {name} n={n} edges_before={before} after_control={control} wall={wall:.2f}s "
                      f"outcome={outcome} edges_after={await edge_count(ledger)} survivor={survivor}", flush=True)
            finally:
                await ledger.close()
                await drop_database(env)


async def part_e() -> None:
    """The REAL heal (built ledger, real schema, one chunk) with the edge DELETE swapped for V3 (statement
    rewrite at `_apply`, production untouched) or served by V4's index. n=12500 is the full 50,000-row chunk."""
    real_apply = TaskLedger._apply  # noqa: SLF001

    async def rewriting_apply(self, fragments):
        swapped = [
            dataclasses.replace(f, statements=[_HEAL_DELETE.sub(r"DELETE \2<-blocks WHERE in = \1", st)
                                               for st in f.statements])
            for f in fragments
        ]
        return await real_apply(self, swapped)

    for n in E_SIZES:
        for name in (sys.argv[3].split(",") if len(sys.argv) > 3 else ("V3", "V4")):
            env, ledger = await fresh()
            try:
                if name == "V4":
                    await s.raw(ledger, INDEX_DDL)
                head, ids = await s.seed_stragglers(ledger, n, 1, "e")
                before = await edge_count(ledger)
                spy = s.ComposeSpy()
                if name == "V3":
                    TaskLedger._apply = rewriting_apply  # noqa: SLF001
                t = time.monotonic()
                try:
                    with spy.installed():
                        try:
                            await s.boot(env)
                            outcome = "ok"
                        except Exception as e:  # noqa: BLE001
                            outcome = f"RAISED {type(e).__name__}: {str(e)[:160]}"
                finally:
                    TaskLedger._apply = real_apply  # noqa: SLF001
                wall = time.monotonic() - t
                on_head = await s.raw(
                    ledger, "SELECT count() AS n FROM task WHERE blocked_by CONTAINS $h GROUP ALL", {"h": head})
                legacy_edges = await s.raw(
                    ledger, "SELECT count() AS n FROM blocks WHERE in = $l GROUP ALL",
                    {"l": RecordID("task", "elegacy0000000000000000000")})
                print(f"E {name} n={n} edges_before={before} heal_rows={spy.heal_rows()} wall={wall:.2f}s "
                      f"outcome={outcome} rows_on_head={on_head} old_edges_left={legacy_edges} "
                      f"edges_after={await edge_count(ledger)}", flush=True)
            finally:
                await ledger.close()
                await drop_database(env)


if __name__ == "__main__" and sys.argv[1] in ("D", "E"):
    asyncio.run({"D": part_d, "E": part_e}[sys.argv[1]]())


async def part_f() -> None:
    """The RULED build emulated end to end: V3 delete + the packer bound at TXN_ROW_WARN_THRESHOLD (the packer
    reads `_txn.TXN_ROW_HARD_CAP` live, so the probe process sets it to the warn threshold), 12,500 stragglers
    in a world that ALSO holds 20,000 unrelated edges. Expect 5 chunks of 10,000 rows."""
    _txn.TXN_ROW_HARD_CAP = _txn.TXN_ROW_WARN_THRESHOLD
    sys.argv[2:] = ["12500", "V3"]
    global E_SIZES
    E_SIZES = (12500,)
    real_seed = s.seed_stragglers

    async def seed_with_noise(ledger, total, blockers, tag):
        await s.raw_seed_row(ledger, "noisehub", blocked_by=[])
        for part in range(4):
            await s.bulk_seed_dependents(ledger, "noisehub", 5000, f"n{part}x")
        return await real_seed(ledger, total, blockers, tag)

    s.seed_stragglers = seed_with_noise
    await part_e()


if __name__ == "__main__" and sys.argv[1] == "F":
    asyncio.run(part_f())
```

## 9. Follow-up (lead-58, lore_comms #20049): the supersede's edge DELETE, and a better pin for both DELETEs

The lead's calls on am-17 (committed `dba16ff`): Decision 2 = the adversary route (§6.3 stands); §8 item 2 = YES, fix
the sibling in this wave; §8 item 1 = the lead adds the store-reference line; the probe commit goes to the r5.3
author with the house sign-in seam. This section rules the sibling. Measured 2026-11-09 on the tree at `dba16ff` plus
builder-58-1's uncommitted edits, TEST store `:18000`, engine 3.3.5, SDK 3.0.0, real schema. Instruments: §INSTRUMENT-2.

### 9.1 Measurements
| statement | hub edges | unrelated edges | wall-clock | edges left from the hub | edge INTO the hub |
|---|---|---|---|---|---|
| T `DELETE blocks WHERE in = $old` (today) | 10 | 0 | 0.005 s | 0 | survived |
| T | 10 | 100,000 | **0.587 s** | 0 | survived |
| G `DELETE $old->blocks` | 10 | 0 | 0.006 s | 0 | survived |
| G | 10 | 100,000 | **0.008 s** | 0 | survived |
| T | 3,000 | 30,000 | 0.896 s | 0 | survived |
| G | 3,000 | 30,000 | 0.945 s | 0 | survived |

- Both forms delete the same set in every world (the hub's outgoing edges and nothing else; the unrelated edge count
  is unchanged). T pays about 5.9 µs per edge in the store; G pays for the hub's own edges only.
- At 30,000 unrelated edges the difference is inside one run's noise. A timing pin at F19 sizes cannot see it.
- **A DELETE's plan IS observable on 3.3.5:** `<DELETE …> EXPLAIN` returns the plan and deletes nothing (5 edges
  before, 5 after). `EXPLAIN DELETE …` (prefix form) is rejected. The plan is a list of `{operation, detail}` nodes —
  not the `{operator, attributes, children}` tree a SELECT's EXPLAIN returns:

| statement EXPLAINed | plan |
|---|---|
| T `DELETE blocks WHERE in = $old` | one `Iterate Table` with `detail.table == "blocks"` |
| G `DELETE $old->blocks` (hub with 5 edges) | 5 × `Iterate Record` |
| heal V1 `DELETE blocks WHERE in = $i AND out = $o` | one `Iterate Table`, `blocks` |
| heal V2 `DELETE $i->blocks WHERE out = $o` (blocker with 50 dependents) | 50 × `Iterate Record` |
| heal V3 `DELETE $o<-blocks WHERE in = $i` (dependent with 2 blockers) | 2 × `Iterate Record` |

### 9.2 Ruling — the statement form
In `_supersede_transaction`, `DELETE blocks WHERE in = $ssx_old_rec` becomes **`DELETE $ssx_old_rec->blocks`**. Same
parameter, still ONE statement in the same fragment at the same position, so `fixed(K)`, `per`, the hub cap, the
refusal's four facts and every count pin are unchanged. It is bounded by the superseded task's own dependent count,
which the transaction re-anchors one by one anyway.
- **Removed-behaviour inventory (the old statement):** deletes every edge whose `in` is the old task — PRESERVED
  (§9.1, both worlds; pinned today by the supersede legs that assert the edge mirror after a supersede). Deletes no
  edge whose `out` is the old task — PRESERVED (the "edge INTO the hub" column). Duplicate edges for one pair (the
  table has no UNIQUE): both forms remove all of them — not separately measured; the mirror legs cover it if any
  fixture seeds a duplicate, otherwise it is spec-silent and unchanged in kind.

### 9.3 Class statement
No statement a task verb or the boot heal sends iterates the whole `blocks` table. After §3 and §9.2 the sweep of §8
item 3 has no table-anchored `blocks` write left; the boot backfill's one `SELECT … FROM blocks` read stays (it is
the backfill's job to read every edge, once per boot).

### 9.4 The pin — one EXPLAIN leg per DELETE, by what the plan iterates (REPLACES §6.2's timing leg)
- **Why EXPLAIN and not time:** §9.1 shows time cannot discriminate at fixture sizes for the supersede, and §6.2's
  timing leg carried a flake margin and a named hole (V2). The plan is deterministic and closes that hole.
- **Pin it like this (supersede leg):** a hub with N = 5 dependents in a store that also holds E ≥ 20 unrelated
  edges under another blocker. Spy `compose` during a real `supersede_task`; take from the recorded transaction the
  statement that deletes the old task's edges, **found by its bound parameter** (the one whose value is the old
  task's `RecordID`), never by its text — the house precedent is `test_brief_ledger.py`'s captured-Q2 pin. Run
  `<that statement> EXPLAIN` with the recorded parameters on a world rebuilt to the pre-supersede state (or captured
  through an `ApplyHook` before the write). Assert:
  1. the plan does not iterate the `blocks` table (walker below);
  2. the plan's `Iterate Record` count == N (the hub's own edges; E plays no part);
  3. the EXPLAIN deleted nothing (edge count unchanged).
  **C+ control in the same leg:** the table-anchored statement, EXPLAINed over the same world, DOES trip assertion 1.
- **Pin it like this (heal leg):** one straggler that has TWO blockers (the superseded one and a live one), under a
  superseded blocker that has ≥ 5 other dependents, plus E ≥ 20 unrelated edges. From the heal chunk's recorded
  transaction take the edge-DELETE statement (the one binding both the dependent's and the old blocker's `RecordID`),
  EXPLAIN it over the pre-heal world. Assert: no `blocks` table iteration; `Iterate Record` count == 2 (the
  dependent's blocker count). The second assertion is what kills V2, which iterates the blocker's ≥ 6 edges. Same C+.
- **One walker (one implementation):** `_governed_contract.scans_table` recognises only the SELECT tree
  (`operator == "TableScan"`, `attributes.table`). It is EXTENDED in place to also answer True for a statement-plan
  node with `operation == "Iterate Table"` and `detail.table == <table>`; a sibling `iterated_records(plan)` counts
  `Iterate Record` nodes. Its existing callers pass SELECT plans, whose shape the new arm cannot match, so their
  behaviour does not change. Both arms get the C+ control above. This is a contract-author edit to a landed 63a
  support file: **the lead grants that one file** (same class as am-15 §9.3 / am-16 §4).
- **Stated bound:** `Iterate Record` / `Iterate Table` are engine plan vocabulary read on 3.3.5. An engine upgrade
  that renames them reds the C+ control first (it stops seeing the table scan), which is the right failure.
- **Fate of §6.2's timing leg:** not written. §6.2's named bound (V2 unpinned) is closed by the heal leg above.
- Both legs are RED on builder-58-1's present tree (both statements iterate the table) and enter `red_nodeids`.

### 9.5 What §6.3's grade gains
Still ONE scoped delta grade (the lead's call). Its wrong-build list becomes seven: the five of §6.3 item 2 — with
"the table-anchored heal DELETE kept" now dying by §9.4's heal leg instead of the timing leg — plus:
6. the table-anchored SUPERSEDE DELETE kept → dies by §9.4's supersede leg, assertion 1;
7. the heal DELETE anchored at the blocker (V2) → dies by §9.4's heal leg, the record count.
Its enumeration scope (§6.3 item 3) gains one family: the supersede's edge DELETE. Is §9.2 a new property? It is the
§6.2 property ("no time or plan growth with unrelated edges") extended to its sibling statement, inside the grade
that property already re-opened; it does not re-open anything further.

### 9.6 Riders (amending §7)
**Builder — edit 6:** `_supersede_transaction`: §9.2's statement. *Rider:* the same one-line constraint comment as
edit 2 ("`blocks` has no index — a table-anchored DELETE iterates the whole table; am-17 §9"), on this statement.
Nothing else in the fragment moves. The builder's targeted run includes the supersede edge-mirror legs.
**Contract author (r5.3):** §9.4's two legs replace §6.2's leg in §7's list (item 3); the walker extension with its
C+ control; the probe files of §INSTRUMENT and §INSTRUMENT-2 committed under `scripts/` through the house sign-in seam
(lead's call, #20049).
**§8 item 2 is hereby ruled, not surfaced. §8 item 1 is the lead's.**

## §INSTRUMENT-2 — the §9 probes, pasted verbatim (run 2026-11-09 from the repo root with `uv run python <file>`)

`probe_supersede_delete_58.py` (run with no arguments for the 3,000 / 30,000 world and the EXPLAIN attempts, and as
`… 10 100000` for the small-hub world):

```python
"""am-17 §9: the supersede's edge DELETE — is a DELETE's plan observable (EXPLAIN), and do the two forms
delete the same set at the same cost? TEST store :18000 only. Run from the repo root: `uv run python <file>`."""
import asyncio
import json
import sys
import time

sys.path.insert(0, "/home/ejprice/PycharmProjects/lore/loremaster/tests")
import _reanchor_58_support as s  # noqa: E402
from _surreal_harness import drop_database, make_env, unique_database  # noqa: E402
from surrealdb import RecordID  # noqa: E402

FORMS = {
    "T table-anchored": "DELETE blocks WHERE in = $old",
    "G graph-anchored": "DELETE $old->blocks",
}
HUB, NOISE = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (3000, 30000)


async def main() -> None:
    env = make_env(database=unique_database(), dim=s.PRODUCTION_DIM)
    assert ":18000" in env.url, "TEST store only"
    ledger = s.new_ledger(env)
    await ledger.ensure_ready()
    try:
        old = RecordID("task", "hubx")
        await s.raw_seed_row(ledger, "hubx", blocked_by=[])
        await s.raw_seed_row(ledger, "noisehub", blocked_by=[])
        await s.bulk_seed_dependents(ledger, "hubx", 5, "p")
        # 1. is a DELETE's plan observable?  (each attempt reports what the engine said)
        for text in (
            "DELETE blocks WHERE in = $old EXPLAIN",
            "DELETE $old->blocks EXPLAIN",
            "EXPLAIN DELETE blocks WHERE in = $old",
            "SELECT * FROM blocks WHERE in = $old EXPLAIN",
            "SELECT * FROM $old->blocks EXPLAIN",
        ):
            try:
                plan = await s.raw(ledger, text, {"old": old})
                print(f"PLAN  {text!r} -> {json.dumps(plan, default=str)[:700]}", flush=True)
            except Exception as e:  # noqa: BLE001 - a probe reports what it saw
                print(f"PLAN  {text!r} -> RAISED {type(e).__name__}: {str(e)[:200]}", flush=True)
        left = await s.raw(ledger, "SELECT count() AS n FROM blocks GROUP ALL")
        print(f"edges after the EXPLAIN attempts (5 seeded; an EXPLAIN must not delete): {left}", flush=True)
    finally:
        await ledger.close()
        await drop_database(env)
    # 2. same set, and cost against unrelated edges
    for name, form in FORMS.items():
        for noise in (0, NOISE):
            env = make_env(database=unique_database(), dim=s.PRODUCTION_DIM)
            ledger = s.new_ledger(env)
            await ledger.ensure_ready()
            try:
                await s.raw_seed_row(ledger, "hubx", blocked_by=[])
                await s.raw_seed_row(ledger, "noisehub", blocked_by=[])
                ids = await s.bulk_seed_dependents(ledger, "hubx", HUB, "d")
                await s.raw_relate(ledger, ids[0], "noisehub")   # an edge INTO another row FROM a dependent: survives
                await s.raw_relate(ledger, "noisehub", "hubx")   # an edge INTO the hub: must survive (out = hub)
                for part in range(noise // 5000):
                    await s.bulk_seed_dependents(ledger, "noisehub", 5000, f"n{part}x")
                before = await s.raw(ledger, "SELECT count() AS n FROM blocks GROUP ALL")
                t = time.monotonic()
                await s.raw(ledger, form, {"old": RecordID("task", "hubx")})
                wall = time.monotonic() - t
                after = await s.raw(ledger, "SELECT count() AS n FROM blocks GROUP ALL")
                from_hub = await s.raw(ledger, "SELECT count() AS n FROM blocks WHERE in = $o GROUP ALL",
                                       {"o": RecordID("task", "hubx")})
                into_hub = await s.raw(ledger, "SELECT count() AS n FROM blocks WHERE out = $o GROUP ALL",
                                       {"o": RecordID("task", "hubx")})
                print(f"SET   {name} hub={HUB} noise={noise} before={before} after={after} from_hub={from_hub} "
                      f"into_hub={into_hub} wall={wall:.3f}s", flush=True)
            finally:
                await ledger.close()
                await drop_database(env)


asyncio.run(main())
```

`probe_heal_delete_plan_58.py`:

```python
"""am-17 §9.4: the EXPLAIN plan of the heal's three DELETE forms. A hub with 50 dependents; dependent d00000 also
has a second blocker. TEST store :18000 only."""
import asyncio
import collections
import sys

sys.path.insert(0, "/home/ejprice/PycharmProjects/lore/loremaster/tests")
import _reanchor_58_support as s  # noqa: E402
from _surreal_harness import drop_database, make_env, unique_database  # noqa: E402
from surrealdb import RecordID  # noqa: E402


async def main() -> None:
    env = make_env(database=unique_database(), dim=s.PRODUCTION_DIM)
    assert ":18000" in env.url, "TEST store only"
    ledger = s.new_ledger(env)
    await ledger.ensure_ready()
    try:
        await s.raw_seed_row(ledger, "hubx", blocked_by=[])
        await s.raw_seed_row(ledger, "otherhub", blocked_by=[])
        ids = await s.bulk_seed_dependents(ledger, "hubx", 50, "d")
        await s.raw_relate(ledger, "otherhub", ids[0])
        params = {"i": RecordID("task", "hubx"), "o": RecordID("task", ids[0])}
        for name, text in (
            ("V1", "DELETE blocks WHERE in = $i AND out = $o EXPLAIN"),
            ("V2", "DELETE $i->blocks WHERE out = $o EXPLAIN"),
            ("V3", "DELETE $o<-blocks WHERE in = $i EXPLAIN"),
        ):
            plan = await s.raw(ledger, text, params)
            ops = collections.Counter(
                (node.get("operation"), (node.get("detail") or {}).get("table")) for node in plan
            )
            print(f"{name} {dict(ops)}")
        print("edges after (51 seeded):", await s.raw(ledger, "SELECT count() AS n FROM blocks GROUP ALL"))
    finally:
        await ledger.close()
        await drop_database(env)


asyncio.run(main())
```

No production code, test, registry or store touched by this amendment. No attribution trailer on the commit.

## 10. Follow-up (lead-58, lore_comms #20058): the build ran ahead of the r5.3 grade — keep or revert

**Ruling: A (keep the build), with the six riders in §10.3. B is refused.** Confidence HIGH on the
choice, MEDIUM on rider 3's exact expected-RED membership (the r5.3 author derives it; I have not read the
r5.3 file).

### 10.1 Facts checked (2026-11-09, this tree, `git status` / `git diff --stat` / one text search)

- `loremaster/loremaster/tasks.py` carries the am-17 packer bound
  (`min(_txn_module.TXN_ROW_WARN_THRESHOLD, _txn_module.TXN_ROW_HARD_CAP)` in the heal packer).
- The same file's uncommitted diff is **547 insertions / 68 deletions**: the WHOLE packet-58 build is
  uncommitted, not just the am-17 hunks. The working tree is the only copy of it.
- Not checked by me: the builder's 98/98 claim, and that FREEZE #20052 is unacked (lead's statements).
- The text search was a grep for statement text in one file (a non-symbol textual seam).

### 10.2 Why A

1. **B does not restore what the ordering law protects.** The law's purpose is that the builder never
   builds to an ungraded contract. The builder's context already holds the ungraded legs and its own code;
   reverting the tree and letting the same builder re-apply buys the right ORDER OF TREE STATES and nothing
   else. Only a fresh builder would restore independence, and that is a rebuild of a fully specified
   three-statement change.
2. **B's revert is a hand edit on the only copy of the build** (10.1). A wrong revert damages 547 lines of
   finished, uncommitted work. A needs the same hand reconstruction (isolating the am-17 hunks), but
   performs it as a patch file applied in reverse in a scratch copy, where a wrong patch is detectable
   (rider 3) and harms nothing.
3. **The grade is independent of the build by construction.** §6.3/§9.5's seven wrong builds and the
   reference are the adversary's own, made from the ruling's text. Nothing in the grade reads builder code.
4. **am-17 is a spec to implement** (exact statement forms, exact bound formula), so the routing rule is
   not offended: no property was invented by the builder.

What A leaves unrepaired, stated plainly: the builder saw ungraded legs, so its code may fit their letter.
The instrument for that is the cold audit's contract-blind read of the patch (rider 5), not the grade.

### 10.3 Riders (each is part of the ruling)

1. **Checkpoint first.** Before any agent touches the tree again, the lead commits the current tree as a
   checkpoint (or, if it will not commit ungraded work, takes a `cp -a` content backup and says where).
   Pin: the commit SHA or backup path is in the lead's wave report before rider 2 starts.
2. **The patch is production-only and small.** The builder emits `am17-build.patch` touching
   `loremaster/loremaster/tasks.py` ONLY, containing exactly §7 edits 1, 2, 3 and §9.6 edit 6 (packer bound +
   docstring, heal DELETE + comment, `max_reanchor_dependents` docstring, supersede DELETE + comment).
   Pin: the lead reads the whole patch and its path list; any test, support or schema path in it is a STOP.
3. **Prove the patch is the am-17 delta, both directions, expectations declared first.** In a
   `scripts/scratch_copy.sh` copy (provenance asserted, `loremaster.__file__` printed) with the patch
   reverse-applied: (a) the r5.3 author declares the expected-RED node ids from `--collect-only` BEFORE the
   run (the new r5.3 legs plus the re-keyed legs of §6.1), then runs the am-17 targeted set and diffs both
   ways via `scripts/mutation_proof.py`: an unexpected red, or a declared red that stays green, is a STOP;
   (b) every other test in that set is green, matching the builder's own last pre-am-17 count for the same
   files. Then, patch applied: the whole set green. A leg that is green WITHOUT the patch was never seen
   red and is not a pin; it goes back to the author before the grade.
4. **The adversary's reference is its own.** It implements edits 1/2/6 from this document on the
   minus-patch scratch tree and never reads `am17-build.patch` or the real `tasks.py` hunks. Its SAT
   receipt is against that reference. The grade stays ONE run, seven wrong builds (§9.5); this fork adds
   no property and does not reopen the loop cap.
5. **The cold audit gets the patch as a contract-blind diff target** (withheld: r5.3, the adversary
   report, test runs). Its questions: does each hunk match the ruled form character-for-character in the
   statement, does anything in the patch exist only to satisfy a test's shape (a statement finder, a
   parameter name), and what did the replaced lines do that the new ones do not (the §9.2 inventory is the
   comparator, read AFTER its own enumeration).
6. **Builder re-greens only.** If the grade adds pins, the builder turns them green with production
   edits; it edits no test. Edits 4 (close-out receipt part E at 2,500 and 12,500) and 5 are still owed
   and are unaffected.

### 10.4 Surfaced, not ruled

- **The class behind the fork:** a FREEZE travelled as a directive to a builder that was mid-build and
  did not drain. That is the standing "never steer a busy builder by inbox" hazard, not a builder fault
  peculiar to this wave. The closing rule is at spawn time: a build brief for an amendment names the
  graded contract commit it may start from, so "no graded SHA" means "do not start". Whether to add that
  to lead-base is the operator's call. Do you want a finding filed for it?
- The ordering law was broken once and A does not pretend otherwise; the wave report should say so in
  its deviations.

## 11. Follow-up (lead-58, lore_comms #20072): §0 against §5 on a single over-bound row

**Ruling: §2/§5 stand. WB9 is a wrong build. No code changes** (the build's
`constrained_batches(..., min(WARN, HARD), strict=True)` is the ruled form). §0's reading-B sentence was
written about populations and said more than that; it is reworded in place. Confidence HIGH.

- **The rule, once:** one row whose own `fragment_rows` weight exceeds `min(WARN, HARD)` makes the boot
  fail loud with `StragglerHealPackerError`, `row_cap` = that bound, nothing committed. This holds for a
  weight in `(bound, hard]` exactly as for a weight above the hard cap.
- **Why not WB9 (pack it alone, let `compose` refuse):**
  1. It breaks the pinned property of §6.1, "every heal transaction's `fragment_rows` is at most the
     packer's live bound", for the one input where the bound matters.
  2. A chunk above the bound has no measured safety for this shape. §1's figures above 10,000 rows
     (21 s at 16,000, 229 s at 50,000) are for one-blocker stragglers. A single row that heavy names
     thousands of blockers, and its dependent-anchored DELETEs each walk that row's own in-edges, so its
     cost grows with the square of its blocker count. Not measured; LOW confidence on the size, which is
     the reason to refuse it.
  3. A timeout there is `SurrealOutcomeUnknownError` on every boot, a worse refusal than a typed one
     that names the row.
- **Cost of the ruling, stated:** a task naming between roughly 2,500 and 12,500 superseded blockers is
  now refused where WB9 might have healed it slowly. §5 already names this as the accepted bound.
  Trigger and instrument: any production boot raising `StragglerHealPackerError`; it names `row_id`
  and `weight`, and re-opens this section with that row's shape measured by §INSTRUMENT part E.
- **Pin it like this (MP-1, routed by the adversary as a builder requirement plus cold-audit probe P3;
  this section does not change that routing or reopen the loop cap):** in the WARN-below-hard world
  (800 under 5,000), one straggler weighing more than 800 and at most 5,000 → the boot raises
  `StragglerHealPackerError` with `row_cap == 800`, and the row and its edges are unchanged. Control in
  the same leg: a straggler weighing at most 800 heals. This is the leg WB9 dies on; the existing F10
  monster (5,101, over both bounds) cannot kill it.

## 12. Follow-up (lead-58, lore_comms #20077): cold-audit F1 (#623) — the boot heal writes a `blocked_by` cycle

Sources read: `coldaudit-58.md` (FINDINGS, DECISIONS), `coldaudit-58-ca58-blind.md` F1, am-3 §4/§5,
`tasks.py` (`_reanchor_stragglers`, `_plan_heal_rows`, `_refuse_a_cycle`, `_backfill_blocks_edges`,
`_record_legacy_cycles`, `supersede_task`'s guard), `server.py` (the superseded-blocker claim text).
**No probe run by me**: the defect is the verifier's receipt; the ruling below is design, and every
"pin" in it is unproven until the contract's RED. Confidence: HIGH on the fate and the chokepoint,
MEDIUM on the pending-set detail in 12.2 (reasoned from the code, not executed).

### 12.0 In one screen

| # | question | ruling |
|---|---|---|
| (1) | the straggler whose re-anchor would close a cycle | **Skip the WHOLE row, leave it byte-identical, record a WARNING every boot.** Never a boot denial, never a partial re-anchor. Same posture as am-3 §5's phantom head. |
| (1) | the chokepoint | The cycle PREDICATE inside `_refuse_a_cycle`, extracted so it returns the cycle instead of raising. `_refuse_a_cycle` raises on it; the heal skips on it. No second walk. |
| (2) | round cap | F1 is a new property, so the cap's own exception applies: ONE scoped fix-wave contract, ONE adversary grade, no re-grade. Probes-F1 (OB3) rides along. |
| (3) | the two wording items | Both confirmed as ruling-alignment, in the wave. |

### 12.1 The three lines (fix the class)

- **SHOULDN'T BE DOING:** the boot heal, a second writer of `blocked_by`, writes the column without
  the write path's cycle invariant.
- **OTHER CONSEQUENCES:** (a) the claim text for the row drifts from "can never resolve" to
  "unresolved", which invites polling; (b) the cycle is logged as a successful heal and counted;
  (c) `_refuse_a_cycle`'s docstring ("a legacy loop the backfill has already RECORDED") becomes false
  for a loop the heal made; (d) later boots label it `legacy_cycle_minted`, a cause it does not have.
- **SIMPLEST CLOSING RULE:** a bound at the point of use. Every writer of `blocked_by` passes the
  rows it is about to write through the one predicate. After this section the writers are create,
  create_many, supersede and the heal; the backfill writes edges only, never the column.

### 12.2 The fate, exactly

**Property P (new): after a boot heal, no row the heal wrote lies on a `blocked_by` cycle.**

- **The check is over the heal's whole pending set at once**, not row by row: `pending = {dependent:
  its post-rewrite column}` for every row `_plan_heal_rows` would build, `minted = set(pending)`.
  Two stragglers can close a cycle jointly that neither closes alone (12.4 leg B).
- **Loop:** ask the predicate for a cycle through a pending row. None → done. Otherwise every
  pending row ON that cycle is skipped and recorded, removed from `pending` (its graph entry returns
  to its stored column), and the predicate is asked again. It ends because `pending` shrinks.
- **One graph read per heal** (`_bounded_dependency_graph` over the pending rows' blockers), then the
  loop runs in memory. A skipped row is on a cycle, so it is in that closure and its stored column is
  already in hand. Cost on a healthy store: one extra round trip on a boot that has stragglers, none
  on a boot that has none.
- **A skipped row:** column, edges and `updated_at` untouched; not in `count`; not in any chunk.
- **Record:** WARNING `task.backfill.straggler_would_close_cycle`, extra `database`, `task_id`,
  `blocker_ids` (the superseded blockers it still names), `cycle` (the `a -> b -> …` string the
  backfill's record uses) and `members`. Repeated every boot until the data is repaired. The
  backfill's `legacy_cycle_minted` is NOT emitted for it: no cycle exists in the store.
- **Deliberately stricter than the live supersede, stated so nobody "aligns" it:** am-3 §4 lets a
  live supersede re-anchor a dependent that already sits on a legacy loop through ANOTHER blocker,
  because refusing there makes the superseded task un-supersedable forever. The heal's refusal is
  per row, so that reason does not apply, and such a row is unclaimable on either blocker. The heal
  skips and records it (12.4 leg C). P implies the lead's wording ("never writes a cycle the live
  path refuses") and is simpler to state and to pin.
- **Why not a boot denial:** one legacy row's shape would stop the server for every consumer, which
  am-3 §5 already refused for phantoms. **Why not a partial re-anchor** (move the row's other
  superseded blockers, leave the cyclic one): am-3 §5 skips the whole row, and a half-moved row is a
  third state no render describes.

### 12.3 The chokepoint (builder rider)

- Extract from `_refuse_a_cycle` a non-raising predicate over `(graph, pending, minted)` that returns
  the first cycle a minted row lies on, or `None`, keeping the existing step-over of loops that touch
  no minted row. `_refuse_a_cycle` becomes: read the graph, call it, raise on a cycle. The heal: read
  the graph, call it in 12.2's loop. `find_blocked_by_cycle` and `_drop_one_cycle_edge` stay the only
  detector and the only step-over.
- Correct `_refuse_a_cycle`'s docstring sentence about legacy loops being "already RECORDED" to what
  12.5 item 1 finds true.
- **Prove the sharing by mutation at audit time, as a run** (make the predicate return `None`): the
  live create-cycle pin, the supersede-cycle pin and 12.4 leg A must all redden. A heal leg that stays
  green means a private copy.

### 12.4 Pin it like this (contract author; raw-seeded worlds, each leg names the wrong build it kills)

- **Leg A, the audit's world plus two riders.** X superseded by H with no re-anchor (seeded raw), H
  `blocked_by [D]`, D `blocked_by [X, X2]` where X2 is superseded by a healthy H2, plus one unrelated
  healthy straggler S. Boot → completes; S healed and `count == 1`; D's column and its edges are
  byte-identical; no cycle over all columns (`find_blocked_by_cycle` on a full read); exactly one
  WARNING of the new event naming D with `members` ⊇ {D, H}. Second boot → the same WARNING again.
  Controls in the leg: on the same shape built fresh, the LIVE supersede is refused with
  `TaskCycleError`; and after removing D from H's `blocked_by` by hand, the next boot heals D to
  `[H, H2]` with no WARNING. Kills: no check (today), check-then-write-anyway, raise (boot denial),
  silent skip, partial re-anchor (X2 moved).
- **Leg B, joint.** D1 `[X1]`, D2 `[X2]`, H1 `blocked_by [D2]`, H2 `blocked_by [D1]`. Boot → no
  cycle over all columns; both rows unchanged; both recorded. Kills a row-by-row check, which heals
  both and writes D1 → H1 → D2 → H2 → D1.
- **Leg C, the stricter-than-live fate.** D `blocked_by [X, Z]`, Z `blocked_by [D]`, X superseded by
  a healthy H. Boot → D unchanged and recorded. Kills a build that copies am-3 §4's `minted` choice.
- Values: at least one leg uses a chain of two supersessions (X → X′ → H) so the cycle closes at the
  chain HEAD, not at the first successor.

### 12.5 Bounds and surfaced items (not ruled)

1. **Legacy cycles are recorded only on a boot that has edges to mint** (`_backfill_blocks_edges`
   returns before `_record_legacy_cycles` when nothing is missing). After 12.2 the heal makes no
   cycle, so the mislabel goes away, but a true legacy loop still falls silent after its first boot,
   unlike the phantom record, which repeats. This predates the heal. Recommendation: record on every
   boot (the columns are already read). Do you want that in this wave, or ledgered?
2. **The claim text on a skipped row** says "block on the successor instead" while that successor
   itself waits on this task. True first half, unhelpful second half; the boot WARNING is the only
   place the loop is named. No verb edits `blocked_by`, so repair is by hand in the store.
   Decision point: the count of 12.2 WARNINGs on the first production boot of this build, read by
   the lead. Zero → the bound is theoretical. Non-zero → the render and a repair verb are the
   operator's call.
3. **Production occurrence of the F1 shape is unmeasured** (the audit did not touch :18500, and
   neither may I). If any long-lived store has already booted aa4ea04, it may hold a heal-written
   cycle that this fix will not undo; it would then be recorded as a legacy loop. Has aa4ea04 been
   deployed anywhere?

### 12.6 (2) The round cap

- **Ruling: yes, ONE scoped fix-wave contract, ONE adversary grade, no re-grade.** The operator's
  "r5.3 is the last round" closed the am-17 loop; the tdd cap's stated exception is a new property,
  and P is one that no round has stated. The operator may overturn this reading.
- **Contract scope, exhaustive:** 12.4 legs A–C, and probes-F1's missing pin (a fixture with a drift
  edge out of the hub, so OB3 dies; a new case of am-17 §9.2's pinned property). Nothing else.
- **Grade scope:** SAT on the adversary's own reference; wrong builds = the five named in leg A, the
  row-by-row check, the am-3 §4 `minted` copy, and OB3. Anything it finds missing after that becomes a
  builder requirement plus a cold-audit probe, as r5.3's MP-1/MP-2 did.
- **Why not skip the contract** (builder requirement + audit mutation proofs only): it is a confirmed
  major on a production write path whose first build shipped the defect green through every gate.
- **Cost:** one author run, one adversary run, one builder pass, one delta audit. The packet's one
  full suite runs again at the end of the wave, because the first one graded a NO-GO build.

### 12.7 (3) The two wording items — both confirmed, in the wave

- **F5:** `"… can never resolve, so this claim can never win: block on the successor instead"` →
  `"… can never resolve: block on the successor instead"`. "Can never win" is false for a row
  stranded by a create racing a supersede: the next boot heal re-anchors it. The code comment above
  the text says the same thing in capitals and is corrected with it. Pin: the existing render pin
  re-keys to the new string; grep the test tree for the old phrase first.
- **#130 shape (a):** the `lore_tasks` `status` Field (`server.py`, "exact-status filter" at two
  sites) and the `query_tasks` docstring name that superseded rows are excluded from a status or
  blocked filter. Already ruled (kickoff §5(a)); this only makes the served text say it.

### 12.8 Lead answers to 12.5 (lead-58, 2026-11-10; the operator may overturn each)

1. **Record legacy cycles on every boot: IN this wave.** A true legacy loop going silent after its first boot is a
   quiet failure on a boot path packet 58 reworked, and the columns are already read, so the fix is small. It joins
   the one scoped contract as **leg D**: a raw-seeded legacy `blocked_by` loop with no missing edge. Boot twice; each
   boot records it (`legacy_cycle_minted` or its existing record), and nothing else changes. It kills the
   early-return build at HEAD. Still ONE contract and ONE adversary grade; the grade's wrong builds add the
   early-return-kept build.
2. **The skipped row's claim text and a repair verb: ledgered**, with 12.5's decision point (the count of
   `task.backfill.straggler_would_close_cycle` WARNINGs on the first production boot of this build, read by the
   lead at the packet 65 cutover smoke). Zero means the bound is theoretical; non-zero goes to the operator.
3. **aa4ea04 has not been deployed anywhere long-lived.** The production container `lore-lore` was created
   2026-10-31 21:01 -0400, before packet 58's first build commit (`fa073bc`, 2026-11-09 22:54 -0500), and packet 58
   is commit-only (its DEPLOY rides packet 65). So no store holds a heal-written cycle. HIGH.

## 13. Follow-up (lead-58, lore_comms #20086): #631 — the cycle predicate itself is unsound; §12.2's loop and §12.3 are withdrawn

**Erratum first.** §12.3 told the builder to keep the step-over and called `find_blocked_by_cycle` /
`_drop_one_cycle_edge` "the only detector and the only step-over". That was reasoned from the code and
never executed (§12 said so), and it is wrong: dropping one edge of a legacy loop hides a cycle through
the asked row when the two share that edge (#631, the adversary's store repro on a LIVE supersede).
§12.2's "ask again" loop and §12.3 are replaced by this section. §12.2's fate (skip the whole row,
byte-identical, WARNING every boot), §12.4 legs A–C, §12.5, §12.6 and §12.7 stand.

Sources: `REPORT-adversary-58-fw1.md` (MISSING PINS, DECISIONS NEEDED, Surfaced, `restore_probe.py`),
finding #631, `tasks.py` (`find_blocked_by_cycle`, `_drop_one_cycle_edge`, `_refuse_a_cycle`),
`server.py`'s batch-key call. **Measured by me this time:** §13.1, in memory, instrument pasted in
§INSTRUMENT-3. Not run by me: anything against a store (the adversary's E1–E4 are the store receipts).

### 13.0 In one screen

| # | question | ruling |
|---|---|---|
| D1 | the predicate | A row is refused iff **one of its proposed blockers is in the row's own strongly connected component** of the graph. `networkx.strongly_connected_components`, one pass. No edge dropping. One function, used by create, create_many, supersede and the heal. |
| D1 | R6 | Amended: `find_blocked_by_cycle` stays the detector for the batch-KEY check only. The sentence and the error class stay shared. `_drop_one_cycle_edge` is deleted. |
| D2 | the heal's fate | Neither option offered. **One pass over stored columns PLUS every pending row's proposed column.** Deterministic, no loop, and the only rule measured safe when a chunk fails on its own. "Every pending row in a non-trivial SCC of the overlay", asked once, is unsound (13.1). |
| D3 | routing | Confirmed, with one change: MP-2's "loop until None" requirement disappears, because there is no loop. |
| — | wait for the operator? | No. Proceed. Two things go in the morning report (13.7). |

### 13.1 Measurement (2026-11-10, `probe_cycle_predicate_58.py 4000 58`, in memory, networkx)

Random graphs of 4–7 tasks with a random `superseded_by` map; 2,911 worlds held stragglers. Property G:
for EVERY subset of the kept rows applied (the rest left as stored), no applied row lies on a cycle.

| rule | worlds violating G, all kept rows applied | worlds violating G, some subset applied |
|---|---|---|
| NONE (skip nothing; the control) | 2,271 | 1,858 |
| OV1: non-trivial SCC of the overlay, one pass (the lead's "canonical over-skip") | **891** | 689 |
| OVF: OV1 repeated to a fixpoint | 0 | **122** |
| **U: proposed blocker shares the row's SCC in stored ∪ proposed, one pass** | **0** | **0** |

- OV1 fails because un-skipping a row restores its stored edge, and that edge can close a cycle through
  a row that was kept.
- OVF is sound only if every kept row is written. A heal chunk can be rejected alone (am-3 §2), which
  is the "some subset applied" column.
- U's cost: in 128 worlds it skips a row OVF would heal. Re-running the boot heals all but 6 of those
  worlds; in those, every such row (7 of 7) has a proposed blocker that reaches a permanently skipped
  row, so it is unclaimable either way.
- Live supersede, 4,000 worlds, 2,108 refusals: asking U of the successor alone gives the same answer
  as "the successor lies on a cycle of the overlay" in every world (0 differences).
- Bounds: small graphs, in memory, my own implementation of the rules, not the built code. 13.5 item 4
  runs the same instrument against the built predicate.

### 13.2 D1 — the predicate, exactly (builder rider; the name is the builder's)

One pure function over `(stored, proposed, asked, all_or_nothing)` returning `{row: cycle}`:
1. **Graph.** `all_or_nothing=True`: `stored` with each proposed row's column REPLACING its stored one
   (the write is one transaction). `False`: `stored` PLUS each proposed row's column (a pending row
   keeps its stored edges as well, because it may not be written).
2. **One** `networkx.strongly_connected_components` pass.
3. A row in `asked` is hit iff some blocker `b` in its proposed column is the row itself or is in the
   row's component.
4. Its cycle is the row followed by `networkx.shortest_path(graph, b, row)`, for the first such `b` in
   sorted order; nodes and edges are added sorted so the answer is the same every run. Same list shape
   as today (`[row, …, row]`), so `format_cycle_refusal` is untouched.

| caller | proposed | asked | all_or_nothing | on a hit |
|---|---|---|---|---|
| create | `{id: deps}` | all | True | `raise_cycle_refusal` |
| create_many (persisted ids) | every minted row | all | True | `raise_cycle_refusal` |
| supersede | `{new_id: deps, **rewired}` | `{new_id}` (am-3 §4 stands) | True | `raise_cycle_refusal` |
| heal | every straggler's post-rewrite column | all | False | skip + record each hit row |

- `_refuse_a_cycle` keeps its job (empty-pending short-circuit, the one bounded-closure read, the
  raise) and calls the function. The heal reads the same closure once and calls it once, BEFORE
  `_pack_heal_chunks`. No loop anywhere.
- The closure read is unchanged: seeds are every proposed blocker. A path in the graph leaves a seed
  along stored edges (in the closure) or along a pending row's proposed edge (to another seed).
  Reasoned, MEDIUM; the adversary's E1–E4 on the built tree are its store check.
- `_drop_one_cycle_edge` is deleted.
- **Removed-behaviour inventory** (the adversary's P6b list of six): 1–5 preserved unchanged. 6 splits:
  "a loop touching no asked row never refuses" is PRESERVED by construction and pinned by am-3 §4's
  leg; "accept when no edge can be dropped" is DROPPED (unreachable without the drop loop); the
  step-over's miss on a shared edge is the OLD BUG (#631), not re-pinned.
- The heal's WARNING keeps §12.2's fields. Its `cycle` is a path in stored ∪ proposed, so it can pass
  through another pending row's stored edge: it names the loop the write could close, which is what
  "would close" says.

### 13.3 R6, amended (operator ruling; flagged in 13.7)

- R6's purpose was that one cyclic input is never refused by two detectors with two sentences and two
  error classes. The sentence (`format_cycle_refusal`) and the class (`raise_cycle_refusal`) stay
  single.
- The detector splits by QUESTION: "is there any cycle among these batch keys" stays
  `find_blocked_by_cycle` (`server.py`, unchanged, so no served batch-key string moves); "does this
  row's write close a cycle through persisted rows" is 13.2's function, and nothing else answers it.
- **Sharing proven by mutation, two runs:** 13.2's function returning `{}` → the create, create_many,
  supersede and heal cycle pins all redden; `find_blocked_by_cycle` returning `None` → the batch-key
  pin reddens and the four persisted pins do not.
- Surfaced, not ruled: 13.2's function also answers the batch-key question (all rows asked, nothing
  stored), which would delete `find_blocked_by_cycle` and restore one detector. It can change which
  cycle a multi-cycle batch names, so it touches served strings. Do you want that as a follow-up?

### 13.4 D2 — the heal's fate

**A pending row is skipped iff one of its post-rewrite blockers can reach it through the stored columns
plus every pending row's post-rewrite column.** One pass, so no order exists to depend on (W21's 12/24
split goes away), and MP-2's and MP-3's classes close at the predicate instead of at a loop.

- Why not minimal: it needs the fixpoint, and the fixpoint is unsafe when a chunk is rejected (13.1).
- What it costs, stated: a row can wait one boot for another row to be healed first, and a row whose
  new blocker leads to a permanently skipped row is never healed (it could not be claimed anyway).
  am-16's "one boot heals the whole population" holds for worlds with no such shape, which is every
  world its legs seed.

### 13.5 Pins (contract author: ONE targeted set, no re-grade)

1. **MP-1, as the adversary wrote it:** E1 (heal: X→H, H `[L1]`, L1 `[L2]`, L2 `[L1, D]`, D `[X]` → D
   unchanged and recorded, D on no cycle) and E3 (supersede: R `[X]`, L1 `[L2]`, L2 `[L1, R]`,
   `supersede(X, blocked_by=[L1])` → `TaskCycleError`, nothing written), each with its control, the
   legacy ids sorting first. "On no cycle" is checked by reachability, not by `find_blocked_by_cycle`.
2. **D2, two worlds.** (i) D1 `[X1→H1]`, H1 `[D1, D2]`, D2 `[X2→H2]`, H2 `[D1]`, run under two id
   assignments, one from each of the adversary's two fate classes → both rows skipped and recorded in
   both. Kills minimal and any order-dependent build. (ii) P `[Xp→Hp]`, Hp `[D]`, D `[X→H]`, X
   `blocked_by [P]`, H clean → boot 1: D healed, P unchanged and recorded; boot 2: P healed, no
   WARNING. Kills the overlay rules, and is the pin that stops someone "fixing" the one-boot wait.
3. **R6 re-key:** `test_MUTATION_neutralising_the_SHARED_detector_lets_BOTH_shapes_through` becomes
   13.3's two mutations.
4. **The instrument against the built code (cold audit, a run):** §INSTRUMENT-3 with `rule_u` replaced
   by a call to the built function (`all_or_nothing=False`, all rows asked) → `U` reads 0 / 0 and
   `NONE` reads non-zero. Commit the probe under `scripts/` with the others.
5. §12.4 legs A–C keep their expectations (checked against rule U by hand: A skips D, B skips both,
   C skips D).

### 13.6 D3 — routing, and cost

- **Confirmed:** MP-2 (E4) and MP-3 (E2) are cold-audit probes on the built tree. MP-2's builder
  requirement ("loop until None") is void. MP-3's is "the predicate runs once, before packing".
- **Confirmed:** MP-1 + the D2 pin + the R6 re-key go to the contract author as one targeted set, no
  adversary re-grade (round cap: a security door gets one targeted pin). The cold audit runs E1–E4 and
  13.5 item 4.
- **Scope:** this widens §12.6's "exhaustive" list by the live supersede guard. It is the same
  function, and leaving a caller-reachable cycle write in a build about to be audited is not an option
  I would rule.
- **Cost:** one author run, one builder pass (one function, four call sites, one deletion), no
  adversary run, and the delta audit already planned gains five probes. This is the third pass on the
  cycle class; 13.1 is why I expect it to be the last: the rule was executed against every partial
  outcome before being ruled, which §12.3 was not.

### 13.7 Proceed, and what the operator should see in the morning

Proceed without waiting: the packet is undeployed, every step is a commit that can be reverted, and
the grant covers design forks. Two items the operator may overturn:
1. **R6, an operator ruling, is amended** (13.3): one detector per question instead of one detector.
2. **The heal can take two boots** for a row whose blocker chain passes through another straggler
   (13.4), a deliberate trade for safety under a rejected chunk.
Standing, unchanged: no deploy of this build before the cold audit's GO.

## §INSTRUMENT-3 — `probe_cycle_predicate_58.py`, pasted verbatim (run 2026-11-10 from the repo root: `uv run python <file> 4000 58`)

```python
"""am-17 §13: candidate skip rules for the boot heal, brute-forced in memory (no store).

World: random small `blocked_by` graphs with a random acyclic `superseded_by` map. A straggler is a
row naming a superseded id; its proposed column replaces each superseded id by its chain head.

Rules (which pending rows are SKIPPED):
  U    one pass: skip row r iff some proposed blocker b of r shares r's strongly connected component
       in (stored columns UNION every pending row's proposed column).
  OV1  one pass: skip r iff r is in a non-trivial SCC of the overlay (every pending row applied).
  OVF  OV1 repeated to a fixpoint (skipped rows return to their stored column).

Property G (what "the heal never puts a row it wrote on a cycle" needs once chunks can fail alone):
for EVERY subset A of the kept rows applied (the rest left as stored), no row in A lies on a cycle.
`full` counts violations with A = all kept rows; `partial` with any proper subset.

Control: rule NONE (skip nothing) must show violations, or the checker sees nothing.

Part S: live supersede. exact = "the successor lies on a cycle of the overlay"; union = rule U asked
of the successor only. Counts worlds where they differ.

Run: uv run python <this file> [worlds] [seed]
"""
import itertools
import random
import sys

import networkx


def digraph(columns):
    g = networkx.DiGraph()
    for node, blockers in columns.items():
        g.add_node(node)
        for b in blockers:
            g.add_edge(node, b)
    return g


def on_cycle(g, node):
    if g.has_edge(node, node):
        return True
    return any(node in comp and len(comp) > 1 for comp in networkx.strongly_connected_components(g))


def component_of(g):
    out = {}
    for index, comp in enumerate(networkx.strongly_connected_components(g)):
        for node in comp:
            out[node] = index
    return out


def world(rng, n):
    ids = [f"t{i}" for i in range(n)]
    order = ids[:]
    rng.shuffle(order)
    successor = {}
    for i, old in enumerate(order[:-1]):          # successor always later in `order` => acyclic chains
        if rng.random() < 0.35:
            successor[old] = rng.choice(order[i + 1:])
    stored = {t: [b for b in ids if b != t and rng.random() < 0.28] for t in ids}

    def head(t):
        while t in successor:
            t = successor[t]
        return t

    proposed = {}
    for t, col in stored.items():
        if any(b in successor for b in col):
            proposed[t] = list(dict.fromkeys(head(b) if b in successor else b for b in col))
    return stored, proposed


def rule_none(stored, proposed):
    return set()


def rule_u(stored, proposed):
    union = digraph(stored)
    for r, col in proposed.items():
        for b in col:
            union.add_edge(r, b)
    comp = component_of(union)
    return {r for r, col in proposed.items() if any(b == r or comp[b] == comp[r] for b in col)}


def rule_ov1(stored, proposed):
    g = digraph({**stored, **proposed})
    return {r for r in proposed if on_cycle(g, r)}


def rule_ovf(stored, proposed):
    pending, skipped = dict(proposed), set()
    while True:
        g = digraph({**stored, **pending})
        hit = {r for r in pending if on_cycle(g, r)}
        if not hit:
            return skipped
        skipped |= hit
        for r in hit:
            del pending[r]


def violations(stored, proposed, skipped):
    kept = [r for r in proposed if r not in skipped]
    full = partial = 0
    for size in range(1, len(kept) + 1):
        for applied in itertools.combinations(kept, size):
            g = digraph({**stored, **{r: proposed[r] for r in applied}})
            if any(on_cycle(g, r) for r in applied):
                if size == len(kept):
                    full += 1
                else:
                    partial += 1
    return full, partial


def boots_until_stable(stored, proposed, rule):
    """Re-run the heal (rule + apply all kept) until nothing changes; return rows still skipped."""
    stored, proposed = dict(stored), dict(proposed)
    while True:
        skipped = rule(stored, proposed)
        kept = [r for r in proposed if r not in skipped]
        if not kept:
            return stored, skipped
        for r in kept:
            stored[r] = proposed.pop(r)


def part_heal(rng, worlds):
    rules = {"NONE": rule_none, "U": rule_u, "OV1": rule_ov1, "OVF": rule_ovf}
    bad = {name: [0, 0] for name in rules}
    with_pending = extra_u = extra_u_after_boots = stuck_checked = stuck_ok = 0
    for _ in range(worlds):
        stored, proposed = world(rng, rng.randint(4, 7))
        if not proposed:
            continue
        with_pending += 1
        for name, rule in rules.items():
            full, partial = violations(stored, proposed, rule(stored, proposed))
            bad[name][0] += bool(full)
            bad[name][1] += bool(partial)
        over = rule_u(stored, proposed) - rule_ovf(stored, proposed)
        extra_u += bool(over)
        final, still = boots_until_stable(stored, proposed, rule_u)
        left = over & still
        extra_u_after_boots += bool(left)
        g = digraph(final)
        for r in left:      # claim: a row U never heals is unclaimable anyway under its proposed column
            stuck_checked += 1
            reach = set().union(*(networkx.descendants(g, b) | {b} for b in proposed[r]))
            stuck_ok += bool(reach & still)
    print(f"heal worlds with stragglers: {with_pending}")
    for name, (full, partial) in bad.items():
        print(f"  rule {name:4s} worlds violating G: all-applied={full} partial={partial}")
    print(f"  worlds where U skips a row OVF heals: {extra_u}; still so after repeated boots: {extra_u_after_boots}")
    print(f"  of those rows, proposed blockers reach a permanently skipped row: {stuck_ok}/{stuck_checked}")


def part_supersede(rng, worlds):
    differ = refused = tried = 0
    for _ in range(worlds):
        n = rng.randint(4, 7)
        ids = [f"t{i}" for i in range(n)]
        stored = {t: [b for b in ids if b != t and rng.random() < 0.3] for t in ids}
        old = rng.choice(ids)
        deps = [b for b in ids if b != old and rng.random() < 0.3]
        rewired = {t: ["new" if b == old else b for b in col] for t, col in stored.items() if old in col}
        tried += 1
        exact = on_cycle(digraph({**stored, **rewired, "new": deps}), "new")
        asked_u = "new" in rule_u(stored, {**rewired, "new": deps}) if deps else False
        # rule U asked of the successor only: recompute directly
        union = digraph(stored)
        for r, col in {**rewired, "new": deps}.items():
            for b in col:
                union.add_edge(r, b)
        comp = component_of(union)
        union_says = any(comp[b] == comp["new"] for b in deps)
        assert union_says == asked_u
        refused += exact
        differ += exact != union_says
    print(f"supersede worlds: {tried}; exact refuses {refused}; union differs from exact in {differ}")


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 58
    part_heal(random.Random(seed), count)
    part_supersede(random.Random(seed + 1), count)
```
