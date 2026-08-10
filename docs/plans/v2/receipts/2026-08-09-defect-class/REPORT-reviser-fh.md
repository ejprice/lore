brief-base v10 read
brief project v7 read

# REPORT — reviser-fh (CONTRACT reviser: F/#279 + H/#290 missing pins)

Session `2026-08-09-fix-344-345`. Role: contract reviser — ADD the adversary-found missing
pins to the existing RED contracts per the consolidated §9 ∀-mutation-proof pattern. CONTRACT
TESTS ONLY; no production/implementation code changed in the real tree.

## SUMMARY

- receipt: brief-base v10 read · brief project v7 read
- state: **done**
- deviations: **none** — every reference-build edit (the demonstrated correct fix) was made in
  a disposable scratch copy only; the real tree carries exactly the two in-scope contract edits.
- Packages considered: none — contract pins only, reusing stdlib (`ast`/`inspect`/`importlib`) +
  pytest; the satisfiability reference build is stdlib-only. No mechanism specified.
- Graded: `962eeb6` · HEAD-at-report: `962eeb6` · SAME
- decisions-needed: **none in my scope** (F5 placement (b) and the B/#337 forks belong to other
  cycles; my pins consume F5's ruled home `loremaster.store._txn_coroutines` as given).
- receipt pointers: F pins → §F (test names in `test_store_seam_one_derivation.py`); H pins → §H
  (`test_wrong_builds.py`); RED / satisfiability / wrong-build discrimination → §Verification;
  scratch dir + surfaced notes → §Flags.

## Files changed (both in the granted writable set)

| file | tracked? | change |
|---|---|---|
| `loremaster/tests/test_store_seam_one_derivation.py` | untracked | F: ∀-drop + LEG-A + coverage pins |
| `scripts/test_wrong_builds.py` | tracked (` M`) | H: routing spy + anti-dup offender scan |

NOT touched (as briefed): `scripts/test_harness_guards.py` (its `refuse_vacuous_baseline`
behaviour pins were graded sound by adversary-eh — left green, unchanged). Out of scope, not
touched: E/#289. All four production files the reference build would edit
(`loremaster/loremaster/store/__init__.py`, `scripts/forgery_door_sweep.py`,
`scripts/wrong_builds.py`, `loremaster/tests/test_blocks_edge.py`) are UNCHANGED in the real
tree — confirmed by `git status` (§Verification).

---

## F — #279 store-seam derivation (`test_store_seam_one_derivation.py`)

**Gap closed (adversary-f):** the sharing mutation proof dropped only `run_query` (and
`run_query`+`bootstrap_session` for `_degrade`), so a *partial private copy* — route the dropped
seam, hardcode the rest — survived. **WB7** (`store_seams`, backstopped/residual) and **WB8**
(`_degrade`, no consistency backstop → **BLOCKER**) both passed the contract at 14/0.

### What I added

1. **`_live_door_surface()` / `_live_degrade_wide_surface()`** (module-level, new) — the ∀-drop
   REACH, re-derived from production truth every collection (`vars(loremaster.store._txn)` for
   doors; what `loremaster.tasks` binds for the wide set), **never the module-level `_DOOR_SEAMS`
   hand-list.** ⚠ META-RECURSION (design §9.1): a ∀ whose reach is a fixture constant is the class
   itself, one level up. These read truth that EXISTS at HEAD, so the parametrised tests COLLECT
   cleanly before the build while their bodies stay RED. Deliberate INDEPENDENT ORACLES (the same
   idiom the existing `test_store_seams_is_exactly_the_public_statement_filter_of_the_core`
   already uses), documented as such.

2. **`TestSharingProvenByMutation` — parametrised** (replaces the 4 single-seam methods; each old
   method is a strict subset of the new ∀, so nothing is lost — `run_query`/`bootstrap_session`
   remain covered):
   - `test_dropping_ANY_door_from_the_core_reddens_store_seams[door]` — ∀ over `_live_door_surface()`
   - `test_dropping_ANY_door_from_the_core_reddens_seam_bindings[door]` — ∀ over `_live_door_surface()`
   - `test_dropping_ANY_wide_seam_from_the_core_reddens_the_degrade_derivation[seam]` — ∀ over
     `_live_degrade_wide_surface()` (doors PLUS `bootstrap_session`).
   Reuses `_core_dropping` (carries the #194 landing assert), `_rebind_everywhere` (by-identity,
   reaches from-imports), `_degrade_reflects_core_drop`, `_degrade_derivation_includes`.

3. **`TestTheMutationSurfaceIsLiveDerivedAndComplete`** (new, section 6) — coverage as a checked
   variable + the LEG-A backstop:
   - `test_the_door_drop_surface_equals_the_live_core_door_filter` — the door ∀ reach == core's
     public+`statement` filter (RED at HEAD via `_load_core`).
   - `test_the_degrade_wide_surface_equals_the_live_core_bound_in_tasks` — the wide ∀ reach ==
     `seam_bindings(seams=core)` filtered to `loremaster.tasks` (RED at HEAD).
   - `test_the_degrade_set_is_exactly_the_wide_core_bound_in_tasks` — **LEG A, the missing
     backstop**: `_degrade`'s OWN derived set == the wide core bound in tasks, live each run.
     Catches a `_degrade` that diverges from the core WITHOUT dropping anything (a future 4th seam
     the two derivations disagree about — the #279 defect on the `_degrade` axis).

### Which pin closes which wrong build

- **WB7** (store_seams hardcodes `execute_transaction`/`execute_read_transaction`): the door ∀-drop
  reddens both hardcoded doors, across `store_seams` AND `seam_bindings`. `run_query` (routed) and
  the coverage pin stay green.
- **WB8 (BLOCKER)** (`_degrade` hardcodes the two): the wide ∀-drop reddens both. `run_query` /
  `bootstrap_session` (routed, via the fail-closed asserts) and LEG A (WB8 returns all 4 today, so
  set-equal) stay green — WB8 is caught by LEG B, and LEG A stands as the future-seam backstop, per
  the adversary's own analysis.

---

## H — #290 baseline anti-vacuity SHARING (`test_wrong_builds.py`)

**Gap closed (adversary-eh, the BLOCKER):** the property *"`refuse_vacuous_baseline` is the ONE
implementation — `wrong_builds.main` SHARES it, not re-inlines it"* had **no RED home**. A build
with the correct shared helper + `main`'s inline copy kept (two copies of one policy, the
#102/#120 trap) passed the whole scripts contract set green (9 passed, nothing reddened).

### What I added (design §9.1 SHARING specialization — delete-the-call + anti-dup)

1. **`TestMainSharesTheVacuousBaselineGuard`** — the delete-the-call proof in **spy form** (design
   §9.1 / adversary-eh both sanction the spy): a routing spy replaces the SHARED
   `refuse_vacuous_baseline` (reaching both `import _harness_guards` and
   `from _harness_guards import …` bindings) and drives `main`'s real baseline path.
   Parametrised over baseline `[0, 315]` — the **315 leg forces the UNCONDITIONAL
   `refuse_vacuous_baseline(baseline, …)` form** (a `if not baseline: refuse(...)` half-extraction
   keeps the vacuity predicate inline and never calls the guard on 315) and satisfies the §9.4
   monoculture law (a hardcoded `0` echo cannot match 315). "Delete `main`'s call → the spy never
   fires → this pin reddens" is exactly the delete-the-call mutation.

2. **`TestNoSecondInlineVacuousBaselineGuard`** — anti-duplication, reusing the
   **`test_retry_seam._all_sdk_call_sites` offender-enumeration SHAPE** (`lore_get_symbol`, HEAD):
   `_inline_vacuity_guards()` AST-walks `wrong_builds.py`, NAMES every inline vacuity guard
   (`if not <name>:` / `if <name> == 0:` that raises) by `file:line`, fail-closed — a DERIVED scan,
   not a fixed-string search. The exclusions are structural, not a denylist (Call operand / BoolOp /
   truthy / `!=`), so the git-check, the `failed or errors` check, the `unknown` check and the
   `not (passed or failed or errors)` check are all correctly ignored. ⚠ BOUND stated in the pin:
   pattern-keyed, so a differently-shaped copy (`if baseline < 1:`) is the un-derivable tail
   INSTRUMENT 0 owns; no allowlist today (one site) — a future legit `not <name>: raise` must be
   allowlisted with a reason (allowlist-the-safe).

### Which pin closes the BLOCKER

- **Two-copies** (helper present + `main` keeps inline, does not route): the spy pins fail (`main`
  raises the inline `SystemExit`, never `_SharedGuardWasCalled`) AND the anti-dup scan fails
  (offender at `wrong_builds.py:430`). Neither alone is the sharing proof; together they are (the
  spy catches "doesn't route", anti-dup catches "routes AND keeps a copy").

---

## Verification (all receipts; scratch is provenance-asserted)

**RED at HEAD `962eeb6` (real tree, read-only test runs):**
- F: `uv run pytest loremaster/tests/test_store_seam_one_derivation.py` → **21 failed, 2 passed**.
  Every new pin RED via `AttributeError: module 'loremaster.store' has no attribute
  '_txn_coroutines'` (right reason). The 2 green = the two HEAD positive controls
  (`test_the_door_subset_is_the_known_three_doors`, `test_the_mutation_technique_moves_a_router…`).
  Parametrisation COLLECTED cleanly: doors `[run_query, execute_transaction,
  execute_read_transaction]`, wide `[bootstrap_session, execute_read_transaction,
  execute_transaction, run_query]`.
- H: `uv run pytest scripts/test_wrong_builds.py` → **3 failed, 1 passed**. Spy pins `[0]`/`[315]`
  RED via `ModuleNotFoundError: No module named '_harness_guards'`; anti-dup RED naming exactly
  `wrong_builds.py:430: UnaryOp(op=Not(), operand=Name(id='baseline'))`. Existing
  `TestTheCommittedWrongBuildsCanActuallyRun` green.

**Satisfiability (scratch `/home/ejprice/scratch-reviser-fh`, built by `scripts/scratch_copy.sh`;
`loremaster.__file__ = /home/ejprice/scratch-reviser-fh/loremaster/loremaster/__init__.py` —
provenance INSIDE the scratch, #140-clean). Reference fix built there: `_txn_coroutines` in
`loremaster.store`; `store_seams`/`seam_bindings(seams=)` routed; `_degrade` routed by identity
through the core; `_harness_guards.refuse_vacuous_baseline`; `main` routes through it
unconditionally.**
- F: **23 passed** (was 21f/2p at HEAD).
- H: `test_wrong_builds.py` **4 passed**; `test_harness_guards.py` (unchanged) **8 passed**.

**Wrong-build discrimination (scratch, wrong build applied over the reference, then restored) —
proves the pins CATCH the survivors, not merely pass on correct:**
- **WB7** (store_seams routes `run_query`, hardcodes the other 2 doors): **4 failed** —
  `reddens_store_seams[execute_transaction]`, `[execute_read_transaction]`,
  `reddens_seam_bindings[execute_transaction]`, `[execute_read_transaction]`; `[run_query]` +
  `door_drop_surface` coverage green.
- **WB8 (BLOCKER)** (`_degrade` routes `run_query`+`bootstrap_session`, hardcodes the other 2):
  **2 failed** — `reddens_the_degrade_derivation[execute_transaction]`, `[execute_read_transaction]`;
  `[run_query]`, `[bootstrap_session]`, LEG-A `degrade_set_is_exactly`, and `degrade_wide_surface`
  coverage all green.
- **H two-copies (BLOCKER)** (helper present via `git checkout -- scripts/wrong_builds.py` to
  restore the HEAD inline `main`, `_harness_guards.py` kept): **3 failed** — spy `[0]`, spy `[315]`,
  anti-dup (`wrong_builds.py:430`); `TestTheCommittedWrongBuildsCanActuallyRun` green. This is
  exactly adversary-eh's reproduced "9 passed, nothing reddens" — now it reddens.

**Static gates on the two touched files (real tree):**
- `uv run ruff check` → **All checks passed!**
- mypy: `MYPYPATH=scripts uv run mypy scripts` → **Success, no issues (39 files)**;
  `uv run mypy loremaster` → **0 errors in `test_store_seam_one_derivation.py`** (the 110 loremaster
  errors are all in SIBLING cycles' RED contracts — `test_auth_composition`, `test_ast_reach_helpers`,
  `test_refusal_observes_effect`, `test_mutating_set_derivation` — which name unbuilt symbols by
  design; not mine, see §Flags).

## §9.6 REUSE MAP — symbols reused (not reinvented)

- **∀-mutation in-test liveness (LEG B):** `_core_dropping` (incl. the #194 landing assert),
  `_rebind_everywhere` (by-identity, reaches from-imports), `_degrade_reflects_core_drop`,
  `_degrade_derivation_includes` — all existing in `test_store_seam_one_derivation.py`, GENERALISED
  ∀ over the live surface (the exact gap adversary-f found).
- **Coverage / set-equality (LEG A):** reused the SHAPE (live set-equality against the core,
  recomputed each run), per-instrument — NOT routed through the tree-scan
  `assert_scan_reached_every_member` (that is TREE-SCAN-scoped; store seams are a non-tree surface —
  §7 over-consolidation ruling).
- **Anti-dup offender enumeration (H):** `test_retry_seam._all_sdk_call_sites` SHAPE (derive from the
  AST, name each offender by `file:line`, fail-closed) — reused, not cloned.
- **`mutation_proof.py`:** its both-direction lesson (declared-RED-that-stays-GREEN is a private
  copy) informs the design; the delete-the-call proof is realised as a pytest routing spy in
  `test_wrong_builds.py` (the brief's named home) rather than the CLI receipt, because a pre-build
  contract has no call to delete yet — the spy is RED at HEAD for the same reason.

## Flags (nothing silently dropped)

1. **Scratch dir left in place:** `/home/ejprice/scratch-reviser-fh` (a `scratch_copy.sh` copy, NOT
   a git worktree; disposable by #140). `rm -rf` was permission-denied to me; flagging for cleanup.
   All reference edits + wrong-build probes were confined to it; the real tree is clean of them.
2. **Sibling RED contracts show mypy errors** (110 in `loremaster`): `test_auth_composition.py`
   (pkt-39 auth), `test_ast_reach_helpers.py` (A-SUB/F4), `test_refusal_observes_effect.py`
   (D/#295), `test_mutating_set_derivation.py` (C/#291). These are other cycles' RED contracts
   naming unbuilt symbols — expected RED, not introduced by me. Raised per scope law (the operator
   owns whether that matters for this session's checkpoint).
3. **The old adversary-f "docstring over-claims" flag is now resolved by adoption:** with the ∀-drop
   in place, `TestSharingProvenByMutation`'s "tells DRY from looks-DRY" claim is TRUE for every seam,
   not just `run_query`; I updated the class docstring to state the ∀ nature explicitly.
4. **Builder note carried forward (adversary-f Flags):** the reference `_degrade` I used routes
   through `_txn_coroutines()` BY IDENTITY and imports NOTHING from `scripts/` — the cleaner form the
   adversary recommended, avoiding the tests→`scripts` `sys.path` fragility. The builder should take
   that form (it is what my satisfiability + discrimination proofs are against).
