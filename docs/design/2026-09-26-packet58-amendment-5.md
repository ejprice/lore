# Packet 58 — ruling amendment 5 (sidecar-64, 2026-09-26): FORK-2 — the guarded-CAS door enumerator's reach is keyed on a code SHAPE; the property goes RUNTIME (C) with a CLASS-keyed static index (B) cross-checked both ways; the builder constraint (A) is REJECTED; erratum against amendment 4's "re-reading" clause

Rules `REPORT-contract-58-r2.md` §FORKS FORK-2 (the author proceeds on A meanwhile — STOP that: A is
rejected below; the r2 revision lands C + B). Amends `…packet58-amendment-4.md` §"The reach question"
and `…packet58-amendment-3.md` §3/§6. The lead's flag is right and it is the instrument lesson's newest
row (CLAUDE.md, seventh defeat — a reach keyed on the raise SHAPE in an AST walk, added 63c am-24): the
enumerator sees a handler ONLY if its BODY re-reads inline (`_select*`); a claim written exactly as
decision 3 rules (`except TxnClaimLostError: pass`, the owner read AFTER the `try`) is invisible to
it, so the `_TYPED_CAS_CATCHES` entry I ruled in amendment 4 can never be FOUND by the instrument that
was supposed to list it.

## 0. Ruling in one screen

| option | verdict | why |
|---|---|---|
| **(A) constrain the builder to re-read INLINE** so the scanner sees claim | **REJECTED** | bends production code to an instrument's blind spot; and the shape it would force — a re-read inside the `except` — is the very door shape the invariant polices, installed on purpose to satisfy a scanner. A guard that dictates code shape gets routed around or switched off (the switched-off-scanner law). |
| **(C) RUNTIME: inject exhausted contention at every guarded-CAS seam and assert it propagates UNREAD; a lost race → the ledger's own verdict; coverage a CHECKED VARIABLE** | **RULED — the ∀** | the property is *"the code DOES not reinterpret exhausted contention"* — a fact about what runs, not about the text's shape (the askable form: *"is this a fact about the code's shape, or about what it DOES?"*). Execution is the only instrument that cannot be fooled by a spelling. |
| **(B) a STATIC index keyed on the caught CLASS's hierarchy — re-read presence IRRELEVANT** | **RULED — the reviewer-visible index, cross-checked with (C) both ways** | keyed on a TYPE fact the code owns, not on a body shape; it also finds what the runtime leg cannot drive by accident: a bare `except:` / `except Exception` around a CAS apply (a closure containing exhausted contention — a DOOR the `_select*` heuristic never saw). |

**The `_select*` re-read criterion is RETIRED as the door test** (amendment 4's "re-reading handler"
widening kept the shape key one level down — my erratum, fourth this packet). A door is now: *an
`except` clause on a guarded-CAS apply whose caught class closure contains `TxnContentionExhaustedError`*;
a typed catch whose closure is disjoint is SAFE-BY-TYPE. What a handler does in its body is the RUNTIME
leg's question.

## 1. (C) — the runtime ∀, pinned

- **The seam:** the ONE apply seam each ledger's CAS verbs call (`TaskLedger._apply` / `FindingLedger.
  _apply` / the briefs relate path — the same seam the R1 and atomicity pins already inject at). The
  fixture wraps it to raise `TxnContentionExhaustedError` on the CAS statement.
- **The property, ∀ CAS verbs:** the typed error PROPAGATES to the caller UNCHANGED — never re-read
  (a spy on the ledger's read seam records ZERO reads after the injection), never reinterpreted (no
  `IllegalTransitionError`, no `ClaimResult`, no `FindingNotFoundError`, no `already_acked`), never
  retried in the ledger (ONE apply call). Control per verb: the SAME wrapper raising the verb's OWN
  domain THROW (`claim_lost:` for claim; the transition/supersede/annotate/relate THROWs) → the verb's
  ruled verdict (claim: `ClaimResult(claimed=False)` via the post-CAS owner read — the ONE read
  observed; transition: `IllegalTransitionError` naming the fresh state; …).
- **Coverage as a checked variable (INSTRUMENT-0):** the DRIVEN verb set is asserted ⊇ the DERIVED
  CAS-caller set — every production caller of `TaskLedger._guarded_append_fragment` and
  `FindingLedger._guarded_append_fragment` (AST: call sites of the two shells, the one-producer pin's
  own derivation) ∪ the briefs relate door; a shell caller with no injection fixture reds by name (a new
  CAS verb tomorrow — 57's `assign`/release — cannot arrive undriven). The reverse: a driven name that is
  not a shell caller is a stale fixture → RED.
- **Bound, named:** a runtime gate is an invariant only over code it RUNS; the derived caller set is
  what makes reach a variable rather than a hidden constant; a CAS written WITHOUT the shell is the
  one-producer pin's catch (§3 of the kickoff), not this leg's.

## 2. (B) — the static index, re-keyed to the CLASS

- **Discovery:** for every `try` whose body (transitively, within the function) calls the apply seam —
  or, simpler and sufficient: every `try` inside a function that is a DERIVED shell caller — enumerate
  each `except` clause: a `Name`, a TUPLE of names, or bare. Resolve each name to its class object
  (import the store module; a name that does not resolve → RED, never skipped). Classify:
  - `issubclass(TxnContentionExhaustedError, caught)` for any caught class (bare `except` counts as
    `BaseException`) → **DOOR**: must be in `_GUARDED_CAS_DOORS` AND the same `try` must carry the
    `except TxnContentionExhaustedError: raise` clause ABOVE it (the existing rule);
  - otherwise → **SAFE-BY-TYPE**: must be in `_TYPED_CAS_CATCHES` (`tasks.py::claim_task`:
    *"TxnClaimLostError — a lost claim, served as ClaimResult"*).
  Both sets EXACT (a surprise handler reds; a stale entry reds). Re-read presence is NOT consulted.
- **Hierarchy pins** (amendment 4's, kept): `not issubclass(TxnContentionExhaustedError,
  TxnClaimLostError)`; `issubclass(TxnClaimLostError, TxnDomainRejectionError)`; a re-parenting flips
  the classification by derivation.
- **The five existing doors keep their entries** (their caught class is `SurrealStoreError`, whose
  closure contains exhausted contention — doors by the new criterion too); `annotate`'s deliberate
  fifth-door comment stands.
- **Discriminators (the scanner's own):** a synthetic shell caller with `except SurrealStoreError` and
  NO guard → door, RED; with the guard → door, GREEN; `except TxnClaimLostError` → safe, listed; a
  bare `except:` → door (the class the old heuristic could never see); `except (SurrealStoreError,
  ValueError)` → door; an unresolvable name → RED.

## 3. The cross-check — two layers, both directions (the F5 L1↔L2 idiom)

- every (B)-listed handler's function is (C)-driven (a listed door or typed catch no injection
  exercises → RED);
- every (C)-driven function has its handlers (B)-classified (a driven verb whose `try` the scanner did
  not enumerate → RED — the scanner's reach measured by the runtime set, and vice versa).
- **Mutation:** in the reference build, make claim catch `SurrealStoreError` instead of the typed class
  → (B) moves it to the door set with no guard → RED, AND (C)'s injection is re-read → RED (two
  independent instruments agree); make transition drop its guard clause → (B) RED, (C) RED.

## 4. Erratum (mine, amendment 4) and what the r2 author does now

- Amendment 4 §"The reach question" widened the enumerator *"to SEE typed catches … whose body
  re-reads"* — it retired the class blindness and KEPT the shape key. Same defect one level down, in the
  ruling written to fix it. The askable form, once more: *"what is the SET this guard covers, is it
  derived from a code SHAPE or from a fact the code OWNS, and would it still read as success if the
  guarded thing were spelled differently?"* The `_select*` key fails the third clause; the class closure
  and the runtime injection pass it.
- **r2:** STOP proceeding on A. Land (C) as the ∀ pin family, (B) as the re-keyed enumerator + the two
  exact sets, the cross-check, the discriminators. `test_retry_seam.py` is a pre-existing shared
  instrument (adversary P-3's) — its re-key is a held-patch-class edit if the lead so classifies it;
  the runtime family lives in 58's own files. The builder writes claim exactly as decision 3 rules.

## Discipline
- CLAUDE.md instrument lesson row 7 (runtime-refusal reach keyed on the raise shape) — applied to its
  sibling (a rollback-handler reach keyed on the re-read shape) before it became row 8.
- No code/tests/store touched; this doc only; no attribution trailer.
