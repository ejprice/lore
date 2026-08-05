# REPORT-adversary-04b4-1

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK
- state: **done**
- **VERDICT: CONTRACT INSUFFICIENT** — 1 BLOCKER missing pin (a C-DEF trap + P6 corpse in the
  #309 area) + 1 named residual bound (#319 class boundary). Everything else is strong and
  discriminates.
- **P1 result — did a wrong build survive the contract? YES, and it TRAPS the builder.** A
  `_DEFAULT_TASK_QUERY_DISPLAY_CAP` of any value in **[2, 40)** — a choice the contract's own
  `_display_cap()` floor (`>= 2`) explicitly permits — passes ALL 41 new pins but reddens the
  pre-existing, un-editable `test_task_read_surface.py::TestTheRenderedListingDISCLOSESItsOwnBOUND::test_an_UNLIMITED_render_over_a_LARGE_ledger_carries_NO_line`.
  Controls: RED at cap=10, GREEN at cap=50. (§Finding-1)
- **Capability check:** brief demanded lore tools + read/write scratch + the test store + a
  scratch mutation harness. All available and used. Store `ws://127.0.0.1:18000` UP (R-2/#309
  live-store pins ran). lore index FRESH at HEAD. Fallback to grep/Read only for served prose in
  `Field(description=...)` literals (non-symbol textual seam — dogfood §3b), said out loud.
- **Satisfiability receipt (C-DEF):** built the reference CORRECT fix in scratch (cap=50 literal):
  **all 41 pins 0-failed; 642 pre-existing+new tests across the 5 touched suites 0-failed; ruff
  clean on changed prod files; no new mypy errors in changed regions.** The ONLY thing the cap
  value changes is the corpse pin above. (§Satisfiability)
- Packages considered: none external — #309's ONE mechanism (counted-elision render) correctly
  REUSES the in-tree shared `loremaster.render.render_line` (house grammar at `server.py`
  `_render_comms_fleet`), never a clone (#102) and no external lib applies. Contract mandates the
  reuse; my reference fix confirmed it works. Verdict: `keep_with_trigger` (reuse the shared render).
- Graded: `5c5ff7ae585bfcc4b9a507eafbd8a569c5aa7fba` · HEAD-at-report:
  `5c5ff7ae585bfcc4b9a507eafbd8a569c5aa7fba` · **SAME**.
- **Provenance:** all wrong-builds ran in `/home/ejprice/lore-scratch-adv04b4` (provenance-asserting
  `scratch_copy.sh`); `loremaster.__file__ = /home/ejprice/lore-scratch-adv04b4/loremaster/loremaster/__init__.py`
  (printed §Satisfiability). The scratch tree is a disposable `scratch_copy.sh` copy — `rm` it freely.
- receipt pointers: quantifier table §P1b · missing pins §Finding-1/§Finding-2 · discrimination
  proofs §P1 · satisfiability §Satisfiability · corpse sweep §P6.

---

## §Finding-1 — BLOCKER: #309 counted disclosure CONTRADICTS a pre-existing pin, and the contract under-constrains the cap so a legal build gets trapped (P6 corpse + P2 arithmetic-alignment + C-DEF trap)

**THE MISSING PIN (what the author must do):** RETIRE or REWRITE the pre-existing
`test_task_read_surface.py::TestTheRenderedListingDISCLOSESItsOwnBOUND::test_an_UNLIMITED_render_over_a_LARGE_ledger_carries_NO_line`
(at `test_task_read_surface.py:964`). It asserts the RETIRED semantics — *"an uncapped answer is
complete, so it discloses nothing"* — over a fixed population of `_SURPLUS_POPULATION = 40`:

```python
async def test_an_UNLIMITED_render_over_a_LARGE_ledger_carries_NO_line(self) -> None:
    rendered = await _rendered_listing(_SURPLUS_POPULATION, limit=None)   # drives the DISPATCHER, no limit
    assert rendered.splitlines() == _rendered_rows(rendered)             # <-- NO disclosure line
    assert len(_rendered_rows(rendered)) == _SURPLUS_POPULATION          # <-- all 40 rows served
```

**THE DEFECT IT (fails to) CATCH:** #309 ADDS the counted-elision disclosure to exactly this
surface (`tasks(action="query")` with no `limit`). The new pin
`test_the_no_limit_read_over_a_surplus_serves_an_HONEST_counted_line` requires a no-limit read over
`cap + surplus` to serve `cap` rows + `+K more — re-run with limit=N`. So for ANY
`_DEFAULT_TASK_QUERY_DISPLAY_CAP < _SURPLUS_POPULATION (40)` the no-limit render over 40 rows serves
`cap` rows + a `+(40−cap) more` line — the corpse's two assertions BOTH fail. The two pins assert
**contradictory** things about the same surface. They coexist green at HEAD's would-be fix ONLY
because a cap ≥ 40 makes the corpse's 40-row fixture fall *below* the cap (P2 axis-3 arithmetic
alignment — a "no disclosure" pass for a fixture reason, not a code reason).

**WHY THIS IS A CONTRACT DEFECT, not a builder-reconciliation chore:**
- The contract's `_display_cap()` gate **only requires `cap >= 2`** (`test_task_read_surface.py:3350`).
  It communicates NO cap-vs-population constraint. A builder who reads the #309 contract and picks a
  natural task-query display cap (10, 20, 25 — all `>= 2`, all sane, all *smaller* than lore's own
  drain cap of 50) satisfies **all 41 new pins** and then hits a RED pre-existing pin **they may not
  edit** (builder ≠ contract author in this repo's TDD). That is the C-DEF trap verbatim: *"a
  pre-existing pin the reshape structurally contradicts, trapping the builder between ruff and a test
  it may not edit."*
- It is also the **P6 dual (corpse)**: a test written before the semantic change certifies the OLD
  world. #309 retires *"the no-limit read never discloses"*; the sweep for pre-existing no-limit
  render assertions was owed (P8d rename-sweep law) and this one was missed. #309's OWN
  `test_the_no_limit_read_AT_OR_BELOW_the_cap_serves_NO_elision_line` already pins the correct
  successor property (complete-**below-cap** → no disclosure), so the corpse is now redundant AND
  contradictory — retire it.

**FIX (for the contract author):** delete the corpse (its property is subsumed by the two #309
successor pins, correctly scoped to the cap), OR rewrite it to seed a population *below* the display
cap and assert completeness there. If you keep a cap-relative fixture anywhere, tighten
`_display_cap()`'s floor and DOCUMENT the constraint so the value is not a hidden landmine. Note the
sibling `test_an_UNLIMITED_listing_NEVER_discloses_a_bound` (`:487`) is NOT a corpse — it drives the
`_task_listing` **helper** directly, which #309 correctly leaves uncapped (the cap is a
dispatcher-surface property), so it stays green and correct.

**Reproduction (controls both ways):** see §P1 probe 1.

---

## §Finding-2 — RESIDUAL (PIN-THE-MISS): the #319 durable guard is CLASS-BOUNDED; required-for / clamp / value-set served-prose lies are unguarded

**THE MISSING PIN:** either extend the derived guard to the **required-for** class (derive the
`required for '<actions>'` set from the dispatcher's own `_require_arg(<param>, ...)` calls per
`action == X` branch, and require the served prose to name exactly that set), OR ship a **PIN-THE-MISS**
(#137/#138) that ASSERTS the bound — *"the #319 durable guard covers only the foreign-param refusal
matrix + the `note` recorder set; required-for / clamp / value-set prose drift is NOT derived-guarded"* —
with a named re-open trigger, so the next engineer meets the boundary deliberately instead of by outage.

**THE DEFECT IT CATCHES:** a served-prose lie of the #319 class that lies *outside* the matrix. Demonstrated
(scratch): making `subject` optional for `supersede` while its served description still reads *"required
for 'create' and 'supersede'"* — a served lie about a `lore_tasks` param — **survives all three #319
pins** (`TestServedParamDescriptionsMatchTheRefusalMatrix`). The matrix pin only scans
`action != X and param is not None` foreign-refusal guards (which `_require_arg` params do not have); the
note pin only covers `note`. See §P1b + §P1 probe 6.

**SCOPE HONESTY:** D-#319's ruling scoped the DERIVED pin to *"the refusal matrix it describes"* and made
the remainder a **one-time anchor-free sweep** (which the sweep-desc-04b4-1 report delivered: 58 TRUE / 1
FALSE / 41 NO-RULE at HEAD). So the required-for/clamp/value-set classes being unguarded-against-FUTURE-drift
is arguably WITHIN the ruling's scope — I do not decide scope (scope law), so I surface it as a residual,
not as the INSUFFICIENT driver. But per the QUANTIFIER LAW the outcome *"served descriptions match behaviour"*
is pinned ∀ only over {foreign-refusal matrix ∪ note}, not ∀ over all served descriptions carrying a rule —
so at minimum it should be a PINNED KNOWN BOUND, not a silent gap.

---

## §P1b — QUANTIFIER TABLE (∀-over-inputs vs guarded-by-failure-mode), every guarded row with a receipt

| Invariant | Classification | Receipt |
|---|---|---|
| **#309 honest-K** (`K == true surplus`, no forged/constant/window count) | **∀ over surplus** — parametrised `surplus ∈ {1,2,7}`, each `fate` forced with a distinct population | Constant-K wrong build (`+1 more` always) RED at surplus-2 & surplus-7, GREEN at surplus-1. §P1 probe 2. |
| **#309 completeness** (below-cap → no disclosure) | ∀-ish, but at ONE fixture value (2 rows) | GREEN guard; regex `\+\d+ more` catches a phantom `+0 more`. Note: over-claim of the RETIRED "no-limit never discloses" lives in a *pre-existing* pin → §Finding-1. |
| **#309 two-grammars-two-properties** (caller-limited keeps existence) | guarded-by-input-shape (did caller pass `limit`?) | GREEN guard `⚑FORK`; rests on lead ruling (A). Discriminates: existence-mark asserted present, counted-regex asserted absent. |
| **#319 served-desc matches refusal matrix** | guarded-by-CLASS (foreign-refusal params only, ∀ over tasks+findings) | Matrix drift RED (author's `limit` proof + my independent `since` reasoning); **class boundary leaks** required-for/clamp/value-set → §Finding-2, §P1 probe 6. |
| **#319 note names every recorder** | ∀ over recorder set DERIVED from dispatcher branches | RED at HEAD (live residual); GREEN when `acknowledge` named. Reddens on a new note-forwarding action. |
| **#322 dispatch drivable** (no missing-arg / missing-method) | **∀ over `TASK_*/FINDING_* ACTIONS`**, and those tuples are pinned `== _TASK_ACTIONS/_FINDING_ACTIONS` both directions (`:847`) — so ∀ over the dispatcher's own action set | BOTH faces fire fail-closed with naming messages: KWARGS fall-through (§P1 probe 3) AND DOUBLE missing-method (§P1 probe 4). Positive control ships. |
| **#324 R-2 fake==real cycle walk** | ∀ over cycle length `{1,2,3,5}`, each fate forced (self-reach `n0` asserted present) | Real-side divergence (`ids[:-1]`) RED at all lengths; injected-drift control fires. §P1 probe 5. |
| **#324 R-3 every declared action branches** | ∀ over `_TASK_ACTIONS` AND `_FINDING_ACTIONS`, ONE shared scan | Dead findings `wontfix` branch RED (asymmetry closed); `In`-control proves batch verbs seen. §P1 probe 7. |
| **#324 R-4 name/to keyword-required** | seam signature ∀ (2 params) + behavioural raise; call-site coverage via existing tests | Forgotten `claim_task` site (the weakest-covered of the 3) → 35 pre-existing tests RED loud. §P1 probe 8. |
| **#310(b) validate-before-transform** | guarded-by-source-order on the ONE known seam (PIN-THE-MISS for the class, by design) | Reorder (`cap + 1` above `validated_task_limit(`) RED. §P1 probe 9. Class deferral is ruled/adjudicated. |

---

## §Satisfiability — the C-DEF reference build

Scratch: `./scripts/scratch_copy.sh /home/ejprice/lore-scratch-adv04b4` (provenance-asserting).
`loremaster.__file__ = /home/ejprice/lore-scratch-adv04b4/loremaster/loremaster/__init__.py` (printed;
the scratch tree's OWN code ran). Reference CORRECT fix (all three deliverables):
1. `server._DEFAULT_TASK_QUERY_DISPLAY_CAP = 50`; no-limit `query` branch materialises the full set
   (no store LIMIT), caps the view, discloses `K = len(all) − shown` via the shared `render_line`
   house grammar (a new `_render_no_limit_task_query` classmethod — `_task_listing` UNCHANGED so the
   helper-level pins at `:487`/`:744` stay green).
2. `lore_findings.note` served description names `'acknowledge'` alongside `resolve`/`wontfix`.
3. `_validate_comms_identities` `name`/`to` defaults removed (kept keyword-only); the 3 call sites
   (`findings`:3154, `claim_task`:3597, `tasks`:3739) pass `name=None, to=None`.

Results at **cap=50** (correct build):
- **41 new contract pins: `41 passed`.**
- **Full touched suites: `383 passed`** (test_task_read_surface + test_query_tasks_bounded +
  test_comms_footer) **+ `259 passed`** (test_task_ledger + mcp_server description classes) = **642
  green, 0 failed** across the five touched suites.
- `uv run ruff check loremaster/server.py loremaster/tasks.py` → **All checks passed!** No orphaned
  imports created (the fix adds/removes none), so the "after cleanup" leg has nothing to break a pin.
- mypy: the canonical `scripts/typecheck.sh` is repo-wide (with known pre-existing packet-39 errors,
  per REPORT-contract-04b4-1 §SUMMARY); a targeted `mypy loremaster/server.py` fails only on config
  ("Source file found twice"/`lorescribe` stubs) — **no error references my changed regions**
  (`_render_no_limit_task_query`, `_DEFAULT_TASK_QUERY_DISPLAY_CAP`, `_validate_comms_identities`).

**Conclusion:** the contract IS satisfiable — by a correct build whose cap ≥ `_SURPLUS_POPULATION`.
It is the UNDER-CONSTRAINED cap (Finding-1) that makes a *different* correct-shaped build trap the
builder, which is exactly what the C-DEF receipt exists to expose.

---

## §P1 — WRONG-BUILD PROBE RECORD (commands + real output tails)

All in scratch. Cap parameterised via `ADV_DISPLAY_CAP` during probing; final reference fix uses a
literal `50`.

**Baseline (real tree, read-only) — confirms the contract's own RED/GREEN claim:**
`6 failed, 35 passed` — the 3× #309 surplus, 1× #319 note, 2× #324 R-4 REDs; 35 GREEN guards. ✔ matches
REPORT-contract-04b4-1 §1.

**Probe 1 — #309 C-DEF trap (Finding-1), controls both ways.**
- `ADV_DISPLAY_CAP=10`: the 41 new pins → `41 passed`; the pre-existing corpse pin →
  `FAILED … test_an_UNLIMITED_render_over_a_LARGE_ledger_carries_NO_line` — served
  `…(id …)\n+30 more — re-run with limit=40` where the pin demands 40 rows and no line.
- `ADV_DISPLAY_CAP=50`: same corpse pin → `1 passed` (positive control — the correct-build leg).
- ⇒ a legal cap ∈ [2,40) passes the whole contract yet contradicts an un-editable pin.

**Probe 2 — #309 honest-K discriminates.** `_render_no_limit_task_query` → constant `more=1`:
`2 failed, 1 passed` — `surplus-2`/`surplus-7` RED (`assert 1 == 7`), `surplus-1` GREEN. Constant/window
K cannot survive.

**Probe 3 — #322 KWARGS fall-through face.** Made `query` require `status` (fixture supplies none):
`FAILED …[query]` → *"lore_tasks action='query': driving it through its own _task_action_kwargs raised
a missing-arg ValueError … Add its branch to _task_action_kwargs (#322, KWARGS face)."* Fails CLOSED,
names the action.

**Probe 4 — #322 DOUBLE missing-method face.** Made the query branch call
`self.task_ledger.a_verb_the_fake_lacks()`: `FAILED …[query]` → *"FakeTaskLedger lacks a method its
production twin has ('… has no attribute 'a_verb_the_fake_lacks') … (#322, DOUBLE face …)."* Fails
CLOSED, names the gap. (`:847` partition pin proven to enforce `tuples == production` both directions,
so the ∀ ranges over the dispatcher's own action set — the name-free claim holds.)

**Probe 5 — #324 R-2 parity discriminates.** Real walk `ids=within[:-1]`:
`4 failed` at lengths {1,2,3,5} — `frozenset({'n1','n3','n4','n2'}) != frozenset({…,'n0'})`. The
shipped injected-drift control also passed on the correct build (dropping `n0` is detected). Store-backed.

**Probe 6 — #319 class boundary leaks (Finding-2).** `subject` made optional for `supersede`, prose
still says *"required for … supersede"*: `3 passed` — all three #319 pins GREEN. The lie survives.

**Probe 7 — #324 R-3 asymmetry closed.** Findings `wontfix` branch made dead
(`elif action == "definitely_dead_wontfix"`): `FAILED test_every_declared_action_BRANCHES_in_the_dispatcher`
→ *"lore_findings: these declared actions reach NO dispatch branch: ['wontfix']"*; positive control
(incl. the `In`-branch batch-verb assertion) `passed`. One shared scan reddens for a dead branch on
EITHER surface.

**Probe 8 — #324 R-4 all 3 call sites covered.** Reverted ONLY the `claim_task` site to omit `name/to`
(the site with the *narrowest* coverage — not driven by #322): `35 failed` across
`TestAHostileIdentityIsREFUSED…`, `TestTheREADBudgetHoldsOnALLTHREEDispatchers`,
`TestTheProductionSeamEXISTSAndIsTheThingDriven` — all loud `TypeError`. The tasks/findings sites are
driven by the #322 ∀ invariant + every footer leg. So a forgotten call site reddens loud at all three.

**Probe 9 — #310(b) source-order.** Moved a `cap + 1` transform above `validated_task_limit(` in
`_task_listing`: `FAILED test_the_KNOWN_over_fetch_seam_validates_BEFORE_it_transforms` →
`assert 2731 < 2648`. The narrow ordering instrument fires; the general class is a ruled/adjudicated
PIN-THE-MISS (not re-litigated).

---

## §P6 — CORPSE SWEEP verdict (pins asserting the RETIRED no-limit semantics)

I grepped every no-limit **dispatcher** drive (`tasks(action="query")` with no `limit`, and
`_rendered_listing(…, limit=None)`) in the touched suites. Individual verdicts:
- `test_task_read_surface.py:966` `test_an_UNLIMITED_render_over_a_LARGE_ledger_carries_NO_line` —
  **CORPSE** (asserts retired "no-limit never discloses" over pop 40; passes only for cap ≥ 40). →
  Finding-1.
- `test_task_read_surface.py:2807` (in `test_get_serves_the_DESCRIPTION…`) — **OK** (1 task, below any
  cap; unaffected).
- `test_task_read_surface.py:3397 / 3449` — the NEW #309 pins themselves. **OK** (this wave).
- `test_task_read_surface.py:487` `test_an_UNLIMITED_listing_NEVER_discloses_a_bound` — **OK, NOT a
  corpse**: drives the `_task_listing` HELPER directly, which #309 correctly leaves uncapped; stays
  green and correct. (A useful signal that the author kept the helper-level semantics right — the miss
  is only at the dispatcher-render level.)

---

## §What I did NOT do / bounds of this pass
- I did not edit the contract, the production tree, or git state (findings only). All wrong builds
  and the reference fix live in the disposable scratch copy.
- I did not re-litigate lead rulings (A)/(B)/(C) — I built #309 to the ruled AUTHORITY direction and
  the `⚑FORK` leg is treated as GREEN-on-correct-build.
- The satisfiability mypy leg is bounded: I confirmed ruff-clean + no new errors in the changed
  regions, but did not run the whole-repo `scripts/typecheck.sh` (it carries pre-existing packet-39
  errors unrelated to this scope, per REPORT-contract-04b4-1 §SUMMARY, and my changes are type-trivial).
- Findings-2's classification as residual-vs-missing-pin is a scope call for the lead; I surface it
  either way (scope law).

## VERDICT: **CONTRACT INSUFFICIENT**
Missing pin (BLOCKER): retire/rewrite the P6 corpse
`test_an_UNLIMITED_render_over_a_LARGE_ledger_carries_NO_line` (it contradicts #309 for any legal
cap < 40, trapping the builder). Residual: PIN-THE-MISS the #319 class boundary (required-for/clamp/
value-set prose drift is unguarded — demonstrated by a surviving wrong build). Everything else
discriminates, and a correct build with cap ≥ 40 goes 0-failed suite-wide (642 tests).
