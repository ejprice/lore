brief-base v27 read · brief project v7 read

# REPORT — builder-58-1 (packet 58 build, base HEAD `60b51c4`)

## SUMMARY BLOCK
- brief-base v27 read · brief project v7 read
- **State: done-with-deviations** (base `60b51c4`; am-17 built per its §7; tree uncommitted).
- **Deviations:** (1) built FROM the r5 reference (lead-accepted) — §PROVENANCE; (2) esc1 ARCHIVED not re-keyed (am-8 §5 option 2); (3) the am-16 §8 measurement FAILED 150 s on the first build (300 s timeout) → am-17 (heal bound `min(WARN,HARD)` + dependent-anchored DELETEs) built, re-measured (§HEAL-TIMING-2); (4) `_reanchor_stragglers` extract-method kept to TWO helpers (a third moved the RELATE-composing verb and reddened 2 derived-verb pins; folded back).
- **Packages considered:** `more_itertools.constrained_batches` keep (installed signature read, `strict=True`; am-8) · house `tenacity` driver untouched · no new mechanism.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 4 rows, all dispositioned (§DRY LEDGER).
- **Graded:** n/a — builder.
- **Decisions needed:** none blocking. FYI for the lead: delete the `packet-58-contract` registry entry (30 SELF-DESTRUCT residuals, §Registry); `git rm scripts/esc1_write_path_cycle_closure.py` + add the archived copy; Containerfile/image must pick up `more-itertools` (pyproject).
- **Targeted-set result (final3):** 188 failed / 8456 passed / 47 skipped; **0 new reds vs BASE (`60b51c4` scratch, 426 failed)**; 238 BASE reds now green. Every 58-owned red left: `findings.py::_run_guarded` ×2 (64b-i, allowed). The 186 others are the 64b findings-governance contract (not 58).
- Receipt pointers: §Gate receipts · §OWED-ITEMS · §HEAL-TIMING / §HEAL-TIMING-2 · §PROVENANCE · §DRY LEDGER.
- Fan-out: haiku 9 (runners; every RAN line checked against my command; two runner reports were interim "waiting" and I read the logs myself; one base run first hit "no tests ran" because the runset named an untracked file absent from the base tree — rerun without it) · sonnet 0 · peak 2.

## Capability check (brief-base §4)
- Demanded: lore tools, comms, haiku-runner/worker spawns, TEST store `ws://127.0.0.1:18000`. Have: all (lore tools loaded; registered `builder-58-1` / session `pkt58-20261109`). Landmine recall: k=50 returned 8 notes (not cut off).

## Routing table (written before first sweep)
| step | tier | who | reason |
|---|---|---|---|
| extract chain + §HELD by address, md5-check, apply | 1 | self (inline, ~10 commands) | on the critical path, output read whole |
| apply reference to tree, productionize, owed items | 3 | self | code authorship; errors would seal (reference ≠ spec) |
| targeted test runs (mine + BASE at `60b51c4` scratch) | 1 | haiku-runner ×2 parallel | test runs |
| gates (typecheck, ruff, currency typecheck/ruff) | 1 | haiku-runner | gate runs |
| red-by-id diff vs BASE | 1 | self inline (set diff on two junit files) | small, I judge the result |


## §OWED-ITEMS
| item | state |
|---|---|
| §HELD parts 1/3/4 applied verbatim | DONE — md5 `dbba9753…`, `15f38e31…`, `f4048e2d…`; `git apply` exit 0 (test_supersede_render_58.py created by part 1) |
| reference chain (build_ref58→my_ref→am6→r3→r4→build_ref_r5 v4→my_ref_r5) applied to the real tree | DONE — result md5s `tasks.py 401fb950…`, `_txn.py 8d37d2f4…` equal the report's |
| `more-itertools` declared | DONE — `loremaster/pyproject.toml` `more-itertools>=11.1.0`, `uv.lock`. ⚠ the container image builds from pyproject: lead check the Containerfile path |
| lease `error_class` rider (BC-r4-2) | DONE — 4 `lease.lock.*` warnings carry `error_class` (from the reference) |
| am-13 §1 F-8 | DONE at ONE chokepoint: `_run_verified_transaction` passes `label=_TXN_ROLLBACK_LABEL, url=url` and chains `RetryableConflictSignal() from _TransactionConflictCause(engine text)`; `_log_rollback` uses the same constant. Driver comment + `retry_on_conflict` docstring clause retired. **Test edit owed (not mine):** `test_retry_seam.py::…::test_every_exemption_matches_a_REAL_call_site` reds because `_ATTRIBUTED_BY_ANOTHER_MECHANISM` still names `_run_verified_transaction` — am-13 §1: empty it. Posted #20045 |
| BC-r5-3 docstring | DONE — `max_reanchor_dependents` |
| amendment 8 §5 esc1 | ARCHIVED, not re-keyed → `docs/plans/v2/receipts/2026-11-09-packet58/esc1_write_path_cycle_closure.py` with a DUAL header (predates SDK 3.0; ESC-1 discharged 2026-08-01; replaced by 04b-3's mechanism + test_blocks_edge/test_reanchor_58_*). Why: question already discharged, nothing imports it, a faithful re-key means re-deriving a 537-line live-store scenario. Its 8 #616 sites are therefore NOT converted (am-15 §11.1 permits). The lead must `git rm scripts/esc1_write_path_cycle_closure.py` and add the moved file |
| am-16 §2.1 typed facts + ruled sentence | DONE (from the reference delta): `HubSupersedeRefusedError(dependents, rows, row_cap, cap_dependents)`, `StragglerHealPackerError(row_id, weight, row_cap)`; sentence re-wrapped for ruff, text unchanged |
| am-16 §8 heal-chunk measurement | **FAILS the 150 s rule** — see §HEAL-TIMING; posted #20046 |

## §HEAL-TIMING (measured 2026-11-09 at HEAD `60b51c4` + my tree, TEST store `ws://127.0.0.1:18000`, real schema via `TaskLedger.ensure_ready`)
`fixed=0 per=4 cap=50000` → 12 500 one-blocker stragglers fill ONE chunk (50 000 rows). Seeded in 4.3 s. Boot's heal: **wall 300.8 s, `SurrealOutcomeUnknownError … no answer within 300s`, boot RAISED** (heal_chunks=1, heal_rows=[50000]). Verdict: a full row-capped heal chunk does not commit inside the request timeout; a store with > ~12k stragglers would fail boot loud. Not tuned by me (design call; recommendation #20046). Instrument (pasted verbatim, brief-base §1):
```python
"""am-16 §8: time ONE heal chunk packed to the real TXN_ROW_HARD_CAP on the REAL schema (TEST store only)."""
import asyncio, sys, time
from pathlib import Path
sys.path.insert(0, "/home/ejprice/PycharmProjects/lore/loremaster/tests")
import _reanchor_58_support as s
from _surreal_harness import make_env, unique_database, drop_database
from loremaster.store import _txn

async def main() -> None:
    assert "18000" in make_env(database="x", dim=s.PRODUCTION_DIM).url, "TEST store only"
    env = make_env(database=unique_database(), dim=s.PRODUCTION_DIM)
    ledger = s.new_ledger(env)
    await ledger.ensure_ready()
    try:
        fixed, per = await s.measure_heal_shape(ledger, env, "cal")
        cap = _txn.TXN_ROW_HARD_CAP
        n = (cap - fixed) // per
        print(f"fixed={fixed} per={per} cap={cap} -> {n} stragglers per full chunk", flush=True)
        t = time.monotonic()
        head, ids = await s.seed_stragglers(ledger, n, 1, "full")
        print(f"seeded {len(ids)} in {time.monotonic()-t:.1f}s", flush=True)
        spy = s.ComposeSpy()
        t = time.monotonic()
        with spy.installed():
            try:
                await s.boot(env)
                outcome = "ok"
            except Exception as e:
                outcome = f"RAISED {type(e).__name__}: {str(e)[:200]}"
        wall = time.monotonic() - t
        print(f"boot wall={wall:.1f}s outcome={outcome} heal_chunks={len(spy.heal_calls())} heal_rows={spy.heal_rows()}")
        left = await s.raw(ledger, "SELECT count() FROM task WHERE blocked_by CONTAINS $h GROUP ALL", {"h": "full000legacy"}) if False else None
    finally:
        await ledger.close(); await s.drop_database(env) if hasattr(s, "drop_database") else await drop_database(env)
asyncio.run(main())
```

## §PROVENANCE (lead #20043) — every production hunk vs the r5 reference (build chain md5s in §OWED-ITEMS; `git diff` of the tree vs `60b51c4`)
Method: the reference chain was run on the real tree (result md5s `tasks.py 401fb950…`, `_txn.py 8d37d2f4…`), THEN my edits. Tags: **REF-VERBATIM** (byte-identical to what the chain wrote, ruff-neutral) · **REF-ADAPTED** · **OWN** · **HELD** (a §HELD patch, not the reference).
| file · symbol | tag | note |
|---|---|---|
| `server.py` (supersede render, `successor_id`/`reanchored`/`reblocked`), `store/surreal_schema.py` (+8 lines) | **HELD** part 1 (`dbba9753…`) | production hunks inside the held patch, applied verbatim |
| `_txn.py`: `TxnClaimLostError`/`TxnCasLostError`/`TxnReanchorStragglerError`/`TxnHealChunkError`, `_ERROR_CLASS_*`, `*_MARKER`, `_constructed_error_class` overrides, `_THROWN_DOMAIN_MARKERS`, classifier branch, `_TYPED_DOMAIN_REJECTIONS`, `_domain_rejection_error`, `_ROLLBACK_LOG_TIERS`, non-conflict raise log, deleted duplicate `_THROW_RESULT_PREFIX` | **REF-VERBATIM** | am-15 §4.1 / BC-r5-5 shape; builder did not re-derive |
| `_txn.py`: `_TransactionConflictCause`, `_TXN_ROLLBACK_LABEL`, `label=`/`url=` + `from _TransactionConflictCause(...)` in `_run_verified_transaction`, `_log_rollback` literal→constant, driver comment, `retry_on_conflict` `label:` docstring | **OWN** | am-13 §1 F-8 / BC-r5-6; the reference did not carry F-8 (it kept the bare raise and the "exempt" prose) |
| `_txn.py` line wrap of the F-8 call | **OWN** | ruff E501 |
| `tasks.py`: `SupersedeResult`, `SupersedeStragglerError`, `_ACTION_*`/`_HEAL_*` constants, `_guarded_append_fragment` + claim/transition rewrite, `_supersede_transaction`, `_dependent_rows`, `_reblocked`, `_still_claimable`, `exclude_superseded`, `supersede_task` body, `_reanchor_fragments`, ensure_ready→`_reanchor_stragglers` call, `_apply`'s `_log_transaction_size(…, row_count)` (B-6), `fragment_rows` pricing, `TXN_ROW_HARD_CAP` reads | **REF-VERBATIM** | BC-r5-1/2 satisfied by the reference's shape; I checked no `STATEMENT_*` name survives |
| `tasks.py`: `HubSupersedeRefusedError` / `StragglerHealPackerError` typed facts + ruled sentence, `max_reanchor_dependents` | **REF-ADAPTED** | reference text unchanged; only string re-wrapped for E501 (am-16 §2.1 sentence byte-equal) |
| `tasks.py`: `max_reanchor_dependents` docstring (BC-r5-3) | **OWN** | the reference had a one-line docstring |
| `tasks.py`: `_reanchor_stragglers` → `_plan_heal_rows` + `_pack_heal_chunks` + `_apply_heal_chunks` | **REF-ADAPTED** | pure extract-method for PLR0912/PLR0915; same statements, same order |
| `tasks.py`: import block order | **REF-ADAPTED** | `ruff --fix` I001 |
| `store/lease.py` 4 warnings' `error_class` | **REF-ADAPTED** | the reference's one-liner wrapped to a multi-line dict (E501) |
| `findings.py` `_TRANSITION_ALREADY_MESSAGE` `cas_lost:` prefix | **REF-VERBATIM** | |
| `loremaster/pyproject.toml`, `uv.lock` (`more-itertools`) | **OWN** | BC-r4-1; `uv add` |
| `docs/plans/v2/receipts/2026-11-09-packet58/esc1_write_path_cycle_closure.py` | **OWN** | archived copy (moved from `scripts/`; lead: `git rm scripts/esc1_write_path_cycle_closure.py`), DUAL header present at the top of the file (predates SDK 3.0; ESC-1 discharged; what replaced it; removed-behaviour inventory; re-open trigger) |
Divergences from the reference forced by a ruling/constraint: only F-8 (am-13 §1; BC-r5-6) and BC-r5-3's docstring. Reference behaviour no test demands that I kept: not separately established — the cold audit's check; candidates `_still_claimable`, `exclude_superseded`, `SupersedeStragglerError` (all 58-pinned per my run, not verified individually).

## §REDUCTION-AND-RESHAPE (productionize)
Reference departures kept/changed: (1) `_reanchor_stragglers` split into `_plan_heal_rows` / `_pack_heal_chunks` / `_apply_heal_chunks` (ruff PLR0912/PLR0915); behaviour unchanged. (2) import block sorted, long lines wrapped. Things in the reference no test/brief names — flagged, kept silently NOT: `_still_claimable` (claim-loss diagnosis), `exclude_superseded` in `_candidate_statement`, `SupersedeStragglerError` — each has a pin in the 58 files per my run (they are green), so kept; the cold audit should confirm each is demanded.

## §DRY LEDGER
| new symbol | where I looked | what | disposition |
|---|---|---|---|
| `_TransactionConflictCause` | `_txn.py` grep `RetryableConflictSignal`/`__cause__`, am-13 §1 | no carrier existed; am-13 orders one | HAND-ROLLED (named by the ruling) |
| `_TXN_ROLLBACK_LABEL` | `_txn.py` grep `store.transaction.rolled_back` | one literal in `_log_rollback` | EXTENDED (literal became the constant; two uses) |
| `_plan_heal_rows`/`_pack_heal_chunks`/`_apply_heal_chunks` | tasks.py | pure extraction of the reference's own method | REUSED (`constrained_batches`, `_txn.fragment_rows`) |
| reference's `_TYPED_DOMAIN_REJECTIONS`, `_THROWN_DOMAIN_MARKERS`, `_ROLLBACK_LOG_TIERS` | `_txn.py` `_classify_engine_error`, 63c's typed idiom | one mapping each | EXTENDED HEAD's classifier / `_domain_rejection_error` |

Packages considered: `more_itertools.constrained_batches` keep (read installed signature `strict=True`; am-8 ruling) · `tenacity` retry driver already the house seam (not touched) · no new mechanism.

## Gate receipts
| gate | exact command | log | EXIT | count line | TREE |
|---|---|---|---|---|---|
| targeted pytest (declared set + r53 file) | `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run pytest $(cat runset.txt) loremaster/tests/test_reanchor_58_r53_bound_and_plans.py -q -n 8 -p no:cacheprovider --timeout=300 --junitxml=…/final3.xml` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/final3.log | 1 | 188 failed, 8456 passed, 47 skipped | 18b4d3ef…376a25 |
| BASE (`60b51c4` scratch copy, same set minus the untracked held file) | same, in `scratchpad/base60b51c4` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/base2.log | 1 | 426 failed, 7755 passed, 47 skipped | (header in log) |
| `scripts/typecheck.sh` | `scripts/typecheck.sh` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/typecheck_final3.log | 1 | Found 50 errors in 15 files — ALL under loremaster/tests/ (64b findings tests + the two 64b-i `_run_guarded` attr errors); none in production | 18b4d3ef…376a25 |
| `uv run ruff check .` | same | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/ruff_final3.log | 0 | All checks passed! | 18b4d3ef…376a25 |
| currency | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/currency_final3.log | 1 | ruff GREEN; typecheck RED_ORPHANED 30 = every one `SELF-DESTRUCT: registered symbol/file … now RESOLVES` for entry `packet-58-contract`; pytest NOT_RUN (leg excluded by `--legs`) | 18b4d3ef…376a25 |
Notes: the `final`/`final2` logs are superseded (the tree changed after them: apply-fold, then am-17). BASE vs final3 by node id: `python` set-diff of the junit files = 0 new, 238 fixed. `scripts/test_forgery_door_sweep.py` and `scripts/test_pending_contract_gate*.py` are in the set (no red among them). `lore_impact` caps at 15 and misses indirect coverage (#563): the covering tests are the AST import scan of `declare_set_r5.py` (grep-equivalent, said out loud).

## Registry (`scripts/pending_contracts.yaml` — NOT edited by me)
Entry `packet-58-contract` self-destructs: delete it. All its `red_nodeids` are GREEN in final3 except none — the only 58-owned reds are `findings.py::_run_guarded` in `test_reanchor_58_r3_cas_seam.py` and `test_reanchor_58_r4_state.py` (64b-i's bound).

## §HEAL-TIMING-2 (am-17 §7 item 4; 2026-11-09, TEST store `:18000`, `uv run python scripts/probe_heal_curve_58.py E 2500,12500`, built tree)
2 500 stragglers: 1 chunk (10 000 rows), **12.2 s**, healed, old edges left 0. 12 500 stragglers: 5 chunks × 10 000 rows, **61.4 s** total (~12 s per chunk), healed. Both under the 30 s per-chunk line (no escalation) but about 1.7× am-17's expectation (7 s / 35 s): other runners were using the same store/host at the time — not re-measured quiet. The pre-am-17 build timed out at 300 s (§HEAL-TIMING). Note: part E applies its own V3 swap by regex; on this tree the swap is a no-op (the built DELETE is already V3) — the "V3" and "V4" rows agree for that reason.

## §AM-17 patch (lead #20061; am-17 §7 edits 1/2/3 + §9.6 edit 6; measured 2026-11-09 at `fa073bc`)
- File: `docs/plans/v2/receipts/2026-11-09-packet58/am17-build.patch`, md5 `daa68841dda26c0eef9ef5a61c4f70ad`, **`loremaster/loremaster/tasks.py` only**, 4 hunks = (1) `_supersede_transaction` DELETE `$ssx_old_rec->blocks` + comment (§9.6 edit 6); (2) `_plan_heal_rows` DELETE `$hd<row>_out<-blocks WHERE in = $hd<row>_<i>_in` + comment (edit 2); (3) `_pack_heal_chunks` `min(TXN_ROW_WARN_THRESHOLD, TXN_ROW_HARD_CAP)` + docstring (edit 1); (4) `max_reanchor_dependents` docstring band (edit 3). Direction: pre-am-17 → post, so it **reverse-applies** on `fa073bc` (which already contains the am-17 edits; the checkpoint was taken after them).
- **RECONSTRUCTED, not snapshotted** (I took no `cp -a` before the am-17 edits): the pre-am-17 `tasks.py` (md5 `3447cd97d33e92c80e4af913cd894d99`) is `fa073bc`'s file with exactly the four edits inverted to the strings I replaced (the old strings are quoted in this report's history above: hard-cap packer line + one-line docstring, `DELETE blocks WHERE in = … AND out = …`, `DELETE blocks WHERE in = $ssx_old_rec`, the am-15 §1.3 docstring band). It equals the file I ran final/final2 on only by that construction, not by a hash taken then.
- Proofs: `git apply -R --check` of the patch at the repo root (tree `tasks.py` md5 `ee791e44beb250a38fe8772b518e8dc9` = `git show fa073bc:…tasks.py` md5) → **EXIT=0**. In a scratch repo seeded with `fa073bc`'s file: `git apply -R` → md5 `3447cd97…` (= reconstructed pre); then `git apply` → md5 `ee791e44…` (= fa073bc). The patch touches no other path.
- Tests run on the am-17 build: `test_reanchor_58_r3_convergence.py`, `_r2_rulings.py`, `_r2_am2.py` and **`test_reanchor_58_r53_bound_and_plans.py`** (contract-58-r53's IN-PROGRESS, ungraded file) → 98 passed (inline run, 41 s); the whole declared set + that file → final3 (188 failed / 8456 passed, 0 new vs base). Part-E receipt: §HEAL-TIMING-2. Edit 5 (no test edit): none made by me.

## §REGREEN (lead #20073, am-17 §10.3 rider 6; measured 2026-11-09, HEAD `54c7595`, uncommitted tree)
Edits (tasks.py ONLY, no test edit): (1) `_supersede_transaction`'s DELETE → `f"DELETE $ssx_old_rec->{BLOCKS_RELATION}"`; (2) `_pack_heal_chunks` docstring states both measurements with their conditions: 7.25 s per full 10 000-row chunk (am-17's curve, quiet host) and 12.2 s for one chunk of 2 500 stragglers (my part E, host shared with other runs); no new number. (3) KEPT unchanged, per the directive: `strict=True` at `max_size=min(WARN,HARD)`; the heal DELETE comprehension uniform for every superseded-blocker index; exactly one supersede DELETE, anchored on `$ssx_old_rec`. Diff vs `fa073bc` is 5 insertions / 3 deletions, both in tasks.py.
| gate | command | log | EXIT | count | TREE |
|---|---|---|---|---|---|
| targeted (r5.3 file + test_supersede_reanchor_58 + test_task_ledger + test_reanchor_58_r4_state) | `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run pytest <those 4> -q -n 8 -p no:cacheprovider --timeout=300` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/regreen.log | 1 | 1 failed, 318 passed | c21f0479…aaee0e |
| ruff | `uv run ruff check .` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/ruff_regreen.log | 0 | All checks passed! | 6b2f94ca…b7a8d6 |
| typecheck | `scripts/typecheck.sh` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/typecheck_regreen.log | 1 | 50 errors, all under loremaster/tests/ (none in tasks.py) | c21f0479…aaee0e |
| currency | `pending_contract_gate.py --currency --legs typecheck,ruff` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/currency_regreen.log | 1 | ruff GREEN; typecheck **RED_ADJUDICATED** 50 (owner packet-64b-i-contract); **no RED_ORPHANED**; `FAIL — claimed but never run: pytest` = the `--legs` selection, as the brief mandates (not a bare run) | 84ddd3d6…f9da |
The one red: `test_reanchor_58_r4_state.py::…[findings.py::_run_guarded -> findings.py::_run_guarded]` — its driver calls `FindingLedger.report(title=…)`, a 64b-i API not built (TypeError): the allowed 64b-i bound, not 58's. The TREE= values differ per gate because the runner sequence overlapped other agents' edits (HEAD moved to `54c7595` and the lead's commits landed meanwhile); the production edit is the same two hunks in all of them.

## §FIXWAVE-1 (lead #20081; cold audit NO-GO at `aa4ea04`; measured 2026-11-10, base HEAD `25cfd16` + my uncommitted diff)
Files touched (production only, no test edit): `store/_txn.py`, `tasks.py`, `findings.py`, `server.py`.
| item | disposition |
|---|---|
| **F4 (#624)** THROW markers single-sourced | DONE. `_txn.CLAIM_LOST_MARKER` / `CAS_LOST_MARKER` / `REANCHOR_STRAGGLER_MARKER` / `HEAL_CHUNK_MARKER` are the ONE spelling (the three private names became public; nothing else referenced them — `git grep`). `tasks._{REANCHOR_LOST,HEAL_CHUNK,STRAGGLER,SUPERSEDE_ALREADY,TRANSITION_ALREADY}_MESSAGE` and the claim THROW (`_CLAIM_LOST_PREFIX` deleted) and `findings._TRANSITION_ALREADY_MESSAGE` are f-strings built FROM them; the classifier `_THROWN_DOMAIN_MARKERS` matches the same constants. Existing owner searched first: `_txn`'s classifier family (cold audit's own DRY row: correct reuse apart from F4). **Mutation self-check (a run, not a test), scratch copy `scratchpad/fw1mut`, `_txn.__file__` printed inside the copy:** all four constants changed to `*_mut:`; the shells' texts followed (`cas_lost_mut: task is already superseded`); `test_task_ledger.py` + `test_task_guarded_shell_58.py` + `test_task_claimable_partition_58.py` + `test_supersede_reanchor_58.py`: 4 failed / 328 passed (log /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/fw1mut.log, TREE 74b21ebf…8b46); the 4 reds are NOT marker-related (2 = the namespace TypeError of the F7b try, since reverted; 2 = the #628 refusal-text legs, fixwave part 2). So a losing claim/CAS still raises its domain error under the mutated marker. |
| **F6** false docstrings/comments | DONE: `supersede_task` Returns (`SupersedeResult` fields) + Raises (`HubSupersedeRefusedError`, `SupersedeStragglerError`); `direct_dependents` (R10(iii)/R10(iv) text replaced); `claim_task` comment (`blocked_by` can change; the CAS guards it); `server._render_supersede_result` "`[]` by construction" (now states the create-after-read case); `updated_since` + `_COL_UPDATED_AT` comment name the re-anchor and heal stamps. **Left untouched on purpose:** `_refuse_a_cycle` (the "already RECORDED" sentence and its Args "pending" line — part 2 / am-17 §12.3). |
| **F7a** `_still_claimable` deleted | DONE. 0 callers by `git grep` over loremaster/, scripts/ (only its `def`). `lore_verify` still showed the symbol after my edit (index lag; reconcile exceeded 300 s) — I rely on the grep. |
| **F7b** `_guarded_append_fragment` uuid default | **RESIDUAL (lead ruling #20083: keep the reverted state; accepted residual)** — was: **STOP, not done** (your rule): all 4 production callers pass `namespace=`, but `test_task_guarded_shell_58.py::TestTheShellIsTheSeam64aGoverns::{test_where_conjuncts_are_each_PARENTHESISED_and_AND_joined,test_event_None_appends_NOTHING}` call the real shell without it. I made it required, saw those 2 TypeErrors, REVERTED the signature to the pre-wave default. Closing it needs those two tests to pass `namespace=` (contract author), then the default can go. Posted #20082. |
| **#622** `max_reanchor_dependents` | DONE: cites `scripts/probe_heal_curve_58.py` part C (not `probe_hub_txn_58.py`, schemaless) and all three §1.4 rows: 1 665 dep / 5 000 rows / 2.82 s committed; 3 332 / 10 001 / 10.15 s committed; 6 000 / 18 005 / 30.34 s `SurrealOutcomeUnknownError`, nothing committed; 5 700 interpolated, not measured. (I took the three rows from am-17 §1.4; I did not re-run part C.) |
Receipts — ALL on the scratch copy `scratchpad/fw1` (`scripts/scratch_copy.sh`; the two other-session scripts reset with `git checkout HEAD --`; `git status` there = my 4 production files + untracked reports only; `fw1`'s `tasks.py` is byte-identical to the live tree, `cmp` equal). TREE = `tree_id.sh <fw1>`:
| gate | command | log | EXIT | count | TREE |
|---|---|---|---|---|---|
| targeted | `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run pytest test_task_ledger test_supersede_reanchor_58 test_reanchor_58_r4_state test_reanchor_58_r53_bound_and_plans test_reanchor_58_r3_convergence test_task_claimable_partition_58 test_task_guarded_shell_58 test_findings test_retry_seam test_exhaustion_fates test_mcp_server test_sdk3_row_bound test_task_read_surface test_blocks_edge scripts/test_forgery_door_sweep -q -n 8 -p no:cacheprovider --timeout=300` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/fw1b.log | 1 | **3 failed, 2312 passed, 1 skipped** | c01c402b…8b308 |
| ruff | `uv run ruff check .` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/ruff_fw1b.log | 0 | All checks passed! | c01c402b…8b308 |
| typecheck | `scripts/typecheck.sh` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/typecheck_fw1b.log | 1 | 50 errors, all under loremaster/tests/ (64b findings tests + 58 `_run_guarded` + fixwave test files); none in production | c01c402b…8b308 |
| currency | `pending_contract_gate.py --currency --legs typecheck,ruff` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/currency_fw1b.log | 1 | ruff GREEN; typecheck RED_ADJUDICATED 50 (owners packet-58-fixwave, packet-64b-i-contract); **no RED_ORPHANED**; pytest NOT_RUN = the `--legs` selection | c01c402b…8b308 |
The 3 reds are the registered `packet-58-fixwave` ids: `test_supersede_reanchor_58.py::TestTheHubBoundIsDERIVED::test_one_past_the_cap_is_REFUSED_byte_inert_and_TEACHES[0]` and `[2]` (#628 served text) and `test_reanchor_58_r3_convergence.py::TestARowOverTheCapFailsTheBootLOUD::test_a_single_row_over_the_cap_raises_the_typed_packer_error_and_changes_NOTHING` (the fixwave's live-bound pin): all part 2. No other red in the set (the 64b findings tests in `test_findings.py`/`test_mcp_server.py` were not red in this scratch run). Superseded logs (void, tree changed): `fw1.log`, `ruff_fw1.log`, `typecheck_fw1.log`, `currency_fw1.log`.

## §FIXWAVE-2 (lead #20088; am-17 §12 as amended by §13; measured 2026-11-10, base HEAD `1130ac9` + my uncommitted diff in `tasks.py`, `server.py`)
| item | disposition |
|---|---|
| **(1) the ONE predicate (§13.2)** | DONE. `tasks.find_row_blocked_by_cycles(stored, proposed, asked, *, all_or_nothing) -> {row: cycle}`: one `networkx.strongly_connected_components` pass, `networkx.shortest_path` for the cycle, nodes/edges added sorted, same `[row, …, row]` shape (so `format_cycle_refusal` is untouched). Wired per §13.2's table: `_refuse_a_cycle` (create, create_many with `asked` = all pending; supersede with `minted={new_id}`, `all_or_nothing=True`; keeps its empty short-circuit, its ONE closure read, its raise) and the heal (`all_or_nothing=False`). `_drop_one_cycle_edge` DELETED. `find_blocked_by_cycle` unchanged, used by `server.py`'s batch-key check only. `_refuse_a_cycle`'s false "already RECORDED" sentence rewritten (it now says: `ensure_ready` records every legacy loop at every boot; the decision is the predicate). Existing owner searched first: `find_blocked_by_cycle` / `_drop_one_cycle_edge` (am-17 §13 withdraws their step-over as unsound, #631) and `networkx` (already a dependency, used by `_record_legacy_cycles`). `Packages considered:` networkx `strongly_connected_components` + `shortest_path` — **replace**, read in the installed package; nothing hand-rolled. |
| **(2) the heal** | DONE. `_plan_heal_rows` now also returns each row's proposed post-rewrite column and the superseded blockers it still names; new `_skip_cycle_closing_rows` does ONE `_bounded_dependency_graph` read seeded by every proposed blocker and ONE predicate call over the whole pending set, BEFORE `_pack_heal_chunks` (MP-3). A hit row is dropped from the plan WHOLE (column, edges, `updated_at` untouched; not counted; in no chunk); WARNING `task.backfill.straggler_would_close_cycle` with `database`, `task_id`, `blocker_ids`, `cycle` (`a -> b …`), `members`, every boot. No loop. The RELATE composition stays in `_reanchor_stragglers` (the derived-verb pins key on it). |
| **(3) leg D** | DONE. `_record_legacy_cycles(columns)` now runs right after `_read_mirror_state()`, BEFORE the nothing-missing early return (the old call after the phantom loop is removed). Existence probe and round-trip count unchanged. |
| **(4) served text** | DONE. F5: `server.py` claim text now "... can never resolve: block on the successor instead", comment above corrected. #625 a: `StragglerHealPackerError` says "heal chunk bound" and serves its live `row_cap` (= `min(WARN, HARD)`; no hardcoded number, no "transaction cap"). #625 b: `HubSupersedeRefusedError` drops "pinned KNOWN BOUND (58 F-1)" / "file it with lore_findings", keeps all four facts, adds "(finding #628)". #130(a): the `lore_tasks` `status` Field description (server.py) and the `query_tasks` docstring name the SUPERSEDED-row exclusion. (The second "exact-status filter" site in server.py at the `lore_findings` tool is a different ledger — not touched.) |
| **(5) requirements** | MP-3: predicate called once over the whole pending set, before packing (above). MP-2 closed by the one pass. |
**Mutation self-check (a run, not a test)** — scratch copy `scratchpad/fw2mut` (`tasks.__file__` printed inside the copy), `find_row_blocked_by_cycles` made to `return {}`: `test_reanchor_58_fixwave.py` + `test_cycle_write_path_04b3.py` + `test_blocks_edge.py` + `test_supersede_reanchor_58.py` (`--run-parked`) → **20 failed / 269 passed** (/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/fw2mut.log, TREE c84fe9b8…bd23). Reds cover every writer: create (`test_a_SELF_blocking_task_is_REFUSED`, `…through_PERSISTED_tasks…`, `…MINTED_cycle_COEXISTING_with_a_LEGACY_cycle…`), create_many (`…batch_whose_items_reference_each_others_IDS…`), supersede (`TestACycleClosingRewireIsRefusedWhole`, E3 ×2), heal (legs A, B, C, D2-i ×2, D2-ii, E1 ×2). Nothing cycle-related stayed green.
Receipts on the scratch copy `scratchpad/fw2` (`scratch_copy.sh` + the two other-session scripts reset; `git status` there = my two production files + untracked reports; `fw2`'s `tasks.py` `cmp`-equal to the live tree at the time of the copy):
| gate | command | log | EXIT | count | TREE |
|---|---|---|---|---|---|
| targeted | `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run pytest --run-parked <23 files: lead's list + the grep-derived covering set> -q -n 8 -p no:cacheprovider --timeout=300` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/fw2.log | 1 | **30 failed, 2455 passed, 1 skipped** | 1bfc28b9…45c49 |
| ruff | `uv run ruff check .` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/ruff_fw2.log | 0 | All checks passed! | 1bfc28b9…45c49 |
| typecheck | `scripts/typecheck.sh` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/typecheck_fw2.log | 1 | 50 errors, all under loremaster/tests/ | 1bfc28b9…45c49 |
| currency | `pending_contract_gate.py --currency --legs typecheck,ruff` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/currency_fw2.log | 1 | ruff GREEN; typecheck RED_ADJUDICATED 50 (packet-58-fixwave, packet-64b-i-contract); no RED_ORPHANED; pytest NOT_RUN = `--legs` | 1bfc28b9…45c49 |
Covering-set derivation: `git grep -l` over `loremaster/tests` and `scripts` for `_refuse_a_cycle|find_blocked_by_cycle|find_row_blocked_by_cycles|_reanchor_stragglers|_backfill_blocks_edges|HubSupersedeRefusedError|StragglerHealPackerError|task.backfill|_record_legacy_cycles|superseded_blockers|exact-status|query_tasks` (a textual grep, said out loud: `lore_impact` caps at 15 and its index lagged my edits this session), plus the lead's list. `--run-parked` was passed (the fixwave ids are parked reds otherwise deselected).
Result: **every `packet-58-fixwave` id GREEN; 0 other 58 reds.** The 30 reds are all 64b-i-parked: 28 in `test_mcp_server.py` (`TestToolBehaviourEndToEnd` findings tests, `TestResolveManyAcknowledgeManyDispatch`: the unbuilt governed `lore_findings` API) and the two `findings.py::_run_guarded` ids (`test_reanchor_58_r3_cas_seam`, `test_reanchor_58_r4_state`); 29 of 30 match registry `red_nodeids` by name (the 30th is the `[\t]` parametrization of a registered family; its yaml escape differs from the junit name).
Interim (non-receipt, live tree, before the pins landed): 587 passed / 1 failed = the R6 mutation pin that §13.5 item 3 re-keys; it is green in `fw2`.
Not done / bounds: the `find_row_blocked_by_cycles` closure read is MEDIUM-confidence per §13.2 (adversary's E1–E4 are the store check); `_guarded_append_fragment`'s uuid default stays (lead #20083).

## §FIXWAVE-3 (lead #20093 + #20095 + #20097; am-17 §14.2/§14.3/§14.7; measured 2026-11-10, base HEAD `9fd7f8c` + my uncommitted diff in `tasks.py`, `store/surreal.py`, and the header of `scripts/coldaudit_cycle_04b3_fork_a_refute.py`)
| item | disposition |
|---|---|
| **(1) the ONE input** | DONE. `TaskLedger._read_dependency_graph() -> {task id: blocked_by}`: one statement through the ordinary read seam (`self._query`), every row with a non-empty column. The statement text is ONE constant `_DEPENDENCY_COLUMNS_STATEMENT`, also the first statement of `_read_mirror_state` (no second spelling). `_refuse_a_cycle` and `_skip_cycle_closing_rows` call it; the heal reads it itself, inside `_skip_cycle_closing_rows`, after the backfill and only when planned rows exist. **Deleted:** `_bounded_dependency_graph`, `_CLOSURE_START_PARAM`, the "sound, not a heuristic" docstring (and the R7/closure paragraph of `_refuse_a_cycle`, now describing the one input). `TASK_BLOCKER_MAX_DEPTH` and `_TRAVERSAL_TIMEOUT` stay (`transitive_blockers`). Predicate and fates unchanged. |
| **(2) `task.guard.graph_large`** | DONE. WARNING from `_backfill_blocks_edges` (the boot already holds `columns`) when `len(columns) > TASK_GUARD_GRAPH_LARGE_ROWS` (= 20 000; **renamed from `GUARD_GRAPH_LARGE_ROWS` per #20095**, bare grep: 4 sites in tasks.py, none left under the old name), extras `database`, `rows`, `threshold`. The constant's comment and `_read_dependency_graph`'s docstring carry §14.1's measurement (300 / 2 400 / 19 200 rows; ~0.18 s) and the re-open instruction (re-run `scripts/probe_guard_input_58.py` at that size). ⚠ that probe file is not in the tree at `9fd7f8c` (`ls scripts | grep guard_input` empty) — the contract author's commit owns it; the docstrings cite its path. |
| **(3) #634** | DONE. `TaskLedger._supersede_lock: asyncio.Lock`, held by `supersede_task` around its WHOLE body (the guard reads through `_apply`), done by wrapping the existing body in `async with self._supersede_lock:` (no helper split, so the derived-verb/CAS-root pins see the same verb). `supersede_task`'s docstring and the lock's comment name finding #634 and its trigger (any deployment with two task-writing processes on one database; packet 39 consults it). No pin-the-miss test written. |
| **(4) arrow normalisation** | DONE. `find_blocked_by_cycle` reverses graphlib's list at its ONE return (graphlib lists blocker→dependent; the ledger's cycle records run row→its blocker); docstring says so. |
| **(5) riders** | `TaskLedger.query_tasks` docstring names the superseded-row exclusion (status/blocked filter). `store.apply.large_transaction` / `store.apply.transaction` now carry `source`: new keyword `source` on `SurrealStore._log_transaction_size` (default `_APPLY_SOURCE = "index_writer"`), the task ledger passes `_TASK_LEDGER_SOURCE = "task_ledger"`. Existing convention looked for first: the `label`/`url` extras of the `_txn` exhaustion record (am-13) and `database` extras of the ledger's own records; the size record had no composer field, so I added the one `source` extra. Stale "ONE shared detector" prose rewritten to §13.3's one-detector-per-question in `CYCLE_NOUN_*`'s comment, `find_blocked_by_cycle`'s docstring and `_record_legacy_cycles`'s docstring. |
| **`scripts/coldaudit_cycle_04b3_fork_a_refute.py`** (lead #20097) | DUAL header written at the top of the file in the live tree (ARCHIVED, FORK A overturned on measurement §14.1, what replaced it = `_read_dependency_graph` pinned in `test_reanchor_58_fixwave.py`, not runnable at HEAD, re-open trigger none). **Not moved, no git** (the lead moves it to `docs/plans/v2/receipts/2026-11-09-packet58/` at commit). In the gate copy `scratchpad/fw3` I moved it there so typecheck/currency reflect the committed layout. Without that move currency was RED_ORPHANED 1 (`TaskLedger has no attribute _bounded_dependency_graph`, /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/currency_fw3.log). |
**Mutation self-checks (runs, not tests; each copy `cmp`-synced to the live tree then ONE line mutated; provenance by the copy's own path):**
- `_read_dependency_graph` made `return {}` (`scratchpad/fw3mi`): `test_reanchor_58_fixwave.py` + `test_cycle_write_path_04b3.py` + `test_blocks_edge.py` + `test_supersede_reanchor_58.py` (`--run-parked`) → **21 failed / 281 passed** (/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/fw3mi.log); reds span create (`test_a_create_that_would_close_a_cycle_through_PERSISTED_tasks_is_REFUSED`, `…MINTED_cycle_COEXISTING…`), supersede (`TestACycleClosingRewireIsRefusedWhole`, E3 ×2), the heal (A, B, C, D2-i ×2, D2-ii, E1 ×2, `test_638_ii_leg_B…`) and the #635 long-chain/cycle legs.
- `async with self._supersede_lock:` → `async with asyncio.Lock():` (`scratchpad/fw3ml`): `test_reanchor_58_fixwave.py` + `test_supersede_reanchor_58.py` → **1 failed / 77 passed**, the failure is exactly `TestTwoConcurrentSupersedesOnOneLedgerCannotJointlyWriteACycle::test_634_one_of_two_concurrent_supersedes_is_refused_every_time` (/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/fw3ml.log).
**Receipts** on scratch copies at `9fd7f8c` (`scripts/scratch_copy.sh`; the two other-session scripts reset; `git status` there = `surreal.py`, `tasks.py`, plus the archived-script move):
| gate | command | log | EXIT | count | TREE |
|---|---|---|---|---|---|
| targeted | `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run pytest --run-parked <29 files> -q -n 8 -p no:cacheprovider --timeout=300` (files: the lead's list + the grep-derived covering set, see below) | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/fw3.log | 1 | **30 failed, 2431 passed, 1 skipped** | dcd3d939…56ea6122 (before the script move; the move touches no file this run executes) |
| ruff | `uv run ruff check .` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/ruff_fw3b.log | 0 | All checks passed! | 0103101b…ebc9 (archived layout) |
| typecheck | `scripts/typecheck.sh` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/typecheck_fw3b.log | 1 | 50 errors, all under loremaster/tests/; scripts leg OK | 0103101b…ebc9 |
| currency | `pending_contract_gate.py --currency --legs typecheck,ruff` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/currency_fw3b.log | 1 | ruff GREEN; typecheck RED_ADJUDICATED 50 (packet-58-fixwave, packet-64b-i-contract); **no RED_ORPHANED**; pytest NOT_RUN = `--legs` | 0103101b…ebc9 |
Covering-set derivation: `git grep -l` over `loremaster/tests` and `scripts` for `_refuse_a_cycle|find_blocked_by_cycle|find_row_blocked_by_cycles|_read_dependency_graph|_reanchor_stragglers|_backfill_blocks_edges|_supersede_lock|supersede_task|task.guard|_log_transaction_size|large_transaction|query_tasks|TASK_GUARD_GRAPH` (textual grep, said out loud; `lore_impact` lagged my edits), plus the lead's list; every listed file existed in the copy.
Result: **every `packet-58-fixwave` §14 id GREEN; the 30 reds are the 64b-i parked set** (28 in `test_mcp_server.py` `TestToolBehaviourEndToEnd` / `TestResolveManyAcknowledgeManyDispatch`, plus the two `findings.py::_run_guarded` ids); the one id not matched by name against the registry is the `[\t]` parametrization of a registered family (escape-form difference, as in part 2).
Interim (non-receipt, before the pins landed): 653 passed / 2 red = the ESC-1 closure-bound pin (re-keyed by the author's `9fd7f8c`) and `_run_guarded`.
Not done / bounds: `scripts/probe_guard_input_58.py` is cited by docstrings but absent from the tree at `9fd7f8c` (contract author / lead to commit it); `_guarded_append_fragment`'s uuid default is the accepted residual (#20083).

## §CLOSEOUT (lead #20100; second delta cold audit at `8679385`; measured 2026-11-10, base HEAD `9cdc3fd` + my uncommitted TEXT-only diff in `tasks.py`, `server.py`)
No logic change, no test edit (diff reviewed: every changed line is a docstring, comment, or the served `blocked` Field description string).
| finding | disposition |
|---|---|
| **F3** | `find_row_blocked_by_cycles`'s `stored` Arg now says: the WHOLE graph, every row with a non-empty column as `_read_dependency_graph` reads it in one statement (empty-column rows / phantom blockers are leaves). `_skip_cycle_closing_rows`' docstring: "ONE full-column read (`_read_dependency_graph`, every dependency-bearing row) and ONE predicate call". `server.py` comment above `create_many`'s `find_blocked_by_cycle` call: "ONE detector per QUESTION and ONE refusal SHAPE, all ledger-owned (R6, amended by am-17 §13.3 …)". |
| **F7** | `max_reanchor_dependents`' KNOWN BOUND names finding #628. |
| **F8** | `TASK_GUARD_GRAPH_LARGE_ROWS`' comment says what was measured (300 / 2 400 / 19 200 rows, am-17 §14.1, ~0.18 s at 19 200; and 0.18 s at 20 000 by the delta cold audit, `coldaudit-58-delta2.md` — your figure, I did not re-measure) and that a boot emitting the event has a graph beyond what was measured. |
| **F1** | The two comments pointing at `scripts/probe_guard_input_58.py` kept (the contract author commits the file). |
| **F17** | The lock's comment and `supersede_task`'s KNOWN BOUND say it precisely: a write from OUTSIDE this TaskLedger instance — another process, or another TaskLedger object in this process — is not serialised (#634); re-open trigger widened to "two task-writing processes (or two ledger objects) on one database". |
| **F18** | `lore_tasks` `blocked` Field description: "…unblocked (False) tasks; a blocked (or status) filter excludes SUPERSEDED tasks. Omit for no dependency filter." (mirrors `status`). |
Receipts — scratch copy `scratchpad/co1` (`scratch_copy.sh`, HEAD `9cdc3fd`; the two other-session scripts reset; `git status` there = `server.py`, `tasks.py` only; the fork-A script is already archived at that HEAD). TREE = `tree_id.sh <co1>`:
| gate | command | log | EXIT | count | TREE |
|---|---|---|---|---|---|
| targeted | `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run pytest --run-parked test_reanchor_58_fixwave test_supersede_reanchor_58 test_blocks_edge test_mcp_server test_task_read_surface test_query_tasks_bounded -q -n 8 -p no:cacheprovider --timeout=300` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/co1.log | 1 | **28 failed, 1076 passed, 1 skipped** | 13aac7fa…d2fc6 |
| ruff | `uv run ruff check .` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/ruff_co1.log | 0 | All checks passed! | 13aac7fa…d2fc6 |
| typecheck | `scripts/typecheck.sh` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/typecheck_co1.log | 1 | 50 errors, all under loremaster/tests/ | 13aac7fa…d2fc6 |
| currency | `pending_contract_gate.py --currency --legs typecheck,ruff` | /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b9f36f3f-43fd-4f52-a698-08baf2dc5d97/scratchpad/logs/currency_co1.log | 1 | ruff GREEN; typecheck RED_ADJUDICATED 50 (packet-58-fixwave + packet-64b-i-contract); no RED_ORPHANED; pytest NOT_RUN = `--legs` | 13aac7fa…d2fc6 |
The 28 reds are all `test_mcp_server.py` findings tests (`TestToolBehaviourEndToEnd`, `TestResolveManyAcknowledgeManyDispatch`) = the parked 64b-i set; 27 match registry names, the 28th is the `[\t]` escape-form variant of a registered family. No packet-58 test red.

## §STATE
done at the am-17 build. Nothing untried except: (a) a quiet-host re-measure of part E; (b) am-17 §9 grade runs on r5.3 not mine; (c) the §PROVENANCE row for am-17's three edits: `_pack_heal_chunks` bound + docstring, `_plan_heal_rows` DELETE + comment, `_supersede_transaction` DELETE + comment, `max_reanchor_dependents` docstring = **OWN** (ruled text, no reference counterpart).
