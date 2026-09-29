# REPORT — contract-58-r4 (packet 58 contract revision 4: the amendment-12 FOLD, ungraded under the round cap)

## SUMMARY BLOCK
- brief-base v18 read · brief project v7 read
- **State: done-with-deviations** — every am-12 §4 fold item landed (tests only; no production file edited). Base `a77dc00`. SAT, RED@HEAD and mutation receipts are in §SAT / §RED@HEAD / §MUTATION.
- **Deviations** (full text §DEVIATIONS):
  - D-R4-1: the FIRED ledger is asserted per derived `(R, v)` leg, not once per session, because `-n 8` splits a session across processes.
  - D-R4-2: ROOTS are cut at each verb's own module (its same-module reverse call graph), not at the served dispatcher.
  - D-R4-3: six fault admissions were REMOVED (FK-r4-1).
  - D-R4-4: registry symbols are spelled the way mypy names them (`type[FindingLedger]._run_guarded`).
  - D-R4-5: my new/edited files name ruled symbols in `TYPE_CHECKING` so the registry can own them (#461 shape).
  - D-R4-6: F-F (evidence by import) is NOT DONE.
  - D-R4-7: F4 position labels: the bad entry after a single healable one is labelled `bad-middle`.
  - D-R4-8: `_exhaustion_fates.py` was `ruff format`ted.
  - D-R4-9: R-7 landed after the REF leg started; the pure-AST files were re-run in REF mode on the final bytes.
- **Packages considered:** none — no production mechanism specified. This is tests-only. The reference delta `my_ref_r4.py` adds one log `extra` key; BC-r3-1 `more_itertools.constrained_batches` stands, per r3.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 7 new reusable symbols, all dispositioned (§DRY LEDGER).
- **Graded:** n/a — this is authorship, not a verdict. Base read = HEAD `a77dc00`.
- **Decisions needed:**
  - FK-r4-1: removing six admissions under am-11 §2 "exact both ways" — confirm, or re-rule as one-way.
  - FK-r4-2: the lease `error_class` rider is carried by 58's BUILD (the lead's call, restated) — named in BUILDER CONSTRAINTS.
- **Headline receipts:**
  - SAT on the reference: 0 r4-attributable reds (REF `661 failed / 6176 passed`, BASE `850 / 5933`; REF-ONLY 36, all 63c-i-a-owned — ⚠ the 58-class collision flag).
  - 10/10 declared mutations PROOF HELD (M4 on its v2 declaration).
  - ruff clean; typecheck lines are only the ruled symbols.
  - `--verify-registry` OK.
- **Receipt pointers:** §ITEMS · §FORKS · §RED@HEAD · §SAT · §MUTATION · §P1c · §DUAL · §HELD · §RE-BASE · §BUILDER CONSTRAINTS · §INSTRUMENTS

## §0 Capability check (brief-base §4), 2026-09-29
- **Required first reads:**
  - `brief-base.md` v18: read in full.
  - `docs/reference/surrealdb-31-capabilities.md`: read the header, the six facts, §3 (incl. the #497 `RETURN`-in-transaction hazard and #501) and §5. The other sections were NOT read in full; I edited no store, schema or DDL, so none was load-bearing here.
  - CLAUDE.md §Quality gates "TEST SCOPE": read, and it governs everything below. No full suite and no currency gate were run.
- **Tools:**
  - lore tools loaded via `ToolSearch "+lore"`. Registered on `lore_comms` (session `63c-20260924`, cadence `≤20m`).
  - grep is hook-blocked (#473), so code reads went through `awk`/`sed`/Python `ast`. Said out loud here.
  - `lore_impact` covering tests cap at 15 (#518). Measured on `loremaster.store.lease`: `covering_tests_elided: 74`. The targeted set was therefore derived by an AST import scan (`declare_set.py`, §INSTRUMENTS).
  - ⚠ The same `lore_impact` call rendered `loremaster.store.lease` as `verdict: dead (heuristic) · 0 prod references`, but `server.py` wires the lease. This looks like a module-target undercount. **Filed as finding #522.**
- **Deadline:** 90 min from spawn (spawn 20:47:43Z → 22:17:43Z).

## §REQUIRED-GREEN — correct builds the rulings require green (enumerated before the pins)
1. A correct 58 build (the r3 reference chain `build_ref58 → my_ref → my_ref_am6 → my_ref_r3`) plus the four-line lease rider (`my_ref_r4.py`) must be green on every r4 pin. The only exceptions are reds owned by 63c-i-a or 64b-i (§SAT).
2. A heal that is called BY NAME from the boot (`ensure_ready → _backfill_blocks_edges → _reanchor_stragglers`) must derive the root pair `(tasks.py::ensure_ready, tasks.py::_reanchor_stragglers)`. That is the reference's shape and the r3 build's.
3. A wrapper above `findings._transition` that passes exhaustion through untouched (HEAD's `acknowledge`/`resolve`/`wontfix`) must be green at every k.
4. The lease's four sites, with `error_class` added, must be green by effect. They serve the fail-safe value, name the class in the WARNING, and make no further store call.
5. The fail-closed resolver must leave 0 unresolved handler elements on the production tree. Measured: `production_catch_sites()` = 237 sites, 0 unresolved (function-local imports resolved through `importlib`, never `exec`).

## §ITEMS — per worklist item (am-12 §4 order)
| # | item | where | status |
|---|---|---|---|
| 1 | **§1 FK-r3-5 AT THE STATE.** ∀ derived root R × verb v × measured write index k: the SAME instance reaches the caller, `statements_after == 0`, and the store is byte-identical to its state at the injection. The FIRED `(R, v, k)` ledger == the derived domain, both ways. | Instrument: `DriverSeamInjection` (`test_reanchor_58_r3_cas_seam.py`: `write_index`, MEASURE mode, `statements_after`, `fired`, `snapshot`, `_root_of`). Derivation: `_reanchor_58_support.module_call_graph` / `roots_in` / `derive_cas_roots`, one edge extraction shared with `cas_verbs_in`. Legs: `test_reanchor_58_r4_state.py::TestTheFiredLedgerEqualsTheDerivedDomain`, parametrised over the DERIVED pairs ∪ `CAS_ROOT_DRIVERS`. Controls: `TestTheStateInstrumentDiscriminates`. | **DONE** |
| 2a | **§2 F-A, the fail-closed resolver.** Evaluate in the module plus function-local imports, flatten nested tuples and `*starred`, and return anything unresolvable BY NAME. | `_catch_sites.resolve_caught` / `local_import_bindings` / `_flatten`; `CatchSite.unresolved`; `caught_classes` = its classes half (same signature, so a28c's scanner is unchanged). Pins: `test_exhaustion_fates.py::TestTheResolverFailsClosed` (positive control `except _T:` → `("_T",)`). The floor is 60 flattened-spelling sites (≥ 51). | **DONE** |
| 2b | lease ×4 = `named-isolation-served` rows, evidence by EFFECT, `error_class` pinned | Rows: `_exhaustion_fates.REGISTERED_FATES["store/lease.py::{get,create,update,release_if_held}"]`, evidence `("logs>=warning", "logs-error-class")`. The new static predicate is `test_exhaustion_fates._logs_error_class`. The by-effect half is `test_reanchor_58_r4_lease_fates.py`: domain derived as the lease module's in-domain, row-due sites == the driver table, both ways. | **DONE** — RED@HEAD on `error_class` only |
| 2c | inbox_awaiter ×4 + scout ×4 → `UNLOGGED_SITES` with owner + trigger (#521) | `UNLOGGED_SITES` became `dict[key, "owner · trigger"]`. There are 8 new rows (scout `run` went from 2 to 4). New pin: every entry names `owner · trigger`. | **DONE** |
| 3 | **am-11 ×5** | (a) the `_count_live_total` `raises-chained` row is DELETED, and the site now DERIVES TRANSLATE. (b) `raises-chained` is RETIRED from `EVIDENCE`. (c) `FAULT_CLASS_NAMES += _ProbeUnavailableError, ProbeGateError`, exact BOTH ways (`TestTheAdmissionRegistryIsExactBothWays`), which forced FK-r4-1. (d) row 47 is `re-raise-unchained` with its REQUIRED `reason`; the pin requires a reason and the log pair. (e) `derived_fate` returns `FORBIDDEN_TRANSLATE` for a chained translate to an un-admitted class, which no row can adjudicate. The synthetic `translates_to_a_verdict` was INVERTED to expect it. Regenerated consequence: the `server.py::run_probe_gate` row is DELETED (now a derived TRANSLATE). | **DONE** |
| 4 | a28c's three items | `install(monkeypatch, *, observe_shell: bool = True)` landed. The `_comms_register` row STAYS DELETED (untouched). `listed_handlers()` is a28c's D-5 hunk, untouched. r4 reads it through the same accessor. | **DONE** |
| 5 | `packet-64b-i-contract` `files:` += `test_reanchor_58_r3_cas_seam.py` (`_run_guarded`) | Added, plus `test_reanchor_58_r4_state.py`: its `_run_guarded` leg is the same 64b-owned red. Both files carry a `TYPE_CHECKING` reference so mypy names the symbol. `--verify-registry` passes. | **DONE** (D-R4-4) |
| 6 | §HELD part 2 SUPERSEDED; parts 1/3 re-derived and `git apply --check` on HEAD | §HELD | **DONE** |
| 7 | §3 hygiene rows | **F-E**: `SCALES` += `2fit+1`, and every scale is a function of the measured fit. **F-G**: `POSITIONS` × compositions (+ `bad_among_two_healable`), generated where the order is distinct. **F-H**: RU/PB and the clean-heal filter take every logger. **R-6**: the keeps UNIQUE leg gets a stray-alarm check. **R-2**: the corpse docstring is repointed. **R-7**: `Fate.catches`, generated from the live sites, plus `test_every_row_is_matched_to_ITS_site_by_the_caught_expression`. **F-F**: NOT DONE (D-R4-6). | **DONE except F-F** |

## §DEVIATIONS
- **D-R4-1 (fired ledger per leg).** am-12 §1 says "a session-scoped set … asserted `== {(R, v, k)}` at session end".
  - Under `-n 8` a pytest session is several processes, so a session-end assertion cannot see every worker's set.
  - Instead, each derived `(R, v)` is its own parametrised leg. The leg MEASURES n, arms k ∈ 1..n, and asserts that the set of triples the seam itself recorded == `{(R, v, k)}`.
  - The parametrisation IS the derived domain: `_collection_pairs()` = `derive_cas_roots(...)` ∪ `CAS_ROOT_DRIVERS`. A stale driver key reds; a derived pair with no driver reds.
  - This is the same equality, both ways, computed where it can be. Alternative reading: an xdist-aware aggregation via a shared file. I rejected it because leg ordering across workers is not guaranteed, so a "last test" assertion can run before its inputs exist.
- **D-R4-2 (ROOTS cut at the module).** am-12 §1 names "served doors (`AppContext.tasks` …) × spec-dict verbs" as root kind (a).
  - `derive_cas_roots` walks the SAME same-module call graph `derive_cas_verbs` uses (R-10's stated bound), so the root is the ledger's own public entry (`acknowledge`/`resolve`/`wontfix`/`annotate`, `transition`, …, `ensure_ready` for the heal).
  - That catches the r3 survivors' doors (W-IMPLICIT/W-REBIND/W-TUPLE live in `findings.resolve`/`wontfix`). A wrapper catch in `server.py`'s dispatcher above the ledger is NOT a root here. That is a named bound, the same one as R-10.
  - Re-open trigger: the first served-door catch site in `server.py` whose closure ∋ exhaustion. The static fate classifier is its backstop today.
  - The lease's four library calls (root kind (c)) are driven by the by-effect lease file, not by the seam. The lease store is not a `_txn` driver-seam caller under a CAS shell.
- **D-R4-3 = FK-r4-1 (six admissions removed).** am-11 §2 rules the admission list "exact, both ways (an admitted class with no translating site → RED 'delete the admission')".
  - MEASURED at `a77dc00` (`translate_targets()` over all 237 sites): `SurrealStoreError`, `FindingLedgerError`, `BriefLedgerError`, `PrincipalStoreError`, `AgentRegistryError` and `KeepStoreError` have NO translating site. `FAULT_CLASS_NAMES` is now `SurrealConnectionError`, `TaskLedgerError` + the two admissions.
  - No current verdict changes; they were translation targets of nothing.
  - Two readings exist. (A) "exact both ways" as written: delete them. This is my pick, and it is what the pin enforces. (B) am-11's "the author derives the current 8 + 2" presumes the 8 are real: keep them and enforce only "un-admitted translate → RED".
  - Consequence of (A): a future build that translates exhaustion to e.g. `FindingLedgerError` (64b-i?) reds `test_no_domain_site_translates_exhaustion_into_an_UNADMITTED_class` until the class is admitted with its reasoning. That is am-11's intent, but it costs 64b-i an admission row.
  - **Operator/sidecar ruling requested.**
- **D-R4-4 (registry spelling).** am-12 §4.3 writes `missing_symbols: [loremaster.findings.FindingLedger._run_guarded]`. The gate's matcher (`pending_contract_gate.error_names_symbol`) requires the OWNER token as mypy quotes it (`"type[FindingLedger]"`), so the entries read `type[FindingLedger]._run_guarded`. This follows the existing `type[TaskLedger]._guarded_append_fragment` rows. `--verify-registry` OK.
- **D-R4-5 (#461 shape on new files).** The gate refuses a registered file that names no missing symbol. So `test_reanchor_58_r4_state.py` references `TaskLedger._reanchor_stragglers` + `FindingLedger._run_guarded`, and `test_reanchor_58_r4_lease_fates.py` / `test_exhaustion_fates.py` reference `TaskLedger._guarded_append_fragment`. All are runtime-inert `TYPE_CHECKING` blocks. The lease rider is not a symbol, so it rides 58's build proxy.
- **D-R4-6 (F-F NOT DONE).** am-12 §3 F-F rules evidence predicates resolved BY IMPORT to the marker object, each with a silent synthetic negative control. The lease rows took evidence BY EFFECT (the runtime file), which is the "under a root" half. The "elsewhere" half (8 text-only rows: `_marks_failed`/`_appends_failed`/`_returns_named_outcome`/`adds-note`/`records-on-self`) is untouched. Owner: the next contract touch of `test_exhaustion_fates.py`, or the lead's routing. Decision point: before 58's build cold audit (the audit's F-F probe `evidence_probe.py` will still show the three silent synthetics satisfying the predicates).
- **D-R4-7 (`bad-middle` label for a two-entry row).** For `bad_plus_healable` (1 bad, 1 healable) the generated orders are `[b, h]` (bad-first) and `[h, b]`. The generator keeps the FIRST position name that yields a new order, so `[h, b]` is labelled `bad-middle`. It is the "bad after a healable" row; `bad-last` for that composition would be the identical order and is deduped.
- **D-R4-8 (`_exhaustion_fates.py` was `ruff format`ted).** Inserting `catches=` into 46 rows pushed many lines past 110. I ran `ruff format` on that one data module, so its diff carries formatting churn (a28c's DUAL comment text is byte-unchanged; the row literals were re-laid).

## §P1c — REACH (every guard r4 introduces or relies on)
| guard | reach set | derived from | growth reds? |
|---|---|---|---|
| FIRED ledger (`TestTheFiredLedgerEqualsTheDerivedDomain`) | `(R, v)` pairs | `derive_cas_roots(PACKAGE_ROOT, derive_cas_verbs ∪ listed_handlers ∪ discovered_drivers ∪ {heal})`, the same-module reverse call graph | YES: a new root is a new parametrised leg that reds until a driver fires under it. Bound: roots outside the verb's module (D-R4-2). |
| write index k | 1..n | n MEASURED per leg (unarmed MEASURE pass) | YES: n grows ⇒ more legs; n == 0 reds by name |
| `statements_after` | every statement at every driver seam (`execute_transaction`/`run_query`, every binding BY IDENTITY) between injection and the call's return | the seam wrapper itself | n/a (a state, not a list). Bound: a statement on a connection that bypasses `_txn` is invisible to the counter; the byte-identical store snapshot is its backstop. |
| store snapshot | every table in `INFO FOR DB` | the engine's own table list | YES: new tables are included automatically |
| fail-closed resolver | every production catch site | THE ONE walker `catch_sites_in` over THE ONE parser | YES: an unresolvable element reds by name |
| lease driver table | the lease module's in-domain, row-due catch sites | `production_catch_sites` × `in_domain` × `derived_fate is None` | YES, both ways |
| R-7 per-site match | row `catches` vs site caught expression, in source order | `site_signature` over the live sites | YES. Bound: a same-spelled new site replacing a same-spelled passthrough still inherits the row (the only residual of R-7). |
| admission registry | classes raised `from` a caught error, over all 237 sites | `translate_targets()` | YES, both ways |

## §DUAL — r4's removed / changed-behaviour rows (continuing r3's numbering)
| # | what changed | adjudication |
|---|---|---|
| R4-D1 | `DriverSeamInjection._should_fire` fired on the FIRST armed write | **dropped deliberately** (am-12 §1 F-D). k = `write_index`, default 1, so every r3/a28c/64b driver keeps its behaviour at k=1 |
| R4-D2 | `expect_the_SAME_instance` asserted identity only | **preserved-with-pin** (identity, am-8 §3 item 2) **+ widened** (am-12 §1 (1): `statements_after == 0` + byte-identical store). This applies to EVERY driver that calls it, r3's own and a28c's included |
| R4-D3 | `install(monkeypatch)` required a shell holder | **preserved-with-pin** for the default (`observe_shell=True` asserts ≥ 1 holder); the new `observe_shell=False` skips it (a28c decision (4) F-3) |
| R4-D4 | `caught_classes` dropped non-class values (tuples) silently | **old-bug** (F-A), not re-pinned; now flattens, fail-closed |
| R4-D5 | `raises-chained` evidence; the `_count_live_total#0` and `run_probe_gate` rows | **dropped deliberately** (am-11 §0 (a)/(b)/(c)) |
| R4-D6 | `translates_to_a_verdict → None` (row-due) | **inverted** (am-11 §0 (e)) → `FORBIDDEN_TRANSLATE` |
| R4-D7 | six fault admissions | **dropped deliberately** (FK-r4-1, am-11 §2 exact both ways) — ruling requested |
| R4-D8 | `UNLOGGED_SITES` frozenset | **reshaped** to a map with owner · trigger (am-12 §2); `set(UNLOGGED_SITES)` keeps the key-set pin byte-compatible |
| R4-D9 | RU/PB/clean-heal logger-name filters | **widened** (F-H): a correct build emits nothing ≥ WARNING from any logger in those windows (SAT §) |
| R4-D10 | `SCALES` offsets / F4 bad-first only | **widened** (F-E / F-G); the r3 legs keep their ids for `fit-1`/`fit`/`fit+1`. The F4 ids gained a `-<position>` segment, so the r3 ids of the form `…[<composition>-<kind>]` are RETIRED and replaced by `…[<composition>-bad-first-<kind>]` etc. |
| R4-D11 | fate rows matched by ordinal only | **widened** (R-7): per-site `catches` |

## §HELD — re-derived at HEAD `a77dc00` (2026-09-29)
- **Part 2 is DELETED** (am-12 §4 item 4: a28c's per-handler scanner is at HEAD). Nothing in r4 edits `test_retry_seam.py`.
- **Part 1** is r1's §HELD, VERBATIM: `5a43aeb:REPORT-contract-58.md` lines 173–557, md5 `dbba9753cbe960cda178f42687039c2d` (re-extracted; it matches r2/r3's recorded value).
- **Part 3** is r2's part 3, VERBATIM: `c42eeaf:REPORT-contract-58-r2.md` lines 177–195, md5 `15f38e319cb8d3c25456084dda4989b1` (matches).
- **Receipts, 2026-09-29:**
  - `git apply --check` part1 → OK and part3 → OK on the main tree (HEAD + peers' WIP).
  - Both → OK again on a clean `scratch_copy.sh` copy reset to HEAD `a77dc00`.
  - Both were APPLIED in the SAT tree (§SAT).
- **Re-derive at the re-base step** (below): re-extract by the two addresses above, check the md5s, and `git apply --check` both on the post-63c-i-a HEAD.

## §RE-BASE — the ONE named step owed when 63c-i-a's build commits (am-12 §5) — the BUILDER's FIRST STEP
1. `git fetch`, and confirm 63c-i-a's build commit is an ancestor of HEAD.
2. `git apply --check` §HELD parts 1 and 3 (addresses and md5s in §HELD) on the new HEAD.
3. Re-run the declared targeted set (`declare_set.py`, re-run on the new tree so the covering-test scan is current) on HEAD + §HELD + the r4 files. Expected changes, each 63c-owned today:
   - `test_reanchor_58_r4_state.py[agents.py::register -> agents.py::register]` goes GREEN (RS-5 control).
   - `test_exhaustion_fates.py::…test_every_non_derived_site_has_a_row_and_every_row_a_site` loses its `server.py::_comms_register` red.
   - test_retry_seam's a28b/a28c door pins go green.
4. If 63c-i-a changed a fact §1/§2 rest on (`_txn`'s class set, the D-9 harness forge, the scanner's key format read through `test_retry_seam._handler_function`), re-derive from HEAD, never from a report. Re-run the member diff (`member_diff.py`, §INSTRUMENTS).

## §BUILDER CONSTRAINTS (r1–r3's stand; r4 adds)
- **BC-r4-0: the FIRST step is §RE-BASE** (above).
- **BC-r4-1 (dependencies)** are BUILDER items; this contract did not edit `pyproject.toml` or the lockfile.
  - `more-itertools` (BC-r3-1, `constrained_batches`) must be a declared dependency of `loremaster`.
  - `pytest-timeout` is a dev dependency (the per-test timeout law; every r4 run used `uv run --with pytest-timeout`).
- **BC-r4-2 (`error_class`, the lead's scope call, am-12 §6).**
  - `store/lease.py`'s four `logger.warning("lease.lock.{read,create,update,release}_failed", extra={...})` calls each gain `"error_class": type(error).__name__`. That is four lines; the reference is `my_ref_r4.py`.
  - Nothing else in the four handlers changes. Keep serving `(False, <non-404 LockAbsent>)` / `False`, and keep NO retry and NO re-read.
  - Pinned by effect in `test_reanchor_58_r4_lease_fates.py`, and statically by `logs-error-class` on the four rows.
- **BC-r4-3 (the §1 instrument binds every exhaustion door, at every write).** The r3 constraints stand. r4 adds the following.
  - (a) Every CAS verb's exhaustion must reach the caller as the SAME instance, at EVERY transaction the verb sends, not only the first. The heal is driven at `2·fit+1` rows, so the second and third chunks are faulted too.
  - (b) After exhaustion the call sends NO further statement through `_txn` (no re-read, retry or compensation), and nothing commits.
  - (c) The heal must be reached BY NAME from the boot path (`ensure_ready` → … → `_reanchor_stragglers`). The root derivation reads the same-module call graph, so a heal invoked through `getattr` or a callback table derives no root and its legs red.
  - (d) A wrapper that catches around a CAS verb (e.g. `findings.resolve`) is a ROOT with its own leg. It must pass the instance through untouched.
- **BC-r4-4 (esc1: nothing escalates to a builder).** The adversary's seven W-* builds + kill probes are the cold audit's mutation set (am-12 §3).
  - If any W-* survives r4 on the build, that is a STOP naming the pin, never a builder-side "fix" to the tests.
  - A 5th CAS-population instance is a cold-audit STOP, never a round.
  - The builder does not edit a test to go green. A red it cannot green is escalated, named by test id.
- **BC-r4-5 (admissions).** A build that translates exhausted contention into any class outside `FAULT_CLASS_NAMES` (now four) reds `test_no_domain_site_translates_exhaustion_into_an_UNADMITTED_class`. The remedy is escalation for an ADMISSION ruling (FK-r4-1), never a site row.

## §DRY LEDGER (brief-base §6 — test-support symbols only; no production symbol)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_reanchor_58_support.module_call_graph` | `lore_search`-free: this IS the edge extraction `cas_verbs_in` inlined (read in full) | the inline loop in `cas_verbs_in` | **EXTENDED** `cas_verbs_in` (the loop is lifted into a function both consume; mutation-shared by construction) |
| `_reanchor_58_support.roots_in` / `derive_cas_roots` | `lore_search("reverse call graph: find the entry-point callers (roots) of a function within a module", k=5)` | top hit `graph_surreal.py:1179` (a production STORE-graph frontier walk over indexed nodes, not an AST same-module graph); in-file: `cas_verbs_in._closure` (a nested private helper) | **HAND-ROLLED** over `module_call_graph` (a reverse closure + no-caller filter; `_closure` is a nested private helper of another function) |
| `_catch_sites.resolve_caught` / `_flatten` / `local_import_bindings` | read `_catch_sites` in full (THE ONE resolver, am-9 §3) | `caught_classes` / `resolved_by_import` | **EXTENDED** `caught_classes` + `resolved_by_import` (`local=`); no second eval site, so the am-34 §5 one-resolver pin stays green |
| `test_exhaustion_fates.site_signature` / `translate_targets` / `_logs_error_class` | read the file's evidence family in full | the `EVIDENCE` predicates | **HAND-ROLLED** siblings in the same family |
| `test_reanchor_58_r4_state.fresh_world` / `db_snapshot` | `_reanchor_58_support.ledger58` / `snapshot` | `ledger58` (a fixture, one DB per test) and `snapshot` (the task ledger only) | **HAND-ROLLED**: a per-LEG world (the recipe `ledger58` uses, THE harness's `unique_database`/`drop_database`) and an all-tables snapshot (`snapshot` covers task rows + edges only; F-C's leg must see any table) |
| `test_reanchor_58_r4_lease_fates._Store` | none (a recording fake) | — | **HAND-ROLLED** |

## Packages considered
none — no production mechanism specified. The reference delta is four `extra` keys. The heal packer stays BC-r3-1 `more_itertools.constrained_batches`, per r3.

## §INSTRUMENTS — pasted VERBATIM (brief-base §1: the scratch root is session-local)
Reference chain for SAT/mutation hosts (a SAT host, NOT A SPEC): `build_ref58.py` (`9f2f580:REPORT-adversary-58.md`, md5 `5915c12e…`) → `my_ref.py` + `my_ref_am6.py` (`821be62:REPORT-adversary-58-r2.md`, md5 `de2d2801…` / `2176fb8e…`) → `my_ref_r3.py` (`7130508:REPORT-contract-58-r3.md`, md5 `c5678ba7…`) — each extracted by heading and md5-verified 2026-09-29; applied to HEAD `a77dc00` + §HELD 1/3 with every anchor asserted once; result md5 `tasks.py 017bdb55…` (= r3's recorded value) · `_txn.py a07f3e30…` · `findings.py 48d8fd7a…` · `lease.py 82f56701…` (after `my_ref_r4.py`).

### `my_ref_r4.py` (md5 `ec33542d43a60911218f96ece58be44e`)
```python
#!/usr/bin/env python3
"""contract-58-r4's reference delta over r3's chain (build_ref58 + my_ref + my_ref_am6 + my_ref_r3): the
packet 58 amendment 12 §2 rider — the four lease WARNINGs carry ``error_class``.  A SAT/mutation host, NOT A
SPEC.  Usage: my_ref_r4.py <scratch-root>.  Each anchor asserted exactly once (#194)."""
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
lease = ROOT / "loremaster/loremaster/store/lease.py"
text = lease.read_text()
anchor = 'extra={"lock_identity": self.identity, "error": str(error)},'
assert text.count(anchor) == 4, text.count(anchor)
text = text.replace(
    anchor,
    'extra={"lock_identity": self.identity, "error": str(error), "error_class": type(error).__name__},',
)
lease.write_text(text)
print("contract-58-r4 reference delta applied:", lease)
```

### `declare_set.py` (md5 `c6d0e1bc6e9f9162e21ab5f79732e565`)
```python
#!/usr/bin/env python3
"""contract-58-r4's DECLARED targeted set, written BEFORE any SAT run (CLAUDE.md TEST SCOPE): (1) my changed/new
test files; (2) the covering tests of `_txn`, `tasks`, `findings`, `briefs`, `keeps`, `lease` — an AST import scan
of every test module (lore_impact caps covering tests at 15, #518; fallback said out loud); (3) the structural pins
named by the brief.  Prints one repo-relative path per line, sorted."""
import ast
from pathlib import Path

TARGETS = {"loremaster.store._txn", "loremaster.tasks", "loremaster.findings", "loremaster.briefs",
           "loremaster.keeps", "loremaster.store.lease"}
MINE = """loremaster/tests/test_exhaustion_fates.py loremaster/tests/test_reanchor_58_r2_rulings.py
loremaster/tests/test_reanchor_58_r3_cas_seam.py loremaster/tests/test_reanchor_58_r3_convergence.py
loremaster/tests/test_reanchor_58_r3_probes.py loremaster/tests/test_reanchor_58_r3_tiers.py
loremaster/tests/test_reanchor_58_r4_state.py loremaster/tests/test_reanchor_58_r4_lease_fates.py""".split()
STRUCTURAL = """loremaster/tests/test_retry_seam.py loremaster/tests/test_mcp_server.py
loremaster/tests/test_reanchor_58_r3_relate.py scripts/test_forgery_door_sweep.py""".split()


def imports_target(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name in TARGETS for alias in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module in TARGETS:
                return True
            if any(f"{node.module}.{alias.name}" in TARGETS for alias in node.names):
                return True
    return False


covering = []
for path in sorted([*Path("loremaster/tests").glob("test_*.py"), *Path("scripts").glob("test_*.py")]):
    if imports_target(ast.parse(path.read_text())):
        covering.append(path.as_posix())
print("\n".join(sorted(set(MINE) | set(covering) | set(STRUCTURAL))))
```

### `sat_run.sh` (md5 `f9008d82218328524baf47127f4e039f`)
```bash
#!/usr/bin/env bash
# sat_run.sh <base|ref|head> <tag> — contract-58-r4's targeted run on the ONE SAT tree.
#   base = HEAD + §HELD 1/3 + r4 tests (the four reference-built production files at HEAD)
#   ref  = base + the reference chain (build_ref58 → my_ref → my_ref_am6 → my_ref_r3 → my_ref_r4), from refprod/
# Admission gate: MemAvailable ≥ 20 GiB (waits ≤ 10 min, logged).  Cgroup-capped, -n 8, per-test timeout 300.
set -uo pipefail
SP=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/2ecc96b6-4599-4602-aad7-9572255082eb/scratchpad
S=$SP/r4sat; MODE=$1; TAG=$2; LOG=$SP/sat-$TAG.log; XML=$SP/sat-$TAG.xml
FILES=(loremaster/loremaster/tasks.py loremaster/loremaster/store/_txn.py loremaster/loremaster/findings.py loremaster/loremaster/store/lease.py)
cd "$S"
for f in "${FILES[@]}"; do
  if [ "$MODE" = ref ]; then cp "$SP/refprod/$f" "$f"; else git show "HEAD:$f" > "$f"; fi
done
for i in $(seq 1 60); do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
  [ "$avail" -ge 20 ] && break
  echo "admission: MemAvailable ${avail} GiB < 20, waiting ($i)" >> "$LOG"; sleep 10
done
{ echo "mode=$MODE $(date -u +%FT%TZ) MemAvailable=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)GiB";
  uv run python -c 'import loremaster; print("loremaster.__file__ =", loremaster.__file__)';
  md5sum "${FILES[@]}"; } >> "$LOG"
mapfile -t SET < "$SP/declared_set.txt"
systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 \
  uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider --junitxml="$XML" "${SET[@]}" >> "$LOG" 2>&1
echo "exit=$?" >> "$LOG"
```

### `sync_mine.sh` (md5 `d82180fc5e467653eb59bea2f2dc49f2`)
```bash
#!/usr/bin/env bash
# sync_mine.sh — copy EXACTLY contract-58-r4's files from the main tree into the SAT copy (tracked: via a
# `git diff HEAD -- <file>` patch applied after restoring the copy's file to HEAD; untracked: cp).
set -euo pipefail
MAIN=/home/ejprice/PycharmProjects/lore
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/2ecc96b6-4599-4602-aad7-9572255082eb/scratchpad/r4sat
TRACKED=(loremaster/tests/_catch_sites.py loremaster/tests/_exhaustion_fates.py loremaster/tests/test_exhaustion_fates.py
  loremaster/tests/_reanchor_58_support.py loremaster/tests/test_reanchor_58_r3_cas_seam.py ${EXTRA_TRACKED:-})
NEW=(loremaster/tests/test_reanchor_58_r4_state.py loremaster/tests/test_reanchor_58_r4_lease_fates.py ${EXTRA_NEW:-})
for f in "${TRACKED[@]}"; do
  git -C "$S" checkout -q HEAD -- "$f"
  git -C "$MAIN" diff HEAD -- "$f" | git -C "$S" apply -
done
for f in "${NEW[@]}"; do cp "$MAIN/$f" "$S/$f"; done
for f in "${TRACKED[@]}" "${NEW[@]}"; do cmp -s "$MAIN/$f" "$S/$f" || { echo "MISMATCH $f"; exit 1; }; done
echo "synced ${#TRACKED[@]} tracked + ${#NEW[@]} new"
```

### `mut58r4.py` (md5 `88af2b4c483be034a99a2ab4dd29b976`)
```python
#!/usr/bin/env python3
"""contract-58-r4's declare-then-diff mutation driver (run INSIDE the SAT copy, in REF mode).

Each mutation: my OWN wrong build (never an adversary-58-r3 W-* build — replaying those is the cold audit's job),
an exact-once anchor, the node ids DECLARED from `pytest --collect-only` before the run, a pytest command whose
baseline reds (owned elsewhere) are DESELECTED so the "unexpected red" direction is live.  Driven through
scripts/mutation_proof.py (both-ways diff); because it does not restore on kill (#509), every mutated file is
`cp -a`'d first and `cmp`'d after — restored from the copy and reported if it differs.
Usage: mut58r4.py <scratch-root> [mutation-id ...]"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
ONLY = set(sys.argv[2:])
T = "loremaster/tests/"
R4 = f"{T}test_reanchor_58_r4_state.py::TestTheFiredLedgerEqualsTheDerivedDomain::test_every_root_verb_and_write_index_fires_and_the_caller_gets_the_SAME_instance"
FATES = f"{T}test_exhaustion_fates.py"
BASELINE_DESELECT = [
    f"{R4}[agents.py::register -> agents.py::register]",
    f"{R4}[findings.py::_run_guarded -> findings.py::_run_guarded]",
    f"{FATES}::TestTheRegistryIsTheAdjudicationBothWays::test_every_non_derived_site_has_a_row_and_every_row_a_site",
]
PYTEST = ["systemd-run", "--user", "--scope", "-q", "-p", "MemoryMax=16G", "-p", "MemorySwapMax=0",
          "uv", "run", "--with", "pytest-timeout", "pytest", "-n", "4", "--timeout=300", "-q", "-p", "no:cacheprovider",
          *[arg for node in BASELINE_DESELECT for arg in ("--deselect", node)]]
CONV = f"{T}test_reanchor_58_r3_convergence.py"
F4 = f"{CONV}::TestAnUnresolvableRowIsSkippedWHOLE"
FAILS_CLOSED = f"{FATES}::TestTheResolverFailsClosed"

MUTATIONS = {
    "M1-findings-reread-after-exhaustion": dict(
        file="loremaster/loremaster/findings.py",
        anchor="            # an IllegalTransitionError below. Propagate untouched.\n            raise\n",
        replacement="            # an IllegalTransitionError below. Propagate untouched.\n"
        "            await self._resolve_or_raise(id_or_number)\n            raise\n",
        expect=[f"{R4}[findings.py::acknowledge -> findings.py::_transition]",
                f"{R4}[findings.py::resolve -> findings.py::_transition]",
                f"{R4}[findings.py::wontfix -> findings.py::_transition]",
                f"{T}test_reanchor_58_r3_cas_seam.py::TestExhaustedContentionReachesTheCallerAsTheSAMEInstance::test_the_injected_instance_reaches_the_caller_and_a_real_loss_is_the_ruled_verdict[findings.py::_transition]"],
        args=[f"{T}test_reanchor_58_r4_state.py", f"{T}test_reanchor_58_r3_cas_seam.py::TestExhaustedContentionReachesTheCallerAsTheSAMEInstance"],
    ),
    "M2-heal-swallows-exhaustion-on-chunk-k>=2": dict(
        file="loremaster/loremaster/tasks.py",
        anchor="                await self._apply([f for f in fragments if f.statements])\n            except TxnDomainRejectionError:\n",
        replacement="                await self._apply([f for f in fragments if f.statements])\n"
        "            except (TxnDomainRejectionError, TxnContentionExhaustedError) if chunk_index else TxnDomainRejectionError:\n",
        expect=[f"{R4}[tasks.py::ensure_ready -> tasks.py::_reanchor_stragglers]",
                f"{FAILS_CLOSED}::test_no_production_handler_element_is_unresolved"],
        args=[f"{R4}[tasks.py::ensure_ready -> tasks.py::_reanchor_stragglers]", FATES],
    ),
    "M3-root-driver-arms-the-wrong-verb": dict(
        file=f"{T}test_reanchor_58_r4_state.py",
        anchor='            seam.arm("findings.py::_transition")\n            await seam.expect_the_SAME_instance(\n                f"findings.py::{verb_call}",',
        replacement='            seam.arm("findings.py::annotate")\n            await seam.expect_the_SAME_instance(\n                f"findings.py::{verb_call}",',
        expect=[f"{R4}[findings.py::resolve -> findings.py::_transition]",
                f"{R4}[findings.py::wontfix -> findings.py::_transition]"],
        args=[f"{T}test_reanchor_58_r4_state.py"],
    ),
    "M4-resolver-drops-tuple-constants": dict(
        file=f"{T}_catch_sites.py",
        anchor="    elif isinstance(value, tuple) and value:\n",
        replacement="    elif False:\n",
        expect=[f"{FAILS_CLOSED}::test_no_production_handler_element_is_unresolved",
                f"{FAILS_CLOSED}::test_each_spelling_flattens_to_the_classes_python_catches[a_tuple_constant-expected0]",
                f"{FAILS_CLOSED}::test_each_spelling_flattens_to_the_classes_python_catches[a_nested_tuple_constant-expected1]",
                f"{FAILS_CLOSED}::test_each_spelling_flattens_to_the_classes_python_catches[a_starred_element-expected2]",
                f"{FAILS_CLOSED}::test_the_tuple_spelled_exhaustion_catchers_are_IN_the_domain",
                f"{T}test_reanchor_58_r4_lease_fates.py::TestTheLeaseDriverTableIsTheDerivedDomain::test_the_driver_table_covers_exactly_the_lease_modules_in_domain_sites"],
        args=[FATES, f"{T}test_reanchor_58_r4_lease_fates.py"],
    ),
    "M5-lease-update-drops-error_class": dict(
        file="loremaster/loremaster/store/lease.py",
        anchor='"lease.lock.update_failed",\n                extra={"lock_identity": self.identity, "error": str(error), "error_class": type(error).__name__},',
        replacement='"lease.lock.update_failed",\n                extra={"lock_identity": self.identity, "error": str(error)},',
        expect=[f"{T}test_reanchor_58_r4_lease_fates.py::TestExhaustionAtTheLeaseStoreIsNamedByEffect::test_the_fail_safe_value_is_served_the_WARNING_names_the_class_and_nothing_follows[update]",
                f"{FATES}::TestTheRegistryIsTheAdjudicationBothWays::test_every_row_names_a_ruled_classification_an_owner_and_evidence_that_HOLDS"],
        args=[f"{T}test_reanchor_58_r4_lease_fates.py", FATES],
    ),
    "M6-an-admission-withdrawn": dict(
        file=f"{T}_exhaustion_fates.py",
        anchor='    "loremaster.calibration.engine._ProbeUnavailableError",\n',
        replacement="",
        expect=[f"{FATES}::TestTheAdmissionRegistryIsExactBothWays::test_the_two_am11_admissions_are_present",
                f"{FATES}::TestTheAdmissionRegistryIsExactBothWays::test_no_domain_site_translates_exhaustion_into_an_UNADMITTED_class"],
        args=[FATES],
    ),
    "M7-heal-sends-at-most-two-chunks": dict(
        file="loremaster/loremaster/tasks.py",
        anchor="        for chunk_index, chunk in enumerate(chunks):\n",
        replacement="        for chunk_index, chunk in enumerate(chunks[:2]):\n",
        expect=[f"{CONV}::TestOneBootHealsEveryShapeAtTheCapBoundary::test_one_boot_heals_the_whole_population_in_the_predicted_chunks[{shape}-2fit+1]"
                for shape in ("e1-distinct-absent", "e1-distinct-present", "e2-distinct-absent", "e2-distinct-present",
                              "e2-shared-absent", "e2-shared-present", "e3-distinct-absent", "e3-distinct-present",
                              "e3-shared-absent", "e3-shared-present")],
        args=[f"{CONV}::TestOneBootHealsEveryShapeAtTheCapBoundary"],
    ),
    "M8-heal-checks-only-the-first-entry": dict(
        file="loremaster/loremaster/tasks.py",
        anchor="            for old in olds:\n                head, cycled = heads[old]\n",
        replacement="            for old in olds[:1]:\n                head, cycled = heads[old]\n",
        expect=[f"{F4}::test_the_row_is_the_unit[{leg}-{kind}]"
                for leg in ("bad_plus_healable-bad-middle", "bad_among_two_healable-bad-middle",
                            "bad_among_two_healable-bad-last", "two_bad-bad-first")
                for kind in ("phantom", "cyclic")]
        + [f"{F4}::test_a_row_with_a_PHANTOM_and_a_CYCLIC_entry_records_BOTH_and_its_healable_entry_waits"],
        args=[F4],
    ),
    "M9-claim-loss-warned-on-a-non-lore-logger": dict(
        file="loremaster/loremaster/tasks.py",
        anchor="            pass  # a routine loss (am-3 §3) — the owner read below decides the verdict\n",
        replacement='            __import__("logging").getLogger("lore.claims").warning("claim lost %s", task_id)\n',
        expect=[f"{T}test_reanchor_58_r2_rulings.py::TestAClaimLossIsDEBUGNeverAnAlarm::test_an_8_way_race_logs_NO_warning_or_error_for_its_7_losers",
                f"{T}test_reanchor_58_r3_probes.py::test_PB_an_8_way_claim_race_raises_no_alarm_from_ANY_lore_logger"],
        args=[f"{T}test_reanchor_58_r2_rulings.py::TestAClaimLossIsDEBUGNeverAnAlarm",
              f"{T}test_reanchor_58_r3_probes.py::test_PB_an_8_way_claim_race_raises_no_alarm_from_ANY_lore_logger"],
    ),
    "M10-a-row-names-another-sites-expression": dict(
        file=f"{T}_exhaustion_fates.py",
        anchor='    "scout.py::_safe_kill": (\n        Fate(_LIFECYCLE, "scout", (), catches="_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION"),',
        replacement='    "scout.py::_safe_kill": (\n        Fate(_LIFECYCLE, "scout", (), catches="Exception"),',
        expect=[f"{FATES}::TestTheRegistryIsTheAdjudicationBothWays::test_every_row_is_matched_to_ITS_site_by_the_caught_expression"],
        args=[FATES],
    ),
}

results = {}
for name, spec in MUTATIONS.items():
    if ONLY and name.split("-")[0] not in ONLY:
        continue
    target = ROOT / spec["file"]
    backup = target.with_name(target.name + ".mutbak")
    shutil.copy2(target, backup)
    anchor_file, repl_file = ROOT / ".mut_anchor", ROOT / ".mut_repl"
    anchor_file.write_text(spec["anchor"])
    repl_file.write_text(spec["replacement"])
    command = [sys.executable if False else "uv", "run", "python", "scripts/mutation_proof.py", "--file", spec["file"],
               "--anchor-file", str(anchor_file), "--replacement-file", str(repl_file),
               *[arg for node in spec["expect"] for arg in ("--expect-red", node)], "--", *PYTEST, *spec["args"]]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    restored_ok = target.read_bytes() == backup.read_bytes()
    if not restored_ok:
        shutil.copy2(backup, target)
    backup.unlink()
    anchor_file.unlink()
    repl_file.unlink()
    tail = "\n".join((completed.stdout + completed.stderr).strip().splitlines()[-8:])
    results[name] = completed.returncode
    print(f"=== {name}: mutation_proof exit {completed.returncode} · restored byte-exact: {restored_ok}\n{tail}\n", flush=True)
print("SUMMARY", results)
```

### `member_diff.py` (md5 `44bb16562bb84fbf615932a7b91188e3`)
```python
"""am-12 §2 rider: the MEMBER sets of test_retry_seam's derived scanners (the exact-set pins' domain), printed
as JSON — run once with the HEAD `_catch_sites.py` and once with r4's, then diffed."""
import json
import test_retry_seam as index
print(json.dumps({
    "cas_handlers": sorted(index._discover_cas_handlers()),
    "guarded_doors": sorted(index._discover_guarded_cas_handlers()),
    "typed_catches": sorted(index._discover_typed_cas_catches()),
}, indent=0))
```

### `pc_edit_r4.py` (md5 `50b2e1f3a9db11b6fdb2d88dc1a0f2f1`)
```python
#!/usr/bin/env python3
"""contract-58-r4's registry edit (scripts/pending_contracts.yaml), applied to a FILE path given as argv[1]: the
working copy AND HEAD's blob (for the index), so the staged patch carries ONLY these hunks.  Anchors asserted
exactly once (#194)."""
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()


def once(old: str, new: str) -> None:
    global text
    assert text.count(old) == 1, (text.count(old), old[:80])
    text = text.replace(old, new)


once(
    """  ruling: docs/design/2026-09-26-packet58-kickoff-rulings.md (c8d3241) + packet58 amendments 1-8 (f4e96b4,
    e0760fd, 7266c1b, fd6497d, 67bf2cc, dcf6b0f, 01565f9, 03cb6d0); contract receipts REPORT-contract-58.md §RED +
    REPORT-contract-58-r2.md §RED@HEAD + REPORT-contract-58-r3.md §RED@HEAD (archived with the wave)""",
    """  ruling: docs/design/2026-09-26-packet58-kickoff-rulings.md (c8d3241) + packet58 amendments 1-8 (f4e96b4,
    e0760fd, 7266c1b, fd6497d, 67bf2cc, dcf6b0f, 01565f9, 03cb6d0) + amendments 9-12 (4cb8ce9, 5b72471, 0ed6705,
    5419448); contract receipts REPORT-contract-58.md §RED + REPORT-contract-58-r2.md §RED@HEAD +
    REPORT-contract-58-r3.md §RED@HEAD + REPORT-contract-58-r4.md §RED@HEAD (archived with the wave). r4 (am-12) —
    the lease `error_class` rider (store/lease.py, four lines) is carried by 58's BUILD (lead scope call) — its reds
    in test_reanchor_58_r4_lease_fates.py / test_exhaustion_fates.py are this bound's; test_reanchor_58_r4_state.py's
    agents.register leg (RS-5 control) and test_exhaustion_fates.py's server.py::_comms_register row are 63c-i-a's
    (discharged by its build, BEFORE 58), and its findings.py::_run_guarded leg is 64b-i's (packet-64b-i-contract)""",
)
once(
    """  - path: loremaster/tests/test_reanchor_58_r3_tiers.py
    missing_symbols:
    - loremaster.store._txn._ROLLBACK_LOG_TIERS
""",
    """  - path: loremaster/tests/test_reanchor_58_r3_tiers.py
    missing_symbols:
    - loremaster.store._txn._ROLLBACK_LOG_TIERS
  - path: loremaster/tests/test_reanchor_58_r4_state.py
    missing_symbols:
    - type[TaskLedger]._reanchor_stragglers
  - path: loremaster/tests/test_reanchor_58_r4_lease_fates.py
    missing_symbols:
    - type[TaskLedger]._guarded_append_fragment
  - path: loremaster/tests/test_exhaustion_fates.py
    missing_symbols:
    - type[TaskLedger]._guarded_append_fragment
""",
)
once(
    """  - path: loremaster/tests/test_comms_footer.py
    missing_symbols:
    - _finding_fakes.arm_finding_identity
""",
    """  - path: loremaster/tests/test_comms_footer.py
    missing_symbols:
    - _finding_fakes.arm_finding_identity
  # packet 58 amendment 12 §4 item 3 (contract-58-r4): 58's files RED on 64b's discovered driver
  # `findings.py::_run_guarded` until 64b-i's build lands `FindingLedger._run_guarded` (lore_verify not_found at
  # a77dc00). ONE path may sit in two bounds (the gate refuses duplicate IDS only); spelled as mypy names it.
  - path: loremaster/tests/test_reanchor_58_r3_cas_seam.py
    missing_symbols:
    - type[FindingLedger]._run_guarded
  - path: loremaster/tests/test_reanchor_58_r4_state.py
    missing_symbols:
    - type[FindingLedger]._run_guarded
""",
)
path.write_text(text)
print("registry edited:", path)
```

### the R-7 row generator (run once in `loremaster/tests`, 2026-09-29; inserts `catches=` from the live sites, in source order)
```python
import ast
from pathlib import Path
from _catch_sites import production_catch_sites
from test_exhaustion_fates import classify, site_signature
from _exhaustion_fates import REGISTERED_FATES
_v, undecided = classify(production_catch_sites())
signatures = []
for key, fates in REGISTERED_FATES.items():
    sites = undecided.get(key, [])
    for index, _fate in enumerate(fates):
        signatures.append(site_signature(sites[index]) if index < len(sites) else "<no site at HEAD>")
path = Path("_exhaustion_fates.py"); text = path.read_text()
tree = ast.parse(text)
assign = next(n for n in tree.body if isinstance(n, ast.AnnAssign) and getattr(n.target, "id", "") == "REGISTERED_FATES")
calls = [n for n in ast.walk(assign.value) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "Fate"]
calls.sort(key=lambda n: (n.lineno, n.col_offset))
assert len(calls) == len(signatures), (len(calls), len(signatures))
lines = text.splitlines(keepends=True)
offsets = [0]
for line in lines: offsets.append(offsets[-1] + len(line.encode()))
data = text.encode()
for call, sig in sorted(zip(calls, signatures), key=lambda pair: (pair[0].end_lineno, pair[0].end_col_offset), reverse=True):
    end = offsets[call.end_lineno - 1] + call.end_col_offset - 1  # position of ')'
    assert data[end:end+1] == b")"
    data = data[:end] + f", catches={sig!r}".encode() + data[end:]
path.write_text(data.decode())
print("rows", len(signatures), "no-site rows", signatures.count("<no site at HEAD>"))
# printed: rows 46 no-site rows 0  (then `ruff format` on the module — D-R4-8; one trailing-comma site fixed by hand)
```

## §MUTATION — every new pin family killed by a DECLARED mutation of my own (declare-then-diff, both ways; 2026-09-29)
- **Driver:** `mut58r4.py` (pasted in §INSTRUMENTS; the committed-pasted version is v2 `bc30af5e…`, which differs from v1 `88af2b4c…` (pasted in full below) only by M4's added declaration and `-n 4`). It runs over `scripts/mutation_proof.py`, byte-identical to HEAD's copy.
- **Declarations:** every node id was declared BEFORE the run and checked against `pytest --collect-only` (all present; anchor counts all 1).
- **Host:** the host copy `r4mut` is a `scratch_copy.sh` copy of HEAD `a77dc00` + §HELD 1/3 + the reference chain + the r4 test files. `loremaster.__file__ = …/scratchpad/r4mut/loremaster/loremaster/__init__.py`.
- **Deselected baseline reds** (owned elsewhere, so the unexpected-red direction stays live):
  - agents RS-5 (63c-i-a);
  - `_run_guarded` (64b-i);
  - the registry both-ways leg (63c-i-a's `_comms_register`).
- **Restore check:** every mutated file was `cp -a`'d before its run and `cmp`'d after (#509). All ten were restored byte-exact.
- **None of these is an adversary-58-r3 W-* build.** Replaying those is the cold audit's job (am-12 §3).

| id | my wrong build | pin family it proves | tail | verdict |
|---|---|---|---|---|
| M1 | `findings._transition`'s exhaustion handler awaits `_resolve_or_raise` (a RE-READ), then re-raises the SAME instance | §1 `statements_after == 0` (E3), all three findings roots + r3's identity leg (now state-checked) | `4 failed, 19 passed in 184.05s` | PROOF HELD |
| M2 | the heal's chunk handler becomes `except (TxnDomainRejectionError, TxnContentionExhaustedError) if chunk_index else TxnDomainRejectionError:`, so chunk ≥ 2's exhaustion is swallowed | §1 write index k (F-D) on `(ensure_ready, _reanchor_stragglers)` at `2·fit+1` + the fail-closed resolver (the IfExp handler is UNRESOLVED by name) | `2 failed, 26 passed in 119.19s` | PROOF HELD |
| M3 | test-side: the `resolve`/`wontfix` root drivers arm `annotate` (declared, never fires) | §1 FIRED-ledger reach (F-NOOP) | `2 failed, 14 passed in 149.51s` | PROOF HELD |
| M4 | the resolver's tuple branch is removed (`elif False:`) | §2 fail-closed resolver (3 spellings, domain membership, 0-unresolved, the lease domain table, R-7 per-site) | v1: exit 4, with ONE undeclared red, R-7's per-site pin (declared before R-7 existed — correct behaviour, a declaration gap); **v2:** `7 failed, 25 passed in 5.98s` | PROOF HELD (v2) |
| M5 | `lease.update`'s WARNING drops `error_class` | §2 lease row evidence by EFFECT + static `logs-error-class` | `2 failed, 30 passed in 5.40s` | PROOF HELD |
| M6 | the `_ProbeUnavailableError` admission is withdrawn | am-11 (c)/(e): admission present + no UN-admitted translate (`_count_live_total` goes FORBIDDEN) | `2 failed, 25 passed in 5.59s` | PROOF HELD |
| M7 | the heal sends at most two chunks (`enumerate(chunks[:2])`) | F-E `2·fit+1` over all 10 shapes | `10 failed, 30 passed in 282.25s` | PROOF HELD |
| M8 | the heal checks only the FIRST legacy entry per row (`olds[:1]`) | F-G positions (bad-middle / bad-last) + two-bad + am-9 §5 PCH | `9 failed, 8 passed in 3.30s` | PROOF HELD |
| M9 | the claim loss WARNs on a non-`loremaster` logger (`lore.claims`) | F-H RU + PB (any logger) | `2 failed, 3 passed in 2.52s` | PROOF HELD |
| M10 | one row's `catches` names another expression | R-7 per-site match | `1 failed, 26 passed in 5.20s` | PROOF HELD |

## §SAT — targeted, one tree, both ways (CLAUDE.md TEST SCOPE; no full suite, no currency gate), 2026-09-29
- **Declared set, written BEFORE the runs.** `declare_set.py` → 87 files, md5 `d788c864…`, made of three parts:
  - my changed/new test files (8);
  - every test module importing `store._txn` / `tasks` / `findings` / `briefs` / `keeps` / `store.lease`. This AST import scan is the fallback for `lore_impact`'s 15-test cap (#518), said out loud. `scripts/` is added by hand, because `scripts/` is not in lore's graph (#507);
  - the structural pins: `test_retry_seam.py`, `test_mcp_server.py`, `test_reanchor_58_r3_relate.py`, `scripts/test_forgery_door_sweep.py`. The fates, cas_seam and tiers files are in the "mine" list.
- **Tree:** `r4sat`, a `scratch_copy.sh` copy reset to HEAD `a77dc00` (`git reset --hard && git clean -fd`, status empty) + §HELD parts 1/3 (applied) + exactly my files (`sync_mine.sh`, `cmp`-verified).
  - `loremaster.__file__ = …/scratchpad/r4sat/loremaster/loremaster/__init__.py`, printed in each log.
  - REF mode swaps in the four reference-built production files (md5 in §INSTRUMENTS); BASE mode is those four at HEAD.
- **Runner:** `sat_run.sh` — the 20 GiB admission gate, `systemd-run --scope MemoryMax=16G MemorySwapMax=0`, `-n 8`, `--timeout=300`, junit.
- **REF leg** (`sat-ref1`, 21:12–21:39Z; ran on my files as of 21:11Z, i.e. BEFORE the R-7 edit — see the note below):
  - Result: **`661 failed, 6176 passed, 23 skipped, 4 warnings in 1629.23s`**, exit 1.
  - No cap kill and no timeout.
  - **Every red sits in a file owned by a registry bound — 0 UNOWNED** (`owners.py`):
    - 63c-i-a-a28: 470 (`test_fixwave_a28c` 280, `a28` 87, `retry_seam` 70, `a28b` 28, `a19b` 2, `surreal_store` 1, plus `exhaustion_fates` 1);
    - 64b-i: 186 (`test_findings_*_64b` ×8 files, `governed_substrate_64b` 34, `mcp_server` 28);
    - 58's own files: 7, all adjudicated below.
  - **The reds in 58's files on the REFERENCE build — each attributable to ANOTHER packet's unbuilt symbol:**

    | id | owner | why |
    |---|---|---|
    | `test_exhaustion_fates.py::…test_every_non_derived_site_has_a_row_and_every_row_a_site` | 63c-i-a-a28 | `server.py::_comms_register` row deleted by a28c (am-32 K5/K6) |
    | `test_reanchor_58_r3_cas_seam.py::…[findings.py::_run_guarded]` | 64b-i | `FindingLedger._run_guarded` unbuilt (am-12 §4.3) |
    | `test_reanchor_58_r4_state.py::…[findings.py::_run_guarded -> findings.py::_run_guarded]` | 64b-i | same; its driver also calls `report(title=…)` (64b's FK-1 signature) |
    | `test_reanchor_58_r4_state.py::…[agents.py::register -> agents.py::register]` | 63c-i-a-a28 | the driver's CONTROL leg: RS-5 unbuilt (a28c's own pin reds identically) |
    | `test_reanchor_58_r3_tiers.py` ×3 (`TxnUniqueViolationError` legs, incl. the keeps race that carries R-6's stray check) | 63c-i-a (am-33) | `TxnUniqueViolationError` unbuilt; the registry's `packet-58-contract` reopen note already names these |
  - **0 attributable (58-owned) reds on the reference.**

### `setdiff.py` (md5 `8910cbe4b7617ed1d12316891c2ad87f`)
```python
#!/usr/bin/env python3
"""Adjudicate SAT reds by set-diff (base-only / ref-only / shared) from two junit XMLs; print counts + files.
Usage: setdiff.py <base.xml> <ref.xml>"""
import sys
import xml.etree.ElementTree as ET
from collections import Counter


def reds(path):
    out, total = set(), 0
    for case in ET.parse(path).getroot().iter("testcase"):
        total += 1
        if case.find("failure") is not None or case.find("error") is not None:
            out.add(f"{case.get('file') or case.get('classname')}::{case.get('name')}")
    return out, total


base, base_total = reds(sys.argv[1])
ref, ref_total = reds(sys.argv[2])
print(f"collected base={base_total} ref={ref_total} · reds base={len(base)} ref={len(ref)}")
for label, ids in (("REF-ONLY", ref - base), ("BASE-ONLY", base - ref), ("SHARED", base & ref)):
    files = Counter(i.split("::")[0] for i in ids)
    print(f"{label} {len(ids)}: " + ", ".join(f"{f}×{n}" for f, n in sorted(files.items())))
    if label == "REF-ONLY":
        for i in sorted(ids):
            print("   ", i)
```

### `owners.py` (md5 `2d99ea7ff47ab4f4440931065eb09e51`)
```python
"""Group a junit run's reds by test FILE (from classname) and name each file's owning registry bound(s)."""
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import yaml

reg = yaml.safe_load(open("scripts/pending_contracts.yaml"))
owners = defaultdict(list)
for bound in reg["bounds"]:
    for entry in bound["files"]:
        owners[entry["path"]].append(bound["id"])


def to_file(classname):
    parts = classname.split(".")
    for cut in range(len(parts), 0, -1):
        candidate = "/".join(parts[:cut]) + ".py"
        if Path(candidate).exists():
            return candidate
    return classname


reds = []
for case in ET.parse(sys.argv[1]).getroot().iter("testcase"):
    if case.find("failure") is not None or case.find("error") is not None:
        reds.append((to_file(case.get("classname")), case.get("classname"), case.get("name")))
print("reds", len(reds))
for path, count in sorted(Counter(r[0] for r in reds).items()):
    print(f"{count:4d} {path} -> {owners.get(path, ['UNOWNED'])}")
for red in reds:
    if red[0] in sys.argv[2:]:
        print("   RED IN", red[0], "::", red[1].rsplit(".", 1)[-1], "::", red[2][:140])
```

## §FORKS (written before the pins that depend on them; brief-base §2)
- **FK-r4-1 — am-11 §2 "exact, both ways" vs. "the author derives the current 8 + 2".**
  - The two sentences conflict once six of the eight turn out to have no translating site.
  - Pick: (A) delete the six (D-R4-3). Alternative: (B) one-way only.
  - **Ruling requested** (sidecar/operator).
- **FK-r4-2 — the lease rider's home.**
  - The lead's scope call (brief) says 58's build carries the four-line `error_class` extra. I pinned it as such (BC-r4-2), with the registry note on `packet-58-contract`.
  - Nothing to rule; restated so the build does not route it to 11-i-a.
- **FK-r4-3 — am-12 §1's root kind (a) "served doors" vs. the same-module graph (D-R4-2).**
  - Pick: the module root, where every #102 wrapper so far has lived. Alternative: walk `server.py`'s dispatch into the ledgers, which needs a cross-module graph that R-10 already bounds.
  - Re-open trigger stated in D-R4-2.

### §SAT note — the R-7 edit landed AFTER the REF leg started (D-R4-9)
`sat-ref1` ran `test_exhaustion_fates.py` / `_exhaustion_fates.py` as they stood before the R-7 (`catches=`) change. The two files are pure-AST (plus the lease file's in-process fake), so I re-ran them on the post-R-7 bytes in REF mode on `r4mut`, which holds the same reference production md5s (`lease.py 82f56701…`) and the same test bytes (`cmp` clean against the main tree):

- **Result:** `1 failed, 32 passed in 5.84s`.
- **The one red** is `…test_every_non_derived_site_has_a_row_and_every_row_a_site`, owned by 63c-i-a (`_comms_register`).
- The BASE leg (below) ran on the post-R-7 bytes throughout.

### §SAT — BASE leg (`sat-base1`, 21:39–21:56Z, post-R-7 bytes), and the set-diff (`setdiff.py`)
- **BASE result:** `850 failed, 5933 passed, 23 skipped, 4 warnings in 1015.25s`. No cap kill, no timeout.
- **Collected:** base 6806 vs ref 6860. The difference is generated parametrisations that read the reference's added `_txn` classes and markers.
- **REF-ONLY: 36**, every one in a 63c-i-a-owned file:
  - `test_fixwave_a28b_63c_i_a.TestKeepsCasDecidesFromTheOneClass63cIAa28b` ×4 (`[TxnCasLostError|TxnClaimLostError|TxnHealChunkError|TxnReanchorStragglerError-winner-landed]`);
  - `test_fixwave_a28c_63c_i_a.TestTheClassIgnoresEveryEchoedPhrase63cIAa28c` ×32 (58's markers × {execute_transaction, run_query}).
- ⚠ **These are 63c's GENERATED sweeps meeting 58's reference `_txn` class set.** 63c's sweep parametrises over every class/marker `_txn` holds, so 58's classes become legs of 63c's pins. Those pins are red on the ref because 63c-i-a's typed decision (am-32/am-36) is unbuilt at HEAD.
  - Owned by `packet-63c-i-a-a28-contract` (files registered), so they are not attributable to r4.
  - **But they are the collision am-12 §5 names.** When 63c-i-a's build lands, these 36 must go GREEN over 58's classes too. If they do not, 58's build and 63c's decision disagree about 58's classes: a STOP at the re-base step, to be re-derived from HEAD, not from this report.
  - **Flagged for the lead.**
- **BASE-ONLY: 225** — packet 58's own RED-until-built legs (the 58 build cures them), plus:
  - ⚠ `test_task_ledger.py` ×10, a file NO registry bound owns. These are red only on HEAD + §HELD part 1: the held `server.py`/`_task_fakes.py` supersede hunks need 58's build. They are green on the reference.
  - This is a property of the §HELD-applied world, not of HEAD. At HEAD alone §HELD is unapplied, so the currency gate never sees it.
  - Named so the build does not read it as a regression. It rides §HELD part 1 exactly as in r1–r3.
- **SHARED: 625** — owned by 63c-i-a / 64b-i (as in the REF table above) plus 58's own cross-packet legs (the `TxnUniqueViolationError` tiers, the agents RS-5 control, `_run_guarded`).
- **ATTRIBUTABLE to r4 on the reference: 0.**

## §RED@HEAD — the BASE leg (HEAD `a77dc00` + §HELD 1/3 + r4 tests), per file I own or edited, 2026-09-29
| file | red / collected | the r4-new reds and why (right reason) |
|---|---|---|
| `test_reanchor_58_r4_state.py` | 4 / 19 | `[tasks.py::ensure_ready -> tasks.py::_reanchor_stragglers]`: the heal is unbuilt, so the pair is not derived (STALE). `[tasks.py::_reanchor_stragglers -> …]`: WRITES measured 0. `[agents.py::register …]`: 63c-i-a RS-5 control. `[findings.py::_run_guarded …]`: 64b-i. The findings root legs (acknowledge/resolve/wontfix/annotate) and the tasks transition/claim/supersede legs are GREEN at HEAD (their exhaustion paths already pass through). |
| `test_reanchor_58_r4_lease_fates.py` | 4 / 5 | the four ops: `error_class` absent (the rider is unbuilt). The served value and the no-further-call legs are reached, so the red is the rider alone. The driver-table leg is GREEN. |
| `test_exhaustion_fates.py` | 2 / 28 | the registry both-ways leg (63c-i-a `_comms_register`); the evidence leg (`logs-error-class` on the four lease rows — the rider). The 11 new F-A / am-11 / R-7 pins are GREEN at HEAD, because the resolver fix and registry are tests-side. |
| `test_reanchor_58_r3_cas_seam.py` | 4 / 23 | r3's four: no task shell ⇒ stale drivers; plus the `_run_guarded` row (64b-i) |
| `test_reanchor_58_r3_convergence.py` | 60 / 62 | the heal is unbuilt (every scale incl. the new `2fit+1` ×10, every F4 position leg) |
| `test_reanchor_58_r3_probes.py` / `test_reanchor_58_r2_rulings.py` / `test_reanchor_58_r3_tiers.py` | 6/7 · 27/27 · 16/20 | r2/r3's RED-until-built legs (unchanged in kind; F-H widened filters, R-2, R-6 ride them) |

### `mut58r4.py` v2 — the FINAL driver (md5 `bc30af5ed73a4d36363931483b501293`); diff against the v1 pasted above:
```diff
--- /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/2ecc96b6-4599-4602-aad7-9572255082eb/scratchpad/mut58r4.v1.py	2026-09-29 17:28:07.346261859 -0400
+++ /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/2ecc96b6-4599-4602-aad7-9572255082eb/scratchpad/mut58r4.py	2026-09-29 17:28:07.365262353 -0400
@@ -67,7 +67,10 @@
                 f"{FAILS_CLOSED}::test_each_spelling_flattens_to_the_classes_python_catches[a_nested_tuple_constant-expected1]",
                 f"{FAILS_CLOSED}::test_each_spelling_flattens_to_the_classes_python_catches[a_starred_element-expected2]",
                 f"{FAILS_CLOSED}::test_the_tuple_spelled_exhaustion_catchers_are_IN_the_domain",
-                f"{T}test_reanchor_58_r4_lease_fates.py::TestTheLeaseDriverTableIsTheDerivedDomain::test_the_driver_table_covers_exactly_the_lease_modules_in_domain_sites"],
+                f"{T}test_reanchor_58_r4_lease_fates.py::TestTheLeaseDriverTableIsTheDerivedDomain::test_the_driver_table_covers_exactly_the_lease_modules_in_domain_sites",
+                # v2 (declared after v1's run named it — R-7's pin landed after M4 was first declared): rows whose
+                # tuple-spelled sites left the domain no longer match a site.
+                f"{FATES}::TestTheRegistryIsTheAdjudicationBothWays::test_every_row_is_matched_to_ITS_site_by_the_caught_expression"],
         args=[FATES, f"{T}test_reanchor_58_r4_lease_fates.py"],
     ),
     "M5-lease-update-drops-error_class": dict(
```
