# REPORT — delta-adversary-asub-3 (contract-adversary, re-grade of §12 un-defeatable-by-spelling A-SUB)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **VERDICT: A-SUB (F4/§12) — CONTRACT INSUFFICIENT.** 1 BLOCKER (r5 continuation of A-SUB-3):
  a routing-not-sharing build STILL survives, moved one placement over from the closed nullary
  shape to a **non-nullary (fixture) private scan**. Plus the carried §12.4 A↔B purpose-swap residual.
- **P1 HEADLINE — a routing-not-sharing wrong build passes the WHOLE contract 47/0, identical to the
  correct reference build.** `_parse_production_trees` is migrated CORRECTLY (routes through the helper —
  the nullary decoy that satisfies every nullary-driven pin), while the `production_trees` **@pytest.fixture
  that feeds every anchored test scans PRIVATELY via `os.walk`**, never through `parse_production_trees`.
  Genuinely non-sharing (fixture keys 129→129 under the drop; the decoy 129→0). Reproduced with controls.
- **Q(a) — the asub-b survivor IS truly closed.** The NULLARY `production_sources`+`ast.parse`+decoy
  survivor now dies at L1 escape + L2 + L3 (4 failed). Fresh NULLARY spellings — `os.walk`, `alias
  ap=ast.parse` — all die at L1. "Un-defeatable-by-spelling" is TRUE **for driven (nullary) code.**
- **Q(b)/r5 CRUX — the DROPPED RIDER (§12.3 both-direction diff) is LOAD-BEARING.** Proven with a
  positive control: on the survivor the adopter's real coverage node STAYS GREEN under
  `parse_production_trees→{}` (declared-RED-stayed-GREEN ⇒ the rider FAILS the build ⇒ CATCH); on the
  correct build it REDDENS (rider passes). L1/L3 miss it because they drive only NULLARY in-process
  derivations — the `_sdk_guard` **v4** failure ("RUNTIME, but armed in N tests → never executed") one layer up.
- **Q4 meta-recursion — CONFIRMED SOUND.** Coverage binds to the ALL-set
  (`_all_workspace_parse_sites()`=`['_logging_fixtures.py::parse_production_trees']`, NON-EMPTY on clean,
  derived from parse-primitive truth), not the offenders set — the v5 empty-on-clean trap is correctly avoided.
- **Q5 §12.4 comms binding — discriminates collapse (bindable=False→RED); BLIND to the A↔B purpose-swap
  (bindable=True→PASS)** — a STATED bound owed to the A-SUB cold-audit hand-check (unchanged residual).
- **MISSING PIN (BLOCKER):** a per-adopter `scripts/mutation_proof.py` both-direction receipt driving each
  adopter's REAL fixture-consuming node under `parse_production_trees→{}`, requiring each declared-RED node
  to actually redden. The contract offers this ONLY as an OR-clause when NO nullary tree-producer exists; a
  decoy supplies one, so it is never demanded. Make it REQUIRED per adopter.
- **Packages considered:** none new — the fix REUSES the in-repo `scripts/mutation_proof.py` both-direction
  diff (already cited by §12.3/§12.5, #194 landing guard); no external library supplies a
  "drive-the-real-node-under-a-mutation" harness. `bespoke (reuse)` — agrees with reviser + §12.5.
- **Satisfiability:** independently reproduced **47 passed / 0 failed** on the reviser's reference build
  (`/tmp/asub3-scr-a`). ⚠ reviser SUMMARY said 46, its TABLE said 47 — my run = 47 (summary undercount, noted).
- **Graded:** working-tree contract (byte-identical to the scratch I ran, diff = empty) = HEAD `15e5540` +
  uncommitted `test_ast_reach_helpers.py` · HEAD-at-report `15e5540` · SAME.
- **Provenance (#140):** `loremaster.__file__ = /tmp/asub3-scr-a/loremaster/loremaster/__init__.py` — every
  wrong build / mutation is against that scratch tree; the main repo was NEVER mutated (git status = only
  the pre-existing 2 files).
- **Decisions-needed:** (1) restore the §12.3 both-direction rider as a REQUIRED per-adopter receipt (the
  BLOCKER fix); (2) the A↔B purpose-swap stays a cold-audit hand-check — confirm the lead's A-SUB build
  brief carries it as an explicit checklist item.

---

## Provenance receipt (#140)

```
$ diff <working-tree contract> </tmp/asub3-scr-a .../test_ast_reach_helpers.py>  -> IDENTICAL
$ /tmp/asub3-scr-a/.venv/bin/python -c "import loremaster; print(loremaster.__file__)"
  /tmp/asub3-scr-a/loremaster/loremaster/__init__.py
$ git status --short   # main repo, throughout: ONLY the pre-existing edits
   M loremaster/tests/test_ast_reach_helpers.py
   M scripts/test_wave_gate.py
```
`/tmp/asub3-scr-a` is the reviser's `scratch_copy.sh` reference build (the 3 helpers + the runtime
`install_parse_guard` in `_logging_fixtures.py` + all 5 adopters migrated). I verified its contract file is
byte-identical to the working tree before trusting it, then mutated ONLY the anchored adopter (with a
`cp -a` content backup `/tmp/anchored.ORIG`, restored after every probe).

---

## THE BLOCKER (r5) — routing-not-sharing survives via a NON-NULLARY (fixture) private scan

### The wrong build (a plausible incomplete migration)

`_parse_production_trees` is migrated **correctly** — it routes through the sanctioned helper. That nullary
tree-producer is what every nullary-keyed pin drives, so it satisfies them all. But the `production_trees`
**fixture** that actually feeds every anchored test is rewired to scan privately:

```python
def _parse_production_trees() -> dict[str, ast.Module]:
    from _logging_fixtures import parse_production_trees              # MIGRATED — the decoy
    return parse_production_trees(include_scripts=True, include_skills=False)

@pytest.fixture(scope="module")
def production_trees() -> dict[str, ast.Module]:                      # NOT migrated — the real scan
    import os
    trees = {}
    for base in (_REPO_ROOT/"loremaster"/"loremaster", _REPO_ROOT/"lorerunes"/"lorerunes",
                 _REPO_ROOT/"lorescribe"/"lorescribe", _REPO_ROOT/"loresigil"/"loresigil",
                 _REPO_ROOT/"scripts"):
        for dirpath, _dirs, files in os.walk(base):
            for fname in files:
                if fname.endswith(".py"):
                    p = Path(dirpath)/fname
                    trees[p.relative_to(_REPO_ROOT).as_posix()] = ast.parse(p.read_text(encoding="utf-8"))
    return trees
```

The fixture is behaviour-faithful (its key set is **identical** to `parse_production_trees`, 129 keys), so
anchored's own tests pass. Full-contract result:

```
$ .venv/bin/python -m pytest loremaster/tests/test_ast_reach_helpers.py -q
  47 passed in 39.08s          # <-- byte-identical verdict to the CORRECT reference build (47/0)
```

### Why every layer is blind (empirically shown, not reasoned)

```
ALL-set sites: ['_logging_fixtures.py::parse_production_trees']
   -> survivor fixture 'production_trees' in ALL-set?: False        # os.walk source ∉ ALL-set vocab
L2 offenders in anchored: []                                        # 'walk' excluded; no alias needed
L1 drivable scan candidates (anchored): ['_scanned_roots','_parse_production_trees']  # fixture EXCLUDED
L3 nullary tree-producers (anchored): ['_parse_production_trees']   # only the decoy; fixture EXCLUDED
   -> production_trees is a @pytest.fixture -> EXCLUDED from ALL in-process driving
```

- **L1 escape invariant & L3 ∀-mutation** drive `_nullary_derivations(...)` — module-level `def`s and
  `self`-only methods, with `@pytest.fixture` nodes explicitly excluded. The real scan lives in the
  fixture, so neither ever reaches it; both drive the **decoy** (`_parse_production_trees`), which routes
  through the helper → sanctioned (no escape) and reflects the drop (∀ passes).
- **L1 coverage pin** (`test_every_whole_workspace_parse_site_was_watched_executing`) enumerates the ALL-set
  from `_parses_whole_workspace` = parse-primitive `{parse,compile}` **AND** source
  `_WHOLE_WORKSPACE_SOURCE_CALL_NAMES = {production_sources, workspace_roots, parse_production_trees}`. A
  private `os.walk` (or a hard-coded-tuple `rglob`) scan uses **none** of those three source names, so it is
  never in the ALL-set → never named as unobserved.
- **L2 lint** deliberately excludes `walk` (the `ast.walk` collision) from its directory-source set, so an
  `os.walk` scan trips no directory leg — no alias even needed. (A `rglob`-over-hard-coded-tuple scan WOULD
  trip L2 un-aliased, but is dodged by one alias `ap=ast.parse`; `os.walk` needs neither.)

### Q(a) control — the redesign genuinely closes the NULLARY class (fair to the reviser)

| wrong build | real-scan placement | verdict |
|---|---|---|
| v1 nullary `production_sources`+`ast.parse` + decoy (asub-b's original survivor) | nullary | **CAUGHT** L1+L2+L3+canonical (4 failed) |
| v3 nullary `os.walk` + decoy | nullary | **CAUGHT** L1 escape (`_parse_production_trees parsed PRIVATELY`) |
| v4 nullary `alias ap=ast.parse` + `production_sources` + decoy | nullary | **CAUGHT** L1 escape |
| **v2 fixture `os.walk` + correctly-migrated decoy** | **non-nullary** | **SURVIVES 47/0 (BLOCKER)** |

The reviser's report table claims "os.walk → CAUGHT" — TRUE, but that was a **nullary** os.walk derivation
(`_is_scan_candidate` lists `walk` as a reach signal, so a nullary os.walk scan is DRIVEN and the chokepoint
catches its parse). The finding is **placement, not spelling**: Layer 1 is un-defeatable-by-spelling only
over the code it DRIVES, and it drives only nullary derivations.

### Q(b)/r5 CRUX — the dropped rider WOULD have caught it (proven with a positive control)

The reviser (§D decision 1) dropped §12.3's both-direction diff, arguing *"L1 already catches the
private-scan survivor robustly and alias-agnostically."* That is FALSE for the non-nullary consumer — which
is exactly where the real scan lives (the reviser's own `_nullary_derivations` docstring: *"anchored's
coverage node takes a `production_trees` FIXTURE (not nullary)"*). Driving the adopter's REAL coverage node
under `parse_production_trees→{}` (the dropped rider, via the `scripts/mutation_proof.py` receipt route):

```
############ SURVIVOR BUILD ############
  fixture keys: healthy=129  under-drop=129  KEYS-CHANGED=False
  anchored coverage node: healthy=GREEN  under-drop=GREEN
  LEG1 sharing: NON-SHARING (fixture ignores the drop)
  LEG2 both-direction-diff: under-drop coverage = GREEN
       -> declared-RED coverage node STAYED GREEN -> rider FAILS THE BUILD -> routing-not-sharing CAUGHT
############ CORRECT BUILD (positive control) ############
  fixture keys: healthy=129  under-drop=0  KEYS-CHANGED=True
  anchored coverage node: healthy=GREEN  under-drop=RED(missing loremaster,lorerunes,lorescribe,loresigil,scripts)
  LEG1 sharing: SHARES (fixture follows the drop)
  LEG2 both-direction-diff: under-drop coverage = RED -> REDDENED -> rider PASSES (sharing proven)
```

The rider **discriminates** (P0 control): it reddens on the correct build under the drop and stays green on
the survivor. It is not an unconditional pass. **Dropped-rider verdict: LOAD-BEARING.** (Instrument: the
harness `_rebind_everywhere(real, lambda:{}) ` + replicate anchored's coverage assertion on a freshly-built
fixture — pasted verbatim in the Probe Record below, since scratch is disposable.)

### Why not close it in the coverage pin instead? (honest bound on the alternative fix)

Broadening `_WHOLE_WORKSPACE_SOURCE_CALL_NAMES` to include the generic directory walkers
(`{rglob,glob,iglob,iterdir,walk}` — the set L2 already partially uses) would pull the `os.walk`/hard-coded
fixture INTO the ALL-set, so the "watched-executing" pin would name it (non-nullary ⇒ undriven ⇒ unobserved).
That closes `os.walk`/`rglob`-hard-coded but is **alias-defeatable** (the ALL-set is parse-name-keyed:
`ap=ast.parse` drops back out). The ROBUST fix is the both-direction diff on the real node — it observes the
EFFECT (does the node's output depend on the shared parser), not the spelling. So the dropped rider is the
right instrument, not a coverage-pin patch.

---

## THE MISSING PIN (the test that should exist + the defect it catches)

**BLOCKER — bind the ∀ to CONSUMPTION by the adopter's REAL node, not to any nullary helper-caller.**
For each declared adopter in `_MIGRATION_SET`, a `scripts/mutation_proof.py` both-direction receipt that
(a) declares the adopter's real fixture-consuming coverage/domain node id(s) expected-RED under
`parse_production_trees→{}` (from `--collect-only`, #194), (b) runs them under the drop, and (c) FAILS if any
declared-RED node stays GREEN (= the adopter feeds it from a private, non-nullary scan = routing-not-sharing).

*Catches:* the v2 survivor — `_parse_production_trees` migrated correctly while the `production_trees` fixture
scans privately. Reproduced above; the both-direction diff reddens on the correct build and stays-green→FAILs
on the survivor (positive control shown).

*Why the current contract misses it:* `test_dropping_the_shared_parser_reddens_the_adopter_derivation`
offers the `scripts/mutation_proof.py` receipt ONLY as an OR-clause reached when `assert derivations` is EMPTY
(no nullary tree-producer). A decoy provides a nullary tree-producer, so the OR-clause is never reached and
the real fixture scan is never checked. The receipt must be REQUIRED per adopter (or L3 must drive the
adopter's real fixture-fed node, not merely a nullary derivation that CALLS the helper).

**RESIDUAL (carried, not new) — §12.4 A↔B purpose-swap.** `test_each_include_tests_mode_binds_to_a_DISTINCT_scan_scope`
catches collapse/dropped-mode (`bindable=False`→RED, verified) but PASSES a pure purpose-swap (Scan-A-by-purpose
given `include_tests=False`, `bindable=True`, verified). Owed to the A-SUB cold-audit hand-check (reviser
decision 2; matches delta-adversary-asub-b pin 2). Confirm the lead's A-SUB build brief carries it as an
explicit checklist item.

---

## P1b — QUANTIFIER TABLE (invariant: ∀-over-inputs vs guarded)

| invariant | ∀ or guarded | receipt |
|---|---|---|
| every declared member has a parsed tree | **∀ over declared members** | oracle from pyproject, independent; fail-closed on `{}`; missing-member names it (`TestAssertScanReachedEveryMember`, 5 pins green on reference) |
| no test file hand-rolls a whole-tree parser (L2) | **∀ over the tree, GUARDED by the directory-source vocab** | DERIVED + allowlist-the-safe; catches `production_sources`+`ast.parse` (un-aliased) — **but `walk` excluded + alias-defeatable ⇒ the os.walk/aliased tail is unguarded (contributes to BLOCKER)** |
| no private parse escapes the sanctioned parser at runtime (L1 escape) | **∀ over DRIVEN nullary derivations** — GUARDED by nullary placement | catches every nullary spelling (v1/v3/v4); **a non-nullary fixture scan is never driven ⇒ unguarded (BLOCKER)** |
| every whole-workspace parse SITE watched executing (L1 coverage) | **∀ over the ALL-set** — GUARDED by the source vocab `{production_sources,workspace_roots,parse_production_trees}` | NON-EMPTY on clean (avoids v5 trap, Q4 sound); **a private os.walk/hard-coded scan ∉ ALL-set ⇒ unguarded (BLOCKER)** |
| every adopter's derivation reflects the shared-parser drop (L3 ∀) | **∀ over `_MIGRATION_SET` × NULLARY tree-producers** — GUARDED by nullary placement | reddens the genuine adopter (correct build under drop); **a decoy provides the nullary derivation while the real fixture scan is exempt (BLOCKER)** |
| Scan-B narrowing drops only member-test files | **∀ over the dropped set** | non-vacuous (asub-b confirmed; unchanged) |
| comms_footer include_tests re-adds EXACTLY `<member>/tests` | **∀ over member roots** | equality both directions; fires on a narrowing helper |

The BLOCKER is the three "GUARDED by nullary placement / narrow source vocab" rows: the sharing ∀ is
quantified over the DRIVEN nullary surface, leaving the real (fixture) consumer — where the scan actually
lives — unquantified.

## P1c — REACH TABLE (per instrument)

| instrument | reach set | DERIVED / hand-list | coverage a checked var | effect vs proxy | one-source proven by mutation | verdict |
|---|---|---|---|---|---|---|
| used-ness (`_calls_shared_parser` ∀ `_MIGRATION_SET`) | files that CALL the helper | `_MIGRATION_SET` literal, each entry re-derived | a CALL exists, file-level | **PROXY** (a decoy call satisfies it) | n/a | **PARTIAL** (decoy) |
| L2 offender lint | every test file's whole-tree clones minus allowlist | DERIVED (allowlist-the-safe) | YES (planted clone flagged, self-cleans) | STATIC name-keyed | n/a | **BLIND to `os.walk` + alias** (feeds BLOCKER) |
| **L1 escape invariant** | **DRIVEN nullary scan candidates** | DERIVED but **bounded to NULLARY** | over EXECUTED nullary code | EFFECT (runtime chokepoint) | catches every nullary spelling | **BLIND to non-nullary fixture (BLOCKER)** — the `_sdk_guard` v4 shape (armed-in-pins, not autouse) |
| **L1 coverage (ALL-set watched)** | **`_all_workspace_parse_sites()`** | DERIVED from parse-primitive truth (NOT offenders — Q4 sound) | YES, NON-EMPTY on clean | EFFECT (observed executing) | n/a | **narrow SOURCE vocab omits os.walk/hard-coded ⇒ misses non-nullary private scan (BLOCKER)** |
| **L3 ∀-mutation** | `_MIGRATION_SET` × **NULLARY tree-producers** | DERIVED but **bounded to NULLARY** | YES for nullary helper-callers/private scans | EFFECT (drops parser, watches keys) | reddens a genuine nullary adopter; **a decoy satisfies it while the fixture scan is exempt** | **BLIND to non-nullary fixture (BLOCKER)** |
| `assert_scan_reached_every_member` | workspace members | DERIVED (pyproject, independent) | YES (fail-closed `{}`, equality both ways) | EFFECT | n/a | **SOUND** |
| §12.4 comms binding | comms_footer parse_production_trees call scopes | DERIVED (AST scopes) | YES (collapse→RED, verified) | STATIC | n/a | **SOUND for collapse; BLIND to A↔B purpose-swap (stated bound)** |

**Legs run:** EMPIRICAL for every A-SUB row (reference build + 4 wrong builds + `_rebind_everywhere`
mutation + positive control, all in scratch). The §12.4 purpose-swap row is construction-inspection +
synthetic AST exercise (the contract itself documents that a lexical purpose-binding is unreliable
post-migration).

---

## Full probe record (commands + real output)

### 1. Satisfiability + RED discipline
```
diff working-tree contract vs /tmp/asub3-scr-a contract        -> IDENTICAL (grading the right contract)
pytest test_ast_reach_helpers.py (reference build)             -> 47 passed in 38.91s
```
Reviser summary said 46, table said 47 — my independent run = **47**. Minor summary undercount; no C-DEF.

### 2. Q(a) — asub-b's original survivor now CAUGHT (v1)
```
FAILED ...TestTheMigrationSetRoutesThroughTheSharedHelpers::test_the_canonical_clone_is_removed_from_the_anchored_scan
FAILED ...TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist::test_no_unallowlisted_whole_tree_parser_clone_survives
FAILED ...TestNoPrivateParseEscapesTheSanctionedParserAtRuntime::test_no_declared_adopter_parses_privately
FAILED ...TestSharingProvenByMutation::test_dropping_the_shared_parser_reddens_the_adopter_derivation[test_anchored_pattern_seam.py]
  -> "keys unchanged: 113 ... routing-not-sharing: a private production_sources+ast.parse copy"
4 failed, 24 passed
```

### 3. Fresh nullary spellings CAUGHT (v3 os.walk, v4 alias)
```
v3 nullary os.walk  -> FAILED test_no_declared_adopter_parses_privately  (1 failed, 12 passed)
v4 nullary alias    -> FAILED test_no_declared_adopter_parses_privately  (1 failed, 46 deselected)
```

### 4. THE BLOCKER — v2 non-nullary fixture os.walk SURVIVES
```
private-fixture keys: 129 | helper keys: 129 | identical: True     # behaviour-faithful, anchored tests pass
pytest test_ast_reach_helpers.py (v2 build)  -> 47 passed in 39.08s  # identical to correct
ALL-set sites: ['_logging_fixtures.py::parse_production_trees']   (fixture NOT in ALL-set)
L2 offenders in anchored: []
L1 drivable scan candidates: ['_scanned_roots','_parse_production_trees']  (fixture excluded)
L3 nullary tree-producers: ['_parse_production_trees']                     (fixture excluded)
```

### 5. Dropped-rider proof (harness — pasted verbatim, scratch is disposable)
```python
import sys; sys.path.insert(0,"loremaster/tests")
import ast, tomllib; from pathlib import Path
import _logging_fixtures as LF, test_anchored_pattern_seam as A, test_store_seam_one_derivation as SS
REPO=Path(LF.__file__).resolve().parents[2]; rebind,real=SS._rebind_everywhere,LF.parse_production_trees
def fresh(): fn=A.production_trees; return (fn.__wrapped__ if hasattr(fn,"__wrapped__") else fn)()
def cov(t):
    d=set(tomllib.loads((REPO/"pyproject.toml").read_text())["tool"]["uv"]["workspace"]["members"])
    return "GREEN" if {k.split("/",1)[0] for k in t}==(d|{"scripts"}) else "RED"
h=set(fresh()); hv=cov(fresh())
with rebind(real, lambda *a,**k:{}): dk=set(fresh()); dv=cov(fresh())
# SURVIVOR: h==dk (129==129), hv==dv=="GREEN"  -> declared-RED node stayed GREEN -> rider CATCHES
# CORRECT : dk=={} (0), dv=="RED"              -> reddens -> rider passes (discriminates)
```
Output (both builds) shown in the Q(b) section above.

### 6. §12.4 comms binding discrimination
```
distinct(correct)      bindable=True    (PASS)
collapsed(wrong)       bindable=False   (RED — caught)
A<->B purpose-swap     bindable=True    (PASS — stated bound, cold-audit hand-check)
```

---

## Verdict

**A-SUB (F4/§12): CONTRACT INSUFFICIENT** — the routing-not-sharing class A-SUB exists to close still has a
surviving shape: the real scan in a **non-nullary (`@pytest.fixture`) consumer** via a source outside the
ALL-set vocabulary (`os.walk`), with a correctly-migrated nullary decoy satisfying every nullary-driven pin.
It passes the whole contract 47/0, is genuinely non-sharing, and the DROPPED §12.3 both-direction rider WOULD
have caught it (proven with a positive control). Missing pin: a per-adopter `scripts/mutation_proof.py`
both-direction receipt driving each adopter's REAL fixture node under `parse_production_trees→{}`, required —
not merely offered as an OR-clause a decoy defeats. The §12.4 A↔B purpose-swap residual is unchanged (owed to
the cold audit).

The redesign's core claim — **un-defeatable-by-spelling for driven (nullary) code** — is TRUE and verified;
the gap is **placement**, the `_sdk_guard` v4 lesson one layer up (a runtime gate armed inside its own pins
is an invariant only over the code those pins DRIVE). Escalation note for the lead: this is the SAME class
(A-SUB-3) surviving another wave — but the fix is a KNOWN, SPECIFIED instrument (§12.3's own rider), dropped,
not a novel design gap. Restore the rider rather than briefing a fourth spelling-patch.
