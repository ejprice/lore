# Packet 58 cold audit — synthesis (ca58-synth)

brief-base v27 read · brief project v7 read

## SUMMARY BLOCK

- **Verdict: NO-GO** (graded aa4ea04, measured 2026-11-10). Two independent grounds, either one sufficient:
  1. **A full-suite RED_ORPHANED caused by packet 58's own work.** `loremaster/tests/test_secret_resolution_seam.py::TestSecretResolutionHasExactlyOneEntryPoint::test_every_environment_read_is_the_entry_point_or_allowlisted` fails at aa4ea04 on exactly one site, `scripts/probe_hub_txn_58.py::<module>`. That probe was added by bed62bd `test(58): contract r5`, and its env reads (`PROBE_TXN_TIMEOUT`, `PROBE_SETTLE`) are present at bed62bd, 60b51c4 and aa4ea04. See the attribution-reading fork under §ATTRIBUTION.
  2. **A confirmed major product defect: blind F1.** The boot straggler heal writes a `blocked_by` cycle and logs it as a success. Verifier: refuted=false, reproduced=true. The verdict rule does not map this case (see Decisions 1).
- **State:** done-with-deviations.
- **Graded:** aa4ea04 · HEAD-at-report 7e2319f · DIFFERENT (5 ahead). What moved: 54004dd, 7e2319f and three others are the parked-contracts session's commits plus one docs-only 58 erratum (96ea7f5). Production diff aa4ea04..HEAD over the workspace members is 2 files, `lorerunes/lorerunes/worker_output.py` and `loremaster/tests/conftest.py` (`git diff --stat aa4ea04 HEAD -- loremaster lorerunes lorescribe loresigil`). Neither is a file the 58 verdicts rest on (`tasks.py`, `server.py`, `store/_txn.py`, `scripts/probe_hub_txn_58.py` are unchanged).
- **Full suite** (aa4ea04 content, TREE=40f080f6…, DIRTY_FILES=4, and those 4 are the untracked REPORT-*.md files):
  - Command: `flock … systemd-run … MemoryMax=16G … pending_contract_gate.py --currency`.
  - Result: EXIT=1, no 137. Wall time 17 min 24.6 s; 50 min 32 s CPU; memory peak 9.2 G (systemd scope accounting, 23:53:51 to 00:11:16 -0500).
  - Gate legs: typecheck RED_ADJUDICATED (50, packet-64b-i-contract) · ruff GREEN · pytest RED_ORPHANED (24).
  - **Passed-count NOT OBSERVED.** The `--currency` render does not print `_read_pytest_leg`'s count line, and the junit was in a TemporaryDirectory that has since been deleted. Completion is inferred, not counted: the gate parsed a junit and refuses both a missing document and a zero-collected one.
- **Confirmed findings** (refuted=false, reproduced=true):
  - majors: blind F1 (heal writes a cycle) and blind F4 (THROW markers spelled twice; sharing fails by mutation);
  - minors: blind F6, F7 and F8; probes F1 (OB3 survives the contract) and F2 (packer prose claims the transaction cap); sharing F-1 (#622) and F-2; receipts F-1, F-2 and F-3.
- **Refuted:** blind F2 (ruled, kickoff §5(a)), F3 (ruled, kickoff F-2 and inventory item 9), F5 (ruled bound, am-1 R2) and F9 (no test distinguishes the two spellings). Each leaves a residual, recorded below.
- **Residuals:**
  - 2 adjudicated `findings.py::_run_guarded` 64b-i reds in every targeted run;
  - #621 (`--legs` exits 1);
  - the 25 tracked root REPORT files to archive;
  - TEST-store debris: 135 dbs, 60 harness-named, 51 of those from dead pids;
  - #508 (the full suite may have run `-n auto`);
  - verifier and dimension residuals R-1…R-5, R-r53-1, R-PR14 and probes R-1…R-3.
- **Decisions needed:** 5, listed in §DECISIONS (the verdict-rule gap, the attribution reading, how to fix the secret-seam red, the stale served prose, and filing).
- **Deviations:**
  - D1: no Agent tool, so the one targeted rerun ran inline;
  - D2: I did not rerun the full suite, which already ran once for this packet;
  - D3: the full-suite count is unobservable from the instrument;
  - D4: no lore findings filed (see Decisions 5).
- `Packages considered: none — no mechanism specified` · `Odoo-20 portability: n/a — no Odoo seam touched` · `Reuse ledger: none` (synthesis only).
- **Receipt pointers:** the four dimension files `coldaudit-58-ca58-{receipts,blind,probes,sharing}.md` in this directory · the full-suite log and the `synth-secret-seam.log` targeted rerun (§RUNS).

## ROUTING TABLE (brief-base §3)

| step | tier | who | reason |
|---|---|---|---|
| read the full-suite log (38 lines) | 1 | self, inline | It is on the critical path and I read every line; the brief says "read it yourself". |
| attribute 24 orphans | 3 | self | It needs git ancestry and per-file history. A sampled draft would miss the base/range-reading fork, which decides the verdict. |
| run 1 orphan test at aa4ea04 | 1 | self, inline | No Agent tool, so no haiku-runner (D1). It was one node id taking 1.3 s. |
| verdict + synthesis | 3 | self | This is the final verdict. |

Fan-out: haiku 0 · sonnet 0 · peak 0.

## RUNS

- Full suite (not mine; read as the ground truth): `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58/full-suite.log`. HEAD=aa4ea04, TREE=40f080f6b8185396394d862637256df9e17d67bbfaeff5bde0f030aae1580f24 (the same TREE as the blind dimension's copy). `git -C <full copy> status --short` lists exactly the 4 untracked REPORTs. Wall time, CPU and memory come from `journalctl --user -u run-p96283-i163547669.scope`.
- My targeted rerun, in the same copy (`loremaster.__file__` = `…/ca58/full/loremaster/loremaster/__init__.py`), under `systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 .venv/bin/python -m pytest -q -p no:cacheprovider --timeout=300 <secret-seam node id>`. Log: `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58/logs/synth-secret-seam.log`. TREE=40f080f6…, `1 failed in 1.27s`, EXIT=1. Failure text: `E assert not ['scripts/probe_hub_txn_58.py::<module>']`.

## ATTRIBUTION — the 24 full-suite RED_ORPHANED node ids (at aa4ea04)

Evidence common to rows 2-24: `scripts/test_parked_contracts.py` was added by 54c7595 (2026-11-09 23:47:15, `test(parked): contract … 23 tests, RED@HEAD 99389cd`). That is the parked-contracts session's contract phase, red by design. 54c7595 is an ancestor of aa4ea04, because the branch is shared and aa4ea04 was committed at 23:50:44. The commit says 23 tests, and the orphan list has exactly 23 ids from this file. At aa4ea04 no registry entry owns them. Ownership arrived at 54004dd (`31 RED@HEAD owned by the new parked-deselection-contract bound`), and that bound self-destructed with the fix at 7e2319f. None of these ids appear in base2.xml, because the file did not exist at 60b51c4.

| # | node id | class | evidence |
|---|---|---|---|
| 1 | `loremaster/tests/test_secret_resolution_seam.py::TestSecretResolutionHasExactlyOneEntryPoint::test_every_environment_read_is_the_entry_point_or_allowlisted` | **(a) packet 58**, under reading B; (c) under reading A | The only unlisted site is `scripts/probe_hub_txn_58.py::<module>` (synth-secret-seam.log). The probe was added by bed62bd `test(58): contract r5` with `os.environ.get("PROBE_TXN_TIMEOUT"…)` / `("PROBE_SETTLE"…)`, which are still present at 60b51c4 and aa4ea04. The test file was last touched 130fa16 (2026-08-16), so the test did not change; packet 58's file did. The test is not in base2/final3/regreen.xml (0 hits), so the builder's targeted set never ran it. Since 548fe54 (decision 6, in range), the default targeted scope no longer adds structural scanners, so only the full suite could catch this. |
| 2 | `scripts/test_parked_contracts.py::TestDefaultRunDeselection::test_parked_nodes_are_deselected_under_xdist` | (b) | common evidence above |
| 3 | `…::TestDefaultRunDeselection::test_naming_a_parked_node_on_the_command_line_does_not_exempt_it` | (b) | " |
| 4 | `…::TestDeselectionReport::test_native_deselected_count_includes_the_parked_nodes` | (b) | " |
| 5 | `…::TestDeselectionReport::test_native_count_adds_parked_nodes_to_other_deselection` | (b) | " |
| 6 | `…::TestDeselectionReport::test_summary_line_names_count_involved_entries_and_flag` | (b) | " |
| 7 | `…::TestDeselectionReport::test_summary_count_excludes_nodes_deselected_by_other_means` | (b) | " |
| 8 | `…::TestDeselectionReport::test_summary_names_only_entries_whose_nodes_this_run_deselected` | (b) | " |
| 9 | `…::TestDeselectionReport::test_summary_line_is_printed_once_under_xdist` | (b) | " |
| 10 | `…::TestRunParkedFlag::test_run_parked_runs_every_collected_node` | (b) | " |
| 11 | `…::TestBrokenRegistry::test_broken_registry_deselects_nothing_and_warns_once[absent]` | (b) | " |
| 12 | `…::TestBrokenRegistry::…[unparseable]` | (b) | " |
| 13 | `…::TestBrokenRegistry::…[unknown-key]` | (b) | " |
| 14 | `…::TestBrokenRegistry::…[non-boolean-active]` | (b) | " |
| 15 | `…::TestBrokenRegistry::…[misfiled-node-id]` | (b) | " |
| 16 | `…::TestActiveField::test_active_is_read_per_bound_with_false_default` | (b) | " |
| 17 | `…::TestActiveField::test_non_boolean_active_is_a_registry_error[string]` | (b) | " |
| 18 | `…::TestActiveField::test_non_boolean_active_is_a_registry_error[integer]` | (b) | " |
| 19 | `…::TestGateRunsParked::test_manifest_pytest_gate_command_carries_run_parked` | (b) | " |
| 20 | `…::TestGateRunsParked::test_leg_runner_spawns_the_pytest_gate_with_run_parked[full-run]` | (b) | " |
| 21 | `…::TestGateRunsParked::test_leg_runner_spawns_the_pytest_gate_with_run_parked[wave-run]` | (b) | " |
| 22 | `…::TestGateRunsParked::test_gate_command_observes_parked_reds_end_to_end` | (b) | " |
| 23 | `…::TestDefaultRunDeselection::test_default_run_runs_exactly_the_unparked_nodes` | (b) | " |
| 24 | `…::TestDefaultRunDeselection::test_unparked_red_in_a_parked_file_still_fails_the_run` | (b) | " |

Totals: (a) 1 · (b) 23 · (c) 0 · (d) 0, all under reading B.

**The attribution-reading fork (brief-base §2), stated and not resolved silently.** The rule says *(a) introduced by 60b51c4..aa4ea04 production or by packet 58 tests*.
- **Reading A:** only commits inside the range count. Under it, row 1 is (c), red at base: bed62bd is older than 60b51c4.
- **Reading B:** packet 58's own artifacts count wherever they fall in the packet. 60b51c4 is a mid-packet base (it is r5.2, and packet 58 began 2026-09-26), and bed62bd is a `test(58)` contract commit.

I pick **B**. The point of the gate is that packet 58's once-per-packet full suite leaves no red with nobody's name on it, and this red exists only because of a packet-58 file. Under reading A the verdict still rests on F1 (Decisions 1).

## FINDINGS — each with its verifier verdict

The receipt file for each dimension is in this directory. Verifier instruments and logs: `…/scratchpad/ca58/verify1-notes/`, `…/verify2-notes/`, `…/vb-logs/`.

### Contract-blind diff read (`coldaudit-58-ca58-blind.md`)
| id | sev | verifier | synthesis |
|---|---|---|---|
| F1 heal writes a `blocked_by` cycle, logs success | major | **CONFIRMED** (verify1-notes/probe_verify1.log) | **Product defect.** `_plan_heal_rows` never runs `_refuse_a_cycle`; the live supersede does. No ruling covers it: am-3 §4 is live-only, am-3 §5 covers chain cycles and phantoms, and am-17 has no "cycl". Narrowed: the cycle IS recorded on later boots, mislabeled `legacy_cycle_minted`, when some unrelated edge is missing, because `_backfill_blocks_edges` returns early when nothing is missing. It is never recorded on the boot that wrote it. The claim render also changes from "can never resolve" to "unresolved". |
| F4 THROW markers spelled twice | major | **CONFIRMED** (vb-logs/p5_mut.log) | A latent code defect (ROUTING-IS-NOT-SHARING). Editing `_txn.CLAIM_LOST_MARKER` makes a losing claim raise `TxnDomainRejectionError`. The same applies to the cas_lost, heal_chunk and reanchor_straggler markers. |
| F2 status/blocked filters exclude superseded rows | major | REFUTED (ruled: kickoff §5(a), inventory item 5, pinned by `test_task_claimable_partition_58.py`, 10 passed) | Residual: the `lore_tasks` `status` Field and the `query_tasks` docstring still say "exact-status filter" without naming the exclusion. `status=superseded` answers "no tasks matched", which is accepted (#130 shape (b), packet 57). |
| F3 re-anchor re-stamps `updated_at` on DONE dependents | major | REFUTED (ruled: kickoff F-2, inventory item 9, §4 rider (iv)) | Residual, folded into F6: the `updated_since` docstring and the `_COL_UPDATED_AT` comment omit the re-anchor and heal stamps. |
| F5 create racing a supersede strands a row | minor | REFUTED (ruled bound: am-1 R2, inventory item 10) | Residual for the operator: the served text adds "so this claim can never win", which over-claims once the next boot heal re-anchors. The ruling's form was "can never resolve; block on the successor". |
| F6 docstrings falsified by the diff | minor | CONFIRMED | `supersede_task` Returns/Raises, `direct_dependents`, the `claim_task` comment, `_refuse_a_cycle` "already RECORDED", `_render_supersede_result` "[] by construction", plus F3's `updated_since` text. |
| F7 dead `_still_claimable` and unreachable uuid default | minor | CONFIRMED | 0 prod / 0 test callers. |
| F8 hub-bound trigger unattributable; served refusal stale | minor | CONFIRMED | `store.apply.large_transaction` carries no source. The 5,700-16,665 timeout band has no finding number and is not served. The served text says "pinned KNOWN BOUND (58 F-1); file it with lore_findings", which uses retired wording, gives a reference the consumer cannot resolve, and leads to a duplicate finding per refusal. This is a TRUST Leg-1 defect on a served surface. |
| F9 re-spelled production to re-green a scanner | minor | REFUTED (vb-logs/f9_concat_regreenset.log: both spellings give the same counts) | Only the commit message is imprecise. |
| R1 six design residuals | residual | CONFIRMED | Its design question (should terminal dependents be re-anchored?) is already ruled (kickoff F-2). |

### Receipt verification (`coldaudit-58-ca58-receipts.md`)
| id | sev | verifier | synthesis |
|---|---|---|---|
| F-1 builder final3/REGREEN TREE ≠ aa4ea04; the tree changed mid-run | minor | CONFIRMED | The receipts are void under brief-base §1. The production claim was re-established by the auditor's clean reruns on aa4ea04: 1977 ids, 2 failed (both 64b-i), 1974 passed, 1 skipped. |
| F-3 "238 base reds now green" is really 237 green plus 1 re-keyed out | minor | CONFIRMED | Benign re-key. |
| F-2 final3 tested older test bytes | residual | CONFIRMED | Covered by this packet's full suite, subject to D3. |
| R-1 REF2 copy time ~03:44:57Z, not ~03:51Z | residual | CONFIRMED | |
| R-2 g2 TREE moves with DIRTY unchanged | residual | CONFIRMED | Explained: appending to the untracked report changes TREE. |
| R-3 `--legs` currency exits 1 on a clean run | residual | CONFIRMED | #621. |
| R-4 25 REPORT-*.md tracked at the root, 9 of them packet 58's | residual | CONFIRMED | Close-out `git mv` per ARCHIVE REPORTS. |
| R-5 TEST-store debris | residual | CONFIRMED class; attribution unknown | 135 dbs in `lore_test`. 60 are `test_<pid>_*` from 54 pids, of which only 3 are alive. |

### Adversary probes (`coldaudit-58-ca58-probes.md`)
| id | sev | verifier | synthesis |
|---|---|---|---|
| F1 OB3 (DELETE only edges to read dependents) survives the contract | minor | CONFIRMED (vb-logs/ob3_wide.log, 17 files: 2 failed (64b-i) / 900 passed) | A missing pin: no fixture has a drift edge out of the hub. am-17 §9.2's "pinned today" holds only in mirror-consistent worlds. The built tree is correct, since the auditor's Q4 is green. |
| F2 `StragglerHealPackerError` says "10000-row transaction cap" | minor | CONFIRMED | The transaction cap is 50000; 10000 is the chunk bound. This prose is served on every failed boot, which makes it TRUST teaching prose that does not match behaviour. |
| R-1 OB1 killed only by r3_convergence F10 | residual | CONFIRMED | Scope note for future targeted runs. |
| R-2 `$ssx_old` defined in another fragment's params | residual | CONFIRMED | 3 pins catch OB7. Class question D3 (compose refusing an undefined `$param`) goes to the operator. |
| R-3 am-17 §5/§11 figures are distinct-head only; adversary arithmetic slip | residual | CONFIRMED | Wording only. |

### Sharing (`coldaudit-58-ca58-sharing.md`)
| id | sev | verifier | synthesis |
|---|---|---|---|
| F-1 `max_reanchor_dependents` cites the wrong probe | minor | CONFIRMED | Filed as #622. |
| F-2 rulings carry 116 tasks; the 2026-11-08 export holds 234 | minor | CONFIRMED | No outcome changes (the largest hub has 4 dependents). |
| R-r53-1 SWALLOWS control passes an under-reporting sweep | residual | CONFIRMED | A test-hygiene gap in the instrument; no product door reached. |
| R-PR14 hard-codes per=3 | residual | CONFIRMED | Test hygiene. |

The sharing dimension proved BC-r5-1 and BC-r5-2 by mutation (PROOF HELD). All 7 W-* builds and #130 W130-T die. The real-population heal ran as 1 chunk on both production exports.

## DECISIONS

1. **Verdict-rule gap (operator or lead).** The rule's NO-GO clause needs severity *blocking*, and its GO-WITH-RESIDUALS clause excludes product defects. A **confirmed major product defect** (F1, and F4 as a latent one) fits neither, so a literal "GO otherwise" would pass it. I rule NO-GO on F1, because the heal writes a state the live path refuses and serves it as success. Ground 1 (the attribution) gives NO-GO independently under reading B.
2. **Attribution reading A vs B for row 1.** My recommendation is B.
3. **How to clear the secret-seam red.** Three options:
   - (i) An evidence-backed `ENV_READ_ALLOWLIST` entry for the probe's two operational knobs. This is a test edit, so it belongs to the contract author or a test-writing agent, not a builder.
   - (ii) Turn the probe's knobs into argparse parameters. This edits a script, so it belongs to a builder.
   - (iii) Cut the scanner per decision 6 (548fe54), which lists it among the source scanners to be cut in Phase 4. This needs an operator ruling.

   I recommend (ii) now. It removes the env read and keeps the probe's knobs explicit.
4. **Fix wave scope.** Code fixes for F1 and F4, plus the served-prose fixes F8 and probes F2. Doc fixes for F6 and sharing F-1/F-2. A missing pin for probes F1. A decision on dead code F7. The F2/F5 served-wording residuals go to the operator, because both rulings left the text as it is.
5. **Filing.** Only sharing F-1 is filed (#622). Blind F1, F4 and F8 and probes F1 and F2 need `lore_findings` rows. I did not file them, to avoid duplicating the lead's filing (D4); the lead files them or tells me to.

## COST

- **Agents:** 4 dimension auditors (receipts, blind, probes, sharing); verifiers, at least 3 by artifact dirs (verify-1, verify-2, verify-batch/vb-logs); 1 full-suite haiku-runner; this synthesiser. That is at least 9.
- **Runs:**
  - 1 full suite (17 min 24.6 s wall);
  - dimension and verifier targeted, mutation and probe runs: about 44 logs in `ca58/logs` and 15 in `vb-logs`, not counted individually;
  - my 1 targeted rerun.
- **Audit wall time:** about 53 min, from the scratch-copy log at 2026-11-09 23:51:38 to the last dimension or verifier log at 2026-11-10 00:44 (file mtimes, -0500).
