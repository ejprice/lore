brief-base v13 read
brief project v7 read

# REPORT — contract-tracegc-06b-r2 (trace-retention GC, E1=Reading Y revision)

## SUMMARY BLOCK
- state: **done-with-escalation** — the lead's E1=Reading-Y ruling is implemented as a targeted delta; RED confirmed on HEAD+stubs, satisfiability green against a provenance-asserted reference build, full 9-leg mutation matrix PROOF-HELD. ONE fork surfaced (E-reach).
- Graded: HEAD `40744a6` · contract is RED on HEAD+stubs (6 behavior pins) / GREEN (13 pins) against a scratch reference build with the gated purge. Claims dated to `40744a6`.
- deviation: extended TWO existing stubs (mypy zero-new, same rationale as r1) — `ReconcileEngine.reconcile` gains a no-op `purge_traces: bool = False` param; `LiveWatcher.run_sweep` gains `purge_traces: bool = False` threaded verbatim to `reconcile`. Exact edits §2.
- deviation: added a NEW pin file-region `test_watcher.py::TestRunSweepThreadsTracePurgeGate` (Tier-2, the `run_sweep→reconcile` seam the ruling named) — beyond the two files the ruling named, justified in §2/§6.
- Packages considered: **none — no new mechanism specified** (the gate is a stdlib `bool` param; the purge rides the store's existing `_query`→`_txn` retry driver, unchanged from r1).
- Reuse ledger: **none — no new reusable symbol introduced** (the delta adds a gate PARAMETER to two existing methods + test pins; `purge_traces_before`/`trace_retention_days` are r1's symbols, unchanged). Full ledger §7.
- decisions-needed: **E-reach (§8)** — the property "purge fires on periodic, NEVER on the initial sweep" is fully pinned at the `reconcile` gate + the `run_sweep` threading, but the LAST MILE (which CALLER passes `purge_traces=True`) lives in TWO duplicated production daemons (`scout._periodic_reconcile` AND `server._periodic_reconcile`) — the ruling named only `server`. Fork: pin both callers now, or accept a mutation-proven builder obligation + named re-open trigger. Recommendation + exact seams in §8.
- receipt pointers: delta §2 · RED set §3 · satisfiability §4 · 9-leg mutation matrix §5 · FINAL Reading-Y reference build (builder) §6 · builder obligations §7 · E-reach fork §8 · store/tool discipline §9.

---

## 1. What I read (cited, not re-transcribed)
- The lead ruling in my spawn brief (E1=Reading Y; E2 accept `cutoff: datetime`; keep retention 90d + the validator + all five requirement pins + the reach pin unchanged).
- The prior contract + report: `test_trace_retention_gc.py`, `test_reconcile.py::TestReconcilePurgesTraceRetention`, and `REPORT-contract-tracegc-06b.md` §2–§8 (the pin inventory, the `DELETE … LIMIT` PARSE-ERROR probe, the RED/satisfiability/6-mutation matrix, escalations, the reference build, builder obligations). Inherited, not re-derived.
- Store law `docs/reference/surrealdb-31-capabilities.md`: §1.4/§1.6 (a long-lived store is a DIRTY store; every test mints a virgin DB — a boot-purge defect is only visible by seeding BEFORE the boot under test), §2 (`ts < $cutoff` range = IndexScan; `option<>` readers must not assume presence), §3 (`.query()` validates statement[0] only). Cited in test docstrings, never re-transcribed.
- Live code at `40744a6`: `ReconcileEngine.reconcile` (holds `self._store`+`self._config`, imports `UTC, datetime` — NOT `timedelta`), `LiveWatcher.run_sweep` (the chokepoint both the initial sweep and the periodic tick funnel through), and the FIVE production `run_sweep`/`reconcile` call sites (§8): `scout.Scout.start`→run_sweep (initial), `scout.Scout._periodic_reconcile`→run_sweep (periodic), `scout.Scout.handle_command`→run_sweep (command), `server.py:8971`→run_sweep (initial), `server._periodic_reconcile`→run_sweep (periodic), plus `LiveWatcher.on_kernel_overflow`→reconcile (overflow) and `server.py:4801/4803` (forced `lore_index(reconcile=True)`).

## 2. What I changed (the targeted delta — E1=Reading Y)
The prior contract pinned the purge in `reconcile()` unconditionally (Reading X), which would run a first-activation purge during the AWAITED initial startup sweep (`run_sweep→reconcile` at boot). The ruling (Reading Y) gates it OFF the initial sweep and ON the periodic tick. The seam is a `purge_traces: bool` gate on `reconcile`, threaded through `run_sweep`, with the purge LOGIC kept in `index/reconcile.py` per DD-1.c. The gate DEFAULT is `False`, so EVERY existing caller (initial sweep, overflow recovery, forced reconcile, command reconcile) is no-purge automatically — "allowlist the safe": exactly the periodic loops opt in.

**Production stubs (mypy zero-new — sanctioned deviation, same rationale as r1):**
- `loremaster/index/reconcile.py` — `reconcile(self, *, purge_traces: bool = False)`; body UNCHANGED (ignores the gate → no purge). Docstring states the gate contract + points at the RED pin. The BUILDER fills the gated purge body (§6).
- `loremaster/index/watcher.py` — `run_sweep(self, *, purge_traces: bool = False)`; threads it verbatim: `return await self._reconcile_engine.reconcile(purge_traces=purge_traces)`. Pure plumbing (the DECISION is in `reconcile`); the threading is a mutation-proven guard (§5 M8/M8b).

**Contract pins:**
- `test_reconcile.py::TestReconcilePurgesTraceRetention` (Tier 1 — the ruling's core, daemon-agnostic gate):
  - `test_gated_periodic_reconcile_purges_with_a_config_derived_cutoff` — was `test_reconcile_purges_with_a_config_derived_cutoff`; now calls `reconcile(purge_traces=True)` (the GATED periodic path).
  - `test_gated_reconcile_cutoff_tracks_config_retention` — was `test_reconcile_cutoff_tracks_config_retention`; now `reconcile(purge_traces=True)`; the INSTRUMENT-0 reach pin (two retentions → cutoff moves).
  - **NEW** `test_ungated_initial_sweep_does_not_purge_but_gated_does` — the ruling's required initial-sweep-no-purge pin. ONE engine/store: `reconcile()` (the initial sweep's call shape) → `cutoffs == []` (assert first, catches the ungated-purge wrong build directly); then `reconcile(purge_traces=True)` → `len(cutoffs) == 1`. RED on HEAD+stub because the stub ignores the gate (the gated leg records 0).
- `test_watcher.py::TestRunSweepThreadsTracePurgeGate` (Tier 2 — the `run_sweep→reconcile` seam the ruling named as a pointer): `run_sweep(purge_traces=True)`→`reconcile(purge_traces=True)`; default `run_sweep()`→`reconcile(purge_traces=False)`. Green-on-stub threading guards (the stub threads correctly), mutation-proven both directions (§5).

**Unchanged (ruling: keep):** retention 90d (`DEFAULT_TRACE_RETENTION_DAYS`), the cross-field validator, all four config pins, the window ∀ pin, the batched-drain pin, the `trace_ts` EXPLAIN receipt, and `TestBootNeverPurges` (the `ensure_ready` DDL-boot no-purge half — still correct: the purge lives in `reconcile`, never in `ensure_ready`). The store interface stays `purge_traces_before(*, cutoff: datetime, batch_size)` (E2, author's pick, no change). The `DELETE … LIMIT` PARSE-ERROR probe / id-batched mechanism is inherited verbatim from `REPORT-contract-tracegc-06b.md` §3 (re-run implicitly — the reference build's drain greens the live window+drain pins).

## 3. RED proof (declared BEFORE the run, from `--collect-only`)
**Declared RED node-ids on HEAD+stubs** (behavior pins; the feature body is absent so the gate never flips):
```
test_trace_retention_gc.py::TestTraceRetentionConfigValidator::test_retention_below_window_is_rejected_naming_both_fields
test_trace_retention_gc.py::TestPurgeRespectsTheWindow::test_purge_deletes_strictly_older_and_keeps_the_rest
test_trace_retention_gc.py::TestBatchedDrainLeavesNoResidual::test_first_activation_over_many_batches_drains_everything
test_reconcile.py::TestReconcilePurgesTraceRetention::test_gated_periodic_reconcile_purges_with_a_config_derived_cutoff
test_reconcile.py::TestReconcilePurgesTraceRetention::test_ungated_initial_sweep_does_not_purge_but_gated_does
test_reconcile.py::TestReconcilePurgesTraceRetention::test_gated_reconcile_cutoff_tracks_config_retention
```
**Observed (HEAD+stubs):** gc file `3 failed, 5 passed`; reconcile class `3 failed`; combined **6 failed, 5 passed** — matches the declared set EXACTLY. The 5 green are guards/scaffolding proven only by mutation: 3 config stub-guards (default-90 / equal / above), the `ensure_ready` boot guard (`TestBootNeverPurges`), the `trace_ts` EXPLAIN receipt. The Tier-2 `test_watcher.py::TestRunSweepThreadsTracePurgeGate` legs are green-on-stub threading guards (2 passed) — NOT in the RED set (declared as guards, §5 M8/M8b prove them).
- **The new pin is RED on HEAD+stubs for the RIGHT reason:** `test_ungated_initial_sweep_does_not_purge_but_gated_does` fails on its SECOND assert (the gated leg records 0 purge because the stub ignores the gate) — its first assert (ungated → no purge) already holds even on the stub, so a HEAD run cannot pass it vacuously.

## 4. Satisfiability (reference build in a provenance-asserted scratch)
Scratch via `./scripts/scratch_copy.sh /tmp/lore-scratch-tgc-r2b`; **`loremaster.__file__ = /tmp/lore-scratch-tgc-r2b/loremaster/loremaster/__init__.py`** (asserted `is_relative_to` the scratch root at every run — #140 provenance receipt printed in the run output). The reference build (§6) replaces the config + store stubs with real behavior and fills the `reconcile` gated purge body.
- Full trace-GC contract: **13 passed** (`test_trace_retention_gc.py` 8 + `test_reconcile.py::TestReconcilePurgesTraceRetention` 3 + `test_watcher.py::TestRunSweepThreadsTracePurgeGate` 2).
- No regression: `test_reconcile.py` + `test_config.py` + `test_watcher.py` full = **135 passed** (the validator is additive; the `run_sweep`/`reconcile` param defaults preserve every existing caller).
- Post-mutation sanity: 13/13 green again, provenance re-asserted.

## 5. Mutation matrix — 9 legs, ALL PROOF-HELD (via `scripts/mutation_proof.py`)
Each row: mutate one production line in the scratch, declare the expected-RED node-ids BEFORE the run, `mutation_proof.py` diffs observed-vs-declared BOTH ways (unexpected reds AND declared-still-green both FAIL) and restores byte-exact (md5 confirmed). "PROOF HELD — declared RED set fired EXACTLY" on every leg.

| # | mutation (file) | target pin(s) | result |
|---|---|---|---|
| M1 | `ts < $cutoff` → `<=` (surreal.py) | window ∀ | **RED** (only); others green |
| M2 | `return total` after ONE batch (surreal.py) | drain | **RED** (only); window green (single-batch fixture) |
| M3 | purge inside `ensure_ready` (surreal.py) | boot (`TestBootNeverPurges`) | **RED** (only); fixture setup boots on empty DB, so no collateral |
| M4 | validator `if False` (config.py) | config below-window reject | **RED** (only); other 3 config green |
| M5 | remove the gated purge CALL (reconcile.py) | **3 gated pins** | **RED** ×3 (periodic + reach + gated leg of the new pin) |
| M6 | `days=config…` → `days=90` hidden constant (reconcile.py) | reach ×2 | **RED** (periodic cutoff + cutoff-tracks-config); the new pin's count-only leg stays green |
| **M7** | **`if purge_traces:` → `if True:`** (reconcile.py) — the ruling's required "purge fires on the ungated/initial sweep" | **initial-sweep-no-purge pin ONLY** | **RED** (only); both gated pins GREEN — clean discrimination |
| M8 | `run_sweep` DROPS the flag → `reconcile()` (watcher.py) | `run_sweep(True)` threading leg | **RED** (only) — periodic would never purge |
| M8b | `run_sweep` HARDCODES `reconcile(purge_traces=True)` (watcher.py) | default `run_sweep()` threading leg | **RED** (only) — would purge on the AWAITED initial sweep (the exact boot-block Reading Y forbids) |

M1–M6 are the prior contract's matrix, still holding (M5/M6 now redden the 3-pin gated set / 2-pin reach set respectively). M7 is the ruling's new mutation. M8/M8b prove the `run_sweep` threading discriminates the two reach failure directions.

## 6. The FINAL reference build (for the builder — proven to green the 13-pin contract)
The builder replaces the r1 config + store stubs (unchanged from `REPORT-contract-tracegc-06b.md` §7) and fills the `reconcile` gated purge body + keeps the `run_sweep` threading (already in the stub). Proven correct in `/tmp/lore-scratch-tgc-r2b`:
```python
# config.py TelemetryConfig — the cross-field validator (unchanged from r1 §7):
@model_validator(mode="after")
def _retention_covers_window(self) -> TelemetryConfig:
    if self.trace_retention_days < self.aggregate_window_days:
        raise ValueError(
            f"telemetry.trace_retention_days ({self.trace_retention_days}) must be "
            f">= telemetry.aggregate_window_days ({self.aggregate_window_days}) so the "
            f"served aggregate window can never outlive its retained trace data")
    return self

# surreal.py SurrealStore.purge_traces_before — id-batched drain (unchanged from r1 §7;
# DELETE...LIMIT is a 3.2.4 PARSE ERROR):
async def purge_traces_before(self, *, cutoff: datetime, batch_size: int = 1000) -> int:
    total = 0
    while True:
        ids = await self._query(
            f"SELECT VALUE id FROM {TRACE_TABLE} "
            f"WHERE {TRACE_TS_FIELD} < $cutoff LIMIT {int(batch_size)}", {"cutoff": cutoff})
        if not ids:
            return total
        await self._query(f"DELETE {TRACE_TABLE} WHERE id IN $ids", {"ids": ids})
        total += len(ids)

# index/reconcile.py — add `from datetime import ... timedelta`; the GATED purge, at the
# END of reconcile() (after the last-sweep meta_set, before `return result`):
async def reconcile(self, *, purge_traces: bool = False) -> ReconcileSummary:
    ...
    if purge_traces:
        trace_cutoff = datetime.now(UTC) - timedelta(
            days=self._config.telemetry.trace_retention_days)
        await self._store.purge_traces_before(cutoff=trace_cutoff)
    return result

# index/watcher.py — run_sweep threads the gate (already in the stub, KEEP it):
async def run_sweep(self, *, purge_traces: bool = False) -> ReconcileSummary:
    async with self._lock:
        return await self._reconcile_engine.reconcile(purge_traces=purge_traces)
```

## 7. Builder obligations (carried from r1 §8 + NEW for Reading Y)
Carried, unchanged:
1. **`FakeSurrealStore.purge_traces_before` must filter `self.db.traces`** (NOT `self.traces`) by `ts >= cutoff`, returning the count — else 13 existing reconcile tests AttributeError the moment `reconcile(purge_traces=True)` calls purge. (The contract's `_install_purge_spy` shadows the store with an INSTANCE attribute, so the fake-trio reconcile pins pass without this — but the LIVE store path and any test that lets the real fake method run need it.)
2. **Name the batch-size constant** (the stub/reference use a literal `1000`) per "no hardcoded values" — a module constant in `surreal.py` or a config knob; the contract passes `batch_size` explicitly so the value is free.
3. **Document `trace_retention_days`** in the `TelemetryConfig` class docstring (the stub carries only a comment).

NEW (Reading Y):
4. **Wire the PERIODIC callers to `run_sweep(purge_traces=True)`** — this is the property's last mile and it lives in TWO daemons (see §8, E-reach). The initial-sweep callers stay `run_sweep()` bare (automatic via the `False` default). The overflow / command / forced-reconcile callers stay bare (correct — periodic tick ONLY).
5. **DRY note:** DO NOT clone a `run_sweep(purge_traces=True)` "pattern" across the two `_periodic_reconcile` bodies as prose — if the duplication is kept, it is a design decision (§8); if collapsed, prove sharing by mutation.

Reuse ledger (§6 of brief-base): **no new reusable symbol** — the delta adds a `bool` gate PARAMETER to two existing methods and test pins. `purge_traces_before` and `trace_retention_days` are r1's symbols (r1's ledger dispositioned them: `purge_traces_before` HAND-ROLLED reusing `_query`; the config field/validator REUSED the `aggregate_window_days` + `RootConfig.model_validator` patterns). No search was owed because nothing new was introduced.

## 8. ESCALATION — E-reach (the fork; a contract-author choice between two readings/scopes is an escalation, not a decision)
**The property "purge fires on the periodic tick, NEVER on the initial startup sweep" is pinned at the GATE (`reconcile`) and its THREADING (`run_sweep`) — but its LAST MILE (which CALLER passes `purge_traces=True`) is unpinned, and it lives in TWO duplicated production daemons.** The ruling named only `server.py`. Ground truth at `40744a6`:

- **`loremaster.scout.Scout`** (the write-role daemon): `start()`→`await self._watcher.run_sweep()` (initial, bare — correct), `_periodic_reconcile()`→`await self._watcher.run_sweep()` (periodic — **must become `run_sweep(purge_traces=True)`**), `handle_command()`→`run_sweep()` (command — bare, correct).
- **`loremaster.server`** (the all-mode lifespan, `_periodic_reconcile` is `live` — referenced by `build_app_context`): `server.py:8971`→`run_sweep()` (initial, bare — correct), `server._periodic_reconcile`→`run_sweep()` (periodic — **must become `run_sweep(purge_traces=True)`**).

So the reach attack on a `reconcile`-only pin is real: a build where NEITHER `_periodic_reconcile` passes `True` compiles, greens Tier-1 + Tier-2, and **never purges** (P-periodic silently violated); a build where an initial-sweep caller passes `True` would purge at boot (P-initial violated). Tier-2 (M8/M8b) closes the `run_sweep` seam, but not the caller seam. This is also a **ONE-IMPLEMENTATION** concern: two cloned `_periodic_reconcile` bodies needing the same "pass the gate" policy.

**Why I stopped at Tier-1 + Tier-2 rather than pinning the callers:** right-sizing (repo law) — this is a boot-latency housekeeping purge (the batched drain bounds each statement, so even a mis-gated boot purge is seconds, not data loss/security), and the operator's anti-spiral lesson says surface the value-vs-depth trade rather than default to max machinery across `test_scout.py` + `test_mcp_server.py` for a trivial surface. The bound is enumerable (two callers), not adversarial-receding.

**The fork (lead's call), with a recommendation:**
- **(A) Pin the callers now** (reach-complete). Exact, cheap seams already exist: `test_scout.py` has a `_FakeWatcher` whose `run_sweep` I would extend to record the `purge_traces` kwarg → pin `Scout._periodic_reconcile`→True + `Scout.start` initial→bare; `test_mcp_server.py` already spies `ctx.reconcile_engine.reconcile` (≈:3206) and stubs `run_sweep` (≈:849) → pin `server._periodic_reconcile`→True + the initial sweep→bare. ~4 small pins across the two files.
- **(B) Accept a mutation-proven builder obligation** (obligation #4) — the gate+threading are the pinned mechanism; the caller wiring is a two-site enumerated obligation with a **named re-open trigger: any third `_periodic_reconcile` (a new deployment role/daemon), OR any deploy where trace-table growth is observed unbounded (P-periodic silently off).**
- **My recommendation: (A)** — the seams exist and are cheap, the reach attack is legitimate, and pinning both callers also erects a guard against the scout/server duplication drifting. **But the DUPLICATION itself (should the two `_periodic_reconcile` loops share one helper?) is a design question above a contract author** — that half goes to the operator/lead regardless of A/B.

## 9. Store / tool discipline
- Live tests hit `spike-surreal ws://127.0.0.1:18000` ONLY (the `_surreal_harness` default, throwaway `unique_database()`); `:18500` never touched.
- lore-first throughout: `lore_recall` (scout/server architecture), `lore_impact` (`server._periodic_reconcile` liveness), `lore_get_symbol` (`ReconcileEngine.reconcile`), `lore_search` (run_sweep / Scout seams). ONE disclosed grep fallback — `grep` over `server.py`/`watcher.py`/`scout.py` for the `run_sweep`/`_periodic_reconcile`/`reconcile(` CALL-SITE enumeration (a cross-cutting "who calls this across daemons" map — CLAUDE.md fallback case (c)) and for the store-constant names in the scratch. No lore weakness encountered; no friction filed.
- No git state mutated (the lead commits). Scratch left at `/tmp/lore-scratch-tgc-r2b` (disposable `scratch_copy.sh` copy, NOT a git worktree). Mutation instrument = the committed `scripts/mutation_proof.py`; probe from r1 is `REPORT-contract-tracegc-06b.md` §3 (pasted verbatim there).
