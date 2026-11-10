brief-base v27 read · brief project v7 read

# coldaudit-58-ca58-probes — packet 58 cold audit, dimension: adversary probes P1–P3 + own wrong builds on the BUILT tree

## SUMMARY BLOCK
- State: done-with-deviations. **Verdict (measured 2026-11-10 at `aa4ea04`): (a), (b), (c) CONFIRMED by read AND by
  construction; P1, P2, P3 GREEN on the built tree, and each re-shown RED on the adversary's matching wrong build
  re-spelled for the built text (C10→P1, C14b→P2, C9→P3, all PROOF HELD). 7 own wrong builds; NONE survives both the
  contract and my probes. ONE (OB3) survives the contract and dies only by my probe Q4 → finding F1 (missing pin; built
  tree correct).** Plus one false-prose finding (F2) and three residuals.
- Deviations: (1) no `Agent` tool → every run inline (no haiku-runner). (2) Added `test_reanchor_58_r3_convergence.py`
  to the brief's 3-file selection because the F10 over-weight leg (the store-unchanged pin) lives there; without it OB1
  would "survive" for a scope reason (R-1). (3) One own probe (Q2) went red on the first baseline run for MY arithmetic
  (I assumed 4k+1; the shared-head weight is 3k+1); fixed the count to 266, re-run green. (4) OB7 ran on its own
  5-file selection (adds `test_reanchor_58_r3_tiers.py`, where the R1 trigger lives).
- Packages considered: `more_itertools.constrained_batches` 11.1.0 (installed source read in the copy: `strict=True`
  raises `ValueError` on the FIRST item over `max_size`, lazily) — keep; the built packer materialises the list inside
  its `try`, so no chunk is applied before the refusal (proven by construction: packer_worlds, Q1, OB1).
- Odoo-20 portability: n/a — no Odoo seam touched.
- Reuse ledger: none (no production symbols; scratch probes only).
- Graded: aa4ea04 · HEAD-at-report: 38e541c · DIFFERENT (3 ahead: 96ea7f5, 48d5288, 38e541c — docs only, `git diff
  --stat aa4ea04 38e541c` = 2 docs files; no symbol this verdict rests on moved).
- Decisions needed: (D1) F1 — add a supersede leg with a drift edge (Q4's shape) or record the bound; (D2) F2 — reword
  `StragglerHealPackerError`'s message/docstring (an implementer edit); (D3) R-2 — should `_txn.compose` refuse a
  statement naming a `$param` no fragment defines (today it silently evaluates NONE; OB7 shows the R1 guard then
  no-ops)? Each is the lead's/operator's routing call.
- `loremaster.__file__` = `<copy>/loremaster/loremaster/__init__.py` (copy = `…/scratchpad/ca58/ca58-probes`), in
  every log header. Copy HEAD = aa4ea04, `git status` = only untracked REPORT files + my 2 probe files; `tasks.py`
  md5 `cb9b15f7…` = `git show aa4ea04:loremaster/loremaster/tasks.py`, restored byte-exact after every mutation.
- Pointers: §CONFIRMATIONS · §WRONG BUILDS · §FINDINGS · §RESIDUALS · §RUNS · §INSTRUMENTS.

## CAPABILITY CHECK
- Demanded: test runs via `haiku-runner` (brief-base §3). Have: no `Agent` tool in this workflow worker. Did: inline,
  under the cgroup cap, every log read by me. Lead must change: nothing for this run.

## ROUTING TABLE (written before the first sweep or run, 2026-11-09)
| step | tier | who | reason |
|---|---|---|---|
| read am-17 §0/§2/§3/§5/§9/§10/§11, adversary r53 §P1/§MISSING PINS/§LEAD'S QUESTION/§INSTRUMENTS | 3 | self | the audit rests on them |
| read `tasks.py` at aa4ea04 (packer, heal plan, supersede txn, error class) | 3 | self | verdict read |
| scratch copy + provenance | 1 | self, inline | 3 commands on the critical path |
| install P1–P3 + my own probes into the scratch copy | 3 | self | probe design is judgment |
| `--collect-only` declarations, every pytest run, mutation_proof runs | 1 | self, inline (no Agent tool) | would be `haiku-runner`; not available here |
| own wrong-build design (≥3) | 3 | self | mutation design is never Haiku |

Fan-out: haiku 0 · sonnet 0 · peak 0 (no Agent tool; test runs inline).

## SCRATCH AND PROVENANCE
- `scripts/scratch_copy.sh …/scratchpad/ca58/ca58-probes` (EXIT=0, provenance asserted), then
  `git -C <copy> checkout aa4ea04 -- .` (this also reverted the live tree's two dirty `scripts/test_*` files in the
  copy). `git rev-parse HEAD` = aa4ea0426e53…; `git status --short` = 4 untracked REPORT files only (before my probes).
- P1–P3: `loremaster/tests/test_adv_r53_probes.py` extracted from REPORT-adversary-58-r53.md lines 355–511; md5
  `b63156ce…` of the extracted file == md5 of those report lines (byte-identical).
- Own probes: `loremaster/tests/test_ca58_own_probes.py` (Q1–Q5), pasted in §INSTRUMENTS.

## CONFIRMATIONS (brief items a–c)
**(a) packer — CONFIRMED (HIGH).** Read: `TaskLedger._pack_heal_chunks` at aa4ea04: `cap = min(_txn_module.
TXN_ROW_WARN_THRESHOLD, _txn_module.TXN_ROW_HARD_CAP)` read in the body (live), `constrained_batches(built, cap,
get_len=lambda entry: entry[3], strict=True)` materialised in a list comprehension inside `try`; `except ValueError`
→ `StragglerHealPackerError(row_id=worst[0], weight=worst[3], row_cap=cap)` with `worst = max(built, key=weight)`.
Construction:
- `tools/packer_worlds.py` (log `logs/packer_worlds.log`, EXIT=0): the REAL packer in four worlds patched after
  import — (10000, 50000), (800, 5000), (800, 500 = HARD<WARN), (10000, 10000): a row of weight == bound packs alone at
  exactly the bound; a row of bound+1 placed BETWEEN two light rows is refused with `(heavy, bound+1, bound)`;
  empty → `[]`. "ALL WORLDS OK".
- Q1 (store, shrunk 800/5000): a straggler of weight 1 201 (400 superseded blockers, one head; weight derived from the
  tree's own `_plan_heal_rows`, asserted in (800, 5000]) plus a HEALABLE companion straggler → BOTH boots raise, typed
  facts `== (heavy, 1201, heal_chunk_bound()=800)`, and the whole-store `snapshot` (every row + every edge) is
  unchanged after each boot. GREEN (`logs/baseline-probes2.log`: 8 passed, EXIT=0).
- Q2 (§11's control leg): 266 superseded blockers → weight 799 ≤ 800 (and 267 → 802 > 800, asserted: a tight control)
  heals in one boot, edges mirror every column. GREEN.
- P3 GREEN on the built tree; control C9 (= adversary WB9 on the built text: refuse only above the hard cap, pack the
  rest with `strict=False`) → P3 + Q1 RED, PROOF HELD (`logs/c09_pack_alone.log`: 3 failed / 141 passed, the 3rd =
  the registry-adjudicated 64b-i id, see §RUNS).

**(b) heal DELETE uniform — CONFIRMED (HIGH).** Read: `TaskLedger._plan_heal_rows` builds ONE comprehension
`f"DELETE $hd{row_index}_out<-{BLOCKS_RELATION} " f"WHERE in = $hd{row_index}_{i}_in" for i in range(len(olds))`
with params `hd{row_index}_out` = the dependent's RecordID and `hd{row_index}_{i}_in` per superseded blocker — no
per-index branch. Construction: P1 (straggler with TWO superseded blockers, EVERY DELETE of the heal EXPLAINed, none
iterates `blocks`) GREEN; control C10 (= WB10: V1 for i>0) → P1 RED only, PROOF HELD (`logs/c10_heal_first_only.log`).
Q3 (two superseded blockers with DIFFERENT heads + one live blocker; exact edge set after heal) GREEN. Q5 (legacy
`[old, old]` column with a DOUBLED old→target edge): both duplicate edges retired by the heal — GREEN; this measures
am-17 §9.2's "duplicate edges … not separately measured" item on the built tree.

**(c) supersede DELETE — CONFIRMED (HIGH).** Read: `TaskLedger._supersede_transaction`'s DELETE fragment holds
exactly one statement, `f"DELETE $ssx_old_rec->{BLOCKS_RELATION}"`, params `{"ssx_old_rec": RecordID(TASK_TABLE,
old_id), "ssx_old": old_id}`. Construction: P2 (EVERY DELETE of the supersede transaction EXPLAINed, none iterates
`blocks`) GREEN; control C14b (= WB14b: decoy + string-spelled table scan) → P2 RED only, PROOF HELD
(`logs/c14b_sup_decoy_plus_scan.log`). Q4 (drift edge) and Q5 (doubled hub→dependent edge) GREEN: every edge out of
the superseded task is retired.

## WRONG BUILDS (mine, not WB1–WB15; reds declared from `--collect-only` at 2026-11-10T05:02:30Z, OB7 at 05:13:05Z,
before any run; each via `scripts/mutation_proof.py`, `mutation LANDED` ×1, restore md5 `cb9b15f7…` every time)
Selection (non-empty, checked): the 3 briefed files + `test_reanchor_58_r3_convergence.py` + P1–P3 + Q1–Q5 = 144 ids
(OB7: `sel_ob7.txt`, 84 ids). The adjudicated 64b-i id is declared in every 144-id run.
| # | family | wrong build | result | killed by | verdict |
|---|---|---|---|---|---|
| OB1 | packer / refusal | "heal what fits, then fail loud": pack only rows ≤ bound, apply them, THEN raise the typed error for the over-bound row (`row_cap` = bound) | PROOF HELD, 3 failed / 141 | r3 F10 leg `TestARowOverTheCapFailsTheBootLOUD` (companion changed) + Q1; **NOT by any of the 3 briefed files** (P3 has no companion, stays green) | KILLED (contract, r3_convergence only) → R-1 |
| OB2 | heal DELETE set | every per-blocker DELETE binds index 0 (`$hd{row}_0_in`) | PROOF FAILED (more reds than declared): 37 failed | 34 r3_convergence ids (`e2-distinct-*` shapes: "edges not implied by any column") + Q2 + Q3 | KILLED (contract) |
| OB3 | supersede DELETE set | `DELETE $ssx_old_rec->blocks WHERE out INSIDE $ssx_deps` (only edges to the dependents it read) | PROOF HELD, 2 failed / 142 | **only my Q4** (+ the adjudicated id); P2, the supersede plan leg and every mirror leg GREEN | **SURVIVES THE CONTRACT** → F1 |
| OB5 | weight / bound | row weight omits the RELATE fragment (`fragment_rows(fragments)`) | PROOF FAILED: 18 failed | r53 legs 1/2/3, r3 F10 + 12 cap-boundary/mixed ids, r4 `[tasks.py::ensure_ready -> …]` | KILLED (contract) |
| OB6 | heal DELETE set | the DELETE comprehension ranges over ALL columns (live blockers' edges deleted too) | PROOF FAILED: 24 failed | r53 heal plan leg, 21 r3_convergence ids, Q3 | KILLED (contract) |
| OB7 | supersede fragment | drop `"ssx_old"` from the DELETE fragment's params (it looks unused there) | PROOF FAILED: 3 failed / 81 | `test_supersede_reanchor_58.py::TestAConcurrentCreateIsRefusedNotStranded::test_the_supersede_is_REFUSED_byte_inert_and_TEACHES_retry` + both r3_tiers `TxnReanchorStragglerError` ids (`DID NOT RAISE`) | KILLED (contract) → R-2 |
(OB4, a default-argument capture of the bound, was designed and dropped before declaration: it is WB3's class.)
"PROOF FAILED" rows: the mutation landed and the contract reddened MORE than my declared probe set — i.e. the contract
kills it; the observed sets are in each log's `WENT RED but was NOT DECLARED` block.

## FINDINGS
**F1 (minor, HIGH) — the supersede DELETE's "every edge out of the old task" is pinned only in mirror-consistent
worlds.** am-17 §9.2's inventory says the old statement's first behaviour (deletes every edge whose `in` is the old
task) is "PRESERVED … pinned today by the supersede legs that assert the edge mirror". OB3 (retire only the edges to
the dependents the supersede read) passes all 144 ids except my Q4: no fixture seeds an edge out of the hub whose
target's column does not name the hub, so the mirror legs cannot see a survivor. The built tree is CORRECT (Q4 green).
Consequence of the wrong build: a drift edge from a superseded task survives forever (the boot backfill only MINTS
edges — `_backfill_blocks_edges` docstring), and edge-riding reads (`transitive_blockers`) would keep naming the
superseded task. Plausibility of an honest builder writing OB3: LOW–MEDIUM. Pin that should exist: Q4 (§INSTRUMENTS).
Receipt: `logs/ob3_sup_only_read_dependents.log` (PROOF HELD, 2 failed / 142 passed, EXIT=0); Q4 green in
`logs/baseline-probes2.log`.

**F2 (minor, HIGH) — `StragglerHealPackerError`'s message and docstring are false after am-17.** The built packer
passes the chunk bound (10 000) as `row_cap`, but the message still says *"alone composes 10001 rows, over the
10000-row transaction cap — the heal cannot pack it"* and the class docstring *"composes more ROWS than one transaction
may carry … `row_cap` (the live cap)"*. The live transaction cap is 50 000 and a 10 001-row straggler fits one
transaction; it is refused by ruling (am-17 §11), not because it cannot be packed. The message is what an agent or
operator reads when every boot fails (`ensure_ready` runs in `server.build_app_context`, lore_impact). TRUST doctrine:
teaching prose must match measured behaviour. am-17 §7/§10.3 ordered the packer docstring, not this class's prose, so
this is a rider nobody was given rather than a dropped one. Receipt: `tools/packer_error_prose.py`, log
`logs/packer_error_prose.log` (EXIT=0): `WARN=10000 HARD=50000 weight=10001 fits_one_txn=True`, message as quoted.

## RESIDUALS
- **R-1 (scope):** the three files the audit brief names do not kill OB1 (partial commit before the loud refusal); only
  `test_reanchor_58_r3_convergence.py`'s F10 leg does. Any targeted run of "the r5.3 + supersede + r4" trio would miss
  that class. Not a defect in the built tree (Q1 + F10 green).
- **R-2 (latent coupling, HIGH on the observation):** `$ssx_old` is defined only in the DELETE fragment's params, yet
  consumed by the final straggler-guard fragment, which carries `params={}`. Removing it (OB7, a tidy-up that looks
  safe locally) makes the guard evaluate against NONE and silently never THROW (`DID NOT RAISE`). It IS pinned (3
  contract ids kill OB7), so no defect today; the class question is whether `compose` should refuse an undefined
  `$param` (D3).
- **R-3 (numbers stated for one shape):** `tools/row_weight_shapes.py` (log `logs/row_weight_shapes.log`, EXIT=0):
  a straggler's weight is `3k+1` with ONE shared chain head and `4k` with k DISTINCT heads; the first refused k at the
  10 000 bound is 3 334 vs 2 501 (verified at k−1/k). am-17 §5/§11's "roughly 2,500 … 12,500 superseded blockers" is
  the distinct-head case; the shared-head range is ~3 334–16 666. The adversary's P3 comment "4·400 + 1 = 1 201" mixes
  the two (1 201 = 3·400 + 1 is right). Wording only.

## RUNS (2026-11-10, all in the copy, `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0`, `-n 8` or
`-n 4`, `--timeout=300`, TEST store :18000; logs under `…/scratchpad/ca58/logs/`, each headed by `tree_id.sh` and
`loremaster.__file__`)
| run | log | count line | EXIT |
|---|---|---|---|
| baseline, 6 files incl. P1–P3 + Q1–Q4 (143 ids) | `baseline-built.log` | 2 failed, 141 passed | 1 |
| probes re-run after the Q2 fix (+Q5) | `baseline-probes2.log` | 8 passed | 0 |
| C9 / C10 / C14b controls | `c09_pack_alone.log` / `c10_heal_first_only.log` / `c14b_sup_decoy_plus_scan.log` | 3 failed/141 · 2/142 · 2/142, PROOF HELD | 0 |
| OB1, OB2, OB3, OB5, OB6, OB7 | `ob*.log` | table above | 0 / 4 / 0 / 4 / 4 / 4 |
| offline instruments | `packer_worlds.log`, `packer_error_prose.log`, `row_weight_shapes.log` | ALL WORLDS OK · printed · printed | 0 |
Baseline reds: (1) `test_reanchor_58_r4_state.py::…[findings.py::_run_guarded -> findings.py::_run_guarded]` —
`TypeError: FindingLedger.report() got an unexpected keyword argument 'title'`; it is a declared bound in
`scripts/pending_contracts.yaml` (packet 64b-i's unbuilt driver), present in every 144-id run and declared in each.
(2) my Q2, for my own arithmetic (deviation 3). No full suite; no live-tree run. One `pkill -f` of my own stuck offline
script self-matched its own shell (exit 144, the #228 landmine); nothing else was running; re-run cleanly.

## §INSTRUMENTS (pasted verbatim; scratch only)
P1–P3: verbatim REPORT-adversary-58-r53.md §INSTRUMENTS `probes/test_adv_r53_probes.py` (md5-checked above).

### `ca58-probes/loremaster/tests/test_ca58_own_probes.py`
```
"""ca58-probes cold-audit probes (SCRATCH ONLY; pasted verbatim in
docs/plans/v2/receipts/2026-11-09-packet58/coldaudit-58-ca58-probes.md §INSTRUMENTS).

Each is GREEN on the built tree aa4ea04 (the positive control) and is the detector for one of my own wrong builds:

* Q1 (P3, widened to the full am-17 §11 rule): a single straggler whose weight is in (bound, hard] fails BOTH boots
  loud with ``StragglerHealPackerError`` whose typed facts equal their derivations (``row_cap`` = the LIVE
  ``min(WARN, HARD)``), and the WHOLE store (a healable companion straggler included) is byte-unchanged.
* Q2 (§11's control leg): a straggler weighing at most the bound (weight derived offline from the tree's own
  ``_plan_heal_rows``, asserted <= bound first so the control is not vacuous) heals in one boot.
* Q3 (heal DELETE SET, the quantifier door of MP-2 on the EFFECT side): a straggler naming TWO superseded blockers
  with DIFFERENT chain heads plus ONE live blocker; after one boot the edge multiset mirrors every column, no edge
  from either superseded blocker into it survives, and the live blocker's edge survives.
* Q4 (supersede DELETE SET, am-17 §9.2's removed-behaviour inventory item 1: "deletes every edge whose ``in`` is the
  old task"): a hub with dependents AND one drift edge hub->X whose X does not name the hub; after the supersede no
  edge out of the hub survives, and X's own row is untouched.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from _reanchor_58_support import (
    CREATOR,
    DESCRIPTION,
    SHRUNK_ROW_HARD_CAP,
    assert_edge_mirrors_column_for_every_row,
    boot,
    bulk_seed_dependents,
    column,
    create,
    edge_pairs,
    heal_chunk_bound,
    ledger58,
    raw,
    raw_relate,
    raw_seed_row,
    shrunk_row_caps,
    snapshot,
    supersede,
)
from _surreal_harness import SurrealEnv
from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE
from loremaster.tasks import StragglerHealPackerError, TaskLedger
from surrealdb import RecordID

__all__ = ["ledger58", "shrunk_row_caps"]


def _offline_weight(superseded_blockers: int) -> int:
    """The tree's OWN weight for one straggler naming ``superseded_blockers`` superseded blockers, one head."""
    ledger = TaskLedger.__new__(TaskLedger)
    ledger._database = "offline"  # noqa: SLF001
    olds = [f"old{index}" for index in range(superseded_blockers)]
    built = ledger._plan_heal_rows(  # noqa: SLF001
        [{"id": "dependent", "blocked_by": olds}],
        {old: "head" for old in olds},
        {old: ("head", False) for old in olds},
        {"head"},
        "t",
    )
    return int(built[0][3])


async def _seed_heavy(ledger: TaskLedger, head: str, tag: str, entries: int) -> tuple[str, list[str]]:
    """One straggler naming ``entries`` superseded blockers (all superseded by ``head``), edges mirrored."""
    now = datetime.now(UTC)
    legacy = [f"{tag}{index:05d}".ljust(32, "a")[:32] for index in range(entries)]
    documents = [
        {
            "id": RecordID(TASK_TABLE, lid),
            **TaskLedger._new_task_content(f"legacy {lid}", DESCRIPTION, [], CREATOR, now),  # noqa: SLF001
            "superseded_by": head,
        }
        for lid in legacy
    ]
    await raw(ledger, f"INSERT INTO {TASK_TABLE} $rows", {"rows": documents})
    heavy = f"{tag}heavy".ljust(32, "b")[:32]
    content = TaskLedger._new_task_content("heavy", DESCRIPTION, legacy, CREATOR, now)  # noqa: SLF001
    await raw(ledger, f"CREATE type::record('{TASK_TABLE}', $id) CONTENT $c", {"id": heavy, "c": content})
    edges = [{"in": RecordID(TASK_TABLE, lid), "out": RecordID(TASK_TABLE, heavy)} for lid in legacy]
    await raw(ledger, f"INSERT RELATION INTO {BLOCKS_RELATION} $edges", {"edges": edges})
    return heavy, legacy


@pytest.mark.usefixtures("shrunk_row_caps")
async def test_Q1_one_row_in_bound_to_hard_fails_both_boots_loud_and_changes_NOTHING(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, env = ledger58
    entries = 400
    derived_weight = _offline_weight(entries)
    bound = heal_chunk_bound()
    assert bound < derived_weight <= SHRUNK_ROW_HARD_CAP, (bound, derived_weight)  # the (bound, hard] door
    head = await create(ledger, "q1 head")
    heavy, _legacy = await _seed_heavy(ledger, head, "q1leg", entries)
    # a healable companion straggler: a boot that heals it before refusing the heavy row changes the store
    old = "q1companionoldaaaaaaaaaaaaaaaaaa"
    await raw_seed_row(ledger, old, blocked_by=[], superseded_by=head)
    companion = "q1companionaaaaaaaaaaaaaaaaaaaaa"
    await raw_seed_row(ledger, companion, blocked_by=[old])
    await raw_relate(ledger, old, companion)
    before = await snapshot(ledger)
    for boot_number in (1, 2):
        with pytest.raises(StragglerHealPackerError) as caught:
            await boot(env)
        facts = (caught.value.row_id, caught.value.weight, caught.value.row_cap)
        assert facts == (heavy, derived_weight, heal_chunk_bound()), (boot_number, facts)
        assert await snapshot(ledger) == before, f"boot {boot_number}: a loud refusal changed the store"


@pytest.mark.usefixtures("shrunk_row_caps")
async def test_Q2_control_a_row_at_most_the_bound_heals(ledger58: tuple[TaskLedger, SurrealEnv]) -> None:
    ledger, env = ledger58
    entries = 266
    derived_weight = _offline_weight(entries)
    assert derived_weight <= heal_chunk_bound(), (derived_weight, heal_chunk_bound())  # non-vacuous control
    assert _offline_weight(entries + 1) > heal_chunk_bound(), "266 must be the LAST in-bound count (tight control)"
    head = await create(ledger, "q2 head")
    heavy, _legacy = await _seed_heavy(ledger, head, "q2leg", entries)
    await boot(env)
    assert await column(ledger, heavy) == [head]
    await assert_edge_mirrors_column_for_every_row(ledger, where="Q2 after one boot")


async def test_Q3_two_superseded_blockers_with_different_heads_plus_a_live_one_heal_the_exact_edge_set(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, env = ledger58
    head_a = await create(ledger, "q3 head a")
    head_b = await create(ledger, "q3 head b")
    live = await create(ledger, "q3 live blocker")
    old_a, old_b = "q3oldaaaaaaaaaaaaaaaaaaaaaaaaa01", "q3oldbbbbbbbbbbbbbbbbbbbbbbbbb02"
    await raw_seed_row(ledger, old_a, blocked_by=[], superseded_by=head_a)
    await raw_seed_row(ledger, old_b, blocked_by=[], superseded_by=head_b)
    target = "q3targetaaaaaaaaaaaaaaaaaaaaaa01"
    await raw_seed_row(ledger, target, blocked_by=[old_a, live, old_b])
    for blocker in (old_a, live, old_b):
        await raw_relate(ledger, blocker, target)
    noise = await create(ledger, "q3 noise")
    await bulk_seed_dependents(ledger, noise, 10, tag="q3n")
    await boot(env)
    assert await column(ledger, target) == [head_a, live, head_b]
    into_target = sorted(blocker for blocker, blocked in await edge_pairs(ledger) if blocked == target)
    assert into_target == sorted([head_a, head_b, live]), into_target
    await assert_edge_mirrors_column_for_every_row(ledger, where="Q3 after one boot")


async def test_Q4_supersede_retires_EVERY_edge_out_of_the_old_task_including_a_drift_edge(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, _env = ledger58
    hub = await create(ledger, "q4 hub")
    await bulk_seed_dependents(ledger, hub, 3, tag="q4d")
    drift = await create(ledger, "q4 drift target")  # its column does NOT name the hub
    await raw_relate(ledger, hub, drift)
    drift_row_before: Any = await raw(ledger, f"SELECT * FROM type::record('{TASK_TABLE}', $id)", {"id": drift})
    await supersede(ledger, hub)
    out_of_hub = [pair for pair in await edge_pairs(ledger) if pair[0] == hub]
    assert out_of_hub == [], f"edges out of the superseded task survived: {out_of_hub}"
    drift_row_after = await raw(ledger, f"SELECT * FROM type::record('{TASK_TABLE}', $id)", {"id": drift})
    assert drift_row_after == drift_row_before


async def test_Q5_duplicate_legacy_edges_are_ALL_retired_by_heal_and_by_supersede(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    """am-17 §9.2 inventory item 3 (spec-silent, "not separately measured"): the table has no UNIQUE(in, out), so a
    legacy store can hold a pair twice. Heal: a straggler whose legacy column is ``[old, old]`` with two old->target
    edges. Supersede: a hub with a doubled hub->dependent edge. After each, no edge out of the retired task survives."""
    ledger, env = ledger58
    head = await create(ledger, "q5 head")
    old = "q5oldaaaaaaaaaaaaaaaaaaaaaaaaa01"
    await raw_seed_row(ledger, old, blocked_by=[], superseded_by=head)
    target = "q5targetaaaaaaaaaaaaaaaaaaaaaa01"
    await raw_seed_row(ledger, target, blocked_by=[old, old])
    await raw_relate(ledger, old, target)
    await raw_relate(ledger, old, target)
    await boot(env)
    assert [pair for pair in await edge_pairs(ledger) if pair[0] == old] == []
    assert sorted(b for b, t in await edge_pairs(ledger) if t == target) == [head]
    hub = await create(ledger, "q5 hub")
    dependent = await create(ledger, "q5 dependent", blocked_by=[hub])
    await raw_relate(ledger, hub, dependent)  # the doubled edge
    await supersede(ledger, hub)
    assert [pair for pair in await edge_pairs(ledger) if pair[0] == hub] == []
```

### `tools/make_builds.py`
```
"""ca58-probes: anchor/replacement files per build against the BUILT tasks.py (aa4ea04); each anchor exactly once.
C9/C10/C14b = the adversary's WB9/WB10/WB14b re-spelled for the built tree's text (positive controls for P1-P3 on
THIS tree). OB1-OB6 = my own builds."""
import sys
from pathlib import Path

S = Path(sys.argv[1])
src = (S / "ca58-probes/loremaster/loremaster/tasks.py").read_text()
HEAL = (
    '                        f"DELETE $hd{row_index}_out<-{BLOCKS_RELATION} "\n'
    '                        f"WHERE in = $hd{row_index}_{i}_in"\n'
)
SUP = '                statements=[f"DELETE $ssx_old_rec->{BLOCKS_RELATION}"],\n'
SUP_WITH_PARAMS = SUP + '                params={"ssx_old_rec": RecordID(TASK_TABLE, old_id), "ssx_old": old_id},\n'
TRY = '''        try:
            return [
                list(batch)
                for batch in constrained_batches(built, cap, get_len=lambda entry: entry[3], strict=True)
            ]
        except ValueError as error:
            worst = max(built, key=lambda entry: entry[3])
            raise StragglerHealPackerError(row_id=worst[0], weight=worst[3], row_cap=cap) from error
'''
LOOP = '''        chunks = self._pack_heal_chunks(built)
        healed = 0
'''
LOOP_TAIL = '''        if healed:
            logger.info(
                _HEAL_EVENT, extra={"database": self._database, "count": healed, "chunks": len(chunks)}
            )
'''
COST = "            cost = _txn_module.fragment_rows([*fragments, self._relate_fragment(relates)])\n"
HEAL_BLOCK = '''                    statements=[
                        f"DELETE $hd{row_index}_out<-{BLOCKS_RELATION} "
                        f"WHERE in = $hd{row_index}_{i}_in"
                        for i in range(len(olds))
                    ],
                    params={
                        f"hd{row_index}_out": RecordID(TASK_TABLE, dependent),
                        **{f"hd{row_index}_{i}_in": RecordID(TASK_TABLE, old) for i, old in enumerate(olds)},
                    },
'''
# OB1 needs the whole _reanchor_stragglers tail as ONE contiguous anchor
start = src.index(LOOP)
end = src.index(LOOP_TAIL, start) + len(LOOP_TAIL)
OB1_ANCHOR = src[start:end]
OB1_REPL = (
    "        bound = min(_txn_module.TXN_ROW_WARN_THRESHOLD, _txn_module.TXN_ROW_HARD_CAP)\n"
    "        over = [entry for entry in built if entry[3] > bound]\n"
    "        chunks = self._pack_heal_chunks([entry for entry in built if entry[3] <= bound])\n"
    + OB1_ANCHOR[len("        chunks = self._pack_heal_chunks(built)\n"):]
    + "        if over:\n"
    "            worst = max(over, key=lambda entry: entry[3])\n"
    "            raise StragglerHealPackerError(row_id=worst[0], weight=worst[3], row_cap=bound)\n"
)
builds = {
    "c09_pack_alone": (TRY, '''        worst = max(built, key=lambda entry: entry[3], default=None)
        if worst is not None and worst[3] > _txn_module.TXN_ROW_HARD_CAP:
            raise StragglerHealPackerError(row_id=worst[0], weight=worst[3], row_cap=cap)
        return [list(batch) for batch in constrained_batches(built, cap, get_len=lambda entry: entry[3], strict=False)]
'''),
    "c10_heal_first_only": (HEAL, '''                        (f"DELETE $hd{row_index}_out<-{BLOCKS_RELATION} WHERE in = $hd{row_index}_{i}_in" if i == 0 else f"DELETE {BLOCKS_RELATION} WHERE in = $hd{row_index}_{i}_in AND out = $hd{row_index}_out")
'''),
    "c14b_sup_decoy_plus_scan": (SUP, '''                statements=[f"DELETE $ssx_old_rec->{BLOCKS_RELATION}", f"DELETE {BLOCKS_RELATION} WHERE in = type::record('{TASK_TABLE}', $ssx_old)"],
'''),
    "ob1_heal_then_raise": (OB1_ANCHOR, OB1_REPL),
    "ob2_heal_index0_only": (HEAL, HEAL.replace("_{i}_in", "_0_in")),
    "ob3_sup_only_read_dependents": (SUP_WITH_PARAMS, '''                statements=[f"DELETE $ssx_old_rec->{BLOCKS_RELATION} WHERE out INSIDE $ssx_deps"],
                params={
                    "ssx_old_rec": RecordID(TASK_TABLE, old_id), "ssx_old": old_id,
                    "ssx_deps": [RecordID(TASK_TABLE, dependent) for dependent in dependents],
                },
'''),
    "ob5_weight_without_relate": (COST, "            cost = _txn_module.fragment_rows(fragments)\n"),
    "ob6_heal_delete_every_column": (HEAL_BLOCK, HEAL_BLOCK.replace("range(len(olds))", "range(len(columns))")
                                     .replace("enumerate(olds)", "enumerate(columns)")),
}
for name, (anchor, repl) in builds.items():
    assert src.count(anchor) == 1, (name, src.count(anchor))
    assert anchor != repl, name
    d = S / "specs" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "anchor").write_text(anchor)
    (d / "replacement").write_text(repl)
    print(name, "ok")
```

### `tools/run_wb.sh`
```
#!/usr/bin/env bash
# run_wb.sh <build>: mutate the BUILT tasks.py in the ca58-probes scratch copy via scripts/mutation_proof.py
# (exactly-once anchor, both-way diff vs the pre-declared RED set, byte-exact restore); selection = sel.txt (6 files).
set -uo pipefail
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58
B=$1; C=$S/ca58-probes; cd "$C" || exit 2
LOG=$S/logs/$B.log
read -r -a SEL < "${SELFILE:-$S/sel.txt}"; mapfile -t RED < "$S/decl/$B.red"
[ "${#SEL[@]}" -gt 0 ] && [ "${#RED[@]}" -gt 0 ] || { echo "REFUSED: empty selection/declaration for $B" > "$LOG"; exit 3; }
for f in "${SEL[@]}"; do [ -f "$f" ] || { echo "REFUSED: missing $f" > "$LOG"; exit 3; }; done
EXP=(); for r in "${RED[@]}"; do EXP+=(--expect-red "$r"); done
BEFORE=$(md5sum loremaster/loremaster/tasks.py | cut -d' ' -f1)
{ ~/.claude/orchestration/tree_id.sh "$C"
  echo "loremaster.__file__=$(.venv/bin/python -c 'import loremaster;print(loremaster.__file__)')"
  echo "tasks.py md5 before=$BEFORE"
  systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 \
    .venv/bin/python scripts/mutation_proof.py --file loremaster/loremaster/tasks.py \
      --anchor-file "$S/specs/$B/anchor" --replacement-file "$S/specs/$B/replacement" "${EXP[@]}" -- \
      .venv/bin/python -m pytest -q -n 8 --timeout=300 -p no:cacheprovider -rfE "${SEL[@]}"
  echo "EXIT=$?"
  echo "tasks.py md5 after=$(md5sum loremaster/loremaster/tasks.py | cut -d' ' -f1)"; } > "$LOG" 2>&1
```

### `tools/packer_worlds.py`
```
"""ca58-probes: drive the REAL TaskLedger._pack_heal_chunks (no store) in four constant worlds, constants patched on
the live _txn module AFTER import (so a build that copied either at import time would show the unpatched bound)."""
import loremaster
from loremaster.store import _txn
from loremaster.tasks import StragglerHealPackerError, TaskLedger
print("loremaster.__file__", loremaster.__file__)
REAL = (_txn.TXN_ROW_WARN_THRESHOLD, _txn.TXN_ROW_HARD_CAP)
def world(warn, hard):
    _txn.TXN_ROW_WARN_THRESHOLD, _txn.TXN_ROW_HARD_CAP = warn, hard
    bound = min(warn, hard)
    at = [("light", [], [], 1), ("exact", [], [], bound), ("light2", [], [], 1)]
    chunks = TaskLedger._pack_heal_chunks(at)
    sizes = [sum(e[3] for e in c) for c in chunks]
    over = [("light", [], [], 1), ("heavy", [], [], bound + 1), ("light2", [], [], 1)]
    try:
        TaskLedger._pack_heal_chunks(over); refused = "NO RAISE"
    except StragglerHealPackerError as e:
        refused = (e.row_id, e.weight, e.row_cap)
    print(f"WARN={warn} HARD={hard} bound={bound}: at-bound chunk sums={sizes} max={max(sizes)} | bound+1 -> {refused}"
          f" | empty -> {TaskLedger._pack_heal_chunks([])}")
    assert max(sizes) <= bound and refused == ("heavy", bound + 1, bound)
for w, h in (REAL, (800, 5000), (800, 500), (REAL[0], REAL[0])):
    world(w, h)
_txn.TXN_ROW_WARN_THRESHOLD, _txn.TXN_ROW_HARD_CAP = REAL
print("ALL WORLDS OK")
```

### `tools/packer_error_prose.py`
```
"""ca58-probes: what StragglerHealPackerError SAYS vs the live caps, for a row the built packer refuses (real constants).
Drives the REAL _pack_heal_chunks with one synthetic entry of weight bound+1 (no store)."""
import loremaster
from loremaster.store import _txn
from loremaster.tasks import StragglerHealPackerError, TaskLedger
print("loremaster.__file__", loremaster.__file__)
bound = min(_txn.TXN_ROW_WARN_THRESHOLD, _txn.TXN_ROW_HARD_CAP)
weight = bound + 1
try:
    TaskLedger._pack_heal_chunks([("rowid0001", [], [], weight)])
except StragglerHealPackerError as error:
    print(f"WARN={_txn.TXN_ROW_WARN_THRESHOLD} HARD={_txn.TXN_ROW_HARD_CAP} weight={weight} fits_one_txn={weight <= _txn.TXN_ROW_HARD_CAP}")
    print("row_cap=", error.row_cap)
    print("message:", error)
    print("class doc:", " ".join(StragglerHealPackerError.__doc__.split()))
else:
    print("NO RAISE")
```

### `tools/row_weight_shapes.py`
```
"""ca58-probes: one straggler's heal weight (the tree's own _plan_heal_rows cost) for k superseded blockers, with ONE
shared chain head vs k DISTINCT heads; linear fit from k=1,2,3,10, and the first refused k at the real chunk bound
PREDICTED from the fit and then VERIFIED by computing the weight at k-1 and k. No store."""
import loremaster
from loremaster.store import _txn
from loremaster.tasks import TaskLedger

print("loremaster.__file__", loremaster.__file__)
led = TaskLedger.__new__(TaskLedger)
led._database = "offline"


def weight(k: int, distinct: bool) -> int:
    olds = [f"old{i}" for i in range(k)]
    head = {o: (f"head{i}" if distinct else "head") for i, o in enumerate(olds)}
    built = led._plan_heal_rows(
        [{"id": "dep", "blocked_by": olds}], dict(head),
        {o: (h, False) for o, h in head.items()}, set(head.values()), "t",
    )
    return built[0][3]


bound = min(_txn.TXN_ROW_WARN_THRESHOLD, _txn.TXN_ROW_HARD_CAP)
for distinct in (False, True):
    ws = [weight(k, distinct) for k in (1, 2, 3, 10)]
    per = ws[1] - ws[0]
    fixed = ws[0] - per
    assert ws[2] == fixed + 3 * per and ws[3] == fixed + 10 * per, ("not linear", ws)
    k = (bound - fixed) // per + 1
    below, at = weight(k - 1, distinct), weight(k, distinct)
    assert below <= bound < at, (k, below, at)
    print(f"distinct_heads={distinct}: weight(1,2,3,10)={ws} fixed={fixed} per={per}; "
          f"first refused k at bound {bound} = {k} (weight {below} at k-1, {at} at k)")
```

### OB7 spec (anchor → replacement, one line each)
```
                params={"ssx_old_rec": RecordID(TASK_TABLE, old_id), "ssx_old": old_id},
                params={"ssx_old_rec": RecordID(TASK_TABLE, old_id)},
```

### Declarations
```
2026-11-10T05:02:30Z
2026-11-10T05:13:05Z
b67813786fc778ecca8d877321699b69  decl/c09_pack_alone.red
51c247d4633eb16bc98689484efe5ea7  decl/c10_heal_first_only.red
0f2136cbb14e29750081effe549fbf22  decl/c14b_sup_decoy_plus_scan.red
dc56a906dee9c5e514020bae5ab48a54  decl/ob1_heal_then_raise.red
033e80af47e37f92926fc8e635812ca8  decl/ob2_heal_index0_only.red
a970758cd8ad4345f4f9e9efcffb3860  decl/ob3_sup_only_read_dependents.red
917cd7f275a1dfd677613f32ae76e10d  decl/ob5_weight_without_relate.red
033e80af47e37f92926fc8e635812ca8  decl/ob6_heal_delete_every_column.red
fd4a6cf6f8b2a09510f23f3995c6d3d3  decl/ob7_drop_unused_looking_param.red
```
