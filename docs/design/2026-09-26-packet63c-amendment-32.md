# Packet 63c — ruling amendment 32 (sidecar-63c-2, 2026-09-26): FK-ADV-1 (the RS-5 conflict class), FK-ADV-2 (the message leg's agent fields), the C1–C3 class routing, and the am-31 fold

Rules directive #17081 (lead, `f5e0b67` §"a28 adversary: INSUFFICIENT") over `REPORT-adversary-63c-i-a-a28.md`
(`4441b9d`): §3 FK-ADV-1, §6 F-4 FK-ADV-2 + F-1/F-2/F-3/F-5, the lifted classes C1–C3 with MP-1…MP-5, and
residuals R-1…R-6. Amends amendment-29 (RS-5 mechanics), amendment-31 (FK-a28-4 — ERRATUM, both halves) and
amendment-28's β-bound rider (R-3).

**Provenance, stated plainly:** the lore client is still `ECONNREFUSED` in this session (the server answered
HTTP 200 at the last check; the client never reconnected), so #17081 was read from the lead report's durable
copy, NOT drained or acked on thread `63c` — the lead must keep the durable copy. grep/rg are hook-blocked here;
every code fact below was read with `awk`/`sed` over `loremaster/loremaster/{store/_txn.py,principals.py,
keeps.py,agents.py}` and `.venv/…/surrealdb/errors.py`, and is cited by SYMBOL. Nothing below was executed
against a store; where a fact needs a live probe I say so and make the probe the rider.

---

## §1 FK-ADV-1 — Reading B: the ONE driver types the record conflict; RS-5 catches THAT class

**Ruling: Reading B.** The driver already does exactly this for one other domain rejection —
`_txn.TxnGovernedConflictError(TxnDomainRejectionError)`, built by the ONE mapping helper
`_domain_rejection_error` from the ONE label `_ERROR_CLASS_GOVERNED_CONFLICT` — so Reading B is not a new
design, it is the existing design applied to a second engine fact. Reading A (broad class + existence re-read)
is what `keeps.get_or_create_keyed` does today and is the shape W7/W14/W15b walked through; amendment 29
§"named decision point" already said *"a typed rejection the registry can catch by class (never by message
text — routing is not sharing) … else STOP"*. The contract resolved that STOP silently; this un-resolves it.

### §1.1 Mechanics (all in `loremaster/loremaster/store/_txn.py`, the shared driver)
1. **Label:** `_ERROR_CLASS_RECORD_EXISTS` — a fixed teaching string in the `_ERROR_CLASS_*` family
   (*"record already exists — the id is taken; re-read the row"* or equivalent), never a slice of the raw text,
   never the id (ledger #31's hygiene boundary is unchanged).
2. **Class:** `TxnRecordExistsError(TxnDomainRejectionError)` — a subclass, so every `except SurrealStoreError`
   / `except TxnDomainRejectionError` keeps catching it (the `TxnGovernedConflictError` argument verbatim); a
   generic message; NO attributes parsed from the raw text. `_domain_rejection_error` maps the label to it —
   the ONE place; no raise site grows an `if label ==`.
3. **Classification, BOTH raise sites, ONE label — because both CAS doors ride different paths** (measured by
   reading: the agent CREATE rides `AgentRegistry._query` → `run_query`, the SDK exception in hand — the
   adversary's §A.5b receipt shows `__cause__` = `surrealdb.errors.AlreadyExistsError`; `keeps.get_or_create_keyed`
   rides `execute_transaction`, where the driver holds only the statement's raw `result` text):
   - **`run_query` path — TYPED.** `isinstance(error, surrealdb.errors.AlreadyExistsError) and error.record_id
     is not None` → the record label. `record_id` is the SDK's own discriminator (`_detail_field(details,
     "Record", "id")`, `errors.py::AlreadyExistsError`): a TABLE / NAMESPACE / DATABASE / SESSION already-exists
     (a DDL door) has `record_id is None` and must NOT take this class — the class means "the row id is taken",
     nothing else. This branch is checked before any text marker (typed beats text; the driver already imports
     `ErrorKind, ServerError` from `surrealdb.errors`).
   - **`execute_transaction` path — the raw-result MARKER, inside the classifier.** `_classify_engine_error`
     gains `_RECORD_EXISTS_MARKER` (the live-verified substring of the engine's per-statement rejection text —
     `already exists` on 3.2.x per §A.5b's `str(cause)`; the BUILDER live-verifies it on the test store
     `:18000`, as `_ASSERT_VIOLATION_MARKER` was), checked after the governed-conflict marker and before the
     ASSERT marker. Text classification is acceptable HERE and only here: the classifier IS the one hygiene
     boundary where engine text is already read (ASSERT, coercion, recursion-depth), so the rule "never by
     message text" (am-29) is satisfied — RS-5 reads a CLASS; the driver reads the text ONCE for everyone.
     **Bound, stated:** on this path a table-level already-exists that happens to carry the same substring would
     also classify as a record conflict; the rider probe (§1.3 pin c) says whether the 3.2.x text differs, and if
     it does not, the bound is carried in the marker's docstring with the re-open trigger *"the first
     transactional DDL statement in the tree"*.
4. **RS-5 (amendment 29, re-stated on the class):** the registry's CREATE branch catches `TxnRecordExistsError`
   ONLY; re-reads `_select_row(id)` as a CONFIRMATION; if the row exists → the existing re-register path with
   THIS call's own writes (model / task_id / cadence / heartbeat — K7's property); if it does not (the row was
   deleted between conflict and re-read) → the caught error propagates UNCHANGED, after exactly ONE CREATE
   attempt (no retry loop; a vanished winner is a STOP for the caller, never W7's recursion). Every other
   `SurrealStoreError` subclass propagates unchanged after one CREATE — K9's partition, verbatim.
5. **K9 lands with `_CONFLICT_CLASS = TxnRecordExistsError`.** Its derivation (`vars(loremaster.store._txn)`
   subclasses of `SurrealStoreError`) picks the new class up unedited; the non-vacuity leg must now assert the
   derived set contains `TxnRecordExistsError` AND at least one non-conflict `TxnDomainRejectionError` sibling
   (`TxnGovernedConflictError` is one — and it must land in the "propagates unchanged" half). K2/K4 stay.

### §1.2 R-6 — ONE predicate for both CAS doors, in the same wave
`keeps.get_or_create_keyed` narrows `except SurrealStoreError:` to `except TxnRecordExistsError:`; its
confirmation re-read (`get_by_key`) and re-raise-if-absent stay byte-for-byte. Then both doors decide from ONE
class and the two hand-rolled classifiers the adversary found (R-6) collapse to `isinstance`. **DUAL row for the
removed behaviour** — *a non-conflict rejection whose key coincidentally resolves used to return the winner*:
**dropped deliberately** — an ASSERT/coercion rejection masked by a coincidental winner is W7's family inside
keeps (the honest rejection was swallowed), not a virtue. Rider: the builder reads keeps' existing CAS pins
FIRST (tests before code); a pin that constructs the conflict on the real engine stays green unchanged; a pin
that FAKES a bare `SurrealStoreError` to mean "conflict" is re-keyed to the typed class and named in the report
as a DUAL re-key. If any keeps pin turns out to construct a genuine non-conflict rejection and expect the
winner, STOP and route to i-b — that is a contradiction with this ruling, not a re-key.

### §1.3 Pins (GATING — the a28b fold; every one mutation-proven)
- **(a) Typed path, live:** a real second CREATE with a taken agent id on `:18000` raises
  `TxnRecordExistsError` from `run_query`; CONTROL: an ASSERT-rejected statement on the same path raises the
  base `TxnDomainRejectionError`, not the subclass. Mutation: delete the typed branch → (a) RED.
- **(b) Transactional path, live:** the same taken-id CREATE inside `execute_transaction` raises
  `TxnRecordExistsError`; CONTROL as in (a). Mutation: reword `_RECORD_EXISTS_MARKER` → (b) RED, (a) GREEN
  (the two paths are proven INDEPENDENT, each with its own kill).
- **(c) The discriminator's control:** an `AlreadyExistsError` whose details kind is `Table` (constructed from
  the SDK class at unit level if a live DDL door is not reachable through `run_query`; the report says which)
  classifies as `unspecified rejection`, not the record class.
- **(d) K9 generated + K7** (§4). **(e) keeps' narrowed door** (§1.2) — its existing pins + the DUAL statement.
- **(f) The guarded-CAS scanner (R-5) — IN, as an instrument repair, flagged in §E.** The moment RS-5 lands,
  the tree holds a CAS door (`except TxnRecordExistsError` + `_select_row`) that
  `test_retry_seam._discover_guarded_cas_handlers` cannot see (it keys on `ast.Name == "SurrealStoreError"`
  and a `_select*` re-read prefix; Tuple handlers and subclass names are invisible; keeps' `get_by_key` door is
  already unlisted at HEAD). A scanner blind to the newest door is the eighth defeat. The fold widens its KEY to
  the derived form: *an `except` handler whose caught expression (each element of a Tuple included) resolves by
  import to a subclass of `_txn.SurrealStoreError`, followed by any re-read* — and the canonical set
  `_GUARDED_CAS_DOORS` gains the RS-5 door and the keeps door; the enumeration pin keeps diffing both ways.

---

## §2 FK-ADV-2 — Reading A (a28): measured counts are served; `None` iff the READ did not run. Amendment 31 FK-a28-4 is WRONG in both halves — erratum

**Ruling: Reading A.** I read the code this time: `principals._agent_migration_preconditions(store, table)` is
THE one read, and it runs BEFORE any refusal decision. Its reads are gated by exactly two facts, neither of
which is "which refusal fired": the agent facts (`unscoped_count`, both agent half-pairs) run iff `agent` is in
`INFO FOR DB`'s table set; the message facts (dangling senders, both message half-pairs) run iff
`table == "message"` AND `message` is defined. `migrate_governed` then asks `_verb_level_refusal` over that
answer, and the message leg (`_migrate_message_owner` → the agent-first ORDER guard → `_message_leg_refusal`)
decides from the SAME object. So:

- On a **message-leg refusal** the agent counts WERE measured (they passed) → served as measured `0`s. a28's
  `_RS1_COUNTS` and `P_message` populations are right; am-31's control clause (*"agent fields `None`"*) is false.
- On a **verb-level refusal on `--table message`** the message facts WERE ALSO measured (the function reads
  them before anything refuses) → served as measured counts. am-31's headline (*"they were not measured"*) is
  false for the built code.

**Erratum (mine, am-31 FK-a28-4, both halves):** I derived "not measured" from the ORDER of the CHECKS
("refuses before any leg runs") instead of from what the ONE read function DOES. The check order and the read
order are different facts; am-22 §4's rule is about READS. This is the instrument question I keep writing down
— *"is this a fact about the code's shape or about what it DOES?"* — asked, this time, only after the adversary
did. Am-31 §W row 2 is REPLACED by §2.1 below.

### §2.1 The rule, derived, ∀ outcomes
- **`None` iff the read was gated off.** `MigratePreconditionCounts` fields are `None` exactly when
  `_agent_migration_preconditions` did not perform that read — a memory-only store (no `agent` table) leaves the
  agent fields `None`; `--table agent` / `--table memory` leave the message fields `None`; `--table message`
  on a store with both tables leaves NOTHING `None`. This holds on EVERY outcome — verb-level refusal, leg
  refusal, success: a measured count does not become a lie on the happy path. (If a28 pins `preconditions` to
  `None` on success, that pin is re-keyed under DUAL and the fold says so; I have not read a28's success pins.)
- **Prose is derived, ONE rule:** the describe function names every MEASURED, NON-ZERO problem count in the
  check order (agent problems, then dangling senders, then message half-pairs — am-26's order ∀ tables); a
  measured zero contributes no problem sentence; a `None` field is omitted. Consequence, and it is the
  am-26 property applied ∀ tables rather than a special case: a verb-level refusal on `--table message` whose
  store also holds message half-pairs NAMES them — one refusal, every failing check the verb read, so the
  operator gets the whole worklist from one call instead of refuse → fix agents → refuse again. The refusal
  DECISION is unchanged (the verb refuses on agent half-pairs; the message leg refuses on its own facts in its
  order).

### §2.2 Pins (GATING; F-5's owed pin is re-keyed to this)
- **Gating pin, generated over the two gates:** for `(table, defined-tables) ∈ {agent, memory, message} ×
  {both defined, agent only, message only, neither}`, the served `preconditions` has field `None` iff the read
  was gated off — derived from the function's two gates, not from which refusal fired. Construct all four
  store shapes (a memory-only store is `INFO FOR DB` without `agent`; F-4's wrong-shape fail-closed pin stays).
- **Both refusals on `--table message` serve the full measured set:** (i) a store with an agent half-pair AND
  a message half-pair → verb-level refusal; every field measured; the reason names BOTH problems in check
  order, with counts equal to the fields (pin (2) unchanged); (ii) after `--table agent` succeeds → the message
  leg's refusal; agent fields measured `0`, message fields measured; the reason names only the message
  problems. Perturbation: add one more half-pair row to either table → the matching count and sentence move.
- **Success serves the measured object** (all fields measured on `--table message`, message fields `None` on
  `--table agent`) — one leg each.

---

## §3 The am-31 fold (F-1 / F-2 / F-3) — eight fields, pins derived by annotation

- **F-1 / F-2:** the model has eight fields (amendment 30's six + amendment 31's two); every population dict
  and `_RULED_COUNT_FIELDS` twin becomes the model's own `model_fields` — no hand-list of names anywhere in the
  contract; the ⊇ leg of pin (2) iterates `model_fields`.
- **F-3 (pin (1)):** parametrised over `model_fields`, the perturbation chosen BY ANNOTATION: an `int | None`
  field is moved by `_PERTURBATION`; a `Literal[...] | None` field is swapped to another member (derived via
  `typing.get_args`, never a hand-picked pair); and a COMPLETENESS leg fails on any field whose annotation is
  neither — a third field type must extend the perturbation table, never be silently skipped. Perturbing
  `owner_classification` must move the owner SENTENCE (the describe derives it), perturbing
  `distinct_owner_principals` must move the owner COUNT in the text.
- **Erratum (mine, am-31):** *"Pin (1) grows to the two new fields by `model_fields`, automatically"* was a
  claim about a contract's shape made without reading the contract (R-9). Recorded.

---

## §4 C1–C3 — the class routing (the lead's second-strike call on F-2's property is confirmed)

The five missing pins are three properties; the fold lands the PROPERTY pins, with the adversary's K-probes
landed AST-equal wherever the probe already encodes this ruling (amendments 16/17: an adversary-authored,
adversary-proven probe landed AST-equal carries its own grading; a deviation is what the narrow delta grades).

| class | property (quantified) | domain — source of truth | lands as | gate |
|---|---|---|---|---|
| **C2** | a foreign principal's register issues ZERO agent-registry queries and is served ONE denial, ∀ probe kinds × ∀ foreign shapes | the registry's ONE seam `AgentRegistry._query` (every read rides `run_query` through it — K1's spy, with a positive control on a householded register; bound: a read on another connection is outside it) × the principal's relation to THIS keep, enumerated from the gate's inputs: {no keep, keeper of another keep, householded in another keep} foreign; {householded in this keep} the NOT-foreign control | **K8** AST-equal + its two extra shapes as parametrisation; **K1** AST-equal, REPLACING RS-3's 3-method spy (a hand-list; the instrument lesson) | GATING (MP-1 HIGH, MP-4) |
| **C3** | ∀ CREATE outcomes ∈ (derived `SurrealStoreError` subclasses) × {row landed, not}: the re-register outcome WITH THIS CALL'S WRITES iff `TxnRecordExistsError` ∧ row exists, else the same class unchanged after ONE CREATE | `vars(loremaster.store._txn)` — a new class joins unedited; non-vacuity per §1.1 item 5 | **K9** with `_CONFLICT_CLASS = TxnRecordExistsError` (the one declared deviation from §A.2); **K7** AST-equal | GATING (MP-2, MP-3) |
| **C1** | ∀ register calls (success, ∀ refusal classes, ∀ denial): the keep store's ONLY write is the session-keep mint; no pre-existing keep / member_of row changes | `KeepStore`'s public async verbs by `inspect` (SAFE set allowlisted: reads + `get_or_create_keyed`), `_query` watched for any non-SELECT, before ⊆ after — K6 verbatim. **Completeness of the refusal-cause legs: derived from `_REGISTRY_CLASSES`** (a28's derived `AgentRegistryError` family): every class is either PROVOKED post-mint by a fixture or named in an evidence-backed exemption list ("not reachable post-mint: <why>"); a new class fails the pin. NOT the adversary's "AST count of `raise` statements after `_select_row`" — a raise-shape walker is the 7th defeat (amendment 24), and a factory-raise idiom would under-count it silently | **K6** as the class pin; **K5** folded as K6's per-cause legs | GATING (MP-5 LOW but cheap; and it is C1's only instrument) |

---

## §5 Residuals ruled
- **R-1 (fold, NON-GATING):** RS-2's non-vacuity leg counts POST-MINT refusals (a `register` that raises after
  the mint) and asserts `== _ROUNDS`, which is what its docstring already promises (measured 200/200 on the
  adversary's reference). A message/assertion gap is a false gate; close it.
- **R-2 (fold, GATING-cheap):** `keeps.minted_by_this_call` / `_MINTED_BY_THIS_CALL` are DELETED (am-28 §F-1
  "dead and go" — a builder constraint), and a one-line retired-name pin over the package (no binding, no prose
  mention: its docstring today still claims the created-only compensation reads it).
- **R-3 (erratum, mine — am-28's β-bound rider):** *"trigger before β: a keep found with a keeper and zero
  scoped rows after a refused register"* — nothing measures it, and the tokenless CONTROL builds its winner at
  the registry so it stays green after β closes the handler door: a trigger nobody measures is a hope, in my own
  ruling, two clauses from where I quoted that law. Rule: the fold re-keys the tokenless control to build its
  winner THROUGH the handler seam (`AppContext.comms(action="register")`), so the pin is a real pin-the-miss
  that reddens when β closes the door; if that is not deterministically constructible, the builder STOPS and
  says so, the bound keeps its docstring + a lead-report row (carrier rule), and the trigger is re-stated as a
  code event: *"the day the handler's post-mint refusal path changes"*.
- **R-4 (fold):** the two stale prose sites in `test_fixwave_a19a_63c_i_a.py` — corpse-swept with the P6
  bare-pattern sweep; each residual hit gets its own verdict.
- **R-5:** §1.3 (f). **R-6:** §1.2. **R-7 / R-8:** instrument and friction notes — not mine to rule.

---

## §W — the worklist, in order

| # | item | class | lands |
|---|---|---|---|
| 1 | `_txn`: `_ERROR_CLASS_RECORD_EXISTS`, `TxnRecordExistsError`, typed branch (`run_query`) + `_RECORD_EXISTS_MARKER` (transactional), one mapping helper; pins (a)(b)(c) | GATING | a28b fold + fix wave |
| 2 | RS-5 catches `TxnRecordExistsError` only; confirmation re-read; ONE CREATE; K9 with the class; K7 | GATING | same |
| 3 | keeps' CAS narrowed to the typed class; DUAL row; existing pins read first | GATING | same |
| 4 | guarded-CAS scanner: derived key + both doors in the canonical set | GATING (instrument repair, §E) | same |
| 5 | FK-ADV-2: `None` iff the read was gated off, ∀ outcomes; describe names every measured non-zero problem in check order; the generated gate pin + the two `--table message` refusal pins + success | GATING | same |
| 6 | am-31 fold: eight fields via `model_fields`; pin (1) by annotation with the completeness leg | GATING | same |
| 7 | C2: K8 (+ shapes) and K1 (replacing the 3-method spy) | GATING | same |
| 8 | C1: K6 with K5 as legs; completeness from `_REGISTRY_CLASSES` | GATING | same |
| 9 | R-1 post-mint count; R-2 deletion + retired-name pin; R-3 handler-seam control or STOP; R-4 corpse | R-2 GATING-cheap, rest NON-GATING | same |

Order for the fresh contract author: 1 → 2 → 3 (one class, three doors) before anything else, because K9's
`_CONFLICT_CLASS` and keeps' narrowed catch both depend on the class existing. The narrow adversary delta
(mandatory, the lead's call and the 2026-07-28 law) grades the DEVIATIONS from §A.2 — K9's class, K5/K6's
completeness leg, the FK-ADV-2 pins, the scanner key — not the AST-equal probes.

---

## §E — operator-visible
1. **A production seam every store rides changes** (`_txn.py`: one label, one subclass, one typed branch, one
   marker). Amendment 29 named this decision point and I judge it design-in-scope for 63c-i-a, pre-authorized
   under the pre-production law; it is a change to the shared driver all the same, so it is here for you to
   pull. If pulled, the fallback is Reading A + K2 pinned, with R-6's two divergent classifiers ledgered as a
   bound.
2. **Scope I widened on my own judgement:** the guarded-CAS scanner repair (§1.3 f) and keeps' CAS convergence
   (§1.2). Both are one-function changes that exist because THIS ruling creates the door / the class they miss;
   deferring either ships an instrument blind to the newest door. Pull if you disagree.
3. **DV-5 — "15 GB PID watchdog":** the adversary ran every full suite under reading (b) (kill the run's own
   PID tree above 15 GB RSS, plus a 4 GB host floor) because reading (a) (host `MemAvailable < 15 GB`) SIGTERMed
   its baseline while foreign tenants held the box at 11–27 GB free. This is a question for you, not a design
   fork: MEMORY.md's line reads as (a); (b) is what actually ran and is the reading that measures the run
   rather than the neighbours.
4. **Loop cost (the 2026-09-26 rule):** a28 ↔ adversary is at ONE round; the packet's running total is the
   lead's. This amendment answers the second strike on F-2's property with the class C2, not another instance,
   and lands the adversary's probes AST-equal so a28b's delta is bounded to the deviations named in §W.

## Errata (cumulative, this amendment)
- am-31 FK-a28-4, both halves (§2) — check order mistaken for read order.
- am-31 "grows automatically" (§3) — a claim about an unread contract.
- am-28 β-bound rider (§5 R-3) — an unmeasured trigger in the ruling that quoted the law against it.
- am-29 (§1) — I wrote "by class, else STOP" and the contract resolved the STOP silently; I did not check that
  the STOP had been exercised when I graded a28's readings (am-30/31). The askable form, recorded: *"did the
  named decision point in my ruling get DECIDED, or did the next document route around it?"*
