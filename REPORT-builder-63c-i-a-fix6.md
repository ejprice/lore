brief-base v18 read · brief project v7 read

# REPORT — builder-63c-i-a-fix6 (packet 63c-i-a, am-37 §13 A–D + §13.1 production fold)

## SUMMARY (2026-09-30, scratch base `365f769` + full4 `7ab76f36`; production NOT committed)
- **State:** done-with-deviations. am-37 §13 A–D and §13.1 are built in production plus the store reference. No test file was edited.
  - Declared set: 62 files, 5031 nodes on the build.
  - **0 GREEN→RED.**
  - **The declared 209 are all accounted for:** 200 RED→GREEN, 8 derived-param churn that passes, and 1 packet-58-owned row, as in the reference.
  - 269 build reds remain: 268 are owned (58 / 64b-i) and **1 is UNOWNED and red at base: `test_retry_seam.py::…test_am34_5…`** (FLAG-1). It is caused by round 4's D test file, not by this build.
  - ruff clean; typecheck RED_ADJUDICATED 83 (unchanged).
- **Deviations:**
  - (1) FORK-1: the §13 D schema gate is the leg's FIRST action, not in `migrate_governed`. §1.9 item 1 keeps the statement in the leg.
  - (2) FORK-2: `PrincipalKeyStore._as_rows` is routed too, so `verify` raises on a wrong-shaped lookup.
  - (3) `_rows_stamped` gained a DEFAULT `noun` to clear an orphan typecheck red on the test's own arity probe.
  - (4) The currency `--legs typecheck,ruff` exits 1 with "pytest NOT_RUN" (FLAG-2).
- **Packages considered:**
  - `_set_columns`: `surrealdb` 2.0.0 was read (module list; `sql_adapter` only joins strings), with no parser → bespoke.
  - CLI logging: stdlib `logging.StreamHandler` / `Formatter` → replace (subclassed).
  - Cause chain: stdlib `__cause__`; no package needed.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 11 new symbols, all dispositioned (§9). `rows_of` / `map_of` are the ruled ONE homes. The foreign tolerant `_as_rows` clones (agents, briefs, diff, findings, messages, tasks) are FLAGGED for 64b's §DRY step.
- **Graded:** n/a (builder).
- **Decisions needed:**
  - FORK-1: accept leg-first placement?
  - FORK-2: accept the `verify` raise?
  - FLAG-1: the test-side fix owner for the am34_5 resolver pin.
  - FLAG-3: `governed.py` module docstring still says STUB — fix now or route?
- **Pointers:** §1 per-class · §2 DUAL · §3 forks/flags · §4 store probe · §5 transitions · §6 currency · §7 secret guard · §8 sweep · §9 DRY · §10 backups/md5s.

## CAPABILITY CHECK
- `lore_comms` register: OK (`builder-63c-i-a-fix6`, session `63c-20260924`, cadence `≤20m`).
- grep/rg are hook-blocked (#473). Every textual sweep below uses **awk**, as the brief requires.
- `lore_impact` caps covering tests at 15 (#518). The covering-test derivation is an **AST scan**, pasted in §5.
- Worked in scratch `…/9744862d…/scratchpad/fix6`, made by `scripts/scratch_copy.sh`, on HEAD `365f769` + full4 (md5 `7ab76f3611bedf69eddc4df943cbbc67` verified; `git apply` clean).
  - `loremaster.__file__` = `…/scratchpad/fix6/loremaster/loremaster/__init__.py`, which is inside the scratch tree.

## 1. Per-class table (edit → clause → chokepoint → receipt)
All edits are in `loremaster/loremaster/{principals,governed,principal_keys}.py` and `docs/reference/surrealdb-31-capabilities.md`. No test file was edited. Symbols are cited, not line numbers. Receipts are the node ids in §5.

| class | edit | clause | chokepoint | receipt |
|---|---|---|---|---|
| A(i) | `main()` wraps `asyncio.run(_dispatch(...))` in `_cli_logging()`. That installs ONE `_CliStderrHandler` (WARNING, bound to the current `sys.stderr`) on the `loremaster` logger (`_CLI_LOGGER_NAME`), with `_CliLogFormatter` = `%(message)s` + `[error_class=…; engine_error=…]` when present (`_CLI_LOG_EXTRA_KEYS`; `url` is deliberately not rendered). Stale instances are removed on install and the handler is removed in `finally` → idempotent across calls. | §13 A (i) | `principals.main` | `TestTheLoreAdmFaultLineTeachesItsCause::test_the_server_log_pointer_resolves_to_stderr[*]`, `…::test_repeated_invocations_do_not_duplicate_the_log_line` |
| A(ii) | `_dispatch`'s ONE handler prints `_fault_line(error)`: `lore-adm: {error}`, then one `  ← caused by: {msg}` per `__cause__` link. Messages only, consecutive duplicates collapsed, an empty message rendered as its class name. | §13 A (ii) | `principals._dispatch` → `_fault_line` | `…::test_the_cause_of_every_laundered_fault_is_printed[verb × fault]` |
| A / F-13 | Three wrap contexts made neutral: `create` → `could not create principal {email!r}`; `set_subject` → `could not bind subject to principal {email!r}`; `principal_keys.mint` → `could not mint key {name!r} for principal {email!r}`. `set_subject`'s `Raises:` restated. | §13 A / F-13 | `wrap_store_rejection` call sites | `TestNoWrapContextOverClaimsItsCause::…` |
| B | NEW `governed.rows_of(result, *, noun)`: non-list → raise; any non-dict member → raise; else returned whole. | §13 B | `governed.rows_of` | `TestRowsOfContract63c13b::*` |
| B / §13.1-1 | NEW `governed.map_of(result, *, noun, required=())`: non-dict → raise; a present `tables`/`fields` sub-map that is not a dict → raise; a `required` key absent → raise. | §13.1 item 1 | `governed.map_of` | `TestMapOfContract63c13_1::*` |
| B / F-6 | `_rows_stamped(update_result, *, noun=_BACKFILL_UPDATE_NOUN)` = `len(rows_of(...))`. All three legs pass their own noun. | §13 B F-6 | `rows_of` | `TestRowsStampedFailsClosed63c13b::*` |
| B / F-7 | `_governed_select` = `rows_of(run_query(...), noun)`. | §13 B F-7 | `rows_of` | `TestGovernedSelectFailsClosed63c13b::*` |
| B / F-1 | `PrincipalStore.delete`'s `cascaded` = `group_all_count(..., noun="cascaded principal-key count")` (inside the §12 wrap). | §13 B F-1 | `group_all_count` | `TestPrincipalDeleteCascadedCount63c13b::*` |
| B | `PrincipalStore._as_rows` → `rows_of`. It is a staticmethod with `noun="principal-substrate query"`; `KeepStore` reads through it too. `PrincipalKeyStore._as_rows` → `rows_of` (Reading A, see §3 FORK-2). | §13 B | `rows_of` | `TestAsRowsNonListIsAStoreFaultNotNotFound63c13b::*` |
| B / §13.1-1 | `PrincipalStore._table_exists` = `map_of(INFO FOR DB, required=("tables",))`. This closes the FAIL-OPEN guard. | §13.1 item 1 | `map_of` | `TestDeleteNeverSkipsTheOwnedRowGuardOnAGarbageInfoAnswer63c13_1::*` |
| B / §13.1-1 | `_agent_migration_preconditions`: the cloned `isinstance(info, dict) or "tables" not in info` policy is DELETED; the read now goes through `map_of(..., required=("tables",))`. | §13.1 item 1 | `map_of` | allowlist walker `TestOneShapePolicyAllowlist63c13b::*`; a28 `test_A2_an_unexpected_INFO_FOR_DB_shape_raises_byte_inert[*]` |
| B / §13.1-2 | `governed.authorize_guarded`'s pre-read = `rows_of(pre_read, noun="governed pre-read")`. The `{}` coercion of a non-dict row is gone. | §13.1 item 2 | `rows_of` | `TestAuthorizeGuardedPreReadFailsClosed63c13_1::*` |
| B / F-5 | Message leg: `backfilled` is measured first, then the leftover read + `group_all_count` run under `wrap_store_rejection(PrincipalStoreError, f"the backfill landed ({backfilled} message row(s) stamped) but the leftover count read failed")`. | §13 B F-5 | `wrap_store_rejection` | `TestMessageLeftoverReadNamesTheLandedWrite63c13b::…F5…` |
| C / F-4 | `MigrateGovernedResult.unsound_sender_messages` → `messages_left_unmigrated` (field, docstring, receipt key, stderr sentence *"N message row(s) remain un-migrated after the backfill — commonly their sender has no owner or scope (re-run after `--table agent` for those); a row inserted during the run is counted here too"*), all six constructions, and the leg docstring. | §13 C F-4 | the field | `TestHonestLabels::test_the_result_field_is_named…`, `…retired_name_survives_in_no_served_source`, `…receipt_key_and_the_stderr_sentence…[0,3]` |
| C / N-3, F-15 | `_TABLE_HELP_DOMAIN` is derived from `_MIGRATE_VALID_TABLES` and used by BOTH verbs' `--table` help. ONE validator `_is_governed_table` is called by `migrate_governed`, by `_dispatch_migrate_governed` (before any store is built) and by `_dispatch_report_unmigrated` (before any store is built). `_render_migrate_refusal` is the one refusal render. | §13 C N-3/F-15 | `_is_governed_table` | `TestHonestLabels::test_the_table_help_is_derived…[*]`, `…invalid_table_is_refused_before_any_store_call[*]` |
| C / N-1 | `report_unmigrated_governed_rows` docstring: "STUB / runnable-RED" and "boot alarm" are gone; it states its ONLY caller is the verb and that the caller validates `table`. | §13 C N-1 | prose | — |
| C / N-2, F-10 | `Raises:` of `set_status`, `set_expires`, `delete` names `PrincipalStoreError`; `revoke` names `PrincipalKeyStoreError`. | §13 C N-2 | prose | `TestEveryWrappedBoundaryDocumentsItsWrapError::*` |
| C / F-2 | `group_all_count`'s "every GROUP ALL read" universal is scoped to the two modules; the foreign tolerant readers are named as routed to 64b. | §13 C F-2 | prose | — |
| C / F-14 | `_dispatch_keep`'s docstring states the policy the code has: write boundaries are the PINNED minimum; `delete` / `get_or_create_keyed` wrap reads too; `ensure_ready` is un-wrapped. | §13 C F-14 | prose | — |
| D | `AgentMigrationPreconditions.defined_fields: frozenset[str]`. ONE `INFO FOR TABLE <table>` read through `map_of(required=("fields",))`, immediately after the `INFO FOR DB` gate, only when `--table` is DEFINED. An undefined table still does exactly one `INFO FOR DB`. | §13 D | `_agent_migration_preconditions` | `TestThePreconditionFactRidesThePreconditionsModel::*` |
| D | NEW `_set_columns(statement)`: a depth-aware parse of the leg's own `UPDATE … SET` text. NEW `_schema_predates_refusal(table, statement, defined_fields)`: the teaching sentence, one backtick span PER column. Each leg builds its function-local `backfill_statement` FIRST and refuses (via `_refused`, `table_defined=True`) before ANY read or write. `MigratePreconditionCounts` is unchanged. | §13 D, §13.1 items 3 + 5 | `_schema_predates_refusal` | `TestADirtyStoreRefusesWithTheTeachingBeforeAnyWrite::*`, `TestAFullSchemaStoreProceeds::*`, `TestTheRequiredColumnSetIsTheLegsOwnSetClause::*` |
| §13.1-4 | `docs/reference/surrealdb-31-capabilities.md` gains §1.9, with the two facts probed live (§4). | §13.1 item 4 | reference | §4 probe |

## 2. DUAL: every replaced function, the old fate of a wrong-shaped answer vs the new one
Measured on base `365f769` + full4 (`7ab76f36`) against the build (2026-09-30).

| function | old fate (full4) | new fate (fix6) |
|---|---|---|
| `PrincipalStore._as_rows` | non-list → `[]`. So `set_status` / `set_subject` / `set_expires` served **`PrincipalNotFoundError`**, `get_by_*` served `None`, `list` served `[]`, and `delete`'s keep read served **"keeps nothing"**, letting the delete proceed (fail-OPEN). A non-dict member was **silently dropped**. The same applied to every `KeepStore` read, which borrows this staticmethod. | `rows_of` → `SurrealStoreError` naming the read. For a delete it is inside the §12 wrap → `PrincipalStoreError("could not delete …")`. The cascade never runs. `[]` still means NotFound (control pins). |
| `PrincipalKeyStore._as_rows` | non-list → `[]`. `revoke` served **`PrincipalKeyNotFoundError`**; `verify` served a **"no-such-key" deny**; `mint` served "vanished after create". Non-dict members were dropped. | `rows_of` → `SurrealStoreError`. `verify` now RAISES on a wrong-shaped lookup instead of denying (§3 FORK-2). |
| `PrincipalStore._table_exists` | non-dict INFO answer → `{}` → **`False`** ("memory absent"). A dict without `tables` → `False`. `delete` then **skipped the SF-63-5 owned-row guard** (fail-OPEN, B-D1). | `map_of(required=("tables",))` → `SurrealStoreError` → `PrincipalStoreError("could not delete …")`; no cascade. |
| `_agent_migration_preconditions` (INFO FOR DB) | its own clone: non-dict or no `tables` → `SurrealStoreError`. A NON-DICT `tables` value (list/str) passed, so `AGENT_TABLE in defined` did **list or substring membership**. | `map_of(required=("tables",))`: same raise for the old shapes, plus a non-dict `tables` raises. The message now names the type (a28 A2 pin). |
| `_governed_select` | non-list → raise; non-dict member → **silently dropped** (a precondition row vanished). | `rows_of`: both raise. |
| `_rows_stamped` | non-list → **`TypeError`** (not laundered by the CLI → traceback); a non-dict member was **counted as stamped**. | `rows_of` → `SurrealStoreError`, which the CLI launders. |
| `PrincipalStore.delete` `cascaded` | `int(count_rows[0].get("count", 0)) if count_rows else 0`: a missing key → **0**; `"3"` → **3**; `None` → **`TypeError`**; a non-list → `_as_rows` → **0**. The cascade then **ran**. | `group_all_count` → `SurrealStoreError` → wrapped `PrincipalStoreError`; the cascade never runs. |
| `governed.authorize_guarded` pre-read | non-list → `[]` → **"row absent"**: no PDP decision, `requires_audit=False`, and the plan was built. A non-dict row → `{}` → an ownerless `Resource` **decided by the PDP**. | `rows_of` → `SurrealStoreError` before any decision. |
| `_dispatch` fault print | `lore-adm: {error}` only. The cause was lost; "see the server log" pointed at nothing (no handler; lastResort dropped the `extra`). | The same first line, then `  ← caused by: …` lines, and the seam's record on stderr with `error_class` / `engine_error`. |
| `report-unmigrated --table` | **unvalidated**: any string was interpolated into `SELECT count() FROM {table} …` (an operator-side SurrealQL injection door on the admin CLI), after the stores were built and readied. | `_is_governed_table` before any store is built; stderr refusal names the table (sanitised); exit 1. |
| `migrate-governed --table <invalid>` | the stores were built and **`ensure_ready` ran (DDL)** before `migrate_governed` refused. | refused before any store is built (same `_not_supported` receipt text, one render `_render_migrate_refusal`). |
| legs (`_migrate_{memory_scope,agent_owner,message_owner}`) | on a schema-behind store: the operator resolution, then the idempotent **project-keep mint (a WRITE)**, then an opaque `unspecified rejection` from the UPDATE. Over 0 legacy rows it "succeeded" silently. | `_schema_predates_refusal` is the leg's FIRST action: a teaching refusal naming each missing column, exit 1, zero writes. |

**Removed-behaviour inventory:** every row above changes a fate ONLY for a wrong-shaped or invalid input. Every well-shaped path is pinned GREEN by the controls. The one deliberately dropped behaviour is `verify`'s deny on a wrong-shaped lookup (§3 FORK-2).

## 3. FORKS / FLAGS (surfaced, not silently settled)
- **FORK-1 (§13 D placement), with both readings written down.** §13 D says "the verb-level refusal (no leg runs)". §13.1 item 5 plus the D pins require the columns to be DERIVED from each leg's own statement. `test_memory_enforcement_63b_ia.py`'s §1.9 item 1 law says the statement is a FUNCTION-LOCAL literal in the leg ("R1 self-containment: the literal, the seam call and the exempt entry live in the SAME symbol"; a module constant or a helper is an L1 orphan). Outside the leg, production cannot reach that text except by AST-parsing its own source.
  - **Reading A** (literal "verb-level", in `migrate_governed` before the legs): needs the statement outside the leg (breaks §1.9 item 1) or a hand column map (breaks §13.1 item 5).
  - **Reading B** (TAKEN): each leg builds its literal FIRST and refuses before ANY read or write, including the keep mint and the operator resolution. The refusal happens before the leg does anything.
  - **Observable difference:** `_verb_level_refusal` (half-pairs, dangling senders, agent-first order) runs BEFORE the schema gate. On a store that is BOTH schema-behind AND has a verb-level problem, the verb-level refusal is served first. Every D pin is GREEN under B, including the all-fields-removed one-derivation pin.
  - Recommendation: accept B. If the lead or sidecar wants the schema refusal ahead of `_verb_level_refusal`, that is a design ruling about §1.9.
- **FORK-2 (`PrincipalKeyStore._as_rows`).**
  - §13 B names `_as_rows` "behind `revoke` / `set_*` / `delete`". `revoke` lives in `principal_keys.py` and reads through `PrincipalKeyStore._as_rows`, a separate tolerant clone outside the walker's domain (`principals.py` / `governed.py`).
  - **Reading A** (TAKEN): route it through `rows_of` too. This is the class fix: the same policy, and the clone is deleted.
  - **Reading B:** leave it tolerant.
  - **Consequence of A:** `verify` (the served token-auth path) now RAISES `SurrealStoreError` on a wrong-shaped hash lookup instead of a uniform "no-such-key" deny. A rejected lookup already raised before this change, so this adds no new failure class to the served path. Covering tests `test_token_verifier.py` + `test_principal_keys_store.py` are in the declared set: 0 GREEN→RED.
- **FLAG-1 (unowned red, NOT mine, RED at base full4 too):** `loremaster/tests/test_retry_seam.py::TestThereIsExactlyOneCatchScanner63cIAa28c::test_am34_5_exactly_one_walker_and_one_resolver_in_the_tree`.
  - Failure text: *"caught-class resolvers [`_catch_sites.py::resolved_by_import`, `test_preboot_schema_precondition_63c_13d.py::_leg_statements`] — exactly ONE may exist"*.
  - Round 4's D test file (`eval(compile(ast.Expression(...)))`) matches the am-37 §9 resolver-by-SHAPE derivation (`eval` ∧ `Expression`). Round 4's targeted set did not include `test_retry_seam.py`, so it was never seen.
  - No registry entry owns it, so it becomes `RED_ORPHANED` at the pytest leg on the packet's full suite.
  - It is test-side: either the D file stops using `eval`+`Expression`, or the pin's resolver shape narrows. Not edited, per the brief's STOP.
- **FLAG-2 (the currency tool vs CLAUDE.md):** `--currency --legs typecheck,ruff` renders `pytest NOT_RUN … ORPHAN` and `CURRENCY: FAIL — claimed but never run: pytest` (exit 1). CLAUDE.md says that invocation "runs NO pytest" and should read RED_ORPHANED 0.
  - Over the two legs it ran: typecheck RED_ADJUDICATED 83 (= round 4's 83) and ruff GREEN, so 0 orphans among the legs actually run.
  - The FAIL line is the tool treating the deliberately excluded leg as an unrun claim. Tool owner's call. Verbatim in §6.
- **FLAG-3:** `governed.py`'s MODULE docstring still says "STUB / runnable-RED … the bodies raise NotImplementedError". This is the same stale class as N-1, one level up. §13 ruled only the function docstring, so I did not touch it. Fix it now, or route it?
- **FLAG-4:** the `…caused by` cause lines print raw exception messages. An engine message with embedded newlines prints as-is (operator stderr, not a served MCP surface). Per spec §13 A secret guard, messages only; no sanitiser applied. Say if the lead wants `sanitise_line` there.
- **Deviation (disclosed):** `_rows_stamped` gained `noun` with a DEFAULT (`_BACKFILL_UPDATE_NOUN`). Without it, mypy flagged the test's own arity-probe branch (`test_fail_closed_shapes_63c_13b.py:222`, `call-arg`) as an UNOWNED typecheck red. Every production caller passes its own noun, and the default only labels a message.
- **Harness slip (disclosed):** my first quick run's log landed inside the scratch tree (a relative path in my runner). It was moved out before any receipt was taken and the runner was fixed; `git status` of the scratch tree shows only the intended files.

## 4. STORE-FACT PROBE (§13.1 item 4). Live on `ws://127.0.0.1:18000` (TEST store), 2026-09-30; minted `unique_database()`, reaped in `finally`
The instrument, pasted verbatim (run from the scratch tree: `PYTHONPATH=loremaster/tests uv run python probe_13_1_store_facts.py`):
```python
"""am-37 §13.1 item 4 — live probe of the two class-D store facts on the TEST store (ws://127.0.0.1:18000).

Mints a unique_database(), applies the production memory DDL (SCHEMAFULL), then measures:
  F1  INFO FOR TABLE <undefined table>   -> an answer with EMPTY maps, no error
  F2  UPDATE memory SET scope = … after REMOVE FIELD scope ON TABLE memory:
        over 0 rows -> silent (answers [])  |  over 1 row -> raises
Controls: INFO FOR TABLE memory lists `scope` before the REMOVE (the probe can see a defined field),
and the same UPDATE over 1 row on the healthy table succeeds (the raise is caused by the removal).
The database is dropped in `finally`. Never :18500.
"""
import asyncio

from _governed_contract import apply_ddl, seed_memory_legacy
from _surreal_harness import PRODUCTION_DIM, connect_admin, drop_database, make_env, run, unique_database
from loremaster.store import surreal_schema

UPDATE = "UPDATE memory SET scope = 'keep:probe' WHERE scope IS NONE"


async def main() -> None:
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    assert ":18500" not in env.url, env.url
    print(f"store={env.url} database={env.database}")
    connection = await connect_admin(env)
    try:
        await apply_ddl(connection, surreal_schema.generate_memory_ddl(dim=PRODUCTION_DIM), url=env.url)
        info_db = await run(connection, "INFO FOR DB")
        print(f"control: 'memory' in INFO FOR DB tables = {'memory' in info_db['tables']}; "
              f"'nosuch_13_1' in tables = {'nosuch_13_1' in info_db['tables']}")
        undefined = await run(connection, "INFO FOR TABLE nosuch_13_1")
        print(f"F1  INFO FOR TABLE nosuch_13_1 -> {undefined!r}")
        healthy = await run(connection, "INFO FOR TABLE memory")
        print(f"control: 'scope' in INFO FOR TABLE memory fields (before REMOVE) = {'scope' in healthy['fields']}")
        # control leg: the UPDATE over one legacy row on the HEALTHY table succeeds
        await seed_memory_legacy(connection, row_id="ctl_13_1", dim=PRODUCTION_DIM)
        control = await run(connection, UPDATE)
        print(f"control: UPDATE over 1 row on the healthy table -> {len(control)} row(s) stamped")
        await run(connection, "DELETE memory")
        removed = await run(connection, "REMOVE FIELD scope ON TABLE memory")
        after = await run(connection, "INFO FOR TABLE memory")
        print(f"REMOVE FIELD scope ON TABLE memory -> {removed!r}; 'scope' in fields after = {'scope' in after['fields']}")
        zero = await run(connection, UPDATE)
        print(f"F2a UPDATE over 0 rows after REMOVE FIELD -> {zero!r} (no error)")
        await seed_memory_legacy(connection, row_id="legacy_13_1", dim=PRODUCTION_DIM)
        try:
            one = await run(connection, UPDATE)
            print(f"F2b UPDATE over 1 row after REMOVE FIELD -> NO ERROR: {one!r}")
        except Exception as error:  # noqa: BLE001 - the measured outcome IS the raise
            print(f"F2b UPDATE over 1 row after REMOVE FIELD -> RAISED {type(error).__name__}: {error}")
    finally:
        await connection.close()
        await drop_database(env)
        print(f"reaped {env.database}")


asyncio.run(main())
```
Output, verbatim:
```
store=ws://127.0.0.1:18000/rpc database=test_4167412_9a88f852049e4cdcb2b4ab85ef5ad5db
control: 'memory' in INFO FOR DB tables = True; 'nosuch_13_1' in tables = False
F1  INFO FOR TABLE nosuch_13_1 -> {'events': {}, 'fields': {}, 'indexes': {}, 'lives': {}, 'tables': {}}
control: 'scope' in INFO FOR TABLE memory fields (before REMOVE) = True
control: UPDATE over 1 row on the healthy table -> 1 row(s) stamped
REMOVE FIELD scope ON TABLE memory -> None; 'scope' in fields after = False
F2a UPDATE over 0 rows after REMOVE FIELD -> [] (no error)
F2b UPDATE over 1 row after REMOVE FIELD -> RAISED InternalError: Found field 'scope', but no such field exists for table 'memory'
reaped test_4167412_9a88f852049e4cdcb2b4ab85ef5ad5db
```
Both facts landed in `docs/reference/surrealdb-31-capabilities.md` §1.9 (in the delta patch). The reference cites this report section, and the lead commit that carries the delta is the commit to cite.

## 5. Declared set + transitions (targeted; no full suite)
**Declared BEFORE any run** in `scratchpad/declared-files.txt` (md5 `2a6a8c93…`, written 17:01Z; the first run was admitted 17:01:30Z). It holds 62 files:
- round 4's four: `test_principals_cli`, `test_engine_rejection_seam`, `test_fail_closed_shapes_63c_13b`, `test_preboot_schema_precondition_63c_13d`;
- fix5's 21 (`REPORT-builder-63c-i-a-fix5.md` §4);
- `test_exhaustion_fates`, `test_retry_seam`, `test_governed_routing_63a`;
- the AST covering-test scan below (57 hits; it over-includes on purpose — generic method names).

```
test_425_stamp_owner_63a.py test_agent_capability.py test_agent_capability_seams.py test_agent_governance_63c_i_a.py test_agent_owns_principal_schema.py test_audit_store.py test_comms_footer.py test_comms_read_governance_63b_ii_b.py test_comms_schema.py test_comms_send_scope_63b_ii_a.py test_comms_tool.py test_engine_rejection_seam.py test_exhaustion_fates.py test_fail_closed_shapes_63c_13b.py test_findings_classes_64b.py test_findings_closeout_64b.py test_findings_enforcement_64b.py test_findings_governance_64b.py test_findings_migrate_64b.py test_findings_system_writer_64b.py test_fixwave_a19_63c_i_a.py test_fixwave_a19a_63c_i_a.py test_fixwave_a19b_63c_i_a.py test_fixwave_a28_63c_i_a.py test_fixwave_a28b_63c_i_a.py test_fixwave_a28c_63c_i_a.py test_governed_migration_63a.py test_governed_routing_63a.py test_governed_substrate_63a.py test_governed_substrate_64b.py test_keep_remediation_cli_61.py test_keep_remediation_store_61.py test_keeps_cli.py test_keeps_store.py test_link5_render_containment.py test_mcp_server.py test_memory_enforcement_63a_v.py test_memory_enforcement_63b_ia.py test_memory_f5_registration_63b_ib.py test_memory_replay_fidelity_63b_ib.py test_memory_retrofit_63a.py test_memory_supersede_atomicity_63b_ib.py test_message_enforcement_63b_ii_a.py test_message_migrate_63b_ii_a.py test_message_migrate_dirty_store_63b_ii_b.py test_migration_wire.py test_preboot_schema_precondition_63c_13d.py test_principal_delete_cascade_61.py test_principal_delete_governed_63a.py test_principal_keys_schema.py test_principal_keys_store.py test_principals_cli.py test_principals_store.py test_reanchor_58_r3_am6.py test_reanchor_58_r3_cas_seam.py test_reanchor_58_r3_tiers.py test_reanchor_58_r4_lease_fates.py test_retry_seam.py test_secret_typing.py test_token_verifier.py test_visible_keeps_61b.py test_wire_isolation_63a.py 
```
AST covering-test scan (`lore_impact` caps covering tests at 15, #518). The instrument, verbatim:
```python
"""AST covering-test scan (lore_impact caps covering tests at 15, #518): every test file whose AST
references (Name / Attribute / string constant) any production symbol this fix6 delta changes."""
import ast, pathlib, sys
SYMBOLS = {
    "authorize_guarded", "guarded_write", "group_all_count", "rows_of", "map_of",
    "report_unmigrated_governed_rows", "MigrateGovernedResult", "_as_rows", "_table_exists",
    "_rows_stamped", "_governed_select", "_agent_migration_preconditions", "AgentMigrationPreconditions",
    "migrate_governed", "_migrate_memory_scope", "_migrate_agent_owner", "_migrate_message_owner",
    "_dispatch", "_dispatch_report_unmigrated", "_dispatch_keep", "main", "build_parser",
    "verify", "revoke", "mint", "create", "set_subject", "set_status", "set_expires", "delete",
    "_MIGRATE_VALID_TABLES", "messages_left_unmigrated", "unsound_sender_messages",
    "migrate-governed", "report-unmigrated",
}
# module anchors: a hit only counts in a file that imports one of these production modules
ANCHORS = ("loremaster.principals", "loremaster.governed", "loremaster.principal_keys", "loremaster.keeps",
           "from loremaster import principals", "principals", "governed")
root = pathlib.Path(sys.argv[1])
hits = {}
for path in sorted(root.glob("test_*.py")):
    text = path.read_text(encoding="utf-8")
    if not any(a in text for a in ANCHORS[:4]) and "import principals" not in text and "governed" not in text:
        continue
    tree = ast.parse(text)
    found = set()
    for node in ast.walk(tree):
        name = node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else (
            node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None)
        if name in SYMBOLS:
            found.add(name)
    if found:
        hits[path.name] = sorted(found)
for name, found in hits.items():
    print(name, ",".join(found))
```

**Runs:** ONE tree, `cmp`-verified swaps of the three production files, and `loremaster/loremaster/**/__pycache__` cleared before each run.
- Every run went through `scratchpad/gated_run.sh`: it waits until no other pytest is alive AND MemAvailable ≥ 20 GiB, then `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider -rfE <files>`.
- There were no cap kills. Memory-gate wait = 0 s on every run (admission lines below).
- The two `--collect-only` passes were NOT gated. Each was a single process of a few seconds, with no other pytest alive (checked just before).

| run | admitted | result | log md5 |
|---|---|---|---|
| base (full4) | 17:14:46 avail=39GiB others=0 waited=0s | 477 failed, 4556 passed, 1 skipped, 7 warnings in 589.94s (0 | `a230d9bd…` |
| build v1 (map_of message before the a28 A2 fix) | 17:04:30 avail=26GiB others=0 waited=0s | 273 failed, 4757 passed, 1 skipped, 7 warnings in 589.26s (0 | superseded |
| **build (final)** | 17:25:34 avail=65GiB others=0 waited=0s | 269 failed, 4761 passed, 1 skipped, 7 warnings in 576.56s (0 | `5198af3b…` |

The base collects 5034 nodes and the build 5031. The difference is ENTIRELY production-derived parametrization: 12 ids exist only on base and 9 only on build.
- The shape-tester walker set shrinks (the 6 old testers stop testing shape; `[governed.map_of]` and `[governed.rows_of]` appear).
- The line-keyed wrap-site ids shift (plus one new site, `principals.py::_migrate_message_owner`, which is F-5).
- Every build-only id PASSES.

**Transitions** (joined by node id; `-rfE` failure lists; non-test `ERROR <logger>:` rows are captured log lines, excluded: 477 / 269 test ids = the tails):
- **GREEN→RED: 0.** No build-only id fails.
- **RED→GREEN: 200 on common ids, ALL inside round 4's declared 209** (`…39327f47…/scratchpad/declALL.txt`, md5 `aeba0126…` sorted). There are 0 RED→GREEN outside the declared set.
- **The declared 209, all accounted for:**
  - 200 RED→GREEN on common ids.
  - 8 are not collected on the build because their parameter is production-derived:
    - 6 walker ids (`[governed.authorize_guarded]`, `[principals._agent_migration_preconditions]`, `[principals._governed_select]`, `[principals.PrincipalStore._as_rows]`, `[principals.PrincipalStore._table_exists]`, `[principals._rows_stamped]`) — the function no longer tests shape, which IS the pass condition;
    - 2 line-keyed ids (`principals.py::create::515` → `::524`, `::set_subject::644` → `::658`) whose build ids PASS.
  - 1 stays RED: `test_exhaustion_fates.py::TestTheRegistryIsTheAdjudicationBothWays::test_every_row_names_a_ruled_classification_an_owner_and_evidence_that_HOLDS`. It is the `packet-58-contract` row, red on the round-4 reference too (its "packet-58 lease pin"), and in fix4/fix5's owned list.
- **Remaining 269 build reds, all red on base too:**
  - `packet-58-contract` — 33: `test_reanchor_58_r3_tiers` 16, `r3_am6` 8, `r3_cas_seam` 4, `r4_lease_fates` 4, `test_exhaustion_fates` 1.
  - `packet-64b-i-contract` — 235: `test_comms_footer` 81, `test_governed_substrate_64b` 34, `test_findings_migrate_64b` 28, `test_mcp_server` 28, `test_findings_classes_64b` 27, `test_findings_governance_64b` 24, `test_findings_system_writer_64b` 9, `test_findings_enforcement_64b` 4. Every path is registered in `scripts/pending_contracts.yaml`; e.g. `UNBUILT (#407): governed.classify_zero_row_cas does not exist`.
  - **UNOWNED — 1: `test_retry_seam.py::…test_am34_5_exactly_one_walker_and_one_resolver_in_the_tree`** (§3 FLAG-1). It is red at base, caused by round 4's D test file, not by this build.
- The round-4 files: 0 failures in the final build run (none appears in the per-file red list above). The earlier quick run `quick2.log` gave 447 passed / 0 failed, but it was taken BEFORE the last two production edits (the `map_of` type-naming message and the `_rows_stamped` default noun), so the final run is the receipt of record.

## 6. Currency, verbatim (the final tree, 2026-09-30 ~17:37Z): `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff`. The long owner prose is cut at 260 chars/line; the full log is `scratchpad/currency-final.log`.
```
========================================================================
GATE CURRENCY — is every CLAIMED gate green, or owned?
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract (owner: packet 58 (supersede re-anchor + task guarded-append shell + finding 130 + amendments 1-8) — the 58 builder, serial after 63c-i-a; trigger: the packet-58 build lands TaskLedg
  ruff         GREEN
  pytest       NOT_RUN — claimed by the manifest, never executed
      ORPHAN: gate 'pytest' is CLAIMED by the manifest and was NOT RUN — a claimed-but-unrun gate is finding #312 exactly. This says NOTHING about whether it would pass.
CURRENCY   : FAIL — claimed but never run: pytest
  (this is NOT the deploy receipt: it answers 'is every gate owned', never 'may this ship')
```
- Gate exit = 1 (FLAG-2).
- typecheck: RED_ADJUDICATED **83** (= round 4's 83; owners `packet-58-contract` · `packet-64b-i-contract`).
- ruff: **GREEN**. `uv run ruff check .` → `All checks passed!`
- Orphans among the legs actually run: **0**.
- An earlier run showed 1 ORPHAN, `test_fail_closed_shapes_63c_13b.py:222 call-arg`. It was caused by my `_rows_stamped` signature and fixed by the default noun (§3 deviation).

## 7. Secret-guard receipt (§13 A). awk over every `extra=` span in `store/_txn.py`, `principals.py`, `keeps.py`, on the final tree
The instrument, verbatim (`scratchpad/secret_guard.awk`):
```awk
# For every `extra=` occurrence, capture the span up to the balancing `}` of its dict (or the line, if the
# value is a Name), print it, and count password|token|secret hits inside the captured spans.
/extra=/ { capturing=1; depth=0; span=""; start=FNR }
capturing {
  line=$0; span=span " " line
  n=split(line, ch, "")
  for (i=1;i<=n;i++){ if (ch[i]=="{") depth++; if (ch[i]=="}") depth-- }
  if (depth<=0) {
    sites++
    lowered=tolower(span)
    hit=(lowered ~ /password|token|secret/)
    if (hit) hits++
    gsub(/  +/," ",span)
    printf "%s:%d %s %s\n", FILENAME, start, (hit?"HIT":"ok "), substr(span,1,150)
    capturing=0
  }
}
END { printf "SITES=%d HITS=%d\n", sites, hits+0 }
```
```
store/_txn.py:1017 ok   extra={ "statement_index": root_cause.index, "statement_count": statement_count, "status": _ERR_STATUS, "engine_result": root_cause.raw_result, "fail
store/_txn.py:1162 ok   logger.warning("store.retry.exhausted", extra=extra)
store/_txn.py:1399 ok   logger.error(label, extra={"url": url, "error_class": error_class, "engine_error": str(error)})
store/_txn.py:1788 ok   logger.error("store.transaction.malformed_response", extra={"response": response})
store/_txn.py:1843 ok   extra={ "statement_index": index, "parse_error": f"{type(parse_failure).__name__}: {parse_failure}", },
principals.py:224 ok   model_config = ConfigDict(extra="forbid", frozen=True)
principals.py:375 ok   extra={"namespace": self._namespace, "database": self._database},
principals.py:403 ok   logger.debug("principal.schema.ready", extra={"database": self._database})
keeps.py:126 ok   model_config = ConfigDict(extra="forbid", frozen=True)
keeps.py:146 ok   model_config = ConfigDict(extra="forbid", frozen=True)
keeps.py:261 ok   extra={"namespace": self._namespace, "database": self._database},
keeps.py:293 ok   logger.debug("keep.schema.ready", extra={"database": self._database})
SITES=12 HITS=0
```
- **0 hits.**
- `_txn.py`'s `extra=extra` (`store.retry.exhausted`) is built from `attempts`, `elapsed_seconds`, `label`, `url` and `engine_error`: no credential.
- The CLI formatter renders ONLY `error_class` / `engine_error` (`_CLI_LOG_EXTRA_KEYS`), never `url` or any other extra.
- Three `extra="forbid"` hits are pydantic `ConfigDict`s (false positives of the pattern, listed not hidden).

## 8. Retired-name sweep (§13 C F-4). BARE pattern `unsound_sender_messages`, awk over every `*.py/*.md/*.yaml/*.yml/*.toml/*.sh` in the final scratch tree (`.venv` and `.git` pruned)
- Package (`loremaster/loremaster/**`), `docs/reference/`, `scripts/`: **0 hits**.
- One verdict per hit:

| hit | verdict |
|---|---|
| `docs/design/2026-09-29-packet63c-amendment-37.md:218` | HISTORY — the ruling doc keeps its history (§13 C: "this doc keeps its history") |
| `docs/design/2026-09-29-packet63c-amendment-37.md:315` | HISTORY — the ruling doc keeps its history (§13 C: "this doc keeps its history") |
| `docs/design/2026-09-29-packet63c-amendment-37.md:338` | HISTORY — the ruling doc keeps its history (§13 C: "this doc keeps its history") |
| `docs/design/2026-09-29-packet63c-amendment-37.md:339` | HISTORY — the ruling doc keeps its history (§13 C: "this doc keeps its history") |
| `docs/design/2026-09-29-packet63c-amendment-37.md:385` | HISTORY — the ruling doc keeps its history (§13 C: "this doc keeps its history") |
| `docs/design/2026-09-29-packet63c-amendment-37.md:593` | HISTORY — the ruling doc keeps its history (§13 C: "this doc keeps its history") |
| `loremaster/tests/test_principals_cli.py:1392` | PIN — `_RETIRED_FIELD`, the constant the retired-name pin scans FOR (correct) |
| `REPORT-blindreader-63c-i-a-4.md:15` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-blindreader-63c-i-a-4.md:51` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-blindreader-63c-i-a-4.md:52` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-blindreader-63c-i-a-4.md:133` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-blindreader-63c-i-a-4.md:233` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-blindreader-63c-i-a-4.md:234` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix2.md:8` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix2.md:39` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix2.md:75` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix2.md:172` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix2.md:225` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix3.md:35` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix3.md:84` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix3.md:91` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix3.md:102` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix3.md:109` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix3.md:110` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix3.md:157` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix3.md:204` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix3.md:205` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix3.md:212` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix3.md:287` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix3.md:297` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix3.md:338` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix3.md:461` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-builder-63c-i-a-fix3.md:489` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-coldaudit-63c-i-a-4.md:110` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-coldaudit-63c-i-a-4.md:113` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-coldaudit-63c-i-a-4.md:116` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-coldaudit-63c-i-a-4.md:122` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-coldaudit-63c-i-a-4.md:123` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-coldaudit-63c-i-a-4.md:124` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-coldaudit-63c-i-a-4.md:132` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-coldaudit-63c-i-a-4.md:135` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-coldaudit-63c-i-a-4.md:181` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-coldaudit-63c-i-a-4.md:217` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-coldaudit-63c-i-a-4.md:239` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-coldaudit-63c-i-a-4.md:667` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-coldaudit-63c-i-a-4.md:776` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-lead-63c.md:1589` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-lead-63c.md:1635` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-lead-63c.md:1654` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-lead-63c.md:1661` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-lead-63c.md:1688` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-lead-63c.md:1693` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-lead-63c.md:1732` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-lead-63c.md:1824` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-lead-63c.md:1833` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-sidecar-63c-2.md:162` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |
| `REPORT-sidecar-63c-2.md:164` | HISTORY — a dated report, kept as written (archived record; renaming inside it would falsify it) |

## 9. DRY ledger (brief-base §6): new reusable symbols
`lore_search` was not run for these. The spec NAMED the homes (`rows_of` / `map_of` in `governed`, §13 B / §13.1), and the candidates were derived by the test-side allowlist walker. The duplicate search was the awk over `isinstance(…, list|dict)` in §1 (all 7 sites routed) plus the `_as_rows` caller sweep; lore was not re-queried (said out loud).

| new symbol | search | found | disposition |
|---|---|---|---|
| `governed.rows_of` | awk `isinstance(.*(list\|dict)` over principals/governed + `_as_rows` defs package-wide | tolerant clones in `principals._as_rows`, `principal_keys._as_rows`, `_governed_select`, `_rows_stamped`, `authorize_guarded`, plus foreign tolerant `_as_rows` in agents/briefs/diff/findings/messages/tasks | HAND-ROLLED as the ruled ONE home. The 63c clones are ROUTED through it. The foreign clones (agents, briefs, diff, findings, messages, tasks) are **NOT routed** — outside §13 B's domain; FLAG for the 64b §DRY step beside `group_all_count`. |
| `governed.map_of` | same awk | `_table_exists`, `_agent_migration_preconditions` clones | HAND-ROLLED as the ruled ONE home (§13.1 item 1); both clones routed (the precondition clone DELETED). |
| `principals._set_columns` / `_schema_predates_refusal` | awk `SET ` parsers package-wide | none in production; the D test file has its own parser (test-side, independent by design) | HAND-ROLLED. There is no SurrealQL parser in the installed SDK (`surrealdb` 2.0.0; its modules were listed and `request_message.sql_adapter` read: it only joins command strings). |
| `principals._is_governed_table` | callers of `_MIGRATE_VALID_TABLES` | one inline membership test in `migrate_governed` | EXTENDED: the inline test became the ONE function, and all three sites call it. |
| `principals._fault_line`, `_cli_logging`, `_CliLogFormatter`, `_CliStderrHandler`, `_render_migrate_refusal` | lore-adm prints / logging handlers package-wide | no CLI log handler anywhere; refusal print was one site | HAND-ROLLED (stdlib `logging` subclasses — package-backed). `_render_migrate_refusal` replaces the one inline print and serves the new zero-I/O path too. |

## 10. Backups (production NOT committed; the lead commits after the re-check GO)
| artifact | md5 |
|---|---|
| FULL 63c-i-a patch `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/9744862d-d833-4a43-b77a-bdbeb70a77d0/scratchpad/builder-63c-i-a-fix6.full.patch` (`git diff --binary HEAD` of the scratch tree + `git diff --no-index` for the 2 untracked round-4 test files; 20 file diffs) | `3132f699d5e0330c09efbbc58c0c3d0f` |
| DELTA over full4 (production + reference doc) `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/9744862d-d833-4a43-b77a-bdbeb70a77d0/scratchpad/builder-63c-i-a-fix6.delta.patch` | `bfd73d83a9f073892c795f73df140f51` |
| `loremaster/loremaster/principals.py` | `3d5bac01259c715f2b67824812cf4463` |
| `loremaster/loremaster/governed.py` | `eb9f47067243b5eada04cf63b8aa98f7` |
| `loremaster/loremaster/principal_keys.py` | `756584370a79cba67361d1cc3076238a` |
| `docs/reference/surrealdb-31-capabilities.md` | `73487207fdf0aefe0a070c24f5160754` |

- `cp -a` copies: `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/9744862d-d833-4a43-b77a-bdbeb70a77d0/scratchpad/changed-files/` (build); `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/9744862d-d833-4a43-b77a-bdbeb70a77d0/scratchpad/base-full4/` (full4 originals).
- Scratch base HEAD `365f7695065720412b2f7b46028a85cc47ca7824`. Main HEAD at report time is `88625436c6c3299a08776efe6f4e61c6634e726a` (moved by docs only: `REPORT-lead-63c.md` +5 lines).
- `git apply --check --cached <full.patch>` at main HEAD `8862543`: **OK**.
- The delta over the full4 originals reproduces all 4 build files byte-exact (`patch -p1` + `cmp`, in `scratchpad/deltacheck2`).

## RESUME (lead, ~17:45Z 2026-09-30 — FORK-1 accepted via am-37 §13.2 `5f39564`; FORK-2 accepted; FLAG-1 + arity probe fixed test-side in round 5 `7a1dac4`; FLAG-2/FLAG-4 residuals)
Work happened in the same `fix6` scratch tree. `cp -a` backups were taken first: `scratchpad/pre-r5/` for principals, governed and the two round-4 test files.

**Summary:**
- **State:** done.
- **Tests:** 0 GREEN→RED vs the `c8c3435` build. `test_am34_5` is GREEN. **0 unowned reds.**
- **Gates:** ruff clean; typecheck RED_ADJUDICATED 83 (unchanged).
- **Deviation (1, disclosed):** besides the module docstring (FLAG-3), I also rewrote the `GovernedAuditUnavailable` CLASS docstring in `governed.py`. It carried the same stale "CONTRACT STUB … `guarded_write` SILENTLY SKIPS the audit" prose. It now states the fact: `authorize_guarded` raises it before any durable effect. There is no `__doc__` pin on governed, and this is prose only.
- **Harness (disclosed):** the first run was started before a `ruff` E501 in the new module docstring was fixed. It was stopped by PID (97350/97359/97371) after ~1 min with no result used; its log is kept as `r5-declared.ABORTED.log`. The line was fixed and the run restarted on the final bytes.

| step | edit | receipt |
|---|---|---|
| 1 | r5 test delta `…39327f47…/scratchpad/fixup-tests-63c-i-a-2.r5.delta.patch` (md5 `5ef35641295e40cc8e143f647fe2784e` verified); `git apply --check` + apply clean. It touches `test_fail_closed_shapes_63c_13b.py` and `test_preboot_schema_precondition_63c_13d.py` only. | applied |
| 2 | `_rows_stamped(update_result, *, noun: str)` — no default. `_BACKFILL_UPDATE_NOUN` DELETED (awk: 0 occurrences). All three legs pass their own noun. | typecheck 83, 0 orphans on the run legs |
| 3 (FLAG-3) | `governed.py` MODULE docstring rewritten to what the module does: the built substrate, the listed entry points, the THREE fail-closed shape readers, R4 routing. No "STUB / runnable-RED / NotImplementedError" remains (awk over `governed.py`: 0 hits for `STUB\|runnable-RED\|NotImplementedError`). | ruff clean |
| 4 (§13.2 rider) | Each of `_migrate_memory_scope`, `_migrate_agent_owner` and `_migrate_message_owner` gains an `ORDERING BOUND (am-37 §13.2)` docstring paragraph. The schema gate is the leg's FIRST action, before any leg read or write; *"a verb-level refusal may precede this gate; each such refusal is true independently of the schema, and this gate runs before any leg read or write."* | AST-read of the three docstrings, checked |

**Targeted run:** the same 62-file declared set (md5 `2a6a8c93…`), which already contains both round-5 files. It went through `gated_run.sh`: process table clear, MemAvailable ≥ 20 GiB, `MemoryMax=16G`, `-n 8`, `--timeout=300`.
- Admitted: `ADMITTED 17:48:30 avail=47GiB others=0 waited=0s`.
- Result: `268 failed, 4762 passed, 1 skipped, 7 warnings in 596.88s (0:09:56)` (5031 nodes = the `c8c3435` build).
- **GREEN→RED vs the `c8c3435` build (`build2-declared.log`): 0.**
- **RED→GREEN: exactly 1** — `test_retry_seam.py::TestThereIsExactlyOneCatchScanner63cIAa28c::test_am34_5_exactly_one_walker_and_one_resolver_in_the_tree` (FLAG-1 closed).
- **Remaining 268 reds, all owned, ZERO unowned:**
  - `packet-58-contract` 33: `r3_tiers` 16, `r3_am6` 8, `r3_cas_seam` 4, `r4_lease_fates` 4, `test_exhaustion_fates` 1.
  - `packet-64b-i-contract` 235: `test_comms_footer` 81, `governed_substrate_64b` 34, `findings_migrate_64b` 28, `test_mcp_server` 28, `findings_classes_64b` 27, `findings_governance_64b` 24, `findings_system_writer_64b` 9, `findings_enforcement_64b` 4.
- The id sets are the same files and counts as §5; no other file reddens.

**Currency, verbatim** (`--currency --legs typecheck,ruff`, ~17:50Z; owner prose cut at 200 chars; full log `scratchpad/currency-r5.log`):
```
========================================================================
GATE CURRENCY — is every CLAIMED gate green, or owned?
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract (owner: packet 58 (supersede re-anchor + task guarded-append shell + finding 130 + amendments 1-8) — the 58 builder, seria
  ruff         GREEN
  pytest       NOT_RUN — claimed by the manifest, never executed
      ORPHAN: gate 'pytest' is CLAIMED by the manifest and was NOT RUN — a claimed-but-unrun gate is finding #312 exactly. This says NOTHING about whether it would pass.
CURRENCY   : FAIL — claimed but never run: pytest
  (this is NOT the deploy receipt: it answers 'is every gate owned', never 'may this ship')
```
- typecheck RED_ADJUDICATED **83**; ruff GREEN; RED_ORPHANED on the run legs **0**.
- Exit 1 is the known FLAG-2 residual (the excluded pytest leg rendered as unrun).
- `uv run ruff check .` → `All checks passed!`

**Re-cut patches:**

| artifact | md5 |
|---|---|
| **FINAL 63c-i-a patch** `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/9744862d-d833-4a43-b77a-bdbeb70a77d0/scratchpad/builder-63c-i-a-fix6.r5.full.patch` (`git diff --binary HEAD` + `--no-index` for the 2 untracked test files) | `bec291900a49c2e5df0704ef912fd5b9` |
| delta over `3132f699` `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/9744862d-d833-4a43-b77a-bdbeb70a77d0/scratchpad/builder-63c-i-a-fix6.r5.delta.patch` (principals.py, governed.py, the 2 round-5 test files; `principal_keys.py` + the reference are unchanged, `cmp`-verified) | `2bb39a7b56613ee4dfceb605ca709bf7` |
| `loremaster/loremaster/principals.py` | `06f367c7d3782b4e373f6151e1f2c604` |
| `loremaster/loremaster/governed.py` | `388a94890eebed779d3015e7d72f0895` |
| `loremaster/loremaster/principal_keys.py` (unchanged) | `756584370a79cba67361d1cc3076238a` |
| `docs/reference/surrealdb-31-capabilities.md` (unchanged) | `73487207fdf0aefe0a070c24f5160754` |

- `cp -a` of the changed files: `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/9744862d-d833-4a43-b77a-bdbeb70a77d0/scratchpad/changed-files-r5/`.
- Scratch base HEAD `365f769`. Main HEAD at re-cut is `4ed61f8`, which moved by docs only (no `loremaster/`, `scripts/` or `docs/reference/` change since `365f769`).
- `git apply --check --cached <r5.full.patch>` at main HEAD `4ed61f8`: **OK**.
- The delta, applied over the `3132f699` state (the `pre-r5/` copies), reproduces all 4 files byte-exact (`patch -p1` + `cmp`, `scratchpad/deltacheck3`).

## RESUME 2 (lead, ~02:06Z 2026-10-01 — am-37 §13.3 production, the FINAL capped round; + lead note on F-5: derived leg set)
brief project v7 read (re-register). Work happened in the same `fix6` scratch tree, which provenance-asserts itself (`loremaster.__file__` = `…/scratchpad/fix6/loremaster/loremaster/__init__.py`, printed by the probe below).

**Summary:**
- **State:** done, with ONE OPEN FORK (item 4 vs `restore_prod_dump.py`, below).
- **Tests:**
  - 0 GREEN→RED vs full6.
  - RED→GREEN is **exactly** round 6's 131 declared ids: ⊇ holds, with equality.
  - The 268 remaining reds are byte-identical to round 5's owned set (58: 33, 64b-i: 235), so **0 unowned**.
- **Gates:** typecheck RED_ADJUDICATED 83 (unchanged); ruff GREEN; `ruff check .` clean.
- **sha512 sweep → NO fallback.** `scrub_text` learns the 128-hex shape for every sink.
- **Live mint-collision receipt:** 0 hex runs on stderr; the control (scrub disabled) shows 2.

### Setup receipts
- `cp -a` first, to `scratchpad/pre-r6/`: governed, principals, principal_keys, logging_setup.
  - ⚠ **Disclosed slip:** `keeps.py` was NOT in that first copy. I learned it was in scope only when the F-6 site list reached it.
  - Its pre-edit content is bec29190's own, so no content was at risk. It was reconstructed from HEAD + `r5.full.patch` as `pre-r6/keeps.py.bec29190` (md5 `6945cb55…`) and proven to differ from the edited file by exactly the 6 noun insertions.
  - The fresh reconstruction in `recon-r6` independently yields the same `6945cb55`.
- r6 test delta `fixup-tests-63c-i-a-2.r6.delta.patch`: md5 `2aff7c3a46be9bd92ab3c42868cb47ee` verified; `git apply --check` + apply clean.
- ⚠ **FLAG-r6-1 (test side's full6 patch is NOT a complete full patch).**
  - My tree after the delta, diffed against HEAD and path-sorted, reproduces full6 md5 `ca4598259d2727b95c6dff877edc27ad` **only after removing** the two untracked round-4 test files: `test_fail_closed_shapes_63c_13b.py` and `test_preboot_schema_precondition_63c_13d.py`.
  - full6 OMITS both of them, although bec29190 carried them. Applying full6 alone at main would silently drop the round-4 test files.
  - My `r6.full.patch` (below) carries them.

### Build per §13.3

| item | edit | pin / receipt |
|---|---|---|
| 1 F-1 | `_set_columns` now reads through ONE `_SetClauseScanner`, a single depth+quote pass over the whole statement. Brackets `()[]{}` are one stack (a mismatched closer raises). Strings `'`/`"` honour a backslash escape. The top-level `SET` opens the clause. `WHERE`/`RETURN`/`TIMEOUT`/`PARALLEL` end it, and `,` splits it, only at depth 0 outside a string, case-insensitively, as whole words. Each item must match `<ident> (=\|+=\|-=\|+?=) <non-empty>`. It raises on an open quote, an open bracket, no top-level SET, a non-identifier target (`a.b`) and an empty item. The regex end-split (`_SET_CLAUSE_START/_END`) is DELETED (awk: 0 hits). | corpus 15/15 exact, 4/4 must-raise; extra probes `'it\'s, x'`, `[1, 2]`, `{k: 1, j: 2}` exact; `, ,` / `(1]` / `a.b` / `a =` raise |
| 2 F-2 | (i) `_cli_logging`: `handler.addFilter(RedactingFilter())`. (ii) `logging_setup._scrub_text` is promoted to PUBLIC `scrub_text`: one name, all callers renamed, `_scrub_text` has 0 hits in the package. `_fault_line` renders the error and every cause through it. (iii) `_CREDENTIAL_HASH_RE = (?<![0-9A-Fa-f])[0-9A-Fa-f]{128,}(?![0-9A-Fa-f])`, applied LAST in `scrub_text`. A 64/127-hex run, a git SHA and a UUID are untouched. The module docstring's "only LABELLED shapes" claim now names this one fixed-LENGTH exception, its bound and its re-open trigger (no entropy prose; the corpse-prose pin is green). | live receipt below |
| 3 #527 | `_fault_line` walks `__cause__` ONLY, with `seen = {id(exc)}`. | 2-cycle → `lore-adm: alpha-cause / ← caused by: beta-cause`, each once |
| 4 #528 | `report_unmigrated_governed_rows` calls the ONE validator `principals._is_governed_table` (function-local import, the house cycle idiom) BEFORE any I/O and raises `ValueError` (in the lore-adm tuple: an input fault). The docstring makes no caller claim. `_dispatch_report_unmigrated` keeps its pre-I/O check. | ⚠ **OPEN FORK**, below |
| 5 F-3 | `rows_of(result, *, noun, landed=False)`. `landed=True` renders the ONE template `_LANDED_SHAPE_FAULT` (byte-exact per the pin). The un-landed texts are byte-unchanged. Both `_as_rows` wrappers thread `landed`. `landed=True` is set at every CREATE/UPDATE `RETURN AFTER` read: principals create/set_status/set_subject/set_expires, principal_keys mint/revoke, and `_rows_stamped` (the 3 legs). The test's own derivation selects them. KeepStore's 6 sites are SELECT reads: noun only (lead note). | population pin green |
| 6 F-5 | Remedy is DERIVED. `t ∈ _MIGRATING_TABLES` → "run `lore-adm migrate-governed --table t` to backfill"; else → "no migrate verb accepts `t` yet — N row(s) remain unscoped". **Per the lead's note (no hand list)**, the three legs are dispatched through ONE mapping `_MIGRATE_LEGS: {table: leg}` (a frozen `_LegCall` carries the verb's measured inputs), and `_MIGRATING_TABLES = tuple(_MIGRATE_LEGS)`. The verb runs a leg ONLY through that mapping and answers any other valid table `_not_supported`, so the set the remedy reads IS the set the verb executes. | `brief` → no-verb form |
| 7 F-6 | `PrincipalStore._as_rows` / `PrincipalKeyStore._as_rows`: `noun` keyword-only and REQUIRED. The 18 in-domain calls each name their read: principals 8, principal_keys 4, keeps 6 (`PrincipalStore._as_rows`). The edit was AST-positioned and reflowed. | site pin green; `test_the_row_reader_wrappers_require_noun` green |
| 8 F-7 | `GovernedStatementError(RuntimeError)` holds every `_set_columns` raise. It is NOT in `_dispatch`'s tuple, so it tracebacks; `ValueError` stays in the tuple. | pins green |
| 9 NITs | #19 "(below)" → "(above)". #21: the message-leg comment now states the F-4 fact (counts EVERY row still unscoped+ownerless after the backfill; commonly sender-unsound; a row inserted mid-run counts too). #31: `_not_supported` derives both lists via `_backticked(...)`: "today:" from `_MIGRATING_TABLES`, the governed list from `_MIGRATE_VALID_TABLES`. | #31 pins green |

### ⚠ OPEN FORK — item 4 vs `scripts/restore_prod_dump.py` (ledger #17142, thread `q:63c-r6-item4-restore`, NO reply at commit)
- **The ruling's claim is false, measured.** Item 4 says restore is "covered by construction". In the fix6 tree, `SliceDeriver().governed_slice()` marks `governed_node=True` for `[agent, brief, finding, memory, message, task]`. `_read_back` calls `report_unmigrated_governed_rows(handle, t)` for each.
- `finding` and `task` are OUTSIDE `_MIGRATE_VALID_TABLES`. With item 4 as ruled (built, pinned), the default restore read-back now RAISES `ValueError` on them. No test covers this path.
- **Options:**
  - (A) as ruled — built, provisional;
  - (B) RECOMMENDED — the report's validator domain is the governed set ∪ the pending-packet tables. It is still ONE validator function, but a second membership is a design call;
  - (C) restore skips non-reportable tables and records "not reportable".
- The lead rules. I did NOT edit `restore_prod_dump.py`.

### sha512 / 128-hex producer sweep (item 2 iii) — the fallback decision
Method:
- awk over all of `loremaster/`, `lorescribe`, `loresigil`, `lorerunes` and `scripts/` for `sha512|sha3_512|blake2b|hexdigest|.hex()`;
- then an **AST sink sweep** (`scratchpad/sha_sink_sweep.py`): every logger call and every `raise` whose arguments name `sha|hash|digest`;
- then the UNIQUE indexes in `surreal_schema.py` that cover a hash column, since the engine echoes a duplicate VALUE into `engine_error`.

| producer (file) | value | reaches a scrubbed sink? | verdict |
|---|---|---|---|
| `principal_keys.mint` / `principals` mint verb (`sha512_hex(f"{name}:{secret}")`) | credential hash | YES: `principal_key_hash` UNIQUE echo in `engine_error` + cause line (live receipt) | MUST redact |
| `agents.py` `capability_hash` (`sha512_hex`, :926/:1102) | credential hash | same class: UNIQUE capability-hash index echo | MUST redact |
| `token_verifier.py:363` `sha512_hex(token)` | cache key | no log or raise argument (AST sweep: 0) | n/a |
| `index/indexer.py` content_hash (:525/:1215/:1594) → manifest / `file` / `file_text` / snapshot `sha512` | content digest | no logger/raise carries it (AST sweep: 0 hits; `store_read` integrity error names tier+path only; `surreal.py:1385` names the KEY `_FILE_TEXT_SHA_KEY`, not a value); no UNIQUE index on a content-sha column | not in a served line |
| `diff.py` snapshot sha512 compare | content digest | no log/raise | not in a served line |
| `floor_calibration/domain.py` (:139/:241) | content digest | no log/raise | not in a served line |
| sha256 (`server.py:10815`, `index/schema.py:136`, `calibration/baseline.py:58`), blake2b/2s (`scripts/gated_ground.py`, `lorerunes/pdp.py`), md5 (`scripts/mutation_proof*`) | 64/32/16 hex | n/a | below 128 — untouched (control pin) |

- **Decision: the PRIMARY rule.** `scrub_text` redacts the shape everywhere; the §13.3 fallback (`secret_params` + driver withholding) is NOT taken.
- **Named bound + re-open trigger** (in the `_CREDENTIAL_HASH_RE` comment): the first log line that must carry a content sha512 → narrow to the mint seam's record.

**Live receipt, item 2** (`scratchpad/probe_r6_mint_collision.py`, log `probe_r6_mint_collision.log`).
- Setup:
  - the REAL `lore-adm main()` on `:18000`, fresh `unique_database()`, reaped;
  - two principals mint `laptop-<leg>` with `secrets.token_urlsafe` pinned, so the hashes are identical and `(principal, name)` stays distinct.
- **SCRUBBED: rc=1, 128-hex runs on stderr = 0.**
  - `engine_error=Database index \`principal_key_hash\` already contains '***REDACTED***'`
  - `← caused by: …already contains '***REDACTED***'`
- **CONTROL** (`scrub_text` = identity at `logging_setup` + the `principals` binding): rc=1, **runs = 2** (`ca0cc4c6…a1bbe` in the log line AND the cause line).
- ⚠ **Observed side effect (residual, < MAJOR):** in the scrubbed leg the record id `principal_key:<id>` also redacts. This is the PRE-EXISTING `_COMPOUND_ASSIGNMENT_RE` trade (`_key:` is a label, "cache_key=abc redacts"), newly visible because the CLI sink is now filtered. It costs a diagnostic, not a secret.

### Removed-behaviour inventory (this round's delete/replace)
- **Regex end-split parser** — replaced, preserved-with-pin. §13.3 item 1: the shipped 3 statements parse identically; the narrowing cases now parse exactly or raise.
- **Raise class** — `ValueError` → `GovernedStatementError`. Dropped deliberately (item 8).
- **`_scrub_text`** — renamed `scrub_text`, no alias kept ("one name", item 2 ii).
- **Hand-listed `_not_supported` tables** — replaced by derivation (#31).
- **The `if/elif` leg branches** — replaced by `_MIGRATE_LEGS`. preserved-with-pin: same three legs, same args, same order of checks (refusal → not-a-leg → undefined table → leg).
- **Default `noun` on `_as_rows`** — dropped deliberately (item 7).

### Targeted run
**Declared set:** 66 files, written BEFORE any run (`scratchpad/declared-r6.txt`, md5 `e69cbbaac514182545e23513720a20a8`):
- the 62-file set (md5 `2a6a8c93…`, which already holds `test_retry_seam.py`, both round-4 files and the 13d/13b files);
- ∪ AST covering scan `scratchpad/cover_r6.py` over every changed symbol (`logging_setup` names incl. the import, `_fault_line`, `_cli_logging`, `_set_columns`, `_not_supported`, `_MIGRATING_TABLES`, `GovernedStatementError`, `rows_of`, `_as_rows`, the 6 KeepStore read methods, both old default-noun strings);
- that adds `test_am37_13_3_63c_i_a.py`, `test_caplog_isolation.py`, `test_logging_setup.py` and `test_secret_leak_vectors.py`;
- no test pins either old default-noun text.

**Gate and tree:** `gated_run.sh`, now narrowed to LORE pytest per the brief (`/[p]ytest/ && /lore/`), MemAvailable ≥ 20 GiB, `MemoryMax=16G`, `-n 8`, `--timeout=300`. Base and build ran in ONE tree:
- BASE = full6 (bec29190 production restored from `pre-r6/`; the tree diff hashed to `ca459825` before launch);
- BUILD = this build (`build-r6/` restored; md5s below).

| run | admitted | result |
|---|---|---|
| BASE `r6-base.log` | `02:18:23 avail=25GiB others=0` | `399 failed, 4978 passed, 3 skipped` in 586.5s |
| BUILD `r6-build.log` | `02:28:23 avail=37GiB others=0` | `268 failed, 5109 passed, 3 skipped` in 654.0s |

- **GREEN→RED: 0.**
- **RED→GREEN: 131, = round 6's declared 131 exactly** (`…39327f47…/r6.declared2.txt`; all 131 red at base, 0 red at build).
- **Remaining 268 reds byte-identical to round 5's** (`diff` of sorted id lists vs `r5-declared.log`: identical). The files and counts are the owned set: `packet-58-contract` 33, `packet-64b-i-contract` 235. **ZERO unowned.**
- Parsing note: 2 lines in the base log start with `ERROR ` but are captured LOG records, not node ids; they are excluded by the path filter.

### Currency (`--currency --legs typecheck,ruff`, ~02:31Z, on the build; `scratchpad/currency-r6.log`)
```
  typecheck    RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract (owner: packet 58 (…)
  ruff         GREEN
  pytest       NOT_RUN — claimed by the manifest, never executed
CURRENCY   : FAIL — claimed but never run: pytest
```
- typecheck 83 is unchanged and RED_ORPHANED on the run legs is 0.
- Exit 1 is the known FLAG-2 residual.
- `uv run ruff check .` → `All checks passed!`

### Patches

| artifact | md5 |
|---|---|
| **FINAL 63c-i-a patch** `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/9744862d-d833-4a43-b77a-bdbeb70a77d0/scratchpad/builder-63c-i-a-fix6.r6.full.patch` (24 files: `git diff --binary HEAD` + `--no-index` for the 3 untracked test files) | `30a13c8ab5b409460d1943256469fcd4` |
| delta over bec29190 `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/9744862d-d833-4a43-b77a-bdbeb70a77d0/scratchpad/builder-63c-i-a-fix6.r6.delta.patch` (8 files: 5 production + the 3 r6 test files) | `868d7ab5adcffbc6d62c48a00d671387` |
| `loremaster/loremaster/principals.py` | `ce5dbc3e94975df280333b925a0f670e` |
| `loremaster/loremaster/governed.py` | `e1286994f7e16be91c05ff6f3e09efc9` |
| `loremaster/loremaster/principal_keys.py` | `d2d80884877ea7b043be2ede2be5af41` |
| `loremaster/loremaster/keeps.py` | `6afced24f8da2f58b9943ea13d6b3d73` |
| `loremaster/loremaster/logging_setup.py` | `e591361fd2c838430cf4e784f9e87603` |
| `docs/reference/surrealdb-31-capabilities.md` (unchanged) | `73487207fdf0aefe0a070c24f5160754` |

- `git apply --check --cached <r6.full.patch>` at main HEAD **`3d29e7c`: OK**. Main moved by docs only since the scratch base `365f769` (`git diff --stat 365f769 HEAD -- loremaster scripts docs/reference`: empty).
- The delta, applied over a FRESH bec29190 reconstruction (`recon-r6-check`: HEAD archive + `r5.full.patch`), reproduces all 24 files byte-exact (`cmp`: 0 mismatches).
- `cp -a` of the changed files: `scratchpad/changed-files-r6/`.

### Retired-name sweep (bare patterns)
- `_scrub_text`: production 0, tests 0 (test_secret_leak_vectors' own wrapper is `scrub_text`).
- 16 hits in archived receipts:
  - `docs/plans/v2/receipts/2026-07-31-packet39/REPORT-adversary-39-auth-1.md:269,599`
  - `…/2026-07-26-packet42/REPORT-refactor-pkt42-1.md:113,199`
  - `REPORT-contract-pkt42-1.md:1061,1114,1163,1263`
  - `REPORT-builder-pkt42-1-pass4.md:67,135,185,201,206`
  - `REPORT-builder-pkt42-1.md:145,175,655,657`
  - Each hit is **historical**: an archived receipt, not a served surface, and not edited.
- `_SET_CLAUSE_START` / `_SET_CLAUSE_END`: 0 hits.
- `_MIGRATING_TABLES` is new.

### Residuals and observations (for the operator; none re-opened)
- OPEN FORK item 4 vs restore (above).
- FLAG-r6-1: full6 omits the 2 round-4 test files.
- The record-id redaction side effect on the CLI sink (above).
- N-1/N-2/N-3: ruled residuals, untouched.
- **ONE-IMPLEMENTATION observation:** six other stores carry their OWN private `_as_rows` (`agents`, `briefs`, `diff`, `findings`, `messages`, `tasks`) that do NOT route through `rows_of`. They are outside §13.3's ruled domain (the pin scopes to `rows_of`-delegating wrappers). Raised, not touched.

## RESUME 3 (lead, 2026-10-01 — am-37 §13.4 `86d18ba` + §13.4.1 `175077a` + §13.4.2 `d0502c0`; item-4 fork RULED option B, derived; LEAD RULING R7b-1)
Work happened in the same `fix6` scratch tree, starting at 30a13c8a.

**Summary:**
- **State:** done.
- **Tests:** 0 GREEN→RED vs full7b.
  - All 13 round 7 + 7b declared ids leave red.
  - The 9 concrete ids PASSED (`-rA` receipt).
  - The 4 collection-placeholder ids (`[<… does not exist>]`) re-keyed to 18 real-member cases, all PASSED.
  - The remaining 268 reds are byte-identical to round 5's owned set, so **0 unowned**.
- **Gates:** typecheck RED_ADJUDICATED 83 (unchanged); ruff GREEN; `ruff check .` clean.
- **Dependency direction:** no `loremaster/` import of `scripts` or `restore_prod_dump` (awk: 0 lines; the round-7 AST pin is green per module).
- **The restore's slice is IDENTICAL** to the pre-r7 script's (names, provenance, required, `governed_node`); only the reason prose is now derived from the entries.

### Setup receipts
- `cp -a` FIRST, to `scratchpad/pre-r7/`: governed, principals, principal_keys, keeps, logging_setup, `store/surreal_schema.py` AND `scripts/restore_prod_dump.py` (md5 `894543ac…`).
  - Only governed, principals and `restore_prod_dump.py` were edited.
  - The round-2 `keeps.py` slip did not recur.
- r7b test delta: md5 `04d9c8d4d7708b69d662dc4b7e0d519d` verified; apply clean. It touches `test_am37_13_3_63c_i_a.py` and `test_am37_13_4_63c_i_a.py`.
- **Tree == full7b, built in a TEMP INDEX** (`GIT_INDEX_FILE` → `git read-tree HEAD`, `git add -A`, `git diff --cached --binary HEAD`): md5 **`fdae25e8feed0e9513c722efc73a5bbb`** = full7b, 25 files.

### Build

| item | edit |
|---|---|
| THE property | `governed.governed_node_tables_of(ddl)`: a table is governed iff `ddl` defines EVERY triple column on it. The triple comes from `surreal_schema._governed_field_specs()`, the one emitter, so no names are restated. It is a pure function over DDL text, so the script's synthetic-DDL and per-dump shape questions call the SAME implementation. |
| DDL-derived set | `ddl_governed_tables()` (`functools.cache`; `cache_clear` re-derives) = the property over EVERY `surreal_schema` function named `generate_*_ddl`. These are found by `inspect.getmembers` at call time; the naming contract is the membership rule, so the round-7b synthetic-generator control is seen. `dim` is passed when present (`_DERIVATION_DIM`; the triple is width-independent), and any other required parameter RAISES (fail closed). Today: `agent`, `memory`, `message`. |
| pending set | `PENDING_GOVERNED_TABLES: Mapping[str, PendingGoverned]` (read-only `MappingProxyType`), MOVED from the script. Each entry carries `reason` + `owning_packet`: `brief` 63c-ii, `finding` 64b, `task` 64a. It is self-destructing: the round-7b pin reds by member. |
| governed set | `governed_tables()` = DDL-derived ∪ pending keys = the REPORT domain (6 tables). |
| ONE validator | `validate_governed_table(table, *, domain, verb)` raises `GovernedTableRefusedError(ValueError)`: *"`<verb>` does not support table '<t>' — its tables are `a`, `b`, …"* (domain sorted, derived). Three callers: `report_unmigrated_governed_rows` (governed domain, before any I/O); `_dispatch_report_unmigrated` (governed domain, before any store is built — the refusal goes to the ONE lore-adm handler, exit 1); and migrate through `principals._migrate_table_refusal` (domain `_MIGRATE_VALID_TABLES`, used by `migrate_governed` AND `_dispatch_migrate_governed`). `_is_governed_table` is RETIRED (awk: 0 hits). |
| R7b-1 | `brief` STAYS in `_MIGRATE_VALID_TABLES` and its teaching refusal stands. The containment pin reads the LEG set ⊆ DDL-derived set. |
| remedy (§13.4.2 rider) | PENDING → *"`<t>` has no governed columns yet (<reason>; packet <owning_packet>) — N row(s) will be scoped by that packet's migration"*. A leg table → `run lore-adm migrate-governed --table <t>`. Else → "no migrate verb accepts `<t>` yet". It never names a refusing verb. |
| derived migrate prose | `_not_supported` takes its packet text from the pending entries (`_backfill_lands`): *"its backfill lands at packet 63c-ii"*. Its invalid-name text is the validator's own refusal plus the legless notes. The hand-written "63c-ii" / "task/finding land at 64" are gone. |
| report `--table` help | `_report_table_help_domain()` is derived: the migrate set in its order, then the other governed tables → `one of: agent, memory, message, brief, finding, task`. ⚠ **FLAG-r7-1:** the F-15 pin `test_the_table_help_is_derived_from_the_valid_set` asserts the substring `", ".join(_MIGRATE_VALID_TABLES)` for BOTH verbs. That certifies the OLD single-domain world, so the help must list the migrate set first to stay green; a sorted list would red it. The help is complete and true, but its ORDER is pinned by an old-world test. |
| scripts → loremaster | `SliceDeriver` CONSUMES `loremaster.governed` (lazy import, the script's existing idiom). Node tables come from `ddl_governed_tables()` (default) or `governed_node_tables_of(emitted_ddl)` (override). Pending comes from `PENDING_GOVERNED_TABLES` (its reason renders `<reason> (packet <p>)`). `is_governed_shape` uses `governed_node_tables_of`. Relations come from the test tree's `governed_relation_tables` over the emitted DDL, as before. The script's local `PENDING_GOVERNED_TABLES` is DELETED, and its module docstring is rewritten to the new direction. |

**Removed-behaviour inventory (the script):**
- **Slice derivation** — preserved-with-pin. The default slice was compared to the pre-r7 script in-process: **IDENTICAL** over `(name, provenance, required, governed_node)`. Derived: `agent, briefed, memory, message, to`. Pending: `brief, finding, task`. Relation: `blocks`. Plus the same 6 dependencies.
- **Synthetic `zeta` growth leg** — still grows the slice (checked).
- **Pending `reason` prose** — changed deliberately (derived from the entry; same facts).
- **`_contract.governed_node_tables` / `governed_populations` for NODES** — replaced by the package property: ONE implementation.

### Targeted run
**Declared set:** 68 files, written BEFORE any run (`scratchpad/declared-r7.txt`, md5 `94b9a83881d244dafdd6ecef1fa85fd1`):
- the 66-file r6 set (holds `test_retry_seam.py`);
- `test_am37_13_4_63c_i_a.py` (the 13_3 file is already in);
- `scripts/test_restore_prod_dump.py` (BY HAND — `lore_impact` cannot see scripts, #507).

AST covering scan (`scratchpad/cover_r7.py`) over every new or changed symbol: it also hit `test_cli.py`, `test_indexer.py` and `test_scout.py`. Each matched ONLY the name `build_parser` of its OWN module's parser, not `principals.build_parser`, so all three are excluded as name collisions.

**Gate and tree:** `gated_run.sh` (lore-only, ≥ 20 GiB, `MemoryMax=16G`, `-n 8`, `--timeout=300`). It now also accepts a `scripts/` path as given. ONE tree:
- BASE = full7b (pre-r7 production restored; the temp-index diff = `fdae25e8` before launch);
- BUILD = the `build-r7/` files restored.

| run | admitted | result |
|---|---|---|
| BASE `r7-base.log` | `03:15:18 avail=35GiB others=0` | `281 failed, 5199 passed, 3 skipped` in 532.2s |
| BUILD `r7-build.log` | `03:24:21 avail=29GiB others=0` | `268 failed, 5226 passed, 3 skipped` in 517.4s |
| BUILD `-rA` over the two am-37 files `r7-build-ra.log` | `≈03:33` | `190 passed`, exit 0 (one `ERROR`-prefixed line is a captured `principal_key.query.rejected` LOG record from the §13.3 end-to-end scrub test, not a test error) |

- **GREEN→RED: 0.**
- Base: all 13 declared ids (`…39327f47…/r7.declared.txt` ∪ `r7b.declared.txt`) are red, and the other 268 = r5's owned set.
- Build: 0 declared ids red; 9/9 concrete ids `PASSED`. The 4 placeholder ids re-key to:
  - `test_the_report_count_accepts_every_governed_table[agent|brief|finding|memory|message|task]`
  - `test_the_remedy_names_a_migrating_verb_or_none[…same 6]`
  - `test_each_entry_carries_a_reason_and_an_owning_packet[brief|finding|task]`
  - `test_a_pending_table_has_no_ddl_triple_yet[brief|finding|task]`
  - all PASSED.
- **The remaining 268 reds are byte-identical to round 5's owned set** (58: 33, 64b-i: 235). **ZERO unowned.**

### Currency (`--currency --legs typecheck,ruff`, on the build; `scratchpad/currency-r7.log`)
```
  typecheck    RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract (…)
  ruff         GREEN
  pytest       NOT_RUN — claimed by the manifest, never executed
CURRENCY   : FAIL — claimed but never run: pytest
```
- typecheck 83 is unchanged and RED_ORPHANED on the run legs is 0.
- Exit 1 is the known FLAG-2 residual.
- `uv run ruff check .` → `All checks passed!`

### Patches (cut in a TEMP INDEX)

| artifact | md5 |
|---|---|
| **FINAL 63c-i-a patch** `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/9744862d-d833-4a43-b77a-bdbeb70a77d0/scratchpad/builder-63c-i-a-fix6.r7.full.patch` (26 files) | `b15c06b054e661ae9c591d1151ddc257` |
| delta over 30a13c8a `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/9744862d-d833-4a43-b77a-bdbeb70a77d0/scratchpad/builder-63c-i-a-fix6.r7.delta.patch` (5 files: governed, principals, `scripts/restore_prod_dump.py`, the 2 am-37 test files) | `5959fa0e670a09ca6a03fe3b8fa458a4` |
| `loremaster/loremaster/governed.py` | `5d1f7e926f7ed714f258f7e21d78af1d` |
| `loremaster/loremaster/principals.py` | `6b9ed20d6cec9a6c44c3f3c7b10c3b04` |
| `scripts/restore_prod_dump.py` | `b887aca293b115ebb71cd03c8c39b226` |
| principal_keys / keeps / logging_setup / the store reference (unchanged since r6) | `d2d80884…` / `6afced24…` / `e591361f…` / `73487207…` |

- **File list vs full7b:** ⊇ holds — **0 of full7b's 25 missing**. The one addition is `scripts/restore_prod_dump.py`.
- The delta, applied over a FRESH 30a13c8a reconstruction (`recon-r7-check`: HEAD archive + `r6.full.patch`), reproduces all 26 files byte-exact (`cmp`: 0 mismatches).
- `git apply --check --cached <r7.full.patch>` at main HEAD **`2e8b0e0`: OK**. Main moved by docs only since `365f769`.
- `cp -a` of the changed files: `scratchpad/changed-files-r7/`.

### Residuals and observations
- FLAG-r7-1: the F-15 help pin certifies the old one-domain world via a substring (above).
- The `else` remedy branch ("no migrate verb accepts") is unreachable today, since every DDL-derived table has a leg. It is kept as the honest answer for a future derived table without a leg.
- The relation-table derivation (`governed_relation_tables`) still lives in the test tree and is called by the script. Only the NODE property moved into the package, as ruled.
- Earlier-round residuals stand as listed in §RESUME 2.
