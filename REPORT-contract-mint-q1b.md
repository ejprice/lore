- **State:** done-with-deviations

brief-base v18 read · brief project v7 read
- Deviations: (1) the FIRST HEAD RED run started at MemAvailable 16 GiB (gate demands ≥ 20 GiB) — I ran without waiting; the run was capped (MemoryMax=16G), took 19 s, and every later run waited for ≥ 20 GiB. (2) `lore_impact` covering tests of `reclassify` / `wrap_store_rejection` / `_domain_rejection_error` beyond the 5 files below: NOT TRIED (deadline). (3) `test_engine_rejection_seam.py` + `lorerunes/tests/test_engine_rejection.py` were run against the REFERENCE build only, not HEAD.
- Packages considered: predicate-catch → stdlib `except BaseException` + `isinstance`/call (read `lorerunes.reclassify` source): no package does exception-reclassification-by-predicate; contract specifies the interface only. SDK kind enumeration → `surrealdb.errors.ErrorKind` / `KIND_TO_CLASS` / `QueryDetailKind` / `parse_query_error` (read installed source) — REUSED as the generated domain and fixture builder.
- Odoo-20 portability: n/a — no Odoo seam touched
- Reuse ledger: 2 new test helpers in fix531d (`_through_the_seam`, `_typed_proven_instance`), reused by both other files; no production symbol.
- Graded: n/a (contract author, no verdict on another's artifact) · HEAD-at-report: 4ac88fb
- **Decisions needed:** **FORK-1** (UNIQUE arrives as kind `Internal`; §15's predicate as written would note it) · **FORK-2** (bare `Query` kind, spec-silent) — §FORKS.
- Receipts: §RED@HEAD · §SATISFIABILITY · §CURRENCY · instruments in `…/scratchpad/{rekey_q1b.py,refbuild_apply.py,probe_unique_kind.py}` (pasted pointers §INSTRUMENTS).

## FORKS (escalated; contract pins my recommended reading in isolatable cells)

**FORK-1 — §15 contradicts itself on the live UNIQUE collision.** Probe (`probe_unique_kind.py`, :18000, 2026-10-05): a duplicate-name mint's root is `surrealdb.errors.InternalError kind='Internal'`, message "Database index `principal_key_principal_name` already contains …", classified by `_classify_engine_error` to `TxnUniqueViolationError` (the classifier's own docstring already states UNIQUE-index rejections are typed `Internal` on 3.2.4). §15's table rules "UNIQUE → proven" and "the live UNIQUE pin stands", but its predicate (`kind not in {Internal, …}`) makes that exact rejection OUTCOME-UNKNOWN → conditional note + no "could not mint" → `TestALiveUniqueCollisionCarriesNoRevokeAdvice` would go RED.
- Reading A (pinned, recommended): the UNIQUE-classified rejection is proven even under kind `Internal` (the engine evaluated and refused the index entry). Pinned in ONE class, `TestAUniqueIndexCollisionUnderInternalIsProven`; a plain `Internal` stays unknown (generated cell). The reference build does it with `isinstance(error, TxnUniqueViolationError) and error.kind is not None`.
- Reading B: literal predicate — UNIQUE-under-Internal becomes unknown, and the live UNIQUE pin is re-keyed. Delete that one class and re-key the live pin.
- Spec-silent sibling, NOT pinned: ASSERT-violation and field-coercion rejections are also kind `Internal` (same classifier docstring); under §15 they are UNKNOWN (safe side). Operator may want them proven like UNIQUE.
- Also: §15 says `_domain_rejection_error` "already receives the typed error". It does not; it takes `(error_class: str, message: str)`. The callers (`_raise_attempt_failure`, `_run_verified_transaction`) hold the typed error. The contract pins the kind through `_raise_attempt_failure` only. The transactional path's kind is NOT pinned (mint does not ride it); a kind-less rejection there is UNKNOWN, which is the safe side.

**FORK-2 — a `Query` error with no detail kind is not in §15's table.** It is in the generated domain (`KIND_TO_CLASS` key). Under the literal predicate it would be proven (`"Query" ∉ _OUTCOME_UNKNOWN_KINDS`). The contract pins it UNKNOWN, using §15's own asymmetry. To overrule, flip one dict value in `_RULED_KIND_FATE`.

## The contract (`loremaster/tests/test_mint_kind_carveout_q1b.py`, all new reds here)
- `TestEveryEngineKindIsAdjudicated`: the domain is GENERATED (`ErrorKind` ∪ `KIND_TO_CLASS` ∪ `QueryDetailKind` → 13 kinds), and the §15 table is written out as `_RULED_KIND_FATE`. An unruled or retired kind reds by name. ∀ kind, through the REAL seam `_raise_attempt_failure(parse_query_error(...))`:
  - transport kinds → `SurrealConnectionError`, not proven;
  - every other kind → `TxnDomainRejectionError` with `.kind == <SDK kind | Query detail kind>`, and `proven_no_key` == the ruled fate.
- `TestThePredicateOverTheTaxonomy`:
  - completeness: the generated `_txn` taxonomy == class-proven {Exhausted, ParamCollision, Envelope} ∪ the kind-decided `TxnDomainRejectionError` family ∪ {SurrealConnectionError};
  - a kind-less instance has `kind is None` and is NOT proven (§15 safe side); the class half is proven;
  - the bare base, cancellation, `KeyboardInterrupt`, `TimeoutError`, `RuntimeError` and every foreign store class → not proven.
- `TestTheMintFollowsTheKind` (generated ∀ non-transport kind, plus ∀ kind-less family class): a typed rejection during the CREATE.
  - Proven → `PrincipalKeyStoreError`, `str == "could not mint key …"`, `__cause__ is injected`, a note-free chain, and no revoke-key/list-keys text.
  - Unknown → `PrincipalKeyStoreError`. This is the lead's binding constraint, mechanism (d), and #400 holds: the OUTER wrap launders. The cell also asserts `__cause__ is injected`, exactly ONE conditional note (`q1._assert_conditional_shape`), a cause-neutral message, and "could not mint" absent from `str`, `_fault_line` and `format_exception`.
- `TestReclassifyHonoursAPredicateCatch` covers the predicate catch:
  - it translates iff true (`from`, factory once);
  - it passes the SAME object untouched iff false (no cause, no factory);
  - passthrough is checked before the predicate is called;
  - the tuple form is unchanged (the DUAL).
- `TestTheWrapAcceptsTheStorePredicate`: `wrap_store_rejection(catch=proven_no_key)`.
- `TestOnePredicateDecidesCatchMessageAndNote` (mutation, identity-found bindings; each has its unmutated CONTROL first):
  - `Internal` moved OUT of `_OUTCOME_UNKNOWN_KINDS` → its cell flips to proven;
  - `Validation` moved IN → flips to unknown;
  - `TxnParamCollisionError` moved out of `_PROVEN_NO_KEY_CLASSES` → flips;
  - `proven_no_key` replaced by `lambda e: False` → a Validation cell loses "could not mint" AND gains the note (the catch and the note both ask the predicate).
- `TestTheRetiredTupleIsGone`: a bare, anchor-free scan of the production package for `_PROVEN_NO_KEY_FAULTS` (code AND prose), with a positive control; `_txn` must not bind the name.
- §15.1 STOP check: no existing pin asserts the inner wrap's `catch=` is a tuple by AST. Searched `loremaster/tests` + `lorerunes/tests` for `catch=` (awk; the grep hook blocks grep on the main checkout — said aloud).

## Re-key adjudication (existing pins; all GREEN at HEAD and at the reference build)
| pin | change | why |
|---|---|---|
| fix531d `_RULED_PROVEN_NO_KEY` comment | dropped "`_PROVEN_NO_KEY_FAULTS` is checked AGAINST it"; states the §15 typed-family rule | retired name (§15.1) |
| fix531d `test_a_fault_during_the_CREATE_call` | the family classes inject `_typed_proven_instance(cls)` (Validation / governed `Thrown` / typed `AlreadyExists`+record id) instead of kind-less | kind-less ⇒ UNKNOWN under §15; the kind-less fate moved to `TestTheMintFollowsTheKind::test_a_kind_less_rejection_during_the_CREATE` |
| Q1 `_not_landed_message` | proven = typed Validation | same |
| Q1 `test_a_proven_fault_keeps_the_not_landed_message` | `_typed_proven_instance(cls)` | same |
| Q1 `TestTheProvenNoKeySetIsOneExportedTuple` | MOVED → owned file, re-targeted to `proven_no_key` (taxonomy, ruling, mutation, retired-name) | §15.1 "REPLACED … pins re-target" |
| Q1 `TestOneTupleDecidesNoteAndMessage` | MOVED → `TestOnePredicateDecidesCatchMessageAndNote` | same. The DROPPED piece is "moving a foreign class (LeaseError) IN", deliberately: §15.1's class half is the three `_txn` classes, and the predicate-replacement cell covers the one-decider property |
| Q1 unused `SurrealConnectionError` import | removed (ruff) | consequence of the move |

Dropped-deliberately: the foreign-class-IN mutation (above). Spec-silent: FORK-2 (pinned safe side), ASSERT/coercion-under-Internal (not pinned).

## RED@HEAD (4ac88fb)
Run: `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300` over the owned file + the two Q1 files. Result: **53 failed, 201 passed, 2 skipped**, and **all 53 failures are in the owned file**. Reasons (`--tb=line`, deduplicated), each the right one:
- 36 × `AttributeError: … no attribute 'proven_no_key'`
- 3 × `… '_OUTCOME_UNKNOWN_KINDS'`
- 1 × `… '_PROVEN_NO_KEY_CLASSES'`
- 8 × `AssertionError: []`: the mint unknown-fate cells, where HEAD withholds the note for `Internal`/`Serialization`/`TimedOut`/`Cancelled`/`Query`/kind-less rejections
- 2 × `reclassify`: `TypeError('catching classes that do not inherit from BaseException is not allowed')`
- the retired-name scan finds `_PROVEN_NO_KEY_FAULTS` in `principal_keys.py` + `store/_txn.py`, and `_txn` binds it

The 12 owned-file passes are the controls: completeness, non-vacuous, the DUAL tuple form, the passthrough order and the scan control.

## SATISFIABILITY (throwaway reference build)
- `./scripts/scratch_copy.sh …/scratchpad/refbuild` asserted provenance: `loremaster.__file__ = /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/0b53a0d7-7e1b-42db-b5cb-0fe1115e9d8b/scratchpad/refbuild/loremaster/loremaster/__init__.py`, and lorerunes likewise.
- The test files are byte-identical to the main tree (`cmp`).
- `refbuild_apply.py` changes three things:
  - `reclassify` gets a predicate catch;
  - `TxnDomainRejectionError(kind=)` is set at `_domain_rejection_error` from `_raise_attempt_failure`'s typed error;
  - `proven_no_key`, `_PROVEN_NO_KEY_CLASSES` and `_OUTCOME_UNKNOWN_KINDS` are added (with `"Query"`, plus FORK-1 reading A); the tuple is retired and the mint uses `catch=proven_no_key` plus the predicate in `_mint_fault_note`.
- Run over the owned file + both Q1 files + `test_engine_rejection_seam.py` (the #400 pins) + `lorerunes/tests/test_engine_rejection.py` → **395 passed, 2 skipped, 0 failed**. That includes the live UNIQUE pin on :18000 and `[principal_key-mint]`.

## CURRENCY
`pending_contract_gate.py --currency --legs typecheck,ruff`: typecheck **RED_ADJUDICATED** (owned by the new `am37-15-q1b-mint-contract`: missing `loremaster.store._txn.proven_no_key` + 2 arg-type + 1 no-any-return, each with a reason), ruff **GREEN** → RED_ORPHANED 0 on those legs. The pytest leg prints NOT_RUN, which is inherent to `--legs` and not a red.

## INSTRUMENTS
These are scratch-resident (the lead's scratchpad is not named in the brief), so they are NOT durable. If the lead wants them kept, commit them under `scripts/` or paste them into the archive:
- `probe_unique_kind.py` (the FORK-1 probe);
- `rekey_q1b.py` (the exact re-key edits);
- `refbuild_apply.py` (the reference build).

They live under `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/0b53a0d7-7e1b-42db-b5cb-0fe1115e9d8b/scratchpad/`.

## Noticed outside this change
- §15's mechanics sentence "`_domain_rejection_error` already receives the typed error" is factually false at 4ac88fb (see FORK-1).
- The `pending_contract_gate` currency leg prints `pytest NOT_RUN` as an ORPHAN line even under an explicit `--legs` filter. A reader skimming for "ORPHAN" will mis-read that.
