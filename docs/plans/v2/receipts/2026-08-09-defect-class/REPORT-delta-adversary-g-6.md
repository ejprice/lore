brief-base v10 read
brief project v7 read

# REPORT-delta-adversary-g-6 — 7th adversary pass on INSTRUMENT G (`scripts/test_wave_gate.py`, #344), the §11.10 TERMINAL served-bytes fix

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT.** §11.10 genuinely closes both delta-g-5 breaks (F1 NOT_RUN,
  F2 main stdout/stderr) on the STANDARD served surface — but the round-8 hunt found **TWO wrong
  builds that survive all 187 pins**, both exit-0 false clears, both the F1/F2 class one axis over.
- **P1 (headline): wrong builds DID survive.** (Gap 1, PRIMARY/undisclosed) **W-main-empty-selector**
  — a `main` over-claim on the empty-selector wave path (`wave_gate.py --wave`, no `-k`) survives
  **187/0**; MP-B fixes the selector to a NON-EMPTY value in every wave cell and leg-2 excludes `main`,
  so main's served bytes on that production-reachable exit-0 path are anchored by NOTHING. (Gap 2,
  secondary/within the reviser's disclosed composer bound but shown to admit EXIT-0) **W-compose-multiowned**
  — an over-claim injected on a 2+-owned (exit-0 PASS) receipt survives **187/0**; MP-A/MP-B/leg-2 are all
  single-gate-non-green, so multi-gate shapes escape.
- **Prior survivors ALL DIE (independently rebuilt):** R7a/R7b/R7c (F1), W-main-print-banner (F2 stdout),
  W-main-print-stderr (round-8 stderr door), new-verdict-domain (leg-1), new-render-branch (leg-2),
  R-adjudicated-body — every one reddens for the right reason on my independent reference.
- **The reviser's D2 deviation claim is measurably false (R1-shaped recurrence):** REPORT-reviser-g-6 D2
  asserts "main's own branches ride MP-1/MP-6/MP-B." MP-B's wave cells all pass `-k …`; no test drives
  `main(["--wave"])`, so a main branch on the empty-selector axis is unreached — a false completeness
  claim about `main`, one axis over, exactly the shape that recurred every prior round.
- **P1b QUANTIFIER TABLE** (§6): I1–I8 hold; **I-served-main is GUARDED** (MP-B fixes the selector axis →
  W-main-empty-selector) and **I-multigate is GUARDED** (single-gate domain → W-compose-multiowned).
- **P1c REACH TABLE** (§7): MP-B's main-input reach is a HIDDEN CONSTANT (fixed selector, single-gate,
  one manifest), NOT a checked variable; leg-2's reach excludes `main` by construction — the 7th-defeat
  class (reach as a hidden constant) at the served surface. Empirical legs run + P0 controls.
- **MISSING PINS:** MP-C `test_main_served_output_anchored_on_the_empty_selector_wave_path` (Gap 1) +
  the deeper fix — make main's branch reach a CHECKED VARIABLE (extend leg-2 to `main` over mode ×
  VERDICT_* × selector-state). Both proven discriminating (P0: pass the honest reference, fail the survivor).
- **Satisfiability (C-DEF): 187 passed / 0 failed** vs an INDEPENDENT reference; **extraction NON-REGRESSIVE
  — `test_pending_contract_gate.py` 41/0.** RED honesty (real repo): `--collect-only` → `ModuleNotFoundError:
  No module named 'wave_gate'` at :154 — RED for the right reason.
- **Graded:** `4ceac32` · HEAD-at-report `4ceac32` · **SAME**.
- **Provenance (#140):** `wave_gate.__file__` / `pending_contract_gate.__file__` / `loremaster.__file__`
  all resolve INSIDE `/home/ejprice/scratch-delta-g-6/` (asserted; §1).
- **Packages considered:** none new — reference reuses in-repo `GateCurrency.render` / `gate_currency` /
  `_residuals_for` / `READERS` / `_run_selected_gates`; stdlib `enum`/`dataclasses`/`ast`; probes use stdlib
  `contextlib.redirect_stdout` + pytest `capfd`/`monkeypatch`. Verdict: reuse/bespoke-minimal.
- **Receipt pointers:** §1 satisfiability/provenance · §2 prior-survivors DIE table · §3 the two round-8
  survivors (rendered bytes) · §4 missing-pin P0 proof · §5 deviations scrutiny · §6 quantifier table ·
  §7 reach table · §8 missing pins · §9 residuals · §10 probe record + instruments.

---

## 1. Satisfiability + extraction non-regression (provenance-asserted scratch, #140)
`./scripts/scratch_copy.sh /home/ejprice/scratch-delta-g-6` → all imports INSIDE the copy:
```
wave_gate  -> /home/ejprice/scratch-delta-g-6/scripts/wave_gate.py
pcg        -> /home/ejprice/scratch-delta-g-6/scripts/pending_contract_gate.py
loremaster -> /home/ejprice/scratch-delta-g-6/loremaster/loremaster/__init__.py
GATE_OUTCOME_VERDICTS -> ('GREEN', 'RED_ADJUDICATED', 'RED_ORPHANED', 'NOT_RUN')
```
I authored an **INDEPENDENT reference** (`build_reference.py`, §10) from the CONTRACT's expected strings +
the delta-g-5 §10 / reviser-g-6 §8 documented shapes: the §11 seam (`LegQualification`/`SummaryVerdict`/
`SummaryLine`/`summary_verdict`/`render_summary`), §11.8 typed `WaveReceipt` (`ReceiptHeader`/`RosterLine`/
`GateLeg`/`DetailLines`/`WaveReceipt`/`compose_wave_receipt`), §11.10 `GATE_OUTCOME_VERDICTS`, the ORIGINAL
`_render_currency` **excised and replaced** (routed through `compose_wave_receipt`, fork-1 typed detail), and
a fresh `wave_gate.py`.
```
C-DEF satisfiability : uv run pytest scripts/test_wave_gate.py -q             -> 187 passed / 0 failed
NON-REGRESSION       : uv run pytest scripts/test_pending_contract_gate.py -q -> 41 passed / 0 failed
RED honesty (real)   : uv run pytest scripts/test_wave_gate.py --collect-only -> ModuleNotFoundError:
                       No module named 'wave_gate' at scripts/test_wave_gate.py:154 — right reason
```
The harness is guarded: `discriminate.py` asserts the pristine control is exactly `(187, 0)`, every mutation
ABORTS at build time if its search string is not found (a mutation cannot silently no-op), and a
collection-errored run is classed BROKEN, never a false SURVIVES (the P0 self-catch lesson).

## 2. Every prior survivor DIES — independently rebuilt (measured)
`discriminate.py`, positive control = pristine reference **187/0**. Each wrong build is a one-line patch of MY
reference; a "search NOT FOUND" aborts.

| wrong build | result | reddened at (right reason) |
|---|---|---|
| **R7a-notrun-body** (NOT_RUN body → "assumed current and clean") | 185p/2f **DIES** | per-verdict leg anchor + MP-A |
| **R7b-unrun-detail** ("claimed but never run" → "gates verified current") | 186p/1f **DIES** | MP-A whole-receipt oracle |
| **R7c-notrun-orphan** (NOT_RUN orphan → "gate ran and is current and clean") | 186p/1f **DIES** | MP-A whole-receipt oracle |
| **W-main-print-banner** (stdout over-claim on exit-0 receipt) | 186p/1f **DIES** | MP-B (F2 stdout) |
| **W-main-print-stderr** (over-claim to STDERR on exit-0 path) | 186p/1f **DIES** | MP-B (round-8 stderr door) |
| **new-verdict-domain** (new `VERDICT_*` w/o golden) | 180p/7f **DIES** | leg-1 source pin + coverage |
| **new-render-branch** (render branch no cell reaches) | 186p/1f **DIES** | leg-2 branch coverage |
| **R-adjudicated-body** (RED_ADJUDICATED body reword) | 185p/2f **DIES** | per-verdict anchor + §11.9 PIN-2 |

`discriminate.py` verdict for these eight: **all DIE for the right reason.** F1, F2, the round-8 stderr door,
leg-1, and leg-2 all hold on the standard surfaces. This is strong work — §11.10 is real.

## 3. ROUND-8 HUNT — TWO wrong builds survive 187/0 (the served surface is NOT terminal)

### Gap 1 (PRIMARY, undisclosed) — `main`'s served bytes are UNANCHORED on the empty-selector wave path
MP-B (`test_main_served_output_equals_the_honest_render_over_the_complete_outcome_domain`) is the F2 fix: it
drives the REAL `main` over (mode × `GATE_OUTCOME_VERDICTS`), `capfd` both streams, and asserts
`stdout == render`, `stderr == ""`. But **every wave cell fixes the pytest selector to a non-empty value**
(`["--wave", "-k", "test_changed_area"]`); a grep of the whole file confirms **NO test ever drives
`main(["--wave"])`** (empty/absent `-k`). Yet `wave_gate.py --wave` with no selector is production-reachable,
and renders an **exit-0 PASS_SCOPED** receipt (measured, pristine reference):
```
ok=True (exit 0)
'GATE BUNDLE [wave] — scope: '
"  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)"
'  typecheck    GREEN'
'  ruff         GREEN'
'  pytest       SCOPED() — NOT a currency clear; full run owed'
'WAVE       : PASS — core is GREEN-or-owned; pytest ran SCOPED, full run still owed'
"  (this is NOT the deploy receipt: ...)"
```
**W-main-empty-selector** — `main` prints `"full tree scanned — all gates clean"` only when
`mode == MODE_WAVE and not args.selector`. Because MP-B never drives `main(["--wave"])`, and leg-2 EXCLUDES
`main` (reviser D2), the branch is anchored by nothing. **Survives 187/0.** Served stdout on `wave_gate.py --wave`
(P0-proven, §4):
```
full tree scanned — all gates clean         <-- FALSE CLEAR injected in main, exit 0
GATE BUNDLE [wave] — scope:
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    GREEN
  ruff         GREEN
  pytest       SCOPED() — NOT a currency clear; full run owed
WAVE       : PASS — core is GREEN-or-owned; pytest ran SCOPED, full run still owed
  (this is NOT the deploy receipt: ...)
```
An agent running `wave_gate.py --wave` (the natural wave invocation, sans a scope) reads `full tree scanned —
all gates clean`, exit 0 — the #306/#344 false clear at the served surface, on a path the "served bytes are
anchored over the complete domain" claim never touched. **This is the F1/F2 class one axis over:** the anchor's
domain is "complete over VERDICT_*" but silently FIXES the pytest-selector axis, and a `main` branch keys on it.
The reviser's D2 claim *"main's own branches ride MP-1/MP-6/MP-B"* is thereby falsified — MP-B's domain is not
complete over main's INPUT space (it is (mode × VERDICT_*) with a FIXED selector + FIXED manifest).

⚠ Also a SPEC SILENCE surfaced (scope law — escalate, never resolve): the contract neither pins that `--wave`
REQUIRES a `-k` selector (which would make this path unreachable), nor anchors the served bytes of
`main(["--wave"])`. It does NEITHER. Two builders could disagree (require-`-k` vs optional-`-k`); the
optional-`-k` builder ships the unanchored exit-0 path. Either resolution closes Gap 1.

Honest calibration (§6 / trust doctrine — stated, not glossed): the surviving build ADDS a branch beyond the
minimal `print("\n".join(lines))`; honest-developer plausibility is MARGINAL-TO-MODERATE (the empty-selector
wave runs pytest FULL — `pytest_args_for(WAVE, []) == ()` — yet renders the leg SCOPED, an inconsistency that
invites a "helpful" full-run banner). But by the packet's OWN operating standard (rounds 2–7 each treated a
surviving over-claim as INSUFFICIENT regardless of the mutation's plausibility) and the P1c reach test (a guard
whose reach is a hidden constant is the 7th-defeat class), a surviving exit-0 false clear on a production-
reachable served surface is a blocker.

### Gap 2 (secondary — within the reviser's DISCLOSED composer bound, but shown to admit EXIT-0)
MP-A/MP-B/leg-2 all realise ONE non-green gate per cell (rest GREEN). Multi-gate COMBINATION receipt shapes are
never produced. **W-compose-multiowned** — `compose_wave_receipt` appends `"  all owned — tree fully current"`
to the header when `len([c for c in currencies if c.verdict == RED_ADJUDICATED]) >= 2`. A 2+-owned receipt is
**exit-0 PASS** (all owned → PASS_FULL/PASS_SCOPED); no MP-A/MP-B cell produces it; `compose` is not a render
method (leg-2 blind). **Survives 187/0.** Served bytes (measured, checkpoint, 2 owned gates):
```
GATE BUNDLE [checkpoint] — scope:
  all owned — tree fully current              <-- FALSE CLEAR injected in compose, exit 0
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    RED_ADJUDICATED — 1 residual(s), owned by: ...
  ruff         GREEN
  pytest       RED_ADJUDICATED — 1 residual(s), owned by: ...
CURRENCY   : PASS — every claimed gate is GREEN or OWNED
  (this is NOT the deploy receipt: ...)
```
This is the reviser's **DISCLOSED** composer-novel-axis residual (§11.10.2 honest bound: "a composer branch
keyed on a NOVEL axis is the named residual; re-open: a composer conditional on a new axis → add that axis to
the domain") — gate-CARDINALITY≥2 is such an axis. Adversarial: the HONEST version `if owned:` fires on the
single-owned MP-A cell and DIES there (MP-A anchors the single-owned receipt to an empty detail/no extra line),
so only the contrived `>= 2` form survives. **BUT** the disclosure treated FAIL-receipt over-claims as
lower-severity; this shows the single-gate domain also admits an **exit-0 PASS** false clear. I surface it as
a residual confirming the same single-gate-domain class as Gap 1, not as an independent blocker.

## 4. The missing pin, P0-proven (positive + negative controls)
The proposed Gap-1 pin drives `main(["--wave"])` (empty selector) with the SAME loader/reader/render-capture
harness MP-B uses, and asserts `stdout == "\n".join(render) + "\n"`, `stderr == ""`, `(code==0)==ok`:
```
=== P0 POSITIVE CONTROL: pristine reference ===
  exit=0 ok=True  stdout_matches=True  stderr_empty=True exit_agrees=True   -> PIN PASSES
=== NEGATIVE CONTROL: W-main-empty-selector ===
  exit=0 ok=True  stdout_matches=False stderr_empty=True exit_agrees=True   -> PIN FAILS (over-claim caught)
    served stdout : 'full tree scanned — all gates clean\nGATE BUNDLE [wave] — scope: \n...'
    honest render : 'GATE BUNDLE [wave] — scope: \n...'
```
The pin PASSES the honest build and FAILS the survivor — discriminating, per P0. (`probe_missing_pin.py`, §10.)

## 5. The five reviser deviations, scrutinised for a false clear
1. **D1 — leg-2 targets the DERIVED render-method set, not the composer.** SOUND as far as render methods go
   (new-render-branch DIES). But the render/composer split is EXACTLY where Gap 1/Gap 2 live: leg-2 covers
   neither `main` nor `compose`, and MP-A/MP-B's single-gate fixed-selector domain doesn't reach the composer's
   cardinality axis or main's selector axis. The bound the reviser wrote for the COMPOSER (novel-axis residual)
   is real; the bound was NOT written for `main`'s input axes — that omission is Gap 1.
2. **D2 — leg-2 drives `render_wave_receipt`, NOT `main`; "main's own branches ride MP-1/MP-6/MP-B."**
   **FALSE-CLEAR (the R1-shaped recurrence).** MP-1/MP-6/MP-B all drive main with a FIXED (non-empty in wave)
   selector; main's empty-selector-wave branch rides NONE of them. This is the exact false-completeness claim
   about a coverage surface that recurred as R1 (reviser-g-4) and the `_canonical_leg_currency` claim (g-5).
3. **D3 — MP-B drives the complete VERDICT_* domain incl. RED_ADJUDICATED-through-main.** SOUND and STRONG (the
   owning-registry + self-destruct neutralisation genuinely realises the OWNED shape through the entrypoint;
   `test_mp_b_domain_drives_every_closed_verdict_through_main` confirms PASS_SCOPED is reached). No false clear —
   this is the best part of §11.10. Its LIMIT is that the domain is (mode × VERDICT_*), single-gate, fixed selector.
4. **D4 — NOT_RUN orphan byte-anchored to production's exact prose.** SOUND (R7c DIES). Verified the golden
   `_notrun_orphan_text` is byte-identical to production `_render_currency`'s NOT_RUN currency prose.
5. **D5 — `_expected_receipt_lines` extended with a NOT_RUN branch (one whole-receipt golden builder).** SOUND
   (R7a/R7b DIE via MP-A). The NOT_RUN body/detail/orphan goldens are INDEPENDENT (not re-derived from the
   receipt), so a mutation drifts rather than moving with it — verified by R7a/b/c reddening.

## 6. P1b — QUANTIFIER TABLE (every honesty invariant classified; every guarded row carries a receipt)
| # | invariant | classification | receipt |
|---|---|---|---|
| I1 | summary line == sole-minted `render_summary(verdict)` | **∀** over `SummaryVerdict` | reference green; PIN-2 |
| I2 | receipt render() = total typed composition, no free APPEND | **∀** over (mode × kind) | W-EXTRA/orphan-slot DIE (g-5) |
| I3 | scoped-leg honest content byte-anchored | **∀** over wave PASS_SCOPED receipt | D2c DIES (g-5) |
| I4 | RED_ORPHANED / RED_ADJUDICATED leg bodies byte-anchored | **∀** over VERDICT_* leg domain | R-adjudicated-body DIES |
| I5 | NOT_RUN body/detail/orphan byte-anchored (F1) | **∀** over `GATE_OUTCOME_VERDICTS` (MP-A) | R7a/R7b/R7c DIE |
| I6 | `main` STDOUT+STDERR == honest render on the STANDARD surface (F2) | **∀** over (mode × VERDICT_*), FIXED selector | W-main-print-banner/-stderr DIE |
| I7 | both currency paths share ONE composition / ONE minter (DRY #1) | **∀** (mutation, both paths) | reference green (P3/P-share) |
| I8 | verdict/leg-verdict/render-branch reach is a checked variable | **∀** over enum/VERDICT_* + branch cov | new-verdict/new-render-branch DIE |
| **I-served-main** | **`main` served bytes anchored over main's INPUT space** | **GUARDED — MP-B FIXES the selector axis; leg-2 excludes main** | **W-main-empty-selector SURVIVES 187/0** (Gap 1) |
| **I-multigate** | **multi-gate combination receipt shapes byte-anchored** | **GUARDED — MP-A/MP-B/leg-2 are single-gate-non-green** | **W-compose-multiowned SURVIVES 187/0** (Gap 2) |

I1–I8 are ∀ over a typed/byte/coverage domain and hold. **I-served-main and I-multigate are the guarded rows,
each with a surviving exit-0 wrong build.**

## 7. P1c — REACH ATTACK TABLE (per instrument). Legs: **E = empirical (wrong build in scratch)**, **C = construction-inspection.**
| instrument | site-set (reach) | DERIVED vs hidden-constant | coverage a checked variable? | effect vs proxy | verdict |
|---|---|---|---|---|---|
| MP-A byte-oracle (complete VERDICT_* domain) | mode × `GATE_OUTCOME_VERDICTS`, **single-gate** | domain DERIVED from `GATE_OUTCOME_VERDICTS` (leg-1); **gate-cardinality FIXED at 1** | YES for per-gate verdict; **NO for cardinality ≥2** | effect (bytes) | **PARTIAL — multi-gate shapes escape (E: W-compose-multiowned)** |
| MP-B served-bytes (`main` stdout+stderr) | main over mode × VERDICT_*, **selector FIXED non-empty in wave** | reach = a HIDDEN CONSTANT (one selector, one manifest, single-gate) | checks (mode × VERDICT_*); **selector/manifest/cardinality axes NOT checked** | effect (both streams) | **PARTIAL — empty-selector wave unanchored (E: W-main-empty-selector)** |
| leg-2 branch-coverage (`_render_method_spans`) | `GateCurrency.render` + `WaveReceipt.render` + component renders, DERIVED from a receipt | DERIVED (receipt structure) | YES for render methods | effect (arcs) | ✅ for render methods (E: new-render-branch DIES); **`main` + `compose` EXCLUDED by construction** |
| leg-1 domain source (`GATE_OUTCOME_VERDICTS`) | the closed VERDICT_* set | DERIVED (both-way diff vs constants) | YES | effect | ✅ (E: new-verdict-domain DIES) |
| main exit-code (MP-1/MP-6) | `main` exit == renderer verdict | DERIVED (`_RED_ENFORCEMENT_CELLS`) | YES | effect (exit) | ✅ (E: W-main-noop DIES, g-5) — but exit ≠ served bytes on the empty-selector path |

**Legs run:** every DIES/SURVIVES verdict is **EMPIRICAL** (`discriminate.py` + `probe_missing_pin.py`, §10),
each paired with the pristine **187/0** positive control. The two survivors are the 7th-defeat class from
CLAUDE.md/INSTRUMENT-0: **a guard certifies only the sites it EXECUTES over, and its reach is a hidden constant
instead of a checked variable** — MP-B's main-input reach is (fixed selector × single manifest × single-gate),
and leg-2 excludes `main` by construction, so main's branch reach is not a checked variable at all.

**The author's own copy (INSTRUMENT 0), applied to MP-B:** *"What is the SET of served-byte cells MP-B anchors
— is it DERIVED from main's INPUT space (mode × VERDICT_* × selector-state × manifest) or a hidden constant
(one selector, one manifest, single-gate) — and does a test go RED when a producible main invocation
(`--wave` with no `-k`) is not among the anchored cells?"* Answer: the cells fix the selector; the coverage is
checked only over (mode × VERDICT_*); an empty-selector wave invocation is silently exempt → W-main-empty-selector.

## 8. MISSING PINS (the test that should exist + the defect it catches)

### MP-C — `test_main_served_output_anchored_on_the_empty_selector_wave_path` (closes Gap 1)
- **Defect caught:** a `main` over-claim on `wave_gate.py --wave` (empty/absent `-k`) — an exit-0 false clear on
  a production-reachable served surface MP-B never drives. Reproduced: W-main-empty-selector survives **187/0** (§3).
- **The pin:** drive `main(["--wave"])` (and `main(["--wave", "-k", "..."])`) with the loader/reader/render-capture
  spies MP-B already uses, and assert `stdout == "\n".join(render) + "\n"`, `stderr == ""`, `(code==0)==ok`.
  **P0 control (proven, §4):** passes the honest reference, fails W-main-empty-selector.
- **Deeper fix (recommended — closes the CLASS, not the instance):** make `main`'s branch reach a **CHECKED
  VARIABLE**. Extend leg-2's branch-coverage backstop to include `main`'s body, driven over
  (mode × VERDICT_* × selector∈{present, absent}), asserting NO un-run branch in `main`. (Must drive BOTH
  selector states or the correct main's `if args.selector else []` branch shows falsely un-run.) A `main`
  branch on ANY unreached input axis then reddens — the point-fix above closes the empty-selector instance;
  this closes the next axis (a selector VALUE, a manifest shape) too. Alternatively, escalate the SPEC SILENCE
  (§3): pin that `--wave` REQUIRES a `-k` selector, making the path unreachable.

### MP-D — `test_multi_gate_receipt_shapes_are_byte_anchored` (closes Gap 2 / the disclosed residual, if the lead rules it in scope)
- **Defect caught:** a `compose` over-claim on a multi-gate exit-0 receipt (2+ owned = PASS). Reproduced:
  W-compose-multiowned survives **187/0** (§3).
- **The pin:** add a multi-gate cell (≥2 gates non-green, incl. a 2+-owned exit-0 cell) to MP-A's byte-oracle
  domain, and make the coverage a checked variable over gate-CARDINALITY, not just per-gate verdict. This is the
  reviser's own disclosed re-open trigger fired ("a composer conditional on a new axis → add that axis to the
  domain"). LOWER priority than MP-C: the surviving form is adversarial (honest `if owned:` dies at the single-gate
  MP-A cell), but the disclosure did not note the residual admits an EXIT-0 clear.

## 9. Residuals (individual verdicts — no "the rest look fine")
- **R1 (Gap 1) — real, undisclosed, PRIMARY.** MP-B's served-bytes reach fixes the selector axis; the
  empty-selector wave path is an exit-0 false-clear surface anchored by nothing. Reviser D2's "main rides MP-B"
  is measurably false. **Verdict: real; the blocker; fix = MP-C.**
- **R2 (Gap 2) — real, within the reviser's disclosed composer bound, adversarial.** Single-gate domain admits
  a 2+-owned exit-0 over-claim. **Verdict: real; residual; surface for lead ruling; fix = MP-D.**
- **R3 — capfd coverage of the served surface is CORRECT.** I probed for an over-claim on a surface capfd misses
  (fd 3+, `/dev/tty`, logging-to-file); none is a plausible CLI served surface. capfd (fd 1 + fd 2) is the right
  instrument; MP-B's stderr leg closes the round-8 stderr door (W-main-print-stderr DIES). **Verdict: no gap here.**
- **R4 — leg-2's render-method coverage is COMPLETE over the render methods.** GateCurrency.render's 4 verdict
  branches, GateLeg's scoped/orphan branches, WaveReceipt.render's loops are all exercised by the single-gate
  domain; a new render-method branch reddens (new-render-branch DIES). The gap is that `main`/`compose` are NOT
  render methods, so they are outside leg-2 entirely (R1/R2). **Verdict: sound within its stated scope.**
- **R5 — `_render_method_spans` derives its method set from ONE reference receipt** (RED_ADJUDICATED wave). A
  component appearing ONLY in some receipts (e.g. a checkpoint-only footer) would be absent from the span set →
  its branches unmeasured. Not exploited (the composition pin `_reconstruct_receipt` catches a 7th component in
  `WaveReceipt.render`, and MP-A byte-anchors component prose over the domain). **Verdict: latent, not currently
  reachable; noted for the record.**
- **R6 (inherited) — `test_no_hardcoded_gate_id_collection`'s `canonical` is a hand-list of renamed-evadable
  ids;** the behavioural `…enumerates_exactly_the_manifest_gates` + `…identified_by_reader_not_literal_id` are the
  coverage-checked instruments. Unchanged from prior rounds, met deliberately. **Verdict: acceptable belt/braces.**
- **My reference is faithful but independent** — 187/0 + 41/0 confirm it is a valid correct build; the two
  survivors are one-line patches of it. **Verdict: my instrument, P0-controlled (pristine=187/0 asserted).**

## 10. Full probe record (commands + real output) + instruments (brief-base §1 — scratch is disposable)
**Scratch (provenance-asserted, #140):** `scratch_copy.sh /home/ejprice/scratch-delta-g-6` → wave_gate/pcg/
loremaster `__file__` all inside scratch (§1).

**`discriminate.py` — pristine control 187/0, then each build:**
```
POSITIVE CONTROL (pristine): 187 passed / 0 failed
R7a-notrun-body           185 passed /   2 failed  -> DIES(right reason)
R7b-unrun-detail          186 passed /   1 failed  -> DIES(right reason)
R7c-notrun-orphan         186 passed /   1 failed  -> DIES(right reason)
W-main-print-banner       186 passed /   1 failed  -> DIES(right reason)
W-main-print-stderr       186 passed /   1 failed  -> DIES(right reason)
new-verdict-domain        180 passed /   7 failed  -> DIES(right reason)
new-render-branch         186 passed /   1 failed  -> DIES(right reason)
R-adjudicated-body        185 passed /   2 failed  -> DIES(right reason)
W-main-empty-selector     187 passed /   0 failed  -> SURVIVES   (Gap 1 — exit-0, empty-selector wave)
W-main-checkpoint-footer  186 passed /   1 failed  -> DIES        (control: MP-B reaches checkpoint exit-0)
W-compose-multiowned      187 passed /   0 failed  -> SURVIVES   (Gap 2 — exit-0, 2+ owned)
```
`W-main-checkpoint-footer` is the positive control that MP-B genuinely reaches the checkpoint exit-0 (PASS_FULL)
surface — an over-claim there DIES; it is only the empty-selector WAVE cell that escapes.

**`probe_missing_pin.py` — P0-controlled Gap-1 pin** (pristine → PASSES; W-main-empty-selector → FAILS): §4.

**Instruments (deliverables, brief-base §1 — pasted so they survive scratch disposal):**
- `build_reference.py` — independent CORRECT reference; appends the §11 seam + §11.8 typed `WaveReceipt` +
  §11.10 `GATE_OUTCOME_VERDICTS` to `pending_contract_gate.py`, excises/replaces `_render_currency` (re.subn,
  matched exactly once), writes `wave_gate.py`. Seam shape: `LegQualification{CLEAN,OWNED,SCOPED,FAILING}` ·
  `SummaryVerdict{PASS_FULL,PASS_SCOPED,FAIL}` · `SummaryLine(str)` · `render_summary` (SOLE minter) ·
  `summary_verdict(qs)=FAIL if any FAILING else PASS_SCOPED if any SCOPED else PASS_FULL` ·
  `_SCOPED_HONESTY="NOT a currency clear; full run owed"` · `compose_wave_receipt(...)` the ONE composition ·
  `wave_gate.main`: argparse mutually-exclusive `--wave|--checkpoint` (required) + `-k` selector,
  `_run_selected_gates(runner, manifest, list(manifest.ids), pytest_args)`, `print("\n".join(str(l) for l in lines))`,
  `return 0 if ok else 1`. Mutations are `(target, search, replace)` one-line patches that ABORT if `search`
  absent. Round-8 mutations added: `W-main-empty-selector` (banner when `mode==WAVE and not args.selector`),
  `W-main-checkpoint-footer` (control), `W-compose-multiowned` (header append when `len(owned)>=2`).
- `discriminate.py` — restores pristine pcg between mutations; asserts pristine control `(187,0)`; classes a
  collection-errored run BROKEN (never a false SURVIVES); per-mutation expected-killer substring map for the
  right-reason check.
- `probe_missing_pin.py` — the Gap-1 missing pin with P0 controls (drives `main(["--wave"])`, redirect_stdout/
  stderr, asserts stdout==render + stderr=="" + exit agrees).
Scratch (disposable, provenance-asserted): `/home/ejprice/scratch-delta-g-6/scripts/{build_reference,discriminate,probe_missing_pin}.py`
— flag to operator: keep or discard at close-out; the shapes above are self-contained.

---

## VERDICT: **CONTRACT INSUFFICIENT**

§11.10 is strong, real work: it closes F1 (the NOT_RUN receipt shape — R7a/R7b/R7c DIE via MP-A + the
per-verdict leg anchor) and F2 (main's served bytes on the STANDARD surface — W-main-print-banner AND the
round-8 stderr door W-main-print-stderr both DIE via MP-B's both-stream capture), the leg-1 verdict-domain
coverage and leg-2 render-branch coverage are genuine checked variables (new-verdict-domain, new-render-branch
DIE), and `GATE_OUTCOME_VERDICTS` is the closed derived set. Satisfiability (187/0) and extraction
non-regression (41/0) hold.

**But the round-8 hunt found the served surface is NOT terminal — two wrong builds survive 187/0, both exit-0
false clears, both the same F1/F2 class one axis over:**
1. **W-main-empty-selector (PRIMARY, undisclosed):** MP-B anchors main's served bytes over (mode × VERDICT_*)
   with a FIXED non-empty selector; no test drives `main(["--wave"])`, and leg-2 EXCLUDES `main` by
   construction. `wave_gate.py --wave` (no `-k`) is a production-reachable exit-0 PASS_SCOPED path, and a
   `main` over-claim there survives untouched — falsifying the reviser's D2 claim that "main's own branches
   ride MP-1/MP-6/MP-B." Main's branch reach is a HIDDEN CONSTANT, not a checked variable — the 7th-defeat class
   at the very served surface #344 exists to protect.
2. **W-compose-multiowned (secondary, within the reviser's disclosed composer bound):** MP-A/MP-B/leg-2 are all
   single-gate-non-green; a 2+-owned (exit-0 PASS) receipt with an injected over-claim survives. Adversarial,
   but demonstrates the single-gate domain admits an exit-0 clear the disclosure treated as FAIL-only.

**Missing pin (closes Gap 1, P0-proven discriminating):** MP-C — anchor main's served bytes on the
empty-selector wave path; deeper fix — make main's branch reach a CHECKED VARIABLE (extend leg-2 to `main` over
mode × VERDICT_* × selector-state), or escalate the spec silence and require `-k` in wave mode. MP-D (optional,
lead ruling) — add a multi-gate cell to MP-A's byte-oracle domain. Routing per standing order:
contract → adversary → build → cold audit.
