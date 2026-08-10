# REPORT-adversary-g — contract-adversary grading of `scripts/test_wave_gate.py` (INSTRUMENT G / #344)

brief-base v10 read
brief project v7 read

## Capability check (tool honesty — first, per brief-base §4)
Everything the brief demanded was satisfiable: `scratch_copy.sh` built a provenance-asserted
copy; I built reference + wrong `wave_gate.py` implementations there and ran the real contract
against them; `lore_comms`/`lore_findings` reachable. No impossibilities to report.

---

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT** — 5 wrong builds survive the full 15/15 contract, one a BLOCKER.
- **P1 (headline): a `wave_gate` whose `main()` runs NO gates and returns 0 unconditionally — the enforcement point that enforces NOTHING — passes 15/15.** No test invokes `main()` with a declared mode; the pure renderer is over-tested and the CLI entrypoint (which #344 says IS the enforcement point, no CI) is untested on its happy path.
- **Packages considered:** none new — INSTRUMENT G is composition over in-repo `pending_contract_gate` machinery; the only package-adjacent verdict is *reuse the existing in-repo runner (`_run_selected_gates`/`GateManifest.load`)* = **keep/reuse**, and the contract does NOT enforce that reuse (MP-2).
- **Graded:** `405d32133eea45a54e345c837d117eba189cd7b3` · HEAD-at-report: `405d3213` · SAME. (Contract file `scripts/test_wave_gate.py` is UNTRACKED at HEAD — graded from the working tree.)
- **Provenance (#140):** `loremaster.__file__` → `/home/ejprice/scratch-adversary-g/loremaster/loremaster/__init__.py` (inside SCRATCH_ROOT).
- **MISSING PINS:** MP-1 (BLOCKER: main never enforces) · MP-2 (DRY leg-5: main re-parses gates.yaml, a 2nd manifest reader) · MP-3 (TRUST: wave summary over-claims "every gate GREEN") · MP-4 (wave×ruff RED_ORPHANED waved through) · MP-5 (selector-echo is a single-value monoculture).
- **Fixtures that cannot tell right from wrong:** the wave-mode integrity is guarded only at the pytest LINE and only for the typecheck core; `main` happy-path has NO fixture; selector-echo uses one value.
- **Satisfiability (C-DEF):** reference build → **15 passed, 0 failed** (after avoiding the NOT_RUN/"manifest" wrinkle, R1).
- **RED honesty (P7):** with no `wave_gate.py`, collection errors `ModuleNotFoundError: No module named 'wave_gate'` at the `importlib.import_module` line — the intended contract-first RED, right reason.
- **P0 controls:** 5 positive controls (W3/W5/W6r/W6c/W1s) each redden the pin meant to catch them → the probe harness demonstrably sees breakage; the survivals above are real.
- Residuals: R1 NOT_RUN/"manifest" satisfiability wrinkle · R2 source-scan `canonical` is itself a hand-list (bounded) · R3 "wave scopes pytest" policy expressed twice.

---

## P1b — QUANTIFIER TABLE (∀-over-inputs vs guarded-by-failure-mode; every guarded row carries a receipt)

| # | invariant the contract intends | classification | receipt |
|---|---|---|---|
| I1 | mode is REQUIRED & recorded | **∀** (render TypeError + cli SystemExit + header) | reference green; W6r/W6c controls redden |
| I2 | reported gate-set == manifest gate-set (coverage a checked variable) | **∀** over manifests (3-gate / +extra / −ruff) | W1s (render first-3) reddens `test_render_enumerates` |
| I3 | a claimed-but-omitted gate → NOT_RUN → fail | **∀** over omitted gate | reference green (with R1 caveat) |
| I4 | a RED_ORPHANED/NOT_RUN gate fails the bundle | **GUARDED** — only (checkpoint,ruff), (checkpoint,omit), (wave,mypy), (wave,junit) cells are pinned; **(wave, ruff) is unguarded** | **W-ruff survives** — ruff dirty in wave → ok=True (MP-4) |
| I5 | a wave receipt can never read as an unqualified pass; the subset is visible | **GUARDED** — checked only at the pytest LINE, with one selector value | **W-B survives** (summary over-claims, MP-3); **W-echo survives** (hardcoded echo, MP-5) |
| I6 | non-omittable core runs full in wave (never scoped) | **GUARDED** — only typecheck exercised (`mypy="dirty"`); ruff half unguarded | **W-ruff survives** (MP-4) |
| I7 | the CLI ENTRYPOINT actually enforces (runs full manifest, exits nonzero on red) | **UNGUARDED** — only the no-mode door is pinned; happy path never invoked | **W-main-noop survives** — main returns 0 always (MP-1, BLOCKER) |
| I8 | `pytest_args_for` scopes only in wave | **∀** over mode (unit-tested) | reference green; but that `main` USES it is untested → folds into I7 |

---

## P1c — REACH ATTACK TABLE (per instrument the contract introduces/relies on). Legs: **E = empirical (wrong build in scratch)**, **C = construction-inspection.**

| instrument | (1) site-set | (2) DERIVED vs hand-list | (3) coverage a checked variable? | (4) effect vs proxy | (5) ONE source proven by mutation | verdict |
|---|---|---|---|---|---|---|
| render gate-enumeration (`render_wave_receipt` iterates `manifest.gates`) | the gates reported | DERIVED from `manifest.gates` ✓ | **YES** — add/drop test reddens (E: W1s) | effect (real parsed results) ✓ | renderer handed the manifest = one source ✓, **but `main` may be a 2nd reader — UNPROVEN** (E: W-DRY) | ✓ in renderer / **MISSING at main (MP-2)** |
| scopable-gate identification (by junit reader) | which gate is scopable | DERIVED by reader identity ✓ | **YES** — `suite` rename reddens (E: W5) | verdict-based ✓ | render & run both key on reader identity — consistent (C) | ✓ |
| mode-required mechanism | render + cli verdict paths | required, no default ✓ | render+cli pinned (E: W6r/W6c) | n/a | one parser (C) | ✓ for what it covers; **does not reach main's happy path (I7)** |
| currency fail-on-red (RED_ORPHANED/NOT_RUN) | the (mode × gate) cells where a red fails | **HAND-PICKED matrix of fixture cells**, not ∀ over mode×gate | **NO** — (wave,ruff) cell silently exempt (E: W-ruff) | effect ✓ | — | **MISSING (MP-4)** |
| wave honesty (SCOPED, never GREEN, selector echoed) | the "no unqualified pass" surface | pytest LINE only; selector one value | **partial** — line ✓, summary ✗, echo monoculture ✗ | effect ✓ | — | **MISSING (MP-3, MP-5)** |
| `test_no_hardcoded_gate_id_collection` (AST source scan) | `wave_gate.__file__` | reach DERIVED from module ✓; but its `canonical={typecheck,ruff,pytest}` is a **hand-list** | catches literal-list door only (E: W1s = passes; hardcoded-tuple = reddens) | source ✓ | belt to the behavioral enumerate test (docstring says so) | acceptable-with-note (R2) |
| **the CLI entrypoint `main` (the #344 enforcement point)** | main's happy-path behavior | — | **NO — essentially untested (only no-mode)** | — | one-source UNPROVEN | **MISSING — BLOCKER (MP-1) + DRY (MP-2)** |

**Which legs were empirical:** every MISSING-PIN row is EMPIRICAL — a wrong build built in scratch that survives the real contract (commands in the probe record). Rows marked (C) are construction-inspection of the shared machinery.

---

## MISSING PINS — each as *the test that should exist* + *the defect it catches* + *the reproduction*

### MP-1 — BLOCKER — `test_main_enforces_the_bundle` (the entrypoint is never invoked with a mode)
- **Defect caught:** a `main` that never fails on the happy path — returns 0 unconditionally, swallows the bundle's `ok`, or runs a subset. This is the single worst failure for #344, whose own framing is *"no CI exists (#285), so the bundle IS the enforcement point."* The contract's ONLY `main(...)` call is `main([])` (the no-mode refusal); `main` with a declared mode is **never** invoked.
- **Reproduction:** W-main-noop — `main()` parses args (still requires a mode) then `print(...); return 0`, running no gates → **15 passed, 0 failed**; `main(["--checkpoint"])→0`, `main(["--wave","-k","x"])→0`.
- **The pin:** monkeypatch `pending_contract_gate._run_selected_gates` (the contract already stubs `GateRunner.run` in `test_cli_refuses_without_a_declared_mode`, so the pattern exists) to return a canned `results` dict, and assert main's exit code: clean dict → `main(["--checkpoint"]) == 0`; a dict carrying a RED_ORPHANED (ruff dirty) → `main(["--checkpoint"]) != 0`; a scoped junit failure → `main(["--wave","-k","x"]) != 0`. A single spy-backed integration test kills MP-1 and MP-2 together.

### MP-2 — DRY / ONE-IMPLEMENTATION (leg 5, the brief's #1 priority) — `test_main_uses_the_one_manifest_reader`
- **Defect caught:** a `main` that RE-PARSES `gates.yaml` itself / re-implements gate execution — a SECOND reader of the manifest (Q4-flag-4; the #102/#120 "two sources of truth for one policy" trap). Two readers drift: the private one skips `GateManifest.load`'s pydantic validation, the reader-allowlist, and the anti-vacuity guards.
- **Reproduction:** W-DRY-reparse — `main` does `yaml.safe_load(gates.yaml)`, builds its own `[entry["id"] …]` leg list, subprocesses each → **15 passed, 0 failed**. The source scan (`test_no_hardcoded_gate_id_collection`) catches only the *literal-tuple* variant (confirmed: injecting `("typecheck","ruff","pytest")` reddens it) — a yaml re-parse names no literal, so it slips.
- **The pin:** a spy on `pending_contract_gate._run_selected_gates` (and/or `GateManifest.load`) asserting `main` called it exactly once, with `manifest.ids` (the full derived leg set) — mutation-style: if main doesn't route through the shared reader the spy count is 0 → RED. Belt: an AST/source pin that `wave_gate.py` contains no second `yaml.safe_load`/`yaml.load`.

### MP-3 — TRUST (priority #2) — extend the wave honesty pin to the SUMMARY line
- **Defect caught:** a wave receipt whose per-gate pytest line is honestly SCOPED but whose OVERALL summary over-claims — the #306/#312 false-clear ("a subset reads as an unqualified pass") reproduced at the summary. `test_wave_pytest_scoped_never_green_and_echoes_selector` inspects only `_verdict_line(lines,"pytest")`, never the whole receipt's verdict.
- **Reproduction:** W-B — pytest line = `SCOPED(-k test_changed_area) …` AND summary = `CURRENCY : PASS — every claimed gate is GREEN or OWNED` → **15 passed, 0 failed**. This is the *path of least resistance* build (relabel one line, keep `_render_currency`'s summary).
- **The pin:** on a wave receipt with a scoped pytest, assert `"\n".join(lines)` contains NO unqualified "every claimed gate is GREEN"/"CURRENCY : PASS" — the receipt's overall verdict must itself carry the SCOPED / full-run-owed bound, never read as a clean currency clear.

### MP-4 — the wave×ruff cell of W4 — `test_wave_ruff_orphan_fails_and_is_not_scoped`
- **Defect caught:** ruff RED_ORPHANED in wave mode waved through — ruff treated as advisory/scopable. W4's title is *"typecheck OR ruff treated as scopable"*, but the only fixture exercises typecheck (`mypy="dirty"`); the ruff half is never driven.
- **Reproduction:** W-ruff — render treats the ruff-reader gate as advisory in wave mode → **15 passed, 0 failed**; `render_wave_receipt(..., ruff="dirty", mode=MODE_WAVE)` returns `ok=True` while printing `WAVE : PASS — core (typecheck+ruff) green-or-owned`.
- **The pin:** mirror `test_wave_core_gates_run_full_and_still_fail` with `ruff="dirty"`: assert `not ok` and the ruff line NOT marked SCOPED. Best form: parametrize the core-integrity test over the core gates `{mypy, ruff}` so the invariant is ∀ over the core, not just typecheck.

### MP-5 — P2 monoculture — strengthen the selector-echo assertion
- **Defect caught:** a build that hardcodes the echoed selector (ignoring the real one) — the receipt LIES about which subset ran, defeating design point 4 ("the subset is in the receipt"). The echo is asserted with a single selector value (`"test_changed_area"`).
- **Reproduction:** W-echo — SCOPED line hardcodes `"-k test_changed_area"` → **15 passed, 0 failed**; with real selector `["-k","test_totally_different_area"]` the receipt still claims `SCOPED(-k test_changed_area)`.
- **The pin:** assert the echoed selector EQUALS the exact `pytest_selector` passed (the joined selector string is a substring of the pytest line) and use a second, distinctive value — a hardcoded echo then cannot match. Best: also pin at integration that the echoed selector == the argv `pytest_args_for` forwarded.

---

## Fixture-discrimination verdicts (W1–W7 + perturbations)

| wrong build class | contract's intended pin | verdict |
|---|---|---|
| W1 hardcoded gate-id **tuple** | `test_no_hardcoded_gate_id_collection` | **CAUGHT** (E: literal reddens) |
| W1 render doesn't track manifest (non-literal, e.g. `manifest.gates[:3]`) | `test_render_enumerates_exactly_the_manifest_gates` | **CAUGHT** (E: W1s reddens enumerate, source-scan passes → enumerate is the real instrument) |
| W2 omitted gate read as a pass | `test_claimed_gate_absent…` | **CAUGHT** (reference green with R1 caveat) |
| W3 wave pytest rendered GREEN | `test_wave_pytest_scoped…` / `test_scopable…` | **CAUGHT** (E: both redden) |
| W4 typecheck scoped in wave | `test_wave_core_gates_run_full_and_still_fail` | **CAUGHT** |
| **W4 ruff scoped/advisory in wave** | — none — | **SLIPS → MP-4** (E: W-ruff) |
| W5 scopable keyed on literal `"pytest"` | `test_scopable_gate_identified_by_reader…` | **CAUGHT** (E: W5) |
| W6 mode defaulted (render / cli) | `test_render_requires_mode_declared` / `test_cli_refuses…` | **CAUGHT** (E: W6r/W6c) |
| W7 RED_ORPHANED waved through | `test_checkpoint_red_orphaned_fails` | **CAUGHT** (checkpoint); **wave×ruff SLIPS → MP-4** |
| **wave summary over-claim** | — none — | **SLIPS → MP-3** (E: W-B) |
| **selector-echo hardcoded** | echo asserted with one value | **SLIPS → MP-5** (E: W-echo) |
| **main never enforces / re-parses gates.yaml** | — none (main happy-path untested) — | **SLIPS → MP-1 (BLOCKER), MP-2** (E: W-main-noop, W-DRY) |

Perturbation both-legs proof: every SLIP row is a wrong build that **survives** the contract AND the **reference build passes all 15** (the correct-build control) — so each is a genuine non-discrimination, not a botched fixture.

---

## Residuals (individual verdicts — no "the rest look fine")

- **R1 — satisfiability wrinkle (NOT_RUN vs `_verdict_line`):** `GateCurrency.render()`'s NOT_RUN text is `"… claimed by the manifest, never executed"`, and the contract's own `_verdict_line` helper *excludes every line containing "manifest"*. A builder faithfully reusing the wrapped machinery's NOT_RUN rendering (exactly the "mirror `_render_currency`" the docstring instructs) fails W2 (`test_claimed_gate_absent…`, `test_render_enumerates…` four-gate) with an opaque `assert None is not None` — verified: my first reference build hit exactly this. NOT a blocker (satisfiable by rendering NOT_RUN without "manifest", as the shipped reference does), but a real trap. Suggest: drop the `"manifest" not in ln` filter in `_verdict_line` (it exists only to skip the roster header, which can be excluded by matching its `manifest :` prefix instead), or state in the render spec that a gate's own NOT_RUN line must name the gate outside any "manifest" mention.
- **R2 — the source scan's `canonical` is itself a hand-list:** `test_no_hardcoded_gate_id_collection` keys on `canonical = {"typecheck","ruff","pytest"}`. If `gates.yaml` renames a gate, a hardcoded tuple of the *new* id could evade it. Bounded and acknowledged (the behavioral enumerate test is the real coverage-checked instrument; the docstring says this pin is "belt to that braces"). Acceptable — noted so it is met deliberately.
- **R3 — "wave scopes pytest" is expressed twice:** `pytest_args_for`'s `if mode == MODE_WAVE` (run side) and the render's scopable branch (`if mode == MODE_WAVE`) are two encodings of one policy; the design said *"the changed-suite selector logic lives in ONE place in the wrapper."* Minor; MP-5's integration form (echoed == forwarded) would also pin these two into agreement.

---

## Full probe record (commands + real output tails)

**Scratch (provenance-asserted, #140):** `./scripts/scratch_copy.sh /home/ejprice/scratch-adversary-g` →
`loremaster -> /home/ejprice/scratch-adversary-g/loremaster/loremaster/__init__.py` (+ 3 siblings).

**P7 RED honesty** (no `wave_gate.py`): `uv run pytest scripts/test_wave_gate.py -q` →
`ModuleNotFoundError: No module named 'wave_gate'` at `test_wave_gate.py:123` (`importlib.import_module`), `1 error in 0.18s`. Right reason.

**C-DEF satisfiability** (reference build `/tmp/wave_gate_REFERENCE.py`): `15 passed in 0.07s`.

**P1 survivors (each = full contract, 15 tests):**
- W-main-noop (`main` runs no gates, returns 0): `15 passed`. `main(['--checkpoint'])→0`, `main(['--wave','-k','x'])→0`.
- W-DRY-reparse (`main` `yaml.safe_load`s gates.yaml, private leg list, subprocesses): `15 passed`.
  - source-scan reach control: injecting literal `("typecheck","ruff","pytest")` → `test_no_hardcoded_gate_id_collection` `1 failed` (`assert not [['typecheck','ruff','pytest']]`) → catches the literal door, not the re-parse door.
- W-B (pytest line SCOPED, summary `CURRENCY : PASS — every claimed gate is GREEN or OWNED`): `15 passed`. Rendered receipt shows the SCOPED line and the over-claim together.
- W-ruff (ruff advisory in wave): `15 passed`; `render_wave_receipt(..., ruff="dirty", mode=WAVE)` → `ok = True`, receipt prints `WAVE : PASS — core (typecheck+ruff) green-or-owned` with `ruff ADVISORY(wave)`.
- W-echo (hardcoded echoed selector): `15 passed`; real selector `test_totally_different_area` → receipt `SCOPED(-k test_changed_area)`.

**P0 positive controls** (wrong build → the pin meant to catch it, expect FAIL):
```
W3  wave-pytest-GREEN      2 test(s) -> FAIL (pin fires ✓)
W5  scopable-by-literal    1 test(s) -> FAIL (pin fires ✓)
W6r render-mode-default    1 test(s) -> FAIL (pin fires ✓)
W6c cli-mode-default       1 test(s) -> FAIL (pin fires ✓)
W1s render-first-3-only    2 test(s) -> FAIL(enumerate) + PASS(source-scan)  ✓
```
→ the probe harness sees breakage; the survivals above are real, not a blind harness.

---

## VERDICT: **CONTRACT INSUFFICIENT**

The pure renderer (`render_wave_receipt`) is well pinned — mode required/recorded, gate-set derived with coverage as a checked variable, scopable-by-reader, checkpoint currency all caught. But five wrong builds survive the full contract, one a BLOCKER:

1. **MP-1 (BLOCKER):** the CLI entrypoint `main` — which every spawn brief invokes and which #344 designates the enforcement point (no CI) — is untested on its happy path; a `main` that enforces nothing passes.
2. **MP-2 (DRY leg-5, priority #1):** `main` may be a second reader of `gates.yaml`, unpinned.
3. **MP-3 (TRUST, priority #2):** the wave summary can over-claim "every gate GREEN" while pytest is scoped.
4. **MP-4:** the wave×ruff RED_ORPHANED cell is waved through.
5. **MP-5:** the selector-echo honesty is a single-value monoculture.

MP-1 + MP-2 are the same root — an untested `main` — and a single spy-backed integration test closes both; MP-4/MP-5 are one-fixture additions to existing tests; MP-3 is a one-assertion extension. R1 (NOT_RUN/"manifest") should be smoothed so the fix doesn't trip builders.
