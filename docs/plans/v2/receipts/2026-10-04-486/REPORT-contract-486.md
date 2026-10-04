brief-base v17 read · brief project v7 read

# REPORT — contract-486 (tdd-light Phase 1 CONTRACT: #486 harness `run()` retry + the test-DB leak)

## SUMMARY BLOCK
- **State:** done-with-deviations
- **Deviation 1:** my first census CREATED a TEST-store DB (a bare `use()` materialises one, M1); it was removed within the minute and no residue remains.
- **Deviation 2:** 6 new tests are GREEN at HEAD BY DESIGN (preservation pins + controls; §RED), where the brief's text said "each new test RED".
- **Packages considered:** retry → `_txn` seam via `_run_under_store_retry_seam` (REUSED; `retry_on_conflict` source read) · session-end reap → pytest `sessionfinish` + xdist 3.8.0 `workeroutput`/`testnodedown` (`replace_with_adapter`; hookspec read, `-n 2` leg green on the reference) · inner session → `pytester.runpytest_subprocess` read, not a default plugin → `keep_with_trigger` (trigger: root conftest enables pytester)
- **Odoo-20 portability:** n/a — no Odoo seam touched
- **Reuse ledger:** 9 new test-side symbols, all dispositioned (§DRY ledger); `_sdk_engine_doors` REUSES `StoreTraffic`'s derivation (measured equal)
- **Graded:** n/a (author) · authored at `e039c64`, HEAD-at-report `86a55eb` (9 docs-only commits; none touch a file this contract rests on)
- **Decisions needed:** D1 no raw door (0/812 sites need it) · D2 killed-session orphans (454 dead-pid DBs; cross-pid-namespace hazard) → sidecar · D3 lint `scripts/` probe clones? · D4 one-shot cleanup of 2186+454 current leaks (destructive, shared store)
- **Receipts:** §RED 15 failed / 80 passed at HEAD · §SAT 259 passed / 0 failed rc 0 (scratch copy, provenance printed) · §Raw-door · §Stub expectations · §HELD (test_mcp_server `_slug`, 1 line) · §Instruments I-1…I-10

## Capability check (brief-base §4)
- grep/rg are hook-blocked (#473), so textual scans used `awk` and Python-AST, and each fallback is named where it is used.
  This is sanctioned grep-case (b) (non-symbol textual seams: statement text, name recipes).
- The lore tools were loaded and used (`lore_get_symbol`, `lore_search`, `lore_index`, `lore_comms`). ⚠ The lore watched root
  reported `git_ref 299abb2` while my session started at HEAD `e039c64`. 299abb2 turned out to be
  AHEAD (the index was current; the fleet was committing). Every structural read was taken from disk.
- No capability demanded by the brief was missing.

## Measurements (2026-09-26, HEAD `e039c64`, TEST store `ws://127.0.0.1:18000` — never :18500)
- **M1 — `use()` ALONE creates a database** (engine `surrealdb-3.2.4+20260803.93ab219`).
  - Leg A: `use(lore_test, <fresh>)` → the name appears in `INFO FOR NS`.
  - Negative control: a never-used name reads as absent. Positive control: `DEFINE DATABASE` → present.
  - Every probe DB was removed (§Instruments I-5/I-6).
  - ⚠ This was discovered by ACCIDENT: my first census (`use()` + `INFO FOR NS`) created
    `census_readonly_nonexistent`, which I then removed. **A census of the namespace is not free.** Any reader
    must `use()` a name it then removes, and the contract's own census helper does exactly that.
- **M2 — leak census of `lore_test`:**
  - 2186 DBs shaped `test_<hex32>`: non-harness mints.
  - 456 DBs shaped `test_<pid>_<hex32>`, of which **454 belong to DEAD pids** (430 distinct pids).
  - An 8-worker pytest session belonging to another agent was live at the time.
  - **The leak class is wider than "minted outside `unique_database()`": harness-minted DBs leak too.**
- **M3 — no orphan reaper exists.** `_surreal_harness`'s module docstring says "a reused PID later
  harmlessly reaps any prior orphan". An awk scan of every test tree plus `scripts/` finds no such mechanism.
  The sentence describes nothing: this is the P8d served-prose-vs-code class, in the test harness.
- **M4 — 25 name mints outside `unique_database()`, in 24 files.** Derived by the committed lint
  (`test_harness_database_lifecycle_486.py::_naming_recipe_sites`, generated over every workspace
  member's `tests/`). Re-derived at HEAD `86a55eb`: 26 recipe sites = 1 mint + 25 clones.
  - The files: `_auth_fixtures.slug`, test_build_store, test_cli, test_comms_send_scope_63b_ii_a,
    test_comms_wiring, test_eager_startup_survives_unparseable_file, test_extension ×2,
    test_graph_wiring, test_impact, test_indexer, test_indexer_bulk_sweep,
    test_indexer_chunker_fault_isolation, test_indexer_contextualized, test_map,
    test_mcp_server (HELD), test_memory_cutover, test_reconcile, test_resilient_db,
    test_schema_rebuild, test_search, test_startup_divergence_reconcile, test_static_snapshot_reacquire,
    test_watcher, test_workspace_status.
  - test_startup_divergence_reconcile puts `uuid.getnode() % 100000`, a MAC-derived number, in the pid slot.
  - A slug IS a database name when `surreal.database` is unset (`LoreConfig.effective_surreal_database`), but only if the
    test DIALS. test_build_store's slug never does (sentinel URL).
  - **So "is this mint a database?" is a RUNTIME fact.**
- **M5 — 21 of 124 `unique_database()` call sites never reach a reap in their own function**
  (heuristic, §Instruments I-4). This cannot be decided statically, so the lifetime pin is a STATE pin.
- **M6 — `SLUG_PATTERN` = `^[a-z0-9][a-z0-9_]*$` admits `test_<pid>_<hex32>`**, so every slug mint can
  route through `unique_database()` unchanged. The SAT run's conversion of all 25 clones proves it.
- **M7 — 39 fixed-literal `database=` values in the test trees** (`'db'`, `'probe_db'`,
  `'never_created'`, `'test_fake_db'`, …; the AST scan is in §Instruments I-7). None appears in the M2 census, so none currently
  leaks. Whether any of them DIALS is a runtime fact that the provenance leg adjudicates at the builder's
  suite run.

## The contract (plain English)
**Item 1: `run()` is one attempt body under the store seam.**
- `_surreal_harness.run(connection, statement, params=None)` keeps its signature and return value.
- It now issues its statement as an attempt handed to `_run_under_store_retry_seam`, so:
  - a retryable engine conflict is retried, re-issuing the SAME statement with the SAME params, and the caller gets the success;
  - a domain rejection propagates untouched, as the same exception object, on attempt 1;
  - a sustained conflict raises the SEAM's `TxnContentionExhaustedError`, with one `store.retry.exhausted` record
    carrying `run`'s own label (`_surreal_harness._RUN_STATEMENT_LABEL`) and the engine's text.
- The retry policy is the seam's, proven by the existing generated mutation pins: `run` joins `_OPERATION_PROBES`,
  so the attempt-ceiling and wall-clock-deadline mutations cover it. A marker-mutation pin covers the
  classification (ROUTING IS NOT SHARING).
- **The REACH is a checked variable.** Every engine-door use anywhere in `_surreal_harness` must sit in an attempt body handed to
  `_run_under_store_retry_seam`. The door set is derived from the SDK, deny by default. The only exemption is the
  passthrough instrument `measure_store_traffic`, with its reason stated at the exemption.
- No raw door (D1).

**Item 2: every database a test creates is minted by `unique_database()` in that process and does not
outlive the session.**
- Per-test (runtime, end to end): a pytest session whose test dials a database its process did not mint through
  `unique_database()` FAILS and names it. This includes a perfect forgery of `test_<pid>_<hex32>`, so provenance is
  required and shape is not enough.
- Per-session (runtime, end to end, at `-n 0` AND under xdist):
  - a minted database still present when the session ends is REAPED;
  - the session FAILS, naming the database and the test that leaked it;
  - a database minted by ANOTHER live process survives.
- `unique_database()` records `name -> minting test` in `_MINTED_DATABASES`. `await reap_minted_databases()` removes
  exactly this process's still-present mints and returns them.
- The `test_…` naming recipe exists once. This is an AST lint, labelled as a lint.
- The false "reused PID reaps orphans" claim is retired.

## Test paths
- `loremaster/tests/test_surreal_harness.py` (edited; sha256 prefix `6b150fbc2c7bac34`). Changes:
  - module docstring §#486;
  - `_FakeConnection.query_params` and `query_outcomes: list[Any]`;
  - `_RUN_PROBE_*` / `_run_result` / `_as_connection`;
  - `_probe_run_statement`, and `_RUN_OPERATION_KEY` added to `_OPERATION_PROBES`;
  - discovery drives `run`;
  - `test_run_detection_follows_the_seams_one_conflict_marker`;
  - class `TestRunRidesTheStoreRetrySeam`;
  - allowlist gains `_RUN_STATEMENT_LABEL`, `_MINTED_DATABASES`, `reap_minted_databases`;
  - `_sdk_engine_doors` / `_engine_door_uses` / class `TestTheHarnessMakesNoEngineCallOutsideTheSeam`.
- `loremaster/tests/test_harness_database_lifecycle_486.py` (NEW; sha256 prefix `c731fc98d7b28044`).

## Per-pin: what wrong build would still pass?
| pin | wrong build it kills | wrong build that STILL passes (honest residual) |
|---|---|---|
| `…once_conflicting…returns_the_success` | no retry; retry with dropped/rebuilt params; returning a copy / `result[0]` | a build that retries but classifies locally → killed by the marker pin |
| `…domain_rejection_propagates_untouched…` | wrapping (`SurrealStoreError from`), retrying a domain error, re-raising a copy | — |
| `…happy_path…one_call` | double-issue on success, `params=None`→`{}` | — |
| `…sustained_conflict…attributable_record` | private budget, raw `QueryError` escape, unlabelled or teardown-label reuse, dropped engine text | a label that is a different non-empty string per call (identity is read off the module, so a stable constant is required) |
| ceiling/deadline mutations `[run:…]` (generated) | private attempt ceiling / private deadline | — (two independent constants) |
| `test_run_detection_follows…marker` | local `"can be retried" in str(e)` classification | — |
| reach AST + controls | bare call, alias capture, literal `getattr`, body handed to `retry_on_conflict` bare, name-only `_attempt` | a door reached through a NON-literal `getattr(conn, name)` or a callable captured OUTSIDE the module — the stated honest-developer threat model (only the exempt instrument does the former) |
| recipe lint + controls | every `test_…`+call clone spelling (f-string, concat, `.format`, `%`, getnode, shape-forgery) | a clone with another prefix (`db_{uuid}`); the runtime legs catch it the moment it dials |
| foreign-name e2e (×2) | no check; a SHAPE/regex check (the forged-pid leg); checking only at the end of the session | a check that observes only `use()` misses a database created by a statement-level `USE DB`/`DEFINE DATABASE` inside `run` (no test-tree literal does this today; bound) |
| leak e2e (n0 + xdist) | no reap; silent reap; reap by prefix/shape (kills the outer DB); report lost in the xdist worker; report without the test name | a session that is KILLED: out of scope by design (D2) |
| reaper direct | registry missing or unattributed; reporting dropped DBs as leaks | — |
| retired-claim pin | the false sentence kept | a reworded false claim; this is a lint-grade phrase pin, and it says so |

## Adversarial pre-flight → case or scoped-out
1. Retry drops or rebuilds params → `query_params` / `operations` equality per attempt.
2. Domain error wrapped or retried → identity plus a 1-call pin.
3. Private budget → the generated ceiling and deadline mutations.
4. Local classification → the marker mutation.
5. Unattributed exhaustion → the label and engine_error pin.
6. Laundered result / `None`→`{}` → the identity pins and `query_params == [None]`.
7. A new harness helper outside the seam (the QUANTIFIER door) → the reach pin, over EVERY door use, with 5 escaping-shape controls and 3 covered-shape controls.
8. Multi-statement double-apply on retry → scoped out: 0 literal sites (positive-controlled predicate). Bound: variable-argument sites.
9. Store-traffic counts change → scoped out: no `measure_store_traffic` call wraps `run` (awk, §Instruments I-8). On a conflict the instrument counts WIRE statements, which is the right semantics.
10. The census itself leaks (M1) → the reader DB is minted and dropped, and the cleanup never `use()`s a foreign name (SAT caught the first version doing exactly that, §SAT).
11. Shape forgery → the forged-pid e2e leg.
12. Leak visible only at `-n 0` → the xdist leg.
13. Reaper over-reach onto a concurrent session → the cross-session leg.
14. Silent reap → rc≠0, naming the DB and the test.
15. Killed session (SIGKILL/OOM/watchdog) → scoped out: D2.
16. pid-namespace collision (in-image conformance run, packet 01a) → scoped out: D2.
17. Clone spelled with another prefix → bound (lint); the runtime legs catch it once it dials.
18. Statement-level DB creation (`DEFINE DATABASE x` / `USE DB x` via `run`) → bound: awk finds no test-tree literal outside the bootstrap.
19. Non-`lore_test` namespaces → bound: the reference observes `TEST_NAMESPACE` only.
20. A test that spawns a SERVER subprocess dialing a slug DB → bound: the subprocess's mints are its own; the outer process neither sees nor reaps them.
21. The HELD file stays red until its patch is sequenced → §HELD.
22. Real-distribution tails → the #486 statement, a uuid5 memory id, the engine's exact conflict text, and the census shapes.

## Realism checklist
- ☑ **Production-realistic inputs.** The real #486 `DELETE` statement and its bound param in production's uuid5 id shape. The engine's verbatim conflict text. The real test store for every e2e leg. DB names from the harness mint.
- ☑ **Independent expected values.** Attempt counts are read from the seam's LIVE constants, never from `run`. Outcomes come from the Phase-0 spec and the measured census (M1–M5).
- ☑ **Seam coverage.** The e2e legs drive the real conftest wiring, the real store and a real xdist worker→controller hop. The `use()` door that creates databases was measured (M1), not assumed.
- ☐ **Magnitude bounds** — not applicable because no derived or aggregated numeric output is produced. Attempt counts are pinned EXACTLY against the seam's own constant, and the census is membership, not magnitude.
- ☑ **Shared conventions.** `TEST_NAMESPACE`, `PRODUCTION_DIM`, `unique_database`, the seam constants and labels are read off their modules. The door set is composed from `StoreTraffic` and `_sdk_guard`. Workspace roots come from `[tool.uv.workspace]`. The recipe prefix matches the mint's own.
- ☐ **Hostile fixtures for rendered stored text** — not applicable: no stored free text is rendered. The leak line renders pytest node ids and minted names, both harness-controlled, into terminal prose that nothing machine-parses.
- ☑ **Input accounting (the reaper consumes the registry).** Every minted name has exactly one fate: dropped by its test (absent, not reported), leaked (present, reaped and reported), or another process's (never touched). The reaper direct pin and the cross-session e2e leg each FORCE the fate they cover.

## Removed-behavior inventory adjudication (the diff replaces `run`'s bare call; the docstring claim)
| behaviour | verdict | citation / reason |
|---|---|---|
| `run` never retries a retryable conflict | **dropped-deliberately** | Phase 0 item 1 (operator "Fix now via /tdd-light"); it is #486's cause |
| a domain rejection surfaces raw, same type | **preserved-with-pin** | Phase 0 pin (i) "does NOT retry a domain error"; 38 `pytest.raises` sites (§Raw-door) |
| raw result returned unlaundered; `params=None` forwarded | **preserved-with-pin** | Phase 0 fix home: "routes … through" the seam, a transport change and not a result change; 812 sites index the result |
| exactly one wire call per `run` | **preserved on the happy path (pinned)**, dropped under conflict | the fix itself |
| an observer of a conflicted `run` sees the raw error | **spec-silent → none found** | 0/812 sites observe it (§Raw-door), so no ruling is needed unless D1 is overruled |
| docstring: "a reused PID later harmlessly reaps any prior orphan" | **old-bug (false claim) — retired, NOT re-pinned** | M3; the pin asserts its absence; the mechanism itself is fork D2 |
| a minted DB outlives a session that ends normally | **dropped-deliberately** | Phase 0 item 2: "make every minted DB reaped" |
| `unique_database()` output shape `test_<pid>_<hex32>` | **preserved (unpinned)** | store reference §1.6 describes it, and M6 needs it slug-legal. A shape pin would invite the regex check the forgery leg exists to kill |

**Deliberate-drop list:** "never retries" · "minted DBs outlive a session". **Spec-silent list:** none open (the raw-conflict observer has 0 sites).

## §Raw-door table (derivation: §Instruments I-1/I-2; 812 `run()` sites, alias-followed)
A site NEEDS the raw door iff the test depends on a RETRYABLE ENGINE CONFLICT surfacing raw from that call.

| class | sites | verdict | why |
|---|---|---|---|
| inside `pytest.raises(Exception \| SurrealError)` expecting a DOMAIN rejection: test_audit_ddl_composition_root_63a_iv, test_audit_schema, test_comms_schema ×7, test_floor_calibration_schema ×6, test_ingest_entity_seam, test_keeps_schema ×2, test_principal_keys_schema, test_principals_schema ×2, test_surreal_schema ×5, test_surreal_store ×11 | 38 | **retried `run`** | A non-conflict error propagates UNTOUCHED on attempt 1. ⚠ Pre-existing, surfaced: `pytest.raises(Exception)` also admits a raw conflict. Before the fix such a site could pass for the WRONG reason; after it, an exhaustion is still an `Exception`. |
| function mentions "conflict": test_agent_governance_63c_i_a ×4, test_fixwave_a19b ×2, test_fixwave_a28 ×6, test_fixwave_a28b ×2, test_governed_substrate_63a ×2, test_message_migrate_dirty_store_63b_ii_b ×1 | 17 | **retried `run`** | `GovernedConflict` / keep-CAS races (DOMAIN) or verification SELECTs. None observes `can be retried`. |
| test_retry_seam.py (a28b, read-only) `:2366 :2554 :2557 :3285 :3286` | 5 | **retried `run`** | setup DDL. **No HELD patch needed.** |
| test_store_lease.py / test_txn_contention.py (Phase-0 worklist) | 0 | n/a | their marker mentions are prose (`:1268`, `:1364`) and a fake's constant (`:102`) |
| broad `except Exception` around `run`: `_count` helpers in test_audit_store, test_keep_remediation_store_61, test_keeps_store, test_principal_delete_cascade_61; test_memory_enforcement_63b_ia `:588` (a BEGIN…THROW…COMMIT probe) | 5 | **retried `run`** | ⚠ Pre-existing, surfaced: the `_count` helpers map ANY error to `0`, so a conflict (before the fix) or an exhaustion (after) reads as a silent false count. |

**0 of 812 need the raw door.** No test adopts one, and no existing test needs editing for Item 1.

## §RED receipt (HEAD `e039c64` tree; re-run 2026-09-26 at HEAD `86a55eb`: identical set)
`uv run pytest -p no:cacheprovider -q -n 12 loremaster/tests/test_harness_database_lifecycle_486.py loremaster/tests/test_surreal_harness.py -rf`
→ **15 failed, 80 passed in 9.12s**.

RED, each for the reason named:
- test_surreal_harness.py (7):
  - `TestRunRidesTheStoreRetrySeam::…once_conflicting…`: a raw QueryError escapes.
  - `…::…sustained_conflict…`: raw QueryError, not the seam type.
  - `test_run_detection_follows_the_seams_one_conflict_marker`: the control leg made 1 call.
  - `test_every_operation_follows_the_seams_attempt_ceiling[run:DELETE type::record('memory',]` and `…wall_clock_deadline[run:…]`: the probe's `pytest.raises(TxnContentionExhaustedError)` gets a raw QueryError.
  - `TestTheHarnessMakesNoEngineCallOutsideTheSeam::test_every_engine_door_use…`: flags `run:… -> .query`.
  - `test_the_harnesss_module_level_names_are_exactly_the_allowed_set`: the 3 new names are not yet declared (stub-level).
- test_harness_database_lifecycle_486.py (8):
  - recipe lint: 25 clones.
  - foreign-name e2e ×2: the inner session passed with rc 0, including for the forged `test_<pid>_…` name.
  - leak e2e `[n0]` and `[xdist-n2]`: the minted DB OUTLIVED the session, which I checked in the namespace.
  - `test_unique_database_records…`: no registry (stub-level).
  - `test_the_reaper_removes…`: no reaper (stub-level).
  - retired-claim pin: the phrase is present.

GREEN at HEAD by design (6 new): `…domain_rejection_propagates_untouched…`, `…happy_path…` (preservation) · the foreign-name CONTROL, the clean-session CONTROL (e2e controls) · recipe `…sees_the_one_mint`, `…documented_exception…` (non-vacuity) · plus the controls parametrized inside the scanners.
Every RED run's inner-created databases were verified ABSENT afterwards (`check_names.py`, §Instruments I-6).

## §SAT (satisfiability receipt)
Reference build in `./scripts/scratch_copy.sh …/scratchpad/sat486`:
`loremaster.__file__ = /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/b777bee8-d4cc-4b19-b792-b8b8b42ee1cd/scratchpad/sat486/loremaster/loremaster/__init__.py`.
The reference diff is in §Instruments I-9; the 25 clones were converted by the I-10 script.

The run covered both contract files plus four heavy store neighbours: test_memory_replay_fidelity_63b_ib (the #486 site), test_surreal_schema (`run`-heavy), test_comms_wiring (a slug becomes a DB through production code), and test_memory_enforcement_63b_ia (the `run`-heavy rollback probe, the observer, and the `_CALL_HOOKS` detach pin).
- **Run 1: 253 passed + 6 ERRORS, which exposed a defect IN THIS CONTRACT.** Its cleanup `drop_database`-d the inner session's names, `use()`-ing databases the outer process never minted, and the provenance leg correctly failed it. I fixed the contract: cleanup now issues `REMOVE DATABASE <name>` from a minted reader connection.
- **Final run, on the final bytes (hashes above): `259 passed, 1 warning in 55.66s`, rc=0.** The warning is pre-existing (test_memory_enforcement_63b_ia's raising-hook pin, an un-awaited coroutine). No `LEAKED` line appeared: the neighbours leak nothing under the reference.
- Satisfiable after the lint-demanded cleanup: the converted files keep orphaned `uuid` imports, which ruff F401 will ask the builder to delete. No pin reads them.

## §Stub expectations (names the contract DECIDES; the exact-set allowlist pin forces exactly these)
- `_surreal_harness._RUN_STATEMENT_LABEL: str`: `run`'s seam label, distinct from both `_TEARDOWN_*_LABEL`.
- `_surreal_harness._MINTED_DATABASES: dict[str, str]`: name → minting test (from `PYTEST_CURRENT_TEST` at mint time). `unique_database()` records into it IN PLACE; a rebinding global would be invisible to holders.
- `async _surreal_harness.reap_minted_databases() -> Iterable[str]`: removes every recorded database still present in the test namespace, returns their names, and touches nothing else. Its engine calls must ride `_run_under_store_retry_seam` (the reach pin covers it).
- The per-test provenance check and the session-end reap must be armed from `loremaster/tests/conftest.py` or by importing `_surreal_harness`. The e2e legs load exactly those (`-p conftest`). Under xdist, the worker's reap report must reach the controller's output and exit status.
- **Any OTHER new module-level name in `_surreal_harness` is a contract amendment**, not a builder decision: the allowlist is exact-set.
- Convention to follow: `_governed_contract` GOTCHA-B. A `_sdk_guard._CALL_HOOKS` observer is appended ONCE at import, never per test (a detach pin clears and restores the list).

## §Builder worklist (derived)
1. `run` → an attempt body under `_run_under_store_retry_seam(label=_RUN_STATEMENT_LABEL, …)`.
2. `_MINTED_DATABASES`, `unique_database()` recording, and `reap_minted_databases()`.
3. conftest: the per-test provenance check (observe `use(TEST_NAMESPACE, db)`) and the session-end reap, which must be loud (rc≠0, naming the DB and the test) and xdist-aware.
4. Harness docstring: drop the reused-PID claim. State the session-end guarantee and the killed-session bound.
5. Convert the 24 non-HELD clone sites (23 files) to `unique_database()`, and delete the orphaned `uuid` imports.
6. Run the full suite at the checkpoint. The provenance leg adjudicates M7's 39 fixed-literal names at runtime, and a straggler that dials will fail loudly by design.

## §HELD (file owned by another agent: 64b's `test_mcp_server.py`; sequence after it commits)
```diff
--- loremaster/tests/test_mcp_server.py  (::_slug)
-    slug = f"test_{uuid.uuid4().hex}"
+    slug = unique_database()
```
(`unique_database` is already imported there, verified in the SAT conversion.) Until it lands, `test_no_test_tree_builds_a_test_name_outside_unique_database` stays RED on this one site. Once the builder arms the provenance check, test_mcp_server's store-dialing tests FAIL at teardown. **Sequence the HELD patch with the builder's conftest change.**

## Decisions needed
- **D1 — no raw door.** Phase 0 admits two readings: "add an explicit raw door" (mandated) vs "a raw door for tests that deliberately observe a raw conflict" (conditional). I measured 0 of 812 such sites and picked the second. If the operator wants the door anyway, it costs one allowlist entry plus one reach-exemption entry.
- **D2 — orphans of KILLED sessions (the 454 dead-pid DBs, and every future SIGKILL/OOM/watchdog kill).**
  - Reaping them means reaping ANOTHER process's databases, keyed on "its pid is dead".
  - The pid slot is not unique across pid namespaces: packet 01a's in-image conformance run is a container.
  - A host-side "dead pid" test could therefore destroy a LIVE container session's database, and a reused pid shields an orphan (the fail-safe direction).
  - Recommendation: mint a namespace-unique process token instead of the bare pid (e.g. `test_<pid>_<boot-or-pidns-id>_<hex>`), THEN a start-of-session sweep of dead local tokens. That is design work, so it goes to the design sidecar.
- **D3 — `scripts/` probe clones:**
  - 8 probe scripts carry their own `test_<pid>_<uuid>` recipe copies. `probe_store_recovery_07a.py` mints `probe07a_<uuid>` and has no reap in-file.
  - Extending the lint's domain to `scripts/` would force them to import the harness.
  - Operator's call. The scratch tools (`scratch_copy.sh`, `scratch_provenance.py`) mint NO databases: 0 `database`/`surreal`/`uuid` mentions.
- **D4 — a one-shot cleanup of the current leaks** (2186 `test_<hex32>` + 454 dead-pid). It is destructive on the shared store and another agent's live suite uses it. A `test_<hex32>` name can still be minted by a session running OLDER code (another worktree), so the cleanup should wait for the fix to land fleet-wide. The lead/operator decides.

## Surfaced (outside this change; the operator owns scope)
- `pytest.raises(Exception)` around `run` (38 sites) admits a conflict or an exhaustion as the "rejection".
- The `_count` helpers (4 files) turn any store error into `0`.
- The harness docstring's "Nothing leaks" is also false for killed sessions (covered by the retired-claim fix and D2).
- `_sdk_guard.SAFE_CONNECTION_METHODS`' 256-connect receipt is self-declared UNVERIFIED (already noted in #486's investigation; not new).

## §DRY ledger (new reusable symbols, all test-side)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_sdk_engine_doors` (test_surreal_harness) | n/a: a direct equality measurement against `StoreTraffic` | the union of `StoreTraffic.uncountable_doors()` and `StoreTraffic.COUNTABLE_DOORS` minus SAFE equals a from-scratch derivation (empty symmetric difference) | **REUSED `StoreTraffic.uncountable_doors` + `StoreTraffic.COUNTABLE_DOORS`** (my first draft re-derived it; rewritten) |
| `_engine_door_uses` / `_DoorUse` | `lore_search` "derive workspace member test directories…" (adjacent) plus a read of the harness scanners | the existing scanners (`_module_level_imported_modules`, `_harness_importer_files`) answer different questions | **HAND-ROLLED**: no existing "door use covered by an attempt body" classifier |
| `_workspace_test_roots` (lifecycle) | `lore_search` "derive workspace member test directories from pyproject tool.uv.workspace members" | only the packet-42 report discussing per-module mirror constants; no shared helper | **HAND-ROLLED**: every existing scanner derives its roots locally. ⚠ A `lorerunes`-style shared test-tooling home would be the ONE-IMPLEMENTATION answer; escalated as an observation, not built |
| `_naming_recipe_sites` / `_RecipeSite` | as above | none | **HAND-ROLLED**: a new question |
| `_databases_in_the_test_namespace` | `lore_search` "list every database in the test namespace INFO FOR NS helper" | only SurrealQL spec files | **HAND-ROLLED**: none exists |
| `_remove_if_present`, `_run_inner_session` / `_InnerSession` | pytester read (Packages line) | `runpytest_subprocess` is equivalent but not enabled | **HAND-ROLLED** (`keep_with_trigger`) |

## §Instruments (pasted VERBATIM, brief-base §1; the two committed scanners live in the test files)

### I-1 raw-door scan (run() in pytest.raises / conflict-marker functions)
Run: `uv run python rawdoor_scan.py <repo>` → 812 sites, 57 candidates.
```python
"""Raw-door worklist for #486 (contract-486). For every call of the harness `run` (import-alias
followed, plus `_surreal_harness.run` attribute calls) in every workspace member's tests dir:
report (a) whether it sits lexically inside a `with pytest.raises(...)` block and the expected
type text; (b) whether its ENCLOSING function's source mentions a conflict marker. A site is a
CANDIDATE if (a) expects a type that a raw retryable conflict could satisfy, or (b) holds."""
import ast, sys, tomllib
from pathlib import Path
ROOT = Path(sys.argv[1])
MARKERS = ("can be retried", "Resource busy", "RetryableConflict", "retryable", "conflict")
members = tomllib.loads((ROOT/"pyproject.toml").read_text())["tool"]["uv"]["workspace"]["members"]
roots = [ROOT/m/"tests" for m in members if (ROOT/m/"tests").is_dir()]
total = 0; cands = []
for r in roots:
    for p in sorted(r.rglob("*.py")):
        if p.name == "_surreal_harness.py": continue
        src = p.read_text(); tree = ast.parse(src)
        names = {a.asname or a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == "_surreal_harness" for a in n.names if a.name == "run"}
        parents = {}
        for n in ast.walk(tree):
            for c in ast.iter_child_nodes(n): parents[c] = n
        def enclosing(n):
            c = parents.get(n)
            while c is not None and not isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)): c = parents.get(c)
            return c
        def raises_ctx(n):
            c = parents.get(n)
            while c is not None and not isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if isinstance(c, (ast.With, ast.AsyncWith)):
                    for item in c.items:
                        e = item.context_expr
                        if isinstance(e, ast.Call) and ast.unparse(e.func).endswith("raises"):
                            return ast.unparse(e.args[0]) if e.args else "?"
                c = parents.get(c)
            return None
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call): continue
            f = n.func
            is_run = (isinstance(f, ast.Name) and f.id in names) or (isinstance(f, ast.Attribute) and f.attr == "run" and ast.unparse(f.value) == "_surreal_harness")
            if not is_run: continue
            total += 1
            fn = enclosing(n)
            fsrc = ast.get_source_segment(src, fn) if fn else ""
            mk = [m for m in MARKERS if m in (fsrc or "")]
            rx = raises_ctx(n)
            if rx or mk:
                cands.append((str(p.relative_to(ROOT)), n.lineno, fn.name if fn else "<module>", rx, mk))
print("TOTAL run() call sites:", total)
print("CANDIDATES:", len(cands))
for c in cands: print(f"{c[0]}:{c[1]} [{c[2]}] raises={c[3]} markers={c[4]}")
```

### I-2 raw-door scan, second door (broad except / suppress / gather)
Run as I-1 → 5 hits.
```python
"""Second raw-door door: run() call sites inside a try whose handler catches Exception/BaseException/
QueryError/SurrealError/ServerError (any error type a raw conflict could satisfy), or passed into an
asyncio.gather(..., return_exceptions=True). Workspace test trees, alias-followed."""
import ast, sys, tomllib
from pathlib import Path
ROOT = Path(sys.argv[1])
CATCH = {"Exception", "BaseException", "QueryError", "SurrealError", "ServerError", "SurrealDBError"}
members = tomllib.loads((ROOT/"pyproject.toml").read_text())["tool"]["uv"]["workspace"]["members"]
for m in members:
    r = ROOT/m/"tests"
    if not r.is_dir(): continue
    for p in sorted(r.rglob("*.py")):
        if p.name == "_surreal_harness.py": continue
        src = p.read_text(); tree = ast.parse(src)
        names = {a.asname or a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == "_surreal_harness" for a in n.names if a.name == "run"}
        if not names: continue
        parents = {}
        for n in ast.walk(tree):
            for c in ast.iter_child_nodes(n): parents[c] = n
        def is_run(n):
            return isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in names
        for n in ast.walk(tree):
            if not is_run(n): continue
            c = parents.get(n); why = None
            while c is not None and not isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if isinstance(c, ast.Try) and any(n in ast.walk(stmt) for stmt in c.body):
                    for h in c.handlers:
                        t = ast.unparse(h.type) if h.type else "bare"
                        if h.type is None or any(x in t for x in CATCH): why = f"try/except {t}"
                if isinstance(c, ast.Call) and ast.unparse(c.func).endswith("gather") and any(k.arg == "return_exceptions" for k in c.keywords): why = "gather(return_exceptions)"
                if isinstance(c, ast.Call) and "suppress" in ast.unparse(c.func): why = f"suppress({ast.unparse(c.args[0]) if c.args else ''})"
                if isinstance(c, (ast.With, ast.AsyncWith)):
                    for it in c.items:
                        e = it.context_expr
                        if isinstance(e, ast.Call) and "suppress" in ast.unparse(e.func): why = f"with suppress({', '.join(ast.unparse(a) for a in e.args)})"
                c = parents.get(c)
            if why: print(f"{p.relative_to(ROOT)}:{n.lineno} {why} :: {ast.unparse(n)[:90]}")
```

### I-3 multi-statement literal scan (shared predicate)
Run from repo root → 0 BARE-multi, 0 BEGIN-envelope; positive control: `'CREATE a; CREATE b'` → MULTI.
```python
"""run() sites whose LITERAL statement is multi-statement per the SHARED predicate
(_txn._assert_envelope_integrity), split by whether it is a BEGIN..COMMIT envelope."""
import ast, sys, tomllib
from pathlib import Path
from loremaster.store import _txn
ROOT = Path(sys.argv[1])
members = tomllib.loads((ROOT/"pyproject.toml").read_text())["tool"]["uv"]["workspace"]["members"]
def text(n):
    if isinstance(n, ast.Constant) and isinstance(n.value, str): return n.value
    if isinstance(n, ast.JoinedStr): return "".join(v.value if isinstance(v, ast.Constant) else "X" for v in n.values)
    if isinstance(n, ast.BinOp): return (text(n.left) or "") + (text(n.right) or "")
    return None
for m in members:
    r = ROOT/m/"tests"
    if not r.is_dir(): continue
    for p in sorted(r.rglob("*.py")):
        tree = ast.parse(p.read_text())
        names = {a.asname or a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == "_surreal_harness" for a in n.names if a.name == "run"}
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in names and len(n.args) >= 2:
                t = text(n.args[1])
                if t is None: continue
                try: _txn._assert_envelope_integrity(t)
                except _txn.TxnEnvelopeViolationError:
                    kind = "BEGIN-envelope" if t.lstrip().upper().startswith("BEGIN") else "BARE-multi"
                    print(f"{p.relative_to(ROOT)}:{n.lineno} {kind} :: {t[:70]!r}")
```

### I-4 unreaped unique_database() sites (heuristic)
→ 21 of 124.
```python
"""unique_database() call sites whose enclosing FUNCTION never reaches a reap
(drop_database / drop_surreal_database / REMOVE DATABASE / _remove_database_with_retry) — a
heuristic worklist (a site may hand the env to a fixture that reaps)."""
import ast, sys, tomllib
from pathlib import Path
ROOT = Path(sys.argv[1])
REAP = ("drop_database", "drop_surreal_database", "REMOVE DATABASE", "_remove_database_with_retry")
members = tomllib.loads((ROOT/"pyproject.toml").read_text())["tool"]["uv"]["workspace"]["members"]
n_all = 0
for m in members:
    r = ROOT/m/"tests"
    if not r.is_dir(): continue
    for p in sorted(r.rglob("*.py")):
        src = p.read_text(); tree = ast.parse(src)
        parents = {}
        for n in ast.walk(tree):
            for c in ast.iter_child_nodes(n): parents[c] = n
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and ast.unparse(n.func).endswith("unique_database"):
                n_all += 1
                c = parents.get(n)
                while c is not None and not isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)): c = parents.get(c)
                body = ast.get_source_segment(src, c) if c else ""
                if c is not None and c.name == "unique_database": continue
                if not any(k in body for k in REAP):
                    print(f"{p.relative_to(ROOT)}:{n.lineno} [{c.name if c else '<module>'}]")
print("total unique_database() call sites:", n_all)
```

### I-5a probe: which call creates a database (TEST store)
Leg A printed `True`; leg B raised NotFoundError (DB already created by use()); cleanup + controls in I-5b.
```python
"""Probe (TEST store :18000 only): which SDK call materialises a database in lore_test?
Legs: (A) use() only; (B) use() + SELECT on a missing table; (C) control: DEFINE DATABASE.
Each leg's DB is removed afterwards. Prints the engine version and each leg's verdict."""
import asyncio, os, uuid
from surrealdb import AsyncSurreal
URL = "ws://127.0.0.1:18000/rpc"
NS = "lore_test"
async def admin():
    c = AsyncSurreal(URL); await c.signin({"username":"root","password":"spikeroot"}); return c
async def exists(name):
    c = await admin(); await c.use(NS, "census_readonly_nonexistent")
    info = await c.query("INFO FOR NS"); await c.close()
    return name in (info or {}).get("databases", {})
async def remove(name):
    c = await admin(); await c.use(NS, name); await c.query(f"REMOVE DATABASE IF EXISTS {name}"); await c.close()
async def main():
    tag = f"probe486_{os.getpid()}_{uuid.uuid4().hex[:8]}"
    a, b, ctl = f"{tag}_a", f"{tag}_b", f"{tag}_c"
    c = await admin(); print("version", await c.version())
    await c.use(NS, a); await c.close()
    print("A use-only creates:", await exists(a))
    c = await admin(); await c.use(NS, b); await c.query("SELECT * FROM nothing_here"); await c.close()
    print("B use+SELECT creates:", await exists(b))
    c = await admin(); await c.query(f"DEFINE NAMESPACE IF NOT EXISTS {NS}"); await c.use(NS, "census_readonly_nonexistent"); await c.query(f"DEFINE DATABASE IF NOT EXISTS {ctl}"); await c.close()
    print("C control DEFINE DATABASE creates:", await exists(ctl))
    for n in (a, b, ctl): await remove(n)
    print("after cleanup exist:", [await exists(n) for n in (a, b, ctl)])
    await remove("census_readonly_nonexistent")
asyncio.run(main())
```

### I-5b cleanup + negative/positive controls
→ negative control False; positive control True; probe leftovers removed.
```python
"""Cleanup + controls for use_creates_probe.py (TEST store :18000 only).
Reads INFO FOR NS from a connection whose use() targets a DB that is then REMOVED, so the
census connection's own side effect is cleaned too. Negative control: a never-used name reads absent."""
import asyncio, os, uuid
from surrealdb import AsyncSurreal
URL = "ws://127.0.0.1:18000/rpc"; NS = "lore_test"
async def admin():
    c = AsyncSurreal(URL); await c.signin({"username":"root","password":"spikeroot"}); return c
async def dbs():
    c = await admin(); await c.use(NS, "census486_tmp")
    info = await c.query("INFO FOR NS"); await c.query("REMOVE DATABASE IF EXISTS census486_tmp"); await c.close()
    return set((info or {}).get("databases", {}))
async def remove(name):
    c = await admin(); await c.use(NS, name); await c.query(f"REMOVE DATABASE IF EXISTS {name}"); await c.close()
async def main():
    probe = sorted(d for d in await dbs() if d.startswith("probe486_") or d == "census_readonly_nonexistent")
    print("probe leftovers:", probe)
    for n in probe: await remove(n)
    never = f"probe486_never_{uuid.uuid4().hex[:8]}"
    after = await dbs()
    print("negative control (never-used name present):", never in after)
    print("leftovers after cleanup:", sorted(d for d in after if d.startswith("probe486_") or d in {"census_readonly_nonexistent","census486_tmp"}))
    # positive control: DEFINE DATABASE creates
    ctl = f"probe486_ctl_{uuid.uuid4().hex[:8]}"
    c = await admin(); await c.use(NS, "census486_tmp"); await c.query(f"DEFINE DATABASE IF NOT EXISTS {ctl}"); await c.query("REMOVE DATABASE IF EXISTS census486_tmp"); await c.close()
    print("positive control DEFINE DATABASE present:", ctl in await dbs())
    await remove(ctl)
    print("final leftovers:", sorted(d for d in await dbs() if d.startswith("probe486_") or d in {"census_readonly_nonexistent","census486_tmp"}))
asyncio.run(main())
```

### I-6a pid census
→ 456 pid-shaped, 430 pids, 454 in DEAD pids.
```python
"""Census (TEST store :18000, read-only except its own reader DB): pid-shaped test DBs by pid liveness."""
import asyncio, re, os, collections
from surrealdb import AsyncSurreal
async def main():
    c = AsyncSurreal("ws://127.0.0.1:18000/rpc"); await c.signin({"username":"root","password":"spikeroot"})
    await c.use("lore_test", "census486_tmp"); info = await c.query("INFO FOR NS")
    await c.query("REMOVE DATABASE IF EXISTS census486_tmp"); await c.close()
    by_pid = collections.Counter()
    for d in info["databases"]:
        m = re.fullmatch(r"test_(\d+)_[0-9a-f]{32}", d)
        if m: by_pid[int(m.group(1))] += 1
    alive = {p: os.path.exists(f"/proc/{p}") for p in by_pid}
    print("pid-shaped:", sum(by_pid.values()), "distinct pids:", len(by_pid))
    print("in LIVE pids:", sum(n for p, n in by_pid.items() if alive[p]), "in DEAD pids:", sum(n for p, n in by_pid.items() if not alive[p]))
    print("top dead pids:", [(p, n) for p, n in by_pid.most_common() if not alive[p]][:10])
asyncio.run(main())
```

### I-6b named-DB presence check (used to verify every RED run's cleanup)

```python
"""Are the named DBs present in lore_test on the TEST store? Reader DB removed after."""
import asyncio, sys
from surrealdb import AsyncSurreal
async def main(names):
    c = AsyncSurreal("ws://127.0.0.1:18000/rpc"); await c.signin({"username":"root","password":"spikeroot"})
    await c.use("lore_test", "census486_tmp"); info = await c.query("INFO FOR NS")
    await c.query("REMOVE DATABASE IF EXISTS census486_tmp"); await c.close()
    dbs = set(info["databases"])
    print({n: (n in dbs) for n in names}, "total:", len(dbs))
asyncio.run(main(sys.argv[1:]))
```

### I-7 fixed-literal database names (M7)
Run from repo root → 39 hits.
```python
import ast, tomllib
from pathlib import Path
members = tomllib.loads(Path("pyproject.toml").read_text())["tool"]["uv"]["workspace"]["members"]
for m in members:
    r = Path(m)/"tests"
    if not r.is_dir(): continue
    for p in sorted(r.rglob("*.py")):
        tree = ast.parse(p.read_text())
        for n in ast.walk(tree):
            if isinstance(n, ast.keyword) and n.arg == "database" and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                print(f"{p}:{n.value.lineno} database={n.value.value!r}")
            if isinstance(n, ast.Dict):
                for k, v in zip(n.keys, n.values):
                    if isinstance(k, ast.Constant) and k.value == "database" and isinstance(v, ast.Constant) and isinstance(v.value, str):
                        print(f"{p}:{v.lineno} 'database': {v.value!r}")
```

### I-8 does any measure_store_traffic call wrap run()?
→ no output.
```bash
# run from loremaster/tests: any run( within 6 lines after a measure_store_traffic( call
awk '/measure_store_traffic\(/{f=FILENAME; l=FNR; c=6} c>0{ if ($0 ~ /(^|[^_a-z])run\(/) print f":"FNR": "$0; c--}' *.py
```

### I-9a reference build — _surreal_harness.py (SAT only; NOT a builder instruction)

```diff
diff --git a/loremaster/tests/_surreal_harness.py b/loremaster/tests/_surreal_harness.py
index 43c7f17..4e9c29c 100644
--- a/loremaster/tests/_surreal_harness.py
+++ b/loremaster/tests/_surreal_harness.py
@@ -17,7 +17,8 @@ Isolation: every test/fixture gets a UNIQUE throwaway database under the
 ``lore_test`` namespace (``test_<pid>_<uuid4>``), and teardown issues
 ``REMOVE DATABASE IF EXISTS`` on it via a FRESH admin connection (independent of
 whatever connection the test used, which a resilience test may have deliberately
-broken). Nothing leaks; a reused PID later harmlessly reaps any prior orphan.
+broken). Every name ``unique_database()`` mints is recorded, and the session's end reaps
+any still present (a killed session's databases are NOT covered).
 
 Import isolation: at MODULE level this imports ONLY the ``surrealdb`` SDK and the
 pre-existing ``loremaster.index.records`` helpers, so it always imports cleanly.
@@ -126,6 +127,10 @@ TIER_B = "community"
 # Shape follows the store seams' own ``_SEAM_REJECTION_EVENTS`` convention.
 _TEARDOWN_SELECT_DATABASE_LABEL = "harness.teardown.select_database"
 _TEARDOWN_REMOVE_DATABASE_LABEL = "harness.teardown.remove_database"
+_RUN_STATEMENT_LABEL = "harness.run.statement"
+
+# name -> the minting test (PYTEST_CURRENT_TEST at mint time)
+_MINTED_DATABASES: dict[str, str] = {}
 
 
 def surreal_url() -> str:
@@ -157,7 +162,9 @@ def unique_database() -> str:
     never collides on, or reaps, this database — the same concurrency-safety the
     Qdrant conftest gets from its per-process collection prefix.
     """
-    return f"test_{os.getpid()}_{uuid.uuid4().hex}"
+    name = f"test_{os.getpid()}_{uuid.uuid4().hex}"
+    _MINTED_DATABASES[name] = os.environ.get("PYTEST_CURRENT_TEST", "<outside a test>")
+    return name
 
 
 @dataclass(frozen=True)
@@ -204,7 +211,12 @@ async def run(
     tests can index/``.get`` results without a cascade of union-narrowing noise —
     the same pattern ``conftest.kz_query``/``kz_row`` use for the Kùzu union.
     """
-    return await connection.query(statement, params)
+    async def _statement() -> Any:
+        return await connection.query(statement, params)
+
+    return await _run_under_store_retry_seam(
+        _statement, label=_RUN_STATEMENT_LABEL, url=str(getattr(connection, "raw_url", "unknown"))
+    )
 
 
 def assert_domain_rejection(error: BaseException) -> None:
@@ -924,3 +936,24 @@ async def admin_db() -> AsyncIterator[tuple[SurrealConnection, SurrealEnv]]:
     finally:
         await connection.close()
         await drop_database(env)
+
+
+async def reap_minted_databases() -> tuple[str, ...]:
+    """Remove every database this process minted that is still present; return their names."""
+    if not _MINTED_DATABASES:
+        return ()
+    reader_env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
+    connection = await connect_admin(reader_env)
+    leaked: tuple[str, ...] = ()
+    try:
+        info = await run(connection, "INFO FOR NS")
+        present = set(info.get("databases", {})) if isinstance(info, dict) else set()
+        leaked = tuple(
+            sorted(n for n in _MINTED_DATABASES if n in present and n != reader_env.database)
+        )
+        for name in leaked:
+            await _remove_database_with_retry(connection, name, url=reader_env.url)
+    finally:
+        await connection.close()
+        await drop_database(reader_env)
+    return leaked
```

### I-9b reference build — conftest.py (SAT only)

```diff
diff --git a/loremaster/tests/conftest.py b/loremaster/tests/conftest.py
index 7e0537c..1de8d6c 100644
--- a/loremaster/tests/conftest.py
+++ b/loremaster/tests/conftest.py
@@ -232,3 +232,74 @@ def _no_sdk_call_escapes_the_retry_driver(monkeypatch: pytest.MonkeyPatch) -> It
         "(query_raw), never bare .query(). Checked at RUNTIME on the real SDK class (the "
         "#144 posture), replacing the per-module hand-list."
     )
+
+
+
+# ===========================================================================
+# #486 item 2 (REFERENCE BUILD for the contract's SAT receipt only): every database a test
+# opens is minted by unique_database(); every minted database is reaped at session end, loudly.
+# ===========================================================================
+import json as _json_486  # noqa: E402
+
+import _sdk_guard as _sdk_guard_486  # noqa: E402
+
+_OPENED_486: list[str] = []
+
+
+def _record_use_486(event, coro):  # type: ignore[no-untyped-def]
+    if event.method == "use":
+        namespace = event.args[0] if event.args else event.kwargs.get("namespace")
+        database = event.args[1] if len(event.args) > 1 else event.kwargs.get("database")
+        import _surreal_harness
+
+        if namespace == _surreal_harness.TEST_NAMESPACE and database is not None:
+            _OPENED_486.append(str(database))
+    return coro
+
+
+if _record_use_486 not in _sdk_guard_486._CALL_HOOKS:
+    _sdk_guard_486._CALL_HOOKS.append(_record_use_486)
+
+
+@pytest.fixture(autouse=True)
+def _every_database_a_test_opens_was_minted_by_the_harness() -> Iterator[None]:
+    import _surreal_harness
+
+    _OPENED_486.clear()
+    yield
+    foreign = sorted({d for d in _OPENED_486 if d not in _surreal_harness._MINTED_DATABASES})
+    _OPENED_486.clear()
+    if foreign:
+        pytest.fail(f"this test opened database(s) NOT minted by unique_database(): {foreign}")
+
+
+_LEAKS_486: list[tuple[str, str]] = []
+
+
+def pytest_sessionfinish(session, exitstatus):  # type: ignore[no-untyped-def]
+    import asyncio
+
+    import _surreal_harness
+
+    registry = dict(_surreal_harness._MINTED_DATABASES)
+    leaked = asyncio.run(_surreal_harness.reap_minted_databases()) if registry else ()
+    report = [(name, registry.get(name, "?")) for name in leaked]
+    workeroutput = getattr(session.config, "workeroutput", None)
+    if workeroutput is not None:
+        workeroutput["lore_486_leaked"] = _json_486.dumps(report)
+        return
+    _LEAKS_486.extend(report)
+    if _LEAKS_486:
+        session.exitstatus = pytest.ExitCode.TESTS_FAILED
+
+
+@pytest.hookimpl(optionalhook=True)
+def pytest_testnodedown(node, error):  # type: ignore[no-untyped-def]
+    raw = getattr(node, "workeroutput", {}).get("lore_486_leaked")
+    if raw:
+        _LEAKS_486.extend(tuple(pair) for pair in _json_486.loads(raw))
+
+
+def pytest_terminal_summary(terminalreporter):  # type: ignore[no-untyped-def]
+    for name, minted_by in _LEAKS_486:
+        terminalreporter.write_line(f"LEAKED test database {name} (minted by {minted_by}) — reaped")
```

### I-10 clone conversion used in the SAT copy (run in the copy's root)
→ total replaced: 25.
```python
import re, ast
from pathlib import Path
clones = {
 "_auth_fixtures.py","test_build_store.py","test_cli.py","test_comms_send_scope_63b_ii_a.py","test_comms_wiring.py",
 "test_eager_startup_survives_unparseable_file.py","test_extension.py","test_graph_wiring.py","test_impact.py","test_indexer.py",
 "test_indexer_bulk_sweep.py","test_indexer_chunker_fault_isolation.py","test_indexer_contextualized.py","test_map.py",
 "test_mcp_server.py","test_memory_cutover.py","test_reconcile.py","test_resilient_db.py","test_schema_rebuild.py","test_search.py",
 "test_startup_divergence_reconcile.py","test_static_snapshot_reacquire.py","test_watcher.py","test_workspace_status.py"}
pat = re.compile(r'f"test_(?:bulk_|\{uuid\.getnode\(\) % 100000\}_)?\{uuid\.uuid4\(\)\.hex\}"')
n = 0
for name in sorted(clones):
    p = Path("loremaster/tests")/name
    s = p.read_text()
    s2, k = pat.subn("unique_database()", s)
    n += k
    tree = ast.parse(s2)
    has = any(isinstance(x, ast.ImportFrom) and x.module == "_surreal_harness" and any(a.name == "unique_database" for a in x.names) for x in tree.body)
    if not has:
        # insert after the last top-level import
        last = max(x.end_lineno for x in tree.body if isinstance(x, (ast.Import, ast.ImportFrom)))
        lines = s2.splitlines(keepends=True)
        lines.insert(last, "from _surreal_harness import unique_database\n")
        s2 = "".join(lines)
    p.write_text(s2)
    print(name, k, "import-added" if not has else "")
print("total replaced:", n)
```
