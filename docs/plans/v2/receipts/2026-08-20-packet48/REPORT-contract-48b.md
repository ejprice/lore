# REPORT — contract-48b (Wave 48-B: the `principal` table + PrincipalStore)

## Revision r3 (2026-08-20 — adversary r2 INSUFFICIENT: 2 blockers + 1 minor, all fixed)

Adversary REPORT-adversary-48b.md graded r2 INSUFFICIENT (satisfiability 60/1). All three demonstrated defects fixed and re-validated on a correct build:
- **BLOCKER 1 (C-DEF, my bug).** `_field_statement`'s locator `\bFIELD\s+{field}\b` could not match `DEFINE FIELD OVERWRITE <name>` (OVERWRITE sits between `FIELD` and the name), so `test_status_and_role_default_to_the_least_privilege_values` was RED on a CORRECT build. **Fix:** `\bFIELD\s+(?:OVERWRITE\s+)?{field}\b`. Validated: matches `status`/`role`/`email` once each, DEFAULT preserved → the pin now GREEN on a correct build (satisfiability 61/0).
- **BLOCKER 2 (QUANTIFIER LEAK — the important one).** No pin pinned the domain is EXACTLY the ruled set, so a build WIDENING the tuple (`_PRINCIPAL_STATUSES += 'archived'`, `_PRINCIPAL_ROLES += 'superadmin'`) survived the whole contract — a `superadmin` leak in the AUTHZ (`role`) domain is a privilege-escalation hole. **Fix (2 pins, QUANTIFIER law ∀):** OFFLINE `test_the_ruled_status_and_role_domains_are_EXACTLY_the_closed_set` (`set(_PRINCIPAL_STATUSES)=={active,suspended}` ∧ `set(_PRINCIPAL_ROLES)=={member,admin}` — a widened tuple REDS); LIVE belt-and-braces `test_a_plausible_but_unruled_status_or_role_is_rejected_by_the_store` (plausible-but-unruled `archived`/`superadmin` REJECTED by the store — a runtime-widened DDL would accept). Live-validated: both rejected on a correct build (4/4).
- **MINOR.** `create`'s `display_name`/`expires_at` params were unpinned. **Fix:** `test_create_round_trips_display_name_and_expires_at` (`create(display_name='Alice Example', expires_at=<tz-aware dt>)` round-trips; `expires_at` binds as a Python datetime, store law §2). Live-validated: both round-trip (4/4).

**r3 verification:** collect **56** (schema 36 + store 17 + migration 3), all new pins RED-for-right-reason via the gates; ruff + mypy clean (0 errors from my files); live legs re-validated (Leg-2 15/15 + r3 4/4). New satisfiability expectation: **63/0** on a correct build (61 r2-fixed + the 2 QUANTIFIER pins; the display_name pin was among the r2 set the adversary already ran). All open decisions-needed unchanged (#1 resolved r2; #2/#3 open).

## Revision r2 (2026-08-20 — lead ruling A applied)

Lead ruling A resolved decisions-needed #1: design §3 moved the `status`/`role` ASSERTs to **CALL-TIME** derivation (the `_floor_measurement_statements` idiom), which **DELETED** the module-level `_PRINCIPAL_STATUS_ALLOWED` / `_PRINCIPAL_ROLE_ALLOWED` join constants (the tuples `_PRINCIPAL_STATUSES` / `_PRINCIPAL_ROLES` survive). Corrected §6 docstring now names the TUPLES.
- **Fix:** swapped the Fork-6 docstring pin token set `_PRINCIPAL_ROLE_ALLOWED`/`_PRINCIPAL_STATUS_ALLOWED` → `_PRINCIPAL_ROLES`/`_PRINCIPAL_STATUSES` (kept `agent`, `input_required`, `_TRACE_DECLARED_KEYS`, all still in corrected §6).
- **Grep result:** the ONLY references to the deleted `_*_ALLOWED` constants in all 3 files were those 3 lines of the Fork-6 pin (now fixed). Everything else references the surviving TUPLES — my Leg-1 mutation pins already monkeypatch `_PRINCIPAL_STATUSES`/`_PRINCIPAL_ROLES`, which is exactly what the corrected call-time build requires. (`test_surreal_store.py`'s `_ALLOWED_FILTER_KEYS` is a pre-existing unrelated chunk-scroll constant, untouched.)
- **Satisfiability re-confirmed:** my Leg-1 derivation pins CLONE `test_floor_calibration_schema::TestTheClosedDomainsAreDerivedIntoTheDdl`, which passes **4/4** on the real call-time floor build — so the identical-idiom principal pins are satisfiable on corrected §3. Live legs re-validated **15/15 GREEN** (the emitted DDL bytes are unchanged; only the derivation SITE moved). ruff + mypy clean; collect unchanged (50 + 3).
- **decisions-needed #1 is now RESOLVED** (ruling A). #2 and #3 remain open.

## SUMMARY BLOCK
- `brief-base v14 read` · `brief project v7 read`
- **State:** done-with-flags (contract complete, RED-for-right-reason; 3 decisions-needed for lead/operator/adversary).
- **Deliverables (all in writable set):** `loremaster/tests/test_principals_schema.py` (NEW, 36 pins — Legs 1+2) · `loremaster/tests/test_principals_store.py` (NEW, 17 pins — CRUD §8-8/8b + the Fork-6 docstring pin §8-9) · `loremaster/tests/test_surreal_store.py` (+3 pins in `TestSchemaMigrationAgainstAnExistingStore` — Leg 3, #107-class). **56 pins total (r3); every §8 item delivered + the QUANTIFIER exact-domain guard.**
- **Deviation:** the 3 Leg-3 pins are supported by ONE module-level-equivalent `@staticmethod` gate + one setup helper appended INSIDE the migration class (the brief's "migration class only" scope) — no other part of `test_surreal_store.py` touched.
- **Packages considered:** none — contract tests only. Every 48-B mechanism the pins target reuses INTERNAL lore seams (`SurrealStore`/`FindingLedger` owner idiom, `run_query`, `execute_transaction`, `_define_field`/`_define_table`/`_unique_index`, `_apply_ddl`); there is no package to prefer (store-layer machinery). DRY ledger below.
- **Reuse ledger:** 8 new test helpers, all dispositioned (below) — every one CLONED from a named in-tree precedent (`_require_build_store`, `_create_finding`, floor `_statements`, `_apply_ddl`), none invented.
- **Graded:** n/a (contract author — I render no verdict on another artifact). HEAD-at-report `1bbb0fb`.
- **RED verified:** offline Leg-1 (15) FAIL via the schema gate; Leg-3 (3) FAIL via the migration gate; CRUD (15) ERROR-at-setup via the module gate — all carrying the clean "`… not yet built (packet 48-B) … RED until it lands`" message, never an ImportError/collection break. ruff clean on all three; `mypy loremaster` reports **0 errors from my three files**.
- **Live-fixture validation:** 20/20 GREEN against the 3.2.x TEST store (`ws://127.0.0.1:18000`) on a design-§3-faithful DDL — Leg-2 15/15 + Leg-3 5/5 (probes pasted §Appendix). The load-bearing two-NONE-coexist, the UPDATE-path UNIQUE-fill reject, and `SELECT *`-omits-NONE are independently re-confirmed.
- **decisions-needed (1 resolved r2, 2 open):**
  1. **✅ RESOLVED r2 (ruling A).** §3-vs-§8 derivation-timing — the lead adopted CALL-TIME derivation; §3 corrected, the `_*_ALLOWED` constants deleted, my pins satisfiability-confirmed. Only follow-on: the Fork-6 token swap (done r2).
  2. **F1b `set_subject` fill-once vs unconditional.** Design ruled UNCONDITIONAL (recommended); I pin that. `test_idempotent_re_fill_of_own_current_subject_succeeds` is the discriminator — it FLIPS if the operator prefers store-enforced fill-once.
  3. **Subject non-empty ASSERT (conditional pin).** I pin the KEEP-ASSERT §3 ruling (`test_empty_string_subject_rejected_while_none_is_accepted`); DELETE that one pin if the operator drops the ASSERT to a bare `option<string>`.
- **FLAGS (not blocking, outside my writable set — builder/lead co-edits):** F6 fold co-edits in `test_surreal_schema.py` (`EXPECTED_TABLES:77` + `_generated_ddl():429`) — neither reddens; details §5.
- **Message to lead (r3):** `STATE: done · REPORT: REPORT-contract-48b.md · r3 — 3 adversary defects fixed (C-DEF regex, QUANTIFIER exact-domain ∀ pin ×2, display_name/expires_at pin); 56 pins, collect+ruff+mypy clean, live re-validated 15/15+4/4. Sat expectation 63/0. #2/#3 open`.

---

## 1. Receipts & ground truth (verified live, HEAD `1bbb0fb`)

All precedents read live via lore + Read (no grep fallback needed for structure; lore `lore_get_symbol`/`lore_search` served every symbol):
- **Leg-1 offline idiom:** `test_floor_calibration_schema.py::TestTheDdlDecisionRuleIsEnforcedMechanically` + `TestTheClosedDomainsAreDerivedIntoTheDdl` (per-rule clause pins + runtime-mutation derivation).
- **Leg-2 live idiom:** `test_surreal_schema.py::TestFindingRoundTrip` + `_create_finding` (CONTENT-create + `admin_db`); floor `TestTheSchemaAppliesToTheLiveEngine` (rejection + positive-control pattern).
- **Leg-3 migration idiom:** `test_surreal_store.py::TestSchemaMigrationAgainstAnExistingStore` + `migration_db`/`_apply_ddl`; floor `test_a_narrowed_state_assert_MIGRATES_back_to_the_full_set`.
- **RED-now gate idiom:** `test_build_store.py::_require_build_store` (dynamic getattr, keeps typecheck/collection clean).
- **Owner idiom (CRUD):** `findings.FindingLedger.__init__/_ensure_connection/_query/ensure_ready` (design §5 clones it verbatim; `PrincipalStore` ctor = `(*, url, namespace, database, user, password: SecretStr)`, no `dim`).
- **Store law cited (not re-transcribed):** §1.1 (TABLE/INDEX `IF NOT EXISTS`, FIELD `OVERWRITE`), §1.3 (ALTER trap), §1.4 (`option<>` on a new field / write-poison), §1.6 (virgin-DB blind spot), §2 (CONTENT; `SELECT *` OMITS a NONE `option<>` column → `KeyError`, explicit projection reads `None`).
- **Key structural fact I verified myself (grounds decisions-needed #1):** `surreal_schema._floor_measurement_statements` builds `allowed_states = ", ".join(...)` **at CALL time** (reads `FLOOR_STATES` live) — which is *why* floor's runtime-mutation pin works. `finding`/`task`/`agent` build their `_*_STATUS_ALLOWED` at **import time** (module constant embedded in a frozen `_*_FIELD_SPECS`). Design §3's sample principal code follows the *import-time* (finding) shape; §8's pin demands the *call-time* (floor) shape.

---

## 2. Pin catalogue

### Leg 1 — OFFLINE DDL (`test_principals_schema.py`, no server)

`TestThePrincipalDdlDecisionRuleIsEnforcedMechanically`
- `test_the_table_definition_is_IF_NOT_EXISTS` — §1.1 TABLE clause.
- `test_every_field_definition_is_OVERWRITE` — #107 (the load-bearing clause).
- `test_no_field_definition_uses_IF_NOT_EXISTS` — the rule from the other side.
- `test_both_indexes_are_IF_NOT_EXISTS_and_never_OVERWRITE` — §1.5 boot-crash guard.
- `test_both_unique_indexes_are_present_on_email_and_subject` — **Model-B structure** (both UNIQUE).
- `test_the_word_ALTER_appears_in_no_statement` — §1.3.
- `test_the_slice_contains_neither_a_relation_table_nor_a_sequence` — pinned KNOWN BOUND.
- `test_the_generator_returns_the_house_terminated_shape` — `";\n".join(...)+";\n"`.
- `test_the_generator_emits_fields_not_just_the_table_name` — anti-vacuity control (adversary F1c).
- `test_principal_is_FOLDED_into_the_global_generate_ddl` — **Variant A fold** (table exists in prod on ship).
- `test_the_slice_ROUTES_THROUGH_the_shared_ddl_emitters` — MUTATION proof (principal calls `_define_field`).

`TestThePrincipalClosedDomainsAreDerivedIntoTheDdl`
- `test_changing_the_status_tuple_changes_the_emitted_ASSERT` — **runtime-mutation derivation (decisions-needed #1)**.
- `test_changing_the_role_tuple_changes_the_emitted_ASSERT` — same.
- `test_every_ruled_status_and_role_reaches_the_ddl` — membership control.
- `test_status_and_role_default_to_the_least_privilege_values` — DEFAULT `active`/`member` (r3: `_field_statement` locator now tolerates `OVERWRITE`).
- **`test_the_ruled_status_and_role_domains_are_EXACTLY_the_closed_set`** — ⚠ r3 QUANTIFIER pin: `set(_PRINCIPAL_STATUSES)=={active,suspended}` ∧ `set(_PRINCIPAL_ROLES)=={member,admin}` (a WIDENED tuple — e.g. a leaked `superadmin` — REDS).

### Leg 2 — LIVE round-trip (`test_principals_schema.py`, `ws://127.0.0.1:18000`, no skip marker)

`TestThePrincipalSchemaAppliesToTheLiveEngine`: `test_the_slice_creates_the_table`, `test_the_slice_is_safely_re_appliable`.

`TestThePrincipalRoundTrip`:
- `test_create_with_subject_reads_back_by_subject_and_by_email` — (d) OAuth-direct path.
- **`test_two_email_only_creates_both_none_subject_coexist`** — ⚠ THE LOAD-BEARING Model-B pin (probe Q1; two DIFFERENT emails so it can't pass for the wrong reason).
- `test_create_with_subject_also_works_alongside_none_rows` — Q1 other half.
- `test_duplicate_non_none_subject_rejected_on_CREATE` — (b/CREATE).
- **`test_duplicate_non_none_subject_rejected_on_UPDATE_fill`** — ⚠ (b/UPDATE, probe Q3) + positive control (free subject lands).
- `test_duplicate_email_rejected` — (c) email UNIQUE.
- `test_empty_or_whitespace_email_rejected[…]` (3) — (c) non-empty ASSERT.
- `test_missing_email_rejected` — (c) required.
- `test_unknown_status_rejected` / `test_unknown_role_rejected` — closed domain (obvious garbage).
- **`test_a_plausible_but_unruled_status_or_role_is_rejected_by_the_store`** — ⚠ r3 QUANTIFIER live belt-and-braces: PLAUSIBLE-but-unruled `archived`/`superadmin` REJECTED (a runtime-widened DDL would accept; `superadmin` is the authz-escalation value).
- `test_every_valid_status_and_role_is_accepted_positive_control` — POSITIVE CONTROL (over-strict ASSERT caught).
- `test_omitted_option_columns_read_back_as_none_under_explicit_projection` — §2 hostile fixture (explicit projection).
- `test_select_star_OMITS_the_none_option_column_the_control` — §2 discriminating control (why the store must NOT use `SELECT *`).
- `test_empty_string_subject_rejected_while_none_is_accepted` — §3 refinement (**conditional, decisions-needed #3**).
- `test_principal_rejects_an_undeclared_field` — SCHEMAFULL discipline (§1.7).

### Leg 3 — DIRTY-STORE migration (`test_surreal_store.py::TestSchemaMigrationAgainstAnExistingStore`, #107-class)

- `test_a_principal_status_widening_lands_on_an_existing_store` — the #107 assertion (widening MIGRATES a dirty store).
- `test_the_migrated_principal_status_still_rejects_out_of_domain` — POSITIVE CONTROL (widened, not GONE; rejection names the value).
- `test_the_legacy_principal_row_survives_and_stays_writable` — legacy row intact **+ still writable** (no write-poison).

Setup helper `_dirty_principal_store_with_narrowed_status` DERIVES the narrowed/widened/legacy status values from `_PRINCIPAL_STATUSES` (never hand-typed) and writes the legacy row UNDER the narrowed definition (§1.4/§1.6: a row written after the full DDL sees no hazard).

### CRUD (`test_principals_store.py`, live, §8-8/8b)

`TestCreateAndRead`: `test_email_only_create_defaults_to_active_member_none_subject`, `test_create_with_subject_is_found_by_subject_and_email`, `test_create_with_explicit_non_default_role_and_status_round_trips` (**FIXTURES-MUST-DISCRIMINATE** — non-default values), `test_create_round_trips_display_name_and_expires_at` (r3 MINOR — the two previously-unpinned `create` params; `expires_at` a tz-aware datetime), `test_get_by_unknown_subject_and_email_return_none_not_error`, `test_two_email_only_creates_coexist_via_the_store_api` (Model-B load-bearing at the store layer), `test_list_returns_all_principals`, `test_duplicate_email_raises_principal_store_error` (wrapped LOUD), `test_duplicate_non_none_subject_on_create_raises_principal_store_error`.

`TestSetStatus`: `test_set_status_transitions_a_known_email` (happy+control), `test_set_status_on_unknown_email_raises_not_found`, `test_not_found_is_a_subclass_of_store_error`.

`TestSetSubject` (§8-8b): `test_fill_binds_a_pre_created_email_only_principal` (i), `test_set_subject_on_unknown_email_raises_not_found` (ii)+positive-control, `test_subject_theft_raises_store_error` (iii — UPDATE-path UNIQUE backstop, MUST wrap into `PrincipalStoreError`), `test_idempotent_re_fill_of_own_current_subject_succeeds` (iv — **decisions-needed #2 discriminator**).

`TestModuleDocstringNamesBothVocabularies` (Fork-6, §6/§8-9, OFFLINE served-prose instrument): `test_docstring_distinguishes_principal_from_the_agent_vocabulary` — asserts the `loremaster.principals` module docstring names the sibling `agent` vocabulary (`agent` + `input_required`, an agent-only status principal lacks), the principal-specific vocabulary TUPLES (`_PRINCIPAL_ROLES`/`_PRINCIPAL_STATUSES` — the surviving constants post-ruling-A), and the law anchor (`_TRACE_DECLARED_KEYS`). A build that dropped the sibling-vocabulary clause (conflating `principal.role`/`status` with the agent tuples — the exact defect) goes RED.

---

## 3. Declared mutation-proof RED sets (`scripts/mutation_proof.py`, run post-GREEN by builder/adversary)

Node ids taken from `--collect-only` (declared BEFORE any run, per THE-LEVER / #194). `SCH=test_principals_schema.py`, `STO=test_principals_store.py`, `MIG=test_surreal_store.py::TestSchemaMigrationAgainstAnExistingStore`. Each row: MUTATION → the pins that MUST redden.

| # | Mutation to production code | DECLARED-RED node ids |
|---|---|---|
| M1 | principal FIELD clause `OVERWRITE`→`IF NOT EXISTS` | `SCH::TestThePrincipalDdlDecisionRuleIsEnforcedMechanically::test_every_field_definition_is_OVERWRITE`, `::test_no_field_definition_uses_IF_NOT_EXISTS`, `MIG::test_a_principal_status_widening_lands_on_an_existing_store` |
| M2 | subject/email INDEX clause `IF NOT EXISTS`→`OVERWRITE` | `SCH::…::test_both_indexes_are_IF_NOT_EXISTS_and_never_OVERWRITE` |
| M3 | drop/plainify the **subject** UNIQUE index | `SCH::…::test_both_unique_indexes_are_present_on_email_and_subject`, `SCH::TestThePrincipalRoundTrip::test_duplicate_non_none_subject_rejected_on_CREATE`, `::test_duplicate_non_none_subject_rejected_on_UPDATE_fill`, `STO::TestSetSubject::test_subject_theft_raises_store_error` |
| M4 | drop the **email** UNIQUE index | `SCH::…::test_both_unique_indexes_are_present_on_email_and_subject`, `SCH::TestThePrincipalRoundTrip::test_duplicate_email_rejected`, `STO::TestCreateAndRead::test_duplicate_email_raises_principal_store_error` |
| M5 | hand-type (freeze) the status ASSERT | `SCH::TestThePrincipalClosedDomainsAreDerivedIntoTheDdl::test_changing_the_status_tuple_changes_the_emitted_ASSERT` |
| M6 | hand-type (freeze) the role ASSERT | `SCH::…::test_changing_the_role_tuple_changes_the_emitted_ASSERT` |
| M7 | subject `option<string>`→required `string` | `SCH::TestThePrincipalRoundTrip::test_two_email_only_creates_both_none_subject_coexist`, `::test_omitted_option_columns_read_back_as_none_under_explicit_projection`, `STO::TestCreateAndRead::test_two_email_only_creates_coexist_via_the_store_api`, `::test_email_only_create_defaults_to_active_member_none_subject` |
| M8 | remove `principal` from the `generate_ddl` fold | `SCH::…::test_principal_is_FOLDED_into_the_global_generate_ddl` |
| M9 | over-strict status ASSERT (accept only DEFAULT) | `SCH::TestThePrincipalRoundTrip::test_every_valid_status_and_role_is_accepted_positive_control` |
| M10 | store `get_by_*` uses `SELECT *` instead of explicit projection | `STO::TestCreateAndRead::test_email_only_create_defaults_…`, `::test_two_email_only_creates_coexist_via_the_store_api` (KeyError on the NONE subject) — schema-level guard: `SCH::…::test_select_star_OMITS_the_none_option_column_the_control` documents WHY |
| M11 | store `create`/`set_subject` lets the raw `SurrealError` bubble (no wrap) | `STO::TestCreateAndRead::test_duplicate_email_raises_principal_store_error`, `::test_duplicate_non_none_subject_on_create_raises_principal_store_error`, `STO::TestSetSubject::test_subject_theft_raises_store_error` |
| M12 | store `set_status`/`set_subject` silent no-op on unknown email | `STO::TestSetStatus::test_set_status_on_unknown_email_raises_not_found`, `STO::TestSetSubject::test_set_subject_on_unknown_email_raises_not_found` |
| M13 | `set_subject` gains `AND subject IS NONE` (fill-once) | `STO::TestSetSubject::test_idempotent_re_fill_of_own_current_subject_succeeds` (⚠ decisions-needed #2 — this is the INTENDED discriminator, not a defect) |
| M14 | module docstring drops the sibling-vocabulary clause (conflate principal.role/status with agent) | `STO::TestModuleDocstringNamesBothVocabularies::test_docstring_distinguishes_principal_from_the_agent_vocabulary` |
| M15 | **WIDEN** the ruled domain (`_PRINCIPAL_STATUSES += 'archived'` / `_PRINCIPAL_ROLES += 'superadmin'`) — the QUANTIFIER LEAK, authz-critical | `SCH::TestThePrincipalClosedDomainsAreDerivedIntoTheDdl::test_the_ruled_status_and_role_domains_are_EXACTLY_the_closed_set` (offline), `SCH::TestThePrincipalRoundTrip::test_a_plausible_but_unruled_status_or_role_is_rejected_by_the_store` (live) — ⚠ note the derivation/membership/known-bad-reject pins DO NOT catch this (adversary r2 blocker 2) |

**⚠ M5/M6 are UNSATISFIABLE unless the builder derives the ASSERT at CALL time** — see decisions-needed #1. Against §3's *literal* import-time code they are FALSE-RED on a correct build.

---

## 4. Decisions-needed (STOP-and-flag; brief-base §2)

### #1 — §3-vs-§8 derivation-timing (SATISFIABILITY, load-bearing) — ✅ RESOLVED r2 (ruling A)

**RESOLUTION (lead ruling A, 2026-08-20):** reading (A) call-time derivation was adopted; design §3 now derives `status`/`role` ASSERTs at call time in `_principal_statements()` (the deleted `_*_ALLOWED` constants; surviving tuples). My pins were already written to (A) and are satisfiability-confirmed (floor precedent 4/4, live legs 15/15). The Fork-6 token swap (r2) is the only follow-on edit. Original analysis kept below for the record.

**The contradiction.** §8 item 5 (my pin list, verbatim): *"the closed-domain derivation (mutate `_PRINCIPAL_STATUSES`/`_PRINCIPAL_ROLES` → the emitted ASSERT changes)"* — a RUNTIME monkeypatch pin, cloning floor's `TestTheClosedDomainsAreDerivedIntoTheDdl`. §3's *sample code* builds `_PRINCIPAL_STATUS_ALLOWED = ", ".join(...)` at module import and embeds it in a frozen module-constant `_PRINCIPAL_FIELD_SPECS` (the `finding` idiom). **A frozen import-time ASSERT cannot move under a runtime monkeypatch of the tuple**, so a build that faithfully implements §3's literal code makes `test_changing_the_status/role_tuple_changes_the_emitted_ASSERT` FALSE-RED — a C-DEF trap (a pin RED on an otherwise-correct build).

**Two readings (brief-base §2 — I write both, then pick):**
- *(A) Call-time derivation (floor).* `_principal_statements()` builds the status/role ASSERT inline from `_PRINCIPAL_STATUSES`/`_PRINCIPAL_ROLES` at call time (exactly `_floor_measurement_statements`). The runtime-mutation pins pass. This is what §8 demands verbatim and is mutation-provable (CLAUDE.md "A DIAGNOSIS IS NOT AN INSTRUMENT").
- *(B) Import-time derivation (finding, §3 literal).* Keep the frozen constant; the mutation pins can't work → they must be replaced by a WEAKER structural check (`_PRINCIPAL_STATUS_ALLOWED == ", ".join(f"'{s}'" for s in _PRINCIPAL_STATUSES)` + the field spec embeds it).

**I PICK (A)** and wrote the pins to it, because §8 is the explicit pin list, floor is the precedent the brief names, and rigor-vs-speed resolves toward the mutation-provable form (repo law). **Resolution for the builder (minimal deviation from §3):** keep `_PRINCIPAL_FIELD_SPECS` as a module constant for the non-domain fields; build the `status`/`role` field-defs at CALL time inside `_principal_statements()` from the tuples (a 4-line floor-shaped hybrid). Orthogonal to Variant-A (the fold). **If the operator instead rules (B),** the two mutation pins must be swapped for the structural form — surface for a ruling; it's a one-method change either way. Flagged loudly in the module docstring + at each pin so the builder cannot miss it.

### #2 — F1b `set_subject` fill-once vs unconditional

Design §5/§7-F1b RULED the **unconditional** email-keyed UPDATE primitive + 39 orchestration (recommended), with a store-enforced fill-once (`AND subject IS NONE`) as an operator alternative. I pin the RULED default (unconditional). The discriminator is `TestSetSubject::test_idempotent_re_fill_of_own_current_subject_succeeds` (setting a row's subject to ITS OWN current value SUCCEEDS). **If the operator prefers store-enforced fill-once, that pin FLIPS** (a re-fill of an already-set row would be an empty UPDATE → `PrincipalNotFoundError`) and must be replaced. No change needed if the ruled default stands.

### #3 — subject non-empty ASSERT (conditional pin)

Design §3 KEEPS `_NON_EMPTY_STRING_ASSERT` on the `option<string>` subject (skipped on NONE, fires on a present empty string) but offers a one-line drop-to-bare-`option<string>` alternative. I pin the KEEP ruling: `TestThePrincipalRoundTrip::test_empty_string_subject_rejected_while_none_is_accepted`. **If the operator drops the ASSERT, delete that ONE pin** (labeled so at the pin). Live-validated: an empty-string subject IS rejected while NONE IS accepted (Appendix).

### Fork-6 docstring pin — DELIVERED (was flagged, now closed)

Design §6 + §8-9's OFFLINE served-prose instrument is written: `test_principals_store.py::TestModuleDocstringNamesBothVocabularies`. I chose the DISCRIMINATING-token set from design §6's own ruled wording rather than pinning exact prose (a brittle prose pin over-specifies): `agent`, `input_required` (agent-only status), `_PRINCIPAL_ROLE_ALLOWED`, `_PRINCIPAL_STATUS_ALLOWED`, `_TRACE_DECLARED_KEYS`. The builder may adjust the surrounding prose (design §6 allows it) but cannot drop any of the four load-bearing statements without reddening this pin. **If the lead/adversary wants a tighter or looser token set, it is a 1-line edit** — surfaced here so the choice is deliberate, but not left unbuilt (don't-kick-the-can). RED-for-right-reason confirmed (gate ERROR-at-setup).

---

## 5. FLAGS — F6 fold co-edits (not blocking; outside my writable set)

Adding `principal` to `generate_ddl` + a new `generate_principal_ddl` touches two existing pins in `test_surreal_schema.py` (NOT in my writable set → builder/lead co-edit):
- **`EXPECTED_TABLES` (`test_surreal_schema.py:77`)** — checked `EXPECTED_TABLES <= tables` (SUBSET) at :545, so it does NOT redden without `principal`. Recommended (not required) co-edit: add `"principal"` for completeness.
- **`_generated_ddl()` registry (`test_surreal_schema.py:429`)** — the per-generator guard-check class. The FOLD already gives principal DEFEN coverage via the `"generate_ddl"` entry, so this does NOT auto-redden. Recommended co-edit: register `"generate_principal_ddl": generate_principal_ddl()` so the STANDALONE slice is guard-checked too (the pin's own comment names this as the intended registration site). Store-law §4 `ENFORCED` does NOT apply (principal is a plain table, not a RELATION edge).

---

## 6. DRY ledger (brief-base §6 — every new reusable test symbol)

| new symbol | lore query / read | found | disposition |
|---|---|---|---|
| `_require_principal_schema` / `_require_principals` / `_require_principal_ddl` (RED-now gates) | read `test_build_store.py::_require_build_store` | the getattr/importlib RED-now gate pattern | **REUSED the pattern** (3 table/module-specific gates; a single shared gate is wrong — each targets a different surface, and cross-test-file import breaks the house independent-collectibility property) |
| `_create_principal` (CONTENT-create helper) | read `test_surreal_schema.py::_create_finding` | finding-specific CONTENT-create helper | **HAND-ROLLED per-table** (no generic create helper exists; `_create_finding` is finding-columned) |
| `_statements` / `_field_statement` | read floor `_statements`, `test_surreal_schema._field_statement` | per-file private test utilities | **HAND-ROLLED 1-liners** (each schema test module defines its own; cross-file import of a private `_` helper is not the norm) |
| `_one` | read `test_surreal_schema._one` | trivial one-row unwrap | **HAND-ROLLED 1-liner** |
| `_dirty_principal_store_with_narrowed_status` | read `test_surreal_store._apply_ddl`, floor `test_a_narrowed_state_assert_MIGRATES…` | `_apply_ddl` (shared `execute_transaction` seam), `migration_db` fixture | **REUSED `_apply_ddl` + `migration_db`**; the principal narrowing-setup is table-specific |

Production-side DRY is enforced BY the pins, not by my helpers: `test_the_slice_ROUTES_THROUGH_the_shared_ddl_emitters` (principal must CALL `_define_field`, mutation-proven) and the two derivation pins (ASSERT derived from the tuples, not cloned) are the ONE-IMPLEMENTATION guards.

---

## 7. collect-only tails (RED-for-right-reason receipts)

```
# test_principals_schema.py (36) + test_principals_store.py (17)  [r3]
53 tests collected in 0.19s
# test_surreal_store.py (full — my +3 did not break its collection)
181 tests collected in 0.24s
# r3 new pins all RED-for-right-reason via gate; ruff + mypy clean; live re-validated (Leg-2 15/15 + r3 4/4)
# Leg-1 offline run (RED via gate):
15 failed in 0.16s   # each: "principal schema not yet built (packet 48-B) — surreal_schema is missing
                     #  ['PRINCIPAL_TABLE','generate_principal_ddl','_PRINCIPAL_STATUSES','_PRINCIPAL_ROLES']; RED until it lands"
# Leg-3 migration run (RED via gate):
3 failed  # "principal schema not yet built … missing ['PRINCIPAL_TABLE','generate_principal_ddl','_PRINCIPAL_STATUSES']"
# CRUD + docstring run (RED via module gate — ERROR-at-setup, clean message):
16 errors # "loremaster.principals not yet built (packet 48-B) — contract is RED until it lands"
# ruff: All checks passed!  (all three files)
# mypy loremaster: 0 errors from my three files (110 pre-existing errors elsewhere — packet-39 adjudicated + test_auth_composition, NOT mine)
```

---

## Appendix A — Leg-2 live-fixture validation probe (throwaway; pasted per brief-base §1)

Ran against `ws://127.0.0.1:18000` (3.2.x TEST store) on a design-§3-faithful DDL. **Result: `==== 15/15 checks OK ==== ALL GREEN`.** Confirms every Leg-2 pin is satisfiable on a correct build AND independently re-confirms the engine behavior (two-NONE-coexist; dup-subject CREATE+UPDATE reject with positive control; `SELECT *` keys `['created_at','email','id','role','status']` — subject/display_name/expires_at OMITTED; explicit projection reads None; empty-string subject reject; expires_at datetime round-trip). Full script content:

```python
# /tmp/principal_leg2_validation.py — DDL mirrors design §3 as final SQL; exercises the
# exact operations the Leg-2 pins assert. (Reproduce: uv run python <this>.)
DDL = [
  "DEFINE TABLE IF NOT EXISTS principal SCHEMAFULL",
  "DEFINE FIELD OVERWRITE email ON principal TYPE string ASSERT string::len(string::trim($value)) > 0",
  "DEFINE FIELD OVERWRITE subject ON principal TYPE option<string> ASSERT string::len(string::trim($value)) > 0",
  "DEFINE FIELD OVERWRITE display_name ON principal TYPE option<string>",
  "DEFINE FIELD OVERWRITE status ON principal TYPE string DEFAULT 'active' ASSERT $value IN ['active', 'suspended']",
  "DEFINE FIELD OVERWRITE expires_at ON principal TYPE option<datetime>",
  "DEFINE FIELD OVERWRITE role ON principal TYPE string DEFAULT 'member' ASSERT $value IN ['member', 'admin']",
  "DEFINE FIELD OVERWRITE created_at ON principal TYPE datetime DEFAULT time::now()",
  "DEFINE INDEX IF NOT EXISTS principal_email ON principal FIELDS email UNIQUE",
  "DEFINE INDEX IF NOT EXISTS principal_subject ON principal FIELDS subject UNIQUE",
]
# checks: (1) CREATE p1{email A}, p2{email B} both succeed, both subject=None;
# (2) CREATE p3{email C, subject S}; (3) CREATE p4{email D, subject S} REJECTED;
# (4a) UPDATE p2 subject=S REJECTED; (4b) UPDATE p2 subject=S2 accepted (positive control);
# (5) SELECT * on a NONE row omits subject; explicit projection reads None;
# (6) CREATE {subject: ''} REJECTED; (7) unknown status/role REJECTED + every valid combo accepted;
# (8) missing/whitespace/duplicate email REJECTED; (9) undeclared field REJECTED;
# (10) expires_at binds+round-trips as a Python datetime.
```

## Appendix B — Leg-3 migration validation (throwaway; pasted per brief-base §1)

Ran against the TEST store. **Result: `==== 5/5 migration checks OK ==== ALL GREEN`.** Sequence: apply real DDL → `DEFINE FIELD OVERWRITE status … ASSERT $value IN ['active']` (narrow, OLD world) → CREATE legacy `{email, status:'active'}` → assert `status:'suspended'` REJECTED (narrow in force) → re-apply the widened status ASSERT (the deploy) → assert `'suspended'` now ACCEPTED (widening LANDED) → assert legacy row survives + UPDATE it to `'suspended'` (still writable) → assert `'bogus'` REJECTED naming the value (ASSERT wider, not gone). Confirms `pytest.raises(SurrealError)` catches the engine rejection (`InternalError → ServerError → SurrealError`, verified).
```

Note both instruments live only at `/tmp` (throwaway by design); the DURABLE deliverable is the committed pin set, and the semantics they validate are re-derivable from the pasted DDL + step lists above against `ws://127.0.0.1:18000`.
