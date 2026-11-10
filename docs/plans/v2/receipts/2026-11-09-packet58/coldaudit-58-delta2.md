# Packet 58 second delta cold audit: synthesis (ca58e-synth)

brief-base v27 read · landmines recalled 2026-11-10 (k=50 returned 10, so nothing was cut off)

## SUMMARY BLOCK

- **Verdict: NO-GO, by the letter of the verdict rule, on ONE ground that carries no product defect.** Graded 8679385 (round delta cdf1ce4..8679385, fix wave aa4ea04..8679385), synthesised 2026-11-10 at about 05:01 -0500. HEAD at report: 8679385, the SAME commit. The live tree also carries uncommitted edits from another session to `scripts/test_scratch_copy.py` and `scripts/test_wrong_builds.py` (736 insertions). Neither is in the graded range, and no copy that was tested carries them.
  - **The sole ground: finding 1** (the graph_large re-open instrument cannot be run). The verifiers confirmed it twice. The contract-blind reader graded it **major**; the receipts and probes dimensions graded the same defect minor. The rule says NO-GO on any confirmed blocking or major finding, so it is NO-GO. **If the lead rules finding 1 minor (Decision 2), the verdict becomes GO-WITH-RESIDUALS.** Either way the fix is one commit.
  - The full suite **COMPLETED** at 8679385. Its only RED_ORPHANED lines are the 7 `packet-58-fixwave` SELF-DESTRUCT lines. Every one of those ids is green, so this is **(a-bookkeeping)**: one lead commit, not a product defect (Decision 1). Finding 2 (sharing E-1, graded major) is the same defect, and I classify it under the same carve-out.
  - **No product defect was found at 8679385.** All four dimensions agree that the cycle guard behaves correctly: one input, one predicate, the in-process lock, boots at 3,000 stragglers, and every sharing mutation PROOF HELD.
- **State:** done-with-deviations.
- **Full suite** (my run; TREE aafce77a…, HEAD 8679385, DIRTY_FILES=5, all of them untracked REPORT files):
  - Command: `flock /tmp/lore-full-suite.lock systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python scripts/pending_contract_gate.py --currency -- --maxprocesses=12`.
  - Result: EXIT=1. Wall time 16 min 53.4 s, 45 min 51.6 s CPU, 10.5G memory peak (journal for `run-p732870-i168374274.scope`).
  - Legs: typecheck RED_ADJUDICATED (50) · ruff GREEN · pytest RED_ORPHANED (7, all a-bookkeeping).
  - **Passed count NOT OBSERVED.** The `--currency` render does not print a pytest count, the same bound the first audit recorded. Completion is shown by the gate parsing a junit and judging each of the 7 registered ids green.
  - The workflow runner's own run **never executed the suite**. Its scope ended after 4.5 s (312.8M peak) with no gate output and no `EXIT=`. The likely cause is that the runner's background shell was killed when the runner returned its turn; I infer this and did not measure it (§FULL SUITE, Decision 6).
- **Confirmed findings** (refuted=false for all 26 verifier rows; deduplicated into 18, see §FINDINGS):
  - **major** (graded by one dimension): 1 (re-open instrument, #641/#643); 2 (registry bound, a-bookkeeping);
  - **minor**, all non-product: 3 (stale closure-read and "ONE detector" prose); 4 (WB5 survives, so #638(i) is not closed); 5 (`LIMIT 1000` survives, #642); 6 (#628 `source` is unpinned and its default mislabels); 7 (`max_reanchor_dependents` does not cite #628); 8 ("largest measured" is 20,000 against a measured 19,200); 9 (the FORK A archive header).
- **Residuals:** 10 (#633/#640 "owned by" render) · 11 (contract-round receipt hygiene) · 12 (record inaccuracies) · 13 (a cancelled supersede releases the lock; PLAUSIBLE, LOW) · 14–15 (graph_large is checked at boot only; the predicate runs inline on the event loop) · 16 (a vacuous oracle leg under M3) · 17 (#634's body is stale; the lock is per instance) · 18 (the `blocked` Field omits the superseded exclusion) · the 50 typecheck errors adjudicated to packet-64b-i-contract · #621 · #508 (sidestepped by `--maxprocesses=12`).
- **Regression:** every confirmed finding of both earlier audits is FIXED, superseded, or explicitly carried. Partials: the "ONE detector" prose is half fixed (finding 3) and #638 is half fixed (finding 4). The registry-bound class RECURRED (finding 2). #633 is still open. See §REGRESSION.
- **Decisions needed:** 7, in §DECISIONS.
- **Deviations:**
  - S1: no Agent tool, so nothing was fanned out;
  - S2: I re-ran the full suite myself, because the runner's run never executed. This is the packet's one full suite, run under the flock;
  - S3: two status-preserving ledger annotations: #640 is a duplicate of #633, and #643 is a duplicate of #641;
  - S4: I filed no new findings. The dimensions filed #640–#643.
- `Packages considered: none — synthesis only` · `Odoo-20 portability: n/a` · `Reuse ledger: none`.
- **Receipt pointers:**
  - the four dimension files `coldaudit-58-delta2-ca58e-{receipts,blind,probes,sharing}.md` in this directory;
  - my full-suite log `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/full-suite-synth.log`, and the runner's log `…/ca58e/full-suite.log`;
  - verifier logs under `…/ca58e/ca58e-verify-{1,2,batch}*` and `…/ca58e/verify-batch-probes/`.
  - The scratch paths are not durable. The lines these claims rest on are pasted in §FULL SUITE.

## ROUTING TABLE (brief-base §3)

| step | tier | who | reason |
|---|---|---|---|
| read the runner's full-suite log | 1 | self, inline | The brief says "read it yourself". It had 5 lines and no `EXIT=`; the scope journal shows it ended after 4.5 s. |
| re-run the once-per-packet full suite | 1 | self, background + Monitor | No Agent tool, so no haiku-runner (deviation S1). The runner's run never executed the suite (§FULL SUITE). One run, under the fleet flock. |
| classify the RED_ORPHANED ids | 3 | self | Needs registry and git ancestry judgement. |
| dedupe findings across dimensions, regression table, verdict | 3 | self | Final verdict. |
| annotate duplicate ledger rows #640, #643 | 1 | self | Two status-preserving notes. |

Fan-out: haiku 0 · sonnet 0 · peak 0.

## FULL SUITE (ground truth; I read it myself)

**The runner's run (the claim):** `…/ca58e/full-suite.log` has 5 lines in total: `HEAD=8679385…`, `DIRTY_FILES=5`, `TREE=aafce77a…`, the `CMD:` line and `Running as unit: run-p130065-i167771505.scope`. It has no gate output and no `EXIT=`. The journal reads "Started … 04:02:31" and then "Consumed 4.461s CPU time over 4.488s wall clock time, 312.8M memory peak" at 04:02:35. At 04:42 the process table held no gate or pytest process. The runner's text ("running in the background … will return … once that line appears") was written before the run could finish, and no later report followed. **The suite did not run.** The harness terminates a background command when its agent gives its final response, so the likely cause is that the runner returned. I infer this and did not measure it.

**My run (ground truth):** in the same provenance-verified copy, `…/ca58e/full`. `scratch_copy.sh --verify-only` gave EXIT=0, with all four members resolving inside the copy. HEAD is 8679385, and `git status` shows only the 5 untracked REPORT files. Log `…/ca58e/full-suite-synth.log`, verbatim apart from the two owner-trigger texts, which are shortened here:

```
2026-11-10T04:43:06-05:00
HEAD=86793850c0563a52c9d4f74961ef522d444a2386
DIRTY_FILES=5
TREE=aafce77a0d9d9dd0f34679445d171b14e873622f35041ccad5ff81b4ceb04d73
CMD: flock /tmp/lore-full-suite.lock systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python scripts/pending_contract_gate.py --currency -- --maxprocesses=12
Running as unit: run-p732870-i168374274.scope; invocation ID: 67e6aaabfe674956a4fef03a756bda89
GATE CURRENCY — is every CLAIMED gate green, or owned?
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    RED_ADJUDICATED — 50 residual(s), owned by: packet-58-fixwave (…) · packet-64b-i-contract (…)
  ruff         GREEN
  pytest       RED_ORPHANED — 7 residual(s) with NO owner
      ORPHAN: SELF-DESTRUCT: adjudicated red <id> (bound 'packet-58-fixwave') is green — delete it with the fix.   [x7, ids in §ATTRIBUTION]
CURRENCY   : FAIL — RED with nobody's name on it: pytest
EXIT=1
2026-11-10T05:00:04-05:00
```

- Journal: "run-p732870-i168374274.scope: Consumed 45min 51.612s CPU time over 16min 53.446s wall clock time, 10.5G memory peak." The run stayed under the 16G cap with no OOM. The first delta's full suite was OOM-killed at 49 s (#508, `-n auto`). `--maxprocesses=12` sidesteps #508; it does not fix it.
- The typecheck "owned by:" line names packet-58-fixwave, which owns 0 of the 50 errors (finding 10, #633). The 50 errors are packet-64b-i-contract's.
- The secret-seam scanner that orphaned the first audit's suite is not among the reds. It is green, which matches S `secret.log`.

## ATTRIBUTION — full-suite RED_ORPHANED node ids

**Common evidence for all 7 rows:**
- The bound `packet-58-fixwave` is packet 58's own registry artifact. It was created by 25cfd16, extended by 1130ac9 and re-keyed to exactly these 7 ids by 9fd7f8c ("packet-58-fixwave now owns exactly the 7 new reds"). All three are packet 58 commits.
- The gate's SELF-DESTRUCT judge fires only when the registered id PASSED in this run's junit, so each of the 7 is green at 8679385. The sharing verifier ran the 7 ids directly in its own copy: `7 passed in 3.17s`, EXIT=0.
- 8679385's stat touches no registry file. The bound's own reopen_trigger says it "is deleted with the build", and am-17 §14.7 item 5 says the contract author deletes it when the build lands.
- No other session committed after 8679385: at 05:00 `git log 8679385..HEAD` is empty and HEAD is 8679385. So class (b) is impossible for this run.

| # | node id | class | note |
|---|---|---|---|
| 1 | `loremaster/tests/test_reanchor_58_fixwave.py::TestTheGuardsInputHasNoDepthBoundAndNoSeedCost::test_636_a_boot_with_300_stragglers_of_DISTINCT_heads_completes_and_heals_them_all` | **(a-bookkeeping)** | green, bound awaiting discharge |
| 2 | `loremaster/tests/test_reanchor_58_fixwave.py::TestTheGuardsInputHasNoDepthBoundAndNoSeedCost::test_635_S_the_live_supersede_refuses_a_cycle_through_a_LONG_chain[40_links]` | **(a-bookkeeping)** | same |
| 3 | `loremaster/tests/test_reanchor_58_fixwave.py::TestTheGuardsInputHasNoDepthBoundAndNoSeedCost::test_635_H_the_heal_skips_a_straggler_whose_reanchor_closes_a_LONG_cycle[40_links]` | **(a-bookkeeping)** | same |
| 4 | `loremaster/tests/test_reanchor_58_fixwave.py::TestTwoConcurrentSupersedesOnOneLedgerCannotJointlyWriteACycle::test_634_one_of_two_concurrent_supersedes_is_refused_every_time` | **(a-bookkeeping)** | same |
| 5 | `loremaster/tests/test_reanchor_58_fixwave.py::TestTheGraphLargeWarning::test_graph_large_is_emitted_once_when_shrunk_and_not_at_the_shipped_value[shrunk_below_the_fixture]` | **(a-bookkeeping)** | same |
| 6 | `loremaster/tests/test_reanchor_58_fixwave.py::TestTheGraphLargeWarning::test_graph_large_is_emitted_once_when_shrunk_and_not_at_the_shipped_value[shipped]` | **(a-bookkeeping)** | same |
| 7 | `loremaster/tests/test_blocks_edge.py::TestTheCyclePolicyHasONEImplementation::test_a_BATCH_KEY_cycle_is_served_in_the_PERSISTED_direction_row_then_its_blocker` | **(a-bookkeeping)** | same |

Classes (a) proper, (b), (c) and (d): **none**. No RED_ORPHANED id is attributed to packet 58 outside the bookkeeping carve-out.

## FINDINGS — deduplicated, each with its verifier verdict

Dimension files (this directory): `coldaudit-58-delta2-ca58e-receipts.md` (R), `coldaudit-58-delta2-ca58e-blind.md` (B), `coldaudit-58-delta2-ca58e-probes.md` (P), `coldaudit-58-delta2-ca58e-sharing.md` (S). Every listed finding was verified: refuted=false for all 26 verifier rows; reproduced=false only for blind R1 and R3 (structural reads, timing not re-run).

| # | finding (dimension ids) | graded severity | product | verifier | synthesis |
|---|---|---|---|---|---|
| 1 | **The graph_large re-open instrument cannot be run.** `tasks.py` (the comment above `TASK_GUARD_GRAPH_LARGE_ROWS`, and `TaskLedger._read_dependency_graph`'s BOUND paragraph) tells a boot that emits `task.guard.graph_large` to re-run `scripts/probe_guard_input_58.py`. No commit on any ref has ever held that file. The only tracked copy, am-17 §INSTRUMENT-4, raises `AttributeError: … '_bounded_dependency_graph'` at 8679385 before its scc/predicate leg, and hardcodes the live checkout's tests path. (R F1 · B F1 · P F3; lore #641, duplicate #643) | **major** (B) / minor (R, P) | no | **CONFIRMED** ×2 (verify-1: tracked fence byte-identical to the scratchpad copy, run at N=300 → AttributeError, EXIT=1; verify-batch `probe_guard_input.log`, EXIT=1) | The verifier corrected B's "only copy is in a scratchpad": the fence in am-17 is tracked and byte-identical. It also showed am-17 §14.2 names §INSTRUMENT-4, not a `scripts/` path, so the production comments over-reach the ruling. The bound's re-open action still cannot be executed as written at 8679385, by any copy. This is the RIDER class ("a trigger nobody measures is a hope"): the 20,000 constant rests on the 0.18 s measurement, and the instrument that re-measures it is broken. Graders split on severity (Decision 2). Fix: one commit, either (a) a trimmed `scripts/probe_guard_input_58.py` (full / mirror / scc legs, tests path as a parameter), or (b) re-point both comments at am-17 §INSTRUMENT-4 and repair the fence. |
| 2 | **`packet-58-fixwave` registry bound not discharged**, so the currency pytest leg renders 7 `SELF-DESTRUCT` orphans. (S E-1; the class of the first delta's receipts F1, recurring) | **major** | no | **CONFIRMED** (verify-2: `ca58e-verify-2.currency.log`, `RED_ORPHANED — 7 residual(s)`, EXIT=1; the 7 ids run directly: `7 passed`, EXIT=0) | Per the brief this is **(a-bookkeeping)**: every id is green, the bound awaits discharge, and it is a one-commit lead action. am-17 §14.7 item 5 gives the deletion to the contract author "when the build lands", so a follow-on commit may have been the plan, but 8679385's stat touches no registry file and its body's "currency RED_ORPHANED 0" holds only for a run that starts no pytest. R's §D independently concluded the bound can be discharged. |
| 3 | **Stale prose: two `tasks.py` docstrings still describe the deleted closure read, and `server.py` still claims ONE cycle detector.** `find_row_blocked_by_cycles` (Args `stored`: "the bounded ancestor closure of the proposed blockers"), `TaskLedger._skip_cycle_closing_rows` ("ONE closure read seeded by every proposed blocker"), and the `server.py` comment above create_many's `find_blocked_by_cycle` call ("ONE cycle detector and ONE refusal SHAPE"). (R F2 · B F2 · P F4 · S E-2) | minor | no | **CONFIRMED** ×4 | The two `tasks.py` sentences were true at cdf1ce4 and this build made them false. The `server.py` line is the first delta's D-1, half fixed (server.py is byte-unchanged cdf1ce4..8679385). am-17 §14.7 item 4 ordered both rewritten. Not served text. |
| 4 | **WB5 still survives the contract** (the sorts removed from `find_row_blocked_by_cycles`): the #638(i) determinism pin permutes insertion order inside one process, but WB5's order dependence is hash-seed order, fixed per process. The pin's docstring "Kills WB5" is false. (P F1; #638 annotated, kept open) | minor | no | **CONFIRMED** (verify-batch: `wb5_mut.log` 27 passed; seeds 0–7 all green; positive control: 1 answer ×8 seeds on the correct build, 6 distinct answers on WB5) | The built code is deterministic. A contract gap: the ruled pin cannot fail for the wrong build it names. This is the "failure message promises a check the assertion does not perform" class. |
| 5 | **A partial guard input passes the contract**: `LIMIT 1000` appended to `_read_dependency_graph`'s query passes all 525 targeted tests. (P F2; lore #642) | minor | no | **CONFIRMED** (verify-batch `wbi1_mut.log`: 525 passed; the 2 failures are the 64b-parked `_run_guarded` ids) | No fixture holds more dependency-bearing rows than a plausible cap with a cycle outside the prefix. P's own scale probe kills it (3 of 4 parametrizations). The shipped read has no LIMIT. A contract gap on the exact shape §14 deleted. |
| 6 | **#628 attribution is unpinned and its default mislabels**: dropping `source=_TASK_LEDGER_SOURCE` from `TaskLedger._apply` leaves every telemetry test green, and the record then says `index_writer`, so #628's trigger ("a record from the task ledger") can never fire. (S E-3 · R F5) | minor (S) / residual (R) | no | **CONFIRMED** ×2 (S `m5.log` 391 passed with positive control red; verify-batch `e3_mut.log` 268 passed + 1 unrelated 64b red) | Live value is correct (`served.log`: `'source': 'task_ledger'`). §14.7 item 4 ordered no pin, so adding one is the lead's call (Decision 4). Also R F5: `TestApplyTxnSizeTelemetry` was outside the builder's 29-file targeted set; it passes (3 passed). |
| 7 | `TaskLedger.max_reanchor_dependents`' KNOWN BOUND docstring does not name #628. (S E-4) | minor | no | **CONFIRMED** (`grep -c '#628'` → 0) | CLAUDE.md "WHEN YOU CANNOT CLOSE A HOLE, RECORD IT" requires the finding number. The served hub refusal does cite #628. Open since the first delta (D-3 secondary). |
| 8 | `TASK_GUARD_GRAPH_LARGE_ROWS` comment calls 20,000 "the largest size … measured"; the listed sizes stop at 19,200. (B F3) | minor | no | **CONFIRMED** (read) | B's own P1 probe measured 0.18 s at 20,000 rows, so the cost claim holds; the wording does not. |
| 9 | The archived FORK A probe's header says "fails at line 161" (the call is at 171) and "the lead moves it … at commit" (it is already there). (B F4 · R F6 part) | minor | no | **CONFIRMED** | Archive header hygiene. |
| 10 | `--currency` RED_ADJUDICATED "owned by:" lists every registry bound, not the owners of the residuals. (R F4; lore #633, duplicate #640) | residual | no | **CONFIRMED** | Pre-existing (e8087b0). Already filed as #633 by the first delta; #640 annotated as its duplicate. |
| 11 | Contract-round receipt defects: `run_base.log` has no TREE (tree_id.sh called without its argument); `verify_registry.log` ran on the live tree with no TREE/EXIT; `currency2.log`, `typecheck.log` lack headers. (R F3) | residual | no | **CONFIRMED**; both re-run green (arrow pin RED at 9fd7f8c for the ruled reason, GREEN at 8679385; `--verify-registry` EXIT=0) | Receipt hygiene; the claims they back hold. |
| 12 | Record inaccuracies: 1130ac9 says "17 declared reds added" (8 added, 17 total; 9+17 = am-17's "26"); the builder's "[\t] unmatched" claim is false (30/30 match); the targeted TREE dcd3d939 is pre-move. (R F6) | residual | no | **CONFIRMED** (the pre-header half not independently reconstructed) | Record only. |
| 13 | A cancelled supersede releases `_supersede_lock` before its transaction's outcome is known (3 of 22 mid-transaction cancels committed anyway; 0 cycles). (B R1) | residual | no | refuted=false, reproduced=false (structural: no `shield`/`CancelledError` handling) | PLAUSIBLE, LOW. A joint cycle was never constructed. Lead's call whether to ledger it. |
| 14 | `graph_large` is evaluated at boot only. (B R2) | residual | no | CONFIRMED | The comment's "a boot that emits it" says so honestly. |
| 15 | The cycle predicate runs synchronously on the server event loop (~74 ms at 20,000 rows). (B R3) | residual | no | refuted=false, reproduced=false (structural) | Not re-timed. |
| 16 | The "no cycle written" oracle in 634 / 635_H / fixwave legs A, B is the batch-key detector, vacuous under M3. (S R-1) | residual | no | CONFIRMED | Each pin keeps a non-vacuous leg. |
| 17 | #634's body is stale for its role as the recorded bound (says "No docstring states this bound", names no trigger). The verifier adds: the lock is per `TaskLedger` instance, so two ledger objects in ONE process are also outside it, while the docstring frames the bound as two PROCESSES. (S R-2) | residual | no | CONFIRMED | Annotate #634; consider whether the docstring's "two processes" should read "two ledger instances". |
| 18 | `lore_tasks`' `blocked` Field description omits the superseded-row exclusion (only `status` says it). (S R-3) | residual | no | CONFIRMED (live schema identical) | Served text, but it under-tells rather than over-claims. |

No finding is a product defect. All four dimensions independently found the cycle guard's product behaviour correct at 8679385: one input for all four writers, one predicate, the lock serialising in-process supersedes (B P2: one ledger 0/20 cycles, two-ledger positive control 20/20; P race fuzzer 0 cycles in 70 per mode, no-lock control 15 and 20), boots completing at 3,000 stragglers in 8.7–11.4 s, and every sharing mutation PROOF HELD (S M1–M4b, BC-r5-1/2, the #624 marker sample).

## REGRESSION — every confirmed finding of the two earlier audits

First audit: `coldaudit-58.md` (graded aa4ea04). First delta: `coldaudit-58-delta.md` (graded cdf1ce4). Status at 8679385.

| audit | item | status at 8679385 | evidence |
|---|---|---|---|
| 1st | blind F1 / #623 the heal writes a cycle | **FIXED** | S §REGRESSION: the first audit's `probe_verify1.py` re-run, EXIT=0, `D ['X']` on boots 1–3 with `straggler_would_close_cycle` logged; S M1/M2 heal legs. |
| 1st | blind F4 / #624 THROW markers spelled twice | **FIXED** | S §S2 `mk_cas.log` PROOF HELD (other three markers by inference: `_txn.py` unchanged in range). |
| 1st | blind F6 falsified docstrings (its list) | FIXED (still true) | S §REGRESSION. New false prose arrived in this wave: finding 3. |
| 1st | blind F7a `_still_claimable` / F7b uuid default | F7a GONE (0 hits); F7b residual (70665b9's choice) | S §REGRESSION. |
| 1st | blind F8 hub refusal served text / #625 | **FIXED** (driven) | S `served.log`; cites #628. Docstring citation still missing: finding 7. |
| 1st | probes F1 OB3 missing pin (#626) | pinned, green | P §(c) regression probes hold; not separately mutation-re-proven this round. |
| 1st | probes F2 packer prose "transaction cap" (#625a) | **FIXED** (driven) | S `served.log`: "over the 2-row heal chunk bound", row_cap = live minimum. |
| 1st | sharing F-1 / #622 wrong probe cited | **FIXED** | S §REGRESSION. |
| 1st | sharing F-2 116 vs 234 tasks | FIXED (since 380414c) | first delta §REGRESSION. |
| 1st | receipts F-1/F-2/F-3 | superseded (graded aa4ea04 receipts) | — |
| 1st | ground 1: secret-seam RED_ORPHANED (probe env reads) | **FIXED** | S `secret.log` 1 passed; see also §ATTRIBUTION. |
| 1st | F5 / #130(a) served wording (refuted-with-residual) | **FIXED** | S `served.log`. |
| delta | probes F-A / #636 boot fails at ~300 stragglers (blocking) | **FIXED** | P `a_scale*.log`: 300/1000/3000 stragglers, 4 passed ×2, 3000-straggler boot 8.7–11.4 s, guard read ≤ 0.045 s; S baseline `test_636_…` green. |
| delta | blind F1 / #634 concurrent supersedes write a cycle | **FIXED in-process**; two-process bound recorded | S M4/M4b PROOF HELD; B P2 and P race fuzzer 0 cycles with positive controls. #634 stays open as the bound (finding 17). |
| delta | blind F2 / probes F-B / #635 = #637 32-hop truncation | **FIXED** | P `a_depth.log` k=3/33/34/40/100 refused or skipped, controls_ok; S M1/M2 redden 635_S/H. |
| delta | receipts F1 registry bound not discharged | **RECURRED** (new bound, same class) | finding 2 (a-bookkeeping). |
| delta | receipts F3 / #633 currency "owned by" | OPEN, pre-existing | finding 10 (#640 duplicate). |
| delta | blind F3 arrow direction differs by noun | **FIXED** | S `served.log` "ka -> kb -> kc -> ka" = row → blocker; R F3 arrow pin RED at 9fd7f8c, GREEN at 8679385; S M3 reddens it. |
| delta | receipts F2 FIXWAVE-1 TREE mismatch; receipts F4 builder prose | superseded (they graded fix-wave-1/-2 receipts) | This round's equivalents: findings 11, 12. |
| delta | blind F4 / sharing D-1 / probes R-1 "ONE shared detector" prose | **HALF FIXED** | `tasks.py` fixed; `server.py` not: finding 3. |
| delta | probes F-C / #638 two wrong builds survive | **HALF FIXED** | WB2 now killed exactly by `test_638_ii`; WB5 still survives: finding 4. |
| delta | sharing D-2 #130(a) `query_tasks` docstring | **FIXED** | S §REGRESSION. |
| delta | sharing D-3 `large_transaction` has no source; #628 not cited | source **FIXED but unpinned** (finding 6); #628 citation **OPEN** (finding 7) | S `served.log`, `m5.log`. |
| delta | blind F5 closure read composed twice (residual) | RESOLVED by design | Both callers now call `_read_dependency_graph()`; the closure read is deleted (R F2 evidence). |

## DECISIONS

1. **Delete the `packet-58-fixwave` bound** (lead, one commit, then `--verify-registry`). This clears the pytest RED_ORPHANED (all 7 ids are green) and stops deselecting 7 green pins from default runs. The class has now recurred in two consecutive waves (first delta receipts F1, now finding 2). Recommended: from now on, the builder's brief makes deletion of the registry entry part of the BUILD commit's rider, with the currency PYTEST leg over the bound's own files as its receipt, because a `--legs typecheck,ruff` currency run is structurally unable to see a stale bound.
2. **Severity of finding 1** (the graph_large re-open instrument). Blind graded it major, while receipts and probes graded it minor; all three agree it is not a product defect. This decides the verdict: major means NO-GO (as rendered), and minor means GO-WITH-RESIDUALS. My recommendation: treat it as the RIDER class and fix it before the close-out, whatever the grade. The fix is one commit, either (a) a trimmed, committed `scripts/probe_guard_input_58.py` (full / mirror / scc legs, tests path as an argument), or (b) re-point both `tasks.py` comments at am-17 §INSTRUMENT-4 and repair the fence. Option (a) matches brief-base §1 (an instrument that backs a load-bearing claim is committed).
3. **One prose commit**: findings 3 (the two `tasks.py` docstrings and the `server.py` comment), 7 (cite #628), 8 ("largest measured") and 9 (the archive header). None of them is served text.
4. **Contract gaps** (contract author, if the lead wants them closed): finding 4 (#638(i): the pin's "Kills WB5" is false; ca58d's cross-process seed probe is a ready instrument), finding 5 (#642: a fixture above any plausible cap with a cycle outside the prefix), and finding 6 (pin `source='task_ledger'`; §14.7 item 4 ordered no pin). Alternatively, rule them recorded residuals. At minimum, the false "Kills WB5" docstring should be corrected.
5. **Ledger hygiene**: close one of each duplicate pair, #633/#640 and #641/#643 (both annotated). Annotate #634's stale body (finding 17), and rule whether the bound reads "two processes" or "two `TaskLedger` instances": the lock is per instance. Decide whether to ledger blind R1 (the cancelled supersede releases the lock; PLAUSIBLE, LOW).
6. **Runner hazard** (lead and orchestration law): a workflow `haiku-runner` that backgrounds a 17-minute suite and then returns its turn kills the suite in about 4 s. Its text read as "running", and no artifact contradicted it until this synthesis read the log. Runner briefs for the full suite should wait in the foreground until the `EXIT=` line, with bounded loops under the 10-minute Bash cap, or the synthesis step should own the run. Do you want this saved as a lore landmine (`lore_remember … harness_type=landmine`)? I did not save it, because it is orchestration law and the decision is yours.
7. **#508** is still open. This run's `--maxprocesses=12` worked (10.5G peak), while a bare `--currency` OOMs. Until #508 is fixed, the sanctioned command needs that suffix.

## COST

- **Agents:** 4 dimension auditors (receipts, blind, probes, sharing), 3 verifiers (verify-1, verify-2, verify-batch), 1 full-suite haiku-runner (its run never executed), and this synthesiser: 9 in total.
- **Runs:**
  - full suite: 1 that died in 4.5 s (runner), and 1 complete (mine: 16 min 53 s, 45 min 52 s CPU, 10.5G peak);
  - receipts: about 6 (currency, typecheck, verify-registry, arrow re-run, telemetry probe, INSTRUMENT-4 probe);
  - blind: 3 probes (P1–P3; about 66 reps);
  - probes: about 22 (prior-audit probes, race fuzzer on 2 seeds, regression probes, 8 mutation proofs over 525 tests);
  - sharing: about 17 (2 baselines, M1–M5, BC-r5-1/2, the marker sample, the served, secret and #623 verifiers, the registry currency run);
  - verifiers: about 12;
  - me: 1 full suite and 0 targeted runs.
- **Wall time:** about 59 min, from `full-copy.log` at 04:01 -0500 to this synthesis at about 05:01. About 17 min of that was the full-suite re-run, made necessary by the runner's lost run.
- **Loop cost:** packet 58 has been through three cold-audit rounds (aa4ea04, cdf1ce4 and 8679385). Every remaining item here is a one-commit lead action or a contract-hygiene ruling. None of them is a product fix.
