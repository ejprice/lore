brief-base v18 read · brief project v7 read

**State:** done. This is the am-37 §14 Q1 GREEN build on HEAD `7908571` (`790857166afc`), measured 2026-10-05 between 11:07Z and 11:25Z. Nothing is committed (the lead commits).

- **Deviations:**
  - (1) Self-destruct: I removed `TYPE_CHECKING` from the `from typing import …` line as well as the `if TYPE_CHECKING:` block. That import was half of the §OWN anchor edit (REPORT-contract-mint-q1.md §OWN step 1), and leaving it would make ruff F401 red.
  - (2) The test file was ALREADY dirty before I started: someone outside this run had changed one comment, at `TestOneTupleDecidesNoteAndMessage.test_moving_a_proven_class_OUT_flips_both` ("∀ such faults, cause-neutral" → "cause-neutral"). I left that hunk as I found it. It is in the diff and it is not mine.
  - (3) I did not run `lore_index(reconcile=True)` (#542). Every `lore_impact` and `lore_get_symbol` read happened BEFORE my first edit, so my edits could not have made them stale. A status read afterwards showed `last_sync` 15 s old at `7908571`.
- **Packages considered:** `lorerunes.reclassify` (read: its installed source, `lorerunes/lorerunes/engine_rejection.py`), verdict `replace`. I reused the existing seam through its new `catch=` parameter and wrote no second reclassifier. PEP 678 `add_note` (stdlib) is unchanged.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 5 new symbols, all dispositioned (§DRY).
- **Graded:** n/a (implementer; I render no verdict on another agent's artifact).
- **Decisions needed:** none blocking. Surfaced items are listed in §NOTICED.
- **Pointers:** §CHANGES · §RUNS (before/after) · §MUTATION · §CURRENCY · §INVENTORY · §SWEEP · §DRY · §NOTICED

## Capability check
- **Demanded:** lore-first discovery, lore_comms registration, gated and capped pytest, `scripts/mutation_proof.py`, and the currency gate.
- **Available:** everything except grep in the main checkout. A PreToolUse hook blocks it, so the textual sweep (§SWEEP) used `find | xargs awk`. That is a FALLBACK and I am saying so: the needles are prose in docstrings and comments, a non-symbol seam (CLAUDE.md dogfood item 3b).
- **Gate script:** the `pgrep` waiting gate is my scratch `gate_run.sh`, a copy of contract-mint-q1's gate with only the header comment changed. Pasted verbatim:
  ```bash
  #!/usr/bin/env bash
  # WAITING gate (implement-mint-q1 brief): MemAvailable >= 20 GiB AND no other lore pytest; then run capped.
  set -u
  cd /home/ejprice/PycharmProjects/lore
  need_kib=$((20 * 1024 * 1024))
  while :; do
    avail=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
    others=$(pgrep -fa '[p]ython.*-m pytest|[b]in/pytest' | awk -v me="$$" '$1 != me' || true)
    if [ "$avail" -ge "$need_kib" ] && [ -z "$others" ]; then break; fi
    echo "GATE WAIT $(date -Is) MemAvailable=$((avail / 1024 / 1024))GiB others=[$(printf '%s' "$others" | head -c 200)]"
    sleep 20
  done
  echo "GATE PASS $(date -Is) MemAvailable=$((avail / 1024 / 1024))GiB"
  exec systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 \
    uv run --with pytest-timeout pytest -n 8 --timeout=300 -p no:cacheprovider "$@"
  ```

## §CHANGES (symbols, not line numbers)

**`loremaster/loremaster/store/_txn.py`**
- NEW `_PROVEN_NO_KEY_FAULTS: tuple[type[SurrealStoreError], ...]`. It is a hand-adjudicated literal (F-2 (b)) placed directly above `wrap_store_rejection`, after every class it names. Its six members are `TxnDomainRejectionError`, `TxnGovernedConflictError`, `TxnUniqueViolationError`, `TxnContentionExhaustedError`, `TxnParamCollisionError` and `TxnEnvelopeViolationError`. The comment states why it is a literal (computing it would be the false-clear direction) and that its complement is never enumerated.
- NEW `_DEFAULT_REJECTION_CATCH = (SurrealStoreError,)`. This names the default and does not change its value.
- `wrap_store_rejection` gains keyword-only `catch: tuple[type[SurrealStoreError], ...] = _DEFAULT_REJECTION_CATCH`, which is forwarded to `reclassify(catch=…)`. Its docstring now names the default and the narrowed catch, and has a new `catch` arg entry. The pass-through tuple is untouched.

**`loremaster/loremaster/principal_keys.py`**
- The import adds `_PROVEN_NO_KEY_FAULTS`.
- NEW module constants `_MINT_CAUSE_CONNECTION` (exactly today's "the connection failed during the CREATE") and `_MINT_CAUSE_UNCONFIRMED` ("the store did not confirm the CREATE"). The second is the F-3 cause-neutral parenthetical: it contains no word from the contract's `_FAMILY_CAUSE_WORDS`.
- `PrincipalKeyStore.mint` uses NESTED wraps on the one seam (N-3 (d)):
  - OUTER, default catch: "the store did not confirm the mint of key {name!r} for principal {email!r}; its outcome is unknown".
  - INNER, `catch=_PROVEN_NO_KEY_FAULTS`: "could not mint key {name!r} for principal {email!r}", the same text as before.
  - Unchanged: the ONE `try`, the ONE `except BaseException`, `error.add_note`, and the bare `raise`.
  - The window comment and the docstring `Raises:` are updated.
- `PrincipalKeyStore._mint_fault_note`:
  - After the answer: the certain note, checked FIRST, unchanged.
  - Before the answer: it computes `fault = cls._classified_fault(error)`. If `isinstance(fault, _PROVEN_NO_KEY_FAULTS)` it returns `None`. Otherwise it returns the conditional note, with the parenthetical `_MINT_CAUSE_CONNECTION` when the fault is a `SurrealConnectionError` and `_MINT_CAUSE_UNCONFIRMED` otherwise.
  - The docstring is rewritten: it corrects §13.5 item 1's "exactly ONE class" and cites §14 Q1, F-1 and F-3.
- NEW `PrincipalKeyStore._classified_fault` (staticmethod), implementing F-1 (b). For a `PrincipalKeyStoreError` with a `__cause__` it returns the cause; otherwise it returns `error`. A wrap error with no cause is classified as itself, which gives the fail-safe conditional note.
- **ONE tuple decides three things:** the inner wrap's catch (and so the message and the translation) and the note. Both read `_PROVEN_NO_KEY_FAULTS` at call time. There is no second copy and no local `isinstance` ladder. The only extra class test is `SurrealConnectionError`, and it chooses the WORDING only, as the operator ruled in F-3. It never decides whether a note is given.

**Self-destruct**
- `scripts/pending_contracts.yaml`: I deleted the `am37-14-q1-mint-contract` entry and the 4-line comment block that belonged to it (17 lines in total).
- `loremaster/tests/test_mint_unknown_outcome_note_q1.py`: I deleted the `if TYPE_CHECKING:` owner anchor and its `TYPE_CHECKING` import (deviation 1). There are no other test edits.

`git diff --stat` at 11:20Z:
```
 loremaster/loremaster/principal_keys.py            | 84 +++++++++++++++++-----
 loremaster/loremaster/store/_txn.py                | 53 +++++++++++---
 .../tests/test_mint_unknown_outcome_note_q1.py     | 11 +--
 scripts/pending_contracts.yaml                     | 17 -----
 4 files changed, 111 insertions(+), 54 deletions(-)
```
(The test-file count includes the one-line comment hunk that is not mine; see deviation 2.)

Final md5s:

| file | md5 |
|---|---|
| `_txn.py` | `4ebe3712beba2963902eb1745e9b80ce` |
| `principal_keys.py` | `c67cc35659e0ddc5518816825e5ad0c7` |
| test file | `90a6d1402831d6432f1970ab8f54ce10` |
| yaml | `b0158ed1189ea905faf9c8d8b9f87f76` |

Pre-edit content backups are in my session scratchpad's `backup/`.

## §RUNS — targeted, BEFORE vs AFTER (each run printed `GATE PASS`; capped scope; `-n 8`)

**Derivation of the targeted set:**
- The two contract files.
- contract-mint-q1's eight-file set: the `lore_impact` covering tests of `wrap_store_rejection`, `PrincipalKeyStore.mint` and `_mint_fault_note`, plus the #400 and fates scanners.
- The store tests of the wrap's other callers (`test_keeps_store`, `test_audit_store`, `test_principals_store`, `test_principal_keys_schema`).
- Tree-scanning AST pins (`test_store_seam_one_derivation`, `test_reanchor_58_r4_lease_fates`, `test_backoff_seam`, `test_anchored_pattern_seam`, `test_txn_contention`, `test_ast_reach_helpers`), and `test_retry_seam` (it scans `_txn`). 19 files in total.
- `lore_impact(wrap_store_rejection)` named 119 covering test ids with 104 elided, so I added the caller store files BY HAND, and I am saying so.

**Results:**
- **BEFORE** (HEAD `7908571`, production unedited): `48 failed, 1941 passed, 6 skipped`. The failures are:
  - 43 in `test_mint_unknown_outcome_note_q1.py`, which is the contract;
  - 1 in `test_exhaustion_fates.py::TestTheRegistryIsTheAdjudicationBothWays::test_every_row_names_a_ruled_classification_an_owner_and_evidence_that_HOLDS`;
  - 4 in `test_reanchor_58_r4_lease_fates.py::TestExhaustionAtTheLeaseStoreIsNamedByEffect::test_the_fail_safe_value_is_served_the_WARNING_names_the_class_and_nothing_follows[create|get|release_if_held|update]`.
- **AFTER, final bytes** (11:20Z): **`5 failed, 1985 passed, 6 skipped`**.
  - **All 43 contract cells are GREEN.** 0 failures are in `test_mint_unknown_outcome_note_q1.py` or `test_am37_13_3_63c_i_a.py`.
  - **0 GREEN→RED.** The 5 remaining reds are exactly the 5 pre-existing ones: the `test_exhaustion_fates.py` `store/lease.py` row the brief names, plus the 4 `test_reanchor_58_r4_lease_fates.py` cells.
  - **Both files are registered under the packet-58 bound** (`scripts/pending_contracts.yaml`, `packet-58-contract`; its `files:` list names both paths). They were red before my build and are unchanged by it.
  - ⚠ The brief named only the fates row as allowed. The 4 r4 lease-fates cells are a second pre-existing, 58-owned family that the brief did not mention.
- **Collection delta, +1, explained.** I diffed `--collect-only` before and after, using a content swap of the backups that was restored by md5. The only new id is `test_principals_cli.py::TestNoWrapContextOverClaimsItsCause::test_the_wrap_context_names_the_operation_not_a_guessed_cause[principal_keys.py::mint::<line>]`.
  - That pin GENERATES one cell per wrap site, and `mint` now has two; both pass, so the OUTER message passes the "names the operation, not a guessed cause" pin.
  - The other id changes are line-number parametrize ids that shifted. They are not tests added or removed.

## §MUTATION — `scripts/mutation_proof.py` (ids declared BEFORE the run, from `--collect-only`)

**Mutation:** in `_txn.py`, drop `TxnParamCollisionError,` from `_PROVEN_NO_KEY_FAULTS`. It is a leaf class, so no ancestor in the tuple covers it.

**Declared RED (6):**
- `test_am37_13_3_63c_i_a.py::TestTheMintWindowNotesTheRevokeRepair::test_a_fault_during_the_CREATE_call[plain-TxnParamCollisionError]` and `[needs-quoting-…]`: the NOTE reddens;
- `test_mint_unknown_outcome_note_q1.py::TestAnUnprovenFaultNeverClaimsNonLanding::test_a_proven_fault_keeps_the_not_landed_message[TxnParamCollisionError]`: the MESSAGE (which wrap translated it) reddens;
- `…::TestTheProvenNoKeySetIsOneExportedTuple::test_the_mint_reads_the_one_tuple[TxnParamCollisionError]`;
- `…::test_the_tuple_is_the_rulings_adjudication`;
- `…::test_the_tuple_plus_the_connection_class_is_the_derived_taxonomy`.

**Command:** `mutation_proof.py --file loremaster/loremaster/store/_txn.py --anchor <the 3 tuple-tail lines> --replacement <minus the class> --expect-red ×6 -- gate_run.sh -q <the two contract files>`.

**Result:** exit 0, `6 failed, 196 passed, 2 skipped`, **"PROOF HELD — the declared RED set fired EXACTLY"**, and "tree restored byte-exact" (md5 `9eecfe5c…`, which is the pre-reflow bytes; only docstring lines changed after that).
- The observed note on the mutated proven fault was the cause-neutral conditional note on a `PrincipalKeyStoreError` whose message was "the store did not confirm the mint of key 'work laptop' … its outcome is unknown". So one tuple edit flipped the note, the message and the translating wrap together.
- I ran the proof on the REAL tree, with a content backup. It does not need `scratch_copy.sh`. `loremaster.__file__` = `/home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py` (printed, together with the live tuple's six names).

## §CURRENCY — `pending_contract_gate.py --currency --legs typecheck,ruff` (final bytes)
- `typecheck RED_ADJUDICATED — 83 residual(s)`. That is down from 84. The owners are now only `packet-58-contract` and `packet-64b-i-contract`, so **the `am37-14-q1-mint-contract` bound is GONE**: the anchor line resolved and the entry was deleted.
- `ruff GREEN`.
- **RED_ORPHANED 0 for typecheck and ruff.** `pytest NOT_RUN` (claimed but not run), which is expected because this command never starts pytest by law.
- The first two currency runs showed `ruff RED_ORPHANED` for one E501 in my own `wrap_store_rejection` docstring edit. I fixed it by reflowing the paragraph; the third run is the one above.
- **Not a gate, surfaced anyway:** `ruff format --check` would reformat both production files. I checked the pre-edit backups and they would be reformatted too, so this is pre-existing drift. I did not reformat them (no refactor in GREEN).

## §INVENTORY — removed or changed behaviour, every changed line, adjudicated

| # | before (`7908571`) | after | verdict |
|---|---|---|---|
| 1 | pre-answer `CancelledError` / `KeyboardInterrupt` / `TimeoutError` / raw `OSError` / `RuntimeError` / any non-store fault → NO note | conditional note (cause-neutral); same object; cancellation propagates | **changed by ruling** (§14 Q1); pinned by the q1 unknown-outcome, real-cancel and sameness cells |
| 2 | pre-answer bare `SurrealStoreError` → `PrincipalKeyStoreError("could not mint …")`, no note | `PrincipalKeyStoreError(<outcome-unknown msg>)` chained `from` it, plus the conditional note | **changed by ruling** (F-4 + N-3 (d)); #400 class preserved; pinned by the N-3 population and `test_engine_rejection_seam` |
| 3 | foreign `SurrealStoreError` subclasses (`LeaseError`, `FenceLostError`, …) → as row 2 before | as row 2 after | **changed by ruling** (N-3); pinned by the generated `_FOREIGN` population |
| 4 | proven, translated (`TxnDomainRejectionError`, `TxnUniqueViolationError`, `TxnGovernedConflictError`, `TxnParamCollisionError`, `TxnEnvelopeViolationError`) → "could not mint …", no note | identical (now the INNER wrap; the note is decided by `__cause__`) | **preserved-with-pin** (§14 "Unchanged: the UNIQUE no-advice pin"; the live UNIQUE pin and `test_a_proven_fault_keeps_the_not_landed_message`) |
| 5 | `TxnContentionExhaustedError` → raw pass-through, no note | identical (a pass-through in both wraps; a tuple member) | **preserved-with-pin** (fix531d's generated taxonomy leg) |
| 6 | `SurrealConnectionError` → raw pass-through, exact conditional text | identical (same pass-through, same text via `_MINT_CAUSE_CONNECTION`) | **preserved-with-pin** (`test_a_fault_during_the_CREATE_call[…-SurrealConnectionError]`, exact text) |
| 7 | post-answer → CERTAIN note, any fault | identical; `answered` is still checked first | **preserved-with-pin** (`TestAPostAnswerInterruptStaysCertain` and fix531d's certain pins) |
| 8 | ONE `try` / ONE `except BaseException` / bare `raise` | identical | **preserved-with-pin** (fix531d's AST one-handler pins and the 58 fates classifier; green) |
| 9 | `wrap_store_rejection(domain_error, context)` translated `(SurrealStoreError,)` | the same default via `_DEFAULT_REJECTION_CATCH`; new keyword-only `catch=`; the 20 other call sites are untouched in source | **preserved-with-pin** (`TestTheOtherWrapCallersAreUnchanged`, the #400 pins) |
| 10 | `mint` had 1 wrap-context site | 2 sites | **new, pinned** by the generated `TestNoWrapContextOverClaimsItsCause` (the +1 cell, green) |
| 11 | a pre-answer `PrincipalKeyStoreError` with NO `__cause__` → no note (it was never `SurrealConnectionError`) | conditional note | **spec-silent and unreachable pre-answer** (only the wraps raise that class before the answer, and they always chain). Fail-safe direction, NOT pinned. Flagged for the lead and auditor; not an operator question unless they disagree |

No other production behaviour changed.

## §SWEEP — old-rule wording, BARE pattern (awk fallback, said out loud)

**Sweep 1:** `find loremaster lorerunes loresigil lorescribe scripts docs/design docs/reference (*.py|*.md|*.yaml) | xargs awk 'BEGIN{IGNORECASE=1} /one class (gets|is unsafe)|exactly one class|ONE class is unsafe|only (the )?connection (class|fault) gets|connection failed during the CREATE/'`. Each hit, with a verdict:

| hit | verdict |
|---|---|
| `docs/design/2026-07-22-embedding-schema-reconciliation.md:77` | unrelated (schema field classes) |
| `docs/design/2026-09-29-packet63c-amendment-37.md:871` | §13.5 item 1 itself: historical spec text, corrected by §14 Q1 (`:912`). Not mine to edit; the spec is append-only |
| `docs/design/2026-09-29-packet63c-amendment-37.md:912` | §14 Q1 quoting the old rule in order to correct it: correct as is |
| `principal_keys.py` `_MINT_CAUSE_CONNECTION` | the connection class's exact text, kept by ruling F-3: correct |
| `principal_keys.py` `_mint_fault_note` docstring | quotes the old rule only to say §14 corrects it: correct (this is my rewrite of the stale prose) |
| `test_mint_unknown_outcome_note_q1.py:92` | the contract's own prose: correct |
| `test_am37_13_3_63c_i_a.py:529` | the connection exact-text oracle: correct |
| `loremaster/tests/test_surreal_store.py:4874` | unrelated ("yields exactly one class" of error) |

**Sweep 2**, over production `*.py`: `conditional|outcome is unknown|unknown outcome|outcome-unknown|proves no key|no key landed|revoke note|revoke repair`.
- The only rule-describing hits outside my own edits are `principals.py` `_fault_line`'s comment "PEP 678 notes (am-37 §13.5 item 1, e.g. ``mint``'s revoke repair)". It is still TRUE: it says where notes render, not which faults get them. Correct as is.
- `_txn.py`'s `TxnDomainRejectionError` docstring ("an UNKNOWN outcome" for transport) is consistent with the new rule. Correct as is.
- Every other hit is "unconditional…" or "conditional def/CAS" prose, unrelated.

**The stale old-rule prose was found in exactly one production place**, `_mint_fault_note`'s docstring, and it is rewritten. The `mint` window comment ("wrapped LOUD … around the CREATE alone") is also updated for the nested wraps.

## §DRY
| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `_txn._PROVEN_NO_KEY_FAULTS` | `lore_get_symbol(wrap_store_rejection)`, plus a read of `_txn` lines 1–254 | the taxonomy classes; no existing proven-set tuple (the contract also recorded 0 hits) | HAND-ROLLED as the ruled literal (F-2 (b)), the contract's named STUB EXPECTATION |
| `_txn._DEFAULT_REJECTION_CATCH` | same read | the inline `(SurrealStoreError,)` in the wrap | EXTENDED `wrap_store_rejection`: the existing inline default was named, not forked |
| `wrap_store_rejection(catch=)` | `lore_get_symbol(lorerunes.engine_rejection.reclassify)` | `reclassify` already takes `catch` | EXTENDED `wrap_store_rejection` (N-3 (d), as ruled); no second reclassifier |
| `principal_keys._MINT_CAUSE_CONNECTION` / `_MINT_CAUSE_UNCONFIRMED` | `lore_get_symbol(PrincipalKeyStore._mint_fault_note)` | the inline literal parenthetical | HAND-ROLLED, named constants for the two ruled parentheticals |
| `PrincipalKeyStore._classified_fault` | the same read; `lore_impact(_mint_fault_note)` (only caller: `mint`) | none | HAND-ROLLED: a 3-line F-1 (b) unwrap. It does NOT classify; the tuple does |

## §NOTICED (surfaced, not acted on)
- **N-a:** `lore-adm`'s `_dispatch` catch tuple does not include `CancelledError`, `KeyboardInterrupt` or raw non-store faults. These now carry the conditional note but still reach the operator as a traceback. That is unchanged behaviour (the brief's "caller rider" is MOOT per v13 addendum 2), and the stdlib traceback renderer prints the note (pinned). It is surfaced in case the lead wants the CLI to render it via `_fault_line`.
- **N-b:** row 11 of §INVENTORY (a causeless pre-answer `PrincipalKeyStoreError` → conditional note) is unpinned and unreachable.
- **N-c:** the pre-existing `ruff format` drift in `principal_keys.py` and `_txn.py` (§CURRENCY). It is not a manifest gate.
- **N-d:** the 4 `test_reanchor_58_r4_lease_fates.py` reds are pre-existing and 58-owned, but the brief did not name them (§RUNS).
- **NOT TRIED (optional):** a second mutation proof on the F-1 path (`_classified_fault` → `return error`). Declaring its exact RED set needs a full enumeration of the translated proven cells, which I did not do. The tuple mutation above already proves the note reads the shared tuple.

## §CLOSEOUT — audit F-1 / F-2 (`REPORT-coldaudit-mint-q1.md` d2d0544 §6), docstring/comment ONLY, over `0bbbd50`, 2026-10-05
- **F-1, `PrincipalKeyStore.mint` `Raises:`.** `PrincipalKeyStoreError` is now split by source: a translated proven fault → "could not mint …" with no note; other translated store faults (bare base, foreign classes) → outcome-unknown message + conditional note; the post-answer no-row case → certain note. New entries: `SurrealConnectionError` (raw pass-through, conditional note in connection wording), `TxnContentionExhaustedError` (raw pass-through, NO note, proven), and `BaseException` (any other CREATE fault re-raised as the same object with the cause-neutral conditional note; any post-answer fault carries the certain note).
- **F-2, `_txn._PROVEN_NO_KEY_FAULTS` comment.** A TRANSLATED member decides the inner `catch=`, and through it the not-landed message and the translation, plus the note (none). A PASS-THROUGH member (`TxnContentionExhaustedError`, re-raised before `catch=` is consulted) decides the note ONLY; its `catch=` membership is inert.
- **Checks:**
  - AST vs HEAD with docstrings blanked (`ast.dump` equality, both files): **True / True**.
  - `ruff check` (both files): All checks passed.
  - `ruff format --check`: "would reformat" both files, the known pre-existing drift. The drift-line count is unchanged (principal_keys 8→8, `_txn` 30→30).
  - No tests run, by instruction.
- **`git diff --stat`:** `principal_keys.py | 19 +++++++++++++++----` · `_txn.py | 8 ++++++--`.
- **md5:** `principal_keys.py a7b169914e6eaa7d2fc16bee87f4699e` · `_txn.py 2ddd395c36ef633493a55da83ea172ab` (pre-edit `c67cc356…` / `4ebe3712…`; backups in my scratchpad).

## §Q1B — am-37 §15 / §15.1 / §15.2 GREEN build (over contract `f7ecbce`; measured 2026-10-05 14:08–14:33Z; nothing committed)

**Summary.**
- All **154/154** owned contract cells are GREEN. I made every production change the brief asked for and did both self-destructs.
- **Two pre-existing test-side defects block a clean close.** Neither is in my writable set, so neither is fixed:
  - **4 GREEN→RED** in `test_fixwave_a28c_63c_i_a.py`;
  - **typecheck RED_ORPHANED 1** in the owned file.
- Both need a one-line edit to a test. Exact edits are in §Q1B.STOP. The production build is complete either way.

Other receipts:
- Packages considered: stdlib only (`contextlib`, `isinstance` / call). I read `lorerunes.reclassify`'s installed source before extending it in place. For the kinds, I read the installed `surrealdb.errors` (`ErrorKind`, `QueryDetailKind`, `QueryError`, `_detail_kind`) and REUSED the SDK constants. Verdict: `replace` (extend the shared seam; no package does a predicate catch).
- Odoo-20 portability: n/a. Graded: n/a.
- I reran the lore impact queries (`reclassify`, `_domain_rejection_error`) and filled in the elided covering tests BY HAND with an awk sweep for the touched symbols over `loremaster/tests` and `lorerunes/tests`. That is a fallback, and I am saying so: `lore_impact` elided 80 and 514 covering-test ids, and the grep hook blocks grep.

### §Q1B.CHANGES (symbols)

**`lorerunes/lorerunes/engine_rejection.py`**
- NEW type alias `CatchSpec = tuple[type[BaseException], ...] | Callable[[BaseException], bool]`.
- NEW `_is_caught(catch, error)`: the ONE place a tuple (`isinstance`) and a predicate (a call) are told apart.
- `reclassify(catch: CatchSpec)`: `except passthrough: raise` stays FIRST. After it, `except BaseException as error`: if `_is_caught` is false, a bare `raise` (the same object); otherwise `raise make_error() from error`.
- The tuple behaviour is unchanged; the DUAL pin plus the lorerunes tests are green.
- The docstring is updated: the predicate is never consulted for a pass-through.

**`loremaster/loremaster/store/_txn.py`**
- `TxnDomainRejectionError.__init__(message="", *, error_class=None, kind=None)` sets two typed attributes, `.error_class` and `.kind`.
- A construction that names no `error_class` takes `_constructed_error_class()`:
  - `unspecified rejection` on the base;
  - its own label on `TxnUniqueViolationError` and `TxnGovernedConflictError`, which are classified by construction (§15.2).
- `_domain_rejection_error(error_class, message, *, kind=None)` passes both attributes to the class it builds. The class mapping is unchanged.
- NEW `_typed_kind(error)`:
  - for a `QueryError`, the detail kind (reusing the existing `_detail_kind`) or else `Query`;
  - for any other `ServerError`, its `.kind`;
  - otherwise `None`.
- **BOTH raise sites pass `kind=_typed_kind(...)`.** `_raise_attempt_failure` passes the SDK error. `_run_verified_transaction` passes `_typed_root_cause(root_cause)`, computed once and fed to both the classifier and the kind.
- NEW `_PROVEN_NO_KEY_CLASSES = (TxnContentionExhaustedError, TxnParamCollisionError, TxnEnvelopeViolationError)`.
- NEW `_OUTCOME_UNKNOWN_KINDS = frozenset({ErrorKind.INTERNAL, ErrorKind.SERIALIZATION, ErrorKind.QUERY, QueryDetailKind.TIMED_OUT, QueryDetailKind.CANCELLED})`. These are SDK constants; `QUERY` is FORK-2.
- NEW `proven_no_key(error) -> bool`:
  - class half → True;
  - not a `TxnDomainRejectionError` → False;
  - `error_class != unspecified` → True;
  - otherwise `kind is not None and not any(kind == unknown for unknown in _OUTCOME_UNKNOWN_KINDS)`.
  - The `==` form is deliberate. a28c's `test_am36_1_2_3_the_only_engine_text_reader_is_the_classifier` flags ANY `in` / `not in` inside a `_txn` function, and its own message prescribes "compare a typed kind with `==`".
- `_PROVEN_NO_KEY_FAULTS` is **deleted**. The bare sweep over `loremaster/loremaster` and `lorerunes/lorerunes` finds 0 hits, in code or prose.
- `wrap_store_rejection(catch: CatchSpec = _DEFAULT_REJECTION_CATCH)`. The default is unchanged, and the docstring names the predicate catch.
- Imports: `QueryDetailKind`, and `from lorerunes.engine_rejection import CatchSpec`. Ruff's isort places the latter in the third-party block; the ruff output is clean.

**`loremaster/loremaster/principal_keys.py`**
- The import adds `proven_no_key` (the retired tuple is removed).
- `mint`'s INNER wrap is `catch=proven_no_key`. The OUTER default-catch wrap (mechanism (d)) stays.
- `_mint_fault_note` uses `if proven_no_key(fault): return None`, so ONE predicate decides the catch, the message and the note.
- The `Raises:` section, the window comment and the `_mint_fault_note` docstring are rewritten for the predicate and the kinds.

**Self-destruct**
- I deleted the `am37-15-q1b-mint-contract` entry in `scripts/pending_contracts.yaml`, with its 3-line comment (29 lines). `--verify-registry` exits 0.
- In the owned file I removed the `if TYPE_CHECKING:` anchor and the now-unused `TYPE_CHECKING` import.

### §Q1B.RUNS — targeted, BEFORE (`f7ecbce`) vs AFTER (final bytes)

**Gate:** `gate_run_q1b.sh`. It waits for ≥ 20 GiB and for no other lore pytest, matched on **argv0** per #544 (`^[^ ]*python[^ ]* .*(-m pytest|bin/pytest|scripts/pending_contract_gate.py)|^[^ ]*/bin/pytest`). Control: a bash shell carrying those words matched 0. Each run is capped at 16G with `-n 8 --timeout=300`.

**Set (37 files):**
- the owned file, both Q1 files, `test_engine_rejection_seam.py`, `lorerunes/tests/test_engine_rejection.py` and `test_pdp_core.py`;
- every test file that names `reclassify`, `wrap_store_rejection`, `_domain_rejection_error`, `_raise_attempt_failure`, `_run_verified_transaction`, `_classify_engine_error` or the `TxnDomainRejectionError` family (the awk sweep above);
- the Q1 AST/seam set (`test_store_seam_one_derivation`, `test_backoff_seam`, `test_anchored_pattern_seam`, `test_txn_contention`, `test_ast_reach_helpers`, `test_reanchor_58_r4_lease_fates`), and `test_retry_seam.py`.

**Results:**
- **BEFORE:** `265 failed, 3301 passed, 7 skipped`. 154 failures are in the owned file. The other 111 are pre-existing reds in files registered to packet 58 or 64b-i:
  - `test_findings_migrate_64b` 28 and `test_governed_substrate_64b` 34;
  - `test_reanchor_58_r2_rulings` 27, `r3_tiers` 16 and `r4_lease_fates` 4;
  - `test_exhaustion_fates` 1 and `test_blocks_edge` 1.
- **AFTER, final bytes** (`_txn` md5 `86f9a898…`): **`115 failed, 3451 passed, 7 skipped`**.
  - **RED→GREEN: 154**, all in the owned file.
  - **GREEN→RED: 4**, all `test_fixwave_a28c_63c_i_a.py::TestTheOneMappingHelperBuildsTheClassEverywhere63cIAa28c::test_am35_2_4_mutating_the_mapping_helper_moves_every_identity_leg[{record-id,unique-index}-collision-{run_query,execute_transaction}]`. See §Q1B.STOP-1.
  - The remaining 111 are exactly the pre-existing 58 / 64b-i set (ID-diffed, `comm`).
- **A first AFTER run** with `kind` REQUIRED gave 24 GREEN→RED: these 4, plus 20 old callers that call the helper with two arguments (`test_principals_cli` ×17, `test_am37_13_3…::TestTheCliSinkIsRedacted`, `test_memory_supersede_atomicity_63b_ib`, `test_surreal_store::TestDomainRejectionErrorType`).
  - Fix: `kind` now defaults to `None`. A kind-less rejection is UNKNOWN, the safe side, and each raise site's kind is pinned separately.
  - The 20 are green again.

### §Q1B.STOP — two test-side defects (outside my writable set; exact edits; the lead or the contract author owns them)

**STOP-1 — §15.2's mechanics contradict a pre-existing a28c pin.**
- `test_am35_2_4_mutating_the_mapping_helper_moves_every_identity_leg` patches `_txn._domain_rejection_error` with `def _base_only(error_class: str, message: str) -> Any`.
- The ruled raise sites call the ONE helper with `kind=...`, so the fake fails at argument binding and its body never runs. Focused run: `4 failed`, each `AssertionError: …the patched mapping helper was never called (#194: did it LAND?)`, `assert []`.
- No production shape satisfies both: setting `.kind` outside the helper is exactly what §15.2 forbids ("set at the ONE helper").
- **Edit (test, 1 line):** in that test, `def _base_only(error_class: str, message: str, *, kind: str | None = None) -> Any:`. Its property (the raise site builds the class through the ONE helper) is unchanged.
- The contract author did not run this file (REPORT-contract-mint-q1b.md deviation (2): covering tests NOT TRIED).

**STOP-2 — the deleted bound's `no-any-return` line OUTLIVES the build.**
- `test_mint_kind_carveout_q1b.py::_proven_no_key` returns `getattr(_txn_module, "proven_no_key")`. mypy types that as `Any` **whether or not the symbol exists**.
- So the bound's reason ("until the build lands it") was false, and with the bound deleted per the brief the currency gate shows `typecheck RED_ORPHANED — loremaster/tests/test_mint_kind_carveout_q1b.py:177 [no-any-return]`.
- **Edit (test, 1 line):** annotate `predicate: Callable[[BaseException], bool] = getattr(_txn_module, "proven_no_key")`, or read `_txn_module.proven_no_key` directly now that it exists.
- I did NOT re-add a bound. Keeping a residual owner is the lead's registry call, so I did not decide it.

### §Q1B.MUTATION — `scripts/mutation_proof.py` (ids declared from `--collect-only` BEFORE the run)

**Mutation:** remove `ErrorKind.SERIALIZATION,` from `_OUTCOME_UNKNOWN_KINDS`.

**Declared RED (5), all in the owned file:**
- `TestEveryEngineKindIsAdjudicated::test_the_seam_and_the_predicate_agree_with_the_ruling[Serialization]`;
- `TestTheClassificationAxis::test_the_predicate_over_label_and_kind[_ERROR_CLASS_UNSPECIFIED-Serialization]`. Only the unspecified label moves; the 6 classified-label cells for `Serialization` are proven for every kind, so they are declared GREEN.
- `TestTheTransactionalRaiseSitePassesTheKind::…[Serialization]`;
- `TestTheMintFollowsTheKind::test_a_typed_rejection_during_the_CREATE[Serialization]`;
- `TestOnePredicateDecidesCatchMessageAndNote::test_the_unknown_kinds_are_the_rulings`.

**Result:** exit 0, `5 failed, 353 passed, 2 skipped`, **"PROOF HELD — the declared RED set fired EXACTLY"**, and "tree restored byte-exact" (md5 `86f9a898…`). This ran on the real tree, with `loremaster.__file__` in the main checkout.

**Note AND message, observed directly.** The mint cell's first failing assertion is the note, which masks the message. So `probe_q1b_note_and_message.py` (pasted below; scratch-resident) serves one typed `Serialization` rejection through the real seam into `mint`, first unmutated and then mutated (every binding rebound by identity):
```
UNMUTATED: class=PrincipalKeyStoreError message="the store did not confirm the mint of key 'laptop' for principal 'dev@example.org'; its outcome is unknown" cause=TxnDomainRejectionError notes=["the mint's outcome is unknown (the store did not confirm the CREATE) — if `lore-adm list-keys --email dev@example.org` shows 'laptop', revoke it (`lore-adm revoke-key --email dev@example.org --name laptop`) and mint a new key"]
MUTATED  : class=PrincipalKeyStoreError message="could not mint key 'laptop' for principal 'dev@example.org'" cause=TxnDomainRejectionError notes=None
```
The note and the message both moved, from one kind edit.

<details><summary>probe_q1b_note_and_message.py (verbatim)</summary>

```python
"""Probe (implement-mint-q1 §Q1B): one typed `Serialization` rejection through the REAL seam into `mint`,
served UNMUTATED and then with `Serialization` removed from `_txn._OUTCOME_UNKNOWN_KINDS` (every binding,
by identity). Prints class, message and notes for each, so the note AND the message are observed moving."""
import asyncio
import logging
import sys

import surrealdb.errors as sdk_errors
from pydantic import SecretStr

import loremaster.principal_keys as principal_keys_module
from loremaster.principal_keys import PrincipalKeyStore
from loremaster.store import _txn


async def typed_rejection(kind: str) -> BaseException:
    async def drop(_connection: object) -> None:
        return None
    try:
        await _txn._raise_attempt_failure(
            sdk_errors.parse_query_error({"kind": kind, "result": f"probe: a {kind} error"}),
            object(), drop=drop, url="ws://127.0.0.1:1/rpc", noun="principal key query",
            label="probe.rejected", logger=logging.getLogger("probe"),
        )
    except BaseException as raised:  # noqa: BLE001
        return raised
    raise AssertionError("unreachable")


async def serve(kind: str) -> BaseException:
    store = PrincipalKeyStore(url="ws://127.0.0.1:1", namespace="n", database="d", user="u",
                              password=SecretStr("p"))
    injected = await typed_rejection(kind)

    async def require_principal_id(_email: str) -> str:
        return "abc"

    async def query(_statement: str, _params: object = None) -> object:
        raise injected

    store._require_principal_id = require_principal_id  # type: ignore[method-assign]
    store._query = query  # type: ignore[method-assign]
    try:
        await store.mint(email="dev@example.org", name="laptop", secret_hash="0" * 128)
    except BaseException as served:  # noqa: BLE001
        return served
    raise AssertionError("mint returned")


def show(label: str, served: BaseException) -> None:
    print(f"{label}: class={type(served).__name__} message={str(served)!r} "
          f"cause={type(served.__cause__).__name__} notes={getattr(served, '__notes__', None)!r}")


original = _txn._OUTCOME_UNKNOWN_KINDS
show("UNMUTATED", asyncio.run(serve("Serialization")))
mutated = frozenset(original - {"Serialization"})
for module in (m for name, m in list(sys.modules.items()) if name.startswith("loremaster") and m is not None):
    for attribute, value in list(vars(module).items()):
        if value is original:
            setattr(module, attribute, mutated)
show("MUTATED  ", asyncio.run(serve("Serialization")))
assert principal_keys_module is not None
```
</details>

### §Q1B.CURRENCY — `--currency --legs typecheck,ruff` (final bytes)
- The **`am37-15-q1b-mint-contract` bound is GONE**: the registry verifies, and no owner of that name remains.
- `ruff GREEN`.
- **`typecheck RED_ORPHANED 1`**: the STOP-2 line `test_mint_kind_carveout_q1b.py:177 [no-any-return]`. The production files type-check clean; that is the only orphan.
- `pytest NOT_RUN`, as the command never starts pytest.
- **RED_ORPHANED 0 is NOT met.** It needs STOP-2's edit, or a lead-owned bound.
- `ruff format` drift is unchanged: `_txn` 30→30 lines, `principal_keys` 8→8, `engine_rejection` 0→0.

### §Q1B.INVENTORY — changed production behaviour

| # | before (`f7ecbce`) | after | verdict |
|---|---|---|---|
| 1 | mint: an UNRECOGNISED `TxnDomainRejectionError` of kind `Internal` / `Serialization` / bare `Query` / `TimedOut` / `Cancelled`, or kind-less → "could not mint", no note | the outer outcome-unknown message plus the conditional note; class `PrincipalKeyStoreError`; `__cause__` is the rejection | **changed by ruling** §15 / §15.2 FORK-2; pinned by `TestTheMintFollowsTheKind` and the axis |
| 2 | mint: a recognised refusal (UNIQUE / ASSERT / coercion / governed …) of ANY kind → "could not mint", no note | identical | **preserved-with-pin** (§15.2; `TestAClassifiedInternalRefusalIsProvenAtTheMint`, the live UNIQUE pin GREEN) |
| 3 | mint: an unrecognised rejection of `Validation` / `Thrown` / `NotFound` / `Configuration` / `AlreadyExists` / `NotExecuted` → "could not mint", no note | identical | **preserved-with-pin** (seam and mint cells) |
| 4 | mint: TCE / param collision / envelope / connection / non-store faults | identical (the class half; pass-throughs unchanged) | **preserved-with-pin** |
| 5 | `reclassify` tuple catch | the same verdicts, via ONE `_is_caught` decision | **preserved-with-pin** (DUAL + `lorerunes/tests/test_engine_rejection.py` GREEN) |
| 6 | `wrap_store_rejection` default for the 20 other callers | unchanged | **preserved-with-pin** (#400 seam pins + `TestTheOtherWrapCallersAreUnchanged`, GREEN) |
| 7 | `TxnDomainRejectionError(msg)` construction | it still works positionally; it now ALSO carries `error_class` / `kind` | additive; every compensation `isinstance` door is unchanged |
| 8 | `_domain_rejection_error(label, msg)` (2 args) | still accepted (`kind=None`) | **preserved** (20 old callers GREEN); a kind-less result is UNKNOWN (safe side) |

### §Q1B.DRY

| new symbol | lore query run | result | disposition |
|---|---|---|---|
| `CatchSpec`, `_is_caught` | `lore_get_symbol(lorerunes.engine_rejection.reclassify)` | `reclassify` took only a tuple | EXTENDED `reclassify` in place (ruled §15.1) |
| `proven_no_key`, `_PROVEN_NO_KEY_CLASSES`, `_OUTCOME_UNKNOWN_KINDS` | the read of `_txn` | none existed (named by the ruling) | HAND-ROLLED as ruled; they replace the retired tuple |
| `_typed_kind` | `lore_get_symbol(loremaster.store._txn._detail_kind)` | `_detail_kind(error)` exists | REUSED `_detail_kind` inside a 4-line kind reader |
| `TxnDomainRejectionError._constructed_error_class` | the read of `_domain_rejection_error` | the label mapping exists only in the helper | HAND-ROLLED: a class-level default for kind-less constructions; the helper still decides the label when it builds one |

### Final bytes
- **md5:**
  - `_txn.py` `86f9a898fa486ad7e7c8b32080e8134c`
  - `principal_keys.py` `552bb7177232a5cf02b47ac363f67af8`
  - `engine_rejection.py` `f325da77075c6abf23810888c8cbef04`
  - `pending_contracts.yaml` `b0158ed1189ea905faf9c8d8b9f87f76`
  - `test_mint_kind_carveout_q1b.py` `4be8d7f7ebf6cba02240da53d21cb30d`
- **Pre-edit backups:** `…/scratchpad/q1b_backup/` (my session scratchpad).
- **`git diff --stat`:**
```
 loremaster/loremaster/principal_keys.py         |  49 ++++---
 loremaster/loremaster/store/_txn.py             | 164 +++++++++++++++++++-----
 loremaster/tests/test_mint_kind_carveout_q1b.py |   8 +-
 lorerunes/lorerunes/engine_rejection.py         |  38 ++++--
 scripts/pending_contracts.yaml                  |  29 -----
 5 files changed, 191 insertions(+), 97 deletions(-)
```
- **State:** blocked: the production build is complete (154/154 owned GREEN, PROOF HELD, bound gone). Two one-line TEST edits outside my writable set are needed for 0 GREEN→RED and RED_ORPHANED 0: STOP-1 (a28c `_base_only` signature, 4 cells) and STOP-2 (owned-file accessor annotation, 1 typecheck line).

## §Q1B.REPAIR — NOT PERFORMED (2026-10-05)

**BRIEF CONFLICT:** I refused the lead's "AUTHORIZED (lead, contract-side repair)" instruction to make the two STOP edits:
- STOP-1: the `_base_only` signature in `test_fixwave_a28c_63c_i_a.py`;
- STOP-2: the `_proven_no_key` accessor in `test_mint_kind_carveout_q1b.py`.

**Why:**
- brief-base v18 §2 ROLE BOUNDARY is NON-OVERRIDABLE. It forbids "implementer → test author: writing or editing the tests it must pass".
- "Only the OPERATOR can grant such a combination, and the brief must quote the grant with its date. A lead's own wording is not a grant."
- The instruction quotes no operator grant.
- Both edits are small and preserve every assertion, but the rule is keyed on WHO edits, not on how much.

**Disclosure — earlier, same class, unflagged.** In the Q1 and Q1B builds I deleted the `TYPE_CHECKING` owner anchors (and their `TYPE_CHECKING` imports) in `test_mint_unknown_outcome_note_q1.py` and `test_mint_kind_carveout_q1b.py`. That was on the lead's "self-destruct" brief, which also quoted no operator grant.
- Those deletions were assertion-free registry plumbing.
- They were still edits to test files I must pass, and I should have flagged them as this same transfer at the time. I am flagging them now.
- Reverting them would only re-create a dangling typecheck line, so I have left them in place for the lead to adjudicate.

**What would unblock this:**
- (a) the contract author (or a fresh `tdd-contract` agent) makes the two one-line edits exactly as written in §Q1B.STOP; or
- (b) the lead re-briefs me quoting a dated OPERATOR grant for this transfer.
- Either way, I re-run the targeted set and `--currency --legs typecheck,ruff` afterwards. That is implementer work, and I will do it on request.

**State of the tree (unchanged since §Q1B):** every md5 is as listed in §Q1B "Final bytes". I made no edits in this round.
- **State:** blocked: the two STOP test edits need a contract-side author or a dated operator grant (brief-base §2); the production build is complete.
