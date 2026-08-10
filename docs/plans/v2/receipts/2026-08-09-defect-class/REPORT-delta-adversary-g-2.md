brief-base v10 read
brief project v7 read

# REPORT-delta-adversary-g-2 — 3rd adversary pass on INSTRUMENT G (`scripts/test_wave_gate.py`, #344)

## Capability check (tool honesty — brief-base §4, first)
Everything the brief demanded was satisfiable. `scratch_copy.sh` built a provenance-asserted
copy; I authored an INDEPENDENT reference `wave_gate.py` there (not the reviser's, which lived
at `/tmp` and is gone) and ran the real 53-pin contract against it, against 8 named wrong builds,
and against 2 NEW r5 probes; `lore_comms` reachable (drained: no unread). No impossibilities.

---

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT.** The re-revision genuinely closed all 3 delta survivors
  (MP-6/7/8) and did not regress the 5 originals — but the MP-7 *replacement* opened a **4th
  survivor (r5)** in the same "wave-mode summary over-claims" class it was built to close.
- **P1 (headline): `W-summary-double` passes 53/53.** A wave receipt that emits the machinery's
  unqualified `CURRENCY : PASS — every claimed gate is GREEN or OWNED` as a NON-last verdict line
  (honest wave banner still last) is a FALSE CLEAR in wave mode — pytest ran SCOPED, not to a
  currency clear — and the new MP-7 pin is blind to it because its reach is `_summary_line` (the
  LAST PASS/FAIL line only). A hidden-constant reach: the 7th-defeat shape, in the fix for #344.
- **Were the 3 delta survivors + 5 originals TRULY closed? YES — independently rebuilt & confirmed
  caught** (my rebuild, not the reviser's claim): W-main-noop 17f · W-DRY-reparse 1f(AST belt) ·
  W-B 1f(MP-7) · W-ruff 2f · W-echo 2f · **W-main-wave-core 5f(main-exit ∀)** · **W-summary-alt
  1f(MP-7)** · **W-wave-notrun 6f(renderer+main omitted-cells)**. Every one caught by its designated
  pin, none vacuous.
- **META-RECURSION at BOTH matrices — independently CONFIRMED (not relayed):** add a 4th gate to
  the canned manifest → renderer matrix AND main-exit matrix BOTH grow 12→16, coverage pins green;
  hardcode `_FAIL_MATRIX_GATES` stale → BOTH coverage pins redden (`['pytest']` never driven).
  Main-exit's ∀ is a genuinely checked variable == the renderer's == the live surface. MP-6 closed.
- **MISSING PIN (r5): `test_wave_scoped_summary_carries_the_bound_on_EVERY_verdict_line`** — assert
  every PASS/FAIL verdict line in a scoped wave receipt carries the marker (∀ over the receipt's
  verdict lines — allowlist-the-safe applied to the WHOLE receipt, which is what design §9.3 says:
  *"Pin the WHOLE receipt, not the line"*). Catches W-summary-double AND keeps W-summary-alt caught.
- **Packages considered:** none new — G composes in-repo `pending_contract_gate` machinery
  (`_run_selected_gates`, `_residuals_for`, `gate_currency`, `READERS`, `GateManifest`). Reuse
  verdict = **keep/reuse** (the contract enforces it: MP-2 spy + AST reparse belt, both confirmed).
- **Satisfiability (C-DEF):** my independent reference → **53 passed, 0 failed** in scratch;
  `--collect-only` → 53 collected. RED honesty: no `wave_gate.py` → `ModuleNotFoundError` at
  `test_wave_gate.py:143` (importlib line), 1 error — contract-first RED, right reason.
- **Provenance (#140):** `loremaster.__file__`, `pending_contract_gate.__file__`, `wave_gate.__file__`
  all INSIDE `/home/ejprice/scratch-delta-adversary-g-2/` (asserted; receipt in Probe record).
- **Graded:** `14b62f2f9bd0d211603895b25e5060ee88bf4716` · HEAD-at-report: `14b62f2` · SAME
  (graded file = working-tree `scripts/test_wave_gate.py`, still `M`/uncommitted, byte-identical
  to scratch — `diff -q` empty).
- **P0 controls:** the harness demonstrably sees breakage (8 wrong builds redden their targeted
  pins; the stale-reach control reddens both coverage pins); the r5 survival is paired with a
  reference control (passes 53/53) AND a discriminating stronger instrument (§9.3 whole-receipt
  scan reddens on double, passes on reference). Not a blind probe.

---

## Did the re-revision TRULY close the 3 delta survivors + 5 originals? (independent rebuild)

Every build below was re-authored as a targeted patch of MY independent reference and run against
the full 53-pin contract in provenance-asserted scratch. Verified, not relayed.

| wrong build | my rebuild | targeted pin that fired | closed? |
|---|---|---|---|
| **W-main-wave-core** (main core-advisory in wave → exit 0) | 5 failed | `test_main_exit_equals_the_renderer_verdict_over_every_cell` (leg-2 divergence, wave cells) — ONLY the entrypoint pin, renderer honest | ✅ (MP-6) |
| **W-summary-alt** ("all gates are clean, tree is green") | 1 failed | `test_wave_scoped_summary_positively_carries_the_scoped_bound` (marker absent) | ✅ (MP-7) |
| **W-wave-notrun** (omitted gate tolerated in wave) | 6 failed | `test_every_mode_gate_cell_fails_on_a_red[wave-*-omitted]` (renderer) + `…over_every_cell[wave-*-omitted]` (entrypoint) | ✅ (MP-8) |
| W-main-noop | 17 failed | routing spy + both matrices + smoke | ✅ |
| W-DRY-reparse | 1 failed | `test_wave_gate_does_not_reparse_the_manifest_itself` (AST belt) | ✅ |
| W-B (over-claim as FINAL line) | 1 failed | MP-7 positive marker (last line lacks SCOPED/OWED — "OWNED" ≠ "OWED") | ✅ |
| W-ruff advisory (renderer) | 2 failed | renderer + main matrix `[wave-ruff-dirty]` | ✅ |
| W-echo hardcode | 2 failed | `test_wave_scoped_selector_echo_equals_the_source` (2 of 3 values) | ✅ |

All 8 genuinely caught. W-main-wave-core caught **only** by the entrypoint divergence pin (its
renderer/summary are honest) — proof the main-exit ∀ is the sole discriminator for that hole, not
vacuous. (My W-DRY reproduction routes its private reparse through `_run_selected_gates`, so it is
caught by the AST belt rather than the spy-count; the belt is the load-bearing catch for the
re-parse door either way. My W-main-wave-core is 5f vs the reviser's 4f because my wave×*×omitted
cells also diverge — a stronger catch, same pin.)

---

## Did it OPEN a NEW wrong build? YES — r5, ONE survivor (same class MP-7 exists to close)

**Root cause: the MP-7 replacement pins the LINE, not the RECEIPT — the opposite of design §9.3.**
The delta re-grade's MP-7 said "assert the SUMMARY line POSITIVELY carries the scoped bound," and
the reviser implemented `_summary_line` = the LAST PASS/FAIL line. But design §9.3 IDIOM 3 says
literally: *"Pin the WHOLE receipt, not the line: on a receipt with a scoped leg, assert the joined
output contains NO unqualified-pass token."* The reviser dropped the whole-receipt scan (correctly
judging the token-deny-list defeatable by alternate wording — W-summary-alt) but replaced it with a
positive check whose **reach is a single line**. A verdict line that is NOT the last PASS/FAIL line
is silently exempt.

| new wrong build | survives? | reference control | the hole |
|---|---|---|---|
| **W-summary-double** — unqualified `CURRENCY : PASS — every claimed gate is GREEN or OWNED` emitted as a NON-last verdict line; honest wave banner still last | **53/53** | ref does not emit it | **r5** — MP-7's reach = `_summary_line` (last PASS/FAIL line); earlier over-claim lines exempt |
| W-summary-inline — marker + over-claim in ONE line ("WAVE : PASS — every claimed gate is GREEN or OWNED (pytest SCOPED)") | **53/53** | ref carries only the honest bound | same class — marker PRESENCE ≠ honesty; needs the §9.3 structural form |

Both prove the same thing: **MP-7 checks marker PRESENCE on one line, which is necessary but not
sufficient for summary honesty.** W-summary-double is the plausible, DRY-faithful build — a builder
who composes `pending_contract_gate` machinery (which the contract MANDATES) inherits its
`CURRENCY : PASS — every claimed gate is GREEN or OWNED` summary; overriding the pytest line to
SCOPED (to pass W3) and appending a wave banner leaves that unqualified line in place. My reference
had to make a DELIBERATE choice to SUPPRESS the machinery summary in wave mode — a choice the
contract does not force.

---

## P1b — QUANTIFIER TABLE (re-graded for the re-revision; every guarded row carries a receipt)

| # | invariant the contract intends | classification | receipt |
|---|---|---|---|
| I1 | mode REQUIRED & recorded | **∀** (render TypeError + cli SystemExit + header) | reference green |
| I2 | reported gate-set == manifest gate-set | **∀** over manifests (3 / +extra / −ruff) | reference green |
| I3 | a claimed-but-omitted gate → NOT_RUN → fail | **∀ over (mode × gate)** — NOW both modes | W-wave-notrun CAUGHT (6f); omitted cells in wave+checkpoint (MP-8 closed) |
| I4 | a RED gate fails the bundle (renderer) | **∀ over (mode × gate × {dirty,omitted})**, DERIVED + coverage-checked | reference green; W-ruff CAUGHT; meta-recursion proven |
| I5 | a wave receipt never reads as an unqualified pass (SUMMARY) | **GUARDED — marker-presence on the LAST PASS/FAIL line only** | **W-summary-double survives (r5)** — over-claim on a non-last verdict line |
| I6 | non-omittable core runs full in wave (never scoped) | **∀ over core gates** | reference green; W-ruff CAUGHT |
| I7 | the ENTRYPOINT `main` enforces the verdict | **∀ over (mode × gate × failure-mode)**, DERIVED + coverage-checked (main == renderer) | W-main-wave-core CAUGHT (5f); meta-recursion at main proven (MP-6 closed) |
| I8 | `pytest_args_for` scopes only in wave | **∀** over mode (unit) | reference green |
| I9 | bundle routes through the ONE manifest reader | **∀** (spy both namespaces + AST belt) | W-main-noop/W-DRY CAUGHT |

**I3 and I7 — the two guarded rows the last pass flagged (MP-8, MP-6) — are now ∀ and genuinely
closed** (independently re-verified). **I5 is the ONLY remaining guarded row**, and it carries a
surviving wrong build (W-summary-double, r5) as its receipt. All other rows are ∀-over-inputs with
a reference-green + wrong-build-control receipt.

---

## P1c — REACH ATTACK TABLE (per instrument). Legs: **E = empirical wrong build/perturbation in scratch**, **C = construction-inspection.**

| instrument | site-set | DERIVED vs hand-list | coverage a checked variable? | effect vs proxy | verdict |
|---|---|---|---|---|---|
| renderer fail-matrix | (mode × gate × failure-mode) cells | **DERIVED** `_canonical_manifest_ids()` | **YES** — meta-recursion both dirs (E) | effect ✓ | ✅ |
| **entrypoint enforcement (main-exit)** | main exit over (mode × gate × failure-mode) | **DERIVED — same `_ENFORCEMENT_PARAMS`** as renderer | **YES** — grows 12→16 with manifest (E); stale reach reddens (E) | effect (exit code) ✓ | ✅ **CLOSED (was MP-6)** |
| omitted-gate → fail | (mode × gate) omitted cells, both modes | DERIVED (failure-mode axis `{dirty,omitted}`) | YES | effect ✓ | ✅ **CLOSED (was MP-8)** |
| **wave summary honesty (MP-7)** | **the verdict-summary lines of a scoped wave receipt** | marker set = 2-token allowlist (fine) | **NO — reach is `_summary_line` = the LAST PASS/FAIL line, a HIDDEN CONSTANT; other verdict lines silently exempt** | effect ✓ | **MISSING (r5)** — hidden-constant reach; the 7th-defeat shape at the summary |
| scopable-gate identification | which gate is scopable | DERIVED by junit-reader identity | YES — `suite` rename reddens (E) | verdict ✓ | ✅ |
| routes-one-reader | main's manifest reader | DERIVED (spy both namespaces) | YES — 0-calls reddens | effect ✓ | ✅ |
| AST reparse belt | `wave_gate.__file__` | DERIVED from module | catches `yaml.load*` door (E) | source ✓ | ✅ |
| `test_no_hardcoded_gate_id_collection` (AST) | `wave_gate.__file__` | reach DERIVED; `canonical` is a hand-list | catches literal-collection door | source ✓ | acceptable-with-note (R2, inherited) |

**Legs run:** the r5 row is **EMPIRICAL** (W-summary-double + W-summary-inline survive 53/53 +
reference control + §9.3 whole-receipt scan discriminates). The main-exit and omitted-gate rows are
**EMPIRICAL** (meta-recursion perturbation grew both matrices 12→16; the stale-reach control
reddened both coverage pins; W-main-wave-core / W-wave-notrun survive nothing). "scopable-by-reader"
and "routes-one-reader" corroborated by the W5/MP-2 empirical results + construction-inspection.

The author's own copy, applied to MP-7: *"What is the SET of receipt lines this summary-honesty
guard inspects, is it DERIVED from the receipt's verdict lines or a hidden constant (`the last
one`), and does a test go RED when an over-claim appears on a verdict line the guard does not
inspect?"* — the fail-matrix and main-exit answer yes; **MP-7 answers no** (reach = one line).

---

## MISSING PIN — the test that should exist + the defect it catches + the reproduction

### MP-9 (r5) — `test_wave_scoped_summary_carries_the_bound_on_EVERY_verdict_line`
- **Defect caught:** a wave receipt with a scoped leg that ALSO carries an unqualified currency
  clear (`every claimed gate is GREEN or OWNED` / `CURRENCY : PASS`) on a verdict line OTHER than
  the last — a false clear at the summary, the #306/#312/#344 disease reproduced because MP-7's
  reach is `_summary_line` (the last PASS/FAIL line only). In wave mode pytest ran a `-k` SUBSET,
  so any "every gate GREEN" line is literally false, and it is exactly the machinery token an
  agent-consumer is trained to read.
- **Reproduction (E):** `W-summary-double` — reference + `lines.append("CURRENCY : PASS — every
  claimed gate is GREEN or OWNED")` before the honest wave banner. Survives **53 passed, 0 failed**.
  Demonstrated directly: the wave receipt CONTAINS the over-claim line; `_summary_line()` returns
  the honest last line (`WAVE : PASS — … SCOPED …`), so the marker check passes; the design §9.3
  whole-receipt scan (`joined contains no unqualified-pass token`) reddens on double and passes on
  the reference. (Full receipts in the Probe record.)
- **The pin (allowlist-the-safe, whole-receipt — what §9.3 specifies):** on a wave receipt with a
  scoped leg, assert **EVERY** PASS/FAIL verdict line carries a scoped marker (`SCOPED`/`OWED`), not
  only `_summary_line`. This catches W-summary-double (the `CURRENCY : PASS — every gate GREEN` line
  lacks the marker → RED) AND keeps W-summary-alt caught (its single line lacks the marker), WITHOUT
  a forbidden-token enumeration. Control: a clean FULL checkpoint (no scoped leg) is exempt (the
  existing MP-7 control leg carries over).
- **Residual the ∀-over-lines pin does NOT close (W-summary-inline):** a single line carrying BOTH
  the marker AND the over-claim survives even that pin. The complete, §9.3-faithful close is
  STRUCTURAL: **derive the summary from a typed per-leg flag** (`scoped: bool` / `qualified`), render
  the summary FROM it (never free-text prose beside it), and pin the derivation by mutation (flip the
  flag → the marker follows; an unqualified currency-clear token is unrepresentable when any leg is
  scoped). This is CLAUDE.md's "prose DERIVED from behaviour, not restated beside it" and requires a
  small surface change (a typed qualification alongside `ok` in `render_wave_receipt`'s return).
  Flagging the fork for the author/lead: **minimal in-surface pin (∀-over-verdict-lines, closes
  double+alt) vs. structural derive-from-typed-flag (closes double+alt+inline, changes the return
  surface).** I recommend the ∀-over-verdict-lines pin now (it closes the plausible headline build
  and is a ~5-line edit to the existing MP-7 test) and the structural form as the durable §9.3 close.

---

## Fixture-discrimination verdicts (every wrong build an individual verdict)

| wrong build | intended pin | verdict |
|---|---|---|
| W-main-noop | MP-1/MP-2 + matrices | **CAUGHT** (E: 17f) |
| W-DRY-reparse | AST reparse belt | **CAUGHT** (E: 1f) |
| W-B (over-claim FINAL line) | MP-7 marker | **CAUGHT** (E: 1f) |
| W-ruff advisory | matrix `[wave-ruff-dirty]` | **CAUGHT** (E: 2f) |
| W-echo hardcode | MP-5 monoculture | **CAUGHT** (E: 2f) |
| W-main-wave-core | main-exit ∀ divergence | **CAUGHT** (E: 5f) — MP-6 closed |
| W-summary-alt | MP-7 marker | **CAUGHT** (E: 1f) — MP-8/MP-7 fix good |
| W-wave-notrun | omitted-cell ∀ (renderer+main) | **CAUGHT** (E: 6f) — MP-8 closed |
| **W-summary-double** | — none (MP-7 reach = last line) — | **SLIPS → MP-9 (r5)** (E: 53/53) |
| **W-summary-inline** | — none — | **SLIPS → MP-9 residual** (E: 53/53) |

Both-legs proof: each SLIP survives 53/53 AND the reference passes 53/53 with the honest behaviour
AND a stronger instrument (§9.3 whole-receipt scan) discriminates — genuine non-discrimination, not
a botched fixture.

---

## Residuals (individual verdicts — no "the rest look fine")

- **R2 (inherited) — `test_no_hardcoded_gate_id_collection`'s `canonical` is a hand-list.** A
  hardcoded tuple of RENAMED ids evades the AST source scan; the behavioural
  `test_render_enumerates_exactly_the_manifest_gates` is the real coverage-checked instrument
  (docstring says so). Unchanged by this re-revision — met deliberately, not a new finding.
- **R3 (inherited) — "wave scopes pytest" expressed twice** (`pytest_args_for` run-side + the
  render's scopable branch). Minor. Note: the main-level `pytest_args` forwarding is NOT asserted at
  the effect level (the MP-2 spy records `pytest_args` but no test checks `main --wave` forwards the
  selector and `main --checkpoint` forwards `()`). Not exploitable as an over-claim (wave always
  scopes pytest; a main that ran pytest FULL in wave would over-WORK, not over-CLAIM), so I record it
  as a residual, not a missing pin — but the lead may want the effect-level assertion for R3 closure.
- **MP-1 kept as smoke — correct.** `test_main_exit_code_reflects_the_bundle_verdict` (4 cells) is a
  positive-control smoke; the `…over_every_cell` matrix supplies the ∀ reach. Extra green coverage,
  no DRY violation (reuses `_patch_loaders`/`_install_reader_spy`). Confirmed it passes W-main-wave-core
  (its 4 cells happen to agree) — consistent with the delta finding.

---

## Full probe record (commands + real output tails)

**Scratch (provenance-asserted, #140):** `./scripts/scratch_copy.sh /home/ejprice/scratch-delta-adversary-g-2`
→ `loremaster -> /home/ejprice/scratch-delta-adversary-g-2/loremaster/loremaster/__init__.py`
(+3 siblings). Receipt: `loremaster.__file__`, `pending_contract_gate.__file__`, `wave_gate.__file__`
all resolve INSIDE `/home/ejprice/scratch-delta-adversary-g-2/`.

**RED honesty (real repo, no `wave_gate.py`):** `uv run pytest scripts/test_wave_gate.py --collect-only -q`
→ `ModuleNotFoundError: No module named 'wave_gate'`, `no tests collected, 1 error in 0.20s`. Right reason.

**C-DEF satisfiability (scratch, my independent reference as `wave_gate.py`):**
`uv run pytest scripts/test_wave_gate.py -q` → `53 passed in 0.19s`; `--collect-only` → 53 collected.

**8 named wrong builds + 2 r5 probes (each = full 53-pin contract, scratch):**
```
REFERENCE          53 passed
main_noop          17 failed, 36 passed   FAIL: main_exit_code_reflects · exit_over_every_cell · exit_on_a_clean_run · routes_through_the_one_manifest_reader
dry_reparse         1 failed, 52 passed   FAIL: wave_gate_does_not_reparse_the_manifest_itself (AST belt)
overclaim_B         1 failed, 52 passed   FAIL: wave_scoped_summary_positively_carries_the_scoped_bound
ruff_advisory       2 failed, 51 passed   FAIL: every_mode_gate_cell_fails_on_a_red · exit_over_every_cell
echo_hardcode       2 failed, 51 passed   FAIL: wave_scoped_selector_echo_equals_the_source
main_wave_core      5 failed, 48 passed   FAIL: exit_over_every_cell   (ONLY the entrypoint ∀ — renderer honest)
summary_alt         1 failed, 52 passed   FAIL: wave_scoped_summary_positively_carries_the_scoped_bound
wave_notrun         6 failed, 47 passed   FAIL: every_mode_gate_cell_fails_on_a_red · exit_over_every_cell
summary_double     53 passed              -> r5 (SURVIVES)
summary_inline     53 passed              -> r5 class residual (SURVIVES)
```

**r5 positive control (direct demonstration — reference vs W-summary-double, clean WAVE receipt):**
```
REFERENCE   wave receipt last lines:
   pytest       SCOPED(-k test_changed_area) — NOT a currency clear; full run owed at the checkpoint
   WAVE       : PASS — core GREEN-or-owned; pytest SCOPED, full run still owed
   _summary_line() -> 'WAVE ... SCOPED, full run still owed'
   MP-7 marker present? True   |  §9.3 WHOLE-RECEIPT over-claims? False

summary_double wave receipt last lines:
   pytest       SCOPED(-k test_changed_area) — NOT a currency clear; full run owed at the checkpoint
   CURRENCY   : PASS — every claimed gate is GREEN or OWNED      <-- FALSE CLEAR (pytest was SCOPED)
   WAVE       : PASS — core GREEN-or-owned; pytest SCOPED, full run still owed
   _summary_line() -> 'WAVE ... SCOPED, full run still owed'     <-- reads the HONEST last line
   MP-7 marker present? True   |  §9.3 WHOLE-RECEIPT over-claims? True   <-- a stronger pin catches it
```

**META-RECURSION at BOTH matrices (perturbed contract copies in scratch):**
```
BASELINE (3 gates): renderer matrix = 12 cells · main-exit matrix = 12 cells
ADD "docs" gate to _manifest default:
  renderer matrix = 16 · main-exit matrix = 16 · coverage pins (both) -> 2 passed   (both grew)
STALE control (hardcode _FAIL_MATRIX_GATES = ("typecheck","ruff")):
  test_enforcement_matrix_covers_… -> FAILED  ("manifest gates the fail-matrix never drives: ['pytest']")
  test_fail_matrix_gate_set_equals_the_live_manifest -> FAILED
```
Main-exit's exit-code reach is a genuinely CHECKED VARIABLE == the renderer's == the live surface.
MP-6 (main-exit was a 4-cell hand-list) is genuinely closed, not a hand-list of 6.

**P0 controls (harness sees breakage, so the r5 survival is real):** all 8 named wrong builds redden
their targeted pins; the stale-reach control reddens both coverage pins; the reference passes 53/53;
W-summary-double / W-summary-inline are each paired with a reference control (passes) AND the §9.3
whole-receipt scan discriminates (reddens on the survivor, passes on the reference). The probe
harness is not blind.

**Instruments (deliverables, not scratch):** the reference build, all 10 wrong builds, the r5
demonstration, and the meta-recursion patcher are pasted-by-generation in
`/home/ejprice/scratch-delta-adversary-g-2/probe_builds/` (disposable). The load-bearing ones are
reproduced above: the reference is a ~150-line composition of `pending_contract_gate`; W-summary-double
is `REFERENCE + one over-claim line before the wave banner`; the §9.3 discriminator is
`any(t in "\n".join(lines) for t in ("every claimed gate is GREEN", "CURRENCY   : PASS"))`.

---

## VERDICT: **CONTRACT INSUFFICIENT**

The re-revision did its named job: MP-6 (main-exit ∀ was a 4-cell hand-list) and MP-8 (NOT_RUN
pinned checkpoint-only) are genuinely closed — independently re-verified, meta-recursion confirmed
at BOTH matrices, main-exit's reach a checked variable. The 5 originals do not regress. But the MP-7
*replacement* opened **r5**: it pins the summary honesty at `_summary_line` (the last PASS/FAIL
line), a HIDDEN-CONSTANT reach — the exact "reach is not a checked variable" class INSTRUMENT G is
part of the packet built to prevent — so a wave receipt that over-claims on any NON-last verdict line
(`W-summary-double`) passes the full 53. Design §9.3 already specified the fix the re-revision
dropped: *"Pin the WHOLE receipt, not the line."*

**One missing pin closes the headline:** `test_wave_scoped_summary_carries_the_bound_on_EVERY_verdict_line`
— ∀ over the receipt's verdict lines carry the scoped marker (allowlist-the-safe, whole-receipt). It
catches W-summary-double and keeps W-summary-alt caught. The residual (W-summary-inline: marker +
over-claim in one line) needs the structural §9.3 form (summary derived from a typed per-leg flag) —
a fork I flag for the author/lead rather than resolve unilaterally.
