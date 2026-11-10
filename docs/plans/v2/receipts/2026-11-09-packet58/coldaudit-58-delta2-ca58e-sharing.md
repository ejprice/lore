# coldaudit-58-delta2-ca58e-sharing — packet 58 fix wave, SECOND delta audit, dimension: sharing by mutation + regression of every confirmed finding

(the routing table below was written first; the summary block and body follow it)

## ROUTING TABLE (written 2026-11-10 after the scratch copy, before the first sweep)
| step | tier | who | reason |
|---|---|---|---|
| scratch copy + provenance receipt | 1 | inline | one scripted command, output read whole |
| locate cycle pins / lock pin / guard-input consumers in the scratch copy (grep) | 1 | inline, one parallel batch | small, on the critical path, read whole; this agent has NO `Agent` tool, so no haiku-worker is reachable |
| declare expected-RED sets (`--collect-only --run-parked` + reading each test) | 3 | me | a mutation-proof verdict; never Haiku |
| mutation runs via `scripts/mutation_proof.py` | 1 | **inline: no `Agent` tool** (brief-base §3 "with no `Agent` tool … run inline. Say which") | |
| driving served refusals (#625 both, F5, #130(a), large_transaction source) | 3 | me | reading served text against a claim is a verdict |
| F6 / docstring regression reads (~8 items) | 2 → kept | me | a Sonnet draft would miss whether each docstring is TRUE of the new code, which needs the code read beside it |
| verdicts | 3 | me | |

Fan-out: haiku 0 · sonnet 0 · peak 0 (no `Agent` tool in this workflow agent's toolset).

## SUMMARY BLOCK
- brief-base v27 read · brief project v7 read · landmines recalled (k=50 returned 10, not cut off) · registered on lore_comms as `ca58e-sharing` (session pkt58-20261109, role auditor).
- State: **done-with-deviations**. Verdict for this dimension (graded 8679385, measured 2026-11-10): **NO-GO by the letter, on one item outside the product code (E-1); every sharing proof HELD and every confirmed product finding is FIXED.**
  - Sharing (all through `scripts/mutation_proof.py`, declared from `--collect-only` before the run, both ways): M1 `_read_dependency_graph` → `{}` (query kept) reddens exactly 21 declared pins over create_many / supersede / heal; M2 `find_row_blocked_by_cycles` → `{}` reddens exactly 33; M3 `find_blocked_by_cycle` → `None` reddens ONLY the 3 batch-key pins; M4 lock removed and M4b a fresh lock per call each redden ONLY the #634 pin. PROOF HELD ×5.
  - BC-r5-1 (`fragment_rows` ×2): 11 declared, PROOF HELD. BC-r5-2 (WARN ×3): 4 declared, PROOF HELD. #624 sample (`CAS_LOST_MARKER` respelled): PROOF HELD.
- Findings:
  - **E-1 major (non-product, CONFIRMED by run):** the `packet-58-fixwave` registry entry was not deleted when its build landed (am-17 §14.7 item 5). All 7 of its ids are green at 8679385, so the currency gate's pytest leg renders RED_ORPHANED with 7 SELF-DESTRUCT lines (`registry_currency.log`). This is the delta's receipts F1 class again, and it makes 8679385's commit claim "currency RED_ORPHANED 0" true only for legs that do not run pytest.
  - **E-2 minor (non-product, read):** §14.7 item 4's stale-prose rider is half done. The `server.py` batch-key comment still says "ONE cycle detector … both ledger-owned". Two docstrings this build made false: `find_row_blocked_by_cycles` Args `stored` ("the bounded ancestor closure of the proposed blockers") and `_skip_cycle_closing_rows` ("ONE closure read seeded by every proposed blocker").
  - **E-3 minor (non-product, measured):** no test pins the `store.apply.large_transaction` `source`. Dropping both the task ledger's `source=` and the extra's `"source"` key leaves 391/391 green (`m5.log`). My probe sees it (`m5_control.log`). The defaulted `source="index_writer"` mislabels any composer that forgets the kwarg, which is the exact #628 attribution the rider bought.
  - **E-4 minor (non-product, read):** D-3's secondary item is still open. `max_reanchor_dependents`' KNOWN BOUND docstring names no #628.
- Deviations: (1) test runs inline, since this agent has no `Agent` tool; (2) M2's first run (`m2_void_regex.log`) is VOID. My declaration regex also matched an unrelated same-named test in `TestTheRowExistencePolicyHasONEImplementation`. I removed that id by class identity and re-ran it as `m2b` (PROOF HELD), and say so here. (3) The #623 verifier's first run is void because I passed no copy-path argument (`f1_verify_void_noarg.log`). (4) I ran the gate's pytest leg over 2 files (`--maxprocesses=8`, cgroup-capped) to judge the registry. That is a targeted run, not the full suite.
- Packages considered: none — no mechanism specified (probes only). Odoo-20 portability: n/a — no Odoo seam touched. Reuse ledger: none (no production symbols).
- Graded: 8679385 · HEAD-at-report: 8679385 · SAME.
- Decisions needed: (a) E-1: delete the `packet-58-fixwave` entry (the contract author's job per §14.7 item 5) before the packet's full suite runs, or that full suite's currency is RED_ORPHANED by construction. (b) E-3: do we pin attribution and make `source` a required keyword? I would do both.
- Pointers: §PROVENANCE · §S1 · §S2 · §REGRESSION · §FINDINGS · §RESIDUALS · §INSTRUMENTS. Logs dir `LOGS/` = `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-sharing-logs/`. That directory is not durable. The counts these claims rest on are pasted here.

## §PROVENANCE (measured 2026-11-10)
- Copy: `scripts/scratch_copy.sh …/scratchpad/ca58e/ca58e-sharing` → EXIT=0, all four members resolved inside the copy. Then `git checkout 8679385 -- .`; `rev-parse HEAD` = `86793850c0563a52c9d4f74961ef522d444a2386`.
- `loremaster.__file__` = `…/ca58e/ca58e-sharing/loremaster/loremaster/__init__.py`. `tasks.__file__` and `_txn.__file__` are in the copy too.
- TREE ids:
  - `aafce77a…` = the pristine copy (5 untracked root REPORTs). baseline_cycle and M1–M4b ran on it.
  - `b7c0a4ee…` = the copy plus 2 untracked probes. served, secret, f1_verify, baseline_bc, bc1, bc2, mk_cas and registry_currency ran on it.
  - `512d319f…` = M5's mutated tree.
- After every run the copy's `git diff --stat` is empty, and each mutated file was restored byte-exact (`RESTORED_BYTE_EXACT` in every log).
- Store: TEST only (`ws://127.0.0.1:18000`, harness default). Every pytest ran under `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0` with `-n 8` or `-n 0` and `--timeout=300`. No empty selection: the runner exits 8 on an empty scope or an empty declared set.
- Parked: `--collect-only --run-parked` = 672 = the default collection over the cycle scope, so no parked ids are in it.
- lore: the scratch copy is unindexed. Covering tests were found by grep plus the AST lister `fn_hits.py` (from ca58d), which are rename-exhaustiveness and textual-seam cases, and I say so here. #563/#557 are why `lore_impact` was not used for the covering set.

## §S1 — sharing by mutation (cycle scope, 672 ids: test_blocks_edge, test_cycle_write_path_04b3, test_reanchor_58_fixwave, _r2_rulings, _r2_probes, _r3_convergence, test_supersede_reanchor_58, test_supersede_render_58, test_task_ledger, test_mcp_server::TestCreateManyDispatch)
- Baseline `baseline_cycle.log`: 654 passed, EXIT=0. That run was over 654 collected ids, before I added `_r2_probes`. The 672-id mutation runs show 651+21, 639+33, … = 672 with nothing else red.

| run | mutation | declared | result |
|---|---|---|---|
| M1 | `_read_dependency_graph`: query kept, then `return {}` | 21 | `m1.log` 21 failed, 651 passed · PROOF HELD |
| M2 | `find_row_blocked_by_cycles`: `return {}` first | 33 | `m2b.log` 33 failed, 639 passed · PROOF HELD (`m2_void_regex.log` VOID, Deviation 2) |
| M3 | `find_blocked_by_cycle`: `return None` first | 3 | `m3.log` 3 failed, 669 passed · PROOF HELD |
| M4 | `async with self._supersede_lock:` → `if True:` | 1 (#634) | `m4.log` 1 failed, 671 passed · PROOF HELD |
| M4b | → `async with asyncio.Lock():` (a lock that is never shared) | 1 (#634) | `m4b.log` 1 failed, 671 passed · PROOF HELD |

- M1's declared 21, by writer. Each was derived by reading the test: does the cycle close through a STORED row (red), or only among the pending rows (stays green)?
  - create_many: `…through_PERSISTED_tasks`, `…MINTED_cycle_COEXISTING_with_a_LEGACY_cycle`, and the in-test `test_MUTATION_the_batch_key_detector…` (its `_persisted_writers_refuse` needs stored rows for 3 of its 4 writers).
  - supersede: E3 ×2, 635_S ×2, 634, supersede_reanchor `test_refused_as_a_cycle_naming_it…` and `…backfill_mints_nothing`.
  - heal: A, B, C, E1 ×2, D2_i ×2, D2_ii, 635_H ×2, 638_ii.
  - **Stayed GREEN as predicted** (the cycle is wholly inside the pending rows, so the empty input cannot hide it): the self-loop, the batch of mutual IDS, the r2 CONTROLs ×2, the arrow pin, the FORMATTER pin, the existence-vs-cycle pin.
  - `create_task` has no pin and cannot have one. Its id is minted inside the verb, so no persisted row can name it (the contract's own note). (HIGH)
- M2's 33 = M1's 21 + the 12 that the in-memory or pending-only shapes need the PREDICATE for: self, batch IDS, BATCH_KEY class (`_ledger_cycle_error`), arrow (its persisted leg), FORMATTER, the cycle-is-not-existence pin, r2 CONTROL ×2, and 638_i ×4. So every writer asks the one predicate, and the input feeds it. (HIGH)
- M3: `test_a_BATCH_KEY_cycle_at_the_TOOL_SEAM…`, `test_a_BATCH_KEY_cycle_is_served_in_the_PERSISTED_direction…`, and `test_mcp_server::TestCreateManyDispatch::test_intra_batch_cycle…`. None of the persisted-row pins reddened. (HIGH)
- M4 and M4b: the lock is the only thing that serialises the pair. A per-call lock is as good as none, and the pin sees that. (HIGH)

## §S2 — BC-r5 and the marker sample (scope `scope_bc.txt`: 25 entries, 391 ids, using the ca58d-adapted probe `test_probe_sharing_ca58d.py`, md5 6c28ed5f8819…)
- `baseline_bc.log`: 391 passed, EXIT=0.
- **BC-r5-1** (`_txn.fragment_rows` doubles the un-annotated count; anchor and replacement `ca58/m1.*`; declared = ca58d's 11 ids, all collected at 8679385): `bc1.log` 11 failed, 380 passed · **PROOF HELD** · restored. (HIGH)
- **BC-r5-2** (`_log_transaction_size` compares against `3 *` the WARN threshold; `ca58/m2.*`. The anchor line survived this round's signature change, and matched once): `bc2.log` 4 failed, 387 passed · **PROOF HELD** · restored. (HIGH)
- **#624 sample** (`CAS_LOST_MARKER` = `"cas_lostq:"`, scope `scope_marker.txt`, 424 ids, declared `[test_P6_each_ruled_tier_and_the_deny_by_default[cas_lost]]`): `mk_cas.log` 1 failed, 423 passed · **PROOF HELD**. The other three markers were not re-run; `_txn.py` has no diff in cdf1ce4..8679385. (HIGH for CAS; MEDIUM by inference for the other three)

## §REGRESSION — every confirmed finding, one line each
| item | verdict | receipt |
|---|---|---|
| #623 (the heal writes a cycle) | FIXED (HIGH) | `f1_verify.log`, the first audit's `ca58/verify1-notes/probe_verify1.py <copy>`, EXIT=0. Plain and phantom variants: boots 1–3 leave `D ['X']`, each logs `straggler_would_close_cycle`; the live-supersede control is refused. Also M1/M2 heal legs. |
| #624 (markers spelled twice) | FIXED (HIGH) | §S2 mk_cas |
| #625 (both refusals, served text) | FIXED (HIGH, driven) | `served.log`. Hub: "…6 dependents; re-anchoring them composes 23 rows, over the 20-row transaction cap (the build-time bound admits at most 5 dependents) — refused, nothing changed. A hub near that size can instead time out without being refused (finding #628)." Packer: "straggler … alone composes 4 rows, over the 2-row heal chunk bound — the heal cannot pack it into one transaction", row_cap=2=live min. |
| #631 (a live supersede writes a cycle) | FIXED (HIGH) | E3 ×2 green at baseline. Red under M1 and M2. |
| #634 (concurrent supersedes) | FIXED in-process (HIGH) | The pin is green at baseline. M4 and M4b redden only it. The two-process bound is in the `supersede_task` docstring and the lock comment, and the finding is still open (residual R-3). |
| #635 (32-hop truncation) | FIXED (HIGH) | 635_S/H ×2 green at baseline. Red under M1 and M2. No depth constant remains in `_read_dependency_graph`. |
| #636 (boot fails at ~300 stragglers) | FIXED (HIGH) | `test_636_…300_stragglers…` green in `baseline_cycle.log`. |
| #638 (determinism, once before packing) | pinned and green (HIGH) | 638_i ×4 and 638_ii green. 638_ii reddens under M1, 638_i under M2. |
| F6 docstrings (first audit's list) | still TRUE (HIGH, read) | This round touched only `supersede_task` (re-indent plus the KNOWN BOUND paragraph) and `_refuse_a_cycle`'s R7 paragraph. Both are true of the new code. **New false prose → E-2.** |
| F7a `_still_claimable` | GONE (HIGH) | `git grep` at 8679385: 0 hits in `loremaster/` and `scripts/` |
| #622 | FIXED (HIGH, read) | `max_reanchor_dependents` cites `probe_heal_curve_58.py` part C with 3 rows. |
| F5 | FIXED (HIGH, driven) | "…a SUPERSEDED blocker can never resolve: block on the successor instead)" |
| #130(a) served schema | FIXED (HIGH, driven) | `status`: "…a status (or blocked) filter excludes SUPERSEDED tasks." (`blocked`'s own description does not say it; R-4) |
| #130(a) `query_tasks` docstring (D-2) | FIXED (HIGH, read) | It gains "SUPERSEDED rows are EXCLUDED whenever a status or a blocked filter is supplied…". True of `_query_rows`' `exclude_superseded or status is not None` clause. |
| batch-key arrow (blind F3) | FIXED (HIGH, driven) | `served.log`: "blocked_by cycle among batch keys: ka -> kb -> kc -> ka" with ka [kb], kb [kc], kc [ka], so row → its blocker. The arrow pin reddens under M3. |
| large_transaction source (sharing D-3) | FIXED, **unpinned** → E-3 (HIGH, driven) | `served.log`: `{'statement_count': 8, 'param_count': 12, 'row_count': 8, 'source': 'task_ledger'}` |
| stale "ONE shared detector" prose (sharing D-1 / blind F4) | **half done** → E-2 | `tasks.py` is fixed; `server.py` is not. |
| secret-seam scanner | GREEN (HIGH) | `secret.log` 1 passed, EXIT=0 |
| delta receipts F1 (registry bound not discharged) | **REGRESSED** → E-1 | `registry_currency.log` |

## §FINDINGS
### E-1 (major, non-product, CONFIRMED by run): the `packet-58-fixwave` registry bound outlived its build, so the currency pytest leg is RED_ORPHANED at 8679385
- `scripts/pending_contracts.yaml` at 8679385 still carries `id: packet-58-fixwave`, `active: true`, with 7 red_nodeids. Its own reopen_trigger says: "then every id below goes GREEN and this entry self-destructs and is deleted with the build". am-17 §14.7 item 5: the contract author "deletes the entry when the build lands". 8679385's stat touches no registry file.
- Run: `pending_contract_gate.py --currency --legs pytest -- loremaster/tests/test_reanchor_58_fixwave.py loremaster/tests/test_blocks_edge.py --maxprocesses=8 --timeout=300` under the cgroup cap (`registry_currency.log`, TREE b7c0a4ee). It renders `pytest RED_ORPHANED — 7 residual(s) with NO owner`, each line `SELF-DESTRUCT: adjudicated red … (bound 'packet-58-fixwave') is green — delete it with the fix.` (typecheck and ruff were NOT_RUN by my `--legs`; that is expected, not a finding.)
- The 8679385 commit body says "currency RED_ORPHANED 0". That is consistent only with a currency run that starts no pytest. The packet's full suite will render this RED_ORPHANED by construction.
- This is the same class as coldaudit-58-delta.md receipts F1, recurring one wave later. Fix: delete the entry (the ids are green).

### E-2 (minor, non-product, read at 8679385): §14.7 item 4's prose rider is half done, and this build made two docstrings false
- `server.py`, the comment above the create_many batch-key check: "⚠ ONE cycle detector and ONE refusal SHAPE, both ledger-owned (operator ruling **R6**…)". server.py is unchanged since cdf1ce4. M3 measures it false: the batch-key detector answers only the batch-key question.
- `tasks.py::find_row_blocked_by_cycles` Args: "stored: … — the bounded ancestor closure of the proposed blockers". Since §14.2 it is every dependency-bearing column (`_read_dependency_graph`).
- `tasks.py::TaskLedger._skip_cycle_closing_rows` docstring: "ONE closure read seeded by every proposed blocker". It now calls `_read_dependency_graph()`, which takes no seeds.
- Test prose, residual only: `TestTheCyclePolicyHasONEImplementation`'s class docstring ("neutralise it and BOTH shapes must stop being refused") and `test_intra_batch_cycle…`'s docstring ("R6 rules ONE cycle detector").
- The sweep was a bare grep over `loremaster/loremaster` (86 files) for `bounded_dependency_graph|CLOSURE_START|ancestor closure|closure read|ESC-1|FORK A|ONE cycle detector…`. Verdict per hit:
  - `__init__.py:5`, `governed.py:25`, `owner_stamp.py:10` and `surreal_schema.py:942` are unrelated (packet 62's ESC-1).
  - `tasks.py` ~2960 and ~2994 are true, because they name the replaced read as replaced.
  - `tasks.py` ~833 and ~2593 are FALSE (above).
  - `server.py` ~5328 is FALSE (above).

### E-3 (minor, non-product, measured): the #628 attribution has no pin, and its default mislabels
- M5 drops `source=_TASK_LEDGER_SOURCE` from `TaskLedger._apply`'s call AND `"source": source` from `_log_transaction_size`'s extra. Over the BC/telemetry scope (391 ids, which includes PR13, `test_surreal_apply::TestApplyTxnSizeTelemetry` and `test_sdk3_row_bound`): `m5.log` 391 passed, EXIT=0.
- Positive control (`m5_control.log`): with only the task ledger's kwarg dropped, my probe's attribution assertion fails ("a task-ledger record is not attributed"), because the record now says `index_writer`. The instrument can see the defect; the suite cannot.
- Consequence: a task-ledger supersede that crosses the WARN line can be attributed to the index writer. #628's re-open trigger then never fires even when its condition occurs, and every gate stays green. Fix: a behaviour pin (a supersede over the WARN line yields `source == "task_ledger"`; an index write yields `index_writer`), and make `source` a required keyword so a new composer cannot inherit another's name.

### E-4 (minor, non-product, read): `max_reanchor_dependents`' KNOWN BOUND docstring still names no finding
- It cites am-17 §4 and a trigger, but not #628. CLAUDE.md "WHEN YOU CANNOT CLOSE A HOLE, RECORD IT" wants the docstring to name the finding. This is D-3's secondary item; §14.7 item 4 ruled only the source.

## §RESIDUALS (NO ROUND unless the lead rules otherwise)
- **R-1 (oracle, HIGH):** the "no cycle written" oracle in 634 and 635_H (`_any_cycle`) and in fixwave A/B is `find_blocked_by_cycle`. Under M3 it is vacuous. Each of those pins still has a non-vacuous leg (the fates, the unchanged row, the skip record), so M3 did not need to redden them, and it did not.
- **R-2 (stale test prose, HIGH):** see E-2's last bullet, plus ca58d's R-5 (`test_supersede_source_calls_BOTH_shared_blocks_edge_prechecks`).
- **R-3 (ledger hygiene, MEDIUM):** finding #634 is open, as §14.7 rules, but its body still says "No docstring states this bound" and names no re-open trigger. An annotation would make the ledger say what the docstring says.
- **R-4 (served, LOW):** the `lore_tasks` `blocked` field's description does not say a blocked filter excludes superseded rows; only `status`'s does. A consumer reading `blocked` alone is not told.
- **R-5 (sharing bound, LOW):** the boot's legacy-loop record and `task.guard.graph_large` count from `_read_mirror_state`'s columns, which is a separate execution of the same `_DEPENDENCY_COLUMNS_STATEMENT`, not the guard's function. The statement text is shared, the call is not. This is §14.2 as ruled ("the first statement of `_read_mirror_state`").

## §INSTRUMENTS
- `run_mut.sh` is ca58d's `run_mut2.sh` (pasted in coldaudit-58-ca58-sharing.md §INSTRUMENTS lineage) with the S/C/L paths changed to `ca58e`. It is otherwise byte-identical.
- The mutation anchor/replacement pairs are in `LOGS/mut/`:
  - `m1`: anchor `        rows = self._as_rows(await self._query(_DEPENDENCY_COLUMNS_STATEMENT))`, replacement that line plus `        return {}`.
  - `m2` = ca58d `mA`; `m3` = ca58d `mB`.
  - `m4`/`m4b`: anchor `        async with self._supersede_lock:`, replacements `        if True:` and `        async with asyncio.Lock():`.
  - BC: `ca58/m1.*` and `ca58/m2.*`; the marker run: ca58d `mk_cas.*`.
- The declared sets are `LOGS/*_declared.txt`, cut from `collect_cycle.txt` by regex before each run. `m2_declared.txt` is the void one, and `m2b_declared.txt` = it minus the one unrelated id.
- M5 was hand-applied with a `cp -a` backup and an md5 restore check (`m5.md5_before/after`, `RESTORED_BYTE_EXACT`). The edit was a python replace of exactly these two lines, each asserted to occur once: `            source=_TASK_LEDGER_SOURCE,` in tasks.py and `            "source": source,` in surreal.py.
- `test_probe_served_ca58e.py` is ca58d's `test_probe_served_ca58d.py` (pasted verbatim in coldaudit-58-delta-ca58d-sharing.md §INSTRUMENTS) with three changes: its seed ids retagged `ca58e…`; one added line after the WARN-record assertion, `assert all(getattr(r, "source", None) == "task_ledger" for r in records), "a task-ledger record is not attributed"`; and this appended test:
```python
async def test_probe_arrow_direction_served_text(ledger58) -> None:
    ledger, _env = ledger58
    from loremaster.tasks import TaskCycleError

    items = [
        {"key": "ka", "subject": "a", "description": "d", "blocked_by": ["kb"]},
        {"key": "kb", "subject": "b", "description": "d", "blocked_by": ["kc"]},
        {"key": "kc", "subject": "c", "description": "d", "blocked_by": ["ka"]},
    ]
    with pytest.raises(TaskCycleError) as caught:
        await _tool_seam(ledger).tasks(action="create_many", created_by="probe", items=items)
    served = str(caught.value)
    print(f"\nPROBE arrow_batch_keys: {served}")
    assert "ka -> kb -> kc -> ka" in served or "kb -> kc -> ka -> kb" in served or "kc -> ka -> kb -> kc" in served
```
