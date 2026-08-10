# REPORT-contract-05a-ii — the `await` verb RED contract (TESTS ONLY)

brief-base v11 read
brief project v7 read

> **REVISION 2 (2026-08-10)** — revised to the lead-ratified seam rulings R-1/R-2/R-3
> (`docs/plans/v2/05-comms-await-story.md` §"Seam rulings"; `REPORT-fable-design-05a-ii.md`
> §"Follow-up rulings 05a-ii"). The three forks §5 first raised are now RESOLVED (see §5).
> Satisfiability + mutation receipts re-earned against the revised reference.

## SUMMARY BLOCK
- **State:** done — RED contract revised to R-1/R-2/R-3 (29 pins across 3 files, all RED/anchor
  for the right reason), fake capability reworked, satisfiability + 10 mutation proofs re-run.
- **Deviations:** (1) a KNOWN-CORRECT reference of the R-1/R-2/R-3 seams was built in a DISPOSABLE
  scratch copy (`/tmp/await-ref2-05aii`, provenance-verified) to earn the receipts — real
  production UNTOUCHED (`git status`: only test files + reports changed). (2) scratch `rm` is
  sandbox-blocked; `/tmp/await-ref{,2}-05aii` + `/tmp/ref*` remain — disposable, operator may delete.
- **Capability check:** all tools present; only spike-surreal `:18000` reasoned about (no store
  connected — the reference awaiter never opens a socket). No production code touched in the real tree.
- **Packages considered:** none — no mechanism specified (a test contract). await REUSES shipped
  seams (`drain`, `awaiting_answer`, the `_render_comms_drain` fence/row, the `CommandSubscriber`
  connect-injection idiom, the shared `_CONNECTION_ERRORS`); hand-rolls nothing.
- **Graded:** contract authorship — no builder artifact graded. `git rev-parse HEAD` = `d64cd23`.
- **Decisions-needed:** none — R-1/R-2/R-3 are ruled; §5 marks them RESOLVED. Ready for the
  `contract-adversary` pass.
- **Receipt pointers:** RED counts §1 · per-pin discriminators + mutation receipts §2 ·
  satisfiability §3 · builder requirements §4 · rulings-resolved §5 · unrelated mypy debt §6.

---

## 1. What was written, and the RED receipts (real tree, HEAD `d64cd23`, await UNBUILT)

**Writable set (R-2 SCOPE ADD: `test_scout.py`, lead-granted).** New:
`loremaster/tests/test_comms_await.py` (25 pins). Extended: `test_comms_tool.py` (exact-set +
`test_await_params`), `test_scout.py` (the R-2 cross-suite scout leg + `_FakeCommandConnection`
`drop_error` param), `_message_fakes.py` (REVERTED my earlier `await_inbox` oracle — R-1 hosts the
wait-machine in a standalone `InboxAwaiter`, not a ledger method). No production code touched.

**RED counts:**
- `test_comms_await.py` — **25 failed** (all RED). Causes: **15 × `AttributeError`** (14 for the
  pending `InboxAwaiter`, 1 for the pending `_SDK_AWAIT_BOUNDARY_ERRORS` — both reached through an
  `Any` handle so they are mypy-clean while unbuilt), **9 × `ValueError: unknown comms action
  'await'`** (dispatch/render pins), **1 × `AssertionError`** (foreign-param: await unregistered so
  the unknown-action guard fires first; flips GREEN when await is registered AND rejects `limit`).
- `test_comms_tool.py::TestCommsActionsTable` — **3 failed** (exact-set mismatch;
  `test_every_other_action_requires_prior_registration` + `test_await_params` `KeyError: 'await'`).
  No collateral breakage.
- `test_scout.py::TestCommandSubscriberSharesTheSdkAwaitBoundary` — **GREEN on current production**
  (CommandSubscriber already recovers a KeyError drop, currently via an inline tuple). It is a
  MUTATION ANCHOR, non-vacuous (drives a real KeyError in-flight drop through the reconnect ladder),
  RED only under the shared-constant mutation (§2). `TestCommandSubscriberTransport` stays green.

Collection clean (25 collected, no uncollectable — every unbuilt symbol is reached at CALL time,
never a module-scope import). **Gates on changed files:** `ruff` clean; `mypy loremaster` reports
**0 errors in my four files** (102 pre-existing elsewhere — §6).

## 2. The pins, their discriminators, and the mutation-proof receipts

Every load-bearing pin was mutation-proven against the revised reference (build wrong → watch RED →
restore). All mutations discriminate; the reference stays **38/38 GREEN** when restored (§3).

| # | Pin (property) | Wrong build it STOPS | Mutation receipt |
|---|---|---|---|
| 1 | **Snapshot-first short-circuit** (InboxAwaiter): pending-at-entry returns immediately — no wait, no LIVE, no poll | "only-new / always-waits" | removed the awaiter short-circuit → `TestSnapshotFirstShortCircuit` **RED** |
| 2 | **Final-snapshot-at-timeout (LOAD-BEARING)**: a deadline arrival is returned (fresh final snapshot), last read at/after the deadline | "renders empty off the stale last-wake read" | awaiter `return <empty>` instead of a final `_snapshot()` → `TestFinalSnapshotAtTimeout` **RED** |
| 3 | **Poll-only completeness**: LIVE silent → poll returns BEFORE the deadline | "LIVE-dependent" | removed the in-loop re-drain → `TestPollOnlyCompleteness` **RED** (validated rev-1; unchanged property) |
| 4 | **Socket-drop non-loss (forgery)**: DEAD LIVE (`KeyError` establish) + traffic → returned, no false-empty; **positive control** genuine-empty → empty | "false-empty / crash on the KeyError boundary" | see R-2 row (the shared-constant mutation is the sharper proof) + `except→return <empty>` → **RED**, control **PASS** |
| **R-2** | **ONE-IMPLEMENTATION cross-suite (MANDATORY)**: await + CommandSubscriber ride the ONE `_SDK_AWAIT_BOUNDARY_ERRORS` | two private `(*_CONNECTION_ERRORS, KeyError)` clones (routing ≠ sharing) | **dropped `KeyError` from the ONE constant → BOTH `test_comms_await`'s #4 AND `test_scout`'s KeyError-drop pin reddened** (the scout pin errored with the escaped `KeyError('req-uuid-abc')` — the subscriber died) + the constant-shape pin **RED** |
| **R-3** | **Non-empty teaches `action=drain`, not the peek re-run** | reuse of `_render_comms_drain(peeked=True)`'s footer verbatim | await render → `_render_comms_drain(peeked=True)` → `TestTheNonEmptyAwaitTeachesDrain…` **RED** (`peek=true` present / `action=drain` absent), while the **fence pin stayed GREEN** (shared fence preserved) |
| 5 | **Injection — emitted LIVE statement** (InboxAwaiter): inlines ONLY the agent-id record literal; no `thread`, no caller substring, no bound `$param`, keyed on `out =` | inlines `thread` (DD-3.e) / binds a param | appended `AND thread='q'` → `test_…inlines_no_thread…` **RED** (validated rev-1; moved to the awaiter) |
| 6 | **Honest-empty-as-fact**: names the caller + a temporal bound, never a disclaimer/drain's bare line | bare disclaimer / drain empty render | empty render → `render_line("no unread messages")` → both `…NamesTheBoundAsAFact` pins **RED** |
| 7 | **Waiting-line via ONE shared helper** (handler): discriminating pair + PROVEN BY MUTATION | a private clone (routing ≠ sharing) | sentinel-patched `_render_comms_waiting_line` routes through await (validated rev-1) |
| 8 | **Fenced bodies + hostile** (SHARED fence): body round-trips, fence wider than its backtick run | a hand-rolled fence-less render | proven GREEN under the R-3 mutation (fence survives a footer swap) |
| F1 | **await PEEKS, never stamps** (InboxAwaiter): every read `peek=True`, shape `stamped_seqs=[]/peeked=True`, idempotent | a stamping build (DD-4.c/#214 loss) | `peek=True → peek=False` → `test_the_awaiter_reads…peek_true` **RED** |
| F2 | **budget is a fixed constant < ~60s** — the InboxAwaiter `budget_s` DEFAULT, the PROPERTY not the number | a `timeout=` param / value ≥ ceiling | RED via `InboxAwaiter` unbuilt; the reference default `55.0` satisfies `0 < x < 60` |
| F3 | **thread narrows CLIENT-SIDE** (awaiter) + **never in the LIVE WHERE** (pin #5) | thread in the LIVE / thread suppresses the inbox | awaiter narrows to the requested thread; #5 forbids thread in the statement |
| 9 | **Exact-set + param honesty** | a drifted/foreign param surface | RED: set-mismatch + `KeyError` until registered |

## 3. Satisfiability receipt (the C-DEF gate)

A KNOWN-CORRECT reference of the R-1/R-2/R-3 seams — the standalone
`loremaster/inbox_awaiter.py::InboxAwaiter` (+ `AWAIT_BUDGET_S`); `store._txn._SDK_AWAIT_BOUNDARY_ERRORS
= (*_CONNECTION_ERRORS, KeyError)` referenced by BOTH the awaiter's catch AND `scout.py`'s reconnect
ladder (4 inline clones DRY'd); `AppContext._comms_await` + the `_COMMS_ACTIONS["await"]` registration
+ the honest-empty render + the R-3 `_render_comms_await_nonempty` (SHARED fence + row, `action=drain`
teach) — was built in a provenance-verified scratch copy (`scratch_copy.sh`). Against it the whole
contract goes **38 passed / 0 failed** (`test_comms_await` 25 + `TestCommsActionsTable` 12 + the
scout cross-suite pin 1). The contract is SATISFIABLE — not a C-DEF trap — and the R-1/R-2/R-3 seam
shapes are buildable as specified. The reference is a throwaway grading instrument reproducible from
§4.

## 4. NAMED builder requirements

1. **Registration** — `_COMMS_ACTION_AWAIT = "await"` + `_COMMS_ACTIONS["await"] =
   CommsActionSpec(AppContext._comms_await, params=frozenset({"thread"}), required=frozenset())`.
   AND a render case for `await` in `test_render_seam_pins`'s `C1_RENDER_CASES` (OUT of my writable
   set — named).
2. **Wait machine (R-1)** — a STANDALONE `InboxAwaiter` (its own module is the builder's call; the
   reference used `loremaster/inbox_awaiter.py`), imported into `loremaster.server`'s namespace by
   the handler (so the tests reach it as `server.InboxAwaiter`). Constructed
   `InboxAwaiter(*, connect, drain, sleep=asyncio.sleep, now=time.monotonic, budget_s=AWAIT_BUDGET_S,
   poll_interval_s=…)`; `async def await_inbox(*, agent_id, limit, thread=None) -> MessageDrainResult`
   (snapshot-first `drain(peek=True)` → LIVE-primary via `connect` + poll-fallback within `budget_s`
   via `now` → final snapshot; PEEK shape); `live_select_statement(agent_id) -> str`. `AWAIT_BUDGET_S`
   ≤55s (the `budget_s` default; F2 pins `0 < x < 60`).
3. **Handler (R-1)** — `AppContext._comms_await(self, *, agent_row, thread=None, **_ignored) ->
   Rendered`: CONSTRUCTS `InboxAwaiter` from the store LIVE-connect + `self.message_ledger.drain`,
   CALLS it, and owns the RENDER. NON-empty → the R-3 drain-teach render (SHARED fence + row,
   `action=drain`, NO "peek=true"); EMPTY → honest-empty naming the bound as a FACT + the SHARED
   `_comms_waiting_lines`. The handler must reference `InboxAwaiter` as the `server` module global
   (so it is monkeypatchable) — the testability seam the render pins ride.
4. **Shared error classification (R-2)** — `store._txn._SDK_AWAIT_BOUNDARY_ERRORS =
   (*_CONNECTION_ERRORS, KeyError)`, referenced by the awaiter's catch AND ≥1 `CommandSubscriber`
   catch site (the reference wired the reconnect-ladder + `_safe_kill`/`_safe_close` Txn-union sites;
   the run ladder is what the scout cross-suite pin exercises). await's reconnect set MAY union
   `TxnContentionExhaustedError` (recommended); teardown set = the base constant. The cross-suite
   mutation pin is the invariant: a private clone reddens only one suite.
5. **R-3 typed applicability (#104)** — the non-empty render's consume-instruction is a typed input
   (drain-teach for await, the peek footer for drain's own peek), NOT a `peeked: bool` hardcoding
   drain's wording. REUSE the fence + row render (the injection-critical part); vary only the taught
   follow-up.
6. **The LIVE-wake + socket-drop against a REAL socket** is the DEPLOY-gated build probe / smoke
   (design §C, §A.6 Leg A/B), run on `:18000` by the Opus-4.8 live-leg builder — the in-process pins
   prove the STATE MACHINE. The probe already settled LIVE-fires + the socket-drop shape
   (`docs/plans/v2/receipts/2026-08-09-packet05ai/REPORT-probe-await-05a-1.md`).

## 5. The three forks — RESOLVED by the ratified rulings

- **§5.1 (rev-1) — the wait-machine seam shape → RESOLVED by R-1** (lead-ratified): a STANDALONE
  `InboxAwaiter` constructed with an injected `connect` factory + the ledger's `drain` seam, NOT a
  `MessageLedger.await_inbox` method; the handler CONSTRUCTS + CALLS it and owns the render. The
  contract's ~14 wait-machine pins were retargeted to construct `InboxAwaiter` directly (the
  `CommandSubscriber`/`test_scout.py` idiom); observable properties unchanged.
- **§5.2 (rev-1) — await's non-empty peek-teach → RESOLVED by R-3** (lead-ratified): the non-empty
  render teaches `action=drain`, never drain's "re-run without peek=true" footer, via typed
  applicability (#104). Added `TestTheNonEmptyAwaitTeachesDrainNotThePeekRerun` with the
  discriminating fixture (a verbatim-drain-footer build fails).
- **NEW from R-2** (lead-ratified, SCOPE ADD to `scout.py`/`test_scout.py`): await + CommandSubscriber
  share ONE error-classification symbol, proven BY MUTATION across BOTH suites. Added the shared-
  constant pin + the scout cross-suite mutation anchor + the `drop_error` fake capability.

## 6. Unrelated pre-existing mypy debt (flagged, not buried)

`uv run mypy loremaster` reports **102 errors** on this branch (`feat/surreal-unification`), ALL in a
pre-existing AUTH-test cluster (`test_auth_composition.py`, `test_permission_resolver_seam.py`,
`test_hosted_readonly_posture.py`, `test_allowlist_roster.py`, `test_google_token_verifier.py`,
`test_auth.py`, `_auth_fixtures.py`, `test_auth_identity_seam.py`) — **zero in my four files**. Out
of my scope; surfaced per "flag unrelated failures, don't bury them". The operator decides.

---

_Contract author proposes; the adversary grades the contract; the operator rules; the lead
adjudicates. Order: contract → adversary → build → cold audit. This revised contract is ready for
the `contract-adversary` pass._
