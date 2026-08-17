# 07a — TEST CONTRACT: store recovery + degradation (#164/#250 · #128 · #126/#127)

Author: `contract-07a-1` · phase: CONTRACT (contract → adversary → build → cold audit → deploy) ·
graded at HEAD `995a358`, engine spike-surreal 3.2.4.
Full measurement + reasoning: `REPORT-contract-07a-1.md` (this session; archive with the wave).
Spec/work-order: `docs/plans/v2/07a-store-recovery-degradation.md`. Design analysis:
`REPORT-fable-sidecar-07a.md`.
**Operator ruling applied:** `docs/plans/v2/receipts/2026-08-17-packet07a/RULING-fork-a.md` — FORK A = A1
(adjudicate #164/#250 as does-not-reproduce-at-HEAD; NO reconnect-and-retry; A2 designed-not-written);
#128 = distinct contention wording; #127 = frozen-caller-set tripwire. All three applied (§A, §B, §D).
**Adversary graded INSUFFICIENT (narrowly) → corrected:** #128/#127 cleared to build; the #164/#250
adjudication's evidence chain was fixed for F1 (false-gate trigger), F2 (chronologically-false
"fixed-by-05a-ii" root cause → UNDIAGNOSED), F3 (drill negative control) — `REPORT-adversary-07a-1.md`,
applied in §B + `REPORT-contract-07a-1.md` §13.

## The reshaping (READ FIRST)
The packet spec assumes #164/#250 is a LIVE wedge needing a reconnect FIX. **Measurement falsifies that:**
a full server bounce self-heals on the next call, 20/20 (`scripts/probe_store_recovery_07a.py`;
transcript `docs/plans/v2/receipts/2026-08-17-packet07a/probe-store-recovery-transcript.txt`). So this
contract is a MIX, not an all-RED reconnect contract:
- **#128** — a genuine RED contract (pins written, RED at HEAD, satisfiable). The core buildable item.
- **#164/#250** — an ADJUDICATION (does-not-reproduce at HEAD; root cause UNDIAGNOSED) + a committed live
  drill with a negative control; the reconnect-and-retry
  build is a SCOPE FORK (A1 vs A2) held for the operator.
- **#126/#127** — written verdicts (RENEW), each with a rider/precision.

## A. #128 — per-item batch degradation (RED, WRITTEN)
Seam: `loremaster/loremaster/server.py::AppContext._resolve_or_acknowledge_many` (the `_FINDING_BATCH_VERB`
loop). Defect: `TxnContentionExhaustedError` / plain `SurrealStoreError` escape the per-item loop (caught
today: only `SurrealConnectionError` → abort-all, and the domain trio → per-item FAILED) → the whole batch
`findings()` response dies. Best-effort contract ("one bad item never vetoes the rest") is violated.

Pins (`loremaster/tests/test_mcp_server.py::TestResolveManyAcknowledgeManyDispatch`):
- `test_a_contended_item_FAILS_per_item_without_aborting_the_rest`
- `test_a_plain_store_error_item_FAILS_per_item_without_aborting_the_rest`
- `test_acknowledge_many_also_degrades_per_item_on_contention`

Injector: `_LedgerRaisingOnSecondCall` (module-level fault double, raises a given error on the 2nd
resolve/acknowledge call — generalizes the existing inline `_ConnectionDroppingAfterFirst`).

Fate table (quantifier law — force EVERY fate; the middle two are the NEW pins):
| fault on an item | required fate | discriminator |
|---|---|---|
| success | resolved/acknowledged line | (existing) |
| domain trio (`NotFound`/`IllegalTransition`/`ValueError`) | per-item `FAILED —`, CONTINUE | existing pin |
| `SurrealConnectionError` (dead socket) | ABORT remaining (render, not raise) | existing pin |
| **`TxnContentionExhaustedError`** | **per-item `FAILED —`, CONTINUE** | item AFTER it MUST still succeed |
| **plain `SurrealStoreError`** | **per-item `FAILED —`, CONTINUE** | render is exactly N+1 rows, unfractured |

Design (sidecar §3 + operator ruling): the builder must DISTINGUISH the two error types — catch, in
order, `SurrealConnectionError` (abort-all) → `TxnContentionExhaustedError` (distinct contention line) →
`SurrealStoreError` (generic FAILED) → domain trio. All after `SurrealConnectionError` (its subclass);
`TxnContentionExhaustedError` before its own `SurrealStoreError` superclass. FAILED-and-CONTINUE for both
non-connection store faults (contention ≠ dead socket: connection is healthy, the next item can succeed).
Sanitise via `_sanitise_line`.

**#128 RENDER WORDING — RULED (RULING-fork-a.md):** a contended item renders the DISTINCT line
**`FAILED — store contention, safe to retry this item`** (contention is genuinely retryable); a plain
`SurrealStoreError` renders the generic `FAILED — {sanitised reason}` and must NOT claim "safe to retry".
The 3 pins now assert the EXACT contention suffix, and the plain-error pin asserts the "safe to retry"
wording is ABSENT (so a build that labels the whole `SurrealStoreError` base "safe to retry" reddens).

**RED receipt (tightened):** `3 failed, 664 deselected` (the escaped error kills `findings()` at
`server.py:3920`). **Satisfiability:** the distinct-wording reference build (catch
`TxnContentionExhaustedError` → contention line, then `SurrealStoreError` → generic) → `3 passed`;
reverted (server.py `git diff` empty). See `REPORT-contract-07a-1.md` §4/§12.

**OPEN for the adversary (one item; wording is now RULED):** the 20-consecutive REAL-contention pin —
forcing a NATURAL `TxnContentionExhaustedError` is unreliable (survey: 0 exhaustions at N≤32). Options: a
live ≥8-way best-effort "never raises unhandled" pin (20×), or a budget-shrink variant that makes
contention actually exhaust. The deterministic injected pins ARE the real discriminators; the adversary
grades whether a live-contention corroboration pin is warranted and in which form.

## B. #164/#250 — RECOVERY (adjudication + drill; reconnect build is FORK A)
Measured: **does NOT reproduce on HEAD** — self-heals on the next call after a full bounce, 20/20
heal-index=1 (`REPORT-contract-07a-1.md` §1). **Root cause of the original July wedge: UNDIAGNOSED**
(corrected per adversary F2 — see below; NOT "fixed-by-05a-ii"). Both known transport-fault branches are
independently guarded and mutation-proven:
- **idle / connection-close (pre-send) + drop/reconnect** — the next query raises `ConnectionClosedError`
  ("no close frame received or sent", a `WebSocketException` ∈ `_CONNECTION_ERRORS`) → drop→reconnect.
  Guarded LIVE by `TestMidLifeConnectionRecovery` (`connection.close()` shape) AND by the committed
  full-bounce drill (the abnormal server-vanish shape), whose **negative control** (Exp B: disable the
  drop → 0/N wedged) proves it discriminates this mechanism.
- **in-flight `KeyError`** — a socket drop with a query in flight raises `KeyError(request-uuid)`, caught
  by the LITERAL `except (*_CONNECTION_ERRORS, KeyError)` in `run_query` / `_txn_query_raw` (NOT
  `_SDK_AWAIT_BOUNDARY_ERRORS` — that constant is read only by `inbox_awaiter.py`/`scout.py`). Guarded by
  the SYNTHETIC unit tests `TestQuerySeamSdkKeyErrorClassification` + `TestTxnSdkKeyErrorClassification`
  (mutation-proven RED under a reverted catch — adversary Exp A). **The drill does NOT reach this branch**
  (the idle bounce never produces a `KeyError`), so it is NOT the guard for it.

Deliverables:
- **The committed live drill + its negative control** (`scripts/probe_store_recovery_07a.py drill`) is the
  spec's literal "20-consecutive bounce-recovery without a container restart" — wire it as a DEPLOY-SMOKE
  step (it needs `systemctl`, so it cannot be a fast unit test).
- **Adjudication (root cause honest — adversary F2):** resolve #164/#250 as *"does not reproduce at HEAD;
  both known transport-fault branches (connection-close + in-flight-KeyError) independently guarded and
  mutation-proven; ROOT CAUSE of the original July wedge UNDIAGNOSED (candidates: a since-changed cause,
  or the 'server not yet back within the 2 calls anyone tried' timing artifact #250 flags)"* — **never
  "fixed by 05a-ii"** (chronologically impossible: the store's KeyError self-heal shipped at `9d29111`
  2026-07-14, 8–13 days BEFORE #164/#250; 05a-ii's `f5aec32` 2026-08-10 never touched the store path).
  Named re-open trigger, split by the instrument that actually guards each:
  - a **connection-close/reconnect** regression → the full-bounce drill stops healing (its negative
    control proves it can detect that);
  - an **in-flight-KeyError-branch** regression → `TestQuerySeamSdkKeyErrorClassification` /
    `TestTxnSdkKeyErrorClassification` go RED (mutation-proven, adversary Exp A);
  - and the standing FORK-A re-open at packet 16 (#249 RSS restart-policy).

**FORK A — RULED A1 (RULING-fork-a.md):** adjudicate #164/#250 as does-not-reproduce-at-HEAD; ship the
committed 20-consecutive drill (+ negative control) as deploy-smoke; NO new reconnect-and-retry code. Named re-open trigger: **packet 16
(#249 RSS restart-policy)** — when store restarts become routine/scheduled, re-open FORK A with fleet
telemetry rather than building A2 speculatively (measure-then-tune). The A2 design stays in
`REPORT-contract-07a-1.md` §3.1 (shared `ReconnectRetrySignal`, pre-send/idempotent-only,
at-most-once-preserving) — **designed, NOT written**. Do not build A2.
Close-out action for the lead: resolve #164 and #250 as *does-not-reproduce-at-HEAD* (both transport-fault
branches guarded + mutation-proven; ROOT CAUSE undiagnosed — never "fixed by 05a-ii"), citing the drill +
its negative control + the two KeyError unit-test classes + the packet-16 re-open trigger.

## C. #126 — retry-under-lock latency (VERDICT: RENEW)
Trigger (multi-second p99 stalls under fleet load) NOT fired: survey p99 ~0.045s @N=32; probe reconnect
~0.5s; no successor latency finding. #250 is a WEDGE not a stall. **RENEW bounded-by-design, trigger
unchanged.** ⚠ RIDER: IF A2 ships, re-adjudicate against the SHIPPED seam (Option A grows the composed
budget #126 is about). If A1, holds unchanged. (`REPORT-contract-07a-1.md` §6.)

## D. #127 — scout `_ensure_connection` no-lock (VERDICT: RENEW latent)
07a touches the STORE seam, not scout → trigger ("a 2nd caller of scout `_ensure_connection` / scout
builds its own socket") NOT met → **RENEW latent; do NOT add the lock.** ⚠ PRECISION: #127's "run() is
its sole driver" is imprecise — `process_pending_once` (test-only, no prod caller, predates #127) is a
2nd in-code caller; safety holds via "sole PRODUCTION driver = run()".
**TRIPWIRE PIN — RULED + WRITTEN (RULING-fork-a.md):** `test_scout.py::
TestScoutEnsureConnectionSoleDriverTripwire` — an AST scan asserting the callers of
`CommandSubscriber._ensure_connection` are EXACTLY `{run, process_pending_once}`, with a
not-vacuously-green self-guard. GREEN today; **mutation-proven** (adding a 3rd caller reddens it, naming
it; `REPORT-contract-07a-1.md` §12). A real 3rd (production) caller now reddens → mechanical re-open
trigger. The lock itself is NOT added (untested lock on a path with no concurrent prod driver = the scope
#127 declined). #127/#164 couple ONLY under A2 (the shared `ReconnectRetrySignal`) — moot under A1.
(`REPORT-contract-07a-1.md` §7.)

## Verification order receipts (operator ruling 2026-08-17)
#250 healing-scope + #308 router-race settled: store-ref §3 → `surrealql-tests` (no transport-reconnect
test) → `surrealdb-docs` (off-version `.new_session()`) → LIVE PROBE is the authority. #308 `Session not
found` NEVER surfaced in 20+ reconnects on 3.2.4. §3's "heals via ConnectionClosedError" = error-SHAPE
normalization, not auto-recovery (recommend a one-line §3 clarification). Full: `REPORT-contract-07a-1.md`
§2, §8.
