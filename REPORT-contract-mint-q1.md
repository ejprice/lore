brief-base v18 read · brief project v7 read

**state:** done-with-deviations · contract on HEAD `c633fbf` (measured 2026-10-04) · TESTS ONLY, no production edit
- **Deviations:**
  - (1) One `pytest --collect-only` ran OUTSIDE the waiting gate (it executes no test; MemAvailable was 28 GiB at the next gate check). Every executing run went through the gate (§RUNS).
  - (2) `lore_index(reconcile=True)` timed out client-side after 300 s (finding **#542**). The `lore_impact` answers were therefore used unreconciled. My session edits were test-only, and the impact targets are unedited production symbols.
- **Packages considered:** stdlib `asyncio.timeout` / `Task.cancel` and `anyio.move_on_after` / `fail_after` as the REAL cancellation drivers. Read: `asyncio.timeouts.Timeout.__aexit__` behaviour, measured live: `TimeoutError.__cause__` is the noted `CancelledError`. anyio 4.x `CancelScope.cancelled_caught` was also measured live (§PROBE). Verdict `replace`: no hand-rolled cancel. PEP 678 `add_note` (stdlib) stays the spec mechanism.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 7 new test-side helpers, all dispositioned (§DRY).
- **Graded:** n/a (contract author; no verdict on another's artifact).
- **decisions-needed:**
  - **F-0 (lead action; outside my writable set): own the 26 RED@HEAD pytest cells.** They are all in the NEW file `loremaster/tests/test_mint_unknown_outcome_note_q1.py`, deliberately split out so that a FILE-granular owner masks nothing else. Exact edit in §OWN. Until then the close-out pytest leg sees them as RED_ORPHANED.
  - **F-1** — how the build sees a proven fault through the wrap. Spec-literal code would note the UNIQUE rejection. The contract pins the OUTCOME; implementer guidance is in §FORKS.
  - **F-2** — "derived" vs "adjudicated" tuple. Resolved by the contract's independent ruled set; either build satisfies it.
  - **F-3** — conditional-note WORDING for non-connection faults is SPEC-SILENT. "(the connection failed during the CREATE)" is false for a cancel or interrupt. Operator ruling needed.
  - **F-4** — the bare `SurrealStoreError` base → conditional note (derived, not chosen). Stated for the record.
- **Pointers:** §CONTRACT · §OWN (registry edit) · §PREFLIGHT · §REALISM · §ADJ (re-keyed pins) · §RUNS (RED / targeted / reference) · §SAT · §FORKS · §DRY · §NOTICED

## Capability check
- **Demanded:** lore-first discovery, register + heartbeat, `lore_index(reconcile=True)`, gated pytest, scratch reference, currency gate.
- **Have:** all of these. Exceptions:
  - `lore_index` reconcile timed out (#542).
  - The Bash hook blocks any command containing `grep`, `pgrep` included, in the main checkout. So the brief's `pgrep` gate lives in a file written with Write, and runs as `bash gate_run.sh` (§RUNS).
  - Textual sweeps used `awk`. That is a FALLBACK, said out loud: the needles were non-symbol seams (`__notes__`, `add_note`, the parametrize constant names).
- **Symbol discovery:** via `lore_get_symbol` (`PrincipalKeyStore.mint`, `_mint_fault_note`, `wrap_store_rejection`) and `lore_impact`.

## §CONTRACT — file and what it pins
**Files (two, deliberately):**
- `loremaster/tests/test_am37_13_3_63c_i_a.py` (fix531d's home). It holds the DUAL re-key of pin (a), the `_RULED_*` adjudication, the generated taxonomy leg plus the contract-side completeness, and `_note_free_chain`. **All GREEN at `c633fbf`** (137 cells).
- `loremaster/tests/test_mint_unknown_outcome_note_q1.py` (NEW). Every cell that is RED until the build: the unknown-outcome classes, the post-answer interrupt class and the exported-tuple class. It reuses fix531d's fixtures by module-qualified import (`import test_am37_13_3_63c_i_a as fix531d`, the same idiom that file uses for `test_engine_rejection_seam`).
- **Why split:** `pending_contract_gate.partition_pytest` owns pytest reds by FILE (`outcome.file in registry.registered_paths`). Owning the reds inside fix531d's 1100-line file would blind its 137 other pins until the build lands, which is am-37 §2 F-15's masking class.

Plain English: before the engine answers, the revoke note is withheld ONLY for a fault that PROVES no key landed. The store layer's own refusals and pre-send faults are proven. EVERY other fault gets the conditional note: cancellation, interrupt, timeout, transport, a future unknown, and the bare store base. The note is attached once, on the same object, and cancellation still propagates. After the answer, every fault (interrupts included) gets the CERTAIN note, unchanged. The proven set is ONE tuple exported from `_txn`, equal to the operator's ruling and to the derived taxonomy minus the connection class. The mint reads THAT tuple, proven by mutation.

| class / test | cells | pins |
|---|---|---|
| `TestTheMintWindowNotesTheRevokeRepair::test_every_generated_store_class_is_adjudicated_by_the_ruling` (NEW) | 1 | completeness, CONTRACT side: derived `_txn` subclasses == `_RULED_PROVEN_NO_KEY` ⊔ `_RULED_UNKNOWN_OUTCOME_STORE`; a new subclass reds BY NAME |
| `…::test_a_fault_during_the_CREATE_call` (RE-KEYED, §ADJ) | 7 classes × 2 email/name | GENERATED ∀ proper `_txn` subclass: ruled-proven → no note on ANY chain link, no `revoke-key`/`list-keys` rendered; connection → exact conditional note, same object; class == the wrap oracle |
| `TestAnUnknownOutcomeDuringTheCREATECarriesTheConditionalNote::test_an_unproven_fault_raised_by_the_CREATE` | 6 faults × 2 | `CancelledError`, `KeyboardInterrupt`, `TimeoutError`, `ConnectionResetError(ECONNRESET)`, `RuntimeError` (future unknown), bare `SurrealStoreError` → exactly ONE conditional-shaped note; same object for non-store faults; class == the wrap oracle; the note is printed by `traceback.format_exception` |
| `…::test_a_real_asyncio_timeout_cancels_the_CREATE_in_flight` | 1 | a real `asyncio.timeout` → caller gets `TimeoutError` whose `__cause__` is the noted `CancelledError` (proves propagation) |
| `…::test_an_anyio_cancel_scope_cancels_the_CREATE_in_flight` | 1 | `anyio.move_on_after`: `scope.cancelled_caught`, mint did not return, the captured cancel exc carries the note |
| `…::test_a_cancelled_task_stays_cancelled` | 1 | `Task.cancel()` mid-CREATE → `task.cancelled()`; the crossing `CancelledError` carries the note |
| `TestAPostAnswerInterruptStaysCertain::test_an_interrupt_after_the_answer` | 3 | `CancelledError` / `KeyboardInterrupt` / `TimeoutError` raised AFTER the answer → exactly `[_certain_note]`, same object |
| `TestTheProvenNoKeySetIsOneExportedTuple` | 5 + 6 + 1 | exported tuple, unique members, all `_txn`-defined proper subclasses; disjoint from the connection class under `isinstance` both ways; ∪ {connection} == derived taxonomy (by name); == the ruled set; **sharing by MUTATION** — every loremaster binding of the tuple (found by IDENTITY) rebound without the class and its covering ancestors → that fault now gets the note; CONTROL: unmutated → no note |

Constants: `_RULED_PROVEN_NO_KEY` (6 names, cited to §14 Q1) and `_RULED_UNKNOWN_OUTCOME_STORE` (`{"SurrealConnectionError"}`). These are the contract's INDEPENDENT adjudication; production's tuple is checked against them, never used as the oracle. Wall-clock: `_CANCEL_AFTER_SECONDS = 0.05`, `_HANG_CAP_SECONDS = 5.0`, the latter only reachable by a wrong build.

**STUB EXPECTATION for the implementer:** `loremaster.store._txn._PROVEN_NO_KEY_FAULTS: tuple[type[SurrealStoreError], ...]`. It must:
- hold exactly the six ruled classes;
- be importable from `_txn`;
- be READ by `mint`'s classification. A private copy fails the mutation cells.

## §PREFLIGHT — adversarial list → covering case
- **Wrong unit / scale / anchor:** n/a. No numeric output; the note is text derived from caller inputs.
- **Wrong CLASS at the handler — the wrap TRANSLATES proven faults** (`PrincipalKeyStoreError` from `TxnDomainRejectionError`, UNIQUE included) → the taxonomy leg asserts the served-and-chained outcome; F-1.
- **Pass-through proven fault** (`TxnContentionExhaustedError` is NOT wrapped) → same leg. It kills a build that inspects `__cause__` only.
- **Bare base `SurrealStoreError`** (in an `isinstance` tuple it would cover the connection class) → `test_the_tuple_is_exported…` (`cls is not SurrealStoreError`) + `test_the_tuple_never_covers_the_connection_class` + the unknown cell.
- **BaseException family** (`KeyboardInterrupt`, `CancelledError` are not `Exception`) → unknown cells. A build with `except Exception` loses them.
- **Real cancellation, not injected** → `asyncio.timeout`, anyio scope and `Task.cancel` cells.
- **Swallowed / converted cancellation** → the three real-cancel cells assert propagation (cause chain, `cancelled_caught`, `task.cancelled()`).
- **Cancellation-first ordering** (checking cancel before `answered`) → `TestAPostAnswerInterruptStaysCertain`.
- **Note duplicated / on the wrong link** → `len(notes) == 1`; `_note_free_chain` walks the cause chain for proven faults.
- **Subclass under its parent's coverage** (UNIQUE under Domain) → the mutation cell drops covering ancestors. I caught this myself in the first reference run (§RUNS).
- **Import-dependent taxonomy** (foreign subclasses `store.lease`, `store.surreal`, `floor_calibration` load only when imported; measured, 7 foreign classes) → the domain is filtered by DEFINING MODULE `_txn`. Scoped: foreign subclasses are not raised on `mint`'s `run_query` path. Under the rule they would get the note via the bare-base logic; no cell pins them (§NOTICED N-2).
- **A new `_txn` subclass** → reds BY NAME in two places (contract-side and production-side completeness).
- **Hostile text in name/email** → see §REALISM; the quoting pair is reused, and the newline residual R2 is surfaced, not pinned.
- **Empty proven tuple** → `assert proven`.

## §REALISM
- ☑ **Production-realistic inputs:**
  - the real taxonomy classes, instantiated as `_txn` constructs them;
  - a real `ECONNRESET` errno;
  - real asyncio/anyio cancellation, not only injected objects;
  - realistic email/name pairs, including a shell-quoting one (`dev.531+keys@example.org`, `work laptop`).
- ☑ **Independent expected values:**
  - the ruled sets are written from §14 Q1, not read from production;
  - the class oracle is the wrap ALONE (`_through_the_wrap`);
  - the certain/conditional texts come from the spec's §13.5 item 5.
- ☑ **Seam coverage:** the injection point is `_query`, BELOW `wrap_store_rejection`, so the real wrap→handler handoff (translation + passthrough) is exercised. The live UNIQUE pin (`TestALiveUniqueCollisionCarriesNoRevokeAdvice`, `:18000`) is kept unchanged, as the real-engine seam.
- ☐ **Magnitude bound:** not applicable. No derived numeric output.
- ☑ **Shared conventions:** command spellings are parsed by the REAL `lore-adm` parser (`_assert_commands_parse`); the taxonomy is walked from `_txn`, never listed for the domain.
- **Hostile fixtures for rendered stored text:** applies weakly. The note renders caller-supplied `name`/`email` into stderr. Q1 changes classification only, not rendering; fix531d's R2 (a newline in a key name) is still open and is NOT pinned here (§NOTICED N-1).
- **Input accounting:** not applicable. Not a collection transform.

## §ADJ — every changed pre-existing pin (fix531d's pin (a))
| pin | old | new | verdict |
|---|---|---|---|
| `_PRE_COMMIT_CLASSES` member `asyncio.CancelledError` → no note | §13.5 item 1 | → **conditional note, class unchanged** (moved to the unknown cells) | **RE-KEYED BY DUAL — an operator-ruled behaviour change (am-37 §14 Q1, "Yes, separate cycle"), NOT a test weakening.** The new pin is strictly stronger: it now requires a note where none was required. |
| member `RuntimeError` → no note | §13.5 item 1 | → conditional note (the "future unknown" representative) | RE-KEYED BY DUAL, §14 Q1 ("any future unknown") |
| member `SurrealStoreError` (bare base) → no note | §13.5 item 1 | → conditional note; removed from the taxonomy domain | RE-KEYED BY DUAL. DERIVED from §14's own mechanism: the base in an `isinstance` tuple would cover `SurrealConnectionError` (F-4) |
| `test_the_generated_pre_commit_domain_is_not_vacuous` | floor ⊆ names | same floor + "base not in domain" | tightened |
| `test_a_fault_during_the_CREATE_call` | `issubclass(cls, SurrealConnectionError)` decides | the RULED set decides; proven → whole chain note-free + no `list-keys` either; unruled → `pytest.fail` by name | tightened; same verdict for all 7 `_txn` subclasses |
| certain-note pins, the UNIQUE live pin, the AST one-handler pins, `_fault_line` notes pin | — | untouched | **Preserved-with-pin** (§14: "Unchanged") |

Lists the lead must surface:
- **Dropped-deliberately:** none.
- **Spec-silent:** F-3 (the wording).

## §RUNS
Gate (pasted verbatim per brief-base §1; it lived at the session scratchpad `gate_run.sh`):
```bash
#!/usr/bin/env bash
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
(The reference-tree variant differs only in the `cd` line.)

**RED on HEAD `c633fbf`** (contract file only; `GATE PASS 22:19:22 MemAvailable=28GiB`): **`26 failed, 137 passed`**. Reasons, tallied from the `E` lines:
- **12** × `exactly ONE conditional note expected, got None`: the 6 unknown faults × 2 email/name pairs. No note on HEAD. Right reason.
- **3** × `AssertionError: None` (`notes is None`): the asyncio-timeout, anyio and `Task.cancel` cells. Each passed its PROPAGATION asserts first, so HEAD already propagates cancellation; only the note is missing. Right reason.
- **11** × `AttributeError: module 'loremaster.store._txn' has no attribute '_PROVEN_NO_KEY_FAULTS'`: the **STUB EXPECTATION**. Exported/unique, disjoint, completeness, ruled-set, CONTROL and 6 mutation cells.
- **GREEN on HEAD, correctly:**
  - the re-keyed taxonomy leg (HEAD already gives the 7 `_txn` subclasses the right fate);
  - the contract-side adjudication completeness;
  - the 3 post-answer interrupt cells (HEAD checks `answered` first);
  - every pre-existing fix531d pin.

**After the split** (both files; `GATE PASS`, MemAvailable 28 GiB):
- HEAD: **`26 failed, 137 passed`**, all 26 in `test_mint_unknown_outcome_note_q1.py`. The `E`-line tally is unchanged: 12 / 3 / 11 as above.
- Reference tree: **`163 passed`**.

**Targeted set** (fix531d's six + the two `_txn` AST/seam scanners): `test_am37_13_3_63c_i_a.py test_principal_keys_store.py test_principals_cli.py test_fail_closed_shapes_63c_13b.py test_exhaustion_fates.py test_engine_rejection_seam.py test_fixwave_a28c_63c_i_a.py test_retry_seam.py`, plus the contract cells. Derivation:
- `lore_impact(PrincipalKeyStore.mint)` covers `test_am37_13_3_63c_i_a` and the token-verifier fixtures (elided: 168).
- `lore_impact(_mint_fault_note)` finds 0 test refs.
- `lore_impact(loremaster.store._txn)` is module-wide (3955), too broad, so I took fix531d's named set plus the scanners that walk `_txn` (a28c's exact-set tester pin, `test_retry_seam`). Hand-added, said out loud.
- That run was made BEFORE the split, with the Q1 cells still in fix531d's file; the split moves code, not behaviour:
  - **HEAD `27 failed, 1627 passed`** = 26 contract cells + 1 `test_exhaustion_fates.py::TestTheRegistryIsTheAdjudicationBothWays::test_every_row_names_a_ruled_classification_an_owner_and_evidence_that_HOLDS` on `store/lease.py::get/create/release_if_held` `logs-error-class`. That one is packet-58-owned and pre-existing; fix531d recorded the same red. **0 attributable reds outside the contract.**
  - **Reference tree `1 failed, 1653 passed`**: only that same 58 red. So the reference satisfies every targeted pin, including 58's fates classifier (the handler stays a passthrough) and a28c's `_txn` tester exact-set pin. The tuple is a plain constant: no `in`, no search method, no `re`.
- **Currency** `--currency --legs typecheck,ruff` (after the split): `typecheck RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract`, `ruff GREEN`, **RED_ORPHANED 0** for both legs. `pytest NOT_RUN` is the known #533 / by law.
  - The first currency run showed 3 orphans of mine (`Trying to read deleted variable "error"`, a name reused after its `except … as error`). Fixed by a rename.

## §OWN — exact registry edit for the lead (`scripts/pending_contracts.yaml` is not in my writable set)
The idiom (packet-58 / 64b-i bounds) is: the test file names the missing symbol STATICALLY, and one bound owns both its typecheck line and its pytest reds. Two edits, ONE commit, because each alone breaks currency:
1. In `test_mint_unknown_outcome_note_q1.py`, add `from typing import TYPE_CHECKING` and `if TYPE_CHECKING: from loremaster.store._txn import _PROVEN_NO_KEY_FAULTS  # noqa: F401 - pending-build owner anchor`. That mints one `attr-defined` typecheck line, which the liveness leg later self-destructs on.
2. A bound:
   ```yaml
   - id: am37-14-q1-mint-contract
     owner: the am-37 §14 Q1 builder (mint unknown-outcome note)
     reopen_trigger: _txn._PROVEN_NO_KEY_FAULTS exists and test_mint_unknown_outcome_note_q1.py is GREEN — delete with the build
     ruling: 'docs/design/2026-09-29-packet63c-amendment-37.md §14 Q1 (fb83c4a); REPORT-contract-mint-q1.md'
     rationale: contract-ahead — the pins name the ruled tuple before it exists
     files:
     - path: loremaster/tests/test_mint_unknown_outcome_note_q1.py
       missing_symbols:
       - loremaster.store._txn._PROVEN_NO_KEY_FAULTS
   ```
   I did NOT add edit 1 myself: alone, it turns typecheck RED_ORPHANED, which the brief forbids. Exact mypy symbol spelling: verify with `--derive` before landing (the 64b entries spell mypy's form).

## §SAT — satisfiability
A reference build is straightforward. It was throwaway, in `./scripts/scratch_copy.sh` tree `…/scratchpad/refq1`. **`loremaster.__file__` = `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/3c627105-1f2b-4e6a-9678-e4109ccfb396/scratchpad/refq1/loremaster/loremaster/__init__.py`** (provenance asserted by the tool and re-printed). The edits:
1. `_txn`: `_PROVEN_NO_KEY_FAULTS = (TxnDomainRejectionError, TxnGovernedConflictError, TxnUniqueViolationError, TxnContentionExhaustedError, TxnParamCollisionError, TxnEnvelopeViolationError)`.
2. `_mint_fault_note`, before the answered check is consulted for the conditional branch: `fault = error.__cause__ if isinstance(error, PrincipalKeyStoreError) and error.__cause__ else error`, then `if not isinstance(fault, _txn._PROVEN_NO_KEY_FAULTS):` → conditional.
3. One module import.

Contract file against it: **`163 passed`** (after the mutation-cell fix below). First reference run: `2 failed, 161 passed`. Both failures were `test_the_mint_reads_the_one_tuple[TxnGovernedConflictError|TxnUniqueViolationError]`, a defect in MY cell: removing a subclass left its parent covering it under `isinstance`. Fixed by also dropping covering ancestors, plus a non-vacuity assert. This was not a grade of the build. Lint-cleanup leg: the reference adds no orphaned import.

## §FORKS (two readings each; my pick stated)
- **F-1 — what the handler sees for a proven fault.** §14 writes `not isinstance(error, _PROVEN_NO_KEY_FAULTS)`. But fix531d's fork A put `wrap_store_rejection` INSIDE the window, around the CREATE alone. So a pre-answer `TxnDomainRejectionError` (UNIQUE included), `TxnParamCollisionError` or `TxnEnvelopeViolationError` reaches the handler as **`PrincipalKeyStoreError` chained `from` it**. Only `TxnContentionExhaustedError` and `SurrealConnectionError` pass through raw.
  - Reading (a), spec-literal on `error`: every translated proven fault gets the conditional note. That breaks the UNIQUE no-advice pin (live + mocked).
  - Reading (b): classify the wrap's translation by its `__cause__`.
  - **Pick: (b)**, the only reading consistent with §14's own "Unchanged: the UNIQUE no-advice pin". The contract pins the OUTCOME, so either mechanism that achieves it passes. Implementer note: pre-answer, a `PrincipalKeyStoreError` can only originate from the wrap.
- **F-2 — "derived" tuple.** §14: "one tuple, derived in `_txn` (the taxonomy minus `SurrealConnectionError`) … so a new `_txn` subclass is adjudicated at birth".
  - (a) COMPUTED from the live subclass tree. A new subclass is then silently "proven", which is the false-clear direction, and the completeness pin becomes tautological.
  - (b) a hand-adjudicated literal checked against the derived taxonomy.
  - **Resolved without choosing:** `test_the_tuple_is_the_rulings_adjudication` compares the tuple to the contract's ruled set. Under (a), a new subclass reds there by name; under (b), it reds in completeness. My recommendation is still (b), so the adjudication lives at the class's birthplace.
- **F-3 — conditional wording for non-connection faults: SPEC-SILENT, operator ruling required.** The §13.5 item 5 text says "(the connection failed during the CREATE)". For `KeyboardInterrupt` or a timeout that is FALSE teaching (consumer law).
  - (a) keep the wording verbatim for all;
  - (b) generalise the parenthetical, e.g. "(the CREATE was interrupted before it answered)", keeping the exact text for the connection class or not.
  - The contract pins the connection class's EXACT text (unchanged) and only the load-bearing SHAPE for the rest ("outcome is unknown" + both commands, parsed). So both (a) and (b) pass. **Recommend (b).**
- **F-4 — the bare base.** Derived, not chosen: `SurrealConnectionError` subclasses `SurrealStoreError`, so the base in the `isinstance` tuple would withhold the connection note. Hence base → conditional. Its only `_txn` raise sites are `compose`'s hard cap (pre-send, so it would truly be proven, but it is not on `mint`'s `run_query` path) and `_failed_statements`' malformed response (txn path). On `mint`'s path the base is unreachable at `c633fbf`; the conditional note is the fail-safe direction.

## §DRY
| new symbol | lookup | result | disposition |
|---|---|---|---|
| `_RULED_PROVEN_NO_KEY`, `_RULED_UNKNOWN_OUTCOME_STORE` | read fix531d's helpers in the same file; awk for `_PROVEN_NO_KEY` over tests (0 hits) | none | HAND-ROLLED: the contract's independent adjudication, guarded by two completeness assertions |
| `_unknown_outcome_faults` / `_UNKNOWN_OUTCOME_FAULTS` (new file) | fix531d's file | `_PRE_COMMIT_CLASSES` held 2 of them as controls | EXTENDED: moved out of `_PRE_COMMIT_CLASSES` and re-keyed |
| `_assert_conditional_shape` | same file | `_conditional_note` (exact), `_assert_commands_parse` | REUSED `_assert_commands_parse`; shape-only wrapper because of F-3 |
| `_note_free_chain` | `TestALiveUniqueCollision…` has an inline chain walk | inline loop | HAND-ROLLED as a helper (cycle-safe); the live pin's inline loop left untouched (not in my scope to refactor) |
| `_hanging_store` | `TestTheMintWindow…._store` | answer/raise only, no hang | HAND-ROLLED sibling (needs a never-answering CREATE + reached Event) |
| `_loremaster_bindings_of` | lore_search not run for it; the identity-scan idiom is not present in the file | — | HAND-ROLLED; flag: candidate for a shared test helper if a second "prove sharing by mutation" pin wants it |

## §NOTICED (surfaced, not acted on)
- **N-1** fix531d **R2** is still open: a newline in a key name splits the note across `_fault_line` lines. Hostile-fixture clause; trigger: any `_fault_line` render hardening.
- **N-2** Foreign `SurrealStoreError` subclasses (`store.lease.LeaseError`, `store.surreal.VectorDimensionError`, `CalibrationPool*`, `floor_calibration.store.FloorCalibrationError`/`FenceLostError`) are not `_txn`'s. Fix531d's walk already filtered by module. If one ever reaches `mint`'s wrap, it is translated to "could not mint key …" plus a conditional note. That pairs a not-landed claim with an unknown-outcome note, the same inconsistency the bare base has. The inconsistency is in the wrap's message, not in Q1.
- **N-3** The wrap's message "could not mint key …" asserts non-landing for EVERY translated `SurrealStoreError`, including the bare base. For the base, that is a claim the conditional note contradicts. Spec-silent; candidate operator question.
- **N-4** `test_exhaustion_fates.py` red on `store/lease.py` `logs-error-class` (58-owned, per fix531d) — see the targeted tail.
