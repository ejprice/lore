# REPORT-contract-fix-04b4-1

brief-base v10 read

## SUMMARY BLOCK
- state: **done** — adversary-04b4-1's BLOCKER + residual both closed; re-run green-where-green, RED-where-builder-work.
- Capability check: lore tools + write test files + store — all available/used. No new fallbacks.
- Packages considered: none — no mechanism specified (test-only delta).
- Graded: authored base `3091610` (my committed pins) · fix is on top, UNCOMMITTED (lead commits) · HEAD-at-report `3091610`.
- decisions-needed: one FLAG (not blocking) — the display cap's SEAM-vs-RENDER placement is now pinned to RENDER by pre-existing `:487`; see §3.
- receipt pointers: FINDING-1 §1 · cap-value de-constraint §2 · FINDING-2 §4 · counts §5.

## §0 · What the adversary found (REPORT-adversary-04b4-1.md)
- **FINDING-1 (BLOCKER):** a P6 corpse — `test_an_UNLIMITED_render_over_a_LARGE_ledger_carries_NO_line` — asserted the RETIRED "no-limit RENDER never discloses" over pop 40; #309's cap overturns it, so any legal cap < 40 reddens it and TRAPS the builder (C-DEF). Both correct and precise.
- **FINDING-2 (RULED PIN-THE-MISS):** my #319 derived guard is a ∀ over a SUBSET (foreign-refusal matrix + note recorder); a required-for / clamp / value-set served-prose lie survives all three pins. Extending the guard is out of §D-#319 scope, but the QUANTIFIER LAW requires the subset be a PINNED KNOWN BOUND, not a silent gap.

## §1 · FINDING-1 — corpse RETIRED (test_task_read_surface.py)
- **DELETED** `TestTheRenderedListingDISCLOSESItsOwnBOUND::test_an_UNLIMITED_render_over_a_LARGE_ledger_carries_NO_line` (was ~:964), replaced with a ⚰ breadcrumb naming why (#309 overturns it; a cap < 40 reddened it — a C-DEF that constrained the cap VALUE). Its live property (a COMPLETE answer discloses nothing) is subsumed, correctly cap-scoped, by my `TestTheNoLimitReadGetsADefaultDisplayCapWithTheCountedGrammar::test_the_no_limit_read_AT_OR_BELOW_the_cap_serves_NO_elision_line`.
- **Re-confirmed the corpse is the ONLY one** (independent of the adversary's sweep):
  - `:487` `test_an_UNLIMITED_listing_NEVER_discloses_a_bound` — **NOT a corpse.** Drives `_task_listing` (typed `rows` + `more`), i.e. the SEAM, which stays uncapped (`more is False`, all rows). Valid under a RENDER-level cap.
  - `:743` `test_an_UNLIMITED_listing_emits_NO_LIMIT_CLAUSE_AT_ALL` — **NOT a corpse.** Asserts the generated SQL binds NO `LIMIT` when uncapped; the display cap is Python-side render slicing, not a SQL `LIMIT`, so this stays true.
  - `:2807` (blockers-agreement) — OK, unrelated.
  - The class's other legs (partial-vs-complete at `_LISTING_CAP`, the normaliser positive control) are cap-scoped and unaffected — they pass.

## §2 · Cap VALUE de-constrained (honoring "no pin should constrain the cap value")
Beyond the corpse, I removed the one remaining soft value-constraint in MY pins:
- `_display_cap()` floor relaxed `>= 2` → `>= 1` (positive int is DEFINITIONAL for a cap, not a value choice; message updated).
- `test_the_no_limit_read_AT_OR_BELOW_the_cap_serves_NO_elision_line` now seeds **1** row (was 2) — `1 <= cap` for ANY positive cap, so the leg is fully cap-VALUE-agnostic.
Net: after the corpse retirement, **no pin constrains the cap value** — the builder may pick any positive int (recommend 50, per the lead). All #309 pins assert BEHAVIOUR (honest K == true surplus; complete ⇒ no line; grammar by input shape).

## §3 · FLAG (non-blocking) — cap placement is now pinned to the RENDER
Retiring the render-level corpse while `:487` (seam-level, `more is False`) stays green means the contract now PINS the display cap to the **RENDER** layer: `_task_listing` returns the full materialised set uncapped, and the RENDER slices to the cap and derives `K = len(rows) − shown`. This matches wave-C §2 ("renders take typed applicability") and the lead's ruling that `:487` is not a corpse. **If a build instead caps the SEAM** (returns capped rows / `more=True` on the no-limit path), `:487` turns red — that is a design escalation, not a corpse. The `⚰` breadcrumb records this so the builder meets it deliberately.

## §4 · FINDING-2 — PIN-THE-MISS added (test_mcp_server.py, #319 class)
Added `TestServedParamDescriptionsMatchTheRefusalMatrix::test_PIN_THE_MISS_the_derived_319_guard_is_bounded_to_its_class` (#137/#138):
- **States the bound:** the derived #319 guards cover EXACTLY two served-prose classes — the foreign-refusal `For '<actions>' ONLY` matrix, and the `note` recorder set. Required-for / clamp/range / value-set prose is **NOT** derived-guarded (the adversary's `subject`-optional-for-`supersede` demo survives all three #319 pins).
- **Reddening WITNESS:** a required-for param (`subject`, required by create/supersede) is structurally OUTSIDE `_derived_strict_to_action_matrix(AppContext.tasks)`, so the derived guard cannot see a false claim about it — the gap, pinned. Reddens the day a future author brings required-for params under the derived matrix (closing the hole), forcing a deliberate bound update.
- **NAMED RE-OPEN TRIGGER:** the day a required-for / clamp / value-set served-prose lie ships in production, EXTEND the derived matrix to that class and retire this pin. Until then the one-time anchor-free sweep (`REPORT-sweep-desc-04b4-1.md`) is the only coverage for those classes.

## §5 · Re-run (scoped, `-n auto`) — passed-COUNT
Consolidated over all authored classes + the corpse's parent class: **6 failed, 40 passed** (46). ruff clean; `scripts/typecheck.sh` clean on my files (also fixed one PLR0911 I'd introduced in the earlier mypy fix — the `_accepting` helper's return count).

Authored delta: **+1 GREEN** (the PIN-THE-MISS) → my authored set is now 6 RED / 36 GREEN; **−1 pre-existing corpse retired.**

The **6 RED are unchanged and all builder-work:** 3× #309 surplus counted-grammar legs (add `_DEFAULT_TASK_QUERY_DISPLAY_CAP` + house `+K more — re-run with limit=N` at the render), 2× #324 R-4 (`name`/`to` keyword-required), 1× #319 `note` residual (name `acknowledge` in the served prose). Everything else GREEN and mutation-provable.

Mutation-proofs from the first pass still hold (both pins unchanged): #319 false-desc → matrix pin RED; #310 sharing-revert → shipped guard RED both directions (scratch `loremaster.__file__` receipts in REPORT-contract-04b4-1.md §2).

## §6 · Scope honesty
- Still CONTRACT-ONLY: the cap + counted grammar, the `note` prose fix, and the `name`/`to` default removal stay RED for the builder. No production edits.
- No git state changes (lead commits).
- Pre-existing UNRELATED mypy reds remain in `loremaster/tests/test_auth_composition.py` (packet-39 area) — flagged in the prior report; not touched.
