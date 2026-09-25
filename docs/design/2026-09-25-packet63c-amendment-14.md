# Packet 63c — ruling amendment 14 (sidecar-63c-2, 2026-09-25): FORK F1-ADMIT — the F-1 leg's admitted set

Amends amendment-13 §F-1 "Pin" (`fab659b`). Rules `REPORT-contract-63c-i-a-r4b-fix.md` §FORK F1-ADMIT
(working tree, uncommitted). Directive: `REPORT-lead-63c.md@20ebc49` (durable copy; this session's lore client
is still down — `Read`/`awk`, said so). HEAD at ruling: `20ebc49`.

## The defect is mine, and it is F-2's class reborn in the pin written to fix F-1
Amendment-13's literal leg — residue integers ⊆ `{len(shown)}` — reds every correct build that ALSO states a
remainder (`(first 2 of 2 ids shown, 0 more)`; `16 more` at birth 15 after F-2) or a legacy count (the r4b
docstring's own `"3 legacy rows"`). The brief REQUIRES the birth-15 remainder variant to be SAT because it is
F-2's scenario. I wrote a satisfiability defect into the pin whose purpose was to close a served-count lie,
one amendment after ruling that satisfiability defects are the one non-negotiable class. The fix author was
right to stop before any F-1 code, and right about (B). Askable form, again: *"does the correct build the
brief REQUIRES satisfy the shape I wrote?"* — I checked the build I imagined, not the one the brief names.

## Ruling — reading (B): the admitted set is the fixture's TRUE counts, derived per population
- **Property pinned (the CONSUMER-LAW form):** every integer the refusal serves is a TRUE count of one of the
  fixture's sets. Admitted = `{len(shown), count, count − len(shown), legacy_count, count + legacy_count}` —
  F-2's `fixture_counts` extended with `len(shown)` per population, exactly as amendment-13 directed and (B)
  builds. A served number that is not a true count of anything is the lie; a served number that IS a true
  count of something the reader can see is honest prose, whether or not I anticipated its phrasing.
- **The guard:** `birth ∉ admitted` wherever `birth ≠ len(shown)` — i.e. wherever N = the constant would BE a
  lie — with `below-cap`'s `legacy_count` moved off `birth` and `birth − count`. This keeps the only PLAUSIBLE
  wrong N (the constant) out of the admitted set in every population where it is wrong, so PXlie is RED in
  `below-cap` for every birth > 2.
- **Stated bound (accepted, named in the docstring):** a lie that coincides with a DIFFERENT true count —
  `(first 3 of 2 ids shown)` when `legacy_count == 3` — is admitted. No honest build derives N from the legacy
  count; the only plausible wrong derivation is the constant, and the guard excludes it. Re-open trigger: a
  served refusal found stating a sample size that equals another fixture count and not `len(shown)`.
- **Above-cap: IN.** ∀ populations, per THE QUANTIFIER LAW; there `shown = bound = birth`, so the leg cannot
  false-RED a correct build, and an unexplained exclusion of one population is exactly the guarded-invariant
  shape the packet keeps catching. The fix author's reading of "all three" as "not only perturbed-bound"
  is the intended one.
- D5's reworded message (`first {shown} of {count}`) and the builder-brief sentence (amendment-13 (i)) are
  unchanged: they teach the derivation; the leg admits every true count.

## §W
| # | item | change |
|---|---|---|
| 2 (amended) | F-1 leg: admitted set = the per-population TRUE counts with the birth guard; run in `below-cap`, `at-cap`, `above-cap`, `perturbed-bound`; bound stated in the docstring | as built to (B); commit it |

## §E
- Erratum against amendment-13 §F-1: the literal `{len(shown)}` set was unsatisfiable by the brief's required
  variant. Pattern across amendments 11, 12 and 13 — three pins in a row carried a SAT-class defect I wrote
  while closing another — and the lesson is one habit, not three: **before writing a pin's admitted shape,
  enumerate the correct builds the brief and the prior rulings already REQUIRE to be green, and check each
  against the shape.** A pin is a claim about a set of builds; I kept writing the claim before listing the set.
