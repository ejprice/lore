brief-base v10 read
brief project v7 read

# REPORT — adversary-eh (contract-adversary, INSTRUMENTS E #289 + H #290)

## SUMMARY BLOCK

- receipt: brief-base v10 read · brief project v7 read
- state: **done**
- **VERDICT: CONTRACT INSUFFICIENT** — one BLOCKER missing pin (priority-1 DRY/sharing).
- deviation: brief named `scripts/test_anchored_pattern_seam.py`; the real path is `loremaster/tests/test_anchored_pattern_seam.py` (found + read; it is E's structural reach backstop).
- P1 headline: **no wrong build of EITHER helper survives its own contract** (only 2 behaviourally-equivalent survivors). But a wrong build of the *overall #290 fix* — correct helper, extraction NOT done, TWO copies of the vacuity policy — passes the ENTIRE scripts contract set green.
- Packages considered: none — both deliverables are stdlib-only predicates (`dict` copy + f-string `\n`; `int == 0` guard). No library does or should do this. Matches design §INSTRUMENT H ("two-line stdlib predicate").
- Graded: e1dfa14 · HEAD-at-report: e1dfa14 · SAME
- decisions-needed: (1) the H `SystemExit`-vs-custom-exception fork is already open in the contract author's report — unchanged by me. (2) whether the owed E residual pin (Exemption door-field coverage as a checked variable) is wanted, or the design's checklist route stands.
- receipt pointers: satisfiability §Satisfiability · E `.match` mutation §Probe-E1 · helper batteries §Probe-E2/§Probe-H1 · **H DRY gap §Probe-H2 (the BLOCKER)** · reach tables §P1c · missing pins §Missing-Pins.
- provenance: `gated_ground.__file__ = /home/ejprice/adv_eh_scratch/scripts/gated_ground.py` (inside scratch, #140-clean); main tree never edited.

---

## VERDICT: CONTRACT INSUFFICIENT

The two contract files, graded in isolation, are **individually strong**: every genuine-defect wrong
build of `newline_forgery_variants` and of `refuse_vacuous_baseline` is killed, both are satisfiable
against a known-correct reference (E 9/9, H 8/8), and the E instance pin is mutation-proven against the
`.fullmatch`→`.match` reversion with its armour shown load-bearing.

The INSUFFICIENT verdict rests on **one BLOCKER**, and it is exactly the operator's priority #1
(DRY / leg 5): the property *"`refuse_vacuous_baseline` is the ONE implementation — `wrong_builds.main`
SHARES it, not re-inlines it, proven by MUTATION"* has **no RED home anywhere in the contract set.**
It exists today only as prose in the contract author's report. A build that adds the correct helper and
leaves `wrong_builds.main`'s inline copy intact (two copies of the policy — the #102/#120
routing-not-sharing trap) passes `test_harness_guards.py` AND `test_wrong_builds.py`, green. Measured below.

---

## P1b — QUANTIFIER TABLE (per invariant: ∀-over-inputs vs guarded-by-failure-mode)

| # | invariant | ∀ or guarded | receipt |
|---|-----------|--------------|---------|
| E1 | a finding number with a trailing `\n` is REJECTED at construction | **guarded-by-instance** in this contract (single fixture `"#188\n"`); ∀-over-prod-code in `test_anchored_pattern_seam` (derived roots incl. `scripts/`) | WB22 `.match` build reddens `test_a_finding_number_..._rejected` + integration pin; controls stay green (§Probe-E1) |
| E2 | helper yields exactly one `\n` variant per DECLARED field, touching only that field | **∀ over the declared fields** (helper iterates all); but the declared SET is caller judgement, not ∀ over Exemption's fields | WBE-b (`\n` every field) & WBE-e (trailing space) killed (§Probe-E2) |
| E3 | helper refuses an empty field list, and an absent field, loudly (`ValueError`) | **∀** (anti-vacuity + absence, both directions) | WBE-c (silent skip), WBE-d (`[]` on empty), WBE-g (`KeyError` not `ValueError`) all killed (§Probe-E2) |
| E4 | the matrix drives the REAL Exemption door field and it is rejected | **guarded-by-instance** (`["finding"]` only; no pin asserts `finding` = complete door set) | WB22 reddens `test_the_matrix_drives_the_real_exemption_door_field` (§Probe-E1) |
| H1 | a zero baseline is REFUSED (`SystemExit`) | **guarded-by-failure-mode** (`== 0`), boundary at 1 pins the threshold | WBH-a (no guard), WBH-c (`< 2`) killed (§Probe-H1) |
| H2 | a non-zero baseline PASSES and returns `None` | **∀** (negative control @315, boundary @1) | WBH-b (always raise), WBH-h (returns truthy) killed (§Probe-H1) |
| H3 | the refusal NAMES the interpreter AND the caller's cause_hint | **∀ over message content** | WBH-d (drops interpreter), WBH-e (drops cause_hint) killed (§Probe-H1) |
| **H4** | **`refuse_vacuous_baseline` is the ONE implementation; `wrong_builds.main` SHARES it (mutation)** | **GUARDED BY NOTHING — no pin in the set** | reference helper present + inline copy intact ⇒ `test_harness_guards.py`+`test_wrong_builds.py` **green, 9 passed** (§Probe-H2) — **the BLOCKER** |

Every guarded row above carries a receipt (a wrong build that walks the bad outcome through a door the
pin closes). Row **H4 is the exception the rule names**: the guarded outcome (two diverging copies of the
vacuity policy) has a live door and no pin — a MISSING PIN, not a receipt.

---

## P1c — REACH TABLE (per instrument the contracts introduce or rely on)

| instrument | reach = set of sites | DERIVED vs hand-list/judgement | coverage a CHECKED variable? | effect vs proxy | ONE-source proven by MUTATION | legs |
|---|---|---|---|---|---|---|
| **E: `newline_forgery_variants`** (new helper) | the fields the caller declares | **caller judgement** (`interpolated_fields` arg) — honest bound, design-declared | **NO** — contract drives `["finding"]` only; no pin asserts finding = Exemption's complete bare-door set | **EFFECT** — integration pin feeds the row to the *real* `Exemption`, which raises | N/A (new helper, single caller in-contract) | EMPIRICAL (built wrong helpers, drove them — §Probe-E2) |
| **E: #289 instance pin** (`.fullmatch` reversion) | `Exemption.finding`; structurally, every `$`-anchored `.match` in prod | **DERIVED** for the structural class — `test_anchored_pattern_seam._SCANNED_ROOTS = workspace_roots(include_skills=False)`, and it **contains `scripts/`** (verified: `scripts/gated_ground.py` is inside a scanned root) | **YES** for the structural class (`TestScanCoverage` + `_scanned_roots` derived from `[tool.uv.workspace] members`); **NO** for the per-field-fixture rule | **EFFECT** — rejects at construction (no render reached) | WB22 mutation proven (§Probe-E1) | EMPIRICAL |
| **H: `refuse_vacuous_baseline`** (new shared guard) | its call sites — intended: `wrong_builds.main` + any future N-vs-baseline harness | **single intended caller**; the contract does NOT verify `main` calls it | **NO** — nothing ties `main`'s guard to the shared helper | **EFFECT** — the helper raises on `0` (observes the count directly) | **NO — this is the gap.** Delete-the-call mutation proof has no home; inline copy can coexist | EMPIRICAL (helper+inline coexist, suite green — §Probe-H2) |

Legs run: all reach rows carry an EMPIRICAL leg (in-tree instruments were built/driven in scratch). The
E structural-backstop coverage claim was verified by construction-inspection (deriving `_SCANNED_ROOTS`
and testing containment of `gated_ground.py`), not merely read.

**Q4-flag-5 (priority 1, the DRY over-consolidation trap) — CLEARED.** `test_harness_guards.py` never
imports or references `pending_contract_gate`; `refuse_vacuous_baseline(measured_count, *, cause_hint,
interpreter)` is a distinct signature/subject from `pending_contract_gate`'s reader-anti-vacuity (which
guards a gate's OWN output — *"zero collected tests is a broken instrument"*, `ANTI_VACUITY_GUARDS`,
`scripts/pending_contract_gate.py`). The contract forces NO wrong merge of the two policies. Good.

---

## Missing-Pins

### MISSING PIN #1 — BLOCKER (priority-1 DRY / leg 5). The H sharing/extraction mutation proof has no RED home.

- **The test that should exist** (in `scripts/test_wrong_builds.py` — the BUILDER's file, per the design's
  scope split): a pin that DRIVES `wrong_builds.main`'s zero-baseline path (run `main` against a scratch
  where the baseline collects 0, or spy that `refuse_vacuous_baseline` is invoked with the baseline count)
  and **reddens when the `refuse_vacuous_baseline` call is deleted from `main`** — the design's own stated
  mutation proof (§INSTRUMENT H: *"delete the call in `main()` → the new covering pin reddens"*). Pair it
  with an anti-duplication pin: `wrong_builds.py` no longer contains a private inline
  `if not baseline: raise SystemExit(...)` — it CALLS the shared guard.
- **The defect it catches**: a builder adds a correct `_harness_guards.refuse_vacuous_baseline` but leaves
  the inline guard in `wrong_builds.main` (or wires nothing) — TWO copies of the vacuity policy, free to
  diverge (#102/#120 routing-not-sharing). Priority #1, and it is unpinned.
- **Reproduction (§Probe-H2)**: with the reference helper present and `wrong_builds.main`'s inline guard
  untouched, `pytest scripts/test_harness_guards.py scripts/test_wrong_builds.py` → **9 passed**. Nothing
  reddens. `grep -nE '_harness_guards|refuse_vacuous' scripts/wrong_builds.py` → no hits (inline copy still
  sole home).
- **Why it must be a RED pin before GREEN, not a report sentence**: lore's own packet-03b law — *"a
  mutation proof needs a home; a rider that lives two clauses from the claim it guards gets dropped."* The
  sharing property currently lives only as prose in the contract author's report. That is precisely the
  droppable rider. The contract AUTHOR's own file (`test_harness_guards.py`) is correct and in-scope; the
  gap is a HANDOFF the lead must close before the build wave.
- **Fail-safe alternative** (if the design prefers to keep the proof off `main`'s path): a structural
  adoption pin *inside* `test_harness_guards.py` (in the author's writable set) — assert `wrong_builds.py`
  source imports `_harness_guards` and no longer contains a bare inline `SystemExit` on `not baseline`.
  Cruder than a mutation proof (a call-site check, not sharing), but it fails-closed on "helper added, copy
  kept." Prefer the mutation pin; offer this only if the scope split forbids touching `test_wrong_builds.py`.

### MISSING PIN #2 — RESIDUAL / OPTIONAL (priority-3, E reach). Exemption door-field coverage is not a checked variable.

- **The test that should exist**: an Exemption-scoped field-fate pin — enumerate
  `dataclasses.fields(Exemption)`; for each field assert it is EITHER driven through
  `newline_forgery_variants` with a `\n` case the real `Exemption` rejects, OR provably `!r`-rendered in
  every validator message. Makes the door-field SET a checked variable **for `Exemption` specifically**
  (no generic AST derivation needed).
- **The defect it catches**: a FUTURE `Exemption` field that is bare-interpolated (a new line-injection
  door) but NOT `$`-anchored-`.match` — so `test_anchored_pattern_seam` is silent — and never given a `\n`
  case. The #289 forgery class through a new field, invisible.
- **Verdict: this is the honest bound the DESIGN explicitly declared** (§INSTRUMENT E part 2: the per-field
  rule "cannot be AST-derived generically… it rides the contract-adversary's malformed-input attack + a
  tdd-contract checklist clause"). NOT required by the design as written; offered as a strengthening. Does
  **not** on its own make E insufficient. The verdict rests on Missing Pin #1.

---

## Fixture-discrimination verdicts (every survivor gets an individual verdict)

- **E / WBE-a — `sorted(interpolated_fields)`**: SURVIVOR (9 passed). **Behaviourally EQUIVALENT.** The
  variants are independent and self-labelled by their tuple's field name, so declaration order is
  immaterial. The pin `test_it_yields_exactly_one_variant_per_declared_field` *appears* to check order
  (`== ["finding", "root"]`) but cannot — the fixture list is already alphabetically sorted, a
  parameter-value monoculture. Cheap non-blocking tweak if order is ever load-bearing: use an UNSORTED
  fixture (`["root", "finding"]`). Not a defect.
- **H / WBH-g — guard on `measured_count <= 0`**: SURVIVOR (8 passed). **Behaviourally EQUIVALENT.** The
  real input is `passed + failed + errors`, always ≥ 0, so `<= 0` ≡ `== 0`. Not a defect.
- All other 6 E wrong builds and 6 H wrong builds were KILLED (§Probe-E2 / §Probe-H1). "The rest look
  fine" is banned — each is listed with its kill count below.

---

## Satisfiability (C-DEF receipt)

Reference builds written in scratch (`/home/ejprice/adv_eh_scratch/scripts/_newline_matrix.py`,
`_harness_guards.py`), then:

```
=== SATISFIABILITY: E contract vs reference ===
9 passed in 0.03s
=== SATISFIABILITY: H contract vs reference ===
8 passed in 0.02s
```

Both contracts go **0-failed** against a known-correct build. The GREEN-today pins (E PART 1 — the #289
fix already at HEAD; H `TestTheZeroBaselineTrapIsReal` — pure arithmetic) are confirmed non-vacuous: E
PART 1 reddens under WB22 (§Probe-E1); `TestTheZeroBaselineTrapIsReal` is a self-contained control that
passes on the arithmetic it asserts (verified in the 8/9 collected each run).

**RED-at-HEAD honesty (P7):** the owed RED is genuine, not an import typo —
`E   ModuleNotFoundError: No module named '_newline_matrix'` and
`E   ModuleNotFoundError: No module named '_harness_guards'` at `e1dfa14`. Right reason: the deliverable
modules genuinely do not exist yet.

---

## Full probe record

### Provenance (#140)
```
gated_ground.__file__ = /home/ejprice/adv_eh_scratch/scripts/gated_ground.py
loremaster            -> /home/ejprice/adv_eh_scratch/loremaster/loremaster/__init__.py   (scratch_copy.sh receipt)
```
Scratch built with `./scripts/scratch_copy.sh /home/ejprice/adv_eh_scratch` (provenance-asserting). Main
tree `scripts/` never edited (`git status` shows only the two pre-existing untracked contract files).
`gated_ground.py` mutated only in scratch, restored byte-exact after each probe (`diff -q` clean).

### Probe-E1 — E PART 1 mutation proof (WB22: `.fullmatch`→`.match` in scratch `gated_ground.py`)
```
PASSED  test_match_and_fullmatch_disagree_on_a_trailing_newline        (regex control — stays green)
PASSED  test_the_same_finding_number_without_the_newline_is_accepted    (negative control — stays green)
FAILED  test_a_finding_number_with_a_trailing_newline_is_rejected       (instance pin — reddens)
FAILED  test_the_matrix_drives_the_real_exemption_door_field            (integration pin — reddens)
2 failed, 7 passed   → restored byte-exact
```
The pin discriminates the `.match` build for the RIGHT reason. **Armour is load-bearing (P2 perturbation,
scratch COPY of the contract):** strip the positive-control assertion `assert "not a finding number" in …`
AND de-embed the `\n` from `reopen_trigger` → the pin PASSES on the correct build (control) AND PASSES on
the WB22 build (BLINDED); the un-perturbed pin FAILS on WB22. So both the embedded trigger and the
positive-control are doing real work — the contract author built them correctly.

### Probe-E2 — wrong-build battery on `newline_forgery_variants` (E contract)
```
WBE-a  sort output fields (order)              9 passed            SURVIVOR (equivalent — see fixture verdicts)
WBE-b  append '\n' to ALL fields per variant   1 failed, 8 passed  killed
WBE-c  skip absent field (continue)            1 failed, 8 passed  killed
WBE-d  return [] on empty (no anti-vacuity)    1 failed, 8 passed  killed
WBE-e  trailing SPACE not newline              2 failed, 7 passed  killed
WBE-f  mutate the base mapping                 2 failed, 7 passed  killed
WBE-g  absent field raises KeyError not VErr   1 failed, 8 passed  killed
```

### Probe-H1 — wrong-build battery on `refuse_vacuous_baseline` (H contract)
```
WBH-a  no guard (return None always)           4 failed, 4 passed  killed
WBH-b  always raise SystemExit                 2 failed, 6 passed  killed
WBH-c  threshold < 2 (rejects a real 1)        1 failed, 7 passed  killed
WBH-d  raise but DROP interpreter              1 failed, 7 passed  killed
WBH-e  raise but DROP cause_hint               1 failed, 7 passed  killed
WBH-f  raise RuntimeError not SystemExit       4 failed, 4 passed  killed
WBH-g  guard on <= 0                           8 passed            SURVIVOR (equivalent — see fixture verdicts)
WBH-h  return truthy on non-zero (not None)    2 failed, 6 passed  killed
```

### Probe-H2 — the BLOCKER: sharing/DRY is unpinned
```
$ grep -nE '_harness_guards|refuse_vacuous' scripts/wrong_builds.py
  (no hits) — wrong_builds.main STILL has its INLINE guard (two copies of the policy)
$ pytest scripts/test_harness_guards.py scripts/test_wrong_builds.py -p no:randomly -q
  9 passed in 0.12s
```
Reference helper present + inline copy intact ⇒ the whole scripts contract set for these two concerns is
green. No pin ties `main`'s guard to the shared helper. `test_wrong_builds.py` at HEAD contains only
`TestTheCommittedWrongBuildsCanActuallyRun` (anchor-landing) — confirmed by
`grep -nE 'baseline|refuse|vacu' scripts/test_wrong_builds.py` → no hits. The owed delete-the-call
mutation proof has no home.

---

## Escalations / notes (nothing silently dropped)
1. **BLOCKER**: Missing Pin #1 (H sharing) → the lead must ensure `test_wrong_builds.py` gains the
   delete-the-call mutation pin + anti-duplication pin BEFORE the build wave. It is priority #1 and unpinned.
2. **Brief path inaccuracy**: `scripts/test_anchored_pattern_seam.py` does not exist; the file is
   `loremaster/tests/test_anchored_pattern_seam.py`. Found and used as E's structural backstop.
3. **Open fork unchanged**: the H `SystemExit`-vs-custom-exception decision is already in the contract
   author's report; my reference used `SystemExit` (as the contract pins). Not mine to settle.
4. **Optional strengthening**: Missing Pin #2 (E Exemption door-field coverage). Honest design bound;
   surfaced for an operator ruling, not asserted as a defect.
