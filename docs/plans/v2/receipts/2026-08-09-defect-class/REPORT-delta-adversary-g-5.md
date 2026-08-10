brief-base v10 read
brief project v7 read

# REPORT-delta-adversary-g-5 — 6th adversary pass on INSTRUMENT G (`scripts/test_wave_gate.py`, #344/#345), the §11.9 whole-receipt byte-oracle

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT.** §11.9 genuinely closed every round-1..5 survivor (D2c, D1a, W-EXTRA, orphan-slot, all die; meta-recursion works). But the round-7 hunt found **TWO wrong builds that survive all 178 pins** — the "PIN-1 anchors EVERY line" claim is measurably false.
- **P1 (headline): wrong builds DID survive.** (a) **NOT_RUN/omitted honesty content is unanchored** — PIN-1's only FAIL cell is `ruff=dirty` (RED_ORPHANED); it NEVER produces a NOT_RUN (omitted) gate, so the NOT_RUN leg body, the **literal #344 "claimed but never run" detail line**, and the NOT_RUN orphan text are byte-anchored by NOTHING. R7a/R7b/R7c survive **178/0**. (b) **`main`'s STDOUT — the served surface — is unpinned**: `main` prints an over-claim banner (`all gates are clean, tree is green`) on a wave-clean PASS_SCOPED **exit-0** receipt, a FALSE CLEAR, surviving **178/0**.
- **The reviser's own justification is measurably false (R1-shaped recurrence):** `_canonical_leg_currency`'s comment says NOT_RUN "is covered by the derived-domain byte-oracle (PIN-1) and GateCurrency's own tests." PIN-1 produces no NOT_RUN cell; `test_pending_contract_gate.py` pins NO currency-render text (grep: zero). Neither leg holds.
- **Meta-recursion CONFIRMED:** grow `LegQualification.PARTIAL` without an anchor → **only** PIN-2 coverage reddens; the live-product combos auto-grow. The checked-variable proof is real — *but its checked set is `LegQualification`/`SummaryVerdict.__members__`, NOT the receipt-content space*, which is why NOT_RUN escapes.
- **All prior survivors DIE (independently rebuilt):** D2c✅ D1a-reword✅ D1a-extra✅ W-EXTRA-in-render(faithful A1)✅ W-EXTRA-receipt✅ orphan-slot✅ summary-alt-in-wave✅ W-main-noop(MP-1)✅.
- **2 deviations:** dev-1 (reuse-idiom) SAFE; **dev-2 is the QUANTIFIER-LAW miss** — "wave FAIL-detail anchored by PIN-1 content" holds for the RED_ORPHANED FAIL shape, FALSE for the NOT_RUN FAIL shape (Finding 1).
- **HONEST-BOUND check:** the goldens ARE honest (no false clear baked in) — so where PIN-1 *does* reach, drift reddens correctly. The gap is REACH, not a corrupt golden.
- **Packages considered:** none new — reference reuses in-repo `GateCurrency.render`/`gate_currency`/`_residuals_for`/`READERS`/`_run_selected_gates`; stdlib `enum`/`dataclasses`/`ast`. Verdict: reuse/bespoke-minimal.
- **Satisfiability (C-DEF): 178 passed / 0 failed** against an INDEPENDENT reference; **extraction NON-REGRESSIVE — `test_pending_contract_gate.py` 41 passed.** RED honesty (real repo): `--collect-only` → `ModuleNotFoundError: No module named 'wave_gate'` at :154, 1 error, right reason.
- **Graded:** `2fe81ba` · HEAD-at-report `2fe81ba` · **SAME** (working-tree `test_wave_gate.py` is `M`/uncommitted; scratch copy byte-identical, `diff -q` empty).
- **Provenance (#140):** `wave_gate.__file__`, `pending_contract_gate.__file__`, `loremaster.__file__` all resolve INSIDE `/home/ejprice/scratch-delta-g-5b/` (asserted; §1).
- **Missing pins:** MP-A `test_omitted_gate_receipt_is_byte_anchored` (extend PIN-1 domain to the NOT_RUN shape + coverage over the receipt-content space); MP-B `test_main_stdout_equals_the_honest_render` (pin the served surface).
- **Receipt pointers:** §1 satisfiability/provenance · §2 prior-survivors table · §3 round-7 findings (rendered receipts) · §4 meta-recursion · §5 deviations · §6 quantifier table · §7 reach table · §8 missing pins · §9 residuals · §10 probe record.

---

## 1. Satisfiability + extraction non-regression (provenance-asserted scratch, #140)
`./scripts/scratch_copy.sh /home/ejprice/scratch-delta-g-5b` → all imports INSIDE the copy:
```
wave_gate  -> /home/ejprice/scratch-delta-g-5b/scripts/wave_gate.py
pcg        -> /home/ejprice/scratch-delta-g-5b/scripts/pending_contract_gate.py
loremaster -> /home/ejprice/scratch-delta-g-5b/loremaster/loremaster/__init__.py
```
I authored an **INDEPENDENT reference** (`build_reference.py`, reproduced §10) from the CONTRACT's expected strings (not the reviser's scratch): the §11 seam + §11.8 typed `WaveReceipt` (`ReceiptHeader`/`RosterLine`/`GateLeg`/`DetailLines`/`WaveReceipt`/`compose_wave_receipt`) appended to `pending_contract_gate.py`, the ORIGINAL `_render_currency` **excised and replaced** (routed through `compose_wave_receipt` with the fork-1 typed detail), and a fresh `wave_gate.py`. Scratch `test_wave_gate.py` byte-identical to the working tree (`diff -q` empty).
```
C-DEF satisfiability : uv run pytest scripts/test_wave_gate.py -q            -> 178 passed / 0 failed
NON-REGRESSION       : uv run pytest scripts/test_pending_contract_gate.py -q -> 41 passed
RED honesty (real)   : uv run pytest scripts/test_wave_gate.py --collect-only -> ModuleNotFoundError:
                       No module named 'wave_gate' at scripts/test_wave_gate.py:154 — 1 error, right reason
```
The harness itself is guarded: `discriminate.py` asserts the pristine control is `(178,0,0)` and every mutation run is non-empty before reporting — the P0 lesson caught a real self-error this run (I first ran the harness under plain `python3`, which has no pytest, so an errored run read as "0/0 SURVIVES"; re-run under `uv run python` with the broken-run guard, §10).

## 2. Every prior survivor DIES — independently rebuilt (measured)
`discriminate.py`, positive control = pristine reference 178/0. Each wrong build = a one-line patch of MY reference; a "search NOT FOUND" aborts (so a mutation that silently no-ops cannot masquerade as a survivor).

| wrong build | result | reddened at |
|---|---|---|
| **D2c** (scoped-leg reworded to a false clear) | 174/4 DIES ✅ | PIN-1[wave-clean/wave-fail] + PIN-2 + `test_scoped_honesty_prose_is_sole_minted` |
| **D1a-reword** (RED_ORPHANED framing reworded) | 176/2 DIES ✅ | PIN-1[checkpoint-fail + wave-fail] |
| **D1a-extra** (extra over-claim line in FAIL detail) | 176/2 DIES ✅ | PIN-1[checkpoint-fail + wave-fail] |
| **W-EXTRA-in-render** (faithful delta-g-4 A1: append INSIDE `render_wave_receipt`) | 176/2 DIES ✅ | `test_render_wave_receipt_delegates_to_the_typed_receipt[wave/checkpoint]` |
| **W-EXTRA-receipt** (free append inside `WaveReceipt.render`) | 169/9 DIES ✅ | byte-oracle + `…fixed_typed_composition_no_free_append` + PIN-1 (all cells) |
| **orphan-slot** (extra line among a leg's orphans) | 174/4 DIES ✅ | `…one_leg_per_gate_orphans_folded[*-fail]` + PIN-1[*-fail] |
| **summary-alt-in-wave** (marker literal in wave_gate.py) | 177/1 DIES ✅ | `test_unqualified_marker_literal_absent_from_wave_gate` |
| **W-main-noop** (`main` returns 0 always, MP-1) | 164/14 DIES ✅ | `test_main_exit_code_reflects_…` + `test_main_exit_equals_the_renderer_verdict_over_every_cell[*]` |

The 5 section-1..7 originals (W1–W9) + MP-1..MP-8 are green on the pristine reference (178/0 = every pin satisfiable on correct code) and their killers are exercised above (MP-1/MP-6 via W-main-noop; W2/W9 omitted-cell enforcement is what W-main-noop's `[*-omitted]` reds prove; W1/W5 are structural/coverage pins green at 178/0). D2c and D1a were the round-6 survivors §11.9 targeted — **all closed.**

## 3. ROUND-7 HUNT — the crux. TWO honesty surfaces the byte-anchor does NOT reach.

### Finding 1 — NOT_RUN / omitted-gate honesty content is UNANCHORED (R7a/R7b/R7c survive 178/0)
PIN-1's cells are `{(checkpoint,clean)→PASS_FULL, (checkpoint,fail)→FAIL, (wave,clean)→PASS_SCOPED, (wave,fail)→FAIL}`, and **"fail" is always `_results(manifest, ruff="dirty")` = RED_ORPHANED**. No cell ever OMITS a gate, so the FAIL state's *other* receipt shape — a **NOT_RUN** gate (the literal #344 event: "a stage ran a subset and omitted a gate") — is never rendered by PIN-1. PIN-2 doesn't cover it either: its FAILING canonical is RED_ORPHANED (`_canonical_leg_currency`), and NOT_RUN is not a `LegQualification` member. And `test_pending_contract_gate.py` pins zero currency-render text. So three honesty lines are anchored by nothing:

| mutation | over-claim | result |
|---|---|---|
| **R7b-unrun-detail** | `"claimed but never run: {ids}"` → `"gates verified current: {ids}"` (the #344 line itself) | **178/0 SURVIVES ❗** |
| **R7a-notrun-body** | `"NOT_RUN — claimed by the manifest, never executed"` → `"NOT_RUN but assumed current and clean"` | **178/0 SURVIVES ❗** |
| **R7c-notrun-orphan** | NOT_RUN orphan text → `"gate ran and is current and clean, nothing owed"` | **178/0 SURVIVES ❗** |

**Rendered receipt (R7b, measured — the over-claim IS produced, on a real omitted-gate wave receipt):**
```
GATE BUNDLE [wave] — scope: -k test_changed_area
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    GREEN
  ruff         NOT_RUN — claimed by the manifest, never executed
      ORPHAN: gate CLAIMED by manifest and NOT RUN — says nothing about whether it passes
  pytest       SCOPED(-k test_changed_area) — NOT a currency clear; full run owed
  gates verified current: ruff                <-- OVER-CLAIM (was "claimed but never run: ruff")
CURRENCY   : FAIL — a claimed gate is RED with nobody's name on it, or was never run
  (this is NOT the deploy receipt: …)
ok=False (exit 1)
```
These over-claims land on a FAIL (exit-1) receipt (mixed message — the summary and exit stay honest, so severity is below a PASS-receipt false clear, per delta-g-4 R2). But the **§11.9 central claim** the brief asked me to verify — *"PIN-1 anchors EVERY line, so there is no subset to escape"* — is **empirically false**: the omitted/NOT_RUN receipt shape is a producible subset PIN-1 never compares, and it carries the very #344 line the instrument exists to protect. **R1 has NOT been dissolved; it recurred one shape over** (verdict-state ≠ receipt-content), with a false coverage claim in `_canonical_leg_currency` exactly as R1 was a false coverage claim in reviser-g-4 §6.

### Finding 2 — `main`'s STDOUT (the served surface) is UNPINNED — an exit-0 false clear survives
The honesty apparatus reaches `render_wave_receipt`'s RETURN VALUE (byte-oracle, delegation pin) and `main`'s EXIT CODE (MP-1/MP-6). **Nothing asserts `main`'s STDOUT equals the honest render.** `main` prints — and the print can inject an over-claim.

**W-main-print-banner** — add `print("all gates are clean, tree is green")` after printing the receipt. **178/0 SURVIVES.** Captured `main` stdout on a wave-clean (PASS_SCOPED, **exit 0**) run:
```
GATE BUNDLE [wave] — scope: -k test_changed_area
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    GREEN
  ruff         GREEN
  pytest       SCOPED(-k test_changed_area) — NOT a currency clear; full run owed
WAVE       : PASS — core is GREEN-or-owned; pytest ran SCOPED, full run still owed
  (this is NOT the deploy receipt: …)
all gates are clean, tree is green        <-- FALSE CLEAR injected in main, exit 0
__EXIT_CODE__ = 0
```
The honest receipt correctly says *"pytest ran SCOPED, full run still owed"*; `main`'s injected banner contradicts it (*"all gates are clean, tree is green"*), **exit 0**. An agent reading this stdout — the actual served surface (#344: "no CI, the bundle IS the enforcement point") — concludes the tree is fully clean. This is the #306/#344 false clear at the one surface the consumer reads.

Why it evades every source scan — it is the **enumerate-the-forbidden trap at the print boundary**: `test_unqualified_marker_literal_absent_from_wave_gate` forbids ONE phrase (`every claimed gate is GREEN or OWNED`); `test_wave_summary_strings_are_not_authored_in_wave_gate` forbids the two summary strings; `test_no_free_receipt_line_composition_outside_render` catches only `.append(str)`. An alternate wording via `print(...)` (or `list(lines) + [...]`) matches none, and the byte-oracle never sees stdout. (The banner I used — "all gates are clean, tree is green" — is literally the `W-summary-alt`/D1a wording the packet already knows about, now escaping through main.)

## 4. Meta-recursion — CONFIRMED as a checked variable, over the WRONG set
`grow-enum` (add `LegQualification.PARTIAL`, no anchor) → 238 passed / **1 failed**: only `test_every_typed_component_prose_is_byte_anchored_over_its_enum_domain` (PIN-2 coverage, `leg_anchor_names == set(LegQualification.__members__)`) reddens. `test_summary_verdict_combination_surface_equals_the_live_product` stays green (the P1 combos + live product auto-grow together) — the meta-recursion genuinely works. **BUT** the checked set is `LegQualification`/`SummaryVerdict.__members__`. NOT_RUN is not a member of either (it is a `GateCurrency` verdict that maps to `FAILING`), so growing the enum does not close Finding 1, and the coverage pin `test_wave_receipt_byte_anchor_covers_the_derived_verdict_state_domain` — which checks the cells produce every `SummaryVerdict` (3 values) — is satisfied while the FAIL state's NOT_RUN shape goes uncovered. The "checked variable" is checked over the enum domain, not the receipt-content space.

## 5. The two disclosed deviations (reviser §5), scrutinised
1. **Reuse-the-idiom vs refactor the checkpoint test — SAFE.** Both the `_render_currency` historical-header receipt (`test_checkpoint_receipt_preserves_the_historical_bytes`) and the `build_wave_receipt` bundle receipt (PIN-1) are anchored where their cells reach; the split introduces no gap of its own. (Finding 1 is orthogonal — it is about a cell PIN-1 *lacks*, not about this reuse choice.)
2. **"Wave FAIL-detail anchored by PIN-1 content, not a new constant" — this is the QUANTIFIER-LAW miss.** The claim holds for the RED_ORPHANED FAIL shape (D1a-reword/D1a-extra DIE at PIN-1[*-fail]) — but is **FALSE for the NOT_RUN FAIL shape**: the *same* `_detail_golden` has a second branch (`"claimed but never run"`) that no PIN-1 cell exercises (R7b survives). A safety property derived over one member of the FAIL set (RED_ORPHANED), stated over the whole FAIL set — CLAUDE.md's THE QUANTIFIER LAW, in migration clothes. The deviation is not merely a DRY choice; it silently narrowed the anchored FAIL surface to one of its two shapes.

**HONEST-BOUND verification (brief ask): the goldens are the audited honest prose, no false clear baked in.** `_SCOPED_HONESTY_GOLDEN = "NOT a currency clear; full run owed"`, `_WAVE_SUMMARY_PASS_SCOPED` = "…pytest ran SCOPED, full run still owed", `_WAVE_SUMMARY_FAIL` = "…RED with nobody's name on it, or was never run", `_HISTORICAL_CHECKPOINT_NOTE` (the not-deploy caveat) — all honest. So where PIN-1 *does* reach, drift reddens correctly (§2 confirms). The failure is REACH (the cells don't produce the NOT_RUN shape; stdout is off-limits), not a corrupt golden. The byte-oracle is not a false clear where the golden over-claims — I checked.

## 6. P1b — QUANTIFIER TABLE (every honesty invariant classified; every guarded row carries a receipt)
| # | invariant | classification | receipt |
|---|---|---|---|
| I1 | summary line == sole-minted `render_summary(verdict)` | **∀** over `SummaryVerdict` | reference green; PIN-2 |
| I2 | receipt render() = total composition, no free APPEND | **∀** over (mode × kind) | A1(in-render)/W-EXTRA-receipt/orphan DIE |
| I3 | scoped-leg honest content byte-anchored | **∀** over the wave PASS_SCOPED receipt | D2c DIES (PIN-1+PIN-2) |
| I4 | RED_ORPHANED FAIL detail framing byte-anchored | **∀** over the RED_ORPHANED FAIL receipt | D1a-reword/D1a-extra DIE |
| **I5** | **NOT_RUN / omitted-gate honesty lines byte-anchored** | **GUARDED — PIN-1 has no NOT_RUN cell; PIN-2 FAILING=RED_ORPHANED; pcg tests pin no render text** | **R7a/R7b/R7c SURVIVE 178/0** (Finding 1) |
| **I6** | **`main` STDOUT (served surface) == the honest render** | **MISSING — no pin captures main's stdout; MP-1/MP-6 pin exit code only** | **W-main-print-banner SURVIVES 178/0**, exit-0 false clear (Finding 2) |
| I7 | both paths share ONE composition / ONE minter (DRY #1) | **∀** (mutation, both paths+namespaces) | reference green; A7 idiom |
| I8 | anchored honesty-line SET is a checked variable | **∀** over `Leg/SummaryVerdict.__members__` — but NOT over the receipt-content space | grow-enum reddens coverage; **NOT_RUN escapes** |

**I5 and I6 are the guarded/missing rows, each with a surviving wrong build.** Every other honesty invariant is ∀ over a typed/byte domain and holds.

## 7. P1c — REACH ATTACK TABLE (per instrument). Legs: **E = empirical (wrong build in scratch)**, **C = construction-inspection.**
| instrument | site-set (reach) | DERIVED vs hand-list | coverage a checked variable? | effect vs proxy | verdict |
|---|---|---|---|---|---|
| PIN-1 byte-oracle `…derived_verdict_state_domain` | 4 cells = {PASS_FULL, PASS_SCOPED, RED_ORPHANED-FAIL} receipts | reach = a HARD-CODED cell list; "fail"≡`ruff=dirty` | coverage pin checks `SummaryVerdict.__members__` (3) — **but a verdict has ≥2 receipt shapes; NOT_RUN-FAIL is uncovered** | effect (bytes) | **PARTIAL — blind to the NOT_RUN receipt shape (E: R7a/b/c)** |
| PIN-2 per-component ∀ | `Summary/LegQualification.__members__` | DERIVED (live `__members__`) | YES for enum members; grow-enum reddens | effect | ✅ for the enum domain; **NOT_RUN not a member → not covered** |
| delegation `…delegates_to_the_typed_receipt` | `render_wave_receipt` return | DERIVED (== receipt.render()) | YES both modes | effect | ✅ (E: W-EXTRA-in-render DIES) |
| AST append-scan `…no_free_…_composition` | all of wave_gate.py + `_render_currency` body | reach DERIVED; forbidden shape = free-`str` **`.append`** ONLY | catches `.append`; **NOT `+`/list-literal/`print`** | source | **PARTIAL — form-specific; `print`/`+` in main evade (E: W-main-print-banner)** |
| marker/summary literal scans | wave_gate.py literals | forbids 3 EXACT phrases | — | source | ✅ for those 3; **alternate wordings escape (enumerate-the-forbidden)** |
| main exit-code (MP-1/MP-6) | `main` exit code == renderer verdict | DERIVED (`_RED_ENFORCEMENT_CELLS`) | YES | effect (exit) | ✅ (E: W-main-noop DIES) — **but exit code ≠ stdout content** |
| **served surface (main STDOUT)** | main's printed output | — | **NO — no pin reads main's stdout** | — | **MISSING (E: W-main-print-banner)** |

**Legs run:** I5/I6 rows and every DIES/SURVIVES verdict above are **EMPIRICAL** (discrimination harness + rendered-receipt probes, §10), each paired with the pristine 178/0 positive control. The reach failures are both the 7th-defeat class from CLAUDE.md: PIN-1's reach is a hidden constant (the 4 cells, `fail≡ruff-dirty`) rather than the receipt-shape space; the honesty guards' reach stops at `render_wave_receipt`'s return and does not extend to the print boundary.

**The author's own copy (INSTRUMENT 0), applied to PIN-1:** *"What is the SET of receipts PIN-1 anchors — is it DERIVED from the receipt-shape space (verdict × detail-branch × leg-verdict) or a hand-list of 4 cells keyed on `fail≡ruff-dirty` — and does a test go RED when a producible receipt shape (a NOT_RUN/omitted gate) is not among the anchored cells?"* Answer: the cells are a hand-list; the coverage pin checks only `SummaryVerdict` (3 values), so a second receipt shape for the same verdict is silently exempt → R7a/b/c.

## 8. MISSING PINS (the tests that should exist + the defects they catch)

### MP-A — `test_omitted_gate_receipt_is_byte_anchored` (closes Finding 1, the round-7 crux)
- **Defect caught:** an over-claim reworded onto the NOT_RUN leg body / the "claimed but never run" detail framing / the NOT_RUN orphan text — the LITERAL #344 honesty lines — on an omitted-gate receipt. Reproduced: R7a/R7b/R7c survive **178/0** (§3).
- **The pin:** extend PIN-1's `_BYTE_ORACLE_CELLS` with an OMITTED-gate cell in each mode (e.g. `_results(manifest, omit=(<scopable-or-core>,))` → a NOT_RUN gate), and byte-anchor the whole receipt against a golden whose NOT_RUN leg body + `"claimed but never run: {ids}"` framing are audited honest constants. **Critically, fix the coverage pin** `test_wave_receipt_byte_anchor_covers_the_derived_verdict_state_domain`: coverage over `SummaryVerdict.__members__` (3) is insufficient — the FAIL state has ≥2 producible receipt shapes (RED_ORPHANED vs NOT_RUN detail); coverage must be a checked variable over the **receipt-content space** (verdict × detail-branch, or the set of `GateCurrency` verdicts a leg can carry), so a producible shape with no anchored cell reddens. **P0 control:** the pin passes the honest reference and fails R7a/R7b/R7c.

### MP-B — `test_main_stdout_equals_the_honest_render` (closes Finding 2, the served surface)
- **Defect caught:** `main` prints/composes an over-claim into stdout (a banner, a footer) that the byte-oracle never sees — an exit-0 false clear on a PASS_SCOPED wave receipt. Reproduced: W-main-print-banner survives **178/0** (§3).
- **The pin:** capture `main`'s stdout (capsys / `redirect_stdout`) for representative (mode × clean/fail) cells with the loader+reader spies already used by the MP-1/MP-6 tests, and assert `stdout == "\n".join(str(l) for l in render_wave_receipt(...)[0])`. This converts the served surface from unpinned into a construction catch and makes the AST append-scan's form-specificity (`.append` only) moot for main. **P0 control:** passes the honest reference (main prints exactly the render), fails W-main-print-banner.

## 9. Residuals (individual verdicts — no "the rest look fine")
- **R1(carried) — DISSOLVED-CLAIM IS FALSE.** §11.9 asserts "R1 dissolved: no hand-named honesty subset — every line, derived." Finding 1 shows a producible receipt shape (NOT_RUN) whose lines PIN-1 never anchors, and `_canonical_leg_currency`'s "covered by PIN-1 + GateCurrency's own tests" is measurably false. **Verdict: real; R1 recurred as a false coverage claim (fix = MP-A).**
- **R2 — Finding-1 over-claims land on FAIL (exit-1) receipts.** Lower severity than Finding 2's exit-0 false clear (the authoritative summary + exit stay honest), but they are the literal #344 line and the design explicitly claims to close them. **Verdict: real, medium; fix = MP-A.**
- **R3 — Finding-2 is the higher-severity false clear (exit 0) but on a surface the design never claimed to pin.** A lead could rule main-stdout out of the honesty remit — but the trust doctrine + "#344: the bundle IS the enforcement point" argue stdout IS the served surface. **Verdict: real; surface it for the operator/lead ruling; recommend MP-B.**
- **R4 — the AST append-scan is form-specific (`.append` only).** `+`/list-literal/`print` compose output uncaught. Subsumed by MP-B (a stdout-equality pin makes composition-form irrelevant). **Verdict: real, subsumed.**
- **R5 (inherited) — `test_no_hardcoded_gate_id_collection`'s `canonical` is a hand-list of renamed-evadable ids;** behavioural `…enumerates_exactly_the_manifest_gates` + `…identified_by_reader_not_literal_id` are the coverage-checked instruments. Unchanged, met deliberately.
- **My reference SEAM is untyped** (a speed shortcut in MY probe; the contract file is mypy-clean, the reviser showed a typed reference is clean). Does not affect behavioural discrimination. **Verdict: my limitation, not the contract's.**

## 10. Full probe record (commands + real output)
**Scratch (provenance-asserted, #140):** `scratch_copy.sh /home/ejprice/scratch-delta-g-5b` → `wave_gate/pcg/loremaster.__file__` all inside scratch (§1).

**Discrimination harness (`discriminate.py`) — pristine control 178/0, then each build:**
```
POSITIVE CONTROL (pristine):        178 passed, 0 failed  OK
D2c                    174 passed / 4 failed  -> DIES ✅   [PIN-1 wave-clean/fail + PIN-2 + scoped-sole-mint]
D1a-reword             176 passed / 2 failed  -> DIES ✅   [PIN-1 checkpoint-fail + wave-fail]
D1a-extra              176 passed / 2 failed  -> DIES ✅   [PIN-1 checkpoint-fail + wave-fail]
W-EXTRA-in-render      176 passed / 2 failed  -> DIES ✅   [delegates_to_the_typed_receipt wave/checkpoint]
W-EXTRA-receipt        169 passed / 9 failed  -> DIES ✅   [byte-oracle + composition + PIN-1 all cells]
orphan-slot            174 passed / 4 failed  -> DIES ✅   [orphans_folded *-fail + PIN-1 *-fail]
summary-alt-in-wave    177 passed / 1 failed  -> DIES ✅   [unqualified_marker_literal_absent]
W-main-noop            164 passed / 14 failed -> DIES ✅   [main_exit_code + main_exit_equals_renderer *]
grow-enum (LegQual.PARTIAL, no anchor)  238 passed / 1 failed  [PIN-2 coverage ONLY -> checked-variable]
--- ROUND-7 HUNT ---
R7b-unrun-detail       178 passed / 0 failed  -> SURVIVES ❗  (Finding 1: "claimed but never run" reworded)
R7a-notrun-body        178 passed / 0 failed  -> SURVIVES ❗  (Finding 1: NOT_RUN leg body over-claim)
R7c-notrun-orphan      178 passed / 0 failed  -> SURVIVES ❗  (Finding 1: NOT_RUN orphan text over-claim)
W-main-print-banner    178 passed / 0 failed  -> SURVIVES ❗  (Finding 2: main stdout over-claim, exit-0 false clear)
```
Rendered over-claim receipts (R7b + W-main-print-banner) captured in §3, measured via `probe_show.py`/`probe_main.py`. The **P0 self-catch**: a first harness pass under plain `python3` (no pytest) returned "0/0 SURVIVES" for W-main-append/W-main-print-banner — a probe erroring, not surviving; re-run under `uv run python` with a `(178,0,0)`-control assertion and a broken-run guard gave the real verdicts above.

**Instruments (deliverables, brief-base §1 — scratch is disposable, reproduced verbatim):**

`build_reference.py` — independent reference. Load-bearing seam shape (read from the CONTRACT's expected strings):
```python
class LegQualification(Enum): CLEAN/OWNED/SCOPED/FAILING
class SummaryVerdict(Enum):   PASS_FULL/PASS_SCOPED/FAIL
class SummaryLine(str): __slots__=()
_SUMMARY_LINES = {PASS_FULL:"CURRENCY   : PASS — every claimed gate is GREEN or OWNED",
                  PASS_SCOPED:"WAVE       : PASS — core is GREEN-or-owned; pytest ran SCOPED, full run still owed",
                  FAIL:"CURRENCY   : FAIL — a claimed gate is RED with nobody's name on it, or was never run"}
summary_verdict(qs)=FAIL if any FAILING else PASS_SCOPED if any SCOPED else PASS_FULL
render_summary(v)=SummaryLine(_SUMMARY_LINES[v])                       # SOLE minter
_leg_qualification_for(verdict,*,scoped)=SCOPED / FAILING(in FAILING_VERDICTS) / OWNED(RED_ADJUDICATED) / CLEAN
_SCOPED_HONESTY="NOT a currency clear; full run owed"                  # honest golden
ReceiptHeader(lines).render()=list(lines)
RosterLine(m).render()=["  manifest   : {ids} ({n} gates)"]
GateLeg(currency,scoped_line).render()=[scoped_line or currency.render(), *["      ORPHAN: {o}" ...]]
DetailLines(lines).render()=list(lines)                               # () on PASS
_fail_detail(cs): "  RED with nobody's name on it: {orphaned}" / "  claimed but never run: {unrun}"   # <-- R7b: unrun unpinned
WaveReceipt(header,roster,legs,detail,summary,note,verdict); .ok=verdict is not FAIL
   .render()=[*header.render(),*roster.render(),*(l for leg in legs for l in leg.render()),
              *detail.render(), str(summary), note]
compose_wave_receipt(gate,manifest,results,*,header,scoped_selector)  # THE one composition, both paths
   scoped = scoped_selector is not None and READERS[reader] is JUnitReportReader and currency.ok
# ORIGINAL _render_currency EXCISED (re.subn, matched exactly once) and REPLACED:
_render_currency(...) = compose_wave_receipt(..., header=ReceiptHeader(("GATE CURRENCY — is every CLAIMED gate green, or owned?",)), scoped_selector=None).render(), .ok
# wave_gate.py: MODE_WAVE/MODE_CHECKPOINT; pytest_args_for; build_wave_receipt(header=ReceiptHeader((f"GATE BUNDLE [{mode}] — scope: {scope}",)), scoped_selector=" ".join(sel) if wave else None);
#   render_wave_receipt=build.render(),ok; main: argparse required mutually-exclusive --wave|--checkpoint + -k selector;
#   _run_selected_gates(runner,manifest,list(manifest.ids),pytest_args); print("\n".join(lines)); return 0 if ok else 1   # <-- Finding 2: stdout unpinned
```
`discriminate.py` — restores pristine between mutations; each mutation is a `(target∈{SEAM,WAVE,BASE}, search, replace)` one-line patch that ABORTS if `search` is not found (a mutation cannot silently no-op); asserts the pristine control is `(178,0,0)` and every run non-empty. The round-7 mutations: `R7b-unrun-detail` (`_fail_detail` unrun framing), `R7a-notrun-body` (`GateCurrency.render` NOT_RUN branch, target BASE), `R7c-notrun-orphan` (NOT_RUN orphan tuple text), `W-main-print-banner` (a `print(banner)` after main's receipt print).

---

## VERDICT: **CONTRACT INSUFFICIENT**

§11.9 did close every round-1..5 survivor — D2c, D1a (both shapes), W-EXTRA (both), orphan-slot all die; the meta-recursion is a genuine checked variable over the enum domains; satisfiability (178/0) and non-regression (41/0) hold; the goldens are honest. This is strong work.

**But the round-7 hunt the brief asked for found the claim it was told to verify — "PIN-1 anchors EVERY line, so there is no subset to escape" — to be empirically false, twice.** (1) PIN-1's byte-oracle never produces a NOT_RUN/omitted-gate receipt (its only FAIL cell is `ruff=dirty`=RED_ORPHANED), so the NOT_RUN leg body, the literal #344 `"claimed but never run"` detail line, and the NOT_RUN orphan text are anchored by nothing — R7a/R7b/R7c survive 178/0, and the reviser's `_canonical_leg_currency` claim that NOT_RUN "is covered by PIN-1 and GateCurrency's own tests" is measurably false on both legs (R1 recurring as a false coverage claim, one receipt-shape over). (2) The honesty apparatus's reach stops at `render_wave_receipt`'s return and `main`'s exit code; `main`'s STDOUT — the served surface an agent actually reads — is unpinned, so a `print("all gates are clean, tree is green")` produces an exit-0 false clear on a PASS_SCOPED wave receipt, surviving 178/0.

**Two missing pins close it:** MP-A (extend PIN-1's cells to the NOT_RUN/omitted receipt shape AND make its coverage a checked variable over the receipt-content space, not just `SummaryVerdict.__members__`) and MP-B (`test_main_stdout_equals_the_honest_render`, pinning the served surface). Both are proven discriminating (pass the honest reference, fail the surviving wrong builds). Routing per standing order: contract → adversary → build → cold audit.
