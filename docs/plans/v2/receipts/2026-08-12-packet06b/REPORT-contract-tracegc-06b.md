brief-base v13 read
brief project v7 read

> ⚠ ARCHIVED — SUPERSEDED ON E1 by `REPORT-contract-tracegc-06b-r2.md` + the lead's ruling:
> this report's §5 E1 recommended Reading X (purge in `reconcile()`); the lead ruled **E1 =
> Reading Y** (purge gated to the periodic tick only, never the initial startup sweep). E1 was
> correctly framed here as an ESCALATION, not a decision. Everything else (the `DELETE…LIMIT`
> PARSE-ERROR probe §3, the reference build §7, the builder obligations §8, E2=cutoff) STANDS and
> was inherited by r2 + the build. The shipped design is in r2 + REPORT-lead-06b.md.

# REPORT — contract-tracegc-06b (trace-retention GC, finding #193 / DD-1.c)

## SUMMARY BLOCK
- state: **done-with-escalations** — RED contract written, satisfiability + mutation proofs green; TWO forks surfaced for the lead (below).
- Graded: HEAD `8e4e440` · contract is RED against HEAD+stubs (5 behavior pins), GREEN against a reference build (scratch, provenance-asserted). Claims dated to `8e4e440`.
- deviation: added **two minimal contract stubs** to production (sanctioned by brief) so mypy is ZERO-NEW — `TelemetryConfig.trace_retention_days` field (no validator) + `SurrealStore.purge_traces_before` raising `NotImplementedError`. Exact edits in §7.
- deviation: edited an existing test home `tests/test_reconcile.py` (added `TestReconcilePurgesTraceRetention` + 2 imports) — sanctioned ("store/config test homes matching convention"); the reconcile engine's fakes live there.
- Packages considered: **none** — the specified mechanism is SurrealQL + stdlib `datetime`; the delete rides the store's existing `_query` seam (which rides the ONE `_txn` retry driver), so no retry/backoff is hand-rolled. No library was a candidate.
- Reuse ledger: 1 new production symbol (`purge_traces_before`), dispositioned HAND-ROLLED (it is the tree's FIRST row-GC — DD-1.c) reusing `_query`; see §6.
- decisions-needed (escalations, §5): **(E1)** `reconcile()` runs on the INITIAL STARTUP SWEEP too (`server.py:8971`, awaited during boot) — so "purge in reconcile()" runs a first-activation purge *during boot*, in tension with the brief's "periodic tick ONLY / must not block boot". **(E2)** store method interface `cutoff: datetime` (my pick) vs `retention_days: int` mirroring `trace_aggregates`.
- probe receipt (load-bearing): **`DELETE … LIMIT` is a PARSE ERROR on surrealdb-3.2.4** → the id-batched fallback is the mechanism; `ts < $cutoff` rides `trace_ts` (IndexScan / Iterate Index). Verbatim probe + output §3.
- RED node-id set (declared pre-run via `--collect-only`): §4. Satisfiability (reference build 15/15 reconcile, 86/86 config, 10/10 pins) + mutation matrix: §4.
- receipt pointers: probe §3 · pin inventory §2 · RED/GREEN + mutations §4 · escalations §5 · reference build (for the builder) §7 · builder obligations §8.

---

## 1. What I read (cited, not re-transcribed)
- **Ruling `docs/plans/v2/03b-deferred-design-rulings.md` §DD-1.c** (the work order) — read in full. Also DD-1.a (the shipped `trace_ts` index) and DD-1.b (the shipped windowed `trace_aggregates`).
- **Store reference `docs/reference/surrealdb-31-capabilities.md`**: §2 (the `ts < $cutoff` range = IndexScan vs `string::starts_with` = TableScan; `option<>` readers must not assume presence), §1.1 (INDEX ships `IF NOT EXISTS`), §1.4/§1.6 (a long-lived store is a DIRTY store; every test mints a virgin DB — so a boot-purge defect is only visible by seeding rows BEFORE the boot under test), §3 (`.query()` validates statement[0] only). Store law CITED in the test docstrings, never re-transcribed.
- Live code at `8e4e440`: `SurrealStore.trace_aggregates` (the adjacent windowed read, my interface mirror), `SurrealStore.record_trace` / `_TRACE_FIELD_SPECS` (`ts` is `datetime DEFAULT time::now()` — no READONLY/ASSERT, so a seed row can carry an explicit `ts`), `ReconcileEngine.reconcile` (holds `self._store` + `self._config`), `_trace_statements` (the `trace_ts` index), `TelemetryConfig` (`aggregate_window_days`, default 14), `_periodic_reconcile` + the initial `run_sweep` (E1).

## 2. Pin inventory → the 5 required requirements
File `loremaster/tests/test_trace_retention_gc.py` (new) + `tests/test_reconcile.py::TestReconcilePurgesTraceRetention` (added).

| # (brief) | requirement | pin(s) | kind |
|---|---|---|---|
| 1 | window bound is LOAD-BEARING (∀ over a SET straddling an explicit cutoff; `<` strict, boundary survives) | `TestPurgeRespectsTheWindow::test_purge_deletes_strictly_older_and_keeps_the_rest` | RED behavior |
| 2 | NEVER in boot; the reconcile tick does it | `TestBootNeverPurges::test_re_ensure_ready_deletes_no_trace_rows` (boot guard, dirty-store §1.6 pattern) **+** `TestReconcilePurgesTraceRetention::test_reconcile_purges_with_a_config_derived_cutoff` (the tick DOES purge) | guard (green on HEAD, RED on wrong build — mutation M3) + RED behavior |
| 3 | rides `trace_ts` — EXPLAIN receipt + TableScan control | `TestPurgeRidesTraceTsIndex::test_ts_range_scan_is_an_index_scan_on_trace_ts` | RECEIPT (green on HEAD — the DD-1.a index already exists; verifies the enabling scan) |
| 4 | config validator: retention ≥ aggregate window, default 90 | `TestTraceRetentionConfigValidator` (4 cases: default-90, equal, above, below-rejects-naming-both-fields) | 1 RED behavior + 3 stub-guards |
| 5 | batched — first activation drains ALL, no silent cap | `TestBatchedDrainLeavesNoResidual::test_first_activation_over_many_batches_drains_everything` (N=25, batch=10 → 3 internal batches; residual asserted 0) | RED behavior |
| — (INSTRUMENT-0 reach) | the delete's reach DERIVES from the window/config, not a hidden constant | `test_purge_deletes_strictly_older…` (reach = {ts<cutoff}, cutoff is a param) **+** `TestReconcilePurgesTraceRetention::test_reconcile_cutoff_tracks_config_retention` (two retentions → cutoff moves ~30d) | RED behavior |

**Interface this contract pins** (my design decision; alternatives in §5):
```
SurrealStore.purge_traces_before(*, cutoff: datetime, batch_size: int = …) -> int   # id-batched drain; returns count
TelemetryConfig.trace_retention_days: PositiveInt = 90  (DEFAULT_TRACE_RETENTION_DAYS) + model_validator(after): retention >= aggregate window
ReconcileEngine.reconcile(): cutoff = now(UTC) - timedelta(days=config.telemetry.trace_retention_days); await store.purge_traces_before(cutoff=cutoff)
```

## 3. The batched-DELETE spelling — VERIFIED (the #107 order: store ref → surrealql-tests → live probe)
Ruled order followed:
- **Rung 1 (store reference):** §2 gives the range-predicate/index fact but says nothing about `DELETE … LIMIT` or how to batch a delete.
- **Rung 2 (`lore_search tier=surrealql-tests`):** the engine's own CI specs show `DELETE record WHERE number = 21;` and `DELETE record;` (`tests/bench/mutate/delete_where.surql`, `tests/bench/crud/delete_1000.surql`) — **no `LIMIT` on any DELETE, and no batched-delete idiom.** The conjunction DD-1.c asked to verify is not spec-covered.
- **Rung 3 (live probe, `ws://127.0.0.1:18000`, throwaway DB, `:18500` never touched):** decisive.

**Findings (surrealdb-3.2.4+20260803.93ab219):**
1. **`DELETE t WHERE ts < $c LIMIT 2` is a PARSE ERROR** — `Unexpected token 'LIMIT', expected Eof`. **So DD-1.c's `DELETE … LIMIT` does not exist; the id-batched fallback IS the mechanism.**
2. **Id-batched fallback works:** `SELECT VALUE id FROM t WHERE ts < $c LIMIT n` (rides the index) → `DELETE t WHERE id IN $ids`. Loop until the SELECT returns empty. Termination is guaranteed: the `ts < cutoff` population strictly shrinks each iteration and no new such row appears (a fresh trace has `ts = now > cutoff`).
3. **`DELETE … WHERE` default-returns `[]`** — no count; use `RETURN BEFORE` for the deleted rows, or `len(ids)` from the SELECT (what the reference build does).
4. **A one-sided `ts < $cutoff` rides `trace_ts`:** SELECT EXPLAIN → `IndexScan` on `t_ts`; **DELETE EXPLAIN → `Iterate Index` on `t_ts`** (EXPLAIN works on DELETE too, 3.2.4); no-index control → `TableScan`. So pin 3 asserts on the DELETE's own plan, not just the SELECT.

**Instrument (verbatim, per brief-base §1 — a load-bearing measurement's tool survives IN the report):**
```python
# probe_trace_delete.py — run: uv run python probe_trace_delete.py  (ws://127.0.0.1:18000 ONLY)
import asyncio, json, os, uuid
from datetime import UTC, datetime, timedelta
from surrealdb import AsyncSurreal
URL="ws://127.0.0.1:18000/rpc"; USER="root"; PASS="spikeroot"; NS="lore_test"; DB=f"probe_{os.getpid()}_{uuid.uuid4().hex}"
async def main():
    c=AsyncSurreal(URL); await c.signin({"username":USER,"password":PASS})
    await c.query(f"DEFINE NAMESPACE IF NOT EXISTS {NS}"); await c.use(NS,DB); await c.query(f"DEFINE DATABASE IF NOT EXISTS {DB}"); await c.use(NS,DB)
    try:
        await c.query("DEFINE TABLE t SCHEMAFULL")
        await c.query("DEFINE FIELD ts ON t TYPE datetime DEFAULT time::now()")
        await c.query("DEFINE FIELD tool ON t TYPE string")
        await c.query("DEFINE INDEX t_ts ON t FIELDS ts")
        base=datetime(2026,1,1,tzinfo=UTC)
        for i in range(10): await c.query("CREATE t CONTENT { ts:$ts, tool:$tool }", {"ts":base+timedelta(days=i),"tool":f"tool{i}"})
        cut=base+timedelta(days=5)
        print("SELECT EXPLAIN", await c.query("SELECT * FROM t WHERE ts < $c EXPLAIN", {"c":cut}))
        print("DELETE EXPLAIN", await c.query("DELETE t WHERE ts < $c EXPLAIN", {"c":cut}))
        try:    print("DELETE LIMIT", await c.query("DELETE t WHERE ts < $c LIMIT 2 RETURN BEFORE", {"c":cut}))
        except Exception as e: print("DELETE LIMIT raised:", repr(e))
        ids=await c.query("SELECT VALUE id FROM t WHERE ts < $c LIMIT 3", {"c":cut})
        print("ids", ids); print("del", await c.query("DELETE t WHERE id IN $ids RETURN BEFORE", {"ids":ids}))
        await c.query("DEFINE TABLE u SCHEMAFULL"); await c.query("DEFINE FIELD ts ON u TYPE datetime DEFAULT time::now()")
        await c.query("CREATE u CONTENT { ts:$ts }", {"ts":base})
        print("control (no index)", await c.query("SELECT * FROM u WHERE ts < $c EXPLAIN", {"c":cut}))
        print("engine", await c.version())
    finally:
        await c.query(f"REMOVE DATABASE IF EXISTS {DB}"); await c.close()
asyncio.run(main())
```
**Observed output (abbreviated):** SELECT EXPLAIN → `{"operator":"IndexScan","attributes":{"index":"t_ts","access":"<d'2026-01-06…'"}}`; DELETE EXPLAIN → `[{"operation":"Iterate Index","detail":{"plan":{"index":"t_ts","to":{"inclusive":false,"value":"2026-01-06…"}}}}, {"operation":"Collector"}]`; DELETE LIMIT raised → `ValidationError … Parse error: Unexpected token 'LIMIT', expected Eof`; ids → `["t:mbrw…","t:qv3s…","t:v8er…"]`; control → `{"operator":"TableScan","predicate":"ts < d'2026-01-06…'"}`; engine → `surrealdb-3.2.4+20260803.93ab219`.

## 4. RED proof + satisfiability + mutation matrix
**Declared RED node-id set** (from `--collect-only`, declared BEFORE the run; RED against HEAD `8e4e440` + the §7 stubs):
```
test_trace_retention_gc.py::TestTraceRetentionConfigValidator::test_retention_below_window_is_rejected_naming_both_fields
test_trace_retention_gc.py::TestPurgeRespectsTheWindow::test_purge_deletes_strictly_older_and_keeps_the_rest
test_trace_retention_gc.py::TestBatchedDrainLeavesNoResidual::test_first_activation_over_many_batches_drains_everything
test_reconcile.py::TestReconcilePurgesTraceRetention::test_reconcile_purges_with_a_config_derived_cutoff
test_reconcile.py::TestReconcilePurgesTraceRetention::test_reconcile_cutoff_tracks_config_retention
```
HEAD+stubs run: **5 failed, 5 passed** (the 5 passed are 2 GUARDS + 3 field-scaffolding: `test_re_ensure_ready_deletes_no_trace_rows`, `test_ts_range_scan_is_an_index_scan_on_trace_ts`, and the default-90 / equal / above config cases — green because the stub field exists, RED-worthy behavior is the *validator* + the *purge* + the *wiring*). Without the stubs the whole set is RED (8 failed, 2 passed — the boot guard + EXPLAIN receipt); the stubs exist only to keep mypy ZERO-NEW.

**Satisfiability (reference build in a provenance-asserted scratch, `scripts/scratch_copy.sh`; `loremaster.__file__ = /tmp/lore-scratch-tracegc/loremaster/loremaster/__init__.py`, verified inside the copy):**
- 10/10 contract pins **PASS**.
- `tests/test_reconcile.py` full: **15 passed** (13 pre-existing + my 2) — no regression.
- `tests/test_config.py` full: **86 passed** — the validator is additive.
- (test_surreal_store / test_trace_telemetry not separately run: `purge_traces_before` and `trace_retention_days` are NEW symbols in neither suite's call graph; the store module is proven healthy because the passing live `gc_store` fixture constructs a real `SurrealStore` and runs `ensure_ready`.)

**Mutation matrix (reference build; each load-bearing pin reddens when its production line breaks; controls stay green):**
| mutation | target pin | result |
|---|---|---|
| M1 `ts < $cutoff` → `<= $cutoff` (strictness) | window ∀ | **RED** (boundary row wrongly deleted) |
| M2 `return` after ONE batch (silent cap) | drain | **RED**; control window pin **green** |
| M3 add `purge_traces_before(cutoff=now)` to `ensure_ready` | boot guard | **RED**; control window pin **green** |
| M4 validator condition → `False` (never rejects) | config reject | **RED**; other 3 config cases **green** |
| M5 delete the `purge_traces_before(...)` call in `reconcile()` | wiring ×2 | **RED** |
| M6 `days=config.telemetry.trace_retention_days` → `days=90` (hidden constant) | reach | **RED** ×2 |
Post-restore sanity: 10/10 green again.

## 5. ESCALATIONS (a contract author choosing between two readings is an escalation, not a decision)
**E1 — WHERE the purge runs vs "must not block boot" (the significant one).** The brief says *"on the PERIODIC reconcile-sweep tick ONLY (`reconcile.py::reconcile`) … NEVER in boot … a first-activation purge over months of rows must not block boot."* But `ReconcileEngine.reconcile()` is called on BOTH the periodic tick AND the **INITIAL STARTUP SWEEP** — `initial_summary = await watcher.run_sweep()` at `server.py:8971`, **awaited during startup**, and `run_sweep` funnels through `reconcile()`. So putting the purge in `reconcile()` (the brief's literal mechanism, and the `trace_aggregates` mirror) means the first-activation purge WOULD run during the initial startup sweep — i.e., during boot.
- Two readings, different code: **(X)** purge in `reconcile()` → runs on the initial sweep too (my contract pins this — simplest, mirror-consistent; the id-batched drain bounds each statement and `ensure_ready` stays DDL-only, so the deeper #131 "slow DDL boot" concern is honored). **(Y)** purge on the PERIODIC tick ONLY, gated OFF for the initial sweep (a flag on `reconcile()`, or wiring at `_periodic_reconcile`) → strictly "never during boot", but changes pin 2b's shape.
- **My recommendation: X**, because the batched drain + off-`ensure_ready` satisfies the real intent, and the initial sweep is already the heavy async part of startup (a full filesystem walk), not the DDL. **But this is the operator's call** — if "never during boot" is literal, the wiring needs gating and the contract's wiring pin must move to the `_periodic_reconcile` seam. Related: the initial `run_sweep` at `server.py:8971` is NOT wrapped in the swallow-and-log that `_periodic_reconcile` (`server.py:9312`) has — so under reading X a purge that raises during the initial sweep could surface at boot; the builder should make the purge resilient (or E1→Y removes the question).

**E2 — store interface `cutoff: datetime` vs `retention_days: int` (minor).** I pinned `purge_traces_before(*, cutoff: datetime, …)` — a pure mechanism ("delete older than this instant"), with the reconcile layer computing `cutoff = now - retention`. This makes the boundary (`<` strict, exact-cutoff row) precisely testable and keeps the RETENTION POLICY at the config/reconcile seam. The alternative mirrors `trace_aggregates(window_days=…)`: `purge_traces_before(retention_days: int)` computing the cutoff internally per-call. I chose `cutoff` for testability + separation; not a blocking fork, but the adversary/lead may prefer the `trace_aggregates` symmetry.

## 6. DRY / reuse ledger
| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `SurrealStore.purge_traces_before` | `lore_search "SurrealStore delete purge rows DELETE FROM query method"` | `delete_by_tier` / `delete_points` (chunk-scoped deletes over `_query`); **no trace GC exists** | **HAND-ROLLED** — DD-1.c states this is the tree's FIRST row-GC; it REUSES `_query` (which rides the ONE `_txn.retry_on_conflict` driver), so no retry/backoff/classification is cloned |
| `trace_retention_days` + validator | read `TelemetryConfig` + `RootConfig._check_policy_fields` (`config.py:296`) | the `aggregate_window_days` field pattern + the `@model_validator(mode="after")` idiom | **REUSED patterns** — field mirrors `aggregate_window_days`; validator mirrors `RootConfig`'s `model_validator` |
(Test-local helpers `_seed_trace`/`_remaining_ts`/`_count_before` and the `run()` laundering are per-file test scaffolding, not reusable production symbols.)

## 7. The reference build (for the builder — proven to green the contract)
Minimal STUBS added to the real tree (deviation, mypy zero-new): `config.py` — `DEFAULT_TRACE_RETENTION_DAYS = 90` + `trace_retention_days: PositiveInt = DEFAULT_TRACE_RETENTION_DAYS` (NO validator); `store/surreal.py` — `purge_traces_before(...)` raising `NotImplementedError`. The builder REPLACES both stubs with the real behavior below (proven correct in scratch):
```python
# config.py TelemetryConfig — the cross-field validator (RRoot pattern):
@model_validator(mode="after")
def _retention_covers_window(self) -> TelemetryConfig:
    if self.trace_retention_days < self.aggregate_window_days:
        raise ValueError(
            f"telemetry.trace_retention_days ({self.trace_retention_days}) must be "
            f">= telemetry.aggregate_window_days ({self.aggregate_window_days}) so the "
            f"served aggregate window can never outlive its retained trace data")
    return self

# surreal.py SurrealStore — id-batched drain (DELETE...LIMIT is a parse error, §3):
async def purge_traces_before(self, *, cutoff: datetime, batch_size: int = ...) -> int:
    total = 0
    while True:
        ids = await self._query(
            f"SELECT VALUE id FROM {TRACE_TABLE} "
            f"WHERE {TRACE_TS_FIELD} < $cutoff LIMIT {int(batch_size)}", {"cutoff": cutoff})
        if not ids:
            return total
        await self._query(f"DELETE {TRACE_TABLE} WHERE id IN $ids", {"ids": ids})
        total += len(ids)

# reconcile.py ReconcileEngine.reconcile() — after meta_set, before `return result` (see E1):
trace_cutoff = datetime.now(UTC) - timedelta(days=self._config.telemetry.trace_retention_days)
await self._store.purge_traces_before(cutoff=trace_cutoff)
```

## 8. BUILDER OBLIGATIONS (companion changes the contract requires; flag-not-fix, they are production)
1. **`FakeSurrealStore.purge_traces_before` must filter `self.db.traces`** (NOT `self.traces` — that is `_FakeSurrealDatabase`'s attribute, and a naive `self.traces` AttributeErrors EVERY existing reconcile test the moment `reconcile()` calls purge). Reference: filter `self.db.traces` by `ts >= cutoff`, return the count. Without this companion change, 13 existing reconcile tests regress (I hit this; the fix greened them 15/15).
2. **Name the batch-size constant** (I used a literal `1000` in the stub/reference) per "no hardcoded values" — e.g. a module constant in `surreal.py` or a config knob; the contract passes `batch_size` explicitly, so the value is free.
3. **Document `trace_retention_days`** in the `TelemetryConfig` class docstring (the stub carries only a comment).
4. **Resolve E1 before wiring** — if the operator rules "never during boot" (reading Y), the purge call moves off `reconcile()` to the periodic seam and the wiring pin follows; either way make the purge resilient if it stays on the awaited initial sweep.

## 9. Store/tool discipline
- Live tests hit `spike-surreal ws://127.0.0.1:18000` only, throwaway `unique_database()`; `:18500` never touched. Probe likewise.
- lore-first throughout (lore_search / lore_get_symbol / lore_impact / lore_read); ONE disclosed grep fallback — `grep` over `surreal_schema.py`/`config.py` for the retired-name-free constant definitions (`TRACE_*`, `DEFAULT_TELEMETRY_WINDOW_DAYS`) and the `DELETE`/`LIMIT`/`batch` seams in the store reference (a non-symbol textual seam — store-reference §-hunt — CLAUDE.md fallback case (b)/(c)). No lore weakness encountered; no friction filed.
- Scratch left at `/tmp/lore-scratch-tracegc` (throwaway, `scratch_copy.sh`) — disposable; probe at `/tmp/probe_trace_delete.py` (pasted verbatim §3). No git state mutated (the lead commits).
