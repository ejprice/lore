# REPORT-adversary-63a-v3 — CONTRACT ADVERSARY grade of the R3 fold (finding #448) + the R4 hunt

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT — R4 FOUND → DESIGN ESCALATION (per operator ruling; NOT a fold-pin).**
- **R3 itself is correctly built and discriminating** (task 1 ✓): the shipped mutation-proof is real, and
  a 2nd same-verb `UPDATE` seizure spliced into the **real** `_migrate_memory_scope` reds the R3 count
  leg (`assert 2 == 1`), the extractor returning a genuine **list of 2** (not verb-collapsed, not
  first-match). §R3-VERIFY.
- **P1 headline — the R4 hunt found TWO independent wrong builds that launder past R1+R2+R3+the core,
  each a reach-recession ONE LEVEL DOWN from R3's own instrument:**
  - **R4-a (shape-leg SUBSTRING):** a SINGLE `UPDATE {memory} SET scope = $scope WHERE scope IS NONE OR
    scope = $victim` seizes OWNED rows yet passes ALL 22 pins (**22 passed / 0 failed** on the reference
    build). The shape leg (`re.search(WHERE scope IS NONE)`) is a substring, not the property "WHERE ==
    exactly scope IS NONE". §R4-a.
  - **R4-c (verb-set HIDDEN CONSTANT):** a co-located memory seizure via `INSERT … ON DUPLICATE KEY
    UPDATE` / `CREATE` / `RELATE` is NOT counted by the R3 extractor (count stays 1 → R3 GREEN) **and is
    INVISIBLE to the runtime observer** (`_mutation_verb_for_table` → None → never recorded → deny-by-
    default can't fire). §R4-c.
- **THE ROOT (why a fold is the wrong move):** across R1 self-containment → R3 frame-count → R4-a shape →
  R4-c verb-set → the label channel (`if observed.label is not None: return True`, which trusts the whole
  labelled frame identically), the exemption blesses everything in the FRAME / matching a LOOSE shape
  substring / a bounded verb-set — never the EXACT adjudicated statement. Reach recedes one level each
  round (CLAUDE.md STOP-rule). **Recommend the DESIGN ESCALATION the operator named: exempt frame →
  STATEMENT scope (allowlist the ONE exact adjudicated statement; everything else in the frame is
  unclassified).** Two-prong nuance in §R4-ESCALATION. Finding **#449** filed.
- **Base-3 FALSE-GATE docstring CONFIRMED (task 3):** `test_migrate_memory_scope_updates_only_none_scope_rows`
  promises *"Reddens the day the migrate grows a write that touches a NON-NONE-scope row"* — its first-match
  substring assertion does NOT (R4-a proves it also fails on an OR-extended FIRST statement). §BASE3.
- state: **done**
- **Graded:** `a48c8a2` · HEAD-at-report: `a48c8a2` · **SAME**.
- `Packages considered:` none — the fold specifies no new production mechanism (R3 is a pure `ast`
  extractor reusing in-tree shape primitives). Reference build = stdlib `contextvars`/`contextlib`
  mirroring the shipped `write_guard`. Independent P-PKG diff vs author (`none`): **AGREED**. §PKG.
- `Reuse ledger:` none (adversary writes no production symbols; scratch discarded, harness pasted §METHOD).
- decisions-needed: **ONE (design fork, operator's call per brief) — adopt statement-scope now (closes
  R1+R3+R4-a+label-channel), OR ledger R4 as a pinned bound with a re-open trigger?** Plus the verb-set
  prong (R4-c) needs mutation-detection to be a PROPERTY, not a verb enumeration. §R4-ESCALATION.
- receipt POINTERS: satisfiability → §SAT; R3 discrimination → §R3-VERIFY; the two R4 witnesses + controls
  → §R4-a / §R4-c; the escalation + two prongs → §R4-ESCALATION; other candidates (b/d/e) → §R4-OTHER;
  base-3 false gate → §BASE3; quantifier → §P1b; reach → §P1c; residuals → §RESIDUALS; instruments →
  §METHOD (applier + demo pasted verbatim).

---

## §SAT — satisfiability receipt (C-DEF), reproduced INDEPENDENTLY

Provenance-asserted scratch `./scripts/scratch_copy.sh /tmp/cav63av3` — receipt printed:
`loremaster.__file__ = /tmp/cav63av3/loremaster/loremaster/__init__.py` (grading the scratch, not the
original — #140-safe; all four members resolve inside the copy).

Reference build (minimal, applied by me from pristine backups — the applier is `/tmp/cav63av3_apply.py`,
pasted verbatim §METHOD):
- `governed.py`: `_ACTIVE_EXEMPT: ContextVar[str|None]` + `active_exempt()` + `@contextmanager
  governed_exempt(name)` — a verbatim mirror of the shipped `write_guard`/`active_write_guard`.
- `principals.py::_migrate_memory_scope`: `with governed_exempt("migrate-governed"):` wrapping the
  backfill `run_query`; `governed_exempt` added to the existing inner `from loremaster.governed import …`.
- `_governed_contract.py`: a NAMED BOUND clause on `classify_tree_observed_write.__doc__` naming
  `guarded_write` / `honest` / `#138`.

Receipts:
- BASELINE (pristine scratch, before ref build): `test_memory_enforcement_63a_v.py` → **4 failed, 18
  passed** — matches HEAD `a48c8a2` exactly (the 4 RED are the unbuilt production mechanism + R2 docstring).
- REFERENCE BUILD: `test_memory_enforcement_63a_v.py` → **22 passed, 0 failed** (4.04s). **All 4 RED flip
  GREEN** (`…governed_exempt_mechanism_is_built`, `…migrate_memory_scope_enters_governed_exempt`,
  `…live_migration_write_is_attributed`, `…docstring_names_the_hand_set_label_bound`).
- No-regression: `test_memory_enforcement_63a_iv.py` + `_bounds_63a_iv.py` → **12 passed, 0 failed** (4.59s).
- Harder leg: `uv run ruff check governed.py principals.py _governed_contract.py` → **All checks passed!**
  (the added inner `governed_exempt` import is USED — no orphan). **C-DEF satisfied.**

## §R3-VERIFY — the R3 pin discriminates (task 1): CONFIRMED on the REAL production frame

The adversary-63a-v2 seizure — a **2nd same-verb** `UPDATE {memory} SET scope = $victim WHERE scope =
$victim` co-located inside `_migrate_memory_scope`'s `governed_exempt("migrate-governed")` block —
applied to the reference build (`ref+r3_update`). Full 63a-v suite → **1 failed, 21 passed**. The one
RED is exactly the R3 pin, on the COUNT leg:

```
E  AssertionError: exempt frame '_migrate_memory_scope' in loremaster/loremaster/principals.py holds
   2 raw memory mutations, not EXACTLY ONE:
   ['UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE',
    'UPDATE {MEMORY_TABLE} SET scope = $victim WHERE scope = $victim']
E  assert 2 == 1
loremaster/tests/test_memory_enforcement_63a_v.py:600
```

Confirmed properties (task 1 checklist):
- The extractor returns a **LIST of 2** — NOT verb-collapsed to `(file,function,verb)` (that would give
  a set of 1), NOT first-match (that would return the first shape only). Byte-proof in the assertion
  message above (two distinct shapes).
- A single-mutation control → GREEN (the reference build's own real frame; 22/0 in §SAT is the control).
- SAME exempt token on both synthetics in the shipped mutation-proof (`test_the_single_shape_pin_reds_
  an_exempt_frame_with_a_second_seizure_write`, token `"second-write-frame"`) → a count-blind /
  first-match / constant / token-special-cased extractor is CAUGHT; that pin is among the 21 passed.
- The mutation-proof is REAL (I ran it; it reds the seizure and greens the control). **R3 is SAFE.**

## §R4-a — REACH RECESSION #1: the shape leg is a SUBSTRING, not a property (BLOCKER survivor)

**Brief R4 candidate (a):** *"a write that MATCHES the WHERE scope IS NONE shape but still does harm."*
Answer: the NONE-scope shape is checked by a **substring** `re.search(r"WHERE\s+scope\s+IS\s+NONE")` —
in BOTH the R3 shape leg (`…exempt_frame_holds_exactly_its_one_none_scope_guarded_mutation`) and the
base-3 pin. A single `UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE OR scope = $victim`:
- is ONE statement → R3 count leg sees 1 (GREEN);
- CONTAINS `WHERE scope IS NONE` as a substring → R3 shape leg + base-3 pin pass (GREEN);
- is one UPDATE site → whole-tree L1 unchanged (GREEN);
- runs under the exempt token, origin == site → runtime classifier True (GREEN);
- **yet touches OWNED rows** (`OR scope = $victim`) — the exact seizure the exemption's justification
  ("a NONE-scope row has no owner to seize") forbids.

**Wrong build (`ref+r4a`):** full 63a-v suite → **22 passed, 0 failed** — laundered past every pin.
**Positive control (`ref+r4a_ctl`, WHERE with NO `scope IS NONE` substring):** → **2 failed** —
`test_migrate_memory_scope_updates_only_none_scope_rows` AND
`test_the_exempt_frame_holds_exactly_its_one_none_scope_guarded_mutation` both red. So the shape legs
CAN see a missing substring (the probe is not blind); the OR-extended survivor is a genuine miss.

Direct store-free confirmation (§METHOD demo):
```
blessed  WHERE scope IS NONE                         -> shape-leg passes=True  => GREEN
OR-extended (seizes owned rows)                      -> shape-leg passes=True  => GREEN   <-- LAUNDERS
no-substring control (seizure)                       -> shape-leg passes=False => REDS
```
The property "restricts to unowned rows" is a **hidden constant** — assumed by substring presence, not
verified as `WHERE == exactly scope IS NONE`. Honest-developer plausible: extending the backfill to also
re-home mis-scoped legacy rows.

## §R4-c — REACH RECESSION #2: the verb-set is a HIDDEN CONSTANT (BLOCKER survivor)

**Brief R4 candidate (c) + (e):** *"a raw memory mutation via a VERB the scanner's verb-set misses"* /
*"an observer-reach gap."* `_raw_mutation_of_table` (reused by BOTH `exempt_frame_raw_memory_mutations`
and the whole-tree scan) matches only `UPSERT|UPDATE|DELETE` + `REMOVE TABLE|FIELD|INDEX`. The runtime
observer's `_mutation_verb_for_table` matches the same plus table-form `UPDATE/DELETE`. **Both miss
`INSERT`, `CREATE`, `RELATE`.** SurrealDB supports `INSERT … ON DUPLICATE KEY UPDATE` (executable spec
`surrealql-tests: tests/language/statements/insert/5776_insert_and_update_on_duplicate_key.surql`) — a
genuine existing-row seizure.

Store-free demonstration with positive controls (§METHOD demo output, verbatim):
```
=== exempt_frame_raw_memory_mutations (blessed UPDATE + a co-located 2nd write) ===
  UPDATE seizure (in-set)      -> count=2  =>  R3 REDS (count!=1)
  DELETE      (in-set)         -> count=2  =>  R3 REDS (count!=1)
  INSERT seizure (MISSED)      -> count=1  =>  R3 GREEN — LAUNDERS
  CREATE mint  (MISSED)        -> count=1  =>  R3 GREEN — LAUNDERS
  RELATE       (MISSED)        -> count=1  =>  R3 GREEN — LAUNDERS
=== runtime observer _mutation_verb_for_table (does it even SEE the write?) ===
  UPDATE type::record   -> verb='UPDATE' => OBSERVED
  DELETE type::record   -> verb='DELETE' => OBSERVED
  INSERT INTO memory    -> verb=None     => INVISIBLE (never recorded)
  CREATE type::record   -> verb=None     => INVISIBLE (never recorded)
  RELATE ->owns->memory -> verb=None     => INVISIBLE (never recorded)
```
Positive control PROVES the miss is genuine: DELETE (in-set, DIFFERENT verb) reds L1+R3 (confirmed live —
`ref+r4c_delete` → 3 failed: the two whole-tree set pins + the R3 count leg); INSERT (out-of-set) does
not. **Worse than R4-a:** the runtime observer never RECORDS an INSERT/CREATE/RELATE memory write, so
deny-by-default (which fires only on OBSERVED-but-unclassified writes) cannot catch it either. F5 is
blind to these verbs end-to-end.

⚠ Honesty note: my initial *live* `ref+r4c_insert` run failed one test
(`test_the_live_migration_write_is_attributed`) — that was a RUNTIME crash from an unbound `$id` in my
INSERT statement, NOT the gate catching it. The CLEAN, uncontaminated finding is the store-free static
demonstration above (extractor count + observer verb), which needs no store execution.

## §R4-ESCALATION — the recommendation (per operator ruling): STATEMENT scope, and the two prongs

Per the operator ruling relayed in my brief: an R4 triggers a **DESIGN ESCALATION of the exempt mechanism
(exempt frame → statement scope)**, NOT another fold. This grade endorses that, and sharpens it:

- **The recurring root, stated once:** the classifier/adjudication trusts a FRAME (exempt or labelled),
  or a LOOSE shape (substring), or a bounded VERB-SET — never the EXACT adjudicated statement. Every
  round so far relocated the hidden constant one level down: R1 made *self-containment* checked; R3 made
  the frame's *count* checked; R4-a shows the *shape predicate* is still a substring; R4-c shows the
  *verb-set* the count is over is still a hand-enumeration; the LABEL channel (§R4-OTHER d) trusts the
  whole labelled frame by the identical `label is not None → True`. This is the CLAUDE.md instrument
  lesson verbatim — *"when you catch yourself enumerating what is FORBIDDEN [verbs/shapes], you have
  already lost; allowlist the SAFE."* The STOP-rule ("is the reach receding one level deeper every
  round?") answers YES — so do NOT run another fold round.
- **The escalation (frame → statement scope):** the exemption/attribution blesses ONLY the ONE exact
  adjudicated statement (its resolved content), and ANY other write running in the frame — regardless of
  verb, shape, or channel — is UNCLASSIFIED (the red signal). This closes R1 (self-containment becomes
  moot — only the exact statement is blessed), R3 (a second statement of any kind is unclassified),
  **R4-a** (an OR-extended statement ≠ the adjudicated one → unclassified), and the LABEL-channel sibling
  (bless the exact statement, not the labelled frame) — **all at once, by allowlisting the one safe
  statement instead of enumerating forbidden ones.**
- **⚠ TWO PRONGS — statement-scope alone does NOT close R4-c.** The verb-set miss is upstream of the
  classifier: an `INSERT`/`CREATE`/`RELATE` memory write is INVISIBLE to both the static extractor and
  the runtime observer (`_mutation_verb_for_table` → None), so it is never even presented to the
  classifier to be blessed-or-denied. Closing R4-c needs the mutation-DETECTION (`_raw_mutation_of_table`
  / `_mutation_verb_for_table`) to become a PROPERTY ("does this statement mutate `memory`?") rather than
  a verb enumeration — the same allowlist-the-safe move, one layer up. This prong is shared with the core
  (L1 + observer), so it is a wider escalation than the exempt mechanism alone; flagged prominently
  because it defeats the R3 pin regardless of statement-scope.
- **Operator fork (decisions-needed):** adopt statement-scope now (+ the verb-set property fix), or ledger
  R4 as a pinned bound (#449) with a named re-open trigger? Right-sizing rigor to importance is the
  operator's call (CLAUDE.md); this is a governed-write security boundary, so my recommendation is to
  ADOPT statement-scope (it is the structural close of the whole class), but the depth-vs-value trade is
  the operator's.

## §R4-OTHER — the remaining R4-hunt candidates, each an individual verdict

- **(b) a same-shape governed write in a DIFFERENT self-contained exempt frame (a future 2nd exempt
  entry):** NO SURVIVOR today — only one exempt entry exists (`migrate-governed`). A future 2nd exempt
  entry is governed by R1 (self-containment ∀) + R3 (single-shape ∀ over ITS frame); if its blessed shape
  ≠ `WHERE scope IS NONE`, R3's hardcoded shape leg reds FAIL-CLOSED (contract-63a-v3 §FLAGS bound 2,
  re-open trigger named). Statement-scope would also cover this generically. **Investigated — closed
  (fail-closed) today.**
- **(d) a memory write in an allowlisted-but-NON-exempt (labelled) frame — sibling hole:** the classifier
  blesses the whole labelled frame via `if observed.label is not None: return True`, identical to the
  exempt channel R3 hardened, and R3's ∀ EXCLUDES label frames (`e.exempt_name is not None`). I tested a
  co-located `SET scope` seizure inside `_reinforce`'s `write_guard("_reinforce")` block: it was CAUGHT —
  by the per-frame base pin `test_the_reinforce_update_sets_only_the_importance_column`, which asserts
  every emitted `SET` column ∈ {importance}. So `_reinforce` is backstopped by a bespoke per-frame column
  pin, NOT a general single-mutation ∀. **Not a clean delta survivor**, but it CORROBORATES the root:
  the label channel structurally trusts the whole frame, saved here only by an accident of per-frame
  coverage. Re-open trigger: any NEW label frame with a raw governed write and no bespoke column/count
  pin. Statement-scope closes this generically.
- **(e) observer-reach / origin-match gap:** the observer verb-set gap IS R4-c (INSERT/CREATE/RELATE
  invisible). The origin-match itself: R1 pins self-containment (origin==site sound); no new gap there.
  **Covered under R4-c.**

## §BASE3 — the base-3 FALSE-GATE docstring (task 3): CONFIRMED, and doubly so

`test_migrate_memory_scope_updates_only_none_scope_rows` (`test_memory_enforcement_63a_v.py:289`) docstring:
*"Reddens the day the migrate grows a write that touches a NON-NONE-scope row."* Its assertion calls
`_migrate_backfill_update_statement` (FIRST-match) then `re.search(WHERE scope IS NONE)`. This is a
CLAUDE.md FALSE GATE on TWO axes:
1. **first-match** (adversary-63a-v2 §R3 failure 2): a blessed WHERE-none write shadows a co-located
   seizure. R3's count leg now delivers THIS half of the promise.
2. **substring** (NEW, §R4-a): even the FIRST statement, OR-extended, passes the substring while touching
   owned rows — R3 does NOT deliver this half (its shape leg has the SAME substring weakness).

The build should either fix the base-3 docstring to state what it actually checks (and point at the true
∀-guard) or — better, under the escalation — replace the substring predicate with an exact-shape match.
Confirms contract-63a-v3 §FLAGS fork 1 and extends it (it is not only first-match).

## §P1b — QUANTIFIER TABLE (delta pins; core table unchanged from adversary-63a-v)

| invariant | classification | receipt |
|---|---|---|
| R3: exempt frame holds EXACTLY ONE raw memory mutation (count) | **∀** over exempt entries (anti-vacuity ≥1) | §R3-VERIFY — reds a 2nd same-verb UPDATE on the real frame |
| R3: that one mutation is `WHERE scope IS NONE`-restricted (shape) | **GUARDED-BY-SUBSTRING — should be ∀ "WHERE == exactly scope IS NONE"** | **§R4-a BLOCKER** — `WHERE scope IS NONE OR scope=$victim` passes |
| R3 count ∀ is over `_raw_mutation_of_table`'s VERB-SET | **GUARDED-BY-VERB-ENUMERATION — should be ∀ over all memory mutations** | **§R4-c BLOCKER** — INSERT/CREATE/RELATE not counted; observer blind |
| R2: hand-set-label bound NAMED in the classifier docstring | point-check on `__doc__` | 4→GREEN in §SAT (control); RED-at-HEAD baseline |
| classifier blesses any LABELLED-frame write (`label is not None → True`) | **GUARDED-BY-PER-FRAME-PIN — not a general ∀** | §R4-OTHER (d) — `_reinforce` backstopped by its column pin only |

Two R3 rows are the P1b failure mode exactly: an invariant conditioned on the shape substring / verb-set
the extractor happened to reuse, not ∀ over all memory mutations. The same bad outcome (a seizure)
reached through an OR-extended WHERE or an unenumerated verb engages no pin.

## §P1c — REACH TABLE (delta: R3's own instrument, both recessions)

Legs: EMPIRICAL for the in-tree extractor/observer (wrong builds run on the reference build; store-free
demos with positive controls). Construction-inspection for the runtime classifier's frame-trust.

| instrument | reach DERIVED vs hidden-constant | coverage a CHECKED var? | effect vs proxy | one-source / mutation | verdict |
|---|---|---|---|---|---|
| R3 `exempt_frame_raw_memory_mutations` — COUNT leg | ∀ over the frame's statements (a real LIST) | **YES** — reds a 2nd same-verb UPDATE (real-frame splice) | effect (AST of real `entry.site.file`) | reuses `_statement_shape`/`_raw_mutation_of_table` | **SAFE (empirical, §R3-VERIFY)** |
| R3 — SHAPE leg (`WHERE scope IS NONE` substring) | **HIDDEN CONSTANT** — substring presence, not "WHERE == exactly scope IS NONE" | **NO** — `… OR scope=$victim` passes | proxy (substring, not the WHERE semantics) | shared with base-3 (same substring) | **MISSING → §R4-a BLOCKER** |
| R3 COUNT reach = the mutation VERB-SET (`_raw_mutation_of_table`) | **HIDDEN CONSTANT** — UPSERT/UPDATE/DELETE/REMOVE; misses INSERT/CREATE/RELATE | **NO** — INSERT/CREATE/RELATE not counted | effect, but blind to unenumerated verbs | shared with L1 scan + observer (`_mutation_verb_for_table`) | **MISSING → §R4-c BLOCKER** |
| runtime observer `_mutation_verb_for_table` | **HIDDEN CONSTANT** verb-set | **NO** — INSERT/CREATE/RELATE → None → never recorded | effect only for enumerated verbs | one impl, but a verb hand-list | **MISSING → §R4-c (observer-blind prong)** |

## §PKG — package survey diff (P-PKG)
Independent table built before reading the author's:
- Reference build `governed_exempt`/`active_exempt` → `contextvars.ContextVar` + `contextlib.contextmanager`
  (stdlib); the shipped `write_guard` IS this exact pattern — a third-party ctx lib is strictly worse and
  breaks the ONE-IMPLEMENTATION mirror. **stdlib (no gap).**
- R3 extractor → stdlib `ast` via the in-tree shape primitives (reuse, not a package). No third-party lib
  does a repo-specific SurrealQL statement-shape scan; a general Python-AST helper (`libcst`) is worse and
  breaks the mirror. **keep (stdlib + in-tree reuse).**
DIFF vs author (`none — no new production mechanism`): **AGREED.**

## §RESIDUALS — every item, an individual verdict
- **R4-a exempt-frame shape-leg substring** — **BLOCKER survivor.** §R4-a. → statement-scope / exact-shape.
- **R4-c verb-set hidden constant (static extractor + runtime observer)** — **BLOCKER survivor.** §R4-c.
  → mutation-detection as a property (allowlist-the-safe), a wider escalation than statement-scope alone.
- **R3 count leg** — genuinely discriminating on the real frame (list of 2, not collapsed/first-match).
  **SAFE.** §R3-VERIFY.
- **Base-3 false-gate docstring** — CONFIRMED (first-match AND substring). Build should fix the docstring
  or (better) the predicate. §BASE3. Consistent with contract-63a-v3 §FLAGS fork 1.
- **Candidate (b) future 2nd exempt entry** — fail-CLOSED today (R3 shape leg hardcodes WHERE-none;
  documented bound + re-open trigger). **Investigated — closed today.** §R4-OTHER.
- **Candidate (d) label-channel whole-frame trust** — structurally present (`label is not None → True`);
  `_reinforce` backstopped by its per-frame column pin only, NOT a general ∀. **Corroborates the root;
  re-open trigger named.** §R4-OTHER.
- **R2 docstring pin, R1 self-containment** — graded SUFFICIENT by adversary-63a-v2; NOT re-litigated
  (satisfiability confirms R2 flips GREEN on the reference docstring). **Out of this grade's frame** (R2/R1
  are done); R4-a merely reuses R1's proven self-containment premise.
- **Core both-ways / whole-tree reach / #447 precision / observer default-target** — graded SUFFICIENT by
  adversary-63a-v; NOT re-litigated except where R4-c intersects the shared verb-set (flagged as the
  second escalation prong).

## §METHOD — instruments (deliverables; scratch is disposable by design)

Scratch: `./scripts/scratch_copy.sh /tmp/cav63av3` — provenance-asserted, `loremaster.__file__` printed
§SAT. All wrong builds layered from PRISTINE backups (`*.pristine`) via the applier below — never
compounded; every variant restored (module back to the 4F/18P baseline, re-verified). No repo file
mutated. Live runs against TEST store `ws://127.0.0.1:18000` (NEVER :18500) via `migration_world`.

**The applier (`/tmp/cav63av3_apply.py`) — pasted verbatim so every wrong build is re-runnable:**
```python
#!/usr/bin/env python3
"""Reference-build + wrong-build applier for adversary-63a-v3. Layers edits onto pristine backups."""
import sys
from pathlib import Path

ROOT = Path("/tmp/cav63av3/loremaster")
GOV = ROOT / "loremaster" / "governed.py"
PRIN = ROOT / "loremaster" / "principals.py"
GC = ROOT / "tests" / "_governed_contract.py"
FILES = [GOV, PRIN, GC]

GOV_ANCHOR = (
    "    token = _ACTIVE_WRITE_GUARD.set(label)\n    try:\n        yield\n    finally:\n"
    "        _ACTIVE_WRITE_GUARD.reset(token)\n"
)
GOV_ADD = GOV_ANCHOR + (
    "\n\n_ACTIVE_EXEMPT: contextvars.ContextVar[str | None] = contextvars.ContextVar(\n"
    '    "loremaster_active_exempt", default=None\n)\n\n\n'
    "def active_exempt() -> str | None:\n"
    '    """The active governed_exempt name, or None (mirror of active_write_guard)."""\n'
    "    return _ACTIVE_EXEMPT.get()\n\n\n@contextlib.contextmanager\n"
    "def governed_exempt(name: str) -> Iterator[None]:\n"
    '    """Attribute a non-write_guard admin mutation to a NAMED exempt token (mirror of write_guard)."""\n'
    "    token = _ACTIVE_EXEMPT.set(name)\n    try:\n        yield\n    finally:\n        _ACTIVE_EXEMPT.reset(token)\n"
)
PRIN_IMPORT_ANCHOR = "    from loremaster.governed import PROJECT_KEEP_KEY, MigrateGovernedResult\n"
PRIN_IMPORT_NEW = "    from loremaster.governed import PROJECT_KEEP_KEY, MigrateGovernedResult, governed_exempt\n"
PRIN_WRITE_ANCHOR = (
    "    await run_query(\n        acquire=store.acquire,\n        drop=store.drop,\n        url=store.url,\n"
    '        noun="governed memory-scope backfill",\n        label="governed.memory_backfill.rejected",\n'
    '        statement=f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE",\n'
    '        params={"scope": project_scope},\n        logger=logger,\n    )\n'
)

def _prin_wrapped(extra_lines: str = "") -> str:
    body = (
        '        await run_query(\n            acquire=store.acquire,\n            drop=store.drop,\n'
        "            url=store.url,\n"
        '            noun="governed memory-scope backfill",\n            label="governed.memory_backfill.rejected",\n'
        '            statement=f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE",\n'
        '            params={"scope": project_scope},\n            logger=logger,\n        )\n'
    )
    return '    with governed_exempt("migrate-governed"):\n' + body + extra_lines

GC_DOC_ANCHOR = "``exempt`` is None → the migrate write is unclassified → RED-until-built."
GC_DOC_NEW = (
    "``exempt`` is None → the migrate write is unclassified → RED-until-built.\n\n"
    "    NAMED BOUND (#138 — WHEN YOU CANNOT CLOSE A HOLE, PIN IT): a production site that hand-sets a\n"
    "    write_guard LABEL without calling guarded_write passes BOTH F5 layers and is CLASSIFIED — an\n"
    "    ACCEPTED bound under this gate's threat model (the HONEST developer, not the hostile author)."
)

def read(p): return p.read_text(encoding="utf-8")
def write(p, s): p.write_text(s, encoding="utf-8")
def assert_in(hay, needle, label):
    if needle not in hay: raise SystemExit(f"ANCHOR MISS in {label}: {needle[:60]!r}...")
def backup():
    for f in FILES: write(f.with_suffix(f.suffix + ".pristine"), read(f))
    print("backed up pristine:", [f.name for f in FILES])
def restore():
    for f in FILES: write(f, read(f.with_suffix(f.suffix + ".pristine")))
    print("restored to pristine:", [f.name for f in FILES])
def apply_ref():
    gov = read(GOV.with_suffix(".py.pristine")); prin = read(PRIN.with_suffix(".py.pristine")); gc = read(GC.with_suffix(".py.pristine"))
    assert_in(gov, GOV_ANCHOR, "governed"); gov = gov.replace(GOV_ANCHOR, GOV_ADD, 1)
    assert_in(prin, PRIN_IMPORT_ANCHOR, "import"); prin = prin.replace(PRIN_IMPORT_ANCHOR, PRIN_IMPORT_NEW, 1)
    assert_in(prin, PRIN_WRITE_ANCHOR, "write"); prin = prin.replace(PRIN_WRITE_ANCHOR, _prin_wrapped(), 1)
    assert_in(gc, GC_DOC_ANCHOR, "doc"); gc = gc.replace(GC_DOC_ANCHOR, GC_DOC_NEW, 1)
    return gov, prin, gc
VARIANTS = {}
def variant(name):
    def deco(fn): VARIANTS[name] = fn; return fn
    return deco
@variant("ref")
def _ref():
    gov, prin, gc = apply_ref(); write(GOV, gov); write(PRIN, prin); write(GC, gc); print("APPLIED ref")
@variant("ref+r4a")
def _r4a():  # OR-extended WHERE (single UPDATE, touches owned rows)
    gov, prin, gc = apply_ref()
    a = 'statement=f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE",'
    b = 'statement=f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE OR scope = $victim",'
    assert_in(prin, a, "r4a"); prin = prin.replace(a, b, 1); write(GOV, gov); write(PRIN, prin); write(GC, gc); print("APPLIED ref+r4a")
@variant("ref+r4a_ctl")
def _r4a_ctl():  # WHERE with NO 'scope IS NONE' substring — shape-leg control
    gov, prin, gc = apply_ref()
    a = 'statement=f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE",'
    b = 'statement=f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope = $victim",'
    assert_in(prin, a, "r4a_ctl"); prin = prin.replace(a, b, 1); write(GOV, gov); write(PRIN, prin); write(GC, gc); print("APPLIED ref+r4a_ctl")
def _second_write(stmt_line):
    return ('        await run_query(\n            acquire=store.acquire, drop=store.drop, url=store.url,\n'
            '            noun="second co-located write", label="governed.memory_backfill.rejected",\n'
            f"            {stmt_line}\n"
            '            params={"scope": project_scope, "victim": project_scope}, logger=logger,\n        )\n')
@variant("ref+r4c_insert")
def _r4c_insert():  # 2nd co-located INSERT memory seizure — verb OUTSIDE set
    gov, prin, gc = apply_ref()
    extra = _second_write('statement=f"INSERT INTO {MEMORY_TABLE} (id, scope) VALUES ($id, $victim) ON DUPLICATE KEY UPDATE scope = $victim",')
    assert_in(prin, _prin_wrapped(), "r4c_insert"); prin = prin.replace(_prin_wrapped(), _prin_wrapped(extra), 1)
    write(GOV, gov); write(PRIN, prin); write(GC, gc); print("APPLIED ref+r4c_insert")
@variant("ref+r4c_delete")
def _r4c_delete():  # 2nd co-located DELETE — positive control (different verb, reds L1)
    gov, prin, gc = apply_ref()
    extra = _second_write('statement=f"DELETE {MEMORY_TABLE} WHERE scope = $victim",')
    assert_in(prin, _prin_wrapped(), "r4c_delete"); prin = prin.replace(_prin_wrapped(), _prin_wrapped(extra), 1)
    write(GOV, gov); write(PRIN, prin); write(GC, gc); print("APPLIED ref+r4c_delete")
@variant("ref+r3_update")
def _r3_update():  # 2nd co-located SAME-VERB UPDATE seizure — R3 count leg must red
    gov, prin, gc = apply_ref()
    extra = _second_write('statement=f"UPDATE {MEMORY_TABLE} SET scope = $victim WHERE scope = $victim",')
    assert_in(prin, _prin_wrapped(), "r3_update"); prin = prin.replace(_prin_wrapped(), _prin_wrapped(extra), 1)
    write(GOV, gov); write(PRIN, prin); write(GC, gc); print("APPLIED ref+r3_update")
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"backup": backup, "restore": restore}.get(cmd, VARIANTS.get(cmd, lambda: (_ for _ in ()).throw(SystemExit(f"unknown {cmd!r}"))))()
```

**The store-free demo (verbatim) — the R4-a substring + R4-c verb-set proofs, no store needed:**
```python
# run from /tmp/cav63av3/loremaster/tests via: uv run python3 <this>
import re, sys; sys.path.insert(0, ".")
from _governed_contract import (exempt_frame_raw_memory_mutations, _mutation_verb_for_table,
    TreeWriteAllowlistEntry, TreeMutationSite)
def entry():
    return TreeWriteAllowlistEntry(site=TreeMutationSite("synthetic/pkg/x.py", "_do_write", "UPDATE"),
        justification="synthetic", pin="p", frames=("_do_write",), exempt_name="tok")
BLESSED = '    await run_query(f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE")\n'
def frame(second):
    return ('MEMORY_TABLE = "memory"\n\n\nasync def _do_write(x):\n' + BLESSED +
            (f'    await run_query(f"{second}")\n' if second else ""))
for label, second in [("UPDATE seizure (in-set)","UPDATE {MEMORY_TABLE} SET scope = $victim WHERE scope = $victim"),
    ("DELETE (in-set)","DELETE {MEMORY_TABLE} WHERE scope = $victim"),
    ("INSERT (MISSED)","INSERT INTO {MEMORY_TABLE} (id, scope) VALUES ($id, $v) ON DUPLICATE KEY UPDATE scope = $v"),
    ("CREATE (MISSED)","CREATE type::record('{MEMORY_TABLE}', $id) CONTENT {{scope: $v}}"),
    ("RELATE (MISSED)","RELATE $a->owns->type::record('{MEMORY_TABLE}', $id)")]:
    n = len(exempt_frame_raw_memory_mutations(entry(), source=frame(second)))
    print(f"  {label:24s} -> count={n} => {'R3 REDS' if n!=1 else 'R3 GREEN — LAUNDERS'}")
for label, stmt in [("UPDATE","UPDATE type::record('memory', $id) SET scope = $v"),
    ("DELETE","DELETE type::record('memory', $id)"),("INSERT","INSERT INTO memory (id) VALUES ($id) ON DUPLICATE KEY UPDATE scope = $v"),
    ("CREATE","CREATE type::record('memory', $id) CONTENT {scope: $v}"),("RELATE","RELATE $a->owns->type::record('memory', $id)")]:
    v = _mutation_verb_for_table(stmt, "memory")
    print(f"  {label:8s} -> observer verb={v!r} => {'OBSERVED' if v else 'INVISIBLE'}")
for label, stmt in [("blessed","UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE"),
    ("OR-extended","UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE OR scope = $victim"),
    ("no-substring ctl","UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope = $victim")]:
    print(f"  {label:16s} -> shape passes={bool(re.search(r'WHERE\\s+scope\\s+IS\\s+NONE', stmt, re.I))}")
```

## VERDICT: **CONTRACT INSUFFICIENT — R4 FOUND → DESIGN ESCALATION (not a fold-pin)**
R3 is correctly built and discriminating on the real frame (§R3-VERIFY), and the C-DEF satisfiability
receipt passes (22/0, ruff clean, provenance asserted). INSUFFICIENT rests on the R4 HUNT finding **TWO
confirmed wrong-build survivors** — the shape-leg substring (§R4-a) and the verb-set hidden constant
(§R4-c, static AND runtime-observer blind) — each a reach-recession ONE LEVEL DOWN from R3's own
instrument, plus a corroborating label-channel sibling (§R4-OTHER d). Per the operator's ruling this is a
**DESIGN ESCALATION** of the exempt mechanism (exempt frame → STATEMENT scope, allowlisting the one
adjudicated statement), NOT another fold — and the escalation must reach the verb-set DETECTION too
(a property, not an enumeration), which is the second prong statement-scope alone does not close. Finding
**#449** filed. The operator owns the depth-vs-value fork.
