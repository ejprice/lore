# Packet 64 — ruling amendment 9 (sidecar-64, 2026-09-27): the 64b-i r2 forks — the identity budget is keyed by TABLE (`member_of`, not `keep`; erratum on am-8 §1), the scope ASSERT is WITHDRAWN (63a §4.1 stands; erratum on am-8 §2), the UNOWNED-LEGACY set is keyed on the SET clause (erratum on am-7 §3), the exempt golden is the COMPOSED transaction text from the ONE composer (erratum on am-7 §1), the alias close-out is an ADJUDICATED bound, S-3 is a28's red, `c3_harness_repair.py` → delete (operator's call)

Rules `REPORT-contract-64b-r2.md` §FORKS FK-r2-1…8 per lead-63c-2's Task 22 (the report is uncommitted; the
author continues on its picks). Every name below was `lore_verify`'d / read at HEAD before citing (the
self-rule from 58 am-11): `visible_keeps.resolve_visible_keeps(keep_store, *, member_email)` →
`KeepStore.list_keeps_for_member(*, member_email)` → `_resolve_principal_id(member_email)` + `SELECT out FROM
member_of WHERE in = $principal` (BORN-WRAPPED whole method, D1); `store.surreal_schema._governed_field_specs`
docstring: *"NO ASSERT/DEFAULT: memory/message are POPULATED tables, so … an ASSERT poisons every legacy row's
next UPDATE … the scope DOMAIN is enforced at the WRITE seam … never a store ASSERT"* (63a design §4.1);
`test_memory_enforcement_63b_ia._MIGRATE_GOLDEN = "UPDATE memory SET scope = $scope WHERE scope IS NONE"` and
`test_message_enforcement_63b_ii_a._MIGRATE_MESSAGE_GOLDEN` = `… WHERE scope IS NONE AND owner_principal IS
NONE …`; `test_fixwave_a19a_63c_i_a._migrate_legs()`; `store._txn.compose(*fragments) -> (statement_text,
merged_params)` — the ONE `BEGIN … COMMIT` composer `SurrealStore.apply` calls first;
`principals._agent_migration_preconditions(store, *, table=None)`; `scripts/c3_harness_repair.py` (2026-08-03,
a rescued pytest plugin `-p c3_harness_repair`) is referenced only by its own docstring and archived receipts.

## 0. Rulings in one screen

| fork | ruling |
|---|---|
| **FK-r2-1** | **The author's pick — CONFIRMED as the class ruling.** The budget is keyed by the TABLE a statement reads: `IDENTITY_READ_BUDGET = {agent: 1, principal: 1, member_of: 1}` per governed call, counted at the store seam ∀ spec-dict verbs. **ERRATUM (am-8 §1):** I wrote `keep ≤ 1 (resolve_visible_keeps)`; the read is `member_of`, and `principal` measured 2 because `list_keeps_for_member` re-resolves the email the caller already resolved. Mechanism: the proven principal id is passed DOWN (`resolve_visible_keeps(…, principal_id=)` → `list_keeps_for_member(*, principal_id=)`; `member_email=` stays for the other callers — exactly one of the two, refused otherwise). Rider: the seam's *"never `[]` for a typo'd identity"* guarantee moves upstream — `principal_id` is accepted ONLY as an id the caller PROVED (`resolve_principal` denies an unknown email first); pin: `resolve_subject`'s path issues exactly one `principal` statement; a wrong build that passes the id without the upstream proof is caught by MP-5's lifecycle leg (principal disabled → denied on the next call). The alternative (pin `agent` only) is REJECTED: the reach law — a budget that names one table is a hidden constant for the other two. §1 |
| **FK-r2-2** | **The ASSERT is WITHDRAWN — ERRATUM (am-8 §2 "Backstop at the STATE").** 63a §4.1 is standing law with a measured reason (a populated table's ASSERT is the DD-3.c write-poison class: one legacy row fails every batch UPDATE that touches it), the emitter's own docstring states it, and the P2 "no constraint a legacy row can violate" pins enforce it. am-8's MEDIUM-confidence bound was the tell. The STATE enforcement is: (a) the WRITE seam ∀ writers (the `lorerunes.pdp` shape predicate + the keep existence read — am-8 §2 unchanged there); (b) a UNIVERSAL leg in the F5 classifier — ∀ observed governed writes, the landed `scope` ∈ DOMAIN, regardless of entry (a 64b §HELD delta to the 63c-shared classifier; **touches 63c's surface — sidecar-63c-2's concurrence requested via the lead**; fallback if refused: a 64-side wrapper that calls the shared classifier and adds the leg); (c) the S2 production-dump leg: zero real rows carry an out-of-domain scope. The author's pick (pin the ASSERT + P2 exemptions + rewrite the docstring) is REJECTED. §2 |
| **FK-r2-3** | CONFIRMED: `$rep_owner_principal` / `$rep_owner_agent` / `$rep_scope` (HEAD's `$rep_*` idiom); the None-bind probe stands. The golden's NAME changes under FK-r2-5: `REPORT_SYSTEM_TXN_GOLDEN`. |
| **FK-r2-4** | **The author's pick — CONFIRMED. ERRATUM (am-7 §3):** the WHERE rule yields `{message, finding}` — memory's golden has no owner conjunct and message's (OWNED-legacy) does. The disposition's meaning is in the SET clause: UNOWNED-LEGACY ⟺ the migrate stamps `scope` and NO owner column. Domain = every leg in `_migrate_legs()` whose golden's SET touches no `owner_*` column; completeness both ways against `_migrate_legs()` AND against `LegacyMapping`'s STRING-UNRESOLVABLE rows (the two derivations must agree). §3 |
| **FK-r2-5** | **Neither reading — the golden is the COMPOSED TRANSACTION TEXT, from the ONE composer. ERRATUM (am-7 §1):** `statement=fragment.statements[1]` assumed the observer records a statement; it records what `execute_transaction` receives, i.e. `compose(...)[0]` (`BEGIN; LET …; CREATE …; COMMIT;`). `report_system` computes `text, _ = compose(fragment)` and enters `governed_exempt("calibration-drift", statement=text)`; `_apply([fragment])` composes the identical text (deterministic; pinned `token.statement == observed`). Leg 2 stays EXACT; the golden pins the counter `LET` too — a stronger oracle, not a cost. **A5 is REJECTED:** widening leg 2 to "one of the `;`-statements" admits a smuggled UNGOVERNED statement in the same transaction (leg 3 sees only governed-table effects) and edits a 63c-shared classifier for a weaker property. The migrate is untouched (one statement via `run_query`). §4 |
| **FK-r2-6** | **The author's pick, with the adjudication fixed:** the alias pin's post-build red is NEVER `RED_ORPHANED` — the r2 author registers a NEW bound `packet-64b-i-closeout` in `scripts/pending_contracts.yaml` NOW (owner: the lead's close-out agent — a contract-author-class agent, since tests are its role; trigger: the 64b-i build's commit), covering exactly the alias pin; it self-destructs when the alias set is empty. BC-r2-9 stands. The alternative (rewrite now) loses the `UNBUILT …` teaching reds — rejected. |
| **FK-r2-7** | CONFIRMED: `A2[finding-*]` reds for the identical reason as its siblings (the shared `_agent_migration_preconditions` read is fail-open until 63c-i-a's a28 BUILD) — a28's adjudicated red by its file partition, never 64b's. Rider: once 63c-i-a's build lands, the r2 SAT base INCLUDES it and the finding leg must go green with ZERO 64b change; a residual finding red is then 64b's. am-8 §4's "the finding leg satisfies a28's properties" stands — satisfied by the shared read once that read is fixed. |
| **FK-r2-8** | **Recommendation to the operator (via the lead): DELETE `scripts/c3_harness_repair.py` in 64b's §HELD**, with a DUAL row citing the archived verbatim copy (`docs/plans/v2/receipts/2026-08-01-packet04b2-wavec/REPORT-refbuild-c3-1.md §6.1`). Measured: zero consumers outside its own docstring and archived reports. Kept, it is a corpse that passes retired served args and fails at first use — an unpinned known limitation. If the operator keeps it: the reference's `title=` rename is the minimum AND a pin that it is imported by nothing (so its rot is deliberate, not silent). Deletion is a scope decision — not taken by me. |

## 1. FK-r2-1 — one read per table, keyed by the table

The property (am-8 §1, corrected): *∀ governed calls, the identity path issues at most one statement per
identity table — `agent`, `principal`, `member_of` — measured at the store seam over the spec dict's
verbs × {agent supplied, omitted}.* Its dual (MP-5) fixes the floor at one. The keys are the TABLES the
executed statements name (derived from the statement text), never the function names on the path — that
is what let am-8 write `keep` for a read of `member_of`. Cost of the mechanism: one keyword on a 61b seam
(`list_keeps_for_member(*, member_email=None, principal_id=None)`, exactly one required); the docstring's
BORN-WRAPPED guarantee is unchanged (the whole body still rides `wrap_store_rejection`).

## 2. FK-r2-2 — why the write seam is the state here, and an ASSERT is not

- A store ASSERT on a populated `option<string>` column is the DD-3.c shape: the day one legacy row holds a
  value the ASSERT refuses, every batch UPDATE over the window that includes it rolls back — total denial
  for a verb, from one row (packet 03b's receipt, reproduced with controls). The value of the ASSERT was a
  backstop against a writer that bypasses Python; that writer is exactly what F5 exists to catch, and (b)
  makes it a universal check rather than a per-entry one.
- The domain's EXISTENCE half cannot live in an ASSERT anyway, so the ASSERT was always a half-check
  bought at the price of a migration hazard on every governed table. 63a §4.1 had already made this call;
  am-8 overrode it without reading the emitter's docstring — the class of error 58 am-11 §4 names.
- Pins: (a) unchanged from am-8 §2 (∀ writers × {nonexistent keep, non-scope, hostile} → refused, row
  unchanged); (b) the classifier's universal leg with a positive control (a synthetic observed write landing
  `scope='banana'` under a valid label → UNCLASSIFIED); (c) the S2 leg over the restored dump; the P2 specs
  are UNTOUCHED (no `scope` exemption needed — there is no constraint).

## 3. FK-r2-4 — the SET clause is the disposition

`UPDATE <t> SET scope = $scope WHERE …` stamps scope only ⇒ UNOWNED-LEGACY; `SET owner_principal = …,
scope = …` ⇒ OWNED-legacy. Deriving from the WHERE (my am-7 rule) read the PRECONDITION as the disposition;
memory's precondition is `scope IS NONE` alone because its legacy rows never had owner columns to test. The
askable form I skipped: *"is this the clause that says what the migrate DOES, or the clause that says WHEN it
runs?"*

## 4. FK-r2-5 — one text, one composer, exact

`compose` is the ONE place transaction text is assembled (`SurrealStore.apply` calls it first; the
envelope, normalisation and the hard cap live there). The token's text must be the observed text; deriving
it from the same composer makes leg 2's equality a fact about the same bytes rather than a claim about two
producers. The test-side golden `REPORT_SYSTEM_TXN_GOLDEN` is the adjudicated full text (whitespace-
normalised as the classifier already does), with FK-r2-3's `$rep_*` names; drift in the LET or the CREATE
reds leg 2 (the oracle working). Discrimination pins (the author's three, re-targeted): token ≠ observed →
RED; golden edited → coverage RED; a second governed mutation in the block → leg 3 RED.

## 5. Discipline
- Four errata in one amendment (am-8 §1 `keep`, am-8 §2 the ASSERT, am-7 §3 the WHERE rule, am-7 §1 the
  statement slice). All one class: a mechanism specified from memory of a seam instead of the seam's text.
  The self-rule (58 am-11 §4) now covers MECHANISMS, not only names: read the seam before ruling how it is
  called.
- Loop status (for the operator): 64b-i at contract r2; no property has struck twice; two of the eight forks
  touch surfaces outside 64 (FK-r2-2's classifier leg → 63c; FK-r2-8's deletion → operator).
- No code/tests/store touched; this doc only; no attribution trailer.
