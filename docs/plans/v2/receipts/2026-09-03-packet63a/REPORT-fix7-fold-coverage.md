brief-base v14 read

# REPORT — fix7-fold-coverage (packet 63a fix wave, finding #452)

## SUMMARY BLOCK
- receipt: `brief-base v14 read`
- state: **done**
- deviations:
  - The brief's triage ("register the new slices in the fold-coverage MAP") rests on a mental model that does not match the guard: **there is NO hand-list map** — `_schema_fold_guard.py` is fully AST-DERIVED (per CLAUDE.md INSTRUMENT-0 / registration_sites law). Registering into a hand-list would REGRESS the guard. The real, non-weakening fix is a **derivation change**: make fold-coverage a *rooted transitive closure* so a nested sub-slice folded via a folded parent is recognized. Disclosed & argued in §"The reconciliation".
  - The brief over-enumerated the offending slices: only **`_governed_index_statements`** is uncovered. `_governed_field_specs` is not a slice (returns `tuple[...]`, not `_*_statements`/`list[str]`); the `keep.key` "slice" is a `_unique_index(...)` *statement* inside the already-covered `_keep_statements`. Neither needs action. Evidence in §"Triage — the real defect is narrow".
  - Used the granted `test_schema_fold_coverage.py` to add **discrimination tests** (not a map) pinning the new transitive-but-rooted semantics. Disclosed in §"New discrimination pins".
- Packages considered: none — no new external mechanism specified (pure-stdlib `ast` graph traversal; see DRY ledger).
- Reuse ledger: 1 new symbol (`_reachable_slices`), dispositioned HAND-ROLLED (see §"DRY ledger").
- Graded: N/A — this is a build, not a verdict pass.
- decisions-needed: none (the deviation is a corrected method, not a fork requiring a ruling; flagged for the cold audit's confirmation).
- receipt POINTERS: RED-before §"RED-before"; GREEN-after §"GREEN-after"; the guard edit `loremaster/tests/_schema_fold_guard.py::_reachable_slices` / `derive_folded_slices` / `derive_standalone_slices`; mutation-proof honesty §"Mutation proofs stay honest".

---

## RED-before (at HEAD `278f524`)
```
FAILED …::TestFoldCoverageMutationProofsOnRealSource::test_removing_a_real_variable_returning_fold_call_reds_the_scan
FAILED …::TestFoldCoverageOnRealSchema::test_the_real_schema_has_zero_fold_coverage_findings
FAILED …::TestFoldCoverageMutationProofsOnRealSource::test_removing_a_real_fold_call_reds_the_scan
FAILED …::TestFoldCoverageOnRealSchema::test_every_folded_and_standalone_name_is_a_real_slice_fn
4 failed, 25 passed in 4.48s
```
Root scan output at HEAD: `scan_schema_fold_coverage(real_source)` → `[FoldFinding(slice_fn='_governed_index_statements')]`.
The two `TestFoldCoverageMutationProofs…` failures are collateral: their **positive control** `assert _scan_fold_fn()(_SUBJECT_SOURCE) == []` fails because the real source is not clean at HEAD.

## Triage — the real defect is narrow
Full scan at HEAD `278f524`: `scan_schema_fold_coverage(real_source)` → exactly one finding,
`_governed_index_statements`. The by-name (30) and by-shape (30) derivations AGREE, so INSTRUMENT-0
is not tripped — the slice is *seen*, just not *covered*.

Why: `_governed_index_statements(table)` (surreal_schema.py `_governed_index_statements`) is a
parameterized shared emitter (design §4.1: the two governed READ indexes on `scope` /
`owner_principal`, reused across governed tables). It is called **only** inside
`_memory_statements` (surreal_schema.py `_memory_statements`, the `statements += _governed_index_statements(MEMORY_TABLE)` line),
which is itself BOTH folded into `generate_ddl` AND standalone via `generate_memory_ddl`. So its
statements genuinely RUN — the guard's one-level (direct-call) coverage model produced a **false
positive** on a legitimately-covered nested sub-slice. This is a NEW code shape 63a introduced (the
first `_*_statements` slice that calls another `_*_statements` slice); the standing invariant
predated it.

The other two items in the brief's triage are **not slices** and need no action:
- `_governed_field_specs` returns `tuple[tuple[str,str,str], ...]` — it matches NEITHER the
  `^_[a-z0-9_]+_statements$` name predicate NOR the `-> list[str]` shape oracle, so it is invisible
  to both derivations. Not a slice fn. (It's a spec table consumed via `_define_field`.)
- The `keep.key` slice: there is no separate slice fn — `keep`'s unique key index is a single
  `_unique_index(KEEP_TABLE, f"{KEEP_TABLE}_key", ("key",))` **statement** emitted inside
  `_keep_statements` (surreal_schema.py line 2226), which is already folded + standalone.

## The reconciliation (a DERIVATION change, NOT a map registration)
There is **no hand-list map** to register into — the guard is fully AST-derived, exactly per
CLAUDE.md INSTRUMENT-0 / registration_sites law ("prefer converting a hand-list into a derived
one"). Adding a `_STANDALONE_SLICES = {...}`-style literal would be the seventh instrument-defeat.
So the correct, non-weakening fix is to broaden the coverage RELATION from a one-level direct check
to a **rooted transitive closure**:

- New helper `_schema_fold_guard._reachable_slices(defs, slices, start)` — BFS over slice-fn call
  edges, intersecting with the real slice set at every hop (phantom-call safe).
- `derive_folded_slices` now returns the closure reachable from `generate_ddl` (direct OR through a
  nested slice fn).
- `derive_standalone_slices` now maps each slice reachable from some `generate_*_ddl` to the set of
  those generators whose closure reaches it.
- `scan_schema_fold_coverage` is UNCHANGED (`covered = folded | standalone`).
- Module docstrings + the contract's PROPERTY (a)/(b) updated so the prose matches the behavior
  (CLAUDE.md "prose must be DERIVED from behavior").

**Why this is a broadening, not a weakening (the SAFE-direction argument):** the closure is ROOTED
at real entry points. A slice reachable ONLY through a slice that is itself unreachable from an
entry point stays UNCOVERED (flagged). So the change removes a real false positive (nested folds)
without admitting any slice whose statements never run — no new false-clear, which is the only
dangerous direction for a coverage guard.

## New discrimination pins (uses the granted test file, for pins — not a map)
Added to `test_schema_fold_coverage.py` so the new semantics cannot be silently reverted (CLAUDE.md
"a fix without an invariant is half a fix"):
- fixture `_nesting_slice_src(name, child)` — a slice that folds a nested child (the 63a shape).
- `TestFoldCoverageStructuralDiscrimination.test_a_nested_slice_folded_via_a_folded_parent_is_not_flagged`
  — the positive case (nested child under a folded parent is covered).
- `TestFoldCoverageStructuralDiscrimination.test_a_nested_slice_whose_parent_is_unfolded_is_flagged`
  — the ROOTED-NESS discriminator. Asserts `flagged == {parent, child}`. Proven to red the wrong
  ("unrooted") build: an unrooted closure ("covered = called by anything") false-clears the child
  (flags only `_deadparent_statements`); the rooted closure flags both. Receipt in §"Mutation
  proofs stay honest".

## DRY ledger
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_schema_fold_guard._reachable_slices` | lore_search "transitive reachability closure of function calls over AST, BFS graph traversal of called names" | `graph.blast_radius` (whole-INDEX live-graph traversal — different input contract) and `test_ast_reach_helpers` (uncollectable test module, whole-workspace tree) | **HAND-ROLLED** — a single-module *source-string* AST traversal over this guard's own slice set; reuses this module's `_called_names`. Same divergence the existing `_called_names` docstring already records for its twin. |

## GREEN-after
```
uv run python -m pytest -q -n auto loremaster/tests/test_schema_fold_coverage.py
...............................                                          [100%]
31 passed in 4.43s
```
All 4 originally-RED node ids now GREEN, plus 25 pre-existing + 2 new discrimination pins = 31.
The 4 target ids specifically:
- `TestFoldCoverageOnRealSchema::test_the_real_schema_has_zero_fold_coverage_findings` — GREEN
- `TestFoldCoverageOnRealSchema::test_every_folded_and_standalone_name_is_a_real_slice_fn` — GREEN
- `TestFoldCoverageMutationProofsOnRealSource::test_removing_a_real_fold_call_reds_the_scan` — GREEN
- `TestFoldCoverageMutationProofsOnRealSource::test_removing_a_real_variable_returning_fold_call_reds_the_scan` — GREEN

## Mutation proofs stay honest
Verified INDEPENDENTLY (direct probe, not just via the passing tests) that the two real-source
mutation legs redden because a real fold removal ORPHANS the slice — not because the fix weakened
them:
- positive control: `scan_schema_fold_coverage(real_source) == []` (clean); `_governed_index_statements`
  now in BOTH the folded closure (via `_memory_statements`) and standalone (via `generate_memory_ddl`).
- MUTATION 1 — drop `    statements += _snapshot_statements()\n` from `generate_ddl` → flagged
  `{_snapshot_statements}`. `_snapshot_statements`'s ONLY caller is `generate_ddl` (no nested caller,
  no `generate_*_ddl`), so the transitive closure cannot mask its removal. Honest.
- MUTATION 2 — drop `    statements += _trace_statements()\n` → flagged `{_trace_statements}`. Same
  single-caller property. Honest.
- The `_snapshot`/`_trace` fold-only guards (`test_a_fold_only_slice_is_not_also_standalone`,
  `test_the_variable_returner_mutation_target_is_fold_only`) stay GREEN under transitive standalone —
  neither is reachable from any `generate_*_ddl`.

New-pin mutation proof (the rooted-ness leg): a deliberately UNROOTED wrong build
(`covered = any slice called by any slice/generator`) flags only `_deadparent_statements` —
false-clearing `_lonelychild_statements`. The correct rooted closure flags `{_deadparent_statements,
_lonelychild_statements}`. So `test_a_nested_slice_whose_parent_is_unfolded_is_flagged`
(asserting `== {both}`) reds the wrong build → the pin discriminates.

## Files changed (symbols, not line numbers)
- `loremaster/tests/_schema_fold_guard.py`: NEW `_reachable_slices`; `derive_folded_slices`,
  `derive_standalone_slices` rewritten to rooted transitive closures; module docstring
  (WHAT IT GUARDS + THE TWO LEGS PRIMARY) updated.
- `loremaster/tests/test_schema_fold_coverage.py`: NEW fixture `_nesting_slice_src`; NEW pins
  `test_a_nested_slice_folded_via_a_folded_parent_is_not_flagged`,
  `test_a_nested_slice_whose_parent_is_unfolded_is_flagged` (in
  `TestFoldCoverageStructuralDiscrimination`); PROPERTY (a)/(b) prose updated for #452.
- **Production schema code (`surreal_schema.py`): UNCHANGED.** No STOP-and-flag was required — the
  reconciliation lives entirely in the guard + contract.

## Gates NOT run (per brief)
ruff / typecheck / currency-gate / full suite were NOT run (brief scope). Scoped suite only.
A cold audit should confirm the reconciliation is a real broadening (not a hack-to-green) and
re-run typecheck/ruff over the two touched test-support files.

## Store-reference citation
No store schema / DDL / migration was touched. The fix is confined to the test-support guard
(`loremaster/tests/_schema_fold_guard.py`) + its contract. `docs/reference/surrealdb-31-capabilities.md`
consulted for context on WHY `_governed_index_statements` is a separate parameterized emitter
(§1.1 index `IF NOT EXISTS` never OVERWRITE; §4.1 governed columns) — cited, not re-transcribed.
