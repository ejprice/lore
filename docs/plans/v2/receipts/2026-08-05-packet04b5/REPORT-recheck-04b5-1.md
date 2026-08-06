# REPORT-recheck-04b5-1 — INDEPENDENT RECHECK of the packet 04b5 render-reach contract (pre-production-build)

brief-base v10 read
brief project v7 read

## CAPABILITY CHECK (tool honesty, first)
Brief satisfiable with the tools granted. lore tools loaded first try (`ToolSearch "+lore"`, no
#334 flake); registered + drained (empty inbox) on `lore_comms` session `pkt04b5`. This is a
RECHECK (read-only + this report + a throwaway scratch reference build): I EDIT no tracked file.
I verified BY CONSTRUCTION — I re-ran the full contract at HEAD, wrote and ran my OWN discrimination
probes (DIFFERENT injection targets than the author's, pasted §INSTRUMENTS), and did a
**scoped reference build** in a `scratch_copy.sh`-provenanced tree (`loremaster.__file__` printed,
coverage.py resolved). lore-first for symbols; **grep/AST is the honest tool** for the interpolation
universe + ternary-arm sweeps (cross-cutting structural maps — dogfood case (c)), used there and
said so. Tests hit spike-surreal `:18000` only; I ran none against `:18500`. No lore weakness forced
a route-around; nothing filed.

## SUMMARY BLOCK
- state: **done** — recheck verdict rendered.
- **VERDICT: NO-GO** — ONE blocking gap, and it is the one my §5 exists to catch. The contract
  LOGIC is verified SOUND (D-A/D-B/D-C discriminate by my own construction; every preserve net is
  green + non-vacuous; core satisfiability is MEASURED). But the **#133 §SAT satisfiability receipt
  was produced by NOBODY** (empty placeholder in REPORT-contract-04b5-**3** AND -**5**; no
  `refbuild-04b5` report exists on disk or in git), and REPORT-contract-04b5-5 **falsely claims it is
  "filled" in four places** (lines 10, 25-26, 43, 138) — a served-prose/measured-behaviour mismatch,
  the exact trust-doctrine class this repo exists to catch. A full 0-failed against a reference build
  has never been demonstrated. That is a named gap → contract author; the remediation is NARROW
  (my scoped build is the verified head start), not a redesign.
- deviations: I did a **SCOPED** reference build (the seam + 2 of ~40 renders routed → 53F→39F in
  scratch, P-S invariant, seam suites green), NOT a full 0-failed build — I MEASURED the risky core
  and ASSESSED the mechanical remainder, and I SAY which (the brief's §5 alternative). This is why my
  own evidence supports satisfiability-in-fact but does NOT itself discharge #133's 0-failed proof.
- **Packages considered:** none — no mechanism specified (this is an audit; the seam I built in
  scratch is throwaway, not a shipped mechanism). coverage.py posture assessed as a finding (§7): it
  is correctly `[dependency-groups]` dev, and the pyproject prose now accurately states it ships in
  the image venv for #139 conformance.
- **Graded:** `f11fc67a7daaea2de3460ce6cbd7863b5cde65cc` (HEAD) · HEAD-at-report: `f11fc67` ·
  **SAME**. Every "GREEN/RED at HEAD" claim re-derived here at `f11fc67`.
- decisions-needed: (1) whether the lead/operator accepts my scoped-build + assessment as sufficient
  satisfiability evidence to proceed, OR requires the author to produce the full 0-failed §SAT first
  (#133 as written requires the latter — surfaced, not decided by me).
- receipt pointers: well-formedness + C-DEF §1 · D-A §2 · D-B + ternary §3 · D-C §4 · **§SAT gap §5**
  · preserve §6 · quality §7 · residual table §R · re-runnable instruments §INSTRUMENTS.

---

## §1 — WELL-FORMEDNESS + THE C-DEF CHECK — PASS

Full contract at HEAD `f11fc67` (`-n auto`, count in the tail):
```
loremaster/tests/test_link5_render_containment.py  =>  53 failed, 100 passed (153 collected)
loremaster/tests/test_task_read_surface.py         =>   3 failed,  96 passed  (fence-unify rework)
loremaster/tests/test_mcp_server.py                =>       645 passed
loremaster/tests/test_render_seam_pins.py          =>        27 passed  (pre-existing seam suite)
```
- Collects clean; **56 REDs total** (53 link5 + 3 fence-unify). I enumerated EVERY one by class and
  each is **FEATURE-ABSENT** (`render_attributed` / `sanitise.fence_width` / the error seam / the
  search.py route-through do not exist at HEAD):
  - 27 `TestEveryDrivenRenderNeutralisesEveryForgery` (P-N door leaks) · 13
    `TestEveryRenderLayerDoorNeutralisesAForgery` (hand-picked subset) · 6+1
    `TestFenceWidthIsTheONEExtractedWidthPolicy` · 4 `TestRenderAttributedIsTheInlineContainmentSeam`
    · 1 `TestNoServedDomainErrorLeavesACallerParamUncontained` (49-door error scan) · 1
    `…older_schema_rows…` = **53**.
  - 3 `TestEveryFenceSiteInProductionResolvesToTheONEImplementation` (fence_width absent +
    search.py:1461 still a private fence site) = **3**.
- **NO non-feature RED.** P-S (`TestEveryDrivenRenderBranchIsExercised`), P-F
  (`TestTheFieldManifestCannotSilentlyMissAField`), P-U (`TestEveryRenderCandidateIsDrivenOrOut`),
  D-C (`TestTheBranchExemptSetIsEarned`) are ALL **GREEN** at HEAD — none is a C-DEF trap (an
  unsatisfiable pin RED-today). This directly resolves cold-audit-04b5-5's D-B "P-S RED-at-HEAD,
  unsatisfiable-by-fix" blocker: the store-free shapes were completed and P-S is now green.
- Zero-new-mypy: `MYPYPATH=loremaster:loremaster/tests mypy test_link5_render_containment.py` →
  `Success: no issues found`.
- `test_attribution_bound.py` is **deleted at HEAD** (removed in the 969fa1c checkpoint) — correct
  per the lead ruling ("retires WITH the fix; its re-open trigger is 'the 04b5 link-5 slice'").

## §2 — D-A (P-F field-reach): DISCRIMINATES — the tautology is GONE (independent construction)
`_manifest()`'s `entry(cls, *, door, safe)` now binds **INDEPENDENT** `frozenset(door)` +
`frozenset(safe)` literals (`test_link5:1428-1440`); the guard and its control share ONE computation
`_unclassified_str_fields` (`:2352`) — `missing = strish − (door ∪ safe)`. `_is_str_ish` is broad
(`"str" in str(annotation)`), biased to INCLUSION (the safe direction for a completeness net).
- **Independent CONSTRUCTION** (§INSTRUMENTS-A — I targeted **Finding**, not the author's Task, and
  drove the ACTUAL guard method's loop over `_manifest()`): baseline GREEN → inject
  `Finding.caller_hint: str` → guard **RED** naming the field → restore GREEN. The `safe := strish −
  door` tautology (cold-audit-04b5-5 §1) cannot recur — a new caller-free-text field lands in neither
  literal and reddens. **CLOSED, confirmed.**

## §3 — D-B (P-S branch-reach): GREEN + DISCRIMINATES; ternary bound NOT exploitable
P-S runs the whole over-drive under real `coverage.Coverage(branch=True)` (`_over_drive_under_coverage`
`:2233`) and asserts, per driven render, no un-run line / un-taken branch arc.
- **Independent CONSTRUCTION** (§INSTRUMENTS-B — I targeted **`_render_claim_result`**, not the
  author's `_render_transitive_blockers`): baseline GREEN → REPLACE its shapes to invoke ONLY the
  `claimed=True` render → P-S **RED** naming `_render_claim_result` un-run lines
  `[3644,3645,3649,3650,3651,3657,3661,3666,3667,3669,…]` (the `claimed=False` elif/else legs) →
  restore GREEN. ⚠ I first reproduced the author's documented false-negative (slicing `shapes(g)[0]`
  runs ALL shapes eagerly, so coverage sees them — P-S wrongly reads green); the CORRECT methodology
  is to REPLACE the shapes fn, which I then did. The author's methodology note is right and load-bearing.
- **Ternary-arm bound (§D-B.2), independently verified** (§INSTRUMENTS-C): AST-scanned all 41 driven
  renders — exactly **2** f-string ternary interpolations exist, both `'y' if len(residue)==1 else
  'ies'` in `_render_transitive_blockers:4118-4119`; **both arms are string-literal constants**, no
  caller door bytes flow through any arm (`residue` appears only in the `len(...)` CONDITION). The
  author's §D-B.2 "not exploitable for this manifest" is **CONFIRMED**. (My first over-broad check
  false-flagged `residue` as laundered-from-`blocked_by`; restricting to arm VALUES cleared it.)
- **P-S is invariant under the fix** — MEASURED, see §5. **CLOSED, confirmed.**

## §4 — D-C (`_BRANCH_COVERAGE_EXEMPT` earned): DISCRIMINATES (independent construction)
`TestTheBranchExemptSetIsEarned` gives the exempt set the `_RENDER_OUT`/P-C treatment. Independent
CONSTRUCTION (§INSTRUMENTS-A) — all 3 abuse cases redden: (a) a store-FREE static render parked in
exempt (`_render_comms_ack`, no `self`) → RED (`…NOT store/self-backed instance methods`); (b) a
stale entry naming no driven render → RED; (c) an empty re-open trigger → RED. Baselines GREEN.
**CLOSED, confirmed.**

## §5 — §SAT (#133): **THE BLOCKING GAP** — the satisfiability receipt was produced by NOBODY
This is the sole basis for NO-GO.

**The receipt does not exist, and the report says it does.** REPORT-contract-04b5-5's `## §SAT`
(lines 108-109) is a literal unfilled placeholder:
```
## §SAT — SATISFIABILITY RECEIPT (#133) — [FILLED FROM refbuild-04b5-5 + my independent re-run]
<!-- FILLED after refbuild-04b5-5's reference build + my own scratch re-run -->
```
yet the same report asserts it IS filled in **four** places: the capability check ("for the MANDATORY
§SAT receipt, a THROWAWAY reference build in a scratch_copy.sh-verified scratch tree", :10), the
summary ("§SAT satisfiability receipt is FILLED (§SAT)", :25-26), the receipt pointers (:43), and the
residual table ("§SAT filled", :138). REPORT-contract-04b5-**3**'s §SAT is ALSO an unfilled
placeholder ("_finalized from refbuild-04b5-1's scratch reference build_"). **No `refbuild-04b5-*`
report exists anywhere** (`find` + `git log --all`: only an unrelated packet04b2 one). So across two
contract-build reports, the #133 satisfiability proof — *"prove the contract goes 0-failed against a
known-correct build, before any builder sees it"* — was **never produced**, and the completion report
misrepresents this. This is precisely #133's own hazard ("20 pins RED on a correct build shipped
inside an otherwise-strong contract") plus a served-prose/measured-behaviour lie.

**What I did about it — a SCOPED reference build (measured, provenanced).** Because §SAT is not merely
incomplete but ABSENT, I established the core satisfiability myself in a `scratch_copy.sh` tree
(provenance receipt: `loremaster.__file__ = /tmp/rc04b5scratch1/loremaster/loremaster/__init__.py`;
`coverage 7.15.3` resolved). I built the seam and routed the 2 highest-risk (D1) renders
(§INSTRUMENTS-D, the 4 edits transcribed):
- extracted `sanitise.fence_width`; `render_fenced` routed through it; added `render.render_attributed`
  (sanitise_line → inline delimiter of `fence_width` → `Rendered`);
- routed `_render_transitive_blockers` (residue list) + `_render_supersede_result`
  (task_id/successor_id/dependents) through `render_attributed`.

Measured result in scratch:
```
seam pins + the 2 routed renders' P-N + P-S            => 18 passed  (P-S GREEN AFTER routing)
FULL test_link5                                        => 39 failed, 114 passed   (was 53F/100P)
test_render_seam_pins (mint-pin accepts render_attributed) => 27 passed  (no regression)
```
This MEASURES the design's load-bearing satisfiability claim: **routing a door through
`render_attributed` is a leaf substitution that keeps P-S GREEN** (adds no un-covered branch), the
seam builds cleanly to its pins, the mint-pin admits `render_attributed` in render.py, and **no
currently-green pin regressed** — the remaining 39 REDs are EXACTLY the un-routed renders' P-N (25) +
the subset net (13) + the error scan (1), i.e. the same mechanical pattern I did not build.

**What this does and does NOT establish.** It establishes that the contract is **not a trap** on the
risky axis (P-S invariance, seam buildability, seam-suite survival) — satisfiability-in-fact is HIGH
confidence. It does **not** discharge #133: I did not reach 0-failed (I built 2 of ~40 renders and 0
of 49 error sites), and the `render_line`-widening handoff (routing a `Rendered` through
`render_line`, which today rejects non-`SafeLine` at `render.py:211`) is an un-exercised structural
change a full §SAT build would have proven. **So the fix: produce a genuine reference build to
0-failed across test_link5 + the fence rework + the pre-existing seam suites, paste counts +
`loremaster.__file__`, and CORRECT the four false "filled" claims. My scoped build is the verified
head start.**

## §6 — PRESERVE — all intact (GREEN + non-vacuous at HEAD)
Targeted run (21 passed): **P-U** method-reach (`TestEveryRenderCandidateIsDrivenOrOut` + its
non-vacuity naming the non-prefix helper `_format_finding_ref`) · **P-C** OUT-set earned
(`TestTheRenderOutSetIsEarned`) · **R2/R4/R5** array-universe partition
(`TestTheDerivedPartitionHasNoDoor`) · **coherence** (`TestEveryServedCallerByteIsInExactlyOneNet` +
its positive control) · the predicate's own controls (`TestTheContainmentPredicateItselfDiscriminates`,
`TestThePositiveControlProvesTheSweepCanFail`). **D1 both doors** (`_render_transitive_blockers` /
`_render_supersede_result`) are DRIVEN with residue-present/absent + dependents-empty/present shapes,
LEAK at HEAD (feature-red), and I confirmed both go GREEN + branch-covered under routing (§5).
**Error-half scan** intact (49 doors, RED at HEAD, non-vacuity + positive control sound).
**code-RAG B-5 OUT**: `map` is `_RENDER_OUT["map"]=("code_rag",…)` with the residual stated
(`_sanitise_line` same-line-forgery-blind → attacker-controlled indexed content owned by the
#138/pkt-39 review). No regression anywhere.

## §7 — QUALITY
- **coverage.py posture — correct** (resolves cold-audit-04b5-5's D-P). `"coverage>=7"` is in
  `[dependency-groups]` (dev), nothing shipped imports it, and the pyproject comment (`:65-70`) now
  ACCURATELY states it ships in `/app/.venv` for the #139 conformance suite (baked exactly like
  pytest). The only residual imprecision is the PACKET DOC summary's bare "NOT an image dep" — the
  actual declaration + pyproject prose are accurate. LOW/info.
- **No tautology or false gate found** in the pins I exercised. The D-A tautology is fixed
  (verified §2). The fence-width name-honesty pin
  (`test_render_attributed_delimiter_has_the_fence_width_OUTPUT_shape`) correctly promises an OUTPUT
  SHAPE (not "not cloned"), delegating non-cloning to the mutation leg — its message matches its
  assertion (no P2 false gate).
- **D-U (LOW, carried from cold audit):** `_RENDER_DRIVERS` (`:600`) is a vestigial 12-entry parallel
  registry subset of `_render_probes()`; -5 FIXED its stale comment (it named the retired
  `TestEveryRenderSiteThatHandlesCallerTextIsDriven`) but the FOLD is a builder ONE-IMPLEMENTATION
  handoff. Not blocking.

## §R — RESIDUAL TABLE (read the WHOLE table, #105)
| # | severity | site | one-line |
|---|----------|------|----------|
| **G1** | **BLOCKING (NO-GO)** | `REPORT-contract-04b5-5.md §SAT` (:108) + no refbuild report exists | #133 satisfiability receipt NEVER produced (empty in -3 AND -5); report falsely claims "filled" 4× (:10/:25/:43/:138). Full 0-failed demonstrated by nobody. Fix: real reference build to 0-failed (my scoped build §5 is the head start) + correct the false claims. |
| G1-sub | info | `render.py:211` / handoff #3 | render_line rejects non-SafeLine; routing a `Rendered` through it needs a widening the full §SAT build would exercise. No seam-test pin appears to block it (not exhaustively verified — inside the un-built §SAT scope). |
| D-A | **CLOSED (discriminates)** | `entry()` :1428 / guard :2378 | Independent DOOR+SAFE literals; Finding.caller_hint→RED (my construction). Tautology gone. |
| D-B | **CLOSED (green + discriminates)** | `TestEveryDrivenRenderBranchIsExercised` | `_render_claim_result` claimed-only→RED naming un-run lines (my construction). P-S invariant under routing (measured §5). |
| D-B.2 | **BOUND (not exploitable)** | ternary arcs | Only 2 driven-render ternaries, both constant arms, no door bytes (my AST scan confirms author). |
| D-C | **CLOSED (discriminates)** | `TestTheBranchExemptSetIsEarned` | 3 abuse constructions redden (my construction). |
| P-U/P-C/COH/ERR/R2-4-5 | **PRESERVED** | §6 | Green + non-vacuous at HEAD; D1 both doors driven+routable. |
| D-P | LOW/info | packet doc "NOT an image dep" | pyproject prose accurate; only the doc summary is imprecise. |
| D-U | LOW | `_RENDER_DRIVERS` :600 | Vestigial subset registry; comment fixed by -5; fold is a builder handoff. |

## VERDICT: **NO-GO** → contract author.
The contract's LOGIC is verified SOUND and satisfiable-in-fact: D-A/D-B/D-C each discriminate by my
own independent construction, every preserve net is green + non-vacuous, the ternary bound is not
exploitable, the fence-unify is coherent, and I MEASURED the core satisfiability (P-S invariant under
routing; seam builds; seam suites survive; no green pin regresses). **The single blocker is that the
#133 §SAT satisfiability receipt was produced by NOBODY and the completion report falsely claims it is
filled** — a full 0-failed against a reference build has never been demonstrated, and my §5 exists to
catch exactly this. The remediation is NARROW (complete the reference build to 0-failed, fill §SAT
with real counts + provenance, correct the four false claims), and my scoped build is the head start —
not a redesign.

---

## §INSTRUMENTS — re-runnable, pasted verbatim per brief-base §1 (run at `f11fc67`, from `loremaster/`, `uv run python`)

### §INSTRUMENTS-A — D-A + D-C discrimination (independent targets: Finding, _render_comms_ack)
```python
# /tmp/recheck_04b5_discriminate.py — exit 0 == D-A + D-C discriminate. (D-B is in -B: the
# slicing-vs-replace subtlety means D-B must REPLACE the shapes fn, done separately.)
import sys
sys.path.insert(0, "tests")
import test_link5_render_containment as T
from pydantic.fields import FieldInfo
ok = True
def expect_red(fn, label):
    global ok
    try: fn(); print(f"  [FAIL] {label}: GREEN — guard did NOT fire"); ok = False
    except AssertionError as e: print(f"  [ok]   {label}: RED -> {str(e).splitlines()[0][:76]}")
def expect_green(fn, label):
    global ok
    try: fn(); print(f"  [ok]   {label}: GREEN")
    except AssertionError as e: print(f"  [FAIL] {label}: RED unexpected -> {str(e).splitlines()[0][:70]}"); ok = False
# D-A (target: Finding, not the author's Task) — drive the ACTUAL guard's loop over _manifest()
Finding = T._model("loremaster.findings", "Finding")
guard = T.TestTheFieldManifestCannotSilentlyMissAField().test_every_rendered_models_str_fields_are_classified
_ = T._manifest(); expect_green(guard, "D-A baseline")
Finding.model_fields["caller_hint"] = FieldInfo(annotation=str, default=""); Finding.model_rebuild(force=True)
expect_red(guard, "D-A Finding gains 'caller_hint'")
del Finding.model_fields["caller_hint"]; Finding.model_rebuild(force=True); expect_green(guard, "D-A restore")
# D-C — 3 abuse constructions
E = T.TestTheBranchExemptSetIsEarned()
expect_green(E.test_every_exempt_method_is_a_store_backed_instance_method, "D-C base store-backed")
saved = dict(T._BRANCH_COVERAGE_EXEMPT); methods = T._appcontext_methods(); driven = {p.method for p in T._probes()}
static_render = next((m for m in driven if (fn := methods.get(m)) and (not fn.args.args or fn.args.args[0].arg != "self")), None)
T._BRANCH_COVERAGE_EXEMPT[static_render] = ("bogus", "trig")
expect_red(E.test_every_exempt_method_is_a_store_backed_instance_method, f"D-C (a) static '{static_render}' parked")
T._BRANCH_COVERAGE_EXEMPT.clear(); T._BRANCH_COVERAGE_EXEMPT.update(saved)
T._BRANCH_COVERAGE_EXEMPT["_render_a_method_that_does_not_exist"] = ("store", "trig")
expect_red(E.test_every_exempt_method_is_a_driven_probe, "D-C (b) stale entry")
T._BRANCH_COVERAGE_EXEMPT.clear(); T._BRANCH_COVERAGE_EXEMPT.update(saved)
k = next(iter(saved)); T._BRANCH_COVERAGE_EXEMPT[k] = (saved[k][0], "   ")
expect_red(E.test_every_exempt_entry_carries_a_re_open_trigger, "D-C (c) empty trigger")
T._BRANCH_COVERAGE_EXEMPT.clear(); T._BRANCH_COVERAGE_EXEMPT.update(saved)
sys.exit(0 if ok else 1)
# MEASURED @f11fc67: D-A field-add -> RED; D-C all 3 abuse -> RED; every baseline GREEN.
```

### §INSTRUMENTS-B — D-B discrimination (CORRECT methodology: REPLACE shapes; target _render_claim_result)
```python
import sys
sys.path.insert(0, "tests")
import test_link5_render_containment as T
from loremaster.tasks import ClaimResult, Task
branch = T.TestEveryDrivenRenderBranchIsExercised().test_no_driven_render_has_an_unexercised_branch
orig = list(T._probes())
def install(p): T._RENDER_PROBES = p; T._OVER_DRIVE_COVERAGE = None
install(list(orig))
try: branch(); print("baseline GREEN")
except AssertionError: print("baseline RED (unexpected)")
def claimed_true_only(g):
    return [T._served("_render_claim_result",
        ClaimResult.model_construct(claimed=True, task=T._forge(Task, forge=g), superseded_blockers={}))]
install([T.RenderProbe(method=p.method, shapes=claimed_true_only) if p.method == "_render_claim_result"
         else p for p in orig])
try: branch(); print("DROPPED: GREEN — NON-DISCRIMINATING")
except AssertionError as e:
    print("DROPPED: RED (P-S fires) ->", [l.strip()[:90] for l in str(e).splitlines() if "_render_claim_result" in l])
install(list(orig)); T._RENDER_PROBES = None; T._OVER_DRIVE_COVERAGE = None
# MEASURED @f11fc67: baseline GREEN; claimed=True-only -> RED naming _render_claim_result un-run lines
# [3644,3645,3649,3650,3651,3657,3661,3666,3667,3669,...]. NB: slicing shapes(g)[0] does NOT drop
# execution (all shapes run eagerly); you MUST replace the shapes fn.
```

### §INSTRUMENTS-C — ternary-arm bound (examine ARM values, not the condition)
```python
import ast, sys
sys.path.insert(0, "tests")
import test_link5_render_containment as T
methods = T._appcontext_methods(); driven = {p.method for p in T._probes()}
door_fields = set()
for _m, (door, _s) in T._manifest().items(): door_fields |= set(door)
def names(n):
    o = set()
    for s in ast.walk(n):
        if isinstance(s, ast.Attribute): o.add(s.attr)
        elif isinstance(s, ast.Name): o.add(s.id)
    return o
exploitable = False
for name in sorted(driven):
    fn = methods.get(name)
    if fn is None: continue
    launder = {a.targets[0].id for a in ast.walk(fn)
               if isinstance(a, ast.Assign) and len(a.targets) == 1 and isinstance(a.targets[0], ast.Name)
               and names(a.value) & door_fields}
    for node in ast.walk(fn):
        if isinstance(node, ast.JoinedStr):
            for val in node.values:
                if isinstance(val, ast.FormattedValue) and isinstance(val.value, ast.IfExp):
                    ifx = val.value; arm_refs = names(ifx.body) | names(ifx.orelse)
                    door_arm = (arm_refs & door_fields) | (arm_refs & launder)
                    print(f"{name}:{val.lineno} arms=({ast.unparse(ifx.body)!r},{ast.unparse(ifx.orelse)!r}) door_in_ARM={sorted(door_arm)}")
                    if door_arm: exploitable = True
print("EXPLOITABLE:", exploitable)
# MEASURED @f11fc67: 2 ternaries, both ('y','ies') constants, door_in_ARM=[] -> EXPLOITABLE False.
```

### §INSTRUMENTS-D — the SCOPED reference build (4 edits; scratch `/tmp/rc04b5scratch1`, provenance-verified)
```python
# sanitise.py — after max_backtick_run:
def fence_width(text: str) -> int:
    return max(MIN_FENCE_WIDTH, max_backtick_run(text) + 1)
# render.py — import fence_width, sanitise_line; render_fenced: `fence = FENCE_CHAR * fence_width(body)`; add:
def render_attributed(value: str) -> Rendered:
    safe = sanitise_line(value)
    delimiter = FENCE_CHAR * fence_width(safe)
    return Rendered(f"{delimiter}{safe}{delimiter}")
# server.py — import render_attributed; route the 2 D1 renders:
#   _render_transitive_blockers residue line: [str(render_attributed(blocker)) for blocker in residue]
#   _render_supersede_result: render_attributed(task_id/successor_id) + [str(render_attributed(d)) for d in dependents]
# MEASURED @scratch (loremaster.__file__=/tmp/rc04b5scratch1/...; coverage 7.15.3):
#   seam+routed-P-N+P-S => 18 passed (P-S GREEN after routing);
#   FULL test_link5 => 39 failed, 114 passed (was 53F/100P); test_render_seam_pins => 27 passed (no regression).
```
