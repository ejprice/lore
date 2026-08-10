brief-base v10 read
brief project v7 read

# REPORT-delta-adversary-g-3 — 4th adversary pass on INSTRUMENT G (`scripts/test_wave_gate.py`, #344/#345), the §11 typed summary-honesty redesign

## Capability check (tool honesty — brief-base §4, first)
Everything the brief demanded was satisfiable. `scratch_copy.sh` built a provenance-asserted copy;
I authored an INDEPENDENT reference (the §11 seam extracted into `pending_contract_gate.py` + a
fresh `wave_gate.py`, NOT the reviser's) and ran the real 143-pin contract against it, against every
named survivor + the 5 originals + MP-6/MP-8 + the corrupted-minter variant + a NEW attack, plus the
meta-recursion / P3-both-sides / RED-honesty controls. `lore_comms` reachable (drained: no unread).
Edited ONLY scratch files; the graded `scripts/test_wave_gate.py` was never mutated in the main tree.
No impossibilities.

---

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT.** The §11 typed redesign genuinely closes ALL prior survivors
  (W-summary-alt/double/inline hand+minter, the 5 originals, MP-6, MP-8 — each independently rebuilt
  and confirmed caught) — but it opens **r5 (round 5): W-extra-line**, a wave receipt that over-claims
  a full clear on an ADDED alternate-wording line while calling `render_summary` honestly. Passes 143/143.
- **P1 (headline): `W-extra-line` passes 143/143.** In wave mode it emits the honest minted
  `render_summary(PASS_SCOPED)` line (so P3's sentinel still moves) AND appends
  `"SUMMARY: all gates are clean, tree is green"` — a FALSE CLEAR (pytest ran a `-k` SUBSET). Blind to
  P2b (no marker literal), P3 (render_summary IS called), P4 (marker-count 0). The contract pins the
  MINTED summary line but never forbids ADDITIONAL free-text lines — §11.2.4's typed `WaveReceipt`
  (the "no free-text append seam left" guarantee) is DESIGNED but NOT PINNED.
- **Were ALL survivors TRULY closed? YES — independently rebuilt & confirmed:** W-summary-alt 2f(P3+P4) ·
  W-summary-double 15f(P2b+P4) · W-summary-inline-hand 15f(P2b+P3+P4) · W-summary-inline-minter 2f(P2a+P4) ·
  W-main-noop 17f · W-DRY-reparse 1f(AST) · W-ruff-advisory 4f · W-echo 2f · W-main-wave-core 7f(MP-6) ·
  W-wave-notrun 7f(MP-8). Every one caught by its designated pin; none vacuous.
- **QUANTIFIER TABLE (P1b):** I1–I4, I6–I9 are ∀-over-inputs (reference-green + wrong-build receipts).
  **I5 (wave never over-claims) is the ONLY guarded row** — guarded by "the marker literal, wherever";
  receipt = W-extra-line survives (alternate-wording over-claim through the unguarded append door). Full table below.
- **REACH TABLE (P1c):** P1/P2a/P3 reach the MINTED line (DERIVED, coverage-checked, effect, mutation-proven —
  all EMPIRICAL). **P2b+P4 (summary honesty) reach = the ONE marker literal — a HIDDEN CONSTANT over the open
  vocabulary of over-claim wordings; the receipt-structure ("no free append line") is NOT a checked variable.**
  MISSING → r5. Full table below.
- **MISSING PIN (r5): `test_wave_receipt_is_the_fixed_composition_no_free_summary_append`** — pin §11.2.4's
  typed `WaveReceipt`: a clean wave receipt is EXACTLY `[*leg_lines(one-per-gate), str(render_summary(verdict)),
  NOT_DEPLOY_NOTE]`, so an extra over-claim line is unrepresentable. Catches W-extra-line; keeps all others caught.
- **Packages considered:** none new — reference composes in-repo `pending_contract_gate` machinery
  (`_run_selected_gates`, `_render_currency`, `_residuals_for`, `gate_currency`, `READERS`), stdlib `enum`,
  `str`-subclass `SummaryLine` (the `Rendered`/`SafeLine` idiom). Verdict = **keep/reuse** (contract enforces it).
- **Satisfiability (C-DEF): 143 passed / 0 failed** against my independent reference in provenance-asserted
  scratch; **extraction NON-REGRESSIVE — `test_pending_contract_gate.py` stays 41 passed** after the seam moves.
  RED honesty: real repo `--collect-only` → `ModuleNotFoundError: No module named 'wave_gate'` at line 149, 1 error.
- **Graded:** `1a5d9b3` · HEAD-at-report: `1a5d9b3` · SAME (graded the working-tree `test_wave_gate.py`,
  uncommitted `M`; scratch copy byte-identical, `diff -q` empty).
- **Provenance (#140):** `wave_gate.__file__`, `pending_contract_gate.__file__`, `loremaster.__file__` all
  resolve INSIDE `/home/ejprice/scratch-delta-adversary-g-3/` (asserted; receipt in Probe record).
- **P0 controls:** harness demonstrably sees breakage (10 wrong builds redden targeted pins; stale-reach control
  reddens the coverage pin; P3-both-sides reddens; RED-honesty errors). r5 paired with reference control (143/143)
  AND a stronger whole-receipt scan that discriminates. Not a blind probe.
- **Decisions-needed (forks, not resolved unilaterally):** (1) reviser fork-1 (checkpoint FAIL becomes a fixed
  line) still owed an operator ruling; (2) reviser fork-2 (PASS_SCOPED/FAIL fixed prose non-over-claiming is a
  one-time review item) — I CONFIRM this residual (see R3); (3) r5 fix form: minimal composition pin vs full
  typed-WaveReceipt return-surface change (I recommend the structural WaveReceipt — it IS §11.2.4).
- **Receipt pointers:** §1 (satisfiability+non-regression) · §2 (survivors rebuilt) · §3 (r5 finding + demo) ·
  §4 (quantifier table) · §5 (reach table) · §6 (missing pin) · §7 (residuals) · §8 (full probe record + instruments).

---

## 1. Satisfiability + extraction non-regression (provenance-asserted scratch, #140)
`./scripts/scratch_copy.sh /home/ejprice/scratch-delta-adversary-g-3` → provenance (all INSIDE scratch):
```
wave_gate  -> /home/ejprice/scratch-delta-adversary-g-3/scripts/wave_gate.py
pcg        -> /home/ejprice/scratch-delta-adversary-g-3/scripts/pending_contract_gate.py
loremaster -> /home/ejprice/scratch-delta-adversary-g-3/loremaster/loremaster/__init__.py
```
Reference = the §11 seam (`SummaryVerdict`/`LegQualification`/`summary_verdict`/`render_summary`/`SummaryLine` +
`_leg_qualification_for`) extracted into `pending_contract_gate.py`, `_render_currency` routed through the
shared minter, and an independent `wave_gate.py`. The scratch `test_wave_gate.py` is byte-identical to the
graded working-tree file (`diff -q` empty).
```
C-DEF satisfiability : uv run pytest scripts/test_wave_gate.py -q            -> 143 passed
NON-REGRESSION       : uv run pytest scripts/test_pending_contract_gate.py -q -> 41 passed   (seam extraction is behaviour-preserving)
RED honesty (real)   : uv run pytest scripts/test_wave_gate.py --collect-only -> ModuleNotFoundError: No module named 'wave_gate'
                       (scripts/test_wave_gate.py:149, importlib.import_module) — 1 error, right reason
```
The extraction-non-regression check the brief asked for: the summary seam moves into `pending_contract_gate.py`
and is consumed by BOTH `_render_currency` (checkpoint) and `render_wave_receipt` (wave); the OLD-world suite that
certifies `pending_contract_gate.py` stays green unchanged. (Verified separately: `test_pending_contract_gate.py`
references neither `_render_currency` nor the summary strings, so it pins the extraction only indirectly — the
byte-oracle pin `test_render_summary_pass_full_preserves_the_checkpoint_line` is the actual removed-behavior net.)

## 2. Did the §11 redesign TRULY close every survivor? (independent rebuild — not the reviser's claim)
Every build below is a targeted patch of MY independent reference, run against the full 143-pin contract in
provenance-asserted scratch. Reproduces the reviser's discrimination table — verified, not relayed.

| wrong build | my rebuild | designated pin(s) that fired | closed? |
|---|---|---|---|
| **W-summary-alt** (hand-authored alt wording, REPLACES minted line) | 2 failed | `test_both_currency_paths_derive_their_summary_from_the_one_minter` (P3) + `…marker_line_count…[checkpoint-clean]` (P4 positive control) | ✅ P3 |
| **W-summary-double** (forged marker line, non-last) | 15 failed | `test_unqualified_marker_literal_absent_from_wave_gate` (P2b) + `…marker_line_count…` (P4, many cells) | ✅ P2b+P4 |
| **W-summary-inline-hand** (marker+lie one line) | 15 failed | P2b + P3 + P4 | ✅ |
| **W-summary-inline-minter** (marker baked into `render_summary(PASS_SCOPED)`) | 2 failed | `test_render_summary_marker_appears_iff_pass_full` (P2a) + `…marker_line_count…[wave-clean]` (P4) | ✅ P2a+P4 (the residual a whole-line token would MISS) |
| W-main-noop | 17 failed | MP-1/MP-2 matrices + routing spy | ✅ |
| W-DRY-reparse | 1 failed | `test_wave_gate_does_not_reparse_the_manifest_itself` (AST belt) | ✅ |
| W-ruff-advisory (renderer) | 4 failed | `test_every_mode_gate_cell_fails_on_a_red[wave-ruff-*]` + main-exit | ✅ |
| W-echo-hardcode | 2 failed | `test_wave_scoped_selector_echo_equals_the_source` (2 of 3 values) | ✅ MP-5 |
| **W-main-wave-core** (core advisory in wave → exit 0) | 7 failed | `test_main_exit_equals_the_renderer_verdict_over_every_cell[wave-*]` (divergence) | ✅ **MP-6** |
| **W-wave-notrun** (omitted gate tolerated in wave) | 7 failed | `…[wave-*-omitted]` renderer + main-exit | ✅ **MP-8** |

W-summary-inline-minter is caught by **P2a** (the corrupted-minter form) — confirming the marker is a
discriminating SUBSTRING anchored to the minter, not a whole-line token; the reviser's claimed residual-catch holds.
All 10 genuinely caught; each paired with the reference control (143/143). Fork-3 (OWNED→PASS_FULL) is correct:
the byte-exact checkpoint PASS line fires for GREEN-or-OWNED, so P1 admits OWNED into PASS_FULL, and the reference
build's byte-preserved checkpoint passes P1 — RED_ADJUDICATED is "owned", not "failing".

## 3. Did it OPEN a new wrong build? YES — r5: W-extra-line, ONE survivor (the same summary-over-claim class §11 exists to kill)

**Root cause: §11 lifts honesty from string→type for the MINTED summary line, but the CONTRACT does not enforce
§11.2.4's structural guarantee that the receipt IS `[*leg_lines, minted_summary, note]` with no free-text append
seam.** The contract pins the pure functions (P1/P2a), the sole minter's marker literal (P2b), the derivation
(P3), and the marker-line count (P4) — all keyed to the ONE canonical marker string
`"every claimed gate is GREEN or OWNED"`. A wave receipt may still carry an ADDITIONAL line, in any OTHER wording,
that reads as a full clear — and nothing sees it.

| new wrong build | survives? | reference control | the hole |
|---|---|---|---|
| **W-extra-line** — honest `render_summary(PASS_SCOPED)` line + an appended `"SUMMARY: all gates are clean, tree is green"` in wave mode | **143/143** | ref emits only the honest SCOPED bound | **r5** — reach of the honesty guard = the ONE marker literal (P2b/P4); an alternate-wording ADDED line is silently exempt, and P3 passes because `render_summary` IS called |

**Direct demonstration (reference control + the false clear + blind pins + a discriminating stronger scan):**
```
REFERENCE clean-WAVE receipt (honest):
    pytest       SCOPED(-k test_changed_area) — NOT a currency clear; full run owed
    WAVE       : PASS — core is GREEN-or-owned; pytest ran SCOPED, full run still owed
   ok=True

W-extra-line clean-WAVE receipt (FALSE CLEAR):
    pytest       SCOPED(-k test_changed_area) — NOT a currency clear; full run owed
    WAVE       : PASS — core is GREEN-or-owned; pytest ran SCOPED, full run still owed
    SUMMARY: all gates are clean, tree is green      <-- pytest ran a -k SUBSET; "all gates clean" is a lie
   ok=True

What the CONTRACT's pins see:
  P4 marker-line-count  REF=0  BAD=0     (expects 0 for scoped wave -> BOTH pass -> P4 BLIND)
  P2b marker literal in bad receipt?  no  (the added line is not the marker -> P2b BLIND)
  P3 render_summary called (honest minted line present in BAD)?  True  (sentinel moves -> P3 BLIND)
What a STRONGER whole-receipt honesty scan sees:
  REF over-claim lines: []      BAD over-claim lines: ['SUMMARY: all gates are clean, tree is green']
  DISCRIMINATOR: reference clean=True | extra-line dirty=True  -> DISCRIMINATES
```
This is r5 recurring one round on: the honesty guard's reach moved from "the LAST line" (round 2/3) to "the
MARKER LITERAL wherever it appears" (§11/round 4) — but "the marker literal" is STILL a hidden constant over the
open set of "lines that read as a full clear". §11.5 claims "the redesign removes the free-text summary seam";
that is true of the DESIGN's typed `WaveReceipt` (§11.2.4) but FALSE of the CONTRACT, which never pins the
receipt's structure — `render_wave_receipt -> tuple[list[str], bool]` leaves `lines.append(<anything>)` wide open.

**Plausibility (threat model per CLAUDE.md "a gate needs a threat model — the honest developer").** The honest
builder wants an agent-consumer-friendly wave banner and appends "wave complete — gates green", forgetting pytest
ran scoped. That is precisely the honest-developer over-claim this whole packet targets; the door is a one-line
`lines.append`. A builder building to the CONTRACT (public seam + 4 pins) rather than to the DESIGN's WaveReceipt
walks straight through it.

## 4. P1b — QUANTIFIER TABLE (every invariant classified; every guarded row carries a receipt)

| # | invariant the contract intends | classification | receipt |
|---|---|---|---|
| I1 | mode REQUIRED & recorded | **∀** (render TypeError + cli SystemExit + header) | reference green |
| I2 | reported gate-set == manifest gate-set | **∀** over manifests (3 / +extra / −ruff), both-direction | reference green |
| I3 | claimed-but-omitted gate → NOT_RUN → fail | **∀ over (mode × gate)**, both modes | W-wave-notrun CAUGHT (7f); MP-8 closed |
| I4 | a RED gate fails the bundle (renderer) | **∀ over (mode × gate × {dirty,omitted})**, DERIVED + coverage-checked | reference green; W-ruff CAUGHT; meta-recursion proven (E) |
| **I5** | **a wave receipt never READS as an unqualified pass** | **GUARDED — "the marker literal, wherever" (P2b+P4); NOT ∀ over the receipt's lines** | **W-extra-line survives 143/143 (r5)** — alternate-wording over-claim through the unguarded append door |
| I6 | non-omittable core runs full in wave (never scoped) | **∀ over core gates** (dirty-cell, non-scopable branch) | reference green; W-ruff CAUGHT |
| I7 | the ENTRYPOINT `main` enforces the verdict | **∀ over (mode × gate × failure-mode)**, main-exit == renderer-ok, coverage-checked | W-main-wave-core CAUGHT (7f); MP-6 closed |
| I8 | `pytest_args_for` scopes only in wave | **∀** over mode (unit) | reference green |
| I9 | bundle routes through the ONE manifest reader | **∀** (spy both namespaces + AST belt) | W-main-noop/W-DRY CAUGHT |
| I10 | summary_verdict is the biconditional | **∀** over `LegQualification^leg_count` (64), coverage a checked variable | reference green; grow enum → 125 (E); stale hardcode reddens (E) |
| I11 | render_summary is the SOLE minter (marker ⟺ PASS_FULL) | **∀** over closed `SummaryVerdict` (3) | reference green; W-summary-inline-minter CAUGHT (P2a) |
| I12 | both currency paths DERIVE the summary from one minter | **∀** (mutation, both namespaces + both sides) | reference green; W-summary-alt CAUGHT; P3-both-sides reddens (E) |

**I5 is the ONLY guarded row, and it carries a surviving wrong build.** I3/I7 (the prior guarded rows, MP-8/MP-6)
are now genuinely ∀ and closed. I10–I12 (the new typed pins) are all ∀-over-a-closed-typed-domain with
reference-green + wrong-build receipts. The gap is exactly one level up from where §11 built its walls: the
per-line honesty is typed and ∀-checked, but the WHOLE-RECEIPT "no extra over-claim line" property is not pinned.

## 5. P1c — REACH ATTACK TABLE (per instrument). Legs: **E = empirical (wrong build / perturbation in scratch)**, **C = construction-inspection.**

| instrument | site-set | DERIVED vs hand-list | coverage a checked variable? | effect vs proxy | one-source-by-mutation | verdict |
|---|---|---|---|---|---|---|
| P1 `summary_verdict` biconditional | `LegQualification^leg_count` | **DERIVED** live (`_leg_qual_combos`) | **YES** — 64→125 on enum growth (E); stale hardcode reddens (E) | effect (typed return) | — | ✅ |
| P2a `render_summary` sole minter | closed `SummaryVerdict` (3) | **DERIVED** (iterate the enum) | YES — total mapping, missing value raises | effect | marker anchored to `render_summary(PASS_FULL)` + byte-oracle | ✅ |
| P2b AST mint/marker scan | `wave_gate.__file__` | reach DERIVED from module; **forbidden set = the ONE marker literal** | catches SummaryLine mint + marker literal (E: double/inline) | source | — | **partial — blind to alternate-wording lines (r5)** |
| P3 prove-sharing-by-mutation | both currency paths | DERIVED (mutate shared minter, both namespaces) | YES — un-share EITHER side reddens (E, both sides) | effect | **proves the MINTED line is shared; blind to an ADDITIONAL non-derived line** | ✅ for the minted line |
| P4 biconditional belt | producible receipts × marker-line-count | reach DERIVED (`_RED_ENFORCEMENT_CELLS`, coverage-pinned) | YES for the marker; **counts only the ONE marker string** | effect | — | **partial — blind to alternate-wording over-claim (r5)** |
| **whole-receipt "no free append line" (§11.2.4)** | **the receipt's line composition** | — | **NO — the receipt structure is NOT pinned; `lines.append(anything)` is unconstrained** | — | — | **MISSING (r5)** |
| renderer fail-matrix (MP-4/8) | (mode × gate × failure-mode) | DERIVED `_canonical_manifest_ids()` | YES — meta-recursion both dirs | effect | — | ✅ |
| entrypoint main-exit (MP-1/6) | main exit over the same cells | DERIVED — same `_ENFORCEMENT_PARAMS` | YES — main == renderer over every cell | effect (exit code) | — | ✅ |
| scopable-by-reader / routes-one-reader | which gate scopable / main's reader | DERIVED (junit-reader identity / spy) | YES | verdict / effect | reader identity | ✅ |
| AST reparse belt | `wave_gate.__file__` | DERIVED from module | catches `yaml.load*` door (E) | source | — | ✅ |

**Legs run:** the r5 row (P2b/P4/whole-receipt) is **EMPIRICAL** — W-extra-line survives 143/143 + reference
control + the stronger whole-receipt scan discriminates. P1 growth/stale, P3 both-sides, MP-6/MP-8 matrices are
**EMPIRICAL** (enum grown 64→125; stale coverage reddens; un-share reddens; W-main-wave-core/W-wave-notrun each
7f). P2a is EMPIRICAL (W-summary-inline-minter → 2f). scopable/routes-one-reader are corroborated by the
W5/MP-2/W-DRY empirical results + construction-inspection.

The author's own copy, applied to the summary-honesty guard (INSTRUMENT 0): *"What is the SET of receipt lines
this honesty guard forbids as over-claims — is it DERIVED from the receipt's STRUCTURE (the receipt is EXACTLY
leg_lines + one minted summary + note) or is it a hidden constant (the ONE marker string) — and does a test go
RED when an over-claim appears on a line the guard does not recognise as the marker?"* — P1/P2a/P3 answer yes for
the MINTED line; the whole-receipt "no free append seam" answers **no** (reach = the marker literal). This is the
7th/8th-defeat shape (reach is a hidden constant) at the summary, one round on from the "last line" reach.

## 6. MISSING PIN — the test that should exist + the defect + the reproduction

### MP-r5 — `test_wave_receipt_is_the_fixed_composition_no_free_summary_append`
- **Defect caught:** a wave receipt with a scoped leg that carries an unqualified/full-clear over-claim on an
  ADDED line in ANY wording other than the canonical marker (e.g. `"SUMMARY: all gates are clean, tree is green"`).
  The honest `render_summary(PASS_SCOPED)` line is present (P3 passes), the added line is not the marker literal
  (P2b/P4 blind) — a false clear in the mode agents run most, the #306/#312/#344 disease, one door over from the
  three §11 closed.
- **Reproduction (E):** `W-extra-line` — reference + `if mode == MODE_WAVE: lines.append("SUMMARY: all gates are
  clean, tree is green")` before the not-deploy note. Survives **143 passed, 0 failed**. The receipt visibly
  carries the over-claim (§3 demo); P2b/P3/P4 are all blind; a stronger whole-receipt scan reddens on it and
  passes on the reference.
- **The pin (STRUCTURAL — pin §11.2.4, which the design specified but the contract dropped):** require
  `render_wave_receipt` to expose the typed `WaveReceipt(leg_lines, verdict)` §11.2.4 designs, and assert its
  render IS the fixed composition — `receipt.render() == (*receipt.leg_lines, str(render_summary(receipt.verdict)),
  NOT_DEPLOY_NOTE)` AND, for a clean run, `len(receipt.leg_lines) == len(manifest.gates)` (one line per gate, no
  extras) — so an appended free-text line is unrepresentable at the type level (allowlist-the-safe over the
  receipt STRUCTURE, not the marker string). This is exactly the string→type lift §11 applied to the summary
  LINE, applied one level up to the RECEIPT.
- **Minimal alternative (cheaper, closes W-extra-line without a return-surface change):** on a CLEAN wave receipt,
  assert the count of lines that are neither a per-gate verdict line (via `_verdict_line`) nor the header/note is
  EXACTLY 1, and it equals `str(render_summary(PASS_SCOPED))`. An extra summary-region line makes the count 2 →
  RED. I recommend the STRUCTURAL WaveReceipt (it is §11.2.4 and removes the append seam by construction, not by
  counting); the minimal form is the belt if the return-surface change is deferred. **This is a fork for the
  author/lead** — minimal composition pin vs the full typed-WaveReceipt return surface — flagged, not resolved.

## 7. Residuals (individual verdicts — no "the rest look fine")
- **R1 — reviser fork-2 CONFIRMED as a real residual (build-time review item).** P2a catches a
  `render_summary(PASS_SCOPED)`/`FAIL` render CONTAINING the exact marker; a rephrased over-claim in those FIXED
  strings that AVOIDS the marker phrase (e.g. `render_summary(FAIL)` reading `"… PASS … tree current"`) is fixed
  prose the type system cannot judge — it carries no marker (P2a/P4 blind) and only fires on a red bundle (exit
  nonzero anyway). Since `render_summary` is the SOLE minter with FIXED strings, this is NOT a per-call wrong-build
  door (a builder cannot vary it); it is a one-time adversary/audit READ of the two new fixed strings. Met
  deliberately, not a new missing pin — but the lead should have the audit read `render_summary(PASS_SCOPED)` and
  `render_summary(FAIL)` for over-claim once the builder writes them.
- **R2 — reviser fork-1 (checkpoint FAIL becomes a FIXED line) still owed an operator ruling.** My reference used
  a fixed `render_summary(FAIL)` + a separate `reasons:` detail line (the reviser's recommended "preserve"
  option); all 41 OLD-world tests stayed green, so it is satisfiable either way. The contract deliberately does
  NOT byte-pin `render_summary(FAIL)`. Operator/lead decides preserve-as-detail vs drop.
- **R3 (inherited) — `test_no_hardcoded_gate_id_collection`'s `canonical` is a hand-list.** A hardcoded tuple of
  RENAMED ids evades the AST source scan; the behavioural `test_render_enumerates_exactly_the_manifest_gates` is
  the coverage-checked instrument (docstring says so). Unchanged — met deliberately.
- **MP-1 kept as smoke — correct.** `test_main_exit_code_reflects_the_bundle_verdict` (4 cells) is a positive
  smoke; the `…over_every_cell` matrix supplies the ∀ reach. No DRY violation.

## 8. Full probe record (commands + real output tails)
**Scratch (provenance-asserted, #140):** `./scripts/scratch_copy.sh /home/ejprice/scratch-delta-adversary-g-3`
→ `wave_gate.__file__`, `pending_contract_gate.__file__`, `loremaster.__file__` all resolve INSIDE the scratch
root (printed in §1).

**Discrimination (each wrong build = a targeted patch of the reference, full 143-pin contract):**
```
REFERENCE                  143 passed
W-summary-alt                2 failed  (P3 derive + P4[checkpoint-clean])
W-summary-double            15 failed  (P2b marker-literal + P4 many cells)
W-summary-inline-hand       15 failed  (P2b + P3 + P4)
W-summary-inline-minter      2 failed  (P2a marker_appears_iff_pass_full + P4[wave-clean])
W-main-noop                 17 failed  (MP-1/MP-2 matrices + routing spy)
W-DRY-reparse                1 failed  (AST reparse belt)
W-ruff-advisory              4 failed  (fail-matrix[wave-ruff-*] + main-exit)
W-echo-hardcode              2 failed  (MP-5, 2 of 3 selector values)
W-main-wave-core             7 failed  (main-exit divergence — MP-6)
W-wave-notrun                7 failed  (omitted-cell ∀ renderer+main — MP-8)
W-extra-line               143 passed  <-- SURVIVOR (r5)
```

**Meta-recursion (P1 reach a checked variable):**
```
baseline P1 params (LegQualification=4 ^ 3 gates)  = 64
grow LegQualification (+EXPIRED, 5 members)         -> 125 ; coverage pin GREEN (both derive live)
hardcode _LEG_QUAL_COMBOS[:10] (scratch contract)   -> test_summary_verdict_combination_surface_equals_the_live_product REDDENS
                                                        (both-direction diff: missing=[54 combos], stale=[])
```

**P3 both-sides DRY proof:**
```
un-share _render_currency (hand-author its PASS line, keep wave sharing)
  -> test_both_currency_paths_derive_their_summary_from_the_one_minter REDDENS
     ("the checkpoint path summary did not move under the shared-minter mutation — two sources of truth, #102/#120")
(the wave side is symmetric: W-summary-alt un-shares wave -> same pin reddens)
```

**RED honesty (real repo, no wave_gate.py):** `uv run pytest scripts/test_wave_gate.py --collect-only` →
`ModuleNotFoundError: No module named 'wave_gate'` at `scripts/test_wave_gate.py:149` (importlib.import_module),
`no tests collected, 1 error`. Right reason.

**P0 controls:** all 10 named wrong builds redden their targeted pins; the stale-reach control reddens the
coverage pin; P3-both-sides reddens; RED-honesty errors; the reference passes 143/143 with an HONEST wave receipt
(no over-claim line, §3 demo). The r5 survival is paired with (a) the reference control, (b) a directly-rendered
over-claiming receipt, (c) a stronger whole-receipt scan that reddens on the survivor and passes on the reference.
The probe harness is demonstrably not blind.

**Instruments (deliverables, per brief-base §1 — the scratch tree is disposable).** Reproduced verbatim so the
claims are re-runnable without the scratch dir:
- Reference seam (extracted into `pending_contract_gate.py`), IDENTICAL in shape to the reviser's:
```python
class LegQualification(enum.Enum): CLEAN="clean"; OWNED="owned"; SCOPED="scoped"; FAILING="failing"
class SummaryVerdict(enum.Enum):   PASS_FULL="pass_full"; PASS_SCOPED="pass_scoped"; FAIL="fail"
class SummaryLine(str): __slots__=()
def summary_verdict(qs):
    if any(q is LegQualification.FAILING for q in qs): return SummaryVerdict.FAIL
    if any(q is LegQualification.SCOPED  for q in qs): return SummaryVerdict.PASS_SCOPED
    return SummaryVerdict.PASS_FULL
_SUMMARY_LINES = {PASS_FULL:"CURRENCY   : PASS — every claimed gate is GREEN or OWNED",  # byte-exact
                  PASS_SCOPED:"WAVE       : PASS — core is GREEN-or-owned; pytest ran SCOPED, full run still owed",
                  FAIL:"CURRENCY   : FAIL — a claimed gate is RED with nobody's name on it, or was never run"}
def render_summary(v): return SummaryLine(_SUMMARY_LINES[v])   # SOLE minter
def _leg_qualification_for(verdict,*,scoped):
    if verdict in FAILING_VERDICTS: return LegQualification.FAILING
    if scoped: return LegQualification.SCOPED
    if verdict == VERDICT_RED_ADJUDICATED: return LegQualification.OWNED
    return LegQualification.CLEAN
# _render_currency tail routed through summary_verdict/render_summary (all legs scoped=False)
```
- `render_wave_receipt` core (shares the minter):
```python
for spec in manifest.gates:
    currency = _gate_currency_for(gate, spec, results.get(spec.id), expired)
    scoped = READERS[spec.reader] is JUnitReportReader and mode==MODE_WAVE and currency.ok
    leg_quals.append(_leg_qualification_for(currency.verdict, scoped=scoped))
    lines.append(f"  {spec.id:<12} SCOPED({sel}) — NOT a currency clear; full run owed" if scoped else currency.render())
verdict = summary_verdict(leg_quals); ok = verdict is not SummaryVerdict.FAIL
lines.append(str(render_summary(verdict))); lines.append(_NOT_DEPLOY_NOTE)   # <-- the append seam r5 exploits
```
- **The r5 wrong build (one added line):** `if mode == MODE_WAVE: lines.append("SUMMARY: all gates are clean, tree is green")` inserted before the not-deploy note.
- The full harness (`build_reference.py`, `discriminate.py`, `demo_extra_line.py`) lived in
  `/home/ejprice/scratch-delta-adversary-g-3/` (disposable); the load-bearing logic is reproduced above.

---

## VERDICT: **CONTRACT INSUFFICIENT**

The §11 typed redesign did its named job, and did it well: the string→type lift genuinely makes the marker-literal
over-claim unrepresentable, and every prior survivor — W-summary-alt (P3), W-summary-double (P2b+P4),
W-summary-inline hand (P2b+P3+P4) and corrupted-minter (P2a+P4), the 5 originals, MP-6 and MP-8 — is independently
rebuilt and confirmed caught, with the P1 combination surface a checked variable (64→125) and P3 a real
both-sides DRY proof. Satisfiability holds (143/0) and the extraction is non-regressive (41/0).

But the redesign walled off the MINTED summary line and left the RECEIPT itself unwalled. The honesty guard's
reach is still a hidden constant — it moved from "the last line" to "the ONE marker literal" — over the open
vocabulary of over-claim wordings, and §11.2.4's typed `WaveReceipt` (the "no free-text append seam left"
guarantee the whole argument rests on) is DESIGNED but NOT PINNED by the contract. So **W-extra-line** — an honest
`render_summary(PASS_SCOPED)` line plus an appended alternate-wording `"all gates are clean, tree is green"` in
wave mode — over-claims a full currency clear while pytest ran a `-k` subset, and passes all 143.

**One missing pin closes it:** `test_wave_receipt_is_the_fixed_composition_no_free_summary_append` — pin §11.2.4's
typed `WaveReceipt` so the receipt IS `[*leg_lines(one-per-gate), str(render_summary(verdict)), NOT_DEPLOY_NOTE]`,
making an extra over-claim line unrepresentable at the type level (the string→type lift applied to the RECEIPT,
not just the LINE). Fork for the author/lead: the structural WaveReceipt (durable, changes the return surface) vs
a minimal clean-wave composition/line-count pin (cheap belt). Routing per standing order: contract → adversary →
build → cold audit.
