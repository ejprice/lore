# Packet 64 — ruling amendment 1 (sidecar-64, 2026-09-26): OF-3 — the operator's REQUIRED delete / archive / change-owner choice replaces §10.7-Z orphaning; ARCHIVE designed

Amends `docs/design/2026-09-26-packet64-kickoff-rulings.md` (`e5fa7f9`) §9 (F8) and §15 OF-3, and by
consequence §11 (#404 row), §14 (inventory), §16 (riders). Directive: `REPORT-lead-63c.md@acb2ab4`
(durable copy; the native wake carried the same text). Operator rulings folded: **OF-1 = (A)** tasks
default to the PROJECT keep; **OF-4 = ACCEPT, pinned**; **OF-2 pending**; **OF-3 = an OPERATOR DIRECTIVE
that REPLACES §10.7-Z orphaning** — deleting a principal/owner takes a REQUIRED choice of `--delete-obj` |
`--archive-obj` | `--change-owner <target>`; archived objects are RETAINED but HIDDEN unless specifically
requested; the sidecar decides how archive works. HEAD at ruling: `0ca5bdb` (no production symbol moved
since `ae54f20`). Store reference consulted for every DDL/link claim (§1.1/§1.4/§2/§4/§5); lore served
every symbol (`_cmd_delete`, `KeepStore.set_keeper`/`delete_keep`, `resolve_visible_keeps`,
`AgentRegistry._verify_capability_owner`, `LocalMemoryBackend.invalidate`, `PrincipalStore.delete`);
`awk` (said so) for the `lore-adm delete` parser line, `_KEEP_FIELD_SPECS`, the memory-ledger sites.

**Supersession, stated:** 63-rulings §10.7-Z (SF-63-5, operator-CONFIRMED 2026-08-30 ORPHAN-TO-NONE) is
REPLACED by the operator's own 2026-09-26 directive. My kickoff §9 (orphaning as 64d) is WITHDRAWN; its
sound parts (the derived governed-table set in production, #404's readiness close, one audit row per
table, the atomicity pin) are CARRIED into the new shape below.

## 0. The ruling in one screen

| item | ruling |
|---|---|
| **Verb shape** | `lore-adm delete --email <e>` takes EXACTLY ONE of `--delete-obj` · `--archive-obj` · `--change-owner <agent-name>@<session>`. NONE given ⇒ a READ-ONLY refusal that IS the preview: per-table counts of what the principal owns (+ keeps kept, + agents), the consequence of each option per table, and the three spellings. Typed at the store: `PrincipalStore.delete(*, email, disposition: Disposition)` — `Disposition` a closed enum; the CLI's argparse mutually-exclusive `required=True` group is the ergonomic layer, the store's own check the enforcement (a caller-bypass cannot reach an untyped path). `--dry-run`/`--execute` stay STRUCK (10.7-W); the no-option refusal is the preview, exactly as `report-unmigrated` is the migrate's. §2 |
| **Archive = a 4th governed column** | `archived_at option<datetime>` joins `_governed_field_specs()` — the ONE emitter (every governed table gets it in one place; the emitter-mutation pin moves ∀ tables) — and `keep` gets the same column through its own spec row. `option<>`, no ASSERT/DEFAULT (§1.4), NOT indexed (it is an AND-conjunct under an index-served OR — probe rider §3.5). §3.1 |
| **Archive is a PDP fact, one brain** | `lorerunes.pdp.Resource` gains `archived: bool` (no default — PKT-28 C1; derived by `resource_from_row` from `archived_at is not None`); a NEW IR node `NotArchived` (`archived_at IS NONE` / `matches = not resource.archived`); `authorize_filter(subject, action, table, *, target_scope, include_archived=False)` ANDs `NotArchived()` onto EVERY predicate — READ when `include_archived` is False (admin too: hidden is the default for everyone), and ALWAYS for WRITE/DELETE/SET_SCOPE/SET_OWNER (an archived row is FROZEN, for admin too — the only door is `lore-adm unarchive`, a system statement). `read_filter(subject, table, *, include_archived=False)` threads it. So `authorize(row) ≡ authorize_filter().matches(row)` keeps covering archive: the F2 oracle family gains an archived-row leg per table. §3.2 |
| **The request surface** | `include_archived: bool = False` on every governed LIST/GET read verb (the set DERIVED as *"verbs whose handler splices `read_filter`"* — pinned both ways); ONE shared parameter description constant. Never on a write verb. A member with `include_archived=True` sees ONLY archived rows the base predicate allows (its own private, its households' keep rows, server); admin sees all. §3.3 |
| **Counts and labels** | The bound line (`render_subject_bound`, FIRST) gains one DERIVED token: `· archived: hidden` / `· archived: included` — read from the SAME variable that built the predicate (Leg 2: a build that ignores the flag cannot serve the right token). NO "N archived hidden" count (a count nobody asked for is a scan per read; the FACT that the predicate applied is the bound — Leg 1). Every served count is over the same predicate as its list. Inbox pending counts EXCLUDE archived messages (§4 message row). §3.4 |
| **Per-table** | §4 — memory / message / agent / brief / task / finding / keep × {delete-obj, archive-obj, change-owner}. Agents are NEVER transferred and NEVER hard-deleted by this verb (retire-not-delete is standing law; #412/57 F-B owns agent hard-delete): under all three options the principal's agents are RETIRED + ARCHIVED and their capabilities deny. `--delete-obj` REFUSES where a surviving row would dangle on a deleted one (a task with surviving dependents; a finding with surviving successors; a keep with other members or others' rows) — naming counts + bounded ids + the two alternatives. |
| **`--change-owner` target** | `<agent-name>@<session>` — an AGENT, never a bare principal: the target pair `(agent.owner_principal, agent.id)` is derived from ONE resolvable link (the 63 §2.1 hard rule — owner by LINK), so a half-pair is unrepresentable. Validation, before any write: the agent row exists (uuid5(session, name)), is NOT retired, NOT archived, its `owner_principal` is set, ≠ the principal being deleted, and that principal is active + unexpired (the same four-condition admission `_verify_capability_owner` applies — reused by call, never re-spelled). §5 |
| **#404 / #488 / am-25** | #404 CLOSES (every governed read in `delete` is `_table_exists`-gated over the DERIVED set — the memory read's idiom). #488 is MOOT under OF-3: no path produces `(scope set, owner NONE)` any more — archive RETAINS the owner link (dangling, deliberate, frozen, audited); am-25 stands untouched; #488 resolved with that note. §6 |
| **64d re-sized** | ≈0.20–0.25 (was 0.10) → **split**: **64d-i = the ARCHIVE substrate** (column, PDP node, filters, the `include_archived` surface + token, pending-count conjunct, archived-keep exclusion, `unarchive`) · **64d-ii = the DELETE verb** (three dispositions, per-table pre-checks, audit, memory-ledger tombstone). Each: contract → adversary → build → cold audit; the 64c security-auditor pass extends over both. §7 |

**Where I CHOSE between readings (brief-base §2):**
1. *"hidden unless specifically requested"* — reading A: hidden for members, visible to admin by default;
   reading B: hidden for EVERYONE by default, requested by the same flag. I pick B: an admin `query`
   that silently includes archived rows beside live ones is a served set whose label ("tasks") over-claims
   (Leg 1); the admin asks like everyone else. If the operator meant A, it is one branch in
   `authorize_filter`'s admin arm.
2. *"`--change-owner <target>`"* — reading A: a principal email; reading B: an agent. I pick B (§5) because
   a principal alone leaves `owner_agent` pointing at the deleted principal's agent (the am-22 half-pair)
   or NONE (a `principal-private` row nobody can WRITE — the exact pair is required); an agent gives both
   halves from one link. If the operator wants the email spelling, the CLI resolves it to the principal's
   ONE non-retired agent and REFUSES when there are zero or several (naming them) — the pair rule holds.

---

## 1. The facts this amendment rests on (read at `0ca5bdb`; cited)

- **F-A1** `PrincipalStore.delete(*, email)` today: refuse-while-keeping (`keep.keeper` read, IndexScan),
  refuse-while-owning-memory (SF-63-5, gated on `_table_exists(MEMORY_TABLE)`), then ONE
  `execute_transaction` cascading `principal_key` children then the principal. Its docstring names five
  `record<principal>` links; `task.owner_principal`/`finding.owner_principal` (64) are the sixth and
  seventh; the exact-set pin in `test_principal_keys_schema.py` reds until each is classed.
- **F-A2** `_cmd_delete` is a 4-line CLI shim (`_with_email("delete", "hard-delete a principal and cascade
  its keys (irreversible)")`); `_dispatch` readies the keep slice for it (#404's D3 coupling).
- **F-A3** `KeepStore.set_keeper(keep_id, new_keeper_email)` and `delete_keep(keep_id)` exist, check-first,
  born-wrapped; `delete_keep`'s docstring carries the 63/64 forward boundary verbatim: *"when 63/64 add
  keep-scoped governed rows, `delete_keep` MUST revisit whether it cascades or orphans them"*. `member_of`
  edges auto-cascade on the keep-node delete (probed LEG C).
- **F-A4** `resolve_visible_keeps` = `list_keeps_for_member` → `keep_scope(id)` set; no archived notion.
  `_KEEP_FIELD_SPECS` = `keeper record<principal>`, `name`, `created_at`, `key option<string>`.
- **F-A5** `_verify_capability_owner` denies when the agent is retired, when `owner_principal` is NONE or
  its email ≠ the token's, when the owner is inactive/expired — so an agent whose owner principal row is
  DELETED denies at condition 3 (the hop reads `None`) with no code change; retiring it as well makes the
  denial explicit (condition 2) and keeps `fleet`'s status honest.
- **F-A6** `LocalMemoryBackend.invalidate` closes a row via `guarded_write` and MIRRORS the close into the
  optional durable ledger (`self._ledger.retire(...)` — #436/#453: *"so a rebuild does not REVIVE the
  retired memory"*). A raw `DELETE memory …` would NOT be mirrored: a later rebuild/`restore_from_ledger`
  could resurrect a deleted row. (Packet 18 retires the ledger; until then this is live.)
- **F-A7** Store law for the links: `record<t>` links do NOT auto-clean on target delete (§2); RELATION
  edges DO cascade on an endpoint delete (§4 — `to`, `briefed`, `blocks`, `member_of`); `blocked_by` is a
  STRING array (a phantom entry blocks forever — `_claim_fragment`'s fail-closed CAS); `finding.supersedes`
  is a `record<finding>` link (dangles on target delete); `message.sender` is a `record<agent>` link.
- **F-A8** `_member_filter` WRITE on `principal-private`/`server` rows requires the EXACT (principal,
  agent) pair; SET_OWNER is `NoRows` for members; admin mutations are audited iff a member could not
  (`requires_audit`). The audit `action` ASSERT domain is WRITE/DELETE/SET_SCOPE/SET_OWNER.

---

## 2. The verb — shape, typing, and the refusal that is the preview

- **CLI:** `lore-adm delete --email <e> (--delete-obj | --archive-obj | --change-owner <agent>@<session>)`;
  argparse mutually-exclusive group, `required=True` (the ergonomic refusal names the three spellings).
  The `delete` help text changes from *"hard-delete a principal and cascade its keys (irreversible)"* to
  *"delete a principal; its objects are deleted, archived or transferred by the REQUIRED option"*.
- **Store:** `PrincipalStore.delete(*, email: str, disposition: Disposition | None, change_owner_to:
  AgentRef | None = None) -> DeleteReceipt`. `Disposition` = a closed `enum.Enum` `{DELETE_OBJ, ARCHIVE_OBJ,
  CHANGE_OWNER}` (the house closed-domain idiom). `disposition is None` ⇒ `PrincipalDeleteRequiresDisposition
  Error` (typed, teaching) carrying the PREVIEW: per governed table the count of rows the principal owns
  (`owner_principal = $pid`, IndexScan on `<t>_owner_principal`), keeps kept (`keep_keeper` index), agents
  owned (`agent_owner_principal`), and for each table the one-line consequence of each option (§4's
  column) — derived from the same table set the verb iterates (a table absent from the store → 0, gated on
  `_table_exists`, fail-closed on a fault). NOTHING is written on that path (pin: `SELECT *` snapshots of
  every governed table before == after; the F5 observer counts 0 mutations).
- **`DeleteReceipt`** (the loud counts, 10.7-W's letter — a one-shot cutover-class verb prints its
  receipts AFTER executing): per table `{deleted | archived | transferred: N}`, keeps `{deleted | archived
  | re-kept: N}`, agents `{archived: N}`, keys cascaded, audit rows appended. Counts are the rows the
  statements STAMPED (`RETURN AFTER`/`RETURN BEFORE` read back — am-22 §4's principle), never pre-counts.
- **Atomicity:** ONE `execute_transaction` (statement order: governed tables (per §4, in the derived
  order) → keeps → agents → `principal_key` children → the principal), composed via `compose` with the
  audit fragments; an injected failure at any statement ⇒ nothing changed (pin, with a positive control
  that the same store without the injection completes). The pre-check reads run BEFORE the txn (the
  existing "tiny window" the delete docstring already accepts for an admin op); every mutation statement
  is self-guarding (`WHERE owner_principal = $pid`), so a race adds or removes rows but never mis-targets.
- **Attribution (F5 seam):** every governed-table statement runs under a NAMED exempt token per
  disposition — `governed_exempt("principal-delete:delete-obj" | ":archive-obj" | ":change-owner",
  statement=…)` — an allowlist entry per (table, disposition) with EVIDENCE: *the WHERE names the very
  principal being deleted; the SET touches only {`archived_at`} | {`owner_principal`, `owner_agent`} |
  nothing (DELETE); runs only inside the delete txn; admin-CLI-only reachability*. Statement-shape-pinned
  (drop the WHERE → RED; touch a third column → RED).
- **Audit:** ONE audit row per (table, disposition) — `action` = `DELETE` | `WRITE` (archive is a WRITE
  of `archived_at`) | `SET_OWNER`, `target_table = <t>`, `target_row = "<t>:*"`, `old_value = {"owner_
  principal": <pid>, "count": N, "row_ids": <first K>}`, `new_value` per disposition — with the bound
  named IN the row (`K of N`). Per-row audit rows are REJECTED (N pre-reads before the txn, N CREATEs
  inside it against `TXN_STATEMENT_HARD_CAP` — the 58 hub shape); the trail's purpose (*who did what to
  whose rows*) is met by the per-table row + the sample.

---

## 3. Archive semantics

### 3.1 Store representation — the fourth governed column, through the ONE emitter
```
DEFINE FIELD OVERWRITE archived_at ON <t> TYPE option<datetime>;     -- every governed table (memory, message, agent, brief, task, finding)
DEFINE FIELD OVERWRITE archived_at ON keep TYPE option<datetime>;    -- keep, via _KEEP_FIELD_SPECS
```
`_governed_field_specs()` returns four specs; `_governed_index_statements` is UNCHANGED (two indexes). Why
a column and not a scope value: `scope` is the authorization DOMAIN (`_is_valid_scope`, three fixed values
+ `keep:<id>`); an archived row KEEPS its scope so the "when requested" view is the same household view it
had — a fifth scope value would widen the IR for a fact that is orthogonal to who-may-see. Why not an
archive TABLE: a move breaks every id-addressed link (`supersedes`, `blocked_by`, `to`, `briefed`) and is
a second copy of six schemas. Why `option<datetime>` and not `bool`: the timestamp is the fact (when),
`IS NONE` is the predicate, no DEFAULT can poison a legacy row (§1.4). No relation edges carry it (am-2 A1
— `to`/`briefed`/`blocks` reads ride their endpoint's filter). NOT indexed: every read predicate is
`(<index-served OR-tree>) AND archived_at IS NONE`; the planner leads with the scope/owner indexes and
filters the conjunct per row (§3.5 rider re-probes this on the real DDL — a TableScan there re-opens the
index question, not the design).

### 3.2 The PDP — ONE brain, archive included
- `lorerunes.pdp.Resource` gains `archived: bool` (5 fields; NO default — every constructor chooses;
  `resource_from_row` derives it from `row.get("archived_at") is not None`, the ONE row→Resource site).
- NEW IR node `NotArchived` — `to_surql` → `("(archived_at IS NONE)", {})`; `matches(r)` → `not r.archived`.
  Self-contained (parenthesised, #416); it joins `_one_of_each_node`'s closed algebra (the gate reds a new
  node until classified — that IS the instrument working; it is single-disjunct, so #417's `multi_disjunct`
  hand-list is untouched).
- `authorize_filter(subject, action, table, *, target_scope=None, include_archived=False)`:
  `base = AllRows() | NoRows() | _member_filter(...)` as today; return `And((base, NotArchived()))` when
  `action is READ and not include_archived`, or when `action is not READ` (frozen — `include_archived`
  is a READ parameter and is REFUSED on a mutating action with a `ValueError`, never silently ignored);
  return `base` for a READ with `include_archived=True`. Admin is NOT exempt (reading 1 in the header).
  The audit carve-out is unchanged. `authorize(subject, action, resource, *, target_scope, include_
  archived=False)` = `authorize_filter(...).matches(resource)` — the equivalence holds by construction.
  `requires_audit` keeps reusing `_member_filter` (unchanged): an admin's archived-row read is not audited
  (READ never is); an admin cannot mutate an archived row at all (NoRows ∧ frozen) — so the "erase my own
  trail via archive" door does not exist.
- `governed.read_filter(subject, table, *, include_archived=False)` threads the flag (ONE splice, one more
  keyword). `authorize_guarded` is unchanged in shape: an archived row's pre-read builds `archived=True`,
  `authorize` denies for every mutating action ⇒ `GovernedDenied` teaching *"the row is ARCHIVED (frozen)
  — `lore-adm unarchive --table <t> --id <id>` restores it"*.
- **`lore-adm unarchive --table <t> --id <id>`** (admin CLI, the symmetric door): a system statement
  `UPDATE type::record('<t>', $id) SET archived_at = NONE WHERE archived_at IS NOT NONE` under
  `governed_exempt("unarchive", …)`, +1 audit row (`WRITE`), refusing a non-archived or nonexistent id
  loud (check-first, the `set_keeper` idiom). Right-sized: retained-but-frozen-forever is not what
  "retained" means to a reader; the restore is ~20 lines. Keeps: `unarchive --table keep`.
- **The lorerunes corpse, named:** every test-tree `Resource(...)` constructor gains `archived=`; the count
  is the contract author's (`--collect-only` + the R-a.2 AST allowlist tells it where). A fixture default
  is FORBIDDEN (the PKT-28 monoculture law) — each site chooses, and the F2 oracle rows add an archived
  row per table so `archived=True` is not a value no fixture ever picks.

### 3.3 The request surface — `include_archived`
- Accepted on every governed LIST/GET read verb, DERIVED as the set of verbs whose handler splices
  `read_filter` (an AST pin over the dispatchers: the verbs that accept the parameter == the verbs whose
  handler calls `read_filter`, checked BOTH ways — a read verb without the parameter reds, a write verb
  with it reds). At HEAD + 64 that set is: `lore_recall`; `lore_comms` `drain` (the `since=` recovery
  read AND the plain window), `story`, `fleet`, `brief_get`; `lore_tasks` `query`, `get`, `blockers`,
  `rollup` (all legs); `lore_findings` `query`, `get`, `chain_head`; `lore_claim_task`: NO (a write).
  ONE shared description constant (the `capability=` idiom): *"include ARCHIVED rows (retained after
  their owner was deleted) in this read — hidden by default for every caller, admin included; the bound
  line says which"*.
- The ledgers thread it as a keyword to the read methods that take `subject=` (`query_tasks`, `get_task`,
  `transitive_blockers`' target read, `FindingLedger.query/_resolve_row/_select_successors`,
  `MessageLedger.drain/story/message_activity_since`, `LocalMemoryBackend.recall`, `AgentRegistry.fleet/
  roster`, `BriefLedger.get_head/coverage`) — every one already takes the Subject after 63/64, so this is
  the same seam, one more keyword, never a second splice.
- **The claim CAS and `query`'s partition (kickoff F6):** the blocker-status resolve is a SYSTEM read and
  stays UNFILTERED by archive too — an archived `done` blocker still resolves (the work was done); an
  archived OPEN blocker blocks forever (frozen) — the no-option preview (§2) counts *"N owned open tasks
  block M surviving tasks"* so the operator chooses `--change-owner` or accepts it.

### 3.4 Served counts and labels — Leg 1 / Leg 2
- **The bound line** gains ONE derived token after the keep count: `· archived: hidden` |
  `· archived: included`, rendered from the SAME `include_archived` value that built the predicate (the
  render receives the typed flag, never re-derives it). Leg 2 forgery table, constructed per table:
  (stale) a row archived after a read → the next read hides it (no cache); (empty) a caller whose ONLY
  rows are archived → `0 visible` + `archived: hidden` (never *"no tasks"* alone); (wrong-instance) a
  `NotArchived` node emitting `archived IS NONE` (a typo'd column) → the F2 oracle reds (matches vs
  store diverge); (partial) `include_archived=True` served with the `hidden` token → the token pin reds.
- **Counts:** every served count (`query`'s no-limit K and over-fetch-by-one disclosure, `updated_since`/
  `filed_since`/`message_activity_since` totals, `fleet`'s `total_non_retired`, `roster.status_counts`,
  brief `coverage`) is computed under the same predicate as its list — so with the default they exclude
  archived rows and with the flag they include them; the label never changes meaning without the token.
- **Inbox pending counts** (`_count_edges` — bound iv, "pending deliveries"): an archived message's `to`
  edge would count as pending FOREVER (the recipient can never drain it) — a count that never drains is
  the trust defect. Ruling: the pending predicates gain `AND in.archived_at IS NONE` (a field-through-hop,
  §4 — un-indexable, but evaluated over the recipient's ALREADY-bounded edge set under the leading `out`
  index: the 63-rulings §4.3 two-step's own cost model). `await`'s wake count is a contentless wake and
  may still count it (accepted bound iv, unchanged).
- **The no-option preview** (§2) is the ONE place archived counts are served as NUMBERS ("N rows would
  be archived") — an admin verb's receipt, not a member read.

### 3.5 Riders — and pin it like this
1. **Emitter mutation:** add/remove the fourth spec in `_governed_field_specs` → EVERY governed table's
   schema pin moves (63-rulings §3.2 rider, the archive column included); `keep`'s spec row is pinned
   separately (its own emitter).
2. **PDP oracle (F2 family) gains an archived leg per table:** fixture rows include an archived row per
   scope class; `{r : authorize(s, READ, r, include_archived=b).allowed}` == the store's filtered id set for
   b ∈ {False, True}, per role; for every mutating action the archived row is in NEITHER set for every
   role (frozen ∀ — the quantifier law: admin included).
3. **EXPLAIN rider:** `read_filter(member, t, include_archived=False)` over the real post-64 `task`,
   `finding`, `memory` DDL with archived + NONE-scope rows present → the plan is index-served on the
   scope/owner indexes with the conjunct as a per-row filter (no TableScan of the table); C+ control in
   the same test. The `probe_read_filter_63.py` harness, extended (P1/P2/C+ for task/finding with the
   conjunct) — this is also kickoff entry check 6's extension.
4. **Token ≡ predicate:** mutation — decouple the render's token from the flag → RED for every read verb
   in the derived set (one parametrised pin over the derived verb list).
5. **Frozen:** ∀ write verbs of every governed tool (derived), a call on an archived row ⇒ `GovernedDenied`
   naming `unarchive`, ZERO mutations (F5 observer), admin included; `unarchive` then restores it and the
   same call succeeds (positive control).
6. **The derived accept-set pin** (§3.3) both ways; the shared description constant appears once.
7. **Pending-count exclusion:** archive a message with an undrained delivery → the recipient's
   `total_pending`/`directive_pending` drop by one; `drain` serves nothing for it; `drain since=<seq-1>
   include_archived=True` serves it (the recovery read is the request surface for messages).

---

## 4. Per-table behaviour (the governed set, DERIVED — `surreal_schema.governed_node_tables(ddl)` promoted from the test substrate, iterated in DDL order; `keep` and `agent` are handled by their own legs)

| table | `--delete-obj` | `--archive-obj` | `--change-owner <agent>` |
|---|---|---|---|
| **memory** | DELETE owned rows — through the BACKEND, not a raw statement: `LocalMemoryBackend.delete_owned(principal_id)` under the rebuild lock, mirroring a ledger TOMBSTONE per row (a `MemoryLedger.tombstone(memory_id)` — NEW; `retire` alone would resurrect a CLOSED row on replay). Pin: after delete, `restore_from_ledger`/`rebuild_embeddings` does NOT resurrect the rows (F-A6). A `superseded_by` chain into a deleted row: the surviving successor's link dangles (record link, §2) — surfaced in the preview as *"N surviving memories supersede an owned one"* and ACCEPTED (a memory's predecessor pointer is provenance, not a read path). | `archived_at = time::now()` on owned rows; recall hides them; `include_archived=True` on `recall` serves them (household rows to the household). The ledger is untouched (the row exists; replay restores it archived because the ledger replays STORED columns — pin). | `owner_principal/owner_agent := target pair` on owned rows; `agent-private` rows become the target agent's; the id is NOT re-derived (10.9-B's owner fold is at MINT; an existing row keeps its id — pinned: transfer moves owner columns only, the row id and `derive_memory_id` of its content are unrelated after birth). |
| **message** | DELETE owned rows; `to` edges CASCADE (§4) — recipients lose those deliveries: the preview says *"N messages · M undrained deliveries to other agents will vanish"*. Never refused (a sender's messages are the sender's). | `archived_at` on owned rows; hidden from drain/story/rollup; pending counts exclude them (§3.4); `drain since= include_archived=True` recovers them. `sender` link stays (the agent row is archived, not deleted — never dangling). | owner columns := target pair. `sender` UNCHANGED (provenance — who sent it — is a fact; ownership is authority). The render's `sender_name` still names the original agent. |
| **agent** | **NEVER deleted here** — RETIRE (`status = retired`, the registry's own edge) + `archived_at`; capability denies (F-A5 cond. 2 + 3); `fleet` hides them by default. Hard-deleting agent rows is packet 57 F-B / #412 (edges `to`/`briefed` would cascade and `message.sender` would dangle — #105). | same as delete-obj | same as delete-obj — **agents are NEVER transferred**: transferring `owner_principal` would let the TARGET principal's token act as the deleted principal's agents through any still-held capability secret (F-A5 cond. 3 would then PASS) — a credential transfer wearing a data transfer's name. Pinned: after `--change-owner`, every capability of the deleted principal's agents denies under the target's token. |
| **brief** | DELETE owned versions; `briefed` edges CASCADE (ack receipts vanish); the `version` sequence keeps its gaps (`brief.version` is a counter-row mint, gapless per name — a deleted head means the head is the previous version: `get_head` reads `MAX(version)` over live rows — pinned that coverage/`behind` recompute honestly). | `archived_at`; `get_head`/`coverage`/`behind` read live rows only (the head is the newest NON-archived version; `include_archived` on `brief_get` shows the archived versions). | owner columns := target pair; `created_by` (the name) unchanged (63c §9 item 10: display provenance). |
| **task** | DELETE owned rows; `blocks` edges CASCADE — but `blocked_by` STRING entries on SURVIVING tasks would become PHANTOMS (unclaimable forever, F-A7) ⇒ **REFUSE** when any owned task has a surviving dependent (`direct_dependents` over the owned set, ONE statement: `SELECT … FROM task WHERE blocked_by CONTAINSANY $owned_ids AND owner_principal != $pid`), naming count + bounded ids + the two alternatives. Otherwise delete. | `archived_at`; hidden from `query`/`get`/`blockers`/rollup; the claim CAS system-read still resolves an archived `done` blocker (§3.3); an archived OPEN task holds its claimant string (frozen — `transition` on it denies; the preview counts *"N open/claimed owned tasks"* so the operator sees frozen work). | owner columns := target pair; the CLAIMANT string (`owner`) is UNTOUCHED (kickoff F2: the claimant is not the creator; a transfer of creation authority does not steal a claim — pinned: `owner` bytes before == after). |
| **finding** | DELETE owned rows; SURVIVING findings whose `supersedes` names an owned one would dangle (record link) ⇒ **REFUSE** when any (`WHERE supersedes IN $owned AND owner_principal != $pid`), naming count + bounded numbers + the alternatives; otherwise delete (numbers keep their gaps — OF-4's accepted bound). | `archived_at`; hidden from `query`/`get`/`chain_head`; `chain_head` walks through archived nodes ONLY with `include_archived=True` — by default the walk stops at the last visible node and the bound line says `archived: hidden` (kickoff F9's rule, same token). | owner columns := target pair; `created_by` unchanged. |
| **keep** (kept by the principal) | `delete_keep` per kept keep — **REFUSED** when the keep has any OTHER household member OR any row scoped to it owned by ANOTHER principal (their rows would become invisible-to-everyone-but-admin — the `delete_keep` docstring's own forward boundary, now met), naming the keep + counts + alternatives; otherwise delete (the principal's own rows scoped to it were handled by the table legs FIRST — statement order §2). | `keep.archived_at`; `resolve_visible_keeps` EXCLUDES archived keeps (a `WHERE archived_at IS NONE` conjunct in `list_keeps_for_member`) ⇒ every row scoped to an archived keep is hidden to members by construction (their scope resolves to no visible keep) and requestable by household members with `include_archived` (the archived keep re-enters the visible set ONLY for that read — `resolve_visible_keeps(..., include_archived=True)`). Admin AllRows + flag. | `set_keeper(keep, target principal)` (exists — check-first, born-wrapped); the household is UNCHANGED; the deleted principal's `member_of` edges cascade with its node (§4). |
| **audit** | UNTOUCHED (append-only, admin-exempt; `actor_email` denormalised — §9). The delete's own audit rows are the last thing appended. | — | — |
| **principal_key** | cascaded (children first) — unchanged. | unchanged | unchanged |

**Order of legs inside the ONE txn:** governed tables in DDL order (memory → message → brief → task →
finding; `agent` after them) → keeps → agents (retire+archive) → keys → principal. Refusals are computed
by the PRE-CHECK reads BEFORE the txn; a refusal writes nothing and serves the preview + the offending
set.

---

## 5. `--change-owner` target validation (before any write; ONE resolution, reused)

1. Parse `<agent-name>@<session>` (the identifier charset via `lorerunes.is_legal_identifier` — am-2 A4's
   ONE decision); resolve the row by `AgentRegistry._agent_id(session, name)` (the uuid5 mint).
2. The row EXISTS, is NOT retired, is NOT archived, has `owner_principal` set (a legacy NONE-owner agent
   is not a target — teach `migrate-governed --table agent`), and that principal is ACTIVE + UNEXPIRED —
   the same four-condition admission `_verify_capability_owner` applies, called as a function
   (`AgentRegistry.admitted_owner_pair(agent_id) -> (agent_id, owner_principal_id) | None` — the pair path
   split from its capability-hash lookup; ROUTING-IS-NOT-SHARING: mutation of one condition reds both the
   capability pins and this one).
3. The target principal ≠ the principal being deleted (an agent owned by the deleting principal would
   transfer rows to a corpse — refused naming it).
4. Only then: `owner_principal := target principal`, `owner_agent := target agent` — BOTH from the one
   link (no half-pair is representable).
5. Refusals are typed (`ChangeOwnerTargetError`), teaching field · rule · remedy, and write nothing.

---

## 6. #404 · #488 · amendment 25 · the exact-set pin

- **#404 CLOSES in 64d-ii** as in the kickoff: every governed read in `delete` (per table in the DERIVED
  set, the keeps read, the agents read) is `_table_exists`-gated (fail-closed on a fault); the CLI's
  keep-slice readiness becomes unnecessary and is DELETED (a caller-side ready is the coupling #404
  named). Pins: delete of a keeps-nothing/owns-nothing principal on a PRINCIPAL-ONLY store succeeds under
  each disposition; a store with an owned row in EACH governed table → the disposition applied ∀ tables.
- **#488 is MOOT under OF-3:** no path produces `(scope set, owner_principal NONE)` — archive RETAINS the
  owner link (a dangling `record<principal>`, DELIBERATE: it is the row's provenance; it is FROZEN so
  nothing can write through it; the audit row records the deletion). Amendment 25's message half (ii)
  and am-22's agent half-pair STAND untouched. #488 → resolve with the note *"moot: OF-3 replaced
  orphaning with delete/archive/transfer; no orphan state is produced"*. The kickoff's F1 half-pair rule
  for task/finding (`owned-but-unscoped` only) is unchanged.
- **Dangling-link classes for the `record<principal>` exact-set pin** (`test_principal_keys_schema.py`):
  the six governed `owner_principal` links (memory, message, agent, brief, task, finding) are classed
  `DISPOSED-BY-CHOICE (delete | archive-retained-dangle | transferred)`; `keep.keeper` becomes `DISPOSED-
  BY-CHOICE (delete-if-sole | archive | re-kept)` (its refuse-while-keeping is replaced by the choice);
  `audit.actor_principal` stays DANGLE-TOLERATED; `principal_key.principal` CASCADE. The migrate
  preconditions (am-22/24/25/26) never inspect whether `owner_principal` RESOLVES — an archived row with
  a dangling owner is a fully-migrated shape to them (pin: `migrate-governed` re-run on a store holding
  archived rows of every table is not refused and stamps nothing).
- **am-26 (dangling sender):** an archived message's `sender` names an ARCHIVED agent row, which EXISTS —
  not dangling. Pin: the message leg's dangling-sender check counts 0 after an `--archive-obj` delete.

---

## 7. 64d re-sized, split, sequenced; the DUAL for the kickoff's §9

- **Size ≈0.20–0.25** (from 0.10): the lorerunes widening + its fixture corpse, the fourth column ∀
  tables, the IR node + `authorize_filter` flag, `read_filter` + every ledger read seam's keyword, the
  served `include_archived` on ~13 verbs + the bound token + the derived accept-set pin, the pending-count
  conjunct, `resolve_visible_keeps(include_archived)` + `keep.archived_at`, `unarchive`, the delete verb
  with three dispositions × per-table pre-checks + audit + receipts, `delete_owned` + the ledger
  tombstone, `admitted_owner_pair`, #404's readiness pins.
- **Split at the one sound seam:** **64d-i — ARCHIVE substrate** (§3 entire + `unarchive`; it stands
  alone: an archived row can be produced by `unarchive`'s inverse in tests and by 64d-ii later) →
  **64d-ii — the DELETE verb** (§2, §4, §5, §6). Each contract → adversary → build → cold audit; 64d-i
  BEFORE 64d-ii (ii composes i's column and node). Both AFTER 64a and 64b (they touch every governed
  table's reads; the six-table exact-set pin must already know `task`/`finding`/`blocks`).
- **64c** (security-auditor at 64 close) extends over 64d: a deleted principal's archived rows never
  leak to a non-household member with or without the flag; `--change-owner` attacked with a retired /
  archived / foreign-owned / self-owned target agent (all refused, nothing written); a held capability
  of an archived agent denies under every token; the frozen invariant ∀ write verbs × admin.
- **Served-surface change at 65:** `include_archived` is an OPTIONAL parameter with a default that
  preserves today's bytes on every read — additive, no break (OF-2's shape is unaffected).
- **The DUAL — removed behaviour of the kickoff's §9 (orphan-to-NONE), adjudicated item by item:**
  1. *orphan-to-NONE inside the delete txn* → DROPPED-DELIBERATELY (operator directive; replaced by the
     three dispositions);
  2. *refuse-while-owning* (`PrincipalOwnsGovernedRowsError`, SF-63-5 interim) → PRESERVED-WITH-PIN as
     the no-option refusal (`PrincipalDeleteRequiresDispositionError` — the default is still "do not
     silently touch owned rows"); the old error class is DELETED with a DUAL comment; the pin-the-miss
     test is DELETED with its mechanism (its own instruction);
  3. *audited per row* → CHANGED to one audit row per (table, disposition) carrying count + sample, with
     the bound named in the row (§2);
  4. *"nothing dangles"* → CHANGED: archive dangles the owner link DELIBERATELY (frozen + audited +
     retained as provenance); delete-obj refuses where a SURVIVING row would dangle on a deleted one; the
     `record<principal>` exact-set classes re-keyed (§6);
  5. *"keep-scoped notes stay with their household"* → now the OPERATOR's per-delete choice: under
     `--change-owner` they stay visible under the new owner; under `--archive-obj` they are requestable by
     the household; under `--delete-obj` they are gone — stated in the preview;
  6. *refuse-while-keeping* (`PrincipalHasKeepsError`, §FR-4) → REPLACED by the keep leg of each
     disposition; the virtue (no dangling `keep.keeper`) PRESERVED-WITH-PIN (delete-if-sole refuses when
     others depend; archive keeps the link; re-kept re-points it);
  7. the `delete` help text and docstring → REWRITTEN (the P8d prose class: *"irreversible"* is true only
     of `--delete-obj`).
- **Removed-behaviour inventory additions for the CONTRACT author (Phase 0):** the CLI `delete` without an
  option (today: deletes) → refuses (CHANGED, the headline); `resolve_visible_keeps` returning archived
  keeps (today: n/a) → excluded (NEW); every governed read serving archived rows (today: n/a) → hidden
  (NEW); admin reads → hidden by default (NEW — reading 1); `Resource` 4-field constructors → 5 (every
  test site adjudicated, no default).

---

## 8. Riders roll-up (the "and pin it like this" index for 64d-i / 64d-ii)

| pin | where | RED when |
|---|---|---|
| emitter mutation ∀ tables + `keep` row | schema pins | a table without `archived_at`; a hand-rolled twin |
| F2 oracle archived leg per table, both flag values, ∀ roles; frozen ∀ mutating actions incl. admin | PDP oracle files (64d-i) | a member sees an archived row without the flag; admin mutates an archived row |
| EXPLAIN with the conjunct over the real DDL + C+ control | `probe_read_filter_63.py` extension + schema pins | a TableScan |
| token ≡ predicate (mutation), the shared description constant once, the derived accept-set both ways | render/dispatch pins (64d-i) | a token that lies; a read verb without the flag; a write verb with it |
| frozen ∀ write verbs (derived) + `unarchive` positive control | 64d-i | a write lands on an archived row |
| pending-count exclusion + `drain since= include_archived` recovery | comms read pins (64d-i) | an archived delivery counts as pending forever |
| no-option refusal = preview, byte-inert (`SELECT *` before == after ∀ tables, F5 0 mutations) | 64d-ii | any write on the refusal path |
| atomicity: injected failure at statement k ⇒ nothing changed; positive control completes | 64d-ii | a partial disposition |
| per-table dispositions ∀ tables (a row in EACH) + receipts = stamped rows (RETURN-read) | 64d-ii | a table skipped; a pre-count served as a receipt |
| delete-obj refusals: task with surviving dependents; finding with surviving successors; keep with other members/others' rows — each with count + bounded ids + alternatives; CONTROL: without the dependent, deletes | 64d-ii | a phantom `blocked_by`; a dangling `supersedes`; an orphaned household |
| agents retired+archived under all three; capability denies under every token after `--change-owner` | 64d-ii | a transferred credential |
| memory delete through the backend + ledger tombstone; rebuild does not resurrect | 64d-ii | a resurrected row |
| `--change-owner` target validation × {missing, retired, archived, legacy NONE-owner, self-owned, inactive principal} → refused, nothing written; CONTROL: a valid target transfers both columns from one link | 64d-ii | a half-pair; a transfer to a corpse |
| claimant string byte-unchanged under transfer; `sender`/`created_by` unchanged | 64d-ii | a transfer that rewrites provenance |
| #404: principal-only store succeeds ∀ dispositions; no caller-side slice readiness remains (AST: `_dispatch` readies nothing for `delete`) | 64d-ii | a crash on a pre-keep store |
| exact-set `record<principal>` pin re-keyed to `DISPOSED-BY-CHOICE` ∀ six + keep | `test_principal_keys_schema.py` (patch) | an unclassed link |
| migrate re-run on a store with archived rows of every table: not refused, 0 stamped; am-26 dangling-sender count 0 after archive | 64d-ii | a precondition that reads a dangle as a half-pair |
| M — every mutation proof declared from `--collect-only`, diffed both ways | all | — |

---

## 9. Flags · DRY · discipline

- **FLAG (63c sidecar / lead, FYI):** #488 resolves as moot under OF-3 (§6) — I will annotate it after the
  lead confirms the directive is final; amendment 25 needs no change.
- **FLAG (packet 18 owner):** `MemoryLedger.tombstone` is a NEW ledger verb on a ledger being retired;
  if 18 lands before 64d-ii the tombstone is unnecessary and the pin ("rebuild does not resurrect")
  stays as the invariant over whatever replay exists then.
- **FLAG (packet 57 / #412):** agent hard-delete is explicitly NOT this verb's; 57 F-B decides it.
- **Packages considered:** none — every mechanism extends a shipped seam (`_governed_field_specs`,
  `lorerunes.pdp` IR, `read_filter`, `resolve_visible_keeps`, `KeepStore.set_keeper/delete_keep`,
  `PrincipalStore.delete`, `AuditStore.append_fragment`, `_verify_capability_owner`, `MemoryLedger`).
- **DRY ledger (candidates; the author owns names/rows):** `NotArchived` — EXTEND the IR (one node beside
  `ScopeEq`); `Resource.archived` — EXTEND (a field, `resource_from_row` derives it); `authorize_filter/
  read_filter(include_archived=)` — EXTEND (one keyword each); `AgentRegistry.admitted_owner_pair` —
  EXTEND `_verify_capability_owner` (split the pair path from the hash lookup; both callers share the
  four conditions); `Disposition`/`DeleteReceipt`/`PrincipalDeleteRequiresDispositionError`/
  `ChangeOwnerTargetError` — new typed carriers (no policy; `lore_search("delete receipt disposition")`
  → nothing to extend, HAND-ROLLED with that query as the receipt); `LocalMemoryBackend.delete_owned` +
  `MemoryLedger.tombstone` — EXTEND the `invalidate`/`retire` pair; `surreal_schema.governed_node_tables`
  — promote from the test substrate (carried from the kickoff); `unarchive` CLI — the `set_keeper`
  check-first idiom, REUSED.
- No code, no tests, no store touched; no pytest; writable set honoured (this doc only); registered in
  both sessions; heartbeat at delivery. No attribution trailer on the commit (the operator's standing rule
  + the brief override the session reminder).
