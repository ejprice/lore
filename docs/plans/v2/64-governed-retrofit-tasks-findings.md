# Packet 64 — Governed-tool retrofit: tasks + findings
size 0.30 →split (**PRE-SPLIT here**: 64a TASKS · 64b FINDINGS · 64c security-auditor over both — the
63b shape) · wave D · lead: Opus + Fable design sidecar · depends: 60, 61, 62, **63a (DONE 2026-09-03)**,
**63b (DONE 2026-09-12)** — NOT on 63c · DEPLOY: **no** (commit-only; packet 65 owns the joint cutover)

**Provenance:** packet file authored 2026-09-24 by `packetdoc-64` (plan-review session), at HEAD
`0eed242`, because the INDEX row had no file and KICKOFF step 2 could not run. Every code fact below was
read at that HEAD; anything not read is marked **UNVERIFIED**. Static per the packet protocol — scope
changes are an operator ruling recorded as an edit + a Log line.

## FIRST READS (cite, never re-transcribe)
1. `docs/reference/surrealdb-31-capabilities.md` — **MANDATORY** (store/schema/DDL/migration work):
   §1.1 OVERWRITE-vs-IF-NOT-EXISTS, §1.4 option<>-on-a-populated-table + the write-the-legacy-row-UNDER-
   THE-OLD-DDL fixture trap, §1.5 index build, §1.8 UNIQUE over option<>, §2 links do not auto-clean,
   §3 statement[0]-only validation, §4 traversal is never index-served, §5 hot-row mint law.
2. `docs/design/2026-08-28-packet63-retrofit-rulings.md` — **the governing design; 64 is a
   parametrisation of it.** §2.1 (LegacyMapping per table), §2.2–§2.3 (project-keep grandfather scope,
   backfill + fail-closed read tolerance), §2.5 (SET_SCOPE/SET_OWNER deferred TO 64), **§3 (the 63↔64
   boundary — the six seams + four pin families 64 CONSUMES UNCLONED, and §3.3's non-obligations)**,
   §4.1 (the exact DDL), §6 (the §9 security target — 64c re-aims it), §10.1 (`Resource.scope=None`),
   §10.2 (the per-verb adjudication home), §10.6 (`StoreHandle` — "64's ledgers the same"), §10.7-Z
   (principal-delete ORPHAN-TO-NONE — **its mechanism is 64's `set_owner`**), §10.9-A (F5 — "`task`/
   `finding` at 64"), §10.9-D (the compose-with-caller shape for `guarded_write`).
3. `docs/design/2026-08-21-lore-authorization-model.md` §4 (the 3-way write rule; "a Keep task is
   CLAIMABLE by any household member"; "any household member may resolve/supersede a Keep finding"),
   §4.3 (scope/owner/delete authority), §7 (migration), **§10-N (defaults: tasks→`principal-private`,
   findings→`project`)**.
4. 63b wave precedents (the split template), all under `docs/design/`:
   `2026-09-03-packet63b-design.md`, `2026-09-09-packet63b-ii-a-owner-resolution-ruling.md` (tokenless
   write DENIES; `requires_capability` flips per verb WITH its enforcing wave),
   `2026-09-11-packet63b-ii-b-drain-update-ruling.md` (the DD-3.c ASSERT DROP/KEEP discriminator — §7 /
   R19), and the INDEX Log 2026-09-04 → 2026-09-12.
5. `docs/design/2026-09-24-packet63c-amendment-2.md` §A1 — what "governed" means for a RELATION (the
   `to`/`briefed` precedent: no edge columns; reads ride the endpoint filter; writes attributed + F5).
6. `docs/plans/v2/DESIGN-LAW.md` §1 (honest served surfaces — every governed list render names its bound).

## Mission
Give the `task` and `finding` ledgers the same owner+scope governance 63 gave memory and comms:
server-stamped identity, every read through `governed.read_filter`, every write/delete/re-scope through
`governed.guarded_write` (the one PDP brain), and a dirty-store migration of the populated production
ledgers — while keeping the single-principal dogfooding fleet's shared task/finding behaviour
byte-unchanged until the 65 cutover.

## Ground truth at `0eed242` (read by `packetdoc-64`; the kickoff re-derives, per the entry-check law)
- **`task` identity columns** (`surreal_schema._TASK_FIELD_SPECS`): `owner option<string>` is the
  **CLAIMANT**, set by `TaskLedger._claim_fragment` from the caller-supplied `owner` arg and used as the
  claim-CAS gate (`WHERE … owner IS NONE`). There is **NO `created_by` column** — the creator is the
  string `provenance.created_by` inside the `object FLEXIBLE` blob (`TaskLedger._new_task_content`),
  with per-event `provenance.events[].actor` strings. ⚠ The 63 rulings §3.1 wording
  "`task.owner`/`created_by`" reads as two columns; only `owner` is a column, and it is not an author.
- **`finding` identity columns** (`_FINDING_FIELD_SPECS`): `created_by` is a **required string column
  carrying the trim-aware non-empty ASSERT**; `provenance.events[].actor` strings; `supersedes` is a real
  `option<record<finding>>` link; `number` is a global UNIQUE int minted from the `finding_counter` row.
- **So authz-model §7's "every row has a free-form string" premise HOLDS for task and finding** (it was
  false for memory/message) — the one case 63 never exercised. 63 already ruled its disposition:
  `LegacyMapping` **STRING-UNRESOLVABLE → UNOWNED-LEGACY** ("a bare name is never promoted",
  `governed.LegacyMapping` docstring + rulings §3.1).
- **The three tools take identity FROM THE CALLER today:** `AppContext.tasks(created_by=, actor=,
  owner=)`, `AppContext.findings(created_by=, actor=)`, `AppContext.claim_task(task_id, owner)`; none
  carries `capability=`. These are exactly F4's hostile-argument surface.
- **Dispatch tables:** `server._TASK_ACTIONS` (8 verbs) and `server._FINDING_ACTIONS` (10) are plain
  string TUPLES — unlike `_COMMS_ACTIONS`, whose specs carry `requires_capability`. The per-verb flip has
  no field to flip yet (FORK F7).
- **#420 legs:** 19 entries in `server._GOVERNED_VERBS_PENDING_ROUTING` (`_ROUTE_64_TASKS` ×8,
  `_ROUTE_64_FINDINGS` ×10, `_ROUTE_64_CLAIM` ×1). `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` holds
  `lore_tasks`/`lore_claim_task`/`lore_findings`. **`scripts/pending_contracts.yaml` carries NO 64 entry**
  — by design (rulings §10.2: that file is typecheck-bound and cannot carry a verb adjudication).
- **Migration verb:** `principals.migrate_governed` dispatches `memory`/`agent`/`message` and REFUSES any
  other table with a reason naming "task/finding land 64".
- **`blocks`** (`task->blocks->task`, ENFORCED, no edge fields) will JOIN the governed population by
  derivation (`_governed_contract.governed_populations`: relations whose IN or OUT is governed) the moment
  `_task_statements` calls `_governed_field_specs` — `TASK_TABLE` is a module-level literal, so this does
  not depend on amendment-2's ImportFrom leg.

## Sub-waves (pre-split; each: contract → adversary → build → cold audit → commit)
- **64a — TASKS, write + read** (`lore_tasks` ×8 + `lore_claim_task`, the `task` table + `blocks`).
  Named split trigger (the 63 §1.4 idiom): if 64a's contract prices >0.30, split at the ONLY sound seam —
  **64a-i = write side** (create/create_many/claim/transition/supersede + the migrate leg) · **64a-ii =
  read side** (query/get/blockers/rollup's task leg + served counts) — never mechanism without its pins.
- **64b — FINDINGS, write + read** (`lore_findings` ×10, the `finding` table). May run after 64a lands
  the shared deltas (FORK F6/F7, #407 extraction); disjoint table otherwise.
- **64c — dedicated SECURITY-AUDITOR over both** (report-only; the 63b-iii shape) — §SECURITY below.

## Scope IN
1. **DDL:** `_task_statements` / `_finding_statements` append `_governed_field_specs()` via
   `_define_field` (OVERWRITE) + `_governed_index_statements(table)` — the ONE emitter, never a
   re-declaration (rulings §3.1 row 4, §4.1). No ASSERT/DEFAULT on the new columns (§1.4).
2. **Identity server-stamped, never a caller arg:** `capability=` on the three tools (the ONE shared
   description constant, rulings §10.5 rider (i)), resolved via `AppContext._resolve_subject` →
   `governed.resolve_subject` (R-a.2: the ONE `Subject` constructor). The caller's `created_by`/`actor`/
   `owner` args stop moving identity (FORK F5 decides their fate).
3. **Every read through `read_filter`** (`query`, `get`, `blockers`, `chain_head`, rollup's task and
   finding legs, and every served COUNT — trust Leg 1: a count over the unfiltered table beside a
   filtered list is a false clear). Every render names its bound, DERIVED from the Subject.
4. **Every write/delete/re-scope through `guarded_write`** over the ledgers' own `StoreHandle`
   (rulings §10.6): claim, transition, supersede, acknowledge/resolve/wontfix/annotate, the `_many`
   batches (per-item, best-effort semantics preserved), and the create paths (a CREATE-OWNS-IT F5
   allowlist triple, evidence-backed, like memory's `remember`).
5. **Keep semantics** (authz §4): a `keep:`-scoped task is claimable/transitionable and a `keep:`-scoped
   finding resolvable/supersedable by ANY household member (the WRITE keep disjunct 61 already emits —
   nothing new in the PDP); hard DELETE stays owner+admin. Defaults per §10-N (tasks→`principal-
   private`, findings→`project` keep), taken as a PARAMETER of the substrate (rulings §3.3).
6. **`SET_SCOPE` + admin `SET_OWNER`** — 64 is their first consumer (rulings §2.5, #429), and §10.7-Z's
   principal-delete ORPHAN-TO-NONE mechanism rides `SET_OWNER` over the DERIVED governed-table set; the
   `PrincipalStore.delete` refuse-meanwhile pin-the-miss is deleted with it (sidecar confirms whether that
   lands in 64 or stays a named trigger — FORK F8).
7. **Dirty-store migration:** `migrate_governed` gains `task` + `finding` legs with the STRING-UNRESOLVABLE
   disposition (owner NONE/NONE, scope = the canonical project keep via `KeepStore.get_or_create_keyed`
   `key='project:lore'`), routed through `StoreHandle`, idempotent, single-principal precondition
   (`resolve_operator_principal` — the ONE ambiguity rule), refusing loud; `report-unmigrated` covers
   both. F1 seeds the legacy rows **UNDER THE OLD DDL**; F1's S2 leg restores the real prod dump into a
   `:18000` throwaway (NEVER `:18500`). A migration UPDATE is byte-inert on every non-governed column.
8. **DD-3.c ASSERT check per table** (the ii-b discriminator): for each ASSERT a whole-table migration
   UPDATE re-validates — `task.status` domain; `finding.status` domain + the five non-empty ASSERTs
   (`kind`/`subject`/`area`/`category`/`created_by`) — decide KEEP (its violation set ≡ the reader's own
   decode-rejection set) or DROP (it can fail a legacy row in a direction the reader tolerates), with a
   dirty-store leg constructing a violating legacy row. A legacy row that aborts the batch UPDATE is total
   migration denial — the ii-b `to.ack_note` class.
9. **Pin families parametrised, never cloned** (rulings §3.2 F1–F4 + §10.9-A F5): rows for `task`,
   `finding`, and `blocks` (F5's reach is the WHOLE derived tree per the #446 correction).
10. **#420 legs go GREEN per verb** as each wave routes them (`_GOVERNED_VERBS_ROUTED` grows, the pending
    dict shrinks); `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` loses `lore_tasks`/`lore_claim_task`/
    `lore_findings` at 64 close (R-a.5: a tool leaves when ALL its verbs route). `requires_capability`
    flips per verb WITH its enforcing wave, never ahead of it (ii-a ruling Q2).
11. **The owned findings** (next section).

## Findings owned (routed 2026-09-24 by `plan-review`; all `acknowledged`, verified by `get`)
| # | one line | disposition |
|---|---|---|
| 404 | `PrincipalStore.delete` hard-requires the `keep` table, docstring-guarded only | **IN if F8 lands orphaning** (delete gains a 2nd table dependency → the trigger fires; give the store method its own slice dependency or a structural pin); else KNOWN BOUND re-pinned |
| 406 | unwrapped store write (+ KeepStore read) paths leak raw `SurrealStoreError` | **IN for task/finding paths 64 opens** — reachability audit per path, set DERIVED by property; other stores stay the bound |
| 407 | CAS lost-race re-validation idiom cloned across `tasks.py` + `findings.py` | **IN — extract ONE helper** (64 opens both; its stated trigger). Must NOT route through `wrap_store_rejection` (that deletes the re-read — a regression) |
| 408 | `transitive_blockers` (+ likely `_reject_unknown_blockers`) wraps transport faults as domain errors | **IN** — 64 reworks these reads; derive the affected set by AST property, then rule preserve-vs-passthrough |
| 411 | `AuditStore.append` routing pin is text-equality | **IN (cheap)** — add the spy/effect pin; 64 is the first audit-trail-load-bearing consumer |
| 414 + 415 | `Resource.table` must be DERIVED from the row id, never a caller field | **IN — a 64 pin**: a `Resource` whose table disagrees with its row id is rejected; first consumers constructing Resources from ledger rows |
| 417 | PDP self-containment pin's `multi_disjunct` is a hand-list | **SIDECAR FORK** — close with the derived to_surql structural check only if 64 composes a NEW multi-disjunct node; else stays a pinned bound (reach STOP-rule) |
| 418 | empty `And(())`/`Or()` emits `"()"` | **IN** — the identity-element guard (`And()`→AllRows, `Or()`→NoRows); a named `lorerunes` touch in the builder writable set |
| 419 + 420 | Fork H-c per-verb routing coverage — the tasks/findings legs | **IN** — the 19 legs of §Ground truth |
| 427 | `_dispatch_verbs` map is a hidden hand-list | **IN** — derive the dispatch table from the tool (64 adds two multi-verb tools' verbs) or pin completeness |
| 428 | `@observes_routing` observes the marker, not the verb's effect | **IN** — the meta-pin confirms each decorated test exercises THAT tool/verb |
| 429 | `guarded_write` DELETE / SET_SCOPE branches unexercised | **IN** — 64 is their first consumer; both branches pinned with positive controls |

### Routed 2026-11-09 (finding slotting; INDEX row 64 carries the same list)
| # | one line | disposition |
|---|---|---|
| 487 | the #420 adjudication is stale for the 63b message family: send/drain/ack/await/story are enforced but still `_GOVERNED_VERBS_PENDING_ROUTING`; the pin checks routed⊆observed only | **IN** — Scope IN 10 gains the reverse leg (observed/enforced ⊆ routed); the comms legs are 63c's to green, 64 adds the pin |
| 488 | am-25 "scoped-but-ownerless row = half-applied, REFUSE" contradicts §10.7-Z orphaning (admin SET_OWNER→NONE on a scoped row): an idempotent migrate re-run refuses once orphaning lands | **FORK at kickoff, with F8** — orphaned rows need a disposition the half-pair precondition recognises |
| 515 | `governed.LegacyMapping` has zero instances; a table's legacy disposition exists only as docstring prose + its migrate leg's SQL | **IN (Scope IN 7)** — materialise `LEGACY_MAPPINGS` as the derivation's twin or delete the class; never both |
| 520 | comms' foreign-param `values` dict is a hand-list; `_comms_foreign_param_error` derives owners from `_COMMS_ACTIONS` unconditionally | **IN** — the F7 `requires_capability` derivation covers it; 64 adds two multi-verb tools and must not clone the hand-list |
| 484 | the 63c-i-a agent-migrate refusal renders STORED record ids raw in lore-adm (a newline-bearing id forges a row line) | **IN 64b (lore-adm migrate legs)** — route through `render_attributed`; hostile fixture required |
| 510 | a member's write on an INVISIBLE foreign memory row serves GovernedDenied naming the row — an existence oracle over uuid5-over-text ids | **64c** — the security-auditor frames it; the tasks/findings legs must not reproduce it (ids are not content-derived there — state that as a pin) |
| 529 / 530 | 63c-i-a residuals: `_set_columns` scanner narrows on a block comment; `unmigrated_rows` WARNING prefix is false for the task/finding legs | **IN 64b** — both sit in the migrate legs 64 extends |

## §DRY — the store-reader sweep (64b-ii; written 2026-11-09)
The 2026-10-01 INDEX Log routed "the `GROUP ALL` + foreign `_as_rows` sweep → 64b §DRY" and
amendment-37 §8.3/§10/§13 of packet 63c name the same step, but no packet-64 document carried it
until now. It is the read-side ONE-IMPLEMENTATION sweep and runs in **64b-ii** (the read side,
which already edits `findings.py`'s readers). Law: `~/.claude/CLAUDE.md` §One implementation and
this repo's §`lorerunes`; prove sharing by MUTATION (change the shared reader, every caller's pins
redden), never by routing.
1. **`GROUP ALL` count readers → ONE `governed.group_all_count`** (am-37 §8.3): `findings._extract_group_count`,
   `messages._extract_group_count`, `diff.py`, `tasks`, `store/surreal.py`, `index/surreal_manifest.py`, the
   `cascaded` audit count. STOP rule (am-37): a pin that expects `0` on a malformed count gets a DUAL re-key,
   never a silent pass.
2. **`_as_rows` → ONE tolerant row reader (`governed.rows_of`)** — **#594**: 13 production copies at `e1593d7`
   (4 distinct bodies: 9 identical in agents/briefs/diff/findings/index.surreal_manifest/memory.local/messages/
   store.surreal/tasks; 2 in floor_calibration.store + store.lease; `noun=`/`landed=` variants in principal_keys
   and principals). Measured by the AST instrument in `receipts/2026-11-09-finding-slotting/head-verify.md`.
3. **`_ensure_connection` disposition wraps → ONE seam** — **#512**: 17 copies at `e1593d7` (scout's `_connect`
   excepted) each wrap `open_surreal_connection → signin → bootstrap_session`, catch exactly
   `TxnContentionExhaustedError` + `_CONNECTION_ERRORS`, close, and translate to `SurrealConnectionError`.
   Packet 66 shared the FACTORY, not the wrap. Sites: agents, audit, briefs, diff, findings,
   floor_calibration/store, graph_surreal, index/snapshots, index/surreal_manifest, keeps, memory/local,
   messages, principal_keys, principals, store/lease, store/surreal, tasks. Routing is not sharing: the
   classification moves with the wrap.
4. **The guarded-append `TxnFragment` shell** — **#489**: findings and tasks each carry their own
   `LET … UPDATE … provenance.events += … + IF array::len == 0 THROW` shell; 58 extracts the TASK side first
   (its Scope IN), 64b-ii unifies across ledgers when the finding side is touched. Trigger stated in #489:
   "when the THIRD ledger needs one" — 64 IS that moment (tasks + findings + messages).
5. **`wrap_store_rejection`'s "could not <verb>" at the 20 non-mint callers** — **#543** (am-37 §14 Q1
   residual, operator scope): the message asserts non-landing for outcome-unknown faults. The mint fix
   (`_txn.proven_no_key`) is the prior art; sweep the callers the same way or pin the bound per caller.
   ⚠ Operator ruled this "operator scope" on 2026-10-05 — confirm at kickoff before building.
Bound: items 1–3 touch files outside the `finding` table (messages, diff, store, manifest, keeps …).
They ride 64b-ii because the shared reader lands in `governed`, which 64b-ii already edits; the
caller sweep is mechanical once the seam exists. If 64b-ii prices over 0.30 with them, split them to
**64d — store-reader DRY** rather than dropping them (the sizing law, not the scope law).

## FORKS for the Fable sidecar at kickoff (asked as questions; the operator rules MAJOR ones)
- **F1 — column mapping.** 63 ruled strings → UNOWNED-LEGACY. Does that hold for BOTH `provenance.
  created_by` (task) and `finding.created_by`? Is there ANY legacy string that is a verifiable LINK (none
  found at `0eed242`) — or is "exactly equals a registered agent name" (the pending-traffic footer's
  match) a guess wearing a mapping, per §2.1's `brief` reasoning? Recommendation to test: UNOWNED-LEGACY.
- **F2 — the CLAIMANT column.** `task.owner` is the claimant, not the governed owner. Do the governed
  `owner_principal`/`owner_agent` mean the CREATOR (row owner — DELETE/SET_SCOPE authority) while `owner`
  stays the claimant? Does the claimant become a server-stamped `record<agent>` (a `claimant_agent`
  link), and what happens to the legacy claimant STRING on migration (kept as display text? cleared?)?
  Every render that says "owner" to an agent must not now mean two things (trust Leg 1). Packet 57's
  `assignee` is OUT of scope but must not be pre-empted.
- **F3 — claim under Keep scope.** Is claim a `WRITE` on the task row (→ any household member of a keep
  task; owner-only on a `principal-private` task — i.e. under the §10-N default a task is claimable only
  by the creator's own principal)? Is that default right for a fleet whose leads create and agents claim?
  And how does the claim CAS (LET-resolved blockers + `owner IS NONE` guard, `TaskLedger._claim_fragment`)
  ride `guarded_write`, whose surface is a single `set_fragment` — extend `guarded_write` with the §10.9-D
  compose-with-caller shape, never a second guarded path?
- **F4 — supersede/resolve by a household member vs the owner.** A supersede mints a NEW row owned by the
  superseder: what scope does the successor inherit (the predecessor's keep, or the superseder's default)?
  May a household member resolve a keep finding it did not report (authz §4 says yes) — and may it
  `annotate`? Is `wontfix` a WRITE or a soft-DELETE (owner+admin only)?
- **F5 — the caller identity args.** `created_by`/`actor`/`owner` are REQUIRED today on several verbs.
  Retire them (a served-surface break every fleet brief must absorb at the 65 cutover), accept-and-ignore
  them (a silent lie — forbidden), or keep them as a non-identity display label? F4's fuzz pins the effect
  either way.
- **F6 — `blocks` as a governed relation.** It joins by derivation (§Ground truth); per the `to`/`briefed`
  precedent it gets no edge columns and its reads ride the task filter. Decide: may a task be `blocked_by`
  a task the creator cannot READ (the `blockers` walk and the claim gate then read an invisible row's
  status — an existence/status oracle)? Is a cross-scope `blocked_by` refused at create?
- **F7 — `requires_capability` home for tuple dispatch tables.** Reshape `_TASK_ACTIONS`/
  `_FINDING_ACTIONS` into spec objects like `_COMMS_ACTIONS` (one mechanism), or a derived sibling set?
- **F8 — does §10.7-Z's orphaning land in 64** (it names 64's `set_owner` as the mechanism), and does it
  also discharge #404?
- **F9 — oracles in the finding ledger.** The global monotonic `number` (and `chain_head`'s walk over
  `supersedes` links into rows the caller cannot read) reveal invisible findings' existence/count. Accept
  as a named bound (single-principal fleet) or close before 65?

## ENTRY CHECK (relative facts only — any contradiction is a STOP)
1. `git merge-base --is-ancestor` holds for 63a's close (`bb31a86`) and 63b-iii's close (INDEX Log
   2026-09-12; 63b-ii-b HEAD `5d61f9e`) against HEAD.
2. The six 63a seams resolve by symbol (`lore_verify`): `governed.resolve_subject`, `governed.read_filter`,
   `governed.guarded_write`, `surreal_schema._governed_field_specs` + `_governed_index_statements`,
   `principals.migrate_governed` + `governed.LegacyMapping` (STRING-UNRESOLVABLE named),
   `store._txn.StoreHandle`; and the test substrate `_governed_contract` (`observes_routing`,
   `governed_populations`, `governed_table_raw_mutation_sites_in_tree`).
3. `partition_tools_by_population` classifies `lore_tasks`/`lore_claim_task`/`lore_findings` GOVERNED
   (`_REVIEWED_GOVERNED_TOOLS`), and their 19 legs are in `_GOVERNED_VERBS_PENDING_ROUTING` with non-blank
   triggers.
4. **The shared tree is quiescent for 64's files:** 63c is in flight in the SAME checkout (NO WORKTREES
   law) and edits `_governed_contract.py`, `server.py`, and the governed exact-set pins that 64 also
   grows. 64 does not start until the 63c wave touching those files is COMMITTED — or the operator rules
   the ordering (FORK F0, a scheduling fork, operator's).
5. Suite green at HEAD: full suite ALONE with `-n 12` (never `-n auto` — #466; check `ps`/`ListAgents`
   for a peer run first); `scripts/pending_contract_gate.py --currency` 0 RED_ORPHANED.
6. Probe the coverage premises (INDEX: an exclusion resting on "X is covered" is an entry check): the
   probe re-runs `scripts/probe_read_filter_63.py`'s P1/P2/C+ over the REAL `task`/`finding` DDL
   (plain tables, no HNSW — P1's option<>-over-NONE delta re-confirmed on each) and commits the extension.

## Scope OUT (surface to the operator if encountered)
- Packet 65's cutover/deploy, the fleet re-brief, and the `:18500` reachability reads.
- Packet 57's `assign`/`assignee`/`reap` and the owner↔liveness surface.
- Packet 58's supersede re-anchor of dependents (#356) — but 64's supersede must not make it harder.
- 63c's `brief`/`agent` roster governance and #467.

## SECURITY (64c target — the rulings §6 frame, re-aimed)
Over the wire on the real tables: cross-principal read isolation ∀ read verbs of both tools (F3 world:
≥2 principals × ≥2 agents, disjoint households, admin AllRows control); served count == served set
(query/rollup/blockers); anti-injection ∀ write verbs (no `created_by`/`actor`/`owner`/`scope=` moves the
stamp or widens scope); claim/resolve by a NON-household principal on a keep row DENIES while a household
member succeeds; the migration cannot widen visibility (single-principal precondition attacked); no
TOCTOU on `guarded_write` (the injected-handle re-scope leg); the F6/F9 oracles adjudicated.

## EXIT
Per sub-wave: scoped pytest + full suite ALONE `-n 12` + `scripts/typecheck.sh` + `uv run ruff check .` +
`pending_contract_gate.py --currency` (0 RED_ORPHANED) → cold REFUTE audit (Opus; contract-blind diff
pass on the delete/replace hunks — removed-behaviour inventory incl. the retired caller-identity args) →
commit. At close: 64c security-auditor GO → findings resolved/annotated with notes → INDEX row flipped +
≤5-line Log → reports `git mv` to `docs/plans/v2/receipts/<date>-packet64/`.

**Pipeline per wave:** contract (Opus) → **contract-adversary (MANDATORY)** + sidecar fidelity read →
build (Opus) → cold audit (Opus REFUTE) → commit. ONE security-auditor at 64 close.
