# REPORT-contract-05a-ii — the `await` verb RED contract (TESTS ONLY)

brief-base v11 read
brief project v7 read

> **REVISION 3 (2026-08-10)** — addresses the `contract-adversary` INSUFFICIENT verdict
> (`REPORT-adversary-05a-ii.md` §4): the R-2 sharing pin was a BEHAVIOR pin (a private inline
> tuple satisfies it), and `TestThreadNarrowsClientSide` was value-monoculture. Both fixed +
> re-proven (§2, §3). Rev-2 addressed the ratified R-1/R-2/R-3; rev-1 the original three forks.

## SUMMARY BLOCK
- **State:** done — INSUFFICIENT addressed. 33 pins across 3 files (all RED/anchor for the right
  reason), satisfiability 42/42, 14 mutation proofs (incl. the two routing-≠-sharing builds 7a/7b).
- **Deviations:** (1) a KNOWN-CORRECT reference of R-1/R-2/R-3 was built in DISPOSABLE scratch
  copies to earn the receipts — real production UNTOUCHED (`git status`: only test files + reports).
  (2) scratch `rm` is sandbox-blocked; `/tmp/await-ref{,2,3}-05aii` + `/tmp/r*` remain — disposable,
  operator may delete.
- **Capability check:** all tools present; only spike-surreal `:18000` reasoned about (no store
  connected). No production code touched in the real tree.
- **Packages considered:** none — no mechanism specified (a test contract). await REUSES shipped
  seams (`drain`, `awaiting_answer`, the `_render_comms_drain` fence/row, the `CommandSubscriber`
  connect-injection idiom, the shared `_CONNECTION_ERRORS`); hand-rolls nothing.
- **Graded:** contract authorship — no builder artifact graded. `git rev-parse HEAD` = `d64cd23`.
- **Decisions-needed:** none — R-1/R-2/R-3 ruled; the two adversary gaps fixed. Ready for the
  `contract-adversary` re-run (no revision skips it).
- **Receipt pointers:** RED counts §1 · per-pin discriminators + mutation receipts §2 ·
  satisfiability §3 · builder requirements §4 · adversary-gaps-closed §5 · unrelated mypy debt §6.

---

## 1. What was written, and the RED receipts (real tree, HEAD `d64cd23`, await UNBUILT)

**Writable set (R-2 SCOPE ADD: `test_scout.py`, lead-granted).** `test_comms_await.py` (28 pins,
new), `test_comms_tool.py` (exact-set + `test_await_params`), `test_scout.py` (the R-2 scout leg —
positive control + runtime mutation — + `_FakeCommandConnection.drop_error`), `_message_fakes.py`
(the earlier `await_inbox` oracle reverted — R-1 hosts the wait-machine in `InboxAwaiter`). No
production code touched.

**RED counts:**
- `test_comms_await.py` — **28 failed** (all RED, no green-at-write). Causes: **AttributeError**
  (the pending `InboxAwaiter` / `_SDK_AWAIT_BOUNDARY_ERRORS`, reached through an `Any` handle so
  mypy-clean while unbuilt), **`ValueError: unknown comms action 'await'`** (dispatch/render pins),
  **AssertionError** (foreign-param, + the thread parametrise legs).
- `test_comms_tool.py::TestCommsActionsTable` — **3 failed** (exact-set + two `KeyError: 'await'`).
- `test_scout.py::TestCommandSubscriberSharesTheSdkAwaitBoundary` — the POSITIVE CONTROL
  (`test_reconnect_recovers_from_a_keyerror_inflight_drop`) is **GREEN on HEAD**; the RUNTIME
  MUTATION (`test_dropping_keyerror_from_the_shared_constant_breaks_recovery`) is **RED on HEAD**
  (scout is still inline — it goes green only when scout NAMES the shared constant). No collateral.

Collection clean (no uncollectable — every unbuilt symbol reached at CALL time). **Gates:** `ruff`
clean; `mypy loremaster` **0 errors in my four files** (102 pre-existing elsewhere — §6).

## 2. The pins, their discriminators, and the mutation-proof receipts

All load-bearing pins mutation-proven against the reference (build wrong → watch RED → restore);
the reference stays **42/42 GREEN** restored (§3).

| # | Pin (property) | Wrong build it STOPS | Mutation receipt |
|---|---|---|---|
| 1 | **Snapshot-first short-circuit** (InboxAwaiter) | "only-new / always-waits" | removed the short-circuit → `TestSnapshotFirstShortCircuit` **RED** |
| 2 | **Final-snapshot-at-timeout (LOAD-BEARING)** | "renders empty off the stale last-wake read" | `return <empty>` instead of a final `_snapshot()` → **RED** |
| 3 | **Poll-only completeness** | "LIVE-dependent" | removed the in-loop re-drain → **RED** (rev-1) |
| 4 | **Socket-drop non-loss (forgery)** + positive control | "false-empty / crash on the KeyError boundary" | `except→return <empty>` → **RED**, control **PASS** |
| **R-2a** | **SHARING by RUNTIME MUTATION — await leg**: patch the awaiter module's `_SDK_AWAIT_BOUNDARY_ERRORS` ⇒ recovery BREAKS (await_inbox RAISES) | **7b** — await hand-rolls a private inline tuple | build **7b** (await inline) → the await-leg pin **RED** (patch no-op, still recovers, `pytest.raises` fails) |
| **R-2b** | **SHARING by RUNTIME MUTATION — scout leg** (in `test_scout.py`): patch scout's module global ⇒ the subscriber NO LONGER recovers | **7a** — scout keeps private inline clones | build **7a** (scout inline) → the scout-leg pin **RED** (still recovers); positive control still recovers **PASS** |
| **R-2c** | **AST REACH-CHECK belt**: DERIVED scan (never a hand-list) — NO `except`-tuple with `*_CONNECTION_ERRORS`+`KeyError` survives in scout OR the awaiter | either private clone | **BOTH 7a AND 7b** → the belt **RED** (offenders found); on the wired reference it finds none |
| 5 | **Injection — emitted LIVE statement** (InboxAwaiter): agent-id literal only, no `thread`/param | inlines `thread` / binds a param | appended `AND thread='q'` → **RED** (rev-1) |
| 6 | **Honest-empty-as-fact** | bare disclaimer / drain empty render | empty render → `render_line("no unread messages")` → both pins **RED** |
| 7 | **Waiting-line via ONE shared helper** | a private clone | sentinel-patched `_render_comms_waiting_line` (rev-1) |
| 8 | **Fenced bodies + hostile (SHARED fence)** | a hand-rolled fence-less render | GREEN under the R-3 footer swap (fence survives) |
| R-3 | **Non-empty teaches `action=drain`, not the peek re-run** | verbatim `_render_comms_drain(peeked=True)` footer | await render → `_render_comms_drain(peeked=True)` → **RED**, fence pin **PASS** |
| F1 | **await PEEKS, never stamps + idempotent** | a stamping (`peek=False`) build | `peek=True→peek=False` → `…peek_true` **RED** AND (now) `test_two_awaits…` **RED** via the shared `_StampingDrain` (§7 fix: the idempotency pin now discriminates, no longer vacuous) |
| F2 | **budget a fixed constant < ~60s** (InboxAwaiter `budget_s` default) | a `timeout=` param / value ≥ ceiling | RED via `InboxAwaiter` unbuilt; reference default `55.0` satisfies `0<x<60` |
| F3 | **thread narrows CLIENT-SIDE** (parametrised over TWO values) + **never in the LIVE WHERE** | a hardcoded single-thread comparand | awaiter filters `entry.thread=='q:gate'` → the `q:other` parametrise leg **RED** (§4.2 fix), `q:gate` leg PASS |
| 9 | **Exact-set + param honesty** | a drifted/foreign param surface | RED: set-mismatch + `KeyError` until registered |

**The R-2 sharing invariant is now R-2a/R-2b/R-2c (runtime-mutation + AST belt) — NOT the behavior
pin.** The behavior pin (does the subscriber recover a KeyError drop?) is retained ONLY as the
positive control that proves the runtime mutation is load-bearing; a private inline tuple recovers
just as well, so it never was the invariant (adversary §4.1, corrected here).

## 3. Satisfiability receipt (the C-DEF gate)

Reference (in provenance-verified scratch): standalone `loremaster/inbox_awaiter.py::InboxAwaiter`
(+ `AWAIT_BUDGET_S`); `store._txn._SDK_AWAIT_BOUNDARY_ERRORS = (*_CONNECTION_ERRORS, KeyError)` +
`_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION = (*…, TxnContentionExhaustedError)`, referenced as
PATCHABLE module attrs at the awaiter's catch AND **all 8 previously-inline scout sites** (4 base +
4 with-contention, DRY'd — the AST belt confirms zero inline clones remain); `AppContext._comms_await`
+ the `_COMMS_ACTIONS["await"]` registration + the honest-empty render + the R-3
`_render_comms_await_nonempty`. Against it the whole contract goes **42 passed / 0 failed**
(`test_comms_await` 28 + `TestCommsActionsTable` 12 + the scout control+mutation 2). SATISFIABLE —
not a C-DEF trap; the R-1/R-2/R-3 seam shapes are buildable as specified.

**The two routing-≠-sharing builds the adversary found both REDDEN now** (each proven in scratch):
**7a** (await wired, scout inline) → scout-leg mutation **RED** + AST belt **RED**; **7b** (scout
wired, await inline) → await-leg mutation **RED** + AST belt **RED**. Neither passes the contract.

## 4. NAMED builder requirements

1. **Registration** — `_COMMS_ACTION_AWAIT` + `_COMMS_ACTIONS["await"] = CommsActionSpec(
   AppContext._comms_await, params=frozenset({"thread"}), required=frozenset())` + a `C1_RENDER_CASES`
   render case in `test_render_seam_pins` (OUT of my writable set — named).
2. **Wait machine (R-1)** — a STANDALONE `InboxAwaiter` (its module is the builder's call; the
   reference used `loremaster/inbox_awaiter.py`), imported into `loremaster.server`'s namespace by
   the handler. `InboxAwaiter(*, connect, drain, sleep=asyncio.sleep, now=time.monotonic,
   budget_s=AWAIT_BUDGET_S, poll_interval_s=…)`; `async def await_inbox(*, agent_id, limit,
   thread=None) -> MessageDrainResult` (snapshot-first `drain(peek=True)` → LIVE-primary via `connect`
   + poll-fallback within `budget_s` via `now` → final snapshot; PEEK shape);
   `live_select_statement(agent_id) -> str`. `AWAIT_BUDGET_S` ≤55s (the `budget_s` default).
3. **Handler (R-1)** — `AppContext._comms_await`: CONSTRUCTS `InboxAwaiter` from the store LIVE-connect
   + `self.message_ledger.drain`, CALLS it, owns the RENDER (NON-empty → R-3 drain-teach render;
   EMPTY → honest-empty + SHARED `_comms_waiting_lines`). References `InboxAwaiter` as the `server`
   module global (monkeypatchable — the testability seam the render pins ride).
4. **Shared error classification (R-2)** — `store._txn._SDK_AWAIT_BOUNDARY_ERRORS =
   (*_CONNECTION_ERRORS, KeyError)` AND `_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION = (*…,
   TxnContentionExhaustedError)`, referenced **as PATCHABLE module attributes** (never an inline
   spread that the AST belt would flag, and never a pre-imported alias the runtime patch can't reach)
   at the awaiter's catch AND **ALL** scout SDK-await-boundary catch sites (the reference DRY'd all
   8). The runtime-mutation pins + the AST belt are the invariant — a private clone reddens.
5. **R-3 typed applicability (#104)** — the non-empty render's consume-instruction is a typed input
   (`action=drain` for await), NOT a `peeked: bool` hardcoding drain's wording; REUSE the fence + row.
6. **The LIVE-wake + socket-drop against a REAL socket** = the DEPLOY-gated build probe / smoke
   (design §C, §A.6 Leg A/B) — the in-process pins prove the STATE MACHINE.

## 5. Adversary gaps closed

- **§4.1 BLOCKER (R-2 sharing was a behavior pin)** → the sharing invariant is now the
  RUNTIME-MUTATION pin, BOTH legs (await in `test_comms_await`, scout in `test_scout`), plus the AST
  reach-check belt (coverage a CHECKED, DERIVED variable — scans the pattern, no hand-list). Proven:
  builds **7a** and **7b** each redden. The behavior pin is retracted as the invariant (kept as the
  positive control). §2/§4 corrected accordingly.
- **§4.2 SECONDARY (thread value-monoculture)** → `TestThreadNarrowsClientSide` is parametrised over
  `{q:gate, q:other}`; a hardcoded-`q:gate` build reddens the `q:other` leg (proven in scratch).
- **§7 (F1 idempotency vacuous)** → the idempotency pin now rides a shared `_StampingDrain` that
  MODELS a stamping drain, so a `peek=False` build reddens the second-await assertion (proven). The
  `…peek_true` pin remains the primary no-stamp discriminator; idempotency proves the consequence.

## 6. Unrelated pre-existing mypy debt (flagged, not buried)

`uv run mypy loremaster` reports **102 errors** on this branch (`feat/surreal-unification`), ALL in a
pre-existing AUTH-test cluster — **zero in my four files**. Out of my scope; surfaced per "flag
unrelated failures, don't bury them". The operator decides.

---

_Contract author proposes; the adversary grades the contract; the operator rules; the lead
adjudicates. Order: contract → adversary → build → cold audit. This revised contract is ready for
the `contract-adversary` re-run._
