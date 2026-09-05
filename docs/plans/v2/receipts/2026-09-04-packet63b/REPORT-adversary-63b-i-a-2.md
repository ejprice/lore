# REPORT-adversary-63b-i-a-2

brief-base v14 read
brief project v7 read

CONTRACT-ADVERSARY re-grade of the REVISED F5 contract (packet 63b wave i-a) — the 2nd adversary
pass. The 1st contract graded INSUFFICIENT (2 missing pins + a borderline C-DEF F-TRAP-3);
`contract-63b-i-a-2` revised it per the design §1.9 ADDENDUM. This pass verifies the fixes
DISCRIMINATE (builds the exact wrong builds the 1st adversary walked through), hunts new gaps the
narrow patch may have introduced, and re-produces the satisfiability receipt INDEPENDENTLY.

## SUMMARY BLOCK
- receipt: brief-base v14 read · brief project v7 read
- **VERDICT: CONTRACT SUFFICIENT.** Every 1st-adversary wrong build now REDS; no new gap; the
  independent §1.9 reference goes 0-failed with NO HANG.
- **P1 headline — NO wrong build survives.** WB#1 (label-ignores-effect) → both MISSING-PIN-#1
  pins RED. WB#1b (frame-specific skip, only `_reinforce`) → the ∀ pin REDS pointing AT `_reinforce`
  (the ∀ is real, QUANTIFIER LAW). WB#2 (`return frozenset({memory})`) → the reach pin REDS while
  the value pin stays GREEN (the exact demanded discrimination). WB#3/#4/#5 (drop leg4/leg2/leg3)
  → each exempt-leg pin REDS, the other two pass (independence survives the ExemptToken reshape).
- **F-TRAP-3 (constructed oracle) CLOSED:** `_memory_ddl_object_names` has NO live definition
  anywhere (AST-confirmed, tests+prod); `_effect_ensure_ready` compares `schema_after == oracle` by
  DICT EQUALITY (no regex); the non-vacuity pin (one extra field) discriminates; both reviser C-DEF
  fixes are LOAD-BEARING (proven by the correct build passing both read-path pins).
- **Independent satisfiability:** `test_memory_enforcement_63b_ia.py` **33 passed / 0 failed**,
  serial `-n0`, `timeout 500`, 11.33s — **NO HANG**; + migrated `63a_v`/`63a_iv`/`bounds_63a_iv`
  **27 passed** (60/0 combined). `loremaster.__file__ = /tmp/adv63bia2-scratch/loremaster/loremaster/__init__.py` (#140).
- Reuse ledger: none committed — I am read-only/advisory; every symbol I wrote lives in the
  DISPOSABLE scratch reference (`/tmp/adv63bia2-scratch`, `scratch_copy.sh`) and is the builder's to
  author. Wrong builds are single-line diffs documented in §"P1 WRONG-BUILD MATRIX".
- Packages considered: none new — the reference is bespoke test substrate (stdlib
  `ast`/`re`/`asyncio`/`contextvars`/`pathlib` + `pyyaml` (already a dep) + the SurrealDB SDK's own
  `query_raw`). P-PKG AGREES with the 1st adversary + the author (`bespoke`/`keep_with_trigger`).
- Graded: 72fc220 · HEAD-at-report: 72fc220 · SAME
- decisions-needed: none.
- pointers: fix-discrimination §"P1 WRONG-BUILD MATRIX"; QUANTIFIER §"P1b"; REACH §"P1c"; new-gap
  hunt §"P2/NEW-GAP"; satisfiability §"SATISFIABILITY RECEIPT"; corpse sweep §"P6".

---

## THE RE-GRADE MANDATE, ITEM BY ITEM

### (1) THE FIXES DISCRIMINATE — each wrong build the 1st adversary walked through now REDS

Built an INDEPENDENT correct reference per §1.9's ruled mechanism (§"SATISFIABILITY RECEIPT"),
then patched it into each wrong build (single-line diffs, in scratch only) and ran the exact pins.

- **MISSING PIN #1 — the classifier RUNS a label frame's effect predicate.** WB#1 = the
  `if observed.label is not None: return True` door (the HEAD stub's label leg; blesses any labeled
  write). RESULT: **both** `TestTheClassifierRunsALabelFramesEffectPredicate` pins RED; the 3 exempt
  legs + the population VALUE pin stayed GREEN (the defect is isolated to the two new label pins).
  The generalised `test_every_label_frame_rejects_an_effect_its_predicate_denies` caught it on
  `remember`/`_upsert_fragment` — a DIFFERENT frame than `_reinforce`, so the ∀ is not conditioned
  on one frame. WB#1b then made it PRECISE: run the predicate for every label frame EXCEPT
  `_reinforce` (blessed) → the ∀ pin REDS pointing SPECIFICALLY at `_reinforce`:
  `"a '_reinforce'-labeled write whose effect its OWN entry predicate REJECTS was CLASSIFIED …:
  _reinforce"`. The `checked >= 4` floor + the per-entry self-check (`entry.effect(rejected) is
  False`) make this a genuine ∀ over ≥4 label frames. **CONFIRMED — the QUANTIFIER LAW holds.**

- **MISSING PIN #2 — `governed_populations()`'s reach is a CHECKED VARIABLE.** WB#2 =
  `return frozenset({MEMORY_TABLE})` (a hardcoded literal). RESULT:
  `test_the_population_derivation_reach_is_a_checked_variable` RED (`assert frozenset({'memory'}) !=
  frozenset({'memory'})` — the synthetic-source growth `_widget_statements`+`_widget_edge_statements`
  is genuinely exercised, not a vacuous ∀), while `test_the_derived_population_set_is_the_known_set`
  PASSED (1 passed) — the VALUE pin alone does NOT catch the hardcode. That is the exact
  discrimination the adversary demanded. **F-TRAP-1 DUAL confirmed** on the correct build: the
  synthetic `_agent_statements` (a DIRECT `owner_principal` DEFINE FIELD, NO `_governed_field_specs`
  call — the packet-62 shape) is EXCLUDED → `baseline == {memory}` (the derivation keys on the
  CALLER, never the field name). Verified live: the real `surreal_schema.py` has ONLY
  `_memory_statements` calling `_governed_field_specs` (AST-checked) → `governed_populations()` =
  `{memory}`; the 6 real `_define_relation_table(...)` calls pass module CONSTANTS not string
  literals, so no relation table joins at i-a — matching the ruled `{memory}`.

- **F-TRAP-3 — the constructed `ensure_ready` oracle.** `_memory_ddl_object_names` (the retired
  DDL-text regex) has **NO live `def` anywhere** in the tests OR production tree (AST-confirmed; the
  only 3 residual string hits are docstrings explaining the retirement). `_effect_ensure_ready`
  compares `effect.schema_after == oracle` (SchemaSnapshot dict equality — no regex, no hand-model
  of implicit expansions). The non-vacuity pin
  (`test_the_ensure_ready_effect_predicate_discriminates`) applies `generate_memory_ddl` + ONE extra
  field to a virgin DB, reads `INFO FOR TABLE`, and asserts `extra != oracle` then the smuggled
  effect fails — GREEN on the correct build (it is contract-side + a live oracle read). **The 2
  reviser-found C-DEF fixes are LOAD-BEARING, and the correct build proves BOTH:**
  1. `schema_snapshot_from_info` normalises BOTH the `query_raw` rpc envelope
     (`{'result':[{'result':<map>}]}`, my observer's read) AND the `.query` bare dict (the oracle
     fixture's read) to the SAME `SchemaSnapshot`. `test_the_rebuild_arc_is_observed_and_classified`
     PASSES → my observer's `schema_after` (via `query_raw`) equals the oracle (via `.query`); had
     the envelope not been dug, `schema_after` would be empty ≠ oracle → RED. Proven load-bearing.
  2. The coverage name-extract is duck-typed `str(getattr(write.exempt, "name", write.exempt))`. My
     reference's `active_exempt()` returns a PRODUCTION `governed.ExemptToken` (a DIFFERENT class
     from the substrate twin); `test_every_runtime_observed_frame_is_observed_with_a_nonempty_effect`
     PASSES → "migrate-governed" is extracted from the production token. An `isinstance(exempt,
     <substrate ExemptToken>)` would have failed to extract it → the channel missing → RED. Proven
     load-bearing.

### (2) NEW-GAP HUNT — did the narrow patch introduce a vacuous or non-firing pin?  NO.

The revision's shape changes and my adversarial findings:
- **ExemptToken (origin moved INTO the token, tuple→dataclass).** The 1st adversary flagged leg4 as
  the reshape's main target. I dropped EACH exempt leg independently against my reference: WB#3 (leg4
  ⇒ `token.origin` ignored) → `test_leg4_reds_a_borrowed_token_from_a_foreign_origin` RED, leg2/leg3
  PASS. WB#4 (leg2 ⇒ golden text ignored) → `test_leg2_reds_a_widened_statement` RED, leg3/leg4 PASS.
  WB#5 (leg3 ⇒ effect ignored) → `test_leg3_reds_a_golden_edited_to_bless_a_seizure` RED, leg2/leg4
  PASS. All four legs still discriminate INDEPENDENTLY — the reshape weakened nothing.
- **`governed_populations(schema_source=…)` new param.** Not vacuous: the reach pin drives the
  SYNTHETIC source (growth exercised); the value pin drives the REAL module. WB#2 proves the reach
  pin fires on a hardcode the value pin waves through.
- **`SchemaSnapshot` + `schema_after` field (default None).** No pin passes vacuously on it: the
  ensure_ready non-vacuity pin constructs the smuggled `schema_after` explicitly; row-entry effect
  predicates ignore `schema_after`; a DDL-frame effect that is `None`-schema fails closed. The LOUD
  raise in `_effect_ensure_ready` (oracle not populated) has no order-dependent vacuity: the ONLY
  test that classifies an ensure_ready write (`test_the_rebuild_arc`) declares the
  `ensure_ready_oracle` fixture dependency; the generalised label pin's ensure_ready candidate
  carries rows → the `if effect.row_deltas: return False` short-circuit fires BEFORE the oracle read
  (no fixture needed, no raise).
- **Observer stub docstring / persistent dispatcher.** The detach pin
  (`test_detaching_the_hook_reds_every_runtime_observation_never_green`) passes on the correct build
  — clearing `_CALL_HOOKS` truly disarms because the dispatcher is persistent (registered once at
  import, not per `observe_…`), and `observe_…` only registers a `(table, sink)` in the registry.

### (3) SATISFIABILITY RECEIPT — reproduced INDEPENDENTLY of the reviser

See §"SATISFIABILITY RECEIPT" for the full receipt (33/0 + 27/0, serial, NO HANG, provenance).

---

## P1 WRONG-BUILD MATRIX (measured in `/tmp/adv63bia2-scratch`, provenance-asserted; correct ref restored byte-exact via md5 after each)
| # | wrong build (single-line patch) | target pin(s) | result |
|---|---|---|---|
| WB#1 | classifier label leg = `if observed.label is not None: return True` | `TestTheClassifierRunsALabelFramesEffectPredicate::{test_a_reinforce_labeled_write_that_seizes…, test_every_label_frame_rejects…}` | **BOTH RED** (exempt legs + value pin GREEN) |
| WB#1b | run predicate for all label frames EXCEPT `_reinforce` (blessed) | `test_every_label_frame_rejects_an_effect_its_predicate_denies` | **RED — names `_reinforce`** (∀ is real) |
| WB#2 | `governed_populations` = `return frozenset({MEMORY_TABLE})` | `test_the_population_derivation_reach_is_a_checked_variable` | **RED** (value pin `test_the_derived_population_set_is_the_known_set` GREEN) |
| WB#3 | exempt `leg4 = True` (ignore `token.origin`) | `test_leg4_reds_a_borrowed_token_from_a_foreign_origin` | **RED** (leg2/leg3 GREEN) |
| WB#4 | exempt `leg2 = True` (ignore golden text) | `test_leg2_reds_a_widened_statement_with_the_same_effect` | **RED** (leg3/leg4 GREEN) |
| WB#5 | exempt `leg3 = True` (ignore effect predicate) | `test_leg3_reds_a_golden_edited_to_bless_a_seizure` | **RED** (leg2/leg4 GREEN) |

Every wrong build the 1st adversary named as a survivor is now CAUGHT, and no new wrong build
survives the exempt/label channel.

## P1b — QUANTIFIER TABLE (the REVISED invariants; unchanged rows carry the 1st adversary's receipts)
| invariant | ∀ / guarded | receipt |
|---|---|---|
| §1.4 LABEL classified iff matched entry's `effect` holds ∀ label frame | **∀ (now closed)** | WB#1 (both pins red) + WB#1b (frame-specific red on `_reinforce`); the ∀ pin exercises ≥4 label frames (`checked >= 4`) with a per-entry self-check |
| §1.4 EXEMPT classified iff name∧golden∧effect∧origin (legs independent) | ∀ (4 independent legs) | WB#3/#4/#5 — dropping each leg reds ONLY its pin; the other two pass |
| §1.5c-iii population set DERIVED ∀ new governed table (checked variable) | **∀ (now closed)** | WB#2 (reach pin red on hardcode; value pin green); F-TRAP-1 dual (agent excluded) green on correct build |
| §5.1 Q1 `ensure_ready` effect == CONSTRUCTED oracle ∀ no-rows DDL apply | ∀ (non-vacuity pinned) | correct build 33/0 + `test_the_ensure_ready_effect_predicate_discriminates` one-extra-field leg |
| §1.2 detection = state-diff effect ∀ observed governed write | ∀ | correct build: `test_every_observed_member_write…` + verb-agnostic + no-effect + rolled-back all green |

## P1c — REACH TABLE (the REVISED/relied-on instruments)
| instrument | reach DERIVED? | coverage a CHECKED variable? | effect vs proxy | one-source / mutation | leg run |
|---|---|---|---|---|---|
| `governed_populations` (population SET) | DERIVED (AST over `surreal_schema`: `_governed_field_specs` callers ∪ governed-endpoint relations) | **YES — synthetic growth reds (WB#2)** | EFFECT (AST) | one derivation | EMPIRICAL |
| classifier LABEL-frame effect predicate | n/a | **YES — off-predicate label reds ∀ frame (WB#1/1b)** | EFFECT (runs `entry.effect(observed.effect)`) | shared classifier | EMPIRICAL |
| effect observer reach = `_sdk_guard` `_CALL_HOOKS` (query_raw door) | DERIVED (SDK class; the `query_raw` door = the partition pin's set, cited by name) | YES — detach → 0-observed → red (correct build's detach pin) | EFFECT (state diff) | one persistent dispatcher | EMPIRICAL (detach) + construction (the UNCOUNTABLE-door partition pin lives in `test_query_tasks_bounded.py`, one instrument over — not re-run here) |
| derived keyword grammar / `SURREALQL_STATEMENT_KEYWORDS` | DERIVED from `surrealdb-docs` corpus statement page stems (currency pin re-derives & compares) | YES — `test_the_keyword_currency_pin_tracks_the_corpus` + `test_every_mutation_keyword_has_an_operand_rule` | EFFECT | one derivation | EMPIRICAL (correct build green) |
| exempt 4-leg classifier | n/a | YES (legs 2/3/4 drops each caught — WB#3/#4/#5) | EFFECT | shared classifier | EMPIRICAL |

## P2 / NEW-GAP — fixture perturbation & vacuity
No new-gap pin found (see §(2) above). The wrong-build matrix IS the perturbation proof: each
load-bearing fixture (the seizing {importance,scope} effect; the two-scope-rows / row-plus-schema
candidates; the synthetic baseline/grown sources; the borrowed-token origin) is shown to
DISCRIMINATE — a wrong build patched away from the fixture's guarded property reds, and the correct
reference passes. The population reach pin's synthetic-source growth is genuinely exercised (WB#2
reds only because the hardcode ignores it).

## P6 — CORPSE SWEEP (retired-behaviour assertions certifying the OLD world)
AST-scanned the whole scratch test tree for live definitions:
- `TestTheAcceptedF5BoundsArePinned` + `test_r4a_*` + `test_r4c_*` (the R4-a/R4-c bound pins) —
  **DELETED** (no live class/def; the 3 substring hits are docstring prose explaining the
  retirement). Design §1.5b's "delete the pins the day 63b closes it" — DONE.
- `_memory_ddl_object_names` — **DELETED** (no live def in tests OR prod; 3 docstring mentions only).
- The `_raw_mutation_of_table` / `_mutation_verb_for_table` "NAMED ACCEPTED BOUND #449" docstring
  clauses REMAIN at HEAD — CORRECT: those functions are ★BUILDER DELIVERABLES★ (RED-until-built at
  HEAD; the widened-grammar pins `test_the_derived_grammar_covers_the_exotic_write_verbs` are RED at
  HEAD and green on my widened reference). The builder deletes the clauses at GREEN (design §1.5b).
  No corpse makes any pin green-for-the-wrong-reason. The migrated `63a_v/iv/bounds` modules go 27/0
  on my widened reference — so no surviving pin asserts the retired bounded-enumeration.

---

## SATISFIABILITY RECEIPT (independent of the reviser)
Built a CORRECT reference implementing §1.9's ruled mechanism FROM SCRATCH (not the reviser's diff),
in a provenance-asserted scratch, and ran the contract SERIAL + BOUNDED.

- Scratch via `scripts/scratch_copy.sh /tmp/adv63bia2-scratch` — provenance ASSERTED (#140 receipt):
  `loremaster.__file__ = /tmp/adv63bia2-scratch/loremaster/loremaster/__init__.py`.
- Command: `cd loremaster && timeout 500 uv run python -m pytest tests/test_memory_enforcement_63b_ia.py -n0 -p no:cacheprovider -q`
  → **33 passed, 0 failed in 11.33s** (serial `-n0`, **NO HANG**; passed-count in tail confirmed).
- Combined with the migrated modules:
  `… test_memory_enforcement_63b_ia.py test_memory_enforcement_63a_v.py test_memory_enforcement_63a_iv.py test_memory_enforcement_bounds_63a_iv.py -n0`
  → **60 passed, 0 failed in 15.58s** (i.e. `63b_ia` 33 + the three `63a` modules 27 — the
  instrument rewrite did not break the surviving 63a pins).
- The 1 warning (`RuntimeWarning: coroutine 'AsyncWsSurrealConnection.query' was never awaited`) is
  BENIGN — it is `test_a_raising_hook_is_loud`'s deliberate unawaited coroutine (the raising hook
  aborts before the coro is awaited); the pin asserts the raise PROPAGATES and passes.

### My reference's §1.9 mechanism (independently authored; matches the ruling, and the reviser's shape)
Production/hook-seam deltas (the load-bearing, non-design-obvious bits — pasted so they survive the
scratch):
- `governed.py`: `ExemptToken(name, statement, origin)` frozen dataclass; `governed_exempt` a CLASS
  CM whose `__enter__` captures `sys._getframe(1)` as `(repo-relative file, co_name)` (NO contextlib
  skip-list); `_ACTIVE_EXEMPT: ContextVar[ExemptToken|None]`; `active_exempt()` returns it.
- `principals._migrate_memory_scope`: FUNCTION-LOCAL `stmt = f"UPDATE {MEMORY_TABLE} SET scope =
  $scope WHERE scope IS NONE"` passed to BOTH `governed_exempt("migrate-governed", statement=stmt)`
  AND `run_query(statement=stmt)` — ONE source, never a module constant.
- `memory/local.ensure_ready`: `with governed.write_guard("ensure_ready"):` around its
  `execute_transaction` (both `ensure_ready` and the oracle resolve the SAME `DEFAULT_ANALYZER_NAME`,
  so `after.schema == oracle` — verified there is no analyzer-name mismatch path in the fixtures).
- `tests/_sdk_guard.py`: `CallEvent` + `_CALL_HOOKS`; `_guarded` applies every hook to the door
  coroutine AFTER `_judge()` (frame depth untouched) and sets `_guarded.__wrapped__ = original`.
- `tests/_governed_contract.py`: ONE persistent dispatcher appended to `_CALL_HOOKS` at import; it
  fires on `query_raw` ONLY (`.query` delegates → observed once at the delegation, no re-entry,
  NO DEADLOCK); reads before/after via `type(conn).query_raw.__wrapped__`; ONE lock PER EVENT LOOP
  (pytest-asyncio mints function-scoped loops) held across before→await→after; records only NON-EMPTY
  effects. The 4-leg+label-effect classifier; the corpus keyword derivation (immediate children of
  `surrealdb-docs/reference/query-language/statements`, first-token-uppercase — 30 keywords ⊇ the
  mutation|read set) with a matching committed constant; the widened grammar
  (UPDATE|UPSERT|DELETE|CREATE + INSERT INTO + RELATE ->…-> + REMOVE/DEFINE TABLE|FIELD|INDEX|EVENT +
  ALTER TABLE + REBUILD INDEX, verb→target adjacency preserved — no new production orphan derived);
  `governed_populations` (AST over `surreal_schema`, `_governed_field_specs` callers ∪
  governed-endpoint `_define_relation_table` string-literal relations, honouring `schema_source`).

## P-PKG (diffed vs the author's §6 table + the 1st adversary)
No NEW production mechanism is specifiable via a package — the instrument is bespoke test substrate
over the live store (an effect diff via stdlib dict-by-id; a schema diff via INFO-FOR-TABLE key
sets; the SDK-class hook via `_sdk_guard`; keyword derivation via `pathlib`+`yaml`; grammar via
`re`). The engine-native change-capture alternative (`DEFINE EVENT` / `CHANGEFEED`) is correctly
`keep_with_trigger` (needs test-side DDL on the real governed table; re-open trigger = a governed
table too large to snapshot in the battery — none today). AGREE with the author and the 1st
adversary on every row; no `bespoke` verdict rests on an unread API (I read the SDK's query→query_raw
delegation LIVE via the `__wrapped__`/re-entry behaviour and the corpus layout on disk).

## PROGRESS LOG
- P0: registered lore_comms (packet63b), idle-gate contract, report stub, heartbeat. Read brief-base
  v14 + role spec + BOTH continuity reports (adversary-63b-i-a INSUFFICIENT · contract-63b-i-a-2's 6
  revisions + 2 C-DEF fixes + 33/0 claim).
- P1: read spec §1.2–§1.9 + §5.1 Q1 (§1.9 BINDING); read the full revised contract module (1545 L) +
  the substrate (1546 L); read the production symbols to patch (governed/principals/local/_sdk_guard)
  via lore_get_symbol. Ruled out the analyzer-name mismatch as a would-be C-DEF (both DEFAULT).
- P2: built the independent §1.9 reference in `/tmp/adv63bia2-scratch` (scratch_copy, provenance
  asserted); 5 files compile; contract 33/0 serial NO HANG; combined 60/0.
- P3: ran the 6 wrong builds (WB#1/1b/#2/#3/#4/#5) — every 1st-adversary survivor now REDS; QUANTIFIER
  + REACH + exempt-leg independence all confirmed; corpse sweep clean; both reviser C-DEF fixes shown
  load-bearing. VERDICT: SUFFICIENT. Report complete.
