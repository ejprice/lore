# REPORT-adversary-63c-i-a — contract-adversary pass on the 63c-i-a agent DATA-layer contract

brief-base v16 read · brief project v7 read

## SUMMARY BLOCK

- **state:** done · **VERDICT: CONTRACT INSUFFICIENT** (measured 2026-09-24 against `0b8ce37`)
- **Graded:** `0b8ce37` · HEAD-at-report: `d0c9946` · DIFFERENT (2 ahead). `f04916d` changes only `.claude/agents/`. `d0c9946` adds only `docs/plans/v2/receipts/2026-09-24-lore-cold-boot/`. No test or production symbol my verdict rests on moved.
- **P1 headline: 11 wrong builds SURVIVE the contract** (their failure set matches the correct build's, byte for byte). Each one has a kill-pin proven RED on the wrong build and GREEN on the reference (§3). **The contract is also UNSATISFIABLE:** on a correct, lint- and type-clean build the full suite reads **8 failed / 11254 passed**, and all 8 are contract defects: 2 missed corpses, 1 broken leg, 3 unadjudicated pre-existing pins (§2).
- **deviations:** none. Report written at the repo root (brief-named). Nothing committed. No edits to the main checkout except this file.
- **Capability check:** everything demanded was reachable. One demand is FALSE: the brief says grep is fine in scratch copies, but the PreToolUse hook refuses grep there too, because it matches the path slug. I fell back to awk/find (said so), and filed this as finding **#473**.
- **Packages considered:** `re` (stdlib) via the existing `AGENT_NAME_PATTERN`: REUSE. `lorerunes.is_blank`: REUSE (source read at `lorerunes/lorerunes/blankness.py::is_blank`). pydantic `StringConstraints(pattern=)`: rejected, because it would create a SECOND spelling of the pattern (pydantic-core Rust regex, different `$` semantics; read `_validate_comms_charset` §#210). SurrealQL single-statement UPDATE: the engine itself, not a library. No `bespoke` verdicts. This diffs clean against the author's "none — no new mechanism" (§8).
- **Odoo-20 portability:** n/a (not an Odoo repo).
- **Reuse ledger:** none. I introduced no production symbols. My scratch instruments are pasted verbatim in §A.
- **decisions-needed (lead):** (1) **ORPHAN risk.** F5 write attribution for agent writers (§2.2 `write_guard("register")`, the CREATE-OWNS-IT allowlist entry, heartbeat) is named in neither the i-a nor the i-b list. (2) Is `briefed` (agent→brief) a governed population once `agent` is? The derivation's rule says yes, but its resolver cannot see the endpoint (MP-10). (3) What is the `register` seam for the session scope? A pre-existing pin bans the NAME `scope`, and the fake lacks the kwarg (MP-12). (4) Should the registry enforce owner ⇒ scope, so that the §6 "impossible" claim holds by construction (R5)?
- **Receipt pointers:** §1 RED reproduction · §2 satisfiability · §3 wrong builds + kill-pins · §4 P1b table · §5 P1c table · §6 mutation proofs · §7 DUAL/P6/P6b · §8 P-PKG · §9 MISSING PINS · §10 residuals · §A instruments (verbatim).

---

## 1. P7 — RED honesty (reproduced)

Scratch copy `…/scratchpad/ref` via `./scripts/scratch_copy.sh`. Provenance: `loremaster.__file__` = `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/2e70e163-b2d4-4ee6-9367-72203a3e11ec/scratchpad/ref/loremaster/loremaster/__init__.py`.
At `f04916d` (the contract tree), `pytest -n 12` over the 5 contract files gives **`38 failed, 433 passed in 47.84s`**. That reproduces the lead's re-measure exactly.

**One of the 38 is RED for the WRONG reason.** `TestAgentHeartbeatOnALegacyRoleRow63cIA::test_a_touch_succeeds_on_a_role_empty_legacy_row_after_the_drop` seeds `row_id="role_empty"`. `AgentRegistry.touch(name, session=)` resolves the deterministic `uuid5(session, name)` id, so the call raises `UnknownAgentError: agent 'legacy-agent' is not registered` before any UPDATE. The broad `except Exception` then relabels this as *"RED-at-HEAD (right reason): … the role non-empty ASSERT is STILL on the store"*. The failure message promises a check the test never performs (CLAUDE.md's "false gate" class). See MP-2.

## 2. SATISFIABILITY RECEIPT — the contract cannot go 0-failed on a correct build

The reference build is `ref_build.py` (§A.1) plus the ref2 delta (§A.2). ref2 differs only in naming the stamp kwarg `session_scope` and passing it only when a session keep exists (see MP-12 for why).
- **Contract files (5):** on `adv-ref`, `5 failed, 466 passed`.
- **Full suite, alone, `-n 12`:** on `adv-ref2` (`d968732` in scratch), **`8 failed, 11254 passed, 62 skipped, 3 xfailed in 607.29s`**.
- **After the lint-demanded cleanup** (the orphaned `_AGENT_OWNER_PRINCIPAL_INDEX_FIELDS` is deleted): `uv run ruff check .` gives "All checks passed!". `./scripts/typecheck.sh` gives OK on lorescribe/loresigil/loremaster/skills/docs-eval/scripts plus shellcheck.

The 8 failures, each with its cause:

| failing pin | cause | fate owed by the CONTRACT |
|---|---|---|
| `test_comms_schema.py::TestAgentRoleNonEmptyAssert::test_empty_role_is_rejected` + `test_whitespace_only_role_is_rejected[ ]`/`[   ]`/`[\t]` (4) | Missed corpse: asserts the STORE rejects a blank role under `generate_agent_ddl()`. Q3 drops that ASSERT. The DUAL deleted `TestAgentCharsetAssert` but missed this sibling. | DELETE-WITH-REPLACEMENT (Leg A[role] + the MOVE blank-role pins carry the virtue) — MP-1 |
| `test_agent_governance_63c_i_a.py::TestAgentHeartbeatOnALegacyRoleRow63cIA::…` (1) | seed id ≠ `uuid5` → `UnknownAgentError` on EVERY build | fix the seed id — MP-2 |
| `test_memory_enforcement_63b_ia.py::TestTheGovernedPopulationSetIsADerivedOutput::test_the_derived_population_set_is_the_known_set` + `test_message_enforcement_63b_ii_a.py::TestTheGovernedPopulationSetGrows::test_the_derived_population_set_grows_to_memory_message_to` (2) | exact-set pins `== {memory, message, to}`; W1-1 makes `agent` a `_governed_field_specs` caller → derived set is `{agent, memory, message, to}` on every correct build | update both + adjudicate `briefed` — MP-3 / MP-10 |
| `test_message_migrate_63b_ii_a.py::TestMigrateAgentOwner::test_agent_migrate_backfills_only_none_owner_agents_to_the_operator` (1) | pkt-62 owner-keyed world: registers `ag_owned` WITH an owner and NO scope → §6's row precondition REFUSES (reference reason: `1 agent row(s) carry an owner but no scope (agent:efa8…) …`) | invert to the scope key — its ∀-mix virtue is exactly MP-6 |

The first reference build (`adv-ref`, kwarg named `scope`, always passed) also reddened 87 more pins:
- `test_agent_capability.py::…::test_register_exposes_no_display_owner_argument` (a forbidden-NAME list `{"owner","as_agent","created_by","scope"}`)
- every fake-driven register in `test_comms_tool.py` / `test_comms_render_architecture.py` (`TypeError: FakeAgentRegistry.register() got an unexpected keyword argument 'scope'`).

A builder can only avoid these by renaming the kwarg to dodge a forbidden-name gate, or by editing test fakes. The contract names neither: MP-12.

No UNRELATED failures in either full run. Neither run reproduced the author's 3 "flaky" failures (`TestFailedRebuildReportsFailed`, `TestRenderInjectionRegistry` params); both passed inside the 11254.

## 3. P1 — wrong builds (the headline)

**Method.**
- Wrong builds are applied ON TOP of the reference build in a second scratch copy (`…/scratchpad/wb`, provenance `…/scratchpad/wb/loremaster/loremaster/__init__.py`), by `wrong_builds.py` (§A.3, exactly-once anchors).
- Each build runs the 5 contract files (`run_wbs.sh`, §A.4).
- **Baseline:** the correct build fails exactly the same 5 contract defects (MP-1 ×4, MP-2). A wrong build SURVIVES iff its failure set is that identical 5.
- **Kill-pins:** in `test_adv_killpins_63c_i_a.py` (§A.5). Each is proven with the pair: GREEN on `adv-ref` (final run **12 passed**) and RED on exactly its wrong build.

| WB | wrong build (plausible door) | contract result | kill-pin RED on it (GREEN on ref) |
|---|---|---|---|
| **WB1** | W1-1 twin: keeps the pkt-62 `owner_principal` row in `_AGENT_FIELD_SPECS` + the inline `agent_owner_principal` index; calls the emitter but skips already-declared columns and dedupes statements | **SURVIVES** (5 failed, 466 passed) | `test_KP_W1_every_governed_column_and_index_moves_with_the_shared_emitter` |
| **WB2** | Q5 backfill loses its `WHERE` → re-stamps ALREADY-governed agents (session-keep scope → project keep, member owner → operator) | **SURVIVES** | `test_KP_Q5_a_store_with_governed_and_legacy_agents_migrates_only_the_legacy` |
| **WB3** | row precondition keyed on `owner_principal IS NOT NONE` only (drops `scope IS NONE`) → refuses every production cutover once any post-63c agent exists | **SURVIVES** | same mixed-store pin |
| **WB4** | register stamps `scope = sorted(visible_keeps)[0]` instead of THE session keep | **SURVIVES** | `test_KP_register_scope_is_THE_session_keep_across_two_sessions` |
| **WB5** | MOVE refusal text `"invalid input"` (no field, no rule, no remedy) | **SURVIVES** | `test_KP_move_refusal_names_the_field_and_the_rule[name/session/role]` |
| **WB6** | wired `AppContext` never calls `agent_registry.ensure_ready()` | KILLED (30 failed over the 5 files — the contract's re-register pin + wiring pins; the printed tail listed 24 of them) | — |
| **WB7** | per-row-resilient backfill (skips violators, never loud) | KILLED (`test_C_CONTROL_…_RAISE`, `test_a_legacy_junk_status_row_refuses_the_real_migrate`) | — |
| **WB8** | row-precondition refusal names the count but NOT the rows (ids) the ruling §6 says it names | **SURVIVES** | `test_KP_row_precondition_refusal_names_the_offending_row_id` |
| **WB9** | refusal reason never states the count (`\b1\b` is satisfied by the "§2.1" citation) | **SURVIVES** | `test_KP_row_precondition_refusal_is_byte_inert_and_counts_two` |
| **WB10** | STAMPS owners on NONE-owner rows first (the old leg's statement), THEN runs the precondition and refuses — a refusal that mutated the store | **SURVIVES** (R-Q5-1 observes only `scope` — a proxy) | same byte-inert pin |
| **WB11** | MOVE uses `AGENT_NAME_PATTERN.match` → accepts `"fixer-b\n"` (finding #210's class, now reachable by any registry caller since the store ASSERT that used to backstop it is gone) | **SURVIVES** | `test_KP_move_refuses_a_trailing_newline_identifier[name/session]` |
| **WB12** | register stamps the session scope only for the KEEPER's agents; a householded joiner's agent stays NONE-scope | **SURVIVES** | `test_KP_a_joined_members_agent_is_stamped_with_the_shared_session_keep` |
| **WB13** | blank-role check is a private `role.strip()` — not the shared `lorerunes.is_blank` (ROUTING-IS-NOT-SHARING) | **SURVIVES** | `test_KP_register_blank_role_routes_through_the_shared_is_blank` |

Receipts (from `wb_results.log` + the kill-pin runs):
- Every surviving row printed `5 failed, 466 passed`. Wherever the tail printed ids (WB1–WB5, WB8–WB11), they were the identical 5 (MP-1 ×4 + MP-2). For WB12/WB13 only the count line was captured.
- Kill-pin runs: `== killpins on REF` gave `12 passed in 8.14s`.
- Each named WB gave `1 failed` (WB5 `3 failed`; WB11 `2 failed`), and only its own pin.

## 4. P1b — QUANTIFIER TABLE (every invariant, ∀ vs guarded)

| # | invariant (ruling §) | pinned as | verdict · receipt |
|---|---|---|---|
| I1 | no agent field carries a store constraint except `status` (§4.3 P2) | ∀ fields DERIVED from the real emitter; floor non-vacuity | **SAFE**. M1 + M2 mutation proofs held (§6). The OVERWRITE-only derivation's IF-NOT-EXISTS blind spot is closed by composition with `test_surreal_schema.py::…every_define_statement_carries_the_guard_its_kind_requires`, which registers `generate_agent_ddl`. |
| I2 | `status` vocabulary aligned across DDL/`AGENT_STATUSES`/`Literal` (§4.3 P-A2) | ∀ three surfaces | **SAFE**. M3: only P-A2 fired (my declared set also named `test_status_domain_is_exactly…`, which stayed green because it reads the same tuple; my misprediction, recorded). |
| I3 | the three governed columns + two indexes come ONLY from the shared emitter (§2.1 W1-1) | guarded: "a probe APPENDED to the emitter appears" + count-once | **MISSING**. WB1 walks through the filter/dedupe door. Kill-pin MP-5. |
| I4 | register stamps scope = THE session keep ∀ sessions, ∀ registrants (keeper or joiner) (§2.2) | one principal, one session, keeper path | **MISSING**. WB4 and WB12. MP-8. |
| I5 | re-register is mint-once (§2.2 row 2) | concrete values after both calls | SAFE for its door. The mint-once test's concrete-value assertion is sound. |
| I6 | the backfill stamps ∀ NONE-scope rows incl. legacy violators (§4.4 Leg B / §6) | ∀ over a legacy-only population | SAFE for legacy-only. WB7 was killed. |
| I7 | the backfill touches ONLY NONE-scope rows (∀ scoped rows untouched — the old leg's "∀ NONE-owner, never a re-stamp", carried to the scope key) | **unpinned** (no fixture holds a scoped row) | **MISSING**. WB2. MP-6. |
| I8 | refuse iff ∃ row (scope NONE ∧ owner NOT NONE) (§6 / #470) | guarded: trap-row refuses + clean store migrates | **MISSING**. WB3 (owner-only predicate) survives: no fixture carries owner ∧ scope. MP-6. |
| I9 | a refused migrate writes NOTHING (§6 "REFUSE … ZERO rows stamped") | observed via `scope` only | **MISSING**. WB10 (proxy observation). MP-7. |
| I10 | the refusal names the count AND the rows (§6) | `\b1\b` | **MISSING**. WB8 and WB9. MP-7 / MP-11. |
| I11 | idempotent (§6) | legacy-only second run | SAFE for its door (early-return + WHERE both satisfy it). |
| I12 | ONE loud statement, never per-row-resilient (§4.5) | P-A3 + C-control | **SAFE**. WB7 was killed. |
| I13 | the three dropped ASSERTs land on a dirty store (§4.4 Leg A) | ∀ three, parametrised | **SAFE**. M1 held (Leg A[role] fired). |
| I14 | legacy violators survive ∀ agent WRITERS: backfill / touch / re-register UPDATE | backfill ✓; touch **BROKEN** (MP-2); re-register UPDATE unreachable for violators after the MOVE (by construction: the MOVE refuses the hostile name / blank role first, and a differing role raises `AgentIdentityConflictError` before the UPDATE) | **MISSING** on touch. MP-2. |
| I15 | the MOVE refuses ∀ hostile identifiers (§4.2) | a LOCAL 7-shape hand-list (`_MOVE_HOSTILE_IDENTIFIERS`), narrower than the shared 12-shape `_HOSTILE_IDENTIFIERS` its deleted predecessor used | **MISSING**. WB11 (trailing newline). MP-9. |
| I16 | the MOVE refusal TEACHES (field + rule + remedy) (§4.2, §8 "TEACHING") | only "not `(assert violation)`" | **MISSING**. WB5. MP-9. |
| I17 | the MOVE shares `AGENT_NAME_PATTERN` AND `is_blank` by mutation (§4.2, ONE IMPLEMENTATION) | pattern: mutation ✓; `is_blank`: none | **MISSING** for `is_blank`. WB13. MP-9. |
| I18 | the wired AppContext applies the agent DDL (virtue of the deleted wiring pin) | other wiring pins | **SAFE**. WB6 was killed by 30 pins. |

## 5. P1c — REACH TABLE (every instrument introduced or relied on)

| instrument | reach: derived vs hand-list | coverage checked? | effect vs proxy | one-source by mutation | verdict · leg |
|---|---|---|---|---|---|
| P2 `[agent]` ∀-no-constraint | DERIVED (real emitter's OVERWRITE FIELD statements); birth set = hand constant, git-derived | YES (floor non-vacuity; exemption non-vacuity) | static DDL text, paired with live Leg A/B | YES (M1, M2) | SAFE · empirical |
| W1-1 routing pins | mutation is APPEND-ONLY; the twin detector is a COUNT | NO: a count is defeated by filter/dedupe | proxy (presence of an appended probe) | **NO**: WB1 routes to the emitter while a private owner_principal row + index survive | **MISSING PIN (MP-5)** · empirical |
| P-A2 status alignment | DERIVED (parses the emitted ASSERT) | YES (parsed-set non-empty) | effect (the emitted set) | YES (M3) | SAFE · empirical |
| Leg A / Leg B / P-A3 dirty-store legs | 3 dropped ASSERTs parametrised; old world = a hand-captured MINIMAL DDL (6 of the 16 agent columns + overlay) | YES (frozen-capture literal control; BASELINE rejections; clean-lands control; C-control) | effect (live engine) | n/a | SAFE for this wave's change set; residual R1 · empirical (M1/M2) |
| heartbeat leg (touch writer) | one violator shape (`role=""`) | **NO**: never reaches the UPDATE (id mismatch) | **PROXY**: any exception reads as "right reason" | n/a | **MISSING PIN (MP-2)** · empirical: corrected leg → base `(assert violation)`, ref `1 passed` |
| R-Q5-1 row precondition | legacy + trap only | NO (no governed-row population) | **PROXY**: observes `scope`, not the rows | n/a | **MISSING PIN (MP-6/MP-7)** · empirical (WB3/WB9/WB10) |
| MOVE hostile matrix | LOCAL hand-list of 7, a narrowed second copy of the shared 12-shape corpus | NO | effect | pattern YES / `is_blank` NO | **MISSING PIN (MP-9)** · empirical (WB11/WB13) |
| `governed_populations()` (relied on; F5 population set) | "DERIVED" by AST, but `_schema_string_constants` only sees module-level `NAME = "literal"` assigns. `AGENT_TABLE`/`PRINCIPAL_TABLE` are re-exported imports (`from lorerunes import AGENT_TABLE as AGENT_TABLE`) and resolve to **None** | NO: a relation whose endpoint is a re-export can never join | effect | n/a | **MISSING PIN (MP-10)** · empirical: resolver printout `['briefed', None, 'brief']`, `['to', 'message', None]`, `['member_of', None, 'keep']`; the derived set on the reference is `['agent','memory','message','to']` (no `briefed`) |
| `test_agent_capability` display-owner pin (relied on) | a FORBIDDEN-NAME list `{"owner","as_agent","created_by","scope"}` | NO (enumerates the forbidden; a rename walks past it) | proxy (parameter names, not provenance) | n/a | construction-inspection: the instrument-lesson antipattern. It blocks the natural seam and admits any rename (MP-12) |

Legs run empirically: P2, W1-1, P-A2, Leg A/B/P-A3 (M1/M2), heartbeat, R-Q5-1, MOVE matrix, population derivation. Construction-inspection only: the display-owner pin.

## 6. P4 — the author's mutation claims, reproduced with `scripts/mutation_proof.py`

Declared RED sets were taken from `--collect-only` and written down BEFORE each run. Command scope: `TestAgentDdlOffline` + the P2 class + the governance file, with the broken heartbeat leg deselected.
- **M1** re-add the `role` ASSERT → `PROOF HELD` {P2[agent], LegA drop[role], LegB survives}; `M1 exit=0`; tree restored byte-exact (md5 `1e1f94c6…`).
- **M2** drop the `status` ASSERT → `PROOF HELD` {status_domain, KEPT, aligns, P2[agent], status-STAYS, P-A3}; `M2 exit=0`.
- **M3** add `"paused"` to the DDL status tuple only → observed {aligns}; `M3 exit=4`. I had also declared `status_domain…`, which stayed green because it compares against the same tuple. This was my misprediction. P-A2 is the sole vocabulary-drift discriminator, and it works.

## 7. P6 / P6b / DUAL — corpse sweep and orphaned-virtue diff

**My independent enumeration came first** (written to scratch before I opened the author's report). Agent-table writers at HEAD (awk sweep, grep hook-blocked):
- register CREATE
- register re-register UPDATE
- touch UPDATE
- `_migrate_agent_owner` UPDATE

Removed or replaced behaviours:
- A. the hand-rolled owner_principal row + index
- B. the name/session charset + role non-empty ASSERTs, which rejected hostile values on CREATE **and on every UPDATE** of such a row
- C1. operator resolution runs first; ambiguity → refused, with a reason naming the principal/admin counts
- C2. an ambiguous operator refuses even when there is nothing to migrate
- C3. unmigrated==0 → not refused, `already_migrated` counted
- C4. **already-owned rows untouched (∀ NONE-owner, never a re-stamp)**
- C5. named exempt frame + `governed.agent_backfill.rejected` label
- C6. `backfilled` = the PRE-count
- C7. operator id partitioned into a `type::record` link
- C8. the old leg minted no project keep
- D. the wired AppContext runs `agent_registry.ensure_ready()` (the virtue of the deleted wiring pin)

**Diff against the author's §DUAL:**
- **C4 is ORPHANED.** The author adjudicated item 9 as "OLD-BUG-NOT-RE-PINNED (F10)". But F10's bug is the missing ROW precondition, not C4. C4's ∀-scoped-rows-untouched virtue has NO pin in the new world, and the one pre-existing pin carrying it (`TestMigrateAgentOwner`) is now a RED corpse (§2). → MP-4 + MP-6 (WB2 proves the gap).
- **D:** the author claims the brief leg "carries the schema-applied proof". That leg proves the BRIEF ledger's DDL, not the agent registry's. **Empirically the virtue survives anyway.** WB6 was killed (30 failures across the contract + wiring files, incl. the contract's re-register pin). Verdict: carried, but by pins other than the one cited.
- **B:** the MOVE carries CREATE-time rejection. UPDATE-time rejection is moot, because no writer changes name/session/role after birth. The deleted `TestAgentCharsetAssert` covered 12 hostile shapes (incl. embedded newline, quotes, backslash, leading `_`, whitespace-only). The MOVE pins cover 7 and omit all of those. → MP-9.
- **C1/C2/C3/C5–C8:** C1 is preserved by the reference (operator resolved first), but **unpinned in this contract** (pre-existing 63b-ii-a ambiguity pins may carry it; not re-verified, because i-a changes the leg's body). C2–C8 are unpinned. They are low-consequence and listed in R8.

**The three DELETED/INVERTED corpse pins (author §DUAL), one by one:**
1. agent charset/role DDL-text pins → replacement P2[agent]. **Virtue carried** (M1).
2. `TestAgentCharsetAssert` → replacement Leg A + MOVE. **Partially carried**: 12 → 7 shapes, trailing newline never covered (WB11).
3. wiring agent leg → the cited replacement is wrong, but the virtue is carried elsewhere (WB6 killed).

**Missed corpses (P6):** `TestAgentRoleNonEmptyAssert` (4 pins) · `TestMigrateAgentOwner` (1) · the two population-set exact pins (2). All four are RED on every correct build.

**ORPHANED-rider check across the i-a/i-b split:**
- (a) §2.2's F5 write attribution for the agent writers (`write_guard("register")`, the CREATE-OWNS-IT allowlist entry, the heartbeat allowlist) appears in neither list. `agent_case()` leaves `write_verbs` empty with the comment "i-b", but i-b's scope (#467, read_filter, EXPLAIN-A, β, flips, P5) does not name it. **POTENTIALLY ORPHANED. Lead to assign.**
- (b) The population-set pin update is named nowhere, yet it reddens IN i-a. It must be i-a.
- (c) §4.4's heartbeat POSITIVE CONTROL (a junk-status `touch` refused by the engine) is in i-a scope and was dropped.

## 8. P-PKG — own table, then diff

| mechanism | candidate(s) | what I READ | verdict |
|---|---|---|---|
| identifier charset in `register` | `re` via `agents.AGENT_NAME_PATTERN` · pydantic `StringConstraints(pattern=)` | `server._validate_comms_charset` docstring (fullmatch rationale, #210; fence-not-repr for echoed values); `AGENT_NAME_PATTERN` at `agents.py` | REUSE the pattern object. pydantic rejected: a second spelling of the pattern string, with a different regex engine |
| blankness | `lorerunes.is_blank` | `lorerunes/lorerunes/blankness.py::is_blank` source (`not value or not value.strip()`, str.isspace semantics) | REUSE. **The contract never proves the reuse** (WB13) |
| scope-keyed backfill + precondition | SurrealQL (engine) | store-ref §1.4, §3; `_migrate_memory_scope` precedent | engine-native, no library |
| DDL emission | house `_define_field`/`_governed_*` | `surreal_schema.py` | house seam |

Diff vs the author's "Packages considered: none — no new mechanism": **no disagreement on packages.** The only gap is the *proof* of the in-house reuse (WB13).

## 9. MISSING PINS (each: ruling § · the wrong build that passes · its receipt · the pin that kills it)

1. **MP-1 (BLOCKER, satisfiability)** · §9 item 6 · every correct build · §2 row 1 · Delete `TestAgentRoleNonEmptyAssert` with a DUAL comment. Its virtue is carried by `TestTheAgentAssertsDropFromADirtyStore63cIA[role]` + `test_register_refuses_a_blank_role_before_any_store_write`.
2. **MP-2 (BLOCKER, satisfiability + false gate)** · §4.4 heartbeat leg · every build · §1 · Seed `row_id=AgentRegistry._agent_id("wave7", "legacy-agent")`. Proven: base → `(assert violation)`, ref → `1 passed`. Narrow the `except` so the RED text asserts the engine refusal. ADD the ruling's dropped positive control: a junk-`status` row seeded under a downgraded DDL, then the real `touch` → raises matching `\(assert violation\)`.
3. **MP-3 (BLOCKER, satisfiability)** · §2.1 W1-1 consequence · every correct build · §2 row 3 · Update both exact-set pins to the grown set, deciding `briefed` explicitly (see MP-10). Name the owning wave in the docstring.
4. **MP-4 (BLOCKER, satisfiability)** · §6 / §9 item 9 · every correct build · §2 row 4 · Re-key `TestMigrateAgentOwner` to the post-63c shape: the pre-owned agent carries owner AND scope. Its ∀-mix assertion becomes MP-6.
5. **MP-5 (BLOCKER)** · §2.1 W1-1 · WB1 · §3 · `test_KP_W1_every_governed_column_and_index_moves_with_the_shared_emitter`: REWRITE (not append) every shared field spec + rename every shared index. Every agent governed statement must carry the mutation, and no `agent_owner_principal` index may survive.
6. **MP-6 (BLOCKER)** · §6 + old-leg virtue C4 · WB2, WB3 · §3 · `test_KP_Q5_a_store_with_governed_and_legacy_agents_migrates_only_the_legacy`: 2 governed (member owner + session scope) + 3 legacy rows → not refused, `backfilled == 3`, governed rows byte-identical.
7. **MP-7 (BLOCKER)** · §6 "ZERO rows stamped … naming the count" · WB9, WB10 · §3 · `test_KP_row_precondition_refusal_is_byte_inert_and_counts_two`: TWO trap rows + legacy rows; full `SELECT *` before == after; the reason states `2`.
8. **MP-8** · §2.2 / §2.3 · WB4, WB12 · §3 · `test_KP_register_scope_is_THE_session_keep_across_two_sessions` + `test_KP_a_joined_members_agent_is_stamped_with_the_shared_session_keep`.
9. **MP-9** · §4.2 MOVE · WB5, WB11, WB13 · §3 · Four changes:
   - (a) parametrise the MOVE pins over the SHARED `_HOSTILE_IDENTIFIERS`, and add a trailing-newline shape (`"fixer-b\n"`) to that corpus. One corpus, not a narrower local copy.
   - (b) the refusal names the field, the rule, and the remedy (`test_KP_move_refusal_names_the_field_and_the_rule`).
   - (c) mutation of `loremaster.agents.is_blank` flips `register` (`test_KP_register_blank_role_routes_through_the_shared_is_blank`).
   - (d) optional: the echoed value rides `render_fenced`, never bare or `repr` (Ruling 10 link 4, as `_validate_comms_charset` already does).
10. **MP-10 (P1c)** · the F5 population reach the contract relies on · §5 · Add a synthetic-source growth leg where a relation's endpoint is an IMPORTED re-export (`from lorerunes import AGENT_TABLE as AGENT_TABLE`) → the relation must join. Fix `_schema_string_constants` to resolve re-exports (e.g. import the module and read its attributes, or follow `ImportFrom` into `lorerunes`). **Lead fork:** is `briefed` governed from i-a on?
11. **MP-11** · §6 "naming the count and the rows (ids, bounded)" · WB8 · §3 · `test_KP_row_precondition_refusal_names_the_offending_row_id`.
12. **MP-12 (contract gap / fork)** · §2.2 register stamp seam · a correct build must rename-to-dodge a forbidden-name gate or edit fakes · §2 · The contract must: name the registry parameter carrying the server-derived session scope; extend `_comms_fakes.FakeAgentRegistry.register` with it; and adjudicate `test_register_exposes_no_display_owner_argument` (allowlist the server-derived params instead of forbidding names).

## 10. Residuals (each with an individual verdict)

- **R1** Frozen/unbounded agent DDL model only 6 of the 16 columns. The dirty-store legs are blind to type changes on the other 10. **Accept as a pinned bound** (not in this wave's change set). Re-open trigger: any change to an existing agent column's type.
- **R2** Leg B never runs a second migrate over the violators (ruling: "idempotent on the second call"), and does not read back `owner_agent` on violator rows. **Minor rider drop.** Add both assertions.
- **R3** `LegacyMapping("agent", "OWNED-BY-THE-OPERATOR")` (§6) has no pin. **Rider-less ruling clause.** Unobservable; the lead decides.
- **R4** `_ConstraintSpec.make_ddl` defaults to `generate_message_ddl` (the fixture-default law). A forgotten `make_ddl` fails loud through the non-vacuity check. **Low risk; prefer no default.**
- **R5** The registry API can express owner-without-scope. `_comms_register` never does, but `TestMigrateAgentOwner` shows the shape exists, and §6 calls the half-applied state "impossible". **Fork:** should `register` refuse `owner_principal_id` without the session scope?
- **R6** α interim: in i-a a tokenless register still writes owner NONE / scope NONE, which the cutover backfills to the operator (the fabrication §3.1 describes). This is unchanged from HEAD. **β (i-b) must land before the 65 cutover.**
- **R7** `_IDENTIFIER_CHARSET_PATTERN` remains beside `AGENT_NAME_PATTERN` (lead-ruled → 63c-ii), and no pin binds the two spellings during the gap. **Accepted, named.**
- **R8** Old-leg behaviours C2/C3/C5/C6/C8 are unpinned in the new leg. **Low consequence.** Old-leg C1 (the operator-ambiguity refusal) may be carried by the pre-existing 63b-ii-a pins; not re-verified.
- **R9** The MOVE's "before any store I/O" is observed as zero rows written. A validation placed after the `_select_row` read would pass. **Consistent with the ruling's own "F5 observes zero writes"; minor.**
- **R10** Finding #473 (the grep hook blocks scratch copies). Filed.

## A. Instruments (pasted verbatim — scratch-only, uncommitted per the writable set)

### A.1 `ref_build.py` — the reference (believed-correct) build
```python
"""Reference (believed-correct) 63c-i-a build, applied to a scratch copy by exact-string edits.

Usage: uv run python ref_build.py <scratch-root>
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
edit(AGENTS, "from lorerunes import parse_credential", "from lorerunes import is_blank, parse_credential")
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
    "        owner_principal_id: str | None = None,\n        scope: str | None = None,\n    ) -> AgentRegisterResult:",
)
edit(
    AGENTS,
    "        agent_id = self._agent_id(session, name)\n        existing_row = await self._select_row(agent_id)\n        now = datetime.now(UTC)\n",
    "        for field_name, value in ((\"name\", name), (\"session\", session)):\n"
    "            if not AGENT_NAME_PATTERN.fullmatch(value):\n"
    "                raise InvalidAgentIdentityError(\n"
    "                    f\"agent {field_name} {value!r} is not a legal identifier — it must match \"\n"
    "                    f\"{AGENT_NAME_PATTERN.pattern} (lowercase letters, digits, '_' or '-', 1-64 chars, \"\n"
    "                    \"starting with a letter or digit); nothing was written — register again with a legal \"\n"
    "                    f\"{field_name}\"\n"
    "                )\n"
    "        if is_blank(role):\n"
    "            raise InvalidAgentIdentityError(\n"
    "                \"agent role must be non-blank — nothing was written; register again with a role \"\n"
    "                \"(e.g. 'builder')\"\n"
    "            )\n"
    "        agent_id = self._agent_id(session, name)\n        existing_row = await self._select_row(agent_id)\n        now = datetime.now(UTC)\n",
)
edit(
    AGENTS,
    "                _COL_CAPABILITY_HASH: sha512_hex(capability),\n",
    "                _COL_CAPABILITY_HASH: sha512_hex(capability),\n"
    "                \"owner_agent\": RecordID(AGENT_TABLE, agent_id),\n"
    "                \"scope\": scope,\n",
)

SERVER = "loremaster/loremaster/server.py"
edit(
    SERVER,
    "            cadence=cadence,\n            owner_principal_id=principal_bare,\n        )\n        now = datetime.now(UTC)\n        registered_age_s",
    "            cadence=cadence,\n            owner_principal_id=principal_bare,\n"
    "            scope=(\n"
    "                keep_scope(str(session_keep.id).split(\":\", 1)[-1])\n"
    "                if session_keep is not None\n"
    "                else None\n"
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
    "                \"adjudicate by hand before migrating (§2.1)\"\n"
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
print("reference build applied")
```

### A.2 ref2 delta (`git diff adv-ref adv-ref2` in the scratch copy)
```diff
diff --git a/loremaster/loremaster/agents.py b/loremaster/loremaster/agents.py
index 16596aa..f9fe1e2 100644
--- a/loremaster/loremaster/agents.py
+++ b/loremaster/loremaster/agents.py
@@ -651,7 +651,7 @@ class AgentRegistry:
         task_id: str | None = None,
         cadence: str | None = None,
         owner_principal_id: str | None = None,
-        scope: str | None = None,
+        session_scope: str | None = None,
     ) -> AgentRegisterResult:
         """Idempotently register an agent identity (design doc §1/§2).
 
@@ -744,7 +744,7 @@ class AgentRegistry:
                 ),
                 _COL_CAPABILITY_HASH: sha512_hex(capability),
                 "owner_agent": RecordID(AGENT_TABLE, agent_id),
-                "scope": scope,
+                "scope": session_scope,
                 # SF-2: no clock TTL by default — the lifetime bound is the binding +
                 # no-cache revocation. The OPTIONAL expiry seam starts unset (never).
                 _COL_CAPABILITY_EXPIRES_AT: None,
diff --git a/loremaster/loremaster/server.py b/loremaster/loremaster/server.py
index 6567f5b..ea547d9 100644
--- a/loremaster/loremaster/server.py
+++ b/loremaster/loremaster/server.py
@@ -6739,10 +6739,10 @@ class AppContext:
             task_id=task_id,
             cadence=cadence,
             owner_principal_id=principal_bare,
-            scope=(
-                keep_scope(str(session_keep.id).split(":", 1)[-1])
+            **(
+                {"session_scope": keep_scope(str(session_keep.id).split(":", 1)[-1])}
                 if session_keep is not None
-                else None
+                else {}
             ),
         )
         now = datetime.now(UTC)
```

### A.3 `wrong_builds.py` — WB1…WB13 (applied on top of A.1)
```python
"""Wrong builds applied ON TOP of the reference build (ref_build.py) in a scratch copy.

Usage: uv run --no-project python wrong_builds.py <scratch-root> <WB-id>
Each edit asserts its anchor occurs exactly once (a no-op mutation is a failed setup — #194).
"""

import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
WB = sys.argv[2]


def edit(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: anchor occurs {count} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


SCHEMA = "loremaster/loremaster/store/surreal_schema.py"
PRINCIPALS = "loremaster/loremaster/principals.py"
SERVER = "loremaster/loremaster/server.py"
AGENTS = "loremaster/loremaster/agents.py"

if WB == "WB1":
    # W1-1 twin: keep the pkt-62 hand-rolled owner_principal row + inline index; call the emitter but
    # skip columns the table already declares, and dedupe identical statements.
    edit(SCHEMA, "    # packet 62, Fork 1 / wave 2 (W2.2, W2-R7)",
         '    ("owner_principal", "option<record<principal>>", ""),\n    # packet 62, Fork 1 / wave 2 (W2.2, W2-R7)')
    edit(SCHEMA,
         "    statements += [\n"
         "        _define_field(AGENT_TABLE, name, type_expr, constraint=constraint)\n"
         "        for name, type_expr, constraint in _governed_field_specs()\n"
         "    ]\n"
         "    statements += _governed_index_statements(AGENT_TABLE)\n",
         "    declared = {spec[0] for spec in _AGENT_FIELD_SPECS}\n"
         "    statements += [\n"
         "        _define_field(AGENT_TABLE, name, type_expr, constraint=constraint)\n"
         "        for name, type_expr, constraint in _governed_field_specs()\n"
         "        if name not in declared\n"
         "    ]\n"
         "    statements.append(_plain_index(AGENT_TABLE, f\"{AGENT_TABLE}_owner_principal\", (\"owner_principal\",)))\n"
         "    statements += _governed_index_statements(AGENT_TABLE)\n"
         "    statements = list(dict.fromkeys(statements))\n")
elif WB == "WB2":
    # Q5: the backfill loses its WHERE — every agent row (incl. already-governed ones) is re-stamped.
    edit(PRINCIPALS, "\"owner_agent = id, scope = $scope WHERE scope IS NONE\"", "\"owner_agent = id, scope = $scope\"")
elif WB == "WB3":
    # Q5: the row precondition keyed on owner only (drops the `scope IS NONE` clause).
    edit(PRINCIPALS,
         "f\"SELECT VALUE id FROM {AGENT_TABLE} WHERE scope IS NONE AND owner_principal IS NOT NONE\"",
         "f\"SELECT VALUE id FROM {AGENT_TABLE} WHERE owner_principal IS NOT NONE\"")
elif WB == "WB4":
    # register stamps scope from "a keep the registrant can see" instead of THE session keep.
    edit(SERVER,
         "                keep_scope(str(session_keep.id).split(\":\", 1)[-1])\n"
         "                if session_keep is not None\n",
         "                sorted(visible)[0]\n"
         "                if session_keep is not None\n")
elif WB == "WB5":
    # MOVE refusals carry no teaching (no field, no rule, no remedy).
    edit(AGENTS,
         "                raise InvalidAgentIdentityError(\n"
         "                    f\"agent {field_name} {value!r} is not a legal identifier — it must match \"\n",
         "                raise InvalidAgentIdentityError(\"invalid input\")\n"
         "                raise InvalidAgentIdentityError(\n"
         "                    f\"agent {field_name} {value!r} is not a legal identifier — it must match \"\n")
    edit(AGENTS,
         "            raise InvalidAgentIdentityError(\n"
         "                \"agent role must be non-blank",
         "            raise InvalidAgentIdentityError(\"invalid input\")\n"
         "            raise InvalidAgentIdentityError(\n"
         "                \"agent role must be non-blank")
elif WB == "WB6":
    # wiring: the wired AppContext never applies the agent DDL.
    edit(SERVER, "        await agent_registry.ensure_ready()\n", "")
elif WB == "WB7":
    # Q5: per-row-resilient backfill (skips violators, never loud).
    edit(PRINCIPALS, "\"owner_agent = id, scope = $scope WHERE scope IS NONE\"", "\"owner_agent = id, scope = $scope WHERE scope IS NONE AND id = $one\"")
    edit(PRINCIPALS,
         "    with governed_exempt(\"migrate-governed\", statement=backfill_statement):\n"
         "        await run_query(\n"
         "            acquire=store.acquire,\n"
         "            drop=store.drop,\n"
         "            url=store.url,\n"
         "            noun=\"governed agent-owner backfill\",\n",
         "    with governed_exempt(\"migrate-governed\", statement=backfill_statement):\n"
         "      ids = await run_query(acquire=store.acquire, drop=store.drop, url=store.url, noun='ids',\n"
         "          label='ids', statement=f'SELECT VALUE id FROM {AGENT_TABLE} WHERE scope IS NONE', params={}, logger=logger)\n"
         "      unmigrated = 0\n"
         "      for one in ids or []:\n"
         "       try:\n"
         "        await run_query(\n"
         "            acquire=store.acquire,\n"
         "            drop=store.drop,\n"
         "            url=store.url,\n"
         "            noun=\"governed agent-owner backfill\",\n")
    edit(PRINCIPALS,
         "            statement=backfill_statement,\n            params={\"owner\": operator_id, \"scope\": project_scope},\n            logger=logger,\n        )\n",
         "            statement=backfill_statement,\n            params={\"owner\": operator_id, \"scope\": project_scope, 'one': one},\n            logger=logger,\n        )\n"
         "        unmigrated += 1\n"
         "       except Exception:\n"
         "        continue\n")
elif WB == "WB8":
    # Q5 refusal names the count but NOT the rows (ids) the ruling says it must name.
    edit(PRINCIPALS, "f\"({', '.join(owned_unscoped_ids[:10])}) — a multi-principal", "f\"— a multi-principal")
elif WB == "WB9":
    # the refusal reason never states the COUNT (only the §2.1 citation carries a '1').
    edit(PRINCIPALS, "f\"{len(owned_unscoped_ids)} agent row(s) carry an owner but no scope \"", "\"some agent rows carry an owner but no scope \"")
elif WB == "WB10":
    # stamp owners on NONE-owner rows FIRST (the old leg's statement), THEN run the row precondition and refuse.
    edit(PRINCIPALS, "    owned_unscoped = await run_query(\n",
         "    await run_query(acquire=store.acquire, drop=store.drop, url=store.url, noun='pre', label='pre',\n"
         "        statement=f\"UPDATE {AGENT_TABLE} SET owner_principal = type::record('{PRINCIPAL_TABLE}', $owner) WHERE owner_principal IS NONE\",\n"
         "        params={'owner': operator.id.partition(':')[2] or operator.id}, logger=logger)\n"
         "    owned_unscoped = await run_query(\n")
    edit(PRINCIPALS, "f\"SELECT VALUE id FROM {AGENT_TABLE} WHERE scope IS NONE AND owner_principal IS NOT NONE\"",
         "f\"SELECT VALUE id FROM {AGENT_TABLE} WHERE scope IS NONE AND owner_principal IS NOT NONE AND owner_principal != type::record('principal', $op)\"")
    edit(PRINCIPALS, "        params={},\n        logger=logger,\n    )\n    owned_unscoped_ids",
         "        params={'op': operator.id.partition(':')[2] or operator.id},\n        logger=logger,\n    )\n    owned_unscoped_ids")
elif WB == "WB11":
    # the MOVE uses .match (Python `$` accepts a trailing newline — finding #210's class).
    edit(AGENTS, "            if not AGENT_NAME_PATTERN.fullmatch(value):\n", "            if not AGENT_NAME_PATTERN.match(value):\n")
elif WB == "WB12":
    # register stamps the session-keep scope ONLY for the keeper's own agents (a joined member's agent stays NONE).
    edit(SERVER, "                if session_keep is not None\n                else None\n",
         "                if session_keep is not None and kept_by_me\n                else None\n")
elif WB == "WB13":
    # the blank-role check is a private strip(), not the shared lorerunes.is_blank (routing-not-sharing).
    edit(AGENTS, "        if is_blank(role):\n", "        if not role.strip():\n")
else:
    raise SystemExit(f"unknown {WB}")
print(f"{WB} applied")
```

### A.4 `run_wbs.sh`
```bash
#!/usr/bin/env bash
# Apply each wrong build on top of adv-ref in the wb scratch copy, run the 63c-i-a contract files, record the tail.
set -u
SCR=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/2e70e163-b2d4-4ee6-9367-72203a3e11ec/scratchpad
cd "$SCR/wb"
FILES="loremaster/tests/test_agent_governance_63c_i_a.py loremaster/tests/test_agent_owns_principal_schema.py loremaster/tests/test_comms_schema.py loremaster/tests/test_comms_wiring.py loremaster/tests/test_agent_registry.py"
echo "provenance: $(uv run python -c 'import loremaster; print(loremaster.__file__)')"
for WB in "$@"; do
  git checkout -q -f adv-ref
  uv run --no-project python "$SCR/wrong_builds.py" "$SCR/wb" "$WB" || { echo "$WB: APPLY FAILED"; continue; }
  echo "== $WB diff: $(git diff --shortstat)"
  timeout 900 uv run pytest -n 12 -q -p no:cacheprovider $FILES 2>&1 | awk '/^(FAILED|ERROR)/ || / passed| failed/' | tail -25
done
git checkout -q -f adv-ref
```

### A.5 `test_adv_killpins_63c_i_a.py` — the kill-pins (final run on ref: 12 passed)
```python
"""adversary-63c-i-a KILL-PINS — scratch-only probes proving each MISSING PIN discriminates.

Each pin must be RED on its named wrong build (wrong_builds.py) and GREEN on the reference build
(ref_build.py). Placed into loremaster/tests/ of a scratch copy only; never into the main checkout.
"""

from __future__ import annotations

from typing import Any

import pytest
from _governed_contract import (
    AGENT_TABLE,
    agent_case,
    apply_ddl,
    build_principal_and_keep_stores,
    credentialed_app_context,
    governed_overlay_ddl,
    seed_agent_governed,
    seed_agent_legacy,
    store_handle,
)
from _surreal_harness import connect_admin, drop_database, make_env, run, unique_database
from loremaster.agents import AgentRegistry, AgentRegistryError
from loremaster.store import surreal_schema
from lorerunes.pdp import keep_scope

from loremaster import principals

_DIM = 8


def _bare(value: Any) -> str:
    text = str(getattr(value, "id", value))
    return text.split(":", 1)[-1] if ":" in text else text


# --- KP-W1: the W1-1 twin (WB1) — mutate the SHARED emitter's EXISTING specs, not append ------------
def test_KP_W1_every_governed_column_and_index_moves_with_the_shared_emitter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rewrite every governed spec's TYPE and every governed index NAME in the shared emitter; the
    agent DDL must carry ONLY the mutated forms. A hand-rolled owner_principal row / inline index kept
    beside the emitter call (deduped or filtered) still emits the OLD form -> RED."""
    original_fields = surreal_schema._governed_field_specs
    original_indexes = surreal_schema._governed_index_statements
    monkeypatch.setattr(
        surreal_schema,
        "_governed_field_specs",
        lambda: tuple((name, f"{type_expr.replace('>', '>', 1)}", "COMMENT 'kp_w1_probe'")
                      for name, type_expr, _c in original_fields()),
    )
    monkeypatch.setattr(
        surreal_schema,
        "_governed_index_statements",
        lambda table: [s.replace(f"{table}_", f"{table}_kpw1_", 1) for s in original_indexes(table)],
    )
    ddl = surreal_schema.generate_agent_ddl()
    statements = [s.strip() for s in ddl.split(";") if s.strip()]
    for column in ("owner_principal", "owner_agent", "scope"):
        defs = [s for s in statements if s.startswith(f"DEFINE FIELD OVERWRITE {column} ON {AGENT_TABLE} ")]
        assert defs and all("kp_w1_probe" in s for s in defs), (column, defs)
    old_named = [s for s in statements if s.startswith("DEFINE INDEX") and f" {AGENT_TABLE}_owner_principal " in s]
    assert not old_named, f"an agent_owner_principal index survives the shared-emitter rename: {old_named}"


# --- KP-Q5-MIX: a mixed store (governed + legacy) — WB2 (clobber) and WB3 (owner-only precondition) --
async def test_KP_Q5_a_store_with_governed_and_legacy_agents_migrates_only_the_legacy() -> None:
    """Production's cutover shape: agents registered AFTER 63c (full triple, session-keep scope) beside
    legacy NONE rows. The migrate must NOT refuse (they are not owned-but-unscoped), must backfill ONLY
    the legacy rows, and must leave every governed row byte-identical (∀ scoped rows untouched — the old
    leg's ∀-NONE-owner-never-a-re-stamp virtue, carried to the scope key)."""
    env = make_env(database=unique_database(), dim=_DIM)
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    connection = await connect_admin(env)
    try:
        await apply_ddl(connection, agent_case().make_ddl(), url=env.url)
        await apply_ddl(connection, governed_overlay_ddl(AGENT_TABLE), url=env.url)
        await principal_store.create(email="operator@example.com", role="admin")
        member = await principal_store.create(email="member@example.com", role="member")
        session_scope = "keep:sessionkeepkp"
        governed_ids = []
        for index in range(2):
            governed_ids.append(await seed_agent_governed(
                connection, row_id=f"gov_{index}", name=f"gov-{index}", session="live",
                owner_principal=_bare(member.id), owner_agent=f"gov_{index}", scope=session_scope,
            ))
        for index in range(3):
            await seed_agent_legacy(connection, row_id=f"leg_{index}", name=f"leg-{index}", session="dead")
        before = await run(connection, f"SELECT * FROM {AGENT_TABLE} WHERE scope IS NOT NONE")
        handle, _calls = store_handle(connection, url=env.url)
        result = await principals.migrate_governed(
            table=AGENT_TABLE, store=handle, keep_store=keep_store, principal_store=principal_store
        )
        assert result.refused is False, f"a governed+legacy store was REFUSED: {result.reason!r}"
        assert result.backfilled == 3, result
        after = await run(
            connection, f"SELECT * FROM {AGENT_TABLE} WHERE id IN $ids",
            {"ids": [r["id"] for r in before]},
        )
        assert sorted(map(str, after), key=str) == sorted(map(str, before), key=str), (
            "the migrate re-stamped an ALREADY-GOVERNED agent (session-keep scope / member owner "
            f"clobbered): before={before!r} after={after!r}"
        )
    finally:
        await connection.close()
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


# --- KP-STAMP-2S: two sessions (WB4) --------------------------------------------------------------
async def test_KP_register_scope_is_THE_session_keep_across_two_sessions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """Parameter-value monoculture breaker: one principal registers into TWO sessions; each row's
    scope must be ITS OWN session's keep (not any keep the registrant can see)."""
    async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM) as world:
        ctx = world["ctx"]
        world["holder"]["email"] = world["emails"]["alice"]
        await ctx.comms(action="register", agent="fixer-b", session="wave7", role="builder")
        await ctx.comms(action="register", agent="fixer-c", session="wave8", role="builder")
        for agent, session in (("fixer-b", "wave7"), ("fixer-c", "wave8")):
            rows = await run(world["admin_conn"], f"SELECT scope FROM {AGENT_TABLE} WHERE name = $n", {"n": agent})
            keep = await ctx._keep_store.get_by_key(f"session:{session}")  # noqa: SLF001
            assert rows[0]["scope"] == keep_scope(_bare(keep.id)), (agent, rows, keep)


# --- KP-MOVE-TEACH: the refusal teaches (WB5) ------------------------------------------------------
@pytest.mark.parametrize(("field", "kwargs"), [
    ("name", {"name": "Bad Name!", "session": "wave7", "role": "builder"}),
    ("session", {"name": "fixer-b", "session": "Bad Session!", "role": "builder"}),
    ("role", {"name": "fixer-b", "session": "wave7", "role": "  "}),
])
async def test_KP_move_refusal_names_the_field_and_the_rule(field: str, kwargs: dict[str, str]) -> None:
    env = make_env(database=unique_database(), dim=_DIM)
    registry = AgentRegistry(url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password)
    try:
        await registry.ensure_ready()
        with pytest.raises(AgentRegistryError) as info:
            await registry.register(kwargs["name"], session=kwargs["session"], role=kwargs["role"])
        message = str(info.value)
        assert field in message, f"refusal does not name the offending field {field!r}: {message!r}"
        rule = "non-blank" if field == "role" else "[a-z0-9]"
        assert rule in message, f"refusal does not state the rule ({rule!r}): {message!r}"
        assert "register again" in message, f"refusal does not teach the remedy: {message!r}"
    finally:
        await registry.close()
        await drop_database(env)


# --- KP-Q5-IDS: the refusal names the rows (WB8) --------------------------------------------------
async def test_KP_row_precondition_refusal_names_the_offending_row_id() -> None:
    env = make_env(database=unique_database(), dim=_DIM)
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    connection = await connect_admin(env)
    try:
        await apply_ddl(connection, agent_case().make_ddl(), url=env.url)
        await apply_ddl(connection, governed_overlay_ddl(AGENT_TABLE), url=env.url)
        await principal_store.create(email="operator@example.com", role="admin")
        await seed_agent_governed(connection, row_id="owned_unscoped_kp", name="x", session="s",
                                  owner_principal="other", owner_agent=None, scope=None)
        handle, _calls = store_handle(connection, url=env.url)
        result = await principals.migrate_governed(table=AGENT_TABLE, store=handle, keep_store=keep_store,
                                                   principal_store=principal_store)
        assert result.refused and "owned_unscoped_kp" in str(result.reason), result
    finally:
        await connection.close()
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


# --- KP-Q5-1-STRICT: the refusal writes NOTHING (WB10) and names the COUNT unambiguously (WB9) ------
async def test_KP_row_precondition_refusal_is_byte_inert_and_counts_two() -> None:
    """TWO owned-but-unscoped rows (count 2 cannot be satisfied by a '§2.1' citation) + clean legacy
    rows; the refused migrate must leave EVERY agent row byte-identical (not just scope)."""
    env = make_env(database=unique_database(), dim=_DIM)
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    connection = await connect_admin(env)
    try:
        await apply_ddl(connection, agent_case().make_ddl(), url=env.url)
        await apply_ddl(connection, governed_overlay_ddl(AGENT_TABLE), url=env.url)
        await principal_store.create(email="operator@example.com", role="admin")
        for index in range(3):
            await seed_agent_legacy(connection, row_id=f"leg_{index}", name=f"leg-{index}", session="dead")
        for index in range(2):
            await seed_agent_governed(connection, row_id=f"trap_{index}", name=f"trap-{index}", session="dead",
                                      owner_principal="other", owner_agent=None, scope=None)
        before = await run(connection, f"SELECT * FROM {AGENT_TABLE} ORDER BY id")
        handle, _calls = store_handle(connection, url=env.url)
        result = await principals.migrate_governed(table=AGENT_TABLE, store=handle, keep_store=keep_store,
                                                   principal_store=principal_store)
        after = await run(connection, f"SELECT * FROM {AGENT_TABLE} ORDER BY id")
        assert result.refused is True and result.backfilled == 0, result
        assert "2 agent" in str(result.reason) or "2 row" in str(result.reason), result.reason
        assert after == before, f"a REFUSED migrate mutated agent rows: before={before!r} after={after!r}"
    finally:
        await connection.close()
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


# --- KP-MOVE-NEWLINE: fullmatch, never match (WB11 / finding #210) -------------------------------
@pytest.mark.parametrize("field", ["name", "session"])
async def test_KP_move_refuses_a_trailing_newline_identifier(field: str) -> None:
    env = make_env(database=unique_database(), dim=_DIM)
    registry = AgentRegistry(url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password)
    admin = await connect_admin(env)
    try:
        await registry.ensure_ready()
        kwargs = {"name": "fixer-b", "session": "wave7"}
        kwargs[field] = kwargs[field] + "\n"
        with pytest.raises(AgentRegistryError):
            await registry.register(kwargs["name"], session=kwargs["session"], role="builder")
        rows = await run(admin, f"SELECT count() FROM {AGENT_TABLE} GROUP ALL")
        assert not rows or rows[0]["count"] == 0, rows
    finally:
        await admin.close()
        await registry.close()
        await drop_database(env)


# --- KP-STAMP-JOINED: a householded (non-keeper) principal's agent is stamped too (WB12) ----------
async def test_KP_a_joined_members_agent_is_stamped_with_the_shared_session_keep(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    async with credentialed_app_context(
        monkeypatch, tmp_path, principals={"alice": "member", "bob": "member"}, dim=_DIM
    ) as world:
        ctx = world["ctx"]
        world["holder"]["email"] = world["emails"]["alice"]
        await ctx.comms(action="register", agent="keeper-a", session="shared", role="builder")
        keep = await ctx._keep_store.get_by_key("session:shared")  # noqa: SLF001
        await ctx._keep_store.add_household_member(keep_id=_bare(keep.id), member_email=world["emails"]["bob"])  # noqa: SLF001
        world["holder"]["email"] = world["emails"]["bob"]
        await ctx.comms(action="register", agent="joiner-b", session="shared", role="builder")
        rows = await run(world["admin_conn"], f"SELECT owner_principal, scope FROM {AGENT_TABLE} WHERE name = 'joiner-b'")
        assert str(rows[0]["owner_principal"]) == f"principal:{world['pids']['bob']}", rows
        assert rows[0]["scope"] == keep_scope(_bare(keep.id)), rows


# --- KP-ISBLANK-SHARED: register's blank-role rule IS lorerunes.is_blank (WB13) --------------------
async def test_KP_register_blank_role_routes_through_the_shared_is_blank(monkeypatch: pytest.MonkeyPatch) -> None:
    import loremaster.agents as agents_module

    env = make_env(database=unique_database(), dim=_DIM)
    registry = AgentRegistry(url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password)
    try:
        await registry.ensure_ready()
        monkeypatch.setattr(agents_module, "is_blank", lambda value: value == "builder", raising=True)
        with pytest.raises(AgentRegistryError):
            await registry.register("fixer-b", session="wave7", role="builder")
    finally:
        await registry.close()
        await drop_database(env)
```

### A.6 corrected heartbeat leg (MP-2) — generated from the contract file by one substitution
```python
# body = contract's TestAgentHeartbeatOnALegacyRoleRow63cIA with exactly one substitution:
body = src[start:end].replace('row_id="role_empty"', 'row_id=AgentRegistry._agent_id("wave7", "legacy-agent")')
# results: adv-base (f04916d) -> FAILED "... engine: SurrealDB agent query rejected ... (assert violation)"  (RIGHT reason)
#          adv-ref            -> 1 passed
```

### A.7 mutation-proof invocations (M1–M3; declared sets fixed before the run from `--collect-only`)
```bash
S=loremaster/tests/test_comms_schema.py; G=loremaster/tests/test_agent_governance_63c_i_a.py
CMD="uv run pytest -n 8 -q -p no:cacheprovider $S::TestAgentDdlOffline $S::TestNoGovernedTableCarriesAConstraintALegacyRowCanViolate $G --deselect $G::TestAgentHeartbeatOnALegacyRoleRow63cIA::test_a_touch_succeeds_on_a_role_empty_legacy_row_after_the_drop"
# M1: --anchor '    ("role", _CHUNK_STRING_TYPE, ""),' --replacement '    ("role", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),'
#     --expect-red P2[agent], LegA drop[role], LegB survives            -> PROOF HELD, exit 0
# M2: --anchor '    ("status", _CHUNK_STRING_TYPE, f"ASSERT $value IN [{_AGENT_STATUS_ALLOWED}]"),' --replacement '    ("status", _CHUNK_STRING_TYPE, ""),'
#     --expect-red status_domain, KEPT, aligns, P2[agent], status-STAYS, P-A3   -> PROOF HELD, exit 0
# M3: --anchor $'    _AGENT_STATUS_RETIRED,\n)' --replacement $'    _AGENT_STATUS_RETIRED,\n    "paused",\n)'
#     --expect-red status_domain, aligns   -> observed {aligns}; exit 4 (my misprediction; P-A2 fired)
uv run python scripts/mutation_proof.py --file loremaster/loremaster/store/surreal_schema.py --anchor ... --replacement ... --expect-red ... -- $CMD
```

### A.8 the `governed_populations` resolver probe (MP-10)
```python
import sys, ast; sys.path.insert(0, 'loremaster/tests')
import _governed_contract as g
from pathlib import Path
src = Path('loremaster/loremaster/store/surreal_schema.py').read_text(); tree = ast.parse(src)
c = g._schema_string_constants(tree)
for call in ast.walk(tree):
    if isinstance(call, ast.Call) and g.call_name(call) == g._DEFINE_RELATION_EMITTER:
        print([g._resolve_schema_table(a, c) for a in call.args[:3]])
# -> ['briefed', None, 'brief'] · ['to', 'message', None] · ['member_of', None, 'keep']   (AGENT_TABLE / PRINCIPAL_TABLE unresolved)
```
