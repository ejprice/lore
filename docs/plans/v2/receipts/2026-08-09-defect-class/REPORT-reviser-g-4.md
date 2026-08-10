brief-base v10 read
brief project v7 read

# REPORT — reviser-g-4 (CONTRACT reviser: §11.8 full typed WaveReceipt for INSTRUMENT G, #344/#345)

## SUMMARY BLOCK
- **State: done.** Applied design §11.8 (VERBATIM spec) to G's contract — added a §11.8 section
  (27 new pins) to `scripts/test_wave_gate.py` that types the WHOLE RECEIPT (all six line
  sources), so an over-claim is unrepresentable RECEIPT-WIDE, not just in the summary slot. The
  §11 P1–P4 summary pins + MP-1..6/MP-8 are UNTOUCHED and still pass.
- **Capability check:** brief fully satisfiable — lore tools loaded (`ToolSearch "+lore"`),
  `scratch_copy.sh` built a provenance-asserted copy, `lore_comms` reachable (drained: empty). No
  impossibility.
- **Deviations (2, both design-forced, disclosed):**
  1. **No byte-equality pin between `render_wave_receipt(CHECKPOINT)` and `_render_currency`.**
     They SHARE the WaveReceipt type+composition (proven by mutation) but are NOT byte-equal: the
     bundle receipt RECORDS the mode in its header (`test_receipt_header_records_the_chosen_mode`),
     `_render_currency` keeps the HISTORICAL checkpoint header (byte-oracle, §11.3). A byte-diff
     between them would be FALSE by construction. DRY #1 is proven by the mutation pin instead.
  2. **AST scan scoped to `wave_gate.py` (whole) + `_render_currency` (function-body), not a
     blanket `.append` ban over all of `pending_contract_gate.py`** — the shared component
     `render()`/helper methods legitimately compose strings; scanning the whole file false-positives
     on `_residuals_for`/`_fail_detail`. The checkpoint free-append door is closed by the AST scan
     on the delegating `_render_currency` PLUS the byte-oracle PLUS the composition pin (effect
     checks, stronger than a source scan). Faithful to §11.8.2's allowlist-the-safe intent.
- **Packages considered:** none new — reference reuses in-repo `pending_contract_gate` machinery
  (`GateCurrency`/`gate_currency`/`_residuals_for`/`READERS`/`_run_selected_gates`), the §11 summary
  seam, and the `TestSafeLineRenderedMintPin` AST idiom; stdlib `ast`/`enum`/`dataclasses`. Verdict:
  **reuse/bespoke-minimal** (the string→type lift applied one level up).
- **Graded:** worked against HEAD `b7bf68c` with the working-tree r5 `scripts/test_wave_gate.py`
  (uncommitted `M`) as baseline · HEAD-at-report `b7bf68c` · SAME.
- **Decisions-needed:** none new. (Delta R2 / reviser fork-1 was RULED by the lead — FAIL reasons →
  typed detail component, pinned as such below. Reviser fork-2 residual = a one-time cold-audit READ
  of `render_summary(PASS_SCOPED)`/`FAIL` fixed strings, §11.8.5 — noted, not a pin.)
- **Receipt pointers:** §1 (satisfiability 170/0 + non-regression 41/0) · §2 (the four §11.8.7
  attacks → designated pins, measured) · §3 (the pins added) · §4 (RED-for-right-reason) · §5 (the
  reference instrument, verbatim) · §6 (bounds, honest).

---

## 1. Satisfiability (C-DEF) + non-regression — provenance-asserted scratch (#140)

`./scripts/scratch_copy.sh /home/ejprice/scratch-reviser-g-4` — provenance VERIFIED, all imports
resolve INSIDE the scratch root:
```
wave_gate  -> /home/ejprice/scratch-reviser-g-4/scripts/wave_gate.py
pcg        -> /home/ejprice/scratch-reviser-g-4/scripts/pending_contract_gate.py
loremaster -> /home/ejprice/scratch-reviser-g-4/loremaster/loremaster/__init__.py
```
I authored an INDEPENDENT reference (the full §11 seam + §11.8 typed `WaveReceipt` extracted into
`pending_contract_gate.py`, `_render_currency` routed through the shared `compose_wave_receipt`, and
a fresh `wave_gate.py`) — reproduced verbatim in §5. The scratch `test_wave_gate.py` is byte-identical
to the working-tree contract (`diff -q` empty).

```
C-DEF satisfiability : uv run pytest scripts/test_wave_gate.py -q            -> 170 passed  (143 prior + 27 new §11.8 pins)
NON-REGRESSION       : uv run pytest scripts/test_pending_contract_gate.py -q -> 41 passed   (the extraction is behaviour-preserving)
GATE clean (contract): MYPYPATH=scripts uv run mypy scripts | grep test_wave_gate.py -> (empty); uv run ruff check scripts/test_wave_gate.py -> All checks passed!
GATE clean (ref seam): MYPYPATH=scripts uv run mypy scripts | grep {wave_gate,pending_contract_gate}.py -> (empty); ruff -> All checks passed!
RED honesty (real)   : uv run pytest scripts/test_wave_gate.py --collect-only -> ModuleNotFoundError: No module named 'wave_gate' at :151, 1 error (right reason)
```
The reference is satisfiable by a build that is ALSO mypy+ruff clean under the gate invocation
(`MYPYPATH=scripts uv run mypy scripts`) — so the contract does not force a gate-dirty seam.

## 2. The four §11.8.7 attacks — each dies at its DESIGNATED pin (measured, not asserted)

Every wrong build is a targeted patch of the reference, run against the FULL contract in
provenance-asserted scratch (`discriminate.sh`, reproduced §5.3). The r5 SURVIVOR (`W-EXTRA-LINE`,
which passed the old 143 pins) now reddens; nothing is vacuous.

| # | attack (§11.8.7) | wrong build | failing count | DESIGNATED pin(s) that fired |
|---|---|---|---|---|
| A1 | **W-EXTRA-LINE** (wrapper) | `render_wave_receipt` appends a banner after `.render()` (wave) — the literal delta survivor | 2 failed | `test_render_wave_receipt_delegates_to_the_typed_receipt` + `test_no_free_receipt_line_composition_outside_render` (AST) |
| A2 | **W-EXTRA-LINE** (receipt) | free append inside `WaveReceipt.render()` | 5 failed | `test_wave_receipt_is_the_fixed_typed_composition_no_free_append` (composition) + byte-oracle |
| A3 | **orphan-slot over-claim** | extra line in `GateLeg.render()` | 5 failed | `test_wave_receipt_one_leg_per_gate_orphans_folded` (`len==1+orphans`) + byte-oracle |
| A4 | **roster over-claim** | extra line in `RosterLine.render()` | 1 failed | `test_checkpoint_receipt_preserves_the_historical_bytes` (byte-oracle) |
| A5 | **header over-claim** (checkpoint) | extra line in `_render_currency` header | 1 failed | `test_checkpoint_receipt_preserves_the_historical_bytes` (byte-oracle) |
| A6 | **NEW free-append path** (round 5) | new `lines.append(...)` in `_render_currency` | 2 failed | `test_no_free_receipt_line_composition_outside_render` (AST) + byte-oracle |
| A7 | **DRY un-share** | `_render_currency` hand-rolls its own composition (routing-not-sharing) | 5 failed | `test_both_currency_paths_share_the_one_wave_receipt_composition` (mutation) + P3 + AST + byte-oracle + prod-fork-1 |

Positive control: the honest reference passes 170/0 with no over-claim line. Scanner self-tests (6)
prove the AST detectors are REAL, not vacuously green (the seam does not exist at authoring time).

## 3. The pins added (§11.8.3), and how they make the reach a CHECKED VARIABLE over STRUCTURE

The §11 walls stopped at the summary LINE; the reach was still the ONE marker string over open
receipt vocabulary (r5). §11.8 lifts string→type ONE LEVEL UP to the RECEIPT. All six line sources
(header, roster, per-gate legs with orphans FOLDED IN, FAIL detail, sole-minted summary, fixed note)
are typed components; `render()` is a total composition over exactly them.

- `test_wave_receipt_is_the_fixed_typed_composition_no_free_append` (4 cells: both modes × clean/FAIL)
  — `render()` == the reconstruction from the NAMED typed components; a line no component produced
  makes them differ → RED. The core round-4 close.
- `test_wave_receipt_one_leg_per_gate_orphans_folded` (4 cells) — `len(legs)==len(gates)` and
  `len(leg.render())==1+len(leg.currency.orphans)`; the orphan free-`str` append (§11.8.2 row 4, the
  OTHER W-EXTRA-LINE slot) is a typed sub-render, so an extra orphan-region line → RED.
- `test_no_free_receipt_line_composition_outside_render` (+ 6 scanner self-tests) — the round-5 GUARD:
  no free-`str` list composition in `wave_gate.py`, none inside `_render_currency`; a NEW append path
  reddens ON SIGHT (reach = a checked variable over structure, allowlist-the-safe, NOT a marker
  deny-list). Reuses the `TestSafeLineRenderedMintPin` AST idiom.
- `test_both_currency_paths_share_the_one_wave_receipt_composition` — mutate `WaveReceipt.render` →
  BOTH the wave path AND checkpoint `_render_currency` move (DRY #1, operator-granted; the mutation
  proof, complementing §11's P3 which shares `render_summary`).
- `test_checkpoint_receipt_preserves_the_historical_bytes` — the removed-behavior net (§11.3/§11.8.4)
  WIDENED from the summary line to the whole clean checkpoint receipt (header/roster/gates/PASS/note),
  converting the checkpoint header/roster/note slots from a cold-audit read into a CONSTRUCTION catch.
- **fork-1 (LEAD ruling), 2 pins:** `test_checkpoint_fail_reasons_preserved_as_typed_detail_not_on_the_verdict_line`
  (bundle: FAIL summary is the FIXED `render_summary(FAIL)`, reasons preserved on a separate TYPED
  `.detail` component, `"ruff"` on detail not on the verdict line) + `test_render_currency_fail_uses_the_fixed_verdict_and_preserves_reasons`
  (the same split lands on the PRODUCTION `--currency` path). Info kept, verdict stays typed, pinned
  as a component (not a free append). Plus `test_clean_receipts_have_no_detail_lines` (detail empty on PASS).
- Support pins: `test_wave_receipt_seam_exists`, `test_wave_receipt_exposes_the_typed_components`,
  `test_render_wave_receipt_delegates_to_the_typed_receipt`,
  `test_wave_receipt_summary_is_the_sole_minted_line_and_ok_agrees`, `test_wave_header_is_results_independent`.

**META-RECURSION:** the ∀ over the receipt's line sources == the COMPLETE named-component set; a new
source must be a typed component in `_reconstruct_receipt` or the composition pin reddens, and a free
append reddens the AST scan — coverage over receipt STRUCTURE is the checked variable, not a string.

## 4. RED-for-the-right-reason (real repo, wave_gate ABSENT)
```
uv run pytest scripts/test_wave_gate.py --collect-only
-> ModuleNotFoundError: No module named 'wave_gate'  at scripts/test_wave_gate.py:151 (importlib.import_module)
   no tests collected, 1 error
```
The intended contract-first RED — the whole file (existing + new pins) errors at collection because
the module under contract does not exist yet.

## 5. The reference instrument (verbatim — the scratch tree is disposable, brief-base §1)

### 5.1 The §11.8 typed receipt seam (added to `pending_contract_gate.py`), load-bearing core
```python
class LegQualification(enum.Enum): CLEAN="clean"; OWNED="owned"; SCOPED="scoped"; FAILING="failing"
class SummaryVerdict(enum.Enum):   PASS_FULL="pass_full"; PASS_SCOPED="pass_scoped"; FAIL="fail"
class SummaryLine(str): __slots__=()
_SUMMARY_LINES = {PASS_FULL:"CURRENCY   : PASS — every claimed gate is GREEN or OWNED",   # byte-exact historical
                  PASS_SCOPED:"WAVE       : PASS — core is GREEN-or-owned; pytest ran SCOPED, full run still owed",
                  FAIL:"CURRENCY   : FAIL — a claimed gate is RED with nobody's name on it, or was never run"}
def summary_verdict(qs): return FAIL if any(q is FAILING for q in qs) else PASS_SCOPED if any(q is SCOPED for q in qs) else PASS_FULL
def render_summary(v):   return SummaryLine(_SUMMARY_LINES[v])                             # SOLE minter
def _leg_qualification_for(verdict,*,scoped):
    if verdict in FAILING_VERDICTS: return FAILING
    if scoped: return SCOPED
    return OWNED if verdict==VERDICT_RED_ADJUDICATED else CLEAN

@dataclass(frozen=True)
class ReceiptHeader: lines: tuple[str,...];         # render()->self.lines  (records mode+scope)
@dataclass(frozen=True)
class RosterLine: manifest: GateManifest            # render()->(f"  manifest   : {ids} ({n} gates)",)
@dataclass(frozen=True)
class GateLeg: currency: GateCurrency; scoped_line: str|None
    # render()-> (scoped_line or currency.render(), *(f"      ORPHAN: {o}" for o in currency.orphans))
@dataclass(frozen=True)
class DetailLines: lines: tuple[str,...]            # render()->self.lines  (FAIL reasons; () on PASS)
@dataclass(frozen=True)
class WaveReceipt:
    header: ReceiptHeader; roster: RosterLine; legs: tuple[GateLeg,...]
    detail: DetailLines; summary: SummaryLine; note: str; verdict: SummaryVerdict
    @property
    def ok(self): return self.verdict is not SummaryVerdict.FAIL
    def render(self):                                # a TOTAL composition over exactly the typed components
        return [*self.header.render(), *self.roster.render(),
                *(l for leg in self.legs for l in leg.render()),
                *self.detail.render(), str(self.summary), self.note]
```
`compose_wave_receipt(gate, manifest, results, *, header, scoped_selector)` is the ONE composition,
shared by `_render_currency` (checkpoint, `scoped_selector=None`, historical header) and
`wave_gate.build_wave_receipt` (wave, the `-k` string, mode-recording header). `_render_currency`
becomes: `receipt = compose_wave_receipt(gate, manifest, results, header=ReceiptHeader(("GATE
CURRENCY — is every CLAIMED gate green, or owned?",)), scoped_selector=None); return receipt.render(),
receipt.ok`.

### 5.2 `wave_gate.py` reference (the delegating bundle)
`build_wave_receipt(...)` builds a `WaveReceipt` with a mode-recording header (`GATE BUNDLE [WAVE|
CHECKPOINT] …`) and `scoped_selector=" ".join(pytest_selector)` in wave / `None` in checkpoint, via
`compose_wave_receipt`. `render_wave_receipt(...) == (build_wave_receipt(...).render(), ...ok)` —
composes nothing itself. `main` uses a REQUIRED mutually-exclusive `--wave|--checkpoint` group
(`parse_known_args`; trailing `-k …` = the selector), routes through the module-global
`_run_selected_gates` + `render_wave_receipt`, and returns `0 if ok else 1`. (Full file in the scratch
tree; skeleton here is the load-bearing shape.)

### 5.3 Discrimination harness (`discriminate.sh`) — the §2 table's generator
Backs up `wave_gate.py`/`pending_contract_gate.py`, applies each attack via an inline `python3` string
patch, runs `uv run pytest scripts/test_wave_gate.py -q -rf --tb=no`, greps the `^FAILED` names, and
restores. Reproduced results are §2. (Lives in `/home/ejprice/scratch-reviser-g-4/discriminate.sh`.)

## 6. Bounds (honest — trust doctrine / §6)
- **Per-call free-append door: CLOSED BY CONSTRUCTION** (the honest-developer threat model — a free
  `lines.append("banner")`). Composition pin + leg-count + wave_gate AST scan + `_render_currency` AST
  scan + byte-oracle cover A1–A6 as measured.
- **A baked over-claim inside a FIXED component render string** (the new WAVE-header text, or a new
  component's constant) is NOT a per-call wrong-build door (a builder cannot vary a sole-minted fixed
  string per call) — it is a ONE-TIME cold-audit READ of the few new component render strings, the
  reviser fork-2 boundary (§11.8.5), stated in the contract's §11.8 section header, met deliberately as
  a checklist item — NOT dressed as a pin it cannot be. The checkpoint byte-oracle converts the
  checkpoint header/roster/note slots from that read into a construction catch (A4/A5 measured RED);
  the WAVE header's results-INDEPENDENCE is pinned (`test_wave_header_is_results_independent`), leaving
  only a fixed WAVE-header constant in the read zone.
- **Named re-open trigger** (from §11.8.7): any new receipt line source added later must be a typed
  component (composition pin) or a free append reddens the AST scan — a builder cannot add a free-`str`
  line. If a future packet splits `OWNED` out of `PASS_FULL`, §11's P1/P2 grow by one enum value (that
  coverage pin reddens until extended) — unchanged by §11.8.

## 7. Scope / housekeeping
- Edited ONLY `scripts/test_wave_gate.py` in the real tree (confirmed `git status`). The scratch pcg +
  wave_gate edits are in `/home/ejprice/scratch-reviser-g-4` (a `scratch_copy.sh` copy, disposable by
  design). **Flagging the scratch dir for the operator** to keep or discard — it holds the reference
  build + `discriminate.sh`; the load-bearing logic is reproduced above so it can be safely removed.
- The BUILDER authors the real seam (§5.1/§5.2) in `pending_contract_gate.py` (operator-granted
  writable) + new `scripts/wave_gate.py`; the contract-adversary re-attacks with W-EXTRA-LINE + orphan-
  slot + header-slot + a NEW free-append path (all four must be caught — §2 shows they are, in the
  reference).
