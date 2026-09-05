# REPORT-contract-63b-i-a

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- receipt: brief-base v14 read · brief project v7 read
- state: in_progress — RED contract WRITTEN + gates green + RED-at-HEAD confirmed; the C-DEF
  SATISFIABILITY RECEIPT (scratch reference build → 0-failed) is the last step (delegated).
- deviations: (none from the brief yet)
- Packages considered: none new — the instrument is bespoke test substrate over the live
  test store; stdlib only (`ast`, `contextvars`, `asyncio.Lock`, `re`). Detail at close.
- Reuse ledger (new test-substrate symbols; the instrument BODIES are the builder's — these are
  the SHAPES I named + the test-local helpers):
  | new symbol | lore query run | returned | disposition |
  |`RowDelta`/`SchemaDelta`/`ObservedEffect`| lore_get_symbol `ObservedWrite` | one flat ObservedWrite, no effect type | **HAND-ROLLED** (new §1.2 effect containers; no prior state-diff type) |
  |`TreeWriteAllowlistEntry.statement`/`.effect`/`.l1_site`| read `_governed_contract` dataclasses | fields absent | **EXTENDED** `TreeWriteAllowlistEntry` |
  |`SURREALQL_STATEMENT_KEYWORDS`+`derive_…_from_corpus`| lore_get_symbol `_raw_mutation_of_table` | bounded verb regex, no derived set | **EXTENDED** (same fn; §1.5a derived grammar) |
  |`governed_populations`| lore_get_symbol `_message_statements`/`_governed_field_specs` | emitter exists, no consumer-set walk | **HAND-ROLLED** (§1.5c-iii derivation stub) |
  |`_normalise` (whitespace collapse)| design §1.4 names a shared `normalise` | no existing collapse helper cited | **HAND-ROLLED** test-local; the builder promotes it to the substrate for the classifier (§1.4) |
  |`_effect_*` predicates / `_memory_ddl_object_names`| n/a — test-local adjudications | — | **HAND-ROLLED** (the adjudicated effect oracles; not reusable policy) |
- Graded: base `e4b8945` (current HEAD; design doc committed here). HEAD-at-report `e4b8945` · SAME.
- decisions-needed: NONE requiring an operator ruling. TWO substrate-shape decisions taken within
  contract-author authority + documented (§ "Substrate-shape decision" below), lead may veto:
  (1) the `effect` predicate takes the whole `ObservedEffect` (rows + schema delta), not the literal
  `Callable[[RowDelta], bool]` §1.4 wrote — §5.1 Q1's ensure_ready effect is a schema-delta predicate
  and one field must serve both; (2) `TreeWriteAllowlistEntry.l1_site: bool` marks a DDL/label frame
  (ensure_ready/guarded_write) that has no raw-literal L1 site so the L1 ghost-check excludes it.
  ONE builder-COORDINATION flag (not a decision): `classify_tree_observed_write`'s docstring must
  KEEP naming the #138 hand-set-label bound through the 4-leg rewrite (63a-v's R2 pin enforces it).
- pointers: contract module `test_memory_enforcement_63b_ia.py` (new); edits to
  `test_memory_enforcement_63a_v.py` (delete R4 pins + observer-patch-set pin; flip
  `_RECREATE_ENTRY.runtime_observed`); `_governed_contract.py` / `_sdk_guard.py` stub shapes.

## Reading receipts (this session, 2026-09-03, at `e4b8945`)
- Design (AUTHORITATIVE): `docs/design/2026-09-03-packet63b-design.md` §1 (1.1–1.8 in full) +
  §0 item (1) + §5.1 ADDENDUM (Q1 ensure_ready DDL frame, Q2 leg-by-leg satisfiability table,
  the i-a/i-b writable-set cut).
- Standing law (CLAUDE.md, cited by section): REACH LAW / INSTRUMENT-0 askable form / "allowlist
  the safe" / enforce-at-RUNTIME-coverage-a-CHECKED-VARIABLE; the six-defeat instrument-lesson
  table; FIXTURES MUST DISCRIMINATE ("what wrong build passes this?"); THE QUANTIFIER LAW;
  A CONTRACT SHIPS WITH A SATISFIABILITY RECEIPT (C-DEF); PROVE WHICH TREE YOU ARE TESTING
  (#140 → `scripts/scratch_copy.sh`); WHEN YOU CANNOT CLOSE A HOLE, PIN IT; A GATE NEEDS A
  THREAT MODEL.
- store-ref `docs/reference/surrealdb-31-capabilities.md` §1 (INFO FOR TABLE; DEFINE FIELD
  OVERWRITE; RELATION-table OVERWRITE), §3 (execute_transaction; statement[0]-only).
- Existing F5 substrate at HEAD via lore_get_symbol/lore_read + disk read (files I will edit):
  `tests/_sdk_guard.py` (install/`_guarded`/`_judge`/`SDK_CONNECTION_CLASSES`/`GuardReport.
  require_observations`/`observed_call_sites` — NO hook seam today), `tests/_governed_contract.py`
  (the whole F5 detector: `_statement_shape`/`_raw_mutation_of_table`/`governed_table_raw_
  mutation_sites{,_in_tree}`/`ObservedWrite`/`_mutation_verb_for_table`/`observe_governed_table_
  writes`/`TreeWriteAllowlistEntry`/`classify_tree_observed_write`/`_originating_prod_site`/
  `seam_modules_for_tree_allowlist`/`exempt_entry_is_self_contained`/`exempt_frame_raw_memory_
  mutations`), `tests/test_memory_enforcement_63a_iv.py` (L2b label battery + allowlist),
  `tests/test_memory_enforcement_63a_v.py` (whole-tree allowlist + R1/R3 + R2 + R4a/R4c pins +
  the observer-patch-set pin), `tests/test_memory_enforcement_bounds_63a_iv.py` (#444 pin —
  STANDS), `loremaster/governed.py` (`write_guard`/`active_write_guard`/`governed_exempt(name)`/
  `active_exempt`/`guarded_write`), `memory/local.py` (`ensure_ready`/`_recreate_memory_table`/
  `rebuild_embeddings`/`remember`/`_replay_record`/`_reinforce`/`invalidate`/`_query`),
  `principals.py::_migrate_memory_scope`, `store/surreal_schema.py::generate_memory_ddl`.
- lore currency: `lore_index()` reports the watched root `/workspace` at git_ref `e4b8945`
  on `feat/surreal-unification` == my working-tree HEAD. Index and disk agree. Files I edit I
  read from DISK (ground truth for the bytes I change); lore used for structure/where-is.

## i-a SCOPE (per §5.1 ADDENDUM — 63b-i is SPLIT: i-a = F5 INSTRUMENT, i-b = memory fidelity)
IN (i-a): the F5 runtime root-fix INSTRUMENT only —
- §1.2 effect-based detection (state diff, not statement classification)
- §1.3 reach = the `_sdk_guard` hook (observer armed through the guard)
- §1.4 statement-scoped `governed_exempt(name, *, statement)` (four legs)
- §1.5 L1 demoted to coverage floor; derived keyword grammar; DELETE R4-a/R4-c pins; population
  set derived from surreal_schema
- §5.1 Q1 `ensure_ready` becomes an allowlisted DDL frame + the `_recreate_memory_table` flip
- §1.6 riders i–ix

OUT (i-b, later — a STOP-and-flag if i-a needs to touch these): `authorize_guarded`/`GuardedPlan`
split (#441 §2), `remember`/`_replay_record`/`_build_content` fidelity (#436 §3.1/3.2),
`memory/ledger.py` retire/delete, `server.py` recall render + `render_subject_bound` (#437 §3.3),
the F5 allowlist DATA changes for #436's widened predicates. i-a goes 0-failed against the
CURRENT memory sites (§5.1 Q2: NONE of i-a's coverage legs need #441/#436's sites).

## THE REFERENCE-BUILD SHAPE (what the builder builds; my RED pins REQUIRE it — I write NO production)
(These are the shapes my pins reference. Production edits are the builder's; I write the RED
pins + the stub SHAPES that make the contract COLLECT and fail BEHAVIORALLY, per the 63a
`governed.py`-stub precedent. The satisfiability receipt fills the bodies in a scratch tree.)

### A. `loremaster/governed.py` (PRODUCTION — builder; i-a writable "exempt API only")
- `governed_exempt(name: str, *, statement: str)` — CM; `_ACTIVE_EXEMPT` carries the pair
  `(name, statement)`; `active_exempt() -> tuple[str, str] | None` returns it.

### B. `loremaster/principals.py` (PRODUCTION — builder; `_migrate_memory_scope` only)
- module constant `MIGRATE_MEMORY_SCOPE_STATEMENT = f"UPDATE {MEMORY_TABLE} SET scope = $scope
  WHERE scope IS NONE"`, passed BOTH to `run_query(statement=…)` and to
  `governed_exempt("migrate-governed", statement=MIGRATE_MEMORY_SCOPE_STATEMENT)` — ONE source.

### C. `loremaster/memory/local.py` (PRODUCTION — builder; `ensure_ready` label + `_recreate` flip)
- `ensure_ready`: wrap its `execute_transaction(BEGIN;{ddl}COMMIT)` in `write_guard("ensure_ready")`.
- `_recreate_memory_table`: no code change beyond what the flip needs (its REMOVE is already
  `write_guard("_recreate_memory_table")`); the FLIP is a test-DATA change (below).

### D. `tests/_sdk_guard.py` (test substrate — builder writes the hook seam; §1.8)
- `CallEvent(method, connection, args, kwargs, site, original)` (frozen dataclass).
- `CallHook = Callable[[CallEvent, Any], Any]`; module-level `_CALL_HOOKS: list[CallHook]`.
- `install`'s `_guarded`, AFTER `_judge()`: `coro = original(self,*a,**k); for h in _CALL_HOOKS:
  coro = h(CallEvent(...), coro); return coro`. `install()` stays autouse + hook-agnostic.
- A raising hook is NOT swallowed (loud) — §1.8 pin.

### E. `tests/_governed_contract.py` (test substrate — builder writes the effect detector)
- `RowDelta(id, kind ∈ {created,updated,deleted}, changed_columns, before, after)`;
  `SchemaDelta(added, removed, changed)` over `INFO FOR TABLE` (fields/indexes/events),
  `.is_empty` property; `ObservedEffect(row_deltas: list[RowDelta], schema_delta: SchemaDelta)`.
- `ObservedWrite` WIDENS: `label`, `exempt: tuple[str,str]|None` (the (name,statement) pair),
  `origin_site`, `statement` (evidence), `effect: ObservedEffect`. `verb`→the effect KIND(s).
- `observe_governed_table_writes(table)` keeps its NAME + CM contract; BODY becomes "register
  `table` as a governed population with the guard hook, arm the observer's hook into
  `_sdk_guard._CALL_HOOKS`, yield the observed list; on exit deregister + unarm". The observer
  hook, per SDK call: read `active_write_guard()`/`active_exempt()`/attributed site; before-diff
  (SELECT * + INFO FOR TABLE via `event.original`), await, after-diff, record iff the diff is
  non-empty. ONE `asyncio.Lock` across before→call→after (serialised attribution). `extra_modules`
  param + `seam_modules_for_tree_allowlist` + `_module_for_repo_relative_file` RETIRED.
- `TreeWriteAllowlistEntry` gains `statement: str` (the GOLDEN, whitespace-normalised) and
  `effect: Callable[[ObservedEffect], bool]` (the adjudicated effect predicate). `exempt_name`
  stays; `runtime_observed` stays (only `_recreate` flips to True).
- `classify_tree_observed_write(observed, allowlist)` becomes 4-leg for exempt, effect-checked
  for labels (§1.4). `normalise(s)` = whitespace collapse (a shared helper).
- `SURREALQL_STATEMENT_KEYWORDS`: a committed constant DERIVED from the `surrealdb-docs` tier
  `…/statements/` page names; `_raw_mutation_of_table` takes its keyword set from it + the
  operand-adjacency grammar (§1.5a). A currency pin reds on drift / operand-less keyword.
- `governed_populations()` — derived from `surreal_schema`: {t : t's DDL slice calls
  `_governed_field_specs`} ∪ {relation tables whose IN/OUT is in that set}. At HEAD = {memory}.

## PIN FAMILIES (the RED contract — new module `test_memory_enforcement_63b_ia.py`)
1. §1.2 EFFECT detection — behavioural battery + self-attack table (rows constructible):
   verb-agnostic (INSERT..ON DUPLICATE/CREATE/RELATE observed), shape-agnostic ("UP"+"DATE"),
   no-effect write not observed, gather→serialised, rollback→not landed, observer's own reads
   excluded, second governed table per-table (deferred to ii — RED_ADJUDICATED), write-then-revert
   = #138 NAMED BOUND pinned.
2. §1.3 reach = the guard — mechanism-built pin (hasattr `_CALL_HOOKS`/`CallEvent`); the DETACH
   pin (remove the observer hook → `require_observations` raises "0 observed", never green).
3. §1.4 four-leg exempt — name / golden-text (== executed == token) / effect ∀ row + empty
   schema / origin; legs 2&3 independent wrong builds; golden proven both ways.
4. §1.5 L1 coverage floor — derived grammar + currency pin; population set an OUTPUT (surprise
   site RED; new governed population w/o F5 case RED); coverage a checked variable (3 legs);
   DELETE R4-a/R4-c + the observer-patch-set pin (§1.7).
5. §5.1 Q1 — `ensure_ready` DDL frame (golden = generate_memory_ddl's own output diff, row set
   unchanged); the `_recreate` flip drives rebuild under observation and asserts the arc.
6. §1.6 riders i–ix — each a mutation proof with the exact RED-when.

## Substrate-shape decision (documented; NOT an operator fork — lead may veto)
§1.4 writes `effect: Callable[[RowDelta], bool]`, applied ∀ changed rows, with "schema delta
empty" checked by the classifier. §5.1 Q1's ensure_ready effect is instead a SCHEMA-delta
predicate ("schema delta == generate_memory_ddl()'s own diff AND row set unchanged"). Two
readings that produce different code:
- A: `effect: Callable[[RowDelta], bool]` per row + a SEPARATE `schema_effect` attribute for DDL
  frames.
- B (CHOSEN): `effect: Callable[[ObservedEffect], bool]` over the whole observed effect (rows +
  schema delta); each entry writes the predicate it needs (a row entry checks per-row + empty
  schema; the DDL entry checks schema==golden + no rows). ONE field serves both; strictly more
  general; matches the design's SEMANTICS (four legs, per-row ∀, schema-empty-or-golden).
Chosen B — it is a test-substrate API shape (my authority as contract author), documented here
so the choice is not silent. The classifier's leg-3 becomes `entry.effect(observed.effect)`.

## GATES (measured at `e4b8945`, 2026-09-03)
- `uv run ruff check` on all 4 touched files → **All checks passed!**
- `uv run mypy loremaster` → **Success: no issues found in 259 source files** (0 errors in my
  files; the loremaster leg is fully green — no pre-existing packet-39 error surfaces here).
- `uv run pytest --collect-only` on the 4 F5 modules → **56 tests collected**, exit 0 (the contract
  COLLECTS; no import/TypeError at collection).

## RED-AT-HEAD RECEIPT (`-n auto`, live test store :18000, at `e4b8945`)
- New module `test_memory_enforcement_63b_ia.py`: **17 failed, 13 passed** — every RED is a
  behavioural AssertionError / pytest.fail naming the UNBUILT fix, NOT a TypeError / parse / store
  error. The 17 RED families: effect-based detection (effect is None) · verb-agnostic (CREATE not
  observed) · shape-agnostic concat · rebuild arc unobserved · gather attribution · live-migrate not
  observed · the `_sdk_guard` hook seam unbuilt (×3: seam / detach / raising-hook) · `governed_exempt`
  has no `statement` kwarg · derived grammar (exotic verbs / operand rules / keyword-set / currency)
  · population derivation unbuilt · `ensure_ready` not a write_guard frame · §1.5c-ii coverage-as-a-
  checked-variable (every runtime_observed frame observed-with-effect under the battery — all 7
  channels missing at HEAD because `.effect` is None).
- ⚠ the §1.5c-ii coverage pin (`TestCoverageIsACheckedVariableOverTheRuntimeObservedFrames`) was
  ADDED after the refbuild worker spawned (I noticed leg (ii) was under-pinned on review — it is the
  adversary-P1c REACH-ATTACK target). It is SATISFIABLE-BY-CONSTRUCTION (the same effect observer
  that greens the arc/migrate/member pins greens it); the refbuild receipt covers it iff the worker's
  scratch copy post-dates the add — I re-verify it against the reference build at close.
- The 13 PASSES are green controls / property pins: the exempt legs 2/3/4 (the current 2-leg
  classifier rejects tuple-exempts wholesale — they DISCRIMINATE against a build missing a specific
  leg) · golden-both-ways · the three "not observed" self-attack pins (no-effect / rollback /
  write-then-revert — GREEN-VACUOUS at HEAD since `.effect` is None, each with an anti-vacuity
  control proving the state truly did/did-not move) · label-frames-excluded · recreate-runtime-
  observed (allowlist-data guard) · guarded_write label (write_guard already wired) · the
  ensure_ready effect-predicate discrimination · L1 site-backed containment · evidencing-pin.
- The migrated 63a_v/63a_iv STANDS pins + the #444 bounds pin stayed GREEN (the instrument
  replacement did not break the surviving pins). Exact split at `e4b8945`, `-n auto`:
  `63b_ia: 17 failed, 13 passed` · `63a_v: 16 passed` · `63a_iv: 9 passed` · `bounds_63a_iv: 2 passed`
  (whole set: 17 failed, 40 passed) — the ONLY reds are the 17 unbuilt-fix pins in the new module.

## FILES CHANGED (all in the §5.1 i-a writable set)
- NEW `loremaster/tests/test_memory_enforcement_63b_ia.py` — the F5 root-fix contract (single source
  of `MEMORY_TREE_ALLOWLIST`).
- `loremaster/tests/_governed_contract.py` — additive shape STUBS (RowDelta/SchemaDelta/
  ObservedEffect; widened ObservedWrite [effect/statement; exempt→`str | tuple[str,str] | None`];
  TreeWriteAllowlistEntry gains statement/effect/l1_site; SURREALQL_STATEMENT_KEYWORDS + mutation/
  read keyword sets + `derive_surrealql_statement_keywords_from_corpus` stub; `governed_populations`
  stub). NON-breaking to existing pins (all additions defaulted); the observer/classifier BODIES are
  left for the builder — my new pins RED behaviourally against the current bodies.
- `loremaster/tests/test_memory_enforcement_63a_v.py` — DELETED `TestTheAcceptedF5BoundsArePinned`
  (R4-a/R4-c), `TestTheClassifierDiscriminatesBothWays` (2-leg controls + the observer-patch-set
  meta-pin), `TestTheLiveMigrationWriteIsAttributed` (`extra_modules` leg). Re-homed the allowlist
  import; L1 ghost leg keys on `L1_ALLOWLISTED_SITES`. STANDS pins kept.
- `loremaster/tests/test_memory_enforcement_63a_iv.py` — DELETED the retired L2b label/seam battery
  method (`test_every_observed_memory_mutation_is_attributed_to_a_frame`); kept the mechanism-built
  pin + L1 + L2a + recreate-boot-admin.
- ⚠ BUILDER COORDINATION: `classify_tree_observed_write`'s docstring must KEEP naming the #138
  hand-set-label bound (63a-v's `TestTheHandSetLabelBoundIsNamedInTheInstrumentDocstring` STANDS and
  enforces it across the 4-leg rewrite).

## Progress log
- 13:44 registered; idle-gate + report stub written.
- design + full substrate + battery scaffolding read; shapes + new module + 63a migration written.
- gates green (ruff/mypy/collect); RED-at-HEAD 16-right-reason confirmed.
- next: scratch satisfiability receipt (0-failed vs a §1+§5.1 reference build, + the ruff-cleanup
  harder leg, + `loremaster.__file__` provenance) — delegated to opus48 worker refbuild-63b-i-a.
- 13:5x read brief-base v14, design §1+§5.1, standing law, store-ref, and the full F5 substrate
  (`_sdk_guard`, `_governed_contract`, `governed.py`, `memory/local.py`, `principals.py`,
  `surreal_schema.py`, the three `test_memory_enforcement_63a_*` modules).
- next: read the battery fixtures (`retrofit_world`/`_exercise_*`, `migration_world`) and write
  the contract module, then the RED-at-HEAD count and the scratch satisfiability receipt.
