brief-base v27 read
brief project v7 read

state: done
deviations: (1) before/after importing-test runs were done inline by me, not a haiku-runner — the before-run needed the six files swapped to HEAD and restored (byte-exact, sha256 -c: 0 mismatches), a sequence I had to own. (2) cycle probe sites 147/160: the before-run crashed at the 164 site first, so their before-values are derived, not printed (see table).
Packages considered: none — no mechanism specified (14 call-site wraps, no new code).
Odoo-20 portability: n/a — no Odoo seam touched
Reuse ledger: 0 new symbols (REUSED `loremaster.store._txn.one_statement_result`, `_txn.py` R2 selection rule, read via lore_get_symbol)
Graded: n/a — builder report
decisions-needed: none
Pointers: §Receipt table · §Importing tests · §Gate receipts · §Residuals

## Routing table
| step | tier | who | reason |
|---|---|---|---|
| 6 probe runs before / after | inline (parallel shell batch) | me | I must judge each value; 6 runs, ~1 min |
| 14 edits | inline | me | one Python substitution script (asserts each old string matches once), `scratchpad/fix616/apply_edits.py` |
| importing-test runs before/after | inline | me | file swap sequencing (deviation 1) |
Fan-out: haiku 0 · sonnet 0 · peak 0

## Store safety
All six probes resolve URL `ws://127.0.0.1:18000/rpc` (hardcoded in `probe_read_filter_63`, `probe_dnd_defense_objects`, `probe_supersede_throw_rollback`; `_surreal_harness.DEFAULT_URL` for the rest, with no `LORE`/`SURREAL` env var set in my shell; `cycle_coexisting…` asserts 18000 and refuses 18500). No credentials printed.

## Change
Measured at HEAD `9bc5807`. Each site routes through `one_statement_result` (imported from `loremaster.store._txn`); no script-local helper. 6 files, 31 insertions / 26 deletions.

## Receipt table (before = unchanged probe at HEAD against :18000; after = edited)
Logs: `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/fix616/{before,after}/<probe>.log`. Exit: every probe EXIT=1 before, EXIT=0 after.

| site (by content) | before | after | seeded fact that says which is right |
|---|---|---|---|
| read_filter_63 · P4 `leak_rows` | `[]` → "LEAK GATE FAILED" | `['message:x_ap']` | seed: x_ap admitted, x_other excluded |
| read_filter_63 · P6 `none_key_count` | `None` → "COEXISTENCE FAILED" | `2` | seed: two manual NONE-key keeps |
| drain_63b_ii_b · `_seen_state` (187) | `[]` (both printed states) | `[('message:md_dirty', False), ('message:md_good', False)]` then `[mc_g1 True, mc_g2 True]` | seeded dirty/good edges |
| drain_63b_ii_b · `_ack_note_of` (201) | not printed before (probe crashed first at 440); site is the same `isinstance(rows[0], dict)` shape → returns None | `{'ack_note': 'acked by probe', 'acked': True}`; `acked=False ack_note=None` after refusal, `acked_count=1 stored-note-len=4000` after at-cap | seeded ack |
| drain_63b_ii_b · `seq_of_m_ap` (440) | `TypeError: list indices must be integers` (crash) | probe completes; C-control writer refuses 4001-char note, accepts 4000 | seeded message m_ap |
| governed_63c · `_agent_names_present` (255) | `real-role accepted+written=False` → "C-CONTROL FAILED" | `=True`, refusals wrote `[]` | seeded blank/real role |
| governed_63c · `stamped_after` (417) | `0` | `5` | 5 seeded agent rows stamped by whole-window backfill |
| governed_63c · `stamped2` (435) | `stamped now=0` → "C2-control FAILED" | `5` | same seed |
| governed_63c · `remaining_none` (546) | `0` ("0 = total denial" false clear: errored=True but 0 remain) | `4` with `errored=True` | seeded briefs reset to scope NONE; abort leaves them NONE |
| dnd_defense · `_q` (211) | Q1 `None`; Q2a–d `returned []`, "MISSING required rows" ×4 | Q2a–d return `stat_block:` rows incl. `sb_rakshasa`/`sb_golem`; Q3a `['stat_block:sb_demon']`; Q4a `['stat_block:sb_rakshasa','stat_block:sb_wraith']` | seeded KNOWN rows sb_* |
| cycle_coexisting · `before` (147) | `len()` = 1 (list of one statement result); not printed, crash came first | `rows before=4` | 4 seeded task rows |
| cycle_coexisting · `after` (160) | `len()` = 1, so `landed = (1 == 1+1)` is False for the wrong reason; not printed | `after=4`, `new task landed? False` (guard refused) | refused create ⇒ 4 = 4 |
| cycle_coexisting · `served` (164) | `TypeError: list indices must be integers` (crash at `row["id"]`) | `new_id in store? False` (iterates 4 ids) | seeded ids |
| supersede_throw_rollback · `_row_exists` (101) | always True → "PROBE FAILED … (a) witness_a SURVIVED" | witness absent after rollback; leg (b) positive control (matching close COMMITS) still True; "PROBE OK" | rollback leaves no witness |

Positive controls: every after-value is a seeded count or present row (2, 4, 5, `x_ap`, named ids), none is 0/empty. Not reached: **none** — all 14 sites executed. Caveats: cycle 147/160 and drain 201 before-values are derived from the code shape plus the crash that preceded them, not printed.
Observation (not mine to fix): governed_63c "C2-control" stamps 5 after the whole-window backfill already stamped all 5, so that control no longer discriminates beyond what C2 shows.

## Importing tests (before vs after)
Set: `test_secret_typing.py`, `test_comms_schema.py`, `test_blocks_edge.py`, `test_message_governed_ddl_63b_ii_a.py` — the only test files that name any of the six probes (grep of the six names over `loremaster/` and `scripts/`; grep, because it is a non-symbol textual seam). `lore_impact(loremaster.tests._governed_contract)` returned a 15-entry covering list with 3303 elided, not usable. `_governed_contract.py` mentions the probes only in docstrings.
- before (HEAD copies of the six probes): **2 failed, 532 passed**
- after: **2 failed, 532 passed** — same two node ids: `test_secret_typing.py::TestSigninCredentialsIsTheOneUnwrapSeam::test_no_module_outside_the_seam_hand_rolls_the_payload`, `test_blocks_edge.py::TestTheBackfillMirrorsADependencyOnASUPERSEDEDTask::test_a_legacy_dependency_on_a_SUPERSEDED_task_is_STILL_MIRRORED`. I did not investigate either; neither failure is in my diff (identical before). Reason of the first not read.
- STOP condition (importing test green on a defective site): not triggered — none of the four tests executes a probe query site (they scan or reference the probe sources / use `_governed_contract`; MEDIUM confidence, from import and reference grep, not a trace).

## Gate receipts
| gate | command | log | EXIT | count | TREE |
|---|---|---|---|---|---|
| pytest before | `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run pytest <4 files> -q -n 8 -p no:cacheprovider` (HEAD probes swapped in) | `…/scratchpad/fix616/tests_before.log` | 1 | 2 failed, 532 passed | see log header |
| pytest after | same command | `…/scratchpad/fix616/tests_after.log` | 1 | 2 failed, 532 passed | d8602d1ab2a17e99… |
| ruff | `uv run ruff check <six files>` | `…/scratchpad/fix616/final_ruff.log` | 0 | All checks passed | 7d6f3136be91… |
| typecheck | `scripts/typecheck.sh` | `…/scratchpad/fix616/final_typecheck.log` | 1 | 0 errors in the six files (known red elsewhere: loremaster/tests 58-owned symbols; not compared to a HEAD run, none of the six is named) | see log header |
Note: DIRTY_FILES in the headers includes other agents' files. Probe logs have no tree header (probe runs, not gates).

## Residuals
- `esc1_write_path_cycle_closure.py` (8 sites): untouched, rides am-8 §5, per brief.
- The two failing tests above (pre-existing at the same node ids).
- Lead action per §11.2: read this diff, re-run one probe at random, then resolve #616 with the commit.
