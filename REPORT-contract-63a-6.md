# REPORT-contract-63a-6 — close 2 deviations: migrate_governed R4 signature + vacuous-pass tighten (RED)

- `brief-base v14 read`
- `brief project v7 read`
- store reference: `docs/reference/surrealdb-31-capabilities.md` — NOT consulted for a store/schema/DDL
  change. Neither edit touches the store, schema, or DDL: DEV 1 is a production-STUB signature reshape
  (body stays `NotImplementedError`); DEV 2 is a test-assertion narrow. The routing the docstring
  describes (run_query / execute_transaction over a StoreHandle) is the design §10.6 R4 ruling, cited.

## SUMMARY BLOCK

- Receipt: `brief-base v14 read` · `brief project v7 read`
- **STATE: done** — both contract-63a-5 deviations closed; contract kept runnable-RED. Count moved by
  exactly the predicted small delta (DEV 2 flips one vacuous GREEN → RED-until-built; DEV 1 is
  count-neutral). No existing pin weakened; no new fork.
- Deviations (from MY run): none. (I closed the two contract-63a-5 flagged as §DEVIATIONS.)
- **DEV 1 (§10.6 R4, latent C-DEF):** `principals.py::migrate_governed` signature `connection: Any` →
  `store: StoreHandle`; the two migration-test call sites → `store=store_handle(conn, url=env.url)[0]`.
  A §10.6-R4-compliant build no longer false-reds on a `TypeError` (proven, §DEV1-PROOF).
- **DEV 2 (pre-existing vacuous pass):** `test_a_keep_resolution_failure_denies` broad
  `pytest.raises((GovernedDenied, Exception))` → narrowed to `pytest.raises(governed.GovernedDenied)`
  (matches its two sibling deny pins) — reds the stub build, keeps the positive intent (§DEV2).
- **Packages considered:** none — no mechanism specified (a production-stub signature reshape + a test
  narrow; §10.6 already adjudicated the migration verb `bespoke` and minted `StoreHandle`).
- **Reuse ledger:** none — no NEW reusable symbol introduced. Both edits REUSE symbols contract-63a-5
  already minted: prod `StoreHandle` (`store/_txn.py`) and the test seam `store_handle`
  (`_governed_contract.py`). No new helper/predicate/constant. (§DRY)
- **Graded:** n/a — I authored no verdict on another artifact; this is a contract fix. Base HEAD
  `a88b08e` (the sha the brief named); my 3 modified files == the writable set.
- **Decisions-needed:** none new.
- Receipt POINTERS: DEV 1 edits → §DEV1; its coupling mutation-proof → §DEV1-PROOF; DEV 2 → §DEV2;
  count delta + reconciliation → §COUNT; right-reason tracebacks → §RIGHT-REASON; gates → §GATES.

---

## §DEV1 — migrate_governed takes the SAME StoreHandle (design §10.6 R4)

**The latent C-DEF (contract-63a-5 §DEVIATIONS item 1):** design §10.6 R4 rules `migrate_governed`
takes the SAME `StoreHandle` as `guarded_write` / `report_unmigrated_governed_rows` — never a raw
connection. But `migrate_governed` lived in `principals.py` (OUT of contract-63a-5's writable set), so
its signature stayed `connection: Any` while the migration tests still called `connection=connection`.
On a §10.6-R4-compliant build (signature `store: StoreHandle`), those test calls would `TypeError`
(unexpected `connection=`) — a false-red for the WRONG reason, trapping the builder. `principals.py`
is in MY writable set, so I closed it.

Three edits (all mechanically coupled — the signature and both call sites move together):

1. `loremaster/loremaster/principals.py` — added `StoreHandle` to the existing runtime import from
   `loremaster.store._txn` (isort-clean, ruff `I` green). Changed `migrate_governed`'s parameter
   `connection: Any` → `store: StoreHandle`; extended the docstring with the R4 routing note (the
   backfill UPDATE + §2.6 agent-NONE-count route through `run_query` / `execute_transaction` over
   `store.acquire` / `store.drop` / `store.url` — no raw connection, no direct SDK call in
   `governed`/`principals`; the verb borrows the target store's own retry/self-heal driver). **The
   STUB body is unchanged** — still `raise NotImplementedError(...)` (I author no migration LOGIC);
   only the error string gained ` / §10.6 R4`. `report_unmigrated_governed_rows` was already reshaped
   to `StoreHandle` by contract-63a-5; this makes its sibling `migrate_governed` consistent.
2. `loremaster/tests/test_governed_migration_63a.py::_migrate_memory` — unpacked `_env` → `env`,
   call `migrate_governed(..., store=store_handle(connection, url=env.url)[0], ...)` (the shipped
   `store_handle` seam builds a `StoreHandle` over the fixture's admin connection; `[0]` is the
   handle, `[1]` the acquire-counter I don't need here). Added a 3-line comment stating the R4 reason.
3. `test_migrate_message_before_agent_refuses` — same call-site swap; `env` was already unpacked in
   that test body, so `store_handle(connection, url=env.url)[0]`.

`migrate_governed` has NO production callers (grep: only these two test files call it; the CLI-verb
pin only exercises `build_parser()`, not dispatch), so the signature change breaks nothing else. No
CLI dispatch handler yet routes to it (that is builder work).

### §DEV1-PROOF — the coupling closes a REAL latent C-DEF (non-destructive mutation-proof)

`uv run python` introspection over the reshaped signature:
```
migrate_governed params: ['table', 'store', 'keep_store', 'principal_store', 'registry', 'dry_run']
  -> store present, connection absent: OK (§10.6 R4)
  -> OLD connection= call now TypeErrors (the latent C-DEF the coupling closes):
     migrate_governed() got an unexpected keyword argument 'connection'
```
The un-coupled world (R4 signature + a test still passing `connection=`) TypeErrors BEFORE the stub
body — the false-red the deviation names. After my coupling, both migration tests reach the stub body
(§RIGHT-REASON), so a correct §10.6-R4 build will pass them on the merits, not trip a signature
mismatch. This is "prove which failure you have": the RED is the unbuilt LOGIC, never the wiring.

## §DEV2 — the pre-existing vacuous pass, tightened (contract-63a-5 §DEVIATIONS item 2)

`test_governed_substrate_63a.py::TestResolveSubjectIsFailClosed::test_a_keep_resolution_failure_denies`
caught `(governed.GovernedDenied, Exception)`. At HEAD `resolve_subject` is a stub →
`NotImplementedError` (a subclass of `Exception`) → the broad catch SWALLOWED it → the test **passed
at HEAD** (a vacuous GREEN when it should be RED-until-built). Verified: at contract-63a-5's baseline
this test was in the 17 PASSED bucket.

**Fix — narrow to the intended type** (the brief's second option; chosen over the
`not isinstance(..., NotImplementedError)` guard because it is STRICTER and matches the two sibling
deny pins): `with pytest.raises(governed.GovernedDenied):`, and dropped the now-dead
`subject = ...`/inner `assert subject is None` and the inapplicable `# noqa: B017,PT011` (B/PT/RUF are
not in ruff's `select`, so the noqa was already a no-op). The class + test docstrings already say the
intended fate is GovernedDenied SPECIFICALLY (design §1.2 item 1), so the narrow is faithful.

**"What WRONG build still passes this?" — interrogated in every direction (narrow catch):**
- stub build (`NotImplementedError`) → not `GovernedDenied` → propagates → RED. ✓ (the vacuous pass is dead)
- build that lets the raw `KeepStoreError` propagate (fails to WRAP as fail-closed) → not `GovernedDenied` → RED. ✓ (stronger than the old broad catch, which passed it)
- build that swallows the resolver error into a `Subject` (no raise) → `pytest.raises` fails "DID NOT RAISE" → RED. ✓
- correct build (keep-resolution failure → `GovernedDenied`) → caught → GREEN. ✓ (positive intent kept)

⚠ The OLD broad form was doubly weak: the inner `assert subject is None` (on a swallowing build) raised
`AssertionError`, itself an `Exception`, which the broad catch ALSO swallowed → the exact
error-swallowing build the test exists to catch could pass. The narrow closes that too.

## §COUNT — RED/GREEN/ERROR + reconciliation (7 `test_*_63a.py` modules, TEST store ws://127.0.0.1:18000)

`pytest -n auto` over the 7 `_63a` modules → **58 failed / 16 passed / 11 errors = 85** (tail in §GATES).

Reconciliation vs predecessor (contract-63a-5 §COUNT: **57F / 17P / 11E = 85**):
- **DEV 2:** `test_a_keep_resolution_failure_denies` flips PASSED → FAILED (vacuous GREEN → RED-until-built):
  failed 57 → 58 (+1), passed 17 → 16 (−1). ✓
- **DEV 1:** count-NEUTRAL. Before, the migration tests reddened via `NotImplementedError` on the
  `connection: Any` stub; after, they redden via `NotImplementedError` on the `store: StoreHandle` stub
  — same bucket (failed), same reason class (unbuilt logic), just now on the R4-correct call shape.
- errors 11 → 11 (the `retrofit_world` `get_or_create_keyed` setup errors — untouched). Total 85 → 85.

## §RIGHT-REASON — the three directly-affected tests, RED for the RIGHT reason (`--tb=line`)

```
tests/test_governed_substrate_63a.py::...::test_a_keep_resolution_failure_denies
  E  NotImplementedError: 63a builder: resolve_subject (design §1.2 item 1)
  loremaster/loremaster/governed.py:94
tests/test_governed_migration_63a.py::...::test_the_verb_backfills_the_project_keep_scope
  E  NotImplementedError: 63a builder: migrate_governed backfill verb (design §1.2 item 5 / §10.6 R4)
  loremaster/loremaster/principals.py:1016
tests/test_governed_migration_63a.py::...::test_migrate_message_before_agent_refuses
  E  NotImplementedError: 63a builder: migrate_governed backfill verb (design §1.2 item 5 / §10.6 R4)
  loremaster/loremaster/principals.py:1016
```
- DEV 2: reds because `resolve_subject` is a stub — the narrowed `pytest.raises(GovernedDenied)` no
  longer swallows the `NotImplementedError`. RED-until-built.
- DEV 1: BOTH migration tests red **inside the stub body** (`principals.py:1016`), **NOT** a
  `TypeError` — confirming `store=store_handle(...)[0]` is accepted by the new `store: StoreHandle`
  signature and the reshaped call site reaches the unbuilt logic. RED-until-built, right reason.

## §DRY — no new reusable symbol

No new helper/retry/predicate/classifier/constant/format-render routine introduced. Both edits REUSE
symbols contract-63a-5 minted and shipped at `a88b08e`:
- prod `StoreHandle` — `loremaster/loremaster/store/_txn.py` (imported into `principals.py`).
- test seam `store_handle` — `loremaster/tests/_governed_contract.py` (already imported by
  `test_governed_migration_63a.py`; I added no import).

So there is nothing to disposition — the DRY search that would precede a NEW symbol does not apply.

## §GATES — receipts (tails)

- `uv run ruff check .` → `All checks passed!` (exit 0). (`StoreHandle` import isort-clean; the
  dropped `# noqa` needed no RUF100 handling — RUF not in `select`.)
- `bash scripts/typecheck.sh` → all members OK (lorerunes/lorescribe/loresigil/loremaster 249 files +
  skills/docs·eval/scripts + shellcheck), exit 0. The `store: StoreHandle` annotation typechecks.
- 7×`_63a` `pytest -n auto`: `58 failed, 16 passed, 11 errors in 11.50s`.
- Corpse modules (`test_agent_capability_seams` + `test_keeps_store`): `2 failed / 78 passed` — the 2
  failures are EXACTLY contract-63a-5's corpse-B (`test_stamp_owner_routes_through_the_shared_verify_
  capability_owner`) and corpse-C (`test_the_derived_write_path_set_matches_the_coverage_map`)
  RED-until-built pins, both in modules I did NOT touch. No collateral.
- Regression (principals store/schema/cli · agent_capability + reach · memory_backend + memory_cutover):
  **289 passed / 0 failed** in 15.75s — the `migrate_governed` signature/docstring change (no
  production callers) regresses nothing; `principals.py` imports and functions cleanly.

**No unrelated failures.** Every RED/ERROR in the 63a + corpse sets is a contract pin RED-until-built
for a verified right reason (resolve_subject / migrate_governed / guarded_write / read_filter / schema
stubs, the get_or_create_keyed keyed-mint, the #425 shared pair-path). The regression sweep is fully
green.
