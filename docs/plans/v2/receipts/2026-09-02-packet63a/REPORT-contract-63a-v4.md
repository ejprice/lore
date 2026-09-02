# REPORT-contract-63a-v4 — FOLD: pin the R4 accepted bounds (#449, pin-the-miss) + fix the base-3 false-gate docstring

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **state:** done
- **deviations:** none
- **Packages considered:** none — no mechanism specified (tests + docstrings only; no production/library code).
- **Reuse ledger:** none — no new reusable symbols. The two pins reuse existing substrate symbols
  (`exempt_frame_raw_memory_mutations`, `_raw_mutation_of_table`, `_mutation_verb_for_table`,
  `TreeWriteAllowlistEntry`, `TreeMutationSite`, `MEMORY_TABLE`); the docstring edits add prose only.
- **Graded:** n/a — this is a CONTRACT-AUTHORING fold, not a verdict pass over another agent's artifact.
  Base for the fold: HEAD `a48c8a2` at spawn. Committed at `1e1d485`.
- **decisions-needed:** none new. (The R4 disposition was operator-ruled OPTION A in finding #449; the
  63b runtime root-fix is task 571ef1a. No new fork surfaced.)
- **count:** `test_memory_enforcement_63a_v.py` → **20 passed / 4 failed** (baseline before fold was
  18 passed / 4 failed). The 2 new pin-the-miss pins are GREEN (the bounds exist today); the base 4 RED
  are UNCHANGED (governed_exempt unbuilt, migrate-enters-exempt unwired, live-migration unattributed,
  R2 docstring not-yet-naming — all still owned by the base build).
- **gates:** `uv run ruff check .` → All checks passed; `bash scripts/typecheck.sh` → exit 0.
- **receipt POINTERS:** the two pins → `test_memory_enforcement_63a_v.py::TestTheAcceptedF5BoundsArePinned`
  (`test_r4a_the_shape_leg_matches_where_scope_is_none_by_substring`,
  `test_r4c_the_raw_mutation_verb_set_is_a_bounded_enumeration`); the base-3 docstring fix →
  `test_memory_enforcement_63a_v.py::…::test_migrate_memory_scope_updates_only_none_scope_rows` (docstring
  only, assertion UNCHANGED); the bound-naming → `_governed_contract.py` docstrings of
  `_raw_mutation_of_table`, `_mutation_verb_for_table`, `exempt_frame_raw_memory_mutations`.

## WHAT THIS FOLD IS (and is NOT)
Per lead-63's brief relaying the operator's **OPTION A** disposition of finding **#449**: adversary-63a-v3's
R4 hunt found TWO reach-recessions that launder past R1+R2+R3 (§R4-a shape-leg SUBSTRING, §R4-c verb-set
HIDDEN CONSTANT). The operator ACCEPTED both as BOUNDS in 63a and DEFERRED the runtime root-fix to 63b
(task 571ef1a). My job: **contract only, NO build** — PIN the two accepted bounds (pin-the-miss), NAME
them in the F5 instrument docstrings, and FIX one false-gate docstring. I did **not** try to CLOSE R4
(that is the 63b runtime root-fix) and did **not** build `governed_exempt` / migrate-wrap / R2 docstring
(the separate base build). I did not touch R1/R2/R3 or the 63a-iv coverage.

## 1. PIN-THE-MISS — the two accepted R4 bounds (GREEN today; RED-when-closed)
New class `TestTheAcceptedF5BoundsArePinned` in `test_memory_enforcement_63a_v.py`. These are pin-the-miss
bounds (CLAUDE.md WHEN YOU CANNOT CLOSE A HOLE, PIN IT), **not** discriminating security pins: each asserts
the bound EXISTS TODAY, carries the message *"KNOWN ACCEPTED BOUND #449 … F5 is a static HONEST-DEVELOPER
net; this substring/verb-set limitation is the #138 hostile-author class F5 does not defend; the runtime
root-fix is 63b (task 571ef1a). If you closed this deliberately (the 63b root-fix), DELETE this pin + the
bound docstring and say so."*, and pairs it with a probe-honesty POSITIVE CONTROL (CLAUDE.md PKT-28 C1) so
the GREEN witness is a genuine laundering path, not a blind matcher.

- **R4-a (shape-leg SUBSTRING bound):** builds the OR-extended seizure `UPDATE {MEMORY_TABLE} SET scope =
  $scope WHERE scope IS NONE OR scope = $victim` as an exempt frame's ONE co-located mutation, runs it
  through the **real** R3 extractor `exempt_frame_raw_memory_mutations`, and asserts (i) it is ONE
  statement (the R3 count leg would pass) and (ii) it CONTAINS the `WHERE scope IS NONE` substring that
  the R3 shape leg + base-3 pin match by — so the seizure is classified as the allowlisted shape (the
  bound is real). Positive control: a no-`IS NONE` seizure `WHERE scope = $victim` does NOT match the
  substring (the matcher is not blind). RED-when-closed: anchored on `exempt_frame_raw_memory_mutations`
  (reds if 63b reshapes/removes it) + the deliberate-deletion instruction.
- **R4-c (verb-set HIDDEN CONSTANT bound):** asserts `_raw_mutation_of_table` (static extractor, reused by
  the whole-tree scan AND `exempt_frame_raw_memory_mutations`) AND `_mutation_verb_for_table` (runtime
  observer) both return **None** for `INSERT … ON DUPLICATE KEY UPDATE` / `CREATE` / `RELATE` memory
  writes — invisible end-to-end (extractor → never derived; observer → never recorded → deny-by-default
  cannot fire). Positive control: an in-set `UPDATE type::record('memory',…)` IS seen by both (== "UPDATE")
  — a genuine verb-set miss, not a blind probe. RED-when-closed: directly references the two verb-set
  functions, so it reds the day 63b makes mutation-detection a PROPERTY (recognising the exotic verbs).

Both GREEN at HEAD confirms the bounds are real TODAY (adversary-63a-v3 §R4-a/§R4-c; the wrong build went
22 passed / 0 failed on the full 63a-v suite; INSERT..ON DUPLICATE KEY UPDATE is a real seizure —
surrealql-tests 5776).

## 2. NAMED-BOUND docstrings — "A GATE NEEDS A THREAT MODEL — WRITE DOWN WHO IT IS FOR"
Added a `⚠ NAMED ACCEPTED BOUND (finding #449 …)` clause to the three F5 instrument docstrings in
`_governed_contract.py`, each naming F5's HONEST-DEVELOPER threat model, the #138 HOSTILE-AUTHOR class as
out of scope, the 63b root-fix (task 571ef1a) as the re-open, and the pin that reds when it is closed:
- `_raw_mutation_of_table` — R4-c static verb-set bound.
- `_mutation_verb_for_table` — R4-c runtime verb-set bound.
- `exempt_frame_raw_memory_mutations` — R4-a shape-substring bound (the shape leg its callers apply).

⚠ I deliberately did **NOT** put the bound-naming in `classify_tree_observed_write.__doc__`: that docstring
is owned by the R2 pin (`test_classify_tree_observed_write_docstring_names_the_hand_set_label_bound`),
which must stay RED until the base build adds the R2 tokens (`guarded_write`/`honest`/`138`). Verified R2 is
still RED after my edits (I did not turn it green). The brief's "and/or the scanner" clause blesses the
scanner homes; only the R2 pin reads a `_governed_contract.py` docstring, so these edits trip no other pin
(checked: `grep -rn '__doc__' loremaster/tests/` — only R2 reads a `_governed_contract` docstring).

## 3. BASE-3 FALSE-GATE DOCSTRING — corrected to match the assertion
`test_migrate_memory_scope_updates_only_none_scope_rows`'s old docstring promised *"Reddens the day the
migrate grows a write that touches a NON-NONE-scope row"* — a FALSE GATE (adversary-63a-v3 §BASE3): the
assertion is FIRST-MATCH (`_migrate_backfill_update_statement`) AND SUBSTRING (`re.search(WHERE scope IS
NONE)`), so it does NOT red on (a) a co-located SECOND seizure after the blessed write (first-match shadows
it) nor (b) an OR-extended FIRST statement (substring still present). Corrected the docstring to state what
it ACTUALLY checks (first-match substring presence), point at the true ∀-guard for half (a) (the R3 count
leg) and the #449 R4-a pin for half (b), and name the threat model. **The assertion is UNCHANGED — docstring
only** (per brief: "Do NOT weaken the assertion — only correct the docstring to match it"). base-3 stays
GREEN.

## RECEIPTS
Baseline (before fold, HEAD `a48c8a2`): `4 failed, 18 passed`.
After fold:
```
loremaster/tests/test_memory_enforcement_63a_v.py  → 4 failed, 20 passed in 4.26s
  (RED, unchanged: test_the_governed_exempt_mechanism_is_built,
   test_migrate_memory_scope_enters_governed_exempt, test_the_live_migration_write_is_attributed,
   test_classify_tree_observed_write_docstring_names_the_hand_set_label_bound)
  (new GREEN: TestTheAcceptedF5BoundsArePinned::test_r4a_…, ::test_r4c_…)
uv run ruff check .   → All checks passed!
bash scripts/typecheck.sh → exit 0 (all members OK: lorescribe/loresigil/loremaster/skills/docs/eval/scripts/shellcheck)
```

## FLAGS / FORKS
None new. The R4 design escalation is already ruled (OPTION A, #449); the 63b runtime root-fix (property-
based mutation detection + statement-scoped exemption, for all governed tables) is task 571ef1a with the
named re-open trigger (63b F5 parametrization, OR the first time migrate-governed / any exempt frame
becomes member-reachable or served). NEXT per brief: the base build (governed_exempt + migrate wrap + R2
docstring), then the cold-audit CLOSE of 63a.

## WRITABLE SET touched
- `loremaster/tests/test_memory_enforcement_63a_v.py` (new pin class + base-3 docstring fix)
- `loremaster/tests/_governed_contract.py` (three F5 instrument docstrings — bound-naming only, no logic)
