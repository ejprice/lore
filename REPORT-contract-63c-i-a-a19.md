# REPORT-contract-63c-i-a-a19 — contract for the amendment-19 fix wave of 63c-i-a (+ CA-1)

brief-base v16 read · brief project v7 read

## SUMMARY BLOCK
- **state:** done. The pins for §W items 1–5 + CA-1 are written. **29 of them are RED at `84af63f`, and each fails on its defect** (no TypeError, ImportError or AttributeError; §3). A reference fix build passes them. **SAT: full suite ALONE at `-n 12` on the lint-clean reference build → `11529 passed, 62 skipped, 3 xfailed, 7 warnings in 576.32s (0:09:36)` · `EXIT=0` · 0 failed** (§5). **13 mutation proofs all HELD** (§4; M8 held on its second run, after I fixed my own broken replacement).
- **deviations:** (1) ruff-formatted the NEW test file (`ruff format --line-length 110`). The two edited files were hand-wrapped only. (2) No `pending_contracts.yaml` entry was needed: the pins reach the not-yet-existing `principals._agent_migration_preconditions` via `vars(principals).get(...)`, so typecheck stays GREEN at `84af63f` (§6).
- **Packages considered:** none. I specified no mechanism. The only library-level choice was reuse: the pins call the repo's own `loremaster.sanitise.sanitise_line` / `CONTROL_CHAR_PATTERN` and `_governed_contract.patch_shared_object_everywhere` (DRY ledger §10).
- **Odoo-20 portability:** n/a. No Odoo seam touched.
- **Reuse ledger:** 9 new test-local symbols, all dispositioned (§10).
- **Graded:** n/a. I authored a contract; I graded no one's artifact. Base: `84af63f` production code, measured with HEAD `5bea418` (`git diff --stat 84af63f HEAD -- loremaster lorerunes loresigil lorescribe` is empty; the delta is docs only).
- **decisions-needed:** none blocking. Three readings are written down in §8 with my pick: F-1 "operator-owned is still refused", the principal-naming bound, and the shared function's name. The lead or sidecar may overrule any of them.
- **receipt pointers:** §1 per-item table · §2 required-green enumeration · §3 RED@84af63f · §4 mutation proofs (driver verbatim in §A.2) · §5 SAT · §6 gates · §7 DUAL · §8 readings/forks · §9 builder-only items + candidate doors · §10 DRY ledger · §A instruments verbatim (reference build diff, driver).

## §0 Capability check (brief-base §4)
- Idle-gate contract written, not denied: `/tmp/claude-idle-gate-lore/7ad40962-1d69-4104-97ad-8a7ae5a02d44-contract-63c-i-a-a19.contract` = `{"artifact": "REPORT-contract-63c-i-a-a19.md"}`. I used my own session id. The brief's `<session-id>` did not say whose.
- lore was reachable. `lore_comms register` succeeded (session `63c-20260924`, role `contract`, cadence `≤20m`). `lore_index()` showed root `/workspace`, branch `feat/surreal-unification`, ref `5bea418` = HEAD, last_sync 92 s, so no reconcile was needed. I used `lore_get_symbol(sanitise_line)` to find the CURRENT sanitiser seam (`loremaster/loremaster/sanitise.py::sanitise_line`; `search._sanitise_line` is a re-binding of it). `lore_search` for the DRY ledger (§10) returned nothing reusable at `summary` detail.
- **Fallback declared:** grep/rg are hook-blocked (#473), so textual sweeps used `awk` over `git ls-files`. There were three: callers of `migrate_governed`/`_owner_count` across tests, existing assertions on the identity-refusal prose, and `is_blank` consumers. Cases (b)/(c) apply: prose seams and a cross-cutting map.
- I read the store reference `docs/reference/surrealdb-31-capabilities.md` FIRST (§0–§8; §1.4's "seed legacy rows under the old DDL" and §2's `SELECT *` omits-NONE are cited in the new file's docstring).
- Nothing demanded was unsatisfiable. I never touched `:18500` or TEI. I used no worktrees and no `git stash`. At most one pytest ran at a time: I checked the process table before each run, and `free` showed ≥47 GB available throughout.

## §1 Per-item table
| # | item | pin (file::test) | wrong build killed | mutation receipt |
|---|---|---|---|---|
| 1 | verb-level §2.1 precondition, ∀ tables, byte-identical store | `test_fixwave_a19_63c_i_a.py::TestTheMultiPrincipalRefusalIsAStoreFactAt63cIAa19::test_every_table_refuses_a_multi_principal_store_and_writes_nothing[agent\|memory\|message\|brief]` + `::test_all_four_tables_serve_the_SAME_teaching` | `84af63f` (memory proceeds; message refuses with the ORDER teaching; brief refuses as unsupported); M13 (check only in agent+message) | RED@84af63f ×4 of 5 (§3) · M13 HELD (7 declared = observed) |
| 1 | order guard re-keyed owner→scope, discriminating fixtures | `…TestTheMessageOrderGuardIsScopeKeyed63cIAa19::test_CA_A_the_message_leg_refuses_the_store_the_agent_leg_refuses` (CA-A store: every agent owned-but-unscoped, 2 foreign principals, 0 ownerless) + `::test_CONTROL_an_ownerless_SCOPED_agent_does_not_trip_the_order_guard` (the predicates disagree the OTHER way) | `84af63f` = CA-A (owner-keyed guard) | RED@84af63f ×2 · M2 (private order-guard query) and M3 (verb check keyed on unscoped alone) HELD |
| 1 | sharing by MUTATION | `…TestThePreconditionIsSHAREDByMutation63cIAa19::test_the_VERB_LEVEL_check_reads_the_shared_function[×4]` + `::test_the_ORDER_GUARD_reads_the_shared_function`. The ONE function is REDIRECTED to read another store, each leg has a twin-store BASELINE, and a call counter proves the redirect landed | M1 (private verb-level copy of the predicate), M2 (private order-guard `_scope_count`) | M1 HELD (4 = 4) · M2 HELD (1 = 1) |
| 1 | DUAL preserved legs | `…::test_PRESERVED_a_legacy_unscoped_agent_refuses_the_message_leg_until_the_agent_leg_runs` · `…::test_PRESERVED_a_single_principal_legacy_store_is_never_refused_as_multi_principal[memory\|brief]` | M3 (verb check keyed on `scope IS NONE` alone refuses every legacy store) | M3 HELD (9 = 9, incl. 6 pre-existing R-Q5-2/3/CONTROL/idempotent/exempt/only-the-legacy pins) |
| 2 | F-3 `AND owner_principal IS NONE` + golden | `test_agent_governance_63c_i_a.py::_assert_the_backfill_statement_shape` (golden re-keyed; either conjunct order) → `…::test_the_migrate_exempt_token_carries_the_EXECUTED_three_column_statement`; control `TestTheBackfillShapeAssertNormalisesSpellingNeverWidens63cIA::test_a_wrong_statement_still_fails[scope-only-not-self-guarding-F3]` + `test_a_correct_statement_passes_in_any_spelling[conjuncts-in-either-order]` | `84af63f` statement / M12 | RED@84af63f · M12 HELD |
| 3 | F-4: handler refuses a blank role before the keep mint | `test_fixwave_a19_63c_i_a.py::TestABlankRoleRegisterHasNoSideEffect63cIAa19::test_a_blank_role_credentialed_register_mints_no_keep_and_denies_no_third_party[''\|'   '\|'\t\n']`. It checks keep + member_of + agent tables byte-identical, then bob's valid register SUCCEEDS and bob keeps the session (the third-party leg). Controls: `::test_CONTROLS_a_hostile_name_mints_no_keep_and_a_valid_register_mints_exactly_one` | `84af63f` = CA-B; M9 (no handler check) | RED@84af63f ×3 · M9 HELD (4 = 4) |
| 3 | handler leg on the shared-decision pin | `test_agent_registry.py::TestQ3RegisterValidatesIdentityBeforeStoreIO63cIA::test_the_blank_role_rule_is_the_SHARED_is_blank[handler]`. It perturbs THE `lorerunes.is_blank` so `builder` counts as blank; the handler must refuse before minting `session:wave-mut` | M8 (handler with a private `role.strip()`) | RED@84af63f · M8 HELD (1 = 1) |
| 4 | F-1 derived diagnosis + operator-owned population | `test_agent_governance_63c_i_a.py::TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent[…]`. Two populations are NEW: `operator-owned` (E3) and `mixed-owners` (cap+3, operator + 2 foreign). All 6 populations assert the derived diagnosis (`_assert_the_derived_diagnosis`) | `84af63f` (fixed phrase); M10 (fixed phrase restored); M11 (operator not derived) | RED@84af63f ×6 · M10 HELD (6 = 6) · M11 HELD (2 = 2) |
| 4 | CA-1: ids through the shared sanitiser, hostile fixture | `test_fixwave_a19_63c_i_a.py::TestTheRefusalRendersStoredIdsThroughTheSanitiser63cIAa19::test_a_hostile_stored_id_cannot_forge_a_line_in_the_refusal[×4 tables]` (newline + `#999 [directive] …` forgery + backtick runs, in BOTH an agent id and an owning-principal id, plus a plain control) + `::test_the_id_render_ROUTES_through_the_shared_sanitise_line` (identity sweep with a tagging wrapper) | `84af63f` (raw render); M6 (raw); M7 (hand-rolled `.replace("\n"," ")`) | RED@84af63f ×5 · M6 HELD (5 = 5) · M7 HELD (1 = 1) |
| 5 | F-9: gloss dropped, one rule/one spelling | `test_fixwave_a19_63c_i_a.py::TestTheIdentityRuleHasOneSpelling63cIAa19::test_both_refusals_serve_the_SAME_rule_and_it_is_the_pattern` + `::test_the_served_rule_MOVES_with_the_shared_pattern` (perturbs THE `AGENT_NAME_PATTERN` object) | `84af63f` (registry gloss, server "does not match"); M4 (gloss restated); M5 (server second spelling) | RED@84af63f ×2 · M4 HELD · M5 HELD |

**Full-suite leg for survivor claims:** I make no survivor claim. Every declared wrong build was killed in the targeted run (§4).

## §2 Required-green enumeration (checked BEFORE design, re-checked by SAT)
The correct builds that prior rulings REQUIRE green, and how each pin respects them:
1. **Single-principal stores: every leg proceeds exactly as before** (§E). The verb-level check keys on OWNED-but-unscoped, never unscoped alone. It is pinned both ways: by `test_PRESERVED_…single_principal…[memory|brief]` and by M3 reddening 6 pre-existing R-Q5 pins.
2. **Memory-only stores (no `agent` table DEFINED):** the 63a memory suites run the memory leg on DBs without an agent table. My first reference build queried `agent` unconditionally, and that failed 5 tests in `test_governed_migration_63a.py` / `test_memory_enforcement_63b_ia.py` (`governed scope count rejected … unspecified rejection`). The reference therefore treats an undefined `agent` table as "no agents" via `INFO FOR DB`. **Builder note:** a correct build MUST handle this. Swallowing the error is NOT a correct way to do it.
3. **The existing 63c-i-a contract** (R-Q5-1 count/sample/`by hand`/true-integer legs, R-Q5-2/3, only-the-legacy, idempotent, exempt token) stays green on the reference build, re-proven in SAT. R-Q5-1's integer check needed ONE satisfiability widening. The ruling's own F-1 wording (*"pkt-62–63b image; see amendment-1 E3"*) carries digits that are citations, not counts. They are now stripped by shape: `#n`, `word-n[–n]`, `E3`. The bound is stated in-line.
4. **Amendment 13/14 refusal-count rules:** every integer the derived diagnosis may state is added to R-Q5-1's `admitted` set as a TRUE count: operator-owned count, foreign count, distinct foreign principals, and how many are named. The birth-value guard is kept.
5. **ii-a message pins** (`test_message_migrate_63b_ii_a.py`): their fixtures register agents WITH `session_keep_id`, so the agents are scoped and are not multi-principal under the new predicate. The order-guard refusal still names "agent". GREEN on the reference build.
6. **The existing `is_blank` sharing legs** (`register`, `fake`) are unchanged. The existing registry refusal pins (`field`, `AGENT_NAME_PATTERN.pattern in message`, `register again`, `render_fenced(value)`) still hold with the gloss dropped. `test_comms_tool.py`'s `"safe charset"` assertions are why the reference server text keeps "names must stay in the safe charset" (a rationale, not a gloss).

## §3 RED at `84af63f` (main tree, production = `84af63f`, new pins in place) — 29 failed / 21 passed
Command: `uv run pytest -n 8 -q --tb=line loremaster/tests/test_fixwave_a19_63c_i_a.py "…test_agent_governance_63c_i_a.py::TestAgentMigrateScopeKeyed63cIA" "…::TestTheBackfillShapeAssertNormalisesSpellingNeverWidens63cIA" "…test_agent_registry.py::…::test_the_blank_role_rule_is_the_SHARED_is_blank"` → `29 failed, 21 passed in 12.56s`. Failure reasons, one line each (from `--tb=line`):
- ∀-tables `[memory]` → `--table memory PROCEEDED on a store holding 11 owned-but-unscoped agents`; `[message]`/`[brief]` → `the refusal does not state the STORE fact — 11 owned-but-unscoped agent row(s)`; SAME-teaching → `got {'agent': '11 agent row(s) carry …', …}`. `[agent]` is GREEN (its leg-level precondition), which is the control.
- CA-A → `the message leg PROCEEDED on the store the agent leg refuses as multi-principal`.
- ownerless-SCOPED CONTROL → `the message order guard FIRED on a store whose every agent is migrated`.
- sharing ×5 → `Failed: principals._agent_migration_preconditions does not exist — amendment 19 D-1 requires ONE function …`. An explicit `pytest.fail` naming the defect, not an AttributeError.
- CA-1 `[agent]` → `CA-1 (#484): the refusal renders a STORED record id raw — a newline / control character reaches the served line`; `[memory|message|brief]` → `does not name the hostile agent id through sanitise_line` (no store-fact refusal on those tables at 84af63f, which is item 1's defect showing through); routing → the identity-sweep miss message.
- blank role ×3 → `a blank-role credentialed register WROTE ['keep', 'member_of'] before refusing`; `[handler]` → `the register HANDLER's blank-role refusal (it minted the session keep first) …`.
- F-9 → `the refusal does not state its rule as 'must match <pattern>': 'agent name does not match ^[a-z0-9][a-z0-9_-]{0,63}$ …'`; MOVES → the sweep-miss message on the registry rule.
- R-Q5-1 ×6 → `F-1: the refusal serves the FIXED diagnosis 'multi-principal or half-applied'`.
- exempt token → `the agent backfill must be ONE scope-keyed, SELF-GUARDING UPDATE (… 'WHERE scope IS NONE AND owner_principal IS NONE')`.
- GREEN at 84af63f by design (21): ∀`[agent]`, both PRESERVED classes (3), CONTROLS, the backfill-shape controls (8, build-independent), R-Q5-1 CONTROL/R-Q5-2/3/idempotent/only-the-legacy (5), `is_blank[register|fake]` (2), plus `F-3` shape control `[scope-only-not-self-guarding-F3]` inside the 8. Total 21 = 50 collected − 29.

## §4 Mutation proofs (reference build in `./scripts/scratch_copy.sh` copy; `scripts/mutation_proof.py`; declared sets written in the driver BEFORE the run, ids from `--collect-only`; every file restored byte-exact)
Provenance: `loremaster.__file__` = `…/scratchpad/ref-tree/loremaster/loremaster/__init__.py` (the scratch copy; scratch_copy.sh asserted all four members).
| id | mutation (reference build → wrong build) | declared RED | verdict |
|---|---|---|---|
| M1 | verb-level check uses a PRIVATE inline copy of the owned-unscoped query | VERB_LEVEL sharing ×4 | **PROOF HELD** rc 0 |
| M2 | order guard uses `_scope_count(store, AGENT_TABLE, none=True)` directly (same semantics, private) | ORDER_GUARD sharing ×1 | **PROOF HELD** rc 0 |
| M3 | verb-level check `owned_unscoped or unscoped_count` (keyed on unscoped alone) | 3 PRESERVED + 6 existing TestAgentMigrateScopeKeyed63cIA pins | **PROOF HELD** rc 0 |
| M4 | registry refusal restates a gloss after the pattern | F-9 ×2 | **PROOF HELD** rc 0 |
| M5 | server refusal back to "does not match {pattern}" | F-9 ×2 | **PROOF HELD** rc 0 |
| M6 | ids rendered raw (`str(row_id)`) — CA-1 | CA-1 property ×4 + routing | **PROOF HELD** rc 0 |
| M7 | ids hand-sanitised `.replace("\n", " ")` (a private copy of the seam) | routing ×1 | **PROOF HELD** rc 0 |
| M8 | handler blank check is a private `role.strip()` | `is_blank[handler]` | first run **PROOF FAILED rc 4**, and the cause was **MY mutation**: the replacement raised `NameError: AgentRegistryError` (not imported), which reddened 3 extra tests. Re-run with the import: **PROOF HELD** rc 0 |
| M9 | handler check deleted (= CA-B) | `is_blank[handler]` + blank-role ×3 | **PROOF HELD** rc 0 |
| M10 | F-1 fixed phrase "multi-principal or half-applied" restored | R-Q5-1 ×6 | **PROOF HELD** rc 0 |
| M11 | operator never recognised (`operator_bare = None`: all owners "other") | R-Q5-1 `[operator-owned]`, `[mixed-owners]` | **PROOF HELD** rc 0 |
| M12 | F-3 conjunct dropped from the backfill | exempt-token golden ×1 | **PROOF HELD** rc 0 |
| M13 | verb-level check only for `agent`/`message` | ∀ `[memory]`,`[brief]`, SAME-teaching, VERB_LEVEL `[memory]`,`[brief]`, CA-1 `[memory]`,`[brief]` | **PROOF HELD** rc 0 |
Raw log: the driver (§A.2) writes `run_all.log`; the per-proof `PROOF HELD — the declared RED set fired EXACTLY` lines are what the verdict column cites.

## §5 SAT receipt — full suite ALONE, `-n 12`, on the lint-clean reference build
- Tree: `./scripts/scratch_copy.sh …/scratchpad/ref-tree` (provenance asserted by the tool; `loremaster.__file__` = `…/scratchpad/ref-tree/loremaster/loremaster/__init__.py`). Production = the reference build of §A.1 AFTER the lint cleanups (ruff/typecheck GREEN first, then the run). Tests = the three contract files, `cmp`-identical to the main tree (checked after the run).
- Pre-checks: no other pytest in the process table, `free` 55 GB available, `spike-surreal.service` active. A PID watchdog (§A.3) was armed at 15 GB and polled every 10 s. It **never fired** (`watchdog: pytest 608457 exited; never fired`).
- Tail, verbatim:
  ```
  11529 passed, 62 skipped, 3 xfailed, 7 warnings in 576.32s (0:09:36)
  EXIT=0
  ```
  **0 failed, 0 errors.** Count check: the cold audit's `84af63f` baseline was `11498 passed, 62 skipped, 3 xfailed`. This contract adds 31 tests (26 in the new file, R-Q5-1 +2 populations, shape +2 controls, `is_blank[handler]` +1), and 11498 + 31 = 11529.
- The run was started once earlier and deliberately STOPPED ~1 min in, because the reference build still had a ruff E501. The brief requires 0-failed AFTER the lint cleanups, so the cleanup came first and the run was restarted. That aborted run's log was discarded; this one is the receipt.

## §6 Gate receipts (2026-09-25)
- **Main tree (production `84af63f` + the new pins):** `uv run ruff check .` → `All checks passed!` · `./scripts/typecheck.sh` → rc 0 (every leg OK) · `pending_contract_gate.py --currency --legs typecheck,ruff` → `typecheck GREEN`, `ruff GREEN`, `pytest NOT_RUN` (excluded by `--legs`, per #466). **No `pending_contracts.yaml` entry added**, because no typecheck red was introduced (the missing shared function is reached via `vars(principals).get`).
- **Reference tree (after the lint cleanups — two string re-wraps in the order-guard reason):** ruff `All checks passed!` · typecheck rc 0 · currency typecheck/ruff GREEN. Production md5 of the SAT bytes: `principals.py 08b0c9a0…`, `agents.py 71523978…`, `server.py 49465c48…`.

## §7 DUAL — removed/changed behaviour (item 1 moves a table-level check to the verb and re-keys a guard)
| old per-table behaviour (`84af63f`) | fate | pin / reason |
|---|---|---|
| agent leg: row precondition refuses owned-but-unscoped, byte-inert, count + bounded ids + "by hand" | **preserved-with-pin** (moved to the verb) | R-Q5-1 (6 populations) + ∀`[agent]`; spec: amendment 19 D-1 |
| memory leg: NO agent precondition, proceeds on any store (mints project keep, stamps scope) | **changed deliberately** on a multi-principal store → refuses (D-1: "memory rows widened into the project keep are wrong there too") · **preserved** on single-principal/legacy stores | ∀`[memory]` · `test_PRESERVED_…single_principal…[memory]` |
| memory leg on a store with NO `agent` table | **preserved** (the 63a suites) | SAT (the 5 memory tests that reddened my first reference build) |
| message leg order guard: refuses while any `agent.owner_principal IS NONE` | **re-keyed** to `scope IS NONE` through THE shared function (D-1) | CA-A + ownerless-SCOPED CONTROL + ORDER_GUARD sharing |
| message leg order guard on a legacy (ownerless, unscoped) store: refuses naming "agent", byte-inert; proceeds after the agent leg | **preserved-with-pin** (§2.6) | `test_PRESERVED_a_legacy_unscoped_agent_refuses_…_until_the_agent_leg_runs` + the ii-a pins |
| message leg on an owned-but-unscoped store with no ownerless agent: PROCEEDS, stamps foreign owners into the project keep | **dropped — it was the BUG (CA-A / BR-F-2)**, not re-pinned | CA-A pin |
| brief: refused as "not supported at 63b" on every store | **changed** on a multi-principal store → the §2.1 teaching (D-1 lists brief) · **preserved** elsewhere (still table-local, never the §2.1 teaching) | ∀`[brief]` · `test_PRESERVED_…[brief]` |
| agent backfill UPDATE `WHERE scope IS NONE` | **changed deliberately** → `… AND owner_principal IS NONE` (F-3); golden re-keyed by me, DUAL comment at `_assert_the_backfill_statement_shape` | exempt-token pin + shape controls |
| R-Q5-1: "never assert a refusal over an operator-owned row" (E3 rule, r2–r4) | **re-keyed deliberately** per amendment 19 D-3 (DUAL paragraph in its docstring); E3's narrowing remains deferred and is pinned as the known bound | R-Q5-1 `[operator-owned]` |
| R-Q5-1 integer check: every digit counted, except § citations | **widened deliberately** (citation SHAPES are stripped: `#n`, `word-n[–n]`, `E3`) so the ruling's own F-1 wording is satisfiable; bound stated in-line | R-Q5-1, all populations |
| `_owner_count` agent use | **retired** (D-1) | M2 (a private count reddens) — message-row use stays (builder F-5 docstring) |

## §8 Readings / forks written down (brief-base §2: a sentence with two readings is the trigger)
1. **F-1 on an operator-only store: refused or not?** D-3 says the operator-owned population's served text is asserted, and that "E3's narrowing … stays deferred as ruled". **My pick:** at i-a it is still REFUSED, and the DIAGNOSIS must say "owned by the operator … E3" and must not say "multi-principal". The alternative reading would make the refusal assertion conditional. The pin carries a PINNED-BOUND note: the day E3's trigger fires and the precondition is narrowed deliberately, `[operator-owned]`'s refusal assertion is the one to change.
2. **"other principals (named, bounded)": which bound?** The ruling names none. **My pick:** the same `_REFUSAL_ID_SAMPLE_SIZE`. Every foreign principal is named when there are ≤ bound of them; above the bound, 1..bound are named. The alternative is a second constant. A build choosing a different, smaller bound still passes; one naming more than `_REFUSAL_ID_SAMPLE_SIZE` principals fails.
3. **The shared function's NAME.** The ruling says "`_agent_migration_preconditions(store)` or the like". **My pick:** that exact name, pinned in `_SHARED_PRECONDITIONS`. Only the name and the fact that it receives the `StoreHandle` are pinned; its return shape is the builder's. The sharing pin is type-agnostic: it redirects the real function at another store.
4. (Not a fork, a stated bound.) When an owned-but-unscoped store ALSO has an unresolvable operator, which refusal wins is not pinned. Both are byte-inert refusals. The reference build refuses at the verb level and diagnoses owners as "other" when the operator is unresolved.

## §9 Builder-only items (NO pin, per the brief) + candidate doors (NOT pinned — the lead's call)
**Builder items:** F-8 (replace the refuted "inlined as a literal into live WHERE clauses" threat model in `lorerunes/identifiers.py` and the `agents.py` block comment with #219's corrected rationale) · F-5 (`_owner_count` docstring; its agent use is retired) · F-7 DUAL line ("dropped-deliberately: `is_blank` is the ONE blankness rule (#222)") · cold-audit R-4 wording ("a `refused=True` writes nothing" in the builder's R8 DUAL row) · the reference build's handler call reaches a registry-private static (`_refuse_an_invalid_identity`, SLF001-noqa'd). The builder may prefer a public seam, and the pins accept either (they observe the effect + the `is_blank` identity sweep).
**Candidate doors (noticed, outside §W — surfaced, not pinned):**
- **CD-1 · the message backfill's own `WHERE owner_principal IS NONE`** has the same TOCTOU shape F-3 closed for agents, and it stays owner-keyed while the agent side moved to scope. Out of §W. Flagging for 63c-ii.
- **CD-2 · `migrate_governed` for an unsupported table on a multi-principal store** now serves the §2.1 teaching instead of "not supported" (verb-level first). That is correct by D-1 for `brief`. For a typo'd table name (`--table tasks`) the operator sees the multi-principal refusal first, which is arguably fine but unruled.
- **CD-3 · the order-guard refusal text** in the reference build says "un-migrated (NONE-scope) agent(s)". The ii-a pins only need "agent", so its exact wording is unpinned. The builder should keep it derived (the count is the shared function's).
- **CD-4 · `test_comms_schema.py::_create_agent`**, the third raw-CREATE clone (cold-audit CA-3), is untouched here.

## §10 DRY ledger (new reusable symbols — all test-local)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_snapshot` / `_keep_snapshot` (byte-inert table snapshots) | `lore_search("test helper that snapshots SELECT * of several tables to assert a refusal is byte-inert", tier=lore)` | only CLAUDE.md prose (budget-elided). By awk, R-Q5-1 inlines `SELECT * … ORDER BY id`. `_refusal_effect.assert_tool_refused_and_did_not_run` is WIRE-tool-only (takes `WireSession.call`) | HAND-ROLLED: no multi-table store snapshot helper exists, and the wire helper cannot drive an in-process verb |
| `_World` / `_governed_world` | (same area) `_governed_contract` read directly | `agent_migrate_world` (agent DDL only, pytest fixture) · `build_principal_and_keep_stores` | EXTENDED by composition: it calls `build_principal_and_keep_stores`, `apply_ddl`, `store_handle`, `governed_overlay_ddl`. A context manager (not a fixture) because the sharing pins need 3 stores per test |
| `_seed_multi_principal_store`, `_seed_foreign_principals`, `_seed_clean_single_principal_store` | — | seeders `seed_agent_governed`/`seed_agent_legacy`/`seed_memory_legacy`/`seed_message_legacy` | REUSED (each composes only the F5 home's seeders; no raw CREATE) |
| `_redirect_the_shared_preconditions` | — | `patch_shared_object_everywhere` (identity sweep over module bindings) | HAND-ROLLED: the sweep rebinds an OBJECT everywhere. This needs the REAL function re-pointed at another store (arg swap), which the sweep cannot express. It is used by 2 pins only |
| `_served_rule` / `_RULE_CLAUSE` | `lore_search("extract the rule clause 'must match pattern' …", tier=lore)` | no code hit | HAND-ROLLED (one regex; the pins that need it are in this file) |
| `_trap_owners`, `_assert_the_derived_diagnosis` (R-Q5-1 static helpers) | — | extracted from R-Q5-1's body to keep it under PLR0912/0915 | EXTENDED `TestAgentMigrateScopeKeyed63cIA` in place |

## §A Instruments (verbatim — scratch is disposable)
### A.1 Reference fix build (the SAT bytes) — `git diff -- loremaster/loremaster` in the scratch copy
```diff
diff --git a/loremaster/loremaster/agents.py b/loremaster/loremaster/agents.py
index 7edcd54..543c014 100644
--- a/loremaster/loremaster/agents.py
+++ b/loremaster/loremaster/agents.py
@@ -699,8 +699,7 @@ class AgentRegistry:
         for field_name, value in (("name", name), ("session", session)):
             if not is_legal_identifier(value):
                 raise InvalidAgentIdentityError(
-                    f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern} (lowercase "
-                    f"letters, digits, '_' or '-', starting with a letter or digit); nothing was "
+                    f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern}; nothing was "
                     f"written — register again with a legal {field_name}. The rejected value "
                     f"was:\n{render_fenced(value)}"
                 )
diff --git a/loremaster/loremaster/principals.py b/loremaster/loremaster/principals.py
index ce55504..76310bf 100644
--- a/loremaster/loremaster/principals.py
+++ b/loremaster/loremaster/principals.py
@@ -98,7 +98,7 @@ from loremaster.config import (
     resolve_secret,
 )
 from loremaster.index.records import sha512_hex
-from loremaster.sanitise import safe_str
+from loremaster.sanitise import safe_str, sanitise_line
 from loremaster.store._txn import (
     _CONNECTION_ERRORS,
     StoreHandle,
@@ -1089,6 +1089,19 @@ async def migrate_governed(
     """
     from loremaster.governed import MigrateGovernedResult
 
+    # amendment 19 D-1: the §2.1 multi-principal refusal is a STORE fact, checked ONCE here, before
+    # ANY table's leg — every --table value refuses with the SAME teaching and writes nothing.
+    preconditions = await _agent_migration_preconditions(store)
+    if preconditions.owned_unscoped:
+        operator = await resolve_operator_principal(principal_store)
+        return MigrateGovernedResult(
+            table=table,
+            scanned=0,
+            backfilled=0,
+            already_migrated=0,
+            refused=True,
+            reason=_multi_principal_refusal_reason(preconditions, operator),
+        )
     if table == MEMORY_TABLE:
         return await _migrate_memory_scope(store, keep_store, principal_store)
     if table == AGENT_TABLE:
@@ -1271,6 +1284,84 @@ async def _owner_count(store: StoreHandle, table: str, *, none: bool) -> int:
 _REFUSAL_ID_SAMPLE_SIZE = 10
 
 
+class AgentMigrationPreconditions(BaseModel):
+    """The agent table's migration state, read ONCE (amendment 19 D-1): the NONE-scope count (the
+    unmigrated predicate ∀ governed tables) and every owned-but-unscoped row as ``(id, owner)``."""
+
+    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
+
+    unscoped_count: int
+    owned_unscoped: list[tuple[Any, Any]]
+
+
+async def _agent_migration_preconditions(store: StoreHandle) -> AgentMigrationPreconditions:
+    """THE shared agent-migration predicate (amendment 19 D-1): the verb-level §2.1 check and the
+    message leg's agent-first ORDER guard both call this. A store with no ``agent`` table DEFINED
+    holds no agent (a memory-only store): nothing is unmigrated, nothing is owned."""
+    info = await run_query(
+        acquire=store.acquire,
+        drop=store.drop,
+        url=store.url,
+        noun="governed agent table probe",
+        label="governed.agent_table_probe.rejected",
+        statement="INFO FOR DB",
+        params={},
+        logger=logger,
+    )
+    tables = info.get("tables", {}) if isinstance(info, dict) else {}
+    if AGENT_TABLE not in tables:
+        return AgentMigrationPreconditions(unscoped_count=0, owned_unscoped=[])
+    unscoped_count = await _scope_count(store, AGENT_TABLE, none=True)
+    rows = await run_query(
+        acquire=store.acquire,
+        drop=store.drop,
+        url=store.url,
+        noun="governed agent row precondition",
+        label="governed.agent_precondition.rejected",
+        statement=(
+            f"SELECT id, owner_principal FROM {AGENT_TABLE} "
+            "WHERE scope IS NONE AND owner_principal IS NOT NONE"
+        ),
+        params={},
+        logger=logger,
+    )
+    owned = [(row["id"], row["owner_principal"]) for row in (rows or [])]
+    owned.sort(key=lambda pair: str(pair[0]))
+    return AgentMigrationPreconditions(unscoped_count=unscoped_count, owned_unscoped=owned)
+
+
+def _multi_principal_refusal_reason(
+    preconditions: AgentMigrationPreconditions, operator: Principal | None
+) -> str:
+    """The derived §2.1 refusal (F-1): says WHO owns the offending rows; ids render via sanitise_line."""
+    operator_bare = None if operator is None else (operator.id.partition(":")[2] or operator.id)
+    offending_count = len(preconditions.owned_unscoped)
+    operator_owned = [pair for pair in preconditions.owned_unscoped if str(pair[1].id) == operator_bare]
+    foreign = [pair for pair in preconditions.owned_unscoped if str(pair[1].id) != operator_bare]
+    parts = [f"{offending_count} agent row(s) carry an owner but no scope."]
+    if operator_owned:
+        parts.append(
+            f"{len(operator_owned)} of them are owned by the operator — registered by a pkt-62–63b "
+            "image (see amendment-1 E3)."
+        )
+    if foreign:
+        owners = sorted({sanitise_line(str(owner)) for _row_id, owner in foreign})
+        shown_owners = owners[:_REFUSAL_ID_SAMPLE_SIZE]
+        parts.append(
+            f"{len(foreign)} of them are owned by {len(owners)} other principal(s) — a "
+            f"multi-principal store (§2.1); first {len(shown_owners)} of {len(owners)} principals "
+            f"shown: {', '.join(shown_owners)}."
+        )
+    shown_ids = [sanitise_line(str(row_id)) for row_id, _owner in preconditions.owned_unscoped][
+        :_REFUSAL_ID_SAMPLE_SIZE
+    ]
+    parts.append(
+        f"First {len(shown_ids)} of {offending_count} ids shown: {', '.join(shown_ids)}. "
+        "Adjudicate these rows by hand before migrating; no row was stamped"
+    )
+    return " ".join(parts)
+
+
 async def _migrate_agent_owner(
     store: StoreHandle,
     keep_store: KeepStore,
@@ -1327,39 +1418,6 @@ async def _migrate_agent_owner(
             already_migrated=already,
             refused=False,
         )
-    # §2.1 ROW precondition (#470 / F10), BEFORE any write — the refusal is byte-inert. ONE read
-    # yields both the count and the sample, so the two numbers the refusal states can never
-    # describe different sets.
-    owned_unscoped_rows = await run_query(
-        acquire=store.acquire,
-        drop=store.drop,
-        url=store.url,
-        noun="governed agent row precondition",
-        label="governed.agent_precondition.rejected",
-        statement=(
-            f"SELECT VALUE id FROM {AGENT_TABLE} "
-            "WHERE scope IS NONE AND owner_principal IS NOT NONE"
-        ),
-        params={},
-        logger=logger,
-    )
-    owned_unscoped_ids = sorted(str(row_id) for row_id in (owned_unscoped_rows or []))
-    if owned_unscoped_ids:
-        offending_count = len(owned_unscoped_ids)
-        shown_ids = owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE]
-        return MigrateGovernedResult(
-            table=AGENT_TABLE,
-            scanned=unmigrated + already,
-            backfilled=0,
-            already_migrated=already,
-            refused=True,
-            reason=(
-                f"{offending_count} agent row(s) carry an owner but no scope — a multi-principal "
-                f"or half-applied store (§2.1). First {len(shown_ids)} of {offending_count} ids "
-                f"shown: {', '.join(shown_ids)}. Adjudicate these rows by hand before migrating; "
-                "no row was stamped"
-            ),
-        )
     project_keep = await keep_store.get_or_create_keyed(
         key=PROJECT_KEEP_KEY, type="project", keeper_email=operator.email, name="lore"
     )
@@ -1369,7 +1427,7 @@ async def _migrate_agent_owner(
     # (never a module constant) passed to BOTH the statement-scoped exemption and the execution.
     backfill_statement = (
         f"UPDATE {AGENT_TABLE} SET owner_principal = type::record('{PRINCIPAL_TABLE}', $owner), "
-        "owner_agent = id, scope = $scope WHERE scope IS NONE"
+        "owner_agent = id, scope = $scope WHERE scope IS NONE AND owner_principal IS NONE"
     )
     with governed_exempt("migrate-governed", statement=backfill_statement):
         await run_query(
@@ -1414,8 +1472,8 @@ async def _migrate_message_owner(
 
     from loremaster.governed import PROJECT_KEEP_KEY, MigrateGovernedResult, governed_exempt
 
-    # §2.6 agent-first: refuse while ANY agent is still NONE-owner (count>0, never only count==1).
-    unmigrated_agents = await _owner_count(store, AGENT_TABLE, none=True)
+    # §2.6 agent-first: refuse while ANY agent is still un-migrated (scope NONE; amendment 19 D-1).
+    unmigrated_agents = (await _agent_migration_preconditions(store)).unscoped_count
     if unmigrated_agents > 0:
         return MigrateGovernedResult(
             table=MESSAGE_TABLE,
@@ -1425,9 +1483,9 @@ async def _migrate_message_owner(
             refused=True,
             reason=(
                 f"cannot migrate `message` rows before the `agent` table is migrated "
-                f"({unmigrated_agents} NONE-owner agent(s) remain) — a message's owner_principal is "
-                "read from sender.owner_principal, NONE for every un-migrated agent (§2.6 agent-first "
-                "ORDER); run migrate-governed for `agent` first"
+                f"({unmigrated_agents} un-migrated (NONE-scope) agent(s) remain) — a message's "
+                "owner_principal is read from sender.owner_principal, NONE for every un-migrated agent "
+                "(§2.6 agent-first ORDER); run migrate-governed for `agent` first"
             ),
         )
 
diff --git a/loremaster/loremaster/server.py b/loremaster/loremaster/server.py
index 4b401d4..5aaf710 100644
--- a/loremaster/loremaster/server.py
+++ b/loremaster/loremaster/server.py
@@ -6573,7 +6573,7 @@ class AppContext:
                 str(
                     render_compose(
                         render_line(
-                            "{label} does not match {pattern} — names must stay in "
+                            "{label} must match {pattern} — names must stay in "
                             "the safe charset. The rejected value was:",
                             label=sanitise_line(label),
                             pattern=sanitise_line(AGENT_NAME_PATTERN.pattern),
@@ -6717,6 +6717,11 @@ class AppContext:
         # register, never a conditional splat), so the registry stamps ``scope`` from the SAME
         # keep the SF-63-1 gate below checks.
         session_keep_bare: str | None = None
+        # amendment 19 D-2: refuse a BLANK role BEFORE the session-keep mint (#97 — a rejected
+        # register has no side effect), through the registry's own refusal over lorerunes.is_blank.
+        from loremaster.agents import AgentRegistry  # noqa: PLC0415 - house lazy-import idiom
+
+        AgentRegistry._refuse_an_invalid_identity(name=agent, session=session, role=role)  # noqa: SLF001
         if principal is not None:
             principal_bare = str(principal.id).split(":", 1)[-1]
             keep_store = self._keep_store
```

### A.2 Mutation driver (declared sets written before the run)
```bash
#!/bin/bash
# contract-63c-i-a-a19 mutation drivers — declared RED sets written BEFORE any run (ids from --collect-only).
cd "$(dirname "$0")/../ref-tree" || exit 9
M=loremaster/tests/test_fixwave_a19_63c_i_a.py
G=loremaster/tests/test_agent_governance_63c_i_a.py
R=loremaster/tests/test_agent_registry.py
F=$M; TA="$G::TestAgentMigrateScopeKeyed63cIA"; TS="$G::TestTheBackfillShapeAssertNormalisesSpellingNeverWidens63cIA"
TB="$R::TestQ3RegisterValidatesIdentityBeforeStoreIO63cIA::test_the_blank_role_rule_is_the_SHARED_is_blank"
CMD=(-- uv run pytest -q -p no:cacheprovider -n 8 "$M" "$TA" "$TS" "$TB")
P=loremaster/loremaster/principals.py; A=loremaster/loremaster/agents.py; V=loremaster/loremaster/server.py
MP="$M::TestTheMultiPrincipalRefusalIsAStoreFactAt63cIAa19"; MO="$M::TestTheMessageOrderGuardIsScopeKeyed63cIAa19"
MS="$M::TestThePreconditionIsSHAREDByMutation63cIAa19"; MC="$M::TestTheRefusalRendersStoredIdsThroughTheSanitiser63cIAa19"
MB="$M::TestABlankRoleRegisterHasNoSideEffect63cIAa19"; MF="$M::TestTheIdentityRuleHasOneSpelling63cIAa19"
RQ="$TA::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent"
proof() { name=$1; shift; echo "=================== $name"; uv run python scripts/mutation_proof.py "$@"; echo "RC[$name]=$?"; }

proof M1-private-verb-level-copy --file $P --anchor-file ../mut/private_verb_anchor.txt --replacement-file ../mut/private_verb.txt \
  --expect-red "$MS::test_the_VERB_LEVEL_check_reads_the_shared_function[agent]" --expect-red "$MS::test_the_VERB_LEVEL_check_reads_the_shared_function[memory]" \
  --expect-red "$MS::test_the_VERB_LEVEL_check_reads_the_shared_function[message]" --expect-red "$MS::test_the_VERB_LEVEL_check_reads_the_shared_function[brief]" "${CMD[@]}"

proof M2-private-order-guard --file $P --anchor '    unmigrated_agents = (await _agent_migration_preconditions(store)).unscoped_count' \
  --replacement '    unmigrated_agents = await _scope_count(store, AGENT_TABLE, none=True)' \
  --expect-red "$MS::test_the_ORDER_GUARD_reads_the_shared_function" "${CMD[@]}"

proof M3-verb-check-keyed-on-unscoped-alone --file $P --anchor '    if preconditions.owned_unscoped:' \
  --replacement '    if preconditions.owned_unscoped or preconditions.unscoped_count:' \
  --expect-red "$MO::test_PRESERVED_a_legacy_unscoped_agent_refuses_the_message_leg_until_the_agent_leg_runs" \
  --expect-red "$MO::test_PRESERVED_a_single_principal_legacy_store_is_never_refused_as_multi_principal[memory]" \
  --expect-red "$MO::test_PRESERVED_a_single_principal_legacy_store_is_never_refused_as_multi_principal[brief]" \
  --expect-red "$TA::test_a_store_with_governed_and_legacy_agents_migrates_only_the_legacy" \
  --expect-red "$TA::test_R_Q5_1_CONTROL_a_clean_store_backfills_every_none_scope_row" \
  --expect-red "$TA::test_R_Q5_2_report_unmigrated_counts_none_scope_before_and_zero_after" \
  --expect-red "$TA::test_R_Q5_3_every_migrated_row_reads_back_the_three_column_stamp" \
  --expect-red "$TA::test_the_migrate_exempt_token_carries_the_EXECUTED_three_column_statement" \
  --expect-red "$TA::test_the_migrate_is_idempotent" "${CMD[@]}"

proof M4-gloss-restated --file $A --anchor '                    f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern}; nothing was "' \
  --replacement '                    f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern} (lowercase letters, digits, _ or -); nothing was "' \
  --expect-red "$MF::test_both_refusals_serve_the_SAME_rule_and_it_is_the_pattern" --expect-red "$MF::test_the_served_rule_MOVES_with_the_shared_pattern" "${CMD[@]}"

proof M5-server-second-spelling --file $V --anchor '                            "{label} must match {pattern} — names must stay in "' \
  --replacement '                            "{label} does not match {pattern} — names must stay in "' \
  --expect-red "$MF::test_both_refusals_serve_the_SAME_rule_and_it_is_the_pattern" --expect-red "$MF::test_the_served_rule_MOVES_with_the_shared_pattern" "${CMD[@]}"

proof M6-raw-id-render-CA1 --file $P --anchor '    shown_ids = [sanitise_line(str(row_id)) for row_id, _owner in preconditions.owned_unscoped][' \
  --replacement '    shown_ids = [str(row_id) for row_id, _owner in preconditions.owned_unscoped][' \
  --expect-red "$MC::test_a_hostile_stored_id_cannot_forge_a_line_in_the_refusal[agent]" --expect-red "$MC::test_a_hostile_stored_id_cannot_forge_a_line_in_the_refusal[memory]" \
  --expect-red "$MC::test_a_hostile_stored_id_cannot_forge_a_line_in_the_refusal[message]" --expect-red "$MC::test_a_hostile_stored_id_cannot_forge_a_line_in_the_refusal[brief]" \
  --expect-red "$MC::test_the_id_render_ROUTES_through_the_shared_sanitise_line" "${CMD[@]}"

proof M7-hand-rolled-sanitiser --file $P --anchor '    shown_ids = [sanitise_line(str(row_id)) for row_id, _owner in preconditions.owned_unscoped][' \
  --replacement '    shown_ids = [str(row_id).replace("\n", " ") for row_id, _owner in preconditions.owned_unscoped][' \
  --expect-red "$MC::test_the_id_render_ROUTES_through_the_shared_sanitise_line" "${CMD[@]}"

proof M8-handler-private-blank-check --file $V --anchor '        AgentRegistry._refuse_an_invalid_identity(name=agent, session=session, role=role)  # noqa: SLF001' \
  --replacement '        if not role.strip():
            raise AgentRegistryError("agent role must not be blank")' \
  --expect-red "$TB[handler]" "${CMD[@]}"

proof M9-handler-check-absent-CAB --file $V --anchor '        AgentRegistry._refuse_an_invalid_identity(name=agent, session=session, role=role)  # noqa: SLF001' \
  --replacement '        _ = AgentRegistry' \
  --expect-red "$TB[handler]" --expect-red "$MB::test_a_blank_role_credentialed_register_mints_no_keep_and_denies_no_third_party[]" \
  --expect-red "$MB::test_a_blank_role_credentialed_register_mints_no_keep_and_denies_no_third_party[   ]" \
  --expect-red "$MB::test_a_blank_role_credentialed_register_mints_no_keep_and_denies_no_third_party[\t\n]" "${CMD[@]}"

proof M10-F1-fixed-phrase --file $P --anchor '    parts = [f"{offending_count} agent row(s) carry an owner but no scope."]' \
  --replacement '    parts = [f"{offending_count} agent row(s) carry an owner but no scope — a multi-principal or half-applied store (§2.1)."]' \
  --expect-red "$RQ[below-cap]" --expect-red "$RQ[at-cap]" --expect-red "$RQ[above-cap]" --expect-red "$RQ[perturbed-bound]" \
  --expect-red "$RQ[operator-owned]" --expect-red "$RQ[mixed-owners]" "${CMD[@]}"

proof M11-F1-operator-not-derived --file $P --anchor '    operator_bare = None if operator is None else (operator.id.partition(":")[2] or operator.id)' \
  --replacement '    operator_bare = None' \
  --expect-red "$RQ[operator-owned]" --expect-red "$RQ[mixed-owners]" "${CMD[@]}"

proof M12-F3-conjunct-dropped --file $P --anchor '"owner_agent = id, scope = $scope WHERE scope IS NONE AND owner_principal IS NONE"' \
  --replacement '"owner_agent = id, scope = $scope WHERE scope IS NONE"' \
  --expect-red "$TA::test_the_migrate_exempt_token_carries_the_EXECUTED_three_column_statement" "${CMD[@]}"

proof M13-verb-check-agent-and-message-only --file $P --anchor '    if preconditions.owned_unscoped:' \
  --replacement '    if preconditions.owned_unscoped and table in (AGENT_TABLE, MESSAGE_TABLE):' \
  --expect-red "$MP::test_every_table_refuses_a_multi_principal_store_and_writes_nothing[memory]" \
  --expect-red "$MP::test_every_table_refuses_a_multi_principal_store_and_writes_nothing[brief]" \
  --expect-red "$MP::test_all_four_tables_serve_the_SAME_teaching" \
  --expect-red "$MS::test_the_VERB_LEVEL_check_reads_the_shared_function[memory]" --expect-red "$MS::test_the_VERB_LEVEL_check_reads_the_shared_function[brief]" \
  --expect-red "$MC::test_a_hostile_stored_id_cannot_forge_a_line_in_the_refusal[memory]" --expect-red "$MC::test_a_hostile_stored_id_cannot_forge_a_line_in_the_refusal[brief]" "${CMD[@]}"

# --- ../mut/private_verb_anchor.txt
    preconditions = await _agent_migration_preconditions(store)
# --- ../mut/private_verb.txt (M1 replacement)
    async def _private_copy(handle: StoreHandle) -> AgentMigrationPreconditions:
        rows = await run_query(
            acquire=handle.acquire, drop=handle.drop, url=handle.url, noun="private copy",
            label="private.rejected",
            statement=f"SELECT id, owner_principal FROM {AGENT_TABLE} WHERE scope IS NONE AND owner_principal IS NOT NONE",
            params={}, logger=logger,
        )
        return AgentMigrationPreconditions(
            unscoped_count=0, owned_unscoped=[(row["id"], row["owner_principal"]) for row in (rows or [])]
        )

    preconditions = await _private_copy(store)
```
M8's corrected replacement (the re-run):
```
        if not role.strip():
            from loremaster.agents import AgentRegistryError  # private copy of the blank decision
            raise AgentRegistryError("agent role must not be blank")
```

### A.3 SAT runner + watchdog
```bash
#!/bin/bash
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/7ad40962-1d69-4104-97ad-8a7ae5a02d44/scratchpad
cd $S/ref-tree || exit 9
uv run pytest -n 12 -q -p no:cacheprovider > $S/sat-full.log 2>&1 &
PID=$!
$S/watchdog.sh $PID $S/watchdog.log &
wait $PID; echo "EXIT=$?" >> $S/sat-full.log

# --- watchdog.sh
#!/bin/bash
# kills the SAT pytest (by PID, and its children) if MemAvailable drops below 15 GB; polls every 10 s
P=$1; LOG=$2
while kill -0 "$P" 2>/dev/null; do
  AV=$(free -g | awk 'NR==2{print $7}')
  if [ "$AV" -lt 15 ]; then echo "WATCHDOG FIRED avail=${AV}G at $(date -Is)" >> "$LOG"; pkill -TERM -P "$P"; kill -TERM "$P"; exit 1; fi
  sleep 10
done
echo "watchdog: pytest $P exited; never fired" >> "$LOG"
```
