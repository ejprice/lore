# REPORT-scout-4849-60 — packet 48/49 shape map for packet 60 (the Keep substrate)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done
- **Capability check:** full — lore tools loaded, index fresh (sweep 152s old at read; watched root `/workspace` @ `feat/surreal-unification` `4945ab4`, matches my tree). No reconcile needed.
- **Deviations:** none. I did NOT read packet 60's own spec (none found in `docs/plans/v2/` or `docs/design/`; INDEX has no clear "Keep"/pkt-60 row) — out of my mission (map 48/49). GOTCHAS are framed generically for "the edge-based model" the brief describes; the lead holds the pkt-60 spec.
- **Packages considered:** none — no mechanism specified (read-only scout).
- **Reuse ledger:** none — no new symbols (read-only scout).
- **Graded:** N/A — this is a source map, not a verdict on someone's artifact. All pointers taken at `4945ab4`.
- **Fallbacks to grep (SAID OUT LOUD):** module CONSTANTS (`_PRINCIPAL_FIELD_SPECS`, `KNOWN_RELATION_EDGES`, `_CLI_PROG`) and the generate_ddl FOLD lines are non-symbol textual seams / cross-cutting maps — `lore_get_symbol` is chunk-scoped to class/method/function so it can't resolve module-level tuples; grep is the honest tool there (CLAUDE.md dogfood §3b/c). Everything else came from lore (`lore_get_symbol`/`lore_read`/`lore_search`).
- **Decisions needed:** none for me. One design fork FLAGGED for the lead in §GOTCHAS G2 (the exact-set edge pin makes a new edge RED-by-design — declare it in the scaffold with the edge).
- **Pointers:** §1 DDL · §2 Store CRUD · §3 CLI · §4 Tests · §GOTCHAS (edge-vs-field divergences).

---

## §1 — THE DDL SLICE (`loremaster/loremaster/store/surreal_schema.py`)

### 1.1 Field specs — the `(name, type_expr, constraint)` triple format
Both are module-level `tuple[tuple[str, str, str], ...]`; `_define_field` appends `constraint`
verbatim after the type.

`_PRINCIPAL_FIELD_SPECS` (@450, the 5 NON-domain fields — status/role are NOT here):
```python
_PRINCIPAL_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("email", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    ("subject", "option<string>", _NON_EMPTY_STRING_ASSERT),   # Model B: NONE until pkt39 fills it
    ("display_name", "option<string>", ""),
    ("expires_at", "option<datetime>", ""),
    ("created_at", "datetime", "DEFAULT time::now()"),          # store OMITS on write, engine stamps
)
```
`_PRINCIPAL_KEY_FIELD_SPECS` (@1877 — note the **`record<principal>` link column**):
```python
_PRINCIPAL_KEY_FIELD_SPECS: tuple[tuple[str, str, str], ...] = (
    ("hash", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    ("name", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),
    ("principal", f"record<{PRINCIPAL_TABLE}>", ""),           # REQUIRED owner link (new empty table → not option<>)
    ("created_at", "datetime", "DEFAULT time::now()"),
    ("expires_at", "option<datetime>", ""),                    # NO DEFAULT — "IS NONE is live" predicate
    ("revoked_at", "option<datetime>", ""),                    # NO DEFAULT — WHERE revoked_at IS NONE = active
)
```
Shared type/assert constants: `_CHUNK_STRING_TYPE` (= `string`), `_NON_EMPTY_STRING_ASSERT`.
Table-name single-source constants: `PRINCIPAL_TABLE = "principal"` (@127), `PRINCIPAL_KEY_TABLE = "principal_key"` (@137).

### 1.2 The statement assemblers
`_principal_statements()` (@1387) and `_principal_key_statements()` (@1887) each build:
`[_define_table(T)]` + one `_define_field(T, n, ty, constraint=c)` per spec + the UNIQUE indexes.

`_principal_statements` (@1387) also DERIVES the closed-domain `status`/`role` field-defs AT CALL TIME
(not frozen constants — the `_floor_measurement_statements` idiom, so a mutation-pin monkeypatching the
vocab tuple moves the emitted ASSERT — mutation-provable):
```python
status_allowed = ", ".join(f"'{s}'" for s in _PRINCIPAL_STATUSES)   # @1408
role_allowed = ", ".join(f"'{r}'" for r in _PRINCIPAL_ROLES)
domain_specs = (
    ("status", _CHUNK_STRING_TYPE, f"DEFAULT '{_PRINCIPAL_STATUS_ACTIVE}' ASSERT $value IN [{status_allowed}]"),
    ("role",   _CHUNK_STRING_TYPE, f"DEFAULT '{_PRINCIPAL_ROLE_MEMBER}' ASSERT $value IN [{role_allowed}]"),
)
statements = [_define_table(PRINCIPAL_TABLE)]
statements += [_define_field(PRINCIPAL_TABLE, n, ty, constraint=c) for n, ty, c in (*_PRINCIPAL_FIELD_SPECS, *domain_specs)]
statements.append(_unique_index(PRINCIPAL_TABLE, f"{PRINCIPAL_TABLE}_email", ("email",)))
statements.append(_unique_index(PRINCIPAL_TABLE, f"{PRINCIPAL_TABLE}_subject", ("subject",)))
```
Domain enums (@431-437): `_PRINCIPAL_STATUSES = (active, suspended)`, `_PRINCIPAL_ROLES = (member, admin)`,
with `_PRINCIPAL_STATUS_ACTIVE`/`_PRINCIPAL_ROLE_MEMBER` as the defaults. The comment @420-438 is the
canonical note: these are principal-SPECIFIC vocabularies (≠ `agent.status`), derived at call time.

`_principal_key_statements` (@1887): table + fields (through shared `_define_field`) + UNIQUE `hash` index +
UNIQUE composite `(principal, name)` index. Both indexes are plain UNIQUE over REQUIRED columns (no `option<>` span).

### 1.3 The DDL-clause helpers (the emitters every slice routes through)
- `_define_table(name)` (@920) → `DEFINE TABLE IF NOT EXISTS {name} SCHEMAFULL`
- `_define_field(table, name, type_expr, *, constraint="")` (@985) → **`DEFINE FIELD OVERWRITE {name} ON {table} TYPE {type}{ " "+constraint}`**. ⚠ **OVERWRITE, not IF NOT EXISTS** — finding #107 (100% `brief_publish` outage): `IF NOT EXISTS` on an existing field is a silent no-op, so a def change never migrates a live store. Docstring explicitly says do NOT flip this on table/index/analyzer.
- `_unique_index(table, name, fields)` (@1044) → `DEFINE INDEX IF NOT EXISTS {name} ON {table} FIELDS {...} UNIQUE`
- `_plain_index(...)` — non-unique index (used by agent slice; available if pkt60 wants a status index)

### 1.4 The `generate_*` slice functions
- `generate_principal_ddl() -> str` (@1824) → `";\n".join(_principal_statements()) + ";\n"`. Applied by `PrincipalStore.ensure_ready` on its OWN connection; needs NO `dim`/analyzer.
- `generate_principal_key_ddl() -> str` (@1925) → `";\n".join(_principal_key_statements()) + ";\n"`. Applied by `PrincipalKeyStore.ensure_ready`.
Both return newline-joined, semicolon-terminated DDL for one `query()`/`BEGIN…COMMIT`.

### 1.5 The FOLD into `generate_ddl` (@1690) — VERBATIM (@1721-1722)
`generate_ddl(*, dim: int, analyzer_name: str = DEFAULT_ANALYZER_NAME) -> str` accumulates `statements`; the fold lines:
```python
    statements += _finding_statements()
    statements += _finding_counter_statements()
    statements += _principal_statements()        # @1721
    statements += _principal_key_statements()    # @1722  — AFTER principal: its record<> link target
```
This "Variant A" fold means the PRIMARY `write_store.ensure_ready()` gains the table the moment the packet
ships (the #131 dirty-store class the fold-pin guards). **Ordering rule: a slice with a `record<X>` link (or an
edge `IN X`) is folded AFTER `X`'s slice** — `principal_key` after `principal`, exactly the `briefed`→`agent` rule.

### 1.6 ⭐ THE RELATION-EDGE PRECEDENT packet 60 mirrors (NOT present in 48/49's own tables)
48/49 use FIELD LINKS only. The edge precedent lives elsewhere in the SAME module:

**`_define_relation_table(name, in_table, out_table, *, enforced=False)` (@925)** — the edge-table emitter:
```python
enforced_clause = " ENFORCED" if enforced else ""
return f"DEFINE TABLE OVERWRITE {name} TYPE RELATION IN {in_table} OUT {out_table}{enforced_clause} SCHEMAFULL"
```
⚠ **OVERWRITE** (store ref §1.1 RELATION-TABLE row): `IF NOT EXISTS` on an existing edge table is a MEASURED
silent no-op (#107's shape). `IN/OUT` type the endpoints (without them an edge accepts ANY table). `enforced=True`
adds `ENFORCED` — validates BOTH endpoints reference EXISTING records; the only guard that closes the
`INSERT RELATION` door no app check reaches (store ref §4).

**`_briefed_statements()` (@1484)** — the cleanest "edge table WITH an edge-local FIELD" precedent
(`briefed` = `agent`→`brief`, and it is the FIRST relation with a UNIQUE(in,out) index):
```python
statements = [_define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, enforced=True)]
statements += [_define_field(BRIEFED_RELATION, n, ty, constraint=c) for n, ty, c in _BRIEFED_FIELD_SPECS]
statements.append(_unique_index(BRIEFED_RELATION, f"{BRIEFED_RELATION}_in_out", _BRIEFED_IN_OUT_INDEX_FIELDS))
```
Edge-field specs `_BRIEFED_FIELD_SPECS` (@598) — the closed-vocab edge property idiom (like `via`/`at`):
```python
_BRIEFED_FIELD_SPECS = (
    ("via", _CHUNK_STRING_TYPE, f"ASSERT $value IN [{_BRIEFED_VIA_ALLOWED}]"),
    ("at",  "datetime", "DEFAULT time::now()"),
)
_BRIEFED_IN_OUT_INDEX_FIELDS = ("in", "out")   # `in`/`out` auto-defined by TYPE RELATION — NEVER hand-declared
```
Other edges emitted the same way (all via `_define_relation_table`): `blocks` (task→task, @1336),
`to` (message→agent, @1604), `refers` / `answers_to` (code_node→name, @1663/1678). The `briefed`/`blocks`
edges are folded into their bigger slices (`_agent_brief_message_statements` @1988; task slice @2041 area).

---

## §2 — THE STORE CRUD CLASSES

### 2.1 Construction & lifecycle (both classes are near-identical; `PrincipalKeyStore` clones `PrincipalStore` verbatim)
- `PrincipalStore` (`principals.py` @206); `PrincipalKeyStore` (`principal_keys.py` @181).
- `__init__(*, url, namespace, database, user, password: SecretStr)` (@223 / @200) — stores wiring, opens NO connection. Lazy `self._connection=None` + `self._connect_lock = asyncio.Lock()` (double-checked locking cloned from `FindingLedger`).
- `_ensure_connection() -> _SurrealConnection` (@246 / @230) — fast path lock-free; on first use `AsyncSurreal(url)` → `signin(signin_credentials(...))` → **`bootstrap_session(connection, ns, db, url=)`** (the ONE shared bootstrap). Any fault (transport OR `TxnContentionExhaustedError`) → close half-open socket → wrap as `SurrealConnectionError`.
- `ensure_ready() -> None` (@294 / @278) — `await self._ensure_connection()`; then `generate_principal_ddl()` (resp. `_key_ddl`) wrapped `BEGIN;\n{ddl}COMMIT;\n` through **`execute_transaction(sql, {}, acquire=self._ensure_connection, drop=self._drop_connection, url=self._url)`** (verifies EVERY statement's status, unlike SDK `query()`). Idempotent (IF NOT EXISTS tables/indexes; OVERWRITE fields). `PrincipalKeyStore.ensure_ready` applies ONLY the key slice on its own connection.
- `close()` / `_drop_connection()` (CAS self-heal) / `_safe_close()` — standard lifecycle, cloned.

### 2.2 The retry/driver seam — routed, NOT hand-rolled (#102/#120)
`_query(statement, params=None) -> Any` (@347 / @338) delegates to the ONE shared attempt body:
```python
return await run_query(
    acquire=self._ensure_connection, drop=self._drop_connection, url=self._url,
    noun="principal query", label="principal.query.rejected",
    statement=statement, params=params or {}, logger=logger)
```
All three seams — `run_query`, `execute_transaction`, `bootstrap_session` — are from **`loremaster.store._txn`**.
The stores introduce NO retry/backoff/classification of their own. The `_query` name is AUTO-DISCOVERED by
`test_retry_seam.py`'s `_query` scan, so the shared retry/backoff/exhaustion pins prove the sharing by mutation.

### 2.3 Public CRUD surface (signatures + returns)
**PrincipalStore** (all `async`, keyword-only where shown):
- `create(*, email, subject=None, role=None, display_name=None, expires_at=None) -> Principal` (@369)
- `get_by_subject(subject) -> Principal | None` (@440); `get_by_email(email) -> Principal | None` (@455)
- `list() -> _PrincipalList` (@469)  ⚠ shadows builtin `list` (module aliases `_RowList`/`_PrincipalList` @199 exist because of this)
- `set_status(*, email, status) -> Principal` (@485); `set_subject(*, email, subject) -> Principal` (@520); `set_expires(*, email, expires_at) -> Principal` (@564)
- `delete(*, email) -> int` (@606) — returns cascaded-key count
- private mappers: `_row_to_principal` (@669), `_to_aware_utc` (@721, the SHARED datetime coercion), `_require_aware_utc` (@702)

**PrincipalKeyStore** (all `async`):
- `mint(*, email, name, secret_hash, expires_at=None) -> PrincipalKey` (@363)
- `list_for(*, email) -> list[PrincipalKey]` (@430)
- `revoke(*, email, name) -> PrincipalKey` (@456)
- `verify(presented) -> KeyVerification | None` (@494, `# noqa: PLR0911`) — the auth path; `_deny(reason)` (@565) launders denial reasons
- `_require_principal_id(email) -> str` (@573) — resolves owner via the owned `PrincipalStore.get_by_email` (shared mapper, never cloned); returns the BARE id via `_record_id_part` (@614, `principal:xyz` → `xyz`)

### 2.4 How writes are done — CONTENT, bound params, NO RELATE (⚠ the key divergence)
`create` (@369) body — `CREATE … CONTENT $content RETURN AFTER`, building `content` dict only with PROVIDED cols
(an omitted `option<>` → NONE, omitted defaulted col → DDL DEFAULT):
```python
content = {_COL_EMAIL: email}
if subject is not None: content[_COL_SUBJECT] = subject
# ... role / display_name / expires_at only if provided
result = await self._query(f"CREATE {PRINCIPAL_TABLE} CONTENT $content RETURN AFTER", {"content": content})
```
`mint` (@363) binds the OWNER LINK as a RecordID (store law §2/§4 — a bare id string may not coerce):
```python
fragments = [f"{_COL_PRINCIPAL}: type::record('{PRINCIPAL_TABLE}', $pid)", f"{_COL_HASH}: $hash", f"{_COL_NAME}: $name"]
params = {"pid": principal_id, "hash": secret_hash, "name": name}   # principal_id = bare id from _require_principal_id
statement = f"CREATE {PRINCIPAL_KEY_TABLE} CONTENT {{ {', '.join(fragments)} }} RETURN AFTER"
```
**48/49 NEVER use `RELATE`.** The `principal_key.principal` owner is a `record<principal>` FIELD LINK, written via
`type::record('principal', $pid)` inside a CONTENT create. No edge table, no `->…->` traversal.

### 2.5 Typed errors & pydantic boundary models
- Errors (`principals.py`): `PrincipalStoreError(RuntimeError)` (@190) / `PrincipalNotFoundError(PrincipalStoreError)` (@194). (`principal_keys.py`): `PrincipalKeyStoreError(RuntimeError)` (@173) / `PrincipalKeyNotFoundError(PrincipalKeyStoreError)` (@177). Convention: transport faults (`SurrealConnectionError`/`TxnContentionExhaustedError`) propagate UNTOUCHED; a `SurrealStoreError` from a UNIQUE backstop is re-wrapped LOUD as the domain error (Consumer Law — never a raw engine error, never silent).
- Models (all `model_config = ConfigDict(extra="forbid", frozen=True)`):
  - `Principal` (@162): `id, email, subject: str|None, display_name: str|None, status, role, expires_at: datetime|None, created_at: datetime`
  - `PrincipalKey` (@135): `id, principal_id: str, name, created_at, expires_at: datetime|None, revoked_at: datetime|None`
  - `KeyVerification` (@158): `principal: Principal, key_name: str` — carries the FULL resolved owner (not a string) so pkt39 mints a per-principal AccessToken.

---

## §3 — THE `lore-adm` CLI (`loremaster/loremaster/principals.py`, packet 49)

`[project.scripts] lore-adm = "loremaster.principals:main"`. `_CLI_PROG = "lore-adm"` (@768).

### 3.1 Structure — argparse subparsers, 9 verbs, dict-dispatch
`build_parser() -> argparse.ArgumentParser` (@857): `prog=lore-adm`; one global `--config` (path to `lore.yaml`);
`subcommands = parser.add_subparsers(dest="command", required=True)`. Local helper `_with_email(name, help)`
adds a subparser with a required `--email`. **NO `--execute` flag, NO dry-run — every verb executes directly**
(operator ruling 2026-08-20). The nine verbs:

| verb | extra args | handler |
|------|-----------|---------|
| `add` | `--display-name`, `--role {member,admin}`, `--expires` | `_cmd_add` |
| `list` | (none — read) | `_cmd_list` |
| `delete` | — | `_cmd_delete` |
| `suspend` / `unsuspend` | — | `_cmd_suspend` / `_cmd_unsuspend` |
| `set-expiry` | mutually-exclusive `--at` \| `--clear` (required) | `_cmd_set_expiry` |
| `mint-key` | `--name` (req), `--expires` | `_cmd_mint_key` |
| `revoke-key` | `--name` (req) | `_cmd_revoke_key` |
| `list-keys` | (read) | `_cmd_list_keys` |

Handlers share signature `(args, principal_store, key_store) -> int`, registered in `_VERB_HANDLERS` dict.

### 3.2 Output idiom — Unix silent-on-success / loud-on-failure
- Mutating verbs print NOTHING on success and return 0 (`add`/`suspend`/`set-expiry`/`revoke-key`).
- Reads print one line per row via SHARED sanitiser: `_render_principal_line` (@801) / `_render_key_line` (@824) route free-text (`email`/`display_name`/`name`) through **`loremaster.sanitise.safe_str`** (P8d rendered-free-text law — a survived newline collapses to a space, cannot forge a phantom row).
- `mint-key` (@1023 `_cmd_mint_key`): mints `secret = secrets.token_urlsafe(_SECRET_ENTROPY_BYTES=32)`, `credential = f"{name}:{secret}"`, stores only `sha512_hex(credential)`, and `print(credential)` — **the one time the raw secret is ever emitted**.
- `delete` prints `deleted {email} ({n} key(s) removed)`.
- Failures: `_dispatch` (@~1015) catches `(PrincipalStoreError, PrincipalKeyStoreError, SurrealConnectionError, ValueError)` → `print(f"{_CLI_PROG}: {error}", file=sys.stderr)` → `return 1`.

### 3.3 Store construction + config/secret resolution (CREDS-FREE)
`_dispatch(args)` (@~1015): lazy-imports `build_principal_key_store` (cycle: `principal_keys` imports `principals`);
`config = load_surreal_only_config(_require_config(args))`; builds BOTH stores; **readies principal FIRST then key**
(link-target order); dispatches; `finally` closes both (key then principal).

- `build_principal_store(config) -> PrincipalStore` (@839): reads `config.surreal.{url,namespace,user_env,password_env}` + `config.effective_surreal_database` (MINUS `dim`), user via `resolve_config_value(config.surreal.user_env)`, password via `resolve_secret(config.surreal.password_env)` — the exact `store.surreal.build_store` accessors.
- `build_principal_key_store(config)` (`principal_keys.py` @629) — sibling factory.
- **Creds-free**: `load_surreal_only_config` (`config.py` @957) reads ONLY the surreal coordinate — the CLI runs with NO Anthropic key set (pinned by `test_principals_cli.py::TestCredsFreeConfigResolution`, and it does NOT call `load_config`). `--role member|admin` uses `choices=list(_PRINCIPAL_ROLES)`.
- `main(argv=None) -> int` (@1053): `args = build_parser().parse_args(argv); return asyncio.run(_dispatch(args))`. Guarded by `if __name__ == "__main__": raise SystemExit(main())`. Helpers: `_require_config` (@779, loud SystemExit if `--config` absent), `_parse_instant` (@787, ISO→tz-aware UTC), `_render_instant` (@796).

---

## §4 — THE TESTS

### 4.1 Test files (48/49)
- `tests/test_principals_schema.py` — principal DDL + live round-trip (classes: `TestThePrincipalDdlDecisionRuleIsEnforcedMechanically` @208, `TestThePrincipalClosedDomainsAreDerivedIntoTheDdl` @352, `TestThePrincipalSchemaAppliesToTheLiveEngine` @455, `TestThePrincipalRoundTrip` @478).
- `tests/test_principal_keys_schema.py` — key DDL + migration leg.
- `tests/test_principals_store.py`, `tests/test_principal_keys_store.py` — store CRUD.
- `tests/test_principals_cli.py` — the `lore-adm` CLI.
- `tests/test_oauth_identity_seam.py` — the pkt39 boundary.

### 4.2 The dirty-store migration idiom (OLD DDL → row → NEW DDL → assert)
**Canonical home: `tests/test_surreal_store.py::TestSchemaMigrationAgainstAnExistingStore` (@4861).** The packet-48
principal leg is @5499-5610. It uses a `migration_db` fixture `(connection, env)` and `_apply_ddl(...)`, and DERIVES
narrowed/widened/legacy values from `_PRINCIPAL_STATUSES` (never hand-typed). The exact shape (@5560+):
```python
# NEW world first (table+fields exist) → OVERWRITE status to a NARROWER ASSERT (the "old" world)
#   → CREATE a legacy row legal under the narrow set  (DIRTY THE STORE)
# test: the narrow schema is really in force (widened value REJECTED now)
#   → re-apply the REAL slice (== ensure_ready) → the widened value is now ACCEPTED (migration LANDED)
# POSITIVE CONTROL (@5604): a migration that "landed" by DROPPING the ASSERT would accept everything —
#   assert the constraint is WIDER, not GONE.
```
The principals/keys schema files also carry their own `#1.6 dirty-store` legs (grep: `test_principals_schema.py:483`
points at this class; `test_comms_schema.py:2580+` is the comms analogue with the same shape).

### 4.3 The CLI test idiom (`test_principals_cli.py`)
- `_CliEnv` (@132) + `cli_env` fixture (@141): writes a real `lore.yaml` (`tmp_path`) pointed at a **per-test unique spike-store DB** (`make_env(database=unique_database(), dim=PRODUCTION_DIM)`), reaped via `drop_database(env)`. This is a LIVE store test, not a mock.
- **`_run_cli(argv)` (@155): `return await asyncio.to_thread(p_module.main, argv)`** — `main` uses `asyncio.run`, which can't be called from the test's running loop, so it runs in a worker thread (adversary FINDING 5). Mirror this exactly for pkt60 CLI tests.
- Assertions read the DB back via `connect_admin(env)` + `run(connection, "INFO FOR DB" / "SELECT …")`. ⚠ On a VIRGIN DB a `SELECT … FROM principal` RAISES on 3.2.4 (adversary FINDING 3) — helpers tolerate an absent table (`_table_names`/`_principal_emails`/`_db_snapshot` return `set()`/`[]`).
- Classes: `TestParserSurface` (@219, offline — every verb parses, source has no `--execute`), `TestSiblingStoreFactories` (@342), `TestCredsFreeConfigResolution` (@402), `TestVerbsExecuteDirectly` (@446, end-to-end `main()` against the live store), `TestMainGuardIsLast` (@303).

### 4.4 ⭐ THE EDGE / RELATE TEST PRECEDENT (what pkt60 actually mirrors for tests)
48/49 have NO edge tests (field links only). The edge test toolkit is:

**`tests/_enforced_relations_scaffold.py`** — the reusable edge-migration scaffold:
- `KNOWN_RELATION_EDGES: dict[str, (in_table, out_table)]` (@73/112) — the declared edge set. `ALL_DDL_GENERATORS` (@78) — every generator that could emit a RELATION table (the ∀ pins sweep this).
- `old_world_ddl(edge, in_table, out_table, generator)` (@199) — derives an UN-enforced OLD-world DDL from today's generator (`test_the_old_world_DIFFERS_from_todays_generator` proves it non-vacuous).
- `apply_ddl(connection, ddl, *, url)` (@175), `relate(...)` (@322), `seed_endpoint(connection, table, row_id)` (@248), `ghost_id(prefix)` (@230, a dangling endpoint), `record_exists` (@242), `edge_set_clause(edge)` (@297), `migration_db()` fixture (@345).

**`tests/test_enforced_relations.py`** — the ∀-pins every emitted edge must pass:
- `TestEveryRelationEdgeIsEnforced` (@169): `test_EVERY_relation_table_the_schema_emits_is_ENFORCED` (@185), `test_the_relation_edge_set_is_EXACTLY_the_five_known_edges` (@211, the EXACT-SET pin), `test_the_edge_carries_ENFORCED_in_its_own_slice` (@242), `test_the_edge_is_declared_OVERWRITE_never_IF_NOT_EXISTS` (@258), `test_the_edge_declares_its_IN_and_OUT_endpoint_tables` (@278).
- `TestTheEnforcedFlipMigratesADirtyStore` (@331): OLD un-enforced DDL → write ONE dangling edge → assert baseline accepts it (@382) → apply today's DDL → guard is LIVE (new dangling RELATE refused, @412) + POSITIVE CONTROL a real endpoint still accepted (@448) + **the pre-existing dangling edge SURVIVES the flip** (@487, ENFORCED is NOT retroactive) + idempotent (@526). Probes BEHAVIOUR (attempt a RELATE), never reads back a DDL string.
- `TestTheLEDGERsOwnMigrationPathLandsTheGuard` (@554): `ensure_ready` on a DIRTY store makes the guard live.

**`tests/test_blocks_edge.py`** — packet 04b-1, the closest FULL precedent for ADDING a new edge (`task->blocks->task`) with the atomic CREATE+RELATE and the "emitted by BOTH paths identically" pins (`TestTheBlocksEdgeIsEmittedByBOTHGenerationPaths` @678). Its module docstring §"WHAT THIS CONTRACT TURNS RED IN FILES IT DOES NOT OWN" (@209) is the exact playbook for the exact-set-pin RED-by-design consequence (see G2). RELATE lives inside a transaction so CREATE+RELATE are atomic; `blocks ≡ blocked_by` mirror is pinned under THE QUANTIFIER LAW.

---

## §GOTCHAS / DIVERGENCES for packet 60 (mirroring 48/49 naively is WRONG for an edge model)

**G1 — 48/49 are FIELD-LINK stores; packet 60 is a RELATE-EDGE store. Do NOT clone `_principal_key_statements`/`mint` for the relationship.**
The right template for the edge table is **`_briefed_statements()` (@1484)** + **`_define_relation_table(..., enforced=True)` (@925)**, not `_define_table`/`CREATE…CONTENT`. Write the relationship with `RELATE` (see the scaffold `relate()` helper), not `type::record(...)` inside a CONTENT create. `_principal_key_statements`/`create`/`mint` are still the right template for any NON-edge NODE table and for its CLI/store lifecycle.

**G2 — ⚠ DESIGN FORK (for the lead): a new relation edge makes `test_the_relation_edge_set_is_EXACTLY_the_five_known_edges` (test_enforced_relations.py @211) go RED, BY DESIGN.** The fix is to DECLARE the new edge in `KNOWN_RELATION_EDGES` (`_enforced_relations_scaffold.py` @73/112) — and per the packet-04b-1 precedent this is done *in the contract, before the edge exists*, so the exact-set pin is the RED forcing function (04a §6.8 "contract-in-force", not a misfire). The contract brief must:
  (a) add the edge to `KNOWN_RELATION_EDGES` with its `(in_table, out_table)`;
  (b) if pkt60 adds a NEW slice generator (`generate_keep_ddl` or similar), register it in `ALL_DDL_GENERATORS` (@78) so the ∀ ENFORCED/OVERWRITE/IN-OUT pins sweep it;
  (c) expect (and want) `test_the_edge_carries_ENFORCED_in_its_own_slice[<newedge>]`, `[…_OVERWRITE…]`, and `[…IN_and_OUT…]` to parametrise onto the new name automatically.
  This is not optional cleanup — the exact-set pin will be RED until (a) lands. Flag it in the contract brief as a "turns RED in files it does not own" consequence (the `test_blocks_edge.py` docstring @209 is the copy-paste model).

**G3 — the edge table MUST be `ENFORCED` from birth and `OVERWRITE` (never `IF NOT EXISTS`).** Every ∀ pin in `test_enforced_relations.py` requires it, and #105/#107 are why. `_define_relation_table` already emits `OVERWRITE`; pass `enforced=True`. An un-enforced edge (or an `IF NOT EXISTS` one) is a MEASURED silent no-op on a dirty store.

**G4 — an edge needs a DIRTY-STORE MIGRATION test of the EDGE-specific shape, not the field shape.** The principal migration (test_surreal_store.py @5499) narrows/widens a field ASSERT. The EDGE migration (test_enforced_relations.py @331) is different: OLD un-enforced DDL → dangling edge → NEW DDL → (a) new dangling RELATE refused, (b) real endpoints accepted, (c) **pre-existing dangling edge SURVIVES** (ENFORCED is not retroactive — pin the survival, it's the attractive-wrong belief), (d) idempotent. Use `migration_db` + `old_world_ddl` from the scaffold, and PROBE behaviour (attempt a RELATE), never read back a DDL string.

**G5 — FOLD ORDER: the edge slice folds into `generate_ddl` AFTER BOTH endpoint tables.** `principal_key` folds after `principal` because of its `record<principal>` link (@1721-22); an edge `IN A OUT B` needs BOTH `A` and `B` defined first (`briefed` after `agent`+`brief`). If pkt60's edge endpoints are `principal` and a new Keep node, fold: node-tables → edge. Also emit the edge from BOTH `generate_ddl` AND any standalone `generate_keep_ddl` IDENTICALLY (test_blocks_edge.py @678/707 pins this).

**G6 — edge-local FIELDS use the `_<EDGE>_FIELD_SPECS` const + call-time-derived ASSERT for any closed vocabulary.** Mirror `_BRIEFED_FIELD_SPECS` (@598): `in`/`out` are auto-defined by `TYPE RELATION` and NEVER hand-declared. If the edge carries a closed-vocab field (the brief's `via`-style property), DERIVE its `ASSERT $value IN [...]` at call time from a module tuple (the `_principal_statements` domain idiom @1408) so a mutation pin can move it — do NOT freeze it into a literal.

**G7 — UNIQUE(in, out) edge index is the `briefed` precedent (`_BRIEFED_IN_OUT_INDEX_FIELDS = ("in","out")` @611), the FIRST such in the codebase.** `refers`/`answers_to` do NOT have it. If pkt60's edge must be de-duplicated per endpoint-pair (idempotent re-relate), clone `briefed`'s UNIQUE(in,out); if not, follow `refers`/`blocks` (no such index — `blocks` deliberately carries NO edge-local field and NO endpoint-pair uniqueness). Decide deliberately.

**G8 — the store's atomic write: `blocks` converted `create_task` to a TRANSACTION so CREATE-node + RELATE-edge commit atomically (test_blocks_edge.py scope §, @16).** If pkt60 creates a node AND its edge in one operation, wrap them in one `execute_transaction`, not two `_query` calls — a half-written node with no edge (or vice-versa) is the hazard.

**G9 — reuse the SHARED seams, do not clone (#102/#120).** `run_query`/`execute_transaction`/`bootstrap_session` (`loremaster.store._txn`), `_to_aware_utc` datetime coercion (`PrincipalStore._to_aware_utc` @721), `safe_str` render sanitiser (`loremaster.sanitise`), `sha512_hex` (`loremaster.index.records` @108), `resolve_secret`/`resolve_config_value`/`load_surreal_only_config` (`config.py`). Name `_query` exactly `_query` so `test_retry_seam.py`'s scan auto-discovers it and the shared retry pins prove sharing by mutation.

**G10 — store-law reads first (CLAUDE.md mandatory): `docs/reference/surrealdb-31-capabilities.md` §1.1 (DDL decision rule — OVERWRITE for fields/relation-tables, IF NOT EXISTS for indexes/tables/analyzers/sequences, why ALTER is a trap), §2 (CONTENT for protected keys, `type::record`, datetimes-as-Python, missing-projection-reads-None), §4 (RELATE bound-RecordID form + the dangling-edge hazard + ENFORCED). Cite it in the contract brief as a numbered first step; the edge model touches every one of those clauses.**
