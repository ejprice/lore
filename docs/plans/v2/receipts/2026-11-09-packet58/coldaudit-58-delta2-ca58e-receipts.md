# coldaudit-58-delta2 — dimension: RECEIPT VERIFICATION (ca58e-receipts)

## SUMMARY BLOCK
- brief-base v27 read · brief project v7 read · landmines recalled (10 returned, under k=50)
- state: done-with-deviations
- deviations: (1) no `Agent` tool in this worker's tool set, so the fan-out routing below could not spawn Haiku runners; every run was mine, one at a time. (2) Two receipts were re-run because they were missing or mismatched (contract run 1 had no TREE; the contract's `--verify-registry` log ran against the LIVE tree's registry). (3) One probe the builders never ran: am-17 §INSTRUMENT-4 run verbatim at HEAD.
- Packages considered: none, no mechanism specified (audit only; stdlib `xml.etree`/`yaml` used to read receipts).
- Odoo-20 portability: n/a, no Odoo seam touched.
- Reuse ledger: none (no production symbols written).
- Graded: 8679385 · HEAD-at-report: 8679385 · SAME
- VERDICT (receipts dimension): the receipts HOLD. Every FIXWAVE-3 gate receipt describes 8679385 (`TREE=` reconciled byte-for-byte; see §B). FIXWAVE-14's 7 declared reds were RED at b99f178 for the ruled reasons, SAT holds with 0 attributable, the registry claim (17, not 26) is right, and 12 sampled sweep verdicts are all correct. Currency at 8679385: RED_ORPHANED 0 (typecheck RED_ADJUDICATED 50, ruff GREEN, pytest NOT_RUN by `--legs`).
- Findings: 2 minor (F1 the graph_large re-open instrument cannot be run: path absent and the pasted copy crashes at HEAD, finding #641; F2 two production docstrings still name the deleted closure read) and 4 residuals (F3 receipt defects re-run green, F4 the currency `owned by` line lists every bound, finding #640, F5 a covering suite outside the targeted set, unpinned `source`, F6 record inaccuracies including where "26" came from).
- Discharge proposal: YES. `packet-58-fixwave` can be deleted. All 7 of its ids and all 17 ids removed at 9fd7f8c PASSED in the builder's junit at a tree equal to 8679385 (§B.3). No typecheck residual sits in its files (§D).
- decisions-needed: (a) delete `packet-58-fixwave` (am-17 §14.7 item 5 says "deletes the entry when the build lands"; it is still present, `active: true`, at 8679385); (b) route F1/F2 to a builder.
- receipt pointers: §B (FIXWAVE-3), §C (FIXWAVE-14), §D (currency), §E (findings), §F (instruments, verbatim).

## A. Routing table (written before the first sweep; fan-out blocked, see deviation 1)
| step | tier | who |
|---|---|---|
| scratch copy, pin to 8679385, TREE | 1 | self (no Agent tool) |
| builder-log inventory + junit/registry cross-match | 1 (script I wrote) | self; instrument pasted in §F |
| TREE reconciliation of builder copies vs 8679385 | 1 | self |
| registry history trace `git log -p` | 1 | self |
| sweep re-derive (55 hits) | 1 | self, grep (rename exhaustiveness, the lore-honest grep case) |
| verdict sampling (12 hits) | 3 | self (audit judgment) |
| currency run, verify-registry rerun, arrow-pin rerun, telemetry probe, INSTRUMENT-4 probe | 1 | self, one run at a time |

Scratch copy: `scripts/scratch_copy.sh …/scratchpad/ca58e/ca58e-receipts` (EXIT=0), then `git checkout 8679385 -- .`; the
5 untracked live-tree `REPORT-*.md` files were moved out. Clean fingerprint at 8679385:
`HEAD=86793850c0563a52c9d4f74961ef522d444a2386 DIRTY_FILES=0 TREE=3bb574813a49b5aee617c8935bfb2d3652905ec5a663be6ac9eca95f3ae748b8`.
`loremaster.__file__` = `…/scratchpad/ca58e/ca58e-receipts/loremaster/loremaster/__init__.py` (inside the copy).

## B. REPORT-builder-58-1.md §FIXWAVE-3, verified against 8679385

### B.1 TREE reconciliation (measured 2026-11-10)
The builder's gate copy `…/b9f36f3f…/scratchpad/fw3` still fingerprints `TREE=0103101b…ebc9` (unchanged since its gates).
Its per-file lines (instrument `tree_lines.sh`, §F) differ from my clean 8679385 checkout in exactly 5 lines, the 5 untracked
`REPORT-*.md` files. With those 5 removed the hash is `3bb57481…48b8` = clean 8679385, exactly.
- **ruff / typecheck / currency rows (TREE 0103101b):** VALID, graded code identical; the only difference is non-code untracked reports.
- **targeted row (TREE dcd3d939):** reconstructed exactly as 8679385 + the 5 REPORTs + `scripts/coldaudit_cycle_04b3_fork_a_refute.py`
  at its **9fd7f8c content (no DUAL header)** in `scripts/`, with no receipts copy. My first reconstruction, with the header-bearing
  file in `scripts/`, gave `6050851b…` (mismatch). With the 9fd7f8c content it gave `dcd3d939…6122` (match). So the run's tree
  differs from 8679385 only in a comment header of a non-test script that the run does not execute → VALID. The report's note
  ("before the script move") is true but incomplete: the header had not been written into that copy either (F6).

### B.2 Gate rows
| gate | log (builder's) | EXIT | count line | verdict |
|---|---|---|---|---|
| targeted (29 files, `--run-parked -n 8 --timeout=300`, cgroup) | `logs/fw3.log` + `fw3.xml` | 1 | `30 failed, 2431 passed, 1 skipped … in 383.01s` | valid; the 30 reds are all registered `packet-64b-i-contract` ids (exact text match of all 30 FAILED ids against the registry: 0 unmatched, §F `junit_status.py` positive control: it reports 30/30 of them `failed`) |
| ruff | `logs/ruff_fw3b.log` | 0 | `All checks passed!` | valid |
| typecheck | `logs/typecheck_fw3b.log` | 1 | 50 errors, scripts leg OK | valid; equals my run at 8679385 (§D) |
| currency `--legs typecheck,ruff` | `logs/currency_fw3b.log` | 1 | typecheck RED_ADJUDICATED 50, ruff GREEN, pytest NOT_RUN | valid; no RED_ORPHANED |
The log carries no `RAN:` line; the command lives only in the report table. That is a minor receipt-shape gap, not a mismatch.

### B.3 Every registry id at the graded tree (from the builder's junit, which is valid for 8679385)
`junit_status.py fw3.xml` over the 7 current `packet-58-fixwave` ids + the 17 removed at 9fd7f8c: **24 passed, 0 other**.

### B.4 Mutation self-checks (builder runs, not gates): count lines confirmed
`fw3mi.log` (`_read_dependency_graph` → `return {}`): `21 failed, 281 passed`, EXIT=1, failure ids match the report's list.
`fw3ml.log` (lock → fresh `asyncio.Lock()`): `1 failed, 77 passed`, the one red is `test_634_…every_time`. Note: under
`return {}` `test_636` stays GREEN (its world has no cycle, so an empty input also heals all 300). Other pins cover that wrong build, so it is not a gap.

## C. REPORT-contract-58-r53.md §FIXWAVE-14, verified

### C.1 Base copy = 9fd7f8c
`…/c58r53/fw14/base` (TREE `6e61cae4…`, unchanged): its 6 dirty tracked files are sha256-identical to `git show 9fd7f8c:<f>`,
and those 6 are the whole `b99f178..9fd7f8c` diff. The base copy is therefore 9fd7f8c + 5 untracked REPORTs (production = b99f178 = cdf1ce4).

### C.2 The 7 declared reds
- Declared from `--collect-only` before any run: `declared.txt` (14 ids) 03:25:35 and `declared_red.txt` (7) 03:25:43; run 1 finished 03:34 (485 s).
- Run 3 (`run_base2.log`, TREE 6e61cae4, EXIT=1, `6 failed, 21 passed`): exactly the 6 fix-wave-file ids, each red for its ruled reason:
  `AttributeError … TASK_GUARD_GRAPH_LARGE_ROWS` ×2, `20 of 20 repeats … ['ok','ok']`, `D was re-anchored`, the 40-link supersede,
  and `QueryError … exceeded the timeout: 5s` / `TxnDomainRejectionError` for #636.
- The 7th (`test_blocks_edge.py::…BATCH_KEY…row_then_its_blocker`) was RED only in run 1, **whose TREE line is missing**
  (`tree_id.sh: usage` in the log). I **re-ran it** at a worktree equal to 9fd7f8c (`git diff 9fd7f8c` empty; TREE `964dc35a…`):
  `1 failed in 1.80s`, EXIT=1, `AssertionError: the batch keys refusal serves arrow-a -> arrow-c -> arrow-b -> arrow-a: steps … do not go from a member to ITS blocker` → RED for the ruled reason.
  The log is `…/scratchpad/ca58e/logs/arrow_red_9fd7f8c.log` (pasted here because scratch paths are not durable).
- SAT (`run_ref3.log`, TREE 650ea234, EXIT=1, `30 failed, 2748 passed, 1 skipped`): the 30 are the 64b-i parked set per the author.
  A reference build has no graded-commit TREE to match. The GREEN of the 7 at the REAL build is §B.3.

### C.3 Registry: "17 at HEAD, not 26". Correct. Where the first 9 went: nowhere.
Traced with `count_fixwave_ids.py` (§F) at each revision of `scripts/pending_contracts.yaml` since 25cfd16:
| rev | ids in `packet-58-fixwave` |
|---|---|
| 25cfd16^ | 0 (entry absent) |
| 25cfd16 | 9 (A, B, C, D, F5, 130a in the fix-wave file; hub-bound `[0]`,`[2]`; r3_convergence over-cap) |
| 1130ac9 | 17 = the same 9 **kept** + 8 added (E1 ×2, E3, D2-i ×2, D2-ii, the 2 `test_MUTATION_*` in test_blocks_edge) |
| b99f178 | 17 (unchanged) |
| 9fd7f8c | 7 (all 17 removed, the 7 §14 reds added) |
| 8679385 | 7 |
1130ac9's diff is +8/−0 ids, but its message reads "17 declared reds added to packet-58-fixwave". 17 was the entry's total
(the §13 declared set, 9 still red plus 8 new), not the number added. Reading it as "added" gives 9 + 17 = 26, the figure in
am-17 §14.7 item 5 and the lead's directive. The author's per-file split (12/2/1/2) matches.

### C.4 The 55-hit sweep
Re-derived at b99f178 over `loremaster/tests` + `scripts` with the author's pattern: **55 hits / 13 files** (blocks_edge 20, capability_seams 8,
04b3 6, coldaudit script 5, query_tasks_bounded 3, trace_telemetry 3, recut_fixtures 2, readonly_guard 2, legacy probe 2, and 1 each in four files).
Matches the table. (am-17 §14.4 item 6's own per-file counts are low by 5 for blocks_edge, by 1 for each script. The author's are right.)
Sampled 12 verdicts against the file at b99f178, and the claimed edit at 9fd7f8c/8679385. **All correct:**
| hit | verdict | check |
|---|---|---|
| `_recut_auth_fixtures.py:5` | unrelated | "no fork — the lead's ESC-1 constraint" (auth recut) ✓ |
| `_surreal_fakes.py:919` | unrelated | telemetry `ok` ESC-1 (d0f84d0) ✓ |
| `test_agent_capability_seams.py:256` | unrelated | "Home RULED loremaster (ESC-1)" ✓ |
| `test_blocks_edge.py:167` | unrelated | legacy-cycle record's consumer "(ESC-1 reading A)" ✓ |
| `test_query_tasks_bounded.py:1559` | unrelated | wave r5 ESC-1 edits ✓ |
| `test_tool_allowlist.py:670` | unrelated | "F [FORK A]: the IDENTITY/preamble line" ✓ |
| `test_trace_telemetry.py:780` | unrelated | ESC-1 `ok` semantics ✓ |
| `scripts/restore_prod_dump.py:49` | unrelated | "packet 64 amendment 6 §2, FORK A = A3" ✓ |
| `test_blocks_edge.py:2049/2052` | re-keyed message | at 8679385 the message cites am-17 §13.2; "ESC-1's bounded read must KEEP the drop-loop" gone ✓ |
| `test_blocks_edge.py:2266…2320` | DELETED | no `def` of the closure-rows pin or `_blocked_noise_traffic` at 8679385; DUAL note at :2202 ✓ |
| `test_blocks_edge.py:9253–9257` | re-keyed + DUAL | the WB-D comment keeps its record and has a DUAL line (8679385 :9198) ✓ |
| `test_cycle_write_path_04b3.py:15/212/220` | DUAL bullet / re-keyed | the DUAL bullet heads the 04b-3 history; "guard-read rework" ✓ |
Residue at 8679385 for `_bounded_dependency_graph|_CLOSURE_START_PARAM` across the whole tree: only docs/receipts/archived
reports and the archived script, none in `loremaster/` or `scripts/`. But the sweep covered tests/scripts only, and production prose still names the read (F2).

## D. Currency at 8679385 (run once, my copy, TREE 3bb57481)
`uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` → EXIT=1:
`typecheck RED_ADJUDICATED — 50 residual(s)` · `ruff GREEN` · `pytest NOT_RUN — claimed by the manifest, never executed` (the `--legs`
filter; `CURRENCY: FAIL — claimed but never run: pytest`). **RED_ORPHANED: 0.**
`scripts/typecheck.sh` at 8679385: `Found 50 errors in 15 files (checked 354 source files)`, EXIT=1. The files are the 12 `*_64b*.py`,
`test_comms_footer.py` (1), `test_mcp_server.py` (6), `test_reanchor_58_r3_cas_seam.py` (1) and `test_reanchor_58_r4_state.py` (1). None is a
`packet-58-fixwave` file. `--verify-registry` at 8679385: EXIT=0 (re-run, see F3).

## E. Findings
- **F1 (minor, #641): the graph_large re-open instrument cannot be run.** `tasks.py` comment on `TASK_GUARD_GRAPH_LARGE_ROWS` and
  `TaskLedger._read_dependency_graph`'s docstring say a boot emitting `task.guard.graph_large` "re-runs `scripts/probe_guard_input_58.py`".
  No such file exists in any commit (`git log --all` empty); the only copy is in another session's scratchpad. am-17 §INSTRUMENT-4 pastes it,
  but run verbatim at 8679385 (sys.path only re-pointed; N=300; :18000) it prints `full: 0.004s rows=300` and `mirror: 0.006s`, then
  `AttributeError: 'TaskLedger' object has no attribute '_bounded_dependency_graph'` before the `scc` leg, EXIT=1. So the bound's
  re-open trigger names an instrument that cannot re-measure the 0.18 s claim as written. (The builder flagged the absent path. Nobody committed it.)
- **F2 (minor): two production docstrings still describe the deleted closure read as the guard's input.**
  `find_row_blocked_by_cycles` Args `stored:` reads "the bounded ancestor closure of the proposed blockers". `TaskLedger._skip_cycle_closing_rows`
  reads "ONE closure read seeded by every proposed blocker". At 8679385 both callers pass `_read_dependency_graph()` (every column).
  The §14.4 item 6 sweep scoped tests/scripts only, and the builder's item (1) lists the docstrings it rewrote; these two were missed.
- **F3 (residual, re-run green): receipt defects in the contract round.** Run 1 had no TREE (the only RED receipt for the arrow pin) → re-run RED,
  §C.2. `fw14/verify_registry.log` names `registry: /home/ejprice/PycharmProjects/lore/scripts/pending_contracts.yaml` (the LIVE tree, not
  the base copy) and has no TREE/EXIT line → re-run at 8679385, EXIT=0. `currency2.log`/`typecheck.log` also lack the tree_id header;
  superseded by my §D run.
- **F4 (residual, pre-existing, #640): the currency line `owned by:` lists every registry bound.** `GateCurrency` owners are built
  `for bound in gate.registry.bounds`, so the line says packet-58-fixwave owns typecheck residuals it does not own (§D). A discharge decision read
  off that line would be wrong.
- **F5 (residual): a covering suite of the `surreal.py` change sat outside the targeted set.** `test_surreal_apply.py::TestApplyTxnSizeTelemetry`
  drives `_log_transaction_size`; it was not among the 29 files. Run at 8679385: `3 passed`, EXIT=0. No test asserts the new `source` extra
  (`index_writer` / `task_ledger`), so a build passing the wrong composer goes green. §14.7 item 4 ordered no pin; whether one is wanted is the lead's call.
- **F6 (residual, record accuracy):** the builder's "one id not matched by name (the `[\t]` parametrization)" is not reproduced: all 30 FAILED ids
  match registry text exactly. The targeted TREE was also pre-header, not just pre-move (§B.1). 1130ac9's "17 … added" is +8 (§C.3), the origin of
  "26". The archived `coldaudit_cycle_04b3_fork_a_refute.py` header says it "fails at line 161"; the call is at line 171 (the header shifted it).
- Not my dimension, noted so it is not dropped: am-17 §14.4 item 4 (creates racing supersede / two creates, a cold-audit RUN) belongs to the probes dimension.

## F. Instruments (pasted verbatim; they live in my scratchpad, which is not durable)
`tree_lines.sh` (the same enumeration as `tree_id.sh`, per file, for diffing two trees):
```bash
#!/usr/bin/env bash
# tree_lines.sh <worktree>: the per-file "sha256 path" lines tree_id.sh hashes (same enumeration), for diffing two trees.
set -euo pipefail
cd "$1"
git ls-files -z --cached --others --exclude-standard | sort -z -u | while IFS= read -r -d '' p; do [ -f "$p" ] && printf '%s %s\n' "$(sha256sum < "$p" | cut -d' ' -f1)" "$p"; done
```
(`sha256sum < tree_lines.sh-output` = the `TREE=` value. A filtered list's hash is how §B.1 removes the REPORT lines.)

`count_fixwave_ids.py` (run with `uv run --project <copy> python count_fixwave_ids.py <rev>...` from the repo):
```python
"""count_fixwave_ids.py <rev>...: print the packet-58-fixwave red_nodeids at each git revision of scripts/pending_contracts.yaml."""
import subprocess, sys, yaml
for rev in sys.argv[1:]:
    raw = subprocess.run(["git", "show", f"{rev}:scripts/pending_contracts.yaml"], capture_output=True, text=True, check=True).stdout
    ids = [n for b in yaml.safe_load(raw)["bounds"] if b["id"] == "packet-58-fixwave" for f in b["files"] for n in f.get("red_nodeids", [])]
    print(f"== {rev}: {len(ids)}")
    for n in ids: print("  ", n)
```

`junit_status.py` (a node id's status in a junit xml; positive control: 30/30 of fw3's FAILED ids report `failed`):
```python
"""junit_status.py <junit.xml> <ids.txt>: print each pytest node id's status in a junit xml (file::Class::name reconstructed from classname)."""
import sys, xml.etree.ElementTree as ET
st = {}
for tc in ET.parse(sys.argv[1]).iter('testcase'):
    cls = tc.get('classname').split('.')
    # module path = leading segments until a CamelCase class segment
    mod = [s for s in cls if not s[:1].isupper()]; klass = [s for s in cls if s[:1].isupper()]
    nid = '/'.join(mod) + '.py::' + '::'.join(klass + [tc.get('name')])
    s = 'passed'
    for ch in tc:
        s = {'failure': 'failed', 'error': 'error', 'skipped': 'skipped'}.get(ch.tag, s)
    st[nid] = s
for line in open(sys.argv[2]):
    n = line.strip()
    if n: print(st.get(n, 'NOT-IN-XML'), n)
```

My run logs (each opens with the tree_id lines, then `RAN:`, then output, then `EXIT=`), in `…/27ef6c0a…/scratchpad/ca58e/logs/`:
`currency_8679385.log` (EXIT=1, RED_ORPHANED 0) · `typecheck_8679385.log` (EXIT=1, 50 errors/15 files) ·
`verify_registry_8679385.log` (EXIT=0) · `arrow_red_9fd7f8c.log` (EXIT=1, 1 failed, ruled reason) ·
`txn_size_telemetry_8679385.log` (EXIT=0, 3 passed) · `probe_guard_input_at_8679385.log` (EXIT=1, AttributeError after the mirror leg).
