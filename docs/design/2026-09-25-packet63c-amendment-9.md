# Packet 63c — ruling amendment 9 (sidecar-63c-2, 2026-09-25): adversary-r4 new-class survivors, residuals R-1/R-2/R-4, and the KB-5 correction

Rules `REPORT-adversary-63c-i-a-r4.md` (verdict INSUFFICIENT with NEW-CLASS survivors, no live production
defect; graded `e80a854`; committed `86379a4`). Directive: `REPORT-lead-63c.md@86379a4` (durable copy; this
session's lore client is still down — `Read`/`sed`, said so). Amends amendment-6 MP-3 and amendment-8 KB-5.
Under amendment-6 §5, new-class survivors are ruled here before any round; every closure below is a row,
a reach fix, or a restored pin carried by the ONE r4a addendum, which then gets its narrow adversary delta
(operator law 2026-07-28) before the builder. No r5.

## Two errata first, because two of the survivors are mine
- **Amendment-8 KB-5's premise is FALSE.** I wrote *"the real writer is pinned mint-once on it (r2's
  `test_re_register_does_not_restamp_the_governed_triple_mint_once`)"*. That pin re-registers with the SAME
  principal, so a build that re-stamps writes identical bytes and passes; MP-F's rows are UNSTAMPED, so a
  build that re-stamps only stamped rows never touches them. Mint-once was pinned ∀ rows and never ∀ callers —
  THE QUANTIFIER LAW, and I cited a pin for a property it cannot see. RS1 is the receipt.
- **Amendment-6 MP-3 deleted a pin that observed a DIFFERENT property.** I called the r3 presence pin *"a proxy
  beside its effect twin … decoration that reads as coverage"*. Wrong: the effect pin observes *silent skip*;
  the presence pin observed *the guard outlives its premise*. FXf (a guard kept with a non-silent fallback)
  separates them, and my deletion is what opened it. The DUAL law I keep citing — a delete/replace ships with
  a removed-behaviour inventory — applied to my own ruling, and I did not run it.

## MP-R4-1 — RS1: a stamped row re-registered from a DIFFERENT consistent pair (real writer). GATING; close in r4a
- **Ruling:** ruling §2.2 row 2 stands as written — a re-register leaves `owner_principal`, `owner_agent`,
  `scope` UNTOUCHED — and is now pinned **∀ callers**: register `(alice_pid, K)`, re-register `(bob_pid, K)` (a
  householded joiner — reachable through `_comms_register`, which admits any principal householded in the
  session keep) → `("re-registered", owner_principal = alice_pid, owner_agent = self, scope = keep:K)`, byte-
  identical row. KP-RS1's shape, with the ABSOLUTE real-side expectation. Security-adjacent (an ownership
  takeover door through an ordinary tool call), so it lands before the builder: the builder's docstring
  sentence "a re-register does NOT re-stamp it" extends to *"from ANY caller, including a different
  householded principal"*.
- **MP-R4-6 (FX2, the fake's twin) closes in the same row:** the KB-5 parity row carries the absolute
  expectation on the real side and `fake == real` on top — a `real == fake`-only row passes RS1 + FX2 together,
  which is exactly the fixture-cannot-discriminate class.

## MP-R4-3 — G1: a NARROWING conjunct at the SKIP gate. SAME-CLASS; close by fixture growth in r4a
- **Ruling:** the legal side gets what the hostile side already has — ONE corpus. `_LEGAL_IDENTIFIER_WITNESSES`,
  beside `_HOSTILE_IDENTIFIERS`, spanning the language's boundary points: length 1 (`"a"`), digit-leading
  (`"0z"`), underscore (`"a_b"`), hyphen (`"a-b"`), the cap (`"a" * 64`). The SKIP-gate legs (baseline "looked
  up exactly once") and the register accept-control parametrise over it. G1 dies on the cap witness; a
  narrowing conjunct on any other axis dies on the witness that carries it. Parameter-value monoculture on the
  LEGAL side is the same defect as on the hostile side, and it gets the same cure.
- **R-2 (the header's "whatever it spells"):** narrowed to what the legs observe — *a decider that WIDENS (the
  hostile corpus), REPLACES (the mutation), or NARROWS on any axis a legal witness carries*. A ∀ over spellings
  is not something fixture witnesses can deliver, and the sentence must not claim it.

## MP-R4-4 — FXg: the effect pin's simulation reaches ONE binding. Reach fix in r4a (the builder's edit is unchanged)
- **Ruling:** the effect pin removes the predicate at EVERY `lorerunes*` module-level binding
  (`module_level_bindings_of(lorerunes.is_legal_identifier)`, anti-vacuity ≥ 1 home found) — KP-FXg's shape,
  layout-independent (R-5). A simulation that reaches one binding of a shared object is the instrument lesson
  inside the instrument: its reach was a hidden constant (`lorerunes`, the package) rather than the derived set.

## MP-R4-5 — FXf: restore the presence pin, property-shaped. Reading (b) — a DUAL loss of MY rewrite
- **Ruling:** the presence pin returns BESIDE the effect pin, but not as the r3 spelling (`except ImportError`).
  Allowlist the safe post-build state: once `lorerunes.is_legal_identifier` exists, `_comms_fakes.py` has a
  module-level `ImportFrom` of it from `lorerunes` AND no `ast.Try` node wraps any import from `lorerunes*`.
  That one shape subsumes X3 (`except Exception`), X3b (the ruled spelling), FXf (any fallback — the `try` is
  the tell), FXg (the submodule import inside a `try`), and a bare `except:`. The effect pin (MP-R4-4 fixed)
  stays for what the shape pin cannot see: a guard built without `try` (a `getattr(…, None)` read). Two pins,
  two properties, both named in their docstrings — the removed-behaviour row amendment-6 owed.
- The builder's granted edit is unchanged: delete the guard, import at module top.

## MP-R4-7 — PX2: a PROSE twin of the sample bound. NON-GATING; r4a
- **Ruling:** in `R_Q5_1[perturbed-bound]`, after stripping the named ids and the full count, the reason
  carries no integer literal equal to the constant's BIRTH value (read from the constant BEFORE patching —
  derived, never `\b10\b` in the test) — and if it states a sample size at all, that number is the PATCHED one.
  The P8d rule inside the served refusal: prose that describes the bound is DERIVED from the constant
  (`f"first {sample_size} ids shown"`) or absent, never restated.

## R-1 — r4's MP-4 premise pin is REDUNDANT and WEAKER than packet 07's: delete it, cite the stronger pin
- **Ruling:** delete r4's premise pin. The premise ("the unswept emitters emit no relation") has been observed
  since packet 07 by `test_floor_calibration_schema.py::TestTheDdlDecisionRuleIsEnforcedMechanically::
  test_this_slice_contains_neither_a_relation_table_nor_a_sequence` (+ `…_every_table_definition_is_IF_NOT_EXISTS`),
  which sweeps BOTH unswept slices and kills R5 AND R5b — where r4's `(edge, endpoints)` key lets R5b through.
  The FORK-A bound's docstring cites the packet-07 pin by name as the premise's observation. Amendment-6 MP-4
  and amendment-8's "made honest" sentence were both written against a scoped-file-set artifact: **a survivor
  is a CONTRACT survivor until the full suite is run on it** — the lead's adversary brief carries that line
  (the r4 adversary's §4.5 is the shape). KP-R5b-live (ENFORCED silently dropped on the test store when a
  later slice re-defines a swept relation) stands as the reason the packet-07 pin matters — a live receipt
  for a hypothetical build, filed with the finding the lead opens when lore returns.

## R-4 — MP-2's failure text; R-3 — noted
- R-4: the perturbation's failure text says *"does not read `_REFUSAL_ID_SAMPLE_SIZE` at CALL time"* (true of
  both the restated literal and a def-time capture), not *"a restated literal: two sources"*. PROSE.
- R-3: the stale-exemption check keys on path only — moot with one entry; the day a second exemption enters the
  same file the key becomes (path, binding). Noted in the pin's docstring as the trigger.

## §W — the ONE r4a addendum (amendment-8 rows + these), then the narrow adversary delta, then the builder
| # | item | source | class |
|---|---|---|---|
| 1 | KP-RS1 real-writer pin (absolute expectation) + KB-5 parity row with absolute real side | MP-R4-1 / -6 | **GATING** |
| 2 | `_LEGAL_IDENTIFIER_WITNESSES` corpus; SKIP-gate legs + accept-control parametrised; header sentence narrowed | MP-R4-3 / R-2 | GATING (fixture growth; the gate legs are already GATING) |
| 3 | effect pin removes the predicate at EVERY `lorerunes*` binding | MP-R4-4 | GATING-adjacent (pin reach) |
| 4 | property-shaped presence pin restored (top-level ImportFrom; no `Try` around a lorerunes import) beside the effect pin | MP-R4-5 | GATING-adjacent |
| 5 | PX2 prose-twin leg in `R_Q5_1[perturbed-bound]` | MP-R4-7 | NON-GATING |
| 6 | delete r4's premise pin; FORK-A docstring cites the packet-07 pin | R-1 | NON-GATING |
| 7 | `"fixer.b"` corpus entry (kills G2) · KB-2 negative control (TWR is the bound, measured) · KB-3/KB-4 prose | amendment-8 | as ruled |
| 8 | R-4 failure text; R-3 trigger sentence | prose | PROSE |
| — | adversary brief line: "a survivor is a CONTRACT survivor until the full suite is run on it" | lead | — |
| — | builder brief: re-register docstring extends to "from ANY caller" | lead | — |

Everything above is a row, a reach fix, or a restored shape pin — no new instrument, no new class of gate.
The STOP-rule (amendment-6 §5) holds: after r4a's delta, any further door in the identity class is a pinned
bound; a new class comes here first.

## §E
- Both errata above are mine and are the lesson of this packet in one sentence each: *cite a pin only for the
  property its fixture can SEE*, and *a ruling that deletes a pin owes the removed-behaviour row it demands of
  builders*.
- No operator-visible scope change: RS1 is a takeover door in a HYPOTHETICAL build, closed by pinning the
  ruling as already written; production at HEAD does not carry it (adversary §1/§2).
