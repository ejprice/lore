# REPORT-contract-63a-v3 — FOLD R3 (exempt-frame single-shape ∀-pin, finding #448)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done** — R3 folded (contract only, NO build), gates green, one concern committed.
- **What R3 is:** a TEST-INFRA INVARIANT (GREEN at fold), NOT a production hook. The real
  `_migrate_memory_scope` holds EXACTLY its one `WHERE scope IS NONE` UPDATE today, so the pin is
  GREEN now and REDS the day the exempt frame grows a second/seizure write — forcing re-adjudication
  before the laundering can ship. Mirrors R1 (live invariant + synthetic discrimination).
- **The defect closed:** a SECOND same-verb `UPDATE {memory} SET scope … WHERE scope = <owned>`
  (a seizure) co-located in `_migrate_memory_scope`'s exempt frame laundered past all 20 pins —
  L1 collapses two same-verb UPDATEs to one `(file,function,verb)` site, the base-3 WHERE-none pin
  is first-match (shadowed by the blessed write), and the exempt token classifies the seizure
  (co-located ⇒ origin match holds by construction).
- **Built:** extractor `exempt_frame_raw_memory_mutations` (collect-ALL statement shapes in the
  exempt frame — never verb-collapsed, never first-match; reuses the shared shape primitives) +
  `TestTheExemptFrameHoldsOnlyItsGuardedMutation` (2 tests: the live ∀-pin + the same-verb-UPDATE
  discrimination mutation-proof). §R3-FOLD.
- **Count:** `test_memory_enforcement_63a_v.py` → **4 failed / 18 passed (22 collected)** at
  `8da0004`+fold. The 4 RED are the UNBUILT production mechanism (builder's GREEN target),
  unchanged from HEAD's 4R/16G; my fold added +2 GREEN test-infra pins. §COUNT.
- deviations: **none.**
- `Packages considered:` stdlib `ast` (the extractor is a pure AST predicate) — **keep**; reuses
  in-tree `_statement_shape`/`_raw_mutation_of_table`/`_enclosing_functions`/`_docstring_node_ids`
  (ONE-IMPLEMENTATION). No third-party candidate exists for a repo-specific SurrealQL statement-shape
  scan; no gap. §PKG.
- `Reuse ledger:` 1 new symbol, dispositioned (HAND-ROLLED, reason cited). §DRY.
- `Graded:` built against `8da0004` · HEAD-at-report: `8da0004` · SAME. (This report renders no
  verdict on another agent's artifact — it re-derives the count/HEAD it acts on.)
- decisions-needed: **ONE (flag to lead-63)** — the base-3 pin
  `test_migrate_memory_scope_updates_only_none_scope_rows` has a FALSE-GATE docstring (promises a
  NON-NONE-scope check its first-match assertion does not perform; adversary-63a-v2 §R3 failure 2).
  R3 now DELIVERS that promise, so the base-3 pin is redundant, but its docstring still over-claims.
  Out of my writable set (brief: "do NOT touch base-3 pins"). Fix-now vs defer is the lead's call.
  §FLAGS.
- receipt POINTERS: mechanism + invariant-vs-hook → §R3-FOLD; discrimination + real-frame splice →
  §MUTATION-PROOF; RED→GREEN + gate tails → §COUNT; reuse → §DRY; forks/bounds → §FLAGS; pkg → §PKG.

---

## §R3-FOLD — what was built, and why it is a TEST-INFRA INVARIANT (not a production hook)

**The gap (adversary-63a-v2 §R3 / finding #448), verbatim shape:** the both-ways classifier
(`classify_tree_observed_write`) blesses the WHOLE exempt frame — any mutation running under the
`migrate-governed` token whose runtime `origin_site == (entry.site.file, entry.site.function)` is
classified True, and a write co-located in `_migrate_memory_scope` has that origin BY CONSTRUCTION.
R1 pinned that the origin match is SOUND (literal site == seam-call site). R3 is the SIBLING premise
R1 left open: the frame's raw-mutation SET was still a HIDDEN CONSTANT (assumed = the one blessed
`WHERE scope IS NONE` write). A honest developer extending the backfill with a second
`UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope = $victim` (a seizure of an owned row) launders
past ALL layers — the reach-as-hidden-constant class ONE LEVEL DOWN, inside the exempt channel.

**The extractor** — `_governed_contract.py::exempt_frame_raw_memory_mutations(entry, *, source,
table=MEMORY_TABLE, table_const_hint="MEMORY_TABLE") -> list[str]`. Walks every AST
`Constant`/`JoinedStr` whose enclosing function is `entry.site.function`, reconstructs its
statement SHAPE (`_statement_shape`), and collects it iff `_raw_mutation_of_table` matches — a LIST
of statement shapes, **never** a `(function, verb)` set (which collapses two same-verb UPDATEs to
one — the exact L1 door R3 walks) and **never** first-match. It reuses the SAME statement-shape
primitives as the whole-tree scan, so the #444 concatenation static bound and the docstring/prose
exclusion are inherited, table-parametrised (ONE implementation; 63b/64 reuse).

**The pin** — `test_memory_enforcement_63a_v.py::TestTheExemptFrameHoldsOnlyItsGuardedMutation`:
- `test_the_exempt_frame_holds_exactly_its_one_none_scope_guarded_mutation` (the adversary's exact
  name) — ∀ exempt allowlist entries (anti-vacuity ≥1): the entry's frame holds **EXACTLY ONE** raw
  memory mutation (count leg — catches a second write of ANY shape, incl. a benign second WHERE-none,
  forcing re-adjudication) **AND** that one is `WHERE scope IS NONE`-restricted (shape leg — catches
  a seizure). Both legs fire on the adversary's seizure construction; either alone excludes it.
- `test_the_single_shape_pin_reds_an_exempt_frame_with_a_second_seizure_write` — the discrimination
  mutation-proof (§MUTATION-PROOF).

**INVARIANT-vs-HOOK — it is a TEST-INFRA INVARIANT, GREEN at fold.** The real `_migrate_memory_scope`
already holds exactly one `WHERE scope IS NONE` UPDATE (verified: the `_scope_count` calls are SELECTs
in a *different* function; the refusal-reason f-string carries no verb→table adjacency; only the
`statement=f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE"` matches). So the pin needs
NO production change — it is GREEN now and its job is to RED the day the frame grows. This mirrors
R1's live invariant exactly: the soundness premise is a CHECKED VARIABLE, surfaced at
allowlist-validity time, so a future non-compliant frame reds the pin instead of quietly laundering.

## §MUTATION-PROOF — the pin discriminates (synthetic + REAL-frame splice)

**Synthetic discrimination (shipped as the test, mirrors R1's construction).** Two synthetics, SAME
frame name (`_do_write`) AND SAME exempt token (`second-write-frame`) — the only difference is the
write count:
- non-compliant: `_do_write` with TWO co-located SAME-VERB UPDATEs (blessed `WHERE scope IS NONE`
  + seizure `WHERE scope = $victim`) → extractor returns **2** (so the count leg reds AND the seizure
  fails the WHERE-none ∀-leg).
- positive control: `_do_write` with ONE `WHERE scope IS NONE` UPDATE → extractor returns **1**,
  WHERE-none → passes.

The SAME-token/SAME-name design CATCHES a wrong extractor that (a) special-cases the token/function,
(b) returns a CONSTANT one-element list, (c) FIRST-matches, or (d) verb-COLLAPSES the two same-verb
UPDATEs (the exact L1 bug). ⚠ The second write is a SAME-VERB `UPDATE` deliberately: the adversary's
P0 showed a DIFFERENT verb (DELETE) already reds at L1 (the derived set grows); the same-verb UPDATE
is the one L1 collapses — the whole of R3. `pytest …::TestTheExemptFrameHoldsOnlyItsGuardedMutation
-v` → **2 passed**.

**REAL-frame splice (a stronger receipt — the pin discriminates on production source, not just a
synthetic; in-memory only, NO repo file mutated).** Reading the real `principals.py`:
```
REAL frame mutations: ['UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE']
REAL -> exactly 1 WHERE-none: PASS (live pin GREEN)
SEIZURE-spliced frame count: 2 -> ['UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope = $victim',
                                   'UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE']
SEIZURE splice -> 2 stmts, one NOT WHERE-none: live pin would RED (count AND shape legs). PASS
```
The instrument (pasted so the claim is re-runnable): read `principals.py`, run
`exempt_frame_raw_memory_mutations` on a `_migrate_memory_scope`/`migrate-governed` entry (expect
`[1]`, WHERE-none); string-splice a second `run_query(statement=f"UPDATE {MEMORY_TABLE} SET scope =
$scope WHERE scope = $victim")` co-located in the frame; re-run (expect `len==2`, one not WHERE-none).
This is exactly the honest-developer seizure the adversary described — and the live pin now reds it.

## §COUNT — RED→GREEN receipts + gate tails (built at `8da0004`)

- `test_memory_enforcement_63a_v.py` → **4 failed, 18 passed** (5.85s). Before the fold (HEAD
  `8da0004`, per adversary-63a-v2 §P7): 4 failed / 16 passed. My fold: **+2 GREEN** test-infra pins,
  4 RED unchanged. The 4 RED are the UNBUILT production mechanism (the builder's GREEN target):
  `test_the_governed_exempt_mechanism_is_built`, `test_migrate_memory_scope_enters_governed_exempt`,
  `test_classify_tree_observed_write_docstring_names_the_hand_set_label_bound`,
  `test_the_live_migration_write_is_attributed`.
- Both new R3 tests GREEN: `…::TestTheExemptFrameHoldsOnlyItsGuardedMutation` → **2 passed** (0.33s).
- **No regression:** `test_memory_enforcement_63a_iv.py` + `test_memory_enforcement_bounds_63a_iv.py`
  → **12 passed, 0 failed** (8.91s) — matches the adversary's baseline (12/0), untouched.
- `uv run ruff check .` → **All checks passed!**
- `bash scripts/typecheck.sh` → **exit 0** (`lorerunes/lorescribe/loresigil/loremaster/skills/
  docs·eval/scripts` all OK; shellcheck OK).

## §DRY — reuse ledger (1 new reusable symbol)

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `exempt_frame_raw_memory_mutations` | "extract all SurrealQL mutation statements co-located in one function, per-function statement collector (not verb-collapsed)" | `test_keeps_store.py::_method_has_mutating_statement` (a BOOLEAN any-mutation predicate keyed on the first whitespace token, different module/purpose — not table-targeted, not a shape collector, no reuse of the shared shape primitives) | **HAND-ROLLED** — the closest in-tree symbol, `governed_table_raw_mutation_sites`, verb-COLLAPSES to `frozenset[MutationSite]` (that collapse IS the R3 defect); `_method_has_mutating_statement` answers a different question. The new extractor **REUSES** `_statement_shape`/`_raw_mutation_of_table`/`_enclosing_functions`/`_docstring_node_ids` (the shared statement-shape scan) and differs from the whole-tree scanner in exactly the axis R3 turns on: it aggregates STATEMENTS (list), never sites. |

## §FLAGS — one fork for lead-63 + one documented bound

1. **FORK (fix-now vs defer, lead's call) — base-3 FALSE-GATE docstring.** The base-3 pin
   `test_migrate_memory_scope_updates_only_none_scope_rows` (via `_migrate_backfill_update_statement`,
   first-match) has a docstring promising *"Reddens the day the migrate grows a write that touches a
   NON-NONE-scope row"* — which its FIRST-MATCH assertion does NOT perform (a blessed WHERE-none write
   shadows a co-located seizure; adversary-63a-v2 §R3 failure 2, a CLAUDE.md FALSE-GATE). R3 now
   DELIVERS that promise, so the base-3 pin is redundant but its docstring still over-claims. My brief
   says "do NOT touch base-3 pins", so I did not edit it. Recommendation: a one-line docstring
   correction on the base-3 pin (point it at the R3 pin as the true ∀-guard) — cheap, closes the
   over-claim; OR leave it (R3 covers the behaviour). **Lead-63 owns the call.**
2. **DOCUMENTED BOUND (named re-open trigger) — 63b/64 shape parametrisation.** The R3 pin's shape
   leg hardcodes `WHERE scope IS NONE` (migrate-governed's allowlisted shape) and its count leg
   asserts exactly one. For 63a this is correct (one exempt entry, one adjudicated write). For a
   FUTURE 63b/64 exempt entry with a DIFFERENT allowlisted shape or >1 adjudicated write, the pin
   fails CLOSED (RED → re-adjudicate) — the SAFE direction and the design's stated intent ("surface
   the design question instead of the match being quietly loosened"). Same property as the R1 pin
   (reused by 63b/64). RE-OPEN TRIGGER: any 63b/64 exempt entry whose allowlisted write shape is not
   `WHERE scope IS NONE`, or whose frame legitimately holds >1 adjudicated mutation — at which point
   the shape/count legs must be parametrised per-entry (design step 5, "per-table classification
   registries beside the code they classify").

## §PKG — package survey (P-PKG)
- `exempt_frame_raw_memory_mutations` → stdlib `ast` via the in-tree shared primitives (reuse, not a
  package). No third-party library does a repo-specific SurrealQL statement-shape scan keyed to this
  project's `MEMORY_TABLE`-constant idiom; a general Python-AST helper (e.g. `libcst`) is strictly
  worse than reusing the module's own scan and breaks the ONE-IMPLEMENTATION mirror. **keep (stdlib
  + in-tree reuse); no gap.** No new production mechanism specified.

## §NEXT
The `contract-adversary` grades this fold and HUNTS R4. Per the operator's ruling (relayed in my
brief): if it finds an R4 reach-recession, that triggers a DESIGN escalation (exempt-mechanism
frame→statement scope), NOT another fold.
