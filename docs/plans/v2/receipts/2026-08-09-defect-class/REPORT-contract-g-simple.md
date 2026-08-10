# REPORT-contract-g-simple

brief-base v10 read
brief project v7 read

## SUMMARY
- state: **done** — `scripts/test_wave_gate.py` rewritten to the operator-SIMPLE G/#344
  design (design §13); RED for the right reason; ruff + mypy clean.
- The fortress (§11.8–§11.11: typed-WaveReceipt / conduit-equality / branch-coverage /
  per-axis byte-oracle / `GATE_OUTCOME_VERDICTS` / MP-A·MP-B·MP-C / summary-honesty) is
  **retired** — replaced, not narrowed. File 3359→794 lines; 15 test fns (several
  parametrized). Contract surface reduced to ONE mandated name: `main(argv=None) -> int`.
- deviations: none.
- Packages considered: none — no mechanism specified (contract reuses
  `pending_contract_gate`'s existing machinery + stdlib pytest/ast/yaml).
- Graded: authored at `3249b22` · HEAD-at-report `3249b22` · SAME (no verdict on another
  agent's artifact; measurements are of my own file).
- decisions-needed:
  1. Architecture presupposed: in-process composition of `pending_contract_gate`
     (`_run_selected_gates` + `GateManifest.load`/`PendingContractRegistry.load` + currency
     logic), NOT a stdout-parsing subprocess wrapper — the SCOPED-not-GREEN override needs
     structured access to the pytest verdict. (Design §3/§13 already implies this.)
  2. Ambiguity RESOLVED-by-omission: the design specifies "no `--wave`→full" and
     "`--wave <args>`→scoped" but is SILENT on bare positionals WITHOUT `--wave`
     (`wave_gate.py foo.py`). I did NOT pin that case — a `--wave nargs="+"` CLI has no bare
     positionals; a CLI that allows them is the builder's call. Flag for the builder/lead.
  3. Flag disclaimer wording pinned to the design's verbatim `"does NOT certify the full"`
     (case-insensitive substring). A different wording is a contract renegotiation, not a
     silent builder choice.
- receipt POINTERS: pins §"WHAT WRONG BUILD WOULD STILL PASS THIS?" (module docstring,
  W1–W8) · RED tail below · gate tails below.

## What changed (file:concern)

`scripts/test_wave_gate.py` — full rewrite to design §13 (OPERATOR SIMPLIFICATION,
supersedes §11.8–§11.11). The prior working-tree file (3359 lines, uncommitted) carried the
full §11.8–§11.11 fortress; it is replaced. HEAD's committed `test_wave_gate.py` was a
957-line pre-fortress version (so `git diff --stat` vs HEAD reads +504/−667).

### The four behaviours pinned (design §13)
- **B1 — no `--wave` → FULL.** `test_main_routes_through_the_one_reader_full`: `main([])`
  routes through `_run_selected_gates` exactly ONCE, `legs == manifest.ids`,
  `pytest_args == ()` (full pytest), exit 0.
- **B2 — `--wave <args>` → core FULL + pytest scoped + honest flag.**
  - run-side: `test_wave_scopes_only_pytest_and_core_stays_full` — `legs == manifest.ids`
    (core untouched) AND `pytest_args == tuple(<args>)` VERBATIM (pass-through, no `-k`).
  - honesty: `test_scoped_receipt_is_unmistakably_scoped` (SCOPED-RUN flag echoing args +
    count + `does not certify the full`; pytest gate line NEVER GREEN; exit 0) +
    `test_scoped_flag_echoes_the_exact_args` (2 arg sets) +
    `test_scoped_flag_echoes_the_actual_test_count` (counts 7/42 — kills a hardcoded count) +
    `test_full_run_pytest_is_a_real_currency_clear` (paired NEGATIVE control: full run has NO
    SCOPED flag and renders pytest GREEN).
- **B3 — `--wave` no args → ERROR.** `test_wave_with_no_args_is_an_error`.
- **B4 — `--wave <args>` collecting ZERO tests → ERROR.**
  `test_wave_zero_collection_is_an_error` — models the real mechanism: zero collection
  surfaces as `BrokenInstrumentError` from the leg-runner (JUnitReportReader total==0 /
  GateRunner exit-5), which the bundle must NOT swallow into a scoped pass (the #290
  anti-vacuity class). Inherits existing anti-vacuity; does not demand a redundant guard.

### The #344 NON-OMITTABLE CORE invariant
- `test_main_fails_on_a_core_red[mode × gate × {dirty, omitted}]` — the gate axis DERIVED
  live from the canned manifest (`_canonical_manifest_ids()`, not a hand-list). In BOTH
  full and wave mode: a RED_ORPHANED (`dirty`, empty registry) or NOT_RUN (`omitted`) on
  ANY gate fails the bundle. This pins: typecheck/ruff currency runs full in wave mode
  (core is never advisory just because pytest is scoped — the headline #344 disease), a
  scoped pytest with real failures still fails (SCOPED downgrades GREEN only), and NOT_RUN
  fails (a subset can never read as a pass — the literal #344 event).
- DRY belts (ONE IMPLEMENTATION, priority #1): `test_main_routes_through_the_one_reader_full`
  (routes through the ONE derived leg-runner) · `test_wave_gate_inherits_the_full_manifest_
  id_set` (a 4th manifest gate reaches the runner — a hardcoded 3-list can't grow) ·
  `test_no_hardcoded_gate_id_collection` (AST, #312) ·
  `test_wave_gate_does_not_reparse_the_manifest` (AST — no second `yaml.safe_load` reader).
- `test_removed_checkpoint_mode_is_rejected` — the retired `--checkpoint` must not be a
  recognised mode.

### §11.8–§11.11 pins RETIRED (not present in the new file)
conduit-equality (main a "proven pure conduit" byte-oracle) · per-axis byte-oracle over
`SummaryVerdict`/`VERDICT_*` domains · branch-coverage (`coverage.Coverage(branch=True)`) ·
typed-WaveReceipt completeness (`SummaryVerdict`/`LegQualification`/`summary_verdict`/
`render_summary`/`SummaryLine`) · `GATE_OUTCOME_VERDICTS`/`_CLOSED_VERDICT_SET`/
`_outcome_cell_receipt` domain machinery · MP-A/MP-B/MP-C · the summary/receipt honesty
fortress · the `MODE_CHECKPOINT`/`MODE_WAVE`/`render_wave_receipt`/`pytest_args_for` mandated
surface. The new file also drops the `_summary_seam` import (the retired production-design
typed-WaveReceipt change). Honesty is now the SCOPED-RUN flag + the two errors.
(The one grep hit for "conduit" in the new file is the word in this retirement list, in the
module docstring — not machinery.)

## RED confirmation (contract-first, wave_gate unbuilt)
```
E   ModuleNotFoundError: No module named 'wave_gate'
scripts/test_wave_gate.py:151: in <module>
    wave_gate = importlib.import_module("wave_gate")
ERROR scripts/test_wave_gate.py — 1 error during collection
```
RED for the RIGHT reason: the simple `scripts/wave_gate.py` does not exist. Every test errors
at collection on the deliberate `importlib.import_module("wave_gate")` (typed `Any`, so it
plants no `type: ignore` that would flip to an orphaned red once built).

## Gate tails (my file)
- ruff: `uv run ruff check scripts/test_wave_gate.py` → `All checks passed!`
- mypy: `MYPYPATH=scripts uv run mypy scripts` → `Success: no issues found in 39 source
  files` (after annotating `_MATRIX_MODES: tuple[tuple[str, list[str]], ...]` — mypy could
  not infer the type through the empty-list branch).

## Self-check (no contract-adversary per §13): satisfiability
Walked a reasonable correct `main` (argparse `--wave nargs="+"`; load canned manifest+registry;
`_run_selected_gates(runner, manifest, manifest.ids, pytest_args)`; render currency with pytest
GREEN→SCOPED override in wave mode; catch BrokenInstrumentError→non-zero) against all 15 test
fns + parametrizations. All pass; each wrong build in the W1–W8 table is killed by a named
pin. The SCOPED marker may live ON the pytest gate line or on a separate banner — `_gate_line`
+ `_scoped_flag_line` accept both, provided a per-gate pytest line still exists (#306:
enumerate WHICH gates ran and the verdict of EACH) and is never GREEN.
