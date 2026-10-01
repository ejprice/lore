brief-base v18 read · brief project v7 read

# REPORT-builder-63c-i-a-a28c — the 63c-i-a fix build (am-27…37) over the a28/a28b/a28c contract

*Every claim is scoped to the tree it names. **Build tree** = a `scratch_copy.sh` copy reset to `bbf6a0c`
(the spawn HEAD) + this build. **Base tree** = a second `scratch_copy.sh` copy reset to `ad6e8ce` (HEAD at baseline
time). `bbf6a0c → a77dc00` (main HEAD at report time) moved ONLY docs/reports (`git diff --stat bbf6a0c a77dc00`:
`REPORT-*`, `docs/design/…amendment-37.md`, `…packet58-amendment-12.md`) — production and tests are byte-identical
across all three shas. Both trees carry a28c §A.8 `held_harness.patch` (lead directive #17124). Measured
2026-09-29 20:37Z–21:25Z on spike-surreal `ws://127.0.0.1:18000` (engine `surrealdb-3.2.4+20260803.93ab219`).*

## SUMMARY BLOCK
- **State: done-with-deviations** (production NOT committed — the lead commits after the cold audit; backup §BACKUP).
- **Deviations** (§DEV): D-1 two structural pins keyed on the pre-F-11 shape satisfied by PROSE naming the ONE ladder
  (fork FK-B1, one native ping) · D-2 FK-8 plumbing consolidated (one typed record + ONE sentence template; the
  reference had the sentence in 3 places) · D-3 reference's `ruff format` noise reverted by an AST-equivalence tool ·
  D-4 `_domain_root_cause` no longer skips an empty-text entry (spec-silent — flagged) · D-5 `Cancelled` cascade kind
  observed live, not in `_CASCADE_KIND` (harmless by ordering — flagged) · D-6 my own A4 docstring regression, caught
  by the contract, fixed.
- **Packages considered:** `surrealdb.errors` 2.0.0 — `parse_query_error` + `ServerError.kind/.details` → replace_with_adapter;
  `ErrorKind.{THROWN,INTERNAL,VALIDATION}` + `QueryDetailKind.NOT_EXECUTED` → replace (constants bound to the SDK's);
  `surrealdb.errors._detail_kind` → keep_with_trigger (private; trigger: the SDK exports it); no SDK constant for
  `TransactionConflict` → bespoke string, read from the installed `errors.py` (§PKG).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 21 new production symbols, all dispositioned (§DRY).
- **Graded:** n/a (builder).
- **Decisions needed:** (1) FK-B1 — accept the prose repair of the two pre-F-11 structural pins, or route an AST re-key
  to the next `_txn` contract (am-37 §W row 4) · (2) D-4 empty-text root-cause skip dropped — confirm · (3) D-5
  `details.kind: Cancelled` — keep out of `_CASCADE_KIND`?
- **Result:** declared set (67 files) base 767 red → build 331 red, **398 RED→GREEN, 0 GREEN→RED**, every remaining
  red owned by `packet-58-contract` / `packet-64b-i-contract` · 20/20 concurrency · currency typecheck
  RED_ADJUDICATED (58/64b-owned) + ruff GREEN · F-11 live both ways + 2 sharing mutations · KF 2/2.
- **Pointers:** RED→GREEN §TABLE · F-11 receipts §REQ-1 · THROW read §REQ-3 · consumers §REQ-4 · DUAL §DUAL ·
  backup §BACKUP · instruments §A.


## §0 Capability check (brief-base §4)
- **lore: reachable.** `lore_index()` 2026-09-29 ~20:54Z: watched root `/workspace` = the MAIN tree (branch
  `feat/surreal-unification`), last_sync 74 s. It does NOT index my scratch copies, so every `lore_impact` answer below
  is about HEAD's production (the consumer set my build changes), never my build.
- **`lore_impact` caps covering tests at 15 (#518)** — `execute_transaction` reports 1840 covering tests, `run_query`
  253, `migrate_governed` 353, all elided to 15. Fallback SAID: an AST scan (`covering_scan.py`, §A.3) over
  `loremaster/tests/test_*.py` + `scripts/test_*.py`.
- **grep/rg are hook-blocked (#473)** — every textual sweep below is `awk`, said here once.
- **Reading `_FailedStatement` field readers is a non-symbol attribute seam** — `lore_impact` answers the call-level
  consumers; the `.raw_result` / `.typed` readers were enumerated by `awk` (§REQ-4).
- No deadline conflict; no role-boundary conflict (I wrote no test; I applied the contract-authored §HELD patch as-is
  on lead directive #17124, acked).

## §1 What was built — per amendment (27–37)
Production files (build tree vs `bbf6a0c`): `store/_txn.py`, `governed.py`, `principals.py`, `server.py`,
`agents.py`, `keeps.py`; registry: `scripts/pending_contracts.yaml` (deletion only); §HELD: `test_surreal_harness.py`
(a28c §A.8, contract-authored). Method: the reference chain (a28 `reference_fix.patch` md5 `0abdf6d8…` exact → a28b
interdiff → a28c `myref_a28c_{txn,migrate,am36,fk8}.py`, md5 exact vs a28c §A.5) was APPLIED, then every hunk was
read and the build was changed where I own a better shape (D-1…D-5, REQ-1…4). The a28b interdiff extracted from the
committed report is md5 `9166f58a…`, not the stated `95935c21…` (the report's copy differs, e.g. in whitespace); it
applied cleanly after a `patch -p1 --dry-run`. The reference is a starting point; what ships is this build.

| am | what | where (symbol) | receipt |
|---|---|---|---|
| 27 | (folded into a28) | — | a28 pins GREEN §TABLE |
| 28 §F-1 | register compensation DELETED (created-only delete + ALSO-line + `minted_by_this_call`) | `server.AppContext` register handler; `keeps` | a28b R-2 retired-name pin GREEN; DUAL §DUAL rows 7–8 |
| 28 §F-2 | READ-ONLY SF-63-1 gate BEFORE `preflight` | register handler, `_sf_63_1_gate` (D-2b) | a28 C2 / KC pins GREEN |
| 28 addendum F-4/F-6/F-7 | INFO FOR DB fail-closed; docstrings derived; message backfill self-guards on sender | `principals._agent_migration_preconditions`, `_governed_select`, `_migrate_message_owner` | A4 pin GREEN (after my own regression, §DEV D-6) |
| 29 RS-5 | CREATE collision → re-read → the re-register path | `agents.AgentRegistry.register` | RS-5 pins GREEN; 20× §CONC |
| 30/31 | `MigratePreconditionCounts` + `preconditions`; owner fields; describe derived from fields | `governed`, `principals._measured_counts`, `_owned_unscoped_part` | a28 am-30/31 pins GREEN |
| 32 §1 | typed `TxnUniqueViolationError`; ONE predicate both CAS doors | `_txn`, `keeps`, `agents` | a28b pins GREEN |
| 32 §2 | a field is `None` iff its read was gated off, ∀ outcomes; message problem parts | `principals._measured_counts`, `_message_problem_parts` | a28b FK-ADV-2 pins GREEN |
| 33 | the class NAME + label | `_txn.TxnUniqueViolationError`, `_ERROR_CLASS_UNIQUE_VIOLATION` | ibid. |
| 34 | `"empty"` + validator; `total/admin_principals`; F-5 `defined_tables` / `table_defined` | `governed`, `principals` | a28c F-5 / am-34 pins GREEN |
| 35 §2 | R typed both paths; record text pair deleted; U prefix-anchored first; governed marker anchored at the THROW prefix | `_txn._classify_engine_error`, `_failed_statements` | a28c KB pins GREEN; §REQ-3 live read |
| 35 §3/§4 | scanner per handler; R-4 read tags | `governed` field tags (scanner is test-side) | a28c pins GREEN |
| 36 §1 | ONE parse per failed statement (`typed`); retry + cascade decided by `details.kind`; both text markers deleted | `_txn` | 15 re-keyed pins GREEN; KF 2/2 (§REQ-2) |
| 36 §2 | FK-4 `table_defined: bool \| None`; FK-8 one per-call resolution record | `governed`, `principals` (D-2) | a28c FK-8 pins GREEN |
| 37 §1 | text decides a LABEL only for `{Internal, Validation, Thrown}` — keyed per kind | `_txn._classify_engine_error` | a28c allowlist pins GREEN |
| 37 §3 | F-11: ONE ladder for both paths | `_txn._raise_attempt_failure` | §REQ-1 (live, both ways + 2 sharing mutations) |
| 37 §4 | F-1: cascade decided ONLY by `details.kind == _CASCADE_KIND`, constant beside `_RETRYABLE_CONFLICT_KIND` | `_txn` | KF probe 2/2 build, 0/2 base |

## §DEV Deviations and forks (written before the ping)
- **FK-B1 / D-1 — two pins keyed on the PRE-F-11 shape (fork; pinged the lead once; continued on my pick).**
  am-37 §3 requires ONE ladder helper called by BOTH `run_query._attempt` and `_txn_query_raw`, and REFUSES a second
  inline copy. Two existing pins read the old shape textually/lexically and went RED on my first build (both GREEN at
  base, so these were build-caused, not inherited):
  1. `test_surreal_store.py::TestDomainRejectionErrorType::test_both_domain_raise_sites_build_their_rejection_via_the_one_mapping_helper`
     asserts the SOURCE TEXT of `run_query` contains `_domain_rejection_error`. After F-11 the domain raise lives in
     `_raise_attempt_failure` (which does call `_domain_rejection_error` — the ONE mapping is kept, more strongly).
  2. `test_retry_seam.py::TestTheSignalsChainingUniversalHoldsOverThePopulationItIsTrueOf::test_the_drivers_explanation_NAMES_every_caller_that_raises_UNCHAINABLY`
     AST-walks `raise RetryableConflictSignal()` sites; one not lexically inside an `except` must be NAMED in the
     comment above `last_conflict_cause`. `_raise_attempt_failure` raises it `from error` (the caught exception,
     passed in) — chained, but not lexically inside a handler.
  - **Reading A (my pick, built):** keep the ONE helper; repair the PROSE, truthfully — `run_query`'s handler comment
    now names `_domain_rejection_error` as the mapping the shared ladder builds with, and the `last_conflict_cause`
    comment names `_raise_attempt_failure` and why its raise has the cause in scope. Both pins GREEN. Cost: pin 1 is
    now satisfied by a comment, i.e. it no longer discriminates a `run_query` that bypasses the mapping (the helper
    is its only raise site, but a text pin cannot see that).
  - **Reading B (not built):** inline the domain tail back into both call sites → copy #2 of the ladder, which am-37
    §3 item 1 refuses by name.
  - **Recommendation:** accept A; re-key pin 1 to an AST/call-graph property ("every domain raise site in `_txn` calls
    `_domain_rejection_error`") in the next `_txn`-touching contract (the same place am-37 §W row 4 routes the
    derived-domain ladder pin). No test was edited by me.
- **D-2 — FK-8 plumbing consolidated.** The reference (a28c §A.5d, "a SAT HOST, not a spec") carried the
  unresolved-operator sentence in THREE places (the leg's `_operator_unresolved_legacy`, the verb's marker renderer,
  and an inline f-string in `_verb_level_refusal`) and a `dict[str, int]` record. Built: ONE template
  `_operator_unresolved_sentence(purpose, *, total_principals, admin_principals)`, every renderer calls it; the record
  is a typed `@dataclass _OperatorResolution` in the `ContextVar`; the out-of-verb fallback (unreachable from
  production — no caller outside `migrate_governed` reaches a leg; awk over tests + package) measures and renders the
  SAME template. **D-2b:** the register handler's two SF-63-1 evaluations (read-only pre-preflight, post-mint) call ONE
  local `_sf_63_1_gate` (the exact expression constraint 2 names, through the call-time `resolve_visible_keeps`
  binding); the reference's production `assert keep_store is not None` is replaced by an explicit condition.
- **D-3 — the reference's `ruff format` pass (a28 D-4) reverted.** The base files are not `ruff format`-clean, so the
  reference's reformat of untouched lines was pure diff noise. `revert_cosmetic_hunks.py` (§A.4) reverted every hunk
  whose reversal leaves `ast.dump` of the module unchanged (principals 14, governed 3, _txn 1). ⚠ It also reverted one
  hunk whose only change was a trailing comment (`# noqa: PLR0911` on `_classify_engine_error`) — caught by ruff,
  restored, and a check over every reverted hunk showed it was the only comment-bearing one.
- **D-4 — `_domain_root_cause` no longer skips an empty-text entry (spec-silent → flagged).** Old: first entry whose
  text is non-empty AND carries no cascade marker. New (the reference's, kept): first entry whose `details.kind` is not
  `NotExecuted` (am-36 §1.1 "decides `details.kind == "NotExecuted"`"). An ERR entry with empty text and a
  substantive kind is now selected (its KIND still classifies it). No ruling mentions the empty-text clause.
- **D-5 — `details.kind: Cancelled` exists (measured, §REQ-3).** A statement AFTER the offender reports
  `{"kind": "Query", "details": {"kind": "Cancelled"}, "result": "The query was not executed due to a cancelled
  transaction"}`. The retired text marker `was not executed due to` matched it; `_CASCADE_KIND` (`NotExecuted`, as
  ruled) does not. Selection is unchanged in every measured shape because the offender always precedes a `Cancelled`
  entry; the only behavioural difference is the degenerate no-substantive-entry fallback (now the first `Cancelled`
  entry rather than the COMMIT notice). am-36's "every cascade notice = `NotExecuted`" is incomplete on 3.2.4. Not
  widened (a ruled constant); lead/sidecar call.
- **D-6 — a self-inflicted regression, caught by the contract.** My first rewrite of `MigrateGovernedResult`'s
  docstring re-stated "a refusal returns before any scan of the target table" — the exact sentence a28 A4 pins as
  false. `test_A4_no_docstring_claims_a_refusal_scans_nothing` went RED on build run 2; fixed (the docstring now says
  the two `None`s are the LEG's own counts; the precondition reads that DID run ride `preconditions`).

## §REQ-1 F-11 (am-37 §3) — ONE ladder helper, both paths
- **Built:** `_txn._raise_attempt_failure(error, connection, *, drop, url, noun, label, logger) -> NoReturn` — the
  three fates (transport → `drop` + `SurrealConnectionError`; `is_retryable_conflict_error` → `RetryableConflictSignal`;
  else `_classify_engine_error` → log under `label`/`logger` → raise `_domain_rejection_error(...)`, message = label +
  `_SERVER_LOG_HINT`, never the engine text). Called by `run_query._attempt` (its seam's own `label`/`logger`, F6
  preserved) and `_txn_query_raw` (`noun="transaction"`, `label=_TXN_REJECTION_LABEL = "store.transaction.rejected"`,
  `_txn`'s own `logger`). No membership/prefix/regex test inside it (the four-tester allowlist is untouched).
  `_txn_query_raw`'s documented self-heals are preserved by construction: `NotAllowed` (auth-after-reconnect) is in
  `_CONNECTION_ERROR_KINDS`; the routing `KeyError` is fate 1.
- **Live receipt, both ways** (`probe_throw_builder.py` §A.1, part B, recursion-depth statement, spike-surreal 3.2.4):
  ```
  BASE  [B] recursion-depth run_query:           TxnDomainRejectionError drops=0 "(query too complex — …); see the server log…"
  BASE  [B] recursion-depth execute_transaction: SurrealConnectionError  drops=1 "SurrealDB transaction failed against '…': Parse error: Exceeded expression recursion depth limit\n --> [2:1013] …"
  BUILD [B] recursion-depth run_query:           TxnDomainRejectionError drops=0 "(query too complex — reduce or shorten the search terms); see the server log…"
  BUILD [B] recursion-depth execute_transaction: TxnDomainRejectionError drops=0 "SurrealDB transaction rejected against '…' (query too complex — reduce or shorten the search terms); see the server log…"
  ```
- **Sharing by MUTATION** (build tree, `cp -a` content backup of `_txn.py`, md5 `5a72a8e3…` before and after, `cmp`
  restore each time):
  - **M1 (am-37 §3.4):** `ErrorKind.VALIDATION` added to `_CONNECTION_ERROR_KINDS` → BOTH paths serve transport:
    `run_query: SurrealConnectionError drops=1` · `execute_transaction: SurrealConnectionError drops=1`.
  - **M2 (the helper body):** `error_class = _classify_engine_error(error)` → `_ERROR_CLASS_UNSPECIFIED` → BOTH labels
    move: `run_query: … (unspecified rejection)` · `execute_transaction: … (unspecified rejection)`.
  - Control after restore: both paths `(query too complex …)`, drops=0.
  The cold audit re-runs these (am-37 §3.4); this is the builder's smoke, not the grade.

## §REQ-2 F-1 (adversary-a28c WB-H) — the cascade decided by the typed kind only
- `_CASCADE_KIND = QueryDetailKind.NOT_EXECUTED` (the SDK's constant, value `"NotExecuted"`), placed directly beside
  `_RETRYABLE_CONFLICT_KIND = "TransactionConflict"` (the SDK has no conflict constant — read `surrealdb/errors.py`:
  `QueryDetailKind = {NOT_EXECUTED, TIMED_OUT, CANCELLED}`). `_is_domain_cascade_notice(failed)` is
  `_detail_kind(failed.typed) == _CASCADE_KIND`; `_domain_root_cause` reads nothing else. No str method, `re`, compiled
  pattern or `from re import` anywhere in the decision (the retired text markers are gone — §SWEEP).
- The same holds for every engine-typed decision (am-36 §1): the retry decision (`_is_retryable_conflict_kind`, both
  paths), the record shape (`isinstance(AlreadyExistsError) and record_id is not None`). Text decides a LABEL only,
  keyed PER KIND (the optional form am-37 §1 allows, which makes the pin-4 bound vacuous): `Thrown` → our anchored
  governed prefix only; `Internal` → U prefix at position 0, then ASSERT, coercion; `Validation` → recursion; a bare
  string (untyped legacy input) → the whole ladder; every other kind → `unspecified rejection`.
- **KF smoke** (adversary §A.4, KF half only — the KG half imports the contract module and needs the package's test
  layout; md5 of the full probe `a6f497df…` = the adversary's): build `2 passed`; base `2 failed` (no `typed` carrier).
- **Live echo receipt** (part B, `THROW "some other failure: value can be retried"`): base run_query →
  `TxnContentionExhaustedError … gave up after 53 attempts over 2.082s`, execute_transaction → `… 64 attempts over
  3.060s` (am-36's ~2 s misclassification, reproduced); build → `TxnDomainRejectionError (unspecified rejection)`,
  one attempt, both paths.

## §REQ-3 Rider — the LIVE governed-THROW wrapping on BOTH paths (read BEFORE anchoring; spike-surreal 3.2.4)
Raw, from `probe_throw_builder.py` part A (the `governed-guard` statement is `GuardedPlan.fragments`' shape:
`LET $gw_hit = (SELECT …); IF array::len($gw_hit) = 0 { THROW "governed_conflict:<t>:<id>" }`):
```
[A] bare-governed-throw query(): ThrownError kind='Thrown' details=null message='An error occurred: governed_conflict:guarded:x'
[A] bare-governed-throw query_raw()[1]: {"kind": "Thrown", "result": "An error occurred: governed_conflict:guarded:x", "status": "ERR", "time": "6.54µs", "type": null}
[A] bare-governed-throw query_raw()[2]: {"details": {"kind": "NotExecuted"}, "kind": "Query", "result": "Cannot COMMIT: the transaction was aborted due to a prior error", "status": "ERR", "time": "0ns", "type": null}
[A] governed-guard query_raw()[1]: {"details": {"kind": "NotExecuted"}, "kind": "Query", "result": "The query was not executed due to a failed transaction", "status": "ERR", "time": "106.8µs", "type": null}
[A] governed-guard query_raw()[2]: {"kind": "Thrown", "result": "An error occurred: governed_conflict:guarded:missing", "status": "ERR", "time": "11.89µs", "type": null}
[A] governed-guard query_raw()[3]: {"details": {"kind": "NotExecuted"}, "kind": "Query", "result": "Cannot COMMIT: the transaction was aborted due to a prior error", "status": "ERR", "time": "0ns", "type": null}
[A] non-governed-throw query(): ThrownError kind='Thrown' details=null message='An error occurred: some other failure: value can be retried'
[A] recursion-depth query(): ValidationError kind='Validation' details=null message='Parse error: Exceeded expression recursion depth limit\n --> [1:1013] …'
```
From the first (table-less) run of the same probe — the post-offender `Cancelled` kind (D-5):
```
[A] governed-guard query_raw()[1]: {"details": {"details": {"name": "guarded"}, "kind": "Table"}, "kind": "NotFound", "result": "The table 'guarded' does not exist", "status": "ERR", …}
[A] governed-guard query_raw()[2]: {"details": {"kind": "Cancelled"}, "kind": "Query", "result": "The query was not executed due to a cancelled transaction", "status": "ERR", "time": "0ns", "type": null}
[A] governed-guard query_raw()[3]: {"details": {"kind": "NotExecuted"}, "kind": "Query", "result": "Cannot COMMIT: the transaction was aborted due to a prior error", …}
```
Conclusion: the governed THROW is `kind: Thrown`, `details: None`, text `An error occurred: <thrown>` at position 0 on
BOTH paths — `_ENGINE_THROW_PREFIX = "an error occurred: "` (compared lower-cased) anchored + `_GOVERNED_CONFLICT_MARKER`
is correct as ruled. Served class through the build: `TxnGovernedConflictError` on both paths (part B).
⚠ Observed, pre-existing, NOT changed: `governed-guard run_query: NO ERROR` — a multi-statement string through
`query()` validates statement[0] only (store-ref §3 bullet 1); production never sends the guard through `run_query`.

## §REQ-4 Rider — `_failed_statements`' typed shape change; every consumer migrated
- **Shape:** `_FailedStatement(index, raw_result, typed: ServerError | None = None)` — `typed` is the ONE
  `parse_query_error` of the per-statement dict, made in `_failed_statements` iff the entry carries a `kind`
  (a two-argument construction still works; the contract constructs `typed=…`).
- **Derivation of the consumer set:** `lore_impact loremaster.store._txn._failed_statements` → 1 prod consumer
  (`_run_verified_transaction`), 0 tests; `lore_impact …_FailedStatement` → 1 prod consumer (`_failed_statements`),
  test module `test_surreal_store`. Attribute readers are a non-symbol seam → `awk` over every `*.py` in
  `loremaster/loremaster`, `lorerunes`, `lorescribe`, `loresigil` for `.raw_result` / `.typed` / `_FailedStatement`:
  36 hits, ALL in `store/_txn.py`, in these functions:
  | consumer | reads | migrated to |
  |---|---|---|
  | `_is_retryable_conflict` | was `str(raw_result)` text | `typed` kind |
  | `_rollback_verdict` (conflict root cause) | was text | `typed` kind |
  | `_domain_root_cause` → `_is_domain_cascade_notice` | was text | `typed` kind |
  | `_run_verified_transaction` → `_typed_root_cause` → `_classify_engine_error` | was `raw_result` | `typed` (else raw text) |
  | `_log_rollback` | `raw_result` | unchanged — EVIDENCE for the server log only |
  No consumer outside `_txn`.

## §CHECK a28c §BUILDER CONSTRAINTS (binding) — item by item
1. `_txn` — ONE parse per failed statement, `typed` defaulted field ✅; retry decision typed via
   `_RETRYABLE_CONFLICT_KIND` on both paths ✅; root-cause selector typed (`NotExecuted`), degenerate fallback kept ✅;
   `_RETRYABLE_CONFLICT_MARKER` + cascade text markers DELETED (§SWEEP) ✅; classifier typed-first: record shape by
   `isinstance(AlreadyExistsError) and record_id is not None`, other `AlreadyExistsError` → unspecified ✅; governed by
   `Thrown` + anchored prefix, THROW wrapping re-read live (§REQ-3) ✅; text only for Internal (U first, then ASSERT,
   coercion) and Validation (recursion) — and, per am-37 §1 (supersedes "Internal only"), `Thrown` for our prefix ✅;
   bare text keeps the ladder ✅; record text pair DELETED ✅; EVERY raise via `_domain_rejection_error` ✅ (the ladder
   helper included); exactly ONE text-testing function for engine text and no NEW tester (the helper has none) ✅ — the
   a28c exact-set pin is GREEN; typed decisions compare with `==` ✅; §HELD harness patch applied ✅ (directive #17124).
2. SF-63-1 gate: exactly `keep_scope(bare) in await resolve_visible_keeps(keep_store, member_email=…)` through the
   call-time import binding, nothing else decides, preflight AFTER the read-only gate ✅ (now ONE local
   `_sf_63_1_gate` evaluated twice — D-2b).
3. `MigratePreconditionCounts`: 8 fields + `total_principals`, `admin_principals` in ruled order, each
   `Field(default=None, json_schema_extra={"read": …})`, classification Literal incl. `"empty"` (as `OwnerClassification`),
   `model_validator` for the triple, `extra="forbid"` ✅; `MigrateGovernedResult.table_defined: bool | None` (`None` on
   the invalid-table refusal) ✅.
4. principals: `"empty"` when the agent read ran with no owned-but-unscoped row ✅; ONE resolver per call feeding
   the two fields, `None` iff none ran ✅; every unresolved sentence derived from the two FIELDS through ONE template
   (D-2) ✅; `defined_tables` from the one `INFO FOR DB` ✅; undefined target → `table_defined=False, scanned=0,
   backfilled=0, refused=False` before any leg read ✅; CLI sentence iff `table_defined is False` (the reference used
   `not`, which also fires on `None` — tightened), exit 0 ✅; `"empty"` adds no owner sentence ✅.
5. RS-5 and keeps SAFE-BY-TYPE (`except TxnUniqueViolationError:` only) ✅; `record_measurement`'s tuple guard
   untouched ✅; no NEW domain handler added (the ladder helper is not a catch site) ✅.
6. The three CAS handlers propagate exhausted contention as the SAME instance ✅ (untouched; the 58-r3 cas_seam rows
   that stay red are 58-owned — §TABLE).
**a28b §10 (carried):** 1 ✅ (class name, label, ONE mapping) · 2 ✅ (RS-5: ONE CREATE, re-read, re-register) · 3 ✅
(keeps narrowed; `test_keeps_store.py` in the declared set, GREEN) · 4 ✅ (`minted_by_this_call` gone from the
package — bare awk sweep: 0 hits in `loremaster/loremaster`) · 5 ✅ · 6 ✅ · 7 ✅ (63c-i-a first; 58's
`_ROLLBACK_LOG_TIERS` NOT built — 58's) · 8 ✅ (`# noqa: PLR0911` kept).

## §SWEEP retired names (bare, anchor-free awk) — build tree, every `*.py`/`*.md` outside `.venv`
Patterns: `RETRYABLE_CONFLICT_MARKER`, `DOMAIN_CASCADE_MARKERS`, `CASCADE_NOT_EXECUTED_MARKER`,
`CASCADE_COMMIT_ABORTED_MARKER`, `is_retryable_conflict_text`, `UNIQUE_VIOLATION_MARKERS`, `minted_by_this_call`.
Production (`loremaster/loremaster`, `lorerunes`, `lorescribe`, `loresigil`): **0 hits** after the docstring repairs
(five `_txn` docstrings taught the retired markers after the reference was applied — `is_retryable_conflict_error`,
`_rollback_verdict`, `_domain_root_cause`, `execute_transaction`, `_is_retryable_conflict` — all rewritten).
Outside my writable set (FLAGS, not edits):
- `docs/reference/surrealdb-31-capabilities.md:452` — §3 bullet 2 cites `_CASCADE_NOT_EXECUTED_MARKER =
  "was not executed due to"` as the live mechanism. After this build it is typed (`_CASCADE_KIND`). Suggested edit:
  replace the sentence with "`_txn._domain_root_cause` picks the first entry whose `details.kind` is not
  `NotExecuted` (`_CASCADE_KIND`, am-36) — note a post-offender statement is `Cancelled`, not `NotExecuted` (measured
  3.2.4)". Same file §3 bullet 4 says the only conflict signal is the `"can be retried"` substring and "#111 ANSWERED
  — keep the substring" — now stale: the decision is `details.kind == "TransactionConflict"` (am-36).
- `scripts/probe_supersede_throw_rollback.py:159` — prose mentions `_RETRYABLE_CONFLICT_MARKER` in a printed
  explanation string (a probe script, not served). Verdict: stale prose, harmless; suggest "`_RETRYABLE_CONFLICT_KIND`".
- Test files mention the retired names only inside DUAL comments / the retired-name pins (a28c §5).
- Residual hits in `docs/design/*amendment-{28,32,36}.md`, `docs/plans/v2/receipts/**` (26 files) and
  `docs/plans/v2/INDEX.md:1122` (an append-only Log line) are HISTORICAL records describing the mechanism at their
  own dates — verdict each: historical, not edited (outside my writable set anyway).

## §SET The declared test set (declared 20:58Z, BEFORE the base run; md5 of the list `b16b77b4…`, 67 files)
Derivation, three parts:
1. **Contract files (14):** the 8 files of the `packet-63c-i-a-a28-contract` registry entry + the test files touched by
   `7017b54` / `e039c64` / `d334042` (`git show --stat`) + `test_surreal_harness.py` (the §HELD patch).
2. **Covering tests (64 files incl. overlap):** `lore_impact` capped at 15 (#518) for every changed symbol I queried
   (`run_query` 253, `execute_transaction` 1840, `migrate_governed` 353, `_FailedStatement` 247) → fallback
   `covering_scan.py` (§A.3): every `loremaster/tests/test_*.py` / `scripts/test_*.py` whose AST NAMES a changed
   production symbol (57 names: the `_txn` classifier/ladder/verdict/mapping/classes/constants, `run_query`,
   `execute_transaction`, `retry_on_conflict`, the governed/principals migrate symbols, `get_or_create_keyed`,
   `preflight`, `AgentRegistry`, `resolve_visible_keeps`, `minted_by_this_call`).
   ⚠ Bound: a test reaching a changed symbol only transitively (through a store verb) without naming it is NOT in the
   set — the cold audit's full suite covers that.
3. **Structural pins:** `test_mcp_server.py` (also covering), `test_retry_seam.py` (also contract),
   `scripts/test_forgery_door_sweep.py` (also covering), `test_text_hygiene.py`, `test_memory_f5_registration_63b_ib.py`,
   and — added by hand because `scripts/` is not in lore's graph (#507) and I edited the registry —
   `scripts/test_pending_contract_gate.py`.

## §TABLE RED@HEAD → GREEN (declared set, both trees, junit per-test outcomes; `junit_compare.py` §A.5)
Every run: `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8
--timeout=300`, MemAvailable ≥ 20 GiB checked before each launch (23.5–27.1 GiB observed; no waits needed). No cap
kill, no timeout.
| tree | passed | failed | skipped | collected | wall |
|---|---|---|---|---|---|
| base (`ad6e8ce` + §HELD) | 5292 | 767 | 18 | 6077 | 9m26s |
| build (`bbf6a0c` + build) | **5692** | **331** | 18 | 6041 | 10m44s |

- **RED→GREEN: 398** (a28 87 · a28c 210 · retry_seam 69 · a28b 22 · a19a 2 · harness 2 · exhaustion_fates 1 ·
  surreal_store 1 · 4 module-level: a19b KP2/KP3, a28b K9-domain, a28b R2-retired-name).
- **GREEN→RED: 0.**
- **RED→RED: 331 — every one owned** (file → registry entry, derived from `scripts/pending_contracts.yaml`):
  `packet-64b-i-contract`: test_comms_footer 81 · test_mcp_server 28 · test_governed_substrate_64b 34 ·
  test_findings_{classes 27, governance 24, migrate 28, schema 17, scope_domain 24, system_writer 9}_64b;
  `packet-58-contract`: test_reanchor_58_r2_rulings 27 · test_reanchor_58_r3_am6 8 · _r3_tiers 16 · _r3_cas_seam 4 ·
  test_blocks_edge 1 · scripts/test_forgery_door_sweep 3. The r3_tiers `TxnUniqueViolationError` legs the 58 entry
  says "need 63c-i-a's am-33 build" still fail — on 58's own unbuilt `_ROLLBACK_LOG_TIERS`, not on the class (which now
  exists). The r3_cas_seam `findings.py::_run_guarded` / `tasks.py::*` rows are the rows am-12 routes to 58/64b.
- **Reasons unchanged:** `red_reasons.py` (§A.6) compared the first failure line of all 331: 4 differ, none in
  substance — 2 `test_findings_migrate_64b` reprs now include the new `preconditions=` field (the failure is still
  64b's unbuilt trap), 1 listing with shifted `governed.py` line numbers, 1 random WebSocket key.
- **Collection differences (both generated from `_txn`'s `*_MARKER` constant set):** ONLY-IN-BASE 50 (a28c KB cases
  parametrised over the retired markers) · ONLY-IN-BUILD 14 (10 a28c KB cases over `_UNIQUE_INDEX_MARKER`, 4 a28b K9 /
  keeps cases over the new class) — all 14 PASS.
- **Contract-set runs on the way** (14 files, `-rfE`): build 1 → 22 failed / 1605 passed (the 2 FK-B1 pins + 20
  58-owned); build 2 → 21 failed / 1606 passed (the A4 docstring regression D-6 + 20 58-owned); final = the declared
  run above.

## §CONC 20 consecutive greens (store-ref §5) — a28c's driver, md5 `cc18fd08…` = a28c §A.10f
`systemd-run … bash conc20_a28c.sh <build> 20 26` (26 collected by `--collect-only` first; RS-2 8-way × 20 rounds,
RS-5 handler + registry, keeps REAL unique-key 8-way, all of `test_txn_contention.py`), 21:20–21:24Z:
```
run 1: exit=0 :: 26 passed in 12.27s    run 11: exit=0 :: 26 passed in 12.37s
run 2: exit=0 :: 26 passed in 13.00s    run 12: exit=0 :: 26 passed in 13.54s
run 3: exit=0 :: 26 passed in 12.54s    run 13: exit=0 :: 26 passed in 12.99s
run 4: exit=0 :: 26 passed in 12.61s    run 14: exit=0 :: 26 passed in 12.58s
run 5: exit=0 :: 26 passed in 13.35s    run 15: exit=0 :: 26 passed in 13.26s
run 6: exit=0 :: 26 passed in 12.49s    run 16: exit=0 :: 26 passed in 11.79s
run 7: exit=0 :: 26 passed in 12.28s    run 17: exit=0 :: 26 passed in 12.21s
run 8: exit=0 :: 26 passed in 12.68s    run 18: exit=0 :: 26 passed in 12.78s
run 9: exit=0 :: 26 passed in 12.36s    run 19: exit=0 :: 26 passed in 12.53s
run 10: exit=0 :: 26 passed in 13.06s   run 20: exit=0 :: 26 passed in 12.28s
ALL 20 CONSECUTIVE GREEN
```

## §GATES
- `ruff check .` over `loremaster/loremaster/` — `All checks passed!`; and the currency leg below.
- **`pending_contract_gate.py --currency --legs typecheck,ruff`** (build tree, after the registry deletion, no `-n`):
  ```
  typecheck    RED_ADJUDICATED — 78 residual(s), owned by: packet-58-contract (…) · packet-64b-i-contract (…)
  ruff         GREEN
  pytest       NOT_RUN — claimed by the manifest, never executed
  CURRENCY   : FAIL — claimed but never run: pytest
  ```
  Both requested legs are non-orphaned (typecheck adjudicated to the two OTHER packets, ruff GREEN; 0 RED_ORPHANED).
  The overall `FAIL` line is ONLY the `pytest` leg the brief excludes (`--legs`), which the gate reports as a
  claimed-but-unrun gate (#312). ⚠ Brief wording "must end GREEN": the per-leg verdicts are as above; the tool's
  overall line cannot read GREEN with `--legs typecheck,ruff` — flagged, not worked around.
- **Typecheck** (`scripts/typecheck.sh` inside the leg): the only production error it found on my first pass
  (`principals.py` `owner_classification: str | None` vs the Literal) is fixed; every residual is in 58/64b-i
  contract test files (their registry entries).
- **Registry:** `packet-63c-i-a-a28-contract` DELETED (56 lines, the entry + its leading comment block) — its
  trigger symbols all land (`MigratePreconditionCounts`, `.preconditions`, `.table_defined`,
  `TxnUniqueViolationError`, `_RETRYABLE_CONFLICT_KIND`) and none of its 8 files has a red left in the declared run.
- **Test store:** `lore_test` held 30 databases after my runs (no pre-run count taken — no growth claim either way).
  My probe namespace `b63cprobe` was removed (`REMOVE NAMESPACE`, verified gone). `:18500` never touched; no TEI call.

## §DUAL Removed-behaviour inventory (every deleted or replaced production branch; build vs `bbf6a0c`)
| # | removed / replaced | verdict | spec |
|---|---|---|---|
| 1 | `_is_retryable_conflict_text` + `_RETRYABLE_CONFLICT_MARKER` ("can be retried" in text → retry) on BOTH paths | replaced by `_is_retryable_conflict_kind` (`details.kind == "TransactionConflict"`); genuine conflicts still retried (20× §CONC; live probe) — an ECHOED phrase no longer retries (live: base 53/64 attempts, build 1) | preserved-with-pin am-36 §1.1 (KB, the 15 re-keyed pins) |
| 2 | `_DOMAIN_CASCADE_MARKERS` text selector | replaced by `_CASCADE_KIND`; all-cascade fallback kept | preserved-with-pin am-36 §1.1 / am-37 §4 (KF) |
| 2a | `_domain_root_cause`'s "text is non-empty" skip | dropped | **spec-silent → lead/operator** (D-4) |
| 2b | the text marker also skipped `Cancelled` post-offender notices | no longer skipped; selection unchanged in every measured shape (the offender precedes them); the degenerate fallback now lands on the first `Cancelled` entry | **spec-silent → lead/operator** (D-5) |
| 3 | `_UNIQUE_VIOLATION_MARKERS` (record + index text pair); unanchored governed marker `in` text; flat ASSERT/coercion/recursion ladder for ANY input | record shape typed; index = position-0 prefix for `Internal`/untyped; governed = `Thrown`/untyped + anchored prefix; labels keyed per kind; any other typed kind → unspecified | preserved-with-pin am-35 §2 + am-37 §1 |
| 4 | `run_query._attempt`'s inline three-way ladder | moved into `_raise_attempt_failure`, same three fates, same seam `label`/`logger`, same raised messages | preserved-with-pin (the #120/#108 ladder pins in `test_retry_seam.py`, GREEN) · am-37 §3 |
| 5 | `_txn_query_raw`: EVERY caught error → `drop` + `SurrealConnectionError` echoing `{error}` | domain kinds keep the connection and raise a hygienic domain rejection; transport/auth/KeyError unchanged | dropped-deliberately, am-37 §3 (F-11) — live both ways §REQ-1 |
| 6 | keeps `except (SurrealConnectionError, TxnContentionExhaustedError): raise` + `except SurrealStoreError:` CAS | `except TxnUniqueViolationError:` only (transport/exhaustion propagate by not being caught; other store errors → the wrap) | preserved-with-pin a28b §10 item 3 / am-32 §1.2 |
| 7 | `keeps.minted_by_this_call`, `_MINTED_BY_THIS_CALL`, the `object.__setattr__` flag | deleted | dropped-deliberately am-28 §F-1 + am-32 R-2 (retired-name pin GREEN) |
| 8 | register handler: created-only compensation (delete the keep on a refused register; the ALSO-line naming the left-behind keep; `comms.register.compensation_failed` log) | deleted | dropped-deliberately am-28 §F-1 ("wrong by design") |
| 9 | register ORDER preflight → mint → gate | read-only gate on an existing keep → preflight → mint → gate on the returned keep | am-28 §F-2 (preserved-with-pin, a28 C2/KC) |
| 10 | `AgentRegistry.register`: a CREATE unique collision propagated | re-read → the re-register path (propagates unchanged iff the row is absent) | am-29 RS-5 (preserved-with-pin RS-5, 20×) |
| 11 | `_migrate_{memory,agent}_*`: `backfilled=unmigrated` (the pre-count) | `backfilled=_rows_stamped(<the UPDATE's return>)` | a28 F-3 / audit P4 (pin GREEN) |
| 12 | `_governed_select` non-list → `[]`; `INFO FOR DB` non-dict → `{}` | both RAISE `SurrealStoreError` (fail closed) | am-28 addendum F-4 |
| 13 | message backfill `WHERE scope IS NONE AND owner_principal IS NONE` | + `AND sender.owner_principal IS NOT NONE AND sender.scope IS NOT NONE` | am-28 addendum F-7 |
| 14 | `_migrate_message_owner`'s own agent-first ORDER refusal | folded into `_message_leg_refusal` (ORDER part first, then row facts, ONE refusal) | am-32 §2.1 (a28b pins GREEN) |
| 15 | `_owned_unscoped_part`: per-owner operator-owned count from Principal comparison | sentence derived from `owner_classification` + `distinct_owner_principals` | am-31 FK-a28-3 |
| 16 | `_operator_unresolved`: always listed principals itself | inside the verb: a `_UnresolvedPurpose` rendered from the counts model; outside: same template, own listing | am-36 FK-8 (D-2) |
| 17 | `migrate_governed` invalid-table refusal had `table_defined` default | `table_defined=None` | am-36 FK-4 |
No branch was removed without a row above; items 2a / 2b are the only spec-silent ones.

## §DRY ledger (brief-base §6) — NEW production symbols
| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `_txn._raise_attempt_failure` | lore_search "shared helper that classifies a failed SurrealDB SDK call as transport (drop connection), retryable conflict, or domain rejection" | am-37 §3 (the ruling) — no existing helper; the ladder lived inline in `run_query._attempt` | EXTENDED `run_query._attempt`'s ladder: MOVED into one function both paths call (not forked); proven by M1/M2 |
| `_txn._TXN_REJECTION_LABEL` | (constant; awk `store.transaction.` over package + tests) | `store.transaction.rolled_back`, `…malformed_response` | HAND-ROLLED — a distinct event (a request refused as a whole ≠ a per-statement rollback); pins read `rolled_back` levels, which must not absorb this |
| `_txn._detail_kind` | lore_search "read details.kind from a typed SurrealDB ServerError details dict" | adversary-a28c §Packages: SDK's private `surrealdb.errors._detail_kind` | HAND-ROLLED 4 lines — the SDK's is private (keep_with_trigger: the SDK exports it) |
| `_txn._is_retryable_conflict_kind`, `_typed_root_cause`, `_RETRYABLE_CONFLICT_KIND`, `_CASCADE_KIND`, `_UNIQUE_INDEX_MARKER`, `_ENGINE_THROW_PREFIX`, `TxnUniqueViolationError`, `_ERROR_CLASS_UNIQUE_VIOLATION` | (ruled names, a28b/a28c constraints) | — | ruled symbols; `_CASCADE_KIND` REUSES `QueryDetailKind.NOT_EXECUTED` |
| `governed.MigratePreconditionCounts`, `OwnerClassification` | (ruled) | — | ruled; `OwnerClassification` = the ONE Literal both the model and `principals._measured_counts` use (was `str` in the reference — a typecheck error) |
| `principals._OperatorResolution`, `_OPERATOR_RESOLUTION`, `_UnresolvedPurpose`, `_operator_unresolved_sentence`, `_migrate_governed_resolved`, `_measured_counts`, `_message_problem_parts` | read the reference (a28c §A.5b/§A.5d) + `_operator_unresolved` at HEAD | the old `_operator_unresolved` WAS the one sentence home | EXTENDED `_operator_unresolved` — its template became `_operator_unresolved_sentence`, now the ONLY copy (the reference had three) |
| `server` local `_sf_63_1_gate` | lore_search "SF-63-1 gate keep_scope in resolve_visible_keeps …" | the 63 retrofit rulings (no helper) | HAND-ROLLED local closure — two evaluations of ONE gate in one handler |

## §PKG Packages considered (detail)
| mechanism | library | what I READ | verdict |
|---|---|---|---|
| typed per-statement error | `surrealdb` 2.0.0 `errors.parse_query_error`, `ServerError(kind, details)`, `KIND_TO_CLASS` | installed `surrealdb/errors.py` (the parse + v3.0.0 double-wrap workaround, the class map) | replace_with_adapter (one parse per entry) |
| kind constants | `ErrorKind`, `QueryDetailKind` | same file: `ErrorKind.{THROWN,INTERNAL,VALIDATION,…}`, `QueryDetailKind.{NOT_EXECUTED,TIMED_OUT,CANCELLED}`; no conflict constant | replace (bound to the SDK's); `TransactionConflict` bespoke |
| `details.kind` accessor | `surrealdb.errors._detail_kind` | same file (private, underscore) | keep_with_trigger (SDK exports it) |
| per-call record | stdlib `contextvars` | stdlib | replace |
| cosmetic-hunk revert (build hygiene only) | stdlib `ast` + `difflib` | stdlib | bespoke instrument, not shipped |

## §BACKUP (production is NOT committed by me)
- Patch: `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/47c98d77-e9df-4c94-b721-d6a661925589/scratchpad/builder-63c-i-a-a28c.patch`
  — `git diff --binary HEAD` in the build tree, **md5 `956e4136b403d061cf60603c53def3ef`**, applies to
  **`bbf6a0cb85b149788a121b4afe253e46a20d40e3`** (production/tests/registry identical at `a77dc00`). It is byte-identical
  to the tree the declared run and the 20× ran on (same md5 taken before the run).
- Files: `…/scratchpad/builder-63c-i-a-a28c-files/` — `cp -a` of the 8 changed files, repo-relative paths.
- **§HELD part (lead: stage with `git apply --cached`, never `git add`, #486's WIP owns the file in the main tree):**
  the `loremaster/tests/test_surreal_harness.py` hunk in the patch = a28c §A.8 `held_harness.patch`
  (md5 `7343bf28…`, sha256 `53896876f6446413b921fc6c4f0453aaef57708e52c47865c4cb95f206dc49b9`), applied verbatim.
- `scripts/pending_contracts.yaml`: deletion of the `packet-63c-i-a-a28-contract` block ONLY. The main tree carries
  a28c's uncommitted comment edits inside that same block — deleting the block supersedes them; stage my hunk, not the
  file.
- Provenance receipts: build `loremaster.__file__` = `…/scratchpad/b63c/loremaster/loremaster/__init__.py`,
  `lorerunes.__file__` = `…/scratchpad/b63c/lorerunes/lorerunes/__init__.py`; base = `…/scratchpad/base/…` (both via
  `scratch_copy.sh`, which asserts provenance).

## §FLAGS (outside my writable set / for others)
- **58-r4 (am-12 §"ONE named re-base step"):** this build changes two `_txn` facts r4 may rest on — a domain-kind RPC
  error on `_txn_query_raw` is now a `TxnDomainRejectionError`/subclass (no longer `SurrealConnectionError` + drop),
  logged as `store.transaction.rejected` (NOT `store.transaction.rolled_back`); and the ONE ladder is
  `_raise_attempt_failure`. `_txn`'s domain class set is unchanged apart from a28b's `TxnUniqueViolationError`.
- **server.py ack-batch teaching** (am-37 §3's own note): `"ABORTED — store connection lost; retry these"` was false for
  a parse error; after F-11 a parse error no longer reaches that `except SurrealConnectionError` — no edit needed.
- **Store reference §3** stale in two bullets (§SWEEP) — docs edit suggested, not made.
- **lore_search at the default budget** served ONE hit + an elision notice for each DRY query (floor-of-one stub) —
  usable, noted; not filed.
- **A process note on myself:** my first RED@HEAD run ran in the SAME tree I then patched (killed via its scope unit,
  discarded; the baseline was re-taken in a separate `base` copy). No receipt above comes from that run.

## §A Instruments (verbatim where they establish a claim; md5 = the file in my scratchpad)

### `probe_throw_builder.py` — md5 `ca0eb155ea0824346be86c3c0c3b9409`, 120 lines
````python
"""probe_throw_builder.py <label> — builder-63c-i-a-a28c rider 3 + F-11 smoke (TEST store :18000 ONLY; throwaway db).

Part A (raw SDK, no lore code): how the 3.2.x engine wraps a THROW on BOTH driver paths —
  run_query path  = AsyncSurreal.query()  (raises a typed ServerError)
  txn path        = AsyncSurreal.query_raw("BEGIN; …; COMMIT;") (per-statement ERR dict)
for (1) the governed guard exactly as production composes it (governed.py GuardedWrite: IF array::len(..)=0 { THROW
"governed_conflict:<t>:<id>" }), (2) a bare governed THROW, (3) a non-governed THROW. Prints type, kind, details,
repr(message) and, for the txn path, every per-statement entry verbatim.

Part B (the lore module under test, whose __file__ is printed): run_query and execute_transaction on the same
statements with a drop spy — the served class — plus the F-11 recursion-depth statement on BOTH paths.
"""

import asyncio
import json
import sys
import uuid

from surrealdb import AsyncSurreal

from loremaster.store import _txn

URL = "ws://127.0.0.1:18000/rpc"
NAMESPACE = "b63cprobe"


async def _connect(database: str) -> AsyncSurreal:
    connection = AsyncSurreal(URL)
    await connection.connect()
    await connection.signin({"username": "root", "password": "spikeroot"})
    await connection.use(NAMESPACE, database)
    return connection


def _statements() -> dict[str, str]:
    return {
        "governed-guard": (
            "LET $gw_hit = (SELECT * FROM guarded WHERE id = guarded:missing); "
            'IF array::len($gw_hit) = 0 { THROW "governed_conflict:guarded:missing" }'
        ),
        "bare-governed-throw": 'THROW "governed_conflict:guarded:x"',
        "non-governed-throw": 'THROW "some other failure: value can be retried"',
        "recursion-depth": "RETURN " + " OR ".join(["true"] * 5000),
    }


async def part_a(connection: AsyncSurreal) -> None:
    print("=== PART A: raw SDK shapes")
    for name, statement in _statements().items():
        try:
            await connection.query(statement)
            print(f"[A] {name} query(): NO ERROR")
        except Exception as error:  # noqa: BLE001 - a probe prints whatever the SDK raises
            print(
                f"[A] {name} query(): {type(error).__name__} kind={getattr(error, 'kind', None)!r} "
                f"details={json.dumps(getattr(error, 'details', None))} message={str(error)!r}"
            )
        try:
            response = await connection.query_raw(f"BEGIN;\n{statement};\nCOMMIT;", {})
            for index, entry in enumerate(response.get("result") or []):
                print(f"[A] {name} query_raw()[{index}]: {json.dumps(entry)[:400]}")
        except Exception as error:  # noqa: BLE001
            print(
                f"[A] {name} query_raw() RAISED: {type(error).__name__} kind={getattr(error, 'kind', None)!r} "
                f"details={json.dumps(getattr(error, 'details', None))} message={str(error)!r}"
            )


async def part_b(connection: AsyncSurreal) -> None:
    print(f"=== PART B: served class through {_txn.__file__}")
    drops: list[str] = []

    async def acquire() -> AsyncSurreal:
        return connection

    async def drop(_connection: AsyncSurreal) -> None:
        drops.append("drop")

    logger = _txn.logger
    for name, statement in _statements().items():
        for path in ("run_query", "execute_transaction"):
            drops.clear()
            try:
                if path == "run_query":
                    await _txn.run_query(
                        acquire=acquire, drop=drop, url=URL, noun="probe query", label="probe.rejected",
                        statement=statement, logger=logger,
                    )
                else:
                    await _txn.execute_transaction(
                        f"BEGIN;\n{statement};\nCOMMIT;", {}, acquire=acquire, drop=drop, url=URL,
                        deadline_seconds=5.0,
                    )
                print(f"[B] {name} {path}: NO ERROR drops={len(drops)}")
            except Exception as error:  # noqa: BLE001
                print(f"[B] {name} {path}: {type(error).__name__} drops={len(drops)} message={str(error)!r}")


async def main() -> None:
    database = f"b63c_{uuid.uuid4().hex[:8]}"
    bootstrap = AsyncSurreal(URL)
    await bootstrap.connect()
    await bootstrap.signin({"username": "root", "password": "spikeroot"})
    await bootstrap.query(f"DEFINE NAMESPACE IF NOT EXISTS {NAMESPACE}")
    await bootstrap.use(NAMESPACE, database)
    await bootstrap.query(f"DEFINE DATABASE IF NOT EXISTS {database}")
    await bootstrap.use(NAMESPACE, database)
    await bootstrap.query("DEFINE TABLE guarded SCHEMALESS")
    await bootstrap.close()
    connection = await _connect(database)
    print("label:", sys.argv[1] if len(sys.argv) > 1 else "-", "| engine:", await connection.version())
    try:
        await part_a(connection)
        await part_b(connection)
    finally:
        await connection.query(f"REMOVE DATABASE {database}")
        await connection.close()


asyncio.run(main())
````

### `covering_scan.py` — md5 `199fe704e5179d605ae67d5c84653560`, 34 lines
````python
"""covering_scan.py <tree> — builder-63c-i-a-a28c: test files whose AST NAMES a changed production symbol
(Name / Attribute / import alias / string constant equal to the name). Fallback for lore_impact's 15-cap (#518)."""
import ast, sys
from pathlib import Path
CHANGED = {
 # _txn
 "run_query","execute_transaction","execute_read_transaction","_txn_query_raw","_raise_attempt_failure",
 "_classify_engine_error","_rollback_verdict","_failed_statements","_FailedStatement","_domain_root_cause",
 "_is_domain_cascade_notice","is_retryable_conflict_error","_is_retryable_conflict","_is_retryable_conflict_kind",
 "_detail_kind","_typed_root_cause","_domain_rejection_error","TxnDomainRejectionError","TxnGovernedConflictError",
 "TxnUniqueViolationError","_RETRYABLE_CONFLICT_KIND","_CASCADE_KIND","_ERROR_CLASS_UNIQUE_VIOLATION",
 "_UNIQUE_INDEX_MARKER","_ENGINE_THROW_PREFIX","retry_on_conflict","RetryableConflictSignal","_TXN_REJECTION_LABEL",
 # governed / principals
 "MigratePreconditionCounts","MigrateGovernedResult","migrate_governed","resolve_operator_principal",
 "_operator_unresolved","_verb_level_refusal","_message_leg_refusal","_agent_migration_preconditions",
 "_migrate_memory_scope","_migrate_agent_owner","_migrate_message_owner","_dispatch_migrate_governed",
 "_governed_select","AgentMigrationPreconditions","_owned_unscoped_part",
 # keeps / agents / server
 "get_or_create_keyed","minted_by_this_call","preflight","AgentRegistry","_comms_register","resolve_visible_keeps",
}
tree = Path(sys.argv[1]); hits = {}
for f in sorted((tree / "loremaster/tests").glob("test_*.py")) + sorted((tree / "scripts").glob("test_*.py")):
    try: mod = ast.parse(f.read_text())
    except SyntaxError: continue
    names = set()
    for node in ast.walk(mod):
        if isinstance(node, ast.Name): names.add(node.id)
        elif isinstance(node, ast.Attribute): names.add(node.attr)
        elif isinstance(node, ast.alias): names.add(node.name.split(".")[-1])
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in CHANGED: names.add(node.value)
    found = names & CHANGED
    if found: hits[str(f.relative_to(tree))] = sorted(found)
for path, found in hits.items(): print(path)
print(f"# {len(hits)} files", file=sys.stderr)
````

### `revert_cosmetic_hunks.py` — md5 `d4f43a7c780b86df50e6e97d42a54918`, 60 lines
````python
"""revert_cosmetic_hunks.py <tree> <relpath>... — builder-63c-i-a-a28c.

For each file, diff HEAD's bytes against the working-tree bytes and REVERT every hunk that is purely cosmetic:
a hunk is cosmetic iff reverting it alone leaves ``ast.dump`` of the whole module unchanged (a line join/split,
implicit-string-concatenation reflow, parenthesis reflow). Docstring and comment edits are NOT touched: a
docstring is an AST constant (so a reworded one is never cosmetic), and a comment-only hunk is left as-is
(it cannot be told apart from an intended comment change by AST equality, so it is kept and reported).
Prints one line per file: hunks total / reverted / kept.
"""

import ast
import difflib
import subprocess
import sys
from pathlib import Path


def _dump(source: str) -> str:
    return ast.dump(ast.parse(source), include_attributes=False)


def _is_comment_or_blank(lines: list[str]) -> bool:
    return all(line.strip() == "" or line.strip().startswith("#") for line in lines)


def revert(tree: Path, relpath: str) -> None:
    base = subprocess.run(
        ["git", "-C", str(tree), "show", f"HEAD:{relpath}"], check=True, capture_output=True, text=True
    ).stdout.splitlines(keepends=True)
    path = tree / relpath
    new = path.read_text().splitlines(keepends=True)
    target = _dump("".join(new))
    opcodes = [op for op in difflib.SequenceMatcher(a=base, b=new, autojunk=False).get_opcodes() if op[0] != "equal"]
    reverted = 0
    kept = 0
    # bottom-up so earlier indices stay valid
    for tag, base_start, base_end, new_start, new_end in reversed(opcodes):
        removed, added = base[base_start:base_end], new[new_start:new_end]
        if _is_comment_or_blank(removed) and _is_comment_or_blank(added):
            kept += 1
            continue
        candidate = new[:new_start] + removed + new[new_end:]
        try:
            same = _dump("".join(candidate)) == target
        except SyntaxError:
            same = False
        if same:
            new = candidate
            reverted += 1
        else:
            kept += 1
    path.write_text("".join(new))
    assert _dump("".join(new)) == target, relpath
    print(f"{relpath}: hunks={len(opcodes)} reverted={reverted} kept={kept}")


if __name__ == "__main__":
    tree_root = Path(sys.argv[1])
    for rel in sys.argv[2:]:
        revert(tree_root, rel)
````

### `junit_compare.py` — md5 `2bd1aca915ee1449611704f365a11e5e`, 33 lines
````python
"""junit_compare.py <base.xml> <build.xml> — builder-63c-i-a-a28c: per-test outcome diff, both ways.

Outcome per test id (classname::name): passed / failed / error / skipped. Prints counts per tree, then:
RED->GREEN (base red, build passed), GREEN->RED (base passed, build red — the regression set), RED->RED,
ONLY-IN-BASE / ONLY-IN-BUILD (collection differences, e.g. generated parametrisations), per file."""
import sys, collections
import xml.etree.ElementTree as ET
def load(path):
    out = {}
    for case in ET.parse(path).getroot().iter("testcase"):
        tid = f"{case.get('classname')}::{case.get('name')}"
        tags = {child.tag for child in case}
        out[tid] = "failed" if "failure" in tags else "error" if "error" in tags else "skipped" if "skipped" in tags else "passed"
    return out
base, build = load(sys.argv[1]), load(sys.argv[2])
red = {"failed", "error"}
for name, d in (("base", base), ("build", build)):
    print(name, dict(collections.Counter(d.values())), "total", len(d))
common = base.keys() & build.keys()
groups = {
 "RED->GREEN": [t for t in common if base[t] in red and build[t] == "passed"],
 "GREEN->RED": [t for t in common if base[t] == "passed" and build[t] in red],
 "RED->RED": [t for t in common if base[t] in red and build[t] in red],
 "ONLY-IN-BASE": sorted(base.keys() - build.keys()),
 "ONLY-IN-BUILD": sorted(build.keys() - base.keys()),
}
for g, ids in groups.items():
    per_file = collections.Counter(t.split("::")[0].rsplit(".", 1)[0] if "." in t.split("::")[0] else t.split("::")[0] for t in ids)
    print(f"{g}: {len(ids)}")
    for f, n in sorted(per_file.items()): print(f"    {n:5d} {f}")
if len(sys.argv) > 3:
    for g in sys.argv[3:]:
        print(f"--- {g} ids"); [print("  ", t, base.get(t), "->", build.get(t)) for t in sorted(groups[g])]
````

### `red_reasons.py` — md5 `02a4f7d0215ded60c5c2fd35adc90c45`, 20 lines
````python
"""red_reasons.py <base.xml> <build.xml> — builder-63c-i-a-a28c: for tests red in BOTH trees, compare the failure
message's first line (paths and hex ids normalised); print every id whose reason differs."""
import re, sys
import xml.etree.ElementTree as ET
def load(path):
    out = {}
    for case in ET.parse(path).getroot().iter("testcase"):
        for child in case:
            if child.tag in ("failure", "error"):
                msg = (child.get("message") or child.text or "").splitlines()[0] if (child.get("message") or child.text) else ""
                msg = re.sub(r"/var/tmp/\S+?/(base|b63c)/", "<tree>/", msg)
                msg = re.sub(r"0x[0-9a-f]+|[0-9a-f]{8,}", "<hex>", msg)
                msg = re.sub(r"test_\d+_[0-9a-f_]+", "<db>", msg)
                out[f"{case.get('classname')}::{case.get('name')}"] = msg[:300]
    return out
base, build = load(sys.argv[1]), load(sys.argv[2])
both = sorted(base.keys() & build.keys())
diff = [t for t in both if base[t] != build[t]]
print(f"red in both: {len(both)}; reason differs: {len(diff)}")
for t in diff: print("-", t, "\n   base :", base[t][:220], "\n   build:", build[t][:220])
````

Reused verbatim (not mine; md5-checked against their reports): `conc20_a28c.sh` `cc18fd08…` (a28c §A.10f), `kp_probe.py` `a6f497df…` (adversary-a28c §A.4; `kf_only_probe.py` = it with the KG half and the contract import removed), `held_harness.patch` `7343bf28…` (a28c §A.8), the reference chain `a28.patch` `0abdf6d8…`, `a28b.patch` (extracted `9166f58a…`), `myref_a28c_*.py` (a28c §A.5, all four md5-exact). `fk8_consolidate.py` (`066677523c…`) is a one-shot build edit script, not an instrument — its effect is the patch.
