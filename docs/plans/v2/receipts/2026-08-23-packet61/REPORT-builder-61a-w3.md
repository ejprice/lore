# REPORT-builder-61a-w3

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done** — full suite **8495 passed / 0 failed** (§Gates)
- deviations:
  - M2 mutation-proof declared RED set was re-declared 2→3 after the harness caught a real,
    understood extra consequence (literal-only `_emits` blinds the PROSE leg too, since
    `_keep_statements` is a variable-returner) — NOT a peek-and-transcribe; mechanism in §Mutation proofs.
  - Small clean refactor of production guard: extracted `_assert_reach_or_raise` so INSTRUMENT-0's
    fail-closed logic has one home (also gives M3 a single clean anchor). Contract stayed 29-green.
- Packages considered: none — no mechanism specified (pure-stdlib `ast`/`re`; the scan is a source/AST
  structural guard, no library candidate. §"Packages" below.)
- Reuse ledger: 1 new reusable helper dispositioned HAND-ROLLED (with query); the rest are guard-private. §DRY ledger.
- Graded: f87e77402fd65bf5e2c8b1c538389ee51dfa13ad · HEAD-at-report: f87e77402fd65bf5e2c8b1c538389ee51dfa13ad · SAME
- decisions-needed: none
- receipt pointers:
  - guard module: `loremaster/tests/_schema_fold_guard.py` (md5 `31d548eaec69938ef22542071fc2d29a`, 330 lines)
  - contract (unchanged — the spec): `loremaster/tests/test_schema_fold_coverage.py` — 29 passed
  - scope-adjacent cleanup: `test_principal_keys_schema.py` docstring (the `# ⚠ STUB surfaces exist` sentence) — SEPARATE one-concern change, lead commits separately citing #398/#399
  - mutation-proof instrument: `scripts/mutation_proof.py` (committed repo tool; exact invocations pasted in §Mutation proofs)

## What I built
The invariant scan the contract references, in the dedicated home `loremaster/tests/_schema_fold_guard.py`
(the first of the contract's `_GUARD_HOMES`). Every public symbol the contract's lazy accessors reach:

| symbol | what it is |
|---|---|
| `scan_schema_fold_coverage(source) -> list[FoldFinding]` | PRIMARY structural leg; FAILS CLOSED via `_assert_reach_or_raise` |
| `scan_stale_emptiness_prose(source) -> list[ProseFinding]` | BACKSTOP prose leg (KNOWN BOUND) — docstring + leading-comment |
| `derive_slice_fns(source) -> set[str]` | BY-NAME derivation (`^_[a-z0-9_]+_statements$`) |
| `derive_statement_emitters(source) -> set[str]` | INDEPENDENT BY-SHAPE oracle (private top-level `-> list[str]`) |
| `derive_folded_slices(source) -> set[str]` | slice-fn names called in `generate_ddl` (∩ real slices) |
| `derive_standalone_slices(source) -> dict[str, set[str]]` | slice → the `generate_*_ddl`(s) that call it |
| `KNOWN_EMPTINESS_PHRASES: frozenset[str]` | the CLOSED phrase set (KNOWN BOUND) |
| `SchemaGuardReachError(Exception)` | fail-closed / reach-divergence signal |
| `FoldFinding` / `ProseFinding` | frozen dataclasses; `.slice_fn`; `__str__` names slice + `generate_ddl` |

It is a **pure function of module SOURCE TEXT** — `ast.parse` for structure + raw-line inspection for the
leading comments the AST discards. No import of the subject's functions, no live SurrealDB connection
(store law read; this contract touches no DDL execution — it reasons ABOUT the DDL emitters). One code
path grades the real module and every synthetic fixture / mutation copy.

### The derived slice-fn convention (confirmed, not assumed)
Re-derived at f87e774 by AST (`ast.parse` over `surreal_schema.py`):
- **28** top-level `def` match `^_[a-z0-9_]+_statements$` (by-NAME).
- **28** top-level PRIVATE defs annotated `-> list[str]` (by-SHAPE) — the SAME 28 (no divergence,
  so `test_name_and_shape_derivations_agree_on_the_real_schema` is green; INSTRUMENT-0 positive control).
- `generate_ddl` folds **16**; the other **12** are consumed by a standalone `generate_*_ddl`
  (`generate_manifest/memory/task/finding/principal/principal_key/agent/brief/message/graph/floor_calibration/lease_ddl`).
  Slices NEITHER folded nor standalone: **[]** → the real-schema scan returns `[]` (green gate).

### How `_emits` handles BOTH return idioms (the adversary's blocker)
`_emits(fn) = not _is_provably_empty(fn)`, where `_is_provably_empty` is TRUE only when the body —
docstring stripped — is EXACTLY a single `return []` (empty-list literal, the RED-STUB shape). Therefore:
- `return [literal, ...]` (8 of 28 real slices, e.g. `_file`/`_snapshot`) → EMITTING.
- the house `statements = [...]; …; return statements` **variable idiom** (20 of 28, e.g. `_trace`/`_chunk`) → EMITTING
  (body is not a lone `return []`).
- a genuine RED-STUB `return []` (with or without a docstring) → NOT emitting (exempt at RED time).
This is CONSERVATIVE in the only safe direction: it can over-flag an exotically-empty slice (harmless —
folding `[]` is a no-op) but can NEVER false-clear a real emitter. A literal-only `_emits` — the adversary's
closed blocker — is proven RED by mutation M2 below.

## Gates (receipts)
- **Contract file** `test_schema_fold_coverage.py -n auto` → **29 passed in 4.34s** (all 29 pins green).
- **Contract + edited test file** together → **61 passed in 4.72s**.
- `./scripts/typecheck.sh` → **exit 0**, `error-lines: 0` (all members incl. test trees + shellcheck).
- `uv run ruff check .` → **All checks passed!**
- **Full suite** `loremaster/tests -n auto` → **8495 passed, 50 skipped, 3 xfailed, 0 failed** in 280.72s (exit 0). Zero failures ⇒ the #405 SOLO re-run caveat does not apply (it triggers only on scattered out-of-scope failures; there were none).

## Mutation proofs (via `scripts/mutation_proof.py` — declares expected-RED BEFORE the run, diffs BOTH ways, restores byte-exact)
Every leg mutates the PRODUCTION guard (`_schema_fold_guard.py`), watches the exact declared pins go RED,
and the harness restores the file byte-exact (final md5 `31d548eaec69938ef22542071fc2d29a`, unchanged).

| # | leg | mutation | declared RED (fired EXACTLY) | verdict |
|---|---|---|---|---|
| M1 | **structural fold-coverage** | `derive_folded_slices` → `return slices` (everything "folded") | 6 pins: `test_an_unfolded_nonempty_slice_is_flagged`, `…_variable_returning_slice_is_flagged`, `test_the_finding_names_the_offending_slice_and_its_reason`, `test_removing_a_real_fold_call_reds_the_scan`, `test_removing_a_real_variable_returning_fold_call_reds_the_scan`, `test_the_scan_is_rederived_per_call_not_cached` | **HELD** |
| M2 | **`_emits` literal-only** (adversary blocker) | `_is_provably_empty`: `if len(body)!=1: return False` → `return True` (variable-returner treated empty) | 3 pins: `…_variable_returning_slice_is_flagged`, `test_removing_a_real_variable_returning_fold_call_reds_the_scan`, **`test_reintroducing_stale_prose_on_a_real_folded_slice_reds_the_prose_scan`** | **HELD** |
| M3 | **INSTRUMENT-0 fail-closed** | drop the `_assert_reach_or_raise(by_name, by_shape)` call | 2 pins: `test_a_misnamed_emitter_fails_the_scan_closed`, `test_a_wholesale_convention_rename_fails_the_scan_closed` | **HELD** |
| M4 | **prose leading-comment** | `_leading_comment_block` → `return ""` | 1 pin: `test_reintroducing_stale_prose_on_a_real_folded_slice_reds_the_prose_scan` | **HELD** |
| M5 | **prose docstring** (bonus — proves the docstring half) | `docstring = ast.get_docstring(node) or ""` → `docstring = ""` | 1 pin: `test_a_folded_slice_with_a_stale_emptiness_docstring_is_flagged` | **HELD** |

**M2's re-declaration is the load-bearing detail.** I first declared 2 pins; the harness's *"WENT RED but was
NOT DECLARED"* leg flagged a 3rd — the prose test. The reason is real and understood, not transcribed: the
literal-only `_emits` mutation touches the SHARED `_emits`, and the prose leg only considers *folded/standalone
AND emitting* slices, so `_keep_statements` (a variable-returner) is treated non-emitting → the prose scan
skips it → the injected comment goes unflagged. A literal-only `_emits` bug therefore blinds BOTH legs to the
20/28 variable-returning slices. Re-ran with the correct 3-pin set → HELD.

## Scope-adjacent cleanup (SEPARATE one-concern change — lead commits separately, cite #398/#399)
`loremaster/tests/test_principal_keys_schema.py` module docstring carried a LIVE stale RED-STUB claim (same
#398/#399 class, but in a TEST file — OUTSIDE the invariant's production scope, which scans only
`surreal_schema.py`). It asserted, present-tense, that `generate_principal_key_ddl` returns `""`,
`_principal_key_statements` returns `[]`, and `principal_key` is *NOT folded into* `generate_ddl`.
**Ground-truthed against HEAD:** all three are FALSE now — `_principal_key_statements` emits real DDL, is
folded into `generate_ddl` (`surreal_schema.py` line ~1722), and is consumed by the real standalone
`generate_principal_key_ddl` (which itself documents the fold). I **reframed** (not blind-deleted) the sentence
to a dated historical-origin note: past-tense for the authoring-time stub state, present-tense for the greened
reality, tagged `retired 2026-08-23, packet 61a-w3, #398/#399`. Only that sentence changed. `test_principal_keys_schema.py` still passes.

## Files touched
- **NEW** `loremaster/tests/_schema_fold_guard.py` — the invariant scan (guard-home #1). 330 lines.
- **MODIFIED** `loremaster/tests/test_principal_keys_schema.py` — docstring stale-prose reframe ONLY (separate concern).
- **NOT TOUCHED**: `test_schema_fold_coverage.py` (the contract/spec — assertions unchanged), `surreal_schema.py` (the scanned subject).

## Packages considered
none — no external mechanism specified. The scan is a pure source/AST structural guard using only the stdlib
(`ast`, `re`, `dataclasses`). No library does "AST-derive this repo's `_*_statements` fold-coverage
convention"; that is inherently bespoke to this codebase's DDL slice idiom. Nothing to `replace`.

## DRY ledger
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_called_names(fn_node)` | `lore_search "helper that collects function call names within an AST node…"` | nearest twin `test_ast_reach_helpers._call_names_in` (sim 0.64) | **HAND-ROLLED** — the twin lives INSIDE a pytest module (uncollectable as a shared import) and serves a whole-workspace tree parser (`parse_production_trees`), a different input contract than this single-module SOURCE-STRING guard. Reason recorded in the helper's docstring. |
| `derive_slice_fns` / `derive_statement_emitters` / `derive_folded_slices` / `derive_standalone_slices` / `scan_schema_fold_coverage` / `scan_stale_emptiness_prose` / `_is_provably_empty` / `_emits` / `_leading_comment_block` / `_assert_reach_or_raise` / `FoldFinding` / `ProseFinding` / `SchemaGuardReachError` / `KNOWN_EMPTINESS_PHRASES` | (same search) | no existing fold-coverage / schema-slice-derivation symbol | **HAND-ROLLED / guard-private** — these ARE the invariant the contract mints; no prior implementation exists (this is the #398/#399 recurrence guard being built for the first time). |

The guard is a single-module, source-string tool by design (the contract's "WHY SOURCE-BASED" section: one code
path grades real + fixtures). It does not clone the whole-workspace `_logging_fixtures` parser family — a
different concern (whole tree of files vs one module's source string).
