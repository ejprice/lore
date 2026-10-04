brief-base v18 read · brief project v7 read

# REPORT — coldaudit-486 (cold audit of lore finding #486's fix, FINAL patch `50cf81ba`)

## SUMMARY BLOCK
- **VERDICT: NO-GO.** The #486 fix is sound on its own merits: construction 9/9 PASS, mutations **5/5 PROOF HELD**, census delta **0**, **0** reds added vs pristine HEAD. Two items block a clean GO:
  - **(1) #534 (MEDIUM, patch-caused):** a session that only mints a NAME crashes in `pytest_sessionfinish` when the TEST store is unreachable. The tests pass, then rc 1, a raw traceback, and **no passed-count line** (§7, 4-cell construction with controls).
  - **(2) The brief's "RED_ORPHANED 0" fails:** pytest has **1 orphan**, the whole-tree-clone pin. It is **NOT #486's**: it is red on pristine HEAD, caused by `test_am37_13_3_63c_i_a.py` since `34d0b6b` (#536).
  - If the operator rules (1) a pinned bound and the lead registers (2), the patch is otherwise GO.
- **State:** done-with-deviations.
- **Deviations:**
  - The gate discarded the full suite's tail, so no passed-count exists for it (#535). Instead I ran the 37 registry-owned + owed files TWICE (patched vs pristine HEAD). That is targeted, not a second full suite.
  - I removed 2 test-store strays that MY pristine-HEAD control run created (§A.3).
  - Mutation (c)'s replacement was aligned to its declared set before any run (§2).
- **Packages considered:** none — no mechanism specified (audit; instruments are stdlib `ast`/`xml` + the SDK, pasted §A).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none (0 new repo symbols; instruments pasted, not committed).
- **Graded:** patch `50cf81ba` over `38fd413` · HEAD-at-report: `38fd413` · SAME.
- **Decisions needed:**
  - (D1) #534: fix now in a small implementer wave (my recommendation: the fix is a session-level opened-set plus a loud unreachable-store line), or rule it a pinned bound.
  - (D2) #536: register an owner in `pending_contracts.yaml`, or fix it before close-out.
- **Receipts:** §1 construction · §2 mutation table · §3 currency verbatim + §3a orphan attribution + §3b targeted/HEAD-diff (replay test PASSED; 9c88779 trio 139/30/216 passed, 0 failed) · §4 census 75→75 · §5 ruff GREEN, typecheck 83 (all registry-owned, 0 in patch files) · §6 NL sweep · §7 #534 · RESIDUAL TABLE · §A instruments.

## Capability check (brief-base §4)
- grep/rg hook-blocked (#473): every textual scan used awk or a Python-AST instrument (grep case (b), non-symbol textual seams). Said here once; each instrument is pasted where used.
- lore loaded (`ToolSearch "+lore"`); used for `lore_findings get 486`, `lore_comms register/heartbeat`. Structure reads were of the files the brief names, read from disk in the audited scratch tree (the patch is uncommitted, so the lore index cannot see it — #125).
- Nothing the brief demanded was out of reach.

## §0 Trees and provenance (measured 2026-10-04 ~17:40Z, HEAD `38fd413`)
- Audit tree `S` = `<my scratchpad>/audit486`, mutation tree `M` = `<my scratchpad>/mut486`, both via
  `./scripts/scratch_copy.sh` (exit 0), then `git reset --hard HEAD && git clean -fd` → `git status --short`
  printed nothing → patch applied.
- Patch `486-FINAL.patch` md5 **`50cf81ba5a1df975bdf0264f06be068d`** (matches the brief), `git apply --stat`:
  **28 files changed, 1941 insertions(+), 93 deletions(-)**, all under `loremaster/tests/`.
- `loremaster.__file__` in S: `<my scratchpad>/audit486/loremaster/loremaster/__init__.py`; in M:
  `<my scratchpad>/mut486/loremaster/loremaster/__init__.py` (both inside their own tree; scratch_copy also
  asserted loresigil/lorescribe/lorerunes inside S).
- The main tree's 28 working files are byte-identical (`cmp`) to S after the patch, so what is graded here is
  what the lead will commit.

## §1 By construction (read in S, patch applied over `38fd413`; cited by symbol)
| # | Property | Verdict | Receipt |
|---|---|---|---|
| 1a | `_surreal_harness.run` routes through `_run_under_store_retry_seam` | PASS | `run`'s body is an inner `_statement()` handed to `_run_under_store_retry_seam(_statement, label=_RUN_STATEMENT_LABEL, url=url)`. |
| 1b | …and takes the seam's CLASSIFICATION (no local matcher) | PASS | The seam helper's `_attempt` catches `_txn._CONNECTION_ERRORS` and asks `_txn.is_retryable_conflict_error` (typed `details.kind` via `_is_retryable_conflict_kind`), raising `RetryableConflictSignal` into `_txn.retry_on_conflict`. An awk over `_surreal_harness.py` for `retried / resource busy / _retryable / conflict_kind / except` finds no local matcher: only the seam's own imports, docstrings, and the unrelated `call_until_ok` recovery probe (`except healable_errors`). Mutation (a) and the re-keyed KIND pin prove it by execution (§2). |
| 1c | `unique_database` records each mint | PASS | `_MINTED_DATABASES[name] = (PYTEST_CURRENT_TEST or "", False)` before return. Mutation (d), §2. |
| 1d | the reaper reads `INFO FOR NS` through `governed.map_of` (fail closed) and marks reaped entries | PASS | `reap_minted_databases`: `map_of(info, noun="test-namespace reaper", required=("databases",))`; after each successful `_remove_database_with_retry` it re-binds the entry to `(minted_by, True)`. The reader DB is itself minted and dropped in `finally`. Mutations (b), (c), §2. |
| 1e | `conftest.pytest_sessionfinish` reports EVERY reaped/leaked DB with its leaking test, regardless of mid-session reaps (D-r2-1) | PASS | The report is built from the REGISTRY (`… for database, (minted_by, reaped) in _MINTED_DATABASES.items() if reaped`), never from the last reap's return. xdist: worker → `workeroutput[_LEAK_REPORT_WORKEROUTPUT_KEY]` (JSON) → controller `pytest_testnodedown` merge → `pytest_terminal_summary` prints one `LEAKED test database <db> (minted by <test>)` line each; exitstatus OK → TESTS_FAILED. Mutation (b2), §2. No exemption mechanism exists (D-r2-1 absolute): the round-1 deliberate leak now lives in an inner session (`_INNER_REAPER_DIRECT_TEST`). |
| 1f | no new harness module-level name after round 1 (D-r2b-1) | PASS | AST diff of module-level bindings, HEAD vs patched: harness **added `['_MINTED_DATABASES', '_RUN_STATEMENT_LABEL', 'reap_minted_databases']`, removed `[]`**. These are exactly the round-1 contract's allowlisted three (stub-486); round 2 added none. `test_the_harnesss_module_level_names_are_exactly_the_allowed_set` is the standing pin. Conftest gained 8 names (`_DATABASES_OPENED_THIS_TEST`, `_LEAK_REPORT_WORKEROUTPUT_KEY`, `_REAPED_LEAKS`, the autouse fixture, `_record_database_selection`, three hooks); D-r2b-1 allowed conftest. |
| 1g | the census oracle fails closed | PASS | `test_harness_database_lifecycle_486._databases_in_the_test_namespace` reads via `map_of(..., required=("databases",))`; `TestTheCensusOracleFailsClosed` has 7 shape cells plus a live control. |
| 1i | (adversarial) can a mid-session OUTER reaper call remove a still-live higher-scoped fixture's DB? | PASS (no such caller / fixture) | The only outer-session callers of `reap_minted_databases` are `TestTheReaperFailsLoudOnANamespaceAnswerItCannotRead` (INFO is faked, so nothing is removed) and `conftest.pytest_sessionfinish`. An AST scan finds **no** non-function-scoped fixture touching `unique_database` / `connect_admin` / `make_env` / slug / `build_app_context` in `loremaster/tests` (instrument §A.2). |
| 1h | producer-side fix at `test_comms_wiring._open_context` | PASS | The slug is now `unique_database()`. A failed `build_app_context` drops the DB before re-raising. `context.aclose` is shadowed by an instance attribute that closes and then drops the DB in `finally`, so borrowers (`test_mcp_server.py`) inherit the cleanup. |

## §2 Mutations (tree M; `scripts/mutation_proof.py`; declared sets fixed BEFORE any run)
- **Declaration:** expected-RED node ids were taken from `pytest --collect-only -q -p no:randomly` over `test_surreal_harness.py` + `test_harness_database_lifecycle_486.py` (114 collected). They were written to per-mutation files at **2026-10-04T17:43:21Z**, md5-locked, and `md5sum -c` was still OK after the runs. The mutation logs are stamped 18:09:16–18:09:52Z. Each set was derived by reading the pins' code (§A.5 lists the selectors).
- ⚠ **Disclosed adjustment, made before any mutation run:** my first draft of (c)'s replacement was `set(info.get(key) or {})`. That would also coerce `databases: None`, while my declared set (modelled on the pre-round-2 code's `info.get("databases", {})`, under which `set(None)` raises) excludes `databases-none`. At 17:45Z I changed the REPLACEMENT to the pre-round-2 shape, so that it matches the declaration. The declaration itself was not touched.
- **Control (unmutated M, same scope):** `114 passed in 7.74s`, rc 0. Satisfiability over this scope holds.
- Every run used `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:randomly`. Every run waited for a pytest-free process table and MemAvailable ≥ 20 GiB (0 min waited). Each mutated file was `cp -a`'d first and `cmp`'d after restore.

| # | Mutation (exact anchor → replacement in §A.5) | Scope | Declared RED | Tail | Tool verdict | Restore |
|---|---|---|---|---|---|---|
| a | `run` bypasses the seam: `return await connection.query(statement, params)` | H+L | 6: ceiling[run], deadline[run], `test_run_detection_follows_the_seams_one_conflict_kind`, `test_a_once_conflicting_statement…`, `test_sustained_conflict_exhausts…`, the reach pin | `6 failed, 108 passed` | **PROOF HELD — exact, both ways** (the reach pin named `run:253 -> .query` and `_statement:248 -> .query`) | md5 `aaf41b8f…` byte-exact; `cmp` OK |
| b | the reaper stops marking: `(minted_by, _already_reaped)` | H+L | 5: `TestALeaked…[n0]`, `[xdist-n2]`, `TestAMidSession…[n0]`, `[xdist-n1]`, `…CONTROL_the_same_leaks_with_no_mid_session_reap…` | `5 failed, 109 passed` | **PROOF HELD** (inner session rc 0, no report line: the false clear) | byte-exact; `cmp` OK |
| b2 | the report reads only the LAST reap's return (conftest) | H+L | 2: `TestAMidSession…[n0]`, `[xdist-n1]` (the end-only-leak legs and the CONTROL must stay GREEN) | `2 failed, 112 passed` | **PROOF HELD** | conftest md5 `f2024e35…` byte-exact; `cmp` OK |
| c | the reaper's INFO read made tolerant: `set(info.get(key, {})) if isinstance(info, dict) else set()` | H+L | 6: every `test_an_unreadable_namespace_answer…` param except `databases-none` | `6 failed, 108 passed` | **PROOF HELD** | byte-exact; `cmp` OK |
| d | `unique_database` stops recording (`pass`) | L | 27: every lifecycle test except the naming-lint class and the docstring pin. Every one opens a test-namespace DB in the outer process, so the provenance guard must fail it. | `16 failed, 25 passed, 26 errors` (the errors are guard teardown failures) | **PROOF HELD** | byte-exact; `cmp` OK |

- **Reading:** (a) proves CLASSIFY-AND-SIGNAL is the seam's at `run` (ROUTING IS NOT SHARING executes). (b) and (b2) each kill a DIFFERENT wrong F2 fix, and (b2) leaves the end-only legs green, which proves the fixture discriminates. (c) proves the F3 fail-closed read is load-bearing. (d) proves the registry is load-bearing for the guard, the reaper AND the report at once: a build that forgets to record fails loudly everywhere, never quietly.
- **Not tried:** a mutation of the xdist `workeroutput` crossing alone (e.g. the controller ignoring `pytest_testnodedown`). The `[xdist-n2]`/`[xdist-n1]` legs exist and reddened under (b)/(b2), but no mutation isolated the crossing. Residual R6.

## §3 THE ONE FULL SUITE (this packet's)
- **Pre-flight (2026-10-04T17:41Z):** process table had **0** pytest processes. MemAvailable was **20.4 GiB** (≥20 required). Fleet wait: 0 min. Memory wait: 0 min.
- **Command (in S):** `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python scripts/pending_contract_gate.py --currency -- --maxprocesses=12`. The gate's resolver rendered `-n auto` (the #508 bound: no other session was live), capped by the forwarded `--maxprocesses=12` → 12 workers. Its own pytest argv, read off the process table: `pytest -q -o junit_family=xunit1 --junit-xml=/var/tmp/tmp16fp_1dp/junit.xml --maxprocesses=12 -n auto`.
- **Resources:** cgroup `MemoryPeak` sampled at **8,160,722,944 B (7.6 GiB)** mid-run. No cap kill; the scope exited on its own.
- **Wall-clock:** ~17:41Z → 17:54:02Z (~13 min).
- **Currency output, verbatim except one marked elision of the registry's owner/trigger prose (`EXIT=1`):**
```
========================================================================
GATE CURRENCY — is every CLAIMED gate green, or owned?
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract (owner: packet 58 (supersede re-anchor + task guarded-append shell + finding 130 + amendments 1-8) — the 58 builder, serial after 63c-i-a; trigger: …[owner/trigger prose elided here; it is the registry text of scripts/pending_contracts.yaml entries packet-58-contract and packet-64b-i-contract, verbatim in the gate output]…)
  ruff         GREEN
  pytest       RED_ORPHANED — 1 residual(s) with NO owner
      ORPHAN: loremaster/tests/test_ast_reach_helpers.py :: loremaster.tests.test_ast_reach_helpers.TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist::test_no_unallowlisted_whole_tree_parser_clone_survives
CURRENCY   : FAIL — RED with nobody's name on it: pytest
  (this is NOT the deploy receipt: it answers 'is every gate owned', never 'may this ship')
EXIT=1
```
- ⚠ **What this run could NOT give, and why (instrument friction, filed §F):** `pending_contract_gate.py` runs pytest with `stdout=PIPE` inside a `TemporaryDirectory`, and it renders only the currency partition. The pytest tail (the passed count), the terminal summary (the session's own `LEAKED test database …` lines) and the junit were all discarded at exit (`/var/tmp/tmp16fp_1dp/` no longer exists). Also, when a gate has ANY orphan, `GateCurrency.render` prints only the orphan count and hides the adjudicated count. So **no passed-count exists for this full suite.** Re-running the full suite to recover them would be a second full suite in one packet, which CLAUDE.md forbids. I recovered the brief's specific asks by a TARGETED run instead (§3b).

### §3a The orphan red — NOT attributable to #486
- `_whole_tree_clone_offenders()` evaluated in S → `{'test_am37_13_3_63c_i_a.py': ['_row_reader_owner_classes', '_shape_reader_call_sites', 'test_the_row_reader_wrappers_require_noun']}`.
- `test_am37_13_3_63c_i_a.py` is **not in the patch** (it is not one of the 28 files). The two helper defs are present in that file at every commit that touches it: `34d0b6b`, `f47724a`, `28395e0`, `b90bd4b`, `9c88779` (2 of 2 defs at each, via `git show <sha>:… | awk`). Nor does the patch touch `test_ast_reach_helpers.py`. ⇒ **pre-existing at HEAD `38fd413`, introduced by 63c-i-a (`34d0b6b`)**. It is red with no registry entry, so the lead's owed 9c88779-family verification finds an orphan here (§3b).

### §3b Targeted recovery run — the brief's specific asks (S, 2026-10-04 ~18:00Z)
- **Scope, and how it was derived:** 37 files. They are every `path` in `scripts/pending_contracts.yaml` (32 files: the gate silently absorbs reds in these, so a guard/leak red there would be invisible in §3), plus `test_memory_replay_fidelity_63b_ib.py`, the 9c88779 trio (`test_am37_13_3_63c_i_a.py`, `test_principal_keys_store.py`, `test_principals_cli.py`) and `test_ast_reach_helpers.py`. Pre-flight: 0 pytest processes, MemAvailable 30.5 GiB.
- **Command:** `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -rfE -o junit_family=xunit1 --junit-xml=<scratch>/targeted.xml <37 files>`.
- **Tail:** `531 failed, 1756 passed, 6 skipped, 3 warnings in 362.31s (0:06:02)`, EXIT=1.
- **Partition (junit, per file):** every red is in a registry-owned file, **except one**: `test_ast_reach_helpers.py` (49 passed, 1 failure). That failure is the §3a orphan. **No red is in a non-registered file other than that one.**
- **The originally-flaky `TestTheReplayCloseIsPairGuarded::test_a_cross_owner_replay_close_is_skipped_with_a_warning`: PASSED** (file: 12 passed / 0 failed). One run under `-n 8` beside 36 other files bounds nothing about rarity (#486 itself was 1-in-a-full-suite). The by-construction fix (§1a/b) plus mutation (a) (§2) is the evidence, not this green.
- **9c88779 owed verification:** `test_am37_13_3_63c_i_a.py` **139 passed / 0 failed**; `test_principal_keys_store.py` **30 passed / 0**; `test_principals_cli.py` **216 passed / 0**. The one 63c-i-a-family red is the §3a orphan, which the am37 file CAUSES (it is the clone offender), although the red itself is reported by `test_ast_reach_helpers.py`.
- **The "opened a database it didn't mint" guard and the leak report over this scope:** `NOT minted by` lines in the log = **0**; `LEAKED test database` lines = **0**. That includes `test_mcp_server.py` (638 passed / 28 registry-owned failures), the borrower whose leak the producer-side fix closes.
- **Attribution control (pristine HEAD):** a third tree `B` (`scratch_copy.sh`, clean, HEAD `38fd413`, NO patch; `loremaster.__file__` inside B) ran the identical 37-file command. Result: `531 failed, 1756 passed, 6 skipped, 3 warnings in 361.13s`. **Red-set diff by junit node id, patched vs HEAD: `[]` both ways; collected sets equal.** The patch adds and removes no red across the registry-owned files and the owed-verification files. **The §3a orphan is red on pristine HEAD too**, which settles that it is not #486's.
- **The same question over the WHOLE suite, by derivation (§3):** the pytest leg's only unowned red was the clone pin, so the guard raised **no** red in any non-registered file across the full suite. Registered files are covered by this targeted run. The full suite's own `LEAKED` lines were discarded by the gate and cannot be reported (§3, ⚠).

## §4 Leak census — TEST store `ws://127.0.0.1:18000`, namespace `lore_test` only
- **Instrument:** my own census, independent of the harness under audit, pasted verbatim in §A.1. It reads `USE NS lore_test; INFO FOR NS;` through `query_raw`, selecting no database, so it creates nothing. It refuses any URL other than `:18000`.
  - **Negative control:** two back-to-back runs gave identical sets, and each run's re-read was equal.
  - **Positive control:** `DEFINE DATABASE coldaudit486_ctl` → census 76. `REMOVE` → 75.
- **BEFORE** (17:41Z, immediately before the gate): `{"total": 75, "harness_shaped": 13, "harness_live_pid": 0, "bare_hex32": 60, "other": ["test_probe_unused", "x"]}`
- **AFTER** (17:55Z, immediately after the gate exited): `{"total": 75, "harness_shaped": 13, "harness_live_pid": 0, "bare_hex32": 60, "other": ["test_probe_unused", "x"]}`
- **Set diff: added `[]`, removed `[]`. Delta = 0.** The 75 pre-existing strays are dead-pid / bare-hex / two named probes, untouched (the reaper never touches another process's DBs — consistent with §1d).
- This is a STATE check, so it also covers databases the per-test guard cannot see: higher-scoped fixtures, a raw `DEFINE DATABASE <name>`, a foreign name that the guard failed but nothing reaped. **The full suite left no database behind, by any door.**
- **Session-end `LEAKED` lines:** for the full suite, they are not recoverable (§3 ⚠). For the targeted §3b run (37 files, including `test_mcp_server.py`), **0**.
- **Bound:** the delta cannot distinguish "no leaks" from "leaks reaped at session end". Only the discarded `LEAKED` lines could. A reaped leak is a test-hygiene defect, not a store leak; the store invariant itself holds.

## §5 Gates (S, after the full suite)
- `uv run ruff check .` → `All checks passed!`, rc 0. The gate's ruff leg also reported GREEN.
- `./scripts/typecheck.sh` → rc 1. lorerunes, lorescribe, loresigil, skills and docs/eval are OK. `loremaster`: **82 errors in 31 files**. `scripts`: **1 error in 1 file**. shellcheck OK.
  - That is **83** total, all in the 32 registry-owned files (largest: `test_governed_substrate_64b.py` 12, `test_supersede_reanchor_58.py` 7).
  - **None of the 28 patch files carries a type error** (each checked against the error-file list).
  - It matches the gate's `typecheck RED_ADJUDICATED — 83 residual(s)` (packet-58-contract + packet-64b-i-contract).

## §6 Natural-language sweep of the patch's added prose (file:line in S after the patch; symbol given)
Method: an awk over the patch's `+` lines in the four substantive files, filtered for claim-bearing tokens (numbers, quantifiers, RED/GREEN-at-HEAD). Then each claim was checked against the code or a measurement. The 23 one-line converted sites were read in full; their only prose change is `test_startup_divergence_reconcile._slug`'s docstring.
| file:line (symbol) | claim | verdict |
|---|---|---|
| `_surreal_harness.py:22-30` (module docstring, "Lifetime") | every mint recorded; session-end reap removes this process's survivors loudly; "a session that ends normally leaves none of its own databases behind"; killed sessions are a stated bound (D2) | **TRUE**: §1c/d/e, census delta 0 (§4) |
| `_surreal_harness.py:47-50` (module docstring, seam paragraph) | `run`'s statement, teardown `use()` and REMOVE all go through the seam; pinned by mutation | **TRUE**: §1a, mutation (a) |
| `_surreal_harness.py:139-141` (`_RUN_STATEMENT_LABEL` comment) | distinct from both teardown labels | **TRUE**: asserted in `test_sustained_conflict_exhausts_with_the_seams_type_and_an_attributable_record` |
| `_surreal_harness.py:166-172` (`_MINTED_DATABASES` comment) | value is `(node id, reaped)`; reaped entries kept; "mutated IN PLACE, never rebound" | **TRUE**: the only binding is the definition at :173 (awk over harness, conftest and the lifecycle file) |
| `_surreal_harness.py:181-186` (`unique_database` docstring) | recorded so the reap can name, and provenance can refuse | **TRUE** |
| `_surreal_harness.py:238-245` (`run` docstring) | conflict retried with the same params; other errors untouched on the first attempt; exhaustion attributed to `_RUN_STATEMENT_LABEL` | **TRUE**: `TestRunRidesTheStoreRetrySeam` (4 pins) |
| `_surreal_harness.py:652-658` (`_run_under_store_retry_seam` docstring) | "the reach pin fails on ANY engine-door use in this module outside an attempt body handed here" | **IMPRECISE (LOW)**: the pin exempts `measure_store_traffic` (`test_surreal_harness._REACH_EXEMPT_FUNCTIONS`), whose forwarded calls ARE door uses outside an attempt body. The exemption and its reason are stated in the TEST, not here. Fix: "…outside an attempt body handed here, except the one exempt forwarding instrument named in `_REACH_EXEMPT_FUNCTIONS`". |
| `_surreal_harness.py:675-679` (`operation` arg doc) | multi-statement `run` strings are the caller's to make re-runnable | **TRUE** as a stated bound. Note: a retried multi-statement string whose first statement committed fails LOUD (non-retryable "already exists"), never silently. |
| `_surreal_harness.py:874-893` (`reap_minted_databases` docstring) | touches only this process's recorded DBs; marks reaped; returns only removed leaks; raises `SurrealStoreError` on an unreadable INFO | **TRUE**: §1d, mutation (b)/(c), census "other"/dead-pid strays untouched |
| `_surreal_harness.py:906` (comment) | "a bare `use()` CREATES one (measured 2026-09-26, 3.2.4)" | **TRUE**: dated. My census avoided exactly this by not selecting a database (§A.1) |
| `conftest.py:241-256` (block comment) | "the one door every test database passes through is the connection's session selection" | **IMPRECISE (LOW)**: a raw `DEFINE DATABASE <name>` statement creates a database with no `use()`. No live test does this: an awk over `loremaster/tests` finds `DEFINE DATABASE` only in fakes, scan fixtures and docstrings. The state check (§4) would catch it anyway. The bound should be added to the BOUNDS list beside "higher-scoped fixture". |
| `conftest.py:252` | "a higher-scoped fixture's `use()` is unobserved (none mints a database today)" | **TRUE**, measured: an AST scan found 0 non-function-scoped fixtures touching a DB name (§A.2) |
| `conftest.py:271-273` (`_record_database_selection`) | records and never raises | **TRUE** |
| `conftest.py:296-299` (fixture docstring) | "the source of the 2186 `test_<hex32>` databases found in `lore_test`" | **UNDATED COUNT (LOW)**: contract-486 M2, measured 2026-09-26. On 2026-10-04 the namespace holds 60 bare-hex DBs (§4). It should read "(2186 measured 2026-09-26, contract-486 M2)". |
| `conftest.py:315-321, 326-328` (`pytest_sessionfinish`) | report from the registry, not the last reap; worker → controller | **TRUE**: mutation (b2), xdist legs |
| `test_comms_wiring.py:165-170` (`_open_context`) | the context owns and drops its DB; "that gap leaked one database per borrowed call in `test_mcp_server.py`" | **TRUE / ACCEPTED**. The ownership is code-verified (§1h). The historical leak rate is implement-486's measurement, consistent with §3b (0 guard/leak lines over `test_mcp_server.py`) and §4. |
| `test_startup_divergence_reconcile.py` `_slug` docstring | the slug is minted by `unique_database()`, recorded, reaped, provenance-accepted | **TRUE** |
| `test_surreal_harness.py:84, 1579, 1584, 1618, 1628, 1637` (`TestRunRidesTheStoreRetrySeam` prose) | "812 call sites", "38 call sites sit inside `pytest.raises`" | **UNDATED COUNT (LOW)**: contract-486, 2026-09-26 at `e039c64`. Re-derived 2026-10-04 at `38fd413` + patch by AST (§A.3): **873** `run(` call sites, **42** inside a `pytest.raises` `with`. The new count includes the patch's own new tests, so drift is expected. Date it, or drop the number. |
| `test_surreal_harness.py:87` (module docstring) | cites `REPORT-investigate-486.md` at `081782e` | **CITATION FORM (LOW)**: SHA-pinned, so recoverable, but a bare root `REPORT-*.md` cite (brief-base §1). Rewrite to the archived `docs/plans/v2/receipts/<date>-<packet>/` path when the lead archives the 486 reports. |
| `test_surreal_harness.py:1535-1547` (KIND pin docstring) | `_RETRYABLE_CONFLICT_MARKER` deleted by `34d0b6b`; re-keyed to KIND; "839/0" | **TRUE**: `_txn` exposes `_RETRYABLE_CONFLICT_KIND`. 839/0 matches CLAUDE.md's #102 receipt. |
| `test_surreal_harness.py:2004-2013` (exemption comment) | `measure_store_traffic` forwards, originates no statement; threat model stated | **TRUE**: read `measure_store_traffic`. The threat model is written into the instrument, per CLAUDE.md. |
| `test_harness_database_lifecycle_486.py:308-312` (F4) | "the harness keeps no prefix constant" | **TRUE**: no harness module-level name holds `"test_"` (§1f name set) |
| `test_harness_database_lifecycle_486.py:808-811, 819-820` (prose-486 edits) | value `(minted_by, reaped)` | **TRUE** |


## §7 NEW DEFECT — a store-free session crashes at session end (patch-caused; finding **#534**)
- **Property violated (lifted):** *a pytest session whose tests pass, and which opened no test database, must end with pytest's own verdict and summary — whatever the state of the TEST store.* The reaper's stateful dependency (the store) was never constructed in the **unreachable** state. That is trust-doctrine Leg 2: dependencies × {unreachable, partial}.
- **Construction (2026-10-04 ~18:12Z, probe pasted in §A.4):** a 2-test file, one test calling `unique_database()` for a NAME only, run as `pytest -c /dev/null -p conftest` (the lifecycle contract's inner-session wiring):

| tree | `LORE_TEST_SURREAL_URL` | tests run | rc | tail |
|---|---|---|---|---|
| **patched (S)** | `ws://127.0.0.1:1` (dead) | both | **1** | `..` then a **raw `ConnectionRefusedError` traceback out of `wrap_session → pytest_sessionfinish`**; **no `2 passed` line** |
| pristine HEAD (B) | dead | both | 0 | `2 passed in 0.64s` |
| patched (S) | live `:18000` | both | 0 | `2 passed in 0.65s` |
| patched (S) | dead | `-k mints_nothing` (no mint) | 0 | `1 passed, 1 deselected` |

- **Why it reaches real runs:** the patch converted ~25 slug sites to `unique_database()`, several inside fake-store test files (e.g. `test_indexer.py`, `test_watcher.py`, `test_reconcile.py` `_config` slugs). `_run_inner_session` also mints directory names. So any targeted store-free run with the store down now crashes after green tests, and its tail carries **no passed count**: the exact shape CLAUDE.md warns reads as ambiguous. It is LOUD (rc 1), so not a false clear. But it destroys the verdict line, and it is a regression against HEAD.
- **Severity: MEDIUM** (my judgement). This dev host's store auto-starts, so it rarely fires here. It WILL fire on any host or container without the TEST store. **Re-open trigger for the bound if not fixed:** packet 01a's in-image conformance run, if its container cannot reach `:18000`.
- **Fix direction (a property, not a prescription; the fix belongs to an implementer):** reap only what this process actually OPENED (the `use()` observer already sees every opened name; it would need a session-level set beside the per-test list). And report an unreachable store at reap time as its own LOUD line, without replacing pytest's summary or exit semantics. Pin it with this probe's four cells: the dead-URL name-only cell must END with the passed-count line.

## RESIDUAL TABLE
| # | Class (lifted) | Severity | Owner | Trigger / next decision |
|---|---|---|---|---|
| R1 | **#534** — session-end reap requires a live store for name-only sessions; crash hides the verdict (§7) | MEDIUM, patch-caused | #486 (fix wave: implementer, then a re-audit of the reap path) | **Blocks GO** unless the operator or lead rules it a pinned bound (then: pin the miss, with trigger = 01a in-image run) |
| R2 | **#536** — `test_am37_13_3_63c_i_a.py` whole-tree clone; currency `RED_ORPHANED` (§3a) | gate-blocking, NOT #486's (red on pristine HEAD) | 63c-i-a packet (`34d0b6b`) | Lead: register it in `scripts/pending_contracts.yaml` with an owner and trigger, or route the migration/allowlist fix. The currency gate FAILS at every close-out until then. |
| R3 | **#535** — the currency gate discards the full suite's pytest tail, junit and terminal summary, and hides the adjudicated count when orphaned (§3 ⚠) | instrument friction, trust-relevant | `scripts/pending_contract_gate.py` maintainers | Until fixed, every cold audit must re-run the registry-owned files to see absorbed reds. Suggested `--keep-artifacts` + always render `registered_count`. |
| R4 | Prose imprecisions (§6): the seam docstring omits the `measure_store_traffic` exemption; the conftest "one door" omits raw `DEFINE DATABASE`; undated counts (2186; 812/38 → re-derived 873/42); bare `REPORT-investigate-486.md` cite | LOW | #486 (can ride the R1 fix wave) or the archiving lead (citation) | None blocking; fix when touching the files |
| R5 | Killed sessions never reap (stated bound, operator ruling D2); 75 strays of dead pids / bare-hex / probes sit in `lore_test` today (§4) | accepted bound | operator (periodic wipes) | D2's own trigger |
| R6 | No mutation isolates the xdist `workeroutput` → `pytest_testnodedown` crossing (§2 "not tried") | LOW | contract owner, if wanted | Only if the xdist path is reworked |
| R7 | F5 (refactor-486): the naming lint keys files by bare filename | LOW, ledgered by the lead | lead | Two same-named test files |
| R8 | The originally-flaky replay test passed once under load (§3b); a single green bounds nothing about rarity | info | — | The by-construction fix + mutation (a) is the evidence. Re-open if a raw `can be retried` `QueryError` ever reaches a test again. |

## §A Instruments (pasted verbatim per brief-base §1)
### §A.1 Leak census (independent of the harness; TEST store only)
```python
"""coldaudit-486 leak census (independent of the harness under audit).

Counts databases in the TEST store's lore_test namespace by shape. Reads through a
query-level `USE NS` (no database selected) so the census itself creates nothing;
the reader proves that by reporting the total twice (before/after its own read).
TEST store only: refuses any URL that is not ws://127.0.0.1:18000.
"""
import asyncio, json, os, re, sys
from surrealdb import AsyncSurreal

URL = "ws://127.0.0.1:18000"
assert os.environ.get("LORE_SURREAL_URL", URL).endswith(":18000"), "TEST store only"
USER = os.environ.get("CENSUS_USER", "root")
PASS = os.environ.get("CENSUS_PASS", "root")
NS = "lore_test"
HARNESS = re.compile(r"^test_(\d+)_[0-9a-f]{32}$")
BARE = re.compile(r"^test_[0-9a-f]{32}$")


async def read_names(connection) -> set[str]:
    raw = await connection.query_raw(f"USE NS {NS}; INFO FOR NS;")
    statements = raw.get("result") if isinstance(raw, dict) else None
    if not isinstance(statements, list) or len(statements) != 2:
        raise SystemExit(f"census: unexpected raw shape: {str(raw)[:300]}")
    info = statements[1].get("result")
    if not isinstance(info, dict) or not isinstance(info.get("databases"), dict):
        raise SystemExit(f"census: unexpected INFO FOR NS shape: {type(info)} {str(info)[:200]}")
    return set(info["databases"])


async def main() -> None:
    connection = AsyncSurreal(URL)
    await connection.signin({"username": USER, "password": PASS})
    first = await read_names(connection)
    second = await read_names(connection)
    await connection.close()
    pids = {}
    for name in first:
        match = HARNESS.match(name)
        if match:
            pids.setdefault(int(match.group(1)), []).append(name)
    live = {pid for pid in pids if os.path.exists(f"/proc/{pid}")}
    out = {
        "total": len(first),
        "total_reread": len(second),
        "harness_shaped": sum(len(v) for v in pids.values()),
        "harness_live_pid": sum(len(pids[p]) for p in live),
        "bare_hex32": sum(1 for n in first if BARE.match(n)),
        "other": sorted(n for n in first if not HARNESS.match(n) and not BARE.match(n))[:40],
        "other_count": sum(1 for n in first if not HARNESS.match(n) and not BARE.match(n)),
    }
    print(json.dumps(out))
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w") as handle:
            json.dump(sorted(first), handle)


asyncio.run(main())
```
Run as `CENSUS_PASS=spikeroot uv run python census.py [names.json]`. Positive control: `USE NS lore_test; DEFINE DATABASE coldaudit486_ctl;` → total +1; `REMOVE DATABASE IF EXISTS coldaudit486_ctl` → back.

### §A.2 AST scans: `run()` call sites, and higher-scoped DB fixtures
```python
import ast, pathlib
root = pathlib.Path("loremaster/tests")
calls = 0; raises_calls = 0
scoped = []
for p in sorted(root.rglob("*.py")):
    t = ast.parse(p.read_text())
    run_names = {a.asname or "run" for n in ast.walk(t) if isinstance(n, ast.ImportFrom) and n.module == "_surreal_harness" for a in n.names if a.name == "run"}
    for n in ast.walk(t):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in n.decorator_list:
                if isinstance(d, ast.Call):
                    for kw in d.keywords:
                        if kw.arg == "scope" and isinstance(kw.value, ast.Constant) and kw.value.value != "function":
                            body = ast.unparse(n)
                            if any(k in body for k in ("unique_database", "connect_admin", "make_env", "_slug(", "slug", "SurrealStore", "build_app_context")):
                                scoped.append(f"{p}:{n.lineno} {n.name} scope={kw.value.value}")
    def visit(node, in_raises=False):
        global calls, raises_calls
        if isinstance(node, (ast.With, ast.AsyncWith)):
            r = any(isinstance(i.context_expr, ast.Call) and ast.unparse(i.context_expr.func).endswith("raises") for i in node.items)
            for c in ast.iter_child_nodes(node): visit(c, in_raises or r)
            return
        if isinstance(node, ast.Call):
            f = node.func
            if (isinstance(f, ast.Name) and f.id in run_names) or (isinstance(f, ast.Attribute) and f.attr == "run" and isinstance(f.value, ast.Name) and f.value.id in ("_surreal_harness", "harness")):
                calls += 1
                if in_raises: raises_calls += 1
        for c in ast.iter_child_nodes(node): visit(c, in_raises)
    visit(t)
print("run() call sites:", calls, "inside pytest.raises:", raises_calls)   # -> 873 / 42
print("\n".join(scoped) or "none")                                            # -> none
```
§1f's module-level-name diff used the same `ast` walk over top-level `Assign`/`AnnAssign`/`def`/`class` of `git show HEAD:<file>` vs the patched file.

### §A.3 Red-set attribution (patched S vs pristine HEAD B, same 37 files)
Both trees ran `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -rfE -o junit_family=xunit1 --junit-xml=<x>.xml <files>`. The file list is every `files[].path` in `scripts/pending_contracts.yaml`, plus the replay file, the 9c88779 trio and `test_ast_reach_helpers.py`. Then:
```python
import xml.etree.ElementTree as ET
def reds(p):
    out, allids = set(), set()
    for tc in ET.parse(p).iter("testcase"):
        i = tc.get("classname") + "::" + tc.get("name"); allids.add(i)
        if any(ch.tag in ("failure", "error") for ch in tc): out.add(i)
    return out, allids
pr, pa = reds("targeted.xml"); br, ba = reds("base.xml")
print(len(pr), len(br), sorted(pr - br), sorted(br - pr), len(pa - ba), len(ba - pa))  # -> 531 531 [] [] 0 0
```
Side-effect receipt: the pristine-HEAD run left **2** bare-hex `test_<hex32>` databases carrying the full app-context schema (`agent`, `brief`, `command`, …). That is HEAD's `_open_context` leak through `test_mcp_server.py`, the leak this patch fixes. The patched run of the same files left none, which makes it a discriminating control for §1h. I removed both (`REMOVE DATABASE IF EXISTS`, TEST store only); the census returned to the BEFORE set exactly.

### §A.4 Store-free probe (§7)
```python
"""coldaudit-486 probe: a test that mints a NAME (as converted _slug() sites do for fake-store
tests) but never touches a live store. Run with the harness URL pointed at a dead port."""
from _surreal_harness import unique_database


def test_mints_a_name_only():
    assert unique_database().startswith("test_")


def test_mints_nothing():
    assert True
```
`LORE_TEST_SURREAL_URL=ws://127.0.0.1:1 PYTHONPATH=<tree>/loremaster/tests uv run pytest -p no:cacheprovider -q -c /dev/null --rootdir <probe dir> -o asyncio_mode=auto -p conftest test_storefree_486.py`

### §A.5 Mutation anchors/replacements (exact) and declared-set selectors
- (a) `    return await _run_under_store_retry_seam(_statement, label=_RUN_STATEMENT_LABEL, url=url)` → `    return await connection.query(statement, params)`
- (b) `            _MINTED_DATABASES[database] = (minted_by, True)` → `            _MINTED_DATABASES[database] = (minted_by, _already_reaped)`
- (b2) in `conftest.pytest_sessionfinish`, the 7 lines from `    if _MINTED_DATABASES:` through the closing `)` of `report = sorted(…if reaped)` → `    last_reap = asyncio.run(reap_minted_databases()) if _MINTED_DATABASES else ()` / `    report = sorted((database, _MINTED_DATABASES[database][0]) for database in last_reap)`
- (c) `        namespace = map_of(info, noun="test-namespace reaper", required=(databases_key,))` / `        present = set(namespace[databases_key])` → `        present = set(info.get(databases_key, {})) if isinstance(info, dict) else set()`
- (d) `    _MINTED_DATABASES[name] = (os.environ.get("PYTEST_CURRENT_TEST", ""), False)` → `    pass`
- Selectors over the collect-only list: (a) `follows_the_seams_attempt_ceiling\[run:|follows_the_seams_wall_clock_deadline\[run:|test_run_detection_follows_the_seams_one_conflict_kind$|TestRunRidesTheStoreRetrySeam::test_a_once_conflicting|TestRunRidesTheStoreRetrySeam::test_sustained_conflict|test_every_engine_door_use_in_the_harness_is_an_attempt_body_of_the_seam$`. (b) `TestALeakedDatabaseIsReapedAndReported::test_a_leaked|TestAMidSessionReapNeverSwallowsALeak::`. (b2) `TestAMidSessionReapNeverSwallowsALeak::test_leaks_before_and_between`. (c) `TestTheReaperFailsLoudOnANamespaceAnswerItCannotRead::test_an_unreadable` minus `databases-none`. (d) every `test_harness_database_lifecycle_486.py::` id minus `TestTheTestDatabaseNamingRecipeExistsOnce|TestTheHarnessDocstringClaimsNoReaperItLacks`.
- Driver loop (per mutation): `cp -a <file> <bak>`; wait for a pytest-free table and MemAvailable ≥ 20 GiB; `uv run python scripts/mutation_proof.py --file <file> --anchor-file <x>.anchor --replacement-file <x>.repl --expect-red <id>… -- <capped pytest> <scope>`; `cmp <file> <bak>`.

## Time log
- Start 17:38:47Z. Full suite 17:41–17:54Z. Targeted 37-file run ~17:57–18:03Z. HEAD-baseline run ~18:03–18:09Z. Mutations 18:09:16–18:09:52Z. Probes ~18:12Z. Report ~18:15Z.
- Fleet waits: 0. Memory waits: 0. Well inside the 120-min deadline; nothing in the brief is NOT TRIED except §2's R6.
- ⚠ One self-inflicted process-table false positive: the pre-flight `ps | awk '/[p]ytest/'` before the store-free probe counted **1**. That was my own shell's command line, which contained `pytest`, not another session (the self-match class, brief-base §5 item 5). A re-check right after showed 0, and the probe ran ~1 s.
