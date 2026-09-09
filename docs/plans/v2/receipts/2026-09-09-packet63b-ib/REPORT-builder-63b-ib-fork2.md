# REPORT-builder-63b-ib-fork2

brief-base v14 read · brief project v7 read

## SUMMARY
- receipt line: `brief-base v14 read` · `brief project v7 read`
- state: **done** — §2.4 (3 parts) built; every gate GREEN; FLAG-1/2 order-matters mutation-proven.
- deviations: **ONE** — also corrected `TxnContentionExhaustedError`'s docstring in `_txn.py` (it said a domain/ASSERT rejection "always raises the plain `SurrealStoreError`", falsified by my own retype → now `TxnDomainRejectionError`). A prose regression my in-scope change directly caused (brief-base §2 exception; P8d served-prose law). `ledger.py` NOT touched (`MemoryLedger.retire` already built + already documents "the supersede path").
- Packages considered: none — no library mechanism (a typed exception subclass + an `except`-gate reorder + a Python-leg pre-read; all reuse existing seams `_domain_rejection_error` / `MemoryLedger.retire` / `_replay_record`). Concurs with the design + adversary lines.
- Reuse ledger: 1 new symbol, dispositioned (§DRY LEDGER below) — `TxnDomainRejectionError` EXTENDED the `_txn` typed-error hierarchy + `_domain_rejection_error` mapping (repo precedent: `TxnContentionExhaustedError`/`TxnGovernedConflictError`), not a clone/new classifier.
- Graded: n/a (builder — no verdict rendered).
- decisions-needed: none. Build settled from the binding rulings + the proven reference (`patch_ref.py` `ref`).
- receipt POINTERS: §PROGRESS LOG M2 (edits, file:concern) · M3 (gates: target 1358p/0f, full suite 11132p/0f, ruff/typecheck/currency 0 RED_ORPHANED, bound discharged) · M4 (FLAG-1/2 mutation proofs, both PROOF HELD, tree restored byte-exact) · §DRY LEDGER.

## CAPABILITY CHECK
- Brief demands: edit `loremaster/store/_txn.py`, `loremaster/memory/local.py`, `loremaster/memory/ledger.py`, `scripts/pending_contracts.yaml`; run pytest, typecheck, ruff, currency gate; mutation-prove FLAG-1/2. All within tool access. lore tools loaded via `ToolSearch "+lore"`. ✓
- grep/rg over repo AND pytest stdout is HOOK-BLOCKED — using lore/Read + `--tb=line`/`tail`. ✓

## PROGRESS LOG
- M1 (read+plan): store law read (§1 DDL/§2 DML/§3 txn classification law/§4 RELATE/§5 concurrency — cited, not re-transcribed). Design rulings §2.4 (3 parts) + B1.1/B1.2 + riders i–vii read. Adversary report read — its `patch_ref.py` `ref` mode is the PROVEN reference §2.4 build (whole suite 9973/0 both adversaries). Corpse rewrites (~21 exact-type test sites) are the CONTRACT author's job (B1.3 item 6), already committed at HEAD `ae180c9` — OUT of my writable set. My build = production-only: 3 parts.
  - Part 1 `_txn.py`: `TxnDomainRejectionError(SurrealStoreError)` defined BEFORE `TxnGovernedConflictError`; reparent `TxnGovernedConflictError` to subclass it; `_domain_rejection_error` returns typed class for non-governed label.
  - Part 2 `local.py`: narrow compensation to `isinstance(error, TxnDomainRejectionError) and plan is not None and self._ledger is not None`; DOMAIN-scoped comment; import the class.
  - Part 3 `local.py`+`ledger.py`: (a) retire-P after composed txn commits; (b) pair-guarded replay close in `_replay_record`. Ship (a)+(b) together.
- M2 (build done, all 3 production edits landed):
  - `_txn.py`: `TxnDomainRejectionError(SurrealStoreError)` defined BEFORE `TxnGovernedConflictError`; `TxnGovernedConflictError` reparented to subclass it; `_domain_rejection_error` non-governed → `TxnDomainRejectionError`; docstring else-clause updated. **DEVIATION (disclosed):** also fixed `TxnContentionExhaustedError`'s docstring, which said a domain/ASSERT rejection "always raises the plain `SurrealStoreError`" — falsified by my own retype (now `TxnDomainRejectionError`). One-line accurate correction; a regression my change directly caused (brief-base §2 exception; P8d served-prose law).
  - `local.py`: imported `TxnDomainRejectionError`; narrowed compensation to `isinstance(error, TxnDomainRejectionError) and plan is not None and self._ledger is not None`; DOMAIN-scoped comment (keeps FP-06 rationale for the `plan is not None` keep); retire-P(a) after composed txn commits; pair-guarded replay close(b) in `_replay_record` with WARNING+skip on owner-pair mismatch.
  - `ledger.py`: **UNTOUCHED** — `MemoryLedger.retire` already built (ledger.py:195-218) and its docstring already names "the supersede path". No edit needed.
  - Import + hierarchy sanity (live): IMPORT OK; MRO `TxnGovernedConflictError→TxnDomainRejectionError→SurrealStoreError`; disjointness pin B1.3-5 all True (domain⊂store, gov⊂domain, conn⊄domain, contention⊄domain).
- M3 (gates, each run ALONE):
  - Target modules (2 FORK-2 + 11 corpse + invariant pin `test_no_exact_type_check_on_surreal_store_error.py`), `-n auto`: **1358 passed, 0 failed, PYTEST_EXIT=0** (45.38s). RED→GREEN: these 13 files were RED_ADJUDICATED at HEAD (`getattr` guards) → GREEN once the symbol landed.
  - Discharged bound: removed `packet-63b-ib-fork2-contract` from `scripts/pending_contracts.yaml` (self-destruct on symbol landing); `bounds: []`, DISCHARGED note added.
  - `uv run ruff check .` → All checks passed, RUFF_EXIT=0.
  - `./scripts/typecheck.sh` → all 7 members OK (loremaster 263 files), TYPECHECK_EXIT=0.
  - `uv run python scripts/pending_contract_gate.py --currency` → CURRENCY: PASS, every gate GREEN, **0 RED_ORPHANED**, CURRENCY_EXIT=0.
  - FULL suite `uv run pytest -n auto` (ALONE): **11132 passed, 51 skipped, 3 xfailed, 0 failed, FULLSUITE_EXIT=0** (321.52s). Warnings (9) are pre-existing (coroutine-never-awaited test fixtures + websockets-legacy DeprecationWarning), none from this change.
- M4 (FLAG-1/2 mutation proofs — the §2.4-3 ORDER-MATTERS proof; `scripts/mutation_proof.py`, mutates real tree + restores byte-exact, expected-RED declared from `--collect-only` BEFORE the run; PROVENANCE `loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`, real tree — the always-sound brief-base §6 alternative):
  - **(a) delete the pair-guard owner predicate** (`if (stored==stamped)` → `if True:`, always close): **PROOF HELD** — reds EXACTLY `test_memory_replay_fidelity_63b_ib.py::TestTheReplayCloseIsPairGuarded::test_a_cross_owner_replay_close_is_skipped_with_a_warning` (1 failed/33 passed); restore of a now-foreign predecessor observed (rider v). Restored byte-exact (md5 14cc03a6…).
  - **(b) ship pair-guard (b) WITHOUT retire-P (a)** (`if plan and supersedes and ledger:` → `if False and …`): **PROOF HELD** — reds EXACTLY `test_memory_replay_fidelity_63b_ib.py::TestAForeignSupersedeSurvivesARebuild::test_an_admin_bypass_foreign_supersede_stays_closed_after_rebuild` (1 failed/33 passed); captured log shows the pair-mismatch WARNING firing (b present) yet P revived (`superseded_by=None, valid_until=None`) on rebuild because (a) is gone — the #453 re-open shape. Restored byte-exact (same md5 14cc03a6…).
  - Both isolate cleanly (no unexpected reds), reproducing the adversary's W3/W2 results against the real tree. This IS the ORDER-MATTERS proof: (b) without (a) breaks fidelity; both ship together.
- M5 (residual-prose + scope): Python exact-substring scan (grep hook-blocked) of `_txn.py`+`local.py` for `plain SurrealStoreError` / `SUPERSEDE-SCOPED` / `supersede-scoped` → 0 residual. `run_query`/`_rollback_verdict` docstrings say "domain rejection → SurrealStoreError" — still TRUE (superclass; the correct `except`-catchable base to teach), left unchanged. `git status`: changed set = exactly `_txn.py`, `local.py`, `scripts/pending_contracts.yaml` (writable set); `ledger.py` untouched.

## DRY LEDGER (§6 — new reusable symbols)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `loremaster.store._txn.TxnDomainRejectionError` | `lore_get_symbol(_domain_rejection_error)` + `lore_get_symbol(TxnGovernedConflictError)` region | the 3-type raise surface (`SurrealConnectionError` / `TxnContentionExhaustedError` / plain `SurrealStoreError` for the non-governed domain label) with NO typed domain class; `_domain_rejection_error` is the ONE mapping both raise sites route through | **EXTENDED** the `_txn` typed-error hierarchy + `_domain_rejection_error` mapping — added the missing typed leaf and reparented `TxnGovernedConflictError` under it (repo precedent: `TxnContentionExhaustedError` / `TxnGovernedConflictError` were both added this way). NOT a new classifier, NOT a clone; the ONE mapping is preserved (both raise sites inherit it — ROUTING-IS-SHARING, proven at HEAD by the adversary's W4 mutation). Pair-guard locals + retire-P reuse existing `MemoryLedger.retire` / `self._query` / `self._as_list` — no new helper.

## FILES CHANGED (file:concern)
- `loremaster/loremaster/store/_txn.py` — Part 1: `TxnDomainRejectionError(SurrealStoreError)` (before `TxnGovernedConflictError`, forward-ref); `TxnGovernedConflictError` reparented to subclass it; `_domain_rejection_error` non-governed label → typed class + else-clause docstring; **[deviation]** `TxnContentionExhaustedError` docstring "plain SurrealStoreError" → `TxnDomainRejectionError`.
- `loremaster/loremaster/memory/local.py` — Part 2: import `TxnDomainRejectionError`; DOMAIN-scoped compensation gate `isinstance(error, TxnDomainRejectionError) and plan is not None and self._ledger is not None` + rewritten teaching comment. Part 3(a): retire-P after the composed txn commits. Part 3(b): pair-guarded replay close in `_replay_record` (WARNING + skip on owner-pair mismatch).
- `scripts/pending_contracts.yaml` — discharged the self-destructed `packet-63b-ib-fork2-contract` bound (`TxnDomainRejectionError` landed; 13 files GREEN); `bounds: []` + DISCHARGED note.
