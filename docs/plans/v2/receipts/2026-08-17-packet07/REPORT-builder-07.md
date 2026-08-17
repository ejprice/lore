# REPORT — builder-07 (packet 07: #144 posture + #124 coverage — BUILD)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **State: done** — FORK-1 RULED (lead directive #5027, AUTHORIZED). Reorder applied + the
  stale comment updated; **full exit bar re-verified GREEN**. Packet ready for cold audit.
- Production build DONE and correct: `_sdk_guard.py` (field + shared-predicate helper +
  orthogonal check) makes all **6 previously-RED pins GREEN** + 6 GREEN controls =
  **12/12** on `test_retry_seam.py`. Full regression `test_retry_seam.py +
  test_ddl_write_target_coverage_124.py + test_floor_calibration_schema.py` = **623 passed,
  0 failed, 0 error**. Mutation-proof CONFIRMED twice (§MUTATION).
- **FORK-1 (RESOLVED):** conftest step-3 (`assert not report.multi_statement_violations`) had
  turned `test_the_runtime_leg_shares_the_txn_predicate_by_mutation` GREEN→ERROR at autouse
  teardown (the F0 test inverted the shared predicate BEFORE `connect_admin`, so the autouse
  guard misread bootstrap's single-statement DEFINEs). Lead #5027 authorized the 1-line reorder
  (invert AFTER connect+arm); applied + comment updated; verified green. Detail in §FORK-1.
- Deviations (all disclosed, none silent):
  - D1: conftest step-3 assertion IS added (my in-scope deliverable) → exposes FORK-1; left
    in place so the blocker is VISIBLE in the gate. F0 currently ERRORs by design of this handoff.
  - D2: deleted `TestNoMultiStatementDdlRidesABareQuery` (step 4) forced an orphaned-import
    cleanup (`ast`, `typing.Any`) in `test_floor_calibration_schema.py` — a regression my own
    deletion directly caused, fixed minimally (brief-base §2).
  - D3: fixture-provenance corrections landed in `test_surreal_store.py` +
    `test_memory_backend.py` — files OUTSIDE my build-touched set. Brief docs-step 2 authorized
    this ("contract-author flagged as owed"); flagged as a scope clarification (§DOCS).
  - D4: re-measured inherited number — the auth-WIP mypy baseline (#333) is **191** at HEAD
    `82e2587`, not the brief's stated "~102". All 191 are in auth/roster/permission/email files;
    ZERO in any file I touched.
- **Packages considered:** `surrealdb` SDK statement splitter/parser — READ installed
  `surrealdb/request_message/sql_adapter.py` (naive `.split(";")` joiner; no statement-count
  validation, no literal handling) → **bespoke detector, reuse `_txn._assert_envelope_integrity`**
  (`keep_with_trigger`: re-open if a future SDK ships a real SurrealQL statement parser). Matches
  contract-author + adversary.
- **Reuse ledger:** 1 new symbol, dispositioned. `_is_multi_statement_query`
  (`tests/_sdk_guard.py`) — lore_search "single-statement predicate / multi-statement check" →
  returned only `_txn._assert_envelope_integrity` (the `compose()` predicate) → **REUSED
  `loremaster.store._txn._assert_envelope_integrity`** (routes to it at CALL time; a thin
  arg-extraction adapter, NOT a `;`-logic clone — mutation-proven, §MUTATION).
- **Graded:** re-derivations rest on HEAD `82e2587` · `git rev-parse HEAD` = `82e2587` · SAME.
  (F1 removed-behavior count independently RE-DERIVED — §REMOVED-BEHAVIOR; not inherited.)
- **Decisions needed (LEAD/operator):**
  1. **FORK-1 — RESOLVED** by lead #5027 (reorder authorized, applied, verified green). No longer open.
  2. Confirm D3 scope (provenance edits in test_surreal_store.py / test_memory_backend.py) was intended.
- **Receipt pointers:** build = `tests/_sdk_guard.py` (`GuardReport.multi_statement_violations`,
  `_is_multi_statement_query`, `_guarded` check) + `tests/conftest.py`
  (`_no_sdk_call_escapes_the_retry_driver`); RED→GREEN §BUILD; mutation-proof §MUTATION;
  fork §FORK-1; removed-behavior §REMOVED-BEHAVIOR; #124 §124; docs §DOCS; gates §GATES.

---

## Capability check (brief-base §4)
All tools the brief assumes are present and working: lore MCP (loaded via `ToolSearch "+lore"`),
`lore_comms` (registered `builder-07`/`packet07-20260817`/builder), the spike-surreal 3.2.4 test
store (`ws://127.0.0.1:18000`, the `[real]` fixtures run against it), pytest/ruff/mypy, git
(read-only — I create no git state; the lead commits). No blockers of capability. The ONE blocker
is the FORK-1 design conflict, not a missing tool.

---

## §BUILD — the production change and RED→GREEN

Three edits to `loremaster/tests/_sdk_guard.py` (the runtime guard), one to `conftest.py`:

1. `GuardReport.multi_statement_violations: list[SdkEscape] = field(default_factory=list)` — a
   new surface parallel to `escapes`. (Added `field` to the `dataclasses` import.)
2. `_is_multi_statement_query(args)` — the single-statement predicate, **routing to the SHARED
   `_txn._assert_envelope_integrity` at CALL time** (`from loremaster.store import _txn` inside the
   function; catch `_txn.TxnEnvelopeViolationError`). Only `args[0]`, only if it is a `str`. This is
   the F0 requirement: an import-captured reference the monkeypatch cannot reach would leave the
   share pin RED. **NOT a `;`-logic clone** (routing-is-not-sharing).
3. In `_guarded`, inside the existing `if site is not None:` block (production frames only — the
   adversary's "Minor" scoping), ORTHOGONAL to the escape check: `if method_name == "query" and
   _is_multi_statement_query(args): report.multi_statement_violations.append(SdkEscape(...))`.
   Scoped to `query` by METHOD NAME (`query_raw` is the safe multi-statement path). Receiver-BLIND
   (the class is patched) — the keystone that lets the offline leg's receiver-name limit stand.
4. `conftest._no_sdk_call_escapes_the_retry_driver` gains `assert not
   report.multi_statement_violations` after the escape assertion (builder-job step 3). **This is
   what exposes FORK-1** — see below.

**RED→GREEN (WITHOUT the conftest step-3 assertion — isolates the guard change, = adversary's
reference build):**
```
$ uv run python -m pytest tests/test_retry_seam.py \
    -k "TestBareQueryMustCarryExactlyOneStatement or TestNoBareQueryCarriesAMultiStatementLiteral" -v
... 12 passed, 564 deselected in 2.90s
```
All 6 previously-RED pins now GREEN (multi-statement-inside-driver, ;-joined-non-BEGIN,
;-in-literal known-bound, F0 runtime-share, F5 oddly-named receiver, F2 quoted-literals) + the 6
GREEN controls (single-not-flagged, query_raw-not-flagged, bootstrap-observed, offline-scan, offline
control, offline-share).

---

## §FORK-1 — BLOCKING: conftest step-3 vs the F0 mutation test (needs a ruling)

**Symptom.** With the required conftest step-3 assertion in place, running the runtime+offline legs:
```
... 12 passed, 564 deselected ...              # each pin's OWN assertion passes
ERROR ...::test_the_runtime_leg_shares_the_txn_predicate_by_mutation   # at conftest teardown
E  AssertionError: 2 bare .query() call(s) carried MORE THAN ONE statement during this test:
E      store/_txn.py:1099 in _define_namespace() -> connection.query()
E      store/_txn.py:1115 in _define_database() -> connection.query()
```
The test's own assertion PASSES; it ERRORs at the **autouse teardown** (`conftest.py:212`).

**Root cause (traced + confirmed).** The F0 test inverts the SHARED predicate GLOBALLY
(`monkeypatch.setattr("loremaster.store._txn._assert_envelope_integrity", _invert)`, where `_invert`
flags EVERY statement as multi) **on its first line — BEFORE `connect_admin(live_env)`.**
`connect_admin` runs `bootstrap_session`, which issues single-statement bare
`.query("DEFINE NAMESPACE …")` / `.query("DEFINE DATABASE …")` from production `_txn.py`
(`_define_namespace`:1099, `_define_database`:1115). The **AUTOUSE guard is armed** (it is armed for
every test), attributes those calls to production frames, and — because the predicate is inverted —
`_is_multi_statement_query` raises for them, recording two multi-statement violations on the AUTOUSE
report. The conftest step-3 assertion then fails at teardown.

**Why nobody caught it.** The adversary's SUFFICIENT verdict rested on a reference build that added
the `_sdk_guard.py` field+check but **NOT the conftest assertion** (§C of REPORT-adversary-07: "in
`_guarded`, when … append" — no conftest change). So the F0 test + conftest step-3 combination was
never exercised. The F0 test's own assertion reads the TEST-FILE-aimed report (which correctly flags
the single-statement `_attempt` under inversion — the share is genuinely proven); the AUTOUSE report
catching bootstrap is a **test-isolation false positive** caused by the global monkeypatch.

**Why there is no clean implementation-side fix.** The F0 pin REQUIRES call-time predicate lookup
(an import-captured copy must stay RED). The autouse guard and the test-file guard share the SAME
`_is_multi_statement_query` → the SAME module attribute → both see the inversion. There is no way to
make the autouse guard use the un-inverted predicate while the test-file guard uses the inverted one.
(An install-time capture would technically pass the F0 test but contradicts the pin's documented
call-time intent and the adversary's reference build — a dodge, not a fix.)

**The fix — verified GREEN.** Reorder the F0 test so the inversion happens AFTER `connect_admin`
(bootstrap runs with the REAL predicate; the inversion is still active for the `_attempt` call, which
is all the pin needs). Minimal diff (`test_retry_seam.py::test_the_runtime_leg_shares_the_txn_
predicate_by_mutation`):
```python
-        monkeypatch.setattr("loremaster.store._txn._assert_envelope_integrity", _invert)
-
         connection = await connect_admin(live_env)  # connect BEFORE arming; bootstrap uses no compose
         report = _install_guard_aimed_at_this_file(monkeypatch)
+        monkeypatch.setattr("loremaster.store._txn._assert_envelope_integrity", _invert)
```
I applied this, ran, got **12 passed** (with the conftest assertion in), then **REVERTED it** (per
the spawn brief: STOP and report a contract-test bug, do not silently patch). The reorder PRESERVES
the pin's discriminating power: an import-captured reference or a `;`-clone still leaves the
single-statement `_attempt` un-flagged → the pin's own assertion RED (verified independently in
§MUTATION). It only stops the autouse guard from mis-reading bootstrap under the global inversion.

**RESOLUTION (lead directive #5027, AUTHORIZED).** The lead independently read the test and
confirmed the diagnosis. I reapplied the reorder AND updated the now-stale comment (the old
`# connect BEFORE arming; bootstrap uses no compose` no longer describes the code — replaced with a
comment explaining that bootstrap must run under the REAL predicate so the always-armed autouse
guard does not misread its single-statement DEFINEs, and that the inversion only has to be live for
the `_attempt` call, so it goes AFTER connect+arm). Re-verified:
```
two contract classes:        12 passed, 564 deselected
full regression set:         623 passed, 0 failed, 0 error   (was 625p+1err: F0's passing call-
                             phase was double-counted alongside its erroring teardown; −2 = the
                             deleted floor_cal class; F0 now clean)
mutation-proof (fixed tree): 1 failed (clean AssertionError at :9776, NOT a teardown error) → restored → 1 passed
ruff (all touched):          All checks passed!
mypy:                        zero errors in touched files / my symbols
```
Net change to the contract test = the authorized reorder + comment only; no assertion or fixture
value touched. The pin's discrimination is preserved (mutation-proof RED confirmed on the fixed tree).

---

## §MUTATION — mutation-proof sanity check (exit-bar requirement)

Defeated F0's fix by inlining a private `;`-clone into `_is_multi_statement_query` (does NOT call the
shared predicate), with the reorder fix temporarily applied for a clean baseline:
```
# CLONE (private ;-logic, ignores the shared predicate):
FAILED test_the_runtime_leg_shares_the_txn_predicate_by_mutation
E  AssertionError: with _txn._assert_envelope_integrity INVERTED, a SINGLE-statement bare
   .query() was NOT flagged — so the runtime leg does not read the shared predicate ...
   assert []
```
The share pin goes RED for exactly the right reason (the clone ignores the inverted predicate).
Restored the call-time-lookup implementation immediately after. So the runtime leg genuinely ROUTES
to the shared predicate — ONE IMPLEMENTATION proven by mutation, not by inspection.

---

## §REMOVED-BEHAVIOR — deleting `TestNoMultiStatementDdlRidesABareQuery` (step 4), adjudicated

Deleted the ONE class (`test_floor_calibration_schema.py`, floor_calibration.store + lease). The
"5 scattered pins" claim was a fabrication the adversary already corrected (F1); I **independently
RE-DERIVED** the real state rather than inherit it:
- The class held two methods: `test_neither_module_calls_query_on_a_connection_directly` (bans ALL
  direct `.query()`/`.query_raw()` on any non-`self` receiver in those 2 modules) + a positive control.
- **Its coverage is preserved by the pre-existing retry-escape lint+guard, NOT by my new offline
  leg.** My offline leg (`TestNoBareQueryCarriesAMultiStatementLiteral`) is narrower in 3 dimensions
  (only `.query()` not `query_raw`; only static multi-statement literals not single-statement direct
  queries; not runtime-composed strings) — it is NOT the subsumer.
- **Re-derived deletion-safety (AST scan of both modules, 2026-08-17 @ 82e2587):** both import
  `surrealdb` AND `_txn` (⇒ scanned by the `_talks_to_surrealdb` retry-escape lint), and their ONLY
  direct non-`self` SDK receivers are `connection.signin()` and `connection.close()` — BOTH in the
  guard's SAFE set. Everything else routes through the seam. So the retry-escape lint + autouse
  runtime guard already ban every unseamed SDK call in both modules → deletion loses no coverage.
- **The one real narrowing, accepted-with-note:** the deleted pin's `not-self`-receiver ban (name-
  agnostic) → the retry lint's `_is_connection_receiver` NAME-limit (connection/conn). **Zero current
  impact** (the only direct receivers are named `connection` and use SAFE methods). Not silently
  dropped — recorded here as a deliberate, evidence-backed narrowing.
- Deletion orphaned `ast` + `typing.Any` imports (used only by the deleted class) → removed (D2).
  `test_floor_calibration_schema.py` → **42 passed** (was 44; −2 = the deleted class), ruff clean.

---

## §124 — the #124 DDL-coverage test needs NO production change (confirmed)
`test_ddl_write_target_coverage_124.py` → **5 passed** against current production code, exactly as
the contract promised (production already declares every write-target table before first write; this
is a regression-prevention pin, not a RED missing-guard). Its premise holds — no STOP.

---

## §DOCS — documentation edits

1. **`docs/reference/surrealdb-31-capabilities.md` §8** — added a `[PROBED 2026-08-17, spike-surreal
   3.2.4]` bullet: the QUERY-TOO-COMPLEX parse recursion-depth branch
   (`_ERROR_CLASS_QUERY_TOO_COMPLEX`, marker `"recursion depth"`, finding #66) is **LIVE on 3.2.4 but
   ONLY for the fulltext `@@`/RRF query SHAPE** (~120 clauses) — simple-operator chains no longer trip
   it at any realistic size (probed to 40000 OR-clauses / 64000 nested parens / 32000 nested fn calls,
   all execute fine). Cites `scripts/probe_query_complexity_07.py` (the negative-space receipt) and
   the standard-gate live instrument
   `test_bypassing_both_clamps_still_raises_a_classified_store_error` (in `test_surreal_store.py` +
   `test_memory_backend.py`) as both the proof and the drift alarm.
   ⚠ **Spot decision:** the brief said "near the existing recursion-depth material in §5/§8", but the
   store ref had NO such material (it lives in `_txn.py` + the live tests). I placed it as a new §8
   bullet (house style, dated, cited). GROUNDED by my own run of the 4 live tests (4 passed on 3.2.4).
2. **Fixture provenance (D3 — files outside my build-touched set, brief-authorized):**
   `test_surreal_store.py:1358` + `test_memory_backend.py:2051` — the recursion-depth unit fixtures'
   `captured live … 3.1.5` provenance now ADDS that the classifier behaviour is RE-CONFIRMED live on
   3.2.4 by the sibling bypass test, while keeping the honest note that the byte-exact 3.2.4 raw text
   was NOT re-captured (that limit is only reachable via the full RRF query). Comment-only; both files
   still green + ruff clean. Flagged as D3 because these are not my build-touched files.

---

## §GATES — receipts (HEAD 82e2587, spike-surreal 3.2.4)
- **ruff** (every file I touched): `tests/_sdk_guard.py tests/conftest.py
  tests/test_floor_calibration_schema.py tests/test_ddl_write_target_coverage_124.py
  tests/test_surreal_store.py tests/test_memory_backend.py` → **All checks passed!**
- **typecheck** (`scripts/typecheck.sh`): **zero errors in any file I touched**; zero errors
  referencing my new symbols (`multi_statement_violations` / `_is_multi_statement_query` /
  `GuardReport`). Total repo count **191** — ALL in auth/roster/permission/email files (the #333
  auth-WIP baseline). ⚠ The brief's "~102" is a stale inherited number; the real HEAD baseline is 191
  (D4). None are mine.
- **Regression** (`tests/test_retry_seam.py tests/test_ddl_write_target_coverage_124.py
  tests/test_floor_calibration_schema.py`): **623 passed, 0 failed, 0 error** (final, post-#5027
  reorder). The two contract classes = **12/12**. (The 1 pre-existing `RuntimeWarning` about
  `_empty_subscription` at `test_retry_seam.py:3216` is not mine — pre-existing in
  `TestEverySdkCallSiteActuallyRetries`.)
- **Live recursion-depth tests** (grounding the §DOCS claim): 4 passed on 3.2.4.
- No git state created. I did not commit. The packet goes to a cold audit before commit/deploy.

## Scope notes / flags
- FORK-1 RESOLVED (lead #5027). Everything is complete and green. Ready for cold audit.
- D3 (provenance edits outside build-touched files) — confirm intended.
- I did NOT touch finding #124's ledger row or `DESIGN-sidecar-144-posture.md`. The ONLY contract-test
  change is the lead-authorized F0 reorder + its comment update (no assertion or fixture value touched).
- ⚠ For the cold audit: `DESIGN-sidecar-144-posture.md` §5.2 still carries the fabricated "5 pins"/
  subsumer framing (adversary-07 flagged it; the lead routed that doc-fix to fable-sidecar-07, not me).
