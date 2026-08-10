# REPORT — reviser-asub-4 (A-SUB CONTRACT reviser, §12.3 both-direction-diff rider RESTORED)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **State: done.** §12.3's both-direction-diff RIDER is RESTORED in
  `loremaster/tests/test_ast_reach_helpers.py` (TEST-ONLY, single-file writable set). The
  key-reflection substitute reviser-asub-3 used is RETIRED. L1 / L2 / ALL-set coverage / §12.4
  comms binding are UNCHANGED (sound, per brief).
- **The restored pin binds to the adopter's REAL FIXTURE the tests consume** (anchored's
  `production_trees`, driven through `__wrapped__`), NOT a nullary decoy — the piece
  `_nullary_derivations` deliberately excludes and the survivor's exact hiding place.
- **How the os.walk-fixture survivor now dies:** its private fixture stays unchanged under
  `parse_production_trees → {}`, so anchored's real coverage consumers (declared-RED on an
  empty tree) STAY GREEN → the #194 both-direction diff fires (declared-RED-stayed-GREEN =
  private copy). REPRODUCED: the survivor that beat the old contract 47/0 now fails 1/43/4skip,
  and ONLY on this pin.
- **RED at HEAD, right reason:** all 5 parametrised cases RED via the accessor
  (`parse_production_trees` not extracted); 3 build-independent controls GREEN.
- **Satisfiability (scratch `/tmp/asub3-scr-a`, provenance clean):** whole contract on the CORRECT
  reference build = **44 passed / 4 skipped / 0 failed** (serial AND `-n auto`); on the SURVIVOR
  build = **1 failed (this pin) / 43 passed / 4 skipped**.
- **`scripts/mutation_proof.py` reused as an independent both-direction receipt on the REAL
  coverage node:** CORRECT build exit **0** (PROOF HELD — node reddens under the drop); SURVIVOR
  build exit **4** (DECLARED RED but STAYED GREEN — private scan caught).
- **Packages considered:** `scripts/mutation_proof.py` (#194 both-direction diff) — REUSED as the
  receipt; `_rebind_everywhere` (shared by-identity drop) — REUSED as the suite drop. `bespoke
  (reuse)` — no external library supplies a drive-the-real-node-under-a-drop harness (agrees §12.5).
- **Graded:** authored against HEAD `b7bf68c` + uncommitted `test_ast_reach_helpers.py` ·
  HEAD-at-report `b7bf68c` · SAME. Reference build = delta-adversary's `/tmp/asub3-scr-a`
  (15e5540-era migration); its semantics are unaffected by the b7bf68c CLAUDE.md doc commits.
- **Provenance (#140):** `loremaster.__file__ = /tmp/asub3-scr-a/loremaster/loremaster/__init__.py`;
  every reference/survivor run was in that scratch (its anchored restored byte-exact after each
  probe); MAIN repo touched ONLY `test_ast_reach_helpers.py`.
- **Deviations:** (1) the SUITE PIN drives the fixture IN-PROCESS via `_rebind_everywhere` (the
  §12.3-sanctioned alternative), not a subprocess `mutation_proof.py`, because shelling out to
  mutate the shared `_logging_fixtures.py` mid-suite is unsound under `-n auto`; `mutation_proof.py`
  is reused as the RECEIPT instead. (2) 4 adopters SKIP (no nullary workspace-tree fixture).
- **Decisions-needed:** (a) confirm the in-process-pin + mutation_proof-receipt split satisfies
  "reuse mutation_proof.py"; (b) the non-nullary-fixture tail is a stated bound (L1 autouse +
  INSTRUMENT 0); (c) §12.4 A↔B purpose-swap residual is UNCHANGED (carried, cold-audit hand-check).
- **Receipt pointers:** §A the change (symbols) · §B satisfiability legs · §C mutation_proof receipt ·
  §D deviations/bounds/flags.

---

## §A — What changed (symbols, not line numbers)

**RETIRED (the key-reflection substitute, reviser-asub-3 decision 1):**
- `TestSharingProvenByMutation.test_dropping_the_shared_parser_reddens_the_adopter_derivation` —
  drove only NULLARY tree-producers and key-compared them. A correctly-migrated
  `_parse_production_trees` DECOY satisfied it while the real `production_trees` fixture scanned
  privately (the delta-adversary-asub-3 survivor). RETIRED.
- `_tree_producing_derivations` / `_is_tree_producer` / `_looks_like_whole_tree_parser` — the
  L3-only helpers that fed it. DELETED (dead once the pin is retired; `_calls_named` stays, L1 uses
  it). The `test_ast_reach_helpers.py` allowlist reason updated to name a live meta-scanner.

**ADDED (the §12.3 both-direction-diff rider, RESTORED):**
- `_workspace_tree_fixtures(filename)` — the LIVE per-adopter set of module-level NULLARY
  `@pytest.fixture` nodes whose OUTPUT is a whole-workspace tree, resolved through `__wrapped__`.
  OUTPUT-classified, NOT AST-call-name: the real fixture body is `return _parse_production_trees()`
  (calls a decoy, carries no parse primitive of its own), so a call-name predicate MISSES it — the
  survivor's exact hiding place. This is precisely the surface `_nullary_derivations` excludes.
- `_fixture_consumer_nodes(filename, fixture_name)` — the `test_*` methods taking exactly
  `(self, <fixture_name>)`: the REAL coverage consumers §12.3 requires to redden under the drop.
- `_consumers_that_redden(consumers, tree_value)` — the both-direction-diff primitive: qualnames
  that raise when fed a tree value.
- `TestSharingProvenByMutation.test_each_real_fixture_consumer_reddens_when_the_shared_parser_is_dropped`
  (∀ `_MIGRATION_SET`) — for each adopter's real fixture, `_rebind_everywhere(real_parse, {})` then
  the #194 both-direction diff: **declared-RED** = consumers reddening on a literal `{}` (the drop's
  genuine tree effect, computed BEFORE the drop); **observed-RED** = consumers reddening when fed the
  fixture's output UNDER the drop; a declared-RED that STAYS GREEN = private copy = FAIL.
- `TestSharingProvenByMutation.test_the_survivor_target_fixture_is_a_checked_variable` — anti-vacuity:
  anchored's `production_trees` MUST be discovered as a nullary workspace-tree fixture, so the reach
  cannot silently regress to nullary-only (a non-nullary evasion reddens here; removal breaks
  anchored's own collection).

**Extracted to module level (DRY):** `_is_pytest_fixture_node` + `_is_nullary_def` (one fixture /
one nullary detector shared by the L1 nullary enumerator and the L3 fixture enumerator).

**KEPT unchanged (sound per brief):** L1 `TestNoPrivateParseEscapesTheSanctionedParserAtRuntime`;
L2 `TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist`; the ALL-set coverage
(`test_every_whole_workspace_parse_site_was_watched_executing`); §12.4 comms binding
(`TestBothCommsFooterScansMigrateWithTheirModes`); used-ness / member-hand-lists / comms-footer
behaviour-preservation; and `TestSharingProvenByMutation`'s
`test_the_rebind_mutation_reaches_a_from_import_binding` + `test_the_declared_adopter_surface_is_non_empty`.

## §B — Satisfiability (scratch `/tmp/asub3-scr-a`; provenance #140 asserted each run)

`loremaster.__file__ = /tmp/asub3-scr-a/loremaster/loremaster/__init__.py` (the delta-adversary's
reference build: the 3 helpers + `install_parse_guard`/`ParseGuardReport` in `_logging_fixtures.py`,
all 5 adopters migrated). Its `_rebind_everywhere` lives in `test_store_seam_one_derivation`; my
`_rebind_everywhere_fn()` resolves it.

| leg | command | result |
|---|---|---|
| RED at HEAD, right reason | `pytest ...::TestSharingProvenByMutation` (real tree) | 5 failed (all via accessor "parse_production_trees is not extracted") + 3 passed (build-independent controls) |
| CORRECT reference build | whole contract, serial | **44 passed / 4 skipped / 0 failed** |
| CORRECT reference build | whole contract, `-n auto` | **44 passed / 4 skipped** (parallel-safe — in-process drive, no file mutation) |
| SURVIVOR build (`production_trees` → private `os.walk`; `_parse_production_trees` decoy migrated) | whole contract, serial | **1 failed / 43 passed / 4 skipped** — the ONLY failure is `test_each_real_fixture_consumer_reddens_...[test_anchored_pattern_seam.py]`, naming the 3 declared-RED consumers that stayed GREEN |

The survivor is the delta-adversary-asub-3 v2 build verbatim (behaviour-faithful private fixture; a
correctly-migrated decoy satisfies every nullary-driven pin). Every OTHER layer passed on it —
confirming the survivor still beats L1/L2/ALL-set/used-ness/comms and dies SOLELY on the restored
rider (the pin is load-bearing, the rest unchanged/sound). The 4 skips are the adopters with no
nullary workspace-tree fixture (backoff/secret_typing/secret_leak/comms_footer) — covered by L1's
escape gate; anchored's case is a real PASS on the correct build.

## §C — `scripts/mutation_proof.py` both-direction receipt (independent cross-check on the REAL coverage node)

Reused the canonical tool to drop the shared parser and require anchored's real coverage node
(`TestScanCoverage::test_the_scan_reaches_every_production_tree`) to redden — the §12.3 "coverage pin
goes RED" leg, via the #194 both-direction diff:

```
# CORRECT reference build:
mutation_proof.py --file _logging_fixtures.py --anchor '    root = _asub_repo_root()' \
  --replacement '    return {}' --expect-red '...TestScanCoverage::test_the_scan_reaches_every_production_tree'
  -> TRUE exit 0 : PROOF HELD — the declared RED set fired EXACTLY (node reddens; reads from shared parser)

# SURVIVOR build (production_trees scans privately):
  -> TRUE exit 4 : PROOF FAILED — DECLARED RED but STAYED GREEN
     declared: [...test_the_scan_reaches_every_production_tree]   observed: []
```
(⚠ the true exit code is captured WITHOUT a `| tail` pipe — mutation_proof.py's own documented
PIPESTATUS bound bit my first harness run, which reported `tail`'s 0; re-run clean gives 0 / 4.)

## §D — Deviations, honest bounds, flags (scope law + THE RIDER IS PART OF THE RULING)

1. **SUITE PIN is in-process (`_rebind_everywhere`), not a subprocess `mutation_proof.py`.** §12.3
   offers both mechanisms ("via `_rebind_everywhere` by-identity … or a `scripts/mutation_proof.py`
   receipt"). A suite pin that shells out to mutate the SHARED `_logging_fixtures.py` in place is
   UNSOUND under `-n auto` (parallel xdist workers import the module mid-mutation) and violates the
   disposable-mutation discipline for a live tree. So the SUITE PIN drives the real fixture
   in-process and applies the #194 both-direction diff; `mutation_proof.py` is REUSED as the
   independent RECEIPT (§C). This satisfies "reuse mutation_proof.py" AND a sound suite pin —
   **flagged for the adversary/operator to confirm the split is acceptable** (I recommend it; a
   subprocess-per-adopter suite pin is a concurrency defect).
2. **4 adopters SKIP** (no nullary workspace-tree fixture). Their reach is nullary domain / single-
   package scans, covered by Layer 1's escape gate — NOT a decoy-defeatable OR-clause: the survivor's
   target IS a nullary workspace-tree fixture (a CHECKED VARIABLE via
   `test_the_survivor_target_fixture_is_a_checked_variable`), so anchored is never skipped; and the
   discovery is LIVE, so a private fixture ADDED to any skipped adopter later would be driven and caught.
3. **Non-nullary-fixture bound (stated in the pin).** A survivor hiding its private scan in a fixture
   that TAKES other fixtures (non-nullary) is not drivable through `__wrapped__` in-process — Layer 1's
   session-wide-autouse form + INSTRUMENT 0's reach-attack own that tail. The specific evasion of
   making anchored's `production_trees` non-nullary is caught by the anti-vacuity control (it can no
   longer be discovered → RED). NOT pretended closed.
4. **§12.4 A↔B purpose-swap residual — UNCHANGED (carried).** Per brief, §12.4 is kept as-is; its
   stated bound (a pure A↔B purpose swap needs comms_footer-internal knowledge → the named A-SUB
   cold-audit hand-check) is delta-adversary-asub-3's carried residual, not this reviser's to close.

**Gates:** `ruff check` clean on the contract; `mypy` — my file contributes ZERO errors (verified by
stash-and-diff). The full `typecheck.sh` shows 104 errors in 10 OTHER files
(`test_auth_composition.py`, `test_mutating_set_derivation.py`, …) — pre-existing WIP contracts
against unbuilt helpers in this fix-wave session, NOT introduced by me. **Flag:** there are 104
mypy errors unrelated to this task's scope, spread across other in-flight contracts — surface to the
operator.

**lore/grep fallback:** none material; work was AST/runtime construction in the one writable file
plus direct reads of the adopters/`_logging_fixtures`/`_rebind_everywhere` (cited by symbol) and
`docs/plans/v2/design/2026-08-09-defect-class-prevention.md` §12.3 (the rider restored verbatim).

**Scratch:** `/tmp/asub3-scr-a` is the delta-adversary's disposable `scratch_copy.sh` tree; I restored
its contract + anchored byte-exact after every probe. Recommend the lead discard it after reading.
