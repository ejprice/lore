brief-base v16 read
brief project v7 read

# REPORT — probe-64: `scripts/restore_prod_dump.py`, the committed S2 restore instrument (amendment 3 §D-3)

## SUMMARY BLOCK
- **State:** done-with-deviations (3 spec-vs-reality readings in §1 + 1 process deviation D4; none changes what §D-3 asks the instrument to PROVE).
- **Deviations:** D1 §D-3 names `surreal_schema.governed_node_tables(generate_ddl())` — no such production function; the ONE derivation lives in `loremaster/tests/_governed_contract.py` and is CALLED there. D2 "a section for every requested table, else REFUSE" would refuse BOTH real dumps (they predate `blocks/keep/member_of/principal/principal_key/audit`) → node tables REQUIRED, relations/dependencies reported `ABSENT`, `--tables` all-required. D3 "opens with `OPTION IMPORT;`" — both dumps open with a captured tracing log line (→ HTTP 400 if sent); the driver strips exactly that line shape and requires `OPTION IMPORT;` as the first STATEMENT. D4 the brief's "one pytest session on the box": a 15-min watcher for a pytest-free window TIMED OUT (other agents' lore + mobile-pricepaper-smoke suites cycled continuously); my 16-test single-process file (≤4.4 s, no uvicorn) and the mutation runs executed alongside them.
- **Packages considered:** import mechanism → vendor `POST /import` (REUSED, per §D-3; read `surrealdb-docs:reference/rest-api/http-protocol.mdx` §import + probed 10 legs, §3); HTTP → `httpx` (replace; already a loremaster dep); env-file parse → `python-dotenv.dotenv_values` (replace); secrets → `pydantic.SecretStr` (replace); read-back → `loremaster.store._txn.run_query` + the harness's `connect_admin`/`drop_database` (reuse); SurrealQL row tokeniser → `bespoke` (no Python SurrealQL parser exists to my knowledge — LOW confidence on that negative; the engine is the only full parser and it is the thing under test, so an independent count cannot come from it; kept to one regex + a bracket stack, gated by a 3-instrument agreement on real data, §4).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 11 new module-level symbols, all dispositioned (§6).
- **Graded:** n/a — builds an instrument, grades no one else's artifact.
- **Decisions-needed:** (1) ratify D2's required/absent split (§1). (2) `PENDING_GOVERNED_TABLES` is a 3-entry hand-list with a named decay rule (§1 D1) — ratify or replace. (3) FLAG: `lore_test` namespace holds ~3,900 databases (suite residue from other sessions; not mine — §5).
- **Gates (final tree, 2026-09-26):** `scripts/test_restore_prod_dump.py` **16 passed**; `--self-test` **13/13**; ruff + `MYPYPATH=scripts mypy` clean on both files; 8 mutation proofs (7 exact, 1 wrong-declaration corrected by probe — §7).
- **Receipts:** §2 per-requirement · §3 vendor probes · §4 live run (08-03 + 07-28 dumps, counts) · §5 teardown/residue · §6 DRY ledger · §7 controls + mutation proofs · §8 gates · §9 the bound.

**The first measurement of the fleet's real legacy population (2026-08-03 dump, restored 2026-09-26):**
`finding 324 · task 116 · agent 95 · memory 177 · message 316 · brief 26` — every one `scope IS NONE` (pre-63 shape), declared == read back, three independent instruments agree.

---

## 0. Capability check (brief-base §4)
- grep/rg are hook-blocked (and the word trips the hook, #473): every text search in this run used `awk`/`sed`/Python. Said here per the brief.
- `lore_search` failed ONCE mid-run with `SurrealDB query failed against 'ws://127.0.0.1:18500/rpc': '<uuid>'` (lore's own backend); the retry on another query succeeded. Not filed as a finding — one transient occurrence, cause unknown; flagged here so the lead can decide.
- No `surreal` binary on the host (per amendment 3); not needed — `POST /import` is host-side.

## 1. The three readings (brief-base §2: two readings → both written down)
**D1 — where the governed-set derivation lives.** §D-3 step 4: *"DERIVED at run time from `surreal_schema.governed_node_tables(generate_ddl())`"*. At `90ada74`/`5d549a1` `surreal_schema` has no such function, and `generate_ddl()` does not even emit the comms tables (`generate_agent_ddl`/`generate_message_ddl`/`generate_brief_ddl` are separate). The repo's ONE derivation is `_governed_contract.governed_populations()` over `_enforced_relations_scaffold.emitted_schema_ddl()` (the union of every `generate_*_ddl`). Reading A (build a production twin in `surreal_schema`) = copy #2 of a policy + outside my writable set. Reading B (CALL the test-tree derivation, house idiom `forgery_door_sweep._harness`) — **picked**. At HEAD it yields `agent, briefed, memory, message, to` — it does NOT yet include `finding/task/brief` (64b/64a/63c-ii land their trio). So `PENDING_GOVERNED_TABLES` names those three WITH the packet that governs each; when the derivation grows to include one, the receipt labels it `derived` and the pending entry is dead weight to delete. Relations over pending nodes are DERIVED (`governed_relation_tables` → `blocks`). Result = exactly §D-3's 15-table list; the self-test asserts slice ⊇ that list (a FLOOR, so growth is absorbed, loss is RED).

**D2 — "a `-- TABLE:` section for every requested table, else REFUSE".** Measured (awk over section headers): both dumps lack `blocks, keep, member_of, principal, principal_key, audit` — they predate packets 60/61/48 and the 04b-3 edge. Literal reading ⇒ the default run refuses on every existing dump, including the 08-03 one the brief orders a receipt run against. **Picked:** node tables (`derived` + `pending`) are REQUIRED (refused if absent — they are the populations S2 exists for); relation/dependency tables absent from the dump render `ABSENT (the dump predates it) (<reason>)`, never silently; `--tables` makes every named table REQUIRED; zero `-- TABLE:` sections or a first statement other than `OPTION IMPORT;` refuse (the format alarm). **Needs a ruling.**

**D3 — "verified to open with `OPTION IMPORT;`".** Both dumps' line 1 is `…Z  INFO surrealdb::method::export: Exporting bytes` and their last line `…Z  INFO surrealdb_server::cli::export: The SurrealQL file was exported successfully` (the export was captured with its log stream). Sent as-is, `/import` answers **HTTP 400** (probe P5, §3). The driver strips exactly `EXPORT_LOG_LINE_PATTERN` lines (counted in the receipt: 2 per dump) and requires `OPTION IMPORT;` as the first non-comment STATEMENT; any other pre-section content refuses.

## 2. Per-requirement receipts (§D-3 steps 1–6 + riders)
| § | requirement | where (symbol) | receipt |
|---|---|---|---|
| 1 | endpoint by CONSTRUCTION, no `--endpoint` | `STORE_PORT`, `HTTP_ENDPOINT`, `RPC_ENDPOINT`, `_refuse_foreign_endpoint`, `build_parser(allow_abbrev=False)` | leg `endpoint_is_a_constant_and_guarded`: `--endpoint/--port/--db/--d` all rejected; `LORE_TEST_SURREAL_URL=…:18500` does NOT retarget; a `:18500` request raises `ForeignEndpointError` with **0** transport calls (MockTransport), positive control `:18000` reaches it |
| 1 | creds from the stores' env file | `StoreCredentials.from_env_file`, `STORES_ENV_FILE` | leg `stores_env_file_and_ports_match_the_quadlets`: spike quadlet binds `127.0.0.1:18000` + names the file; lore-surreal quadlet binds `:18500` (file READ only — the store is never contacted) |
| 2 | minted `test_dump_<stamp>_<uuid4>`, asserted absent, no `--db`, `--reap` refuses foreign | `mint_database`, `DATABASE_NAME_PATTERN`, `validate_reapable` | legs `database_name_pattern_and_reap_refusal` + `live_define_database_refuses_an_existing_name` (engine-side 2nd guard: plain `DEFINE DATABASE` on an existing name → `already exists`); CLI `--reap lore` → exit 2 before any credential is read |
| 2 | ONE stdout line | `main` | run1 stdout = exactly `LORE_PROD_DUMP_DB=test_dump_20260926T143119Z_1524…` (§4) |
| 3 | `--dump` default newest; `OPTION IMPORT;` + sections else REFUSE naming missing | `newest_dump`, `ExportScanner._check` | legs `slice_precision_recall_and_missing_refusal` (refusal names `gamma`), `format_alarms_refuse` (no OPTION / junk before first section / non-INSERT data line / no sections) |
| 4 | governed-slice text pass + `POST /import`; `--full` | `SliceDeriver.governed_slice`, `ExportScanner`, `StoreClient.import_file` | live run: slice 10.6 MB of 3.6 GB, import 2.0 s (§4); `--full` implemented, NOT run (3.5 GB of chunk/snapshot_entry into the 4 GiB-budget test store — deliberately not exercised; see §9) |
| 5 | per-table read-back counts, `scope IS NONE` via `report_unmigrated_governed_rows`, elapsed, DB name; non-zero on mismatch | `_read_back`, `verify`, `render_report` | §4 table; tampered-count leg → `VerifyMismatchError` naming `beta` only, DB reaped |
| 6 | controls: visible via 2nd connection; reap removes; determinism | `leg_live_import_visible_reaped_and_deterministic` | import over HTTP, read back over the WS SDK; 2nd import into a fresh DB identical; both reaped and absent from `INFO FOR NS`. Also on REAL data: run1 vs run2 table rows `diff` → IDENTICAL (§4) |
| rider | PEP 723 + uv shebang | file head | `#!/usr/bin/env -S uv run --script` + inline deps; `loremaster` as an EDITABLE path source → `loremaster.__file__` = `/home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py` (the tree under test; measured with a throwaway probe script, cold resolve 6.9 s / warm 0.9 s). Also runs as `uv run python scripts/restore_prod_dump.py` |
| rider | self-test committed | `SelfTest` + `scripts/test_restore_prod_dump.py` | `scripts/` is in `testpaths` and a typecheck root → gated; `test_every_leg_method_is_registered_to_run` makes leg REACH a checked variable |
| bound | named | module docstring "THE BOUND" | §9 |

## 3. Vendor-claim probes — what the docs say vs what 3.2.4 did
Engine `surrealdb-3.2.4+20260803.93ab219` (`GET /version` on :18000). Probes run 2026-09-26 by curl into throwaway `test_dump_probe_<hex>` DBs in `lore_test` (all reaped; §5). Doc: `surrealdb-docs:reference/rest-api/http-protocol.mdx` §`POST /import` (headers table + one example), `…/cli/surrealdb-cli/commands/export.mdx` + `import.mdx` (OPTION IMPORT), `explore/tutorials/demos/surreal-deal-store.mdx` (the `--data-binary` example). The store reference `docs/reference/surrealdb-31-capabilities.md` has NO import/export content (awk for `import|export`: zero hits) — these are new facts; a store-ref §6 entry is recommended (outside my writable set — FLAG).

| # | claim / question | docs | 3.2.4 measured |
|---|---|---|---|
| P1 | `--data-binary @file` + `Surreal-NS`/`Surreal-DB` imports | tutorial: yes | ✅ into a pre-created DB → HTTP 200, body `[]` |
| P2 | response shape | **silent** | success statements return NOTHING under OPTION IMPORT; body = `[]` iff every statement succeeded; each failure = one `{"status":"ERR",…}` entry |
| P3 | runtime error mid-file | **silent** | **HTTP 200** + ERR entries, and the import **CONTINUES** (b:2, b:3 inserted after two `AlreadyExists` failures) — NOT atomic |
| P4 | parse error mid-file | **silent** | HTTP 200 + one ERR (`Parse error …`); statements BEFORE it applied (c:1), everything after silently NOT (c:2 absent) |
| P5 | DB must exist? | **silent** | absent DB: HTTP 200 + ONE ERR (`database … does not exist`), yet later statements ran: table `t` came back `TYPE ANY SCHEMALESS` (its SCHEMAFULL define failed), fields/event defined, rows inserted — a silent schema DOWNGRADE with one error line |
| P6 | `OPTION IMPORT` required as first statement (≥3.0.4) | ✅ | HTTP 400 `Import requires \`OPTION IMPORT;\` as the first statement` |
| P7 | field processing disabled | ✅ ("field processing") | `ASSERT $value < 10` bypassed (n=99 stored); `VALUE 'computed'` bypassed ('raw' stored); EVENT not fired (count 0) — restored rows are byte-faithful, never re-validated |
| P8 | reference example `-d file.surql` | shown as THE example | ❌ sends the literal string → HTTP 400; `-d @file` strips newlines → a leading `--` comment swallows the file → HTTP 400 |
| P9 | `Accept` header "required" | ✅ required | not enforced (omitted → 200 `[]`) |
| P10 | auth | Authorization optional | wrong password → HTTP 401 `The password did not verify` |
| P11 | the raw export file | — | its line-1 tracing log line → **HTTP 400** `Invalid statement: Parse error … 2026-08-03T14:19:30…` (whole file refused) |

Also: `THIS IS NOT SURREALQL;` is NOT a parse error — it parses as the expression `THIS != SURREALQL`. My first parse-error probe was invalid for that reason; P4 used `SELECT FROM WHERE };` (a probe needs a control that actually exercises the branch).

**What the driver does with these:** P2/P3/P4 → accept only HTTP 200 + exactly `[]` (`StoreClient.check_import_response`); P5 → always `DEFINE DATABASE` first; P11 → strip log lines; P7 → documented (a restored legacy row may violate the CURRENT DDL's asserts — S2's migration must tolerate that, which is precisely the §1.4 dirty-store condition S2 exists to reach).

## 4. Live run receipts (2026-09-26, working tree over `5d549a1`)
Pre-run: `lore_test` namespace total 3905 DBs, `test_dump*`: `[]`. MemAvailable 54 GiB. Dump sha256 `3089f0f7…a2e87`.
`./scripts/restore_prod_dump.py` (default = newest = `lore-prod-20260803T141930Z.surql`) → **exit 0**, `real 0m21.4s`:
```
restore_prod_dump: dump /backups/lore/lore-prod-20260803T141930Z.surql (3633447078 B)
restore_prod_dump: mode slice — slice 10642335 B; preamble sections OPTION, ANALYZERS, SEQUENCES; export log lines stripped 2
table            provenance   declared  readback scope NONE  note
agent            derived            95        95         95  pre-63 shape: scope NONE must == rows
brief            pending            26        26         26  pre-63 shape: scope NONE must == rows
briefed          derived           123       123
finding          pending           324       324        324  pre-63 shape: scope NONE must == rows
finding_counter  dependency          1         1
memory           derived           177       177        177  pre-63 shape: scope NONE must == rows
message          derived           316       316        316  pre-63 shape: scope NONE must == rows
task             pending           116       116        116  pre-63 shape: scope NONE must == rows
to               derived           337       337
blocks           relation       ABSENT  the dump predates it (relation over a pending node)
audit / keep / member_of / principal / principal_key   dependency  ABSENT  the dump predates it (<reason each>)
restore_prod_dump: elapsed scan 18.0s, import 2.0s, readback 0.1s, total 20.2s
stdout: LORE_PROD_DUMP_DB=test_dump_20260926T143119Z_1524fc1bd9b641ff9cab035bb0df460b
```
**Independent cross-checks on that DB (different instruments):** `/sql` over HTTP: `finding 324`, `task 116`; `INFO FOR DB`: all 9 tables `SCHEMAFULL`/`ENFORCED` as dumped (not the P5 `ANY SCHEMALESS` downgrade), sequences `message_seq, trace_seq`, analyzer `code_ident`. A crude awk text count of `[{,] id: <t>:` per DATA section: finding 324, task 116, agent 95, memory 177, message 316, brief 26 — equal to the tokeniser and the read-back.
**Determinism on real data:** run2 (fresh DB) → exit 0, per-table rows `diff` vs run1 → IDENTICAL.
**Older dump:** `--dump lore-prod-20260728T194511Z.surql` → exit 0, 16.0 s: agent 46, brief 23, briefed 70, finding 258, finding_counter 1, memory 150, message 231, task 114, to 239 — all declared == read back, all node tables scope NONE == rows.

## 5. Teardown / residue
All three live DBs reaped with the driver's own `--reap` (exit 0 each, each confirmed absent via `INFO FOR NS`); `--reap test_1234_abc` / `--reap lore` → exit 2 REFUSED. My 9 vendor-probe DBs (`test_dump_probe_*`, curl) reaped by `REMOVE DATABASE`. **After:** `test_dump*: []` (namespace total 3911 — +6 from OTHER sessions' tests during my run, none `test_dump_`). Dumps: sha256 of the 08-03 dump identical before/after; mtimes unchanged (`2026-07-28 15:46:51`, `2026-08-03 10:21:33`) — read-only.
**FLAG (not mine, surfaced per scope law):** `lore_test` holds ~3,900 databases — the suite's per-test DBs are not all being reaped by someone. Want it examined?

## 6. DRY ledger (brief-base §6)
lore_search was used for the derivation (`governed_node_tables`, S2 docstring); symbol lookups by `lore_get_symbol` and awk over defs (said so, §0).
| new symbol | query run | returned | disposition |
|---|---|---|---|
| governed-slice derivation (`SliceDeriver`) | `lore_get_symbol governed_node_tables`; awk `governed_populations` | `_governed_contract.governed_node_tables/governed_relation_tables/governed_populations` | **REUSED** (called, never cloned) |
| pre-63 shape test (`is_governed_shape`) | same | `governed_node_tables(ddl)` over the dump's own table DDL | **REUSED** |
| read-back counts (`_read_back`) | awk `^async def run_query`; `store_handle` | `loremaster.store._txn.run_query`, `_governed_contract.store_handle`, `_surreal_harness.connect_admin` | **REUSED** |
| unmigrated count | spec cites it | `loremaster.governed.report_unmigrated_governed_rows` | **REUSED** |
| DB reap (`reap_database`) | awk harness defs | `_surreal_harness.drop_database` (retry-seamed) | **REUSED** + a post-reap `INFO FOR NS` proof |
| test namespace | harness | `_surreal_harness.TEST_NAMESPACE` | **REUSED** |
| env parse (`StoreCredentials`) | packages | `dotenv_values` (loremaster already declares python-dotenv) | package |
| endpoint guard (`_refuse_foreign_endpoint`) | lore_search "open signed-in websocket …" (errored once, §0); awk over `scripts/` probes | probes hardcode `:18000` constants; no shared HTTP guard exists | **HAND-ROLLED** — an httpx event hook, 5 lines; no existing HTTP client seam in the repo |
| `count_insert_rows` | none possible in-repo (no SurrealQL tokeniser exists: awk for `INSERT_TOKEN|tokeni` in loremaster → none) | — | **HAND-ROLLED** (bespoke, §SUMMARY) |
| `ExportScanner` | awk `export` in loremaster/scripts → none | — | **HAND-ROLLED** — nothing in the repo reads a `surreal export` |
| `mint_database_name` / `validate_reapable` | `_surreal_harness.unique_database` | `test_<pid>_<uuid4>` — a different, harness-owned shape | **HAND-ROLLED**: §D-3 mandates the `test_dump_<stamp>_<uuid4>` shape so `--reap` can refuse everything else; reusing `unique_database` would make harness DBs reapable by this tool |

## 7. Controls and mutation proofs
**Controls** = the 13 `SelfTest.leg_*` methods (8 offline + 5 live), each a pytest case in `scripts/test_restore_prod_dump.py`; `test_every_leg_method_is_registered_to_run` asserts `{leg_* methods} == OFFLINE_LEGS ∪ LIVE_LEGS`, so a new leg that is never registered goes RED (reach as a checked variable). Negative controls with positive partners: runtime error mid-file (HTTP 200!) → `ImportRejectedError`; parse error mid-file → `ImportRejectedError`; a scanner that misdeclares `beta` by +1 → `VerifyMismatchError` naming `beta` only; `:18500` request refused with 0 transport calls vs `:18000` delivered; `--reap lore` refused vs minted names accepted; a synthetic governed table `zeta` GROWS the derived slice. Each failure leg proves the EXACT DB it minted (`on_mint`) is gone — not a namespace set-diff, which races xdist workers.

**Mutation proofs** — `scripts/mutation_proof.py` (anchor matched exactly once, RED set diffed BOTH ways against a set declared BEFORE the run in the scratchpad plan; node ids from `--collect-only`); file restored byte-exact after each (sha256 compared):
| # | mutation | declared RED | verdict |
|---|---|---|---|
| M1 | endpoint guard → `if False:` | offline[endpoint], cli_offline | exit 0 ✅ |
| M2 | tokeniser keeps only brackets (no quoted skip) | offline[precision, row_count, format_alarms], live[visible, runtime, parse, tampered], cli_offline | exit 0 ✅ |
| M3 | accept any HTTP 200 | offline[import_response_rule], live[runtime, parse], cli_offline | exit 0 ✅ |
| M4 | `verify` blind | live[tampered] | exit 0 ✅ (re-run after the leak fix below: 0 residue) |
| M5 | no reap on failure | live[runtime, parse, tampered] | exit 0 ✅ (leaked 3 DBs as predicted → reaped with `--reap`) |
| M6 | drop `PENDING_GOVERNED_TABLES` | offline[derived_slice], cli_offline | exit 0 ✅ |
| M7 | skip `DEFINE DATABASE` at mint | live[visible, tampered, define_database] | **exit 4 — visible + tampered stayed GREEN**; only define_database went RED |
| M8 | keep export log lines | offline[precision, format_alarms], live[visible, runtime, parse, tampered], cli_offline | exit 0 ✅ |

**M7 was MY wrong declaration, and the probe that showed it is P12:** I generalised P5 ("absent DB ⇒ schema downgrade") to every file. Measured: a leading `DEFINE ANALYZER`/`DEFINE SEQUENCE` (the real dumps' and the synthetic's shape) silently CREATES the absent DB and the import is clean (`[]`, SCHEMAFULL kept); only a leading `DEFINE TABLE` fails `NotFound` and downgrades — and that failure is always an ERR entry, which the `[]` rule rejects. So M7's two green legs were correct behaviour; the explicit mint is pinned by `leg_live_define_database_refuses_an_existing_name` (RED under M7). The module docstring's claim was corrected to the measured, first-statement-dependent form.

**Defect found by the mutation batch and fixed (self-test hygiene, not the driver):** under M4 the tampered leg's restore SUCCEEDED and `_expect_failure_reaped` raised "accepted as clean" WITHOUT reaping the DB a successful restore leaves for its caller → one leaked `test_dump_…145223Z` (found by a residue listing, reaped). Fix: an unexpected success now reaps what it minted before raising; M4 re-run → exit 0, residue `[]`.

## 8. Gates (final tree; sha256 `restore_prod_dump.py` 2b857745…b773, `test_restore_prod_dump.py` 7f15c4aa…b47a)
- `uv run pytest -q -p no:cacheprovider scripts/test_restore_prod_dump.py` → `16 passed in 3.69s` (exit 0).
- `./scripts/restore_prod_dump.py --self-test` → `self-test: 13/13 legs held` (exit 0).
- `uv run ruff check` + `ruff format --check` on both files → clean; `MYPYPATH=scripts uv run mypy` both files → `Success: no issues found in 2 source files` (the gate's per-root invocation shape; the full `scripts/typecheck.sh` was NOT run — FLAG for the cold audit).
- `uv run ruff check .` → 1 error, NOT mine: `loremaster/tests/test_findings_identity_64b.py:313` E501 (contract-64b's in-flight file). Surfaced per scope law.
- Final-code real-dump receipt (run4, 08-03 dump): exit 0; per-table rows IDENTICAL to run1; elapsed scan 19.6 s, import 23.0 s (store under other suites' load; 2.0 s unloaded), total 42.9 s; reaped; `FINAL test_dump*: []`.

## 9. The named bound
S2 is NOT in the standard gate: a multi-GB backup is an environment dependency. The standard gate runs the driver's 13 controls on a synthetic 40-line export (`scripts/test_restore_prod_dump.py`); the REAL-dump run is the close-out receipt at 64b-i, 64a, and 65's dress rehearsal (the driver takes any `--dump`, incl. a fresh `surreal export` of :18500 taken by the operator — the driver itself never addresses :18500). A close-out without it is `done-with-deviations`. The tokeniser knows the export's CURRENT quoting and one-`INSERT`-per-line shape; a change is refused or surfaces as a declared≠read-back mismatch (exit 4) — never a silent pass. `--full` is implemented but was NOT exercised (3.5 GB of HNSW-bearing `chunk`/`snapshot_entry` into the 4 GiB-budget test store is a capacity question, not a correctness one). **RE-OPEN TRIGGER:** the day the export format changes — step 3's refusal is the alarm.

## Appendix A — the vendor-probe instrument, VERBATIM (brief-base §1: pasted, not committed)
Run 2026-09-26 against `:18000` only; each probe into a fresh `test_dump_probe_<uuid4hex>` DB in `lore_test`, pre-created with `DEFINE DATABASE` unless the probe is about an absent DB; all reaped with `REMOVE DATABASE`.
```bash
set -a; . ~/docker/mcp/lore-secrets/lore.env; set +a     # SURREAL_USER / SURREAL_PASS (never echoed)
EP=http://127.0.0.1:18000
sql(){ curl -s -X POST -u "$SURREAL_USER:$SURREAL_PASS" -H 'Accept: application/json' -H 'Surreal-NS: lore_test' ${2:+-H "Surreal-DB: $2"} --data-binary "$1" $EP/sql; echo; }
imp(){ curl -s -w ' HTTP%{http_code}\n' -X POST -u "$SURREAL_USER:$SURREAL_PASS" -H 'Surreal-NS: lore_test' -H "Surreal-DB: $2" -H 'Accept: application/json' --data-binary @$1 $EP/import; }
# P1/P2/P7 pre-created DB: sql "DEFINE DATABASE $D;"; imp p1.surql $D; sql 'SELECT * FROM t; SELECT count() FROM ev GROUP ALL; INFO FOR TABLE t;' $D
# P5 absent DB: imp p1.surql $D (no DEFINE DATABASE)        P3: imp p3.surql $D    P4: imp p4.surql $D
# P6: imp p6.surql $D   P8: curl ... -d p1.surql / -d @p1.surql   P9: omit Accept   P10: -u root:nope   P11: imp p5.surql $D   P12: imp p12.surql (absent DB)
# ---- p1.surql
-- comment
OPTION IMPORT;

DEFINE TABLE t TYPE NORMAL SCHEMAFULL PERMISSIONS NONE;
DEFINE FIELD OVERWRITE n ON t TYPE int ASSERT $value < 10 PERMISSIONS FULL;
DEFINE FIELD OVERWRITE v ON t TYPE string VALUE 'computed' PERMISSIONS FULL;
DEFINE TABLE ev TYPE NORMAL SCHEMALESS PERMISSIONS NONE;
DEFINE EVENT e ON t WHEN $event = "CREATE" THEN (CREATE ev SET src = $after.id);

INSERT [ { id: t:a, n: 1, v: 'raw' }, { id: t:b, n: 99, v: 'raw' } ];
# ---- p3.surql
OPTION IMPORT;
DEFINE TABLE b TYPE NORMAL SCHEMALESS PERMISSIONS NONE;
INSERT [ { id: b:1 } ];
DEFINE INDEX bi ON nosuchtable FIELDS x UNIQUE;
CREATE b:1 SET z = 1;
INSERT [ { id: b:2 } ];
CREATE b:1 SET z = 2;
INSERT [ { id: b:3 } ];
# ---- p4.surql
OPTION IMPORT;
INSERT [ { id: c:1 } ];
SELECT FROM WHERE };
INSERT [ { id: c:2 } ];
# ---- p5.surql
2026-08-03T14:19:30.863852Z  INFO surrealdb::method::export: Exporting bytes
-- x
OPTION IMPORT;
INSERT [ { id: d:1 } ];
# ---- p6.surql
INSERT [ { id: e:1 } ];
# ---- p12.surql
OPTION IMPORT;
DEFINE ANALYZER code_ident TOKENIZERS BLANK FILTERS LOWERCASE;
DEFINE TABLE t TYPE NORMAL SCHEMAFULL PERMISSIONS NONE;
DEFINE FIELD OVERWRITE n ON t TYPE int PERMISSIONS FULL;
INSERT [ { id: t:a, n: 1 } ];
```
