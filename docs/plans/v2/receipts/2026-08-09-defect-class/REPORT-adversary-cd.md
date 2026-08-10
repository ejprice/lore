# REPORT-adversary-cd — contract adversary, INSTRUMENTS C (#291) + D (#295)

brief-base v10 read
brief project v7 read

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT** (both contracts satisfiable, but each waves through a wrong build).
- **P1 headline — two wrong builds survive the contracts:**
  - **D-WB2 (in-process helper):** a helper that dispatches via `wire.mcp.call_tool` and NEVER touches the wire passes all 6 D pins — the contract's own step-1 docstring forbids exactly this (WB30). → **MISSING PIN MP-1 / finding #346.**
  - **C-WB5 (hybrid hardcode):** a helper that derives every tool from annotations EXCEPT `lore_findings` (hardcoded) passes all 10 C pins — the liveness mutation proof's reach is 2/15 tools. → **MISSING PIN MP-2 / finding #347.**
- **Graded:** working-tree (both contracts UNTRACKED `??`) · HEAD-at-report: `405d3213` · design-doc graded `74694dc` (ancestor, 5 behind) — no symbol my verdict rests on moved (contracts are new, deliverables still absent at HEAD).
- **Packages considered:** none — grading built two reference impls (a set-predicate annotation-derivation + an assert helper); neither is a mechanism a library provides (stdlib set ops / `assert`). C's suggested `frozenset` return is already stdlib.
- **C-DEF satisfiability:** REFERENCE builds → **16 passed, 0 failed** (both contracts, one run). Reference is the intended fix; the GREEN-today pins stay green and are non-vacuous (controls fire).
- **DRY (priority #1):** C forces a single source — the two-sources wrong builds are caught (derive-in-test → import fails; stale hand-list → equality pin RED). D shares the effect-check as one helper. **BUT** C's liveness proof only covers 2/15 tools (MP-2) and D's wire-driving is unverified (MP-1).
- **TRUST:** D does NOT falsely claim a coverage guarantee — the no-permanent-coverage-pin bound is stated honestly (synthetic sweep sets + the `_SWEEP_ENUMERATION_MUST_BE_...` note). The marker-only proxy build IS caught by the effect leg (byte-identical 0-vs-1 proof reproduced).
- **Provenance:** all builds in `/tmp/adv-cd-work`; `uv run` resolves `loremaster.__file__ = /tmp/adv-cd-work/loremaster/loremaster/__init__.py`; blessed verifier VERIFIED.
- Receipt pointers: §C (C wrong builds), §D (D wrong builds + proposed-pin controls), §TABLES (quantifier + reach), §SAT (satisfiability), §RESID (residuals).

---

## MISSING PINS (the findings list — each routes back to CONTRACT)

### MP-1 (D / #295 / finding #346) — the effect-helper's WIRE-driving is unpinned
- **The test that should exist:** a pin that proves the helper drove the WIRE, not the in-process handle. Constructible auth-free (DEMONSTRATED, §D.4): wrap the `wire` handed to the helper so `.call` is counted; assert it was invoked ≥1. A helper using `wire.mcp.call_tool` invokes it 0 times → RED.
- **The defect it catches:** an in-process helper (`wire.mcp.call_tool`) that is DEAD ON THE WIRE (WB30, finding #295 WAVE 1). Packet 39 consumes this exact helper for its posture pins (F2). A wire-dead helper sees a WB30 guard as LIVE while the real wire path is unguarded → mutating tool dispatchable over the wire, pin GREEN. **The contract's own step-1 docstring names WB30 and forbids this, but no pin enforces it.**
- **Alternative resolution (operator/author's call):** if wire-verification genuinely belongs to packet 39 (F2 routes the *structural* answer there), then DEMOTE the step-1 docstring's WB30 claim so the contract stops asserting a property it does not verify. Either add the pin here or demote the claim — the current claim-vs-check gap is the trust defect.

### MP-2 (C / #291 / finding #347) — the liveness mutation proof's reach is a hidden constant (2 of 15 tools)
- **The test that should exist:** make the mutation proof's reach a CHECKED VARIABLE — flip EACH annotation constant in turn (or, structurally, ∀ over the surface: build a synthetic tool list, flip each tool's hint one at a time, assert the partition tracks exactly that tool). The single `_TASK_TOOL_ANNOTATIONS` flip verifies liveness for 2/15 tools only.
- **The defect it catches:** a build that derives most tools from annotations but HARDCODES one non-task tool's class (C-WB5 hardcodes `lore_findings`). It passes all 10 pins because the mutation proof never flips the hardcoded tool and every other oracle agrees at HEAD. This is exactly #291's drift, one tool over — flip `_FINDINGS_TOOL_ANNOTATIONS` later and the hardcoded class silently disagrees with production. **The reach-is-a-hidden-constant class, inside the contract built to kill it.**

---

## TABLES

### P1b — QUANTIFIER TABLE (per invariant: ∀-over-inputs vs guarded-by-a-known-door)

| # | invariant | class | receipt |
|---|-----------|-------|---------|
| C-1 | helper EXISTS + partition non-empty | existence | derive-in-test / no-prod-helper → import fails (RED baseline, 13 failed "deliverable ABSENT") |
| C-2 | every tool carries a non-None readOnlyHint | ∀ over surface | GREEN-today; control `test_the_non_none_hint_pin_is_not_vacuous` FIRES on the unannotated probe (non-vacuous) |
| C-3 | mutating ∪ read_only == surface, disjoint | ∀ over surface | reference passes; catches partial/phantom partitions |
| C-4 | unannotated → MUTATING (deny-by-default) | ∀ over unannotated tools, exercised by 1 synthetic probe | **caught C-WB4 (`==False`)** and C-WB3 (hardcode); SOLE catcher of `==False` (spec-equality agrees on the unperturbed surface) |
| C-5 | derived == spec predicate | ∀ over surface (same predicate twice) | catches a *different* predicate; does NOT catch `==False` on the real surface (noted — belt-and-braces with C-4) |
| **C-6** | **derivation is LIVE (reads annotations)** | **GUARDED by the `_TASK_TOOL_ANNOTATIONS` flip → reach = 2/15 tools** | **DOOR-BUILD C-WB5 (hardcode `lore_findings`) PASSES all 10 pins → MP-2.** Non-vacuity confirmed: reference passes, C-WB3 hardcode fails |
| C-7 | known-mutating ⊆ derived mutating | ∀ over a named 6-set | independent contents oracle; GREEN today (catches a real tool mis-annotated) |
| C-8 | known-read-only ⊆ derived read_only | ∀ over a named 9-set | GREEN today (security-relevant direction) |
| **C-9** | **no drifted hand-list beside the derivation** | **GUARDED by 2 names (`_MUTATING_TOOLS`/`_READ_ONLY_TOOLS`)** | **caught C-WB2 (stale 4-name).** Bound: a hand-list under a THIRD name escapes (residual R1; standing guard = INSTRUMENT 0) |
| D-1 | helper passes a refuse-first build | negative control | reference passes (marker present, effect 0) |
| **D-2** | **helper fails run-then-refuse ON THE EFFECT LEG** | **effect sub-property ∀-observed; WIRE sub-property (step 1) UNOBSERVED** | **caught D-WB1 (marker-only) + D-WB3 (read-before-dispatch); DOOR-BUILD D-WB2 (in-process) PASSES → MP-1** |
| D-3 | proxy cannot distinguish the two builds | the #295 2-build proof (byte-identical) | GREEN, self-contained (passes even at RED baseline — proves the loopback wire mechanism runs store-free) |
| D-4 | sweep coverage: names missed pin, fails-closed on empty | ∀ over synthetic sets | passes; HONEST BOUND — no real derived refusal-pin set (stated in the `_SWEEP_ENUMERATION_MUST_BE_...` note), guarded by INSTRUMENT 0 |

Every **guarded** row carries its receipt: C-6 → a surviving door-build (MP-2); C-9 → the door named (residual R1); D-2 → a surviving door-build (MP-1).

### P1c — REACH TABLE (per instrument the contract introduces/relies on)

| instrument | reach = SET of sites | DERIVED or hand-list? | coverage a CHECKED variable? | EFFECT or PROXY? | one-source proven by MUTATION? | verdict |
|---|---|---|---|---|---|---|
| `partition_tools_by_posture` (the derivation) | the tools passed in | **DERIVED** from the input tool set | **YES** — coverage pin C-3 (∪==surface, disjoint) | observes the real annotations (EFFECT) | mutation proof exists — but see next row | reach OK; liveness reach weak (below) |
| `test_the_derivation_is_live…` (mutation proof) | which tools' liveness is verified = `{lore_tasks, lore_claim_task}` | **HAND-LIST (2 tool names, hardcoded in the test)** | **NO** — nothing asserts every annotation-constant/tool was flipped-and-tracked | effect (flips a real prod constant, rebuilds) | proves liveness for 2/15 only | **MISSING PIN MP-2** — door-build C-WB5 passes |
| `test_no_drifted_hand_list…` | `{_MUTATING_TOOLS, _READ_ONLY_TOOLS}` by name | **HAND-LIST (2 names)** | NO (a third-named hand-list escapes) | compares to a freshly re-derived spec each run (effect) | catches a disagreeing hand-list (C-WB2) | OK for its stated scope; residual R1 (bound, INSTRUMENT 0) |
| `assert_tool_refused_and_did_not_run` (effect helper) | the `wire`/`effect_count` it is handed | derived from input | n/a (single-call helper) | **observes the EFFECT (counter) ✓** — BUT does not verify the effect was observed OVER THE WIRE | — | **MISSING PIN MP-1** — in-process dispatch (a proxy for the wire) passes |
| `assert_sweep_reached_every_refusal_pin` (sweep coverage) | the `derived` set handed in | the PRIMITIVE is derived-agnostic; the REAL derived set is NOT constructed here | YES for the primitive (fail-closed on empty D-4; names missed pin) | n/a | n/a | HONEST BOUND stated (no derivable refusal-pin set); guarded by INSTRUMENT 0 |

**Legs run:** C-6/MP-2, C-9, D-2/MP-1 are EMPIRICAL (the guards are in-tree at my phase; I built the wrong versions in scratch and ran the real contract). The two hand-list reach rows (mutation-proof reach, no-drift reach) are read by construction-inspection of the contract source, then confirmed empirically by the surviving door-builds. Positive controls paired with every negative (reference build passes; §SAT).

---

## §SAT — C-DEF SATISFIABILITY (positive control for every probe)

Reference builds (the intended fix):
- **C:** `loremaster.server.partition_tools_by_posture` = the deny-by-default derivation (`readOnlyHint is not True → mutating`); `test_mcp_server._MUTATING_TOOLS` corrected 4→6 names.
- **D:** `loremaster/tests/_refusal_effect.py` = wire-driving effect helper (`wire.call`, marker leg, `effect_count()==0` post-dispatch) + subset-semantics sweep primitive (fail-closed on empty).

```
$ cd /tmp/adv-cd-work && uv run pytest \
    loremaster/tests/test_mutating_set_derivation.py \
    loremaster/tests/test_refusal_observes_effect.py -q
................                                                         [100%]
16 passed in 1.47s
```

Non-vacuity of the GREEN-today pins: C-2's control (`test_the_non_none_hint_pin_is_not_vacuous`) registers an unannotated probe and asserts it carries a `None` hint — it FIRES (proves the non-None pin is a real gate). D-3 passes even at the RED baseline, proving the loopback-wire byte-identical-marker / 0-vs-1-counter mechanism runs store-free — the contract's central #295 proof is live, not decorative.

---

## §C — C WRONG-BUILD RECORD (INSTRUMENT C / #291)

Baseline: reference C helper live; `_MUTATING_TOOLS` = 6 names. Each build patched in scratch, contract run, then restored.

| build | mutation | result | which pins RED |
|---|---|---|---|
| RED baseline | no deliverable | 13 failed / 3 passed | all deliverable-dependent pins fail "deliverable ABSENT" (correct RED, P7) |
| REFERENCE | correct helper | **10 passed** | — (satisfiable) |
| **C-WB2** | correct helper + stale 4-name `_MUTATING_TOOLS` (private hand-list beside the derivation) | 1 failed / 9 passed | `test_no_drifted_hand_list_survives_beside_the_derivation` (the #291 drift instance) |
| **C-WB3** | hardcoded 6/9 return, ignores `tools` (P2: "corrected-but-still-hardcoded") | 2 failed / 8 passed | `test_deny_by_default…` (fresh probe unseen) + `test_the_derivation_is_live…` (hardcode doesn't move) |
| **C-WB4** | `readOnlyHint == False` predicate (None leaks to read_only) | 1 failed / 9 passed | `test_deny_by_default…` ONLY (spec-equality agrees on the unperturbed surface — deny-by-default probe is the sole catcher) |
| **C-WB5** | HYBRID: derive all tools EXCEPT `lore_findings` (hardcoded mutating) | **10 passed — SURVIVES** | none → **MP-2** |

C-WB1 ("derive in TEST code, no prod helper") ≡ the RED baseline: the contract imports `from loremaster.server import partition_tools_by_posture`, so a test-only derivation fails the import → caught. Verified by the baseline.

**DRY verdict for C (priority #1):** the single-source is enforced — but by the EQUALITY pin (C-9), not the mutation proof. The mutation proof (C-6) proves the DERIVATION is live; C-9 (re-derives a spec partition each run and compares any surviving hand-list to it) is what stops a private copy from silently drifting. A correct-today hand-list is harmless because C-9 re-checks it every run; a disagreeing one is caught (C-WB2). The brief's framing — "flip a prod annotation → prod partition moves AND a private copy stays green = caught?" — resolves precisely: the mutation proof checks only that the derived set MOVES (it does not inspect a private copy); C-9 is the pin that catches a private copy. Together they close the *divergence* risk. **The gap is not DRY-divergence; it is liveness REACH (MP-2).**

---

## §D — D WRONG-BUILD RECORD (INSTRUMENT D / #295)

Baseline: reference D helper live. `mcp.call_tool` returns a TUPLE `([TextContent…], {result})` — verified empirically before writing the in-process build (my first D-WB2 extraction was buggy and returned `''`; P0 caught it — I re-ran with correct extraction).

| build | mutation | result | which pins RED |
|---|---|---|---|
| REFERENCE | wire-driving effect helper | **6 passed** | — (satisfiable) |
| **D-WB1** | marker-only helper (no effect leg) — the WB48 proxy observer | 1 failed / 5 passed | `test_the_helper_fails_a_run_then_refuse_build_on_the_effect_leg` (doesn't raise → the `pytest.raises` fails) |
| **D-WB3** | reads `effect_count()` BEFORE dispatch (stale 0) | 1 failed / 5 passed | same effect-leg pin (contract forces POST-dispatch observation) |
| **D-WB2** | IN-PROCESS `wire.mcp.call_tool`, never touches the wire (WB30 shape) | **6 passed — SURVIVES** | none → **MP-1** |

### §D.4 — the proposed pin for MP-1 (DEMONSTRATED, auth-free, discriminating)

A wire-drive spy: wrap the `wire` so `.call` is counted and `.mcp` still exposed; assert `.call` was invoked. Written to `loremaster/tests/test_cd_wiredrive_probe.py` in scratch:

```
$ uv run pytest loremaster/tests/test_cd_wiredrive_probe.py -q
..                                                                       [100%]
2 passed
```

- `test_proposed_pin_passes_the_wire_driving_reference` — reference helper drives `wire.call` ≥1 → PASS (positive control).
- `test_proposed_pin_catches_the_in_process_helper` — in-process helper drives 0 wire calls → the pin would RED it (the WB30 door).

So the "you can't pin wire-driving without auth" objection is FALSE — the pin is constructible in exactly the D contract's auth-free loopback setting.

**TRUST verdict for D (priority #2):** the contract does NOT falsely claim a coverage guarantee — its sweep-coverage tests use synthetic `pin_a…pin_d` sets and the `_SWEEP_ENUMERATION_MUST_BE_PROPERTY_DERIVED_AND_BOUND_STATED` note states the no-permanent-coverage bound plainly. The marker-only proxy (D-WB1) IS caught by the effect leg, and D-3 reproduces the byte-identical 0-vs-1 discriminator. The ONE trust defect is the claim-vs-check gap on wire-driving (MP-1): the step-1 docstring asserts a property the pins never verify.

---

## §RESID — residuals (every one gets an individual verdict; scope law — surfaced, not dropped)

- **R1 (C, bound):** `test_no_drifted_hand_list_survives_beside_the_derivation` keys on the two names `_MUTATING_TOOLS`/`_READ_ONLY_TOOLS`. A second/third-named hand-list (e.g. `_WRITABLE_TOOLS`) escapes it — the enumerating-the-named-set bound. **Verdict:** honest bound of a name-keyed pin, consistent with the design's positioning (INSTRUMENT 0's reach-attack is the standing guard). NOT a blocking missing pin; noted so a future author does not read the pin as exhaustive.
- **R2 (C, no-op):** the contract pins the helper's EXISTENCE + CORRECTNESS but not that any *production* or *test* code CONSUMES it. A build could ship `partition_tools_by_posture` as decoration this session (packet 39 consumes it later). **Verdict:** acceptable for this cycle's scope (the #291 test-side drift is fixed by C-9 regardless), but the helper is not proven to be on any live path until packet 39 — worth the lead knowing.
- **R3 (D, low):** the sweep primitive is tested only for `observed == derived` (D-4), never `observed ⊋ derived`. A stricter `==` implementation would pass the contract yet wrongly reject a healthy over-observation (the property is `observed ⊇ derived`). **Verdict:** low-value; the design's intent is subset semantics ("RED if any derived pin was not observed"). A one-line `test_coverage_passes_when_the_sweep_observed_MORE_than_derived` would pin it. Non-blocking.
- **R4 (D, API smell):** the helper is handed the whole `WireSession`, exposing `wire.mcp` — which is the in-process door MP-1 walks through. Passing only a `call` callable (not the whole session) would make the in-process path unreachable by construction. **Verdict:** a design suggestion that would make MP-1 unrepresentable rather than merely pinned; surfaced for the author, not required.

---

## §PROV — provenance & tooling

- Scratch tree: `/tmp/adv-cd-work`, built by `./scripts/scratch_copy.sh` (excludes poison, `uv sync --all-packages`, asserts provenance). Blessed verifier: `scratch copy VERIFIED`.
- `uv run python -c "import loremaster; print(loremaster.__file__)"` → `/tmp/adv-cd-work/loremaster/loremaster/__init__.py` (I am grading the scratch tree, not the original — #140). My reference `partition_tools_by_posture` confirmed live in it.
- ⚠ A bare `python -c "import loremaster"` (system python, no `uv run`) returned `__file__=None` (empty namespace package, #140 poison mode 3) — the pytest runs all use `uv run`, so they use the scratch venv. Receipt captured to avoid the trap.
- Instruments built (deliverables per brief-base §1): the reference C helper (§SAT), reference D helper (`_refusal_effect.py`, §SAT), and the MP-1 proposed-pin demo (`test_cd_wiredrive_probe.py`, §D.4) are all pasted/described inline here; the scratch tree is disposable, so this report carries them.
- Findings filed durably: **#346 (MP-1, D wire-driving), #347 (MP-2, C liveness reach)**.

## VERDICT: CONTRACT INSUFFICIENT

Both contracts are satisfiable (16 passed against reference) and strong on their headline properties — C's deny-by-default and single-source, D's effect-observation and honest no-coverage bound all hold and were empirically confirmed against multiple wrong builds. But two wrong builds survive, each a real "fixed it wrong" that reintroduces the very class the contract exists to kill:
1. **MP-1 / #346** — D waves through an in-process helper (WB30), which packet 39 will consume.
2. **MP-2 / #347** — C's liveness proof has reach 2/15; a hybrid hardcode passes (the reach-is-a-hidden-constant class, inside the contract built to kill it).

Each has a concrete, demonstrated missing pin. Route both back to CONTRACT.
