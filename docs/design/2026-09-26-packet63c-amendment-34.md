# Packet 63c — ruling amendment 34 (sidecar-63c-2, 2026-09-26): the a28b contract's forks — FK-a28b-4 (two sets NOW), FK-a28b-2 (a fifth enum member; the `mixed` sentence), FK-a28b-3 (the unresolved-operator counts are FIELDS), F-5 (fix in i-a), and the owner of the one-scanner pin

Rules lead Task 35 over `REPORT-contract-63c-i-a-a28b.md` (`e039c64`) §F FK-a28b-2/3/4, §FLAGS F-5/F-6, and
58 am-7 §3 item 4's unowned pin. Lore client still `ECONNREFUSED`; the directive was read from the native wake.
Amends amendment-31 (enum members), amendment-32 §2.1 (one clarification, no change of rule), and confirms 58
am-7 with one ordering refinement. `adversary-63c-i-a-a28b` grades against these.

## 1. FK-a28b-4 — Reading B: the PARTITION lands NOW, in 63c-i-a. 58's §HELD shrinks to a named delta

**Ruling: B (the author's pick, and the lead's #17087).** The partition predicate — *does the caught class's
subclass closure contain `TxnContentionExhaustedError`?* — is data a28b's scanner ALREADY computes for
`has_guard`; splitting the exact set on it is one line, not a second instrument. Reading A would ship an
intermediate hand-list that names two typed catches as "doors with a vacuous guard" — a false statement in a
canonical set, to be un-said by another packet later (DUAL churn across two packets on one hand-list). 58 am-7
§0 row 2 and I (Task 34) agreed on the PROPERTY and the build ORDER; the only thing that moves is WHEN the
partition appears, and "now, by the packet that lands the scanner" is strictly stronger. The symbol
`_TYPED_CAS_CATCHES` is born in 63c-i-a (contract-58-r2's import then resolves earlier, with one fewer red).

**58's §HELD delta, exactly (for contract-58-r3, folding now):**
1. `tasks.py::claim_task` → `_TYPED_CAS_CATCHES` when 58's production lands it (the both-ways exact pin
   goes RED until the entry is added — that is the completeness working, not a 63c defect);
2. the UNION completeness pin over the four sub-populations {door, typed-safe, translate-seam, passthrough}
   (58 am-7 §1) — a handler in none reds by `file::function`;
3. the runtime↔static cross-check (every listed handler has a runtime injection; every driven function's
   handlers are classified — 58 am-5 §3 / am-7 §3 item 2);
4. `_ROLLBACK_LOG_TIERS` re-keyed by class, `TxnUniqueViolationError → WARNING` (am-7 §4).
Nothing else. The two moves (RS-5, keeps) and `record_measurement`'s door entry are 63c-i-a's, already done.

## 2. FK-a28b-2 — Reading B: a FIFTH member, `"empty"`; `None` keeps ONE meaning. The `mixed` sentence states the total

**Ruling: B.** Amendment 32 §2.1 rules *"`None` iff the read was gated off"* — for EVERY field. Reading A makes
the enum the one exception (its `None` would also mean "the read ran and found no owner"): two meanings in one
served value, disambiguable only by cross-reading a sibling field — the exact shape the consumer law forbids
(renders take typed applicability; a reader must never derive a value's meaning by comparing it with another).
A rule with one exception is the quantifier law wearing a field name. So:
- `owner_classification: Literal["operator", "foreign", "mixed", "unclassified", "empty"] | None` —
  `"empty"` = the agent read RAN and the owned-but-unscoped set is empty; nothing to classify.
- **Invariants, pinned as ONE generated leg over the populations:** `owner_classification is None` ⇔
  `owned_but_unscoped_agents is None` (same read, gated together); `== "empty"` ⇔
  `owned_but_unscoped_agents == 0` ⇔ `distinct_owner_principals == 0`; any other member ⇔ the count `> 0`.
  Enforce it as a pydantic model validator (the STATE, not each path), so a wrong build cannot serve a
  contradictory pair through any door.
- Prose: `"empty"` contributes NO sentence (nothing to say); the by-annotation pin (1) swaps a Literal to
  ANOTHER member — for `"empty"` the swap must ADD the owner sentence, for the others it must change it.
  `_POPULATIONS["P_message"]`, `_RS1_COUNTS`, the gating pin's leg and the success legs move from `None` to
  `"empty"`; the author already named those as the only expectations that change.

**The `mixed` sentence (F-6) — states `distinct_owner_principals` as the TOTAL, the only integer it carries.**
"N other principals" would be `distinct − 1`, a derived integer that is no field value and would breach pin (2).
Constraints, not wording: it contains the substring `owned by the operator` (the existing
`[mixed-owners]` pin), it names the samples, and its ONLY integer is `distinct_owner_principals` rendered as
the total — e.g. *"owned by the operator and by others — N distinct principal(s) in all: <samples>"*.
`_OWNER_SENTENCE_STATES_N["mixed"] = True` stands; `foreign` states the same field (there the operator owns
none, so the total IS the "other" count — no arithmetic anywhere).

## 3. FK-a28b-3 — Reading B: the unresolved-operator counts become FIELDS; pin (2) has NO excluded population

**Ruling: B.** `_operator_unresolved`'s "(N principals, M admins)" are measured integers an agent acts on
(M = 0 → no admin principal exists; M > 1 → ambiguous — the remedy differs), so by amendment 30's rule they
are fields, not an exemption: `total_principals: int | None`, `admin_principals: int | None` on
`MigratePreconditionCounts`, `None` iff operator resolution was not attempted (it runs only when the
owned-but-unscoped set is non-empty — consistent with §2's invariant and am-32 §2.1). The unclassified
sentence is then DERIVED from the two fields by the ONE describe; pin (2) holds ∀ populations with no
`_UNCLASSIFIED_POPULATION` carve-out (the carve-out is precisely the hole the author's §13 item 8 names), and
the by-annotation pin (1) picks both up as ints. Reading A would leave one served sentence outside the one
instrument that guards served integers.

## 4. F-5 — FIX in 63c-i-a: an undefined target table is a typed, measured answer, never a driver error

A legal `--table agent` on a memory-only store today raises `TxnDomainRejectionError … governed scope count
rejected` — a raw driver teaching ("see the server log") for a call that is not wrong. Loud, yes; honest, no:
the served class says "the store rejected an illegal write" about a store that was never written. The
precondition read already gates on `INFO FOR DB` (the ONE read; am-28 addendum F-4); the LEG's own scope count
does not — the same property, derived on the precondition and stated over the verb (quantifier law; the
precondition's docstring says "the store is never queried for an undefined table" and the leg breaks it).
It is one branch inside the verb 63c-i-a owns, so it is fixed here, not bounded:
- `AgentMigrationPreconditions` carries `defined_tables` from the ONE `INFO FOR DB`; every leg checks its own
  table there BEFORE any store read.
- The answer is NOT a refusal (nothing is wrong with the store): `MigrateGovernedResult` gains
  `table_defined: bool`; when `False`, `scanned = 0`, `backfilled = 0`, `refused = False`, and the render
  derives *"the `<table>` table is not defined in this store — nothing to migrate"* from the typed field
  (never from a count compare).
- Pin, generated over `tables × {undefined}`: the typed answer, AND exactly ONE store read
  (`INFO FOR DB`) — a `run_query` spy counts calls; the gating pin's clause that "tolerates exactly this
  raise" is re-keyed to assert the typed answer (a pin that tolerates a defect is a pin-the-miss without a
  trigger). The adversary grades the re-key as part of this delta.

## 5. OWNER of the "exactly one scanner function" pin — 63c-i-a

A guard belongs with the thing it guards, at birth: the scanner is born in 63c-i-a, and the party most likely
to write a second one is the next delta on it (58's). Shape: allowlist-the-safe — the DERIVED candidate set is
every test-tree function whose body both walks `ast` over production files AND names a class from
`_txn`'s `SurrealStoreError` tree; the allowlist is the one function; a new candidate reds by name. Bound
stated in its docstring: a scanner that spells the class tree without naming it is invisible (the runtime
cross-check is the layer that does not care).

## 6. Notes, not rulings
- **R-3 constructible** (the author's note): the tokenless winner registers OWNERLESS through the handler seam
  → the control is re-keyed, not stopped. Good; the bound now has a pin that reddens when β closes the door.
- **#509 (`mutation_proof.py` does not restore on kill):** the standing law already covers the gap (`cp -a`
  the content first; restore from content) — the instrument should do what the law says. Not mine; recorded.

## §W
| # | item | lands |
|---|---|---|
| 1 | two exact sets now; 58's delta = items 1–4 of §1 | a28b as committed (no change) |
| 2 | `"empty"` member + the model validator + the generated invariant leg; `mixed` = total, one integer | a28b delta |
| 3 | `total_principals`, `admin_principals` fields; no pin-(2) carve-out | a28b delta |
| 4 | F-5: `defined_tables` on the preconditions, `table_defined` on the result, one-read pin; gating clause re-keyed | a28b delta + fix wave |
| 5 | one-scanner allowlist pin | a28b delta |

## §E — operator-visible
- §4 widens the fix wave by one branch in the migrate verb and one typed field on its result. I judged it
  in-scope (the verb is 63c-i-a's; "known defects get fixed in the session that finds them"); pull it to a
  bound if the loop cost matters more — the bound would be the raise itself, pinned with the trigger *"the
  first memory-only deployment".*
- Loop cost: a28b's contract is at ONE adversary round (in progress); these five rulings change pins the
  adversary treats as pending, not pins it has graded.
