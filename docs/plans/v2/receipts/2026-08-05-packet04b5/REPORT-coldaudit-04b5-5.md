# REPORT-coldaudit-04b5-5 — DELTA cold audit of the RENDER-REACH instrument (packet 04b5, 3rd contract build)

brief-base v10 read
brief project v7 read

## CAPABILITY CHECK (tool honesty, first)
Brief satisfiable with the tools granted. lore tools loaded first try (`ToolSearch "+lore"`, no
#334 flake); registered + drained (empty inbox) on `lore_comms` session `pkt04b5`. I EDIT nothing
(read-only delta-audit; this report is my only writable artifact). I **ran the full contract at
HEAD `-n auto`**, **CONSTRUCTED the P-F defect with a live introspection probe** (pasted §APPENDIX,
per brief-base §1), ran the P-S branch net in isolation, and spot-read production spans. lore-first
for the render symbols; **grep/AST is the honest tool** for the interpolation-universe + `_render_*`
sweeps + the un-run-branch characterisation (cross-cutting structural maps — CLAUDE.md dogfood case
(c)) — used there, said so. My probe is a read-only AST/pydantic-introspection run against the real
tree (`loremaster.__file__` in-tree, no store, no mutation) — no scratch copy / provenance receipt
owed (I built no reference impl; the #133 satisfiability rebuild is assessed, not re-run — said
which, §6). Tests would hit spike-surreal `:18000` only; I ran none against `:18500`. No lore
weakness forced a route-around; nothing filed.

## SUMMARY BLOCK
- state: **done** — delta-verdict rendered.
- **VERDICT: INSUFFICIENT** → back to the contract author. **D1 is genuinely CLOSED** (both
  byte-proven doors now DRIVEN + RED at HEAD + branch-covered) and **P-U method-reach is CLOSED**
  (name-blind by interpolation property). But **TWO of the three coupled checked variables fail**:
  (D-A) **P-F field-reach is a TAUTOLOGY that cannot fire** — `SAFE := strish − door` (line 1429)
  makes `missing = strish − (door∪safe)` structurally always empty, so a NEW caller-free-text field
  is silently absorbed into SAFE, untokenised, undetected (CONSTRUCTED §1); (D-B) **P-S branch-reach
  is RED-at-HEAD and unsatisfiable as authored** — ~12 store-free driven renders have dozens of
  un-run door-free branches the shapes never reach, and P-S is fix-independent (it drives the real
  renders, not `render_attributed`), so a production build CANNOT green it; the **#133 satisfiability
  receipt (§SAT) is EMPTY** (§2). Either alone blocks; together they say render field-reach and
  branch-reach are not yet checked variables — the D2 root, one granularity down.
- deviations: I did NOT rebuild the full §SAT reference build (the render half is a ~40-render +
  ~49-error-site build); satisfiability is assessed by the P-S mechanism + the HEAD run, which is
  DECISIVE without a rebuild (P-S's un-run set is invariant under any value-wrapping fix — §2) —
  said which, per the brief.
- **Packages considered:** none — no mechanism specified (audit). The contract's `coverage.py`
  posture is a finding, not a mechanism I chose (§7: it is dev-group AND baked into the image venv
  for #139 conformance — the "NOT an image dep" prose is imprecise).
- **Graded:** `9cb1633` (HEAD; the tree the contract was authored against — production
  `server.py`/`render.py`/`sanitise.py` byte-identical to `5cedb38`) · HEAD-at-report: `9cb1633` ·
  **SAME**. Every "RED at HEAD" claim re-derived here at `9cb1633`.
- **DECISIONS-NEEDED (surfaced, not resolved):**
  1. **P-F must be an INDEPENDENT DOOR+SAFE hand-list (the sidecar §4 P-F.2 design), not
     DOOR + auto-complement.** The fix is small (make `_manifest()` carry both sets, assert their
     union == `strish`) but it is a CONTRACT change — route to the author.
  2. **P-S needs its shapes COMPLETED (they are store-free-completable) + a filled §SAT receipt**
     before the adversary sees it. Full branch coverage of door-FREE system branches is the
     operator's literal ruling (batch-2 #1) — the author flagged the brittleness (their
     decision-needed #1) but did not write the shapes.
  3. `_BRANCH_COVERAGE_EXEMPT` is a SILENT hand-list (§3) — should be earned like `_RENDER_OUT`.
- receipt pointers: P-F tautology §1 (+probe §APPENDIX) · P-S unsatisfiable §2 · exempt-set hole §3 ·
  served-notice door CLOSED §4 · coherence/B-5 sound §5 · satisfiability §6 · regression/counts §7 ·
  minor §8 · residual table §R (read the WHOLE table, #105).

---

## §1 — D-A: P-F FIELD-REACH IS A TAUTOLOGY THAT CANNOT FIRE (CONSTRUCTED) → INSUFFICIENT

**The design's intent** (sidecar §4 P-F.2; packet ruling P-F; the contract's own docstring at
`test_link5:2145-2149`): DOOR and SAFE are **independent hand-lists**, so a NEW `str` field on a
rendered model is in NEITHER → `DOOR ∪ SAFE ≠ strish` → RED, "the manifest cannot silently go stale."

**What was built instead** — `entry()` (`test_link5:1425-1429`):
```python
def entry(cls, door):
    strish = {n for n, f in cls.model_fields.items() if _is_str_ish(f.annotation)}
    return cls, (frozenset(door), frozenset(strish - door))   # SAFE := the LIVE COMPLEMENT of door
```
SAFE is not an independent list — it is `strish − door`, recomputed from the SAME `model_fields`
the completeness test reads. So `DOOR ∪ SAFE = door ∪ (strish − door) = strish ∪ door ⊇ strish`, and
`test_every_rendered_models_str_fields_are_classified`'s
`missing = strish − (door ∪ safe)` is **unconditionally empty for every model, regardless of which
fields exist.** The only live leg is `extra = (door∪safe) − strish` (catches a typo'd door name).
The "new field reddens" property — one of the three D2 checked variables — is **dead**.

**CONSTRUCTED, not reasoned** (probe §APPENDIX, run at `9cb1633`):
```
=== structural tautology check (over the REAL manifest, every model) ===
  For EVERY manifest model, DOOR|SAFE == strish exactly: True
  => the test's `missing = strish - (door|safe)` is STRUCTURALLY always empty.
=== faithful NEW-FIELD simulation (Task gains caller-free-text `tags`) ===
  'tags' present in strish?           True
  'tags' in DOOR hand-list?           False
  'tags' absorbed into SAFE(complement)? True
  missing (what the P-F test FLAGS):  []
  => P-F test verdict on the new door field: GREEN (ESCAPED)
  _forge sets tags = 'release-bot' (marker present? False) => untokenised ...
```
The simulation subclasses `Task` with a NEW caller-free-text `str` field `tags`, replicates
`entry()`'s exact `safe = strish − door` computation, and the P-F completeness test stays **GREEN**.
`_forge` then leaves `tags` at the benign default (untokenised), so `TestEveryDrivenRenderNeutralises­EveryForgery` stays green too — the leak is invisible end-to-end. **This is the design's own WB-2,
escaping.**

**Why the author's §ATTACK missed it.** The self-attack (contract report §ATTACK-SCRIPT WB-2) removes
`summary` from `door` while holding `safe` FROZEN at its original value (which excluded `summary`),
so `(door − {summary}) ∪ safe` omits `summary` and `missing == {summary}` → "RED". But a REAL new
field is NOT a removal-from-door; it flows INTO the live `safe` complement. The attack modelled a
world that cannot occur and reported a green it would never see in practice — the exact "a probe
needs a control / what WRONG build survives this?" failure the packet law names. **The instrument
does not discriminate the wrong build it claims to.**

**Severity:** BLOCKING. Field-reach is one of the three coupled checked variables the design pins as
the D2 fix; a checked variable that cannot fail is decoration (`CLAUDE.md`: "a fixture that cannot
distinguish the correct build from a plausible wrong one is decoration"), and the docstring promises
a check the assertion does not perform (the P2 false-gate law). **Fix:** carry an independent
`_SAFE_FIELDS[M]` hand-list (each entry with its reason, per design P-F.1) and assert
`DOOR ∪ SAFE == strish` where BOTH are literals — then a new field is in neither and reddens.

---

## §2 — D-B: P-S BRANCH-REACH IS RED-AT-HEAD AND UNSATISFIABLE AS AUTHORED; §SAT EMPTY → INSUFFICIENT

`TestEveryDrivenRenderBranchIsExercised::test_no_driven_render_has_an_unexercised_branch` is **RED at
HEAD `9cb1633`** naming un-run branches on **12 non-exempt driven renders** (measured, verbatim tail):
```
_comms_footer, _comms_foreign_param_error, _render_claim_result, _render_comms_ack,
_render_comms_brief_coverage_line, _render_comms_brief_publish, _render_comms_drain,
_render_comms_drain_row, _render_comms_fleet (25 un-run lines), _render_comms_send,
_render_comms_skew_breakdown, _render_comms_skew_lines
```
**This is NOT a feature-absent RED** (the other 52 REDs are — `render_attributed`/`fence_width`
absent). P-S drives the REAL renders under `coverage.Coverage(branch=True)` and asserts every branch
executed; it **never touches `render_attributed`**, so its verdict is INDEPENDENT of the fix. The
un-run branches are a pure function of `(probe shapes) × (current server.py structure)`. **The fix
wraps leaf values inside existing branches — it adds no branch and no probe shape — so the un-run set
is INVARIANT under any correct build. P-S stays RED on the fix.** Spot-confirmed concretely:
`_render_comms_skew_lines:6309-6322` (un-run) is the `if over > 0 / else` "+N more briefs" leg — a
**door-free, store-free** branch reachable only by a probe shape with `> _COVERAGE_NAMES_CAP`
remainder briefs; the current shapes (`test_link5:1778-1782`) pass ≤2 skew entries and never enter
`if remainder:`. The fix cannot reach it; only an added test SHAPE can.

The contract author KNEW: §GATES says P-S is "RED at HEAD until the driver shapes are completed …
delegated to `refbuild-04b5-1` … goes GREEN once every branch is reached", and decision-needed #1
flags full branch coverage of door-free branches as "a real (accepted) brittleness. Kept as ruled."
**But the shapes on disk are incomplete and the delegated completion never landed:** the **§SAT
satisfiability receipt is an EMPTY placeholder** (`test_link5`… the report's `## §SAT` reads
`<!-- FILLED AFTER refbuild-04b5-1 -->` / `_(finalized from refbuild-04b5-1's scratch reference
build)_`). So the #133 rule — *"a contract ships with a satisfiability receipt: prove it goes
0-failed against a known-correct build"* — is **unmet**, and my analysis says a value-wrapping build
would NOT reach 0-failed (P-S persists). The builder would be trapped between a green feature and a
red P-S it cannot fix by writing production code.

**Severity:** BLOCKING, but the remediation is cheap and mechanical: these renders are store-FREE
(they are non-exempt driven probes, i.e. the author already asserts they are drivable store-free), so
the missing shapes are just additional `_probes()` entries reaching each branch. Complete them, run
the full contract to 0-failed against a reference `render_attributed`, and PASTE the §SAT counts +
`loremaster.__file__` provenance. Until then the contract is not satisfiable-as-authored.

---

## §3 — `_BRANCH_COVERAGE_EXEMPT` IS A SILENT HAND-LIST (item 3) — legitimate bound, UNDER-INSTRUMENTED

The 4 store-backed doors (`_create_many`, `_resolve_or_acknowledge_many`, `_filter_miss_notice`,
`_tier_miss_teach`) are DRIVEN for the neutralisation byte-check (all 4 leak at HEAD → RED, §4) and
EXEMPT from P-S branch coverage with the reason "branches are store state (B-α)". The **bound is
legitimate in principle** — which batch item succeeds/fails/aborts, which filter arm fires, is store
state you cannot drive store-free. **But the exemption is a raw `dict` used at exactly ONE site — the
skip at `test_link5:2125` — with no guarding test at all** (grep: `_BRANCH_COVERAGE_EXEMPT` appears
only at its definition `:1860` and the skip `:2125`). Compare `_RENDER_OUT`, which earns each entry
three ways (`TestTheRenderOutSetIsEarned`: machine-verified `error_only`, non-empty re-open-trigger,
closed reason vocabulary). The exempt set has **none of the three**:
- no machine-check that an exempt method IS store-backed (an async instance method that reads the
  store) — a future author could park a store-FREE render here and silently drop it from branch
  coverage;
- no test that each reason carries a non-empty re-open trigger (the packet-03b rider law — "a
  trigger nobody measures is a hope"; the triggers live only in a comment at `:1858`);
- no non-stale guard that every exempt key is a real driven probe.

**Could an attacker-reachable door hide in an exempt branch?** Yes, in principle: a batch render's
error/abort branch that renders `subject`/`actor` differently from its success line is neither
branch-covered (exempt) nor caught by the coherence pin (these are DRIVEN, not OUT, so
`test_no_out_bound_directly_renders_a_registered_param` skips them). The success-line door IS
byte-checked; a divergent un-driven branch is not. **This is a real (secondary) hole** — not
byte-proven reachable today, but the instrument does not close it and does not pin it as a bound with
the rigor `_RENDER_OUT` gets. Recommend: give `_BRANCH_COVERAGE_EXEMPT` the same P-C treatment
(machine-verify store-backed, enforce trigger, closed reason, subset-of-driven guard).

---

## §4 — THE SERVED-NOTICE DOOR CLASS (item 4): REAL AND CORRECTLY DRIVEN — CLOSED

`_filter_miss_notice` / `_tier_miss_teach` reflect a caller `path`/`tier` via `!r`/`_sanitise_line`
into a `SearchResult` **NOTICE** (neither an exception — so the ERROR-half AST scan is blind to it —
nor a prior render-set member). This is a genuine new door class the author's own instrument caught
(their §FINDINGS 1-2), and it is now DRIVEN: all four store-backed doors (`_tier_miss_teach`,
`_filter_miss_notice`, `_create_many`, `_resolve_or_acknowledge_many`) appear in the 26
`test_no_shape_leaks_the_forgery` failures at HEAD (measured), i.e. they LEAK the forgery today and
are correctly RED. The neutralisation coverage of this class is sound (the branch-exemption caveat is
§3, separate). CLOSED.

---

## §5 — COHERENCE + CODE-RAG B-5 (item 5): SOUND

- **Coherence** (`TestEveryServedCallerByteIsInExactlyOneNet`): `test_no_out_bound_directly_renders_a_registered_param` scans every non-error OUT method for a direct registered-param interpolation, with
  a working positive control (`test_the_coherence_backstop_can_actually_see_a_param`, synthetic
  `{owner}` surfaces). GREEN at HEAD (no OUT bound hides a direct door). The partition is sound for
  the DIRECT-param case; laundered locals are the explicitly-named B-γ bound. No gap.
- **code-RAG file renders B-5 OUT**: `map` is `_RENDER_OUT["map"] = ("code_rag", …)`, and the
  `code_rag` reason's docstring (`test_link5:1895-1899`) states the residual explicitly —
  `_sanitise_line` is same-line-forgery-blind, so attacker-controlled indexed content is a LIVE
  surface **owned by the #138 / packet-39 threat-model review, met deliberately not silently**
  (operator ruling batch-2 #2). Correctly rendered OUT with residual stated + pkt39 flag. Sound.
  ⚠ Minor: only `map` is listed OUT; `diff.py`/`impact.py` file renders (scout §3 / sidecar §3) are
  in OTHER modules, so they are outside the `server.py`-AppContext P-U universe by construction (the
  B-β module bound) rather than being an explicit `_RENDER_OUT` entry — consistent with the design's
  scoping, not a defect, but the coherence story rests on the B-β bound for those two, not on an OUT
  pin.

---

## §6 — SATISFIABILITY (#133, item 6): RECEIPT MISSING; contract NOT satisfiable as authored
The `## §SAT` section of `REPORT-contract-04b5-3.md` is an unfilled placeholder — no
`loremaster.__file__` provenance, no passed/failed counts, no confirmation the pre-existing seam
suites (`test_render_seam_pins`, the injection registries, the fence invariant) still pass on the
reference build. I did NOT rebuild the full reference (deviation) because the P-S mechanism (§2) is
**decisive without it**: P-S is fix-independent and RED at HEAD, so a value-wrapping reference build
cannot reach 0-failed. The contract therefore fails the #133 gate on two counts — the receipt is
absent AND the contract is provably not 0-failable as authored (P-S), before even reaching P-F. This
is the blocking half of D-B.

## §7 — REGRESSION / COUNTS (item 7; full contract at HEAD `9cb1633`)
```
uv run pytest loremaster/tests/test_link5_render_containment.py -n auto  => 53 failed, 96 passed (149 collected)
```
Failure breakdown (by class): 26 `TestEveryDrivenRenderNeutralisesEveryForgery` (P-N door leaks) ·
13 `TestEveryRenderLayerDoorNeutralisesAForgery` (old registry + served_error) · 7
`TestFenceWidthIsTheONEExtractedWidthPolicy` · 4 `TestRenderAttributedIsTheInlineContainmentSeam` ·
1 `TestNoServedDomainErrorLeavesACallerParamUncontained` (error scan, 49 doors) · 1
`TestTheLink5BoundsArePinned…::test_older_schema_rows…` · **1
`TestEveryDrivenRenderBranchIsExercised::test_no_driven_render_has_an_unexercised_branch` (P-S — the
NON-feature-RED, §2).** So **52/53 are feature-absent RED** (green on the fix); **1 is the P-S
shape-incompleteness RED a production fix cannot clear.**
- **ERROR half PRESERVED** — the AST site scan is still the derived, non-vacuous, positive-controlled
  net (cold-audit-04b5-4 §3 confirmed it sound); RED at HEAD for the caller-param doors; the
  seven-base drift guard intact. Not regressed.
- **R2/R4/R5 PRESERVED** — the array-universe partition (`_schema_carries_string` + `TestTheDerived­PartitionHasNoDoor`) passes structurally at HEAD; R4 name honesty intact; R5 prose sweep intact.
- **P-U method-reach CLOSED** — `_candidate_render_sites()` derives name-blind by the interpolation
  property; `test_the_universe_is_non_vacuous_and_names_known_members` asserts the non-prefix serving
  helpers (`_format_finding_ref`) are IN the universe and PASSES, so a NEW render with a bare
  caller-byte door (prefix or not) reddens `test_every_candidate_is_driven_or_out`. This is the D2
  method-reach fix and it is sound.
- **D1 CLOSED** — `_render_transitive_blockers` and `_render_supersede_result` are DRIVEN
  (`_probes()` `:1704-1718`, residue-present + residue-absent / dependents-empty + dependents-present
  shapes), LEAK at HEAD (both in the 26 P-N failures), and are ABSENT from the P-S un-run list → their
  residue/dependent branches ARE exercised. The byte-proven cold-audit-04b5-4 leak is neutralised on
  the fix and its branch is a checked variable. Good work.
- **coverage.py**: `"coverage>=7"` is in `[dependency-groups] dev` (dev-only ✓; nothing shipped
  imports it ✓; `py.typed`, no mypy override ✓). ⚠ **Prose-accuracy flag**: the pyproject comment +
  packet ruling say "**NOT an image dependency**", but `Containerfile:87` runs `uv sync --locked
  --all-packages` which installs the dev group into `/app/.venv` **deliberately** (`Containerfile:74`,
  for the #139/packet-01a in-image conformance suite — which must run `test_link5` and therefore NEEDS
  coverage in-image). So coverage physically SHIPS in the image venv. The claim is true under
  "nothing shipped imports it" and the baking is arguably correct (conformance needs it), but the bare
  words "not an image dep" are imprecise — a served-prose/measured-behaviour mismatch, the class this
  packet exists to catch. Not blocking; flagging per scope law.
- **zero-new-mypy**: `MYPYPATH=loremaster:loremaster/tests mypy test_link5_render_containment.py` →
  `Success: no issues found`. (Scoped to the contract file, as the author did; full-member typecheck
  not re-run — deviation, consistent with cold-audit-04b5-4.)

## §8 — MINOR (surfaced, not blocking)
- **`_RENDER_DRIVERS` (`:605`) is now a vestigial parallel registry.** It is a 12-entry
  `{method: (label, driver)}` map consumed ONLY by `TestEveryRenderLayerDoorNeutralisesAForgery`
  (`:624`), duplicating 12 of the neutralisation checks `_render_probes()` already performs. Its
  comment (`:601-604`) references the **RETIRED** test `TestEveryRenderSiteThatHandlesCallerTextIsDriven`
  (grep: no such class exists). Two driver registries for one purpose + a stale comment naming a dead
  test — a ONE-IMPLEMENTATION smell and a rename-sweep residual (the exact "prose teaching a retired
  name" class). Recommend folding `_RENDER_DRIVERS` into `_render_probes()` or documenting why the
  subset net is kept, and fixing the comment.

---

## §R — RESIDUAL TABLE (read the WHOLE table, #105)

| # | severity | site | one-line |
|---|----------|------|----------|
| **D-A** | **INSUFFICIENT** | `entry()` `test_link5:1429` / `TestTheFieldManifestCannotSilentlyMissAField:2151` | **CONSTRUCTED** (§APPENDIX): `SAFE:=strish−door` makes `missing` structurally empty; a NEW caller-free-text field is absorbed into SAFE, untokenised, undetected — P-F (field-reach, 1 of 3 D2 checked vars) cannot fire. Fix: independent DOOR+SAFE hand-lists, union==strish. |
| **D-B** | **INSUFFICIENT** | `TestEveryDrivenRenderBranchIsExercised:2119` + `REPORT-contract-04b5-3.md §SAT` | P-S RED at HEAD on 12 store-free renders (dozens of un-run door-free branches); P-S is fix-independent so a production build CANNOT green it; **§SAT satisfiability receipt EMPTY** → #133 unmet. Fix: complete the store-free probe shapes + fill §SAT with 0-failed counts. |
| **D-C** | **MED** | `_BRANCH_COVERAGE_EXEMPT:1860` | Silent hand-list (skip-only at `:2125`); no machine-verify-store-backed, no re-open-trigger test, no stale guard — unlike `_RENDER_OUT`. A divergent un-driven branch of a batch render is uncaught. Earn it like P-C. |
| **D-U** | **LOW** | `_RENDER_DRIVERS:605` | Vestigial 12-entry parallel registry duplicating `_render_probes()`; comment `:602` names the retired `TestEveryRenderSiteThatHandlesCallerTextIsDriven`. Fold or document; fix the dead-test reference. |
| **D-P** | **LOW (info)** | `pyproject.toml:64` + `Containerfile:74,87` | "coverage NOT an image dep" prose is imprecise: the dev group (hence coverage) IS synced into the image venv for #139 conformance. True as "nothing shipped imports it"; imprecise as written. |
| D1 | **CLOSED** | `_probes():1704-1718` | Both byte-proven doors DRIVEN (residue/dependent shapes), LEAK at HEAD, branches covered (absent from P-S un-run set). The cold-audit-04b5-4 D1 gap is genuinely closed. |
| P-U | **CLOSED** | `_candidate_render_sites():1967` / `TestEveryRenderCandidateIsDrivenOrOut:1977` | Method-reach name-blind by interpolation property (non-prefix helpers IN, non-vacuity PASSES); a new render reddens. The D2 method-reach fix is sound. |
| S-N | **CLOSED** | `_tier_miss_teach`/`_filter_miss_notice` probes | The served-NOTICE door class is real and DRIVEN (all 4 store-backed doors leak at HEAD). |
| COH | **SOUND** | `TestEveryServedCallerByteIsInExactlyOneNet:2347` | Coherence pin + positive control green; `map` is `code_rag` OUT with residual + pkt39 flag. |
| ERR | **PRESERVED** | `TestNoServedDomainErrorLeavesACallerParamUncontained:1138` | Error-half AST site scan intact, RED at HEAD (49 doors), non-vacuity + positive control sound. |

## VERDICT: **INSUFFICIENT** → back to the contract author.
D1 and P-U are genuinely closed and much of the instrument is strong. The blocker is that **two of
the three coupled render checked variables do not hold**: P-F field-reach is a tautology that cannot
fail (D-A, CONSTRUCTED), and P-S branch-reach is RED-at-HEAD unsatisfiable-by-any-production-fix with
an empty §SAT receipt (D-B). Under the operator's all-or-nothing ruling and #133, a render net in
which field-reach can't fire and branch-reach can't be satisfied is not yet the checked variable D2
requires. Close D-A (independent DOOR+SAFE hand-lists) and D-B (complete the store-free shapes + fill
§SAT to 0-failed), give `_BRANCH_COVERAGE_EXEMPT` the P-C earning (D-C), then to the contract-adversary.

---

## §APPENDIX — the P-F construction probe (instrument, pasted verbatim per brief-base §1; run at `9cb1633` from `loremaster/`)
```python
"""DELTA-AUDIT probe (coldaudit-04b5-5): does P-F's manifest-completeness net actually
REDDEN when a rendered model gains a NEW caller-free-text str field?
Run from loremaster/: `uv run python /tmp/probe_pf_manifest.py`  (exit 1 == guard FAILED to fire).
"""
import sys
sys.path.insert(0, "tests")
import test_link5_render_containment as T
from loremaster.tasks import Task

door, safe = T._manifest()[Task]
strish = {n for n, f in Task.model_fields.items() if T._is_str_ish(f.annotation)}

print("=== structural tautology check (over the REAL manifest, every model) ===")
always_empty = True
for model, (d, s) in T._manifest().items():
    live_strish = {n for n, f in model.model_fields.items() if T._is_str_ish(f.annotation)}
    missing = live_strish - (d | s)           # exactly what the test asserts == {}
    if (d | s) != live_strish:
        always_empty = False
        print(f"  {model.__name__}: d|s != strish (missing={sorted(missing)})")
print(f"  For EVERY manifest model, DOOR|SAFE == strish exactly: {always_empty}")
print(f"  => the test's `missing = strish - (door|safe)` is STRUCTURALLY always empty.")

print("\n=== faithful NEW-FIELD simulation (Task gains caller-free-text `tags`) ===")
class TaskWithNewField(Task):
    tags: str = ""      # NEW caller-free-text field, NOT added to _manifest()'s door set

strish_new = {n for n, f in TaskWithNewField.model_fields.items() if T._is_str_ish(f.annotation)}
safe_new = frozenset(strish_new - door)        # entry() recomputes safe as the complement
missing_new = strish_new - (door | safe_new)   # what test_every_rendered_models_str_fields_are_classified asserts == {}

print(f"  'tags' present in strish?           {'tags' in strish_new}")
print(f"  'tags' in DOOR hand-list?           {'tags' in door}")
print(f"  'tags' absorbed into SAFE(complement)? {'tags' in safe_new}")
print(f"  missing (what the P-F test FLAGS):  {sorted(missing_new)}")
print(f"  => P-F test verdict on the new door field: "
      f"{'RED (caught)' if missing_new else 'GREEN (ESCAPED)'}")

forged = T._forge(TaskWithNewField, forge=True)
tags_val = getattr(forged, "tags")
print(f"  _forge sets tags = {tags_val!r} (marker present? {T.FORGERY_MARKER in str(tags_val)}) "
      f"=> untokenised, so a bare render of `tags` would NOT leak a marker; neutralisation stays GREEN.")

sys.exit(0 if missing_new else 1)  # exit 1 == the guard FAILED to fire == defect present
# MEASURED @9cb1633: tautology True; new field 'tags' -> GREEN (ESCAPED); PROBE_EXIT=1.
```

## §COMMANDS (re-runnable, run at `9cb1633` from `loremaster/`)
```
uv run pytest loremaster/tests/test_link5_render_containment.py -n auto   # 53 failed, 96 passed (149)
uv run pytest loremaster/tests/test_link5_render_containment.py -k "no_driven_render_has_an_unexercised_branch"  # P-S RED, names 12 methods' un-run branches
uv run python /tmp/probe_pf_manifest.py                                    # P-F tautology, exit 1
MYPYPATH=loremaster:loremaster/tests uv run mypy loremaster/tests/test_link5_render_containment.py  # Success
```
