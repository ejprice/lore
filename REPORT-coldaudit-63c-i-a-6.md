brief-base v18 read · brief project v7 read

# REPORT-coldaudit-63c-i-a-6 — FINAL cold audit of 63c-i-a (`b15c06b0`, am-37 §13.3 / §13.4 / §13.4.1 / §13.4.2)

## SUMMARY BLOCK
- **VERDICT: GO.**
  - No BLOCKER or MAJOR.
  - Every §13.3 item 1–9, §13.4, §13.4.1 and §13.4.2 clause holds by construction and receipt (§1).
  - **The owed mutation proofs are DONE: 9/9 KILLED** (§3), A–E re-pointed (E = the §13.1 one-derivation) plus F1a/F1b (F-1 narrowing), F2 (drop `addFilter`) and G (the report validator back on the migrate set).
  - Live mint collision: 0 hex runs and no exact hash on stderr; the control shows both (§2a). The wrong-shaped verify still denies 500/401 with 0 leaks (§2b).
  - Real-dump restore completes with scope-NONE for all 6 governed tables, then is reaped and proven absent (§4).
  - Targeted 75 files: **327 failed / 5404 passed, owned 327, ORPHAN 0**, no 63c pin red (§5).
  - ruff clean; typecheck 83 = prev's IDENTICAL set; currency RED_ORPHANED 0 (§6).
  - Four MINOR residuals (#529–#532) + NITs (§R).
- **state:** done-with-deviations
- **deviations:** (1) the restore read-back (§4) ran concurrently with the targeted pytest run (§5), not after it. It ran no pytest and used its own minted DB. (2) I also ran the §13.2 rider receipt (§4b), which spec §13.3's delta-audit scope names and my brief did not. (3) My first reap-check RE-CREATED a reaped probe DB, because the SDK's `use()` auto-creates a database (measured). I removed it and proved absence with a control (§3a). (4) Mutation A's both-ways diff reported 1 undeclared extra red, a sibling lifecycle pin (§3). It was killed correctly; the gap was in MY declaration.
- **Packages considered:** none — no mechanism specified (a grader; the probes reuse the SDK, the gate's own registry, and `scripts/mutation_proof.py`).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none (no production symbol introduced; the instruments are pasted in §A).
- **Graded:** `9e99fc2` + patch `b15c06b054e661ae9c591d1151ddc257` · HEAD-at-report: `28bde55` · DIFFERENT (2 docs-only commits: `REPORT-blindreader-63c-i-a-6.md` + `REPORT-lead-63c.md`; `git diff --stat 9e99fc2 28bde55 -- loremaster scripts docs/reference` is empty; `git apply --check --cached` of the patch at `28bde55` is OK)
- **New findings (all MINOR, so residuals by the operator cap):**
  - **#529** the SET scanner NARROWS on a `/* WHERE */` block comment (F-1's class; latent; pre-existing door);
  - **#530** the unmigrated-rows line's "(member-invisible until migrated)" is FALSE for the 3 PENDING tables;
  - **#531** `_LANDED_SHAPE_FAULT`'s "a re-run is idempotent" is false for CREATE / mint (spec-originated);
  - **#532** a real restore never serves the pending remedy line: `main()` sets the logger to ERROR, and the pin passes only via `caplog.at_level` (test-fiction class).
  - Plus 5 NITs (N-a–N-e) and observations R-6–R-8 (§R).
- **decisions-needed:** (a) #532: either the restore receipt renders the remedy itself, or the §13.4.2 rider is satisfied by `lore-adm report-unmigrated` alone (it is, live, §4c). The lead/operator rules; the operator cap makes it a residual either way. (b) Ledger #529–#532 + the NITs as residuals.
- **receipt pointers:** §0 setup · §1 construction · §2 live receipts · §3 mutations · §4 restore · §5 targeted run · §6 gates · §7 NL sweep · §R residuals · §W gate waits · §A instruments.

## §0 Capability check / setup (2026-10-01, spawn 03:36:05Z; hard deadline 05:26Z + memory-gate waits)
- **Capability:**
  - `lore_comms` registered `coldaudit-63c-i-a-6` (session `63c-20260924`, role audit, cadence ≤20m).
  - grep/rg are hook-blocked (#473), so every sweep is `awk`/AST.
  - `lore_impact` caps covering tests at 15 (#518), and lore indexes the MAIN tree, not my copy. So the covering set is **AST-derived** (§A.1 `cover6.py`) — a fallback, said out loud. It is a known shape (#518/#507), with nothing new to file.
  - Nothing demanded was unavailable.
- **Base:** `git fetch` done. Main HEAD at spawn was `d9b79be`; the copies were cut at `9e99fc2` (one lead docs commit, `REPORT-lead-63c.md` only).
- **Patches:**
  - `r7.full` md5 **`b15c06b054e661ae9c591d1151ddc257`** ✅ (26 files);
  - `r5.full` md5 **`bec291900a49c2e5df0704ef912fd5b9`** ✅.
- **Trees.** Each was built with `scripts/scratch_copy.sh` → `git reset --hard HEAD && git clean -fd` → `git apply`. `loremaster.__file__`, printed in each:
  - `final` = `…/9d4cb5b8-…/scratchpad/final/loremaster/loremaster/__init__.py` (26 paths in `git status`);
  - `prev` = `…/scratchpad/prev/loremaster/loremaster/__init__.py` (20 paths);
  - `mut` = `…/scratchpad/mut/loremaster/loremaster/__init__.py` (26 paths).
- **Delta `prev → final`** (`diff -rq`):
  - production: `governed.py`, `keeps.py`, `logging_setup.py`, `principal_keys.py`, `principals.py`, `scripts/restore_prod_dump.py`;
  - tests: `_logging_fixtures.py`, `test_secret_leak_vectors.py`, and the new `test_am37_13_3_63c_i_a.py` + `test_am37_13_4_63c_i_a.py`;
  - `scripts/pending_contracts.yaml` is UNCHANGED between the two builds.

## §1 Construction — §13.3 items 1–9, §13.4, §13.4.1, §13.4.2 (code read in `final`; the builder's tables were not used as evidence)
Instrument: §A.2 `construct6.py` (AST, independent).

| clause | construction (symbol) | receipt |
|---|---|---|
| 1 F-1 ONE depth+quote-aware scanner, complete-or-raise | `principals._SetClauseScanner` is a single char loop. One bracket stack over `()[]{}` (a mismatched closer raises) and one quote state with backslash escape are tracked together. `SET` opens the clause at depth 0 outside a string; `WHERE/RETURN/TIMEOUT/PARALLEL` (`_SET_CLAUSE_END_KEYWORDS`, whole-word, case-insensitive) end it, and `,` splits it, only there. At the end it RAISES on an open quote / open bracket / no SET, and per item on a non-`<ident> op= <value>` (`_SET_ITEM`). The regex end-split `_SET_CLAUSE_START/_END` is retired (AST: 0 hits). | Mutations F1a/F1b (§3). Corpus pin green (§5). **Beyond-corpus probe (§A.3): 13/14 shapes EXACT or RAISE; `/* WHERE */` → SUBSET → #529.** The prev parser fails 8 of the same 14. |
| 2(i) `RedactingFilter` on the CLI sink | `_cli_logging`: `handler.addFilter(RedactingFilter())` (AST: the one call) | mutation F2 (§3); live §2a |
| 2(ii) public `scrub_text`, one name | `logging_setup.scrub_text` is public; `_scrub_text` has **0** hits in package + scripts. `_fault_line` calls `scrub_text(str(error))` and `scrub_text(str(cause) or …)`. The filter, `_scrub_value` and `scrubbed_exception_text` all call it. | §2a control leg (identity at both bindings shows the hash) |
| 2(iii) the 128-hex rule | `_CREDENTIAL_HASH_RE = (?<![0-9A-Fa-f])[0-9A-Fa-f]{128,}(?![0-9A-Fa-f])`, applied LAST in `scrub_text`; bound + re-open trigger written at the constant | live §2a: scrubbed 0 runs / exact hash absent; control 2 runs / exact hash present |
| 3 #527 seen-set, `__cause__` only | `_fault_line`: `seen = {id(error)}`, `while cause is not None and id(cause) not in seen`; no `__context__` read | the 2-cycle / plain-chain / context-not-walked pins green (§5) |
| 4 + §13.4 ONE validator, two derived domains | `governed.validate_governed_table(table, *, domain, verb)` raises `GovernedTableRefusedError(ValueError)`. Three call sites (AST): `governed.py` `report_unmigrated_governed_rows` (domain `governed_tables()`, before I/O); `principals._dispatch_report_unmigrated` (domain `governed_tables()`, before any store is built); `principals._migrate_table_refusal` (domain `_MIGRATE_VALID_TABLES`). `_is_governed_table` is retired (0 hits). | mutations C, G (§3); live §4c (`principal` refused, exit 1; six tables accepted) |
| 5 F-3 `rows_of(…, landed=)` + ONE template | `rows_of(result, *, noun, landed=False)` → `_shape_fault` → `_LANDED_SHAPE_FAULT` | population pin green (§5); prose → #531 |
| 6 F-5 remedy derived | `report_unmigrated_governed_rows`: PENDING entry → reason + packet; `∈ _MIGRATING_TABLES` (= `tuple(_MIGRATE_LEGS)`, the dispatch's own keys) → the migrate verb; else "no migrate verb accepts" | live §4c, all six tables |
| 7 F-6 `noun` required | Both wrappers are `_as_rows(result, *, noun, landed=False)`. AST over the whole package: every `rows_of`/`_as_rows`/`map_of`/`group_all_count` call in principals/principal_keys/keeps/governed names `noun=` (0 missing in-domain). | the 76 noun-less `_as_rows` calls are the six OTHER stores' private `_as_rows` (briefs, agents, messages, diff, tasks, findings, + floor_calibration, memory/local, store/surreal, lease, surreal_manifest), which do not delegate to `rows_of` — outside §13.3's ruled domain; builder's ONE-IMPLEMENTATION observation, residual R-6 |
| 8 F-7 `GovernedStatementError` outside the tuple | `class GovernedStatementError(RuntimeError)`. `_dispatch`'s only handler: `(PrincipalStoreError, PrincipalKeyStoreError, KeepStoreError, SurrealStoreError, ValueError)`. | AST; pins green; mutation F1a's declared traceback pin (§3) |
| 9 NITs #19/#21/#31 | "(above)"; the message-leg comment states the F-4 fact; `_not_supported` derives "today:" from `_MIGRATING_TABLES` and the list from the validator's refusal | live: `bogus` → "…its tables are `agent`, `brief`, `memory`, `message` (`brief`'s backfill lands at packet 63c-ii)…"; `brief` → "…lands at packet 63c-ii (today: `memory`, `agent` and `message`)…" |
| §13.4.1 NO `scripts` import in the package | AST over all **75** modules under `loremaster/loremaster/`, every `Import`/`ImportFrom` (any depth, any alias) plus `import_module`/`__import__`/`run_path`/`spec_from_file_location` string args. | **0 hits.** The builder's AST pin + positive control are green (§5). |
| §13.4.2 governed set | `governed_tables() = ddl_governed_tables() ∪ PENDING_GOVERNED_TABLES` (a `MappingProxyType`; each entry carries `reason` + `owning_packet`: brief 63c-ii, finding 64b, task 64a). `ddl_governed_tables()` = `governed_node_tables_of(_emitted_schema_ddl())` over every `surreal_schema.generate_*_ddl`, and fails closed on an unsuppliable parameter. | live: `ddl` = {agent, memory, message}; `governed_tables()` = 6; `ddl ∩ pending = ∅` |
| §13.4.2 scripts consume the package | `SliceDeriver` reads `governed_node_tables_of` / `ddl_governed_tables` / `PENDING_GOVERNED_TABLES` from `loremaster.governed`; the script's own `PENDING_GOVERNED_TABLES` is deleted (AST: no top-level PENDING/GOVERNED assign) | live: `SliceDeriver().governed_slice()` `governed_node` set **== `governed_tables()`** → True |
| R7b-1 (lead) | `brief` stays in `_MIGRATE_VALID_TABLES`; the containment holds as LEG set ⊆ ddl | live: legs ⊆ ddl True; `_MIGRATE_VALID_TABLES ⊆ ddl` False only by `brief` (ruled) |

**Removed-behaviour check: `is_governed_shape` / the slice's node derivation moved from the test tree's `_governed_contract.governed_node_tables` to `governed.governed_node_tables_of`.** Instrument: §A.4 `shape_equiv.py`.
- Old and new agree on the emitted DDL (`agent, memory, message`) and on the real dump's 353 DDL lines (`[]` — the dump is pre-63).
- They also agree on 5 hostile shapes: comment-led, lowercase, backticked, leading whitespace, `;` inside a string.
- Verdict: **preserved**. Both MISS a `-- comment`-led `DEFINE FIELD` statement. That is shared, pre-existing and unreachable from today's generators (they emit no comments), so it is NIT residual R-7.

## §2 Live receipts on the TEST store `:18000`

### §2a §13.3 item 2 — a live key-mint COLLISION through `lore-adm`
Instrument: §A.5 `probe6_mint.py`.
- **Method:** the REAL `principals.main()` runs in a **subprocess**, so stderr is a real fd 2. The secret is pinned in the child, so two principals' `mint-key` produce the identical `sha512_hex(f"{name}:{secret}")`.
- **Checks:** any 128+-hex run on stderr, AND the **exact** expected hash string.
- **Store:** a fresh `unique_database()`; port asserted `:18000`.

| leg | rc | 128-hex runs | exact hash on stderr | traceback |
|---|---|---|---|---|
| SCRUBBED (as shipped) | 1 | **0** | **False** | no |
| CONTROL (`scrub_text` → identity in `logging_setup` AND `principals`) | 1 | **2** | **True** | no |

Scrubbed stderr, verbatim:
- `principal.key.query.rejected [error_class=…; engine_error=Database index \`principal_key_hash\` already contains '***REDACTED***', with record \`principal_key:***REDACTED***]`
- `lore-adm: could not mint key 'laptop-scrubbed' for principal 'b-scrubbed@probe.test'`
- `  ← caused by: SurrealDB principal key query rejected against 'ws://127.0.0.1:18000/rpc' (unique violation …); see the server log for the full engine detail`
- `  ← caused by: Database index \`principal_key_hash\` already contains '***REDACTED***', with record \`principal_key:***REDACTED***`

In the control leg, the same two lines carry `b71207c6…4ff67e7` and the record id `principal_key:nsbh6oq4hfy819qlbaze`. **HOLDS.**

Observation, already a builder residual: the record id also redacts in the scrubbed leg. That is the pre-existing `_COMPOUND_ASSIGNMENT_RE` `_key:` label trade. It costs a diagnostic, not a secret.

### §2b The 500/deny on a wrong-shaped verify — spot re-check
Instrument: audit-5's `probe_fork2.py`, re-run verbatim on `final` (§A.6). It drives the REAL composed ASGI app with a well-formed bearer.

| cell | status | leaks |
|---|---|---|
| CONTROL-empty `[]` | **401** `invalid_token` | [] |
| CONTROL-rejected (`SurrealStoreError`) | **500** `Internal Server Error` | [] |
| `"garbage"` | **500** | [] |
| `["x"]` | **500** | [] |
| `{"name": …}` | **500** | [] |

Identical to audit-5 §2(a) on `bec29190`. **HOLDS.**

### §3a Reap-check hazard (my own instrument, disclosed)
`AsyncSurreal.use(ns, db)` **auto-creates** `db` (measured: a control name absent beforehand was listed afterwards, `control_autocreated=True`). So my first post-reap check (`use(ns, <reaped db>)`) re-created the §2a probe DB, which `drop_database` HAD removed.
- Repaired: `REMOVE DATABASE` → present False.
- `ns_dbs.py` (§A.7) now selects a dedicated control DB and removes it after use.
- A namespace `coldaudit63c` exists on the root of `:18000`. It is not mine (pre-dates this run) — FYI.

## §3 The OWED mutation proofs (audit-5 §A.12b A–E, re-pointed; + F1a, F1b, F2, G)
Method:
- `mutchain6.sh` (§A.12) waited for the targeted run's EXIT. Then, gated, it ran `--collect-only` on the `mut` tree over the five test files: **all 50 declared ids EXIST (0 MISSING)**. The ids were declared and confirmed BEFORE any mutated result existed.
- Each proof then ran through `mp6.sh` (§A.11) → `scripts/mutation_proof.py`: exactly-once anchor, declared reds diffed BOTH ways. A `cp -a` backup was taken first and `cmp`'d after.
- **Gate waits:** admitted 03:56:23Z–03:58:35Z, each wait 0–20 s. The earlier hold was 03:49:07Z→03:56:23Z (see §W).
- **Tree:** `loremaster.__file__` = `…/scratchpad/mut/loremaster/loremaster/__init__.py` on every ADMITTED line. After the chain, `mut` principals.py and governed.py are `cmp`-identical to `final`; 9/9 `CMP: restored byte-exact`.

| key | mutation (target) | test files | declared | observed | verdict |
|---|---|---|---|---|---|
| A | `with _cli_logging():` → `if True:` (handler never installed; principals) | test_principals_cli.py | 17 | 18 failed / 198 passed | **KILLED**: all 17 declared red, plus 1 UNDECLARED red: `TestTheLoreAdmFaultLineTeachesItsCause::test_repeated_invocations_do_not_duplicate_the_log_line`, the handler-lifecycle pin, which also legitimately dies when no handler is installed. `mutation_proof` exit 4 (both-ways diff) — a gap in MY declaration (copied from audit-5's), not in a pin. |
| B | `map_of` tolerant on a non-dict INFO answer (governed) | test_fail_closed_shapes_63c_13b.py | 8 | 8 / 77 | **HELD exactly** (exit 0) |
| C | `_dispatch_report_unmigrated`'s pre-I/O `validate_governed_table(...)` → `pass` (re-anchored: `_is_governed_table` is retired) | test_principals_cli.py | 1 | 1 / 215 | **HELD exactly**: `TestHonestLabels::test_an_invalid_table_is_refused_before_any_store_call[report-unmigrated]` |
| D | schema gate never fires (`if not missing: return None` → `if True:`) | test_preboot_…_13d.py | 10 | 10 / 15 | **HELD exactly** |
| E | **the §13.1 one-derivation**: `missing` filter drops `agent.owner_agent` | test_preboot_…_13d.py | 2 | 2 / 23 | **HELD exactly** |
| F1a | **F-1: the scanner NARROWS** — open quote / open bracket at end-of-clause → `return items` instead of raising | test_am37_13_3 | 3 | 3 / 88 | **HELD exactly**: `[open-paren-at-end]`, `[open-quote-at-end]`, `test_an_unreadable_leg_literal_reaches_main_as_a_traceback` |
| F1b | **F-1: an unreadable ITEM is skipped** (`continue`) instead of raising | test_am37_13_3 | 1 | 1 / 90 | **HELD exactly**: `[trailing-item-without-equals]` |
| F2 | **F-2: drop `handler.addFilter(RedactingFilter())`** | test_am37_13_3 + test_principals_cli.py | 2 | 2 / 305 | **HELD exactly**: `test_the_cli_stderr_handler_carries_a_RedactingFilter`, `test_the_stderr_log_record_is_scrubbed_end_to_end` |
| G | **§13.4: the report function's validator back on `_MIGRATE_VALID_TABLES`** | test_am37_13_4 + test_am37_13_3 | 6 | 6 / 184 | **HELD exactly**: report_count_accepts[finding], [task]; read_back_completes…; pending_tables_report…; remedy_names…[finding], [task] |

**All 9 mutations are KILLED; 8 match the declared set exactly, and 1 has a disclosed extra sibling.** The §13.1 one-derivation (E) proof that audit-5 owed is now DONE.


## §4 The restore read-back on the REAL dump, with the NEW code

### §4a The run
`cd final && uv run python scripts/restore_prod_dump.py --dump /backups/lore/lore-prod-20260803T141930Z.surql`: **exit 0**, total 19.3 s, DB `test_dump_20261001T034516Z_ab42850890f84045a109cce926eb06c9`.

| table | provenance | declared | readback | scope NONE |
|---|---|---|---|---|
| agent | derived | 95 | 95 | **95** |
| brief | pending | 26 | 26 | **26** |
| finding | pending | 324 | 324 | **324** |
| memory | derived | 177 | 177 | **177** |
| message | derived | 316 | 316 | **316** |
| task | pending | 116 | 116 | **116** |

`briefed` 123, `to` 337 and `finding_counter` 1 also restored. The ABSENT rows (blocks, audit, keep, member_of, principal, principal_key) are reported as "the dump predates it".

**A scope-NONE count is printed for all six governed tables ✅.** It never says "migrate-governed" for any of them ✅.

**⚠ But NO remedy line is served by the restore at all → #532.** `main()` runs `logging.getLogger("loremaster.governed").setLevel(logging.ERROR)  # the receipt renders that count itself`. That line is pre-existing since `80409f4`.
- The §13.4 pin 3 / §13.4.2 rider cell (`test_the_pending_tables_report_their_packet_never_a_migrate_verb`) drives `_read_back` under `caplog.at_level(WARNING)`. That re-raises the level the entry point lowers, so the pin certifies an emitted record that the real restore never serves.
- Served-truth impact: nil. The receipt's own note reads "pre-63 shape: scope NONE must == rows".

### §4b The §13.2 rider (spec §13.3 delta-audit scope)
Fresh restore `test_dump_20261001T035205Z_b767…`, pre-boot. `migrate-governed --table message` → exit 1:
- *"the `message` table has no `owner_agent`, `owner_principal`, `scope` column(s) — this store's schema predates the governed columns; boot the new image once (its DDL defines them), then re-run migrate-governed"*;
- `--table agent` → the same teaching for `agent`;
- the schema teaching arrives FIRST and alone. That is true per §13.2 reading B, and the same as audit-5 §6(iii).

### §4c Where the remedy IS served — live `lore-adm report-unmigrated` on the restored dump
Instrument: audit-5's `adm5.py` (#525 loader swap), re-used.

| `--table` | stdout | remedy on stderr | exit |
|---|---|---|---|
| finding | unmigrated=324 | "`finding` has no governed columns yet (the finding ledger is governed by intent; its S2 leg migrates these rows; **packet 64b**) — 324 row(s) will be scoped by that packet's migration" | 0 |
| task | unmigrated=116 | "… (**packet 64a**) — 116 row(s) will be scoped …" | 0 |
| brief | unmigrated=26 | "… (**packet 63c-ii**) — 26 row(s) …" | 0 |
| agent / message / memory | 95 / 316 / 177 | "run `lore-adm migrate-governed --table <t>` to backfill" | 0 |
| principal (control) | — | "lore-adm: report-unmigrated does not support table 'principal' — its tables are `agent`, `brief`, `finding`, `memory`, `message`, `task`" | 1 |

The fixed prefix on every pending line is *"carry a NONE scope (member-invisible until migrated)"*. `findings.py`/`tasks.py`/`briefs.py` hold **0** `scope` references (awk), so those rows are not member-invisible → **#530**.

### §4d Reap
Both dump DBs were reaped with `restore_prod_dump.py --reap <db>` (exit 0, *"absent from INFO FOR NS"*).
- Independently, with `ns_dbs.py`: BEFORE `present=True` (79 dbs) → AFTER `present=False` (78).
- Second DB: AFTER `present=False`.

## §5 Targeted run on `final` (NO full suite)
- **Set: 75 files** (`target6.files`, md5 `e9d2ca08becf5d23cd4664205b147bab`), the union of:
  - the AST covering set over every symbol changed `bec29190 → b15c06b0`: `cover6.py` (§A.1), 56 files. Changed symbols are listed in §A.1's output; they include every `logging_setup` symbol, and every test importing `loremaster.logging_setup` is added;
  - fix6's declared 68 (`declared-r7.txt`, md5 `94b9a838…` ✅);
  - `scripts/test_restore_prod_dump.py`, added by hand (#507);
  - `test_retry_seam.py`, `test_exhaustion_fates.py`, `test_mcp_server.py`, `test_token_verifier.py`.
- **Over-inclusion:** 7 files enter only via name collisions (`items`/`list`/`__init__`/`get_by_email`). They are kept, not pruned.
- **Gate:** `gated6.sh` (§A.8). No other LORE pytest ran, and MemAvailable was ≥ 20 GiB, admitted **03:38:10Z avail=20GiB others=0 waited=0s**. Under `systemd-run --scope MemoryMax=16G MemorySwapMax=0`, `-n 8 --timeout=300`.
- **Result:** `327 failed, 5404 passed, 3 skipped, 7 warnings in 653.43s` (EXIT 1, 03:49:07Z).
- **Ownership** (`own6.py`, §A.9, applies the gate's own per-file partition rule against the build's `scripts/pending_contracts.yaml`): **red 327 = owned 327, ORPHAN 0.**
  - `packet-64b-i-contract` 294;
  - `packet-58-contract` 29;
  - both, 4 (`test_reanchor_58_r3_cas_seam.py`).
- **No 63c pin file is red.** Every red file is a 64b or 58 file: comms_footer 81, findings_* 146, governed_substrate_64b 34, mcp_server 27, reanchor_58_* 32, exhaustion_fates 1.
- **Cross-check:** restricted to fix6's 68 files, my red id set is **byte-identical** to the builder's r7 BUILD red set (268 = 268, `diff` empty). The extra 59 reds sit in the three 64b-owned files that only my AST scan added (adversary_pins 13, identity 22, scope_domain 24).

## §6 Gates (on `final`)
- `uv run ruff check .` → **All checks passed!** (exit 0).
- `./scripts/typecheck.sh` → `Found 82 errors in 31 files` + `Found 1 error in 1 file` = **83**. The `error:` lines are **IDENTICAL to `prev`** (incl. line numbers; `diff` empty).
- `pending_contract_gate.py --currency --legs typecheck,ruff`:
  - `typecheck RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract … · packet-64b-i-contract`;
  - `ruff GREEN`;
  - `pytest NOT_RUN — claimed by the manifest, never executed` → `CURRENCY : FAIL` (exit 1).
  - **RED_ORPHANED 0 on the run legs.** The pytest NOT_RUN line is the known tool-UX residual (FLAG-2).

## §7 Natural-language sweep of the delta's added lines
Instrument §A.10 `nl_sweep6.py`: every NEW/CHANGED string literal and comment in the 6 production files prev→final — **146 hits, each with its own verdict** (fragments of one f-string are separate hits). Plus one hit the instrument filters out (a bare literal): `governed.py:986` `verb="report-unmigrated"` — NIT N-c, a second spelling of `principals._REPORT_VERB`.

| file:line | role | text (≤90) | verdict |
|---|---|---|---|
| `governed.py:1` | docstring | The shared GOVERNED SUBSTRATE (packet 63a; extended through 63c) — built, not a stub.\n\nT | true (read against the code) |
| `governed.py:752` | other | the {noun} LANDED (committed) but answered a {type} instead of its rows — nothing was deci | **over-claim** — 'a re-run is idempotent' false for create/mint (→ #531, spec-verbatim) |
| `governed.py:758` | docstring | THE one reader of a row-list answer (a ``SELECT`` / ``UPDATE … RETURN …`` result), with th | true (read against the code) |
| `governed.py:788` | docstring | :func:`rows_of`'s fault text: the ONE landed template for a post-write read, else the read | true (read against the code) |
| `governed.py:863` | docstring | THE governed-table property over DDL TEXT (am-37 §13.4.1): a table is governed iff ``ddl`` | true (read against the code) |
| `governed.py:878` | docstring | Every ``surreal_schema.generate_*_ddl`` function's output, joined — the ARTIFACT the image | true (read against the code) |
| `governed.py:899` | docstring | The tables whose GENERATED DDL defines the governed triple (am-37 §13.4.2): today ``agent` | true (live: agent, memory, message) — NIT N-b: restates a DERIVED value in prose |
| `governed.py:907` | docstring | Why a governed-by-intent table is governed before its DDL carries the triple, and which pa | true (read against the code) |
| `governed.py:937` | docstring | THE governed set — the REPORT domain (am-37 §13.4 / §13.4.2): :func:`ddl_governed_tables`  | true (read against the code) |
| `governed.py:943` | docstring | A ``--table`` outside the verb's domain (am-37 §13.4): operator INPUT, so a ``ValueError`` | true (read against the code) |
| `governed.py:948` | docstring | THE one ``--table`` validator (am-37 §13.4): ``table`` must be in ``domain``, else\n    :c | true (read against the code) |
| `governed.py:962` | docstring | Count ``table``'s rows that still carry a NONE ``scope`` — the forgotten-backfill measurem | true (read against the code) |
| `governed.py:796` | other | read answered a | true (noun/remedy fragment; rendered live §4c or by name) |
| `governed.py:796` | other | at row | true (noun/remedy fragment; rendered live §4c or by name) |
| `governed.py:796` | other | , not a row object — nothing was decided from it | true (noun/remedy fragment; rendered live §4c or by name) |
| `governed.py:794` | other | read answered a | true (noun/remedy fragment; rendered live §4c or by name) |
| `governed.py:794` | other | , not a row list — nothing was decided from it | true (noun/remedy fragment; rendered live §4c or by name) |
| `governed.py:1016` | served:log | governed.unmigrated_rows: %d %s row(s) carry a NONE scope (member-invisible until migrated | **FALSE for pending members** — 'member-invisible' (→ #530) |
| `governed.py:921` | other | the brief ledger is governed by intent; its governed columns and backfill land together | true (noun/remedy fragment; rendered live §4c or by name) |
| `governed.py:925` | other | the finding ledger is governed by intent; its S2 leg migrates these rows | true (noun/remedy fragment; rendered live §4c or by name) |
| `governed.py:929` | other | the task ledger is governed by intent; its S2 leg migrates these rows | true (noun/remedy fragment; rendered live §4c or by name) |
| `governed.py:956` | served:result | does not support table | true (live §4c refusal text) |
| `governed.py:956` | served:result | — its tables are | true (live §4c refusal text) |
| `governed.py:1008` | other | ` has no governed columns yet ( | true (noun/remedy fragment; rendered live §4c or by name) |
| `governed.py:1008` | other | ; packet | true (noun/remedy fragment; rendered live §4c or by name) |
| `governed.py:1009` | other | row(s) will be scoped by that packet's migration | true (noun/remedy fragment; rendered live §4c or by name) |
| `governed.py:1012` | other | run `lore-adm migrate-governed --table | true (noun/remedy fragment; rendered live §4c or by name) |
| `governed.py:1012` | other | ` to backfill | true (noun/remedy fragment; rendered live §4c or by name) |
| `governed.py:1014` | other | no migrate verb accepts ` | true (noun/remedy fragment; rendered live §4c or by name) |
| `governed.py:1014` | other | ` yet — | true (noun/remedy fragment; rendered live §4c or by name) |
| `governed.py:1014` | other | row(s) remain unscoped | true (noun/remedy fragment; rendered live §4c or by name) |
| `governed.py:891` | served:raise | requires | true (fail-closed TypeError, read) |
| `governed.py:891` | served:raise | , which the governed-set derivation cannot supply | true (fail-closed TypeError, read) |
| `governed.py:748` | comment | #: THE one post-write shape-fault text (am-37 §13.3 item 5): a write sink's answer read wi | true (read) |
| `governed.py:749` | comment | #: that is not a row list. The write has already COMMITTED, so the text says so — a reader | true (read) |
| `governed.py:750` | comment | #: "nothing happened" from a fault raised after the write landed. | true (read) |
| `governed.py:845` | comment | #: The DDL generators' naming contract (the membership rule — a new ``generate_<slice>_ddl | true (see :846) |
| `governed.py:846` | comment | #: derivation the day it lands; the test tree's ``schema_ddl_generators`` applies the same | true (`_enforced_relations_scaffold.schema_ddl_generators` = same rule) — NIT N-e: the rule now lives twice |
| `governed.py:850` | comment | #: The width handed to a generator that takes ``dim``. Any positive width will do: the gov | true |
| `governed.py:851` | comment | #: emitted identically at every width; only the vector index text varies. | true (measured dim 8 vs 1024: identical set) |
| `governed.py:854` | comment | #: One ``DEFINE FIELD [OVERWRITE \| IF NOT EXISTS] <column> ON [TABLE] <table>`` statement. | true (read) |
| `governed.py:868` | comment | # noqa: SLF001 | true (read) |
| `governed.py:914` | comment | #: The DECLARED governed-by-intent tables (am-37 §13.4.2; moved here from ``scripts/restor | true (read) |
| `governed.py:915` | comment | #: so the image ships it and ``scripts`` consumes it): governed, reportable and restored,  | true (read) |
| `governed.py:916` | comment | #: governed columns in their DDL yet. SELF-DESTRUCTING: a pin reds BY MEMBER the day a tab | true (read) |
| `governed.py:917` | comment | #: triple (``ddl_governed_tables() ∩ keys == ∅``), so this set can only shrink. | true (read) |
| `governed.py:983` | comment | # Function-local: ``principals`` imports this module (the house cycle-breaking idiom). | true (read) |
| `principals.py:1301` | docstring | ``report-unmigrated``'s ``--table`` help domain, DERIVED: the migrate set first (in its or | true (read against the code) |
| `principals.py:1311` | docstring | ``names`` as prose — each in its own backtick span, ``, ``-joined with a final ``and`` — s | true (read against the code) |
| `principals.py:1318` | docstring | THE one validator (:func:`loremaster.governed.validate_governed_table`, am-37 §13.4) over  | true (read against the code) |
| `principals.py:1333` | docstring | Where a valid-but-legless table's backfill lands, DERIVED from its\n    :data:`~loremaster | true (read against the code) |
| `principals.py:1367` | docstring | The "not supported" refusal. ``table_defined`` is the verb\'s derived answer (amendment 37 | true (read against the code) |
| `principals.py:1953` | docstring | A migrate leg's backfill statement that the schema gate cannot read COMPLETELY (am-37 §13. | true (read against the code) |
| `principals.py:1982` | docstring | The clause keyword starting at ``index`` when it stands as a whole word — preceded by whit | true (read against the code) |
| `principals.py:1997` | docstring | THE one scanner over an ``UPDATE`` statement (am-37 §13.3 item 1): a single depth- AND quo | true (read against the code) |
| `principals.py:2072` | docstring | The columns an ``UPDATE <table> SET <col> = <expr>, …`` statement assigns, in statement or | true (read against the code) |
| `principals.py:2359` | docstring | The verb's measured inputs, handed to whichever migrate leg :data:`_MIGRATE_LEGS` dispatch | true (read against the code) |
| `principals.py:2814` | docstring | The lore-adm fault text: ``lore-adm: <error>`` then one cause line per ``__cause__`` link  | true (read against the code) |
| `principals.py:2863` | docstring | Install ONE WARNING-level, :class:`~loremaster.logging_setup.RedactingFilter`-filtered std | true (read against the code) |
| `principals.py:920` | docstring | A ``SELECT``/``CREATE``/``UPDATE`` result's rows, through the ONE fail-closed row-list pol | true (read against the code) |
| `principals.py:1307` | other | one of: | true (noun/remedy fragment; rendered live §4c or by name) |
| `principals.py:1338` | other | has no migrate leg yet | true (noun/remedy fragment; rendered live §4c or by name) |
| `principals.py:2011` | docstring | Advance the string/bracket state over ``statement[index]``; ``True`` when that character i | true (read against the code) |
| `principals.py:2037` | docstring | The ``SET`` clause's raw items, split at top-level commas. Raises\n        :class:`Governe | true (read against the code) |
| `principals.py:1338` | other | lands at packet | true (noun/remedy fragment; rendered live §4c or by name) |
| `principals.py:1392` | served:result | ; nothing was read or written | true (live) |
| `principals.py:533` | other | principal create | true (noun/remedy fragment; rendered live §4c or by name) |
| `principals.py:552` | other | principal lookup by subject | true (noun/remedy fragment; rendered live §4c or by name) |
| `principals.py:567` | other | principal lookup by email | true (noun/remedy fragment; rendered live §4c or by name) |
| `principals.py:582` | other | principal list | true (noun/remedy fragment; rendered live §4c or by name) |
| `principals.py:627` | other | principal status update | true (noun/remedy fragment; rendered live §4c or by name) |
| `principals.py:671` | other | principal subject bind | true (noun/remedy fragment; rendered live §4c or by name) |
| `principals.py:722` | other | principal expiry update | true (noun/remedy fragment; rendered live §4c or by name) |
| `principals.py:1377` | served:result | does not yet migrate ` | true (live text §1 row 9) |
| `principals.py:1377` | served:result | ` — its backfill | true (live text §1 row 9) |
| `principals.py:1377` | served:result | (today: | true (live text §1 row 9) |
| `principals.py:1378` | served:result | ); the store's governed-table preconditions were read and passed, and nothing was written | true |
| `principals.py:1384` | served:raise | ` is a valid migrate table, answered not-supported with no store read | true (internal guard; unreachable by construction) |
| `principals.py:1386` | other | `'s backfill | true (noun/remedy fragment; rendered live §4c or by name) |
| `principals.py:2549` | other | the governed table to inspect ( | true (noun/remedy fragment; rendered live §4c or by name) |
| `principals.py:817` | other | kept-keep lookup before a principal delete | true (noun/remedy fragment; rendered live §4c or by name) |
| `principals.py:2063` | served:result | an unterminated | true (read; scanner/refusal texts exercised by §A.3 / §4c) |
| `principals.py:2063` | served:result | string in | true (read; scanner/refusal texts exercised by §A.3 / §4c) |
| `principals.py:2065` | served:result | unclosed bracket(s) in | true (read; scanner/refusal texts exercised by §A.3 / §4c) |
| `principals.py:2067` | served:result | not an `UPDATE … SET` statement: | true (read; scanner/refusal texts exercised by §A.3 / §4c) |
| `principals.py:2088` | served:result | a SET item that is not `<column> = <value>`: | true (read; scanner/refusal texts exercised by §A.3 / §4c) |
| `principals.py:2031` | served:result | an unbalanced | true (read; scanner/refusal texts exercised by §A.3 / §4c) |
| `principals.py:2031` | served:result | at offset | true (read; scanner/refusal texts exercised by §A.3 / §4c) |
| `principals.py:1295` | comment | #: The two ``--table`` verbs' names, as the ONE validator renders them in a refusal. | true (read) |
| `principals.py:1961` | comment | #: The keywords that END an ``UPDATE`` statement's ``SET`` clause — recognised by :func:`_ | true (read) |
| `principals.py:1962` | comment | #: at bracket depth 0 outside a string (am-37 §13.3 item 1). | true (read) |
| `principals.py:1965` | comment | #: The keyword that OPENS the clause, under the same depth-0 / outside-a-string rule. | true (read) |
| `principals.py:1968` | comment | #: The opening → closing bracket pairs the scanner tracks as ONE depth (a call's arguments | true (read) |
| `principals.py:1969` | comment | #: object literal — a comma inside any of them never splits an item). | true (read) |
| `principals.py:1972` | comment | #: The string delimiters (SurrealQL ``\'…\'`` / ``"…"``; a backslash escapes the next char | true (read) |
| `principals.py:1975` | comment | #: One ``SET`` item: ``<column> <op>= <value>`` — ``=``, ``+=``, ``-=`` or ``+?=``, the va | true (read) |
| `principals.py:1976` | comment | #: column must be a bare identifier; any other target (a nested path, a quoted name) is no | true (read) |
| `principals.py:1977` | comment | #: can check against ``INFO FOR TABLE``'s field names, so it RAISES rather than guess. | true (read) |
| `principals.py:2198` | comment | # ONE statement, three columns, scope-keyed (ruling §6) — built at the top of this leg (ab | true (statement built at the leg's top, line 2165) |
| `principals.py:2319` | comment | # amendment 37 §6 F-10 (the input-fate law) + §13 F-4: the rows the self-guarding UPDATE l | true (read) |
| `principals.py:2320` | comment | # are neither stamped nor refused — so they are MEASURED here, by ONE read, and reported,  | true (read) |
| `principals.py:2321` | comment | # silent fate a re-run would repeat forever. The read counts EVERY message row still unsco | true (read) |
| `principals.py:2322` | comment | # ownerless after the backfill: commonly a row whose SENDER is unsound (no owner or no sco | true (read) |
| `principals.py:2323` | comment | # inserted during the run is counted too — it is not a sender-skipped count. | true (read) |
| `principals.py:2370` | comment | #: THE migrate-leg dispatch: ``table -> the leg that backfills it``. :func:`_migrate_gover | true (read) |
| `principals.py:2371` | comment | #: table\'s leg through THIS mapping and answers any other valid table "not yet migrated", | true (read) |
| `principals.py:2372` | comment | #: tables the verb actually migrates — not a list kept beside the dispatch. | true (read) |
| `principals.py:2398` | comment | #: The tables ``migrate-governed`` has a backfill LEG for — DERIVED from the dispatch's ow | true (read) |
| `principals.py:2399` | comment | #: F-5 ruling: no hand list). The not-yet-migrated refusal\'s "today:" list (:func:`_not_s | true (read) |
| `principals.py:2400` | comment | #: §13.3 item 9 / #31) and ``report-unmigrated``'s remedy (item 6: a remedy names ``migrat | true (read) |
| `principals.py:2401` | comment | #: for a table the verb would actually run) read it. | true (read) |
| `principals.py:2874` | comment | # am-37 §13.3 item 2 (i): THE redaction seam, exactly as ``configure_logging`` attaches it | true (§2a: engine_error extra scrubbed) |
| `principals.py:2875` | comment | # scrubs ``msg``, ``args`` and EVERY extra (``engine_error`` included) through ``scrub_tex | true |
| `principals.py:2969` | comment | # am-37 §13 C N-3 / F-15 + §13.4: validated BEFORE any I/O (no store is even built) throug | true (live: `principal` → exit 1, §4c) |
| `principals.py:2970` | comment | # validator, over the REPORT domain — the governed set. A refusal is a ``ValueError``: the | true |
| `principals.py:2971` | comment | # handler renders it to stderr + exit 1. | true |
| `logging_setup.py:1` | docstring | Structured logging for the lore monorepo (stdlib ``logging``, Mezmo-friendly).\n\nThis is  | true (read against the code) |
| `logging_setup.py:309` | docstring | Redact secrets from a single string: auth header, bearer, labelled assignment, hash.\n\n   | true (read against the code) |
| `logging_setup.py:368` | docstring | Scrub a single ``extra`` value, recursing through containers.\n\n    Strings are scrubbed  | true (read against the code) |
| `logging_setup.py:476` | docstring | Scrub secrets from a record's message, ``extra`` values, AND its traceback.\n\n    Mutates | true (read against the code) |
| `logging_setup.py:170` | comment | #: The credential-hash SHAPE (am-37 §13.3 item 2): a run of 128 or more hex characters, | true (read) |
| `logging_setup.py:171` | comment | #: bounded by non-hex. A lore credential is stored as ``sha512_hex(f"{name}:{secret}")`` | true (read) |
| `logging_setup.py:172` | comment | #: (128 hex), and the one surface that can carry it is a UNIQUE-hash index rejection the | NIT N-d: 'the one surface … on a key mint' — builder's own sweep names `agents.py` capability_hash as the same class (regex covers both) |
| `logging_setup.py:173` | comment | #: engine echoes into the store seam's ``engine_error`` extra on a key mint. This is a | see :172 |
| `logging_setup.py:174` | comment | #: fixed LENGTH, not a randomness guess: a 40-hex git SHA, a 64-hex sha256 and a 127-hex | true (read) |
| `logging_setup.py:175` | comment | #: run are copied through untouched. | true (read) |
| `logging_setup.py:176` | comment | #: | true (read) |
| `logging_setup.py:177` | comment | #: ⚠ KNOWN BOUND, met deliberately: a sha512 CONTENT digest in a log line would be redacte | true (read) |
| `logging_setup.py:178` | comment | #: too. Swept for this ruling (``REPORT-builder-63c-i-a-fix6.md`` §RESUME 2): no logger | NIT N-a: cites a bare `REPORT-builder-63c-i-a-fix6.md` (dangles on archive, #152) |
| `logging_setup.py:179` | comment | #: call and no raise in the package carries a content digest VALUE, and the only UNIQUE | true (read) |
| `logging_setup.py:180` | comment | #: indexes over a hash column hold credential hashes. Re-open trigger: the first log line | true (read) |
| `logging_setup.py:181` | comment | #: that must carry a content sha512 — then narrow this to the mint seam's record instead | true (read) |
| `logging_setup.py:182` | comment | #: (§13.3 item 2's fallback). | true (read) |
| `principal_keys.py:645` | docstring | A ``SELECT``/``CREATE``/``UPDATE`` result's rows, through the ONE fail-closed row-list pol | true (read against the code) |
| `principal_keys.py:428` | other | principal-key mint | true (noun/remedy fragment; rendered live §4c or by name) |
| `principal_keys.py:458` | other | principal-key list | true (noun/remedy fragment; rendered live §4c or by name) |
| `principal_keys.py:500` | other | principal-key revoke | true (noun/remedy fragment; rendered live §4c or by name) |
| `principal_keys.py:557` | other | principal-key verify lookup | true (noun/remedy fragment; rendered live §4c or by name) |
| `keeps.py:439` | other | keep membership read | true (noun/remedy fragment; rendered live §4c or by name) |
| `keeps.py:632` | other | keep lookup by key | true (noun/remedy fragment; rendered live §4c or by name) |
| `keeps.py:649` | other | keep lookup by id | true (noun/remedy fragment; rendered live §4c or by name) |
| `keeps.py:942` | other | keep household read | true (noun/remedy fragment; rendered live §4c or by name) |
| `keeps.py:965` | other | keeper's keep list | true (noun/remedy fragment; rendered live §4c or by name) |
| `keeps.py:1027` | other | member's keep list | true (noun/remedy fragment; rendered live §4c or by name) |
| `scripts/restore_prod_dump.py:13` | docstring | restore_prod_dump.py — restore the GOVERNED SLICE of a production ``surreal export`` into  | true (read against the code) |
| `scripts/restore_prod_dump.py:348` | docstring | Derives the default governed slice (§D-3 step 4), CONSUMING the package's governed set (am | true (read against the code) |


## §R Residual table (operator cap: every item below MAJOR is a residual; the audit records, the lead ledgers)
| id | sev | class (lifted property) | evidence | owner (proposed) | re-open trigger |
|---|---|---|---|---|---|
| **#529** | MINOR (latent) | F-1's own property: ∀ leg statement, the SET parse is COMPLETE or RAISES — comments are parsed as text | §A.3: `/* WHERE */` → SUBSET `['a']`; line comment / apostrophe-comment / backtick → RAISE; prev narrows identically (pre-existing door) | 63c-ii (next touch of `principals._SetClauseScanner`) | the first leg statement carrying a comment |
| **#530** | MINOR | every clause of the unmigrated-rows WARNING holds ∀ member of the report domain | §4c: "(member-invisible until migrated)" on finding/task/brief; their stores hold 0 `scope` refs | 63c-ii / 64a / 64b (each lands its table's read filter) — or a one-line derivation now | any pending table's read filter landing (then true for it) / the next edit of `report_unmigrated_governed_rows` |
| **#531** | MINOR (spec-originated) | a fault text's safety claim holds ∀ write sink it renders for | `_LANDED_SHAPE_FAULT` "a re-run is idempotent" at `principal create` / `principal-key mint` (UNIQUE email / (principal,name); a landed mint raises before the secret is returned) | lead (spec text) | the first observed wrong-shaped answer to a committed CREATE |
| **#532** | MINOR | a pin over a served line asserts it through the entry point that serves it | §4a: `restore_prod_dump.main()` sets `loremaster.governed` to ERROR; the §13.4.2 pin passes via `caplog.at_level` | lead/operator ruling (decision (a)) | the next change to the restore's receipt or to the rider |
| N-a | NIT | durable citations | `logging_setup.py` `_CREDENTIAL_HASH_RE` comment cites bare `REPORT-builder-63c-i-a-fix6.md §RESUME 2` (#152 class) | lead (archive path at close-out) | the report's archive move |
| N-b | NIT | prose restating a derived value | `governed.ddl_governed_tables` docstring "today `agent`, `memory`, `message`" | 63c-ii | the first table gaining the triple |
| N-c | NIT | one name per verb | `governed.py` passes `verb="report-unmigrated"` while `principals._REPORT_VERB` holds the same literal (cycle-free import direction makes it a deliberate copy) | 63c-ii | a verb rename |
| N-d | NIT | comment accuracy | `_CREDENTIAL_HASH_RE` comment: "the one surface … on a key mint" — the builder's own sweep lists `agents.py` capability_hash UNIQUE echo as the same class (the regex covers it regardless) | 63c-ii | — |
| N-e | NIT (ONE IMPLEMENTATION) | the "which functions are the schema's DDL generators" rule has ONE home | `governed._emitted_schema_ddl` (production) re-implements `_enforced_relations_scaffold.schema_ddl_generators` (test) — same rule, two copies; the test tree could now delegate to production | 63c-ii | a generator that is not a plain function (the scaffold's own named bound) |
| R-6 | observation | ROUTING IS NOT SHARING | 76 `_as_rows` calls in 11 other modules use private readers that do not route through `rows_of` (builder raised; outside §13.3's ruled domain) | operator scope call | next fail-closed sweep |
| R-7 | NIT (pre-existing, shared) | governed-shape derivation over DDL text | a `-- comment`-led `DEFINE FIELD` statement is missed by BOTH old and new derivations (§A.4); today's generators emit no comments | 63c-ii | a generator emitting comments |
| R-8 | FYI | — | namespace `coldaudit63c` on `:18000` root (not mine; predates this run) | lead | — |
| carried | — | — | FLAG-r7-1 (report `--table` help order held by the old F-15 pin), FLAG-2 (currency pytest NOT_RUN UX), the record-id redaction side effect, N-1/N-2/N-3, FLAG-4 newline forgery — all lead-ruled residuals, unchanged by this build | lead | as ruled |

## §W Memory-gate waits (excluded from the deadline)
- Targeted run: admitted 03:38:10Z, waited 0 s.
- Mutation chain: eligible at 03:49:07Z (the targeted run's EXIT). It was HELD at MemAvailable 18–19 GiB < 20 GiB until **03:56:23Z** (~7 min, never bypassed). Per-mutation waits were 0–20 s after that.
- Spawn 03:36:05Z → report ~04:05Z; well inside the 110-minute bound.


## §A Instruments (pasted VERBATIM — they established load-bearing claims; scratch is disposable)

### §A.1 `cover6.py`
```python
"""AST-derived covering-test set for the delta PREV(bec29190) -> FINAL(b15c06b0) (coldaudit-63c-i-a-6).
lore_impact caps covering tests at 15 (#518) and lore indexes the MAIN tree, not this scratch copy, so:
(1) diff every top-level def/class/assign and every class method by ast.dump between the two trees over the
changed production files; (2) a test file covers the delta iff it imports one of the changed production modules
(by dotted name or `from loremaster import <mod>`) AND its AST references (Name/Attribute/alias/str constant) a
changed symbol name; (3) every test file importing loremaster.logging_setup is added (brief: the logging_setup
covering tests). Usage: cover6.py <prev_tree> <final_tree>"""
import ast, pathlib, sys
prev, final = map(pathlib.Path, sys.argv[1:3])
PROD = {"loremaster/loremaster/principals.py": "principals", "loremaster/loremaster/governed.py": "governed",
        "loremaster/loremaster/principal_keys.py": "principal_keys", "loremaster/loremaster/keeps.py": "keeps",
        "loremaster/loremaster/logging_setup.py": "logging_setup", "scripts/restore_prod_dump.py": "restore_prod_dump"}
def defs(path):
    out = {}
    if not path.exists():
        return out
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[node.name] = ast.dump(node)
            if isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        out[f"{node.name}.{sub.name}"] = ast.dump(sub)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            for t in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                if isinstance(t, ast.Name):
                    out[t.id] = ast.dump(node)
    return out
changed, changed_mods = set(), set()
for rel, mod in PROD.items():
    a, b = defs(prev / rel), defs(final / rel)
    diff = {k for k in set(a) | set(b) if a.get(k) != b.get(k)}
    if diff:
        changed_mods.add(mod)
    for k in diff:
        changed.add(k.split(".")[-1])
        print(f"CHANGED {mod}: {k}{' (new)' if k not in a else ' (removed)' if k not in b else ''}", file=sys.stderr)
def imported_mods(tree):
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                mods.add(a.name.split(".")[-1])
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                mods.add(n.module.split(".")[-1])
            for a in n.names:
                mods.add(a.name)
    return mods
hits = []
roots = [final / "loremaster/tests", final / "scripts"]
for root in roots:
    for test in sorted(root.glob("test_*.py")):
        tree = ast.parse(test.read_text())
        mods = imported_mods(tree) & (changed_mods | {"logging_setup"})
        if not mods:
            continue
        names = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Name): names.add(n.id)
            elif isinstance(n, ast.Attribute): names.add(n.attr)
            elif isinstance(n, ast.alias): names.add(n.name.split(".")[-1])
            elif isinstance(n, ast.Constant) and isinstance(n.value, str): names.add(n.value)
        why = sorted(names & changed)
        if why or "logging_setup" in mods:
            hits.append(str(test.relative_to(final)))
            print(f"COVER {test.relative_to(final)} mods={sorted(mods)} via={why[:6]}", file=sys.stderr)
print("\n".join(hits))
```

### §A.2 `construct6.py`
```python
"""Independent construction checks for am-37 §13.3/§13.4/§13.4.1/§13.4.2 (coldaudit-63c-i-a-6), AST over the
FINAL tree. Each check prints PASS/FAIL with its evidence; never reads the builder's tables."""
import ast, pathlib, sys
root = pathlib.Path(sys.argv[1])
pkg = root / "loremaster/loremaster"
def parse(p): return ast.parse(p.read_text(), filename=str(p))
# 1. no import of scripts / restore_prod_dump anywhere under the package, any depth, any alias
bad = []
for p in pkg.rglob("*.py"):
    for n in ast.walk(parse(p)):
        names = []
        if isinstance(n, ast.Import): names = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom): names = [n.module or ""] + [a.name for a in n.names]
        for nm in names:
            parts = nm.split(".")
            if "scripts" in parts or "restore_prod_dump" in parts:
                bad.append(f"{p.relative_to(root)}:{n.lineno} {nm}")
    # importlib dynamic forms
    for n in ast.walk(parse(p)):
        if isinstance(n, ast.Call) and isinstance(n.func, (ast.Attribute, ast.Name)):
            fn = n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id
            if fn in ("import_module", "__import__", "spec_from_file_location", "run_path"):
                for a in n.args:
                    if isinstance(a, ast.Constant) and isinstance(a.value, str) and ("scripts" in a.value or "restore_prod_dump" in a.value):
                        bad.append(f"{p.relative_to(root)}:{n.lineno} dynamic {a.value}")
print("1 no-scripts-import:", "PASS" if not bad else f"FAIL {bad}", f"(modules scanned={sum(1 for _ in pkg.rglob('*.py'))})")
pr = parse(pkg / "principals.py")
# 2. GovernedStatementError not in any except tuple in principals.py; ValueError is in _dispatch's
handlers = []
for fn in ast.walk(pr):
    if isinstance(fn, ast.AsyncFunctionDef | ast.FunctionDef) and fn.name in ("_dispatch", "main"):
        for h in ast.walk(fn):
            if isinstance(h, ast.ExceptHandler) and h.type is not None:
                handlers.append((fn.name, h.lineno, ast.unparse(h.type)))
print("2 handler tuples:", handlers)
print("  GovernedStatementError in a handler:", any("GovernedStatementError" in t for *_, t in handlers))
# 2b. GovernedStatementError's base
for n in pr.body:
    if isinstance(n, ast.ClassDef) and n.name == "GovernedStatementError":
        print("  GovernedStatementError bases:", [ast.unparse(b) for b in n.bases])
# 3. every rows_of/_as_rows/map_of/group_all_count call names noun= (whole workspace package)
missing = []; total = 0
for p in pkg.rglob("*.py"):
    for n in ast.walk(parse(p)):
        if isinstance(n, ast.Call):
            fn = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", None)
            if fn in ("rows_of", "_as_rows", "map_of", "group_all_count"):
                total += 1
                if not any(k.arg == "noun" for k in n.keywords):
                    missing.append(f"{p.relative_to(root)}:{n.lineno} {fn}")
print(f"3 noun= on shape-reader calls: total={total} missing={missing}")
# 4. retired names
for name in ("_scrub_text", "_is_governed_table", "_SET_CLAUSE_START", "_SET_CLAUSE_END"):
    hits = [f"{p.relative_to(root)}" for p in list(pkg.rglob("*.py")) + list((root/"scripts").glob("*.py")) if name in p.read_text().replace(name+"_", "")]
    print(f"4 retired {name}: {hits or 'none'}")
# 5. _cli_logging addFilter(RedactingFilter()) and _fault_line calls scrub_text on error and cause
for n in pr.body:
    if isinstance(n, ast.FunctionDef) and n.name == "_cli_logging":
        print("5 _cli_logging addFilter:", [ast.unparse(c) for c in ast.walk(n) if isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "addFilter"])
    if isinstance(n, ast.FunctionDef) and n.name == "_fault_line":
        print("5 _fault_line scrub_text calls:", [ast.unparse(c) for c in ast.walk(n) if isinstance(c, ast.Call) and getattr(c.func, "id", "") == "scrub_text"])
# 6. restore script: no PENDING_GOVERNED_TABLES / governed-set definition of its own
rs = parse(root / "scripts/restore_prod_dump.py")
assigns = [ast.unparse(t) for n in rs.body if isinstance(n, (ast.Assign, ast.AnnAssign)) for t in (n.targets if isinstance(n, ast.Assign) else [n.target])]
print("6 restore top-level assigns naming PENDING/GOVERNED:", [a for a in assigns if "PENDING" in a or "GOVERNED" in a])
# 7. validate_governed_table call sites
for p in [pkg/"principals.py", pkg/"governed.py"]:
    for n in ast.walk(parse(p)):
        if isinstance(n, ast.Call) and getattr(n.func, "id", getattr(n.func, "attr", None)) == "validate_governed_table":
            print(f"7 validate call {p.name}:{n.lineno}", ast.unparse(n))
# 8. any other "table in _MIGRATE_VALID_TABLES"-style membership validator left?
for p in [pkg/"principals.py", pkg/"governed.py"]:
    for n in ast.walk(parse(p)):
        if isinstance(n, ast.Compare) and any(isinstance(o, (ast.In, ast.NotIn)) for o in n.ops):
            s = ast.unparse(n)
            if "_MIGRATE_VALID_TABLES" in s or "governed_tables" in s or "_MIGRATING_TABLES" in s or "_MIGRATE_LEGS" in s:
                print(f"8 membership {p.name}:{n.lineno}", s)
```

### §A.3 `scanner_doors.py`
```python
"""Hostile-shape probe of principals._set_columns beyond the pinned corpus (coldaudit-63c-i-a-6). For each
statement: EXPECTED exact set (None = must raise); verdict EXACT / RAISED / SUBSET(!) / WRONG. CONTROL: the
shipped agent statement parses exact; a known-subset build (prev tree's regex parser) is run on the same
corpus by passing a second tree path, so the probe is shown able to detect a subset."""
import sys, importlib
sys.path.insert(0, sys.argv[1] + "/loremaster")
import loremaster, loremaster.principals as p
print("loremaster", loremaster.__file__)
CASES = {
 "control-shipped-agent": ("UPDATE agent SET owner_principal = type::record('principal', $owner), owner_agent = id, scope = $scope WHERE scope IS NONE AND owner_principal IS NONE", {"owner_principal","owner_agent","scope"}),
 "block-comment-WHERE": ("UPDATE t SET a = 1 /* WHERE */ , b = 2 WHERE x = 1", {"a","b"}),
 "line-comment-WHERE": ("UPDATE t SET a = 1, -- WHERE\n b = 2 WHERE x = 1", {"a","b"}),
 "comment-with-apostrophe": ("UPDATE t SET a = 1, -- it's\n b = 2 WHERE x = 1", {"a","b"}),
 "backtick-ident-comma": ("UPDATE t SET a = `x,y`, b = 2 WHERE x = 1", {"a","b"}),
 "keyword-after-paren": ("UPDATE t SET a = (1)WHERE x = 1", {"a"}),
 "tab-before-WHERE": ("UPDATE t SET a = 1,\tb = 2\tWHERE x = 1", {"a","b"}),
 "UNSET-tail": ("UPDATE t SET a = 1 UNSET b WHERE x = 1", None),
 "multi-statement": ("UPDATE t SET a = 1 WHERE x = 1; UPDATE t SET b = 2", {"a"}),
 "escaped-quote": ("UPDATE t SET a = 'it\\'s, x', b = 2 WHERE x = 1", {"a","b"}),
 "IF-THEN-END value": ("UPDATE t SET a = IF x THEN 1 ELSE 2 END, b = 3 WHERE y = 1", {"a","b"}),
 "set-lowercase": ("update t set a = 1, b = 2 where x = 1", {"a","b"}),
 "eq-eq-value": ("UPDATE t SET a == 1 WHERE x = 1", None),
 "nested-path-target": ("UPDATE t SET a.b = 1 WHERE x = 1", None),
}
def verdict(fn, stmt, exp):
    try: got = set(fn(stmt))
    except Exception as e: return f"RAISED {type(e).__name__}"
    if exp is None: return f"RETURNED {sorted(got)} (expected raise)"
    if got == exp: return "EXACT"
    if got < exp: return f"SUBSET! {sorted(got)}"
    return f"WRONG {sorted(got)}"
for k, (s, e) in CASES.items():
    print(f"{k:28} {verdict(p._set_columns, s, e)}")
```

### §A.4 `shape_equiv.py`
```python
"""Old (test-tree _governed_contract.governed_node_tables) vs new (loremaster.governed.governed_node_tables_of)
governed-shape property, over (1) the emitted schema DDL, (2) the real dump's DDL lines, (3) per-table slices
of the dump DDL, (4) hostile shapes (comment-led statement, backticked names, lowercase). coldaudit-63c-i-a-6."""
import sys, pathlib
sys.path.insert(0, "loremaster/tests")
import loremaster, _governed_contract as c, _enforced_relations_scaffold as s
from loremaster import governed as g
print("loremaster", loremaster.__file__)
emitted = s.emitted_schema_ddl()
print("emitted  old", sorted(c.governed_node_tables(emitted)), "new", sorted(g.governed_node_tables_of(emitted)), "ddl_governed", sorted(g.ddl_governed_tables()))
print("governed_tables", sorted(g.governed_tables()), "pending", sorted(g.PENDING_GOVERNED_TABLES))
dump = pathlib.Path(sys.argv[1]).read_text()
print("dump     old", sorted(c.governed_node_tables(dump)), "new", sorted(g.governed_node_tables_of(dump)))
cases = {
  "comment-led": "-- note\nDEFINE FIELD scope ON t TYPE option<string>;\n-- n\nDEFINE FIELD owner_agent ON t TYPE option<string>;\n-- n\nDEFINE FIELD owner_principal ON t TYPE option<string>;",
  "lower": "define field scope on table t type string; define field owner_agent on table t type string; define field owner_principal on table t type string;",
  "backtick": "DEFINE FIELD scope ON `t` TYPE string; DEFINE FIELD owner_agent ON `t` TYPE string; DEFINE FIELD owner_principal ON `t` TYPE string;",
  "leading-ws": "  DEFINE FIELD scope ON t TYPE string;\n  DEFINE FIELD owner_agent ON t TYPE string;\n DEFINE FIELD owner_principal ON t TYPE string;",
  "semicolon-in-string": "DEFINE FIELD scope ON t TYPE string ASSERT $value != ';DEFINE FIELD owner_agent ON t'; DEFINE FIELD owner_principal ON t TYPE string;",
}
trio = [n for n, *_ in __import__("loremaster.store.surreal_schema", fromlist=["x"])._governed_field_specs()]
print("trio", trio)
for name, ddl in cases.items():
    try: old = sorted(c.governed_node_tables(ddl))
    except Exception as e: old = f"RAISE {type(e).__name__}"
    print(f"{name:20} old={old} new={sorted(g.governed_node_tables_of(ddl))}")
```

### §A.5 `probe6_mint.py`
```python
"""am-37 §13.3 item 2 live receipt (coldaudit-63c-i-a-6): a key-mint COLLISION on the TEST store :18000 through
the REAL lore-adm main() in a SUBPROCESS (real fd-2 stderr), checked for (a) any 128+-hex run and (b) the EXACT
expected credential hash sha512_hex(f"{name}:{secret}"). The secret is pinned in the child so two principals'
mints collide on the UNIQUE hash index. CONTROL leg: the child replaces logging_setup.scrub_text and
principals.scrub_text with identity — the same collision must then SHOW the hash (proves the probe can see it).
Fresh unique_database(), reaped in finally, absence verified by INFO FOR NS. Never :18500."""
import asyncio, os, re, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, "loremaster/tests")
import loremaster, yaml
import test_principals_cli as cli
from _surreal_harness import drop_database, make_env, surreal_password, surreal_user, unique_database
from loremaster.index.records import sha512_hex
SCRATCH = Path(sys.argv[1]).resolve()
assert Path(loremaster.__file__).resolve().is_relative_to(SCRATCH), loremaster.__file__
print("loremaster.__file__ =", loremaster.__file__)
HEX = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{128,}(?![0-9A-Fa-f])")
SECRET = "PINNED-coldaudit6-secret"
CHILD = """
import sys, secrets
import loremaster.principals as p
secrets.token_urlsafe = lambda n=None: %r
p.secrets.token_urlsafe = secrets.token_urlsafe
if sys.argv[1] == "control":
    import loremaster.logging_setup as ls
    ident = lambda t: t
    ls.scrub_text = ident; p.scrub_text = ident
sys.exit(p.main(sys.argv[2:]))
""" % SECRET
def run(leg, cfg, *args):
    env = dict(os.environ)
    env[cli._USER_ENV] = surreal_user(); env[cli._PASS_ENV] = surreal_password().get_secret_value()
    env[cli._ANTHROPIC_ENV] = "unused"
    proc = subprocess.run([sys.executable, "-c", CHILD, leg, "--config", str(cfg), *args], capture_output=True, text=True, env=env, timeout=120)
    return proc.returncode, proc.stderr
async def ns_dbs(env):
    from surrealdb import AsyncSurreal
    async with AsyncSurreal(env.url) as db:
        await db.signin({"username": surreal_user(), "password": surreal_password().get_secret_value()})
        await db.use(env.namespace, env.database)
        info = await db.query("INFO FOR NS")
        return set((info or {}).get("databases", {}))
def main():
    database = unique_database(); env = make_env(database=database, dim=cli.PRODUCTION_DIM)
    assert ":18500" not in env.url and ":18000" in env.url, env.url
    print("store", env.url, "ns", env.namespace, "db", database)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp) / "lore.yaml"; cfg.write_text(yaml.safe_dump(cli._config_payload(database=database)))
            for leg in ("scrubbed", "control"):
                name = f"laptop-{leg}"; expected = sha512_hex(f"{name}:{SECRET}")
                for who in "ab":
                    rc, err = run(leg, cfg, "add", "--email", f"{who}-{leg}@probe.test"); assert rc == 0, err
                rc, err = run(leg, cfg, "mint-key", "--email", f"a-{leg}@probe.test", "--name", name); assert rc == 0, err
                rc, err = run(leg, cfg, "mint-key", "--email", f"b-{leg}@probe.test", "--name", name)
                runs = HEX.findall(err)
                print(f"--- leg {leg}: rc={rc} hex128_runs={len(runs)} exact_hash_present={expected in err} traceback={'Traceback' in err}")
                for line in err.splitlines(): print("    |", line[:260])
    finally:
        asyncio.run(drop_database(env))
        print("reaped", database, "still_present=", database in asyncio.run(ns_dbs(env)))
main()
```

### §A.6 `ns_dbs.py`
```python
"""List databases in lore_test on :18000 and report presence of NAME (coldaudit-63c-i-a-6). The SDK keeps no
USE across calls, so the session selects ns + a CONTROL db name; whether USE itself creates that control db is
MEASURED and printed (control_autocreated), and the control is removed after. Usage: ns_dbs.py NAME"""
import asyncio, sys
sys.path.insert(0, "loremaster/tests")
from _surreal_harness import make_env, surreal_password, surreal_user
from surrealdb import AsyncSurreal
CONTROL = "coldaudit6_listing_control"
async def main(name):
    env = make_env(database="x", dim=8); assert ":18000" in env.url
    async with AsyncSurreal(env.url) as db:
        await db.signin({"username": surreal_user(), "password": surreal_password().get_secret_value()})
        await db.use(env.namespace, CONTROL)
        dbs = set((await db.query("INFO FOR NS") or {}).get("databases", {}))
        print(f"ns={env.namespace} total_dbs={len(dbs)} present({name})={name in dbs} control_autocreated={CONTROL in dbs}")
        if CONTROL in dbs:
            await db.query(f"REMOVE DATABASE IF EXISTS {CONTROL}")
asyncio.run(main(sys.argv[1]))
```

### §A.7 `gated6.sh`
```bash
#!/usr/bin/env bash
# Memory-gated, cgroup-capped pytest runner (coldaudit-63c-i-a-6). Usage: gated6.sh <tree> <logfile> <pytest args...>
# Waits until NO other LORE pytest is live AND MemAvailable >= 20 GiB (never bypassed; wait logged), then runs under
# systemd-run MemoryMax=16G MemorySwapMax=0 with -n 8 --timeout=300 (pytest-timeout).
set -u
tree=$1; log=$2; shift 2
here=$(dirname "$0"); start=$(date +%s)
while :; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
  others=$("$here/lore_pytest_count.sh")
  if [ "$avail" -ge 20 ] && [ "$others" -eq 0 ]; then break; fi
  sleep 20
done
echo "ADMITTED $(date -u +%H:%M:%SZ) avail=${avail}GiB others=$others waited=$(( $(date +%s) - start ))s" > "$log"
cd "$tree" || exit 3
echo "loremaster=$(.venv/bin/python -c 'import loremaster;print(loremaster.__file__)')" >> "$log"
systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 uv run --no-sync --with pytest-timeout \
  pytest -n 8 --timeout=300 -q -p no:cacheprovider -rf "$@" >> "$log" 2>&1
echo "EXIT $? $(date -u +%H:%M:%SZ)" >> "$log"
```

### §A.8 `lore_pytest_count.sh`
```bash
#!/usr/bin/env bash
# Count live LORE pytest processes (coldaudit-63c-i-a-6): a pytest whose cwd is a lore tree (main repo or any
# scratch copy under a -home-ejprice-PycharmProjects-lore scratchpad). Foreign projects' pytest is ignored (brief).
# Excludes the caller's own process group via $1 (optional pid to ignore).
n=0
for pid in $(ps -eo pid=,args= | awk '/[p]ytest/ && !/lore_pytest_count/ && !/awk/{print $1}'); do
  [ "$pid" = "${1:-}" ] && continue
  cwd=$(readlink /proc/$pid/cwd 2>/dev/null) || continue
  case "$cwd" in *PycharmProjects/lore*|*PycharmProjects-lore*) n=$((n+1));; esac
done
echo $n
```

### §A.9 `own6.py`
```python
"""Red ownership for a `pytest -rf` log (coldaudit-63c-i-a-6), with the gate's OWN registry + partition rule
(scripts/pending_contract_gate.py: PendingContractRegistry.load, .registered_paths, .entries_for — ownership is
per FILE, exactly as PendingContractGate.partition_pytest decides it). Reads every `FAILED <nodeid>` /
`ERROR <nodeid>` summary line (a captured LOG record that merely starts with ERROR has no `::`/path and is
skipped by the path filter). Prints totals, per-file reds with owner bound ids, ORPHANs, and writes the sorted
red id list to <log>.reds. Usage (tree root): own6.py <pytest.log>"""
import collections, pathlib, re, sys
sys.path.insert(0, "scripts")
import pending_contract_gate as g
log = pathlib.Path(sys.argv[1]).read_text()
ids = []
for line in log.splitlines():
    if line.startswith(("FAILED ", "ERROR ")) and ".py::" in line.split(" ", 1)[1].split(" - ", 1)[0]:
        ids.append(line.split(" ", 1)[1].split(" - ", 1)[0].strip())
ids = sorted({i for i in ids})
reg = g.PendingContractRegistry.load(pathlib.Path("scripts/pending_contracts.yaml"))
registered = reg.registered_paths
per = collections.Counter(i.split("::", 1)[0] for i in ids)
orphans = [i for i in ids if i.split("::", 1)[0] not in registered]
owners = collections.Counter()
for f, n in sorted(per.items()):
    names = sorted({b.id for b, _ in reg.entries_for(f)})
    owners[" + ".join(names) or "ORPHAN"] += n
    print(f"  {n:4d}  {f}  -> {names or 'ORPHAN'}")
print(f"red={len(ids)} owned={len(ids) - len(orphans)} ORPHAN={len(orphans)}")
print("by owner:", dict(owners))
for o in orphans: print("ORPHAN:", o)
pathlib.Path(sys.argv[1] + ".reds").write_text("\n".join(ids) + "\n")
```

### §A.10 `nl_sweep6.py`
```python
"""NL sweep instrument (coldaudit-63c-i-a-6): every string literal (incl. f-string parts) and every comment that
is NEW or CHANGED between PREV and FINAL in the given files, with its FINAL file:line and its role (docstring /
served = inside raise/logger/print/return-of-a-message / comment / other). Usage: nl_sweep6.py PREV FINAL files..."""
import ast, difflib, io, pathlib, sys, tokenize
prev, final = map(pathlib.Path, sys.argv[1:3])
def added_lines(rel):
    a = (prev / rel).read_text().splitlines() if (prev / rel).exists() else []
    b = (final / rel).read_text().splitlines()
    out = set()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag in ("replace", "insert"):
            out.update(range(j1 + 1, j2 + 1))
    return out
for rel in sys.argv[3:]:
    src = (final / rel).read_text(); tree = ast.parse(src); added = added_lines(rel)
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    def role(node):
        cur = node
        while cur in parents:
            cur = parents[cur]
            if isinstance(cur, ast.Raise): return "served:raise"
            if isinstance(cur, ast.Call):
                f = cur.func; name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
                if name in ("warning", "error", "info", "exception", "critical", "debug"): return "served:log"
                if name == "print": return "served:print"
                if name in ("_refused", "MigrateGovernedResult", "GovernedTableRefusedError", "GovernedStatementError", "SurrealStoreError", "PrincipalStoreError"): return "served:result"
            if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                body = cur.body
                if body and isinstance(body[0], ast.Expr) and node in ast.walk(body[0]): return "docstring"
                return "other"
        return "other"
    seen = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value.strip()) > 3:
            lines = set(range(node.lineno, (node.end_lineno or node.lineno) + 1))
            if lines & added and (node.lineno, node.value) not in seen:
                seen.add((node.lineno, node.value))
                r = role(node)
                if r != "other" or any(c.isspace() for c in node.value.strip()):
                    print(f"{rel}:{node.lineno} [{r}] {node.value.strip()[:150]!r}")
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT and tok.start[0] in added:
            print(f"{rel}:{tok.start[0]} [comment] {tok.string[:150]!r}")
```

### §A.11 `mp6.sh`
```bash
#!/usr/bin/env bash
# Mutation proof wrapper (coldaudit-63c-i-a-6): cp -a backup of the target FIRST; gate = no other LORE pytest
# (lore_pytest_count.sh) AND MemAvailable >= 20 GiB (waits logged, never bypassed); then scripts/mutation_proof.py
# (declared reds diffed BOTH ways) under a MemoryMax=16G cgroup with -n 8 --timeout=300; afterwards `cmp` the
# target against its cp -a backup. Usage: mp6.sh <tree> <key> <target-file> <test files...>
set -u
tree=$1; key=$2; target=$3; shift 3
here=$(cd "$(dirname "$0")" && pwd); SP=$(dirname "$here"); M=$SP/mutdefs; log=$SP/mut_$key.log
cd "$tree" || exit 3
mkdir -p "$SP/mutbak_$key"; cp -a "$target" "$SP/mutbak_$key/"
start=$(date +%s)
while :; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
  others=$("$here/lore_pytest_count.sh")
  [ "$avail" -ge 20 ] && [ "$others" -eq 0 ] && break; sleep 20
done
echo "ADMITTED $(date -u +%H:%M:%SZ) avail=${avail}GiB others=$others waited=$(( $(date +%s) - start ))s loremaster=$(.venv/bin/python -c 'import loremaster;print(loremaster.__file__)')" > "$log"
args=(); while read -r id; do [ -n "$id" ] && args+=(--expect-red "$id"); done < "$M/$key.decl"
systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 .venv/bin/python scripts/mutation_proof.py \
  --file "$target" --anchor-file "$M/$key.anchor" --replacement-file "$M/$key.repl" "${args[@]}" -- \
  uv run --no-sync --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider "$@" >> "$log" 2>&1
echo "mutation_proof exit=$?" >> "$log"
cmp "$target" "$SP/mutbak_$key/$(basename "$target")" && echo "CMP: restored byte-exact vs cp -a backup" >> "$log" || echo "CMP: DIFFERS — TREE DIRTY" >> "$log"
```

### §A.12 `mutchain6.sh`
```bash
#!/usr/bin/env bash
# Sequential mutation chain (coldaudit-63c-i-a-6). Waits for the targeted run's EXIT line, then (gated) a
# --collect-only over every mutation's test files on the `mut` tree, confirms every declared id EXISTS (ids are
# fixed BEFORE any mutated result exists), then runs A..G through mp6.sh, one at a time.
here=$(cd "$(dirname "$0")" && pwd); SP=$(dirname "$here"); T=$SP/mut; M=$SP/mutdefs
until awk '/^EXIT/{f=1} END{exit !f}' $SP/run_targeted.log 2>/dev/null; do sleep 15; done
until [ "$($here/lore_pytest_count.sh)" -eq 0 ] && [ "$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)" -ge 20 ]; do sleep 15; done
P=loremaster/tests
cd $T && systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 uv run --no-sync pytest --collect-only -q -p no:cacheprovider $P/test_principals_cli.py $P/test_fail_closed_shapes_63c_13b.py $P/test_preboot_schema_precondition_63c_13d.py $P/test_am37_13_3_63c_i_a.py $P/test_am37_13_4_63c_i_a.py > $SP/collect6.txt 2>&1
for k in A B C D E F1a F1b F2 G; do while read -r id; do awk -v id="$id" '$0==id{f=1} END{exit !f}' $SP/collect6.txt && echo "OK $k $id" || echo "MISSING $k $id"; done < $M/$k.decl; done > $SP/collect6_check.txt
if awk '/^MISSING/{f=1} END{exit !f}' $SP/collect6_check.txt; then echo "CHAIN STOPPED: missing declared ids" > $SP/mutchain6.done; exit 1; fi
PR=loremaster/loremaster/principals.py; GV=loremaster/loremaster/governed.py
$here/mp6.sh $T A $PR $P/test_principals_cli.py
$here/mp6.sh $T B $GV $P/test_fail_closed_shapes_63c_13b.py
$here/mp6.sh $T C $PR $P/test_principals_cli.py
$here/mp6.sh $T D $PR $P/test_preboot_schema_precondition_63c_13d.py
$here/mp6.sh $T E $PR $P/test_preboot_schema_precondition_63c_13d.py
$here/mp6.sh $T F1a $PR $P/test_am37_13_3_63c_i_a.py
$here/mp6.sh $T F1b $PR $P/test_am37_13_3_63c_i_a.py
$here/mp6.sh $T F2 $PR $P/test_am37_13_3_63c_i_a.py $P/test_principals_cli.py
$here/mp6.sh $T G $GV $P/test_am37_13_4_63c_i_a.py $P/test_am37_13_3_63c_i_a.py
echo "CHAIN DONE $(date -u +%H:%M:%SZ)" > $SP/mutchain6.done
```

### §A.13 `probe_fork2.py` / `adm5.py` — re-used VERBATIM from coldaudit-63c-i-a-5 (pasted in that report's §A.5 / §A.7; byte-identical copies run from my scratch as `probe_fork2_a5.py` / `adm_a5.py`)

### §A.14 Mutation definitions (`mutdefs/`; A, B, D, E copied byte-exact from coldaudit-5 §A.13; C re-anchored; F1a, F1b, F2, G new). Declared-set md5s:
```
feb299313364455089b5ac377a189574  A.decl
71f17d43abdb716af616e30250366181  B.decl
61e3e4139acb40455aaffc3fc7983ebf  C.decl
54af3402dde83093b62c925765df1b6c  D.decl
ed4742f5ff58b72fc91285ec27a9d15c  E.decl
830a18ef32e4389d7f686589b0c0fd00  F1a.decl
28acc232514515371843ccd1118b271b  F1b.decl
755e2eb107eb05606d9ddd192be03b0a  F2.decl
ddea7f46fceef5e396a7d16294558379  G.decl
```

**C** — anchor:
```
    validate_governed_table(args.table, domain=governed_tables(), verb=_REPORT_VERB)
```
replacement:
```
    pass  # MUTATION C: dispatch-level report validation bypassed
```
declared reds:
```
loremaster/tests/test_principals_cli.py::TestHonestLabels::test_an_invalid_table_is_refused_before_any_store_call[report-unmigrated]
```

**F1a** — anchor:
```
        if self._quote is not None:
            raise GovernedStatementError(f"an unterminated {self._quote} string in {statement!r}")
        if self._closers:
            raise GovernedStatementError(f"{len(self._closers)} unclosed bracket(s) in {statement!r}")
```
replacement:
```
        if self._quote is not None or self._closers:
            return items  # MUTATION F1a: narrow to the items parsed so far instead of raising
```
declared reds:
```
loremaster/tests/test_am37_13_3_63c_i_a.py::TestTheSetParserIsCompleteOrRaises::test_an_unreadable_statement_raises[open-paren-at-end]
loremaster/tests/test_am37_13_3_63c_i_a.py::TestTheSetParserIsCompleteOrRaises::test_an_unreadable_statement_raises[open-quote-at-end]
loremaster/tests/test_am37_13_3_63c_i_a.py::TestGovernedStatementErrorTracebacks::test_an_unreadable_leg_literal_reaches_main_as_a_traceback
```

**F1b** — anchor:
```
        if match is None:
            raise GovernedStatementError(
                f"a SET item that is not `<column> = <value>`: {item!r} in {statement!r}"
            )
```
replacement:
```
        if match is None:
            continue  # MUTATION F1b: skip the unreadable item (a subset) instead of raising
```
declared reds:
```
loremaster/tests/test_am37_13_3_63c_i_a.py::TestTheSetParserIsCompleteOrRaises::test_an_unreadable_statement_raises[trailing-item-without-equals]
```

**F2** — anchor:
```
    handler.addFilter(RedactingFilter())
```
replacement:
```
    pass  # MUTATION F2: no RedactingFilter on the lore-adm stderr sink
```
declared reds:
```
loremaster/tests/test_am37_13_3_63c_i_a.py::TestTheCliSinkIsRedacted::test_the_cli_stderr_handler_carries_a_RedactingFilter
loremaster/tests/test_am37_13_3_63c_i_a.py::TestTheCliSinkIsRedacted::test_the_stderr_log_record_is_scrubbed_end_to_end
```

**G** — anchor:
```
    validate_governed_table(table, domain=governed_tables(), verb="report-unmigrated")
```
replacement:
```
    from loremaster.principals import _MIGRATE_VALID_TABLES as _MUTATION_G_DOMAIN

    validate_governed_table(table, domain=_MUTATION_G_DOMAIN, verb="report-unmigrated")  # MUTATION G
```
declared reds:
```
loremaster/tests/test_am37_13_4_63c_i_a.py::TestTheReportDomainIsTheGovernedSet::test_the_report_count_accepts_every_governed_table[finding]
loremaster/tests/test_am37_13_4_63c_i_a.py::TestTheReportDomainIsTheGovernedSet::test_the_report_count_accepts_every_governed_table[task]
loremaster/tests/test_am37_13_4_63c_i_a.py::TestTheRestoreReadBackServesEveryGovernedTable::test_read_back_completes_with_one_scope_none_count_per_governed_table
loremaster/tests/test_am37_13_4_63c_i_a.py::TestTheReadBackServesThePendingRemedy::test_the_pending_tables_report_their_packet_never_a_migrate_verb
loremaster/tests/test_am37_13_3_63c_i_a.py::TestTheReportRemedyIsDerived::test_the_remedy_names_a_migrating_verb_or_none[finding]
loremaster/tests/test_am37_13_3_63c_i_a.py::TestTheReportRemedyIsDerived::test_the_remedy_names_a_migrating_verb_or_none[task]
```

