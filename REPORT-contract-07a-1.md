brief-base v14 read · brief project v7 read

# REPORT — contract-07a-1 — packet 07a CONTRACT phase (store recovery + degradation)

## SUMMARY BLOCK
- receipt: brief-base v14 read · brief project v7 read
- state: **done** — contract phase + operator ruling (A1) + **adversary corrections (F1/F2/F3)** all applied (§12, §13). The packet's central premise was FALSIFIED by measurement (#164/#250 wedge does NOT reproduce at HEAD, 20/20); the adversary cleared #128 + #127 to build and INSUFFICIENT'd the #164/#250 evidence chain (false-gate trigger, chronologically-false root cause, no negative control) — all three fixed. Final contract = #128 RED pins (tightened) + #127 GREEN tripwire (mutation-proven) + adjudications + committed drill WITH a negative control.
- deviation 1: #164/#250 "store bounce WEDGES the held connection forever, only a container restart heals" **does not reproduce** — 20/20 consecutive full bounces self-heal on the 2nd call. So there is **no RED contract for a reconnect FIX**; instead an adjudication + regression guard + a committed live drill. See §1–§3.
- deviation 2: contract is a MIX (measurement demanded it): #128 RED pins (real) + #164/#250/#126/#127 adjudications + a committed live-bounce probe. Not the all-RED contract the spec assumed.
- deviation 3: reference-build applied to server.py to earn the #128 satisfiability receipt, then **reverted** — `git diff loremaster/loremaster/server.py` is EMPTY (§4). Production code unchanged.
- Packages considered: **none new** — #128 rides the EXISTING per-item best-effort loop (`_resolve_or_acknowledge_many`); the #164 reconnect (if built) rides the EXISTING `retry_on_conflict` + `bootstrap_session` + the SDK's own reconnect. The retry substrate is the audited in-house `retry_on_conflict` (#102/#108/#120), deliberately not a package (settled in that wave; read: its docstring at `_txn.py`).
- Reuse ledger: **1 new test symbol** — `_LedgerRaisingOnSecondCall` (fault-injection double), all dispositioned (§9 DRY ledger). Probe script reuses `signin_credentials` + the packet-07 probe template.
- Graded: 995a358 (measurement base) · HEAD-at-report: edbd72a · code-identical (3 test/docs commits ahead — the contract commit + two ruling docs; `git diff 995a358..edbd72a -- loremaster/loremaster/` EMPTY, so the measurement holds). Probes run vs engine spike-surreal 3.2.4.
- decisions-needed: **ALL THREE RULED** (operator, `RULING-fork-a.md`; revisions applied — §12):
  1. **FORK A** → **A1** (adjudicate #164/#250 FIXED; no reconnect-and-retry; A2 designed-not-written; re-open at packet 16).
  2. **#128 wording** → distinct `FAILED — store contention, safe to retry this item`; pins tightened.
  3. **#127 tripwire** → add the frozen-caller-set pin; written + mutation-proven.
- receipt POINTERS: measurement + drill §1 · #250 healing-scope + #308 §2 · FORK A §3 · #128 RED pins + satisfiability §4–§5 · #126 verdict §6 · #127 verdict + precision §7 · store-ref clarification §8 · DRY ledger §9 · files §10 · POST-RULING revisions §12 · **ADVERSARY corrections F1/F2/F3 + git timeline §13**.

---

## 1. THE MEASUREMENT — #164/#250 does NOT reproduce on HEAD (the load-bearing finding)

**Instrument:** `scripts/probe_store_recovery_07a.py` (committed). **Transcript receipt:**
`docs/plans/v2/receipts/2026-08-17-packet07a/probe-store-recovery-transcript.txt` (committed, regenerable).
Engine: spike-surreal 3.2.4 (verified live: `podman ps` → floating `v3.2`, up; the store reference §0
header + memory `surreal 3.2.4 floating tag` — the packet spec's "3.2.1" is stale, #336). The probe
exercises the **REAL `SurrealStore`** path (not a bare `AsyncSurreal`), so it measures what
`run_query` + `_ensure_connection` + `_drop_connection` actually do — against a **FULL server restart**
(`systemctl --user restart spike-surreal.service`), the exact #164/#250 shape.

**Result (control passes — the probe can see a healthy store):**
- Control (no bounce): 3/3 `RETURN 1` → OK.
- Idle-then-full-bounce (#164/#250's exact shape): call 0 after the bounce raises
  `SurrealConnectionError [<- SurrealStoreError]: SurrealDB query failed against '…': no close frame
  received or sent` (the socket is dead; `_drop_connection` nulls the cached handle — `conn True→False`);
  **call 1 reconnects via `bootstrap_session` (`conn False→True`) and returns 1.**
- **20-consecutive full-bounce drill on ONE long-held store: 20/20 recovered without a container
  restart, heal-index UNIFORMLY = 1.** `SUMMARY: 20/20 recovered … heal-index set=[1]; wedged=[] ⇒ PASS`.
- A brand-NEW `SurrealStore` in the SAME process after the bounce: connects + queries fine (isolates
  out any process/SDK-level poisoning — there is none).

**So the store SELF-HEALS after a full server bounce, deterministically, on the very next call** — one
"sacrificed" call (the call that discovers + drops the dead socket) then a transparent reconnect. **#250's
"the 2nd call ALSO failed, no heal, needs `podman restart lore-lore`" DOES NOT reproduce on HEAD.**

**The #250 "sibling container" datapoint (does DI survive where lore-lore wedges?), answered without
touching production:** #250 hypothesised the difference was periodic-reconcile (lore-demand_intelligence,
survived) vs one long-held WS (lore-lore, wedged). My probe tests BOTH on spike-surreal — a fresh
`SurrealStore` (the periodic-reconnect analogue) AND a long-held one (the lore-lore analogue): **both
recover.** So the periodic-vs-held distinction is DISSOLVED on HEAD — DI survived in July because its
fresh connections were never carrying a stale KeyError-escaped dead handle; the long-held path now heals
too. (I did NOT and must NOT probe the prod containers on `:18500`; the mechanism question is answered on
the TEST store.)

**Why it wedged in July but not now — ROOT CAUSE UNDIAGNOSED (corrected per adversary F2; my first
draft's "fixed-by-05a-ii" claim was chronologically FALSE — see §13).** I originally inferred the July
wedge was an in-flight `KeyError` escaping `run_query` before packet 05a-ii closed it. **The git record
refutes that for the store path** (re-derived myself, §13): `run_query` shipped ALREADY catching the
literal `(*_CONNECTION_ERRORS, KeyError)` with the `isinstance(error, KeyError) or is_connection_error`
heal guard at `9d29111` (2026-07-14) — **8 days before #164 (07-22) and 13 before #250 (07-27)** — and
05a-ii (`f5aec32`, 2026-08-10) added `_SDK_AWAIT_BOUNDARY_ERRORS` used ONLY by `inbox_awaiter.py`/`scout.py`,
never the store's `run_query`/`_txn_query_raw`. So the store's KeyError self-heal was present, tested and
unchanged BEFORE the wedge was ever reported; 05a-ii did not fix it. **What DID cause the July production
wedge is undiagnosed** — the two live candidates are (a) a since-changed cause I have not identified, or
(b) the "server not yet back within the 2 calls anyone tried" timing artifact #250 itself flags ("nobody
waited minutes") — my probe's `_wait_server_back` is built precisely to rule (b) out of the HEAD
measurement. **What IS established:** the wedge does not reproduce at HEAD (20/20), and both known
transport-fault branches are independently guarded and mutation-proven (below). The *decision* (A1: the
store self-heals → don't build A2) stands; the *why* of July does not, and I do not assert one.

**Already guarded — TWO DISTINCT branches, guarded by DIFFERENT instruments (corrected per adversary F1;
the two are NOT interchangeable):**
- **Connection-close / idle (pre-send) + drop/reconnect** — the branch the full-bounce hits (the next
  query raises `ConnectionClosedError` ∈ `_CONNECTION_ERRORS`). Guarded LIVE by
  `TestMidLifeConnectionRecovery` (`test_count_recovers_…` / `test_hybrid_search_recovers_…`; a CLEAN
  `connection.close()` shape) + `test_record_trace_recovers_…`, AND by the committed full-bounce drill
  (the ABNORMAL server-vanish shape), whose **negative control** (§13/F3) proves it discriminates this
  mechanism (disable the drop → 0/N wedged).
- **In-flight `KeyError`** — a socket drop with a query in flight, caught by the LITERAL
  `except (*_CONNECTION_ERRORS, KeyError)` in `run_query`/`_txn_query_raw`. Guarded ONLY by the SYNTHETIC
  monkeypatched-`query` unit tests `TestQuerySeamSdkKeyErrorClassification` +
  `TestTxnSdkKeyErrorClassification` (mutation-proven RED under a reverted catch — adversary Exp A).
  **⚠ The drill does NOT reach this branch** (an idle bounce never produces a `KeyError`), so it is NOT
  the guard for it — my first draft's claim that the drill catches "any regression to the KeyError branch"
  was a FALSE GATE (§13/F1). The live in-flight-under-full-bounce path (#250's claimed prod shape) is
  exercised by nothing gated; its coverage is SYNTHETIC-only, stated honestly here (adversary MP-2).

---

## 2. #250 healing-scope + #308 router-race — SETTLED (mandatory verification order applied)

Order applied per the operator's 2026-08-17 ruling: (1) store reference → (2) `surrealql-tests` →
(3) `surrealdb-docs` → (4) live probe.

**#250's open question — is the store-reference §3 note ("the next call heals via ConnectionClosedError")
scoped narrower than a FULL SERVER restart, or has it regressed?** SETTLED, tier (1)+(4):
- §3 says: a socket drop with queries IN FLIGHT surfaces a raw `KeyError(uuid)`; **"the next call heals
  via `ConnectionClosedError`."** #250 read "heals" as "recovers/works" and reported a contradiction. **It
  is not a contradiction — "heals via ConnectionClosedError" means the ERROR SHAPE normalizes** (a raw
  `KeyError` on the in-flight call → a clean `ConnectionClosedError` on the next call, which
  `is_connection_error` then classifies as transport → `drop` → reconnect). §3 never claimed the
  *connection* auto-recovers; the reconnect happens on the call AFTER the drop, via `_ensure_connection`.
- My probe confirms both legs: the pre-send idle-bounce call raises `ConnectionClosedError` ("no close
  frame received or sent"), and the SUBSEQUENT call reconnects (20/20). So §3 is CORRECT but
  easily-misread; #250's "no heal" was the July wedge whose root cause is UNDIAGNOSED (§1/§13 — NOT the
  "KeyError-escape, since closed by 05a-ii" story my first draft told; that is chronologically false).
  **Neither §3 is false nor has it regressed.** (Recommended §3 one-line clarification: §8.)

**#308 "cold-start `Session not found` router-race fix" — does it change the wedge shape?** SETTLED,
tiers (2)+(3)+(4):
- Tier (2) `surrealql-tests`: the only session hit is `session::*` GETTER semantics — a query-language
  property; **there is NO executable language test for transport-layer reconnect/session-loss** (the CI
  SurrealQL suite doesn't exercise the WS transport). Corroborated by the sidecar's independent search
  (`REPORT-fable-sidecar-07a.md` §6).
- Tier (3) `surrealdb-docs`: nearest hit is the SDK `.new_session()` page — a 3.x SDK feature; our SDK is
  pinned 2.0.0 (no `.new_session()`), so it does not describe our path. Vendor prose can lie (§6 of the
  store reference has receipts).
- **Conclusion (a design output in itself): the stored-tests + docs corpora do NOT cover transport
  reconnect — so #308/#250 are settled ONLY by tier (4), the live probe.** Tier (4): in 20+ rapid
  reconnects on 3.2.4 (the fresh-connect server-back poll + the held-store reconnect), **`Session not
  found` NEVER surfaced.** #308 is not a factor at our reconnect cadence. Bound: I did not hammer
  cold-start N-way simultaneous first-connects immediately post-restart, so "never observed in 20+
  sequential reconnects" is the honest claim, not "cannot occur."

---

## 3. FORK A — the scope decision the measurement forces (OPERATOR)

The spec (`07a-store-recovery-degradation.md`) work-orders: *"Teach the seam to classify
dead-socket/closed-connection as RECONNECT-AND-RETRY … verify recovery without a container restart,
20-consecutive."* **The measurement falsifies the premise that recovery is broken** — it already recovers
without a container restart, 20/20. What remains is only the **one sacrificed call** (the first
post-bounce call surfaces `SurrealConnectionError` to the agent, then heals). Two readings:

- **A1 — adjudicate #164/#250 FIXED + regression guard (my recommendation).** Ship: (a) this measurement +
  the committed live drill as the deploy-smoke instrument (satisfies the spec's "20-consecutive
  bounce-recovery, no container restart" literally); (b) resolve #164/#250 as *does-not-reproduce-at-HEAD*
  (root cause undiagnosed — §1/§13), with a named re-open trigger; (c) NO new reconnect-and-retry code. **Rationale — measure-then-tune (operator
  deferral law):** the intervention's original target (the wedge) is gone; Option A now buys only a
  cosmetic "0 sacrificed calls instead of 1," at the cost of code that **partially reverses the
  at-most-once write-safety rule** (`retry_on_conflict` refuses to retry a transport fault precisely
  because a write in flight may already have committed). That is a real safety surface for a currently-
  cosmetic gain. **Named decision point:** packet 16 (#249 RSS restart-policy) — when store restarts
  become ROUTINE, the "1 failed call per scheduled restart × every active consumer" cost becomes real and
  measurable, and Option A earns its keep.

- **A2 — build reconnect-and-retry now (spec's literal intent).** Eliminate the sacrificed call so a
  bounce is transparent. This is a genuine design problem (a property to INVENT, at-most-once-safe), NOT
  a mechanical build — so per this repo's routing law it must be an Opus author who adversarially attacks
  its own design, or an operator ruling. The safe mechanism (sidecar §2, my probe): retry-after-reconnect
  ONLY for the **pre-send / idempotent** shape (idle-bounce = nothing sent = safe), NOT the in-flight
  `KeyError` write shape (may have committed). Its RED contract is designed in §3.1 below, to write IF the
  operator picks A2.

**This is a scope decision — it belongs to the operator, not me.** I recommend **A1** and have built the
A1 deliverables (adjudication + drill + verdicts). The A2 RED contract is designed but NOT written,
pending the ruling.

### 3.1 If A2: the reconnect-and-retry RED contract (designed, not written)
Quantifier-law fate table — pin the OUTCOME ∀ shapes, each fate FORCED by a fixture:
- pre-send `ConnectionClosedError` on a READ → reconnected-and-retried-in-one-call → SUCCEEDS (RED today: surfaces one error).
- pre-send `ConnectionClosedError` on a WRITE → reconnected-and-retried (nothing was sent) → SUCCEEDS.
- **in-flight `KeyError` on a WRITE → NOT auto-retried (at-most-once) → surfaces `SurrealConnectionError`, heals next call** (removed-behaviour guard — the dual: pin that this is STILL not auto-retried).
- domain rejection → NOT retried → `SurrealStoreError`.
- retryable conflict → retried (unchanged).
Mechanism: a shared `ReconnectRetrySignal` in `_txn` (the SHARED classifier both the store retry AND scout's ladder read — routing-is-not-sharing), retried by `retry_on_conflict` within the existing composed budget; NO second connect path (rides `bootstrap_session`, #120); NO retry-budget/jitter change (scope OUT). Plus the pre-send-vs-in-flight boundary must be probe-confirmed airtight before it is leaned on (sidecar §2 ⚠).

---

## 4. #128 — per-item degradation: RED pins WRITTEN + satisfiability receipt

**Confirmed live at HEAD:** `AppContext._resolve_or_acknowledge_many` (`server.py`, the
`_FINDING_BATCH_VERB` loop) catches per-item `SurrealConnectionError` (→ ABORT all remaining) and the
domain trio `(_FindingNotFoundError, _FindingIllegalTransitionError, ValueError)` (→ per-item FAILED,
continue) — but **`TxnContentionExhaustedError` and plain `SurrealStoreError` match NEITHER clause, so
they propagate and kill the whole batch response**, defeating the best-effort contract the batch verbs
advertise. Both subclass `SurrealStoreError`; `SurrealConnectionError` is a sibling subclass (caught
first, correctly).

**RED pins written** (`loremaster/tests/test_mcp_server.py`,
`TestResolveManyAcknowledgeManyDispatch`) — mirroring the existing
`test_connection_loss_aborts_remaining_as_render_not_raise` idiom:
- `test_a_contended_item_FAILS_per_item_without_aborting_the_rest` — injects `TxnContentionExhaustedError`
  on item 2 of 3; asserts item 1 resolved, item 2 a per-item `FAILED` line (NOT `ABORTED — store
  connection lost`), **item 3 STILL resolved** (the discriminator: a build that catches contention but
  aborts-all reddens here), header `resolved 2 of 3`.
- `test_a_plain_store_error_item_FAILS_per_item_without_aborting_the_rest` — same, injecting a plain
  `SurrealStoreError`; also asserts the render is exactly 4 rows (never fractured — sanitiser hygiene).
- `test_acknowledge_many_also_degrades_per_item_on_contention` — the SAME loop serves `acknowledge_many`;
  a build special-casing only `resolve_many` passes the two above and fails HERE.

**RED confirmed (meaningful):** all 3 fail because `TxnContentionExhaustedError` escapes
`_resolve_or_acknowledge_many` (`server.py:3920`) → kills the batch `findings()` call. Receipt:
`3 failed, 664 deselected`.

**Satisfiability receipt:** a minimal reference build (add `except SurrealStoreError` AFTER
`except SurrealConnectionError` → per-item `FAILED — {_sanitise_line(str(error))}` + `continue`; import
`SurrealStoreError`) turns all 3 GREEN (`3 passed, 664 deselected`). Reverted immediately —
`git diff loremaster/loremaster/server.py` is EMPTY. So the contract is satisfiable by a known-correct fix
and RED against HEAD.

---

## 5. #128 design call (confirmed with sidecar §3): FAILED-and-CONTINUE, not abort

`SurrealConnectionError` aborts the remainder because the socket is DEAD and nothing else can be
attempted. `TxnContentionExhaustedError` is the OPPOSITE: the connection is HEALTHY, this row just lost a
write-write race after exhausting retries; the next item (different row) can well succeed. **So contention
→ per-item FAILED, CONTINUE** (order load-bearing: `except SurrealConnectionError` first — it is a
subclass — then `except SurrealStoreError`). My pins assert the CONTINUE property (item after the
contended one succeeds) and that the contended line is a `FAILED` line, NOT an `ABORTED` line — they do
NOT over-pin the exact suffix wording, leaving the builder/operator the trust-doctrine choice
(**decision-needed 2**): a DISTINCT contention line (`FAILED — store contention, safe to retry this
item`) reads more honestly than the generic domain `FAILED — {reason}`, because contention is genuinely
retryable where a domain rejection is not.

**Real-contention concurrency pin (the 20-consecutive law) — a contract-design caveat for the adversary:**
the survey (`scripts/survey_txn_contention_102.py`) measured **ZERO exhaustions across 2900 mints at
N≤32**, so a "force a NATURAL `TxnContentionExhaustedError` under real ≥8-way contention" pin is
**unreliable** (it would rarely trigger the branch → a fixture-reason green). The deterministic injected
pins above ARE the discriminators. Proposed corroboration pin (for the adversary to grade): a live ≥8-way
`resolve_many`/`report` contention pin asserting every batch returns a per-item render and NEVER raises an
unhandled error, 20-consecutive — OR a budget-shrink variant (monkeypatch a tiny deadline) that makes
real contention actually exhaust. Flagged, not decided.

---

## 6. #126 verdict — RENEW acceptance (trigger NOT fired), with a rider

Re-open trigger: *"production or smoke telemetry showing multi-second p99 stalls on scout command
dispatch or on cold `_ensure_connection` under real fleet load."*
- **Not fired.** Evidence: the committed survey measures p99 **~0.045s at N=32** (`_txn.py` comment block,
  `survey_txn_contention_102.py`); my probe measures reconnect ~0.5s + heal on the next call — no
  multi-second stalls. No new latency finding exists (`lore_findings query area=store._txn`: #126 is the
  only latency row, still `acknowledged`, no successor). #250/#164 is a WEDGE (total), NOT a p99 stall —
  a different failure, so it does not itself meet #126's named trigger (sidecar §4).
- **Verdict: RENEW the bounded-by-design acceptance, trigger unchanged.**
- **⚠ RIDER (part of the ruling — sidecar §4): re-adjudicate against the SHIPPED 07a seam, not today's.**
  IF the operator picks A2, Option A adds reconnect-and-retry INTO the composed budget (outer retry floor
  × inner bootstrap, now × a reconnect) — it GROWS the very latency composition #126 is about, so the
  magnitude the acceptance rests on changes and #126 must be re-taken post-A2. If A1 (no seam change), the
  acceptance holds unchanged.

---

## 7. #127 verdict — RENEW latent (trigger NOT met by 07a) + a PRECISION correction

Re-open trigger: *"any change that adds a second caller of `scout._ensure_connection`, or makes scout
construct its own socket."* 07a's #164 work (A1 or A2) lives in the STORE seam
(`run_query`/`_ensure_connection`/`bootstrap_session`), NOT scout — scout has its own reconnect ladder in
`run()`. **07a adds no second scout caller and does not make scout build its own socket → RENEW latent.**

**⚠ PRECISION CORRECTION (surfaced, not silently narrowed) — #127's premise AND the sidecar's §5 are both
imprecise.** #127 says "safe today ONLY because `run()` is its sole driver"; the sidecar says
"`scout._ensure_connection` is called ONLY from `run()` (confirmed by read)." **Both are wrong on the
letter:** `scout._ensure_connection` has **TWO in-code callers** — `run()` (scout.py:487) AND
`process_pending_once()` (scout.py:367) — and `process_pending_once` predates #127 (it shipped with the
original scout, commit `3552285`, P5 C6). The safety survives because **`process_pending_once` has ZERO
production callers** (grep: only its own def + a docstring mention — it is a test-only entry point) and is
serialised on `_drain_lock`; so `run()` remains the sole *PRODUCTION* driver. The correct invariant is
"sole PRODUCTION driver," not "sole caller." (Verification: `lore_impact` flagged 2 prod consumers via the
bare-name channel; confirmed by grep — an exact-call-site question where grep is honest, said out loud.)

**Recommendation (decision-needed 3): do NOT add the lock** (an untested lock on a path with no concurrent
prod driver is the scope the original decision declined). IF the operator wants the latent bound made
DELIBERATE (WHEN YOU CANNOT CLOSE A HOLE, PIN IT), the tripwire must pin the CORRECT invariant — a frozen
caller-set: *the scout methods that call `_ensure_connection` are exactly `{run, process_pending_once}`*
(an AST scan over scout.py) — so a THIRD caller (the literal trigger) reddens it. A naive "run() is the
only caller" pin would be RED today (process_pending_once). I have NOT written this pin (it is an
adjudication instrument, not a fix, and its exact form wants the operator's nod); its design is above.

**Two-reconnect-policies question (spec: adjudicate #127+#164 together):** the store's self-heal and
scout's `run()` ladder are STRUCTURALLY DISTINCT loops (discrete-query self-heal vs long-lived-subscription
re-serve) — that difference is inherent to the two usage patterns, not duplication. ONE IMPLEMENTATION is
satisfied at the MECHANISM layer: both ride the SAME `bootstrap_session`, the SAME `is_connection_error` +
`_CONNECTION_ERRORS`, the SAME `retry_on_conflict`. IF A2 introduces a `ReconnectRetrySignal`/widened
predicate, it MUST be the SHARED one both seams read (routing-is-not-sharing) — that is the only #127/#164
coupling, and it only exists under A2.
⚠ **Minor two-source shape SURFACED (not fixed — out of my writable set, pre-existing):** the KeyError
boundary value is expressed TWICE — `run_query`/`_txn_query_raw` catch the LITERAL
`(*_CONNECTION_ERRORS, KeyError)`, while `inbox_awaiter.py`/`scout.py` import the NAMED constant
`_txn._SDK_AWAIT_BOUNDARY_ERRORS` (defined as that exact tuple). Same value, two sources — so a change to
the constant would NOT reach the store's literal. `_txn.py`'s own docstring (~:400) warns consumers to
import the constant rather than re-define it; `run_query` (which predates the constant, `9d29111`) was
never migrated onto it. Low-stakes today (both equal `(*_CONNECTION_ERRORS, KeyError)`), but a genuine
ROUTING-IS-NOT-SHARING residual if A2 ever widens the boundary. Flagged for the operator/lead; NOT in 07a's
scope to fix.

---

## 8. Store-reference §3 — recommended one-line clarification (flag, docs-only writable set)

§3's *"The next call heals via `ConnectionClosedError`"* was read by #250 as "the connection recovers" and
generated a false-contradiction report. It means the ERROR SHAPE normalizes (raw `KeyError` → clean
`ConnectionClosedError`), which then drives the drop→reconnect on the FOLLOWING call. Recommend appending:
*"— i.e. the exception TYPE normalizes so `is_connection_error` classifies it as transport; the
reconnect itself happens on the next call via the owner's `_ensure_connection`, not automatically."* This
kills the #250-class misread. Docs-only; flagged for the lead, not edited (writable set is tests +
scripts + receipts).

---

## 9. DRY ledger (brief-base §6) — new reusable symbols

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_LedgerRaisingOnSecondCall` (test double, test_mcp_server.py) | grep test tree for existing fault-injection ledger doubles (`_ConnectionDroppingAfterFirst`, `resolve_many` wrappers) | the sibling `_ConnectionDroppingAfterFirst` is an INLINE per-test class raising on the 2nd call — no reusable module-level double for injecting an arbitrary error on the Nth verb call | **HAND-ROLLED** — a module-level generalization of the existing inline pattern (parameterized by the error + per-verb counters), so the 3 #128 pins share ONE injector rather than cloning three near-identical inline wrappers. Cites `_ConnectionDroppingAfterFirst` as the pattern extended. |
| probe `scenario_*`/`_make_store`/`_wait_server_back` (scripts/, standalone instrument) | reuse of packet-07 `scripts/probe_store_error_classes_07.py` connection template + `loremaster.store._txn.signin_credentials` | the packet-07 probe already established the spike-surreal-3.2.4 connect pattern | **REUSED** `signin_credentials` + the packet-07 probe template; the bounce/recovery scenarios are new (no prior full-server-bounce probe existed). |

---

## 10. Files (this contract phase)

- `scripts/probe_store_recovery_07a.py` — **NEW**, committed instrument (the live bounce-recovery + 20-consecutive drill).
- `docs/plans/v2/receipts/2026-08-17-packet07a/probe-store-recovery-transcript.txt` — **NEW**, run receipt (control passes, 20/20 PASS).
- `loremaster/tests/test_mcp_server.py` — **MODIFIED**: 3 RED #128 pins + `_LedgerRaisingOnSecondCall` double + import (`SurrealStoreError`, `TxnContentionExhaustedError`).
- `loremaster/loremaster/server.py` — **UNCHANGED** (reference build applied for the satisfiability receipt, then reverted; `git diff` empty).
- `REPORT-fable-sidecar-07a.md` — the design sidecar's report (not mine; present at repo root).

**Gate note:** I ran only the scoped set (the 3 new pins + the reference-build check), per brief-base §3.
I did NOT run the full suite. The 3 new pins are RED by design (contract phase); no other suite was
touched. Whether an unrelated failure exists elsewhere is unknown to me — I ran nothing that would show it.

## 11. What ends here / what's next
This ends the CONTRACT phase. I did NOT proceed to build. Next per this repo's cycle: contract-adversary
grades this (especially the #128 fixture discrimination + the FORK A framing), then it PAUSES for operator
review of FORK A. The A2 reconnect-and-retry RED contract (§3.1) is designed but unwritten pending that
ruling.

---

## 12. POST-RULING revisions (operator ruled A1 + 2 secondaries — `RULING-fork-a.md`)

The operator ruled all three decisions-needed per my recommendation
(`docs/plans/v2/receipts/2026-08-17-packet07a/RULING-fork-a.md`). Bounded revisions applied at HEAD
`995a358`; production code remains UNCHANGED (`git diff loremaster/loremaster/{server,scout}.py store/` is
EMPTY):

1. **FORK A → A1.** No reconnect-and-retry code written; A2 stays designed-not-written (§3.1). #164/#250
   adjudicated *does-not-reproduce-at-HEAD, root cause undiagnosed* (see §13 for the F2 correction — NOT
   "fixed-by-05a-ii"); the committed drill + its negative control (`scripts/probe_store_recovery_07a.py`)
   is the deploy-smoke instrument; re-open trigger = packet 16 (#249 RSS restart-policy). Close-out action
   for the lead: resolve findings #164 + #250 with that citation.

2. **#128 wording → distinct contention line, pins TIGHTENED.** The 3 RED pins now assert the EXACT
   operator-ruled line `- #<n> FAILED — store contention, safe to retry this item` for the contention
   case, and the plain-`SurrealStoreError` pin asserts that "safe to retry this item" is ABSENT — so a
   wrong build that catches the `SurrealStoreError` BASE class and labels every store fault "safe to
   retry" reddens (a plain rejection is not known-retryable). **Re-verified:** RED at HEAD (`3 failed`);
   satisfiability GREEN (`3 passed`) against a distinct-wording reference build that catches
   `TxnContentionExhaustedError` → contention line, then `SurrealStoreError` → generic — then reverted
   (server.py diff empty). Ruff clean.

3. **#127 tripwire → WRITTEN + mutation-proven.** `loremaster/tests/test_scout.py::
   TestScoutEnsureConnectionSoleDriverTripwire` — an AST scan (scoped to the `CommandSubscriber` class;
   `scout.py` has a second `run` on the unrelated `Scout` class) asserting the callers of
   `_ensure_connection` are EXACTLY `{run, process_pending_once}`, plus a not-vacuously-green self-guard
   (`{run, process_pending_once} <= callers` first). **GREEN today (`2 passed`); mutation-proven:** a
   temporary 3rd caller added to `CommandSubscriber` made the equality pin RED, naming
   `_mutation_probe_third_caller` in the diff, while the self-guard stayed green — then reverted (scout.py
   diff empty). The connect lock itself is NOT added (the scope #127 declined).

**New reuse ledger row (§9 addendum):** `_command_subscriber_ensure_connection_callers` (test_scout.py, AST
helper) — lore/grep for an existing caller-set scan returned `_discover_socket_owners` (a CONSTRUCTS-a-
socket scan, different property) and `_discover_bootstrap_owners`; neither answers "who CALLS
`_ensure_connection`". Disposition: **HAND-ROLLED**, mirroring `_discover_socket_owners`' AST technique +
its not-silently-finding-nothing self-guard (cited), scoped to one class. The two properties are distinct
scans, not one shareable helper.

**Final pin state:** #128 → 3 RED (`test_mcp_server.py`); #127 → 2 GREEN (`test_scout.py`). Ruff clean on
both files. Ready for the contract-adversary.

---

## 13. ADVERSARY corrections (F1/F2/F3 — `REPORT-adversary-07a-1.md`)

The contract-adversary graded **#128 (3 RED pins) and #127 (tripwire) SUFFICIENT — cleared to build**
(every wrong build it constructed was caught; quantifier table complete; `except`-order guarded). It
graded the **#164/#250 A1 adjudication INSUFFICIENT** on three points, all "re-anchoring, not new logic."
All three fixed here (docs/scripts/receipts only; production code UNCHANGED — `git diff 995a358..HEAD --
loremaster/loremaster/` empty):

**F1 (BLOCKER — false gate, FIXED).** My re-open trigger prose claimed the 20× drill catches "any
regression to the KeyError branch." **Empirically false** (adversary Exp A, reproduced: revert the store's
`(*_CONNECTION_ERRORS, KeyError)` catch → the KeyError unit tests go RED (`2 failed`) but the drill stays
**20/20 green** — the idle bounce raises `ConnectionClosedError`, never a `KeyError`, so it never exercises
that arm). Re-anchored (§1, §B of the contract doc): KeyError-branch regression → the two unit-test classes
(mutation-proven); connection-close regression → the drill (its negative control, F3). **Symbol fixed:**
the store path uses the LITERAL `(*_CONNECTION_ERRORS, KeyError)` tuple in `run_query`/`_txn_query_raw`,
NOT `_SDK_AWAIT_BOUNDARY_ERRORS` (verified: that constant is imported only by `inbox_awaiter.py` +
`scout.py`).

**F2 (ROOT CAUSE — chronologically false, FIXED + escalated).** My "fixed-by-05a-ii" mechanism is
impossible for the store path. **Re-derived myself (not inherited):**

| fact | commit · date | receipt |
|---|---|---|
| `run_query` created ALREADY catching `(*_CONNECTION_ERRORS, KeyError)` + `isinstance(error, KeyError) or is_connection_error` heal | `9d29111` · **2026-07-14** | `git show 9d29111:…/store/_txn.py` → lines 1093–1094, 1289 |
| #164 reported | **2026-07-22** | finding #164 |
| #250 reported (prod repro) | **2026-07-27** | finding #250 |
| 05a-ii adds `_SDK_AWAIT_BOUNDARY_ERRORS` — read ONLY by `inbox_awaiter.py`/`scout.py`, never the store path | `f5aec32` · **2026-08-10** | `grep -rn _SDK_AWAIT_BOUNDARY_ERRORS loremaster/loremaster/` |

The store's KeyError self-heal shipped **8–13 days before** the wedge was ever reported, and 05a-ii never
touched the store path. So the July wedge's **root cause is UNDIAGNOSED** (candidates: a since-changed
cause, or the "server not yet back within the 2 calls anyone tried" timing #250 flags). Corrected in §1,
§2, §3, §12 and the contract doc + the close-out language. The A1 *decision* stands (self-heals 20/20 at
HEAD; both branches guarded); the false *cause* is removed. This also escalates to the operator, since
`RULING-fork-a.md` itself asserts "fixed-by-05a-ii" — the lead has been notified to correct the ruling's
root-cause line.

**F3 (no negative control — FIXED).** The committed drill transcript showed only PASS. Added a **permanent
negative-control leg** to `scenario_negative_control` (the adversary's Exp B): disable the self-heal
(`_drop_connection` → no-op) and require the SAME recovery loop to WEDGE. Re-ran `drill` mode; the
regenerated transcript now carries BOTH `20/20 recovered … ⇒ PASS` (positive) AND `heal-index=None …
⇒ PASS — the drill DETECTS a wedge` (negative control). A rotted drill that always prints PASS now fails
its own self-test. The drill returns a non-zero exit code if the negative control does not hold.

**Not-fixed-by-design (adversary residuals, agreed):** the live in-flight-KeyError coverage stays
SYNTHETIC-only (MP-2) — reliably reproducing a real in-flight `KeyError` under a full bounce is
timing-fragile (my `scenario_inflight_bounce` got an "unspecified rejection", not a `KeyError`), so it is
stated honestly rather than faked. The #127 tripwire's two reach bounds (a cross-class/non-`self` caller;
a concurrent nested driver inside an existing method) are named residuals, not blockers — the tripwire
covers the realistic trigger and fails closed.
