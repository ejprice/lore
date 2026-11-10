# REPORT-contract-58-r53 — packet 58 contract revision 5.3 (am-17 §6.1, §7, §9.4/§9.6)

brief-base v27 read · brief project v7 read

## SUMMARY BLOCK
- brief-base v27 read · brief project v7 read · **State: done-with-deviations** (2026-11-10 ~04:20Z).
- **Deviations:** D1 the production tree moved twice under me (builder edits, lead #20053/#20057): RED-1/RED-2 ran on tasks.py `3447cd97` (pre-am-17, the reds' messages and my delta anchors prove it); REF1 superseded by REF2 · D2 registry: my first pass (+5 ids, §REGISTRY) superseded by the lead's ruling (b) (§REGISTRY-2) → the packet-58 entry is fully discharged and DELETED (0 of 21 file entries keep anything on fa073bc) · D3 probes carry type annotations + 5 listed non-body edits vs the am-17 fences (§PROBES) · D4 heal EXPLAIN leg gained an edge-mirror assertion after RED-1 (kills a pair-loose DELETE the plan cannot see) · D5 two precondition ASSERTS added to the cited leg-3 worlds (no behaviour change).
- **Packages considered:** `more_itertools.constrained_batches` keep (only `max_size` re-keyed) · pytest `MonkeyPatch` replace · `_governed_contract.scans_table` EXTENDED (no second walker) · stdlib `re` for `$param` refs, bespoke 1 line (§PACKAGE SURVEY).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 3 shared test-support symbols (`heal_chunk_bound`, `iterated_records`, the `scans_table` arm) + test-local helpers, all dispositioned (§DRY LEDGER); probes REUSE `probe_hub_txn_58.URL` / `_surreal_harness`.
- **Graded:** n/a — authorship. HEAD-at-report `1d1e8e3` (build checkpoint `fa073bc` + am-17 §10 doc); my edits uncommitted.
- **Decisions needed:** (1) stale `owned by packet-58-contract` prose in 6 test files (§REGISTRY-2) — sweep? · (2) `_ExplainBeforeTheWrite` vs extending `ApplyHook` (§DRY LEDGER) · (3) hoist the 6-line `fresh_test_store_env` into `probe_hub_txn_58.py`? (3 copies) — none blocks.
- **Headline receipts:** **rider 3 (am-17 §10.3) PROOF HELD** — fa073bc minus `am17-build.patch` (tasks.py-only): 34/34 declared red exactly, 404 green, byte-exact restore; patch applied 437/438 green (the 1 = 64b-i's, named) (§RIDER3) · RED (declared 33 from `--collect-only` before the run) 33/33 red, 0 declared-but-green, 1 extra = 64b-i's (§RED, §RED-2) · new legs 5/5 GREEN on the reference · SAT 315 red ALL 64b-i-owned by id, **0 r5.3-attributable**, 33/33 r5.3 ids GREEN (§SAT) · `_governed_contract` callers: 5591 nodes before/after, **0 changed outcomes** (§GC) · gates: verify-registry EXIT=0, currency typecheck RED_ADJUDICATED(64b-i) + ruff GREEN → RED_ORPHANED 0 over typecheck/ruff, `test_secret_typing` 69 passed (§GATES) · plus-patch rider-3 set: 437 passed / 1 failed (64b-i's) (§REGISTRY-2).
- **Commit-ready paths (the lead commits; `git commit -- <paths>`):** `loremaster/tests/{_governed_contract.py, _reanchor_58_support.py, test_reanchor_58_r2_am2.py, test_reanchor_58_r2_rulings.py, test_reanchor_58_r3_convergence.py, test_reanchor_58_r3_probes.py, test_reanchor_58_r4_state.py, test_reanchor_58_r53_bound_and_plans.py}`, `scripts/{probe_heal_curve_58.py, probe_supersede_delete_58.py, probe_heal_delete_plan_58.py, pending_contracts.yaml}`, this report.
- **Pointers:** §WHAT CHANGED · §PACKAGE SURVEY · §DRY LEDGER · §FORALL · §PREFLIGHT · §CHECKLIST · §DUAL · §DECLINED · §PROBES · §RED / §RED-2 · §REFERENCE (delta verbatim + md5) · §REGISTRY-2 · §LEAD · §GC · §SAT · §GATES · §RUNS · §RIDER3.
- **Fan-out:** haiku 12 (all test/gate runners; 5 handed back early or quoted their own wrapper log — I read every count line from the named log myself) · sonnet 0 · peak 3. Deadline 120 min from spawn.

## CAPABILITY CHECK
- Tools: Bash, Read/Edit/Write, Agent (haiku-runner/haiku-worker), lore MCP (loaded, registered on lore_comms).
- Landmine recall returned 8 rows (< 50; not cut off).

## ROUTING TABLE (written before the first sweep, 2026-11-09)
| step | tier | who | reason |
|---|---|---|---|
| read spec am-17, store ref §0b/§3/§4, r5 report §R5.2/§INSTRUMENTS/§RE-BASE | 3 | self | contract rests on them |
| read the 6 legs to re-key + `_reanchor_58_support.py` + `_governed_contract.scans_table` | 3 | self | fixture judgment |
| inventory: every `TXN_ROW_HARD_CAP` read in `*58*` test files (textual seam) | 1 | self, one grep batch | small set (am-17 says 8 hits / 13 files), read whole, on critical path |
| callers of `_governed_contract` (`lore_impact` + grep cross-check) | 1 | self, one parallel batch | small; I need the node-id set myself |
| BEFORE/AFTER runs of every `_governed_contract` importer | 1 | haiku-runner | test run |
| RED run of new/re-keyed legs at builder tree | 1 | haiku-runner | test run |
| SAT run on reference copy | 1 | haiku-runner | test run |
| `--verify-registry`, `--currency --legs typecheck,ruff`, `test_secret_typing.py` | 1 | haiku-runner | gates |
| writing legs, helper, walker arm, probes, registry | 3 | self | contract authorship |

Routing note: the brief routes test runs to `haiku-runner` (followed). The `scripts/` probe copies, the walker arm and
every test edit are tier 3 (contract authorship / fixture judgment); the two inventories (hard-cap reads in 58 files;
`_governed_contract` importers) were small parallel greps I read whole (13 hits / 76 files) — said here per §3.
Fallbacks said out loud (brief-base §4): grep for the `TXN_ROW_HARD_CAP` reads in 58 test files (textual seam:
the re-key sweep), and grep cross-checking `lore_impact(_governed_contract.scans_table)` — lore served the
bare-name fallback with 15 of 535 covering entries (elided 520, classes/modules counted as tests: the known #557/#563
bound, not a new finding), so the importer set was derived by grep (`from _governed_contract import`): 70 test files.

## §WHAT CHANGED (all paths repo-relative; tree = HEAD `9e2f59d` + builder-58-1's uncommitted build)
| file | change | spec |
|---|---|---|
| `loremaster/tests/_reanchor_58_support.py` | NEW `heal_chunk_bound()` = `min(_txn.TXN_ROW_WARN_THRESHOLD, _txn.TXN_ROW_HARD_CAP)`, read live | am-17 §6.1 "one support helper states the ruled rule once" |
| `loremaster/tests/_governed_contract.py` (lead grant, am-17 §9.4) | `scans_table` EXTENDED in place: second arm `operation == "Iterate Table"` and `detail.table == table`; NEW sibling `iterated_records(plan)` (counts `operation == "Iterate Record"`). Nothing else in the file. | am-17 §9.4 "one walker" |
| `loremaster/tests/test_reanchor_58_r2_am2.py` | PR18r2: `predicted_chunks(…, heal_chunk_bound())` + message | §6.1 re-key 1 |
| `loremaster/tests/test_reanchor_58_r2_rulings.py` | six-blocker leg (`sizes ≤ heal_chunk_bound()`, message); padding MUTATION (`predicted_chunks(…, heal_chunk_bound())`); domain-rejection leg (`fit` from the helper); door leg: precondition ASSERT `heal_chunk_bound() == hard < WARN` (no behaviour change) | §6.1 re-keys 2 (the "two predicted_chunks / fit sites" + the six-blocker size bound) |
| `loremaster/tests/test_reanchor_58_r3_convergence.py` | `_cap()` returns `heal_chunk_bound()` (feeds the shape sweep's `fit`, the mixed-population greedy check, the over-weight row's non-vacuity and its `row_cap` fact); module docstring | §6.1 re-key 3 + "the over-weight single row leg" + "`StragglerHealPackerError.row_cap`'s pin re-keys to the helper" |
| `loremaster/tests/test_reanchor_58_r3_probes.py` | PC two-blocker leg: `rows ≤ heal_chunk_bound()` | §6.1 re-key 4 |
| `loremaster/tests/test_reanchor_58_r4_state.py` | `_drive_heal_multi_chunk`: precondition ASSERT hard < WARN inside the shrink (no behaviour change) | §6.1 leg 3 ("cited as this fate's pin") |
| `loremaster/tests/test_reanchor_58_r53_bound_and_plans.py` | NEW: legs 1, 2, 4 of §6.1 and the two §9.4 EXPLAIN legs | §6.1 legs 1/2/4, §9.4 |
| `scripts/probe_heal_curve_58.py`, `scripts/probe_supersede_delete_58.py`, `scripts/probe_heal_delete_plan_58.py` | NEW: committed copies of am-17 §INSTRUMENT / §INSTRUMENT-2 (diff vs the fences in §PROBES) | lead #20049, am-17 §9.6 |
| `scripts/pending_contracts.yaml` | packet-58-contract entry only (§REGISTRY) | brief |

## §PACKAGE SURVEY
| mechanism | libraries evaluated | what I READ | verdict |
|---|---|---|---|
| greedy packing by weight (the production packer the legs observe) | `more_itertools.constrained_batches` | installed call at `tasks.py::_pack_heal_chunks` (`constrained_batches(built, cap, get_len=…, strict=True)`) | keep (am-8/am-15/am-17) — the contract only re-keys `max_size` |
| restoring a monkeypatched constant (leg 2) | pytest 9 `MonkeyPatch.setattr` | the fixture's teardown restores it (used by every r5 leg) | replace — no hand-rolled save/restore |
| walking an EXPLAIN plan | none external: the plan is engine JSON; `_governed_contract.scans_table` is the house walker | read `scans_table` (SELECT-tree arm only) and live 3.3.5 plans (`rawplan.py`, §PROBES) | EXTENDED in place (am-17 §9.4) — no second walker |
| finding a statement's bound parameters | stdlib `re` over `$name` tokens | — | bespoke 1-line regex: SurrealQL ships no Python parser of its parameter references in the SDK (`surrealdb` 3.0.0 exposes no statement AST — not re-verified this round beyond the import surface used here; LOW-MEDIUM) |

**Odoo-20 portability: n/a — no Odoo seam touched.**

## §DRY LEDGER (brief-base §6 — test-support symbols only)
| new symbol | where I looked | what it returned | disposition |
|---|---|---|---|
| `_reanchor_58_support.heal_chunk_bound` | `_reanchor_58_support` symbols; grep `TXN_ROW_WARN_THRESHOLD` in 58 tests | `shrunk_row_caps` / `assert_unpatched_row_cap` (set/check constants, do not combine them) | HAND-ROLLED (the ruled rule, stated once — am-17 §6.1 asks for exactly this helper) |
| `_governed_contract.iterated_records` | `_governed_contract` (`operators`, `scans_table`, `index_served`) | `operators()` lists operator names; nothing counts `Iterate Record` | HAND-ROLLED sibling, as ruled (am-17 §9.4) |
| `_governed_contract.scans_table` second arm | same | — | EXTENDED in place |
| `_ExplainBeforeTheWrite` (test-local) | `_reanchor_58_support.ApplyHook` | fires ONCE at the FIRST `_apply` and passes no fragments; the heal leg needs the first `_apply` whose transaction holds a matching statement (a boot may `_apply` earlier), and both legs need the fragments | HAND-ROLLED (extending ApplyHook would add two knobs to a fixture 30+ legs use; flagged for the lead if it wants the extension instead) |
| `_binds`, `_statements_with_params`, `_edge_count`, `_seed_unrelated_edges`, `_assert_the_walker_sees_a_table_scan`, `_heal_rows_of_one_boot` (test-local) | support module (`ComposeSpy`, `snapshot`, `edge_pairs`, `bulk_seed_dependents`) | `edge_pairs` reads every pair (I need a count only); `bulk_seed_dependents` REUSED inside `_seed_unrelated_edges` | HAND-ROLLED, local, trivial |
| `probe_*_58.py::fresh_test_store_env` | `probe_hub_txn_58.py` (URL + `_surreal_harness`), `forgery_door_sweep._harness` | REUSED `probe_hub_txn_58.URL` and `._surreal_harness` (imported, not copied) | the 6-line env pin is one copy per probe file (3) — FLAG: a lead may want it hoisted next to `URL` in `probe_hub_txn_58.py` |

## §FORALL — ∀-vs-GUARDED for r5.3's load-bearing rows (analysis; the builds are the adversary's)
| invariant | property pinned | ∀ / GUARDED | fixture forcing each fate | wrong build it kills |
|---|---|---|---|---|
| chunk bound (leg 1 + the re-keyed sweep) | every heal transaction's `fragment_rows` ≤ `min(WARN, hard)` and the chunk count is the greedy packer's | ∀ over the generated shapes × {fit−1, fit, fit+1, 2fit+1} (r3 sweep, re-keyed) + mixed classes + one-/six-/two-blocker populations; GUARDED to shrunk constants by F19 (leg 4 is the one real-constant leg) | WARN < hard (5 000/800); hard < WARN (door + r4 worlds, now ASSERTED); real constants (leg 4) | packer at the hard cap (legs 1/4, re-keyed sweep at fit+1/2fit+1, PR18r2, six-blocker, PC, padding, rejection); packer at WARN with no `min` (leg 3 worlds: one over-cap chunk → compose refuses / door control reds); bound off by any constant (exact `heal_rows` lists) |
| read live (leg 2) | the bound follows `_txn.TXN_ROW_WARN_THRESHOLD` at heal time, boot to boot | ∀ boots in the leg (two) | shrink by `per·3` between boots | an import-time copy / `from _txn import …` (boot A); a read-once cache (boot B) |
| typed packer error `row_cap` | `row_cap == heal_chunk_bound()` | GUARDED to the one over-weight row (r5.2's reason: same branch, F19) | the 1 700-entry monster | a `row_cap` that serves the hard cap |
| supersede DELETE plan | the statement binding the old task's `RecordID` iterates no `blocks` table and exactly the hub's N outgoing edges | ∀ statements binding that id in the transaction (asserted exactly one); GUARDED to N = 5 / E = 25 (F19) — the count is the hub's degree, so a larger N adds nothing a builder could branch on | hub with its own blocker (edge INTO the hub excluded) + 25 unrelated edges | table-anchored DELETE kept (§9.5 #6); a both-direction anchor (N+1); a statement no longer binding a RecordID (non-vacuity reds) |
| heal DELETE plan | the statement binding dependent + old blocker iterates no table and exactly the dependent's blocker count (2) | GUARDED to the first heal transaction holding it (one target straggler); the plan is per-statement, so one representative is the statement form | straggler with 2 blockers; old blocker with 6 other dependents; 25 unrelated edges | V1 kept (assertion 1); V2 blocker-anchored (7 ≠ 2; §9.5 #7) |
| walker arms (C+) | the walker sees a table iteration in BOTH 3.3.5 plan shapes; `iterated_records` sees a non-2 count | positive controls in each EXPLAIN leg, live engine | table-anchored DELETE + SELECT over the same world; V2 over the healed head | an engine rename of `Iterate Table` / `TableScan` (C+ reds first); a walker that answers False always |

"Does my hostile fixture REACH the guard?" — leg 1 asserts the whole population fits ONE hard-cap chunk (else a
hard-cap packer would also chunk it); leg 4 asserts `bound < rows ≤ hard`; both EXPLAIN legs assert exactly ONE
matching statement (the hook can't EXPLAIN nothing and pass) and the heal leg asserts the straggler healed (the boot
reached the heal).

## §PREFLIGHT — adversarial pre-flight and fate of each
| input / wrong build | fate |
|---|---|
| wrong unit: bound in statements vs rows | covered: weights are `fragment_rows` measured at `compose` (unchanged); 58 fragments un-annotated (r5.2 pin) |
| wrong scale: the hard cap (50 000/5 000) used as the bound | legs 1, 4 + re-keyed sweep |
| WARN alone, no `min` (hard shrunk below WARN) | leg 3 worlds, precondition now asserted |
| a copied constant / cached read | leg 2 |
| off-by-one at the chunk boundary (`<` vs `≤`) | exact `heal_rows` lists in legs 1/2/4 (a full chunk is exactly `fixed + per·fit`) |
| heal DELETE: table-anchored (V1) / blocker-anchored (V2) / pair-loose (`DELETE $dep<-blocks`, deletes the live blocker's edge too) | V1, V2: heal EXPLAIN leg; pair-loose: NOT by the plan (it iterates 2 records too) — covered by the existing edge-mirror legs (`assert_edge_mirrors_column_for_every_row` after every heal), which red when the live blocker's edge vanishes |
| supersede DELETE: table-anchored / both-direction / `$old<-blocks` (wrong direction: deletes the edge INTO the hub, keeps the dependents' edges) | first two: supersede EXPLAIN leg (Iterate Table; N+1); wrong-direction: iterates 1 record ≠ 5 → reds here, and the edge-mirror supersede legs red too |
| an EXPLAIN that deletes (prefix form, or a build that sends DELETE without EXPLAIN) | edge count around the EXPLAIN asserted equal |
| producer↔consumer seam (`_apply` fragments → `compose` → store) | the hook reads the fragments at `_apply`, the ONE write door; the plan is the engine's, not ours |
| hostile stored free text | not applicable — no render of stored text in r5.3 |
| planted data (duplicate edges for one pair) | scoped out: no door writes a duplicate `blocks` pair (relates dedupe; §9.2 "spec-silent and unchanged in kind") |

## §CHECKLIST — realism & independence
- ☑ Production-realistic inputs — the real task schema via `ensure_ready`; one-blocker stragglers of the measured production shape (`fixed=0, per=4`, builder §HEAL-TIMING); sizes derived from the live constants, never literal row counts; ids 32-char house shape.
- ☑ Independent expected values — `fixed`/`per` measured at `compose` (`measure_heal_shape`); the bound from the RULING (`heal_chunk_bound`), never read from the packer; plan counts are the fixture's own degrees (5, 2), set by construction.
- ☑ Seam coverage — `compose` (ComposeSpy), `TaskLedger._apply` (the hook), the engine planner (EXPLAIN).
- ☑ Magnitude bounds — `bound < rows ≤ hard` (leg 4), whole population ≤ one hard-cap chunk (leg 1), every chunk ≤ 800.
- ☑ Shared conventions — `_txn` constants read live; `BLOCKS_RELATION` / `TASK_TABLE` from `surreal_schema`; walker shared (`_governed_contract`).
- ☐ Hostile free text — not applicable: no free-text render.
- ☐ Input accounting — not applicable for r5.3's new legs (no new collection transform; the heal's per-row accounting is r3/r4's and unchanged).

## §DUAL — every leg r5.3 re-keys or retires (continuing r5's numbering style; ruling = am-17)
| leg | was (r5.2) | now (r5.3) | ruling |
|---|---|---|---|
| `test_reanchor_58_r2_am2.py::test_PR18r2_cap_plus_one_of_ONE_blocker_heals_in_the_PACKERS_predicted_chunks` | `predicted_chunks(…, TXN_ROW_HARD_CAP)` | `…, heal_chunk_bound()` | §6.1 |
| `test_reanchor_58_r2_rulings.py::TestTheHealPacksByItsOwnComposedCount::test_cap_plus_1_stragglers_over_SIX_blockers_…` | every chunk ≤ hard cap | ≤ `heal_chunk_bound()` | §6.1 |
| `…r2_rulings.py::TestTheHealPacksByItsOwnComposedCount::test_MUTATION_padding_the_shell_moves_the_packer_AND_the_accessor` | predicted at the hard cap | at `heal_chunk_bound()` (the accessor half unchanged: the supersede still prices against the hard cap) | §6.1 |
| `…r2_rulings.py::…::test_a_chunk_DOMAIN_rejection_is_isolated_WARNED_and_healed_next_boot` | `fit` from the hard cap | from `heal_chunk_bound()` | §6.1 |
| `…r2_rulings.py::TestAHealStoreFaultIsLOUD::test_every_heal_door_after_the_backfill_RAISES[*]` | hard shrunk to `fixed + 4·per` | unchanged + ASSERT `bound == hard < WARN` | §6.1 leg 3 |
| `test_reanchor_58_r3_convergence.py` `_cap()` (shape sweep ×36, mixed ×2, over-weight row) | live hard cap | `heal_chunk_bound()`; the packer error's `row_cap` fact re-keys with it | §6.1 + "row_cap's pin re-keys to the helper" |
| `test_reanchor_58_r3_probes.py::test_PC_stragglers_naming_TWO_superseded_blockers_at_scale_heal_in_ONE_boot` | chunks ≤ hard cap | ≤ `heal_chunk_bound()` | §6.1 |
| `test_reanchor_58_r4_state.py` `_drive_heal_multi_chunk` (the r4 heal legs) | hard shrunk to `fixed + 4·w` | unchanged + ASSERT hard < WARN | §6.1 leg 3 |
| am-17 §6.2's timing leg | — | NOT WRITTEN (replaced by §9.4's EXPLAIN legs) | §9.4 "Fate of §6.2's timing leg" |
| L3 `test_reanchor_58_r2_scale.py::test_L3_REAL_CAP_…` | unchanged | unchanged (≈5 004 rows < 10 000: still ONE transaction) — cited as the "surviving 5 000" kill | §6.1 leg 4 |
| r3_probes `rows <= _txn.TXN_ROW_HARD_CAP` (am-17 names it "`test_reanchor_58_r3_probes.py`'s assertion") | | the PC leg above — the only such read in that file | — |
| `test_reanchor_58_r2_probes.py::test_PR14_the_accessor_follows_the_shared_hard_cap` and every supersede-cap leg | | NOT re-keyed: the supersede hub cap still prices against the hard cap (am-17 §4: bound accepted, not changed) | §4 |

Sweep receipt (textual seam, grep): `TXN_ROW_HARD_CAP|predicted_chunks|_cap()|_HEAL_DRIVER_FIT|row_cap` over the 18
`*58*` test files → every heal-bound read above re-keyed or asserted; the remaining hard-cap reads are supersede /
compose / spy (`over_cap`, the hub refusal facts, PR14, L1/L2) — each a supersede or compose bound, which am-17 does
not move. am-17 §6.1 said "8 hits over 13 files"; my sweep's heal-bound sites are the 8 rows above (PR18r2, three
r2_rulings sites + the door leg, `_cap()`, PC, r4) — the count matches on the heal reads; I re-derived, not copied.

## §DECLINED — wrong builds I may not build (role boundary; the adversary's, am-17 §6.3 / §9.5)
| wrong build | the pin I expect to kill it (analysis) |
|---|---|
| 1 packer at the hard cap | leg 1 (one chunk > 800), leg 4, re-keyed sweep |
| 2 packer at the WARN threshold with no `min` | leg 3 worlds (door leg control; r4 heal driver) |
| 3 a copied 10 000 | leg 2 boot A (and leg 1) |
| 4 a surviving 5 000 | L3 (unchanged) |
| 5 table-anchored heal DELETE kept | heal EXPLAIN leg, assertion 1 |
| 6 table-anchored supersede DELETE kept | supersede EXPLAIN leg, assertion 1 |
| 7 heal DELETE anchored at the blocker (V2) | heal EXPLAIN leg, record count |
| + a read-once cached bound | leg 2 boot B |
| + a pair-loose heal DELETE (`DELETE $dep<-blocks`, no `WHERE`) | NOT the plan leg (2 records either way); the edge-mirror check (added to the heal EXPLAIN leg after the RED run, and the r3 `_assert_converged` legs) |
| + wrong-direction supersede DELETE (`$old<-blocks`) | supersede EXPLAIN record count (1 ≠ 5) + the supersede edge-mirror legs |

## §PROBES — the committed copies (lead #20049; am-17 §9.6)
| file | md5 (2026-11-09, final) | source fence | smoke run on `:18000` (2026-11-10 ~03:36Z) |
|---|---|---|---|
| `scripts/probe_heal_curve_58.py` | `0914f46b…` | am-17 §INSTRUMENT | `E 20 V3` → `heal_rows=[80] outcome=ok rows_on_head=20 old_edges_left=0` |
| `scripts/probe_supersede_delete_58.py` | `3d57789d…` | am-17 §INSTRUMENT-2 (first fence) | `10 100` → both forms: from_hub 0, into_hub 1 (survived); EXPLAIN attempts deleted nothing (5 → 5) |
| `scripts/probe_heal_delete_plan_58.py` | `6bc9a2f3…` | am-17 §INSTRUMENT-2 (second fence) | `V1 {Iterate Table blocks: 1}`, `V2 {Iterate Record: 50}`, `V3 {Iterate Record: 2}`, 51 edges after — reproduces §9.1 |

Diff vs each fence (the ONLY changes; extracted md5s of the fences: heal_curve `12f8a2b2…`, supersede `b286d391…`,
heal_plan `7ed397bd…`): (1) a header comment + `# ruff: noqa: E501, PLW0603` (the fence body keeps the spec's line
width and part F's `global`); (2) `sys.path.insert(0, "/home/ejprice/…/loremaster/tests")` → `from probe_hub_txn_58
import URL as TEST_STORE_URL, _surreal_harness; _surreal_harness()` (relative path, REUSED, not copied); (3) every
`make_env(database=unique_database(), dim=s.PRODUCTION_DIM)` → `fresh_test_store_env()`, which pins
`url=TEST_STORE_URL` (`ws://127.0.0.1:18000/rpc`) whatever `$SURREAL_URL` says and asserts it; (4) `ruff check --fix`
(import order; heal_plan's now-unused `import sys` and heal_curve's duplicate `import dataclasses` dropped); (5)
heal_plan only: `asyncio.run(main())` under `if __name__ == "__main__":` (so `rawplan.py` could import it); (6) type
annotations (lead #20055: the gate types `scripts/` — 22 mypy errors → `MYPYPATH=scripts mypy scripts`: Success, 66 files),
with `PRODUCTION_DIM` / `SurrealEnv` imported from `_surreal_harness` and two `# type: ignore[method-assign]` on part E's
monkeypatch. Re-smoked after: plan probe V3 = 2 records; curve `E 20 V3` healed 20.
**Sign-in:** every probe connection is a `TaskLedger` built from the harness env (the suite's TEST-store credential),
and `TaskLedger` signs in through `loremaster.store._txn.signin_credentials` (`tasks.py`'s connect path) — no probe
hand-rolls a signin payload. `test_secret_typing.py` is in the SAT set (it scans `scripts/`).

## §RED — run 1 (2026-11-10 ~03:37Z), on the REAL tree: builder-58-1's build (tasks.py `3447cd97…`) + r5.3 tests
- Declared BEFORE the run from `--collect-only` (123 ids over the 6 files; `declared_red_r53.txt`, md5 `93d2e6d6…`,
  by the written rule: every new-file leg; PR18r2; the six-blocker, padding and domain-rejection legs; the convergence
  sweep at `fit+1` / `2fit+1` (not `fit−1` / `fit`: those fit one chunk under either bound); both mixed populations;
  the over-weight row; the PC two-blocker leg) — 33 ids.
- `logs/red-r53.log` (TREE `ebd5a667…`): **34 failed / 89 passed, EXIT=1, 200 s.** `red_diff_r53.py`: all 33 declared
  ids red, 0 declared-but-green; ONE unexpected red, `test_reanchor_58_r4_state.py::…[findings.py::_run_guarded ->
  findings.py::_run_guarded]` — `TypeError: FindingLedger.report() got an unexpected keyword argument 'title'`,
  registered under **packet-64b-i-contract** (`pending_contracts.yaml`, that id), not r5.3's.
- Every r5.3 red is 58's reason, read from the junit messages: chunk lists at the hard cap (`[1604]` vs
  `[800, 800, 4]`; `[804]` vs `[800, 4]`; `[10004]` vs `[10000, 4]`; `[5000, 1664]`; `[5000, 5000, 400]`), the packer
  error's `row_cap: 5000` vs derived 800, and both EXPLAIN legs: `Iterate Table` / `blocks`.
- ⚠ The lead's #20053: production moved after my first BASE copy; this run used the CURRENT working tree (tasks.py
  `3447cd97`), not BASE. It is re-run on the checkpoint SHA when posted (§RED-2). After run 1 I added one assertion
  to the heal EXPLAIN leg (edge mirror after the boot) — after its red line, so its red is unchanged in kind.

## §REFERENCE — a SAT HOST, NOT A SPEC (the ruling is am-17 §2 / §3 / §9.2)
- REF2 = `./scripts/scratch_copy.sh` of the real tree at ~03:51Z (builder tasks.py `3447cd97…` + the r5.3 tests) + `ref_delta_r53.py` (md5 `b3e674f9…`) → REF2 tasks.py `e5d19642…`; `loremaster.__file__` = `…/scratchpad/c58r53/ref2/loremaster/loremaster/__init__.py` (scratch_copy receipt). `diff -rq` vs the real `loremaster/`: only `tasks.py` differs. (REF1, built on the stale BASE tasks.py `52d2fff8`, is superseded; its one debug run — the new file 5/5 GREEN — is reported in §RUNS.)
- The delta, as a unified diff of tasks.py (md5 of the diff file `ca31beea…`):
```diff
--- /home/ejprice/PycharmProjects/lore/loremaster/loremaster/tasks.py	2026-11-09 22:27:35.167842595 -0500
+++ /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/c58r53/ref2/loremaster/loremaster/tasks.py	2026-11-09 22:44:57.586996013 -0500
@@ -2287,7 +2287,8 @@
         fragments = [TaskLedger._supersede_fragment(old_id, new_id, content, event)]
         fragments.append(
             TxnFragment(
-                statements=[f"DELETE {BLOCKS_RELATION} WHERE in = $ssx_old_rec"],
+                # `blocks` has no index — a table-anchored DELETE iterates the whole table; am-17 §9.
+                statements=[f"DELETE $ssx_old_rec->{BLOCKS_RELATION}"],
                 params={"ssx_old_rec": RecordID(TASK_TABLE, old_id), "ssx_old": old_id},
             )
         )
@@ -2458,9 +2459,10 @@
                 final = list(dict.fromkeys(head if b == old else b for b in final))
             fragments = [
                 TxnFragment(
+                    # `blocks` has no index: a table-anchored DELETE scans it once per straggler — anchor
+                    # on the dependent (am-17 §3; scripts/probe_heal_curve_58.py).
                     statements=[
-                        f"DELETE {BLOCKS_RELATION} WHERE in = $hd{row_index}_{i}_in "
-                        f"AND out = $hd{row_index}_out"
+                        f"DELETE $hd{row_index}_out<-{BLOCKS_RELATION} WHERE in = $hd{row_index}_{i}_in"
                         for i in range(len(olds))
                     ],
                     params={
@@ -2481,8 +2483,15 @@
     def _pack_heal_chunks(
         built: Sequence[tuple[str, list[TxnFragment], list[tuple[str, str]], int]],
     ) -> list[list[tuple[str, list[TxnFragment], list[tuple[str, str]], int]]]:
-        """Greedy chunks sized by each row's OWN composed cost against the live row cap."""
-        cap = _txn_module.TXN_ROW_HARD_CAP
+        """Greedy chunks sized by each row's OWN composed cost against the heal's chunk bound.
+
+        The bound is ``min(TXN_ROW_WARN_THRESHOLD, TXN_ROW_HARD_CAP)``, both read live: the WARN threshold by
+        ruling (packet 58 amendment 17 §2) — a transaction's time grows with the square of its rows, measured
+        7.25 s per 10,000-row chunk on the real schema — and never above what ``compose`` accepts.
+        Re-open trigger (am-17 §5): a production ``task.backfill.stragglers_reanchored`` record with
+        ``chunks >= 2``, or a heal that raises ``SurrealOutcomeUnknownError``; either re-runs
+        ``scripts/probe_heal_curve_58.py``."""
+        cap = min(_txn_module.TXN_ROW_WARN_THRESHOLD, _txn_module.TXN_ROW_HARD_CAP)
         try:
             return [
                 list(batch)
```
- The delta script verbatim (`ref_delta_r53.py`, md5 `b3e674f99cdd2ea3c9d79d217d6922f9`):
```python
#!/usr/bin/env python3
"""ref_delta_r53.py <tree-root> — contract-58-r53's reference delta (a SAT HOST, NOT A SPEC; the ruling is
packet 58 amendment 17 §2 / §3 / §9.2). Applies am-17 §7's production edits 1, 2 and 6 (+ their docstring /
comment riders) to builder-58-1's tasks.py. Exact-once anchors (#194): a missing or doubled anchor exits 1."""
import sys
from pathlib import Path

TASKS = Path(sys.argv[1]) / "loremaster" / "loremaster" / "tasks.py"
src = TASKS.read_text()


def sub(old: str, new: str) -> None:
    global src
    count = src.count(old)
    if count != 1:
        sys.exit(f"anchor count {count} != 1: {old[:80]!r}")
    src = src.replace(old, new)


# edit 1 — the packer's bound (am-17 §2), with its docstring rider
sub('''        """Greedy chunks sized by each row's OWN composed cost against the live row cap."""
        cap = _txn_module.TXN_ROW_HARD_CAP
''', '''        """Greedy chunks sized by each row's OWN composed cost against the heal's chunk bound.

        The bound is ``min(TXN_ROW_WARN_THRESHOLD, TXN_ROW_HARD_CAP)``, both read live: the WARN threshold by
        ruling (packet 58 amendment 17 §2) — a transaction's time grows with the square of its rows, measured
        7.25 s per 10,000-row chunk on the real schema — and never above what ``compose`` accepts.
        Re-open trigger (am-17 §5): a production ``task.backfill.stragglers_reanchored`` record with
        ``chunks >= 2``, or a heal that raises ``SurrealOutcomeUnknownError``; either re-runs
        ``scripts/probe_heal_curve_58.py``."""
        cap = min(_txn_module.TXN_ROW_WARN_THRESHOLD, _txn_module.TXN_ROW_HARD_CAP)
''')
# edit 2 — the heal's edge DELETE anchored on the dependent (am-17 §3), with its comment rider
sub('''                    statements=[
                        f"DELETE {BLOCKS_RELATION} WHERE in = $hd{row_index}_{i}_in "
                        f"AND out = $hd{row_index}_out"
                        for i in range(len(olds))
                    ],''', '''                    # `blocks` has no index: a table-anchored DELETE scans it once per straggler — anchor
                    # on the dependent (am-17 §3; scripts/probe_heal_curve_58.py).
                    statements=[
                        f"DELETE $hd{row_index}_out<-{BLOCKS_RELATION} WHERE in = $hd{row_index}_{i}_in"
                        for i in range(len(olds))
                    ],''')
# edit 6 — the supersede's edge DELETE anchored on the superseded task (am-17 §9.2), with its comment rider
sub('''                statements=[f"DELETE {BLOCKS_RELATION} WHERE in = $ssx_old_rec"],''',
    '''                # `blocks` has no index — a table-anchored DELETE iterates the whole table; am-17 §9.
                statements=[f"DELETE $ssx_old_rec->{BLOCKS_RELATION}"],''')
TASKS.write_text(src)
print("contract-58-r53 reference delta applied:", TASKS)
```

## §REGISTRY — ⚠ SUPERSEDED by §REGISTRY-2 (kept as the record of the first pass) — `scripts/pending_contracts.yaml`, packet-58-contract entry ONLY (md5 before `pending_contracts.before.yaml` in my scratch)
- `registry_r53.py` (text-level, idempotent; in my scratch) added **5 ids**: the new file entry
  `loremaster/tests/test_reanchor_58_r53_bound_and_plans.py` with its 5 legs. The other **28 declared r5.3 reds were
  already listed** (registered red before the build landed) — they are red again on the build for r5.3's reason, so
  they STAY: deleting them now would orphan them.
- For the 6 files I ran, the 58 entry lists 104 ids (`red-r53.xml`): **33 listed & red (keep — exactly the r5.3
  declared set) · 70 listed & GREEN (stale; the lead's deletion — list in `stale_listed_ids.txt`) · 1 listed & not
  collected** (`test_reanchor_58_r4_state.py::…[tasks.py::_reanchor_stragglers -> tasks.py::_reanchor_stragglers]` —
  the derived root key moved on the build; stale too).

## §LEAD — rows the build discharged (at g1 I deleted none, per the brief; the lead then ruled (b), executed in §REGISTRY-2)
The currency typecheck leg's **30 RED_ORPHANED residuals are ALL packet-58 self-destructs** (`self_destruct_30.txt`
in my scratch; the verify-registry run lists the 10 symbol ones): 9 `missing_symbols` that now resolve
(`SupersedeResult` ×5, `TxnCasLostError` ×2, `StragglerHealPackerError` ×2, `_ROLLBACK_LOG_TIERS` ×1 — overlap the
file rows), 19 "registered file produced NO mypy errors", 2 "registered symbol matched NO error line"
(`_guarded_append_fragment` in r3_cas_seam, `_reanchor_stragglers` in r4_state).
⚠ **How to delete them without orphaning r5.3's reds:** the gate's own message says "DELETE its registry entry", but
a file entry that also lists `red_nodeids` is a PYTEST claim too (`PendingFile.claims_mypy` = `missing_symbols or
unsymboled_codes`). For a file that still has r5.3 reds (r2_am2, r2_rulings, r3_convergence, r3_probes, and the new
file) remove only `missing_symbols` / `unsymboled_codes` and the stale ids; keep the entry with the 33 ids. Two
readings of "the rows self-destruct", written down: (a) delete whole file entries → my 28 re-keyed reds go unowned;
(b) strip the mypy claims + stale ids → 0 orphans. I would pick (b).
**Mine at RED_ORPHANED: 0** — no mypy error and no ruff finding in any file I touched (`currency-g1.log`: ruff GREEN;
the only typecheck residuals are the 30 above; `MYPYPATH=scripts mypy scripts` → "Success: no issues found in 66
source files" after the probe annotations).

## §RED-2 — on the FINAL test bytes (heal leg's edge-mirror line included), real tree, 2026-11-10T03:45Z
`logs/red2-r53.log` (TREE `2f7ff60b…`, tasks.py `3447cd97…`, `loremaster.__file__` = the repo's own): **34 failed / 89
passed, EXIT=1, 124 s.** `red_diff_r53.py` vs the same declaration: all 33 declared red · 0 declared-but-green · the one
unexpected red is again 64b-i's `findings.py::_run_guarded` `TypeError` (owned by packet-64b-i-contract). (The tree id
moves after a run only by this report's own appends — `REPORT-contract-58-r53.md` is a dirty file `tree_id.sh` hashes.)

## §RUNS — every harness run (all via `haiku-runner`; I checked each RAN: line and read each count line from the log)
| # | label | tree | command / log | result |
|---|---|---|---|---|
| 1 | gc BEFORE (the 70 `_governed_contract` importers, pre-walker) | BASE copy (builder tasks.py `52d2fff8`, pre-edit tests) | `run_set.sh … base gc-before gc_test_files.txt` → `logs/gc-before.{log,xml}` (TREE `399615c4…`) | 313 failed / 5277 passed / 1 skipped, 704 s |
| 2 | fixture debug: new file on REF1 | REF1 (stale BASE tasks.py + delta) | `logs/newfile-ref-debug.log` | 5 passed, 18.6 s |
| 3 | pre-edit baseline of the 5 re-keyed files (red attribution) | BASE | `logs/rekey-baseline.{log,xml}` (TREE `399615c4…`) | 4 failed / 114 passed, 556 s — 3 convergence `*-distinct-present-2fit+1` (on the builder's EARLIER tasks.py) + 64b-i's `_run_guarded` |
| 4 | RED-1 | real tree (tasks.py `3447cd97`) | `logs/red-r53.{log,xml}` (TREE `ebd5a667…`) | 34 failed / 89 passed — §RED |
| 5 | RED-2 (final test bytes) | real tree | `logs/red2-r53.{log,xml}` (TREE `2f7ff60b…`) | 34 failed / 89 passed — §RED-2 |
| 6 | gc AFTER | real tree | `logs/gc-after.{log,xml}` | 313 failed / 5277 passed — 0 changed outcomes (§GC) |
| 7 | SAT | REF2 | `logs/sat-r53.{log,xml}` | 315 failed (all 64b-i-owned) / 9323 passed — §SAT |
| 8 | rest of the 58 registry files, patch applied (for ruling (b)) | `cp/` | `logs/rest-plus.{log,xml}` | 242 passed / 1 skipped / 1 failed (64b-i's) |
| 9 | rider 3 plus | `cp/` | `logs/rider3-plus.log` | 437 passed / 1 failed (64b-i's) |
| 10 | rider 3 minus (mutation_proof) | `cp/` minus patch | `logs/rider3-minus.log` | 34 failed / 404 passed — PROOF HELD |
| — | gates (no pytest except secret typing) | real tree | `gates_r53.sh g1` → `logs/{verify-registry,currency,secret-typing}-g1.log` | §LEAD / §GATES |
More than ~2 runs, reasons: (3) attribution needed a pre-edit baseline — no builder receipt existed for these files;
(1)/(6) the brief's before/after-by-node-id demand; (2)/(5) a fixture debug and a re-run after the lead's moving-tree
warning (#20053) plus one added assertion; (8)/(9)/(10) the lead's ruling (b) (#20063) and am-17 §10.3 rider 3 (#20062),
both after spawn.

## §GC — the existing `_governed_contract` callers are unchanged (brief: before and after, by node id)
- BEFORE: `logs/gc-before.xml` (BASE copy, pre-walker `_governed_contract.py` md5 `e12b6a69…`, TREE `399615c4…`); AFTER:
  `logs/gc-after.xml` (real tree, walker md5 `c671da33…`); the same 70 test files (every `test_*.py` that imports
  `_governed_contract`, grep-derived, `gc_test_files.txt`).
- `compare_runs.py`: **before 5591 nodes (313 red) · after 5591 nodes (313 red) · 0 only-before · 0 only-after · 0
  changed outcomes.** The 313 reds are pre-existing and identical by node id (64b-i's registered bound and others; not
  r5.3's). Bound, stated: production `tasks.py` moved under the AFTER run (03:47:48Z, the builder's am-17 edits) — xdist
  workers had already imported it; the AFTER header shows `3447cd97`. No outcome changed, so the move cannot have hidden
  a walker regression in either direction for these files.

## §REGISTRY-2 — SUPERSEDES §REGISTRY: lead ruling (b) (#20063) applied on the r5.3 tree (2026-11-10 ~04:05Z)
- The r5.3 tree is `fa073bc` (the build checkpoint, which INCLUDES am-17 edits 1/2/6) + my uncommitted tests. On it the
  r5.3 legs are GREEN — so under F6 ("each listed id self-destructs when it passes") their ids are stale there too, and
  the 5 ids I added in §REGISTRY would have self-destructed at once. **The r5.3 RED proof therefore lives in §RIDER3
  (checkpoint minus `am17-build.patch`), not in the registry.**
- Measured on `cp/` (scratch_copy of the real tree = `fa073bc` + r5.3 tests; `loremaster.__file__` inside `cp/`;
  tasks.py `ee791e44…`): the 11 rider-3 files → `rider3-plus.log` **437 passed / 1 failed**; the other 10 registered
  files → `rest-plus.{log,xml}` **242 passed / 1 skipped / 1 failed**. Both reds are packet-64b-i-contract's
  (`test_reanchor_58_r4_state.py::…[findings.py::_run_guarded -> …]` and
  `test_reanchor_58_r3_cas_seam.py::…[findings.py::_run_guarded]`, both listed under that entry).
- `strip_r53.py` dry run (`strip_r53.dryrun.txt`): every packet-58 listed id green or uncollected, every mypy claim
  discharged (the currency-g1 self-destruct lines), **kept 0 of 21 file entries**. With no file left, the entry is its
  own self-destruct: deleted, with a dated `⚠ DISCHARGED` note above `bounds:` (the file's own precedent, the
  63b-ib-fork2 note). Reading I did NOT take: keep an empty `files: []` entry — the model would hold a bound that owns
  nothing. `scripts/pending_contracts.yaml` now holds `packet-64b-i-contract` only. Pre-strip copy:
  `pending_contracts.pre-strip.yaml` in my scratch.
- ⚠ Consequence the lead should know: the stale `# … owned by packet-58-contract` comments in 6 test files
  (`test_forgery_door_sweep.py`, `test_blocks_edge.py`, `test_exhaustion_fates.py`, `test_reanchor_58_r4_state.py`,
  `test_reanchor_58_r5_rows.py`, `test_reanchor_58_r3_am6.py`; grep, prose seam) now name a deleted bound. I did not
  edit them (prose only; four of them are outside the files I touched this round). Do you want them swept?
- Dry-run counts (`strip_r53.dryrun.txt`, run on the pre-strip copy): **243 listed ids removed** (green or uncollected on
  the r5.3 tree), **23 mypy claims discharged**, **21 file entries emptied** → entry deleted. Registry md5 after:
  `92d5f4bc…`; `strip_r53.py` md5 `fa7fa123…`.

## §SAT — 0 r5.3-attributable reds over the targeted set on REF2 (2026-11-10, started 03:45:23Z)
- Set (`sat_set.txt`, 146 files) = r5's declared targeted set (`declared_set.txt`, 117 files: the 58 files + the
  `lore_impact` covering tests of the 58-touched symbols + the structural pins, derived by `declare_set_r5.py`; the
  am-17 edits touch the same three `tasks.py` symbols, so it is not re-derived) ∪ the 70 `_governed_contract` importers
  (the walker change) ∪ the new r5.3 file ∪ `test_secret_typing.py` (the `scripts/` probes).
- `logs/sat-r53.{log,xml}` on REF2 (TREE `6314ea4b…`, `loremaster.__file__` inside `ref2/`, tasks.py `e5d19642…`):
  **315 failed / 9323 passed / 47 skipped, EXIT=1, 1531 s.** All 315 reds are listed BY ID under
  `packet-64b-i-contract`; **0 unowned, 0 under packet 58 → 0 r5.3-attributable.** All 33 r5.3 ids GREEN (0 missing);
  slowest r5.3 leg: leg 4 (real constants), 13.7 s.

## §GATES — final gate receipts (registry after the ruling-(b) strip; `gates_r53.sh g2`)
| gate | command | log | EXIT | count / verdict line | TREE |
|---|---|---|---|---|---|
| verify-registry | `uv run python scripts/pending_contract_gate.py --verify-registry` | `logs/verify-registry-g2.log` | 0 | `self-destruct: 9 import-checked absent · 34 UNCHECKED (owner not importable)` (all 64b-i's) | `69c07373…` |
| currency typecheck,ruff | `… --currency --legs typecheck,ruff` | `logs/currency-g2.log` | 1 | `typecheck RED_ADJUDICATED — 50 residual(s), owned by: packet-64b-i-contract` · `ruff GREEN` · the only ORPHAN is `pytest NOT_RUN` (leg-filtered by design) → **RED_ORPHANED 0 over typecheck/ruff** | `dad3a318…` |
| secret typing | `systemd-run … pytest -n 4 loremaster/tests/test_secret_typing.py` | `logs/secret-typing-g2.log` | 0 | `69 passed` | `dad3a318…` |
TREE moves between rows only by this report's appends (a hashed dirty file). The g1 run (before the strip) is
superseded: it showed the 30 packet-58 self-destructs §LEAD lists.

## §RIDER3 — am-17 §10.3 rider 3 (lead #20062)
- Copy: `cp/` = `./scripts/scratch_copy.sh` of the real tree = HEAD `1d1e8e3` (production = checkpoint `fa073bc`) + the
  r5.3 tests; `loremaster.__file__` = `…/scratchpad/c58r53/cp/loremaster/loremaster/__init__.py`; tasks.py `ee791e44…`.
- The am-17 targeted set (`rider3_set.txt`, 11 files, 438 ids collected): the new r5.3 file, the 5 re-keyed files, and
  the covering files of the three touched symbols' behaviours (L3 `test_reanchor_58_r2_scale.py`, PR14
  `test_reanchor_58_r2_probes.py`, the supersede edge-mirror legs `test_supersede_reanchor_58.py`,
  `test_blocks_edge.py`, the heal doors `scripts/test_forgery_door_sweep.py`).
- **Declared BEFORE any run, from `--collect-only`** (`rider3_declared.txt`, md5 `19a4c2e0…`, 2026-11-10T03:55Z): 34 ids
  = the 33 r5.3 ids (§RED's rule) + 1 NAMED non-r5.3 red that is red on the checkpoint either way (packet-64b-i's
  `test_reanchor_58_r4_state.py::…[findings.py::_run_guarded -> findings.py::_run_guarded]`), so (b)'s "every other
  test green" is measured over the remaining 404.
- **Patch applied** (`rider3.sh plus` → `logs/rider3-plus.log`, TREE `d5c221ce…`): **437 passed / 1 failed** — the one
  red is the named 64b-i id; every r5.3 leg GREEN.
- **Patch reversed** (`rider3.sh minus`: `git apply -R` builds the reversed tasks.py — patch body unread — and
  `scripts/mutation_proof.py --anchor-file <forward> --replacement-file <reversed>` with the 34 `--expect-red`, both-way
  diff, byte-exact restore; `rider3.sh` md5 `d879d1c4…`) → `logs/rider3-minus.log`, 2026-11-10T04:15:55Z:
  - patch `am17-build.patch` md5 `daa68841…`, numstat paths: **`loremaster/loremaster/tasks.py` only** (24+/7−);
    `git apply -R --check` OK; reversed tasks.py md5 **`3447cd97…`** = the exact tree RED-1/RED-2 ran on (so those two
    runs were, after the fact, runs on checkpoint-minus-patch);
  - `mutation LANDED (anchor matched exactly once)` · **34 failed / 404 passed, 139.6 s** · `tree restored byte-exact
    (… md5 ee791e44…)` · **`PROOF HELD — the declared RED set fired EXACTLY`** · EXIT=0.
  - (a) satisfied: 0 unexpected reds, 0 declared reds staying green. (b) satisfied: the other 404 ids green with the
    patch reversed; with it applied 437/438 green, the one red the named 64b-i id. No r5.3 leg is green without the
    patch, so every one has been seen red.

## §CLEANUP — lead #20070's three rulings (base `a77f72e`, 2026-11-10; tests/probes only, no behaviour change)
1. **Stale-prose sweep** — bare, anchor-free `grep -rn packet-58-contract` over `loremaster/` + `scripts/` (`*.py`;
   coverage: 580 tracked `*.py`, 16 files hit) and the design docs. Each hit:
   | file:line (at a77f72e) | verdict |
   |---|---|
   | `loremaster/tests/test_reanchor_58_r3_tiers.py:64` | EDIT — the comment says "a mypy error at HEAD owned by … `packet-58-contract`", which is now false; a dated `⚠ DISCHARGED 2026-11-10 (a77f72e)` line is inserted above the comment block |
   | `loremaster/tests/test_task_read_surface.py:236` | EDIT (same) |
   | `loremaster/tests/test_reanchor_58_r3_cas_seam.py:87` | EDIT (same) |
   | `loremaster/tests/test_reanchor_58_r3_probes.py:59` | EDIT (same) |
   | `loremaster/tests/test_reanchor_58_r4_state.py:73` | EDIT — a MIXED block (58's heal + 64b-i's `_run_guarded`): the note says the 58 half is discharged and the 64b-i half is still pending |
   | `loremaster/tests/test_reanchor_58_r3_convergence.py:86` | EDIT (same as first row) |
   | `loremaster/tests/test_reanchor_58_r3_relate.py:49` | EDIT |
   | `loremaster/tests/test_blocks_edge.py:350` | EDIT |
   | `loremaster/tests/test_task_guarded_shell_58.py:57` | EDIT |
   | `loremaster/tests/test_reanchor_58_r5_rows.py:45` | EDIT |
   | `loremaster/tests/test_task_claimable_partition_58.py:57` | EDIT |
   | `loremaster/tests/test_reanchor_58_r4_lease_fates.py:50` | EDIT |
   | `loremaster/tests/test_reanchor_58_r3_am6.py:43` | EDIT |
   | `loremaster/tests/test_exhaustion_fates.py:62` | EDIT |
   | `scripts/test_forgery_door_sweep.py:45` | EDIT |
   | `scripts/test_pending_contract_gate_f6.py:118` | KEEP — a synthetic registry fixture inside the gate's own test, not a claim about the real registry |
   | `scripts/pending_contracts.yaml:67` | KEEP — my DISCHARGED note |
   | `docs/design/2026-09-26-packet58-amendment-9.md:76`, `…-amendment-12.md:12,183`, `…-amendment-15.md:275,413,440,442` | KEEP — dated rulings (historical record; a ruling is not rewritten) |
   The `if TYPE_CHECKING:` imports themselves stay (they now resolve; removing them is not prose, and the ruling said no behaviour change).
2. **ApplyHook extended** — `_reanchor_58_support.ApplyHook(…, *, when=None)`: an optional predicate over the
   fragments `_apply` receives; the hook fires at the first `_apply` it accepts. With `None` (every existing caller) the
   condition is `not self.fired and True`, the original. `test_reanchor_58_r53_bound_and_plans.py`'s
   `_ExplainBeforeTheWrite` (which wrapped `_apply` itself) → `_PlanBeforeTheWrite`, a capture whose
   `holds_the_statement` is the `when` and `explain` the `before`, installed via `ApplyHook.installed()`. **0 assertion
   lines changed** (`git diff | grep -c '^[-+] *assert'` = 0); the attributes the assertions read (`matches`, `plan`,
   `edges_around_explain`) are unchanged.
3. **Hoist** — `scripts/probe_hub_txn_58.py::fresh_test_store_env` (next to `URL` and `_surreal_harness`; typed
   `-> SurrealEnv` under `TYPE_CHECKING`); the three am-17 probes import it, and each copy was deleted (with the imports
   only it used). Re-smoked on `:18000`: plan probe V3 = 2 records, 51 edges intact; supersede probe `10 100` sets equal;
   curve `E 20 V3` healed 20.
- **Proof that callers are unchanged** (targeted set `cleanup_set.txt`, 29 files = every `_reanchor_58_support` importer
  ∪ every `ApplyHook` importer ∪ every swept test file ∪ `test_secret_typing.py`; `_governed_contract` is untouched
  this round, so its importers are not re-run): BEFORE on a scratch_copy of `a77f72e` (`clean/`, `logs/cleanup-before.xml`,
  TREE `6678c8bb…`) **2 failed / 1974 passed / 1 skipped**; AFTER on the real tree (`logs/cleanup-after.xml`) **2 failed /
  1974 passed / 1 skipped**; `compare_runs.py`: **1977 nodes each, 0 only-before, 0 only-after, 0 changed outcomes.** Both
  reds are packet-64b-i-contract's (`r3_cas_seam … [findings.py::_run_guarded]`, `r4_state … [findings.py::_run_guarded
  -> …]`).
- **Gates** (`gates_r53.sh g3`, TREE `2ace38ca…`): verify-registry EXIT=0 · currency `--legs typecheck,ruff`: typecheck
  RED_ADJUDICATED (packet-64b-i-contract, 50), ruff GREEN, the only ORPHAN the leg-filtered pytest NOT_RUN → **RED_ORPHANED
  0 over typecheck/ruff** · `test_secret_typing.py` 69 passed · `MYPYPATH=scripts mypy scripts`: Success, 66 files.
- No am-17 leg assertion touched (adversary-58-r53 grades `a77f72e`).
- **Commit-ready:** `loremaster/tests/_reanchor_58_support.py`, `loremaster/tests/test_reanchor_58_r53_bound_and_plans.py`,
  `scripts/probe_hub_txn_58.py`, `scripts/probe_heal_curve_58.py`, `scripts/probe_supersede_delete_58.py`,
  `scripts/probe_heal_delete_plan_58.py`, the 15 swept files above, `REPORT-contract-58-r53.md`.

## §R2 — adversary-58-r53 R-2 (lead #20074): part E's V3 swap can no longer no-op silently (2026-11-10)
- **Defect:** `scripts/probe_heal_curve_58.py` part E swapped the heal's edge DELETE to V3 with a regex keyed on the
  retired V1 text. On the built tree, which already sends V3, the regex matched nothing and the probe still printed
  timings: "if step N silently no-opped, would step N+1 still print success?" Yes, it would.
- **Fix (scope: this file only):** `rewriting_apply` counts both shapes in every transaction it sees: V1 statements it
  swaps (`_HEAL_DELETE.subn`) and V3 statements the heal already sends (new `_HEAL_DELETE_V3`). After each V3 run it
  prints which one happened. If it saw **neither**, it raises `SystemExit("REFUSED (part E, V3, n=…): …")` (exit 1), after
  the `finally` blocks close the ledger and drop the throwaway database. So the probe stays meaningful on the built
  tree (it says the heal already sends V3 and times that heal) and on a V1 tree (it swaps), and fails loud otherwise.
  md5 `bfadf0b9…`; the diff against the pre-R2 copy is pasted below.
- **Runs, TEST store `:18000` only** (the probe's env is pinned through `probe_hub_txn_58.fresh_test_store_env`):
  | case | tree | command | result | log |
  |---|---|---|---|---|
  | built | real tree (`a77f72e` + cleanup), tasks.py `ee791e44` | `E 20 V3` | `swap: none needed: the heal already sends V3 x20` · healed 20 · EXIT=0 | `logs/r2-probe-1-2.log` |
  | **positive control: the refusal fires** | same | `E 0 V3` (no stragglers, so no heal DELETE is sent in either form) | `REFUSED (part E, V3, n=0): no heal edge DELETE was seen in either form …` · **EXIT=1** | same |
  | swap-arm control | `cp/` with the pre-am-17 tasks.py (`3447cd97`, = fa073bc minus am17-build.patch; `loremaster.__file__` inside `cp/`), restored to `ee791e44` afterwards | `E 20 V3` | `swap: V1->V3 swapped x20` · healed 20 · EXIT=0 | `logs/r2-probe-3.log` |
  The control fails for a different reason than the pin it controls: the pin checks the swap/native counts, and the
  control removes the statement itself.
- **Gates:** `uv run ruff check scripts/probe_heal_curve_58.py`: All checks passed · `MYPYPATH=scripts uv run mypy scripts`:
  Success, no issues in 67 source files.
- R-1 (`iterated_records`) left alone, as directed (close-out residual).
- **Commit-ready (do not commit — lead):** `scripts/probe_heal_curve_58.py`, `REPORT-contract-58-r53.md`.

```diff
--- /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/c58r53/probe_heal_curve_58.pre-r2.py	2026-11-09 23:49:12.073694329 -0500
+++ scripts/probe_heal_curve_58.py	2026-11-09 23:49:12.093694852 -0500
@@ -158,6 +158,10 @@
 E_SIZES = tuple(int(x) for x in (sys.argv[2] if len(sys.argv) > 2 else "4000,12500").split(","))
 INDEX_DDL = "DEFINE INDEX IF NOT EXISTS blocks_out ON blocks FIELDS out"
 _HEAL_DELETE = re.compile(r"DELETE blocks WHERE in = (\$\w+) AND out = (\$\w+)")
+#: R-2 (adversary-58-r53, lead #20074): the dependent-anchored form (V3) a built heal already sends. Part E counts both
+#: shapes in every transaction it sees; a V3 run that met NEITHER refuses (exit non-zero) instead of timing a heal
+#: whose DELETE it never saw — the swap keyed on V1 text silently no-ops on a tree that already sends V3.
+_HEAL_DELETE_V3 = re.compile(r"DELETE \$\w+<-blocks WHERE in = \$\w+")
 
 
 async def part_d() -> None:
@@ -207,13 +211,19 @@
     """The REAL heal (built ledger, real schema, one chunk) with the edge DELETE swapped for V3 (statement
     rewrite at `_apply`, production untouched) or served by V4's index. n=12500 is the full 50,000-row chunk."""
     real_apply = TaskLedger._apply  # noqa: SLF001
+    seen = {"swapped_v1": 0, "native_v3": 0}
 
     async def rewriting_apply(self: TaskLedger, fragments: list[TxnFragment]) -> None:
-        swapped = [
-            dataclasses.replace(f, statements=[_HEAL_DELETE.sub(r"DELETE \2<-blocks WHERE in = \1", st)
-                                               for st in f.statements])
-            for f in fragments
-        ]
+        swapped = []
+        for f in fragments:
+            statements = []
+            for st in f.statements:
+                new, hits = _HEAL_DELETE.subn(r"DELETE \2<-blocks WHERE in = \1", st)
+                seen["swapped_v1"] += hits
+                if not hits and _HEAL_DELETE_V3.search(st):
+                    seen["native_v3"] += 1
+                statements.append(new)
+            swapped.append(dataclasses.replace(f, statements=statements))
         await real_apply(self, swapped)
 
     for n in E_SIZES:
@@ -226,6 +236,7 @@
                 before = await edge_count(ledger)
                 spy = s.ComposeSpy()
                 if name == "V3":
+                    seen.update(swapped_v1=0, native_v3=0)
                     TaskLedger._apply = rewriting_apply  # type: ignore[method-assign]  # noqa: SLF001
                 t = time.monotonic()
                 try:
@@ -238,6 +249,17 @@
                 finally:
                     TaskLedger._apply = real_apply  # type: ignore[method-assign]  # noqa: SLF001
                 wall = time.monotonic() - t
+                if name == "V3":
+                    if seen["swapped_v1"]:
+                        swap = f"V1->V3 swapped x{seen['swapped_v1']}"
+                    elif seen["native_v3"]:
+                        swap = f"none needed: the heal already sends V3 x{seen['native_v3']}"
+                    else:
+                        raise SystemExit(
+                            f"REFUSED (part E, V3, n={n}): no heal edge DELETE was seen in either form (V1 to swap, "
+                            f"or V3 already sent) — the timing would not be of a V3 heal; outcome={outcome}"
+                        )
+                    print(f"E V3 n={n} swap: {swap}", flush=True)
                 on_head = await s.raw(
                     ledger, "SELECT count() AS n FROM task WHERE blocked_by CONTAINS $h GROUP ALL", {"h": head})
                 legacy_edges = await s.raw(
```

## §FIXWAVE — the packet 58 fix-wave contract (lead #20079; spec: am-17 §12, cold audit `coldaudit-58.md`, #625/#626/#628)

### Routing table (written before the first sweep, 2026-11-10)
| step | tier | who | reason |
|---|---|---|---|
| read am-17 §12, the cold audit, #625/#626/#628 | 3 | self | the spec |
| sweep the test tree for the retired served phrases ("can never win", "transaction cap", "KNOWN BOUND (58 F-1)", "file it with lore_findings", "exact-status filter") | 1 | self, one parallel grep batch | small, on the critical path, every hit gets a verdict |
| locate seams: heal cycle record names, `_refuse_a_cycle`, the claim text, the served `lore_tasks` schema, probe knobs | 3 | self | fixture realism needs the real names |
| write legs A–D, OB3, served-text pins, probe argparse | 3 | self | contract authorship |
| reference build (SAT host) | 3 | self | needed to show the pins are satisfiable |
| RED on aa4ea04 / SAT on the reference / currency / verify-registry / secret-seam | 1 | haiku-runner | test and gate runs |

### What the fix-wave contract pins (each leg's kills are analysis, not builds)
| item | where | pin | wrong builds it kills |
|---|---|---|---|
| leg A (§12.4) | `test_reanchor_58_fixwave.py::TestTheHealNeverWritesARowOntoACycle::test_A_…` | X→H, H `[D]`, D `[X, X2]` (X2→healthy H2), plus straggler S. Boot: S healed, `count == 1`; D byte-identical (column, every edge touching it, `updated_at`); no cycle over all columns (`find_blocked_by_cycle`); exactly ONE `task.backfill.straggler_would_close_cycle` WARNING naming D, with `blocker_ids == {X, X2}`, `members ⊇ {D, H}`, `cycle` an `a -> b` string, and `database`; no `legacy_cycle_minted`. Boot 2: the same WARNING. Control 1: the same shape through the live verbs → `TaskCycleError`. Control 2: break H's link by hand → the next boot heals D to `[H, H2]` with no WARNING | no check (HEAD); check-then-write-anyway; boot denial (the boot raises); silent skip; partial re-anchor (X2 moved); record on the first boot only; a fixture that can never heal (control 2) |
| leg B (§12.4) | `…::test_B_…` | D1 `[X1]` with **X1 → X1′ → H1** (the two-supersession chain), D2 `[X2]` with X2→H2, H1 `[D2]`, H2 `[D1]`. Boot: no cycle over all columns; both rows byte-identical; one WARNING each (`members ⊇ {D1, H1, D2, H2}`); 0 counted | a row-by-row check (heals both, writes D1→H1→D2→H2→D1); a check that stops at the first successor (X1′ waits on nothing) |
| leg C (§12.4) | `…::test_C_…` | D `[X, Z]`, Z `[D]` (legacy loop), X→healthy H. Boot: D byte-identical, one WARNING (`members ⊇ {D, Z}`), 0 counted | a build copying am-3 §4's `minted` choice (only the successor minted → the legacy loop is stepped over → D healed to `[H, Z]`) |
| leg D (§12.8 item 1) | `…::TestALegacyLoopIsRecordedEveryBoot::test_D_…` | A `[B]`, B `[A]`, both edges present (nothing missing). Two boots: each has exactly one `task.backfill.legacy_cycle_minted` WARNING with `members ⊇ {A, B}`; the store snapshot is unchanged | the early return (HEAD: `_backfill_blocks_edges` returns before `_record_legacy_cycles` when nothing is missing); a record-once flag |
| OB3 (#626) | `…::TestTheSupersedeRemovesEveryOutEdgeOfTheOldTask::test_a_DRIFT_edge_…` | hub with its own blocker, 3 dependents, and a drift edge hub→E (E's column does not name the hub). After the supersede: no edge leaves the hub; blocker→hub survives; E's column untouched; E not in `reanchored` | OB3 (`DELETE … WHERE out INSIDE $dependents_read`); a both-direction DELETE; a "dependent" set read from edges instead of columns (E reported) |
| F5 (§12.7) | `…::TestTheServedTextSaysWhatIsTrue::test_F5_…` | the legacy strand claimed through the `lore_tasks` dispatcher (`test_query_tasks_bounded._tool_seam`): names the blocker and the successor; serves `can never resolve: block on the successor instead`; does not serve `can never win` | the old text kept; the phrase dropped without the ruled form |
| #130(a) | `…::test_130a_…` | the served MCP schema (`build_mcp_server(LoreServer(...)).list_tools()`, `lore_tasks` → `parameters.properties.status.description`) contains "superseded" and "exclud…" | text unchanged; a docstring-only fix (the source is not what is served) |
| #625 a | `test_reanchor_58_r3_convergence.py::TestARowOverTheCapFailsTheBootLOUD::test_a_single_row_over_the_cap_…` (assertions ADDED) | under the 5 000 / 800 shrink: the served text has no "transaction cap", names the chunk ("chunk"), serves the live bound (800, whole number) and no "10000"/"10,000" | the old prose; a hardcoded 10 000; the hard cap (5 000 here) served as the bound |
| #625 b | `test_supersede_reanchor_58.py::TestTheHubBoundIsDERIVED::test_one_past_the_cap_is_REFUSED_byte_inert_and_TEACHES[0,2]` (RE-KEYED) | `_reanchor_58_support.assert_hub_refusal_serves_its_facts`: the contained id; dependents, rows, row_cap and cap_dependents each as a whole number; "nothing changed"; `#628`; none of `KNOWN BOUND`, `58 F-1`, `file it with lore_findings` | the old prose; a refusal that drops a fact; a refusal that does not name #628 |
| probe knobs (cold audit decision 3 (ii)) | `scripts/probe_hub_txn_58.py` | `PROBE_TXN_TIMEOUT` / `PROBE_SETTLE` env reads → `--txn-timeout` (default 0 = none) / `--settle` (default 75) | — (it clears the secret-seam scanner's one orphan; that scanner is the pin) |

### ∀-vs-GUARDED (fix wave)
| invariant | property | ∀ / GUARDED | fixtures forcing each fate | wrong build it kills |
|---|---|---|---|---|
| P (§12.2) | after a heal no row the heal wrote lies on a cycle, and every such row is skipped WHOLE and recorded every boot | ∀ over the three ways a heal can close a cycle that §12.4 names: alone (A), jointly (B), by joining a legacy loop (C); plus the healthy fate (A's S, control 2). GUARDED to those shapes: a cycle through 3+ stragglers is the same joint check B forces, so it adds no new branch | A (alone, two blockers), B (joint, two-supersession chain), C (legacy loop), control 2 (no cycle) | the 5 in leg A, row-by-row, first-successor, am-3 §4 `minted` copy |
| the skip is a record, not a silence | one WARNING per skipped row per boot, with the ruled extras | ∀ skipped rows in A, B and C; ∀ boots in A (two) | A boots 1 and 2; B two rows | silent skip; record-once |
| legacy loops every boot | a mirror-consistent legacy loop is recorded on every boot | GUARDED to a 2-cycle (a longer loop runs the same enumeration, `networkx.simple_cycles`, already pinned by `TestTheEnumerationEQUALSNetworkxAfterTheSwap`) | leg D, two boots | the early return; record-once |
| supersede DELETE (§9.2 row 1) | every edge out of the old task is gone, drift edges included | ∀ out-edges, in a world that is NOT mirror-consistent | OB3 world | OB3; both-direction delete |
| served text | each ruled text is served and the retired one is not | per text: F5 (claim render), #130(a) (served schema), #625 a (shrunk-cap world: the LIVE bound), #625 b (facts) | the existing worlds of each error | old text kept; hardcoded number; a fact dropped |

"Does the hostile fixture reach the guard?" — A asserts S healed and `count == 1` (the heal ran, it did not skip
everything); A's control 2 shows the same D heals once the loop is broken (the skip was the cycle's doing); B and C
assert 0 counted, so a build that heals and also logs a WARNING still reds on the byte-identical row.

### Adversarial pre-flight (fix wave)
| input / wrong build | fate |
|---|---|
| a cycle closing at the chain HEAD, not the first successor | leg B (X1 → X1′ → H1) |
| two rows closing a cycle jointly | leg B |
| a row already on a legacy loop through another blocker | leg C |
| a boot that raises instead of skipping | leg A (the boot must complete) |
| a partial re-anchor of a multi-blocker row | leg A (D names X and X2) |
| a record that fires only on the first boot | legs A (boot 2) and D |
| a legacy loop with nothing missing | leg D |
| a drift edge out of the hub | OB3 |
| a hardcoded bound in served text | #625 a in the 5 000 / 800 world |
| the served schema vs the source | #130(a) through `list_tools()` |
| hostile stored free text | not applicable — no new free-text render |
| planted data | every leg is raw-seeded LEGACY data: a shape the verbs refuse today but that `:18500` can carry (rows from before 58, am-1 R2's strand), so these are real-data shapes, not planted-only |

### §DUAL (fix wave)
| leg | was | now | ruling |
|---|---|---|---|
| `test_supersede_reanchor_58.py::TestTheHubBoundIsDERIVED::test_one_past_the_cap_is_REFUSED_byte_inert_and_TEACHES[0,2]` | `str(error) == hub_refusal_sentence(...)` (exact am-16 §2.1 sentence) | `assert_hub_refusal_serves_its_facts` (facts + `#628` + no retired phrases); typed-facts equality, byte-inert and the before-compose spy unchanged | #625 b ("pin facts, not the exact prose") |
| `_reanchor_58_support.hub_refusal_sentence` | the exact sentence builder | DELETED (its one caller re-keyed); replaced by `assert_hub_refusal_serves_its_facts`, `HUB_TIMEOUT_BAND_FINDING`, `HUB_REFUSAL_RETIRED_PHRASES` | #625 b |
| `test_reanchor_58_r3_convergence.py::…::test_a_single_row_over_the_cap_…` | text "not pinned (ruling)" | 4 text assertions added; the typed facts unchanged | #625 a (lead #20079 overrides am-16's "text not pinned") |
| retired-phrase sweep (grep, textual seam: "can never win", "transaction cap", "KNOWN BOUND (58 F-1)", "file it with lore_findings", "exact-status filter" over the test tree) | — | `test_task_ledger.py:908`, `test_query_tasks_bounded.py:616`, `test_blocks_edge.py:7352`: KEEP — each is an assertion MESSAGE describing a different defect, not a pin on served text; `_reanchor_58_support.py:115/116`: the deleted sentence builder; no test asserted "can never win" or "exact-status filter" on served text (so F5 and #130(a) are ADDED pins, not re-keys) | §12.7 "grep the test tree first" |

### Package survey (fix wave)
| mechanism | evaluated | read | verdict |
|---|---|---|---|
| cycle detection over the full column graph (the tests' "no cycle" assertion) | `loremaster.tasks.find_blocked_by_cycle` (the house detector, R6); `networkx` | the function's signature `(Mapping[str, Iterable[str]]) -> list[str] \| None` | REUSED — the tests call the production detector, the same one §12.3 keeps as the only detector |
| whole-number token match in served text | stdlib `re` | — | bespoke 1-line regex |
| CLI knobs for the probe | stdlib `argparse` | — | replace (cold audit decision 3 (ii)) |

### Receipts (fix wave)
| run | tree | log | result |
|---|---|---|---|
| declaration | `--collect-only -p no:lore-parked-contracts` on the real tree (380414c + my edits), 2026-11-10T06:00Z, BEFORE any run | `fw/declared_red.txt` md5 `98552d57…` | 9 ids: fix-wave legs A, B, C, D, F5, #130(a); the hub cap+1 leg [0] and [2]; the over-weight row leg. OB3 and the secret-seam scanner declared GREEN |
| RED | `fw/base` = scratch_copy of the real tree, the other session's `scripts/test_scratch_copy.py` / `test_wrong_builds.py` reset to HEAD **inside the copy only**; production = HEAD `380414c` = graded `aa4ea04` for `loremaster/loremaster` | `logs/fw-red.{log,xml}` (TREE `a2f80668…`) | **9 failed / 2715 passed / 1 skipped** over the 33-file set; declared vs observed: 9/9, 0 unexpected, 0 declared-but-green. ⚠ leg C's red was the WRONG reason (setup: `RELATE` to a row not yet seeded; `blocks` is ENFORCED) — fixture fixed (rows first, then edges) and re-run below |
| RED, re-run after the leg C fixture fix | `fw/base` | `logs/fw-red2.{log,xml}` (TREE `7a4da2f3…`) | the fix-wave file: **6 failed / 1 passed**, exactly the declared 6 + OB3 green; leg C now red for 58's reason (`D was re-anchored onto its legacy loop: [<H>, <Z>]`) |
| reasons, read per failure (RED) | — | — | A: `count == 2` (D healed too); B: `the heal wrote a cycle: [H1, D1, H2, D2, H1]`; C (re-run): D re-anchored; D: `saw []` (no record); F5: old text served; #130(a): `"…optional exact-status filter. Omit otherwise."`; #625 a: `"…over the 800-row transaction cap…"`; #625 b [0]/[2]: `does not name #628` (served `pinned KNOWN BOUND (58 F-1)…`) |
| secret-seam scanner | `fw/base`, the one node, inline, twice | `logs/fw-secret-seam.log` | with HEAD's probe: **1 failed** (`scripts/probe_hub_txn_58.py::<module>` reads the environment) · with the argparse probe: **1 passed** |
| SAT | `fw/ref` = the same copy + `ref_delta_fw.py` (md5 `8a6e1c53…`; a SAT host, NOT A SPEC) | `logs/fw-sat.{log,xml}` (TREE `fb168abc…`) | **1 failed / 2723 passed / 1 skipped** — the one red is leg C's setup bug above (same error on both trees), 0 others |
| SAT, re-run after the fixture fix | `fw/ref` | `logs/fw-sat2.{log,xml}` (TREE `2ca2965b…`) | the fix-wave file **7 passed**. With fw-sat, **0 fix-wave-attributable reds over the 33-file set** (64b-i's reds are parked by default, so they are deselected, not hidden: they are listed by id under packet-64b-i-contract) |

### The fix-wave reference — a SAT HOST, NOT A SPEC (`ref_delta_fw.py`, md5 `8a6e1c539c85…`; REF tasks.py `e83dcf51…`, server.py `4a468b74…`)
It extracts `cycle_through_minted` (the §12.3 predicate, used by both `_refuse_a_cycle` and the heal), adds `_skip_heal_rows_that_close_a_cycle` (§12.2: the whole pending set, looped), moves `_record_legacy_cycles` before the early return (§12.8 item 1), and edits the four served texts. The builder implements from am-17 §12, never from this.
```python
#!/usr/bin/env python3
"""ref_delta_fw.py <tree-root> — contract-58-r53's FIX-WAVE reference (a SAT HOST, NOT A SPEC; the rulings are
am-17 §12.2/§12.3/§12.7/§12.8 item 1, #625 a/b, #130(a)). Exact-once anchors (#194): a missing or doubled anchor
exits 1."""
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
TASKS = ROOT / "loremaster" / "loremaster" / "tasks.py"
SERVER = ROOT / "loremaster" / "loremaster" / "server.py"


def sub(src: str, old: str, new: str) -> str:
    count = src.count(old)
    if count != 1:
        sys.exit(f"anchor count {count} != 1: {old[:90]!r}")
    return src.replace(old, new)


t = TASKS.read_text()
# §12.2 record name
t = sub(t, '_HEAL_CYCLE_EVENT = "task.backfill.straggler_chain_cycle"\n',
        '_HEAL_CYCLE_EVENT = "task.backfill.straggler_chain_cycle"\n'
        '_HEAL_WOULD_CLOSE_CYCLE_EVENT = "task.backfill.straggler_would_close_cycle"\n')
# §12.3 the extracted predicate (module level, beside _drop_one_cycle_edge's users)
t = sub(t, "def raise_cycle_refusal(*, noun: str, cycle: Sequence[str]) -> NoReturn:\n",
        '''def cycle_through_minted(
    graph: Mapping[str, Iterable[str]], minted: set[str]
) -> list[str] | None:
    """The first ``blocked_by`` cycle a ``minted`` row lies on, or ``None`` (am-17 §12.3). Loops touching no minted
    row are stepped over one edge at a time (``_drop_one_cycle_edge``), on a COPY of ``graph``."""
    work = {node: set(refs) for node, refs in graph.items()}
    while True:
        cycle = find_blocked_by_cycle(work)
        if cycle is None:
            return None
        if minted.intersection(cycle):
            return cycle
        if not _drop_one_cycle_edge(work, cycle):
            return None


def raise_cycle_refusal(*, noun: str, cycle: Sequence[str]) -> NoReturn:
''')
t = sub(t, '''        minted = set(pending) if minted is None else minted
        while True:
            cycle = find_blocked_by_cycle(graph)
            if cycle is None:
                return
            if minted.intersection(cycle):
                raise_cycle_refusal(noun=CYCLE_NOUN_PERSISTED_IDS, cycle=cycle)
            if not _drop_one_cycle_edge(graph, cycle):
                return
''', '''        minted = set(pending) if minted is None else minted
        cycle = cycle_through_minted(graph, minted)
        if cycle is not None:
            raise_cycle_refusal(noun=CYCLE_NOUN_PERSISTED_IDS, cycle=cycle)
''')
# §12.2 the heal skips and records every row that would close a cycle (whole pending set, looped)
t = sub(t, '''        built = self._plan_heal_rows(stragglers, successor, heads, existing, at)
        chunks = self._pack_heal_chunks(built)
''', '''        built = self._plan_heal_rows(stragglers, successor, heads, existing, at)
        built = await self._skip_heal_rows_that_close_a_cycle(built, stragglers, successor, heads)
        chunks = self._pack_heal_chunks(built)
''')
t = sub(t, "    def _plan_heal_rows(\n", '''    async def _skip_heal_rows_that_close_a_cycle(
        self,
        built: list[tuple[str, list[TxnFragment], list[tuple[str, str]], int]],
        stragglers: Sequence[Mapping[str, Any]],
        successor: Mapping[str, str],
        heads: Mapping[str, tuple[str | None, bool]],
    ) -> list[tuple[str, list[TxnFragment], list[tuple[str, str]], int]]:
        """am-17 §12.2 (REFERENCE): drop, and record every boot, each planned row whose re-anchor would put it on a
        ``blocked_by`` cycle, checked over the WHOLE pending set at once."""
        stored = {
            str(row.get(_ID_KEY)): [str(b) for b in (row.get(_COL_BLOCKED_BY) or ())] for row in stragglers
        }
        pending: dict[str, list[str]] = {}
        olds_of: dict[str, list[str]] = {}
        for entry in built:
            dependent = entry[0]
            olds = list(dict.fromkeys(b for b in stored[dependent] if b in successor))
            final = list(stored[dependent])
            for old in olds:
                head = cast("str", heads[old][0])
                final = list(dict.fromkeys(head if b == old else b for b in final))
            pending[dependent], olds_of[dependent] = final, olds
        if not pending:
            return built
        seeds = {blocker for column in pending.values() for blocker in column}
        graph: dict[str, set[str]] = {
            node: set(refs) for node, refs in (await self._bounded_dependency_graph(seeds)).items()
        }
        for dependent, column in pending.items():
            graph[dependent] = set(column)
        skipped: set[str] = set()
        while pending:
            cycle = cycle_through_minted(graph, set(pending))
            if cycle is None:
                break
            for dependent in [d for d in pending if d in cycle]:
                logger.warning(
                    _HEAL_WOULD_CLOSE_CYCLE_EVENT,
                    extra={
                        "database": self._database, "task_id": dependent, "blocker_ids": olds_of[dependent],
                        "cycle": " -> ".join(cycle), "members": sorted(set(cycle)),
                    },
                )
                skipped.add(dependent)
                del pending[dependent]
                graph[dependent] = set(stored[dependent])
        return [entry for entry in built if entry[0] not in skipped]

    def _plan_heal_rows(
''')
# §12.8 item 1: record legacy loops on EVERY boot
t = sub(t, '''        columns, existing = await self._read_mirror_state()
        wanted = {''', '''        columns, existing = await self._read_mirror_state()
        self._record_legacy_cycles(columns)
        wanted = {''')
t = sub(t, '''        self._record_legacy_cycles(columns)
        if not mintable:
            return''', '''        if not mintable:
            return''')
# #625 a / b served text
t = sub(t, '''f"straggler {render_attributed(row_id)} alone composes {weight} rows, over the {row_cap}-row "
            f"transaction cap — the heal cannot pack it"''',
        '''f"straggler {render_attributed(row_id)} alone composes {weight} rows, over the {row_cap}-row "
            f"heal chunk bound — the heal cannot pack it"''')
t = sub(t, '''at most {cap_dependents} dependents) — refused, nothing changed. This is a pinned KNOWN "
            f"BOUND (58 F-1); file it with lore_findings."''',
        '''at most {cap_dependents} dependents) — refused, nothing changed. A supersede of fewer dependents "
            f"may still time out (about 5,700 or more): finding #628."''')
TASKS.write_text(t)

s = SERVER.read_text()
s = sub(s, '''f"blocker can never resolve, so this claim can never win: block on the "
                f"successor instead"''', '''f"blocker can never resolve: block on the successor instead"''')
s = sub(s, '''"of 'done' additionally requires 'summary'). For 'query', an "
                    "optional exact-status filter. Omit otherwise."''',
        '''"of 'done' additionally requires 'summary'). For 'query', an "
                    "optional exact-status filter; superseded rows are excluded from it (and from "
                    "'blocked'). Omit otherwise."''')
SERVER.write_text(s)
print("contract-58-r53 fix-wave reference delta applied:", ROOT)
```

### Gates (fix wave; `fw/gates_fw.sh fw <fw/base>`, the pinned copy; TREE `e4e9628e…`)
| gate | log | EXIT | verdict |
|---|---|---|---|
| `pending_contract_gate.py --verify-registry` | `logs/verify-registry-fw.log` | **0** | `self-destruct: 9 import-checked absent · 34 UNCHECKED` (all 64b-i's) |
| `--currency --legs typecheck,ruff` | `logs/currency-fw.log` | 1 (#621: `--legs` exits 1 on the leg-filtered pytest NOT_RUN) | typecheck **RED_ADJUDICATED** (the same 50 residuals as before, packet-64b-i-contract's; `packet-58-fixwave` claims no mypy error, it has no `missing_symbols`) · ruff **GREEN** · the only ORPHAN is `pytest NOT_RUN` → **RED_ORPHANED 0 over typecheck/ruff** |
| `test_secret_typing.py` | `logs/secret-typing-fw.log` | 0 | 69 passed |
| secret-seam scanner (the packet's one full-suite RED_ORPHANED) | `logs/fw-secret-seam.log` | — | red with HEAD's probe, **green** with the argparse probe |
The live tree was not gated: it carries another session's uncommitted `scripts/test_scratch_copy.py` with 2 mypy
errors (`GitIsolationGuard`), which are not mine and not touched (lead #20079).

### Summary, decisions and paths (fix wave)
- **State: done** (2026-11-10 ~06:35Z). Graded: n/a (authorship). Base HEAD `380414c`; production there = `aa4ea04`.
- **Readings I chose (brief-base §2), each with the alternative:**
  1. `packet-58-fixwave` is **`active: true`**: the fix-wave builder works against these reds now, so a default run
     must show them. Alternative: parked (`active` omitted), like 64b-i, which hides them from default runs until
     `--run-parked`. Currency is RED_ADJUDICATED either way.
  2. **#625 b** is pinned as facts plus `#628` plus no retired phrases. The reference's wording ("A supersede of
     fewer dependents may still time out (about 5,700 or more): finding #628.") is not pinned.
  3. **F5 and #130(a) are ADDED pins, not re-keys.** No existing test asserted the old served strings (sweep in
     §DUAL).
  4. **OB3 is green at HEAD.** The built DELETE is already `$old->blocks`, so it carries no RED. Its kill is the
     adversary's to show (OB3 build).
- **Not in this contract, flagged:** cold-audit F4 (THROW markers spelled twice, #624) is a builder item with no
  pin asked here; F6/F7 docstrings and dead code are the builder's and the audit's.
- **Decisions needed:** none blocking. (1) above is the one most worth a glance.
- **Commit-ready (lead commits; do not stage the other session's `scripts/test_scratch_copy.py` /
  `scripts/test_wrong_builds.py`):** `loremaster/tests/test_reanchor_58_fixwave.py` (NEW),
  `loremaster/tests/_reanchor_58_support.py`, `loremaster/tests/test_supersede_reanchor_58.py`,
  `loremaster/tests/test_reanchor_58_r3_convergence.py`, `scripts/probe_hub_txn_58.py`, `scripts/pending_contracts.yaml`,
  `REPORT-contract-58-r53.md`.
- **Runs:** RED (33 files), SAT (33 files), 2 re-runs of the fix-wave file after the leg C fixture fix, 2 single-node
  scanner runs inline, 1 gate bundle. Fan-out for this section: haiku 5 · sonnet 0 · peak 2.

## §FIXWAVE-13 — am-17 §13.5 items 1–3 + the probe + the F5 message (lead #20087; base HEAD `cec81c2`)

### ⚠ Exposure and tree notes (said first)
- **A builder is writing the §13 build into the LIVE tree** (uncommitted `loremaster/loremaster/tasks.py` and `server.py`,
  seen 2026-11-10 ~06:50Z when an in-memory script of mine failed to import `_drop_one_cycle_edge` from the live
  tree). All my runs use scratch copies with `tasks.py`, `server.py` and the other session's two files reset to HEAD
  `cec81c2` **inside the copy** (`git diff --quiet HEAD -- loremaster/loremaster` asserted on `fw13/base`).
- **Contract-blind exposure, disclosed:** one `grep` over the live `tasks.py` printed the builder's function name
  `find_row_blocked_by_cycles` and two docstring fragments. I did not read its body. §13.2 leaves the name to the
  builder; the R6 mutation pin needs a name to patch, so the contract fixes it as that name
  (`test_blocks_edge.py::PERSISTED_ROW_CYCLE_PREDICATE_ATTR`). Reading I did not take: a contract-chosen name the
  builder would then rename to.

### What §13 adds (each leg's kills are analysis)
| item | where | pin | kills |
|---|---|---|---|
| MP-1 E1 (heal) | `test_reanchor_58_fixwave.py::TestTheCyclePredicateIsExact::test_E1_…[legacy_ids_sort_first, control_dependent_sorts_first]` | X→H; H `[L1]`; L1 `[L2]`; L2 `[L1, D]`; D `[X]`. After the boot D is unchanged (column, edges, `updated_at`), recorded (§12.2 extras), and on no cycle by REACHABILITY (`_reaches`), never `find_blocked_by_cycle` | no check (HEAD); the step-over predicate (#631, legacy ids sorting first); a stored-graph-only check |
| MP-1 E3 (live supersede, the SECURITY DOOR) | `…::test_E3_…[with_legacy_loop, control_no_legacy_loop]` | R `[X]`; L1 `[L2]`; L2 `[L1, R]` (ids `00e3…`, sorting before the uuid successor); `supersede(X, blocked_by=[L1])` → `TaskCycleError`, snapshot unchanged. Control: no back edge L2→L1 | the step-over predicate (HEAD: the supersede SUCCEEDS and writes S→L1→L2→R→S) |
| D2 (i) | `…::TestTheHealsFateIsOnePassOverStoredPlusProposed::test_D2_i_…[old_loop_skips_D1_only, old_loop_skips_both]` | D1 `[X1→H1]`, H1 `[D1, D2]`, D2 `[X2→H2]`, H2 `[D1]`, under two id assignments, one from each fate class of the WITHDRAWN §12.2 loop (computed on HEAD's own `find_blocked_by_cycle` + `_drop_one_cycle_edge` by `fw13/d2_fate_classes.py`, pasted below: 12 orders skip D1 only, 12 skip both). Both rows unchanged and recorded, both on no cycle | the minimal fate (heal D2 once D1 is skipped); any id-order-dependent build |
| D2 (ii) | `…::test_D2_ii_…` | P `[Xp→Hp]`, Hp `[D]`; D `[X→H]`, X `[P]`; H clean. Boot 1: D healed to `[H]`, P unchanged and recorded; boot 2: P healed to `[Hp]`, no WARNING, no cycle | the overlay rules (all pending applied → no cycle → both heal on boot 1); someone "fixing" the one-boot wait |
| R6 re-key (§13.3) | `test_blocks_edge.py::TestTheCyclePolicyHasONEImplementation::test_MUTATION_the_persisted_row_predicate_answers_for_ALL_FOUR_writers` and `…::test_MUTATION_the_batch_key_detector_answers_ONLY_the_batch_key_question` | shared world `_persisted_writers_refuse`: create_many self loop, create_many through a persisted row, the supersede S→L1→L2→R→S, the heal D↔H'. Mutation 1: the predicate → `{}` (`raising=True`) ⇒ all four let the cycle through. Mutation 2: `find_blocked_by_cycle` → `None` in `tasks` and `server` ⇒ the cyclic BATCH is accepted and all four still refuse | a writer with a private check (routing is not sharing); a persisted writer still asking the batch-key detector (HEAD); a batch-key check riding the persisted predicate |
| F5 message (adversary residual 1) | `test_task_read_surface.py::…::test_a_claim_blocked_by_a_SUPERSEDED_task_names_it_AND_its_successor` | assertion MESSAGE only: "can NEVER win" → "can never resolve, and the move is to block on the successor (until the next boot heal re-anchors the row — am-17 §12.7)" | — (a message; the assertion is unchanged) |
| the instrument (§13.5 item 4) | `scripts/probe_cycle_predicate_58.py` | §INSTRUMENT-3 verbatim plus annotations and the seam: every rule-U call goes through `RULE_U`; `--built` points it at `rule_u_built`, whose body the cold audit replaces with the built predicate (it raises `NotImplementedError` until then). Smoke (`300 58`): U 0/0, OV1 69/44, OVF 0/5, supersede 0 differences | — (cold audit's run) |
| `create_task` | — | not offered to the R6 mutations: its id is minted inside the verb, so no persisted row can name it (the adversary's SIBLINGS NOT TRIED, by argument) | — |
- **§12.4 legs A–C unchanged** (§13.5 item 5). MP-2 and MP-3 not pinned (cold-audit probes, as directed).
- **Flag, not edited (outside the packet-58 files):** `test_cycle_write_path_04b3.py`'s docstring says
  "`_drop_one_cycle_edge` STAYS" (two prose lines; no code references it). §13 deletes it, so the prose goes stale
  when the build lands. Do you want it swept with the build?

### `fw13/d2_fate_classes.py` (pasted verbatim; the fate classes behind D2 (i)'s two id assignments)
```python
"""d2_fate_classes.py — contract-58-r53 (am-17 §13.5 item 2 (i)): the WITHDRAWN §12.2 loop (step-over predicate,
skip every pending row on the reported cycle, restore its stored column, ask again) over the D2 world under all
24 id orders, with HEAD's own find_blocked_by_cycle / _drop_one_cycle_edge. Prints each order's fate class, so
the contract can pick one id assignment from each class (the adversary's restore_probe, re-run on HEAD code)."""
import itertools
from loremaster.tasks import _drop_one_cycle_edge, find_blocked_by_cycle

def step_over(graph, minted):
    work = {n: set(r) for n, r in graph.items()}
    while True:
        c = find_blocked_by_cycle(work)
        if c is None: return None
        if minted & set(c): return c
        if not _drop_one_cycle_edge(work, c): return None

out = {}
for d1, h1, d2, h2 in itertools.permutations("abcd"):
    stored = {h1: [d1, d2], h2: [d1], d1: ["x1"], d2: ["x2"]}
    pending = {d1: [h1], d2: [h2]}
    view = {**stored, **pending}; skipped = []
    while pending:
        c = step_over(view, set(pending))
        if c is None: break
        for r in [r for r in pending if r in c]:
            view[r] = stored[r]; skipped.append(r); del pending[r]
    fate = "both" if len(skipped) == 2 else ("D1-only" if skipped == [d1] else f"other:{skipped}")
    out.setdefault(fate, []).append(dict(d1=d1, h1=h1, d2=d2, h2=h2))
for k, v in out.items(): print(k, len(v), "first:", v[0])
```
Output on `fw13/base` (HEAD code): `D1-only 12 first: {'d1': 'a', 'h1': 'b', 'd2': 'c', 'h2': 'd'}` · `both 12 first: {'d1': 'a', 'h1': 'c', 'd2': 'd', 'h2': 'b'}`.

### Receipts (§13)
| run | tree | log | result |
|---|---|---|---|
| declaration | `--collect-only` on `fw13/base`, 2026-11-10T07:04:52Z, BEFORE any run | `fw13/declared_red.txt` md5 `66fc44be…` | 17 ids = the fix-wave's 9 (still red: HEAD has no fix-wave part 2) + 8 new: E1 ×2, E3[with_legacy_loop], D2 (i) ×2, D2 (ii), R6 mutations 1 and 2. E3[control_no_legacy_loop] declared GREEN |
| RED | `fw13/base`: scratch_copy of the real tree with `tasks.py`, `server.py` and the other session's two files reset to HEAD `cec81c2` inside the copy (`git diff --quiet HEAD -- loremaster/loremaster`) | `logs/fw13-red.{log,xml}` (TREE `a73ee2d7…`) | **17 failed / 2718 passed / 1 skipped** over 34 files; declared vs observed 17/17, 0 unexpected, 0 declared-but-green |
| reasons (RED, new legs) | — | — | E1 both orders: `the heal wrote D onto a cycle` (HEAD's heal checks nothing); E3: `DID NOT RAISE TaskCycleError` (the #631 step-over miss); D2 (i) both: the first row changed (healed); D2 (ii): `boot 1: P must be unchanged, got [Hp]`; R6 mutation 1: `has no attribute 'find_row_blocked_by_cycles'` (the predicate is unbuilt); R6 mutation 2: `these persisted-row writers let a cycle through: [create_many, create_many_through_a_persisted_row, heal, supersede]` |
| SAT | `fw13/ref` = the same pinning + `ref_delta_fw13.py` (md5 `10e3645e…`; the ONE §13.2 predicate, a SAT host NOT A SPEC) | `logs/fw13-sat.{log,xml}` (TREE `d300a1f1…`) | **1 failed / 2734 passed / 1 skipped**. The one red was MY pin: R6 mutation 2 asserted the cyclic batch is ACCEPTED, but under §13 the batch passes the batch-key check and the ONE persisted predicate refuses the minted ids, in the persisted-id noun. Re-keyed: what must disappear is the BATCH-KEY refusal (`CYCLE_NOUN_BATCH_KEYS` not served) |
| re-run after that re-key (and a prose-only refill) | both copies; the fix-wave file + `TestTheCyclePolicyHasONEImplementation` | `logs/fw13-red2.{log,xml}` · `logs/fw13-sat2.{log,xml}` | HEAD **14 failed / 5 passed**, exactly the declared 14 of those files; mutation 2 still red at HEAD for the right reason (all four persisted writers let the cycle through) · REF **19 passed**. With fw13-sat: **0 attributable reds** over the 34-file set |
| prose refill check | — | — | an AST comparison (string constants whitespace-normalised) of both files before/after the refill: **equal** — the refill touched prose only |

### The §13 reference — a SAT HOST, NOT A SPEC (`ref_delta_fw13.py`, md5 `10e3645e40310d64f1c9c661bf37720b`)
On HEAD's production it adds `find_row_blocked_by_cycles(stored, proposed, asked, all_or_nothing) -> {row: cycle}`
(one `strongly_connected_components` pass; cycle = row + `shortest_path(blocker, row)`), routes `_refuse_a_cycle`
through it (`all_or_nothing=True`), deletes `_drop_one_cycle_edge`, adds the heal's one pass before packing
(`all_or_nothing=False`, stored + every pending row's post-rewrite column, skip + §12.2 record per hit), moves the
legacy-loop record before the early return, and edits the four served texts. The builder implements am-17 §13.2,
never this file.
```python
#!/usr/bin/env python3
"""ref_delta_fw13.py <tree-root> — contract-58-r53's FIX-WAVE §13 reference (a SAT HOST, NOT A SPEC; the rulings
are am-17 §13.2 (ONE predicate, SCC, no edge dropping), §13.4 (the heal: one pass over stored + proposed), §12.2's
fate and record, §12.7/§12.8 item 1, #625 a/b, #130(a)). Applied to HEAD cec81c2. Exact-once anchors (#194)."""
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
TASKS = ROOT / "loremaster" / "loremaster" / "tasks.py"
SERVER = ROOT / "loremaster" / "loremaster" / "server.py"


def sub(src: str, old: str, new: str) -> str:
    count = src.count(old)
    if count != 1:
        sys.exit(f"anchor count {count} != 1: {old[:90]!r}")
    return src.replace(old, new)


t = TASKS.read_text()
# §12.2 record name
t = sub(t, '_HEAL_CYCLE_EVENT = "task.backfill.straggler_chain_cycle"\n',
        '_HEAL_CYCLE_EVENT = "task.backfill.straggler_chain_cycle"\n'
        '_HEAL_WOULD_CLOSE_CYCLE_EVENT = "task.backfill.straggler_would_close_cycle"\n')
# §13.2 the ONE predicate (module level), and _drop_one_cycle_edge deleted
t = sub(t, "def raise_cycle_refusal(*, noun: str, cycle: Sequence[str]) -> NoReturn:\n",
        '''def find_row_blocked_by_cycles(
    stored: Mapping[str, Iterable[str]],
    proposed: Mapping[str, Iterable[str]],
    asked: Iterable[str],
    all_or_nothing: bool,
) -> dict[str, list[str]]:
    """am-17 §13.2 (REFERENCE): ``{row: cycle}`` for every ``asked`` row one of whose proposed blockers is the row
    itself or shares the row's strongly connected component. ``all_or_nothing``: a proposed column REPLACES the
    stored one; otherwise it is ADDED to it. One ``strongly_connected_components`` pass, no edge dropping."""
    columns: dict[str, list[str]] = {node: list(refs) for node, refs in stored.items()}
    for row, refs in proposed.items():
        refs = list(refs)
        columns[row] = refs if all_or_nothing else list(dict.fromkeys([*columns.get(row, []), *refs]))
    graph = networkx.DiGraph()
    for node in sorted(columns):
        graph.add_node(node)
        for blocker in sorted(set(columns[node])):
            graph.add_edge(node, blocker)
    component: dict[str, int] = {}
    for index, members in enumerate(networkx.strongly_connected_components(graph)):
        for member in members:
            component[member] = index
    hits: dict[str, list[str]] = {}
    for row in sorted(set(asked)):
        for blocker in sorted(set(proposed.get(row, ()))):
            if blocker == row or (blocker in component and component[blocker] == component.get(row)):
                hits[row] = [row, *networkx.shortest_path(graph, blocker, row)]
                break
    return hits


def raise_cycle_refusal(*, noun: str, cycle: Sequence[str]) -> NoReturn:
''')
start = t.index("def _drop_one_cycle_edge(")
end = min(i for i in (t.find("\ndef ", start + 1), t.find("\nclass ", start + 1)) if i > 0)
t = t[:start] + t[end + 1:]
t = sub(t, '''        minted = set(pending) if minted is None else minted
        while True:
            cycle = find_blocked_by_cycle(graph)
            if cycle is None:
                return
            if minted.intersection(cycle):
                raise_cycle_refusal(noun=CYCLE_NOUN_PERSISTED_IDS, cycle=cycle)
            if not _drop_one_cycle_edge(graph, cycle):
                return
''', '''        minted = set(pending) if minted is None else minted
        hits = find_row_blocked_by_cycles(
            {node: refs for node, refs in graph.items() if node not in pending}, pending, minted, True
        )
        if hits:
            raise_cycle_refusal(noun=CYCLE_NOUN_PERSISTED_IDS, cycle=hits[sorted(hits)[0]])
''')
# §12.2 the heal skips and records every row that would close a cycle (whole pending set, looped)
t = sub(t, '''        built = self._plan_heal_rows(stragglers, successor, heads, existing, at)
        chunks = self._pack_heal_chunks(built)
''', '''        built = self._plan_heal_rows(stragglers, successor, heads, existing, at)
        built = await self._skip_heal_rows_that_close_a_cycle(built, stragglers, successor, heads)
        chunks = self._pack_heal_chunks(built)
''')
t = sub(t, "    def _plan_heal_rows(\n", '''    async def _skip_heal_rows_that_close_a_cycle(
        self,
        built: list[tuple[str, list[TxnFragment], list[tuple[str, str]], int]],
        stragglers: Sequence[Mapping[str, Any]],
        successor: Mapping[str, str],
        heads: Mapping[str, tuple[str | None, bool]],
    ) -> list[tuple[str, list[TxnFragment], list[tuple[str, str]], int]]:
        """am-17 §12.2 fate + §13.4 rule (REFERENCE): ONE pass of the predicate over the stored columns PLUS every
        pending row's post-rewrite column; every hit row is skipped and recorded, BEFORE packing. No loop."""
        stored = {
            str(row.get(_ID_KEY)): [str(b) for b in (row.get(_COL_BLOCKED_BY) or ())] for row in stragglers
        }
        pending: dict[str, list[str]] = {}
        olds_of: dict[str, list[str]] = {}
        for entry in built:
            dependent = entry[0]
            olds = list(dict.fromkeys(b for b in stored[dependent] if b in successor))
            final = list(stored[dependent])
            for old in olds:
                head = cast("str", heads[old][0])
                final = list(dict.fromkeys(head if b == old else b for b in final))
            pending[dependent], olds_of[dependent] = final, olds
        if not pending:
            return built
        seeds = {blocker for column in pending.values() for blocker in column}
        graph = {node: list(refs) for node, refs in (await self._bounded_dependency_graph(seeds)).items()}
        for dependent in pending:
            graph[dependent] = stored[dependent]
        hits = find_row_blocked_by_cycles(graph, pending, set(pending), False)
        for dependent in sorted(hits):
            logger.warning(
                _HEAL_WOULD_CLOSE_CYCLE_EVENT,
                extra={
                    "database": self._database, "task_id": dependent, "blocker_ids": olds_of[dependent],
                    "cycle": " -> ".join(hits[dependent]), "members": sorted(set(hits[dependent])),
                },
            )
        return [entry for entry in built if entry[0] not in hits]

    def _plan_heal_rows(
''')
# §12.8 item 1: record legacy loops on EVERY boot
t = sub(t, '''        columns, existing = await self._read_mirror_state()
        wanted = {''', '''        columns, existing = await self._read_mirror_state()
        self._record_legacy_cycles(columns)
        wanted = {''')
t = sub(t, '''        self._record_legacy_cycles(columns)
        if not mintable:
            return''', '''        if not mintable:
            return''')
# #625 a / b served text
t = sub(t, '''f"straggler {render_attributed(row_id)} alone composes {weight} rows, over the {row_cap}-row "
            f"transaction cap — the heal cannot pack it"''',
        '''f"straggler {render_attributed(row_id)} alone composes {weight} rows, over the {row_cap}-row "
            f"heal chunk bound — the heal cannot pack it"''')
t = sub(t, '''at most {cap_dependents} dependents) — refused, nothing changed. This is a pinned KNOWN "
            f"BOUND (58 F-1); file it with lore_findings."''',
        '''at most {cap_dependents} dependents) — refused, nothing changed. A supersede of fewer dependents "
            f"may still time out (about 5,700 or more): finding #628."''')
TASKS.write_text(t)

s = SERVER.read_text()
s = sub(s, '''f"blocker can never resolve, so this claim can never win: block on the "
                f"successor instead"''', '''f"blocker can never resolve: block on the successor instead"''')
s = sub(s, '''"of 'done' additionally requires 'summary'). For 'query', an "
                    "optional exact-status filter. Omit otherwise."''',
        '''"of 'done' additionally requires 'summary'). For 'query', an "
                    "optional exact-status filter; superseded rows are excluded from it (and from "
                    "'blocked'). Omit otherwise."''')
SERVER.write_text(s)
print("contract-58-r53 fix-wave reference delta applied:", ROOT)
```

### Gates (§13; `fw/gates_fw.sh fw13 <fw13/base>`, TREE `02b94041…`)
| gate | log | EXIT | verdict |
|---|---|---|---|
| `--verify-registry` | `logs/verify-registry-fw13.log` | **0** | `packet-58-fixwave`: 17 ids (4 files) |
| `--currency --legs typecheck,ruff` | `logs/currency-fw13.log` | 1 (#621) | typecheck RED_ADJUDICATED (the same 50 residuals, packet-64b-i-contract's; none new) · ruff GREEN · only ORPHAN = the leg-filtered `pytest NOT_RUN` → **RED_ORPHANED 0 over typecheck/ruff** |
| `test_secret_typing.py` | `logs/secret-typing-fw13.log` | 0 | 69 passed |

### Close-out (§13)
- **State: done.** Not committed. HEAD-at-report `cec81c2`; the live tree also holds a builder's uncommitted §13 build
  in `tasks.py` / `server.py` (not mine, not read beyond one grep line, not in any of my runs).
- **Decisions / flags:** (1) the predicate's name `find_row_blocked_by_cycles` is fixed by the contract (the build's
  own choice); (2) `test_cycle_write_path_04b3.py`'s "`_drop_one_cycle_edge` STAYS" prose goes stale with the build:
  sweep it then?; (3) the R6 mutation-2 pin asserts the batch-KEY noun disappears rather than "the batch is
  accepted", because under §13 the persisted predicate refuses a cyclic batch's minted ids (measured on the
  reference). That is am-17 §13.3's "reddens only the batch-key pin", read as the batch-key REFUSAL.
- **Commit-ready (lead commits; never stage `scripts/test_scratch_copy.py` / `scripts/test_wrong_builds.py`, nor the
  builder's `tasks.py` / `server.py`):** `loremaster/tests/test_reanchor_58_fixwave.py`, `loremaster/tests/test_blocks_edge.py`,
  `loremaster/tests/test_task_read_surface.py`, `scripts/probe_cycle_predicate_58.py` (NEW), `scripts/pending_contracts.yaml`,
  `REPORT-contract-58-r53.md`.
- **Runs:** RED (34 files), SAT (34 files), 1 re-run each on the two changed files, 1 gate bundle, plus in-memory
  scripts (fate classes, probe smoke). Fan-out: haiku 5 · sonnet 0 · peak 2.

## §FIXWAVE-14 — am-17 §14.4 items 1, 2, 3 (first sentence), 5, 6 as amended by §14.7 (lead #20092; base HEAD `b99f178`)

### ⚠ Tree and scope notes (said first)
- Both copies are `scripts/scratch_copy.sh` copies with `loremaster/loremaster` reset to HEAD `b99f178` (production
  == `cdf1ce4`); the builder's live `tasks.py`/`server.py`/`_txn.py` hunks are not in either copy and I did not read them.
  `scripts/test_scratch_copy.py` / `scripts/test_wrong_builds.py` reset to HEAD in each copy, untouched in the live tree.
- The registry entry held **17** ids at HEAD, not the 26 the directive named (12 in `test_reanchor_58_fixwave.py`, 2 in
  `test_supersede_reanchor_58.py`, 1 in `test_reanchor_58_r3_convergence.py`, 2 in `test_blocks_edge.py`; measured by
  loading `scripts/pending_contracts.yaml`). All 17 removed.
- No scanner, no pin-the-miss (§14.7 item 1): the two-PROCESS supersede race stays finding #634 + docstrings.
- The graph-large constant's NAME is not ruled by §14.2; this contract fixes it as `TASK_GUARD_GRAPH_LARGE_ROWS` in
  `loremaster.tasks` (decision for the lead, listed below).

### The pins (new legs in `loremaster/tests/test_reanchor_58_fixwave.py` unless named; each leg's kills are analysis)
| § item | leg | world | RED at HEAD because | wrong build it kills |
|---|---|---|---|---|
| 1 #636 | `TestTheGuardsInputHasNoDepthBoundAndNoSeedCost::test_636_…300_stragglers…` | the audit's world: 300 stragglers, each re-anchored to its OWN head, every head blocked by one 30-deep chain (930 rows, 300 seeds) | the closure read's `TIMEOUT 5s` fails the boot | any guard input whose cost grows with the seed count; a heal that skips or drops stragglers to finish |
| 2 #635 S | `test_635_S_…[40_links]` (+ `[control_3_links]`) | T0; D[T0]; X_k[D] … X_0; `supersede(T0, blocked_by=[X_0])` closes a 43-member loop | 32-hop closure bound: the loop is written | a depth-bounded input; a supersede that writes before refusing (snapshot compare) |
| 2 #635 H | `test_635_H_…[40_links]` (+ control) | D; chain onto D; T0 superseded by S[X_0]; then the racing straggler D[T0]+edge; boot | same bound: the heal re-anchors D onto the loop | depth-bounded input; a heal that skips silently (one record asserted); a heal that writes the loop (graphlib witness) |
| 3 #634 | `TestTwoConcurrentSupersedes…::test_634_…every_time` | per repeat T1,T2,D1[T1],X[T2]; `supersede(T1,[X])` ∥ `supersede(T2,[D1])` on ONE ledger, 20 repeats | both commit (audit: 20/20) | no lock; a lock around the guard only (not the write); a build refusing BOTH (fates must be exactly one ok + one refused) |
| 5 §14.2 | `TestTheGraphLargeWarning::…[shrunk_below_the_fixture]`, `[shipped]` | 5 dependency-bearing rows; constant shrunk to 2 → one WARNING per boot; shipped → none, constant == 20,000 | no constant, no record | a missing/per-chunk/per-row warning (count == 1); a warning that fires at the shipped value; a different number |
| 6 #638 (i) | `TestTheCycleAnswerIsDeterministic…::test_638_i_…[create|create_many|supersede|heal]` | one world per writer shape, ≥3 stored orders × every proposed order, blockers reversed | GREEN at HEAD (build correct) | WB5: `sorted()` removed — the predicate's answer, the served sentence or the WARNING's `cycle` string varies with order |
| 6 #638 (ii) | `test_638_ii_leg_B_at_ONE_row_per_chunk…` | leg B's joint loop with `TXN_ROW_WARN_THRESHOLD` = one row's measured weight | GREEN at HEAD | WB2: predicate asked per chunk after packing (chunk 1 heals D1, chunk 2 skips D2) |
| 7 §14.7 item 3 | `test_blocks_edge.py::TestTheCyclePolicyHasONEImplementation::test_a_BATCH_KEY_cycle_is_served_in_the_PERSISTED_direction_row_then_its_blocker` | 3-key loop a[b] b[c] c[a] at the tool seam, and the same shape under caller-chosen ids | graphlib's path runs blocker -> dependent | a batch-key refusal in either direction other than `row -> its blocker`; a persisted refusal that flips |

Witness independence: the "no cycle written" checks use `find_blocked_by_cycle` (graphlib, the batch-key detector),
not the persisted-row predicate under test.

### The sweep (item 7) — every hit, its own verdict (55 hits / 13 files, the grep over `_bounded_dependency_graph`,
`_CLOSURE_START_PARAM`, `closure read`, `ancestor closure`, `bounded closure`, `FORK A`, `ESC-1`; line numbers are HEAD's)
| hit | verdict |
|---|---|
| `loremaster/tests/_recut_auth_fixtures.py:5` | unrelated — packet 39's auth-recut ESC-1; no edit |
| `loremaster/tests/_recut_auth_fixtures.py:60` | unrelated — packet 39's auth-recut ESC-1; no edit |
| `loremaster/tests/_surreal_fakes.py:919` | unrelated — telemetry `ok`-column ESC-1 (d0f84d0); no edit |
| `loremaster/tests/test_agent_capability_seams.py:25` | unrelated — packet 62's stamp_owner-home ESC-1; no edit |
| `loremaster/tests/test_agent_capability_seams.py:27` | unrelated — packet 62's stamp_owner-home ESC-1; no edit |
| `loremaster/tests/test_agent_capability_seams.py:83` | unrelated — packet 62's stamp_owner-home ESC-1; no edit |
| `loremaster/tests/test_agent_capability_seams.py:256` | unrelated — packet 62's stamp_owner-home ESC-1; no edit |
| `loremaster/tests/test_agent_capability_seams.py:259` | unrelated — packet 62's stamp_owner-home ESC-1; no edit |
| `loremaster/tests/test_agent_capability_seams.py:289` | unrelated — packet 62's stamp_owner-home ESC-1; no edit |
| `loremaster/tests/test_agent_capability_seams.py:298` | unrelated — packet 62's stamp_owner-home ESC-1; no edit |
| `loremaster/tests/test_agent_capability_seams.py:302` | unrelated — packet 62's stamp_owner-home ESC-1; no edit |
| `loremaster/tests/test_auth_composition_recut.py:12` | unrelated — packet 39's wire_session ESC-1; no edit |
| `loremaster/tests/test_blocks_edge.py:167` | unrelated — the legacy-cycle record's reader (ESC-1 reading A), not the read; no edit |
| `loremaster/tests/test_blocks_edge.py:2002` | re-keyed prose — MP-1 docstring kept as 04b-3 record + a DUAL paragraph (one SCC predicate, every column) |
| `loremaster/tests/test_blocks_edge.py:2004` | re-keyed prose — same docstring, same DUAL paragraph |
| `loremaster/tests/test_blocks_edge.py:2049` | re-keyed — failure message rewritten: a legacy loop must not mask the minted row's cycle (am-17 §13.2), no bounded closure |
| `loremaster/tests/test_blocks_edge.py:2052` | re-keyed — same failure message ('ESC-1's bounded read must KEEP the drop-loop' removed) |
| `loremaster/tests/test_blocks_edge.py:2266` | DELETED as certifying FORK A — `test_the_write_paths_rows_READ_is_BOUNDED_by_the_ancestor_CLOSURE` (and its only helper `_blocked_noise_traffic`), DUAL note in its place |
| `loremaster/tests/test_blocks_edge.py:2268` | DELETED as certifying FORK A — `test_the_write_paths_rows_READ_is_BOUNDED_by_the_ancestor_CLOSURE` (and its only helper `_blocked_noise_traffic`), DUAL note in its place |
| `loremaster/tests/test_blocks_edge.py:2274` | DELETED as certifying FORK A — `test_the_write_paths_rows_READ_is_BOUNDED_by_the_ancestor_CLOSURE` (and its only helper `_blocked_noise_traffic`), DUAL note in its place |
| `loremaster/tests/test_blocks_edge.py:2276` | DELETED as certifying FORK A — `test_the_write_paths_rows_READ_is_BOUNDED_by_the_ancestor_CLOSURE` (and its only helper `_blocked_noise_traffic`), DUAL note in its place |
| `loremaster/tests/test_blocks_edge.py:2281` | DELETED as certifying FORK A — `test_the_write_paths_rows_READ_is_BOUNDED_by_the_ancestor_CLOSURE` (and its only helper `_blocked_noise_traffic`), DUAL note in its place |
| `loremaster/tests/test_blocks_edge.py:2283` | DELETED as certifying FORK A — `test_the_write_paths_rows_READ_is_BOUNDED_by_the_ancestor_CLOSURE` (and its only helper `_blocked_noise_traffic`), DUAL note in its place |
| `loremaster/tests/test_blocks_edge.py:2294` | DELETED as certifying FORK A — `test_the_write_paths_rows_READ_is_BOUNDED_by_the_ancestor_CLOSURE` (and its only helper `_blocked_noise_traffic`), DUAL note in its place |
| `loremaster/tests/test_blocks_edge.py:2320` | DELETED as certifying FORK A — `test_the_write_paths_rows_READ_is_BOUNDED_by_the_ancestor_CLOSURE` (and its only helper `_blocked_noise_traffic`), DUAL note in its place |
| `loremaster/tests/test_blocks_edge.py:2361` | re-keyed prose — DEPENDENCY_FREE leg's docstring: growth with dependency-BEARING rows is now the ruled design (§14.2) |
| `loremaster/tests/test_blocks_edge.py:2362` | re-keyed prose — DEPENDENCY_FREE leg's docstring: growth with dependency-BEARING rows is now the ruled design (§14.2) |
| `loremaster/tests/test_blocks_edge.py:2364` | re-keyed prose — DEPENDENCY_FREE leg's docstring: growth with dependency-BEARING rows is now the ruled design (§14.2) |
| `loremaster/tests/test_blocks_edge.py:2392` | re-keyed — DEPENDENCY_FREE leg's failure message points at §14.2, not the deleted pin |
| `loremaster/tests/test_blocks_edge.py:9253` | re-keyed — WB-D proof-recipe comment kept as record + a DUAL line (closure pin deleted; WB-D targets the one-statement read again) |
| `loremaster/tests/test_blocks_edge.py:9256` | re-keyed — WB-D proof-recipe comment kept as record + a DUAL line (closure pin deleted; WB-D targets the one-statement read again) |
| `loremaster/tests/test_blocks_edge.py:9257` | re-keyed — WB-D proof-recipe comment kept as record + a DUAL line (closure pin deleted; WB-D targets the one-statement read again) |
| `loremaster/tests/test_cycle_write_path_04b3.py:1` | unrelated-in-place — module title naming 04b-3's escalations; no edit (the DUAL bullet below covers it) |
| `loremaster/tests/test_cycle_write_path_04b3.py:15` | re-keyed — a DUAL bullet added above: FORK A and variant D overturned (§13/§14); the bullet kept as 04b-3 history |
| `loremaster/tests/test_cycle_write_path_04b3.py:18` | same — covered by the DUAL bullet (names the deleted pin as deleted) |
| `loremaster/tests/test_cycle_write_path_04b3.py:21` | same — covered by the DUAL bullet |
| `loremaster/tests/test_cycle_write_path_04b3.py:212` | re-keyed — 'the ESC-1 bounded-read rework' → 'the guard-read rework' |
| `loremaster/tests/test_cycle_write_path_04b3.py:220` | re-keyed — the guard's read is every blocked_by column, one statement (§14.2) |
| `loremaster/tests/test_query_tasks_bounded.py:121` | unrelated — wave r5's query_tasks ESC-1; no edit |
| `loremaster/tests/test_query_tasks_bounded.py:126` | unrelated — wave r5's query_tasks ESC-1; no edit |
| `loremaster/tests/test_query_tasks_bounded.py:1559` | unrelated — wave r5's query_tasks ESC-1; no edit |
| `loremaster/tests/test_readonly_guard.py:10` | unrelated — packet 39's harness-recut ESC-1; no edit |
| `loremaster/tests/test_readonly_guard.py:18` | unrelated — packet 39's harness-recut ESC-1; no edit |
| `loremaster/tests/test_tool_allowlist.py:670` | unrelated — another packet's FORK A (identity/preamble line); no edit |
| `loremaster/tests/test_trace_telemetry.py:129` | unrelated — telemetry `ok`-column ESC-1 (d0f84d0); no edit |
| `loremaster/tests/test_trace_telemetry.py:780` | unrelated — telemetry `ok`-column ESC-1 (d0f84d0); no edit |
| `loremaster/tests/test_trace_telemetry.py:832` | unrelated — telemetry `ok`-column ESC-1 (d0f84d0); no edit |
| `scripts/coldaudit_cycle_04b3_fork_a_refute.py:17` | archived — one-line SUPERSEDED header (FORK A overturned, `_bounded_dependency_graph` deleted); history only |
| `scripts/coldaudit_cycle_04b3_fork_a_refute.py:18` | archived — same header |
| `scripts/coldaudit_cycle_04b3_fork_a_refute.py:20` | archived — same header |
| `scripts/coldaudit_cycle_04b3_fork_a_refute.py:23` | archived — same header |
| `scripts/coldaudit_cycle_04b3_fork_a_refute.py:160` | archived — the call to the deleted method; a run raises AttributeError (loud), the header says why |
| `scripts/cycle_coexisting_legacy_soundness_probe.py:21` | archived — one-line SUPERSEDED header (variant D and ESC-1's bounded read gone) |
| `scripts/cycle_coexisting_legacy_soundness_probe.py:23` | archived — same header |
| `scripts/restore_prod_dump.py:49` | unrelated — packet 64 amendment 6 FORK A (store ports); no edit |

Query-count pins: `test_the_cycle_WALK_is_ONE_round_trip_however_DEEP_the_chain` (R7) needs no re-key — it counts round trips, and the one-statement read is one; `test_the_WRITE_paths_rows_READ_does_NOT_grow_with_the_DEPENDENCY_FREE_population` keeps its assertion (the new read filters `array::len(blocked_by) > 0`). No other test or script in the tree names the deleted symbols (grep, rename exhaustiveness — the lore-honest grep case).

### Receipts (§14)
Declared BEFORE any run, from `--collect-only --run-parked` on `fw14/base` (14 new node ids): RED at HEAD = 7
(`/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/c58r53/fw14/declared_red.txt`): `test_636_…`, `test_635_S_…[40_links]`, `test_635_H_…[40_links]`, `test_634_…`,
`test_graph_large_…[shrunk_below_the_fixture]`, `…[shipped]`, `test_a_BATCH_KEY_cycle_is_served_in_the_PERSISTED_direction_…`;
GREEN at HEAD = 7 (both 3-link controls, `test_638_i` ×4, `test_638_ii`). Targeted set = `fw13/set.txt` (34 files: every
covering suite of `tasks.py`'s changed symbols plus the two edited test files; the two scripts carry comment headers only).
All runs through `haiku-runner`, cgroup-capped (`MemoryMax=16G`), `-n 8 --timeout=300 --run-parked`, store :18000.

| run | tree | command / log | count | attribution |
|---|---|---|---|---|
| 1 RED at HEAD | base, HEAD `b99f178` (TREE line missing: `tree_id.sh` was called without its argument; fixed for runs 3–5) | `fw14/run_base.sh` → `fw14/run_base.log`, EXIT=1 | 38 failed, 2740 passed, 1 skipped | 7/7 declared reds RED for the ruled reason; 30 parked `packet-64b-i-contract`; **1 undeclared: `test_638_i[create_many]` — MY fixture defect** (2 stored rows → only 2 insertion orders, the leg's own `>= 3` assert fired). Fixed: a third stored row `z [q]`. |
| 2 SAT | ref, HEAD + `ref_delta_fw14.py` v1 (wrapper) | `fw14/run_ref.sh` → `fw14/run_ref.log`, EXIT=1 | 36 failed, 2745 passed | 7/7 declared GREEN; 30 parked 64b-i; `638_i[create_many]` (the fixture, above); 5 from MY REFERENCE'S SHAPE (renamed `_supersede_task_under_lock`): the derived CAS/RELATE/root-verb registries and `test_supersede_source_calls_BOTH_shared_blocks_edge_prechecks` |
| 3 RED re-run (fixture fix) | base, TREE `6e61cae4…` | `fw14/run_base2.sh` → `fw14/run_base2.log` (its RAN line reads `run_base.sh`: my sed did not rewrite the echo), EXIT=1 | 6 failed, 21 passed (fix-wave file only) | exactly the 6 declared reds of this file, each for its reason: `AttributeError` no `TASK_GUARD_GRAPH_LARGE_ROWS` ×2 · 20 of 20 repeats `['ok','ok']` with a written 4-cycle · `D was re-anchored` · `DID NOT RAISE TaskCycleError` · `TxnDomainRejectionError` (closure read exceeded `TIMEOUT 5s`); `638_i[create_many]` GREEN |
| 4 SAT (decorator) | ref v2 | `fw14/run_ref2.sh` → `fw14/run_ref2.log` (header clobbered by the runner's own redirect; count line read by me), EXIT=1 | 31 failed, 2747 passed | 7/7 GREEN; 30 parked; 1 reference shape: `r4_state[supersede_task -> supersede_task]` fired from the decorator's `serialised` frame |
| 5 SAT | ref v3 (lock as `async with` inside `supersede_task`'s own body), TREE `650ea234…` | `fw14/run_ref3.sh` → `fw14/run_ref3.log`, EXIT=1 | **30 failed, 2748 passed, 1 skipped** | **0 attributable**: all 30 are `packet-64b-i-contract` parked reds (`AppContext.findings()` `capability=` / `arm_finding_identity` absent); 0 unowned |

Runs used: 5 (2 more than the budget): one re-run for my own fixture defect, two for the reference's shape. **What the
two reference shapes tell the builder:** the pre-existing derived-domain pins (`test_reanchor_58_r4_state`, `r3_cas_seam`,
`r3_relate`) constrain WHERE §14.3's lock goes: inside `supersede_task`'s own frame. A wrapper method or a decorator
reddens them. That is the existing contract working, not this one over-firing; a correct build in the body passes.
`loremaster.__file__` in every run is inside its own copy (lines 4–5 of each log).

Reference (a SAT host, NOT a spec): `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/c58r53/fw14/ref_delta_fw14.py` md5 `9eacded6cf5819a80b0e32616d248eac`: the one-statement
column read (`SELECT record::id(id) AS id, blocked_by FROM task WHERE array::len(blocked_by) > 0`) for both call sites,
`_bounded_dependency_graph` + `_CLOSURE_START_PARAM` deleted, `TASK_GUARD_GRAPH_LARGE_ROWS = 20_000` + one WARNING from
the boot's existing `_read_mirror_state` columns, `self._supersede_lock` around `supersede_task`'s body, and the batch-key
path reversed when its first step is not row -> blocker.

Gates on the pinned base copy (TREE `6e61cae4…`, after the fixture fix): `--currency --legs typecheck,ruff` EXIT=1 =
typecheck RED_ADJUDICATED (50 residuals, none in a file I touched: all 64b-i's) · ruff GREEN · pytest NOT_RUN (the leg
filter, #621); RED_ORPHANED 0 for the legs run. `--verify-registry` EXIT=0. Registry: `packet-58-fixwave` rewritten:
its 17 HEAD ids removed (measured; the directive said 26), the 7 declared reds added, `active: true`.

### Package survey (§14)
| mechanism | libraries evaluated | what I READ | verdict |
|---|---|---|---|
| concurrent start of two coroutines | `asyncio.gather` (stdlib 3.12) | its use already in this suite and the stdlib signature `gather(*aws, return_exceptions=False)` | replace (used) |
| cycle witness | `graphlib.TopologicalSorter` via `find_blocked_by_cycle` | `tasks.py::find_blocked_by_cycle` body (`CycleError.args[1]`) | replace (used; independent of the SCC predicate) |
| insertion-order permutations | `itertools.permutations` / `islice` | stdlib | replace (used) |
| lock / WARNING / one-statement read | — | §14.2/§14.3 rule them; production, not contract | n/a (the builder's) |

Odoo-20 portability: n/a — no Odoo seam touched.

### Realism-&-independence checklist (§14)
- ☑ Production-realistic inputs: the audit's measured worlds (300 stragglers, 40 links past the 32 bound, the 20/20 race).
- ☑ Independent expected values: the ruled constant (20,000), the audit's counts, a graphlib witness.
- ☑ Seam coverage: the boot heal, the live supersede and the tool seam each driven through their real door.
- ☑ Magnitude bound: `test_636` heals exactly 300 of 300; graph_large count == 1.
- ☑ Shared conventions: `TXN_ROW_WARN_THRESHOLD` measured (`measure_heal_shape`), event names as constants.
- ☐ Hostile free text: not applicable, no free-text render beyond ids.
- ☑ Input accounting: 636 accounts every straggler (healed); 634 accounts both supersedes (exactly one each fate).

### Decisions for the lead
1. `TASK_GUARD_GRAPH_LARGE_ROWS` is the constant's name the pin reads (§14.2 names the bound, not the symbol).
2. The FORK A rows-read pin is DELETED (with `_blocked_noise_traffic`, its only caller); its R7 half is
   `test_the_cycle_WALK_is_ONE_round_trip_however_DEEP_the_chain`, untouched.
3. ⚠ Raised, not acted on: `test_blocks_edge.py::TestSupersedeCarriesBlockedBy174::test_supersede_source_calls_BOTH_shared_blocks_edge_prechecks`
   (pre-existing) reads `supersede_task`'s SOURCE. It reddened under a wrapper-shaped lock, so it is a spelling pin under
   the global §Tests rule. Not mine to convert in this brief. Does the lead want it routed?

### Commit-ready paths (§14; I staged and committed nothing)
- `loremaster/tests/test_reanchor_58_fixwave.py` (the §14 legs)
- `loremaster/tests/test_blocks_edge.py` (the arrow pin; the FORK A rows-read pin and `_blocked_noise_traffic` deleted with a DUAL note; prose re-keys)
- `loremaster/tests/test_cycle_write_path_04b3.py` (DUAL bullet and prose re-keys)
- `scripts/coldaudit_cycle_04b3_fork_a_refute.py`, `scripts/cycle_coexisting_legacy_soundness_probe.py` (one-line SUPERSEDED headers)
- `scripts/pending_contracts.yaml` (`packet-58-fixwave` rewritten)
- `REPORT-contract-58-r53.md` (this section)
Unrelated dirty files in the live tree that I did not touch: `loremaster/loremaster/store/surreal.py`, `loremaster/loremaster/tasks.py`, `scripts/test_scratch_copy.py`, `scripts/test_wrong_builds.py`.

## §CLOSEOUT — the second delta audit's contract-side fix-up (lead #20099; base HEAD `9cdc3fd`, production == `8679385`)

**BRIEF CONFLICT: "each new pin is red on its wrong build (one mutation run each)" — refused per tdd-contract role
boundary.** Building and running wrong builds is the contract-adversary's job; the brief quotes no dated operator
grant. Everything else in #20099 is done. What I can offer instead is analysis, plus the audit's own measurements:
- F4 pin: the audit's verify-batch ran ca58d's program on WB5 (`d_WB5b.log`: 4 hash seeds → 4 digests; correct build
  1 digest). My pin runs the same 3,000 worlds and adds the served sentence to the digest, so WB5 still separates.
  **Not run by me.**
- F6 pin: the audit's S `m5.log` / verify `e3_mut.log` show that dropping `source=` makes the record read the
  index writer's default. My pin asserts `source == 'task_ledger'` on every record, so that build reddens.
  **Not run by me.** The adversary should run both.

### Items
| # | audit | done | receipt |
|---|---|---|---|
| F1 (#641) | the re-open instrument cannot run | `scripts/probe_guard_input_58.py` (new): §INSTRUMENT-4 ported to `TaskLedger._read_dependency_graph`; legs full / mirror / scc, each with a control that prints `ok`/`CONTROL FAILED` (exit 1 on any failure); `--tests-dir` parameter (default: the tests dir beside the script); store pinned to `probe_hub_txn_58.URL` (:18000), asserted | `co/probe_guard_input.log` (TREE `04e37044…`, EXIT=0) |
| F2 | registry bound not discharged | `packet-58-fixwave` DELETED (21 lines incl. its comment header); its 7 ids re-checked green at HEAD in the run below | `co/verify_registry.log` EXIT=0 |
| F4 (#638) | WB5 survives `test_638_i` | NEW `test_638_i_the_cycle_answer_is_identical_across_HASH_SEEDS`: 3,000 worlds (ca58d's generator, credited) in 4 interpreters, `PYTHONHASHSEED` 0–3; rows, cycles and served sentences digested; non-vacuity: hits > 0. The in-process pin's docstring corrected: it kills insertion-order dependence, NOT WB5 | green below |
| F6 (#628 trigger) | attribution unpinned | NEW `TestATaskLedgerTransactionIsAttributedToTheTaskLedger::test_a_supersede_over_the_shrunk_threshold_records_source_task_ledger`: a supersede re-anchoring 2 dependents under `TXN_ROW_WARN_THRESHOLD = 0`; ≥1 WARNING record, every one `source == 'task_ledger'` | green below |
| F9 | archived header | `docs/plans/v2/receipts/2026-11-09-packet58/coldaudit_cycle_04b3_fork_a_refute.py`: "line 161" → the call named by symbol plus "line 171 at 9cdc3fd" (verified by grep); "the lead moves it … at commit" → "Moved here from `scripts/` in 8679385." Line count unchanged, so 171 stays true | grep |

### Probe numbers (F1; :18000, cgroup-capped, one run)
| N | full (`_read_dependency_graph`) | mirror (`_read_mirror_state`) | scc (one proposed row) | controls |
|---|---|---|---|---|
| 300 | 0.004 s, 300 rows | 0.007 s | 0.001 s, 0 hits; planted cycle 1 hit | 3/3 ok |
| 20,000 | 0.080 s, 20,000 rows | 0.151 s | 0.117 s, 0 hits; planted cycle 1 hit | 3/3 ok |

### Receipts
- Green at HEAD (`co/run_green.sh` → `co/run_green.log`, haiku-runner, TREE `78674755…`, `loremaster.__file__` in
  the copy): **30 passed, EXIT=0**: `test_reanchor_58_fixwave.py` (29 collected, both new pins among them, listed by
  `--collect-only`) + the arrow pin = all 7 ex-registry ids.
- Currency `--legs typecheck,ruff` on the copy (`co/currency.log`, TREE `78674755…`): typecheck RED_ADJUDICATED
  (50 residuals, all `packet-64b-i-contract`; `typecheck.sh` lists no error in any file I touched) · ruff GREEN ·
  pytest NOT_RUN (leg filter, #621). **RED_ORPHANED 0** for the legs run.
- Runs used: 1 pytest run + 1 probe run (+ the currency legs).

### Paths (nothing staged or committed)
`scripts/probe_guard_input_58.py` (new) · `scripts/pending_contracts.yaml` · `loremaster/tests/test_reanchor_58_fixwave.py` ·
`docs/plans/v2/receipts/2026-11-09-packet58/coldaudit_cycle_04b3_fork_a_refute.py` · this report.
