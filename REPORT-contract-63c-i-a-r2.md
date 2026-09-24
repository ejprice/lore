# REPORT-contract-63c-i-a-r2 — the 63c-i-a contract, revision 2 (amendment-2 §D worklist)

brief-base v16 read · brief project v7 read

## SUMMARY BLOCK
- **state:** done-with-deviations. All 15 §D items are pinned. Receipts were measured 2026-09-24, with the tests authored on base `3dcc1a0`. HEAD moved to `d237ad7` during the run, but only docs changed there.
  - **SATISFIABILITY:** full suite ALONE, `-n 12`, on the reference build → **11292 passed, 0 failed** (62 skipped, 3 xfailed). ruff and `typecheck.sh` are clean on the reference.
  - **RED (main checkout):** 70/70 declared contract pins RED and 48/48 declared controls GREEN. 78 fixture-fallout reds, all missing-seam. 0 unclassified.
  - **MUTATION:** 22/22 wrong builds reached PROOF HELD through `scripts/mutation_proof.py`.
- **deviations:**
  - (D-1) **A3/A2 corpse fixtures re-keyed beyond the worklist.** The A3 writer invariant plus the A2 kwarg turned every pre-existing owner-only `register` fixture site (the awk sweep's list in §FALLOUT; 13 test files touched) into a corpse on every correct build, plus the fake. The r1-contract-on-reference baseline measured 130 failed / 61 errors. They are re-keyed to the consistent provenance pair (§FALLOUT). This is within the writable set and directly caused by the ruled change.
  - (D-2) **A4 corpse retargeted.** `test_comms_footer.py::…::test_perturbing_the_SHARED_predicate_moves_EVERY_members_refusal` was named in neither the worklist nor the adversary report (§DUAL row 5).
  - (D-3) **The E2 control applies the current emitter BEFORE the frozen DDL.** Frozen-only cannot declare the columns `touch` writes. See §FORKS F-1.
- **Packages considered:** none. No production mechanism was specified: the pins exercise already-ruled in-house seams (`lorerunes.is_legal_identifier`/`keep_scope`/`is_blank`). The test instruments use stdlib `importlib`/`ast`/`inspect`/`re`/`sys.modules`, read at use.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 3 new shared test-substrate symbols, all dispositioned (§DRY). One is copy #2 of a test instrument, so the fork is surfaced as F-3.
- **Graded:** n/a — this is the contract author's report; it renders no verdict on another agent's artifact.
- **decisions-needed:**
  - **F-2:** does the fake mirror `is_blank`/`is_legal_identifier` too? The ruling names only the stamp.
  - **F-3:** fold `test_secret_typing.py::_patch_everywhere` onto the new shared `patch_shared_object_everywhere`?
  - F-1 is informational: a reading choice, with both readings written down.
- **receipt pointers:** §ITEMS · §DUAL · §FALLOUT · §RED · §SAT · §MUT · §GATES · §FORKS · §DRY · §INSTRUMENTS (reference build, wrong-build driver and RED-receipt driver, pasted verbatim).

## Capability check (brief-base §4)
- Everything demanded was reachable: the lore MCP (read + comms), `Read`/`Edit`/`Write`, `git`, `uv run pytest/ruff`, `./scripts/typecheck.sh`, `./scripts/scratch_copy.sh`, `scripts/mutation_proof.py` and `scripts/pending_contract_gate.py`.
- grep/rg are hook-blocked (#473), so every textual sweep here is `awk` over `git ls-files`. Fallbacks, said:
  - `lore_search("test_MUTATING_the_predicate_moves_BOTH_callers")` returned no test hit (#383 class), so I used awk.
  - The `owner_principal_id=` register-site sweep, the `AGENT_NAME_PATTERN` sweep and the `key="session:` sweep are exhaustiveness/textual sweeps (CLAUDE.md grep-honest cases a/b), done with BARE awk patterns.
- Store reference `docs/reference/surrealdb-31-capabilities.md` §1–§3 was read first. It is cited in pins, never re-probed.

## §ITEMS — per worklist item (amendment-2 §D)
Mutation receipts are from `mutation_proof.py`: expected-RED ids are declared from `--collect-only` before each run and diffed both ways (§MUT). "HEAD-RED" is measured at `3dcc1a0` (§RED).

| # | item | pin (file::test) | wrong build it kills | mutation receipt |
|---|---|---|---|---|
| 1 | DELETE `TestAgentRoleNonEmptyAssert` + DUAL | `test_comms_schema.py` — DUAL comment in place | the corpse itself (4 pins RED on every correct build) | satisfiability: full suite 0 failed |
| 2 | heartbeat: seed id, narrowed `except`, E2 control | `test_agent_governance_63c_i_a.py::TestAgentHeartbeatOnALegacyRoleRow63cIA::{test_a_touch_succeeds_…, test_CONTROL_the_frozen_asserted_ddl_makes_the_touch_RAISE}` | MP-2 false gate; the seed is now `AgentRegistry._agent_id("wave7","legacy-agent")` | HEAD-RED for the right reason: `TxnDomainRejectionError … (assert violation)` (§RED). The control is GREEN at HEAD and on the reference. A MERGE-skips-validation touch could not be built (F-4) |
| 3 | population resolver ImportFrom leg; five-set; fold to one | `_governed_contract._schema_string_constants` (ImportFrom leg) · `test_memory_enforcement_63b_ia.py::…::test_a_relation_over_a_RE_EXPORTED_endpoint_joins_and_a_non_str_re_export_does_not` · `test_message_enforcement_63b_ii_a.py::…::test_the_derived_population_set_grows_to_memory_message_to` (now `{agent, briefed, memory, message, to}`, with `briefed` adjudicated in its docstring) · ia exact pin DELETED+DUAL | MP-10 (a re-exported endpoint never joins) | **TS-RESOLVER** held: {re-export leg, five-set pin} |
| 4 | re-key `TestMigrateAgentOwner`; mixed-store pin | `test_message_migrate_63b_ii_a.py::TestMigrateAgentOwner::test_agent_migrate_backfills_only_none_owner_agents_to_the_operator` (owner AND session keep; asserts the governed row is byte-identical on all 3 columns; `backfilled == 1`) · `…governance…::TestAgentMigrateScopeKeyed63cIA::test_a_store_with_governed_and_legacy_agents_migrates_only_the_legacy` | WB2 (WHERE lost), WB3 (owner-only precondition) | **WB2** held: {mixed, exempt-token, MigrateAgentOwner}. **WB3** held: {mixed, MigrateAgentOwner} |
| 5 | W1-1 rewrite+rename kill-pin | `test_agent_owns_principal_schema.py::TestTheGovernedTripleRoutesThroughTheOneEmitter63cIA::test_every_governed_column_and_index_MOVES_with_a_REWRITE_of_the_shared_emitter` | WB1 (filter/dedupe twin: 1 failed / 81 passed, and ONLY this pin — every r1 twin pin stayed green) | **WB1** held |
| 6 | R-Q5-1 byte-inert, 2 traps, count+ids+remedy, E3 KNOWN BOUND | `…governance…::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent` | WB8 (no ids), WB9 (no count), WB10 (stamps first, `!= operator` predicate) | **WB8, WB9, WB10** held. The trap owners are non-operator, so no pin sits against the E3 trigger |
| 7 | stamp ∀ legs | `…governance…::TestRegisterStampsTheGovernedTriple63cIA::{test_scope_is_THE_session_keep_across_two_sessions, test_a_householded_joiners_agent_is_stamped_with_the_shared_session_keep}` · `TestTheRegistryProvenanceSeam63cIA::test_the_scope_is_formed_by_the_SHARED_keep_scope_formatter` | WB4 (`sorted(visible)[0]`), WB12 (keeper-only), WB-A2a (private `f"keep:{…}"`) | **WB4, WB12, WB-A2a** held. WB4 is deterministic because keep ids are ULIDs (time-ordered), so `sorted(visible)[0]` is always the EARLIER session's keep |
| 8 | `session_keep_id` seam; forbidden-name pin re-keyed; fake mirrors; unconditional pass | `TestTheRegistryProvenanceSeam63cIA::test_the_registry_stamps_scope_from_session_keep_id_and_owner_agent_self` · `test_agent_capability.py::TestRegisterStampsOwnerPrincipalFromTheCredential::{test_register_signature_is_exactly_identity_plus_the_server_derived_provenance_pair, test_the_provenance_pair_is_unreachable_from_the_wire, test_the_fake_registry_mirrors_the_real_register_surface}` · `…governance…::test_the_tool_passes_session_keep_id_UNCONDITIONALLY` · `_comms_fakes.FakeAgentRegistry.register` (gains `session_keep_id`; stamps `owner_agents`/`scopes`; mirrors A3) | WB-SIG (a 3rd provenance kwarg `scope`), TS-FAKE (fake lacks the kwarg), WB-A2b (conditional splat) | **WB-SIG** held: {signature, fake-mirror}. **TS-FAKE** held. **WB-A2b** held |
| 9 | A3 inconsistent pair refused | `TestTheRegistryProvenanceSeam63cIA::{test_an_inconsistent_provenance_pair_is_refused_before_any_store_io[owner-without-keep/keep-without-owner], test_a_consistent_provenance_pair_registers[alpha-interim-both-none/both-set]}` | WB-A3 (XOR check removed) | **WB-A3** held: exactly the 2 mixed-pair pins |
| 10 | MOVE over the shared corpus + teaching + shared-predicate mutations + regex-twin retarget | `_HOSTILE_IDENTIFIERS` gains `"fixer-b\n"` (ONE corpus). `test_agent_registry.py::TestQ3RegisterValidatesIdentityBeforeStoreIO63cIA::`: `test_register_refuses_a_hostile_identifier_before_any_store_write[13×2]` (field · the `AGENT_NAME_PATTERN.pattern` text · "register again" · the value via `render_fenced`) · `test_register_refuses_a_blank_role_…` (field · "blank" · remedy) · `test_the_identifier_decision_is_the_SHARED_is_legal_identifier[name/session]` (register AND tool layer) · `test_register_charset_check_reads_the_ONE_pattern_in_its_lorerunes_home[name/session]` · `test_the_blank_role_rule_is_the_SHARED_is_blank` | WB5a/b (`"invalid input"`), WB11 (`.match`), WB13 (private `strip()`), WB-A4a (server keeps a private fullmatch), WB-A4b (agents keeps a DRIFTED private pattern) | **WB5a** held: all 26 hostile pins. **WB5b** held: 4. **WB11** held: {2 newline, 2 shared-predicate}. **WB13, WB-A4a, WB-A4b** held (WB-A4b: see F-5, the `re.compile` cache) |
| 11 | `hazard` slot (no default), `make_ddl` no default, `[agent]` content leg | `test_comms_schema.py::_ConstraintSpec` · `_constraint_violation_message` / `_assert_no_violable_constraint` (the ∀ body, lifted so the SERVED message is pinnable) · `TestTheConstraintREDNamesTheTablesOwnWriter63cIA::test_the_served_red_names_this_tables_writer_and_pin[AGENT_TABLE/TO_RELATION/MESSAGE_TABLE]` | TS-HAZARD (the agent hazard swapped to `to`'s prose) | **TS-HAZARD** held |
| 12 | Leg B: `owner_agent` read-back + second run; R1 bound | `…governance…::test_the_real_migrate_survives_the_legacy_violators_all_stamped` (+ an `owner_agent == own id` read-back per violator; second migrate `backfilled == 0`, not refused) · the R1 KNOWN BOUND + re-open trigger in `_governed_contract.frozen_asserted_agent_ddl`'s docstring | a 2-of-3-column stamp on violators (not representable under ONE statement; the pin is the proof, per sidecar F7) | not separately mutated (unbuildable under one UPDATE — F-4). HEAD-RED (§RED); GREEN on the reference |
| 13 | migrate exempt token follows the 3-column golden | `…governance…::test_the_migrate_exempt_token_carries_the_EXECUTED_three_column_statement` (under `observe_governed_table_writes("agent")`: origin `_migrate_agent_owner`, token statement == the executed statement, ONE scope-keyed UPDATE setting all 3 columns) | WB-EX (the token keeps the old owner-only statement) | **WB-EX** held (WB2 also reds it) |
| 14 | `_create_agent` docstring re-dated; D3 fold noted | `test_agent_owns_principal_schema.py::_create_agent` docstring | prose corpse (sidecar F4) | n/a (prose) |
| 15 | builder docstring rows (`LegacyMapping`, D3) | the "BUILDER NOTES" block in `test_agent_governance_63c_i_a.py`'s module docstring | unpinnable by construction (R3/N2) — named so it is not rediscovered | n/a |
| R8-C1 | C1 still covered | `test_message_migrate_63b_ii_a.py::TestMigrateAgentOwner::test_agent_migrate_refuses_on_multi_principal_ambiguity` — confirmed by `--collect-only` NAME (in the RED receipt's declared-GREEN set) and GREEN on both HEAD and the reference | — | — |

**THE RIDER self-check, per item:** every item's "pin it like this" half is the pin named in the table. For items 12/2, whose wrong build is unbuildable, the gap is stated (F-4) rather than claimed.

## §DUAL — every pin deleted or inverted (a DUAL comment sits in place for each)
| # | pin | fate | virtue → replacement |
|---|---|---|---|
| 1 | `test_comms_schema.py::TestAgentRoleNonEmptyAssert` (×5, incl. the real-role control) | DELETED | the blank role is never written → `test_register_refuses_a_blank_role_…` + `test_the_blank_role_rule_is_the_SHARED_is_blank`. The store accepts a legacy blank role → Leg A `[role]`. A real role is accepted → `test_register_accepts_a_valid_identifier_positive_control` |
| 2 | `test_memory_enforcement_63b_ia.py::…::test_the_derived_population_set_is_the_known_set` | DELETED (fold) | the exact known set → the ONE ii-a pin (five-set). Not a hardcode → the ia reach pins + ii-a `…_is_an_OUTPUT_not_a_hand_list` |
| 3 | `test_agent_capability.py::…::test_register_exposes_no_display_owner_argument` | RE-KEYED to three allowlist pins | "provenance is server-derived only and unreachable from the wire" → exact signature set + derived wire disjointness + fake mirror (item 8) |
| 4 | r1 `_MOVE_HOSTILE_IDENTIFIERS` (a local list of 7) + the r1 regex-twin pin (it patched the `agents` re-export) | DELETED / RETARGETED | hostile refusal → the shared 13-shape corpus. ONE spelling → the pattern-object identity + `lorerunes`-home mutation |
| 5 | `test_comms_footer.py::…::test_perturbing_the_SHARED_predicate_moves_EVERY_members_refusal` (it patched `loremaster.server.AGENT_NAME_PATTERN`) | RETARGETED (not in the worklist — D-2) | after A4 the server binding is a re-export the decision no longer reads, so the pin would RED on a correct build. It now patches THE pattern object in every holding module; GREEN at HEAD AND on the reference |
| 6 | `TestMigrateAgentOwner` pre-owned fixture (owner, no scope) | RE-KEYED to owner + THE session keep | the ∀-scoped-untouched virtue (C4) is asserted on all 3 columns; many-row form → the mixed-store pin |

## §FALLOUT — the A2/A3 corpse fixtures (deviation D-1)
**How they were found.** The r1 test tree was run on the r2 reference build (§SAT), and the reds were grouped by cause:
- A3 refuses `owner_principal_id` without `session_keep_id`.
- A2 adds a kwarg the fake did not have.

**How they were fixed.** Every site was located by a bare awk sweep of `owner_principal_id=` over `git ls-files`, and each one now passes the CONSISTENT pair:
- **Store-backed fixtures** use the new shared `_governed_contract.session_keep_id_for`, which mints THE session keep exactly as `_comms_register` does:
  - `register_owned` (used by the ii-a/ii-b credentialed files and `test_wire_isolation_63a.py`)
  - `test_comms_tool.py`'s credentialed helper
  - `test_comms_read_governance_63b_ii_b.py`'s `read_gov_world`
  - `test_comms_schema.py` (the drain-over-cap fixture)
  - `test_governed_substrate_63a.py`
  - `test_mcp_server.py` (the governed-tool fixture)
  - `test_memory_retrofit_63a.py`
  - `test_message_migrate_63b_ii_a.py` (both message fixtures)
  - `test_message_migrate_dirty_store_63b_ii_b.py`
- **Registry-only harnesses** have no keep store, so they use `registry_level_session_keep_id(session)`, a documented synthetic opaque id: the registry only formats it and never reads the keep. These are `test_425_stamp_owner_63a.py`, `test_agent_capability.py::_register_owned` (keep only when an owner exists) and `test_agent_capability_seams.py` (×4).
- `_comms_fakes.FakeAgentRegistry.register` mirrors the writer (item 8).

**Result:** all of these are GREEN on the reference (§SAT), and every one of their HEAD-reds is the missing-seam `session_keep_id` TypeError (§RED).

## §RED — main checkout, tests only, production at HEAD (measured at `3dcc1a0`)
Instrument: `red_receipt_r2.py` (§INSTRUMENTS).
- **What was declared, and when:** its `CONTRACT_RED` / `CONTRACT_GREEN` rules select node ids from `--collect-only` BEFORE the run.
- **Scope:** the 17 touched `test_*.py` files, `pytest -n 12` (the regex-twin pin's docstring gained the F-5 bound after this run — docstring only).
- **Tail:** `collected 2493; DECLARED contract RED 70, contract GREEN 48` → `TOTAL red 148 · passed 2345` · `contract RED declared 70 · observed-red 70` · `contract GREEN declared 48 · observed-green 48` · `fixture fallout red 78 · missing-seam-classified 78 · UNCLASSIFIED 0` · `missing-seam [unexpected keyword argument 'session_keep_id']: 78` · EXIT 0.

**Classification of the 70 contract reds.** Missing-seam reds (a not-yet-built kwarg, symbol or column):
- `TypeError … unexpected keyword argument 'session_keep_id'` — 7
- `AttributeError: module 'lorerunes' has no attribute 'is_legal_identifier' / 'AGENT_NAME_PATTERN'` — 4
- W1-1 columns/indexes absent, and `owner_agent`/`scope` read back NONE

Behavioural reds (HEAD's logic pinned as wrong):
- The store ASSERT still refuses hostile/blank values on the MOVE pins, the Leg A drop-lands and Leg B. That is ~40 lines of `surrealdb.errors.InternalError: Found '…' for field …` chained into `TxnDomainRejectionError (assert violation)`.
- R-Q5-1 does not refuse.
- R-Q5-2/3, the mixed store and the exempt token: HEAD's owner-keyed statement and the missing project keep.
- The tokenless spy sees no `session_keep_id` key.
- The `is_blank` mutation → `DID NOT RAISE`.
- The five-set is `['memory','message','to']`.

**No contract pin is RED for a wrong reason.** The r1 MP-2 case is fixed: the heartbeat leg now reds on `TxnDomainRejectionError … (assert violation)`.

**HEAD reds are structurally RED_ORPHANED under `--currency`'s pytest leg until the build**, as the r1 author reported: the registry adjudicates mypy bounds only.

## §SAT — satisfiability (measured 2026-09-24)
- **The reference build:** `ref_build_r2.py` (§INSTRUMENTS) applied in the scratch `…/scratchpad/ref`. It is the adversary's §A.1 amended for A2/A3/A4 and §6 teaching.
  - Provenance: `loremaster.__file__` = `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/92811d83-1a6b-4ce2-9e50-3516d7b935e7/scratchpad/ref/loremaster/loremaster/__init__.py`.
  - The r2 test tree is identical to the main checkout: `diff -rq loremaster/tests` is empty.
- **Full suite ALONE, `-n 12`:** `11292 passed, 62 skipped, 3 xfailed, 7 warnings in 873.04s` — **0 failed, 0 errors**.
  - The known #466 flakes (`TestFailedRebuildReportsFailed`, `TestRenderInjectionRegistry`) did not appear, so there were none to re-prove.
- **After the lint-demanded cleanups:**
  - ruff `--fix` removed `agents.py`'s now-unused `import re` and re-sorted imports. The re-export takes `# noqa: PLC0414`, per the `surreal_schema` idiom.
  - `_AGENT_OWNER_PRINCIPAL_INDEX_FIELDS` was deleted.
  - Then `uv run ruff check .` gave "All checks passed!" and `./scripts/typecheck.sh` passed every leg (lorerunes/lorescribe/loresigil/loremaster/skills/docs-eval/scripts + shellcheck).
- **Baseline, for the record:** the r1 test tree on the same reference gave **130 failed, 11071 passed, 61 errors**. That is the fallout D-1 repairs.
- ⚠ **The builder's self-destruct duty:** on the built world `pending_contracts.yaml`'s `packet-63c-i-a-contract-r2` entry has nothing left to adjudicate (the reference typechecks clean), so the builder DELETES it with the build.

## §MUT — mutation proofs (all through `scripts/mutation_proof.py`)
**Setup.** The proofs ran in a second scratch copy, `…/scratchpad/wb`, whose production + tests trees are `diff -rq`-identical to `ref`; provenance: `…/scratchpad/wb/loremaster/loremaster/__init__.py`. The driver is `wb_r2.py` (§INSTRUMENTS). Default targets: the governance file, the MOVE class, the W1-1 routes class and `TestMigrateAgentOwner` (82 collected); WB-SIG and TS-FAKE use `test_agent_capability.py` (38); TS-HAZARD and TS-RESOLVER use their own classes.

**Results:**
- WB1, WB2, WB3, WB4, WB5a (26), WB5b (4), WB8, WB9, WB10, WB11 (4), WB12, WB13, WB-A2a, WB-A2b, WB-A3 (2), WB-A4a (2), WB-EX, WB-SIG (2), TS-HAZARD, TS-RESOLVER (2) and TS-FAKE each printed **`PROOF HELD — the declared RED set fired EXACTLY`**, exit 0. Every file was restored byte-exact; the md5 is printed by the tool.
- **WB-A4b** printed `PROOF FAILED` twice before it held, and both were instrument defects the tool caught:
  1. My replacement used `re`, which ruff had removed from the reference, so collection errored.
  2. An identical-text private copy is the SAME object because of CPython's `re.compile` cache, so the identity pin cannot tell it apart (F-5).

  Rebuilt as a DRIFTED copy (`{0,64}`), it gave **PROOF HELD** on both legs.
- **Not re-run:** the adversary's WB6/WB7. They were already KILLED against r1, and r2 removes none of the pins that killed them.

## §GATES (main checkout, measured 2026-09-24)
- `uv run ruff check .` → **All checks passed!**
- `./scripts/typecheck.sh` → 13 errors in `loremaster/tests`, all missing-seam:
  - 10 × `Unexpected keyword argument "session_keep_id"`, across 7 files
  - 3 × `attr-defined` (`lorerunes.is_legal_identifier` / `AGENT_NAME_PATTERN`), in `test_agent_registry.py`

  They are registered as `scripts/pending_contracts.yaml` → `packet-63c-i-a-contract-r2` (owner: the 63c-i-a build; trigger: the kwarg and the lorerunes symbols land). `--verify-registry` passes. Note: `7 UNCHECKED (owner not importable)` for `register.session_keep_id` — the self-destruct liveness leg cannot import a call-arg name.
- `pending_contract_gate.py --currency --legs typecheck,ruff` → **typecheck RED_ADJUDICATED** (13 residuals, owned by `packet-63c-i-a-contract-r2`) · **ruff GREEN**.
  - The **pytest leg was deliberately NOT run.** The manifest runs it at `-n auto`, which the brief forbids (#466), and a RED contract's pytest reds are RED_ORPHANED by construction.
  - The §RED receipt is the pytest instrument for this revision.
  - Currency therefore prints `FAIL — claimed but never run: pytest` (#312's shape, SAID here, not hidden).

## §FORKS — readings chosen, with the alternative written down
- **F-1 (E2 control DDL order).**
  - Reading (a), "never apply the current emitter at all", is unsatisfiable. The frozen capture declares 6 of ~16 columns, so `touch`'s SET of undeclared columns would fail with a schema error, not `(assert violation)` — RED for the wrong reason.
  - Reading (b), taken: the current emitter first declares the columns, then `frozen_asserted_agent_ddl()` re-lands the role ASSERT by OVERWRITE. The refusing ASSERT is the frozen one on every build, so the control stays build-immune.
- **F-2 (the fake mirrors which checks?)** — decision for the lead/sidecar.
  - A2 names the stamp; I added the A3 pair check. I did NOT mirror `is_blank`/`is_legal_identifier` in `FakeAgentRegistry.register`: the ruling did not name them, and the tool layer already charset-gates identities before the registry.
  - Residual: a fake-driven test could register a BLANK role and succeed where the real registry refuses.
  - Recommendation: mirror `is_blank` (it exists at HEAD, so there is no RED fallout), in a follow-up or by ruling.
- **F-3 (DRY — a second patch-everywhere instrument)** — decision for the lead.
  - `patch_shared_object_everywhere` (`_governed_contract.py`) is keyed on object IDENTITY and parametrised by attribute; it is reused by 5 pins in this contract.
  - `test_secret_typing.py::…::_patch_everywhere` is an older private staticmethod keyed on the NAME only. It patches any same-named attribute, and its docstring states the same idiom.
  - Recommendation: fold it onto the shared one (a one-line call-site change). Not done here: outside the worklist, and duplication is a design decision (brief-base §6).
- **F-4 (unbuildable wrong builds, stated rather than claimed):**
  - The heartbeat control's "MERGE that skips validation": SurrealDB re-validates the whole record on any UPDATE form (store-ref §1.4), so no such build was constructible.
  - Leg B's 2-of-3 stamp is unrepresentable under the ruled ONE statement. Those pins are guards whose wrong build I could not construct.
- **F-5 (a measured bound, pinned in the pin's docstring):**
  - The regex-twin identity pin cannot distinguish an IDENTICAL-text private pattern copy, because `re.compile` caches it and returns the shared object.
  - Such a copy is also behaviourally identical at birth. The pin catches the DRIFT, which is the defect.
- **Two-sessions determinism (WB4):** it relies on keep ids being ULIDs (`keeps.py::KeepStore.get_or_create_keyed` mints `str(ULID())`), which are time-ordered. Re-open trigger: keep ids stop being time-ordered.

## §DRY — reuse ledger (brief-base §6)
⚠ These queries were run AFTER the symbols were written (at close-out), so the ledger records the check, not a search-first habit.

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_governed_contract.session_keep_id_for` | `lore_search("test helper mint session keep for an owner principal get_or_create_keyed session key")`, plus an awk sweep of `key=f"session:` over the tests | no shared helper. `test_comms_tool.py`'s private credentialed helper mints the keep inline (line ~375, after register) | **HAND-ROLLED** as the ONE seam every owned-register fixture now calls (it mirrors `_comms_register`'s mint). The comms_tool helper keeps its idempotent second mint call — flagged, harmless |
| `_governed_contract.registry_level_session_keep_id` | same | nothing | **HAND-ROLLED** — a documented synthetic id for registry-only harnesses |
| `_governed_contract.patch_shared_object_everywhere` | `lore_search("patch predicate in every module that imported it monkeypatch sys.modules shared object mutation")` | `test_secret_typing.py::_patch_everywhere` (a private staticmethod, name-keyed) | **HAND-ROLLED, copy #2 of a test instrument → escalated as F-3** (identity-keyed, attribute-parametrised, importable) |
| test-local: `_constraint_violation_message`, `_assert_no_violable_constraint`, `_synthetic_violating_ddl`, `registry_world`, `_agent_rows` | — | — | LIFTED (the ∀ body moved, not cloned) / fixture-local |

## §INSTRUMENTS (pasted verbatim — scratch-only; the writable set excludes `scripts/`)

### `ref_build_r2.py` — the reference build (applied, then `ruff --fix` + the `# noqa: PLC0414` sed below)
```python
"""Reference (believed-correct) 63c-i-a build for contract r2, applied to a scratch copy by exact-string edits.

Derived from adversary-63c-i-a's ref_build.py (REPORT-adversary-63c-i-a.md §A.1) and amended to the
amendment-2 rulings: A2 (registry kwarg ``session_keep_id``, the registry forms the scope via
``lorerunes.pdp.keep_scope``, ``_comms_register`` passes it UNCONDITIONALLY), A3 (register refuses an
inconsistent provenance pair before any store I/O), A4 (``lorerunes.is_legal_identifier`` + the
pattern MOVE; ``_is_comms_charset_legal`` and ``register`` both call the predicate), §6 (refusal
names count + ids + remedy).

Usage: uv run --no-project python ref_build_r2.py <scratch-root>
Each edit asserts its anchor occurs exactly once (a silent no-op edit is a failed setup — #194).
"""

import sys
from pathlib import Path

ROOT = Path(sys.argv[1])


def edit(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: anchor occurs {count} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


def write(rel: str, text: str) -> None:
    path = ROOT / rel
    assert not path.exists(), f"{rel} already exists"
    path.write_text(text)


# --- A4: lorerunes gains the identifier DECISION (+ the pattern MOVES there) ----------------------
write(
    "lorerunes/lorerunes/identifiers.py",
    '"""The comms identifier charset — ONE pattern, ONE decision (packet 63c-i-a, amendment-2 A4)."""\n\n'
    "from __future__ import annotations\n\n"
    "import re\n\n"
    'AGENT_NAME_PATTERN: re.Pattern[str] = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")\n\n\n'
    "def is_legal_identifier(value: str) -> bool:\n"
    '    """Whether ``value`` could BE a comms identity — ``fullmatch``, never ``match`` (#210)."""\n'
    "    return AGENT_NAME_PATTERN.fullmatch(value) is not None\n",
)
RUNES_INIT = "lorerunes/lorerunes/__init__.py"
edit(
    RUNES_INIT,
    "from lorerunes.email_normalisation import normalize_email\n",
    "from lorerunes.email_normalisation import normalize_email\n"
    "from lorerunes.identifiers import AGENT_NAME_PATTERN, is_legal_identifier\n",
)
edit(RUNES_INIT, '__all__ = [\n    "AGENT_TABLE",\n', '__all__ = [\n    "AGENT_NAME_PATTERN",\n    "AGENT_TABLE",\n')
edit(RUNES_INIT, '    "authorize_filter",\n', '    "authorize_filter",\n    "is_legal_identifier",\n')

SCHEMA = "loremaster/loremaster/store/surreal_schema.py"
# Q3: drop name/session/role ASSERTs (KEEP status).
edit(
    SCHEMA,
    '    ("name", _CHUNK_STRING_TYPE, _IDENTIFIER_CHARSET_ASSERT),\n'
    '    ("session", _CHUNK_STRING_TYPE, _IDENTIFIER_CHARSET_ASSERT),\n'
    '    ("role", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),\n    ("model"',
    '    ("name", _CHUNK_STRING_TYPE, ""),\n'
    '    ("session", _CHUNK_STRING_TYPE, ""),\n'
    '    ("role", _CHUNK_STRING_TYPE, ""),\n    ("model"',
)
# W1-1: retire the hand-rolled owner_principal row.
edit(SCHEMA, '    ("owner_principal", "option<record<principal>>", ""),\n    # packet 62, Fork 1', "    # packet 62, Fork 1")
# W1-1: retire the inline index, route through the ONE emitter.
edit(
    SCHEMA,
    "    statements.append(\n"
    "        _plain_index(\n"
    "            AGENT_TABLE,\n"
    '            f"{AGENT_TABLE}_owner_principal",\n'
    "            _AGENT_OWNER_PRINCIPAL_INDEX_FIELDS,\n"
    "        )\n"
    "    )\n",
    "    statements += [\n"
    "        _define_field(AGENT_TABLE, name, type_expr, constraint=constraint)\n"
    "        for name, type_expr, constraint in _governed_field_specs()\n"
    "    ]\n"
    "    statements += _governed_index_statements(AGENT_TABLE)\n",
)
edit(SCHEMA, '_AGENT_OWNER_PRINCIPAL_INDEX_FIELDS = ("owner_principal",)\n', "")

AGENTS = "loremaster/loremaster/agents.py"
edit(AGENTS, "from lorerunes import parse_credential", "from lorerunes import AGENT_NAME_PATTERN as AGENT_NAME_PATTERN\nfrom lorerunes import is_blank, is_legal_identifier, keep_scope, parse_credential")
edit(AGENTS, 'AGENT_NAME_PATTERN: re.Pattern[str] = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")\n', "")
edit(AGENTS, "from loremaster.render import render_attributed", "from loremaster.render import render_attributed, render_compose, render_fenced, render_line\nfrom loremaster.sanitise import sanitise_line")
edit(
    AGENTS,
    "class AgentIdentityConflictError(AgentRegistryError):",
    "class InvalidAgentIdentityError(AgentRegistryError):\n"
    '    """A register argument violates the agent identity rules (63c-i-a §4.2 MOVE)."""\n\n\n'
    "class AgentIdentityConflictError(AgentRegistryError):",
)
edit(
    AGENTS,
    "        owner_principal_id: str | None = None,\n    ) -> AgentRegisterResult:",
    "        owner_principal_id: str | None = None,\n        session_keep_id: str | None = None,\n    ) -> AgentRegisterResult:",
)
edit(
    AGENTS,
    "        agent_id = self._agent_id(session, name)\n        existing_row = await self._select_row(agent_id)\n        now = datetime.now(UTC)\n",
    "        if (owner_principal_id is None) != (session_keep_id is None):\n"
    "            raise AgentRegistryError(\n"
    '                "register called with an owner but no session keep (or the reverse) — a "\n'
    '                "server-side caller bug; nothing was written"\n'
    "            )\n"
    '        for field_name, value in (("name", name), ("session", session)):\n'
    "            if not is_legal_identifier(value):\n"
    "                raise InvalidAgentIdentityError(\n"
    "                    str(\n"
    "                        render_compose(\n"
    "                            render_line(\n"
    '                                "agent {field} is not a legal identifier — it must match {pattern} "\n'
    "                                \"(lowercase letters, digits, '_' or '-', 1-64 chars, starting with a \"\n"
    '                                "letter or digit); nothing was written — register again with a legal "\n'
    '                                "{field}. The rejected value was:",\n'
    "                                field=sanitise_line(field_name),\n"
    "                                pattern=sanitise_line(AGENT_NAME_PATTERN.pattern),\n"
    "                            ),\n"
    "                            render_fenced(value),\n"
    "                        )\n"
    "                    )\n"
    "                )\n"
    "        if is_blank(role):\n"
    "            raise InvalidAgentIdentityError(\n"
    '                "agent role must be non-blank — nothing was written; register again with a role "\n'
    "                \"(e.g. 'builder')\"\n"
    "            )\n"
    "        agent_id = self._agent_id(session, name)\n        existing_row = await self._select_row(agent_id)\n        now = datetime.now(UTC)\n",
)
edit(
    AGENTS,
    "                _COL_CAPABILITY_HASH: sha512_hex(capability),\n",
    "                _COL_CAPABILITY_HASH: sha512_hex(capability),\n"
    '                "owner_agent": RecordID(AGENT_TABLE, agent_id),\n'
    '                "scope": keep_scope(session_keep_id) if session_keep_id is not None else None,\n',
)

SERVER = "loremaster/loremaster/server.py"
edit(
    SERVER,
    "        return AGENT_NAME_PATTERN.fullmatch(value) is not None\n",
    "        return is_legal_identifier(value)\n",
)
edit(SERVER, "from loremaster.agents import AGENT_NAME_PATTERN\n", "from lorerunes import is_legal_identifier\n\nfrom loremaster.agents import AGENT_NAME_PATTERN\n")
edit(
    SERVER,
    "            cadence=cadence,\n            owner_principal_id=principal_bare,\n        )\n        now = datetime.now(UTC)\n        registered_age_s",
    "            cadence=cadence,\n            owner_principal_id=principal_bare,\n"
    "            session_keep_id=(\n"
    '                str(session_keep.id).split(":", 1)[-1] if session_keep is not None else None\n'
    "            ),\n"
    "        )\n        now = datetime.now(UTC)\n        registered_age_s",
)

PRINCIPALS = "loremaster/loremaster/principals.py"
edit(
    PRINCIPALS,
    "    if table == AGENT_TABLE:\n        return await _migrate_agent_owner(store, principal_store)\n",
    "    if table == AGENT_TABLE:\n        return await _migrate_agent_owner(store, keep_store, principal_store)\n",
)
edit(
    PRINCIPALS,
    "async def _migrate_agent_owner(\n    store: StoreHandle,\n    principal_store: PrincipalStore,\n) -> MigrateGovernedResult:",
    "async def _migrate_agent_owner(\n    store: StoreHandle,\n    keep_store: KeepStore,\n    principal_store: PrincipalStore,\n) -> MigrateGovernedResult:",
)
edit(
    PRINCIPALS,
    "    from loremaster.governed import MigrateGovernedResult, governed_exempt\n\n    operator = await resolve_operator_principal(principal_store)\n",
    "    from lorerunes.pdp import keep_scope\n\n"
    "    from loremaster.governed import PROJECT_KEEP_KEY, MigrateGovernedResult, governed_exempt\n\n"
    "    operator = await resolve_operator_principal(principal_store)\n",
)
edit(
    PRINCIPALS,
    "    unmigrated = await _owner_count(store, AGENT_TABLE, none=True)\n"
    "    already = await _owner_count(store, AGENT_TABLE, none=False)\n"
    "    if unmigrated == 0:\n"
    "        return MigrateGovernedResult(\n"
    "            table=AGENT_TABLE,\n",
    "    unmigrated = await _scope_count(store, AGENT_TABLE, none=True)\n"
    "    already = await _scope_count(store, AGENT_TABLE, none=False)\n"
    "    if unmigrated == 0:\n"
    "        return MigrateGovernedResult(\n"
    "            table=AGENT_TABLE,\n",
)
edit(
    PRINCIPALS,
    "    operator_id = operator.id.partition(\":\")[2] or operator.id\n"
    "    backfill_statement = (\n"
    "        f\"UPDATE {AGENT_TABLE} SET owner_principal = type::record('{PRINCIPAL_TABLE}', $owner) \"\n"
    "        \"WHERE owner_principal IS NONE\"\n"
    "    )\n",
    "    owned_unscoped = await run_query(\n"
    "        acquire=store.acquire,\n"
    "        drop=store.drop,\n"
    "        url=store.url,\n"
    "        noun=\"governed agent row precondition\",\n"
    "        label=\"governed.agent_precondition.rejected\",\n"
    "        statement=(\n"
    "            f\"SELECT VALUE id FROM {AGENT_TABLE} WHERE scope IS NONE AND owner_principal IS NOT NONE\"\n"
    "        ),\n"
    "        params={},\n"
    "        logger=logger,\n"
    "    )\n"
    "    owned_unscoped_ids = [str(row) for row in (owned_unscoped or [])]\n"
    "    if owned_unscoped_ids:\n"
    "        return MigrateGovernedResult(\n"
    "            table=AGENT_TABLE,\n"
    "            scanned=unmigrated + already,\n"
    "            backfilled=0,\n"
    "            already_migrated=already,\n"
    "            refused=True,\n"
    "            reason=(\n"
    "                f\"{len(owned_unscoped_ids)} agent row(s) carry an owner but no scope \"\n"
    "                f\"({', '.join(owned_unscoped_ids[:10])}) — a multi-principal or half-applied store; \"\n"
    "                \"nothing was stamped — adjudicate those rows by hand (set their scope, or clear their \"\n"
    "                \"owner) before migrating (§2.1)\"\n"
    "            ),\n"
    "        )\n"
    "    project_keep = await keep_store.get_or_create_keyed(\n"
    "        key=PROJECT_KEEP_KEY, type=\"project\", keeper_email=operator.email, name=\"lore\"\n"
    "    )\n"
    "    project_scope = keep_scope(project_keep.id.partition(\":\")[2] or project_keep.id)\n"
    "    operator_id = operator.id.partition(\":\")[2] or operator.id\n"
    "    backfill_statement = (\n"
    "        f\"UPDATE {AGENT_TABLE} SET owner_principal = type::record('{PRINCIPAL_TABLE}', $owner), \"\n"
    "        \"owner_agent = id, scope = $scope WHERE scope IS NONE\"\n"
    "    )\n",
)
edit(
    PRINCIPALS,
    "            statement=backfill_statement,\n            params={\"owner\": operator_id},\n",
    "            statement=backfill_statement,\n            params={\"owner\": operator_id, \"scope\": project_scope},\n",
)
print("reference build r2 applied")
```
Post-apply commands: `sed -i 's/^from lorerunes import AGENT_NAME_PATTERN as AGENT_NAME_PATTERN$/…  # noqa: PLC0414 - explicit re-export (A4)/' loremaster/loremaster/agents.py && uv run ruff check --fix lorerunes loremaster/loremaster`.

### `wb_r2.py` — the wrong-build driver (22 WBs, declared RED sets)
```python
"""Wrong builds for the 63c-i-a r2 contract, each a SINGLE exactly-once edit on the r2 reference build
(ref_build_r2.py), run through scripts/mutation_proof.py with the expected-RED node ids DECLARED here,
before any run (the #194/#196 discipline: the set is fixed by this file, never read off the output).

Usage (from the scratch reference root):  uv run --no-project python ../wb_r2.py <WB-id> [<WB-id> ...]
Each WB: (file, anchor, replacement, expected-RED node ids, pytest targets). mutation_proof.py asserts the
anchor matches exactly once, restores the file, and diffs observed REDs against the declared set BOTH ways.
"""

from __future__ import annotations

import subprocess
import sys

G = "loremaster/tests/test_agent_governance_63c_i_a.py"
R = "loremaster/tests/test_agent_registry.py"
O = "loremaster/tests/test_agent_owns_principal_schema.py"
C = "loremaster/tests/test_agent_capability.py"
M = "loremaster/tests/test_message_migrate_63b_ii_a.py"
S = "loremaster/tests/test_comms_schema.py"
POP_IA = "loremaster/tests/test_memory_enforcement_63b_ia.py"
POP_IIA = "loremaster/tests/test_message_enforcement_63b_ii_a.py"

SCHEMA = "loremaster/loremaster/store/surreal_schema.py"
AGENTS = "loremaster/loremaster/agents.py"
SERVER = "loremaster/loremaster/server.py"
PRINCIPALS = "loremaster/loremaster/principals.py"
FAKES = "loremaster/tests/_comms_fakes.py"
GOV = "loremaster/tests/_governed_contract.py"

MOVE = f"{R}::TestQ3RegisterValidatesIdentityBeforeStoreIO63cIA"
SEAM = f"{G}::TestTheRegistryProvenanceSeam63cIA"
STAMP = f"{G}::TestRegisterStampsTheGovernedTriple63cIA"
MIG = f"{G}::TestAgentMigrateScopeKeyed63cIA"
CAP_CLASS = "TestTheOwnerPrincipalIsServerDerived"  # resolved at run time below
CORE_TARGETS = [
    G,
    MOVE,
    f"{O}::TestTheGovernedTripleRoutesThroughTheOneEmitter63cIA",
    f"{M}::TestMigrateAgentOwner",
]

HOSTILE_IDS = [
    "", " ", "Fixer-B", "fixer b", "-fixer", "_fixer", "fixer:b", "fixer'b", 'fixer"b', "fixer\\b",
    "fixer\nb", "fixer-b\n", "z" * 65,
]


def _collect(targets: list[str]) -> list[str]:
    out = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", *targets],
        capture_output=True, text=True, check=False,
    ).stdout
    return [line.strip() for line in out.splitlines() if "::" in line]


WBS: dict[str, dict[str, object]] = {
    "WB1": {
        "file": SCHEMA,
        "anchor": (
            "    statements += [\n"
            "        _define_field(AGENT_TABLE, name, type_expr, constraint=constraint)\n"
            "        for name, type_expr, constraint in _governed_field_specs()\n"
            "    ]\n"
            "    statements += _governed_index_statements(AGENT_TABLE)\n"
        ),
        "replacement": (
            '    statements.append(_define_field(AGENT_TABLE, "owner_principal", "option<record<principal>>"))\n'
            "    statements += [\n"
            "        _define_field(AGENT_TABLE, name, type_expr, constraint=constraint)\n"
            "        for name, type_expr, constraint in _governed_field_specs()\n"
            '        if name != "owner_principal"\n'
            "    ]\n"
            '    statements.append(_plain_index(AGENT_TABLE, f"{AGENT_TABLE}_owner_principal", ("owner_principal",)))\n'
            "    statements += _governed_index_statements(AGENT_TABLE)\n"
            "    statements = list(dict.fromkeys(statements))\n"
        ),
        "expect": [
            f"{O}::TestTheGovernedTripleRoutesThroughTheOneEmitter63cIA::"
            "test_every_governed_column_and_index_MOVES_with_a_REWRITE_of_the_shared_emitter"
        ],
    },
    "WB2": {
        "file": PRINCIPALS,
        "anchor": '"owner_agent = id, scope = $scope WHERE scope IS NONE"',
        "replacement": '"owner_agent = id, scope = $scope"',
        "expect": [
            f"{MIG}::test_a_store_with_governed_and_legacy_agents_migrates_only_the_legacy",
            f"{MIG}::test_the_migrate_exempt_token_carries_the_EXECUTED_three_column_statement",
            f"{M}::TestMigrateAgentOwner::test_agent_migrate_backfills_only_none_owner_agents_to_the_operator",
        ],
    },
    "WB3": {
        "file": PRINCIPALS,
        "anchor": 'f"SELECT VALUE id FROM {AGENT_TABLE} WHERE scope IS NONE AND owner_principal IS NOT NONE"',
        "replacement": 'f"SELECT VALUE id FROM {AGENT_TABLE} WHERE owner_principal IS NOT NONE"',
        "expect": [
            f"{MIG}::test_a_store_with_governed_and_legacy_agents_migrates_only_the_legacy",
            f"{M}::TestMigrateAgentOwner::test_agent_migrate_backfills_only_none_owner_agents_to_the_operator",
        ],
    },
    "WB4": {
        "file": SERVER,
        "anchor": 'str(session_keep.id).split(":", 1)[-1] if session_keep is not None else None',
        "replacement": 'sorted(visible)[0].split(":", 1)[-1] if session_keep is not None else None',
        "expect": [f"{STAMP}::test_scope_is_THE_session_keep_across_two_sessions"],
    },
    "WB5a": {
        "file": AGENTS,
        "anchor": "            if not is_legal_identifier(value):\n                raise InvalidAgentIdentityError(\n",
        "replacement": (
            "            if not is_legal_identifier(value):\n"
            '                raise InvalidAgentIdentityError("invalid input")\n'
            "                raise InvalidAgentIdentityError(\n"
        ),
        "expect": "HOSTILE_ALL",
    },
    "WB5b": {
        "file": AGENTS,
        "anchor": "        if is_blank(role):\n            raise InvalidAgentIdentityError(\n",
        "replacement": (
            "        if is_blank(role):\n"
            '            raise InvalidAgentIdentityError("invalid input")\n'
            "            raise InvalidAgentIdentityError(\n"
        ),
        "expect": "BLANK_ALL",
    },
    "WB8": {
        "file": PRINCIPALS,
        "anchor": "f\"({', '.join(owned_unscoped_ids[:10])}) — a multi-principal or half-applied store; \"",
        "replacement": '"— a multi-principal or half-applied store; "',
        "expect": [f"{MIG}::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent"],
    },
    "WB9": {
        "file": PRINCIPALS,
        "anchor": 'f"{len(owned_unscoped_ids)} agent row(s) carry an owner but no scope "',
        "replacement": '"some agent rows carry an owner but no scope "',
        "expect": [f"{MIG}::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent"],
    },
    "WB10": {
        "file": PRINCIPALS,
        "anchor": (
            "    owned_unscoped = await run_query(\n"
            "        acquire=store.acquire,\n"
            "        drop=store.drop,\n"
            "        url=store.url,\n"
            '        noun="governed agent row precondition",\n'
            '        label="governed.agent_precondition.rejected",\n'
            "        statement=(\n"
            '            f"SELECT VALUE id FROM {AGENT_TABLE} WHERE scope IS NONE AND owner_principal IS NOT NONE"\n'
            "        ),\n"
            "        params={},\n"
        ),
        "replacement": (
            "    await run_query(acquire=store.acquire, drop=store.drop, url=store.url, noun='pre', label='pre',\n"
            "        statement=f\"UPDATE {AGENT_TABLE} SET owner_principal = type::record('{PRINCIPAL_TABLE}', $owner) "
            "WHERE owner_principal IS NONE\",\n"
            "        params={'owner': operator.id.partition(':')[2] or operator.id}, logger=logger)\n"
            "    owned_unscoped = await run_query(\n"
            "        acquire=store.acquire,\n"
            "        drop=store.drop,\n"
            "        url=store.url,\n"
            '        noun="governed agent row precondition",\n'
            '        label="governed.agent_precondition.rejected",\n'
            "        statement=(\n"
            '            f"SELECT VALUE id FROM {AGENT_TABLE} WHERE scope IS NONE AND owner_principal IS NOT NONE "\n'
            "            f\"AND owner_principal != type::record('{PRINCIPAL_TABLE}', $op)\"\n"
            "        ),\n"
            "        params={'op': operator.id.partition(':')[2] or operator.id},\n"
        ),
        "expect": [f"{MIG}::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent"],
    },
    "WB11": {
        "file": AGENTS,
        "anchor": "            if not is_legal_identifier(value):\n",
        "replacement": "            if not AGENT_NAME_PATTERN.match(value):\n",
        "expect": [
            f"{MOVE}::test_register_refuses_a_hostile_identifier_before_any_store_write[HOSTILE_NL-name]",
            f"{MOVE}::test_register_refuses_a_hostile_identifier_before_any_store_write[HOSTILE_NL-session]",
            f"{MOVE}::test_the_identifier_decision_is_the_SHARED_is_legal_identifier[name]",
            f"{MOVE}::test_the_identifier_decision_is_the_SHARED_is_legal_identifier[session]",
        ],
    },
    "WB12": {
        "file": SERVER,
        "anchor": 'str(session_keep.id).split(":", 1)[-1] if session_keep is not None else None',
        "replacement": 'str(session_keep.id).split(":", 1)[-1] if session_keep is not None and kept_by_me else None',
        "expect": [f"{STAMP}::test_a_householded_joiners_agent_is_stamped_with_the_shared_session_keep"],
    },
    "WB13": {
        "file": AGENTS,
        "anchor": "        if is_blank(role):\n",
        "replacement": "        if not role.strip():\n",
        "expect": [f"{MOVE}::test_the_blank_role_rule_is_the_SHARED_is_blank"],
    },
    "WB-A2a": {
        "file": AGENTS,
        "anchor": '"scope": keep_scope(session_keep_id) if session_keep_id is not None else None,',
        "replacement": '"scope": f"keep:{session_keep_id}" if session_keep_id is not None else None,',
        "expect": [f"{SEAM}::test_the_scope_is_formed_by_the_SHARED_keep_scope_formatter"],
    },
    "WB-A2b": {
        "file": SERVER,
        "anchor": (
            "            session_keep_id=(\n"
            '                str(session_keep.id).split(":", 1)[-1] if session_keep is not None else None\n'
            "            ),\n"
        ),
        "replacement": (
            "            **(\n"
            '                {"session_keep_id": str(session_keep.id).split(":", 1)[-1]}\n'
            "                if session_keep is not None\n"
            "                else {}\n"
            "            ),\n"
        ),
        "expect": [f"{STAMP}::test_the_tool_passes_session_keep_id_UNCONDITIONALLY"],
    },
    "WB-A3": {
        "file": AGENTS,
        "anchor": "        if (owner_principal_id is None) != (session_keep_id is None):\n",
        "replacement": "        if False:\n",
        "expect": [
            f"{SEAM}::test_an_inconsistent_provenance_pair_is_refused_before_any_store_io[owner-without-keep]",
            f"{SEAM}::test_an_inconsistent_provenance_pair_is_refused_before_any_store_io[keep-without-owner]",
        ],
    },
    "WB-A4a": {
        "file": SERVER,
        "anchor": "        return is_legal_identifier(value)\n",
        "replacement": "        return AGENT_NAME_PATTERN.fullmatch(value) is not None\n",
        "expect": [
            f"{MOVE}::test_the_identifier_decision_is_the_SHARED_is_legal_identifier[name]",
            f"{MOVE}::test_the_identifier_decision_is_the_SHARED_is_legal_identifier[session]",
        ],
    },
    "WB-A4b": {
        "file": AGENTS,
        "anchor": "from lorerunes import AGENT_NAME_PATTERN as AGENT_NAME_PATTERN  # noqa: PLC0414 - explicit re-export (A4)\n",
        # a DRIFTED private copy (cap 64→65): an identical-text copy is the SAME object (re.compile's
        # cache) and behaviourally identical at birth — the second spelling that matters is one that drifts.
        "replacement": 'import re as _re\n\nAGENT_NAME_PATTERN = _re.compile(r"^[a-z0-9][a-z0-9_-]{0,64}$")\n',
        "expect": [
            f"{MOVE}::test_register_charset_check_reads_the_ONE_pattern_in_its_lorerunes_home[name]",
            f"{MOVE}::test_register_charset_check_reads_the_ONE_pattern_in_its_lorerunes_home[session]",
        ],
    },
    "WB-EX": {
        "file": PRINCIPALS,
        "anchor": '    with governed_exempt("migrate-governed", statement=backfill_statement):\n'
        "        await run_query(\n"
        "            acquire=store.acquire,\n"
        "            drop=store.drop,\n"
        "            url=store.url,\n"
        '            noun="governed agent-owner backfill",\n',
        "replacement": '    with governed_exempt("migrate-governed", statement=(\n'
        "        f\"UPDATE {AGENT_TABLE} SET owner_principal = type::record('{PRINCIPAL_TABLE}', $owner) \"\n"
        '        "WHERE owner_principal IS NONE")):\n'
        "        await run_query(\n"
        "            acquire=store.acquire,\n"
        "            drop=store.drop,\n"
        "            url=store.url,\n"
        '            noun="governed agent-owner backfill",\n',
        "expect": [f"{MIG}::test_the_migrate_exempt_token_carries_the_EXECUTED_three_column_statement"],
    },
    "WB-SIG": {
        "file": AGENTS,
        "anchor": "        session_keep_id: str | None = None,\n    ) -> AgentRegisterResult:",
        "replacement": "        session_keep_id: str | None = None,\n        scope: str | None = None,\n    ) -> AgentRegisterResult:",
        "targets": [C],
        "expect": [
            "SIG",
            "FAKE",
        ],
    },
    "TS-HAZARD": {
        "file": S,
        "anchor": '        "`agent` is UPDATE-hot per agent (`AgentRegistry.touch` — every heartbeat — re-validates the "\n',
        "replacement": '        "`to` is UPDATE-hot: `drain` stamps the delivery edges in ONE statement — MessageLedger "\n',
        "targets": [f"{S}::TestTheConstraintREDNamesTheTablesOwnWriter63cIA"],
        "expect": [
            f"{S}::TestTheConstraintREDNamesTheTablesOwnWriter63cIA::test_the_served_red_names_this_tables_writer_and_pin[AGENT_TABLE]"
        ],
    },
    "TS-RESOLVER": {
        "file": GOV,
        "anchor": "        elif isinstance(node, ast.ImportFrom) and node.module is not None and node.level == 0:\n",
        "replacement": "        elif False:\n",
        "targets": [
            f"{POP_IA}::TestTheGovernedPopulationSetIsADerivedOutput",
            f"{POP_IIA}::TestTheGovernedPopulationSetGrows",
        ],
        "expect": [
            f"{POP_IA}::TestTheGovernedPopulationSetIsADerivedOutput::"
            "test_a_relation_over_a_RE_EXPORTED_endpoint_joins_and_a_non_str_re_export_does_not",
            f"{POP_IIA}::TestTheGovernedPopulationSetGrows::test_the_derived_population_set_grows_to_memory_message_to",
        ],
    },
    "TS-FAKE": {
        "file": FAKES,
        "anchor": "        owner_principal_id: str | None = None,\n        session_keep_id: str | None = None,\n    ) -> AgentRegisterResult:",
        "replacement": "        owner_principal_id: str | None = None,\n    ) -> AgentRegisterResult:\n        session_keep_id = None",
        "targets": [C],
        "expect": ["FAKE"],
    },
}


def main() -> int:
    failures = 0
    for wb in sys.argv[1:]:
        spec = WBS[wb]
        targets = list(spec.get("targets", CORE_TARGETS))  # type: ignore[call-overload]
        collected = _collect(targets)
        expect = spec["expect"]
        if expect == "HOSTILE_ALL":
            declared = [n for n in collected if "test_register_refuses_a_hostile_identifier_before_any_store_write[" in n]
        elif expect == "BLANK_ALL":
            declared = [n for n in collected if "test_register_refuses_a_blank_role_before_any_store_write[" in n]
        else:
            declared = []
            for item in expect:  # type: ignore[union-attr]
                if item == "SIG":
                    declared += [n for n in collected if n.endswith(
                        "test_register_signature_is_exactly_identity_plus_the_server_derived_provenance_pair")]
                elif item == "FAKE":
                    declared += [n for n in collected if n.endswith("test_the_fake_registry_mirrors_the_real_register_surface")]
                elif "HOSTILE_NL" in item:
                    prefix, field = item.split("[HOSTILE_NL-")
                    declared += [n for n in collected if n.startswith(prefix + "[fixer-b\n") or (
                        n.startswith(prefix + "[") and "fixer-b" in n and n.endswith(f"-{field[:-1]}]")
                        and ("\\n]" in n or "\n" in n or "fixer-b\\n" in n))]
                else:
                    declared.append(item)
        missing = [d for d in declared if d not in collected]
        print(f"== {wb}: {len(declared)} declared RED (of {len(collected)} collected); undeclared-missing={missing}")
        if missing or not declared:
            print(f"== {wb}: SETUP FAILED — declared ids not collected")
            failures += 1
            continue
        cmd = [
            "uv", "run", "python", "scripts/mutation_proof.py",
            "--file", str(spec["file"]), "--anchor", str(spec["anchor"]), "--replacement", str(spec["replacement"]),
        ]
        for node in declared:
            cmd += ["--expect-red", node]
        cmd += ["--", "uv", "run", "pytest", "-n", "12", "-q", "-p", "no:cacheprovider", *targets]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        tail = "\n".join((result.stdout + result.stderr).splitlines()[-12:])
        print(f"== {wb}: exit={result.returncode}\n{tail}\n")
        failures += result.returncode != 0
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
```

### `red_receipt_r2.py` — the RED receipt (declared contract RED/GREEN + missing-seam classifier)
```python
"""RED receipt for the 63c-i-a r2 contract in the MAIN checkout (tests only; production at HEAD).

Two declared expectations, BOTH fixed in this file before any run (never read off the output):

1. CONTRACT pins — node ids selected from ``--collect-only`` by the (file, name-fragment) rules in
   ``CONTRACT_RED`` must ALL be RED at HEAD; the ids selected by ``CONTRACT_GREEN`` (controls /
   guards / green-discriminators) must ALL be GREEN at HEAD.
2. FIXTURE FALLOUT — every OTHER red node in the touched files must carry one of the MISSING-SEAM
   signatures in ``MISSING_SEAM_SIGNATURES`` (the A2/A3/A4 seams the i-a build adds). A red with any
   other reason is printed as UNCLASSIFIED — a RED-for-the-wrong-reason defect to fix (the MP-2 class).

Usage (main checkout root):  uv run python <this> <junit-out.xml> <touched test files...>
"""

from __future__ import annotations

import subprocess
import sys
import xml.etree.ElementTree as ET

G = "test_agent_governance_63c_i_a.py"
R = "test_agent_registry.py"
O = "test_agent_owns_principal_schema.py"
C = "test_agent_capability.py"
S = "test_comms_schema.py"
IA = "test_memory_enforcement_63b_ia.py"
IIA = "test_message_enforcement_63b_ii_a.py"
M = "test_message_migrate_63b_ii_a.py"
F = "test_comms_footer.py"

# (file, fragment) — a node is selected when its id contains the file AND the fragment.
CONTRACT_RED = [
    (G, "TestRegisterStampsTheGovernedTriple63cIA::"),
    (G, "TestTheRegistryProvenanceSeam63cIA::"),
    (G, "::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent"),
    (G, "::test_a_store_with_governed_and_legacy_agents_migrates_only_the_legacy"),
    (G, "::test_R_Q5_2_"),
    (G, "::test_R_Q5_3_"),
    (G, "::test_the_migrate_exempt_token_carries_the_EXECUTED_three_column_statement"),
    (G, "::test_the_assert_DROPS_and_the_value_survives_byte_intact"),
    (G, "::test_the_real_migrate_survives_the_legacy_violators_all_stamped"),
    (G, "::test_a_touch_succeeds_on_a_role_empty_legacy_row_after_the_drop"),
    (R, "::test_register_refuses_a_hostile_identifier_before_any_store_write"),
    (R, "::test_register_refuses_a_blank_role_before_any_store_write"),
    (R, "::test_the_identifier_decision_is_the_SHARED_is_legal_identifier"),
    (R, "::test_register_charset_check_reads_the_ONE_pattern_in_its_lorerunes_home"),
    (R, "::test_the_blank_role_rule_is_the_SHARED_is_blank"),
    (O, "TestTheGovernedTripleShape63cIA::"),
    (O, "::test_the_three_governed_columns_are_byte_equal_to_the_shared_emitter"),
    (O, "::test_the_governed_columns_route_through_the_shared_field_emitter"),
    (O, "::test_the_governed_indexes_route_through_the_shared_index_emitter"),
    (O, "::test_the_two_governed_indexes_are_emitted_each_once"),
    (O, "::test_every_governed_column_and_index_MOVES_with_a_REWRITE_of_the_shared_emitter"),
    (C, "::test_register_signature_is_exactly_identity_plus_the_server_derived_provenance_pair"),
    (C, "::test_the_fake_registry_mirrors_the_real_register_surface"),
    (S, "::test_no_field_carries_a_constraint_a_legacy_row_can_violate[agent]"),
    (IIA, "::test_the_derived_population_set_grows_to_memory_message_to"),
    (M, "TestMigrateAgentOwner::test_agent_migrate_backfills_only_none_owner_agents_to_the_operator"),
]
CONTRACT_GREEN = [
    (G, "::test_the_frozen_old_world_is_a_faithful_asserted_capture"),
    (G, "::test_BASELINE_the_asserted_old_world_refuses_every_violator"),
    (G, "::test_CONTROL_a_clean_row_lands_under_the_asserted_old_world"),
    (G, "::test_the_status_assert_STAYS_after_migrating_a_dirty_store"),
    (G, "::test_C_CONTROL_the_frozen_asserted_ddl_makes_the_migrate_RAISE"),
    (G, "::test_CONTROL_the_frozen_asserted_ddl_makes_the_touch_RAISE"),
    (G, "::test_R_Q5_1_CONTROL_a_clean_store_backfills_every_none_scope_row"),
    (G, "::test_the_migrate_is_idempotent"),
    (G, "TestAJunkStatusLegacyRowRefusesTheAgentBackfill63cIA::"),
    (R, "::test_register_accepts_a_valid_identifier_positive_control"),
    (O, "::test_owner_principal_is_emitted_exactly_once"),
    (C, "::test_the_provenance_pair_is_unreachable_from_the_wire"),
    (S, "TestTheConstraintREDNamesTheTablesOwnWriter63cIA::"),
    (S, "::test_no_field_carries_a_constraint_a_legacy_row_can_violate[to]"),
    (S, "::test_no_field_carries_a_constraint_a_legacy_row_can_violate[message]"),
    (S, "TestBriefCharsetAssert::"),
    (IA, "::test_a_relation_over_a_RE_EXPORTED_endpoint_joins_and_a_non_str_re_export_does_not"),
    (IA, "::test_the_population_derivation_reach_is_a_checked_variable"),
    (IIA, "::test_the_population_set_is_an_OUTPUT_not_a_hand_list"),
    (IIA, "::test_message_and_to_join_the_derived_population_set"),
    (M, "TestMigrateAgentOwner::test_agent_migrate_refuses_on_multi_principal_ambiguity"),
    (F, "::test_perturbing_the_SHARED_predicate_moves_EVERY_members_refusal"),
]
MISSING_SEAM_SIGNATURES = (
    "unexpected keyword argument 'session_keep_id'",
    "has no attribute 'is_legal_identifier'",
    "has no attribute 'AGENT_NAME_PATTERN'",
    "register called with an owner but no session keep",  # the fake mirrors A3; HEAD's caller passes owner only
)


def _select(nodes: list[str], rules: list[tuple[str, str]]) -> set[str]:
    return {node for node in nodes for file, fragment in rules if file in node and fragment in node}


def main() -> int:
    junit, *files = sys.argv[1:]
    collected_out = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", *files],
        capture_output=True, text=True, check=False,
    ).stdout
    nodes = [line.strip() for line in collected_out.splitlines() if "::" in line]
    declared_red = _select(nodes, CONTRACT_RED)
    declared_green = _select(nodes, CONTRACT_GREEN)
    print(f"collected {len(nodes)}; DECLARED contract RED {len(declared_red)}, contract GREEN {len(declared_green)}")
    for file, fragment in CONTRACT_RED + CONTRACT_GREEN:
        if not any(file in node and fragment in node for node in nodes):
            print(f"RULE MATCHES NOTHING (declaration defect): {file} {fragment}")
    subprocess.run(
        ["uv", "run", "pytest", "-n", "12", "-q", "-p", "no:cacheprovider", f"--junitxml={junit}", *files],
        capture_output=True, text=True, check=False,
    )
    red: dict[str, str] = {}
    passed: set[str] = set()
    for case in ET.parse(junit).getroot().iter("testcase"):
        classname, name = case.get("classname", ""), case.get("name", "")
        path = classname.replace(".", "/")
        # junit classname is dotted module path + class; rebuild a node-id-ish key for matching.
        key = f"{path}::{name}"
        problem = case.find("failure") if case.find("failure") is not None else case.find("error")
        if problem is not None:
            red[key] = (problem.get("message") or "") + "\n" + (problem.text or "")
        elif case.find("skipped") is None:
            passed.add(key)

    def _match(node: str, pool: set[str] | dict[str, str]) -> str | None:
        file_part, _, rest = node.partition("::")
        module = file_part.removesuffix(".py").split("/")[-1]
        klass_and_name = rest.replace("::", "/")
        for key in pool:
            if module in key and key.endswith(klass_and_name.split("/")[-1]) and all(
                piece in key for piece in klass_and_name.split("/")[:-1]
            ):
                return key
        return None

    missing_red = [n for n in sorted(declared_red) if _match(n, red) is None]
    missing_green = [n for n in sorted(declared_green) if _match(n, passed) is None]
    contract_red_keys = {_match(n, red) for n in declared_red}
    fallout = {k: v for k, v in red.items() if k not in contract_red_keys}
    seam = {k: v for k, v in fallout.items() if any(sig in v for sig in MISSING_SEAM_SIGNATURES)}
    unclassified = {k: v for k, v in fallout.items() if k not in seam}
    print(f"TOTAL red {len(red)} · passed {len(passed)}")
    print(f"contract RED declared {len(declared_red)} · observed-red {len(declared_red) - len(missing_red)}")
    print(f"contract GREEN declared {len(declared_green)} · observed-green {len(declared_green) - len(missing_green)}")
    print(f"fixture fallout red {len(fallout)} · missing-seam-classified {len(seam)} · UNCLASSIFIED {len(unclassified)}")
    for node in missing_red:
        print(f"DECLARED RED STAYED GREEN: {node}")
    for node in missing_green:
        print(f"DECLARED GREEN WENT RED/ABSENT: {node}")
    for key, text in sorted(unclassified.items()):
        print(f"UNCLASSIFIED RED: {key} :: {text.strip().splitlines()[0][:200] if text.strip() else ''}")
    for node in sorted(declared_red):
        key = _match(node, red)
        if key is not None:
            first = next((ln.strip() for ln in red[key].splitlines() if ln.strip().startswith("E ")), red[key].strip().splitlines()[0] if red[key].strip() else "")
            print(f"CONTRACT RED: {node.split('::', 1)[1][:110]} :: {first[:170]}")
    by_sig: dict[str, int] = {}
    for text in seam.values():
        sig = next(s for s in MISSING_SEAM_SIGNATURES if s in text)
        by_sig[sig] = by_sig.get(sig, 0) + 1
    for sig, count in sorted(by_sig.items()):
        print(f"  missing-seam [{sig}]: {count}")
    return int(bool(missing_red or missing_green or unclassified))


if __name__ == "__main__":
    raise SystemExit(main())
```
