brief-base v10 read
brief project v7 read

# REPORT-reviser-g-6 — apply design §11.10 (TERMINAL) to the G contract (`scripts/test_wave_gate.py`, #344)

## SUMMARY BLOCK
- **State: done.** §11.10 applied — main's SERVED BYTES (both streams) anchored over the COMPLETE
  derived outcome domain, the closed `VERDICT_*` set. CONTRACT TESTS ONLY; only `scripts/test_wave_gate.py`
  edited. §11/§11.8/§11.9 + MP-1..8 pins KEPT (§11.9 render-return oracle retained as failure-localizer,
  subsumed not deleted).
- **What landed (9 new pins, §11.10 section):** MP-A `test_omitted_gate_NOT_RUN_receipt_is_byte_anchored`
  (whole-receipt byte-oracle over the closed VERDICT_* domain — closes F1's NOT_RUN body/detail/orphan);
  MP-B `test_main_served_output_equals_the_honest_render_over_the_complete_outcome_domain` (capfd BOTH
  streams: stdout==render, stderr=="" — closes F2 stdout AND the round-8 stderr door); the round-8 guard —
  leg-1 verdict-domain coverage (meta-recursion re-keyed on `GATE_OUTCOME_VERDICTS`) + leg-2
  branch-coverage (P-S `coverage.Coverage(branch=True)`, method set DERIVED from the receipt); a per-verdict
  leg component anchor (closes R7a); the `GATE_OUTCOME_VERDICTS` closed-set source pin; 3 non-vacuity/self-tests.
- **Deviations (5, all stated in the instruments — none a silent narrowing):** (D1) leg-2 targets the DERIVED
  render-method set (`GateCurrency.render` + `WaveReceipt.render` + typed components' `render`), NOT the
  composer — P-S division, honest bound stated; (D2) leg-2 drives `render_wave_receipt` (main's stdout render
  path), not the CLI `main` fn (main's own branches ride MP-1/MP-6/MP-B); (D3) MP-B drives the COMPLETE
  VERDICT_* domain incl RED_ADJUDICATED-through-`main` (owning registry + self-destruct neutralisation) —
  resolves the "extend the red-cell harness" vs "complete domain" ambiguity toward the stronger reading;
  (D4) the NOT_RUN orphan is byte-anchored to PRODUCTION's exact prose (removed-behavior faithful) — the
  builder's shared composition MUST preserve it; (D5) extended the §11.9 helper `_expected_receipt_lines`
  with a NOT_RUN branch (one whole-receipt golden builder — DRY; PIN-1 unaffected, its cells never hit it).
- **Packages considered:** none new — stdlib `ast`/`inspect`/`enum` + pytest `capfd`/`monkeypatch` +
  `coverage` (already used by §11's P-S). Reused in-repo idioms: `_build_receipt`/`_expected_receipt_lines`/
  `_canonical_leg_currency`/`_leg_golden` · `_patch_loaders`/`_install_reader_spy`/`_install_render_capture` ·
  the meta-recursion coverage idiom · the P-S `coverage.Coverage(branch=True)` idiom · the
  `test_pending_contract_gate.py` registry-fixture pattern (owning gate). Verdict: **bespoke-minimal,
  extending existing harnesses** — no new machinery, NO forbidden-shape/marker scan.
- **Graded:** `4ceac32` · HEAD-at-report `4ceac32` · SAME. (§11.10 committed at `481b1c1`, unchanged through
  `4ceac32` — the HEAD advance was a §12.8 A-SUB DOCS commit that touched none of my files.)
- **Decisions-needed:** none blocking. One builder note (below): the builder must expose
  `pending_contract_gate.GATE_OUTCOME_VERDICTS` and preserve production's NOT_RUN orphan prose.
- **Receipt pointers:** §11.10 section `scripts/test_wave_gate.py` (starts at the `# 11. §11.10 — TERMINAL`
  banner) · satisfiability + mutation table §"Satisfiability" below · reference deltas + discriminate.py
  §"Instruments" below (scratch is disposable — pasted here).

---

## 1. Capability check
Brief satisfiable with my toolset: lore tools loaded (`ToolSearch "+lore"`), Read/Edit/Write, Bash (`uv run`
pytest/mypy/ruff), `scratch_copy.sh`. No impossibility. lore-first used for currency/orientation; grep used
for symbol/line location within the two files under contract (a legitimate cross-cutting map over ONE file's
own structure) — said out loud, no friction filed (grep here is not routing around a lore weakness).

## 2. What §11.10 fixes (the two delta-adversary-g-5 breaks, closed)
Design §11.10 (my spec, VERBATIM) and `REPORT-delta-adversary-g-5` name two wrong builds that survived the
§11.9 contract 178/0 — the two together are WHY G recurred:
- **F1 (quantifier law):** §11.9's byte-oracle domain was `SummaryVerdict.__members__` (3), but a verdict has
  ≥2 receipt SHAPES — `FAIL` renders differently for RED_ORPHANED vs NOT_RUN, and NOT_RUN (the literal #344
  omitted-gate event) was byte-anchored by NOTHING. R7a (NOT_RUN body), R7b (`claimed but never run` detail),
  R7c (NOT_RUN orphan) survived 178/0.
- **F2 (recipe vs cake, #131/#107):** every honesty pin reached `render_wave_receipt`'s RETURN (a proxy); the
  SERVED surface is `main`'s STDOUT. `main` could `print("all gates are clean, tree is green")` on an exit-0
  PASS_SCOPED receipt (alt-wording evading marker/summary/append scans, `print` ≠ `.append`) — surviving 178/0.

## 3. The pins (design §11.10.3 + the round-8 guard §11.10.2), by mechanism

**Domain source (F1) — `test_gate_outcome_verdicts_is_the_closed_verdict_set`:** pins the builder's
`GATE_OUTCOME_VERDICTS` == the closed `{VERDICT_GREEN, VERDICT_RED_ADJUDICATED, VERDICT_RED_ORPHANED,
VERDICT_NOT_RUN}` (both directions, from the statically-imported constants). The byte-anchor domain is DERIVED
from this — NEVER `SummaryVerdict.__members__` (the 3-value under-derivation that IS F1). A new `VERDICT_*` →
this reddens (domain source stale). The domain source is itself a checked variable.

**MP-A — `test_omitted_gate_NOT_RUN_receipt_is_byte_anchored`:** the WHOLE rendered receipt byte-exact vs the
audited honest golden (`_expected_receipt_lines`) for EACH cell in mode × `GATE_OUTCOME_VERDICTS` — crucially
the NOT_RUN (omitted-gate) shape §11.9 never produced. The three honesty lines that were pinned by nothing are
anchored to INDEPENDENT goldens (never re-derived from the receipt, so a mutation drifts rather than moving
with it): NOT_RUN body (`_leg_golden_by_verdict`), `claimed but never run` detail (`_detail_golden`), NOT_RUN
orphan (`_notrun_orphan_golden_lines`). Non-vacuity control `test_mp_a_actually_produces_the_notrun_shape`
(the domain must PRODUCE a NOT_RUN leg — the §11.9 blind spot — carrying exactly one #312 orphan).

**Per-verdict LEG component anchor — `test_every_gate_verdict_leg_render_is_byte_anchored_over_the_closed_verdict_domain`:**
re-keys §11.9's LegQualification-keyed PIN-2 leg anchor onto the FINER `VERDICT_*` set (which distinguishes
NOT_RUN from RED_ORPHANED — the shape §11.9 collapsed), so `GateCurrency.render()` for NOT_RUN is anchored to
an independent golden (R7a's exact closure) — and the anchored set == the live domain (leg-1 at the component
level). Reuses `_canonical_leg_currency`/`_leg_golden` for the three shared verdicts.

**LEG 1 (verdict-domain coverage) — `test_byte_oracle_domain_covers_the_closed_verdict_set`:** the per-gate
verdicts the domain PRODUCES == the live `GATE_OUTCOME_VERDICTS`, both directions — the §11 meta-recursion
re-keyed from the 3-value `SummaryVerdict` to the 4-value closed set (the receipt-CONTENT space, F1's fix).
A verdict shape with no producing cell escapes exactly as NOT_RUN did → reddens.

**LEG 2 (branch-coverage backstop) — `test_render_path_has_no_unexercised_branch_over_the_complete_outcome_domain`:**
drives the render path over the complete domain under `coverage.Coverage(branch=True)` (the §11 P-S idiom:
`cov.start()`/drive/`cov.stop()`/`cov._analyze`), asserting NO un-run line/branch in any receipt render method.
The method set is DERIVED from a built receipt's own component structure (`GateCurrency.render` +
`type(receipt).render` + each `type(component).render`) — a checked variable, not a hand-list; a new typed
component's render joins it automatically. Body spans (not the `def` line) via `ast` — the P-S
`_method_body_spans` idiom (the `def`/decorator lines execute at import, before the measured region). Catches a
NEW render SHAPE that is not a new verdict (F1's class): had this existed for §11.9's RED_ORPHANED-only domain,
`GateCurrency.render`'s NOT_RUN branch would have shown un-run → F1 caught at build time. Self-test
`test_render_path_derives_the_render_methods_from_the_receipt` + an anti-vacuity leg (GateCurrency.render was
actually executed).

**MP-B — `test_main_served_output_equals_the_honest_render_over_the_complete_outcome_domain`:** drives the REAL
`main` over the complete domain (SAME checked domain as the exit code), `capfd` BOTH streams, and asserts
`stdout == "\n".join(render lines) + "\n"` (the exact render main produced — recipe→cake), `stderr == ""`, and
`(code == 0) == ok`. A banner `print`ed around the render → stdout ≠ render → RED; a `print(over-claim,
file=sys.stderr)` on the exit-0 path → stderr ≠ "" → RED. Extends the existing main-exit harness
(`_patch_loaders`/`_install_reader_spy` + a line-capturing `_install_render_output_capture` mirroring
`_install_render_capture`). Non-vacuity `test_mp_b_domain_drives_every_closed_verdict_through_main` (every
closed leg-verdict + every summary state incl. PASS_SCOPED — the exact exit-0 false-clear surface — reached).

## 4. How F1, F2, round-8, and every prior round die BY CONSTRUCTION — MEASURED (both-way mutation proofs)
Independent reference (delta-adversary-g-5's `build_reference.py` + my 3 deltas; §Instruments) driven by
`discriminate.py`; positive control = pristine **187 passed / 0 failed**; every wrong build ABORTS if its
search string is not found (a mutation cannot silently no-op).

| wrong build | result | reddened at (right reason) |
|---|---|---|
| **R7a-notrun-body** (NOT_RUN body → "assumed current and clean") | 185p/2f DIES | per-verdict leg anchor + MP-A |
| **R7b-unrun-detail** ("claimed but never run" → "gates verified current") | 186p/1f DIES | MP-A |
| **R7c-notrun-orphan** (NOT_RUN orphan → "gate ran and is current and clean") | 186p/1f DIES | MP-A |
| **W-main-print-banner** (stdout over-claim on exit-0 receipt) | 186p/1f DIES | MP-B |
| **W-main-print-stderr** (over-claim to STDERR on exit-0 path) | 186p/1f DIES | MP-B (the round-8 door) |
| **new-verdict-domain** (a new `VERDICT_*` w/o a golden) | 180p/7f DIES | leg-1 (source pin + coverage) |
| **new-render-branch** (a render branch no cell reaches) | 186p/1f DIES | leg-2 |
| **R-adjudicated-body** (RED_ADJUDICATED body reword) | 185p/2f DIES | per-verdict anchor + §11.9 PIN-2 |
| D2c / D1a-reword / D1a-extra / W-EXTRA-wrapper / W-EXTRA-receipt / orphan-slot / summary-alt-in-wave / grow-enum | all DIE | prior §11.5/§11.8/§11.9 pins (unbroken) — MP-A/MP-B also catch several (subsumption) |

`discriminate.py` verdict: **RESULT: ALL OK** (every mutation DIES for the right reason; none SURVIVES; none BROKEN).

## 5. Satisfiability, non-regression, RED honesty, gates
- **C-DEF satisfiability:** full contract vs the INDEPENDENT reference → **187 passed / 0 failed**
  (178 prior + 9 new).
- **Extraction non-regression:** `test_pending_contract_gate.py` → **41 passed / 0 failed** against the
  reference (the shared-composition extraction, incl. the production-faithful NOT_RUN orphan).
- **RED honesty (real repo, wave_gate absent):** `--collect-only` → `ImportError ... wave_gate` at
  `scripts/test_wave_gate.py:154` — RED for the RIGHT reason (the module-under-contract does not yet exist).
- **Gates on the contract file:** `ruff check scripts/test_wave_gate.py` → **All checks passed!**;
  `MYPYPATH=scripts uv run mypy scripts/test_wave_gate.py` → **Success, 0 issues** (the canonical
  scripts-imports-scripts invocation; a bare standalone `mypy` reports the SAME 27→ `no-any-unimported`
  artifacts at HEAD, resolved by `MYPYPATH=scripts` exactly as `typecheck.sh` does).
- **Provenance (#140):** `wave_gate.__file__` / `pending_contract_gate.__file__` / `loremaster.__file__` all
  resolve INSIDE `/home/ejprice/scratch-reviser-g-6/` (asserted; provenance-asserted `scratch_copy.sh`).

## 6. Builder note (NOT a scope fork — the brief pre-assigned this to the builder)
The contract references and PINS `pending_contract_gate.GATE_OUTCOME_VERDICTS` — the builder must expose that
one-line closed-verdict tuple beside the existing `VERDICT_*`/`FAILING_VERDICTS` (design §11.10.5; brief:
"the `GATE_OUTCOME_VERDICTS` constant + pcg extraction is the builder's; you PIN/reference it"). The shared
composition must (removed-behavior faithful, D4) construct the NOT_RUN currency's orphan with production's
exact `_render_currency` prose ("gate {id!r} is CLAIMED by the manifest and was NOT RUN — a claimed-but-unrun
gate is finding #312 exactly. This says NOTHING about whether it would pass.") — MP-A anchors it byte-exact.

## 7. Honest bound (stated, not glossed — §6 / trust doctrine)
LEG 2's DERIVED method set is the receipt RENDER methods (the line-emitting surface). The COMPOSER (which
builds the typed currencies + scoped/detail/orphan strings) is data-prep whose OUTPUT is byte-anchored by MP-A
over the COMPLETE domain — the P-S division (branch-cover the renders, byte-check the content). Every composer
branch keyed on the domain axes (mode × VERDICT_* × scoped) is reached by the complete domain and byte-anchored;
a composer branch keyed on a NOVEL axis is the named residual (re-open trigger: a composer conditional on a new
axis → add that axis to the domain). Stated in the leg-2 docstring + the §11.10 section header. Same honest
boundary §11.9.5 carries: the byte-oracle pins CONSISTENCY WITH AN AUDITED GOLDEN (this author's read of the
NOT_RUN prose, once), not semantic honesty in the abstract; drift from that golden reddens.

## 8. Instruments (brief-base §1 — scratch is disposable, so the load-bearing pieces are pasted here)
Reference = delta-adversary-g-5's `build_reference.py` (its shape is in `REPORT-delta-adversary-g-5.md` §10)
with THREE deltas making it a CORRECT build against the §11.10 contract:
1. add module constant in the SEAM:
   `GATE_OUTCOME_VERDICTS = (VERDICT_GREEN, VERDICT_RED_ADJUDICATED, VERDICT_RED_ORPHANED, VERDICT_NOT_RUN)`
2. in `compose_wave_receipt`, the NOT_RUN currency's orphan becomes production's exact prose:
   `orphans=(f"gate {spec.id!r} is CLAIMED by the manifest and was NOT RUN — a claimed-but-unrun gate is finding #312 exactly. This says NOTHING about whether it would pass.",)`
3. four new `MUTATIONS` entries — `W-main-print-banner`, `W-main-print-stderr` (insert a `print(...)` /
   `print(..., file=sys.stderr)` before `return 0 if ok else 1` in the WAVE blob), `new-verdict-domain`
   (append `"VERDICT_PHANTOM"` to `GATE_OUTCOME_VERDICTS` in the SEAM), `new-render-branch` (prepend an
   unreachable `if self.gate_id == "____phantom_gate____": return ...` branch to `GateCurrency.render` in BASE)
   — plus the belt `R-adjudicated-body`.

`discriminate.py`: restores pristine pcg → `build_reference.py --mutate X` → runs the FULL contract under
`uv run pytest` → parses passed/failed + `FAILED` ids → verdict DIES(right reason)/SURVIVES/BROKEN, keyed to
a per-mutation expected-reddened-substring map; asserts the pristine control is exactly `(187, 0)` and treats a
collection-errored run as BROKEN (never a false SURVIVES — the P0 self-catch lesson). Scratch (disposable,
provenance-asserted): `/home/ejprice/scratch-reviser-g-6/` (`build_reference.py`, `discriminate.py`) — flag to
operator: keep or discard at close-out; the reconstruction above is self-contained.

## 9. Scope + coordination
- Edited ONLY `scripts/test_wave_gate.py` (the granted writable set). No production/implementation code touched
  (the `GATE_OUTCOME_VERDICTS` constant + pcg extraction are the builder's — I only reference/PIN them). No git
  state mutated (lead commits).
- Concurrent sibling delta-adversary-asub-5 is read-only per the brief; no contention.
- No unrelated test failures encountered in my scoped runs.
