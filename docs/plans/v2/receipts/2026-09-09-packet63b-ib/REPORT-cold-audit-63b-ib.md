# REPORT-cold-audit-63b-ib

brief-base v14 read
Graded: f64c875 · HEAD-at-report: f64c875 · SAME (to be re-derived at close)

## SUMMARY BLOCK
- state: **done**
- role: COLD AUDITOR — REFUTE stance, builder≠grader (built NONE of this)
- scope: the whole 63b-i-b close-out delta c658781..f64c875 (8 commits)
- **VERDICT: GO** — packet 63b-i-b cleared to CLOSE. All 4 close gates independently GREEN (ALONE);
  all mandated mutation receipts HELD (FORK-B load-bearing leg reddened; FLAG-1/2 ORDER-MATTERS proven;
  ONE-mapping ROUTING-IS-SHARING proven); B1 corpse reconciliation exhaustive + legit; twin-retirement
  virtues preserved; no un-bounded residual.
- deviations (disclosed, both legit): TxnContentionExhaustedError docstring fix (f64c875);
  secret-typing allowlist add for a TEST-store probe (20a58c0). The lead's #460 ruff fix (a047eea) is fixed.
- Packages considered: none — no mechanism specified (audit, not a build)
- Reuse ledger: none (audit — no new symbols authored)
- Graded: f64c875 · HEAD-at-report: f64c875 · SAME
- decisions-needed (operator, non-blocking): obs-1 — a LOW-severity, out-of-ruling-scope ledger-durability
  edge (a foreign-supersede retire failure could revive P on a later rebuild). Surfaced per scope law;
  not a fix-now item, does not gate the close.
- receipt pointers: §GATES (4 gates) · §PROBES (FORK-B / FLAG-1/2 (a,b,c) / ONE-mapping / B1 / twin) ·
  §RESIDUAL TABLE · §DELTA CONFORMANCE.

## DELTA CONFORMANCE (read c658781..f64c875, source on disk — REFUTE)
Design authority: `docs/design/2026-09-08-packet63b-ib-closeout-rulings.md`. Independently
confirmed the built code matches the ruled shape (not relayed from builder reports):
- **§2.4-1 `_txn.py`**: `TxnDomainRejectionError(SurrealStoreError)` defined before
  `TxnGovernedConflictError`, which now subclasses IT (MRO Gov→Domain→StoreError).
  `_domain_rejection_error` returns `TxnDomainRejectionError` for non-governed label — ONE mapping,
  both raise sites inherit. ✓ (read `_txn.py` at HEAD)
- **§2.4-2 `local.py` remember**: compensation gated
  `isinstance(error, TxnDomainRejectionError) and plan is not None and self._ledger is not None`
  → delete. `plan is not None` guard retained (FP-06 unchanged). ✓ (local.py:727-732)
- **§2.4-3(a) FLAG-2**: `ledger.retire(supersedes, valid_until=now.isoformat(), superseded_by=memory_id)`
  AFTER a clean `_apply` (store-first, inside `_rebuild_lock`, past the try/except so it only runs
  on commit success). `now` bound at 615. ✓ (local.py:746-749)
- **§2.4-3(b) FLAG-1**: `_replay_record` pre-reads P's stored owner pair, composes the close ONLY on
  pair-match against S's stamped pair (metadata owner), else logs `memory.replay.close.pair_mismatch`
  WARNING + skips. ✓ (local.py:1395-1440)
- **Item 5 disjointness pin**: all 4 legs present —
  `issubclass(Domain,StoreError)`, `issubclass(Gov,Domain)`, `not issubclass(Conn,Domain)`,
  `not issubclass(Contention,Domain)` (atomicity:949-976). ✓
- **Item 3 tree-wide invariant pin**: `test_no_exact_type_check_on_surreal_store_error.py` —
  deny-by-default over `<member>/tests/` via shared `parse_production_trees(include_tests=True)` +
  `assert_scan_reached_every_member` (reach as checked variable), discrimination control (4 spellings +
  negative), non-vacuity (≥40 files + ≥1 `assert_domain_rejection` adoption). ✓
- **B1.2-I shared helper**: `assert_domain_rejection` in `_surreal_harness.py` (isinstance Domain +
  not-Conn); I-class corpses route it. M-class mint pins use exact-type on the leaf. ✓
- **rider ii 2×2**: parametrized `{plain,supersede}×{transport,domain}` with
  survives=[T,T,T,F] — only supersede×domain compensates. No cell uncovered. ✓

## GATES (independent re-run — REFUTE)
| gate | independent result | builder claim | verdict |
|---|---|---|---|
| FULL suite (`uv run pytest -n auto`, run ALONE) | **11132 passed, 51 skipped, 3 xfailed, 0 failed** (317.27s, EXIT=0) | 11132p/0f | ✅ MATCH |
| currency (`pending_contract_gate.py --currency`) | **PASS** — typecheck GREEN, ruff GREEN, pytest GREEN; manifest `(typecheck,ruff,pytest)`; `bounds: []`; 0 RED_ORPHANED (EXIT=0) | PASS 0 RED_ORPHANED | ✅ MATCH |
| `./scripts/typecheck.sh` | **EXIT=0** — all 7 members/dirs OK + shellcheck OK | EXIT=0 | ✅ MATCH |
| `uv run ruff check .` | **All checks passed! (EXIT=0)** | clean | ✅ MATCH |

Full-suite tail receipt: `11132 passed, 51 skipped, 3 xfailed, 9 warnings in 317.27s` · EXIT=0.
(9 warnings = benign RuntimeWarnings from a deliberate un-awaited-coroutine hook test — not failures.)
#461 (gate mypy-self-destruct) is MOOT: `bounds: []`, currency PASS, no orphan window.
Scratch provenance receipt: `loremaster -> .../scratch-63bib/loremaster/loremaster/__init__.py` (inside the copy).

## PROBES (mutation receipts — scratch `.../scratch-63bib`, provenance-asserted)
All probes: declared expected-RED from `--collect-only` BEFORE mutating; baseline GREEN confirmed;
observed-RED diffed against declared BOTH ways; restore → GREEN.

### PROBE 2 — FORK-B mutation receipt (Fable's rider) ✅ HELD
Mutation: `AppContext.render_subject_bound` → bare f-string (no render_line/render_attributed seam).
Baseline: 3 passed. Declared expected-RED = observed-RED = all 3:
- (i) `test_link5_render_containment.py::TestEveryRenderCandidateIsDrivenOrOut::test_every_candidate_is_driven_or_out` — **RED** ✅ **LOAD-BEARING leg reddened** → the P-U universe derivation is a checked variable with NO blind spot; FORK-B Reading A holds (no re-open).
- (ii) `…::TestEveryDrivenRenderNeutralisesEveryForgery::test_no_shape_leaks_the_forgery[_render_recalled_memories]` — **RED** ✅
- (iii) `test_memory_render_bound_63b_ib.py::TestTheBoundLineContainsForgedIds::test_a_forged_principal_id_does_not_escape_the_render` — **RED** ✅
Restore → 3 passed; `server.py` byte-exact vs HEAD (`SERVER_PY_IDENTICAL`).

### PROBE 3 — FORK-2 §2.4 durability (FLAG-1/2 + ONE-mapping) ✅ ALL HELD
All in scratch; each: baseline GREEN → mutate → observed-RED == declared-RED (both ways) → restore GREEN.
- **(a) drop pair-guard owner predicate** in `_replay_record` (force close unconditionally):
  `test_memory_replay_fidelity_63b_ib.py::TestTheReplayCloseIsPairGuarded::test_a_cross_owner_replay_close_is_skipped_with_a_warning` → **RED** ✅ (foreign P closed across owners); same-owner positive control → GREEN.
- **(b) ship (b) WITHOUT (a)** (remove the `remember` retire-P block, keep the pair guard):
  `…::TestAForeignSupersedeSurvivesARebuild::test_an_admin_bypass_foreign_supersede_stays_closed_after_rebuild` → **RED** ✅ (WARNING fires, P revived `superseded_by:None valid_until:None` — the exact ORDER-MATTERS defect); same-owner control → GREEN. Confirms (a)+(b) must ship together — and DO at HEAD.
- **(c) widen compensation to all-exceptions** (drop the `isinstance(TxnDomainRejectionError)`):
  rider i `test_a_transport_failure_on_the_composed_supersede_keeps_the_ledger_row` → **RED**; rider iv behavioural `test_exhausted_contention_…_keeps_the_ledger_row` → **RED**; 2×2 `test_the_ledger_row_survives…[True-transport-True]` → **RED**; the other 3 cells → GREEN. Only supersede×transport reds — allowlist-the-safe confirmed (contention also reds, so a deny-transport-only build still fails).
- **(iii) ONE mapping** — `_domain_rejection_error` returns plain `SurrealStoreError` for non-governed:
  RED set = helper-unit (test_surreal_store `test_the_domain_rejection_helper_maps_the_governed_label_to_the_typed_error` + atomicity `test_the_one_mapping_helper_returns_the_typed_domain_error_for_a_non_governed_label`) + compensation control (`[True-domain-False]`) + **both raise sites** (`test_a_governed_conflict_throw_via_the_transaction_seam_raises_the_typed_error[execute_transaction]` AND `[execute_read_transaction]` — their non-governed control legs = the ROUTING-IS-SHARING proof). ✅ The structural `test_both_domain_raise_sites_build_their_rejection_via_the_one_mapping_helper` correctly stayed GREEN (asserts routing, not type). Restore → GREEN.

Restore proof: `local.py`, `_txn.py`, `server.py` all byte-exact vs HEAD after every probe; combined
re-check of all probed tests → **46 passed** on the restored scratch.

### PROBE 4/5 — B1 corpse exhaustiveness + 63a_iv twin retirement ✅
- **Exhaustiveness:** the tree-wide invariant pin `test_no_exact_type_check_on_surreal_store_error.py`
  is a STATIC AST scan over `<member>/tests/` (covers SKIPPED tests too) and is GREEN in the full suite;
  combined with whole-suite green (any un-rewritten corpse reds on the correct build) that IS the
  exhaustiveness proof. Its non-vacuity leg (≥40 files ∧ ≥1 `assert_domain_rejection` adoption) passed.
- **Corpse rewrites legit (spot-checked 7, not hack-to-green):** I-sites →
  `assert_domain_rejection(…)` keeping the connection-kept/hygiene lines (test_surreal_store `:754`
  TestReplaceFile, `:2142` late-DDL, `:4411` RecordTrace, `:4516` QueryMessageHygiene, `:855`
  DomainRejectionErrorType poison); M-sites → exact-type on the LEAF `TxnDomainRejectionError`
  (`:887`, `:1040` non-governed throw). Matches B1.2 M/I/P policy.
- **Twin retirement (9e0524d):** whole 63a_iv module deleted (§1.2+§1.3 combined END STATE — a routing
  the ruling permitted for "same wave"). Virtues preserved by NAMED surviving pins, verified present:
  C1 recreate pin MOVED to `test_memory_enforcement_63b_ia.py:1468`; V1/V2 deny-by-default twin at
  `63b_ia:1304`; whole-tree twin at `63a_v:100`. Substrate deletion (C5) broke no importer — whole-suite
  collection 0 errors (11132 ran).

## RESIDUAL TABLE (C1 law — every item an individual verdict; NONE is a blocker)
| # | item | bound / verdict |
|---|---|---|
| #461 | pending_contract_gate mypy self-destruct | **MOOT** — `bounds: []`, currency PASS, no orphan window. Confirmed independently. |
| #460 | pre-existing ruff E501 in the F5 contract (lead's own 46288b6 regression) | **FIXED** by a047eea (pure line-split, meaning unchanged); ruff EXIT=0 confirmed. |
| R1 (re-adversary) | a SKIPPED test pinning a domain rejection by a spelling OTHER than the banned three (e.g. `.__class__.__name__ == "SurrealStoreError"`) | **Correctly bounded** — all 21 real corpses used exactly `type(x) is SurrealStoreError`; named bound + re-open trigger. Not a blocker. Concur. |
| R2 (re-adversary) | the ban forbids a bare-base `SurrealStoreError` MINT exact-type pin | **Correctly bounded** — by design (base is effectively abstract; P=0 today); re-open trigger stated. Concur. |
| R3 (re-adversary) | `assert_scan_reached_every_member` checks package coverage, reach via the shared parser | **SOUND** — reach genuinely derived from `[tool.uv.workspace] members`; empirically proven (M9 planted `lorerunes/tests`). Not a gap. |
| dev-1 | `TxnContentionExhaustedError` docstring corrected in f64c875 (disclosed) | **Legit** — served-prose regression the retype directly caused; correctly disclosed. |
| dev-2 | secret-typing allowlist add (20a58c0) for `probe_supersede_throw_rollback.py` | **Legit** — TEST-store probe (`:18000`), hardcoded dev literal (not a real secret), evidence-backed + re-open trigger; scan untouched. |
| obs-1 (cold-audit, LOW) | §2.4-3(a) `remember` retire-P and §2.4-3(b) replay both assume `ledger.retire` succeeds; a (rare) local-sqlite retire failure on a FOREIGN supersede after a clean store commit would revive P on a later rebuild (the pair guard refuses S's cross-owner close, and P's own row was never retired). | **Non-blocker, out of ruling scope** — a new failure mode (ledger durability), not introduced by this delta's shape; the ruling handles the happy path exactly. Surfaced for the operator per scope law; not a fix-now item. |

## VERDICT
**GO — packet 63b-i-b is cleared to CLOSE.**

Every close gate is independently GREEN (run ALONE): full suite **11132 passed / 0 failed** (EXIT=0),
currency **PASS / 0 RED_ORPHANED**, typecheck **EXIT=0**, ruff **EXIT=0** — all matching the builder's
claims. The production delta faithfully implements the ruled §2.4 shape (§2.4-1 typed-subclass retype ·
§2.4-2 domain-scoped compensation · §2.4-3(a)+(b) FLAG-1/FLAG-2 shipped together). Every mandated
mutation receipt HELD, declared-RED == observed-RED both ways:
- **FORK-B** — the LOAD-BEARING leg (`test_every_candidate_is_driven_or_out`) reddened → the P-U
  universe derivation has no blind spot; Reading A holds (no re-open).
- **FLAG-1/2** — (a) pair-guard drop → rider v RED; (b)-without-(a) → rider vi RED (ORDER-MATTERS
  proven); (c) all-exceptions → rider i + contention + supersede×transport cell RED.
- **ONE-mapping (iii)** — reds across both files + both raise sites (ROUTING-IS-SHARING).
B1 corpse reconciliation is exhaustive (static invariant pin + whole-suite green) and legit (M/I/P
policy, 7 spot-checked). The 63a_iv twin retirement preserved every virtue by a named surviving pin
(collection 0 errors). No un-bounded residual; the one new observation (obs-1) is a low-severity,
out-of-scope ledger-durability edge surfaced for the operator, not a blocker.

Graded: f64c875 · HEAD-at-report: f64c875 · SAME.
