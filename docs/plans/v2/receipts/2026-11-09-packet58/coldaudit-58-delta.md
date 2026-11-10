# Packet 58 delta cold audit: synthesis (ca58d-synth)

brief-base v27 read · landmines recalled 2026-11-10 (k=50 returned 10, so nothing was cut off)

## SUMMARY BLOCK

- **Verdict: NO-GO.** Graded cdf1ce4 (fix-wave range aa4ea04..cdf1ce4), synthesised 2026-11-10. HEAD at report: cdf1ce4, the SAME commit. The live tree also carries two modified tracked files from another session, `scripts/test_scratch_copy.py` and `scripts/test_wrong_builds.py`. Neither is in the graded range, and no dimension's copy carries them. Three independent grounds; each one alone is enough under the tightened rule:
  1. **The full suite did not complete.** Its own cgroup OOM-killed it at the 16G cap after 49 s (see §FULL SUITE). There is no pytest count and no leg verdict.
  2. **One confirmed blocking product defect.** probes F-A, #636: at about 300 stragglers the boot heal's single closure read hits its `TIMEOUT 5s`, and the server fails to boot.
  3. **Confirmed major product defects:**
     - blind F1, #634: two concurrent supersedes together write a `blocked_by` cycle (20/20);
     - blind F2 = probes F-B, #635 = #637: the cycle guard's closure stops at 32 hops, so a live supersede and the heal both write long cycles;
     - receipts F1: the `packet-58-fixwave` registry bound was not discharged, so the pytest currency leg goes RED_ORPHANED. It is major/product only by the letter of the rule; see Decision 4.
- **State:** done-with-deviations.
- **Full suite** (TREE 8cde72fc…, HEAD cdf1ce4, DIRTY_FILES=5):
  - Command: `flock /tmp/lore-full-suite.lock systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python scripts/pending_contract_gate.py --currency`.
  - Result: EXIT=143. The journal says `oom-kill`, 16G peak, 9 min 55.7 s CPU over 49.5 s wall.
  - Gate legs: none rendered (typecheck, ruff and pytest all NOT OBSERVED). RED_ORPHANED: none printed. Count: none.
  - The runner's claim of "SIGTERM, not a timeout" is incomplete: the kernel OOM killer acted inside the scope. Likely cause: #508 (when it runs alone, the gate resolves `-n auto`, which is 64 workers). This is inferred, not measured.
  - The pytest leg would be RED_ORPHANED with 17 SELF-DESTRUCT lines from receipts F1. That is derived by a verifier through the gate's own judges in full-suite form; the full suite did not observe it.
- **Confirmed findings** (verifier refuted=false, reproduced=true; 23 rows, all confirmed, none refuted):
  - blocking: probes F-A (#636);
  - major: blind F1 (#634); blind F2 / probes F-B (#635 / #637, one defect); receipts F1;
  - minor, product: receipts F3 (#633, the currency "owned by" lists every bound); blind F3 (the cycle arrow points opposite ways for the two nouns);
  - minor, non-product: receipts F2 (the FIXWAVE-1 TREE does not match 70665b9) and F4 (builder prose); blind F4 = sharing D-1 = probes R-1 (stale "ONE shared detector" prose); probes F-C (#638, two wrong builds survive the contract); sharing D-2 (the #130(a) docstring rider was dropped) and D-3 (F8 part 1 is still open; the `large_transaction` record has no source).
- **Residuals:** blind F5 (the closure read is composed twice); probes R-2 (the same issue as receipts F1); sharing R-1…R-6; #621 (`--legs` exits 1); #508.
- **Decisions needed:** 7, in §DECISIONS. The headline: the cycle-guard class has now survived two waves, so it escalates as a DESIGN question rather than a third fix brief.
- **Deviations:**
  - S1: no Agent tool, so nothing was fanned out;
  - S2: I did not re-run the full suite, because a solo re-run would hit #508 again;
  - S3: I wrote two status-preserving ledger annotations, #508 (this OOM) and #637 (a duplicate of #635);
  - S4: I filed no new findings (Decision 6).
- `Packages considered: none — synthesis only` · `Odoo-20 portability: n/a` · `Reuse ledger: none`.
- **Receipt pointers:**
  - the four dimension files `coldaudit-58-delta-ca58d-{receipts,blind,probes,sharing}.md` in this directory;
  - the full-suite log `…/scratchpad/ca58d/full-suite.log`, with the journal for scope `run-p3217433-i166667620.scope`;
  - verifier logs under `…/scratchpad/ca58d/ca58d-verify-{1,2,batch}*`.
  - The scratch paths are not durable. The counts these claims rest on are pasted in the dimension files.

## ROUTING TABLE (brief-base §3)

| step | tier | who | reason |
|---|---|---|---|
| read the full-suite log (6 lines) and the scope journal | 1 | self, inline | It is on the critical path and short, and the brief says "read it yourself". No Agent tool. |
| decide the OOM's likely cause (#508) | 3 | self | This is judgement over the journal, the resolver's constants and #508's prior annotations. |
| spot-check regression items not covered by a dimension (sharing F-2, probes F1/OB3, probes F2) | 1 | self, inline | 4 `git show … | grep` reads. |
| verdict and synthesis | 3 | self | This is the final verdict. |

Fan-out: haiku 0 · sonnet 0 · peak 0.

## FULL SUITE (ground truth; I read it myself)

- Log, all 6 lines: `HEAD=cdf1ce4…` · `DIRTY_FILES=5` · `TREE=8cde72fc3c9925a9ce87b9c5cda95131a067a88a9ce6a3e3473935d75c3fdd9f` · `CMD: flock … --currency` · `Running as unit: run-p3217433-i166667620.scope` · `EXIT=143`.
- Copy provenance: `full-copy.log` shows that scratch_copy.sh resolved all four members inside `…/ca58d/full`.
- Journal (`journalctl --user -u run-p3217433-i166667620.scope`, measured 2026-11-10):
  - 02:30:17 started;
  - 02:31:06 "The kernel OOM killer killed some processes in this unit" and "Failed with result 'oom-kill'";
  - "Consumed 9min 55.679s CPU time over 49.463s wall clock time, 16G memory peak".
- The flock was taken, because systemd-run's unit line printed, so this was not a lock wait.
- **Likely cause (MEDIUM): #508.**
  - `scripts/_pytest_sessions.py`: `SOLO_PYTEST_WORKERS = "auto"` and `FLEET_CAPPED_PYTEST_WORKERS = "12"`.
  - At 02:30:17 this was the only systemd-run scope started in the 02:29–02:32 window.
  - The signature (49 s, 16G peak, OOM) matches audit-parked-1's solo attempt earlier on 2026-11-10, annotated on #508: 68 processes, 16.8 GiB summed RSS, about 260 MB per worker.
  - The first packet-58 audit (aa4ea04) completed with a 9.2G peak over 17 min.
  - The gate does not print its resolved `-n`, so 64 workers is inferred.
  - Classification: (d) unknown as to test ids, and NOT packet 58. The fix-wave range does not touch `_pytest_sessions.py`, which was last changed at b6f57e9.
- Per CLAUDE.md, a pytest tree over 16 GiB is a defect to report. It is reported as an annotation on #508, because no test ids exist to name.

## ATTRIBUTION — full-suite RED_ORPHANED node ids

**No RED_ORPHANED ids were observed: the run died before any gate leg rendered.** No id gets a class from observation. One row is recorded as DERIVED, not observed, so the lead knows what a completed run will show:

| # | node id / line | class | evidence |
|---|---|---|---|
| (none observed) | — | — | The full-suite log has no leg output (EXIT=143, OOM). |
| D1 (derived) | 17 `SELF-DESTRUCT: adjudicated red … (bound 'packet-58-fixwave') is green — delete it with the fix.` lines in the pytest leg | **(a) packet 58** (its own registry artifact, reading B) | receipts F1. The verifier fed a fresh 348-passed junit at cdf1ce4 through the gate's own `pytest_self_destruct_findings` → `_residuals_for` → `gate_currency`. With an empty (full-suite) selection: RED_ORPHANED as committed, GREEN with only that bound removed (`ca58d-verify-1-logs/verify1_judge.log`). The bound was added by 25cfd16 and extended by 1130ac9, both packet 58 commits. |

Even if the suite had completed, D1 alone would give NO-GO under the rule ("any RED_ORPHANED attributed to packet 58").

## FINDINGS — each with its verifier verdict

### Receipt verification (`coldaudit-58-delta-ca58d-receipts.md`)
| id | sev | product | verifier | synthesis |
|---|---|---|---|---|
| F1 `packet-58-fixwave` bound not discharged | major | yes | **CONFIRMED** (independent junit plus judge; `verify1_judge.log`) | All 17 ids are green at cdf1ce4. The bound's own reopen_trigger says it "is deleted with the build". It also still deselects 17 now-green pins from default runs (verifier note on probes R-2). Fix: one commit deleting the bound, then `--verify-registry`. The verifier calls major/product "arguably over-graded" (Decision 4). |
| F3 currency "owned by:" lists every registry bound (#633) | minor | yes | **CONFIRMED** (`verify2-currency.log`, `verify2-typecheck.log`) | Code at `gate_currency` dates to e8087b0 (2026-08-01), before this wave. The verifier corrected one detail: 2 of the 50 errors are in packet-58 test files, but both are owned by `packet-64b-i-contract`, so `packet-58-fixwave` owns 0 of 50. This is a served gate verdict that over-claims. |
| F2 FIXWAVE-1 TREE c01c402b ≠ 70665b9 | minor | no | **CONFIRMED** | The 4 differing tracked files are the lead's e0df22b/8fc46f0 docs and scripts. The production bytes are equal. Re-run on cdf1ce4: `2316 passed, 1 skipped in 370.17s`, EXIT=0, TREE 1ae664a9. |
| F4 builder receipt prose (3 statements) | minor | no | **CONFIRMED** | (a) no fix-wave file is in the 50 typecheck errors; (b) the 29 tests were deselected, not run; (c) 30/30 match once the YAML is decoded. The counts are right. |

### Contract-blind diff read (`coldaudit-58-delta-ca58d-blind.md`)
| id | sev | product | verifier | synthesis |
|---|---|---|---|---|
| F1 concurrent supersedes write a cycle (#634) | major | yes | **CONFIRMED** (`ca58d-verify-batch/vprobe/logs/probe_concurrent_supersede_cycle.log`: control refused; 20/20 in three variants) | The check reads the graph before the transaction, and the transaction re-checks only `CONTAINS old` and the straggler count. The only `asyncio.Lock` is `_connect_lock`. No ruling or docstring bounds concurrency, so the unconditional `TaskCycleError` contract is false on the served shape (one ledger, `asyncio.gather`). |
| F2 closure stops at 32 hops (#635) | major | yes | **CONFIRMED** (`vprobe/logs/probe_depth_bound_cycle.log`: k=40 written, 43-member cycle, on both the supersede and heal legs; controls_ok=True) | The same defect as probes F-B (#637, annotated as a duplicate). `_bounded_dependency_graph`'s docstring, "sound, not a heuristic", is false. |
| F3 the served cycle arrow points opposite ways by noun | minor | yes | **CONFIRMED** (`vprobe/logs/predicate_inmemory.log`) | At aa4ea04 both refusals came from graphlib. At cdf1ce4 persisted ids list `blocked_by` order and batch keys list `blocks` order, under the same sentence. Every member is still named. |
| F4 R6 "ONE shared detector" prose false | minor | no | **CONFIRMED** (`vprobe/logs/mB.log`: only the batch-key test reddens) | The same text defect as sharing D-1 and probes R-1. `_record_legacy_cycles`' "about to mirror" is also stale. |
| F5 the closure read is composed twice | residual | no | **CONFIRMED** (read) | `_refuse_a_cycle` and `_skip_cycle_closing_rows` both run seeds → `_bounded_dependency_graph` → predicate. The F-A and F2 fixes must land in both, or in one helper. |

### Adversary probes (`coldaudit-58-delta-ca58d-probes.md`)
| id | sev | product | verifier | synthesis |
|---|---|---|---|---|
| F-A the heal's closure read times out, so the boot fails (#636) | **blocking** | yes | **CONFIRMED** (`vprobe/logs/fa_scale.log`: 2 failed `exceeded the timeout: 5s`; `fa_control.log` with `stored = {}`: 2 passed, boots in 0.50 s / 8.06 s) | am-17 §12.2 rules out a boot denial. Cost grows as task rows × seeds (0.6 s per seed at 19 200 rows). The live writers share the read, so their latency grows linearly too. Mechanism MEDIUM (no EXPLAIN). How many stragglers production has is unmeasured: aa4ea04 was never deployed (am-17 §12.8), and the 2026-11-08 export holds 234 tasks. |
| F-B closure depth (#637) | major | yes | **CONFIRMED** (`vprobe/logs/depth_det.log`: 2 failed past_depth, controls pass) | A duplicate of blind F2. |
| F-C two wrong builds survive the contract (#638) | minor | no | **CONFIRMED** (`wb5.log` 289 passed with only the determinism probe red; `wb2.log` only S2 red) | Contract gaps for am-17 §13.2 item 4 (determinism) and §13.6 (one read, before packing). The production code is correct at cdf1ce4. |
| R-1 stale `CYCLE_NOUN_PERSISTED_IDS` comment | residual | no | CONFIRMED | Folds into blind F4 / D-1. |
| R-2 `packet-58-fixwave` still active | residual | no | CONFIRMED | The same issue as receipts F1. |

### Sharing by mutation (`coldaudit-58-delta-ca58d-sharing.md`)
| id | sev | product | verifier | synthesis |
|---|---|---|---|---|
| D-1 `find_blocked_by_cycle` docstring and server.py comment claim ONE detector | minor | no | **CONFIRMED** (mB reproduced: `1 failed, 223 passed`) | This is the F6 class reintroduced by cdf1ce4. The prose contradicts am-17 §13.3's own "split by QUESTION". |
| D-2 #130(a) rider half done | minor | no | **CONFIRMED** | The served Field is fixed. The `TaskLedger.query_tasks` docstring is not. The cdf1ce4 message and REPORT-builder-58-1 §FIXWAVE-2 over-claim. |
| D-3 F8 part 1 still open | minor | no | **CONFIRMED** | `store.apply.large_transaction` carries no source, so #628's trigger cannot be checked. `surreal.py` is unchanged across the range. `max_reanchor_dependents` does not cite #628. |
| R-1 the batch-key class test's oracle rides the persisted predicate | residual | no | CONFIRMED | |
| R-2 fixwave legs A/B use `find_blocked_by_cycle` as their "no cycle" oracle | residual | no | CONFIRMED | Vacuous under M-B. The column-unchanged assertions still guard both legs. |
| R-3 `RULED_TIERS` hard-codes the marker literals | residual | no | CONFIRMED | Test hygiene. |
| R-4 `_REANCHOR_LOST_MESSAGE` has no real-trigger test | residual | no | CONFIRMED | MEDIUM. |
| R-5 a test docstring says `_refuse_a_cycle` never fires for supersede | residual | no | CONFIRMED | False since E3. |
| R-6 the first audit's BC-r5-1 probe rotted on the 3-tuple return | residual | no | CONFIRMED | It was adapted in 2 lines and re-run: PROOF HELD. |

Sharing held by mutation (mutation_proof, PROOF HELD both ways):
- Neutralising `find_row_blocked_by_cycles` reddens create, create_many, supersede and heal (22 tests).
- Neutralising `find_blocked_by_cycle` reddens only the 2 batch-key tests.
- Each of the 4 THROW markers is one spelling, and 2 private-copy controls show the probe can see a private copy.

## REGRESSION — the first audit's confirmed items (coldaudit-58.md, graded aa4ea04)

| first-audit item | status at cdf1ce4 | evidence |
|---|---|---|
| blind F1 / #623 the heal writes a cycle | **FIXED for the first audit's world**; the class is **NOT closed** | sharing: the first audit's verifier `probe_verify1.py` re-run leaves D `['X']` and logs WARNING on every boot. But #634 (concurrency), #635/#637 (depth) and #636 (boot timeout) are new doors into the same guard. |
| blind F4 / #624 markers spelled twice | FIXED | sharing §S2: 4 runs plus 2 controls, PROOF HELD. |
| blind F6 docstrings falsified | FIXED (all listed items) | sharing §REGRESSION. A NEW falsified docstring came in with this wave (D-1). |
| blind F7 `_still_claimable` / uuid default | F7a FIXED; F7b kept as a residual (70665b9's choice) | `git show cdf1ce4:…/tasks.py` has no `_still_claimable`. |
| blind F8 hub refusal served text | served text FIXED (driven); trigger attribution **OPEN** (D-3) | sharing `served.log`. |
| probes F1 OB3 missing pin (#626) | pin ADDED (25cfd16, `test_reanchor_58_fixwave.py` §#626) and green in the 301 baseline; **not mutation-re-proven by this delta** | probes `d_baseline.log`. |
| probes F2 packer prose "transaction cap" (#625a) | FIXED (driven) | sharing §REGRESSION. |
| sharing F-1 / #622 wrong probe cited | FIXED | sharing §REGRESSION. |
| sharing F-2 116 vs 234 tasks | FIXED | `git show cdf1ce4:` am-15 line ~110 and am-17 lines ~161/183 say 234 and mark 116 superseded (380414c). |
| receipts F-1/F-2/F-3 (builder TREE, older test bytes, 237+1) | superseded: they graded aa4ea04 receipts | This delta's receipts dimension re-graded the fix-wave receipts (F1–F4 above). |
| ground 1: the secret-seam RED_ORPHANED (packet 58 probe env reads) | FIXED | 25cfd16 made the probe knobs argparse. sharing `secret.log`: 1 passed. |
| refuted-with-residual F5 / #130(a) served wording | FIXED on the served surface; the #130(a) ledger docstring is **not done** (D-2) | sharing §REGRESSION. |

## DECISIONS

1. **Escalate the cycle guard's DESIGN (operator or lead; recommended).**
   - Two waves running, defects of one class have reached the same guard: #623, then #631 inside wave 1; now #634, #635/#637 and #636. Each wave fixed the predicate. Each new door is in the predicate's INPUT: a stale read (#634), a bounded read (#635) and a costly read (#636).
   - Per CLAUDE.md ("when the same class of defect survives TWO waves, STOP briefing a third fix and escalate the DESIGN"), this goes to a design author or the sidecar, not a builder brief.
   - The questions it has to answer: one closure read inside the write transaction or a ledger-level write lock (#634); an unbounded or engine-side reachability check vs a bound named in the served render (#635); and a read whose cost does not grow with task rows × seeds (#636). blind F5 says the fix needs one composed helper.
2. **Full-suite re-run (lead).** A solo run of the sanctioned command hits #508 every time: this run, and audit-parked-1's first attempt today. Options:
   - (i) fix #508 (`SOLO_PYTEST_WORKERS` → 12) before the next packet full suite. This is a script change, routed to packet 09b per the ledger;
   - (ii) run the suite while another pytest session is live. That is luck, not a mechanism;
   - (iii) the operator rules a different cap.

   I recommend (i). The re-run belongs after the design fix in Decision 1 anyway.
3. **Delete the `packet-58-fixwave` bound (lead, one commit, then `--verify-registry`).** Independent of Decision 1. Until then it hides 17 green pins from default runs and orphans the pytest leg.
4. **Severity of receipts F1.** It is major/product by the auditor's label and confirmed. The verifier argues it is a missed registry discharge, not served behaviour. The NO-GO does not depend on it (grounds 1–3 stand without it).
5. **Duplicate rows.** #635 and #637 are one defect; I annotated #637. Keep one, close the other.
6. **Filing.** Filed by the dimensions: #633, #634, #635, #636, #637, #638. **Not filed:**
   - blind F3 (arrow direction, served);
   - blind F4 / D-1 (stale R6 prose);
   - D-2 (the #130(a) docstring);
   - D-3: annotate #625/#628, or a new row.

   The lead files these, or tells me to.
7. **R6 amendment.** cec81c2 says R6 was amended to "one detector per question" and "flagged for the operator". That ruling is an operator item and is still open. D-1's prose fix should follow it.

## COST

- **Agents:** 4 dimension auditors (receipts, blind, probes, sharing), 3 verifiers (verify-1, verify-2, verify-batch), 1 full-suite haiku-runner and this synthesiser: 9.
- **Runs:**
  - 1 full suite, OOM-killed after 49.5 s;
  - receipts: 1 targeted run (2316 passed, 370 s) plus 2 gate-script runs;
  - blind: 3 probes;
  - probes: 26 runs, including WB0–WB7;
  - sharing: about 15 runs (baselines, mA/mB, 4 marker mutations, 2 controls, BC-r5-1/2, served, secret, f1_verify);
  - verifiers: about 12 runs and judges;
  - me: 0 test runs.
- **Wall time:** about 37 min, from `full-copy.log` at 2026-11-10 02:29:05 -0500 to this synthesis at about 03:06 (the last verifier artifact is at 02:58).
