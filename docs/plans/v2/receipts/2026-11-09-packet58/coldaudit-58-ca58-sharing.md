# coldaudit-58-ca58-sharing — packet 58 cold audit, dimension: the COLD-AUDIT SET + the sharing mutations

## SUMMARY BLOCK
- brief-base v27 read · brief project v7 read · landmines recalled (k=50 returned 10, not cut off)
- State: **done**. Verdict: **GO for this dimension.** All 5 COLD-AUDIT SET items run on `aa4ea04`. Both sharing mutations PROVE sharing: BC-r5-1 by an independent-oracle probe plus its private-copy positive control, BC-r5-2 PROOF HELD. All 7 re-anchored W-* builds die on the BUILT tree. The #130 shell bypass is caught by 2 behaviour pins (and 2 source scanners). No product defect found.
- Deviations: (1) test runs were inline: this agent has no `Agent` tool (brief-base §3). (2) M1's declared set missed one red (PR14, which hard-codes per=3), so `mutation_proof` reports PROOF FAILED, exit 4, on the unexpected-red direction. All 10 declared reds fired; see §M1. (3) The real-population receipt also ran on the newer 2026-11-08 export, beside the am-2-named 2026-08-03 dump.
- Packages considered: none — no mechanism specified (probes only)
- Odoo-20 portability: n/a — no Odoo seam touched
- Reuse ledger: none (no production symbols; scratch probes are pasted in §INSTRUMENTS)
- Graded: aa4ea04 · HEAD-at-report: 54004dd · DIFFERENT (4 behind). The 4 commits touch only `docs/` and the parked-contracts tests. None touches tasks.py, _txn.py, surreal.py, forgery_door_sweep.py or the 58 tests (`git diff --stat aa4ea04 54004dd -- <those>` is empty).
- Findings: F-1 minor: the `max_reanchor_dependents` docstring names a probe that does not produce its numbers (lore #622). F-2 minor: am-15 §1.3 and am-17 §4/§3 carry the stale "116 tasks" production count; the 2026-11-08 export holds 234. Residuals: R-r53-1 CONFIRMED real (residual). R-r53-2 discharged for a 2nd label. PR14's literal per (residual).
- Decisions needed: none.
- Pointers: §PROVENANCE · §BASELINE · §M1 · §M2 · §ITEM-4 · §ITEM-5 · §ITEM-1 (W-*) · §R-r53-1 · §R-r53-2 · §130 · §INSTRUMENTS. Logs: `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58/logs/`.

## ROUTING TABLE (written before the first sweep, 2026-11-09)
| step | tier | who |
|---|---|---|
| scratch copy + provenance receipt | 1 | inline (one scripted command, output read whole) |
| locate callers/pins of `_txn.fragment_rows`, `_log_transaction_size` (scratch copy, unindexed: grep) | 1 | inline — small parallel batch, read whole |
| declare expected-RED sets for each mutation | 3 | me (a mutation-proof verdict; never Haiku) |
| mutation runs via `scripts/mutation_proof.py` | 1 | **inline: this agent has no `Agent` tool** (brief-base §3: "with no `Agent` tool … run inline. Say which") |
| verdicts, residual measurement, #130 wrong build | 3 | me |

## §PROVENANCE (measured 2026-11-10)
- Copy: `scripts/scratch_copy.sh …/scratchpad/ca58/ca58-sharing` → EXIT=0. Then `git checkout aa4ea04 -- .` (this dropped the other session's dirty `scripts/test_*.py`). `rev-parse HEAD` = `aa4ea0426e53dadd0e905f83092d764b350e4d46`. Status: the 4 untracked REPORT files only. After my probe file was added, a 5th.
- `loremaster.__file__` = `…/scratchpad/ca58/ca58-sharing/loremaster/loremaster/__init__.py`; `_txn.__file__` is inside the copy.
- TREE ids: `40f080f6…` = the pristine copy. `146f518f…` = the copy plus my untracked probe `loremaster/tests/test_probe_sharing_ca58.py`: baseline, M1, M2, R1, R2 and #130 ran on it. `f28d4c4d…` = the same plus the inert W-* switches: P0 and W-*. `b56cc5a0…` = the W-PRIV positive control. After every run, `git diff` is empty and every mutated file was restored byte-exact (md5 before = after, in `<run>.md5_before/after`).
- Store: TEST only (`ws://127.0.0.1:18000`, harness `DEFAULT_URL`; restore_prod_dump's constant `STORE_PORT=18000`). All three minted dump DBs were reaped (`--reap`: "absent from INFO FOR NS").
- Every pytest ran under `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0`, with `-n 8` and `--timeout=300`. No empty selection: `run_mut.sh` refuses with exit 8 when a scope or declared set is empty.

## §BASELINE — the unmutated scope (366 collected: probe 3 + the 18 `test_*58*.py` + `test_exhaustion_fates.py` + `test_sdk3_row_bound.py` + 3 `test_surreal_apply.py` classes)
- `logs/baseline.log` · TREE `146f518f…` · `2 failed, 364 passed` · EXIT=1. The 2 reds are the known 64b-i `findings.py::_run_guarded` bound (r3_cas_seam, r4_state); they are deselected in every mutation run (`logs/baseline_reds.txt`). The probe's 3 legs are GREEN here, which is the unmutated half of its control.

## §M1 — BC-r5-1: mutate `_txn.fragment_rows` (double the un-annotated count)
- Mutation: `sum(len(fragment.statements) if …` → `sum(2 * len(fragment.statements) if …` (anchor matched once).
- **Why the 58 suite alone cannot prove it (am-15 §2 F-RB-2, confirmed by reading).** 58's own pricing pins derive their oracle through `composed_rows`, which is `_txn.fragment_rows`, via `ComposeSpy`, `_derive` and `measure_heal_shape`. Under M1 the code and the oracle move together, and those pins stay GREEN by design. So the proof needs an INDEPENDENT oracle: `test_probe_sharing_ca58.py` (§INSTRUMENTS) pins hand-derived literals. Accessor (0)=16 665, (2)=16 664. Heal row cost 4: 2 500 stragglers make 1 chunk, 2 501 make 2. compose accepts 25 001 un-annotated statements.
- Declared BEFORE the run (`logs/m1_declared.txt`, 10 ids, derived by reading, ids from `--collect-only`): the 3 probe legs; the 3 un-annotated riders (`annotated_calls`: r5_rows, L2 `test_REAL_CAP_a_supersede_past…`, L3 `test_L3_REAL_CAP…`); sdk3 `test_single_row_statements_count_one_row_each_against_the_cap` and `…stay_quiet` (the WARN in `apply` is a fourth consumer); and surreal_apply `test_compose_raises…over_the_hard_cap` and `test_compose_accepts_exactly_at_the_hard_cap`.
- Run: `logs/m1.log` · `11 failed, 353 passed` · EXIT=4 · restored byte-exact (`_txn.py` md5 `1b8fa479…`). All 10 declared ids went RED. One red was NOT declared: `test_reanchor_58_r2_probes.py::test_PR14_the_accessor_follows_the_shared_hard_cap` (`assert 781 == (831 - 100)`). It hard-codes per=3 (`TXN_ROW_HARD_CAP - 300` → `baseline - 100`). That is my declaration miss, and the red is still a right-reason "the accessor moved" signal.
- What moved (probe failure text): the accessor `(8331, 8331) != (16665, 16664)`; the heal row cost `[8] != [4]`, so the packer's chunk boundary moved; compose refused `50002 rows, over the 50000-row cap`. **All three consumers move with the shared counter. Sharing is PROVEN.** (HIGH)
- **Positive control (W-PRIV + M1), run because a probe needs a control.** The accessor's `_supersede_rows` gets a private `sum(len(statements))` counter, then M1 is applied. Declared: the packer and compose legs RED, the accessor leg GREEN. `logs/wpriv_m1.log` · `2 failed, 1 passed` · **PROOF HELD** · EXIT=0. tasks.py was restored from the `cp -a` copy byte-exact. So the probe does see a private copy stay put.

## §M2 — BC-r5-2: mutate the house warn comparison
- Mutation (`SurrealStore._log_transaction_size`): `if row_count > _txn.TXN_ROW_WARN_THRESHOLD:` → `if row_count > 3 * _txn.TXN_ROW_WARN_THRESHOLD:`.
- Declared BEFORE the run (`logs/m2_declared.txt`, 4 ids): `test_crossing_the_WARN_threshold_logs_ONE_warning_and_SUCCEEDS` (803 rows vs 800 → no warn) · `test_sdk3_row_bound::…test_rows_over_the_threshold_in_two_statements_warn` (20 < 21) · `test_PR13_CONTROL_the_house_policy_DOES_warn_at_that_size` (905 < 2 400) · `test_surreal_apply::…test_apply_warns_above_the_row_threshold`.
- Run: `logs/m2.log` · `4 failed, 360 passed` · **PROOF HELD** (exact both ways) · EXIT=0 · restored (`surreal.py` md5 `bb0f368b…`). The task ledger's WARN has no private comparison: it reddens with the house function. (HIGH)

## §ITEM-4 — `max_reanchor_dependents`'s docstring (BC-r5-3 as corrected by am-17 §4), read at aa4ea04
- It states the bound, corrected per am-17 §4: 3 332 commit in 10.2 s; 6 000 time out at 30 s; the 30 s line is interpolated near 5 700; the band runs from ~5 700 to the cap of 16 665, where a supersede times out loud and commits nothing. It also states the date (2026-11-09), the schema and engine, the trigger (`store.apply.large_transaction` from the task ledger) and a probe path. Present: YES.
- **F-1 (minor, HIGH, lore #622): the named probe does not produce the stated numbers.** The docstring says `Probe: scripts/probe_hub_txn_58.py`. That file is am-15 §1.3's SCHEMALESS raw-statement lower-bound probe: its own docstring says "task here is SCHEMALESS … LOWER bound", and it contains no `supersede_task` call. It measured 3 332 dependents at 3.44 s. The docstring's 10.2 s / 6 000 numbers are am-17 §1.4's, produced by `scripts/probe_heal_curve_58.py` part C (`C_SIZES = (1665, 3332, 6000)`, "a real `supersede_task` … under the served 30 s timeout"). A reader who re-runs the cited probe gets numbers about 3× lower than the docstring states. Secondary: am-17 §4's rider asks for "§1.4's three rows"; the docstring carries two (1 665 / 2.82 s is omitted). Fix: one docstring line (name part C).

## §ITEM-5 — the am-2 real-population heal receipt + the largest hub
- Instrument: `scripts/restore_prod_dump.py --dump <dump> --tables task` (TEST store constant), then `realpop_heal_ca58.py` (§INSTRUMENTS). The second script boots TWICE through the built `TaskLedger.ensure_ready()` and captures every `task.backfill.*` record.
| dump | tasks | superseded | stragglers (pre) | boot 1 | boot 2 | largest hub (blocked_by column / `blocks` edges per `in`) |
|---|---|---|---|---|---|---|
| 2026-08-03 (am-2's) · `logs/realpop_0803_b.log` | 116 | 7 | 1 | `blocks_edges_minted minted=51`; `stragglers_reanchored count=1 chunks=1` | silent | **4** / **4** |
| 2026-11-08 (newest) · `logs/realpop_1108.log` | 234 | 11 | 1 | `minted=61`; `count=1 chunks=1` | silent | **4** / **4** |
- No WARNING record in either boot (no phantom, cycle or chunk-rejected event). The largest real hub (4 dependents) sits about 1 400× below the ~5 700 timeout band and the 16 665 cap. The heal is one chunk of 4 rows against the 10 000 bound. (HIGH)
- My first PRE count (`logs/realpop_0803.log`) read stragglers=0 with spurious phantoms. That was MY parser's defect: ids beginning with a digit render as `task:⟨…⟩`. I fixed the parser, restored a fresh DB and re-ran; the boot records were identical in both runs.
- **F-2 (minor, design-doc prose, HIGH):** am-15 §1.3 ("Production holds 116 task rows (am-2)"), am-17 §3 ("production holds 116 tasks") and am-17 §4 ("a population 29× production's whole task table") inherit a count that the 2026-11-08 export puts at **234** (so ~14×, not 29×). No ruling changes: the hub/population ratio stays enormous.

## §ITEM-1 — the adversary's seven re-anchored W-* builds, replayed on the BUILT tree
- Instrument: the adversary's `adv58r5b/wstar_patch.py` (md5 `2559ef36…` = the copy pasted in REPORT-adversary-58-r5-2 §INSTRUMENTS). Every anchor matched exactly once on aa4ea04. It installs INERT env switches; each W-* was then turned on by a one-line `mutation_proof` edit of its own switch line (`ws/<W>.anchor/.repl`).
- P0 control (switches inert, built behaviour), 54 collected minus 2 baseline deselects: `logs/ws_p0.log` · `52 passed` · EXIT=0. The r4 heal leg now passes in seconds (am-16 §3's shrink landed), so R-8's slowness is gone on the built tree.
| W-* | declared (from `--collect-only`, before the run) | log | result |
|---|---|---|---|
| W-TUPLE | r4 `[findings.py::resolve -> findings.py::_transition]` | `ws_W-TUPLE.log` | 1 failed, 51 passed · PROOF HELD |
| W-IMPLICIT | same id | `ws_W-IMPLICIT.log` | 1 failed, 51 passed · PROOF HELD |
| W-REBIND | r4 `[findings.py::wontfix -> findings.py::_transition]` | `ws_W-REBIND.log` | 1 failed, 51 passed · PROOF HELD |
| W-F3-ROOT | r3_probes `test_PB_an_8_way_claim_race_raises_no_alarm_from_ANY_lore_logger` | `ws_W-F3-ROOT.log` | 1 failed, 51 passed · PROOF HELD |
| W-HEAL2 | r4 `[tasks.py::ensure_ready -> tasks.py::_reanchor_stragglers]` | `ws_W-HEAL2.log` | 1 failed, 51 passed · PROOF HELD |
| W-F4-PREFIX | convergence `test_the_row_is_the_unit` × {bad_among_two_healable: bad-middle, bad-last; bad_plus_healable: bad-middle} × {phantom, cyclic} | `ws_W-F4-PREFIX.log` | 6 failed, 46 passed · PROOF HELD |
| W-NOOP-DRIVERS (test-tree build; `wstar_noop.py` absent, reconstructed: each `CAS_SEAM_DRIVERS` value → an async no-op) | r4 `[agents.py::register …]`, `[keeps.py::get_or_create_keyed …]`, `[floor_calibration/store.py::record_measurement …]` | `ws_W-NOOP.log` | 3 failed, 49 passed · PROOF HELD |
- All 7 die on the built tree, exact both ways. Afterwards the tree was restored from `wstar-backup/` (`git diff` empty, TREE back to `146f518f…`).

## §R-r53-1 — the count-free SWALLOWS control (adversary-58-r5-2 §Residuals): CONFIRMED real · severity residual
- Unmutated measurement (`r1_silent_set.py`): the swallowing-backfill sweep reports doors `[(1 execute_transaction LOUD), (2 execute_read_transaction silent), (3 run_query silent), (4 execute_transaction silent), (5 run_query LOUD)]`, so silent = **[2, 3, 4]**.
- ONE mutation, on the instrument: `DoorSweepReport.silent_doors` truncated to its first element (`[:1]`, "a contiguous run that ends early"). Declared RED: `test_a_ledger_that_SWALLOWS_its_backfill_failure_is_CAUGHT` (the claim that it pins EVERY backfill door silent). `logs/r1.log`: `2 passed` · **PROOF FAILED: the declared red STAYED GREEN** · EXIT=4 · restored (md5 `d7281faf…`). Landing evidence: the same truncation in-process makes the sweep return `silent [2]` (`r1_silent_set_mut.py`). k=2 is the mirror-state read, so "THE ONE THAT MATTERS" still holds.
- Reading: an under-reporting sweep (it names 1 of 3 silent doors) passes the instrument's own positive control. No product door is reached: `all_doors_loud` and the legacy FAILS_LOUD reach check are unaffected, because any silent door still flips the verdict. NO ROUND stands, and I report it at severity residual. (HIGH)

## §R-r53-2 — W-MARKER-LEAK mutated one label: run on a SECOND label · DISCHARGED for 2 of 4
- Mutation: `_ERROR_CLASS_CAS_LOST = "cas lost — …"` → `"cas_lost: cas lost — …"`. Declared: the leak leg's `[TxnCasLostError-transaction]` and `[TxnCasLostError-query]`. `logs/r2.log`: `2 failed, 14 passed` · **PROOF HELD** · EXIT=0 · restored. With the adversary's TxnHealChunkError run, 2 of the 4 labels are now mutation-proven. Claim and straggler remain proven only by the shared parametrisation over `fifty_eight_thrown_markers()`. (HIGH for the two run; MEDIUM by parametrisation for the other two)

## §130 — one wrong build that bypasses the guarded-append shell for ONE task verb
- W130-T: `_transition_fragment` returns a hand-rolled, byte-equivalent private copy (the same guarded UPDATE, the `updated_at` stamp, the event append, `IF array::len … THROW`) instead of calling `TaskLedger._guarded_append_fragment`. Its behaviour is identical, so only the sharing pins can see it.
- Scope: `test_task_guarded_shell_58.py` + `test_task_ledger.py` + r4 `TestTheFiredLedgerEqualsTheDerivedDomain` (284 collected, 1 baseline deselect). Declared: 4 ids. `logs/w130.log`: `4 failed, 279 passed` · **PROOF HELD** · EXIT=0 · restored.
- **What catches it:** two BEHAVIOUR pins, `TestSharingIsProvenByMutationALWAYSTHROW::test_TRANSITION_routes_through_the_shell` (the shell perturbation does not move transition) and `TestSharingIsProvenByMutationTHEAPPEND::test_transition_stamp_claim_and_reanchor_events_all_come_from_the_shell` (the event is not marked). Two SOURCE SCANNERS also fire: `TestEachLedgerModuleHasExactlyONEGuardedAppendProducer::test_every_guarded_append_ledger_has_ONE_producer` and `::test_the_task_ledgers_one_producer_IS_the_shell`. Note: the scanners are not among the four checks the operator's 2026-11-09 decision 6 keeps. When Phase 4 cuts them, the two behaviour pins still kill this class on their own. No `test_task_ledger.py` behaviour test reddens, as expected for a behaviour-identical copy.

## §RESIDUALS (each NO ROUND unless the lead rules otherwise)
- R-r53-1: confirmed real (above).
- PR14 (`test_PR14_the_accessor_follows_the_shared_hard_cap`) hard-codes per=3 (`- 300` → `- 100`), while its comment says "by per·d". A legitimate per-dependent statement change reddens it for a fixture reason. Test hygiene.
- Builder gate receipts were not verified by this dimension. Observed in passing: `REPORT-builder-58-1.md` §Gate receipts carries `TREE=18b4d3ef…376a25`, and aa4ea04's pristine copy hashes `40f080f6…`. 83359e9 and aa4ea04 landed after that build run. This is for the receipts dimension, not adjudicated here.

## §INSTRUMENTS (pasted verbatim; scratch root `…/scratchpad/ca58/`)

### `ca58-sharing/loremaster/tests/test_probe_sharing_ca58.py` (md5 `289ad2060d9b…`)
```
"""ca58-sharing cold-audit probe (packet 58, am-15 §2 rider): do the three consumers of ``_txn.fragment_rows``
MOVE when its body changes?

Each leg pins the UNMUTATED value as a hand-derived LITERAL (an oracle independent of ``fragment_rows``), so a
source mutation of ``fragment_rows`` (doubling the un-annotated count) must red all three legs if, and only if,
each consumer prices through the shared counter. A consumer with a private counter stays put and its leg stays
GREEN under the mutation — that is the private-copy signal am-15 §2 names. No store, no network.

Hand derivation at aa4ea04 (one row per un-annotated statement):
* supersede: fixed(K=0) = 5 rows, per dependent = 3 rows -> (50_000 - 5) // 3 = 16_665; K=2: fixed 7 -> 16_664.
* heal: one straggler of one superseded blocker = 4 rows; packer bound min(10_000, 50_000) = 10_000 ->
  2_500 stragglers fit ONE chunk, 2_501 need two.
* compose: 25_001 un-annotated single statements = 25_001 rows < 50_000 -> composes.
"""

from __future__ import annotations

from loremaster.store import _txn
from loremaster.store._txn import TxnFragment, compose
from loremaster.tasks import TaskLedger

_AT = "2026-11-09T00:00:00+00:00"


def _offline_ledger() -> TaskLedger:
    """A TaskLedger with no connection: the pricing paths under test are pure."""
    ledger = TaskLedger.__new__(TaskLedger)
    ledger._database = "ca58-probe"  # noqa: SLF001 - only read by skip-path log extras
    return ledger


def _built(ledger: TaskLedger, stragglers: int) -> list:  # type: ignore[type-arg]
    rows = [{"id": f"d{index}", "blocked_by": ["o0"]} for index in range(stragglers)]
    return ledger._plan_heal_rows(rows, {"o0": "n0"}, {"o0": ("n0", False)}, {"n0"}, _AT)  # noqa: SLF001


def test_probe_accessor_prices_through_the_shared_counter() -> None:
    ledger = _offline_ledger()
    assert _txn.TXN_ROW_HARD_CAP == 50_000
    assert (ledger.max_reanchor_dependents(0), ledger.max_reanchor_dependents(2)) == (16_665, 16_664)


def test_probe_packer_chunk_boundary_prices_through_the_shared_counter() -> None:
    ledger = _offline_ledger()
    assert (_txn.TXN_ROW_WARN_THRESHOLD, _txn.TXN_ROW_HARD_CAP) == (10_000, 50_000)
    assert [entry[3] for entry in _built(ledger, 1)] == [4]
    assert len(ledger._pack_heal_chunks(_built(ledger, 2_500))) == 1  # noqa: SLF001
    assert len(ledger._pack_heal_chunks(_built(ledger, 2_501))) == 2  # noqa: SLF001


def test_probe_compose_refusal_prices_through_the_shared_counter() -> None:
    count = 25_001
    fragment = TxnFragment(
        statements=[f"UPDATE probe:{index} SET n = $ca_p{index}" for index in range(count)],
        params={f"ca_p{index}": index for index in range(count)},
    )
    _text, params = compose(fragment)
    assert len(params) == count

```

### `run_mut.sh` (md5 `8fec3f6dcdf8…`)
```
#!/usr/bin/env bash
# run_mut.sh <name> <file> <anchor-file> <replacement-file> <declared-file> [scope-file]
# One mutation proof over the audit scope, baseline reds deselected, expected reds declared from a file.
C=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58/ca58-sharing
L=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58/logs
name=$1; file=$2; anchor=$3; repl=$4; declared=$5; scope=${6:-$L/scope.txt}
cd "$C" || exit 9
read -r -a S < "$scope"
DES=(); while IFS= read -r id; do [ -n "$id" ] && DES+=(--deselect "$id"); done < "$L/baseline_reds.txt"
EXP=(); while IFS= read -r id; do [ -n "$id" ] && EXP+=(--expect-red "$id"); done < "$declared"
[ ${#S[@]} -gt 0 ] && [ ${#EXP[@]} -gt 0 ] || { echo "EMPTY selection/declared"; exit 8; }
md5sum "$file" > "$L/$name.md5_before"
{ ~/.claude/orchestration/tree_id.sh "$C"; echo "DECLARED(${#EXP[@]}/2):"; cat "$declared";
  systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python scripts/mutation_proof.py \
    --file "$file" --anchor-file "$anchor" --replacement-file "$repl" "${EXP[@]}" -- \
    uv run pytest "${S[@]}" "${DES[@]}" -q -n 8 -p no:cacheprovider --timeout=300 -rfE; echo EXIT=$?; } > "$L/$name.log" 2>&1
md5sum "$file" > "$L/$name.md5_after"; cmp -s "$L/$name.md5_before" "$L/$name.md5_after" && echo RESTORED_BYTE_EXACT || echo RESTORE_MISMATCH
tail -25 "$L/$name.log" | cut -c1-260

```

### `realpop_heal_ca58.py` (md5 `a9c80a1e45e4…`)
```
"""ca58-sharing: the am-2 real-population heal receipt + the largest hub (COLD-AUDIT SET item 5).

Run from the scratch copy's root:  uv run python <this file> <database-name-from-restore_prod_dump>
TEST store only (the URL is the harness constant ws://127.0.0.1:18000/rpc, namespace lore_test).
Prints: pre-boot population facts, every task.backfill.* record from TWO boots (count/chunks), and the
largest hub before (blocked_by column) and after (blocks edges per `in`).
"""

from __future__ import annotations

import asyncio
import logging
import sys
from collections import Counter

sys.path.insert(0, "loremaster/tests")
from _surreal_harness import DEFAULT_URL, TEST_NAMESPACE, surreal_password, surreal_user  # noqa: E402
from loremaster.tasks import TaskLedger  # noqa: E402


class _Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _ledger(database: str) -> TaskLedger:
    return TaskLedger(
        url=DEFAULT_URL, namespace=TEST_NAMESPACE, database=database,
        user=surreal_user(), password=surreal_password(),
    )


def _key(value: object) -> str:
    """A task id without its table prefix or the engine's ⟨⟩ quoting (ids that start with a digit)."""
    return str(value).split(":", 1)[-1].strip("⟨⟩`")


async def _rows(ledger: TaskLedger, statement: str) -> list[dict]:
    result = await ledger._query(statement, {})  # noqa: SLF001
    return list(result or [])


async def main(database: str) -> None:
    assert DEFAULT_URL.endswith(":18000/rpc"), DEFAULT_URL
    capture = _Capture()
    logging.getLogger("loremaster").addHandler(capture)
    logging.getLogger("loremaster").setLevel(logging.DEBUG)
    ledger = _ledger(database)
    tasks = await _rows(ledger, "SELECT id, blocked_by, superseded_by, status FROM task")
    ids = {_key(t["id"]) for t in tasks}
    superseded = {_key(t["id"]) for t in tasks if t.get("superseded_by") is not None}
    naming = Counter(_key(b) for t in tasks for b in (t.get("blocked_by") or ()))
    stragglers = [t for t in tasks if any(_key(b) in superseded for b in (t.get("blocked_by") or ()))]
    print(f"PRE tasks={len(tasks)} superseded={len(superseded)} rows_with_blocked_by="
          f"{sum(1 for t in tasks if t.get('blocked_by'))} stragglers={len(stragglers)} "
          f"phantom_blockers={sorted(set(naming) - ids)}")
    print(f"PRE largest hub by blocked_by column: {naming.most_common(3)}")
    for boot in (1, 2):
        capture.records.clear()
        booted = _ledger(database)
        try:
            await booted.ensure_ready()
        finally:
            await booted.close()
        for record in capture.records:
            message = record.getMessage()
            if message.startswith("task.backfill") or record.levelno >= logging.WARNING:
                extra = {k: v for k, v in vars(record).items() if k in ("count", "chunks", "minted", "rows", "database", "task_id", "blocker_id")}
                print(f"BOOT{boot} {record.levelname} {message} {extra}")
        print(f"BOOT{boot} done ({len(capture.records)} records)")
    edges = await _rows(ledger, "SELECT in, count() AS n FROM blocks GROUP BY in")
    print(f"POST blocks edges total={sum(e['n'] for e in edges)} largest hub by edges per in="
          f"{sorted(((e['n'], _key(e['in'])) for e in edges), reverse=True)[:3]}")
    await ledger.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))

```

### `r1_silent_set.py` (md5 `82c88580770f…`)
```
"""ca58: print the SWALLOWS control's silent door set (k, seam) on the unmutated sweep."""
import asyncio, sys
sys.path[:0] = ["scripts", "loremaster/tests"]
import forgery_door_sweep as fds
from loremaster.tasks import TaskLedger
original = TaskLedger._backfill_blocks_edges
async def _swallowing_backfill(ledger):
    try:
        await original(ledger)
    except Exception:
        return
TaskLedger._backfill_blocks_edges = _swallowing_backfill
report = asyncio.run(fds.sweep_doors(fds.legacy_task_store, entry_point="ensure_ready", world="a legacy store", observable="edges"))
print("control_calls", report.control_calls)
print("doors", [(d.k, d.seam_called, d.loud) for d in report.doors])
print("silent", [d.k for d in report.silent_doors])

```

### `w130/repl` (md5 `a2fed4efb8ad…`)
```
        # W130-T (ca58-sharing wrong build): transition BYPASSES the shell with a byte-equivalent private copy.
        merged: dict[str, Any] = {**params, "trg_id": task_id, "trg_ev": dict(event)}
        sets = [*set_parts, f"{_COL_UPDATED_AT} = time::now()", f"{_COL_PROVENANCE}.{_PROV_EVENTS} += [$trg_ev]"]
        update = (
            f"UPDATE type::record('{TASK_TABLE}', $trg_id) SET {', '.join(sets)} "
            f"WHERE ({_COL_STATUS} = ${_TRANSITION_EXPECTED_FROM_PARAM}) AND ({_COL_SUPERSEDED_BY} IS NONE)"
        )
        return TxnFragment(
            statements=[
                f"LET $trg_upd = ({update})",
                f"IF array::len($trg_upd) == 0 {{ THROW '{_TRANSITION_ALREADY_MESSAGE}' }}",
            ],
            params=merged,
        )
```
