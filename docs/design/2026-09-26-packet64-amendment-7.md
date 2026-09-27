# Packet 64 — ruling amendment 7 (sidecar-64, 2026-09-26): the 64b-i contract forks — FK-7 the SYSTEM writer (calibration drift) rides the exempt channel UNOWNED, FK-1 `subject=` is the ONE identity kwarg ∀ ledgers (the title becomes `title` at the Python seam), FK-2 derived over the UNOWNED-LEGACY set, FK-6 invisible ⇒ not-found DERIVED from the one pre-read, FK-8 confirmed, FK-3/4/5 confirmed with riders

Rules `REPORT-contract-64b.md` (`d8ea4ba`) §5 FK-1…FK-8 per lead-63c-2's Task 18. Amends the kickoff
§2 (F1 rider), §4.3 (item 1's address + the zero-row/invisible classification) and am-2 §7 (the seam
kwarg name). Facts read at `d8ea4ba`: `server._CalibrationFindingsAdapter.report_drift_finding` →
`FindingLedger.report(subject, body, kind=, area=, category=, created_by=)`, constructed at the DI core
with NO principal in reach (`calibration.engine.FindingsPort`); `governed.governed_exempt(name, *,
statement)` captures the entering frame as origin; the test-side `TreeWriteAllowlistEntry` carries
`exempt_name` / `statement` (golden) / `effect` / `l1_site`; `authorize_guarded` pre-reads
`type::record(table, $id)` UNFILTERED and DENIES via `pdp.authorize` — the 63b-ib memory pin
`test_a_member_superseding_a_foreign_row_denies_with_zero_effect` expects `GovernedDenied` for an
INVISIBLE foreign row; `_report_fragment` is TWO statements (counter `LET` on `finding_counter`, an
ungoverned table + one parametrised `CREATE … CONTENT {…}` whose text is deterministic when
`supersedes` is absent); `principals._migrate_memory_scope` passes ONE function-local statement to both
the token and the driver.

## 0. Rulings in one screen

| fork | ruling |
|---|---|
| **FK-7** SYSTEM writer | **RULED — the author's recommendation, made concrete.** `FindingLedger.report_system(title, body, *, kind, area, category, created_by)`: owner `NONE/NONE`, `scope = keep_scope(project keep)` via the SAME `get_or_create_keyed(PROJECT_KEEP_KEY, …)` every legacy leg uses; the row is written INSIDE `with governed_exempt("calibration-drift", statement=<the CREATE text>)` entered in `report_system`'s own frame; a NEW F5 exempt entry with a golden + an effect predicate; ONE production caller (the adapter), no served verb; a missing project keep is a LOUD, non-fatal boot fault. Never a fabricated owner; never a `None`-Subject path through `report`. §1 |
| **FK-1** identity kwarg | **`subject=` is the ONE identity kwarg ∀ ledgers** (memory 63a, findings 64b, tasks 64a) — `caller=` REJECTED. The colliding TITLE parameter is renamed at the Python seam only: `FindingLedger.report(title, body, …)`, `TaskLedger.create_task(title, description, …)`, `supersede_task(…, title=, …)`. Served params, columns, models keep `subject`; the dispatcher maps served `subject=` → `title=` at ONE site per tool. §2 |
| **FK-2** half-pair ∀ | **Over the DERIVED UNOWNED-LEGACY set, not a hand pair.** Domain = every table whose migrate golden WHERE contains `owner_principal IS NONE` (the ∀-tables WHERE pin already holds the goldens); today that yields {memory, finding}, at 64a {memory, finding, task}. Memory RED@HEAD is a pin under a ruled property — the lead assigns its fix (recommend 64b's builder: the pin is 64b's, the fix is the ONE migrate function). §3 |
| **FK-6** write on an invisible row | **CONFIRMED, with the mechanism that keeps §4.3's ONE pre-read:** invisibility is DERIVED in Python from the same pre-read row — after a WRITE/DELETE/SET_SCOPE deny, `pdp.authorize(subject, READ, resource)`; READ also denied ⇒ the substrate raises `GovernedInvisible(GovernedDenied)`; the ledger maps it to its not-found (`FindingNotFoundError`, byte-identical to a nonexistent address); READ allowed ⇒ `GovernedDenied` (visible-but-unwritable). Zero extra reads. `authorize_guarded` takes an ADDRESS (`row_id=` or `number=`) so by-number writes are ONE read too. §4 |
| **FK-8** R8 read budget | **CONFIRMED, no exemption.** The footer takes the resolved row; ZERO footer registry reads on a governed write. Rider: the 16-leg pin's verb axis is DERIVED from the spec dict (F7), never a hand-list of 8. §5 |
| **FK-3** `classify_zero_row_cas` | CONFIRMED (sync `ledger_verdict: (row | None) -> T`, helper RETURNS). Rider: the `None` leg (row vanished between CAS and re-read) is a REQUIRED generated case ∀ verbs — the ledger's verdict callable decides it, the helper never guesses. §5 |
| **FK-4** `target_scope=` / `params=` | CONFIRMED. Rider: `SET_SCOPE` with `target_scope=None` is a LOUD refusal (a typed `ValueError` naming the missing target), never the silent `NoRows` that hid #429's dead branch. §5 |
| **FK-5** P-F3 heal text | CONFIRMED (the pin's docstring, 63c P-A3's precedent). §5 |

## 1. FK-7 — the system writer

- **Question.** The calibration engine files a drift finding at boot with no principal, no capability, no
  Subject. §4.3 routes EVERY finding write through `authorize_guarded`. What is a system writer?
- **Answer.** A system writer is the finding-side twin of the migrate: a governed-table write that is NOT
  member-reachable, evidenced by a NAMED exempt entry, writing the UNOWNED shape (F1: owner
  `NONE/NONE`, scope = the project keep). It never enters `report` (whose Subject is required — a
  `subject=None` door would be a second brain beside the PDP) and never fabricates an owner (F1's
  α-fabrication class: an owner is a principal who PROVED it wrote the row; the engine proved nothing).
- **Mechanism (ONE fragment builder, two entry points):** `_report_fragment` gains the governed triple as
  PARAMETERS (`owner_principal`, `owner_agent`, `scope`); `report(title, body, *, subject, scope=None, …)`
  passes the Subject's pair + `resolve_write_scope(...)`; `report_system(...)` passes `NONE, NONE,
  keep_scope(project keep)`. Both run the SAME two statements; ONE IMPLEMENTATION by construction (pad the
  CREATE → both move; the mutation proof is the sharing pin).
- **Attribution (the F5 exempt leg, current substrate shapes — no new field):**
  `fragment = self._report_fragment(...)`; `with governed_exempt("calibration-drift",
  statement=fragment.statements[1]):` → `await self._apply([fragment])`. The token's text IS the executed
  CREATE text (one source, as the migrate does with its function-local statement); the test-side entry
  `TreeWriteAllowlistEntry(site=(findings.py, "report_system", CREATE), exempt_name="calibration-drift",
  statement=<the GOLDEN CREATE text with supersedes: NONE and the governed triple>, effect=…,
  l1_site=False, runtime_observed=True)` — `l1_site=False` because the literal lives in `_report_fragment`
  (already the L1 site of the `report` LABEL entry), exactly the 63b-i-a §5.1 Q1 shape for a frame whose
  statement is a call result. Leg 4 holds because the `with` is entered in `report_system`'s frame.
  **Effect predicate (the leg that stops laundering):** created row `owner_principal is None ∧
  owner_agent is None ∧ scope == <project keep> ∧ status == open ∧ area == CALIBRATION_AREA ∧
  created_by == DRIFT_CREATED_BY`; schema delta empty. A second system writer tomorrow REDS this entry
  and gets its OWN name + entry (deny-by-default working); never a parametrised name.
- **Reach:** `report_system` is in NO served dispatch table (`_FINDING_ACTIONS` exact-set pin) and has
  EXACTLY ONE production caller — `_CalibrationFindingsAdapter.report_drift_finding` — pinned by a
  call-graph derivation (`lore_impact`-shaped, whole production tree), the one-producer idiom. The F5
  battery DRIVES the adapter under observation (a fake engine or a direct call): the write CLASSIFIES via
  the exempt entry; CONTROL: the same write with the token removed → UNCLASSIFIED RED; a member `report`
  stays on the LABEL leg.
- **The project keep is a PRECONDITION, not an assumption:** no project keep ⇒ `report_system` raises the
  substrate's typed refusal (63-rulings: "no project keep → governed write REFUSES"); the ADAPTER catches
  that ONE typed class, logs `calibration.drift.unfiled` at ERROR with the reason, and the boot CONTINUES
  (an alarm that cannot be filed must not take the server down; it must be seen). Pin: unprovisioned keep →
  boot completes, exactly one ERROR record, zero finding rows; CONTROL: provisioned → one row, no ERROR.
- **Consequences named (Leg 1):** the drift finding is READABLE by every household member (project keep —
  the fleet-wide alarm it is); `acknowledge`/`resolve`/`wontfix`/`annotate` by any household member (F4's
  keep rule — the operator re-baselines and a member closes it); `set_scope` owner-only ⇒ ADMIN only (nobody
  owns it); 64d `--delete-obj <principal>` never touches it (unowned). `created_by` stays the display
  string `DRIFT_CREATED_BY` (byte-inert, like every legacy row).
- **The dedupe READ (`has_open_drift_finding`) is 64b-ii's** (am-3 D-1b: reads flip in 64b-ii). Ruled
  shape for that wave, so the author does not invent one: a typed `SystemReader` sentinel (NOT `None` —
  a `None`-means-all read is fail-OPEN and one bug away from serving everything), accepted by the read
  seam under a deny-by-default construction allowlist with ONE entry (the adapter), reach-pinned like the
  exempt entry; the F3 ∀-reads pin counts a `SystemReader` read as attributed iff its site is listed.
  Named decision point: 64b-ii's contract; owner: its author; this amendment is the ruling it cites.
- **DRY row:** `report_system` REUSES `_report_fragment` (parametrised); the adapter is unchanged in
  shape (one call swap); `governed_exempt` REUSED; the allowlist entry EXTENDS the registry. No new
  primitive.

## 2. FK-1 — `subject=` everywhere; the title is `title` at the seam

- **Question.** The governed identity kwarg collides with the finding/task TITLE parameter `subject`.
  Which concept keeps the name?
- **Answer.** The GOVERNING concept. `Subject` is the PDP's noun; `resolve_subject`, `authorize_guarded(
  subject, …)`, `read_filter(subject, …)` and memory's 63a seam all say `subject`; every governed
  dispatcher passes it. Two names for that one concept across ledgers (`subject=` for memory, `caller=`
  for tasks/findings) would show at every governed call site in `server.py` — the naming rule ("once a
  name is chosen for a concept, use it everywhere") applied to the concept that governs everything. The
  title's Python parameter is the cheaper rename: `title` in `FindingLedger.report`,
  `TaskLedger.create_task`, `TaskLedger.supersede_task` (three signatures; keyword call sites move). The
  SERVED params (`lore_findings subject=`, `lore_tasks subject=`, `create_many` item keys), the columns
  and the pydantic models keep `subject` — the served surface is byte-unchanged; the dispatcher maps
  served `subject=` → `title=` at its ONE ledger call per verb.
- **Pin:** `_governed_contract_64.LEDGER_IDENTITY_KWARG == "subject"` AND it equals the memory seam's
  kwarg name DERIVED by `inspect.signature` (never a second literal); ∀ ledger write verbs across the
  three ledgers (derived from the spec dicts, F7), the `subject` parameter is annotated `Subject` and is
  keyword-only; no ledger signature carries a `caller` parameter (bare-name sweep, per-hit verdicts).
- **64a inherits this ruling verbatim** (the lead asked for ONE ruling for both).

## 3. FK-2 — the half-pair refusal over the derived set

- The property: *∀ UNOWNED-LEGACY tables, the only half-pair a governed create cannot produce is
  owned-but-unscoped; scoped-but-ownerless is the table's own migrated state* (kickoff §2's rider (ii)).
  Its DOMAIN's source of truth is the migrate goldens: a table is UNOWNED-LEGACY iff its backfill WHERE
  contains `owner_principal IS NONE` — read from the ∀-tables WHERE pin's golden table, never a hand pair.
  D-1's "no registry to derive from" is answered: the goldens ARE the registry (a `LegacyMapping` row with
  disposition `STRING-UNRESOLVABLE` is the second derivation; the pin asserts the two agree — completeness
  both ways).
- Generated sweep: ∀ derived table × {owned-but-unscoped → refused, byte-inert; scoped-but-ownerless →
  `already_migrated`, byte-inert; clean → `backfilled == N`}. Memory's red leg is the property doing its
  job on a table whose migrate predates the rule.

## 4. FK-6 — invisible ⇒ not-found, derived from the one pre-read

- **The conflict the author did not name:** §4.3 item 1 merges the ledger's resolution read INTO
  `authorize_guarded`'s pre-read (rider (v): ONE read). That pre-read is by `type::record` and UNFILTERED,
  so an invisible row IS read and `pdp.authorize` DENIES it — `GovernedDenied` names `{table}:{row_id}`:
  an existence oracle, and the 63b-ib memory pin PINS that behaviour for memory. The author's shape
  (resolve THROUGH the filter first) restores not-found but costs a SECOND read on every write and
  contradicts rider (v).
- **Ruling — derive, don't re-read:** in `authorize_guarded`, after a deny for `action ∈ {WRITE, DELETE,
  SET_SCOPE}`, evaluate `pdp.authorize(subject, Action.READ, resource)` on the SAME row: READ denied ⇒
  raise `GovernedInvisible` (a subclass of `GovernedDenied`, so every existing `except GovernedDenied`
  and the 63b-ib `pytest.raises` stay green — additive); READ allowed ⇒ `GovernedDenied` as today. The
  finding ledger catches `GovernedInvisible` at its ONE gate site and raises `FindingNotFoundError` with
  the SAME text a nonexistent address produces (byte-diff pinned: invisible row vs no row → identical
  bytes; CONTROL: visible-but-unwritable → `GovernedDenied` naming the row). 64a maps it to the task's
  not-found the same way. Admin (AllRows) never reaches either branch.
- **The address:** `authorize_guarded(..., row_id=…)` OR `number=…` (mutually exclusive, one required):
  the pre-read is `type::record(table, $id)` or `SELECT … FROM <table> WHERE number = $n LIMIT 1` —
  still ONE read for a by-number write. Rider (v)'s round-trip count is pinned ∀ write verbs × {by id,
  by number} (generated).
- **Sibling, NOT ruled here (quantifier law — derived on `finding`, stated over `finding` + `task`):**
  memory serves `GovernedDenied` for an invisible foreign row today, and memory ids are CONTENT-DERIVED
  (uuid5 over text) — a member can hash a text and probe whether another principal remembers it. Filed
  as a finding for the lead; the mapping to memory's not-found is the memory owner's edit (63c or
  64b-ii), one `except` at its gate site, additive under the subclass.

## 5. FK-8 · FK-3 · FK-4 · FK-5 — confirmations with riders

- **FK-8:** R8's read budget is POLICY (one place decides it — `_with_comms_footer`'s docstring says so).
  The capability path resolves the agent row ONCE in `_resolve_identity`; the footer REUSES it
  (`resolved=own_row`). No exemption: the R8(2) fallback is gone for governed calls (am-2 §7), so a second
  read would serve no fact the first did not. Rider: the pin's verb axis derives from the F7 spec dicts
  (∀ write verbs × {agent supplied, omitted}); a verb added to the spec with no leg → RED.
- **FK-3:** `classify_zero_row_cas(store, *, table, row_id, subject, action, ledger_verdict)` — the helper
  re-reads ONCE, asks `authorize` on the fresh row (DENY ⇒ `GovernedConflict`; the §4.3 item 4 rule), else
  RETURNS `ledger_verdict(row)`. Rider: `row is None` (deleted between CAS and re-read — reachable only via
  64d's delete, constructible now) is passed THROUGH to `ledger_verdict`; the generated sweep ∀ CAS verbs
  includes that leg, and no verb's verdict callable may raise a bare `KeyError`/`TypeError` on `None`.
- **FK-4:** `target_scope=` on `authorize_guarded`/`guarded_write` (SET_SCOPE's `_grantable` needs the
  target — the #429 branch was dead without it, measured) and `params=` on `guarded_write` → CONFIRMED.
  Rider: `action is SET_SCOPE and target_scope is None` ⇒ a typed `ValueError` naming the missing target
  BEFORE any read — never `NoRows`.
- **FK-5:** the three-step heal rides the pin's docstring (P-A3). The served refusal stays the engine's
  (redacted field name); the migrate's own teaching prose is unchanged.

## 6. Loop status (for the operator, via the lead)
- 64b-i's contract is at its FIRST adversary round; these forks are pending there. No property has
  struck twice in 64b-i. Two rulings here are CLASS routings by construction (FK-2's derived set, FK-6's
  derived invisibility) so an instance-level sibling cannot arrive as a second round.
- No code/tests/store touched; this doc only; no attribution trailer.
