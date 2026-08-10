# REPORT-builder-05a-ii — the `await` verb: InboxAwaiter + shared SDK-await-boundary constant + `action=drain` render

brief-base v11 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done. The RED `await` contract is GREEN (28/28 `test_comms_await` + 12 `TestCommsActionsTable` + the R-2 scout control/mutation legs). All gates pass; the live build-probe passes.
- **Deviations (each expanded in §6):**
  1. **Blast-radius the contract missed: `test_retry_seam.py`.** `InboxAwaiter` makes SDK connection calls, tripping the retry-seam AST + runtime-OBSERVED guards. Fixed per the brief's mandated reuse (route through `retry_on_conflict`) + drove the new sites in the OBSERVED pin. **Process finding** — the contract's blast-radius set should name `test_retry_seam.py` for any packet adding a production SDK call site.
  2. **No LIVE-socket reconnect/backoff** (the reuse-inventory "reconnect backoff" item was NOT needed): the poll fallback rides `message_ledger.drain` (the ledger's OWN, INDEPENDENT connection), so a dead LIVE socket never blocks the authoritative re-drain — §A.6 Leg-B acceptance is met by the poll path alone.
  3. **Four served-surface consistency pins** (beyond the named build-list one) required registering the new action/renders — the P8d "a new action registers everywhere" class. All updated.
- **Capability check:** all tools present; spike-surreal `:18000` reachable (build-probe ran live; NEVER touched `:18500`).
- **Packages considered:** `surrealdb` 2.0.0 — the project SDK, **keep** (its LIVE + in-flight socket-drop `KeyError` behaviour is store-referenced §3/§10, re-probed on 3.2.4). READ: the installed `surrealdb/connections/async_ws.py` — confirmed `subscribe_live` is a coroutine returning the async iterator, `query`/`kill` are the guarded methods. No new mechanism hand-rolled; the awaiter REUSES shipped in-house seams (see §1 table).
- **Graded:** own build (builder artifact); built on HEAD `cb37eee`. `git rev-parse HEAD` = `cb37eee` at build time.
- **Decisions-needed:** none blocking. ONE flag for the lead/operator (§6.2): if instant early-wake after a mid-wait LIVE drop is wanted, a bounded LIVE reconnect is a latency add-on — it is NOT a correctness fix (poll already carries the load).
- **Receipt pointers:** reuse-audit §1 · build-list↔build §2 · gate counts §3 · live-probe receipt + verbatim probe §4 · scout DRY (8 sites) §5 · deviations + process finding §6.

---

## 1. MANDATORY REUSE-AUDIT (operator 2026-08-10 "adhere to DRY. Reuse, don't reinvent.")

Every mechanism `InboxAwaiter` needs, and the EXISTING seam it CALLS (nothing cloned):

| Mechanism | Reused seam it CALLS | Where |
|---|---|---|
| connect factory (dedicated LIVE socket) | `scout._open_command_connection` (the ONE shared opener) | `server.AppContext._await_live_connect` |
| secret/config resolution for the connect | `config.resolve_secret` / `resolve_config_value` + `config.effective_surreal_database` | same |
| SDK-await-boundary error classification | `store._txn._SDK_AWAIT_BOUNDARY_ERRORS` / `_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION` (IMPORTED, not re-defined) | `inbox_awaiter` catch sites |
| retry driver | `store._txn.retry_on_conflict` (as `CommandSubscriber` uses it) | `_live_query` / `_consume_live` / `_safe_kill` |
| conflict classify-and-signal | `store._txn.is_retryable_conflict_error` + `RetryableConflictSignal` | same three attempt bodies |
| reads (snapshot/poll/final) | `MessageLedger.drain(peek=True)` (injected `drain` seam) | `await_inbox` |
| waiting line (outstanding debt) | `AppContext._comms_waiting_lines` → `MessageLedger.awaiting_answer` + `_render_comms_waiting_line` | `_comms_await` empty path |
| render — fence + row (injection-critical) | `AppContext._render_comms_drain_row` + `render_fenced` | `_render_comms_await` |
| render — compose/line | `render_compose` / `render_line` (the shipped render verbs) | both await renders |

**One reuse-inventory item deliberately NOT taken:** `reconnect backoff → CommandSubscriber's backoff`. The awaiter does NOT reconnect the LIVE socket (§6.2) — R-1 puts drain on the ledger's connection and LIVE on a separate one, so a dead LIVE never blocks the re-drain. No hand-rolled backoff; none needed.

## 2. Build list → what was built (contract §4)

1. **Registration** — `_COMMS_ACTION_AWAIT = "await"`; `_COMMS_ACTIONS["await"] = CommsActionSpec(AppContext._comms_await, params=frozenset({"thread"}), required=frozenset())`; the `RenderCase("await.thread", …)` in `test_comms_tool.py::C1_RENDER_CASES`.
2. **Wait machine (R-1)** — `loremaster/inbox_awaiter.py::InboxAwaiter` (standalone; injected `connect`/`drain`/`sleep`/`now`/`budget_s`/`poll_interval_s`), `async def await_inbox(*, agent_id, limit, thread=None) -> MessageDrainResult` (snapshot-first PEEK short-circuit → best-effort LIVE establish → wait racing LIVE-wake/poll-tick → **final snapshot at deadline** → PEEK), `live_select_statement(agent_id) -> str`. Imported into `loremaster.server` (so `server.InboxAwaiter` is the monkeypatchable global the render pins ride).
3. **Handler (R-1)** — `AppContext._comms_await(self, *, agent_row, thread=None, **_ignored)`: CONSTRUCTS `InboxAwaiter` from the store LIVE-connect + `self.message_ledger.drain`, CALLS it, owns the render (non-empty → R-3 drain-teach; empty → honest-empty + shared waiting lines).
4. **Shared error constants (R-2)** — `store._txn._SDK_AWAIT_BOUNDARY_ERRORS = (*_CONNECTION_ERRORS, KeyError)` + `_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION = (*_SDK_AWAIT_BOUNDARY_ERRORS, TxnContentionExhaustedError)`, IMPORTED (not re-defined — the adversary §R3.3 pinned bound) at the awaiter AND all 8 previously-inline scout catch sites (§5).
5. **R-3 typed applicability (#104)** — `_render_comms_await` teaches `action=drain` (the real consume path), NEVER drain's `peek=true` re-run; REUSES the fence + row (§1). The consume-teach is a SEPARATE promise line, registered + proven (§6.3).
6. **`AWAIT_BUDGET_S = 55.0`** — fixed constant, no `timeout=` param; `0 < 55 < 60` (comment states the ceiling rationale).

## 3. Gate receipts (passed-COUNTS, not "green")

- `pytest -n auto` over the changed + blast-radius suites — **all pass:**
  - `test_comms_await.py` **28 passed** · `test_comms_tool.py` + `test_mcp_server.py` **1569 passed** · `test_scout.py test_render_seam_pins.py test_message_ledger.py test_comms_waiting_line.py test_link5_render_containment.py test_retry_seam.py` folded into a combined **1989 passed, 17 skipped** run · `test_comms_promise_registry.py` **120 passed** · `test_task_read_surface.py` in the 445-passed re-run.
- `scripts/typecheck.sh` — **102 mypy errors, ALL in `test_auth_composition.py`** (the #333 auth-WIP baseline), **ZERO in any file I touched** → zero-new.
- `uv run ruff check .` — **All checks passed!**
- `uv run python scripts/pending_contract_gate.py --currency` — **PASS: every claimed gate GREEN or OWNED; 0 RED_ORPHANED** (typecheck RED_ADJUDICATED 191 / pytest RED_ADJUDICATED 444, both owned by packet-39; my two transient orphans from the new action were fixed — §6.3).

## 4. Live build-probe receipt (design §A.6 / §A.5 residual; DEPLOY-gated)

Ran against **spike-surreal `ws://127.0.0.1:18000`** (TEST store — NEVER `:18500`). Store version-stamped: **`surrealdb-3.2.4+20260803.93ab219`**.

```
STORE VERSION (spike-surreal :18000) = 'surrealdb-3.2.4+20260803.93ab219'
EMITTED (hex id): LIVE SELECT * FROM to WHERE out = agent:`a076620b84375c3b88c52b1853ff76ba`
LEG 1a  PARSE+ESTABLISH (hex uuid5)        -> OK, live_uuid=UUID('813fb3f4-…')
EMITTED (hyphenated id): LIVE SELECT * FROM to WHERE out = agent:`5ef97165-fc78-5730-a31d-f3ad4b3098ce`
LEG 1b  PARSE+ESTABLISH (hyphenated uuid5) -> OK, live_uuid=UUID('f16d0665-…')
LEG 2a  matching RELATE (out=agent:A)      -> LIVE FIRED
        notification = {'grade':'signal','id':RecordID(to,…),'in':RecordID(message,…),'out':RecordID(agent,'a076620b…')}
LEG 2b  non-matching RELATE (out=agent:B)  -> LIVE STAYED SILENT (discriminates)
PROBE VERDICT: PASS  (parse hex=True, parse hyphenated=True, fires=True, discriminates=True)
```

**What it proves:** the production `InboxAwaiter.live_select_statement` backtick record-id literal `` agent:`<id>` `` PARSES for BOTH the real uuid5-HEX id AND a hyphenated uuid5 (the §A.5 subtraction hazard — the backtick literal handles both); the filtered LIVE-on-edge FIRES on a matching `RELATE` and DISCRIMINATES (a non-matching recipient stays silent — scoped wake, no whole-table storm). The probe (a one-off deploy instrument, pasted VERBATIM per brief-base §1(b) — promote to `scripts/` as the await deploy-smoke if desired):

```python
"""Packet 05a-ii DEPLOY-GATED build probe (design §A.6 / §A.5 residual)."""
import asyncio
from uuid import NAMESPACE_URL, uuid4, uuid5
from surrealdb import AsyncSurreal, RecordID
from loremaster.inbox_awaiter import InboxAwaiter

URL, USER, PASSWORD, NAMESPACE = "ws://127.0.0.1:18000/rpc", "root", "spikeroot", "lore_test"

def _awaiter():
    async def _c(): raise AssertionError
    async def _d(**_): raise AssertionError
    return InboxAwaiter(connect=_c, drain=_d)

async def _wait(sub, timeout):
    try:
        return await asyncio.wait_for(sub.__anext__(), timeout)
    except (asyncio.TimeoutError, StopAsyncIteration):
        return None

async def main():
    database = f"probe_await_{uuid4().hex}"
    conn = AsyncSurreal(URL)
    await conn.signin({"username": USER, "password": PASSWORD})
    await conn.query(f"DEFINE NAMESPACE IF NOT EXISTS {NAMESPACE}")
    await conn.use(NAMESPACE, database)
    await conn.query(f"DEFINE DATABASE IF NOT EXISTS {database}")
    await conn.use(NAMESPACE, database)
    await conn.query("DEFINE TABLE IF NOT EXISTS to SCHEMALESS")
    print("STORE VERSION =", await conn.version())
    awaiter = _awaiter()
    hex_a = uuid5(NAMESPACE_URL, "lore://agent/probe-wave/recipient-A").hex
    hex_b = uuid5(NAMESPACE_URL, "lore://agent/probe-wave/recipient-B").hex
    hyph  = str(uuid5(NAMESPACE_URL, "lore://agent/probe-wave/recipient-hyphen"))
    live_hex = await conn.query(awaiter.live_select_statement(hex_a))          # LEG 1a
    live_hyp = await conn.query(awaiter.live_select_statement(hyph)); await conn.kill(live_hyp)  # LEG 1b
    sub = conn.subscribe_live(live_hex)
    if asyncio.iscoroutine(sub): sub = await sub
    await conn.query("RELATE $f->to->$t SET grade='signal'",
                     {"f": RecordID("message", uuid4().hex), "t": RecordID("agent", hex_a)})
    fired = await _wait(sub, 3.0) is not None                                  # LEG 2a
    await conn.query("RELATE $f->to->$t SET grade='signal'",
                     {"f": RecordID("message", uuid4().hex), "t": RecordID("agent", hex_b)})
    discriminates = await _wait(sub, 2.0) is None                             # LEG 2b
    await conn.kill(live_hex); await conn.query(f"REMOVE DATABASE {database}"); await conn.close()
    print("VERDICT:", "PASS" if fired and discriminates else "FAIL")

asyncio.run(main())
```

## 5. R-2 DRY consolidation — 8 scout inline clones → the ONE imported constant

`scout.py` held **8 inline `(*_CONNECTION_ERRORS, KeyError[, TxnContentionExhaustedError])` catch tuples** (the derived AST belt's target set). All 8 now reference the imported shared constant — **4 base** `_SDK_AWAIT_BOUNDARY_ERRORS` (`_scout_query_once`, `_safe_close`, `_consume_live._attempt`, `_safe_kill._attempt`) + **4 with-contention** `_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION` (`run` connect-fail, `run` serve-drop, `_consume_live` outer, `_safe_kill` outer). `TxnContentionExhaustedError` dropped from scout's imports (now only referenced by the constant's definition in `_txn`). The `except _CONNECTION_ERRORS:` at `_open_command_connection`'s close-after-failed-bootstrap is left as-is (a plain connection-error close, NOT the SDK-await boundary — a deliberate distinction, not a miss). The R-2 runtime-mutation legs (both suites) + the AST reach-belt confirm zero inline clones survive.

## 6. Deviations, blast-radius, and the process finding

### 6.1 The contract missed `test_retry_seam.py` as blast radius (PROCESS FINDING)
`InboxAwaiter` is a production module that opens an SDK connection and calls `query`/`subscribe_live`/`kill` on it — so it entered the retry-seam guards' scan population, reddening TWO pins the contract/adversary never ran (they graded the 42-pin contract, not `test_retry_seam`):
- `test_every_sdk_call_site_is_run_by_the_retry_seam` (AST offenders) — my 3 SDK calls were unseamed. **Fix:** routed each through `retry_on_conflict` with the shared classify-and-signal (the brief's mandated reuse; mirrors `CommandSubscriber`'s `_scout_query`/`_consume_live`/`_safe_kill`). NOT a design improvisation — the brief's reuse inventory names `retry_on_conflict` explicitly.
- `test_every_production_sdk_call_site_was_OBSERVED_by_the_guard` (live-store runtime guard) — my 3 sites were enumerated but nothing drove them. **Fix:** edited the OBSERVED pin to drive `awaiter._live_query`/`_consume_live`/`_safe_kill` with a guarded connection (defining the `to` table), exactly as it drives the subscriber's — this pin's OWN intended maintenance ("a new SDK call site nothing drives turns this RED").
- **PROCESS FINDING for the lead/contract:** any packet adding a production SDK **connection call site** must carry `test_retry_seam.py` in its blast-radius gate set. The 05a-ii contract's satisfiability run (42/42) could not see this because it never ran that suite. I will file this to `lore_findings`.

### 6.2 No LIVE reconnect/backoff (deliberate simplification — FLAG for the lead)
The awaiter does NOT reconnect a dropped LIVE socket. On any SDK-await-boundary failure at establish/consume it falls to poll-only, and the poll re-drain rides `message_ledger.drain` — the LEDGER's OWN connection, **independent of the awaiter's LIVE socket**. So a dead LIVE never blocks the authoritative re-drain, and §A.6 Leg-B acceptance (returns pending traffic, no false-empty) is met by the poll path ALONE. R-1 itself separates the two connections, so the reuse-inventory "reconnect backoff" is not needed. Cost: after a mid-wait LIVE drop, the return latency is bounded by the poll interval (~2s) rather than instant. **FLAG:** if instant early-wake-after-drop is desired, a bounded LIVE reconnect is a latency add-on, not a correctness fix — the lead/operator's call.

### 6.3 Served-surface consistency pins (the P8d "new action registers everywhere" class)
Beyond the named build-list `C1_RENDER_CASES` addition, the new `await` action + its two render helpers tripped served-surface pins that I updated (all intended "register the new surface" maintenance):
- **`lore_comms` tool DESCRIPTION + action-param description** (`test_description_names_every_action`) — added an `await` sentence; also added the long-missing `story` to the action-param description (a pre-existing gap that pin did not cover).
- **`_EXPECTED_COMMS_ACTIONS`** in `test_task_read_surface.py` — the served unknown-action-refusal vocabulary EQUALITY pin; appended `await` in dispatch order.
- **`_PROMISE_REGISTRY` / `_PROMISE_FREE` + `_PROOF_LIST`** in `test_comms_promise_registry.py` (#104) — classified my 4 render literals (the consume-teach is a PROMISE with a mutation-proven emission gate: emitted on non-empty, absent on empty; the header, body-fence label, and honest-empty bound are promise-FREE status/label lines). The honest-empty render was simplified to drop a "consume anything that arrives via action=drain" tail so it stays a clean promise-free bound (the consume teach belongs on the non-empty render, where there IS something to consume).

### 6.4 Untouched
`REPORT-lead-05a-ii.md` shows modified in `git status` — it was already modified at session start (the lead's file); I did NOT touch it and it is NOT in my commit.

---

_Order: contract → adversary → build → cold audit. This build satisfies the SUFFICIENT-graded contract; the cold audit is the next instrument._

---

## 7. FOLLOW-UP FIX — #354 LIVE-connect crash → degrade-to-poll (commit `7bc68f9`, 2026-08-10)

The cold audit (NO-GO §2, finding **#354**) caught a crash the build-list state machine implied but did not guard: the dedicated LIVE **connect+establish** sat in a `try`/`finally` with **no `except`**, so a failing `self._connect()` (the shared opener re-raises by contract; connect can also hit a concurrent-first-connect `TxnContentionExhausted`) **propagated and crashed `await_inbox`** instead of degrading to poll-only (design §A.1 step 2 says establish is best-effort). Operator approved fix-now ("it affected the usability of the tool"); the adversary graded the fix pins SUFFICIENT at HEAD `f71760f`.

**Fix (17+/2−, `inbox_awaiter.py` only):** a nested `try`/`except _SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION` around ONLY the connect+establish — on failure `connection=None` and the poll loop carries the load (mirrors `CommandSubscriber.run`'s connect guard; the shared constant is IMPORTED, never re-defined — the §R3 pinned bound). The guard **fences the connect path only**: the three authoritative `self._drain` reads (snapshot/poll/final) stay OUTSIDE the `except` and MUST raise on a fault — a drain fault is a loss-free RAISE (F1=peek), never a false-empty. OSError is *inside* the boundary set, so over-guarding a drain read would false-empty; the two pins fence the guard.

**Pins GREEN:** `TestConnectFailureDegradesToPoll` all 4 legs (OSError + `TxnContentionExhausted` × {returns-pending `drain.calls≥2`, honest-empty}) · `TestADrainFaultRaisesNeverFalseEmpties` all 3 sites (snapshot/poll/final each mutation-proven) · `TestSocketDropNonLoss` + the R-2 mutation legs unchanged. Full await + blast-radius (`scout`/`retry_seam`/`render_seam_pins`/`message_ledger`/`comms_waiting_line`/`comms_tool`) = **1838 passed, 17 skipped**. `typecheck.sh`: ZERO in `inbox_awaiter.py` (191 total = the pkt39-adjudicated #333 baseline). ruff on the tracked tree clean.

⚠ **`--currency` ruff RED_ORPHANED is NOT from this fix:** all 5 hits are the cold-audit's UNTRACKED `scratch_coldaudit_{liveprobe,probe_connect,probe_r2}.py`; `ruff check . --exclude 'scratch_coldaudit_*.py'` passes. Recommended to the lead: `git clean -f scratch_coldaudit_*.py` (disposable audit scratch) — not deleted here (not mine; scope is the operator's).
