# REPORT-build-63a — packet 63a GOVERNED-substrate + memory-retrofit BUILD

- `brief-base v14 read`
- `brief project v7 read`
- store reference consulted: `docs/reference/surrealdb-31-capabilities.md` §1.1 (FIELD OVERWRITE /
  INDEX IF-NOT-EXISTS), §1.4 (option<> on a populated table — no ASSERT/DEFAULT), §1.8 (UNIQUE over
  option<> — many NONE coexist), §2 (CONTENT / record<> links / explicit projection reads NONE),
  §3 (execute_read_transaction / BEGIN…COMMIT envelope None entries / statement[0] trap), §5 (hot-row
  CAS mint). Cited, never re-transcribed.

## SUMMARY BLOCK

- receipt: `brief-base v14 read` · `brief project v7 read`
- **state: done-with-deviations** — the 63a substrate + memory retrofit is BUILT and GREEN; the
  retrofit's identity-less-DENY has a wide, DISCLOSED blast radius (below) resolved in-session.
- deviations (one line each):
  - **D1 (search.py, PRODUCTION):** `search_code`'s memory-boost enrichment is now identity-less-
    governed → DENIES. Fixed: graceful degrade (no boost, no leak) — directly-caused, isolation-
    correct. §FORK-D1.
  - **D2 (corpse-A wider than named ~102):** the retrofit broke test_schema_rebuild + _memory_fakes
    (parity) beyond the brief's test_memory_backend/test_memory_cutover. Fixed via a shared-admin
    default-subject wrapper (assertion-preserving). §CORPSE-A.
  - **D3 (FORK-Y, tool-layer, DECISION-NEEDED):** the tool layer DENIES all memory calls at 63a
    (R6), so 18 test_mcp_server tool-layer tests test REMOVED behavior. SKIPPED with a 63b/64
    re-enable trigger. §FORK-Y — **lead/operator: confirm skip vs re-point.**
  - **D4 (FORK-Z, cascade, DECISION-NEEDED):** `memory.owner_principal` is a new `record<principal>`
    link that CORRECTLY fired the cascade re-open trigger. Pin set updated + classified LIVE-
    DEPENDENCY; the `PrincipalStore.delete` cascade/refuse disposition is DEFERRED (design §2.1
    silent; latent — no principal-delete in the commit-only single-principal fleet). §FORK-Z.
  - **D5 (FORK-W, CLI dry-run):** design §1.2 specifies `[--dry-run]` but the shipped 2026-08-20
    ruling STRUCK dry-run from the CLI (a pin). CLI flag OMITTED (contract needs only `--table`);
    the `migrate_governed(dry_run=)` function param survives. §FORK-W.
- **Packages considered:** none — no mechanism introduced beyond the 60/61/62 seams the build reuses
  (`run_query`/`execute_read_transaction`/`compose`/`TxnFragment`/`StoreHandle`/`wrap_store_rejection`/
  `AuditStore.append_fragment`/`authorize`/`authorize_filter`/`_grantable`/`stamp_owner`/
  `resolve_visible_keeps`). Verified by reading the installed seams' signatures in `store/_txn.py`.
- **Reuse ledger:** 8 new shipped symbols, all dispositioned — §DRY. ⚠ lore_search timed out (>120s,
  twice); the reuse survey fell back to direct grep+read of the target modules (SAID OUT LOUD per the
  dogfood protocol; friction filed below).
- **Graded:** N/A (this is a build report, not a verdict on another artifact). Built at HEAD `2bf5769`.
- **decisions-needed:** FORK-Y (tool-layer skip vs re-point) · FORK-Z (memory-row delete disposition)
  · FORK-W (design §1.2 [--dry-run] vs shipped no-dry-run ruling). All three surfaced with a
  recommendation below; none blocks the green build.
- receipt POINTERS: build map → §BUILD; DRY → §DRY; mutation proofs → §MUTATION; corpse-A → §CORPSE-A;
  forks → §FORK; gates → §GATES.

---

## §BUILD — file-by-file, mapped to REPORT-adversary-63a-3 §SAT

All shipped shapes match the adversary's 85/85 reference build (§SAT). The contract went 168/168
(85 across the 7 `test_*_63a.py` + 83 corpse B/C), identical to the adversary's reference count.

- **`lorerunes/lorerunes/pdp.py`** — FORK 1 (§10.1): `Resource.scope: str | None`; `__post_init__`
  admits the literal `None` (absent/legacy scope) and STILL raises on `""` + every non-domain string.
  `to_surql`/`matches` unchanged (byte-identical emitted SurrealQL). One-line widening + docstring.
- **`loremaster/agents.py`** — #425 additive close (§10.3): new `_verify_capability_owner(presented,
  token) -> (agent_id, owner_principal_id) | None` — the ONE verified SELECT now ALSO projects
  `owner_principal AS owner_id` (constant `_OWNER_ID_ALIAS`); `verify_capability` returns its `[0]`
  (shipped `str|None` shape byte-unchanged, all 13 call sites pass); `owner_principal_of` DELETED.
- **`loremaster/owner_stamp.py`** — `stamp_owner` consumes `_verify_capability_owner` in ONE
  round-trip; NAMES the retired method nowhere (the P8d source-scan pin caught my first comment
  mention — reworded).
- **`loremaster/store/surreal_schema.py`** — `_governed_field_specs()` (3 option<> cols, no
  ASSERT/DEFAULT) + `_governed_index_statements(table)` (plain IF-NOT-EXISTS on `scope`+
  `owner_principal`; `owner_agent` NOT indexed), WIRED into `_memory_statements`; SF-63-4
  `keep.key option<string>` spec + `keep_key` UNIQUE index into `_keep_statements`.
- **`loremaster/keeps.py`** — `get_or_create_keyed` (get_by_key → CREATE+RELATE with `key` → CAS
  re-read on a UNIQUE conflict, transport pass-through) + `get_by_key`; the WHOLE verb under ONE
  `wrap_store_rejection(KeepStoreError, …)` (corpse-C rejection-wrap pin: the injected fault hits the
  initial key READ first).
- **`loremaster/governed.py`** — `resolve_subject` (stamp_owner → get_by_email → resolve_visible_keeps,
  fail-closed → `GovernedDenied`; the ONE production `Subject(` constructor, R-a.2); `read_filter` (==
  `authorize_filter(READ).to_surql()`, R-a.3); `guarded_write(store: StoreHandle)` (pre-read via
  `run_query` = acquire #1 → authorize → guarded mutation carrying `authorize_filter(action)` in WHERE
  + RETURN, composed with the audit fragment via `execute_read_transaction` = acquire #2; `row_count`
  read back from the RETURN by SHAPE, 0 → `GovernedConflict`); `report_unmigrated_governed_rows`.
  R4: NO direct SDK call — routes only through the injected handle + the driver seams. `PROJECT_KEEP_KEY`
  constant (shared home).
- **`loremaster/memory/local.py`** — `handle` property (`StoreHandle(self._ensure_connection,
  self._drop_connection, self._url)`); `remember`/`recall`/`invalidate` take `subject: Subject|None=
  None` (None → `GovernedDenied`); `remember` stamps owner from the subject + resolves scope
  (`_resolve_write_scope` → `_grantable`-validated `scope=` via the pdp MODULE attribute, else
  `_default_project_scope` by `key='project:lore'`); `recall` splices `read_filter`; `invalidate`
  routes through `guarded_write(store=self.handle)`.
- **`loremaster/server.py`** — `_GOVERNED_VERBS_ROUTED` (the 2 memory verbs) + `_GOVERNED_VERBS_PENDING_
  ROUTING` (30 pending (tool,verb) → trigger, DERIVED-then-hand-authored per §10.2; a new action REDS
  the coverage pin); `lore_remember`/`lore_recall` self-destruct from `_GOVERNED_TOOLS_PENDING_OWNER_
  STAMP` (R-a.5); ONE shared `_CAPABILITY_PARAM_DESCRIPTION` on both memory tools; `capability=` param
  wired through `AppContext.recall/remember` (accepted but NOT resolved at 63a — R6 honest bound: the
  present path denies, the composition root lands 63b/64).
- **`loremaster/principals.py`** — `migrate_governed(table, store, keep_store, principal_store,
  registry=None, dry_run=False)` → `MigrateGovernedResult` (memory scope backfill to the minted
  project keep resolving THE operator principal; message REFUSES agent-first; idempotent) via
  `_migrate_memory_scope`/`_scope_count`; the `migrate-governed` CLI subparser (`--table`) + dispatch.
- **`loremaster/memory/backend.py`** (protocol, directly-caused) — `MemoryBackend` protocol gains
  `subject`/`scope` on recall/remember/invalidate so protocol-typed callers typecheck.

**HONEST BOUNDS honoured:** R6 (AppContext present path NOT wired — denies at 63a) and R5
(`rebuild_embeddings`/`restore_from_ledger` re-strip: replay does NOT stamp governed columns — the
rebuilt rows land NONE-scope; NOT fixed, noted for 63b/65) both stand.

---

## §DRY — reuse ledger (8 new shipped symbols)

⚠ lore_search timed out twice (>120s); survey fell back to `grep`+`Read` over the target modules —
said out loud, friction filed (`lore_findings`, capability_gap, area=lore_search).

| new symbol | search run | returned | disposition |
|---|---|---|---|
| `governed.PROJECT_KEEP_KEY` | grep `project:lore\|PROJECT_KEEP\|project_keep_id` over `loremaster/` | no existing constant | **HAND-ROLLED** — ONE shared home for the project-keep natural key (backend default + migration mint agree; design §2.2). slug-hardcoded bound flagged in-source. |
| `agents._verify_capability_owner` | read `agents.py::verify_capability` | the ONE verified SELECT already projected owner_principal.email | **EXTENDED** `verify_capability` (§10.3 additive — the shared pair-path; `verify_capability` returns `[0]`). |
| `keeps.get_or_create_keyed` | design §8 pre-dispositioned (`lore_get_symbol KeepStore.create_keep`) | non-idempotent `ulid()` create + keeper auto-household | **EXTENDED** `create_keep` — same txn shape + a UNIQUE-conflict CAS re-read (store-ref §5). |
| `keeps.get_by_key` | read `keeps.py` (get_keep / list_keeps_* are the only readers) | no key-lookup reader existed | **HAND-ROLLED** — the SF-63-4 natural-key read (mirrors `get_keep`'s explicit-projection idiom). |
| `local._default_project_scope` / `_resolve_write_scope` | read `local.py` writes | no scope-resolution helper existed | **HAND-ROLLED** — reuses `pdp._grantable` (via the module attr, mutation-provable) + `KEEP_TABLE`; not a fork of anything. |
| `principals.migrate_governed` (+ `_migrate_memory_scope`/`_scope_count`) | design §8 (`grep migrate\|backfill`) | no data-migration verb exists | **HAND-ROLLED** — the first row-backfill; the `lore-adm` CLI family is the home (60/61 precedent). |
| `server._GOVERNED_VERBS_ROUTED` / `_GOVERNED_VERBS_PENDING_ROUTING` | design §3.1/§10.2 pre-dispositioned | the per-TOOL `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` sibling | **HAND-ROLLED (design-mandated)** — the per-VERB #420 adjudication; the coverage pin guards it. |
| `server._CAPABILITY_PARAM_DESCRIPTION` | design §10.5 rider (i) (packet-45 `_comms_identity_agent_description` idiom) | the per-tool shared-description idiom | **EXTENDED** the packet-45 idiom — ONE constant, both memory tools. |

---

## §MUTATION — load-bearing pin proofs (break prod → pin RED → restore, all restores verified)

| # | mutation | pin | observed |
|---|---|---|---|
| 1 | drop FORK-1 `scope is not None` guard (reject None) | `test_pdp_none_scope_63a::…test_resource_constructs_with_a_none_scope` | **RED**, restored |
| 2 | route `stamp_owner` back through `verify_capability` | corpse B `…routes_through_the_shared_verify_capability_owner` | **RED** (leg B), restored |
| 3 | append the audit in a SEPARATE round-trip (break atomicity) | `test_governed_substrate_63a::…test_a_rejected_mutation_appends_no_audit_row` | **RED** (before≠after), restored |
| 4 | hand-write memory's governed fields (bypass `_governed_field_specs`) | `test_governed_schema_63a::…test_the_governed_fields_route_through_the_shared_emitter` | **RED**, restored |

(The adversary's reference build additionally mutation-proved R4, the TOCTOU leg, the vanished-conflict
row_count leg, and the corpse-C coverage map — my build matches that reference 168/168, §SAT.)

---

## §CORPSE-A — shipped-test updates (assertion-preserving)

The brief named test_memory_backend (104) + test_memory_cutover (2). The retrofit's REQUIRED `subject`
also broke test_schema_rebuild (22, directly-caused) and forced `_memory_fakes` parity. Approach: ONE
shared **ADMIN** subject — an admin's `read_filter` is `AllRows` (UNFILTERED), so recall behaves
EXACTLY as pre-retrofit and every original assertion is byte-preserved; remember carries an explicit
`scope="server"` (grantable by any subject) so no per-test project keep is needed.

- **test_memory_backend.py (104 sites):** ONE `_GovernedTestBackend` transparent proxy at the
  `make_backend` + `real_backend` fixtures (injects `subject`/`scope`, delegates every other attr via
  `__getattr__`/`__setattr__` so the `_connection`/`_query` durability seams still work). 0 call-site
  edits. **Spot-check: no test reads `scope`/`owner_*` (grep = 0), so admin-unfiltered preserves all.**
  129/129.
- **test_memory_cutover.py (2 recall sites):** `subject=_GOV_SUBJECT` added directly. GREEN.
- **test_schema_rebuild.py (22 sites, DIRECTLY-CAUSED — beyond the named files):** `subject=_GOV_SUBJECT`
  (+`scope="server"` on remember) added per-call. GREEN.
- **_memory_fakes.py (parity, DIRECTLY-CAUSED):** `FakeMemoryBackend.{remember,recall,invalidate}`
  accept + IGNORE `subject`/`scope` (behavioural parity — the fake pins memory behaviour, not
  governance). GREEN.
- **memory/backend.py (protocol, DIRECTLY-CAUSED):** protocol gains the params so the fake + protocol-
  typed callers typecheck.

Each corpse-A assertion is PRESERVED (admin = unfiltered; no scope/owner reads); the removed-behaviour
adjudication (identity-less deny) is pinned separately by the 63a contract, never weakened here.

---

## §FORK — the disclosed blast-radius decisions (lead/operator to rule)

### FORK-D1 (search.py, PRODUCTION — resolved, directly-caused)
`search_code` enriches code-search with a memory recall (`_recall_memory`). Post-retrofit that recall
is identity-less-governed → DENIES. **Fixed:** catch `GovernedDenied` → `[]` (no boost). This is the
ISOLATION-correct 63a behaviour — an identity-less search must never boost with (or leak) a principal's
governed memory. 63b/64 threads the caller's `Subject` to scope the boost. (`search.py::_recall_memory`.)

### FORK-Y (tool-layer test coverage — DECISION-NEEDED; recommend SKIP-with-trigger)
R6 keeps the AppContext composition root unwired at 63a, so `AppContext.recall/remember` DENY EVERY
memory call (identity-less AND capability-bearing). 18 test_mcp_server tests pin the PRE-retrofit
tool-layer ANSWER (save/recall/filters/metadata) → they test removed behaviour and CANNOT pass at 63a.
**Resolved:** `@pytest.mark.skip(reason=_TOOL_LAYER_63A_SKIP)` on each, naming the 63b/64 composition-
root re-enable trigger. The underlying behaviour is RETAINED at the backend layer (test_memory_backend);
the deny itself is pinned by `test_memory_retrofit_63a::TestIdentityLessToolLayerCallsDeny`.
**RECOMMEND skip** (least-destructive; bodies survive for 63b/64 to re-point to the capability path —
the deny will start FAILING them then, self-signalling the re-point). Alternative: re-point to
assert-deny (redundant with the contract). **Lead/operator: confirm.** (test_mcp_server.py, 18 skips.)

### FORK-Z (cascade delete-disposition — DECISION-NEEDED; DEFERRED with trigger)
`memory.owner_principal` (`option<record<principal>>`) is the FIRST governed-row owner link — the exact
new link `test_principal_keys_schema::…cascade_adjudication` anticipated (its re-open trigger fired
CORRECTLY). **Resolved (pin's own instruction):** added to the expected set, CLASSIFIED **LIVE-
DEPENDENCY** (a governed row's owner must not silently point at a ghost). ⚠ The substantive
`PrincipalStore.delete` cascade/refuse is **DEFERRED**: design §2.1 is SILENT on the memory-row delete
disposition, and it is LATENT at 63a (commit-only, single-principal dogfood fleet — no principal is
deleted). **Re-open trigger:** the first principal-delete against a store holding an owned memory row
(63b/64 wires cascade-or-refuse; never a silent dangle). **Lead/operator: rule cascade vs refuse.**

### FORK-W (CLI --dry-run — resolved; design vs shipped ruling)
design §1.2 item 5 specifies `migrate-governed … [--dry-run]`, but the shipped 2026-08-20 ruling STRUCK
the dry-run/--execute paradigm from this CLI (pinned by `test_principals_cli::…no_execute_flag_or_dry_
run`, which scans all code strings). The 63a CONTRACT requires only `--table`. **Resolved:** the CLI
flag is OMITTED (complies with the shipped ruling); the `migrate_governed(dry_run=)` FUNCTION param
survives for the design's preview intent + programmatic use. **Lead: reconcile the design/ruling
conflict** (update the pin to exempt migrate-governed, or accept the no-flag form).

---

## §GATES

- **7 `test_*_63a.py` + corpse B/C:** `168 passed` (85 contract + 83 corpse) — identical to the
  adversary reference (§SAT). `/tmp` receipt reproduced twice.
- **Changed/affected suites** (test_mcp_server, test_search, test_schema_rebuild, test_memory_backend,
  test_memory_cutover, test_principal_keys_schema, test_principals_cli): `1042 passed, 18 skipped`
  (the 18 = FORK-Y).
- **60/61/62 regression sweep:** `622 passed` (was 620/2-failed; the 2 = cascade + dry-run, now
  resolved). Files: test_agent_capability, test_agent_owns_principal_schema, test_audit_{schema,store},
  test_keeps_{cli,schema}, test_pdp_oracle_61b, test_principal_delete_cascade_61,
  test_principal_keys_{schema,store}, test_principals_{cli,schema,store}, test_visible_keeps_61b,
  test_surreal_store.
- **`uv run ruff check .`** → All checks passed.
- **`bash scripts/typecheck.sh`** → every member OK incl. test trees.

**Aggregate green (this session):** 168 (contract+corpse) + 1042/18-skip (affected) + 622 (60/61/62)
= all green, 18 deliberate FORK-Y skips. Committed as logical one-concern `feat(63a): …` commits.
