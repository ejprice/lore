brief-base v27 read · brief project v7 read

# coldaudit-58-delta-ca58d-probes: packet 58 fix-wave delta audit, cycle probes and own wrong builds

## SUMMARY BLOCK
- **Verdict (this dimension): NO-GO.** Every probe the brief named HOLDS on cdf1ce4: E1–E4, the strengthened S1–S4, the F1 verifier, r53 P1–P3, the predicate probe at 0/0 on two seeds, and supersede with `all_or_nothing=True` at 0 differences. Two new **product defects**, both in the predicate's INPUT (the closure read), which am-17 §13.2 left unchanged and tagged "reasoned, MEDIUM":
  - **F-A (#636, blocking):** the heal's one closure read costs about (task rows × seeds) and carries `TIMEOUT 5s`. About 300 stragglers fail the BOOT with `TxnDomainRejectionError (unspecified rejection)`. Control: without that read, the same boots heal.
  - **F-B (#637, major):** the closure stops at `TASK_BLOCKER_MAX_DEPTH = 32` hops. A live supersede built only through the API writes a cycle of length 36, and the heal writes one of length 35.
- **Wrong builds:** 8 of my own, run through `mutation_proof.py`. 6 die on the contract. **2 survive the contract** and die only on my probes (F-C, #638, minor test gap):
  - WB5: non-deterministic cycle string;
  - WB2: predicate per chunk, after packing.
- State: done · deviations: (1) test runs inline: this workflow subagent has no `Agent` tool, so it cannot spawn a haiku-runner; (2) WB6's selection adds the two am-3 §4 pin files, because the brief's four files hold no pin for that door; (3) WB0's declared set was 3 reds short (an under-prediction, both-ways diff shown, no declared-but-green).
- `Packages considered: none — no mechanism specified` (audit; the predicate's networkx use was read, not re-specified).
- `Odoo-20 portability: n/a — no Odoo seam touched`. `Reuse ledger: none` (no production symbol written).
- `Graded: cdf1ce4 · HEAD-at-report: cdf1ce4 · SAME`.
- Decisions needed:
  - F-A: what the heal's closure read becomes, and whether the live writers' read changes with it. A design question, so it goes to the lead (fix shape, MEDIUM: compute the closure once in a `LET`, then fetch those ids, instead of a subquery inside `WHERE id IN`).
  - F-B: whether the cycle guard's depth bound may stay as a recorded bound, or the guard refuses when the walk is truncated.
- Pointers: §(a) · §(b) · §(c) · §(d) · §F-A · §F-B · §F-C · §RUNS · §INSTRUMENTS. Findings filed: #636, #637, #638.

## CAPABILITY CHECK
- Demanded: scratch copy, cgroup cap, mutation_proof.py, TEST store :18000, lore. All met.
- Demanded (brief-base §3): fan-out to a haiku-runner. I have no `Agent` tool, so every run was inline, through my guarded runner (`run.sh`, refuses an empty or non-file selection, #620; proven rc=64 on two inputs before the first run).
- lore: loaded, landmine recall returned 10 (< 50, not cut off), registered `ca58d-probes` in `pkt58-20261109`. Grep was used only inside the scratch copy (not indexed) and for node-id extraction from `--collect-only` output.

## ROUTING TABLE (written 2026-11-10 before the first sweep or run)

| step | tier | who | reason |
|---|---|---|---|
| read am-17 §12/§13, fw1 MISSING PINS/P2/INSTRUMENTS, r53 INSTRUMENTS, coldaudit-58 F1 | 3 | me | the probes' expectations are judgment over the ruling |
| scratch copy + checkout cdf1ce4 + provenance | 1 | me inline | one command, on the critical path |
| test runs (E1–E4, P1–P3, verify1, contract files vs each wrong build) | 1 | me inline | no `Agent` tool in this workflow subagent's tool set, so no haiku-runner can be spawned (capability, not choice); every run wrapped by my guarded runner with a tree_id header and EXIT line |
| probe_cycle_predicate_58.py vs the built function | 1 | me inline | a script I run; judgment of its output stays with me |
| wrong-build design | 3 | me | adversarial judgment |
| mutation-proof verdicts | 3 | me | never Haiku (brief-base §3) |

Fan-out: haiku 0 · sonnet 0 · peak 0 — no Agent tool available.

## Provenance (measured 2026-11-10)
- Copy: `scratchpad/ca58d/ca58d-probes` via `scripts/scratch_copy.sh` (EXIT=0), then `git checkout cdf1ce4 -- .`.
  - HEAD = `cdf1ce40680aafcb0ffe8d836ff3ae0e506eca68`.
  - `git status` lists untracked files only: the live tree's five REPORTs, one sibling receipt, and my probe files.
  - Tracked files diff vs cdf1ce4 = 0 at report time.
- `loremaster.__file__` = `…/scratchpad/ca58d/ca58d-probes/loremaster/loremaster/__init__.py`.
- `tasks.py` md5 `769c4bffe177a708366b1937939d6df2` before and after every mutation (restored byte-exact each time).
- Logs: `scratchpad/ca58d/ca58d-probes-tools/logs/` (lead-named dir; each log opens with `tree_id.sh` + `CMD`, ends with `EXIT=`). TREE differs between logs only because untracked probe files were added; production files are unchanged.

## (a) adversary-58-fw1 E1–E4 on cdf1ce4: HOLD
- Verbatim fw1 file → `loremaster/tests/test_ca58d_fw1_probes.py` (md5 e6b4d7a9…, identical to the fence). `logs/a_E1E4.log`: **6 passed, EXIT=0**.
- What E1–E4 leave unchecked, I strengthened (`test_ca58d_own_probes.py`, S1–S4, pasted below). `logs/a_own.log`: S1×2, S2, S3×2, S4 and both depth controls all pass (8 passed). The 2 failures are F-B.
  - S1 (E1 world, two boots): D's column, `updated_at` and edges are byte-identical. Exactly one WARNING per boot, with `blocker_ids == [X]`, `members ⊇ {D, H}` and a cycle starting and ending at D. No `stragglers_reanchored` count.
  - S2 (E2, one row per chunk): both rows unchanged and both recorded.
  - S3 (E3 + control): the store snapshot is identical after the refused supersede, and the refusal names L1, L2 and R.
  - S4 (E4): both recorded.

## (b) §13.5 item 4: the instrument against the built predicate: HOLDS
- `rule_u_built` body = `set(find_row_blocked_by_cycles(stored, proposed, set(proposed), all_or_nothing=False))`. Added: `part_supersede_built_aon`, the built function with `all_or_nothing=True` and `asked={new}` vs "the successor lies on a cycle of the overlay". It also checks that every served cycle is a real path of the overlay.

| run | log | heal worlds | U all / partial | NONE all / partial | supersede (built, AON) differs |
|---|---|---|---|---|---|
| `--built 4000 58` | `logs/b_built_58.log` | 2911 | **0 / 0** | 2271 / 1858 | **0** of 4000 (2065 refused) |
| `--built 6000 20261110` | `logs/b_built_20261110.log` | 4338 | **0 / 0** | 3336 / 2720 | **0** of 6000 (3080 refused) |
| reference (no `--built`), 4000 58 | `logs/b_ref_58.log` | 2911 | 0 / 0 | 2271 / 1858 | — (same numbers as am-17 §13.1) |

- In-process order independence (`determinism_probe.py`, 3000 worlds × 4 shuffles × both modes): 0 order-dependent answers (`logs/b_determinism.log`).
- Bound: the probe hands the function the WHOLE graph. It cannot see F-A or F-B, which are in the closure read that feeds the function in production.

## (c) The first audit's instruments: F1 now PASSES, P1–P3 no regression
- `probe_verify1.py` (from `scratchpad/ca58/verify1-notes/`, unchanged), `logs/c_verify1.log`, EXIT=0, both variants, three boots each:
  - D stays `['X']`;
  - every boot emits `WARNING:task.backfill.straggler_would_close_cycle`;
  - no `stragglers_reanchored`;
  - the live-supersede control is still REFUSED.

  At aa4ea04 the same probe wrote D→H→D.
- r53 P1–P3 (verbatim fence → `test_ca58d_r53_probes.py`): `logs/c_r53_P1P3.log`, **3 passed, EXIT=0**. P3 still raises `StragglerHealPackerError` (the skip runs before packing and does not swallow an over-bound row).

## (d) Own wrong builds (mutation_proof.py; declared reds from `--collect-only --run-parked`, written 2026-11-10T07:40:48Z before any run; WB0 amended pre-run with 4 create-path ids; `decl/WRITTEN_AT`)
Selection: the brief's four files (`test_reanchor_58_fixwave.py`, `test_blocks_edge.py`, `test_cycle_write_path_04b3.py`, `test_supersede_reanchor_58.py`) plus fw1 E1–E4 and my S1–S4 = **301 tests**. Baseline on cdf1ce4: **301 passed, EXIT=0** (`logs/d_baseline.log`).

| build | delta (tasks.py) | declared | observed | verdict | log |
|---|---|---|---|---|---|
| WB0 | predicate returns `{}` (positive control + sharing) | 29 | 32 failed | KILLED; all 29 red, plus 3 more undeclared reds (positive legs of formatter / batch-key / error-class pins that also ride on the predicate); 0 declared-but-green | `d_WB0.log` |
| WB1 | supersede checks only the successor's own column (`**rewired` dropped) | 10 | 10 | KILLED, exact | `d_WB1.log` |
| WB2 | predicate per CHUNK, after `_pack_heal_chunks` | 2 (E2, S2) | 1 (S2) | **SURVIVES the contract (and fw1 E2)**; only my S2 kills it | `d_WB2.log` |
| WB3 | heal `all_or_nothing=True` (pending rows lose stored edges) | 1 (D2-ii) | 1 | KILLED, exact | `d_WB3.log` |
| WB4 | heal proposes only the rewrite DELTA (new heads) | 1 (leg C) | 1 | KILLED, exact | `d_WB4.log` |
| WB5 | every `sorted()` in the predicate removed (hash-order cycle string) | 1 (guess) | 0 (301 passed) | **SURVIVES all 301**; killed by my cross-process probe (`d_WB5b.log`: 4 seeds → 4 digests; correct build: `d_determinism_correct.log` 1 passed) | `d_WB5.log` |
| WB6 | supersede `minted=None` (breaks am-3 §4) | 2 (PR8 pins) | 2 | KILLED, exact (selection + 2 am-3 §4 files, deviation) | `d_WB6.log` |
| WB7 | predicate returns after the FIRST hit row | 6 | 6 | KILLED, exact | `d_WB7.log` |

- WB2 does NOT violate P on any world I tried. Each later chunk re-reads the store after earlier chunks wrote, so in E2 the build heals D1 and then skips D2. That is a fate §13.4 rules out ("one pass … BEFORE packing"; both rows skipped), and it makes one closure read per chunk. It is a ruling deviation the contract cannot see. MEDIUM on "no P violation", because chunk-rejection interleavings were not tried.
- WB5 breaks am-17 §13.2 item 4 ("the answer is the same every run"). The served refusal and the WARNING's `cycle` would name a different loop in different processes. No contract pin can see it, because every pin runs in one process.

## F-A (#636): the heal's closure read fails the boot at a few hundred stragglers
- **Claim:** am-17 §13.2 makes the heal call `_bounded_dependency_graph(seeds)` once, with seeds = every proposed blocker. That read's engine cost is about (task-table rows) × (seeds), and its SELECT carries `TIMEOUT 5s` (`_TRAVERSAL_TIMEOUT`). Past roughly 290k row-seeds, `ensure_ready` raises and the server does not boot.
- **Evidence, cost curve** (`logs/e_closure_2d.log` + `closure_2d.txt`, `logs/e_closure_curve.log` + `closure_curve.txt`; depth-0 worlds, so the walk itself is trivial):
  - seeds = 1: 0.011 / 0.042 / 0.149 / 0.607 s at 300 / 1 200 / 4 800 / 19 200 rows (linear in the table);
  - table = 2 400 rows: 0.449 / 2.069 / 4.106 s at 10 / 50 / 100 seeds, and 200 seeds hits the TIMEOUT;
  - heal-shaped (3n rows, n seeds): 0.007 / 0.135 / 0.550 / 2.112 s at n = 10 / 50 / 100 / 200, and n = 400 hits the TIMEOUT.
- **Evidence, boot level** (`logs/e_closure_scale2.log`): worlds of 300 stragglers (930 rows, chain depth 30), 1 000, 3 000 (depth 0) and 3 000 (depth 30). **All 4 boots raise**:
  - `QueryError: The query was not executed because it exceeded the timeout: 5s` → `TxnDomainRejectionError … (unspecified rejection)`;
  - traceback `ensure_ready` (tasks.py `ensure_ready`) → `_reanchor_stragglers` → `_skip_cycle_closing_rows` → `_bounded_dependency_graph` (`logs/e_closure_scale.log`).
- **Control** (`logs/e_closure_control_noread.log`): only that one line replaced by `stored = {}`. The 300- and 3 000-straggler boots then complete (0.44 s, 9.27 s) and heal. tasks.py restored byte-exact (md5 above).
- **Why it matters:** am-17 §12.2 rules out a boot denial ("one legacy row's shape would stop the server for every consumer"). am-17 §2 sizes heal chunks at 10 000 rows. The heal now never reaches the packer once rows × seeds passes ~290k, and the error names no cause. §12.2's cost claim ("one extra round trip") is true of the round-trip count and false of the cost.
- **Siblings, pre-existing (04b-3), not driven here at the verbs:** create, create_many and supersede use the same read, so their latency grows linearly with table size (0.6 s per seed at 19 200 rows). A supersede seeds every rewired dependent's blockers, so a hub supersede multiplies seeds; #628 may be the same mechanism.
  - The 04b-3 pin `test_the_WRITE_paths_rows_READ_does_NOT_grow_with_the_DEPENDENCY_FREE_population` counts rows SERVED, not engine work, which is why it stayed green.
- **Mechanism, MEDIUM** (inferred from the linear-in-table growth; no EXPLAIN run): the closure subquery inside `WHERE id IN (…)` appears to be re-evaluated per outer row of a task-table scan.
- **Confidence:** HIGH on the measurements, timeout and boot failure, with its control. MEDIUM on the mechanism. Production table size is unknown (not measured; :18500 not touched).
- **Reproduce:** paste `test_ca58d_closure_2d.py` / `test_ca58d_closure_scale.py` (below) into `loremaster/tests/` of a cdf1ce4 scratch copy, then `run.sh <copy> <log> 1 loremaster/tests/test_ca58d_closure_scale.py`.

## F-B (#637): the cycle guard's input stops at 32 hops, so supersede and the heal write long cycles
- **Claim:** `find_row_blocked_by_cycles` is exact over its input, but the input is `@.{1..32+collect}` over `blocks`. A cycle whose return path is longer than 32 hops is never read, so the predicate answers "no cycle". The docstring of `_bounded_dependency_graph` says "Bounding to the closure therefore loses no cycle; it is sound, not a heuristic". That holds only up to `TASK_BLOCKER_MAX_DEPTH`.
- **Evidence** (`logs/a_own.log`, `logs/a_depth_edge.log`; probe `TestDepthDoor`):
  - **Live supersede, built entirely through `create_task` / `supersede_task`:** X; R [X]; c_n [R]; c_{n-1} [c_n] … c_1 [c_2]; `supersede(X, blocked_by=[c_1])`. n = 28, 31, 32, 33: refused. **n = 34: SUCCEEDS** and writes S → c1 → … → c34 → R → S (length 36). Reachability check: the successor is on a cycle.
  - **Boot heal:** D [X→H]; H [c_1]; c_1 [c_2] … c_n [D]. n = 28, 31, 32: skipped and recorded. **n = 33: D re-anchored onto a cycle of length 35**, logged as a normal heal.
- **Why it matters:** every member of such a cycle is unclaimable forever, and nothing records it. The supersede rewire and the heal are packet 58 code (undeployed, am-17 §12.8-3).
  - 04b-3 relied on "a persisted-id cycle is UNREACHABLE through the verbs" (`test_cycle_write_path_04b3.py` module docstring). Packet 58's rewire made it reachable, and the depth bound was never re-examined.
  - The deep-chain pin `test_the_cycle_WALK_is_ONE_round_trip_however_DEEP_the_chain` uses depth 30, under the bound.
  - Exposure: a 34-deep blocker chain is unusual but legal. Plausibility LOW-MEDIUM. Correctness of a served guard: HIGH.
- **Reproduce:** `TestDepthDoor` in `test_ca58d_own_probes.py` (below); `extra = 2` is the failing leg and `extra = -4` the control.

## F-C (#638, minor, test gap): two survivors of the contract
WB5 (determinism) and WB2 (per-chunk). See §(d). Both rulings are am-17 §13.2 / §13.4 / §13.6 text with no pin. Instruments that kill them: `test_ca58d_determinism.py` and S2.

## Residuals noticed (no finding filed; for the lead)
- R1: the `CYCLE_NOUN_PERSISTED_IDS` comment in tasks.py still says the two vocabularies sit over "the ONE shared detector (`find_blocked_by_cycle`)". After §13.3 the persisted-id noun is served from `find_row_blocked_by_cycles`. A stale comment, not served text.
- R2: `scripts/pending_contracts.yaml` `packet-58-fixwave` is still `active: true` at cdf1ce4, and its trigger says it "self-destructs and is deleted with the build". All 17 ids I ran are green. This is the receipts dimension's to rule on. I only note it.
- R3: `find_row_blocked_by_cycles`'s `blocker == row` test is subsumed by the component test (a node is in its own SCC). Equivalent mutant, harmless.

## §RUNS (all 2026-11-10, scratch copy at cdf1ce4, TEST store :18000, `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0`, `-n ≤ 8`, `--timeout=300`)

| # | what | command (runner) | log | count line | EXIT |
|---|---|---|---|---|---|
| 1 | fw1 E1–E4 | `run.sh … 4 test_ca58d_fw1_probes.py` | `a_E1E4.log` | 6 passed | 0 |
| 2 | S1–S4 + depth | `run.sh … 6 test_ca58d_own_probes.py` | `a_own.log` | 2 failed, 8 passed | 1 (F-B) |
| 3 | depth edge n=31..33 | `run.sh … 6 test_ca58d_depth_edge.py::TestDepthDoor` | `a_depth_edge.log` | 1 failed, 5 passed | 1 (F-B) |
| 4–6 | predicate probe | `uv run python probe_cycle_predicate_58_built.py --built 4000 58` / `--built 6000 20261110` / `4000 58` | `b_built_58.log`, `b_built_20261110.log`, `b_ref_58.log` | see §(b) | 0 |
| 7 | in-process determinism | `determinism_probe.py 3000 7` | `b_determinism.log` | 0 order-dependent | 0 |
| 8 | F1 verifier | `probe_verify1.py <copy>` | `c_verify1.log` | see §(c) | 0 |
| 9 | r53 P1–P3 | `run.sh … 3 test_ca58d_r53_probes.py` | `c_r53_P1P3.log` | 3 passed | 0 |
| 10 | baseline | `run.sh … 8 --run-parked <301-test selection>` | `d_baseline.log` | 301 passed | 0 |
| 11 | am-3 §4 baseline | `run.sh … 4 --run-parked <2 PR8 files>` | `d_baseline_r2.log` | 4 passed | 0 |
| 12–19 | WB0–WB7 | `proof.sh WBn` | `d_WBn.log` | §(d) | 4/0/4/0/0/4/0/0 |
| 20–21 | determinism, correct + WB5 | `run.sh … 1 test_ca58d_determinism.py`; mutation_proof WB5 | `d_determinism_correct.log`, `d_WB5b.log` | 1 passed; 1 failed | 0 / 0 |
| 22–26 | F-A curve, 2d, scale, control | `run.sh … test_ca58d_closure_*.py` | `e_closure_*.log` | §F-A | — |

## §INSTRUMENTS (pasted verbatim below by the auditor's shell, from `scratchpad/ca58d/ca58d-probes-tools/`)

### `extra/test_ca58d_own_probes.py`
```python
"""ca58d-probes (delta cold audit, packet 58 fix wave): strengthened E1-E4 + the closure-depth door.

Scratch only, never committed by this auditor (pasted verbatim into the receipts file).
S-legs strengthen adversary-58-fw1's E1-E4 with the parts of P the originals leave unchecked
(byte-identical row + edges, recorded with the ruled fields, nothing written on a refused supersede).
DEPTH legs: the predicate is exact over its INPUT, but the input is the ancestor closure bounded at
TASK_BLOCKER_MAX_DEPTH hops over the `blocks` edge. A cycle longer than that is never read.
"""
from __future__ import annotations

import logging

import pytest
from _reanchor_58_support import (
    all_columns, boot, column, create, edge_pairs, ledger58, raw_force, raw_relate, raw_seed_row,
    row_count, snapshot, supersede, updated_at_of,
)
from _surreal_harness import SurrealEnv
from loremaster.tasks import TASK_BLOCKER_MAX_DEPTH, TaskCycleError, TaskLedger

__all__ = ["ledger58"]
WOULD = "task.backfill.straggler_would_close_cycle"


def _id(tag: str) -> str:
    return tag.ljust(32, "0")[:32]


def _on_cycle(cols: dict[str, list[str]], node: str) -> bool:
    """Ground truth by reachability: node reaches itself over blocked_by columns."""
    seen, stack = set(), list(cols.get(node, ()))
    while stack:
        n = stack.pop()
        if n == node:
            return True
        if n in seen:
            continue
        seen.add(n)
        stack.extend(cols.get(n, ()))
    return False


def _would(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.getMessage() == WOULD]


async def _row_picture(ledger: TaskLedger, task_id: str) -> tuple:
    edges = sorted(p for p in await edge_pairs(ledger) if task_id in p)
    return (await column(ledger, task_id), await updated_at_of(ledger, task_id), edges)


class TestS1E1Strengthened:
    @pytest.mark.parametrize("order", ["legacy_ids_sort_first", "control_dependent_sorts_first"])
    async def test_S1_E1_world_row_byte_identical_recorded_with_fields_every_boot(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture, order: str
    ) -> None:
        ledger, env = ledger58
        if order == "legacy_ids_sort_first":
            l1, l2, h, x, d = _id("00s1a1"), _id("00s1b2"), _id("00s1h"), _id("00s1x"), _id("00s1d")
        else:
            l1, l2, h, x, d = _id("00s1l1"), _id("00s1l2"), _id("00s1h"), _id("00s1x"), _id("00s1d")
        await raw_seed_row(ledger, h, blocked_by=[])
        await raw_seed_row(ledger, x, blocked_by=[], superseded_by=h)
        await raw_seed_row(ledger, d, blocked_by=[x])
        await raw_seed_row(ledger, l1, blocked_by=[])
        await raw_seed_row(ledger, l2, blocked_by=[])
        await raw_force(ledger, l1, blocked_by=[l2])
        await raw_force(ledger, l2, blocked_by=[l1, d])
        await raw_force(ledger, h, blocked_by=[l1])
        for blocker, blocked in ((x, d), (l2, l1), (l1, l2), (d, l2), (l1, h)):
            await raw_relate(ledger, blocker, blocked)
        before = await _row_picture(ledger, d)
        for boot_no in (1, 2):
            caplog.clear()
            with caplog.at_level(logging.DEBUG):
                await boot(env)
            cols = await all_columns(ledger)
            assert not _on_cycle(cols, d), f"boot {boot_no}: D on a cycle: {cols}"
            assert await _row_picture(ledger, d) == before, f"boot {boot_no}: D's row/edges changed"
            recs = [r for r in _would(caplog) if getattr(r, "task_id", None) == d]
            assert len(recs) == 1, f"boot {boot_no}: expected one WARNING for D, saw {len(recs)}"
            rec = recs[0]
            assert rec.levelno == logging.WARNING
            assert list(rec.blocker_ids) == [x], rec.blocker_ids
            assert {d, h}.issubset(set(rec.members)), rec.members
            assert rec.cycle.startswith(d) and rec.cycle.endswith(d), rec.cycle
            counted = [r for r in caplog.records if r.getMessage() == "task.backfill.stragglers_reanchored"]
            assert not counted, f"boot {boot_no}: a heal count was logged with D skipped: {[r.__dict__.get('count') for r in counted]}"


class TestS2E2Strengthened:
    async def test_S2_joint_cycle_one_row_per_chunk_both_unchanged_and_recorded(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        ledger, env = ledger58
        monkeypatch.setattr(TaskLedger, "_pack_heal_chunks", staticmethod(lambda built: [[e] for e in built]))
        h1 = await create(ledger, "s2 H1"); h2 = await create(ledger, "s2 H2")
        x1, x2 = _id("s2x1"), _id("s2x2")
        await raw_seed_row(ledger, x1, blocked_by=[], superseded_by=h1)
        await raw_seed_row(ledger, x2, blocked_by=[], superseded_by=h2)
        d1, d2 = _id("s2d1"), _id("s2d2")
        await raw_seed_row(ledger, d1, blocked_by=[x1]); await raw_relate(ledger, x1, d1)
        await raw_seed_row(ledger, d2, blocked_by=[x2]); await raw_relate(ledger, x2, d2)
        await raw_force(ledger, h1, blocked_by=[d2]); await raw_relate(ledger, d2, h1)
        await raw_force(ledger, h2, blocked_by=[d1]); await raw_relate(ledger, d1, h2)
        before = (await _row_picture(ledger, d1), await _row_picture(ledger, d2))
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            await boot(env)
        cols = await all_columns(ledger)
        assert not _on_cycle(cols, d1) and not _on_cycle(cols, d2), cols
        assert (await _row_picture(ledger, d1), await _row_picture(ledger, d2)) == before
        assert sorted(getattr(r, "task_id", "") for r in _would(caplog)) == sorted([d1, d2])


class TestS3E3Strengthened:
    @pytest.mark.parametrize("legacy_loop", [True, False], ids=["with_legacy_loop", "control_no_legacy_loop"])
    async def test_S3_refused_supersede_writes_NOTHING(
        self, ledger58: tuple[TaskLedger, SurrealEnv], legacy_loop: bool
    ) -> None:
        ledger, env = ledger58
        x = await create(ledger, "s3 X")
        l1, l2, r = _id("00s3l1"), _id("00s3l2"), _id("00s3r")
        await raw_seed_row(ledger, r, blocked_by=[x]); await raw_relate(ledger, x, r)
        await raw_seed_row(ledger, l1, blocked_by=[]); await raw_seed_row(ledger, l2, blocked_by=[])
        await raw_force(ledger, l1, blocked_by=[l2])
        await raw_force(ledger, l2, blocked_by=[l1, r] if legacy_loop else [r])
        for blocker, blocked in ((l2, l1), (r, l2)) + (((l1, l2),) if legacy_loop else ()):
            await raw_relate(ledger, blocker, blocked)
        await boot(env)
        before = await snapshot(ledger)
        with pytest.raises(TaskCycleError) as refused:
            await supersede(ledger, x, blocked_by=[l1])
        assert await snapshot(ledger) == before, "a refused supersede changed the store"
        text = str(refused.value)
        for member in (l1, l2, r):
            assert member in text, f"the refusal does not name {member}: {text}"


class TestS4E4Strengthened:
    async def test_S4_two_independent_cycles_both_recorded(
        self, ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
    ) -> None:
        ledger, env = ledger58
        h1 = await create(ledger, "s4 H1"); h2 = await create(ledger, "s4 H2")
        x1, x2 = _id("s4x1"), _id("s4x2")
        await raw_seed_row(ledger, x1, blocked_by=[], superseded_by=h1)
        await raw_seed_row(ledger, x2, blocked_by=[], superseded_by=h2)
        d1, d2 = _id("s4d1"), _id("s4d2")
        await raw_seed_row(ledger, d1, blocked_by=[x1]); await raw_relate(ledger, x1, d1)
        await raw_seed_row(ledger, d2, blocked_by=[x2]); await raw_relate(ledger, x2, d2)
        await raw_force(ledger, h1, blocked_by=[d1]); await raw_relate(ledger, d1, h1)
        await raw_force(ledger, h2, blocked_by=[d2]); await raw_relate(ledger, d2, h2)
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            await boot(env)
        assert await column(ledger, d1) == [x1] and await column(ledger, d2) == [x2]
        assert sorted(getattr(r, "task_id", "") for r in _would(caplog)) == sorted([d1, d2])


# ---- the closure-depth door ------------------------------------------------------------------------------
@pytest.mark.parametrize("extra", [-4, 2], ids=["control_inside_depth", "past_depth"])
class TestDepthDoor:
    async def test_DEPTH_live_supersede_refuses_a_cycle_longer_than_the_closure_depth(
        self, ledger58: tuple[TaskLedger, SurrealEnv], extra: int
    ) -> None:
        """Built ENTIRELY through the live API (no raw seed): X; R blocked_by [X]; a chain c_n -> ... -> c_1
        with c_n blocked_by [R]. supersede(X, blocked_by=[c_1]) re-anchors R onto S, closing
        S -> c_1 -> ... -> c_n -> R -> S. Must be refused whatever n is."""
        ledger, env = ledger58
        n = TASK_BLOCKER_MAX_DEPTH + extra
        x = await create(ledger, "depth X")
        r = await create(ledger, "depth R", [x])
        chain = [await create(ledger, f"depth c{n}", [r])]
        for i in range(n - 1, 0, -1):
            chain.append(await create(ledger, f"depth c{i}", [chain[-1]]))
        c1 = chain[-1]
        try:
            await supersede(ledger, x, blocked_by=[c1])
        except TaskCycleError:
            return
        cols = await all_columns(ledger)
        succ = (await ledger.get_task(x)).superseded_by
        assert succ is not None and _on_cycle(cols, succ), "probe world wrong: no cycle after supersede"
        pytest.fail(f"n={n}: the live supersede WROTE a blocked_by cycle of length {n + 2} through its successor")

    async def test_DEPTH_heal_never_writes_a_cycle_longer_than_the_closure_depth(
        self, ledger58: tuple[TaskLedger, SurrealEnv], extra: int, caplog: pytest.LogCaptureFixture
    ) -> None:
        """D [X -> H]; H [c_1]; c_1 [c_2] ... c_n [D] (live creates for the chain, raw for the legacy
        straggler). Re-anchoring D closes D -> H -> c_1 -> ... -> c_n -> D."""
        ledger, env = ledger58
        n = TASK_BLOCKER_MAX_DEPTH + extra
        d, x = _id("00dpd"), _id("00dpx")
        await raw_seed_row(ledger, d, blocked_by=[])
        chain = [await create(ledger, f"heal c{n}", [d])]
        for i in range(n - 1, 0, -1):
            chain.append(await create(ledger, f"heal c{i}", [chain[-1]]))
        h = await create(ledger, "heal H", [chain[-1]])
        await raw_seed_row(ledger, x, blocked_by=[], superseded_by=h)
        await raw_force(ledger, d, blocked_by=[x]); await raw_relate(ledger, x, d)
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            await boot(env)
        cols = await all_columns(ledger)
        assert not _on_cycle(cols, d), (
            f"n={n}: the heal wrote D onto a blocked_by cycle of length {n + 2}: D={cols[d]}"
        )
        assert cols[d] == [x] and any(getattr(r, "task_id", None) == d for r in _would(caplog))
```

### `extra/test_ca58d_determinism.py`
```python
"""ca58d-probes: the persisted-row cycle predicate gives the SAME answer (rows and cycle strings) in every
process (am-17 §13.2 item 4: "nodes and edges are added sorted so the answer is the same every run"). Two
interpreters with different PYTHONHASHSEED values evaluate the same 3000 worlds and must agree byte-for-byte."""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys

_PROGRAM = r'''
import hashlib, json, random
from loremaster.tasks import find_row_blocked_by_cycles
rng = random.Random(58)
digest = hashlib.sha256()
for _ in range(3000):
    n = rng.randint(4, 9)
    ids = [f"{rng.getrandbits(32):08x}" for _ in range(n)]
    stored = {t: [b for b in ids if b != t and rng.random() < 0.35] for t in ids}
    proposed = {t: [b for b in ids if rng.random() < 0.4] for t in rng.sample(ids, rng.randint(1, n))}
    for aon in (True, False):
        out = find_row_blocked_by_cycles(stored, proposed, list(proposed), all_or_nothing=aon)
        digest.update(json.dumps(sorted(out.items())).encode())
print(digest.hexdigest())
'''


def _digest(seed: str) -> str:
    env = {**os.environ, "PYTHONHASHSEED": seed}
    done = subprocess.run([sys.executable, "-c", _PROGRAM], capture_output=True, text=True, env=env, check=True)
    return done.stdout.strip()


def test_the_cycle_answer_is_identical_across_hash_seeds() -> None:
    digests = {seed: _digest(seed) for seed in ("1", "2", "3", "4")}
    assert len(set(digests.values())) == 1, f"order-dependent answers across processes: {digests}"
    assert all(len(d) == 64 for d in digests.values()), digests
```

### `extra/test_ca58d_closure_curve.py`
```python
"""ca58d-probes: cost curve of ONE _bounded_dependency_graph call vs seed count (the heal passes every proposed
blocker as a seed). World per n: n heads (no blockers), n superseded olds, n stragglers. Depth 0, so the walk itself
is trivial; only the seed count and the table size grow. Each timing is appended to a file as it is taken."""
from __future__ import annotations

import time
from datetime import UTC, datetime

import pytest
from _reanchor_58_support import CREATOR, DESCRIPTION, ledger58, raw
from _surreal_harness import SurrealEnv
from loremaster.store.surreal_schema import TASK_TABLE
from loremaster.tasks import TaskLedger
from surrealdb import RecordID

__all__ = ["ledger58"]
OUT = "/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58d/ca58d-probes-tools/logs/closure_curve.txt"


@pytest.mark.parametrize("n", [10, 50, 100, 200, 400, 800])
async def test_closure_curve(ledger58: tuple[TaskLedger, SurrealEnv], n: int) -> None:
    ledger, _env = ledger58
    now = datetime.now(UTC)
    c = lambda s, d: TaskLedger._new_task_content(s, DESCRIPTION, d, CREATOR, now)  # noqa: E731,SLF001
    heads = [f"ch{j:05d}".ljust(32, "0") for j in range(n)]
    rows = [{"id": RecordID(TASK_TABLE, h), **c(h, [])} for h in heads]
    rows += [{"id": RecordID(TASK_TABLE, f"cx{j:05d}".ljust(32, "0")), **c("x", []), "superseded_by": h} for j, h in enumerate(heads)]
    rows += [{"id": RecordID(TASK_TABLE, f"cd{j:05d}".ljust(32, "0")), **c("d", [f"cx{j:05d}".ljust(32, "0")])} for j in range(n)]
    await raw(ledger, f"INSERT INTO {TASK_TABLE} $rows", {"rows": rows})
    t0 = time.perf_counter()
    try:
        got = await ledger._bounded_dependency_graph(heads)  # noqa: SLF001
        verdict = f"ok rows={len(got)}"
    except Exception as error:  # noqa: BLE001
        verdict = f"RAISED {type(error).__name__}"
    with open(OUT, "a") as out:
        out.write(f"n={n} table_rows={3 * n} seeds={n} seconds={time.perf_counter() - t0:.3f} {verdict}\n")
```

### `extra/test_ca58d_closure_2d.py`
```python
"""ca58d-probes: separate the closure read's two growth variables. (a) table fixed at 3*800 rows, seeds k varies;
(b) seeds fixed at 1 and 100, table grows (dependency-free filler rows)."""
from __future__ import annotations

import time
from datetime import UTC, datetime

import pytest
from _reanchor_58_support import CREATOR, DESCRIPTION, ledger58, raw
from _surreal_harness import SurrealEnv
from loremaster.store.surreal_schema import TASK_TABLE
from loremaster.tasks import TaskLedger
from surrealdb import RecordID

__all__ = ["ledger58"]
OUT = "/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58d/ca58d-probes-tools/logs/closure_2d.txt"


async def _time(ledger: TaskLedger, seeds: list[str], label: str) -> None:
    t0 = time.perf_counter()
    try:
        got = await ledger._bounded_dependency_graph(seeds)  # noqa: SLF001
        verdict = f"ok rows={len(got)}"
    except Exception as error:  # noqa: BLE001
        verdict = f"RAISED {type(error).__name__}"
    with open(OUT, "a") as out:
        out.write(f"{label} seeds={len(seeds)} seconds={time.perf_counter() - t0:.3f} {verdict}\n")


async def _fill(ledger: TaskLedger, ids: list[str]) -> None:
    now = datetime.now(UTC)
    rows = [{"id": RecordID(TASK_TABLE, i), **TaskLedger._new_task_content(i, DESCRIPTION, [], CREATOR, now)} for i in ids]  # noqa: SLF001
    for s in range(0, len(rows), 2000):
        await raw(ledger, f"INSERT INTO {TASK_TABLE} $rows", {"rows": rows[s:s + 2000]})


async def test_a_fixed_table_varying_seeds(ledger58: tuple[TaskLedger, SurrealEnv]) -> None:
    ledger, _env = ledger58
    ids = [f"fa{j:05d}".ljust(32, "0") for j in range(2400)]
    await _fill(ledger, ids)
    for k in (10, 50, 100, 200):
        await _time(ledger, ids[:k], "a table=2400")


async def test_b_fixed_seeds_growing_table(ledger58: tuple[TaskLedger, SurrealEnv]) -> None:
    ledger, _env = ledger58
    have: list[str] = []
    for size in (300, 1200, 4800, 19200):
        new = [f"fb{j:06d}".ljust(32, "0") for j in range(len(have), size)]
        await _fill(ledger, new)
        have += new
        await _time(ledger, have[:1], f"b table={size}")
        await _time(ledger, have[:100], f"b table={size}")
```

### `extra/test_ca58d_closure_scale.py`
```python
"""ca58d-probes: the heal's ONE closure read at scale. N stragglers, each re-anchored to its OWN head, every head
blocked by one shared chain of depth 30. Seeds = N heads; each seed's +collect walk covers the 30-deep chain.
Measures the closure call and asserts the boot completes (the read carries TIMEOUT 5s)."""
from __future__ import annotations

import time
from datetime import UTC, datetime

import pytest
from _reanchor_58_support import CREATOR, DESCRIPTION, boot, column, ledger58, raw
from _surreal_harness import SurrealEnv
from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE
from loremaster.tasks import TaskLedger
from surrealdb import RecordID

__all__ = ["ledger58"]


@pytest.mark.parametrize(("n", "depth"), [(300, 30), (1000, 30), (3000, 0), (3000, 30)])
async def test_closure_read_at_scale(ledger58: tuple[TaskLedger, SurrealEnv], n: int, depth: int, monkeypatch) -> None:
    ledger, env = ledger58
    now = datetime.now(UTC)
    content = lambda subject, deps: TaskLedger._new_task_content(subject, DESCRIPTION, deps, CREATOR, now)  # noqa: E731,SLF001
    chain = [f"sc{i:05d}".ljust(32, "0") for i in range(max(depth, 1))]
    heads = [f"sh{j:05d}".ljust(32, "0") for j in range(n)]
    olds = [f"sx{j:05d}".ljust(32, "0") for j in range(n)]
    deps = [f"sd{j:05d}".ljust(32, "0") for j in range(n)]
    rows = [{"id": RecordID(TASK_TABLE, c), **content(c, [chain[i + 1]] if i + 1 < len(chain) else [])}
            for i, c in enumerate(chain)]
    rows += [{"id": RecordID(TASK_TABLE, h), **content(h, [chain[0]] if depth else [])} for h in heads]
    rows += [{"id": RecordID(TASK_TABLE, x), **content(x, []), "superseded_by": h} for x, h in zip(olds, heads)]
    rows += [{"id": RecordID(TASK_TABLE, d), **content(d, [x])} for d, x in zip(deps, olds)]
    for start in range(0, len(rows), 2000):
        await raw(ledger, f"INSERT INTO {TASK_TABLE} $rows", {"rows": rows[start:start + 2000]})
    edges = [{"in": RecordID(TASK_TABLE, chain[i + 1]), "out": RecordID(TASK_TABLE, c)} for i, c in enumerate(chain[:-1])]
    edges += [{"in": RecordID(TASK_TABLE, chain[0]), "out": RecordID(TASK_TABLE, h)} for h in heads] if depth else []
    edges += [{"in": RecordID(TASK_TABLE, x), "out": RecordID(TASK_TABLE, d)} for d, x in zip(deps, olds)]
    for start in range(0, len(edges), 2000):
        await raw(ledger, f"INSERT RELATION INTO {BLOCKS_RELATION} $edges", {"edges": edges[start:start + 2000]})
    timings: list[tuple[int, float, int]] = []
    original = TaskLedger._bounded_dependency_graph

    async def timed(self, seeds):  # noqa: ANN001
        seeds = list(seeds)
        t0 = time.perf_counter()
        out = await original(self, seeds)
        timings.append((len(seeds), time.perf_counter() - t0, len(out)))
        return out

    monkeypatch.setattr(TaskLedger, "_bounded_dependency_graph", timed)
    t0 = time.perf_counter()
    await boot(env)
    total = time.perf_counter() - t0
    print(f"CLOSURE n={n} depth={depth} timings(seeds, seconds, rows)={timings} boot_seconds={total:.2f}")
    with open('/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58d/ca58d-probes-tools/logs/closure_timings.txt', "a") as out:
        out.write(f"CLOSURE n={n} depth={depth} timings(seeds, seconds, rows)={timings} boot_seconds={total:.2f}\n")
    assert await column(ledger, deps[0]) == [heads[0]]
```

### `extra/determinism_probe.py`
```python
"""ca58d-probes: is find_row_blocked_by_cycles' answer (rows AND cycle strings) independent of the INPUT's
dict / list order? The ruled property (am-17 §13.2 item 4): the same answer every run."""
import random, sys
from loremaster.tasks import find_row_blocked_by_cycles
rng = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 7)
worlds = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
differ = hits_total = 0
for _ in range(worlds):
    n = rng.randint(4, 9)
    ids = [f"{rng.getrandbits(32):08x}" for _ in range(n)]
    stored = {t: [b for b in ids if b != t and rng.random() < 0.3] for t in ids}
    proposed = {t: [b for b in ids if rng.random() < 0.3] for t in rng.sample(ids, rng.randint(1, n))}
    for aon in (True, False):
        base = find_row_blocked_by_cycles(stored, proposed, set(proposed), all_or_nothing=aon)
        hits_total += len(base)
        for _ in range(4):
            s_items = list(stored.items()); rng.shuffle(s_items)
            p_items = list(proposed.items()); rng.shuffle(p_items)
            s2 = {k: rng.sample(v, len(v)) for k, v in s_items}
            p2 = {k: rng.sample(v, len(v)) for k, v in p_items}
            asked = list(proposed); rng.shuffle(asked)
            if find_row_blocked_by_cycles(s2, p2, asked, all_or_nothing=aon) != base:
                differ += 1
print(f"worlds={worlds} hits={hits_total} order-dependent answers={differ}")
```

### `extra/probe_cycle_predicate_58_built.py` — diff vs committed `scripts/probe_cycle_predicate_58.py` at cdf1ce4
```diff
--- /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58d/ca58d-probes/scripts/probe_cycle_predicate_58.py	2026-11-10 02:30:54.724057961 -0500
+++ /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58d/ca58d-probes-tools/extra/probe_cycle_predicate_58_built.py	2026-11-10 02:35:56.086016578 -0500
@@ -98,13 +98,9 @@
 
 
 def rule_u_built(stored: Columns, proposed: Columns) -> set[str]:
-    """⚠ COLD-AUDIT SEAM (am-17 §13.5 item 4): replace this body with a call to the BUILT persisted-row cycle
-    predicate (am-17 §13.2: ``all_or_nothing=False``, every proposed row asked) returning the hit rows as a set,
-    then run with ``--built``: rule ``U`` must read 0 / 0 and ``NONE`` non-zero. Until then it refuses to run."""
-    raise NotImplementedError(
-        "cold audit: call the built predicate here (stored, proposed, asked=set(proposed), all_or_nothing=False) "
-        "and return set(result)"
-    )
+    """ca58d-probes: the BUILT predicate (cdf1ce4), all_or_nothing=False, every proposed row asked."""
+    from loremaster.tasks import find_row_blocked_by_cycles
+    return set(find_row_blocked_by_cycles(stored, proposed, set(proposed), all_or_nothing=False))
 
 
 #: Which implementation rule ``U`` runs: the in-memory reference (``rule_u``, default) or the built function
@@ -210,6 +206,38 @@
     print(f"supersede worlds: {tried}; exact refuses {refused}; union differs from exact in {differ}")
 
 
+def part_supersede_built_aon(rng: random.Random, worlds: int) -> None:
+    """ca58d-probes: the live supersede against the BUILT predicate with all_or_nothing=True, asked={new}.
+    exact = the successor lies on a cycle of the overlay (rewired columns REPLACE stored)."""
+    from loremaster.tasks import find_row_blocked_by_cycles
+    differ = refused = tried = 0
+    miss_examples = []
+    for _ in range(worlds):
+        n = rng.randint(4, 7)
+        ids = [f"t{i}" for i in range(n)]
+        stored = {t: [b for b in ids if b != t and rng.random() < 0.3] for t in ids}
+        old = rng.choice(ids)
+        deps = [b for b in ids if b != old and rng.random() < 0.3]
+        rewired = {t: ["new" if b == old else b for b in col] for t, col in stored.items() if old in col}
+        tried += 1
+        exact = on_cycle(digraph({**stored, **rewired, "new": deps}), "new")
+        hits = find_row_blocked_by_cycles(stored, {**rewired, "new": deps}, {"new"}, all_or_nothing=True)
+        built = "new" in hits
+        if built:
+            cyc = hits["new"]
+            assert cyc[0] == "new" and cyc[-1] == "new", cyc
+            g = digraph({**stored, **rewired, "new": deps})
+            assert all(g.has_edge(a, b) for a, b in zip(cyc, cyc[1:])), ("cycle not a path of the overlay", cyc)
+        refused += exact
+        if exact != built:
+            differ += 1
+            if len(miss_examples) < 3:
+                miss_examples.append((stored, old, deps, exact, built))
+    print(f"supersede (BUILT, all_or_nothing=True) worlds: {tried}; exact refuses {refused}; built differs from exact in {differ}")
+    for ex in miss_examples:
+        print("  DIFF", ex)
+
+
 if __name__ == "__main__":
     if "--built" in sys.argv:
         sys.argv.remove("--built")
@@ -218,3 +246,4 @@
     seed = int(sys.argv[2]) if len(sys.argv) > 2 else 58
     part_heal(random.Random(seed), count)
     part_supersede(random.Random(seed + 1), count)
+    part_supersede_built_aon(random.Random(seed + 2), count)
```

### `extra/test_ca58d_depth_edge.py`
Identical to `test_ca58d_own_probes.py` with `TestDepthDoor`'s parametrize replaced by `@pytest.mark.parametrize("extra", [-1, 0, 1])`.

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
C=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58d/ca58d-probes; T=$C-tools; wb=$1
sel=$(cat $T/sel.txt); [ "$wb" = WB6 ] && sel="$sel loremaster/tests/test_reanchor_58_r2_rulings.py::TestOnlyACycleThroughXPrimeIsRefused loremaster/tests/test_reanchor_58_r2_probes.py::test_PR8_a_dependent_on_a_legacy_loop_does_not_block_the_supersede"
[ -z "$sel" ] && { echo "REFUSED empty selection"; exit 64; }
[ -s $T/decl/$wb ] || { echo "REFUSED empty declaration"; exit 64; }
exp=(); while IFS= read -r id; do exp+=(--expect-red "$id"); done < $T/decl/$wb
log=$T/logs/d_$wb.log
cd $C
{ ~/.claude/orchestration/tree_id.sh $C; echo "WB=$wb declared=$(wc -l < $T/decl/$wb) decl_md5=$(md5sum $T/decl/$wb | cut -d' ' -f1)";
  uv run python scripts/mutation_proof.py --file loremaster/loremaster/tasks.py --anchor-file $T/mut/$wb.anchor --replacement-file $T/mut/$wb.repl "${exp[@]}" -- \
    systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 uv run pytest -q -p no:cacheprovider -n 8 --timeout=300 --run-parked $sel;
  echo "EXIT=$?"; } > $log 2>&1
grep -E '^EXIT=|[0-9]+ (passed|failed)|PROOF FAILED|RESTORE|restored byte-exact' $log | tail -4
```

### Wrong-build deltas (`mut/WBn.anchor` → `mut/WBn.repl`, applied to `loremaster/loremaster/tasks.py` by `mutation_proof.py`, exactly-once anchors)

#### WB0
```diff
--- anchor
+++ replacement
@@ -1,2 +1,3 @@
     hits: dict[str, list[str]] = {}
+    return hits  # WB0
     for row in sorted(set(asked)):
\ No newline at end of file
```

#### WB1
```diff
--- anchor
+++ replacement
@@ -1 +1 @@
-await self._refuse_a_cycle({new_id: dependencies, **rewired}, minted={new_id})
\ No newline at end of file
+await self._refuse_a_cycle({new_id: dependencies}, minted={new_id})  # WB1
\ No newline at end of file
```

#### WB2
```diff
--- anchor
+++ replacement
@@ -1,5 +1,9 @@
-        built = await self._skip_cycle_closing_rows(built, proposed, superseded_blockers)
-        chunks = self._pack_heal_chunks(built)
+        chunks = self._pack_heal_chunks(built)  # WB2: predicate per chunk, after packing
         healed = 0
         for chunk_index, chunk in enumerate(chunks):
+            chunk = await self._skip_cycle_closing_rows(
+                chunk, {entry[0]: proposed[entry[0]] for entry in chunk}, superseded_blockers
+            )
+            if not chunk:
+                continue
             fragments = [f for entry in chunk for f in entry[1]]
```

#### WB3
```diff
--- anchor
+++ replacement
@@ -1 +1 @@
-cycles = find_row_blocked_by_cycles(stored, proposed, proposed, all_or_nothing=False)
\ No newline at end of file
+cycles = find_row_blocked_by_cycles(stored, proposed, proposed, all_or_nothing=True)  # WB3
\ No newline at end of file
```

#### WB4
```diff
--- anchor
+++ replacement
@@ -1 +1 @@
-            proposed[dependent] = final
+            proposed[dependent] = [b for b in final if b not in columns]  # WB4
```

#### WB5
```diff
--- anchor
+++ replacement
@@ -1,13 +1,13 @@
     graph = networkx.DiGraph()
-    for node, blockers in sorted(stored.items()):
+    for node, blockers in stored.items():  # WB5
         if all_or_nothing and node in proposed:
             continue  # the write REPLACES this row's column, so its stored edges do not exist afterwards
         graph.add_node(node)
-        for blocker in sorted(set(blockers)):
+        for blocker in set(blockers):
             graph.add_edge(node, blocker)
-    for node, blockers in sorted(proposed.items()):
+    for node, blockers in proposed.items():
         graph.add_node(node)
-        for blocker in sorted(set(blockers)):
+        for blocker in set(blockers):
             graph.add_edge(node, blocker)
     component_of: dict[str, frozenset[str]] = {}
     for component in networkx.strongly_connected_components(graph):
@@ -15,8 +15,8 @@
         for member in members:
             component_of[member] = members
     hits: dict[str, list[str]] = {}
-    for row in sorted(set(asked)):
-        for blocker in sorted(set(proposed.get(row, ()))):
+    for row in set(asked):
+        for blocker in set(proposed.get(row, ())):
             if blocker == row or blocker in component_of.get(row, ()):
                 path = [row] if blocker == row else networkx.shortest_path(graph, blocker, row)
                 hits[row] = [row, *(str(node) for node in path)]
```

#### WB6
```diff
--- anchor
+++ replacement
@@ -1 +1 @@
-await self._refuse_a_cycle({new_id: dependencies, **rewired}, minted={new_id})
\ No newline at end of file
+await self._refuse_a_cycle({new_id: dependencies, **rewired}, minted=None)  # WB6
\ No newline at end of file
```

#### WB7
```diff
--- anchor
+++ replacement
@@ -1,2 +1,2 @@
                 hits[row] = [row, *(str(node) for node in path)]
-                break
+                return hits  # WB7
```

### Declared red sets (`decl/`, written before the runs)
```
2026-11-10T07:40:48Z
amended WB0 (+4 create-path pins) 2026-11-10T07:41:19Z, before any wrong-build run
2026-11-10T07:46:30Z
--- WB0
loremaster/tests/test_reanchor_58_fixwave.py::TestTheHealNeverWritesARowOntoACycle::test_A_a_straggler_whose_reanchor_closes_a_cycle_is_skipped_WHOLE_and_recorded_every_boot
loremaster/tests/test_reanchor_58_fixwave.py::TestTheHealNeverWritesARowOntoACycle::test_B_two_stragglers_that_close_a_cycle_JOINTLY_are_both_skipped
loremaster/tests/test_reanchor_58_fixwave.py::TestTheHealNeverWritesARowOntoACycle::test_C_a_straggler_already_on_a_LEGACY_loop_is_skipped_stricter_than_the_live_supersede
loremaster/tests/test_reanchor_58_fixwave.py::TestTheCyclePredicateIsExact::test_E1_the_heal_never_writes_a_cycle_that_shares_an_edge_with_a_legacy_loop[legacy_ids_sort_first]
loremaster/tests/test_reanchor_58_fixwave.py::TestTheCyclePredicateIsExact::test_E1_the_heal_never_writes_a_cycle_that_shares_an_edge_with_a_legacy_loop[control_dependent_sorts_first]
loremaster/tests/test_reanchor_58_fixwave.py::TestTheCyclePredicateIsExact::test_E3_the_live_supersede_refuses_a_cycle_that_shares_an_edge_with_a_legacy_loop[with_legacy_loop]
loremaster/tests/test_reanchor_58_fixwave.py::TestTheCyclePredicateIsExact::test_E3_the_live_supersede_refuses_a_cycle_that_shares_an_edge_with_a_legacy_loop[control_no_legacy_loop]
loremaster/tests/test_reanchor_58_fixwave.py::TestTheHealsFateIsOnePassOverStoredPlusProposed::test_D2_i_both_rows_are_skipped_whatever_the_id_order[old_loop_skips_D1_only]
loremaster/tests/test_reanchor_58_fixwave.py::TestTheHealsFateIsOnePassOverStoredPlusProposed::test_D2_i_both_rows_are_skipped_whatever_the_id_order[old_loop_skips_both]
loremaster/tests/test_reanchor_58_fixwave.py::TestTheHealsFateIsOnePassOverStoredPlusProposed::test_D2_ii_a_row_whose_cycle_runs_through_another_stragglers_STORED_edge_waits_one_boot
loremaster/tests/test_blocks_edge.py::TestTheCyclePolicyHasONEImplementation::test_MUTATION_the_batch_key_detector_answers_ONLY_the_batch_key_question
loremaster/tests/test_supersede_reanchor_58.py::TestACycleClosingRewireIsRefusedWhole::test_refused_as_a_cycle_naming_it_and_NOTHING_changed
loremaster/tests/test_supersede_reanchor_58.py::TestTheBootBackfillAfterAReanchorIsANoOp::test_after_a_REFUSED_supersede_the_backfill_mints_nothing
loremaster/tests/test_ca58d_fw1_probes.py::TestE1HealCycleSharingAnEdgeWithALegacyLoop::test_E1_heal_never_writes_a_cycle_that_shares_an_edge_with_a_legacy_loop[legacy_ids_sort_first]
loremaster/tests/test_ca58d_fw1_probes.py::TestE1HealCycleSharingAnEdgeWithALegacyLoop::test_E1_heal_never_writes_a_cycle_that_shares_an_edge_with_a_legacy_loop[control_dependent_sorts_first]
loremaster/tests/test_ca58d_fw1_probes.py::TestE2JointCycleAcrossAChunkBoundary::test_E2_leg_B_with_one_row_per_chunk
loremaster/tests/test_ca58d_fw1_probes.py::TestE3LiveSupersedeCycleSharingAnEdgeWithALegacyLoop::test_E3_live_supersede_refuses_a_cycle_that_shares_an_edge_with_a_legacy_loop[with_legacy_loop]
loremaster/tests/test_ca58d_fw1_probes.py::TestE3LiveSupersedeCycleSharingAnEdgeWithALegacyLoop::test_E3_live_supersede_refuses_a_cycle_that_shares_an_edge_with_a_legacy_loop[control_no_legacy_loop]
loremaster/tests/test_ca58d_fw1_probes.py::TestE4TwoIndependentCycles::test_E4_two_stragglers_each_closing_their_OWN_cycle_are_both_skipped
loremaster/tests/test_ca58d_own_probes.py::TestS1E1Strengthened::test_S1_E1_world_row_byte_identical_recorded_with_fields_every_boot[legacy_ids_sort_first]
loremaster/tests/test_ca58d_own_probes.py::TestS1E1Strengthened::test_S1_E1_world_row_byte_identical_recorded_with_fields_every_boot[control_dependent_sorts_first]
loremaster/tests/test_ca58d_own_probes.py::TestS2E2Strengthened::test_S2_joint_cycle_one_row_per_chunk_both_unchanged_and_recorded
loremaster/tests/test_ca58d_own_probes.py::TestS3E3Strengthened::test_S3_refused_supersede_writes_NOTHING[with_legacy_loop]
loremaster/tests/test_ca58d_own_probes.py::TestS3E3Strengthened::test_S3_refused_supersede_writes_NOTHING[control_no_legacy_loop]
loremaster/tests/test_ca58d_own_probes.py::TestS4E4Strengthened::test_S4_two_independent_cycles_both_recorded
loremaster/tests/test_blocks_edge.py::TestCreateRefusesToFormACycle::test_a_batch_whose_items_reference_each_others_IDS_is_REFUSED
loremaster/tests/test_blocks_edge.py::TestCreateRefusesToFormACycle::test_a_SELF_blocking_task_is_REFUSED
loremaster/tests/test_blocks_edge.py::TestCreateRefusesToFormACycle::test_a_create_that_would_close_a_cycle_through_PERSISTED_tasks_is_REFUSED
loremaster/tests/test_blocks_edge.py::TestCreateRefusesToFormACycle::test_a_MINTED_cycle_COEXISTING_with_a_LEGACY_cycle_in_the_closure_is_REFUSED
--- WB1
loremaster/tests/test_reanchor_58_fixwave.py::TestTheHealNeverWritesARowOntoACycle::test_A_a_straggler_whose_reanchor_closes_a_cycle_is_skipped_WHOLE_and_recorded_every_boot
loremaster/tests/test_reanchor_58_fixwave.py::TestTheCyclePredicateIsExact::test_E3_the_live_supersede_refuses_a_cycle_that_shares_an_edge_with_a_legacy_loop[with_legacy_loop]
loremaster/tests/test_reanchor_58_fixwave.py::TestTheCyclePredicateIsExact::test_E3_the_live_supersede_refuses_a_cycle_that_shares_an_edge_with_a_legacy_loop[control_no_legacy_loop]
loremaster/tests/test_blocks_edge.py::TestTheCyclePolicyHasONEImplementation::test_MUTATION_the_batch_key_detector_answers_ONLY_the_batch_key_question
loremaster/tests/test_supersede_reanchor_58.py::TestACycleClosingRewireIsRefusedWhole::test_refused_as_a_cycle_naming_it_and_NOTHING_changed
loremaster/tests/test_supersede_reanchor_58.py::TestTheBootBackfillAfterAReanchorIsANoOp::test_after_a_REFUSED_supersede_the_backfill_mints_nothing
loremaster/tests/test_ca58d_fw1_probes.py::TestE3LiveSupersedeCycleSharingAnEdgeWithALegacyLoop::test_E3_live_supersede_refuses_a_cycle_that_shares_an_edge_with_a_legacy_loop[with_legacy_loop]
loremaster/tests/test_ca58d_fw1_probes.py::TestE3LiveSupersedeCycleSharingAnEdgeWithALegacyLoop::test_E3_live_supersede_refuses_a_cycle_that_shares_an_edge_with_a_legacy_loop[control_no_legacy_loop]
loremaster/tests/test_ca58d_own_probes.py::TestS3E3Strengthened::test_S3_refused_supersede_writes_NOTHING[with_legacy_loop]
loremaster/tests/test_ca58d_own_probes.py::TestS3E3Strengthened::test_S3_refused_supersede_writes_NOTHING[control_no_legacy_loop]
--- WB2
loremaster/tests/test_ca58d_fw1_probes.py::TestE2JointCycleAcrossAChunkBoundary::test_E2_leg_B_with_one_row_per_chunk
loremaster/tests/test_ca58d_own_probes.py::TestS2E2Strengthened::test_S2_joint_cycle_one_row_per_chunk_both_unchanged_and_recorded
--- WB3
loremaster/tests/test_reanchor_58_fixwave.py::TestTheHealsFateIsOnePassOverStoredPlusProposed::test_D2_ii_a_row_whose_cycle_runs_through_another_stragglers_STORED_edge_waits_one_boot
--- WB4
loremaster/tests/test_reanchor_58_fixwave.py::TestTheHealNeverWritesARowOntoACycle::test_C_a_straggler_already_on_a_LEGACY_loop_is_skipped_stricter_than_the_live_supersede
--- WB5
loremaster/tests/test_supersede_reanchor_58.py::TestACycleClosingRewireIsRefusedWhole::test_refused_as_a_cycle_naming_it_and_NOTHING_changed
--- WB5b
loremaster/tests/test_ca58d_determinism.py::test_the_cycle_answer_is_identical_across_hash_seeds
--- WB6
loremaster/tests/test_reanchor_58_r2_rulings.py::TestOnlyACycleThroughXPrimeIsRefused::test_the_legacy_loop_is_untouched_and_Y_follows_the_work
loremaster/tests/test_reanchor_58_r2_probes.py::test_PR8_a_dependent_on_a_legacy_loop_does_not_block_the_supersede
--- WB7
loremaster/tests/test_reanchor_58_fixwave.py::TestTheHealNeverWritesARowOntoACycle::test_B_two_stragglers_that_close_a_cycle_JOINTLY_are_both_skipped
loremaster/tests/test_reanchor_58_fixwave.py::TestTheHealsFateIsOnePassOverStoredPlusProposed::test_D2_i_both_rows_are_skipped_whatever_the_id_order[old_loop_skips_D1_only]
loremaster/tests/test_reanchor_58_fixwave.py::TestTheHealsFateIsOnePassOverStoredPlusProposed::test_D2_i_both_rows_are_skipped_whatever_the_id_order[old_loop_skips_both]
loremaster/tests/test_ca58d_fw1_probes.py::TestE4TwoIndependentCycles::test_E4_two_stragglers_each_closing_their_OWN_cycle_are_both_skipped
loremaster/tests/test_ca58d_own_probes.py::TestS2E2Strengthened::test_S2_joint_cycle_one_row_per_chunk_both_unchanged_and_recorded
loremaster/tests/test_ca58d_own_probes.py::TestS4E4Strengthened::test_S4_two_independent_cycles_both_recorded
```

### Control delta for F-A (applied by hand with a cp -a backup, md5 verified restored)
```diff
-        stored = await self._bounded_dependency_graph(seeds)
+        stored = {}  # CONTROL: heal closure read removed
```

Verbatim copies of other agents' instruments run unchanged: `test_adv_fw1_probes.py` (REPORT-adversary-58-fw1.md §INSTRUMENTS), `test_adv_r53_probes.py` (REPORT-adversary-58-r53.md §INSTRUMENTS), `probe_verify1.py` (`scratchpad/ca58/verify1-notes/`).
