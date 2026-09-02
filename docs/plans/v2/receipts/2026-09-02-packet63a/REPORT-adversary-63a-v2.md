# REPORT-adversary-63a-v2 — CONTRACT ADVERSARY grade of the R1/R2 fold (63a-v revision)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT** — **1 concrete missing pin (R3), a BLOCKER-class survivor:** a
  production change an *honest* developer could make — a **second raw `UPDATE {memory} SET scope …
  WHERE scope = <owned>` (a SEIZURE) co-located inside `_migrate_memory_scope`'s
  `governed_exempt("migrate-governed")` block** — passes **ALL 20** pins on the reference build
  (repro + positive control in §R3). This is EXACTLY the laundering scenario the brief's R3 hunt
  named. **R1 and R2 themselves are correctly built and discriminating** (they pass their own jobs);
  R3 is the SIBLING assumption the both-ways blessing left open.
- **P1 headline — a wrong build DID survive (R3).** The R1 discrimination battery (5 mutations +
  control) is fully caught; the R3 seizure-laundering build is NOT.
- **The fold introduces NO regression.** It added one pure predicate + two test classes (+ a docstring
  clause on the reference build); it touched no scanner/observer/classifier LOGIC. R3 is a
  pre-existing sibling gap the fold's soundness argument (self-contained ⇒ origin-match sound) does
  not cover — surfaced because R1 pins self-containment, which is *also* what lets a co-located foreign
  write launder.
- **R1 (self-containment invariant + discrimination):** genuinely discriminating, NOT vacuous. 5
  wrong builds of `exempt_entry_is_self_contained` run; the key permissive build ("seam anywhere in
  source") reds on the exact discrimination assertion (P0 control confirmed). SAFE. §R1.
- **R2 (docstring bound, 3-token matcher):** satisfiable, non-trapping, phrasing-robust (faithful + 2
  paraphrases GREEN). Two accepted-bound residuals: a pure name-drop greens it, and a *coincidental
  `138x`* can false-green a FUTURE deletion. Fit for purpose (force documentation / catch wholesale
  deletion); tightening would trap the builder. SAFE (residuals §R2).
- state: **done**
- **Graded:** `8da0004` · HEAD-at-report: `8da0004` · **SAME**.
- Packages considered: none — the fold specifies no new production mechanism (R1 is a pure `ast`
  predicate reusing in-tree `function_calls_named`; R2 is a `__doc__` substring assertion). Reference
  build = stdlib `contextvars`/`contextlib` mirroring the shipped `write_guard`. Independent P-PKG diff
  vs author (`none`): **AGREED**. §PKG.
- Reuse ledger: none (adversary writes no production symbols; scratch discarded).
- decisions-needed: **ONE (scope) — fold R3 now, or ledger it?** R3 lives in the migrate-governed
  triple (63a-v core). The brief said don't re-litigate the core wholesale, but explicitly tasked the
  R3 hunt with this scenario. Recommendation: **fold R3** — it is one ∀ pin, cheap, and "no contract
  revision skips the adversary" + "don't kick the can" both point to closing it before the builder.
  Operator owns the call. §R3.
- receipt POINTERS: verdict driver → §R3 (+ finding #448 filed); R1 battery → §R1; R2 gameability →
  §R2; satisfiability → §SAT; quantifier → §P1b; reach → §P1c; residuals → §RESIDUALS; instruments → §METHOD.

---

## §SAT — satisfiability receipt (C-DEF), reproduced INDEPENDENTLY

Provenance-asserted scratch `./scripts/scratch_copy.sh /tmp/cav63av2_adv` (all four members resolve
INSIDE the copy). Reference build (minimal, applied by me — not relayed):
- `governed.py`: `_ACTIVE_EXEMPT: ContextVar[str|None]` + `active_exempt()` + `@contextmanager
  governed_exempt(name)` — a verbatim mirror of the shipped `write_guard`/`active_write_guard`.
- `principals.py::_migrate_memory_scope`: `with governed_exempt("migrate-governed"):` wrapping the
  backfill `run_query`; `governed_exempt` added to the existing inner `from loremaster.governed import …`.
- `_governed_contract.py`: a NAMED BOUND clause on `classify_tree_observed_write.__doc__` naming
  `guarded_write` / `honest` / `#138`.

Receipt: `loremaster.__file__ = /tmp/cav63av2_adv/loremaster/loremaster/__init__.py` (grading the
scratch, not the original — #140-safe).
- `test_memory_enforcement_63a_v.py` → **20 passed, 0 failed** (4.19s). All **4 RED flip GREEN**
  (`…governed_exempt_mechanism_is_built`, `…migrate_memory_scope_enters_governed_exempt`,
  `…live_migration_write_is_attributed`, `…docstring_names_the_hand_set_label_bound`).
- Nothing else moves: `test_memory_enforcement_63a_iv.py` + `_bounds_63a_iv.py` → **12 passed, 0 failed**.
- Harder leg: `uv run ruff check governed.py principals.py _governed_contract.py` → **All checks
  passed!** (the added inner `governed_exempt` import is USED — no orphan). **C-DEF satisfied.**

## §P7 — RED honesty (reproduced at HEAD `8da0004`)

`test_memory_enforcement_63a_v.py` at HEAD → **4 failed, 16 passed** (matches contract §COUNT exactly).
R1's two legs (`TestEveryExemptAllowlistEntryIsSelfContained`, 2 tests) are among the 16 GREEN. R2's
RED is **for the right reason** — the assertion reports all three concept tokens
(`guarded_write`/`honest`/`138`) missing from the docstring (docstring genuinely unwritten). The other
3 RED isolate the UNBUILT production mechanism (`governed_exempt`/`active_exempt`). No import/path/fixture
error.

## §R3 — THE MISSING PIN (verdict driver): the exempt frame's raw-mutation SET is a HIDDEN CONSTANT

**The brief's R3 hunt, verbatim:** *"a BORROWED-token case under a SELF-CONTAINED twin (a foreign write
in a self-contained function laundering the migrate-governed token) — does the (file,symbol) origin
match still catch it?"* **Answer: NO.**

**The wrong build (a production change, within the honest-developer threat model).** On the reference
build, add a SECOND raw memory UPDATE inside `_migrate_memory_scope`'s exempt block — a seizure of an
OWNED (non-NONE-scope) row:
```python
    with governed_exempt("migrate-governed"):
        await run_query(..., statement=f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope IS NONE", ...)  # blessed
        await run_query(..., statement=f"UPDATE {MEMORY_TABLE} SET scope = $scope WHERE scope = $victim", ...)  # SEIZURE
```
Run the whole module → **20 passed, 0 failed.** NOTHING reds. (An honest developer extending the
backfill to also re-home some other scope condition writes exactly this — a second UPDATE they believe
F5 covers.)

**Why every layer misses it — three independent failures:**
1. **L1 collapses.** `TreeMutationSite` is keyed by `(file, function, verb)`. Two UPDATEs in one
   function → ONE site. `test_the_whole_tree_derived_set_is_the_known_four_sites` /
   `…every_whole_tree_site_is_in_the_allowlist` stay GREEN (still the known 4). *Only a DIFFERENT verb
   would grow the set* — see the positive control below.
2. **The WHERE-none pin is FIRST-MATCH, and its docstring promises a check it does not perform.**
   `test_migrate_memory_scope_updates_only_none_scope_rows` calls `_migrate_backfill_update_statement`,
   which `return`s the **FIRST** `UPDATE … SET scope` shape (`test_memory_enforcement_63a_v.py:627-640`).
   The blessed WHERE-NONE write shadows the seizure; the pin passes. Its docstring says *"Reddens the
   day the migrate grows a write that touches a NON-NONE-scope row"* — the assertion does not do that.
   **A FALSE GATE** (CLAUDE.md) + a **QUANTIFIER-LAW** violation (invariant stated over the first match,
   not ∀ over the frame's raw memory mutations).
3. **The both-ways classifier LAUNDERS it — and self-containment is *why*.** The seizure runs under the
   exempt contextvar (`exempt="migrate-governed"`) and its runtime origin is `_migrate_memory_scope`
   (it is co-located), so `(entry.site.file, entry.site.function) == observed.origin_site` is trivially
   satisfied → classified True. The origin match's discriminating power is *catching a DIFFERENT origin*
   (the `test_a_borrowed_exempt_token_is_unclassified` control). A launderer co-located in the
   self-contained frame has `origin == site` **by construction**, so the match cannot see it.

**The recursion this exposes.** R1 makes *self-containment* a checked variable (the origin match is
SOUND for legit writes: literal site == seam-call site). But it leaves the SIBLING assumption unpinned:
that the self-contained exempt frame contains **ONLY its one blessed mutation**. The frame's
raw-mutation SET is still a **hidden constant** (assumed = 1, unchecked) — the reach-as-hidden-constant
class ONE LEVEL DOWN, inside the exempt frame R1 was hardening. The design's own justification for the
exemption is about ONE statement (*"the statement can only touch UNMIGRATED rows … a NONE-scope row has
no owner to seize"*); a second statement voids that justification and nothing reds.

**P0 POSITIVE CONTROL (the probe can SEE a caught case).** Swap the second write's verb UPDATE→DELETE.
`TestTheWholeTreeReachIsAnOutput` → **2 failed** with
`UNCLASSIFIED raw memory mutation(s): [TreeMutationSite('…/principals.py','_migrate_memory_scope','DELETE')]`.
So a NEW verb reds (L1 orphan); the 20-passed on the same-verb UPDATE is a genuine miss, not a blind
probe. The laundering surface is precisely **additional UPDATE-of-memory statements co-located in the
exempt frame**.

**THE MISSING PIN (buildable now, test-infra only — the extractor + pin both live in
`test_memory_enforcement_63a_v.py`):**
- *Test that should exist:* `test_the_exempt_frame_holds_exactly_its_one_none_scope_guarded_mutation` —
  enumerate **ALL** raw memory mutation *statements* in `_migrate_memory_scope` (walk every
  `_statement_shape` that `_raw_mutation_of_table` matches, not first-match), assert (a) there is
  **exactly one** and (b) it is `WHERE scope IS NONE`-restricted. Equivalently: replace
  `_migrate_backfill_update_statement`'s first-`return` with a collect-ALL, and make the WHERE-none
  assertion ∀ over the collected statements.
- *Defect it catches:* the seizure above — and any co-located second same-verb memory write that L1
  collapses and the first-match pin shadows.
- *Not a current false clear:* the real `_migrate_memory_scope` holds exactly one blessed write (I
  AST-verified). This makes the frame's mutation SET a checked variable ∀, rather than a hidden constant.

## §R1 — self-containment: genuinely discriminating (5 wrong builds + reference control)

`exempt_entry_is_self_contained` (`_governed_contract.py:1094`) reuses `function_calls_named`. I ran the
two R1 legs (`TestEveryExemptAllowlistEntryIsSelfContained`) against 5 scratch mutations of the predicate
+ the reference control:

| mutation of the predicate | result | verdict |
|---|---|---|
| **CONTROL** (reference build) | **2 passed** | satisfiable ✓ |
| `return True` | 1 failed (discrimination: non-self-contained expected False) | **CAUGHT** ✓ |
| `return False` | 2 failed (live invariant + positive control) | **CAUGHT** ✓ |
| `return entry.exempt_name == "migrate-governed"` (token special-case) | 1 failed (both synthetics share token) | **CAUGHT** ✓ |
| **`return "run_query" in source or "execute_transaction" in source`** (seam ANYWHERE in source — the permissive build) | 1 failed on the **exact** discrimination assertion (`…reds_a_non_self_contained…`; live invariant PASSES) | **CAUGHT** ✓ (P0 control §METHOD) |
| `return function_calls_named(source, entry.site.function, "run_query")` (drop the exec-txn leg) | **2 passed** | not caught — **fail-CLOSED**, see residual |

The discrimination test (a fragment-builder synthetic: literal in `_build_fragment`, seam call in
`_drain`, plus a self-contained positive control, **same token** on both) is the load-bearing guardian
and it fires for the right reason. R1 is NOT vacuous. **SAFE.**

## §R2 — docstring bound: satisfiable, non-trapping, phrasing-robust (+ 2 accepted-bound residuals)

The 3-token matcher (`guarded_write`, `honest`, `138`, case-insensitive substrings of
`classify_tree_observed_write.__doc__`) run against 9 candidate docstrings (faithful replica of the
assertion; the reference-build real docstring is the positive control):

| candidate | matcher | note |
|---|---|---|
| reference-build real docstring (POSITIVE CONTROL) | GREEN | satisfiable ✓ (also proven by 20/0) |
| faithful bound clause | GREEN | ✓ |
| paraphrase A / paraphrase B (different words) | GREEN / GREEN | **phrasing-robust** ✓ (non-trapping) |
| missing `honest` / missing `138` / missing `guarded_write` | red / red / red | discriminates each token ✓ |
| **pure name-drop** ("See guarded_write. Be honest. Ticket 138.") | GREEN | **accepted bound** — R2's own threat model is the honest developer; gaming a docstring is out of scope |
| **coincidental `138x`** ("classifies a guarded_write label honestly; see line 1380 …") | GREEN | **residual (future false-green)** — a FUTURE edit that DELETES the bound clause but leaves a `guarded_write` mention + a `honest*` word + any `138x` number keeps the pin GREEN |

R2 is fit for its stated purpose (force the bound to be documented now + catch wholesale deletion) and
correctly non-trapping. The `138` token is the weakest (matches any `138x`); an optional cheap hardening
is to require `#138` or an additional low-collision mechanism token (`hand-set`). **Not a blocker** —
tightening to a phrase match would trap the builder, the exact thing R2's non-trapping design avoids.
**SAFE (residuals noted).**

## §P1b — QUANTIFIER TABLE (delta pins only; the core table is adversary-63a-v §P1b, unchanged)

| invariant | classification | receipt |
|---|---|---|
| R1: self-containment ∀ exempt allowlist entries | **∀** over exempt entries (anti-vacuity: ≥1 asserted) | 5-build battery §R1; W4 reds the discrimination |
| R1 discrimination: a non-self-contained entry reds; a self-contained passes | **∀** (both directions, same token) | `…reds_a_non_self_contained_exempt_entry` (control + mutant) |
| R2: the hand-set-label bound is NAMED in the classifier docstring | point-check on `__doc__` (a documentation invariant) | 9-candidate matcher §R2; RED-at-HEAD §P7 |
| **migrate WHERE-scope-IS-NONE (the exempt frame's write shape)** | **GUARDED-BY-FIRST-MATCH — should be ∀ over the frame's raw memory mutations** | **§R3 BLOCKER** — the seizure walks the unguarded door (a second same-verb UPDATE) |

The R3 row is the P1b failure mode exactly: an invariant conditioned on the ONE statement the extractor
happened to find, not ∀ over the frame's raw mutations. The same bad outcome (a seizure) reached through
a second-statement door engages no pin.

## §P1c — REACH TABLE (delta: R1's own instrument + the R3 recursion)

Legs: EMPIRICAL for R1's in-tree predicate; construction-inspection for the origin-match reach.

| instrument | reach DERIVED vs hand-list | coverage a CHECKED var? | effect vs proxy | one-source / mutation | verdict |
|---|---|---|---|---|---|
| `exempt_entry_is_self_contained` (R1) | ∀ over `MEMORY_TREE_ALLOWLIST` exempt entries (anti-vacuity ≥1) | **YES** — discrimination reds a synthetic non-self-contained entry; live invariant reds a genuine one | **effect** (AST of the real `entry.site.file`) | reuses `function_calls_named`; 5-build battery | **SAFE (empirical)** |
| R2 docstring pin | point on `__doc__` | reds on any missing token | effect (reads the doc) | one matcher | **SAFE** (residual: 138-coincidence) |
| **exempt-origin match reach = the exempt frame's raw-mutation SET** | **HIDDEN CONSTANT** — assumed = the ONE blessed write; NO ∀-check that the self-contained frame holds only its blessed mutation | **NO** — no pin reds when the frame grows a second same-verb memory UPDATE | effect | — | **MISSING PIN → §R3** |

R1 correctly makes *self-containment* a checked variable. The reach attack's residual, one level down:
the exempt frame's *contents* are not — the seizure launders because self-containment guarantees
`origin==site`, and nothing pins that the frame contains only its single adjudicated write.

## §PKG — package survey diff (P-PKG)
Independent table built before reading the author's:
- `governed_exempt`/`active_exempt` → `contextvars.ContextVar` + `contextlib.contextmanager` (stdlib);
  the shipped `write_guard` IS this exact pattern — a third-party context lib is strictly worse and
  breaks the ONE-IMPLEMENTATION mirror. **stdlib (no gap).**
- R1 predicate → stdlib `ast` via the in-tree `function_calls_named` (reuse, not a package). **keep.**
- R2 → a `str.__contains__` matcher. No package. **stdlib.**
DIFF vs author (`none — no new production mechanism`): **AGREED**.

## §RESIDUALS — every item, an individual verdict
- **R3 exempt-frame single-mutation ∀-pin** — **MISSING (verdict driver / BLOCKER-class survivor).** §R3.
- **R1 self-containment invariant + discrimination** — genuinely discriminating; 5-build battery caught,
  incl. the permissive "seam-anywhere" build on the exact assertion. **SAFE.**
- **R1 W5 (drop the `execute_transaction` leg)** — passes the battery but is **fail-CLOSED**: a
  self-contained entry using `execute_transaction` (not `run_query`) would be flagged non-self-contained
  → RED → re-adjudicate. Never a false clear (safe direction). Migrate uses `run_query`, so inert today.
  An optional harder discrimination leg (a self-contained-via-`execute_transaction` positive control)
  would pin it. **SAFE (noted).**
- **R2 satisfiable/non-trapping/phrasing-robust** — faithful + 2 paraphrases GREEN; each token
  discriminated. **SAFE.**
- **R2 `138`-coincidence future false-green** — a FUTURE edit deleting the bound clause but leaving a
  `guarded_write` mention + `honest*` + any `138x` keeps it GREEN. Low-probability; primary purpose
  (documentation + wholesale-deletion catch) served. Optional hardening: `#138` or a `hand-set` token.
  **SAFE (noted).**
- **R2 pure name-drop greens it** — accepted bound (R2's own threat model is the honest developer, not a
  hostile author gaming a docstring). Consistent with the gate-threat-model law. **SAFE (accepted bound).**
- **Fold introduces no regression** — R1/R2 touched no scanner/observer/classifier logic; 63a-iv modules
  12/0 unchanged on the reference build. **SAFE.**
- **Core both-ways / whole-tree reach / migrate triple (WHERE-none single-statement) / #447 precision /
  observer default-target** — graded SUFFICIENT by adversary-63a-v; NOT re-litigated here except where
  R3 intersects the migrate triple. **Out of this grade's frame** (except §R3).

## §METHOD — instruments (deliverables; scratch is disposable by design)
- Scratch: `./scripts/scratch_copy.sh /tmp/cav63av2_adv` — provenance-asserted
  (`loremaster.__file__` inside the copy, printed §SAT). Reference build applied by inline `python3`
  `str.replace` edits to `governed.py` / `principals.py` / `_governed_contract.py`; pristine backups at
  `/tmp/ref_gc_v2.py`, `/tmp/ref_principals_v2.py`; every mutation restored (module back to 20/0, §SAT).
  No repo file mutated.
- **R1 battery** (5 predicate mutations + control): a Python loop applying each `str.replace` and running
  the two R1 test nodes; the permissive build's failing node captured with `-rA` (asserts on
  `…reds_a_non_self_contained_exempt_entry`, live invariant PASSES — P0 control).
- **R2 matcher battery**: a faithful replica of the assertion body
  (`all(t in doc.lower() for t in ["guarded_write","honest","138"])`) over 9 candidates, positive
  control = the reference-build real docstring.
- **R3 probe**: a second seizure `UPDATE` added to `_migrate_memory_scope` under the exempt block → 20/0
  (miss); the SAME probe with verb DELETE → 2 failed (L1 orphan — P0 positive control).
- All live runs against TEST store `ws://127.0.0.1:18000` (NEVER :18500) via `migration_world`.

## VERDICT: **CONTRACT INSUFFICIENT**
R1 and R2 are correctly built, satisfiable, and discriminating for their own jobs — the fold is clean and
introduces no regression. INSUFFICIENT rests on **ONE concrete missing pin (R3)**: a wrong build an honest
developer could ship — a second seizure `UPDATE` co-located in the self-contained exempt frame — survives
ALL 20 pins (repro + P0 positive control). R1 pinned self-containment as the origin-match's soundness
premise but left the SIBLING assumption unpinned: the exempt frame's raw-mutation SET is still a hidden
constant. **Fold the ∀ pin (§R3) — cheap, test-infra only — before the builder;** operator owns the
core-vs-delta scope call.
