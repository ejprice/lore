# REPORT-contract-63c-i-a-a19a — contract addendum a19a for 63c-i-a (amendments 20 R1/R2, 21 CD-1/CD-2, 22 §W 1–6)

brief-base v16 read · brief project v7 read

## SUMMARY BLOCK
- **state:** done. 63 new pins (`loremaster/tests/test_fixwave_a19a_63c_i_a.py`) + 3 in-place edits with DUAL (a19 D-1 CONTROL re-key, R-Q5-1 R1, ii-a message golden). Base HEAD `6659ed8`, production = `84af63f`. **RED at `84af63f`: 80 failed** = 52 new (each on its defect, 0 TypeError/Import/Attribute) + a19's 28 still-open; 11 new pins GREEN there by design (§6). **SAT: reference build, full suite ALONE `-n 12`, lint-clean → `11592 passed, 62 skipped, 3 xfailed … EXIT=0`, 0 failed (§7).** **23 mutation proofs HELD** (M01–M23, declared = observed both ways); P1c reach: 4 HELD + 1 FAILED-as-declared (an under-declaration: 4 extra on-defect reds, §3).
- **deviations:** (1) FK-1/FK-2 escalated and RULED mid-run (amendment 23 `e3abc7c`, directive #17016 acked). (2) SAT run #1 exposed a contract defect of mine — the handler's `preflight` hit `FakeAgentRegistry` without one (86 reds) — fixed in the TEST tree: `FakeAgentRegistry.preflight` (+ ONE extracted conflict helper), the recorder's surface, a new mirror pin (§9 D-2). (3) A double-collection near-miss (D-1). (4) The ii-a message golden was dead data — a live leg added (D-3). (5) P1c-e declared set incomplete (§3).
- **Packages considered:** none — no mechanism specified for production (the pins reuse `sanitise_line`, `store_handle`, `observe_governed_table_writes`, `emitted_schema_ddl`, `_normalise_statement`, `scripts/mutation_proof.py`; the reference build is scratch-only).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** every new reusable test-local symbol dispositioned in §8 (REUSED: `_renderings`, the F5 seeders, `emitted_schema_ddl`, `store_handle`, the real-registry harness; EXTENDED: `FakeAgentRegistry`; the rest HAND-ROLLED with the search that found nothing fitting). Fixture data (`_REFUSAL_FIXTURES`, `_PREFLIGHT_CASES`, the per-case setups) is not listed.
- **Graded:** n/a — I authored a contract; I graded no one's artifact (base `6659ed8`; production byte-identical to `84af63f`).
- **decisions-needed:** none blocking. 9 candidate doors outside the ruled items (§10) — notably a message-table half-pair (owned-but-unscoped message) that CD-1's WHERE never stamps yet counts forever (reasoned, not probed), and compensation masking.
- **Builder contract created by D-2:** the handler calls `preflight` BY NAME on the wired registry with keywords `session`, `role`, `spawned_by`, `owner_principal_id` (no `session_keep_id` before the mint); `get_or_create_keyed` is called BY NAME (the K3 spy + its CONTROL require it); the dangling-sender check lives in `principals._agent_migration_preconditions` (the redirect pins require it).
- **receipt pointers:** §F forks + rulings · §1 required-green · §2 per-item table · §3 P1c reach · §4 mutation proofs · §5 DUAL · §6 RED@`84af63f` · §7 SAT · §8 DRY · §9 deviations · §10 candidate doors · §11 gates · §A instruments verbatim (reference patcher, mutation + P1c drivers, ghost probe).

## §0 Capability check (brief-base §4)
- Idle-gate contract written, NOT denied: `/tmp/claude-idle-gate-lore/297217bd-cb03-409c-ac95-0eb7ca9bf74b-contract-63c-i-a-a19a.contract`
  = `{"artifact": "REPORT-contract-63c-i-a-a19a.md"}` (the lead's session id, the one the other 63c agents' files carry).
- lore reachable: `lore_comms register` OK (session `63c-20260924`, role `contract`, cadence `≤20m`); `lore_index()` at
  2026-09-26T02:00Z: root `/workspace`, branch `feat/surreal-unification`, ref `97b2db6` = HEAD, last_sync 34 s.
- grep/rg are hook-blocked (#473): textual sweeps use `awk` over `git ls-files` (said so; cases (b)/(c)).
- Store reference `docs/reference/surrealdb-31-capabilities.md` read FIRST, in full (§1.4 legacy-row seeding, §2
  `SELECT *` omits NONE, §4/§6.4 dangling record links, §7).

## §F FORKS (brief-base §2 / brief ESCALATION) — written BEFORE the pins that depend on them

### FK-1 (BLOCKING item 2 / #485 pin) — amendment 22 §1's ∀-refusal-classes coverage clause is unsatisfiable as written
The ruling: *"the set of refusal classes is derived … every concrete subclass of `AgentRegistryError` defined in
`agents.py` (plus the base for the teaching refusals) … for each derived class there is a driven fixture through
`AppContext.comms(action="register")` … a class with no fixture reds the pin with the class's name."*
Measured at HEAD `97b2db6` (AST over `AgentRegistry`, script in §A):
- `agents.py` defines SIX concrete subclasses: `UnknownAgentError`, `AmbiguousAgentError`, `InvalidAgentIdentityError`,
  `AgentIdentityConflictError`, `RetiredAgentError`, `IllegalAgentStatusError`.
- `register` + the helpers it calls raise ONLY: `AgentRegistryError` (the A3 pair guard, and two post-write
  "vanished" checks), `InvalidAgentIdentityError`, `RetiredAgentError`, `AgentIdentityConflictError` (×2: role,
  spawned_by). `UnknownAgentError`/`AmbiguousAgentError` are raised only by `_resolve_row`; `IllegalAgentStatusError`
  only by `_validate_status_edge` — neither is in register's call tree. **No comms-register fixture can raise
  them, so the pin as written is permanently RED on every correct build.**
- The base's teaching refusal (A3's mixed provenance pair) is **unreachable through `comms(register)` by construction**:
  `_comms_register` derives `owner_principal_id` and `session_keep_id` together (both set iff a principal resolved).
- Reading A (recommended): the derived set = { c ∈ (AgentRegistryError-subclasses defined in `agents.py`) ∪ {base} :
  c is RAISED somewhere in the AST call closure of `AgentRegistry.register` } — derived at test time from production
  truth, coverage a checked variable BOTH ways (a class register newly raises reds by NAME; a stale fixture reds too).
  The base is covered by a registry-level fixture for the A3 pair (raised before any store I/O — the existing
  amendment-4 MP-B pins), because comms cannot produce a mixed pair; its comms-unreachability is a STATED BOUND in
  the pin with a re-open trigger ("the handler derives the pair from anything other than one principal").
- Reading B: the literal clause (all six subclasses + base through comms) — unsatisfiable; would need the ruling to
  name what "driven" means for classes register cannot raise.
- **I proceed on Reading A's shape for the non-base classes (it is the literal clause restricted to what is
  drivable) and hold the base's disposition open until ruled.**

### FK-2 (BLOCKING one pin of item 4 / F-2) — the post-migrate invariant "∀ stamped messages, owner_principal IS NOT NONE" is FALSE on a correct F-2 build for a GHOST sender
Amendment 22 §3 derives the invariant as a CONSEQUENCE of refusing ownerless-scoped senders (*"the message leg can
never meet an ownerless-scoped sender, so it never stamps a NONE owner"*). That is derived over ONE source of a NONE
`sender.owner_principal`. A legacy message whose `sender` record link names NO agent row (store-ref §2/§4: record
links are not existence-checked) is a second source. **Probed at HEAD `97b2db6` (production = `84af63f`), 2026-09-26,
verbatim** (instrument pasted in §A):
```
GHOST first=MigrateGovernedResult(table='message', scanned=2, backfilled=2, already_migrated=0, refused=False, reason=None)
GHOST rows=[{'id': RecordID(table_name=message, record_id='m_ghost'), 'owner_agent': RecordID(table_name=agent, record_id='ghost_agent'), 'owner_principal': None, 'scope': 'keep:01M3DQEFMP59XY05JZ43DGGGV8'}, {'id': RecordID(table_name=message, record_id='m_ok'), 'owner_agent': RecordID(table_name=agent, record_id='governed_sender'), 'owner_principal': RecordID(table_name=principal, record_id='3g99cpxslqpvqtck1lq3'), 'scope': 'keep:01M3DQEFMP59XY05JZ43DGGGV8'}]
GHOST second=MigrateGovernedResult(table='message', scanned=2, backfilled=1, already_migrated=1, refused=False, reason=None)
```
(every agent migrated; the ghost-sender message is stamped `owner_principal` NONE + the project scope; the owner-keyed
WHERE re-stamps it on run 2 — CD-1's scope-keyed WHERE ends the re-stamp but not the NONE owner.)
- Reading A (recommended): pin the invariant ∀ populations REACHABLE under the ruled mechanism (legacy, fully
  migrated, the half-pair populations — all refused or stamped non-NONE), and SURFACE the ghost sender as a candidate
  door with this probe as its receipt (the operator decides refuse / skip / out of scope). The pin's docstring names
  the ghost-sender bound and its re-open trigger.
- Reading B: pin the invariant ∀ inputs including a ghost sender — requires an UNRULED production behaviour (refuse
  the message leg on a dangling sender? skip and report?), so the contract would invent a design.
- **Until ruled, the invariant pin is written on Reading A's populations (satisfiable either way); the ghost-sender
  leg is NOT written.**

### FK-3 (non-blocking; pick stated) — amendment 22 §2 (F-1) names "the production constant the five-set resolver pin already cross-checks (nodes only)" as the governed set; no such production constant exists, and the derived node set EXCLUDES `brief`
- The five-set pin (`test_message_enforcement_63b_ii_a.py::TestTheGovernedPopulationSetGrows::test_the_derived_population_set_grows_to_memory_message_to`)
  cross-checks the TEST helper `_governed_contract.governed_populations()` (derived from emitted DDL) against a
  test-local known set {agent, briefed, memory, message, to}; nodes only = {agent, memory, message}. `brief` does not
  carry the governed trio at i-a (it lands 63c-ii), so it is NOT in the derived node set.
- The same paragraph says `brief` IS valid (*"on a multi-principal store `--table brief` still meets the §2.1 refusal
  … the four `∀[brief]` pins are right and stand"*). The behavioural clause and the pointer disagree.
- **Pick (behaviour wins, the pointer is a factual slip):** valid = {agent, memory, message, brief} (D-1's explicit
  list, the a19 `_MIGRATE_TABLES`). Reading B (derived nodes) would RED the four `∀[brief]` pins F-1 says stand, so it
  is self-refuting within the ruling. The CD-2 pin probes invalid names DERIVED from the emitted schema's table set
  minus the valid four (so `briefed`, `to`, `keep`, `task`, … each get the zero-read "not supported"), plus a typo.

### FK-4 (non-blocking; pick stated) — PD2-as-pin (MP-4) and F-2 interact: PD2's population is now refused at the verb
PD2's population (1 legacy + 2 ownerless-SCOPED agents) is exactly F-2's forbidden half-pair state, so on a correct
a19a build it meets the verb-level "half-applied" refusal and the order guard never runs. Under F-2 the order guard
can ONLY see agents that are (NONE,NONE) or (set,set), where the NONE-scope and NONE-owner counts are equal — so
MP-4's noun/count lie is **unreachable by construction** after F-2 (no store, redirect or population can present the
guard with disagreeing predicates without also tripping the verb-level refusal).
- **Pick:** PD2 lands as ruled (its population, its assertion that no served count stands under a noun naming a
  different set) — it now asserts the half-applied diagnosis; the report states that MP-4's wrong build is
  dissolved by F-2, not killed by PD2, with the re-open trigger "the verb-level precondition is narrowed (E3) so a
  half-pair can reach the order guard".

### Rulings received (2026-09-26): amendment 23 (`e3abc7c`) — FK-1 Reading A (pre-write raise closure of `register`, both-ways coverage, two stated exclusions), FK-2 RULED (a dangling sender REFUSES the message leg: count + bounded ids, byte-inert, "dangling sender"; the invariant then holds ∀ incl. ghost), FK-3/FK-4 confirmed. Every pin below is written on those readings. Lore directive #17016 acked.

## §1 Required-green enumeration (checked BEFORE each pin was written; re-checked by the reference build)
1. **Single-principal stores proceed on every governed `--table` exactly as before.** New verb-level conditions key on
   HALF-PAIRS only (owned-unscoped — a19's — and ownerless-scoped — F-2), never on "unscoped" or "ownerless" alone;
   an AST scan of every `seed_agent_governed(owner_principal=None, scope=<set>)` call in the test tree found exactly ONE
   such population (the a19 D-1 CONTROL), which F-2 itself re-keys (§5 DUAL). The dangling-sender refusal fires only on
   legacy messages whose sender row does not exist — no existing fixture seeds one (every ii-a/63a message fixture has a
   real sender). Re-proven: reference build, 6 contract files `539 passed` (§6) + full suite (§7).
2. **Memory-only stores (no `agent` table):** the reference reads `INFO FOR DB` once and gates BOTH the agent reads and the
   new message dangling read on the tables actually defined (a19 builder note carried; the store error is not swallowed).
3. **The existing 63c-i-a contract incl. both helper shapes, the generated legs, the effect leg** — unchanged except the
   three DUAL rows in §5; `_MIGRATE_MESSAGE_GOLDEN` changes and its F5 effect predicate `_effect_migrate_message` is
   untouched (it reads the effect, not the statement).
4. **Amendment 13/14 refusal-count rules:** R-Q5-1's integer-truth leg is untouched; R1 narrows only the principal-sample
   leg. The R2/half-applied/dangling refusals state only counts their fixtures seed (count assertions are membership of
   the TRUE count, never a phrase regex).
5. **a19's pins as amended:** the four `∀[brief]` pins stand (FK-3); a19's D-1 CONTROL is re-keyed (F-2 erratum).
6. **The reference's widened citation-strip in R-Q5-1** (a19 author's note) is the committed test code; unchanged.

## §2 Per-item table (file `loremaster/tests/test_fixwave_a19a_63c_i_a.py` unless named; class names abbreviated `…63cIAa19a`)
| § / item | pin (file::test) | wrong build killed (mutation id, §4) |
|---|---|---|
| am-22 §W1 MP-1 (K1) | `TestSharingMovesInBothDirections::test_K1_the_verb_does_not_refuse_when_the_shared_function_says_clean[agent\|memory\|message\|brief]` — reverse redirect + twin BASELINE + call counter | WB1 private verb copy ORed beside the shared answer (M01) |
| am-22 §W1 MP-2 (K2) | `…::test_K2_the_order_guard_refuses_when_the_shared_function_says_unmigrated` | WB2 retired owner count ANDed into the guard (M02) |
| am-22 §W1 MP-3 (K3) | `TestEveryRegisterRefusalPrecedesTheKeepMint::test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[×6]` — zero-mint spy per class | WB3 mint-then-undo (M03) |
| am-22 §W1 MP-4 (PD2) | `TestNoServedCountStandsUnderAForeignNoun::test_PD2_the_served_count_describes_the_set_its_noun_names` | F-2 absent (M20). MP-4's noun lie itself is DISSOLVED by F-2, not killed (FK-4, am-23) |
| am-22 §W1 MP-5 | `TestTheIdentityRefusalsHaveAGoldenSkeleton::test_the_registry_refusal_skeleton_is_the_golden[name\|session]`, `::test_the_server_refusal_skeleton_is_the_golden` | WB4 gloss in a later clause, registry (M14) + server (M15) |
| am-22 §W2 #485 derived ∀ | `TestEveryRegisterRefusalPrecedesTheKeepMint::test_every_derived_refusal_class_has_a_driven_fixture` (AST raise closure of `register`, pre-write, both-ways coverage, A3 exclusion checked for staleness) | P1c probes a/b/e (§3) |
| am-22 §W2 #485 driven | `…::test_a_refused_credentialed_register_…[InvalidAgentIdentityError-blank-{empty,spaces,ideographic} \| AgentIdentityConflictError-{role,spawned-by}-conflict \| RetiredAgentError-retired]` — 0 mints, keep+household inert, served == registry's own teaching, next principal keeps the session; `…::test_CONTROL_a_valid_register_mints_exactly_one_keep` | PQ1 #485 construction (M04), WB3 (M03) |
| am-22 §W2 ONE method | `…::test_register_itself_decides_with_preflight_in_BOTH_directions`, `…::test_the_handler_decides_with_preflight_BEFORE_the_mint` (forward refuse / reverse admit / order preflight→mint→register) | register private copy (M07), handler private copy (M08), WB3 (M03), PQ1 (M04) |
| am-22 §W2 race compensation | `…::test_the_RACE_compensation_deletes_only_a_keep_this_call_created[created-by-this-call\|found-pre-existing]` | no compensation (M05), delete-a-FOUND-keep (M06) |
| am-21 CD-2 / am-22 F-1 / am-23 FK-3 | `TestTableValidityIsCheckedFirst::test_an_invalid_table_is_answered_not_supported_with_zero_store_io` (27 schema-derived names + typo; 0 acquires on handle/principal/keep stores; CONTROL sees reads) | validity after the precondition (M13); brief answered "not supported" (M12, kills via a19's four `∀[brief]` pins + K1/half/R2 `[brief]`) |
| am-22 §W4 F-2 half-pairs | `TestHalfPairsAreRefusedAtTheVerb::test_an_ownerless_SCOPED_agent_refuses_every_table_as_half_applied[×4]`, `::test_BOTH_half_pairs_together_are_refused_byte_inert[×4]` | F-2 absent (M20) |
| am-22 §W4 F-2 + am-23 FK-2 invariant | `TestNoStampedMessageCarriesANoneOwner::test_after_agent_then_message_no_stamped_message_has_a_NONE_owner[legacy\|fully-migrated\|half-pair-ownerless-scoped\|half-pair-owned-unscoped\|dangling-sender]` (+ exact stamped count per population — never vacuous) | message leg stamps NONE (M10), F-2 absent (M20) |
| am-23 FK-2 ghost refusal | `TestADanglingSenderRefusesTheMessageLeg::test_a_dangling_sender_refuses_the_message_leg_byte_inert[one-ghost\|two-ghosts\|above-cap]`, `::test_a_hostile_dangling_id_cannot_forge_a_line`, `::test_the_dangling_sender_refuses_the_MESSAGE_leg_only[agent\|memory]`, `::test_the_dangling_decision_is_THE_shared_functions_in_BOTH_directions[×2]` | no refusal (M10), private dangling query (M11) |
| am-22 §W4 D-1 control re-key | `test_fixwave_a19_63c_i_a.py::TestTheMessageOrderGuardIsScopeKeyed63cIAa19::test_CONTROL_a_FULLY_migrated_store_does_not_trip_the_order_guard` (DUAL) | control (GREEN at `84af63f`) |
| am-22 §W5 F-3 | `TestRefusalReceiptsServeOnlyWhatWasMeasured::test_the_multi_principal_refusal_serves_no_unmeasured_count[×4]` + the same leg inside the half-applied, R2 and invalid-table pins | zero-receipt refusal (M09) |
| am-21 CD-1 | `TestTheMessageBackfillIsScopeKeyed::test_a_scoped_but_ownerless_message_is_never_restamped_and_counts_as_migrated`, `::test_the_message_backfill_EXECUTES_the_golden` (new live leg: the golden was dead data), `::test_EVERY_governed_legs_backfill_WHERE_is_scope_keyed` (legs AST-derived, coverage checked); golden edit in `test_message_enforcement_63b_ii_a.py::_MIGRATE_MESSAGE_GOLDEN` (DUAL) | owner-keyed WHERE (M17), not self-guarding (M18), owner-keyed counts (M19) |
| am-20 R1 | `test_agent_governance_63c_i_a.py::TestAgentMigrateScopeKeyed63cIA::_assert_the_derived_diagnosis` — exactly `min(bound, distinct)` (DUAL), exercised by R-Q5-1 `[above-cap]`/`[perturbed-bound]` | WB7b (M16) |
| am-20 R2 | `TestAnUnresolvableOperatorAndOwnedUnscopedRowsAreBothNamed::test_the_refusal_names_both_operator_first_owners_unclassified[×4]` | operator part dropped (M21), owners classified "other" (M22) |
| am-22 §W2 (test double, D-2) | `TestTheFakePreflightMirrorsTheWriter::test_the_fake_and_the_real_preflight_agree[×9]` (outcome class + write-free + ABSOLUTE real expectation); `test_comms_tool.py::TestTheStoreTouchRecorder` (existing derived reach pin, `preflight` recorded) | fake preflight admits existing-row conflicts (M23) |

## §5 DUAL — every pin deleted, inverted or re-keyed (each carries an in-place DUAL comment)
| pin | change | virtue kept | virtue dropped (reason) |
|---|---|---|---|
| `test_fixwave_a19_63c_i_a.py::…::test_CONTROL_an_ownerless_SCOPED_agent_does_not_trip_the_order_guard` → `test_CONTROL_a_FULLY_migrated_store_does_not_trip_the_order_guard` | RE-KEYED (am-22 §3 erratum): population = two FULLY migrated agents (operator + foreign owner), a legacy message each; asserts proceed + `backfilled == 2` | the order guard does not fire once migrated; governed senders' messages are backfilled | the owner-vs-scope discrimination in THIS direction — unreachable after F-2 (FK-4); the ownerless-scoped population is now pinned as a verb-level half-applied refusal (`TestHalfPairsAreRefusedAtTheVerb…`) and by PD2. The other direction stays pinned by CA-A |
| `test_agent_governance_63c_i_a.py::TestAgentMigrateScopeKeyed63cIA::_assert_the_derived_diagnosis` (above-bound leg) | RE-KEYED (am-20 R1): `1 <= named <= bound` → `named == min(bound, distinct foreign owners)` | never more than the bound; never none | "any sample 1..bound" — it admitted WB7b (a private shape-dependent sample) |
| `test_message_enforcement_63b_ii_a.py::_MIGRATE_MESSAGE_GOLDEN` | CHANGED (am-21 CD-1): `WHERE owner_principal IS NONE` → `WHERE scope IS NONE AND owner_principal IS NONE` | one UPDATE, the same three SET columns, NONE-owner rows only | the owner-keyed "unmigrated" meaning (the ruling retires it) |
| `test_fixwave_a19_63c_i_a.py::_MIGRATE_TABLES` comment | NOTE only (no behaviour): the 4-tuple is now the ruled VALID set (FK-3); invalid names are derived elsewhere | — | — |
| `_comms_fakes.py::FakeAgentRegistry.register` (a test DOUBLE, not a pin) | REFACTORED: the retired / role / spawned_by refusals moved into `_refuse_an_existing_row_conflict`, called inside the CAS | every refusal, its message and its position (inside the `await`-free compare-and-set) — removed-behaviour inventory: none | — |
| `test_comms_tool.py::_RecordingAgentRegistry.RECORDED_METHODS` | ADDITIVE: `preflight` + an override | the recorder still equals the fake's public surface | — |
No pin was deleted or inverted.

## §8 DRY ledger (new reusable symbols — all test-local, `test_fixwave_a19a_63c_i_a.py`)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_renderings` | (read a19's file) | `TestTheRefusalRendersStoredIdsThroughTheSanitiser63cIAa19._renderings` — identical | **REUSED** (my first draft had a verbatim copy; replaced by a reference to a19's before the SAT run) |
| `_ClosureWalk` / `_register_raise_sites` / `_comms_required_classes` | `lore_search("AST walk collecting raise statements of exception classes reachable from a function call closure")` | only my own new file; a memory about the comms promise-instrument's deny-by-default AST scanner (different job) | HAND-ROLLED — no existing raise-closure derivation; bounds stated in its docstring |
| `_migrate_legs` (AST: functions opening `governed_exempt("migrate-governed", …)`) | read `_governed_contract.function_calls_named` | answers "does function F call G" for a NAMED F — cannot enumerate the Fs | HAND-ROLLED (enumeration, not a membership check) |
| `_count_connection_acquires` | `lore_search("test helper that counts _ensure_connection calls on a store to prove zero store I/O")` | no code hit (docs noise) | HAND-ROLLED; `_governed_contract.store_handle`'s acquire counter is REUSED for the migrate handle itself |
| `_spy_the_mint` | (a19 file / adversary §A.4 K3 read) | K3 inline in the adversary's probe file (scratch-only, never committed) | HAND-ROLLED as the one home for K3's spy + the race injection |
| `_stated_integers` | read `TestAgentMigrateScopeKeyed63cIA._integers_stated_beside_the_seeded_identifiers` | strips the FULL COUNT (the very integer my pins look FOR) and needs `before` rows | HAND-ROLLED trimmed variant (identifiers + `§` only); the difference is the stripped count |
| `_keep_snapshot` (keep + member_of) | a19's `_keep_snapshot` read | a19's includes `agent`, which the race injection legitimately writes | HAND-ROLLED (2 lines; table set differs deliberately) |
| `_seed_half_applied_store`, `_seed_migrated_senders`, `_seed_ghost_store`, `_seed_invariant_population` | — | the F5 home's seeders | REUSED (compose `seed_agent_governed`/`seed_agent_legacy`/`seed_memory_legacy`/`seed_message_legacy` only; no raw CREATE) |
| `_comms_fakes.FakeAgentRegistry.preflight` + `_refuse_an_existing_row_conflict` | read `_comms_fakes.FakeAgentRegistry` | the fake's own register-path refusals (inline, inside the CAS) | **EXTENDED** `FakeAgentRegistry`: ONE static conflict helper now called by both `preflight` and `register` (no second copy of the decision) |
| `_preflight_outcome` (mirror harness) | read `test_agent_registry.py::TestTheFakeRegistryMirrorsTheWriter63cIA` | a REGISTER-only harness (`_real_outcome`/`_fake_outcome`) | HAND-ROLLED for `preflight`; **REUSES** `TestQ3RegisterValidatesIdentityBeforeStoreIO63cIA._real_registry` / `_agent_row_count` |
| `_assert_no_unmeasured_count`, `_scan_counts`, `_skeleton`, `_invalid_table_names`, `_require_preflight` | — | — | HAND-ROLLED single-purpose assertions; `_invalid_table_names` REUSES `_enforced_relations_scaffold.emitted_schema_ddl` (the ONE emitted-schema corpus) |

## §3 P1c REACH proof — the derived ∀-refusal-classes pin (probes on the reference; driver verbatim §A.3; declared sets written in the driver BEFORE the run; agents.py restored byte-exact, md5 `5f7d3d3b9a9cb64d814b5f59f84153d6`)
| probe | declared RED | verdict (2026-09-26) |
|---|---|---|
| P1c-a: a NEW subclass `DummyRefusalError(AgentRegistryError)` defined in `agents.py` and raised PRE-write in `preflight` | the coverage pin, naming `DummyRefusalError` | **PROOF HELD** — `1 failed, 543 passed`; the failure names the class |
| P1c-b: an EXISTING never-raised class (`UnknownAgentError`) newly raised pre-write | the coverage pin, naming `UnknownAgentError` | **PROOF HELD** — `1 failed, 543 passed` |
| P1c-c: a new subclass DEFINED but not raised | none | **PROOF HELD** — `544 passed` (am-23: reach = the raise closure, not the module class list) |
| P1c-d: a new subclass raised only POST-write (after the CREATE) | none | **PROOF HELD** — `544 passed` (exclusion 1) |
| P1c-e: the A3 pair guard removed from `preflight` | the coverage pin (STALE exclusion) + the 4 amendment-4 MP-B pair pins | **PROOF FAILED as declared** — the mutation landed, the coverage pin reddened naming STALE and all 4 declared pair pins reddened, but 4 MORE pre-existing pins also reddened on the same defect: `test_agent_registry.py::TestTheFakeRegistryMirrorsTheWriter63cIA::test_the_fake_and_the_real_writer_agree_on_outcome_class_and_stamps[pair-owner-only\|pair-keep-only]` and `…::test_the_fake_and_the_real_writer_agree_on_the_RE_REGISTER_door[consistent-then-owner-only\|consistent-then-keep-only]`. My declaration was INCOMPLETE (I did not know those fake-mirror pins guard A3 too); every red is on-defect. Not re-declared after seeing the output (#194 discipline) — recorded as the honest result. |
Counts are 544 because this run preceded the double-collection fix (§9 D-1): 5 a19 tests were collected twice. The verdict logic is count-independent (node-id sets).

## §4 Mutation proofs — every new kill-pin against its wrong build (scripts/mutation_proof.py on the reference; each = reference + ONE defect; declared sets written in the driver BEFORE the run from `pytest --collect-only -q`; driver verbatim §A.2; contract files: the 6 files of §6)
Provenance: every run in the `scratch_copy.sh` tree; `loremaster.__file__` = `…/scratchpad/ref/loremaster/loremaster/__init__.py`. Production restored after each (mutation_proof content restore); post-run md5s re-verified before SAT (`principals 86f08339…`, `agents 5f7d3d3b…`, `server c9afb9f8…`, `keeps 230ee086…`, `governed 1a186212…`).
| id | wrong build | declared RED (n) | verdict |
|---|---|---|---|
| M01-WB1-verb-private-copy | see §A.2 | 4 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M02-WB2-order-guard-ANDs-owner-count | see §A.2 | 1 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M03-WB3-mint-then-undo | see §A.2 | 7 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M04-PQ1-485-blank-only-handler | see §A.2 | 4 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M05-no-compensation | see §A.2 | 1 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M06-compensation-deletes-a-FOUND-keep | see §A.2 | 1 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M07-register-private-copy | see §A.2 | 2 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M08-handler-private-copy | see §A.2 | 1 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M09-zero-receipt-refusal | see §A.2 | 12 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M10-message-leg-stamps-NONE-owner | see §A.2 | 7 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M11-private-dangling-check | see §A.2 | 2 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M12-CD2-brief-not-supported | see §A.2 | 7 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M13-validity-after-precondition | see §A.2 | 1 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M14-WB4-registry-gloss-later-clause | see §A.2 | 2 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M15-WB4-server-gloss-later-clause | see §A.2 | 1 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M16-WB7b-names-one-principal-above-bound | see §A.2 | 2 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M17-CD1-owner-keyed-WHERE | see §A.2 | 3 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M18-CD1-not-self-guarding | see §A.2 | 1 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M19-CD1-owner-keyed-counts | see §A.2 | 1 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M20-F2-half-pair-not-refused | see §A.2 | 6 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M21-R2-operator-part-dropped | see §A.2 | 4 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M22-R2-owners-classified-as-other | see §A.2 | 4 | **PROOF HELD** (rc 0, declared = observed both ways) |
| M23-fake-preflight-admits-existing-row-conflicts (`loremaster/tests/_comms_fakes.py`, run scope: this file + `test_comms_tool.py`) | fake `preflight` skips `_refuse_an_existing_row_conflict` | 3 (`TestTheFakePreflightMirrorsTheWriter63cIAa19a::…[role-conflict\|spawned-by-conflict\|retired]`) | **PROOF HELD** (rc 0; `_comms_fakes.py` restored byte-exact, md5 `d1b80030…`) |

Note on the test bytes each proof graded: M01–M22 ran on the a19a test file as it stood before two
behaviour-neutral edits (`_renderings` became a module-qualified reference to a19's identical staticmethod;
the fake-preflight mirror class was appended). P1c ran with the `_renderings` alias in its intermediate,
double-collected form (§9 D-1). Every assertion M01–M22/P1c exercised is byte-identical in the committed file.
No survivor claim is made (every declared wrong build was killed in its targeted run), so no full-suite
survivor leg is owed.

## §9 Deviations, near-misses and in-scope test-tree changes (all inside the writable set)
- **D-1 (near-miss, self-caught by a count):** importing a19's `Test…` class into the new module made pytest COLLECT
  its 5 tests a second time (539 → 544 in P1c's tail). Fixed by module-qualified imports
  (`import test_fixwave_a19_63c_i_a as a19`, `import test_agent_registry`) — no `Test*` class is bound in the new
  module. Collection is now 63 for the new file.
- **D-2 (SAT run #1 caught a contract defect — mine):** the ruled handler calls `preflight` through whatever
  registry the context wires, and 86 comms tests wire `_comms_fakes.FakeAgentRegistry` (+ its subclass
  `test_comms_tool.py::_RecordingAgentRegistry`), which had no `preflight` — `AttributeError` on a CORRECT
  build, and the builder may not edit tests. Fix (test tree): `FakeAgentRegistry.preflight` (mirrors the writer:
  identity/blank/pair-once-minted, then the existing-row refusals) with the retired/conflict decision extracted
  into ONE static `_refuse_an_existing_row_conflict` that `register`'s compare-and-set also calls (sync — the
  CAS stays `await`-free; messages byte-identical; no behaviour removed). The recorder's derived reach pin
  (`TestTheStoreTouchRecorder`) then reddened BY DESIGN — `preflight` joined `RECORDED_METHODS` with an override.
  NEW mirror pin `TestTheFakePreflightMirrorsTheWriter63cIAa19a` (9 cases, outcome class + write-free + ABSOLUTE
  expectation on the real side); M23 proves it.
  **Builder contract this creates:** the handler must call `preflight` by that NAME on the wired registry, with
  keyword arguments `session`, `role`, `spawned_by`, `owner_principal_id` (and NOT `session_keep_id` before the
  mint); the fake accepts exactly the ruled parameter names (am-22 §1).
- **D-3:** the ii-a message golden was dead data (no live comparison) — a live leg was added
  (`test_the_message_backfill_EXECUTES_the_golden`) rather than trusting the edit (receipt: the golden edit reddened
  nothing at `84af63f`, measured 2026-09-26).
- **D-4:** the brief's "prove the reach with a dummy subclass → RED naming it" is honoured as P1c-a; amendment 23
  (received mid-run) makes a DEFINED-but-never-raised subclass correctly NOT red (P1c-c) — both recorded.
- Mutation evidence note (P1c-e): recorded as PROOF FAILED-as-declared (§3) — an under-declaration, not a
  mutation that failed to land.

## §10 Candidate doors (noticed, OUTSIDE the ruled items — surfaced, NOT pinned; the operator owns scope)
1. **Both half-pairs in one store** — refused (pinned), but which diagnoses the ONE refusal carries is unruled (am-20
   §8.4's consumer-law logic — "a refusal that names one of two problems buys two round trips" — would say both).
2. **Owned-but-unscoped MESSAGE rows** (owner set, scope NONE — a message-table half-pair): CD-1's self-guarding
   WHERE never stamps them, but the scope-keyed "unmigrated" count includes them, so `backfilled` would over-report
   and the leg would never converge. REASONED from the ruled shapes, NOT probed (confidence MEDIUM). Unruled.
3. **Leg-level refusals still serve `scanned=0`/`already_migrated=0`** (ORDER guard, operator ambiguity at
   `84af63f`); F-3 is ruled for VERB-level refusals only. My reference serves `None` on the dangling-sender refusal;
   no pin requires either.
4. **Compensation masking:** if the race compensation's `delete_keep` itself raises (e.g. `KeepNotFoundError` under a
   concurrent delete), the caller sees a keep error instead of the registry's teaching. The ruled bound names only
   "a keep left behind".
5. **R2's stored-id render** has no hostile fixture of its own (CA-1's hostile fixture exercises the
   operator-RESOLVED path; the R2 path renders the same ids through the same seam in my reference only).
6. **Test-module re-collection hazard** (D-1): binding a `Test*` class from another test module re-runs its tests
   silently. A repo-local hygiene invariant would close the class.
7. **Dead allowlist goldens** (D-3): an allowlist `statement` no live test compares to the executed token. A ∀ pin
   over every `TreeWriteAllowlistEntry` with an `exempt_name` would close the class.
8. **Dangling-link detection shape:** `SELECT id FROM message WHERE scope IS NONE AND record::exists(sender) = false`
   detected every seeded ghost on 3.2.4 (my reference; 0 false positives over the six contract files). It is not in
   `docs/reference/surrealdb-31-capabilities.md`; am-23 asks the builder to confirm the shape — a probe row there would
   make it citable.
9. **Tool friction:** `scripts/mutation_proof.py` requires ≥1 `--expect-red`, so a DECLARED-EMPTY proof (a mutation
   that must redden NOTHING — P1c-c/d) needs a hand driver (§A.3).

## §6 RED at `84af63f` (main tree; production = `84af63f` — `git diff --stat 84af63f HEAD -- loremaster/loremaster lorerunes/lorerunes loresigil lorescribe` is EMPTY; tests = the committed bytes; 2026-09-26)
Command: `uv run pytest -n 8 -q -p no:randomly --tb=line` over the 6 contract files + `test_comms_tool.py` +
`test_comms_render_architecture.py` → **`80 failed, 1418 passed in 89.07s`**. **0 TypeError / AttributeError /
ImportError / NameError** (awk over the log). Distribution:
- **52 of the 63 new pins RED, each on its defect**: `preflight does not exist` (`pytest.fail` naming am-22 §1) ×11
  (mirror ×9, register-both-directions, handler order); #485 "reached get_or_create_keyed" ×6; the shared function
  missing (`pytest.fail` in a19's redirect helper) for K1/K2/ghost-sharing; K1 twin BASELINES for memory/message/
  brief (the a19 defect: those tables are not refused at `84af63f`); half-applied ×4 (agent/memory PROCEED, message
  serves the ORDER teaching, brief "not supported"); BOTH-half-pairs[memory]; F-3 ×4 (`scanned=13/…`, memory
  proceeds, `0`s); R2 ×4 (operator refusal ALONE); dangling ×3 PROCEEDED + hostile unnamed + invariant
  `[dangling-sender]` stamped NONE; invariant `[half-pair-owned-unscoped]` stamped 1 (CA-A); CD-1 ×3 (scoped row
  re-stamped; golden; ∀-WHERE); invalid-table F-3 leg (`answers_to … scanned=0`); MP-5 ×3; PD2 (ORDER teaching,
  not half-applied); race[created] (keep left behind).
- **11 new pins GREEN at `84af63f`, by design:** the derivation instrument (`test_every_derived_refusal_class_…` — the
  classes are the same; `preflight` moves them), `CONTROL_a_valid_register_mints_exactly_one_keep`,
  `race[found-pre-existing]` (the created-only control), `the_dangling_sender_refuses_the_MESSAGE_leg_only[agent\|memory]`,
  `BOTH_half_pairs…[agent\|message\|brief]` (refused at `84af63f` by other paths), invariant `[legacy\|fully-migrated\|
  half-pair-ownerless-scoped]` (84af63f's owner-keyed guard refuses the last).
- **a19's still-open pins: 28** (its 29 minus the re-keyed CONTROL, now a GREEN control by design): 20 in
  `test_fixwave_a19_63c_i_a.py`, R-Q5-1 ×6 + exempt-token golden in `test_agent_governance_63c_i_a.py`,
  `is_blank[handler]` in `test_agent_registry.py`.
- `test_comms_tool.py` / `test_comms_render_architecture.py`: all GREEN at `84af63f` — the fake's `preflight` +
  refactor and the recorder change are behaviour-neutral where `preflight` is not called.

## §7 SAT receipt — the contract is satisfiable by a known-correct build
- Reference = a19's reference diff (REPORT-contract-63c-i-a-a19.md §A.1, applied verbatim) + my a19a patcher (§A.1),
  in `./scripts/scratch_copy.sh …/scratchpad/ref` (provenance asserted by the tool for all four members; printed
  `loremaster.__file__` = `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/a73d6805-d1cb-4680-96c7-3e1e3442d135/scratchpad/ref/loremaster/loremaster/__init__.py`).
  Lint cleanups FIRST: `ruff check .` → `All checks passed!`; `./scripts/typecheck.sh` → rc 0. Production md5s:
  principals `86f0833920a5…`, agents `5f7d3d3b9a9c…`, server `c9afb9f8ff47…`, keeps `230ee0867d5f…`, governed
  `1a1862122b6f…`. Tests = the main tree's committed bytes (`cmp` identical, all 6 changed/new test files).
- **Run #1 (2026-09-26, alone, `-n 12`, 63 GB avail, spike-surreal active): `86 failed, 11497 passed` — a CONTRACT
  defect (D-2: the fake had no `preflight`), fixed in the test tree, not a build defect.**
- **Run #2 (same reference production bytes, final tests), alone, `-n 12`, MemAvailable 62 GB, no other pytest,
  spike-surreal active, PID watchdog at 15 GB / 10 s (never fired):**
  ```
  11592 passed, 62 skipped, 3 xfailed, 9 warnings in 488.74s (0:08:08)
  EXIT=0
  ```
  **0 failed.** Count check: a19's SAT `11529` + 63 new tests = `11592`. #486 did not appear in either run.
- Builder notes carried into the reference (brief): the `INFO FOR DB` gate (the memory table still migrates on a store
  with NO `agent` table — no store error swallowed) now also gates the message dangling read; R-Q5-1's widened
  citation-strip is unchanged test code.

## §11 Gate receipts — main tree, committed bytes (2026-09-26)
- `uv run ruff check .` → `All checks passed!`
- `./scripts/typecheck.sh` → rc 0 (`typecheck: scripts OK`, `shellcheck OK`, every leg OK)
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` → `typecheck GREEN`, `ruff GREEN`,
  `pytest NOT_RUN` (excluded by `--legs`, #466 — the full suite ran on the reference, §7). **No
  `scripts/pending_contracts.yaml` entry** — nothing new reddens typecheck (not-yet-existing symbols are reached through
  `getattr`/`vars` or a typed-`Any` receipt).

## §A Instruments (verbatim — the scratch trees are disposable by design; every measured claim above is re-runnable from these)

### §A.1 Reference patcher `a19a_ref_patch.py` (applied AFTER `git apply` of the a19 author's reference diff, REPORT-contract-63c-i-a-a19.md §A.1, in a `scratch_copy.sh` tree of `84af63f` production; then `ruff check --fix` and one line re-wrap in `agents.py` — the `keep_id = cast(...)` split)
```python
"""contract-63c-i-a-a19a — reference fix build for the a19a addendum, applied ON TOP of the a19 author's
reference diff (REPORT-contract-63c-i-a-a19.md §A.1) in a scratch_copy.sh tree of 84af63f production.
Each replacement asserts it landed exactly once (#194). Usage: python a19a_ref_patch.py <scratch-root>"""

import pathlib
import sys

ROOT = pathlib.Path(sys.argv[1])


def patch(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: expected exactly one match, found {count}: {old[:90]!r}"
    path.write_text(text.replace(old, new))


P = "loremaster/loremaster/principals.py"
G = "loremaster/loremaster/governed.py"
A = "loremaster/loremaster/agents.py"
S = "loremaster/loremaster/server.py"
K = "loremaster/loremaster/keeps.py"

# ---- F-3: receipts may be None ("not measured") -------------------------------------------------
patch(G, "    scanned: int\n    backfilled: int\n    already_migrated: int\n",
      "    scanned: int | None\n    backfilled: int\n    already_migrated: int | None\n")

# ---- the verb: validity FIRST (CD-2/F-1), then the store preconditions (both half-pairs, R2) -----
patch(P, """    preconditions = await _agent_migration_preconditions(store)
    if preconditions.owned_unscoped:
        operator = await resolve_operator_principal(principal_store)
        return MigrateGovernedResult(
            table=table,
            scanned=0,
            backfilled=0,
            already_migrated=0,
            refused=True,
            reason=_multi_principal_refusal_reason(preconditions, operator),
        )
    if table == MEMORY_TABLE:""", """    if table not in _GOVERNED_MIGRATE_TABLES:
        return MigrateGovernedResult(
            table=table,
            scanned=None,
            backfilled=0,
            already_migrated=None,
            refused=True,
            reason=(
                f"migrate-governed does not support table {table!r} — only `memory`, `agent` and "
                "`message` migrate (brief lands 63c-ii, task/finding land 64)"
            ),
        )
    preconditions = await _agent_migration_preconditions(store)
    if preconditions.owned_unscoped or preconditions.ownerless_scoped:
        operator = await resolve_operator_principal(principal_store)
        roster = await principal_store.list() if operator is None else []
        admins = sum(1 for principal in roster if principal.role == _ROLE_ADMIN)
        return MigrateGovernedResult(
            table=table,
            scanned=None,
            backfilled=0,
            already_migrated=None,
            refused=True,
            reason=_multi_principal_refusal_reason(
                preconditions, operator, principal_count=len(roster), admin_count=admins
            ),
        )
    if table == MEMORY_TABLE:""")
patch(P, """    return MigrateGovernedResult(
        table=table,
        scanned=0,
        backfilled=0,
        already_migrated=0,
        refused=True,
        reason=(
            f"migrate-governed does not support table {table!r} at packet 63b — only `memory`, "
            "`agent` and `message` (brief lands 63c, task/finding land 64)"
        ),
    )
""", """    return MigrateGovernedResult(
        table=table,
        scanned=None,
        backfilled=0,
        already_migrated=None,
        refused=True,
        reason=(
            f"migrate-governed does not support table {table!r} at packet 63c-i — only `memory`, "
            "`agent` and `message` (brief lands 63c-ii, task/finding land 64)"
        ),
    )
""")
patch(P, "_REFUSAL_ID_SAMPLE_SIZE = 10\n", """_REFUSAL_ID_SAMPLE_SIZE = 10
#: The governed tables ``--table`` may name (amendment 22 F-1 / amendment 23 FK-3).
_GOVERNED_MIGRATE_TABLES = frozenset({"agent", "memory", "message", "brief"})
""")

# ---- the shared preconditions: + ownerless-scoped half-pairs, + dangling message senders -------
patch(P, """    unscoped_count: int
    owned_unscoped: list[tuple[Any, Any]]
""", """    unscoped_count: int
    owned_unscoped: list[tuple[Any, Any]]
    ownerless_scoped: list[Any] = []
    dangling_messages: list[Any] = []
""")
patch(P, """    tables = info.get("tables", {}) if isinstance(info, dict) else {}
    if AGENT_TABLE not in tables:
        return AgentMigrationPreconditions(unscoped_count=0, owned_unscoped=[])""", """    tables = info.get("tables", {}) if isinstance(info, dict) else {}
    dangling: list[Any] = []
    if MESSAGE_TABLE in tables:
        dangling_rows = await run_query(
            acquire=store.acquire,
            drop=store.drop,
            url=store.url,
            noun="governed message dangling-sender probe",
            label="governed.message_dangling.rejected",
            statement=(
                f"SELECT id FROM {MESSAGE_TABLE} WHERE scope IS NONE AND record::exists(sender) = false"
            ),
            params={},
            logger=logger,
        )
        dangling = sorted((row["id"] for row in (dangling_rows or [])), key=str)
    if AGENT_TABLE not in tables:
        return AgentMigrationPreconditions(
            unscoped_count=0, owned_unscoped=[], dangling_messages=dangling
        )""")
patch(P, """    owned = [(row["id"], row["owner_principal"]) for row in (rows or [])]
    owned.sort(key=lambda pair: str(pair[0]))
    return AgentMigrationPreconditions(unscoped_count=unscoped_count, owned_unscoped=owned)""",
"""    owned = [(row["id"], row["owner_principal"]) for row in (rows or [])]
    owned.sort(key=lambda pair: str(pair[0]))
    half_rows = await run_query(
        acquire=store.acquire,
        drop=store.drop,
        url=store.url,
        noun="governed agent half-pair precondition",
        label="governed.agent_half_pair.rejected",
        statement=f"SELECT VALUE id FROM {AGENT_TABLE} WHERE scope IS NOT NONE AND owner_principal IS NONE",
        params={},
        logger=logger,
    )
    return AgentMigrationPreconditions(
        unscoped_count=unscoped_count,
        owned_unscoped=owned,
        ownerless_scoped=sorted(half_rows or [], key=str),
        dangling_messages=dangling,
    )""")

# ---- the refusal text: F-1 derived + R2 (both, operator first, unclassified) + F-2 half-applied --
patch(P, """def _multi_principal_refusal_reason(
    preconditions: AgentMigrationPreconditions, operator: Principal | None
) -> str:""", """def _multi_principal_refusal_reason(
    preconditions: AgentMigrationPreconditions,
    operator: Principal | None,
    *,
    principal_count: int = 0,
    admin_count: int = 0,
) -> str:""")
patch(P, """    operator_bare = None if operator is None else (operator.id.partition(":")[2] or operator.id)
    offending_count = len(preconditions.owned_unscoped)
    operator_owned = [pair for pair in preconditions.owned_unscoped if str(pair[1].id) == operator_bare]
    foreign = [pair for pair in preconditions.owned_unscoped if str(pair[1].id) != operator_bare]
    parts = [f"{offending_count} agent row(s) carry an owner but no scope."]
    if operator_owned:""", """    parts: list[str] = []
    offending_count = len(preconditions.owned_unscoped)
    if offending_count and operator is None:
        parts.append(
            f"cannot resolve THE operator principal ({principal_count} principals, {admin_count} admins) "
            "— provision a single operator principal (or a single admin) first; until it resolves, the "
            "owners below are unclassified (any of them may be the operator)."
        )
    operator_bare = None if operator is None else (operator.id.partition(":")[2] or operator.id)
    classify = operator is not None
    operator_owned = [pair for pair in preconditions.owned_unscoped if str(pair[1].id) == operator_bare]
    foreign = [pair for pair in preconditions.owned_unscoped if str(pair[1].id) != operator_bare]
    if offending_count:
        parts.append(f"{offending_count} agent row(s) carry an owner but no scope.")
    if classify and operator_owned:""")
patch(P, """    if foreign:
        owners = sorted({sanitise_line(str(owner)) for _row_id, owner in foreign})""",
"""    if classify and foreign:
        owners = sorted({sanitise_line(str(owner)) for _row_id, owner in foreign})""")
patch(P, """    shown_ids = [sanitise_line(str(row_id)) for row_id, _owner in preconditions.owned_unscoped][
        :_REFUSAL_ID_SAMPLE_SIZE
    ]
    parts.append(
        f"First {len(shown_ids)} of {offending_count} ids shown: {', '.join(shown_ids)}. "
        "Adjudicate these rows by hand before migrating; no row was stamped"
    )
    return " ".join(parts)""", """    if offending_count:
        shown_ids = [sanitise_line(str(row_id)) for row_id, _owner in preconditions.owned_unscoped][
            :_REFUSAL_ID_SAMPLE_SIZE
        ]
        parts.append(f"First {len(shown_ids)} of {offending_count} ids shown: {', '.join(shown_ids)}.")
    half = preconditions.ownerless_scoped
    if half:
        shown_half = [sanitise_line(str(row_id)) for row_id in half[:_REFUSAL_ID_SAMPLE_SIZE]]
        parts.append(
            f"{len(half)} agent row(s) carry a scope but no owner — a half-applied store (one of the "
            f"owner/scope pair was written without the other). First {len(shown_half)} of {len(half)} "
            f"ids shown: {', '.join(shown_half)}."
        )
    parts.append("Adjudicate these rows by hand before migrating; no row was stamped")
    return " ".join(parts)""")

# ---- the message leg: scope-keyed counts, dangling-sender refusal, CD-1 WHERE -------------------
patch(P, """    unmigrated_agents = (await _agent_migration_preconditions(store)).unscoped_count
    if unmigrated_agents > 0:""", """    preconditions = await _agent_migration_preconditions(store)
    unmigrated_agents = preconditions.unscoped_count
    if unmigrated_agents > 0:""")
patch(P, """    operator = await resolve_operator_principal(principal_store)
    if operator is None:
        principals = await principal_store.list()
        admins = [principal for principal in principals if principal.role == _ROLE_ADMIN]
        return MigrateGovernedResult(
            table=MESSAGE_TABLE,""", """    dangling = preconditions.dangling_messages
    if dangling:
        shown = [sanitise_line(str(row_id)) for row_id in dangling[:_REFUSAL_ID_SAMPLE_SIZE]]
        return MigrateGovernedResult(
            table=MESSAGE_TABLE,
            scanned=None,
            backfilled=0,
            already_migrated=None,
            refused=True,
            reason=(
                f"{len(dangling)} legacy message(s) name a dangling sender — no agent row exists for the "
                f"sender, so no owner can be read from it. First {len(shown)} of {len(dangling)} ids "
                f"shown: {', '.join(shown)}. Adjudicate these messages by hand before migrating `message`; "
                "no row was stamped"
            ),
        )
    operator = await resolve_operator_principal(principal_store)
    if operator is None:
        principals = await principal_store.list()
        admins = [principal for principal in principals if principal.role == _ROLE_ADMIN]
        return MigrateGovernedResult(
            table=MESSAGE_TABLE,""")
patch(P, """    unmigrated = await _owner_count(store, MESSAGE_TABLE, none=True)
    already = await _owner_count(store, MESSAGE_TABLE, none=False)""",
"""    unmigrated = await _scope_count(store, MESSAGE_TABLE, none=True)
    already = await _scope_count(store, MESSAGE_TABLE, none=False)""")
patch(P, """"owner_principal = sender.owner_principal, scope = $scope WHERE owner_principal IS NONE\"""",
      """"owner_principal = sender.owner_principal, scope = $scope "
        "WHERE scope IS NONE AND owner_principal IS NONE\"""")

# ---- keeps: get_or_create_keyed reports created-vs-found on request -------------------------------
patch(K, "from typing import Any\n", "from typing import Any, Literal, overload\n")
patch(K, """    async def get_or_create_keyed(
        self, key: str, *, type: str, keeper_email: str, name: str | None = None  # noqa: A002
    ) -> Keep:""", """    @overload
    async def get_or_create_keyed(
        self,
        key: str,
        *,
        type: str,  # noqa: A002
        keeper_email: str,
        name: str | None = None,
        report_created: Literal[False] = False,
    ) -> Keep: ...

    @overload
    async def get_or_create_keyed(
        self,
        key: str,
        *,
        type: str,  # noqa: A002
        keeper_email: str,
        name: str | None = None,
        report_created: Literal[True],
    ) -> tuple[Keep, bool]: ...

    async def get_or_create_keyed(
        self,
        key: str,
        *,
        type: str,  # noqa: A002
        keeper_email: str,
        name: str | None = None,
        report_created: bool = False,
    ) -> Keep | tuple[Keep, bool]:""")
patch(K, """            existing = await self.get_by_key(key)
            if existing is not None:
                return existing
            keeper_id = await self._resolve_principal_id(keeper_email)""", """            existing = await self.get_by_key(key)
            if existing is not None:
                return (existing, False) if report_created else existing
            keeper_id = await self._resolve_principal_id(keeper_email)""")
patch(K, """                winner = await self.get_by_key(key)
                if winner is not None:
                    return winner
                raise""", """                winner = await self.get_by_key(key)
                if winner is not None:
                    return (winner, False) if report_created else winner
                raise""")
patch(K, """                raise KeepStoreError(f"created keyed keep {keep_id!r} did not read back")
            return created""", """                raise KeepStoreError(f"created keyed keep {keep_id!r} did not read back")
            return (created, True) if report_created else created""")

# ---- agents: preflight — the ONE write-free refusal method register calls first ----------------
patch(A, """    async def register(
        self,
        name: str,
        *,
        session: str,
        role: str,""", """    async def preflight(
        self,
        name: str,
        *,
        session: str,
        role: str,
        spawned_by: str | None = None,
        owner_principal_id: str | None = None,
        session_keep_id: str | None | object = _KEEP_NOT_YET_MINTED,
    ) -> dict[str, Any] | None:
        \"\"\"Every refusal ``register`` can raise WITHOUT a write (amendment 22 §1, #485); returns the
        existing row (or ``None``). The pair check runs only once the keep id is known.\"\"\"
        if session_keep_id is not _KEEP_NOT_YET_MINTED:
            self._refuse_an_inconsistent_provenance_pair(owner_principal_id, cast("str | None", session_keep_id))
        self._refuse_an_invalid_identity(name=name, session=session, role=role)
        existing_row = await self._select_row(self._agent_id(session, name))
        if existing_row is None:
            return None
        existing = self._row_to_agent(existing_row)
        if existing.status == STATUS_RETIRED:
            raise RetiredAgentError(
                f"agent {name!r} is retired (terminal) — respawns register a fresh name"
            )
        if existing.role != role:
            raise AgentIdentityConflictError(
                f"agent {name!r} is already registered with role {render_attributed(existing.role)} "
                f"(you sent {render_attributed(role)}) — names are never reused; register a fresh name "
                f"(e.g. {name + '2'!r})"
            )
        if (
            spawned_by is not None
            and existing.spawned_by is not None
            and existing.spawned_by != spawned_by
        ):
            raise AgentIdentityConflictError(
                f"agent {name!r} is already registered with spawned_by "
                f"{render_attributed(existing.spawned_by)} (you sent "
                f"{render_attributed(spawned_by)}) — names are never "
                f"reused; register a fresh name (e.g. {name + '2'!r})"
            )
        return existing_row

    async def register(
        self,
        name: str,
        *,
        session: str,
        role: str,""")
patch(A, """        self._refuse_an_inconsistent_provenance_pair(owner_principal_id, session_keep_id)
        self._refuse_an_invalid_identity(name=name, session=session, role=role)
        agent_id = self._agent_id(session, name)
        existing_row = await self._select_row(agent_id)
        now = datetime.now(UTC)""", """        existing_row = await self.preflight(
            name,
            session=session,
            role=role,
            spawned_by=spawned_by,
            owner_principal_id=owner_principal_id,
            session_keep_id=session_keep_id,
        )
        agent_id = self._agent_id(session, name)
        now = datetime.now(UTC)""")
patch(A, """        existing = self._row_to_agent(existing_row)
        if existing.status == STATUS_RETIRED:
            raise RetiredAgentError(
                f"agent {name!r} is retired (terminal) — respawns register a fresh name"
            )
        if existing.role != role:
            raise AgentIdentityConflictError(
                f"agent {name!r} is already registered with role {render_attributed(existing.role)} "
                f"(you sent {render_attributed(role)}) — names are never reused; register a fresh name "
                f"(e.g. {name + '2'!r})"
            )
        if (
            spawned_by is not None
            and existing.spawned_by is not None
            and existing.spawned_by != spawned_by
        ):
            raise AgentIdentityConflictError(
                f"agent {name!r} is already registered with spawned_by "
                f"{render_attributed(existing.spawned_by)} (you sent "
                f"{render_attributed(spawned_by)}) — names are never "
                f"reused; register a fresh name (e.g. {name + '2'!r})"
            )

        new_model""", """        existing = self._row_to_agent(existing_row)

        new_model""")
patch(A, "class AgentRegistryError(RuntimeError):", """#: ``preflight``'s "the session keep is not minted yet" marker — the handler preflights BEFORE the mint.
_KEEP_NOT_YET_MINTED: object = object()


class AgentRegistryError(RuntimeError):""")

# ---- server: preflight BEFORE the mint; created-only compensation for the race -----------------
patch(S, """        # amendment 19 D-2: refuse a BLANK role BEFORE the session-keep mint (#97 — a rejected
        # register has no side effect), through the registry's own refusal over lorerunes.is_blank.
        from loremaster.agents import AgentRegistry  # noqa: PLC0415 - house lazy-import idiom

        AgentRegistry._refuse_an_invalid_identity(name=agent, session=session, role=role)  # noqa: SLF001
        if principal is not None:""", """        # amendment 22 §1 (#485): EVERY write-free registry refusal BEFORE the session-keep mint.
        await self.agent_registry.preflight(
            agent,
            session=session,
            role=role,
            spawned_by=spawned_by,
            owner_principal_id=None if principal is None else str(principal.id).split(":", 1)[-1],
        )
        keep_created = False
        if principal is not None:""")
patch(S, """            session_keep = await keep_store.get_or_create_keyed(
                key=f"session:{session}", type="session", keeper_email=principal.email, name=session
            )""", """            session_keep, keep_created = await keep_store.get_or_create_keyed(
                key=f"session:{session}",
                type="session",
                keeper_email=principal.email,
                name=session,
                report_created=True,
            )""")
patch(S, """        result = await self.agent_registry.register(
            agent,
            session=session,
            role=role,
            model=model,
            spawned_by=spawned_by,
            task_id=task_id,
            cadence=cadence,
            owner_principal_id=principal_bare,
            session_keep_id=session_keep_bare,
        )""", """        from loremaster.agents import AgentRegistryError  # noqa: PLC0415 - house lazy-import idiom

        try:
            result = await self.agent_registry.register(
                agent,
                session=session,
                role=role,
                model=model,
                spawned_by=spawned_by,
                task_id=task_id,
                cadence=cadence,
                owner_principal_id=principal_bare,
                session_keep_id=session_keep_bare,
            )
        except AgentRegistryError:
            # The race bound (amendment 22 §1.2): a conflicting register landed between preflight and
            # register. Delete the session keep ONLY if this call CREATED it.
            if keep_created and session_keep_bare is not None and self._keep_store is not None:
                await self._keep_store.delete_keep(keep_id=session_keep_bare)
            raise""")
print("patched")
```

### §A.2 Mutation driver `mut_driver.py` (M01–M22; declared sets are IN the file, written before the run) — M23 command line follows
```python
"""contract-63c-i-a-a19a — mutation-proof driver. Every wrong build = the a19a REFERENCE (scratch `ref/`) + ONE
defect, applied by scripts/mutation_proof.py (exactly-once anchor, content restore, declared RED set diffed BOTH
ways). DECLARED SETS WERE WRITTEN IN THIS FILE BEFORE ANY RUN (ids from `pytest --collect-only -q`).
usage: python mut_driver.py <ref-root> <log-dir> [M-id ...]"""

import pathlib
import subprocess
import sys

REF = pathlib.Path(sys.argv[1])
LOGS = pathlib.Path(sys.argv[2])
ONLY = set(sys.argv[3:])
LOGS.mkdir(parents=True, exist_ok=True)

P, S, A = "loremaster/loremaster/principals.py", "loremaster/loremaster/server.py", "loremaster/loremaster/agents.py"
N = "loremaster/tests/test_fixwave_a19a_63c_i_a.py::"
A19 = "loremaster/tests/test_fixwave_a19_63c_i_a.py::"
GOV = "loremaster/tests/test_agent_governance_63c_i_a.py::"
FILES = [
    "loremaster/tests/test_fixwave_a19a_63c_i_a.py",
    "loremaster/tests/test_fixwave_a19_63c_i_a.py",
    "loremaster/tests/test_agent_governance_63c_i_a.py",
    "loremaster/tests/test_message_enforcement_63b_ii_a.py",
    "loremaster/tests/test_agent_registry.py",
    "loremaster/tests/test_message_migrate_63b_ii_a.py",
]
TABLES = ("agent", "memory", "message", "brief")
K1 = [f"{N}TestSharingMovesInBothDirections63cIAa19a::test_K1_the_verb_does_not_refuse_when_the_shared_function_says_clean[{t}]" for t in TABLES]
K2 = [f"{N}TestSharingMovesInBothDirections63cIAa19a::test_K2_the_order_guard_refuses_when_the_shared_function_says_unmigrated"]
PD2 = f"{N}TestNoServedCountStandsUnderAForeignNoun63cIAa19a::test_PD2_the_served_count_describes_the_set_its_noun_names"
REG = f"{N}TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::"
DRIVEN = {
    v: f"{REG}test_a_refused_credentialed_register_mints_no_keep_and_denies_no_third_party[{v}]"
    for v in (
        "InvalidAgentIdentityError-blank-empty", "InvalidAgentIdentityError-blank-spaces",
        "InvalidAgentIdentityError-blank-ideographic", "AgentIdentityConflictError-role-conflict",
        "AgentIdentityConflictError-spawned-by-conflict", "RetiredAgentError-retired",
    )
}
HANDLER = f"{REG}test_the_handler_decides_with_preflight_BEFORE_the_mint"
REGISTER_BOTH = f"{REG}test_register_itself_decides_with_preflight_in_BOTH_directions"
RACE_CREATED = f"{REG}test_the_RACE_compensation_deletes_only_a_keep_this_call_created[created-by-this-call]"
RACE_FOUND = f"{REG}test_the_RACE_compensation_deletes_only_a_keep_this_call_created[found-pre-existing]"
INVALID = f"{N}TestTableValidityIsCheckedFirst63cIAa19a::test_an_invalid_table_is_answered_not_supported_with_zero_store_io"
HALF = [f"{N}TestHalfPairsAreRefusedAtTheVerb63cIAa19a::test_an_ownerless_SCOPED_agent_refuses_every_table_as_half_applied[{t}]" for t in TABLES]
F3 = [f"{N}TestRefusalReceiptsServeOnlyWhatWasMeasured63cIAa19a::test_the_multi_principal_refusal_serves_no_unmeasured_count[{t}]" for t in TABLES]
R2 = [f"{N}TestAnUnresolvableOperatorAndOwnedUnscopedRowsAreBothNamed63cIAa19a::test_the_refusal_names_both_operator_first_owners_unclassified[{t}]" for t in TABLES]
GH = f"{N}TestADanglingSenderRefusesTheMessageLeg63cIAa19a::"
DANGLING = [f"{GH}test_a_dangling_sender_refuses_the_message_leg_byte_inert[{p}]" for p in ("one-ghost", "two-ghosts", "above-cap")]
HOSTILE_GHOST = f"{GH}test_a_hostile_dangling_id_cannot_forge_a_line"
GHOST_SHARING = [f"{GH}test_the_dangling_decision_is_THE_shared_functions_in_BOTH_directions[{d}]" for d in ("shared-says-dangling", "shared-says-sound")]
INV = f"{N}TestNoStampedMessageCarriesANoneOwner63cIAa19a::test_after_agent_then_message_no_stamped_message_has_a_NONE_owner"
CD1 = f"{N}TestTheMessageBackfillIsScopeKeyed63cIAa19a::"
SKEL = f"{N}TestTheIdentityRefusalsHaveAGoldenSkeleton63cIAa19a::"
RQ51 = f"{GOV}TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent"

MUTATIONS: dict[str, tuple[str, str, str, list[str]]] = {
    # id: (file, anchor, replacement, declared RED)
    "M01-WB1-verb-private-copy": (
        P,
        "    if preconditions.owned_unscoped or preconditions.ownerless_scoped:\n        operator = await resolve_operator_principal(principal_store)\n        roster",
        "    private_rows = await run_query(acquire=store.acquire, drop=store.drop, url=store.url, noun=\"private\", "
        "label=\"private.rejected\", statement=f\"SELECT VALUE id FROM {AGENT_TABLE} WHERE scope IS NONE AND "
        "owner_principal IS NOT NONE\", params={}, logger=logger)\n"
        "    if preconditions.owned_unscoped or preconditions.ownerless_scoped or private_rows:\n        operator = await resolve_operator_principal(principal_store)\n        roster",
        K1,
    ),
    "M02-WB2-order-guard-ANDs-owner-count": (
        P,
        "    unmigrated_agents = preconditions.unscoped_count\n    if unmigrated_agents > 0:",
        "    unmigrated_agents = preconditions.unscoped_count\n    if unmigrated_agents > 0 and await _owner_count(store, AGENT_TABLE, none=True) > 0:",
        K2,
    ),
    "M03-WB3-mint-then-undo": (
        S,
        "        await self.agent_registry.preflight(\n            agent,\n            session=session,\n            role=role,\n            spawned_by=spawned_by,\n            owner_principal_id=None if principal is None else str(principal.id).split(\":\", 1)[-1],\n        )\n",
        "",
        [*DRIVEN.values(), HANDLER],
    ),
    "M04-PQ1-485-blank-only-handler": (
        S,
        "        await self.agent_registry.preflight(\n            agent,\n            session=session,\n            role=role,\n            spawned_by=spawned_by,\n            owner_principal_id=None if principal is None else str(principal.id).split(\":\", 1)[-1],\n        )\n",
        "        from loremaster.agents import AgentRegistry  # noqa: PLC0415\n\n        AgentRegistry._refuse_an_invalid_identity(name=agent, session=session, role=role)\n",
        [DRIVEN["AgentIdentityConflictError-role-conflict"], DRIVEN["AgentIdentityConflictError-spawned-by-conflict"], DRIVEN["RetiredAgentError-retired"], HANDLER],
    ),
    "M05-no-compensation": (
        S,
        "            if keep_created and session_keep_bare is not None and self._keep_store is not None:\n                await self._keep_store.delete_keep(keep_id=session_keep_bare)\n",
        "            pass\n",
        [RACE_CREATED],
    ),
    "M06-compensation-deletes-a-FOUND-keep": (
        S,
        "            if keep_created and session_keep_bare is not None and self._keep_store is not None:",
        "            if session_keep_bare is not None and self._keep_store is not None:",
        [RACE_FOUND],
    ),
    "M07-register-private-copy": (
        A,
        "        existing_row = await self.preflight(\n            name,\n            session=session,",
        "        self._refuse_an_invalid_identity(name=name, session=session, role=role)\n        existing_row = await self.preflight(\n            name,\n            session=session,",
        [REGISTER_BOTH, HANDLER],
    ),
    "M08-handler-private-copy": (
        S,
        "        # amendment 22 §1 (#485): EVERY write-free registry refusal BEFORE the session-keep mint.\n",
        "        from loremaster.agents import AgentRegistry  # noqa: PLC0415\n\n        AgentRegistry._refuse_an_invalid_identity(name=agent, session=session, role=role)\n",
        [HANDLER],
    ),
    "M09-zero-receipt-refusal": (
        P,
        "            scanned=None,\n            backfilled=0,\n            already_migrated=None,\n            refused=True,\n            reason=_multi_principal_refusal_reason(",
        "            scanned=0,\n            backfilled=0,\n            already_migrated=0,\n            refused=True,\n            reason=_multi_principal_refusal_reason(",
        [*F3, *HALF, *R2],
    ),
    "M10-message-leg-stamps-NONE-owner": (
        P,
        "    dangling = preconditions.dangling_messages\n    if dangling:",
        "    dangling = preconditions.dangling_messages\n    if dangling and False:",
        [*DANGLING, HOSTILE_GHOST, *GHOST_SHARING, f"{INV}[dangling-sender]"],
    ),
    "M11-private-dangling-check": (
        P,
        "    dangling = preconditions.dangling_messages\n",
        "    dangling = sorted(await run_query(acquire=store.acquire, drop=store.drop, url=store.url, noun=\"private\", "
        "label=\"private.rejected\", statement=f\"SELECT VALUE id FROM {MESSAGE_TABLE} WHERE scope IS NONE AND "
        "record::exists(sender) = false\", params={}, logger=logger) or [], key=str)\n",
        GHOST_SHARING,
    ),
    "M12-CD2-brief-not-supported": (
        P,
        '_GOVERNED_MIGRATE_TABLES = frozenset({"agent", "memory", "message", "brief"})',
        '_GOVERNED_MIGRATE_TABLES = frozenset({"agent", "memory", "message"})',
        [
            f"{A19}TestTheMultiPrincipalRefusalIsAStoreFactAt63cIAa19::test_every_table_refuses_a_multi_principal_store_and_writes_nothing[brief]",
            f"{A19}TestTheMultiPrincipalRefusalIsAStoreFactAt63cIAa19::test_all_four_tables_serve_the_SAME_teaching",
            f"{A19}TestThePreconditionIsSHAREDByMutation63cIAa19::test_the_VERB_LEVEL_check_reads_the_shared_function[brief]",
            f"{A19}TestTheRefusalRendersStoredIdsThroughTheSanitiser63cIAa19::test_a_hostile_stored_id_cannot_forge_a_line_in_the_refusal[brief]",
            K1[3], HALF[3], R2[3],
        ],
    ),
    "M13-validity-after-precondition": (
        P,
        "    if table not in _GOVERNED_MIGRATE_TABLES:\n        return MigrateGovernedResult(",
        "    if False:\n        return MigrateGovernedResult(",
        [INVALID],
    ),
    "M14-WB4-registry-gloss-later-clause": (
        A,
        'f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern}; nothing was "',
        'f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern}; lowercase letters or digits; nothing was "',
        [f"{SKEL}test_the_registry_refusal_skeleton_is_the_golden[name]", f"{SKEL}test_the_registry_refusal_skeleton_is_the_golden[session]"],
    ),
    "M15-WB4-server-gloss-later-clause": (
        S,
        '"{label} must match {pattern} — names must stay in "',
        '"{label} must match {pattern} — lowercase letters or digits; names must stay in "',
        [f"{SKEL}test_the_server_refusal_skeleton_is_the_golden"],
    ),
    "M16-WB7b-names-one-principal-above-bound": (
        P,
        "        shown_owners = owners[:_REFUSAL_ID_SAMPLE_SIZE]\n",
        "        shown_owners = owners[:_REFUSAL_ID_SAMPLE_SIZE] if len(owners) <= _REFUSAL_ID_SAMPLE_SIZE else owners[:1]\n",
        [f"{RQ51}[above-cap]", f"{RQ51}[perturbed-bound]"],
    ),
    "M17-CD1-owner-keyed-WHERE": (
        P,
        '        "WHERE scope IS NONE AND owner_principal IS NONE"',
        '        "WHERE owner_principal IS NONE"',
        [f"{CD1}test_a_scoped_but_ownerless_message_is_never_restamped_and_counts_as_migrated", f"{CD1}test_the_message_backfill_EXECUTES_the_golden", f"{CD1}test_EVERY_governed_legs_backfill_WHERE_is_scope_keyed"],
    ),
    "M18-CD1-not-self-guarding": (
        P,
        '        "WHERE scope IS NONE AND owner_principal IS NONE"',
        '        "WHERE scope IS NONE"',
        [f"{CD1}test_the_message_backfill_EXECUTES_the_golden"],
    ),
    "M19-CD1-owner-keyed-counts": (
        P,
        "    unmigrated = await _scope_count(store, MESSAGE_TABLE, none=True)\n    already = await _scope_count(store, MESSAGE_TABLE, none=False)",
        "    unmigrated = await _owner_count(store, MESSAGE_TABLE, none=True)\n    already = await _owner_count(store, MESSAGE_TABLE, none=False)",
        [f"{CD1}test_a_scoped_but_ownerless_message_is_never_restamped_and_counts_as_migrated"],
    ),
    "M20-F2-half-pair-not-refused": (
        P,
        "    if preconditions.owned_unscoped or preconditions.ownerless_scoped:",
        "    if preconditions.owned_unscoped:",
        [*HALF, PD2, f"{INV}[half-pair-ownerless-scoped]"],
    ),
    "M21-R2-operator-part-dropped": (
        P,
        "    if offending_count and operator is None:",
        "    if False:",
        R2,
    ),
    "M22-R2-owners-classified-as-other": (
        P,
        "    classify = operator is not None\n",
        "    classify = True\n",
        R2,
    ),
}

verdicts = []
for mutation_id, (file, anchor, replacement, declared) in MUTATIONS.items():
    if ONLY and mutation_id.split("-")[0] not in ONLY:
        continue
    work = LOGS / mutation_id
    work.mkdir(exist_ok=True)
    (work / "anchor.txt").write_text(anchor)
    (work / "replacement.txt").write_text(replacement)
    command = [
        "uv", "run", "python", "scripts/mutation_proof.py", "--file", file,
        "--anchor-file", str(work / "anchor.txt"), "--replacement-file", str(work / "replacement.txt"),
    ]
    for node in declared:
        command += ["--expect-red", node]
    command += ["--", "uv", "run", "pytest", "-n", "8", "-q", "-p", "no:randomly", "--tb=no", *FILES]
    completed = subprocess.run(command, cwd=REF, capture_output=True, text=True)
    (work / "proof.log").write_text(completed.stdout + "\n--- stderr ---\n" + completed.stderr)
    verdict = [line for line in completed.stdout.splitlines() if "PROOF" in line]
    verdicts.append(f"{mutation_id}: rc={completed.returncode} declared={len(declared)} :: {verdict[-1] if verdict else completed.stdout[-300:]}")
    print(verdicts[-1], flush=True)
(LOGS / "verdicts.txt").write_text("\n".join(verdicts) + "\n")
```
```bash
# M23 (fake preflight admits existing-row conflicts), run in the reference tree
M=loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestTheFakePreflightMirrorsTheWriter63cIAa19a::test_the_fake_and_the_real_preflight_agree
printf '        self._refuse_an_existing_row_conflict(existing, name=name, role=role, spawned_by=spawned_by)\n        return existing.model_copy(deep=True)\n' > m23_anchor.txt
printf '        return existing.model_copy(deep=True)\n' > m23_repl.txt
uv run python scripts/mutation_proof.py --file loremaster/tests/_comms_fakes.py --anchor-file m23_anchor.txt --replacement-file m23_repl.txt --expect-red "$M[role-conflict]" --expect-red "$M[spawned-by-conflict]" --expect-red "$M[retired]" -- uv run pytest -n 8 -q -p no:randomly --tb=no loremaster/tests/test_fixwave_a19a_63c_i_a.py loremaster/tests/test_comms_tool.py
```

### §A.3 P1c reach driver `p1c_driver.py` (multi-anchor probes + declared-EMPTY probes, hence not mutation_proof.py; content backup + md5-verified restore)
```python
"""contract-63c-i-a-a19a — P1c REACH proof for the derived ∀-refusal-classes pin (amendment 23 FK-1).
Each probe edits agents.py in the scratch REFERENCE (content backup first, md5-verified restore after), runs the
six contract files, and diffs the observed RED set against the set DECLARED HERE, BEFORE the run, both ways.
Multi-anchor probes are why this is not scripts/mutation_proof.py (it takes one anchor); the discipline is the same.
usage: python p1c_driver.py <ref-root> <log-dir>"""

import hashlib
import pathlib
import re
import subprocess
import sys

REF = pathlib.Path(sys.argv[1])
LOGS = pathlib.Path(sys.argv[2])
LOGS.mkdir(parents=True, exist_ok=True)
AGENTS = REF / "loremaster/loremaster/agents.py"
FILES = [
    "loremaster/tests/test_fixwave_a19a_63c_i_a.py",
    "loremaster/tests/test_fixwave_a19_63c_i_a.py",
    "loremaster/tests/test_agent_governance_63c_i_a.py",
    "loremaster/tests/test_message_enforcement_63b_ii_a.py",
    "loremaster/tests/test_agent_registry.py",
    "loremaster/tests/test_message_migrate_63b_ii_a.py",
]
COVERAGE = (
    "loremaster/tests/test_fixwave_a19a_63c_i_a.py::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::"
    "test_every_derived_refusal_class_has_a_driven_fixture"
)
PAIR = [
    f"loremaster/tests/test_agent_governance_63c_i_a.py::TestTheRegistryProvenanceSeam63cIA::{test}[{case}]"
    for test in (
        "test_an_inconsistent_provenance_pair_is_refused_before_any_store_io",
        "test_an_inconsistent_provenance_pair_is_refused_on_the_RE_REGISTER_path_too",
    )
    for case in ("owner-without-keep", "keep-without-owner")
]
PRE_WRITE_ANCHOR = (
    "        self._refuse_an_invalid_identity(name=name, session=session, role=role)\n"
    "        existing_row = await self._select_row(self._agent_id(session, name))\n"
)
POST_WRITE_ANCHOR = "            created = await self._select_row(agent_id)\n            if created is None:\n"
CLASS_ANCHOR = "class AgentRegistry:\n"
DUMMY_CLASS = 'class DummyRefusalError(AgentRegistryError):\n    """P1c reach probe."""\n\n\n'

# id: (list of (anchor, replacement), declared RED set, message fragment the coverage pin must name)
PROBES = {
    "P1c-a-new-subclass-raised-pre-write": (
        [
            (CLASS_ANCHOR, DUMMY_CLASS + CLASS_ANCHOR),
            (PRE_WRITE_ANCHOR, '        if name == "__never__":\n            raise DummyRefusalError("reach probe")\n' + PRE_WRITE_ANCHOR),
        ],
        {COVERAGE},
        "DummyRefusalError",
    ),
    "P1c-b-existing-class-newly-raised-pre-write": (
        [(PRE_WRITE_ANCHOR, '        if name == "__never__":\n            raise UnknownAgentError("reach probe")\n' + PRE_WRITE_ANCHOR)],
        {COVERAGE},
        "UnknownAgentError",
    ),
    "P1c-c-new-subclass-defined-NOT-raised": ([(CLASS_ANCHOR, DUMMY_CLASS + CLASS_ANCHOR)], set(), None),
    "P1c-d-new-subclass-raised-POST-write": (
        [
            (CLASS_ANCHOR, DUMMY_CLASS + CLASS_ANCHOR),
            (POST_WRITE_ANCHOR, '            created = await self._select_row(agent_id)\n            if name == "__never__":\n                raise DummyRefusalError("post-write probe")\n            if created is None:\n'),
        ],
        set(),
        None,
    ),
    "P1c-e-A3-pair-guard-removed": (
        [("            self._refuse_an_inconsistent_provenance_pair(owner_principal_id, keep_id)\n", "            del keep_id\n")],
        {COVERAGE, *PAIR},
        "STALE",
    ),
}

original = AGENTS.read_bytes()
digest = hashlib.md5(original).hexdigest()
results = []
for probe_id, (edits, declared, must_name) in PROBES.items():
    text = original.decode()
    for anchor, replacement in edits:
        assert text.count(anchor) == 1, f"{probe_id}: anchor matched {text.count(anchor)} times: {anchor[:70]!r}"
        text = text.replace(anchor, replacement)
    AGENTS.write_text(text)
    try:
        completed = subprocess.run(
            ["uv", "run", "pytest", "-n", "8", "-q", "-p", "no:randomly", "--tb=line", *FILES],
            cwd=REF, capture_output=True, text=True,
        )
    finally:
        AGENTS.write_bytes(original)
        assert hashlib.md5(AGENTS.read_bytes()).hexdigest() == digest, "RESTORE FAILED"
    (LOGS / f"{probe_id}.log").write_text(completed.stdout + completed.stderr)
    observed = {line.split(" ", 1)[1].split(" - ", 1)[0] for line in completed.stdout.splitlines() if line.startswith("FAILED ")}
    tail = completed.stdout.strip().splitlines()[-1] if completed.stdout.strip() else "<no output>"
    named = must_name is None or must_name in completed.stdout
    held = observed == declared and named and "passed" in tail
    results.append(
        f"{probe_id}: {'PROOF HELD' if held else 'PROOF FAILED'} · declared={sorted(declared)} · "
        f"unexpected={sorted(observed - declared)} · declared-but-green={sorted(declared - observed)} · "
        f"names {must_name!r}: {named} · tail: {tail}"
    )
    print(results[-1], flush=True)
(LOGS / "p1c_verdicts.txt").write_text("\n".join(results) + "\n")
print(f"agents.py restored byte-exact: md5 {digest}")
```

### §A.4 FK-2 ghost-sender probe (the §F receipt; run at HEAD `97b2db6`, production `84af63f`, then deleted)
```python
"""SCRATCH probe (contract-63c-i-a-a19a) — deleted after the run. Ghost-sender message stamping."""
from __future__ import annotations

from _governed_contract import seed_agent_governed, seed_message_legacy
from _surreal_harness import run
from lorerunes.pdp import keep_scope
from test_fixwave_a19_63c_i_a import _governed_world


async def test_probe_ghost_sender() -> None:
    async with _governed_world() as world:
        await seed_agent_governed(
            world.connection, row_id="governed_sender", name="governed-sender", session="s1",
            owner_principal=world.operator_bare, owner_agent="governed_sender", scope=keep_scope("sk1"),
        )
        await seed_message_legacy(world.connection, sender_id="governed_sender", session="s1", seq=1, row_id="m_ok")
        await seed_message_legacy(world.connection, sender_id="ghost_agent", session="s1", seq=2, row_id="m_ghost")
        first = await world.migrate("message")
        rows = await run(world.connection, "SELECT id, owner_principal, owner_agent, scope FROM message ORDER BY id")
        second = await world.migrate("message")
        print(f"\nGHOST first={first!r}\nGHOST rows={rows!r}\nGHOST second={second!r}")
```
