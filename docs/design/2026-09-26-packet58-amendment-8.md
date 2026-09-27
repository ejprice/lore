# Packet 58 — ruling amendment 8 (sidecar-64, 2026-09-26): the r2 adversary — the packer IS `more_itertools.constrained_batches` (erratum), the THIRD-STRIKE property for the heal, the CAS population moved to the STATE (driver-seam runtime ∀ + a call-graph static index), F2/F3/F4/F11 as generated pins under existing rulings, the esc1 owner, and am-7 folded into r3

Rules `REPORT-adversary-58-r2.md` (`821be62`, verdict INSUFFICIENT — 7 MISSING PIN · 3 reach · 2 SAT
FRAGILITY · 1 P-PKG) per lead-63c-2's Task 17. Loop status, stated for the operator (CLAUDE.md *Fix the
CLASS* rule 5): 58's contract↔adversary loop is at **round 3**; rounds 1–3 share ONE property on the heal
(chunk sizing: r1 → am-2 defect → am-3 → N3) — the third strike — so this amendment routes the PROPERTY,
not another instance fix, and r3 must land it as GENERATED pins. Amends am-3 §1/§6, am-5 §2–§3, am-7 §1–§3.

## 0. The rulings in one screen

| # | item | ruling |
|---|---|---|
| **PKG** | the heal packer | **`more_itertools.constrained_batches(items, max_size=TXN_STATEMENT_HARD_CAP, get_len=<the ONE counter>, strict=True)`** — the lead's ruling, ratified: the adversary read AND ran the installed source (11.1.0 — `reached_size = item_len + batch_size > max_size` → yield the batch, then append; `strict=True` raises on a single over-size item). `more-itertools` becomes a DECLARED direct dependency (pre-approved install; today it is only transitive). **ERRATUM, mine (am-3 §1 and its `Packages considered: none`):** *"arithmetic over compose's own count"* asserted a limitation without reading an installed API — brief-base §1's named failure, verbatim. §1 |
| **CLASS** | the third-strike property | **CONFIRMED, sharpened to the STATE:** *∀ straggler populations whose heads resolve, ONE boot heals ALL of them — `count == |population|`, every sent transaction ≤ `TXN_STATEMENT_HARD_CAP` — where each row's WEIGHT is its OWN composed statement count from the ONE shared counter, computed by building the row's fragments ONCE (carried, never rebuilt).* The lead's framing adds nothing false; the sharpening is that CONVERGENCE is the property (the cap alone is already enforced at the state by `compose`'s refusal — the defect was never an over-cap chunk landing, it was a refused chunk never converging). Domain = the straggler SHAPE space × scale; pinned by a GENERATED sweep (§2). |
| **(1) F5/F8/N20** | `try`-shape and `_apply`-shape SAT fragility; the helper-applied escape | **Move the ∀ to the STATE — the driver seam — and derive coverage at runtime; the static index is reviewer-visible only and learns the missing catch FORMS.** Neither instrument may demand a literal `try` or a direct `self._apply` in the verb (am-5's rejected option A, twice). Not a receding reach: the sequence ENDS at the chokepoint every store write passes through. §3 |
| **(2) F3** | which logger the claim-loss pin covers | **(b) — ANY lore logger.** The principle is *"a routine loss is not an alarm"*; an alarm from `loremaster.tasks` is the same switched-off scanner. Pin filter = `loremaster` (all lore loggers), nothing ≥ WARNING for the seven losers; INFO/DEBUG allowed. |
| **(3) F2 · F4 · F11** | tier ∀ · mixed-chain row · RELATE sharing | F2: a missing pin under am-6/am-7 — GENERATED over the tier table's classes. F4: **skip the WHOLE row** (the row is the unit), one WARNING per unresolvable ENTRY, the row uncounted — a missing pin under am-3 §5, generated over row shapes. F11: a missing pin under am-1's rider — GENERATED over every RELATE-composing verb. §4 |
| **(4) esc1** | `scripts/esc1_write_path_cycle_closure.py`, red since #174 | **Owner = 58's builder** (confirming r1 §FLAGS 1): 58 rewrites the exact write paths it exercises; the script is RE-KEYED to the current contract (its scenario re-derived under #174's sentinel and 58's re-anchor) or ARCHIVED with a DUAL header — never left red, never deleted silently. §5 |
| **am-7** | folded into r3 | the §HELD scanner is a DELTA over 63c-i-a's a28b scanner (partition, moves, union pin) PLUS this amendment's §3 (catch forms, the call-graph static set, the driver-seam runtime ∀). §6 |

## 1. The packer — erratum and the ruled mechanism

- am-3 §1 wrote *"ONE statement-counting function … the heal packer is GREEDY"* and its `Packages considered`
  said *"none (the packer is arithmetic over compose's own count)"*. The adversary's P-PKG table read
  `more_itertools.constrained_batches` from the installed source and RAN it: the greedy close-before-
  overflow and the strict single-item refusal are exactly am-3's two clauses. I asserted a limitation I
  had not checked — the P-PKG failure brief-base §1 names (*"a `bespoke` verdict with an empty read-column"*).
- **Ruled shape:** `items` = `(row, fragments, weight)` triples built ONCE per straggler (the fragments
  are carried into the chunk — never rebuilt — so `get_len` returns the stored weight and the packer never
  re-prices); `get_len` = the ONE counter `_composed_statement_count(fragments)` the supersede accessor
  also consumes (am-3 §1's sharing pin stands: pad the shell → both move); `max_size` =
  `TXN_STATEMENT_HARD_CAP`; `strict=True` → its `ValueError` is caught at the ONE call site and re-raised
  as the typed `StragglerHealPackerError` (loud boot failure — F10's rider, now pinned, §2). The per-row
  weight INCLUDES the row's own edge DELETE(s) and RELATE(s) — a row naming two superseded blockers with
  distinct heads weighs more than a one-blocker row (N3's exact defect: pricing every row at one unit).
- **DRY row (the builder's):** `constrained_batches` → **REPLACE** the hand-rolled packer; the counter is
  in-house (REUSE); `more-itertools` added to `pyproject.toml` dependencies (declared, pinned by the
  lockfile; a `Packages considered` line that reads "none" for a specified mechanism is itself the defect
  the adversary flagged — the builder writes the table).

## 2. The property, generated (the r3 fold's ONE pin family for the heal)

- **Generated sweep — the domain is the straggler SHAPE space, enumerated in the test from the cost
  ingredients the heal itself has:** per row, `entries ∈ {1, 2, k}` superseded blockers; heads
  `{distinct, shared}`; head `{absent, already present}` (no RELATE); `{healable, phantom, cyclic}` per
  entry; populations `{pure, mixed cost classes}`; scale `{cap−1, cap, cap+1}` items in EACH class where
  "cap" is the packer's own prediction for that class (never a literal). For every generated population:
  one boot → `count == |healable rows|`, every sent transaction's statement count ≤ the cap (a `compose`
  spy records each), unresolvable rows skipped whole and recorded (§4 F4), second boot silent.
- **The edge (F10):** ONE row whose own weight exceeds the cap (1700 blockers superseded by one head; the
  adversary's 1.6 s fixture) → `StragglerHealPackerError` names the row and its weight, the boot FAILS
  LOUD (am-3 §2: a packer bug / an impossible row is a store-class fault), nothing changed; a silent skip
  (N19) reds.
- **Kill set carried from r2:** N3 (per-unit pricing) → the two-blocker-distinct-heads class at scale;
  N15 (post-check overflow) → the `compose` spy; AM2L → the multi-blocker class; N14 stays NOT A DEFECT.
- **Litmus (CLAUDE.md):** *"if the grader found one more shape tomorrow, would the sweep already cover
  it?"* — yes iff the shape is expressible in the enumerated ingredients; a new ingredient (a new
  per-row statement) is a change to the heal's fragment builder, which the sweep reads from (the
  ingredients are DERIVED from the builder's own branches, asserted non-vacuous per ingredient).

## 3. F5 / F8 / N20 — the CAS population, enforced at the STATE

- **The defect class, lifted:** three instruments keyed on code SHAPE in three rounds — `_select*` (r1),
  the `try` node (am-5 (B)), the literal `self._apply(` in the verb body (r2's `derive_cas_verbs`) — and
  each round's correct-but-differently-spelled build was RED (F5: `contextlib.suppress`, a house idiom
  used 10× in production; F8: an extracted helper) while a wrongly-spelled NEW door was GREEN (N20: a
  helper-applied verb in neither layer; F6: a door in `messages.py` outside a hand-listed module set).
  **The askable STOP-rule question — *is this reach receding one level deeper every round?* — answers
  YES for the static shape keys. The rule's consequence is not "pin a bound": it is CLAUDE.md rule 2 —
  enforce at the STATE, the one point every violation must pass through.** That point exists: every store
  write reaches `execute_transaction` / `run_query`, and the R4 runtime gate (`_sdk_guard`) already sees
  every SDK call with its calling frames.
- **Ruling — the ∀ is a DRIVER-SEAM fault injection with runtime-derived coverage:**
  1. the injection sits at the driver seam (`execute_transaction` / `run_query`), not at `_apply`: on a
     flagged call it raises a fresh `TxnContentionExhaustedError` INSTANCE;
  2. the assertion is IDENTITY: the exception that reaches the test's call boundary `is` the injected
     instance (a passthrough re-raise preserves identity; a reinterpretation — a re-read, a `ClaimResult`,
     a domain error `from` it, a swallow — does not);
  3. coverage is a CHECKED VARIABLE derived at RUNTIME: the set of production functions observed on the
     stack between the test's entry and the driver during the suite (the `_sdk_guard` frame idiom, F5 L2)
     — every observed store-writing entry point is driven with the injection at least once; the static
     side (below) must be ⊆ the observed set (a call-graph CAS verb nobody drives → RED) and the observed
     set ⊆ the static call-graph set (an observed writer the graph did not derive → RED: the graph's
     blind spot, named);
  4. the ledger's OWN verdict per verb (a THROW'd domain rejection → `ClaimResult` / `IllegalTransition
     Error` / the heal's WARNING) stays the control leg, injected the same way with the verb's own THROW
     class.
  This does not care whether the catch is a `try`, a `suppress`, an `except*`, an alias, or a helper —
  the property is about what reaches the caller. N20's verb is caught the moment it is DRIVEN (and it
  is driven, or the static side reds it as undriven).
- **The static index (am-7's (B)) stays reviewer-visible and learns the catch FORMS — it is no longer
  the ∀:** its domain gains `ast.TryStar` handlers and `with contextlib.suppress(<names>)` (a `With`
  whose context expression resolves by import to `contextlib.suppress`; each name resolved by import;
  classified by the same closure predicate; the enclosing function is the handler's site); the
  `derive_cas_verbs` population is re-derived from the CALL GRAPH — a function is a CAS verb iff some
  same-module transitive call path from it reaches BOTH the shell and a function that reaches the driver
  (F8's proposal; a synthetic verb→shell + verb→helper→driver discriminator is DERIVED). No hand-listed
  module set survives (F6): the graph is walked over the whole production tree.
- **Consequence for BC-r2-3 / BC-r2-9:** DELETED — a builder may write the typed catch as `try` or
  `suppress` and may extract the chunk apply into a helper; no instrument may dictate the shape. The
  `floor_calibration` fence door (F7) is COVERED by the driver-seam ∀ the moment its fence tests are
  driven with the injection — if they are not, the static graph reds it as undriven and the lead routes
  a one-test driver to that module's owner (am-7 §3 item 2's shape).

## 4. F2 · F4 · F11 — missing pins under existing rulings, generated

- **F2 (the WARNING tier ∀):** under am-6/am-7 the tier table is keyed by CLASS; the pin is GENERATED over
  the table's rows — for each class, drive the verb that produces it to its rollback and assert exactly
  one `store.transaction.rolled_back` at that class's tier; plus the completeness assertion (keys == the
  classifier's producible classes) — am-7 §4's pins, now with PA1 (supersede lost race) and PA2 (R1
  straggler) as two generated instances, and the heal chunk's rollback level as a third.
- **F4 (the mixed row):** RULED — the ROW is the unit of the heal: a row with ≥ 1 unresolvable chain
  (phantom or cyclic head) is SKIPPED WHOLE (byte-identical after the boot), UNCOUNTED, and RECORDED with
  ONE WARNING PER UNRESOLVABLE ENTRY (am-3 §5's `blocker_id` per record — the adversary's open question,
  answered: per entry, because the operator heals per pointer). Why whole-row: a half-healed row is
  rewritten under a record that says it was skipped, and `count` over-claims (Leg 1); the entry-level
  rewrite is one statement per row, so partial rewriting is also a second statement shape. Generated over
  `{one bad, bad+healable, two bad, healable+healable}` × `{phantom, cyclic}`.
- **F11 (RELATE sharing):** a missing pin under am-1's rider *"the SAME re-anchor fragment the supersede
  uses"* / MP13 — GENERATED over every verb that composes a `blocks` RELATE (the MP9 `_apply`-caller set:
  `create_task`, `create_many`, `supersede_task`, `_reanchor_stragglers`): spy `_relate_fragment` and
  `compose`, every composed `RELATE` statement was produced by the spy; mutation: change the fragment's
  param naming → every verb's leg reds.

## 5. esc1 — owner confirmed

`scripts/esc1_write_path_cycle_closure.py` has been red since #174 changed supersede's `blocked_by`
semantics; 58 now rewrites the exact paths it exercises (`_refuse_a_cycle` over the rewired graph, the
re-anchor). **Owner: 58's builder.** Disposition: re-key the script's scenario to the current contract
(#174's inherit/clear/replace sentinel + 58's re-anchor + am-3 §4's "refuse only a cycle through X'"),
re-run it as a receipt in the build report; if its scenario is no longer expressible, ARCHIVE it under
`docs/plans/v2/receipts/…` with a DUAL header naming what replaced it. A red instrument nobody runs is a
hope with a filename; the builder either makes it green or retires it deliberately.

## 6. am-7 folded into r3's worklist

The §HELD `test_retry_seam` re-key = a DELTA over 63c-i-a's a28b scanner: am-7's partition +
`_TYPED_CAS_CATCHES` + the two moves + the union completeness pin; PLUS this amendment's catch forms
(`TryStar`, `suppress`), the call-graph `derive_cas_verbs`, and the driver-seam runtime ∀ with
runtime-derived coverage (§3). `record_measurement` listed as a guarded door (am-7); its driver is the
lead's routing (§3). The §8c header and `_GUARDED_CAS_RE_READ` corpse prose (adversary §DUAL) are
REWRITTEN in the delta.

## 7. For the operator (via the lead) — loop cost and the class routing
- Round 3 on 58's contract; rounds 1–3 shared the heal-sizing property (now routed as a generated sweep
  and a library packer) and rounds 2–3 shared the CAS-population reach property (now moved to the state).
  Under CLAUDE.md rule 5, r3 must not receive instance fixes for either; if r3's grade finds a fourth
  instance of EITHER property, the ruling — not the contract — is what to re-open.
- Two errata of mine in this amendment's ancestry (am-3's packer "no library"; am-5's shape-keyed index),
  both of the same kind: a mechanism specified without reading what already exists (a package; a
  chokepoint). Named so the next reader weighs my `Packages considered` lines accordingly.
- No code/tests/store touched; this doc only; no attribution trailer.
