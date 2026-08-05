# REPORT-adversary-04b4-2

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK
- state: **done**
- **VERDICT: CONTRACT SUFFICIENT** — adversary-04b4-1's BLOCKER (C-DEF corpse trap) is
  closed AND PROVEN closed; the #319 PIN-THE-MISS genuinely discriminates. One LOW-severity
  residual (note-only), not a driver.
- **C-DEF TRAP GONE: YES.** Reference correct fix at **cap=10 AND cap=50** → **125 passed /
  0 failed** across the touched suites, IDENTICAL count. Before the fix a legal cap<40
  reddened the (now-retired) corpse; no legal positive cap now reddens an un-editable pin.
- **PIN-THE-MISS DISCRIMINATES: YES.** Pristine helper → GREEN; closure (extend the derived
  matrix to required-for params) → RED with its own "you closed the bound — retire this pin"
  message. Required-for lie survives all 4 #319 pins today (gap is real). (§P3)
- **QUANTIFIER TABLE (delta):** §P1b — the two invariants the fix TOUCHED (#309 completeness,
  #319 class-bound) re-classified with receipts; the rest are unchanged from adversary-04b4-1's
  full table (fix adds/removes no invariant) and re-affirmed by cite.
- **MISSING PINS: none blocking.** One residual (§Residual-1): the PIN-THE-MISS keys on
  `_derived_strict_to_action_matrix` specifically, so a closure that adds a *separate*
  required-for derivation would leave it green (benign stale pin, never a false clear).
- Capability check: brief demanded lore tools + read/write scratch + test store + scratch
  mutation harness. All available/used. Store `ws://127.0.0.1:18000` UP. Fallback to
  grep/Read only for the non-symbol corpse-sweep textual seam (dogfood §3b), said out loud.
- **Packages considered: none — no mechanism specified** (test-only contract delta; the fix
  specifies no new mechanism). adversary-04b4-1's P-PKG stands: #309's ONE mechanism reuses
  in-tree `render_line` — `keep_with_trigger`.
- **Graded: `37d4adce69bb65adbd4f26e8d4ea3542217c6dbd` · HEAD-at-report:
  `37d4adce69bb65adbd4f26e8d4ea3542217c6dbd` · SAME.**
- Provenance: all builds in `/home/ejprice/lore-scratch-adv04b4-2` (provenance-asserting
  `scratch_copy.sh`); `loremaster.__file__ = /home/ejprice/lore-scratch-adv04b4-2/loremaster/loremaster/__init__.py`
  (printed §Sat). Disposable — `rm` freely.
- receipt pointers: satisfiability+C-DEF §Sat/§P1 · corpse sweep §P2 · PIN-THE-MISS §P3 ·
  cap-value §P4 · render-layer coherence §P5 · regression §P6.

---

## §Sat — SATISFIABILITY + the C-DEF reference build (item 1 + item 6)

I built the REFERENCE CORRECT fix in scratch (all three still-RED deliverables), parameterised
by cap, via `adv_apply_reference_fix.py` (pasted §Instrument-1):
1. **#309**: `_DEFAULT_TASK_QUERY_DISPLAY_CAP = <cap>`; the no-limit `query` branch
   materialises the full set (`query_tasks(...)`, NO store LIMIT), a new
   `_render_no_limit_task_query` classmethod caps the VIEW and discloses
   `K = len(all) − shown` with the house counted grammar `+K more — re-run with limit=N`;
   the caller-limited path is UNCHANGED (`_render_task_listing(_task_listing(...))`, existence
   grammar).
2. **#319 note**: served desc names `'acknowledge'` alongside `resolve`/`wontfix`.
3. **#324 R-4**: `_validate_comms_identities` `name`/`to` made keyword-REQUIRED; the 3 sites
   (`server.py`:3154/3597/3739) pass `name=None, to=None`.

Provenance receipt (scratch venv):
```
__file__ /home/ejprice/lore-scratch-adv04b4-2/loremaster/loremaster/__init__.py
cap 50
sig (agent: 'str | None', *, session: 'str | None', name: 'str | None', to: 'list[str] | None') -> 'None'
```

**Touched-suite run (`-n auto`), the contract pin set** — `test_task_read_surface.py` (FULL:
#309, #310(b), #324 R-3, the retired corpse's parent class `TestTheRenderedListingDISCLOSESItsOwnBOUND`,
`:487`/`:743` seam-uncapped pins, the served-filter `:2227` class), plus
`test_comms_footer.py::{TestEveryDispatchActionIsDrivableWithoutAMissingArgOrMethod,TestTheCommsIdentitySeamHasNoDefaultForNameOrTo}`,
`test_task_ledger.py::TestTransitiveBlockersCycleWalkAgreesFakeVsReal`,
`test_mcp_server.py::TestServedParamDescriptionsMatchTheRefusalMatrix`:

| build | result |
|---|---|
| **cap=50** (control — was passing pre-fix) | `125 passed in 7.61s` |
| **cap=10** (WAS the C-DEF trap: cap<40 reddened the corpse) | `125 passed in 7.56s` |

**Identical pass COUNT at both caps ⇒ no test is silently skipped or cap-value-dependent.**
The corpse retirement freed the cap floor: a legal cap<40 now goes 0-failed suite-wide. THE
C-DEF TRAP IS GONE.

---

## §P1 — item 1 detail: the C-DEF trap, controls both ways

The BLOCKER adversary-04b4-1 filed: the pre-existing corpse
`test_an_UNLIMITED_render_over_a_LARGE_ledger_carries_NO_line` asserted the RETIRED "no-limit
RENDER never discloses" over `_SURPLUS_POPULATION=40`, so any correct build with cap<40 served
`cap` rows + a `+(40−cap) more` line and reddened it — trapping the builder (un-editable pin).

- **At HEAD** (`git show 37d4adc`): the corpse is DELETED (test_task_read_surface.py, replaced
  by a `⚰` breadcrumb at ~:964 naming why), and its live property (complete answer discloses
  nothing) is subsumed by `test_the_no_limit_read_AT_OR_BELOW_the_cap_serves_NO_elision_line`.
- **Reference build cap=10** → `125 passed / 0 failed` (the trap value; **positive control that
  the trap is gone** — the exact cap that reddened the corpse pre-fix now passes).
- **Reference build cap=50** → `125 passed / 0 failed` (the pre-fix control leg — still passes).

Both legs present, both green, identical count ⇒ the pair proves the retirement (not a botched
fixture): the correct build is accepted at a cap that was formerly rejected.

---

## §P2 — CORPSE SWEEP, independent (item 2)

I grepped EVERY no-limit dispatcher/seam drive across the touched suites (bare, anchor-free —
`_rendered_listing(...limit=None)`, `_listing_over(...limit=None)`, `tasks(action="query")` with
no limit, `query_tasks()` direct, and the `NEVER_discloses/carries_NO/no disclosure` prose class),
NOT trusting the fix's hand-list. **No `_rendered_listing(..., limit=None)` remains — the corpse
was the only one.** Individual verdicts (every hit, no "the rest are fine"):

| site | drive | verdict |
|---|---|---|
| `test_task_read_surface.py` ~:964 | (retired corpse) | **RETIRED** — deleted + `⚰` breadcrumb. The trap. |
| `:487` `test_an_UNLIMITED_listing_NEVER_discloses_a_bound` | `_listing_over(40, limit=None)` → `_task_listing` SEAM | **OK, not a corpse** — seam stays uncapped (cap is at render); passes on reference build. |
| `:493` (same test body) | `_listing_over(40, limit=None)` | **OK** — same seam pin. |
| `:473` `test_a_SHORT_answer_carries_NO_disclosure` | `_listing_over(pop, limit=_LISTING_CAP)` SEAM, short answers | **OK** — caller-limited seam; short answers legitimately disclose nothing. |
| `:2808` `test_get_serves_the_DESCRIPTION…` | `tasks(action="query")`, 1 task | **OK** — asserts the description FIELD is omitted from the row, not "no disclosure"; 1 row < any cap. |
| `:2227` `TestTheDisclosureSurvivesTheFILTERSAtTheSERVEDSeam` | `tasks(action="query", …, limit=5)` | **OK** — CALLER-LIMITED (limit=5); filter-uniformity of the existence disclosure, independent of the display cap. |
| `:3400` #309 surplus pin | `tasks(action="query")` | **OK** — this wave's successor pin. |
| `:3452` #309 below-cap pin | `tasks(action="query")` | **OK** — this wave's successor pin. |
| `test_query_tasks_bounded.py:1201` `…UNLIMITED_query_still_serves_EVERYTHING` | `ledger.query_tasks()` DIRECT (store) | **OK, not a corpse** — asserts the STORE read stays uncapped; #309 caps the RENDER, not the store. Passes on reference build. |
| `test_query_tasks_bounded.py:743` `…emits_NO_LIMIT_CLAUSE_AT_ALL` | seam, no SQL LIMIT | **OK** — display cap is Python-side render slicing, not a SQL LIMIT. |
| `test_query_tasks_bounded.py:1187` | `tasks(action="query", limit=_SERVED_LIMIT)` | **OK** — caller-limited. |
| `test_query_tasks_bounded.py:1598` | `tasks(action="query", since=…)` | **OK** — a REFUSAL test (since is rollup-only), not disclosure. |
| `test_comms_footer.py:1255` | `action="query"` (fake dispatch, footer) | **OK** — comms-footer plumbing, not disclosure. |
| `test_task_ledger.py:568` | (docstring mention) | **OK** — prose, not a test. |

No OTHER pin asserts the retired "no-limit never discloses" semantics. Sweep clean.

---

## §P3 — PIN-THE-MISS DISCRIMINATES (item 3) — the central delta probe

The #319 PIN-THE-MISS's ONLY reddening condition is
`"subject" in _derived_strict_to_action_matrix(AppContext.tasks)` (a required-for witness param
that is structurally OUTSIDE the foreign-refusal matrix), plus a `create/supersede ∈ _TASK_ACTIONS`
witness that is always true. All probes on the pristine-server scratch:

**Part (b) — the required-for lie survives (the gap is REAL).** Reproduced adversary-1 probe 6 +
isolated it: made `subject` OPTIONAL for `supersede` in the dispatcher while its served prose
(`server.py:9289`) still reads *"required for 'create' and 'supersede'"*, AND fixed the live
`note` residual (so the only possible trigger left is the subject lie). Result:
```
loremaster/tests/test_mcp_server.py::TestServedParamDescriptionsMatchTheRefusalMatrix
....                                                                     [100%]
4 passed in 0.90s
```
**All 4 #319 pins GREEN with the required-for lie present** — the matrix pin (the only pin that
could conceivably check subject's prose) does NOT see it. Gap confirmed real.

**Matrix-pin POSITIVE CONTROL (the class boundary is real, not a dead pin).** On the same build I
also dropped `'query'` from `lore_tasks.limit`'s `For 'rollup' and 'query' ONLY` clause (a
MATRIX-class lie):
```
E    Extra items in the right set: 'query'
FAILED …::test_every_strict_to_action_param_description_matches_its_matrix
```
So the matrix pin CATCHES a matrix-class lie and is SILENT on a required-for lie — a genuine
class boundary, exactly what the PIN-THE-MISS documents.

**Part (a) — build the closure → PIN-THE-MISS goes RED.** In the scratch TEST copy I extended
`_derived_strict_to_action_matrix` to ALSO derive required-for params from the dispatcher's own
`_require_arg(<param>, …)` calls per `action == X` branch (the documented closure — "extend the
derived matrix to that class"). `subject → {create, supersede}` enters the matrix:
```
E    AssertionError: `subject` (a REQUIRED-FOR param of create/supersede) is now inside the
     derived strict-to-action matrix — the #319 derived guard has grown to cover the
     required-for class it was pinned as NOT covering. Meet the bound deliberately… retire
     this PIN-THE-MISS (#137/#138)… matrix params=['actor','created_by','description','items',
     'limit','max_depth','since','status','subject','task_id']
FAILED …::test_PIN_THE_MISS_the_derived_319_guard_is_bounded_to_its_class
```

**PIN-THE-MISS POSITIVE CONTROL — pristine helper → GREEN:**
```
loremaster/tests/…::test_PIN_THE_MISS_the_derived_319_guard_is_bounded_to_its_class
.                                                                        [100%]
1 passed in 1.05s
```

So the PIN-THE-MISS is a TRUE pin: GREEN while the bound is open, RED the day the derived matrix
is extended to cover the required-for class — carrying its own retire-me message. It discriminates.

---

## §Residual-1 (LOW severity — note only, NOT an INSUFFICIENT driver)

The PIN-THE-MISS keys on `subject in _derived_strict_to_action_matrix` — the FOREIGN-REFUSAL
helper SPECIFICALLY. Its reddening is a pure function of that ONE helper's output. The finding-2
remedy the PIN documents ("derive `required for '<actions>'` from `_require_arg` calls") is a
prose shape (`"required for '<actions>'"`) and a guard shape (`_require_arg`) DISTINCT from the
matrix's (`"For '<actions>' ONLY"` / `action != X and param is not None`). A clean closure could
therefore add a SEPARATE `_derived_required_for_matrix` + its own pin and leave
`_derived_strict_to_action_matrix` untouched — closing the bound while the PIN-THE-MISS stays
GREEN (an orphaned tautology asserting a gap that no longer exists).

- This is a STRUCTURAL certainty from the pin's single assertion (a separate method cannot add
  `subject` to a helper it does not modify); I confirmed the pristine helper's output omits
  `subject` and that only a direct edit of THAT helper adds it (§P3).
- Severity is LOW: the failure mode is a benign stale-GREEN pin, never a false clear or a
  builder trap. The pin's own re-open trigger says "EXTEND the derived matrix", which DOES
  redden it, so the pin is internally consistent with its stated closure — the evasion is only
  the *cleaner separate-method* implementation.
- OPTIONAL hardening (author's call, not required for SUFFICIENT): broaden the witness so it
  reddens on ANY derived required-for coverage — e.g. assert `subject`'s served description is
  not validated by ANY `_derived_*` helper the class exposes, or add an explicit
  "no `_derived_required_for` symbol exists yet" leg. I surface this per scope law; I do not
  rule it in scope.

---

## §P1b — QUANTIFIER TABLE (delta scope)

The fix (37d4adc) is test-only and adds/removes NO invariant — it retires a corpse, adds a
PIN-THE-MISS, de-constrains the cap value, and refactors one AST helper. So the full ∀-vs-guarded
table from `REPORT-adversary-04b4-1.md §P1b` stands unchanged for every row the fix did not touch.
The two rows the fix TOUCHED, re-classified with fresh receipts:

| Invariant | Classification | Receipt (this pass) |
|---|---|---|
| **#309 completeness** (below-cap → no phantom disclosure) | ∀-ish at ONE fixture value — seed was 2, now **1** (`≤` any positive cap ⇒ cap-VALUE-agnostic) | Seed change BROADENS validity, doesn't weaken it: verified GREEN at cap=1/10/50; a forged constant `+0 more — re-run…` still matches `_COUNTED_ELISION` and reddens. §P4. |
| **#319 served-desc class bound** (∀ over {foreign-refusal matrix ∪ note}, required-for/clamp/value-set is a PINNED KNOWN BOUND) | guarded-by-CLASS, now with a **declared** bound (PIN-THE-MISS) | Matrix pin discriminates within class (matrix-class lie RED); required-for lie survives (gap real); PIN-THE-MISS reddens on closure, green when open. §P3. The `_accepting` refactor did NOT break derivation (§P6). |

Every other invariant (#309 honest-K, #309 two-grammars, #319 note-recorder, #322 both faces,
#324 R-2/R-3/R-4, #310(b)) carries its adversary-04b4-1 receipt; I re-affirmed the ones the edited
file could touch (§P6).

---

## §P4 — CAP VALUE UNCONSTRAINED (item 4)

The only value-ish gate is `_display_cap()` (`test_task_read_surface.py:3358`), relaxed
`>= 2` → `>= 1` by the fix. `>= 1` is DEFINITIONAL (a cap must be a positive int), not a value
choice.

- **cap=1** (the new floor) → the whole #309 class `5 passed` (de-constraint proven — the value
  is now free down to the definitional floor).
- **cap=0** → `_display_cap` fails at `:3358` (`3 failed` on the surplus legs) — **positive
  control: the definitional floor still bites** (0/negative/bool/non-int is not a cap).
- **cap=10 / cap=50** → `125 passed` each (§Sat).

No pin hard-codes a cap value or bounds it above; the surplus legs compute `population = cap +
surplus` (value-agnostic) and the below-cap leg seeds 1 (`≤` any positive cap). The floor>=1
introduced nothing beyond "must be a positive int". Cap = builder's choice, confirmed.

---

## §P5 — RENDER-LAYER placement is COHERENT (item 5) — no finding

Retiring the render-corpse while `:487` (seam, `_task_listing`, uncapped, `more is False`) stays
green pins the cap to the RENDER layer. I verified this is CONSISTENT, not incoherent, because a
SINGLE reference build satisfies simultaneously:
- **seam/store stays UNCAPPED**: `:487`/`:493` (seam serves all 40), `test_query_tasks_bounded.py:743`
  (no SQL LIMIT clause), `:1201` (`query_tasks()` direct serves EVERYTHING) — all GREEN on my
  materialise-full build; AND
- **render caps + discloses K**: the #309 surplus/below-cap pins — GREEN on the same build.

Further, the **honest-K pin FORCES** the render-cap placement: a build that instead capped the
STORE on the no-limit path could only fetch `cap` rows and could not know the true surplus K,
so `elided == surplus` would redden (§P6). So the contract structurally excludes a store-side
cap on the no-limit path and requires materialise-full-then-slice — exactly wave-C §2 (full set
materialised; `K = len(materialised) − shown`; cap is a render-view property). The contract-fix
§3 FLAG documents this placement; it is coherent and correctly pinned. **No finding.**

---

## §P6 — NO REGRESSION (item 6)

The fix diff (`git show 37d4adc --stat`) touches EXACTLY two test files
(`test_mcp_server.py` +59, `test_task_read_surface.py` +51/−29) and NO production code. Regression
surface + fresh mutation spot-checks (each with the wrong-build RED shown):

- **#319 matrix (the `_accepting` AST refactor — the ONLY guard-logic change):** matrix-class
  lie (`limit` ONLY clause drops `query`) → matrix pin RED (§P3). The refactor is behaviour-
  preserving; derivation still discriminates. ✔
- **#309 honest-K:** forged constant `+1 more` in the render → surplus-2/surplus-7 RED (`elided ==
  surplus` at `:3417`), surplus-1 GREEN. Constant/window K cannot survive. ✔
- **#324 R-3 branch scan** (in the EDITED file — highest collateral risk): made the findings
  `wontfix` branch dead → `test_every_declared_action_BRANCHES_in_the_dispatcher` RED (`Left
  contains one more item: 'wontfix'`). ✔
- **#322 both faces / #324 R-2 / #324 R-4 / #310(b):** NOT touched by the 2-file test-only diff
  (they live in `test_comms_footer.py`, `test_task_ledger.py`, and untouched classes of
  `test_task_read_surface.py`), so they are byte-identical to their adversary-04b4-1-verified
  state — an unedited pin over unchanged production cannot regress. All passed on the reference
  build (part of the 125-passed set + the explicit R-4/#322/R-2 class runs at cap=10/50). I did
  not re-run adversary-1's mutations for these (no new information); their discrimination rests
  on `REPORT-adversary-04b4-1.md §P1/§5`.

Satisfiability re-confirmed: reference correct fix → **0-failed suite-wide at cap=10 AND cap=50**
(§Sat).

---

## §Instrument-1 — the reference-fix patch (deliverable, pasted verbatim)

Committed to scratch as `adv_apply_reference_fix.py`; the scratch tree is disposable, so it is
pasted here so the measurement is re-runnable. Applies all three still-RED deliverables to a
scratch `server.py`, parameterised by `--cap`, restoring from a pristine backup each run.

```python
#!/usr/bin/env python3
"""Apply the #309/#319/#324-R4 REFERENCE CORRECT fix to the scratch server.py, by --cap."""
from __future__ import annotations
import argparse, shutil
from pathlib import Path
SERVER = Path("loremaster/loremaster/server.py")
PRISTINE = Path("loremaster/loremaster/server.py.pristine")
def _restore_pristine():
    if not PRISTINE.exists(): shutil.copy2(SERVER, PRISTINE)
    else: shutil.copy2(PRISTINE, SERVER)
def _replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1: raise SystemExit(f"ANCHOR '{label}': expected 1, found {n}")
    return text.replace(old, new)
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--cap", type=int, required=True)
    cap = ap.parse_args().cap
    _restore_pristine(); text = SERVER.read_text()
    # #309 constant
    text = _replace_once(text,
        "_TASK_ACTIONS_ACCEPTING_LIMIT = (_TASK_ACTION_ROLLUP, _TASK_ACTION_QUERY)\n",
        "_TASK_ACTIONS_ACCEPTING_LIMIT = (_TASK_ACTION_ROLLUP, _TASK_ACTION_QUERY)\n"
        f"_DEFAULT_TASK_QUERY_DISPLAY_CAP = {cap}\n", "constant")
    # #309 render classmethod (materialise-full, slice, disclose K = len(all) - shown)
    new_method = (
        "    @classmethod\n"
        "    def _render_no_limit_task_query(cls, all_rows: list) -> str:\n"
        "        cap = _DEFAULT_TASK_QUERY_DISPLAY_CAP\n"
        "        shown = all_rows[:cap]\n"
        "        rendered = cls._render_task_rows(shown)\n"
        "        remainder = len(all_rows) - len(shown)\n"
        "        if remainder <= 0:\n"
        "            return rendered\n"
        "        next_limit = len(all_rows)\n"
        '        return f"{rendered}\\n+{remainder} more — re-run with limit={next_limit}"\n\n'
        "    @classmethod\n"
        "    def _render_task_listing(cls, listing: TaskListing) -> str:\n")
    text = _replace_once(text,
        "    @classmethod\n    def _render_task_listing(cls, listing: TaskListing) -> str:\n",
        new_method, "render-method")
    # #309 rewire query branch: no-limit -> new render; caller-limited unchanged
    old_query = (
        "            rendered, writes = (\n"
        "                AppContext._render_task_listing(\n"
        "                    await AppContext._task_listing(\n"
        "                        self, status=status, owner=owner, blocked=blocked, limit=limit\n"
        "                    )\n                ),\n                0,\n            )\n")
    new_query = (
        "            if limit is None:\n"
        "                rendered, writes = (\n"
        "                    AppContext._render_no_limit_task_query(\n"
        "                        await self.task_ledger.query_tasks(\n"
        "                            status=status, owner=owner, blocked=blocked\n"
        "                        )\n                    ),\n                    0,\n                )\n"
        "            else:\n"
        "                rendered, writes = (\n"
        "                    AppContext._render_task_listing(\n"
        "                        await AppContext._task_listing(\n"
        "                            self, status=status, owner=owner, blocked=blocked, limit=limit\n"
        "                        )\n                    ),\n                    0,\n                )\n")
    text = _replace_once(text, old_query, new_query, "query-branch")
    # #319 note names 'acknowledge'
    text = _replace_once(text,
        "                    \"An optional free-text note recorded with a 'resolve' / 'wontfix' \"\n"
        '                    "transition. Ignored by the other actions."\n',
        "                    \"An optional free-text note recorded with an 'acknowledge' / \"\n"
        "                    \"'resolve' / 'wontfix' transition. Ignored by the other actions.\"\n",
        "note-desc")
    # #324 R-4 name/to keyword-REQUIRED + 3 sites pass them
    text = _replace_once(text,
        "        *,\n        session: str | None,\n        name: str | None = None,\n"
        "        to: list[str] | None = None,\n    ) -> None:\n",
        "        *,\n        session: str | None,\n        name: str | None,\n"
        "        to: list[str] | None,\n    ) -> None:\n", "identity-sig")
    text = text.replace(
        "AppContext._validate_comms_identities(agent, session=session)\n",
        "AppContext._validate_comms_identities(agent, session=session, name=None, to=None)\n")
    SERVER.write_text(text); print(f"applied reference fix at cap={cap}")
if __name__ == "__main__": main()
```

The PIN-THE-MISS closure probe (§P3 part a) appended, before `return matrix` in the scratch copy
of `TestServedParamDescriptionsMatchTheRefusalMatrix._derived_strict_to_action_matrix`, a walk of
each `action == X` branch collecting `_require_arg(<param>, …)` first-args into
`matrix[param] |= {action}` — bringing `subject → {create, supersede}` into the matrix and
reddening the PIN-THE-MISS.

---

## §Bounds of this pass / what I did NOT do
- No edits to the repo, the contract tests, or git state (findings only; confirmed
  `git status` clean of tracked edits, HEAD = graded `37d4adc`). All builds in the disposable
  `scratch_copy.sh` tree.
- I did not re-litigate lead rulings (A)/(B)/(C) — I built #309 to the ruled AUTHORITY direction
  (render-cap, K derived, no `count()`), and treated the `⚑FORK` caller-limited leg as GREEN.
- I did not re-run the full repo suite (test-only delta; the touched-suite contract set is the
  scope). mypy/ruff satisfiability rests on adversary-04b4-1's clean run at the same regions plus
  the fix being test-only (no production edit); I did not re-run `scripts/typecheck.sh`.
- For #322/R-2/R-4/#310(b) I relied on the 2-file diff scope + the reference-build greens rather
  than re-running adversary-1's mutations (no new information available there).

## VERDICT: **CONTRACT SUFFICIENT**
The BLOCKER (C-DEF corpse trap) is closed and PROVEN closed: a legal cap<40 (cap=10) now goes
`125 passed / 0 failed` suite-wide, identical to cap=50. The #319 PIN-THE-MISS genuinely
discriminates (GREEN open, RED on the documented closure, with a matrix-pin positive control
proving the class boundary is real). The cap value is unconstrained (1/10/50 pass; 0 rejected as
non-cap). The render-layer placement is coherent and correctly forced by the honest-K pin. No
guard adversary-04b4-1 verified was weakened (matrix/honest-K/R-3 re-proven; the rest untouched by
a test-only diff). One LOW-severity residual (§Residual-1: the PIN-THE-MISS is evadable by a
separate-method closure, yielding only a benign stale-green pin) — surfaced per scope law, not a
driver.
