brief-base v14 read · brief project v7 read

# REPORT — fable-sidecar-07a — packet 07a design analysis (WORKING, pre-probe)

## SUMMARY BLOCK
- state: **standing by** — working design analysis delivered; the #164 *mechanism* recommendation is **PROBE-GATED** (waiting on `contract-07a-1`'s live spike-surreal 3.2.4 bounce).
- deviations: none.
- Packages considered: **none new** — the #164 reconnect rides the EXISTING `_txn.retry_on_conflict` driver + `bootstrap_session` + the SDK's own reconnect; #128 reuses the existing per-item best-effort loop. No new dependency specified. (The retry/backoff substrate is the audited in-house `retry_on_conflict` — the ONE driver, #102/#108/#120 — deliberately not a package, settled in that wave.)
- Reuse ledger: **none** — design analysis, no new production symbols authored here.
- Graded: 995a358 · HEAD-at-report: 995a358 · SAME. (All code read as-of-HEAD; symbol-cited, not line-cited.)
- decisions-needed:
  1. **#164 mechanism** — probe-gated fork (§2): reconnect-and-retry-within-one-call vs. keep-drop-and-fix-the-reconnect-path. Decides after the probe reveals WHERE it wedges + the exact 3.2.4 error shape.
  2. **#128 abort-vs-fail on contention** (§3) — my recommendation: per-item FAILED-and-CONTINUE (contention ≠ dead socket). Operator/lead confirm the render wording.
  3. **#126 re-open** (§4) — needs the latency telemetry the trigger names; and MUST be re-adjudicated against the SHIPPED 07a seam, not today's.
  4. **#127 lock now vs renew** (§5) — my recommendation: RENEW latent (07a does not add a second scout caller), + a cheap sole-driver tripwire pin.
- receipt POINTERS: mechanism map §1 · #164 fork §2 · #128 fix §3 · #126 §4 · #127 §5 · corpus-verification result §6 · probe worklist for contract-07a-1 §7.

---

## 1. Confirmed mechanism map (read at 995a358 — citations, not memory)

The whole error seam is `loremaster/loremaster/store/_txn.py` (the ONE audited home, #102/#108/#120). Every single-statement owner routes through it.

- **Classification** — `_txn.is_connection_error(error)`: a raw `WebSocketException`/`OSError` → **always `True`** (transport); a `ServerError` → `True` only if `error.kind ∈ _CONNECTION_ERROR_KINDS = {NOT_ALLOWED, CONNECTION}`; every other kind → `False` (domain). `_txn.is_retryable_conflict_error(error)` → matches the literal `_RETRYABLE_CONFLICT_MARKER = "can be retried"`.
- **Retry driver** — `_txn.retry_on_conflict(attempt, …)` retries **ONLY** a `RetryableConflictSignal`. Anything else `attempt` raises propagates UNTOUCHED, **zero retries**. Its docstring names the reason this is deliberate: *"a transport fault may already have committed (retrying would double-apply — the at-most-once rule) and a domain rejection can never succeed, so only the signal is ever caught."* **This is the load-bearing constraint for #164** (§2).
- **Single-statement body** — `_txn.run_query(...)`. Its inner `_attempt()`:
  - `connection = await acquire()` — the connection is acquired **INSIDE** the retried attempt (adversary R-3, so a retry re-acquires after a drop).
  - on `except (*_CONNECTION_ERRORS, KeyError)`: if `KeyError or is_connection_error(error)` → `await drop(connection)` (self-heal) then **raise `SurrealConnectionError`** (NOT a signal → not retried); elif `is_retryable_conflict_error` → raise `RetryableConflictSignal` (retried); else → domain `SurrealStoreError`.
- **Store seam** — `SurrealStore._query` passes `acquire=self._ensure_connection`, `drop=self._drop_connection`. `_ensure_connection` (double-checked lock): fast path returns the cached handle; on miss it constructs `AsyncSurreal(url)` → `signin` → `bootstrap_session`, wrapping ANY failure as `SurrealConnectionError`. `_drop_connection` is a compare-and-swap: nulls `self._connection` **iff it is still the failed handle**, then closes.
- **Bootstrap** — `_txn.bootstrap_session` is THE ONE session bootstrap (DEFINE NS / `use()` / DEFINE DB), retried through `retry_on_conflict` under ONE composed wall-clock budget. It NEVER wraps its own exhaustion — the wrap belongs at the seam (store wraps → `SurrealConnectionError`; scout does not wrap, by design).
- **Scout** — `CommandSubscriber.run()` is a **bounded-backoff reconnect LOOP**: `_ensure_connection` (a bare check-then-set, NO lock — this IS #127) → `_serve`; on `_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION` it `_drop_connection()` + backoff + re-loops. Scout does **not** use `run_query`; it has its own disposition loop. So scout ALREADY reconnects on a bounce — the store does not (it drops + raises, healing on the caller's next call).

### The wedge, precisely (#164 / #250)
On a store bounce the held WS dies. The next `SurrealStore._query`:
1. `_ensure_connection` returns the cached **dead** handle (fast path — `_connection is not None`).
2. `connection.query()` raises `websockets` `ConnectionClosedError` → `"no close frame received or sent"` (a `WebSocketException`). `is_connection_error` → `True`.
3. `drop(connection)` nulls `self._connection`, closes; raises `SurrealConnectionError` — **not retried**.

By the code, the **next** call should see `_connection is None` and reconnect. **But #250 observed the second call ALSO failed with the identical string, no heal** — which the code as-read does NOT explain. So the wedge is NOT simply "we never retry": it is either (a) the reconnect path itself re-fails (server not yet back within those seconds; or the fresh `AsyncSurreal`/signin re-raises the same WS error against a still-restarting server), or (b) the drop's CAS didn't clear the handle for some reason, or (c) the SDK object wedges in a state that neither cleanly raises-to-drop nor reconnects. **Which one it is decides the fix** — hence the probe (§7). The `SurrealConnectionError` message format in #164/#250 (`SurrealDB query failed against '…': no close frame received or sent`) is `run_query`'s exact wording, so we know the error DID reach the connection branch and `drop` DID fire on call 1.

---

## 2. #164 / #250 — the design fork (PROBE-GATED)

**The hard constraint:** `retry_on_conflict` refuses to retry a transport fault BECAUSE a write in flight when the socket dropped may already have committed server-side — blind retry = double-apply. Any "reconnect-and-retry" MUST respect at-most-once for WRITES. So the packet's "classify dead-socket as RECONNECT-AND-RETRY" cannot be a blanket retry of every `SurrealConnectionError`.

**The safe distinction the store reference §3 already hands us — two error SHAPES:**
- **In-flight drop** → raw `KeyError(request-uuid)` (SDK 2.0.0 response-routing race; §3, re-probed unchanged on 3.2.4). The query WAS on the wire → may have committed → **must NOT auto-retry a write**. Keep as today: drop + raise, heal next call.
- **Pre-send / socket-already-dead** → `WebSocketException`/`ConnectionClosedError` ("no close frame") or `OSError`. The socket was dead BEFORE we sent (the #164 held-connection-died-on-bounce case) → the statement never reached the server → **safe to reconnect-and-retry** even for a write. This is #164's exact shape.

  ⚠ This mapping (KeyError=in-flight-unsafe, WebSocketException=pre-send-safe) is an INFERENCE from §3's two probes; it is NOT proven that a `WebSocketException` can never surface mid-flight. **The probe must confirm the boundary before we lean on it** (§7). If it can't be cleanly separated by error type, fall back to the idempotency axis below.

**Idempotency axis (the always-sound fallback):** a READ (SELECT) is idempotent → reconnect-and-retry is safe regardless of shape; a WRITE is not. All three #164/#250 receipts are `lore_index()` — read-heavy. `run_query` does not today know read-vs-write. If the error-shape split does not hold under probe, the conservative fix is to let callers declare idempotency (a `retry_on_reconnect: bool` on `run_query`, default False; True for the read seams) — NOT to auto-retry every write.

### Options
- **Option A — reconnect-and-retry within ONE call (packet's literal intent).** In `run_query._attempt`, for a *safe* connection error (pre-send shape, or an idempotent statement): `await drop(connection)` then raise a NEW `ReconnectRetrySignal`; teach `retry_on_conflict` to retry it too (it already sleeps/bounds/【floor+ceiling+deadline】). Because `acquire()` is inside `_attempt` and the handle was dropped, the next iteration reconnects via `bootstrap_session` and re-runs the statement — healing within the existing composed budget, no second connect path (#120 satisfied). Preserve today's drop-and-raise for the KeyError/in-flight/unsafe-write shape.
  - This is the cleanest match to the packet text AND to scout's philosophy (retry after reconnect). It ships the heal into the SHARED seam, so every one of the eleven owners gets it for free.
- **Option B — keep drop-and-raise; fix the RECONNECT PATH.** If the probe shows the drop works but `_ensure_connection`'s reconnect re-fails (e.g. the SDK object needs full re-construction, or a signin-after-restart race), the fix is in `_ensure_connection`/`bootstrap_session`, not classification. Then #164 is "make the next-call reconnect actually succeed," and Option A is unnecessary (or complementary).

**My recommendation (to finalize post-probe):** implement **Option A** for the pre-send/idempotent shape — it directly delivers "recover WITHOUT a container restart, mid-flow" and puts the policy in the shared seam — AND verify the reconnect path (Option B's concern) is sound, since A depends on `bootstrap_session` succeeding on the retry. If the probe shows the reconnect itself is what's broken, B is mandatory and A rides on top of it. Either way: NO new connect path, NO retry-budget/jitter change (scope OUT), reconnect rides `bootstrap_session`.

**Removed-behaviour guard (the dual):** whatever ships, the at-most-once refusal that `retry_on_conflict` documents is a BEHAVIOUR being partially reversed — inventory it and pin that a genuinely in-flight write is STILL not auto-retried (the quantifier law: pin the outcome ∀ shapes — pre-send→retried, in-flight-write→not-retried, domain→not-retried, conflict→retried).

---

## 3. #128 — per-item degradation (DECIDED, with a recommendation)

Seam: `AppContext._resolve_or_acknowledge_many` (server.py, `_FINDING_BATCH_VERB` loop). Today it catches, per item, `SurrealConnectionError` (→ set `aborted`, ABORT all remaining) and the domain trio `(_FindingNotFoundError, _FindingIllegalTransitionError, ValueError)` (→ per-item FAILED, continue). **`TxnContentionExhaustedError` and plain `SurrealStoreError` match neither clause → they propagate and kill the whole batch response.** Both are `SurrealStoreError` subclasses; `SurrealConnectionError` is too (caught first, correctly).

**Fix shape:** add an `except SurrealStoreError` clause **AFTER** the `except SurrealConnectionError` (order is load-bearing — the connection subclass must be caught first to keep abort-all) rendering a **per-item FAILED-and-CONTINUE** line, sanitised via `_sanitise_line`.

**The design call — why FAIL-and-continue, not abort-all:** a `SurrealConnectionError` aborts because the socket is dead and the rest cannot be attempted. A `TxnContentionExhaustedError` is the OPPOSITE: the connection is HEALTHY, this item just lost a write-write race after exhausting retries; the NEXT item (different row, maybe less contention) can well succeed. Aborting the batch on contention would throw away recoverable work and under-serve the best-effort contract. So contention → per-item FAILED, continue.

**Trust-doctrine wording:** contention is genuinely *retryable*, unlike a domain rejection. Recommend a DISTINCT line for it so the render doesn't over- or under-claim, e.g. `- {ref} FAILED — store contention, safe to retry this item` (vs. the domain trio's `FAILED — {reason}`). A plain `SurrealStoreError` (unexpected non-trio rejection) → `FAILED — {sanitised reason}`. Lead/operator confirm the exact strings.

**Contract must (packet + quantifier law):** force EVERY fate with a fixture — success · domain-FAILED · connection-ABORT-all · **contention-FAILED-continue** · plain-store-error-FAILED-continue — and a REAL-contention concurrency pin, **20-consecutive** (a single green run never clears a concurrency test, §5 store-ref / CLAUDE.md). The pin must land a `TxnContentionExhaustedError` on ONE mid-batch item and assert the items AFTER it still process. Fixtures must DISCRIMINATE (what wrong build passes?) — e.g. a build that catches contention but ALSO aborts must go RED (so the fixture needs ≥1 item after the contended one that MUST still succeed).

---

## 4. #126 — retry-under-lock latency composition (adjudication)

Status: ACCEPTED bounded-by-design; re-open trigger = *"production or smoke telemetry showing multi-second p99 stalls on scout command dispatch or on cold `_ensure_connection` under real fleet load."*

- **The trigger is a LATENCY signal, and #250 is NOT it.** #250/#164 is a total WEDGE (no heal), not a p99 stall — a different failure. So #250 does not, by itself, meet #126's named trigger.
- **Adjudication needs the telemetry the trigger names.** Recommend the contract author / a Mezmo pass check `store.retry.exhausted` records and cold `_ensure_connection` timings under fleet load. Absent evidence of multi-second p99 stalls → **RENEW** the acceptance with the trigger unchanged.
- **⚠ The interaction that MUST be written into the verdict:** 07a's #164 fix (if Option A) adds reconnect-and-retry INTO the composed budget — it GROWS the worst-case latency composition #126 is about (outer retry floor × inner bootstrap, now × a reconnect). So #126 must be **re-adjudicated against the SHIPPED 07a seam, not today's** — the magnitude the acceptance rests on changes. This is the rider that would otherwise be dropped (THE RIDER IS PART OF THE RULING).

---

## 5. #127 — scout `_ensure_connection` no-lock (adjudication) + the two-policies question

Status: latent-by-design; re-open trigger = *"any change that adds a second caller of `scout._ensure_connection`, or makes scout construct its own socket."*

- **Does 07a meet the trigger? No (as scoped).** The #164 fix lives in the STORE's `run_query`/`_ensure_connection`/`bootstrap_session`. `scout._ensure_connection` is called ONLY from `run()` (confirmed by read). 07a adds no second scout caller and does not make scout construct its own socket. → **RENEW latent.**
- **Recommendation:** do NOT add the lock (adding an untested lock to a single-caller path is exactly the scope the original decision declined). BUT the existing P-2 pin enumerates classes whose `_ensure_connection` *constructs* `AsyncSurreal` — scout's does NOT (it calls `self._connect()`), so scout is NOT captured by that tripwire. Recommend a cheap **sole-driver structural pin** ("`run()` is the only caller of `scout._ensure_connection`") so the latent acceptance has a real tripwire, per WHEN YOU CANNOT CLOSE A HOLE, PIN IT.
- **The "two reconnect policies" concern (packet: adjudicate #127+#164 together):** the store's reconnect (07a) and scout's reconnect (`run()` ladder) are STRUCTURALLY DISTINCT loops — discrete-query self-heal vs. long-lived-subscription re-serve — and that difference is INHERENT to the two usage patterns, not a duplication. **ONE IMPLEMENTATION is satisfied at the MECHANISM layer, which is what matters:** both ride the SAME shared `bootstrap_session`, the SAME `is_connection_error`/`_SDK_AWAIT_BOUNDARY_ERRORS` classification, and the SAME `retry_on_conflict`. The disposition LOOP differs, correctly. **The adjudication's job is to ensure 07a's new reconnect classification is added to the SHARED classifier/signal, not hand-rolled in `run_query` alone** — so scout's ladder and the store's retry agree on what "reconnectable" means (routing-is-not-sharing: if #164 introduces a `ReconnectRetrySignal` or widens a predicate, it must be the shared one both seams read).

---

## 6. Operator's added law (2026-08-17) — corpus verification result

Order applied: (1) `docs/reference/surrealdb-31-capabilities.md` → (2) `surrealql-tests` → (3) `surrealdb-docs` → (4) live probe.

- **§ store reference (1):** §3 documents the socket-drop shape (KeyError → next call ConnectionClosedError) — but that probe was a **client-side socket drop with queries IN FLIGHT**, explicitly NOT a full SERVER restart. #250 already flags this scope gap. §0 quotes the 3.2.1 release notes' `Session not found` router-race fix (#308) as a **`[VENDOR]` release-note claim, NOT probed**.
- **`surrealql-tests` (2):** searched session/reconnect/connection-drop. The only hit is `tests/language/functions/session.surql` — it tests `session::*` GETTER semantics (NONE-or-typed), a QUERY-LANGUAGE property. **There is NO executable language test for transport-layer reconnect / session-loss healing** — the CI SurrealQL suite doesn't exercise the WS transport. So the executable-spec tier does NOT settle #308 or #250's healing question.
- **`surrealdb-docs` (3):** the nearest hit is the Python SDK `.new_session()` API page — a WS-only **3.x SDK** feature; our SDK is pinned **2.0.0** (no `.new_session()`), so it does not describe our reconnect path. Vendor prose can lie (§6 has receipts) and here it isn't even on-version.
- **CONCLUSION (a design output in itself):** applied honestly, the operator's "verify against stored tests + docs" law returns **"these corpora do not cover transport-layer reconnect behaviour."** So the #308 router-race claim and #250's full-restart healing question are settled ONLY by order-step (4): **a live probe against spike-surreal 3.2.4** — which is precisely the packet's Entry Check mandate. The docs-first law is satisfied (we read them first and found the gap); the probe is now the authority, and its transcript must be committed as a tracked receipt (not scratchpad/tmp — #152/#153).

---

## 7. Probe worklist for `contract-07a-1` (what the live bounce must SETTLE)

Against spike-surreal `ws://127.0.0.1:18000` (TEST — never :18500). Commit the transcript as a tracked receipt under `docs/plans/v2/receipts/<date>-packet07a/`.

1. **Exact error shape of a FULL SERVER RESTART** (`systemctl --user restart spike-surreal.service`) with a held connection, on the NEXT query — is it `WebSocketException`/`ConnectionClosedError` ("no close frame"), an `OSError`, or a `ServerError`? Confirm `is_connection_error` classifies it as transport.
2. **Does the store's current design heal on the 2ND call?** Reproduce #250: hold a `SurrealStore` connection, bounce the server, issue two `_query` calls. Does call 2 reconnect (as the code says it should) or wedge (as #250 observed)? This decides Option A vs B (§2). If it wedges, find WHERE — dead-cached-handle-not-dropped, or reconnect-re-fails, or SDK object poisoned.
3. **In-flight vs pre-send boundary** (§2): does a query dropped WHILE IN FLIGHT give `KeyError` (per §3) and a query sent to an ALREADY-dead socket give `WebSocketException`? If the two shapes don't cleanly separate, the idempotency axis (read-vs-write) is the fallback for at-most-once safety. **A probe needs a control** — pair the "reconnect healed it" observation with a negative (a genuine domain rejection is NOT reconnected) and a positive (a healthy write DID commit).
4. **#308 router-race:** does a rapid reconnect after restart ever surface `Session not found`? (Vendor claims 3.2.1 fixed a cold-start race; unprobed by us.)
5. **20-consecutive drill:** bounce mid-flow, verify recovery without a container restart, 20 times in a row (a single green never clears it).
