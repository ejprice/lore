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
