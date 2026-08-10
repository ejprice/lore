# REPORT-builder-treescan

brief-base v10 read
brief project v7 read

## SUMMARY
- **state:** done-with-deviations. Both RED contracts GREEN; all 5 A-SUB adopters migrated; F one-derivation + mutation proofs pass; promotion proven by mutation.
- **deviation (scope):** edited `loremaster/loremaster/store/__init__.py` (a 1-line re-export) — OUTSIDE the literal writable set (which named `_txn.py`), but REQUIRED so `loremaster.store._txn_coroutines` resolves (F5-ruled package home + the contract pin `test_the_helper_is_importable_from_loremaster_store`). `__init__.py` was empty; edit is minimal/non-destructive. See §Deviations.
- **deviation (DRY):** also routed `forgery_door_sweep.public_coroutines_not_swept` through the core (a 3rd `vars(_txn)` walk, same #279 policy; output-preserving) — not named in brief.
- **deviation (scope-widening, measured-benign):** backoff + secret_leak scan-2 route through `parse_production_trees` which covers scripts/skills TEST files too (+24 files); measured 0 new offenders. secret_typing kept production-only (widening would flag test fixtures).
- **deviation (ruling):** comms_footer Scan B narrowed 131→90 (operator reading (b)); the 41 leaked non-loremaster test files drop (measured 0 query sites).
- **deviation (right-sized):** `install_parse_guard` GENERALISES the `_sdk_guard` pattern (reuses `GuardCannotSubstantiate` + the #136/arm-precondition/plain-def policy) rather than fully extracting a shared `(primitive, sanctioned-frame)` scaffold — the contract left that "the builder's call". See §Decisions.
- **deviation (unused grant):** `test_retry_seam.py` (granted "only for the `_rebind_everywhere` promotion") left UNTOUCHED — it has no `_rebind_everywhere`; `_sdk_guard.py` also untouched (SDK path intact, 562 pass).
- **Packages considered:** parsing/introspection use the **stdlib** directly (`ast`, `tomllib`, `inspect`) — no hand-roll, `keep`. The runtime parse-guard is **bespoke** (no package wraps `builtins.compile`+stack-walk) but REUSES the in-repo `_sdk_guard` scaffold + `GuardCannotSubstantiate` (ONE IMPLEMENTATION). `_rebind_everywhere` promoted (in-repo), not cloned. No third-party dependency needed or missing.
- **Graded:** builder (no external verdict). Built at `003a337` · HEAD-at-report `003a337` · SAME. Contracts authored RED at `641f758` (A-SUB) / `e1dfa14` (F); re-derive if base moved.
- **decisions-needed:** (1) confirm `loremaster/store/__init__.py` is the right home for the `_txn_coroutines` re-export (vs relocating). (2) OK to leave the guard as a generalised-pattern rather than a fully-extracted shared scaffold (§12.5 candidate)?
- **receipt pointers:** RED→GREEN §RED→GREEN; mutation proofs §Mutation; gate tails §Gates; deviations §Deviations.

## RED→GREEN
- **F — `test_store_seam_one_derivation.py`: 23 pins, RED→GREEN (23 passed).** RED at HEAD: `loremaster.store._txn_coroutines` did not exist (`_load_core` → `AttributeError`) and `seam_bindings` had no `seams=` (`TypeError`). GREEN after: `_txn_coroutines` built in `_txn.py` (re-exported at the package), `store_seams`/`seam_bindings`/`_degrade_every_STORE_seam` routed through it.
- **A-SUB — `test_ast_reach_helpers.py`: 54 collected → 50 passed + 4 skipped.** RED at HEAD: `parse_production_trees` / `assert_scan_reached_every_member` / `install_parse_guard` absent (lazy accessors raised NAMED failures). GREEN after build + 5-adopter migration. The 4 skips are the `_ASUB_PARSE_SKIP` adopters (backoff/secret_typing/secret_leak/comms_footer) correctly skipping Layer-3's fixture-consumer pin (they expose no nullary workspace-tree fixture; covered by L1 + the skip-coverage pin). #349/#351 KNOWN_BOUND pins GREEN (left contract-side, unchanged).
- **FULL `test_blocks_edge.py`: 210 passed** (the cold-audit re-run target).

## What changed (symbols, not line numbers)
### Shared substrate — `loremaster/tests/_logging_fixtures.py` (all NEW, appended)
- `parse_production_trees(*, include_scripts=True, include_skills=False, include_tests=False) -> dict[str, ast.Module]` — the ONE tree parser; keys = repo-relative posix; `include_tests=True` re-adds `<member>/tests` (the §10 R6.3 granularity hazard). Roots from `workspace_roots`.
- `assert_scan_reached_every_member(scanned_trees, *, extra_roots=("scripts",)) -> None` — the ONE coverage assertion; oracle read INDEPENDENTLY from pyproject; fail-closed on empty; `scanned_packages == declared_members ∪ extra_roots`.
- `install_parse_guard(monkeypatch, *, watched_root=None, witness=None) -> ParseGuardReport` (+ `ParseEscape`, `ParseGuardReport`, `_source_to_member_map`, `_first_workspace_site`, `_stack_has_frame`, `_require_parse_root_runs`) — L1 runtime guard wrapping `builtins.compile` (plain def, stack-walk at CALL time). `.escapes`/`.observed`/`.intercepted`/`.require_observations` mirror `_sdk_guard.GuardReport`; `.member` resolved from SOURCE TEXT (offenders pass no `filename`); primitive `ast.parse`/`compile` from whether the caller frame is `ast.parse` (routing VERIFIED on 3.14.6 by the contract's pos-control).
- `_rebind_everywhere` — PROMOTED here from `test_store_seam_one_derivation` (§10 #3, ≥2 reusers F+A-SUB); `_workspace_root` / `_declared_workspace_members` helpers.

### F (#279)
- `loremaster/loremaster/store/_txn.py`: `_txn_coroutines()` — the ONE walk (every coroutine defined in `_txn`, WIDE superset = `{run_query, execute_transaction, execute_read_transaction, retry_on_conflict, bootstrap_session, _run_verified_transaction, _txn_query_raw}`).
- `loremaster/loremaster/store/__init__.py` (⚠ out-of-set): `from ._txn import _txn_coroutines as _txn_coroutines` — package-level home.
- `scripts/forgery_door_sweep.py`: `store_seams` / `public_coroutines_not_swept` route through `_txn_coroutines()` (public+statement / public+no-statement filters, same fn objects); `seam_bindings` gains `seams=` (default = door subset).
- `loremaster/tests/test_blocks_edge.py`: `_degrade_every_STORE_seam` derives from `_txn_coroutines()` intersected BY IDENTITY with what `loremaster.tasks` binds (imports nothing from `scripts`); adds `assert "bootstrap_session" in patched`.
- `loremaster/tests/test_store_seam_one_derivation.py`: imports the promoted `_rebind_everywhere`; local clone deleted.

### A-SUB (F4) adopter migrations
- **anchored**: `_parse_production_trees` → routes to `parse_production_trees`; `TestScanCoverage` → `assert_scan_reached_every_member`; stale `_scanned_roots`/`_SCANNED_ROOTS` retired. `production_trees` fixture kept (the delta-adversary-3 survivor target, a checked variable).
- **backoff**: the whole-workspace Pow scan routes through `parse_production_trees(include_scripts=True, include_skills=True)`; split-leg `_production_python_files` retired.
- **secret_leak**: function-name scan (`include_scripts=False`, behaviour-preserving) + the locals/hook scan route through the parser; the corpse-prose scan is NON-parsing (KNOWN BOUND #349), left as-is.
- **secret_typing**: `_SCANNED_MEMBERS` RETIRED; `_python_sources` → `_python_source_trees` (reuses `production_sources` for display+production-filter, `parse_production_trees` for the sanctioned trees — preserves display format + production-only set so allowlists keyed on display keep matching); coverage pin → `assert_scan_reached_every_member`. lorerunes single-package scans kept (allowlisted).
- **comms_footer**: Scan A (`TestTheCharsetGuardDoesNotTeachAFalseRationale._scan`, non-parsing marker scan) derives its file set from `parse_production_trees(include_tests=True)`; Scan B (`TestNoCommsIdentityReachesQueryTEXT._scan`) consumes `parse_production_trees(include_tests=False)` trees (narrowed 131→90); `_scan_source` kept for synthetic controls via extracted `_doors_in_tree`; `_workspace_scan_roots` retired.

## Mutation proofs (§Mutation)
- **F sharing (`_txn_coroutines`)**: `TestSharingProvenByMutation` (parametrised over live door/wide surfaces) drops each seam from the shared core → both `store_seams`/`seam_bindings` AND `_degrade_every_STORE_seam` redden. GREEN (in the 23).
- **A-SUB sharing (`parse_production_trees`)**: Layer 3 `test_each_real_fixture_consumer_reddens_when_the_shared_parser_is_dropped` (anchored) + `test_the_rebind_mutation_reaches_a_from_import_binding`. GREEN.
- **Promotion (`_rebind_everywhere`, §10 #3)**: manually broke the shared `_rebind_everywhere` (byte-exact backup+restore) → **11 pins reddened across BOTH files** (A-SUB from-import proof + all F sharing pins); restored byte-exact; re-verified 11 GREEN. Proves both route through the ONE tool, not a private copy.

## Gates (tails)
- `pytest` (all touched suites, `-n auto`): consolidated **662 passed, 4 skipped**; `test_blocks_edge` **210 passed**; `test_retry_seam` **562 passed**; `test_logging_setup` **44 passed**.
- `ruff check` on all 11 touched files: **All checks passed!**
- `scripts/typecheck.sh`: exit 1 (RED_ADJUDICATED at HEAD) — **191 mypy errors, NONE in my files** (all in unrelated auth/posture/roster contract files: `test_auth_composition` 40, `test_roster_parser` 36, `test_posture` 35, …). My changes add zero mypy errors.

## Deviations (detail)
1. **`store/__init__.py` (out-of-set, REQUIRED).** The F5 ruling + the pin `test_the_helper_is_importable_from_loremaster_store` require `loremaster.store._txn_coroutines`; `__init__.py` was empty and not in the writable set. Exact edit: a module docstring + `from ._txn import _txn_coroutines as _txn_coroutines`. Left as an edit (not a flag-only) because the mandated F deliverable cannot green without it. → decision-needed (1).
2. **`public_coroutines_not_swept` routed through the core** — same #279 policy as `store_seams`; leaving it a private `vars(_txn)` walk would be the exact "did the fix reach all copies" trap. Output-preserving.
3. **backoff/secret_leak scan-2 widen into scripts/skills test files** (+24 files) — measured 0 new offenders (variable-Pow / capture_locals / excepthook). secret_typing deliberately did NOT widen (its scans would flag plain-str test fixtures) — it filters to production via `production_sources`.
4. **Scan B narrowing 131→90** — operator reading (b); adjudicated by `test_scan_B_narrowing_drops_only_accidental_test_over_reach`; the 41 dropped files measured to hold 0 query-receiver sites (pre=130, post=130).
5. **Guard: generalised pattern, not a fully-extracted scaffold** — §12.5 named the extraction a candidate "the builder's call". The two guards' attribution walks genuinely differ (the parse guard must see THROUGH stdlib `ast.parse` to the workspace caller; the SDK guard uses immediate-caller-only). Reused: `GuardCannotSubstantiate`, the #136 anti-vacuity policy, the arm-time root precondition, plain-def-walks-at-call-time. → decision-needed (2).
6. **Concurrent siblings:** the working tree also shows `server.py`, `test_mcp_server.py`, `wave_gate.py`, `pending_contract_gate.py`, etc. modified — that is the server/scriptsgate sibling builders' disjoint work, NOT mine. My deliverable is the 11 files listed above. Did NOT commit (per brief).

## Flags
- 191 pre-existing mypy errors (auth/posture cycles) are RED_ADJUDICATED at HEAD, unrelated to this work — not chased. No FAILING TESTS surfaced in any scoped run.
