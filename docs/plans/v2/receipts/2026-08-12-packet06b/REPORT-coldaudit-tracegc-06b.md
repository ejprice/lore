brief-base v13 read
brief project v7 read

# REPORT — coldaudit-tracegc-06b (cold REFUTE audit, trace-retention GC, #193 / DD-1.c)

## SUMMARY BLOCK
- **VERDICT: GO** — the trace-retention GC build is correct, its pins are non-vacuous,
  and it ships with named, non-blocking residuals only. Every gate re-run and every
  mutation was established INDEPENDENTLY (builder ≠ grader); no claim below rests on the
  builder's matrix.
- state: **done-with-residuals** (all residuals non-blocking; none is a defect).
- Independent gate re-runs (my counts): 18-pin trace-GC contract **18 passed**; affected
  9-suite set **1229 passed** exit 0 (no regression); `typecheck.sh` loremaster leg 102
  errors = **#333 baseline, ZERO in the 12 touched files** (zero-new); `ruff check .` clean.
- Caller-pin NON-VACUITY (I constructed all 4 mutations; byte-exact restore each): periodic
  True→bare reddens the periodic pin (scout+server); initial bare→True reddens the
  initial-guard pin (scout+server). **All 4 caller pins are non-vacuous.** §B.
- Mutation matrix (12/12 reddened target, byte-exact restore): +M7, M5, config validator
  both directions, window boundary `<`→`<=`, window delete-all, boot-purge injection. §C.
- R1 EXPLAIN receipt VERIFIED LIVE on :18000 by my own probe: the purge's ACTUAL SELECT
  IndexScans `trace_ts`; TableScan positive control discriminates; test EXPLAINs the store's
  own imported template (real query, not a proxy). Adversary residual R1 is FIXED. §D.
- Removed-behavior: keyword-only `purge_traces=False` preserves all 9 bare callers unchanged
  (grep + lore_impact agree); id-DELETE is genuinely NOT ts-indexed (live EXPLAIN =
  `Iterate Table`), so pinning the SELECT is correct; spy type-ignore change is comment-only. §E.
- Packages considered: none — I specified/built no mechanism (auditor; my probes are stdlib +
  the surrealdb SDK via the repo harness).
- Reuse ledger: none — I introduced no production symbol.
- **Graded:** `40744a6` (+ the uncommitted worktree build) · HEAD-at-report: `40744a6` · SAME.
- decisions-needed: **none blocking.** Two non-blocking notes for the lead: R2 (load-time
  validator can reject a pre-existing `window>retention` lore.yaml — no such config exists in
  this repo today) and one observation (periodic purge holds the single-writer lock; benign). §F.
- receipt pointers: gates §A · caller non-vacuity §B · mutation matrix §C · R1 live §D ·
  removed-behavior §E · residuals §F · instruments (pasted) §G.

---

## A. Independent gate re-runs (I am the ground-truth instrument)

All run from `loremaster/`, `-n auto` unless noted; counts are from the pasted tails.

| gate | command | result |
|---|---|---|
| trace-GC contract (18 pins) | `pytest -n auto` over test_trace_retention_gc.py + the 5 GC classes | `18 passed in 18.24s` |
| affected suites (9 files) | `pytest -n auto` reconcile/config/trace_telemetry/watcher/scout/mcp_server/surreal_store/surreal_fakes/trace_retention_gc | `1229 passed in 120.43s` EXIT=0 |
| typecheck | `bash scripts/typecheck.sh` | loremaster leg **102 errors** (= #333 baseline), ruff-adjacent legs OK |
| ruff | `uv run ruff check .` | `All checks passed!` EXIT=0 |

**18-pin set** = test_trace_retention_gc.py (8) + test_reconcile.py::TestReconcilePurgesTraceRetention
(3) + test_watcher.py::TestRunSweepThreadsTracePurgeGate (2) +
test_scout.py::TestTracePurgeGateReachesTheRightCallers (2) +
test_mcp_server.py::TestServerTracePurgeGateReachesTheRightCallers (2) +
test_surreal_fakes.py::TestPurgeTracesBeforeFake (1) = **18**. Builder's "18 passed" and
"1229 passed" both reproduced EXACTLY.

**Typecheck zero-new — verified, not assumed.** The 102 loremaster-leg errors are ALL in 8
unrelated auth test files (`test_auth_composition.py`, `test_auth.py`, `_auth_fixtures.py`,
`test_allowlist_roster.py`, `test_auth_identity_seam.py`, `test_google_token_verifier.py`,
`test_hosted_readonly_posture.py`, `test_permission_resolver_seam.py` — a different in-flight
packet). A grep of the 102 error lines against the 12 files this diff touches returned **NONE**.
So this build adds zero mypy errors. `ruff` clean.

---

## B. Caller-pin NON-VACUITY — I constructed every mutation (special scrutiny)

The lead flagged that the 4 Fork-A caller pins were written by the BUILDER (contract-completion
merged into the build), so a vacuous pin is possible. I did **not** read the builder's matrix; I
CONSTRUCTED each mutation myself in a provenance-asserted scratch and observed the redness.

Scratch: `./scripts/scratch_copy.sh /tmp/lore-cold-tracegc`, provenance ASSERTED —
`loremaster.__file__ = /tmp/lore-cold-tracegc/loremaster/loremaster/__init__.py` (inside the
scratch; #140 poison ruled out). Baseline: the 4 caller pins are **4 passed** before mutating.

| # | mutation I applied | line | pin that MUST redden | observed |
|---|---|---|---|---|
| a1 | scout periodic `run_sweep(purge_traces=True)` → bare `run_sweep()` | scout.py:897 | `test_scout…::test_periodic_reconcile_passes_the_trace_purge_gate` | **1 failed** ✓ |
| a2 | server periodic `run_sweep(purge_traces=True)` → bare | server.py:9324 | `test_mcp_server…::test_server_periodic_reconcile_passes_the_trace_purge_gate` | **1 failed** ✓ |
| b1 | scout initial `run_sweep()` → `run_sweep(purge_traces=True)` | scout.py:869 | `test_scout…::test_initial_startup_sweep_does_not_pass_the_purge_gate` | **1 failed** ✓ |
| b2 | server initial `run_sweep()` → `run_sweep(purge_traces=True)` | server.py:8971 | `test_mcp_server…::test_server_initial_sweep_does_not_pass_the_trace_purge_gate` | **1 failed** ✓ |

Each file restored byte-exact after its mutation (`md5sum FILE FILE.bak | uniq -c` → `2 <hash>`,
i.e. the pair is identical). **All 4 caller pins are NON-VACUOUS** — each reddens exactly its own
target and only on the wrong build. The special-scrutiny concern is discharged.

---

## C. Mutation matrix — the rest of the contract (all reddened, byte-exact restore)

| mutation | site | target pin | observed |
|---|---|---|---|
| M7: `if purge_traces:` → `if True:` (ungated purges) | reconcile.py:194 | `test_ungated_initial_sweep_does_not_purge_but_gated_does` | **1 failed** ✓ |
| M5: drop the gated purge call → `pass` | reconcile.py:198 | `test_gated_periodic_reconcile_purges_with_a_config_derived_cutoff` | **1 failed** ✓ |
| validator NEUTERED (`if False`) | config.py:518 | `test_retention_below_window_is_rejected_naming_both_fields` | **1 failed** ✓ |
| validator `<` → `<=` (rejects legal `==`) | config.py:518 | `test_retention_equal_to_window_validates` | **1 failed** ✓ |
| window `< $cutoff` → `<= $cutoff` (boundary wrongly deleted) | surreal.py:369 | `TestPurgeRespectsTheWindow` | **1 failed** ✓ |
| window delete-ALL (`… < $cutoff OR true …`) | surreal.py:369 | `TestPurgeRespectsTheWindow` | **1 failed** ✓ |
| boot-purge injection (`purge_traces_before` in `ensure_ready`) | surreal.py:550a | `TestBootNeverPurges` | **1 failed** ✓ |

Config both-directions: the neuter proves the REJECT direction discriminates (below-window no
longer rejected → RED); the `<`→`<=` proves the ACCEPT direction discriminates (legal `==`
wrongly rejected → RED). (A naive `<`→`>` also reddens but errors the whole module at collection
because the default `TelemetryConfig()` then raises — proof of effect, but the two surgical
mutations above are the clean per-assertion discriminators.) All files restored byte-exact.

---

## D. R1 EXPLAIN receipt — verified LIVE on spike-surreal :18000 (my own probe)

The adversary's residual R1 was "the EXPLAIN receipt observes a proxy query." The builder's R1
tightening extracts the purge's row-finding query into a module template `_TRACE_PURGE_ID_SELECT`
that the store AND the receipt both read, and removed the old `DELETE … WHERE ts < $c` EXPLAIN leg
(a query the code never issues). I verified the fix by an INDEPENDENT live probe (not by trusting
the passing test), on a throwaway `unique_database()` on `:18000`. Full instrument in §G.

```
ACTUAL PURGE SELECT: SELECT VALUE id FROM trace WHERE ts < $cutoff LIMIT 100
  IndexScan?  True  | trace_ts named?  True
  '<=' variant IndexScan?  True  | trace_ts named?  True
  CONTROL (tool=) TableScan?  True  | IndexScan absent?  True
RAW actual plan: {… "children":[{"attributes":{"access":"<d'2026-06-01T00:00:00Z'",
  "direction":"Forward","index":"trace_ts","limit":"100"},"operator":"IndexScan"}] …}
```

- The purge's **actual** SELECT (imported template, `.format(limit=100)`) rides `trace_ts` as a
  one-sided range IndexScan — the raw plan literally shows `"index":"trace_ts","operator":"IndexScan"`.
- The `<=` boundary variant STILL IndexScans → my §C boundary mutation reddened on SEMANTICS
  (boundary row deleted), not on a plan regression. Good cross-check.
- The TableScan positive control (`WHERE tool = …`, an unindexed field) TableScans with no
  IndexScan → the EXPLAIN reader discriminates and does not always report IndexScan.
- The test EXPLAINs the store's OWN imported `_TRACE_PURGE_ID_SELECT` (I confirmed the import at
  test_trace_retention_gc.py:66 and the `.format(limit=100)` at :311), so the receipt tracks the
  real query (INSTRUMENT-0 satisfied). **R1 is FIXED.**

---

## E. Removed-behavior adjudication (the reshape) — CONFIRMED

**Exhaustive caller inventory** (grep is the honest instrument for reshape-exhaustiveness; a
missed bare caller compiles-but-changes-behavior — said out loud per the dogfood protocol.
Corroborated by `lore_impact` on a FRESH index: it watches `/workspace` at `40744a6`, last_sync
531s, and its `run_sweep` `direct_consumers` list matches the grep exactly — 6 sites, no dynamic
caller missed):

- `run_sweep(` callers (6): scout `start` 869 **bare**, scout `_periodic_reconcile` 897 **True**,
  scout `handle_command` 919 **bare**, server `AppContext.index` (lore_index forced) 4801 **bare**,
  server initial startup 8971 **bare**, server `_periodic_reconcile` 9324 **True**.
- `reconcile(` callers (3): watcher `run_sweep` 1070 threads the flag; watcher
  `on_kernel_overflow` 1092 **bare**; server `AppContext.index` reconcile branch 4803 **bare**.

Mapping to the E1=Reading Y design of record: initial startup (×2) bare ✓, periodic tick (×2)
True ✓, IN_Q_OVERFLOW recovery bare ✓, forced `lore_index(reconcile=True)` (run_sweep + reconcile
branches) bare ✓, `reconcile` command bare ✓. **The keyword-only `purge_traces=False` default
preserves EVERY pre-existing bare caller unchanged; only the two periodic callers opt in.** No
dropped branch, no silently-changed behavior.

**id-DELETE adjudication (builder dropped the old ts-DELETE-EXPLAIN leg).** I EXPLAINed the ACTUAL
`DELETE trace WHERE id IN $ids` live (§G): plan = `[{"operation":"Iterate Table"…}, {"Collector"}]`,
**no `trace_ts`, no IndexScan** — the delete is bounded by the concrete RecordID set (which came
from the bounded SELECT page), never a ts scan. So DD-1.c req 3 ("rides `trace_ts`") is a property
of the row-FINDING scan, and the SELECT is the correct thing to pin; the removed leg EXPLAINed a
query the code never issues. **Adjudication CONFIRMED — the drop is strictly more honest, not a lost receipt.**

**Spy type-ignore change (attr-defined→method-assign).** Comment/type-only: the fake companion
now DEFINES `FakeSurrealStore.purge_traces_before`, so `trio.store.purge_traces_before = _spy`
became a method reassignment rather than a new-attribute define; the assignment line and its
runtime effect are unchanged. Confirmed from the diff.

**GOAL DELETE-scope reach-attack.** (1) Deletes ONLY beyond the window: a fresh row survives
because `record_trace` server-stamps `ts = time::now()`, always `>= cutoff` (cutoff = now −
retention, retention positive) — and the window ∀ (§C boundary/delete-all mutations + the passing
`TestPurgeRespectsTheWindow`) pins in-window survival. (2) Never at boot: `TestBootNeverPurges`
(non-vacuous, §C) + the 4 caller pins + M7. (3) Terminates: the `ts<cutoff` population strictly
shrinks each pass and no fresh row enters it, so `TestBatchedDrainLeavesNoResidual` (25 rows /
batch 10 → residual 0) drains to completion. All three legs hold.

---

## F. Residuals — each an individual verdict (non-blocking)

- **R1 (adversary residual): FIXED, not a residual anymore.** The receipt observes the actual
  query; verified live §D.
- **R2 — load-time validator rejects a pre-existing `aggregate_window_days > trace_retention_days`
  config. VERDICT: by-design, non-blocking.** A loud fail beats a silently-partial aggregate; the
  `⚠ DEPLOY NOTE` docstring documents it. I grepped every `*.yaml`/`*.yml` in the repo: **no config
  sets `aggregate_window_days` or `trace_retention_days` at all**, so nothing in this project trips
  it today (defaults 14 ≤ 90). Deploy note for the lead: the only way this bites is a *deployed*
  lore.yaml that raised the window above 90 — none exists here.
- **R3 — Fork-A companion cost (`_FakeWatcher`/`_FailingWatcher.run_sweep` signature widened).
  VERDICT: necessary and correct, non-blocking.** Without the widening the wired periodic caller
  TypeErrors the fakes.
- **Observation (mine, non-blocking) — the periodic purge runs UNDER the single-writer lock.**
  `run_sweep` holds `self._lock` across the whole `reconcile`, so a first-activation purge over a
  large backlog holds the writer lock for its (batched) duration, delaying index writes on that
  tick. This is OFF the boot path (daemon already running), index writes wait rather than being
  lost, and steady-state ticks purge small deltas — it is the intended "periodic tick under the
  lock" trade, not a defect. Surfaced for visibility only; the operator owns whether it matters.
- **Observation (mine, non-blocking) — the returned delete count could over-count under a
  hypothetical concurrent EXTERNAL deleter** (`total += len(ids)` counts the SELECTed page, not the
  rows the DELETE actually removed). In production the purge is single-writer and `record_trace`
  never enters the target population, so the count is exact; no caller uses the return value anyway.

---

## G. Instruments (pasted verbatim — deliverables, not scratch)

**Caller-pin + all fast/live mutations** were driven by three throwaway scripts
(`/tmp/mut_callers.sh`, `/tmp/mut_fast.sh` + `/tmp/mut_cfg.sh`, `/tmp/mut_live.sh`); each does
`cp` backup → line-addressed `sed` → single-node `pytest -n0` → `cp` restore →
`md5sum FILE FILE.bak | uniq -c` proof. The pattern for one representative (caller a1):
```bash
cp loremaster/scout.py /tmp/scout.bak
sed -i '897s/run_sweep(purge_traces=True)/run_sweep()/' loremaster/scout.py
uv run pytest -n0 -q "tests/test_scout.py::TestTracePurgeGateReachesTheRightCallers::test_periodic_reconcile_passes_the_trace_purge_gate"
cp /tmp/scout.bak loremaster/scout.py; md5sum loremaster/scout.py /tmp/scout.bak | awk '{print $1}' | uniq -c   # -> "2 <hash>"
```

**Live EXPLAIN probe (`/tmp/explain_probe.py`)** — §D receipt, and the DELETE probe
(`/tmp/delete_probe.py`) — §E adjudication. Both connect via the repo test harness to
`ws://127.0.0.1:18000` (spike-surreal TEST store; :18500 NEVER), each on a `unique_database()`
that is `REMOVE DATABASE`'d in teardown:
```python
# explain_probe.py (abridged — full file used):
env = make_env(database=unique_database(), dim=8)
store = SurrealStore(url=env.url, namespace=env.namespace, database=env.database,
                     dim=env.dim, user=env.user, password=env.password)   # password is a SecretStr
await store.ensure_ready()
conn = await connect_admin(env)
actual = _TRACE_PURGE_ID_SELECT.format(limit=100)                          # the store's OWN template
plan   = json.dumps(await run(conn, actual + " EXPLAIN", {"cutoff": cutoff}), default=str)
assert "IndexScan" in plan and f"{TRACE_TABLE}_ts" in plan
ctrl   = json.dumps(await run(conn, f"SELECT * FROM {TRACE_TABLE} WHERE tool = $t EXPLAIN", {"t":"probe"}), default=str)
assert "TableScan" in ctrl and "IndexScan" not in ctrl                     # positive control
# delete_probe.py: seed 3 old rows, SELECT their ids, then:
#   EXPLAIN DELETE trace WHERE id IN $ids  ->  [{"operation":"Iterate Table"…},{"Collector"}]  (no trace_ts)
```
