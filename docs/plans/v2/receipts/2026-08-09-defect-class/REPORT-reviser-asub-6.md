# REPORT — reviser-asub-6 (Opus CONTRACT reviser; §12.8 skip-coverage → L1 RUNTIME observation)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **State:** done-with-deviations (two measured refinements of §12.8.3, both within delegated
  authority — the design's own "the reviser flags if not"; see Deviations).
- **What shipped (test-only, ONE file — `loremaster/tests/test_ast_reach_helpers.py`):** the §12.7.2
  skip-coverage pin `test_no_skip_set_file_parses_the_tree_unrouted` is RE-SOURCED from the STATIC
  `_all_workspace_parse_sites` detector to L1's RUNTIME `report.escapes` (the `builtins.compile`
  chokepoint). It now DRIVES each `_ASUB_PARSE_SKIP` file's scan candidates under the armed guard and
  requires, per file: (1) the guard OBSERVED it parse (anti-vacuity #136, `require_observations` +
  per-file intercepted-delta), and (2) no unrouted WHOLE-WORKSPACE parse beyond a per-file DECLARED
  budget (default 0 = it routes). Split-leg / comprehension / os.walk-parse / aliased survivors die,
  ANY spelling. `_all_workspace_parse_sites` STAYS as L1's own coverage instrument (unchanged).
- **The false-clear docstring is FIXED (§12.8.4):** the skip-coverage docstring no longer calls an
  in-scope split-leg PARSE "the #349 pinned bound." It now distinguishes (a) an in-scope PARSE (any
  spelling) CLOSED by L1's runtime observation, from (b) #349's KNOWN BOUND = a NON-parsing tree-walk
  only. The #349 pin (`TestAsubNonParsingTreeWalkKnownBound349`) is UNCHANGED and still passes (honest).
- **Deviations (both MEASURED against real data in scratch, both refine §12.8.3 correctly):**
  1. **DISCRIMINATOR = MEMBERS-SPANNED, not compile-COUNT-per-site.** My first draft used "≥2 compiles
     at one site". The real data (satisfiability §below) showed that FALSE-FLAGS `test_secret_typing`'s
     lorerunes single-package scans (≥2 lorerunes FILES at one site, but ONE member) as whole-workspace
     — a **C-DEF** (RED on a correct migrated build). Fixed to "escapes span ≥2 distinct MEMBERS," which
     is exactly the §4 caveat's "spans ≥2 members." (No design gap — the §4 caveat wanted members; I
     under-simplified, then corrected.)
  2. **The escape-record extension IS needed, as `.member` resolved from the compiled SOURCE — NOT the
     "target PATH."** §12.8.3's premise ("L1 already inspects the compiled .py path") is factually wrong:
     the survivor calls `ast.parse(path.read_text())` with NO `filename`, so the compiled target is
     `<unknown>`; L1 keys the SITE off the CALLER frame (its own line ~207 says so). So I extended the
     escape record to carry `.member` (the member of the compiled SOURCE, resolved via a `{source:member}`
     map at arm time) — the useful form of the extension the brief/§12.8.3 authorized. Spec'd in the
     `_install_parse_guard_fn` REQUIRED-API docstring; the builder implements it.
- **Packages considered:** none new — stdlib `ast`/`sys`/`inspect`/`builtins` + a `{source:member}`
  dict. The runtime guard REUSES the shipped in-repo `_sdk_guard` / `test_retry_seam` runtime-guard
  idiom (`report.armed/.escapes/.observed/.intercepted/.require_observations`), generalised to
  `builtins.compile` — `keep_with_trigger` (design §12.5's shared-extraction candidate, gated on
  prove-by-mutation). Verdict: bespoke-minimal, re-sourcing an existing pin to the existing runtime
  observation. No library supplies a "no-unsanctioned-frame-above-a-primitive" gate.
- **Graded:** working-tree `test_ast_reach_helpers.py` (uncommitted, reviser-asub-5's §12.7 contract as
  the baseline I revised) atop HEAD `4ceac32` · HEAD-at-report `4ceac32` · SAME.
- **Decisions-needed:** none blocking. The two refinements are flagged for the §12.8 design sidecar +
  contract-adversary to confirm; both are corrections that make the pin CORRECT (without them it
  false-clears or false-fails). See §4.
- **Receipt pointers:** §1 what changed (symbols) · §2 satisfiability receipts (scratch, provenance
  `/tmp/asub6-scratch-a/...`) · §3 RED/GREEN at HEAD · §4 the two refinement flags · §5 stated bounds ·
  §6 scratch note.

---

## §0 — Capability check

Full tool access; lore tools loaded (`ToolSearch "+lore"`). Registered `reviser-asub-6` (session
`2026-08-09-fix-344-345`, role contract, model claude-opus-4-8); inbox drained empty. No brief demand
unmet. No lore structure-query fallback to flag (work was AST + runtime construction in scratch + direct
source reads cited by symbol). Writable set honoured: only `loremaster/tests/test_ast_reach_helpers.py`
is modified by me in the main repo (git status confirms; `scripts/test_wave_gate.py` is reviser-g-6's
disjoint concurrent edit, untouched by me). The one possible non-test touch §12.8.6 named — extending
L1's escape record — is inside the guard's REQUIRED-API SPEC (the guard is spec-only at HEAD, unbuilt),
so it is a docstring change in this same test file; no separate guard file exists to edit.

## §1 — What changed (by symbol, `loremaster/tests/test_ast_reach_helpers.py`)

1. **`_ASUB_PARSE_SKIP` reshaped** `dict[str,str]` → `dict[str,_ParseSkip]` (new `NamedTuple` with
   `unrouted_whole_workspace_budget: int` + `reason: str`). All 4 entries declare budget **0** (each
   ROUTES its whole-workspace parse). Reasons updated to state the RUNTIME mechanism. Header comment
   updated (§12.8 re-sourcing note). All existing readers are key-based (membership / iteration) — the
   value-type change breaks nothing (verified: no AttributeError/KeyError/TypeError in the full-file run).
2. **New pure helpers** (near the skip set): `_whole_workspace_escape_sites(escapes)` (sites whose
   escapes span ≥2 MEMBERS), `_skip_files_parsing_whole_workspace(escapes)` (attribute those to skip
   files — PURE, so build-independently testable), `_skip_budget_verdict(observed,budget)` (over/dead/OK,
   the both-ways adjudication).
3. **`test_no_skip_set_file_parses_the_tree_unrouted` re-sourced** (takes `monkeypatch`): enumerates
   candidates BEFORE arming (AST-before-arm discipline), arms `install_parse_guard`, drives each skip
   file's `_drivable_scan_candidates`, and asserts per file — unobserved (intercepted-delta 0) → RED;
   whole-workspace unrouted sites > budget → RED (over); < budget → RED (dead); then global
   `report.require_observations(...)`. Docstring rewritten (the §12.8.4 fix).
4. **`test_the_skip_coverage_pin_would_flag_a_skip_file_that_parses` → `..._discrimination_fires_and_discriminates`:**
   build-independent controls over the NEW logic with synthetic escapes (`.site`+`.member`): POSITIVE
   (≥2 members → flagged), NEGATIVE-1 (single-PACKAGE many files/ONE member → NOT flagged — the C-DEF
   this refinement fixes), NEGATIVE-2 (non-skip-file site → not attributed), and the `_skip_budget_verdict`
   both-ways table (over/dead/OK).
5. **`_install_parse_guard_fn` REQUIRED-API docstring:** `report.escapes` entries now also carry
   `.member` (§12.8.3), with the source-resolution instruction and the measured rationale.
6. **UNCHANGED (per brief):** `_all_workspace_parse_sites` + `test_every_whole_workspace_parse_site_was_watched_executing`
   (L1's own coverage), L1/L2/L3, the §12.3 rider, §12.4 comms-footer pins, the #349 pin.

## §2 — SATISFIABILITY (scratch, provenance-asserted)

Provenance (#140): `loremaster.__file__ = /tmp/asub6-scratch-a/loremaster/loremaster/__init__.py`
(scratch_copy.sh, asserted INSIDE the copy). A minimal REAL compile-chokepoint guard + `parse_production_trees`
were built in the scratch `_logging_fixtures.py` (honouring the REQUIRED API incl. `.member`) — the
smallest instrument to run the pin on `report.escapes`; NOT the production builder's implementation.

- **Guard sanity:** `ast.parse` routes through the wrapped `builtins.compile` (primitives
  `{compile, ast.parse}` register); a private `production_sources()+ast.parse` loop from a workspace
  site → escapes at ONE site; `parse_production_trees` → SANCTIONED (observed, 0 escapes).
- **(a) The split-leg survivor DIES — the REAL pin on the un-migrated real skip files (guard built):**
  RED naming the whole-workspace unrouted sites incl. **`test_backoff_seam.py:780 in test_no_production_module_...`
  (6 members)** — the exact delta-adversary-asub-5 SPLIT-LEG survivor the STATIC detector missed (the
  static pin flagged only 1 of 4 files; the runtime pin flags all 4, spelling-agnostic: backoff,
  secret_typing×5, secret_leak×2, comms_footer×2).
- **The MEMBERS refinement (Deviation 1) verified:** with members-spanned, `test_secret_typing` drops
  7→5 flagged sites — the two lorerunes single-package scans (`:1313`, `:1341`, ONE member each) are
  CORRECTLY EXCLUDED; `backoff:951` (single-file, 1 member) and `backoff:885` (0 members) excluded. A
  raw count≥2 proxy flagged all of them → the measured C-DEF.
- **(d) A ROUTED skip file → GREEN:** a real routed test-double (whole-workspace via
  `parse_production_trees` + a lorerunes single-package scan) drove the pin over a controlled 1-file
  skip set → GREEN (observed + 0 whole-workspace unrouted sites). Proves no C-DEF on the correct path.
- **(b)+(c) build-independent controls PASS:** `test_the_skip_coverage_discrimination_fires_and_discriminates`
  → 1 passed (positive ≥2-members flagged; single-package excluded; non-skip-site not attributed;
  `_skip_budget_verdict` over/dead/OK).
- **Per-file ANTI-VACUITY fires:** a skip file that READS but never PARSES → intercepted-delta 0 →
  RED `[ANTI-VACUITY] the guard OBSERVED NO compile ... BLINDNESS, not cleanliness` (#136 / §12.8.2).

## §3 — RED / GREEN at HEAD (`4ceac32`, guard/helpers unbuilt)

- `test_no_skip_set_file_parses_the_tree_unrouted` — **RED for the RIGHT reason**: the accessor
  `_install_parse_guard_fn()` raises the honest "build the guard" AssertionError (it now depends on
  the runtime guard, like every other Layer-1 pin). This REPLACES the old static RED (secret_leak
  un-migrated). Once the guard is built, on an un-migrated tree it REDs naming the whole-workspace
  survivors (§2a); on a migrated tree it is GREEN (§2d).
- `test_the_skip_set_is_non_empty_...`, `test_the_skip_coverage_discrimination_...`,
  `test_the_parse_skip_allowlist_carries_no_dead_entries` — **GREEN** (build-independent).
- `TestAsubNonParsingTreeWalkKnownBound349` — **GREEN**, unchanged.
- Whole file: 53 collected, 19 passed / 34 failed at HEAD — every failure references an unbuilt helper
  (`parse_production_trees` / `install_parse_guard` / `assert_scan_reached_every_member`); zero
  errors from the `_ParseSkip` value-type change. Gates: `ruff check` clean; `mypy` (canonical) clean.

## §4 — The two refinement flags (for the §12.8 sidecar + contract-adversary)

Both are within the delegated authority §12.8.3 grants the reviser ("the reviser flags if not"), and
both make the pin CORRECT — without them it either false-clears or false-fails:

- **Flag A — discriminator is MEMBERS-SPANNED (≥2 distinct members per site), not compile-COUNT.** The
  §4 caveat already wanted "spans ≥2 members"; the count proxy is a C-DEF (measured — lorerunes
  single-package scans). No design change owed; this is the faithful reading.
- **Flag B — §12.8.3's "L1 already inspects the compiled .py path" is FALSE.** The survivor passes no
  `filename` (`<unknown>`); L1 discriminates the SITE by the CALLER frame (its own line ~207). So the
  member is resolved from the compiled SOURCE (a `{source:member}` map), and the escape record carries
  `.member`. This IS the escape-record extension the brief/§12.8.3 authorized — its useful form. The
  §12.8.6 "possible non-test touch = extending L1's escape record" is thus REALISED, and it is inside
  the guard's SPEC (spec-only at HEAD), so it stayed test-only.

## §5 — Stated bounds (honest, not pretended closed)

- **Unroll-across-sites tail:** members-spanned is PER-SITE. A loop/comprehension over the tree = ONE
  site spanning ≥2 members → caught. A fully-UNROLLED per-member parse (N literal `ast.parse` statements
  at N distinct lines, each 1 member) would evade — but that is not the honest-developer LOOP pattern
  the §12.7.1 drift threat targets (a hardcoded-member-LIST loop is one site spanning ≥2 → caught), and
  the tail is Layer 2's weak-total lint + INSTRUMENT 0's reach-attack, exactly as §12.2/§12.3 already state.
- **`{source:member}` collisions:** two byte-identical workspace files (e.g. empty `__init__.py`) collide
  in the map (last wins); immaterial to a ≥2-members verdict (a whole-workspace scan spans real members
  regardless). The builder may harden resolution (filename when present + source fallback); spec'd loosely.

## §6 — Scratch tree

`/tmp/asub6-scratch-a` (scratch_copy.sh, disposable by design) holds the minimal guard used for §2.
`rm -rf` was permission-denied this session — recommend the lead discard it (it is under `/tmp`,
provenance-asserted, no main-repo footprint).

## Verdict

§12.8 applied. The skip-coverage checked variable runs on L1's RUNTIME `report.escapes`, per-skip-file
`require_observations`, with a per-file declared budget (default 0) and a MEMBERS-SPANNED whole-workspace
discriminator (the correct form of §12.8.3, measured). The split-leg / comprehension / os.walk-parse /
aliased in-scope PARSE dies at the `compile` chokepoint, ANY spelling; the lorerunes single-package
scans are correctly NOT false-flagged (C-DEF avoided); a routed skip stays GREEN; an un-observed skip
REDs. The false-clear docstring is corrected; the #349 non-parsing bound stays pinned and honest. Two
measured refinements of §12.8.3 (members-not-count; `.member`-from-source, not target-path) are flagged
for the sidecar/adversary. RED-at-HEAD for the honest "build the guard" reason; gates clean.
