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

## §R2 — round 2 (lead rulings F-1/F-2/F-4, operator rulings F-3 + N-3, 2026-10-05; base `d27a0ce`, production identical to `c633fbf`)
- **State:** done-with-deviations (r2 + the N-3 landing, measured 2026-10-05 at HEAD `8cf6edd`, production == `c633fbf`).
  - **F-3:** pinned as a CAUSE-NEUTRAL property.
  - **N-3:** LANDED under mechanism **(d)**, in the owned file (§R2.N3-LANDED).
  - **§OWN:** landed; typecheck RED_ADJUDICATED to `am37-14-q1-mint-contract`, **RED_ORPHANED 0**.
  - **HEAD:** **43 RED, all in the owned file, all for the right reason.**
  - **Reference ref-D:** **202 passed, 2 skipped** on both files; on the targeted set its only red is the pre-existing 58 row, and the #400 pin is GREEN.
  - **Ruling-channel conflict, resolved toward the DURABLE record:**
    - the native message (lead, received ≈02:45Z) said N-3 = option (a) plus a caller rider;
    - the newer committed lead record `8cf6edd` (REPORT-lead-63c.md v13 addendum 2, ≈03:00Z) re-rules to **(d)**, marks the rider MOOT, and adds "the outer message must be CAUSE-NEUTRAL".
    - I implemented (d). Reading (a) would redden #400's `…[principal_key-mint]` pin, which is outside my writable set. If (a) was really meant, say so; its pins differ in one assertion (untranslated `served is injected` for unproven store faults) plus a DUAL re-key of that #400 cell.
  - **Decision applied (two readings written):** the lead's cause-neutral correction names the OUTER MESSAGE. I applied the same reason to the NOTE's parenthetical: the operator's example "interrupted before the store answered" is false for a malformed-response bare base, which gets the conditional note under F-4. So `interrupt` and `answered` joined `_FAMILY_CAUSE_WORDS`. The alternative reading (note keeps the operator's example) is a one-line revert of the tuple.
  - **Earlier deviation:** a transient lint-probe file in `loremaster/tests/`, deleted in the same command.
  - **Decisions needed:** none blocking. The (a)-vs-(d) confirmation above is the only open one.
### §R2.STOP — N-3: the wrap's other callers (brief: "STOP and report its other callers before pinning")
`lore_impact(loremaster.store._txn.wrap_store_rejection)`, measured 2026-10-05 at `d27a0ce`: **21 production references**. The direct consumers, verbatim:
- `audit.AuditStore.append`
- `keeps.KeepStore.{add_household_member, create_keep, delete_keep, get_or_create_keyed, list_keeps_for_member, remove_household_member, set_keeper, set_rank}`
- `principal_keys.PrincipalKeyStore.{mint, revoke}`
- `principals.PrincipalStore.{create, delete, set_expires, set_status, set_subject}`
- `principals._migrate_message_owner`

(lore's caveat: the profile rode the bare-name channel; it is a heuristic, so it may undercount and never overcounts consumers of this name.)

**What this means for N-3:** the not-landed message ("could not mint key …") is built by the shared wrap translating EVERY non-passthrough `SurrealStoreError`, the bare base and the foreign subclasses included. Fixing N-3 at the wrap changes the translation fate for all 21 sites, and that is outside Q1's ruling.

**A mint-scoped design exists**, which is why I am surfacing it rather than declaring N-3 blocked. It is the operator's call:
- (a) **widen the ONE seam:** give `wrap_store_rejection` an optional `catch=` (default `(SurrealStoreError,)`, so the 20 other sites are byte-unchanged). `mint` passes `_PROVEN_NO_KEY_FAULTS`. A non-proven store fault then passes through UNTRANSLATED: no "could not mint" claim, and the conditional note decides from the same tuple. One taxonomy binding, one tuple deciding both note and message.
- (b) `mint` calls `lorerunes.reclassify` directly with the tuple. REFUSED by me: it is a second binding of the surreal taxonomy, beside the wrap whose docstring says it is "the single place the surreal taxonomy is named" (ROUTING-IS-NOT-SHARING).
- (c) change the shared wrap for everyone. Outside the ruling.

**Recommendation SUPERSEDED by §R2.STOP-2, which recommends (d).** (a) reddens a #400 pin. The N-3 pins are DRAFTED in scratch (not in the repo, per the STOP) and ready to land the moment (a) or another reading is ruled. Their property and wrong-build list are in §R2.N3-DRAFT.

### §R2.F3 — operator F-3 (GENERALISE), pinned as a property, in the OWNED file
- `_FAMILY_CAUSE_WORDS = ("connection", "cancel", "timed out", "timeout", "keyboard")`. `interrupt` is deliberately absent, because the operator's own example uses it generically.
- `_assert_conditional_shape` is used by EVERY non-connection conditional cell: the 6 injected faults, the 3 real-cancel cells and the 6 mutation cells. It now also asserts:
  - `note != fix531d._conditional_note(email, name)`;
  - no family word appears (case-insensitive);
  - plus, unchanged: "outcome is unknown", not LIVE, both commands parsed by the real parser.
- NEW `test_every_non_connection_fault_gets_ONE_parenthetical[plain|needs-quoting]`: all six non-connection faults give an IDENTICAL note for a given key. This is the ruling's "ONE parenthetical TRUE for all".
- The connection class keeps its EXACT text, in fix531d's file (`test_a_fault_during_the_CREATE_call[…-SurrealConnectionError]`, unchanged, green on HEAD).
- **Wrong builds it kills (by inspection, not by building them, per the role boundary):**
  - connection text kept for all → the `!=` and the `connection` ban fail on every non-connection cell;
  - per-family texts, e.g. "(the CREATE was cancelled)" → the sameness cell fails, and so does the `cancel` ban;
  - a build that drops the commands → the parse check fails.
- **Bound, stated:** the property bans the five family words and nothing else. A generic parenthetical that is false some other way (e.g. "(the engine refused)") passes. Semantic truth beyond those named causes is not mechanically checkable, and the operator's example text is not pinned as a string, per the ruling's "a property, not one string".

### §R2.F1/F2/F4 — lead rulings, implementer guidance (the pins already admit them)
- **F-1 (b):**
  - classify a pre-answer `PrincipalKeyStoreError` by its `__cause__`;
  - pre-answer, that class can only originate from the wrap;
  - `TxnContentionExhaustedError` and `SurrealConnectionError` pass through raw and are classified as themselves.
- **F-2 (b):** a hand-adjudicated tuple literal in `_txn`, beside the classes. The contract checks it against BOTH the derived taxonomy and the ruled set, so a computed tuple would still pass mechanically: say so to the builder; the literal is the ruling, the pins are its guard.
- **F-4:** bare base → conditional (pinned since r1).

### §R2.OWN — done (lead-authorized)
1. `test_mint_unknown_outcome_note_q1.py`: a runtime-inert `if TYPE_CHECKING: from loremaster.store._txn import _PROVEN_NO_KEY_FAULTS  # noqa: F401` with an owner-anchor comment.
2. `scripts/pending_contracts.yaml`: bound **`am37-14-q1-mint-contract`**, one file, `missing_symbols: [loremaster.store._txn._PROVEN_NO_KEY_FAULTS]`. The spelling was verified by `--derive`, which printed exactly that entry for the file.

Receipts:
- `--verify-registry` exit 0.
- `--currency --legs typecheck,ruff`:
  - **`typecheck RED_ADJUDICATED — 84 residual(s)`** (83 → 84; the new line is listed under owner **`am37-14-q1-mint-contract`** beside packet-58 / 64b-i);
  - **`ruff GREEN`**;
  - **RED_ORPHANED 0** for both legs; `pytest NOT_RUN` by law.
- **Every NEW red cell lives in the owned file:** HEAD run, 28/28 failures in `test_mint_unknown_outcome_note_q1.py`, 0 in fix531d's file.

### §R2.RED — on HEAD `d27a0ce` (production == `c633fbf`), both repo files, `GATE PASS`
**`28 failed, 137 passed`**; all 28 in the owned file. `E`-line tally:
- 12 × `exactly ONE conditional note expected, got None`: the 6 unknown faults × 2 keys;
- 3 × `AssertionError: None`: the real-cancel cells, past their propagation asserts;
- 11 × `AttributeError … '_PROVEN_NO_KEY_FAULTS'`: the STUB;
- **2 NEW** × `AssertionError: ('CancelledError', [])`: the F-3 sameness cells (no note at all on HEAD; the right reason, the first fault in the loop has none).

### §R2.SAT — reference builds (scratch `…/scratchpad/refq1`, `loremaster.__file__` = `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/3c627105-1f2b-4e6a-9678-e4109ccfb396/scratchpad/refq1/loremaster/loremaster/__init__.py`, `scratch_copy.sh --verify-only` exit 0)
- **ref-A** = r1's reference plus F-3: `cause = "the connection failed during the CREATE" if isinstance(fault, SurrealConnectionError) else "the CREATE was interrupted before the store answered"`. Both repo files: **`165 passed`** — every cell, satisfiable.
- **ref-B** = ref-A plus N-3 option (a):
  - `wrap_store_rejection(…, *, catch=(SurrealStoreError,))`, with the default unchanged;
  - `mint` passes `catch=_txn._PROVEN_NO_KEY_FAULTS`.

  Run over both repo files plus the N-3 draft: **`2 failed, 192 passed, 2 skipped`**. The 2 failures are EXACTLY the predicted `test_an_unproven_fault_raised_by_the_CREATE[{plain,needs-quoting}-SurrealStoreError]`. Their `type(served) is type(_through_the_wrap(...))` pins today's translation of the bare base, which N-3 deliberately changes. That is the DUAL re-key that rides N-3 (§R2.N3-DRAFT item 4), and it is not satisfiable together with N-3 by construction.

### §R2.STOP-2 — (a) breaks a finding-#400 pin; (d) satisfies BOTH (measured)
- ref-B's targeted run (option (a)): **`4 failed, 1652 passed`**.
  - The 58-owned exhaustion-fates red.
  - The 2 predicted bare-base cells.
  - **AND `test_engine_rejection_seam.py::TestEngineRejectionWrappingBehaviourIsPreserved::test_a_raw_store_error_surfaces_as_the_domain_error[principal_key-mint]`.** `_inject_store_error` raises a **bare `SurrealStoreError`** as its "engine rejection" representative and requires mint to serve `PrincipalKeyStoreError` (#400's consumer law: no raw engine error reaches the caller). Under (a) the bare base passes through raw.
- So F-4 + N-3 + (a) contradict a pre-existing pin outside my writable set. That is a STOP-DUAL I may not re-key.
- **(d), the nested ONE-seam form**, satisfies both. `PrincipalKeyStoreError` does NOT subclass `SurrealStoreError` (measured MRO), so in `mint`:
  ```python
  with (
      wrap_store_rejection(PrincipalKeyStoreError, f"the mint of key {name!r} for principal {email!r} was interrupted before the store answered; its outcome is unknown"),
      wrap_store_rejection(PrincipalKeyStoreError, f"could not mint key {name!r} for principal {email!r}", catch=_txn._PROVEN_NO_KEY_FAULTS),
  ):
      result = await self._query(statement, params)
  ```
  - The inner wrap catches ONLY the proven tuple and gives the true not-landed message.
  - The outer wrap, with its default catch, translates every OTHER store fault (bare base, foreign subclasses) into the domain class with an outcome-unknown message. #400 holds: class preserved, no raw engine error.
  - The handler classifies by `__cause__` (F-1). The SAME tuple decides the inner catch AND the note, which is the one chokepoint the mutation drafts flip.
  - `wrap_store_rejection` gains only an optional `catch=` (default `(SurrealStoreError,)`), so the other 20 callers are byte-unchanged (the draft's CONTROL class).
- **ref-C (= ref-A + (d)), targeted set + the owned file + the N-3 draft: `1 failed, 1685 passed, 2 skipped`.**
  - The only failure is the 58-owned `store/lease.py` fates row.
  - The #400 pin is GREEN.
  - All 165 repo cells are GREEN (the bare-base type oracle holds: the class is still `PrincipalKeyStoreError`), so **§R2.N3-DRAFT item 4 (the DUAL re-key) is NOT needed under (d)**.
  - Every N-3 draft cell is GREEN; 58's fates classifier still reads the handler as a passthrough; a28c's `_txn` tester exact-set pin is green.
- Operator question: rule (d) (recommended), (a) (requires a DUAL re-key of a #400 pin in `test_engine_rejection_seam.py`, not mine), or narrow N-3.

### §R2.TARGETED
Set: r1's eight files (`$(cat targeted.txt)`, derivation in r1 §RUNS) + `test_mint_unknown_outcome_note_q1.py`.
- **HEAD `d27a0ce`: `29 failed, 1627 passed`.** 28 in the owned file + 1 `test_exhaustion_fates.py::…test_every_row_names_a_ruled_classification_an_owner_and_evidence_that_HOLDS` (`store/lease.py` `logs-error-class`, packet-58-owned, pre-existing since fix531d). **0 attributable reds outside the owned file.**
- ref-A covers both repo files (165/165). ref-B and ref-C are as above.

### §R2.N3-DRAFT — the N-3 pins, drafted, NOT landed (STOP)
Property (operator, 2026-10-05): ∀ fault that gets the CONDITIONAL note, no rendered message (`str(error)` + `traceback.format_exception`) claims non-landing; proven faults keep the not-landed message; ONE tuple decides both, proven by mutation.
1. GENERATED unproven population = the 6 r1 unknown faults + every FOREIGN `SurrealStoreError` subclass, derived after importing every non-test `loremaster` module (measured: `LeaseError`, `FenceLostError`, `FloorCalibrationError`, `VectorDimensionError`, `CalibrationPoolError` + 2 subclasses; floor `{LeaseError, FenceLostError}`). Each is constructed without knowing its constructor and injected at `_query`, inside the window. Each must give exactly one conditional-shaped note, and its render must NOT contain the not-landed message, which is DERIVED from mint's own proven serve, never hard-coded, nor `could not mint`.
2. Proven faults wrapped today keep `str(served) == "could not mint key 'laptop' for principal 'ops531@example.com'"` and a note-free chain. Connection and exhausted contention are skipped: they pass through today.
3. Sharing by mutation, both directions: `TxnDomainRejectionError` OUT of every identity-found binding → its note AND its message flip; `LeaseError` IN → no note AND the not-landed message.
4. **DUAL re-key on landing:** the owned file's bare-base unknown cell drops `type(served) is type(_through_the_wrap(...))` for non-proven STORE faults. The property in item 1 replaces it.
5. CONTROL for option (a): the shared wrap's DEFAULT still translates the bare base and every foreign class to the domain error, `from` the original. The other 20 callers are byte-unchanged.

Receipts:
- Against HEAD production (scratch tree reverted to HEAD with `git checkout` inside the SCRATCH copy, then restored): **`15 failed, 14 passed, 2 skipped`**. 13 fail as `assert 0 == 1` (no note) and 2 fail on the stub; this is the right reason.
- Against ref-B: all draft cells pass (inside the 192 above).

The instrument is pasted verbatim because it lives in scratch (brief-base §1). md5 is `4015d39e…` (after lint; `ruff check` clean in the scratch tree).
```python
"""DRAFT, NOT in the repo: am-37 §14 Q1 N-3 is STOPPED pending a ruling on the shared wrap.

contract-mint-q1 r2, 2026-10-05. On a ruling these classes move INTO
``loremaster/tests/test_mint_unknown_outcome_note_q1.py`` (the owned file), and ONE cell there is DUAL
re-keyed (REPORT-contract-mint-q1.md §R2.N3-DRAFT item 4).

N-3 (operator, 2026-10-05): whenever the CONDITIONAL note applies, NO rendered message claims the key was
not minted. Proven faults keep their not-landed message, which is TRUE for them. ONE tuple decides the note
AND the message; sharing is proven by mutation, since moving a class across the tuple flips BOTH.
"""

from __future__ import annotations

import importlib
import pkgutil
import traceback

import pytest
import test_am37_13_3_63c_i_a as fix531d  # module-qualified: its Test* classes are not re-collected here
import test_mint_unknown_outcome_note_q1 as q1
from loremaster.principal_keys import PrincipalKeyStoreError
from loremaster.store import _txn as _txn_module
from loremaster.store._txn import SurrealStoreError, TxnDomainRejectionError, wrap_store_rejection

import loremaster

_MINT_EMAIL, _MINT_NAME = fix531d._PLAIN  # noqa: SLF001


def _foreign_store_classes() -> list[type[BaseException]]:
    """GENERATED: every ``SurrealStoreError`` subclass defined OUTSIDE ``_txn``, after importing EVERY
    non-test ``loremaster`` module (so the walk does not depend on what this worker happened to import)."""
    for module in pkgutil.walk_packages(loremaster.__path__, "loremaster."):
        if ".tests" not in module.name:
            importlib.import_module(module.name)
    found: set[type[BaseException]] = set()
    pending = list(SurrealStoreError.__subclasses__())
    while pending:
        cls = pending.pop()
        pending.extend(cls.__subclasses__())
        if cls.__module__ != _txn_module.__name__:
            found.add(cls)
    return sorted(found, key=lambda cls: f"{cls.__module__}.{cls.__qualname__}")


def _construct(cls: type[BaseException]) -> BaseException:
    """An instance without knowing the class's constructor (foreign classes take bespoke kwargs)."""
    instance = cls.__new__(cls)
    BaseException.__init__(instance, f"injected n3: {cls.__name__}")
    return instance


_FOREIGN = _foreign_store_classes()
_UNPROVEN: list[BaseException] = [*q1._unknown_outcome_faults(), *(_construct(cls) for cls in _FOREIGN)]  # noqa: SLF001


async def _served(monkeypatch: pytest.MonkeyPatch, injected: BaseException) -> BaseException:
    window = fix531d.TestTheMintWindowNotesTheRevokeRepair
    store, reached = window._store(monkeypatch, raises=injected)  # noqa: SLF001
    with pytest.raises(BaseException) as caught:  # noqa: PT011 - the fate IS the assertion
        await store.mint(email=_MINT_EMAIL, name=_MINT_NAME, secret_hash="0" * 128)
    assert reached["count"] == 1, "the CREATE was never reached (#194)"
    return caught.value


async def _not_landed_message(monkeypatch: pytest.MonkeyPatch) -> str:
    """DERIVED, not hard-coded: what mint serves for a PROVEN rejection (the true not-landed claim)."""
    served = await _served(monkeypatch, TxnDomainRejectionError("injected n3 proven"))
    assert isinstance(served, PrincipalKeyStoreError), type(served)
    return str(served)


def _rendered(error: BaseException) -> str:
    return str(error) + "\n" + "".join(traceback.format_exception(error))


class TestAnUnprovenFaultNeverClaimsNonLanding:
    def test_the_foreign_population_is_not_vacuous(self) -> None:
        names = {cls.__name__ for cls in _FOREIGN}
        assert {"LeaseError", "FenceLostError"} <= names, names

    @pytest.mark.parametrize("injected", _UNPROVEN, ids=lambda error: type(error).__name__)
    async def test_the_message_does_not_claim_the_key_was_not_minted(
        self, monkeypatch: pytest.MonkeyPatch, injected: BaseException
    ) -> None:
        not_landed = await _not_landed_message(monkeypatch)
        served = await _served(monkeypatch, injected)
        notes = getattr(served, "__notes__", None) or []
        assert len(notes) == 1, (type(injected).__name__, notes)
        q1._assert_conditional_shape(notes[0], email=_MINT_EMAIL, name=_MINT_NAME)  # noqa: SLF001
        assert not_landed not in _rendered(served), _rendered(served)
        assert "could not mint" not in _rendered(served).lower(), _rendered(served)

    @pytest.mark.parametrize("cls", fix531d._PRE_COMMIT_CLASSES, ids=lambda cls: cls.__name__)  # noqa: SLF001
    async def test_a_proven_fault_keeps_the_not_landed_message(
        self, monkeypatch: pytest.MonkeyPatch, cls: type[BaseException]
    ) -> None:
        passes_through = cls.__name__ == "TxnContentionExhaustedError"
        if cls.__name__ not in fix531d._RULED_PROVEN_NO_KEY or passes_through:  # noqa: SLF001
            pytest.skip("not translated by the wrap today (connection / exhausted contention pass through)")
        served = await _served(monkeypatch, fix531d._instance(cls))  # noqa: SLF001
        assert str(served) == f"could not mint key {_MINT_NAME!r} for principal {_MINT_EMAIL!r}"
        fix531d._note_free_chain(served)  # noqa: SLF001


class TestOneTupleDecidesNoteAndMessage:
    async def test_moving_a_proven_class_OUT_flips_both(self, monkeypatch: pytest.MonkeyPatch) -> None:
        proven = q1.TestTheProvenNoKeySetIsOneExportedTuple._proven()  # noqa: SLF001
        not_landed = await _not_landed_message(monkeypatch)
        mutated = tuple(member for member in proven if not issubclass(TxnDomainRejectionError, member))
        for namespace, attribute in q1._loremaster_bindings_of(proven):  # noqa: SLF001
            monkeypatch.setattr(namespace, attribute, mutated)
        served = await _served(monkeypatch, TxnDomainRejectionError("injected n3 moved out"))
        assert len(getattr(served, "__notes__", None) or []) == 1, "the NOTE did not flip"
        assert not_landed not in _rendered(served), "the MESSAGE did not flip"

    async def test_moving_a_foreign_class_IN_flips_both(self, monkeypatch: pytest.MonkeyPatch) -> None:
        foreign = next(cls for cls in _FOREIGN if cls.__name__ == "LeaseError")
        proven = q1.TestTheProvenNoKeySetIsOneExportedTuple._proven()  # noqa: SLF001
        not_landed = await _not_landed_message(monkeypatch)
        for namespace, attribute in q1._loremaster_bindings_of(proven):  # noqa: SLF001
            monkeypatch.setattr(namespace, attribute, (*proven, foreign))
        served = await _served(monkeypatch, _construct(foreign))
        assert not getattr(served, "__notes__", None), "the NOTE did not flip"
        assert str(served) == not_landed, "the MESSAGE did not flip"


class TestTheOtherWrapCallersAreUnchanged:
    """CONTROL for option (a): the shared wrap's DEFAULT still translates every non-passthrough fault, so
    the 20 non-mint callers (audit / keeps / principals / revoke) are byte-unchanged."""

    @pytest.mark.parametrize(
        "injected",
        [SurrealStoreError("bare"), *(_construct(c) for c in _FOREIGN)],
        ids=lambda error: type(error).__name__,
    )
    def test_the_default_wrap_translates(self, injected: BaseException) -> None:
        with pytest.raises(PrincipalKeyStoreError) as caught:
            with wrap_store_rejection(PrincipalKeyStoreError, "control"):
                raise injected
        assert str(caught.value) == "control"
        assert caught.value.__cause__ is injected
```

### §R2.N3-LANDED — mechanism (d), in `test_mint_unknown_outcome_note_q1.py` (owned)
The drafted pins (§R2.N3-DRAFT, pasted above) were landed with these adaptations to (d). The class stays `PrincipalKeyStoreError`; only the message and the note move.
- `_FAMILY_CAUSE_WORDS` gained `interrupt` and `answered` (cause-neutral). It now governs BOTH the note (`_assert_conditional_shape`) and the outcome-unknown MESSAGE (`_assert_cause_neutral_message`).
- `TestAnUnprovenFaultNeverClaimsNonLanding` covers the GENERATED population: the 6 r1 unknown faults plus 7 foreign store classes. Floor: `{LeaseError, FenceLostError}`. For each:
  - one conditional note;
  - no derived not-landed message and no `could not mint` anywhere in the render;
  - store faults: `type is PrincipalKeyStoreError`, `__cause__ is injected`, and a cause-neutral message;
  - non-store faults: the same object.
- Proven faults keep `could not mint key …` with a note-free chain.
- `TestOneTupleDecidesNoteAndMessage` covers mutation both ways over identity-found bindings. Moving `TxnDomainRejectionError` OUT flips the note and the message (the class stays the domain class, cause chained). Moving `LeaseError` IN gives no note and the not-landed message.
- `TestTheOtherWrapCallersAreUnchanged` (lead item 1):
  - the DEFAULT `wrap_store_rejection` still translates the bare base and every foreign class;
  - a REAL non-mint caller, `revoke`, still serves `could not revoke key …` with the cause chained and no note.
  - Under a wrong default (the proven tuple), the bare base and the foreign classes would pass `revoke` untranslated and these cells red. That is by inspection: I did not build that wrong build (role boundary).
  - The generated cross-store counterpart is `test_engine_rejection_seam.py`'s #400 pins, in the targeted set and GREEN on ref-D.
- **§R2.N3-DRAFT item 4 (the DUAL re-key) is NOT needed:** under (d) the r1 bare-base oracle (`type(_through_the_wrap)` = `PrincipalKeyStoreError`) still holds.
- **Lead item 2 (caller rider):** MOOT under (d), per addendum 2. `mint` still raises only `PrincipalKeyStoreError` / pass-through classes to `_cmd_mint_key`, and `_dispatch`'s handler already catches both (§11). No pin added.
- **Lead item 3 (three effects):** under (d) the "translation" effect is WHICH wrap translated, observed as the message. The class does not flip by design.

**Receipts:**
- **RED on HEAD `8cf6edd`** (both files, `GATE PASS`): **`43 failed, 159 passed, 2 skipped`**, 43/43 in the owned file. Tally:
  - 30 "no note": 12 `exactly ONE … got None` + 3 real-cancel + 2 sameness + 13 N-3 population cells (`assert 0 == 1`);
  - 13 STUB `AttributeError … _PROVEN_NO_KEY_FAULTS`: r1's 11 + the 2 N-3 mutation cells.
  - GREEN on HEAD, correctly: proven-keeps-message (5), the CONTROL wrap and `revoke` cells (16; they pin TODAY's default), the foreign floor.
  - The 2 skips are connection and exhausted contention in the proven-keeps-message cell (not translated today).
- **ref-D** = r1 reference + F-3 cause-neutral note (`"the store did not confirm the CREATE"` for non-connection) + (d) nested wraps with outer message `"the store did not confirm the mint of key … ; its outcome is unknown"` + `catch=` on the seam. Both files: **`202 passed, 2 skipped`**. `loremaster.__file__` is the scratch tree's (printed above).
- **Targeted** (r1's eight files + the owned file):
  - HEAD **`44 failed, 1649 passed, 2 skipped`** = 43 owned + the pre-existing 58 `test_exhaustion_fates` row. **0 attributable reds outside the owned file.**
  - ref-D **`1 failed, 1693 passed, 2 skipped`**: only the 58 row. #400's `test_engine_rejection_seam.py` is all GREEN.
- **Currency** `--currency --legs typecheck,ruff`: `typecheck RED_ADJUDICATED — 84 residual(s)` (owners include `am37-14-q1-mint-contract`), `ruff GREEN`, **RED_ORPHANED 0**; `pytest NOT_RUN` by law.
