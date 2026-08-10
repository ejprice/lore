# REPORT — reviser-asub-2 (Opus CONTRACT reviser, A-SUB touch-up per design §10 #1)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **State: done — with ONE escalated DECISION-NEEDED** (Scan B narrowing, below). Contract
  tests only; edited exactly one file (`loremaster/tests/test_ast_reach_helpers.py`).
  `test_comms_footer.py` / `_logging_fixtures.py` left UNTOUCHED (builder's job — I PIN the
  migration).
- **Capability check:** all tools present (lore loaded via `ToolSearch "+lore"`, registered in
  comms as `reviser-asub-2`). No brief demand unmet. One sandbox friction: `rm -rf /tmp/...`
  is denied, so the scratch tree could not be self-cleaned — see deviations.
- **What I added (design §10 Ruling 6 / fable-designer-2), all RED-for-the-right-reason at HEAD:**
  - (a) **Removed the provisional `test_comms_footer.py` allowlist entry** → the offender scan
    now FLAGS Scan B's `_scan` clone (`{'test_comms_footer.py': ['_scan']}`) as un-migrated → RED
    until migrated; self-cleans on migration (verified in scratch: comms_footer drops out).
  - (b) **Per-scan behaviour-preservation equality pins**, oracle = pre-migration set re-derived
    INDEPENDENTLY from disk: Scan A == 262 files (prod ∪ member-tests); Scan B == 90 (see the
    escalation — Scan B's TRUE pre-migration is 131, not prod-only).
  - (c) **The granularity-hazard pin**: `parse_production_trees(include_tests=True)` re-adds
    EXACTLY `<member>/tests` (172 files) that `workspace_roots` (`<member>/<member>`) excludes,
    so Scan A does not NARROW.
  - `test_comms_footer.py` added to `_MIGRATION_SET` (routing/used-ness) + a file-level
    both-modes pin ({True, False} literals). `_live_adopters()` picks comms_footer up
    automatically once it CALLS the helper (§9.1 meta-recursion preserved — no hand-list).
- **Deviations (2):**
  1. **Scan B oracle = the design-INTENDED prod-only set (90), NOT the literal pre-migration set
     (131).** Forced by a factual error in §10 R6 (below); the drop is adjudicated safe by a
     removed-behaviour pin. This is the DECISION-NEEDED.
  2. **Minimal robustness guard added to the existing ∀-mutation** (`TestSharingProvenByMutation
     .test_dropping...`): an `isinstance(healthy, dict)` check before `set(...)`, so a
     comms_footer-shaped derivation returning `(counts, hits)` fails as a CLEAN guided
     AssertionError instead of a raw `TypeError`. My adding comms_footer as an adopter directly
     exposes this; disclosed per scope law. Behaviour for dict-returning adopters unchanged.
- **Packages considered:** none — no mechanism specified (contract tests only).
- **Graded: 14b62f2 · HEAD-at-report: 14b62f2 · SAME.** Index fresh (branch
  `feat/surreal-unification`). Design read at §10 R6, §8 R1, §7, §9.5/§9.6/§9.7. Pre-migration
  file sets MEASURED at HEAD (script pasted in body §4).
- **DECISION-NEEDED (1, for lead/operator):** §10 R6 calls Scan B "PRODUCTION ONLY" and migrates
  it to `include_tests=False` — but Scan B's TRUE pre-migration reach is **131** files
  (90 prod + **41** lorerunes/loresigil/lorescribe TEST files), so an EXACT §8-R1 preservation
  via one helper call is IMPOSSIBLE (False→90, True→262; neither is 131). **Recommend reading
  (b): narrow to prod-only (90), the 41 test files adjudicated OLD-BUG.** Alternative (a):
  preserve 131 via bespoke roots (fights DRY #1). See §3.
- **Receipt POINTERS:** contract file `loremaster/tests/test_ast_reach_helpers.py` —
  `TestCommsFooterScansMigrateBehaviourPreserving` (b+c), `TestBothCommsFooterScansMigrateWithTheirModes`
  (both-modes), the deleted allowlist entry (~line 493), `_MIGRATION_SET` (comms_footer added),
  the ∀-mutation isinstance guard (~line 944). Satisfiability receipt: body §5.
- **BUILDER NOTE (below §6):** migrate BOTH scans to `parse_production_trees` — Scan A
  `include_tests=True` (+`<member>/tests` re-add), Scan B `include_tests=False`; route each scan
  through a **nullary dict-returning tree-derivation helper** (NOT a direct call inside `_scan`,
  which returns `(counts, hits)`), so the ∀-mutation drives a dict cleanly.

---

## 1. Boot / dogfood

- `brief-base.md` v10 read first; project brief v7 auto-acked on `lore_comms register` (agent
  `reviser-asub-2`, role `contract`, session `2026-08-09-fix-344-345`, model `claude-opus-4-8`).
- lore loaded via `ToolSearch "+lore"` (keyword form). Used `lore_comms` (register). Symbol/span
  work done by direct Read of the named files (all paths given in the brief). **Fallback
  disclosure:** used `grep`/`ast`-shape reads + a disk-walk script for the NON-symbol textual
  seams — the two comms_footer `_scan` loop bodies, `_workspace_scan_roots`, and the pre-migration
  FILE SETS (counting files on disk is not a symbol query). Honest grep case (b)/(c) per project
  CLAUDE.md; no lore weakness routed around.

## 2. What §10 Ruling 6 requires that the HEAD contract LACKED (assessed, not duplicated)

The HEAD contract (`test_ast_reach_helpers.py` @ `14b62f2`) already pinned: the shared
`parse_production_trees`/`assert_scan_reached_every_member` helpers, the DERIVED offender scan
(`_whole_tree_clone_offenders`), the `_SCANNED_MEMBERS`-retired pin, the import-is-USED routing
pin, and the ∀-mutation over the LIVE-derived adopter set (`_live_adopters`). It did NOT cover
comms_footer, which §10 R6 rules an adopter: comms_footer was **provisionally ALLOWLISTED** (a
C-DEF-avoidance placeholder), so nothing forced its migration, and there were no per-scan
equality/granularity pins. My additions close exactly that gap.

## 3. The Scan B contradiction (DECISION-NEEDED) — ground-truthed, not argued

§10 R6 evidence says *"Scan B (~3144-3165): iterates a HARDCODED 4-tuple ... PRODUCTION ONLY →
`parse_production_trees(include_tests=False)`."* **Measured at HEAD, that is false by 41 files.**
Scan B's tuple is `("loremaster/loremaster", "lorerunes", "loresigil", "lorescribe")`: loremaster
via its NESTED package path (prod only), but the 3 FLAT members via their MEMBER dir — so
`lorerunes/tests`, `loresigil/tests`, `lorescribe/tests` LEAK IN. Scan B's TRUE reach is **131**
(90 prod + 41 non-loremaster test files); loremaster's tests were NEVER in Scan B (the asymmetry
that reveals it as an accidental over-reach).

Consequence: **no single `parse_production_trees` mode reproduces 131** (False=90, True=262). So
§10 R6.2's "each pinned to its EXACT pre/post scanned-file-set (§8 R1)" is internally contradictory
for Scan B — its author believed Scan B was 90. This is a spec ambiguity/defect → escalation
(PKT-28 C1: "spec ambiguity is a defect, not a judgment call"). I did NOT pick silently.

- **Reading (a) — preserve 131:** the builder keeps bespoke roots (not a clean single-helper call)
  → fights DRY (priority #1); only "preserves" an accidental over-reach of a *production*-door scan
  over *test* files.
- **Reading (b) — narrow to prod-only 90 [RECOMMENDED]:** clean consolidation (DRY #1);
  `include_tests=False`. The 41 dropped files are member TEST files, adjudicated OLD-BUG per the
  removed-behaviour law — Scan B (`TestNoCommsIdentityReachesQueryTEXT`) hunts PRODUCTION query-doors,
  and a query-text f-string in a test is not a served/production trust surface, so the drop does not
  widen a real gap (priority #3). Its safety is pinned mechanically:
  `test_scan_B_narrowing_drops_only_accidental_test_over_reach` reddens if the drop would ever hit a
  PRODUCTION file or a loremaster file.

I encoded reading (b) (the pin is satisfiable against the design's reference build) and marked it
pending the ruling in the pin's docstring. If the operator rules (a), that pin + its sibling change
and the builder keeps bespoke roots.

## 4. Pre-migration file sets — MEASURED (the instrument, committed here verbatim)

```python
from pathlib import Path
root = Path(".").resolve()
def rglob_set(rel):
    return {p.relative_to(root).as_posix() for p in (root/rel).rglob("*.py")
            if "__pycache__" not in str(p)}
members = ["lorerunes","lorescribe","loresigil","loremaster"]      # pyproject [tool.uv.workspace]
scanA = set().union(*(rglob_set(m) for m in members))                              # 262
scanB = set().union(*(rglob_set(m) for m in ("loremaster/loremaster","lorerunes","loresigil","lorescribe")))  # 131
pkg   = set().union(*(rglob_set(f"{m}/{m}") for m in members))                     # 90 (prod only == workspace_roots)
mtest = set().union(*(rglob_set(f"{m}/tests") for m in members))                   # 172 (<member>/tests)
assert scanA == pkg | mtest                       # True  (262 == 90 + 172)
assert scanB != pkg                               # True  (131 != 90)
assert scanB - pkg == 41 files, all */tests/*, none loremaster/*   # the accidental over-reach
```
These oracles are re-derived independently inside the contract (`_member_package_files`,
`_member_test_files`, `_comms_footer_scan_a_pre_migration`, `_comms_footer_scan_b_pre_migration`)
— never `derived == derived`; the migration deletes the subject's own loops, so the Scan B oracle
transcribes the frozen tuple, dated.

## 5. Satisfiability receipt (scratch, provenance-asserted)

Scratch via `./scripts/scratch_copy.sh /tmp/asub2-scratch-a`. **Provenance:**
`loremaster.__file__ = /tmp/asub2-scratch-a/loremaster/loremaster/__init__.py` (resolves INSIDE
the copy — NOT the original). In scratch I built a reference `parse_production_trees`
(+`assert_scan_reached_every_member`) in `_logging_fixtures.py` and migrated comms_footer's two
scans through nullary dict-returning helpers (`include_tests=True`/`False`). Results:

- **My 5 new comms-footer pins: `5 passed`** (Scan A equality, Scan B equality, granularity re-add,
  Scan B narrowing-adjudication, both-modes).
- **comms_footer routing pin PASSED**; the 4 OTHER migration files (not migrated in scratch) RED —
  expected, out of my scope.
- **∀-mutation `test_dropping_the_shared_parser_reddens_the_adopter_derivation[test_comms_footer.py]`
  PASSED** — sharing proven by mutation (drop → helpers return `{}` → keys change); the isinstance
  guard held (helpers return dicts).
- **Offender scan now names only `{'test_anchored_pattern_seam.py': ['_parse_production_trees']}`**
  — comms_footer SELF-CLEANED out of the offenders once migrated.

At HEAD (un-migrated) the same pins are RED for the right reason: helper absent
(`parse_production_trees` unbuilt) / comms_footer un-migrated / offender scan flags Scan B. The
disk-oracle adjudication + dead-entry + not-vacuous pins are GREEN at HEAD (verified).

`ruff` clean on the file; `py_compile` OK; `mypy` (canonical `scripts/typecheck.sh`) reports NO
errors in `test_ast_reach_helpers.py`. (The runner's "one or more legs failed" is the pre-existing
#333 WIP baseline on this branch, not from my edit — unrelated to this scope.)

## 6. BUILDER NOTE (A-SUB cycle)

- Migrate BOTH comms_footer scans onto `_logging_fixtures.parse_production_trees`:
  - **Scan A** (`TestTheCharsetGuardDoesNotTeachAFalseRationale._scan`, prod AND member tests) →
    `include_tests=True`. The helper MUST re-add `<member>/tests` (the granularity pin enforces it).
    Scan A does TEXT-line scanning, so it consumes the helper's KEYS (paths) then re-reads text.
  - **Scan B** (`TestNoCommsIdentityReachesQueryTEXT._scan`, query-door AST scan) →
    `include_tests=False` (reading b — pending the ruling above). It consumes the helper's ASTs.
- **Route each scan's parse_production_trees call through a NULLARY, DICT-returning tree-derivation
  helper** (e.g. `def _comms_footer_scan_a_trees(): return parse_production_trees(...)`), consumed by
  `_scan`. Do NOT call `parse_production_trees` directly inside `_scan` (it returns `(counts, hits)`,
  which the ∀-mutation cannot key-compare — the isinstance guard now makes that a guided RED, but the
  clean structure avoids it). This matches the design's documented §9.7 pattern and gives the
  ∀-mutation a drivable, dict-returning derivation per scan.
- Retiring Scan B's hardcoded 4-tuple falls out of the migration (the offender scan forces it).
- `_rebind_everywhere` promotion (§10 #3): if A-SUB lands before F, promote it to `_logging_fixtures`
  and prove sharing by mutation. The contract's accessor `_rebind_everywhere_fn()` already tolerates
  either home.

## 7. Housekeeping / flags

- **Scratch tree `/tmp/asub2-scratch-a` could NOT be self-removed** — the sandbox denies `rm -rf`.
  It is a disposable `scratch_copy.sh` tree in `/tmp` (cleared on reboot); please delete it, or I can
  on a granted `rm`.
- **Pre-existing, out-of-scope:** `scripts/typecheck.sh` reports failing mypy legs (the #333 WIP
  baseline on `feat/surreal-unification`) unrelated to this contract file. Flagged, not fixed
  (contract-only scope).
