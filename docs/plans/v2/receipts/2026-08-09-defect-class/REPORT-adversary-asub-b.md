# REPORT — adversary-asub-b (contract-adversary, A-SUB / F4 + B / #345)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK (read first)

- **VERDICT: A-SUB (F4) — CONTRACT INSUFFICIENT.  B (#345) — CONTRACT INSUFFICIENT.**
- **P1 headline — a "fixed nothing" build passes:** A-SUB goes **16 passed / 0 failed** with
  3 of its 4 migration files "migrated" by nothing but one **unused** `from _logging_fixtures
  import … as _asub_route  # noqa: F401` each — `test_secret_typing`'s `_SCANNED_MEMBERS` hand-list
  and THREE private `rglob("*.py")` clones all survive. Consolidation contract certifies zero
  consolidation. **B** cannot reach 0-failed on the build Ruling 2 declares CORRECT: Leg 2
  false-flags `blocked_by`'s `[render_attributed(b) for b in …]` render; the only escape is the
  Ruling-2-FORBIDDEN allowlist entry (a false clear reopening the #345 mis-park class).
- **DRY / sharing proof (priority #1):** the sharing property has **no RED home in the A-SUB
  contract** — a routing-not-sharing adopter (imports the helper, derives via private
  `production_sources`, no `rglob`) passes both static pins AND survives the parse-mutation. Same
  class the sibling E+H contract was found INSUFFICIENT for.
- **REACH TABLE (P1c):** body §"P1c REACH TABLE". Two A-SUB instruments are HAND-LISTS
  (`_MIGRATION_SET`, the anchored-only clone check); a new-file whole-tree clone is invisible.
- **MISSING PINS:** body §"MISSING PINS" — 5 for A-SUB, 3 for B, each with a reproduction.
- **`blocked_by` verdict (asked):** **forgery DOOR** (Ruling 2 correct); HEAD render is genuinely
  contained (hostile value does not `_leaks`); B's Leg 2 detector is the defect, not the code.
- **Fixture discrimination:** B's Leg 1 mis-park/vacuous-drive detection + retirement superset
  proof + hostile fixture all DISCRIMINATE (verified). A-SUB helper-behavior pins are SOUND
  (fail-closed on `{}`, oracle-independent). The rot is in the migration/sharing pins only.
- **Graded: 405d321 · HEAD-at-report: 405d321 · SAME.** Contract dated to `641f758`; HEAD is 2
  docs-only commits ahead (`e1dfa14`, `405d321`) — no target code moved.
- **Packages considered:** none new — A-SUB is stdlib `ast`+`pathlib.rglob`+`tomllib` glue
  (project-specific; no library provides "parse every workspace-member tree keyed by repo-relative
  posix"); B reuses the existing `test_link5` interpolation predicates (no new mechanism). `bespoke`
  is correct on both.
- **Provenance (#140): `loremaster.__file__ = /tmp/asubb-scr/loremaster/loremaster/__init__.py`**
  (scratch built via `scripts/scratch_copy.sh`; `--verify-only` re-confirmed all 4 members resolve
  inside the copy). Every run below is against that scratch tree, never the main repo.

---

## Instruments (durable — pasted so this report is self-contained)

- **Reference A-SUB helpers** (`parse_production_trees` + `assert_scan_reached_every_member`) built
  in scratch to run the satisfiability + mutation proofs: pasted verbatim in §"Reference A-SUB
  helpers" below.
- **The Leg-2 comprehension-blindness probe** and the **routing-not-sharing wrong build** are
  pasted in their sections.

---

## A-SUB (F4) — `test_ast_reach_helpers.py`

### What is SOUND (receipts, so a SUFFICIENT-looking core is not mistaken for the whole)

The two shared helpers, once built, are genuinely well-pinned. With the reference impl in place:

```
$ uv run pytest .../test_ast_reach_helpers.py::TestParseProductionTrees \
      .../test_ast_reach_helpers.py::TestAssertScanReachedEveryMember -p no:xdist -q
9 passed in 3.52s
```

`test_it_fails_closed_on_an_empty_derivation` (raises on `{}`), `test_the_oracle_is_independent_of_the_subject`
(one-member-only dict raises naming the others), `test_an_undeclared_extra_package_raises`, and
`test_a_missing_member_raises_and_names_it` are all real, discriminating pins. The **mutation proof
works for a GENUINELY-shared adopter**: after migrating the anchored parser to call
`parse_production_trees`, source-editing that helper to `return {}` reddens the anchored coverage:

```
$ # parse_production_trees -> return {}   (source edit)
$ uv run pytest .../test_anchored_pattern_seam.py::TestScanCoverage::test_the_scan_reaches_every_production_tree -p no:xdist -q
1 failed   (declared-not-scanned: 'loremaster','loresigil','lorescribe','lorerunes',…)
```

So the coverage machinery is not the problem. The **reach of the migration/anti-dup pins is.**

### BLOCKER A-SUB-1 — the routing pin passes an UNUSED import; the contract certifies zero consolidation

`TestTheMigrationSetRoutesThroughTheSharedHelpers.test_the_file_routes_through_a_shared_reach_helper`
uses `_imports_a_shared_reach_helper`, which returns True iff the file contains an `ast.ImportFrom`
of `parse_production_trees`/`assert_scan_reached_every_member`. It never checks the import is USED,
nor that the file's private parser/coverage is gone. Reproduction — I added ONE unused import to each
of the 3 non-anchored files and touched nothing else:

```
$ # each of test_backoff_seam / test_secret_typing / test_secret_leak_vectors gains:
$ #   from _logging_fixtures import parse_production_trees as _asub_route  # noqa: F401
$ uv run pytest .../test_ast_reach_helpers.py -p no:xdist -q
16 passed in 3.52s
$ grep -nE "_asub_route|_SCANNED_MEMBERS: tuple|rglob" .../test_secret_typing.py
40: from _logging_fixtures import parse_production_trees as _asub_route  # noqa: F401,E402
123:_SCANNED_MEMBERS: tuple[tuple[str, str], ...] = (          # <-- hand-list SURVIVES
183:            for path in sorted(root.rglob("*.py"))          # <-- private clone SURVIVES
1314:        for source_path in sorted(root.rglob("*.py")):     # <-- private clone SURVIVES
1342:            for path in sorted(root.rglob("*.py"))          # <-- private clone SURVIVES
$ grep -rn "_asub_route" (used anywhere?)  ->  (nothing: the routing import is unused in all 3)
```

`test_secret_typing`'s duplicate `_SCANNED_MEMBERS` (the #291-shaped drift the design wanted "killed
for free") and all three of its private whole-tree parse loops survive, and A-SUB is fully GREEN.
**A builder that satisfied this contract perfectly but fixed nothing (3 unused imports) ships.**

### BLOCKER A-SUB-2 — `_MIGRATION_SET` is a hardcoded adopter hand-list (§7-FORBIDDEN); a new/other clone is invisible

`_MIGRATION_SET` is `("test_anchored_pattern_seam.py","test_backoff_seam.py","test_secret_typing.py",
"test_secret_leak_vectors.py")` — a literal 4-file tuple. Design §7 (line 744-747) is explicit: *"The
design must NOT hardcode an adopter list. A list of 'the files to migrate' … IS the enumeration
antipattern."* The clone-removal pin (`test_the_canonical_clone_is_removed_from_the_anchored_scan`)
inspects ONLY `test_anchored_pattern_seam.py`. So the clone-check reach is a hand-list too. Design §7
(line 748-752, and §7 Q3) REQUIRED an ANTI-DUPLICATION STRUCTURAL PIN (*"no test file hand-rolls
rglob+ast.parse outside an evidence-backed non-adopter allowlist … Without this pin, 'migrated' is a
claim over the files someone remembered — the exact class"*). It is **not built.** Reproduction — a
new file with a full `rglob`+`ast.parse`+`read_text` clone is invisible:

```
$ # before planting: 3 failed, 13 passed
$ # plant loremaster/tests/test_zzz_new_whole_tree_scanner.py  (full rglob+parse+read_text clone)
$ uv run pytest .../test_ast_reach_helpers.py -p no:xdist -q
3 failed, 13 passed         # <-- IDENTICAL. the clone adds zero failures.
$ # _MIGRATION_SET contains it? -> False
```

This is §7's own warning realized: *"A-SUB is itself an instance of the class … its REACH is which
callers actually adopt it, and if that reach is a hidden constant … A-SUB is a 15th copy nobody
adopts."* The contract's docstring (lines 320-329) justifies dropping the structural pin as "the
enumerate-the-forbidden antipattern" — but a *deny-hand-rolled-parser-outside-an-allowlist* scan is
**allowlist-the-safe** (the design even specified the allowlist), i.e. the CORRECT pattern, not the
antipattern. The justification does not hold; the reach stayed a hand-list.

### BLOCKER A-SUB-3 — the sharing property has NO RED home; routing-not-sharing survives the mutation

Even for the one file it fully checks (anchored), the static half cannot tell sharing from routing.
Wrong build (pasted below): from-import the helper (satisfies routing), derive trees privately via
`production_sources` (no `rglob` → clone detector blind), never call `parse_production_trees`:

```python
from _logging_fixtures import parse_production_trees, production_sources  # noqa: F401
def _parse_production_trees() -> dict[str, ast.Module]:
    trees = {}
    for _label, path in production_sources(include_scripts=True, include_skills=False):
        trees[path.relative_to(_REPO_ROOT).as_posix()] = ast.parse(path.read_text(encoding="utf-8"))
    return trees
```
```
$ # both static pins on this wrong build:
$ uv run pytest ".../routes_through[test_anchored_pattern_seam.py]" ".../canonical_clone_is_removed" -p no:xdist -q
2 passed
$ # now mutate parse_production_trees -> return {} and re-run the anchored coverage:
$ uv run pytest ".../TestScanCoverage::test_the_scan_reaches_every_production_tree" -p no:xdist -q
1 passed          # <-- SURVIVES. mutation does not reach it. routing-not-sharing is invisible.
```

The contract delegates the mutation proof to prose ("a BUILDER/adversary RUNTIME receipt … requires a
scratch mutation this read-only contract cannot make"). That is the exact E+H-class miss the brief
flagged. Note a genuine subtlety I confirmed: the from-import form the routing pin *mandates* binds
the helper's function object locally, so an in-process `monkeypatch.setattr(_logging_fixtures,
"parse_production_trees", …)` would NOT reach a from-import adopter — so the sharing proof genuinely
cannot be an ordinary pytest pin; it must be a **committed, run-and-recorded receipt** (the repo
already ships `scripts/mutation_proof.py`, which takes expected-RED node-ids and diffs both ways —
the right instrument). The contract has neither the pin nor a required-receipt hook.

### A-SUB-4 (residual) — `_SCANNED_MEMBERS` retirement has no pin
The design names retiring `test_secret_typing._SCANNED_MEMBERS` as an explicit A-SUB deliverable.
No A-SUB pin asserts it is gone (shown surviving under A-SUB-1). Add a pin: `_SCANNED_MEMBERS` (and
any per-file member hand-list) is absent from the migrated files.

### A-SUB-5 (minor) — routing detector recognizes only `from`-import, false-flags module-attribute sharing
`_imports_a_shared_reach_helper` matches only `ast.ImportFrom`. A genuinely-sharing adopter written
`import _logging_fixtures; _logging_fixtures.parse_production_trees(...)` FAILS the routing pin
(measured: my first correct migration failed it). This is the six-defeats shape one level down
(enumerate ONE import spelling) — and it is the *only* spelling a module-attribute mutation proof
could reach, so the pin pushes builders toward the mutation-proof-hostile spelling.

---

## B (#345) — `test_render_slot_inventory.py`

### RED baseline is honest
At HEAD: `2 failed, 8 passed` — both failures driven solely by the empty `_SERVED_SAFE_FIELDS`. The
#345 production fix is ALREADY in at HEAD: `test_the_drain_row_task_id_slot_is_driven_with_content`,
the hostile-multiline fixture, and both retirement superset proofs all PASS.

### What is SOUND (receipts)
- **Leg 1 mis-park / vacuous-drive discrimination WORKS.** Mutating the manifest to move
  `InboxEntry.task_id` DOOR→SAFE (the exact #345 mis-park) reddens Leg 1: `task_id` is no longer
  observed-with-content and surfaces as an offender; the dedicated control also reddens. Verified.
- **Retirement superset proof discriminates.** `old-net (12) − driven (42) == []` at HEAD; dropping
  a probe for any old-net method reddens `test_every_old_net_method_is_a_derived_driven_render`.
- **Non-vacuity + hostile-fixture + leak-predicate controls all fire.**

### BLOCKER B-1 — Leg 2 false-flags the `render_attributed`-comprehension Ruling 2 declares correct → unsatisfiable without a forbidden false clear

`blocked_by` verdict (asked): **it is a forgery DOOR** — `TaskSpecItem.blocked_by` is unconstrained
caller text echoed verbatim (Ruling 2 is right). At HEAD `_render_task_rows` renders it
`blocked_by {[render_attributed(blocker) for blocker in task.blocked_by]}`, which is **genuinely
contained** — a hostile value does not leak:

```
$ # production _render_task_rows with blocked_by=[HOSTILE_MULTILINE]
HOSTILE blocked_by leaks? False        # each element sits in a width-sized render_attributed span
```

But B's `_served_slots` marks `contained=True` only for a *direct* `render_attributed(...)`/
`render_fenced(...)` call as the whole value expression. A comprehension is invisible to it — it
cannot distinguish the CORRECT render from the two Ruling 2 wants flagged:

```
CORRECT render_attributed-comprehension: blocked_by (field,contained) = [('blocked_by', False)]
LEAKING safe_str:                        blocked_by (field,contained) = [('blocked_by', False)]
LEAKING bare list-repr:                  blocked_by (field,contained) = [('blocked_by', False)]
```

Consequence, reproduced: populate `_SERVED_SAFE_FIELDS` with the correct SAFE set (all charset-gated
identities + opaque ids, `blocked_by` EXCLUDED per Ruling 2) → B stays RED with `blocked_by` as the
**sole residual**:
```
$ uv run pytest .../test_render_slot_inventory.py -p no:xdist -q
1 failed, 9 passed   →  _render_task_rows:4641 serves 'blocked_by' UNCONTAINED
```
The only way to green B is to add `blocked_by` to `_SERVED_SAFE_FIELDS` → `10 passed`. But that is
the **exact #345 mis-park Ruling 2 forbids by name** (a door parked SAFE), and once allowlisted Leg 2
would wave through a `safe_str(blocked_by)` revert too. The builder's writable set is the two test
files (design §5); `server.py` is not in it, so reshaping the render is out of scope — and Ruling 2
says the HEAD render is already correct. **B is internally inconsistent: Ruling 2 blesses the HEAD
render that Leg 2 flags, and the contract cannot go 0-failed on that build without a false clear.**

MISSING PIN / fix: `_served_slots` must recognize element-wise / collection containment — a value
expression where every vocab-field-bearing leaf is under a `_CONTAIN_VERBS` call (comprehension,
`", ".join(...)` wrapped, etc.) is `contained=True`; a bare/`safe_str`/`sanitise_line` element is
`contained=False`. Then the correct `blocked_by` render is GREEN, a `safe_str`/repr revert is RED —
the discriminating pin Ruling 2 actually mandates — and `blocked_by` never needs allowlisting.

### B-2 (residual) — field-name-keying collision is documented for `task_id` only; `kind` is also split
Two fields are DOOR in one model / SAFE in another: `task_id` (DOOR `InboxEntry` / SAFE `Agent`,
`Message` — has a dedicated control) and **`kind`** (DOOR `Finding`,`RecalledMemory` / SAFE
`MemorySource` — NO dedicated control). Currently moot (`kind` is not served by any driven render, so
never needs allowlisting), so it is a latent bound, not a live defect — but the contract's documented
bound (lines 58-62) names only `task_id`. Re-open trigger: a render begins serving `MemorySource.kind`.
Either extend the bound text to name `kind`, or add a `kind` dedicated control mirroring `task_id`'s.

### B-3 (residual) — Ruling 2's required comment-correction has no home in the contract
Ruling 2 (§8) calls the `_render_task_rows` comment (server.py ~4631, *"defense-in-depth, though this
field is NOT live-forgeable"*) a served-English defect to correct. It is still present at HEAD, and no
B pin requires it changed. Served-English is a known-hard class (no AST pin), so this is a checklist
item for the builder/cold audit, not a mechanical miss — flagged so it is not silently dropped.

### B — retirement-proof observation (minor)
The retirement pins import `_RENDER_DRIVERS` at call time. Once the builder DELETES `_RENDER_DRIVERS`
(the retirement action) these pins raise `ImportError` rather than cleanly retiring, so the builder
must delete the pins in lockstep; nothing observes that the superset held *at the moment of* deletion.
Inherent to a snapshot gate — noted, not a blocker.

---

## P1c REACH TABLE (per instrument)

| instrument | reach set | DERIVED or hand-list | coverage a checked var | effect vs proxy | one source proven by mutation | verdict |
|---|---|---|---|---|---|---|
| A-SUB routing pin (`_imports_a_shared_reach_helper` ∀ `_MIGRATION_SET`) | which files must adopt | **HAND-LIST** (`_MIGRATION_SET`, 4 literals) | **NO** — checks import *presence*, not use; other/new files absent | **PROXY** — an unused import statement, not actual sharing | **NO** — unused import passes; routing-not-sharing survives mutation | **MISSING PIN (A-SUB-1/-3/-5)** |
| A-SUB clone-removal (`_has_tree_parser_clone`) | which files are clone-checked | **HAND-LIST** (only `test_anchored_pattern_seam.py`) | **NO** — new/other-file clones invisible | n/a | n/a | **MISSING PIN (A-SUB-2)** |
| A-SUB `assert_scan_reached_every_member` | workspace members scanned | DERIVED (pyproject, independent oracle) | YES (fail-closed on `{}`; equality both directions) | EFFECT (consumes actual scanned trees) | reddens under source-edit mutation *iff adopter genuinely shares* | **SOUND** |
| A-SUB `parse_production_trees` behavior pins | keys == rglob(workspace_roots) | DERIVED (independent rglob) | YES | EFFECT | n/a | **SOUND** |
| B Leg 1 (observed-with-content ∨ allowlist) | every driven render's str-ish slots | DERIVED (render AST via `_render_probes`) | YES (mis-park & vacuous-drive redden) | EFFECT (runs over-drive, byte-checks `Model.field` tokens) | manifest mutation moves it (coupled) | **SOUND** |
| B Leg 2 (contained ∨ allowlist) | every driven render's str-ish slots | DERIVED (render AST) | reach YES, **containment detector FALSE-FLAGS comprehensions** | STATIC | n/a | **DEFECTIVE (B-1)** |
| B retirement superset proof | old `_RENDER_DRIVERS` ⊆ derived driven net | DERIVED (`_RENDER_DRIVERS` + `_render_probes`) | YES (reddens on dropped slot) | EFFECT (drives forgery, checks marker) | n/a | **SOUND** (pre-deletion) |

Legs run: **empirical** for every A-SUB row and every B row (reference build + wrong builds + source-edit
mutation, all in scratch). The one construction-inspection point: the from-import-defeats-monkeypatch
reasoning in A-SUB-3 (I verified the import shape empirically; the monkeypatch-non-reach is Python import
semantics, stated as such).

---

## MISSING PINS (each: the test that should exist + the defect it catches)

**A-SUB**
1. *A pin that a migration-set file's shared-helper import is USED, not merely present* — catches the
   unused-import "consolidation" that ships `_SCANNED_MEMBERS` + 3 private clones green (A-SUB-1).
2. *The design §7 anti-duplication structural pin*: a DERIVED scan (not a 4-file tuple) that no test
   file hand-rolls whole-tree `rglob("*.py")`+`ast.parse`+`read_text` outside an evidence-backed
   non-adopter allowlist — fail-closed on empty. Catches an un-migrated or new whole-tree clone
   (A-SUB-2); makes "migration complete" a checked variable.
3. *A required, run-and-recorded mutation-sharing receipt* (e.g. `scripts/mutation_proof.py` declaring
   each adopter's coverage node-id as expected-RED under `parse_production_trees`→`{}`) — catches
   routing-not-sharing that survives the static half (A-SUB-3).
4. *A pin that `_SCANNED_MEMBERS` (and any per-file member hand-list) is absent from migrated files*
   (A-SUB-4).
5. *Broaden `_imports_a_shared_reach_helper` to accept `import _logging_fixtures` + attribute use*
   (A-SUB-5) — or drop the from-import mandate in favor of the used-ness pin in (1).

**B**
6. *Leg 2 containment must recognize element-wise/collection containment* so the correct
   `[render_attributed(b) for b in blocked_by]` is contained while `safe_str`/bare-repr is not —
   the discriminating pin Ruling 2 mandates; without it B is unsatisfiable except by a false clear
   (B-1).
7. *A pin that no `_SERVED_SAFE_FIELDS` key is a manifest DOOR field in any model* — mechanically
   enforces Ruling 2's "do not allowlist a door SAFE" so the B-1 escape hatch cannot be taken silently.
8. *Name `kind` in the field-name-keying bound (or give it a dedicated control like `task_id`'s)* (B-2).

---

## Reference A-SUB helpers (pasted — the instrument, per brief-base §1)

```python
def parse_production_trees(*, include_scripts=True, include_skills=False, include_tests=False):
    repo = _workspace_root()  # loremaster.__file__ -> parent.parent.parent
    trees = {}
    for _label, root in workspace_roots(include_scripts=include_scripts, include_skills=include_skills):
        for path in sorted(root.rglob("*.py")):
            trees[path.relative_to(repo).as_posix()] = ast.parse(path.read_text(encoding="utf-8"))
    return trees

def assert_scan_reached_every_member(scanned_trees, *, extra_roots=("scripts",)):
    manifest = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))
    declared = set(manifest["tool"]["uv"]["workspace"]["members"])
    expected = declared | set(extra_roots)
    scanned = {k.split("/", 1)[0] for k in scanned_trees}
    assert scanned, "empty scan — fail closed (#290 anti-vacuity)"
    assert scanned == expected, f"declared-not-scanned={sorted(expected-scanned)}; scanned-not-declared={sorted(scanned-expected)}"
```
Passes all 9 A-SUB helper-behavior pins (fail-closed, oracle-independent, missing-member-names-it,
undeclared-extra-raises, toggle-honored). This is what makes A-SUB satisfiable at all — the rot is the
migration/sharing reach, not the helper spec.

## Satisfiability receipts
- **A-SUB is satisfiable to 16/0** — but *also* satisfiable by a fix-nothing build (A-SUB-1), which is
  the defect.
- **B is NOT satisfiable to 0-failed** on the Ruling-2-correct build without the forbidden `blocked_by`
  allowlist entry (1 failed → 10 passed only after the forbidden entry). C-DEF defect.

## Verdict
- **A-SUB (F4): CONTRACT INSUFFICIENT** — missing pins 1-5.
- **B (#345): CONTRACT INSUFFICIENT** — missing pins 6-8; internally inconsistent with Ruling 2.
