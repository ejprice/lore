brief-base v14 read

STARTED: revising i-b contract per adversary F1/2/3 + §2.5

# REPORT — contract-63b-i-b-3

## SUMMARY BLOCK
- receipt: brief-base v14 read · brief project v7 read
- state: done-with-deviations
- deviations:
  - **F1 split (R2)**: the brief said "change the rescope pin to assert GovernedConflict". The seam it
    exercises is `execute_transaction` (STORE layer), which per §2.5 CANNOT raise GovernedConflict
    (a layering fact the adversary's own F1 probe measured). Resolved by SPLIT: the store-layer pin
    asserts `TxnGovernedConflictError` (§2.5 rider i) + hygiene; a NEW governed-layer pin asserts
    `GovernedConflict` via `guarded_write` (§2.5 rider vi / point 4). Both typed outcomes pinned at
    their honest layers; no raw marker anywhere. See F1 ANALYSIS.
  - **cand-2 rider-i "both raise sites LIVE"**: transaction seam is LIVE (pin F, both entry points);
    `run_query` is covered by unit (`_domain_rejection_error`) + structural (routes through it),
    because governed conflicts never flow through `run_query` in production. Honest, deterministic.
- Packages considered: none — no mechanism specified (contract tests only; the §2.5 reference build
  reuses existing `_txn`/`governed`/`render` seams, hand-rolls nothing new).
- Reuse ledger: none — no NEW production reusable symbols introduced by the CONTRACT. (The reference
  build EXTENDED existing seams: `_txn._classify_engine_error`/`_domain_rejection_error`,
  `governed.guarded_write`→`authorize_guarded`+`GuardedPlan`, `server.render_subject_bound` via
  `render_line`/`render_attributed` — those are the BUILDER's symbols, described here for reproducibility.)
- Graded: contract-author (no verdict rendered on another's artifact). HEAD 6f64649 · HEAD-at-report 6f64649 · SAME.
- decisions-needed: none (F1 layering fork resolved within contract-author authority — R2 split; flagged as a deviation).
- receipt POINTERS:
  - RED-at-HEAD: this report §RED-AT-HEAD (6 pure-unit failed/1 green invariant; F1 5 failed via
    `_require_new_api`; cand-2 F 2 failed via unbuilt type; 4 i-b modules 27 failed/11 passed).
  - Satisfiability: this report §SATISFIABILITY (25 passed / 0 failed on a §2.5-compliant reference;
    `loremaster.__file__` = /tmp/lore-ref-63bib3/… asserted; `-n0`; no hang).
  - Sweep: this report §SATISFIABILITY (raw-marker sweep — only the `not in message` hygiene guard remains).
  - Finding #456: annotated FOLDED (lore_findings #456, contract-63b-i-b-3 event 2026-09-04).

## WORK ORDER (this run)
Revise the committed i-b memory-fidelity RED contract (6f64649) per REPORT-adversary-63b-i-b.md
(F1 CONFIRMED BLOCKER + candidates 2/3) + design §2.5 ADDENDUM + §3.3:
1. FIX F1 (BLOCKER C-DEF): rescope-conflict pin asserts raw `governed_conflict` underscore marker →
   change to typed outcome (GovernedConflict) + atomicity legs. Sweep for any other raw-marker assertion.
2. ADD §2.5 `_txn` classification UNIT pin (candidate 2): marker→typed subclass w/ fixed label, both raise
   sites, hygiene (no raw marker/suffix/table/id), `_rollback_verdict` untouched. RED-at-HEAD.
3. FIX candidate 3 (render coverage REACH, §3.3 pin ii): derive render set from-truth, not hardcoded name.

## F1 ANALYSIS + DECISION (a fork the brief did not anticipate — layering)
Measured ground truth (lore_get_symbol at HEAD 6f64649):
- `execute_transaction`/`execute_read_transaction` live in `loremaster.store._txn`; they CANNOT
  import `loremaster.governed` (a layering fact). Per §2.5 they raise the TYPED store error
  `TxnGovernedConflictError` (a `SurrealStoreError` subclass) with the FIXED label. The adversary's
  own F1 probe MEASURED exactly this: `type=TxnGovernedConflictError`, `isinstance … = True`,
  `'governed_conflict' in msg = False`. So `execute_transaction` CANNOT raise `GovernedConflict`.
- `remember` (the composed governed path that also runs the §2.2-step-4 ledger compensation) uses
  `self.handle` = `StoreHandle(acquire=self._ensure_connection, drop=self._drop_connection, url)`
  — NO `on_acquire` seam. A deterministic re-scope conflict cannot be injected through `remember`
  without monkeypatching internals; a real race is non-deterministic (CLAUDE.md forbids).
- `guarded_write` IS deterministically injectable (`store=` param via `store_handle(on_acquire=…)`)
  and maps → `GovernedConflict`, BUT runs only the standalone close (no composed successor), AND at
  HEAD it already raises `GovernedConflict` via the OLD Python `row_count==0` branch (so a bare
  `pytest.raises(GovernedConflict)` on it is GREEN-at-HEAD, not RED).

Two readings of the brief's F1 instruction ("assert GovernedConflict on THIS test"):
- **R1 (impossible-as-literal):** keep the test on `execute_transaction` and assert `GovernedConflict`
  → UNSATISFIABLE (store layer can only raise `TxnGovernedConflictError`). Re-implementing the
  mapping inside the test is a tautology (fixture cannot discriminate). REJECTED.
- **R2 (chosen):** SPLIT the concern across two deterministic, layer-honest pins, and pin
  `GovernedConflict` where it is real:
  1. Retarget the existing composed-path test → assert `isinstance(conflict.value,
     TxnGovernedConflictError)` (§2.5 rider i store type) + hygiene (rider ii: message carries the
     fixed label, NOT the raw marker/`<t>:<id>` suffix) + KEEP the validated atomicity legs
     (successor rolled back, predecessor unchanged). RED-at-HEAD via unbuilt `authorize_guarded`.
  2. ADD a governed-layer pin driving `guarded_write(store=handle_with_rescope_on_acquire_2)` →
     assert `isinstance(conflict.value, governed.GovernedConflict)` AND `isinstance(
     conflict.value.__cause__, TxnGovernedConflictError)` (RED-at-HEAD: at HEAD the Python branch
     raises `GovernedConflict` with NO `TxnGovernedConflictError` cause, and the type is unbuilt;
     GREEN on the §2.5 reference where `raise GovernedConflict(...) from error`). This pins §2.5
     rider vi / §2.4 rider i's `GovernedConflict` END-TO-END mapping, deterministically.
  This removes the raw-marker C-DEF EVERYWHERE, pins BOTH typed outcomes at their honest layers, and
  is satisfiable on the §2.5 reference build. **DEVIATION from the brief's literal wording; flagged.**

## PROGRESS LOG
- (startup) report + idle-gate contract written; registered on lore_comms.
- (F1) measured the layering; chose R2 (split). See F1 ANALYSIS above.
- (F1 DONE) test_memory_supersede_atomicity_63b_ib.py:
  - import: added `from loremaster.store.surreal import SurrealStoreError`.
  - `test_a_rescope_on_the_composed_transaction_conflicts_and_rolls_back`: raw-marker assertion
    REMOVED → `isinstance(conflict.value, TxnGovernedConflictError)` (§2.5 rider i) + hygiene
    (`"governed_conflict:" not in msg`, no `race_pred`/`race_succ` suffix — rider ii); atomicity legs
    (successor absent, predecessor open) KEPT. Docstring updated to §2.5.
  - ADDED `TestTheComposedConflictGuardIsInStore::test_a_conflicting_guarded_close_surfaces_governed_conflict`:
    `guarded_write(store=handle_with_rescope_on_acquire_2)` → `pytest.raises(GovernedConflict)` +
    `isinstance(conflict.value.__cause__, TxnGovernedConflictError)` (the discriminator — RED at HEAD:
    OLD Python branch raises GovernedConflict with no such cause + type unbuilt) + predecessor open.
    This is the ONE pin proving §2.5 point 4 / rider vi (store→governed TYPE mapping end-to-end).
  - SWEEP: the ONLY raw-marker-in-exception assertion in the contract was this one. The
    `"governed_conflict:" in statements` assertion in `test_the_guarded_plan_fragment_carries_the_in_store_throw`
    is about the FRAGMENT's SurrealQL TEXT (the THROW our code authors, §2.5 point 1) — CORRECT, KEPT.
    f5_registration / replay_fidelity / render_bound files carry NO raw-marker-in-exception assertion.
    (definitive grep sweep run in the scratch copy — see satisfiability receipt.)
- (CAND-2 DONE) test_surreal_store.py::TestDomainRejectionErrorType EXTENDED (§2.5):
  - module import: added `_FailedStatement, _rollback_verdict, TxnFragment, compose, execute_read_transaction`.
  - A `test_the_classifier_maps_the_governed_conflict_marker_to_the_fixed_label` (classifier→label, RED).
  - B `test_the_domain_rejection_helper_maps_the_governed_label_to_the_typed_error` (helper both directions, RED).
  - C `test_the_governed_conflict_label_carries_no_raw_marker_or_suffix` (rider ii label hygiene, RED).
  - D `test_a_governed_conflict_rollback_is_a_domain_rejection_never_retried` (`_rollback_verdict` untouched
    is_conflict=False + positive control; GREEN-at-HEAD invariant guard, rider iii).
  - E `test_both_domain_raise_sites_build_their_rejection_via_the_one_mapping_helper` (structural: run_query
    AND _run_verified_transaction route through `_domain_rejection_error`; RED — ROUTING-IS-NOT-SHARING).
  - F `test_a_governed_conflict_throw_via_the_transaction_seam_raises_the_typed_error` (LIVE, parametrized
    execute_transaction + execute_read_transaction → TxnGovernedConflictError + hygiene + a NON-governed
    THROW → plain SurrealStoreError positive control + caplog forensics-survive control; RED) + fixture
    `governed_conflict_conn`.
  - NOTE on §2.5 rider i "both raise sites LIVE": the transaction seam is exercised LIVE (F); `run_query`
    is covered by unit B (`_domain_rejection_error` maps) + structural E (run_query routes through it),
    because a governed_conflict never flows through `run_query` in production (guarded_write/remember use
    the transaction seam) — a live run_query THROW leg is added IFF the satisfiability probe shows
    `.query()` raises on THROW (else the unit+structural pair is the honest, deterministic cover).
- (RIDER v DONE) test_retry_seam.py::TestTheGovernedConflictClassIsRegisteredInTheSeam — the classification
  family gains the governed member (marker+label+typed subclass registered in _txn.py; subclass of
  SurrealStoreError; label no-raw-marker). RED-until-built.
- (CAND-3 DONE) test_memory_render_bound_63b_ib.py: replaced the hardcoded
  `test_the_recall_render_takes_the_subject_and_calls_render_subject_bound` with derived
  `test_every_governed_read_render_calls_render_subject_bound` + helper `_governed_read_render_methods()`
  (from-truth: `_resolve_subject`-calling AppContext entry points → their `_render_*` calls; grows as
  63b-ii comms reads land; non-vacuity anchored on `_render_recalled_memories`; verified caller set at
  HEAD = {recall(read,renders), remember(write,no-render)} → no false positive). RED-at-HEAD.

## RED-AT-HEAD (each RED for the right reason, at HEAD 6f64649, TEST store :18000, `-n0`)
- Pure-unit (no store): **6 failed, 1 passed**.
  - `test_the_classifier_maps_the_governed_conflict_marker_to_the_fixed_label` — FAILED (governed label unbuilt).
  - `test_the_domain_rejection_helper_maps_the_governed_label_to_the_typed_error` — FAILED (helper/type unbuilt).
  - `test_the_governed_conflict_label_carries_no_raw_marker_or_suffix` — FAILED (label unbuilt).
  - `test_a_governed_conflict_rollback_is_a_domain_rejection_never_retried` — **PASSED** (GREEN invariant
    guard, §2.5 rider iii — `_rollback_verdict` already leaves a governed conflict is_conflict=False).
  - `test_both_domain_raise_sites_build_their_rejection_via_the_one_mapping_helper` — FAILED (sites raise plain).
  - `test_retry_seam.py::TestTheGovernedConflictClassIsRegisteredInTheSeam` — FAILED (members unbuilt).
  - `test_every_governed_read_render_calls_render_subject_bound` — FAILED (derivation FOUND
    `_render_recalled_memories` [non-vacuity passed], reds on missing `subject`).
- Store-backed F1 (`TestTheComposedConflictGuardIsInStore`) — **5 failed** via `_require_new_api()`
  (authorize_guarded unbuilt): the retargeted rescope pin + the new governed-layer pin + the 3 existing
  composed pins.
- cand-2 live integration `test_a_governed_conflict_throw_via_the_transaction_seam...` — **2 failed**
  (both params) via `TxnGovernedConflictError is None` (unbuilt) — reds before the store assert.
- 4 i-b memory-fidelity modules aggregate at HEAD: **27 failed, 11 passed** (a healthy RED contract;
  all 4 collect cleanly). Full 6-file collect-only: **893 tests collected, no collection errors**.

## SATISFIABILITY (§2.5-compliant reference; provenance asserted; `-n0`; no hang)
- Scratch built with `scripts/scratch_copy.sh /tmp/lore-ref-63bib3` — provenance ASSERTED:
  `loremaster.__file__ = /tmp/lore-ref-63bib3/loremaster/loremaster/__init__.py` (INSIDE the scratch).
- Reference build (throwaway; the BUILDER lands the real thing — described for reproducibility):
  - `store/_txn.py`: `TxnGovernedConflictError(SurrealStoreError)` (TxnContentionExhaustedError shape,
    no text-parsed attrs) · `_ERROR_CLASS_GOVERNED_CONFLICT` (fixed label) · `_GOVERNED_CONFLICT_MARKER
    = "governed_conflict:"` · `_classify_engine_error` gains the marker branch → the fixed label ·
    `_domain_rejection_error(error_class, message)` (label→type, ONE helper) · BOTH raise sites
    (`run_query`, `_run_verified_transaction`) route through it. `_rollback_verdict` UNCHANGED.
  - `governed.py`: `authorize_guarded`→`GuardedPlan` split; `GuardedPlan.fragments` emits
    `LET $gw_hit=(UPDATE … RETURN AFTER); IF array::len($gw_hit)=0 { THROW "governed_conflict:<t>:<id>" }`;
    `guarded_write` = authorize_guarded + fragments + execute + `except TxnGovernedConflictError → raise
    GovernedConflict from error`; the Python `row_count==0` branch DELETED.
  - `server.py`: `render_subject_bound(subject)` (via `render_line` + `render_attributed`);
    `_render_recalled_memories(recalled, *, subject)` prepends it (incl. empty case); `recall` passes `subject=`.
- Command (serial, timeout 600): `uv run python -m pytest -n0` over
  `test_memory_supersede_atomicity_63b_ib.py::{TestTheComposedConflictGuardIsInStore,TestAuthorizeGuardedIsDenyFirst,TestSupersedeAndInvalidateShareOneImplementation}`
  + `test_surreal_store.py::TestDomainRejectionErrorType` + `test_retry_seam.py::TestTheGovernedConflictClassIsRegisteredInTheSeam`
  + `test_memory_render_bound_63b_ib.py` → **25 passed, 0 failed** (no hang; ~4.7s). The retargeted
  rescope pin AND the new `_txn` unit pins AND the governed-layer GovernedConflict pin AND the derived
  render coverage pin ALL pass on the §2.5-compliant reference.
- SCOPE of this receipt (honest bound): the reference is scoped to the surfaces MY fixes touch
  (§2.5 `_txn` + #441 `governed.py` split + #437 `server.py`). The UNCHANGED #441/#436 pins that drive
  the composed `remember` / `_replay_record` end-to-end (TestSupersedeIsAtomicUnderSuccessorFailure,
  TestSupersedeAuditRidesTheComposedTransaction, the replay-fidelity module, the f5_registration
  integration pin) require the FULL memory-layer build — the BUILDER's deliverable — which I
  deliberately did NOT reconstruct in a contract-author scratch (it would pre-empt the builder wave and
  risk a false satisfiability signal). Their SHAPE was validated at b2f9b0e by contract-63b-i-b; my
  §2.5 fixes do not alter them (they are error-TYPE-independent / on untouched seams).
- Raw-marker sweep (python, over the 4 i-b files + the F5 DATA file): the ONLY `"governed_conflict:"`
  in an exception context is the HYGIENE guard `assert "governed_conflict:" not in message` (the fix,
  not the C-DEF) + the `__cause__` TYPE check. `test_the_guarded_plan_fragment_carries_the_in_store_throw`
  asserts the marker in the FRAGMENT's SurrealQL text (§2.5 point 1 — correct, kept). replay_fidelity /
  f5_registration / render_bound / enforcement_63b_ia: ZERO mentions.

## WRITABLE SET / DISCIPLINE
- Edited (LIVE tree, contract only): `loremaster/tests/test_memory_supersede_atomicity_63b_ib.py`,
  `test_memory_render_bound_63b_ib.py`, `test_surreal_store.py`, `test_retry_seam.py`.
- NOT edited: production (`_txn.py`/`governed.py`/`server.py` in the LIVE tree — the §2.5/#441/#437
  build is the BUILDER's; contract-first), the F5 instrument, `test_memory_enforcement_63b_ia.py`
  (F5 DATA — kept intact), the other RED-at-HEAD pins (#441 atomicity legs, #436/#453 replay, #437
  render behavioral, F5 DATA — all validated, untouched).
- `ruff check` CLEAN on all 4 changed files (one auto-fix applied: dropped an unused
  `execute_read_transaction` module import — pin F reaches both transaction entry points via
  `getattr(_txn, entry_point)`, so neither is used by name; re-confirmed cand-2 RED-at-HEAD after: 6 failed / 2 passed).
- Did NOT commit (the lead commits). Did NOT touch git state.
- Scratch `/tmp/lore-ref-63bib3` is a disposable reference build (a `scratch_copy.sh` cp, NOT a git
  worktree). `rm -rf` was sandbox-denied at close-out, so it remains in `/tmp` — safe for the operator
  or lead to delete; it holds only the throwaway §2.5/#441/#437 reference edits, no deliverable.
