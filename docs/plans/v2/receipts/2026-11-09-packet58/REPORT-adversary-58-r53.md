brief-base v27 read · brief project v7 read

# REPORT — adversary-58-r53: packet 58 contract r5.3, the am-17 scoped delta grade (LAST adversary round)


## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT — 2 missing pins, BOTH bucket (b) PINNED PROPERTY, NEW CASE; 0 NEW PROPERTY; 0 SECURITY
  DOOR. The loop cap stays closed** (last round, operator ruling 2026-11-09): MP-1 and MP-2 become builder requirements plus
  cold-audit checks, not a contract round. State: done-with-deviations.
- **P1 headline: all 7 ruled wrong builds (am-17 §9.5) die by the leg the amendment names** (WB1 leg 1 · WB2 leg 3 = r4
  `[tasks.py::ensure_ready -> tasks.py::_reanchor_stragglers]` · WB3 leg 2 · WB4 L3 · WB5 heal plan leg, assertion 1 · WB6
  supersede plan leg, assertion 1 · WB7 heal plan leg, record count). Of my 9 own builds, 6 die and 3 survive the contract,
  each caught only by my probe: **WB9** (an over-bound row packed alone; refusal only above the hard cap) → MP-1 · **WB10** (heal
  DELETE anchored only for a row's first superseded blocker) → MP-2 · WB14b (a decoy + string-spelled supersede scan) → R-3,
  NO ROUND. Re-confirmed against HEAD `99389cd`'s rewritten DELETE legs (§HEAD).
- **SAT (rider 4, own reference from am-17 §2/§3/§9.2; patch body and the real tasks.py hunks unread except one disclosed
  grep line):** 15 files + 3 probes, 717 ids → **716 passed / 1 failed**; the 1 = the registry's declared packet-64b-i id. 0
  r5.3-attributable reds; no over-fire. There is 1 failing test unrelated to our present scope.
- **Spec fork (decision needed):** am-17 §0 ("the hard cap stays the only size at which anything is REFUSED") vs §2/§5
  (`strict=True`; one row over the chunk bound fails the boot loud). They produce different code. I graded on §2/§5. MP-1.
- **Lead's question (builder saw ungraded legs):** the packer-bound legs cannot be fitted by letter (6 bound variants all
  killed). The DELETE legs (by anchor binding) and the F10 leg (monster above both bounds) can be. The cold audit should read for
  `strict=True` at `min(…)`, one uniform heal DELETE comprehension and exactly one supersede DELETE, and run P1–P3 on the
  built tree.
- Deviations: (1) **§INCIDENT: my wrapper ran 4 UNSCOPED pytest runs concurrently for ~6.5 min** (an empty selection file).
  Killed, guarded, re-run scoped; possible TEST-store debris → lead (#486). (2) One unscoped grep printed one am-17 line of
  the real `tasks.py` (§SCRATCH TREES).
- Packages considered: `more_itertools.constrained_batches` 11.1.0 — keep (installed source read; lazy `strict` is safe
  because the list is materialised in the `try`). Diff vs author: no finding.
- Odoo-20 portability: n/a — no Odoo seam touched.
- Reuse ledger: 0 new production symbols; P-PRIOR on r5.3's test symbols: `iterated_records` duplicates `operators()`'s walk
  (R-1, NO ROUND).
- Graded: a77f72e · HEAD-at-report: 99389cd · DIFFERENT (2 ahead: 548fe54 docs, 99389cd r5.3 hygiene). The DELETE legs
  moved; the verdict was re-run there (§HEAD) and holds.
- `loremaster.__file__` receipts: `$S/ref/loremaster/loremaster/__init__.py`; each `$S/wbNN_*/loremaster/loremaster/__init__.py`
  in its run-log header (§SCRATCH TREES). `$S` = `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/a58r53`.
- **COST:** wall ~40 min (≈04:15–04:55Z 2026-11-10). Harness runs: adversary 1 SAT + 16 scoped wrong builds + 10 HEAD
  recheck + 4 aborted unscoped. Fan-out: haiku 10 · sonnet 0 · peak 5.
- Pointers: §P1 table · §P1b · §P1c · §MISSING PINS · §TRIAGE TABLE · §THE LEAD'S QUESTION · §INCIDENT · §HEAD · §INSTRUMENTS.

## ROUTING TABLE (written before the first sweep, 2026-11-09)
| step | tier | who | reason |
|---|---|---|---|
| read am-17, store ref §3/§4, ROUND CAP, r5.3 legs (diff of a77f72e) | 3 | self | the grade rests on them |
| scratch copy of a77f72e + `git apply -R am17-build.patch` | 1 | self, inline | on the critical path, 2 commands, output small and read whole (provenance receipt is mine) |
| reference build (am-17 edits 1/2/6 from the text) | 3 | self | rider 4: the adversary's own reference; judgment |
| 7 wrong builds + my own enumeration builds, one scratch copy each | 3 | self | mutation design is never Haiku |
| `--collect-only` to declare expected reds | 1 | self, inline | output is the declared set I must own before any run; small |
| every pytest run (SAT, minus-patch RED, wrong builds) | 1 | `haiku-runner` | test runs; I read every count line and RAN: line |
| corpse sweep (heal legs still keyed on `TXN_ROW_HARD_CAP` alone; table-anchored `DELETE blocks WHERE` in tests/prod) | 1 | self, one parallel grep batch | 2 literal patterns, output small, read whole; grep is the sanctioned textual-seam case |
| P-PRIOR (walker extension `scans_table` / `iterated_records`) | 3 | self, lore_get_symbol/lore_search | two symbols; judgment on owner fit |
| P-PKG diff | 3 | self | one mechanism (`constrained_batches`) |

| P6b delete-inventory probe + offline heal-shape probe (added mid-run) | 1 | self, inline | short scripts on the critical path; output small, read whole |

Fan-out: haiku 10 (1 SAT · 4 wave-1 runners, aborted per §INCIDENT · 4 relaunch · 1 HEAD recheck) · sonnet 0 · peak 5. Test runs: haiku-runner; every count line and verdict re-read by me from the logs.

## MY OWN WRONG-BUILD ENUMERATION (written before reading REPORT-contract-58-r53.md, 2026-11-09)
Families (am-17 §6.3 item 3 + §9.5): the packer's bound · the heal's edge DELETE · the supersede's edge DELETE.
Required (am-17 §9.5): WB1 packer at hard cap · WB2 packer at WARN, no `min` · WB3 copied 10 000 · WB4 surviving 5 000 ·
WB5 table-anchored heal DELETE kept · WB6 table-anchored supersede DELETE kept · WB7 heal DELETE anchored at the blocker (V2).
Mine:
- WB8 (cosmetic) bound right, `StragglerHealPackerError.row_cap` still the hard cap.
- WB9 (fixture door, F10) a row heavier than the chunk bound but within the hard cap is packed ALONE and healed (refusal
  only above the hard cap, error still typed with `row_cap` = the bound). The only over-weight leg's monster is heavier
  than BOTH bounds, so it may not see where the refusal sits.
- WB10 (quantifier door) heal DELETE dependent-anchored only for a row's FIRST superseded blocker, table-anchored for the
  rest — the heal plan leg's straggler has exactly one superseded blocker.
- WB11 (pair-loose) `DELETE $dep<-blocks` with no WHERE — deletes the live blocker's edge too.
- WB12 (wrong direction, supersede) `DELETE $ssx_old_rec<-blocks` — deletes edges INTO the hub, leaves its own.
- WB13 (both directions, supersede) `DELETE $ssx_old_rec<->blocks`.
- WB14 (letter-fit, supersede) the anchored DELETE emitted AND a table scan spelled through the STRING id param
  `type::record('task', $ssx_old)`, which binds no RecordID so the hook never EXPLAINs it.
- WB15 (off-by-one) `max_size = bound - 1` — P2 arithmetic-alignment check on leg 1/leg 4 fixtures.

## SCRATCH TREES AND PROVENANCE (2026-11-09/10)
- Lead-named dir `…/27ef6c0a-…/scratchpad/a58r53/` (below: `$S`). `base` = `scripts/scratch_copy.sh` of a77f72e, then
  `git apply -R docs/plans/v2/receipts/2026-11-09-packet58/am17-build.patch` (body unread; `--stat`: tasks.py only,
  7+/24−; patch md5 `daa68841…`; tasks.py `ee791e44…` → `3447cd97…`, both equal to the author's figures).
- `ref` = `scratch_copy.sh` of `base`, then am-17 edits 1/2/6 written from am-17 §2, §3, §9.2 (scratch commit `40535c9`;
  delta pasted in §INSTRUMENTS). `loremaster.__file__` = `$S/ref/loremaster/loremaster/__init__.py`.
- 16 wrong-build copies `$S/wb*` = `scratch_copy.sh` of `ref`; each asserted `loremaster.__file__` inside itself
  (`$S/wbNN_…/loremaster/loremaster/__init__.py`, all 16 printed at creation and again in each run log's header).
- **DEVIATION (disclosed):** one sweep grep (`grep -rn 'DELETE … <-{BLOCKS_RELATION}' loremaster/loremaster …`) was not
  scoped away from the REAL tree and printed one am-17 line of the real `tasks.py` (the heal DELETE's first line,
  `DELETE $hd{row_index}_out<-{BLOCKS_RELATION} `). It is the form am-17 §3 prescribes verbatim; my reference was written
  from the amendment and is not derived from it. No other real-tree production line was read; later greps exclude it.

## P-PKG — my table (built before opening the author's), then the diff
| mechanism | library | what I READ | verdict |
|---|---|---|---|
| greedy packing by weight with an over-size refusal | `more_itertools.constrained_batches` 11.1.0 | installed source (`inspect.getsource`): `max_size` inclusive (`item_len + batch_size > max_size` starts a batch); `strict` raises `ValueError` LAZILY, at the oversize item | keep — and the lazy raise is safe only because `_pack_heal_chunks` materialises the whole `list` inside the `try` (pinned: F10 leg's "changes NOTHING" snapshot) |
| EXPLAIN-plan walking (tests) | none (engine JSON) | `_governed_contract.operators` / `scans_table` (lore_search) | reuse; see P-PRIOR |
| the bound | builtin `min` | — | — |
Diff vs author §PACKAGE SURVEY: same mechanisms, same verdicts; the author adds `MonkeyPatch` (agree) and a bespoke `$name`
regex (agree, LOW-MEDIUM as it says). My one addition (lazy strict) is already pinned. **No package finding.**

## P-PRIOR
| new symbol | owner found | verdict |
|---|---|---|
| `_reanchor_58_support.heal_chunk_bound` | production has no accessor (the bound is inline in `_pack_heal_chunks`); lore_search "heal chunk bound min warn threshold hard cap helper" returns only this helper | fine — ruled (am-17 §6.1); legs 1/4 also anchor on the literal `SHRUNK_ROW_WARN_THRESHOLD` / `UNPATCHED_ROW_WARN_THRESHOLD`, so the expectation is not only the code's formula restated |
| `_governed_contract.scans_table` 2nd arm | itself | EXTENDED in place — correct |
| `_governed_contract.iterated_records` | **`_governed_contract.operators(plan)`** already walks every `operation` key (lore_search "walk an EXPLAIN plan tree…", `[SOURCE:loremaster/tests/_governed_contract.py:117]`) → `operators(plan).count("Iterate Record")` | RESIDUAL R-1 (test structure; am-17 §9.4 ruled a sibling, so NO ROUND). The author's DRY row "nothing counts `Iterate Record`" is literally true but `operators` is the walker |
| `_ExplainBeforeTheWrite` | `_reanchor_58_support.ApplyHook` (author's row) | agree HAND-ROLLED — ApplyHook fires once with no fragments |

## P-PORT
Odoo-20 portability: n/a — no Odoo seam touched (lore repo; my own seam list over r5.3's tests and fixtures: 0 Odoo seams).

## P6 — corpse sweep (grep, sanctioned textual seam; coverage: 64 files under loremaster/ name `blocks`/`BLOCKS_RELATION`)
Pattern 1 `DELETE {BLOCKS_RELATION} WHERE|DELETE blocks WHERE|<-{BLOCKS_RELATION}|->{BLOCKS_RELATION}` over tests + scripts
(probe_* excluded), each hit:
- `_reanchor_58_support.py` `raw_relate` (`RELATE $from->…->$to`) — seeding, not a DELETE: **not a corpse**.
- `test_reanchor_58_r53_bound_and_plans.py` `_assert_the_walker_sees_a_table_scan` (`DELETE … WHERE in = $…`) — the C+
  control, deliberately table-anchored: **not a corpse**.
- same file, heal leg `DELETE $old->… WHERE out = $dependent EXPLAIN` — the V2 count control: **not a corpse**.
- `scripts/cycle_coexisting_legacy_soundness_probe.py` / `scripts/coldaudit_cycle_04b3_fork_a_refute.py` `RELATE` — seeding
  probes: **not a corpse**.
- No test asserts the retired statement text. **0 corpses.**
Pattern 2 `TXN_ROW_HARD_CAP` in `test_reanchor_58_*.py` (minus setattr/UNPATCHED/SHRUNK lines), each hit:
- `r2_rulings.py` K-accessor leg `cap = (_txn.TXN_ROW_HARD_CAP - fixed) // per` — the SUPERSEDE hub cap, which am-17 §4
  leaves on the hard cap: **correct, not a corpse**.
- `r2_probes.py` `max_reanchor_dependents(k) == (_txn.TXN_ROW_HARD_CAP - fixed) // per` — same: **correct**.
- `r2_rulings.py` door-world precondition, `r4_state.py` precondition — the ruled leg-3 worlds: **correct**.
- `r3_convergence.py` / r53 file docstrings and one failure message — prose: **correct**.
- Off-tree: `scripts/probe_heal_curve_58.py` part E's `_HEAL_DELETE` regex matches the RETIRED V1 text, so on the built
  tree part E's "swap V3 in" is a silent no-op (a probe, not a test; it still measures the real heal). RESIDUAL R-2.

## P6b — removed-behaviour inventory (my enumeration from the pre-am-17 source, BEFORE reading am-17 §9.2's)
Old heal DELETE `DELETE blocks WHERE in = $old AND out = $dep`, one per superseded blocker of the row: (a) deletes every
edge of that pair, duplicates included; (b) deletes no other edge into `dep`; (c) a pair with no edge deletes nothing, no
error; (d) params `hd{r}_out`, `hd{r}_{i}_in` as RecordIDs (weights unchanged). Old supersede DELETE `DELETE blocks WHERE
in = $old`: (e) deletes every outgoing edge of `old`, duplicates included; (f) deletes no edge INTO `old`; (g) one
statement, same fragment position (`fixed`/`per` unchanged). Old packer: (h) bound = hard cap; (i) `row_cap` = hard cap;
(j) `strict=True`, whole list materialised before any apply.
Probe `probe_delete_inventory.py` (TEST store, §INSTRUMENTS) — duplicate pairs `old→dep`×2, `old→dep2`×2, plus `live→dep`:
| form | after |
|---|---|
| heal V1 (old) | `live→dep`, `old→dep2`×2 |
| heal V3 (am-17) | `live→dep`, `old→dep2`×2 — identical (a)(b) |
| sup T (old) | `live→dep` |
| sup G (am-17) | `live→dep` — identical (e)(f) |
Dangling-edge cell DROPPED, with the reason: constructing it FAILED — `RELATE $old->blocks->task:ghost` is refused (`The
record 'task:ghost' does not exist`), so no door writes one. (c): every r5.3 heal and supersede leg runs worlds where an
edge exists; (c) is unchanged by construction (a WHERE over an empty traversal deletes nothing). (d)(g): weights unchanged —
r5.3 legs 1/2/4 measure `fixed`/`per` at compose and stay green on my reference (SAT). (h)(i) replaced as ruled; (j) kept.
Diff vs am-17 §9.2's inventory (read after): §9.2 lists (e), (f) and duplicates "not separately measured … spec-silent" —
**now measured: both forms remove all duplicates**. It does not inventory the heal DELETE (a)–(c) separately; my probe
covers (a)(b). No inventory item I could not ground. **No P6b finding.**

## ⚠ INCIDENT (2026-11-10 ~04:31–04:38Z): four UNSCOPED pytest runs — my wrapper's defect, caught and killed
- What ran: wave 1 launched WB01, WB05, WB09, WB13 concurrently (one per haiku-runner). Each ran
  `pytest -q -n 3 --timeout=300 -p no:cacheprovider` with **no node ids**, so each collected the whole configured
  testpaths. That is four concurrent full-suite-scope runs (12 xdist workers), against the binding TEST SCOPE (targeted
  only; one full suite fleet-wide, under the flock). Each ran under its own `MemoryMax=16G` cgroup. None reached a result.
- Found at ~6.5 min because the 2-test WB05 had not finished; `/proc/<pid>/cmdline` showed the empty selection. I stopped
  the four runners (TaskStop) and SIGTERMed the pytest trees; 0 processes remained.
- Cause: my declaration helper truncated `<build>.select` but appended the ids to `<build>.$mode` with `mode=sel`, i.e. to
  `<build>.sel`. The `.red` declarations were unaffected. Fix: rename `.sel` → `.select` (46 ids over 16 builds; the
  content was written at the same 04:30:58Z declaration time, so the declarations still predate every run) **plus a guard
  in `run_wb.sh` that refuses an empty selection or declaration** (positive control: an empty `.select` → `REFUSED …`,
  exit 3). This is the "if step N silently no-ops, does step N+1 still look like success?" class: an empty pytest
  selection does not fail, it widens to everything.
- Collateral: the stop killed mutation_proof before its restore, so 4 copies were left mutated. Restored with
  `git checkout -- tasks.py` in each SCRATCH copy (scratch git; HEAD `40535c9` = ref). All 17 trees then md5
  `c6378f09…` = ref. The aborted logs are kept in `$S/logs/aborted-unscoped/` (headers only).
- **Possible TEST-store debris:** the killed runs may have left `test_<pid>_<uuid>` databases on `:18000` that their
  teardown never reaped (#486 class). I did not enumerate the store. Lead: a stray-wipe per #486 D2 may be due.
- The SAT run (separate wrapper, explicit file list) was not affected.

## REFERENCE / SAT RECEIPT (graded commit a77f72e's tests on my reference, 2026-11-10)
- Set (`$S/sat_set.txt`, 15 files, 714 ids from `--collect-only`): the author's 11-file am-17 set (438 ids, which matches
  its claim) plus `test_supersede_render_58.py` (a walker caller), `test_task_ledger.py` (supersede),
  `test_reanchor_58_r5_rows.py`, `test_reanchor_58_r3_relate.py` (heal). Plus my 3 probes. lore_impact gave 0 covering
  tests for `_pack_heal_chunks` / `_supersede_transaction` (#563, indirect coverage not traced), so the files were added by
  hand with grep for walker callers. Said here as the brief requires.
- Declared before the run: the one registry-owned red (`pending_contracts.yaml`, packet-64b-i):
  `test_reanchor_58_r4_state.py::…[findings.py::_run_guarded -> findings.py::_run_guarded]`.
- `logs/a77f72e/sat-ref.log` (TREE `0bd93f0e…` family; header in log): **716 passed / 1 failed, 104 s, EXIT=1**. The 1 =
  the declared 64b-i id (`TypeError: FindingLedger.report() got an unexpected keyword argument 'title'`, raised from
  `test_findings_cas_seam_64b.py`). **0 r5.3-attributable reds; every r5.3 leg, every re-keyed leg and P1–P3 GREEN on the
  reference.** No over-fire.
- That one red is outside this grade's scope and owned by packet-64b-i in the registry. There is 1 failing test unrelated
  to our present scope.

## P1 — THE WRONG BUILDS (graded commit a77f72e; each in its own scratch copy; reds declared 04:30:58Z before any run)
Instrument: `scripts/mutation_proof.py` (exactly-once anchor, both-way diff against the declared set, byte-exact restore)
inside `$S/run_wb.sh`. Every row below: `mutation LANDED` ×1, its own `loremaster.__file__`, **PROOF HELD** (observed reds
== declared reds), restore md5 `c6378f09…` = ref. Logs `$S/logs/a77f72e/<build>.log`.
| # | wrong build | selection → count | killed by | verdict |
|---|---|---|---|---|
| WB1 | packer at the hard cap | 5 → 4 failed / 1 passed | leg 1 (`[1604]` vs 3 chunks), leg 2, leg 4 (`[10004]`), + P3; L3 green as predicted | **KILLED** (am-17: leg 1 ✓) |
| WB2 | packer at WARN, no `min` | 7 → 4 failed / 3 passed | r4 `[tasks.py::ensure_ready -> tasks.py::_reanchor_stragglers]` + door ×3 (`TxnRowCapExceededError: 36 rows, over the 16-row cap`); legs 1/2/4 green as predicted | **KILLED** (leg 3 ✓) |
| WB3 | copied 10 000 (`min(10_000, HARD)`) | 3 → 2 failed / 1 passed | leg 2 (boot A `[804]`), leg 1; leg 4 green as predicted | **KILLED** (leg 2 ✓) |
| WB4 | surviving 5 000 (`min(WARN, HARD, 5_000)`) | 4 → 2 failed / 2 passed | L3 (`[5000, 4]`), leg 4 (`[5000, 5000, 4]`) | **KILLED** (L3 ✓) |
| WB5 | heal DELETE table-anchored (V1) | 2 → 1 failed / 1 passed | heal plan leg, assertion 1 (`Iterate Table blocks`) | **KILLED** ✓ |
| WB6 | supersede DELETE table-anchored (T) | 2 → 1 failed / 1 passed | supersede plan leg, assertion 1 | **KILLED** ✓ |
| WB7 | heal DELETE blocker-anchored (V2) | 2 → 1 failed / 1 passed | heal plan leg, record count (`7 == 2`) | **KILLED** ✓ |
| WB8 | bound right, packer error `row_cap` = hard cap | 2 → 1 failed / 1 passed | F10 leg (`row_cap 5000` vs derived 800) | KILLED |
| **WB9** | over-bound row packed ALONE; refusal only above the hard cap (typed, `row_cap`=bound) | 6 → 1 failed / 5 passed | **only my P3** (`DID NOT RAISE StragglerHealPackerError`); F10, legs 1/2/4, L3 all GREEN | **SURVIVES the contract** |
| **WB10** | heal DELETE dependent-anchored for a row's FIRST superseded blocker, V1 for the rest | 4 → 1 failed / 3 passed | **only my P1** (`['DELETE blocks WHERE in = $hd0_1_in AND out = $hd0_out']`); heal leg, supersede leg, PC GREEN | **SURVIVES the contract** |
| WB11 | heal `DELETE $dep<-blocks` (no WHERE, pair-loose) | 1 → 1 failed | heal leg non-vacuity (`found []`) | KILLED |
| WB12 | supersede `DELETE $old<-blocks` (wrong direction) | 1 → 1 failed | supersede leg count (`1 == 5`) | KILLED |
| WB13 | supersede `DELETE $old<->blocks` | 1 → 1 failed | supersede leg count (`6 == 5`) | KILLED |
| WB14a | supersede scan spelled via the STRING id only | 1 → 1 failed | supersede leg non-vacuity (`found []`) — fails closed | KILLED |
| **WB14b** | anchored DELETE + a second, string-spelled table scan | 2 → 1 failed / 1 passed | **only my P2** (`["DELETE blocks WHERE in = type::record('task', $ssx_old)"]`); supersede leg GREEN | **SURVIVES the contract** |
| WB15 | bound − 1 (off-by-one) | 3 → 3 failed | legs 1, 2, 4 (`[9996, 8]` vs `[10000, 4]`) | KILLED |
**All seven ruled wrong builds (am-17 §9.5) die by the leg the amendment names.** Of my nine, six die; three survive
(WB9, WB10, WB14b), each caught only by my own probe, and each probe is GREEN on the reference (SAT): the positive-control pair.
P2 (fixture arithmetic) on the bound legs: offline shape `fixed=0, per=4` gives remainder 0 at 800 / 5 000 / 10 000, so an
off-by-one changes `fit`. WB15 confirms legs 1/2/4 discriminate ±1. Leg 4's 2 501 stragglers sit exactly one past a full
10 000-row chunk; WB4 shows L3 + leg 4 separate 5 000 from 10 000.

## P1b — QUANTIFIER TABLE
| invariant | ∀ / guarded | receipt |
|---|---|---|
| I1 every heal chunk ≤ `min(WARN, HARD)` | ∀ over the generated populations (convergence), both orderings (shrunk WARN<HARD; r4/door HARD<WARN), real constants (leg 4, L3) | WB1/2/3/4/15 killed |
| I2 chunk count = the greedy packer's | ∀ (same domain) | WB1, WB15 killed |
| I3 both constants read live | ∀ over the two constants (leg 2 WARN; shrink fixtures HARD) | WB3 killed |
| I4 a single row over the chunk bound fails the boot LOUD, typed, `row_cap` = bound, nothing changes | **GUARDED by the fixture**: the only monster (weight 5 101) is over the bound AND the hard cap (5 000) | **WB9 SURVIVES** — door: weight in (bound, hard] |
| I5 no heal DELETE iterates `blocks` | **GUARDED**: one straggler with ONE superseded blocker; the statement located by binding both anchors | **WB10 SURVIVES** — door: a row naming ≥2 superseded blockers |
| I6 the heal DELETE is pair-exact | ∀ over the leg's world (edge mirror) | WB11 killed |
| I7 no supersede DELETE iterates `blocks` | **GUARDED**: the one statement binding the hub's RecordID | WB14a killed (fails closed); **WB14b SURVIVES** (a second statement not binding it) |
| I8 the supersede DELETE removes exactly the hub's outgoing edges | ∀ over the leg's world (count + existing mirror legs) | WB12, WB13 killed |

## P1c — ENFORCEMENT TABLE (legs: empirical = a wrong build run; inspection = read only)
| rule | ONE chokepoint | effect vs proxy | removal / move-after | sharing by mutation | spelling test? |
|---|---|---|---|---|---|
| chunk bound | `TaskLedger._pack_heal_chunks` | EFFECT (ComposeSpy rows = what is sent) | removal = WB1 red (empirical); move-after n/a (sizing, not a guard before a body) | the `_txn` constants: WARN shrunk in-test (leg 2), HARD shrunk (r4/door) reddened WB2/WB3 (empirical) | no |
| over-bound row refusal | same, `strict=True` at `min(…)` | EFFECT, but only for weight > hard | WB9 (refusal moved to the hard cap) GREEN → **MISSING PIN** (empirical) | — | no |
| heal DELETE anchored | `TaskLedger._plan_heal_rows` | the engine's plan (EXPLAIN) — a deterministic cost witness ruled by am-17 §9.4, plus the edge mirror for the set | WB5 red; partial WB10 GREEN → **MISSING PIN** (empirical) | — | no: statements are found by bound PARAMETER values in the composed transaction (runtime data, not source) |
| supersede DELETE anchored | `TaskLedger._supersede_transaction` | same | WB6 red; WB14b GREEN (residual R-3) | — | no |
| walker `scans_table` (shared, test side) | `_governed_contract.scans_table` | C+ controls in both legs fire on live 3.3.5 shapes (both arms) | — | inspection only: a SELECT plan cannot match the `operation`/`detail` arm; the author's §GC before/after run (0 changed outcomes over 5 591 nodes) was not re-run by me | no |

## MISSING PINS (both bucket (b) PINNED PROPERTY, NEW CASE — the loop stays closed)
**MP-1 (WB9) — the over-bound-row refusal is pinned only above the hard cap.**
- *Test that should exist:* the F10 leg's sibling, under the shrunk caps: ONE straggler whose own weight is above
  `heal_chunk_bound()` and at most `TXN_ROW_HARD_CAP` (400 superseded blockers: weight 1 201 vs 800 / 5 000) → both boots
  raise `StragglerHealPackerError` with `row_id`, the derived `weight` and `row_cap == heal_chunk_bound()`, and the snapshot is
  unchanged. My P3 (§INSTRUMENTS) is that leg minus the second boot and the snapshot.
- *Defect it catches:* a packer that lets compose be the refusal (`strict=False`, or "pack an over-bound row alone"). It
  heals a single row in one transaction of up to 50 000 rows (~230 s on am-17 §1.2's curve). That is the timeout class
  am-17 exists to close, where the ruling says the boot fails loud (am-17 §2 "`strict=True` stays", §5 named bound).
- CLASS: a single row's refusal threshold is the packer's chunk bound, not the compose cap. CHOKEPOINT:
  `_pack_heal_chunks` (`constrained_batches(built, min(WARN, HARD), get_len=…, strict=True)`).
  SIBLINGS TRIED: WB8 (`row_cap` reported as the hard cap) killed; WB9 survived. SIBLINGS NOT TRIED: a refusal threshold at
  some other value between bound and cap; the same door at the real constants (weight in (10 000, 50 000]) — slow fixture.
- **⚠ SPEC FORK (decision for the sidecar/operator; brief-base §2):** am-17 §0 reading-B says *"The hard cap stays the only
  size at which anything is REFUSED; a chunk target below it refuses nothing (the same stragglers heal, in more
  transactions)."* Read for a single row, that sentence makes WB9 the CORRECT build. §2 (`strict=True` stays) and §5 (*"ONE
  row whose own weight exceeds the chunk bound makes `constrained_batches` raise … drops from 50,000 rows to 10,000"*)
  make my reference correct. I graded against §2/§5 (they are the specific rulings; §0's sentence is about populations).
  The two readings produce different code. Recommendation: confirm §5, and reword §0's sentence to "no POPULATION is
  refused below the hard cap".
- Bucket **(b)**: an implementation requirement for the builder's re-green pass (keep `strict=True` at `min(…)`; never let
  compose be the single-row refusal), named for the cold audit (read the hunk; run P3 on the built tree). Not `REPEAT CLASS`
  (the door opened only when am-17 separated the bound from the cap).

**MP-2 (WB10) — "no heal DELETE iterates `blocks`" is pinned for a row with ONE superseded blocker only.**
- *Test that should exist:* the heal plan leg over a straggler naming TWO superseded blockers: EXPLAIN **every** DELETE the
  heal transaction sends for it; none iterates `blocks`; each `Iterate Record` count == the straggler's own blocker count.
  My P1 is that leg. The same ∀-over-the-transaction form for the supersede (my P2) also closes R-3.
- *Defect it catches:* the table scan kept for any blocker index past the first: the quadratic boot cost am-17 §1.1
  measured, on every multi-superseded straggler.
- CLASS: am-17 §9.3's class statement ("no statement a task verb or the boot heal sends iterates the whole `blocks`
  table"), pinned as "the one statement that binds these anchors". CHOKEPOINT: the DELETE comprehension in
  `_plan_heal_rows` (and the DELETE fragment in `_supersede_transaction`). SIBLINGS TRIED: WB5, WB7, WB11 (heal) killed;
  WB14a killed, WB14b survived (supersede). SIBLINGS NOT TRIED: a table scan in a NON-DELETE statement inside these
  transactions (P1/P2 EXPLAIN only DELETEs; a class-level pin over every statement would have to exempt the backfill's
  ruled `SELECT … FROM blocks`).
- Plausibility LOW (a per-index partial inside one comprehension). Bucket **(b)**: an implementation requirement (one uniform
  comprehension for every superseded blocker of the row), named for the cold audit (P1 on the built tree).

## TRIAGE TABLE (this is the LAST adversary round — operator ruling 2026-11-09)
| finding | bucket | goes to |
|---|---|---|
| MP-1 WB9 over-bound row refusal | (b) PINNED PROPERTY, NEW CASE | builder requirement + cold audit (P3); spec fork → sidecar/operator |
| MP-2 WB10 multi-superseded heal DELETE | (b) PINNED PROPERTY, NEW CASE | builder requirement + cold audit (P1) |
| R-3 WB14b decoy + string-spelled supersede scan | (c) NO ROUND — not a plausible honest build; consequence ~1 s per supersede at 200 000 edges (am-17 §8 item 2) | cold audit's rider-5 question ("does anything exist only to satisfy a test's shape") + P2 |
| R-1 `iterated_records` re-walks what `operators()` walks | (c) NO ROUND (test structure) | close-out |
| R-2 `probe_heal_curve_58.py` part E regex keys on the retired V1 text (the V3 swap is a silent no-op on the built tree) | (c) NO ROUND (a probe) | close-out; the r5.3 author's probe commit |
| R-4 my incident: possible TEST-store debris from 4 killed runs | (c) NO ROUND (hygiene) | lead: #486 stray wipe |
| SECURITY DOOR | none — no caller-reachable access, entitlement or validation path is touched | — |
| NEW PROPERTY | **none** | — |

## THE LEAD'S QUESTION — does r5.3 still discriminate, given the builder saw the in-progress legs (am-17 §10.2)?
- **The packer-bound legs cannot be fitted by letter.** They assert exact chunk-row lists measured off `compose` in four
  worlds (WARN<HARD shrunk, WARN shrunk live, HARD<WARN, real constants). Six distinct bound variants were all killed
  (WB1/2/3/4/8/15). Only the ruled `min(WARN, HARD)` read live satisfies them.
- **Two families have a letter a wrong build can satisfy:** (1) the DELETE legs certify the statement that binds the anchor
  RecordID(s), not every DELETE the transaction sends. WB10 (row shape) and WB14b (a second, string-spelled statement)
  pass. (2) The F10 leg certifies refusal only for a row over the hard cap (WB9). A builder who read the legs could land in
  either without meaning to (WB9 especially: am-17 §0's sentence points there).
- **So the cold audit's contract-blind read of the patch (rider 5) should check, in addition to its own questions:**
  `strict=True` kept at `max_size = min(…)`; the heal DELETE comprehension uniform for every `i`; exactly ONE DELETE
  statement in the supersede's DELETE fragment, anchored on `$ssx_old_rec`. It should also run P1–P3 (pasted below) on
  the built tree, so neither the grade nor the builder grades the build.

## RUNS USED (2026-11-10)
- 1 × SAT on the reference: 15 files + 3 probes, 717 ids, `-n 8`, 104 s → 716 / 1 (declared 64b-i).
- 16 × scoped wrong-build runs (`-n 3`, 1–7 ids each, 2–32 s each) → table above.
- 4 × ABORTED unscoped runs (§INCIDENT), ~6.5 min each, no result, killed.
- HEAD recheck (§HEAD): 1 reference run (r5.3 file + probes) + 9 DELETE-family builds.
- Non-pytest: 2 × `--collect-only`; 1 offline shape probe; 3 × `probe_delete_inventory.py` (2 failed on construction:
  `task:ghost` refused).
- Full contract tag set: run once (the SAT), as the brief allows. No full suite (the 4 aborted runs were an accident, not a
  choice).

## §INSTRUMENTS (pasted verbatim; scratch only, never in the repo)

### Reference delta (`$S/ref`, scratch commit 40535c9 over the minus-patch base d5ec901)
```diff
diff --git a/loremaster/loremaster/tasks.py b/loremaster/loremaster/tasks.py
index 5b03da2..3c03e7b 100644
--- a/loremaster/loremaster/tasks.py
+++ b/loremaster/loremaster/tasks.py
@@ -2287,7 +2287,8 @@ class TaskLedger:
         fragments = [TaskLedger._supersede_fragment(old_id, new_id, content, event)]
         fragments.append(
             TxnFragment(
-                statements=[f"DELETE {BLOCKS_RELATION} WHERE in = $ssx_old_rec"],
+                # `blocks` has no index — a table-anchored DELETE iterates the whole table; am-17 §9
+                statements=[f"DELETE $ssx_old_rec->{BLOCKS_RELATION}"],
                 params={"ssx_old_rec": RecordID(TASK_TABLE, old_id), "ssx_old": old_id},
             )
         )
@@ -2459,8 +2460,9 @@ class TaskLedger:
             fragments = [
                 TxnFragment(
                     statements=[
-                        f"DELETE {BLOCKS_RELATION} WHERE in = $hd{row_index}_{i}_in "
-                        f"AND out = $hd{row_index}_out"
+                        # `blocks` has no index: a table-anchored DELETE scans it once per straggler —
+                        # am-17 §3 (probe: scripts/probe_heal_curve_58.py)
+                        f"DELETE $hd{row_index}_out<-{BLOCKS_RELATION} WHERE in = $hd{row_index}_{i}_in"
                         for i in range(len(olds))
                     ],
                     params={
@@ -2481,8 +2483,10 @@ class TaskLedger:
     def _pack_heal_chunks(
         built: Sequence[tuple[str, list[TxnFragment], list[tuple[str, str]], int]],
     ) -> list[list[tuple[str, list[TxnFragment], list[tuple[str, str]], int]]]:
-        """Greedy chunks sized by each row's OWN composed cost against the live row cap."""
-        cap = _txn_module.TXN_ROW_HARD_CAP
+        """Greedy chunks sized by each row's OWN composed cost against ``min(TXN_ROW_WARN_THRESHOLD,
+        TXN_ROW_HARD_CAP)``, both read live (am-17 §2: the WARN threshold by ruling; 7.25 s per full chunk
+        measured; re-open trigger am-17 §5)."""
+        cap = min(_txn_module.TXN_ROW_WARN_THRESHOLD, _txn_module.TXN_ROW_HARD_CAP)
         try:
             return [
                 list(batch)
```

### `probes/test_adv_r53_probes.py`
```python
"""adversary-58-r53 positive-control probes (SCRATCH ONLY — never in the repo; pasted verbatim in
REPORT-adversary-58-r53.md §INSTRUMENTS).

Three doors the r5.3 contract's legs do not cover, each run on the adversary's REFERENCE (must be green) and on the
wrong build that walks through it (must be red):

* P1 (WB10): every DELETE a heal transaction sends — not only the one statement binding both a dependent's and ONE
  superseded blocker's RecordID — iterates no ``blocks`` table, for a straggler naming TWO superseded blockers.
* P2 (WB14b): every DELETE the supersede transaction sends iterates no ``blocks`` table (am-17 §9.3's class
  statement, over the whole transaction, not over the one statement that binds the hub's RecordID).
* P3 (WB9): a single row whose weight is ABOVE the chunk bound but WITHIN the hard cap fails the boot LOUD with the
  typed packer error, ``row_cap`` = the chunk bound (am-17 §2 ``strict=True`` stays; §5's named bound).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

import pytest
from _governed_contract import scans_table
from _reanchor_58_support import (
    CREATOR,
    DESCRIPTION,
    SHRUNK_ROW_HARD_CAP,
    SHRUNK_ROW_WARN_THRESHOLD,
    boot,
    bulk_seed_dependents,
    column,
    create,
    ledger58,
    new_ledger,
    raw,
    raw_relate,
    raw_seed_row,
    shrunk_row_caps,
    supersede,
)
from _surreal_harness import SurrealEnv
from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE
from loremaster.tasks import StragglerHealPackerError, TaskLedger
from surrealdb import RecordID

__all__ = ["ledger58", "shrunk_row_caps"]

_PARAMETER_REFERENCE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


class _ExplainEveryDelete:
    """Wrap ONE ledger's write door: EXPLAIN every DELETE statement of every transaction over the pre-write world (on a
    second connection), then let the write through."""

    def __init__(self, ledger: Any, explainer: TaskLedger) -> None:
        self._ledger = ledger
        self._explainer = explainer
        self._original = ledger._apply  # noqa: SLF001
        self.plans: list[tuple[str, Any]] = []

    async def __call__(self, fragments: Any) -> Any:
        merged: dict[str, Any] = {}
        for fragment in fragments:
            merged.update(fragment.params)
        for fragment in fragments:
            for statement in fragment.statements:
                if statement.lstrip().upper().startswith("DELETE"):
                    params = {n: merged[n] for n in _PARAMETER_REFERENCE.findall(statement) if n in merged}
                    self.plans.append((statement, await raw(self._explainer, f"{statement} EXPLAIN", params)))
        return await self._original(fragments)

    def install(self) -> None:
        self._ledger._apply = self  # noqa: SLF001

    def restore(self) -> None:
        self._ledger._apply = self._original  # noqa: SLF001


async def _unrelated_edges(ledger: TaskLedger, tag: str) -> None:
    noise = await create(ledger, f"{tag} unrelated blocker")
    await bulk_seed_dependents(ledger, noise, 25, tag=f"{tag}n")


async def test_P1_every_heal_DELETE_for_a_TWO_superseded_blocker_straggler_iterates_no_table(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, env = ledger58
    head = await create(ledger, "p1 head")
    olds = ["p1legacyaaaaaaaaaaaaaaaaaaaaaa01", "p1legacyaaaaaaaaaaaaaaaaaaaaaa02"]
    for old in olds:
        await raw_seed_row(ledger, old, blocked_by=[], superseded_by=head)
    target = "p1targetaaaaaaaaaaaaaaaaaaaaaa01"
    await raw_seed_row(ledger, target, blocked_by=list(olds))
    for old in olds:
        await raw_relate(ledger, old, target)
    await _unrelated_edges(ledger, "p1")
    booted, explainer = new_ledger(env), new_ledger(env)
    try:
        hook = _ExplainEveryDelete(booted, explainer)
        hook.install()
        await booted.ensure_ready()
        assert len(hook.plans) >= len(olds), f"non-vacuity: the heal sent {len(hook.plans)} DELETEs"
        scanning = [statement for statement, plan in hook.plans if scans_table(plan, BLOCKS_RELATION)]
        assert scanning == [], f"heal DELETEs iterating the whole {BLOCKS_RELATION} table: {scanning}"
        assert await column(ledger, target) == [head]
    finally:
        await booted.close()
        await explainer.close()


async def test_P2_every_supersede_DELETE_iterates_no_table(ledger58: tuple[TaskLedger, SurrealEnv]) -> None:
    ledger, env = ledger58
    hub = await create(ledger, "p2 hub")
    await bulk_seed_dependents(ledger, hub, 5, tag="p2d")
    await _unrelated_edges(ledger, "p2")
    explainer = new_ledger(env)
    try:
        hook = _ExplainEveryDelete(ledger, explainer)
        hook.install()
        try:
            await supersede(ledger, hub)
        finally:
            hook.restore()
        assert hook.plans, "non-vacuity: the supersede sent no DELETE"
        scanning = [statement for statement, plan in hook.plans if scans_table(plan, BLOCKS_RELATION)]
        assert scanning == [], f"supersede DELETEs iterating the whole {BLOCKS_RELATION} table: {scanning}"
    finally:
        await explainer.close()


@pytest.mark.usefixtures("shrunk_row_caps")
async def test_P3_a_row_above_the_chunk_bound_but_within_the_hard_cap_fails_the_boot_LOUD(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, env = ledger58
    entries = 400  # weight 4·400 + 1 = 1 201: above the 800 bound, within the 5 000 hard cap (offline-measured)
    head = await create(ledger, "p3 head")
    now = datetime.now(UTC)
    legacy = [f"p3leg{index:05d}aaaaaaaaaaaaaaaaaaaaa"[:32] for index in range(entries)]
    documents = [
        {
            "id": RecordID(TASK_TABLE, lid),
            **TaskLedger._new_task_content(f"legacy {lid}", DESCRIPTION, [], CREATOR, now),  # noqa: SLF001
            "superseded_by": head,
        }
        for lid in legacy
    ]
    await raw(ledger, f"INSERT INTO {TASK_TABLE} $rows", {"rows": documents})
    heavy = "p3heavyaaaaaaaaaaaaaaaaaaaaaaaa1"
    content = TaskLedger._new_task_content("heavy", DESCRIPTION, legacy, CREATOR, now)  # noqa: SLF001
    await raw(ledger, f"CREATE type::record('{TASK_TABLE}', $id) CONTENT $c", {"id": heavy, "c": content})
    edges = [{"in": RecordID(TASK_TABLE, lid), "out": RecordID(TASK_TABLE, heavy)} for lid in legacy]
    await raw(ledger, f"INSERT RELATION INTO {BLOCKS_RELATION} $edges", {"edges": edges})
    with pytest.raises(StragglerHealPackerError) as caught:
        await boot(env)
    assert SHRUNK_ROW_WARN_THRESHOLD < caught.value.weight <= SHRUNK_ROW_HARD_CAP, caught.value.weight
    assert caught.value.row_cap == SHRUNK_ROW_WARN_THRESHOLD, caught.value.row_cap
    assert caught.value.row_id == heavy
```

### `probes/make_builds.py`
```python
"""Write anchor/replacement files for each wrong build; each anchor must match the REFERENCE tasks.py exactly once."""
import sys
from pathlib import Path
S = Path(sys.argv[1]); ref = (S / "ref/loremaster/loremaster/tasks.py").read_text()
PACK = "        cap = min(_txn_module.TXN_ROW_WARN_THRESHOLD, _txn_module.TXN_ROW_HARD_CAP)\n"
HEAL = '                        f"DELETE $hd{row_index}_out<-{BLOCKS_RELATION} WHERE in = $hd{row_index}_{i}_in"\n'
SUP = '                statements=[f"DELETE $ssx_old_rec->{BLOCKS_RELATION}"],\n'
RAISE = "            raise StragglerHealPackerError(row_id=worst[0], weight=worst[3], row_cap=cap) from error\n"
TRY = '''        try:
            return [
                list(batch)
                for batch in constrained_batches(built, cap, get_len=lambda entry: entry[3], strict=True)
            ]
        except ValueError as error:
            worst = max(built, key=lambda entry: entry[3])
            raise StragglerHealPackerError(row_id=worst[0], weight=worst[3], row_cap=cap) from error
'''
builds = {
 "wb01_pack_hard": (PACK, "        cap = _txn_module.TXN_ROW_HARD_CAP\n"),
 "wb02_pack_warn_nomin": (PACK, "        cap = _txn_module.TXN_ROW_WARN_THRESHOLD\n"),
 "wb03_copied_10000": (PACK, "        cap = min(10_000, _txn_module.TXN_ROW_HARD_CAP)\n"),
 "wb04_surviving_5000": (PACK, "        cap = min(_txn_module.TXN_ROW_WARN_THRESHOLD, _txn_module.TXN_ROW_HARD_CAP, 5_000)\n"),
 "wb05_heal_table": (HEAL, '                        f"DELETE {BLOCKS_RELATION} WHERE in = $hd{row_index}_{i}_in AND out = $hd{row_index}_out"\n'),
 "wb06_sup_table": (SUP, '                statements=[f"DELETE {BLOCKS_RELATION} WHERE in = $ssx_old_rec"],\n'),
 "wb07_heal_v2": (HEAL, '                        f"DELETE $hd{row_index}_{i}_in->{BLOCKS_RELATION} WHERE out = $hd{row_index}_out"\n'),
 "wb08_rowcap_hard": (RAISE, "            raise StragglerHealPackerError(row_id=worst[0], weight=worst[3], row_cap=_txn_module.TXN_ROW_HARD_CAP) from error\n"),
 "wb09_pack_alone": (TRY, '''        worst = max(built, key=lambda entry: entry[3], default=None)
        if worst is not None and worst[3] > _txn_module.TXN_ROW_HARD_CAP:
            raise StragglerHealPackerError(row_id=worst[0], weight=worst[3], row_cap=cap)
        return [list(batch) for batch in constrained_batches(built, cap, get_len=lambda entry: entry[3], strict=False)]
'''),
 "wb10_heal_first_only": (HEAL, '''                        (f"DELETE $hd{row_index}_out<-{BLOCKS_RELATION} WHERE in = $hd{row_index}_{i}_in" if i == 0 else f"DELETE {BLOCKS_RELATION} WHERE in = $hd{row_index}_{i}_in AND out = $hd{row_index}_out")
'''),
 "wb11_heal_pairloose": (HEAL, '                        f"DELETE $hd{row_index}_out<-{BLOCKS_RELATION}"\n'),
 "wb12_sup_wrongdir": (SUP, '                statements=[f"DELETE $ssx_old_rec<-{BLOCKS_RELATION}"],\n'),
 "wb13_sup_bothdir": (SUP, '                statements=[f"DELETE $ssx_old_rec<->{BLOCKS_RELATION}"],\n'),
 "wb14a_sup_string_scan": (SUP, '                statements=[f"DELETE {BLOCKS_RELATION} WHERE in = type::record(\'{TASK_TABLE}\', $ssx_old)"],\n'),
 "wb14b_sup_decoy_plus_scan": (SUP, '                statements=[f"DELETE $ssx_old_rec->{BLOCKS_RELATION}", f"DELETE {BLOCKS_RELATION} WHERE in = type::record(\'{TASK_TABLE}\', $ssx_old)"],\n'),
 "wb15_offbyone": (PACK, "        cap = min(_txn_module.TXN_ROW_WARN_THRESHOLD, _txn_module.TXN_ROW_HARD_CAP) - 1\n"),
}
for name, (anchor, repl) in builds.items():
    assert ref.count(anchor) == 1, (name, ref.count(anchor))
    d = S / "specs" / name; d.mkdir(parents=True, exist_ok=True)
    (d / "anchor").write_text(anchor); (d / "replacement").write_text(repl)
    print(name, "ok")
```

### `run_wb.sh`
```bash
#!/usr/bin/env bash
# run_wb.sh <build>: apply the build's mutation in ITS OWN scratch copy via scripts/mutation_proof.py (exactly-once
# anchor, both-way diff against the pre-declared RED set, byte-exact restore), pytest scoped to the build's selection.
set -uo pipefail
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/a58r53
B=$1; N=${2:-3}; cd "$S/$B" || exit 2
LOG=$S/logs/$B.log
mapfile -t SEL < "$S/decl/$B.select"; mapfile -t RED < "$S/decl/$B.red"
EXP=(); for r in "${RED[@]}"; do EXP+=(--expect-red "$r"); done
# GUARD (2026-11-10, after an empty .select ran 4 unscoped suites): refuse an empty selection or declaration.
[ "${#SEL[@]}" -gt 0 ] && [ "${#RED[@]}" -gt 0 ] || { echo "REFUSED: empty selection (${#SEL[@]}) or declaration (${#RED[@]}) for $B" | tee "$S/logs/$B.log"; exit 3; }
{ ~/.claude/orchestration/tree_id.sh "$S/$B"
  echo "loremaster.__file__=$(.venv/bin/python -c 'import loremaster;print(loremaster.__file__)')"
  systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 \
    .venv/bin/python scripts/mutation_proof.py --file loremaster/loremaster/tasks.py \
      --anchor-file "$S/specs/$B/anchor" --replacement-file "$S/specs/$B/replacement" "${EXP[@]}" -- \
      .venv/bin/python -m pytest -q -n "$N" --timeout=300 -p no:cacheprovider "${SEL[@]}"
  echo "EXIT=$?"; } > "$LOG" 2>&1
tail -25 "$LOG"
```

### `run_sat.sh`
```bash
#!/usr/bin/env bash
# run_sat.sh: the reference SAT/over-fire run — the 15-file am-17 targeted set (714 ids) + the 3 adversary probes.
set -uo pipefail
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/a58r53
cd "$S/ref" || exit 2; LOG=$S/logs/sat-ref.log
{ ~/.claude/orchestration/tree_id.sh "$S/ref"
  echo "loremaster.__file__=$(.venv/bin/python -c 'import loremaster;print(loremaster.__file__)')"
  systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 \
    .venv/bin/python -m pytest -q -n 8 --timeout=300 -p no:cacheprovider -rfE $(cat "$S/sat_set.txt") loremaster/tests/test_adv_r53_probes.py
  echo "EXIT=$?"; } > "$LOG" 2>&1
tail -15 "$LOG"
```

### `run_head.sh`
```bash
#!/usr/bin/env bash
# Re-run the DELETE-family wrong builds with HEAD 99389cd's r5.3 file + support (tests only), and the reference control.
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/a58r53
{ cd $S/ref && ~/.claude/orchestration/tree_id.sh $S/ref && systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 .venv/bin/python -m pytest -q -n 4 --timeout=300 -p no:cacheprovider loremaster/tests/test_reanchor_58_r53_bound_and_plans.py loremaster/tests/test_adv_r53_probes.py; echo "EXIT=$?"; } > $S/logs/head99389cd/ref.log 2>&1
tail -2 $S/logs/head99389cd/ref.log
for b in wb05_heal_table wb06_sup_table wb07_heal_v2 wb10_heal_first_only wb11_heal_pairloose wb12_sup_wrongdir wb13_sup_bothdir wb14a_sup_string_scan wb14b_sup_decoy_plus_scan; do
  bash $S/run_wb.sh $b > /dev/null 2>&1; cp $S/logs/$b.log $S/logs/head99389cd/$b.log
  echo "$b: $(grep -oE 'PROOF HELD|PROOF FAILED' $S/logs/head99389cd/$b.log | head -1) $(grep -E '^[0-9]+ (failed|passed)' $S/logs/head99389cd/$b.log | tail -1)"
done
```

### `probes/heal_shape_offline.py`
```python
"""Offline: the heal chunk's fragment_rows for n one-blocker stragglers, and one row with k superseded blockers.
No store. Uses the tree's own _plan_heal_rows / _relate_fragment / _txn.fragment_rows."""
import loremaster
from loremaster.tasks import TaskLedger
from loremaster.store import _txn
print("loremaster.__file__", loremaster.__file__)
led = TaskLedger.__new__(TaskLedger); led._database = "x"
def chunk_rows(n, k=1):
    succ = {f"old{j}": "head" for j in range(k)}
    heads = {o: ("head", False) for o in succ}
    strag = [{"id": f"d{i}", "blocked_by": list(succ)} for i in range(n)]
    built = led._plan_heal_rows(strag, succ, heads, {"head"}, "t")
    frags = [f for e in built for f in e[1]] + [TaskLedger._relate_fragment([p for e in built for p in e[2]])]
    return _txn.fragment_rows([f for f in frags if f.statements]), built
r1, _ = chunk_rows(1); r2, _ = chunk_rows(2); r3, _ = chunk_rows(3)
per = r2 - r1; fixed = r1 - per
print(f"one-blocker: rows(1,2,3)={r1},{r2},{r3} fixed={fixed} per={per} linear={r3 == fixed + 3 * per}")
for bound in (800, 5000, 10000):
    print(f"bound {bound}: fit={(bound - fixed) // per} remainder={(bound - fixed) % per}")
_, built = chunk_rows(1, 1700)
print("monster (1700 superseded blockers) own weight entry[3] =", built[0][3])
for k in (200, 400, 1000, 1200):
    _, b = chunk_rows(1, k); print(f"k={k} weight={b[0][3]}")
```

### `probes/probe_delete_inventory.py`
```python
"""P6b: do the am-17 anchored DELETEs delete what the table-anchored ones deleted, on the shapes §9.2 left unmeasured?
World per form: dependent `dep` with TWO edges from `old` (a duplicate pair) + one edge from `live`; `old` also has a
DANGLING edge to a record that never existed (`ghost`) and two duplicate edges to `dep2`. TEST store :18000 only."""
import asyncio, sys
sys.path.insert(0, "loremaster/tests")
import loremaster
import _reanchor_58_support as s
from _surreal_harness import drop_database, make_env, unique_database
from surrealdb import RecordID
print("loremaster.__file__", loremaster.__file__)
T = lambda i: RecordID("task", i)
FORMS = {
    "heal V1 (old)": ("DELETE blocks WHERE in = $o AND out = $d", {"o": T("old"), "d": T("dep")}),
    "heal V3 (am-17)": ("DELETE $d<-blocks WHERE in = $o", {"o": T("old"), "d": T("dep")}),
    "sup T (old)": ("DELETE blocks WHERE in = $o", {"o": T("old")}),
    "sup G (am-17)": ("DELETE $o->blocks", {"o": T("old")}),
}
async def pairs(ledger):
    rows = await s.raw(ledger, "SELECT record::id(in) AS i, record::id(out) AS o FROM blocks")
    return sorted((r["i"], r["o"]) for r in rows)
async def main():
    for name, (stmt, params) in FORMS.items():
        env = make_env(database=unique_database(), dim=s.PRODUCTION_DIM)
        assert ":18000" in env.url, "TEST store only"
        ledger = s.new_ledger(env); await ledger.ensure_ready()
        try:
            for t in ("old", "live", "dep", "dep2"):
                await s.raw_seed_row(ledger, t, blocked_by=[])
            for a, b in (("old", "dep"), ("old", "dep"), ("live", "dep"), ("old", "dep2"), ("old", "dep2")):
                await s.raw_relate(ledger, a, b)
            before = await pairs(ledger)
            await s.raw(ledger, stmt, params)
            after = await pairs(ledger)
            print(f"{name:16} {stmt!r}\n   before={before}\n   after ={after}")
        finally:
            await ledger.close(); await drop_database(env)
asyncio.run(main())
```

Declaration files: `$S/decl/<build>.{select,red}` (md5 list `$S/decl.md5`, taken at 04:30:58Z before any run; the `.sel`→`.select` rename is the §INCIDENT fix, content unchanged).

## §HEAD — the DELETE family re-run against HEAD `99389cd`'s tests (2026-11-10 ~04:47Z)
HEAD moved during the grade: `548fe54` (CLAUDE.md only) and `99389cd` (r5.3 hygiene: the DELETE legs' private
`_ExplainBeforeTheWrite` replaced by `ApplyHook(when=…)` + `_PlanBeforeTheWrite`; same anchor-binding locator, same
assertions). I copied HEAD's `test_reanchor_58_r53_bound_and_plans.py` and `_reanchor_58_support.py` (md5 of the r5.3 file
`6bbb7582…` = `git show HEAD:…`) into the reference and the nine DELETE-family copies (tests only), then re-ran them with
the unchanged 04:30Z declarations (`run_head.sh`; logs `$S/logs/head99389cd/`):
- reference: r5.3 file + P1–P3 → **8 passed, EXIT=0**;
- WB5, WB6, WB7, WB11, WB12, WB13, WB14a: PROOF HELD, killed by the same leg as at a77f72e;
- **WB10 and WB14b: PROOF HELD with only P1 / P2 red. They still survive the contract at HEAD.**
The packer-bound family (WB1–4, 8, 9, 15) was not re-run: `99389cd` changes no packer-bound leg (diff read; the r2/r3/r4/r5
file hunks are one-line ownership comments), and WB9's surviving door is in the F10 leg, which `99389cd` does not touch.
