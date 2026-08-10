# REPORT — delta-adversary-asub-4 (contract-adversary, re-grade of the RESTORED §12.3 rider + the 4-adopter SKIP)

brief-base v10 read
brief project v7 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **VERDICT: A-SUB (F4/§12) — CONTRACT INSUFFICIENT.** 1 BLOCKER. The restored rider works
  FOR ANCHORED, but the "4 adopters SKIP" decision RE-OPENS the routing-not-sharing hole for the
  other 4 — the exact class A-SUB exists to close, one adopter over.
- **Q(a): YES — the restored §12.3 rider TRULY kills the anchored os.walk-in-fixture survivor.**
  Rebuilt it independently: whole contract = **1 failed / 43 passed / 4 skipped**, the ONLY failure
  `test_each_real_fixture_consumer_reddens...[test_anchored_pattern_seam.py]`, naming the 3
  declared-RED consumers that stayed GREEN. Solely on the rider. Confirmed load-bearing (matches reviser).
- **Q(b): NO — the SKIP is a SILENT EXEMPTION, not evidence-justified, and it hides a live survivor.**
- **P1 HEADLINE — a routing-not-sharing wrong build passes the WHOLE contract 44/4skip, byte-identical
  to the correct build.** backoff's real whole-workspace scan rewritten to a blatant private `os.walk`
  loop; only the unconsumed `_asub_reference_trees` DECOY routes through the helper. Reproduced.
- **The "correct reference build" is ITSELF a routing-not-sharing build for backoff:** drop
  `parse_production_trees → {}` and backoff's OWN suite is **18 passed / 0 failed** — nothing in
  backoff depends on the shared parser. The "migration" is a pure decoy (`_asub_reference_trees`, 1
  occurrence = def only, unconsumed). secret_typing / secret_leak / comms_footer are PARTIAL (decoy +
  private real scans; Scan A / `_python_sources` / `_workspace_python_sources` stay green under the drop).
- **Every layer is EMPIRICALLY blind to the 4 skipped adopters' real scans:** Rider SKIPS (no nullary
  WS-tree fixture); L1 escape checks only tree-RETURNING derivations (the decoy routes; the real
  negative scans return None → filtered by `_is_workspace_tree_result`); ALL-set = ONLY
  `parse_production_trees` (real sources not in `_WHOLE_WORKSPACE_SOURCE_CALL_NAMES`); L2 = `{}`
  (split-leg: source factored into a nullary helper evades "3 legs in 1 function"); used-ness = "a call
  exists" (decoy satisfies).
- **reviser-asub-4 §D-2's justification is FALSE**, measured: "covered by Layer 1's escape gate" — L1
  does NOT cover them; "a private fixture ADDED later would be driven and caught" — a non-nullary
  fixture / a non-fixture negative scan is not driven, and a negative scan does not redden on empty.
- **MISSING PIN:** per-adopter `test_no_declared_adopter_keeps_a_private_whole_workspace_parse` (∀
  `_MIGRATION_SET`) that follows the directory-source leg ONE LEVEL DOWN through nullary helpers
  (closing the split-leg evasion), OR requires each real scan to route through `parse_production_trees`;
  AND the rider SKIP must become a CHECKED VARIABLE (skip only when PROVEN no private whole-workspace parse).
- **Packages considered:** none new — reused in-repo `scripts/mutation_proof.py` (#194) principle +
  `_rebind_everywhere` + a suite-level `parse_production_trees→{}` drop. `bespoke (reuse)` — no external
  library supplies a "split-leg whole-workspace-parse" detector (agrees §12.5).
- **Graded:** working-tree contract = HEAD `b7bf68c` + uncommitted `test_ast_reach_helpers.py` ·
  HEAD-at-report `b7bf68c` · SAME. Reference build = `/tmp/asub3-scr-a` (delta-asub-3's scratch;
  its adopters + `_logging_fixtures` helpers unchanged since; I copied the working-tree contract in).
- **Provenance (#140):** `loremaster.__file__ = /tmp/asub3-scr-a/loremaster/loremaster/__init__.py`;
  every wrong build / drop was in that scratch (restored byte-exact after each probe); MAIN repo
  touched ZERO files (git status = only the 2 pre-existing edits, throughout).
- **Decisions-needed:** (1) the missing pin above — route the real scans OR follow the source leg;
  (2) whether backoff/secret_typing/secret_leak belong in `_MIGRATION_SET` at all if their real scans
  are negative (assert-no-offenders, un-reddenable) — an operator/design call; (3) §12.4 A↔B purpose-swap
  residual UNCHANGED (carried).
- **Receipt pointers:** §1 satisfiability + Q(a) · §2 the P1 wrong build · §3 the drop (both-direction) ·
  §4 mechanical blindness · §5 tables · §6 missing pin.

---

## §0 — Capability check
Full tool access; `/tmp/asub3-scr-a` reference build present with all helpers built
(`parse_production_trees`, `assert_scan_reached_every_member`, `install_parse_guard`,
`ParseGuardReport`, `_rebind_everywhere` in `test_store_seam_one_derivation`). No brief demand unmet.
lore/grep fallback: work was AST/runtime construction in the scratch + direct reads of the adopters
and the design doc (cited by §/symbol); no lore structure-query was needed, so no fallback to flag.

## §1 — SATISFIABILITY + Q(a): the rider works FOR ANCHORED

**Correct reference build (restored-rider contract copied into `/tmp/asub3-scr-a`):**
```
$ ./.venv/bin/python -m pytest loremaster/tests/test_ast_reach_helpers.py -q -p no:xdist
44 passed, 4 skipped in 35.25s          # matches reviser-asub-4's 44/0(+4skip)
```
The 4 skips = backoff, secret_typing, secret_leak_vectors, comms_footer (∀ `_workspace_tree_fixtures`
returns empty for them).

**Q(a) — anchored os.walk-in-fixture survivor, rebuilt independently** (production_trees fixture
rewired to a private `os.walk` whole-tree scan; the `_parse_production_trees` decoy stays migrated):
```
FAILED ...TestSharingProvenByMutation::test_each_real_fixture_consumer_reddens_when_the_shared_parser_is_dropped[test_anchored_pattern_seam.py]
  AssertionError: ...DECLARED-RED... STAYED GREEN when the shared parser was dropped:
  ['TestNoAnchoredPatternValidatedWithMatch.test_the_allowlist_carries_no_dead_entries',
   'TestScanCoverage.test_the_scan_reaches_every_production_tree',
   'TestScanCoverage.test_the_scan_resolves_the_known_anchored_constants']
1 failed, 43 passed, 4 skipped in 36.56s
```
The restored rider **discriminates** (P0): reddens on the survivor, passes on the correct build (§1
first block), the ONLY failure. **Q(a) = YES, the rider is load-bearing and correct — for anchored.**

## §2 — THE BLOCKER (Q(b)): a routing-not-sharing wrong build survives at a SKIPPED adopter

### The wrong build (a plausible incomplete migration of backoff)
backoff is in `_MIGRATION_SET`; the design (§ lines 677/787/903-907) says its whole-tree scan should
migrate onto `parse_production_trees` ("they consume parsed trees instead"). A builder who migrates only
the used-ness decoy and leaves the real scan private produces:

```python
def _asub_reference_trees():                       # the DECOY — routes through the helper, UNCONSUMED
    from _logging_fixtures import parse_production_trees
    return parse_production_trees(include_scripts=True, include_skills=False)

class TestNoNewHandRolledBackoff:
    def test_no_production_module_outside_the_allowlist_exponentiates_by_a_variable(self) -> None:
        import os                                    # THE REAL SCAN — private, whole-workspace
        offenders = []
        for base in (_REPO_ROOT/'loremaster'/'loremaster', ...lorerunes, loresigil, lorescribe):
            for dp,_d,fs in os.walk(base):
                for fn in fs:
                    if fn.endswith('.py'):
                        tree = ast.parse((Path(dp)/fn).read_text())   # private parse, no sanctioned frame
                        ... assert not offenders ...                  # returns None
```
```
$ ./.venv/bin/python -m pytest loremaster/tests/test_ast_reach_helpers.py -q -p no:xdist
44 passed, 4 skipped in 34.33s          # <-- BYTE-IDENTICAL verdict to the correct build
```
A blatant private `os.walk` whole-workspace parse survives the WHOLE contract. It escapes **both** the
rider (backoff SKIPS) **and** L1 (the real scan returns None → the no-escape law skips it).

### It is not even necessary to write a wrong build — the REFERENCE build already IS one
`_asub_reference_trees` appears exactly once (def only) in each of backoff/secret_typing/secret_leak —
a pure, unconsumed decoy. The both-direction diff at suite level (drop `parse_production_trees → {}`,
run each adopter's OWN suite; GREEN = does not depend on the shared parser = routing-not-sharing):
```
test_backoff_seam         : 18 passed                         <-- ZERO dependence — PURE DECOY
test_secret_typing        : 5 failed, 64 passed               <-- PARTIAL (core _python_sources scans private)
test_secret_leak_vectors  : 1 failed, 211 passed              <-- PARTIAL (_workspace_python_sources scan private)
test_comms_footer         : 1 failed, 244 passed              <-- PARTIAL (Scan A private; only Scan B reddened)
```
- **backoff** — its entire suite is GREEN when the shared parser returns `{}`. Nothing in it consumes
  `parse_production_trees`. The "migration" is a decoy; the real scan (`_production_python_files()` →
  `production_sources()` + inline `ast.parse`) is private, and would stay private-green forever.
- **secret_typing** — `_python_sources()` routes through `production_sources()` (paths, NOT the shared
  parser); its core secret-scan tests `ast.parse` inline privately. Only cross-check / allowlist tests
  reddened; the principal whole-workspace AST scans stay private.
- **secret_leak** — one scan routes (line ~765, `for _key,tree in parse_production_trees(...).items()`,
  reddened), but `_workspace_python_sources()` (→ `production_sources()`) + inline parse stays private.
- **comms_footer** — Scan B routes (reddened); Scan A (`TestTheFalseRationale..._scan`, private
  `(root/member).rglob("*.py")` + `_hits_in` parse) stays green, with `_AsubReferenceScanA._scan_a`
  (def-only decoy) satisfying §12.4's "both modes in distinct scopes".

## §3 — WHY every layer is blind (empirically shown, not reasoned)

Per-adopter enumerator output on the reference build (the contract's OWN functions):

| adopter | RIDER `_workspace_tree_fixtures` | L1 tree-producers it CHECKS (`_is_workspace_tree_result`) |
|---|---|---|
| anchored | `['production_trees']` → DRIVEN | `['_parse_production_trees']` (the real fixture source) |
| backoff | `[]` → **SKIP** | `['_asub_reference_trees']` — **the DECOY only** |
| secret_typing | `[]` → **SKIP** | `['_asub_reference_trees']` — **the DECOY only** |
| secret_leak | `[]` → **SKIP** | `['_asub_reference_trees']` — **the DECOY only** |
| comms_footer | `[]` → **SKIP** | `['_AsubReferenceScanA._scan_a','_AsubReferenceScanB._scan_b','_asub_reference_trees']` |

For backoff/secret_typing/secret_leak, the **only** derivation whose output is a workspace tree — and
therefore the only one L1's no-escape law inspects — is the decoy, which routes correctly. Their REAL
scans return None (negative scans) or lists (source helpers), so `_is_workspace_tree_result(out)` is
False → `continue` → their private parses are recorded in `report.escapes` but never asserted on.

L2 static + ALL-set coverage (reference build):
```
_whole_tree_clone_offenders()   == {}                                   # nothing flagged
_whole_tree_parse_offenders_in(backoff)      == []                       # split-leg: source in _production_python_files, parse in the method
_whole_tree_parse_offenders_in(secret_leak)  == []
_whole_tree_parse_offenders_in(comms_footer) == []
_whole_tree_parse_offenders_in(secret_typing)== ['test_the_shared_package_*']   # only its lorerunes single-package scans (allowlisted §7)
_all_workspace_parse_sites()    == ['_logging_fixtures.py::parse_production_trees']   # NO adopter real scan is a watched site
```
The universal evasion is **split-leg factoring**: every adopter puts the directory-source leg
(`production_sources`/`rglob`) in a nullary helper and the parse in the consumer, so L2's "parse +
read + directory-source in ONE function" never matches, and the source name (`_python_sources`,
`_production_python_files`, `_workspace_python_sources`) is not in
`_WHOLE_WORKSPACE_SOURCE_CALL_NAMES`, so the ALL-set never enumerates it.

## §4 — The SKIP is a silent exemption, not a checked variable (the CRUX answer)

The rider skips when `_workspace_tree_fixtures(adopter)` is empty — i.e. **"no nullary workspace-tree
fixture found"**, which is NOT the same as **"this adopter has no private whole-workspace parse."**
backoff HAS a private whole-workspace parse; it simply is not in a fixture. So the skip exempts it
silently. Only anchored's `production_trees`-stays-nullary is a checked variable
(`test_the_survivor_target_fixture_is_a_checked_variable`); the other 4 adopters' "absence of a
private scan" is **unchecked and FALSE**. The design's §12 model — "the decoy dies at Layer 3 because
it can't redden the real coverage pin" — assumes every adopter has a POSITIVE reach consumer that
reddens on `{}` (anchored's `test_the_scan_reaches_every_production_tree`). backoff/secret_typing/
secret_leak's scans are NEGATIVE (assert-no-offenders) and pass on an empty tree, so there is no RED
home for the both-direction diff, the rider skips, and the decoy — the exact artifact §12 set out to
kill (design § lines 1962-1963, 2085-2091) — survives.

## §5 — Tables

### P1b — QUANTIFIER TABLE (∀-over-inputs vs guarded)

| invariant | ∀ or guarded | receipt |
|---|---|---|
| every `_MIGRATION_SET` adopter's REAL whole-workspace scan routes through the shared parser | **claimed ∀ over `_MIGRATION_SET`; ACTUALLY guarded to (a) fixture-mediated AND (b) reddens-on-empty consumers** | anchored covered; backoff/secret_typing/secret_leak/comms_footer(ScanA) exempt — **BLOCKER** (backoff 18/0 under drop; wrong build 44/4skip) |
| no private parse escapes the sanctioned parser at runtime (L1 escape) | **∀ over DRIVEN derivations whose OUTPUT is a workspace tree** — guarded by return-value shape | catches tree-RETURNING private scans (anchored survivor via rider; nullary tree-producers via L1); **a None-returning negative scan or a list-returning source helper is filtered out ⇒ BLIND (BLOCKER)** |
| every whole-workspace parse SITE watched (L1 coverage) | **∀ over the ALL-set** — guarded by source vocab `{production_sources,workspace_roots,parse_production_trees}` | ALL-set = only `parse_production_trees`; a private `_python_sources`/`_production_python_files`/rglob scan ∉ ALL-set ⇒ never required watched (BLOCKER) |
| no test file hand-rolls a whole-tree parser (L2) | **∀ over the tree, GUARDED by 3-legs-in-ONE-function** | split-leg factoring (source in a nullary helper) evades it for ALL 4 adopters (`{}` offenders) (BLOCKER) |
| the migration-set file CALLS the shared parser (used-ness) | ∀ over `_MIGRATION_SET`, "a call exists" | a decoy call satisfies it — PROXY, not consumption (BLOCKER contributor) |
| anchored's fixture consumers redden under the drop (restored rider) | **∀ over anchored's LIVE workspace-tree fixtures × (self,fixture) consumers** | SOUND — kills the anchored survivor (§1 Q(a)); the ONE adopter it covers |
| assert_scan_reached_every_member reach | ∀ over declared members, independent oracle, fail-closed on `{}` | SOUND (unchanged) |
| comms_footer include_tests re-adds EXACTLY `<member>/tests` | ∀ over member roots, equality both ways | SOUND for the HELPER's output; does NOT prove Scan A CONSUMES it (Scan A private) |

### P1c — REACH TABLE (per instrument)

| instrument | reach set | DERIVED / hand-list | coverage a checked var | effect vs proxy | one-source proven by mutation | verdict |
|---|---|---|---|---|---|---|
| restored rider (`test_each_real_fixture_consumer_reddens...`) | `_MIGRATION_SET` × LIVE nullary WS-tree fixtures × (self,fixture) consumers | DERIVED (`_workspace_tree_fixtures`, output-classified) | YES for anchored (survivor target is a checked var) | EFFECT (drop → redden, #194 both-direction) | reddens the anchored survivor | **SOUND for anchored; SKIPS the other 4 — the SKIP is NOT a checked variable (BLOCKER)** |
| L1 escape invariant | DRIVEN nullary derivations whose **OUTPUT is a workspace tree** | DERIVED but **filtered by return-value** | over executed tree-RETURNING code only | EFFECT (runtime chokepoint) | catches tree-returning private scans | **BLIND to None-returning negative scans / list-returning source helpers (BLOCKER)** |
| L1 coverage (ALL-set watched) | `_all_workspace_parse_sites()` = `['parse_production_trees']` | DERIVED from parse-primitive + narrow SOURCE vocab | NON-EMPTY on clean (v5 trap avoided) | EFFECT | n/a | **source vocab omits private wrappers ⇒ real scans never enumerated (BLOCKER)** |
| L2 static clone lint | test files' whole-tree clones minus allowlist | DERIVED, allowlist-the-safe | self-cleaning | STATIC name-keyed, **3-legs-in-1-function** | n/a | **split-leg factoring evades it — `{}` offenders across all 4 (BLOCKER)** |
| used-ness (`_calls_shared_parser`) | files that CALL the helper | `_MIGRATION_SET` literal | "a call exists", file-level | **PROXY** (decoy call satisfies) | n/a | **PARTIAL — decoy** |
| §12.4 comms binding | comms_footer parse_production_trees call scopes | DERIVED (AST scopes) | collapse→RED | STATIC | n/a | SOUND for collapse; a `_scan_a` decoy binds the mode while Scan A stays private; A↔B purpose-swap = stated cold-audit residual |
| assert_scan_reached_every_member | workspace members | DERIVED (pyproject, independent) | YES (fail-closed `{}`) | EFFECT | n/a | **SOUND** |

**Legs run:** EMPIRICAL for every A-SUB row — reference build + the backoff wrong build + the
suite-level `parse_production_trees→{}` drop across all 4 adopters + the anchored survivor rebuild +
the contract's own enumerators run against the reference tree. Every negative paired with a positive
control (the drop reddens genuine consumers: anchored 3 nodes, secret_typing 5, secret_leak 1,
comms_footer 1 — so the drop instrument demonstrably SEES dependence where it exists).

## §6 — THE MISSING PIN (the test that should exist + the defect it catches)

**BLOCKER — bind sharing to CONSUMPTION for EVERY adopter, and make the rider SKIP a checked variable.**
Add `test_no_declared_adopter_keeps_a_private_whole_workspace_parse` (∀ `_MIGRATION_SET`): a detector
that follows the directory-source leg **one level down through nullary helpers** — a function that
`ast.parse`s items yielded by a nullary helper which itself reaches the workspace (`production_sources`/
`workspace_roots`/an rglob-over-members) is a private whole-workspace parse and must be flagged unless
it routes through `parse_production_trees`. Equivalently, promote the rider's SKIP to
`assert <detector returns [] for this adopter>` so an adopter may skip the fixture pin ONLY when PROVEN
to hold no private whole-workspace parse.

*Catches:* backoff's `test_no_production_module_...` (source `_production_python_files`→`production_sources`),
secret_typing's `_python_sources`-fed scans, secret_leak's `_workspace_python_sources`-fed scan,
comms_footer's Scan A (`_scan` rglob-over-members + `_hits_in`). All four are `[]` under the current
L2 (split-leg) and skipped by the rider; the reference build passes them as pure/partial decoys.

*Why the current contract misses it:* the rider covers only fixture-mediated, reddens-on-empty
consumers (anchored). L1's no-escape law inspects only tree-RETURNING derivations (the decoy). L2
requires 3 legs in one function (the source leg is universally factored into a helper). Used-ness
requires only "a call exists" (the decoy). No instrument requires the REAL scan to route.

*Honest note on an alternative:* the both-direction diff (drop→redden) cannot bind to backoff's scan
because it is NEGATIVE (assert-no-offenders passes on `{}`). So the fix must be ROUTING-based
(structural, source-following) OR each negative-scan adopter must carry a POSITIVE reach assertion
(like anchored's) — the latter is a design/operator call (decision-needed #2).

**RESIDUAL (carried, not new) — §12.4 A↔B purpose-swap.** Unchanged; owed to the A-SUB cold-audit
hand-check (delta-adversary-asub-3 / -b). NOTE it interacts with this finding: comms_footer's Scan A
can stay private while `_AsubReferenceScanA._scan_a` (a decoy) supplies the `include_tests=True` scope
the binding pin requires — so the cold-audit hand-check for comms_footer must ALSO verify Scan A
CONSUMES `parse_production_trees`, not merely that a scope calls it.

---

## Full probe record (commands + real output)

Provenance throughout: `loremaster.__file__ = /tmp/asub3-scr-a/loremaster/loremaster/__init__.py`;
MAIN repo git status = only the 2 pre-existing edits (`test_ast_reach_helpers.py`,
`scripts/test_wave_gate.py`), verified before and after. All mutations were `cp -a`-backed and restored
byte-exact (`/tmp/{anchored,backoff,lf}.ORIG`). `/tmp/asub3-scr-a` is delta-asub-3's disposable
`scratch_copy.sh` tree; recommend the lead discard it after reading.

1. **Baseline (restored-rider contract in scratch):** `pytest test_ast_reach_helpers.py -p no:xdist` →
   `44 passed, 4 skipped in 35.25s`.
2. **Per-adopter enumerators** (`_workspace_tree_fixtures`, `_drivable_scan_candidates`, tree-producer
   filter) → §3 table; the only L1-checked tree-producer for the 3 skipped non-comms adopters is
   `_asub_reference_trees`.
3. **backoff wrong build** (real scan → blatant private `os.walk`, decoy kept) → `44 passed, 4 skipped`.
4. **Decoy census** — `_asub_reference_trees` = 1 occurrence (def only) in backoff/secret_typing/secret_leak.
5. **Suite-level drop** `parse_production_trees→{}` → backoff `18 passed`; secret_typing `5 failed,64
   passed`; secret_leak `1 failed,211 passed`; comms_footer `1 failed,244 passed`.
6. **anchored survivor rebuild** (production_trees fixture → private os.walk) → `1 failed, 43 passed, 4
   skipped`, solely `test_each_real_fixture_consumer_reddens...[anchored]`.
7. **Static blindness** — `_whole_tree_clone_offenders() == {}`; per-file `_whole_tree_parse_offenders_in`
   = `[]` for backoff/secret_leak/comms_footer, only lorerunes single-package scans for secret_typing;
   `_all_workspace_parse_sites() == ['_logging_fixtures.py::parse_production_trees']`.
8. **Design intent** — § lines 677/787/903-907 (5 real adopters, "consume parsed trees"); § lines
   1962-1963/2085-2091 (the unconsumed nullary decoy is the named survivor the design set out to kill).

## Verdict

**A-SUB (F4/§12): CONTRACT INSUFFICIENT.** The restored §12.3 rider correctly kills the anchored
os.walk-in-fixture survivor (Q(a) = YES), but the "4 adopters SKIP" decision (Q(b)) re-opens the
routing-not-sharing hole for the other four: the SKIP is decided by "no nullary workspace-tree fixture
found," which is a silent exemption, not proof of "no private whole-workspace parse." backoff is a
pure decoy that survives the whole contract (18/0 under the parser drop; a blatant private-os.walk
wrong build passes 44/4skip); secret_typing / secret_leak / comms_footer keep private real scans behind
decoys too. Every instrument is empirically blind — the rider (skips), L1 escape (filters by
tree-return), L1 coverage (narrow source vocab), L2 (split-leg), used-ness (decoy). Missing pin: a
per-adopter detector that follows the source leg through nullary helpers and requires the REAL scan to
route through `parse_production_trees`, with the rider's SKIP promoted to a CHECKED variable. This is
the SAME class (A-SUB-3, routing-not-sharing) surviving another wave — the `_sdk_guard`-v4 lesson
("a runtime gate is an invariant only over the code its arming DRIVES") re-expressed as
"the rider is an invariant only over the adopters that happen to expose a nullary workspace-tree fixture."
