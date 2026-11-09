brief-base v27 read · brief project v7 read
state: done-with-deviations
- DEVIATION 1: test_a_ledger_that_SWALLOWS_its_backfill_failure_is_CAUGHT is NOT green. Its first assertion (control_observation == 2) now passes (edges=2, was -1). It then fails on a LATER assertion: "the straggler-heal door runs AFTER the swallowed backfill and must still fail loud ... assert 4 not in [2,3,4]" (the swallowed doors k=2,3,4 RETURNED; heal door k=5 does not exist). That assertion needs packet 58's heal, so the brief's "must go GREEN" cannot hold before 58. Two readings: (a) the test is meant to stay red until 58 (same as the door-count test) - I assume this; (b) the test should be green today and is wrong. Lead rules; no test edited.
- DEVIATION 2: baseline had a THIRD red the brief did not name: TestThisInstrumentIsTYPECHECKED::test_mypy_is_clean... (test_forgery_door_sweep.py:42 "loremaster.tasks has no attribute SupersedeResult", a 58 symbol). Unchanged by my fix.
Packages considered: none - no mechanism specified
Odoo-20 portability: n/a - no Odoo seam touched
Reuse ledger: 0 new symbols (1 reuse, see DRY)
Graded: n/a - build report
decisions-needed: DEVIATION 1 (which reading); route the CLASS-HITS below.
Fan-out: haiku 2 (sweep, runners) · sonnet 1 (verdict draft) · peak 2

## Routing table
| step | tier | who | reason |
| .query( sweep (112 hits) | 1 | haiku-worker | literal grep, coverage line |
| baseline + final test/ruff/typecheck | 1 | haiku-runner | test runs |
| 109 hit verdicts | 2 | sonnet | span-decidable vs key; I sampled 4 rows (probe_supersede_throw_rollback:101, esc1:483, probe_store_error_classes_07:112, probe_read_filter_63:660): agree |
| the 1-function edit | inline | me | 14 lines |
Grep fallback (said out loud): .query( SDK3 result-shape exhaustiveness = §10.1's named rename-class sweep; lore_search cannot enumerate call sites.

## Change
scripts/forgery_door_sweep.py::_blocks_edge_count: both reads (INFO FOR DB, SELECT count()) now go through loremaster.store._txn.one_statement_result (lazy import, same idiom as its BLOCKS_RELATION import). No local unwrap.

## DRY ledger
| new symbol | where I looked | returned | disposition |
| (none new) unwrap of one-statement result | lore_get_symbol one_statement_result; §10.1 names it | _txn.py:769 R2 selection rule | REUSED loremaster.store._txn.one_statement_result |

## Before / after (test_forgery_door_sweep.py, 20 tests)
- before: 3 failed, 17 passed (/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/fix614/baseline.log, TREE=c0bba531...). Swallow test failed on control_observation (-1 != 2). Door-count test: "derived door set ... is 4, not the 5 ... Doors seen: [execute_transaction, execute_read_transaction, run_query, execute_transaction]".
- after: 3 failed, 17 passed. Door-count test: SAME message (4 != 5), does not fail on control_observation. Swallow test: moved past control (see deviation 1). mypy test: same SupersedeResult error.
- Counts equal because the swallow test relocated its failure, not because nothing changed.

## Gate receipts
| gate | command | log | EXIT | count | TREE |
| pytest | systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run pytest scripts/test_forgery_door_sweep.py -q -n 4 -p no:cacheprovider | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/fix614/final_pytest.log | 1 | 3 failed, 17 passed | ae158a4f... |
| ruff | uv run ruff check scripts/forgery_door_sweep.py | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/fix614/final_ruff.log | 0 | All checks passed | 00a07ca4... |
| typecheck | scripts/typecheck.sh | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/fix614/final_typecheck.log | 1 | errors only in loremaster/tests/* 58 symbols (SupersedeResult, _guarded_append_fragment, max_reanchor_dependents, TxnCasLostError, StragglerHealPackerError...); none in scripts/forgery_door_sweep.py (grep count 0). Not compared against a HEAD run: lead may diff. | 45b1f28e... |
Note: DIRTY_FILES=4 includes scripts/pending_contracts.yaml (not mine).

## CLASS-HITS (§CLASS-HITS; sweep: files_opened=64 hits=112 (/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/fix614/query_sweep.txt); forgery_door_sweep.py's 3 handled here; 109 verdicts in /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/fix614/query_verdicts.txt: 62 OK-DISCARDED, 25 OK-SHAPE-AGNOSTIC, 22 SAME-CLASS, 0 UNSURE). Not fixed (no failing test; outside writable set):
- scripts/probe_drain_read_63b_ii_b.py:187 | SAME-CLASS | isinstance(row, dict) over rows; yields empty under list-per-statement
- scripts/probe_drain_read_63b_ii_b.py:201 | SAME-CLASS | rows[0] dict-checked as a row
- scripts/probe_drain_read_63b_ii_b.py:440 | SAME-CLASS | seq_of_m_ap[0]["seq"] used as a row
- scripts/probe_governed_63c.py:255 | SAME-CLASS | iterates rows, row.get(name) with isinstance dict
- scripts/probe_governed_63c.py:417 | SAME-CLASS | fed to _scalar: rows[0] dict-check; yields None then `or 0`
- scripts/probe_governed_63c.py:435 | SAME-CLASS | fed to _scalar: rows[0] dict-check; yields None then `or 0`
- scripts/probe_governed_63c.py:546 | SAME-CLASS | fed to _scalar: rows[0] dict-check; yields None then `or 0`
- scripts/probe_supersede_throw_rollback.py:101 | SAME-CLASS | bool(rows) as existence: non-empty list-per-statement always truthy
- scripts/probe_dnd_defense_objects.py:211 | SAME-CLASS | _q passthrough; callers use _rows(isinstance dict) and raw[0].get
- scripts/esc1_write_path_cycle_closure.py:170 | SAME-CLASS | iterates id_rows as rows with row["id"]
- scripts/esc1_write_path_cycle_closure.py:172 | SAME-CLASS | iterates column_rows as rows with row.get
- scripts/esc1_write_path_cycle_closure.py:184 | SAME-CLASS | info.get(tables) behind isinstance dict; INFO FOR DB list-shaped
- scripts/esc1_write_path_cycle_closure.py:188 | SAME-CLASS | iterates edge_rows as rows with row["b"]
- scripts/esc1_write_path_cycle_closure.py:246 | SAME-CLASS | not rows / rows[0].get('upstream') treats rows[0] as row
- scripts/esc1_write_path_cycle_closure.py:334 | SAME-CLASS | info.get(tables) behind isinstance dict; INFO FOR DB list-shaped
- scripts/esc1_write_path_cycle_closure.py:414 | SAME-CLASS | `not rows` emptiness check; list-per-statement never empty
- scripts/esc1_write_path_cycle_closure.py:483 | SAME-CLASS | len(deleted)==1 as row count; len is statement count
- scripts/probe_read_filter_63.py:660 | SAME-CLASS | leak_rows via _row_ids isinstance-dict filter; yields empty
- scripts/probe_read_filter_63.py:686 | SAME-CLASS | none_key_count via _scalar rows[0] dict-check
- scripts/cycle_coexisting_legacy_soundness_probe.py:147 | SAME-CLASS | len(result) used as row count before/after
- scripts/cycle_coexisting_legacy_soundness_probe.py:160 | SAME-CLASS | len(result) used as row count before/after
- scripts/cycle_coexisting_legacy_soundness_probe.py:164 | SAME-CLASS | iterates result as rows with row["id"]
Files: probe_drain_read_63b_ii_b, probe_governed_63c, probe_supersede_throw_rollback, probe_dnd_defense_objects, esc1_write_path_cycle_closure, probe_read_filter_63, cycle_coexisting_legacy_soundness_probe. All are probes/instruments; whether they are still run is unknown to me.
Fan-out note: the sweep file lives only in the scratchpad dir named by the brief.
