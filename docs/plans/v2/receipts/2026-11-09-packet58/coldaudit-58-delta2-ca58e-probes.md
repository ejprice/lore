brief-base v27 read · brief project v7 read

# coldaudit-58-delta2-ca58e-probes: packet 58 second delta audit, guard-input probes and own wrong builds

## SUMMARY BLOCK
- **Verdict (this dimension): GO on the guard's input and the lock, with two minor test gaps and one unmet claim.** Every probe the brief named HOLDS on 8679385, with no cycle written and every boot completing:
  - #634: one ledger, 20/20, exactly one supersede refused, no cycle.
  - #635: depth k=3/33/34/40/100 on both legs, every case refused or skipped.
  - #636: 300 / 1 000 / 3 000 stragglers, every boot completes; the 3 000-straggler boot takes 8.7–11.4 s, and the guard read takes ≤ 0.045 s at 6 032 dependency-bearing rows.
  - §14.4 item 4 (creates racing): 0 cycles in 70 attempts for each of create∥supersede, create∥create, create_many∥supersede and two-ledger create∥supersede; the no-lock positive control wrote 15 and 20 cycles.
  - Regressions all hold: fw1 E1–E4, ca58d S1–S4 and the depth door, r53 P1–P3, and the predicate probe (rule U 0/0, NONE non-zero, on two seeds).
- **Wrong builds:**
  - WB2 dies by the contract (#638 half ii closed). **WB5 still SURVIVES the contract** (F1, #638 annotated): the ruled in-process permutation pin cannot see hash-order dependence, and its worlds agree across 8 hash seeds even on WB5.
  - Of my 6 own builds: 3 lock builds and the stale-cache input build are killed. **A partial input (`LIMIT 1000`) survives all 525 tests** (F2, #642); only my scale probe kills it. The heal-reads-before-backfill build is an argued equivalent mutant, not run.
- F3 (#643): the re-run instrument the code cites, `scripts/probe_guard_input_58.py`, is absent at 8679385, and its only copy calls the deleted function. F4: two stale "closure read" docstrings (no finding filed).
- Recorded bound reproduced as documented: two ledgers still write the #634 cycle 20/20 (finding #634; the served shape is one server).
- State: done-with-deviations. (1) Test runs are inline: this workflow subagent has no `Agent` tool, so no haiku-runner. (2) I used two scratch copies, one for mutation proofs and one for live probes, so no probe ran on a mutated tree. (3) The proof selection is all 15 `test_reanchor_58_*` files plus the brief-era three (525 tests), wider than the four contract files.
- `Packages considered: none — no mechanism specified` (audit; networkx and asyncio.Lock use read, not re-specified). `Odoo-20 portability: n/a — no Odoo seam touched`. `Reuse ledger: none` (no production symbol written).
- `Graded: 8679385 · HEAD-at-report: 8679385 · SAME`
- Decisions needed: (a) whether #638(i) needs a cross-process pin over multi-candidate worlds (ca58d's `test_ca58d_determinism.py` is a ready one); (b) whether the contract gains a scale world with a late-sorting cycle (`test_ca58e_scale.py`) for #642; (c) committing or re-pointing the probe script (#643).
- Pointers: §(a) · §(b) · §(c) · §(d) · §(e) · §Findings · §RUNS · §INSTRUMENTS. Findings filed: #642, #643; #638 annotated.

## CAPABILITY CHECK
- Demanded: scratch copy, cgroup cap, mutation_proof.py, TEST store :18000, lore. Met.
- Demanded (brief-base §3): test runs to a haiku-runner. This workflow subagent has NO `Agent` tool, so every run is inline through a guarded runner (refuses an empty / non-file selection, #620). Lead change: give workflow auditors the Agent tool, or brief `test runs: inline`.
- lore: loaded; landmine recall returned 10 (< 50, not cut off); registered `ca58e-probes` in `pkt58-20261109`. Grep used only in the (unindexed) scratch copy and for textual seams (a cited script path).

## ROUTING TABLE (written 2026-11-10 before the first run)
| step | tier | who | reason |
|---|---|---|---|
| read am-17 §14/§14.7, delta diff, prior instruments | 3 | me | the probes' expectations are judgment over the ruling |
| scratch copy + checkout 8679385 + provenance | 1 | me inline | one command, critical path |
| test / probe runs (a)–(e) | 1 | me inline | no `Agent` tool (capability, not choice); each log has a tree_id header and EXIT line |
| wrong-build design, mutation verdicts | 3 | me | adversarial judgment, never Haiku |

Fan-out: haiku 0 · sonnet 0 · peak 0 — no Agent tool available.

## Provenance (measured 2026-11-10)
- Copy 1 (mutation proofs): `scratchpad/ca58e/ca58e-probes` via `scripts/scratch_copy.sh` (EXIT=0), then `git checkout 8679385 -- .`. HEAD = `86793850c0563a52c9d4f74961ef522d444a2386`; tracked diff vs 8679385 = 0; `loremaster.__file__` = `…/scratchpad/ca58e/ca58e-probes/loremaster/loremaster/__init__.py`; `tasks.py` md5 `be7f4c1f38591616161f943a2fd41633`, restored byte-exact after every proof (mutation_proof.py's own line plus an md5 after each).
- Copy 2 (live probes, so no probe ever ran against a mutated tree): `scratchpad/ca58e/ca58e-probes2`, same recipe, HEAD 8679385, tracked diff 0, `loremaster.__file__` = `…/ca58e-probes2/loremaster/loremaster/__init__.py`. `TREE=dc352a08…` (untracked: the live tree's REPORTs and two delta-2 receipts files; production identical).
- Logs: `scratchpad/ca58e/ca58e-probes-tools/logs/` (each opens with `tree_id.sh` + `CMD`, ends with `EXIT=`).

## (a) The first delta audit's probes on 8679385
### #635 depth door (ca58d-blind `probe_depth_bound_cycle.py`, k widened to 3/33/34/40/100) — `logs/a_depth.log`, EXIT=0: HOLDS
| leg | k=3 (control) | k=33 | k=34 | k=40 | k=100 |
|---|---|---|---|---|---|
| S (live supersede, public verbs only) | REFUSED, no cycle | REFUSED | REFUSED | REFUSED | REFUSED |
| H (boot heal, straggler planted) | SKIPPED, 1 record | SKIPPED, 1 | SKIPPED, 1 | SKIPPED, 1 | SKIPPED, 1 |
Whole-table cycle after every run: none. At cdf1ce4 the same probe wrote a 43-member loop at k=40 on both legs.
Also ca58d-probes `TestDepthDoor` (own_probes + depth_edge, the n=31..34 edge): `logs/c_own_S_depth.log` **22 passed, EXIT=0** (at cdf1ce4: 3 failed).

## (c) Regression probes: HOLD
- adversary-58-fw1 E1–E4, verbatim (md5 e6b4d7a9…): `logs/c_fw1_E1E4.log` **6 passed, EXIT=0**.
- ca58d S1–S4 strengthened + depth: `logs/c_own_S_depth.log` 22 passed (above). r53 P1–P3: `logs/c_r53.log` **3 passed, EXIT=0**.
- `probe_cycle_predicate_58.py` with `rule_u` = the built `find_row_blocked_by_cycles(stored, proposed, set(proposed), all_or_nothing=False)` (ca58d's `probe_cycle_predicate_58_built.py`, diff vs the committed script pasted in coldaudit-58-delta-ca58d-probes.md §INSTRUMENTS):
| run | log | heal worlds | rule U all / partial | NONE all / partial | supersede built (AON) differs |
|---|---|---|---|---|---|
| `--built 4000 58` | `c_pred_built_58.log` | 2911 | **0 / 0** | 2271 / 1858 | **0** of 4000 |
| `--built 6000 20261110` | `c_pred_built_seed2.log` | 4338 | **0 / 0** | 3336 / 2720 | **0** of 6000 |
- In-process order independence (`determinism_probe.py 3000 7`): `c_determinism.log` 17 680 hits, **0 order-dependent**.
- Identical numbers to the cdf1ce4 run: the §14 delta did not touch the predicate (confirmed by the diff: only `find_blocked_by_cycle`'s return direction changed, the graphlib batch-key detector).

### #634 concurrent supersedes (ca58d-blind `probe_concurrent_supersede_cycle.py`, plus a one-ledger barrier leg) — `logs/a_concurrent.log`, EXIT=0
| leg (20 attempts each, fixture T1,T2; D1[T1]; X[T2]; A=supersede(T1,[X]) ∥ B=supersede(T2,[D1])) | fates | whole-table cycle | at cdf1ce4 |
|---|---|---|---|
| CONTROL sequential | ok, cycle-refused | no | same |
| ONE ledger, `asyncio.gather` (the served shape) | **ok, cycle-refused 20/20** | **no, 20/20** | ok,ok + cycle 20/20 |
| two ledgers (two connections, one DB) | ok, ok 20/20 | YES 20/20 | same |
| two ledgers, barrier after the guard | ok, ok 20/20 | YES 20/20 | same |
| ONE ledger, barrier after the guard (added) | TimeoutError, TimeoutError 20/20 | no | — |
- The two-ledger rows are the recorded bound #634 (two processes; am-17 §14.7 item 1), reproduced as documented: the lock is in-process only. The served shape is one server per project, so this is not reachable there. Named re-open trigger: two task-writing processes on one database (packet 39).
- The added one-ledger barrier leg is a positive control for the lock: the first supersede waits at the barrier INSIDE the lock, so the second can never reach the barrier. Both time out (10 s `wait_for`), and nothing is written. That proves the lock spans the guard read, not just the write.

### #636 scale (own `test_ca58e_scale.py`, the delta audit's world plus a late-sorting cycle control) — `logs/a_scale.log`, `logs/a_scale_r2.log`, both **4 passed, EXIT=0**, `-n 1`, quiet store
| stragglers | chain depth | task rows | guard read (s, rows) run 1 / run 2 | boot (s) run 1 / run 2 | D* (cycle control) | at cdf1ce4 |
|---|---|---|---|---|---|---|
| 300 | 30 | 934 | 0.0074 / 0.0062 (632 rows) | 0.52 / 0.44 | skipped, 1 record | boot raised (TIMEOUT 5s) |
| 1 000 | 30 | 3 034 | 0.0167 / 0.0161 (2 032) | 2.58 / 2.23 | skipped, 1 record | boot raised |
| 3 000 | 0 | 9 005 | 0.0233 / 0.0218 (3 003) | **11.37 / 9.82** | skipped, 1 record | boot raised |
| 3 000 | 30 | 9 034 | 0.0339 / 0.0442 (6 032) | **8.81 / 8.74** | skipped, 1 record | boot raised |
- Every boot completes, every D_j heals onto its own head, the cycle-closing D* (ids sorting LAST, so a prefix read would miss it) is untouched and recorded exactly once, no cycle over all columns. One guard read per boot, ≤ 0.045 s at 6 032 dependency-bearing rows; the 3 000-straggler boot (~9–11 s) is dominated by the heal's chunk writes (cdf1ce4's no-read control measured 9.27 s for the same world), far inside the 300 s boot request timeout.
- Bound: one host, a quiet TEST store, one world shape (distinct heads over one shared chain). Production size not measured (:18500 not touched).

## (b) am-17 §14.4 item 4 — creates need no lock (a RUN): HOLDS, zero cycles
Instrument `probe_race_writers_58.py` (pasted below): per attempt a fresh DB, a random 7-row acyclic world built through `create_task` (odd attempts) or the #634 hand shape (even attempts), two verbs started together with `asyncio.gather`, then the boot heal `_reanchor_stragglers`; a whole-table graphlib cycle check after the pair AND after the heal (independent of the predicate under test).
| mode | seed 58, 30 attempts (`logs/b_race.log`) | seed 20261110, 40 attempts (`logs/b_race_seed2.log`) |
|---|---|---|
| CS create ∥ supersede, one ledger | both ok 28, **cycles 0** | both ok 33, **cycles 0** |
| CC create ∥ create, one ledger | both ok 30, **cycles 0** | both ok 40, **cycles 0** |
| MS create_many(2, M2 names sibling M1) ∥ supersede | both ok 22, **cycles 0** | both ok 26, **cycles 0** |
| CS2 create ∥ supersede on TWO ledgers (no lock can help) | both ok 24, **cycles 0** | both ok 28, **cycles 0** |
| SS supersede ∥ supersede, shipped lock | both ok 4, **cycles 0** | both ok 8, **cycles 0** |
| SSX POSITIVE CONTROL: SS with the lock replaced by `contextlib.nullcontext()` | **cycles 15** | **cycles 20** |
- 70 attempts per create mode, 0 cycles; non-vacuous (most pairs both commit; refusals tallied by class in the logs: TaskCycleError, SupersedeStragglerError, UnknownBlockerError). The positive control proves the instrument sees a race-written cycle. The heal never wrote one either (cycle check after it).
- This supports am-17 §14.3's "only supersede": a created row is minted with a fresh uuid4 (create_task; the dispatcher's `_create_many` mints `uuid4().hex` too), so no persisted row names it at commit. Bound, stated: the ledger-level `create_many(ids=…)` accepts caller ids; a caller id equal to a phantom blocker some legacy row already names WOULD give the new row an in-edge at commit. The served dispatcher never does this (it mints), so not reachable in the served shape; not driven here. Confidence HIGH on the measurement, MEDIUM on the ids bound (read, not run).

## (d) #638: WB2 now dies by the contract; **WB5 still SURVIVES it** (finding #638 annotated, kept open)
Selection for every proof: all 15 `test_reanchor_58_*.py` + `test_blocks_edge.py` + `test_cycle_write_path_04b3.py` + `test_supersede_reanchor_58.py` = **525 tests** without `--run-parked` (packet-58-fixwave is `active: true`, so its ids run). Baseline on 8679385 with `--run-parked`: 525 passed + 2 red, both `findings.py::_run_guarded` rows owned by `packet-64b-i-contract` (`logs/baseline.log`); without it the two files hold 39 passed and 2 parked-deselected (`logs/baseline_cas_noparked.log`). Declared reds from `--collect-only`, written before each run (`decl/WRITTEN_AT`: 09:11:58Z, 09:17:05Z, 09:24:05Z).
| build | delta (tasks.py, anchor matched once) | declared | observed | verdict | log |
|---|---|---|---|---|---|
| WB2 | predicate per CHUNK, after `_pack_heal_chunks` (ca58d's delta, unchanged anchor) | `test_638_ii` | `test_638_ii` (1 failed / 524 passed) | **KILLED, exact**. #638 half (ii) closed. | `d_WB2.log` |
| WB5 | every `sorted()` in `find_row_blocked_by_cycles` removed (ca58d's delta) | 4 × `test_638_i[…]` | **none — 525 passed** | **SURVIVES the contract.** #638 half (i) NOT closed | `d_WB5.log` |
| WB5 vs cross-process probes | same delta; selection `test_ca58d_determinism.py` + own `test_ca58e_wb5_worlds.py` | the determinism test | the determinism test (1 failed / 1 passed) | killed by ca58d's probe only: 4 hash seeds → 4 digests. The correct build passes both (`d_WB5b_correct.log`, 2 passed) | `d_WB5b.log` |
- **Why the ruled pin cannot fail (HIGH on the measurement, MEDIUM on the mechanism):** `test_638_i` permutes the insertion order of `stored` / `proposed` inside ONE process. WB5's order dependence is `set()` iteration over strings, which the per-process hash seed fixes. Inside one process every permutation gives the same answer, so the in-process pin is structurally blind. The second reason is measured: `test_ca58e_wb5_worlds.py` evaluates the pin's own four `WRITER_WORLDS` in 8 interpreters with different `PYTHONHASHSEED` values ON WB5, and they agree. Each world appears to hold one candidate loop, so even a cross-process pin over those worlds would pass. Two things are needed: worlds with several equal candidate cycles or several in-component blockers, and a run across processes (ca58d's 3 000 random worlds do both).
- So am-17 §14.7 item 2(i)'s instrument ("in memory, at least 3 permutations") does not test the property it was ruled for. The test docstring's "Kills WB5 (the `sorted()` calls removed)" is false.
- Served impact: the build itself is deterministic (the sorts are present, and ca58d's 3 000-world cross-process probe is green on 8679385). This is a test gap, `product_defect: false`.

## (e) Own wrong builds against the guard INPUT and the lock (mutation_proof.py, same 525-test selection)
| build | what it breaks | declared | observed | verdict | log |
|---|---|---|---|---|---|
| WB-L1 | lock held around the guard read only, RELEASED before the transaction commits | `test_634` | `test_634` (1 failed / 524) | KILLED, exact | `d_WBL1.log` |
| WB-L2 | a fresh `asyncio.Lock()` per call (serialises nothing) | `test_634` | `test_634` | KILLED, exact | `d_WBL2.log` |
| WB-L3 | lock held around the WRITE only, guard read outside it | `test_634` | `test_634` | KILLED, exact | `d_WBL3.log` |
| WB-I9 | STALE input: the first `_read_dependency_graph` result is cached on the ledger and reused | `test_635_S` ×2 | 7 reds (the 2 declared + `test_634`, 2 in `test_blocks_edge`, 2 in `test_supersede_reanchor_58`) | KILLED (under-predicted by 5; 0 declared-but-green) | `d_WBI9.log` |
| **WB-I1** | **PARTIAL input: the guard read gets `LIMIT 1000`** (the boot mirror read untouched) | `test_636` (a placeholder: mutation_proof needs ≥ 1 declared id; I predicted survival before the run, in my working notes, not in the file) | **none, 525 passed** | **SURVIVES the contract** → finding **#642** | `d_WBI1.log` |
| WB-I1 vs own scale probe | same delta; selection `test_ca58e_scale.py` | `[1000-30]`, `[3000-0]`, `[3000-30]` | exactly those 3 (`[300-30]`, 632 rows < 1 000, stays green) | KILLED, exact: the late-sorting cycle control is outside the prefix | `d_WBI1scale.log` |
| WB-H (argued, NOT run) | the heal's graph read BEFORE the backfill | — | — | **equivalent mutant**, by reading: `_backfill_blocks_edges` writes only `blocks` edges (`_relate_fragment`), and `_record_legacy_cycles` only logs. Neither writes a `blocked_by` column, so a read before the backfill returns identical input. MEDIUM-HIGH (not executed: it needs two non-adjacent edits, and mutation_proof takes one anchor) | — |
- Every proof restored `tasks.py` byte-exact (md5 `be7f4c1f…` after each, `logs/proofs_all.txt`, `logs/proofs_2.txt`). WB5 and WB2 first failed with `FileNotFoundError` on the anchor file (copy omitted). No tests ran in those two attempts, and both were re-run cleanly (`proofs_2.txt`).
- WB-I1 is plausible (an honest re-bound of an unbounded read, the shape of the read §14 deleted). It is a TEST gap, not a product defect: at 8679385 the read has no LIMIT.

## Findings and residuals (this dimension)
- **F1 (minor, test gap, #638 annotated): WB5 survives the contract.** See §(d). Not closed by `test_638_i`, whose in-process permutation cannot see hash-order dependence.
- **F2 (minor, test gap, #642): a partial guard input (`LIMIT 1000`) survives the contract.** See §(e). Kill instrument: `test_ca58e_scale.py`.
- **F3 (minor, unmet claim, #643): the cited re-run instrument `scripts/probe_guard_input_58.py` does not exist at 8679385.** `git ls-tree -r 8679385` has no such file, and no commit has ever added it. Cited by the comment above `TASK_GUARD_GRAPH_LARGE_ROWS` and by `_read_dependency_graph`'s docstring. The only copy (am-17 §INSTRUMENT-4) calls the deleted `_bounded_dependency_graph`, so it raises `AttributeError` at 8679385, and it imports the test support through an absolute live-tree path. Not served text: the WARNING record carries only `database`/`rows`/`threshold`.
- **F4 (minor, false docstrings, no finding filed — for the lead):** two prose sites still describe the deleted closure read (a non-symbol textual seam, so grep is the right tool here, in the unindexed scratch copy):
  - `find_row_blocked_by_cycles` Args: `stored: … — the bounded ancestor closure of the proposed blockers.`
  - `_skip_cycle_closing_rows` docstring: `ONE closure read seeded by every proposed blocker and ONE predicate call`.
  - am-17 §14.2 ordered the closure docstring deleted. These two survived the §14.4 item 6 sweep (which counted test and script hits, not these). Neither is served.
- **Recorded bound reproduced, not a finding:** two ledgers on one database still write the #634 joint cycle 20/20 (§(a)). This is the documented two-process bound (`supersede_task` docstring, finding #634 open).
- **NOT TRIED:** WB-H as a live run (argued equivalent, §(e)); a guard input filtered by status (excluding done or superseded rows). The second was not tried because whether a cycle through a done row harms anyone is a ruling question, not a wrong build. Also not tried: `build_app_context` ordering (heal finishes before the first verb), which §14.3 relies on for "why not the heal"; it is not driven here.

## §RUNS (all 2026-11-10, TEST store :18000, `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0`, pytest `-n ≤ 8 --timeout=300`)
| # | what | copy | log (`scratchpad/ca58e/ca58e-probes-tools/logs/`) | count / result | EXIT |
|---|---|---|---|---|---|
| 1 | baseline, 527 with `--run-parked` | 1 | `baseline.log` | 2 failed (64b-owned), 525 passed | 1 |
| 2 | the 2 cas/state files without parked | 1 | `baseline_cas_noparked.log` | 39 passed, 2 deselected | 0 |
| 3 | depth door S/H k=3..100 | 2 | `a_depth.log` | all refused / skipped, controls_ok=True | 0 |
| 4 | #634 concurrency, 5 legs × 20 | 2 | `a_concurrent.log` | §(a) | 0 |
| 5–6 | scale ×2 | 2 | `a_scale.log`, `a_scale_r2.log` | 4 passed each | 0 |
| 7–8 | race fuzzer, 2 seeds | 2 | `b_race.log`, `b_race_seed2.log` | §(b) | 0 |
| 9 | fw1 E1–E4 | 2 | `c_fw1_E1E4.log` | 6 passed | 0 |
| 10 | ca58d S1–S4 + depth door | 2 | `c_own_S_depth.log` | 22 passed | 0 |
| 11 | r53 P1–P3 | 2 | `c_r53.log` | 3 passed | 0 |
| 12–14 | predicate probe ×2, determinism | 2 | `c_pred_built_58.log`, `c_pred_built_seed2.log`, `c_determinism.log` | §(c) | 0 |
| 15–22 | proofs WB2, WB5, WBL1–3, WBI1, WBI9, WBI1scale | 1 | `d_<WB>.log` | §(d), §(e) | 0 held / 4 failed-as-shown |
| 23–24 | WB5 cross-process: correct, mutant | 1 | `d_WB5b_correct.log`, `d_WB5b.log` | 2 passed; 1 failed / 1 passed | 0 / 0 |

## §INSTRUMENTS (pasted verbatim by the auditor's shell from `scratchpad/ca58e/ca58e-probes-tools/`)
Reused unchanged: ca58d-blind `probe_depth_bound_cycle.py` / `probe_concurrent_supersede_cycle.py` (fences in coldaudit-58-delta-ca58d-blind.md) with these edits only: `for k in (3, 40)` → `for k in (3, 33, 34, 40, 100)`; `created_by` renamed; one added leg `("CONCURRENT barrier-forced ONE ledger (…)", True, True)`. ca58d-probes `test_ca58d_own_probes.py`, `test_ca58d_depth_edge.py`, `test_ca58d_determinism.py`, `probe_cycle_predicate_58_built.py`, `determinism_probe.py`, the fw1/r53 files, and the WB2/WB5 anchor/repl pairs (fences in coldaudit-58-delta-ca58d-probes.md §INSTRUMENTS; WB2/WB5 files md5-identical to ca58d's).

### `probes/probe_race_writers_58.py`
```python
"""ca58e-probes (packet 58 delta-2 audit, 2026-11-10; am-17 §14.4 item 4, a cold-audit RUN): can a blocked_by cycle be
closed by a CREATE racing a SUPERSEDE, or by two CREATES, on ONE ledger (the served shape) at 8679385?

Per attempt: a fresh test_<pid>_<uuid> database on ws://127.0.0.1:18000; a random acyclic world of ROWS tasks built
through create_task (row i blocked by up to 2 earlier rows); then TWO verbs started together with asyncio.gather;
then the boot heal (_reanchor_stragglers) runs; a whole-table cycle check (graphlib, independent of the predicate
under test) after the pair AND after the heal. Verb args are random over the world's rows, so a create may name the
supersede's target (becoming a straggler) or any of its dependents, and a supersede may name any row.
Modes:
  CS  create_task || supersede_task            (one ledger)        expect 0 cycles
  CC  create_task || create_task               (one ledger)        expect 0 cycles
  MS  create_many(2, sibling ref) || supersede (one ledger)        expect 0 cycles
  CS2 create || supersede on TWO ledgers (two connections, one database)   expect 0 (creates need no lock at all)
  SS  supersede || supersede                   (one ledger, the shipped lock)   expect 0 cycles
  SSX POSITIVE CONTROL: SS with the lock replaced by a no-op   expect > 0 cycles (the fuzzer can see a race cycle)
Each mode's half of the attempts use the #634 hand shape (T1,T2; D1[T1]; X[T2]) mapped onto the verb pair."""
import asyncio
import contextlib
import os
import random
import sys
import uuid

import loremaster
from loremaster.tasks import TaskLedger, find_blocked_by_cycle

sys.path.insert(0, os.path.join(os.path.dirname(loremaster.__file__), "..", "..", "scripts"))
from probe_query_complexity_07 import NAMESPACE, PASSWORD, URL, USER  # noqa: E402

assert ":18500" not in URL, URL
print("loremaster.__file__ =", loremaster.__file__, "| store =", URL, flush=True)
ATTEMPTS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 58
ROWS = 7
WHO = "ca58e-probes"


class Spec:
    def __init__(self, subject, blocked_by):
        self.subject, self.description, self.blocked_by = subject, "p", blocked_by


def mk(db):
    return TaskLedger(url=URL, namespace=NAMESPACE, database=db, user=USER, password=PASSWORD)


async def cycle_of(ledger):
    rows = ledger._as_rows(await ledger._query("SELECT record::id(id) AS id, blocked_by FROM task"))
    return find_blocked_by_cycle({str(r["id"]): [str(b) for b in (r.get("blocked_by") or ())] for r in rows})


async def fate(coro):
    try:
        await coro
        return "ok"
    except Exception as error:  # noqa: BLE001 - every refusal is tallied by class
        return type(error).__name__


async def attempt(mode, rng, index):
    db = f"test_{os.getpid()}_{uuid.uuid4().hex}"
    a = mk(db)
    b = mk(db) if mode == "CS2" else a
    try:
        await a.ensure_ready()
        if mode == "SSX":
            a._supersede_lock = contextlib.nullcontext()
        if index % 2 == 0:  # the #634 hand shape
            t1 = await a.create_task("T1", "p", created_by=WHO)
            t2 = await a.create_task("T2", "p", created_by=WHO)
            d1 = await a.create_task("D1", "p", blocked_by=[t1], created_by=WHO)
            x = await a.create_task("X", "p", blocked_by=[t2], created_by=WHO)
            ids = [t1, t2, d1, x]
            sup_a = (t1, [x])
            sup_b = (t2, [d1])
            cre_a = [d1]
            cre_b = [x]
        else:
            ids = []
            for i in range(ROWS):
                deps = rng.sample(ids, k=min(len(ids), rng.randint(0, 2)))
                ids.append(await a.create_task(f"r{i}", "p", blocked_by=deps, created_by=WHO))
            t_a, t_b = rng.sample(ids, 2)
            sup_a = (t_a, rng.sample([i for i in ids if i != t_a], k=rng.randint(1, 2)))
            sup_b = (t_b, rng.sample([i for i in ids if i != t_b], k=rng.randint(1, 2)))
            cre_a = rng.sample(ids, k=rng.randint(1, 2))
            cre_b = rng.sample(ids, k=rng.randint(1, 2))
        await b._query("RETURN 1")
        sup = lambda led, s: led.supersede_task(s[0], subject="S", description="p", created_by=WHO, blocked_by=s[1])  # noqa: E731
        cre = lambda led, deps: led.create_task("C", "p", blocked_by=deps, created_by=WHO)  # noqa: E731
        if mode in ("CS", "CS2"):
            pair = (cre(a, cre_a), sup(b, sup_a))
        elif mode == "CC":
            pair = (cre(a, cre_a), cre(a, cre_b))
        elif mode == "MS":
            m1, m2 = uuid.uuid4().hex, uuid.uuid4().hex  # the dispatcher's pre-minted ids; M2 names its sibling M1
            pair = (a.create_many([Spec("M1", cre_a), Spec("M2", [*cre_b, m1])], created_by=WHO, ids=[m1, m2]),
                    sup(a, sup_a))
        else:  # SS, SSX
            pair = (sup(a, sup_a), sup(a, sup_b))
        fates = await asyncio.gather(fate(pair[0]), fate(pair[1]))
        after_pair = await cycle_of(a)
        heal = await fate(a._reanchor_stragglers())
        after_heal = await cycle_of(a)
        return tuple(fates), heal, after_pair, after_heal
    finally:
        try:
            await a._query(f"REMOVE DATABASE {db}")
        finally:
            await a.close()
            if b is not a:
                await b.close()


async def main():
    rng = random.Random(SEED)
    verdict = 0
    for mode in ("CS", "CC", "MS", "CS2", "SS", "SSX"):
        tally, cycles, both_ok = {}, [], 0
        for index in range(ATTEMPTS):
            fates, heal, after_pair, after_heal = await attempt(mode, rng, index)
            tally[(fates, heal)] = tally.get((fates, heal), 0) + 1
            both_ok += fates == ("ok", "ok")
            if after_pair or after_heal:
                cycles.append((index, fates, heal, after_pair, after_heal))
        print(f"MODE {mode}: attempts={ATTEMPTS} both_ok={both_ok} cycles={len(cycles)}", flush=True)
        for key, count in sorted(tally.items(), key=str):
            print(f"  fates={key[0]} heal={key[1]} : {count}", flush=True)
        for c in cycles[:3]:
            print(f"  CYCLE attempt={c[0]} fates={c[1]} heal={c[2]} after_pair={c[3]} after_heal={c[4]}", flush=True)
        expected_cycles = mode == "SSX"
        if bool(cycles) != expected_cycles:
            verdict = 2
            print(f"  VERDICT {mode}: UNEXPECTED ({'cycle' if cycles else 'no cycle in the positive control'})", flush=True)
        else:
            print(f"  VERDICT {mode}: as expected", flush=True)
    return verdict


sys.exit(asyncio.run(main()))
```

### `extra/test_ca58e_scale.py`
```python
"""ca58e-probes (packet 58 delta-2 audit, 2026-11-10): the guard's INPUT at scale on the BUILT tree (8679385).

World (the first delta audit's #636 shape, extended): N stragglers D_j [X_j], X_j superseded by its OWN head H_j,
every H_j blocked by one shared chain of `depth` links. PLUS a positive control inserted with ids that sort LAST
(so a guard input that reads only a prefix of the table misses it): D* [X*], X* superseded by H*, H* [E*], E* [D*].
Re-anchoring D* onto H* would close D* -> H* -> E* -> D*, so the heal must SKIP D* and record it once.
Asserts: the boot completes; every D_j is healed onto H_j; D* is untouched and recorded; no cycle over all columns.
Times the whole boot (`boot(env)`) and the guard's one read (`_read_dependency_graph`)."""
from __future__ import annotations

import logging
import time
from datetime import UTC, datetime

import pytest
from _reanchor_58_support import CREATOR, DESCRIPTION, all_columns, boot, column, ledger58, raw
from _surreal_harness import SurrealEnv
from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE
from loremaster.tasks import TaskLedger, find_blocked_by_cycle
from surrealdb import RecordID

__all__ = ["ledger58"]
TIMINGS = "/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-probes-tools/logs/scale_timings.txt"


@pytest.mark.parametrize(("n", "depth"), [(300, 30), (1000, 30), (3000, 0), (3000, 30)])
async def test_guard_input_at_scale(
    ledger58: tuple[TaskLedger, SurrealEnv], n: int, depth: int, monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    ledger, env = ledger58
    now = datetime.now(UTC)
    content = lambda subject, deps: TaskLedger._new_task_content(subject, DESCRIPTION, deps, CREATOR, now)  # noqa: E731,SLF001
    chain = [f"ec{i:05d}".ljust(32, "0") for i in range(max(depth, 1))]
    heads = [f"eh{j:05d}".ljust(32, "0") for j in range(n)]
    olds = [f"ex{j:05d}".ljust(32, "0") for j in range(n)]
    deps = [f"ed{j:05d}".ljust(32, "0") for j in range(n)]
    d_star, x_star, h_star, e_star = ("zzd".ljust(32, "0"), "zzx".ljust(32, "0"), "zzh".ljust(32, "0"), "zze".ljust(32, "0"))
    rows = [{"id": RecordID(TASK_TABLE, c), **content(c, [chain[i + 1]] if i + 1 < len(chain) else [])}
            for i, c in enumerate(chain)]
    rows += [{"id": RecordID(TASK_TABLE, h), **content(h, [chain[0]] if depth else [])} for h in heads]
    rows += [{"id": RecordID(TASK_TABLE, x), **content(x, []), "superseded_by": h} for x, h in zip(olds, heads)]
    rows += [{"id": RecordID(TASK_TABLE, d), **content(d, [x])} for d, x in zip(deps, olds)]
    rows += [
        {"id": RecordID(TASK_TABLE, h_star), **content(h_star, [e_star])},
        {"id": RecordID(TASK_TABLE, e_star), **content(e_star, [d_star])},
        {"id": RecordID(TASK_TABLE, x_star), **content(x_star, []), "superseded_by": h_star},
        {"id": RecordID(TASK_TABLE, d_star), **content(d_star, [x_star])},
    ]
    for start in range(0, len(rows), 2000):
        await raw(ledger, f"INSERT INTO {TASK_TABLE} $rows", {"rows": rows[start:start + 2000]})
    edges = [{"in": RecordID(TASK_TABLE, chain[i + 1]), "out": RecordID(TASK_TABLE, c)} for i, c in enumerate(chain[:-1])]
    edges += [{"in": RecordID(TASK_TABLE, chain[0]), "out": RecordID(TASK_TABLE, h)} for h in heads] if depth else []
    edges += [{"in": RecordID(TASK_TABLE, x), "out": RecordID(TASK_TABLE, d)} for d, x in zip(deps, olds)]
    edges += [{"in": RecordID(TASK_TABLE, a), "out": RecordID(TASK_TABLE, b)}
              for a, b in ((e_star, h_star), (d_star, e_star), (x_star, d_star))]
    for start in range(0, len(edges), 2000):
        await raw(ledger, f"INSERT RELATION INTO {BLOCKS_RELATION} $edges", {"edges": edges[start:start + 2000]})
    reads: list[tuple[float, int]] = []
    original = TaskLedger._read_dependency_graph

    async def timed(self):  # noqa: ANN001
        t0 = time.perf_counter()
        out = await original(self)
        reads.append((round(time.perf_counter() - t0, 4), len(out)))
        return out

    monkeypatch.setattr(TaskLedger, "_read_dependency_graph", timed)
    caplog.set_level(logging.INFO, logger="loremaster")
    t0 = time.perf_counter()
    await boot(env)
    total = time.perf_counter() - t0
    skip_records = [r for r in caplog.records if r.getMessage() == "task.backfill.straggler_would_close_cycle"]
    line = (f"SCALE n={n} depth={depth} task_rows={len(rows)} guard_reads(seconds,rows)={reads} "
            f"boot_seconds={total:.2f} skip_records={[getattr(r, 'task_id', None) for r in skip_records]}")
    print(line)
    with open(TIMINGS, "a") as out:
        out.write(line + "\n")
    columns = await all_columns(ledger)
    unhealed = [d for d, h in zip(deps, heads) if columns.get(d) != [h]]
    assert not unhealed, f"{len(unhealed)} of {n} not healed, e.g. {unhealed[:3]}"
    assert await column(ledger, d_star) == [x_star], "D* was re-anchored onto a cycle"
    assert [getattr(r, "task_id", None) for r in skip_records] == [d_star], "D* not recorded exactly once"
    assert find_blocked_by_cycle(columns) is None, "a cycle was written"
```

### `extra/test_ca58e_wb5_worlds.py`
```python
"""ca58e-probes: are the #638(i) pin's own four WRITER_WORLDS able to see hash-order non-determinism at all?
Evaluates exactly the pin's worlds (imported from the contract file) in 8 interpreters with different PYTHONHASHSEED
values and compares the answers. If the predicate's answer is unique in each world (one candidate cycle), no order
change of any kind can alter it, and this stays GREEN even on a build with every sorted() removed."""
from __future__ import annotations

import os
import subprocess
import sys

_PROGRAM = r'''
import json, sys
sys.path.insert(0, "loremaster/tests")
from test_reanchor_58_fixwave import TestTheCycleAnswerIsDeterministicAndAskedOnceBeforePacking as K
from loremaster.tasks import find_row_blocked_by_cycles
out = {}
for writer, (stored, proposed, asked, aon) in sorted(K.WRITER_WORLDS.items()):
    out[writer] = sorted(find_row_blocked_by_cycles(stored, proposed, sorted(asked), all_or_nothing=aon).items())
print(json.dumps(out))
'''


def _answer(seed: str) -> str:
    env = {**os.environ, "PYTHONHASHSEED": seed}
    return subprocess.run([sys.executable, "-c", _PROGRAM], capture_output=True, text=True, env=env, check=True).stdout


def test_the_pins_worlds_across_hash_seeds() -> None:
    answers = {seed: _answer(seed) for seed in map(str, range(1, 9))}
    assert len(set(answers.values())) == 1, f"the pin's worlds DO vary across processes: {answers}"
```

### `probe.sh`
```bash
#!/usr/bin/env bash
# probe.sh <log> <script> [args...] : run a probe script from copy 2's root under the cgroup cap, tree_id header, EXIT line.
set -u
C2=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-probes2
log=$1; shift; [ -f "$1" ] || { echo "REFUSED: no script $1"; exit 64; }
cd $C2 || exit 65
{ ~/.claude/orchestration/tree_id.sh $C2; echo "CMD: uv run python $*"; date -u +START=%FT%TZ;
  systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 uv run python "$@"; echo "EXIT=$?"; date -u +END=%FT%TZ; } > "$log" 2>&1
tail -3 "$log"
```

### `run.sh`
```bash
#!/usr/bin/env bash
# run.sh <copy> <log> <N-workers> [--run-parked] <selection...> — capped, timed pytest in a scratch copy.
# GUARD (#620): refuses an empty selection and any element that is not an existing file / file::node under the copy.
set -u
copy=$1; log=$2; n=$3; shift 3
extra=()
if [ "${1:-}" = "--run-parked" ]; then extra+=(--run-parked); shift; fi
if [ $# -eq 0 ]; then echo "REFUSED: empty selection" >&2; exit 64; fi
for sel in "$@"; do f=${sel%%::*}; if [ ! -f "$copy/$f" ]; then echo "REFUSED: not a file under copy: $sel" >&2; exit 64; fi; done
cd "$copy" || exit 65
{ ~/.claude/orchestration/tree_id.sh "$copy"; echo "CMD: pytest -q -n $n --timeout=300 ${extra[*]} $*";
  systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 uv run pytest -q -p no:cacheprovider -n "$n" --timeout=300 "${extra[@]}" "$@"; echo "EXIT=$?"; } > "$log" 2>&1
grep -E '^EXIT=|[0-9]+ (passed|failed)' "$log" | tail -2
```

### `proof.sh`
```bash
#!/usr/bin/env bash
# proof.sh <WB> : mutation_proof.py in the scratch copy, declared reds from decl/<WB> (written before the run).
set -u
C=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-probes; T=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-probes-tools; wb=$1
sel=$(cat $T/sel.$wb.txt 2>/dev/null || cat $T/sel.txt)
[ -z "$sel" ] && { echo "REFUSED empty selection"; exit 64; }
[ -s $T/decl/$wb ] || { echo "REFUSED empty declaration"; exit 64; }
exp=(); while IFS= read -r id; do exp+=(--expect-red "$id"); done < $T/decl/$wb
log=$T/logs/d_$wb.log
cd $C
{ ~/.claude/orchestration/tree_id.sh $C; echo "WB=$wb declared=$(wc -l < $T/decl/$wb) decl_md5=$(md5sum $T/decl/$wb | cut -d' ' -f1)";
  uv run python scripts/mutation_proof.py --file loremaster/loremaster/tasks.py --anchor-file $T/mut/$wb.anchor --replacement-file $T/mut/$wb.repl "${exp[@]}" -- \
    systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 uv run pytest -q -p no:cacheprovider -n 8 --timeout=300 $sel;
  echo "EXIT=$?"; } > $log 2>&1
grep -E '^EXIT=|[0-9]+ (passed|failed)|PROOF FAILED|RESTORE|restored byte-exact' $log | tail -4
```

### Own wrong-build deltas (anchor → replacement, applied to `loremaster/loremaster/tasks.py` by mutation_proof.py; anchors matched exactly once)

#### WBL1
```diff
--- anchor
+++ replacement
@@ -1,4 +1,4 @@
-        async with self._supersede_lock:
+        if True:  # WB-L1: lock released before the transaction commits
             row = await self._select_row(task_id)
             if row is None:
                 raise TaskNotFoundError(f"no task with id {render_attributed(task_id)}")
@@ -56,4 +56,5 @@
                 )
                 for dependent, (columns, _row) in dependent_rows.items()
             }
-            await self._refuse_a_cycle({new_id: dependencies, **rewired}, minted={new_id})
+            async with self._supersede_lock:
+                await self._refuse_a_cycle({new_id: dependencies, **rewired}, minted={new_id})
```

#### WBL2
```diff
--- anchor
+++ replacement
@@ -1 +1 @@
-        async with self._supersede_lock:
+        async with asyncio.Lock():  # WB-L2: per-call lock
```

#### WBL3
```diff
--- anchor
+++ replacement
@@ -1,4 +1,4 @@
-        async with self._supersede_lock:
+        if True:  # WB-L3
             row = await self._select_row(task_id)
             if row is None:
                 raise TaskNotFoundError(f"no task with id {render_attributed(task_id)}")
@@ -72,9 +72,10 @@
                 # ride ONE transaction: RELATE comes AFTER the CREATE so the ENFORCED ``out``
                 # endpoint (the fresh successor) exists, and the loser of a raced supersede
                 # rolls back the WHOLE txn (stamp + CREATE + RELATEs) — ZERO orphan edges.
-                await self._apply(
-                    self._supersede_transaction(
-                        task_id, new_id, content, event, dependencies, dependent_ids,
-                        actor=created_by, at=now.isoformat(),
+                async with self._supersede_lock:  # WB-L3: lock around the write only
+                    await self._apply(
+                        self._supersede_transaction(
+                            task_id, new_id, content, event, dependencies, dependent_ids,
+                            actor=created_by, at=now.isoformat(),
+                        )
                     )
-                )
```

#### WBI1
```diff
--- anchor
+++ replacement
@@ -1 +1 @@
-        rows = self._as_rows(await self._query(_DEPENDENCY_COLUMNS_STATEMENT))
+        rows = self._as_rows(await self._query(_DEPENDENCY_COLUMNS_STATEMENT + " LIMIT 1000"))  # WB-I1
```

#### WBI9
```diff
--- anchor
+++ replacement
@@ -1,5 +1,9 @@
+        cached = getattr(self, "_wb_graph_cache", None)  # WB-I9: the first read is reused (stale input)
+        if cached is not None:
+            return {key: list(value) for key, value in cached.items()}
         rows = self._as_rows(await self._query(_DEPENDENCY_COLUMNS_STATEMENT))
-        return {
+        self._wb_graph_cache = {
             str(row.get(_ID_KEY)): [str(blocker) for blocker in (row.get(_COL_BLOCKED_BY) or ())]
             for row in rows
         }
+        return {key: list(value) for key, value in self._wb_graph_cache.items()}
```

### Declared red sets (`decl/`, written before the runs)
```
== WB2
loremaster/tests/test_reanchor_58_fixwave.py::TestTheCycleAnswerIsDeterministicAndAskedOnceBeforePacking::test_638_ii_leg_B_at_ONE_row_per_chunk_still_skips_and_records_both_rows
== WB5
loremaster/tests/test_reanchor_58_fixwave.py::TestTheCycleAnswerIsDeterministicAndAskedOnceBeforePacking::test_638_i_the_served_and_recorded_cycle_is_identical_across_insertion_orders[create]
loremaster/tests/test_reanchor_58_fixwave.py::TestTheCycleAnswerIsDeterministicAndAskedOnceBeforePacking::test_638_i_the_served_and_recorded_cycle_is_identical_across_insertion_orders[create_many]
loremaster/tests/test_reanchor_58_fixwave.py::TestTheCycleAnswerIsDeterministicAndAskedOnceBeforePacking::test_638_i_the_served_and_recorded_cycle_is_identical_across_insertion_orders[heal]
loremaster/tests/test_reanchor_58_fixwave.py::TestTheCycleAnswerIsDeterministicAndAskedOnceBeforePacking::test_638_i_the_served_and_recorded_cycle_is_identical_across_insertion_orders[supersede]
== WB5b
loremaster/tests/test_ca58d_determinism.py::test_the_cycle_answer_is_identical_across_hash_seeds
== WBI1
loremaster/tests/test_reanchor_58_fixwave.py::TestTheGuardsInputHasNoDepthBoundAndNoSeedCost::test_636_a_boot_with_300_stragglers_of_DISTINCT_heads_completes_and_heals_them_all
== WBI1scale
loremaster/tests/test_ca58e_scale.py::test_guard_input_at_scale[1000-30]
loremaster/tests/test_ca58e_scale.py::test_guard_input_at_scale[3000-0]
loremaster/tests/test_ca58e_scale.py::test_guard_input_at_scale[3000-30]
== WBI9
loremaster/tests/test_reanchor_58_fixwave.py::TestTheGuardsInputHasNoDepthBoundAndNoSeedCost::test_635_S_the_live_supersede_refuses_a_cycle_through_a_LONG_chain[control_3_links]
loremaster/tests/test_reanchor_58_fixwave.py::TestTheGuardsInputHasNoDepthBoundAndNoSeedCost::test_635_S_the_live_supersede_refuses_a_cycle_through_a_LONG_chain[40_links]
== WBL1
loremaster/tests/test_reanchor_58_fixwave.py::TestTwoConcurrentSupersedesOnOneLedgerCannotJointlyWriteACycle::test_634_one_of_two_concurrent_supersedes_is_refused_every_time
== WBL2
loremaster/tests/test_reanchor_58_fixwave.py::TestTwoConcurrentSupersedesOnOneLedgerCannotJointlyWriteACycle::test_634_one_of_two_concurrent_supersedes_is_refused_every_time
== WBL3
loremaster/tests/test_reanchor_58_fixwave.py::TestTwoConcurrentSupersedesOnOneLedgerCannotJointlyWriteACycle::test_634_one_of_two_concurrent_supersedes_is_refused_every_time
== WRITTEN_AT
2026-11-10T09:11:58Z
2026-11-10T09:17:05Z
2026-11-10T09:24:05Z
```
