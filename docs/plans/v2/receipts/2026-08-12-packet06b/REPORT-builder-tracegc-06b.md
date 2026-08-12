brief-base v13 read
brief project v7 read

# REPORT — builder-tracegc-06b (trace-retention GC build, finding #193 / DD-1.c)

## SUMMARY BLOCK
- state: **done** — feature built, Fork-A caller reach pinned + wired, full trace-GC
  contract GREEN, no regression, gates clean, 7 mutation proofs PROOF-HELD.
- deviation: fixed `test_reconcile.py::_install_purge_spy` type-ignore code
  `[attr-defined] → [method-assign]` — a mypy regression my fake companion (adding
  `FakeSurrealStore.purge_traces_before`) directly caused; minimal fix, §D.
- deviation: added `TestPurgeTracesBeforeFake` (test_surreal_fakes.py) so the fake
  companion is a PIN, not untested infra — beyond the ~4 caller pins, justified §C.
- deviation (R1): added `_TRACE_PURGE_ID_SELECT` module template in surreal.py (shared
  by the store AND the EXPLAIN receipt) and REMOVED the receipt's ts-DELETE-EXPLAIN leg
  (the purge deletes by `id`, not `ts`) — removed-behavior adjudication §E.
- Packages considered: **none — no new mechanism** (stdlib `datetime` + SurrealQL; the
  drain rides the store's existing `_query` → the ONE `_txn.retry_on_conflict` driver, so
  no retry/backoff/classification is hand-rolled).
- Reuse ledger: 2 new production symbols (`_TRACE_PURGE_BATCH_SIZE`,
  `_TRACE_PURGE_ID_SELECT`), both dispositioned HAND-ROLLED; §F.
- Graded: built on HEAD `40744a6` + the inherited uncommitted r1/r2 stubs; feature GREEN
  against this tree. (`Graded:` proper is for verdict-reports — I am a builder.)
- decisions-needed: **one BOUND to note, not a fork** — the caller pins are a hand-list
  of the 2 current daemons; named re-open trigger = a 3rd `_periodic_reconcile`. The
  scout/server `_periodic_reconcile` DUPLICATION (#366) is a design question above me, out
  of scope; I wired both correctly without cloning a "pattern". §G.
- receipt pointers: caller pins RED→GREEN §A · feature impl §B · companion §C · deviation
  §D · R1 §E · DRY §F · reach bound §G · mutation matrix §H · gates §I · footprint §J.

---

## A. Fork-A caller pins — RED-first, then GREEN after wiring
The adversary graded the contract INSUFFICIENT on exactly ONE gap: the property "purge fires
on the periodic tick, NEVER on the awaited initial startup sweep" is pinned at the `reconcile`
GATE and the `run_sweep` THREADING, but the LAST MILE — which CALLER sets the gate — was
unpinned, and it lives in TWO duplicated daemons. Two directions × two daemons = 4 pins.

**New pins added** (2 classes):
- `test_scout.py::TestTracePurgeGateReachesTheRightCallers` — `_FakeWatcher.run_sweep` widened
  to `(*, purge_traces=False)` and records `run_sweep_purge_flags`; `_FailingWatcher.run_sweep`
  widened too (else the wired periodic caller TypeErrors it — residual R3). A `_SweepOnceSleep`
  (returns once, then parks) drives exactly ONE periodic iteration.
  - `test_periodic_reconcile_passes_the_trace_purge_gate` (SP) — periodic → `True`.
  - `test_initial_startup_sweep_does_not_pass_the_purge_gate` (SI) — initial → bare (guard).
- `test_mcp_server.py::TestServerTracePurgeGateReachesTheRightCallers`:
  - `test_server_periodic_reconcile_passes_the_trace_purge_gate` (VP) — drives module-level
    `server._periodic_reconcile` directly with a recording watcher (interval 0, one iteration).
  - `test_server_initial_sweep_does_not_pass_the_trace_purge_gate` (VI) — spies `LiveWatcher.
    run_sweep` across a real `build_app_context(start_tasks=True)` startup (guard).

**Declared RED node-ids BEFORE running** (from `--collect-only`; the 2 periodic callers are
bare on HEAD+stubs → RED; the 2 initial-bare are guards → green now, mutation-proven §H):
```
loremaster/tests/test_scout.py::TestTracePurgeGateReachesTheRightCallers::test_periodic_reconcile_passes_the_trace_purge_gate
loremaster/tests/test_mcp_server.py::TestServerTracePurgeGateReachesTheRightCallers::test_server_periodic_reconcile_passes_the_trace_purge_gate
```
**Observed RED (pre-wiring, bare callers):** `2 failed, 2 passed` — matched the declared set
EXACTLY, RED for the RIGHT reason (SP: `assert False is True` — periodic caller passed bare;
VP: `seen == [False]` — same). The 2 initial guards PASSED.

**Wiring (greens the periodic pins):**
- `scout.py::Scout._periodic_reconcile` → `await self._watcher.run_sweep(purge_traces=True)`
  (initial sweep in `start()` + `handle_command` left BARE).
- `server.py::_periodic_reconcile` (module-level) → `await watcher.run_sweep(purge_traces=True)`
  (the initial sweep at the awaited-startup site + the forced `lore_index` sweep left BARE).

**After wiring:** all 4 caller pins GREEN. Full 18-pin trace-GC set (13 inherited + 4 caller +
1 fake) = **18 passed** (§I).

## B. Feature implementation (the 3 stub bodies + the gate wiring)
Filled VERBATIM from the r2 §6 / adversary §A reference build, plus obligations:
- **`config.TelemetryConfig._retention_covers_window`** — `@model_validator(mode="after")`
  raising `ValueError` naming BOTH fields when `trace_retention_days < aggregate_window_days`.
  `trace_retention_days` documented in the class docstring incl. the **R2 deploy note** (an
  existing YAML with `aggregate_window_days > 90` now fails to load — a loud, deliberate reject).
- **`store.surreal.SurrealStore.purge_traces_before`** — id-batched drain
  (`_TRACE_PURGE_ID_SELECT` → `DELETE ... WHERE id IN $ids`, looped until the page is empty).
  `DELETE ... LIMIT` is a 3.2.4 PARSE ERROR (inherited probe, `REPORT-contract-tracegc-06b.md`
  §3); the one-sided `ts < $cutoff` SELECT rides `trace_ts` (store ref §2). Batch default =
  the named `_TRACE_PURGE_BATCH_SIZE` (obligation #2 — no literal `1000`). Reuses `_query`
  (the ONE `_txn` retry driver).
- **`index.reconcile.ReconcileEngine.reconcile`** — added `from datetime import ... timedelta`;
  the GATED purge before `return result`: `if purge_traces: cutoff = now(UTC) - timedelta(days=
  config.telemetry.trace_retention_days); await store.purge_traces_before(cutoff=cutoff)`.
- **`index.watcher.LiveWatcher.run_sweep`** — the `purge_traces` threading was already in the
  r2 stub (`return await self._reconcile_engine.reconcile(purge_traces=purge_traces)`); KEPT
  unchanged (no edit by me).

## C. Companion changes (builder obligations)
1. **`FakeSurrealStore.purge_traces_before`** (obligation #1) — filters `self.db.traces`
   KEEPING `ts >= cutoff` (boundary survives, `<` strict), returns the DELETED count;
   `batch_size` accepted for signature compat but inert (an in-memory filter needs no batching).
   `_TRACE_PURGE_BATCH_SIZE` imported from the store (matches the fake's existing `_MAX_HYBRID_K`
   import pattern). NO test currently exercises the real fake method (the contract's
   `_install_purge_spy` shadows it; the caller pins use watcher fakes) — so I added
   **`TestPurgeTracesBeforeFake`** (a ∀ window pin at the fake level) so it is a PIN, not
   untested infra ("an oracle whose logic cannot FAIL is not an oracle"), and mutation-proven
   §H (MFK).
2. **Batch-size constant named** (#2) — `_TRACE_PURGE_BATCH_SIZE = 1000`.
3. **`trace_retention_days` documented** (#3) — TelemetryConfig docstring + R2 deploy note.
4. **Both periodic callers wired** (#4, Reading Y) — §A. #366 note: both `_periodic_reconcile`
   bodies call the same `run_sweep(purge_traces=True)`; I wired each correctly WITHOUT cloning a
   prose "pattern" — the duplication itself is out of scope (§G).

## D. Deviation — the `_install_purge_spy` type-ignore code
Adding `FakeSurrealStore.purge_traces_before` made the attribute EXIST, so the contract's
`trio.store.purge_traces_before = _spy  # type: ignore[attr-defined]` became two mypy errors:
`[unused-ignore]` (the attr-defined error no longer fires) + `[method-assign]` (assigning over a
now-real method). This is a regression my in-scope companion change DIRECTLY caused → minimal fix
per scope law: changed the suppression to `# type: ignore[method-assign]` (+ a one-line reason).
The contract's own docstring already anticipated this ("works whether or not the fake class
defines `purge_traces_before`"). No behavioral change (comment-only). Disclosed here prominently.

## E. R1 disposition — TIGHTENED (lead's ruling: "tighten if cheap")
The `TestPurgeRidesTraceTsIndex` receipt EXPLAINed a hand-written `SELECT *` proxy (adversary
residual R1: decoupled from the purge's actual query). **Tightened:** added
`_TRACE_PURGE_ID_SELECT` as ONE module template that BOTH the store's drain AND the receipt read,
so the receipt now EXPLAINs the purge's EXACT `SELECT VALUE id FROM trace WHERE ts < $cutoff
LIMIT n` — a change to the purge predicate now reddens the receipt (INSTRUMENT-0: observe the
effect of the actual code, not a proxy). **Verified live** on spike-surreal 3.2.4:
`SELECT VALUE id ... LIMIT 100 EXPLAIN` → `IndexScan` on `trace_ts` (the receipt is GREEN §I).
- **Removed-behavior adjudication** (the receipt's old ts-DELETE-EXPLAIN leg): the prior receipt
  also EXPLAINed `DELETE trace WHERE ts < $c` and asserted it rode `trace_ts`. The id-batched
  drain issues **`DELETE ... WHERE id IN $ids`** (bounded by PRIMARY id, NOT `trace_ts`) — the
  ts-DELETE was a proxy for a query the purge NEVER issues. **Dropped deliberately**: DD-1.c
  requirement 3 ("rides `trace_ts`") is a property of the row-FINDING scan, which is the SELECT,
  now asserted exactly. The TableScan positive control is KEPT.

## F. DRY ledger (new reusable symbols)
| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `surreal._TRACE_PURGE_BATCH_SIZE` (constant) | `lore_search "surreal batch size limit constant delete purge"` + grep the constants block | existing caps are `_MAX_HYBRID_K`, `FILE_TEXT_MAX_BYTES`, `TXN_STATEMENT_HARD_CAP`; no trace/delete batch knob | **HAND-ROLLED** — first trace-GC batch knob; obligation #2 forbids the literal |
| `surreal._TRACE_PURGE_ID_SELECT` (query template) | read `SurrealStore.trace_aggregates` / `record_trace` (adjacent query builders) | the store builds each SurrealQL string INLINE as an f-string; no shared query-template helper exists | **HAND-ROLLED** — matches the store's inline-query idiom; shared with the receipt to close the R1 proxy (§E) |
(Not new reusable symbols: `purge_traces_before` + the validator were introduced by r1's contract
— r1's ledger dispositioned them HAND-ROLLED-reusing-`_query` / REUSED-`model_validator`; I only
filled bodies. `FakeSurrealStore.purge_traces_before` + `_SweepOnceSleep` are test infra.)

## G. Reach bound + the #366 duplication (honest INSTRUMENT-0 accounting)
The caller pins are a HAND-LIST of the 2 current daemons' 4 sites (2 periodic + 2 initial), NOT a
set DERIVED from "every `run_sweep`/`reconcile` caller". A THIRD `_periodic_reconcile` (a new
daemon/deployment role) added BARE would NOT be caught by these pins. Per the adversary this reach
is finite/enumerable/terminating (not receding), and the lead ruled Fork A = pin the current
callers. **Named re-open trigger: any third `_periodic_reconcile`, OR an observed unbounded
trace-table growth in a deployment (P-periodic silently off).** The scout/server
`_periodic_reconcile` DUPLICATION (should they share one helper? = #366) is a DESIGN question above
a builder — flagged, not touched. I wired both callers correctly and did NOT write a "copy this
pattern" prose anywhere.

## H. Mutation matrix — 7 proofs, ALL PROOF-HELD (scripts/mutation_proof.py)
Scratch: `./scripts/scratch_copy.sh /tmp/lore-scratch-builder-tracegc` — provenance asserted,
**`loremaster -> /tmp/lore-scratch-builder-tracegc/loremaster/loremaster/__init__.py`** (inside
the scratch, #140). Each row: declared expected-RED node-ids (from `--collect-only`) BEFORE the
run; `mutation_proof.py` diffs observed-vs-declared BOTH ways and restores byte-exact (md5).

| # | mutation (file) | target pin(s) | result |
|---|---|---|---|
| MC1 | scout periodic `run_sweep(purge_traces=True)` → bare (scout.py) | SP | **RED (only)** |
| MC2 | server periodic `run_sweep(purge_traces=True)` → bare (server.py) | VP | **RED (only)** |
| MC3 | scout INITIAL sweep → `run_sweep(purge_traces=True)` (scout.py) | SP + SI | **RED (both)** — SP also guards `flags[0] is False`, so it co-fires; declared both |
| MC4 | server INITIAL sweep → `run_sweep(purge_traces=True)` (server.py) | VI | **RED (only)** |
| M5 | drop the gated purge CALL (reconcile.py) | the 3 `TestReconcilePurgesTraceRetention` pins | **RED ×3** |
| M7 | `if purge_traces:` → `if True:` (reconcile.py) | ungated-vs-gated pin ONLY | **RED (only)**; both gated legs GREEN |
| MFK | fake purge `>=` → `>` (_surreal_fakes.py) | `TestPurgeTracesBeforeFake` | **RED (only)** |
Every leg printed "PROOF HELD — the declared RED set fired EXACTLY" and restored byte-exact.
M5/M7 re-confirm the inherited feature mutations still discriminate on my build.

## I. Gates
- **Full trace-GC contract (13 inherited + 4 caller + 1 fake) = `18 passed`** — incl. the
  R1-tightened live EXPLAIN receipt (`SELECT VALUE id ... LIMIT n` → IndexScan on `trace_ts`,
  verified on spike-surreal 3.2.4).
- **No regression across affected suites** — `tests/{test_reconcile, test_config,
  test_trace_telemetry, test_watcher, test_scout, test_mcp_server, test_surreal_store,
  test_surreal_fakes, test_trace_retention_gc}.py -n auto` = **`1229 passed in 114.55s`**.
- **`uv run ruff check .` → `All checks passed!`**
- **`scripts/typecheck.sh` → ZERO-NEW.** NOT green (do-not-claim): the #333 auth-WIP baseline is
  `Found 102 errors` (loremaster) + `Found 89 errors` (lorerunes) = **191**, matching the
  documented baseline. NONE of the 191 are in any file I touched (verified by grep over all 13
  touched paths — my session's 3 introduced errors were fixed §D + `_SweepOnceSleep` subclassing).
- Discipline: all live tests hit `spike-surreal ws://127.0.0.1:18000` (throwaway
  `unique_database()`); `:18500` NEVER touched. No git state mutated (the lead commits).

## J. Deliverable footprint
`git status --short` (my writable set — all in scope; watcher.py + test_watcher.py diffs are the
INHERITED r2 stubs, untouched by me):
```
 M loremaster/loremaster/config.py
 M loremaster/loremaster/index/reconcile.py
 M loremaster/loremaster/index/watcher.py      (inherited r2 stub — not edited by me)
 M loremaster/loremaster/scout.py              (my wiring)
 M loremaster/loremaster/server.py             (my wiring)
 M loremaster/loremaster/store/surreal.py
 M loremaster/tests/_surreal_fakes.py
 M loremaster/tests/test_mcp_server.py
 M loremaster/tests/test_reconcile.py
 M loremaster/tests/test_scout.py
 M loremaster/tests/test_surreal_fakes.py
 M loremaster/tests/test_watcher.py            (inherited r2 stub — not edited by me)
?? loremaster/tests/test_trace_retention_gc.py (inherited contract + my R1 tightening)
```
`git diff --stat`: 12 files, +601 −10. Scratch left at `/tmp/lore-scratch-builder-tracegc`
(disposable `scratch_copy.sh` copy, NOT a git worktree).

## K. Store / tool discipline
- Store reference `docs/reference/surrealdb-31-capabilities.md` consulted (§2 `ts<$cutoff` =
  IndexScan; §1.1/§1.6 dirty-store; §3 `.query()` statement[0]-only) — cited, not re-transcribed.
  The `DELETE ... LIMIT` PARSE-ERROR / id-batch mechanism is r1 §3's probe, inherited + confirmed
  by the live window+drain pins greening.
- lore-first: `lore_get_symbol` (ReconcileEngine.reconcile, Scout._periodic_reconcile, Scout.start,
  server._periodic_reconcile), `lore_search`/`lore_recall` context. ONE disclosed grep fallback —
  cross-cutting caller/constant enumeration across scout/server/watcher/surreal and the fakes
  (CLAUDE.md fallback case (c) cross-cutting map + (b) non-symbol constant/text seams). No lore
  weakness encountered; no friction filed.
