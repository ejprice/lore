# REPORT — contract-61a-w4 (the append-only `audit` store substrate)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done, **adversary round 1 resolved** + **operator-ratified identity-at-write addition** (§Identity-at-write). The RED contract for packet 61a-w4 (the `audit` table + `AuditStore`) is written: `loremaster/tests/test_audit_schema.py` (**47 pins**) + `loremaster/tests/test_audit_store.py` (**29 pins**) = **76 pins** (68 original + 3 adversary-round + 5 identity-at-write).
- **Deviations:** none material. One self-correction during satisfiability: my threat-model docstring pins first read only the *class* docstring; a plausible-correct build puts the model in the *module* docstring, so I loosened them to read class-OR-module (still faithful to Fork G "on AuditStore"). Reference build lives in a disposable scratch (`/tmp/lore-sat-61a-w4b`), not committed.
- **Packages considered:** none — no new mechanism specified. The reference build reuses existing deps only (`ulid.ULID` — the `KeepStore.create_keep` precedent) + internal seams (`_txn.wrap_store_rejection` / `compose` / `execute_transaction` / `TxnFragment`); no new package to evaluate.
- **Reuse ledger:** 7 new production symbols the builder creates, all dispositioned (table below) — every one HAND-ROLLED (a greenfield audit substrate; `lore_search`/grep proved no `AuditStore`/`_audit_statements` exists) while REUSING the shared emitters + seams.
- **Graded:** e92bd0f · HEAD-at-report: e92bd0f · SAME. (Satisfiability graded my own reference build on a scratch of e92bd0f.)
- **Decisions-needed (surfaced, non-blocking; recommendations made):** (1) composable seam = public `append_fragment(...) -> TxnFragment`; (2) `append(...) -> str` returns the row id; (3) actor args are BARE ids; (4) ⚠ Fork-G-rationale imprecision re `agent` not folded in `generate_ddl` (fold PROVEN sound); (5) cross-wave: `_AUDITED_ACTIONS` values must equal 61b's `Action` enum mutating subset.
- **Receipt pointers:** node sets → §Satisfiability; the 61a/61b boundary held → §Boundary; the #410 + born-wrapped BUILDER instructions → §Builder; required STUB surface → §Stub.

---

## What this contract pins (the store SUBSTRATE only — Fork G)

Two files, mirroring the packet-60 `test_keeps_schema.py` / `test_keeps_store.py` split.

### `test_audit_schema.py` — the `audit` table DDL + live round-trip (47 pins)
- **DDL decision rule (§1.1):** table `SCHEMAFULL IF NOT EXISTS`; every field `OVERWRITE` (never `IF NOT EXISTS`, #107); no `ALTER`; routes through the shared `_define_field`/`_define_table` (mutation-proven); house-terminated `";\n".join(...)+";\n"`; a CONTROL pin demanding fields exist (no vacuous mechanical gate).
- **Field set (Fork G + the identity-at-write addendum):** `actor_principal record<principal>` + `actor_agent record<agent>` (REQUIRED — greenfield §1.4 N/A); **`actor_email` + `actor_agent_name` denormalized non-empty string VALUE columns (§9 forensics — NOT record links)**; `target_table`/`target_row` non-empty strings (NOT a closed domain — the reach-law trap, governed tables don't exist until 63/64); `old_value`/`new_value` `option<object> FLEXIBLE`; `created_at datetime DEFAULT time::now()`; **NO index** (Fork G DEFERS — pinned as a KNOWN BOUND with the "first listing verb" re-open trigger).
- **`action` domain, mutation-proven + quantifier-pinned:** ASSERT derived at CALL TIME from `_AUDITED_ACTIONS` (adding to the tuple moves the DDL); the ruled set is EXACTLY `{WRITE, DELETE, SET_SCOPE, SET_OWNER}`; **READ is NOT audited** (discriminates the mutating subset from the full Action taxonomy).
- **Fold (Fork G / the w3 guard):** `_audit_statements` folded into `generate_ddl` AFTER `_member_of_statements`; emitted IDENTICALLY by `generate_audit_ddl` and `generate_ddl` (one emitter, both paths).
- **Live (ws://127.0.0.1:18000):** `generate_audit_ddl` + the WHOLE folded `generate_ddl` apply cleanly and re-apply idempotently; a WRITE/DELETE/from-nothing row round-trips old→new (explicit projection — the `SELECT *` NONE-omission trap); an arbitrary nested shape round-trips (FLEXIBLE); a ulid id round-trips; unaudited/garbage actions rejected (+ positive control every audited action accepted); empty `target_*` rejected; each required field ∀-omitted → rejected (+ all-present positive control); an undeclared key rejected (SCHEMAFULL).
- **⚠ THE #131/#107 FOLD-SAFETY PROOF (`TestTheFullDdlWithAuditFoldedApplies`):** the audit slice carries `record<agent>` while `agent` is NOT in `generate_ddl` — if a `record<t>` field-def needed its target, folding audit would crash the primary `ensure_ready()` at boot (production-only, invisible to offline pins). Applies the whole folded `generate_ddl` live and proves it does not.

### `test_audit_store.py` — `AuditStore` (29 pins)
- **Denormalized identity (§9 forensics — operator-ratified):** the LOAD-BEARING survives-a-hard-principal-delete pin + the captures-exact-identity control (see §Identity-at-write).
- **Layer-1 append-only surface (allowlist-the-safe over the RESOLVED MRO, #344/#345):** the set of public members reachable on an `AuditStore` instance — **inherited included** — ⊆ `{append, append_fragment, ensure_ready, close}`; `append` present; no mutator reachable; a META-CONTROL that the allowlist itself excludes every mutator; **+ a mutation-proof that the MRO detector SEES an inherited `purge` a class-body scan misses** (adversary BLOCKER 1, security-critical).
- **Creation-ordered id (adversary BLOCKER 2):** 8 sequential appends (distinct-ms) produce strictly creation-ordered ids — Fork G rules `ulid()` for sortability; a `uuid4`/random-id build reds (~1/8! false-pass ≈ 2.5e-5).
- **Fragment routing (adversary RESIDUAL):** `append`'s executed statement == `compose(append_fragment(same args))` — proving `append`'s write IS the composable fragment (one path); a Build-E bypassing non-composable append reds.
- **Threat model stated IN the instrument (Fork G / gate-needs-a-threat-model):** the docstring (class or module) states append-only + IN-PROCESS + the ACCEPTED root/direct-store bound + the Version-B re-open trigger. (Prose pin — a KNOWN BOUND, checks load-bearing concepts not exact wording.)
- **`append` writes the record (Fork G old→new):** WRITE → old+new; DELETE → old + `new_value=None`; SET_OWNER → the owner change; returns a non-empty id handle; two appends → distinct ids; a rejected append leaves no row.
- **No hot-row contention (Fork G):** ≥8-way concurrent appends → 8 distinct rows, no exhaustion (a ulid mint, not a counter-row).
- **Composable `TxnFragment` seam (forward-compat for 63/64):** `append_fragment` returns a single-statement CREATE fragment (no BEGIN/COMMIT), params namespaced; `append` executes via the VERIFIED `execute_transaction` (AST — never a lax `.query()`); POSITIVE atomicity (compose with a co-producer → both land) + ⛔ NEGATIVE atomicity (a rejected co-producer rolls the audit append back → neither lands).
- **Born-wrapped (#400 / Fork I):** `append` routes through `wrap_store_rejection` (AST); a raw `SurrealStoreError` surfaces as `AuditStoreError`; transport/exhausted-contention faults propagate untouched (the discriminator against a catch-all wrong wrap); a REAL engine rejection wraps end-to-end.

---

## The 61a/61b boundary I HELD

Fork G lists pins under the audit story that belong to **61b** (PDP logic). This contract pins **none** of them:
- **NOT `requires_audit`** — a `Decision` field computed inside the PDP's `authorize` (`requires_audit = admin AND NOT member_predicate.matches`). 61b.
- **NOT the PDP admin carve-out** — `authorize(admin, {WRITE,DELETE,SET_SCOPE,SET_OWNER}, audit)=DENY` (Layer 2). 61b (needs the PDP + the IR).

w4 pins ONLY: the `audit` table + fields + mutation-provable `action` domain + fold; `AuditStore.append`/`append_fragment`; the narrow class SURFACE (Layer 1); the composable fragment; born-wrapped. Every store-test docstring names this boundary so a builder reading only the contract does not over-reach into 61b.

---

## ⚠ FLAG surfaced (brief-base §2): Fork G's fold rationale is imprecise, but the fold is SOUND

Fork G says fold audit after member_of because `actor_principal`/`actor_agent` "reference principal/agent, which are **defined earlier**" in `generate_ddl`. **`principal` IS folded there; `agent` is NOT** — the `agent` table is emitted only by `generate_agent_ddl` (standalone, `AgentRegistry.ensure_ready`), never by `generate_ddl` (grep-confirmed: `_agent_statements()` is called at exactly one site, `generate_agent_ddl`).

The fold is nonetheless **SOUND**, because a `record<t>` field-def does not require its target table to pre-exist at DDL time — documented in-repo (`loremaster/loremaster/principal_keys.py`, the `ensure_ready` docstring: *"a `record<t>` field-def does not require the target table to pre-exist at DDL time"*) **and PROVEN live** by `TestTheFullDdlWithAuditFoldedApplies` (the whole folded `generate_ddl` applies to a fresh 3.2.4 store — receipt below). No action needed; flagged so the adversary/builder knows "agent defined earlier" is the imprecise half, and the load-bearing fact is the record-link-needs-no-target one.

---

## Decisions surfaced (I chose; countermand is cheap)

1. **Composable seam = public `append_fragment(...) -> TxnFragment`.** The dominant house precedent is a public `*_fragment` method that RETURNS a `TxnFragment` for external composition (`graph_surreal.purge_file_fragment`, and `findings`/`tasks`/`messages`/`briefs`/`memory` all build+return fragments). `append` = `compose(self.append_fragment(...))` + `execute_transaction`. This honours Fork G's "exposes ONLY append" as *append-only (no mutators)* — `append_fragment` is part of the append capability, and it is on the safe allowlist. Countermand: if the seam should be named/shaped differently, it's a one-line contract touch.
2. **`append(...) -> str` returns the created row's `str(RecordID)` id.** A useful handle, and it lets 61 tests target the exact row WITHOUT a read verb (Fork G DEFERS audit-query verbs). Countermand: `-> None` (fire-and-forget) — then the round-trip pins would read the row by scanning on `target_row`, a small change.
3. **`actor_principal`/`actor_agent` are BARE ids** (the resolved `Subject` stamp), bound via `type::record`. `AuditStore` composes NO `PrincipalStore` (append takes already-resolved ids, unlike `KeepStore`'s email verbs). `record<t>` links don't validate existence (store §4), so no seeding is needed.
4. **Cross-wave vocabulary (for the lead / 61b):** `_AUDITED_ACTIONS = ("WRITE","DELETE","SET_SCOPE","SET_OWNER")` (uppercase, per Fork C/G). 61b's `Action` enum MUST reuse these exact spellings for its mutating subset (one-column-one-vocabulary law) — else the audit ASSERT and the PDP disagree. Not a w4 decision to make, but a consistency constraint 61b must honour.

---

## ⚠ BUILDER INSTRUCTIONS (bake these in — two LIVE guards will gate you)

1. **#410 fold-guard prose landmine (coldaudit-61a-w3 R1).** The w3 fold-coverage guard's PROSE backstop (`_schema_fold_guard.scan_stale_emptiness_prose`) false-positives on a `KNOWN_EMPTINESS_PHRASES` phrase (`"emit []"`, `"emits nothing"`, `"red stub"`, `"not folded"`, `"do not implement"`, `"raises notimplementederror"`) in the docstring/leading-comment of a folded EMITTING slice. **On green, DELETE any TDD RED-STUB comment on `_audit_statements`, or keep a historical note NON-adjacent** — never reframed-in-place directly above `def _audit_statements`. (My reference build's `_audit_statements` docstring is clean — the w3 guard stayed GREEN: 29 passed.)
2. **Born-wrapped, NOT a hand-rolled clone (#400 / the LIVE w2 shape-guard).** `test_engine_rejection_seam.py` AST-walks EVERY loremaster module (now including `audit.py`) for the full #400 idiom (`except (SurrealConnectionError, TxnContentionExhaustedError): raise` preceding a sole-body `except SurrealStoreError as e: raise <Domain>(...) from e`) and asserts it appears NOWHERE outside `wrap_store_rejection`. **`AuditStore.append` MUST route through `wrap_store_rejection(AuditStoreError, ...)`** (the `create_keep` idiom) — a hand-rolled try/except clone would red the w2 guard. (My reference build born-wraps — w2 stayed GREEN: 56 passed.) Note: the w2 contract deliberately does NOT add an AuditStore `_CASES` entry ("born-wrapped in w4 — not here"); the AuditStore wrap mutation/behaviour proof lives in MY `test_audit_store.py::TestAppendIsBornWrapped`, and the no-clone property is auto-covered by w2's module sweep.

---

## Required STUB surface (for the tdd STUB phase → behavioural RED)

At HEAD (e92bd0f) the audit symbols do not exist, so the contract imports directly and the STUB phase makes them importable (the `test_keeps_schema` RED-STUB precedent). Minimal surface:
- **`surreal_schema.py`:** `AUDIT_TABLE = "audit"`; `_AUDITED_ACTIONS = ("WRITE","DELETE","SET_SCOPE","SET_OWNER")`; `_AUDIT_FIELD_SPECS` (or not — a stub `_audit_statements` may `return []`); `_audit_statements() -> list[str]` (`return []`); `generate_audit_ddl() -> str` (`return ""`); `_audit_statements()` folded into `generate_ddl`.
- **`loremaster/loremaster/audit.py`:** `AuditStoreError(RuntimeError)`; `AuditStore` with the real lifecycle (`__init__`/`_ensure_connection`/`ensure_ready`/`close`/`_drop_connection`/`_safe_close`) + `append`/`append_fragment` raising `NotImplementedError`.

`loremaster/loremaster/audit.py` is a NEW MODULE inside the existing `loremaster` workspace member (NOT a new member) — no `registration_sites.py` entry is needed; the w2 module-sweep and the mypy `loremaster` leg cover it automatically.

---

## Reuse (DRY) ledger — the reference build's new production symbols

| new symbol | search run | returned | disposition |
|---|---|---|---|
| `_audit_statements` / `generate_audit_ddl` | grep `_audit_statements`/`generate_audit_ddl`/`AUDIT_TABLE` in `loremaster/` | nothing (greenfield) | HAND-ROLLED, mirroring `_keep_statements`/`generate_keep_ddl`; REUSES `_define_table`/`_define_field` (mutation-proven shared emitters) |
| `_AUDITED_ACTIONS` / `_AUDIT_FIELD_SPECS` | same grep | nothing | HAND-ROLLED, the `_KEEP_TYPES`/`_KEEP_FIELD_SPECS` idiom (call-time ASSERT derivation) |
| `AuditStore` (lifecycle) | `lore_get_symbol KeepStore`; grep `class AuditStore` | KeepStore (the mirror); no AuditStore | HAND-ROLLED, MIRRORS `KeepStore` `__init__`/`_ensure_connection`/`ensure_ready`/`close`/`_drop_connection`/`_safe_close` |
| `AuditStore.append`/`_append_fragment` | grep `TxnFragment(` + `compose(` | the `create_keep` + `purge_file_fragment` precedents | HAND-ROLLED; REUSES `TxnFragment`/`compose`/`execute_transaction` (shared) + `ulid.ULID` |
| `AuditStore.append_fragment` (public) | grep `def .*_fragment` in `graph_surreal.py`, `messages.py`, `tasks.py` | `purge_file_fragment` (public fragment-return precedent) | HAND-ROLLED, MIRRORS `purge_file_fragment` |
| `AuditStore.append` wrap | `lore_get_symbol wrap_store_rejection` | the ONE shared seam | REUSED `loremaster.store._txn.wrap_store_rejection` (born-wrapped) |
| `AuditStoreError` | grep `class KeepStoreError`/`PrincipalStoreError` | the domain-error parity | HAND-ROLLED, `RuntimeError` subclass (the house parity) |

---

## Adversary round 1 (INSUFFICIENT → resolved)

`REPORT-adversary-61a-w4.md` found 2 blockers + 1 residual (contract otherwise strong). All three fixed and mutation-proven (§Satisfiability wrong-build table):
1. **BLOCKER 1 (SECURITY — append-only reach gap):** the surface pins scanned the class BODY only, so an INHERITED mutator (`AuditStore(_Base)` with `_Base.purge`) passed — an admin could erase the trail. **FIX:** the surface allowlist is now over the RESOLVED MRO (`inspect.getmembers` — inherited included), allowlist-the-safe (not a forbidden-name denylist), with a mutation-proof that the MRO detector sees an inherited `purge` the body scan misses.
2. **BLOCKER 2 (ulid creation-order):** a `uuid4` passed all store pins, but Fork G rules `ulid()` for CREATION-ORDER sortability. **FIX:** pinned the ORDER PROPERTY — 8 distinct-ms sequential appends are strictly creation-ordered; a random-id build reds.
3. **RESIDUAL (routing-is-not-sharing):** the fragment pins didn't prove `append()` ROUTES THROUGH the fragment (Build E: a fragment method PLUS a bypassing non-composable append survived). **FIX:** pinned `append`'s executed statement == `compose(append_fragment(same args))` (one path).

## Identity-at-write (operator-ratified §9 forensics addition, Fork G addendum)

The operator ratified DENORMALIZED identity-at-write on the audit store — so a deleted/offboarded compromised admin's human identity survives in the trail as VALUES even as the record links dangle on principal-delete (the dangle-tolerated cascade is RULED; immutable history outlives the actor). Added (+5 pins):
1. **Schema (`_AUDIT_FIELD_SPECS`):** `actor_email` + `actor_agent_name` — plain non-empty string VALUE columns (NOT `record<>` links), REQUIRED. ⚠ **Substrate-verified:** `actor_agent_name` is REQUIRED (not `option<>`) because `agent.name` is a REQUIRED identifier field (`_AGENT_FIELD_SPECS` — an agent always has a name); `actor_email` is required (a principal always has an email). Field-set pin asserts both are string VALUES, non-empty, and NOT record links.
2. **`append`/`append_fragment` take the identity as INPUT** (the CALLER — the 61b PDP — resolves the actor to email/name; at w4 the fixtures provide them). `AuditStore` does NOT fetch the principal row itself (avoids coupling the stores + a race with a concurrent delete). No default on the production method (never a fixture monoculture on a forensic column); a test helper supplies them for non-identity writes.
3. **THE LOAD-BEARING PIN** (`test_actor_identity_survives_a_hard_principal_delete`): write an audit row → `PrincipalStore.delete` the actor principal → `actor_email` + `actor_agent_name` VALUES survive intact, the `actor_principal` link value still holds the now-dangling RecordID, and dereferencing it (`actor_principal.email`) yields NONE. A link-only build (no denormalized value) REDS it — mutation-proven (table below). Plus `test_append_captures_the_EXACT_identity_provided` (distinct values → append records exactly them, not a default/derived value). Boundary held: no `requires_audit`/PDP carve-out; no cascade/refuse of audit rows pinned.

## Satisfiability receipt (the contract goes 0-failed against a KNOWN-CORRECT build)

Re-verified after the adversary-round fixes AND the identity-at-write addition. Built the correct audit store in a provenance-asserting scratch (`./scripts/scratch_copy.sh /tmp/lore-sat-61a-w4b`):

```
PROVENANCE  loremaster.__file__ = /tmp/lore-sat-61a-w4b/loremaster/loremaster/__init__.py   (#140 — INSIDE the scratch)
```

- **76/76 GREEN** against the correct build (live 3.2.4 test store ws://127.0.0.1:18000): `76 passed in 6.30s`.
- **ruff clean** (all 4 files) · **mypy clean** (`uv run mypy loremaster` — the member leg: `Success: no issues found in 231 source files`).
- **w3 fold-coverage guard GREEN with the audit slice folded:** `test_schema_fold_coverage.py` — `29 passed` (fold correct, no #410 prose trap).
- **w2 #400 shape-guard GREEN with `audit.py` born-wrapped:** `test_engine_rejection_seam.py` — `56 passed` (no hand-rolled clone; the module sweep sees `audit.py`).
- **⚠ WRONG-BUILD MUTATION PROOFS (each new pin reds its wrong build, mutation in scratch + revert):**
  | wrong build | pin that must red | result |
  |---|---|---|
  | `AuditStore(_Base)` inherits a `purge` mutator | `test_the_reachable_public_surface_is_within_the_safe_allowlist` | **RED ✓** (`1 failed`) |
  | `append` mints `str(uuid4())` (not creation-ordered) | `test_sequential_appends_produce_creation_ordered_ids` | **RED ✓** (`1 failed`) |
  | `append` writes via a separate non-composable path (Build E) | `test_append_write_IS_the_composable_fragment_one_path` | **RED ✓** (`1 failed`) |
  | link-only build (no denormalized identity columns; append writes only the links) | `test_actor_identity_survives_a_hard_principal_delete` | **RED ✓** (`1 failed`) |
- **RED demonstrated behaviourally against a STUB** (from round 0, contract logic unchanged for the stubbed surface) (`_audit_statements`→`[]`, `generate_audit_ddl`→`""`, `append`/`append_fragment`→`NotImplementedError`): **46 failed / 22 passed** — imports all resolved (no ImportError/collection error), so the RED is behavioural. All schema-correctness discriminators are in the RED 46 (SCHEMAFULL, ASSERT-rejection, required-field, undeclared-key, table-created, born-wrapped). The 22 green-at-stub are structural invariants (error hierarchy, surface allowlist + its meta-control, threat-model docstrings, ruled-constant pins) plus round-trip pins that hold on both a schemaless (stub-auto-created) and a SCHEMAFULL table — their schema-correctness partners (the ASSERT/required/SCHEMAFULL pins) DO discriminate, so suite-level discrimination is intact.

### Declared node sets (from `--collect-only`, **76 nodes**: 47 schema + 29 store)
- **GREEN against the correct build:** all 76 (both files) — `76 passed`.
- **The 3 adversary-round pins are mutation-proven RED against their SPECIFIC wrong builds** (the table above — stronger than a stub run): `test_the_reachable_public_surface_is_within_the_safe_allowlist` (inherited-mutator), `test_sequential_appends_produce_creation_ordered_ids` (uuid4), `test_append_write_IS_the_composable_fragment_one_path` (Build E). The surface pins were renamed from round 0 (`test_the_public_surface…`→`test_the_reachable_public_surface…`, `test_no_mutator_method_is_exposed`→`test_no_mutator_member_is_reachable`).
- **RED against the STUB (round 0, 46 of the original 68):** every node NOT in the green-at-stub list below (behavioural RED — imports resolve).
- **GREEN-at-STUB (round 0, 22, structural/invariant — NOT build-behaviour discriminators):**
  `test_audit_schema.py`: `TestTheAuditDdlDecisionRuleIsEnforcedMechanically::{test_every_audit_field_definition_is_OVERWRITE, test_no_audit_field_definition_uses_IF_NOT_EXISTS, test_the_word_ALTER_appears_in_no_statement}` · `TestTheAuditFieldSet::test_the_audit_slice_emits_NO_index` · `TestTheAuditActionDomainIsDerivedIntoTheDdl::{test_the_ruled_action_domain_is_EXACTLY_the_mutating_actions, test_READ_is_NOT_an_audited_action}` · `TestTheAuditSchemaAppliesToTheLiveEngine::test_the_slice_is_safely_re_appliable` · `TestTheFullDdlWithAuditFoldedApplies::test_the_full_generate_ddl_is_re_appliable` · `TestTheAuditRowRoundTrip::{test_a_delete_audit_row_has_old_value_and_a_NONE_new_value, test_a_create_shaped_audit_row_has_a_NONE_old_value, test_old_and_new_value_round_trip_an_ARBITRARY_nested_shape, test_the_ulid_id_round_trips}` · `TestTheAuditActionAssertLive::test_every_audited_action_is_accepted_positive_control` · `TestTheAuditRequiredFieldDiscipline::test_the_all_required_positive_control_is_accepted`.
  `test_audit_store.py`: `TestTheErrorHierarchy::test_audit_store_error_is_a_runtime_error` · `TestTheAppendOnlySurfaceLayer1::{test_the_public_surface_is_within_the_safe_allowlist, test_append_is_actually_present, test_no_mutator_method_is_exposed, test_the_allowlist_itself_excludes_every_mutator}` · `TestTheThreatModelIsStatedInTheInstrument::{test_the_auditstore_docstring_states_append_only_in_process, test_the_docstring_states_the_accepted_root_bound, test_the_docstring_names_the_version_b_reopen_trigger}`.

The reference build is scratch (disposable, `scratch_copy.sh`), NOT committed — the SHIPPED impl is the builder's. ⚠ Two disposable `/tmp` scratch_copies could NOT be removed at close-out (sandbox denied `rm -rf`): `/tmp/lore-sat-61a-w4` (round 0, now stubbed) and `/tmp/lore-sat-61a-w4b` (round 1, correct build). Both are `/tmp` scratch_copies (NOT git worktrees, no uncommitted real-tree state), safe for the operator to delete — `rm -rf /tmp/lore-sat-61a-w4 /tmp/lore-sat-61a-w4b`.

---

## Handoff
- Writable set honoured: only `loremaster/tests/test_audit_schema.py`, `loremaster/tests/test_audit_store.py`, and this report were written in the real tree. No production file touched (the reference build lives only in the scratch).
- Next: the adversary RE-RUNS (focused on the identity columns, per the lead), then the builder adds the fields + the ruled tripwire test-edits (order: contract → adversary → build → cold audit). Adversary round 1 already attacked the surface reach (inherited-mutator gap), the ulid ruling (uuid4 gap), and fragment routing (Build-E residual) — all closed + mutation-proven; the identity-at-write addition ships with its own LOAD-BEARING survives-delete pin, mutation-proven against a link-only build. Residual attack surface for the re-run: whether the survives-delete pin's `PrincipalStore.delete` path (it readies the full substrate via `generate_ddl`) could pass on a build that stored the identity but derived it from the link at WRITE time (the captures-exact pin + the post-delete read guard against this); the `action` quantifier/READ-exclusion pins; the born-wrapped transport-passthrough discriminator; the negative-atomicity co-producer rollback.
