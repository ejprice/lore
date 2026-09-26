# Packet 64 — kickoff rulings: F1–F9 + the #417 fork, the 64b-first contract worklist, the contract-ahead boundary, inventory seeds, operator forks (sidecar-64, 2026-09-26)

brief-base v16 read · brief project v7 read · store reference read FIRST
(`docs/reference/surrealdb-31-capabilities.md` — cited below by §1.1 / §1.2 / §1.4 / §1.5 / §1.8 / §2 /
§3 / §4 / §5; never re-transcribed).

**Authority.** Sidecar rulings are authoritative for forks (operator ruling 2026-09-24); only MAJOR scope
or architecture goes to the operator — §15 names four such items, each with my recommendation. Binding
inputs: operator ruling F0 (design + contract run AHEAD of 63c; 64 contracts land NEW test files only;
edits to 63c-shared files are a held integration patch; every 64 BUILD is serial after 63c) and pool 30
(58 lands BEFORE 64; 64a governs 58's extracted task-side guarded-append shell). Governing design:
`docs/design/2026-08-28-packet63-retrofit-rulings.md` (cited as **63-rulings**); the 63c ruling
`docs/design/2026-09-13-packet63c-remainder-ruling.md` + amendments 2/14/21/22/24/25 (cited as **63c** /
**am-N**); `docs/design/2026-08-21-lore-authorization-model.md` (cited as **authz**); the packet file
`docs/plans/v2/64-governed-retrofit-tasks-findings.md` (cited as **P64**).

- **Graded:** `ae54f20` · HEAD-at-report: `ae54f20` · SAME (`lore_index()` watched root `/workspace`,
  branch `feat/surreal-unification`, git_ref `ae54f20`; last_sync 222 s old at read time). ⚠ The 63c
  fix wave (`test_fixwave_a19a/a19b_63c_i_a.py`) is UNCOMMITTED in the shared tree; nothing below rests
  on it.
- **Packages considered:** none — no NEW package mechanism is specified. Every mechanism ruled here is an
  EXTENSION of a shipped seam (`authorize_guarded`/`GuardedPlan`, `read_filter`, `resolve_write_scope`,
  `migrate_governed`/`LegacyMapping`, `_governed_field_specs`/`_governed_index_statements`,
  `CommsActionSpec`, the F5 substrate, `AuditStore.append_fragment`). The 61/62 bespoke-PDP verdict
  (authz §11) stands, cited not re-argued.
- **Reuse ledger:** 0 production symbols RULED by name as final; every candidate symbol is the contract
  author's/builder's to name, with the DRY row it owes listed in §17 (nine candidates, each an EXTEND or a
  REUSE of a named existing symbol — none hand-rolled).
- **Capability check (brief-base §4):** everything demanded was reachable — lore MCP served every symbol
  read (`lore_get_symbol` × 46, `lore_verify` × 4, `lore_recall` × 3, `lore_findings get` × 13); `Read`,
  `sed`, `awk`, read-only `git`. Text-search binaries are hook-blocked (#473): every textual sweep below is
  `awk` over an explicit file list and is SAID so where used. No pytest run (63c holds the lane, #466); no
  live probe (no ruling needed an engine fact the store reference does not carry).
- **decisions-needed (operator):** §15 OF-1 (task default scope — §10-N amendment), OF-2 (F5's served
  break shape at 65), OF-3 (F8 orphaning as a 64 wave), OF-4 (F9's `number` count-leak bound at a HOSTED
  65). Everything else is a HOW inside confirmed scope.
- **receipt pointers:** §0 (one screen) · §1 (facts F-1…F-18) · §2–§10 (F1–F9) · §11 (#417 + the owned
  findings) · §12 (a: the 64b-first worklist) · §13 (b: the contract-ahead boundary) · §14 (c: inventory
  seeds) · §15 (d: operator forks) · §16 (riders roll-up) · §17 (flags, findings filed, DRY, discipline).

---

## 0. The rulings in one screen

| # | fork | ruling |
|---|---|---|
| **F1** | column mapping | **UNOWNED-LEGACY for BOTH tables** — `owner_principal`/`owner_agent` NONE/NONE, `scope = keep:<project>`; `provenance.created_by` (task), `finding.created_by`, `events[].actor` STAY as display strings, byte-inert. "Exactly equals a registered agent name" is a guess wearing a mapping (the registry id is `uuid5(session, name)`; N rows per name) — REJECTED, exactly as 63-rulings §2.1 rejected it for `brief`. The pending-traffic footer's exact-match is a third-person render courtesy, not a mapping. §2 |
| **F2** | the CLAIMANT column | **`task.owner` STAYS the CLAIMANT** (string, `owner IS NONE` CAS gate, `query owner=` filter, `resolve_holder` — all unchanged); post-64 it is SERVER-DERIVED (the Subject's agent NAME) instead of caller-supplied, so legacy and new rows share one shape and nothing migrates. The governed pair is the CREATOR (DELETE/SET_SCOPE authority; the one vocabulary the shared emitter gives every table). NO `claimant_agent` link at 64 — that is packet 57's fork 3 (owner→registry resolve), named, not pre-empted. Served vocabulary: "owner"/"held by" = the claimant (the word every fleet brief already knows); the governed pair renders as "created by … · scope …" via `render_subject_bound` — NEVER the word "owner" (Leg 1: one word, one meaning; pinned). §3 |
| **F3** | claim under Keep scope | Claim is a **WRITE on the task row**: any household member of a keep-scoped task; the exact (principal, agent) creator of a private one. Under §10-N's `principal-private` default a lead-created task is claimable ONLY by the lead's own agent — the fleet's lead→agent handoff breaks → **OF-1 (operator): recommend tasks default to the PROJECT keep** (the mission's "byte-unchanged fleet behaviour"). The CAS rides the substrate as **authorize-first, execute-later**: `authorize_guarded` (Python gate, one pre-read that ALSO projects the ledger's columns) → the ledger's OWN guarded shell (post-58: the extracted task-side shell) takes `plan.guard()` as one more WHERE conjunct → `plan.compose(shell)` appends the audit fragment when required → ONE transaction. Never a second guarded path; a zero-row outcome is re-classified by the ONE #407 helper (re-read → `authorize(fresh)` denies ⇒ `GovernedConflict`, else the ledger's own lost-race verdict — a claim LOSS stays a RESULT). §4 |
| **F4** | supersede / resolve / annotate / wontfix | Task supersede = guarded WRITE on the predecessor (household under keep) + a CREATE owned by the superseder; successor scope = `resolve_write_scope(subject, scope, default=<tool default>)` — NEVER silently inherited. Finding supersede (`report(supersedes=X)`) mutates nothing on X → needs READ of X only (X resolved THROUGH the read filter; invisible ≡ unknown, byte-identical). `acknowledge`/`resolve`/`wontfix`/`annotate` are all WRITEs (household may; `wontfix` vanishes nothing — the row and its history stay). Hard DELETE: no served verb on either ledger; the substrate DELETE branch is exercised by the #429 positive-control pin, and by F8. 58's re-anchor of dependents under governance = a SYSTEM effect (`governed_exempt("supersede-reanchor")`, statement-shape-pinned), never N guarded writes and never an existence oracle. §5 |
| **F5** | the caller identity args | `created_by`/`actor`/`owner` become OPTIONAL and are a SELF-CONSISTENCY CHECK (63c Q4a's `agent=` shape, ONE site): supplied ⇒ must equal the Subject's own agent name, else a teaching `GovernedDenied`; omitted ⇒ derived. Never identity, never ignored (accept-and-ignore is the forbidden silent lie), never a lookup key. The string columns stay POPULATED from the Subject (display provenance, #100's name convention) and `events[]` gains `actor_agent` (the agent RecordID) beside `actor`. **OF-2 (operator):** whether the args are additionally RETIRED (foreign-param refusal) at 65 — recommend NO: keep them as checks; the only served break 65 owns is `capability=` required. §6 |
| **F6** | `blocks` as a governed relation | Joins by derivation; no edge columns; reads ride the task filter (am-2 A1's `to`/`briefed` precedent). A `blocked_by` entry naming a task the creator cannot READ is refused at create/supersede BYTE-IDENTICALLY to a phantom (the existence check rides the creator's read filter — no oracle). The claim CAS's blocker-status resolve and `query`'s partition read are SYSTEM reads inside the CAS/snapshot: the caller learns only the outcome, never a status. `blockers`/`get`/`query` render ids bare (an id already sits in a readable column) and decorate ONLY visible rows. §7 |
| **F7** | `requires_capability` home | ONE mechanism: a flags-only base `GovernedVerbSpec(requires_capability, limit_cap)` that `CommsActionSpec` EXTENDS; `_TASK_ACTIONS`/`_FINDING_ACTIONS` become `dict[str, GovernedVerbSpec]` (iteration/`list()`/`in` unchanged; the `action ==` chain and its AST vocab pin untouched). ALL 19 legs flip TRUE in 64 (every task/finding verb is governed: reads need the filter, writes the stamp) WITH the enforcing wave (ii-a §4). `rollup` becomes capability-REQUIRED (its task/finding legs are governed). §8 |
| **F8** | §10.7-Z orphaning + #404 | **Lands in 64 as its own small wave (64d)** after 64a/64b, over the DERIVED governed table set (a production `governed_node_tables(ddl)` the test substrate then imports — ONE derivation). Mechanism: ONE predicate `UPDATE <t> SET owner_principal = NONE, owner_agent = NONE WHERE owner_principal = $p` per table inside the delete transaction + ONE audit row per table (count + bounded ids), under `governed_exempt("principal-delete-orphan")` with evidence; the pin-the-miss dies with it. #404 closes by making the store method own its readiness: every governed read in `delete` is gated on `_table_exists` (the memory read's existing idiom), never on a caller's slice. **OF-3 (operator):** a wave added to 64. Re-open trigger on am-25 half (ii): finding #488. §9 |
| **F9** | oracles in the finding ledger | `chain_head` walks `supersedes` links THROUGH the read filter: the served head is the head of the VISIBLE chain, the bound line names the set — never a "withheld" count. `get`/`chain_head` on an invisible number renders byte-identically to a nonexistent one. The global monotonic `number` is an ACCEPTED, PINNED bound (a count of others' activity, never content) for the single-principal fleet — **OF-4 (operator):** 65 IS hosted enablement, so the operator confirms carrying the bound into a hosted deployment (re-open: per-keep numbering, a served-handle break). §10 |
| **#417** | PDP self-containment reach | 64 composes NO new multi-disjunct IR node — the CAS conjunct is caller SurrealQL ANDed beside the parenthesised guard, not an IR node — so the pinned bound STANDS (STOP-rule); 64 adds the composition-safety pin for the conjunct (the shell parenthesises it). §11 |

**Where I CHOSE between two readings (brief-base §2 — written down, not silent):**
1. 63-rulings §3.1 says *"`task.owner`/`created_by`"* as if two columns; P64 corrects it (only `owner` is a
   column, and it is the claimant). I read §3.1's disposition sentence (*"a bare name is never promoted"*)
   as governing BOTH the column and the blob string — reading B; reading A (the disposition applies to
   `created_by` only and `owner` gets a link) is 57's territory and REJECTED here (§3).
2. §10-N *"tasks→`principal-private`"* — reading A: the default is a HARD ruling 64 must realise; reading B:
   §10-N was written before the 3-way rule's WRITE semantics made a private task un-claimable by a sibling
   agent, and the mission's "byte-unchanged fleet behaviour" governs. I pick B and put it to the operator
   (OF-1), because §10-N is operator-CONFIRMED text — a sidecar does not overrule it silently.
3. P64 §Scope IN 6 reads *"64 is [SET_SCOPE + admin SET_OWNER]'s first consumer"* as either "build served
   verbs" or "build the substrate branches". I rule: `set_scope` IS a served verb on both tools (owner-only,
   grantable target — a member's own row); `set_owner` is a SUBSTRATE function + a `lore-adm set-owner`
   admin verb, NOT an MCP verb at 64 (no member-reachable need; trigger: the first hosted transfer request).

---

## 1. The facts this ruling rests on (read at `ae54f20`; cited by symbol, never re-transcribed)

- **F-1 — `task` columns** (`surreal_schema._TASK_FIELD_SPECS`, awk over the module — said so): `subject`,
  `description`, `status` (ASSERT closed domain), `owner option<string>`, `claimed_at option<datetime>`,
  `blocked_by array<string> DEFAULT []`, `provenance object FLEXIBLE`, `superseded_by option<string>`,
  `created_at datetime`, `updated_at`/`summary`/`report_path` `option<>`. ONE ASSERT (`status`); one
  birth DEFAULT (`blocked_by`). NO `created_by` column — `TaskLedger._new_task_content` writes
  `provenance.created_by` + `events: []`.
- **F-2 — `finding` columns** (`_FINDING_FIELD_SPECS`): `number int`, `kind`/`subject`/`area`/`category`/
  `created_by` each with `_NON_EMPTY_STRING_ASSERT`, `status` (`DEFAULT 'open' ASSERT …`), `body`,
  `created_at DEFAULT time::now()`, `supersedes option<record<finding>>`, `provenance object FLEXIBLE`.
  SIX ASSERT-bearing columns; two birth DEFAULTs.
- **F-3 — the readers' decode models:** `Task.status: TaskStatus` and `Finding.status: FindingStatus` are
  `Literal`s (pydantic-validated per row in `_row_to_task`/`_row_to_finding`); every other string column
  decodes as `str` (any value). So the ONLY reader-aligned store ASSERT on either table is `status` —
  the same shape 63c Q3 found on `agent` and ii-b §13 on `message.grade`.
- **F-4 — the writers' app caps:** `TaskLedger.transition` validates the edge + `_validate_done_summary`;
  `create_task`/`supersede_task` run `_reject_unusable_blockers` + `_refuse_a_cycle`; `FindingLedger.report`
  runs `_require_non_empty_area_category` (area/category ONLY — `kind`/`subject`/`created_by` have NO
  ledger-side blankness check; the tool layer's `_require_finding_arg` is the only guard); `annotate`
  rejects a blank note via `lorerunes.is_blank`.
- **F-5 — the claim CAS** (`TaskLedger._claim_fragment`): `LET $clm_resolved = (SELECT VALUE record::id(id)
  FROM task WHERE record::id(id) IN $blocked_by AND status IN $terminal)` then `UPDATE type::record('task',
  $id) SET owner=$owner, status='claimed', claimed_at=time::now(), updated_at=time::now() WHERE status='open'
  AND owner IS NONE AND superseded_by IS NONE AND array::len(array::distinct(blocked_by)) =
  array::len($clm_resolved)`. `claim_task` pre-reads the row (`_select_row`), applies, then decides victory
  by OWNER IDENTITY on a post-CAS read; a LOSS is a `ClaimResult(claimed=False)`, never an exception.
- **F-6 — the guarded shells at HEAD:** tasks hand-roll THREE (`_transition_fragment`, `_supersede_fragment`,
  `_claim_fragment` — the 58 packet's DRY item; `lore_verify TaskLedger._guarded_append_fragment` →
  not_found, so 58 has NOT landed); findings have ONE (`FindingLedger._guarded_append_fragment`, with
  `status_target`/`expected_from`). Every shell is `LET $x = (UPDATE … WHERE …)` + `IF array::len($x) == 0
  { THROW … }` — the SAME shape `GuardedPlan.fragments` emits (`LET $gw_hit = (UPDATE … WHERE (<guard>)
  RETURN AFTER)` + `THROW "governed_conflict:<t>:<id>"`).
- **F-7 — the substrate's compose-with-caller shape EXISTS:** `governed.authorize_guarded(subject, action,
  *, table, row_id, audit, store) -> GuardedPlan` (one pre-read projecting the three governed columns;
  Python gate; RES-2 refuse) and `GuardedPlan.fragments(set_fragment, params)` (the by-id guarded
  mutation + audit append when `requires_audit`); `guarded_write` = the two composed. `GuardedPlan`
  carries `guard_fragment`/`guard_params`/`requires_audit`/`audit`/`pre_read_row` as fields.
- **F-8 — the #407 idiom, measured:** `TaskLedger.transition`, `supersede_task`, `FindingLedger._transition`,
  `annotate` each carry `except SurrealConnectionError: raise` / `except TxnContentionExhaustedError:
  raise` / `except SurrealStoreError: <re-read + re-validate → state-named error>`. FOUR sites, one policy.
- **F-9 — `StoreHandle` accessor:** `LocalMemoryBackend.handle` exists; `lore_verify` `TaskLedger.handle`,
  `FindingLedger.handle`, `MessageLedger.handle` → all `not_found`. 64 adds the accessor on both ledgers
  (the `StoreHandle` docstring already promises it: *"64's task/finding ledgers expose the same accessor"*).
- **F-10 — the dispatchers:** `AppContext.tasks(action, task_id, subject, description, created_by, actor,
  status, owner, blocked, blocked_by, since, limit, max_depth, items, summary, report_path, agent, session)`;
  `AppContext.findings(action, id_or_number, subject, body, area, category, created_by, kind, actor, note,
  status, limit, supersedes, items, agent, session)`; `AppContext.claim_task(task_id, owner, *, agent,
  session)`. None carries `capability=`. `created_by` is REQUIRED on create/create_many/supersede/report;
  `actor` on transition/acknowledge/resolve/wontfix/annotate/resolve_many/acknowledge_many; `owner` on
  claim. Each dispatcher's ONE exit runs `_with_comms_footer(..., attributions=(…))` — R8(2)'s exact-match
  fallback ("matched, never authenticated", third person).
- **F-11 — the dispatch tables:** `_TASK_ACTIONS` (8) and `_FINDING_ACTIONS` (10) are plain string TUPLES;
  `_COMMS_ACTIONS` is `dict[str, CommsActionSpec]` with `handler`, `params`, `required`,
  `requires_registration`, `requires_capability: bool = False`, `limit_cap`. The `tasks()` docstring pins
  the `action ==` chain IN the method (an AST vocabulary pin scans it).
- **F-12 — the #420 constants** (`server.py`, read directly): `_GOVERNED_VERBS_ROUTED` = the two memory
  verbs ONLY; `_GOVERNED_VERBS_PENDING_ROUTING` = 6 × 63b + 5 × 63c + 8 × `_ROUTE_64_TASKS` + 10 ×
  `_ROUTE_64_FINDINGS` + 1 × `_ROUTE_64_CLAIM` (the 19 legs P64 counts — re-derived: 19). `awk` over
  `loremaster/tests/*.py` for `observes_routing("` finds markers for the two memory verbs only. ⚠ The
  63b legs are ENFORCED (`requires_capability=True`, 63c F4) yet still PENDING — filed as **#487** (§17).
- **F-13 — the routing derivation** (`test_governed_routing_63a.py::_dispatch_verbs`): a HAND map
  `{lore_comms→_COMMS_ACTIONS, lore_tasks→_TASK_ACTIONS, lore_findings→_FINDING_ACTIONS}` + the
  `(tool, tool)` fail-closed fallback (#427); `_SINGLE_VERB_TOOLS` names `lore_claim_task`. The meta-pin
  checks `routed ⊆ observed` only (one direction).
- **F-14 — the read paths:** `query_tasks` = ONE `execute_read_transaction` (`_candidate_statement` +
  the server-side blocker-status read over the candidates' own `blocked_by`), the partition applied in
  Python via `_is_blocked`; `transitive_blockers` = a `@.{1..n+collect}(<-blocks<-task)` traversal
  (GraphEdgeScan — store-ref §4: never index-served; per-row predicates fine); `direct_dependents` =
  `WHERE blocked_by CONTAINS $id`; `FindingLedger.query` = `SELECT * … ORDER BY number LIMIT n`;
  `chain_head` walks `_select_successors` (`WHERE supersedes = type::record(…)`) to a head;
  `updated_since`/`filed_since` (rollup legs) = rows + a `count() GROUP ALL`, NO `subject=` (unlike
  `MessageLedger.message_activity_since`, which splices `read_filter` into both).
- **F-15 — the migrate seams:** `migrate_governed(table=…)` dispatches memory/agent/message and refuses
  the rest naming 64; `_migrate_memory_scope` (UNOWNED-LEGACY precedent: `UPDATE memory SET scope=$scope
  WHERE scope IS NONE` under `governed_exempt("migrate-governed", statement=…)`, `resolve_operator_principal`
  ambiguity → refuse, `get_or_create_keyed(PROJECT_KEEP_KEY, …)`); `report_unmigrated_governed_rows` =
  `WHERE scope IS NONE` ∀ tables. am-21 CD-1: every leg's WHERE is `scope IS NONE [AND owner_principal IS
  NONE]`; am-22 §3/§4: half-pairs refused, receipts `None` on refusal; am-24 door #1: one refusal naming
  both diagnoses.
- **F-16 — `PrincipalStore.delete`:** refuses while keeping (`keep.keeper`), refuses while OWNING a memory
  row (SF-63-5 interim, gated on `_table_exists(MEMORY_TABLE)` — fail-closed on a fault), cascades
  `principal_key` children first, ONE `execute_transaction`. Its docstring names the FIVE
  `record<principal>` links; the exact-set pin in `test_principal_keys_schema.py` reds when a sixth
  appears — `task.owner_principal` and `finding.owner_principal` are the sixth and seventh.
- **F-17 — the render seams:** `_render_claim_result` says *"is now owned by"* / *"already held by"*
  (the CLAIMANT); `_render_task_detail` composes rows + fenced description + `provenance` via
  `render_attributed`; `_holder_liveness_notice` (#262) reads a task by id at `register` and resolves
  `task.owner` by NAME (`resolve_holder`). `render_subject_bound` (ii-b §9.1) is the ONE bound-line render.
- **F-18 — the PDP:** `_member_filter` WRITE = exact pair on private/server rows, `ScopeInKeeps` for keep
  rows; DELETE = exact pair, scope-independent; SET_SCOPE = exact pair ∧ `_grantable(target)`; SET_OWNER =
  `NoRows` for members. `authorize_filter` = `AllRows` for admin except the audit carve-out.
  `resolve_write_scope(subject, scope, *, default)` is the ONE grant seam. `Resource(table, owner_principal,
  owner_agent, scope)`; `authorize_guarded` builds it from its `table` ARGUMENT (the #414/#415 door).
  `ScopeInKeeps.to_surql` and `Or.to_surql` parenthesise; `And(())`/`Or(())` emit `()` (#418).

---

## 2. F1 — RULING: UNOWNED-LEGACY for `task` AND `finding`; a string is never an owner

- **Question.** Does 63's STRING-UNRESOLVABLE → UNOWNED-LEGACY hold for both `provenance.created_by`
  (task) and `finding.created_by`, and is "exactly equals a registered agent name" a verifiable link?
- **Answer.** YES to the first; NO to the second. `LegacyMapping("task", "STRING-UNRESOLVABLE")` and
  `LegacyMapping("finding", "STRING-UNRESOLVABLE")` join the table beside `brief`: owner NONE/NONE, `scope
  = keep_scope(<project keep>)` via the SAME `get_or_create_keyed(PROJECT_KEEP_KEY, …)` every leg uses. The
  blob/column strings are UNTOUCHED (byte-inert on every non-governed column — am-22 §4's principle).
- **Why.** A bare name resolves to N agent rows (`uuid5(session, name)`); "best effort" is a guess wearing a
  mapping (63-rulings §2.1, the `brief` row, verbatim). The footer's exact-match (`_with_comms_footer`
  R8(2)) is worded third-person precisely because it is *matched, never authenticated* — a render courtesy
  is not an ownership derivation. Fabricating an owner from a string is the α-fabrication class 63c Q2
  refused (a wrong owner is worse than none: it grants a real principal DELETE authority over a row nobody
  proved they wrote).
- **The migrate legs (both tables, one shape — the memory precedent):** `UPDATE <t> SET scope = $scope WHERE
  scope IS NONE AND owner_principal IS NONE` (am-21 CD-1's scope-keyed, self-guarding WHERE — the ∀-tables
  WHERE pin gains `[task]`/`[finding]` rows), under `governed_exempt("migrate-governed", statement=…)`
  (function-local statement, R1 self-containment), driver-routed (R4), idempotent (second run
  `backfilled == 0`). NO order precondition (no link to resolve — 63c §6's "a precondition with no
  mechanism behind it is ceremony"; pinned: `migrate_governed(table="task")` on a store with unmigrated
  agents SUCCEEDS). Operator ambiguity → the shared `resolve_operator_principal` refusal. `blocks` has no
  columns → nothing to migrate (a pin asserts the relation is NOT in `LegacyMapping`'s table set).
- **The half-pair precondition for an UNOWNED-LEGACY table (am-22 §3 re-derived for this disposition):**
  the MIGRATED state is `(owner NONE, scope set)` — so scoped-but-ownerless is the healthy post-migrate row
  here, NOT a half-pair. The only half-pair a governed create cannot produce is `owner_principal IS NOT
  NONE AND scope IS NONE` (owned-but-unscoped) → REFUSE, ONE refusal per am-24 door #1 (count + bounded
  ids + "half-applied"), byte-inert, receipts `None` for counts not measured (am-22 §4).
  **RIDER — and pin it like this:** (i) seed one owned-but-unscoped row → `refused=True`, ZERO rows stamped,
  `SELECT *` before == after; CONTROL: without it `backfilled == N`; (ii) seed a scoped-but-ownerless row →
  NOT refused, byte-inert, counted `already_migrated` (the DUAL of am-25's message rule, ruled for THIS
  disposition — a pin written the other way would forbid the table's own migrated state); (iii) the ∀-tables
  WHERE pin: the golden for `task`/`finding` contains `scope IS NONE` AND `owner_principal IS NONE`.
- **Required-green builds for (i)–(iii)** (am-14's lesson — enumerate before writing the admitted shape):
  a store with 0 legacy rows (`scanned == already`, not refused); a mixed store (N legacy + M governed rows
  with the pair set → `backfilled == N`, governed rows byte-identical); a second run (0 backfilled).
- **F1's S1/S2 seeds (63-rulings §2.3):** S1 = the synthetic old-DDL seed via `frozen_asserted_finding_ddl()`
  / `unbounded_finding_ddl()` (+ the task twins in 64a) — legacy rows written UNDER THE OLD DDL (store-ref
  §1.4's trap); S2 = the real production dump restored into a `:18000` throwaway (NEVER `:18500`) —
  ⚠ UNVERIFIED by me whether 63a's S2 restore instrument is a committed script; the contract author cites
  it by path or STOPs (an instrument that exists only in a report is the #278 class).
- **Re-open trigger:** *"the day a task/finding writer stamps a resolvable LINK for its author"* — none
  exists at HEAD; F5 makes the Subject the author of every NEW row, so legacy rows are the only unowned
  population forever (create-path-immune, like memory's legacy rows under 10.9-B).

---

## 3. F2 — RULING: `task.owner` stays the claimant; the governed pair is the creator; one served word per meaning

- **Question.** Do `owner_principal`/`owner_agent` mean the CREATOR while `owner` stays the claimant? Does
  the claimant become a `record<agent>` link? What happens to the legacy claimant string on migration?
- **Answer.** Creator: YES — the governed pair is the row's owner in the PDP's one vocabulary (DELETE /
  SET_SCOPE authority; the WRITE disjunct on private rows), stamped at create/supersede-successor from the
  Subject (`subject.principal_id`, `subject.agent_id`), exactly as `send` stamps `message`. Claimant: `owner
  option<string>` KEEPS its name, type, CAS role (`owner IS NONE`), filter role (`query owner=`) and
  render role; its VALUE becomes server-derived — the Subject's agent NAME (`own_row.name`, the value a
  caller supplies today) — so a legacy claimant string and a new one are the same shape and NOTHING
  migrates on that column. NO `claimant_agent` link at 64.
- **Why not a link now.** (a) Packet 57 owns "owner→registry resolve" (its fork 3) and the `assignee`
  field — a link column here is 57's design decision made by the wrong packet (P64: "must not be
  pre-empted"). (b) Two live consumers key on the STRING today — `query_tasks(owner=)` and
  `resolve_holder(task.owner)` (#262, retired-inclusive) — and both keep working with a server-derived name;
  a link would force both onto a new read shape in the same wave that governs them. (c) The mission is
  byte-unchanged fleet behaviour; the CAS and the served claim render do not move.
- **What DOES move — the name's provenance:** the claimant name is no longer a claim of the caller's; it
  is the resolved agent's own name. Cross-session ambiguity of a bare name is the SAME bound `resolve_holder`
  already carries (most-recent-heartbeat on ambiguity — 05b F1); the LINK that dissolves it is 57's.
- **Served vocabulary — Leg 1, ONE word per meaning (binding):** "owner" / "owned by" / "held by" in every
  task render and every `lore_tasks`/`lore_claim_task` parameter description means the CLAIMANT and ONLY
  the claimant (unchanged served meaning). The governed pair NEVER renders under the word "owner": every
  governed task/finding render opens with `render_subject_bound` (*"scope: principal … · visible via N
  keep(s)"* — ii-b §9.1 placement, FIRST line), and a detail render adds ONE derived line `created by
  <agent name> (principal <email>) · scope <s>` from typed state (the PKT-28 derived-prose law). The
  store column names stay `owner_principal`/`owner_agent` (the shared emitter — one vocabulary across six
  tables; a per-table rename is a clone). The word appears in a served description once, in the
  `lore_tasks` `owner` param, and its text gains *"the CLAIMANT (server-derived at claim); distinct from
  the row's creator, which the bound line names"*.
  **RIDER — and pin it like this:** (i) an AST/text sweep over every task/finding render function and the
  three tool descriptions: the token `owner` appears ONLY in a claimant context — allowlist the safe: the
  exact set of served strings that may carry it is a constant in the pin (`{"owned by", "held by", "owner="
  param text, …}`), a new occurrence reds; (ii) `render_subject_bound` prose contains no `owner`; (iii)
  mutation: swap the stamped `owner_agent` for a different agent → the bound/created-by line moves and
  `_render_claim_result` does NOT (they read different columns — the two-meanings pin).
- **`_holder_liveness_notice` (63c flag, 64 re-homes it):** the task read at `register` takes the freshly
  minted Subject's `read_filter` (63c §3.5 precedent) — an invisible task ⇒ `None` (silent), never *"unknown
  task"* (an oracle); the holder resolve stays by name (57's link later).
- **Re-open trigger:** packet 57 (`assignee` + the owner↔liveness surface) — at which point the claimant
  string's served word may become "claimant" if 57 introduces a second holder concept; not before.

---

## 4. F3 — RULING: claim is a WRITE; the default-scope question goes to the operator; the CAS rides the substrate authorize-first

### 4.1 Claim = WRITE (binding)
A claim mutates the row (`owner`, `status`, `claimed_at`, `updated_at`) → `Action.WRITE`. Under the 3-way
rule: keep-scoped ⇒ ANY household member (authz §4 *"a Keep task is CLAIMABLE by any household member"*
— the WRITE keep disjunct 61 already emits; nothing new in the PDP); `principal-private`/`agent-private`/
`server` ⇒ the EXACT (principal, agent) creator only (`_member_filter` WRITE, reading 1). Admin ⇒ any row,
audited when a member could not (a claim of another principal's private task IS a load-bearing bypass —
`requires_audit` fires by the existing `authorize` rule; pinned as the admin control).

### 4.2 The default that breaks the fleet → OF-1 (operator)
Under §10-N (`tasks → principal-private`) a task the lead creates is writable by the LEAD'S AGENT ROW only
(exact pair) — a sibling agent of the same principal can READ it (the principal-private READ disjunct) but
cannot CLAIM it. That kills lead-creates/agent-claims, which is the fleet's whole task pattern (57's
"leads assign, agents claim"; every spawn brief names a task id to claim). Three realisations, each with
the wrong world it blesses:
- **(A) default = the PROJECT keep** (`keep:<project>` via `get_or_create_keyed(PROJECT_KEEP_KEY)` — the
  same value memory/findings/briefs default to and the grandfather scope of every legacy row). Fleet
  behaviour byte-unchanged (every fleet agent's principal is the keeper's household). A private task is an
  explicit `scope=principal-private` on create (PDP-validated by `resolve_write_scope`). **RECOMMENDED.**
  Costs: §10-N's letter changes for tasks; a hosted foreign principal in the project household sees the
  backlog (which is what a project collaborator IS).
- **(B) default = the SESSION keep** (`send`'s rule): claimable within the session's household; but tasks
  outlive sessions (the ledger is project-wide, `rollup` spans sessions, packets reference tasks across
  sessions) and a `lore_tasks` call may carry no `session=` — the Subject's agent row has one, but a task
  created "in session S" being invisible to next week's session T (unless T's principal is S's keeper) is
  a served-surface change the fleet must absorb, with the same "explicit `scope=` for the rest" remedy.
- **(C) keep §10-N** and require every lead to pass `scope=keep:<project>` on every `create`/`create_many`
  — a per-call ceremony whose omission silently manufactures un-claimable tasks (the #174 false-unblock
  class: the task looks open, nobody can take it, and the loss render says "unowned but not claimable
  (status open)" — a true sentence that teaches nothing).
**Ruling (mechanism, independent of the operator's default choice):** the default is a PARAMETER of the
substrate (63-rulings §3.3), resolved through `resolve_write_scope(subject, scope, default=<the ruled
default>)` at create/create_many/supersede-successor/report; an explicit `scope=` is PDP-validated (a keep
the caller is not householded in DENIES, teaching `lore-adm add-household`). **Rider:** the default is a
TYPED constant read by the tool description (derived prose) so the served text names the default the code
uses; mutation: change the constant → the description pin AND the create pin move.

### 4.3 The CAS rides the substrate — authorize-first, execute-later, ONE shell (binding)
Post-58 the task side has ONE guarded-append shell (58 item 2: `_transition_fragment`, the supersede stamp,
the re-anchor note and `_claim_fragment` all route through it, mutation-proven); findings already have
`_guarded_append_fragment`. Both shells have EXACTLY `GuardedPlan.fragments`' shape (F-6). Governing them:

1. **`authorize_guarded` is the Python gate for EVERY task/finding write** (claim, transition, supersede,
   acknowledge/resolve/wontfix/annotate, set_scope, the `_many` items per item): one pre-read (the
   `type::record` read it already does) → `Resource` → `authorize` → deny BEFORE any durable effect (#97).
   **Additive extension (the contract author names it):** `authorize_guarded(..., projection=(…))` returns
   the pre-read row WITH the ledger's extra columns (`status`, `owner`, `superseded_by`, `blocked_by`) in
   `plan.pre_read_row`, so the ledger's own `_select_row` pre-read is DELETED (ONE read, no second
   TOCTOU window between two reads of the same row). Default `()` keeps memory/comms byte-identical.
2. **The guard is a WHERE CONJUNCT the ledger's shell takes:** `GuardedPlan.guard() -> tuple[str,
   dict]` (the existing `guard_fragment`/`guard_params` fields, exposed as one accessor) is passed to the
   shell as `guard=`; the shell emits `WHERE (<ledger CAS predicate>) AND (<guard>)` — the ledger's
   predicate parenthesised by the shell (the #417 composition-safety rider, §11), the guard already
   self-contained (#416). The shell's THROW stays the ledger's; a zero-row match rolls the whole txn back
   as today.
3. **Audit rides the SAME transaction:** `GuardedPlan.compose(*caller_fragments) -> list[TxnFragment]`
   returns the caller's fragments + the audit append iff `requires_audit` (the ONE place the audit is
   attached; `guarded_write` becomes `plan.compose(plan.fragments(set_fragment))` — ROUTING-IS-NOT-SHARING
   by construction: the by-id path and the compose-with-caller path share the attach site). The ledger
   calls `self._apply(plan.compose(shell_fragment[, relate_fragment…]))` inside `write_guard("<verb>")`.
4. **A zero-row outcome is CLASSIFIED by the ONE #407 helper** (§11): on the store's rollback the helper
   re-reads the row, first asks `authorize(subject, action, resource_from_row(fresh))` — a DENY means a
   re-scope/re-own landed between the gate and the CAS ⇒ `GovernedConflict` (loud, never a silent no-op
   and never mis-served as a ledger verdict); an ALLOW hands the fresh row to the ledger's own lost-race
   classifier (claim: a `ClaimResult(claimed=False)` decided by owner identity — the contract's RESULT-not-
   exception letter preserved; transition/resolve: `IllegalTransitionError` naming the fresh state).
5. **Never a second guarded path:** the AST reach pin (F5 L1) derives every `task`/`finding` mutation site;
   each must be ∈ (sites whose statement carries `plan.guard()` — observed at L2 by the guard's
   content-addressed param names in the executed statement) ∪ the CREATE-OWNS-IT allowlist ∪ the exempt
   allowlist. A shell that stops taking the guard reds L2 (the executed statement lacks the param names).
**RIDERS — and pin it like this:** (i) mutation — perturb `ScopeEq.to_surql` → claim, transition,
supersede, acknowledge, resolve, wontfix, annotate, set_scope pins ALL red (63-rulings R-a.3 for writes; a
verb that stays green is a private copy); (ii) the TOCTOU leg with the injected handle (63-rulings §10.6
rider iii): a re-scope landing between `authorize_guarded` and the CAS → `GovernedConflict`, row untouched,
for EACH of claim/transition/resolve (three constructions, one helper); (iii) the claim-loss leg: two
household agents race a keep task ≥8-way × 20 runs — exactly one `claimed=True`, every loser a
`ClaimResult` (never `GovernedConflict`), NO audit rows (members, no bypass); (iv) the admin control: an
admin claims another principal's `principal-private` task → allowed, +1 audit row, target names the row;
(v) ONE pre-read: count `_query`/acquire round-trips on a claim — the ledger's separate `_select_row` is
gone (a build that keeps both reads reds on the count).
**Required-green builds (am-14):** a claim on an unblocked keep task by a non-creator household member; by
the creator; by admin on a private row (audited); a claim that loses to a superseded blocker (R10(iii)
render unchanged); a claim on a legacy NONE-scope row by a member ⇒ `GovernedDenied` at the Python gate
(member-invisible), by admin ⇒ allowed (AllRows) + audited — the 63-rulings §10.1 rider (ii) dirty-row leg.
**Cost stated:** one extra Python gate per write (no extra round-trip after the projection merge); the
shell gains one conjunct. Re-open trigger: a measured p50 regression on `claim` attributable to the gate.

---

## 5. F4 — RULING: supersede/resolve/annotate/wontfix under Keep scope; the successor's scope; the re-anchor as a system effect

| verb | action on the EXISTING row | the NEW row | who may (member) |
|---|---|---|---|
| `lore_tasks supersede` | WRITE on the predecessor (the `superseded_by` stamp — guarded per §4.3) | CREATE owned by the superseder; `scope = resolve_write_scope(subject, scope, default=<task default>)` | household of a keep task; the exact creator pair of a private one |
| `lore_findings report(supersedes=X)` | NONE — X is not mutated (the link lives on the successor) | CREATE owned by the reporter; `scope = resolve_write_scope(subject, scope, default=<project keep>)` | anyone who can READ X: `supersedes` is resolved THROUGH `read_filter(subject, FINDING_TABLE)`; an invisible X ⇒ `FindingNotFoundError` byte-identical to a nonexistent one (ii-b §9.5 α's twin) |
| `acknowledge` / `resolve` / `wontfix` | WRITE (status edge via the guarded shell) | — | household of a keep finding (authz §4 *"any household member may resolve/supersede a Keep finding"*); the exact pair of a private one |
| `annotate` | WRITE (a status-preserving event append) | — | same as above — an annotate is a correction, the collaborative act the keep exists for |
| `resolve_many` / `acknowledge_many` | WRITE per ITEM, best-effort preserved: each item runs its own `authorize_guarded` + shell; a DENIED item renders as that item's failure (`GovernedDenied` text) and never vetoes the rest | — | per item |
| `set_scope` (NEW, both tools) | SET_SCOPE — the exact creator pair ∧ `_grantable(target)`; admin any (audited) | — | owner only (authz §4.3: *"a member may NOT change the scope of a row it doesn't own"*) |
| hard delete | NO served verb (both ledgers "never delete"); the substrate DELETE branch = #429's positive-control pin + F8's orphaning path | — | — |

- **Why `wontfix` is a WRITE, not a soft-DELETE:** the 3-way rule's delete clause guards VANISHING
  (*"members correct and supersede, they do not vanish each other's work"*); a `wontfix` row stays readable,
  its number stays, its history stays, `chain_head` still walks through it. Nothing vanishes. A household
  member closing a finding it did not report is the collaborative act §4 names.
- **Why the successor's scope is NOT inherited:** inheritance would need X's scope to be grantable by the
  superseder — true for a keep they are householded in, FALSE for `server` (a member may not mint server…
  61 D4(b) says server IS grantable) and false for X's `principal-private` if X belongs to another principal
  (unreachable — they could not read X). One rule beats a branch per case: the successor is a NEW row and
  its author states its scope (default or explicit); the render of a supersede names the successor's scope
  in the bound line so a scope crossing is SEEN, never silent (Leg 1).
- **58's re-anchor of dependents (58 F-3, live because 58 lands first):** for each dependent Y of X the
  supersede rewrites `Y.blocked_by` X→X', re-mirrors the edge, appends a provenance note. Under 64 that is
  a mutation of rows the superseder may not have WRITE on. Two honest shapes: (a) refuse when any Y is
  unwritable — but a refusal reveals that invisible dependents EXIST (an oracle, even without a count);
  (b) treat the re-anchor as a SYSTEM effect of a write the superseder DID prove (on X). **Ruling: (b).** The
  re-anchor statements run under `governed_exempt("supersede-reanchor", statement=…)` — an allowlist entry
  with EVIDENCE: the statement's WHERE is `blocked_by CONTAINS $old` (only rows pointing at the row the
  superseder just proved WRITE on), its SET touches ONLY `blocked_by` + `provenance.events` (+ the edge
  DELETE/RELATE), never a governed column or a status — statement-shape-pinned (drop the WHERE → RED; add a
  column → RED). The render counts dependents re-anchored over the VISIBLE set only (`direct_dependents`
  spliced with the read filter for the RENDER; the WRITE runs over all) and its bound line says so.
  **Pin:** seed Y in a keep the superseder is not householded in → the supersede SUCCEEDS, Y is re-anchored,
  the render's count excludes Y, the served bytes are IDENTICAL to a run without Y (no oracle — byte-diff).
- **Re-open triggers:** *"the first request for a finding's supersede to CLOSE its predecessor"* (would make
  finding supersede a WRITE on X); *"a re-anchor observed on a row whose owner objects"* (→ (a) with a
  designed non-oracle refusal).

---

## 6. F5 — RULING: the identity args become derived-or-checked; the served break is 65's `capability=` only

- **Question.** `created_by`/`actor`/`owner` are REQUIRED today on several verbs. Retire, accept-and-ignore,
  or keep as a non-identity label?
- **Answer — the ONE shape 63c Q4a already ruled for `agent=`, extended by its call set (never cloned):**
  1. Identity comes from `capability=` → `Subject` via the ONE composition root (`AppContext._resolve_
     subject`), and the caller's own agent ROW via the 63c dispatcher helper (Q4a steps 2–4: resolve
     Subject → read own row BY ID → `agent=`/`session=` self-consistency check, one site). **64's three
     dispatchers CALL that helper** (name it `AppContext._resolve_identity(capability, *, agent, session)
     -> tuple[Subject, Agent]` if 63c inlined it in `comms` — the integration patch LIFTS it; a second copy
     in `tasks()` is #102).
  2. `created_by`/`actor`/`owner` become OPTIONAL (`str | None = None`). Supplied ⇒ must equal
     `own_row.name` (the identity the capability proved) else ONE teaching `GovernedDenied` (*"created_by=
     must name the agent your capability proves — it is derived, not declared"*); omitted ⇒ derived. The
     check EXTENDS the Q4a helper's compared set (`agent`, `session`, and now the verb's identity arg).
  3. The columns/blob strings are POPULATED from `own_row.name` (`provenance.created_by`,
     `finding.created_by`, `events[].actor`) — display provenance survives in the shape every consumer
     reads today; `events[]` ADDITIONALLY carries `actor_agent: <agent RecordID as str>` (the provenance
     blob is FLEXIBLE; a name is ambiguous across sessions, the id is not).
  4. `lore_claim_task(task_id, owner=None, *, capability, agent, session)`: `owner` optional, same check;
     the claimant string = `own_row.name`.
  5. `rollup`: `capability=` REQUIRED (its task/finding legs are governed reads; an identity-less rollup has
     nothing governed to serve — a teaching deny, never a partial render). The `since`/`limit` shape is
     unchanged.
- **Why not RETIRE (foreign-param refusal) in 64:** every fleet brief passes `created_by=`/`actor=` today;
  65 already forces one break (`capability=`). A second break in the same cutover doubles the re-brief
  surface for zero security gain — the value is CHECKED, so it carries no authority. **Why not IGNORE:** a
  value accepted and dropped is the silent lie authz §3.2.2 forbids and the trust doctrine's false clear.
- **The R8(2) footer fallback dies for governed calls:** `_with_comms_footer(attributions=…)` matched a
  free-text value to a registered name "never authenticated". Every task/finding/claim call now has a
  Subject, so the footer takes the Subject's own agent (the same row the comms footer uses) and the
  `attributions=` fallback is DELETED for these three tools (inventory §14: dropped-deliberately; its
  third-person "matched, never authenticated" served line and the `agent=` description's *"one disclosed
  exception"* sentence are STALE PROSE to correct with the flip — the P8d sweep).
- **OF-2 (operator, §15):** confirm the served-break shape at 65 = `capability=` required only (this
  ruling), vs. also retiring the three args to foreign-param refusals (a cleaner surface, a second break).
  My recommendation: this ruling; re-open trigger for retirement = *"the first hosted (non-fleet) consumer
  of `lore_tasks`/`lore_findings`"*, when a name-carrying arg is noise to a reader who never chose a name.
- **RIDERS — and pin it like this (F4's fuzz, parametrised ∀ write verbs of both tools + claim, derived from
  the spec tables):** (i) hostile `owner_principal=`/`owner_agent=`/`as_agent=`/`scope=server`(member: allowed
  by `_grantable` — pin it lands as `server`, not refused)/`scope=<keep not householded>` (DENY) → the stamp
  equals the Subject's pair whatever the call carried; (ii) `created_by="someone-else"` ⇒ `GovernedDenied`,
  ZERO rows written (the F5 observer counts 0 mutations); `created_by=<own name>` ⇒ accepted; omitted ⇒
  accepted, `provenance.created_by == own name`; (iii) the sweep: a bare `awk` for `never authenticated` /
  `disclosed exception` / `exact-match` over `server.py` + the three descriptions → every hit a file +
  verdict; (iv) `_resolve_identity` is ONE site: AST — exactly one production comparison of a supplied
  identity arg against `own_row.name` across `tasks`/`findings`/`claim_task`/`comms` (63c R-467-3 extended).

---

## 7. F6 — RULING: `blocks` is governed by derivation; cross-scope dependencies are refused where they would leak and system-read where they cannot

- **Population:** `blocks` (`task→blocks→task`, ENFORCED, no fields) joins `governed_populations()` the
  moment `_task_statements` appends the trio (`TASK_TABLE` is a module literal — no ImportFrom leg
  needed). Per am-2 A1: NO edge columns; its reads ride the task filter; its writes are attributed
  (`write_guard("task_create")`/`("task_supersede")` labels) and F5-observed as a population. The exact-set
  known set grows by `{task, finding, blocks}` at 64 (§13).
- **May a task be `blocked_by` a task its creator cannot READ?** At create/supersede: NO — the blocker
  existence check (`_reject_unusable_blockers` → the shared `reject_unknown_rows`) takes the creator's
  `read_filter(subject, TASK_TABLE)` spliced into its existence SELECT, so an invisible blocker is refused
  with the SAME `UnknownBlockerError` text as a phantom (byte-identical — no existence oracle). `blocks`
  ENFORCED still guards the table for any writer that skips the check. Later re-scoping CAN make an
  existing dependency's blocker invisible to Y's creator; that is not refused (a scope change on X is X's
  owner's right) and it is not a leak (below).
- **The claim gate and the query partition are SYSTEM reads, not served reads:** the CAS's `LET
  $clm_resolved` and `query_tasks`' server-side status read over the candidates' `blocked_by` ids resolve
  blocker STATUS inside the transaction/snapshot regardless of visibility; the caller learns only the
  OUTCOME (claimed / not claimable / blocked partition). A visible-only resolve would make an invisible
  blocker count as UNRESOLVED forever (fail-closed) — correct for safety, WRONG for the fleet (a task
  blocked by a private-but-done task could never be claimed by anyone but its blocker's owner). Ruled:
  system read, unfiltered, stated in both docstrings; the served render never carries the blocker's status.
- **`blockers` (transitive walk), `get`, `query`:** ids render BARE (an id already sits in a readable
  row's `blocked_by` column — no new fact); any DECORATION (subject/status of a blocker) is served only
  for visible rows. At HEAD `_render_transitive_blockers` decorates nothing per blocker (it reads the
  TARGET only) — nothing to withhold today; the rule binds any future decoration. The `blocked_by …
  unresolved` loss render lists ids (already readable) — unchanged.
- **RIDERS — and pin it like this:** (i) create with `blocked_by=[<invisible X>]` vs `[<phantom>]` → both
  `UnknownBlockerError`, deny texts byte-identical, zero rows, zero edges; (ii) a keep task Y blocked by a
  `principal-private` X of another principal (seeded through the ledger, not the tool — the only door):
  when X reaches `done`, Y is claimable by Y's household (the system read resolved it); (iii) the `blocks`
  row in the exact-set pin + an F5 case (`seed_blocks_*` beside `to`'s) with its two writer labels and
  the evidence line *"an edge is minted only inside a task CREATE/supersede/re-anchor the caller proved"*.
- **Re-open trigger:** *"the first render that decorates a blocker id with its status/subject"* → the
  visible-only decoration rule above applies and the bound line names it.

---

## 8. F7 — RULING: one typed spec base; the tuples become spec dicts; every 64 leg flips WITH its wave

- **Ruling:** promote the flags of `CommsActionSpec` into a base `GovernedVerbSpec(requires_capability:
  bool = False, limit_cap: int | None = None)`; `CommsActionSpec(GovernedVerbSpec)` adds `handler`/`params`/
  `required`/`requires_registration` (byte-identical behaviour for comms). `_TASK_ACTIONS: dict[str,
  GovernedVerbSpec]` and `_FINDING_ACTIONS: dict[str, GovernedVerbSpec]` replace the tuples — iteration,
  `list(_TASK_ACTIONS)` in the unknown-action teaching, `action in _TASK_ACTIONS`, `tuple(table)` in the
  routing derivation all keep working (dict → keys). The `if action == …` chains STAY in the methods (the
  vocab AST pin scans them; `tasks()`'s docstring constraint unchanged). ONE helper reads the flag for all
  three dispatchers: `_requires_capability(table, action) -> bool` — typed applicability, never a name
  compared (PKT-28).
- **Why not a derived sibling set:** a `frozenset` beside each tuple is the same per-verb hand assignment
  the spec already is, in a SECOND shape — the #102 seam (a fix reaches the comms field and not the set).
  Why not a full `CommsActionSpec` table with handlers for tasks: it would move the branch chain out of
  the method the AST vocabulary pin scans (the documented blinding of `TestTheServedActionVocabulariesAre
  PinnedByEQUALITY`) for no governance gain.
- **The flips (ii-a §4 — WITH the enforcing handler, never ahead):** 64b flips the 10 finding verbs; 64a
  flips the 8 task verbs (+ `lore_claim_task`'s single-verb `capability=`); each `True` lands with the
  handler that resolves the Subject unconditionally. `_GOVERNED_VERBS_ROUTED` gains each leg WITH an
  `@observes_routing` marker on its F3/F4 behavioural pin; `_GOVERNED_VERBS_PENDING_ROUTING` loses it.
  `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` loses `lore_findings` at 64b close, `lore_tasks` + `lore_claim_task`
  at 64a close (R-a.5).
- **The P5 render-coverage derivation (ii-b §9.2/§14.2; 63c re-keyed it to the typed signal):** the same
  typed signal now covers tasks/findings — every handler branch of a `requires_capability=True` verb is a
  Subject-resolving render → its render is in the demanded set for `render_subject_bound`. No third signal.
- **RIDERS — and pin it like this:** (i) the ii-a R6 driver table gains 19 rows (derived from the two spec
  dicts + the single-verb tool): ∀ `True` verb, a call with NO capability ⇒ `GovernedDenied`; coverage
  `required − drivers.keys() == ∅`; (ii) the REVERSE #420 direction (finding #487's fix): a verb whose spec
  says `requires_capability=True` OR that carries an `@observes_routing` marker MUST be in
  `_GOVERNED_VERBS_ROUTED` — a pending entry with a fired trigger reds by name; (iii) mutation: flip one
  verb's flag to `False` → its R6 row, its render-coverage membership AND the reverse pin move together
  (one field, three consumers — sharing by mutation).

---

## 9. F8 — RULING: §10.7-Z orphaning LANDS in 64 (wave 64d); #404 closes with it

- **Question.** Does the principal-delete ORPHAN-TO-NONE mechanism (63-rulings §10.7-Z, SF-63-5
  operator-CONFIRMED) land in 64, and does it discharge #404?
- **Answer — YES, as a small dedicated wave after 64a/64b (64d), and #404 closes.** 64 is the packet §10.7-Z
  NAMED (*"the orphaning mechanism is 64's admin `set_owner`"*) and the SET_OWNER substrate branch must be
  exercised by 64 anyway (#429). Deferring past 64 leaves refuse-while-owning as the HOSTED-era behaviour
  (65 provisions principals; a principal with one saved note becomes undeletable) with no packet named —
  a deferral with no decision point (the can-kick law). The trigger has not fired in production; that is
  why it is a wave, not a blocker.
- **Mechanism (a HOW within §10.7-Z's letter, one deviation named):** inside `PrincipalStore.delete`'s ONE
  transaction, for each table in the DERIVED governed set: `UPDATE <t> SET owner_principal = NONE,
  owner_agent = NONE WHERE owner_principal = type::record('principal', $pid)` (an IndexScan on each
  `<t>_owner_principal` index — free) + ONE audit row per table (`action=SET_OWNER`, `target_table=<t>`,
  `target_row=<t>:*`, `old_value={"owner_principal": $pid, "count": N, "row_ids": <first K>}`,
  `new_value={"owner_principal": None}`) via `AuditStore.append_fragment` composed into the same
  `execute_transaction`. **Deviation from §10.7-Z's "each an audited bypass":** per-ROW audit rows would
  be N `authorize_guarded` pre-reads (N round-trips before the txn) and N audit CREATEs inside it (the
  `TXN_STATEMENT_HARD_CAP = 5000` bound — 58's hub shape); ONE audit row per table carrying count + a
  bounded id sample records *who orphaned what* (the trail's purpose) with its bound NAMED in the row (K of
  N — Leg 1). The statement is not member-reachable, so it attributes at the F5 seam via
  `governed_exempt("principal-delete-orphan", statement=…)` with evidence: *the WHERE names the very
  principal being deleted; the SET touches only the two owner columns; runs only inside the delete txn* —
  statement-shape-pinned.
- **The derived governed table SET, in PRODUCTION:** promote the test substrate's pure text derivation
  (`governed_node_tables(emitted_ddl)` over `generate_ddl()`'s text — F-12's `_enforced_relations_scaffold
  .emitted_schema_ddl` idiom) to `surreal_schema.governed_node_tables(ddl: str) -> frozenset[str]`; the
  test substrate IMPORTS it (ONE derivation; its growth pins keep it honest). `delete` iterates that set —
  a seventh governed table joins the orphaning by the same derivation that registers it everywhere else
  (the registration-site lesson).
- **#404 closes:** the keep-table coupling (and now six more) is guarded by `_table_exists(<t>)` per read
  — the memory read's existing idiom, fail-CLOSED on a fault — so the store method owns its own readiness
  and NO caller must ready a slice first. Pin: `delete` of a keeps-nothing, owns-nothing principal on a
  PRINCIPAL-ONLY store (no keep/memory/task/finding tables) succeeds; on a store with an owned row in EACH
  governed table → every row orphaned, one audit row per table, the principal gone, keys cascaded — in
  ONE txn (an injected failure at table k ⇒ nothing changed). The `PrincipalOwnsGovernedRowsError` pin-the-
  miss is DELETED with the mechanism (its own instruction); the exact-set link class flips from
  `ORPHAN-AUDITED (refuse meanwhile)` to `ORPHAN-AUDITED`.
- **Two collisions, named:** (1) **finding #488** — am-25's message half (ii) ("scoped-but-ownerless = half-
  applied → refuse") and am-22 §3's agent half-pair both refuse the state orphaning PRODUCES; 64d's contract
  carries a pin that `migrate_governed` re-runs on a table holding an orphaned row are NOT refused — which
  forces 63c's document to retire half (ii) for message/agent (or key it on the audit trail) before 64d
  lands. Not mine to rule; surfaced. (2) `agent` orphaning: an agent row's `owner_agent` is ITSELF (63c
  Q1); clearing both columns on a live agent breaks `verify_capability`'s binding (fail-closed deny under
  every principal — 62 W2) — which is CORRECT (a deleted principal's agents may not act) and is pinned as
  the positive control (an orphaned agent's capability denies).
- **OF-3 (operator, §15):** a wave added to 64's plan (≈0.10; principals.py + audit + the derivation
  promotion). Alternative: defer with the named trigger *"the first principal-delete against an owning
  store"* and keep refuse-while-owning — honest but it is the hosted era's first support ticket.

---

## 10. F9 — RULING: the finding ledger's oracles — walk through the filter; accept the `number` bound, pinned, and ask the operator to carry it into a hosted 65

- **`chain_head`:** `_select_successors` takes the caller's `read_filter` (the same splice ∀ finding list
  reads); the walk therefore stops at the last VISIBLE successor and serves it as the head OF THE VISIBLE
  CHAIN. The render's bound line (`render_subject_bound`, first) states the set; the `forked`/
  `fork_successor_numbers` legs are computed over the visible successors only. NO *"N successors withheld"*
  line (an existence leak — 63-rulings §4.3's rule); withheld successors are logged server-side at
  WARNING with the count. Trust Leg 1: the consumer who acts on this head without checking cannot be wrong
  in a way the response did not name — the response named its set.
- **`get`/`chain_head`/`query` on an invisible finding:** `_resolve_row` takes the filter → an invisible
  number/id raises the SAME `FindingNotFoundError` text as a nonexistent one (byte-identical). `query`'s
  `ORDER BY number LIMIT n` runs over the filtered set; `filed_since` (rollup) gains `subject=` and splices
  the filter into BOTH the rows SELECT and the `count()` (the `message_activity_since` shape, cited).
- **The global monotonic `number` — ACCEPTED BOUND, PINNED:** a member sees `#N` on its own report and can
  infer that ~N findings exist and, across two reports, how many others filed between (a COUNT of others'
  activity, never content, never an id, never a scope). Alternatives, each rejected: per-keep numbering
  (breaks the global handle every report, INDEX row, memory note and finding body in this repo cites —
  `#404`, `#487`; a served-surface break of the first order); opaque-only addressing (the same break plus
  the #89 class — agents were reading raw rows to resolve ids before `get` existed); a per-principal number
  offset (a fabricated sequence). The bound is stated in the `lore_findings` description (one sentence:
  *"numbers are a global sequence; a gap means findings you cannot see exist"*) — a fact, not a
  disclaimer. Pin: two principals report alternately → each sees consecutive numbers with gaps; the gap is
  the only leak (a `query` by the second principal never returns the first's rows; `get` on the gap number
  is byte-identical to a nonexistent number).
- **OF-4 (operator, §15):** 65 IS the hosted-write enablement; carrying this bound into a hosted deployment
  is the operator's call. Re-open trigger: *"a hosted deployment with a second principal whose finding
  activity must be unobservable to the first"* → per-keep numbering + a served-handle migration (a packet,
  not a fix).

---

## 11. The #417 fork and the owned findings — adjudicated

| # | ruling | wave |
|---|---|---|
| **#417** | 64 composes NO new multi-disjunct IR node: the write guard enters the ledgers' shells as caller SurrealQL (`WHERE (<cas>) AND (<guard>)`), not as an IR node under `And`. The pinned bound STANDS (reach STOP-rule). 64 adds the composition-safety pin for the CONJUNCT: the shell parenthesises the ledger predicate itself, and a hostile predicate carrying a top-level `OR` (`status='open' OR true`) cannot escape the guard — the emitted WHERE has the guard AND-bound at the top level (a text pin over the emitted statement + a live leg: the hostile predicate matches ZERO rows the guard excludes). Re-open: *"the first IR node 64+ adds"* — the closed-algebra gate reds it anyway. | 64b |
| **#418** | IN, minimal: `And(())` → the AND identity (`"true"`, `matches` True), `Or(())` → the OR identity (`"false"`, `matches` False) — the identity-element guard; pins: `to_surql` ≡ `matches` on the empty case for both, and `And((X,))`/`Or((X,))` unchanged. A named `lorerunes` touch in 64b's builder writable set (the §10.1 precedent). | 64b |
| **#411** | IN (cheap): a spy pin — monkeypatch `AuditStore.append_fragment`, call `append()`, assert it was consumed (effect, not text). 64 is the first trail-load-bearing consumer (the per-table orphan audit row + the admin-claim audit). | 64b |
| **#414 / #415** | IN — the ONE row→`Resource` constructor `governed.resource_from_row(row) -> Resource` derives `table` from `row["id"]` (`RecordID.table_name`), never a caller field; `authorize_guarded` uses it and ASSERTS the pre-read row's id table == its `table` argument (mismatch ⇒ `GovernedDenied` naming both — an internal-invariant teaching, never a silent trust); the #407 helper's fresh-row re-validate uses the same constructor. Pins: a row whose id is `audit:x` handed with `table="finding"` is refused; the R-a.2-style AST pin: `Resource(` in production ONLY inside `resource_from_row` (allowlist the one site). | 64b (substrate touch → held patch, §13) |
| **#407** | IN — ONE helper `governed.classify_zero_row_cas(store, *, table, row_id, subject, action, ledger_verdict)` (name = the author's): re-read the fresh row → `authorize(subject, action, resource_from_row(fresh))` DENY ⇒ `GovernedConflict`; vanished ⇒ the ledger's not-found; else `ledger_verdict(fresh)` (the ledger's own state-named lost-race error / result). The four F-8 sites route through it (findings in 64b, tasks in 64a — the mutation proof of sharing lands at 64a: perturb the helper's DENY branch → transition/supersede/claim/resolve/annotate pins ALL red). Must NOT route through `wrap_store_rejection` (it deletes the re-read — #407's own warning). | 64b builds; 64a proves sharing |
| **#406 / #408** | IN for the paths 64 opens — the affected sets DERIVED by AST property over `tasks.py`/`findings.py` (an async store method calling `_query` without `wrap_store_rejection`; a sole-body `except SurrealStoreError: raise <Domain>` with no passthrough-first clause). Ruling for #408: PASSTHROUGH-FIRST ∀ derived sites (transport propagates; a domain rejection is classified) — `transitive_blockers`' *"never a partial answer"* virtue is PRESERVED for the store-rejection case (still classified, still no partial render) and its transport case now renders `connection down` like every sibling (the `server.py` handler already exists). #406: each derived unwrapped path with a REACHABLE domain rejection is wrapped; the rest are listed with their verdict (no blind wrap-everything). | 64a (tasks) · 64b (findings); ONE derivation function in the substrate |
| **#419 / #420** | IN — 19 legs go GREEN per verb WITH markers (§8); the REVERSE pin (#487) lands with 64b. | per wave |
| **#427** | IN — `_dispatch_verbs` derives the table from the TOOL: the mapping the tool's handler subscripts/iterates with `action` (AST over the registered `tool.fn`'s body: the `Name` indexed by `action` or iterated in the unknown-action teaching), falling back to `(tool, tool)`; NO hand map. Pin: a synthetic governed multi-verb tool whose handler indexes a fresh `_X_ACTIONS` dict is discovered with no test edit; a handler with no such mapping still derives exactly one verb. | 64b (held patch — `test_governed_routing_63a.py`) |
| **#428** | IN — the meta-pin confirms each `@observes_routing(tool, verb)` test's BODY drives THAT tool/verb (AST: a call carrying `action=<verb>` literal for a multi-verb tool, or a call to the single-verb tool's method); a marker on a test that drives nothing reds by name. | 64b (held patch) |
| **#429** | IN — DELETE and SET_SCOPE branches exercised with positive controls: SET_SCOPE via the served `set_scope` verbs (owner ⇒ moved, +0 audit; non-owner member ⇒ deny; admin ⇒ moved +1 audit; non-grantable target ⇒ deny); DELETE via the substrate leg on a `finding` fixture row (owner ⇒ 1 row, RETURN BEFORE; a household non-owner ⇒ deny — the D4(a) scope-independence control: an owner deletes its keep row after leaving the keep) and via 64d's orphaning. | 64b · 64d |
| **#404** | closes in 64d (§9). | 64d |

---

## 12. (a) The 64b-first contract worklist — per ruling: pins, the wrong builds each kills, the discriminating fixtures

**The fixture floor for EVERY table below (F3 world):** ≥2 principals (`alice`, `bob`) × ≥2 agents each,
keeps with DISJOINT households (`keep:A` alice-only, `keep:B` bob-only, `keep:AB` both), the canonical
project keep, an ADMIN control subject (`AllRows`), one LEGACY NONE-scope row seeded under the OLD DDL,
and — where a value can branch — ≥2 values per parameter (no monoculture: two keeps, two statuses, two
sessions). Parametrise by table via the existing `GovernedTableCase` + a NEW `finding_case()`
(`_governed_contract_64.py`, §13); never a copied module.

| ruling | pins ("pin it like this") | wrong build it kills | fixture that discriminates |
|---|---|---|---|
| F1 migrate `[finding]` | F1-a: OLD DDL → seed 3 legacy (NONE/NONE/NONE) + 1 governed → NEW DDL (`ensure_ready`) → seeds survive + an unrelated-column UPDATE succeeds (§1.4 poison check); F1-b: BEFORE the verb — member `query` serves 0 of the 3, admin serves 3 (fail-closed leg); F1-c: `migrate_governed(table="finding")` → `backfilled == 3`, owner NONE/NONE, `scope == keep:<project>`, `created_by` bytes intact, governed row byte-identical; second run `backfilled == 0`; F1-d: the owned-but-unscoped trap row → refused, byte-inert, ONE refusal naming count + ids; F1-e: a scoped-but-ownerless row → NOT refused (this disposition's migrated state); F1-f: `migrate_governed(table="finding")` with unmigrated agents SUCCEEDS; F1-g: `report_unmigrated_governed_rows(store,"finding")` == 3 before, 0 after; F1-h: the ∀-tables WHERE golden gains `[finding]` | a leg that stamps an owner from `created_by`; a WHERE without the self-guard; a leg that refuses the healthy post-migrate state; an order precondition that guards nothing | legacy rows whose `created_by` EXACTLY equals a registered agent's name (the guess-mapping door) → still NONE/NONE after migrate |
| DD-3.c `[finding]` | P2 `[finding]` row: birth = the git-derived field set (the author DERIVES it from `git log -S _FINDING_FIELD_SPECS`; candidate: all eleven), `birth_defaults = {status, created_at}`, `exemptions = {status}`, floor ⊇ `{number, status, created_by, owner_principal, scope}`, `hazard` slot naming the finding migrate; P-F2: the ASSERT literal set == `FINDING_STATUSES` == `get_args(FindingStatus)`; Leg A: five shapes (blank `kind`/`subject`/`area`/`category`/`created_by`) REJECTED under the frozen `ae54f20` DDL, ACCEPTED via the raw seeder after the current emitter, `status='urgent'` STILL rejected; Leg B: the real migrate over the five violators + one clean → all stamped, second run 0; P-F3 (KNOWN BOUND): a junk-status legacy row refuses the whole backfill, message carries the §13.2 three-step heal; MOVE pins: `report` refuses blank `kind`/`subject`/`created_by` via `lorerunes.is_blank` (teaching, BEFORE any store I/O — F5 observes 0 writes), parametrised over the shared `_HOSTILE_IDENTIFIERS`-style blank corpus | a bare DROP (widens the writer); a KEEP that denies the cutover on a blank legacy `kind`; a status ASSERT that drifts from the `Literal` | the raw seeder bypasses the writer (that IS the hypothesis under test); the `created_by` violator is the one F5 makes impossible via the tool — seed it raw |
| F2 (finding has no claimant) | the served-word pin over finding renders: no `owner` token; `render_subject_bound` FIRST on `query`/`get`/`chain_head`/rollup's finding leg; `created by <name> (principal <email>) · scope <s>` derived from the row's typed columns | a render that prints `owner_agent` under "owner"; a bound line hand-written per render | a row created by alice's agent, read by bob (household) — the created-by line names alice's agent, the bound line names bob's principal |
| F3/F4 writes | R6 rows for all 10 verbs (no capability ⇒ deny); F4 fuzz ∀ 7 write verbs (report, acknowledge, resolve, wontfix, annotate, resolve_many, acknowledge_many) + `set_scope`; keep semantics: bob's agent resolves alice's `keep:AB` finding (allowed, 0 audit), bob CANNOT resolve alice's `keep:A` or `principal-private` finding (deny), admin can (allowed, +1 audit); `annotate` by a household non-reporter allowed; `wontfix` by household allowed and the row still readable + `chain_head` still walks it; `report(supersedes=X)` with X invisible ⇒ `FindingNotFoundError` byte-identical to a nonexistent number; successor scope = default (project) unless explicit; explicit `scope=keep:B` by alice ⇒ deny (not householded); `resolve_many` with one denied item → that item's failure rendered, the others resolved (best-effort preserved); the TOCTOU leg (injected handle) for resolve; the #407 helper: a same-target race renders `IllegalTransitionError` naming the fresh state, a re-scope race renders `GovernedConflict` | a resolve that checks only READ; a supersede that inherits X's scope; a batch where one deny vetoes all; a lost race served as success; a re-scope conflict served as "already resolved" | the disjoint-household triple `keep:A`/`keep:B`/`keep:AB`; two racers with DIFFERENT principals on one keep row |
| F5 identity | `created_by=`/`actor=` optional; supplied-mismatch ⇒ deny, 0 writes; omitted ⇒ derived; `provenance.created_by == own_row.name` and `events[].actor_agent == <agent id>`; the footer's R8(2) fallback gone (a bare `awk` for `never authenticated` over `server.py` + descriptions → 0 hits in the governed three); ONE identity-compare site (AST) | a dispatcher that trusts `created_by=`; one that ignores it; a second copy of the compare | `created_by=<bob's name>` from alice's capability; `created_by=<alice's own name>`; omitted |
| F7 flips | `_FINDING_ACTIONS` is `dict[str, GovernedVerbSpec]`, all 10 `requires_capability=True`; the R6 driver coverage `required − drivers == ∅`; the REVERSE #420 pin (`True`/marked ⇒ routed); the render-coverage derivation demands the 10 finding renders (non-vacuity ⊇ them); mutation: flip one to `False` → three consumers move | a flag with no enforcing handler; a routed leg with no marker; a marker on a test that drives nothing (#428) | the synthetic-verb discriminator + a synthetic multi-verb tool (#427) |
| F9 reads | F3 isolation ∀ 3 read verbs + rollup's finding leg: bob's agents never receive alice's `keep:A`/private rows via `query` (each filter combination: status/kind/area/limit), `get`, `chain_head`, rollup (rows AND `total`); served COUNT == served set (`filed_since.total` filtered; `query`'s cap disclosure over the visible set); `chain_head` over a chain whose middle node is invisible to bob → bob's head is the last visible node, bound line present, NO withheld count in the bytes; `get` on an invisible number ≡ nonexistent (byte-diff); the `number` bound: alternating reports by alice/bob → gaps; the description sentence present (promise-registry) | a count over the unfiltered table; a walk that follows invisible successors; a "withheld N" line; an invisible-number error that differs from a nonexistent one | a 4-node chain alternating owners across `keep:A`/`keep:B` |
| substrate touches (#414/#415, #418, #411, #407 helper, `GuardedPlan.guard/compose`, `authorize_guarded(projection=)`) | as §11 + §4.3 riders; each with its mutation proof declared from `--collect-only` and diffed both ways (`scripts/mutation_proof.py`) | — | — |
| F5 enforcement `[finding]` | the F5 case: seeders (`seed_finding_legacy`/`seed_finding_governed`), write verbs + `write_guard` labels (`finding_report`, `finding_acknowledge`, …, `finding_set_scope`), the CREATE-OWNS-IT allowlist triple for `report` (evidence: *the owner pair is server-derived from the Subject and the id is a fresh uuid4 — no argument names a foreign row*), the migrate exempt token with its golden; L1↔L2 both-ways over `findings.py` | an unclassified write site; a label that lies | the F5 observer under every driven verb |
| F1 S2 (integration) | the real dump restored into a `:18000` throwaway → pre/post migrate `query` id-set byte-diff for the keeper's agent (63-rulings §2.2's pin) | — | the fleet's own rows |
| 64c target (report-only, at 64 close — the 63b-iii shape) | over the WIRE on the real tables: F3 ∀ read verbs of both tools; count == set; anti-injection ∀ write verbs; keep semantics (non-household DENY / household succeeds / admin audited); the migration cannot widen visibility (the half-pair precondition attacked: seed one owned-but-unscoped row → the verb refuses ALL 64 tables, writes nothing); no TOCTOU on the shells (injected handle); F6/F9 oracles byte-diffed; the Leg-2 forgery table (dependencies × {stale, empty, wrong-instance, partial}) CONSTRUCTED per table | — | the archived `secaudit_63b_iii_probe2.py` harness, re-aimed |

**Split trigger for 64b (the 63 §1.4 idiom):** if the contract prices > 0.30, split at the ONLY sound
seam — **64b-i = the substrate touches + the WRITE side + migrate** (`report`/the five status verbs/the
batches/`set_scope`, F5 case, DD-3.c legs) · **64b-ii = the READ side** (`query`/`get`/`chain_head`/rollup's
finding leg/counts/F9) — never mechanism without its isolation pins.

---

## 13. (b) The contract-ahead boundary — what lands as NEW files now, what waits in the held integration patch

**Shared (63c-edited) files — NOT touched by any 64 contract file:** `loremaster/tests/_governed_contract.py`,
`loremaster/loremaster/server.py`, `loremaster/loremaster/governed.py` (the 63c fix wave touches it —
treat as shared), `loremaster/tests/test_message_enforcement_63b_ii_a.py` (the ONE exact-set known-set pin),
`loremaster/tests/test_comms_schema.py` (the P2 parametrised constraint pin 63c is extending with
`[agent]`/`[brief]`), `loremaster/tests/test_governed_routing_63a.py` (`_dispatch_verbs`, the meta-pin),
`loremaster/tests/test_principal_keys_schema.py` (the `record<principal>` exact-set pin), `principals.py`
(63c-i-a's migrate legs).

| lands NOW as NEW files (64b contract) | goes in the HELD integration patch (applied on the final 63c base) |
|---|---|
| `loremaster/tests/_governed_contract_64.py` — the 64 substrate additions: `finding_case()` / `task_case()` (`GovernedTableCase` rows), `seed_finding_legacy` / `seed_finding_governed` / `seed_task_*` / `seed_blocks_*`, `frozen_asserted_finding_ddl()` / `unbounded_finding_ddl()` (+ task twins), the AST property derivations for #406/#408, a `finding`-parametrised F5 registry — importing ONLY names that EXIST at `ae54f20` (`credentialed_app_context`, `register_owned`, `store_handle`, `observe_governed_table_writes`, `governed_populations`, `member`/`admin`/`access_token`, `governed_overlay_ddl`, `python_allowed_ids`, `classify_tree_observed_write`, …) | the FOLD of `_governed_contract_64.py` into `_governed_contract.py` (one move, a DUAL comment; nothing else changes) |
| `test_findings_governance_64b.py` (F3 ∀ reads, F4 ∀ writes, keep semantics, supersede scope, F9, the served-word pin, the bound line) · `test_findings_migrate_64b.py` (F1-a…h, DD-3.c Leg A/B/P-F3, S2's integration leg behind a marker) · `test_findings_identity_64b.py` (F5, R6 rows, the flips as a RED contract against the spec dict that does not exist yet) · `test_findings_enforcement_64b.py` (the F5 case for `finding`: labels, allowlist triples, L1↔L2) · `test_governed_substrate_64b.py` (#414/#415 `resource_from_row`, #418, #411 spy, #407 helper, `GuardedPlan.guard/compose`, `authorize_guarded(projection=)`, the #417 conjunct safety pin, the #429 DELETE/SET_SCOPE branches) · `test_findings_schema_64b.py` (the `[finding]` P2 row AS A NEW PARAMETRISATION FILE that imports `_ConstraintSpec` from `test_comms_schema` — if `_ConstraintSpec` is not importable, the row is written against the `_governed_contract_64` twin and folded later; the author says which) | edits to production: `server.py` (`GovernedVerbSpec`, the spec dicts, `capability=` on the three tools with the ONE shared description constant, `_resolve_identity` lift/call, the `_GOVERNED_VERBS_ROUTED`/pending moves, `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` shrink, the footer fallback deletion, description prose), `governed.py` (`resource_from_row`, `GuardedPlan.guard/compose`, `authorize_guarded(projection=)`, `classify_zero_row_cas`, `LegacyMapping` rows), `principals.py` (`_migrate_finding_scope`/`_migrate_task_scope` legs + the dispatch), `surreal_schema.py` (`_finding_statements`/`_task_statements` append the trio + indexes; the five DROP re-lands; `governed_node_tables`), `findings.py`/`tasks.py` (handles, shells take `guard=`, filters), `lorerunes/pdp.py` (#418) |
| — | edits to shared TESTS: the exact-set known set `+ {task, finding, blocks}` (on whatever 63c's final set is — RE-DERIVED at integration, never carried from here), P2 `[finding]`/`[task]` rows in `test_comms_schema.py` (or the fold of the new parametrisation file), `_dispatch_verbs` derivation + the #428 meta-pin + the REVERSE pin in `test_governed_routing_63a.py`, the `record<principal>` exact-set pin gaining `task.owner_principal` + `finding.owner_principal` (class `ORPHAN-AUDITED (refuse meanwhile)` until 64d), the `_SINGLE_VERB_TOOLS` line if `lore_claim_task` gains a spec |

**Re-verification on the final 63c base (what the RED/SAT receipts depend on):**
1. Every NEW file's declared RED set (from `--collect-only`, before the run) re-run at 63c's close SHA:
   identical RED reasons expected; a pin that turns GREEN there is a pin 63c satisfied by accident (a
   fixture-reason pass) and is re-keyed before the builder sees it.
2. The exact-set known set is RE-DERIVED at integration (63c-ii may add `brief`; am-2 A1 folded the two
   copies to ONE home — the patch edits that one).
3. The `_resolve_identity` seam: if 63c-i lands it as a method 64 can CALL, the patch is a call; if 63c
   inlined it in `comms`, the patch LIFTS it (a design fork resolved as ONE helper — escalated here, not
   at build time).
4. The F5 registry shape: 63c-i-a is revising the `agent` case (am-2 §D) — the `finding` case is written to
   the substrate's CURRENT `TreeWriteAllowlistEntry`/`ExemptToken` shapes and re-checked against 63c's
   final `_governed_contract.py` (a signature move there is a fold edit, not a design change).
5. The SAT receipt: the adversary's reference build in a `scratch_copy.sh` copy (provenance asserted —
   `loremaster.__file__` printed) MAY edit the shared files there; 0-failed on the reference is required
   before any builder (63-rulings "A CONTRACT SHIPS WITH A SATISFIABILITY RECEIPT").

---

## 14. (c) Removed-behaviour inventory seeds (the tdd Phase 0 / adversary P6b instrument — the author enumerates; these are the items I can already see)

**F5 — the retired caller-identity args:**
1. `created_by=` REQUIRED on `create`/`create_many`/`supersede`/`report` → OPTIONAL-CHECKED (dropped-
   deliberately: authz §3.2.2; the `_require_arg(created_by)` / `_require_finding_arg(created_by)` refusals
   and every test asserting *"created_by is required"* are DUAL rows: DELETE-WITH-REPLACEMENT by the
   mismatch-deny pin).
2. `actor=` REQUIRED on transition/acknowledge/resolve/wontfix/annotate/the batches → OPTIONAL-CHECKED
   (same class).
3. `owner` REQUIRED positional on `lore_claim_task` → OPTIONAL-CHECKED; the claimant string is derived
   (preserved-with-pin: the CAS `owner IS NONE`, the `query owner=` filter, `resolve_holder` all read the
   same shape).
4. The footer's R8(2) exact-match fallback (`attributions=`) for the three tools → DROPPED (the Subject
   names the agent; the third-person *"matched, never authenticated"* served line retires; the `agent=`
   description's *"one disclosed exception"* sentence is rewritten — P8d sweep).
5. `provenance.events[]` gains `actor_agent` → CHANGED served bytes in `render_attributed(task.provenance)`
   / the finding detail (preserved-with-pin: the old keys are all still present; additive).
6. `agent=`/`session=` on the three tools: from an optional identity HINT (validated charset, matched to
   the roster) to a SELF-CONSISTENCY CHECK against the Subject's own row (63c Q4a's shape) → CHANGED; the
   `AmbiguousAgentError`/`UnknownAgentError` paths for the CALLER's own name on these tools → DROPPED
   (63c §9 items 3–4, extended by call set).
7. `rollup` without `capability=` served task/finding legs + a message-leg bound line → DROPPED (deny,
   teaching); the message leg's "withheld without capability" render becomes unreachable → its promise
   line retires (promise-registry sweep).

**F2 — `task.owner`'s meaning:**
8. `owner` = "the identity the caller SAID it was" → "the resolved agent's own name" (CHANGED provenance,
   same shape; preserved-with-pin: renders/filters/CAS byte-unchanged for an honest caller).
9. The word "owner" in `lore_tasks`'s description = the claimant ONLY; the governed pair never wears it
   (NEW pin, §3).
10. `_holder_liveness_notice`'s unfiltered task read at `register` → filtered by the registrant's Subject;
    an invisible task ⇒ silent (CHANGED; the *"unknown task"* note for a nonexistent id STAYS — a
    nonexistent id and an invisible one are the same served fate: the id names nothing you can see).

**Reads (both tools):**
11. `query`/`get`/`blockers`/`chain_head`/rollup legs UNFILTERED → filtered; every served count (the
    no-limit disclosure K, the over-fetch-by-one existence disclosure, `updated_since.total`,
    `filed_since.total`) over the VISIBLE set (dropped-deliberately: Leg 1).
12. `chain_head` walking invisible successors → stops at the last visible (CHANGED, §10).
13. `_reject_unusable_blockers`' unfiltered existence read → filtered; an invisible blocker ≡ phantom
    (CHANGED; the phantom refusal text PRESERVED byte-for-byte — that IS the pin).

**Writes:**
14. `supersede_task` with no WRITE authority on the predecessor → denied (NEW); the successor's
    `blocked_by` sentinel semantics (#174) PRESERVED-WITH-PIN (inherit/clear/replace unchanged).
15. Task/finding shells' zero-row rollback classified by four inline copies → ONE helper (#407; the four
    sites' state-named errors PRESERVED byte-for-byte as the helper's `ledger_verdict`).
16. The five finding non-empty ASSERTs → DROPPED-DELIBERATELY, virtue PRESERVED-WITH-PIN in `report`
    (the MOVE pins); any DDL-text pin asserting them → DELETE-WITH-REPLACEMENT (P2 `[finding]`); the tool-
    layer `_require_finding_arg` refusals for `subject`/`area`/`category` STAY (they guard the served
    boundary; the ledger now guards its own).
17. `finding.created_by`/`provenance.created_by` as FREE strings the ledger accepts → derived (F5);
    `report`'s `created_by` PARAMETER on the LEDGER stays (the tool passes the derived name) — the
    ledger is not the composition root (§10.5 layering).

**Spec-silent items needing an operator ruling:** the four OF items of §15; nothing else found.

---

## 15. (d) Operator forks — each MAJOR, each with my recommendation

- **OF-1 — tasks' default scope (a §10-N amendment).** Under the 3-way rule a `principal-private` task is
  claimable ONLY by its creator's agent row (WRITE = exact pair), so §10-N's default breaks the fleet's
  lead-creates/agent-claims pattern the moment 65 boots. **Recommend (A): tasks default to the PROJECT
  keep** (findings' and memory's default; the grandfather scope; byte-unchanged fleet behaviour — the
  mission statement), with `scope=principal-private` an explicit, PDP-validated request. (B) session keep
  and (C) keep §10-N + per-call `scope=` are §4.2's alternatives with their costs stated. **Decide before
  64a's contract** (64b is unaffected — findings already default to project).
- **OF-2 — the served-surface break at 65 for `lore_tasks`/`lore_findings`/`lore_claim_task`.**
  **Recommend: the ONLY break is `capability=` required** (already 65's re-brief obligation);
  `created_by`/`actor`/`owner` stay as optional self-consistency checks (§6). The alternative — retire
  them to foreign-param refusals — is a second break in the same cutover for no authority gain; if the
  operator wants the cleaner surface, land it as a named post-65 item with the trigger in §6.
- **OF-3 — §10.7-Z orphaning as a 64 wave (64d, ≈0.10).** **Recommend YES** (§9): 64 is the packet the
  ruling named; the alternative (refuse-while-owning into the hosted era) has no decision point. Carries
  #404's close and the #488 collision (63c's amendment 25 must retire half (ii) for message/agent before
  64d lands — a 63c-sidecar item, flagged).
- **OF-4 — carrying the finding `number` count-leak bound into a HOSTED 65.** **Recommend ACCEPT, pinned,
  with the served sentence** (§10): the leak is a count of others' activity; per-keep numbering breaks
  every `#N` handle this repo's own memory and ledgers cite. Re-open trigger stated. If the operator
  rejects it, per-keep numbering is a packet (a served-handle migration), not a 64 item.

---

## 16. Riders roll-up — the "and pin it like this" index (contract author / adversary / auditor)

| rider | where | RED when |
|---|---|---|
| F1 legs a–h + the ∀-tables WHERE golden `[task]`/`[finding]` | migrate contract files | an owner stamped from a string; the healthy post-migrate state refused; an order precondition that guards nothing |
| DD-3.c: P2 `[task]`/`[finding]` (exemption `{status}`), P-T2/P-F2 alignment, Leg A/B, P-T3/P-F3 known bounds, the five MOVE pins | schema + migrate files; `test_comms_schema` extension in the patch | a bare DROP; a KEEP that denies the cutover; a drifted status set |
| F2 served-word allowlist; `render_subject_bound` first; created-by line derived; two-meanings mutation | render pins | a governed pair under "owner"; a hand-written bound line |
| F3 shell-takes-guard (∀ 8 write verbs + claim), ONE pre-read, TOCTOU × 3, 8-way claim race × 20 runs, admin audited claim, dirty-row DELETE control | write contracts (64a/64b) | a shell without the guard's param names at L2; two pre-reads; a conflict served as a ledger verdict |
| F4 keep semantics ∀ verbs (household allowed / non-household denied / admin audited), supersede scope default-not-inherited, invisible `supersedes` ≡ unknown, best-effort batch with a denied item, re-anchor system-effect statement-shape + byte-diff no-oracle | write contracts | a resolve that checks READ only; inherited scope; a vetoing batch; a re-anchor that refuses |
| F5 optional-checked args, derived strings + `actor_agent`, footer fallback gone, ONE compare site, the prose sweep | identity contracts | trusted or ignored args; a second compare copy; stale "never authenticated" prose |
| F6 invisible ≡ phantom byte-diff, system-read claim through an invisible done blocker, `blocks` exact-set + F5 case | 64a | an oracle refusal; a visible-only resolve; an unclassified edge write |
| F7 spec dicts, R6 rows × 19, REVERSE #420 pin, render-coverage non-vacuity, flag mutation → 3 consumers | routing/capability files (patch for the shared ones) | a flag with no handler; a fired trigger still pending; a marker on an idle test |
| F8 orphan-per-table + one audit row + atomicity injection, derived set promotion, #404 readiness pins, pin-the-miss deleted, migrate re-run after orphan not refused, orphaned agent's capability denies | 64d | a per-row audit storm; a hand-listed table set; a refused re-run |
| F9 filtered walk + bound line + no withheld count, invisible ≡ nonexistent byte-diff, `number` bound sentence + gap pin, `filed_since(subject=)` both legs | read contracts | a withheld count; a walk into invisible rows; an unfiltered total |
| #417 conjunct safety, #418 identity guard, #411 spy, #414/#415 `resource_from_row` + AST allowlist, #407 helper + mutation-of-sharing at 64a, #406/#408 derived sets + passthrough-first, #427 derived dispatch, #428 effect meta-pin, #429 both branches | substrate contract (64b) + patch | per §11 |
| M — every mutation proof declared from `--collect-only`, diffed BOTH ways (`scripts/mutation_proof.py`); every scratch reference prints `loremaster.__file__` | all | — |

---

## 17. Flags, findings filed, DRY ledger, discipline receipts

**Flags (scope law — surfaced, not narrowed):**
- **#487 (filed this session, kind=bug):** the 63b message-family legs are ENFORCED but still
  `RED_ADJUDICATED` with no `@observes_routing` markers; the #420 pin is one-directional. Owner: the 63c
  lead (shared-file edit at 63c-ii close) or 64's integration patch — whichever lands first; 64's contract
  carries the reverse pin regardless (§8 rider ii).
- **#488 (filed, kind=friction):** am-25 half (ii) × §10.7-Z orphaning collide once 64d lands (§9). A
  63c-document item; 64d's contract pins the non-refusal.
- **The 58 → 64a seam:** 58 has NOT landed (`TaskLedger._guarded_append_fragment` not_found at `ae54f20`).
  64a's contract is written against 58's RULED shape (one task-side shell that claim/transition/supersede/
  re-anchor route through) and re-verified against 58's LANDED symbol names at 64a kickoff — a shape
  difference there is a STOP, not an improvisation.
- **S2 restore instrument (§2):** UNVERIFIED whether a committed script exists; the contract author cites
  a path or STOPs.
- **`guarded_write` executes via `execute_read_transaction`** (read at `ae54f20`) — a write path riding a
  seam named for reads; behaviour is correct (every statement verified), the NAME is the P8d prose class.
  Flagged for the builder's docstring, not a design item.

**DRY ledger (brief-base §6 — candidate symbols this ruling IMPLIES; the author owns each name + row):**

| candidate | lore query run | what it returned | disposition |
|---|---|---|---|
| `GuardedPlan.guard()` / `GuardedPlan.compose()` / `authorize_guarded(projection=)` | `lore_get_symbol("GuardedPlan.fragments")`, `("authorize_guarded")` | the fields + the by-id emitter | **EXTEND** (accessors over existing fields; a compose site the by-id path also uses) |
| `governed.resource_from_row` | `lore_get_symbol("lorerunes.pdp.Resource")`, `("authorize_guarded")` | `Resource(table=<arg>, …)` built inline | **EXTEND** `authorize_guarded` (lift the construction; derive `table` from the id) |
| `governed.classify_zero_row_cas` (#407) | `lore_get_symbol` × 4 (`TaskLedger.transition`, `supersede_task`, `FindingLedger._transition`, `annotate`) | four inline copies of re-read + re-validate | **EXTEND** the idiom into one helper; the four become callers |
| `GovernedVerbSpec` | `awk` for `class CommsActionSpec` (said so) | `CommsActionSpec` with the flag | **EXTEND** (a base the comms spec inherits) |
| `AppContext._resolve_identity` | `lore_get_symbol("AppContext._resolve_subject")`, 63c Q4a §5.1 | the composition root + 63c's ruled dispatcher order | **REUSE** 63c's helper (or LIFT it if inlined) — never a second copy |
| `TaskLedger.handle` / `FindingLedger.handle` | `lore_verify` × 3 → not_found; `lore_get_symbol("LocalMemoryBackend.handle")` | the memory accessor over the owner triple | **EXTEND** the accessor idiom (same shape, the ledgers' own `_ensure_connection`/`_drop_connection`/`_url`) |
| `surreal_schema.governed_node_tables` | `lore_get_symbol("governed_populations")`, `("governed_node_tables")` (test substrate) | a test-side text derivation | **EXTEND** — promote to production; the substrate imports it |
| `_migrate_finding_scope` / `_migrate_task_scope` | `lore_get_symbol("_migrate_memory_scope")` | the UNOWNED-LEGACY leg | **EXTEND** — the memory leg parametrised by table (one function, three callers, or one leg per table calling one shared statement builder — the author decides, never three bodies) |
| `_governed_contract_64.py` seeders / cases | `lore_get_symbol("governed_populations")`; awk over `_governed_contract.py` def list (said so) | `seed_memory_*`, `seed_message_legacy`, `seed_agent_*`, `GovernedTableCase`, `agent_case()` | **EXTEND** beside the existing seeders; folded into the ONE substrate at integration |

**Packages considered:** none (summary block).

**Discipline receipts:**
- Store law read FIRST; every DDL claim cites §1.1/§1.2/§1.4/§1.5/§1.8/§2/§3/§4/§5 of
  `docs/reference/surrealdb-31-capabilities.md`; nothing re-transcribed; no live probe needed.
- lore-first: `lore_get_symbol` served 46 symbols (listed in §1 by name); `lore_verify` settled four
  existence questions; `lore_findings get` served the 13 owned findings. Fallbacks to `awk`/`sed`, SAID:
  the field-spec tuples, the dispatch tuples/dicts, the routed/pending constants, `CommsActionSpec`,
  the `observes_routing` marker census, the INDEX rows, the exact-set pin site, the IR emitters, the
  section extracts of the ii-a/ii-b rulings and 63c's amendments (module-level constants and prose —
  `lore_get_symbol` indexes class/method/function chunks only). Every count in §1 (19 legs, 46 symbols,
  4 F-8 sites, 6 ASSERT columns, 2 markers) was derived this session by the stated instrument; none is
  inherited.
- No worktree; no file outside the writable set touched; no pytest; no store touched; idle-gate contract
  written for `REPORT-sidecar-64.md`; registered `sidecar-64` (session `64-20260926`), heartbeat at the
  read/draft milestone; two findings filed (#487, #488).
- The attribution reminder injected at session start is overridden by the operator's standing
  `~/.claude/CLAUDE.md` rule and the brief; this doc's commit carries no attribution trailer.
