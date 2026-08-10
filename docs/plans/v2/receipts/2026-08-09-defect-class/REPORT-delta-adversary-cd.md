# REPORT-delta-adversary-cd — DELTA contract adversary, revised C (#291/#347) + D (#295/#346)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK

- **VERDICT: CONTRACT SUFFICIENT.** Both revised contracts are satisfiable and no wrong build
  survives the satisfiable suite. Independently reproduced — I did not trust the reviser.
- **(a) Did the revision truly close each original survivor?** YES, both, reproduced in scratch:
  - **C-WB5** (derive-all-but-hardcode `lore_findings`): CAUGHT by the ∀-flip
    `…is_live_over_every_annotation_constant[_FINDINGS_TOOL_ANNOTATIONS]`.
  - **D-WB2** (in-process helper): whole-session form CAUGHT by the D file (AttributeError on the
    `(call,…)` sig); the representable `__self__` back-door CAUGHT by R16's receiver-blind scan,
    which the reach pin forces the builder to extend.
- **(b) Did the revision open a NEW wrong build?** NO surviving new build found. The C ∀
  generalises correctly to EVERY constant (I broke it three different ways, all caught); the D
  closure holds. **One non-blocking trust NIT** (below), already adjudicated by the reviser.
- **P1 headline:** 0 surviving wrong builds. C-WB5 + two NEW different-constant hardcodes
  (`lore_comms`, `lore_search`) all RED; D-WB2 both forms RED. §DISCRIM.
- **Meta-recursion (the #347 crux) EMPIRICALLY confirmed:** C's ∀ parametrized set == the LIVE
  annotation surface — 6 members at HEAD, GROWS to 7 when I add a constant, a rogue constant
  (governs no tool) REDDENS via the landing assert, and a hand-list regression of the surface is
  caught by the reach pin naming `['lore_index','lore_remember']`. §C-META.
- **DRY (priority #1):** single-source enforced — helper + stale 4-name `_MUTATING_TOOLS` → C-9
  RED. **TRUST (priority #2):** D makes no false coverage claim (the no-permanent-coverage bound
  is STATED via `_SWEEP_ENUMERATION_MUST_BE_…`, not faked); the effect-leg still catches the
  marker-only proxy under the new signature.
- **⚠ P0 self-catch:** my first D-WB2b probe "passed" the D file for the WRONG reason (buggy
  extraction: `call_tool` returns a TUPLE for `-> str` tools, my `.text`-join yielded `''`).
  Faithful extraction flipped it to **8 passed (D file BLIND) → caught only by R16.** §D-P0.
- **NIT (non-blocking, trust):** the R4 pin name/docstring say the in-process door is
  "unrepresentable by construction," but the `__self__` form IS representable and closed by the
  R16 leg, not by construction. The reviser's residual R1 says this honestly. Recommend softening
  the name; do NOT add a cloned scan (DRY). §RESID R-N1.
- **C-DEF satisfiability:** my OWN reference (not the reviser's) → **34 passed, 0 failed** across
  both contracts + `test_wire_discipline.py`. §SAT.
- **Packages considered:** none — my reference builds are stdlib set ops / `assert` / AST reuse;
  no library provides deny-by-default annotation partitioning, a wire-effect helper, or an AST
  reach scan. `frozenset` return is already stdlib.
- **Graded:** `3b708e5` · HEAD-at-report: `14b62f2` · DIFFERENT (1 behind) — `14b62f2` added only
  design-doc §10; the two contracts + `server.py` + `test_wire_discipline.py` are byte-identical
  `3b708e5`→HEAD (`git diff --stat` empty). Nothing my verdict rests on moved.
- **Provenance:** all builds in `/tmp/delta-cd-work` via `scratch_copy.sh`;
  `loremaster.__file__ = /tmp/delta-cd-work/loremaster/loremaster/__init__.py` (#140 — I graded
  the scratch tree). §PROV.
- Receipt pointers: §SAT · §C-DISCRIM · §C-META · §D-DISCRIM · §D-P0 · §P7 · §TABLES · §RESID.

---

## §SAT — SATISFIABILITY (my own reference, positive control for every probe)

I re-derived the intended fix from the contracts (NOT the reviser's build) in scratch:
- **C:** `loremaster.server.partition_tools_by_posture(tools)` = deny-by-default
  (`readOnlyHint is not True → mutating`); `test_mcp_server._MUTATING_TOOLS` corrected 4→6.
- **D:** `loremaster/tests/_refusal_effect.py` = `(call,…)` effect helper (wire via the callable,
  marker leg, `effect_count()==0` post-dispatch) + subset sweep primitive (fail-closed on empty).
- **R16 (builder leg):** `test_wire_discipline.posture_modules()` extended (a
  `REFUSAL_HELPER_MODULE_NAMES` set unioned in, derived-by-existence) to cover `_refusal_effect.py`.

```
$ cd /tmp/delta-cd-work && uv run pytest \
    loremaster/tests/test_mutating_set_derivation.py \
    loremaster/tests/test_refusal_observes_effect.py \
    loremaster/tests/test_wire_discipline.py -q
..................................                                        [100%]
34 passed in 2.42s
```

Re-run to a clean tree after all swap/restore cycles: **34 passed** again (positive control that my
harness restores the reference byte-faithfully). `loremaster.__file__` inside scratch (§PROV).

---

## §C-DISCRIM — C wrong-build record (INSTRUMENT C / #291 / #347)

Each build swaps only `partition_tools_by_posture` in scratch `server.py`, runs the C contract,
restores. Every hardcode AGREES with the annotations at HEAD, so every non-flip oracle passes — the
∀-flip on the governing constant is the sole catcher, exactly as intended.

| build | mutation | result | which pin RED |
|---|---|---|---|
| REFERENCE | deny-by-default derivation | **18 passed** | — (satisfiable) |
| **C-WB5** (#347 survivor) | derive all EXCEPT `lore_findings` (hardcode mutating) | 1 failed / 17 passed | `…is_live_over_every_annotation_constant[_FINDINGS_TOOL_ANNOTATIONS]` |
| **C-NEW-1** (new, singleton constant) | hardcode `lore_comms` mutating | 1 failed / 17 passed | `…[_COMMS_TOOL_ANNOTATIONS]` |
| **C-NEW-2** (new, 9-tool shared constant) | hardcode `lore_search` read_only | 1 failed / 17 passed | `…[_READ_ONLY_ANNOTATIONS]` |

**Verdict:** the original C-WB5 is TRULY closed, and the fix is NOT a point-patch for `lore_findings` —
a hardcode of ANY tool is caught by its governing constant's flip, including a read-only-side hardcode
and a hardcode under a constant shared by nine tools. This answers the brief's step-2 directly:
C-WB5 AND a NEW hybrid hardcoding a DIFFERENT constant are BOTH caught by the ∀-flip.

---

## §C-META — the meta-recursion: is the ∀ set the LIVE surface? (brief step 4)

The parametrization is `@pytest.mark.parametrize("constant_name", sorted(_live_annotation_constants()))`,
evaluated at COLLECTION against the real `loremaster.server`. Empirically:

```
# param count at HEAD:
$ pytest test_mutating_set_derivation.py --collect-only | grep -c is_live_over…
6
  [_COMMS_TOOL_ANNOTATIONS] [_FINDINGS_TOOL_ANNOTATIONS] [_INDEX_ANNOTATIONS]
  [_READ_ONLY_ANNOTATIONS]  [_SAVE_MEMORY_ANNOTATIONS]   [_TASK_TOOL_ANNOTATIONS]

# after injecting a bare rogue `_PROBE_META_ANNOTATIONS` into server.py:
param count -> 7                       # the parametrization GREW: the set is LIVE, not a fixture constant
run -> 1 failed: …is_live_over_every_annotation_constant[_PROBE_META_ANNOTATIONS]   # landing assert:
                                       # "flipping … did not change the spec partition … governs no tool"
```

And the guard-of-the-guard (`test_the_flip_surface_reaches_every_tool`) FIRES when the surface
derivation is regressed to a hand-list that still passes the "names known constants" anti-vacuity check:

```
# _live_annotation_constants() shrunk to the 4 'known' names (omits _SAVE_MEMORY, _INDEX):
$ pytest test_mutating_set_derivation.py
1 failed / 15 passed
AssertionError: the LEG-B flip surface does NOT reach every registered tool:
  ['lore_index', 'lore_remember'] are governed by an annotation constant ABSENT from the live surface …
```

**Verdict:** the ∀ parametrized set IS the live annotation surface (grows with production), a rogue
constant reddens (landing assert), and a shrunk surface is named-and-caught by the reach pin. The
reach is a CHECKED VARIABLE, not a hidden constant — the #347 class is genuinely closed, including
one level up (the meta-recursion). The vacuous-parametrize hole (surface → empty → ∀ over nothing)
is guarded by the non-parametrized anti-vacuity + reach pins, which run regardless of the expansion.

---

## §D-DISCRIM — D wrong-build record (INSTRUMENT D / #295 / #346)

Each build swaps `_refusal_effect.py`, runs the D contract file AND `test_wire_discipline.py`
(R16), restores. FastMCP `call_tool` returns `list[block]` OR `(blocks, structured)` depending on
the tool's return annotation — extraction handles both (see §D-P0).

| build | mutation | D file | R16 scan |
|---|---|---|---|
| REFERENCE | `(call,…)` wire-driving effect helper | **8 passed** | 8 passed |
| **D-WB2** (whole session) | sig `(session,…)`, `session.mcp.call_tool` in-process | **3 failed / 5 passed** (AttributeError: bound method has no `.mcp`) | 1 failed `[_refusal_effect.py]` |
| **D-WB2b** (`__self__` back-door) | sig `(call,…)`, `call.__self__.mcp.call_tool` in-process, FAITHFUL extraction | **8 passed — D FILE BLIND** | **1 failed `[_refusal_effect.py]`** (receiver-blind scan) |
| **D-WB1** (marker-only, new sig) | `(call,…)`, no effect leg | 1 failed / 7 passed | — |

**Verdict:** D-WB2 is closed by TWO legs that together leave no survivor:
1. The SIMPLE in-process door (`wire.mcp.call_tool`, needing a `wire` handle) is unrepresentable —
   the helper is handed only `call`. A whole-session helper AttributeErrors → D file catches it.
2. The `__self__` back-door (`call.__self__.mcp.call_tool`) IS representable and the D file is BLIND
   to it (8 passed). It is caught ONLY by R16's receiver-blind AST scan, which the D contract's
   reach pin FORCES the builder to extend to cover `_refusal_effect.py`. Once extended (required for
   satisfiability — the reach pin is RED until then), the scan flags `.call_tool` regardless of
   receiver. Making the reach pin green NECESSARILY brings the helper under the scan: both use the
   SAME `posture_modules()` (the scan parametrizes over it; the reach pin asserts membership tied to
   `inspect.getfile(helper)`). No decoupling without an obvious, auditable subversion of R16 itself.

The effect-leg (D-WB1) and read-before-dispatch (D-WB3, original) catches survive the signature
change — D-WB1 shown RED above.

---

## §D-P0 — the probe that lied, and the control that caught it (CLAUDE.md "a probe needs a control")

My FIRST D-WB2b build "passed" the D file for the WRONG reason and would have made me falsely credit
the D file with closing the `__self__` door. DEBUG receipt:

```
DEBUG __self__ type: WireSession has mcp: True
DEBUG res type: tuple repr: ([TextContent(text='REFUSED-BY-CONTRACT-PROBE-CD')], {'result': '…'})
DEBUG body: '' effect: 0     # my `.text`-join iterated the 2-TUPLE -> '' -> `marker in body` False -> the D file "caught" it
```

Root cause: the probe tools declare `-> str`, so FastMCP returns `(blocks, structured_dict)` — a
tuple — where my earlier standalone probe (a `def t()` with no annotation) returned a bare list. With
faithful extraction (`res[0] if isinstance(res, tuple) else res`), D-WB2b flips to **8 passed on the
D file** (genuinely blind) and is caught only by R16. Pairing the negative (door survives D file)
with the positive control (reference 34-passed; the R16 scan FIRES on the same file) is what made the
truth legible. This is the exact P0 failure the role warns of — logged so the closure claim rests on
the real mechanism, not a buggy wrong build.

---

## §P7 — RED honesty (contracts fail for the RIGHT reason)

Deliverables stripped (no `partition_tools_by_posture`; `_refusal_effect.py` deleted):
- **C:** `ImportError: cannot import name 'partition_tools_by_posture'` → caught by `_import_derivation`
  → `pytest.fail("finding #291 deliverable ABSENT …")`. Behavioral fail via the lazy-import guard, not
  a module-level collection error.
- **D:** `ModuleNotFoundError: No module named '_refusal_effect'` → caught by `_import_effect_helper`
  → `"helper absent"`. Same lazy-import discipline.

Both RED for the genuine "deliverable absent" reason — no import-typo / bad-path / "no tests ran"
false RED.

---

## §TABLES

### P1b — QUANTIFIER TABLE (per invariant: ∀-over-inputs vs guarded-by-a-known-door)

| # | invariant | class | receipt |
|---|-----------|-------|---------|
| C-1 | helper EXISTS + partition non-empty | existence | RED baseline "deliverable ABSENT" (§P7); reference passes |
| C-2 | every tool carries a non-None readOnlyHint | ∀ over surface | GREEN-today; control fires on the unannotated probe (non-vacuous) |
| C-3 | mutating ∪ read_only == surface, disjoint, both non-empty | ∀ over surface | coverage/anti-vacuity; catches partial/phantom partitions & tools-ignoring hardcode (with C-4) |
| C-4 | unannotated → MUTATING (deny-by-default) | ∀ over unannotated, 1 synthetic probe | sole catcher of `==False`; also kills a tools-ignoring hardcode (probe unseen) |
| C-5 | derived == spec predicate | ∀ over surface (predicate twice) | catches a different predicate (name-substring / destructiveHint) |
| **C-6** | **derivation is LIVE ∀ over EVERY annotation constant** | **∀ over the LIVE-DERIVED surface (was 2/15; now 6 constants → 15/15 tools)** | **C-WB5 + C-NEW-1 + C-NEW-2 all RED (§C-DISCRIM); reach IS a checked variable (§C-META). #347 CLOSED** |
| C-6b | flip surface reaches every registered tool | meta-reach, ∀ | **FIRES on a shrunk surface, names `['lore_index','lore_remember']` (§C-META)** |
| C-6c | live surface non-empty + names #291/#347 constants | anti-vacuity | guards the vacuous-parametrize hole (non-parametrized, runs regardless) |
| C-7 | known-mutating ⊆ derived mutating | ∀ over a named 6-set | independent contents oracle; catches a real tool mis-annotated |
| C-8 | known-read-only ⊆ derived read_only | ∀ over a named 9-set | security-relevant direction |
| **C-9** | **no drifted hand-list beside the derivation (DRY)** | **guarded by 2 names** | **helper + stale 4-name `_MUTATING_TOOLS` → RED (§final probe). BOUND: a 3rd-named hand-list escapes (R-R1)** |
| D-1 | helper passes a refuse-first build | negative control | reference passes (marker present, effect 0) |
| **D-2** | **helper fails run-then-refuse ON THE EFFECT LEG** | **effect ∀-observed; WIRE sub-property now enforced by construction+R16** | **D-WB1 (marker-only) RED; D-WB3 (read-before) RED (inherited); D-WB2 CLOSED (§D-DISCRIM)** |
| D-3 | proxy cannot distinguish the two builds | the #295 byte-identical 2-build proof | GREEN, self-contained |
| **D-4** | **helper WIRE-driving verified (R4 + R16 reach)** | **guarded: R4 removes the simple handle; R16 scan (reach-forced) removes the `__self__` door** | **D-WB2 both forms RED. MP-1/#346 CLOSED. NIT: R4 name overclaims "unrepresentable" (R-N1)** |
| D-5 | sweep coverage: names missed pin, fails-closed on empty | ∀ over synthetic sets | passes; HONEST BOUND — no real derived refusal-pin set, STATED not faked |

Every **guarded** row carries its receipt (a surviving-or-killed door-build), above.

### P1c — REACH TABLE (per instrument the contract introduces/relies on)

| instrument | reach = SET of sites | DERIVED or hand-list? | coverage a CHECKED variable? | EFFECT or PROXY? | one-source proven by MUTATION? | verdict |
|---|---|---|---|---|---|---|
| `partition_tools_by_posture` | the input tools | **DERIVED** (input set) | YES — C-3 (∪==surface, disjoint, non-empty) | EFFECT (real annotations) | ∀-flip below | SAFE |
| `…is_live_over_every_annotation_constant` (∀-flip) | `sorted(_live_annotation_constants())` | **DERIVED, LIVE** (6→7 when I added a constant, §C-META) | YES — reach pin + landing assert | EFFECT (flips real prod constant, rebuilds) | this IS the mutation proof | **SAFE — #347 fix, EMPIRICAL** |
| `test_the_flip_surface_reaches_every_tool` (meta-reach) | union of tools moved by flipping all constants vs full surface | **DERIVED** | YES — coverage IS the assertion; fires on shrink | EFFECT (spec oracle) | oracle-based on purpose | **SAFE — EMPIRICAL (named unreached)** |
| `…surface_is_not_empty_and_names_known` (anti-vacuity) | the live surface | DERIVED + named receipts | YES (non-empty + named) | — | — | SAFE (guards vacuous parametrize) |
| `test_no_drifted_hand_list…` (C-9 DRY) | `{_MUTATING_TOOLS, _READ_ONLY_TOOLS}` by name | **HAND-LIST (2 names)** | NO (3rd-named escapes) | EFFECT (re-derives spec each run) | catches a disagreeing hand-list | OK for scope; BOUND R-R1 (INSTRUMENT 0 is the standing guard) |
| `assert_tool_refused_and_did_not_run` (effect helper) | the `(call, effect_count)` handed in | derived from input | n/a (single-call) | **EFFECT (counter==0 post-dispatch)** | wire-driving via R4+R16 below | SAFE |
| R4 pin `…boundary_callable…unrepresentable` | the helper's parameter surface | construction | n/a | closes the SIMPLE door by construction | — | SAFE for `wire.mcp`; **NIT: name overclaims for `__self__` (R-N1)** |
| R16 reach pin `…within_R16_wire_discipline_reach` | `posture_modules()` (glob + builder union) | **DERIVED**, tied to `inspect.getfile(helper)` | YES — membership IS the check; same set the scan parametrizes | forces the receiver-blind scan (EFFECT: no in-process handler call) | REUSES R16, not cloned (DRY) | **SAFE — #346 closure, EMPIRICAL (D-WB2b RED on R16)** |
| `assert_sweep_reached_every_refusal_pin` (sweep coverage) | the `derived` set handed in | primitive is derived-agnostic; the REAL set is NOT built here | YES for the primitive (fail-closed on empty; names missed pin) | n/a | n/a | HONEST BOUND STATED (`_SWEEP_…` note); INSTRUMENT 0 guards instance #9 |

**Legs run:** every C row and the D helper/R4/R16-reach rows are **EMPIRICAL** — I built the wrong
versions in scratch and ran the real contract (+ R16). The C-9 name-keyed bound and the sweep
primitive's "no real derived set" bound are read by **construction-inspection**, then the C-9 bound
was confirmed empirically (stale hand-list → RED) and the sweep primitive's three semantics were
confirmed by the contract's own tests. Positive controls paired with every negative (34-passed
reference; §SAT).

---

## §RESID — residuals (each individually adjudicated; scope law — surfaced, not dropped)

- **R-N1 (D, TRUST NIT, non-blocking):** the R4 pin is named
  `…the_in_process_door_is_unrepresentable` and its docstring says the door is removed "by
  construction," but the `__self__` back-door (`call.__self__.mcp.call_tool`) IS representable and is
  closed by the R16 leg, not by construction (§D-DISCRIM proves the D file is BLIND to it — 8 passed).
  The door is genuinely closed (R16 reach-forced), so this is NOT a surviving wrong build — but the
  pin NAME asserts a stronger property than that pin delivers. The reviser's own residual R1 documents
  this honestly. **Recommendation (operator/author call):** soften the pin name/docstring to name
  R16 as the `__self__` closer (e.g. `…the_simple_in_process_door_is_unrepresentable_and_R16_closes_the_rest`),
  or add a one-line docstring pointer. **Do NOT** clone R16's scan into the D file — that is the DRY
  defect (priority #1) this cycle exists to kill. Surfaced for a ruling, not filed as a new finding
  (#346 already covers the class).
- **R-R1 (C, name-keyed bound, inherited adversary R1/reviser R4):** `test_no_drifted_hand_list…`
  keys on `_MUTATING_TOOLS`/`_READ_ONLY_TOOLS`; a third-named hand-list (`_WRITABLE_TOOLS`) escapes.
  **Verdict:** honest bound of a name-keyed pin; INSTRUMENT 0's reach-attack is the standing guard.
  Non-blocking, unchanged by the revision.
- **R-2 (C, single-constant-at-a-time liveness, low):** the ∀-flip flips ONE constant per parametrized
  case. A wrong build that is correct on every single-constant flip but wrong only on a COMBINATION of
  flips would evade it. **Verdict:** for a partition that is a pure per-tool function of that tool's
  annotation (the only realistic shape; a hardcode/hand-list is a per-tool divergence), single-tool
  flips are sufficient — a cross-tool-stateful derivation is not a plausible honest build. Non-blocking
  bound, noted so a future author does not read the ∀ as covering combinations.
- **R-3 (D, R16 scan is name-based, inherited):** R16 forbids `.call_tool`/`.list_tools` (the
  SDK-bound handler names, DERIVED from `FastMCP._setup_handlers`). A grotesque in-process dispatch via
  a non-handler method (`call.__self__.mcp._tool_manager.get_tool(name).fn(**args)`) would evade it.
  **Verdict:** out of the honest-engineer threat model (CLAUDE.md — the gate is for the developer who
  reaches for the DOCUMENTED in-process shortcut, `mcp.call_tool`, not a hostile author); R16's own
  design and derivation own this bound. Non-blocking, pre-existing (not opened by this revision).
- **R-4 (C helper not proven CONSUMED, inherited):** the contract pins the helper's existence +
  correctness, not that production consumes it (packet 39 does, later). **Verdict:** acceptable for
  this cycle's scope; the #291 test-side drift is fixed regardless. Unchanged.

---

## §PROV — provenance & tooling

- Scratch tree: `/tmp/delta-cd-work`, built by `./scripts/scratch_copy.sh` (excludes poison,
  `uv sync --all-packages`, ASSERTS provenance). `loremaster.__file__ =
  /tmp/delta-cd-work/loremaster/loremaster/__init__.py` (I graded the scratch tree, not the original — #140).
- My OWN reference (`partition_tools_by_posture`, `_refusal_effect.py`, the `posture_modules()`
  extension) + all wrong builds (C-WB5 / C-NEW-1 / C-NEW-2 / the rogue-constant + surface-shrink meta
  mutations / D-WB2 / D-WB2b / D-WB1) are described inline with their diffs and receipts here; the
  harness scripts (`/tmp/delta-cd-setup.py`, `-cwrong.py`, `-dwrong2.py`) live in `/tmp` (disposable)
  and their exact variant bodies are pasted in this report per brief-base §1.
- lore tools used: `lore_comms` (register). Grep used for the `*_ANNOTATIONS` surface, `_MUTATING_TOOLS`
  drift, and the R16 `posture_modules`/scan structure — non-symbol textual seams + cross-cutting map
  (two of the three honest grep cases); SAID here per the dogfood protocol. No lore weakness to file.
- Findings #346 (MP-1) / #347 (MP-2) were filed by the original adversary; both are now CLOSED by the
  revision per my empirical reproduction (they formally close when the builder ships + the cold audit
  confirms). I file no new finding — R-N1 is a naming nit for an operator ruling, already captured by
  the reviser's R1.

## VERDICT: CONTRACT SUFFICIENT

Both original surviving wrong builds are truly closed, independently reproduced: C-WB5 by the ∀-flip
over the live annotation surface (and the fix generalises — two NEW different-constant hardcodes also
RED), and D-WB2 by R4 (simple door) + R16 (the `__self__` door, reach-forced). No NEW surviving wrong
build was found across the C hardcode family, the meta-recursion (the ∀ set is genuinely the live
surface, and its reach is a checked variable that reddens on a shrink), and the D signature change (the
effect-leg still catches the proxy observer). The suite is satisfiable (34 passed against my own
reference), the RED baseline fails for the right reason, DRY single-source and D's honest
no-coverage-bound both hold. The one open item — the R4 pin's "unrepresentable" name overclaiming a
closure the R16 leg actually provides — is a non-blocking TRUST nit already documented by the reviser,
routed to the operator for a naming ruling, NOT a missing pin (adding a duplicate scan would violate
DRY, the #1 priority this cycle exists to enforce).
