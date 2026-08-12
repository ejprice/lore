brief-base v13 read
brief project v7 read

# REPORT — adversary-tracegc-06b (contract-adversary on the trace-retention GC, #193 / DD-1.c)

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT** — on exactly ONE confirmed missing pin (the caller reach), which is the lead's already-ruled **Fork A**. Everything else was attacked empirically and WITHSTOOD. The reach is a FINITE, ENUMERABLE, terminating set (2 periodic callers + 2 initial-sweep callers across the scout/server daemons) — **not** adversarial-receding, so: pin the callers and STOP. No spiral.
- **P1 headline — did a wrong build survive the contract? YES, one:** the §6 reference build (config validator + store drain + gated reconcile purge, **callers untouched**) greens **13/13** while BOTH periodic callers (`scout.py:895`, `server.py:9321`) stay bare → **it never purges in production.** That build IS the E-reach receipt. Symmetric hole: flipping an initial-sweep caller (`server.py:8971`) to `run_sweep(purge_traces=True)` would purge AT BOOT and still green 13/13 — no contract test references any caller seam (grep §B).
- **Satisfiability (P1c/P7): PASS.** 13/13 green on the reference build (provenance-asserted scratch, `loremaster.__file__=/tmp/lore-adv-tracegc/...`). No reshape regression: config+telemetry 217, scout+watcher 68, the 2 `test_mcp_server` spy tests 2 — all green (§C). My hypothesised `_spy_reconcile` TypeError did NOT reproduce (watcher-not-started → `lore_index` takes the `reconcile()` branch, server.py:4803) — built, not reasoned.
- **QUANTIFIER TABLE (P1b):** §D — 8 invariants; 7 ∀-over-inputs with receipts, 1 GUARDED (caller reach) carrying the surviving wrong build.
- **REACH TABLE (P1c):** §E — 6 instruments; 5 safe, 1 MISSING-PIN (caller reach) + 1 residual (EXPLAIN-receipt observes a proxy query).
- **MISSING PINS:** (A) periodic caller passes `run_sweep(purge_traces=True)` — unpinned; (B) initial-sweep caller stays bare — unpinned. Both = E-reach, both directions. §D/§E.
- **Fixtures interrogated:** window ∀ (straddling, boundary=cutoff), drain N=25/batch=10, reach retention∈{30,60} (non-default → not a 90-monoculture) — all discriminate; perturbations WB-1/WB-3 §F.
- **Reproduced:** M1/M2/M4/M5/M6/M7/M8 re-confirmed via the reference build's own mutations + 2 NEW wrong builds (WB-1 drain early-stop, WB-3 validator wrong-direction) — all RED, restores md5-exact. §F.
- **Residuals (individual verdicts):** R1 EXPLAIN-receipt proxy (LOW), R2 validator rejects any `window>retention` config at LOAD (by-design, deploy note), R3 Fork-A companion cost (`_FakeWatcher.run_sweep` signature). §G.
- **Graded:** `40744a6` · HEAD-at-report: `40744a6` · SAME.
- **Packages considered:** none — I specified/built no mechanism (adversary; reference build is the author's stdlib+SurrealQL design).
- **Reuse ledger:** none — I introduced no production symbol.
- **decisions-needed:** the E-reach A/B fork is the lead's (recommend A, pin the 4 caller sites); the scout/server `_periodic_reconcile` DUPLICATION (one shared helper?) is a design question above a contract author.
- receipt pointers: reference build §A · caller grep §B · satisfiability §C · quantifier §D · reach §E · wrong-build reproductions §F · residuals §G.

---

## A. What I graded, and how (the reference build)
Graded HEAD `40744a6` + the uncommitted r1/r2 stubs (`git status`: config.py, index/reconcile.py, index/watcher.py, store/surreal.py, test_reconcile.py, test_watcher.py, + new test_trace_retention_gc.py). Contract under grade = the 13 pins:
- `test_trace_retention_gc.py` (8): `TestTraceRetentionConfigValidator` ×4, `TestPurgeRespectsTheWindow`, `TestBatchedDrainLeavesNoResidual`, `TestBootNeverPurges`, `TestPurgeRidesTraceTsIndex`.
- `test_reconcile.py::TestReconcilePurgesTraceRetention` ×3 (gated-periodic, ungated-vs-gated, cutoff-tracks-config).
- `test_watcher.py::TestRunSweepThreadsTracePurgeGate` ×2 (threading both directions).

Reference build (from `REPORT-contract-tracegc-06b-r2.md` §6) applied in a provenance-asserted scratch via `./scripts/scratch_copy.sh /tmp/lore-adv-tracegc` (`loremaster -> /tmp/lore-adv-tracegc/loremaster/loremaster/__init__.py`, asserted `is_relative_to` the scratch — #140). The patch is a committed-style instrument, pasted verbatim so the grade is re-runnable:

```python
# /tmp/apply_refbuild.py  — fills the 3 stub bodies the builder must write
# 1) config.py TelemetryConfig: add after `trace_retention_days: PositiveInt = DEFAULT_TRACE_RETENTION_DAYS`
    @model_validator(mode="after")
    def _retention_covers_window(self) -> "TelemetryConfig":
        if self.trace_retention_days < self.aggregate_window_days:
            raise ValueError(
                f"telemetry.trace_retention_days ({self.trace_retention_days}) must be "
                f">= telemetry.aggregate_window_days ({self.aggregate_window_days}) so the "
                f"served aggregate window can never outlive its retained trace data")
        return self
# 2) store/surreal.py purge_traces_before: replace the NotImplementedError with the id-batched drain
        total = 0
        while True:
            ids = await self._query(
                f"SELECT VALUE id FROM {TRACE_TABLE} "
                f"WHERE {TRACE_TS_FIELD} < $cutoff LIMIT {int(batch_size)}", {"cutoff": cutoff})
            if not ids:
                return total
            await self._query(f"DELETE {TRACE_TABLE} WHERE id IN $ids", {"ids": ids})
            total += len(ids)
# 3) index/reconcile.py: import timedelta + gate the purge before `return result`
        if purge_traces:
            trace_cutoff = datetime.now(UTC) - timedelta(
                days=self._config.telemetry.trace_retention_days)
            await self._store.purge_traces_before(cutoff=trace_cutoff)
        return result
```
`run_sweep`'s `purge_traces` threading and both method signatures are already in the r2 stubs; the builder fills only the 3 bodies above. This exactly matches the r2 §6 reference build (independently re-derived, not copied — same result).

## B. The confirmed E-reach gap — CONFIRMED BY CONSTRUCTION (the P1 wrong build)
The property DD-1.c/E1=Reading-Y wants is **"purge fires on the periodic tick, NEVER on the awaited initial startup sweep."** The contract pins the GATE (`reconcile(purge_traces=…)`) and its THREADING (`run_sweep→reconcile`). The **last mile — which CALLER sets the gate — is unpinned**, and it lives in two duplicated daemons.

Caller ground truth (scratch = HEAD; the reference build does NOT touch these):
```
scout.py:869   Scout.start           -> run_sweep()            initial   (bare — correct)
scout.py:895   Scout._periodic_reconcile -> run_sweep()        PERIODIC  (MUST be run_sweep(purge_traces=True) — bare in ref build)
scout.py:917   Scout.handle_command  -> run_sweep()            command   (bare — correct)
server.py:8971 initial sweep         -> run_sweep()            initial   (bare — correct)
server.py:9321 server._periodic_reconcile -> run_sweep()       PERIODIC  (MUST be run_sweep(purge_traces=True) — bare in ref build)
server.py:4801 forced lore_index     -> run_sweep()            forced    (bare — correct)
watcher.py:1092 on_kernel_overflow   -> reconcile()            overflow  (bare — correct)
```
**The reference build greens 13/13 (§C) with `scout.py:895` and `server.py:9321` BARE → production never purges.** That is the surviving wrong build: a perfect-looking, contract-satisfying build that silently violates P-periodic. The symmetric hole (P-initial): a build with `server.py:8971` → `run_sweep(purge_traces=True)` purges over months of rows at boot and ALSO greens 13/13.

**Grep proof no contract test references the caller seam (§B receipt):** every `Scout`/`_periodic_reconcile`/`8971`/`.start(`/`server` hit in the three contract files is a DOCSTRING or a harness-builder (`LoreServer(config)` to mint the registry) — **zero assertions on which caller passes the gate.** So both reach directions are unpinned by construction, not merely under-tested.

**Missing pin A** (the test that should exist): drive `Scout._periodic_reconcile` (and `server._periodic_reconcile`) and assert it calls `run_sweep(purge_traces=True)`. Defect it catches: a bare periodic caller — production NEVER purges (trace table grows unbounded).
**Missing pin B**: drive `Scout.start`'s initial sweep (and `server.py:8971`) and assert `run_sweep()`/`run_sweep(purge_traces=False)` (bare). Defect it catches: an initial caller passing `True` — a months-long purge blocks boot, the exact regression Reading Y forbids.

Seams for both already exist and are cheap (r2 §8 Fork A): `test_scout._FakeWatcher.run_sweep` extended to record the kwarg; `test_mcp_server` already spies `ctx.reconcile_engine.reconcile` (~:3206) and stubs `run_sweep` (~:849). **This is a finite enumerable reach (4 sites, terminating) — pin them and stop; do NOT manufacture receding-reach machinery.**

## C. Satisfiability + no-reshape-regression (P1c/P7) — all measured on the reference build
```
13-pin contract                                    : 13 passed in 4.59s   (provenance asserted inside scratch)
test_config.py + test_trace_telemetry.py           : 217 passed
test_watcher.py + test_scout.py (full)             : 68 passed
test_mcp_server.py -k index_wrapper_*sweeps (spies) : 2 passed, 664 deselected
13-pin contract (re-run after all restores)        : 13 passed in 3.21s
```
- The reshape is backward-compatible: `reconcile`/`run_sweep` gain keyword-only `purge_traces=False`; every existing bare caller is unchanged. The config validator is satisfiable — no production or test constructs a `TelemetryConfig` with `aggregate_window_days > trace_retention_days` (only real constructions: `config.py:635` default 90/14, `test_reconcile.py:679` retention∈{30,60}/window 14; `test_trace_telemetry.py:959` uses a `SimpleNamespace`, so the validator never runs there).
- **Killed a false alarm by BUILDING it:** I predicted `test_mcp_server.py` `_spy_reconcile()` (no `purge_traces` kwarg) would TypeError once `run_sweep` threads the gate. It does NOT — `lore_index(reconcile=True)` in the `indexed` fixture takes the `else` branch `reconcile_engine.reconcile()` (server.py:4803, watcher not started), never the threaded `run_sweep`. Construction, not reasoning (#107 lesson).

## D. QUANTIFIER TABLE (P1b)
| # | invariant | ∀-over-inputs / guarded | receipt |
|---|---|---|---|
| 1 | window: `ts<cutoff` deleted, `>=cutoff` survives, **boundary (`ts==cutoff`) survives** | ∀ over a straddling SET, boundary forced | M1 (`<=` reddens); WB-1 (early-stop → deleted 0) |
| 2 | batched drain leaves NO residual across N≫batch | ∀ over 25 rows / batch 10 (3 pages) | M2 (silent-cap); **WB-1** (early-stop before delete → RED) |
| 3 | config validator `retention >= window` | ∀ over 4 (retention,window) pairs + default-import | M4 (`if False`); **WB-3** (wrong-direction → default-config load fails) |
| 4 | `ensure_ready` (DDL boot) purges nothing | guarded @ ensure_ready | M3 (purge-in-ensure_ready reddens) |
| 5 | gate discrimination: ungated reconcile no-purge, gated purges | ∀ forced ONE engine/store, both legs | M5 (remove call), M7 (`if True`) |
| 6 | reach: cutoff = config-derived, NOT a hidden constant | ∀ over retention∈{30,60} | M6 (`days=90` reddens both reach pins) |
| 7 | `run_sweep` threads the gate verbatim (both directions) | ∀ both legs | M8 (drop→RED), M8b (hardcode-True→RED) |
| **8** | **purge fires on periodic tick, NEVER initial — at the CALLER** | **GUARDED — pinned NOWHERE at caller level** | **§B surviving wrong build (ref build, callers bare, 13/13 green, never purges)** |

Row 8 is the single guarded invariant whose bad outcome walks through an unguarded door (the caller). All others are ∀ with a live receipt.

## E. REACH TABLE (P1c) — legs: E for empirical (in-tree wrong build), I for construction-inspection
| instrument | reach = set of sites | DERIVED vs hand-list | coverage a CHECKED var? | effect vs proxy | one-source / mutation | verdict |
|---|---|---|---|---|---|---|
| reconcile gate (`purge_traces`) | the `reconcile` method | n/a (single method) | yes — spy records the actual purge call | **EFFECT** (spy = the call) | mutation M5/M7 redden | **SAFE (E)** |
| run_sweep threading | the `run_sweep` method | n/a | yes — both legs pinned | EFFECT (reconcile-gate spy) | M8/M8b redden both directions | **SAFE (E)** |
| window/drain live pins | the store purge query | n/a | yes — live rows | EFFECT (real DELETE) | M1/M2/WB-1 redden | **SAFE (E)** |
| config validator | `TelemetryConfig` construction | n/a | yes — 4 cases + default-import | EFFECT | M4/WB-3 redden | **SAFE (E)** |
| EXPLAIN receipt (`TestPurgeRidesTraceTsIndex`) | "a `ts<cutoff` scan rides `trace_ts`" | relies on DD-1.a index | NO — asserts a HAND-WRITTEN `SELECT */DELETE … WHERE ts<$c`, decoupled from purge code | **PROXY** — not the purge's own `SELECT VALUE id … LIMIT n` | — | **residual R1 (LOW)** |
| **property "periodic-only"** | **the SET of run_sweep/reconcile CALLERS** | **HIDDEN SET — no test enumerates callers** | **NO — no pin reddens when a caller drops/adds the gate** | n/a | n/a | **MISSING PIN (E-reach, §B)** |

The reach attack's central hit is the last row: the property's reach is a hidden constant (the caller list), never a checked variable — exactly the class INSTRUMENT-0 warns of, here bounded and enumerable.

## F. Wrong-build reproductions (empirical, scratch, restores md5-exact)
All in `/tmp/lore-adv-tracegc/loremaster`; each patch → run affected pins → restore from a pre-patch `cp`; md5 confirmed identical after restore.

- **WB-1 — drain HARMFUL early-stop** (`if len(ids) < batch_size: return total` BEFORE the DELETE): `TestBatchedDrainLeavesNoResidual` **RED** and `TestPurgeRespectsTheWindow` **RED** (`assert deleted == 2` → `0 == 2` — a non-full first page returns 0, deleting nothing). The drain pin catches the classic off-by-one, and the window pin catches it too (any non-full first page). restore md5 `06e9012…` == ref.
- **WB-3 — validator WRONG DIRECTION** (`if retention > window: raise`): module **fails to COLLECT** — the default `TelemetryConfig()` (90/14) at `LoreConfig` import raises `… (90) must be >= … (14)`. So the default-config construction is a live positive assertion of the direction; any validator that rejects 90-with-14 breaks the whole config module. restore md5 `09c0b54…` == ref.
- **Inherited mutations re-confirmed via the reference build's own lines** (r1/r2 matrix, independently reproduced here as the reference build greens then the mutations redden the named pins): M1 `<`→`<=` (window), M2 single-batch (drain), M3 purge-in-`ensure_ready` (boot), M4 `if False` (validator), M5 drop the gated call (3 gated pins), M6 `days=90` (2 reach pins), M7 `if True` (ungated-no-purge pin), M8/M8b (run_sweep threading). Consistent with r2 §5.

## G. Residuals — each an individual verdict (none is a blocker)
- **R1 (LOW) — the `trace_ts` EXPLAIN receipt observes a PROXY.** `TestPurgeRidesTraceTsIndex` asserts on a hand-written `SELECT * / DELETE … WHERE ts<$c EXPLAIN`, NOT on the purge's actual `SELECT VALUE id … LIMIT n`. A drain that used a non-index predicate would still (a) pass this receipt — it tests its own query, and the index exists regardless — and (b) pass window/drain (results are plan-agnostic). So DD-1.c requirement 3 ("rides `trace_ts`") is verified only for a proxy. Mitigation is real: the purge uses the SAME `ts<$cutoff` predicate the receipt proves rides the index, and Reading-Y moved the purge off boot, so a scan-vs-index gap is a non-boot perf nicety, not correctness. **Right-sized to a LOW residual, not a blocker** — but if cheaply closable, assert the EXPLAIN over the purge's exact `SELECT VALUE id … LIMIT n` string.
- **R2 (deploy note, by-design) — the validator rejects any config with `aggregate_window_days > trace_retention_days` at LOAD.** Because retention defaults to 90, an existing deployment YAML that set `aggregate_window_days > 90` would newly FAIL to boot. This is the validator's intended invariant (not a defect), but it is a behavior change worth one line in the config docstring / a CHANGELOG note.
- **R3 (Fork-A companion cost, not a current defect) — if the lead pins the callers (recommended), `test_scout._FakeWatcher.run_sweep(self)` (signature-narrow, lines 287/308) must gain `*, purge_traces: bool = False`,** else the pinned `Scout._periodic_reconcile → run_sweep(purge_traces=True)` TypeErrors against the fake. Flagging so the caller-pin wave includes it. (Also observed harmlessly today: `test_scout.py:1505`'s `_boom()` reconcile spy now receives `purge_traces=False` via the threaded `run_sweep`→ raises TypeError instead of its intended RuntimeError, but the test only asserts "command marked failed + scout survives", which both errors satisfy — green, no action needed.)

## H. Store / tool discipline
- All live probes + scratch runs hit `spike-surreal ws://127.0.0.1:18000` ONLY (the `_surreal_harness` default, throwaway `unique_database()`); `:18500` NEVER touched.
- Store reference `docs/reference/surrealdb-31-capabilities.md` consulted (§2 `ts<$cutoff`=IndexScan, §1.1/§1.6 dirty-store, §3 statement[0]-only) — cited, not re-transcribed. The `DELETE … LIMIT` PARSE-ERROR fact underpinning the id-batched drain is r1 §3's probe (spike-surreal 3.2.4), inherited and consistent with the reference build greening the live window+drain pins.
- lore-first: `lore_comms` (register), and the graded artifacts read directly. ONE disclosed grep fallback — cross-cutting caller/shadow enumeration across scout/server/watcher and the corpse/config-construction sweeps over the test tree (CLAUDE.md fallback case (c): cross-cutting multi-question map, and (b): non-symbol textual seam for the shadow-signature hunt). No lore weakness encountered; no friction filed.
- No git state mutated (the lead commits). Scratch at `/tmp/lore-adv-tracegc` (disposable `scratch_copy.sh` copy, NOT a worktree); reference-build patch pasted verbatim §A; wrong-build patches pasted §F. The real tree was never edited.

**VERDICT: CONTRACT INSUFFICIENT** — one confirmed missing pin (the caller reach, both directions = the lead's Fork A), reach finite/enumerable/terminating. Recommend **Fork A** (pin the 4 caller sites + the `_FakeWatcher` signature) then ship; the scout/server `_periodic_reconcile` duplication is a design question for the operator/lead. Every other pin was attacked (2 new wrong builds + 8 re-confirmed mutations) and held.
