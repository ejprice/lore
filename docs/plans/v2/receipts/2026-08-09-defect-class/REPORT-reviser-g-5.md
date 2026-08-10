brief-base v10 read
brief project v7 read

# REPORT-reviser-g-5 — §11.9 applied to the G contract: ∀ over the DERIVED honesty-line set (round 6, the endgame)

## SUMMARY BLOCK
- **State:** done. `scripts/test_wave_gate.py` extended with the §11.9 endgame pins — CONTRACT TESTS ONLY, no production/impl code touched. 170 → **178** pins.
- **The 2 derived anchors added (§11.9.3):**
  1. `test_every_wave_receipt_line_is_byte_anchored_over_the_derived_verdict_state_domain` — the WHOLE receipt byte-exact vs the audited golden, ∀ over the derived verdict-state domain (checkpoint→PASS_FULL/FAIL, wave→PASS_SCOPED/FAIL). **EXTENDS the existing byte-oracle idiom** (`test_checkpoint_receipt_preserves_the_historical_bytes`) to the WAVE receipt — the one it skipped. Anchors EVERY line, so it strictly SUBSUMES the honesty subset (D2c scoped-leg, D1a wave FAIL-detail, any round-7 line).
  2. `test_every_typed_component_prose_is_byte_anchored_over_its_enum_domain` — per-component ∀: summary over `SummaryVerdict.__members__`, leg over `LegQualification.__members__` (× scoped); the iterated (component × state) set == the live `__members__` (§11 meta-recursion), so the anchored honesty-line set is a **CHECKED VARIABLE**.
- **The existing byte-oracle EXTENDED (named):** `test_checkpoint_receipt_preserves_the_historical_bytes` (§11.8.4) — its construction idiom (`GateCurrency.render()` legs + fixed honesty constants) is reused via the new shared `_expected_receipt_lines` golden builder, generalised to both modes + the FAIL state.
- **NO honesty-line classifier written** (R1's trap): the byte-oracle anchors every line; the per-component ∀ iterates enum `__members__`; every "hand-list" (`_SUMMARY_GOLDEN_BY_NAME` keys, `leg_anchor_names`) is DIFFED both-ways against live `__members__`. No content classification of "lines that read as a clear" anywhere.
- **D2c / D1a / round-7 / R1 all die by construction** — see §4; each proven RED-for-the-right-reason by a mutation (§3).
- **HONEST BOUND stated in the contract (not glossed):** the byte-oracle pins CONSISTENCY WITH AN AUDITED GOLDEN, not semantic honesty; the golden's prose honesty is human-established ONCE (my read when I wrote the goldens, generalising reviser fork-2's one-time read to every catalog constant). Written into the §10 section header + `_expected_receipt_lines`/`_detail_golden` docstrings.
- **Packages considered:** none new — reuses in-repo idioms only (the checkpoint byte-oracle, the §11 closed enums + `_leg_qual_combos` meta-recursion, `test_render_summary_*`, the `TestSafeLineRenderedMintPin`/`_string_literal_lines_containing` mint-scan, `GateCurrency.render`). stdlib only in the reference (`enum`/`dataclasses`). Verdict: **bespoke-minimal, extending four in-repo idioms** — no library supplies "every receipt line byte-anchored over a derived enum domain".
- **Graded:** `pending_contract_gate.py` (extraction base) at HEAD `2fe81ba` · HEAD-at-report `2fe81ba` · **SAME** (the 4158f96→2fe81ba move is the design doc only, +123 lines appended after §12; §11.9 unchanged, 0 deletions; pcg unchanged, working-tree pcg == HEAD).
- **RED honesty (real repo):** `--collect-only` → `ModuleNotFoundError: No module named 'wave_gate'` at :151 — 1 error, the intended contract-first RED. ruff clean · mypy clean (contract, MYPYPATH=scripts).
- **Satisfiability (C-DEF):** **178 passed / 0 failed** against an INDEPENDENT reference; **extraction NON-REGRESSIVE — `test_pending_contract_gate.py` 41 passed**. All 4 mutation proofs discriminate; positive control 178/0.
- **Provenance (#140):** reference built in `/home/ejprice/scratch-reviser-g-5/` (via `scratch_copy.sh`); `wave_gate.__file__`, `pending_contract_gate.__file__`, `loremaster.__file__` all resolve INSIDE the scratch root (asserted, §1).
- **Deviations / decisions-needed:** 2, both minor and disclosed — see §5. Neither blocks; each has a recommendation.
- **Receipt pointers:** §1 satisfiability+non-regression+provenance · §2 the pins added (file:symbol) · §3 mutation proofs (measured) · §4 how each survivor dies · §5 deviations/forks · §6 reused instruments (verbatim shapes).

---

## 1. Satisfiability + extraction non-regression (provenance-asserted scratch, #140)

`./scripts/scratch_copy.sh /home/ejprice/scratch-reviser-g-5` → all imports INSIDE the copy:
```
wave_gate  -> /home/ejprice/scratch-reviser-g-5/scripts/wave_gate.py
pcg        -> /home/ejprice/scratch-reviser-g-5/scripts/pending_contract_gate.py
loremaster -> /home/ejprice/scratch-reviser-g-5/loremaster/loremaster/__init__.py
```
I authored an INDEPENDENT reference (the §11 seam + §11.8 typed `WaveReceipt`
[`ReceiptHeader`/`RosterLine`/`GateLeg`/`DetailLines`/`WaveReceipt`/`compose_wave_receipt`]
extracted into `pending_contract_gate.py`, `_render_currency` routed through the shared
`compose_wave_receipt` with the fork-1 typed FAIL detail, and a fresh `wave_gate.py`),
adopting the shape `REPORT-delta-adversary-g-4.md` §9 measured at 170/0 and extending it with
the §11.9 audited goldens. The scratch `test_wave_gate.py` is byte-identical to my working-tree
contract.
```
C-DEF satisfiability : uv run pytest scripts/test_wave_gate.py            -> 178 passed / 0 failed
NON-REGRESSION       : uv run pytest scripts/test_pending_contract_gate.py -> 41 passed
RED honesty (real)   : uv run pytest scripts/test_wave_gate.py --collect-only
                       -> ModuleNotFoundError: No module named 'wave_gate' at :151 (1 error, right reason)
ruff (real contract) : uv run ruff check scripts/test_wave_gate.py         -> All checks passed!
mypy (real contract) : MYPYPATH=scripts uv run mypy scripts/test_wave_gate.py -> Success: no issues found
```
178 = the 170 pre-existing pins + my 8 new (`…derived_verdict_state_domain`[4 cells] +
`…covers_the_derived_verdict_state_domain` + `…prose_is_byte_anchored_over_its_enum_domain` +
`test_scoped_honesty_prose_is_sole_minted` + `test_wave_summary_strings_are_not_authored_in_wave_gate`).

The reference instruments (`build_reference.py`, `discriminate.py`) live in the disposable scratch;
their load-bearing shape is reproduced verbatim in §6 (brief-base §1 — an instrument is a deliverable).

## 2. The pins added (`scripts/test_wave_gate.py`, section 10 — file:symbol)

- **Goldens (the audited honest prose, §11.9.5 — established ONCE, here):** `_bundle_header`,
  `_SCOPED_HONESTY_GOLDEN` (`"NOT a currency clear; full run owed"`), `_WAVE_SUMMARY_PASS_SCOPED`,
  `_WAVE_SUMMARY_FAIL`, `_SUMMARY_GOLDEN_BY_NAME` (keyed by SummaryVerdict NAME, coverage-diffed live).
- **Helpers (reuse the shared honest machinery):** `_scopable_gate_id` (reader-derived, not `"pytest"`),
  `_wave_scope`, `_canonical_leg_currency`, `_leg_golden`, `_detail_golden`, `_expected_receipt_lines`
  (the checkpoint byte-oracle's construction generalised to both modes + FAIL — the EXTENSION).
- **PIN-1** `test_every_wave_receipt_line_is_byte_anchored_over_the_derived_verdict_state_domain`
  (4 parametrized cells) + its meta-recursion coverage
  `test_wave_receipt_byte_anchor_covers_the_derived_verdict_state_domain`.
- **PIN-2** `test_every_typed_component_prose_is_byte_anchored_over_its_enum_domain` (coverage asserted
  BEFORE iterating — the round-7 checked variable).
- **Sole-mint (mint-scan extended to the new prose):** `test_scoped_honesty_prose_is_sole_minted`
  (one source across production) + `test_wave_summary_strings_are_not_authored_in_wave_gate` (the
  summary strings authored only by `render_summary` in the seam, never in `wave_gate.py` — extends
  `test_unqualified_marker_literal_absent_from_wave_gate`).

## 3. Mutation proofs (§11.9.3, both directions) — each RED for the RIGHT reason (measured)

`discriminate.py` applies each wrong build to the reference and runs the full contract; positive
control = pristine 178/0. Measured output:

| # | wrong build | result | pins that reddened |
|---|---|---|---|
| D2c | scoped-leg tail reworded to `tree is current and clean; nothing owed` (false clear on a PASS_SCOPED, exit-0 receipt) | 4 failed | PIN-1 (`…derived_verdict_state_domain`) + PIN-2 (`…enum_domain`) + `test_scoped_honesty_prose_is_sole_minted` |
| D1a-extra | over-claim EXTRA line `SUMMARY: all gates are clean, tree is green` in the FAIL detail | 2 failed | PIN-1 (checkpoint-fail + wave-fail cells) |
| D1a-reword | the FAIL-detail FRAMING reworded (`RED with nobody's name on it:` → a false clear) | 2 failed | PIN-1 (checkpoint-fail + wave-fail) — proves the framing is byte-anchored, not just "an extra line" |
| round-7 grow-enum | add `LegQualification.PARTIAL` WITHOUT an anchor | 1 failed | PIN-2 coverage ONLY (the other meta-recursion pins auto-grow live; the byte-anchor SET is the checked variable that reddens) |
| round-7 new-line | a brand-new honesty line planted in the wave receipt | 4 failed | PIN-1 (all cells that render it) |

The **round-7 grow-enum** case is the load-bearing checked-variable proof: growing `LegQualification`
grows `_leg_qual_combos` and the live product together (so `test_summary_verdict_combination_surface_equals_the_live_product`
stays green — the meta-recursion working), while **only** PIN-2's coverage
(`leg_anchor_names == set(LegQualification.__members__)`) reddens — a new member without a byte-anchor
cannot pass. That is the recurrence-ender: the anchored honesty-line SET is DERIVED and CHECKED, not a
hand-named subset.

The **D1a-reword** case also shows PIN-1 catches what the pre-existing containment pin cannot:
`test_render_currency_fail_uses_the_fixed_verdict_and_preserves_reasons` stayed GREEN under the reword
(its `"ruff" in line` check still held) — exactly the honesty-content gap PIN-1 closes.

## 4. How each survivor — and round 7 — dies BY CONSTRUCTION (§11.9.4)

- **D2c (W-SCOPED-OVERCLAIM):** the scoped-leg line is a byte-anchored catalog line; a reworded
  `nothing owed` ≠ the anchored `NOT a currency clear; full run owed` → PIN-1 (whole wave PASS_SCOPED
  receipt) AND PIN-2 (the SCOPED leg anchor, verified through the real seam) redden. The pin never asks
  "does it read as a clear" (R1's trap) — it asks "is it the anchored bytes." **Dies (measured, §3).**
- **D1a (wave FAIL-detail):** anchored over the FAIL state in PIN-1 — the detail FRAMING is
  `_detail_golden` (byte-exact) and any extra line is a byte mismatch. **Dies (measured, both shapes, §3).**
- **A round-7 honesty line (the next neighbour):** any new/reworded line ≠ golden → PIN-1 reddens,
  forcing a REVIEWED golden update where the prose is read (the honest bound). No SILENT over-claim.
  **Dies (measured, §3).** The recurrence ends because the read-zone is the WHOLE receipt over the
  DERIVED domain, not the next single line someone remembers to anchor.
- **R1 (partial enumeration of the read-zone):** DISSOLVED — there is no hand-named honesty subset; the
  read-zone is every line over the derived state domain, and the derivation (enum domains + the cell set)
  is a checked variable (PIN-1 coverage + PIN-2 coverage). **No honesty-subset left to enumerate wrong.**

## 5. Deviations + forks (disclosed; brief-base §2 — both readings written)

1. **"Extend the existing byte-oracle" — reading chosen: reuse the IDIOM via a shared golden builder;
   did NOT refactor the existing checkpoint test in place.** PIN-1 anchors the `build_wave_receipt`
   path in BOTH modes via `_expected_receipt_lines` (which reuses the checkpoint oracle's construction:
   `GateCurrency.render()` legs, the fixed note, the roster format). The pre-existing
   `test_checkpoint_receipt_preserves_the_historical_bytes` is LEFT intact — it anchors a DIFFERENT
   production path (`_render_currency`, historical header), which `build_wave_receipt` (bundle header
   recording the mode) legitimately cannot produce. **Alternative reading:** fold that test into
   `_expected_receipt_lines` via a `header` parameter so there is one golden builder for all paths.
   **I picked reuse-the-idiom over refactor-the-passing-test** (lower risk to a delta-verified,
   load-bearing pin; the golden POLICY is centralised, only the small historical-header assertion stays
   separate). If the lead prefers strict single-builder unification, it is a one-helper follow-up. Not a
   blocker either way.
2. **The "wave FAIL-detail catalog constant" (brief phrasing) is anchored by PIN-1 + the summary
   sole-mint, NOT minted as a separate NEW wave-only constant — deliberately, for DRY.** Ground truth:
   the FAIL detail's framing (`RED with nobody's name on it: {ids}`) is SHARED between checkpoint and
   wave (both route through `compose_wave_receipt`); the FAIL honesty VERDICT is `render_summary(FAIL)`,
   already sole-minted in the seam. Minting a wave-ONLY FAIL-detail constant would DUPLICATE the shared
   reasons framing — the opposite of DRY #1. So the wave FAIL-detail is anchored by CONTENT (PIN-1
   byte-oracle over the FAIL state, proven to catch both an extra line and a reworded framing, §3) +
   `render_summary(FAIL)` kept out of `wave_gate.py` by `test_wave_summary_strings_are_not_authored_in_wave_gate`.
   `_SCOPED_HONESTY` IS the one genuinely-new wave honesty constant and IS pinned sole-source. **This is
   the DRY-correct reading; flagging it because the brief's parenthetical implied two new constants.**

Neither deviation weakens the closure of D2c/D1a/round-7 (all measured RED, §3). No operator ruling is
required; both are recommendations the lead can accept or ask me to change.

## 6. Reused instruments (verbatim shapes — brief-base §1)

**`build_reference.py`** (scratch, disposable) — appends the seam to pcg + routes `_render_currency` +
writes `wave_gate.py`. Load-bearing seam shape (independent reference, adopts delta-g-4 §9 + fork-1 detail):
```python
class LegQualification(Enum): CLEAN/OWNED/SCOPED/FAILING
class SummaryVerdict(Enum):   PASS_FULL/PASS_SCOPED/FAIL
class SummaryLine(str): __slots__=()
_SUMMARY_LINES = {PASS_FULL:"CURRENCY   : PASS — every claimed gate is GREEN or OWNED",  # byte-exact historical
                  PASS_SCOPED:"WAVE       : PASS — core is GREEN-or-owned; pytest ran SCOPED, full run still owed",
                  FAIL:"CURRENCY   : FAIL — a claimed gate is RED with nobody's name on it, or was never run"}
def summary_verdict(qs): FAIL if any FAILING else PASS_SCOPED if any SCOPED else PASS_FULL
def render_summary(v): return SummaryLine(_SUMMARY_LINES[v])            # SOLE minter
def _leg_qualification_for(verdict,*,scoped): SCOPED / FAILING / OWNED(RED_ADJUDICATED) / CLEAN
_SCOPED_HONESTY = "NOT a currency clear; full run owed"                 # the D2c line, ONE source
ReceiptHeader(lines).render()->list(lines)
RosterLine(manifest).render()->["  manifest   : {ids} ({n} gates)"]
GateLeg(currency, scoped_line).render()->[scoped_line or currency.render(), *["      ORPHAN: {o}" ...]]
DetailLines(lines).render()->list(lines)                               # () on PASS
WaveReceipt(header,roster,legs,detail,summary,note,verdict); .ok = verdict is not FAIL
   .render()->[*header.render(), *roster.render(), *(l for leg in legs for l in leg.render()),
               *detail.render(), str(summary), note]
compose_wave_receipt(gate, manifest, results, *, header, scoped_selector)  # THE one composition, both paths
   scoped = scoped_selector is not None and READERS[reader] is JUnitReportReader and currency.ok
   scoped_line = f"  {id:<12} SCOPED({scoped_selector}) — {_SCOPED_HONESTY}"
   detail: "  RED with nobody's name on it: {orphaned}" / "  claimed but never run: {unrun}"  # fork-1
_render_currency(...) = compose_wave_receipt(..., header=ReceiptHeader(("GATE CURRENCY — …",)), scoped_selector=None).render(), .ok
# wave_gate.py: MODE_WAVE/MODE_CHECKPOINT; pytest_args_for; build_wave_receipt(header=ReceiptHeader((f"GATE BUNDLE [{mode}] — scope: {scope}",)),
#   scoped_selector=" ".join(sel) if wave else None); render_wave_receipt=build.render(),ok;
#   main: argparse required mutually-exclusive --wave|--checkpoint + parse_known_args selector;
#         GateManifest.load/PendingContractRegistry.load; _run_selected_gates(runner, manifest, list(manifest.ids), pytest_args);
#         render_wave_receipt(...); print; return 0 if ok else 1
```
**`discriminate.py`** (scratch) — restores pristine between mutations; each mutation = a one-line patch of
the reference; asserts the designated pins redden (§3 table) + positive control 178/0. The 5 mutations:
D2c (`_SCOPED_HONESTY` reword), D1a-extra (extra detail line), D1a-reword (framing reword, run separately
§3), round-7 grow-enum (`LegQualification.PARTIAL` with no anchor), round-7 new-line (extra header line).

**Reused, not invented:** `test_checkpoint_receipt_preserves_the_historical_bytes` (byte-oracle idiom,
EXTENDED) · `_leg_qual_combos` + `test_summary_verdict_combination_surface_equals_the_live_product`
(meta-recursion) · `test_render_summary_*` (per-component byte anchor, extended to PASS_SCOPED/FAIL) ·
`_string_literal_lines_containing` (`TestSafeLineRenderedMintPin` idiom, already self-tested — no new
detector) · `GateCurrency.render()` (the shared leg render, the byte oracle).

## 7. Scratch disposition
Provenance-asserted scratch at `/home/ejprice/scratch-reviser-g-5` (a `scratch_copy.sh` copy, NOT a git
worktree — disposable by design). Contains the reference + `build_reference.py` + `discriminate.py`.
Safe to `rm -rf` once the lead has (optionally) re-run the receipts; I left it in place for that.
