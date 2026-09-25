# Packet 63c — ruling amendment 11 (sidecar-63c-2, 2026-09-25): narrow-delta r4a MP-A1/A2/A3, G3/PX2w, and the SHAPE of what follows

Rules `REPORT-adversary-63c-i-a-r4a.md` (narrow delta over `e80a854..bf77fb9`; INSUFFICIENT; uncommitted on
disk at ruling). Directive: `REPORT-lead-63c.md@a564edf` (durable copy; this session's lore client is still
down — `Read`/`sed`, said so). Amends amendment-9 MP-R4-5, amendment-10 C-4/C-5. HEAD at ruling: `a564edf`.

## The STOP-rule question, answered honestly: YES, two families are receding — so r4b closes them at the OUTERMOST boundary, not one level deeper
- **The fake-guard family** has moved five times: `except ImportError` (X3b) → `except Exception` (X3) → the
  submodule import inside the `try` (FXg) → a non-silent fallback inside the `try` (FXf) → a `try`-free
  `getattr` with a non-silent fallback (FXh). Every closure relocated the hidden constant — a spelling, then a
  node type, then a binding, then a handler. The adversary's clause (iii) ("no `Attribute`/`getattr`/`hasattr`
  naming the predicate") is the SIXTH deny-list entry, and `vars(lorerunes).get(…)`, `sys.modules[…]`,
  `importlib.import_module(…).is_legal_identifier` are the seventh through ninth. **When you catch yourself
  enumerating what is forbidden, you have already lost.**
- **The ownership family** has moved once: the registry seam (RS1) → the tool seam (RS1srv). One more inner
  seam exists in principle (any helper `_comms_register` calls after the registry returns).
- **The identity-text family did NOT recede:** TWR survives exactly as the instrument's threat model says it
  must, and its control is green. That pin's shape — allowlist the safe, keyed on the artifact — is the
  reason; it is also the shape the two receding families now get.
- **Ruling on the shape of what follows:** ONE r4b, carrying only closures whose shape ENDS a recession by
  construction (the safe set enumerated, or the effect observed at the outermost boundary), the non-negotiable
  satisfiability fix, and the two rows amendment-10 already parked on "r4b-if-any". It gets its narrow
  adversary delta — the 2026-07-28 law admits no "too small" — and that delta is graded under a pre-ruling
  written here so it cannot open an r4c: **any survivor of the fake-guard or ownership family after r4b is a
  pinned KNOWN BOUND with the honest-engineer threat model, recorded by the lead; a satisfiability defect is
  the one exception and is FIXED, verified by the delta author's own reference (its SAT leg re-run — the
  instrument that found it), not by a new round.** The builder is spawned on the r4b verdict either way.

## MP-A2 — SH1: the phrase leg refuses correct derived prose. FIX, non-negotiable; DELETE the phrase leg
- **Ruling:** delete the `N … shown` / `first N` / `showing N` phrase leg outright rather than strip the count
  from its residue. Amendment-10 C-4 already called it a convenience; the birth-value leg is what kills PX2
  (measured, adversary-r4a §4.1), and every patch to a phrase regex is another phrase a correct build can
  trip. What remains is one leg with one stated bound: *after stripping the named ids and the full count, no
  integer literal equals the constant's birth value* — ∀ over DIGIT spellings. PX2w (the bound in WORDS) is that
  leg's stated bound, accepted; the docstring and my amendment-10 C-4 sentence ("the ∀ half") are narrowed to
  "∀ over digit spellings" (erratum). No builder-brief phrasing constraint is needed once the leg is gone.

## MP-A3 — RS1srv: pin the GATING door at the OUTERMOST seam, in r4b; the refusal stays i-b
- **Ruling:** the end-to-end ownership-INVARIANCE pin rides r4b — through `AppContext.comms(action="register")`
  on the credentialed harness: keeper registers; joiner householded; joiner re-registers the keeper's agent
  WITH THE SAME ROLE → `owner_principal`, `owner_agent`, `scope` byte-identical; controls: foreign principal
  denied (SF-63-1), the joiner's fresh name created owned by the joiner. The adversary's C-3 probe minus its
  recording is the test (it exists; the harness exists). GREEN at HEAD and on a correct build (no RED-receipt
  change), RED on RS1srv.
- **Why this ends the ownership recession rather than relocating it:** a pin that observes the ROW after the
  whole tool call has returned covers every inner seam by construction — registry, tool, render, any helper
  — because there is no seam outside the call. It asserts DATA invariance only, so it does not cross the
  i-a/i-b line; amendment-10 C-3's served DENIAL (which would also kill RS1srv) stays i-b's, with its
  adversary and the #467 battery row.
- The r4a author's KP-RS1 (registry seam) stays: it is the unit-level twin, and it is what tells a builder
  WHICH seam broke.
- On "no live production defect — MEDIUM": the receipt behind my statement is amendment-1 E3's measurement
  (2026-09-24): the running `lore-lore` image was built 2026-08-17, before pkt 62 (`66b5fa4`, 2026-08-24), and
  production `:18500` carries no `owner_principal` column; the plan is commit-only until pkt 65. HIGH on that
  measurement; the adversary was right not to touch `:18500` to re-derive it.

## MP-A1 — FXh: close the fake-guard family with an ALLOWLIST, in r4b; obfuscation is the pinned bound
- **Ruling:** clause (iii) in ALLOWLIST form, not the adversary's deny-list form. In `_comms_fakes.py` the name
  `is_legal_identifier` may appear in exactly two shapes: (1) the ONE module-top `ImportFrom` (from `lorerunes`
  or a submodule — R-A (ii)), and (2) `Call` nodes whose func is the bare `Name`. Any other occurrence — an
  `Attribute` with that `attr`, ANY string constant equal to it (which is how `getattr`, `hasattr`,
  `vars().get`, `sys.modules[…]`, `importlib` lookups all spell it), a `Name` that is not a call — is a
  violation naming `file:line`. Positive controls: FXh (`getattr` + fallback), X3d, FXf, FXg, a `vars(…)`
  read; negative controls: the honest post-build fake; R-A (ii)'s submodule import; an unrelated `try`.
  The safe set is two shapes; everything else is denied — the family cannot recede again because there is
  no list to extend.
- **The pinned bound (threat model in the instrument):** an OBFUSCATED name (`"is_legal_" + "identifier"`,
  `"".join(…)`) is adversarial-only and survives; KNOWN BOUND with #138's trigger, same message shape as KB-2.
- **Errata:** the shape pin's docstring ("cannot outlive its premise in ANY spelling") and my amendment-9
  MP-R4-5 ("that one shape subsumes … FXf (any fallback — the `try` is the tell)") both over-claimed; FXh
  falsifies both. Narrowed to the allowlist sentence above. The effect pin (MP-R4-4 reach) stays for the
  silent-skip property; FXhS proves it fires.
- **Amendment-10 C-5 is NOT widened in r4b (correction to "r4b-if-any"):** the allowlist above is
  fake-specific by construction — the mutation pins in other test modules legitimately name the predicate as
  a STRING (`patch_shared_object_everywhere(monkeypatch, "is_legal_identifier", …)`), so a tree-wide form
  would red the instruments that prove sharing. Reach stays `_comms_fakes.py`, stated, with i-b's new test
  doubles as the trigger (amendment-10 C-5's second branch). Corrected here so the r4b author does not build
  the contradiction.

## G3 · C2 · PX2w · TWR
- **G3 — CLOSE in r4b (fixture growth):** `"a-"`, `"a_"`, `"00"` join `_LEGAL_IDENTIFIER_WITNESSES` — the
  trailing-separator and all-digit axes. The corpus is a HAND-LIST of boundary witnesses and its docstring says
  so, with the header sentence amendment-9 R-2 already narrowed; a derived corpus (class members × positions
  from `AGENT_NAME_PATTERN`) would close the axis class outright but multiplies every corpus-parametrised store
  leg — rigor-to-importance says no for a footer gate. Trigger for deriving it: a fourth witness axis found by
  an adversary.
- **C2 — CLOSE in r4b:** amendment-10 C-2's "r4b-if-any" has its "any"; KP-C2 (real + fake, absolute) is the row.
- **PX2w:** the stated bound of the surviving leg (above). Docstring only.
- **TWR:** the KB-2 bound working, control green. Nothing.

## §W — r4b (one addendum; one narrow delta under the pre-ruling above; then the builder)
| # | item | source | class |
|---|---|---|---|
| 1 | delete the PX2 phrase leg; docstring "∀ over digit spellings"; PX2w named as the bound | MP-A2 / PX2w | **SAT fix — non-negotiable** |
| 2 | end-to-end ownership-invariance pin through `AppContext.comms(action="register")` (probe minus recording) | MP-A3 | **GATING** |
| 3 | fake predicate ALLOWLIST clause (two shapes) + controls + obfuscation KNOWN BOUND; both over-claiming sentences narrowed; C-5 stays one-file | MP-A1 | **GATING** (the builder's granted edit is unchanged) |
| 4 | `"a-"`, `"a_"`, `"00"` witnesses; corpus docstring states the hand-list bound + trigger | G3 | fixture growth |
| 5 | C-2 registry-seam row, real + fake, absolute (KP-C2) | C2 | row |
| — | i-b: the served refusal (amendment-10 C-3) + #467 battery row; R-6's metadata columns are covered by that refusal | — | i-b |
| — | lead: record any post-r4b survivor of the two families as a KNOWN BOUND per the pre-ruling; no r4c | — | process |

## §E — operator-visible
- **The pre-ruling that caps rounds** (§1): after r4b's delta, the two receding families become pinned bounds by
  the lead's hand under my written authority; only satisfiability defects are still fixed. This is the
  amendment-6 STOP-rule applied a second time with a tighter cap, because the first application did not stop
  the recession — it moved one level. Flagged because it caps rigor on a security-adjacent seam; my reading is
  that the remaining doors are adversarial-only (obfuscated names; a decider hidden in a production shim), and
  that the seam's real boundary — the tool call — is now pinned at its outermost edge.
- Errata: amendment-9 MP-R4-5's "any fallback"; amendment-10 C-4's "the ∀ half"; amendment-10 C-5's
  "r4b-if-any" widening (withdrawn — it would contradict the sharing pins).
