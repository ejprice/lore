brief-base v18 read

# REPORT — coldaudit-mint-q1 (am-37 §14 Q1 build, cold REFUTE audit)

## SUMMARY BLOCK
- **State:** done — GO-with-residuals (written 2026-10-05 12:47Z, last).
- **Verdict: GO-with-residuals.** The am-37 §14 Q1 build (working tree on `cc834ca`, == `q1-BUILD.patch` a755a8a4…) conforms to §14 Q1 + F-1 (b) / F-2 (b) / F-3 / N-3 (d) on every row of §2b. 5 / 5 own mutations KILLED, 0 survivors. Full suite: currency PASS, RED_ORPHANED 0 on every leg; the build moves 0 reds in owned files.
- Deviations: (1) the brief's 20 GiB floor stalled runs ~11:36–12:06Z (host, not ours) — I waited, no bypass (§FORK; no reply needed in the end); (2) one VOID M-b attempt (my own outer timeout killed it in the gate; scratch-only, restored, re-run) (§3); (3) a first full-suite launch deadlocked on the lead's watcher shell matching my gate pattern — killed by PID before any pytest, pattern re-keyed and control-tested, re-run (§5, #544); (4) passed/skipped of the full suite NOT captured by the gate instrument (#545) — denominator derived instead (§5a).
- Packages considered: none — no mechanism specified (audit; instruments are scratch shell around the repo's own `mutation_proof.py` / `scratch_copy.sh` / currency gate).
- Odoo-20 portability: n/a — no Odoo seam touched.
- Reuse ledger: none (no new symbols; read-only audit).
- Graded: working tree over `cc834ca5054c` (brief named `52d10ae`; `cc834ca` is a docs-only lead-report commit on top, 1 file, `REPORT-lead-63c.md`) · HEAD-at-report: `cc834ca5054c` · SAME.
- Findings: F-1 LOW (`mint` `Raises:` over-claims "any OTHER store fault" → PKSE; connection/TCE arrive raw) · F-2 LOW (tuple comment's "not-landed message" inert for TCE) · F-3 LOW instrument (#545) · F-4 LOW coordination (#544). None blocks the commit.
- Full suite: 13,799 collected · **530 failed, all owned** — files under `packet-58-contract` 217 (reanchor/task 211 + exhaustion_fates 1 + blocks_edge 1 + task_read_surface 1 + forgery_door_sweep 3; the two files registered under BOTH bounds counted here), under `packet-64b-i-contract` 313 (findings 170 + governed_substrate 34 + comms_footer 81 + mcp_server 28) · typecheck RED_ADJUDICATED 83 (58 + 64b-i) · ruff GREEN · 701 s · peak sampled RSS 2.6 GiB.
- Decisions needed: R-1 (operator, LOW confidence): is every non-connection, non-conflict engine error kind on a single CREATE provably pre-commit? It is what makes `TxnDomainRejectionError` "proven" (§7).
- md5: all four files + the patch identical at START and END; the working-tree diff md5 == the patch md5.
- Pointers: §1 contract-blind fate table · §2 inventory diff · §2b conformance · §3 mutations · §4 trust read · §5/§5a full suite + owned census · §6 findings · §7 residuals · §8 instruments · md5 START/END.

## md5 receipts — START (2026-10-05, HEAD 52d10ae)
| file | md5 | matches brief |
|---|---|---|
| loremaster/loremaster/principal_keys.py | c67cc35659e0ddc5518816825e5ad0c7 | yes |
| loremaster/loremaster/store/_txn.py | 4ebe3712beba2963902eb1745e9b80ce | yes |
| loremaster/tests/test_mint_unknown_outcome_note_q1.py | 90a6d1402831d6432f1970ab8f54ce10 | yes |
| scripts/pending_contracts.yaml | b0158ed1189ea905faf9c8d8b9f87f76 | yes |
| q1-BUILD.patch | a755a8a482e42e740ac484035b06c818 | yes |

## 1. Contract-blind diff read (written BEFORE reading the contract, the reports, or the spec §14)

Inputs read: the working-tree diff of `principal_keys.py` + `_txn.py` only; `_txn.run_query`,
`_raise_attempt_failure`, `_classify_engine_error`, `_domain_rejection_error`, `is_connection_error`,
`lorerunes.engine_rejection.reclassify`; `PrincipalKeyStoreError` (base `RuntimeError`, NOT a
`SurrealStoreError` — so the outer wrap can never re-translate the inner wrap's output).

Runtime census (2026-10-05, HEAD cc834ca + the uncommitted build, every `loremaster.*` module imported, 0
import failures) of the `SurrealStoreError` tree: `_txn` = {SurrealConnectionError [passthrough],
TxnParamCollisionError, TxnEnvelopeViolationError, TxnContentionExhaustedError [passthrough],
TxnDomainRejectionError ⊃ {TxnGovernedConflictError, TxnUniqueViolationError}}; foreign =
{surreal.VectorDimensionError, surreal.CalibrationPoolError ⊃ {…Truncated, …CountMismatch},
floor_calibration.FloorCalibrationError ⊃ {FenceLostError}, lease.LeaseError}. `run_query` raises only
SurrealConnectionError / Txn{Domain,Governed,Unique}Rejection / TxnContentionExhausted (+ anything
outside `(*_CONNECTION_ERRORS, KeyError)` raw); the foreign classes are unreachable from the mint CREATE.
`_CONNECTION_ERRORS = (OSError, surrealdb.errors.SurrealError, WebSocketException)`.

### 1a. Fate table — every fault class that can reach `mint`'s try (traced by hand from the diff)

| fault at the CREATE (answered=False) | inner wrap (catch=PROVEN) | outer wrap (default) | served class / message | note OLD | note NEW |
|---|---|---|---|---|---|
| SurrealConnectionError | passthrough | passthrough | raw SCE | conditional, connection text | conditional, connection text — byte-identical composition |
| TxnContentionExhaustedError | passthrough (membership in `catch` inert) | passthrough | raw TCE | none | none (classified as itself → PROVEN) |
| TxnUnique/Governed/DomainRejection, TxnParamCollision, TxnEnvelopeViolation | translate → PKSE "could not mint…" from orig | PKSE is not SSE → propagates | PKSE "could not mint" | none | none (`__cause__` → PROVEN) |
| bare SurrealStoreError / any non-PROVEN SSE subclass | not caught | translate → PKSE "store did not confirm…; outcome is unknown" from orig | PKSE outcome-unknown | none, msg "could not mint" | conditional, UNCONFIRMED cause |
| CancelledError / KeyboardInterrupt / SystemExit / GeneratorExit | — | — | raw, re-raised (bare `raise`) | none | conditional, UNCONFIRMED cause |
| any foreign non-SSE Exception escaping `run_query` raw (e.g. a decode `ValueError`) | — | — | raw | none | conditional, UNCONFIRMED cause |
| PKSE with no `__cause__` (unreachable pre-answer today) | — | — | PKSE | none | conditional (fail-safe direction) |

| fault AFTER the CREATE answered (answered=True) | OLD | NEW |
|---|---|---|
| `_as_rows` shape error, "answered no row" PKSE, `_row_to_key` failure, a cancellation | CERTAIN note | CERTAIN note — that branch is textually unchanged |

### 1b. Removed/changed-behaviour inventory (mine, independent)

| # | old behaviour | new behaviour | my adjudication |
|---|---|---|---|
| I-1 | bare/non-proven SSE → PKSE "could not mint", no note | PKSE "outcome unknown" + conditional note | changed deliberately (the Q1 point: "could not mint" was a false not-landed claim) — needs spec cite |
| I-2 | cancellation/interrupt/foreign before answer → no note | conditional note | changed deliberately — needs spec cite |
| I-3 | connection fault → conditional note, exact text | identical text (cause constant reproduces the old parenthetical) | preserved — needs a byte pin |
| I-4 | proven classes → PKSE "could not mint", no note | same | preserved |
| I-5 | TCE → raw, no note | same | preserved |
| I-6 | answered → CERTAIN note | same | preserved |
| I-7 | `wrap_store_rejection(domain_error, context)` translates every non-passthrough SSE | new kw-only `catch=` defaulting to an equal `(SurrealStoreError,)` tuple | preserved for the other callers — needs a mutation proof (step 3a) |
| I-8 | the handler re-raises the SAME object | same (`raise`) | preserved |
| I-9 | the classification was one `isinstance(error, SurrealConnectionError)` | `_classified_fault` unwraps a PKSE's `__cause__`, then tests the tuple | new; the unwrap is the only local logic and it reads the same tuple (no re-classification) |

### 1c. Contract-blind observations (before reading anything else)
- O-1: `_PROVEN_NO_KEY_FAULTS` membership of `TxnDomainRejectionError` is sound only if EVERY non-transport,
  non-conflict engine `ServerError` on a single-statement CREATE precedes the commit. `_classify_engine_error`
  sends every kind not in `_CONNECTION_ERROR_KINDS` (Internal, Query incl. `TimedOut`/`Cancelled`,
  Serialization, NotAllowed, …) to `TxnDomainRejectionError`. I have not seen a probe that a
  post-commit failure cannot arrive typed as one of those kinds (e.g. `Serialization` of the `RETURN AFTER`
  output). Spec-level, LOW confidence — check whether §14 / F-2 addresses it.
- O-2: TCE is in the tuple AND a passthrough; its tuple membership affects the note (none) but never the
  catch. The `_PROVEN_NO_KEY_FAULTS` comment says mint reads the tuple "to choose its inner wrap's
  `catch=` (and therefore its not-landed message)" — for TCE the message is TCE's own. Minor prose precision.

## 2. The two-inventory diff (mine §1b vs `REPORT-implement-mint-q1.md` §INVENTORY @52d10ae)

| item | mine | implementer | diff verdict |
|---|---|---|---|
| unknown non-store faults pre-answer → note | I-2 | row 1 | agree |
| bare SSE → outcome-unknown msg + note | I-1 | row 2 | agree |
| foreign SSE subclasses | folded into I-1 (I showed them unreachable from `run_query`) | row 3 | agree; my census adds that the foreign classes cannot arise on the mint path in production — the N-3 cells construct them by injection only |
| proven classes unchanged | I-4 | row 4 | agree |
| TCE raw, no note | I-5 | row 5 | agree |
| connection text unchanged | I-3 | row 6 | agree |
| post-answer CERTAIN | I-6 | row 7 | agree |
| one try / bare raise | I-8 | row 8 | agree |
| wrap default unchanged | I-7 | row 9 | agree — not mutation-proven by anyone before this audit (§3 M-a) |
| mint now has TWO wrap-context sites | **missed** | row 10 | theirs only — a real served-surface change (the generated `TestNoWrapContextOverClaimsItsCause` cell), accepted |
| causeless pre-answer PKSE → note | I-9 (fail-safe) | row 11 | agree; unreachable, unpinned (fail-safe direction) |
| O-1 TxnDomainRejectionError ⊂ proven is sound only if no post-commit engine fault arrives typed as a domain kind | **mine only** | absent | spec-level (§14 ruled the domain-rejection family proven); surfaced as residual R-1 |
| O-2 TCE's tuple membership is inert for the catch; the tuple comment says it chooses "the not-landed message" | **mine only** | absent | prose precision, LOW — finding F-2 below |

Note on provenance (implementer deviation 2): the comment hunk in `test_mint_unknown_outcome_note_q1.py`
("∀ such faults, cause-neutral" → "cause-neutral") pre-dated the implementer per its report; its author is not
recorded anywhere I can read. It is a comment only (no assertion changed — I read both sides of the hunk).

## 3. Mutations (mine) — `scripts/mutation_proof.py` in a `scratch_copy.sh` tree

Tree: `…/c9dba7af…/scratchpad/q1audit` (created 2026-10-05 ~11:29Z from the working tree; its three build files
carry the brief's md5s). Provenance receipt printed in-run: `loremaster.__file__ =
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/c9dba7af-41f2-4005-b2bd-1474ed75b09d/scratchpad/q1audit/loremaster/loremaster/__init__.py`.
Target set T (8 files): `test_mint_unknown_outcome_note_q1.py`, `test_am37_13_3_63c_i_a.py`,
`test_engine_rejection_seam.py`, `test_principals_cli.py`, `test_principal_keys_store.py`, `test_keeps_store.py`,
`test_audit_store.py`, `test_principals_store.py` — the contract's two files, the #400 cross-store seam pins, the
CLI fates, and the store files of the wrap's other callers (hand-added, said out loud: `lore_impact` elides
>100 covering ids for `wrap_store_rejection`). **Baseline (unmutated scratch): 690 passed, 2 skipped, 0 failed.**
Every run went through a waiting gate (MemAvailable ≥ 20 GiB ∧ no other lore pytest) under
`systemd-run --scope -p MemoryMax=16G -p MemorySwapMax=0`, `-n 8 --timeout=300`. Declared sets were taken from
`--collect-only` (692 ids) BEFORE each run.

| # | mutation | prediction (written before) | declared | observed | verdict |
|---|---|---|---|---|---|
| M-a | `wrap_store_rejection`'s DEFAULT `catch=` → `_PROVEN_NO_KEY_FAULTS` | every bare-`SurrealStoreError` injection at a non-mint caller and at mint's outer wrap reddens: the 15 #400 cells, the audit born-wrapped cell, the 16 `TestTheOtherWrapCallersAreUnchanged` cells, the 8 store-class cells of the N-3 population | 40 | **49 failed / 641 passed**; 40/40 declared fired; **9 unexpected**, all `test_keeps_store.py` bare-SSE wrap pins (`TestKeepStoreWrapsEngineRejections::…[×7]`, `TestListKeepsForMember::test_born_wrapped_{engine,RESOLUTION}_rejection…`) | **KILLED.** The tool printed PROOF FAILED because MY declaration was short by 9 killers of the same class — an under-prediction, not a survivor. I did not re-declare from the output (that is the tautology). Restored byte-exact (md5 4ebe3712…). Observation: r1's `test_an_unproven_fault_raised_by_the_CREATE[…SurrealStoreError]` stays GREEN under M-a, because its oracle `fix531d._through_the_wrap` uses the default wrap and FOLLOWS the mutation — that cell alone does not discriminate the default; the N-3 cells and the other-caller cells do |

## 4. Trust / consumer-law read of every served string the build changed (2026-10-05, build bytes)

Population that can reach each string IN PRODUCTION, derived from the §1 census + `run_query` /
`_raise_attempt_failure` / `_ensure_connection` (bootstrap failures, including exhausted bootstrap contention,
are re-raised as `SurrealConnectionError`):

| served string | who gets it | true for all of them? |
|---|---|---|
| inner msg `could not mint key … for principal …` (unchanged) | Txn{Domain,Governed,Unique}Rejection, ParamCollision, EnvelopeViolation | TRUE for the pre-send pair; TRUE for the domain family **iff** an engine `ServerError` of a non-connection, non-conflict kind on a single CREATE always precedes commit — see residual R-1 (spec-ruled, not probed by anyone for every kind) |
| outer msg `the store did not confirm the mint of key …; its outcome is unknown` (NEW) | bare `SurrealStoreError` + any non-proven SSE subclass. `run_query` raises neither today, so in production this is defence-in-depth, reachable only by a future raise site | TRUE: names no cause, claims neither landing nor non-landing ("did not confirm" holds for a malformed answer too). Cause-neutral by the contract's vocabulary. The generated CLI pin (`TestNoWrapContextOverClaimsItsCause`) passes it |
| note parenthetical `(the connection failed during the CREATE)` (unchanged bytes, now a constant) | `SurrealConnectionError` only — including bootstrap failures that happened BEFORE the CREATE was sent | over-cautious for a pre-send bootstrap failure (pre-existing, unchanged; the advice "if list-keys shows it, revoke" is harmless when nothing landed) |
| note parenthetical `(the store did not confirm the CREATE)` (NEW) | cancellation, interrupts, `SystemExit`/`GeneratorExit`, any raw non-SDK exception escaping `run_query`, the outer-wrapped store faults | TRUE for all: none of them is a confirmation. A cancellation that lands before the CREATE was sent (e.g. while `acquire()` awaits the connect lock) is also "unconfirmed" — over-cautious, never false. The note's head "the mint's outcome is unknown" is honest for every member |
| `_PROVEN_NO_KEY_FAULTS` comment, `wrap_store_rejection` docstring, `_mint_fault_note` / `_classified_fault` docstrings, mint window comment | code readers (served to agents through lore spans) | TRUE, with two precision gaps → findings F-1, F-2 |

Consumer-law (#400) check: `mint` serves a raw `SurrealStoreError`-family error ONLY for the two documented
passthroughs (connection, exhausted contention), both before and after the build; every other store fault is
`PrincipalKeyStoreError`. A raw non-SDK exception (outside `(*_CONNECTION_ERRORS, KeyError)`) propagates raw,
as before — the build adds only the note.

## FORK (written 2026-10-05 12:02Z) — the brief's 20 GiB MemAvailable floor is not being met by the host
- Measured: MemAvailable 19.4–19.8 GiB continuously 11:36Z→12:01Z (one pass at ~11:33Z let M-a run). Consumers:
  postgres containers ≈86 GiB summed RSS, surreal ≈12 GiB; no lore pytest live; nothing of mine running.
- Effect: M-b..M-e and the full suite are queued behind the waiting gate (no bypass). At this rate the full
  suite may not start before the 13:55Z deadline.
- Options for the lead: (a) keep the 20 GiB floor and accept a NOT TRIED full suite if the host does not recover;
  (b) lower the floor (e.g. to 17 GiB — every run is ALREADY hard-capped at MemoryMax=16G, so the floor is
  headroom for the host, not for the run). **Recommendation: (b) 17 GiB**, because the cgroup cap is the
  instrument that protects the host from OUR runaway; the floor only protects against the host's own
  pressure, which is ~19 GiB free and flat. I am NOT changing it on my own.
- **RESOLVED 12:06Z by host recovery** (MemAvailable 20–24 GiB; M-b..M-e and the full suite then ran under the 20 GiB floor as briefed). No lead reply was received or needed.
- **OPERATOR RULING (relayed by team-lead, ruled ≈12:05Z, received by me 12:48Z, AFTER all runs finished): option (b)** —
  a 17 GiB MemAvailable floor for coldaudit-mint-q1's runs only. Everything else unchanged: still a waiting loop, no other
  lore pytest live, 16G cgroup cap on every targeted run, the full suite via `pending_contract_gate.py --currency --
  --maxprocesses=12` with no `-n`. Standing law stays 20 GiB for everyone else. Deadline extended to 15:30Z.
- **Floor ACTUALLY USED: 20 GiB, for every run** (the ruling arrived too late to be applied). GATE PASS readings from
  the logs: M-a 20 GiB (~11:33Z), M-b 20 GiB (12:06Z), M-c 23 GiB, M-d 24 GiB, M-e 23 GiB, full suite 24 GiB (12:17:55Z),
  owned-file census ≥20 GiB. So every run met the stricter floor, and none needs re-running under the ruling.
- **What "M-a KILLED" means (the lead's question):** "KILLED" is mutation vocabulary: the MUTANT was killed, i.e. the
  tests caught it. Nothing killed the RUN. M-a ran to completion in the ~11:33Z window, when MemAvailable briefly met
  20 GiB: 49 failed / 641 passed / 2 skipped in 22.81 s, and the scratch `_txn.py` was restored byte-exact (4ebe3712…).
  All 40 declared tests failed, plus 9 undeclared `test_keeps_store.py` tests that test the same thing (a bare-SSE wrap
  translation). `mutation_proof.py` printed PROOF FAILED only because my declaration listed fewer tests than actually
  failed (it diffs both ways). The result is **USABLE and does not need a re-run**: the mutant is caught, and re-declaring
  from the output would be the tautology the tool exists to prevent. The only run that DID die was the first M-b
  attempt (my own outer timeout, while it sat in the gate, with zero tests executed). It is void, and it was re-run
  cleanly as M-b in the chain (PROOF HELD).
- Durable signal: this fork is posted via lore_comms to lead-63c-2; I will check for a reply at my turn
  boundaries. Absent a reply, I keep waiting under the brief's 20 GiB floor.

## 6. Findings (each lifted to its CLASS)

### F-1 (LOW, prose) — `mint`'s `Raises:` over-claims that every non-proven store fault becomes `PrincipalKeyStoreError`
- **Where:** `PrincipalKeyStore.mint` docstring, `Raises: PrincipalKeyStoreError: … or any OTHER store fault, whose
  outcome is unknown (an outcome-unknown message plus the conditional revoke note …)`.
- **Failure scenario:** a reader (agent, via a lore span) concludes a `SurrealConnectionError` during the CREATE
  arrives as `PrincipalKeyStoreError` and catches only that; it actually arrives RAW (passthrough), and so does
  `TxnContentionExhaustedError`. The two passthroughs are named in the window comment, not in `Raises:`.
  Pre-existing omission (the old `Raises:` named neither), but the new sentence makes an affirmative "any OTHER
  store fault" claim that is false for the connection class.
- **CLASS:** *a `Raises:` section must name every class the method can raise for the domain its sentence
  quantifies over.* **SIBLINGS TRIED:** the `_mint_fault_note`, `_classified_fault`, `wrap_store_rejection` and
  `_PROVEN_NO_KEY_FAULTS` prose (all consistent with the code except F-2). **SIBLINGS NOT TRIED:** `revoke`'s and
  the other 20 wrapped methods' `Raises:` sections (unchanged by this build).
- **Fix shape (for an implementer, not me):** add `SurrealConnectionError` / `TxnContentionExhaustedError` (raw,
  passthrough; the former carries the conditional note) to `Raises:`, or narrow "any OTHER store fault" to "any
  other non-passthrough store fault".

### F-2 (LOW, prose) — the tuple comment says mint reads it to choose "its not-landed message"; for TCE that is inert
- **Where:** the `_PROVEN_NO_KEY_FAULTS` comment in `_txn.py` ("…to choose its inner wrap's ``catch=`` (and
  therefore its not-landed message)…").
- **Failure scenario:** `TxnContentionExhaustedError` is a tuple member AND a passthrough; `reclassify` re-raises
  passthroughs first, so it is never translated and never gets "could not mint". A reader who moves TCE out of the
  tuple expecting the MESSAGE to change sees only the NOTE change. Behaviour is correct; the sentence is precise
  for 5 of 6 members.
- **CLASS:** *prose describing a shared tuple's effects must hold for every member, including members another
  rule (the passthrough) overrides.* **SIBLINGS TRIED:** the mint window comment ("A transport fault / exhausted
  contention passes through both untouched" — correct). **NOT TRIED:** none relevant.

### 3 (cont.) — M-b..M-e (runner `runmut.sh`, pasted in §8; declarations written 2026-10-05 ~11:50Z, before any of these ran)

| # | mutation | prediction | declared | observed | verdict |
|---|---|---|---|---|---|
| M-b | drop `TxnEnvelopeViolationError` (a leaf, not the implementer's choice) from `_PROVEN_NO_KEY_FAULTS` | its NOTE (fix531d CREATE-call ×2), its MESSAGE (`test_a_proven_fault_keeps_the_not_landed_message`), the sharing cell, and both literal/derived completeness cells | 6 | 6 failed / 684 passed; **PROOF HELD** (exact both ways) | KILLED — note, message and translation move together on ONE tuple edit |
| M-c | F-1 path: `fault = cls._classified_fault(error)` → `fault = error` | every TRANSLATED proven fault gains a note: 10 fix531d cells, the LIVE UNIQUE no-advice pin, 5 not-landed-message cells, the CONTROL, the foreign-IN flip | 18 | 18 failed / 672 passed; **PROOF HELD** | KILLED — incl. `TestALiveUniqueCollisionCarriesNoRevokeAdvice::test_a_duplicate_name_mint` (live store) |
| M-d | outer message → `"it was interrupted; its outcome is unknown"` | the 8 store-class N-3 cells + `test_moving_a_proven_class_OUT_flips_both` (cause-neutral asserts); the CLI over-claim pin bans only its own phrase, so stays green | 9 | 9 failed / 681 passed; **PROOF HELD** | KILLED |
| M-e | swallow cancellation: `if type(error).__name__ == "CancelledError": return None` before the bare `raise` | the 9 cells injecting or really delivering a cancel (r1 ×2, ONE-parenthetical ×2, asyncio.timeout, anyio scope, Task.cancel, post-answer, N-3) | 9 | 10 failed / 680 passed; 9/9 declared fired + **1 unexpected**: `test_am37_13_3_63c_i_a.py::TestTheMintHasOneNoteHandlerOverTheWholeWindow::test_one_add_note_handler` | KILLED (tool: PROOF FAILED on my under-prediction; the extra is an AST one-handler pin that also sees the added `return` — a second, structural killer) |

Every run restored byte-exact (`_txn.py` 4ebe3712…, `principal_keys.py` c67cc356… printed after each). ⚠ One
VOID run, disclosed: my first M-b attempt was killed by my own outer `timeout 1500` while parked in the memory
gate (exit 124, zero tests executed) and left the SCRATCH `_txn.py` mutated (md5 d1805e5d…); its "still-green"
listing is meaningless. I restored the scratch file from the build bytes (md5 4ebe3712… verified) before re-running.
The real tree was never touched by any mutation.
**No survivors. Mutation table: 5 / 5 KILLED.**

## 5. The packet's ONE full suite — `pending_contract_gate.py --currency -- --maxprocesses=12` (REAL tree)

- **Run:** 2026-10-05, gate passed 12:17:55Z (MemAvailable 24 GiB, no live lore pytest/gate process), finished
  12:29:36Z, **701 s**, `CURRENCY EXIT=0`. Wrapped in `systemd-run --scope -p MemoryMax=16G -p MemorySwapMax=0`
  (no cap kill). `-n` NOT forwarded. The four build md5s were printed by the runner immediately before the run and
  equal the brief's (c67cc356… / 4ebe3712… / 90a6d140… / b0158ed1…).
- **Peak RSS** (10 s sampler summing every process whose argv mentions pytest/xdist/the gate/mypy — host-wide, so
  an over-estimate): **2.6 GiB**. Far under the 16 GiB defect line.
- **Per-gate verdicts (verbatim heads):**
  - `typecheck RED_ADJUDICATED — 83 residual(s)`, owners `packet-58-contract` · `packet-64b-i-contract` (83 equals
    the implementer's post-build figure; the `am37-14-q1-mint-contract` owner is gone).
  - `ruff GREEN`.
  - `pytest RED_ADJUDICATED — 530 residual(s)`, owners `packet-58-contract` · `packet-64b-i-contract`.
  - `CURRENCY: PASS — every claimed gate is GREEN or OWNED`. **RED_ORPHANED: 0 on every leg.**
- ⚠ **Counts the instrument did NOT give me:** the gate runs pytest into a `TemporaryDirectory` junit and pipes
  its stdout away (`pending_contract_gate.py` `run_gate` → `RawGateResult`), and the currency render prints only
  the residual count and owners. So from THIS run I have: **530 failed, all owned; passed/skipped NOT CAPTURED**.
  I did not run a second full suite to get them (one per packet, fleet-wide). §5a closes the part that matters.
  This is an instrument gap (a served count with no denominator) — filed below as a finding against the gate.
- **The deadlock incident (disclosed):** my first full-suite launch (12:14Z) waited on a false "other session":
  my gate's `pgrep -f '…|[p]ending_contract_gate|…'` matched the LEAD's watcher shell (PID 3509133), whose
  command text names `pending_contract_gate` while waiting for THIS report. Killed my runner by PID (it had
  started no pytest; exit 143), re-keyed the pattern to argv0
  (`^[^ ]*python[^ ]* .*(-m pytest|bin/pytest|scripts/pending_contract_gate.py|scripts/wave_gate.py)|^[^ ]*/bin/pytest`),
  control-tested both ways (two python decoys matched; a bash shell carrying the same words did not), relaunched.
  Filed as **#544**.

### F-3 (LOW, instrument) — the currency gate's pytest leg cannot report its own counts → filed **#545**
- CLASS: *a served count must carry its denominator, and a once-per-packet run must be able to answer every
  receipt a close-out requires.* SIBLINGS TRIED: the typecheck leg (prints residual count; mypy has no "passed"
  analogue — fine). NOT TRIED: `wave_gate.py`'s render.

### F-4 (LOW, coordination) — `pgrep -f` waiting gates match other agents' shells → filed **#544** (§5)

## 7. Residuals (not defects in this build; surfaced for the lead/operator)
- **R-1 (spec-level, LOW confidence — operator question).** `TxnDomainRejectionError ⊂ _PROVEN_NO_KEY_FAULTS`
  claims every non-transport, non-conflict engine `ServerError` on a single-statement CREATE precedes commit.
  `_classify_engine_error` routes EVERY other `ErrorKind` (Internal, Query incl. `TimedOut`/`Cancelled`,
  Serialization, NotAllowed, …) there. Nobody has probed whether a post-commit failure (e.g. serialising the
  `RETURN AFTER` row) can arrive typed as one of those kinds; if it can, the mint would say "could not mint" with
  no note while the key is LIVE. §14 Q1 ruled the family proven; this is a re-open trigger, not a build defect.
  Askable form: *"which engine error kinds can a single CREATE raise AFTER its implicit commit?"* — answerable from
  `lore_search(tier="surrealql-tests", …)` / the 3.2 docs before any probe.
- **R-2 (= implementer N-a).** lore-adm `_dispatch` lets a cancel/interrupt/raw fault reach the operator as a
  traceback (the note prints in it). Behaviour unchanged by this build.
- **R-3 (test quality, LOW).** r1's `test_an_unproven_fault_raised_by_the_CREATE[…-SurrealStoreError]` takes its
  expected class from `fix531d._through_the_wrap`, which uses the DEFAULT wrap and so follows a default-catch
  mutation (M-a left it green). Other cells kill M-a, so no survivor; the oracle is production-derived.
- **R-4 (by design).** `TxnGovernedConflictError` / `TxnUniqueViolationError` are listed AND covered by their
  parent `TxnDomainRejectionError`: removing either from the literal is behaviourally inert and is caught only by
  the two literal-equality cells (the ruling's adjudication pin). Correct as an adjudication record; noted so
  nobody reads a green note-cell as proof the subclass entry is load-bearing.
- **R-5 (= implementer N-b).** A causeless pre-answer `PrincipalKeyStoreError` → conditional note: unreachable,
  unpinned, fail-safe direction.
- **R-6 (= implementer N-c).** `ruff format --check` drift in both production files, pre-existing, not a gate.
- **R-7 (provenance).** The one-word comment hunk in `test_mint_unknown_outcome_note_q1.py` pre-dates the
  implementer and has no recorded author (comment only; assertions unchanged).
- **R-8 (host).** MemAvailable sat at 18–19.8 GiB for ~30 min (postgres containers ≈86 GiB summed RSS); the 20 GiB
  floor stalled this audit's runs from 11:36Z to ~12:06Z. Not ours; surfaced in §FORK.

## 2b. Spec conformance (am-37 §14 Q1 + lead rulings F-1 (b), F-2 (b), F-3, N-3 (d)) — checked 2026-10-05 on the build bytes

| requirement | evidence | verdict |
|---|---|---|
| ONE tuple decides the inner catch, the note, the message and the translation | the inner wrap passes `catch=_PROVEN_NO_KEY_FAULTS`; `_mint_fault_note` tests `isinstance(fault, _PROVEN_NO_KEY_FAULTS)`; both read the module binding at call time. M-b: one tuple edit flips note + message + which wrap translated (PROOF HELD) | PASS |
| no second copy, no local re-classification (ROUTING IS NOT SHARING) | the only other class test is `isinstance(fault, SurrealConnectionError)`, which picks the WORDING only (F-3 ruling), never whether a note is given; `_classified_fault` unwraps `__cause__` and classifies nothing. M-c (classify on `error`) reddens 18 incl. the live UNIQUE pin | PASS |
| F-2 (b): hand-adjudicated literal in `_txn`, checked against the derived taxonomy | literal of 6 beside the classes; `test_the_tuple_is_the_rulings_adjudication` + `…_is_the_derived_taxonomy` both redden under M-b | PASS |
| the other 20 `wrap_store_rejection` callers unchanged | `git diff --stat`: only `principal_keys.py` + `_txn.py` change in production; mint is the only `catch=` site; default `_DEFAULT_REJECTION_CATCH == (SurrealStoreError,)`; M-a reddens 49 cells across keep / principal / principal_key / audit | PASS |
| #400: mint never serves a raw engine error | outer default wrap translates every non-passthrough store fault; M-a (outer narrowed via the default) reddens `test_a_raw_store_error_surfaces_as_the_domain_error[principal_key-mint]` | PASS |
| certain note after the answer unchanged | branch textually unchanged, checked first; `TestAPostAnswerInterruptStaysCertain` + fix531d certain pins green in baseline | PASS |
| UNIQUE no-advice behaviour unchanged | `TestALiveUniqueCollisionCarriesNoRevokeAdvice::test_a_duplicate_name_mint` (live store) green in baseline, red under M-c | PASS |
| cancellation propagates | bare `raise`; M-e reddens 9 + the AST one-handler pin | PASS |
| N-3 (d) outer message cause-neutral | M-d reddens 9 | PASS |

### 5a. Where the 530 full-suite reds live, and whether the BUILD moved any of them (file-granular ownership masks that)
Targeted runs over the 32 owned files (`pending_contracts.yaml` `bounds[*].files`, derived by script) in the
scratch tree, waiting gate + 16 GiB cap, `-n 8`:

| tree | result |
|---|---|
| BUILD bytes (c67cc356… / 4ebe3712…) | **530 failed, 1310 passed, 2 skipped** (348 s) |
| HEAD production bytes (`git show HEAD:` → 27d06f08… / e2b15f7f…) | **530 failed, 1310 passed, 2 skipped** (339 s) |
| red-id diff BUILD vs HEAD | **∅** — the only differing parsed line is a captured log record (`_txn.py:1015` → `:1050 store.transaction.rolled_back`), a line shift from the added tuple, not a test id |

So: the full suite's 530 reds are exactly the owned files' 530 (equal counts; the gate certified 0 orphans), **the
build adds 0 reds and removes 0 reds inside owned files**, and the brief's expected owned families are present
(`test_exhaustion_fates.py` ×1, `test_reanchor_58_r4_lease_fates.py` ×4) among 58's and 64b-i's contract-ahead
cells. Per-file red counts (build): comms_footer 81 · 64b findings files 170 (adversary 13, classes 27,
enforcement 4, governance 24, identity 22, migrate 28, schema 17, scope_domain 24, signatures 2, system_writer 9)
· governed_substrate_64b 34 · mcp_server 28 · 58 reanchor/task files 211 (incl. the 4 r4 lease-fates cells) · exhaustion_fates 1 · blocks_edge 1 ·
task_read_surface 1 · scripts/test_forgery_door_sweep 3. Scratch restored to build bytes after (md5 printed).
**Whole-suite denominator:** `--collect-only` (same testpaths the gate's command uses) = **13,799 collected** →
full suite = 530 failed (all owned) + 13,269 passed-or-skipped; the exact passed/skipped split was not captured
by the instrument (#545).

## 8. Instruments (pasted, per brief-base §1)
- Scratch waiting gate `gate_run.sh` (final form):
```bash
#!/usr/bin/env bash
set -u
cd "${GATE_CWD:?}"
need_kib=$((20 * 1024 * 1024))
while :; do
  avail=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
  others=$(pgrep -fa '^[^ ]*python[^ ]* .*(-m pytest|bin/pytest|scripts/pending_contract_gate.py|scripts/wave_gate.py)|^[^ ]*/bin/pytest' | awk -v me="$$" '$1 != me' || true)
  if [ "$avail" -ge "$need_kib" ] && [ -z "$others" ]; then break; fi
  echo "GATE WAIT $(date -Is) MemAvailable=$((avail / 1024 / 1024))GiB others=[$(printf '%s' "$others" | head -c 200)]" >&2
  sleep 20
done
echo "GATE PASS $(date -Is) MemAvailable=$((avail / 1024 / 1024))GiB" >&2
exec systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 \
  uv run --with pytest-timeout pytest -n 8 --timeout=300 -p no:cacheprovider "$@"
```
- Mutation runner `runmut.sh <tag> <file> <anchor-file> <replacement-file>`: `cd` scratch; build `--expect-red`
  args from `<tag>.declared` (written from `--collect-only` before the run); `mutation_proof.py --file …
  --anchor-file … --replacement-file … <args> -- gate_run.sh -q -rf <T>`; then diff observed `FAILED` ids vs
  declared both ways and print the file md5. Anchors/replacements, verbatim:
  M-a `    catch: tuple[type[SurrealStoreError], ...] = _DEFAULT_REJECTION_CATCH,` → `… = _PROVEN_NO_KEY_FAULTS,` ·
  M-b `    TxnParamCollisionError,\n    TxnEnvelopeViolationError,\n)` → `    TxnParamCollisionError,\n)` ·
  M-c `        fault = cls._classified_fault(error)` → `        fault = error` ·
  M-d `                    "its outcome is unknown",` → `                    "it was interrupted; its outcome is unknown",` ·
  M-e `                error.add_note(note)\n            raise` → `…add_note(note)\n            if type(error).__name__ == "CancelledError":\n                return None  # type: ignore[return-value]\n            raise`.
- Owned-file census `owned_pair.sh`: run the 32 owned files on build bytes, swap in `git show HEAD:` production
  bytes, re-run, restore build bytes, diff the parsed red sets.

## md5 receipts — END (2026-10-05 12:43Z, HEAD cc834ca)
| file | md5 | = START |
|---|---|---|
| loremaster/loremaster/principal_keys.py | c67cc35659e0ddc5518816825e5ad0c7 | yes |
| loremaster/loremaster/store/_txn.py | 4ebe3712beba2963902eb1745e9b80ce | yes |
| loremaster/tests/test_mint_unknown_outcome_note_q1.py | 90a6d1402831d6432f1970ab8f54ce10 | yes |
| scripts/pending_contracts.yaml | b0158ed1189ea905faf9c8d8b9f87f76 | yes |
| q1-BUILD.patch | a755a8a482e42e740ac484035b06c818 | yes |
| `git diff` of the working tree (all tracked) | a755a8a482e42e740ac484035b06c818 | **== the patch**; `git apply --check -R` clean |
No tracked file edited, no git state mutated, no worktree, no stash. Every mutation ran in the scratch copy.
