# REPORT-contract-63a-5 — CONTRACT FIX rd2: BLOCKER 1/2 (§10.6) + corpse sweep + flags (RED)

- `brief-base v14 read`
- `brief project v7 read`
- store reference consulted: `docs/reference/surrealdb-31-capabilities.md` §3
  (execute_transaction / the `.query()` statement[0]-only trap → verified multi-statement txns for
  the mutation+audit compose), §1.4 (option<> on a populated table), §5 (hot-row CAS mint). Cited,
  never re-transcribed.

## SUMMARY BLOCK

- **STATE: done** — RED contract strengthened, runnable-RED preserved. Folded adversary-63a-2's two
  BLOCKERS + the corpse sweep + the two flags, plus design §10.6's 5 riders + R4.
- BLOCKER 1 (#431): `_governed_contract.index_statement` regex de-anchored → the governed-INDEX
  mutation pin discriminates on a correct `_plain_index` build (§B1).
- BLOCKER 2 (#430, design §10.6): `guarded_write(..., store=StoreHandle)`; 4 substrate call sites +
  all 5 riders (vanished-conflict+positive-control, audit-atomicity BOTH legs, TOCTOU-by-injected-
  acquire, counting-acquire mutation proof, DRY) + R4 (governed.py no-direct-SDK AST pin) (§B2).
- CORPSE sweep (#432): all 57 shipped tests inventoried + adjudicated individually (§CORPSE) — B
  (stamp_owner re-key) + C (get_or_create_keyed coverage) folded in-contract, both RED-until-built;
  A (52 identity-less) = DOCUMENTED build-phase task (NOT contract-level — my judgment, §CORPSE-A).
- FLAG 1 + FLAG 2 applied verbatim (retrofit docstring + annotations); §9-rider-9 prose sweep done,
  every hit adjudicated file:line (§PROSE) — no stale served surface needs a contract fix.
- **Deviations (2):** (1) `migrate_governed`'s StoreHandle signature is in `principals.py` (OUT of my
  writable set) → FLAGGED with the exact coordinated edit, not edited (§DEVIATIONS); the governed.py
  half (`report_unmigrated_governed_rows`) IS reshaped to StoreHandle. (2) a PRE-EXISTING broad-catch
  vacuous-pass in `test_a_keep_resolution_failure_denies` (not my code) surfaced (§DEVIATIONS).
- **Packages considered:** none — no mechanism specified (test-contract strengthening + a typed
  data-carrier `StoreHandle`; the design already adjudicated the migration verb `bespoke`).
- **Reuse ledger:** 2 new symbols, all dispositioned (§DRY).
- **Graded:** n/a — I authored no verdict; this is a contract fix, not an audit.
- **Decisions-needed:** none new. migrate_governed principals.py edit → FLAGGED (§DEVIATIONS). Corpse
  A build-task size (~52 tests) surfaced for lead awareness; I judge it build-phase, not a fork.
- Receipt POINTERS: BLOCKER 1 → §B1; BLOCKER 2 + riders → §B2; R4 → §B2-R4; corpse → §CORPSE;
  flags → §FLAGS; prose sweep → §PROSE; DRY → §DRY; mutation-proof plan → §MUTATION; deviations →
  §DEVIATIONS; counts + reconciliation → §COUNT; gate tails → §GATES.

---

## §B1 — BLOCKER 1 (#431): the governed-INDEX mutation pin now discriminates

`_governed_contract.py::index_statement` — the regex was END-ANCHORED
(`FIELDS\s+{col}\s*(?:UNIQUE)?\s*$`), so the governed-INDEX mutation pin
(`test_governed_schema_63a::TestGovernedIndexesAreEmittedOnMemory::
test_the_governed_indexes_route_through_the_shared_emitter`), which APPENDS ` COMMENT
'gov-index-probe'` to the whole `DEFINE INDEX`, made `FIELDS scope` no longer the tail → the helper
returned None → the pin reddened on a CORRECT `_plain_index` build.

**Fix (adversary-proven → schema 24/24):** `FIELDS\s+{col}\b\s*(?:UNIQUE\b)?(?!\s*,)` — tolerate a
trailing clause (COMMENT / SEARCH ANALYZER / …) while the negative lookahead `(?!\s*,)` still
rejects a composite `FIELDS scope, owner` (the §4.1 single-column-index semantics). Verified against
EVERY index pin that calls the helper: the plain-scope/owner_principal index pin, the `owner_agent`
NOT-indexed discriminator, the keep.key UNIQUE pin, and the mutation pin — all still discriminate.

## §B2 — BLOCKER 2 (#430, design §10.6): `guarded_write(..., store=StoreHandle)`

**The ruled shape (design §10.6, option (c) — a typed injection of the connection-OWNER triple):**
- `loremaster/store/_txn.py` — NEW frozen `StoreHandle(acquire, drop, url)` beside the driver seams
  (it carries connection callables → `loremaster`, never `lorerunes`). Data-carrier, not a mechanism.
- `loremaster/governed.py` — `guarded_write(subject, action, *, table, row_id, set_fragment, audit,
  store: StoreHandle)`; the docstring pins the ruled internals: pre-read via `run_query(acquire=,
  drop=, url=)`, mutation+audit via `compose(...)` → `execute_transaction(...)`, `row_count` read
  BACK from the guarded statement's RETURN. Also added `report_unmigrated_governed_rows(store, table)`
  stub (§2.3 alarm) taking the SAME StoreHandle (R4).
- `loremaster/memory/local.py` — NEW `LocalMemoryBackend.handle` property STUB → the ONE accessor
  every governed store exposes over its own `(_ensure_connection, _drop_connection, _url)` triple.
- `_governed_contract.py::store_handle(connection, *, url, on_acquire=None) -> (handle, calls)` — the
  test seam building a StoreHandle over a shared per-test connection + an ACQUIRE COUNTER (rider iv)
  + an on_acquire injection hook (rider iii). The substrate/migration modules build handles this way.

**The 4 frozen substrate call sites** (`test_governed_substrate_63a.py`) all now pass `store=handle`;
the retrofit invalidate route reaches guarded_write through `backend.handle` (builder-GREEN).

**The 5 riders — each folded and pinned:**
- **(i) vanished-conflict + positive control in the SAME test** — `test_a_guarded_write_on_a_vanished_
  row_raises_conflict` reshaped: LEG 1 = alice's write on her EXISTING row returns `row_count == 1`
  from the RETURN (a no-handle/dead-seam build fails HERE, killing the old FALSE-PASS where a
  no-store call raised GovernedConflict byte-identically); LEG 2 = DELETE the row, identical call →
  GovernedConflict.
- **(ii) audit atomicity BOTH legs** — leg A `test_an_admin_bypass_write_appends_an_audit_row` (+1);
  NEW leg B `test_a_rejected_mutation_appends_no_audit_row`: a `set_fragment` violating the SCHEMAFULL
  memory schema (`embedding = 'not-a-float-array'`, `embedding` is `array<float>`) is REJECTED → the
  whole composed `BEGIN…COMMIT` rolls back → ZERO audit rows (before==after), proving the audit rides
  the SAME txn (a separate-round-trip build appends +1 and reds). ⚠ leg B carries a
  `not isinstance(rejection.value, NotImplementedError)` guard — see §MUTATION for the self-caught
  vacuous-pass it prevents.
- **(iii) TOCTOU by injected acquire** — NEW `test_a_rescope_between_the_read_and_the_write_raises_
  conflict`: `on_acquire(2)` lands a re-scope UPDATE between the pre-read (acquire #1) and the guarded
  mutation (acquire #2); the guarded WHERE excludes the moved row → GovernedConflict, row untouched.
  Deterministic, no 8-way race.
- **(iv) counting-acquire mutation proof** — every guarded_write pin asserts `calls['acquire'] >= 1`;
  a build that bypasses the handle for any statement observes 0 acquires and reds.
- **(v) DRY** — see §DRY (StoreHandle minted after the required `lore_search`; the adversary's
  `run_governed_query(connection,…)` shim rejected as the wrong direction — takes a raw connection).

Plus a DRY/accessor pin `TestAGovernedStoreExposesAHandleAccessor` (RED-until-built): `backend.handle`
is a `StoreHandle` whose `url` is the backend's OWN driver url (§10.6 "ONE accessor").

⚠ **A latent precision fix I made** (in-scope, substrate module): `governed_world` applied ONLY
`generate_memory_ddl` (no governed columns at HEAD), so every guarded_write pin reddened at the SEED
(`no such field 'owner_agent'`), masking the precise RED. I applied the §4.1 governed overlay
(hand-transcribed, decoupled from the emitter — the retrofit `oracle_conn` idiom), so the pins now
red on the SUBSTRATE seam (`guarded_write` NotImplementedError, verified at HEAD). On a GREEN build
the emitter also emits these columns → a safe idempotent double-apply. The schema module independently
owns the emitter pin, so this decoupling loses no coverage.

### §B2-R4 — governed.py issues no direct SDK call (design §10.6 R4)

`TestGovernedRoutesAllSdkThroughTheDriver` (`test_governed_substrate_63a.py`):
- `test_governed_py_has_no_direct_sdk_call_site` — AST scan over `governed.py`: (a) no `surrealdb`
  import (it holds a StoreHandle of callables, constructs no connection); (b) no SDK connection-method
  call, the method set DERIVED from `_sdk_guard.SDK_CONNECTION_CLASSES` (reach law #344/#345, never a
  hand-list). GREEN at HEAD + on the correct build; reds a build that hand-rolls `connection.query`.
- `test_the_sdk_call_site_scanner_is_not_blind` — POSITIVE CONTROL: the scanner FLAGS a synthetic
  `connection.query_raw(...)` source, so the GREEN above is cleanliness, not blindness.
- Reach honesty: this AST lint covers ALL of governed.py's code (even non-executed branches) weakly;
  the AUTOUSE runtime `_sdk_guard` (conftest) covers EXECUTED paths absolutely (guarded_write /
  report_unmigrated are executed by the substrate/migration pins). The seam between them is stated.

## §CORPSE — all 57 shipped tests the retrofit + #425 retire, adjudicated INDIVIDUALLY

The adversary measured 57 shipped tests broken by the reference build (52 A + 1 B + 4 C). "The rest
are X" is BANNED — each class adjudicated, and B/C folded in-contract (RED-until-built), A documented.

### §CORPSE-A — the 52 identity-less tests (build-phase task, NOT contract-level)

**Re-derived at HEAD** (I cannot reproduce the exact "52" without building the reference — I author no
production logic — so I characterise the surface instead): `test_memory_backend.py` (100 `recall`/
`remember` call sites) + `test_memory_cutover.py` (2) = **102 identity-less call sites across 136
collected tests, 0 passing `subject=` today, ALL green at HEAD** (regression sweep). They certify the
RETIRED identity-less world (design §0 removed-behavior 1: post-retrofit `subject=None` DENIES).

**Disposition = the spec:** the builder updates each to pass a `subject`, PRESERVING its original
assertion; the cold-audit verifies none is SILENTLY WEAKENED (the rename-sweep dual — tests written
before the change certify the old world). **Judgment: build-phase, not contract-level** — the
retrofit module ALREADY pins the new identity-less DENY (`TestIdentityLessCallsDeny` +
`TestIdentityLessToolLayerCallsDeny`), so no NEW contract pin is owed; the 102 shipped call sites just
need the new API, which is the builder's mechanical (but careful) work. I did NOT bulk-edit them (per
brief). ⚠ **Lead heads-up:** this is a sizeable build task (~52 breaking tests); it is build-phase
pricing, not a contract fork, but worth naming.

### §CORPSE-B — stamp_owner routing re-keyed for #425 (in-contract, RED-until-built)

`test_agent_capability_seams.py::test_stamp_owner_routes_through_verify_capability` → RENAMED
`test_stamp_owner_routes_through_the_shared_verify_capability_owner`. The pre-#425 form patched
`verify_capability` and expected stamp_owner to break — but §10.3 routes stamp_owner through the
SHARED `_verify_capability_owner` (ONE read), so on a correct build it FALSE-REDs, and a builder could
"fix" it WRONG by re-routing through `verify_capability` (reintroducing the #425 second read). Two
legs: LEG A (positive) patches `_verify_capability_owner` (raising=False, unbuilt at HEAD) → stamp_owner
must surface it; LEG B (discriminator) patches `verify_capability` → stamp_owner must COMPLETE with a
valid pair, NOT surface it. Verified RED-until-built at HEAD (LEG A: "DID NOT RAISE" because the shared
path is unbuilt). LEG B is the leg that reds the wrong re-route.

### §CORPSE-C — get_or_create_keyed registered in the keeps coverage-map (in-contract, RED-until-built)

`test_keeps_store.py::_WRITE_PATH_INVOCATIONS` gains a `get_or_create_keyed` entry. At HEAD the stub
carries no mutating literal → the DERIVED `_WRITE_PATHS` excludes it → `test_the_derived_write_path_
set_matches_the_coverage_map` reds (map=7 ⊋ derived=6) — the correct contract-first RED-until-built
(verified: this pin now the sole new RED in the keeps module; the parametrized wrap/transport pins do
NOT error at HEAD because get_or_create_keyed is not yet in the DERIVED param set). On the GREEN build
its CREATE/RELATE lands it in `_WRITE_PATHS` → the equality holds and the 3 parametrized pins
(coverage + rejection-wrap + transport-propagate) exercise it via the map entry I added.

## §FLAGS — FLAG 1 + FLAG 2 (retrofit module), applied verbatim from contract-63a-4 §FLAGS

- **FLAG 1** — `test_memory_retrofit_63a.py` module docstring: the stale FORK-5 paragraph teaching the
  REJECTED Reading B ("The design's stated shape is `capability=`") REPLACED with the §10.5-CONFIRMED
  text (Reading A: typed `subject=` at the BACKEND, `capability` at the TOOL layer). Verified: no
  residual "resolved to a Subject inside" / "stated shape is capability" anywhere in the tree.
- **FLAG 2** — every pin's `alice_capability: str` / `bob_capability: str` → `: _Credential` (the
  fixture yields `_Credential`). Verified: no `capability: str` annotation remains.

## §PROSE — §9-rider-9 BARE prose-currency sweep (every hit a file:line + verdict)

| pattern | hit | verdict |
|---|---|---|
| `owner_principal_of` | `owner_stamp.py:85`, `agents.py:954` | **LIVE code the 63a builder DELETES** (#425 §10.3 §5); pinned by the 63a #425 module (adversary §P6b). Correctly present at HEAD — not stale prose. |
| `owner_principal_of` | design doc lines 529/534/647/656/689/743 | **the design's OWN ruling** prescribing the deletion. Must NOT edit (brief). Correct. |
| `owner_principal_of` | `receipts/2026-08-24-packet62/*` (7 hits) | **ARCHIVED dated packet-62 receipts** of the pre-#425 world (the R4 forward-note even predicts the #425 close). Correctly dated — not a current claim; archived, not edited. |
| "free-form (created_by/actor/agent)" | `surreal_schema.py:548`, `server.py:1478` | **DIFFERENT concept** — "free-form agent text" = the `declared_cadence` value's format, unrelated to the §7 author-provenance premise. Correct, not stale. |
| "free-form created_by" | design doc:689 | the sweep-rule definition itself. Must not edit. Correct. |
| "capability= at the backend" / "resolved inside" (Reading B) | **ZERO** | FLAG 1 removed the one stale served-prose instance. Clean. |
| "no governed tool routes" | design doc:689 (rule), `packet61-...:533,559` | packet-61's DATED ruling ("At 61 … yet … that is 63/64") — correctly time-scoped, archived design. Correct. |

**Conclusion:** every retired-premise hit is (a) live code the builder deletes (pinned), (b) a design
doc's own ruling (must not edit), (c) an archived dated receipt, or (d) a different concept. No stale
CURRENT served surface needs a contract-author edit; FLAG 1 already cleared the one that did.

## §DRY — reuse ledger (2 new reusable symbols)

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `StoreHandle` (prod, `store/_txn.py`) | `lore_search("connection owner acquire drop url handle triple driver seam store injected")` | NO existing `StoreHandle`; the closest is the `(acquire, drop, url)` triple `run_query`/`execute_transaction` already take as SEPARATE kwargs (`_txn.py`) | **HAND-ROLLED** — a frozen data-carrier BUNDLING the existing driver-seam params (design §10.6 ruled minting it; §8 deferred the shape to BLOCKER 2). The adversary's `run_governed_query(connection,…)` shim is the WRONG direction (raw connection). |
| `store_handle` (test, `_governed_contract.py`) | same search (test tree) — no test helper builds a StoreHandle | the sibling `apply_ddl` `_acquire`/`_drop`-closure idiom in the SAME file | **EXTENDED** the `apply_ddl` closure idiom — same acquire/drop-closure shape, now returning a StoreHandle + an acquire counter/hook (the rider iii/iv instrument). Test-local convenience, not shared production policy. |

## §MUTATION — mutation-proof plan per new pin (and a self-caught vacuous pass)

- **rider (i) LEG 1 (row_count==1 from RETURN):** on a no-handle/dead-seam build the positive control
  fails (can't reach the store to read back 1) → the pin can no longer FALSE-PASS on the raised
  GovernedConflict in LEG 2. Proven by construction (the adversary's R6/§P2 false-pass is closed).
- **rider (ii) leg B (ZERO audit):** a separate-round-trip audit build appends +1 → before≠after →
  RED. ⚠ **SELF-CAUGHT (fixtures-must-discriminate):** my first draft used a bare
  `pytest.raises(Exception)`, which SWALLOWED the unbuilt-stub `NotImplementedError` and left
  `before==after` TRUE trivially — a VACUOUS PASS at HEAD (observed: it passed). Fixed with a
  `not isinstance(rejection.value, NotImplementedError)` guard → now RED-until-built (verified). The
  "what WRONG build still passes this?" question caught it: the unbuilt stub did.
- **rider (iii) TOCTOU:** a read-then-write build with a TOCTOU window writes on the moved row →
  `note_text != 'original'` → RED. The re-scope is landed deterministically via `on_acquire(2)`.
- **rider (iv) counting-acquire:** a build hand-rolling `connection.query` inside guarded_write
  observes 0 acquires → `calls['acquire'] >= 1` reds. (Belt-and-braces with the R4 AST + runtime guard.)
- **R4 AST pin:** paired with its positive control (flags a synthetic `query_raw`) so a mis-derived
  empty method set cannot pass it vacuously.
- **corpse B:** LEG B reds a build re-routing stamp_owner through `verify_capability`.
- **corpse C:** the DERIVED `_WRITE_PATHS` growth reds the coverage-map equality until the map matches.

## §DEVIATIONS

1. **migrate_governed StoreHandle (R4) — FLAGGED, not edited (out of writable set).** Design §10.6 R4
   rules `migrate_governed` takes the SAME StoreHandle. `migrate_governed` lives in
   `loremaster/loremaster/principals.py`, which is NOT in my writable set. I reshaped the governed.py
   half (`report_unmigrated_governed_rows` → StoreHandle, and its migration-test call site) but left
   the migration test's `migrate_governed(connection=connection)` calls unchanged (a clean
   NotImplementedError RED against the current principals.py stub; changing the test alone would make
   it a TypeError RED). **Exact coordinated edit for the builder/lead:**
   - `principals.py::migrate_governed` — signature `connection=<conn>` → `store: StoreHandle` (import
     from `loremaster.store._txn`); route the backfill UPDATE + count through `run_query`/
     `execute_transaction` over `store.acquire/drop/url`.
   - `test_governed_migration_63a.py` — `_migrate_memory` + `test_migrate_message_before_agent_refuses`:
     `connection=connection` → `store=store_handle(connection, url=<env>.url)[0]`.
   - **Interim enforcement:** the AUTOUSE `_sdk_guard` ALREADY reds a hand-rolled `connection.query`
     in migrate_governed's EXECUTED paths, so the driver-routing BEHAVIOUR is guarded regardless; the
     signature change is R4 design-consistency. Not a blocker to the build.
2. **PRE-EXISTING broad-catch vacuous pass (surfaced, not my code):**
   `test_governed_substrate_63a.py::TestResolveSubjectIsFailClosed::test_a_keep_resolution_failure_
   denies` uses `pytest.raises((GovernedDenied, Exception))`, so it PASSES at HEAD by catching the
   `resolve_subject` stub's `NotImplementedError` — GREEN-at-HEAD when it should be RED-until-built. I
   did NOT author it and did NOT edit it (outside the fold). Low priority (it does verify the deny path
   on a correct build), but it is a fixture-discrimination weakness the builder/adversary may want to
   tighten (mirror my rider-ii `not isinstance(..., NotImplementedError)` fix).

## §COUNT — RED/GREEN/ERROR + full reconciliation

**The 7 `test_*_63a.py` modules** (⚠ the brief says "8 modules"; only SEVEN `test_*63a.py` files exist
— I ran all 7 + the 2 corpse modules + the regression sweep):

`pytest -n auto` (TEST store ws://127.0.0.1:18000): **57 failed / 17 passed / 11 errors = 85** (tail
pasted below in §GATES).

Reconciliation vs predecessor (contract-63a-4 §COUNT: **54F / 15P / 11E = 80**):
- +5 tests (substrate): rescope (RED), rejected-mutation (RED), R4 AST pin (GREEN), R4 control (GREEN),
  accessor pin (RED); the vanished-conflict was reshaped in place (already in the 54).
- Fails 54→57 (+3 new RED: rescope, rejected-mutation, accessor). Passes 15→17 (+2 GREEN: R4 AST +
  control). Errors 11→11 (the `retrofit_world` get_or_create_keyed setup errors — HONEST, unchanged).
- 80 + 5 = 85 ✓ (57+17+11).

**Corpse modules** (`test_agent_capability_seams` + `test_keeps_store`): **2 failed / 78 passed** — the
2 failures are EXACTLY the corpse B re-key + corpse C coverage-map pin, both RED-until-built (expected
per brief). No collateral regression in those modules.

**60/61/62 regression sweep** (8 changed-surface modules: retry_seam, memory_backend, memory_cutover,
mcp_server, agent_capability, engine_rejection_seam, surreal_store, audit_store): **1776 passed / 0
failed, exit 0** — the additive stubs (`StoreHandle`, `guarded_write` store= param, report_unmigrated
stub, `backend.handle` stub) regress nothing.

## §GATES — receipts (tails)

- `uv run ruff check .` → `All checks passed!` (exit 0).
- `bash scripts/typecheck.sh` → all members OK (lorerunes/lorescribe/loresigil/loremaster 249 files/
  skills/docs·eval/scripts + shellcheck), exit 0.
- 7×`_63a` `pytest -n auto`: `57 failed, 17 passed, 11 errors in 10.36s`.
- corpse: `2 failed, 78 passed in 8.27s`.
- regression: `1776 passed, 4 warnings in 155.11s`, exit 0.

**No unrelated failures.** Every RED/ERROR in the 63a + corpse sets is a contract pin RED-until-built
for a verified right reason (guarded_write/handle/read_filter/resolve_subject/migrate/schema stubs,
the get_or_create_keyed keyed-mint, the #425 shared pair-path); the regression sweep is fully green.
