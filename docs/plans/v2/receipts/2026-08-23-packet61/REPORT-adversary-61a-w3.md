# REPORT — adversary-61a-w3

brief-base v14 read
brief project v7 read

## RE-GRADE (2026-08-23, revised contract, 29 pins) — **VERDICT: CONTRACT SUFFICIENT**

The author closed the RG-A blocker. Focused delta re-grade (all in `/tmp/scratch-adv-61aw3`,
provenance `loremaster.__file__ = /tmp/scratch-adv-61aw3/loremaster/loremaster/store/surreal_schema.py`):

1. **BLOCKER CLOSED.** New `_var_slice_src` (the house `statements = [...]; return statements` idiom, 20/28
   real slices) + two pins: `TestFoldCoverageStructuralDiscrimination::test_an_unfolded_variable_returning_slice_is_flagged`
   (synthetic) and `TestFoldCoverageMutationProofsOnRealSource::test_removing_a_real_variable_returning_fold_call_reds_the_scan`
   (REAL `_trace_statements`, a fold-only variable-returner) + its fold-only guard, and a
   `test_a_folded_variable_returning_slice_is_not_flagged` negative control. **My exact original wrong build
   (literal-only structural `_emits`, which passed 24/24 before) now REDS 2 pins** — both a synthetic AND a
   real-source variable pin. The primary fold-coverage defense is no longer blind to variable-returning
   slices. ⚠ HONEST NOTE: I reproduce **2** reds with my precise literal-only `_emits`, not the "3" the lead
   relayed from the author's counter-build (a different wrong-`_emits` flavor). Immaterial to sufficiency —
   both a synthetic and a real variable-returner now discriminate.
2. **Secondary PIN-THE-MISS is LIVE.** `TestStandaloneExemptionIsAKnownBound::test_a_slice_consumed_only_by_a_generate_ddl_is_exempt_regardless_of_that_generate_being_wired`
   asserts the standalone-via-dead-generate bound, passes on the correct build, and **REDS when I close the
   exemption** (dropped `standalone` from the fold-coverage exemption → pin trips) — so it discriminates, is
   not decoration, and carries its whole-tree-reachability re-open trigger in the message.
3. **Satisfiability:** correct build **29 passed**; RED@HEAD **29 failed**, NAMED (#133 guard); ruff + mypy
   clean on the contract file.

Everything from the original grade that was SOLID stayed solid; nothing regressed. **SUFFICIENT — release
the builder.** The original blocker analysis below is retained as the dated record of why the delta mattered.

---

## SUMMARY BLOCK (original grade — 2026-08-23, at 24 pins — SUPERSEDED by the re-grade above)
- **VERDICT (original): CONTRACT INSUFFICIENT** — 1 BLOCKER missing pin (a wrong build passes all 24). Now FIXED.
- **P1 headline — a wrong build SURVIVES the contract:** a structural-leg emptiness check that
  recognizes only a **non-empty list LITERAL** as "emitting" (blind to `return <variable>`) passes
  **24/24** while the PRIMARY fold-coverage defense is BLIND to **19 of 28** real slices — every slice
  that emits via the `return statements` idiom (incl. fold-only `_trace`/`_chunk`). Live-demoed:
  unfolding `_trace_statements` is flagged by the correct build, MISSED by the wrong one.
- **Root class:** PKT-28 C1 fixture-value MONOCULTURE + THE QUANTIFIER LAW — all emitting fixtures are
  `return [_define_table("x")]`; the real-source structural mutation targets `_snapshot_statements` (a
  literal-returner). The ∀-invariant is conditioned on `_emits`, and `_emits`'s reach over return-STYLE
  is a hidden constant for the structural leg.
- **Secondary (recommendation, not blocker):** standalone-via-DEAD-`generate_*_ddl` over-exemption
  (Attack 3, CONFIRMED) is documented as report bound #3 but — unlike the other two bounds — is not
  pinned as an asserting PIN-THE-MISS test; the report is archived, the pin would survive.
- **Attack 2 REFUTED** (shared under-reaching enumeration): the by-name==by-shape cross-check + synthetic
  fixtures caught it (7 pins red); INSTRUMENT-0 is genuinely present and solid.
- **Author claims VERIFIED (P4):** 28 slices / 16 folded / 12 unfolded / 0 orphans / 0 prose findings;
  by-name==by-shape=28; mutation proofs reproduce; RED@HEAD 24 failed NAMED; reference build 24 passed;
  ruff+mypy clean (incl. the post-ruff C-DEF leg).
- **Graded:** f87e774 · HEAD-at-report: f87e774 · SAME (wave uncommitted; contract file untracked at HEAD).
- **Packages considered:** none — no runtime mechanism; the instrument is a stdlib `ast` scan (matches
  the author's verdict).
- **Reuse ledger:** none — I introduce no production symbols (adversary; scratch probes only).
- **Provenance receipt (#140):** `loremaster.__file__ = /tmp/scratch-adv-61aw3/loremaster/loremaster/store/surreal_schema.py`
  (all wrong builds graded the scratch, not the original).
- **Decisions-needed:** the DERIVED-standalone-vs-literal-allowlist ratification is the lead's; I
  concur DERIVED (a literal `_STANDALONE_SLICES` would be the 7th reach-defeat). See §Reach table row 5.

---

## THE BLOCKER (missing pin) — the structural leg's emptiness reach is a return-style monoculture

**The test that should exist:** in `TestFoldCoverageStructuralDiscrimination`, a fixture with an
emitting-via-VARIABLE slice, folded nowhere, that MUST be flagged — e.g. a `_slice_src` variant whose
body is `out = [_define_table("x")]\n    return out` (the real `return statements` idiom) instead of
`return [_define_table("x")]`. **AND/OR** the real-source structural mutation
(`test_removing_a_real_fold_call_reds_the_scan`) should target a **variable-returning** fold-only slice
(`_trace_statements`), not only `_snapshot_statements` (a literal-returner).

**The defect it catches:** a builder whose structural-leg emptiness classifier treats a return of a
non-empty list LITERAL as "emitting" and everything else (a `return <variable>`) as empty. This is a
plausible narrow reading of "emits ≥1 statement", and the contract's binding TESTS never force
otherwise — the note *"conservative: NOT provably `return []`"* is prose, not a pin.

**Why it is load-bearing, measured at f87e774:** 19 of 28 real slices emit via `return statements`
(a `Name`), only 9 via a list literal. The guard's whole PURPOSE is to catch a FUTURE unfolded emitting
slice (e.g. the `audit` slice landing in 61a-w4). If that slice returns a variable (the dominant
idiom), a literal-only structural `_emits` false-clears it — the exact #398/#399 recurrence the packet
exists to prevent, reintroduced through the guard's blind spot, green at every gate.

**Empirical reproduction (all in `/tmp/scratch-adv-61aw3`, provenance-asserted):**

| build | contract result | unfold `_trace_statements` → flagged? |
|---|---|---|
| reference (Appendix A) — correct `_emits` | **24 passed** | **True** (correct) |
| structural `_emits` = literal-only; prose `_emits` correct | **24 passed** | **False** (BLIND) |

The wrong build differs from the reference ONLY in the structural scan's emptiness predicate
(`_emits_struct_literal_only`: `return True` iff a `Return` holds a non-empty `ast.List`); the prose
scan keeps the correct `_emits`, so `test_reintroducing_stale_prose_on_a_real_folded_slice_reds_the_prose_scan`
(which targets the variable-returning `_keep_statements`) still passes. **Nothing in the contract forces
the two scans to share one `_emits`, and only the PROSE leg is pinned on a variable-returner — the
STRUCTURAL leg, the PRIMARY defense, is pinned only on literals.**

> Note the asymmetry that hides this: `_keep_statements` (a `return statements` slice) IS incidentally
> pinned as emitting — but by the PROSE mutation proof, not any structural test. So a builder who
> shares one `_emits` is caught; a builder who inlines emptiness separately in each scan is not. The
> contract must pin the STRUCTURAL leg's emptiness on a variable-returner directly.

## The quantifier table (P1b)

| invariant | ∀-over-inputs or guarded? | receipt |
|---|---|---|
| every emitting slice is folded-or-standalone (real schema) | ∀ over derived slices — **but conditioned on `_emits`** | The ∀ is only evaluated where `_emits`→emitting; a literal-only `_emits` makes it VACUOUS on 19/28 slices → **BLOCKER above**. THE QUANTIFIER LAW: an invariant conditioned on the very predicate that is under-pinned. |
| an unfolded emitting slice is flagged | ∀ (synthetic + real mutation) | GREEN on correct build, but the "emitting" branch is only exercised with literal bodies — see BLOCKER. |
| a genuinely-empty (`return []`) stub is exempt | ∀ | `test_a_genuinely_empty_stub_is_exempt` discriminates (correct build). |
| folded/standalone emitting slice with emptiness prose → flagged | guarded (best-effort, KNOWN BOUND) | honestly pinned + threat model + re-open trigger (`TestStaleEmptinessProseIsAKnownBound`). |
| name-set ≠ shape-set → fail closed | ∀ (divergence) | `test_a_misnamed_emitter_fails_the_scan_closed`, `test_a_wholesale_convention_rename_fails_the_scan_closed` reproduce. |

## The REACH table (P1c) — per instrument the contract introduces/relies on

Legs: **E** = empirical (wrong build in scratch), **C** = construction-inspection.

| # | instrument | reach DERIVED vs hand-list | coverage a checked variable? | effect vs proxy | one-source / mutation | verdict |
|---|---|---|---|---|---|---|
| 1 | slice-fn set (by-name `^_[a-z0-9_]+_statements$`) | DERIVED, re-derived per call (E: `test_the_scan_is_rederived_per_call_not_cached`) | YES — cross-checked vs by-shape, fail-closed on divergence + non-empty floor | effect (source AST) | independent shape oracle (row 2) | **SAFE** |
| 2 | by-shape oracle (private `-> list[str]`) | DERIVED (annotation), independence pinned (E: `test_name_and_shape_derivations_are_independent`) | YES — is the INSTRUMENT-0 cross-check itself | effect | shares `_top_defs` substrate; Attack 2 tried + **REFUTED** (7 pins red) | **SAFE**; KNOWN BOUND (annotation-drop rename) pinned |
| 3 | **`_emits` emptiness classifier** | predicate over return SHAPE; reach over return-STYLE is a **HIDDEN CONSTANT** for the structural leg (only literals pinned) | **NO** for the structural leg (E: literal-only build passes 24) | effect | structural + prose leg free to use TWO `_emits` (not mutation-proven shared) | **MISSING PIN → INSUFFICIENT** (the BLOCKER) |
| 4 | folded derivation (calls in `generate_ddl`) | DERIVED (AST calls) | YES (E: real mutation `test_removing_a_real_fold_call_reds_the_scan`) | effect | — | **SAFE** |
| 5 | standalone derivation (calls in any `generate_*_ddl`) | DERIVED (AST) — NOT a literal hand-list (I concur; a literal `_STANDALONE_SLICES` = the 7th reach-defeat) | flags orphan ✓ / exempts real standalone ✓ (both pinned) | effect | — | **DERIVED**; over-exemption residual (Attack 3, below) unpinned |
| 6 | prose backstop (`KNOWN_EMPTINESS_PHRASES`) | enumerate-the-forbidden by nature — KNOWN BOUND | within its CLOSED set: discriminates (positive/negative/mismatch controls, E) | effect | — | **SAFE** as a bounded backstop; novel-phrasing residual = ACCEPTED bound (not flagged) |

**INSTRUMENT-0 present & real?** YES. The by-name/by-shape cross-check with fail-closed-on-divergence
and a non-empty floor is genuinely built and pinned (rows 1–2). The BLOCKER is NOT an INSTRUMENT-0
gap — it is a *different* reach surface (`_emits`'s coverage over return-STYLE) that INSTRUMENT-0 does
not touch.

## Attack 3 (CONFIRMED residual — recommendation, not blocker): standalone via a DEAD generate

A slice consumed ONLY by a `generate_*_ddl` that is itself never wired to any store `ensure_ready` is
EXEMPTED — `scan_schema_fold_coverage` returns `[]` for a `_zombie_statements` + `generate_zombie_ddl`
(unwired) module. This is the #398/#399 class (DDL wearing an implementation that never runs).

- It is within the instrument's **stated single-module scope** (closing it needs a whole-tree wiring
  scan — the reach STOP-rule; verified false at HEAD: every `generate_*_ddl` is wired, author's table).
  So this is a SCOPE boundary, not a hole in a mechanism the instrument employs. **Not a blocker.**
- **BUT it is handled inconsistently:** the other two KNOWN BOUNDS (prose novel-phrasing, annotation-drop)
  each get an asserting PIN-THE-MISS test that reds if someone closes them; this bound lives ONLY in the
  report prose (`REPORT-contract-61a-w3.md` §"KNOWN BOUNDS" #3), which is archived at wave close.
- **Recommendation:** add `TestStaleEmptinessProseIsAKnownBound`-style asserting pin —
  `test_a_standalone_via_dead_generate_is_a_known_bound` (synthetic zombie module → scan returns `[]`),
  with the re-open trigger *"a `generate_*_ddl` found unconsumed by any store `ensure_ready` → add a
  wiring cross-check"*. Cheap; makes the bound met deliberately per §"WHEN YOU CANNOT CLOSE A HOLE".

## Fixture-discrimination verdicts (P2)

- **`_slice_src(emits=True)` = `return [_define_table("x")]` — a MONOCULTURE.** Every emitting fixture
  uses the list-LITERAL shape; the code branches on return-shape (literal vs variable) and no emitting
  fixture uses the variable shape. This is the PKT-28 C1 parameter-value-monoculture trap verbatim → the
  BLOCKER. FIX: add an `emits_via_variable` mode / target a variable-returner in the real mutation.
- `test_removing_a_real_fold_call_reds_the_scan` — discriminates, but on a LITERAL-returner
  (`_snapshot_statements`); its guard `test_a_fold_only_slice_is_not_also_standalone` correctly prevents
  a vacuous mutation. Reproduced GREEN. Should ADD or SWITCH to `_trace_statements` (variable, fold-only).
- Prose fixtures (`test_a_folded_slice_with_a_stale_emptiness_docstring_is_flagged` +
  `_with_honest_prose_is_not_flagged` + `_an_empty_stub_with_truthful_emptiness_prose_is_not_flagged`)
  — GOOD discrimination (mismatch = emit+claim-empty vs honest empty claim on an empty stub). Reproduced.
- INSTRUMENT-0 fixtures (misnamed emitter / wholesale rename / independence / re-derived-per-call /
  annotation-drop bound) — all discriminate; reproduced against reference build.

## Attack 2 — REFUTED (the contract holds)

Hypothesis: a shared `_top_defs` that under-reaches drops a real slice from BOTH derivations identically,
so the cross-check stays green while a slice is silently unguarded. Constructed `_top_defs` returning
`defs[:-1]` → **7 pins red** (synthetic modules place `generate_ddl` last; dropping it breaks fold
detection), AND on the real schema the LAST top-level def is `generate_lease_ddl` (a generator, not a
slice), so `derive_slice_fns` still returned 28. I could not construct a NATURAL under-reach that
survives. Residual (verdict, not a miss): no pin ties the derived count to a THIRD independent ground
truth beyond `_snapshot`/`_keep` membership; the by-name==by-shape cross-check is belt-and-braces and I
could not break it — **acceptable**.

## RED honesty (P7) & satisfiability (P1/C-DEF)

- **RED@HEAD (no scan home):** `24 failed`, each a NAMED behavioral `AssertionError` carrying the full
  build-instruction note (e.g. `scan_schema_fold_coverage is not built in any of ('_schema_fold_guard',
  '_logging_fixtures')…`), collection clean — the #133 guarded-import idiom works; not an import typo.
- **Reference build (Appendix A of the contract report, written verbatim to
  `/tmp/scratch-adv-61aw3/loremaster/tests/_schema_fold_guard.py`):** `24 passed in 0.55s`.
- **C-DEF ruff leg:** ruff + mypy clean on the contract file (real tree). Satisfiable, including after
  lint.
- **Counts (P4, independently derived):** 28 slices, by-name==by-shape (28), 16 folded, 12 unfolded, 0
  orphans, 0 real-schema prose findings. Matches the author's report exactly.

## Probe record (commands + real output)

Scratch: `./scripts/scratch_copy.sh /tmp/scratch-adv-61aw3` → provenance asserted
(`loremaster -> /tmp/scratch-adv-61aw3/loremaster/loremaster/__init__.py`). Reference scan pasted into
`loremaster/tests/_schema_fold_guard.py`.

1. **Positive control (reference):** `uv run python -m pytest loremaster/tests/test_schema_fold_coverage.py -q`
   → `24 passed`.
2. **RED@HEAD:** stash `_schema_fold_guard.py` → `24 failed`, sample = NAMED AssertionError with the
   build note.
3. **Attack 1 (BLOCKER):** patch structural scan to `_emits_struct_literal_only`, prose scan unchanged →
   `24 passed`. Live damage: correct build flags unfolded `_trace_statements` = **True**; wrong build =
   **False**. (`_trace_statements` confirmed: returns a `Name`, standalone=False, folded no-arg.)
4. **Attack 2 (REFUTED):** `_top_defs` → `defs[:-1]` → `7 failed, 17 passed`; real derived count still 28.
5. **Attack 3 (CONFIRMED residual):** zombie slice + unwired `generate_zombie_ddl` →
   `scan_schema_fold_coverage` returns `[]` (exempted).

## Handoff
CONTRACT INSUFFICIENT → return to the author (per law: contract → adversary → **revise** → build). The
one BLOCKER is a single-fixture fix (force the structural leg's `_emits` on a variable-returner);
Attack 3 is a cheap PIN-THE-MISS add (recommended, not required). Everything else — INSTRUMENT-0, the
derivations, RED honesty, satisfiability, the author's counts — is SOLID and reproduced.
