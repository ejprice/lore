# REPORT — coldaudit-61a-w4 · cold REFUTE audit of the append-only `audit` store substrate

brief-base v14 read
brief project v7 read
store reference read (`docs/reference/surrealdb-31-capabilities.md` — cited by §: §1.1 FIELD
`OVERWRITE`/#107, §1.4 greenfield, §2 `record<>` links do NOT auto-clean on target delete +
explicit-projection-reads-None, §3 `execute_transaction` verifies every statement, §4 RELATE/
dangle semantics)

## SUMMARY BLOCK
- **State:** done. **VERDICT: GO** (commit + close 61a). The 61a-w4 build (new `AuditStore` +
  the `audit` schema slice + the 2 authorized tripwire edits) is correct, faithful to Fork G +
  the §9 addendum, and its append-only + identity-at-write properties are independently
  re-derived by construction — not merely re-run.
- **Deviations:** none. I edited NO real-tree file; wrong-build mutation done in a disposable
  provenance-asserted `/tmp` scratch only (git status identical to session start).
- **Packages considered:** none — a cold audit specifies no mechanism. (Build's own choices
  re-verified: `ulid.ULID` reused, `_txn` seams reused, no new dep — concur.)
- **Reuse ledger:** none — I introduced no production symbol (audit only).
- **Graded:** `e92bd0f` · HEAD-at-report `e92bd0f` · SAME (wave uncommitted; the lead commits).
- **Decisions-needed:** none. (The currency gate false-RED'd once under concurrent load — known
  #405 — then **PASSED clean on the truly-solo re-run**; see §Gates / R1.)
- **Receipt pointers:** gate table → §Gates; the 6 load-bearing checks → §Checks; the controlled
  mutation table (with `__file__`) → §Mutation; residuals → §Residuals.

---

## VERDICT: **GO** — commit the wave and close 61a.

Every changed-scope gate is green (independently re-run), the two security-critical properties
(Layer-1 append-only surface; §9 identity-at-write) are re-derived **by construction** and shown
to **discriminate** their wrong builds, the 61a/61b boundary held, and both authorized tripwire
edits are faithful (not weakening). The one transient red — the currency gate under concurrent
load — was the lead-filed KNOWN false RED_ORPHANED (#405, `test_migration_wire.py`); the
**truly-solo currency re-run PASSED clean**. Nothing blocks the commit.

---

## Gates (all re-run by me at `e92bd0f`; counts pasted)

| gate | command | result |
|---|---|---|
| w4 contract (76 pins) | `pytest test_audit_schema.py test_audit_store.py -p no:xdist` | **76 passed** in 5.06s |
| typecheck (all members) | `./scripts/typecheck.sh` | **0** — loremaster `no issues found in 231 source files`; every member OK; shellcheck OK |
| ruff | `uv run ruff check .` | **All checks passed!** |
| w3 fold-guard | `pytest test_schema_fold_coverage.py -p no:xdist` | **29 passed** (audit slice folded, no #410 prose trap) |
| w2 shape-guard | `pytest test_engine_rejection_seam.py -p no:xdist` | **56 passed** (`audit.py` born-wrapped, no clone) |
| tripwires + guards bundle | `pytest test_schema_fold_coverage + test_engine_rejection_seam + test_principal_keys_schema + test_retry_seam -p no:xdist` | **783 passed** (1 pre-existing scout-subscription RuntimeWarning, unrelated) |
| full suite | `pytest loremaster/tests -n auto` | **8563 passed / 2 failed / 9 errors** — ALL 11 anomalies are `test_migration_wire.py` (xdist-hostile HTTP wire-smoke); **14/14 GREEN solo** ⇒ effective **8574 passed / 0 failed** (matches the builder's solo-serial 8574/0) |
| currency (concurrent) | `pending_contract_gate.py --currency` (overlapping the bg full-suite + scratch uv-sync) | typecheck GREEN · ruff GREEN · **pytest RED_ORPHANED — 9 residuals, ALL `test_migration_wire.py`, no owner** → known #405 false-red under load |
| currency (**SOLO**) | `pending_contract_gate.py --currency` (nothing else running) | **PASS — typecheck GREEN · ruff GREEN · pytest GREEN** (the #405-predicted clean solo result) |

The full suite's only failures were confined to ONE out-of-scope module; per the brief's
"scattered out-of-scope ⇒ re-run solo" I re-ran `test_migration_wire.py` solo → **14 passed** in
26.5s. The 11 anomalies are the exact xdist-triggered uvicorn-boot flake finding #405 names as
mechanism #3. I did NOT burn 38 min re-running the whole 8574-test suite serially to clear 11
already-isolated-and-cleared flaky nodes; the anomalies are fully explained.

---

## Checks (the REFUTE — each independently re-derived, not trusted from the reports)

### 1. APPEND-ONLY, Layer 1 (the security half w4 owns) — CONFIRMED, allowlist-the-safe
Independently resolved `AuditStore`'s public callable surface across its FULL MRO
(`inspect.getmembers`): `AuditStore.__mro__ == [AuditStore, object]`; reachable public members =
**`{append, append_fragment, close, ensure_ready}`** — NOTHING beyond the safe allowlist, no
mutator own OR inherited. Full callable set incl. private = `{_drop_connection, _ensure_connection,
_safe_close, append, append_fragment, close, ensure_ready}` — no `update`/`delete`/`set_*`/`upsert`/
`purge` anywhere. Built a base carrying `purge` **AND a novel `obliterate`** (NOT in the contract's
`_FORBIDDEN_MUTATOR_NAMES`): a leaf inheriting it shows `{obliterate, purge}` beyond the allowlist
→ the surface pin **reds**. Proves the pin is allowlist-the-safe over the resolved surface, not a
name blocklist (#344/#345 satisfied).

### 2. IDENTITY-AT-WRITE §9 (the load-bearing forensics property) — CONFIRMED by construction
`actor_email`/`actor_agent_name` are DENORMALIZED required non-empty **string VALUE** columns
(`_CHUNK_STRING_TYPE` + `_NON_EMPTY_STRING_ASSERT`), caller-provided kwargs, bound as `$audit_email`/
`$audit_agent_name` VALUEs — NOT fetched, NOT links. Two engine facts probed live on
`ws://127.0.0.1:18000` (a probe needs a control — both carry one):
- **FACT 1 (lazy-derive is impossible):** `DEFINE FIELD … VALUE <future>{ actor_principal.email }`
  is a **PARSE ERROR** on 3.2.4 (`Unexpected token, expected a kind name`). A read-time-lazy field
  is not constructible → no lazy-derive build that passes the contract can exist (confirms the
  adversary's measurement).
- **FACT 2 (the §9 guarantee):** wrote an audit row linking a real principal, then hard-DELETEd the
  principal. Post-delete: `actor_email` VALUE **survived** (`victim@example.com`); the
  `actor_principal` link still held the now-dangling `RecordID(principal, p_del)` (store §2 — record
  links do not auto-clean); its deref (`actor_principal.email`) → **None**. Exactly §9: the human
  identity survives as a VALUE while the link dangles.
- **Controlled mutation (link-only build):** in the scratch, dropped the two denormalized columns
  from the schema specs AND from the write. Correct build → the 2 identity pins **PASS**; link-only
  build → both **FAIL** with `assert None == 'compromised-admin@example.com'`. The pin genuinely
  discriminates a link-only build (see §Mutation).

### 3. DANGLE-TOLERATED cascade (the ruled policy) — CONFIRMED, tripwire ARMED
Independently derived every `record<principal>`/`record<agent>` link across the WHOLE folded
`generate_ddl`:
- `record<principal>` = **exactly 3**: `(actor_principal, audit)`, `(keeper, keep)`,
  `(principal, principal_key)` — EXACTLY the tripwire's expected set.
- `record<agent>` = **1**: `(actor_agent, audit)`.
The tripwire (`test_..._matches_the_cascade_adjudication`) asserts `found == expected` over the 3,
each CLASSIFIED (cascade / refuse / dangle) — a synthetic 4th `record<principal>` link makes
`found != expected` ⇒ **RED**, so it stays armed for 63/64's `owner_principal`. NO audit-row
cascade/refuse is pinned (immutable history outlives its actors — the ruled §9 disposition). The
`actor_agent` policy (dangle-tolerated, moot: agents retired-not-deleted) is documented with a
named re-open trigger; correctly NOT enumerated as an exact-set pin (would drag the comms
subsystem's common `record<agent>` links into scope — sidecar addendum, concur).

### 4. BORN-WRAPPED + composable fragment — CONFIRMED
`AuditStore.append` wraps its `execute_transaction` in `wrap_store_rejection(AuditStoreError, …)`
— the ONE #400 seam (`passthrough=(SurrealConnectionError, TxnContentionExhaustedError)`,
`catch=(SurrealStoreError,)`, delegating control-flow to `lorerunes.reclassify`). So a raw store
rejection wraps LOUD; transport/exhausted-contention pass through untouched. NOT a hand-rolled
full-#400 clone (w2 shape-guard 56 GREEN confirms). `append`'s write **IS**
`compose(self.append_fragment(...))` (ONE path — read in source, and the contract's
statement-equality pin covers it). `append_fragment` is a single-statement `CREATE` with NO
`BEGIN`/`COMMIT`, params namespaced `audit_*` — composable into 63/64's atomic
`execute_transaction` (POSITIVE + NEGATIVE atomicity pins in the 76). #411 byte-identical-clone is
an accepted bound (not re-flagged).

### 5. The 2 tripwire edits are LEGITIMATE (not weakening)
- **`test_retry_seam.py`:** `AuditStore` added as a REAL `_EXECUTE_TRANSACTION_OWNERS` entry with
  its OWN driving pin (`test_each_execute_transaction_owner_logs_ITS_OWN_url_on_bootstrap_exhaustion`)
  AND added to the pairwise-distinct url list AND the `driven` coverage set — coverage stays a
  CHECKED variable (the scan's `scanned` set includes `audit.py`'s `bootstrap_session` call; it is
  now `driven`, so `test_every_owner_the_scan_finds_is_DRIVEN_here` counts it). Verified
  independently: `AuditStore` has **no `_query`** (its writes thread url via `execute_transaction`),
  so no dead `_query` was added. Not a widened exclusion.
- **`test_principal_keys_schema.py`:** the exact-set pin now classifies 3 links (was 2) with the
  dangle rationale inline; it ADDS a classified link, does not remove/loosen an assertion. The
  classification is faithful (each disposition matches the ruled principle). Still armed.

### 6. BOUNDARY (61a/61b) + #410 — CONFIRMED
- Grepped the wave's production files for `requires_audit|authorize|carve|Decision|credential|
  governed-table|PDP|owner_principal`: every hit is DOCSTRING prose describing what is deferred to
  61b (the Layer-2 threat model, the `signin_credentials` store login). ZERO PDP logic, ZERO 61b
  pins in the contract files. The audit slice emits **0 `DEFINE INDEX`** (Fork G defers). No
  `requires_audit`/carve-out/credential/governed-table retrofit snuck in.
- **#410:** scanned the `_audit_statements` def + docstring + leading lines for the w3 guard's
  `KNOWN_EMPTINESS_PHRASES` (`emit []`, `emits nothing`, `red stub`, `not folded`, `do not
  implement`, `raises notimplementederror`) → **NONE**. The builder built the slice fresh (no stub
  comment to retire); the fold-guard's prose backstop stays GREEN.

Spec fidelity: the build matches every core Fork G ruling (field set, `ulid()` id, fold-after-
`member_of`, deferred indexes, SCHEMAFULL/`OVERWRITE`, append-only Layer-1 surface, threat model,
composable `TxnFragment`, born-wrapped) + the §9 addendum.

---

## Mutation table (controlled; provenance-asserted disposable scratch, real tree untouched)

`loremaster.__file__` = `/tmp/lore-coldaudit-61a-w4/loremaster/loremaster/__init__.py` (#140 —
INSIDE the scratch; all 4 workspace members resolve inside it). Real-tree `git status` identical
to session start throughout (I never edited a real-tree file; the scratch is disposable, no
restore needed).

| build | pins run | result |
|---|---|---|
| CONTROL — correct scratch build | `TestTheDenormalizedIdentitySurvivesActorDelete` (2 pins) | **2 passed** |
| WRONG — link-only (denormalized columns dropped from schema specs + write) | same 2 pins | **2 failed** — `assert None == 'compromised-admin@example.com'` (§9 identity lost after principal-delete) |

This is the operator-ratified §9 property, independently mutation-proven to discriminate. (FACT 1
above independently forecloses the lazy-derive wrong build — it is un-constructible on 3.2.4.)

---

## RESIDUALS

1. **Currency close-out gate: PASSED solo; false-RED once under concurrent load (finding #405) —
   RESOLVED, non-blocking.** My FIRST currency run (which overlapped the background full-suite
   `-n auto` + a `scratch_copy` uv-sync — heavy concurrent load) reported `pytest RED_ORPHANED` with
   9 residuals, **every one a `test_migration_wire.py` node**: the gate's mandated `-n auto` pytest
   leg tripped the module's xdist uvicorn-boot flake (finding #405, mechanism #3). The **truly-solo
   re-run (nothing else running) PASSED clean** — typecheck/ruff/pytest all GREEN — exactly as #405
   predicts ("the truly-solo currency re-run = PASS"). Corroborated independently: `test_migration_
   wire.py` is **14/14 GREEN solo**, and the wave touches no HTTP transport. So the currency gate IS
   citable as GREEN for this close-out (solo), and the transient red was concurrent-load #405, not a
   wave defect. No lead decision required; #405 remains the lead's open ledgered test-infra item (its
   deeper fix — xdist-serial the heavy/boot tests — waits for CI, where currency becomes job 1).
2. **Immaterial prose count (non-blocking):** `audit.py`'s `append` docstring calls itself "the 9th
   consumer of finding #400's ONE seam" while Fork G calls `AuditStore` "the 3rd store to wrap
   engine rejections." These scope different things (methods routing through `wrap_store_rejection`
   vs store classes), so they are not contradictory — but "9th" is an unverified descriptive ordinal
   on a natural-language surface no gate checks (the P8d class). Behaviour is unaffected (the w2
   shape-guard proves the routing regardless of the ordinal). Not worth a fix; flagged for
   completeness.
3. **Pre-existing RuntimeWarning (not a defect):** `test_retry_seam.py::…_scouts_live_subscription_
   is_retried` emits `coroutine '_empty_subscription' was never awaited` — a pre-existing
   scout-subscription warning unrelated to the wave (the builder noted it too).
4. **Disposable scratch to reap:** `/tmp/lore-coldaudit-61a-w4` (mine, provenance-asserted
   `scratch_copy`, NOT a git worktree, no uncommitted real-tree state) — safe for the operator to
   `rm -rf`. The contract author's `/tmp/lore-sat-61a-w4{,b}` and the adversary's
   `/tmp/lore-adv-61a-w4` are likewise safe to delete.

## Adversary/contract residuals reviewed (no new finding)
- Fragment-routing Build-E1 (byte-identical clone passes the text-equality pin at ship, drift-
  protected): the SHIPPED build routes correctly (`append = compose(self.append_fragment(...))`),
  so the residual is theoretical; adversary accepted it non-blocking; concur.
- `append`-scoped AST pins are over-constrained (would false-RED a helper-delegating refactor): a
  builder-facing note, not a false-green; the shipped build inlines both. Concur.
