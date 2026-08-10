# REPORT — builder-scriptsgate (Opus BUILDER, session 2026-08-09-fix-344-345)

brief-base v10 read
brief project v7 read

## SUMMARY
- **state: done.** Four RED contracts GREENED (G/#344 simple wave-gate · D/#295 refusal-effect
  helper + R16 reach · E/#289 trailing-newline matrix · H/#290 baseline anti-vacuity), minimal
  code, no adversary (per §13/operator). Cold audit follows.
- **RED→GREEN:** G `test_wave_gate` collection-ERROR (ModuleNotFoundError, all 29 errored at
  collection) → **29 passed** · D `test_refusal_observes_effect` 7f/1p → **8 passed** (+
  `test_wire_discipline` **8 passed**, now scanning `_refusal_effect.py`) · E
  `test_trailing_newline_matrix` 6f/3p → **9 passed** · H `test_harness_guards` 6f/2p → **8
  passed** · `test_wrong_builds` (E WB22 lands + H sharing) 3f/1p → **4 passed**.
- **Non-regression (pcg `_currencies_for` extraction):** `test_pending_contract_gate` **41
  passed**, `test_gate_currency` **21 passed** — the two consumers of the currency machinery.
  Final consolidated run: **128 passed, 0 failed**.
- deviations: (1) pcg MINIMAL change = extracted `_currencies_for` from `_render_currency` (byte-
  identical output; both consumers green) so wave_gate gets STRUCTURED verdicts for the SCOPED
  override. (2) R16 reach extended via a role-named `REFUSAL_EFFECT_HELPER_MODULE_NAMES` set
  unioned into `posture_modules()` BY EXISTENCE — this slightly widens `posture_modules()` to
  cover a non-glob module (the reviser-cd BUILDER-NOTE demonstrated form). (3) `refuse_vacuous_
  baseline` raises `SystemExit` (contract-eh Fork 1, pinned).
- **Packages considered:** none — the mechanisms are stdlib predicates (a dict→variants generator;
  a zero-count refusal; an effect-observing assertion helper) + in-process COMPOSITION of existing
  `pending_contract_gate` machinery. Read: `pending_contract_gate.py` (`_run_selected_gates`,
  `_currencies_for`/`_render_currency`, `GateManifest`/`PendingContractRegistry.load`),
  `_auth_fixtures.WireSession.call`, `test_wire_discipline.posture_modules`. No library replaces a
  two-line predicate, a manifest-derived gate bundle, or a wire-effect refusal assertion.
- **Graded:** 003a337 · HEAD-at-report: 003a337 · SAME. (One verdict on others' artifacts: the
  loremaster typecheck bound below.)
- decisions-needed: **none.** Fork resolutions consumed as ruled (E home `scripts/_newline_matrix`,
  H `SystemExit`, D R4 form). Sibling-owned follow-ups (packet 39 posture pins consuming the D
  helper; structural registration-gating) are out of my scope, unchanged.
- receipt POINTERS: §G · §D · §E · §H · §Gates · §Flags. RED baselines + GREEN counts in §Verify.

---

## §G — #344 non-omittable gate bundle (SIMPLE design §13)

**New:** `scripts/wave_gate.py` — `main(argv=None) -> int`, the one mandated public name (§13
retires the §11.8–§11.11 typed-WaveReceipt / conduit / branch-coverage / byte-oracle fortress).

Behaviour, all four pinned:
- **B1 no `--wave` → FULL.** legs = `manifest.ids` (FULL core), `pytest_args = ()`. Routes through
  `pcg._run_selected_gates` exactly ONCE (spy records 1 call — W1 killed).
- **B2 `--wave <sel…>` → core FULL + pytest scoped + honest flag.** legs = `manifest.ids` (core
  never scoped — W2 killed), `pytest_args = tuple(sel)` VERBATIM (no `-k`). The pytest gate's GREEN
  currency verdict RENDERS **SCOPED, never GREEN** (`_scoped_pytest_line`), and a `"SCOPED RUN —
  ran {args} ({N} tests); does NOT certify the full gate"` banner echoes the exact args + the
  collected count. Pass/fail is UNCHANGED by the render (a scoped GREEN still exits 0; a scoped
  RED_ORPHANED still fails — honesty is in the render, not the exit).
- **B3 `--wave` no args → ERROR.** `nargs="+"` → argparse SystemExit(2).
- **B4 `--wave <sel>` zero-collection → ERROR.** `BrokenInstrumentError` from the leg-runner is
  NOT swallowed (caught → return 2); the run is attempted first (spy records the call).
- **W8 removed `--checkpoint` → ERROR.** No such argument → argparse SystemExit(2).

**DRY / non-omittable core (priority #1):** wave_gate NAMES NO GATES. `_scopable_gate_id` DERIVES
the pytest gate as the sole `JUnitReportReader` gate (not a hardcoded `"pytest"`); legs come from
`manifest.ids`; a 4th manifest gate reaches the runner (W3 behavioral pin green). No literal gate-id
collection (W3 AST pin), no second `yaml` reader (W4 AST pin) — verified by the contract's own
scans. pcg change is the MINIMAL extraction of `_currencies_for` (see §Deviations), giving the
wrapper structured access to the pytest verdict for the SCOPED-not-GREEN override — the one reason
§13/contract-g-simple call for in-process composition over a stdout-parsing wrapper.

**Real-composition smoke** (cheap; no gate subprocess): real `gates.yaml` → ids
`('typecheck','ruff','pytest')`; `_scopable_gate_id` → `pytest`; empty results → all `NOT_RUN`,
`_render(wave=True)` → `ok=False` + SCOPED-RUN flag present. Proves the real manifest/registry
wiring, not just the canned contract.

## §D — #295 refusal pins observe the EFFECT (auth-independent half)

**New:** `loremaster/tests/_refusal_effect.py`:
- `assert_tool_refused_and_did_not_run(call, tool_name, args, *, effect_count, refusal_marker)` —
  drives the REAL wire via `await call(...)` (handed ONLY the boundary callable — the D-WB2 in-
  process `wire.mcp.call_tool` door is unrepresentable, R4); WEAK leg `refusal_marker in body`;
  STRONG leg `effect_count() == 0` with a message that NAMES the effect (so the WB48 run-then-refuse
  build fails on the EFFECT leg, not the proxy). Returns the body.
- `assert_sweep_reached_every_refusal_pin(derived, observed)` — fail-closed on empty `derived`
  (anti-vacuity), RED naming any un-swept derived pin (coverage as a checked variable).

**R16 reach (builder leg):** `test_wire_discipline.posture_modules()` extended — a role-named
`REFUSAL_EFFECT_HELPER_MODULE_NAMES = {"_refusal_effect.py"}` unioned in BY EXISTENCE — so R16's
receiver-blind AST scan now governs `_refusal_effect.py` (a SECOND, independent closure of the D-WB2
door, and governs packet 39's future consumers). My helper uses `await call(...)` (a Name call, not
`.call_tool`), so the receiver-blind scan does NOT false-flag it — `test_no_posture_assertion_
calls_a_handler_in_process[_refusal_effect.py]` green.

**R-N1 fix:** the R4 pin docstring in `test_refusal_observes_effect.py` no longer claims the door is
closed "by construction" — it now states the `call.__self__.mcp` back-door is closed by the R16
scan leg, not by R4's `hasattr(call,"mcp")` check (reviser-cd R1); the two legs together cover it.

## §E — #289 trailing-newline malformed-input matrix

**New:** `scripts/_newline_matrix.py::newline_forgery_variants(base, interpolated_fields)` — one
`(field, kwargs)` variant per declared field, differing from `base` only by a trailing `\n` on that
field. Fresh dicts (no base mutation); **ValueError** on an empty field list (anti-vacuity on the
matrix itself — #290 lesson) and on a field absent from `base` (a silent skip leaves that field with
no `\n` case). The field-CLASSIFICATION (which fields are bare doors vs `!r`-safe) stays the residual
judgement the design's honest bound names — the helper only makes a forgotten case impossible.

**Killed wrong build:** `scripts/wrong_builds.py::WB22_finding_number_validated_with_match` —
`if not _FINDING_NUMBER.fullmatch(self.finding):` → `.match(...)`. Lands exactly once against
`gated_ground.py` and parses (`TestTheCommittedWrongBuildsCanActuallyRun` green); killed by the
matrix's construction + integration pins.

## §H — #290 anti-vacuity on a comparison's baseline (SHARED guard)

**New:** `scripts/_harness_guards.py::refuse_vacuous_baseline(measured_count, *, cause_hint,
interpreter)` — raises `SystemExit` (behaviour-preserving, contract-eh Fork 1) on
`measured_count == 0`, NAMING the interpreter + cause_hint; returns None otherwise (1 IS a real
measurement — keyed on `== 0`, not `< 2`).

**Sharing wired in `wrong_builds.py`:** the inline `if not baseline: raise SystemExit(...)` is
REPLACED by an UNCONDITIONAL `refuse_vacuous_baseline(baseline, cause_hint=…, interpreter=sys.
executable)` (imported top-level). The unconditional form is what the reviser-fh spy pin forces (the
315 leg would never route a half-extracted `if not baseline:` copy), and removing the inline guard
clears the anti-dup AST scan — `test_wrong_builds` 4 passed (was 3f/1p, both spy legs + the offender
scan).

---

## §Verify — RED→GREEN receipts (at 003a337, `-p no:randomly`)

| contract | RED baseline | GREEN |
|---|---|---|
| G `scripts/test_wave_gate.py` | collection ERROR — `ModuleNotFoundError: wave_gate` (all error) | **29 passed** |
| D `loremaster/tests/test_refusal_observes_effect.py` | 7 failed, 1 passed | **8 passed** |
| D `loremaster/tests/test_wire_discipline.py` (R16) | (green) | **8 passed** (now scanning `_refusal_effect.py`) |
| E `scripts/test_trailing_newline_matrix.py` | 6 failed, 3 passed | **9 passed** |
| H `scripts/test_harness_guards.py` | 6 failed, 2 passed | **8 passed** |
| E+H `scripts/test_wrong_builds.py` | 3 failed, 1 passed | **4 passed** |
| non-reg `scripts/test_pending_contract_gate.py` | (green) | **41 passed** |
| non-reg `scripts/test_gate_currency.py` | (green) | **21 passed** |

Consolidated (all above): **128 passed, 0 failed** in 1.38s.

## §Gates (my touched files)
- **ruff** `uv run ruff check <all 8 touched files>` → `All checks passed!`
- **mypy scripts leg** `MYPYPATH=scripts uv run mypy scripts` → `Success: no issues found in 42
  source files` (after `Mapping[str, object]` covariance fix on `_render` + import-order autofix on
  wave_gate.py).
- **mypy loremaster leg** `uv run mypy loremaster` → my 3 D files (`_refusal_effect.py`,
  `test_wire_discipline.py`, `test_refusal_observes_effect.py`) are CLEAN (absent from the error
  set). Total 102 errors in 8 files, ALL packet-39 auth files (see §Flags) — my D helper REDUCED
  the count by ~8 (resolved `test_refusal_observes_effect`'s missing-symbol errors).

## §Flags (scope law — surfaced, not fixed)
1. **Pre-existing loremaster typecheck bound (NOT mine).** `uv run mypy loremaster` = 102 errors in
   8 files, all packet-39 auth (`test_auth`, `test_auth_composition`, `test_google_token_verifier`,
   `test_hosted_readonly_posture`, `test_permission_resolver_seam`, `test_allowlist_roster`,
   `test_auth_identity_seam`, `_auth_fixtures`). This is the #296-held / packet-39 designed-RED
   bound documented in `pending_contract_gate.py` — pre-existing, outside my writable set, and my
   change only shrank it. Flagged per the "don't handwave unrelated failures" rule.
2. **Concurrent sibling footprint in the shared tree.** `git status` shows tracked modifications to
   `server.py`, `test_mcp_server.py`, `test_link5_render_containment.py`,
   `test_comms_promise_registry.py`, `test_render_slot_inventory.py` — the concurrent `builder-
   server`'s work on DISJOINT files (INSTRUMENT B/C/#337), NOT mine. My footprint is EXACTLY the
   writable set (4 new files + 4 tracked edits, diffstat `93 insertions / 24 deletions`).
3. **reviser-fh scratch dir** `/home/ejprice/scratch-reviser-fh` remains (its report flagged it;
   `rm -rf` was permission-denied to it). I did not touch it.

## §Standing by
Registered `builder-scriptsgate` (session `2026-08-09-fix-344-345`). Will drain lore_comms at turn
boundaries and answer follow-ups. No git state touched (lead commits). Signal sent to
lead-defect-class.
