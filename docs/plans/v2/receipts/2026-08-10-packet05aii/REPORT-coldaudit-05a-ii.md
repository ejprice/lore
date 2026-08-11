# REPORT-coldaudit-05a-ii — cold REFUTE audit of the `await` build (packet 05a-ii)

brief-base v11 read
brief project v7 read

## SUMMARY BLOCK
- **VERDICT: GO** (updated 2026-08-10 by the §8 DELTA re-audit at HEAD `c1e1b31`). The
  original audit returned **NO-GO** on BLOCKER #354 (a LIVE-**connect** failure crashed
  `await_inbox`); the builder's connect-guard at `7bc68f9` CLOSES it — re-verified
  empirically (§8). All other findings were GO at the original audit and are unchanged
  (scout/server/`_txn` byte-identical since `f5aec32`). **The build is GO for deploy.**
- **State:** done (delta re-audit complete; I do not fix).
- **Graded:** original **f5aec32**; DELTA re-audit **c1e1b31** (HEAD; = `7bc68f9` fix +
  two docs-only commits `ae7fe18`/`c1e1b31`; the brief said HEAD `ae7fe18` but true HEAD is
  `c1e1b31` — both docs, production code identical). HEAD-at-report: c1e1b31 · **SAME**.
- **Gates (re-derived independently, not relayed):** pytest 8-suite **2476 passed / 17 skipped, exit 0**
  · typecheck **191 residual, ZERO in any touched file** (= #333 baseline, RED_ADJUDICATED→pkt39)
  · ruff **clean** · currency **PASS, 0 RED_ORPHANED**.
- **R-2 sharing:** PROVEN by IDENTITY (both consumers' constants ARE the same `_txn` object —
  no clone) + consumer-global runtime mutation (recovery breaks). §R3.3 residual clone does
  NOT exist in this build. One documented nuance: the brief's literal "patch `store._txn`"
  does NOT propagate (consumers use `from _txn import` — a value snapshot), which is Python
  import semantics, NOT a clone (identity already proves same-source).
- **Packages considered:** `surrealdb` 2.0.0 (project SDK) — no re-evaluation; I READ the
  installed in-flight-drop `KeyError` behaviour via store reference §3 (re-probed 3.2.4,
  #336) and the build's use of it. No mechanism specified by this audit.
- **Provenance:** every probe ran in-tree — `loremaster.__file__ =
  /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py` (#140 law).
- **Decisions-needed:** ONE — fix #354 now vs. accept as a pinned bound (operator's call; §2).
- **Receipt pointers:** gates §1 · the BLOCKER + verbatim probe §2 · R-2 mutation §3 ·
  scout 8-site adjudication §4 · injection+render+live probe §5 · DRY/#353 §6 · residuals §7.

---

## 1. Gates — re-run by me, passed-COUNTS in the tails (task 1)

All four independently re-run at HEAD `f5aec32`.

| Gate | Command | Result |
|---|---|---|
| pytest (8 suites) | `pytest -n auto` over the brief's 8 suites | **2476 passed, 17 skipped, 1 warning in 189.71s; exit 0** |
| typecheck | `scripts/typecheck.sh` | exit 1 — **191 mypy residual**, ALL in the #333 auth-WIP / lorerunes-roster cluster (102 loremaster auth + 89 lorerunes posture/roster/email); **ZERO in inbox_awaiter.py / scout.py / server.py / store/_txn.py** (grep-confirmed) → **zero-new** |
| ruff | `uv run ruff check .` | **All checks passed!** |
| currency | `scripts/pending_contract_gate.py --currency` | **PASS** — typecheck RED_ADJUDICATED(191, owner packet-39), pytest RED_ADJUDICATED(444, owner packet-39), ruff GREEN; **0 RED_ORPHANED** |

Core new suite alone: `test_comms_await.py` = **28 passed** (0.76s). No failures anywhere in
the 8-suite run (grep of the log for `failed`/`error` outside `0 errors` = empty). The 191
typecheck residual matches the brief's accepted `~191` baseline exactly. **Gates: GO.**

## 2. THE BLOCKER — LIVE-connect failure crashes `await_inbox` (task 2; finding #354)

**The load-bearing non-loss question, split into its two real cases:**

- **Socket-DROP mid-await (the contract's non-loss pin, `TestSocketDropNonLoss`): HOLDS.**
  My positive control (connect succeeds, LIVE establish raises the probed `KeyError` in-flight
  shape, `dead=True`) **recovered via poll** (`drain.calls=2`, returned the pending traffic).
  So the brief's *literal* NO-GO trigger — *a drop producing a false-empty* — is **NOT met**.
  `_establish_live`/`_consume_live` correctly catch `_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION`
  and fall to poll; the drain rides the ledger's INDEPENDENT connection, so a dead LIVE socket
  never false-empties.

- **CONNECT-failure (LIVE socket never establishes): CRASHES.** `await_inbox` (`inbox_awaiter.py`
  ~line 152) runs `connection = await self._connect()` inside a `try`/**`finally`** with **no
  `except`**. The connect factory (`server._await_live_connect` → `scout._open_command_connection`)
  is **deliberately UNWRAPPED** (its own docstring, `W1-SCOUTKILL`): it re-raises RAW SDK types
  (`_CONNECTION_ERRORS` members) and `TxnContentionExhaustedError`, *by contract* expecting the
  caller's reconnect ladder to catch. `CommandSubscriber.run` **does** catch it
  (`except _SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION: backoff+retry`). The awaiter reuses the
  shared opener but **drops that caller-catch discipline** — so a failed LIVE connect propagates
  straight out and crashes the `await` tool call (no softening catch exists: `comms()` dispatch
  is a bare `return await spec.handler(...)`; `_comms_await` does not wrap the call).

**Reproduced (positive-controlled):**
```
A connect->OSError        : RAISED OSError  drain.calls=1  => CRASH (poll fallback UNREACHED)
B connect->ContentionExh  : RAISED TxnContentionExhaustedError  drain.calls=1  => CRASH (poll UNREACHED)
C control connect-ok/dead : returned entries=1 total=1  drain.calls=2  => RECOVERED via poll
```
Leg C proves the probe's drain seam genuinely surfaces poll traffic, so A/B are a real crash,
not a dead probe.

**Why this matters / realistic trigger.** It violates the build's own stated invariant
(builder §6.2 / design §A.6): *"the poll fallback carries the load ALONE … a dead LIVE never
blocks the authoritative re-drain."* A failed connect is the deadest LIVE and it DOES block
the re-drain. Trigger set: concurrent first-connects exhausting bootstrap contention (the
repo's measured 6.2%–34.4% first-connect loss at 16-way → leg B), or any transient refusal of
the fresh per-await socket while the ledger's drain connection is healthy (→ leg A). Builder
§6.2 over-claims here: it says fallback happens on *"any SDK-await-boundary failure at
establish/consume"* — but the CONNECT boundary is neither, and is unguarded.

**Blast radius (fair scoping — why the operator *may* downgrade).** NOT permanent data loss:
the traffic stays in the inbox for the next `drain`/`await`, and snapshot-first already returns
any traffic pending AT ENTRY before connect is reached. It is a **graceful-degradation failure**:
in the window {no pending traffic at entry} × {connect fails}, the `await` call errors instead
of poll-surfacing arriving traffic or returning honest-empty.

**Minimal fix (mirrors `CommandSubscriber.run`; I do NOT apply it):** guard connect+establish so
an `_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION` at connect leaves `connection=None` and the loop
polls with no LIVE; add a contract pin driving `await` with a RAISING connect (the test's
`_connect_factory` already RAISES a `BaseException` entry) asserting poll-recovery + no crash.

**The instrument (verbatim, brief-base §1(b) — establishes the blocker):**
```python
# scratch_coldaudit_probe_connect.py — run: uv run python scratch_coldaudit_probe_connect.py
import asyncio
import loremaster
from loremaster.inbox_awaiter import InboxAwaiter
from loremaster.messages import InboxEntry, MessageDrainResult
from loremaster.store._txn import _CONNECTION_ERRORS, TxnContentionExhaustedError
print("loremaster.__file__ =", loremaster.__file__)

def _entry(seq):
    from datetime import UTC, datetime
    return InboxEntry(seq=seq, message_id=f"{seq:026x}", grade="signal", sender_name="lead",
        thread="wave7", task_id=None, body="pending body", refs=[],
        created_at=datetime.now(UTC), acked_at=None, ack_note=None, question=False)
def _empty():   return MessageDrainResult(entries=[], total_pending=0, directive_pending=0, stamped_seqs=[], peeked=True)
def _traffic(): return MessageDrainResult(entries=[_entry(1)], total_pending=1, directive_pending=0, stamped_seqs=[], peeked=True)

class _ScriptedDrain:  # empty on the snapshot, PENDING on every later poll
    def __init__(self): self.calls = 0
    async def __call__(self, *, agent_id, limit, peek=False, since=None):
        self.calls += 1
        return _empty() if self.calls == 1 else _traffic()

class _DeadLiveConnection:  # connect ok; LIVE establish raises the probed KeyError
    async def query(self, s, params=None): raise KeyError("probe-inflight-drop")
    async def subscribe_live(self, q):     raise KeyError("probe-live-drop")
    async def kill(self, q): ...
    async def close(self): ...

class _FastClock:
    def __init__(self): self.t = 0.0
    def now(self): return self.t
    async def sleep(self, s): self.t += s

async def _run_leg(name, connect):
    clock, drain = _FastClock(), _ScriptedDrain()
    a = InboxAwaiter(connect=connect, drain=drain, sleep=clock.sleep, now=clock.now, budget_s=6.0, poll_interval_s=2.0)
    try:
        r = await a.await_inbox(agent_id="probe-agent", limit=20)
    except BaseException as exc:
        print(f"{name}: RAISED {type(exc).__name__}  drain.calls={drain.calls}  => CRASH (poll UNREACHED)"); return
    print(f"{name}: entries={len(r.entries)} drain.calls={drain.calls}  => {'RECOVERED via poll' if r.entries else 'FALSE-EMPTY'}")

async def _raise(exc):
    async def _c(): raise exc
    return _c
async def main():
    assert OSError in _CONNECTION_ERRORS
    await _run_leg("A connect->OSError       ", await _raise(OSError("connection refused")))
    await _run_leg("B connect->ContentionExh ", await _raise(TxnContentionExhaustedError("exhausted", attempts=8, elapsed_seconds=1.0)))
    async def _c_ok(): return _DeadLiveConnection()
    await _run_leg("C control connect-ok/dead", _c_ok)
asyncio.run(main())
```

## 3. R-2 ONE-IMPLEMENTATION — sharing PROVEN by mutation (task 3)

`InboxAwaiter` and `scout` both `from loremaster.store._txn import _SDK_AWAIT_BOUNDARY_ERRORS[
_WITH_CONTENTION]` (IMPORTED, never re-defined — the adversary §R3.3 rec-1 tightening is
honoured). Proven three ways (probe `scratch_coldaudit_probe_r2.py`, in-tree):

```
CHECK 1 IDENTITY:  inbox_awaiter IS _txn : True   scout IS _txn : True   (both constants)
CHECK 2 MUTATION (consumer global): control -> recovered ;
        MUTATED awaiter global (drop KeyError) -> RAISED KeyError (recovery BROKE) ; restored -> recovered
CHECK 3 (brief's literal "patch _txn"): patched _txn only -> consumer UNAFFECTED
```
- **CHECK 1 (identity) is the strongest anti-clone proof:** each consumer's constant IS the same
  tuple OBJECT as `_txn`'s — there is no private same-value clone. The §R3.3 residual (a
  same-named LOCAL re-definition that escapes both the AST belt and the mutation pin) is
  **absent in this build**; it remains only as the adversary's re-open trigger for a future
  consumer.
- **CHECK 2** confirms the catch sites resolve the name at runtime (not an inline tuple):
  dropping `KeyError` from the awaiter's own module attr breaks `KeyError` recovery.
- **CHECK 3 is a NUANCE, not a defect.** The brief's literal instruction ("patch
  `store._txn._SDK_AWAIT_BOUNDARY_ERRORS`") does NOT reach the consumers, because `from X import Y`
  snapshots the value at import — a later rebind of `_txn.Y` doesn't propagate. This is Python
  import semantics; CHECK 1 already proves same-source, so it is not a clone. I flag it so a
  future auditor running the brief's literal step doesn't misread "patching `_txn` did nothing"
  as a private clone. The load-bearing mutation vector is the consumer module global (CHECK 2),
  which is exactly what the contract's R-2a/R-2b pins patch.

## 4. Scout 8-site consolidation — removed-behavior adjudication (task 4)

Every one of the 8 replaced catch sites maps to the constant whose expansion is **byte-equivalent**
to the prior inline tuple (`_SDK_AWAIT_BOUNDARY_ERRORS = (*_CONNECTION_ERRORS, KeyError)`;
`_WITH_CONTENTION = (*_CONNECTION_ERRORS, KeyError, TxnContentionExhaustedError)`). **No mismap.**

| # | site (symbol) | before | after | verdict |
|---|---|---|---|---|
| 1 | `_scout_query_once` | `(*_CE, KeyError)` | `_SDK_AWAIT_BOUNDARY_ERRORS` | preserved-EXACT |
| 2 | `CommandSubscriber._safe_close` | `(*_CE, KeyError)` | `_SDK_AWAIT_BOUNDARY_ERRORS` | preserved-EXACT |
| 3 | `run` connect-fail | `(*_CE, KeyError, TxnCE)` | `_WITH_CONTENTION` | preserved-EXACT |
| 4 | `run` serve-drop | `(*_CE, KeyError, TxnCE)` | `_WITH_CONTENTION` | preserved-EXACT |
| 5 | `_consume_live` subscribe attempt | `(*_CE, KeyError)` | `_SDK_AWAIT_BOUNDARY_ERRORS` | preserved-EXACT |
| 6 | `_consume_live` outer | `(*_CE, KeyError, TxnCE)` | `_WITH_CONTENTION` | preserved-EXACT |
| 7 | `_safe_kill` inner attempt | `(*_CE, KeyError)` | `_SDK_AWAIT_BOUNDARY_ERRORS` | preserved-EXACT |
| 8 | `_safe_kill` outer | `(*_CE, KeyError, TxnCE)` | `_WITH_CONTENTION` | preserved-EXACT |

The 9th boundary-ish site, `_open_command_connection`'s close-after-failed-bootstrap
(`except _CONNECTION_ERRORS:`, scout:240), correctly stays `_CONNECTION_ERRORS` (NO `KeyError`):
it is a best-effort close of a socket whose signin/bootstrap already failed — not an in-flight
SDK-await boundary, so the `KeyError` in-flight shape cannot arise. Deliberate distinction, not a
miss. `TxnContentionExhaustedError` was cleanly dropped from scout's imports (only 2 docstring
mentions remain — grep-confirmed, no live ref). `test_scout.py` + `test_retry_seam.py` GREEN in
the 8-suite run.

## 5. Injection + render + live probe (task 5)

- **Emitted LIVE statement:** `inbox_awaiter.live_select_statement` returns
  `f"LIVE SELECT * FROM {TO_RELATION} WHERE out = agent:`{agent_id}`"`. `TO_RELATION = "to"` is a
  module constant; **only `agent_id` is inlined** (backtick-quoted), never `thread`, never a
  `$param`. `agent_id` is a `uuid5` of charset-ASSERTed name/session → zero caller free text →
  injection-safe by construction (§A.5). CLEAN.
- **R-3 non-empty render** (`_render_comms_await`) teaches the REAL consume path: *"consume these
  via lore_comms action=drain — await surfaced them without stamping"* (server:7651); it does NOT
  carry drain's *"re-run without peek=true"* footer (those strings at 7460/7536/7564 are drain's
  own peeked renders). Bodies route through the shared `_render_comms_drain_row` + `render_fenced`
  (hostile-fixture-pinned). Honest-empty render names the bound as a FACT (*"as of my final
  snapshot — waited up to 55s"*), not a disclaimer.
- **Live build-probe re-run by me** on spike-surreal `:18000` (NEVER `:18500`), store
  `surrealdb-3.2.4+20260803.93ab219`: **PASS** — `parse_hex=True, parse_hyph=True, fires=True,
  discriminates=True`. Independently corroborates builder §4.

## 6. DRY reuse + Finding #353 (task 6)

The builder's §1 reuse-audit table is ACCURATE — `InboxAwaiter` CALLS shared seams and hand-rolls
no copy #2: connect via `_open_command_connection`; error classification via the imported
`_SDK_AWAIT_BOUNDARY_ERRORS[_WITH_CONTENTION]` (§3); retry via `retry_on_conflict` (lines 207/250/292);
classify-and-signal via `is_retryable_conflict_error`+`RetryableConflictSignal`; reads via
`message_ledger.drain(peek=True)`; waiting line via `_comms_waiting_lines`→`awaiting_answer`+
`_render_comms_waiting_line`; render via `_render_comms_drain_row`+`render_fenced`. All 3 new SDK
call sites route through `retry_on_conflict` (Finding #353's fix); `test_retry_seam.py` GREEN.
Finding **#353** (open, by builder-05aii-1) correctly documents the retry-seam blast-radius
process gap. ⚠ **Note the DRY story intersects the BLOCKER:** the awaiter reused the shared
opener but NOT the opener's documented caller-catch contract — that omission IS finding #354.

## 7. RESIDUALS (read the residual table, not just the verdict)

- **R1 — the snapshot-first drain (line 139) is also unguarded**, and it is OUTSIDE the try
  (lines 139–142 precede the `try` at 151). A transient failure of the ledger's own drain at the
  snapshot would also propagate. Lower severity than #354 (drain IS the source of truth — there is
  no fallback to degrade to), but noted: it shares the "no graceful degradation on a transient
  store fault" shape. If `message_ledger.drain` has its own internal retry this is moot; I did not
  chase that path.
- **R2 — test-hygiene warning, not a defect:** `test_retry_seam.py:3216` emits
  `RuntimeWarning: coroutine '_empty_subscription' was never awaited`. The test PASSES; it is a
  fixture-await hygiene nit in the suite, not in the build.
- **R3 — naming:** per the brief I wrote the canonical report as `REPORT-coldaudit-05a-ii.md`
  and a pointer `REPORT-coldaudit-05aii-1.md` (agent-name-keyed idle-gate), matching the sibling
  convention (`REPORT-{builder,adversary,contract}-05aii-1.md` are pointers to the `-05a-ii`
  canonicals).
- **R4 — scratch instruments** at repo root (`scratch_coldaudit_probe_connect.py`,
  `scratch_coldaudit_probe_r2.py`, `scratch_coldaudit_liveprobe.py`): the two load-bearing ones
  are pasted verbatim (§2) or fully reproduced-in-effect (§3/§5). Lead: promote the live probe to
  `scripts/` as the await deploy-smoke if desired, else delete at close-out. They are untracked;
  I did not commit (the lead commits).

---

## 8. DELTA RE-AUDIT — #354 CLOSED (2026-08-10, HEAD `c1e1b31`)

The builder applied the connect-guard at `7bc68f9`. I verified the fix (I did NOT re-audit the
whole build; §§1–7 stand, and scout/server/`_txn` are byte-identical to `f5aec32` — confirmed by
`git diff --quiet`). Fix flow was proper: contract-first (`2e40b03`/`b18ed31`) → adversary
SUFFICIENT (`f71760f`) → build (`7bc68f9`).

**The fix (19-line diff, `inbox_awaiter.py::await_inbox` ONLY):** `connect()` + `_establish_live()`
are now wrapped `try: … except _SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION: connection = live_uuid =
consume_task = None` → the poll loop carries with no LIVE. Mirrors `CommandSubscriber.run`'s connect
guard; the catch NAMES the shared `_WITH_CONTENTION` global (R-2 mutation-pin-safe). The 3 `self._drain`
reads (snapshot/poll/final) are deliberately LEFT OUTSIDE the guard.

**1 — #354 CLOSED (empirical, positive-controlled; `loremaster.__file__` in-tree).** Re-ran the §2
repro against the guarded build, expanded to {OSError, TxnContentionExhausted} × {arrives-via-poll,
stays-empty, pending-at-entry}:
```
OSError / arrives-via-poll        connect.calls=1 drain.calls= 2 -> poll-recovered   OK
OSError / stays-empty             connect.calls=1 drain.calls= 5 -> honest-empty     OK
OSError / pending-at-entry        connect.calls=0 drain.calls= 1 -> poll-recovered   OK
TxnContentionExh / arrives-poll   connect.calls=1 drain.calls= 2 -> poll-recovered   OK
TxnContentionExh / stays-empty    connect.calls=1 drain.calls= 5 -> honest-empty     OK
TxnContentionExh / pending-entry  connect.calls=0 drain.calls= 1 -> poll-recovered   OK
control connect-ok/dead / poll    connect.calls=1 drain.calls= 2 -> poll-recovered   OK
```
The pre-fix crash (`drain.calls=1`, RAISED) is GONE: every connect-failure now shows `connect.calls=1`
(attempted → caught) then the poll loop carries. NO crash, NO false-empty. Positive control still
recovers. Matches the new pin `TestConnectFailureDegradesToPoll` ({oserror,contention}×{pending,empty}).

**2 — scope + no regression (my §7 R1 now LOCKED).** Production diff `f5aec32..c1e1b31` = ONLY
`inbox_awaiter.py` (19 lines). The 3 drain reads are STILL unguarded — a separate probe raising OSError
at each authoritative read propagated every time (`snapshot/poll/final → RAISED, not swallowed`),
so a drain fault never becomes a false-empty. Matches the new pin `TestADrainFaultRaisesNeverFalseEmpties`
({snapshot,poll,final}). No new swallow anywhere; the only new `except` is the connect-guard.

**3 — gates re-run independently at HEAD `c1e1b31`:** pytest 7-suite (the brief's set) **1838 passed /
17 skipped, exit 0** · typecheck **191 residual, ZERO in touched files** (= #333 baseline,
RED_ADJUDICATED→pkt39) · ruff **clean** (repo root cleared of my disposable scratch — the prior
RED_ORPHANED source) · currency **PASS, 0 RED_ORPHANED**.

**Residual R2 (test-hygiene warning) and R3 (naming) from §7 are unchanged and non-blocking.** The
delta probe was disposable and is not committed; its logic is reproduced verbatim above and in §2.

**DELTA VERDICT: GO.** #354 closed, scope contained, all gates green.

---

_Order: contract → adversary → build → **cold audit** → fix (contract→adversary→build) → **delta
re-audit**. The original build passed every gate and still shipped one defect the contract could not
see (its non-loss pin used an establish-drop, not a connect-failure) — the cold audit's whole reason
to exist. The fix closed it under the same discipline. VERDICT: **GO**._
