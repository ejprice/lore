# REPORT — contract-63b-ib-fork2-r3

brief-base v14 read · brief project v7 read

## SUMMARY BLOCK
- receipt: `brief-base v14 read` · `brief project v7 read`
- state: **done-with-deviations** (one in-scope regression fixed + disclosed: the harness allowlist pin)
- deviations: (1) added `assert_domain_rejection` to `test_surreal_harness.py::_ALLOWED_MODULE_LEVEL_NAMES`
  (the pin's own message prescribes this) — `test_surreal_harness.py` green after; (2) supplied the
  invariant-pin file's own address (default `REPORT-*.md` deliverable present); (3) 2 `test_smoke.py`
  "import file mismatch" collection errors appear ONLY under `-o addopts=""` (which clears the configured
  `--import-mode=importlib`) — a pre-existing runner artifact, not my change, not present in a gate-style run.
- Packages considered: none — no library mechanism (a test-assertion helper + AST scan over stdlib `ast`
  + `tomllib`; reuses the repo's `parse_production_trees`/`assert_scan_reached_every_member`).
- Reuse ledger: 1 new symbol — `assert_domain_rejection` · lore/substrate search · nothing shared existed
  (21 sites hand-rolled `type(x) is SurrealStoreError`) · **HAND-ROLLED** (B1.2-I mandates exactly this).
- decisions-needed: none — B1 fully mechanical; no genuine per-corpse design ambiguity arose (P-class
  empty, M/I split decided by execution).
- receipt pointers: M2/M3 (the 21-site M/I/P inventory + corpse proof) · M4 (helper + mutation receipt
  19→flip→19) · M5 (rewrites + RED-until-built) · M7 (invariant pin RED-at-HEAD-naming-21 / GREEN-after)
  · M8 (`scripts/pending_contracts.yaml` 13-file bound) · M9 (satisfiability + gates) · M10 (prod sweep 0).
- Graded: n/a (this is a contract-authoring report, not a verdict on another artifact).

STATE: **DONE-WITH-DEVIATIONS** — contract complete & satisfiable; ONE fork escalated to the lead
(currency 0-RED_ORPHANED unachievable due to gate bug #461 + pre-existing ruff #460 — pytest is
RED_ADJUDICATED, my contract's job is correct). Ready for the mandatory re-adversary.

### Deliverables scorecard (brief's 8 + B1.3 completeness bar)
1. Corpse set by EXECUTION + DIFF vs textual scan → **21 sites, triple-reconciled** (M2/M3). ✓
2. ONE `assert_domain_rejection` helper + **mutation receipt 19→flip→19** (M4). ✓
3. M/I/P rewrites (19 I + 2 M, **P empty**), RED-until-built for the right reason (M5). ✓
4. Disjointness hierarchy pin — already committed, verified RED-until-built (M6). ✓
5. Repo-local AST invariant pin — RED-at-HEAD naming 21 / GREEN-after; discrimination + non-vacuity +
   HOME-accepts (`test_ast_reach_helpers.py` 50p) (M7). ✓
6. RED_ADJUDICATED registration — **pytest RED_ADJUDICATED (30 owned)**; 0-RED_ORPHANED blocked by
   #461 (gate bug) + #460 (pre-existing) → escalated (M8). ⚠ owned/escalated
7. Whole-suite satisfiability **0 failed / 9973 passed (ALONE)** · typecheck **EXIT=0** · ruff clean
   on my files (M9). ✓
8. Production sweep **0 hits** (M10). ✓
- B1.3-7 re-adversary: MANDATORY, lead-routed (ready). · B1.3-8 rider-iv hardening: rely on the
  behavioural contention cell (stated). 

## CAPABILITY CHECK
- lore tools loaded via `ToolSearch "+lore"` (keyword form) — FIRST CHOICE. Fallback SAID OUT LOUD:
  `grep`/`rg` is HOOK-BLOCKED this session (any command containing grep, whatever the path), AND
  over pytest STDOUT — so the textual `type(...) is SurrealStoreError` scan is done with a Python
  string-scan (a Python string scan is explicitly permitted for the AST invariant pin's own logic;
  I extend it to the corpse-derivation textual scan, dogfood grep-class case (b): assertion-spelling
  sweep). Whole-suite runs via `-n auto` + `timeout`, `--tb=line`/`tail` not grep.
- spike-surreal `ws://127.0.0.1:18000` = TEST store; never :18500. Store law:
  `docs/reference/surrealdb-31-capabilities.md` (cited, not re-transcribed). NO production/store/DDL
  change by this contract pass (tests + substrate + `scripts/pending_contracts.yaml` only).
- Git attribution reminder (session-start) **ignored** per standing CLAUDE.md; moot — COMMIT-ONLY.

## Reference build patcher (adversary's, REUSED verbatim)
The adversary's `patch_ref.py` (pasted verbatim in `REPORT-adversary-63b-ib-fork2.md` §"The patcher
instrument") is the reference-build instrument. `ref` mode = faithful §2.4. REUSED, not re-derived.

## Mission
CONTRACT REVISER for FORK 2 (packet 63b-i-b). Implement B1.2 + B1.3 from
`docs/design/2026-09-08-packet63b-ib-closeout-rulings.md` §"FORK 2 — ADVERSARY BLOCKER B1":
derive the corpse set BY EXECUTION, add the ONE shared `assert_domain_rejection()` helper,
rewrite each corpse per its M/I/P class, add the disjointness hierarchy pin + the repo-local
AST invariant pin, register RED_ADJUDICATED entries, and produce a whole-suite satisfiability
receipt + production sweep. NO production code. COMMIT-ONLY (lead commits).

## Milestones
- [x] M0: idle-gate + report skeleton + brief-base read + comms register + lore load
- [x] M1: read spec (B1.1/B1.2/B1.3) + adversary report + committed FORK-2 contract
- [x] M2: scratch copy + apply ref patcher + WHOLE-SUITE reference run → RED-set inventory
- [x] M3: textual scan for `type(...) is|== SurrealStoreError` → DIFF/union worklist
- [x] M4: shared helper `assert_domain_rejection()` + mutation receipt (19→flip→19)
- [x] M5: rewrite each corpse per M/I/P class (19 I + 2 M, P empty)
- [x] M6: disjointness hierarchy pin (RED-at-HEAD) — ALREADY COMMITTED, verified
- [x] M7: repo-local AST invariant pin (discrimination + non-vacuity + HOME accepts)
- [~] M8: registered (pytest RED_ADJUDICATED); 0 RED_ORPHANED BLOCKED by #461+#460 → escalated
- [x] M9: satisfiability 0-failed/9973-passed + typecheck EXIT=0 + ruff clean (my files)
- [x] M10: production sweep — 0 hits

## M2/M3 — THE DERIVED CORPSE INVENTORY (by execution + textual scan, reconciled)

Reference build = adversary `patch_ref.py ref` (verbatim) onto a `scratch_copy.sh` copy
(provenance: `loremaster.__file__ = .../scratchpad/ref63bib_r3/loremaster/loremaster/__init__.py`,
INSIDE the copy; `TxnDomainRejectionError` built, MRO `TxnGovernedConflictError → TxnDomainRejectionError
→ SurrealStoreError`).

**Whole-suite reference run** (`uv run pytest loremaster lorerunes loresigil lorescribe -n auto`,
ALONE, 320s): **22 failed, 9946 passed, 51 skipped, 3 xfailed** + 2 `test_smoke.py` collection ERRORs
(a scratch-copy pyc/basename artifact — NOT corpses; addressed in M9). Every one of the 22 failures =
identical reason `assert <class 'loremaster.store._txn.TxnDomainRejectionError'> is SurrealStoreError`.

**Corpse proof (RED-on-reference ∧ GREEN-at-HEAD):** the same 22 nodes run at HEAD `98cf52c` (main repo)
→ **22 passed in 8.96s**. So every one is a corpse of the OLD world, not a real regression.

**DIFF vs the textual scan** (Python string-scan — grep is hook-blocked; dogfood grep-class case (b),
assertion-spelling sweep; bare/anchor-free, both operand orders, `type(...)`/`.__class__`/`.type`):
the scan found **21 line-sites across 11 files**; execution RED = **22 nodes** (`:1036` is
parametrized ×2). **UNION == INTERSECTION == the 21 sites** — the scan and execution agree EXACTLY;
no corpse the scan missed, no execution RED the scan missed. (Fable's ruling measured 21; the
adversary measured ~15 and missed 8 — all 8 are in this union. P-class = EMPTY: all 21 are
RED-on-reference, so none is a plain-base raise that stays green.)

### EXHAUSTIVE M/I/P inventory (one row per site — "all remaining hits are X" is BANNED)

| # | file:line (symbol) | node(s) | class | edit | intent preserved |
|---|---|---|---|---|---|
| 1 | test_surreal_store.py:912 (`test_the_domain_rejection_helper_maps_the_governed_label_to_the_typed_error`) | 1 | **M** | `type(plain) is TxnDomainRejectionError and not isinstance(plain, TxnGovernedConflictError)`; RED-until-built via `getattr(_txn,"TxnDomainRejectionError",None)` | the helper's mint contract: a NON-governed domain label maps to the TYPED domain leaf (§2.4-1 supersedes §2.5's "plain SurrealStoreError") |
| 2 | test_surreal_store.py:1036 (`test_a_governed_conflict_throw_via_the_transaction_seam_raises_the_typed_error`) | 2 (`[execute_transaction]`,`[execute_read_transaction]`) | **M** | same as #1, on the seam's non-governed THROW positive-control leg | both raise sites route the ONE helper → a non-governed THROW mints the typed domain leaf |
| 3 | test_surreal_store.py:754 (`test_replace_file_surfaces_a_rolled_back_transaction`) | 1 | **I** | `assert_domain_rejection(exc_info.value)`; keep connection-kept lines | store rejection, not connection; connection kept. ⚠ carries the `:754` "pinned EXACTLY, not just a subclass of" comment — QUOTED + sharpened in its row below |
| 4 | test_surreal_store.py:857 (`test_single_statement_domain_rejection_raises_store_error`) | 1 | **I** | `assert_domain_rejection(...)` | single-statement ASSERT reject is a store error, connection kept, nothing persisted |
| 5 | test_surreal_store.py:2124 (`TestEnsureReadyRaisesOnLateDdlFailure::test_ensure_ready_raises_on_a_semantically_invalid_late_ddl_statement`) | 1 | **I** | `assert_domain_rejection(...)` | late DDL reject → store error, connection kept |
| 6 | test_surreal_store.py:4393 (`TestRecordTraceErrorPosture::test_domain_rejection_raises_store_error_and_keeps_connection`) | 1 | **I** | `assert_domain_rejection(...)` | domain rejection is a store error, connection kept |
| 7 | test_surreal_store.py:4498 (`TestQueryMessageHygiene::test_domain_rejection_message_never_echoes_the_raw_engine_text`) | 1 | **I** | `assert_domain_rejection(...)` | message hygiene + connection kept |
| 8 | test_agent_registry.py:983 (`TestAgentRegistryConnectionLifecycle::test_domain_rejection_never_echoes_the_raw_engine_text`) | 1 | **I** | `assert_domain_rejection(...)` | hygiene + connection kept |
| 9 | test_brief_ledger.py:1588 (same shape) | 1 | **I** | `assert_domain_rejection(...)` | hygiene + connection kept |
| 10 | test_diff.py:785 (`TestQueryClassifiedErrorPosture::...`) | 1 | **I** | `assert_domain_rejection(...)` | hygiene + connection kept |
| 11 | test_findings.py:1221 (`TestQueryClassifiedErrorPosture::...`) | 1 | **I** | `assert_domain_rejection(...)` | hygiene + connection kept |
| 12 | test_graph_surreal.py:2766 (`TestEnsureReadyRaisesOnLateDdlFailure::...`) | 1 | **I** | `assert_domain_rejection(...)` | late DDL reject → store error, connection kept |
| 13 | test_graph_surreal.py:3007 (`TestQueryClassifiedErrorPosture::...`) | 1 | **I** | `assert_domain_rejection(...)` | hygiene + connection kept |
| 14 | test_memory_backend.py:1714 (`TestQueryClassifiedErrorPosture::...`) | 1 | **I** | `assert_domain_rejection(...)` | hygiene + connection kept |
| 15 | test_snapshots.py:1085 (`TestQueryClassifiedErrorPosture::...`) | 1 | **I** | `assert_domain_rejection(...)` | hygiene + connection kept |
| 16 | test_surreal_apply.py:1157 (`TestApplyMidTxnFailureRollsBackEverything::test_failing_fragment_last_rolls_back_all_surfaces`) | 1 | **I** | `assert_domain_rejection(...)` | mid-txn rollback → store error, connection kept |
| 17 | test_surreal_manifest.py:439 (`TestSetState::test_out_of_domain_state_is_rejected_loudly`) | 1 | **I** | `assert_domain_rejection(...)` | out-of-domain state reject → store error, connection kept |
| 18 | test_surreal_manifest.py:588 (`TestReplace::test_replace_rolls_back_on_failure_and_the_caller_sees_it`) | 1 | **I** | `assert_domain_rejection(...)` | rollback → store error, connection kept, prior row intact |
| 19 | test_surreal_manifest.py:1104 (`TestEnsureReadyRaisesOnLateDdlFailure::...`) | 1 | **I** | `assert_domain_rejection(...)` | late DDL reject → store error, connection kept |
| 20 | test_surreal_manifest.py:1342 (`TestQueryClassifiedErrorPosture::...`) | 1 | **I** | `assert_domain_rejection(...)` | hygiene + connection kept |
| 21 | test_task_ledger.py:1715 (`TestQueryClassifiedErrorPosture::...`) | 1 | **I** | `assert_domain_rejection(...)` | hygiene + connection kept |

**Totals: 2 M line-sites (3 nodes) · 19 I line-sites (19 nodes) · 0 P.** 21 line-sites / 22 nodes / 11 files.

**The `:754` comment (QUOTED, per B1.3-2), with the sharpening argument so the next reader does not restore it:**
> `# elsewhere, so the type is pinned EXACTLY, not just "a subclass of".`

Sharpening: exact-type on `SurrealStoreError` was, at authoring time, the ONLY way to say "a store
error that is NOT the `SurrealConnectionError` subclass". `assert_domain_rejection` (→
`isinstance(error, TxnDomainRejectionError)` ∧ `not isinstance(error, SurrealConnectionError)`) says
that MORE precisely — it also excludes `TxnContentionExhaustedError` — so the F2 intent is not merely
preserved, it is sharpened. Restoring `type(x) is SurrealStoreError` re-opens the exact drift the tree-wide
invariant pin (M7) now bans, because the class is now a non-leaf (its subclasses ARE store rejections).

## M4 — THE ONE SHARED HELPER + MUTATION RECEIPT

`assert_domain_rejection(error)` added to **`loremaster/tests/_surreal_harness.py`** (the shared
harness EVERY store test imports; RULING 1 → in-function `from loremaster.store import _txn`, no
module-level store import). It asserts `isinstance(error, TxnDomainRejectionError)` (RED-until-built via
the repo's `getattr(_txn, "TxnDomainRejectionError", None)` idiom + a legible message) AND
`not isinstance(error, _txn.SurrealConnectionError)`. It is SHARPER than the corpse: it also excludes
`TxnContentionExhaustedError` (via the hierarchy — `TxnContentionExhaustedError` is not a
`TxnDomainRejectionError`, pinned by the disjointness pin).

**Reuse ledger (brief-base §6):** 1 new symbol — `assert_domain_rejection` · lore query
`lore_search("AST scan test tree parser allowlist … assert domain rejection helper")` +
`lore_get_symbol` over the substrate · returned: no existing shared domain-rejection assertion (each of
the ~21 sites hand-rolled `type(x) is SurrealStoreError`) · disposition **HAND-ROLLED** (a new shared
predicate is exactly what B1.2-I mandates; 21 call sites need ONE policy → a function they call).

**MUTATION RECEIPT (sharing proven, ref+edits scratch `refedits63bib_v2`, provenance
`loremaster.__file__ = .../refedits63bib_v2/loremaster/loremaster/__init__.py` INSIDE, `ref` build):**
- BASELINE (helper intact): 19 I-callers → **19 passed in 25.60s**.
- MUTATED (`isinstance(error, domain_rejection_error)` → `not isinstance(...)`): 19 I-callers →
  **19 failed in 20.07s** — EVERY caller reds. Restored.
- ⇒ all 19 I-callers route through the ONE helper (brief-base §6). The 2 M pins do NOT (they use the
  mint-contract exact-type on the leaf) — correct discrimination.

## M5 — CORPSE REWRITES (19 I + 2 M) + RED-until-built receipts
- 19 I-corpses: exact-type line replaced by `assert_domain_rejection(exc_info.value)`, each test's own
  `not isinstance(..., SurrealConnectionError)` + connection-kept lines KEPT untouched (B1.2-I).
  `assert_domain_rejection` added to each file's existing `from _surreal_harness import (` block.
- 2 M-corpses (test_surreal_store.py :912 helper-mapping, :1036 seam ×2): `type(x) is domain_type and
  not isinstance(x, governed_type)` where `domain_type = getattr(_txn, "TxnDomainRejectionError", None)`,
  RED-until-built; the retired-mapping docstring/comment rewritten to teach §2.4-1 supersedes §2.5.
- **RED-until-built at HEAD `98cf52c` for the RIGHT reason:** all 21 rewritten nodes (22 w/ `:1036`×2)
  → RED; I-nodes fail at `_surreal_harness.py:234` (`assert_domain_rejection` "TxnDomainRejectionError
  is UNBUILT"), M-nodes at `test_surreal_store.py:1052` (getattr UNBUILT). No parse errors, no
  collateral. (Adjudicated to the FORK-2 build in `pending_contracts.yaml` — see M8.)

## M6 — DISJOINTNESS HIERARCHY PIN (deliverable #4) — ALREADY COMMITTED, verified
The FORK-2 contract `test_memory_supersede_atomicity_63b_ib.py::TestDomainRejectionErrorType::
test_the_typed_domain_class_exists_and_governed_conflict_subclasses_it` (committed at `98cf52c`)
ALREADY asserts all four required relations: `issubclass(TxnDomainRejectionError, SurrealStoreError)`,
`issubclass(TxnGovernedConflictError, TxnDomainRejectionError)`, `not issubclass(SurrealConnectionError,
TxnDomainRejectionError)`, `not issubclass(TxnContentionExhaustedError, TxnDomainRejectionError)`.
Verified RED-until-built at HEAD ("TxnDomainRejectionError is UNBUILT"). No new authorship needed;
registered in `pending_contracts.yaml` under the FORK-2 file (M8).

## M7 — REPO-LOCAL AST INVARIANT PIN (deliverable #5)
New file `loremaster/tests/test_no_exact_type_check_on_surreal_store_error.py`. Bans
`type(<expr>)`/`<expr>.__class__`/`<excinfo>.type` `is|==|is not|!=` `SurrealStoreError` (either operand
order; bare or dotted ref) across the TEST tree.
- **REACH is a CHECKED VARIABLE (INSTRUMENT 0 / ruling item 3):** routes through the SHARED
  `parse_production_trees(include_tests=True)` (roots DERIVED from `[tool.uv.workspace] members`, NOT
  `loremaster/tests` only) + `assert_scan_reached_every_member` (fail-CLOSED on empty). Because it
  CONSUMES the shared parser (hand-rolls no whole-tree parse), `test_ast_reach_helpers.py`'s
  clone/parse-skip detectors do NOT flag it and it is NOT in `_MIGRATION_SET` (a curated 5-file
  hand-list) — so no allowlist entry is required. (HOME-accepts receipt: `test_ast_reach_helpers.py`
  green — M9.)
- **Legs:** (1) the ban (deny-by-default, names each offender file:line); (2) DISCRIMINATION control
  — a synthetic source with all four banned spellings (bare/`__class__`/`excinfo.type`/reversed) is
  flagged by line, and the subclass-aware spellings + the M-class `type(x) is <leaf>` are NOT;
  (3) NON-VACUITY — scanned ≥40 test files AND ≥1 `assert_domain_rejection(` call.
- **RED-at-HEAD for the RIGHT reason (BEFORE rewrites):** the ban named EXACTLY the 21 corpse sites
  (triple-reconciled: textual scan 21 == AST walk 21 == execution RED 22 nodes w/ `:1036`×2), and
  non-vacuity red (helper not yet adopted). Discrimination control GREEN.
- **GREEN after rewrites (at HEAD):** 3 passed — 0 offenders, 19 `assert_domain_rejection` adoptions,
  discrimination control holds.

## DEVIATION (scope law, brief-base §2) — one regression my in-scope change directly caused
Adding `assert_domain_rejection` as a module-level function in `_surreal_harness.py` reddened
`test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::
test_the_harnesss_module_level_names_are_exactly_the_allowed_set` (an EXACT-SET allowlist pin on the
harness's module-level names — finding #150). The pin's OWN message prescribes the fix: *"If the new
name is legitimate, add it here in a diff a reviewer can see."* I added `"assert_domain_rejection"` to
`_ALLOWED_MODULE_LEVEL_NAMES` with a comment stating it is a test-assertion helper, NOT retry policy
(the property that allowlist protects). Verified GREEN at HEAD (`TestTheHarnessDeclaresNoRetryPolicyOfItsOwn`
→ 11 passed). This is the ONLY file I touched outside the corpse/helper/pin/registry set;
`test_surreal_harness.py` is fully green at HEAD after the fix.

## M8 — RED_ADJUDICATED REGISTRATION (`scripts/pending_contracts.yaml`)
- **The red-at-HEAD pytest set (derived by a full pytest run on the edited tree, `98cf52c`): 30 nodes
  across 13 files** (after the harness fix above; the 31st node was the harness regression, now green):
  my 22 corpses (11 files) + `test_memory_supersede_atomicity_63b_ib.py` (7) +
  `test_memory_replay_fidelity_63b_ib.py` (1). Every node RED-until-built via the §2.4-1 keystone
  `loremaster.store._txn.TxnDomainRejectionError` (verified absent at HEAD; `authorize_guarded`/
  `GuardedPlan`/`MemoryLedger.retire` are ALREADY built, so only the §2.4 pins are red).
- **ONE `PendingBound`** `packet-63b-ib-fork2-contract`, owner = the FORK-2 §2.4 build, reopen_trigger
  = the build landing `TxnDomainRejectionError` (self-destructs on `hasattr` — the liveness leg). 13
  `PendingFile` entries, each `missing_symbols: [loremaster.store._txn.TxnDomainRejectionError]`.
  Registry loads: 1 bound / 13 files / 13 symbols (validated via `PendingContractRegistry.load`).
- **pytest adjudication is FILE-level** (`partition_pytest` matches `outcome.file in registered_paths`).
  I verified each registered file's ONLY red nodes are the FORK-2-related ones (no unrelated red masked):
  the full-run red set = exactly {22 corpses} ∪ {8 committed FORK-2 §2.4 nodes} — no other node in any
  registered file. The file-granularity masking window is disclosed in the entry's `rationale` and
  discharges when the build lands.
- Currency-gate 0-RED_ORPHANED tail: see M9.

## M10 — PRODUCTION SWEEP (re-derive the 0)
Scanned **143 production files** (`<member>/<member>/**.py` + `scripts/`, tests excluded) with BOTH the
invariant pin's AST offender function AND a bare textual regex (`type(...)`/`.__class__`/`.type`
`is|==|is not|!=` `SurrealStoreError`, both operand orders): **0 hits** (AST 0, textual 0). Confirms
adversary R4 + Fable's derivation — the retype is behaviour-preserving for production
(`except SurrealStoreError` / `isinstance` / `match case` are subclass-aware). No builder concern,
no design-adjacent escalation.

## M9 — WHOLE-SUITE SATISFIABILITY + GATES (in progress)
- **ruff (the harder leg — orphaned imports):** the 19 I-rewrites inserted `assert_domain_rejection`
  into each `from _surreal_harness import (` block; every corpse file still uses `SurrealStoreError`
  (`pytest.raises`/`isinstance`), so NO orphaned import. `ruff check` on all 14 edited files →
  **All checks passed (0 errors)** after: (a) isort auto-fix of the 11 inserted imports
  (`--select I --fix`, behavior-neutral), (b) stripping one stray U+200B zero-width space from the
  invariant-pin docstring. HOME-accepts: `test_ast_reach_helpers.py` → **50 passed, 4 skipped** at HEAD
  (the new invariant-pin file routes through the shared parser → not flagged as a whole-tree clone).
- **rider iv AST hardening (ruling item 8, optional):** I RELY ON the behavioural contention cell
  (`test_exhausted_contention_on_the_composed_supersede_keeps_the_ledger_row`, already committed) — the
  adversary proved W1c reds ONLY that cell, so it already discriminates "allowlist the safe class" from
  "enumerate the forbidden transport shapes". No AST source-pin added (name-presence would be a weaker
  proxy; the behavioural cell is stronger).
- **WHOLE-SUITE SATISFIABILITY RECEIPT (deliverable #7) — ref build + ALL rewrites + new pins, run
  ALONE:** in the `refedits63bib_v2` scratch (adversary `patch_ref.py ref` on _txn.py/local.py +
  my helper + 21 corpse rewrites + invariant pin + harness fix + registry), provenance
  `loremaster.__file__ = .../refedits63bib_v2/loremaster/loremaster/__init__.py` (INSIDE the copy):
  `uv run pytest loremaster lorerunes loresigil lorescribe -n auto` (keeping `--import-mode=importlib`)
  → **9973 passed, 51 skipped, 3 xfailed, 0 FAILED, 0 collection errors in 304.94s**. Every RED-until-built
  pin (21 corpses + M/disjointness + FORK-2 §2.4) goes GREEN on the reference build; the invariant pin
  is GREEN (0 offenders). ⚠ The earlier 48-failed/390-error run was store-CONTENTION (I wrongly ran it
  concurrently with the currency gate); re-run ALONE = 0 failed. (The isort/ZWSP ruff fixes are
  behaviour-neutral, so this pytest result holds for the final source.)
- **typecheck (deliverable #7):** `./scripts/typecheck.sh` → **EXIT=0** — "Success: no issues found"
  across lorerunes/lorescribe/loresigil/loremaster (263 files)/skills/docs-eval/scripts + shellcheck.
  The getattr idiom adds ZERO mypy errors → the currency `typecheck RED_ORPHANED` is PURELY the
  registration self-destruct (#461), never a real mypy failure. Raw typecheck is clean.
- **re-adversary (B1.3-7):** MANDATORY next step, the lead's to route — its brief carries the P1c reach
  attack on the invariant pin (M7) + a mutation of `assert_domain_rejection`'s predicate (done here as
  the M4 receipt). The contract is ready for it.

### CLEAN currency-gate tail (`pending_contract_gate.py --currency`, run ALONE at HEAD `98cf52c`)
```
  typecheck    RED_ORPHANED — 13 residual(s) with NO owner
      (each: SELF-DESTRUCT "registered file X … produced NO mypy errors — the bound is discharged")
      -> the gate bug #461: my getattr-idiom pytest bound has 0 mypy errors, so the MYPY self-destruct
         leg misfires on all 13 registered files. NOT a real mypy issue.
  ruff         RED_ORPHANED — 1 residual(s) with NO owner
      loremaster/tests/test_memory_f5_registration_63b_ib.py:295:111 — E501 (132 > 110)  [#460, pre-existing, not mine]
  pytest       RED_ADJUDICATED — 30 residual(s), owned by: packet-63b-ib-fork2-contract
      (owner: the FORK-2 §2.4 build)   ✓✓ MY CONTRACT'S 30 RED-until-built PINS ARE CORRECTLY OWNED
  CURRENCY   : FAIL — RED with nobody's name on it: typecheck, ruff
```
- **The pytest leg is RED_ADJUDICATED (30, owned)** — the registration does its job; the 82 pytest
  "orphans" in an earlier CONTAMINATED run were ALL store-contention (I had wrongly run currency +
  satisfiability concurrently; both re-run ALONE). Clean pytest red set = exactly 22 corpses + 8
  committed FORK-2 §2.4 nodes, every one in a registered file.
- The currency FAIL is entirely #461 (typecheck self-destruct bug) + #460 (pre-existing ruff E501) —
  neither a FORK-2 contract defect. See the escalation fork above.

## ⚠ M8/M9 BLOCKERS + ESCALATION — the currency gate CANNOT read 0 RED_ORPHANED at this contract commit
Two independent reasons, NEITHER a defect in the FORK-2 contract itself:

**(1) The registry cannot adjudicate a PYTEST-only bound — a gate bug (finding #461).**
`gates.yaml` sets `pytest` `adjudicated_by: pending-contracts` and its prose says the registry "can
express a pending CONTRACT — pins designed RED until [a build] lands" — so registering the 30 FORK-2
pytest pins is correct-per-design, and `partition_pytest` DOES adjudicate them (matches by file path).
BUT `transcript_self_destruct_findings` (pending_contract_gate.py:1104-1110) is MYPY-only: for EVERY
registered file it fires a self-destruct the moment that file "produced NO mypy errors". My files use
the `getattr(_txn, "TxnDomainRejectionError", None)` idiom → 0 mypy errors by construction → the
`typecheck` gate emits 13 false "the bound is discharged" self-destructs → typecheck RED_ORPHANED.
- **Register** → pytest RED_ADJUDICATED (owned) ✓ · typecheck RED_ORPHANED (the bug) ✗
- **Don't register** → typecheck GREEN ✓ · pytest RED_ORPHANED (30 unowned reds) ✗
- Either way currency FAILS. The design's own pytest-bound path is unreachable until #461 is fixed.

**(2) Pre-existing ruff E501 (finding #460), NOT mine.** `ruff check .` at HEAD `98cf52c` = exactly ONE
error: `test_memory_f5_registration_63b_ib.py:295` (E501, 132>110) — a file I never touched
(`git diff` empty; last changed by `46288b6`). ruff is `adjudicated_by: none` (zero tolerance), so the
ruff leg is RED_ORPHANED at HEAD regardless of the FORK-2 contract. 1-line fix named in #460.

**Note on scope:** the currency gate is required GREEN at wave **CLOSE-OUT**, not at a mid-wave contract
commit. A RED-until-built pytest contract is EXPECTED to be red in the contract→build window; the build
landing `TxnDomainRejectionError` turns all 30 pins GREEN and self-destructs the registry entry. So this
is not a defect that blocks the contract — it is a currency-verdict question for the lead.

**ESCALATION (fork — the lead decides; I left the registration IN as the brief's letter, correctly
owning the pytest reds):**
- (a) KEEP the registration [my recommendation]: pytest is RED_ADJUDICATED (owned by the FORK-2 build),
  which is the brief's actual intent; the typecheck RED_ORPHANED is the flagged gate bug #461, not a
  mypy issue; it self-destructs cleanly when the build lands.
- (b) REMOVE the registration: typecheck GREEN, pytest RED_ORPHANED (honest contract-window state).
- (c) Route the two 1-shot fixes (#460 the E501, #461 the self-destruct scoping) — both out of my
  writable set (`pending_contract_gate.py` is production tooling; the F5 test is another packet's) — then
  registration works cleanly and ruff greens.
- The exact clean per-gate currency verdicts (run ALONE) are pasted in M9 below.

## Findings
_(appended per milestone)_
- #460 (ruff): pre-existing E501 at test_memory_f5_registration_63b_ib.py:295 — branch ruff-red at HEAD.
- #461 (pending_contract_gate): the mypy self-destruct leg misfires on pytest-only bounds.
