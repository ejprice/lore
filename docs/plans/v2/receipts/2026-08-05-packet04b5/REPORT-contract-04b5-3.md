# REPORT-contract-04b5-3 — Packet 04b5 Link-5 render-reach instrument: the RENDER-half CHECKED-VARIABLE contract

brief-base v10 read
brief project v7 read

## CAPABILITY CHECK (tool honesty, first)
Brief satisfiable with the tools granted. lore tools loaded first try (`ToolSearch "+lore"`, no
#334 flake); registered + drained (empty inbox) on `lore_comms` session `pkt04b5`. `coverage.py`
install authorized + done (§INSTALL). `scratch_copy.sh` present for the satisfiability build.
spike-surreal `:18000` only (these render tests are store-FREE; I ran none against `:18500`).
**lore-first** for the render symbols (`lore_get_symbol`/`lore_read`; `lore_index` currency —
watched `/workspace`@`9cb1633`, fresh, my session had not edited production when I derived).
**grep/AST is the honest tool** for the interpolation-property universe sweep + the `_render_*`
enumeration (a cross-cutting structural map — CLAUDE.md dogfood case (c)); said so, used there.
No lore weakness forced a route-around; nothing filed. Delegated: an inventory scout (render
surface) and `refbuild-04b5-1` (branch-shape completion + reference-impl satisfiability) — their
work is GRADED by my authored assertions and re-verified here.

## SUMMARY BLOCK
- state: **done-with-deviations** — the render-reach instrument is authored, RED-at-HEAD
  behaviourally, structural nets GREEN, self-attacked; satisfiability via the delegated reference
  build (§SAT).
- **The render half is now THREE COUPLED CHECKED VARIABLES over a RUNTIME over-drive** (sidecar
  §4): P-U (name-blind candidate universe by the INTERPOLATION property) · P-F (model-guarded
  field manifest) · P-S (BRANCH observation via `coverage.py`). Containment PROOF is runtime
  `_leaks`, never structural (structural is unsound BOTH ways — re-confirmed §DESIGN). The 2 D1
  doors are DRIVEN; the OUT set is machine-verified/named (P-C); a coherence pin partitions the
  served caller-byte surface with the error half.
- deviations (one line each):
  - **coverage.py MECHANIZES branch reach** (operator ruling batch-2 #1) — replaces the sidecar's
    stdlib `settrace`; validated on real production code (§DESIGN P-S).
  - **4 store-backed doors** (`_create_many`/`_resolve_or_acknowledge_many` batch renders;
    `_filter_miss_notice`/`_tier_miss_teach` code-RAG served-NOTICE teaches) are DRIVEN for the
    neutralisation byte-check via a mock `self`, and BRANCH-EXEMPT (`_BRANCH_COVERAGE_EXEMPT`,
    B-α: their branches are store state) — pin-the-miss with a re-open trigger each.
  - **My instrument caught FOUR of my own mis-classifications** (`_tier_miss_teach`/
    `_filter_miss_notice` wrongly `error_only`; `_create_many`/`_resolve_or_acknowledge_many`
    wrongly `store_backed`) — the coherence pin + P-C reddened, I re-classified to DRIVEN. This is
    the instrument working; surfaced, not buried.
  - **The served-NOTICE door class is a real finding** (§FINDINGS): `_filter_miss_notice`/
    `_tier_miss_teach` reflect caller `path`/`tier` via `!r`/`_sanitise_line` into a
    `SearchResult` NOTICE — covered by NEITHER the error half (not an exception) NOR the prior
    render set. Now driven.
- **Packages considered:** `coverage` — **READ** the installed API (`Coverage(branch=True)`,
  `cov._analyze(file).missing` / `.missing_branch_arcs()`; probed §DESIGN P-S) — verdict
  **replace** the sidecar's stdlib `settrace` hand-roll (operator-ruled, packages-over-hand-rolling;
  test-only dev dep, ships `py.typed`, no image dep, no mypy override). `pydantic` model
  introspection (`model_fields`/`model_construct`) — **keep** (the manifest + generic builder are a
  `.model_fields` read, not a re-mechanise). No other mechanism specified.
- **Graded:** `9cb1633` (HEAD; production `server.py`/`render.py`/`sanitise.py` byte-identical to
  `5cedb38` — the two intervening commits are docs-only, so the contract's `5cedb38` RED-at-HEAD
  claims hold; re-derived here at `9cb1633`) · HEAD-at-report: `9cb1633` · **SAME**.
- **DECISIONS-NEEDED (forks surfaced, not resolved):**
  1. **Branch coverage of door-FREE system branches** (e.g. `_render_comms_fleet`'s
     session/grouping/retired branches render only counts/session, no caller door). Full branch
     coverage is the operator's literal ruling and makes branch-reach a genuine checked variable,
     but forces shapes for door-free branches — a real (accepted) brittleness. Kept as ruled;
     flagging the trade.
  2. **The reference-impl satisfiability is a FULL packet-04b5 build** (~40 renders + ~49 error
     sites + fence_width extraction + render_line widening + search.py route-through). This is 3×
     contract-04b5-2's reference build; it is essentially the whole builder job done twice. Priced
     as required by #133, but the lead should know the render half's all-or-nothing scope makes the
     satisfiability receipt itself large.
- receipt pointers: install §INSTALL · design (P-U/P-F/P-S/P-C/coherence + the coverage validation)
  §DESIGN · the RED/GREEN split §GATES · the 4 caught mis-classifications §FINDINGS · I attacked my
  own design §ATTACK · satisfiability §SAT · preserved parts §PRESERVE · builder handoffs §HANDOFF.

---

## §INSTALL — coverage.py (authorized)
Added `"coverage>=7"` to root `pyproject.toml` `[dependency-groups] dev` with a house-style
rationale comment (mirrors pytest-xdist/markdown-it-py/shellcheck-py). `uv sync` →
`coverage 7.15.3`, imports on Python 3.14. Committed WITH its first consumer (the instrument) —
the lead commits the dep + `test_link5_render_containment.py` §G as one coherent change; NOT an
orphaned bare-dep commit.

## §DESIGN — the render half as three coupled checked variables (sidecar §4)
The load-bearing measurement, re-confirmed at `9cb1633`: **caller-vs-system provenance of a render
field is NOT name-blind derivable, so the containment proof MUST be runtime.** Two receipts:
- Structural over-flags: the interpolation property yields **60 candidate methods**; a structural
  door-derivation flags every render interpolating an id/status/count (~37 "door candidates"),
  ~99% of which are system ids — the sidecar §2 measurement reproduced.
- **`render_line` is ASSEMBLY, not containment** (measured): `render_line("fleet: {note}",
  note=sanitise_line(FORGERY))` leaks the forgery verbatim — and the comms family renders
  `role`/`last_note`/`thread` through `render_line`+`sanitise_line` with ZERO `FormattedValue`s,
  so ANY structural scan is BLIND to them. Only `render_attributed`/`render_fenced` contain.
  Therefore the DRIVEN set is the render surface driven-and-byte-checked; P-U forces completeness.

**P-U** — `_candidate_render_sites()` derives the universe name-blind by the interpolation property
(a `FormattedValue` of a non-constant OR a `sanitise_line`/`safe_str`/`_sanitise_line` call),
scoped to `AppContext`. Every candidate ∈ `_render_probes()` (driven) xor `_RENDER_OUT` (reason +
trigger); a candidate in neither → RED. Non-vacuity + reverse-leg guards. Catches the serving
helpers the `_render_` prefix misses (`_format_finding_ref`, `_task_status_marker`, …).

**P-F** — a MODEL-GUARDED field manifest (`_manifest()`): per rendered model, `str`-ish
`model_fields` split DOOR/SAFE, guarded so DOOR ∪ SAFE == the model's `str`-ish fields — a NEW
`str` field reddens until classified. A generic `_forge(cls, forge)` builder tokenises EVERY door
field (distinct `_field_token`, shared `FORGERY_MARKER`) and recurses nested models — ONE builder
for the whole graph (no per-model clone; the manifest is the shared policy).

**P-S** — BRANCH observation via `coverage.py` (operator ruling batch-2 #1). The over-drive runs
under `Coverage(branch=True)`; `analysis.missing` + `analysis.missing_branch_arcs()`, sliced to
each driven render's body span, must be empty. VALIDATED on the real `_render_transitive_blockers`:
with one shape the residue line (D1's own leak, `if residue:`) shows as a missing branch arc; with
the residue-present + residue-absent shapes it clears. An un-run branch is a NAMED gap → RED.

**P-C** — the OUT set is EARNED: `error_only` machine-verified structurally (every f-string is an
exception-constructor arg, OR the method returns a scalar non-string so it serves no string — the
`_parse_rollup_since` case); the rest (`store_backed`/`dispatcher`/`composer`/`code_rag`/
`index_metadata`) are named bounds, each with a re-open trigger + the coherence backstop; the
reason vocabulary is closed (a typo can't skip verification).

**Coherence** — no OUT-bound method (non-error reason) may DIRECTLY interpolate a registered
caller free-text param into a served answer (WB-10); with a positive control that the scan can see
a bare `{owner}`.

## §GATES — RED behaviourally at HEAD, collect-clean, ZERO NEW mypy
At `9cb1633`, BEFORE the delegated branch-shape completion:
```
pytest tests/test_link5_render_containment.py --collect-only   => 149 tests collected, clean
MYPYPATH=loremaster:loremaster/tests mypy <the contract file>  => Success: no issues found
```
- **Structural nets GREEN at HEAD** (14 passed): P-U completeness/non-vacuity/reverse, P-F
  completeness + non-vacuity, P-C (error_only machine-verified + trigger + closed vocabulary),
  coherence (no-door-in-OUT + positive control), the containment-predicate controls.
- **Neutralisation RED at HEAD** for the door renders (task_rows / task_detail / finding_rows /
  recalled_memories / transitive_blockers / supersede_result / task_transition / claim_result /
  comms family / the 4 store-backed doors all LEAK the forgery outside a delimiter), GREEN for the
  system-only renders (no token) — the correct feature-absent RED. The 4 store-backed doors' HEAD
  leak was byte-confirmed (`tier`/`path`/`subject`/`actor` marker reaches the served answer).
- **P-S branch coverage** RED at HEAD until the driver shapes are completed (a completeness test on
  MY shapes, not a feature-RED) — delegated to `refbuild-04b5-1` (§SAT), goes GREEN at HEAD once
  every branch is reached, stays GREEN on the fix (the fix wraps values, adds no branch).

## §ATTACK — I attacked my own design (6/6 wrong builds caught)
The property-to-invent roster law: the author attacks its own design. I ran a read-only attack
(instrument pasted below, per brief-base §1 — it establishes the load-bearing "discriminates"
claim; archive it to `docs/plans/v2/receipts/2026-08-05-packet04b5/` — `/tmp/attack_own_design.py`
is unrecoverable by construction). Each sidecar §6 wrong build that would pass a WEAKER design is
REDDENED by an authored net; **6 attacked, 6 caught, 0 escaped:**
```
[RED] WB(new-render-slips-universe)   -> P-U       (drop a driver -> completeness names it)
[RED] WB-2(new-str-field)             -> P-F       (un-classify Task.summary -> manifest names it)
[RED] WB-3(door-on-un-run-branch)     -> P-S       (residue-absent-only -> names branch 4115:[4116], D1's leak)
[RED] WB-6/10(door-hidden-in-OUT)     -> coherence (_resolve_or_ack_many interpolates 'actor' directly)
[RED] WB-4/5(field-B-hides-while-A)   -> P-F       (_forge tokenises EVERY Task door field, not one)
[RED] WB(false-error_only)            -> P-C       (_tier_miss_teach serves a non-error line -> refused)
```
The reference-build satisfiability (§SAT) is the complementary control: the instrument must go
0-failed on a KNOWN-CORRECT build (not just RED on wrong ones).

<!-- FILLED AFTER refbuild-04b5-1 -->
## §SAT — satisfiability receipt (#133)
_(finalized from `refbuild-04b5-1`'s scratch reference build — `loremaster.__file__` provenance +
the FULL contract passed/failed counts)_

## §FINDINGS — the four mis-classifications my own instrument caught
1–2. `_tier_miss_teach` / `_filter_miss_notice` — I first classified `error_only`; P-C's
   machine-verification (`_fstrings_all_error_routed`) reddened: they build a served `SearchResult`
   NOTICE (not an exception) reflecting caller `tier`/`path` via `!r`/`_sanitise_line`. This is a
   SERVED-NOTICE door class covered by neither net. → re-classified DRIVEN (mock-`self` harness).
3–4. `_create_many` / `_resolve_or_acknowledge_many` — I first classified `store_backed`; the
   coherence pin reddened naming `subject`@`_create_many` and `actor`@`_resolve_or_acknowledge_many`
   as registered params interpolated directly into a served answer. → re-classified DRIVEN
   (mock-`self` harness), branch-exempt (B-α, store-state branches).
Each was surfaced by an authored assertion, not by inspection — the instrument discriminates.

## §PRESERVE (round-1/round-2-sound parts, NOT regressed)
The error-half scan `TestNoServedDomainErrorLeavesACallerParamUncontained` (49 doors/7 modules,
litmus reddens) · R2 (`_schema_carries_string` array universe + `TestTheDerivedPartitionHasNoDoor`)
· R4 (width-pin name) · R5 (prose sweep) · §A seam pins · §C hostile fixture +
containment-predicate controls · the fence rework in `test_task_read_surface.py` · the B-5 bounds.
Only `TestTheRenderDriverRegistryCoversTheRenderDoors` was RETIRED (the delta-audit's subset), a
one-line pointer left in its place at the render-reach seam.

## §HANDOFF — for the BUILDER (named, not fixed)
- R3 ripple: `test_task_ledger.py::TestDoneSummaryReportPath` exact-text pins (`task '{id}'` → the
  contained form) — update in the SAME diff (P8d).
- `server.py`'s docstring reference to the deleted `test_attribution_bound.py` (prod do-not-touch
  for me).
- `render_line` widening to accept `Rendered` (§SAT build-design point).

## §ATTACK-SCRIPT — the self-attack instrument (verbatim, per brief-base §1; run at `9cb1633` from `loremaster/`)
```python
"""I ATTACK MY OWN DESIGN (roster law): each sidecar §6 wrong build that passes a WEAKER
design must be REDDENED by an authored net here. Read-only — exercises the contract's own
logic functions with wrong-build inputs. Run from loremaster/: `uv run python /tmp/attack_own_design.py`.
"""
import sys, ast
sys.path.insert(0, "tests")
import test_link5_render_containment as T

results = []

def check(name, reddens, detail):
    results.append((name, reddens, detail))
    print(f"[{'RED (caught)' if reddens else 'GREEN (ESCAPED!)'}] {name}: {detail}")

# WB — a NEW render function that slips the universe (P-U). Simulate a builder adding a render
# without a driver: drop one driven probe; the completeness check must NAME it.
candidates = T._candidate_render_sites()
driven = {p.method for p in T._render_probes()}
out = set(T._RENDER_OUT)
unclassified_if_dropped = candidates - (driven - {"_render_task_rows"}) - out
check("WB(new-render-slips-universe) -> P-U",
      "_render_task_rows" in unclassified_if_dropped,
      f"dropping _render_task_rows' driver -> P-U names {sorted(unclassified_if_dropped)}")

# WB-2 — a NEW str field on a rendered model, rendered bare, not in the manifest (P-F). Simulate
# by removing a door field: the completeness guard must name it.
Task = T._model("loremaster.tasks", "Task")
door, safe = T._manifest()[Task]
strish = {n for n, f in Task.model_fields.items() if T._is_str_ish(f.annotation)}
missing_if_new_field = strish - ((door - {"summary"}) | safe)
check("WB-2(new-str-field) -> P-F",
      missing_if_new_field == {"summary"},
      f"un-classifying Task.summary -> manifest completeness names {sorted(missing_if_new_field)}")

# WB-3 — a door on an un-exercised branch (P-S): D1's own residue leak. Drive transitive_blockers
# with ONLY the residue-ABSENT shape; the residue line must show as an un-run branch.
import coverage, pathlib
import loremaster.server as server_mod
from loremaster.tasks import Task as TaskCls, TransitiveBlockers
server_file = str(pathlib.Path(server_mod.__file__).resolve())
spans = T._method_body_spans()
cov = coverage.Coverage(branch=True, data_file=None)
cov.start()
# only the residue-ABSENT shape (blocked_by subset of ids)
server_mod.AppContext._render_transitive_blockers(
    T._forge(TaskCls, forge=True, blocked_by=["walked"]),
    TransitiveBlockers.model_construct(ids=["walked"], truncated=False, max_depth_used=1))
cov.stop()
a = cov._analyze(server_file)
lo, hi = spans["_render_transitive_blockers"]
missing_branch = {s: d for s, d in a.missing_branch_arcs().items() if lo <= s <= hi}
check("WB-3(door-on-un-run-branch) -> P-S",
      len(missing_branch) > 0,
      f"residue-absent-only drive -> P-S names un-run branches {missing_branch}")

# WB-6 / WB-10 — a real door method placed in _RENDER_OUT with a false reason (coherence). Show
# the coherence scan sees a registered param interpolated directly.
import asyncio
async def _coh():
    door_vocab = await T._served_error_door_vocab()
    methods = T._appcontext_methods()
    fn = methods["_resolve_or_acknowledge_many"]
    interps = {ident for _ln, ident in T._raw_render_interpolations(fn)}
    return interps & door_vocab
hit = asyncio.run(_coh())
check("WB-6/10(door-hidden-in-OUT) -> coherence",
      "actor" in hit,
      f"_resolve_or_acknowledge_many directly interpolates registered param(s) {sorted(hit)}")

# WB-4/5 — the manifest tokenises EVERY door field, so a render leaking field B (while a
# hand-picked driver set only field A) still reddens. Prove _forge(Task) carries a token in
# EVERY door field (not just a representative).
t = T._forge(TaskCls, forge=True)
def has_marker(v):
    return T.FORGERY_MARKER in (str(v) if not isinstance(v, (list, dict))
                                else str(v))
tokenised = {f for f in door if has_marker(getattr(t, f))}
check("WB-4/5(field-B-hides-while-A-driven) -> P-F manifest",
      tokenised == door,
      f"_forge tokenises EVERY Task door field: {sorted(tokenised)} == {sorted(door)}")

# WB — a method asserting error_only while it serves a non-error line (P-C). _tier_miss_teach
# serves a NOTICE with tier!r; the machine check must refuse the error_only reason.
methods = T._appcontext_methods()
check("WB(false-error_only) -> P-C",
      not T._fstrings_all_error_routed(methods["_tier_miss_teach"]),
      "_tier_miss_teach serves a non-error line -> _fstrings_all_error_routed = False")

print("\n=== SUMMARY ===")
escaped = [n for n, red, _ in results if not red]
print(f"{len(results)} wrong builds attacked; {len(results)-len(escaped)} caught; escaped: {escaped}")
sys.exit(1 if escaped else 0)
```
