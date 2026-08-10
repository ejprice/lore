# REPORT-reviser-cd — CONTRACT reviser, INSTRUMENTS C (#291/#347) + D (#295/#346)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK

- **state: done.** Two RED contract files revised to close the two adversary-found surviving
  wrong builds (C-WB5 / MP-2 / #347; D-WB2 / MP-1 / #346), per §9 IDIOM 1 (C) + IDIOM 2 (D).
- **C (#347), `test_mutating_set_derivation.py`:** REPLACED the single-constant liveness proof
  (reach 2/15) with a direction-agnostic **∀-mutation over EVERY `*_ANNOTATIONS` constant**
  (6, live-derived), + a meta reach pin (surface reaches every tool), + anti-vacuity + a
  probe-control. **C-WB5 CAUGHT** (was 10/10 green).
- **D (#346), `test_refusal_observes_effect.py`:** helper handed **ONLY the boundary callable**
  (R4) so `.mcp` is unrepresentable, + a pin bringing the helper's module **UNDER R16's
  wire-discipline scan**. **D-WB2 CAUGHT two independent ways.**
- deviation 1: REPLACED (not merely added) the old C single-constant liveness test — strictly
  subsumed by the ∀; keeping it is a DRY private-copy smell. No coverage lost.
- deviation 2: changed the D helper signature `(wire, …)` → `(call, …)` per the DIRECTED R4 form;
  updated its two existing call sites to hand `probe.wire.call`.
- deviation 3: went beyond the brief's "mutating-annotation surface" to **all 6 constants**
  (literal "EVERY `*_ANNOTATIONS`"; also catches the read-only-side hardcode, demo C-WB6). Flagged
  as a strengthening, not a silent scope change.
- **Packages considered:** none — the reference builds are stdlib set ops / `assert` / AST reuse;
  no library provides deny-by-default annotation partitioning, a wire-effect spy, or an AST reach
  scan. (`frozenset` return is already stdlib.)
- **Graded:** working-tree (both contracts UNTRACKED `??`) · HEAD-at-report: `962eeb6` · design §9
  graded at `962eeb6` (= HEAD; `74694dc` reuse-map is an ancestor, nothing my verdict rests on moved).
- decisions-needed: none. **BUILDER MUST** extend R16's `posture_modules()` to cover the
  effect-helper module (outside my writable set) — see §BUILDER-NOTE; else the D reach pin stays RED.
- Receipt pointers: §C-CHANGES · §D-CHANGES · §SAT (satisfiability) · §DISCRIM (wrong-build catches)
  · §REUSE (§9.6 symbols) · §BUILDER-NOTE · §RESID.

---

## §C-CHANGES — INSTRUMENT C (#291 / #347), `loremaster/tests/test_mutating_set_derivation.py`

The #347 survivor **C-WB5** derives every tool from annotations EXCEPT `lore_findings`, which it
hardcodes mutating. It passed all 10 pins because the old liveness proof flipped only
`_TASK_TOOL_ANNOTATIONS` (reach = `{lore_tasks, lore_claim_task}`, 2 of 15 tools). The fix makes the
proof's reach a CHECKED VARIABLE over the LIVE-DERIVED surface (§9.1 IDIOM 1 LEG B; meta-recursion).

Added / changed (LEG A = the existing C-9 equality pin `test_the_derivation_equals_the_spec_predicate`
is KEPT untouched):

1. **`_live_annotation_constants()`** — the LIVE surface: every `loremaster.server` global ending
   `_ANNOTATIONS` that is a `ToolAnnotations` (all 6). Derived each call, never a hand-list — the
   meta-recursion requirement (§9.1 ⚠). `_flip_to_opposite()` flips one constant's `readOnlyHint`
   to its opposite posture (direction-agnostic).
2. **`test_the_derivation_is_live_over_every_annotation_constant`** (parametrized ∀, REPLACES the
   old single-constant test): for EACH constant, flip to opposite → rebuild → assert
   `derived == spec` on the flipped surface (both partitions), with a #194 LANDING ASSERT that the
   flip moved ≥1 tool (symmetric-diff, direction-agnostic). Reuses the `_core_dropping` STRUCTURE
   (healthy baseline → landing assert → caller-reflects); mechanism is flip-hint, not drop-seam.
   **Catches C-WB5**: flipping `_FINDINGS_TOOL_ANNOTATIONS` moves `lore_findings` to read_only in
   spec, but the hardcode keeps it mutating → derived != spec → RED.
3. **`test_the_flip_surface_reaches_every_tool`** (META-RECURSION, oracle-based): union of the
   partition changes over all 6 flips must equal the FULL registered surface (15 tools). A shrunk
   surface derivation (hand-list regression, e.g. old reach 2/15) or an inline-annotated tool leaves
   a tool unreached → RED. This is the pin that reddens if a future author regresses the surface to
   a hand-list — the exact way #347 recurs. (Probe-measured this cycle: reached = 15, unreached = ∅.)
4. **`test_the_live_annotation_surface_is_not_empty_and_names_the_known_constants`** — anti-vacuity,
   mirroring R16's `test_the_handler_derivation_is_not_empty`; the surface must be non-empty and still
   name the #291/#347-receipt constants.
5. **`test_the_flip_hint_technique_discriminates_a_live_read_from_a_hardcode`** — positive control ON
   THE PROBE (CLAUDE.md "a probe needs a control"; mirrors `TestTheMutationProofDiscriminates`):
   proves the flip technique moves a live-reader and NOT a hardcode, independent of the real build.

**DRY verdict (priority #1):** the divergence risk was already closed by the C-9 equality pin
(re-derives spec each run) + the no-drift pin; the gap was liveness REACH, now the live surface. The
∀-mutation MECHANISM stays per-instrument (flip-hint), not merged into `assert_scan_reached_every_member`
— consistent with §7's over-consolidation ruling and §9.6 ("one policy per surface").

## §D-CHANGES — INSTRUMENT D (#295 / #346), `loremaster/tests/test_refusal_observes_effect.py`

The #346 survivor **D-WB2** dispatches via the in-process `wire.mcp.call_tool` handle (dead on the
wire, byte-identical to a live guard at every proxy point) and passed all 6 pins because the WIRE
claim lived only in a docstring, verified by no pin (the claim-vs-check TRUST gap). Two closures:

1. **R4 strongest form — `test_the_helper_is_handed_only_the_boundary_callable_so_the_in_process_door_is_unrepresentable`**
   (§9.2): the helper's signature is changed to receive ONLY the boundary callable
   `call` (= `WireSession.call`), never the whole session. A bound method exposes no `.mcp`, so
   `wire.mcp.call_tool(...)` cannot be written — the door is UNREPRESENTABLE, not merely pinned. The
   pin asserts `not hasattr(call, "mcp")` and drives the correct build through only the callable.
   The two existing helper tests and the `_import_effect_helper` fail-message were updated to the
   `(call, …)` signature.
2. **R16 reach — `test_the_effect_helper_module_is_within_R16_wire_discipline_reach`**: imports
   `test_wire_discipline.posture_modules()` (R16's own site-enumeration) and asserts the effect-
   helper's module is a MEMBER. R16's receiver-blind AST scan then mechanically forbids any
   `<anything>.call_tool(...)` in the helper's body. This REUSES R16 rather than cloning its scan
   (cloning would be the DRY defect this cycle exists to kill). RED until the builder extends R16's
   reach (§BUILDER-NOTE) — packet 39 consumes this helper, so the reach must hold for its callers too.

The step-1 docstring's WIRE claim is now VERIFIED by pins (the MP-1 trust gap is closed), the honesty
fork resolved toward BUILD (the auth-free spy/scan was demonstrated constructible, §9.2), not DEMOTE.
The sweep-coverage honest-bound note (`_SWEEP_ENUMERATION_MUST_BE_…`) is UNTOUCHED — D still makes no
false coverage claim (TRUST priority #2).

## §SAT — SATISFIABILITY (positive control for every probe)

Scratch: `/tmp/reviser-cd-work` via `./scripts/scratch_copy.sh` (excludes poison, `uv sync
--all-packages`, provenance ASSERTED). `uv run python -c "import loremaster; print(loremaster.__file__)"`
→ `/tmp/reviser-cd-work/loremaster/loremaster/__init__.py` (grading the scratch tree, #140).

Reference build (the intended fix, built in scratch, NOT production):
- C: `loremaster.server.partition_tools_by_posture(tools)` deny-by-default; `test_mcp_server._MUTATING_TOOLS` corrected 4→6.
- D: `_refusal_effect.py` — `(call, …)` effect helper (wire via callable, marker leg, `effect_count()==0`) + subset sweep primitive.
- R16: `test_wire_discipline.posture_modules()` extended to include `_refusal_effect.py` (the builder's leg, demonstrated).

```
$ cd /tmp/reviser-cd-work && uv run pytest \
    loremaster/tests/test_mutating_set_derivation.py \
    loremaster/tests/test_refusal_observes_effect.py \
    loremaster/tests/test_wire_discipline.py -q
..................................                                        [100%]
34 passed in 2.42s
```

Non-vacuity: the R16 negative control `test_no_posture_assertion_calls_a_handler_in_process[_refusal_effect.py]`
is GREEN on the reference — the extended scan does NOT false-flag the correct wire-driving helper
(it uses `await call(...)`, never `.call_tool`). A gate that refuses honest code gets switched off; this one doesn't.

## §DISCRIM — WRONG-BUILD RECORD (each new pin shown FIRING)

| wrong build | mutation (scratch) | result | which pin RED |
|---|---|---|---|
| **C-WB5** (#347 survivor) | derive all tools EXCEPT `lore_findings` (hardcoded mutating) | 1 failed / 17 passed | `…is_live_over_every_annotation_constant[_FINDINGS_TOOL_ANNOTATIONS]` (`only-in-derived=['lore_findings']`) |
| **C-WB6** (read-only-side, Option-B bonus) | hardcode `lore_search` read_only | 1 failed / 17 passed | `…[_READ_ONLY_ANNOTATIONS]` — the direction-agnostic ∀ catches a read-only hardcode the old/mutating-only proof would miss |
| **D-WB2** (#346 survivor) | in-process `wire.mcp.call_tool`, takes whole session | R4 pin + 2 helper tests: `AttributeError: 'function' object has no attribute 'mcp'`; R16 scan: `_refusal_effect.py:23: wire.mcp.call_tool(...)` flagged | R4 pin unrepresentable-by-construction; R16 receiver-blind scan |

Every catch paired with the reference positive control (§SAT, 34 passed). RED-at-HEAD (no
deliverables): **20 failed / 6 passed** — all 20 fail "deliverable ABSENT" (the RIGHT reason via
`_import_derivation` / `_import_effect_helper`); the 6 GREEN are the sound, non-deliverable pins
(C: non-none-hint + its control, live-surface anti-vacuity, flip-surface-reaches-every-tool,
flip-hint probe-control; D: the D-3 proxy-blindness proof). `uv run ruff check` on both files: clean.

## §REUSE — §9.6 symbols reused (REUSE > RECREATE, priority #1)

- **`_core_dropping` / #194 landing-assert / reflects-predicate STRUCTURE** (`test_store_seam_one_derivation`)
  → generalised ∀ over the surface as the C ∀-mutation; mechanism is flip-hint (NOT one function — §9.6).
- **`TestTheMutationProofDiscriminates`** → the C flip-hint probe-control shape.
- **R16 `sdk_bound_handler_names` / `test_the_handler_derivation_is_not_empty`** anti-vacuity shape → the C live-surface anti-vacuity pin.
- **`_auth_fixtures.WireSession.call`** (the boundary callable; `.mcp` is structural-only) → handed as the D helper's only argument (R4).
- **R16 AST invariant** (`test_wire_discipline`) → REUSED via `posture_modules()` membership, not cloned.
- No new machinery invented. IDIOM 3 (summary honesty) is not in scope for C/D.

## §BUILDER-NOTE — the one action outside this reviser's writable set

The D reach pin (`test_the_effect_helper_module_is_within_R16_wire_discipline_reach`) is RED until
`test_wire_discipline.posture_modules()` is extended to include the effect-helper's module
(`_refusal_effect.py` does not match `POSTURE_MODULE_GLOB = "test_*posture*.py"`). I may NOT edit
`test_wire_discipline.py` (shared tree, concurrent siblings), so the builder does it. Demonstrated
viable in scratch by adding a `REFUSAL_HELPER_MODULE_NAMES` set that `posture_modules()` unions in
(derived-by-existence, not a raw hand-list) — 34 passed, and R16's own tests stay green. Any equivalent
extension that brings the module under the scan is acceptable; do NOT clone R16's scan into the D
contract (DRY).

## §RESID — residuals (each individually adjudicated; scope law — surfaced, not dropped)

- **R1 (D, R4 `__self__` back-door, low):** `probe.wire.call.__self__` still exposes `.mcp`, so a
  maximally-contrived helper doing `call.__self__.mcp.call_tool(...)` evades the `hasattr(call, "mcp")`
  leg. **Verdict:** closed by the R16 scan leg (`.call_tool` flagged receiver-blind), so the two legs
  together cover it. Noted so it is not read as fully closed by R4 alone.
- **R2 (D reach depends on a builder edit):** the reach pin cannot go green without the R16 extension,
  which is outside my writable set. **Verdict:** intended — the pin FORCES the extension; §BUILDER-NOTE
  records it. Not a C-DEF trap (the builder owns `test_wire_discipline.py`).
- **R3 (C helper not proven CONSUMED, inherited from adversary R2):** the contract pins the helper's
  existence + correctness, not that production consumes it (packet 39 does, later). **Verdict:**
  acceptable for this cycle's scope; the #291 test-side drift is fixed regardless. Unchanged by my revision.
- **R4 (C no-drift pin name-keyed, inherited adversary R1):** `test_no_drifted_hand_list…` keys on
  `_MUTATING_TOOLS`/`_READ_ONLY_TOOLS`; a third-named hand-list escapes. **Verdict:** honest bound of a
  name-keyed pin (INSTRUMENT 0's reach-attack is the standing guard). Unchanged.
- **Structural registration-gating → packet 39** (do NOT build here): fold-in note only, per brief.

## §PROV — provenance & tooling

- Scratch `/tmp/reviser-cd-work` (disposable `/tmp` cp copy via `scratch_copy.sh`, NOT a git worktree —
  no worktree abandonment concern; discard at will). `loremaster.__file__` printed inside scratch (§SAT).
- Instruments built as satisfiability deliverables (pasted for durability, scratch is disposable):
  the reference `partition_tools_by_posture` (§C-CHANGES), the reference `_refusal_effect.py` `(call,…)`
  helper + sweep primitive (§D-CHANGES/§SAT), and the C-WB5/C-WB6/D-WB2 wrong builds (§DISCRIM) are all
  described inline with their diffs and receipts here.
- Findings #346 (MP-1) and #347 (MP-2) were filed by the adversary; left OPEN — they close when the
  builder ships and the cold audit confirms, not by this contract revision.
- lore tools used: `lore_get_symbol` (WireSession), `lore_comms` (register/drain). Grep used for the
  `*_ANNOTATIONS` surface + R16 structure (non-symbol textual seams / cross-cutting map — the two
  honest grep cases); SAID here per the dogfood protocol. No lore weakness to file.
