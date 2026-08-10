brief-base v10 read
brief project v7 read

# REPORT-delta-adversary-g — re-grade of the REVISED INSTRUMENT G contract (`scripts/test_wave_gate.py`, #344)

## Capability check (tool honesty — brief-base §4, first)
Everything the brief demanded was satisfiable. `scratch_copy.sh` built a provenance-asserted
copy; I built an INDEPENDENT reference `wave_gate.py` there (not the reviser's, which lived at
`/tmp` and is gone) and ran the real 29-pin contract against it and against 7 wrong builds;
`lore_comms` reachable. No impossibilities.

---

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT.** The revision genuinely closed all 5 original wrong builds
  and opened NO regression of them — but the SAME defect class G exists to kill survives through
  **three unpinned wave-mode cells**. 3 wrong builds pass the full 29/29.
- **P1 (headline): `main(["--wave","-k","x"])` with a CORE ruff `RED_ORPHANED` returns exit 0**
  (reference returns 1) — the #344 disease AT the enforcement point ("no CI, the bundle IS the
  enforcement point"), in the mode agents run most. Survives 29/29 (W-main-wave-core).
- **Did the revision close each original wrong build? YES, independently confirmed** (my rebuild
  reproduces the reviser's RED table exactly): W-main-noop→3 failed · W-DRY-reparse→4 failed ·
  W-B→1 (MP-3) · W-ruff→1 (MP-4[ruff]) · W-echo→2 (MP-5). **Did it open a new one? NO regression
  of MP-1..MP-5**, but 3 NEW survivors of the shared class (below).
- **Packages considered:** none new — G composes in-repo `pending_contract_gate` machinery
  (`_run_selected_gates`, `_render_currency`, `_residuals_for`, `gate_currency`, readers). Reuse
  verdict = **keep/reuse** (the contract DOES enforce the reuse now — MP-2 spy — good).
- **Graded:** `3b708e5c2196c29a11b8b7e6656c921a14db4f28` · HEAD-at-report: `14b62f2` · DIFFERENT
  (1 behind) — but the graded files (`test_wave_gate.py`, `pending_contract_gate.py`, `gates.yaml`)
  are **byte-identical** across the gap (`git diff --stat 3b708e5 14b62f2` = empty for all three;
  the only intervening commit is `14b62f2` §10 docs). Grading holds for HEAD.
- **Provenance (#140):** `loremaster.__file__` → `/home/ejprice/scratch-delta-adversary-g/loremaster/loremaster/__init__.py`; `pending_contract_gate.__file__` → same scratch root (INSIDE).
- **MISSING PINS (new):** **MP-6** (headline: main's exit-code enforcement is a HAND-LIST of 4
  cells, not ∀ over mode×gate — wave×core-red waved through) · **MP-7** (wave summary over-claims
  with alternate wording — MP-3 is a forbidden-token list, not a positive scoped-marker assertion)
  · **MP-8** (a NOT_RUN/omitted gate in wave mode is tolerated — the literal #344 event reproduced
  in wave; `test_claimed_gate_absent` is checkpoint-only).
- **Satisfiability (C-DEF):** my independent reference → **29 passed, 0 failed**. Contract passes
  its OWN gates: `ruff` clean, `mypy` (strict, `MYPYPATH=scripts`) Success.
- **RED honesty (P7):** with no `wave_gate.py`, collection errors `ModuleNotFoundError: No module
  named 'wave_gate'` at the `importlib.import_module` line (test_wave_gate.py:134) — contract-first
  RED, right reason.
- **META-RECURSION (item d):** CONFIRMED both directions — add a 4th gate to the canned manifest →
  `test_every_mode_gate_cell_fails_on_a_red` param count grows 3→4 AND the coverage pin stays
  green; hardcode `_FAIL_MATRIX_GATES` stale → coverage pin RED. The renderer's ∀-reach IS a
  checked variable. **The gap is that this discipline was NOT extended to the entrypoint (MP-6) or
  to the NOT_RUN failure-mode (MP-8).**
- **Leg-5 (item e):** CONFIRMED — the bundle routes through `pending_contract_gate._run_selected_gates`
  (MP-2 spy: reference 1 call with `manifest.ids`; W-main-noop/W-DRY 0 calls → RED) and re-parses
  nothing (AST belt catches W-DRY's `yaml.safe_load` → RED). No second manifest reader survives.
- **P0 controls:** the harness demonstrably SEES breakage — all 5 MP wrong builds redden their
  targeted pins, the meta-recursion stale-hardcode reddens the coverage pin, and the reference
  passes 29/29. So the 3 new survivals are REAL non-discriminations, each paired with a reference
  control doing the right thing.

---

## Did the revision TRULY close each original wrong build? (independent rebuild — not the claim)

Every wrong build below was reconstructed from MY independent reference with a targeted mutation
and run against the full 29-pin contract in provenance-asserted scratch. This reproduces the
reviser's claimed RED table — verified, not relayed.

| original wrong build | my rebuild result | targeted pin(s) fired | closed? |
|---|---|---|---|
| **W-main-noop** (main runs no gates, returns 0) | 3 failed, 26 passed | MP-1[checkpoint-orphan], MP-1[wave-scoped-failure], MP-2 | ✅ |
| **W-DRY-reparse** (`yaml.safe_load` of gates.yaml, private legs) | 4 failed, 25 passed | MP-1 ×2, MP-2, MP-2-belt (AST) | ✅ |
| **W-B** (SCOPED pytest line + machinery over-claim summary) | 1 failed, 28 passed | MP-3 | ✅ |
| **W-ruff** (ruff advisory/scopable in wave, renderer) | 1 failed, 28 passed | MP-4[ruff] | ✅ |
| **W-echo** (hardcoded echoed selector) | 2 failed, 27 passed | MP-5[test_totally_different_area], MP-5[not (slow or flaky)] | ✅ |

All five are genuinely caught. The R1 satisfiability trap is fixed (my reference emits NOT_RUN
lines containing "manifest" and `test_claimed_gate_absent`/`test_render_enumerates` pass — the
`_verdict_line` prefix-exclusion works). The from-import spy works (my reference uses
`from pending_contract_gate import _run_selected_gates` and MP-2 reaches it).

---

## Did it OPEN a new wrong build? YES — 3 survivors, ONE class (r5 lesson)

**Shared root cause: the wave-mode failure/enforcement surface is under-pinned relative to
checkpoint.** The ∀ discipline (IDIOM 1) and summary-honesty (IDIOM 3) that were applied to the
renderer's DIRTY-cell matrix (MP-4) and to checkpoint currency were NOT extended to (a) the
entrypoint's exit code as a ∀, (b) the summary as a POSITIVE assertion, or (c) the NOT_RUN
failure-mode in wave. Each survivor passes 29/29; each paired with a reference control.

| new wrong build | survives? | reference control | the hole |
|---|---|---|---|
| **W-main-wave-core** — `main` treats core reds as advisory in wave mode | **29/29** | ref `main` → exit 1 | **MP-6** — main's exit ∀ is a hand-list |
| **W-summary-alt** — wave summary "PASS — all gates are clean, tree is green" | **29/29** | ref summary carries "SCOPED … full run still owed" | **MP-7** — MP-3 forbids 2 tokens, not a positive marker |
| **W-wave-notrun** — NOT_RUN (omitted) gate tolerated in wave mode | **29/29** | ref → ok=False | **MP-8** — wave NOT_RUN unpinned |

---

## P1b — QUANTIFIER TABLE (∀-over-inputs vs guarded; every guarded row carries a receipt)

| # | invariant the contract intends | classification | receipt |
|---|---|---|---|
| I1 | mode REQUIRED & recorded | **∀** (render TypeError + cli SystemExit + header) | reference green; W6r/W6c-class controls in original pass |
| I2 | reported gate-set == manifest gate-set | **∀** over manifests (3 / +extra / −ruff) | reference green; W1-class caught by enumerate |
| I3 | a claimed-but-omitted gate → NOT_RUN → fail | **GUARDED — CHECKPOINT ONLY** | **W-wave-notrun survives** (MP-8): wave omit → ok=True |
| I4 | a RED in any gate fails the bundle (renderer) | **∀ over (mode × gate)** for DIRTY reds, DERIVED (`_FAIL_MATRIX_GATES`) + coverage-checked | reference green; W-ruff reddens MP-4[ruff]; META-RECURSION proven |
| I5 | a wave receipt never reads as an unqualified pass | **GUARDED** — per-gate line ✓; summary checked only by ABSENCE of 2 tokens | **W-summary-alt survives** (MP-7): alternate over-claim wording |
| I6 | non-omittable core runs full in wave (never scoped) | **∀ over core gates** (MP-4 non-scopable branch) | reference green; W-ruff reddens |
| I7 | the ENTRYPOINT `main` enforces the verdict | **GUARDED — 4 HAND-PICKED (mode,gate) cells, not ∀** | **W-main-wave-core survives** (MP-6): main(--wave) exit 0 over a core RED_ORPHANED |
| I8 | `pytest_args_for` scopes only in wave | **∀** over mode (unit) | reference green |
| I9 | bundle routes through the ONE manifest reader | **∀** (spy both namespaces + AST belt) | reference 1 call; W-main-noop/W-DRY 0 calls |

Two guarded rows (I3, I7) carry a **surviving wrong build** as the receipt; I5 likewise. Those are
MP-8, MP-6, MP-7. The rest are ∀-over-inputs with a reference-green + control receipt.

---

## P1c — REACH ATTACK TABLE (per instrument). Legs: **E = empirical wrong build in scratch**, **C = construction-inspection.**

| instrument | site-set | DERIVED vs hand-list | coverage a checked variable? | effect vs proxy | one-source-by-mutation | verdict |
|---|---|---|---|---|---|---|
| renderer gate-enumeration | gates reported | DERIVED from `manifest.gates` ✓ | **YES** — add/drop reddens (E) | effect ✓ | renderer handed the manifest; `main` routes ONE reader (E: MP-2) | ✅ |
| **renderer fail-matrix (MP-4)** | (mode × gate) DIRTY-red cells | **DERIVED** `_FAIL_MATRIX_GATES=_canonical_manifest_ids()` ✓ | **YES** — META-RECURSION proven both ways (E) | effect ✓ | — | ✅ **but only the DIRTY failure-mode** (omitted absent → MP-8) |
| **entrypoint enforcement (MP-1)** | main's exit over (mode,gate) | **HAND-LIST of 4 cells** — not derived | **NO** — add a gate / the wave×core cells don't grow it | effect (exit code) ✓ | — | **MISSING (MP-6)** — reach is a hidden constant; the 7th-defeat shape at the entrypoint |
| scopable-gate identification | which gate is scopable | DERIVED by junit-reader identity ✓ | YES — `suite` rename reddens (E: W5) | verdict ✓ | render+run key on reader identity (C) | ✅ |
| wave summary honesty (MP-3) | the "no unqualified pass" surface | forbidden-TOKEN list (2 tokens), token DERIVED from machinery | **partial** — catches machinery-token reuse; blind to alternate wording | effect ✓ | — | **MISSING (MP-7)** — enumerate-the-forbidden, no positive scoped-marker |
| NOT_RUN → fail | omitted-gate cells | checkpoint only | **NO for wave** | effect ✓ | — | **MISSING (MP-8)** |
| `test_no_hardcoded_gate_id_collection` (AST) | `wave_gate.__file__` | reach DERIVED from module; `canonical` set is a hand-list | catches literal-collection door (E) | source ✓ | belt to enumerate (docstring) | acceptable-with-note (R2, inherited) |

**Legs run:** MP-6, MP-7, MP-8 rows are **EMPIRICAL** (wrong build in scratch survives 29/29 +
reference control). The META-RECURSION row is EMPIRICAL (mutated the canned manifest, counted the
matrix, reddened the stale hardcode). "scopable-by-reader" and "routes-one-reader" corroborated by
the MP-2/W5 empirical results + construction-inspection of the shared machinery.

The author's own copy, applied to MP-1: *"What is the SET of cells this exit-code guard drives main
over, is it DERIVED from (modes × manifest.gates × failure-modes) or a hand-list, and does a test go
RED when a new gate/mode/failure-mode joins the set but main is not driven over it?"* — MP-4 (the
renderer) answers yes; MP-1 (the entrypoint, the actual enforcement point) answers **no**.

---

## MISSING PINS — each as *the test that should exist* + *the defect* + *the reproduction*

### MP-6 — HEADLINE — `test_main_exit_code_over_every_mode_gate_cell` (entrypoint enforcement is a hand-list, not ∀)
- **Defect caught:** a `main` that treats a CORE gate (typecheck/ruff) as advisory in **wave** mode
  and returns 0 over an orphaned core red. This is the #306/#312/#344 disease — a subset/advisory
  reading as a pass — reproduced AT the enforcement point that #344 itself designates ("no CI
  exists, so the bundle IS the enforcement point"), in the mode agents run most between checkpoints.
  MP-1 fixed main's happy path but pinned only **4 hand-picked (mode,gate) cells**: checkpoint×{clean,
  ruff}, wave×{clean, junit}. The dangerous **wave×core-red** cells are absent, so main's exit-code
  reach is a hidden constant while the renderer's (MP-4) is a checked variable — the exact asymmetry
  P1c names.
- **Reproduction (E):** `W-main-wave-core` — `main` recomputes its verdict and in wave mode returns
  `0` iff the scoped pytest subset is clean, ignoring core reds. `main(["--wave","-k","x"])` with a
  ruff `RED_ORPHANED` → **exit 0** (reference → exit 1); the printed receipt itself says `FAIL`.
  Survives **29 passed, 0 failed**.
- **The pin:** drive the REAL `main`'s exit code over a matrix **DERIVED** like `_FAIL_MATRIX_GATES`
  — ∀ over (mode × gate × failure-mode ∈ {dirty, omitted}), asserting `main(argv) != 0` for every
  red cell (via the existing `_patch_loaders` + `_install_reader_spy` scaffolding). **STRONGEST
  (delete-the-divergence, IDIOM 2):** assert `(main(argv) == 0) == render_wave_receipt(...)[1]`
  across the matrix — main's exit code must EQUAL the renderer's `ok`, so a divergent main is
  unrepresentable. Make the main-cell set a CHECKED VARIABLE (coverage pin: cells == modes × manifest
  gates × failure-modes) so a new gate/mode grows it or reddens — the same META-RECURSION MP-4 has
  and MP-1 lacks.

### MP-7 — TRUST (operator #2) — `test_wave_scoped_summary_positively_carries_the_scoped_bound`
- **Defect caught:** a wave-scoped receipt whose per-gate pytest line is honestly SCOPED but whose
  SUMMARY over-claims with wording DIFFERENT from the machinery's token — a false clear that reads
  as a full pass while pytest ran only a subset. `test_wave_scoped_summary_never_reads_as_a_full_
  currency_clear` forbids exactly two tokens ("every claimed gate is GREEN", "CURRENCY : PASS — …");
  that is a FORBIDDEN-SET enumeration — the antipattern CLAUDE.md has the most receipts against — and
  the design's OWN §9.3 first bullet asks for the opposite: "the summary is DERIVED from per-leg
  qualified flags … if ANY leg is SCOPED, the summary carries that bound."
- **Reproduction (E):** `W-summary-alt` — wave summary = `"WAVE : PASS — all gates are clean, tree
  is green"`. Dodges both forbidden tokens; survives **29 passed, 0 failed**. Reference summary
  honestly reads `"WAVE : PASS — core GREEN-or-owned; pytest SCOPED, full run still owed"`.
- **The pin:** on a wave receipt with a scoped leg, assert the SUMMARY line POSITIVELY carries the
  scoped bound (contains "SCOPED", or "owed", or the echoed selector) — the allowlist-the-safe form.
  Control (already present in spirit): the checkpoint clean summary (no scoped leg) IS allowed the
  unqualified clear, so this is an honesty check, not a blanket ban.

### MP-8 — `test_wave_omitted_gate_is_not_run_and_fails` (NOT_RUN ∀ over mode)
- **Defect caught:** a gate the manifest claims but the run omitted (NOT_RUN) is tolerated in **wave**
  mode (ok stays True) — the LITERAL #344 event ("a stage ran a subset and omitted a gate, read
  green") reproduced in wave mode. `test_claimed_gate_absent_from_results_is_not_run_and_fails` uses
  only `MODE_CHECKPOINT`; `test_every_mode_gate_cell_fails_on_a_red` injects a DIRTY gate (present-
  but-red), never an OMITTED one. So the wave × NOT_RUN cell is unpinned.
- **Reproduction (E):** `W-wave-notrun` — in wave mode a `results.get(id) is None` gate does not set
  `ok=False`. A wave receipt with the ruff gate OMITTED → `ok=True`, summary `"WAVE : PASS — core
  GREEN-or-owned…"`. Survives **29 passed, 0 failed**.
- **The pin:** mirror `test_claimed_gate_absent` for `MODE_WAVE` (assert `not ok` + the omitted gate
  named NOT_RUN). Best: fold "omitted" in as a failure-mode of MP-6's ∀ matrix so dirty AND omitted
  are covered in BOTH modes at both the renderer and the entrypoint — one ∀, not three point-fixes.

---

## Fixture-discrimination verdicts (every wrong build an individual verdict)

| wrong build | intended pin | verdict |
|---|---|---|
| W-main-noop | MP-1 / MP-2 | **CAUGHT** (E: 3 failed) |
| W-DRY-reparse | MP-2 + AST belt | **CAUGHT** (E: 4 failed) |
| W-B (machinery over-claim summary) | MP-3 | **CAUGHT** (E: 1 failed) |
| W-ruff advisory (renderer) | MP-4[ruff] | **CAUGHT** (E: 1 failed) |
| W-echo hardcode | MP-5 (≥2 values) | **CAUGHT** (E: 2 failed) |
| W1 literal gate tuple | `test_no_hardcoded_gate_id_collection` | **CAUGHT** (inherited, source scan) |
| W5 scopable-by-literal-id | `test_scopable_gate_identified_by_reader…` | **CAUGHT** (inherited) |
| **W-main-wave-core** (main core-advisory in wave) | — none — | **SLIPS → MP-6** (E: exit 0) |
| **W-summary-alt** (alternate over-claim wording) | — none — | **SLIPS → MP-7** (E: false clear) |
| **W-wave-notrun** (omitted gate tolerated in wave) | — none — | **SLIPS → MP-8** (E: ok=True) |

Both-legs proof: every SLIP is a wrong build that **survives 29/29** AND the **reference passes
29/29** with the correct behaviour (exit 1 / honest summary / ok=False) — genuine non-discrimination,
not a botched fixture.

---

## Residuals (individual verdicts — no "the rest look fine")

- **R2 (inherited from adversary-g) — the source scan's `canonical` is a hand-list.**
  `test_no_hardcoded_gate_id_collection` keys on `canonical={"typecheck","ruff","pytest"}`; a
  hardcoded tuple of RENAMED ids would evade it. Bounded (the behavioral enumerate test is the real
  coverage-checked instrument; the docstring says so). Unchanged by the revision — noted so it is met
  deliberately, not a new finding.
- **R3 (inherited) — "wave scopes pytest" is expressed twice** (`pytest_args_for` run-side and the
  render's scopable branch). Minor. MP-6's strongest form (main-exit == renderer-ok) would also tie
  these into agreement at integration.
- **R-new — MP-6/MP-7/MP-8 are ONE class, and the fix is ONE ∀.** Reporting them as three pins so
  each carries its own reproduction, but the durable fix is: extend the renderer's DERIVED
  (mode × gate) matrix to (mode × gate × failure-mode ∈ {dirty, omitted}), pin main's exit == the
  renderer's ok across it (so the entrypoint's reach is a checked variable like the renderer's), and
  make the wave summary honesty a POSITIVE scoped-marker assertion. That is IDIOM 1 ∀ + IDIOM 2
  entrypoint-spy + IDIOM 3 positive-summary applied uniformly to wave mode, which is the design's own
  §9.5 row for G — the revision applied them to the renderer's dirty cells and stopped there.

---

## Full probe record (commands + real output tails)

**Scratch (provenance-asserted, #140):** `./scripts/scratch_copy.sh /home/ejprice/scratch-delta-adversary-g`
→ `loremaster -> /home/ejprice/scratch-delta-adversary-g/loremaster/loremaster/__init__.py` (+3
siblings); `pending_contract_gate.__file__` → same scratch root.

**P7 RED honesty** (no `wave_gate.py`): `uv run pytest scripts/test_wave_gate.py -q` →
`ModuleNotFoundError: No module named 'wave_gate'` at `test_wave_gate.py:134` (`importlib.import_module`),
`1 error in 0.19s`. Right reason.

**C-DEF satisfiability** (my independent reference `wave_gate_REFERENCE.py`): `29 passed in 0.12s`;
`--collect-only` → `29 tests collected`. Contract own gates: `ruff` `All checks passed!`;
`MYPYPATH=scripts mypy` `Success: no issues found in 1 source file`.

**Original 5 wrong builds (each = full 29-pin contract):**
```
wg_main_noop.py          3 failed, 26 passed  : MP-1[checkpoint-orphan], MP-1[wave-scoped-failure], MP-2
wg_dry_reparse.py        4 failed, 25 passed  : MP-1[checkpoint-orphan], MP-1[wave-scoped-failure], MP-2, MP-2-belt(AST)
wg_overclaim_B.py        1 failed, 28 passed  : MP-3
wg_ruff_advisory.py      1 failed, 28 passed  : MP-4[ruff]
wg_echo_hardcode.py      2 failed, 27 passed  : MP-5[test_totally_different_area], MP-5[not (slow or flaky)]
```

**3 NEW survivors (each = full 29-pin contract):**
```
wg_summary_alt.py        29 passed   -> MP-7 gap
wg_main_wave_core.py     29 passed   -> MP-6 gap (headline)
wg_wave_notrun.py        29 passed   -> MP-8 gap
```

**Gap demonstrations (direct, with reference control):**
```
REFERENCE      GAP1 wave summary: "WAVE : PASS — core GREEN-or-owned; pytest SCOPED, full run still owed"   (honest)
REFERENCE      GAP2 main(--wave -k x) with core ruff RED_ORPHANED -> exit 1                                  (correct)
wg_summary_alt GAP1 wave summary: "WAVE : PASS — all gates are clean, tree is green"                          (FALSE CLEAR)
wg_main_wave_core GAP2 main(--wave -k x) with core ruff RED_ORPHANED -> exit 0                                (FALSE CLEAR)
wg_wave_notrun demo: wave receipt with ruff OMITTED -> ok=True; summary "WAVE : PASS — core GREEN-or-owned…"  (FALSE CLEAR)
```

**META-RECURSION (item d):**
```
BEFORE mutation: test_every_mode_gate_cell_fails_on_a_red param count = 3
add ("docs","ruff","none",["true"]) to _manifest default:
AFTER  mutation: param count = 4  AND  test_fail_matrix_gate_set_equals_the_live_manifest -> 1 passed
control: hardcode _FAIL_MATRIX_GATES=("typecheck","ruff") -> test_fail_matrix_… FAILED (AssertionError line 890)
contract restored -> 29 passed
```

**Leg-5 (item e):** MP-2 spy (`test_main_routes_through_the_one_manifest_reader`) — reference 1 call
with `legs == manifest.ids`; W-main-noop/W-DRY 0 calls → RED. AST belt
(`test_wave_gate_does_not_reparse_the_manifest_itself`) — W-DRY's `yaml.safe_load` → RED. No second
manifest reader survives.

**P0 controls (harness sees breakage, so survivals are real):** all 5 MP wrong builds redden their
targeted pins; the meta-recursion stale hardcode reddens the coverage pin; the reference passes
29/29 and each new-gap survivor is paired with a reference control exhibiting the CORRECT behaviour
(exit 1 / honest summary / ok=False). The probe harness is not blind.

---

## VERDICT: **CONTRACT INSUFFICIENT**

The revision did its named job well: all five original wrong builds are genuinely closed (rebuilt
and confirmed RED, matching the reviser's table), the R1 trap is fixed, the from-import spy and the
META-RECURSION are real, and leg-5 (one manifest reader) is enforced. But the revision applied its
∀ / summary-honesty discipline to the **renderer's DIRTY-cell matrix** and stopped — leaving the
**wave-mode** failure/enforcement surface asymmetric with checkpoint. Three wrong builds pass the
full 29:

1. **MP-6 (headline):** `main`'s exit-code enforcement is a hand-list of 4 cells, not a ∀ —
   `main(["--wave","-k","x"])` returns 0 over a core `RED_ORPHANED`. The #344 disease at the very
   enforcement point #344 names, in the most-used mode.
2. **MP-7:** the wave summary can over-claim with alternate wording — MP-3 enumerates two forbidden
   tokens instead of asserting the positive scoped marker the design (§9.3) specifies.
3. **MP-8:** a NOT_RUN/omitted gate is tolerated in wave mode — the literal #344 event, pinned only
   in checkpoint.

One ∀ closes all three: (mode × gate × failure-mode) DERIVED and coverage-checked, driven at BOTH
the renderer AND `main`'s exit code, plus a positive wave-summary scoped-marker assertion.
