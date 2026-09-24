# REPORT-contract-63c-i-a-r3 — the 63c-i-a contract, revision 3 (amendment-4 §W worklist)

brief-base v16 read · brief project v7 read

## SUMMARY BLOCK
- **state:** done-with-deviations — r3a `11cbfb2` (items 1–6, GATING) + r3b (items 7–11, NON-GATING + prose, with amendment-5's `26511f0` rulings on FORK-A/B/C applied) committed as two commits. **SAT (measured 2026-09-24 19:03–19:12 EDT, 36 GB available, no other lore pytest): FULL SUITE ALONE `-n 12` on the reference → `11405 passed, 62 skipped, 3 xfailed` — 0 failed, 0 errors, exit 0**; ruff clean in the reference; its typecheck residuals are exactly the 11 registry SELF-DESTRUCTs (no real mypy error).
- **deviations:** (D-1) FORK-B: generator discovery lifted into `_enforced_relations_scaffold` and its two private copies folded (ratified by amendment-5, with the `dim`-whenever-present rider applied). (D-2) MP-G: `_logging_fixtures.module_level_bindings_of` extracted from `_rebind_everywhere` (a 4th identity-rebind copy) instead of another loop (ratified). (D-3) Most wrong builds ran through my declare-then-diff lane driver (multi-edit / declared-to-survive); single-anchor ones through `scripts/mutation_proof.py`. (D-4) Two declaration mispredictions recorded, not re-declared: IM3 (4 skip-by-design ids), GD1 (one extra consumer red, safe direction). (D-5) The reference includes the builder's ONE granted test-tree edit (amendment-5 FORK-C guard deletion, `builder_guard_deletion.py`).
- **Packages considered:** stdlib `ast`/`inspect`/`re`/`types`/`sys` (read at use); `pytest.MonkeyPatch.setattr` (single target — why the sweep is bespoke, as adversary-r2 §9 read); no production mechanism specified (tests only).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 18 new shared/test-substrate symbols, all dispositioned (§DRY): 3 EXTENDED (`module_level_bindings_of`, the generator-discovery trio, `relation_endpoints`), 1 REUSED base (`_normalise_statement`), the rest HAND-ROLLED with reasons (incl. `FakeAgentRegistry._shared_identifier_predicate`, the amendment-5 guard seam).
- **Graded:** n/a — this is the contract author's report, not a verdict on another agent's artifact.
- **decisions-needed:** none open. For the lead's builder brief (amendment-5 §W): the builder deletes the fake's `except ImportError` guard in REFACTOR (the conditional pin reds until it does) and deletes both `pending_contracts.yaml` entries (`…-r2`, `…-r3`) with the build — all 11 self-destruct on the built world. Builder notes (MP-F docstring pair, MP-C constant, A4-bis home body) are in `test_agent_governance_63c_i_a.py`'s module docstring. Finding #477 filed (lore_impact covering-tests noise).
- **receipt pointers:** §FORKS (all RULED) · §ITEMS · §DUAL (D1–D17) · §DRY · §MUT · §RED · §SAT · §GATES · §INSTRUMENTS.

## Capability check (brief-base §4)
- Reachable and used: `Read`/`Edit`/`Write`, `git`, `uv run pytest/ruff`, `./scripts/typecheck.sh`, `./scripts/scratch_copy.sh`, `scripts/mutation_proof.py`, `scripts/pending_contract_gate.py`, the lore MCP (register/heartbeat/send/drain, `lore_search`, `lore_get_symbol`, `lore_impact`, `lore_index`, `lore_findings`), the test store `ws://127.0.0.1:18000`. `:18500` and the production TEI embedder were never touched.
- **grep/rg are hook-blocked (#473)** — every textual sweep here is `awk` over `git ls-files` (bare patterns), said per the dogfood protocol: the `AGENT_NAME_PATTERN` read sweep, the `generate_*_ddl` discovery-copy sweep (FORK-B — lore's semantic search found one of the two copies, `_all_schema_ddl`; the awk sweep found the second), the retired-resolver-name corpse sweep, the `_comms_fakes` consumer list. One command was refused by the hook because a pipe contained `grep`; re-run with `awk`.
- lore friction, FILED as finding #477 (area `lore_impact`): `lore_impact("patch_shared_object_everywhere")` lists 418 "covering tests" that are simply every symbol of `_governed_contract` (module-level co-location, not coverage); the 5 test references it counts matched the awk sweep.
- Host memory: every targeted run was ONE pytest session of mine at `-n 8`; other sessions' small pytest processes (another project, ≈145 MB each) were running throughout.

## Progress log (appended per milestone)
- 2026-09-24: read brief-base v16, store reference, amendments 1–4, base ruling pointers, adversary-r2 §0–§14 + §A, r2 author report. Reference build `ref_build_r3.py` = adversary-r2 `my_ref_build.py` verbatim + the MP-C named constant, applied in `scratch_copy.sh` copy `…/scratchpad/ref` (branch `r3-ref`, ruff clean). Provenance: `…/scratchpad/ref/loremaster/loremaster/__init__.py`.
- 2026-09-24: **r3a committed `11cbfb2`** (items 1–6). Lane receipts in §MUT (r3a). HEAD-side RED diff vs the r2 baseline in §RED (r3a).

## §FORKS (written BEFORE acting on them — brief §ESCALATION)

### FORK-A — item 7's "⊇ pin" (amendment-4 §MP-D point 1): two readings that produce different code
- **Text:** *"a pin that this derived set ⊇ `ALL_DDL_GENERATORS` (RED the day the scaffold's hand-list and the module disagree — today it names the two unswept emitters)"*; §E: *"item 7's ⊇ pin makes it loud on every run until the scaffold derives its own set."*
- **Reading (a), literal:** `derived ⊇ hand-list` — measured 2026-09-24 at `11cbfb2`: 15 derived `generate_*_ddl`, 10 hand-listed, all 10 ∈ derived → **GREEN today**; it names nothing and only reds if the hand-list names a generator the module lost.
- **Reading (b), the parenthetical:** `hand-list ⊇ derived` (or its composition-aware form: every derived generator's emitted statements are covered by the hand-list's union) — **RED today** naming `generate_lease_ddl` + `generate_floor_calibration_ddl`. ⚠ A committed pin that is RED on a CORRECT build makes this brief's SATISFIABILITY receipt ("0 failed on the FULL suite") **impossible**, and it is RED_ORPHANED under currency (the gap is outside 63c).
- **Reading (c), my recommendation — PIN THE MISS (CLAUDE.md "WHEN YOU CANNOT CLOSE A HOLE, PIN IT"):** assert `derived ⊇ hand-list` (a) AND `{generator : its emitted statements ⊄ the hand-list's union} == {generate_lease_ddl, generate_floor_calibration_ddl}` EXACTLY, with the message *"KNOWN BOUND (the ALL_DDL_GENERATORS hand-list gap, amendment-4 §E) — if you closed it deliberately, delete this set and say so"*. GREEN today (SAT holds), RED the day the gap GROWS (a third unswept emitter) or CLOSES (forces the deliberate deletion). It names the two emitters on every read of the source, not on every run.
- **Status:** RULED — amendment-5 (`26511f0`) ratified (c); the (a) leg is kept with a docstring stating it is vacuous-by-import; the decision point (the scaffold-gap finding's fix deletes the pin) is in the pin's docstring.

### FORK-B — item 7's "generator set by inspection" already exists TWICE in the test tree (ONE IMPLEMENTATION)
- **Found (awk, bare pattern `startswith("generate_")|endswith("_ddl")` over `git ls-files loremaster/tests`):** `test_ddl_write_target_coverage_124.py::_ddl_generators` + `_emit` (derive by `inspect.getmembers`, pass `dim` when accepted) and `test_principal_keys_schema.py::_all_schema_ddl` (same derivation, returns the union text). Item 7 needs exactly that property → writing it inside `_governed_contract` would be **copy #3**.
- **What I did (EXTENDED, not forked):** lifted ONE `schema_ddl_generators()` + `emit_schema_ddl()` into the shared scaffold `_enforced_relations_scaffold.py` (beside `MIGRATION_DIM`/`statements`), routed item 7 through it, and **re-pointed the two private copies to delegate to it** (two one-line bodies; their tests unchanged). Proven by mutation (§MUT r3b: perturb the shared derivation → all three consumers' pins red).
- **Alternative (if the lead rules the fold out of scope):** revert the two delegations; item 7 then keeps the lifted helper and the two old copies remain (copy #3 exists — I would file it as a finding). Recommendation: keep the fold (≈6 changed lines, in the writable set, found in-session).
- **Status:** RULED — amendment-5 ratified the lift, both folds and the `_rebind_everywhere` extraction, with a rider: my lifted `emit_schema_ddl` passed `dim` only when REQUIRED (a narrowing of both retired copies' "whenever present") — restored, DUAL row D17, pinned by `test_emit_threads_dim_WHENEVER_present_and_fails_closed_on_any_other_required_parameter` (mutation DIM: PROOF HELD); the `inspect.isfunction` membership bound is now stated in `schema_ddl_generators`' docstring.

### FORK-C — amendment-3 F-2's HEAD-RED premise is FALSE, measured (item 8)
- **Ruled mechanism (amendment-3 F-2):** the fake imports `is_legal_identifier` at CALL time inside `register`; *"The RED population does not grow: every fake-driven register is already HEAD-RED on the `session_keep_id` seam."*
- **Measured 2026-09-24 at `11cbfb2` + the mirror:** the 11 files importing `_comms_fakes` (`test_agent_capability`, `test_agent_registry`, `test_blocks_edge`, `test_brief_ledger`, `test_comms_fleet_grouping`, `test_comms_footer`, `test_comms_promise_registry`, `test_comms_render_architecture`, `test_comms_tool`, `test_enforced_relations`, `test_query_tasks_bounded`), `pytest -n 8`, HEAD production: **without the mirror `55 failed, 2006 passed`; with the ruled deferred import `287 failed, 1774 passed`** — **232 tests that are GREEN at HEAD go RED** (every tokenless fake-driven register — `(None, None)` is legal at HEAD and never touched the `session_keep_id` seam — now raises `ImportError`). Diff instrument `diffred.py` (§INSTRUMENTS); junit `fake_without.xml` / `fake_with.xml`.
- **Reading (a) — as ruled:** accept +232 HEAD reds, all one missing-seam class (`ImportError: cannot import name 'is_legal_identifier'`), greened by the builder's first GATING symbol. Cost: 232 unrelated pins carry no signal at HEAD for the build's duration, and the r3b commit alone turns 232 green tests red on `feat/surreal-unification`.
- **Reading (b) — my recommendation:** the call-time import guarded by `except ImportError` → the IDENTITY leg is inert until the symbol exists (the `is_blank` leg is live at HEAD — it already exists). Nothing the contract relies on is hidden: the F-2 mirror pin's identity legs stay RED at HEAD (legibly — the fake does not refuse), and every real-registry MOVE pin imports `lorerunes.is_legal_identifier` directly. After the build the guard is dead code; a builder that later deletes the symbol reds the MOVE pins first. Measured growth under (b): reported in §RED (r3b).
- **Status:** RULED — amendment-5 ratified (b) with riders, all applied: the guard lives in ONE helper `FakeAgentRegistry._shared_identifier_predicate()` (narrow `except ImportError`, docstring names it a HEAD-RED ACCOMMODATION + removal trigger); the conditional pin `test_agent_registry.py::test_the_fakes_HEAD_RED_import_guard_is_deleted_once_the_predicate_exists` is GREEN at HEAD (with an anti-vacuity control that the scan sees the guard) and RED once the predicate exists with the guard present (mutation GUARD: PROOF HELD); the reference models the builder's one granted test-tree edit (`builder_guard_deletion.py`, §INSTRUMENTS). The two HEAD mypy codes the guarded import raises are registered in the r2 entry's `_comms_fakes.py` row.
- 2026-09-24 (dated history): r3b in progress (uncommitted, pending FORK-A/C): item 7 re-keyed (emitted-DDL resolver + shared generator discovery, FORK-B fold), item 8 (fake mirror + parity matrix + fake consumer legs), item 9 fold done — verdict-neutral at HEAD (135/135 before and after) and both private-copy-wearing-the-shared-name builds measured: old instrument FALSE-CLEARS (69/69, 66/66), folded instrument PROOF HELD (2 and 11 red).

## §ITEMS — per worklist item (amendment-4 §W), measured 2026-09-24
Wrong-build receipts are the lane driver's verdict lines (§MUT); "HEAD" = production at `c98b8cb`/`11cbfb2` (production untouched by this contract).

| # | class | pin file::test | wrong build killed (receipt) |
|---|---|---|---|
| 1 | GATING | `test_agent_registry.py::TestQ3RegisterValidatesIdentityBeforeStoreIO63cIA::test_the_identifier_decision_is_the_SHARED_is_legal_identifier[{name,session}-{register,refuse-policy,skip-policy,fake}]` + `::TestTheIdentifierPatternIsReadOnlyForProseOutsideLorerunes63cIA` (real-tree allowlist scan + 7 positive / 5 negative synthetic controls) | **N1** PROOF HELD (skip-policy ×2 + AST pin) · **N1b** PROOF HELD (same 3) · **N1c** PROOF HELD (skip-policy ×2; AST pin blind BY DESIGN — stated in its threat model) |
| 2 | GATING | `test_agent_governance_63c_i_a.py::TestAHostileNamedLegacyAgentCannotReRegisterButStillTouches63cIA::test_a_hostile_legacy_row_is_refused_on_re_register_and_still_touches[<13 corpus shapes>-{name,session}]` | **NF2** (MOVE only on the CREATE branch) PROOF HELD 26/26 |
| 3 | GATING | `…::TestTheRegistryProvenanceSeam63cIA::test_an_inconsistent_provenance_pair_is_refused_on_the_RE_REGISTER_path_too[owner-without-keep, keep-without-owner]` | **N2** PROOF HELD 2/2 |
| 4 | GATING | `…::TestTheRegistryProvenanceSeam63cIA::test_a_credentialed_re_register_never_stamps_an_UNSTAMPED_row_mint_once_for_every_row[alpha-register, legacy-seed]` + builder note (docstring → the pair) in the module docstring | **N10** PROOF HELD 2/2 |
| 5 | GATING | `…::TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent[below-cap, at-cap, above-cap]` (reads `principals._REFUSAL_ID_SAMPLE_SIZE`; above-cap = bound + 15) | **N3** PROOF HELD (above-cap) · **C3** (constant 10→3, pin follows) SURVIVES as declared · **LIT10** (literal `[:10]` beside constant 3) PROOF HELD (above-cap) |
| 6 | GATING | `_governed_contract.patch_shared_object_everywhere` (identity alone, `expect_in`, refused value types) + `identity_sweep_miss_message` + `…::TestThePatchSharedObjectInstrument63cIA` (5 self-tests) | **IM1** (r2 name∧identity) PROOF HELD · **IM2** (name-only) PROOF HELD 3/3 · **ALIAS** (a CORRECT aliased `keep_scope` build) SURVIVES as declared · **IM3** (the ONE finder finds nothing) 27/27 executed declared ids red, 0 unexpected, 4 declared ids skip-by-design (§MUT) |
| 7 | NON-GATING | `_governed_contract.governed_populations(*, emitted_ddl=…)` over `_enforced_relations_scaffold.emitted_schema_ddl()`; `test_memory_enforcement_63b_ia.py::…::{test_the_population_derivation_reach_is_a_checked_variable, test_a_PARTIAL_trio_never_joins_and_the_FULL_trio_always_does[×2], test_the_relation_leg_reads_the_EMITTED_endpoints[×4], test_a_relation_statement_whose_endpoints_cannot_be_parsed_FAILS_CLOSED, test_the_old_SOURCE_parameter_is_refused_loudly}`; `test_message_enforcement_63b_ii_a.py::TestTheGovernedPopulationSetGrows::{test_the_population_set_is_an_OUTPUT_not_a_hand_list, test_the_generator_corpus_is_DERIVED_by_inspection_and_non_vacuous, test_KNOWN_BOUND_the_ALL_DDL_GENERATORS_hand_list_gap_is_EXACTLY_lease_and_floor_calibration, test_the_relation_INVENTORY_and_the_POPULATION_agree}` | **N4h** (adversary-r2 survivor: keyword endpoints + enforced + inventory row) PROOF HELD (five-set) · **DIM** (`dim` only when required) PROOF HELD · **R1** any-column node leg PROOF HELD 4/4 · **R2** IN-only PROOF HELD · **R3** fail-open parser PROOF HELD · **GD1/GD2** (FORK-B sharing) — §MUT |
| 8 | NON-GATING | `_comms_fakes.FakeAgentRegistry._refuse_what_the_writer_refuses` + `_shared_identifier_predicate` (F-2 mirror, FORK-C guard); `test_agent_registry.py::test_the_fakes_HEAD_RED_import_guard_is_deleted_once_the_predicate_exists`; `test_agent_registry.py::TestTheFakeRegistryMirrorsTheWriter63cIA::test_the_fake_and_the_real_writer_agree_on_outcome_class_and_stamps[36 rows]`; fake legs on the two shared-decision pins (`[{name,session}-fake]`, `test_the_blank_role_rule_is_the_SHARED_is_blank[fake]`) | **N5** PROOF HELD 2/2 · **F2a** (fake drops identity mirror) PROOF HELD 28/28 · **F2b** (private `strip()` in the fake) PROOF HELD · **GUARD** (guard kept after the build) PROOF HELD |
| 9 | NON-GATING | `test_secret_typing.py::TestTheBlanknessPredicateIsGENUINELYSHARED` + `test_engine_rejection_seam.py::TestSharingProvenByMutation` folded onto the shared instrument | STOP-rule: verdict-neutral at HEAD (135/135 before AND after). Private-copy-WEARING-THE-SHARED-NAME builds: **old instrument FALSE-CLEARS** (69/69, 66/66 passed); **folded: PROOF HELD** (2 and 11 red) via `scripts/mutation_proof.py` |
| 10 | NON-GATING | `test_agent_governance_63c_i_a.py::_statement_shape` / `_assert_the_backfill_statement_shape` + `TestTheBackfillShapeAssertNormalisesSpellingNeverWidens63cIA` (4 correct spellings pass, 3 wrong statements fail) | **R6** (normaliser widened back to raw) PROOF HELD 3/3 |
| 11 | PROSE | heartbeat control docstring (E2-bis: current emitter then frozen LAST; kill set (i)–(iii)); regex-twin pin docstring (F-5 bound · MISS-only direction · re-open trigger, citing `parse_production_trees` not the retired `_schema_string_constants`) | n/a (prose) |

## §DUAL — every pin deleted, inverted or re-keyed (an in-place DUAL comment sits at each)
| # | what changed | virtue it carried | where the virtue now lives |
|---|---|---|---|
| D1 | R-Q5-1: one fixture of 2 traps, "EVERY id named" → 3 populations; "every id" INVERTED above the cap | the refusal names its rows | below-cap/at-cap legs (every id) + above-cap leg (exactly `bound` ids) |
| D2 | decision pin `[name]/[session]` → `[field-consumer]`; `assert any(...startswith("lorerunes"))` removed | register + refuse-policy share the decision; the probe landed | same two legs + `expect_in` (the sweep RAISES if the home was not patched) |
| D3 | `patch_shared_object_everywhere` NAME ∧ identity → identity alone + `expect_in` | "an unrelated same-named attribute is never clobbered" | preserved: identity never touches a different object (self-test `…WEARING_THE_SHARED_NAME…`) |
| D4 | footer `test_perturbing_the_SHARED_predicate_moves_EVERY_members_refusal`: `assert patched` → `expect_in=("loremaster.agents",)` | non-vacuity | the instrument's expectation (holds before AND after the MOVE) |
| D5 | regex-twin + blank pins: `assert any(startswith lorerunes)` / `assert patched` removed | non-vacuity | `expect_in` default (`lorerunes`) |
| D6 | `_logging_fixtures._rebind_everywhere` loop body → `module_level_bindings_of` | by-identity reach across `sys.modules` | the ONE finder (IM3 proves both instruments route through it) |
| D7 | AST resolver RETIRED: `_GOVERNED_FIELD_SPECS_EMITTER`, `_DEFINE_RELATION_EMITTER`, `_schema_string_constants`, `_resolve_schema_table`, `_governed_node_tables`, `_governed_relation_tables` | (1) an OUTPUT, never a hand-list; (2) a lone packet-62 `owner_principal` never joins | (1) `schema_ddl_generators` + growth pins; (2) the FULL-TRIO node leg, pinned both ways (`test_a_PARTIAL_trio…`) |
| D8 | `governed_populations(schema_source=…)` → `governed_populations(*, emitted_ddl=…)` | synthetic reach input | same, keyword-only + renamed; `test_the_old_SOURCE_parameter_is_refused_loudly` |
| D9 | ia reach pin + ii-a OUTPUT pin: Python-source fixtures → emitted-DDL fixtures | growth / F-TRAP-1 / relation join | same assertions, DDL text (`synthetic_field_ddl`, trio names derived) |
| D10 | ia `test_a_relation_over_a_RE_EXPORTED_endpoint_joins_and_a_non_str_re_export_does_not` DELETED | a re-exported endpoint joins; a non-table name does not | `test_the_relation_leg_reads_the_EMITTED_endpoints[in-governed, no-governed-endpoint]` + the real-tree five-set (`briefed` via `AGENT_TABLE`) + the inventory cross-check |
| D11 | `test_secret_typing…._patch_everywhere` DELETED (→ `_patch_the_shared_predicate`, a call of the shared instrument) | import-style agnostic; `patched >= 1` | shared instrument + `expect_in=("lorerunes",)` |
| D12 | `test_engine_rejection_seam._patch_everywhere` DELETED | same; `assert patched` | shared instrument + `expect_in` (`lorerunes` / `loremaster.store._txn`) |
| D13 | `test_ddl_write_target_coverage_124._ddl_generators` / `_emit` bodies → delegate | derived generator set; `dim` supplied | `schema_ddl_generators` / `emit_schema_ddl` (GD1 proves routing) |
| D14 | `test_principal_keys_schema._all_schema_ddl` body → delegate | derived union corpus | `emitted_schema_ddl(dim=NONDEFAULT_DIM)` (GD2 proves routing) |
| D15 | blank-role pin (register only) → `[register, fake]` | register uses the shared `is_blank` | register leg unchanged + fake leg |
| D17 | `emit_schema_ddl` (r3b draft) passed `dim` only when REQUIRED → WHENEVER present (amendment-5 FORK-B rider) | both retired copies threaded `dim` whenever the parameter existed | `emit_schema_ddl` + `test_emit_threads_dim_WHENEVER_present…` |
| D16 | exempt-token pin: raw `startswith/endswith/"<col> ="` → R-6 normalised shape | the backfill is ONE scope-keyed 3-column UPDATE | `_assert_the_backfill_statement_shape` + its wrong-statement controls; token==executed EQUALITY still F5's unchanged `_normalise_statement` |

## §DRY — reuse ledger (brief-base §6)
| new symbol | lore query / sweep run | what it returned | disposition |
|---|---|---|---|
| `_logging_fixtures.module_level_bindings_of` | `lore_impact("patch_shared_object_everywhere")`; `lore_search("AST scan … allowlist only .pattern reads")` surfaced `_logging_fixtures` (`parse_production_trees`), whose file carries `_rebind_everywhere` | `_rebind_everywhere` = an existing identity-alone loop (a 4th copy no amendment named) | **EXTENDED `_rebind_everywhere`**: its loop lifted into the finder; both instruments call it (IM3) |
| `_governed_contract.identity_sweep_miss_message`, `_IDENTITY_SWEEP_REFUSED_TYPES` | same | nothing | **HAND-ROLLED** — the ONE honest failure text (MP-G rider 2), one home so the stated bound cannot drift |
| `_enforced_relations_scaffold.schema_ddl_generators` / `emit_schema_ddl` / `emitted_schema_ddl` | `lore_search("ALL_DDL_GENERATORS hand-list misses …")` → `test_principal_keys_schema._all_schema_ddl`; awk bare sweep `startswith("generate_")|endswith("_ddl")` → also `test_ddl_write_target_coverage_124._ddl_generators/_emit` | two private copies of the same derivation | **EXTENDED** (lifted to the shared scaffold; both copies now delegate — FORK-B; GD1/GD2 prove routing) |
| `_enforced_relations_scaffold.relation_endpoints` (+ `_DEFINE_RELATION_RE` IN/OUT groups) | read `relation_table_statements` | the existing relation parser (name only) | **EXTENDED** (ruling MP-D point 3 names this regex) |
| `_governed_contract.governed_trio_columns`, `governed_node_tables`, `governed_relation_tables`, `synthetic_field_ddl`, `_DEFINE_FIELD_ON_RE` | read `field_statement` / `_DEFINE_FIELD` / `ddl_statements` (same module) | `field_statement(ddl, table, column)` answers one pair but ASSERTS ≤1 match — the union corpus defines `memory.owner_principal` TWICE (measured: 2; `generate_ddl` folds slices standalone generators also emit) and it has no `IF NOT EXISTS` arm | **HAND-ROLLED** (pair extraction), reason stated; trio names REUSE `_governed_field_specs` |
| `test_agent_registry._pattern_decision_sites` / `_watched_pattern_names` | `lore_search` (above) → `test_anchored_pattern_seam.py` (a different property: `$`-anchored patterns under `.match`); reach via `parse_production_trees` + `assert_scan_reached_every_member` | no existing "reads of a named object" scan | **HAND-ROLLED** property scan; tree parse + reach REUSED |
| `test_agent_governance…_statement_shape` / `_assert_the_backfill_statement_shape` | read `_governed_contract._normalise_statement` | the F5 leg-2 normaliser | **REUSED** for the equality; shape layer added on top (R-6) |
| `_comms_fakes.FakeAgentRegistry._refuse_what_the_writer_refuses` | — | — | extraction of the fake's own A3 check (branch limit) + ROUTING to `lorerunes.is_blank` / `is_legal_identifier` (never a restated rule) |
| `_comms_fakes.FakeAgentRegistry._shared_identifier_predicate` | — (amendment-5 FORK-C rider 1 names the seam) | — | **HAND-ROLLED** — the ONE guarded call-time read (a HEAD-RED accommodation with a removal trigger and a conditional pin); routes to `lorerunes.is_legal_identifier`, decides nothing itself |
| test-local: `_parity_cases`, `_real_outcome`, `_fake_outcome`, `_identifier_consumer_refuses`, `_server_policy_refuses`, `_registry_refuses`, `_mpg_*` synthetic objects | — | — | fixture-local |

## §MUT — mutation proofs (measured 2026-09-24)
**Lane.** One `scratch_copy.sh` copy, `…/scratchpad/ref` — provenance printed by the driver: `loremaster.__file__ = /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/3bff958a-e5fb-4126-b391-762dd6a032ae/scratchpad/ref/loremaster/loremaster/__init__.py`. Branch `r3-ref` = `ref_build_r3.py` + the r3 tests. Each wrong build is applied on top by `wbs_r3.py` (exactly-once anchors), its DECLARED expected-RED ids are resolved from `pytest --collect-only -q` listings taken BEFORE any wrong-build run, and `run_lane_r3.sh` diffs observed vs declared BOTH ways, then restores (`restored: 0 dirty paths` after every batch). Multi-edit and declared-to-survive builds need this driver (`scripts/mutation_proof.py` requires a non-empty `--expect-red` and one anchor); the single-anchor fold proofs used `scripts/mutation_proof.py` itself.

**r3a** — run set: `test_agent_governance_63c_i_a.py`, `test_agent_registry.py`, `test_comms_footer.py` (531 collected); IM builds add `test_store_seam_one_derivation.py` + `test_ast_reach_helpers.py`.
```
N1   3 failed, 528 passed  · PROOF HELD — declared RED set fired EXACTLY; observed=3 declared=3
N1b  3 failed, 528 passed  · PROOF HELD — observed=3 declared=3
N1c  2 failed, 529 passed  · PROOF HELD — observed=2 declared=2
N2   2 failed, 529 passed  · PROOF HELD — observed=2 declared=2
N3   1 failed, 530 passed  · PROOF HELD — observed=1 declared=1
C3   531 passed            · SURVIVES as DECLARED (0 red)   [the pin READS the constant]
LIT10 1 failed, 530 passed · PROOF HELD — observed=1 declared=1
N10  2 failed, 529 passed  · PROOF HELD — observed=2 declared=2
NF2  26 failed, 505 passed · PROOF HELD — observed=26 declared=26
ALIAS 531 passed           · SURVIVES as DECLARED (0 red)   [MP-G: a correct aliased build is GREEN]
IM1  1 failed, 603 passed, 4 skipped · PROOF HELD — observed=1 declared=1
IM2  3 failed, 601 passed, 4 skipped · PROOF HELD — observed=3 declared=3
IM3  27 failed, 577 passed, 4 skipped · PROOF FAILED (set differs); observed=27 declared=31
     DECLARED-STILL-GREEN ×4: test_ast_reach_helpers.py::TestSharingProvenByMutation::test_each_real_fixture_consumer_reddens_when_the_shared_parser_is_dropped[test_backoff_seam.py | test_comms_footer.py | test_secret_leak_vectors.py | test_secret_typing.py]
```
IM3 reading: those 4 ids are SKIPPED on every build (`… is an _ASUB_PARSE_SKIP adopter`, read from the junit) — my declaration over-included skip-parametrised ids; every EXECUTED declared id went red and nothing unexpected did. Recorded as a misprediction, not re-declared after the fact.

**r3b** — run set: the 22 files in `r3b_files.txt` (every touched file + every `_comms_fakes` / scaffold / `_rebind_everywhere` consumer; 2576 collected).
```
N4h  1 failed, 2554 passed · PROOF HELD — observed=1 declared=1
R1   4 failed, 2549 passed · PROOF HELD — observed=4 declared=4
R2   1 failed, 2552 passed · PROOF HELD — observed=1 declared=1
R3   1 failed, 2552 passed · PROOF HELD — observed=1 declared=1
GD1  4 failed, 2549 passed · PROOF FAILED (set differs); observed=4 declared=3
     UNEXPECTED-RED test_ddl_write_target_coverage_124.py::TestTheCoverageInvariantDiscriminates::test_a_planted_undeclared_constant_would_redden_the_invariant
GD2  6 failed, 2547 passed · PROOF HELD — observed=6 declared=6
N5   2 failed, 2551 passed · PROOF HELD — observed=2 declared=2
F2a  28 failed, 2525 passed · PROOF HELD — observed=28 declared=28
F2b  1 failed, 2552 passed · PROOF HELD — observed=1 declared=1
R6   3 failed, 2550 passed · PROOF HELD — observed=3 declared=3
```
GD1 reading: all 3 declared fired; the extra red is a THIRD coverage_124 pin that also reads the shared discovery (misprediction in the safe direction — more consumers moved than I predicted). GD2 was then declared and HELD exactly, exercising the `principal_keys` delegation GD1 could not (lease emits no `record<principal>`).

**amendment-5 riders — `scripts/mutation_proof.py`, lane `ref` (lane HEAD `3688b2a` = reference + final tests + the builder's guard deletion):**
- GUARD (restore the fake's `try/except ImportError` on the built world): `test_agent_registry.py` → **PROOF HELD — the declared RED set fired EXACTLY: [`test_the_fakes_HEAD_RED_import_guard_is_deleted_once_the_predicate_exists`]**, restored byte-exact.
- DIM (`emit_schema_ddl` back to required-only `dim`): run over ii-a + principal_keys + coverage_124 → **PROOF HELD** [`TestTheGovernedPopulationSetGrows::test_emit_threads_dim_WHENEVER_present_and_fails_closed_on_any_other_required_parameter`], restored byte-exact.

**Item 9 fold (STOP-rule) — `scripts/mutation_proof.py`, lane `ref`:**
- SN-config (`config.py`: `from lorerunes import is_blank` → a PRIVATE `def is_blank` wearing the shared name): `2 failed, 133 passed` · `tree restored byte-exact (… md5 2b0dbb12ed19eed1fafc9a3b4ec31562)` · **PROOF HELD** (`test_MUTATING_the_predicate_moves_BOTH_callers`, `test_the_mutation_probe_can_actually_SEE_a_change`). Same build with the PRE-fold `test_secret_typing.py` (`11cbfb2`): **`69 passed` — the name-keyed instrument FALSE-CLEARS it** (amendment-3 F-3's claim, now measured).
- SN-txn (`_txn.py`: `from lorerunes import reclassify` → a frozen private `reclassify` wearing the name): `11 failed` · restored byte-exact (md5 `58f657eb7c58f8e9f1d54ccbf6cdedb5`) · **PROOF HELD** (all 11 `test_dropping_LAYER1_reclassify_moves_every_routed_path[…]`). Pre-fold file: **`66 passed` — false clear**.
- GREEN before/after the fold at HEAD: `135 passed` / `135 passed`, diff of the two junit red sets empty → **no pin changed verdict; the STOP-rule did not fire.**

## §RED — main checkout, tests only, production at HEAD (measured 2026-09-24)
- **r3a** (files: governance, registry, footer, store_seam, ast_reach): `93 failed, 511 passed, 4 skipped`. Diff vs the r2 baseline (same two contract files with `11cbfb2`'s parent tests, stashed with a `cp -a` + md5 backup, restored and md5-verified): **every NEW red is a NEW test id (40 ids)**; the only "no-longer-red" ids are the 3 RE-KEYED ones (R-Q5-1 unparametrised → 3 legs; decision pin `[name]`/`[session]` → consumer axis); **zero previously-green tests went red**. Substrate consumers green: `test_store_seam_one_derivation` 23/23, `test_ast_reach_helpers` 50/50, `test_comms_footer` 248/248.
- **r3b** (the 22-file set): `146 failed, 2404 passed, 23 skipped, 3 errors`; vs the r3a-committed tests on the same set (`110 failed, 2386 passed, 3 errors`): **36 new reds, all NEW test ids** (parity matrix 34, decision `[name-fake]`/`[session-fake]`), plus the re-keyed blank pin `[register]`; **zero previously-green tests went red** (under FORK-C's guard). The 3 setup errors are identical in both runs (pre-existing r2 fallout in `test_memory_enforcement_63b_ia.py`, missing-seam `session_keep_id`).
- **Final, after amendment-5 (the committed r3b tree):** `146 failed, 2406 passed, 23 skipped, 3 errors` over the same 22 files — identical red set to the pre-amendment-5 run; the two new pins (guard conditional, `dim` rider) are GREEN at HEAD by design; still zero previously-green tests red.
- **Classification of every HEAD red in the r3b set** (`classify.py`, junit message shapes): 61 store ASSERT still lands (right reason: the Q3 DROP/MOVE unbuilt — incl. the NF-2 legs and the parity hostile/blank rows' real side) · 61 `session_keep_id` kwarg absent · 10 `lorerunes` symbol absent · 3 `principals._REFUSAL_ID_SAMPLE_SIZE` absent · 7 governed column/stamp unbuilt · 1 AST second decider (`server.py`'s `AGENT_NAME_PATTERN.fullmatch`) · 1 five-set (agent/briefed unbuilt) · 1 tokenless spy · 1 householded joiner · 1 identity sweep did not move (HEAD has no shared blank decision in register) · 2 r2 signature pins (kwarg absent). **Unclassified: 0. No pin is RED for a wrong reason.**
- Right-reason spot checks: the AST pin names `loremaster/loremaster/server.py:6622: AGENT_NAME_PATTERN.fullmatch(value)`; NF-2 legs fail with the labelled *"RED-at-HEAD (right reason) … refused by the STILL-PRESENT charset ASSERT"*; the exempt-token pin fails on HEAD's owner-keyed statement.

## §SAT — satisfiability (measured 2026-09-24)
- **Reference:** `ref_build_r3.py` + `builder_guard_deletion.py` (§INSTRUMENTS) = adversary-r2 `my_ref_build.py` verbatim (REPORT-adversary-63c-i-a-r2 §A.1) + the MP-C named constant `_REFUSAL_ID_SAMPLE_SIZE = 10` + deletion of `agents.py`'s now-unused `import re`; lane `…/scratchpad/ref`, provenance `…/scratchpad/ref/loremaster/loremaster/__init__.py`. `uv run ruff check .` in the lane → `All checks passed!`.
- **Targeted, on the reference (all r3 tests):** r3a files `308 passed` (governance + registry + footer class); r3b 22-file set `2553 passed, 23 skipped` after fixing my own `count() GROUP ALL` fixture bug (registry file `246 passed`); every lane base run is green (`531 passed` r3a set; `2553 passed` r3b set).
- **FULL SUITE ALONE at `-n 12` (measured 2026-09-24):** lane HEAD `3688b2a` (reference + final r3 tests + the builder's granted guard deletion), 0 dirty paths, provenance `…/scratchpad/ref/loremaster/loremaster/__init__.py`, start 19:03:28 with 36 GB available, no other lore pytest running → **`11405 passed, 62 skipped, 3 xfailed, 7 warnings in 533.72s (0:08:53)` — 0 failed, 0 errors, EXIT 0.** (An earlier attempt was stopped at 55%, all green so far, because amendment-5 changed the tests; it is not counted.) Valid for the ruled readings — FORK-A (c), FORK-C (b).
- **Typecheck on the built world** (`pending_contract_gate.py --currency --legs typecheck,ruff` in the lane, registry synced): the ONLY typecheck residuals are **11 SELF-DESTRUCTs** — 9 files of `packet-63c-i-a-contract-r2` + `lorerunes.is_legal_identifier` now RESOLVES (its `_comms_fakes.py` row) + 1 file of `packet-63c-i-a-contract-r3` — i.e. no real mypy error on the build, and every entry discharges exactly when it should (the builder deletes both entries with the build). ruff GREEN.
- Lint-cleanup leg: the only lint-demanded production cleanup on the reference is `agents.py`'s unused `import re` (same as adversary-r2 §2).

## §GATES (main checkout, measured 2026-09-24, r3b working tree)
- `uv run ruff check .` → `All checks passed!`
- `./scripts/typecheck.sh` → **`Found 17 errors in 10 files`** (final, after amendment-5) in `loremaster/tests`, all missing-seam: the 15 below + `_comms_fakes.py`'s guarded import (`attr-defined` on `lorerunes.is_legal_identifier` + `no-any-return`, both HEAD-only, registered in the r2 entry). The 15: `session_keep_id` call-args (r2's 10 + 1 new from the parity matrix, registered in the r2 entry's `test_agent_registry.py` row) · `lorerunes.is_legal_identifier`/`AGENT_NAME_PATTERN` attr-defined ×3 · `principals._REFUSAL_ID_SAMPLE_SIZE` attr-defined ×1 (new entry `packet-63c-i-a-contract-r3`). Every other leg `Success`.
- `pending_contract_gate.py --verify-registry` → passes (`1 import-checked absent · 8 UNCHECKED (owner not importable)` — the kwarg liveness leg cannot import a call-arg name, as r2 reported).
- `pending_contract_gate.py --currency --legs typecheck,ruff` → **typecheck RED_ADJUDICATED — 17 residual(s), owned by `packet-63c-i-a-contract-r2` · `packet-63c-i-a-contract-r3`** · **ruff GREEN** · `CURRENCY: FAIL — claimed but never run: pytest` (the manifest runs pytest at `-n auto`, which #466 forbids; §RED is this revision's pytest instrument — said, not hidden).
- #461 check: every registered file is mypy-red until its symbol lands, so no entry can self-destruct early; the r3 entry discharges alone if the constant lands first (correct — its claim is then false).

## §INSTRUMENTS (pasted VERBATIM — scratch-only; the writable set excludes `scripts/`)

### `ref_build_r3.py`
```python
"""contract-63c-i-a-r3 reference = adversary-63c-i-a-r2 my_ref_build.py (verbatim, REPORT-adversary-63c-i-a-r2 §A.1) + the MP-C named constant.

adversary-63c-i-a-r2 — an INDEPENDENT reference (believed-correct) 63c-i-a build.

Written from the production source + amendment-2 §A1–A4, NOT from the r2 author's ref_build_r2.py.
Base legs (Q3 drop, W1-1 routing, Q5 scope-keyed migrate + row precondition) re-use the PRIOR
adversary's §A.1 anchors (b46d3f2 — a different author than the contract under grade); the A2/A3/A4
legs are my own.

Usage: uv run --no-project python my_ref_build.py <scratch-root>
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


def create(rel: str, body: str) -> None:
    path = ROOT / rel
    assert not path.exists(), f"{rel} already exists"
    path.write_text(body)


SCHEMA = "loremaster/loremaster/store/surreal_schema.py"
AGENTS = "loremaster/loremaster/agents.py"
SERVER = "loremaster/loremaster/server.py"
PRINCIPALS = "loremaster/loremaster/principals.py"
RUNES_INIT = "lorerunes/lorerunes/__init__.py"

# ---- Q3: drop name/session/role ASSERTs (KEEP status) -------------------------------------------
edit(
    SCHEMA,
    '    ("name", _CHUNK_STRING_TYPE, _IDENTIFIER_CHARSET_ASSERT),\n'
    '    ("session", _CHUNK_STRING_TYPE, _IDENTIFIER_CHARSET_ASSERT),\n'
    '    ("role", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),\n    ("model"',
    '    ("name", _CHUNK_STRING_TYPE, ""),\n'
    '    ("session", _CHUNK_STRING_TYPE, ""),\n'
    '    ("role", _CHUNK_STRING_TYPE, ""),\n    ("model"',
)
# ---- W1-1: the governed triple comes only from the ONE emitter ----------------------------------
edit(SCHEMA, '    ("owner_principal", "option<record<principal>>", ""),\n    # packet 62, Fork 1', "    # packet 62, Fork 1")
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

# ---- A4: the identifier DECISION + the pattern MOVE to lorerunes ---------------------------------
create(
    "lorerunes/lorerunes/identifiers.py",
    '"""The comms identity charset — ONE pattern, ONE decision (63c-i-a amendment-2 A4)."""\n\n'
    "from __future__ import annotations\n\n"
    "import re\n\n"
    'AGENT_NAME_PATTERN: re.Pattern[str] = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")\n\n\n'
    "def is_legal_identifier(value: str) -> bool:\n"
    '    """Whether ``value`` matches ``AGENT_NAME_PATTERN`` IN FULL (``fullmatch``, finding #210)."""\n'
    "    return AGENT_NAME_PATTERN.fullmatch(value) is not None\n",
)
edit(
    RUNES_INIT,
    "from lorerunes.engine_rejection import reclassify\n",
    "from lorerunes.engine_rejection import reclassify\n"
    "from lorerunes.identifiers import AGENT_NAME_PATTERN, is_legal_identifier\n",
)
edit(RUNES_INIT, "__all__ = [\n", '__all__ = [\n    "AGENT_NAME_PATTERN",\n    "is_legal_identifier",\n')
edit(
    AGENTS,
    'AGENT_NAME_PATTERN: re.Pattern[str] = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")\n',
    "AGENT_NAME_PATTERN = _RUNES_AGENT_NAME_PATTERN  # re-export (A4: the pattern lives in lorerunes)\n",
)
edit(
    AGENTS,
    "from lorerunes import parse_credential\n",
    "from lorerunes import AGENT_NAME_PATTERN as _RUNES_AGENT_NAME_PATTERN\n"
    "from lorerunes import is_blank, is_legal_identifier, keep_scope, parse_credential\n",
)
edit(AGENTS, "from loremaster.render import render_attributed\n", "from loremaster.render import render_attributed, render_fenced\n")
edit(
    SERVER,
    "        return AGENT_NAME_PATTERN.fullmatch(value) is not None\n",
    "        from lorerunes import is_legal_identifier  # noqa: PLC0415 - house lazy-import idiom\n\n"
    "        return is_legal_identifier(value)\n",
)

# ---- A4 register MOVE (teaching) + A3 XOR + A2 stamp --------------------------------------------
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
    '                    f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern} (lowercase letters, "\n'
    "                    f\"digits, '_' or '-', 1-64 chars, starting with a letter or digit); nothing was \"\n"
    '                    f"written — register again with a legal {field_name}. The rejected value was:\\n"\n'
    '                    f"{render_fenced(value)}"\n'
    "                )\n"
    "        if is_blank(role):\n"
    "            raise InvalidAgentIdentityError(\n"
    '                "agent role must not be blank — nothing was written; register again with a role "\n'
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
edit(
    SERVER,
    "            cadence=cadence,\n            owner_principal_id=principal_bare,\n        )\n        now = datetime.now(UTC)\n        registered_age_s",
    "            cadence=cadence,\n            owner_principal_id=principal_bare,\n"
    "            session_keep_id=(\n"
    '                str(session_keep.id).split(":", 1)[-1] if session_keep is not None else None\n'
    "            ),\n"
    "        )\n        now = datetime.now(UTC)\n        registered_age_s",
)

# ---- Q5: scope-keyed 3-column migrate + §2.1 row precondition (prior adversary §A.1 anchors) ------
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
    "    already = await _owner_count(store, AGENT_TABLE, none=False)\n",
    "    unmigrated = await _scope_count(store, AGENT_TABLE, none=True)\n"
    "    already = await _scope_count(store, AGENT_TABLE, none=False)\n",
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
    "                f\"({', '.join(owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE])}) — \"\n"
    "                \"a multi-principal or half-applied store; \"\n"
    "                \"adjudicate these rows by hand before migrating (§2.1)\"\n"
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

# ---- MP-C (amendment 4): the refusal's id bound is a NAMED constant ------------------------------
edit(
    PRINCIPALS,
    "async def _migrate_agent_owner(\n",
    "#: The most agent ids an owned-but-unscoped refusal names (MP-C: a NAMED bound, never a literal).\n"
    "_REFUSAL_ID_SAMPLE_SIZE = 10\n\n\nasync def _migrate_agent_owner(\n",
)
# ruff F401: the pattern moved out of agents.py
edit(AGENTS, "import re\n", "")
print("r3 reference build applied (adversary-r2 my_ref_build.py + MP-C constant)")
```

### `wbs_r3.py`
```python
"""contract-63c-i-a-r3 — wrong builds applied ON TOP of the r3 reference (scratch lane, branch r3-ref + r3 tests).

Usage: uv run --no-project python wbs_r3.py <scratch-root> <WB-id> [--declared]
  --declared   print the DECLARED expected-RED node ids, resolved against collected_r3*.txt
               (``pytest --collect-only -q`` output taken BEFORE any wrong-build run), then exit.
Every edit asserts its anchor occurs EXACTLY once (a no-op mutation is a failed setup — #194).
Adversary-r2 builds (N1, N1b, N1c, N2, N3, N10) are re-expressed from REPORT-adversary-63c-i-a-r2.md §A.2
against the same anchors.
"""

import sys
from pathlib import Path

SCR = Path(__file__).resolve().parent
ROOT = Path(sys.argv[1])
WB = sys.argv[2]

SERVER = "loremaster/loremaster/server.py"
AGENTS = "loremaster/loremaster/agents.py"
PRINCIPALS = "loremaster/loremaster/principals.py"
GOVC = "loremaster/tests/_governed_contract.py"
FAKES = "loremaster/tests/_comms_fakes.py"

GOV = "test_agent_governance_63c_i_a.py"
REG = "test_agent_registry.py"

DECISION = "test_the_identifier_decision_is_the_SHARED_is_legal_identifier"
AST_PIN = "test_no_production_module_outside_lorerunes_DECIDES_with_the_pattern"
NF2 = "test_a_hostile_legacy_row_is_refused_on_re_register_and_still_touches"
MPB = "test_an_inconsistent_provenance_pair_is_refused_on_the_RE_REGISTER_path_too"
MPF = "test_a_credentialed_re_register_never_stamps_an_UNSTAMPED_row_mint_once_for_every_row"
RQ51 = "test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent"

# DECLARED expected-RED sets — (file fragment, node fragment) rules. WRITTEN BEFORE ANY RUN.
DECLARED: dict[str, list[tuple[str, str]]] = {
    # A4-bis: the server HOME keeps a private decision on the shared pattern (two deciders).
    "N1": [(REG, f"{DECISION}[name-skip-policy]"), (REG, f"{DECISION}[session-skip-policy]"), (REG, AST_PIN)],
    # ... drifting to .match (#210 class) on the home.
    "N1b": [(REG, f"{DECISION}[name-skip-policy]"), (REG, f"{DECISION}[session-skip-policy]"), (REG, AST_PIN)],
    # ... a private DRIFTED regex (never touches AGENT_NAME_PATTERN — the AST pin is blind BY DESIGN).
    "N1c": [(REG, f"{DECISION}[name-skip-policy]"), (REG, f"{DECISION}[session-skip-policy]")],
    # MP-B: A3's XOR only on the CREATE branch.
    "N2": [(GOV, MPB)],
    # MP-C: the refusal lists EVERY id (no bound).
    "N3": [(GOV, f"{RQ51}[above-cap]")],
    # MP-C sharing-by-mutation (a): move the NAMED constant 10 -> 3; the pin READS it, so it must follow.
    "C3": [],
    # MP-C (b): a LITERAL [:10] beside a constant of 3 — the literal no longer follows the constant.
    "LIT10": [(GOV, f"{RQ51}[above-cap]")],
    # MP-F: a re-register HEALS a NONE-scope row's scope + owner_agent (not the owner).
    "N10": [(GOV, MPF)],
    # NF-2: the identity/role checks run only on the CREATE branch (re-register skips the MOVE).
    "NF2": [(GOV, NF2)],
    # MP-G: a CORRECT build importing the shared formatter under an ALIAS — must SURVIVE.
    "ALIAS": [],
    # MP-G instrument mutation IM-1: the r2 NAME ∧ identity sweep (skip bindings not named ``attribute``).
    "IM1": [(GOV, "test_an_ALIASED_binding_of_the_shared_object_MOVES")],
    # IM-2: a NAME-only sweep (patch every module exposing ``attribute``, whatever object it holds).
    "IM2": [
        (GOV, "test_an_ALIASED_binding_of_the_shared_object_MOVES"),
        (GOV, "test_a_private_copy_WEARING_THE_SHARED_NAME_does_NOT_move"),
        (GOV, "test_the_callers_EXPECTATION_is_enforced"),
    ],
    # ---- r3b (items 7-10) ----
    # N4h (adversary-r2): a new owns(agent -> memory) relation, KEYWORD endpoints, enforced=True, plus
    # its KNOWN_RELATION_EDGES row — the resolver-blind build. Under the emitted-DDL resolver it JOINS.
    "N4h": [("test_message_enforcement_63b_ii_a.py", "test_the_derived_population_set_grows_to_memory_message_to")],
    # R1: node leg keyed on ANY governed column (F-TRAP-1). floor_head (scope only) and a lone
    # owner_principal now join.
    "R1": [
        ("test_memory_enforcement_63b_ia.py", "test_a_PARTIAL_trio_never_joins_and_the_FULL_trio_always_does"),
        ("test_memory_enforcement_63b_ia.py", "test_the_population_derivation_reach_is_a_checked_variable"),
        ("test_message_enforcement_63b_ii_a.py", "test_the_derived_population_set_grows_to_memory_message_to"),
    ],
    # R2: relation leg reads only IN.
    "R2": [("test_memory_enforcement_63b_ia.py", "test_the_relation_leg_reads_the_EMITTED_endpoints[out-governed]")],
    # R3: relation parser fails OPEN (continue instead of raise).
    "R3": [("test_memory_enforcement_63b_ia.py", "test_a_relation_statement_whose_endpoints_cannot_be_parsed_FAILS_CLOSED")],
    # GD1 (FORK-B sharing proof): the ONE generator discovery loses generate_lease_ddl — all three
    # consumers (the population corpus's gap pin, coverage_124, principal_keys' union) route through it.
    "GD1": [
        ("test_message_enforcement_63b_ii_a.py", "test_KNOWN_BOUND_the_ALL_DDL_GENERATORS_hand_list_gap"),
        ("test_ddl_write_target_coverage_124.py", "test_the_declared_generator_reach_covers_every_generate_ddl_symbol"),
        ("test_ddl_write_target_coverage_124.py", "test_every_table_constant_value_is_a_declared_table"),
    ],
    # GD2 (FORK-B sharing proof, principal_keys leg): the ONE discovery loses generate_agent_ddl — the
    # principal_keys forward-scope union, coverage_124 and the population corpus must all move.
    "GD2": [
        ("test_principal_keys_schema.py", "test_the_record_principal_link_set_matches_the_cascade_adjudication"),
        ("test_principal_keys_schema.py", "test_the_scanned_corpus_covers_the_standalone_comms_slices"),
        ("test_message_enforcement_63b_ii_a.py", "test_the_derived_population_set_grows_to_memory_message_to"),
        ("test_message_enforcement_63b_ii_a.py", "test_the_generator_corpus_is_DERIVED_by_inspection_and_non_vacuous"),
        ("test_ddl_write_target_coverage_124.py", "test_every_table_constant_value_is_a_declared_table"),
        ("test_ddl_write_target_coverage_124.py", "test_a_planted_undeclared_constant_would_redden_the_invariant"),
    ],
    # N5 (adversary-r2): the fake stamps WRONG scope/owner_agent.
    "N5": [
        ("test_agent_registry.py", "test_the_fake_and_the_real_writer_agree_on_outcome_class_and_stamps[pair-both-set]"),
        ("test_agent_registry.py", "test_the_fake_and_the_real_writer_agree_on_outcome_class_and_stamps[pair-alpha-none]"),
    ],
    # F2a: the fake drops its identity mirror (accepts what the writer refuses).
    "F2a": [
        ("test_agent_registry.py", "test_the_fake_and_the_real_writer_agree_on_outcome_class_and_stamps[hostile-"),
        ("test_agent_registry.py", "test_the_identifier_decision_is_the_SHARED_is_legal_identifier[name-fake]"),
        ("test_agent_registry.py", "test_the_identifier_decision_is_the_SHARED_is_legal_identifier[session-fake]"),
    ],
    # F2b: the fake's blank-role check is a PRIVATE strip() (routing-not-sharing in the fake).
    "F2b": [("test_agent_registry.py", "test_the_blank_role_rule_is_the_SHARED_is_blank[fake]")],
    # R6: the exempt-token SHAPE normaliser widened back to raw text (no ; strip, no = collapse) — the
    # correct-spelling controls red; the wrong-statement controls stay green.
    "R6": [
        ("test_agent_governance_63c_i_a.py", "test_a_correct_statement_passes_in_any_spelling[trailing-semicolon]"),
        ("test_agent_governance_63c_i_a.py", "test_a_correct_statement_passes_in_any_spelling[no-spaces-around-equals]"),
        ("test_agent_governance_63c_i_a.py", "test_a_correct_statement_passes_in_any_spelling[doubled-whitespace-and-spaced-semicolon]"),
    ],
    # IM-3 (DRY sharing proof): the ONE finder ``module_level_bindings_of`` finds NOTHING — BOTH
    # instruments that route through it (patch_shared_object_everywhere + _rebind_everywhere) must fail.
    "IM3": [
        (GOV, "test_an_ALIASED_binding_of_the_shared_object_MOVES"),
        (GOV, "test_a_private_copy_under_ANOTHER_name_does_NOT_move"),
        (GOV, "test_a_private_copy_WEARING_THE_SHARED_NAME_does_NOT_move"),
        (GOV, "test_the_scope_is_formed_by_the_SHARED_keep_scope_formatter"),
        (REG, DECISION),
        (REG, "test_register_charset_check_reads_the_ONE_pattern_in_its_lorerunes_home"),
        (REG, "test_the_blank_role_rule_is_the_SHARED_is_blank"),
        ("test_comms_footer.py", "test_perturbing_the_SHARED_predicate_moves_EVERY_members_refusal"),
        ("test_store_seam_one_derivation.py", "TestSharingProvenByMutation::"),
        ("test_store_seam_one_derivation.py", "test_the_mutation_technique_moves_a_router_and_not_a_private_clone"),
        ("test_ast_reach_helpers.py", "TestSharingProvenByMutation::test_the_rebind_mutation_reaches_a_from_import_binding"),
        ("test_ast_reach_helpers.py", "TestSharingProvenByMutation::test_each_real_fixture_consumer_reddens_when_the_shared_parser_is_dropped"),
    ],
}


def edit(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: anchor occurs {count} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


if "--declared" in sys.argv:
    collected: list[str] = []
    for listing in sorted(SCR.glob("collected_r3*.txt")):  # r3a listings archived before r3b ran
        collected += listing.read_text().splitlines()
    for file_fragment, node_fragment in DECLARED[WB]:
        hits = sorted({node for node in collected if file_fragment in node and node_fragment in node})
        assert hits, f"declared rule ({file_fragment}, {node_fragment}) matched NO collected node"
        for node in hits:
            print(node)
    raise SystemExit(0)

HOME_SHARED = (
    "        from lorerunes import is_legal_identifier  # noqa: PLC0415 - house lazy-import idiom\n\n"
    "        return is_legal_identifier(value)\n"
)
VALIDATE_VIA_HOME = "        if not AppContext._is_comms_charset_legal(value):\n            raise ValueError(\n"
VALIDATE_DIRECT = (
    "        from lorerunes import is_legal_identifier  # noqa: PLC0415\n\n"
    "        if not is_legal_identifier(value):\n            raise ValueError(\n"
)
XOR = (
    "        if (owner_principal_id is None) != (session_keep_id is None):\n"
    "            raise AgentRegistryError(\n"
    '                "register called with an owner but no session keep (or the reverse) — a "\n'
    '                "server-side caller bug; nothing was written"\n'
    "            )\n"
)

if WB == "N1":
    edit(SERVER, VALIDATE_VIA_HOME, VALIDATE_DIRECT)
    edit(SERVER, HOME_SHARED, "        return AGENT_NAME_PATTERN.fullmatch(value) is not None\n")
elif WB == "N1b":
    edit(SERVER, VALIDATE_VIA_HOME, VALIDATE_DIRECT)
    edit(SERVER, HOME_SHARED, "        return AGENT_NAME_PATTERN.match(value) is not None\n")
elif WB == "N1c":
    edit(SERVER, VALIDATE_VIA_HOME, VALIDATE_DIRECT)
    edit(SERVER, HOME_SHARED, '        return re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,63}", value) is not None\n')
elif WB == "N2":
    edit(AGENTS, XOR, "")
    edit(
        AGENTS,
        "        if existing_row is None:\n            # packet 62 W2.3",
        "        if existing_row is None:\n"
        + "\n".join(("    " + line) if line else line for line in XOR.split("\n"))
        + "            # packet 62 W2.3",
    )
elif WB == "N3":
    edit(PRINCIPALS, "', '.join(owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE])", "', '.join(owned_unscoped_ids)")
elif WB == "C3":
    edit(PRINCIPALS, "_REFUSAL_ID_SAMPLE_SIZE = 10\n", "_REFUSAL_ID_SAMPLE_SIZE = 3\n")
elif WB == "LIT10":
    edit(PRINCIPALS, "_REFUSAL_ID_SAMPLE_SIZE = 10\n", "_REFUSAL_ID_SAMPLE_SIZE = 3\n")
    edit(PRINCIPALS, "owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE]", "owned_unscoped_ids[:10]")
elif WB == "N10":
    edit(
        AGENTS,
        "        new_model = model if model is not None else existing.model\n",
        "        if existing_row.get(\"scope\") is None and session_keep_id is not None:\n"
        "            await self._query(\n"
        "                f\"UPDATE type::record('{AGENT_TABLE}', ${_ROW_ID_PARAM}) SET scope = $heal_scope, \"\n"
        "                f\"owner_agent = type::record('{AGENT_TABLE}', ${_ROW_ID_PARAM})\",\n"
        "                {_ROW_ID_PARAM: agent_id, \"heal_scope\": keep_scope(session_keep_id)},\n"
        "            )\n"
        "        new_model = model if model is not None else existing.model\n",
    )
elif WB == "NF2":
    # Move the MOVE (identity + role checks) inside the CREATE branch: first register refuses, a
    # RE-register of an existing (legacy hostile) row skips it.
    text = (ROOT / AGENTS).read_text()
    start = text.index('        for field_name, value in (("name", name), ("session", session)):\n')
    end = text.index("        agent_id = self._agent_id(session, name)\n        existing_row = await self._select_row(agent_id)\n")
    checks = text[start:end]
    edit(AGENTS, checks, "")
    edit(
        AGENTS,
        "        if existing_row is None:\n            # packet 62 W2.3",
        "        if existing_row is None:\n"
        + "".join(("    " + line + "\n") if line else "\n" for line in checks.rstrip("\n").split("\n"))
        + "            # packet 62 W2.3",
    )
elif WB == "ALIAS":
    edit(
        AGENTS,
        "from lorerunes import is_blank, is_legal_identifier, keep_scope, parse_credential\n",
        "from lorerunes import is_blank, is_legal_identifier, parse_credential\n"
        "from lorerunes import keep_scope as _format_keep_scope\n",
    )
    edit(
        AGENTS,
        '"scope": keep_scope(session_keep_id) if session_keep_id is not None else None,\n',
        '"scope": _format_keep_scope(session_keep_id) if session_keep_id is not None else None,\n',
    )
elif WB == "IM1":
    edit(
        GOVC,
        "    for module_name, module, binding_name in module_level_bindings_of(original):\n",
        "    for module_name, module, binding_name in module_level_bindings_of(original):\n"
        "        if binding_name != attribute:\n            continue\n",
    )
elif WB == "IM2":
    edit(
        GOVC,
        "    for module_name, module, binding_name in module_level_bindings_of(original):\n"
        "        patcher.setattr(module, binding_name, replacement, raising=True)\n"
        '        patched.append(f"{module_name}.{binding_name}")\n',
        "    import sys as _sys\n\n"
        "    for module_name, module in list(_sys.modules.items()):\n"
        "        if module is not None and hasattr(module, attribute):\n"
        "            patcher.setattr(module, attribute, replacement, raising=True)\n"
        '            patched.append(f"{module_name}.{attribute}")\n',
    )
elif WB == "IM3":
    edit(
        "loremaster/tests/_logging_fixtures.py",
        "            if value is target:\n                bindings.append((module_name, module, attribute))\n",
        "            if value is target and module_name == '__never__':\n"
        "                bindings.append((module_name, module, attribute))\n",
    )
elif WB == "N4h":
    SCHEMA = "loremaster/loremaster/store/surreal_schema.py"
    edit(SCHEMA, 'BRIEFED_RELATION = "briefed"\n', 'BRIEFED_RELATION = "briefed"\nOWNS_RELATION = "owns"\n')
    edit(
        SCHEMA,
        "    statements: list[str] = [\n"
        "        _define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, enforced=True)\n"
        "    ]\n",
        "    statements: list[str] = [\n"
        "        _define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, enforced=True)\n"
        "    ]\n"
        "    statements.append(\n"
        "        _define_relation_table(OWNS_RELATION, in_table=AGENT_TABLE, out_table=MEMORY_TABLE, enforced=True)\n"
        "    )\n",
    )
    edit(
        "loremaster/tests/_enforced_relations_scaffold.py",
        "    MEMBER_OF_RELATION: (PRINCIPAL_TABLE, KEEP_TABLE),\n}\n",
        '    MEMBER_OF_RELATION: (PRINCIPAL_TABLE, KEEP_TABLE),\n    "owns": (AGENT_TABLE, "memory"),\n}\n',
    )
elif WB == "R1":
    edit(GOVC, "if trio <= columns}", "if trio & columns}")
elif WB == "R2":
    edit(GOVC, "        if (in_tables | out_tables) & nodes\n", "        if in_tables & nodes\n")
elif WB == "R3":
    edit(
        "loremaster/tests/_enforced_relations_scaffold.py",
        "        if in_tables is None or out_tables is None:\n            raise ValueError(\n",
        "        if in_tables is None or out_tables is None:\n            continue\n            raise ValueError(\n",
    )
elif WB == "GD1":
    edit(
        "loremaster/tests/_enforced_relations_scaffold.py",
        '        if name.startswith("generate_") and name.endswith("_ddl")\n    }\n',
        '        if name.startswith("generate_") and name.endswith("_ddl") and name != "generate_lease_ddl"\n    }\n',
    )
elif WB == "GD2":
    edit(
        "loremaster/tests/_enforced_relations_scaffold.py",
        '        if name.startswith("generate_") and name.endswith("_ddl")\n    }\n',
        '        if name.startswith("generate_") and name.endswith("_ddl") and name != "generate_agent_ddl"\n    }\n',
    )
elif WB == "N5":
    edit(FAKES, "            self.db.owner_agents[agent_id] = agent_id\n", "            self.db.owner_agents[agent_id] = 'WRONG'\n")
    edit(
        FAKES,
        "            self.db.scopes[agent_id] = keep_scope(session_keep_id) if session_keep_id is not None else None\n",
        "            self.db.scopes[agent_id] = 'keep:WRONG'\n",
    )
elif WB == "F2a":
    edit(FAKES, "        if identifier_decision is not None:  # None at HEAD only", "        if False:  # None at HEAD only")
elif WB == "F2b":
    edit(FAKES, "        if is_blank(role):\n", "        if not role.strip():\n")
elif WB == "R6":
    edit(
        "loremaster/tests/test_agent_governance_63c_i_a.py",
        '    shaped = shaped.removesuffix(";").rstrip()\n    return re.sub(r"\\s*=\\s*", " = ", shaped)\n',
        "    return shaped\n",
    )
else:
    raise SystemExit(f"unknown {WB}")
print(f"{WB} applied")
```

### `run_lane_r3.sh`
```bash
#!/usr/bin/env bash
# Apply each wrong build on top of the scratch lane's HEAD (r3 reference + r3 tests), run the named
# test files, diff the observed RED set against the DECLARED set (resolved from collect-only BEFORE
# the run) BOTH ways, restore. Usage: run_lane_r3.sh "<test files>" WB...
set -u
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/3bff958a-e5fb-4126-b391-762dd6a032ae/scratchpad
FILES=$1; shift
cd "$S/ref"
echo "[lane] provenance: $(uv run python -c 'import loremaster; print(loremaster.__file__)')"
for WB in "$@"; do
  git checkout -q -f HEAD -- . && git clean -qfd loremaster/loremaster lorerunes/lorerunes
  uv run --no-project python "$S/wbs_r3.py" "$S/ref" "$WB" --declared > "$S/decl_$WB.txt" || { echo "$WB: DECLARE FAILED"; continue; }
  uv run --no-project python "$S/wbs_r3.py" "$S/ref" "$WB" || { echo "$WB: APPLY FAILED"; continue; }
  echo "== $WB landed: $(git diff --shortstat)"
  timeout 1500 uv run pytest -n 8 -q -p no:cacheprovider --tb=line --junitxml="$S/wb_$WB.xml" $FILES > "$S/wb_$WB.log" 2>&1
  echo "== $WB tail: $(tail -n 1 $S/wb_$WB.log)"
  uv run --no-project python - "$WB" <<'PY'
import sys, xml.etree.ElementTree as ET
S="/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/3bff958a-e5fb-4126-b391-762dd6a032ae/scratchpad"
wb=sys.argv[1]
declared=set(open(f"{S}/decl_{wb}.txt").read().split("\n"))-{""}
def nid(tc):
    parts=tc.get("classname").split(".")
    mod_idx=next(i for i,p in enumerate(parts) if p.startswith("test_"))
    path="/".join(parts[:mod_idx+1])+".py"; rest="::".join(parts[mod_idx+1:])
    return f"{path}::{rest}::{tc.get('name')}" if rest else f"{path}::{tc.get('name')}"
root=ET.parse(f"{S}/wb_{wb}.xml").getroot()
observed={nid(tc) for tc in root.iter("testcase") if tc.find("failure") is not None or tc.find("error") is not None}
unexpected=sorted(observed-declared); still_green=sorted(declared-observed)
if not declared:
    verdict = "SURVIVES as DECLARED (0 red)" if not observed else "DECLARED-SURVIVOR WENT RED"
else:
    verdict = "PROOF HELD — declared RED set fired EXACTLY" if not unexpected and not still_green else "PROOF FAILED (set differs from declaration)"
print(f"== {wb} VERDICT: {verdict}; observed={len(observed)} declared={len(declared)}")
for n in unexpected: print(f"   UNEXPECTED-RED {n}")
for n in still_green: print(f"   DECLARED-STILL-GREEN {n}")
PY
done
git checkout -q -f HEAD -- . && git clean -qfd loremaster/loremaster lorerunes/lorerunes
echo "[lane] restored: $(git status --porcelain loremaster lorerunes | wc -l) dirty paths"
```

### `classify.py`
```python
"""Classify every red in a junit XML by its failure message shape (r3 RED receipt instrument)."""
import collections, re, sys, xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
buckets = collections.defaultdict(list)
RULES = [
    ("missing-seam: session_keep_id kwarg", r"unexpected keyword argument 'session_keep_id'"),
    ("missing-seam: lorerunes symbol", r"module 'lorerunes' has no attribute"),
    ("missing-seam: principals._REFUSAL_ID_SAMPLE_SIZE", r"_REFUSAL_ID_SAMPLE_SIZE"),
    ("behavioural: store ASSERT still lands (RED-at-HEAD right reason)", r"RED-at-HEAD \(right reason\)|assert violation"),
    ("behavioural: AST second decider (server.py .fullmatch)", r"may be read ONLY for its prose"),
    ("behavioural: fake/real parity mismatch (real side unbuilt: MOVE/stamps)", r"does NOT mirror the writer"),
    ("behavioural: identity-sweep did not move (consumer has no shared decision at HEAD)", r"did not move under the MODULE-LEVEL identity sweep"),
    ("behavioural: governed column/stamp unbuilt (owner_agent/scope NONE)", r"owner_agent|scope must be|NO row may carry a NONE scope|did not mint the canonical project keep|SELECT \* before"),
    ("behavioural: owner-keyed backfill statement at HEAD", r"scope-keyed UPDATE|backfill must be ONE"),
    ("behavioural: population five-set (agent/briefed unbuilt)", r"adjudicated known set"),
    ("behavioural: tokenless spy sees no session_keep_id", r"TOKENLESS register must pass session_keep_id"),
    ("behavioural: householded joiner scope unbuilt", r"householded JOINER"),
    ("behavioural: W1-1 governed column/index absent from the agent emitter", r"W1-1|REWRITE|shared emitter|governed column"),
]
for tc in root.iter("testcase"):
    node = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
    if node is None:
        continue
    text = (node.get("message") or "") + "\n" + (node.text or "")
    nid = f"{tc.get('classname')}::{tc.get('name')}"
    for label, pattern in RULES:
        if re.search(pattern, text):
            buckets[label].append(nid)
            break
    else:
        first = (node.get("message") or "").splitlines()[0][:160] if node.get("message") else "?"
        buckets[f"UNCLASSIFIED: {first}"].append(nid)
for label, nodes in sorted(buckets.items()):
    print(f"{len(nodes):4d}  {label}")
    if label.startswith("UNCLASSIFIED") or "--all" in sys.argv:
        for n in nodes:
            print(f"        {n}")
```

### `diffred.py`
```python
"""Diff two junit XMLs: tests red in NEW not red in BASE (and whether they existed in base), and vice versa."""
import sys, xml.etree.ElementTree as ET
def load(p):
    root=ET.parse(p).getroot(); red=set(); allids=set()
    for tc in root.iter("testcase"):
        nid=f"{tc.get('classname').split('.')[-2] if tc.get('classname').count('.')>=3 else ''}{'::' if tc.get('classname').count('.')>=3 else ''}{tc.get('classname').split('.')[-1]}::{tc.get('name')}"
        nid=f"{tc.get('classname')}::{tc.get('name')}"
        allids.add(nid)
        if tc.find("failure") is not None or tc.find("error") is not None: red.add(nid)
    return red, allids
br, ba = load(sys.argv[1]); nr, na = load(sys.argv[2])
print("NEW-RED (red now, not red in base):")
for n in sorted(nr-br): print(("   [new test] " if n not in ba else "   [WAS GREEN] ")+n)
print("NO-LONGER-RED (red in base, not red now):")
for n in sorted(br-nr): print(("   [test gone] " if n not in na else "   [now green] ")+n)
```

### fold mutation texts (`scripts/mutation_proof.py --anchor-file/--replacement-file`)
`sn_config_anchor.txt`:
```
from lorerunes import is_blank
```
`sn_config_repl.txt`:
```
def is_blank(value: str) -> bool:  # WRONG BUILD: a PRIVATE copy WEARING the shared name
    return not value or not value.strip()
```
`sn_txn_anchor.txt`:
```
from lorerunes import reclassify
```
`sn_txn_repl.txt`:
```
from lorerunes import reclassify as _shared_reclassify


def reclassify(*args, _frozen=_shared_reclassify, **kwargs):  # WRONG BUILD: frozen private copy, shared NAME
    return _frozen(*args, **kwargs)


del _shared_reclassify
```

### `builder_guard_deletion.py` (the reference's model of the builder's ONE granted test-tree edit, amendment-5 FORK-C)
```python
"""contract-63c-i-a-r3 — the ONE test-tree edit amendment-5 FORK-C grants the 63c-i-a BUILDER (REFACTOR
step): delete the fake's HEAD-RED ``except ImportError`` guard. Applied to the reference lane AFTER the r3
tests are synced, so the reference models the builder's full output. Exactly-once anchor (#194).

Usage: uv run --no-project python builder_guard_deletion.py <scratch-root>"""

import sys
from pathlib import Path

path = Path(sys.argv[1]) / "loremaster/tests/_comms_fakes.py"
text = path.read_text()
old = (
    "        try:\n"
    "            from lorerunes import is_legal_identifier  # noqa: PLC0415 - call-time read (mutation-visible)\n"
    "        except ImportError:  # HEAD-RED accommodation — delete once the build lands the predicate\n"
    "            return None\n"
    "        return is_legal_identifier\n"
)
new = (
    "        from lorerunes import is_legal_identifier  # noqa: PLC0415 - call-time read (mutation-visible)\n\n"
    "        return is_legal_identifier\n"
)
assert text.count(old) == 1, f"guard anchor occurs {text.count(old)} times"
path.write_text(text.replace(old, new))
print("builder's granted guard deletion applied")
```

### amendment-5 mutation texts
`guard_anchor.txt` → `guard_repl.txt` (GUARD) and `dim_anchor.txt` → `dim_repl.txt` (DIM):
```
        from lorerunes import is_legal_identifier  # noqa: PLC0415 - call-time read (mutation-visible)

        return is_legal_identifier
---
        try:
            from lorerunes import is_legal_identifier  # noqa: PLC0415 - call-time read (mutation-visible)
        except ImportError:  # HEAD-RED accommodation — delete once the build lands the predicate
            return None
        return is_legal_identifier
---
        if parameter.name == "dim":
            kwargs["dim"] = dim
            continue
        if parameter.default is not inspect.Parameter.empty:
            continue
---
        if parameter.default is not inspect.Parameter.empty:
            continue
        if parameter.name == "dim":
            kwargs["dim"] = dim
            continue
```

## Progress log — close-out
- 2026-09-24 18:58: amendment-5 (`26511f0`) landed; riders applied; GUARD + DIM mutations PROOF HELD; final HEAD RED `146 failed, 2406 passed, 3 errors` (unchanged red set); SAT full suite `11405 passed / 0 failed`; r3b committed.
