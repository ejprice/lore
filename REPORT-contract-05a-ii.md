# REPORT-contract-05a-ii — the `await` verb RED contract (TESTS ONLY)

brief-base v11 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done — RED contract delivered (26 pins, all RED for the right reason), fake
  capability added, satisfiability + 8 mutation proofs run against a reference build.
- **Deviations:** (1) I built a KNOWN-CORRECT reference of the await seams in a DISPOSABLE
  scratch copy (`/tmp/await-ref-05aii`, provenance-verified) to earn the satisfiability +
  mutation receipts — production code in the REAL tree was NOT touched. (2) Scratch cleanup
  (`rm`) is sandbox-blocked; `/tmp/await-ref-05aii` + `/tmp/ref_{messages,server}.py` remain —
  disposable, no uncommitted value, operator may delete.
- **Capability check:** all tools present; lore reachable; only spike-surreal `:18000` reasoned
  about (no store connected — the reference ledger never opens a socket). No production touched.
- **Packages considered:** none — no mechanism specified (a test contract). await REUSES shipped
  seams; hand-rolls nothing.
- **Graded:** contract authorship — no builder artifact graded. `git rev-parse HEAD` = `d64cd23`.
- **Decisions-needed (escalations — see §Escalations):**
  1. **RATIFY the wait-machine seam shape** — I resolved a design gap the design-of-record left
     thin (`MessageLedger.await_inbox` with injectable `connect`/`sleep`/`now`, reusing
     `self.drain(peek=True)`); proven satisfiable, but the operator/lead should ratify (or the
     builder proposes an equivalent, and the ~13 wait-machine pins adapt).
  2. **await's non-empty render peek-teach nuance** — `_render_comms_drain(peeked=True)` teaches
     "re-run without peek=true", which await has no param for. Consume-teach fix? (Consumer-Law.)
- **Receipt pointers:** RED counts §1 · per-pin discriminators + mutation receipts §2 ·
  satisfiability §3 · builder requirements §4 · escalations §5 · unrelated mypy debt §6.

---

## 1. What was written, and the RED receipts

**Writable set honoured.** New: `loremaster/tests/test_comms_await.py` (23 behavioural pins).
Extended: `loremaster/tests/test_comms_tool.py` (exact-set + `test_await_params`),
`loremaster/tests/_message_fakes.py` (the `FakeMessageLedger.await_inbox` oracle). No
production code touched in the real tree.

**RED counts (real tree, HEAD `d64cd23`, await UNBUILT):**
- `test_comms_await.py` — **23 failed** (all RED). Causes, aggregated:
  - 9 × `ValueError: unknown comms action 'await'` (dispatch/render pins — await unregistered)
  - 8 × `AttributeError: 'MessageLedger' object has no attribute 'await_inbox'` (wait-machine pins)
  - 4 × `AttributeError: … 'await_live_select_statement'` (injection pins #5)
  - 1 × `AttributeError: module 'loremaster.messages' has no attribute 'AWAIT_BUDGET_S'` (F2)
  - 1 × the foreign-param pin (unknown-action guard fires before the strict-param check — flips
    GREEN when await is registered AND rejects `limit`)
- `test_comms_tool.py::TestCommsActionsTable` — **3 failed** (`test_exact_action_set` set-mismatch;
  `test_every_other_action_requires_prior_registration` + `test_await_params` `KeyError: 'await'`).
  `TestCommsToolRegistration` and the other table pins stay GREEN — no collateral breakage.
- `test_comms_waiting_line.py` — **14 passed** (the `_message_fakes` extension is non-breaking).

A green-at-write pin would test nothing; there are none — every pin reddens on the unbuilt seam.
Collection is clean (23 collected, no uncollectable — the message module + unbuilt seams are
reached at CALL time per the #133 discipline, never a module-scope import of a missing symbol).

**Gates on changed files:** `ruff check` clean; `mypy loremaster` reports **0 errors in my three
files** (102 pre-existing errors elsewhere — see §6).

## 2. The pins, their discriminators, and the mutation-proof receipts

Every load-bearing pin was mutation-proven: a plausible WRONG build was built in the scratch
reference, the pin watched RED, then restored. Table = mutation applied → pin → observed.

| # | Pin (property) | Wrong build the pin STOPS | Mutation receipt |
|---|---|---|---|
| 1 | **Snapshot-first short-circuit** — pending-at-entry returns immediately: no wait, no LIVE, no poll | "only-new / always-waits" | M1: removed the `if snapshot.entries: return` short-circuit → `TestSnapshotFirstShortCircuit` **RED** |
| 2 | **Final-snapshot-at-timeout (LOAD-BEARING)** — a deadline arrival is returned (fresh final snapshot), + the last read ran at/after the deadline | "renders empty off the stale last-wake read" | M2: replaced `return await _snap()` with `return <empty>` → `TestFinalSnapshotAtTimeout` **RED** |
| 3 | **Poll-only completeness** — LIVE silent, poll returns the traffic BEFORE the deadline | "LIVE-dependent" (waits out the budget) | M8: removed the in-loop re-drain (only sleep) → `TestPollOnlyCompleteness` **RED** |
| 4 | **Socket-drop non-loss (forgery)** — a DEAD LIVE (`KeyError` on establish) with traffic present → returned, no false-empty, no crash; **positive control**: genuine-empty → empty | "false-empty / crash on the KeyError boundary" | M3: `except → return <empty>` → non-loss pin **RED**, positive control **PASS** |
| 5 | **Injection — emitted LIVE statement** inlines ONLY the agent-id record literal: no `thread`, no caller substring, no bound `$param`, keyed on `out =` | inlines `thread` (DD-3.e door) / binds a param (SDK ignores → delivers nothing) | M4: appended `AND thread = 'q'` → `test_…inlines_no_thread…` **RED** |
| 6 | **Honest-empty-as-fact** — empty render names the SET (caller) + a TEMPORAL bound, never a disclaimer, never drain's bare "no unread messages" | bare disclaimer / reuse drain's empty render | M7: replaced the honest-empty with `render_line("no unread messages")` → both `…NamesTheBoundAsAFact` pins **RED** |
| 7 | **Waiting-line on debt via ONE shared helper** — discriminating pair (WITH/WITHOUT a question) + PROVEN BY MUTATION (monkeypatched `_render_comms_waiting_line` sentinel routes through await) | a private CLONE of the waiting line (routing ≠ sharing) | M5: cloned the await handler's waiting line → mutation pin **RED**; the output-identity pin stayed **PASS** (proving output-identity alone is blind to the clone) |
| F1 | **await PEEKS, never stamps** — every drain read is `peek=True`; return shape `stamped_seqs=[]`, `peeked=True`; two awaits both return | a stamping build (DD-4.c/#214 loss path) | M6: `peek=True → peek=False` → `test_await_reads…peek_true` **RED** |
| F2 | **budget is a fixed constant strictly under the ~60s ceiling** — the PROPERTY, not the number | a `timeout=` param / a value ≥ ceiling | RED via `AWAIT_BUDGET_S` unbuilt; the reference `55.0` satisfies `0 < x < 60` |
| 9 | **Exact-set + param honesty** — `"await"` in `_EXPECTED_ACTIONS`; `params={"thread"}`, `required=∅` | a drifted/foreign param surface | RED: set-mismatch + `KeyError` until registered |

**FIXTURE-MUST-DISCRIMINATE fix, caught by the mutation loop itself:** pin #4 first used
`_FakeLiveConnection(die_on_subscribe=True)` — a fault firing ONLY on `subscribe_live`. A correct
build that ESTABLISHES the LIVE without consuming it never hits that path, so M3's false-empty
mutation passed the pin **vacuously**. Switched to `dead=True` (the establish op itself raises the
PROBED `KeyError` shape), a fault EVERY build that touches the LIVE encounters — M3 then reddens
correctly. This is the "what wrong build would still pass this?" question answered by BUILDING it.

## 3. Satisfiability receipt (the C-DEF gate)

A KNOWN-CORRECT reference of the await seams (`MessageLedger.await_inbox` +
`await_live_select_statement` + `AWAIT_BUDGET_S`; `AppContext._comms_await` + the
`_COMMS_ACTIONS["await"]` registration + the honest-empty render) was built in a
provenance-verified scratch copy (`scratch_copy.sh`, imports asserted INSIDE the copy). Against
it the whole contract goes **35 passed / 0 failed** (`test_comms_await.py` 23 +
`TestCommsActionsTable` 12). So the contract is SATISFIABLE — it is not a C-DEF trap, and the
seam shape I resolved (§5.1) is buildable as specified. The reference is a throwaway grading
instrument; its exact source is reproducible from §4's seam contract (it lived only in the
disposable scratch).

## 4. NAMED builder requirements (the seams the pins reference)

1. **Registration** — `_COMMS_ACTION_AWAIT = "await"` + `_COMMS_ACTIONS["await"] =
   CommsActionSpec(AppContext._comms_await, params=frozenset({"thread"}), required=frozenset())`.
   AND a render case for `await` in `test_render_seam_pins`'s `C1_RENDER_CASES` so
   `assert_actions_covered` stays satisfied (that pin is OUT of my writable set — named here).
2. **Handler** — `AppContext._comms_await(self, *, agent_row, thread=None, **_ignored) -> Rendered`:
   calls `self.message_ledger.await_inbox(...)`; NON-empty → the SHARED `_render_comms_drain`
   (fenced bodies); EMPTY → an honest-empty naming the bound as a FACT (caller + waited-time)
   composed with the SHARED `_comms_waiting_lines` (ONE IMPLEMENTATION — the mutation pin #7
   enforces routing, not cloning).
3. **Wait machine** — `MessageLedger.await_inbox(self, *, agent_id, limit, thread=None,
   budget_s=AWAIT_BUDGET_S, poll_interval_s=…, connect=None, sleep=asyncio.sleep,
   now=time.monotonic) -> MessageDrainResult`. Snapshot-first (`self.drain(peek=True)`)
   short-circuit; else LIVE-primary (via `connect`) + poll-fallback (re-`drain`) within `budget_s`
   (measured via `now`); a FINAL snapshot at the deadline; catch `(*_CONNECTION_ERRORS, KeyError)`
   so a LIVE fault falls to poll (never a false-empty). Returns a PEEK (`stamped_seqs=[]`,
   `peeked=True`). The pins inject `connect`/`sleep`/`now` and monkeypatch `self.drain` (the snapshot
   seam), exactly as `test_scout.py` injects connect/sleep into `CommandSubscriber`.
4. **LIVE statement** — `MessageLedger.await_live_select_statement(agent_id: str) -> str`: the
   filtered `LIVE SELECT * FROM to WHERE out = <agent-id record literal>`; agent-id inlined, no
   `thread`, no bound param. **Builder BUILD-PROBE (live store, NOT an in-process pin — design
   §A.5):** confirm the record-id literal for a real uuid5 `.hex` id (which can start with a digit)
   PARSES on spike-surreal `:18000` and still discriminates — the reference used angle-bracket
   quoting (`agent:⟨…⟩`); confirm it against the live engine. Injection-safety is unaffected (the
   id is a charset-safe uuid5 hash).
5. **Constant** — `AWAIT_BUDGET_S` (the reference used `55.0`); pin F2 guards `0 < x < ~60`.
6. **The LIVE-wake + socket-drop against a REAL socket** is the DEPLOY-gated build probe / smoke
   (design §C, §A.6 Leg A/B), run on `:18000` by the Opus-4.8 live-leg builder — the in-process
   pins prove the STATE MACHINE (the recipe); only the real send-across-a-socket proves the wake
   (the cake). The probe report already settled LIVE-fires + the socket-drop shape
   (`docs/plans/v2/receipts/2026-08-09-packet05ai/REPORT-probe-await-05a-1.md`).

## 5. Escalations (surfaced, not silently resolved)

### 5.1 — RATIFY the wait-machine seam shape (design gap I resolved; recommend ratifying)
The design-of-record says "await mirrors `CommandSubscriber`" and "await REUSES the drain SELECT",
but does NOT specify the Python seam that makes the state machine testable in-process. That is a
genuine fork (brief-base §2). I resolved it as §4.3 — a `MessageLedger.await_inbox` method with
injectable `connect`/`sleep`/`now`, reusing `self.drain(peek=True)` for snapshot/poll/final reads
and `connect` for the LIVE wake. Rationale: it is the faithful `CommandSubscriber` mirror the
design + brief point at (`test_scout.py` is the template), it honours ONE IMPLEMENTATION (the drain
read is reused, not re-hand-rolled), and it is proven satisfiable (§3). **Alternative not taken:** a
standalone `InboxAwaiter` class constructed with the seams (also valid, more surface). **Recommend:
ratify §4.3.** If the builder prefers an equivalent shape, the ~13 wait-machine pins adapt to its
entry point — the OBSERVABLE properties (§2) are unchanged; only the seam the pins CALL moves.

### 5.2 — await's non-empty render peek-teach (Consumer-Law nuance)
`_render_comms_drain(peeked=True)` renders "peeked N of M pending — nothing stamped; re-run
WITHOUT peek=true to mark them seen". await has NO `peek` param — its caller consumes via a
subsequent **`drain`**, not `await(peek=false)`. So reusing `_render_comms_drain` verbatim teaches a
consume instruction await cannot honour. Under the hard trust definition a consumer acting on that
line is misdirected. **Fork for the builder/operator:** does await's non-empty render need a
variant teach ("…consume via `action=drain`")? I did NOT pin the exact peek-teach wording (pin #8
asserts only the FENCE + verbatim round-trip, which holds either way), so this is open latitude, not
a contract contradiction — flagged so it is a DELIBERATE choice, not an accident.

### 5.3 — the `assert_actions_covered` render case (named, out of my writable set)
Once the builder registers `await`, `assert_actions_covered` (test_render_seam_pins) REQUIRES a
render case for it. That file is outside my writable set — named as a builder requirement (§4.1).

## 6. Unrelated pre-existing mypy debt (flagged, not buried)

`uv run mypy loremaster` (the gate's loremaster leg) reports **102 errors in 8 files** on this
branch (`feat/surreal-unification`) — ALL in an AUTH-test cluster I never touched
(`test_auth_composition.py` 40, `test_permission_resolver_seam.py` 20,
`test_hosted_readonly_posture.py` 13, `test_allowlist_roster.py` 10, `test_google_token_verifier.py`
7, `test_auth.py` 7, `_auth_fixtures.py` 3, `test_auth_identity_seam.py` 2). **Zero are in my three
files.** This is pre-existing branch debt, out of my scope — surfaced per the "flag unrelated
failures, don't bury them" rule; the operator decides whether it wants it examined.

---

_Contract author proposes; the adversary grades the contract; the operator rules; the lead
adjudicates. The order is contract → adversary → build → cold audit — this contract is ready for
the `contract-adversary` pass._
