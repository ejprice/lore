# REPORT-adversary-63a-2 — CONTRACT-ADVERSARY RE-GRADE of the packet-63a RED contract (satisfiability receipt)

- `brief-base v14 read`
- `brief project v7 read`
- store reference consulted AS NEEDED — `docs/reference/surrealdb-31-capabilities.md` §1.1 (FIELD
  OVERWRITE / INDEX IF NOT EXISTS), §1.4 (option<> on a populated table), §1.8 (UNIQUE over
  option<> = many NONE coexist), §2 (record<> links; CONTENT), §5 (hot-row CAS mint). Cited, never
  re-transcribed.

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT** — the 4 prior pins ARE genuinely closed and the §10.5 reshape
  DOES remove its C-DEF, BUT the satisfiability receipt (the leg the predecessor could not run)
  exposed **2 NEW BLOCKER C-DEFs** that no reasoning pass could see, plus a corpse-sweep gap.
- **P1 headline — reference build result: 76 passed / 4 failed** over the 7 `test_*_63a.py` modules
  (NOT 0-failed). The 4 failures are the 2 C-DEFs below — both **contract/design defects, not builder
  code**. Every other pin (all of retrofit PIN1–4 + §10.5, migration, routing, #425, pdp-none-scope,
  the schema DDL emitter + keep.key, resolve_subject/read_filter/one-Subject) is GREEN on the ruled build.
- **BLOCKER 1 (schema):** `_governed_contract.index_statement` anchors `FIELDS <col>` to end-of-string,
  but the governed-INDEX mutation pin APPENDS `COMMENT '…'` — so `test_the_governed_indexes_route_
  through_the_shared_emitter` reds on a CORRECT `_plain_index` build (schema 23/24). Fix PROVEN → 24/24.
- **BLOCKER 2 (substrate):** `governed.guarded_write(…)` (design §1.2 item 3) carries NO store handle;
  the frozen substrate tests seed a per-test `test_<pid>_<uuid4>` DB and call it with none → 3 pins
  unsatisfiable (+1 FALSE-PASS). guarded_write's logic PROVEN correct given a handle (retrofit routes
  through it 2/2). A design/contract signature fix (design escalation candidate).
- **Prior 4 pins CONFIRMED closed:** retrofit module 19/19 on the ruled build — PIN1 (default project
  scope), PIN2 (invalidate→guarded_write foreign-deny + owner-succeed), PIN3 (scope→_grantable),
  PIN4 (real-recall served-set < unfiltered) all discriminate; the 11 formerly-setup-error tests all GREEN.
- **§10.5 reshape CONFIRMED:** the `_exercise_*` seam resolves capability→Subject via the REAL
  `governed.resolve_subject` and the backend takes `subject=`; no C-DEF, no test-side `Subject()`.
- **Ruled shapes are shipped-compatible:** §10.1 Resource `str|None` + §10.3 #425 additive close pass
  the shipped world (pdp_core + agent_capability = 138 green; verify_capability's 13 call sites intact).
- **CORPSE gap (P6):** the retrofit's identity-less DENY + the #425 routing change falsify shipped pins
  the 63a modules never sweep — 50 test_memory_backend + 2 test_memory_cutover + 1 stamp_owner mutation
  pin + 4 keeps coverage-map pins. See §CORPSE (surfaced, not silently narrowed).
- **Satisfiability receipt:** `loremaster.__file__ = /tmp/adv63a2-ref/loremaster/loremaster/__init__.py`
  (provenance-asserted scratch, `scratch_copy.sh`); 76/80 baseline; BLOCKER-1 fix → 77/80; the other 3
  need BLOCKER-2. Reference build is faithful to §10 + §10.5 (§SATISFIABILITY).
- **Packages considered:** none — no mechanism specified (pure test-contract grade + a reference build
  to ruled shapes; the design already adjudicated the migration verb `bespoke`).
- **Reuse ledger:** n/a — I authored no production symbol for the repo; the reference build lives only
  in scratch and is discarded (all reused existing seams: run_query, resolve_visible_keeps, _grantable).
- **Graded: 8306577 · HEAD-at-report: 8306577 · SAME** (`git rev-parse HEAD` = 8306577; nothing committed).
- Decisions-needed: BLOCKER-2's fix touches the frozen substrate tests + the guarded_write seam SHAPE —
  a contract fix that may want a design ruling on how the seam reaches the store (§BLOCKERS).
- Receipt POINTERS: satisfiability → §SATISFIABILITY; the 2 blockers → §BLOCKERS; prior-4 confirm →
  §PRIOR-PINS; §10.5 confirm → §SEAM; corpse sweep → §CORPSE; quantifier → §P1b; reach → §P1c;
  perturbation → §P2; deletion → §P6b; residuals → §RESIDUALS.

---

## §SATISFIABILITY — the reference build + the 76/80 receipt (the leg the predecessor could not run)

I BUILT the ruled reference implementation in a provenance-asserted scratch copy and ran the REAL
contract against it. `./scripts/scratch_copy.sh /tmp/adv63a2-ref` →
`loremaster.__file__ = /tmp/adv63a2-ref/loremaster/loremaster/__init__.py` (imports resolve INSIDE the
copy — I graded the ruled build, not the original tree; #140).

**What I built, to the §10 + §10.5 ruled shapes (all three §REGRADE builder deliverables + more):**
- §10.1 — `lorerunes.pdp.Resource.scope: str | None`; `__post_init__` admits literal `None`, still
  raises on `""` and every non-domain string (a ONE-line widening; `to_surql` unchanged).
- §4.1 schema — `surreal_schema._governed_field_specs()` (3 option<> columns, no ASSERT/DEFAULT) +
  `_governed_index_statements()` (plain IF-NOT-EXISTS scope + owner_principal, owner_agent NOT indexed),
  WIRED into `_memory_statements`; SF-63-4 `keep.key option<string>` + UNIQUE index in `_keep_statements`.
- SF-63-4 — `KeepStore.get_or_create_keyed` CAS mint (read-by-key → create-with-key+RELATE → re-read on
  UNIQUE conflict).
- §10.3 #425 — `AgentRegistry._verify_capability_owner(presented, token) -> (agent_id, owner_principal_id)|None`
  (the ONE verified SELECT also projects the owner id), `verify_capability` returns its `[0]`,
  `owner_principal_of` DELETED, `stamp_owner` consumes the pair (ONE round-trip).
- §1.2 — `governed.resolve_subject` (the ONE `Subject(` constructor), `read_filter`
  (== authorize_filter(READ).to_surql()), `guarded_write`, `report_unmigrated_governed_rows`.
- §10.2 — `server._GOVERNED_VERBS_ROUTED` (memory) + `_GOVERNED_VERBS_PENDING_ROUTING` (derived from the
  live `_COMMS_ACTIONS`/`_TASK_ACTIONS`/`_FINDING_ACTIONS` dispatch tables, non-empty triggers).
- §10.5 — `LocalMemoryBackend.remember/recall/invalidate(subject=…)` route through the substrate
  (stamp+scope+`_grantable` on write, `read_filter` on read, `guarded_write` on invalidate; identity-less
  → GovernedDenied); `capability=` at the tool + AppContext (ONE shared description), resolved via
  `resolve_subject`.
- §1.2 item 5 — `principals.migrate_governed` (memory scope backfill to the project keep; agent-first
  refusal for message; idempotent) + the `migrate-governed` CLI subparser.

**The receipt (`pytest -n0 -p no:cacheprovider`, TEST store ws://127.0.0.1:18000):**

| module | reference build | note |
|---|---|---|
| test_pdp_none_scope_63a.py | **4 / 4** | §10.1 Resource widening |
| test_425_stamp_owner_63a.py | **4 / 4** | #425 additive close, one round-trip |
| test_governed_routing_63a.py | **7 / 7** | 32 derived verbs; memory routed, 30 pending |
| test_governed_schema_63a.py | **23 / 24** | 1 fail = **BLOCKER 1** (fix → 24/24) |
| test_governed_substrate_63a.py | **8 / 12** | 4 fail = **BLOCKER 2** (guarded_write no handle) |
| test_governed_migration_63a.py | **10 / 10** | backfill + idempotent + agent-first refusal + boot count |
| test_memory_retrofit_63a.py | **19 / 19** | PIN1–4 + §10.5 + identity-less deny + isolation |
| **TOTAL** | **76 / 80** | with BLOCKER-1 fix → 77/80; the other 3 are BLOCKER-2 |

The 11 tests that ERROR at HEAD (get_or_create_keyed stub) all resolve **GREEN** on the ruled build —
the reshape is satisfiable, exactly what the re-grade required.

**Honest bound:** the AppContext capability-PRESENT resolution (§10.5(ii), a full composition-root wire
of the request token + principal/keep stores) is NOT exercised by any 63a pin; my reference build wires
the identity-less DENY (the only 63a-tested tool path) and the shared `capability=` description, and
implements the present branch best-effort (`AppContext._governed_subject`). Stated so this receipt does
not over-claim.

---

## §BLOCKERS — the 2 C-DEFs (each: the defective pin + the defect + the reproduction + the fix)

### BLOCKER 1 — `index_statement`'s end-anchor makes the governed-INDEX mutation pin unsatisfiable
- **Defective pin:** `test_governed_schema_63a.py::TestGovernedIndexesAreEmittedOnMemory::
  test_the_governed_indexes_route_through_the_shared_emitter`.
- **The defect:** `_governed_contract.index_statement` matches `re.search(rf"FIELDS\s+{col}\s*(?:UNIQUE)?\s*$")`
  — anchored to END-OF-STRING. The mutation pin appends ` COMMENT 'gov-index-probe'` to the WHOLE
  DEFINE INDEX statement, so `FIELDS scope` is no longer at the end → `index_statement` returns `None` →
  `assert statement is not None` FAILS on a correct §4.1 build that emits `DEFINE INDEX IF NOT EXISTS
  memory_scope ON memory FIELDS scope` via `_plain_index`. The structurally-identical FIELD mutation pin
  PASSES only because `field_statement` is NOT end-anchored.
- **Reproduction (reference build):** `test_governed_schema_63a.py` → **23 passed / 1 failed**, the sole
  failure this pin (`assert None is not None`). A standalone control proved the mechanism:
  `FIELDS scope$` matches the original but NOT `…FIELDS scope COMMENT 'gov-index-probe'`.
- **The fix (PROVEN → 24/24):** change `index_statement`'s regex from `\s*(?:UNIQUE)?\s*$` to
  `\b\s*(?:UNIQUE\b)?(?!\s*,)` (tolerate a trailing clause; still reject a composite `FIELDS scope, owner`).
  Applied to a scratch copy of `_governed_contract.py` → schema module **24/24**.
- **Class:** a mutation pin that cannot discriminate on the correct build — a "failure message promises a
  check the assertion does not perform" defect one level up, in the shared helper.

### BLOCKER 2 — `governed.guarded_write` has no store handle → 3 substrate pins unsatisfiable
- **Defective pins:** `test_governed_substrate_63a.py::TestGuardedWriteIsSingleBrainOnWrites::
  {test_a_member_write_on_a_foreign_owned_row_denies_and_does_not_mutate,
  test_a_member_write_on_its_own_row_succeeds}` + `TestGuardedWriteComposesAudit::
  test_an_admin_bypass_write_appends_an_audit_row`. (A 4th, the vanished-conflict pin, FALSE-PASSES — below.)
- **The defect:** the frozen contract signature `guarded_write(subject, action, *, table, row_id,
  set_fragment, audit)` (design §1.2 item 3) carries NO connection / store / database. The fixture seeds
  rows in a per-test `test_<pid>_<uuid4>` database (harness `unique_database()` — a random uuid that is in
  NO env var), and all 4 calls pass NO store handle (3 pass `audit=None`; the 4th passes an AuditStore).
  guarded_write cannot read the row it must gate or execute the guarded mutation. No correct build that
  keeps the frozen signature can pass these pins.
- **Reproduction (reference build):** `test_governed_substrate_63a.py` → **8 passed / 4 failed**. The 8
  passing are `resolve_subject` (4), `read_filter` (3), the R-a.2 one-Subject AST pin (1) — so the blocker
  is scoped PRECISELY to guarded_write. `conftest`'s autouse `_sdk_guard` + a filesystem sweep confirm no
  ambient connection/database is available to a `governed.guarded_write` call.
- **PROOF the logic is correct (so this is a HANDLE gap, not a logic gap):** a probe that gives
  guarded_write a driver-routed `query` seam over a seeded row shows **own-row-succeeds (row_count 1,
  mutated), foreign-row-denies (GovernedDenied, unchanged), vanished-row-conflict (GovernedConflict)** — all
  PASS. And the retrofit's `TestInvalidateRoutesThroughGuardedWrite` (2/2) routes real
  `backend.invalidate` → guarded_write through `self._query` and correctly denies bob / lets alice close.
- **FALSE-PASS (fixture-discrimination defect):** `test_a_guarded_write_on_a_vanished_row_raises_conflict`
  PASSES on my reference build because a no-handle call raises `GovernedConflict` — BYTE-IDENTICAL to a
  genuine 0-row guarded mutation. The pin cannot distinguish "guarded_write correctly detected a vanished
  row" from "guarded_write could not reach the store at all." Even after the handle fix, this pin is only
  meaningful once a real store handle is passed.
- **The fix:** give `guarded_write` a store handle — add a `query`/`connection`/store parameter and pass
  it at the 4 frozen substrate call sites AND from the retrofit backend (`query=self._query`), OR make
  guarded_write a method on the memory store. This changes the frozen substrate tests → a CONTRACT-author
  fix, and the seam SHAPE is a design question (how the substrate reaches the store) → design-ruling candidate.

---

## §PRIOR-PINS — the 4 adversary-63a pins are GENUINELY closed (confirmed on the ruled build)

Re-graded EMPIRICALLY (retrofit module 19/19 on the reference build), not by reading the fix report:

- **PIN 1 (C-DEF fix):** `retrofit_world` mints the project keep via `get_or_create_keyed(key='project:lore')`;
  `test_a_remembered_note_defaults_to_the_project_keep_scope` PASSES — a §2.2-compliant build resolving the
  project keep by `SELECT id FROM keep WHERE key='project:lore'` names the SAME keep. No longer a C-DEF.
- **PIN 2 (invalidate→guarded_write):** `test_a_member_cannot_close_a_foreign_owned_row` — bob (not
  householded in the project keep) is DENIED and `valid_until IS None` (double-caught); `test_an_owner_can_
  close_its_own_row` (positive control) — alice closes her own note, `valid_until` set. invalidate genuinely
  routes through `guarded_write(query=self._query)` (not a bare UPDATE).
- **PIN 3 (scope→_grantable):** `test_an_ungrantable_scope_argument_denies_with_a_teaching_error` — alice's
  `remember(scope=keep:<bob's keep>)` DENIES via `_grantable`, message names `lore-adm add-household`;
  the grantable positive control (`scope=principal-private`) is accepted and STORED as that scope.
- **PIN 4 (real-recall served set):** `test_recall_serves_the_caller_filtered_set_not_the_unfiltered_total`
  — alice's recall never contains bob's principal-private row, `served ⊆ alice_visible`, and
  `len(served) < unfiltered_total` (3, measured). Ranking-robust; reds an unfiltered build.

---

## §SEAM — the §10.5 reshape removes the C-DEF (confirmed)

The `_exercise_recall/_remember/_invalidate` seam resolves `capability → Subject` via the REAL
`governed.resolve_subject` (no test-side `Subject(...)`) and calls `backend.<verb>(subject=…)`; the backend
takes `subject: Subject | None`. On the ruled build the whole `retrofit_world` suite reaches its body
assertions (no TypeError), and the F4 hostile-owner leg resolves via the `except TypeError` branch (a
backend that takes a typed Subject and no owner kwarg — §10.5 point 4, accepted). Confirmed: the 11
formerly-erroring `retrofit_world` tests all GREEN.

---

## §P1b — QUANTIFIER TABLE (every invariant: ∀-over-inputs vs guarded-by-known-failure-mode)

| invariant | classification | receipt (reference build) |
|---|---|---|
| F2 READ single-brain (`read_filter` == authorize ∀ subjects, real DDL incl. dirty rows) | **∀-over-inputs** | SOUND — `test_read_filter_equals_authorize_over_the_real_table` GREEN + its GREEN control (authorize_filter==authorize). 5 subjects × hostile rows m1–m13. |
| F2 NONE-scope member-invisible / admin-visible (m12) + DELETE scope-independent (m13) | ∀ members + admin, owner/non-owner forced | SOUND — pdp-none-scope 4/4 + the retrofit F2 DELETE legs GREEN (Resource(scope=None) constructs; owner deletes own NONE-scope row, non-owner cannot). |
| F3 cross-principal isolation **∀ READ verbs** | **GUARDED (1 verb)** — memory has ONE read verb (recall); `read_verbs=("recall",)` | ACCEPTABLE at 63a. Real recall isolation now pinned (bob→alice GREEN) + the served-set < unfiltered pin. Store-level ∀ carried by F2. Thin, not a blocker. |
| F4 anti-injection **∀ WRITE verbs** | **CLOSED at 63a** — remember (owner-arg TypeError + scope `_grantable`) + invalidate (guarded_write) | SOUND — PIN2 (invalidate foreign-deny) + PIN3 (scope door) + the owner-stamp pin close the doors the predecessor found. Both write verbs exercised. |
| verb-routing coverage (`derived == routed ∪ pending`) | **∀-over-derived-verbs** (partition_tools × dispatch tables) | SOUND — routing 7/7; 32 derived verbs (memory routed, 30 pending w/ triggers); grows-and-reds discriminator GREEN. |
| #425 one round-trip | single call counted at `_query` | SOUND — 425 4/4; `test_stamp_owner_still_returns_the_correct_owner_pair` is the positive control the round-trip pin cannot pass by not reading the owner. |

No surviving wrong build walks a bad outcome through an unguarded door at 63a — the F4 doors the
predecessor found (invalidate, scope) are now pinned and discriminate (PIN2/PIN3 positive+negative legs).

## §P1c — REACH TABLE (per guard: reach DERIVED vs hand-list · coverage a checked variable · effect vs proxy · one-source-by-mutation). Legs: routing/AST/emitter run IN-tree (empirical, on the reference build).

| guard | reach source | coverage a checked variable? | effect vs proxy | verdict |
|---|---|---|---|---|
| `test_every_governed_verb_is_routed_or_adjudicated` | `partition_tools_by_population(live).governed` × dispatch tables (DERIVED) | YES — `derived == routed ∪ pending` reds when `_COMMS/_TASK/_FINDING_ACTIONS` grows; synthetic discriminator GREEN | effect (live tables) | **SOUND at 63a.** R1 (the `_dispatch_verbs` `{lore_comms→_COMMS_ACTIONS…}` table-name hand-list) is RED_ADJUDICATED to 63b per design §10.5 — confirmed the 63a instance HONEST (all 32 verbs covered). |
| `@observes_routing` meta-pin (`routed ⊆ observed`) | AST scan of test tree for the marker (DERIVED) | YES — reds a routed-without-marker; anti-vacuity pin finds the memory markers | **PROXY** (scans the marker's args, not the decorated test's effect-for-that-verb) | **SOUND at 63a** — the memory markers sit on GENUINE behavioural tests (F3 isolation, owner-stamp, invalidate deny) that PASS on the ruled build. R2 proxy-gap RED_ADJUDICATED to 63b — 63a instance honest. |
| R-a.2 ONE production `Subject(` constructor | AST scan of shipped `loremaster` pkg (DERIVED) | YES — `== 1`, in governed.py | effect (AST over shipped source) | SOUND — verified it reds a MIS-named site: aliasing `Subject as _Subject` in resolve_subject made the scan find 0 → RED; spelling it `Subject` → 1 → GREEN. |
| R-a.3 ONE splice (`read_filter` == authorize_filter(READ).to_surql()) | byte-equality delegation pin | YES | effect | SOUND — substrate read_filter 3/3 (member/2-keeps/admin); a private-copy fragment diverges → RED. |
| governed FIELD emitter mutation pin | monkeypatch `_governed_field_specs` → marker in emitted DDL | YES | effect + MUTATION | SOUND — `test_the_governed_fields_route_through_the_shared_emitter` GREEN on the ruled build (memory routes through the ONE emitter). |
| governed **INDEX** emitter mutation pin | monkeypatch `_governed_index_statements` → marker | YES (intent) | effect + MUTATION | **BROKEN → BLOCKER 1.** The instrument (`index_statement`) cannot SEE the mutated statement (end-anchor); the pin reds on a correct build. A guard that cannot observe its own effect is not a guard. |
| EXPLAIN index pins (P1/P2/P6) | shipped walker + C+ TableScan controls in the SAME test | YES — C+ proves the walker sees a TableScan | effect | SOUND — schema live legs GREEN on the ruled DDL (scope IndexScan, full member filter IndexScan, keep.key IndexScan + NONE coexistence). |
| keeps write-path reach pin (SHIPPED, `test_keeps_store`) | AST-derived `_WRITE_PATHS` == coverage map | YES — a NEW write path grows the set and reds the map | effect | **Reds on the new `get_or_create_keyed`** — WORKING AS DESIGNED; the 63a build must add it to the coverage map (§CORPSE C). Not a 63a-contract defect, a flagged integration. |

Legs run: routing/AST/emitter/EXPLAIN pins EMPIRICAL (on the reference build); the meta-pin proxy is
construction-inspection (as at HEAD). R1/R2 confirmed honest-at-63a (not re-litigated, per brief).

## §P2 — fixture perturbation / discrimination

The reference build IS the discrimination proof: each load-bearing fixture separated the correct build
from a plausible wrong one, empirically —
- **PIN4 `< unfiltered_total`:** an unfiltered `recall` (all 3 rows) fails `< 3`; the correct filtered
  build (1–2 rows) passes. Ranking-independent (bob's row excluded at the SQL filter, not by ordering).
- **PIN2 double-catch:** a bare-UPDATE invalidate would set `valid_until` on bob's denied close → the
  `IS None` leg reds; a deny-everything build fails the owner positive control.
- **PIN3 pair:** a verbatim-scope-write build files bob's keep scope → the deny leg reds; a deny-all or
  ignore-scope build fails the `principal-private` positive control.
- **owner-stamp F4:** a hostile `owner_principal=bob` arg cannot move the stamp (the backend has no such
  param → TypeError → accepted). A build that accepted it would store bob → the effect leg reds.
- **The FALSE-PASS I found (BLOCKER-2 vanished-conflict):** the ONE fixture that does NOT discriminate —
  it cannot tell a real 0-row conflict from a no-store-handle call.

## §P6b — deleted-code enumeration (`AgentRegistry.owner_principal_of`, #425)

Independent enumeration from source BEFORE the §8 inventory: `owner_principal_of(agent_id)` returned the
owning principal's bare id (else None), the SECOND `_query` #425 removes; its virtue (agent→owner mapping)
is already produced by the verified SELECT (which now projects `owner_principal AS owner_principal_id`).
On the ruled build: `owner_principal_of` DELETED (`test_owner_principal_of_no_longer_exists` GREEN),
`owner_stamp.py` no longer names it (source pin GREEN), one round-trip pinned, and the owner-pair
correctness preserved (`test_stamp_owner_still_returns_the_correct_owner_pair` GREEN). The #425 pins are
adequate — **but the deletion has an ORPHANED-VIRTUE MISS the 63a contract does not sweep (§CORPSE B).**

---

## §CORPSE — the retrofit + #425 retire behavior the 63a modules never sweep (P6; surfaced, not narrowed)

The reference build's "harder leg" (run the ruled build against the SHIPPED 60/61/62 suites) broke **57
shipped tests**. Each individually verdicted (not "the rest are X"):

- **A — retrofit identity-less DENY (52 tests):** `backend.recall/remember/invalidate` now DENY when
  `subject=None`. The shipped **test_memory_backend (50)** and **test_memory_cutover (2)** call
  recall/remember without a subject → they certify the RETIRED identity-less world (P6 corpses). The 63a
  retrofit module ADDS the new deny tests but NEVER flags/updates these — a builder meets 52 red shipped
  tests with zero contract guidance. (Internal callers `restore_from_ledger`/`rebuild_embeddings` use a
  DIRECT `_apply`/`_upsert_fragment`, NOT `remember`, so there is no boot/restore break — verified.)
- **B — #425 routing change (1 test):** the shipped mutation pin `test_agent_capability_seams::
  test_stamp_owner_routes_through_verify_capability` patches `verify_capability` and expects stamp_owner to
  break. But §10.3 routes stamp_owner through the SHARED `_verify_capability_owner` (so it reads once), NOT
  `verify_capability` — so patching `verify_capability` no longer affects it → the pin reds. A builder could
  "fix" it WRONG by re-routing stamp_owner through `verify_capability` (reintroducing the second read, the
  #425 defect). The 63a #425 module does not flag this corpse. **This is the highest-value corpse** (it
  guards the exact property #425 changes).
- **C — new write path (4 tests):** `get_or_create_keyed` is a new KeepStore write path → the shipped
  `TestKeepStoreWrapsEngineRejections` DERIVED coverage-map pin reds until the builder adds it (coverage map
  + rejection-wrap + transport-propagate). The 63a schema contract adds the method but not the integration.

**Missing pin the 63a contract should carry:** a corpse-sweep note (P6) inventorying the shipped assertions
the retrofit + #425 retire, with each adjudicated (update to pass a subject / re-key the mutation to
`_verify_capability_owner` / register the new write path). The RULED SHAPES themselves are shipped-compatible
(pdp_core + agent_capability 138 GREEN — Resource `str|None` + the #425 additive return preserve the 13
call sites), so this is a corpse/inventory gap, not a shape defect.

---

## §RESIDUALS (every item an individual verdict — "the rest look fine" is banned)

| # | item | verdict |
|---|---|---|
| R1 | `_dispatch_verbs` table-name hand-list (P1c) | **RED_ADJUDICATED → 63b** (design §10.5). 63a instance honest (32 verbs covered). Not re-litigated per brief. |
| R2 | `@observes_routing` observes a MARKER not the effect-for-that-verb (P1c) | **RED_ADJUDICATED → 63b** (design §10.5). 63a markers sit on genuine passing behavioural tests. |
| R3 | F3 recall isolation is 1 read verb (memory has one) | **OK, mildly thin.** Real recall isolation + served-set now pinned; store-level ∀ carried by F2. |
| R4 | `report_unmigrated_governed_rows` / `migrate_governed` take a RAW connection | **RESIDUAL / friction.** Production SDK calls must route through the retry driver (repo `_sdk_guard`); a raw `connection.query` is an SDK escape. My build routed via a `run_governed_query(connection, …)` shim, but the contract could pass a DRIVER-ROUTED seam instead of a bare connection. Satisfiable, not a blocker. |
| R5 | `rebuild_embeddings`/`restore_from_ledger` reconstruct rows via direct `_upsert` (no governed columns) | **RESIDUAL (low).** A rebuild AFTER migration would re-strip scope/owner (the ledger carries neither) → rebuilt rows land NONE-scope (member-invisible until re-migrated). Out of the 63a retrofit's test surface; note for 63b/65. |
| R6 | vanished-conflict pin FALSE-PASSES under BLOCKER-2 | **Folded into BLOCKER 2** — the pin cannot discriminate no-handle from a real 0-row conflict. |
| R7 | AppContext capability-PRESENT resolution unexercised by 63a | **Honest bound (§SATISFIABILITY).** The identity-less tool DENY + shared description are the only 63a AppContext surfaces; the present branch is best-effort in the reference build. |

---

## §HANDOFF — the contract fixes (for contract-63a / lead-63)

1. **BLOCKER 1 (mechanical, test-helper):** change `_governed_contract.index_statement`'s regex to
   `FIELDS\s+<col>\b\s*(?:UNIQUE\b)?(?!\s*,)`. Proven → schema 24/24.
2. **BLOCKER 2 (contract + maybe design):** give `governed.guarded_write` a store handle (a `query` seam /
   connection / store param) and pass it at the 4 frozen substrate call sites + the retrofit backend; the
   vanished-conflict pin must pass a real handle to discriminate. Escalate the seam SHAPE if a design ruling
   is wanted (how the substrate reaches the store).
3. **CORPSE sweep (P6, new pins/flags):** the 63a contract should inventory + adjudicate the shipped
   assertions the retrofit (identity-less deny) and #425 (stamp_owner routing) retire — chiefly
   `test_stamp_owner_routes_through_verify_capability` (re-key to `_verify_capability_owner`), the
   test_memory_backend/cutover identity-less recall/remember suites (pass a subject), and the keeps
   coverage-map for `get_or_create_keyed`.

Findings filed: lore **#430** (guarded_write), **#431** (index_statement), **#432** (corpse sweep).

**VERDICT: CONTRACT INSUFFICIENT** — the 4 prior pins are genuinely closed and §10.5 is confirmed, but the
satisfiability receipt (76/80) exposed 2 reproduced C-DEF blockers + a corpse-sweep gap the contract author
must close. Both blockers were structurally invisible to the reasoning-only prior grade — which is exactly
why the receipt was required.
