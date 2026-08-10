brief-base v10 read
brief project v7 read

# REPORT-delta-adversary-g-4 — 5th adversary pass on INSTRUMENT G (`scripts/test_wave_gate.py`, #344/#345), the §11.8 full typed WaveReceipt

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT** — by a hair, on the honesty-bearing line §11.8 left unpinned.
  The typed `WaveReceipt` genuinely does its named job: **all seven §11.8.7 attacks die** and the
  meta-recursion append-path reddens on sight. But one wrong build over-claims **on a PASSING receipt**.
- **P1 (headline): a wrong build DID survive — `W-SCOPED-OVERCLAIM` (D2c), 170/170.** In `--wave`, the
  scoped pytest leg line — the line whose ENTIRE job is "don't trust this scoped run as a full clear" —
  reads `SCOPED(-k …) — tree is current and clean; nothing owed` on a `PASS_SCOPED` receipt (ok=True,
  exit 0). Every pin is blind: the scoped pin enforces only {SCOPED present · not-literally-"GREEN" ·
  selector echoed}; P4 sees no marker; the composition pin is in-component. Its honest CONTENT is unpinned.
- **The 2 DEVIATIONS are each individually SAFE, but they CONVERGE on this gap** (details §3):
  (a) no byte-eq wave/checkpoint → checkpoint IS byte-pinned, but the wave `PASS_SCOPED` receipt is the
  ONE pass receipt with no byte/construction anchor; (b) AST scan scoped to `_render_currency`+wave_gate →
  SAFE, because any component SHARED with checkpoint is byte-pinned (D2a/D2d caught), leaving only
  wave-ONLY content — which is exactly where the scoped line lives.
- **MISSING PIN (MP-r6):** `test_wave_scoped_leg_line_is_the_fixed_honest_template` — byte-anchor the
  wave scoped leg line (the instrument the byte-oracle already applies to the checkpoint receipt + summary),
  extended to the ONE pass receipt it skips. Proven discriminating (P0: passes reference, fails D2c).
- **Read-zone under-enumeration (R1):** `REPORT-reviser-g-4.md` §6 says "leaving ONLY a fixed WAVE-header
  constant in the read zone" — MEASURABLY FALSE: the scoped-line template (D2c) and the checkpoint FAIL
  detail (D1a) are two more fixed constants there. A partial enumeration of the cold-audit-read set is the
  packet's own defect class, one level up.
- **Packages considered:** none new — reference reuses in-repo `GateCurrency.render`/`_residuals_for`/
  `gate_currency`/`READERS`/`_run_selected_gates` + the §11 summary seam + the `TestSafeLineRenderedMintPin`
  AST idiom; stdlib `enum`/`dataclasses`/`ast`. Verdict: **reuse/bespoke-minimal** (string→type lift). No
  library supplies a "typed receipt minted only via render()".
- **Satisfiability (C-DEF): 170 passed / 0 failed** against my INDEPENDENT reference; **extraction
  NON-REGRESSIVE — `test_pending_contract_gate.py` 41 passed**. RED honesty: real-repo `--collect-only` →
  `ModuleNotFoundError: No module named 'wave_gate'` at :151, 1 error (right reason).
- **Graded:** `b7bf68c` · HEAD-at-report `b7bf68c` · **SAME** (graded the working-tree `test_wave_gate.py`,
  uncommitted `M`; scratch copy byte-identical, `diff -q` empty).
- **Provenance (#140):** `wave_gate.__file__`, `pending_contract_gate.__file__`, `loremaster.__file__` all
  resolve INSIDE `/home/ejprice/scratch-delta-adversary-g-4/` (asserted; §1).
- **Decisions-needed:** (1) MP-r6 fix form — minimal byte-anchor pin vs sole-minted typed `ScopedLine`
  (I recommend the byte-anchor now; the sole-minter is §11's string→type lift applied to the scoped line).
  (2) If the bound is KEPT as cold-audit-read rather than pinned, the disclosed read zone must enumerate
  ALL THREE fixed slots (wave header · scoped-line template · FAIL detail), not just the header.
- **Receipt pointers:** §1 (satisfiability+non-regression+provenance) · §2 (7 attacks + meta-recursion, measured)
  · §3 (the 2 deviations, probed) · §4 (P1 survivor + P0 control) · §5 (quantifier table) · §6 (reach table)
  · §7 (missing pin) · §8 (residuals) · §9 (full probe record).

---

## 1. Satisfiability + extraction non-regression (provenance-asserted scratch, #140)
`./scripts/scratch_copy.sh /home/ejprice/scratch-delta-adversary-g-4` → all imports INSIDE scratch:
```
wave_gate  -> /home/ejprice/scratch-delta-adversary-g-4/scripts/wave_gate.py
pcg        -> /home/ejprice/scratch-delta-adversary-g-4/scripts/pending_contract_gate.py
loremaster -> /home/ejprice/scratch-delta-adversary-g-4/loremaster/loremaster/__init__.py
```
I authored an **INDEPENDENT reference** (NOT the reviser's) from the ground truth — the §11 seam +
§11.8 typed `WaveReceipt` (`ReceiptHeader`/`RosterLine`/`GateLeg`/`DetailLines`/`WaveReceipt` +
`compose_wave_receipt`) extracted into `pending_contract_gate.py`, `_render_currency` routed through the
shared `compose_wave_receipt`, and a fresh `wave_gate.py`. The scratch `test_wave_gate.py` is byte-identical
to the graded working-tree file (`diff -q` empty). The reference build script (`build_reference.py`) and the
discrimination harness (`discriminate.py`) are reproduced in §9 (scratch is disposable, brief-base §1).
```
C-DEF satisfiability : uv run pytest scripts/test_wave_gate.py -q            -> 170 passed
NON-REGRESSION       : uv run pytest scripts/test_pending_contract_gate.py -q -> 41 passed
RED honesty (real)   : uv run pytest scripts/test_wave_gate.py --collect-only -> ModuleNotFoundError:
                       No module named 'wave_gate' at scripts/test_wave_gate.py:151 — 1 error, right reason
ruff (contract+ref)  : uv run ruff check scripts/test_wave_gate.py scripts/wave_gate.py -> All checks passed!
mypy (contract)      : the CONTRACT file test_wave_gate.py is mypy-clean under MYPYPATH=scripts (no errors
                       on it). [My reference SEAM is untyped for speed — a shortcut in MY probe, not a
                       contract-forced dirtiness; the reviser already showed a TYPED reference is clean.]
```

## 2. The seven §11.8.7 attacks + the round-6 append path — each DIES (measured, discrimination harness)
Every wrong build is a targeted patch of MY reference, run against the full 170-pin contract. `discriminate.py`
output (§9), positive control = reference 170/0 with an honest receipt:

| # | attack | result | designated pin(s) that fired |
|---|---|---|---|
| A1 | **W-EXTRA-LINE (wrapper)** — append after `.render()` in `render_wave_receipt` | 2 failed | `…delegates_to_the_typed_receipt[wave]` + AST `…no_free_receipt_line_composition_outside_render` |
| A2 | **W-EXTRA-LINE (receipt)** — free append inside `WaveReceipt.render()` | 5 failed | `…is_the_fixed_typed_composition_no_free_append` (all 4 cells) + byte-oracle |
| A3 | **orphan-slot over-claim** — extra line in `GateLeg.render()` | 5 failed | `…one_leg_per_gate_orphans_folded` (all 4 cells) + byte-oracle |
| A4 | **roster over-claim** — extra line in `RosterLine.render()` | 1 failed | byte-oracle `…preserves_the_historical_bytes` |
| A5 | **header over-claim (checkpoint)** — extra header line in `_render_currency` | 1 failed | byte-oracle |
| A6 | **NEW free-append path** — `lines.append(...)` in `_render_currency` | 2 failed | AST scan + byte-oracle |
| A7 | **DRY un-share** — `_render_currency` hand-rolls its own composition | 2 failed | `…share_the_one_wave_receipt_composition` (mutation) + AST |
| M1 | **round-6 meta-recursion** — plant a brand-new append in wave_gate.py | 1 failed | AST scan reddens ON SIGHT |

**All seven named attacks + the planted append die at their designated pins.** The typed `WaveReceipt` +
byte-oracle + mint-scan genuinely close the free-APPEND door (per-call over-claim) receipt-wide. This is a
strong contract; §11.8's core claim holds.

## 3. The 2 disclosed DEVIATIONS — each probed empirically (the brief's central asks)

### Deviation (a): no byte-equality pin between `render_wave_receipt(CHECKPOINT)` and `_render_currency`
**Probe D1a** — checkpoint FAIL detail over-claims (`compose_wave_receipt` builds a FAIL detail carrying
`"SUMMARY: all gates are clean, tree is green"`). **SURVIVOR** — but it exits **nonzero** (ok=False), carries
the FIXED `render_summary(FAIL)` verdict, and the authoritative signals stay honest. Lower severity (§8 R2).
**Verdict: deviation (a) is SAFE for the checkpoint PASS path** — the byte-oracle pins the whole clean
checkpoint receipt, and checkpoint can only produce `PASS_FULL` (never scoped) → its one pass receipt is
fully byte-anchored. The mutation proof (`…share_the_one_wave_receipt_composition`) forces both paths through
`WaveReceipt.render`, so a hand-rolled checkpoint composition (A7) reddens. The divergence the mutation
"misses" (different headers) is intentional and harmless — the checkpoint pass receipt is byte-pinned anyway.

### Deviation (b): AST mint-scan scoped to `_render_currency` + all of `wave_gate.py` (NOT whole pcg)
**Enumeration of what the scope EXCLUDES:** every pcg function except `_render_currency` — `compose_wave_receipt`,
`_currencies_for`, `_fail_detail`, any new helper, and every component `.render()` method. **Probed each route:**
- **D2a** — `compose_wave_receipt` builds a non-empty detail on a PASS receipt → **CAUGHT** (`…clean_receipts_have_no_detail_lines` + byte-oracle).
- **D2d** — a NEW unscanned pcg helper `_roster_lines(...)` free-appends an over-claim feeding the roster on a PASS → **CAUGHT** (byte-oracle).
- **The reason:** any component SHARED with the checkpoint path (header/roster/legs/summary/note) is byte-pinned by the checkpoint oracle even though the helper that BUILDS it is unscanned — **the elegant DRY catch: the byte-oracle backstops the shared components' OUTPUT, so an unscanned pcg helper can't over-claim through them.**

**Verdict: deviation (b) is SAFE — the scoped AST scan does not open a new helper door,** because the byte-oracle
covers every shared component. The ONE thing neither the AST scope nor the byte-oracle backstops is **wave-ONLY
content** (the wave header and the scoped leg line), and that is precisely where the surviving over-claim (D2c)
lives — a gap about the scoped line's UNPINNED CONTENT, not about the AST scope per se.

**The two deviations converge:** (a) leaves the wave `PASS_SCOPED` receipt un-byte-anchored; (b)'s scope excludes
its wave-only content. Together, the wave `PASS_SCOPED` receipt's honesty content has no construction anchor.

## 4. P1 — the surviving wrong build: `W-SCOPED-OVERCLAIM` (D2c), 170/170, over-claim on a PASS receipt

**The wrong build:** the scoped pytest leg template (built once in `compose_wave_receipt`, a fixed template)
reads `— tree is current and clean; nothing owed` instead of `— NOT a currency clear; full run owed`.

**Rendered receipt (measured, `ok=True`, exit 0):**
```
GATE BUNDLE [wave] — scope: -k test_changed_area
  manifest   : ('typecheck', 'ruff', 'pytest') (3 gates)
  typecheck    GREEN
  ruff         GREEN
  pytest       SCOPED(-k test_changed_area) — tree is current and clean; nothing owed   <-- OVER-CLAIM
WAVE       : PASS — core is GREEN-or-owned; pytest ran SCOPED, full run still owed
  (this is NOT the deploy receipt: it answers 'is every gate owned', never 'may this ship')
```
**What the pins see (all blind):**
```
scoped pin  : SCOPED present=True · GREEN absent=True · selector echoed=True   -> PASSES
P4          : unqualified marker present=False                                  -> PASSES
composition : the over-claim is IN the GateLeg component (render()==reconstruct) -> PASSES
byte-oracle : checkpoint-only, never touches the wave receipt                    -> N/A
```
**Why this is the dangerous class, not a clever-attacker artefact:** the builder MUST author the scoped line
(it is required), and the contract pins only "SCOPED + not-literally-GREEN + echo" — NOT its cautionary content.
A builder building TO THE CONTRACT (the pins, not the docstring prose) is free to write a reassuring scoped line
that reads as a clear, on a `PASS_SCOPED` (exit 0) receipt. This is the #306/#344 honesty failure — a run reading
clear while pytest ran a `-k` subset — on the one line whose purpose is to prevent it. And §11 spent FOUR rounds
byte-anchoring + sole-minting the SUMMARY line (the receipt's sibling honesty line); the scoped leg line received
none of that. **The design's own standard for honesty-bearing lines (byte-anchor + sole-mint) was not applied to
this one.**

**P0 CONTROL (my probe is not blind):** the proposed pin — the scoped leg line == the fixed honest template with
the selector substituted — **PASSES on the honest reference** (`… NOT a currency clear; full run owed`) and
**FAILS on D2c** (`… tree is current and clean; nothing owed`). Measured, both legs, §9. A differently-broken
build (D2a/D2d over-claims routed through a shared component) is caught by a DIFFERENT pin (byte-oracle), so the
harness demonstrably distinguishes over-claim routes.

## 5. P1b — QUANTIFIER TABLE (every invariant classified; every guarded row carries a receipt)

| # | invariant | classification | receipt |
|---|---|---|---|
| I1 | mode REQUIRED & recorded | **∀** (render TypeError + cli SystemExit + header) | reference green |
| I2 | reported gate-set == manifest gate-set | **∀** over manifests, both-direction | reference green |
| I3 | claimed-but-omitted → NOT_RUN → fail | **∀ over (mode × gate)** | reference green; MP-8 matrix |
| I4 | a RED gate fails the bundle (renderer) | **∀ over (mode × gate × {dirty,omitted})**, coverage-checked | reference green; meta-recursion pinned |
| I5 | the ENTRYPOINT `main` enforces == renderer verdict | **∀ over (mode × gate × failure-mode)**, coverage-checked | reference green (MP-6 divergence pin) |
| I6 | receipt render() = total composition over typed components (no free APPEND) | **∀ over (mode × kind)** (4 cells) | reference green; A1/A2/A3/A6/M1 CAUGHT |
| I7 | one GateLeg per gate; leg renders 1+orphans | **∀ over (mode × kind)** | reference green; A3 CAUGHT |
| I8 | both currency paths share ONE WaveReceipt composition (DRY #1) | **∀** (mutation, both paths) | reference green; A7 CAUGHT |
| I9 | both paths derive summary from the ONE minter (§11 P3) | **∀** (mutation, both namespaces) | reference green |
| I10 | `summary_verdict` biconditional | **∀** over `LegQualification^leg_count`, coverage-checked | reference green |
| I11 | `render_summary` sole minter (marker ⟺ PASS_FULL) | **∀** over closed `SummaryVerdict` | reference green |
| I12 | clean checkpoint receipt byte-identical to historical | **∀** (whole receipt) over the clean cell | reference green; A4/A5 CAUGHT |
| **I13** | **a wave `PASS_SCOPED` receipt never READS as a full clear** | **GUARDED — {SCOPED present · not-"GREEN" · echo}; the scoped line's honest CONTENT is NOT ∀-pinned** | **W-SCOPED-OVERCLAIM survives 170/170 (D2c)** — over-claim on the honesty-bearing leg line, PASS receipt |
| I14 | detail empty on PASS; FAIL reasons preserved as typed detail (fork-1) | **∀** over PASS both modes / FAIL both paths | reference green; D2a CAUGHT |

**I13 is the ONLY guarded row, and it carries a surviving wrong build.** Every other honesty invariant is either
∀-over-a-typed-domain (I6–I12, I14) or byte-anchored (I12). I13 — the scoped leg line's honest content — is the
one honesty assertion left as free text guarded by a weak "not literally GREEN" proxy. This is I5 of round 4
(the summary over-claim) recurring one line over: the summary got the string→type lift; the scoped leg line did
not.

## 6. P1c — REACH ATTACK TABLE (per instrument). Legs: **E = empirical (wrong build in scratch)**, **C = construction-inspection.**

| instrument | site-set | DERIVED vs hand-list | coverage a checked variable? | effect vs proxy | one-source-by-mutation | verdict |
|---|---|---|---|---|---|---|
| composition pin `…no_free_append` | receipt line composition, 4 cells | DERIVED (`_reconstruct_receipt` over named components) | YES — a new un-routed component's line ≠ reconstruction | effect (rendered lines) | — | ✅ (E: A1/A2/A6/M1) |
| leg-count `…orphans_folded` | each GateLeg render | DERIVED (`len==1+orphans`) | YES per leg | effect | — | ✅ (E: A3) |
| AST mint-scan `…outside_render` | ALL of wave_gate.py + `_render_currency` body | reach DERIVED from module/function; forbidden shape = free-`str` `.append` | catches a NEW append path (E: M1/A1/A6) | source | — | ✅ for free-APPEND; **excludes other pcg fns — SAFE because byte-oracle backstops shared components (E: D2a/D2d caught)** |
| byte-oracle `…preserves_the_historical_bytes` | whole CLEAN checkpoint receipt | DERIVED (historical literals + `GateCurrency.render`) | YES (exact) | effect (bytes) | shared components → checkpoint | ✅ (E: A2/A4/A5/D2a/D2d); **covers checkpoint pass ONLY, not the wave PASS_SCOPED receipt** |
| DRY-share mutation `…share_the_one_wave_receipt_composition` | both currency paths | DERIVED (mutate `WaveReceipt.render`) | YES — un-share EITHER reddens | effect | proves both share `.render()` | ✅ (E: A7) |
| §11 P3 mutation (share `render_summary`) | both paths, both namespaces | DERIVED (mutate the minter) | YES | effect | proves shared minter | ✅ |
| scoped pin `…scoped_never_green_and_echoes_selector` | the wave pytest leg line | keyed on {SCOPED · not-"GREEN" · selector} | **NO for the line's honest CONTENT** — "not the word GREEN" is a hidden-constant proxy over the open vocabulary of over-claim wordings | proxy | — | **PARTIAL — blind to a non-"GREEN" over-claim (D2c)** |
| **scoped-line honest content (I13)** | the wave scoped leg line | — | **NO — the honest template is NOT anchored; only the checkpoint receipt + summary are byte/type-anchored** | — | — | **MISSING (D2c)** |
| P4 marker-line-count | producible receipts × marker | DERIVED (`_RED_ENFORCEMENT_CELLS`) | YES for the marker | effect | — | ✅ for the marker; blind to alternate-wording (by design — closed for APPEND by the composition pin) |

**Legs run:** the I13 / scoped-content row is **EMPIRICAL** — W-SCOPED-OVERCLAIM survives 170/170 + reference
control + the proposed-pin discriminator (passes reference, fails D2c). The 7 attacks + M1 + D2a + D2d are
**EMPIRICAL** (discrimination harness, §9). Deviation (a)/(b) safety is **EMPIRICAL** (D1a/D2a/D2d measured).
The scoped pin's blindness is the 7th/8th-defeat shape (reach = a hidden constant, "the word GREEN") applied to
the scoped LEG line — exactly the class §11 fixed for the summary line, left unfixed one line over.

**The author's own copy, applied to the scoped-line guard (INSTRUMENT 0):** *"What is the SET of over-claim
wordings the scoped-line guard forbids — is it DERIVED from the receipt's honest template (the scoped line IS the
fixed honest string with the selector substituted) or a hidden constant (the single token 'GREEN') — and does a
test go RED when the scoped line reads as a clear in words other than 'GREEN'?"* — the byte-oracle answers YES for
the checkpoint receipt and the summary; the wave scoped line answers **NO** (reach = the token "GREEN").

## 7. MISSING PIN — the test that should exist + the defect + the reproduction

### MP-r6 — `test_wave_scoped_leg_line_is_the_fixed_honest_template`
- **Defect caught:** a `--wave` `PASS_SCOPED` receipt whose scoped pytest leg line over-claims a full/clean
  clear in any wording other than the literal "GREEN" (e.g. `SCOPED(-k …) — tree is current and clean; nothing
  owed`). ok=True, exit 0 — the #306/#344 honesty failure on the line built to prevent it.
- **Reproduction (E):** `W-SCOPED-OVERCLAIM` (D2c) — reference with the scoped template's tail changed from
  `NOT a currency clear; full run owed` to `tree is current and clean; nothing owed`. Survives **170 passed,
  0 failed**. Receipt + blind-pin proof in §4.
- **The pin (byte-anchor — the instrument the design ALREADY uses for the checkpoint receipt + summary):** on a
  clean wave receipt, the scoped pytest leg line MUST EQUAL a fixed honest template with the selector substituted,
  e.g. `f"  {'pytest':<12} SCOPED({' '.join(selector)}) — NOT a currency clear; full run owed"` (keyed off the
  scopable gate's DERIVED id, not the literal "pytest"). Converts the scoped-line honest content from an
  under-enumerated cold-audit-read into a CONSTRUCTION catch. **P0 control (§9): passes the honest reference,
  fails D2c.**
- **Durable alternative (recommended for parity with §11):** fold the scoped line into a **sole-minted typed
  `ScopedLine`** (a `render_scoped_leg(selector) -> ScopedLine` byte-anchored template), the string→type lift §11
  applied to the SUMMARY line, applied to the SCOPED leg line — so the honest content is unrepresentable-otherwise,
  not merely byte-checked. **Fork for the author/lead:** minimal byte-anchor pin vs the sole-minted typed line.

## 8. Residuals (individual verdicts — no "the rest look fine")
- **R1 — the disclosed cold-audit-read ZONE is under-enumerated (a partial enumeration).** `REPORT-reviser-g-4.md`
  §6 states "leaving ONLY a fixed WAVE-header constant in the read zone." **Measurably false:** the wave `PASS_SCOPED`
  receipt has THREE wave-only fixed strings — the wave header (disclosed), the `render_summary(PASS_SCOPED)` string
  (fork-2 / §11.8.5, disclosed), and **the scoped-line template (D2c, NOT disclosed)**. If the bound is KEPT as
  cold-audit-read rather than pinned (MP-r6), the disclosure MUST name all three, or the cold audit reads the header
  and misses the honesty-critical one. This is the packet's own "diagnosis is not an instrument / partial enumeration"
  class, one level up in the disclosure. **Verdict: real; fix = MP-r6 (pin it) OR complete the enumeration.**
- **R2 — D1a: checkpoint FAIL detail can carry an over-claim.** A `_render_currency` FAIL receipt can render
  `"SUMMARY: all gates are clean, tree is green"` in the detail. **But it exits nonzero, carries the fixed
  `render_summary(FAIL)` verdict, and the authoritative signals (exit code + fixed FAIL summary) stay honest.**
  Lower severity than D2c (it is not a false CLEAR — the run reads FAIL). Closable by extending the byte-oracle to
  the FAIL receipt (today only PASS is byte-pinned). **Verdict: real, low-severity; flagged for the cold audit.**
- **R3 — D2b: wave header over-claim (the disclosed bound).** A fixed over-claim baked into the wave header string
  survives — but it is results-independent-pinned (`test_wave_header_is_results_independent`), genuinely a fixed
  one-build-site string, and EXPLICITLY disclosed. **Verdict: disclosed bound, met deliberately; least severe.**
- **R4 (inherited) — `test_no_hardcoded_gate_id_collection`'s `canonical` is a hand-list.** A hardcoded tuple of
  RENAMED ids evades the source scan; the behavioural `test_render_enumerates_exactly_the_manifest_gates` +
  `test_scopable_gate_identified_by_reader_not_literal_id` are the coverage-checked instruments. Unchanged — met deliberately.
- **My reference SEAM is untyped** (a speed shortcut in MY probe). It does not affect the wrong-build discrimination
  (behavioural). The CONTRACT file is mypy-clean; the reviser demonstrated a TYPED reference is clean. **Verdict: my
  limitation, not the contract's.**

## 9. Full probe record (commands + real output)
**Scratch (provenance-asserted, #140):** `./scripts/scratch_copy.sh /home/ejprice/scratch-delta-adversary-g-4` →
`wave_gate.__file__`, `pending_contract_gate.__file__`, `loremaster.__file__` all INSIDE the scratch root (§1).

**Discrimination harness (`discriminate.py`, reproduced below) — reference 170/0, then each wrong build:**
```
REFERENCE (positive control): 170 passed, 0 failed
A1 W-EXTRA-LINE (wrapper)                             2 failed  [delegates[wave] + AST]
A2 W-EXTRA-LINE (receipt.render)                      5 failed  [composition x4 + byte-oracle]
A3 orphan-slot over-claim                             5 failed  [orphans_folded x4 + byte-oracle]
A4 roster over-claim                                  1 failed  [byte-oracle]
A5 header over-claim (checkpoint)                     1 failed  [byte-oracle]
A6 NEW free-append (in _render_currency)              2 failed  [byte-oracle + AST]
A7 DRY un-share (_render_currency hand-rolls)         2 failed  [share_the_one_wave_receipt_composition + AST]
D2a compose_wave_receipt over-claims PASS detail      2 failed  [byte-oracle + clean_receipts_have_no_detail_lines]
D2b over-claim baked in WAVE header (disclosed bound) SURVIVOR  [R3]
D2c over-claim baked in scoped_line                   SURVIVOR  [MP-r6 -- the P1 finding]
D2d over-claim via new pcg roster-helper (PASS)       1 failed  [byte-oracle -- shared component backstop]
D1a checkpoint FAIL detail over-claims                SURVIVOR  [R2 -- exits nonzero]
M1 planted new append in wave_gate                    1 failed  [AST reddens on sight -- meta-recursion]
SURVIVORS: D2b (disclosed), D2c (P1/MP-r6), D1a (R2, exits nonzero)
```

**P0 control for MP-r6 (the proposed pin discriminates):**
```
REFERENCE  proposed-pin passes: True   got='  pytest       SCOPED(-k test_changed_area) — NOT a currency clear; full run owed'
D2c        proposed-pin passes: False  got='  pytest       SCOPED(-k test_changed_area) — tree is current and clean; nothing owed'
```

**Instruments (deliverables, brief-base §1 — scratch is disposable). Reproduced verbatim so re-runnable:**

`build_reference.py` — independent reference builder (seam appended to pcg + `_render_currency` routed through
`compose_wave_receipt` + fresh `wave_gate.py`). Load-bearing shape:
```python
# §11 seam
class LegQualification(Enum): CLEAN/OWNED/SCOPED/FAILING
class SummaryVerdict(Enum):   PASS_FULL/PASS_SCOPED/FAIL
class SummaryLine(str): __slots__=()
_SUMMARY_LINES = {PASS_FULL:"CURRENCY   : PASS — every claimed gate is GREEN or OWNED",  # byte-exact historical
                  PASS_SCOPED:"WAVE       : PASS — core is GREEN-or-owned; pytest ran SCOPED, full run still owed",
                  FAIL:"CURRENCY   : FAIL — a claimed gate is RED with nobody's name on it, or was never run"}
def summary_verdict(qs): FAIL if any FAILING else PASS_SCOPED if any SCOPED else PASS_FULL
def render_summary(v): return SummaryLine(_SUMMARY_LINES[v])   # SOLE minter
def _leg_qualification_for(verdict,*,scoped): FAILING/SCOPED/OWNED(RED_ADJUDICATED)/CLEAN
# §11.8 typed components (frozen dataclasses)
ReceiptHeader(lines).render()->list(lines)
RosterLine(manifest).render()->[f"  manifest   : {ids} ({n} gates)"]
GateLeg(currency, scoped_line).render()->[scoped_line or currency.render(), *[f"      ORPHAN: {o}" for o in orphans]]
DetailLines(lines).render()->list(lines)          # () on PASS
WaveReceipt(header,roster,legs,detail,summary,note,verdict); .ok = verdict is not FAIL
   .render()->[*header.render(), *roster.render(), *(l for leg in legs for l in leg.render()),
               *detail.render(), str(summary), note]
compose_wave_receipt(gate, manifest, results, *, header, scoped_selector)  # THE one composition, both paths
   scoped = scoped_selector is not None and READERS[reader] is JUnitReportReader and currency.ok
   scoped_line = f"  {id:<12} SCOPED({scoped_selector}) — NOT a currency clear; full run owed"   # <-- D2c: unpinned content
_render_currency(...) = compose_wave_receipt(..., header=ReceiptHeader(("GATE CURRENCY — …",)), scoped_selector=None).render(), .ok
# wave_gate.py
MODE_WAVE="wave"; MODE_CHECKPOINT="checkpoint"
pytest_args_for(mode, sel) = tuple(sel) if wave else ()
build_wave_receipt(...) -> compose_wave_receipt(..., header=ReceiptHeader((f"GATE BUNDLE [{mode}] — scope: {scope}",)),
                                                scoped_selector=" ".join(sel) if wave else None)
render_wave_receipt(...) = build_wave_receipt(...).render(), .ok
main(argv) -> required mutually-exclusive --wave|--checkpoint; parse_known_args -> trailing -k = selector;
              GateManifest.load / PendingContractRegistry.load; _run_selected_gates(runner, manifest, list(manifest.ids), pytest_args);
              render_wave_receipt(...); return 0 if ok else 1
```
The full `build_reference.py` + `discriminate.py` live in `/home/ejprice/scratch-delta-adversary-g-4/` (disposable);
the D2c one-line wrong build = `compose_wave_receipt`'s scoped template tail `NOT a currency clear; full run owed`
→ `tree is current and clean; nothing owed`.

---

## VERDICT: **CONTRACT INSUFFICIENT**

§11.8 did its named job and did it well: the typed `WaveReceipt` makes the free-APPEND over-claim (W-EXTRA-LINE)
unrepresentable receipt-wide — all seven §11.8.7 attacks die at their designated pins, the round-6 planted append
reddens on sight, the byte-oracle backstops every component shared with the checkpoint path (so the AST-scan scope
deviation opens no helper door), and the mutation proofs make a hand-rolled checkpoint composition red. Both
disclosed deviations are individually SAFE. Satisfiability holds (170/0) and the extraction is non-regressive (41/0).

**But the round-4/5 work hardened the free-APPEND door and the SUMMARY line, and left the scoped LEG line — the
receipt's OTHER honesty-bearing line — as free text guarded only by "not literally GREEN".** `W-SCOPED-OVERCLAIM`
(D2c) over-claims `tree is current and clean; nothing owed` on that line, on a `PASS_SCOPED` (ok=True, exit 0)
receipt, and passes all 170 pins — the #306/#344 honesty failure on the line built to prevent it. The two deviations
converge here: the wave `PASS_SCOPED` receipt is the one pass receipt with no byte/construction anchor on its
honesty content, and the disclosed cold-audit-read zone under-enumerates it (naming only the wave header).

**One missing pin closes it:** `test_wave_scoped_leg_line_is_the_fixed_honest_template` — byte-anchor the scoped
leg line, the instrument the byte-oracle already applies to the checkpoint receipt and the summary line, extended
to the one pass receipt it skips (proven discriminating: passes reference, fails D2c). Recommended durable form:
fold the scoped line into a sole-minted typed `ScopedLine` — the string→type lift §11 applied to the summary,
applied one line over. Routing per standing order: contract → adversary → build → cold audit.
