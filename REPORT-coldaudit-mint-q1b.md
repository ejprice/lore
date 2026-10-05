brief-base v18 read · brief project v7 read

# REPORT — coldaudit-mint-q1b (cold REFUTE audit of the am-37 §15/§15.1/§15.2 "Q1b" build)

## SUMMARY
- **Verdict: GO-with-residuals.** The build conforms to §15/§15.1/§15.2. All 6 of my mutations held EXACTLY (0 survivors). The full suite gives **CURRENCY PASS**: 13355 passed / 530 failed / 70 skipped, and every red is owned by packet-58 / packet-64b-i. **The 530 failure ids are identical at HEAD and at the build** (0 moved either way). Tree byte-identical at start and end.
- **State:** see the last line. **Deviations:**
  - (1) I started the owned-file HEAD re-run at MemAvailable 19.47 GiB, just under the 20 GiB gate. It ran clean under its 16G cap.
  - (2) `grep`/`rg` are hook-blocked everywhere, including scratch, so exhaustiveness used Python AST scans (said out loud in §Capability).
- **Packages considered:** none — no mechanism specified (audit). **Odoo-20 portability:** n/a — no Odoo seam touched. **Reuse ledger:** none (no new symbols).
- **Graded:** `ad2c9c9` + the uncommitted 6-file build (patch md5 `476827a2…`) · HEAD-at-report: `ad2c9c9` · SAME.
- **Decisions needed:**
  - (a) **R-1 (MEDIUM, sidecar/operator ruling):** `proven_no_key`'s kind half enumerates the UNKNOWN kinds. Any engine kind the installed SDK does not enumerate is therefore served as "could not mint key …" with NO revoke note. Probed: kind `Transaction` and Query detail `Aborted` both give TRUE. The engine is on the floating `v3.2` tag (#336). The build is spec-conformant (§15.2: "other kinds TRUE"). Recommended fix: invert to an allowlist `_PROVEN_KINDS` (§6 R-1).
  - (b) R-2 (process): the implementer edited the contract file without an operator grant. The edit is inert and was disclosed.
- **Pointers:** §1 inventory + diff · §2 conformance + test-edit check · §3 mutation table · §4 trust · §5 census · §6 findings R-1..R-4 · §7 md5s · §8 instruments (verbatim).

## Body (measured 2026-10-05 against HEAD `ad2c9c9` + the uncommitted 6-file build)

### Capability check
- `grep`/`rg` on any path are blocked by a PreToolUse hook (it also blocked `rg` inside my scratch copy). I used lore
  (`lore_impact`), `sed`/`awk` and Python AST scans instead. Construction-site and call-site exhaustiveness
  (§Inventory) used an AST scan, which is the CLAUDE.md fallback case (a). I am saying so here.
- Everything else the brief demanded was available.

### §1 Contract-blind inventory (written from the diff BEFORE reading the spec/reports), then diffed

**Fates under the build: every fault that can reach `PrincipalKeyStore.mint`'s CREATE.** "Inner" is the
`catch=proven_no_key` wrap; "outer" is the default-catch wrap (#400).

| fault reaching the CREATE | inner wrap | outer wrap | served class / message | note |
|---|---|---|---|---|
| `TxnDomainRejectionError` with a RECOGNISED `error_class` (UNIQUE / ASSERT / coercion / governed / recursion-depth / retryable-conflict label), any kind incl. `None` | translates | — (not a store error any more) | `PrincipalKeyStoreError` "could not mint key …" | none |
| `TxnUniqueViolationError` / `TxnGovernedConflictError` built kind-less | translates (classified by construction) | — | "could not mint key …" | none |
| unspecified `TxnDomainRejectionError`, kind ∈ {Validation, Thrown, AlreadyExists, NotFound, Configuration, NotExecuted} | translates | — | "could not mint key …" | none |
| unspecified `TxnDomainRejectionError`, kind ∈ {Internal, Serialization, Query (no detail), TimedOut, Cancelled} or `None` | passes UNTOUCHED (bare `raise`) | translates | `PrincipalKeyStoreError`, outcome-unknown message | CONDITIONAL |
| **unspecified `TxnDomainRejectionError`, kind NOT enumerated by the installed SDK** (e.g. a future engine kind) | **translates** | — | **"could not mint key …"** | **none** ← finding R-1 |
| `TxnParamCollisionError` / `TxnEnvelopeViolationError` (pre-send) | translates | — | "could not mint key …" | none |
| `TxnContentionExhaustedError` | passthrough (raw) | passthrough | raw | none (class half) |
| `SurrealConnectionError` | passthrough | passthrough | raw | CONDITIONAL (connection wording) |
| bare `SurrealStoreError`, a foreign `SurrealStoreError` subclass | passes untouched | translates | outcome-unknown | CONDITIONAL |
| `CancelledError`, `KeyboardInterrupt`, `TimeoutError`, any non-store exception | passes untouched | passes untouched | raw | CONDITIONAL |
| CREATE answered, no row | — | — | "the mint answered no row" | CERTAIN |

**`reclassify` / `wrap_store_rejection` callers (AST scan of `loremaster/loremaster`, measured at the build):**
`wrap_store_rejection` has 18 call sites: 17 default-catch (audit 1, keeps 8, principals 6, principal_keys 2 = the
mint's OUTER wrap + `revoke`) and exactly 1 `catch=`, the mint's inner wrap. `reclassify` has 1 production caller,
`wrap_store_rejection`. Rejection classes are constructed in production ONLY inside `_domain_rejection_error` (3
calls, all passing `error_class=` and `kind=`). There are no production subclasses beyond the two in `_txn`.

**Removed-behavior inventory (mine):**
1. `_PROVEN_NO_KEY_FAULTS` (a class tuple that held the whole `TxnDomainRejectionError` family) is deleted, so every
   domain rejection used to be "proven". Now only classified rejections and timing-proving kinds are. **Dropped
   deliberately** (§15 R-1).
2. `reclassify`: `except catch as error` became `except BaseException` plus `_is_caught`, with a bare `raise` for a
   miss. For a TUPLE catch the behavior is preserved: a non-member is re-raised as the same object, and bare `raise`
   leaves `__cause__` / `__context__` untouched. Pinned by `test_DUAL_the_tuple_form_is_unchanged`, by mutation (d)
   and by the 16 DUAL cells. **New failure mode:** if a predicate itself raises, that exception replaces the
   original fault. `proven_no_key` only does `isinstance` checks and attribute reads, and every
   `TxnDomainRejectionError` gets both attributes in `__init__`, so this is latent. LOW, see R-3.
3. `TxnDomainRejectionError.__init__` changed from `Exception(*args)` to `(message="", *, error_class, kind)`, so a
   multi-positional construction would now raise `TypeError`. The AST scan found NO production construction outside
   the ONE helper. **Preserved** for every live site.
4. The `_domain_rejection_error(error_class, message)` signature gains a keyword-only `kind=None`. Two-argument
   callers in tests still work; the builder measured 20 such test callers green.
5. The default `catch=` of `wrap_store_rejection` is unchanged (`(SurrealStoreError,)`). **Preserved-with-pin**:
   mutation (d), 16/16 cells red.

**Diff against the spec/report inventories:** my fate table matches §15's table plus the §15.2 classification axis
and FORK-2, cell for cell, with ONE row the spec does not write down: an engine kind the SDK does not enumerate. §15.2
says "other kinds TRUE", and the build implements that literally (finding R-1). The builder's §Q1B.CHANGES lists the
same symbol set I derived. Nothing in the diff is undisclosed.

**Count correction:** the brief and two test docstrings say *"the 20 other callers"* (`test_mint_unknown_outcome_note_q1.py::TestTheOtherWrapCallersAreUnchanged`,
`test_mint_kind_carveout_q1b.py::TestTheWrapAcceptsTheStorePredicate`). Derived at the build: there are **16
non-mint default call sites** (17 default sites, minus the mint's own outer wrap). lore_impact's "21 production
references" counts 21 consumer ENTRIES (4 modules + 17 functions), not call sites. The default is unchanged for ALL
of them, so this is a prose-count error only (test-tree docstrings, not served). R-4.

### §2 Conformance

| requirement | verdict | receipt |
|---|---|---|
| ONE predicate decides catch + message + note; no second copy, no local re-classification | **HOLDS** | `principal_keys` imports `proven_no_key` and uses it at exactly 2 sites (`catch=` and `_mint_fault_note`). AST (`principal_keys.py`): the only store-class `isinstance` is `isinstance(fault, SurrealConnectionError)`, which picks the conditional note's WORDING after the predicate has said FALSE. It is not a proven-ness decision. `_classified_fault` only unwraps `__cause__`. Mutations (c), (f) and the contract's rebind pins move BOTH. |
| Classified refusals proven ∀ kind; `unspecified` × {Internal, Serialization, TimedOut, Cancelled, bare Query, None} unknown | **HOLDS** | `test_the_predicate_over_label_and_kind` 91/91 green at the build; mutation (b) reddens exactly the 36 classified×unknown-kind cells (+8); mutation (f) reddens the bare-Query cells |
| kind set only at `_domain_rejection_error`, from typed errors at BOTH raise sites, never parsed | **HOLDS** | `_typed_kind` reads `ServerError.kind` and `details.kind` (a typed dict field, the existing `_detail_kind`), with no text read. Mutations (a) txn site and (a') single site are each caught by name |
| tuple `catch=` default unchanged for the other callers | **HOLDS** (count is 16, not 20 — R-4) | mutation (d) |
| #400 outer wrap, live UNIQUE pin, cancellation propagation | **HOLDS** | AST: the mint keeps a default-catch outer wrap; `TestALiveUniqueCollisionCarriesNoRevokeAdvice::test_a_duplicate_name_mint` is green at the build (:18000) and red under mutation (b); `test_a_non_taxonomy_fault_is_never_proven[CancelledError/KeyboardInterrupt]` green, plus the full suite (§5) |

**Test-file edits (disclosure check), diffed against HEAD:**
- `test_fixwave_a28c_63c_i_a.py`: one line. A fake's signature gains `*, kind: str | None = None`. The body and all
  assertions are unchanged, and the fake still returns a kind-less base rejection, which suits a class-mapping pin.
  **No assertion changed.**
- `test_mint_kind_carveout_q1b.py`:
  - The `TYPE_CHECKING` import and the 4-line anchor block are deleted. These are runtime-inert lines and the
    registry bound's self-destruct trigger.
  - `getattr(_txn_module, "proven_no_key")` becomes the attribute read. The `assert callable(...)` that follows is
    unchanged, so the accessor still reds by name if the symbol vanishes.
  - **No assertion changed, nothing weakened.** One stale docstring remains ("STUB EXPECTATION … RED by
    AttributeError"), already flagged as F-2 in the contract-fix report.
- Process note (not a defect in the bytes): the anchor deletion was a test-file edit by the implementer, a role
  boundary crossing (brief-base §2) done on a lead instruction, with no operator grant quoted. It was disclosed, and
  I confirm it is inert.
- `scripts/pending_contracts.yaml`: the `am37-15-q1b-mint-contract` bound and its comment are removed (−29 lines),
  as that entry's own reopen_trigger demands.

### §3 Mutations (my own; `scripts/mutation_proof.py`; declared ids taken from `--collect-only` and written before each run)

Tree: a `./scripts/scratch_copy.sh` copy. **Provenance receipt** printed by every run:
`loremaster.__file__ = /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/51894dc5-4184-4f95-b668-253731883342/scratchpad/mut/loremaster/loremaster/__init__.py`
(`lorerunes` likewise in the scratch copy). Every run ended with "tree restored byte-exact".

| id | mutation | declared RED | observed | verdict |
|---|---|---|---|---|
| (a) | `_run_verified_transaction` stops passing `kind=` | 10 (txn-site cells ∀ non-transport kind) | 10 failed / 159 passed | **PROOF HELD exactly** |
| (a') | `_raise_attempt_failure` stops passing `kind=` | 23 (11 seam cells, 6 proven-kind mint cells, 3 classified-Internal cells, 2 rebind pins, wrap[Validation]) | 23 failed / 147 passed | **PROOF HELD exactly** |
| (b) | drop `if error.error_class != _ERROR_CLASS_UNSPECIFIED: return True` (classified labels decided by kind) | 44 (36 classification-axis cells: 6 labels × {Internal, Serialization, TimedOut, Cancelled, Query, None}; 2 kind-less-instance + 2 kind-less-mint cells for UNIQUE/governed; 3 classified-Internal mint cells; the LIVE UNIQUE pin) | 44 failed / 126 passed | **PROOF HELD exactly** |
| (c) | `_is_caught`: `return catch(error)` → `return True` (predicate ignored) | 14 (3 reclassify predicate pins, wrap[TimedOut], 5 unknown-kind mint cells, kind-less base mint cell, 4 one-predicate rebind pins) | 14 failed / 155 passed | **PROOF HELD exactly** |
| (d) | `_DEFAULT_REJECTION_CATCH = (TxnDomainRejectionError,)` | 16 (`TestTheOtherWrapCallersAreUnchanged` ×16) | 16 failed | **PROOF HELD exactly** |
| (f) | remove `ErrorKind.QUERY` from `_OUTCOME_UNKNOWN_KINDS` (FORK-2) | 3 (seam[Query], mint[Query], axis[UNSPECIFIED-Query]) | 3 failed / 166 passed | **PROOF HELD exactly** |

No mutation survived. Mutation (c) was run over the owned file only, to keep the declared set exact. In principle it
would also redden `test_mint_unknown_outcome_note_q1.py` cells (a bare base fault would be translated to "could not
mint"). I did not measure that: **NOT TRIED** as a declared proof.

Instrument (committed tool + my battery script, pasted verbatim in §8).

### §4 Trust: served strings the build changed
- **No served message text changed.** The three messages ("could not mint key …", the outcome-unknown message, "the
  mint answered no row") and both notes are byte-identical to HEAD. What changed is WHICH faults get which.
- "Could not mint" beside a conditional note is impossible by construction: ONE predicate decides both, and the
  contract's `_assert_unknown_fate` asserts the substring appears nowhere in `str`, `_fault_line` or
  `traceback.format_exception`. Mutation (c) shows that pin can fail.
- The new `error_class` / `kind` attributes are not rendered anywhere (AST: no production read outside `_txn`).
- **The one false cause the build CAN serve is R-1:** "could not mint key …" with NO revoke note for an
  unenumerated-kind rejection. That is a claim of non-landing the kind does not prove.


### §5 Full suite (ONCE) — `uv run python scripts/pending_contract_gate.py --currency -- --maxprocesses=12` under `systemd-run --scope MemoryMax=16G`
- Started at MemAvailable 30.3 GiB with no other lore pytest (process-name match). Peak scope memory was 9.2 GB, with 0 cap kills.
- **Gate verdict:** typecheck RED_ADJUDICATED (83 residuals, owned by packet-58 / packet-64b-i) · ruff GREEN · pytest RED_ADJUDICATED (**530 residuals**, owned by packet-58-contract / packet-64b-i-contract) · **`CURRENCY: PASS`**, RED_ORPHANED 0.
- **Junit census (build):** **13355 passed, 530 failed, 70 skipped** (13955 cases).
  - All 530 failures are in 32 files, every one registered in `scripts/pending_contracts.yaml`. The largest are `test_comms_footer` 81, `test_reanchor_58_r3_convergence` 60, `test_supersede_reanchor_58` 44, `test_governed_substrate_64b` 34, `test_findings_migrate_64b` 28 and `test_mcp_server` 28.
  - The contract files are all green, including `test_mint_kind_carveout_q1b.py` 169/169 (also measured directly at baseline in §3) and the live UNIQUE pin.
  - The total matches the Q1 audit's 530.
- **HEAD vs build on the owned files.** The 32 registered files were run in the scratch tree with the 6 files restored to `git show HEAD:` bytes (provenance: `_txn.__file__` in scratch, `proven_no_key` absent). Result: `530 failed, 1310 passed, 2 skipped`.
  - Diffed by node id against the build's full-suite junit: **HEAD 530 · build 530 · identical 530 · HEAD-only 0 · build-only 0.**
  - No owned-file red moved.

### §6 Findings

**R-1 · MEDIUM · design (spec-conformant; needs a sidecar/operator ruling): the kind half of `proven_no_key`
enumerates the UNKNOWN set, so any kind outside it, including a kind nobody has ever seen, is filed "proven no key".**
- **CLASS:** *a predicate that grants a safety verdict must allowlist the SAFE kinds. Here the domain it is complete
  over (the installed SDK's enumerations) is narrower than the domain it is applied to (any string the engine
  sends).* This is the CLAUDE.md "allowlist the safe" law. It also contradicts §15's own asymmetry ("a conditional
  note on a pre-commit fault costs one `list-keys`; the reverse costs a live credential").
- **Failure scenario (constructed, probe in §8):**
  - `surrealdb.errors.parse_rpc_error` / `parse_query_error` build a plain `ServerError(kind=<raw>)` for any kind
    string missing from `KIND_TO_CLASS`. The same happens for a `Query` error whose `details.kind` is not a
    `QueryDetailKind`.
  - `is_connection_error` says domain, `_classify_engine_error` says `unspecified rejection`, and
    `_typed_kind` passes the raw string through.
  - So `proven_no_key` is TRUE: the mint says "could not mint key …" with no revoke note.
  - Measured at the build: kind `'Transaction'` gives TRUE, and Query detail `'Aborted'` gives TRUE. CONTROLS:
    `Internal` gives FALSE and `Validation` gives TRUE.
  - The engine runs the FLOATING `v3.2` tag (#336, store reference §0). A patch release can therefore introduce a
    kind with no SDK change and no decision, and no completeness pin fires.
  - The contract's completeness pin (`TestEveryEngineKindIsAdjudicated::test_every_kind_is_ruled`) is generated over
    the SDK's enumerations, so it reds only when the SDK is upgraded, never when the engine moves.
- **Why it is not a build defect:** §15.2 rules *"other kinds TRUE"* verbatim, and §15's mechanics wrote
  `kind not in _OUTCOME_UNKNOWN_KINDS`. The builder implemented the ruling exactly.
- **Recommended fix (one line, the inverse form):**
  - `proven = kind in _PROVEN_KINDS`, with `_PROVEN_KINDS = {Validation, Thrown, AlreadyExists, NotFound,
    Configuration, NotExecuted}`. That is exactly §15's "proven" row, and it is a smaller set than the unknown one.
  - Keep the completeness pin over the SDK enumerations.
  - Add a pin: an unenumerated kind string through the real seam must be UNKNOWN.
  - Mutation: add `"Transaction"` to `_PROVEN_KINDS`, and the pin reds.
- **SIBLINGS TRIED:**
  - an unenumerated top-level kind (TRUE, the false clear);
  - an unenumerated Query detail kind (TRUE, the false clear);
  - kind `None` (FALSE, safe);
  - every enumerated kind (matches the ruling; mutations (a'), (f)).
- **SIBLINGS NOT TRIED:**
  - the transactional path with an unenumerated kind (rolled back, so a TRUE there is accurate anyway);
  - `NotExecuted` arriving as the ROOT cause on the single-statement path. Is it reachable for a lone CREATE?
    Not probed.

**R-2 · LOW · process (disclosed): the implementer edited the owned contract file** (deleted the `TYPE_CHECKING`
anchor). This is a §2 role-boundary transfer done on a lead instruction with no operator grant quoted. The bytes are
inert, and I verified no assertion changed.
- **CLASS:** test-file edits by a non-author.
- **SIBLINGS TRIED:** both test-file diffs, line by line.
- **SIBLINGS NOT TRIED:** none.

**R-3 · LOW · latent: a predicate `catch=` that raises masks the original fault.** `reclassify` consults the
predicate inside `except BaseException`. If the predicate raises, the new exception propagates, with the original
fault only as `__context__`. `proven_no_key` cannot raise for any instance built through `__init__` (it does
attribute reads on attributes always set there). The risk is a future predicate, or a subclass overriding `__init__`
without `super()`.
- **CLASS:** "the catch decision is total". Suggested pin: a raising predicate. Should it re-raise the ORIGINAL fault?
  That is a lorerunes design choice for the sidecar.
- **SIBLINGS TRIED:** an AST scan for subclasses of the family (none outside `_txn`).
- **SIBLINGS NOT TRIED:** `copy` / `pickle` round-trips of a rejection (the `__reduce__` path re-calls
  `__init__(message)` and restores `__dict__`, so the attributes survive; not executed).

**R-4 · LOW · prose count: "the 20 other callers"** (brief; docstrings of
`test_mint_unknown_outcome_note_q1.py::TestTheOtherWrapCallersAreUnchanged` and
`test_mint_kind_carveout_q1b.py::TestTheWrapAcceptsTheStorePredicate`). The derived count is 16 non-mint
default-catch call sites (AST, §1). Behavior is unaffected.
- **CLASS:** un-derived counts in prose.
- **SIBLINGS TRIED:** a scan of production code and the am-37 spec (no "20 callers" claim there).
- **SIBLINGS NOT TRIED:** other reports.

Also carried, not new: the contract-fix report's **F-2** (a stale "STUB EXPECTATION" docstring in
`_proven_no_key`) and **F-3** (`pending_contract_gate.py --legs` reports a deselected leg as ORPHAN/FAIL).


### §7 md5s (start = end; tree left byte-identical; no git mutation)
| file | start | end |
|---|---|---|
| `loremaster/loremaster/principal_keys.py` | 552bb7177232a5cf02b47ac363f67af8 | 552bb7177232a5cf02b47ac363f67af8 |
| `loremaster/loremaster/store/_txn.py` | 86f9a898fa486ad7e7c8b32080e8134c | 86f9a898fa486ad7e7c8b32080e8134c |
| `lorerunes/lorerunes/engine_rejection.py` | f325da77075c6abf23810888c8cbef04 | f325da77075c6abf23810888c8cbef04 |
| `loremaster/tests/test_fixwave_a28c_63c_i_a.py` | 48e51b1ecde3ffa1df705049af4e90dd | 48e51b1ecde3ffa1df705049af4e90dd |
| `loremaster/tests/test_mint_kind_carveout_q1b.py` | c7cd0b34ed32423df6e3c3223ea45496 | c7cd0b34ed32423df6e3c3223ea45496 |
| `scripts/pending_contracts.yaml` | b0158ed1189ea905faf9c8d8b9f87f76 | b0158ed1189ea905faf9c8d8b9f87f76 |
| build patch | 476827a257083df896f6d302297ac291 | (unchanged) |

Every mutation ran in the scratch copy, never in the real tree. `git status` at the end shows the same 6 `M` files plus untracked reports (this one added).

### §8 Instruments (pasted verbatim; scratch-resident, so this is their durable copy)

`run_mutations.sh` (the battery; `scripts/mutation_proof.py` is the committed tool it drives):
```bash
#!/usr/bin/env bash
# coldaudit-mint-q1b mutation battery — run from the scratch_copy tree. Declared red sets are written
# from the contract + spec BEFORE any run (ids from --collect-only); mutation_proof diffs both ways.
set -u
cd "$1" || exit 2
which="$2"
Q=loremaster/tests/test_mint_kind_carveout_q1b.py
Q1=loremaster/tests/test_mint_unknown_outcome_note_q1.py
LIVE=loremaster/tests/test_am37_13_3_63c_i_a.py::TestALiveUniqueCollisionCarriesNoRevokeAdvice
RUN=(systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300 -p no:cacheprovider -q)
uv run python -c "import loremaster,lorerunes;print('PROVENANCE', loremaster.__file__, lorerunes.__file__)"
ex() { for id in "$@"; do printf -- '--expect-red\n%s\n' "$id"; done; }
case "$which" in
a_txn)  # transactional raise site stops passing kind
  mapfile -t E < <(ex $(for k in AlreadyExists Cancelled Configuration Internal NotExecuted NotFound Serialization Thrown TimedOut Validation; do echo "$Q::TestTheTransactionalRaiseSitePassesTheKind::test_the_transactional_rejection_carries_its_kind[$k]"; done))
  uv run python scripts/mutation_proof.py --file loremaster/loremaster/store/_txn.py \
    --anchor $'                kind=_typed_kind(typed_root),\n' --replacement '' "${E[@]}" -- "${RUN[@]}" $Q ;;
a_single)  # single-statement raise site stops passing kind
  ids=()
  for k in AlreadyExists Cancelled Configuration Internal NotExecuted NotFound Query Serialization Thrown TimedOut Validation; do ids+=("$Q::TestEveryEngineKindIsAdjudicated::test_the_seam_and_the_predicate_agree_with_the_ruling[$k]"); done
  for k in AlreadyExists Configuration NotExecuted NotFound Thrown Validation; do ids+=("$Q::TestTheMintFollowsTheKind::test_a_typed_rejection_during_the_CREATE[$k]"); done
  for r in assert coercion unique; do ids+=("$Q::TestAClassifiedInternalRefusalIsProvenAtTheMint::test_a_classified_internal_refusal[$r]"); done
  ids+=("$Q::TestOnePredicateDecidesCatchMessageAndNote::test_moving_Internal_OUT_of_the_unknown_kinds_flips_message_and_note")
  ids+=("$Q::TestOnePredicateDecidesCatchMessageAndNote::test_moving_Validation_IN_flips_message_and_note")
  ids+=("$Q::TestTheWrapAcceptsTheStorePredicate::test_the_predicate_catch[Validation]")
  mapfile -t E < <(ex "${ids[@]}")
  uv run python scripts/mutation_proof.py --file loremaster/loremaster/store/_txn.py \
    --anchor $'        kind=_typed_kind(error),\n' --replacement '' "${E[@]}" -- "${RUN[@]}" $Q $LIVE ;;
b_label)  # a classified label is treated by kind (drop the error_class check)
  ids=()
  for l in ASSERT_VIOLATION FIELD_COERCION GOVERNED_CONFLICT QUERY_TOO_COMPLEX RETRYABLE_CONFLICT UNIQUE_VIOLATION; do
    for k in Internal Serialization TimedOut Cancelled Query None; do ids+=("$Q::TestTheClassificationAxis::test_the_predicate_over_label_and_kind[_ERROR_CLASS_$l-$k]"); done; done
  for c in TxnGovernedConflictError TxnUniqueViolationError; do
    ids+=("$Q::TestThePredicateOverTheTaxonomy::test_a_kind_less_instance[$c]")
    ids+=("$Q::TestTheMintFollowsTheKind::test_a_kind_less_rejection_during_the_CREATE[$c]"); done
  for r in assert coercion unique; do ids+=("$Q::TestAClassifiedInternalRefusalIsProvenAtTheMint::test_a_classified_internal_refusal[$r]"); done
  ids+=("$LIVE::test_a_duplicate_name_mint")
  mapfile -t E < <(ex "${ids[@]}")
  uv run python scripts/mutation_proof.py --file loremaster/loremaster/store/_txn.py \
    --anchor $'    if error.error_class != _ERROR_CLASS_UNSPECIFIED:\n        return True\n' --replacement '' "${E[@]}" -- "${RUN[@]}" $Q $LIVE ;;
c_pred)  # reclassify ignores the predicate (treat it as always true)
  ids=()
  for t in test_a_true_predicate_translates test_a_false_predicate_passes_the_SAME_object_untouched test_a_base_exception_the_predicate_rejects_propagates; do ids+=("$Q::TestReclassifyHonoursAPredicateCatch::$t"); done
  ids+=("$Q::TestTheWrapAcceptsTheStorePredicate::test_the_predicate_catch[TimedOut]")
  for k in Cancelled Internal Query Serialization TimedOut; do ids+=("$Q::TestTheMintFollowsTheKind::test_a_typed_rejection_during_the_CREATE[$k]"); done
  ids+=("$Q::TestTheMintFollowsTheKind::test_a_kind_less_rejection_during_the_CREATE[TxnDomainRejectionError]")
  for t in test_moving_Internal_OUT_of_the_unknown_kinds_flips_message_and_note test_moving_Validation_IN_flips_message_and_note test_moving_a_class_OUT_of_the_class_half_flips_the_note test_replacing_the_predicate_moves_catch_and_note_together; do ids+=("$Q::TestOnePredicateDecidesCatchMessageAndNote::$t"); done
  mapfile -t E < <(ex "${ids[@]}")
  uv run python scripts/mutation_proof.py --file lorerunes/lorerunes/engine_rejection.py \
    --anchor $'    return catch(error)\n' --replacement $'    return True\n' "${E[@]}" -- "${RUN[@]}" $Q ;;
d_default)  # the default catch= narrowed
  ids=()
  for c in SurrealStoreError FenceLostError FloorCalibrationError LeaseError CalibrationPoolCountMismatchError CalibrationPoolError CalibrationPoolTruncatedError VectorDimensionError; do
    ids+=("$Q1::TestTheOtherWrapCallersAreUnchanged::test_the_default_wrap_translates[$c]" "$Q1::TestTheOtherWrapCallersAreUnchanged::test_revoke_still_translates[$c]"); done
  mapfile -t E < <(ex "${ids[@]}")
  uv run python scripts/mutation_proof.py --file loremaster/loremaster/store/_txn.py \
    --anchor $'_DEFAULT_REJECTION_CATCH: tuple[type[SurrealStoreError], ...] = (SurrealStoreError,)\n' \
    --replacement $'_DEFAULT_REJECTION_CATCH: tuple[type[SurrealStoreError], ...] = (TxnDomainRejectionError,)\n' \
    "${E[@]}" -- "${RUN[@]}" "$Q1::TestTheOtherWrapCallersAreUnchanged" ;;
esac
echo "EXIT=$?"
```

Mutation (f) was run inline:
```bash
systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 uv run python scripts/mutation_proof.py \
  --file loremaster/loremaster/store/_txn.py --anchor $'        ErrorKind.QUERY,\n' --replacement '' \
  --expect-red "$Q::TestEveryEngineKindIsAdjudicated::test_the_seam_and_the_predicate_agree_with_the_ruling[Query]" \
  --expect-red "$Q::TestTheMintFollowsTheKind::test_a_typed_rejection_during_the_CREATE[Query]" \
  --expect-red "$Q::TestTheClassificationAxis::test_the_predicate_over_label_and_kind[_ERROR_CLASS_UNSPECIFIED-Query]" \
  -- uv run --with pytest-timeout pytest -n 8 --timeout=300 -p no:cacheprovider -q $Q
```

`probe_unenumerated_kind.py` (R-1), with its output at the build:
```python
"""coldaudit-mint-q1b probe: what proven_no_key answers for an engine kind the installed SDK does NOT enumerate.
Built through the REAL failure ladder (_raise_attempt_failure) from a REAL SDK parse, exactly as the contract does."""
import asyncio, logging
import surrealdb.errors as sdk
from loremaster.store import _txn

async def through(error):
    async def drop(_c): pass
    try:
        await _txn._raise_attempt_failure(error, object(), drop=drop, url="ws://x/rpc", noun="probe",
                                          label="probe.rejected", logger=logging.getLogger("probe"))
    except BaseException as raised:
        return raised

cases = {
    "CONTROL Internal (enumerated, unknown)": sdk.parse_query_error({"kind": "Internal", "result": "boom"}),
    "CONTROL Validation (enumerated, proven)": sdk.parse_query_error({"kind": "Validation", "result": "boom"}),
    "unenumerated top-level kind 'Transaction'": sdk.parse_query_error({"kind": "Transaction", "result": "boom"}),
    "unenumerated Query detail kind 'Aborted'": sdk.parse_query_error({"kind": "Query", "result": "boom", "details": {"kind": "Aborted"}}),
}
for label, error in cases.items():
    raised = asyncio.run(through(error))
    print(f"{label:45s} sdk_class={type(error).__name__:12s} -> {type(raised).__name__} kind={getattr(raised,'kind',None)!r} "
          f"error_class={getattr(raised,'error_class',None)!r} proven_no_key={_txn.proven_no_key(raised)}")
```
```
CONTROL Internal (enumerated, unknown)        sdk_class=InternalError -> TxnDomainRejectionError kind='Internal' error_class='unspecified rejection' proven_no_key=False
CONTROL Validation (enumerated, proven)       sdk_class=ValidationError -> TxnDomainRejectionError kind='Validation' error_class='unspecified rejection' proven_no_key=True
unenumerated top-level kind 'Transaction'     sdk_class=ServerError  -> TxnDomainRejectionError kind='Transaction' error_class='unspecified rejection' proven_no_key=True
unenumerated Query detail kind 'Aborted'      sdk_class=QueryError   -> TxnDomainRejectionError kind='Aborted' error_class='unspecified rejection' proven_no_key=True
```

- **State:** done
