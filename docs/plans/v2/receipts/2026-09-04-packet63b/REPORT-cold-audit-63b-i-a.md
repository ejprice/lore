# REPORT-cold-audit-63b-i-a

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done**
- Graded: `81250d8` · HEAD-at-report: `81250d8` · **SAME**
- **VERDICT: GO** — the F5 runtime root-fix is correct; all four gates green; the effect
  detector / statement-scoped exempt / population derivation / coverage-checked-variable
  mechanisms are sound and mutation-proven to discriminate; residuals are dead-code /
  prose-currency only, none blocking.
- Packages considered: none — auditor writes no mechanism (I graded the committed build).
- decisions-needed (lead): named CLEANUP within the F5 wave (not a fix-wave): delete 4 dead
  helpers + trim 2 retired-bound-teaching docstrings + 1 DRY dedup — see §RESIDUALS.
- pointers: gates §"PHASE 1 — GATES"; retired-API sweep §"PHASE 3"; REFUTE probes §"PHASE 2";
  mutation proofs §"PHASE 2 · MUTATION PROOFS"; residual adjudications §"RESIDUALS";
  allowlist verdict §"PHASE 5"; dead-code/prose residual filed as **lore finding #455**.

Frame: cold auditor, REFUTE (builder≠grader). Ran everything INLINE (no nested spawns).
Scratch mutation proofs in a provenance-asserted `scratch_copy.sh` tree (receipt in §PHASE 2).

---

## PHASE 1 — GATES (independent ground-truth)

All run by me at `81250d8`. The #452 lesson (a scoped run misses cross-cutting breaks) —
so I ran the FULL repo suite, not just the F5 scope.

- **FULL REPO SUITE** `uv run python -m pytest -n auto -q`:
  **`11077 passed, 51 skipped, 3 xfailed, 9 warnings in 315.25s` — ZERO failed.**
  (The build report's "1 failed" was at build-sha `72fc220`, BEFORE the lead's allowlist
  fix; at `81250d8` that meta-pin is GREEN — §PHASE 5.)
- **CURRENCY** `uv run python scripts/pending_contract_gate.py --currency`:
  `CURRENCY : PASS — every claimed gate is GREEN or OWNED` — typecheck GREEN · ruff GREEN ·
  pytest GREEN. **0 RED_ORPHANED.**
- **RUFF** `uv run ruff check .`: `All checks passed!`
- **TYPECHECK** `./scripts/typecheck.sh`: all members OK — lorerunes 13 / lorescribe 27 /
  loresigil 35 / loremaster 259 / skills 12 / docs/eval 2 / scripts 53, shellcheck OK. 0 errors.
- **F5 contract serial** `-n0` (independent of `-n auto`): **`33 passed in 14.17s`, NO HANG**
  (the one warning is the intentional coroutine-close in the raising-hook test — benign).
- **Migrated 63a modules** (`_63a_v` + `_63a_iv` + `_bounds_63a_iv`): **`27 passed in 11.63s`.**
- lore index freshness: `last_sweep` 5 min old, watched root git_ref == `81250d8` (== HEAD),
  files_failed 0 — so `lore_impact` below is trustworthy for this sha.

---

## PHASE 2 — REFUTE THE MECHANISM (constructions, not trust in the pins)

### (2a) Effect detection is verb/shape-agnostic — CONFIRMED
The observer detects by a before/after **`SELECT *` row diff + `INFO FOR TABLE` schema diff**
(`_f5_read_state` / `_f5_row_deltas` / `_f5_schema_delta`). It **never reads the verb** — so
detection is verb-agnostic BY CONSTRUCTION (an INSERT/UPSERT/CREATE that lands a row produces a
`created`/`updated` RowDelta identically). Empirically pinned + green (full suite + serial):
- `test_detection_is_verb_agnostic_insert_create_relate_are_observed` — a label-less CREATE that
  LANDS a governed row is OBSERVED (non-empty effect) + UNCLASSIFIED (deny-by-default).
- `test_ii_shape_agnostic_a_concatenated_seizure_is_observed` — `"UP"+"DATE"` concat (the #444
  static bound) is observed at L2 by effect.
- Grammar-level exotic-verb coverage (`test_the_derived_grammar_covers_the_exotic_write_verbs`,
  `test_every_mutation_keyword_has_an_operand_rule_in_the_grammar`) — CREATE/INSERT INTO/RELATE/
  DEFINE/ALTER/REBUILD all derive; SELECT does not.
- No-effect (`SET scope = scope`) and rolled-back-txn writes produce EMPTY effects → not
  governance events (self-attack rows 1 & 4, both green, both with anti-vacuity controls).
- Note on RELATE at the OBSERVER: a RELATE creates an edge row in a *relation* table, not in
  `memory`, so it is correctly not a `memory` event — RELATE-observer detection begins mattering
  in ii-a when `to`/`message` become registered populations (§1.5c-iii derivation covers that).

### (2b) Observer re-entry / hang (#454) — CONFIRMED CLOSED (in the mode the observer runs)
- The observer's own `SELECT *`/`INFO FOR TABLE` reads go through `type(conn).query_raw.__wrapped__`
  (`_sdk_guard` sets `_guarded.__wrapped__ = original`), so they call the TRUE SDK door and never
  re-enter the guard, the hook chain, or the observer. The dispatcher acts on `query_raw` ONLY
  (`.query` delegates to `query_raw`, which would re-enter + deadlock on the held lock — the exact
  #454 class). The persistent single dispatcher (`_f5_dispatcher` appended once at import) + the
  detach pin's `_CALL_HOOKS.clear()` are consistent (a per-observe append would re-arm behind the
  clear — GOTCHA-B, correctly avoided).
- Empirical: F5 battery serial `-n0` **33 passed / 14.17s / no hang** — includes the `asyncio.gather`
  of two writes (`test_iv`) and the full REMOVE→ensure_ready→replay rebuild arc; the full suite (with
  these under `-n auto`) completed in 315s with no hang or double-count.
- ⚠ LATENT (not reachable today, so NOT a defect): `__wrapped__` unwraps exactly ONE layer. Under a
  **double-armed** guard (an autouse arm + a second `install()` re-arm on the same class), the second
  wrapper's `__wrapped__` is the FIRST wrapper, so an observer read WOULD re-enter/deadlock. This is
  unreachable in the suite: the only `install()` re-arms are `_sdk_guard`'s own controls, which never
  register the observer, and no F5-battery test re-arms. Filing as a named latent bound (see §RESIDUALS).

### (2c) Statement-scoped exempt — four legs, INDEPENDENT — CONFIRMED
- Origin capture: `governed_exempt.__enter__` uses `sys._getframe(1)` (class-CM form, no contextlib
  frame between), so `origin` is the BUSINESS frame. Empirically confirmed green:
  `test_the_live_migrate_write_classifies_by_all_four_legs` asserts the token's `origin ==
  (loremaster/loremaster/principals.py, _migrate_memory_scope)` — i.e. it lands on the business
  frame, NOT `_txn.py`/`contextlib`; `test_governed_exempt_takes_a_statement...` asserts
  `origin[1] == <the test fn that entered the with>`. Repo-root shapes agree
  (`governed._GOVERNED_REPO_ROOT` == `_governed_contract._REPO_ROOT` == repo root; both emit
  `loremaster/loremaster/...` repo-relative posix), so the leg-4 `token.origin == entry.site` compare
  is sound. Positive control (the true migrate) classifies by all four legs — green.
- The four legs are INDEPENDENT (each caught by exactly its own pin): legs 2 (widened statement),
  3 (golden edited to bless a seizure), 4 (borrowed foreign-origin token) each red their own leg
  while the other legs pass in the fixture — all green.

### (2d) Population derivation is AST-derived, not a hidden constant — CONFIRMED
`governed_populations()` walks `surreal_schema` AST for `_governed_field_specs` CALLERS ∪ relation
tables with a governed endpoint (keyed on the caller, NOT `owner_principal` field presence — the
F-TRAP-1 correction). `test_the_population_derivation_reach_is_a_checked_variable` (green) feeds a
SYNTHETIC schema source: a new `_widget_statements` caller GROWS the set, an `agent`-shaped DIRECT
`owner_principal` field does NOT. A hardcoded `frozenset({memory})` passes the value pin but FAILS
this growth pin. Confirmed a checked variable over the population SET.

### (2e) Coverage as a checked variable — CONFIRMED
`test_every_runtime_observed_frame_is_observed_with_a_nonempty_effect` (green) drives the WHOLE
battery (member create/reinforce/close · rebuild REMOVE→ensure_ready→replay · migrate) under the
observer and asserts every `runtime_observed=True` entry's channel is OBSERVED with a NON-EMPTY
effect. A frame the battery never exercises with an effect reds — reach is a checked variable over
the SET of frames, not a hidden constant.

### PHASE 2 · MUTATION PROOFS (provenance-asserted scratch)
Scratch: `scripts/scratch_copy.sh /tmp/coldaudit-scratch-63bia`; provenance receipt
`loremaster.__file__ = /tmp/coldaudit-scratch-63bia/loremaster/loremaster/__init__.py` (INSIDE
the copy). Two independent mutations, each RED the discriminating pin:

1. **Label-effect leg (MISSING PIN #1).** Re-widened `_label_leg_classifies` to
   `return True` (ignore the effect predicate — the exact HEAD wrong build). →
   `test_a_reinforce_labeled_write_that_seizes_a_governed_column_is_unclassified` **FAILED** and
   `test_every_label_frame_rejects_an_effect_its_predicate_denies` **FAILED** (2 failed). Restored.
2. **Exempt golden-text leg-2 (R4-a closure).** Neutralised the three-way golden equality
   (`... and True`). → `test_leg2_reds_a_widened_statement_with_the_same_effect` **FAILED**
   (the R4-a `WHERE scope IS NONE OR scope = $victim` seizure now classifies), while
   `test_leg3` and `test_leg4` stayed **PASSED** — empirically confirming the legs are INDEPENDENT.

Both central mechanisms of the root fix are load-bearing and their pins discriminate.
(Scratch is a disposable `/tmp` `scratch_copy.sh` tree — no worktree; safe to leave/reap.)

---

## PHASE 3 — RETIRED-API SWEEP (blast radius of a cross-cutting rewrite)

Primary: `lore_impact` (index fresh at `81250d8`). Cross-check for exhaustiveness (a retired
symbol still CONSUMED = compiles-but-breaks): a bare, anchor-free textual scan of every `.py`/`.md`
across the member trees + scripts + docs. **⚠ Fallback disclosed (dogfood protocol §3a):** the
`grep` command is blocked by a repo hook, so the exhaustive textual cross-check was run via a
Python `str in line` sweep — same effect, said out loud.

**Finding: NO live consumption of any retired symbol** — no compiles-but-breaks, no orphan:
- `extra_modules` kwarg — NO live call passes it (`observe_governed_table_writes(table)` no longer
  accepts it); all 14 hits are prose/docstrings/archived receipts. No TypeError risk.
- `test_the_observer_patch_set_is_derived_from_the_allowlist` (retired meta-pin) — DELETED; only
  prose mentions remain. No orphan `def`.
- `_memory_ddl_object_names` (retired DDL-text regex) — DELETED; only docstring/comment mentions.
- `_mutation_verb_for_table` — `lore_impact`: **dead (0 prod / 0 test refs)**; definition-only + prose.
- `seam_modules_for_tree_allowlist` — `lore_impact`: **dead (0/0)**; defined at `_governed_contract.py:1780`,
  self-referenced only by the (also-dead) `_module_for_repo_relative_file`.
- `_module_for_repo_relative_file` — `lore_impact`: **dead (0/0)**; called only by the dead
  `seam_modules_for_tree_allowlist`.
- `_originating_prod_site` — `lore_impact`: **dead (0/0)**; definition-only.

**⚠ But the builder's disclosed residual table is INCOMPLETE (the C1 "read the residual table"
lesson):** it disclosed only `_mutation_verb_for_table` as dead. Three MORE dead functions were left
DEFINED after the observer rewrite — `seam_modules_for_tree_allowlist`, `_module_for_repo_relative_file`,
`_originating_prod_site` — and the design (§1.3/§1.7) says these are RETIRED. They are functionally
retired (no consumer, kwarg gone) but the corpses are still in the tree. Adjudicated GO-with-cleanup
in §RESIDUALS.

---

## PHASE 4 / RESIDUALS — adjudications (GO-with-cleanup vs NO-GO)

None block. All are dead-code / prose-currency (P8d class) in the TEST SUBSTRATE, gates green.

| # | residual | verdict | recommendation |
|---|---|---|---|
| a | `_mutation_verb_for_table` DEAD, docstring still teaches the retired #449 R4-c bound (disclosed) | **GO-with-cleanup** | delete the fn + clause (design §1.5b says trim); dead code teaching a retired bound is the P8d prose-currency defect generator |
| b | `observe_governed_table_writes` docstring keeps the ★CONTRACT SHAPE★ "at HEAD the body is the retired verb-observer" framing (disclosed) | **GO-with-cleanup** | trim to describe the BUILT mechanism (now stale — the body IS the new mechanism) |
| c | `_defined_test_names` inlined a 3rd time in `test_every_entry_pin_is_a_defined_test` instead of a shared helper (disclosed in the allowlist entry) | **GO-with-cleanup** | extract ONE shared test-tree-enumeration helper (low priority; the allowlist entry already flags it) |
| d | **UNDISCLOSED**: `seam_modules_for_tree_allowlist` + `_module_for_repo_relative_file` + `_originating_prod_site` left DEFINED though design retired them; `seam_modules_for_tree_allowlist`'s docstring still describes the live-`extra_modules` mechanism | **GO-with-cleanup** | delete all three. Real value (don't-kick-the-can): an ii-a builder parametrizing message/to could clone `seam_modules_for_tree_allowlist` as the "live reach mechanism" and reintroduce the #446 reach-as-hidden-constant defect (a pattern to clone is a defect to clone) |
| e | LATENT double-arm `__wrapped__` re-entry (§PHASE 2b) — unreachable today | **GO, pin the bound** | optional: a named-bound pin (RED the day a test both re-arms the guard AND registers the observer), per WHEN-YOU-CANNOT-CLOSE-A-HOLE. Not urgent (structurally unreachable now) |

Why none is a NO-GO: a NO-GO requires "a real defect with a repro." Every item above is dead code
with **0 consumers** (proven by `lore_impact` + the textual sweep) and passes every gate; (e) is
structurally unreachable in the suite. The mechanism is correct and mutation-proven.

---

## PHASE 5 — ALLOWLIST RECONCILIATION VERDICT (lead's direct fix)

The new `_ALLOWED_WHOLE_TREE_CLONE_FILES` entry for `test_memory_enforcement_63b_ia.py`
(`test_ast_reach_helpers.py:935`) is **LEGITIMATE**. Verified independently:
- The offending scan is `test_every_entry_pin_is_a_defined_test` (contract file `:1531`). It does
  `Path(__file__).resolve().parent` (= the TEST dir) `.glob("test_*.py")` then `ast.parse`s each to
  ENUMERATE `def test_*` names, verifying every `MEMORY_TREE_ALLOWLIST` entry's `pin` exists. It
  parses NO production/workspace source — a **TEST-TREE enumeration**, NOT a masked whole-tree
  production-parser clone.
- It is the SAME class as its allowlisted siblings: `test_memory_enforcement_63a_iv.py` /
  `_63a_v.py` (`_defined_test_names`) and `test_governed_routing_63a.py` (`_behaviourally_observed_verbs`)
  — all test-dir enumerations. `parse_production_trees` (the shared production parser) scans the
  members' package roots, not the test tree, so it genuinely cannot express this reach.
- The re-open trigger is valid and machine-honest: "if this scan ever parses a workspace-.py
  PRODUCTION source" → it becomes a real adopter and migrates. The dead-entry pin
  (`test_no_unallowlisted_whole_tree_parser_clone_survives` §DEAD-ENTRY leg) strikes it if it
  stops matching. Confirmed green in the full suite (`test_ast_reach_helpers.py` passes at `81250d8`).

---

## Bottom line
**GO.** The F5 effect-based root fix is correct and complete for the memory instance: detection is
a verb/shape-agnostic state diff, the exempt channel is four independent legs, the population set
and coverage are checked variables, and #454 re-entry is closed in the mode the observer runs. All
four gates are independently green at `81250d8`, and the two central mechanisms are mutation-proven
to discriminate. The residuals are dead-code / prose-currency cleanups (4 dead helpers, 2 stale
docstrings, 1 DRY dedup, 1 latent-bound pin) — recommend they be cleaned WITHIN this F5 wave
(don't-kick-the-can; residual (d) has a concrete reintroduction risk for ii-a), none blocking.
