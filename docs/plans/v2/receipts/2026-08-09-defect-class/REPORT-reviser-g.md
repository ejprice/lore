brief-base v10 read
brief project v7 read

# REPORT-reviser-g — INSTRUMENT G contract revision (add adversary-g missing pins MP-1..MP-5 + R1)

## SUMMARY BLOCK
- **state: done.** `scripts/test_wave_gate.py` grew from **15 → 29 pins**; all 5 adversary-g
  wrong builds now caught, R1 satisfiability trap fixed. Contract stays RED-first (right reason).
- deviations: none. Edited ONLY `scripts/test_wave_gate.py` (writable set honoured); no other file touched, no git state mutated.
- **Packages considered:** none — no mechanism specified. This is contract TESTS that COMPOSE in-repo `pending_contract_gate` machinery (reused `_render_currency`, `_run_selected_gates`-as-spy-target, `GateManifest`/`PendingContractRegistry`/readers, run-types) + stdlib `ast`/`tempfile`/`types.SimpleNamespace`. Nothing hand-rolled (ONE IMPLEMENTATION); the §9.6 REUSE MAP shapes are reused, not reinvented.
- **Graded:** `962eeb6b88385106ba440c06ca7c6adac67704e3` · HEAD-at-report: `962eeb6` · SAME. (`scripts/test_wave_gate.py` is UNTRACKED at HEAD — the working-tree contract file; `wave_gate.py` deliberately unbuilt.)
- **Provenance (#140):** reference-build satisfiability run in `scripts/scratch_copy.sh`-asserted scratch `/home/ejprice/scratch-reviser-g2`; `loremaster.__file__` → `/home/ejprice/scratch-reviser-g2/loremaster/loremaster/__init__.py` (INSIDE scratch).
- decisions-needed (2): (D1) MP-2 pins the seam `pending_contract_gate._run_selected_gates` as the ONE reader `main` must route through — enforces §9.6 DRY leg-5 reuse; a builder using a differently-named equivalent must reconcile. (D2) MP-3's checkpoint control asserts a clean FULL checkpoint receipt DOES carry "every claimed gate is GREEN" — couples checkpoint wording to the machinery it wraps (`_render_currency`), which the contract already mandates mirroring. Both are the design's intent; flagged, not silently chosen.
- receipt POINTERS: new pins in `scripts/test_wave_gate.py` §"7. The ENTRYPOINT enforces…"; R1 in `_verdict_line` + `_ROSTER_HEADER`; satisfiability + wrong-build RED table §RECEIPTS below.

---

## What was added (each new pin → the MP-N / wrong-build it closes → RED confirmation + reason)

Applying design doc `docs/plans/v2/design/2026-08-09-defect-class-prevention.md` §9 (IDIOM 1/2/3 + companion laws + §9.6 REUSE MAP). Every wrong build below was CONSTRUCTED from the adversary's reference (`/tmp/wave_gate_REFERENCE.py`) with a targeted mutation and run against the FULL contract in scratch — confirming it no longer survives.

| new pin(s) | MP / idiom | wrong build closed | RED confirmation (right reason) |
|---|---|---|---|
| `test_main_exit_code_reflects_the_bundle_verdict` (4 params) | **MP-1 BLOCKER** · IDIOM 2 (drive real `main`, assert EXIT CODE via gate-runner spy) | **W-main-noop** (`main` runs no gates, returns 0) | `[checkpoint-orphan-fails]` + `[wave-scoped-failure-fails]` RED — `main` returned 0 where the bundle must be red |
| `test_main_routes_through_the_one_manifest_reader` | **MP-2** · IDIOM 1 SHARING (spy `_run_selected_gates` called once with `manifest.ids`) | **W-main-noop** & **W-DRY-reparse** | RED — spy recorded 0 calls (didn't route through the ONE reader) |
| `test_wave_gate_does_not_reparse_the_manifest_itself` (AST) | **MP-2 belt** | **W-DRY-reparse** (private `yaml.safe_load` of gates.yaml) | RED — AST found a `yaml.safe_load` call (a 2nd manifest reader) |
| `test_wave_scoped_summary_never_reads_as_a_full_currency_clear` | **MP-3** · IDIOM 3 (whole-receipt honesty, DERIVED token) | **W-B** (SCOPED pytest line + over-claiming summary) | RED — "`CURRENCY : PASS — every claimed gate is GREEN or OWNED`" present in a wave-scoped receipt; fails on the over-claim assertion, NOT the `wave_ok` precondition (verified) |
| `test_every_mode_gate_cell_fails_on_a_red` (3 params) + `test_fail_matrix_gate_set_equals_the_live_manifest` | **MP-4** · IDIOM 1 ∀ over (mode × gate), both-direction coverage diff | **W-ruff** (ruff advisory/scopable in wave) | `[ruff]` RED — a red ruff in wave was waved through (ok=True); the (wave, ruff) cell no longer slips |
| `test_wave_scoped_selector_echo_equals_the_source` (3 params) | **MP-5** · companion monoculture (§9.4) | **W-echo** (hardcoded echoed selector) | `[test_totally_different_area]` + `[not (slow or flaky)]` RED — hardcode `-k test_changed_area` cannot match a 2nd value; the original single value still passes (proving it WAS a monoculture) |
| `_verdict_line` + `_ROSTER_HEADER` (R1) | **R1** satisfiability trap | a DRY-faithful builder reusing `GateCurrency.render()` NOT_RUN text | fixed: roster header now excluded by PREFIX, not by any "manifest" substring — a NOT_RUN line naming the manifest is no longer filtered out (would have failed W2 opaquely) |

**§9.6 REUSE MAP symbols reused (generalise, don't invent):**
- **IDIOM 2 wire/effect spy** → spy on `pending_contract_gate._run_selected_gates` (the ONE derived leg reader); reach-safe across from-import AND module-attr spellings (the §9.7 single-module-monkeypatch defect avoided — see below).
- **IDIOM 3 summary honesty** → net-new (design confirmed "none found"), but the forbidden token is **DERIVED from `_render_currency`'s own output**, not hand-typed — principle-backed by CLAUDE.md "render from typed applicability, never a name compared".
- **IDIOM 1 coverage / both-direction diff** → reused the `test_backoff_seam._DECLARED_SITES` SHAPE (`missing = live − declared`, `undeclared = declared − live`, fail-closed) per-instrument, recomputed LIVE from the canned manifest — NOT the tree-scan helper (that would be §7 over-consolidation).
- **∀-mutation reach** → the (mode × gate) parametrized set is `_canonical_manifest_ids()`, DERIVED live from `_manifest` at collection; the coverage pin makes that reach a CHECKED VARIABLE (§9.1 META-RECURSION).

**Satisfiability (C-DEF):** reference build → **29 passed, 0 failed** (was 15) in provenance-asserted scratch. RED honesty preserved: with no `wave_gate.py`, collection errors `ModuleNotFoundError: No module named 'wave_gate'` at the `importlib.import_module` line (contract-first RED, right reason). Contract's own gates: **mypy Success** (strict, `MYPYPATH=scripts`) · **ruff clean**.

---

## Key construction decisions (the traps avoided, so the pins discriminate)

### The from-import trap (§9.7) — why the spy is installed in BOTH namespaces
The natural/reference spelling is `from pending_contract_gate import _run_selected_gates`, which binds the name into `wave_gate`'s OWN module dict at import time. A `monkeypatch.setattr(pending_contract_gate, "_run_selected_gates", …)` alone would NOT reach `main` — the exact single-module-monkeypatch defect adversary-asub-b named. `_install_reader_spy` patches BOTH `wave_gate._run_selected_gates` (reaches the from-import adopter) AND `_pcg._run_selected_gates` (reaches a `pcg._run_selected_gates` adopter); the SAME spy records into one list, so the call count is honest regardless of spelling. The loaders (`GateManifest.load` / `PendingContractRegistry.load`) are patched on the CLASS (shared object) so one setattr reaches `main` whatever the import spelling — a class-attribute patch cannot be dodged by a from-import.

### Hermetic entrypoint driving (no weather)
MP-1/MP-2 drive the REAL `main` but patch the loaders to a CANNED manifest + EMPTY registry and spy the gate execution, so `main` never reads the real `gates.yaml`/`pending_contracts.yaml` and never shells out — asserting the INSTRUMENT, not the tree's current health. ruff's zero-tolerance (`adjudicated_by: none`) makes the orphan row robust regardless of registry.

### MP-3 token is DERIVED, not a denylist
The forbidden "unqualified pass" token is extracted from `_render_currency`'s own all-green output (the exact string a path-of-least-resistance W-B build keeps), then asserted absent from the wave-scoped receipt. Both directions checked: a clean FULL checkpoint IS allowed the clear (control), a SCOPED wave is not. So an always-omit build fails the control and an always-include build (W-B) fails the pin. Verified the failure is the over-claim assertion, not the `wave_ok` precondition (a probe passing/failing for the wrong reason).

### MP-4 META-RECURSION proven (the ∀'s reach is a checked variable)
`_FAIL_MATRIX_GATES = _canonical_manifest_ids()` derives the parametrized gate set LIVE from the canned manifest. `test_fail_matrix_gate_set_equals_the_live_manifest` asserts that set EQUALS `manifest.ids` both directions — so a builder who hardcodes the parametrize is caught. **Proven by mutation:** hardcoding `_FAIL_MATRIX_GATES = ("typecheck","ruff")` reddens the coverage pin with `manifest gates the fail-matrix never drives: ['pytest']`. A reach that is a hidden constant is INSTRUMENT 0's seventh defeat; this makes it a variable.

---

## §RECEIPTS — commands + real output tails

**Scratch (provenance-asserted, #140):** `./scripts/scratch_copy.sh /home/ejprice/scratch-reviser-g2` →
`loremaster -> /home/ejprice/scratch-reviser-g2/loremaster/loremaster/__init__.py` (+ 3 siblings).

**Contract gates (real tree, HEAD 962eeb6):**
- `uv run ruff check scripts/test_wave_gate.py` → `All checks passed!`
- `MYPYPATH=scripts uv run mypy scripts/test_wave_gate.py` → `Success: no issues found in 1 source file`

**RED honesty (contract-first, wave_gate absent):** `uv run pytest scripts/test_wave_gate.py -q` →
`E ModuleNotFoundError: No module named 'wave_gate'` at `test_wave_gate.py:134` (`importlib.import_module`), `1 error in 0.17s`.

**C-DEF satisfiability (reference build in scratch):** `uv run pytest scripts/test_wave_gate.py -q` → **`29 passed in 0.14s`**; `--collect-only` → **29** pins.

**Wrong-build RED confirmation (each = full 29-pin contract; only the targeted pin(s) fail):**
```
W-main-noop     -> 3 failed, 26 passed  : MP-1[checkpoint-orphan], MP-1[wave-scoped-failure], MP-2
W-DRY-reparse   -> 4 failed, 25 passed  : MP-1[checkpoint-orphan], MP-1[wave-scoped-failure], MP-2, MP-2-belt
W-B (overclaim) -> 1 failed, 28 passed  : MP-3  (reason: over_claim token present, NOT wave_ok precondition)
W-ruff advisory -> 1 failed, 28 passed  : MP-4[ruff]
W-echo hardcode -> 2 failed, 27 passed  : MP-5[test_totally_different_area], MP-5[not (slow or flaky)]
META-RECURSION  -> 1 failed             : coverage pin RED on a hardcoded stale _FAIL_MATRIX_GATES
```

Every wrong build fails EXACTLY its targeted pin(s) and the reference passes all 29 — genuine discrimination, both legs (positive control + wrong-build), not a blind harness.

## Scope / verification notes
- Writable set honoured: edited ONLY `scripts/test_wave_gate.py`. No production code, no other file, no git state.
- No worktree used (standing law #134/#125 — shared single tree). Scratch is a disposable `scratch_copy.sh` tree at `/home/ejprice/scratch-reviser-g2` (provenance-asserted) — disposable by design; leaving it for the lead to reap or discard.
- lore currency: read-only session for me (I authored one untracked test file); graph-derived answers not relied on as gates. `pending_contract_gate`'s surface confirmed by LIVE import in the pytest run, not from the index. No grep-for-structure fallback (lore + direct Reads of the two named files sufficed).
