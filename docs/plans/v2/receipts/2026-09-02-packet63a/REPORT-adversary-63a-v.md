# REPORT-adversary-63a-v — CONTRACT ADVERSARY grade of the F5-whole-tree-reach RED contract (#446 close)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT** — 2 concrete missing pins, both **freshly-ruled design
  step-6 riders** (`3aea565`, committed **4 minutes AFTER** the contract `194f3c8`), which the
  contract at HEAD does not yet carry. The contract's CORE is otherwise SUFFICIENT-grade.
- **P1 headline — NO wrong build survived the contract in this wave's scope.** 9 mutation-proofs,
  all RED-for-the-right-reason (incl. the RELOCATED-HIDDEN-CONSTANT build, both forms). Satisfiability
  reproduced independently: **29 passed / 0 failed** + ruff clean on the minimal reference build.
- **The §FORK is RESOLVED, not open:** design step 6 (`3aea565`) BLESSES the contract's chosen
  both-ways reading as the faithful realisation (fragment-builder soundness). I independently confirm
  the reading is SOUND. The INSUFFICIENT rests ONLY on the two riders step 6 ADDED.
- **Missing pin 1 (R1, primary):** no ∀-over-exempt-entries **self-containment validity pin** (literal
  site == seam-call site). Migrate-governed IS self-contained (AST-verified) so no CURRENT false clear
  — but the origin-match guard's SOUNDNESS CONDITION is a hidden constant, the reach class one level up.
- **Missing pin 2 (R2, secondary):** the #138-class **hand-set-label accepted bound** is named in NO
  instrument docstring (threat-model rider). Documentation gap, not a false clear.
- state: **done**
- **Graded:** `3aea565` · HEAD-at-report: `3aea565` · **SAME**. (Contract test files byte-identical
  between `194f3c8` and `3aea565`; `3aea565` is docs-only — it moved the DESIGN, not the contract.)
- Packages considered: none — the only production mechanism is `governed_exempt` (stdlib
  `contextvars`+`contextlib`, mirroring shipped `write_guard`); test infra is stdlib `ast`/`tomllib`/
  `sys._getframe`. No package replaces a contextvar CM or an AST/stack-walk instrument. Author's
  `Packages considered: none` CONFIRMED by independent diff.
- Reuse ledger: none (adversary writes no production symbols; scratch discarded).
- decisions-needed: **route R1/R2 to a contract revision before the builder** (no revision skips the
  adversary). Recommendation + buildable form in §MISSING-PINS.
- receipt POINTERS: verdict driver → §MISSING-PINS; wrong-build battery → §P1; quantifier → §P1b;
  reach → §P1c; satisfiability → §SAT; RED honesty → §P7; residuals → §RESIDUALS.

---

## §SAT — satisfiability receipt (C-DEF), reproduced INDEPENDENTLY

Provenance-asserted scratch via `./scripts/scratch_copy.sh /tmp/cav63av_adv_2302454` (all four members
resolve INSIDE the copy). Reference build = the minimal builder GREEN, applied by me (not relayed):
- `governed.py`: `_ACTIVE_EXEMPT: ContextVar[str|None]` + `active_exempt()` + `@contextmanager
  governed_exempt(name)` — a verbatim mirror of the shipped `write_guard`/`active_write_guard`.
- `principals.py::_migrate_memory_scope`: `with governed_exempt("migrate-governed"):` wrapping the
  backfill `run_query(...)`.

Receipt: `loremaster.__file__ = /tmp/cav63av_adv_2302454/loremaster/loremaster/__init__.py`
(**grading the scratch, not the original — #140-safe**). The 3 F5 modules
(`test_memory_enforcement_63a_v.py` + `_63a_iv` + `_bounds_63a_iv`) → **29 passed, 0 failed** in 8.86s.
All 3 RED pins flip GREEN; nothing else moves. Harder leg: `uv run ruff check
governed.py principals.py` → **All checks passed!** (the inner `from loremaster.governed import
governed_exempt` mirrors the function's existing inner import — no orphaned import). C-DEF satisfied.

## §P7 — RED honesty (reproduced), and the ANTI-VACUITY leg is REAL

At HEAD `3aea565`, `test_memory_enforcement_63a_v.py` → **3 failed, 14 passed** (module-local; 26 GREEN
across all 3 F5 modules, matching the contract report). All 3 RED isolate the UNBUILT production
mechanism, for the right reason:
1. `test_the_governed_exempt_mechanism_is_built` — `governed.governed_exempt`/`active_exempt` absent.
2. `test_migrate_memory_scope_enters_governed_exempt` — `_migrate_memory_scope` calls no `governed_exempt`.
3. `test_the_live_migration_write_is_attributed` — **fails on the CLASSIFICATION assert, NOT the
   anti-vacuity assert.** The observed write was:
   `[('run_query','UPDATE',('loremaster/loremaster/principals.py','_migrate_memory_scope'))]`
   → the observer's reach GENUINELY extends to principals and it SAW the migrate write originating in
   `_migrate_memory_scope` (the exact coverage the cold audit found missing). The RED is purely the
   missing exempt token. **Anti-vacuity CONFIRMED empirically** — this is the load-bearing claim the
   whole both-ways instrument rests on, and it is not vacuous.

## §P1 — WRONG-BUILD BATTERY (the highest-value probe): every build RED-for-the-right-reason

Nine wrong builds, each applied in the provenance-asserted scratch, each restored after. NONE survived.

| # | wrong build (the seductive/plausible error) | pin(s) that RED | verdict |
|---|---|---|---|
| **M1a** | **RELOCATED HIDDEN CONSTANT** — scan a FILE hand-list `[local.py, principals.py]` (CLOSES #446 by adding principals, but the reach is a hand-list) | `test_a_governed_write_in_any_member_grows_the_reach…` (derives `[]` under `repo_root=tmp_path`) | **CAUGHT** ✓ |
| **M1b** | RELOCATED at the ROOTS — `derive_member_source_roots` returns only loremaster | `…_scan_roots_are_derived_from_workspace_members_not_a_hand_list` **AND** the synthetic pin | **CAUGHT ×2** ✓ |
| **M2** | TABLE HARDCODE — tree scanner forces `"memory"`, ignores the table arg | `test_scanning_for_a_different_table_finds_that_table_not_memory` | **CAUGHT** ✓ |
| **M3** | LOOSENED MATCHER (#447 regression) — revert `_raw_mutation_of_table` to the old `verb + \w` form | `TestTheScannerRejectsProseNamingAVerb` **AND** the exact-4-site pin (phantom EXPLOSION) | **CAUGHT ×2** ✓ |
| **M4** | DROPPED WHERE-guard — migrate UPDATE without `WHERE scope IS NONE` (seizure-capable) | `test_migrate_memory_scope_updates_only_none_scope_rows` | **CAUGHT** ✓ |
| **M5** | ORPHAN-ON-REMOVAL — drop `_MIGRATE_ENTRY` from the allowlist | `test_every_whole_tree_site_is_in_the_allowlist` (migrate → orphan) | **CAUGHT** ✓ |
| **M6** | classifier drops the `(file,symbol)` origin match (any borrower classifies) | `test_a_borrowed_exempt_token_is_unclassified` | **CAUGHT** ✓ |
| **M7** | OBSERVER REACH drops principals (derived-not-observed) | `…observer_patch_set_is_derived…` **AND** the live anti-vacuity assert (`observed: []`) | **CAUGHT ×2** ✓ |
| **M8** | WRONG-NAME EXEMPT — `governed_exempt("wrong-name")` (the no-op/partial builder fix) | live test reds (token mismatch); **structural pin PASSES** | **CAUGHT** ✓ |

**Two findings from the battery worth the lead's eye (not blockers — they VINDICATE the contract):**
- **M1a proves the from-truth pin is the SOLE defense against relocation.** The "known-four-sites" and
  "migrate-in-reach" pins BOTH PASS on the file-hand-list build (it derives exactly the 4 sites and
  covers principals). Only the SYNTHETIC-member end-to-end pin (`repo_root=tmp_path`, different
  filenames) catches it. That pin is load-bearing and it fires. The reach is a genuinely checked
  variable — the #446 class is closed, not relocated.
- **M3 is a vivid #447 receipt:** the loosened matcher, once let loose on the WHOLE tree, derives a
  PHANTOM EXPLOSION (`surreal_manifest.py::{upsert,reset_tier,replace_fragment}`, `messages.py::drain`,
  … 44 lines). The precision fix (verb-operand-must-BE-the-table) is not cosmetic — it is what makes a
  whole-tree scan viable at all. M8 proves the exempt token NAME is guarded by the LIVE test ALONE (the
  structural pin is name-blind) — so the live test's anti-vacuity (verified §P7) is the single guardian
  of the correct token, and it is real.

## §P1b — QUANTIFIER TABLE (∀-over-inputs vs guarded-by-failure-mode)

| invariant | classification | receipt |
|---|---|---|
| L1 deny-by-default: every derived tree-site ∈ allowlist | **∀** over the whole-tree derived set | M5 orphan reds; M1 relocation reds |
| L1 whole-tree reach == known 4 (grows-and-reds) | **∀** over tree files | M1a/M1b red the synthetic + roots pins |
| classifier: `label` OR valid-exempt, else unclassified | **∀** over observed writes (ONE uniform rule) | M6 borrowed reds; M8 wrong-name reds; 4 controls both directions |
| both-ways: observed-not-classified → RED | **∀** (uniform rule, deny-by-default) | `test_a_bare_unattributed_write_is_unclassified` (concat/unguarded escape) |
| both-ways: derived-not-observed → RED | **∀** (observer reach a checked var) | M7 reds `…patch_set_derived…` + live anti-vacuity |
| table-parametrisation (memory/message/…) | **∀** over tables | M2 hardcode reds |
| precision: prose-naming-a-verb is not a mutation | **∀** over prose f-strings | M3 loosen reds |
| migrate-in-reach (#446 close) | point-check, **backed by** the ∀ whole-tree reach pin | reverting reach to a file reds it (M1) |
| migrate `WHERE scope IS NONE` | point statement-shape on the ONE exempt site (guarded-by-seizure-mode) | M4 dropped-WHERE reds |

Every ∀ row carries an empirical receipt. The two point-checks (migrate-in-reach, WHERE-none) each
sit on ONE deliberately-singular site (the sole exempt entry) and are complemented by the ∀ reach/orphan
pins — not the guarded-by-the-failure-mode antipattern.

## §P1c — REACH TABLE (the CENTRAL attack: is each guard's reach a CHECKED variable?)

Legs run: **EMPIRICAL** for every in-tree guard (all are test infra the contract introduces).

| instrument | reach DERIVED vs hand-list | coverage a CHECKED var? | effect vs proxy | one-source / mutation | verdict |
|---|---|---|---|---|---|
| L1 whole-tree scanner (`governed_table_raw_mutation_sites_in_tree`) | **DERIVED** from `[tool.uv.workspace] members` (the `registration_sites` from-truth seam) | **YES** — `derived==known-4` reds on growth; roots pin + synthetic pin red hand-lists | **effect** (AST literal) | reuses `governed_table_raw_mutation_sites`; M1b reds roots pin | **SAFE (empirical)** |
| L2b observer patch-set (`seam_modules_for_tree_allowlist`) | **DERIVED** from allowlist files | **YES** — `…patch_set_derived…` + live anti-vacuity; M7 reds both | **effect** (resolved statement at seam, runtime) | derived from allowlist | **SAFE** (see note) |
| classifier (`classify_tree_observed_write`) | ∀ over observed writes | **YES** — 4 controls both directions + live; M6 reds | **effect** (classifies observed write) | ONE function, uniform; M6 mutation reds | **SAFE (empirical)** |
| allowlist evidencing-pin (`…entry_has_a_real_evidencing_pin`) | **DERIVED** — `_defined_test_names()` (AST, not hand-list) | YES (a deleted pin drops the entry) | effect | AST-derived | **SAFE** |
| precision matcher (`_raw_mutation_of_table`) | ∀ over statement shapes | YES — M3 reds prose + 4-site | effect | ONE matcher | **SAFE (empirical)** |
| **exempt-origin match** (`classify_…`'s `(file,symbol)==origin_site` leg) | reach = **self-contained exempt entries** — the SOUNDNESS CONDITION is a **HIDDEN CONSTANT** (assumed, verified for the ONE current entry only) | **NO ∀-check** — no pin fails when a NON-self-contained exempt entry joins the allowlist | effect | migrate-governed self-contained (AST-verified), but un-pinned ∀ | **MISSING PIN → R1** |

**The reach attack's own finding is R1.** Every derivation-reach in the instrument is a checked variable
(the #446 class is closed). But the exempt-origin match's *soundness premise* — that an exempt entry is
self-contained (literal enclosing function == seam-call frame) — is itself a hidden constant: true for
`_migrate_memory_scope` (I AST-verified: the `UPDATE {MEMORY_TABLE}…` literal AND the `run_query` call
both live in `_migrate_memory_scope`), unchecked for any FUTURE exempt entry. That is the reach class one
level up, inside the very channel #446 exists to harden. The design independently ruled it (step 6 R1).

*Observer note (not a blocker):* `observe_governed_table_writes` hard-codes `local_mod`/`governed_mod`
as DEFAULT patch targets, then unions the DERIVED `extra_modules`. The defaults are redundant with the
derivation (both modules are also allowlist-file modules) and the checked channel is the derived one
(`test_the_observer_patch_set_is_derived_from_the_allowlist` + M7). The named-module assertions spot-check
`principals`+`local`; a NEW allowlist file's module joins the observer BY the derivation automatically.
Acceptable — coverage is derived, not hand-listed.

## §MISSING-PINS — the two step-6 riders the contract does not carry (verdict driver)

Both are riders design step 6 (`3aea565`, 2026-09-01 14:09) ADDED when it blessed the both-ways reading —
**4 minutes AFTER** the contract commit `194f3c8` (14:05). So this is *the ruling moved*, not author
negligence — but the design AT HEAD requires them and the contract AT HEAD lacks them, and *no contract
revision skips the adversary* (CLAUDE.md). Neither is a CURRENT false clear; both are exactly the dropped-
rider class this repo bleeds from ("THE RIDER IS PART OF THE RULING" / "FILING A RULE DOES NOT INSTALL IT").

**R1 (primary) — the exempt-entry self-containment validity pin.**
- *The test that should exist:* `test_every_exempt_allowlist_entry_is_self_contained` — for each
  `TreeWriteAllowlistEntry` whose `exempt_name is not None`, assert the entry's L1-derived literal site
  == its seam-call site (buildable with the existing `function_calls_named`: the literal's enclosing
  function `entry.site.function` must ALSO call the store seam `run_query`/`execute_transaction` in
  `entry.site.file`). Fails CLOSED if the derived literal function is not the seam-call function.
- *The defect it catches:* a FUTURE non-self-contained exempt candidate (63b/64 — a fragment-builder
  whose literal is in `_build_X` but whose seam call fires from `_drain`) makes the origin match
  `(entry.site) == origin_site` UNSOUND. Without R1's pin it either false-positives at runtime (a
  confusing RED with no design signal) or is dodged by a mis-sited allowlist entry; with it, the design
  question surfaces at validity time. Design R1, verbatim: *"pin the premise … so a future
  non-self-contained candidate REDS the check … instead of the match being quietly loosened."*
- *Not a current false clear:* migrate-governed IS self-contained (AST-verified), and the conjunction of
  L1's derived site (`_migrate_memory_scope`) + the live test's origin assertion (`_migrate_memory_scope`)
  incidentally verifies it for the one entry that exists. R1 makes the premise a CHECKED VARIABLE ∀
  exempt entries rather than a hidden constant.

**R2 (secondary) — the #138-class hand-set-label accepted bound is named in NO instrument docstring.**
- *What is missing:* `classify_tree_observed_write`'s classification `if observed.label is not None:
  return True` accepts ANY write that hand-sets `write_guard(...)` without calling `guarded_write`. This
  is an ACCEPTED bound under the gate's threat model (the honest developer, not the hostile author). Grep
  of the classifier/observer/`write_guard` docstrings: **0 hits** for the bound or its threat model.
- *The requirement (design R2 + "A GATE NEEDS A THREAT MODEL — WRITE DOWN WHO IT IS FOR"):* NAME the
  bound + threat model in the instrument docstring (`classify_tree_observed_write` or
  `observe_governed_table_writes`), "never closed by false positives." A named-bound rider, not a pin —
  lower priority than R1, but a real dropped rider.

## §PKG — package survey diff (P-PKG)
Independent table built before reading the author's:
- `governed_exempt`/`active_exempt` → `contextvars.ContextVar` + `contextlib.contextmanager` (stdlib).
  The shipped `write_guard` IS this exact pattern; a third-party context library is strictly worse and
  breaks the ONE-IMPLEMENTATION mirror. Verdict: **stdlib (no package gap)**.
- whole-tree scan / stack-walk → stdlib `ast`, `tomllib`, `sys._getframe`. `libcst` exists but is heavier
  and would fork the existing `governed_table_raw_mutation_sites` idiom. Verdict: **keep (one impl)**.
DIFF vs author: author reported `none — no new production mechanism`. **AGREED** — no bespoke verdict with
an empty read-column; the one mechanism is stdlib mirroring a shipped primitive.

## §RESIDUALS — every item, an individual verdict
- **From-truth whole-tree reach (L1)** — DERIVED + checked; M1a/M1b red both catchers. **SAFE.**
- **Both-ways cross-check** — sound (design-blessed step 6); observed-not-classified + derived-not-observed
  each red-proven (bare-unattributed control / M7). No false-positive on fragment-builders (label channel;
  satisfiability GREEN). **SAFE.**
- **migrate-governed triple** — WHERE-none (M4), orphan-on-removal (M5), uniform L2 rule, wrong-name (M8)
  all caught. Self-contained (AST-verified). **SAFE, except the R1 ∀-premise → §MISSING-PINS.**
- **Table-parametrisation** — M2 caught. **SAFE.**
- **#447 precision fix** — M3 caught (prose + 4-site); the 3 local.py sites + #444 bound + docstring
  exclusion preserved (reference build's `_63a_iv`/`_bounds_63a_iv` → GREEN). **SAFE.**
- **Observer default-target hard-code (`local_mod`/`governed_mod`)** — redundant with the derived channel;
  the checked reach is derived. **SAFE (noted).**
- **Exempt contextvar leak (lifecycle)** — no pin forces `governed_exempt` to reset the contextvar. NOT
  exploitable for a false clear: even a leaked token fails the origin `(file,symbol)` match for any write
  firing from a different frame (verified by the M6/M8 logic + the classifier's origin leg). Reference
  build mirrors `write_guard`'s `finally: reset` so it does reset. **SAFE (noted; not a blocker).**
- **DRY: `governed_exempt` vs `write_guard`** — contract pins no internal structure, so a clone would
  pass. A builder/cold-audit concern (mirror, don't clone the contextvar plumbing). **NOTED — for builder.**
- **R1 exempt self-containment ∀-pin** — **MISSING (verdict driver).** §MISSING-PINS.
- **R2 hand-set-label threat-model bound** — **MISSING (docstring rider).** §MISSING-PINS.
- 63a-iv local.py coverage / #439 / corpse / item-5 / F-B — NOT regraded (brief instruction);
  reference build shows them GREEN and untouched. **SAFE (out of this grade's frame).**

## §METHOD — instruments (deliverables; scratch is disposable by design)
- Scratch: `./scripts/scratch_copy.sh /tmp/cav63av_adv_2302454` — provenance-asserted
  (`loremaster.__file__` inside the copy). All 9 mutations applied by inline `python3` `str.replace`
  edits (transcribed in §P1's table + the session log), each restored from a pristine reference-build
  backup (`/tmp/ref_{governed_contract,test63av,principals,governed}.py`). No repo file was mutated.
- RED-at-HEAD, satisfiability, and every mutation ran against TEST store `ws://127.0.0.1:18000` (NEVER
  :18500) via the `migration_world` fixture — verified live.
- Self-containment probe (AST): pasted in the session (`_migrate_memory_scope` has the literal UPDATE AND
  the `run_query` call → self-contained=True). R1/R2 absence: narrow greps returned no matching pin/bound.

## VERDICT: **CONTRACT INSUFFICIENT**
Not for a defect in what the contract DID — every wrong build in this wave's scope is caught, the core
both-ways reading is design-blessed, and satisfiability holds. INSUFFICIENT because the DESIGN moved
(`3aea565`, step 6) 4 minutes after the contract and now requires two riders the contract does not carry:
**R1 (the exempt-entry self-containment validity pin — the reach class one level up, in the exempt
channel)** and **R2 (the #138-class hand-set-label bound named in the instrument docstring)**. Route both
to a contract revision before the builder; R1 is buildable via the existing `function_calls_named`.
