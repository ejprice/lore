# coldaudit-58-delta-ca58d-sharing — packet 58 fix-wave DELTA audit, dimension: sharing by mutation + regression of the first audit's confirmed findings

## SUMMARY BLOCK
- brief-base v27 read · brief project v7 read · landmines recalled (k=50 returned 10, not cut off) · registered on lore_comms as `ca58d-sharing` (session pkt58-20261109, role auditor).
- State: **done-with-deviations**. Verdict for this dimension (graded cdf1ce4, measured 2026-11-10): **GO-WITH-RESIDUALS.** No product defect found. Every sharing mutation in the brief PROVED sharing, run by `scripts/mutation_proof.py` with the declared set fixed before the run and matched exactly both ways.
  - am-17 §13.3, mutation 1: `find_row_blocked_by_cycles` → `{}` reddens 22 declared ids, covering create, create_many, supersede and heal. mutation 2: `find_blocked_by_cycle` → `None` reddens ONLY the 2 batch-key pins, and none of the persisted-row pins. Both PROOF HELD.
  - #624: each of the 4 THROW markers was respelled in turn. Each time, only that marker's literal-oracle leg reddened. The real-trigger legs (8-way claim race, lost transition, lost supersede, lost finding transition, R1 straggler, heal chunk row moved) stayed GREEN: their DOMAIN errors and ruled tiers held. A private producer spelling (control, claim and cas) reddens the real-trigger leg, so the instrument can see a private copy.
  - BC-r5-1 and BC-r5-2, re-run once each: both PROOF HELD.
- Regression of the first audit's confirmed items: F1/#623 FIXED (its verifier probe re-run). F4/#624 FIXED. F6: every listed docstring is now true. F7a FIXED. Probes F2/#625a FIXED (driven). #622 FIXED. Secret-seam scanner test GREEN. F5 and #130(a) served texts FIXED (driven). F8 served text FIXED (driven). One part of F8 is still open (finding D-3).
- Findings: **D-1 minor**: the fix wave made `find_blocked_by_cycle`'s docstring and server.py's batch-key comment false ("ONE detector… BOTH shapes must stop being refused"), and my M-B run measures that claim false. **D-2 minor**: am-17 §12.7's #130(a) rider asked for the `query_tasks` docstring to name the superseded-row exclusion, and it was not done. **D-3 minor**: F8 part 1 is still open. A `store.apply.large_transaction` record still carries no source, so #628's re-open trigger ("…from the task ledger") cannot be attributed. The `max_reanchor_dependents` docstring does not cite #628. Residuals R-1…R-6 (§RESIDUALS).
- Deviations:
  - (1) Test runs were inline: this agent has no `Agent` tool (brief-base §3).
  - (2) The first audit's BC-r5-1 probe `test_probe_sharing_ca58.py` broke at cdf1ce4 on an API change: `_plan_heal_rows` now returns a 3-tuple, so the packer leg raised IndexError. I adapted it in 2 lines as `test_probe_sharing_ca58d.py` (diff in §INSTRUMENTS) and re-ran BC-r5-1 on it. The first BC-r5-1 run on the broken probe is void (`bc1.log`, EXIT=4).
  - (3) PR14 is declared in BC-r5-1. It is the first audit's measured undeclared red (coldaudit-58-ca58-sharing.md §M1), so it was known before this run and not read off it.
- Packages considered: none — no mechanism specified (probes only). Odoo-20 portability: n/a — no Odoo seam touched. Reuse ledger: none (no production symbols; the scratch probes are in §INSTRUMENTS).
- Graded: cdf1ce4 · HEAD-at-report: cdf1ce4 · SAME.
- Decisions needed: (a) D-3: is a source field on `store.apply.large_transaction` in the fix wave's scope? #625's body says "fix in packet 58's fix wave" and names the unattributable trigger. (b) Who files D-1…D-3? I filed nothing, to avoid duplicating the synthesis (same posture as the first audit's D4).
- Pointers: §PROVENANCE · §S1 (cycle predicate) · §S2 (markers) · §S3 (BC-r5) · §REGRESSION · §FINDINGS · §RESIDUALS · §INSTRUMENTS. Logs: `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58d/ca58d-sharing-logs/`. In the rest of this file, `LOGS/` means that directory.

## ROUTING TABLE (written 2026-11-10 before the first sweep, after the copy was made)
| step | tier | who | reason |
|---|---|---|---|
| scratch copy + provenance receipt | 1 | inline | one scripted command, output read whole |
| locate the cycle pins and marker consumers in the unindexed scratch copy (grep / an AST lister) | 1 | inline, one parallel batch | Small, on the critical path, read whole. No `Agent` tool in this agent's toolset, so no haiku-worker is reachable. |
| declare expected-RED sets (from `--collect-only --run-parked`) | 3 | me | a mutation-proof verdict; never Haiku |
| mutation runs via `scripts/mutation_proof.py` | 1 | **inline: no `Agent` tool** (brief-base §3: "with no `Agent` tool … run inline. Say which") | |
| driving the served refusals (F8, probes F2, F5, #130(a), #625) | 3 | me | reading served text against a claim is a verdict |
| F6 docstring reads | 2 → kept | me | A Sonnet draft would miss whether each docstring is TRUE of the new code, which needs the code read beside it. The set is ~7 items. |
| verdicts | 3 | me | |

Fan-out: haiku 0 · sonnet 0 · peak 0 (no `Agent` tool).

## §PROVENANCE (measured 2026-11-10)
- Copy: `scripts/scratch_copy.sh …/scratchpad/ca58d/ca58d-sharing` gave EXIT=0 (`ca58d-sharing.copy.log`). Then `git checkout cdf1ce4 -- .`.
  - `rev-parse HEAD` = `cdf1ce40680aafcb0ffe8d836ff3ae0e506eca68`.
  - Status at start: 6 untracked files only. They are the 5 root REPORTs and a sibling dimension's delta file copied from the live tree.
- `loremaster.__file__`, `_txn.__file__` and `tasks.__file__` all resolve inside the copy (`…/ca58d/ca58d-sharing/loremaster/loremaster/…`). `f1_verify.log` prints it again.
- TREE ids:
  - `1ae664a9…` = the pristine copy. The baselines, S1 and S2 ran on it.
  - `64455894…` = the copy plus my two untracked probes. The served probe, the secret-seam test, the F1 verifier, `baseline_bc`, `bc1` (void) and `bc2` ran on it.
  - `571b6c56…` = the copy with the adapted BC-r5-1 probe. `baseline_probe` and `bc1b` ran on it.
- After every run, `git diff --stat` is empty and each mutated file was restored byte-exact (`RESTORED_BYTE_EXACT` in each log, plus `<run>.md5_before/after`).
- Store: TEST only (`ws://127.0.0.1:18000`, harness `DEFAULT_URL`). The `ledger58` fixture mints and reaps every database, and the F1 verifier drops its own.
- Every pytest ran under `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0`, with `-n 8` on suites and `--timeout=300` on every run. No empty selection: both runners exit 8 on an empty scope or declared set.
- The parked deselection was live. `--collect-only --run-parked` counted 641 in the cycle scope, the same as the default collection, so no parked ids were in scope. The BC scope collected 380 with `--run-parked` and ran 378: 2 parked ids were deselected by default.
- lore: `lore_index()` was current at cdf1ce4 (watched root `/workspace`, git_ref cdf1ce4). `lore_impact(find_row_blocked_by_cycles)` gave `2 prod / 0 test, tests: none detected`. That is the known #563/#557 gap, so the covering tests were found by grep plus an AST lister over the scratch copy (bare grep, rename-exhaustiveness and textual-seam cases), and I say so here.

## §S1 — the persisted-row predicate vs the batch-key detector (am-17 §13.3, two runs)
- Scope (`LOGS/scope_cycle2.txt`, 641 ids): `test_blocks_edge.py`, `test_cycle_write_path_04b3.py`, `test_reanchor_58_fixwave.py`, `test_reanchor_58_r2_rulings.py`, `test_supersede_reanchor_58.py`, `test_task_ledger.py`, `test_reanchor_58_r3_convergence.py`, `test_supersede_render_58.py`, and `test_mcp_server.py::TestCreateManyDispatch`.
- Unmutated baseline (`LOGS/baseline_cycle.log`, TREE 1ae664a9, the first 631 ids without the mcp class): `631 passed`, EXIT=0.
- **M-A**: `find_row_blocked_by_cycles` gains `return {}` as its first statement.
  - Declared (`LOGS/mA_declared.txt`, 22 ids, by reading each test before the run):
    - blocks_edge `TestCreateRefusesToFormACycle`: batch ids, SELF, through PERSISTED, MINTED+LEGACY;
    - `TestTheCyclePolicyHasONEImplementation`: BATCH_KEY class (see R-1), MUTATION batch-key, MUTATION formatter;
    - `TestTheRowExistencePolicy…::test_the_CYCLE_error_is_NOT_an_existence_error`;
    - fixwave A, B, C, E1×2, E3×2, D2_i×2, D2_ii;
    - r2_rulings the two `TestOnlyACycleThroughXPrimeIsRefused` CONTROL refusals;
    - supersede_reanchor `test_refused_as_a_cycle_naming_it_and_NOTHING_changed` and `test_after_a_REFUSED_supersede_the_backfill_mints_nothing`.
  - `LOGS/mA.log`: `22 failed, 619 passed` · **PROOF HELD** · EXIT=0 · restored.
  - Every writer reddens: create_many (self loop and through a persisted row), supersede (E3 and the two r2 CONTROLs), and the heal (A/B/C/E1/D2). `create_task` cannot be offered a persisted cycle, because its id is minted inside the verb (the contract's own note). The in-test mutation-1 pin stays GREEN, as it should. (HIGH)
- **M-B**: `find_blocked_by_cycle` gains `return None` as its first statement. `server.py` imports the same function object.
  - Declared (`LOGS/mB_declared.txt`, 2 ids): `test_blocks_edge.py::TestTheCyclePolicyHasONEImplementation::test_a_BATCH_KEY_cycle_at_the_TOOL_SEAM_raises_the_LEDGERS_cycle_CLASS` and `test_mcp_server.py::TestCreateManyDispatch::test_intra_batch_cycle_is_refused_and_NAMES_every_member`.
  - `LOGS/mB.log`: `2 failed, 639 passed` · **PROOF HELD** · EXIT=0 · restored.
  - None of the 22 persisted-row pins reddened, so no writer asks the batch-key detector. (HIGH)

## §S2 — #624: the four THROW markers are one spelling each
- Scope (`LOGS/scope_marker.txt`, 411 ids): `test_reanchor_58_r3_tiers.py` (the REAL triggers per class), `test_reanchor_58_r3_am6.py`, `test_reanchor_58_r2_rulings.py`, `test_reanchor_58_r5_rows.py`, `test_task_ledger.py`, `test_task_guarded_shell_58.py`, `test_reanchor_58_fixwave.py`, `test_supersede_reanchor_58.py`.
- Baseline (`LOGS/baseline_marker.log`): `411 passed`, EXIT=0.
- Mutation: `_txn.<X>_MARKER = "<m>:"` → `"<m>q:"`. The new spelling still contains the old stem, so the r2 AST pin (which counts `claim_lost` constants) cannot redden for a spelling reason.
- Declared per run: only the am-6 literal-oracle leg, which hard-codes the marker (`test_P6_each_ruled_tier_and_the_deny_by_default[<m>]`), plus `test_P6_mutation_dropping_ONE_table_entry…` for the straggler marker, which spells `"reanchor_straggler: x"`. This is the landing evidence. Every other leg staying GREEN is the sharing claim.

| marker | log | result |
|---|---|---|
| CLAIM_LOST_MARKER | `mk_claim.log` | 1 failed, 410 passed · PROOF HELD |
| CAS_LOST_MARKER | `mk_cas.log` | 1 failed, 410 passed · PROOF HELD |
| REANCHOR_STRAGGLER_MARKER | `mk_straggler.log` | 2 failed, 409 passed · PROOF HELD |
| HEAL_CHUNK_MARKER | `mk_heal.log` | 1 failed, 410 passed · PROOF HELD |

- The domain errors held under every mutation. The following stayed GREEN:
  - the losing claimants of an 8-way race still get `claimed=False` at DEBUG;
  - a claim of a BLOCKED task (the p5 shape, r2 `test_the_ledger_catches_the_TYPE_never_the_text` control leg) is still a `ClaimResult`, not the `TxnDomainRejectionError` the first audit's `vb-logs/p5_mut.log` showed at aa4ea04;
  - the lost transition, lost supersede and lost finding transition still raise `IllegalTransitionError` at WARNING;
  - the R1 straggler still raises `SupersedeStragglerError` at WARNING;
  - a heal chunk whose row moved still rolls back at WARNING.

  **Sharing HOLDS for all four.** (HIGH)
- **Positive controls** (a probe needs a control): a PRIVATE producer spelling in `tasks.py`, with the shared constant unchanged. Scope `test_reanchor_58_r3_tiers.py::TestEachClassRollsBackAtItsTier` (8 ids).
  - `c_claim`: the claim shell's `throw_message` becomes `f"claim_lostp:{task_id}"`. Declared `[TxnClaimLostError-claim-race-8-way]`. Result: `1 failed, 7 passed` · PROOF HELD; the losers raise `TxnDomainRejectionError … (unspecified rejection)`, the aa4ea04 shape.
  - `c_cas`: `_SUPERSEDE_ALREADY_MESSAGE` becomes `"cas_lostp: …"`. Declared `[TxnCasLostError-lost-supersede-PA1]`. Result: `1 failed, 7 passed` · PROOF HELD.

## §S3 — the first audit's BC-r5-1 and BC-r5-2, re-run once each
- Scope: the first audit's `logs/scope.txt` plus `test_reanchor_58_fixwave.py`. The probe file is the adapted `test_probe_sharing_ca58d.py` (Deviation 2).
- `baseline_bc.log` (old probe): `1 failed, 377 passed`. The 1 failure is the probe's packer leg, `IndexError` at `_built(ledger, 1)`, because `_plan_heal_rows` returns `(built, proposed, superseded_blockers)` at cdf1ce4. The aa4ea04 64b-i pair no longer runs by default (parked).
- `baseline_probe.log` (adapted probe, TREE 571b6c56): `3 passed`.
- **BC-r5-1 (M1: `_txn.fragment_rows` doubles the un-annotated count)**: `bc1b.log` · `11 failed, 367 passed` · **PROOF HELD** · EXIT=0 · restored. What moved is identical to the first audit:
  - the accessor: `(8331, 8331) != (16665, 16664)`;
  - the heal row cost: `[8] != [4]`;
  - compose refuses `50002 rows, over the 50000-row cap`.

  All three consumers still price through the shared counter. (HIGH)
- **BC-r5-2 (M2: `_log_transaction_size` compares against `3 *` the WARN threshold)**: `bc2.log` · `4 failed, 373 passed` · **PROOF HELD** · EXIT=0 · restored. The broken old probe was deselected, which is fine because M2 does not touch it. (HIGH)

## §REGRESSION — the first audit's confirmed items, one line each
| item | verdict | receipt |
|---|---|---|
| F1 / #623 (the heal writes a cycle) | **FIXED** (HIGH) | The first audit's own verifier `ca58/verify1-notes/probe_verify1.py` re-run on the copy (`LOGS/f1_verify.log`, EXIT=0). Both variants: boots 1–3 leave `D ['X']` unchanged, and each boot logs `WARNING:task.backfill.straggler_would_close_cycle`. At aa4ea04 the result was `D ['H']`, `stragglers_reanchored`, then `legacy_cycle_minted`. No mislabel is emitted. The live-supersede control is still refused. Also M-A in §S1 reddens legs A/B/C/E1/D2. |
| F4 / #624 (markers spelled twice) | **FIXED** (HIGH) | §S2: 4 runs PROOF HELD plus 2 controls. |
| F6 docstrings | **all listed items now TRUE** (HIGH, read at cdf1ce4) | `supersede_task` Returns `SupersedeResult`, and Raises names `HubSupersedeRefusedError` and `SupersedeStragglerError`. `direct_dependents` no longer claims the render rides it or that `blocked_by` is immutable. The `claim_task` comment says `blocked_by` CAN change and names the CAS conjunct. `_refuse_a_cycle` Args names supersede's rewired dependents, and "records every such loop at EVERY boot" is true (leg D green; `_record_legacy_cycles(columns)` now runs before the early return). `_render_supersede_result` names the post-pre-write straggler exception. `updated_since` and the `_COL_UPDATED_AT` comment name the re-anchor and heal stamps. **But see D-1** (a NEW docstring falsified by this wave). |
| F7a `_still_claimable` | **GONE** (HIGH) | `git grep _still_claimable cdf1ce4` finds hits only in tracked REPORT-*.md. F7b (`_guarded_append_fragment`'s uuid default, `tasks.py` line ~2369) stays, as a residual that 70665b9 chose deliberately. |
| F8 served hub refusal | **FIXED** (HIGH, driven) | Through the `lore_tasks` dispatcher, with the hard cap at 20 (`LOGS/served.log`): *"… 6 dependents; re-anchoring them composes 23 rows, over the 20-row transaction cap (the build-time bound admits at most 5 dependents) — refused, nothing changed. A hub near that size can instead time out without being refused (finding #628)."* There is no "KNOWN BOUND", no "58 F-1" and no "file it with lore_findings", and the cap is the live value. |
| F8 trigger attribution | **OPEN** → D-3 | |
| probes F2 / #625 a (packer prose) | **FIXED** (HIGH, driven) | Boot with the WARN threshold at 2: *"straggler … alone composes 4 rows, over the 2-row heal chunk bound — the heal cannot pack it into one transaction"*, `row_cap=2` equal to the live `min()`. The words "transaction cap" are gone. |
| #622 (`max_reanchor_dependents` cites the wrong probe) | **FIXED** (HIGH, read) | It now cites `scripts/probe_heal_curve_58.py` part C, says "NOT `probe_hub_txn_58.py`", and carries all three rows (1 665/2.82 s, 3 332/10.15 s, 6 000/timeout 30.34 s). `C_SIZES = (1665, 3332, 6000)` is in the probe. |
| secret-seam scanner red | **GREEN** (HIGH) | `LOGS/secret.log`: `1 passed`, EXIT=0. `probe_hub_txn_58.py`'s knobs became argparse (25cfd16; the env-read comment at its line ~38). |
| F5 claim text | **FIXED** (HIGH, driven) | Dispatcher claim of a legacy strand: *"… — a SUPERSEDED blocker can never resolve: block on the successor instead)"*. "can never win" is absent. |
| #130(a) served schema | **FIXED on the served surface** (HIGH, driven); **ledger docstring not done** → D-2 | Served `lore_tasks.status`: *"For 'query', an optional exact-status filter; a status (or blocked) filter excludes SUPERSEDED tasks."* |

## §FINDINGS
### D-1 (minor, HIGH, measured): the fix wave left `find_blocked_by_cycle`'s docstring and the batch-key comment claiming ONE shared detector, which M-B measures false
- `tasks.py::find_blocked_by_cycle` docstring at cdf1ce4: *"The ONE `blocked_by` cycle detector (operator ruling R6). Ledger-owned and shared: BOTH the write-time guard over PERSISTED ids and `server.py`'s batch-local temp-KEY check route through it … neutralise this and BOTH shapes must stop being refused."*
- `server.py`, the comment above the create_many batch-key check: *"⚠ ONE cycle detector and ONE refusal SHAPE, both ledger-owned (operator ruling R6)"*.
- am-17 §13.3 amended R6: one detector per question. The persisted question is now `find_row_blocked_by_cycles`, and `find_blocked_by_cycle` has one production caller (server.py's batch-key check). **`LOGS/mB.log` is the measurement: neutralising it stops only the 2 batch-key refusals; all 22 persisted-shape pins still refuse.**
- This is the F6 class (prose the diff made false), reintroduced by cdf1ce4. It is not served (docstring and comment), but it is the text the next engineer reads before "aligning" the two detectors. Fix: two prose edits that name §13.3's split.

### D-2 (minor, HIGH, read): am-17 §12.7's #130(a) clause is half done
- The ruling: *"the `lore_tasks` `status` Field (`server.py`, … two sites) **and the `query_tasks` docstring** name that superseded rows are excluded from a status or blocked filter."*
- Both server sites now say so: the Field (served, driven above) and the `tasks` handler's Args at server.py ~4646.
- `TaskLedger.query_tasks`'s docstring at cdf1ce4 (lines 1347–1414) still says *"exact `status` / `owner` equality filters"* and never mentions superseded rows. Its Args say `status: restrict to tasks in this exact status`. The commit message (cdf1ce4: "#130(a) status exclusion named") over-claims.
- This is the rider pattern from CLAUDE.md "THE RIDER IS PART OF THE RULING". Fix: one docstring sentence.

### D-3 (minor, HIGH, driven): F8 part 1 is still open. #628's re-open trigger cannot be attributed, and the docstring does not name #628
- I drove a task-ledger supersede with `TXN_ROW_WARN_THRESHOLD=3` (`LOGS/served.log`, `PROBE large_transaction_records`). The record served was `('loremaster.store.surreal', 'WARNING', {'statement_count': 8, 'param_count': 12, 'row_count': 8})`. It carries no database, caller or table, and the index writer emits the same event from the same function.
- So #628's RE-OPEN TRIGGER, *"a store.apply.large_transaction record from the task ledger"*, and `max_reanchor_dependents`' "Trigger: a `store.apply.large_transaction` record from the task ledger" still name a condition no reader can test.
- #625's body names this ("the re-open trigger … carries no source, so a trigger firing cannot be attributed"), and its closing scope line lists only "served prose plus a finding for the timeout band". So whether the attribution was in the wave's scope is the decision in (a). Neither surface surfaced it as dropped.
- Secondary: the `max_reanchor_dependents` KNOWN BOUND docstring cites am-17 §4 but not #628. CLAUDE.md ("WHEN YOU CANNOT CLOSE A HOLE, RECORD IT") wants the docstring to name the finding and its re-open trigger. The served refusal does cite #628.
- Fix: pass `database` (or a caller tag) into `_log_transaction_size`'s extras from `TaskLedger._apply`, and add "(#628)" to the docstring.

## §RESIDUALS (each NO ROUND unless the lead rules otherwise)
- **R-1 (test coupling, HIGH):** `test_a_BATCH_KEY_cycle_at_the_TOOL_SEAM_raises_the_LEDGERS_cycle_CLASS` and the FORMATTER pin both reddened under M-A. They derive the expected class (resp. sentence) from a LEDGER self-loop refusal (`_ledger_cycle_error`), so the batch-key class pin depends on the persisted predicate as well. M-A still holds, because I declared both. §13.3's "the batch-key pin reddens and the four persisted pins do not" is about M-B only, and it holds there.
- **R-2 (oracle, MEDIUM):** fixwave legs A and B check "no cycle" with `find_blocked_by_cycle(all_columns) is None`. Under M-B that is vacuously true. Their column-unchanged assertions still guard them, and E1/D2 use the reachability oracle §13.5 asked for.
- **R-3 (hard-coded markers, HIGH):** `test_reanchor_58_r3_am6.py::RULED_TIERS` spells the 4 marker literals, so a legitimate respelling reddens it for a spelling reason. This is the PR14 shape. It served here as landing evidence.
- **R-4 (coverage, MEDIUM):** the 4th CAS_LOST producer, `_REANCHOR_LOST_MESSAGE` (a dependent stopped naming the superseded task mid-supersede), has no REAL trigger in `r3_tiers`. It is proven shared by reading only: it is built as `f"{_txn_module.CAS_LOST_MARKER} …"`.
- **R-5 (stale test prose, HIGH):** `test_blocks_edge.py::TestSupersedeCarriesBlockedBy174::test_supersede_source_calls_BOTH_shared_blocks_edge_prechecks` says *"`_refuse_a_cycle` can NEVER fire for supersede behaviourally"*. E3 and the r2 CONTROLs show that it does. Test hygiene.
- **R-6 (instrument rot, HIGH):** the first audit's BC-r5-1 probe broke on `_plan_heal_rows`' new return shape (Deviation 2). A pasted instrument that indexes a private return value rots silently: it went RED for an IndexError, not for pricing.

## §INSTRUMENTS (scratch root `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58d/`)
- The mutation anchors and replacements are files in `LOGS/mut/` (`mA`, `mB`, `mk_{claim,cas,straggler,heal}`, `c_{claim,cas}`). BC-r5 used the first audit's `ca58/m1.*` and `ca58/m2.*`.
- `run_mut.sh` is the first audit's runner (pasted in coldaudit-58-ca58-sharing.md §INSTRUMENTS) with three changes: paths point at `ca58d`, the baseline-deselect line is dropped, and the restore check is appended to the log. `run_mut2.sh` adds an optional 7th argument: a file of node ids passed as `--deselect`.
- `test_probe_sharing_ca58d.py` (md5 `6c28ed5f8819…`) is the first audit's pasted probe (md5 `289ad2060d9b…`) with exactly this diff:
```
34c34,35
<     return ledger._plan_heal_rows(rows, {"o0": "n0"}, {"o0": ("n0", False)}, {"n0"}, _AT)  # noqa: SLF001
---
>     built, _proposed, _olds = ledger._plan_heal_rows(rows, {"o0": "n0"}, {"o0": ("n0", False)}, {"n0"}, _AT)  # noqa: SLF001
>     return built  # cdf1ce4: _plan_heal_rows returns (built, proposed, superseded_blockers)
```
  The docstring's first line also changes, to name it a delta copy.
- `test_probe_served_ca58d.py`, the served-text driver, verbatim:
```python
"""ca58d-sharing delta-audit probe (packet 58 fix wave, graded cdf1ce4): DRIVE each refusal the first cold audit
flagged and PRINT the served text, so the auditor reads what a consumer reads, not the source.

Run (scratch copy root, TEST store ws://127.0.0.1:18000 via the harness):
    uv run pytest loremaster/tests/test_probe_served_ca58d.py -q -s -p no:cacheprovider
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from _reanchor_58_support import create, ledger58, new_ledger, raw_relate, raw_seed_row
from _surreal_harness import SurrealEnv
from loremaster.store import _txn
from loremaster.tasks import HubSupersedeRefusedError, StragglerHealPackerError, TaskLedger
from test_query_tasks_bounded import _tool_seam

__all__ = ["ledger58"]


def _pad(tag: str) -> str:
    return tag.ljust(32, "0")


async def test_probe_hub_refusal_served_text(ledger58, monkeypatch) -> None:
    ledger, _env = ledger58
    monkeypatch.setattr(_txn, "TXN_ROW_HARD_CAP", 20, raising=True)
    hub = await create(ledger, "hub")
    for index in range(6):
        await create(ledger, f"dependent {index}", [hub])
    with pytest.raises(HubSupersedeRefusedError) as caught:
        await _tool_seam(ledger).tasks(
            action="supersede", task_id=hub, subject="reframed", description="d", created_by="probe"
        )
    served = str(caught.value)
    print(f"\nPROBE hub_refusal: {served}")
    assert "KNOWN BOUND" not in served and "58 F-1" not in served and "file it with lore_findings" not in served
    assert "#628" in served and "20-row transaction cap" in served


async def test_probe_large_transaction_record_attribution(ledger58, monkeypatch, caplog) -> None:
    ledger, _env = ledger58
    monkeypatch.setattr(_txn, "TXN_ROW_WARN_THRESHOLD", 3, raising=True)
    hub = await create(ledger, "hub")
    await create(ledger, "dependent", [hub])
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        await ledger.supersede_task(hub, subject="reframed", description="d", created_by="probe")
    records = [r for r in caplog.records if r.getMessage() == "store.apply.large_transaction"]
    standard = set(vars(logging.makeLogRecord({})))
    shown = [(r.name, r.levelname, {k: v for k, v in vars(r).items() if k not in standard}) for r in records]
    print(f"\nPROBE large_transaction_records: {shown}")
    assert records, "the WARN record never fired: the probe saw nothing"


async def test_probe_packer_error_served_text(ledger58, monkeypatch) -> None:
    ledger, env = ledger58
    head = await create(ledger, "head")
    legacy, straggler = _pad("ca58dleg"), _pad("ca58drow")
    await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
    await raw_seed_row(ledger, straggler, blocked_by=[legacy])
    await raw_relate(ledger, legacy, straggler)
    monkeypatch.setattr(_txn, "TXN_ROW_WARN_THRESHOLD", 2, raising=True)
    booted = new_ledger(env)
    try:
        with pytest.raises(StragglerHealPackerError) as caught:
            await booted.ensure_ready()
    finally:
        await booted.close()
    served = str(caught.value)
    print(f"\nPROBE packer_error: {served} | row_cap={caught.value.row_cap} live_min="
          f"{min(_txn.TXN_ROW_WARN_THRESHOLD, _txn.TXN_ROW_HARD_CAP)}")
    assert "transaction cap" not in served and "2-row heal chunk bound" in served
    assert caught.value.row_cap == min(_txn.TXN_ROW_WARN_THRESHOLD, _txn.TXN_ROW_HARD_CAP)


async def test_probe_F5_claim_served_text(ledger58) -> None:
    ledger, _env = ledger58
    successor = await create(ledger, "where the work went")
    blocker, dependent = _pad("ca58df5b"), _pad("ca58df5d")
    await raw_seed_row(ledger, blocker, blocked_by=[], superseded_by=successor)
    await raw_seed_row(ledger, dependent, blocked_by=[blocker])
    await raw_relate(ledger, blocker, dependent)
    served = str(await _tool_seam(ledger).claim_task(dependent, "probe"))
    print(f"\nPROBE F5_claim: {served}")
    assert "can never win" not in served and "can never resolve: block on the successor instead" in served


async def test_probe_130a_served_schema(tmp_path: Path) -> None:
    from loremaster.server import LoreServer, build_mcp_server
    from test_mcp_server import _config, _slug

    mcp = build_mcp_server(LoreServer(_config(_slug(), tmp_path / "live")))
    tools = {tool.name: tool for tool in await mcp.list_tools()}
    props = tools["lore_tasks"].parameters["properties"]
    for field in ("status", "blocked"):
        print(f"\nPROBE 130a_{field}: {props[field].get('description', '')}")
    assert "superseded" in str(props["status"].get("description", "")).lower()
```
  (Type annotations on the fixture parameters are elided here. The run file `LOGS/test_probe_served_ca58d.py` has them; the bodies are identical.) Bound: the probe reads `str(exception)` at the dispatcher. FastMCP's own error wrapping on the wire is not observed.
- `fn_hits.py` (`LOGS/fn_hits.py`, the AST lister that found candidate tests): it lists `Class::function` for every function in the given files whose source span matches a regex. It was used only to build the reading list. The declared sets came from reading each test.
