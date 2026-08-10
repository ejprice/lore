# REPORT — reviser-asub-5 (A-SUB CONTRACT reviser, §12.7 convergence: skip-set → checked variable + #349 pinned bound)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **State:** done (contract tests only; edited ONLY `loremaster/tests/test_ast_reach_helpers.py`).
- **Delivered §12.7's two required parts** (design `docs/plans/v2/design/2026-08-09-defect-class-prevention.md`
  §12.7.2 + §12.7.3):
  1. **SKIP-SET → CHECKED VARIABLE** — `_ASUB_PARSE_SKIP` (evidence-reason per entry, mirrors the
     `_ALLOWED_WHOLE_TREE_CLONE_FILES` idiom) + `test_no_skip_set_file_parses_the_tree_unrouted`
     (REUSES L1's `_all_workspace_parse_sites`) + `test_the_parse_skip_allowlist_carries_no_dead_entries`
     (REUSES the dead-entry `_ALLOWED_*` idiom + `_workspace_tree_fixtures`). Plus: Layer 3's silent
     `pytest.skip` is now GATED on `_ASUB_PARSE_SKIP` membership (a fixtureless adopter can no longer
     skip SILENTLY — the exact hole delta-adversary-asub-4 flagged).
  2. **#349 PINNED BOUND** — `test_asub_nonparsing_tree_walk_is_a_KNOWN_BOUND_349` (the #137/#138
     pin-the-miss idiom): asserts A-SUB's L2 offender lint does NOT flag a non-parsing os.walk, with a
     PARSING-variant positive control, the KNOWN-BOUND #349 message, and the three named re-open triggers.
- **Threat model stated IN the instruments** (§12.7.1): A-SUB guards the PARSE; chokepoint = `compile`;
  a non-parsing tree-walk produces no AST → out of parser scope.
- **⚠ DECISION-NEEDED (1) — §12.7's backoff example reason is FACTUALLY WRONG, and I did not transcribe it.**
  §12.7.2 gives `backoff = "does not parse the tree — it is a runtime-site reach check"`. Ground-truth
  (`test_backoff_seam.py::TestNoNewHandRolledBackoff.test_no_production_module_outside_the_allowlist_exponentiates_by_a_variable`)
  shows backoff **DOES** parse the whole workspace (`_production_python_files()` → `production_sources()`
  + `ast.parse` over every production file). So do secret_typing / secret_leak_vectors / comms_footer.
  My `_ASUB_PARSE_SKIP` reasons state the TRUE classification: *"routes its whole-workspace parse through
  `parse_production_trees`; exposes NO nullary workspace-tree fixture, so Layer 3's fixture-consumer pin
  cannot drive it; sharing proven by L1's escape gate + this skip-coverage pin."* The skip-coverage pin
  ENFORCES this (a skip file that parses unrouted → RED), so the honesty is checked, not asserted. Flagged
  because it deviates from the spec's literal example text; the mechanism is unchanged.
- **⚠ DECISION-NEEDED (2) — the skip-coverage pin's REACH is the single-function shape; split-leg /
  os.walk-source-hidden private parses are a STATED BOUND, not caught here.** Per my brief's explicit
  steer (*"REUSE L1's `_all_workspace_parse_sites`"*) and the operator's *"REUSE > REINVENT, do NOT write
  a new scanner"*, the pin keys on the static ALL-set (`_parses_whole_workspace` = parse-primitive +
  whole-workspace-source-NAME in ONE function). It catches a skip file that DIRECTLY parses the whole
  workspace un-routed (e.g. secret_leak's `_production_function_names` at HEAD). It does NOT catch the
  delta-adversary survivor's split-leg factoring (source in a nullary helper) or an `os.walk`+`ast.parse`
  build (source name not in the whole-workspace vocab) — those are recorded by L1's runtime guard but its
  escape INVARIANT filters them by return value, so they are the #349 pinned-bound tail + INSTRUMENT 0's
  reach-attack. This is the honest bound the operator's "pin, don't chase" ruling accepts; building the
  source-following detector is the round-6 scanner that was overruled. Stated in the pin's docstring.
- **Packages considered:** none — stdlib `ast` only, all reuse (`_all_workspace_parse_sites`,
  `_workspace_tree_fixtures`, `_whole_tree_parse_offenders_in`, `_ALLOWED_WHOLE_TREE_CLONE_FILES` idiom,
  the #137/#138 pin-the-miss idiom). No new scanner. Verdict: bespoke-minimal, extending §12 instruments.
- **Graded:** N/A (I authored contract tests; I render no verdict on another artifact). Contract graded
  against working tree at HEAD `2fe81ba` + the uncommitted `test_ast_reach_helpers.py` I extended.
- **Satisfiability:** re-derived in a scratch tree — see §Satisfiability below. Provenance printed.
- **Receipt pointers:** §Design · §What-changed (symbols) · §Satisfiability · §Decisions-needed.

_(Body below.)_

## §Design — what §12.7 asked for, and how each part is built

§12.7 (my verbatim spec) has TWO required parts + a threat model. Ground truth read directly
(the four skipped adopters' real source), because §12.7's own backoff example was based on an
incomplete read (see Decision-needed 1).

### Part 1 — the SKIP-SET is a CHECKED VARIABLE (§12.7.2)

The Layer-3 fixture-consumer rider
(`TestSharingProvenByMutation.test_each_real_fixture_consumer_reddens_when_the_shared_parser_is_dropped`)
skips adopters with no nullary workspace-tree `@pytest.fixture`. Before §12.7 that skip was a
bare `pytest.skip` — the delta-adversary-asub-4 hole (a fixtureless adopter whose private scan no
layer asserts on passes 44/4-skip byte-identical). Promoted to allowlist-the-safe:

- **`_ASUB_PARSE_SKIP`** — `{file: evidence-reason}` for the four fixtureless adopters
  (`test_backoff_seam.py`, `test_secret_typing.py`, `test_secret_leak_vectors.py`,
  `test_comms_footer.py`). Each reason states the TRUE classification (routes its whole-workspace
  parse; no nullary fixture; sharing proven by L1 + the skip-coverage pin) — mirrors the
  `_ALLOWED_WHOLE_TREE_CLONE_FILES` evidence-reason idiom.
- **Layer 3's skip is now GATED** on `_ASUB_PARSE_SKIP` membership: `assert adopter in
  _ASUB_PARSE_SKIP` BEFORE `pytest.skip`. A new fixtureless adopter can no longer skip silently —
  it reddens with a named disposition (give it a fixture, or add it to the skip allowlist with a
  reason). This is the "no silent third category" closure.
- **`TestTheParseSkipSetIsACheckedVariable.test_no_skip_set_file_parses_the_tree_unrouted`** — the
  checked variable. REUSES L1's `_all_workspace_parse_sites` (the ALL-set, no new scanner): assert
  NO `_ASUB_PARSE_SKIP` file appears as a whole-workspace parse SITE. A skip file that DIRECTLY
  parses the whole workspace un-routed (parse-primitive + whole-workspace source in ONE function)
  → RED (mis-classified adopter, or its "routes its parse" reason is false). Anti-vacuity: the
  ALL-set must be non-empty. Positive control (build-independent):
  `test_the_skip_coverage_pin_would_flag_a_skip_file_that_parses` proves the discrimination logic
  fires + a negative control (the sanctioned parser's home is not flagged).
- **`test_the_parse_skip_allowlist_carries_no_dead_entries`** — the dead-entry pin (the
  `_ALLOWED_WHOLE_TREE_CLONE_FILES` / `test_the_allowlist_carries_no_dead_entries` idiom + REUSES
  `_workspace_tree_fixtures`): a skip entry whose file is gone, is no longer a declared adopter, or
  now exposes a nullary workspace-tree fixture (Layer 3 would drive it) → RED, self-cleaning.
- **`test_the_skip_set_is_non_empty_and_scoped_to_the_migration_set`** — anti-vacuity + scoping.

Together these three guards partition `_MIGRATION_SET` with no silent third category:
ADOPTERS-WITH-A-FIXTURE (Layer 3 drives) ∪ `_ASUB_PARSE_SKIP` (checked not to parse un-routed) ∪
(anything else that parses → an ALL-set site / L1 escape).

### Part 2 — the NON-PARSING tree-walk is a PINNED BOUND (§12.7.3, #349)

`TestAsubNonParsingTreeWalkKnownBound349.test_asub_nonparsing_tree_walk_is_a_KNOWN_BOUND_349` —
the #137/#138 pin-the-miss idiom (also the `test_backoff_seam.TestKnownBoundsOfThisInstrument`
sibling). A synthetic non-parsing `os.walk` scan (walks the tree, checks `.py` filenames, NEVER
`ast.parse`/`compile`): asserts it is genuinely a walk (`walk` ∈ call names) AND genuinely
non-parsing (no parse primitive → structurally invisible to L1's `compile` chokepoint), and that
A-SUB's L2 offender lint (`_whole_tree_parse_offenders_in`) does NOT flag it. POSITIVE CONTROL: the
PARSING variant (rglob + read_text + ast.parse) IS flagged — the bound is precisely "non-parsing",
not "the detector never fires". Reddens the day someone teaches the detector to catch non-parsing
walks (→ delete the pin). Carries the KNOWN-BOUND #349 message + the three re-open triggers (real
drift / threat-model change / CI+root-audit #285), and states the residual is DRIFT, already mostly
mitigated (only HARDCODED-root walks drift; the one instance, comms_footer Scan B, is migrating).

### Threat model (§12.7.1) — stated IN the instruments

Both classes' docstrings state: A-SUB guards the PARSE (`parse_production_trees`), chokepoint =
`compile`, honest-developer threat, NOT security. A non-parsing tree-walk produces no AST → out of
parser scope by definition. So the verdicts follow mechanically (private parse → in scope; skip
file parsing un-routed → skip-coverage RED; non-parsing walk → pinned bound).

## §What-changed (symbols, not line numbers)

All in `loremaster/tests/test_ast_reach_helpers.py` (my only writable file):
- ADDED `_ASUB_PARSE_SKIP` (module-level dict, after `_ALLOWED_WHOLE_TREE_CLONE_FILES`).
- EDITED `TestSharingProvenByMutation.test_each_real_fixture_consumer_reddens_when_the_shared_parser_is_dropped`
  — the `if not fixtures:` branch now asserts `_ASUB_PARSE_SKIP` membership before `pytest.skip`.
- ADDED class `TestTheParseSkipSetIsACheckedVariable` (4 methods) + class
  `TestAsubNonParsingTreeWalkKnownBound349` (1 method). +5 tests (48 → 53 collected).
- KEPT ALL sound pins unchanged (L1, L2, ALL-set, the §12.3 rider, §12.4 comms binding,
  member-hand-list retirement) — adversary graded them SOUND; I touched none.

## §Satisfiability (re-derived; provenance printed)

Provenance receipt (#140): reference build `loremaster.__file__ =
/tmp/asub3-scr-a/loremaster/loremaster/__init__.py` (delta-adversary-asub-4's disposable
`scratch_copy.sh` tree, migrated helpers present). Every mutation `cp -a`-backed + restored
byte-exact; MAIN repo touched only `loremaster/tests/test_ast_reach_helpers.py`.

- **(d) correct/migrated reference build PASSES.** New pins + Layer 3 on the migrated build:
  `6 passed, 4 skipped` (the 4 `_ASUB_PARSE_SKIP` adopters skip AFTER asserting membership;
  `test_no_skip_set_file_parses_the_tree_unrouted` GREEN because the migrated
  `_all_workspace_parse_sites() == {parse_production_trees}`, delta §7).
- **(a)+(b) a skip-set file that parses UN-ROUTED (single-function) → RED.** At HEAD (`2fe81ba`):
  `test_no_skip_set_file_parses_the_tree_unrouted` FAILS naming
  `test_secret_leak_vectors.py::_production_function_names` (real un-migrated single-function
  `production_sources()`+`ast.parse`). In scratch: injected `_asub_evil_private_parse` into
  `test_backoff_seam.py` → pin FAILS naming `test_backoff_seam.py::_asub_evil_private_parse`;
  byte-exact restore → GREEN. Proves per-file discrimination, not keyed to one file.
- **(c) a non-parsing os.walk → the PINNED BOUND, not a false clear.**
  `test_asub_nonparsing_tree_walk_is_a_KNOWN_BOUND_349` GREEN (bound documented); its positive
  control confirms the PARSING variant IS flagged, so the bound is "non-parsing", not a dead detector.
- HEAD final state of new pins: `4 passed, 1 failed` (the failed one is the intended contract-first
  RED above). ruff clean, mypy clean on the file.

## §Decisions-needed (forks surfaced for the lead/operator)

1. **§12.7's backoff example reason is factually wrong; I wrote the TRUE reason instead of
   transcribing it.** §12.7.2 says `backoff = "does not parse the tree — it is a runtime-site reach
   check"`. Ground truth: `test_backoff_seam.py` has BOTH a non-parsing runtime reach check
   (`TestEveryBackoffSharesTheOnePolicy`) AND a whole-workspace AST parse
   (`TestNoNewHandRolledBackoff.test_no_production_module_outside_the_allowlist_exponentiates_by_a_variable`
   → `_production_python_files()` → `production_sources()` + `ast.parse`). secret_typing /
   secret_leak_vectors / comms_footer likewise all parse. So the honest classification is "routes its
   parse; no fixture", NOT "does not parse". The skip-coverage pin ENFORCES this, so the honesty is
   checked. If the operator/lead prefers the literal spec text, that would make the reasons FALSE and
   the pin would (correctly) not be able to certify them — I recommend keeping the true reasons.
   This does not change the mechanism, only the prose.
2. **The skip-coverage pin's REACH is the single-function shape; split-leg / os.walk-source-hidden
   private parses are a STATED BOUND, not caught here.** Per my brief's explicit steer ("REUSE L1's
   `_all_workspace_parse_sites`") and the operator's "REUSE > REINVENT, no new scanner", the pin keys
   on the static ALL-set. It catches the delta survivor's private parse ONLY in the single-function
   shape (parse-primitive + whole-workspace-source-NAME in one function). A SPLIT-LEG factoring
   (source in a nullary helper) or `os.walk`+`ast.parse` (source name not in the whole-workspace
   vocab) is NOT an ALL-set site; L1's runtime guard RECORDS the escape but its escape INVARIANT
   (`test_no_declared_adopter_parses_privately`) filters None-returning negative scans by return
   value — so those remain the delta-adversary-asub-4 residual. §12.7.1 CLAIMS "a private parse (any
   spelling) → L1 catches"; that is true of the recording but NOT of any assertion for a
   None-returning split-leg scan. This residual is what the operator's "pin the bound, don't chase
   spellings" ruling implicitly accepts (the source-following detector is the round-6 scanner that
   was overruled); it is owned by the #349 pinned bound + INSTRUMENT 0's reach-attack. Flagged so the
   cold audit / contract-adversary knows the skip-coverage pin's honest reach, not to reopen the
   ruling. If the operator wants the split-leg parse actually asserted (not just recorded), that is a
   scope decision beyond §12.7 (it would require either wiring L1's escape invariant to stop
   filtering by return value for skip-set files, or the source-following detector).

## §Coordination

- Registered `reviser-asub-5` (session `2026-08-09-fix-344-345`, role contract). Inbox drained: empty.
- lore/grep fallback: none. Work was direct reads of the contract, the design doc (§12.7 verbatim),
  the two named reports, and the four adopter sources, cited by symbol; plus AST/pytest construction
  in the scratch. No lore structure-query was needed, so no fallback to flag.
- Scratch `/tmp/asub3-scr-a` (delta-adversary-asub-4's disposable tree) has my contract copied in for
  the satisfiability run; recommend the lead discard it (as delta already recommended).
