brief-base v10 read
brief project v7 read

# REPORT-reviser-g-3 — §11 typed summary-honesty redesign for the G contract (`scripts/test_wave_gate.py`, #344/#345)

## Capability check (tool honesty — brief-base §4, first)
Everything the brief demanded was satisfiable. `scratch_copy.sh` built a provenance-asserted copy
(all four members resolve inside it); I authored an INDEPENDENT reference `wave_gate.py` + the seam
extraction there and ran the real contract against it, against every named survivor + the hybrid +
the corrupted-minter variant, and the §9.1 meta-recursion controls. `lore_comms`/lore tools
reachable. Edited ONLY `scripts/test_wave_gate.py` (the seam lives in `pending_contract_gate.py` +
`wave_gate.py` — the BUILDER's, not touched). No impossibilities.

---

## SUMMARY BLOCK
- **State: done.** Retired the string-check summary pins (`_summary_line` + the positive-marker MP-7);
  added §11's four TYPED pins (P1 biconditional ∀ · P2 sole minter · P3 prove-sharing-by-mutation ·
  P4 biconditional belt) — none a forbidden-shape scan.
- **RED for the right reason:** collection errors `ModuleNotFoundError: wave_gate` (deliverable absent);
  the section-8 pins additionally require the absent seam (`SummaryVerdict`/`render_summary`/
  `summary_verdict`/`SummaryLine`). Contract-first RED confirmed.
- **Satisfiability (C-DEF): 143 passed / 0 failed** against an independent reference build in
  provenance-asserted scratch; the OLD-world `test_pending_contract_gate.py` stays **41 passed** after
  the extraction (behaviour-preserving net holds).
- **Discrimination: every survivor + hybrid caught by its designated pin** — W-summary-alt/hybrid→P3,
  W-summary-double→P4+P2b, W-summary-inline(hand)→P3+P4+P2b, W-summary-inline(corrupted-minter)→**P2a+P4**
  (the residual a whole-line token would have MISSED). Meta-recursion: grow the enum → ∀ grows 64→125,
  coverage green; hardcode stale → coverage reddens (both-direction diff).
- **Packages considered:** stdlib `enum` (`SummaryVerdict`/`LegQualification`) + `str` subclass for
  `SummaryLine` — REUSE the in-repo `Rendered`/`SafeLine` AST-mint idiom (`test_render_seam_pins`), not
  a new one. Verdict: **bespoke-minimal, reusing 4 in-repo idioms** (design §11.6 already ruled this).
- **Graded:** `1a5d9b3` · HEAD-at-report: `1a5d9b3` · SAME (graded the working-tree `test_wave_gate.py`,
  uncommitted `M`; scratch copy byte-identical, `diff -q` empty).
- **Decisions-needed (forks surfaced, not resolved unilaterally):** (1) checkpoint FAIL-summary becomes
  a FIXED line — a behaviour change (today's is dynamic) the builder must inventory; (2) the fixed
  PASS_SCOPED/FAIL prose being non-over-claiming is a one-time adversary/audit review item; (3) brief
  paraphrase "PASS_FULL requires ALL legs clean" vs §11.2.2 "no SCOPED ∧ no FAILING (CLEAN-or-OWNED)" —
  resolved toward §11 (see body). Details below.
- **Receipt pointers:** §1 (what changed) · §2 (four pins) · §3 (survivor deaths) · §4 (satisfiability +
  discrimination probes) · §5 (forks) · §6 (instruments, pasted verbatim).

---

## 1. What changed (`scripts/test_wave_gate.py` only)
- **Retired** `_summary_line` (the LAST-PASS/FAIL-line reach — the round-2/3 hidden constant
  `W-summary-double` defeated) and `test_wave_scoped_summary_positively_carries_the_scoped_bound` (MP-7,
  the positive-marker pin). Both are the recurring enumerate-the-forbidden defect. Replaced in place
  with retirement notes pointing at section 8.
- **Added** `import itertools`, `from typing import Any`, and `_summary_seam =
  importlib.import_module("pending_contract_gate")` — a DYNAMIC handle (attrs type as `Any`, measured)
  for the not-yet-built seam, so the typecheck gate stays clean in BOTH the RED and GREEN states (the
  same discipline, same mechanism, as the file's existing `wave_gate` import). `scripts` IS a typecheck
  member (`typecheck.sh` MEMBERS), so a static `from pending_contract_gate import SummaryVerdict` would
  have planted a `has no attribute` red today that flips to a clean import once built — the exact latent
  orphaned red the file's docstring (134–142) forbids.
- **Added section 8** — the four §11 pins + helpers + scanner self-tests + a byte-exact checkpoint
  oracle + the marker anchor. Updated docstring W10 to describe the typed redesign.
- Kept the sound MP-1..MP-6/MP-8 pins intact (verified: the entrypoint ∀, renderer fail-matrix,
  omitted-cell ∀, routes-one-reader spy, meta-recursion, monoculture, scopable-by-reader — all in the
  143-pass).

## 2. The four typed pins (design §11.4 — no forbidden-shape scan)
- **P1 — `summary_verdict` is the biconditional, ∀ over the leg-flag surface**
  (`test_summary_verdict_is_the_biconditional_over_the_flag_surface`, parametrized over
  `LegQualification` members ^ manifest-leg-count, DERIVED live). Typed in, typed out — NO string read.
  Coverage a CHECKED VARIABLE via `test_summary_verdict_combination_surface_equals_the_live_product`
  (both-direction diff, mirrors `test_enforcement_matrix_covers_...`).
- **P2 — `render_summary` is the SOLE minter.**
  - **P2a** `test_render_summary_marker_appears_iff_pass_full` — TOTAL over `SummaryVerdict`; the marker
    appears in EXACTLY PASS_FULL's render (biconditional at the TYPE level, closed 3-value domain). This
    is what forbids BAKING the marker into `render_summary(PASS_SCOPED)`'s fixed string.
  - **P2b** the `Rendered`-style AST scan over `wave_gate.py` (module-scoped like
    `_ALLOWED_MINT_MODULES`): `test_summaryline_is_not_minted_in_wave_gate` +
    `test_unqualified_marker_literal_absent_from_wave_gate` (marker DERIVED from `render_summary(
    PASS_FULL)`, never hardcoded in the scanner) + 6 scanner self-tests proving the detectors are real.
  - **anchor + byte-oracle** `test_unqualified_pass_marker_is_the_sole_minters_marker` (the marker MUST
    be a substring of `render_summary(PASS_FULL)`, so it can never drift into an arbitrary phrase) +
    `test_render_summary_pass_full_preserves_the_checkpoint_line` (removed-behaviour inventory, §11.3).
- **P3 — prove-sharing-by-mutation (DRY #1)** `test_both_currency_paths_derive_their_summary_from_the_
  one_minter`: mutate the shared `render_summary` (both namespaces, §9.7 from-import trap) → BOTH
  `_render_currency`'s AND `render_wave_receipt`'s summaries move. Pos+neg controls (sentinel absent
  before the mutation, present after). NEVER reads a wrong build's wording — inspects DERIVATION.
- **P4 — biconditional belt** `test_unqualified_marker_line_count_is_one_iff_pass_full`: over every
  producible receipt (both modes; clean cells + live `_RED_ENFORCEMENT_CELLS`), the marker appears on
  exactly ONE line IFF the verdict is PASS_FULL, else ZERO. Allowlist-the-safe, keyed to the sole
  minter's marker — NOT a deny-list. This is §9.3's "pin the receipt, not the line" the round-2/3
  `_summary_line` reach dropped.

**Why the marker is DERIVED, not a hardcoded forbidden token.** `_UNQUALIFIED_PASS_MARKER` is the ONE
phrase §11.2.1 names, ANCHORED (must be a substring of `render_summary(PASS_FULL)`) and byte-pinned to
the historical checkpoint line. P2a/P4 tie its appearance to the TYPED verdict by a BICONDITIONAL over
the closed `{PASS_FULL,PASS_SCOPED,FAIL}` domain (marker ⟺ PASS_FULL). That is categorically different
from the deny-list-of-wordings scan that failed 3× — it is the sole minter's own marker, over a closed
enum, not a receipt-text scan for a list of forbidden phrases.

## 3. How each survivor dies BY CONSTRUCTION (empirically confirmed — §4)
- **W-summary-alt** (hand-authored alternate wording) → **P3**: its literal summary does not move when
  `render_summary` is mutated. (Also P4, because a hand-authored summary is not the PASS_FULL clear the
  checkpoint receipt still owes.)
- **W-summary-double** (forged unqualified line on a non-last line) → **P4** (marker-line count) + **P2b**
  (marker literal planted in `wave_gate.py`). Not P3 — the derived line still moves, which is exactly why
  the round-2/3 `_summary_line` pin missed it and P4 does not.
- **W-summary-inline** (marker + lie on one line):
  - hand-authored → **P3** + **P2b** + **P4**.
  - **baked into `render_summary(PASS_SCOPED)`'s fixed string** (the corrupted-minter form — the residual
    a WHOLE-LINE token would have missed, because PASS_SCOPED's prefix differs from PASS_FULL's) → **P2a**
    (PASS_SCOPED render carries the marker) + **P4** (a wave receipt carries a marker line). This is why
    the marker is a discriminating SUBSTRING, anchored to the minter, not the whole line.
- **routing-not-sharing hybrid** (`_render_currency` shares, `render_wave_receipt` hand-rolls) → **P3**:
  the wave summary does not move while the checkpoint one does — P3 pinpoints the un-shared side.

The common death: §11 removes the free-text summary seam and replaces it with
`(typed leg quals) → summary_verdict → SummaryVerdict → render_summary → SummaryLine`. All survivors
require a free-text-authoring seam that no longer exists.

## 4. Satisfiability + discrimination receipts (provenance-asserted scratch, #140)
`./scripts/scratch_copy.sh /home/ejprice/scratch-reviser-g-3` → provenance receipt (all inside scratch):
```
loremaster -> /home/ejprice/scratch-reviser-g-3/loremaster/loremaster/__init__.py
pcg        -> /home/ejprice/scratch-reviser-g-3/scripts/pending_contract_gate.py
wave_gate  -> /home/ejprice/scratch-reviser-g-3/scripts/wave_gate.py
```
Reference build (seam extracted into pcg + independent `wave_gate.py`) — the scratch
`test_wave_gate.py` is byte-identical to the graded working-tree file (`diff -q` empty):
```
C-DEF satisfiability : uv run pytest scripts/test_wave_gate.py -q     -> 143 passed
OLD-world net        : uv run pytest scripts/test_pending_contract_gate.py -> 41 passed  (extraction non-regressive)
RED honesty (real)   : --collect-only -> ModuleNotFoundError: No module named 'wave_gate'  (1 error, right reason)
```
Discrimination (each wrong build = a targeted patch of the reference; full contract run):
```
REFERENCE                              -> 143 passed
W-summary-alt / hybrid                 -> FAIL: test_both_currency_paths_derive... (P3) + marker_line_count (P4)
W-summary-double                       -> FAIL: marker_line_count (P4, ~all cells) + marker_literal_absent (P2b)
W-summary-inline (hand-authored)       -> FAIL: derive (P3) + marker_line_count (P4) + marker_literal_absent (P2b)
W-summary-inline (corrupted minter)    -> FAIL: marker_appears_iff_pass_full (P2a) + marker_line_count[wave-clean] (P4)
```
Meta-recursion (§9.1 ⚠, P1 reach is a checked variable):
```
grow LegQualification (+EXPIRED)       -> P1 params 64 -> 125 (5^3); coverage pin GREEN (both derive live)
hardcode _LEG_QUAL_COMBOS stale        -> test_summary_verdict_combination_surface_equals_the_live_product REDDENS
                                          (both-direction diff: missing=[60 combos], stale=[])
```
Non-vacuity of the anchor/byte-oracle: rewording `render_summary(PASS_FULL)` reddens 5 pins (anchor,
byte-oracle, P2a, the literal-scan belt, P4[checkpoint-clean]). Every probe paired with the reference
control (143-pass), so no result is a blind probe.

## 5. Forks surfaced (scope law — I do not resolve these unilaterally)
1. **Checkpoint FAIL summary becomes a FIXED line — a behaviour change.** Today's `_render_currency`
   FAIL line is DYNAMIC (`f"CURRENCY   : FAIL — {reasons}"`, embedding the specific failing gate ids). A
   fixed `render_summary(FAIL)` enum→string mapping CANNOT reproduce it byte-exact, so §11.2.1's "FAIL
   maps byte-exact to today's FAIL line" is in tension with §11.2.3's "enum → FIXED string". The per-gate
   `ORPHAN:` detail lines still carry the specifics, so no INFORMATION is lost and no existing test pins
   the dynamic FAIL line (verified — `test_pending_contract_gate.py` does not exercise `_render_currency`).
   My reference used a fixed FAIL line and all 41 OLD-world tests stayed green. **Builder fork:** keep the
   dynamic reasons as a SEPARATE detail line under a fixed FAIL headline (preserve), or drop them
   deliberately (removed-behaviour inventory). My contract does NOT pin `render_summary(FAIL)`'s exact
   bytes for this reason. **Recommend: preserve as a separate detail line.**
2. **PASS_SCOPED/FAIL fixed prose being non-over-claiming is a one-time review item.** P2a catches a
   PASS_SCOPED render CONTAINING the exact marker; a rephrased over-claim that avoids the marker phrase is
   fixed prose the type system cannot judge. Per §11.2.3 ("wording is FIXED, not a per-call degree of
   freedom") this is a build-time review item — the adversary + cold audit should READ the two new fixed
   strings. Not automatable without re-introducing an enumerate-the-forbidden scan. Flagged, not closed.
3. **Brief paraphrase vs §11 spec (resolved reading, brief-base §2).** The spawn brief says "PASS_FULL
   requires ALL legs clean"; §11.2.2's biconditional says PASS_FULL iff NO leg SCOPED ∧ NO leg FAILING —
   i.e. all legs ∈ {CLEAN, **OWNED**}. I pinned §11.2.2 (OWNED admitted into PASS_FULL) because the
   byte-exact checkpoint PASS line FORCES it: today's clear (`every claimed gate is GREEN or OWNED`) fires
   for GREEN-**or-OWNED**, so a "requires ALL CLEAN" reading would make the reference build's own byte-
   preserved checkpoint fail P1. §11 is the spec (brief: "§11 VERBATIM — your spec"); the paraphrase is a
   compression. Both readings written into the P1 docstring; I picked §11.
4. **`pending_contract_gate.py` in G's writable set** — already operator-RULED (brief: "APPROVED — G's
   build extracts the summary seam into the SHIPPED `pending_contract_gate.py`"). Noted, not a new fork.

## 6. Instruments (deliverables, pasted verbatim per brief-base §1 — the scratch tree is disposable)
The scratch tree `/home/ejprice/scratch-reviser-g-3` holds `build_reference.py` + `discriminate.py`
(the reference build + the wrong-build patch table) and is disposable by design; the load-bearing logic
is reproduced here so the satisfiability/discrimination claims are re-runnable without it.

**Reference seam (extracted into `pending_contract_gate.py`):**
```python
class LegQualification(enum.Enum): CLEAN="clean"; OWNED="owned"; SCOPED="scoped"; FAILING="failing"
class SummaryVerdict(enum.Enum):   PASS_FULL="pass_full"; PASS_SCOPED="pass_scoped"; FAIL="fail"
class SummaryLine(str): __slots__=()
def summary_verdict(leg_quals):
    if any(q is LegQualification.FAILING for q in leg_quals): return SummaryVerdict.FAIL
    if any(q is LegQualification.SCOPED  for q in leg_quals): return SummaryVerdict.PASS_SCOPED
    return SummaryVerdict.PASS_FULL
_SUMMARY_LINES = {
  SummaryVerdict.PASS_FULL:   "CURRENCY   : PASS — every claimed gate is GREEN or OWNED",   # byte-exact
  SummaryVerdict.PASS_SCOPED: "WAVE       : PASS — core is GREEN-or-owned; pytest ran SCOPED, full run still owed",
  SummaryVerdict.FAIL:        "CURRENCY   : FAIL — a claimed gate is RED with nobody's name on it, or was never run",
}
def render_summary(verdict): return SummaryLine(_SUMMARY_LINES[verdict])   # SOLE minter
def _leg_qualification_for(verdict, *, scoped):
    if verdict in FAILING_VERDICTS: return LegQualification.FAILING
    if scoped: return LegQualification.SCOPED
    if verdict == VERDICT_RED_ADJUDICATED: return LegQualification.OWNED
    return LegQualification.CLEAN
# _render_currency routes its summary through summary_verdict/render_summary (all legs scoped=False);
# a shared _gate_currencies(gate, manifest, results) factors the per-gate loop (ONE implementation).
```
**Reference `wave_gate.render_wave_receipt` core (derives scoped per leg, shares the minter):**
```python
for spec, currency in zip(manifest.gates, currencies):
    is_scopable = READERS[spec.reader] is JUnitReportReader
    scoped = is_scopable and mode == MODE_WAVE and currency.ok
    leg_quals.append(_leg_qualification_for(currency.verdict, scoped=scoped))
    lines.append(f"  {spec.id:<12} SCOPED({selector}) — NOT a currency clear; full run owed"
                 if scoped else currency.render())
verdict = summary_verdict(leg_quals); ok = verdict is not SummaryVerdict.FAIL
lines.append(str(render_summary(verdict)))   # the ONE sharing point P3 mutates
```
**Wrong-build patches (each a one-line targeted edit of the reference):**
```
W-summary-alt/hybrid : render_wave_receipt summary line -> "SUMMARY: all gates are clean, tree is green"
W-summary-double     : insert  "CURRENCY   : PASS — every claimed gate is GREEN or OWNED"  before the derived line
W-summary-inline(hand): summary line -> "WAVE : PASS — every claimed gate is GREEN or OWNED (pytest SCOPED)"
W-summary-inline(minter): _SUMMARY_LINES[PASS_SCOPED] -> "...every claimed gate is GREEN or OWNED (pytest SCOPED)"
```

## VERDICT
CONTRACT REVISED to §11's four typed pins; string-check summary pins RETIRED. RED for the right reason;
satisfiable 143/0 against a known-correct build; every survivor + hybrid + the corrupted-minter residual
caught by its designated pin; P1 reach a checked variable (meta-recursion both directions). Routing:
**contract → adversary → build → cold audit** — the contract-adversary should re-attack with
W-summary-alt/double/inline + the hybrid + the corrupted-minter variant (all confirmed caught here), and
the operator/lead should rule fork (1) (FAIL-line behaviour) and note fork (2) (fixed-prose review).
