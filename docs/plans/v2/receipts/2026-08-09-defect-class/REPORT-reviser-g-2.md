brief-base v10 read
brief project v7 read

# REPORT-reviser-g-2 — the ONE ∀ closing the 3 delta-survivors of INSTRUMENT G (`scripts/test_wave_gate.py`, #344)

## Capability check (tool honesty — brief-base §4, first)
Everything the brief demanded was satisfiable. Edited ONLY `scripts/test_wave_gate.py`.
`scratch_copy.sh` built a provenance-asserted copy; the delta-adversary's own reference +
its 3 survivors + the 5 originals were re-run against my revised contract there;
`lore_comms` reachable. No impossibilities. lore tools loaded via `ToolSearch "+lore"` (used
for machinery structure via direct Read of `pending_contract_gate.py`, which was the faster
path here since the delta-adversary named exact symbols — no grep fallback needed).

---

## SUMMARY BLOCK

- **State: done.** ONE ∀ over the DERIVED failure surface `(mode × gate × failure-mode ∈
  {dirty, omitted})` now drives BOTH the renderer AND `main`'s exit code, plus a POSITIVE
  scoped-marker summary pin. All 3 delta survivors (MP-6/7/8) are caught; the 5 originals
  do not regress.
- **The ONE ∀ (DRY, acceptance #1):** a single derived cell set `_RED_ENFORCEMENT_CELLS`
  (gate axis re-derived live from the manifest via `_FAIL_MATRIX_GATES`) is consumed by the
  renderer matrix, the entrypoint matrix, AND a META-RECURSION coverage pin — so growing the
  manifest grows every ∀ or reddens the coverage pin. Not three point-fixes; one surface.
- **MP-6 (headline):** `test_main_exit_equals_the_renderer_verdict_over_every_cell` drives
  the REAL `main` over every red cell and asserts `(main-exit==0) == renderer-ok` (delete-
  the-divergence, IDIOM 2). Main's exit reach is now the SAME checked variable the renderer's
  is — the exact asymmetry the delta re-grade named. Catches W-main-wave-core.
- **MP-8:** the failure-mode axis is now `{dirty, omitted}` (an ALLOWLIST derived from the
  type of `results.get(id)`, not a forbidden-set), so an OMITTED/NOT_RUN gate fails in WAVE
  mode too, at both renderer and entrypoint. Catches W-wave-notrun.
- **MP-7 (TRUST, acceptance #2, ALLOWLIST-THE-SAFE):** the 2-token deny-list pin is REPLACED
  by `test_wave_scoped_summary_positively_carries_the_scoped_bound` — the wave summary line
  must POSITIVELY carry a scoped marker (`SCOPED`/`owed`). Alternate over-claim wording then
  cannot pass: the required marker is absent whatever wording it chooses. Catches W-summary-alt.
- **Removed for DRY:** `test_wave_scoped_summary_never_reads_as_a_full_currency_clear` (the
  deny-list) and its now-orphaned imports (`cast`, `_render_currency`, `MypyRun`/`RuffRun`/
  `PytestRun`, the `_GateResults` alias). **Subsumed:** the old dirty-only
  `test_every_mode_gate_cell_fails_on_a_red` (rewritten as the ∀ over dirty AND omitted).
- **Packages considered:** none new — G composes in-repo `pending_contract_gate` machinery
  (`_run_selected_gates`, `_residuals_for`, `gate_currency`, `READERS`, `GateManifest`). The
  reference imports `_render_currency` only to prove the reuse home. Verdict = **keep/reuse**.
- **Graded:** `14b62f2f9bd0d211603895b25e5060ee88bf4716` · HEAD-at-report: `14b62f2` · SAME.
- **RED (contract-first, right reason):** real repo — `wave_gate.py` does not exist, so the
  whole file errors at collection `ModuleNotFoundError: No module named 'wave_gate'`
  (`scripts/test_wave_gate.py:143`, the `importlib.import_module` line). 1 error in 0.17s.
- **Satisfiability (C-DEF):** against the delta-adversary's independent reference (which
  derives main's exit ∀ — `main` returns `0 if ok else 1` faithfully — and carries the
  positive marker), the full revised contract → **53 passed, 0 failed** in scratch. Contract's
  own gates: `ruff` All checks passed; `mypy --strict MYPYPATH=scripts` Success (1 file).
- **Provenance (#140):** `loremaster.__file__` and `pending_contract_gate.__file__` both
  resolve INSIDE `/home/ejprice/scratch-reviser-g-2/` (asserted; receipt in §Probe record).
- **decisions-needed:** none.
- **Receipt pointers:** §"The 3 survivors now caught" (pin-by-pin), §"No regression",
  §"META-RECURSION", §"Probe record".

---

## The ONE ∀ — what it is, mechanically

The failure surface is `(mode × gate × failure-mode)`:
- **gate axis** — re-derived LIVE from the manifest each import (`_FAIL_MATRIX_GATES =
  _canonical_manifest_ids()`, unchanged from MP-4). NOT a hand-list.
- **mode axis** — `{wave_gate.MODE_WAVE, wave_gate.MODE_CHECKPOINT}` (the production constants).
- **failure-mode axis** — `_FAILURE_MODES = ("dirty", "omitted")`. This is the COMPLETE
  non-green set: `results.get(id)` is either `None` (OMITTED), a Run with residuals (DIRTY),
  or a clean Run (GREEN — not a failure). It is an **allowlist of the failure surface derived
  from the type**, not a forbidden-token list — the operator's acceptance #1 made concrete.

`_red_enforcement_cells()` builds the cross-product; `_RED_ENFORCEMENT_CELLS` /
`_ENFORCEMENT_PARAMS` are consumed by:

1. **`test_every_mode_gate_cell_fails_on_a_red`** (RENDERER leg — subsumes old MP-4, adds
   MP-8): every red cell asserts `render_wave_receipt(...) ok is False`, the gate is NAMED,
   and a non-omittable core gate is never marked SCOPED. The `omitted` cells are the MP-8 fix.
2. **`test_main_exit_equals_the_renderer_verdict_over_every_cell`** (ENTRYPOINT leg — MP-6):
   drives the REAL `main` via the existing `_install_reader_spy`, captures the EXACT ok the
   renderer returned to `main` (`_install_render_capture` wraps the module-global renderer),
   and asserts two legs — (1) `captured ok is False` for a red cell, (2) `(code==0)==captured
   ok`. Together: `main(argv) != 0` for every red cell, and a `main` that overrides the
   renderer is UNREPRESENTABLE (delete-the-divergence). `assert captured` also forces main to
   compose the ONE renderer (ONE-IMPLEMENTATION — a main that re-derives its verdict is caught).
3. **`test_enforcement_matrix_covers_every_mode_gate_and_failure_mode`** (META-RECURSION):
   `set(_RED_ENFORCEMENT_CELLS) == modes × live-manifest-gates × failure-modes`. Grow the
   manifest → the cells grow or this reddens. This is what makes main's exit reach a CHECKED
   VARIABLE, closing the P1c asymmetry the delta re-grade named (renderer had it; main did not).

Positive control: `test_main_exit_equals_the_renderer_verdict_on_a_clean_run` (both modes) —
main exits 0 and `main==renderer` in the PASSING direction, so the red matrix is not merely a
build that always fails (a main hardwired to exit 1 is caught here). P0 pos+neg pairing.

**MP-7** (`test_wave_scoped_summary_positively_carries_the_scoped_bound`): isolates the SUMMARY
line via `_summary_line` (the last PASS/FAIL line — per-gate verdicts never carry a PASS/FAIL
token, so the honest per-gate `SCOPED` line does not satisfy it), and requires the summary to
positively carry a marker from the safe set `{"SCOPED","OWED"}`. CONTROL: a clean full
checkpoint run is allowed the unqualified clear and is NOT required to carry the marker — so
this is an honesty check, not a blanket ban.

---

## The 3 survivors now caught (each rebuilt against the revised contract, in scratch)

| delta survivor | the hole (delta re-grade) | now caught by | measured |
|---|---|---|---|
| **W-main-wave-core** (main treats core reds advisory in wave → exit 0) | MP-6: main's exit ∀ was a 4-cell hand-list | `test_main_exit_equals_the_renderer_verdict_over_every_cell[wave-{ruff,typecheck}-{dirty,omitted}]` (leg 2 divergence) | **4 failed, 49 passed** |
| **W-summary-alt** (summary "all gates are clean, tree is green") | MP-7: deny-list beaten by alternate wording | `test_wave_scoped_summary_positively_carries_the_scoped_bound` (marker absent) | **1 failed, 52 passed** |
| **W-wave-notrun** (omitted gate tolerated in wave) | MP-8: NOT_RUN pinned checkpoint-only | `test_every_mode_gate_cell_fails_on_a_red[wave-*-omitted]` (renderer) **AND** `test_main_exit_equals_the_renderer_verdict_over_every_cell[wave-*-omitted]` (entrypoint leg 1) | **6 failed, 47 passed** |

Each survivor is caught by exactly its designated pin, and passes the rest — genuine
discrimination. W-main-wave-core's summary and renderer are HONEST (its bug is in `main`), so
it survives MP-7/MP-8 and is caught ONLY by the entrypoint divergence pin — proof the
main-exit ∀ is the sole discriminator for that hole, not vacuous. W-wave-notrun is caught at
BOTH the renderer and the entrypoint — the "one ∀, not three point-fixes" belt.

---

## No regression — the 5 original wrong builds stay caught

| original wrong build | still caught by | measured |
|---|---|---|
| W-main-noop | routing spy + both matrices + clean-run control | 17 failed |
| W-DRY-reparse | routing spy + AST reparse belt + both matrices | 18 failed |
| W-B (machinery over-claim summary) | **the new MP-7 positive marker** (its summary lacks `SCOPED`/`owed`) | 1 failed |
| W-ruff advisory | `…_fails_on_a_red[wave-ruff-dirty]` + `…over_every_cell[wave-ruff-dirty]` | 2 failed |
| W-echo hardcode | MP-5 monoculture selector-echo (≥2 values) | 2 failed |

W-B is now caught by the POSITIVE marker pin rather than the removed deny-list — proof the
replacement subsumes the old pin's catch. `test_main_exit_code_reflects_the_bundle_verdict`
(MP-1, kept as positive-control smoke) still fires on W-main-noop / W-DRY-reparse.

---

## META-RECURSION — the checked variable, proven both directions (on the restructured surface)

```
BASELINE (3 gates × 2 modes × 2 failure-modes):
  renderer-matrix params = 12 · main-matrix params = 12 · coverage pin PASS
DIRECTION 1 — add a 4th gate ("docs") to _manifest default:
  renderer-matrix params = 16 · main-matrix params = 16 · coverage pin PASS   (reach grew)
DIRECTION 2 — hardcode _FAIL_MATRIX_GATES = ("typecheck","ruff") stale:
  test_enforcement_matrix_covers_every_mode_gate_and_failure_mode -> FAILED
  test_fail_matrix_gate_set_equals_the_live_manifest              -> FAILED   (stale caught)
```

Both ∀ parametrizations grow with the manifest; a stale hand-list reddens the coverage pin.
The entrypoint's exit-code reach is a checked variable exactly like the renderer's.

---

## Full probe record (commands + real output tails)

**Scratch (provenance-asserted, #140):** `./scripts/scratch_copy.sh /home/ejprice/scratch-reviser-g-2`
→ `loremaster -> /home/ejprice/scratch-reviser-g-2/loremaster/loremaster/__init__.py` (+3
siblings). Receipt: `loremaster.__file__` and `pending_contract_gate.__file__` both asserted
`/scratch-reviser-g-2/`-relative (`provenance OK: both INSIDE scratch`).

**RED honesty (real repo, no `wave_gate.py`):** `uv run pytest scripts/test_wave_gate.py -q`
→ `ModuleNotFoundError: No module named 'wave_gate'` at `test_wave_gate.py:143`
(`importlib.import_module`), `1 error in 0.17s`. Contract-first RED, right reason.

**Contract own gates (real repo):** `uv run ruff check scripts/test_wave_gate.py` → All checks
passed; `MYPYPATH=scripts uv run mypy --strict scripts/test_wave_gate.py` → Success: no issues
found in 1 source file.

**C-DEF satisfiability (scratch, reference as `wave_gate.py`):** `uv run pytest
scripts/test_wave_gate.py -q` → `53 passed in 0.22s`; `--collect-only` → `53 tests collected`.

**Wrong builds (each = full revised contract, scratch):**
```
wg_main_wave_core.py   4 failed, 49 passed  -> MP-6 (main-exit divergence, wave×core cells)
wg_summary_alt.py      1 failed, 52 passed  -> MP-7 (positive scoped-marker absent)
wg_wave_notrun.py      6 failed, 47 passed  -> MP-8 renderer + MP-6 entrypoint (omitted-in-wave)
wg_main_noop.py       17 failed, 36 passed  -> routing spy + both matrices + clean control
wg_dry_reparse.py     18 failed, 35 passed  -> + AST reparse belt
wg_overclaim_B.py      1 failed, 52 passed  -> MP-7 (summary lacks scoped marker)
wg_ruff_advisory.py    2 failed, 51 passed  -> renderer + main matrix, wave×ruff×dirty
wg_echo_hardcode.py    2 failed, 51 passed  -> MP-5 monoculture selector echo
```

**P0 controls (harness sees breakage, so the reference's clears are real):** the reference
passes 53/53; every wrong build reddens its targeted pin(s); the meta-recursion stale hardcode
reddens the coverage pin; each new pin has a paired positive control (clean-run main==0;
checkpoint unqualified clear allowed). The probe harness is not blind.

---

## Residuals / notes (individual verdicts — no "the rest look fine")

- **R2 (inherited) — `test_no_hardcoded_gate_id_collection`'s `canonical` is a hand-list.**
  A hardcoded tuple of RENAMED ids would evade the AST source scan; the behavioral
  `test_render_enumerates_exactly_the_manifest_gates` is the real coverage-checked instrument
  (its docstring says so). Unchanged by this revision — INSTRUMENT 0's standing tail, met
  deliberately, not a new finding.
- **MP-1 kept intentionally.** `test_main_exit_code_reflects_the_bundle_verdict` remains as a
  4-cell positive-control smoke; the NEW `…over_every_cell` supplies the ∀ reach it lacked.
  Extra green coverage never masks — it only adds. Not a DRY violation (it reuses the same
  `_patch_loaders`/`_install_reader_spy` helpers, no cloned policy).
- **Renderer-matrix vs individual W-pins (W4/W7/etc.).** The ∀ matrix subsumes the individual
  single-cell dirty pins, but they are kept as readable single-fixture controls (the pattern
  the contract already used). Not removed — removing readable controls would trade clarity
  for nothing.
- **Scratch trees:** `/home/ejprice/scratch-reviser-g-2` (mine, provenance-asserted, cp-based
  disposable — safe to `rm -rf`) and `/home/ejprice/scratch-delta-adversary-g` (the
  delta-adversary's, source of the reference + survivors). Neither is a git worktree. Flagging
  for operator disposal per standing law; I did not delete the delta-adversary's tree.

---

## VERDICT: revision COMPLETE

ONE ∀ over `(mode × gate × failure-mode ∈ {dirty, omitted})`, DERIVED and coverage-checked,
driven at BOTH the renderer and `main`'s exit code, plus a POSITIVE scoped-marker summary pin
(allowlist-the-safe). The 3 delta survivors are caught (each by its designated pin, with
controls); the 5 originals do not regress; the reference passes 53/53; meta-recursion holds
both directions. The contract is RED in the real repo for the right reason (contract-first) and
its own ruff/mypy gates are clean.
