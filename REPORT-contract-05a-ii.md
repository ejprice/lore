# REPORT-contract-05a-ii — the `await` verb RED contract (TESTS ONLY)

brief-base v11 read
brief project v7 read

> **REVISION 4 (2026-08-10)** — addresses the cold-audit NO-GO on BLOCKER #354
> (`REPORT-coldaudit-05a-ii.md` §2). The feature is now BUILT (HEAD `c111400`), so the contract
> runs against the REAL artifact: 29 pins VALIDATE it, and the 4 new **PIN 1** legs correctly
> redden on the unguarded LIVE-connect crash. Added PIN 1 (connect-failure → degrade-to-poll) +
> PIN 2 (drain-fault → raise-not-false-empty); PIN 3 skipped (§7). See §7. Rev-1/2/3 below.
>
> **REVISION 3 (2026-08-10)** — addressed the `contract-adversary` INSUFFICIENT verdict §4: the
> R-2 sharing pin was a BEHAVIOR pin; `TestThreadNarrowsClientSide` was value-monoculture. Both
> fixed. Rev-2 addressed the ratified R-1/R-2/R-3; rev-1 the original three forks.

## SUMMARY BLOCK
- **State:** done — cold-audit BLOCKER #354 pinned. **The feature is BUILT (HEAD `c111400`); the
  contract runs against the real artifact — 29 pins VALIDATE it, the 4 PIN-1 legs redden on the
  #354 crash.** 38 pins/legs across 3 files. Satisfiability 47/47 on the fixed (guarded) build;
  16 mutation proofs.
- **Deviations:** (1) receipts earned by applying the ~3-line #354 guard fix in a DISPOSABLE
  scratch — real production UNTOUCHED (`git status`: only my test files + reports modified; the
  built feature was committed by the builder at `f5aec32`/`c111400`, not by me). (2) scratch `rm`
  is sandbox-blocked; `/tmp/await-ref{,2,3,4}-05aii` + `/tmp/r*` remain — disposable, operator may
  delete. (3) 3 `scratch_coldaudit_*.py` at repo root are the cold auditor's leftovers, not mine.
- **Capability check:** all tools present; only spike-surreal `:18000` reasoned about (no store
  connected — the injected seams open no socket). No production code touched by me.
- **Packages considered:** none — no mechanism specified (a test contract). await REUSES shipped
  seams (`drain`, `awaiting_answer`, the `_render_comms_drain` fence/row, the `CommandSubscriber`
  connect-injection idiom, the shared `_CONNECTION_ERRORS`); hand-rolls nothing.
- **Graded:** contract authorship — the contract now grades the BUILT feature at HEAD `c111400`
  (29 pins GREEN validate it; 4 PIN-1 legs RED = #354). `git rev-parse HEAD` = `c111400`.
- **Decisions-needed:** none — #354 pinned; the builder writes the ~3-line connect guard (§7). PIN
  3 (early-wake reconnect bound) skipped deliberately (§7). Ready for the `contract-adversary` re-run.
- **Receipt pointers:** RED counts §1 · per-pin discriminators + mutation receipts §2 ·
  satisfiability §3 · builder requirements §4 · adversary-gaps-closed §5 · unrelated mypy debt §6 ·
  the #354 pins + fix + mutation receipts §7.

---

## 1. What was written, and the RED receipts (real tree, HEAD `c111400`, feature BUILT)

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

## 7. The #354 cold-audit BLOCKER — two OPPOSITE fates pinned (rev-4)

The audit (`REPORT-coldaudit-05a-ii.md` §2) found the socket-DROP path holds (`TestSocketDropNonLoss`
passes on the built code) but the LIVE-**connect** failure was UNPINNED and the built awaiter
crashes on it: `inbox_awaiter.py::await_inbox` wraps `connection = await self._connect()` in a
`try/…/finally` with **no `except`** (real code, lines 151–167). The shared opener re-raises raw SDK
types by contract (a `_CONNECTION_ERRORS` member) AND `TxnContentionExhaustedError` (#102
concurrent-first-connect) — the caller MUST catch, as `CommandSubscriber.run` does. Design §A.1 step 2
says establish is best-effort → poll-only. Two fates, opposite, now pinned:

- **PIN 1 — `TestConnectFailureDegradesToPoll` (4 legs, RED on the built code = the blocker).** A
  raising `connect` factory — parametrised `OSError` AND `TxnContentionExhaustedError` — must DEGRADE
  TO POLL: returns pending traffic (`drain.calls≥2`, poll reached) or an honest-empty, never a crash
  or false-empty. Against HEAD `c111400` all 4 legs RED (the connect error propagates out of
  `await_inbox`). **Mutation-proven:** on the fixed build (the ~3-line guard below) all 4 go GREEN
  (satisfiability 47/47); reverting the guard (the current unguarded build) → **RED**.
- **PIN 2 — `TestADrainFaultRaisesNeverFalseEmpties` (GREEN on the built code — a regression lock).**
  The DRAIN read (the authoritative snapshot/poll/final read) is NOT best-effort: a fault must RAISE
  (F1=peek makes it loss-free), never a false-empty. The built code already raises (drain unguarded),
  so this LOCKS that. **Mutation-proven:** a build that catches the drain fault and RETURNS empty →
  **RED**; the connect guard (PIN 1's fix) stays GREEN — the two pins fence the guard to the connect
  path ONLY (a builder over-guarding the drain while fixing PIN 1 is caught).
- **PIN 3 — SKIPPED (deliberately).** The early-wake LIVE-reconnect known bound (§R-4). A clean
  in-process pin (`connect.calls==1`) would CONFLICT with PIN 1's latitude (a degradation that
  retries the connect within budget is legal). The bound + re-open trigger are already recorded in
  `05-comms-await-story.md` §R-4, so per the lead's "skip if awkward" this is left there.

**Named builder fix (~3 lines):** wrap the connect+establish in the shared boundary catch —
`try: connection = await self._connect(); live_uuid, consume_task = await self._establish_live(…)
except _SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION: connection = None` — so a connect/establish fault
degrades to poll-only (teardown already tolerates `connection=None`). The drain reads stay UNGUARDED
(PIN 2). Proven satisfiable in scratch (47/47).

---

_Contract author proposes; the adversary grades the contract; the operator rules; the lead
adjudicates. Order: contract → adversary → build → cold audit. This revised contract is ready for
the `contract-adversary` re-run._
