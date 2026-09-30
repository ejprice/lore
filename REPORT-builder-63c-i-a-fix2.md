brief-base v18 read
brief project v7 read

# REPORT — builder-63c-i-a-fix2 (packet 63c-i-a, post-audit fix round over `956e4136`; spec = amendment 37 §5–§7 at `6ade684`)

## SUMMARY BLOCK
- **State: done-with-deviations** — 8 of 9 items FIXED; **F-12(a) NOT FIXED (STOP: the ruled catch reddens `test_exhaustion_fates`; needs one registry row in a test file — §FORKS F-c)**.
- Deviations: D-1 base md5 drift (content-identical; §BASE) · D-2 `unsound_sender_messages` carries `default=None` (a closed a28c pin constructs the result without it) · D-3 F-12(a) reverted (above) · D-4 extra same-class prose fixed next to item 1 (§ITEMS footnote).
- Packages considered: SDK `surrealdb.errors.QueryError.is_not_executed/is_cancelled/is_timed_out` (READ installed `errors.py`, SDK 2.0.0; measured live) → **replace** (the cascade predicate IS the SDK's); `parse_query_error`/`parse_rpc_error` raise set READ from source → caught exactly (`_SDK_PARSE_FAILURES`); no package for a fail-closed GROUP ALL reader → bespoke (§DRY).
- Odoo-20 portability: n/a — no Odoo seam touched.
- Reuse ledger: 3 new symbols, all dispositioned (§DRY) — one ESCALATION: a second GROUP ALL count reader now exists beside `FindingLedger._extract_group_count` with a deliberately DIFFERENT (fail-closed) policy.
- Graded: n/a (builder; no verdict rendered) · HEAD `3969719`.
- Tests (declared set 72 files, md5 `7ac1d9c9…`, same scratch tree, junit per-test): base 5899 passed / 340 failed / 18 skipped; final build **5899 / 340 / 18 — GREEN→RED 0, RED→GREEN 0**; 339 reds registry-owned (58 / 64b-i); **1 red UNOWNED and PRE-EXISTING at base** (`test_retry_seam.py::…::test_am34_5_exactly_one_walker_and_one_resolver_in_the_tree`).
- Gates: `ruff check .` GREEN; typecheck: 0 errors in production files; currency `--legs typecheck,ruff` → ruff GREEN, typecheck **RED_ORPHANED 2 — IDENTICAL on base and build** (pre-existing, `FindingLedger._run_guarded` in two 58/64b test files; §GATES).
- Item 1 live on `:18000`: degenerate → LAST (6), non-degenerate → offender (3), control (base predicate) → false `Cancelled` root (4). §LIVE.
- Decisions needed: (1) F-12(a): land the registry row + the ruled catch (F-c), or rule the passthrough alternative; (2) the two pre-existing unowned reds (walker pin; typecheck orphans) need owners; (3) the GROUP ALL reader duplication (§DRY); (4) F-a: the F-10 sentence goes to stderr with exit 0 — confirm.
- Pointers: patches + backups §BACKUP · per-item §ITEMS · receipts §SET/§GATES/§LIVE · DUAL §DUAL · forks §FORKS.

## Capability check (brief-base §4)
- All demanded capabilities present. `grep`/`rg` hook-blocked (#473) → `awk`/`sed` used throughout (said out loud).
  `lore_impact` covering-test cap (#518) → AST scan (§SET, instrument pasted). lore's index covers the MAIN tree, not my
  scratch copy; used only for the DRY searches (existing code), not for my edits.

## §BASE
Scratch `…/f503eb3c…/scratchpad/fix2` via `scripts/scratch_copy.sh` (provenance asserted by the tool); `git reset --hard
HEAD && git clean -fd` → `git status --short` empty; HEAD `39697197923f74d67ca8068998e9a4580f397e12`; patch file md5
`956e4136b403d061cf60603c53def3ef` ✓; `git apply` clean. **D-1:** `git diff --binary HEAD | md5sum` = `17a6d0e3…`, not
`956e4136`: `diff` of the re-diff against the patch file shows exactly TWO differing lines, both in
`scripts/pending_contracts.yaml` — the `index` line and the hunk header offset (`-264` → `-287`), because HEAD's copy of
that file gained 23 lines above the hunk after the patch was cut. Content identical. `loremaster.__file__` =
`…/scratchpad/fix2/loremaster/loremaster/__init__.py` (inside the scratch).

## §ITEMS — per item (am-37 §5–§7; symbols, not line numbers)
| # | item | state | chokepoint | receipt | STOP-condition check |
|---|---|---|---|---|---|
| 1 | §7 F-C11 / §5 D-5 cascade predicate | FIXED | `_txn._is_domain_cascade_notice` := `isinstance(failed.typed, QueryError) and (typed.is_not_executed or typed.is_cancelled)`; `_CASCADE_KIND` + `QueryDetailKind` import DELETED; no `_CASCADE_KINDS` set, no `_detail_kind` in the decision; the NotExecuted/Cancelled→cascade, TimedOut→substantive adjudication lives ONLY in that docstring | §LIVE (degenerate → LAST, non-degenerate → offender, base-predicate control → the false `Cancelled` root) | a28c exact-set text-reader pin (`test_fixwave_a28c_63c_i_a.py::_text_testers_in` derivation — keys on `Compare(In/NotIn)`, `_SEARCH_METHODS` attr-calls, `re.`): the new body has attribute ACCESS + `or` + a bare-name `isinstance` call → not a tester. Pin GREEN: §SET (named pins) |
| 2 | §6 M-2 `table_defined` | FIXED | `governed.MigrateGovernedResult.table_defined: bool \| None = field(kw_only=True)` (NO default); derived ONCE in `principals._migrate_governed_resolved` as `table in preconditions.defined_tables` (INFO FOR DB has run by then — the read raises otherwise) and handed to EVERY constructor (`_refused`, `_not_supported`, the undefined-table answer, all three legs as a required kw-only `table_defined`); `None` only from `migrate_governed`'s zero-I/O invalid-table branch (`_not_supported(table, table_defined=None)`) | §SET run | a28 `…_a28_…` "`is (table not in removed)`", a28c FK-4 (`None`) and am-34 §4 (`False`) cells — see §SET; a28c's forged construction passes `table_defined=` by keyword (satisfied by the kw-only field) |
| 3 | §6 F-9 mixed-owner sentence | FIXED | `principals._owned_unscoped_part` mixed branch: ONE integer `distinct_owner_principals`, rendered as the TOTAL ("… — and by others: N distinct principal(s) in all, the operator among them (a sample of the others: …)"); the second integer (`first K named`) is gone; `owned by the operator` substring kept; `foreign` unchanged | §SET run | `_OWNER_SENTENCE_STATES["mixed"]`, stems, `[mixed-owners]` substring pin — §SET |
| 4 | §6 F-10 unsound-sender messages | FIXED (with deviation D-2) | new measured field `MigrateGovernedResult.unsound_sender_messages: int \| None` (kw-only; `default=None` — D-2; every production construction passes it explicitly); `_migrate_message_owner` runs ONE read after its UPDATE (`SELECT count() FROM message WHERE scope IS NONE AND owner_principal IS NONE GROUP ALL`, via `_group_all_count`); `0` on the no-legacy-rows path is DERIVED from the measured `scope IS NONE` count 0 (a superset); `None` on every refusal / other leg / undefined answer; CLI render `_dispatch_migrate_governed` DERIVES the ruled sentence iff `> 0` (stderr, exit stays 0 — see §FORKS F-a); leg docstring's stale predicate rewritten to the full 4-clause WHERE | §SET run | **STOP condition "a pin counting the message leg's store reads on its success path"** — none found by awk before the build; the §SET run is the check (a count pin would go GREEN→RED): see §SET |
| 5a | §6 F-12(a) dispatch catch | **NOT FIXED — STOP (a fix that reddens a pin)** | built as ruled, then REVERTED to the base tuple: the base-class catch makes `principals.py::_dispatch_migrate_governed` a new catch site whose caught closure contains `TxnContentionExhaustedError`, so `test_exhaustion_fates.py::TestTheRegistryIsTheAdjudicationBothWays::test_every_non_derived_site_has_a_row_and_every_row_a_site` went GREEN→RED (`SILENT-FATE sites with no (or a mis-counted) row … {'principals.py::_dispatch_migrate_governed': 1}`). The remedy is a `REGISTERED_FATES` row in `loremaster/tests/_exhaustion_fates.py` — a test file, outside my writable set. Exact edits in §FORKS F-c | build-1 run (§SET) | the fates pin — GREEN only with the revert |
| 5b | §6 F-12(b) `_scope_count` fail-closed | FIXED (coupled to 5a: until 5a lands, a wrong-shaped count raises a bare `SurrealStoreError` out of the CLI as a traceback — loud, never a silent 0; the same fate `_governed_select`'s raise already has at base) | new `principals._group_all_count(result, *, noun)` — THE one `GROUP ALL` count reader: `[]` → 0; `[{"count": int}]` → int; anything else raises `SurrealStoreError` (the `_governed_select` policy). `_scope_count` and F-10's leftover read both route through it; `_governed_select`'s stale "reads as no rows" docstring corrected | §SET run | **STOP condition "a pin feeding `_scope_count` a wrong shape and expecting `0`"** — §SET run |
| 6 | §6 F-8 stale `last_conflict` | FIXED | `_txn._run_verified_transaction._attempt` resets `last_conflict = None` at ENTRY; comment above the stash says why | §SET run (58 tiers / exhaustion pins in set) | **STOP condition "a pin asserting exhaustion logs an EARLIER attempt's conflict"** — §SET run. The label/url rider is 58's — NOT done |
| 7 | §7 F-C8 (+F-14) parse failures | FIXED | new `_txn._parse_failed_statement(index, statement_result)` — THE one parse; kindless → `None` (F-14 residual unchanged); an SDK parse failure → `None` + WARNING `store.transaction.untypeable_err_entry` naming `statement_index` and the parse error. Caught classes = `_txn._SDK_PARSE_FAILURES = (AttributeError, TypeError, RecursionError)`, READ from the installed `surrealdb/errors.py` (SDK 2.0.0): `parse_rpc_error` calls `raw.get` on a non-dict `cause` (AttributeError); an unhashable `kind`/`code` keys `KIND_TO_CLASS`/`CODE_TO_KIND` (TypeError); `parse_rpc_error` recurses once per `cause` level (RecursionError) | smoke: a non-dict `cause` and an unhashable `kind` each → `typed=None` + one WARNING; a well-formed `NotExecuted` entry → `QueryError` | a28c pins constructing `_FailedStatement(typed=None)` — unchanged fate |
| 8 | prose F-4 / F-5 / F-C7 / F-C9 | FIXED | F-4 `execute_transaction` docstring (typed cascade + typed conflict); F-5 `TxnContentionExhaustedError` docstring + the comment above `_ASSERT_VIOLATION_MARKER` (text = LABEL only, on the untyped leg); F-C7 `KeepStore.get_or_create_keyed` `Raises:` (the narrowed `TxnUniqueViolationError` door + the two pass-throughs) and its stale in-body comment; F-C9 the `last_conflict_cause` comment in `retry_on_conflict` — every signal raise site DERIVED by awk (all chain `from error` except `_run_verified_transaction._attempt`, which also passes no `label=`, so its exhaustion record carries NO `engine_error` key at all — the old comment claimed "the empty string") | awk raise-site list in §DUAL | no `__doc__` pin on these (am-37 §6/§7 pin checks) |
| 9 | §6 M-1 store reference | FIXED | `docs/reference/surrealdb-31-capabilities.md`: §3 "Classify SEMANTICALLY" (the marker-seeking sentence → a dated SUPERSEDED block, kind-seeking via `_txn._is_domain_cascade_notice`); §3 "Client-side conflict retry" (typed signal, `_txn._RETRYABLE_CONFLICT_KIND`, text = evidence, 3.1.5 claim marked superseded); its #111 sub-bullet ("#111 ANSWERED — trigger MET (2026-09-27)" + one-level-below + SDK ships no conflict constant); §6.6 item 3 (corrected claim + the untyped set as a fact); the closing summary line. Also retired the stale `_txn.py:416` / `:714` line citations in the edited §3 passage (symbols, not lines) | `git diff` of that file in the delta patch | no instrument reads `docs/reference` |

Extra prose touched in the same class (disclosed, not in the brief's list — each was stale against the item-1 change it
sits next to): the `_RETRYABLE_CONFLICT_KIND` comment block ("Both … both DECIDE" after the second constant was
deleted); `_rollback_verdict` docstring "(marker-seeking)" → "(kind-seeking)"; `_domain_root_cause` docstring (cited the
deleted `_CASCADE_KIND`, and called the COMMIT notice "marker-less"); `_FailedStatement.typed` docstring (now names the
untypeable case).

## §SET — the declared set (written 00:19Z 2026-09-30, BEFORE any run)
- Base builder's 67-file set (`…/47c98d77…/scratchpad/declared_set.txt`, md5 `b16b77b4…` ✓ verified) ∪ the AST covering
  scan of every symbol I changed (51 files; 5 new beyond the 67): `test_comms_await.py`, `test_comms_promise_registry.py`,
  `test_comms_send_scope_63b_ii_a.py`, `test_reanchor_58_r4_lease_fates.py`, `test_reanchor_58_r4_state.py`. Result:
  **72 files, md5 `7ac1d9c9eaf9351f3c42999637bf117a`** (`…/f503eb3c…/scratchpad/declared_fix2.txt`). STOP-condition-named
  pins (F-8 / F-10 / F-12) name no pin that exists (am-37's awk; mine agreed) — their files (58 tiers, exhaustion fates,
  a28/a28b/a28c, governed migration) are all in the set, so a hidden one would surface as GREEN→RED.
- Bound: a test reaching a changed symbol only transitively (through a store verb, without naming it) is not in the set;
  the packet's full suite (coldaudit) covers that.
- Every run: `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --no-sync --with pytest-timeout pytest
  -n 8 --timeout=300 -q -p no:cacheprovider --junitxml=…` (fresh `PYTHONPYCACHEPREFIX` per tree swap); MemAvailable
  28–32 GiB at each launch; no cap kill, no timeout. ONE tree, swapped by `cp -p` from content backups (base re-diff md5
  re-verified `17a6d0e3…` before the base run).

| run (2026-09-30Z) | tree | passed | failed | skipped | collected | wall |
|---|---|---|---|---|---|---|
| build-1 00:20 | first build | 5896 | 343 | 18 | 6257 | 10m46s |
| base 00:31 | `956e4136` content | 5899 | 340 | 18 | 6257 | 10m49s |
| **build-2 00:42** | **final build** | **5899** | **340** | 18 | 6257 | 10m34s |

- build-1 vs base: **GREEN→RED 3** — all mine, all traced: `test_exhaustion_fates…::test_every_non_derived_site_has_a_row_and_every_row_a_site`
  (F-12(a) → STOP, reverted) and `test_fixwave_a28c_63c_i_a.py::TestAnUndefinedTargetTableIsATypedAnswer63cIAa28c::test_am34_4_the_cli_render_derives_the_sentence_from_the_typed_field[False|True]`
  (`TypeError: MigrateGovernedResult.__init__() missing 1 required keyword-only argument: 'unsound_sender_messages'` → D-2).
- **build-2 vs base: transitions `{passed→passed 5899, failed→failed 340, skipped→skipped 18}` — GREEN→RED 0, RED→GREEN 0,
  collection identical.** (RED→GREEN 0 is expected: this round adds no pin.)
- Remaining 340 reds by owner (file-level map from `scripts/pending_contracts.yaml`; r3_cas_seam / r4_state sit under
  BOTH entries): `packet-64b-i-contract` — comms_footer 81, governed_substrate_64b 34, findings_{classes 27, governance 24,
  migrate 28, schema 17, scope_domain 24, system_writer 9}_64b, mcp_server 28, reanchor_58_r3_cas_seam 4, reanchor_58_r4_state 3;
  `packet-58-contract` — reanchor_58_r2_rulings 27, r3_tiers 16, r3_am6 8, r4_lease_fates 4, exhaustion_fates 1 (the lease
  rows' `logs-error-class`, named in the 58 entry), forgery_door_sweep 3, blocks_edge 1;
  **UNOWNED 1, RED at base too:** `test_retry_seam.py::TestThereIsExactlyOneCatchScanner63cIAa28c::test_am34_5_exactly_one_walker_and_one_resolver_in_the_tree`
  — `catch-handler walkers [] — exactly ONE may exist (loremaster/tests/_catch_sites.py::catch_sites_in)`. Not caused by
  this round (identical at base). `_catch_sites.py` was last changed by 58's contract r4 `4d864c9`, after a28c `7017b54`
  wrote the pin (MEDIUM confidence that `4d864c9` is the cause — not bisected). The base builder's run (at `bbf6a0c`) had it
  green. **Needs an owner — flagged, not touched.**
- Named pins GREEN in build-2 (junit, verbatim ids): `TestTheEngineTextReadersAreExactlyTheClassifier63cIAa28c::test_am36_1_2_3_the_only_engine_text_reader_is_the_classifier`
  (the exact-set tester pin item 1 had to survive) · `…::test_am36_1_2_3_the_derivation_SEES_a_text_reader` ·
  `TestTheEngineFactsTheClassifierRestsOn63cIAa28c::test_am36_1_1_KNOWN_BOUND_every_cascade_notice_is_typed_NotExecuted` ·
  `TestAnUndefinedTargetTableIsATypedAnswer63cIAa28c::test_am34_4_an_undefined_target_answers_table_defined_False_after_ONE_probe[*]` (6) ·
  `…::test_am36_FK4_table_defined_is_None_when_INFO_FOR_DB_never_ran[*]` (29) · `…::test_am34_4_the_cli_render_derives_the_sentence_from_the_typed_field[False|True]` ·
  `…::test_am34_4_the_preconditions_carry_the_defined_table_set` · `TestEmptyContributesNoOwnerSentence63cIAa28c::test_am34_2_every_classified_population_carries_an_owner_stem[P_mixed]` ·
  `TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent[mixed-owners]` ·
  `TestKATheOneClassifierDecidesTheTextShape::test_KA_mutating_the_one_classifier_moves_both_raise_sites[run_query|execute_transaction]`.
  Of 245 pins matched by a name filter over the a28/a28b/a28c/fates/retry_seam/txn/58-tiers/migration files, 244 PASSED;
  the 1 FAILED is the pre-existing walker pin above.

## §GATES
- `uv run ruff check .` (build) → `All checks passed!`
- `./scripts/typecheck.sh` (build) → loremaster 82 errors / scripts 1, **every one in a 58/64b test file naming an unbuilt
  symbol; zero in any production file** (awk over the log: no `error:` line outside `tests/` except
  `scripts/test_forgery_door_sweep.py:42 … SupersedeResult`, 58's).
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff`:
  - build: `ruff GREEN` · `typecheck RED_ORPHANED — 2 residual(s) with NO owner` ·
    `ORPHAN: loremaster/tests/test_reanchor_58_r3_cas_seam.py:93: "type[FindingLedger]" has no attribute "_run_guarded"` ·
    `ORPHAN: loremaster/tests/test_reanchor_58_r4_state.py:77: …same…` · pytest NOT_RUN (expected: legs-only, per brief).
  - **base (same tree, swapped back, re-diff md5 `17a6d0e3` verified): the IDENTICAL two orphans.** Pre-existing, not this
    round. The registry DOES list `type[FindingLedger]._run_guarded` for both files under `packet-64b-i-contract`, and the
    same two files ALSO appear under `packet-58-contract`; I did not debug the gate's matching (GUESS: a file registered
    under two entries is matched against only one). **The brief's "0 RED_ORPHANED" is NOT met, for a reason outside this
    round — decision needed.**

## §LIVE — item 1 on `:18000` (TEST store; throwaway DB `test_<pid>_<uuid>` in `lore_test`, `REMOVE DATABASE`d after)
Live statement: `BEGIN; CREATE probe:a; CREATE probe:b; THROW 'offender'; CREATE probe:c; CREATE probe:d; COMMIT;`
```
loremaster.__file__ = /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/f503eb3c-926a-40f5-927c-1ce3af738c5f/scratchpad/fix2/loremaster/loremaster/__init__.py
  NotExecuted  -> QueryError is_not_executed=True is_cancelled=False is_timed_out=False cascade=True
  Cancelled    -> QueryError is_not_executed=False is_cancelled=True is_timed_out=False cascade=True
  TimedOut     -> QueryError is_not_executed=False is_cancelled=False is_timed_out=True cascade=False
LIVE failed statements (index, typed kind, details.kind):
  [1] QueryError kind=Query details.kind=NotExecuted cascade=True
  [2] QueryError kind=Query details.kind=NotExecuted cascade=True
  [3] ThrownError kind=Thrown details.kind=None cascade=False
  [4] QueryError kind=Query details.kind=Cancelled cascade=True
  [5] QueryError kind=Query details.kind=Cancelled cascade=True
  [6] QueryError kind=Query details.kind=NotExecuted cascade=True
NON-DEGENERATE: build selects index 3 (ThrownError); base-predicate CONTROL selects index 3
DEGENERATE (live cascade entries ['NotExecuted', 'NotExecuted', 'Cancelled', 'Cancelled', 'NotExecuted'], indices [1, 2, 4, 5, 6]): build selects index 6 (LAST=6); base-predicate CONTROL selects index 4 (Cancelled)
END-TO-END: TxnDomainRejectionError: SurrealDB transaction failed and was rolled back: statement 4 of 7 was rejected (unspecified rejection); see the server log for the full engine detail
```
- **Non-degenerate (measured shape) → the offender** (index 3, the `ThrownError`), both builds.
- **Degenerate all-cascade list** (the five LIVE cascade entries, offender removed) → **the LAST entry (index 6)**; the
  **control** — the base build's predicate (`details.kind == NotExecuted` only) over the same list — selects index 4, a
  `Cancelled` entry: the false root cause am-37 §5 describes. The probe demonstrably discriminates the two builds.
- End to end through `execute_transaction` on the live connection: `TxnDomainRejectionError … statement 4 of 7` (the
  offender's position), and the `drop` spy (which raises if called) was never called.

## §DUAL — removed / replaced behavior, adjudicated
| removed / replaced | adjudication |
|---|---|
| `_txn._CASCADE_KIND` + `QueryDetailKind` import | dropped-deliberately (am-37 §7: the SDK's predicates decide; a constant no decision reads would claim sharing that does not exist). Consumers: awk over the workspace — none besides `_is_domain_cascade_notice` and prose |
| cascade = `NotExecuted` only | dropped-deliberately (§5 D-5: `Cancelled` is cascade; §LIVE control shows the old fate) |
| `_scope_count`: non-list / non-dict / missing or non-int `count` → `0` | dropped-deliberately (F-12(b) fail-closed). `[]` → 0 preserved-with-pin (the empty-set GROUP ALL, e.g. `test_a_none_scope_count_is_reported_over_a_dirty_memory_table` green). A `{"count": None}` or `True` now raises — no measured engine shape emits either |
| `_not_supported(table, *, store_was_read: bool)` | replaced by `table_defined: bool \| None` — preserved: `None` ⇔ the zero-I/O prose, a bool ⇔ the `brief` prose (FK-4 cells green); the two coupled params could previously disagree, now cannot |
| `table_defined` default `True` | dropped-deliberately (M-2); every constructor passes the derived value |
| `_failed_statements` inline `parse_query_error(...) if kind else None` | preserved for well-formed and kindless entries; parse failures now `None` + WARNING (F-C8) instead of `AttributeError` escaping |
| mixed-owner sentence: `other principal(s): N distinct owner(s) (first K named: …)` | dropped-deliberately (F-9 / am-34 §2): the "other" label on the total, and the second integer K |
| `last_conflict` carried across attempts | dropped-deliberately (F-8) |
| `_dispatch_migrate_governed` catch tuple | UNCHANGED (F-12(a) reverted — §FORKS F-c) |

F-C9 raise-site derivation (awk over the workspace, 2026-09-30): `RetryableConflictSignal()` is raised at
`store/_txn.py` (`bootstrap_session` ×3 closures, `_raise_attempt_failure`, `_run_verified_transaction._attempt`),
`scout.py` ×3, `inbox_awaiter.py` ×3 — every one `from error` inside/under an `except`, except
`_run_verified_transaction._attempt` (bare).

## §DRY — new reusable symbols
| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `principals._group_all_count` | `lore_search("read a SELECT count() GROUP ALL result into an int count helper")` + `("extract count from GROUP ALL result rows default 0")` | `findings.py::FindingLedger._extract_group_count` — TOLERANT (`int(rows[0].get(_COUNT_KEY, 0))`), a private classmethod | **HAND-ROLLED + ESCALATED**: the ruling demands the OPPOSITE policy (fail-closed) for the migration, so reusing it would adopt the forbidden tolerance and widening it in place would change findings' behavior (outside this round). Two GROUP ALL readers with deliberately different policies now exist; recommend ONE reader with an explicit strict/tolerant choice (home: `loremaster.store` or `lorerunes` — the lead's call). `_scope_count` and the F-10 read share it (one policy inside principals) |
| `_txn._parse_failed_statement` | `lore_search("safely parse a per-statement ERR entry with parse_query_error catching malformed dict")` | only report prose (coldaudit-3 F-C8) | HAND-ROLLED — it IS the ruled ONE chokepoint (F-C8); the SDK parser is reused inside it |
| `_txn._SDK_PARSE_FAILURES` | same | same | HAND-ROLLED — the exception set read from the installed SDK source (no SDK constant exports it) |

## §FORKS (both readings written; the pick stated)
- **F-a (F-10 render channel).** The ruling fixes the sentence, not the channel/exit. Picked: **stderr, exit 0** — the run
  succeeded for every sound row; the sentence is a diagnostic, and stdout stays the receipt line. Alternative: stdout, or
  exit 1 (treat skipped rows as a failure). Lead's call.
- **F-b (M-2 mechanics).** Reading A (picked): derive once in `_migrate_governed_resolved`, thread the value into every
  constructor (legs gain a required kw-only `table_defined`). Reading B: construct with a placeholder and overwrite at the
  final `dataclasses.replace` — rejected: a placeholder IS a default. ⚠ Consequence for 64b: `test_findings_migrate_64b.py`
  calls a future `_migrate_finding_scope(store, keep_store, principal_store)`; any 64b leg constructing
  `MigrateGovernedResult` must now pass `table_defined=` (and should pass `unsound_sender_messages=None`).
- **F-c (F-12(a) STOP — the exact edits, for the lead to route).** Two edits land together:
  1. `principals._dispatch_migrate_governed`: the `except` tuple becomes `(PrincipalStoreError, KeepStoreError,
     SurrealStoreError, ValueError)` (the ruled base class; `SurrealConnectionError` is subsumed).
  2. `loremaster/tests/_exhaustion_fates.py` `REGISTERED_FATES` gains the row its sibling already has:
     ```
     "principals.py::_dispatch_migrate_governed": (
         Fate(
             "cli-exit",
             "principals",
             ("stderr", "returns-named-outcome"),
             catches="(PrincipalStoreError, KeepStoreError, SurrealStoreError, ValueError)",
         ),
     ),
     ```
     (mirrors `principals.py::_dispatch_report_unmigrated`'s row). Edit 1 without edit 2 is the measured GREEN→RED.
  Alternative that needs no test edit: keep the base catch AND add `except TxnContentionExhaustedError: raise` above it
  (a derived PASSTHROUGH) — exhausted contention would then keep its base fate (a traceback), contradicting F-12(a)'s
  "every store fault → stderr + exit 1". I recommend the row (edits 1+2).
- **D-2 (F-10 field default).** CLAUDE.md says never default a value the code branches on; the closed a28c pin
  constructs the result without the field, so it carries `default=None` (= "not measured", honest). Every production
  construction passes it explicitly. Re-open: the next contract touching the result model may drop the default.

## §BACKUP (HEAD `39697197923f74d67ca8068998e9a4580f397e12`)
All under `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/f503eb3c-926a-40f5-927c-1ce3af738c5f/scratchpad/`:
- `builder-63c-i-a-fix2.patch` — FULL patch vs HEAD (base + delta), md5 **`01fd04715160fab72f80b06d2126421d`**
  (`git apply --check -R` passes on the scratch tree).
- `builder-63c-i-a-fix2-delta.patch` — delta ONLY over the base, md5 **`54e6b613c6e4fe8cd7c370d6f13fd1da`**; touches
  exactly `docs/reference/surrealdb-31-capabilities.md`, `governed.py`, `keeps.py`, `principals.py`, `store/_txn.py`
  (no test file); `git apply --check` passes on a copy of the base files.
- `builder-63c-i-a-fix2-files/` — `cp -a` of all 9 files the full patch touches (build content); `base-files/` — the base.
- Receipts: `runs/{base,build,build2}.{log,xml}`, `runs/compare{1,2}.txt`, `runs/currency{,-base}.log`,
  `runs/probe_item1.log`, `runs/typecheck-build.log`; set `declared_fix2.txt`; covering map `covering_fix2.tsv`.
- Nothing committed to production code (per brief); only this report is committed.

## §INSTRUMENTS (pasted verbatim, per brief-base §1)

`covering_scan_fix2.py`:
```python
"""Covering-test AST scan (builder-63c-i-a-fix2): every test file whose AST NAMES a changed symbol
(Name id / Attribute attr / import alias) or carries a string constant naming one (or the CLI verb)."""
import ast, pathlib, sys
root = pathlib.Path(sys.argv[1])
SYMBOLS = {
    # _txn
    "_is_domain_cascade_notice", "_CASCADE_KIND", "_domain_root_cause", "_rollback_verdict", "_failed_statements",
    "_parse_failed_statement", "_SDK_PARSE_FAILURES", "_FailedStatement", "_run_verified_transaction",
    "execute_transaction", "execute_read_transaction", "TxnContentionExhaustedError", "retry_on_conflict",
    "_ASSERT_VIOLATION_MARKER", "_RETRYABLE_CONFLICT_KIND",
    # governed / principals
    "MigrateGovernedResult", "migrate_governed", "_migrate_governed_resolved", "_refused", "_not_supported",
    "_migrate_memory_scope", "_migrate_agent_owner", "_migrate_message_owner", "_scope_count", "_group_all_count",
    "_governed_select", "_owned_unscoped_part", "_dispatch_migrate_governed", "_agent_migration_preconditions",
    "table_defined", "unsound_sender_messages",
    # keeps
    "get_or_create_keyed",
}
STRINGS = {"migrate-governed"}
hits = {}
files = sorted(list((root / "loremaster/tests").glob("test_*.py")) + list((root / "scripts").glob("test_*.py")))
for path in files:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name): names.add(node.id)
        elif isinstance(node, ast.Attribute): names.add(node.attr)
        elif isinstance(node, ast.alias): names.add(node.name.rsplit(".", 1)[-1])
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in SYMBOLS or any(s in node.value for s in STRINGS): names.add(node.value if node.value in SYMBOLS else "<migrate-governed>")
    matched = (names & SYMBOLS) | ({"<migrate-governed>"} & names)
    if matched:
        hits[str(path.relative_to(root))] = sorted(matched)
for f, m in hits.items():
    print(f"{f}\t{','.join(m)}")
```

`junit_compare_fix2.py`:
```python
"""Per-test outcome diff of two junit XMLs + registry ownership of every remaining red (builder-63c-i-a-fix2).
usage: junit_compare_fix2.py BASE.xml BUILD.xml pending_contracts.yaml"""
import sys, collections, xml.etree.ElementTree as ET, yaml

def outcomes(path):
    result = {}
    for case in ET.parse(path).getroot().iter("testcase"):
        key = f"{case.get('classname')}::{case.get('name')}"
        tags = {child.tag for child in case}
        outcome = "failed" if tags & {"failure", "error"} else "skipped" if "skipped" in tags else "passed"
        if key in result and result[key] != outcome and outcome == "failed":
            result[key] = outcome  # an error in teardown after a pass counts as failed
        result.setdefault(key, outcome)
    return result

def file_of(key):
    classname = key.split("::", 1)[0]
    parts = classname.split(".")
    for i in range(len(parts), 0, -1):
        candidate = "/".join(parts[:i]) + ".py"
        if parts[i - 1].startswith("test_"):
            return candidate
    return classname

base, build = outcomes(sys.argv[1]), outcomes(sys.argv[2])
registry = yaml.safe_load(open(sys.argv[3]))
owner_of = {}
for entry in registry.get("bounds") or registry.get("entries") or []:
    for f in entry.get("files", []):
        owner_of[f["path"].rsplit("/", 1)[-1]] = entry["id"]
for label, data in (("base", base), ("build", build)):
    c = collections.Counter(data.values())
    print(f"{label}: collected={len(data)} passed={c['passed']} failed={c['failed']} skipped={c['skipped']}")
common = base.keys() & build.keys()
trans = collections.Counter((base[k], build[k]) for k in common)
print("transitions (base->build) over common ids:", dict(trans))
g2r = sorted(k for k in common if base[k] == "passed" and build[k] == "failed")
r2g = sorted(k for k in common if base[k] == "failed" and build[k] == "passed")
print(f"GREEN->RED: {len(g2r)}"); [print("   ", k) for k in g2r]
print(f"RED->GREEN: {len(r2g)}"); [print("   ", k) for k in r2g]
only_base, only_build = sorted(base.keys() - build.keys()), sorted(build.keys() - base.keys())
print(f"ONLY-IN-BASE: {len(only_base)}"); [print("   ", k, base[k]) for k in only_base]
print(f"ONLY-IN-BUILD: {len(only_build)}"); [print("   ", k, build[k]) for k in only_build]
reds = [k for k, v in build.items() if v == "failed"]
by_file = collections.Counter(file_of(k).rsplit("/", 1)[-1] for k in reds)
print(f"BUILD REDS by file -> owner ({len(reds)}):")
unowned = 0
for f, n in sorted(by_file.items()):
    owner = owner_of.get(f, "UNOWNED")
    unowned += n if owner == "UNOWNED" else 0
    print(f"    {f} {n} -> {owner}")
print(f"UNOWNED reds: {unowned}")
```

`probe_item1_fix2.py`:
```python
"""Item-1 live receipt (builder-63c-i-a-fix2, am-37 §7 F-C11): the cascade predicate is the SDK's own
QueryError.is_not_executed / is_cancelled. Live :18000 TEST store only; throwaway DB, reaped."""
import asyncio, sys, pathlib
sys.path.insert(0, str(pathlib.Path("loremaster/tests").resolve()))
import _surreal_harness as H
from surrealdb import AsyncSurreal
from surrealdb.errors import QueryError, parse_query_error
import loremaster
from loremaster.store import _txn

assert H.DEFAULT_URL.endswith(":18000/rpc") and "18500" not in H.DEFAULT_URL
print("loremaster.__file__ =", loremaster.__file__)

# (0) the one-liner receipt: the SDK's predicates for the three QueryDetailKind members
for kind in ("NotExecuted", "Cancelled", "TimedOut"):
    typed = parse_query_error({"kind": "Query", "details": {"kind": kind}, "result": "x", "status": "ERR"})
    print(f"  {kind:12s} -> {type(typed).__name__} is_not_executed={typed.is_not_executed} "
          f"is_cancelled={typed.is_cancelled} is_timed_out={typed.is_timed_out} "
          f"cascade={_txn._is_domain_cascade_notice(_txn._FailedStatement(0, 'x', typed))}")

def base_predicate(failed):  # the am-36/base build's predicate: NotExecuted only (the CONTROL)
    return _txn._detail_kind(failed.typed) == "NotExecuted"

def select(failed_statements, predicate):
    for failed in failed_statements:
        if not predicate(failed):
            return failed
    return failed_statements[-1]

async def main():
    database = H.unique_database()
    connection = AsyncSurreal(H.DEFAULT_URL)
    await connection.connect()
    await connection.signin({"username": H.DEFAULT_USER, "password": H.DEFAULT_PASS})
    await connection.use(H.TEST_NAMESPACE, database)
    try:
        statement = ("BEGIN; CREATE probe:a SET v = 1; CREATE probe:b SET v = 2; "
                     "THROW 'offender'; CREATE probe:c SET v = 3; CREATE probe:d SET v = 4; COMMIT;")
        response = await connection.query_raw(statement, {})
        failed = _txn._failed_statements(response)
        print("LIVE failed statements (index, typed kind, details.kind):")
        for f in failed:
            print(f"  [{f.index}] {type(f.typed).__name__} kind={getattr(f.typed,'kind',None)} "
                  f"details.kind={_txn._detail_kind(f.typed)} cascade={_txn._is_domain_cascade_notice(f)}")
        # (1) the measured NON-degenerate shape -> the offender
        root = _txn._domain_root_cause(failed)
        print(f"NON-DEGENERATE: build selects index {root.index} ({type(root.typed).__name__}); "
              f"base-predicate CONTROL selects index {select(failed, base_predicate).index}")
        # (2) the DEGENERATE all-cascade list, built from the LIVE cascade entries (offender removed)
        degenerate = [f for f in failed if _txn._is_domain_cascade_notice(f)]
        kinds = [_txn._detail_kind(f.typed) for f in degenerate]
        root = _txn._domain_root_cause(degenerate)
        control = select(degenerate, base_predicate)
        print(f"DEGENERATE (live cascade entries {kinds}, indices {[f.index for f in degenerate]}): "
              f"build selects index {root.index} (LAST={degenerate[-1].index}); "
              f"base-predicate CONTROL selects index {control.index} ({_txn._detail_kind(control.typed)})")
        # (3) end to end through execute_transaction: the served message names the offender's position
        async def acquire():
            return connection
        async def drop(_c):
            raise AssertionError("a domain rejection must never drop the connection")
        try:
            await _txn.execute_transaction(statement, {}, acquire=acquire, drop=drop, url=H.DEFAULT_URL)
        except _txn.TxnDomainRejectionError as error:
            print(f"END-TO-END: {type(error).__name__}: {error}")
    finally:
        await connection.query(f"REMOVE DATABASE {database}")
        await connection.close()

asyncio.run(main())
```

## Flags for the Operator (unrelated to this round's scope — surfaced, not handled)
- The unowned walker pin (§SET) and the two typecheck orphans (§GATES) are RED at base; both sit in 58/64b territory.
- There are 340 failing tests in the declared set, 339 registry-owned by 58 / 64b-i and 1 unowned (above).
