# Packet 64 — ruling amendment 8 (sidecar-64, 2026-09-26): the 64b-i adversary — R8's budget is ONE agent-row read AT THE SEAM (the verify SELECT projects the identity columns), admin `set_scope` = any ROW never any STRING (a scope DOMAIN ∀ writers), authorize BEFORE the edge check (the invisible-row oracle decides it), the r2 fold's SAT base and the FK-9 signature form, and the CLASS of every surviving wrong build

Rules `REPORT-adversary-64b.md` (`0f69efa`, INSUFFICIENT — 14 missing pins · 4 SAT defects · 2 new doors; 10
wrong builds + the reference survive) per lead-63c-2's Task 19 Part A. Amends am-7 §5 FK-8 (its "ONCE" was
stated over a path I had not measured — the adversary's store-seam probe counts TWO agent-row reads) and the
kickoff §5 row `set_scope` ("admin any (audited)" — any ROW). Facts: `owner_stamp.stamp_owner` →
`AgentRegistry._verify_capability_owner` is ONE SELECT over `agent` projecting `id, status,
capability_expires_at, owner_principal …` (#425 closed the second OWNER read); the reference's
`_resolve_identity` then runs `SELECT * FROM type::record('agent', $id)` for `name`/`session` — the same row,
read twice; `governed.resolve_write_scope` validates a MEMBER's explicit scope via `pdp._grantable` (fixed
scopes ∪ the caller's OWN keeps) and admin bypasses it; `FindingLedger._transition` at HEAD resolves the row,
validates the edge, THEN applies (no gate exists yet).

## 0. Rulings in one screen

| # | ruling |
|---|---|
| **(1) R8 / MP-7** | **YES, the capability-verify read COUNTS — it IS the agent-row read.** Budget: **≤ 1 statement against `agent` per governed call**, measured at the STORE seam (the adversary's `test_adv64b_r8_seam.py` shape), ∀ write verbs DERIVED from the spec dict × {agent supplied, omitted}. Mechanism: the verify SELECT PROJECTS the identity columns (`name`, `session`, + what the footer reads) and returns a frozen `VerifiedAgent` record; Subject construction, the identity compare and the footer all consume THAT result. A second `type::record('agent')` read is #425's defect one column wider. am-7 FK-8 ERRATUM: "resolves the agent row ONCE" described the design, not the reference. §1 |
| **(2) MP-12** | **"admin any" = any ROW, NEVER any STRING.** `scope` has a DOMAIN — `{principal-private, agent-private, server} ∪ keep:<EXISTING keep id>` — enforced ∀ writers (member, admin, migrate, system, 64d's change-scope) by ONE predicate in `lorerunes.pdp` (shape) + ONE existence read for a `keep:` target in the substrate; admin bypasses only the HOUSEHOLD clause. Out-of-domain → a typed teaching refusal, byte-inert. Backstop at the STATE: the column ASSERT via the ONE DDL emitter (⚠ builder verifies the populated-table semantics against the store-ref before landing). §2 |
| **(3) L5 order** | **Authorize FIRST, then the edge.** The pre-read → gate (incl. am-7's invisibility derivation) → edge validation → CAS. Reason: validating first would name an INVISIBLE row's status in `IllegalTransitionError` — an oracle. DUAL row: CHANGED-DELIBERATELY. §3 |
| **r2 fold routing** | SAT base = HEAD **as 64b will build on it**: HEAD + 58-r3's committed contract + 58's §HELD applied FIRST + 64b's §HELD. S-1 the fold repoints the import; S-2/S-3 the finding leg SATISFIES a28's ∀-legs pins (measured `backfilled`, fail-closed INFO-FOR-DB) — they are properties over every leg and the finding leg is a leg; S-4 64b owns the driver re-key for the doors 64b MERGES, declared in 64b's OWN test module via 58-r3's discovered `CAS_SEAM_DRIVERS` registry (58 am-9 FK-r3-4). §4 |
| **FK-9 / MP-9** | Declarations are **TYPED CALLS** with the ruled keyword surfaces (mypy `[call-arg]` sees a renamed kwarg — the adversary's positive control), kept PERMANENTLY as signature pins; the runtime `Any` aliases / `vars().get` reach-arounds get a SELF-DESTRUCT pin: alias set ⊆ the bound's unbuilt symbols, derived; a landed symbol still reached through `Any` → RED. §5 |
| **CLASSES** | every survivor's property named, one sweep each. §6 |

## 1. (1) — one agent-row read, at the seam

- **Question.** Does `stamp_owner`'s capability-verify SELECT count against R8's "at most ONE registry read per
  call"? **Answer: it is the ONE.** R8's line is a budget on the REGISTRY (`agent` table) per call; the verify
  SELECT reads the agent row — that read is the budget spent. The reference's second read exists only because
  the first PROJECTS too little. #425 fixed exactly this for the owner pair ("the verified SELECT already
  projects the owning principal id, so there is NO second owner read"); the identity columns are the same case.
- **Mechanism:** `_verify_capability_owner` (the ONE verification seam — ROUTING-IS-NOT-SHARING keeps it the
  only path) projects `name`, `session`, `status`, `owner_principal` and returns a frozen `VerifiedAgent`
  (bare ids; the footer's fields included). `stamp_owner` returns it (or the pair derived from it — the author
  chooses ONE shape); `resolve_subject` stays THE Subject constructor (R-a.2's allowlist unchanged) and hands
  the verified record up; `_resolve_identity(capability, *, agent, session) -> (Subject, VerifiedAgent)`
  compares `agent`/`session` against the record and the footer takes it (`resolved=`). No `get_agent`, no
  `_select_row` on the identity path.
- **Budget table (pinned at the store seam, per table, per governed call):** `agent` ≤ 1 · `principal` ≤ 1
  (`resolve_principal`) · `keep` ≤ 1 (`resolve_visible_keeps`); the pin counts statements by table name in
  the executed text during ONE governed write with the REAL identity path (the `_finding_fakes` arm is NOT
  the instrument — MP-7's own P0 catch). Generated over the spec dict's write verbs × {agent supplied,
  omitted}. Mutation: add a by-name `get_agent` to the identity step → RED by count.
- **Its DUAL is MP-5 (lifecycle): ≥ 1 read per call — every authorization input (capability, agent status,
  principal status, household) is read PER CALL, never memoised (WB4).** Generated sweep over the four
  degradations {household removed, capability expired, agent retired, principal disabled}: the CALL before →
  allowed (control); the call after → refused; row unchanged. The two pins together fix the count at exactly
  one per table per call.

## 2. (2) — the scope DOMAIN, ∀ writers

- **Question.** Kickoff §5 says admin `set_scope` is "any (audited)". Any ROW, or any STRING?
- **Answer.** Any ROW. Admin's bypass is of the HOUSEHOLD clause of `_grantable` (an admin may re-scope a row
  into a keep it is not householded in — the operator's repair verb); it is not a licence to store a value
  that is not a scope. `banana` and a dangling `keep:` make the row member-invisible forever (an audited
  soft-delete by typo) and plant free text in a column 64b-ii renders.
- **Property (the CLASS, MP-12):** *∀ writers of `scope` — member `report`/`set_scope`, admin `set_scope`,
  `migrate_governed`, `report_system`, 64d's `--change-scope` — the landed value ∈ DOMAIN, where DOMAIN =
  the fixed scopes ∪ `keep:<id of a keep that EXISTS at write time>`.* Mechanism, ONE implementation:
  `lorerunes.pdp.scope_shape_ok(value)` (the SHAPE: fixed set ∪ `keep:` + the keep-id charset; stdlib, no
  store) is the predicate `_grantable` ALREADY implies for members and that every other writer now calls
  BEFORE its write; for a `keep:` target the substrate performs ONE keep existence read (`keep_store` by id)
  — members get it free (their own keeps came from the store), admin/migrate/system pay one read. Refusal: a
  typed `GovernedDenied`-family teaching error for members (unchanged), a typed `ValueError`-family
  refusal naming the domain for admin/system; byte-inert, +0 audit rows.
- **Backstop at the STATE:** the `scope` column's `ASSERT` in `_governed_field_specs()` (the ONE emitter)
  admits `NONE` (legacy rows) ∪ the fixed scopes ∪ `string::starts_with($value, 'keep:')` with the charset —
  the shape half only (existence cannot live in an ASSERT). ⚠ **Bound, verified by the builder before
  landing, not by me:** `DEFINE FIELD … OVERWRITE` on a POPULATED table with a NEW ASSERT — the store
  reference §1.4/#107 governs the migration verb; whether existing rows are re-validated is a live question
  → a dirty-store leg (seed an out-of-domain legacy value under the OLD DDL, run the DDL, assert the outcome
  the store-ref documents) before the ASSERT ships. If the engine re-validates and refuses, the ASSERT lands
  AFTER a heal, or ships as `NONE`-tolerant only. MEDIUM confidence on the engine behaviour; the leg decides.
- **Pins (generated over the writer set, derived from the spec dict + the migrate/system/64d entry points):**
  each writer × {nonexistent keep, non-scope string, HOSTILE_FREE_TEXT} → refused, row unchanged, +0 audit;
  CONTROL: an existing keep moves. Reach: the writer set's completeness assertion — every production site
  that assigns `scope` in a fragment (AST: the `scope` column in a `SET`/`CONTENT`) is a listed writer.

## 3. (3) — authorize, then validate the edge

- **Question.** The reference gates (`authorize_guarded`) BEFORE `_validate_transition`; HEAD validates first
  (there is no gate at HEAD). Which order?
- **Answer.** Gate first. The edge check reads the row's CURRENT status and names it in
  `IllegalTransitionError`. On an INVISIBLE row that text is an oracle (am-7 §4 / MP-1's class) — so the
  gate (with its invisibility derivation) must run before anything reads the status into a served string.
  On a VISIBLE-but-unwritable row either order is safe to reveal; `GovernedDenied` first is still right
  (the caller cannot act on the edge at all — the deny is the fact). On a writable row the edge check runs
  next, before any write, exactly as today.
- **Pins:** invisible × illegal edge → not-found bytes, never a status; visible-unwritable × illegal edge →
  `GovernedDenied`, never `IllegalTransitionError`; writable × illegal edge → `IllegalTransitionError`
  naming both states, ZERO writes; writable × legal edge → the CAS. Generated over {acknowledge, resolve,
  wontfix} × {id, number} (the `_transition` callers, derived). **DUAL row:** HEAD's "validate BEFORE any
  write" survives (still true — the gate writes nothing); the ORDER relative to authorization is
  CHANGED-DELIBERATELY for the oracle reason above.

## 4. The r2 fold — SAT base and the four defects

- **Base:** the receipt is worthless on a base 64b will never build on. r2's SAT runs on **HEAD + packet
  58-r3's committed contract files + 58's §HELD (applied first, as its own scratch commit) + 64b's §HELD**;
  the baseline is the SAME tree minus 64b's §HELD. Attributable reds = 0 is the bar, on THAT tree.
- **S-1:** the fold step (`_governed_contract_64` → `_governed_contract`) repoints `test_mcp_server.py`'s
  `finding_context` import in the SAME hunk — a fold that deletes a module and leaves an importer is not a
  fold.
- **S-2 / S-3:** a28's ∀-legs pins (`backfilled` MEASURED post-UPDATE, am-27 FORK-1; fail-closed on a forged
  `INFO FOR DB`, A2) are PROPERTIES over every governed migrate leg. The finding leg is a leg: the contract
  gains the a28 FORK-1 population for `_migrate_finding_scope` (the §HELD shared-test edit) and the
  reference measures `backfilled` from the UPDATE's result, never a pre-count (MP-10). NOT an exemption.
- **S-4:** the merge of `annotate`/`_transition` into `findings.py::_run_guarded` is 64b's change, so 64b
  owns its consequence: 64b's contract declares `CAS_SEAM_DRIVERS = {"findings.py::_run_guarded": …}` in
  its OWN test module (58 am-9 FK-r3-4's discovered registry — the exact shape 58-r3 documents in
  `REPORT-contract-58-r3.md` §FLAGS F-r3-4), and 58-r2's static driver table entries for the two merged
  doors are RETIRED in 64b's §HELD with a DUAL note. Whichever wave lands second re-derives; the property
  (every CAS verb driven with the injection) does not move.

## 5. FK-9 — the signature-checking form (MP-9)

- Each ruled symbol is declared under `if TYPE_CHECKING:` as a **typed CALL** with every ruled keyword
  surface (`_ruled_64b_i_report_takes_the_caller`'s idiom — the adversary's positive control): mypy reports
  `[call-arg]` on a renamed or missing kwarg, so the bound's typecheck half discharges only on the ruled
  SHAPE. The declared surfaces are the adversary's derived list: `authorize_guarded(projection=,
  target_scope=, row_id=|number=)`, `guarded_write(params=, target_scope=)`, `FindingLedger.report(title,
  body, *, subject, scope=, …)`, `annotate(…, subject=)`, `AppContext.findings(capability=, scope=)`,
  `ReportResult.scope`, `classify_zero_row_cas(…, ledger_verdict=)`, `_resolve_identity` — re-derived by the
  author's `derive_symbols.py`-shaped scan (declared == exercised, both directions RED).
- These declarations are PERMANENT signature pins (mypy checks `TYPE_CHECKING` bodies after the build too) —
  no cleanup step needed for them.
- The runtime reach-arounds (`x: Any = governed.…`, `vars(module).get(…)`) get the self-destruct they lack:
  a pin derives the alias set from the contract files' AST and asserts it ⊆ the bound's unbuilt symbols
  (read from `scripts/pending_contracts.yaml`); a symbol that has landed but is still reached through `Any`
  → RED naming the alias. When the bound is deleted (§11 item 15), the alias set must be EMPTY.

## 6. Fix the CLASS — every survivor's property (ratifying the adversary's CLASS lines; one sweep each)

| survivors | property (∀ …) | sweep's domain source |
|---|---|---|
| reference, WB1, WB2, WB17 (MP-1/2/3) | ∀ write verb × address {id, number} × {invisible, nonexistent, visible-denied}: invisible ≡ nonexistent bytes; visible-denied = `GovernedDenied` | spec dict's write verbs (am-7 §4) |
| WB3 (MP-4) | the zero-row classifier authorizes the PASSED action — fixtures where READ and WRITE DISAGREE (readable-unwritable) ∀ actions the classifier serves | `Action` enum × a re-scope construction per action |
| WB4 (MP-5) | every authorization input is read per call | the four degradations (§1) |
| WB10 (MP-7) | the budget is counted at the SEAM, per table | §1's table |
| WB19 (MP-6) | per-field provenance (`actor`, `actor_agent`) ∀ event producers | callers of the append shell (derived) |
| WB21 (MP-8) | ONE identity-compare site (routing is not sharing) | AST over every dispatcher (comms, findings, tasks, claim) |
| WB22b (MP-11) | ∀ migrate legs: write set == the requested table (+ named dependencies) | `_MIGRATE_TABLES` (derived) × every OTHER table byte-identical |
| WB23 | ∀ (verb, param) outside the verb's spec: a teaching refusal, never silent acceptance | the spec dict matrix (#319's shape) |
| MP-12 | ∀ scope writers: value ∈ DOMAIN | §2 |
| MP-9 | declarations certify SHAPE | §5 |
| S-2/MP-10 | ∀ migrate legs: `backfilled` is measured | a28's leg derivation |

- **Loop status (for the operator):** 64b-i at round 1 → r2. No property has struck twice within 64b; MP-1/2/3
  are the FK-6 class am-7 ruled mid-pass (the graded commit predates it). If r2's grade finds a second instance
  of ANY row above, the ruling — not the contract — re-opens (CLAUDE.md rule 5).
- No code/tests/store touched; this doc only; no attribution trailer.
