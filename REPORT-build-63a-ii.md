# REPORT-build-63a-ii — packet 63a wave 63a-ii: wire the served memory tool layer + 3 riders

- `brief-base v14 read`
- `brief project v7 read`
- store reference consulted: `docs/reference/surrealdb-31-capabilities.md` (cited, not re-transcribed) —
  §2 (record<> links / CONTENT / explicit projection reads NONE), §3 (execute_read_transaction /
  statement[0]) for the composition-root wiring, the SF-63-5 count read, and the report-unmigrated
  driver-routed read.

## SUMMARY BLOCK

- receipt: `brief-base v14 read` · `brief project v7 read`
- **state: done-with-deviations** — all 4 items built + GREEN + mutation-proved; two disclosed
  deviations (D1 a directly-caused search-test fix; D2 an adjacent pre-existing leak fixed).
- deviations (one line each):
  - **D1 (test_mcp_server, directly-caused):** FORK-D1's withheld-boost notice now appears on EVERY
    identity-less search (the designed Leg-1 behavior until 63b), so 2 search-teaching tests that
    read `notices[0]` were re-pointed to select the teaching notice BY CONTENT. §FORK-D1.
  - **D2 (server.py, adjacent pre-existing bug):** `build_app_context`'s build-FAILURE path did NOT
    close `message_ledger` (a leaked connection on a partial build). Fixed in the same block I
    extended for the new stores; disclosed here. §COMPOSITION-ROOT.
  - **FORK-W scope note (surfaced, not a silent narrowing):** the §10.7-W grep rider names "the 63a
    test modules → 0 hits", which required editing the FROZEN `test_governed_migration_63a.py`
    (removing a dead `dry_run` passthrough). Reading A (the ruling authorizes it) taken; both
    readings + rationale in §FORK-W — lead/operator, confirm.
- **Packages considered:** none — no new mechanism; reused existing seams (`governed.resolve_subject`,
  `stamp_owner`, `LocalMemoryBackend`, `PrincipalStore`/`KeepStore`, `StoreHandle`,
  `report_unmigrated_governed_rows`, `SearchResult`/`NOTICE_KIND`, `run_query`). Read the installed
  signatures via lore_get_symbol before wiring.
- **Reuse ledger:** 5 new shipped symbols, all dispositioned — §DRY.
- **Graded:** N/A (a build report, not a verdict). Built on `a8c17c1` (the GREEN 63a build);
  committed atop `5be3714`. HEAD-at-report: `3f9790c` + the D1 test-fix commit.
- **decisions-needed:** FORK-W frozen-63a-test edit (Reading A taken; confirm) — the only open fork;
  everything else is built + green.
- receipt POINTERS: composition root → §COMPOSITION-ROOT; FORK-Y re-point → §FORK-Y; FORK-D1 →
  §FORK-D1; FORK-W → §FORK-W; SF-63-5 → §SF-63-5; DRY → §DRY; mutation proofs → §MUTATION; gates →
  §GATES.

---

## §COMPOSITION-ROOT — the headline (item 1)

The ONE shared seam, `server.py::AppContext._resolve_subject(capability)`:
reads `get_access_token()` (imported from `fastmcp.server.dependencies`, patchable at
`loremaster.server.get_access_token`), delegates to `governed.resolve_subject(token, capability,
registry=self.agent_registry, principal_store=self._principal_store, keep_store=self._keep_store)`
— the R-a.2 single `Subject` constructor. Fail-closed: an absent/unverified capability (or an
identity-less call, `capability=None` with no ambient token) → `GovernedDenied` (teaching), never a
`TypeError` (verified: `parse_credential(None)` → `is_blank(None)` → `None` → `stamp_owner`
`OwnerStampError` → `resolve_subject` `GovernedDenied`). **63b/63c/64 CALL this; they never re-spell
the token/registry read** (ONE-IMPLEMENTATION).

- `AppContext.recall`/`remember` resolve `capability` → `Subject`, thread `subject=` to the backend
  (recall SCOPED to the caller's visible set; remember owner-stamped, default project-keep scope).
- `AppContext.__init__` gains `principal_store` / `keep_store` (optional, default None → the
  non-governed test paths still build a context); `build_app_context` constructs + `ensure_ready`s a
  `PrincipalStore` + `KeepStore` over the unified DB (principal FIRST — the `member_of` ENFORCED
  endpoint the keep slice needs), appended to `write_stack_readied` (build-failure unwind) + closed
  in `aclose`. **D2:** the same build-failure block was missing `message_ledger.close()` — added.
- #420 adjudication comments updated: the memory verbs are tool-layer-WIRED (green), the R6
  backend-only bound is retired (`_GOVERNED_VERBS_ROUTED` + `_CAPABILITY_PARAM_DESCRIPTION` comments).

## §FORK-Y — the 18 re-pointed tool-layer tests (item 1, operator ruling A)

The 18 `@pytest.mark.skip(_TOOL_LAYER_63A_SKIP)` markers + the constant are DELETED; the 18 tests
now PASS via a `governed_ctx` fixture that: admits a principal on the ctx's OWN
`_principal_store`, registers an owned agent (`agent_registry.register`) capturing the minted
`capability`, mints the project keep (`_keep_store.get_or_create_keyed(key='project:lore')` so a
default-scope remember resolves), and patches `loremaster.server.get_access_token`. A transparent
`_GovernedAppContext` proxy injects the capability into `remember`/`recall` (the corpse-A
`_GovernedTestBackend` idiom), so the 17 `cutover_ctx` test BODIES + signatures stay byte-unchanged —
re-pointed via a class-scoped `cutover_ctx` override returning `governed_ctx` in the 4 all-repointed
classes (`TestSaveMemoryCutover`, `TestRecallMemoryCutover`, `TestSaveMemoryReservedMetadataGuard`,
`TestRecallMemoryFilters`); the 1 `indexed_context` test (`test_remember_then_recall_roundtrips`)
renamed to `governed_ctx` (2 body refs). The retrofit-contract deny twin
(`test_memory_retrofit_63a::TestIdentityLessToolLayerCallsDeny`) + the capability-description pin
stay GREEN. `test_mcp_server.py`: **665 passed, 0 skipped** (was 18 skipped) — see §GATES.
⚠ Note: `TestSaveMemoryCutover`'s ONE non-skipped test (`test_save_memory_rejects_an_unknown_kind`)
now routes through the governed override too (kind-validation fires before subject resolution — still
green, intent preserved); disclosed.

## §FORK-D1 — name the withheld memory boost (item 2)

`search.py::_recall_memory` now returns `_MemoryRecall(recalled, withheld)`: a governed deny is
caught but reported as `withheld=True` (distinct from an empty no-match). `search_code` emits ONE
derived `_MEMORY_WITHHELD_NOTICE` line (a `NOTICE_KIND` `SearchResult`) when withheld — a Leg-1 fact,
never a silent `[]` (the #131 shape). Code hits still return.
Pin `test_search.py::TestMemoryBoostWithheldNotice`: a denied boost is NAMED in exactly one render
line + the search still succeeds + the boost was attempted; POSITIVE CONTROL: a healthy empty recall
emits NO withheld notice.
⚠ **Served-surface consequence (disclosed):** `search_code` is still identity-less at 63a-ii (the
caller-`Subject` threading is 63b), so EVERY `lore_search` now appends this line until 63b. The
design FORK-D1 rider ordered exactly this (Leg-1 honesty). This is what caused D1 (2 teaching-notice
tests updated).

## §FORK-W — delete the struck dry_run mechanism; add report-unmigrated (item 3)

- Deleted: `migrate_governed(dry_run=)` param + `_migrate_memory_scope(dry_run=)` param + its
  `if dry_run or …` branch + all docstring mentions-as-feature + the CLI FORK comment. **The
  `MigrateGovernedResult.dry_run` FIELD never existed** (only a docstring line + the two fn params) —
  so "delete the field" was a no-op beyond the docstring; noted for the record.
- Added `lore-adm report-unmigrated --table <t>` → `report_unmigrated_governed_rows` over an injected
  `StoreHandle` (R4, `_dispatch_report_unmigrated`). A READ (never writes); loud-on-failure (a
  missing governed table exits 1 with a stderr line — `SurrealStoreError` caught — never a traceback).
- Pin `test_principals_cli.py::TestParserSurface::test_no_dry_run_mechanism_survives_the_governed_migration_surface`:
  a runtime-mechanism leg (no `dry_run` param on either fn, no field on `MigrateGovernedResult`,
  migrate-governed rejects `--dry-run`) + a bare-grep leg asserting every `dry[_-]run` residual over
  `governed.py`/`principals.py`/the 63a test modules is PROSE (comment/docstring), never a live code
  token. `TestReportUnmigratedVerb`: parser accepts it, counts over a provisioned table (exit 0),
  fails loud on an absent table.
- **Bare-grep residual adjudication (§10.7-W rider — each a file:line + verdict):** all residual
  `dry-run` hits are PROSE documenting the struck paradigm → **KEEP** (a struck-paradigm note is the
  threat-model documentation, not a mechanism): pre-existing `principals.py:849,~1163,~1225`; my new
  §10.7-W notes `governed.py:~77`, `principals.py:~1007,~1289,~1594`, `test_governed_migration_63a.py:~84`.
  `lore_dead_code`: no `dry_run` residue by construction (never a symbol).
- **⚠ FORK (surfaced, Reading A taken):** the rider names "the 63a test modules → 0 hits", requiring
  an edit to the FROZEN `test_governed_migration_63a.py` (dropping the `_migrate_memory(dry_run=)`
  helper param + passthrough — a DEAD param, no test ever passed `dry_run=True`, so a pure mechanical
  removal that changes no asserted behavior; + a `[--dry-run]` docstring fix). **Reading A:** the
  §10.7-W ruling naming these very modules authorizes the deletion-cleanup. **Reading B:** the brief's
  DISCIPLINE ("only re-point the 18 + 2 corpse") forbids touching frozen `test_*_63a.py`, making the
  grep rider unsatisfiable → escalate. I took **A** (the ruling is explicit and the edit weakens no
  pin) and surface it; a revert is trivial if the lead rules B.

## §SF-63-5 — delete refuses while owning a governed row (item 4, operator confirmed)

New `PrincipalOwnsGovernedRowsError(PrincipalStoreError)`. `PrincipalStore.delete`, after the
keep-refuse (both before any DELETE), refuses when `SELECT count() FROM memory WHERE owner_principal
= $p GROUP ALL > 0`, naming the count + the packet-64 `set_owner` orphaning mechanism.
**TOLERANT of a store without the memory table** via a fail-CLOSED `_table_exists` probe (INFO FOR
DB): a pre-retrofit/principal-only store owns no governed rows (delete proceeds), but a connection
fault during the probe PROPAGATES (never read as "0 owned rows") — so the frozen-61 delete tests
(no memory table) stay green. Pin `test_principal_delete_governed_63a.py`: the refuse fires with one
owned row (keeping no keep, so it is the memory-owner refuse doing the work), names count +
mechanism, removes nothing; POSITIVE CONTROL: a principal owning no governed row deletes cleanly.
Carries `#SF-63-5 — RED the day 64's orphan-to-NONE lands; delete this pin with the mechanism.`

## §DRY — reuse ledger (5 new shipped symbols)

| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `server.AppContext._resolve_subject` | `lore_get_symbol governed.resolve_subject` + `lore_search "get_access_token"` | `governed.resolve_subject` (the R-a.2 constructor) + `readonly_guard` reads `get_access_token` | **HAND-ROLLED (the composition root)** — the ONE shared seam that CALLS `resolve_subject`; 63b/63c/64 reuse it (no second token/registry read). |
| `server._GovernedAppContext` (test proxy) | read corpse-A `_GovernedTestBackend` | the transparent-proxy idiom | **EXTENDED** the corpse-A proxy idiom to the AppContext layer (inject `capability=`). |
| `search._MemoryRecall` | read `search.SearchPipeline._recall_memory` (1 caller) | no result type existed | **HAND-ROLLED** — a 2-field frozen dataclass so `withheld` is a fact, not conflated with empty. |
| `search.SearchPipeline._memory_withheld_notice` | read `_memory_section_header`/`_memory_elision_notice` | the NOTICE_KIND builder idiom | **EXTENDED** the notice-builder idiom (one more static NOTICE_KIND entry). |
| `principals.PrincipalOwnsGovernedRowsError` + `_table_exists` | read `PrincipalHasKeepsError` + `PrincipalStore.delete` | the keep-refuse typed-error idiom; no table-existence helper existed | **EXTENDED** the refuse idiom (a sibling typed error) + **HAND-ROLLED** `_table_exists` (fail-closed INFO-FOR-DB probe; nothing existed). |

## §MUTATION — load-bearing pin proofs (break prod → pin RED → restore, all restored clean)

| # | mutation | pin | observed |
|---|---|---|---|
| 1 | swallow the governed deny silently (`withheld=False`) | `test_search::TestMemoryBoostWithheldNotice::test_a_denied_boost_is_named_in_the_render` | **RED** (positive control stayed green), restored |
| 2 | re-add the struck `dry_run` param to `migrate_governed` | `test_principals_cli::…test_no_dry_run_mechanism_survives_the_governed_migration_surface` | **RED** (runtime-mechanism leg), restored |
| 3 | neuter the SF-63-5 refuse (`if False`) | `test_principal_delete_governed_63a::TestDeleteRefusesWhileOwningGovernedRows` (both legs) | **RED** (loner control stayed green), restored |

FORK-Y is proven by construction: the 18 tests are RED-when-skipped-removed on an unwired root (they
DENY) and GREEN only because the composition root resolves the injected capability end to end.

## §GATES (all green)

- **7 `test_*_63a.py` + the new SF-63-5 module:** `89 passed` (85 contract — unchanged from 63a — + 4
  SF-63-5).
- **`test_mcp_server.py` (full):** `667 passed, 0 skipped` (was 667 total with **18 skipped**; the
  18 are now re-pointed + passing, 0 skipped) — final re-run after the D1 test-fix.
- **search + principals + principal_* suites:** `312 passed` (test_search, test_principals_cli,
  test_principals_store, test_principals_schema, test_principal_keys_schema, test_principal_keys_store,
  test_principal_delete_cascade_61).
- **60/61/62 regression sweep:** `626 passed` (was 622; +4 = the FORK-W CLI pins on test_principals_cli).
- **`uv run ruff check .`** → All checks passed.
- **`bash scripts/typecheck.sh`** → every member OK (incl. test trees) + shellcheck OK.

### §MCP-FINAL
Final full `test_mcp_server.py` re-run (after the D1 test-fix): **`667 passed, 0 skipped`** in
147s — 0 failed, 0 skipped. (The interim run before the fix was `2 failed, 665 passed`; the 2 were
the D1-caused teaching-notice tests, now green → 667 passed.)

## FRICTION filed
- **lore finding #434** (`capability_gap`, area `lore_index`): `lore_index(reconcile=True,
  tier=lore)` exceeded the 300s MCP idle timeout (backgrounded, then failed on idle) — a full-tier
  reconcile is heavier than the tool-idle budget. Not blocking (the dead_code rider is satisfied by
  construction — `dry_run` was never a symbol). Routed around it, filed per the dogfood protocol.
