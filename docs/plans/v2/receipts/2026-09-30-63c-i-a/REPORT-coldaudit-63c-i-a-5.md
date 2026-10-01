brief-base v18 read · brief project v7 read

# REPORT-coldaudit-63c-i-a-5 — cold RE-CHECK audit of the 63c-i-a FINAL patch (`bec29190…`, am-37 §13 / §13.1 / §13.2 fold)

## SUMMARY BLOCK
- **VERDICT: GO — conditional on ONE owed receipt (§3 mutation proofs NOT DONE: held at the ≥20 GiB memory gate 18:18Z→20:02Z, never admitted, never bypassed).** Every §13 / §13.1 / §13.2 clause holds by construction and by receipt (§1); FORK-2's served auth path still DENIES with no leak (§2a); the new reference facts reproduce independently on 3.2.4 (§2c); targeted 70 files **268 failed / 5117 passed, owned 268, ORPHAN 0**, every 63c pin file 0 reds (§4); typecheck 83 = the prior build's IDENTICAL error set, ruff clean, RED_ORPHANED 0 on the run legs (§5); **REAL DIRTY STORE: pre-boot `--table agent` serves the D teaching refusal (three spans, exit 1, row content byte-identical); `engine_error` + `caused by` reach stderr natively; post-boot receipts = audit-4 §7.4 except the renamed key; counts = direct SELECT; idempotent; reaped** (§6). The owed receipt: §13.1 item 5 names the audit's one-derivation mutation (my mutation E) as required — the lead either accepts fixup round 4's author-side mutation proofs for it or re-runs `mutchain.sh` (§A.12b, declared + collect-confirmed) when memory admits.
- **state:** done-with-deviations.
- **deviations:** (1) §3 NOT DONE (memory gate; see §W). (2) §6 ran concurrently with §4 instead of strictly after checks 1–5 (no pytest in §6; own DB). (3) a control principal was added + deleted on the dump in §6(iv) (restored to audit-4's one-admin state before §6(v)). (4) my own mutation chain was stopped by PID at the bound so no unattended pytest starts after exit; `mut5` verified unmutated.
- **Packages considered:** none — no mechanism specified (a grader; probes reuse the SDK, the gate's own junit reader/registry, `scripts/mutation_proof.py`).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none (no production symbol introduced; instruments pasted §A).
- **Graded:** `5746de5` + patch `bec291900a49c2e5df0704ef912fd5b9` · HEAD-at-report: `5863328` · DIFFERENT (3 docs-only commits: `REPORT-blindreader-63c-i-a-5.md` + two `REPORT-lead-63c.md` entries; nothing under `loremaster/`, `scripts/`, `docs/reference/` moved; `git apply --check --cached` of the patch OK at `5863328`).
- **New findings:** **#527** MINOR (introduced) — `_fault_line` never terminates on a cyclic `__cause__` (probe: 2 hang cells, control terminates) · **#528** MINOR (spec-originated) — `report_unmigrated_governed_rows`' "ONLY caller" docstring is false (`scripts/restore_prod_dump.py`) · MINOR — `_rows_stamped`'s post-commit wrong-shape message names no landed write (F-5's property, 3 legs) · 3 NITs (§7 #19/#21/#31) · receipt: §13.2's "agent-first first" prediction did not hold — the schema teaching arrives first (§6 iii).
- **decisions-needed:** (a) accept GO without my mutation receipts, or re-run §A.12b first; (b) fold #527 (one line + one cell) and #528 (reword) into the commit, or residual them; (c) the `_rows_stamped` F-5 sibling: fold or residual. Cross-reference, NOT re-verified by me: blindreader-5's MAJOR "CLI log sink bypasses RedactingFilter" (`585388f`) — my §1.A secret-guard awk (the spec's ruled instrument) was clean, but it does not examine filters on the new handler.
- **receipt pointers:** §1 construction · §2 lead items · §3 mutations (NOT DONE) · §4 targeted run · §5 gates · §6 dirty store · §7 NL sweep · §R residuals · §W gate wait · §A instruments.

## §0 Capability check / setup (measured 2026-09-30, spawn 18:01:06Z, hard deadline 19:51Z + memory-gate waits)
- lore_comms: registered `coldaudit-63c-i-a-5` (session `63c-20260924`, role audit, cadence ≤20m) — OK.
- grep/rg are hook-blocked (#473) → every text sweep is `awk`/`find`. `lore_impact` caps covering tests at 15 (#518)
  and lore indexes the MAIN tree, not my scratch copy → the covering-test set is AST-derived (instrument §A.2).
  Fallback said out loud; known shape (#518/#507), nothing new to file.
- Scratch `audit5`: `scripts/scratch_copy.sh` → `git reset --hard HEAD && git clean -fd` → `git status --short`
  printed nothing → patch md5 `bec291900a49c2e5df0704ef912fd5b9` ✅ → `git apply` clean (20 files: 18 modified +
  2 new test files). `loremaster.__file__` =
  `…/15893c68-…/scratchpad/audit5/loremaster/loremaster/__init__.py` (inside the copy).
- Scratch `audit5prev` = HEAD + prior audited patch `5f2d7c4366d469e5c2a34d53aa235d6e` ✅ (`loremaster.__file__` inside
  `audit5prev`). Delta 5f2d7c43 → bec29190 touches exactly: `governed.py`, `principal_keys.py`, `principals.py`,
  `docs/reference/surrealdb-31-capabilities.md`, `test_engine_rejection_seam.py`, `test_principals_cli.py`, and the
  2 new files `test_fail_closed_shapes_63c_13b.py`, `test_preboot_schema_precondition_63c_13d.py` (`diff -rq`).
- Scratch `mut5` = HEAD + bec29190 (for mutations, so no mutation ever touches the tree the targeted run uses);
  `principals.py` / `governed.py` `cmp`-identical to `audit5`; `loremaster.__file__` inside `mut5`.
- HEAD at spawn: `5746de5` (main tree).

## §1 am-37 §13 A–D, §13.1, §13.2 — by construction + receipt (code read in `audit5`; the builder's tables were not used as evidence)

### §1.A The lore-adm error line teaches the cause
| clause | construction (symbol) | receipt |
|---|---|---|
| (i) stderr WARNING handler on the `loremaster` logger, `%(message)s` + `error_class`/`engine_error` extras | `principals._cli_logging` (contextmanager) installs ONE `_CliStderrHandler(sys.stderr)` at WARNING with `_CliLogFormatter`; `main()` = `with _cli_logging(): return asyncio.run(_dispatch(args))`; extras `_CLI_LOG_EXTRA_KEYS = ("error_class","engine_error")` (the seam's `url` extra deliberately not rendered) | mutation A (§3) + the real dump (§6 iv) |
| idempotent across calls | `_cli_logging` removes every stale `_CliStderrHandler` BEFORE adding, and removes its own in `finally` | pinned by `test_repeated_invocations_do_not_duplicate_the_log_line` (green, §4) |
| (ii) the cause chain | `principals._fault_line`: `lore-adm: {error}` + one `  ← caused by: {cause}` per `__cause__` link, messages only, consecutive duplicates collapsed, empty message → class name. The §11 handler prints `_fault_line(error)` | probe `probe_faultline.py` CONTROL (§A.4): `"lore-adm: outer\n  ← caused by: mid\n  ← caused by: 'root'"` (the duplicate `mid` collapsed) |
| F-13 neutral contexts | `create` → `could not create principal {email!r}`; `set_subject` → `could not bind subject to principal {email!r}`; `PrincipalKeyStore.mint` → `could not mint key {name!r} for principal {email!r}` | awk over every `wrap_store_rejection(` call + 3 lines in `principals.py`/`keeps.py`/`principal_keys.py` for `already exist|collid` → **0 hits** |
| secret guard | — | awk over every `extra=` span (to its balancing `}`) in `store/_txn.py`, `principals.py`, `keeps.py`: **spans=12, password/token/secret hits=0** (instrument §A.3) |

**NEW DEFECT — finding #527 (MINOR, introduced by this patch) — `_fault_line` never terminates on a cyclic `__cause__` chain.**
The walk is `while cause is not None: … cause = cause.__cause__` with no visited-set. Probe (§A.4), each cell in a
thread bounded at 3 s: CONTROL (3-link chain) terminates; **CELL-1 `e.__cause__ = e` → HANG; CELL-2 `a↔b` → HANG**.
lore-adm would spin at 100% CPU instead of printing and exiting 1. CLASS: *every exception-chain walker terminates on
any chain* (domain: every `__cause__`/`__context__` walker in the workspace — awk found exactly two: this one and
`scripts/forgery_door_sweep.py`, which already carries the house guard `while current is not None and id(current) not
in seen`). SIBLINGS TRIED: both walkers. SIBLINGS NOT TRIED: none found. Reachability for the HONEST developer: low —
a cycle needs a re-used exception object (`raise e from e`, or two caught errors chained into each other); stdlib
`traceback` guards the same case with a seen-set. Fix shape (not mine to build): the `seen`-set guard, one line.
**Verdict: MINOR, not GO-blocking by itself; recommend fixing in the commit (one line + one pinned cell) — the lead rules.**

**CONFIRMED RESIDUAL (builder FLAG-4)** — CELL-3: a cause message carrying a newline prints as-is, so an engine text
`"engine said\nlore-adm: everything is fine"` renders a forged `lore-adm:` line on stderr. Operator's own terminal,
not a served MCP surface (spec §13 A: messages only, no sanitiser ruled). Already routed by the lead as a residual.

### §1.B Fail-closed shapes — ONE policy
- **The allowlist, DERIVED** (instrument §A.1 `shape_scan.py`: every function in `principals.py` / `governed.py` /
  `principal_keys.py` / `keeps.py` whose body calls `isinstance(<x>, …list|dict…)`):
  - FINAL (`bec29190`): **exactly `governed.group_all_count`, `governed.rows_of`, `governed.map_of`** — nothing else
    in any of the four files.
  - PRIOR (`5f2d7c43`): `_governed_select`, `_agent_migration_preconditions`, `_rows_stamped`, `_table_exists`,
    `PrincipalStore._as_rows`, `authorize_guarded`, `group_all_count`, `PrincipalKeyStore._as_rows` — every one of the
    seven non-helpers is gone or routed.
- **Routed readers** (awk of every `_as_rows|rows_of|map_of|group_all_count` site):
  `_rows_stamped` = `len(rows_of(update_result, noun=noun))` (noun REQUIRED, no default); `_governed_select` →
  `rows_of`; `delete`'s `cascaded` → `group_all_count(…, noun="cascaded principal-key count")`; `PrincipalStore._as_rows`
  → `rows_of` (and `KeepStore` reads through `PrincipalStore._as_rows` at 6 sites, so keeps are fail-closed too);
  `PrincipalKeyStore._as_rows` → `rows_of` (FORK-2); `_table_exists` → `map_of(…, required=("tables",))` (**was
  fail-OPEN: now fail-closed**); `_agent_migration_preconditions`' INFO FOR DB → `map_of(…, required=("tables",))`, the
  cloned third policy deleted; D's INFO FOR TABLE → `map_of(…, required=("fields",))`; `authorize_guarded`'s pre-read
  → `rows_of(pre_read, noun="governed pre-read")`, and its `rows[0] if isinstance(...) else {}` coercion is gone.
- F-5: the message leg's leftover read runs under `wrap_store_rejection(PrincipalStoreError, f"the backfill landed
  ({backfilled} message row(s) stamped) but the leftover count read failed")`, with `backfilled` computed BEFORE it. ✓
- `delete`'s docstring claim ("a wrong-shaped answer … wrapped by `wrap_store_rejection`") holds by construction:
  `rows_of`/`map_of`/`group_all_count` raise plain `SurrealStoreError`, which is `wrap_store_rejection`'s `catch`
  class and is not one of its pass-throughs (`SurrealConnectionError`, `TxnContentionExhaustedError`).

### §1.C Honest labels and prose
- `messages_left_unmigrated` is the field (`MigrateGovernedResult`), the receipt key, and the stderr sentence
  (text = spec §13 C F-4 verbatim, with the `migrate-governed --table message:` prefix).
- **BARE sweep `unsound_sender_messages`** (find + awk over every `*.py/*.md/*.yaml/*.yml/*.toml/*.sh/*.txt` in the
  final tree; `.venv`/`.git`/caches pruned), every hit adjudicated:
  - `docs/design/2026-09-29-packet63c-amendment-37.md` ×6 — the ruling's own history (§6/§8/§10/§13), kept by ruling. OK.
  - `loremaster/tests/test_principals_cli.py` ×1 — `_RETIRED_FIELD = "unsound_sender_messages"`, the retired-name
    pin's own needle. OK.
  - tracked historical reports `REPORT-blindreader-63c-i-a-4.md` ×6, `REPORT-builder-63c-i-a-fix2.md` ×5,
    `-fix3.md` ×15, `-fix6.md` ×3, `REPORT-coldaudit-63c-i-a-4.md` ×13, `REPORT-lead-63c.md` ×9,
    `REPORT-sidecar-63c-2.md` ×2 — dated receipts of the pre-rename world. OK (archive, not served).
  - production source, `docs/reference/`, every other test: **0**.
- `--table` help for BOTH verbs = `f"… ({_TABLE_HELP_DOMAIN})"`, `_TABLE_HELP_DOMAIN = f"one of: {', '.join(_MIGRATE_VALID_TABLES)}"`. ✓
- ONE validator `_is_governed_table`, called by `_dispatch_migrate_governed` (before any store is BUILT), inside
  `migrate_governed` (first line), and by `_dispatch_report_unmigrated` (before `build_principal_store`). ✓
  Mutation C (§3) proves the report-unmigrated leg.
- `report_unmigrated_governed_rows`' "STUB / runnable-RED" docstring and `governed.py`'s module docstring are rewritten;
  awk over `governed.py` for `STUB|runnable-RED|NotImplementedError` → 0.
- **NEW DEFECT — finding #528 (MINOR, NL-vs-code; the spec carried it) — `report_unmigrated_governed_rows`' new docstring states a
  false universal:** *"Its ONLY caller is the `lore-adm report-unmigrated` verb … so the caller validates it against
  `principals._MIGRATE_VALID_TABLES` BEFORE calling."* A second production caller exists:
  `scripts/restore_prod_dump.py` (its read-back counts helper: `{table: await
  governed_module.report_unmigrated_governed_rows(handle, table) for table in governed}`), whose `governed` list is
  derived from the dump's schema, not validated through `_is_governed_table`. am-37 §13 C N-1 itself says "its ONLY
  caller is the verb" — the builder executed the spec verbatim; the miss is the spec's, and it is the #507 shape
  (`scripts/` is outside lore's graph, so a `lore_impact`-derived caller set cannot see it). CLASS: *a docstring's
  caller-set claim equals the derived caller set* (domain: every call site of the symbol across `loremaster/` +
  `scripts/`). Fix shape: reword to "its callers are the verb and `scripts/restore_prod_dump.py`'s read-back; each
  passes a name it validated" — or validate inside the function. Not GO-blocking by itself.

### §1.D The pre-boot schema teaching precondition
- ONE `INFO FOR TABLE {table}` in `_agent_migration_preconditions`, AFTER the `INFO FOR DB` gate, only when `table in
  defined` (an undefined table short-circuits: one `INFO FOR DB`, no field read — the one-read pin's premise holds),
  read through `map_of(…, required=("fields",))`; the answer rides `AgentMigrationPreconditions.defined_fields:
  frozenset[str]` (default `frozenset()`), beside `defined_tables`. ✓
- Columns DERIVED from each leg's own statement: each leg builds its FUNCTION-LOCAL `backfill_statement` first and
  calls `_schema_predates_refusal(TABLE, backfill_statement, defined_fields)`, which calls `_set_columns(statement)`
  (a depth-aware top-level `SET … WHERE|RETURN|TIMEOUT|PARALLEL` parse). No column list exists anywhere in production
  (the three statements are the only sources). The SAME literal is then passed to `governed_exempt(...)` and executed. ✓
- One backtick span PER column: `", ".join(f"`{column}`" for column in missing)`. ✓
- `MigratePreconditionCounts` unchanged: the delta touches no line of it (diff §0). ✓
- §13.2 ordering bound: `_migrate_memory_scope`, `_migrate_agent_owner`, `_migrate_message_owner` each carry the
  `ORDERING BOUND (am-37 §13.2)` paragraph with the ruled sentence verbatim; in code the gate is the first statement
  after the imports + literal in each leg (before operator resolution / keep mint / counts / backfill; in the message
  leg before `_message_leg_refusal`). ✓ The verb-level `_verb_level_refusal` + precondition READS precede it, as §13.2 accepts.

## §2 Lead audit items
### §2(a) FORK-2 — `PrincipalKeyStore._as_rows` → `rows_of`; the SERVED auth path with the fault injected
Instrument `probe_fork2.py` (§A.5): the REAL composed ASGI app (`build_mcp_server` + `build_asgi_app`, LAN_BEARER
posture, the SDK auth + session stack real, the heavy lifespan stubbed exactly as `_auth_fixtures.stub_heavy_startup`
does), an httpx client POSTing `initialize` to `/mcp` with a WELL-FORMED `probe-key:<secret>` bearer (a colon-free
bearer never reaches the lookup — it is the malformed deny). The ONLY substitution: `PrincipalKeyStore._query`
answers the hash lookup with the cell's value; every principal-store lookup is trapped to raise (none fired). The
response body AND headers are scanned for `Traceback`, `SurrealStoreError`, the `rows_of` message fragments, the
presented SECRET, `sha512`, `ws://`, `18000`, `18500`, `engine`, `password`.
| cell | FINAL `bec29190` | PRIOR `5f2d7c43` |
|---|---|---|
| CONTROL-empty (`[]`, no such key) | **401** `invalid_token` + `WWW-Authenticate: Bearer error="invalid_token"`; leaks [] | 401, leaks [] |
| CONTROL-rejected (lookup raises `SurrealStoreError`, the pre-existing class) | **500** body `Internal Server Error`; leaks [] | 500, leaks [] |
| FORK2-str (`"garbage"`) | **500** `Internal Server Error`; leaks [] | 401 `invalid_token` |
| FORK2-nondict-member (`["x"]`) | **500** `Internal Server Error`; leaks [] | 401 `invalid_token` |
| FORK2-dict (`{"name": …}`) | **500** `Internal Server Error`; leaks [] | 401 `invalid_token` |
- **Verdict: HOLDS.** A wrong-shaped lookup still DENIES (no `AccessToken` is minted, the session never opens); the
  5xx body is Starlette's generic `Internal Server Error` with no engine detail, no credential, no internals; and the
  fate is exactly the pre-existing fate of a REJECTED lookup (CONTROL-rejected), so FORK-2 adds no new failure class to
  the served path. The prior build served a store fault as `invalid_token` + "clear authentication tokens … reconnect" —
  a false teaching to the client; the 500 is the honest one.

### §2(b) `_BACKFILL_UPDATE_NOUN` gone; `_rows_stamped` has no default
- `find … -name '*.py' | xargs awk '/_BACKFILL_UPDATE_NOUN/'` over the whole final tree → **0 hits**.
- `def _rows_stamped(update_result: Any, *, noun: str) -> int:` — keyword-only, **no default**; its three production
  callers pass `"governed memory-scope backfill"`, `"governed agent backfill"`, `"governed message-owner backfill"`.
- (Observation, not a defect: `PrincipalStore._as_rows` keeps a default `noun="principal-substrate query"` — it only
  labels a message and nothing branches on it; the ruled default removal was `_rows_stamped`'s.)

### §2(c) The new `docs/reference/surrealdb-31-capabilities.md` §1.9 facts — re-probed independently
Instrument `probe_ref19.py` (§A.6): my OWN SCHEMAFULL table `t19` (fields `a`, `b`) + a SCHEMALESS `t19e`, in a
minted `test_audit5_ref19_<hex>` on `ws://127.0.0.1:18000` (port asserted), NOT the production DDL the builder used.
- Engine: `surrealdb-3.2.4+20260803.93ab219` (MEASURED — the reference says "3.2.4 per MEMORY.md, not re-measured"; consistent).
- F1: `INFO FOR TABLE nosuch19` → `{'events': {}, 'fields': {}, 'indexes': {}, 'lives': {}, 'tables': {}}`, no error;
  and a DEFINED field-less table `t19e` answers **byte-identically** (`identical=True`) — the reference's "an undefined
  table and a defined table with no fields answer identically" HOLDS. ✓
- F2: control — before the REMOVE, `INFO FOR TABLE t19` lists `b`, and `UPDATE t19 SET b = 7 WHERE a = 1` over one row
  stamped it. After `REMOVE FIELD b ON TABLE t19` (answers `None`; `b` gone from `fields`): the same UPDATE over **0
  rows → `[]` (silent)**; over **1 row → `InternalError: Found field 'b', but no such field exists for table 't19'`**. ✓
- Reaped: `REMOVE DATABASE` → `INFO FOR NS` no longer lists it (`present = False`). (Bound: this probe did not print a
  before-control listing; the dump reap in §6(vi) carries the before/after pair.)

## §6 THE REAL DIRTY STORE — `test_dump_20260930T180530Z_afabf225d81f4ad5a423601085c26bbd` (the lead's restore, name read from the lead's `audit5-dump.txt`), `ws://127.0.0.1:18000` ns `lore_test`
Measured 2026-09-30 18:15–18:17Z on HEAD `5746de5` + patch `bec29190` (the `audit5` copy). Port asserted `18000` before
every call (instruments §A.7 `adm5.py` — audit-4 §A.2's loader swap, needed because of #525 — and §A.8 `dq5.py`,
§A.9 `ddl5.py`). `:18500` never addressed. **Ordering deviation (disclosed):** §6 ran while the targeted pytest run
(§4) and the mutation chain (§3) were in flight, instead of strictly after checks 1–5 — lore-adm/probe processes are
not pytest and use their own DB; nothing in §6 depended on §3/§4.

### §6.0 Baseline (direct SELECT, before any lore-adm call)
agent 95 / memory 177 / message 316 / brief 26; every agent/message row `scope IS NONE AND owner_principal IS NONE`
(95/316), memory/brief `scope IS NONE` 177/26; `sender IS NONE` 0; `principal` and `keep` tables NOT defined. `INFO FOR
TABLE agent` fields = the pre-63 set only (`checkpoint, heartbeat_at, last_note, model, name, registered_at, role,
session, spawned_by, status, task_id`); `memory` has no `scope`; `message` has no `owner_agent`/`owner_principal`/`scope`.
**= audit-4 §7.0's counts exactly.**

### §6(i) Operator bootstrap (+ a bonus receipt before it)
```
$ lore-adm migrate-governed --table agent          # 0 principals, BEFORE the bootstrap
  stderr| lore-adm: migrate-governed --table agent REFUSED: the `agent` table has no `owner_principal`, `owner_agent`, `scope` column(s) — this store's schema predates the governed columns; boot the new image once (its DDL defines them), then re-run migrate-governed
  exit=1
$ lore-adm add --email operator@audit5.test --role admin --display-name audit5-operator      exit=0
$ lore-adm list →  operator@audit5.test  audit5-operator  active  admin  expires=-
```
(At 0 principals the schema teaching now precedes the operator refusal audit-4 saw — the gate is the leg's first act, §13.2.)

### §6(ii) PRE-BOOT `migrate-governed --table agent` → the D teaching refusal, ZERO writes
```
BEFORE snapshot: e9c665f3f9d9   (md5 of SELECT * FROM agent/memory/message/keep/member_of/principal)  agent NONE-pair 95 · keep 0 · member_of 0
$ lore-adm migrate-governed --table agent
  stderr| lore-adm: migrate-governed --table agent REFUSED: the `agent` table has no `owner_principal`, `owner_agent`, `scope` column(s) — this store's schema predates the governed columns; boot the new image once (its DDL defines them), then re-run migrate-governed
  exit=1
AFTER  snapshot: e9c665f3f9d9   agent NONE-pair 95 · keep 0 · member_of 0
```
Exactly the three missing columns, ONE backtick span each, exit 1, no keep minted, row content byte-identical. The
snapshot's power to SEE a write is shown in §6(v) (it changes after the migrate). **D's acceptance receipt: MET.**
(audit-4 §7.3 on the same dump shape: `governed.agent_backfill.rejected` + "unspecified rejection; see the server log".)

### §6(iii) The §13.2 rider — `--table message` (and `memory`) on the PRE-BOOT dump
```
$ lore-adm migrate-governed --table message
  stderr| lore-adm: migrate-governed --table message REFUSED: the `message` table has no `owner_agent`, `owner_principal`, `scope` column(s) — this store's schema predates the governed columns; boot the new image once (its DDL defines them), then re-run migrate-governed
  exit=1
$ lore-adm migrate-governed --table memory
  stderr| lore-adm: migrate-governed --table memory REFUSED: the `memory` table has no `scope` column(s) — …
  exit=1
AFTER (iii) snapshot: e9c665f3f9d9   (still zero writes)
```
**Receipt: the SCHEMA teaching arrives FIRST for `--table message`, not the agent-first order §13.2 "expected".** Why, by
code: the agent-first ORDER lives in `_message_leg_refusal`, which the message leg calls AFTER its schema gate;
`_verb_level_refusal` (the only thing that may precede the gate) holds owned-unscoped agents / ownerless-scoped agents
(+ message problem parts when those fire) — all impossible on a pre-boot store, where every governed column reads NONE.
So §13.2's premise "every `_verb_level_refusal` teaching is … the agent-first order …" misplaces the agent-first check
(spec-prose inaccuracy, no code defect); the outcome is the stronger one (the true schema prerequisite first). The
agent-first teaching does arrive on the next run after the boot, before `--table agent` — §6(v).

### §6(iv) Class A on real engine rejections — `engine_error` on stderr + a wrapped fault's `caused by`
```
$ lore-adm add --email operator@audit5.test --role admin --display-name audit5-dup
  stderr| principal.query.rejected [error_class=unique violation — the record id or a unique index value is already taken; re-read the row; engine_error=Database index `principal_email` already contains 'operator@audit5.test', with record `principal:toxgyv5j07p9xlkcnv5u`]
  stderr| lore-adm: could not create principal 'operator@audit5.test'
  stderr|   ← caused by: SurrealDB principal query rejected against 'ws://127.0.0.1:18000/rpc' (unique violation — the record id or a unique index value is already taken; re-read the row); see the server log for the full engine detail
  stderr|   ← caused by: Database index `principal_email` already contains 'operator@audit5.test', with record `principal:toxgyv5j07p9xlkcnv5u`
  exit=1
```
The seam's own record (with `error_class` + `engine_error`) is on stderr, so "see the server log" now resolves; the
neutral F-13 context; the typed cause chain; no traceback; no credential (the `url` is creds-free). The adm driver
attaches NO log handler (audit-4 needed `logextra.py`; §A.7 does not). Control: `add --email second@audit5.test` exit 0,
then `delete --email second@audit5.test` → `deleted second@audit5.test (0 key(s) removed)` exit 0 — the fail-closed
`cascaded` count (§13 B F-1) accepts the REAL engine answer shape (positive control for B on a real store); the extra
principal was removed so §6(v) ran under audit-4's one-admin conditions.

### §6(v) Boot DDL, then migrate — receipts vs audit-4 §7.4, counts = direct SELECT, idempotent
report-unmigrated BEFORE: agent 95 / memory 177 / message 316 / brief 26, each with its WARNING line now on stderr natively.
Boot DDL (`ddl5.py`, the audit-4 §A.4 generator list): `generate_ddl(dim=2048)` 175 · agent 24 · message 28 · brief 14 ·
audit 11 · task 15 · finding 16 statements — **0 not-OK** (= audit-4).
```
# post-boot, --table message BEFORE --table agent
snap before: 189f89b4a160
$ lore-adm migrate-governed --table message
  stderr| lore-adm: migrate-governed --table message REFUSED: cannot migrate `message` rows before the `agent` table is migrated (95 un-migrated (NONE-scope) agent(s) remain) — a message's owner_principal is read from sender.owner_principal, NONE for every un-migrated agent (§2.6 agent-first ORDER); run migrate-governed for `agent` first
  exit=1
snap after: 189f89b4a160
$ lore-adm migrate-governed --table agent    stdout| migrate-governed --table agent: scanned=95 backfilled=95 already_migrated=0 messages_left_unmigrated=None      exit=0
$ lore-adm migrate-governed --table memory   stdout| migrate-governed --table memory: scanned=177 backfilled=177 already_migrated=0 messages_left_unmigrated=None   exit=0
$ lore-adm migrate-governed --table message  stdout| migrate-governed --table message: scanned=316 backfilled=316 already_migrated=0 messages_left_unmigrated=0     exit=0
$ lore-adm migrate-governed --table brief    stderr| lore-adm: migrate-governed --table brief REFUSED: migrate-governed does not yet migrate `brief` — … nothing was written   exit=1
snap after migrate: a6ce1443944a      (≠ 189f… — the snapshot SEES writes: positive control for §6(ii))
=== RE-RUN
agent 95/0/95 None · memory 177/0/177 None · message 316/0/316 0 · brief REFUSED (same line) — exits 0/0/0/1
snap after re-run: a6ce1443944a      (row content byte-identical: idempotent)
report-unmigrated AFTER: agent 0 · memory 0 · message 0 · brief 26 (+ its WARNING)
```
**Every receipt line equals audit-4 §7.4's except the renamed key `messages_left_unmigrated` (was
`unsound_sender_messages`).** Served vs direct (`dq5.py`, verbatim values):
| table | served | direct after | invariants (with controls) |
|---|---|---|---|
| agent | 95/95/0 → 95/0/95 | count 95; scope NONE 0; owner NONE 0 | ONE group: owner `principal:toxgyv5j07p9xlkcnv5u` (the operator) × `keep:01M3SRHA6MGFMPW1FXJVXH0FP1` n=95; `owner_agent != id` 0 (CONTROL `= id` 95) |
| memory | 177/177/0 → 177/0/177 | scope NONE 0 | ONE group: owner_principal NONE, owner_agent NONE, scope = the project keep, n=177 |
| message | 316/316/0 → 316/0/316; `messages_left_unmigrated=0` | scope NONE 0; `scope IS NONE AND owner_principal IS NONE` 0 (= the field) | ONE group owner = operator × project keep n=316; `owner_agent != sender` 0 (CONTROL `= sender` 316); `owner_principal != sender.owner_principal` 0 |
| brief | refused, nothing written | scope NONE 26 | — |
Project keep: exactly ONE (`key project:lore`, type project, keeper = the operator, name `lore`); `member_of` 1 — the
three pre-boot refusals and the post-boot message refusal minted nothing.

### §6(vi) Reap
```
BEFORE: present in INFO FOR NS databases = True (of 59 dbs)
$ uv run python scripts/restore_prod_dump.py --reap test_dump_20260930T180530Z_afabf225d81f4ad5a423601085c26bbd
restore_prod_dump: reaped test_dump_20260930T180530Z_afabf225d81f4ad5a423601085c26bbd (absent from INFO FOR NS)
reap exit=0
AFTER:  present in INFO FOR NS databases = False (of 58 dbs)
```

## §5 Gates (the `audit5` copy, tracked-tree md5 `f1daeeb1`, final bytes)
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` (exit 1):
  `typecheck RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract …` · `ruff GREEN` ·
  `pytest NOT_RUN — claimed by the manifest, never executed` / `CURRENCY: FAIL — claimed but never run: pytest`.
  **RED_ORPHANED 0 on the two legs run**; the pytest NOT_RUN line is the known tool-UX residual (builder FLAG-2).
- `uv run ruff check .` → `All checks passed!` (exit 0).
- `./scripts/typecheck.sh` (exit 1): lorerunes / lorescribe / loresigil / skills / docs-eval OK; **loremaster `Found 82
  errors in 31 files (checked 318 source files)`**; **scripts `Found 1 error in 1 file`**; shellcheck OK (7 .sh) — 83
  total. The SAME script on the PRIOR tree (`audit5prev`, 316 source files) → 82 + 1 = 83, and the two error sets are
  **IDENTICAL** once line numbers are stripped (`diff` of the sorted `file:message` lines) — no error was swapped under
  the adjudicated count.

## §3 Mutation proofs — NOT DONE (memory gate), everything up to the run is ready
- Mutation copy `mut5` (HEAD + bec29190; `loremaster.__file__` inside `mut5`). Five mutations defined BEFORE any run
  (§A.13: anchor, replacement, declared reds): **A** handler never installed (`with _cli_logging():` → `if True:`),
  17 declared reds = `test_the_server_log_pointer_resolves_to_stderr[<every derived verb>]`; **B** `map_of` tolerant of a
  non-dict answer, 8 declared (`TestMapOfContract…non_dict…[None|int|list|str]`, `TestDeleteNeverSkips…[same 4]`);
  **C** report-unmigrated validator bypassed, 1 declared (`…invalid_table…[report-unmigrated]`); **D** the schema gate
  never fires, 10 declared (7 leg×column dirty-store cells + 3 one-derivation cells); **E** (§13.1 item 5) a hand map
  missing `agent.owner_agent`, 2 declared (`[agent-owner_agent]` dirty-store cell + the one-derivation `[agent]` cell).
- Every anchor matched exactly once in `mut5` (checked); all **38 declared ids EXIST** in a `--collect-only` of the
  three files, taken after the targeted run and before any mutation run (`collect_check.txt`: A 17 · B 8 · C 1 · D 10 ·
  E 2 OK, 0 MISSING).
- The chain (`mutchain.sh` → `mp5.sh`: `cp -a` backup, process-table + ≥20 GiB gate, `mutation_proof.py` diffing both
  ways, `cmp` after) was never admitted (§W) and was stopped by PID at 20:02Z (pids 207360, 226615). `mut5`'s tracked
  diff md5 = `audit5`'s (`f1daeeb1`); `principals.py`/`governed.py` `cmp`-identical to `audit5` — no mutation landed.
- **To complete:** from the scratchpad, `nohup inst/mutchain.sh &` (it waits on the gate itself), then read `mut_{A..E}.log`
  (`mutation_proof exit=0` + `CMP: restored byte-exact` per mutation). What exists meanwhile, NOT independent of the
  author: fixup-tests-63c-i-a-2 ROUND 4 FINAL reports 5/5 mutations held on these pin files; my §6 dirty-store run
  demonstrates the D and A BEHAVIOUR directly on a real store, which shows the code works but not that the pins would
  catch its removal.

## §4 Targeted run on the final build (NO full suite)
- **Set derivation (declared before the run: `declared5.txt`, 70 files, md5 `12efd3c1`):**
  - AST covering-test scan (instrument §A.2 `changed_symbols5.py`): every top-level def/class/assignment and class
    method whose `ast.dump` differs PRIOR→FINAL in `principals.py`/`governed.py`/`principal_keys.py` — 50 changed
    symbols (list in §A.2's output) — × every test file that imports an anchor module (`principals`, `governed`,
    `principal_keys`, `keeps`, `token_verifier`) AND references a changed name (Name/Attribute/str constant) → 38 files;
  - ∪ fix6's 62-file declared set (read from its own `declared-files.txt`, md5 `2a6a8c93` ✓, identical to the list in
    its report) — the AST scan added exactly ONE file outside it (`test_search.py`);
  - ∪ the tree-scanning structural pins `test_retry_seam.py`, `test_exhaustion_fates.py`, `test_mcp_server.py`, the render
    pins (`test_render.py`, `test_render_seam_pins.py`, `test_render_slot_inventory.py`, `test_comms_render_architecture.py`,
    `test_link5_render_containment.py`, `test_memory_render_bound_63b_ib.py`, `test_render_mypy_layer{,_optout}.py`)
    ∪ `test_token_verifier.py`.
  - Bound: `scripts/test_pending_contract_gate.py` is NOT in the set — the delta 5f2d7c43 → bec29190 changes nothing
    under `scripts/` (diff §0); audit-4 ran it green on the same script bytes.
- Command (instrument §A.10 `gated_run.sh`): process table clear + MemAvailable ≥ 20 GiB, then `systemd-run --user
  --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --no-sync --with pytest-timeout pytest -n 8 --timeout=300 -q -p
  no:cacheprovider --junitxml=… <70 files>`. `ADMITTED 18:06:35Z avail=20GiB others=0 waited=20s`. No cap kill.
- **Result: `268 failed, 5117 passed, 1 skipped, 3 xfailed, 7 warnings in 669.45s`**; junit total 5389; no collection
  error.
- **Ownership of every red** against the BUILD's `scripts/pending_contracts.yaml`, through the gate's OWN
  `JUnitReportReader` + `PendingContractRegistry` + `PendingContractGate.partition_pytest` + `entries_for` (instrument
  §A.11 `own5.py`; the junit was xunit2, so `file` is derived from `classname` before the reader sees it):
  **owned 268 · ORPHAN 0** — `packet-64b-i-contract` 235 (`test_comms_footer` 81, `governed_substrate_64b` 34,
  `findings_migrate_64b` 28, `test_mcp_server` 28, `findings_classes_64b` 27, `findings_governance_64b` 24,
  `findings_system_writer_64b` 9, `findings_enforcement_64b` 4) · `packet-58-contract` 29 (`r3_tiers` 16, `r3_am6` 8,
  `r4_lease_fates` 4, `test_exhaustion_fates` 1) · both 4 (`r3_cas_seam`). **= fix6's RESUME table exactly (58: 33 incl.
  cas_seam; 64b-i: 235).**
- **File-level ownership masks per-test causes (the F-15 window), so the shared files' reds were read by CAUSE:**
  - `test_mcp_server` 28: 13× `AppContext.findings() got an unexpected keyword argument`, 12× ImportError, 3× the same
    TypeError asserted. The ONLY ImportError symbol across ALL 268 reds is `arm_finding_identity` (59×) — a 64b-i
    pending symbol.
  - `test_exhaustion_fates` 1 (`…evidence_that_HOLDS`): all 6 FATE-CHANGED sites are `store/lease.py` (58's rider).
  - **63c-owned pin files carry 0 reds:** `test_principals_cli` 216/0 · `test_engine_rejection_seam` 121/0 ·
    `test_fail_closed_shapes_63c_13b` 85/0 · `test_preboot_schema_precondition_63c_13d` 25/0 · `test_retry_seam` 678/0
    (incl. am34_5, FLAG-1 closed) · `test_keeps_cli` 49/0 · `test_keep_remediation_cli_61` 15/0 ·
    `test_fixwave_a28c_63c_i_a` 333/0 · `test_render_seam_pins` 27/0 · `test_token_verifier` 41/0 ·
    `test_principal_keys_store` 30/0 · `test_governed_migration_63a` 10/0 · `test_message_migrate_dirty_store_63b_ii_b`
    5/0 · `test_principal_delete_governed_63a` 6/0 · `test_governed_routing_63a` 7/0 · `test_memory_enforcement_63b_ia` 41/0.

## §7 Natural-language sweep of the delta's ADDED lines (production + reference; every prose unit, individually)
Method: read the whole production delta 5f2d7c43 → bec29190 (`delta.diff`, 6 files; the test-file prose was not swept
line by line — stated bound) and check each claim against code or a probe. Verdicts: OK / FALSE / NIT.
| # | site (symbol) | claim | verdict + evidence |
|---|---|---|---|
| 1 | `governed` module docstring | lists entry points + "THREE fail-closed … readers … no other function here or in `principals.py` tests a store answer's shape" | OK — every named symbol defined (awk); shape_scan §1.B |
| 2 | `governed.GovernedAuditUnavailable` | "Raised by `authorize_guarded` … BEFORE any durable effect" | OK — the only `raise GovernedAuditUnavailable` is inside `authorize_guarded`, before `guarded_write` composes |
| 3 | `MigrateGovernedResult` (`messages_left_unmigrated`) | superset of unsound-sender; `None` iff not measured | OK — code + §6(v) |
| 4 | `authorize_guarded` comment | wrong-shaped pre-read raises | OK — `rows_of` |
| 5 | `group_all_count` "Scope, as measured" | callers are `_scope_count`, leftover read, owned-row count, cascaded count, `report_unmigrated_governed_rows` | OK — awk: exactly those 5 sites. "Other GROUP ALL readers elsewhere … still carry tolerant copies" — NOT re-derived by me (routed to 64b §DRY; stated bound) |
| 6 | `rows_of` / `map_of` / `_INFO_SUB_MAP_KEYS` | the fail-closed policy | OK — code; `map_of` probed via mutation B (§3) |
| 7 | `report_unmigrated_governed_rows` | "Its ONLY caller is the `lore-adm report-unmigrated` verb … so the caller validates it" | **FALSE — finding #528** (`scripts/restore_prod_dump.py` is a second, unvalidating caller; spec-originated) |
| 8 | `PrincipalKeyStore.mint` context | neutral | OK |
| 9 | `PrincipalKeyStore.revoke` `Raises:` | wrap error named | OK |
| 10 | `PrincipalKeyStore._as_rows` | never `[]` → `verify` would deny a store fault as no-such-key | OK — §2(a) probe (prior served 401 `invalid_token`) |
| 11 | `PrincipalStore._table_exists` doc + comment | fail-closed on a wrong shape; "used to read as no tables … SKIPPED the guard" | OK — code + mutation B leg |
| 12 | `create` / `set_subject` / `set_status` / `set_expires` / `delete` `Raises:` + contexts | neutral contexts; wrap errors named; `delete` wraps a wrong-shaped answer | OK — §1.A/§1.B; §6(iv) shows the create context on a real rejection |
| 13 | `PrincipalStore._as_rows` | "`KeepStore` reads through this too" | OK — 6 `PrincipalStore._as_rows(` sites in `keeps.py` |
| 14 | `_CLI_LOGGER_NAME` comment | every store seam logs under `loremaster` | OK — seams use module loggers under the package |
| 15 | `_TABLE_HELP_DOMAIN`, `_is_governed_table` | derived help; ONE validator called before I/O by both verbs | OK — code; mutation C (§3) |
| 16 | `_refused` docstring | `messages_left_unmigrated` `None` on refusals | OK |
| 17 | 3× `ORDERING BOUND (am-37 §13.2)` | gate is the leg's first act; a verb-level refusal MAY precede it | OK — code + §6(i)(ii)(iii) |
| 18 | 3× leg comments "§1.9 item 1 … built FIRST" | literal built before any read/write | OK |
| 19 | `_migrate_agent_owner` inline comment | "— built at the top of this leg (below)." | **NIT** — the literal is ABOVE the comment (it was hoisted to the top); "(below)" points the wrong way |
| 20 | `_migrate_message_owner` docstring | F-10/F-4 superset wording | OK |
| 21 | `_migrate_message_owner` inline comment (context line, NOT added by the delta) | "the rows the self-guarding UPDATE skipped because their SENDER is unsound … are MEASURED here" | **NIT (F-4 sibling)** — the read measures every row still `scope IS NONE AND owner_principal IS NONE`, a superset; the docstring was relabelled, this comment was not |
| 22 | F-5 comment + wrap context | a failed leftover read names the landed write | OK — code |
| 23 | `AgentMigrationPreconditions.defined_fields` doc | INFO FOR TABLE on an undefined table answers EMPTY maps | OK — §2(c) probe |
| 24 | `_set_columns`, `_schema_predates_refusal` docstrings | derived from the statement; SCHEMAFULL silent over 0 rows / raises over ≥1 | OK — code + §2(c) + mutations D/E |
| 25 | `_rows_stamped` docstring + its SERVED message | "a store fault, raised as `SurrealStoreError` through `rows_of`" → renders `the governed agent backfill read answered a str, not a row list — nothing was decided from it` | docstring OK. **MINOR (F-5's property, sibling not ruled):** that message is raised AFTER the backfill UPDATE has committed (all 3 legs), calls the UPDATE a "read", and names no landed write — F-5 lifted = "a failure after a committed write names the write"; SIBLINGS: `_rows_stamped` × memory/agent/message (not probed live; by construction). Idempotent re-run bounds the harm |
| 26 | `_fault_line` docstring | messages only, duplicates collapsed, empty → class name | OK — probe CONTROL. Silent on termination → **finding #527** (cycle hang) |
| 27 | `_CliLogFormatter` / `_CliStderrHandler` / `_cli_logging` | extras rendered; idempotent; bound to current stderr | OK — §6(iv); lifecycle pin green |
| 28 | `_dispatch_migrate_governed` comment | invalid `--table` refused before any store is built | OK — code |
| 29 | receipt-line comment + stderr sentence | renamed key; sentence = spec §13 C F-4 | OK — §6(v) |
| 30 | `_render_migrate_refusal` | one stderr line; table sanitised | OK |
| 31 | `_dispatch_report_unmigrated` refusal | "the governed tables are `agent`, `memory`, `message`, `brief`; nothing was read" | OK (derived). NIT, pre-existing: `migrate-governed`'s `_not_supported` refusal for the SAME validator outcome still hand-lists the tables (`memory`, `agent`, `message`, `brief`) — two texts, one derived, one not |
| 32 | `_dispatch` docstring (F-14) | write boundaries pinned; `delete` + `KeepStore.get_or_create_keyed` wrap reads too | OK — awk: `get_or_create_keyed` contains a `wrap_store_rejection(` |
| 33 | reference §1.9 (both bullets + the 3.2.4 bracket + the `Internal` kind note) | as written | OK — §2(c) (version measured 3.2.4; `InternalError` observed) |

## §A Instruments (pasted VERBATIM — brief-base §1; the scratch trees are disposable)

### §A.1 shape_scan.py
```python
"""§13 B construction check: every function in principals.py / governed.py / principal_keys.py / keeps.py
whose body calls isinstance(<x>, list|dict|tuple...) — printed with the tested name, so the allowlist
(group_all_count, rows_of, map_of) can be compared against the derived set. Usage: shape_scan.py <tree>"""
import ast, pathlib, sys
tree = pathlib.Path(sys.argv[1])
for rel in ["loremaster/loremaster/principals.py", "loremaster/loremaster/governed.py",
            "loremaster/loremaster/principal_keys.py", "loremaster/loremaster/keeps.py"]:
    mod = ast.parse((tree / rel).read_text())
    for fn in ast.walk(mod):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        hits = []
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "isinstance" and len(node.args) == 2:
                kinds = ast.unparse(node.args[1])
                if any(k in kinds for k in ("list", "dict")):
                    hits.append(f"{ast.unparse(node.args[0])}:{kinds}@{node.lineno}")
        if hits:
            print(f"{rel.split('/')[-1]}::{fn.name}  {hits}")
```

### §A.2 changed_symbols5.py
```python
"""AST-derived covering-test set for the delta PRIOR -> FINAL (coldaudit-63c-i-a-5). lore_impact caps covering
tests at 15 (#518) and lore indexes the MAIN tree, not this scratch copy, so: (1) diff every top-level def/class
and every class method by ast.dump between the two trees over the changed production files, (2) a test file is
covering iff it imports one of the anchor production modules AND its AST references (Name / Attribute / str
constant) a changed symbol's name. Usage: changed_symbols5.py <prior_tree> <final_tree>"""
import ast, pathlib, sys
prior, final = map(pathlib.Path, sys.argv[1:3])
PROD = ["loremaster/loremaster/principals.py", "loremaster/loremaster/governed.py", "loremaster/loremaster/principal_keys.py"]
ANCHORS = ("loremaster.principals", "loremaster.governed", "loremaster.principal_keys", "loremaster.keeps",
           "loremaster.token_verifier")
def defs(path):
    out = {}
    if not path.exists():
        return out
    mod = ast.parse(path.read_text())
    for node in mod.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[node.name] = ast.dump(node)
            if isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        out[f"{node.name}.{sub.name}"] = ast.dump(sub)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name):
                    out[t.id] = ast.dump(node)
    return out
changed = set()
for rel in PROD:
    a, b = defs(prior / rel), defs(final / rel)
    for k in set(a) | set(b):
        if a.get(k) != b.get(k):
            changed.add(k.split(".")[-1])
print("CHANGED SYMBOLS:", " ".join(sorted(changed)), file=sys.stderr)
hits = []
for test in sorted((final / "loremaster/tests").glob("test_*.py")):
    src = test.read_text()
    mod = ast.parse(src)
    imports = any(a in src for a in ANCHORS)
    names = set()
    for n in ast.walk(mod):
        if isinstance(n, ast.Name): names.add(n.id)
        elif isinstance(n, ast.Attribute): names.add(n.attr)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str): names.add(n.value)
    if imports and names & changed:
        hits.append(test.name)
print("\n".join(hits))
```

Output (run 2026-09-30 on `audit5prev` → `audit5`):
```
CHANGED SYMBOLS: AgentMigrationPreconditions GovernedAuditUnavailable MigrateGovernedResult PrincipalKeyStore PrincipalStore _CAUSE_LINE_PREFIX _CLI_LOGGER_NAME _CLI_LOG_EXTRA_KEYS _CliLogFormatter _CliStderrHandler _INFO_SUB_MAP_KEYS _SET_CLAUSE_END _SET_CLAUSE_START _TABLE_HELP_DOMAIN _agent_migration_preconditions _as_rows _cli_logging _dispatch _dispatch_keep _dispatch_migrate_governed _dispatch_report_unmigrated _fault_line _governed_select _is_governed_table _migrate_agent_owner _migrate_governed_resolved _migrate_memory_scope _migrate_message_owner _refused _render_migrate_refusal _rows_stamped _schema_predates_refusal _set_columns _table_exists authorize_guarded build_parser create delete format group_all_count main map_of migrate_governed mint report_unmigrated_governed_rows revoke rows_of set_expires set_status set_subject
```

### §A.3 secret-guard awk (run in `loremaster/loremaster`) + the F-13 context sweep
```bash
awk '
/extra=/ { cap=1; span=""; depth=0 }
cap { span = span $0 "\n"; n=split($0, ch, ""); for(i=1;i<=n;i++){ if(ch[i]=="{") depth++; if(ch[i]=="}") depth-- }
      if (depth<=0) { total++; if (tolower(span) ~ /password|token|secret/) { hits++; print FILENAME":"FNR": " span } cap=0 } }
END { print "spans=" total " hits=" hits+0 }' store/_txn.py principals.py keeps.py
for f in principals.py keeps.py principal_keys.py; do awk -v F=$f '/wrap_store_rejection\(/{cap=4} cap>0{buf=buf $0; cap--; if(cap==0){ if(buf ~ /already exist|collid/) print F":"FNR": "buf; buf=""}}' $f; done
```

### §A.4 probe_faultline.py
```python
"""_fault_line probe (coldaudit-63c-i-a-5): CONTROL a 3-link chain with a consecutive duplicate; CELL-1 a
self-cycle (e.__cause__ = e); CELL-2 a 2-cycle (a<->b); CELL-3 a message with an embedded newline + a forged
`lore-adm:` line (operator stderr, FLAG-4). Each cell runs in a thread with a 3 s bound so a hang is observed,
not suffered."""
import threading
from loremaster.principals import _fault_line
def run(name, err):
    box = {}
    t = threading.Thread(target=lambda: box.setdefault("out", _fault_line(err)), daemon=True); t.start(); t.join(3)
    print(f"{name}: " + ("HANG (>3s)" if t.is_alive() else repr(box["out"])))
a = RuntimeError("outer"); b = ValueError("mid"); c = KeyError("root"); d = ValueError("mid")
a.__cause__ = b; b.__cause__ = d; d.__cause__ = c
run("CONTROL", a)
s = RuntimeError("self"); s.__cause__ = s; run("CELL-1 self-cycle", s)
x = RuntimeError("x"); y = RuntimeError("y"); x.__cause__ = y; y.__cause__ = x; run("CELL-2 two-cycle", x)
f = RuntimeError("outer"); f.__cause__ = RuntimeError("engine said\nlore-adm: everything is fine"); run("CELL-3 newline", f)
```

### §A.5 probe_fork2.py
```python
"""FORK-2 served-path probe (coldaudit-63c-i-a-5): drive the REAL composed ASGI app (build_mcp_server +
build_asgi_app, LAN_BEARER posture, the SDK auth stack real, heavy lifespan stubbed exactly as the auth
fixtures do) with a well-formed `<name>:<secret>` bearer, and substitute ONLY the PrincipalKeyStore's
`_query` answer to the hash lookup. Cells: CONTROL-empty ([] -> no-such-key deny), CONTROL-rejected (the
pre-existing SurrealStoreError class), and the FORK-2 wrong shapes (a str, a non-dict member, a dict).
Prints status, body, and whether any engine/credential/internal token leaks. No store is contacted:
_query is replaced, and principal_store lookups are trapped to raise. Run from the tree root."""
import asyncio, os, sys, uuid, pathlib, logging
sys.path.insert(0, "loremaster/tests")
from urllib.parse import urlparse
import httpx
from _auth_fixtures import (base_config_payload, lan_bearer_auth_block, running_asgi_app, stub_heavy_startup,
    API_KEY_ENV_LOCAL_AGENT, API_KEY_ENV_LAN_CLIENT, API_KEY_VALUE_LOCAL_AGENT, API_KEY_VALUE_LAN_CLIENT,
    LOOPBACK_HOST, SERVER_PORT, MCP_PATH)
from loremaster.config import LoreConfig
from loremaster.server import LoreServer, build_asgi_app, build_mcp_server
from loremaster.store.surreal import SurrealStoreError

os.environ.setdefault("SURREAL_USER", "probe-unused"); os.environ.setdefault("SURREAL_PASS", "probe-unused"); os.environ.setdefault("SURREAL_PASSWORD", "probe-unused")
os.environ[API_KEY_ENV_LOCAL_AGENT] = API_KEY_VALUE_LOCAL_AGENT
os.environ[API_KEY_ENV_LAN_CLIENT] = API_KEY_VALUE_LAN_CLIENT
SECRET = "s3cr3t-PROBE-" + uuid.uuid4().hex
BEARER = f"probe-key:{SECRET}"
LEAK_TOKENS = ["Traceback", "SurrealStoreError", "principal-key query", "row list", "answered a", SECRET,
               "sha512", "ws://", "18000", "18500", "engine", "password"]

async def cell(name, answer):
    tmp = pathlib.Path(os.environ.get("TMPDIR", "/tmp")) / f"fork2-{uuid.uuid4().hex}"
    tmp.mkdir(parents=True)
    payload = base_config_payload(f"test_{uuid.uuid4().hex}", tmp)
    payload["auth"] = lan_bearer_auth_block()
    payload["surreal"] = {"url": "ws://127.0.0.1:18000/rpc", "namespace": "lore_test",
                          "database": f"never_{uuid.uuid4().hex}"}
    config = LoreConfig.model_validate(payload)
    assert urlparse(config.surreal.url).port == 18000, "REFUSED: not the TEST store"
    mcp = build_mcp_server(LoreServer(config))
    stub_heavy_startup(mcp)
    verifier = mcp.auth
    pks = verifier._principal_key_store
    calls = []
    async def fake_query(statement, params=None):
        calls.append(statement.split()[0])
        if isinstance(answer, BaseException):
            raise answer
        return answer
    pks._query = fake_query
    async def trap(*a, **k):
        raise AssertionError("principal store contacted")
    pks._principals.get_by_email = trap
    verifier._principal_store.get_by_email = trap
    app = build_asgi_app(mcp, config)
    origin = f"http://{LOOPBACK_HOST}:{SERVER_PORT}"
    async with running_asgi_app(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
                                     base_url=origin) as client:
            r = await client.post(MCP_PATH, headers={"Authorization": f"Bearer {BEARER}",
                "Accept": "application/json, text/event-stream", "Content-Type": "application/json"},
                json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18",
                      "capabilities": {}, "clientInfo": {"name": "probe", "version": "0"}}})
    body = r.text
    leaks = [t for t in LEAK_TOKENS if t in body or t in str(dict(r.headers))]
    print(f"{name:22s} status={r.status_code} query_calls={calls} leaks={leaks} "
          f"www-auth={r.headers.get('www-authenticate')!r} body={body[:160]!r}")

async def main():
    await cell("CONTROL-empty", [])
    await cell("CONTROL-rejected", SurrealStoreError("SurrealDB principal key lookup rejected (probe)"))
    await cell("FORK2-str", "garbage")
    await cell("FORK2-nondict-member", ["x"])
    await cell("FORK2-dict", {"name": "probe-key"})

asyncio.run(main())
```

### §A.6 probe_ref19.py
```python
"""Independent re-probe of docs/reference/surrealdb-31-capabilities.md §1.9 (coldaudit-63c-i-a-5).
TEST store ws://127.0.0.1:18000 ONLY (asserted). Mints its own DB in ns lore_test, defines its OWN SCHEMAFULL
table `t19` (fields a, b) — independent of the production DDL the builder used — and measures:
  V   the engine version (the reference says "3.2.4 per MEMORY.md, not re-measured")
  F1  INFO FOR TABLE <undefined> -> empty maps, no error; plus the identity claim: a DEFINED table with no
      fields (SCHEMALESS `t19e`) answers identically
  F2  after REMOVE FIELD b ON TABLE t19: UPDATE t19 SET b = 1 WHERE ... over 0 rows -> silent; over 1 row -> raises
Controls: INFO FOR TABLE t19 lists b before REMOVE; the same UPDATE over 1 row BEFORE the REMOVE succeeds.
Reaps with REMOVE DATABASE and proves absence via INFO FOR NS."""
import asyncio, sys, uuid
from urllib.parse import urlparse
sys.path.insert(0, "loremaster/tests")
from _surreal_harness import surreal_url, surreal_user, surreal_password, TEST_NAMESPACE
from surrealdb import AsyncSurreal
URL = surreal_url()
assert urlparse(URL).port == 18000, f"REFUSED: {URL} is not the TEST store"
DB = f"test_audit5_ref19_{uuid.uuid4().hex}"
async def q(db, s):
    try:
        r = await db.query(s)
        print(f"  {s}\n    => {r!r}")
        return r
    except Exception as e:
        print(f"  {s}\n    => RAISED {type(e).__name__}: {e}")
        return e
async def main():
    db = AsyncSurreal(URL); await db.connect()
    await db.signin({"username": surreal_user(), "password": surreal_password().get_secret_value()})
    await db.use(TEST_NAMESPACE, DB)
    print(f"store={URL} ns={TEST_NAMESPACE} db={DB}")
    try:
        print("V:", await db.version())
        await q(db, "DEFINE TABLE t19 SCHEMAFULL; DEFINE FIELD a ON TABLE t19 TYPE int; DEFINE FIELD b ON TABLE t19 TYPE option<int>;")
        await q(db, "DEFINE TABLE t19e SCHEMALESS;")
        print("F1 undefined vs defined-no-fields:")
        u = await q(db, "INFO FOR TABLE nosuch19")
        e = await q(db, "INFO FOR TABLE t19e")
        print(f"  identical={u == e}")
        print("control: fields before REMOVE"); await q(db, "INFO FOR TABLE t19")
        await q(db, "CREATE t19:ctl SET a = 1")
        print("control: UPDATE over 1 row on the healthy table"); await q(db, "UPDATE t19 SET b = 7 WHERE a = 1")
        await q(db, "DELETE t19")
        print("F2:"); await q(db, "REMOVE FIELD b ON TABLE t19"); await q(db, "INFO FOR TABLE t19")
        print("  over 0 rows:"); await q(db, "UPDATE t19 SET b = 7 WHERE a = 1")
        await q(db, "CREATE t19:one SET a = 1")
        print("  over 1 row:"); await q(db, "UPDATE t19 SET b = 7 WHERE a = 1")
    finally:
        await db.query(f"REMOVE DATABASE {DB}")
        ns = await db.query("INFO FOR NS")
        print(f"REAPED: {DB} present in INFO FOR NS databases = {DB in ns.get('databases', {})}")
        await db.close()
asyncio.run(main())
```

### §A.7 adm5.py
```python
"""Drive lore-adm's REAL entry (`principals.main`) against the restored dump DB (coldaudit-63c-i-a-5; the
audit-4 §A.2 method, needed because of #525). The ONLY substitution: `principals.load_surreal_only_config` is
replaced by a loader that validates the repo lore.yaml normally and then `model_copy`s the surreal block to the
dump coordinate (SurrealConfig.database's pattern refuses the name restore_prod_dump.py mints — #525). The port
is asserted 18000 before every call. NO log handler is attached here: whatever reaches stderr is lore-adm's own
(§13 A i). Usage (from the tree root): adm5.py <verb> [args...]; DUMP_DB env = the minted database name."""
import os, sys, contextlib, io
sys.path.insert(0, "loremaster/tests")
from urllib.parse import urlparse
from _surreal_harness import surreal_user, surreal_password
from loremaster import principals, config as config_module
DUMP_DB = os.environ["DUMP_DB"]
os.environ["AUDIT5_SURREAL_USER"] = surreal_user()
os.environ["AUDIT5_SURREAL_PASS"] = surreal_password().get_secret_value()
def dump_loader(path):
    base = config_module.load_surreal_only_config(path)
    surreal = base.surreal.model_copy(update={"url": "ws://127.0.0.1:18000/rpc", "namespace": "lore_test",
        "database": DUMP_DB, "user_env": "AUDIT5_SURREAL_USER", "password_env": "AUDIT5_SURREAL_PASS"})
    cfg = base.model_copy(update={"surreal": surreal})
    assert urlparse(cfg.surreal.url).port == 18000, "REFUSED: not the TEST store"
    assert cfg.surreal.database == DUMP_DB and cfg.surreal.namespace == "lore_test"
    return cfg
principals.load_surreal_only_config = dump_loader
argv = ["--config", "lore.yaml", *sys.argv[1:]]
out, err = io.StringIO(), io.StringIO()
print(f"$ lore-adm {' '.join(sys.argv[1:])}")
with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
    try:
        rc = principals.main(argv)
    except SystemExit as e:
        rc = f"SystemExit({e.code})"
    except BaseException as e:
        import traceback; traceback.print_exc(); rc = f"TRACEBACK {type(e).__name__}"
for line in out.getvalue().splitlines(): print(f"  stdout| {line}")
for line in err.getvalue().splitlines(): print(f"  stderr| {line}")
print(f"  exit={rc}")
```

### §A.8 dq5.py
```python
"""Direct-query probe on the restored dump (TEST store :18000 ONLY; port asserted). DUMP_DB env = database.
Usage: dq5.py '<surql>' ...   Prints each statement and its raw answer (or the raised error)."""
import asyncio, os, sys
from urllib.parse import urlparse
sys.path.insert(0, "loremaster/tests")
from _surreal_harness import surreal_url, surreal_user, surreal_password
from surrealdb import AsyncSurreal
URL = surreal_url(); DB = os.environ["DUMP_DB"]
assert urlparse(URL).port == 18000, f"REFUSED: port {urlparse(URL).port} is not the TEST store"
async def main():
    db = AsyncSurreal(URL); await db.connect()
    await db.signin({"username": surreal_user(), "password": surreal_password().get_secret_value()})
    await db.use("lore_test", DB)
    for q in sys.argv[1:]:
        try: r = await db.query(q)
        except Exception as e: r = f"ERR {type(e).__name__}: {e}"
        print(f"{q}\n  => {r}")
    await db.close()
asyncio.run(main())
```

### §A.9 ddl5.py
```python
"""Simulate the "new image boots" step on the restored dump (coldaudit-63c-i-a-5; audit-4 §7.4/§A.4 method):
apply exactly the server's DDL generators — generate_ddl(dim=2048), generate_agent_ddl, generate_message_ddl,
generate_brief_ddl, generate_audit_ddl, generate_task_ddl, generate_finding_ddl — via query_raw, and count every
per-statement status != OK. TEST store :18000 only (asserted); DUMP_DB env = database. Run from the tree root."""
import asyncio, os, sys
from urllib.parse import urlparse
sys.path.insert(0, "loremaster/tests")
from _surreal_harness import surreal_url, surreal_user, surreal_password
from surrealdb import AsyncSurreal
from loremaster.store import surreal_schema as s
URL = surreal_url(); DB = os.environ["DUMP_DB"]
assert urlparse(URL).port == 18000, "REFUSED: not the TEST store"
GENS = [("generate_ddl(dim=2048)", lambda: s.generate_ddl(dim=2048)), ("generate_agent_ddl", s.generate_agent_ddl),
        ("generate_message_ddl", s.generate_message_ddl), ("generate_brief_ddl", s.generate_brief_ddl),
        ("generate_audit_ddl", s.generate_audit_ddl), ("generate_task_ddl", s.generate_task_ddl),
        ("generate_finding_ddl", s.generate_finding_ddl)]
async def main():
    db = AsyncSurreal(URL); await db.connect()
    await db.signin({"username": surreal_user(), "password": surreal_password().get_secret_value()})
    await db.use("lore_test", DB)
    for name, gen in GENS:
        raw = await db.query_raw(gen())
        results = raw.get("result", [])
        bad = [r for r in results if r.get("status") != "OK"]
        print(f"{name}: {len(results)} statements, {len(bad)} not-OK" + (f" first={bad[0]}" if bad else ""))
    await db.close()
asyncio.run(main())
```

### §A.10 gated_run.sh
```bash
#!/usr/bin/env bash
# Memory-gated, cgroup-capped pytest runner (coldaudit-63c-i-a-5). Usage: gated_run.sh <tree> <logfile> <pytest args...>
# Waits until NO other pytest process is live AND MemAvailable >= 20 GiB (never bypassed), logs the wait, then runs
# under systemd-run MemoryMax=16G MemorySwapMax=0 with -n 8 --timeout=300 (pytest-timeout).
set -u
tree=$1; log=$2; shift 2
start=$(date +%s)
while :; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
  others=$(ps -eo pid,args | awk '/[p]ytest/ && !/gated_run/ && !/awk/' | wc -l)
  if [ "$avail" -ge 20 ] && [ "$others" -eq 0 ]; then break; fi
  sleep 20
done
echo "ADMITTED $(date -u +%H:%M:%SZ) avail=${avail}GiB others=$others waited=$(( $(date +%s) - start ))s" > "$log"
cd "$tree" || exit 3
echo "tree-md5 $(git diff --binary HEAD | md5sum | cut -c1-8) (tracked only)" >> "$log"
systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --no-sync --with pytest-timeout \
  pytest -n 8 --timeout=300 -q -p no:cacheprovider "$@" >> "$log" 2>&1
echo "EXIT $? $(date -u +%H:%M:%SZ)" >> "$log"
```

### §A.11 own5.py
```python
"""Red ownership for a junit run (coldaudit-63c-i-a-5), using the gate's OWN reader + registry + partition
(scripts/pending_contract_gate.py: JUnitReportReader, PendingContractRegistry.load, PendingContractGate.
partition_pytest, entries_for). Prints totals, per-file red counts with owner bound names, and ORPHANs.
Usage (from the tree root): own5.py <junit.xml>"""
import collections, pathlib, sys
sys.path.insert(0, "scripts")
import pending_contract_gate as g
import xml.etree.ElementTree as ET
tree = ET.parse(sys.argv[1])
for case in tree.iter("testcase"):  # xunit2 drops `file`: derive it from classname (module path up to test_*.py)
    if "file" not in case.attrib:
        parts = case.get("classname", "").split(".")
        mod = [p for p in parts if p.startswith("test_")][0]
        case.set("file", "/".join(parts[: parts.index(mod) + 1]) + ".py")
run = g.JUnitReportReader.read(ET.tostring(tree.getroot(), encoding="unicode"))
reg = g.PendingContractRegistry.load(pathlib.Path("scripts/pending_contracts.yaml"))
part = g.PendingContractGate(reg, pathlib.Path(".")).partition_pytest(run)
print(f"total={run.total} passed={run.passed} red={len(run.outcomes)} owned={len(part.expected)} ORPHAN={len(part.unexpected)}")
per = collections.Counter(o.file for o in run.outcomes)
owners = collections.Counter()
for f, n in sorted(per.items()):
    names = sorted({b.id for b, _ in reg.entries_for(f)})
    owners[" + ".join(names) or "ORPHAN"] += n
    print(f"  {n:4d}  {f}  -> {names or 'ORPHAN'}")
print("by owner:", dict(owners))
for o in part.unexpected: print("ORPHAN:", o.test_id)
```

### §A.12a mp5.sh
```bash
#!/usr/bin/env bash
# Mutation proof wrapper (coldaudit-63c-i-a-5): cp -a backup of the target FIRST, process-table + MemAvailable>=20GiB
# gate (waits logged, never bypassed), then scripts/mutation_proof.py (declared reds, diffed BOTH ways) under a
# MemoryMax=16G cgroup with -n 8 --timeout=300; afterwards `cmp` the target against the cp -a backup.
# Usage: mp5.sh <tree> <key> <target-file> <test files...>   (reads mutdefs/<key>.{anchor,repl,decl})
set -u
tree=$1; key=$2; target=$3; shift 3
SP=$(dirname "$0")/..; M=$SP/mutdefs; log=$SP/mut_$key.log
cd "$tree" || exit 3
mkdir -p "$SP/mutbak_$key"; cp -a "$target" "$SP/mutbak_$key/"
start=$(date +%s)
while :; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
  others=$(ps -eo pid,args | awk '/[p]ytest/ && !/mp5\.sh/ && !/mutation_proof/ && !/awk/' | wc -l)
  [ "$avail" -ge 20 ] && [ "$others" -eq 0 ] && break; sleep 20
done
echo "ADMITTED $(date -u +%H:%M:%SZ) avail=${avail}GiB others=$others waited=$(( $(date +%s) - start ))s loremaster=$(uv run --no-sync python -c 'import loremaster;print(loremaster.__file__)')" > "$log"
args=(); while read -r id; do [ -n "$id" ] && args+=(--expect-red "$id"); done < "$M/$key.decl"
systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 uv run --no-sync python scripts/mutation_proof.py \
  --file "$target" --anchor-file "$M/$key.anchor" --replacement-file "$M/$key.repl" "${args[@]}" -- \
  uv run --no-sync --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider "$@" >> "$log" 2>&1
echo "mutation_proof exit=$?" >> "$log"
cmp "$target" "$SP/mutbak_$key/$(basename "$target")" && echo "CMP: restored byte-exact vs cp -a backup" >> "$log" || echo "CMP: DIFFERS — TREE DIRTY" >> "$log"
```

### §A.12b mutchain.sh
```bash
#!/usr/bin/env bash
# Sequential mutation chain (coldaudit-63c-i-a-5). Waits for the targeted run to finish, confirms every declared id
# EXISTS via --collect-only (collection names tests without running them: the set is fixed before any result), then
# runs A..E through mp5.sh.
SP=$(cd "$(dirname "$0")/.." && pwd); T=$SP/mut5
until awk '/^EXIT/{f=1} END{exit !f}' $SP/run_targeted.log 2>/dev/null; do sleep 15; done
until [ "$(ps -eo args | awk '/[p]ytest/ && !/awk/' | wc -l)" -eq 0 ]; do sleep 15; done
cd $T && uv run --no-sync pytest --collect-only -q -p no:cacheprovider loremaster/tests/test_principals_cli.py loremaster/tests/test_fail_closed_shapes_63c_13b.py loremaster/tests/test_preboot_schema_precondition_63c_13d.py > $SP/collect.txt 2>&1
for k in A B C D E; do while read -r id; do awk -v id="$id" '$0==id{f=1} END{exit !f}' $SP/collect.txt && echo "OK $k $id" || echo "MISSING $k $id"; done < $SP/mutdefs/$k.decl; done > $SP/collect_check.txt
$SP/inst/mp5.sh $T A loremaster/loremaster/principals.py loremaster/tests/test_principals_cli.py
$SP/inst/mp5.sh $T B loremaster/loremaster/governed.py loremaster/tests/test_fail_closed_shapes_63c_13b.py
$SP/inst/mp5.sh $T C loremaster/loremaster/principals.py loremaster/tests/test_principals_cli.py
$SP/inst/mp5.sh $T D loremaster/loremaster/principals.py loremaster/tests/test_preboot_schema_precondition_63c_13d.py
$SP/inst/mp5.sh $T E loremaster/loremaster/principals.py loremaster/tests/test_preboot_schema_precondition_63c_13d.py
echo "CHAIN DONE $(date -u +%H:%M:%SZ)" > $SP/mutchain.done
```

### §A.13 mutation definitions (anchor → replacement, and the declared reds; md5 of each .decl: A feb29931 · B 71f17d43 · C 61e3e413 · D 54af3402 · E ed4742f5)

**A** — anchor:
```
    with _cli_logging():
        return asyncio.run(_dispatch(args))

```
replacement:
```
    if True:  # MUTATION A: handler never installed
        return asyncio.run(_dispatch(args))

```
declared reds:
```
loremaster/tests/test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_server_log_pointer_resolves_to_stderr[add]
loremaster/tests/test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_server_log_pointer_resolves_to_stderr[add-household]
loremaster/tests/test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_server_log_pointer_resolves_to_stderr[create-keep]
loremaster/tests/test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_server_log_pointer_resolves_to_stderr[delete]
loremaster/tests/test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_server_log_pointer_resolves_to_stderr[delete-keep]
loremaster/tests/test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_server_log_pointer_resolves_to_stderr[list]
loremaster/tests/test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_server_log_pointer_resolves_to_stderr[list-keys]
loremaster/tests/test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_server_log_pointer_resolves_to_stderr[migrate-governed]
loremaster/tests/test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_server_log_pointer_resolves_to_stderr[mint-key]
loremaster/tests/test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_server_log_pointer_resolves_to_stderr[remove-household]
loremaster/tests/test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_server_log_pointer_resolves_to_stderr[report-unmigrated]
loremaster/tests/test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_server_log_pointer_resolves_to_stderr[revoke-key]
loremaster/tests/test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_server_log_pointer_resolves_to_stderr[set-expiry]
loremaster/tests/test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_server_log_pointer_resolves_to_stderr[set-keeper]
loremaster/tests/test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_server_log_pointer_resolves_to_stderr[set-rank]
loremaster/tests/test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_server_log_pointer_resolves_to_stderr[suspend]
loremaster/tests/test_principals_cli.py::TestTheLoreAdmFaultLineTeachesItsCause::test_the_server_log_pointer_resolves_to_stderr[unsuspend]
```

**B** — anchor:
```
    if not isinstance(result, dict):
        raise SurrealStoreError(
            f"the {noun} read answered a {type(result).__name__}, not an INFO map
```
replacement:
```
    if not isinstance(result, dict):
        return {"tables": {}, "fields": {}}  # MUTATION B: tolerant
    if False:
        raise SurrealStoreError(
            f"the {noun} read answered a {type(result).__name__}, not an INFO map
```
declared reds:
```
loremaster/tests/test_fail_closed_shapes_63c_13b.py::TestMapOfContract63c13_1::test_a_non_dict_info_answer_raises_the_store_class[None]
loremaster/tests/test_fail_closed_shapes_63c_13b.py::TestDeleteNeverSkipsTheOwnedRowGuardOnAGarbageInfoAnswer63c13_1::test_a_malformed_info_for_db_answer_raises_and_deletes_nothing[None]
loremaster/tests/test_fail_closed_shapes_63c_13b.py::TestMapOfContract63c13_1::test_a_non_dict_info_answer_raises_the_store_class[int]
loremaster/tests/test_fail_closed_shapes_63c_13b.py::TestDeleteNeverSkipsTheOwnedRowGuardOnAGarbageInfoAnswer63c13_1::test_a_malformed_info_for_db_answer_raises_and_deletes_nothing[int]
loremaster/tests/test_fail_closed_shapes_63c_13b.py::TestMapOfContract63c13_1::test_a_non_dict_info_answer_raises_the_store_class[list]
loremaster/tests/test_fail_closed_shapes_63c_13b.py::TestDeleteNeverSkipsTheOwnedRowGuardOnAGarbageInfoAnswer63c13_1::test_a_malformed_info_for_db_answer_raises_and_deletes_nothing[list]
loremaster/tests/test_fail_closed_shapes_63c_13b.py::TestMapOfContract63c13_1::test_a_non_dict_info_answer_raises_the_store_class[str]
loremaster/tests/test_fail_closed_shapes_63c_13b.py::TestDeleteNeverSkipsTheOwnedRowGuardOnAGarbageInfoAnswer63c13_1::test_a_malformed_info_for_db_answer_raises_and_deletes_nothing[str]
```

**C** — anchor:
```
    if not _is_governed_table(args.table):
        print(
            f"{_CLI_PROG}: report-unmigrated does not support
```
replacement:
```
    if False:  # MUTATION C: validator bypassed
        print(
            f"{_CLI_PROG}: report-unmigrated does not support
```
declared reds:
```
loremaster/tests/test_principals_cli.py::TestHonestLabels::test_an_invalid_table_is_refused_before_any_store_call[report-unmigrated]
```

**D** — anchor:
```
    if not missing:
        return None

```
replacement:
```
    if True:  # MUTATION D: gate never fires
        return None

```
declared reds:
```
loremaster/tests/test_preboot_schema_precondition_63c_13d.py::TestADirtyStoreRefusesWithTheTeachingBeforeAnyWrite::test_one_removed_column_is_refused_and_named_with_zero_writes[agent-owner_principal]
loremaster/tests/test_preboot_schema_precondition_63c_13d.py::TestADirtyStoreRefusesWithTheTeachingBeforeAnyWrite::test_one_removed_column_is_refused_and_named_with_zero_writes[agent-owner_agent]
loremaster/tests/test_preboot_schema_precondition_63c_13d.py::TestADirtyStoreRefusesWithTheTeachingBeforeAnyWrite::test_one_removed_column_is_refused_and_named_with_zero_writes[agent-scope]
loremaster/tests/test_preboot_schema_precondition_63c_13d.py::TestADirtyStoreRefusesWithTheTeachingBeforeAnyWrite::test_one_removed_column_is_refused_and_named_with_zero_writes[memory-scope]
loremaster/tests/test_preboot_schema_precondition_63c_13d.py::TestADirtyStoreRefusesWithTheTeachingBeforeAnyWrite::test_one_removed_column_is_refused_and_named_with_zero_writes[message-owner_agent]
loremaster/tests/test_preboot_schema_precondition_63c_13d.py::TestADirtyStoreRefusesWithTheTeachingBeforeAnyWrite::test_one_removed_column_is_refused_and_named_with_zero_writes[message-owner_principal]
loremaster/tests/test_preboot_schema_precondition_63c_13d.py::TestADirtyStoreRefusesWithTheTeachingBeforeAnyWrite::test_one_removed_column_is_refused_and_named_with_zero_writes[message-scope]
loremaster/tests/test_preboot_schema_precondition_63c_13d.py::TestTheRequiredColumnSetIsTheLegsOwnSetClause::test_the_refused_column_set_equals_the_set_clause[agent]
loremaster/tests/test_preboot_schema_precondition_63c_13d.py::TestTheRequiredColumnSetIsTheLegsOwnSetClause::test_the_refused_column_set_equals_the_set_clause[memory]
loremaster/tests/test_preboot_schema_precondition_63c_13d.py::TestTheRequiredColumnSetIsTheLegsOwnSetClause::test_the_refused_column_set_equals_the_set_clause[message]
```

**E** — anchor:
```
    missing = [column for column in _set_columns(statement) if column not in defined_fields]

```
replacement:
```
    missing = [column for column in _set_columns(statement) if column not in defined_fields and not (table == "agent" and column == "owner_agent")]  # MUTATION E

```
declared reds:
```
loremaster/tests/test_preboot_schema_precondition_63c_13d.py::TestADirtyStoreRefusesWithTheTeachingBeforeAnyWrite::test_one_removed_column_is_refused_and_named_with_zero_writes[agent-owner_agent]
loremaster/tests/test_preboot_schema_precondition_63c_13d.py::TestTheRequiredColumnSetIsTheLegsOwnSetClause::test_the_refused_column_set_equals_the_set_clause[agent]
```

### §A.14 declared targeted set `declared5.txt` (md5 12efd3c1, 70 files, under `loremaster/tests/`)
```
test_425_stamp_owner_63a.py test_agent_capability.py test_agent_capability_seams.py test_agent_governance_63c_i_a.py test_agent_owns_principal_schema.py test_audit_store.py test_comms_footer.py test_comms_read_governance_63b_ii_b.py test_comms_render_architecture.py test_comms_schema.py test_comms_send_scope_63b_ii_a.py test_comms_tool.py test_engine_rejection_seam.py test_exhaustion_fates.py test_fail_closed_shapes_63c_13b.py test_findings_classes_64b.py test_findings_closeout_64b.py test_findings_enforcement_64b.py test_findings_governance_64b.py test_findings_migrate_64b.py test_findings_system_writer_64b.py test_fixwave_a19_63c_i_a.py test_fixwave_a19a_63c_i_a.py test_fixwave_a19b_63c_i_a.py test_fixwave_a28_63c_i_a.py test_fixwave_a28b_63c_i_a.py test_fixwave_a28c_63c_i_a.py test_governed_migration_63a.py test_governed_routing_63a.py test_governed_substrate_63a.py test_governed_substrate_64b.py test_keep_remediation_cli_61.py test_keep_remediation_store_61.py test_keeps_cli.py test_keeps_store.py test_link5_render_containment.py test_mcp_server.py test_memory_enforcement_63a_v.py test_memory_enforcement_63b_ia.py test_memory_f5_registration_63b_ib.py test_memory_render_bound_63b_ib.py test_memory_replay_fidelity_63b_ib.py test_memory_retrofit_63a.py test_memory_supersede_atomicity_63b_ib.py test_message_enforcement_63b_ii_a.py test_message_migrate_63b_ii_a.py test_message_migrate_dirty_store_63b_ii_b.py test_migration_wire.py test_preboot_schema_precondition_63c_13d.py test_principal_delete_cascade_61.py test_principal_delete_governed_63a.py test_principal_keys_schema.py test_principal_keys_store.py test_principals_cli.py test_principals_store.py test_reanchor_58_r3_am6.py test_reanchor_58_r3_cas_seam.py test_reanchor_58_r3_tiers.py test_reanchor_58_r4_lease_fates.py test_render_mypy_layer_optout.py test_render_mypy_layer.py test_render.py test_render_seam_pins.py test_render_slot_inventory.py test_retry_seam.py test_search.py test_secret_typing.py test_token_verifier.py test_visible_keeps_61b.py test_wire_isolation_63a.py 
```

## §R Residual table (dated 2026-09-30, graded patch `bec29190` on HEAD `5746de5`)
| id | class (lifted property) | severity | owner (recommended) | re-open / decision trigger |
|---|---|---|---|---|
| **#527** (NEW, introduced by this patch) | every exception-chain walker terminates on any chain — `_fault_line` hangs on a cyclic `__cause__` | MINOR (operator CLI spins; no data effect; low honest-developer reachability) | 63c-i-a — one-line `seen` guard + one pinned cell, if the lead folds it now; else the next lore-adm-touching contract | the lead's commit decision; or a lore-adm hang observed in the field |
| **#528** (NEW, spec-originated) | a docstring's caller-set claim equals the derived caller set — `report_unmigrated_governed_rows` "ONLY caller" is false (`scripts/restore_prod_dump.py`) | MINOR (prose; the unvalidated caller passes schema-derived names) | 63c-i-a (reword) or packet 64 (the restore script's owner) | the lead's commit decision; the next edit to either caller |
| §7 #25 | a failure after a committed write names the write (F-5's property) — `_rows_stamped`'s wrong-shape message after the backfill UPDATE says "… read … nothing was decided from it", naming no landed write (×3 legs) | MINOR (idempotent re-run bounds the harm) | 63c-i-a or the next migrate-touching contract | a wrong-shaped UPDATE answer observed on 3.2.x |
| §7 #19 / #21 / #31 | prose NITs: agent-leg "(below)" points the wrong way; message-leg inline comment still says the read measures sender-skipped rows only (F-4 sibling); `_not_supported` still hand-lists the tables | NIT | whoever next edits `principals.py`'s migrate legs | next edit |
| §6(iii) | §13.2's prediction "expected: agent-first order first" on a pre-boot `--table message` did not hold — the schema teaching arrives first (agent-first lives in `_message_leg_refusal`, after the gate) | receipt, not a defect (both teachings true; the observed order is the stronger one) | sidecar-63c-2 (am-37 §13.2 prose) | if §13.2's reasoning is ever cited as a design basis |
| FLAG-4 (confirmed) | a cause/engine message with a newline forges a `lore-adm:` line on the operator's stderr | residual (operator terminal, not a served MCP surface) | as the lead routed | a served surface ever reuses `_fault_line` |
| FLAG-2 (confirmed) | `--currency --legs typecheck,ruff` renders `pytest NOT_RUN … CURRENCY: FAIL` for a deliberately excluded leg | tool UX residual | the gate owner | as the lead routed |
| inherited | R-1/F-8, F-9, F-11, F-12, F-16, §W row 4, the GROUP ALL sweep → 64b, D-4 (brief alarm teaches a refusing verb — re-observed §6(v)), #525 (dump name vs config — the loader swap was needed again) | unchanged | per am-37 §13 "Residuals confirmed" | per am-37 §13 |

## §W Memory-gate wait log (excluded from the deadline per the brief)
- Mutation chain (§3) armed 18:13Z; the targeted run released the process table at 18:17:47Z; from then the chain's
  mp5.sh gate (no other pytest AND MemAvailable ≥ 20 GiB) was never satisfied through 19:22Z: MemAvailable 13.2–17.5 GiB
  (top RSS: other sessions' postgres workers ~2 GiB each ×6, prod `surreal` 5.4 GiB), and from ~18:37Z a FOREIGN pytest
  (`mobile-pricepaper-smoke` session, `uv run pytest -q`, pid 309754) was alive until before 20:02Z. Bounded wait ended
  20:02:21Z with MemAvailable 17.1 GiB — gate still closed. Not bypassed, not lowered. Total gate wait ≈ 104 min.
