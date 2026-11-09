brief-base v25 read
brief project v7 read

# REPORT — builder-sdk3-66 (packet 66, surrealdb 2.0.0 → 3.0.0)

## SUMMARY (2026-11-08; production HEAD 7d44cf1, TREE 1aa04470e945…)
- **UPDATE — R43/R44 fix wave DONE (see §R43, §R44, §EXIT RECEIPT at the end):** production fda1411 · 5b4c138 · f2327ef · b411cab · d41aa47 · b2214d7 · 273bb69; receipt at HEAD 3f4d20a DIRTY 0 TREE 3fd07c54…: 530 failed / 11224 passed = the owned 530 node-for-node, R44 fallout 150/150 green, currency RED_ORPHANED 0. #25 recorded RETIRE (owed; pending audit confirmation). Lines below this one describe the earlier exit at 7d44cf1.
- **State: done-with-deviations.** Build commits: `9863c11` pin · `df84764` `60ca97e` `66a9979` `48067e8` build · `ead3356` retirements · `4566699` Q5 · `480ae72` #9 + teardown defect · `835d971` R34 · `4190c3e` R36 · `2c0d5ee` R34-F1 · `58fd5df` F6 · `5e464bc` R41-T · `6b43b65` R41-S · `d7c880d` R30 rider. (`7d44cf1` = the lead's operator-override removal, not mine.)
- **Exit (a):** packet-58/64b-i reds 523 (c503bf7) vs 524 (build), HEAD∖build = ∅; the one new node (`test_exhaustion_fates::…NON_VACUITY…51_sites`, 42 < 51 after FORK S deleted 18 tuple-catch sites) is an OPEN request (REQ-H, #19083). **(b)** F6 pins: all green (F6 landed). **(b')** other build reds: 0. **(c)** open requests: REQ-H only. **UPDATE (8032c5b):** REQ-H serviced test-only (`769903c` + docs `8032c5b`; production diff 7d44cf1→8032c5b EMPTY); the node now PASSES — `logs/reqh_confirm.log` (TREE `00c0df6e1e92…`, HEAD 8032c5b, DIRTY 0): `test_exhaustion_fates.py` 1 failed / 27 passed, the one red being packet-58's lease rows (`get`/`create`/`release_if_held` `logs-error-class`), red at c503bf7 too. So owned reds = 523 = c503bf7's count BY DERIVATION (524 − the one node, file-level run), not by a re-run of the 176-file set; **open requests: none**.
- **Currency** `--legs typecheck,ruff` at 7d44cf1: typecheck RED_ADJUDICATED (99, owned 58/64b-i), ruff GREEN, **RED_ORPHANED 0 on the run legs**; EXIT=1 is ONLY the pytest leg's NOT_RUN under `--legs` (the known #312-worded quirk).
- **20× loop:** **20/20 green on the FINAL production tree** (directive #19086): `loop20f_{1..20}.log`, 35 passed each, ~105.6–106.2 s. Production 7d44cf1 throughout: run 1 at HEAD 7d44cf1 DIRTY 1 (TREE `2ed8af7bf701…`; it straddled the servicer's REQ-H test commit `769903c` 12:17:01 — the dirty file is inferred to be that test edit, MEDIUM: tree_id records a count, not a name); runs 2–20 at HEAD 8032c5b DIRTY 0 (TREE `00c0df6e1e92…`); production diff 7d44cf1→8032c5b EMPTY. (Earlier loop: 20/20 on 480ae72.)
- **Deviations:** file-grouped commits (no interactive staging); M2 declaration error (3 declared / 4 observed); run scope by grep (#563); baseline without TREE= (identity lines given); interim runner races discarded. Forks raised and RULED: FORK-B1 (R34), REQ-A (R36), FORK T/S (R41), awaiter swallow (operator override of R42).
- **Defects found and fixed in this build:** teardown `kill()` parked 30 s on a dropped socket (SDK-3 regression; `480ae72` → `5e464bc`); memory's diverged private stamp check (`835d971`); keeps/principal_keys second refusal (`2c0d5ee`, servicer-found); 4 stamp readers serving `str(value)` / silently skipping corrupt values (`835d971`).
- Packages considered: tenacity (replace), surrealdb 3.0 natives (replace; `db.batch()` keep_with_trigger), stdlib timeout (replaced by SDK `connection.timeout` per R41), SurrealQL `INSERT … ON DUPLICATE KEY UPDATE` (replace) — §Packages considered.
- Odoo-20 portability: n/a — no Odoo seam touched.
- Reuse ledger: 30-odd new symbols, all dispositioned — §DRY ledger rows (three tables).
- Graded: n/a (builder report; no verdict on another's artifact).
- Decisions needed: none open. (Resolved: 20× loop re-run on the final tree per #19086; REQ-H serviced via R36 route `769903c`; `db.batch()` upstream gap filed by the lead as finding #588.)
- Receipt pointers: §Gate receipts (below, end); §C-row measurement table; §FINAL drop-list fate table; §Servicing-request log; §Sharing proved by mutation.

## Capability check (brief-base §4)
- Tools: Bash, Read/Edit/Write, Agent (haiku-runner/haiku-worker), lore MCP (loaded), SendMessage (deferred). Nothing the brief demands is unreachable as of start.

## Routing table (written before the first sweep — brief-base §3)
| step | tier | who | reason |
|---|---|---|---|
| read rulings / packet doc / store ref / adversary reports | 3 | me | binding spec; judgment |
| reference-build diff inventory (ref vs HEAD, 25 files) | 1 | me, one `git diff --stat` + per-file reads | small, on critical path, I read all of it anyway (it is the prior art I must judge) |
| SDK pin (`uv add`, lock) | 1 | me | 2 commands, critical path |
| production edits (seam, factory, retry, scout, indexer, ids, store, outcome, ensure_ready, B-1, B-2) | 3 | me | builder role (lore pins builders to Opus) |
| scripts/ Q5 headers: list of SDK sites | 1 | haiku-worker | literal grep sweep |
| scripts/ Q5 header wording | 3 | me | rule/doc wording is never Haiku |
| targeted test runs (155-file set + covering) | 1 | haiku-runner | test runs |
| typecheck/ruff currency | 1 | haiku-runner | gate run |
| 20× loop | 1 | haiku-runner | test run |
| red classification / both-ways diff verdicts | 3 | me | judging failures |
| covering-test derivation (`lore_impact`) | 1 | me, one parallel batch | small, feeds my run scope |

## Progress log
- 2026-11-08: commit A `9863c11` — `surrealdb==3.0.0` in `loremaster/pyproject.toml` + `uv.lock`. The image installs via `uv sync --locked --all-packages` (Containerfile), so the lock carries 3.0.0 into the conformance image; Containerfile unchanged.
- REQUEST 1 posted (lore_comms #19000, thread `q:servicing-commit-1`) + native wake to contract-sdk3-r7.
- Production work (uncommitted, in progress): `_txn` seam (factory/`long_operation`/row cap/outcome-unknown/native tenacity/`one_statement_result`/`record_key`/`record_text`), 17 owners on the factory + `@ensure_ready_operation`, scout native ladder, inbox awaiter selection, `SurrealStore` shared chunk-row builder + `upsert` + `apply` under `index_transaction_operation` + row warn, graph batched + native `starts_with`, indexer `_isolate_store_failure` (MP-1 chokepoint) + served `failed_files`, D1/F18 sites (server batch, briefs publish, calibration note), id-text homes collapsed onto `_txn.record_key`, `backoff.full_jitter` + delegation.
- Probe `probes/probe_chunk_overwrite.py` (R4 rider 1 / X13 / R27-2a), 3.3.5 TEST store: batched `INSERT … ON DUPLICATE KEY UPDATE <every CHUNK_COLUMNS col> = $input.<col>` == per-row `UPSERT … CONTENT` byte-for-byte (overwrite dropping an optional column; intra-batch duplicate → last wins); control: plain `INSERT` over an existing id → `AlreadyExistsError`. `$input.<absent>` reads NONE. PROBE PASS, EXIT=0.
- Production build committed (holding further commits while the servicer works): `df84764` seam · `60ca97e` scout/awaiter/factory owners · `66a9979` batched index + MP-1 helper + served failed_files + D1 batch line · `48067e8` ids + remaining owners + F18. Production mypy clean (`uv run mypy loresigil` Success; `uv run mypy loremaster`: no production-file errors), ruff clean. Woke servicer (lore_comms #19003).
- Contract run before C10 (`logs/sdk3_contract_2.log`, 16 `test_sdk3_*` files, TREE at the then-dirty tree): 53 failed / 115 passed. Every failure triaged reads through harness `run()` returning SDK-3 per-statement lists (C10 = servicing commit 1). Not a production verdict yet.
- ⚠ Side effect observed: 6 untracked `test_<pid>_<uuid>.memory.db` files at the repo root (06:02, during that run) — a memory ledger written to cwd by tests that died mid-way. Re-check after C10; flagged, not deleted yet.

## C-row measurement table (packet doc §R6.6) — measurements dated 2026-11-08, SDK 3.0.0 + 3.3.5 TEST store (fates and the commits that implement them: §FINAL drop-list fate table, which supersedes any PENDING cell below)
| drop-list row | measurement (instrument) | result | fate |
|---|---|---|---|
| #8 `_to_aware_utc` ×6 | declared types of every column the six coercers (and their `_require_*` wrappers) read, derived by parsing every `surreal_schema.generate_*` DDL; SDK decode of `time::now()` | every column is `datetime` / `option<datetime>` (agent.capability_expires_at, principal.expires_at, principal_key.{created,expires,revoked}_at, keep.created_at, member_of.since, to.acked_at, task.claimed_at/updated_at, …); none string/FLEXIBLE. SDK 3.0.0 decodes `PreciseDatetime` (a `datetime`), tz=UTC, ns kept. ⇒ X8's string/naive branches are unreachable from the store | R — IMPLEMENTATION PENDING (after servicing commit 1); fork FORK-B1 below |
| #15 `_SDK_PARSE_FAILURES` | `probes/probe_c15_parse_failures.py` (offline, SDK 3.0.0) | control → QueryError; non-dict cause → RETURNS (AttributeError arm GONE: `parse_rpc_error` returns `InternalError` for a non-dict); list cause → RETURNS; unhashable kind → RAISES TypeError; unhashable cause code → RAISES TypeError; deep chain → RAISES RecursionError | simplify: drop `AttributeError`, keep `(TypeError, RecursionError)` — PENDING (R1 rider: retirement pin is contract surface → servicing request) |
| #19 `"recursion depth"` marker | `probes/probe_c_engine.py` (3000 OR'd `@@` terms) | `ValidationError`, `kind=Validation`, `details=None`, `is_parse_error=False`, text "Parse error: Exceeded expression recursion depth limit" | K — the SDK predicate does NOT cover it; the text marker on an untyped Validation is still the only discriminator |
| #25 `name.value` mirror | `probes/probe_c_engine.py` EXPLAIN | `string::starts_with(record::id(id), $p)` → `TableScan` ("unsupported predicate"), 20 rows; control `string::starts_with(value, $p)` → `IndexScan name_value` | K — the mirror column is still what makes the prefix reach index-served |
| #26 `rebuild_embeddings` dance | `probes/probe_c_engine.py` + code read | `REBUILD INDEX` on a 2,000-row HNSW: ok in 0.24 s, kNN answers after. But the dance exists to CHANGE the HNSW DIMENSION (a dim change); `REBUILD` rebuilds at the existing definition | K — `REBUILD INDEX` cannot do the dance's job (dim change) |
| #34 `tasks._to_aware_utc_ceiling` (+1 µs) | live probe: `CREATE t:1 SET u = time::now()`, decode, through a pydantic `datetime` field, rebind as `$since` | decoded `PreciseDatetime` ns=951; through pydantic still `PreciseDatetime` ns=951; `WHERE u > $since` → `[]` for both (exclusive boundary holds with NO ceiling) | R — PENDING implementation (R1 rider pin: R6b + the `updated_since` exclusive-boundary tests) |
| #35 `floor_calibration` client-side NONE guard | `probes/probe_c_engine.py` | `record::id(NONE)` still RAISES InternalError on 3.3.5 (control `record::id(t:1)` → 1) | K (design) — re-probed; guard now routes through `_txn.record_key_or_none` |
| #9 `WebSocketException` arm (F10) | `probes/probe_c_proxy.py 20` (log `logs/probe_c_proxy_20.log`, EXIT=0), 20 × {ABORT, CLOSE_FRAME}, factory connections | LIVE iterator over a dead socket → `surrealdb.errors.ConnectionUnavailableError` 40/40; `kill()` while down → `surrealdb.errors.TransportTimeoutError` (after the 30 s request timeout) 40/40; `kill()` after `come_up` of a LIVE the new session never had → `surrealdb.errors.InternalError` 40/40; **no `websockets.*` class observed** | R — retire `WebSocketException` from `_CONNECTION_ERRORS` (PENDING edit after the in-flight run) |
| #16 `_safe_close` ×18 | same probe, CLOSE leg | `close()` over a severed socket → ok, 40/40 (both sever modes) | **R** (R41 FORK S): retired in `6b43b65`; the servicer lands a live close pin over every owner + a mutation receipt |
| #21 scout ladder | same probe, BOOT leg | first request through a fresh factory connection with the store down → `ConnectionUnavailableError` (the SDK does not reconnect a connection that never connected) | keep the ladder (R11: native tenacity, done) — a boot-time outage still needs it |
| #14 `db.batch()` | `probes/probe_c14_batch.py` (3.3.5 TEST store): [CREATE, THROW, CREATE] via `db.batch().execute()` | THROW whose text QUOTES the cascade notice → raises `QueryError` kind `Query` "…not executed due to a cancelled transaction" (the WRONG root cause; T6 fails); control plain THROW → `ThrownError` kind `Thrown`; nothing committed in either. `db.batch()` also raises ONE error, so X12's per-statement rollback log has no source | K — `compose` + `_failed_statements` + `_rollback_verdict` stay; upstream gap to file (SDK `connections/batch.py::_results` text selector), lead's call where |
| #17 signin replay / `auth=` | design read + pins RP2/L1/L6 in the targeted run (the SDK replays the session's signin after its own reconnect) | lore has no manual re-sign-in left beyond the first connect (each owner's `signin_credentials` + `.signin()`); the factory reconnects and the SDK re-authenticates | K (design) — adopting `auth=` would move credential ownership into the factory with no defect behind it; receipt = RP2/L1/L6 green on the build run |
| #24 LIVE literal escaping | code read: `InboxAwaiter.live_select_statement` | the inlined id is a `uuid5` hex digest of charset-ASSERTed parts — it cannot hold a backtick | K — safe by construction |

### FORK-B1 (#8 coercer deletion, low)
R6 S2: the six coercers are DELETED in favour of native `PreciseDatetime`, "not merged into a seventh shared copy". Each module also has a `_require_aware_utc` that REFUSES a missing/non-datetime required column loudly (a corrupt-row guard — design, not an SDK workaround). Reading A: delete the coercers; reduce each `_require_*` to a local `isinstance` check (six clones of one validation policy — against ONE IMPLEMENTATION). Reading B: delete the coercers; ONE shared validator for "a required datetime column holds a datetime" (a validator, not a coercer — S2's target was the coercion). I take B unless ruled otherwise.

## Drop-list fate table (packet doc §R3.5 #1–#31, §R4.8 #32–#36, #37) — as BUILT at `48067e8` (DRAFT; pending rows marked)
| # | fate as ruled | as built | where |
|---|---|---|---|
| 1 | R | KeyError arm deleted from `_SDK_AWAIT_BOUNDARY_ERRORS`, `run_query`, `_txn_query_raw`, `_raise_attempt_failure` | `_txn` |
| 2 | R | `_RETRYABLE_CONFLICT_KIND` deleted; `_is_retryable_conflict_kind` = `isinstance(QueryError) and is_transaction_conflict` (X4 keeps the QueryError check) | `_txn` |
| 3 | R (simplify) | 18 constructions → `open_surreal_connection`; per-owner `_drop_connection` kept as the racing backstop (X6) | 17 owners + scout |
| 4 | R | scout connects through the factory; the drop stays inside the reconnect ladder | `scout` |
| 5 | R (F16) | 7 `_bare_id` clones, `governed._bare`, `principal_keys._record_id_part`, `floor_calibration._bare_record_id`, 5 `principals` partitions, 2 `memory/local` splits → `_txn.record_key` / `record_key_or_none`; `KeepStore._record_id_part` = alias (tests call it) | see `48067e8` |
| 6 | R | `str(RecordID)` served text → `record_text` (principals, principal_keys, audit, diff, graph) / engine `<string> id` (keeps, F15) | |
| 7 | R | (no code change needed beyond #5: callers now key by `record_key` text; `RecordID` is hashable on 3.0) — VERIFY at audit: residual `str(record_id)` de-dupe keys in `graph_surreal` NOT yet swept | pending |
| 8 | C | measured (C-row table) → R; implementation PENDING | |
| 9 | C | measurement in flight | |
| 10 | R | range + `_prefix_upper_bound` + `_MAX_UNICODE_CODEPOINT` deleted; native `string::starts_with` | `graph_surreal` |
| 11 | R | batched INSERT per table (chunk, name, code_node, answers_to, refers); statement cap deleted, row cap | `surreal`, `graph_surreal`, `_txn` |
| 12 | R | `one_statement_result` in `run_query`, scout, awaiter | |
| 13 | R | `AsyncEmbeddedSurrealConnection` dropped from `_txn` (test-side sites: servicer) | |
| 14 | C | measured → K (db.batch fails T6) | C-row table |
| 15 | C | measured → simplify; implementation PENDING | |
| 16 | C → R (R41 FORK S) | measured (close() over a severed socket never raised, 40/40); the 18 wrappers deleted, 69 calls call `close()` — `6b43b65` | 17 owners + scout |
| 17 | C | NOT YET MEASURED | |
| 18 | K | unchanged | |
| 19 | C | measured → K | |
| 20 | K | unchanged | |
| 21 | C / R11 | ladder survives (boot-time connect still fails on the store down) and is native tenacity | `scout` |
| 22 / 36 | R | native `AsyncRetrying`; `_txn_conflict_backoff_seconds` deleted | `_txn` |
| 23 | K | unchanged | |
| 24 | K / C | measured by construction → K (uuid5 id, no backtick possible) | |
| 25 | C | measured → K | |
| 26 | C | measured → K | |
| 27, 28 | K | unchanged | |
| 29, 30 | K-inherited | SDK defaults accepted (no lore code) | |
| 31 | ruled | `SURREAL_REQUEST_TIMEOUT_SECONDS = 30.0` + named overrides via `long_operation` | `_txn` |
| 32 | RS7 R27-2a | `upsert` composes the ONE chunk-row builder through `apply` | `surreal` |
| 33 | Q5 | scripts headers PENDING (after servicing) | |
| 34 | C→R | measured → R; implementation PENDING | |
| 35 | K | re-probed (still raises); guard routed through `record_key_or_none` | |
| 37 | F-a | test-side (servicer) | |

## DRY ledger (every new reusable symbol)
| new symbol | where I looked | what it returned | disposition |
|---|---|---|---|
| `_txn.open_surreal_connection`, `long_operation`, `ensure_ready_operation`, `index_transaction_operation`, `_request_scope`, `one_statement_result`, `SurrealOutcomeUnknownError`, `TxnRowCapExceededError`, `TXN_ROW_*` | the rulings name them (R2/R5/F12/F14); reference build as prior art; grep `AsyncSurreal(` / `timeout(` / `[0]` selection in production | no prior owner (18 inline constructors; no timeout seam) | HAND-ROLLED as the ruled single owners |
| `_txn.fragment_rows` | grep `rows` / `len(f.statements)` in `_txn`, `surreal` | the reference computed the same sum twice (compose + apply) | HAND-ROLLED once; both call it |
| `_txn.record_key` / `record_key_or_none` / `record_text` | grep `_bare_id`, `_bare(`, `_record_id_part`, `_bare_record_id`, `partition(":")`, `split(":")`; test-side `sdk3_shape_fakes.record_parts` | 11 production homes (adversary-3 R12) + the test helper (test tree, not importable by production) | EXTENDED the reference's `record_text` into the one home; 11 homes deleted/aliased onto it |
| `_txn.OUTCOME_UNKNOWN_ADVICE` | grep "verify before retrying" | only the reference's inline text | HAND-ROLLED constant (one home of the Q6 sentence) |
| `loresigil.backoff.full_jitter` | ruled (R20 A4); `jittered_backoff_delay` in the same module | twin construction (adversary-3 R11) | `jittered_backoff_delay` now DELEGATES to it |
| `SurrealStore._chunk_rows_fragment`, `_CHUNK_OVERWRITE_CLAUSE` | R27-2a; graph_surreal's `ON DUPLICATE KEY UPDATE` prior art | no chunk-row builder existed | HAND-ROLLED (the ruled one builder; clause DERIVED from `CHUNK_COLUMNS`) |
| `SurrealCodeGraph._node_row` / `_answers_to_rows` / `_refers_row` | replaced `_node_statements` / `_edge_statement` | same job, statement-shaped | REPLACED (one each) |
| `Indexer._isolate_store_failure`, `failed_reason_meta_key`, `_NO_RECORDED_REASON`, `IndexSummary.failed_files` | the two cloned `except SurrealStoreError` arms (MP-1); `meta_get/meta_set` | the reference cloned the arms | HAND-ROLLED as the ONE helper both arms call |
| `AppContext._batch_connection_loss_line` | the batch renderer's own arms | — | extracted (keeps one catch site; ruff PLR0912) |
| `KeepStore._served_keep_id` | `record_text`; R8 F15 (engine form for keep ids) | — | HAND-ROLLED (reads the projected engine text, falls back to `record_text`) |
| `CommandSubscriber._stopped`, `_log_failed_connect` | tenacity `stop` / `before_sleep` hooks | — | thin tenacity hooks |
- `d78baa3` servicing commit 1 (C10 harness `run()` + R29 landmine-1 narrowing) landed; the servicer's own proof on `48067e8`: 957 nodes 62F → 1F (a `test_backoff_seam` AST spelling pin vs my R11 delegation — the servicer's REQ 2), green→red ∅, loop 20/20.
- Batch 2 committed: `ead3356` (drop #7/#8/#15/#34 + SDK-2.0 prose sweep), `4566699` (Q5 headers ×16 + survey port). Production mypy clean; `MYPYPATH=scripts mypy scripts`: 1 error, packet 58's pre-existing `tasks.SupersedeResult`.
- Prose sweep (production, retired names: KeyError-as-transport, statement cap, `_txn_conflict_backoff_seconds`, `CommandSubscriber._backoff`, unhashable RecordID, `_to_aware_utc`, embedded connection, "first-statement-only query()"): every hit adjudicated — FIXED: inbox_awaiter (mutation-pin prose), diff + snapshots (self-heal idiom), audit, floor_calibration/store, lease, surreal (×2), surreal_schema, indexer (×2), calibration/engine, keeps, principal_keys; UNRELATED (a domain `KeyError`, the `SELECT *` NONE-column trap, config/env `KeyError`s): config.py ×9, auth.py, principal_keys:145, keeps:110/641, graph_surreal:1014, embedding ×2, symbols, principals:197, floor_calibration/store:511, indexer:2200/2213, calibration/engine:248/627, lease:96, calibration/counting ×3, surreal:1431/1865, server ×5, floor_calibration/domain ×2; PACKET-68 SITE (left for 68): calibration/engine `jittered_backoff_delay` + counting `jittered_backoff_delay`; CURRENT (describes the retirement): `_txn` 463/760/781/867/870/1751/2138/2209.
- Run scope (TEST SCOPE law): `target_set_b66.txt` = r8's 155 files + 18 hand-derived behaviour-delta suites (`target_set_b66_added.txt`). Derivation: `lore_impact` covering view unusable for this change (elides at 15, bare-name unions — `CommandSubscriber.run` → 5,384 via `run`; 0 tests for every row mapper; #563), so the delta was derived by GREP over test-file imports/constructions of the modules whose behaviour differs from the satisfiability reference (agents, briefs, findings, messages, principals, tasks, keeps, principal_keys, graph_surreal, memory.local, governed, floor_calibration.store, calibration.engine) + test_backoff_seam + test_calibration_engine. Said here, per the dogfood protocol; the store-seam modules (`_txn`, `server`) are imported by ~90% of the tree — their covering set IS the full suite, which the cold audit runs.
- Baseline tree for EXIT (a): `head_c503bf7/` = `git archive c503bf7` + `lore.yaml` + `uv sync --all-packages` (SDK 2.0.0); `scratch_copy.sh --verify-only` VERIFIED (`loremaster.__file__` inside it).
- Runs in flight (haiku-runners): `logs/target_build_1.log` (tree 4566699) and `logs/target_head_c503bf7.log`, `-n 6` each. Diff instrument: `reddiff_b66.py` (pasted at hand-back).

### DEFECT found by the #9 measurement (SDK-3 regression, fixed in this build — PENDING edit)
`kill()` on a dropped socket PARKS on the SDK's reconnect until the 30 s request timeout (40/40, `TransportTimeoutError`);
SDK 2.0 failed at once. Both best-effort teardowns (`scout.CommandSubscriber._safe_kill`, `InboxAwaiter._safe_kill`) call it
during an outage, so the `await` verb (budget `AWAIT_BUDGET_S = 55`, chosen to stay under the ~60 s MCP ceiling) could hold
its caller ~55 + 30 s and be killed by the client instead of serving its honest render. Fix: the kill runs under ONE named
bound, `_txn.TEARDOWN_KILL_TIMEOUT_SECONDS`, via stdlib `asyncio.timeout` (fake-compatible; its `TimeoutError` is an
`OSError`, so the existing best-effort `except` swallows it and the registry-adjudicated catch sites do not move). A
pin (budget held when the store drops mid-await and stays down) is contract surface → servicing request.

### FORK-B2 (#16 `_safe_close`, low)
The measurement says `close()` over a severed socket never raises on 3.0.0 (40/40). Reading A: retire the 18 wrappers (call
`close()` bare). Reading B: keep them — each is a two-line best-effort guard whose removal no behaviour pin can see (a
spelling-level deletion), and the X18 nested-close obligation sits in the same per-owner `close()` bodies. I take B for this
build (no behaviour gained; risk of touching 18 lifecycle bodies), recorded as a measured K-with-reason; the lead may rule A.

## Targeted run vs HEAD c503bf7 (EXIT criterion (a)) — measured 2026-11-08 at build `4566699`
- Build: `logs/target_build_1.log{,.xml}` — TREE `7f1429b6…` (HEAD 4566699; DIRTY_FILES=6 = the six untracked `test_*.memory.db`), `loremaster.__file__` main checkout, surrealdb 3.0.0 — **556 failed, 9992 passed, 48 skipped, 3 xfailed** · EXIT=1.
- Baseline: `logs/target_head_c503bf7.log{,.xml}` — `head_c503bf7/` (git archive; no `.git`, so the header has no TREE= line — provenance by `loremaster.__file__` inside it + surrealdb 2.0.0) — **842 failed, 9665 passed, 47 skipped, 3 xfailed, 4 errors** · EXIT=1.
  - identity (lead #19009): extract = `mkdir -p head_c503bf7 && git archive c503bf7 | tar -x -C head_c503bf7` (then `uv sync --all-packages` on its own `uv.lock`; `scripts/scratch_copy.sh --verify-only` VERIFIED); `git rev-parse c503bf7^{tree}` = `4a33c4bff0546deb13baa4f498f075a46df6e33a`; `lore.yaml` (gitignored, R27-7c rider) copied from the main checkout `/home/ejprice/PycharmProjects/lore/lore.yaml`, md5 `3e02e6e21680285418261419c903bf45` in both places.
- Diff (`reddiff_b66.py` → `logs/reddiff_1.txt`):
  - (a) reds in packet-58 / packet-64b-i registered files: HEAD 523 · build 524 · build∖HEAD = 1 (`test_exhaustion_fates::…test_both_store_handlers_record_the_ONE_reason_for_both_causes` — REQ-A) · HEAD∖build = 0. Same file, already-red node `::TestTheRegistryIsTheAdjudicationBothWays::test_every_row_names_…_HOLDS` gained two indexer rows in its message (REQ-A sibling).
  - (b) other build reds: 32 = 29 `scripts/test_pending_contract_gate_f6.py` (F6 PENDING → exit (b)) + `test_backoff_seam::test_the_shared_policy_is_backed_by_tenacity_not_a_hand_roll` (servicer's own REQ 2) + `test_fixwave_a28c::…the_only_engine_text_reader_is_the_classifier` (REQ-C) + `test_link5_render_containment::…driven_or_out` (REQ-B).
  - (c) green@HEAD ∖ green@build = 52: 49 are line-number-parametrised ids renamed by my edits (`test_am37_13_3::…test_the_call_passes_noun[<file>::<fn>::<line>]` ×31, `test_principals_cli::…wrap_context…[<file>::<fn>::<line>]` ×18) — same counts on both trees, 0 bad on either (checked); the other 3 are the (b) reds above.
- Teardown/#9 targeted run `logs/target_teardown_1.log` (10 files, -n 8, before commit 480ae72): **3 failed, 848 passed** — the 3 = REQ-A ×2 + REQ 2; nothing new from the #9 retirement or the kill bound.

## Sharing proved by mutation (brief-base §6) — in `mut_tree/` (`scratch_copy.sh`-verified; `loremaster.__file__` inside it, printed in each log)
| proof | mutation | declared (from --collect-only, before the run) | observed | verdict | log |
|---|---|---|---|---|---|
| M1 MP-1 helper | `_isolate_store_failure`: reason always `_FAILED_STORE_REASON` (drops the bound) | refused-file pin `[batch]` + `[realtime]` | exactly those 2 (2 failed / 2 passed) | PROOF HELD — one helper reaches BOTH sweep shapes | `logs/mut_M1_mp1_helper.log` |
| M2 chunk-row builder | `_chunk_rows_fragment` declares `rows=0` | upsert over-cap pin + replace two-statement cap pin + replace row-warn pin | those 3 + `TestTheRowCapIsTheOneBound::test_apply_refuses_over_the_row_cap_before_anything_is_sent` (another `replace_file_fragment` consumer) | sharing HELD in substance (the upsert leg and the replace legs redden together); tool EXIT=4 = MY DECLARATION ERROR (declared 3, observed 4) — recorded, not re-declared from the output (R30 D1 rule) | `logs/mut_M2_chunk_row_builder.log` |
| `record_key` | — | — | — | NOT RUN by me (broad caller set; a raising-mutation attribution like R27-7a is the audit's) | — |

## 20× timing/concurrency loop — measured 2026-11-08 on production `480ae72`
`loop20.sh` (r8's set + `test_comms_await::TestSocketDropNonLoss`, whose teardown I changed): **20/20 EXIT=0, 35 passed each** (`logs/loop20_{1..20}.log`, ~106 s per run). ⚠ The working tree moved under the loop: 9 distinct TREE= values, HEAD 480ae72 → 3114183 — all of it the servicer's TEST commits (REQ-B/C/D/2/3, #584); `git diff 480ae72 HEAD -- loremaster/loremaster loresigil/loresigil scripts/*.py` is EMPTY, so the production under test was 480ae72 throughout. Stray `test_*.memory.db` at the repo root after the loop: 0 (servicer's #584 fix `f866fbe` landed meanwhile).

**FINAL re-run on 7d44cf1 (directive #19086, FORK T/S in the loop's teardown/close paths):** `loop20_final.sh` (same set; logs `loop20f_{1..20}.log`, summary `loop20f_summary.txt`): **20/20 EXIT=0, 35 passed each**, LOOP_EXIT=0. Run 1: HEAD 7d44cf1, DIRTY_FILES=1, TREE `2ed8af7bf701…` — it began ~12:16:12 and the servicer's REQ-H commit `769903c` (test-only) landed 12:17:01, so the dirty file is inferred to be that in-progress test edit (MEDIUM; the header carries a count). Runs 2–20: HEAD 8032c5b, DIRTY 0, TREE `00c0df6e1e92…`. `git diff 7d44cf1 8032c5b` touches only `loremaster/tests/test_exhaustion_fates.py` + the migration doc — the production under test was 7d44cf1 throughout. `loremaster.__file__` = the checkout, surrealdb 3.0.0, every run.

## Servicing-request log
| request | node(s) | ruling | commit |
|---|---|---|---|
| 1 (R27-1 + R29) | C10 harness `run()`; landmine-1 narrowing | applied | `d78baa3` |
| servicer REQ 2 | `test_backoff_seam::test_the_shared_policy_is_backed_by_tenacity_not_a_hand_roll` (spelling pin vs my R11 delegation) | REWRITE (behaviour) | `a5bd688` |
| servicer REQ 3 (packet-66 half) | `_surreal_fakes` statement-cap fallback; `_surreal_harness._RemovableDatabaseConnection`; the packet-66 registry bound (self-destructed) | REWRITE / delete | `0ae1dea` |
| servicer REQ 3 (packet-58 half) | 16 `TXN_STATEMENT_*` reads in packet-58 files (typecheck RED_ORPHANED) | FORK → sidecar (cross-packet) | open |
| REQ-A | `test_exhaustion_fates` known-bound pin + registry sibling (MP-1 helper moved the reason/log) | FORK → sidecar (packet-58 surface) | open |
| REQ-B | `test_link5_render_containment` — `_batch_connection_loss_line` unclassified | REWRITE (probe drives both branches through `_format_finding_ref`) | `aea8344` |
| REQ-C | `test_fixwave_a28c` engine-text scan flags `record_key` | REWRITE (allowlist row, reason stated); "keep record_key where it is" | `2834909` |
| REQ-D | retirement pins #8, #9, #15 + teardown-kill bound | pins added | `20c5623` |
| #584 (lead) | stray `test_*.memory.db` | test fixture fix (shared conftest `ledger_path`) | `f866fbe` |

## #102 contention survey re-run (the named re-run, ported in `4566699`) — measured 2026-11-08, TREE 48e4af15… (HEAD 20c5623), SDK 3.0.0 + 3.3.5 TEST store
`cd loremaster && uv run python ../scripts/survey_txn_contention_102.py` → `logs/survey_102_sdk3.log`, EXIT=0. The native tenacity `retry_on_conflict` driving the real `FindingLedger._report_fragment` mint, 50 rounds per N:
| N | exhausted | attempts p50/p90/p99/max | latency p50/p90/p99 (s) |
|---|---|---|---|
| 2 | 0 | 1 / 1 / 1 / 2 | 0.0037 / 0.0050 / 0.0075 |
| 8 | 0 | 1 / 2 / 3 / 4 | 0.0044 / 0.0089 / 0.0188 |
| 16 | 0 | 1 / 2 / 3 / 4 | 0.0052 / 0.0112 / 0.0216 |
| 32 | 0 | 1 / 3 / 4 / 5 | 0.0100 / 0.0201 / 0.0416 |
Against `_txn`'s cited SDK-2.0 survey (0 exhaustions; max attempts 6 and p99 0.045 s at N=32): no regression — BASE/CAP/deadline unchanged, still endorsed by measurement (drop list #22 / R11).

## R34 (sidecar RULING-11, adopted) — FORK-B1 = B, with riders — implemented (uncommitted until the targeted run reports)
- **Found defect fixed:** `memory/local._row_datetime` was a private copy that had already DIVERGED (no tz-aware check — memory accepted a naive stamp the other modules refuse). Deleted; memory's `valid_from` / `created_at` go through `required_datetime`, and its optional `valid_until` / `expires_at` (passed to the model raw before) through `stored_datetime`.
- `memory/local._parse_iso` labelled NOT a sibling (it parses the sqlite LEDGER's JSON text on replay).
- **Reach, derived by grep** (`required_datetime(|stored_datetime(` call sites + a sweep of bare `isinstance(…, datetime)` reads of store rows): agents, briefs, findings, keeps, messages, principal_keys, principals, tasks (the eight the ruling names) + memory/local + three more readers the sweep found and routed: `diff._row_to_summary` (snapshot `created_at` — served `str(value)` for a non-datetime: a silent conversion), `index/surreal_manifest._row_to_model` (file `updated_at` — same), `memory/local` supersede read-back of `valid_until` (silently skipped a corrupt value), and `floor_calibration/store` adopted head's `adopted_at` (keeps its domain "torn pointer" refusal for a MISSING stamp; the type check now rides the shared helper). Sweep verdicts: those 4 ROUTED; `_txn` 803/805 = the helper itself.
- **Served refusal text (R17), one place:** `"<table> <record_text(row id)> is unreadable: column '<col>' holds <type | a naive datetime>, a tz-aware datetime was required — a store-integrity fault (report it with lore_findings); other rows are unaffected"`; class `SurrealStoreError`. Bound, stated: the row id is rendered by `record_text` (R7 (d)'s parts form) — equal to the engine's `<string> id` for every key lore mints; for a NON-WORD key the engine brackets and this does not (F15) — acceptable here because the text is a DISPLAY of the faulty row, never persisted or compared.
- DRY ledger row added below; pins → servicing request REQ-E (after the run).

| new symbol | where I looked | what it returned | disposition |
|---|---|---|---|
| `_txn.required_datetime` / `stored_datetime` (R34) | the six deleted `_to_aware_utc`/`_require_aware_utc` pairs; `PrincipalStore._to_aware_utc` (keeps, principal_keys rode it); `memory/local._row_datetime`; `memory/local._parse_iso`; grep `isinstance(…, datetime)` over production | 8 copies of one policy + one diverged private copy (memory) + 4 unrouted readers; `_parse_iso` is a different domain (ledger JSON) | EXTENDED into ONE owner (check, never convert); every store-row stamp reader calls it; the repo has no helper registry (lead #19024) — this ledger is the record |
- R34 committed `835d971`. Targeted run over the 61-file R34 scope (`logs/target_r34_1.log`, uncommitted tree = the commit's content): **112 failed, 4186 passed, 18 skipped**; vs `logs/target_build_1.log` the ONLY new reds are the 10 `test_sdk3_retirement_pins_66d::TestARequiredDatetimeColumnIsCheckedNeverCoerced` nodes (`TypeError: required_datetime() got an unexpected keyword argument 'row'` — the REQ-D pins call the pre-R34 signature) → REQ-E (lore_comms #19034). The other 102 were red before (packet-58/64b-i-owned files: comms_footer, task_claimable_partition_58, task_guarded_shell_58, task_read_surface).

## R36 (sidecar RULING-12 fork 2, option (c)) — ONE per-file store catch site — `4190c3e`
- `Indexer._commit_or_isolate` holds the compose + `store.apply` AND the whole disposition (outcome-unknown read-back → served `indexed` when proven landed; row-cap reason naming its bound; `index.file.store_failed` WARNING with exc_info; `_mark_file_failed`) — `_isolate_store_failure` is inlined into it and deleted. `_index_chunks` / `_commit_batch_file` keep NO `except` arm (they return the helper's outcome when it refused). The cloned arms MP-1 found diverged no longer exist.
- M1 re-run on the helper: **PROOF HELD** — exactly `[batch]` + `[realtime]` (`logs/mut_M1b_commit_or_isolate.log`, in a refreshed `scratch_copy.sh` copy).
- Targeted run (`logs/target_r36_1.log`, 8 indexer-adjacent files): **4 failed, 94 passed** — all four are adjudication tables keyed on the old sites (F18 family table, exhaustion-fates registry ×2 incl. the packet-58 known-bound pin) → servicer follow-through posted on the REQ-A thread; `…_HOLDS` is back to exactly its c503bf7 message (lease rows only).
- `required_datetime` docstring now states the record_text-vs-engine-text bound (lead's R36 note; named cold-audit check).

| new symbol | where I looked | what it returned | disposition |
|---|---|---|---|
| `Indexer._commit_or_isolate` (R36) | the two arms' try bodies (byte-identical: `_compose_file_fragments` + `self._store.apply`); my `_isolate_store_failure` | one disposition already shared, two catch sites still cloned | EXTENDED `_isolate_store_failure` into the ONE catch site (renamed; the old name deleted) |

## R34 F1 (servicer-found, REQ-E part 2's legs) — `2c0d5ee`
- DEFECT: `KeepStore._row_to_keep` (created_at), `_row_to_membership` (since) and `PrincipalKeyStore`'s row mapper (created_at) read their REQUIRED stamps through `stored_datetime` and then hand-rolled the missing-stamp refusal (`KeepStoreError` / `PrincipalKeyStoreError`, no row named, pre-R34 text) — ROUTING-IS-NOT-SHARING: one policy, two refusals. My R34 sweep missed it because it grepped for raw `isinstance(…, datetime)` reads, not for a shared call FOLLOWED by a private raise. Fixed: `required_datetime`. Re-swept (grep `stored_datetime(` followed within 4 lines by `raise`): no remaining instance; the one deliberate domain refusal (`floor_calibration` adopted_at, an `option<datetime>` whose absence means a torn pointer) is RULING-11's kept case.
- Served consequence: a corrupt keep / member_of row met in `governed.resolve_subject` is no longer relabelled "keep store unreachable / wrong instance" (its `except KeepStoreError` arm); it surfaces as the integrity fault naming the row — still fail-closed, now the TRUE cause.
- Run `logs/target_f1_1.log` (14 files: keeps / principal_keys / visible_keeps / governed / the retirement pins): 34 failed / 360 passed — all 34 in `test_governed_substrate_64b.py` (packet 64b-i UNBUILT), identical to c503bf7 and to `target_build_1`; 0 new.

## F6 — `58fd5df` (OPERATOR-F6: GRANT-i → pins c01b114 + 64fcdd6 + 6ae8338 · ADV5 SATISFIED)
- Built on the r11 reference's shape (prior art; it passes 520/520) and re-written: no stray `import dataclasses` (uses `dataclasses.replace` via the existing import), docstrings stating each ruling, `_is_module_level_report` factored out, the self-destruct loop restructured as collected → judged / not collected → scope.
- Requirements met by construction (each named in the code): R30 (`PendingFile.red_nodeids`; `--verify-registry` admits ids-only, refuses no-claim); R31 reading (b) + CLASS (adjudication from exact id × collected × failed only; registry-iterating; exact membership; an entry's mypy claims still self-destruct; skip/xfail → no verdict + KEPT note); R37 (selection-level stale, names the selector, "confirm with --collect-only"; prefix walk decides SCOPE only); R39 D3 (a collected id is always judged); MP5-1..4; **W5** every selector walked (`for selector in selection`; `selection = tuple(pytest_args)`); **W6** scope never enters `partition_pytest` (a listed red under any selector stays RED_ADJUDICATED); **MP6-5** stated as a bound in `_is_module_level_report`'s docstring and the commit (a module-skipped file gets no KEPT note) — not silently fixed.
- Receipt `logs/f6_gate_suites_1.log`: **155 passed, 0 failed/skipped** — `test_pending_contract_gate_f6` 61 (= `--collect-only` 61), `test_pending_contract_gate` 44, `test_wave_gate` 29, `test_gate_currency` 21. `--verify-registry` on the live registry: EXIT=0.
- Follow-ups posted to the servicer (#19054): delete the self-destructed `packet-66-f6-contract` bound; register the 302-id entry afterwards; R30's path-prefix validator line on request. The builder did NOT register the 302-id entry (brief).

## Deviations and forks (each: what, why, who decides)
1. **Commit granularity.** One-concern commits were approximated by FILE groups: interactive staging is unavailable, and several files carry two concerns (e.g. `48067e8`: id routing + factory adoption in the same owners). Each commit message lists every concern it carries.
2. ~~**Teardown-kill bound uses stdlib `asyncio.timeout`**~~ — RESOLVED by R41 FORK T (`5e464bc`): both sites now use the SDK's `with connection.timeout(TEARDOWN_KILL_TIMEOUT_SECONDS)` after the servicer gave the kill() doubles `timeout()` through one mixin (`81f9cbd`); live re-measure 2.00 s vs 30.00 s control (`logs/probe_teardown_kill_forkT.log`); worst case 2·N stated at the constant. Original note: (R5 F4b words overrides as `with db.timeout(N)`). Reason: six test doubles implement `kill()` but no `timeout()` (grep), and this is a teardown bound, not a request-timeout override; the stdlib `TimeoutError` is an `OSError`, so the existing best-effort `except` swallows it and the adjudicated catch sites do not move. Alternative: `connection.timeout(TEARDOWN_KILL_TIMEOUT_SECONDS)` + a servicing request adding `timeout()` to the six doubles. Lead's call.
3. ~~**FORK-B2 (#16 `_safe_close` ×18): kept**~~ — RESOLVED by R41 FORK S: retired (`6b43b65`). Original note: although measured unnecessary on 3.0.0 (`close()` over a severed socket never raised, 40/40) — the deletion is behaviour-invisible and touches 18 lifecycle bodies beside X18's nested-close obligation. Reading A (retire them) is the lead's to rule.
4. **M2 mutation declaration error** — declared 3, observed 4 (a 4th `replace_file_fragment` consumer); recorded per R30's D1 rule, not re-declared from the output.
5. **`record_text` vs engine `<string> id` in the R34 refusal** — accepted by the lead as a stated bound (named cold-audit check); in `required_datetime`'s docstring.
6. **Run scope by grep, not `lore_impact`** (#563: elided at 15, bare-name unions, 0 tests for row mappers) — said in §Run scope; the store-seam modules' true covering set is the full suite (the cold audit's).
7. **Baseline without `TREE=`** (git-archive extract) — identity lines added (lead #19009).
8. **Interim runner races:** `logs/sdk3_contract_1.log` ran before `full_jitter` existed (discarded; re-run as `_2`); one `mypy` run raced the same edit. Neither is a receipt.
9. **#26 / #25 / #19 / #14 / #35 / #24 kept (K)** on measurement — see the C-row table; #14 owes an upstream SDK issue (db.batch's text selector) — the lead's channel, not mine.
10. **One owned-file node moved before R36** (`test_exhaustion_fates` known-bound pin, packet 58): resolved by R36 (`4190c3e` + servicer `da24469`).

## Packages considered
- `tenacity` 9.1.4 (installed source read: `AsyncRetrying`, `stop_any/stop_all/stop_after_*`, `wait_random_exponential`, `retry_if_exception_type`, `retry_error_callback`, `before_sleep`): **replace** — both in-66 loops are native `AsyncRetrying`; `backoff.full_jitter` is the one factory.
- `surrealdb` 3.0.0 (installed source read: `errors.py`, `connections/async_ws.py`, `connections/batch.py`, `data/types/datetime.py`): **replace** — `ReconnectOptions`, `timeout`/`streaming`, `TransportError` family, `QueryError.is_transaction_conflict`, `RecordID` parts, `PreciseDatetime`; `db.batch()` **keep_with_trigger** (compose stays: fails T6 by measurement, `probe_c14_batch.py`; trigger = an SDK release whose `batch._results` selects by typed kind, not text).
- stdlib `asyncio.timeout` for the teardown bound: **replace** (no hand-rolled timer).
- SurrealQL `INSERT … ON DUPLICATE KEY UPDATE` (corpus `insert/5776_…` read, then probed): **replace** the per-row UPSERT.

Odoo-20 portability: n/a — no Odoo seam touched.


## R41 (sidecar RULING-13) and the R30 rider — built
- FORK T `5e464bc`: `with connection.timeout(TEARDOWN_KILL_TIMEOUT_SECONDS): await connection.kill(live_uuid)` at both `_safe_kill` sites; the constant states the 2·N worst case and the skipped-`_end_live` note. Kill-path suites `logs/target_forkT_1.log`: 1 failed / 823 passed — the 1 is `test_exhaustion_fates::…HOLDS`'s lease rows, identical to c503bf7.
- FORK S `6b43b65`: 18 `_safe_close` wrappers deleted (−203 lines); X18's nested `PrincipalStore` closes untouched. Close-path suites `logs/target_forkS_1.log`: **1076 passed, 0 failed**.
- R30 rider `d7c880d`: `_entries_must_state_a_claim` refuses a `red_nodeids` id whose path prefix (text before the first `::`; a bare path is its own prefix) is not EXACTLY its entry's path, naming the id and the entry path. Gate suites `logs/f6_gate_suites_2.log`: **158 passed**; live `--verify-registry` EXIT=0.
- Servicer, meanwhile: `packet-66-f6-contract` deleted `2c8877e`; the 302-id entry regenerated EMPTY on this tree (all 302 collected and green — nothing to register); post-F1/R36 pin fallout `abc3b74`; FORK T mixin `81f9cbd`; R30 pins `078f502`.

| new symbol | where I looked | what it returned | disposition |
|---|---|---|---|
| `_txn.TEARDOWN_KILL_TIMEOUT_SECONDS` | `SURREAL_REQUEST_TIMEOUT_SECONDS`, `long_operation` overrides | those bound REQUESTS; nothing bounded a best-effort teardown | HAND-ROLLED (one named constant, applied through the SDK's `connection.timeout`) |
| `pending_contract_gate._is_module_level_report`, `selecting_selector`, `junit_node_id`, `GateCurrency.detail_lines`, `PendingContractGate.pytest_self_destruct_findings` / `pytest_kept_notes`, `PendingFile.claims_mypy` | the r11 reference (prior art), the existing `JUnitReportReader` / typecheck self-destruct | the reference's same-named functions | ADOPTED from the reference's shape and rewritten (docstrings per ruling; module-level predicate factored out); the ONE shared render (`detail_lines`) serves both `_render_currency` and `wave_gate` |
- Servicer receipts after R41 (r13 copy at d7c880d): FORK T mutation (drop the `with connection.timeout(...)`) → exactly the 4 awaiter / 2 scout bound legs red (HELD); R30 (remove the line) → exactly the 2 refusal legs red (HELD), `packet-66-r30-validator` self-destructed live and deleted; FORK S live close pin `5fb57fc` (17 close owners × 2 sever modes + scout's drop path; declared mutation → exactly 36 legs red, HELD); 302-id re-measure after T/S: 0 reds, nothing to register.
- R42 / operator override (#19081): the `inbox_awaiter` teardown close-swallow (`except _SDK_AWAIT_BOUNDARY_ERRORS: pass` around `connection.close()`) is REMOVED by a lead-run agent and committed by the lead — NOT by me; I made no debug-log edit and did not touch `inbox_awaiter.py`. The cold audit checks the removal. My final 175-file pair + currency are HELD until the lead posts that SHA (choice per #19078/#19081: hold, so the exit receipts are on the final tree).

## FINAL drop-list fate table (supersedes the DRAFT above; measured/built 2026-11-08, production HEAD 7d44cf1)
| # | ruled fate | as built (commit) | measurement / pin |
|---|---|---|---|
| 1 KeyError-as-transport | R | deleted (`df84764`) | RP1 |
| 2 `"TransactionConflict"` literal | R | SDK `QueryError.is_transaction_conflict` (`df84764`) | RP3/T1/T2 |
| 3 18 per-owner `AsyncSurreal` | R (simplify) | `open_surreal_connection` everywhere; `_drop_connection` kept as racing backstop (`60ca97e`, `48067e8`) | L1/L6 |
| 4 scout non-CAS drop | R | factory + native ladder (`60ca97e`) | L1 |
| 5 text re-parsers (~31) | R | `_txn.record_key` / `record_key_or_none` (`48067e8`) | K1–K4, B-2 |
| 6 `str(RecordID)` served text | R | `record_text` / engine `<string> id` (`48067e8`) | K1/K3/K4, C4 |
| 7 "RecordID unhashable" str keys | R | graph de-dupe by `RecordID` (`ead3356`) | K0 |
| 8 `_to_aware_utc` ×6 | C → R | deleted; one check-never-convert pair `_txn.required_datetime`/`stored_datetime` (R34; `ead3356`, `835d971`, `2c0d5ee`) | DDL types + SDK decode measured; 48 per-module pins `7135da4` |
| 9 `WebSocketException` arm | C → R | retired from `_CONNECTION_ERRORS` (`480ae72`) | `probe_c_proxy.py` 120 legs, 0 websockets classes; pin in `20c5623` |
| 10 prefix range | R | native `string::starts_with`; `_prefix_upper_bound` deleted (`66a9979`) | native_shapes |
| 11 per-row statements + statement cap | R | batched INSERT per table; `TXN_ROW_HARD_CAP` (`df84764`, `66a9979`) | B1–B4, row_bound |
| 12 raw first-statement `query()` | R | `one_statement_result` (`df84764`, `60ca97e`) | S1–S4, R1–R10 |
| 13 embedded connection | R | dropped from `_txn` (`df84764`) | — |
| 14 hand verification / `db.batch()` | C → K | `compose` kept | `probe_c14_batch.py`: db.batch fails T6 (upstream gap to file) |
| 15 `_SDK_PARSE_FAILURES` | C → simplify | `AttributeError` dropped (`ead3356`) | `probe_c15_parse_failures.py`; pin `20c5623` |
| 16 `_safe_close` ×18 | C → R (R41 FORK S) | deleted (`6b43b65`) | close over severed socket 40/40; live pin `5fb57fc` |
| 17 `signin` / `auth=` | C → K (design) | unchanged | RP2/L1/L6 green |
| 18 `_CONNECTION_ERROR_KINDS` | K | unchanged | — |
| 19 `"recursion depth"` marker | C → K | unchanged | `probe_c_engine.py`: untyped Validation, `is_parse_error=False` |
| 20 ASSERT/coercion markers | K | unchanged | — |
| 21 scout ladder | C / R11 | native `AsyncRetrying` per outage (`60ca97e`) | boot connect to a down store still fails (`probe_c_proxy.py`) |
| 22 / 36 `retry_on_conflict` | R | native `AsyncRetrying` (`df84764`) | T1/T2, native_retry; #102 survey re-run 0 exhaustions |
| 23 lease thread-bridge timeout | K | unchanged | — |
| 24 LIVE literal escaping | C → K | unchanged | uuid5 id — no backtick possible |
| 25 `name.value` mirror | C → K | unchanged | `probe_c_engine.py`: `record::id` prefix = TableScan |
| 26 `rebuild_embeddings` dance | C → K | unchanged | REBUILD INDEX cannot change DIMENSION |
| 27, 28 | K | unchanged | — |
| 29, 30 | K-inherited | SDK defaults | — |
| 31 30 s default timeout | ruled | `SURREAL_REQUEST_TIMEOUT_SECONDS` + named overrides (`df84764`) | CF1/CF2, MP3 |
| 32 `upsert` | RS7 / R27-2a | one chunk-row builder (`66a9979`) | probe_chunk_overwrite; M2 |
| 33 scripts/ SDK sites | Q5 | 16 headers + survey ported (`4566699`) | survey re-run |
| 34 tasks +1 µs ceiling | C → R | deleted (`ead3356`) | ns kept through pydantic + rebind (probe) |
| 35 floor_calibration NONE guard | K (design) | routed via `record_key_or_none`/`stored_datetime` | `record::id(NONE)` still raises |
| 37 F-a SDK-2.0 fake branch | R | test-side (servicer) | — |
| — awaiter teardown close swallow | removed by OPERATOR OVERRIDE of R42 | lead-committed `7d44cf1` (not mine) | no pin by operator direction; cold audit verifies |

X-inventory adjudications as built: X1/X2 dropped (KeyError arm); X3 pinned (SDK predicate); X4 kept (`isinstance(QueryError)`); X5 old-bug fixed (factory); X6 drop kept as racing backstop; X7 one socket per owner; X8 **dropped-deliberately: unreachable from the store (DDL-derived) and refused if it ever arrives** (R34 rider 2); X9 bare text → key via `record_key` (keeps alias kept); X10 `principals.delete` binds `record_key(principal.id)`; X11 old-bug fixed (native prefix); X12 preserved (compose + per-statement rollback log kept; db.batch K); X13 resolved: `ON DUPLICATE KEY UPDATE` overwrite (probed); X14 edges written after endpoints (B4); X15/X20 row cap, refused file NAMED; X16 old-bug fixed (S1–S3); X17 F15 engine form for keeps; X18 nested close preserved (untouched; live pin `5fb57fc` covers it); X19 `_rebuild_lock` untouched; X21–X23 preserved under native tenacity; **awaiter teardown close swallow: removed by operator override of R42 (`7d44cf1`)**.


## Gate receipts (exit receipts are the first three rows)
| gate | exact command | log (lead scratch `build66/logs/`) | EXIT | count line | TREE |
|---|---|---|---|---|---|
| targeted exit run, build | `run_tree.sh /home/ejprice/PycharmProjects/lore logs/exit_build.log 300 6 $(cat target_set_b66_exit.txt)` (176 files; `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 … pytest -q -rfE -p no:cacheprovider --timeout=300 -n 6 -o junit_family=xunit1`) | `exit_build.log{,.xml}` | 1 | 524 failed, 10178 passed, 48 skipped, 3 xfailed | `1aa04470e945…` (HEAD 7d44cf1, DIRTY 0) |
| targeted exit run, baseline c503bf7 | same runner on `head_c503bf7/` over `target_set_b66_exit_head.txt` (173 files that exist at c503bf7) | `exit_head_c503bf7.log{,.xml}` | 1 | 842 failed, 9665 passed, 47 skipped, 3 xfailed, 4 errors (identical in 3 runs) | no TREE (git-archive extract; `c503bf7^{tree}` = 4a33c4bf…; lore.yaml md5 3e02e6e2…) |
| currency typecheck + ruff | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | `exit_currency.log` | 1 (pytest NOT_RUN quirk only) | typecheck RED_ADJUDICATED 99 (58 / 64b-i) · ruff GREEN · RED_ORPHANED 0 on run legs | `1aa04470e945…` |
| both-ways diff | `uv run python reddiff_b66.py logs/exit_head_c503bf7.log logs/exit_build.log` | `reddiff_exit.txt` | — | (a) 523/524, HEAD∖build 0 · (b) 0 · (c) 50 = 49 line-number renames + REQ-H | — |
| F6 + gate suites | `run_tree.sh … logs/f6_gate_suites_2.log 300 8 scripts/test_pending_contract_gate_f6.py scripts/test_pending_contract_gate.py scripts/test_wave_gate.py scripts/test_gate_currency.py` | `f6_gate_suites_2.log` | 0 | 158 passed | `6660bbca7e91…` (= d7c880d content) |
| **20× timing loop, FINAL** | `bash loop20_final.sh` | `loop20f_{1..20}.log`, `loop20f_summary.txt` | 0 ×20 | 35 passed each | run 1 `2ed8af7bf701…` (HEAD 7d44cf1, DIRTY 1); runs 2–20 `00c0df6e1e92…` (HEAD 8032c5b, DIRTY 0); production 7d44cf1 throughout (production diff empty) |
| REQ-H confirm | `run_tree.sh /home/ejprice/PycharmProjects/lore logs/reqh_confirm.log 300 8 loremaster/tests/test_exhaustion_fates.py` | `reqh_confirm.log` | 1 | 1 failed (58's lease rows, = c503bf7), 27 passed; NON_VACUITY node PASSES | `00c0df6e1e92…` (HEAD 8032c5b, DIRTY 0) |
| 20× timing loop (earlier) | `bash loop20.sh` | `loop20_{1..20}.log` | 0 ×20 | 35 passed each | production 480ae72 (TREE varied with servicer test commits; production diff empty) |
| close-path suites (FORK S) | `run_tree.sh … logs/target_forkS_1.log 300 8 <9 files>` | `target_forkS_1.log` | 0 | 1076 passed | `c8639f2086da…` (= 6b43b65 content) |
| kill-path suites (FORK T) | `run_tree.sh … logs/target_forkT_1.log 300 8 <5 files>` | `target_forkT_1.log` | 1 | 1 failed (58's lease rows, = c503bf7), 823 passed | `99b31add8e59…` |
| mutation M1b (R36 helper) | `mutation_proof.py --file …indexer.py …` in `mut_tree/` | `mut_M1b_commit_or_isolate.log` | 0 | PROOF HELD 2/2 | `f0e604bc09d3…` |
| mutation M2 (chunk-row builder) | `mutation_proof.py --file …surreal.py …` | `mut_M2_chunk_row_builder.log` | 4 | declared 3, observed 4 (declaration error) | `d642ee88e79b…` |
| #102 survey re-run | `cd loremaster && uv run python ../scripts/survey_txn_contention_102.py` | `survey_102_sdk3.log` | 0 | 0 exhaustions at N=2/8/16/32 | `48e4af1578cb…` |

## Fan-out
Routing table at the top. haiku-runner ×19 (contract ×2, build_1, head, teardown, loop20, r34, r36, f1, final ×2, exit ×2 + interim, loop20 final, REQ-H confirm); haiku-worker 0; sonnet 0; peak 3 concurrent. Kept inline (tier 3 or small batches, each stated): every production edit; probe authoring and short probe runs (output < 30 lines each); red classification and the both-ways diffs; prose-sweep verdicts (~60 hits, read in one batch).

DONE · (report in hand-back) · SDK 3.0.0 build + F6 landed; exit: owned reds = c503bf7's 523 after REQ-H (769903c, test-only), 0 other reds, currency RED_ORPHANED 0; 20× loop 20/20 on final production 7d44cf1

---

## R43 FIX WAVE (RULING-14, directive #19092) — 2026-11-08, builder items only
Read in full: `sidecar66/RULING-14.md`, `audit66/REPORT-audit-66.md`. Scope run: the exit set ∪ `structural_pins.txt` (92) ∪ every test file grep-naming a touched symbol (`target_set_r43.txt`, 212 files; grep because `lore_impact` caps at 15 covering tests, #563 — said out loud).

### Commits (production, explicit paths, one concern each; two-concern files staged as intermediate content, each commit's diff read before commit, final content byte-checked against the snapshot `r43_final/`)
| commit | item |
|---|---|
| `fda1411` | **B1 #590** — THE cursor codec in `store._txn`: `served_instant_text` (`PreciseDatetime.isoformat_with_nanoseconds`) renders `next cursor:` AND the cursor echo (`rollup since …` / `no ledger activity since …`); `parse_served_instant` (SDK `parse_instant` + a zone-presence check, since `parse_instant` reads a zone-less text as UTC) parses `since`, teaching error kept. No ceiling. Codec rule written beside the pair; fix note (µs cursor re-serves its boundary row once, no shim) in docstrings + commit. |
| `5b4c138` | **R-6** — 4 `server.py` `str(x.id).split(":",1)[-1]` sites + `TaskLedger._traversal_ids` → `record_key` (behaviour note: `_traversal_ids`' non-RecordID branch used to serve the raw text incl. `table:`; it now serves the bare key like the RecordID branch — unreachable from the traversal projection, which yields RecordIDs). |
| `f2327ef` | **R34 clause** (ruled text verbatim) + `required_datetime`'s stated bound corrected (9a). |
| `b411cab` | **Prose**: R-7 (`_RECORD_KEY_ESCAPES`, `record_text`), R-8 (`_names_with_value_prefix`, `_compose_file_fragments`, `forgery_door_sweep` handled-family list), named bounds R-4/T3 (`_raise_attempt_failure`), R-11/T20 (`Indexer._commit_or_isolate`), R-12/T23 (`CommandSubscriber.stop`), R-12/O21 (`BriefLedger._relate_briefed`). |
| `d41aa47` | **R-7 quantifier fix, found by my own R-9 re-run**: the engine backticks an ALL-DIGIT key too (control `42` → ``keep:`42` ``), so b411cab's "the engine renders a `[a-z0-9]` key bare" over-claimed; the rule is "a word key that holds a letter". Bound added: a `uuid4().hex` key (findings, tasks) is all-digit with p ≈ (10/16)^32 ≈ 3e-7. |

### B1 — the class ("who else hands a stamp back?"), re-swept at HEAD
- rollup `since` / `next cursor` / the cursor echo → the codec (fixed).
- `server._age_status_from_iso` parses a STORED manifest stamp (not a hand-back) — unchanged, as ruled.
- `principals._parse_instant` (CLI `--expires/--at`, `fromisoformat`, naive → UTC): an OPERATOR-typed expiry, not a served stamp handed back; truncation ≤ 1 µs of an expiry instant. **Sibling, reported, not changed** — say if you want it on the codec.
- `diff.SnapshotSummary.created_at` serves `.isoformat()` (µs), but `lore_diff since/until` take snapshot IDS, never stamps — not a hand-back today; it becomes one the day a tool accepts it (then: the codec).
- `scripts/snapshot_gc._to_aware_utc` (R-12): **no edit — neither branch of the Q5 rule applies.** The script imports no `surrealdb` (it drives loremaster's ported stores), so it is not one of Q5's "21 SDK users" and an "SDK 2.0 result shapes" header would be FALSE. Its naive → UTC branch serves the `--epoch` CLI argument (documented policy); on `_snapshot_instant` the text comes from `SnapshotSummary.created_at`, rendered from an R34-validated tz-aware stamp, so the naive branch is unreachable there. Not drop #8's class (no store column is coerced).

### Prose sweep (R-8 receipt) — `r43_sweep.md`, one row per hit, 108 rows
`git grep -nE 'UPSERT per record|statement\[0\]|KeyError|2\.0\.0'` over production members + `scripts/` non-test at HEAD: HEADER 32 (Q5 headers, true by design) · BOUNDED 13 (SDK-2.0 prose inside Q5-headered unported scripts) · HISTORICAL 7 (`_txn`/`lease` past-tense retirement notes, accurate) · CODE 17 (stdlib KeyError catch/raise) · NOT-SDK 29 (env/dict/registry KeyError prose) · ENGINE-ROW 9 (dict KeyError on a NONE column the engine omits — engine behaviour from the store reference, not re-measured by me) · FIXED 1. `UPSERT per record`: 0 hits (fixed). Noted: `probe_store_recovery_07a.py:46` names test classes retired in `b655971` — inside a Q5-headered script, left BOUNDED.

### R34 clause — one Leg-1 question for the ruling's owner
The ruled text says "**this listing** could not be completed". `required_datetime` also guards SINGLE-record reads (each module's row mapper serves get and list alike), where the response is not a listing. The remedy ("report it") is right either way; only the noun over-claims. Implemented verbatim; flagging rather than re-wording a ruled string.

### R-9 — every C row now has a saved instrument + log (`build66/probes/`, `build66/logs/r9_*.log`; each log: TREE `17796957…` = HEAD b411cab DIRTY 0, `loremaster.__file__` = checkout, surrealdb 3.0.0, probe sha256, EXIT=0)
| row | instrument | decisive line(s) | verdict |
|---|---|---|---|
| #14 | `probe_c14_batch.py` | T6 quoting → `QueryError kind= Query … cancelled transaction`; control → `ThrownError kind= Thrown`; nothing committed either way | **K holds** (db.batch fails T6; finding #588) |
| #15 | `probe_c15_parse_failures.py` | non-dict/list cause → RETURNS; TypeError ×2 and RecursionError still RAISE | **as built** (AttributeError arm only dropped) |
| #19 | `probe_c_engine.py` | `ValidationError … details= null is_parse_error= False` | **K holds** |
| #25 cand. 1 | `probe_c_engine.py`, `probe_c25_id_range.py` | `string::starts_with(record::id(id),$p)` → TableScan; `WHERE id >= $lo AND id < $hi` → TableScan (rows exact) | fails (plan) |
| **#25 cand. 2** | `probe_c25_id_range.py`, `probe_c25_bound_range.py` | `FROM name:⟨lo⟩..⟨hi⟩` → **RecordIdScan**, 20/20 exact, traps excluded; BOUND `FROM $r` (`RecordID('name', Range(BoundIncluded, BoundExcluded))`) → RecordIdScan 20/20; two prefixes `FROM $r1, $r2` → Union of 2 RecordIdScans 40/40; control = mirror IndexScan / BitmapOr | **PASSES → the KEEP basis fails. Recorded "RETIRE (owed; pending audit confirmation)" per the lead (RULING-14 §ADDENDUM); NO schema migrated; fork posted #19096** (follow-up must state the last-char-increment bound — a prefix ending in U+10FFFF has none, the X11 shape) |
| #26 | `probe_c26_rebuild_dimension.py` (NEW) | L1 control REBUILD ok 0.19 s; L2 `REBUILD … DIMENSION 16` → parse error; L3 16-dim row under the 8-dim index → refused; L4 `DEFINE INDEX OVERWRITE … DIMENSION 16` over 8-dim rows → refused | **K holds, now MEASURED** (REBUILD cannot change dimension; a model change needs recreate + replay) |
| #34 | `probe_c34_cursor_boundary.py` (NEW — the row that had none) | stamp ns 372; L1 in-process rebind EXCLUDED; L2 pydantic keeps `PreciseDatetime` ns → EXCLUDED; **L3 CONTROL isoformat/fromisoformat → RE-SERVED (#590 reproduced)**; L4 the codec → EXCLUDED; L5 µs cursor via the codec → re-served once (the stated bound) | **R holds with B1**; the control proves the probe sees the defect |
| #35 | `probe_c_engine.py` | `record::id(NONE)` RAISES InternalError; control `[1]` | **K holds** |
| X13 | `probe_chunk_overwrite.py` | overwrite OLD==NEW, intra-batch dup last-wins, control plain INSERT → AlreadyExistsError, `$input.<absent>` → None; PROBE PASS | **as built** |
| R-7 facts | `audit_probe_record_text{,_2}.py` (audit's, copied verbatim with a provenance line) | ULID/digit-led/alpha/hex equal; controls `a-b`, `42` differ (backticked); memory uuid5 differs; composite array equal | prose corrected (`d41aa47`) |
Deviation (accepted, the worker's own): two probes (#14, #15) ran concurrently — separate throwaway databases, #15 offline; logs intact.

### Servicing requests (test changes)
- **REQ-I** #19097 (q:r43-rollup-format-pins, directive): 7 `TestRollupDispatch` pins red ONLY on the B1 format; proposal: expected text derived from `served_instant_text`; `test_cursor_normalises_a_trailing_z`'s premise is gone (rewrite or retire under the B1 round-trip pin).
- R34 text assertion (already queued by the lead): the 10 `test_sdk3_retirement_pins_66d::TestARequiredDatetimeColumnIsCheckedNeverCoerced` nodes red ONLY on the ruled clause — listed in REQ-I.
- B1 round-trip pin (queued by the lead): my `probe_c34_cursor_boundary.py` legs L3/L4 are the shape (L3 is the mutation's expected-red direction).

### R43 receipts
| gate | command | log | EXIT | count | TREE |
|---|---|---|---|---|---|
| targeted (212 files) | `run_tree.sh … logs/r43_target_1.log 300 8 $(cat target_set_r43.txt)` | `r43_target_1.log{,.xml}` | 1 | 545 failed, 11126 passed, 52 skipped, 3 xfailed | `17796957…` (HEAD b411cab, DIRTY 0) |
| both-ways node diff vs the audit's full junit at 7cc5837 | `r43_junit_diff.py logs/r43_target_1.log.xml audit66/junit/junit_1.xml` | `r43_reddiff_1.txt` | — | common 11726 · NEW red 17 (7 B1 format + 10 R34 text, every message read: format/text only) · GONE 1 (`test_text_hygiene` Tier-1 — servicer B3 `dabc671`) · RED both 528 = 527 in files registered in `pending_contracts.yaml` (58/64b-i) + 1 the B2 raw-listener orphan (servicer's, unregistered) — classified by script, not by eye | — |
| currency typecheck + ruff | `pending_contract_gate.py --currency --legs typecheck,ruff` | `r43_currency_1.log` | 1 (pytest NOT_RUN quirk only) | typecheck RED_ADJUDICATED 99 (58/64b-i) · ruff GREEN · RED_ORPHANED 0 on run legs | `17796957…` |
| structural pins at d41aa47 (92 files) | `run_tree.sh … logs/r43_structural_2.log 300 8 $(cat structural_pins.txt)` | `r43_structural_2.log{,.xml}` | 1 | 341 failed, 8140 passed, 8 skipped; diff vs the b411cab run (`r43_reddiff_structural.txt`): NEW red 0 · GONE 7 (the B1 format pins, servicer REQ-I `f8e2048`) · RED both 341 | `218d0df5…` (HEAD d41aa47, DIRTY 3 = the servicer's in-flight test files, not mine) |
| probes ×10 | `run_probe.sh <probe> logs/r9_<probe>.log` | `r9_*.log` | 0 ×10 | see R-9 table | `17796957…` |

## R44 (RULING-15, #591 + #592 leans, directive #19100) — builder, production only
Order honoured: built in my tree, then MOVED OUT (byte copies + sha256 in `build66/r44_final/`) so the shared tree sat at HEAD for the servicer's RED proof; production commits only after the pin SHA lands on q:r43-ruling15-591.
- **ONE helper** `loremaster/store/stamp_paging.py`: `read_stamp_page` (reads `limit+1` + the honest `count()` over the same predicate + one `count()` at a held stamp so `N` describes the whole group; `LIMIT` bound as a param; the caller's filter fragment ANDed into every statement), `cut_stamp_page` (the pure rule — fakes call it instead of copying it), `stamp_key` (`(instant, nanosecond)` — **measured: `PreciseDatetime ==`/`<` IGNORE ns**, `eq True, lt False` for ns 1 vs 2), `HeldStampGroup(stamp, rows)`. Stamps read through `required_datetime` (a corrupt stamp gets the R34 refusal, never a `TypeError` mid-compare). Re-open triggers to the compound cursor (a) in the module docstring, as ruled.
- **Callers**: `TaskLedger.updated_since`, `FindingLedger.filed_since`, `MessageLedger.message_activity_since` — their three hand-rolled `WHERE col > $since ORDER BY … LIMIT` + `count()` pairs are gone; `_UPDATED_SINCE_PARAM` / `_FILED_SINCE_PARAM` deleted (no test references, grep).
- **Models**: the three `*ActivityWindow` gain REQUIRED `resume_at: datetime` and REQUIRED `held_group: HeldStampGroup | None` (no defaults: the render branches on them — CLAUDE.md fixture-default law).
- **`_rollup_next_cursor`** reads `resume_at`; MIN/MAX by `stamp_key`. Same-class fix found while building (not in the ruling's text, inside its class): the old `min()`/`max()` over `PreciseDatetime`s ordered to the µs only, so two truncated legs whose resume stamps differ only in ns could pick the LATER one and skip the other leg's rows in between.
- **Headers** (strings agreed with the servicer #19102/#19103/#19105, lead-endorsed #19104): h1 task/finding held (§2 text verbatim inside the leg header; `limit` == `shown` by construction), h3 task/finding truncated (other legs re-serve rows above the elision point), h2 message truncated (not covered by the next cursor; raise limit on THIS call), h2-held message held (names N and the stamp, never claims a cursor hold — the cursor does not read the message leg, #592 Q1(ii)). Stamps render through `served_instant_text` (+ `sanitise_line` for the render seam's type).
- **§3.3 prose**: three `*_since` docstrings + the three models' `rows` doc ("at most `limit`, never ending inside a stamp group; a head group wider than `limit` holds the cursor and is named"); `_rollup_next_cursor` docstring; the `limit` schema line gains "a page may stop short of the cap to avoid splitting rows that share a stamp". The `since` schema line is unchanged, as ruled.
- **Pre-build checks**: ruff clean; `mypy loremaster` → 0 errors under `loremaster/loremaster/` (test-side window-construction errors are the servicer's fallout, agreed); pure-rule smoke (P2 shrink → {a}, P1 held → first row + resume=since + held stamp, ns-distinct µs-equal stamps NOT a tie, empty, all-fit).

### DRY ledger / registry rows (R44)
| new symbol | where I looked | disposition |
|---|---|---|
| `stamp_paging.read_stamp_page` | `lore_search("keyset paging by timestamp cursor limit plus one tie group")` → no production hit (only a surrealql-tests file); the three `*_since` bodies (the triplication RULING-15 names) | NEW, THE one rule; the three bodies become callers |
| `stamp_paging.cut_stamp_page` | same | NEW pure core of the same rule (shared with fakes) |
| `stamp_paging.stamp_key` | grep `nanosecond` over production: only `_txn`'s codec + docs | NEW; also used by `_rollup_next_cursor` |
| `stamp_paging.HeldStampGroup` | — | NEW model (the render's input) |
Not added: a 13th `_as_rows` / 4th `_extract_group_count` — the helper takes each ledger's own narrowers. **Observed, not fixed (out of this directive — your call):** `_as_rows` is hand-copied ~12× across the package and `_extract_group_count` 3× (pre-existing DRY cluster).

### R44 commit + receipts
- **`b2214d7`** — R44 production (gate: servicer pins `fb79869`, red-first 10/10 at 9f3922f). Restored from `r44_final/` with sha256 verified per file before commit.
| gate | command | log | EXIT | count | TREE |
|---|---|---|---|---|---|
| targeted (217 files: R43 set ∪ fb79869's files ∪ tests naming the changed symbols, grep) | `run_tree.sh … logs/r44_target_1.log 300 8 $(cat target_set_r44.txt)` | `r44_target_1.log{,.xml}` | 1 | 677 failed, 11053 passed, 52 skipped, 3 xfailed; **R44 pins `test_sdk3_rollup_ties_r15` 9/9 PASS** | `1dd3748c…` (HEAD b2214d7, DIRTY 0) |
| both-ways diff vs b411cab | `r43_junit_diff.py` | `r44_reddiff_1.txt` | — | NEW red 146, every message classified by script: F4 field-missing-at-construction 126 · F4 hand-built window lacks field 16 (incl. `test_render_slot_inventory` ×4, not in the servicer's list — reported) · F2 header signature 2 · F3 query-text door 1 · F7 render candidate 1 · OTHER 0. GONE 14 (servicer's B1/B2/R34 fixes). RED both 531 | — |
All 146 are the servicer-announced test-side fallout of REQUIRED fields / new render branches (#19111/#19112); none is a behaviour red. Servicing posted #19118.
- **`273bb69`** — R34 re-word (lead-approved #19110, gate `2666ade` two-shape re-pin): "… the store's other rows are intact, but this call reads that row and could not be completed — report it with lore_findings".
- **Baseline reconciliation (lead's 677 − 146 = 531 vs 530):** by node, script. RED both 531 = **527 owned** 58/64b-i reds inside my 217-file scope + **4 non-owned** `TestRollupDispatch` nodes red at both trees for DIFFERENT transient causes (b411cab: B1 format pre-REQ-I; b2214d7: `_FakeTaskActivityWindow` lacks `held_group` = F4). True R44 fallout = 146 + 4 = **150**. The audit's 530 owned = those 527 + 3 in `scripts/test_forgery_door_sweep.py` (outside my scope; RED at c503bf7). **Owned reds = 530, unchanged.**

## R43/R44 EXIT RECEIPT — one TREE, DIRTY 0 (directive: lead wake after 2c6efcf / 3f4d20a)
`receipt_r44.sh`: tree_id before → targeted pytest → `--currency --legs typecheck,ruff` → tree_id after. Before = after = `HEAD=3f4d20a` `DIRTY_FILES=0` `TREE=3fd07c54ffd6…` (logs `receipt_tree_{before,after}.txt`).
| gate | command | log | EXIT | count | TREE |
|---|---|---|---|---|---|
| targeted (219 files = R44 set ∪ `structural_pins.txt` 92 ∪ `scripts/test_forgery_door_sweep.py` ∪ 2c6efcf's test files) | `run_tree.sh … logs/receipt_target.log 300 8 $(cat target_set_receipt.txt)` | `receipt_target.log{,.xml}` | 1 | **530 failed, 11224 passed, 52 skipped, 3 xfailed** | `3fd07c54…` |
| receipt check | `receipt_check.py receipt × b2214d7 × b411cab × audit full junit` | `receipt_check.txt` | — | R44 fallout 150/150 GREEN (incl. the 4 named TestRollupDispatch nodes) · reds 530, all in registered files · **red set == the audit's owned 530, node for node** · unowned 0 | — |
| currency typecheck + ruff | `pending_contract_gate.py --currency --legs typecheck,ruff` | `receipt_currency.log` | 1 (pytest NOT_RUN quirk only) | typecheck RED_ADJUDICATED 99 (58/64b-i) · ruff GREEN · RED_ORPHANED 0 on run legs | `3fd07c54…` |
Production SHAs this wave: fda1411 (B1) · 5b4c138 (R-6) · f2327ef (R34 clause) · b411cab + d41aa47 (prose) · b2214d7 (R44) · 273bb69 (R34 re-word).

STATE: done · production b2214d7 + 273bb69 (HEAD 3f4d20a) · 530 failed / 11224 passed (= owned 530, 0 unowned), currency RED_ORPHANED 0

## R45 (RULING-16) + R46 (RULING-17) — builder, production
| commit | item |
|---|---|
| `8509e14` | S1 h3 = §S1 verbatim; `_rollup_leg_header` docstring + #592 Q2 note; `_rollup_next_cursor` docstring's same "other legs" slip in prose (lead-approved #19130) |
| `a535d2e` | S4 R34 string = §S4 verbatim + its docstring paraphrase |
| `f289f5b` | S6 `id` added to `message_activity_since`'s projection (the refusal names `message:<key>`) |
| `8289bc5` | S3 `snapshot_gc._to_aware_utc` bound + trigger verbatim (S5: no edit, as ruled) |
| `d2df34c` | R46: `read_stamp_page` docstring states the predicate once (what `> $since` admits/excludes on 3.3.5, the admin-retype door, KNOWN BOUND #597, re-open triggers, the named boot-time instrument). No render change, as ruled |
Gate: servicer pins `15a553f` (R45, 17 red-first) and `de6e116` (R46 pin-the-miss, green by design). R45 patch built out of tree and dry-run on a mirror before the pin SHA.

### R45 receipt — STRADDLED (named, per lead #19138/#19140)
`receipt_r45.sh`, 221 files = the R44 receipt set ∪ 15a553f's files ∪ tests naming the touched symbols. `r45_target.log` header: HEAD 8289bc5 DIRTY 0 TREE `927e7ddd…` (17:18:34) → after: HEAD c8cf105 TREE `4b9cbf51…`. **Count: 530 failed, 11298 passed, 52 skipped, 3 xfailed** (EXIT=1). Check (`r45_check.txt`): reds 530, all in registered files, == the audit's owned 530 node for node; R44 fallout 150/150 still green; unowned 0.
**The straddle, by path (R22 path check):** `8289bc5..c8cf105` = `de6e116` (tests only: `test_sdk3_retirement_pins_66d.py`, `test_sdk3_rollup_ties_r15.py`) + `c8cf105` (one docs row); the servicer EDITED those two files uncommitted from ~17:19 and committed at 17:25:51 (#19139). Production unchanged across the run; the other 219 files' content did not move. So the run stands for every file but those two, which the closing receipt re-runs at one TREE (lead #19140). The currency leg of this script ran at c8cf105: typecheck RED_ADJUDICATED 99, ruff GREEN, RED_ORPHANED 0 on run legs.

### CLOSING RECEIPT (R45 + R46) — one TREE, DIRTY 0
`receipt_r46.sh`: before = after = HEAD `d2df34c`, DIRTY 0, TREE `b4927866…`. Scope (lead #19140): `test_sdk3_retirement_pins_66d.py` (incl. de6e116's #597 pins), `test_sdk3_rollup_ties_r15.py`, `test_mcp_server.py`, `test_sdk3_rollup_cursor_66b1.py` + `test_text_hygiene.py` (added: a text scanner over the docstring change, said so).
| gate | log | EXIT | count | TREE |
|---|---|---|---|---|
| closing pytest (5 files, 720 nodes) | `r46_target.log{,.xml}` | 1 | **28 failed, 692 passed** — 66d 32/32, r15 14/14, rollup-cursor 3/3, text_hygiene 5/5, #597 pins 2/2 PASS; the 28 are all `test_mcp_server`, every one RED in the audit's full run at 7cc5837 (packet-64b-i's owned findings-signature reds; `r46_check.txt`) | `b4927866…` |
| currency typecheck + ruff | `r46_currency.log` | 1 (pytest NOT_RUN quirk only) | typecheck RED_ADJUDICATED 99 · ruff GREEN · RED_ORPHANED 0 on run legs | `b4927866…` |

STATE: done · production 8509e14 · a535d2e · f289f5b · 8289bc5 (R45) + d2df34c (R46) · R45 run 530F/11298P (straddled by path, 66d/r15 only) · closing receipt 28F/692P at d2df34c (28 = owned), currency RED_ORPHANED 0
