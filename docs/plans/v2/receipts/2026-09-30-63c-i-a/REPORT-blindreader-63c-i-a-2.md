# REPORT — blindreader-63c-i-a-2 (contract-blind diff reader, 63c-i-a fix wave)

brief-base v16 read · brief project v7 read
**State:** done (report-only; nothing edited but this file).
**Deviations:** none. HEAD moved `5a43aeb`→`f867f71` during the read (docs/test commits only; the six touched files byte-identical — diff md5 `b23f3e43…` re-derived at `f867f71`).
**Packages considered:** none — no mechanism specified (grader). **Odoo-20 portability:** n/a — no Odoo seam touched. **Reuse ledger:** none (no new symbols).
**Graded:** `5a43aeb` + working-tree patch md5 `b23f3e43416b9d0931dff1635ad53f85` · HEAD-at-report: `f867f71` · DIFFERENT (8 behind): no graded symbol moved.
**Headline:** 1 BLOCKER · 2 MAJOR · 4 MINOR findings (F-4–F-7) + 2 MINOR notes (N-2, N-5) · F-8 + remaining N-notes are NOTE. (§3, §4, §5)
- **F-1 BLOCKER** `server.py:_comms_register` race compensation: "created by this call" ≠ "used only by this call". On every principal-bearing trigger of the branch, the concurrent winner has FOUND and is SCOPED to the keep this call minted; the delete strands it (keep ids are fresh ULIDs, so there is no re-attach). The race pin only constructs an ownerless winner, the one value where the delete is harmless. §3 F-1, §5.
- **F-2 MAJOR** preflight-before-gate: a FOREIGN principal now learns an existing agent row's existence/retirement/role/spawned_by, where SF-63-1 used to speak first (existence-leak stance). **Decision needed (operator):** accept, or gate read-only before preflight. §3 F-2.
- **F-3 MAJOR** `backfilled` measured on the message leg only; agent (now self-guarding) and memory legs still serve the pre-count, which contradicts the new `MigrateGovernedResult` ∀ docstring and ruling am-27 FORK-1 (commit subject `40c188d`). §3 F-3.
- MINOR: F-4 fail-open on `INFO FOR DB` shape · F-5 "LEFT BEHIND" served on KeepNotFoundError · F-6 "not measured" reason false for agent/message · F-7 sender-state race in message UPDATE · N-2/N-5 served prose.
**Decisions needed:** F-1 remedy (guarded delete vs no compensation, since only same-principal/tokenless winners can race); F-2 precedence.
**Receipts:** §1 inventory (36 rows) · §2 input-fate · §4 served English E1–E16 + N-6 pasted instrument · §5 coverage.


## 0. Capability check + provenance (2026-09-26)

- Brief demanded: read the diff + HEAD bodies, write the removed-behaviour inventory BEFORE any test,
  input-fate analysis, served-English audit, then skim tests; no pytest; awk not grep. All satisfiable.
- Diff under review: `builder-63c-i-a-fix.patch` md5 `b23f3e43416b9d0931dff1635ad53f85` ==
  `git diff HEAD -- loremaster/loremaster/{agents,governed,keeps,principals,server}.py
  lorerunes/lorerunes/identifiers.py` md5 (identical, measured 2026-09-26). Base HEAD `5a43aeb`.
- Withheld files honoured: no REPORT-contract/adversary/builder/coldaudit/lead/predecessor and no
  `docs/design/*packet63c*` opened. (A docstring in the diff CITES `REPORT-builder-63c-i-a-fix.md §P`;
  not opened.)
- Tools: lore comms registered; grep hook-blocked → awk/sed used for every textual search (non-symbol
  seams: served strings, SQL text) — said out loud per the dogfood protocol.
- One non-pytest probe run (pydantic flag behaviour, §4 N-6): `uv run python -c …`, `loremaster.__file__`
  = `/home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py` (the real tree, read-only use).

## 1. Removed-behaviour inventory (written BEFORE reading any test)

Legend: PRESERVED · CHANGED (deliberate per the code's own comment) · CHANGED-SILENT (no comment
acknowledges it) · DROPPED · NEW.

| # | Old behaviour (HEAD `5a43aeb`) | File:symbol (new home) | Fate |
|---|---|---|---|
| A1 | `register`: provenance-pair (A3) refusal before any store I/O | `agents.py:AgentRegistry.preflight` (called by `register` with `session_keep_id`) | PRESERVED |
| A2 | `register`: illegal name/session / blank role refused before I/O | `preflight` → `_refuse_an_invalid_identity` | PRESERVED (order: pair → identity → read) |
| A3 | illegal-identity message carried an English gloss "(lowercase letters, digits, '_' or '-', starting with a letter or digit)" | `_refuse_an_invalid_identity` | CHANGED (gloss dropped; pattern alone states the rule incl. the 64 cap) |
| A4 | ONE `_select_row` per register | `register` via `preflight` | PRESERVED inside `register`; but the tool path now reads the row TWICE (handler preflight + register's preflight) — CHANGED-SILENT, cost only (N-1) |
| A5 | retired → `RetiredAgentError` (text) | `preflight` | PRESERVED byte-identical |
| A6 | role conflict → `AgentIdentityConflictError` (text) | `preflight` | PRESERVED byte-identical |
| A7 | concrete `spawned_by` conflict (both non-None, differ) | `preflight` | PRESERVED byte-identical |
| A8 | CREATE path (secret mint, content, read-back, vanished error) | `register` | PRESERVED (untouched) |
| A9 | re-register UPDATE fed from `existing` (= `_row_to_agent(existing_row)`) | `register` | PRESERVED (`existing` now comes from `preflight`, same conversion, same read) |
| S1 | handler order: resolve principal → mint session keep → SF-63-1 gate → `register` | `server.py:AppContext._comms_register` | CHANGED: resolve → **preflight** → mint → gate → register |
| S2 | a principal DENIED by SF-63-1 learned only the session + add-household remedy, never anything about the agent row (the gate ran before any registry read) | `_comms_register` | **CHANGED-SILENT** — preflight's retired/role/spawned_by refusals now fire BEFORE the gate (F-2) |
| S3 | a register the registry refused (blank role; conflict) still minted the session keep first (the SF-63-1 poison) | `_comms_register` | CHANGED (the fix): refused-before-mint for every write-free refusal |
| S4 | no compensation of any kind after `register` failed | `_comms_register` `except _AgentRegistryError` | NEW: created-only `delete_keep` + appended-line on failed delete |
| S5 | `principal_bare` computed only when a principal exists | `_comms_register` | PRESERVED (same value; now computed eagerly, `None` when tokenless) |
| S6 | `keep_store is None` → `GovernedDenied` (pragma no-cover) | `_comms_register` | PRESERVED |
| S7 | non-registry exceptions from `register` (store rejection e.g. duplicate CREATE, transport) propagate, keep stays | `_comms_register` | PRESERVED (no compensation for them — N-3) |
| S8 | charset refusal prose "`{label} does not match {pattern}`" | `server.py:AppContext._validate_comms_charset` | CHANGED ("must match") |
| K1 | `get_or_create_keyed` returns found / CAS-winner / created keep, indistinguishable | `keeps.py:KeepStore.get_or_create_keyed` | PRESERVED + NEW non-field `minted_by_this_call` attribute on the created leg only |
| G1 | `MigrateGovernedResult.scanned/already_migrated: int` (0 on refusals) | `governed.py:MigrateGovernedResult` | CHANGED (`int | None`; `None` on every refusal) |
| M1 | `migrate_governed`: `memory`/`agent`/`message` dispatched straight to their legs; anything else refused "not supported at packet 63b" with zero I/O | `principals.py:migrate_governed` | CHANGED: invalid → zero-I/O refusal (preserved); `brief` → store read + "not yet" refusal (NEW); every valid table first passes `_verb_level_refusal` (NEW) |
| M2 | `memory` leg never looked at the `agent` table | `migrate_governed` | CHANGED (by ruling D-1): memory now refused on an owned-unscoped / ownerless-scoped agent |
| M3 | memory/agent/message "cannot resolve THE operator principal …" prose, measured counts | `_operator_unresolved` | PRESERVED byte-identical for the three purposes ("to keep the project keep" ×2, "to own the fleet's agents"); counts 0→`None` |
| M4 | agent leg: operator resolved FIRST; then §2.1 guard `SELECT VALUE id … scope IS NONE AND owner_principal IS NOT NONE` | `_agent_migration_preconditions` + `_verb_level_refusal` | CHANGED: guard hoisted to the verb and runs BEFORE operator resolution; unresolved operator + owned rows now yields a combined refusal (improvement) |
| M5 | agent §2.1 refusal served MEASURED `scanned=unmigrated+already`, `already_migrated=already` | `_refused` | CHANGED → `None`/`None`. Note `unscoped_count` (= the leg's `unmigrated`) IS measured at the verb and discarded (F-6) |
| M6 | agent leg: an ownerless-but-scoped agent was silently counted as `already_migrated` and left ownerless | `_verb_level_refusal` | CHANGED: now refused (half-applied store) |
| M7 | agent UPDATE `WHERE scope IS NONE` | `_migrate_agent_owner` | CHANGED: `… AND owner_principal IS NONE` (self-guard) |
| M8 | agent `backfilled = unmigrated` (pre-count) | `_migrate_agent_owner` | PRESERVED — but now CONTRADICTS the new self-guard and the new `MigrateGovernedResult` docstring (F-3) |
| M9 | message leg agent-first guard keyed `agent.owner_principal IS NONE` count; prose "NONE-owner agent(s)" | `_migrate_message_owner` | CHANGED → `scope IS NONE` count ("un-migrated (NONE-scope) agent(s)"); equivalent in effect because the verb guard catches the owner/scope-disagreeing rows first |
| M10 | message leg: a legacy message with a DANGLING sender was stamped `owner_agent=<dangling link>`, `owner_principal=NONE`, `scope=project` (manufactured a scoped-ownerless row) | `_message_leg_refusal` | CHANGED: refused (all rows, byte-inert) |
| M11 | message leg: an owned-but-unscoped message was silently skipped (UPDATE keyed `owner_principal IS NONE`) and left invisible | `_message_leg_refusal` | CHANGED: refused |
| M12 | message leg: a scoped-but-ownerless message was RE-STAMPED — its existing `scope` OVERWRITTEN to the project keep | `_message_leg_refusal` + UPDATE self-guard | CHANGED: refused; and the UPDATE can no longer touch it |
| M13 | message counts owner-keyed; `backfilled = unmigrated` (pre-count) | `_migrate_message_owner` | CHANGED: scope-keyed; `backfilled = len(UPDATE result)` (measured); a non-list UPDATE result now raises `TypeError` AFTER the write committed (N-4) |
| M14 | `_owner_count` helper | — | DROPPED (no remaining prod caller; awk sweep of tracked non-test `.py`, 2026-09-26) |
| M15 | `_REFUSAL_ID_SAMPLE_SIZE = 10`, sample rendered `sorted(str(id))` | `_id_sample` / `_by_id` | PRESERVED value; ids now `sanitise_line`d (NEW); sort key unchanged (`str`) |
| I1 | `is_legal_identifier` = `AGENT_NAME_PATTERN.fullmatch` | `lorerunes/identifiers.py` | PRESERVED (only docstring/comment changed) |
| I2 | module docstring taught "load-bearing injection guard … inline it as a literal into live WHERE clauses" | `identifiers.py`, `agents.py` comment | CHANGED (corrected threat model; see §4 N-8 for a surviving stale sibling) |

## 2. Input-fate analysis

### 2a. Agent register (tool `lore_comms register` → `_comms_register` → registry)

Tool-seam charset (`_validate_comms_charsets`, server) runs before the handler for `agent`/`session`,
so illegal/blank name|session never reach the handler on the tool path; the registry's own identity
check still governs direct `AgentRegistry.register` callers.

| Input class | Before (HEAD) | After (patch) | Silent change? |
|---|---|---|---|
| legal role, first register, principal | mint keep → gate → CREATE | preflight(read) → mint → gate → register(preflight read again) → CREATE | extra read only |
| blank / whitespace role, principal | **keep minted**, then `InvalidAgentIdentityError` (keep left: SF-63-1 poison) | refused in preflight, no mint | intended fix |
| blank role, tokenless | refused, nothing minted | same | no |
| illegal name/session (direct registry caller) | refused pre-I/O | same (preflight) | no |
| retired / role-conflict / spawned_by-conflict, **principal whose session another principal keeps** | `GovernedDenied` (session + remedy only) | registry refusal naming role / spawned_by / retirement of the existing row | **YES — F-2** |
| same, own session | keep found → registry refusal | preflight refusal, no mint | no (improved) |
| existing keep (found) | returned, no flag | returned, flag False | no |
| created keep | returned | returned, flag True | no |
| concurrent winner (CAS re-read) | returned | returned, flag False | no |
| concurrent conflicting register lands between preflight and register (same principal) | refusal; keep stays (used by winner) | refusal; **keep this call minted is DELETED although the concurrent winner is scoped to it** | **YES — F-1 BLOCKER** |
| concurrent duplicate (same role) register, CREATE collides | `TxnDomainRejectionError` from `_query`, keep stays | same (not an `AgentRegistryError` → no compensation) | no |
| failed compensation delete | n/a | refusal text + one appended line naming the keep + remedy | new; one false branch (F-5) |
| transport fault / gate-read fault after mint | keep left, silent | keep left, silent | no (N-3) |

### 2b. `migrate_governed` per `--table`

| Input class | agent | memory | message | brief | invalid name |
|---|---|---|---|---|---|
| clean store | HEAD: backfill. NOW: same (+ precondition reads) | same | same | HEAD: refused "not supported" no I/O. NOW: store read, refused "not yet … preconditions passed" | zero I/O both; prose changed |
| owned-but-unscoped agent (multi-principal / E3) | HEAD: leg refusal, measured counts. NOW: verb refusal, `None` counts, owner diagnosis | HEAD: **migrated**. NOW: refused | HEAD: refused only if some agent owner NONE … owned-unscoped agents are NOT NONE-owner → HEAD proceeded if every agent had an owner. NOW: refused | NOW refused | n/a |
| ownerless-but-scoped agent | HEAD: counted `already`, left ownerless. NOW: refused | HEAD migrated; NOW refused | HEAD: refused (NONE-owner count >0). NOW: refused (verb) | NOW refused | n/a |
| single- vs multi-principal store, operator unresolvable | HEAD: operator refusal first (agent). NOW: combined refusal, owners UNCLASSIFIED | NOW: combined verb refusal if agent facts present, else leg refusal | same | same | n/a |
| message owned-but-unscoped | — | — | HEAD: silently skipped. NOW: refused | — | — |
| message scoped-but-ownerless | — | — | HEAD: **scope overwritten** to project. NOW: refused | — | — |
| message dangling sender | — | — | HEAD: stamped owner NONE + scope project (manufactured half-pair). NOW: refused | — | — |
| message both at once (dangling + half-pairs) | — | — | NOW: ONE refusal naming all three lists in fixed order | — | — |
| store with no `agent` table | HEAD: `_scope_count` on undefined table; NOW: preconditions skip agent reads (gated on `INFO FOR DB`) then same leg | same | NOW: `unscoped_count=0` → ORDER guard passes; every legacy message's sender dangles → caught by the dangling refusal | NOW: passes → "not yet" | — |
| `INFO FOR DB` returns a non-dict (SDK shape change) | NOW: `defined={}` → **every agent fact reads empty → verb guard silently disabled** (F-4) | same | same | same | — |
| hostile stored ids (newline / control chars) | NOW: `sanitise_line` on every id, owner, sender | — | same | — | table name `sanitise_line(...)!r` |
| hostile ids with `, ` inside the id text | NOW: renders as extra list items; the stated `of N` count still discriminates (N-7) | — | same | — | — |

### 2c. Identifier predicate
`is_legal_identifier` body unchanged (`fullmatch`). Every input class (legal, trailing-newline twin,
65-char, uppercase, blank) has an identical fate before and after. Only the WHY prose moved.

## 3. Findings

### F-1 — BLOCKER — compensation deletes a keep the concurrent winner is already scoped to
`server.py:AppContext._comms_register` (`except _AgentRegistryError` branch) + `keeps.py:minted_by_this_call`.

The compensation's safety argument is "delete iff THIS call CREATED the keep — never one it found
(that keep belongs to another registration)". Created ≠ exclusively used. Walk the only race the
branch exists for (a conflicting register landing between `preflight` and `register`):

1. X (`agent=a, session=s, role=builder`, principal P) preflights — no row.
2. X' (`agent=a, session=s, role=auditor`, principal P) preflights — no row.
3. X mints `session:s` keep K (`minted_by_this_call=True`).
4. X' `get_or_create_keyed` FINDS K; SF-63-1 gate passes (P keeps it); X' `register` CREATEs the
   agent row with `scope = keep:K` (CREATE-only stamp, never re-stamped).
5. X `register` → preflight reads X''s row → role differs → `AgentIdentityConflictError`.
6. X deletes K. `delete_keep` cascades K's `member_of` edges and — by its own docstring's
   "63/64 FORWARD-BOUNDARY" warning — ORPHANS every row scoped `keep:K`.

Result: X' (the registration that WON) holds `scope=keep:K` pointing at nothing. Keep ids are a fresh
`ULID()` per mint (`get_or_create_keyed`), so the next register into `s` mints K2 ≠ K and X' is
permanently stranded in a dead scope; any OTHER agent P registered into `s` in the same window (step
3→6) is stranded too.

Why this is the common case, not a corner: the conflicting winner must pass the SF-63-1 gate on the
keep X minted, and a freshly minted keep's only household member is its keeper — so a
principal-bearing winner is necessarily the SAME principal, and it necessarily FOUND K (if it had
minted first, X would have found it and `minted` would be False). The only winner that does not adopt
K is a TOKENLESS one. So on every principal-bearing trigger of this branch, the delete strands the
winner. This is CLAUDE.md's DD-3.c / quantifier shape: a safety property derived over "keeps I found"
stated over "keeps I did not create".

Status: derived by reading, not executed (brief forbids pytest; I built no store probe). Confidence
HIGH on the code path (every step cites code read at `5a43aeb`+patch). Construction recipe for a
pin: two handler calls on one principal/session/name with differing roles, interleaved at the
`get_or_create_keyed` / `register` boundary (e.g. an injected pause after step 3); assert the winner's
`scope` resolves to a live keep and the session keep still exists.
Candidate remedies (design, not mine to pick): delete only if no row is scoped to K (guarded DELETE,
`… WHERE count(<scoped rows>) = 0`, in one txn) · or do not delete, and let the session keep persist
(it is P's own keep; the SF-63-1 harm only exists for a DIFFERENT principal, who could not have raced
here anyway — which suggests the compensation may be unneeded for the race it targets).

### F-2 — MAJOR (operator ruling needed) — preflight-before-gate leaks agent-row facts past SF-63-1
`server.py:AppContext._comms_register`, `agents.py:AgentRegistry.preflight`.

HEAD: a principal registering into a session ANOTHER principal keeps was denied by SF-63-1 before any
registry read; the denial names only the session and the remedy (63-rulings §6 existence-leak stance,
quoted in the handler's own comment). Now `preflight` runs first, so the same foreign principal
probing `(session, name)` receives, for an existing row: `RetiredAgentError` ("agent 'x' is retired")
or `AgentIdentityConflictError` naming the existing `role` and `spawned_by` values. That discloses the
existence, retirement, role and spawner of agents in a session the caller cannot join.
Bound on severity: a TOKENLESS register (reading α) never passes the gate at all, so on a deployment
whose transport admits tokenless calls the same facts were already reachable; on a token-required
transport this is a NEW disclosure. I did not establish which deployments admit tokenless calls.
The docstring's ORDER paragraph states the new order but not this precedence consequence — the change
is unacknowledged. Possible shape keeping both properties: a read-only gate (`get_by_key` + visibility,
no mint) before `preflight`, the mint after.

### F-3 — MAJOR — `backfilled` is served as MEASURED by prose but is the pre-count on two of three legs
`governed.py:MigrateGovernedResult` docstring ("On a proceeding run ``backfilled`` is the number of rows
the backfill actually stamped"), `principals.py:_migrate_agent_owner`, `_migrate_memory_scope`.

Only the message leg uses `_rows_stamped`. The agent leg still returns `backfilled=unmigrated`
(the `scope IS NONE` pre-count) while its UPDATE gained `AND owner_principal IS NONE` precisely so
that a row turning owned-but-unscoped between read and write is NOT stamped — i.e. the self-guard's
own firing case is exactly where the served count over-claims. Memory leg likewise pre-count. The
CLI prints `backfilled=` to the operator. ∀-claim in the dataclass docstring, true for 1 of 3 legs.

### F-4 — MINOR — the verb guard fails OPEN on an unexpected `INFO FOR DB` shape
`principals.py:_agent_migration_preconditions`: `defined = info.get("tables", {}) if isinstance(info,
dict) else {}`. Any non-dict answer (or a dict without `tables`) makes every agent/message fact read
empty, so `_verb_level_refusal` and `_message_leg_refusal` return `None` and the legs proceed —
the agent UPDATE self-guards, but `message` would then stamp messages from unmigrated/unowned senders
(owner NONE, scope project = the half-pair the refusal exists to prevent). HEAD had no such gate (it
queried the tables directly). Forgery-pin leg "wrong-shape" of the new dependency; a raise on a
non-dict/keyless answer (like `_rows_stamped` does) would close it. (`_governed_select` has the same
tolerance for non-list rows — same class.)

### F-5 — MINOR — failed-delete line can be false: "LEFT BEHIND" when the keep is already gone
`server.py:_comms_register` `except Exception as delete_error`. `delete_keep` raises
`KeepNotFoundError` when the keep no longer exists (e.g. an admin or another compensator deleted it).
That is caught by the same `except Exception`, and the caller is told the keep "is LEFT BEHIND and
would deny the next principal's register … remedy: `lore-adm delete-keep --keep <id>`" — whose remedy
would itself fail "no keep … exists". Served English not derived from the error class. (The remedy verb
and `--keep` flag DO exist: `principals.py` parser `delete-keep`, verified.)

### F-6 — MINOR — "not measured" prose over-claims on the agent and message refusals
`principals.py:_refused` / `MigrateGovernedResult` docstring: "every refusal returns before any scan of
the target table". False for `--table agent` (the verb ran `_scope_count(agent, none=True)` and the
half-pair SELECT over `agent`) and for `--table message` refusals (the dangling / half-pair SELECTs
scanned `message` before the ORDER refusal). Serving `None` is a legitimate choice, but the stated
reason is not what the code does, and M5: HEAD served a measured `scanned/already_migrated` on the
agent §2.1 refusal that the new code measures half of and discards. Docstring, not served — MINOR.

### F-7 — MINOR — message backfill does not self-guard on the SENDER's state (race)
`principals.py:_migrate_message_owner` UPDATE `WHERE scope IS NONE AND owner_principal IS NONE`
self-guards the target row but not `sender.owner_principal IS NOT NONE` / `sender.id IS NOT NONE`.
A tokenless register (ownerless, unscoped agent) + a send landing between the precondition read and
the UPDATE yields a message stamped owner NONE + scope project — the scoped-ownerless half-pair the
leg refuses. Same for a sender deleted in the window. Old code had the same window; the new code
added the target-side guard and stopped there. Cutover is presumably quiesced; ledger-worthy.

### F-8 — NOTE — stale charset-ASSERT prose survives the threat-model correction
`inbox_awaiter.py:InboxAwaiter.live_select_statement` docstring: "The id is a ``uuid5`` hash of
charset-ASSERTed ``name``/``session``" — the store ASSERT was DROPPED at 63c-i-a (the corrected
`identifiers.py` docstring says so). Outside the diff; the rename/reshape law says prose surfaces are
where these hide. Also `principals.py` CLI `--table` help strings still read "(63a supports: memory)"
for both `migrate-governed` and `report-unmigrated` — stale beside the new supported set.

## 4. Served English — every string the new code serves

| # | Surface (file:symbol) | Text (abridged) | Matches behaviour? | Numbers |
|---|---|---|---|---|
| E1 | `agents.py:_refuse_an_invalid_identity` | "agent {field} must match {pattern}; nothing was written — register again with a legal {field}. The rejected value was:" + fence | YES (pre-write refusal) | pattern derived from `AGENT_NAME_PATTERN` |
| E2 | `server.py:_validate_comms_charset` | "{label} must match {pattern} — names must stay in the safe charset." | YES | derived |
| E3 | `_comms_register` failed-delete line | "ALSO: this refused register minted session keep {id} and could not delete it — it is LEFT BEHIND and would deny the next principal's register into this session; remedy: `lore-adm delete-keep --keep {id}`" | PARTLY: false on `KeepNotFoundError` (F-5); "would deny" true only for a DIFFERENT principal; the named remedy strands any agent already scoped to the keep (F-1's mechanism) — N-2 | id store-minted |
| E4 | `principals.py:_not_supported(store_was_read=False)` | "does not support table 'x' — the governed tables are `memory`, `agent`, `message` and `brief` (… 63c-ii; task/finding land at 64); nothing was read or written" | YES (zero I/O, verified by reading) | table names from constants |
| E5 | `_not_supported(store_was_read=True)` | "does not yet migrate `brief` … the store's governed-table preconditions were read and passed, and nothing was written" | YES | — |
| E6 | `_operator_unresolved` | "cannot resolve THE operator principal {purpose} (n principals, m admins) — provision a single operator principal (or a single admin) before migrating" | YES | n, m measured at call time |
| E7 | `_owned_unscoped_part` (operator known) | "K of them are owned by the operator — registered by a pkt-62–63b image; see amendment-1 E3." | NO — provenance ASSERTED, not derived: the code knows only owner == operator (N-5) | K derived |
| E8 | `_owned_unscoped_part` (operator unknown) | "their owners are UNCLASSIFIED — with the operator unresolved, any of them may BE the operator." | YES | derived |
| E9 | `_verb_level_refusal` tail | "Adjudicate these rows by hand before migrating ANY governed table; no row was stamped" | YES (returns before any write) | — |
| E10 | ownerless-scoped agent part | "N agent row(s) carry a scope but no owner — a half-applied store …" | YES | derived |
| E11 | `_migrate_message_owner` ORDER | "({n} un-migrated (NONE-scope) agent(s) remain) … run migrate-governed for `agent` first" | YES | derived |
| E12 | `_message_leg_refusal` dangling | "N legacy message(s) name a dangling sender — their `sender` link resolves to no agent row" | MOSTLY: predicate is `sender.id IS NONE` (no row of ANY table; a NONE `sender` also lands here, rendered "(sender None)") | derived |
| E13 | message half-pairs | "N message row(s) carry an owner but no scope — a half-applied store …" | YES — checked: governed `send` stamps owner+scope in one CONTENT since `eafb8fd` and refuses without a session keep, so no legitimate owner-only message population exists (premise probed, no finding) | derived |
| E14 | `_id_sample` | "First {shown} of {count} ids shown: …" | YES; shown is `len(shown)`, never the constant | derived |
| E15 | `_rows_stamped` TypeError | "a governed backfill UPDATE returned X, not the list of rows it stamped" | YES, but raised AFTER the write committed; `lore-adm`'s except tuple lacks `TypeError` → traceback (N-4) | — |
| E16 | CLI help `--table` (unchanged) | "(63a supports: memory)" | NO — stale (F-8) | — |

### Notes (NOTE severity unless stated)
- **N-1** Tool path reads the agent row twice (handler `preflight`, then `register`'s own). Cost only; the
  two reads can disagree under the very race F-1 describes — that disagreement is what triggers the
  compensation.
- **N-2 (MINOR)** E3's remedy `lore-adm delete-keep` cascades `member_of` and orphans scoped rows (the
  `delete_keep` docstring's own 63/64 FORWARD-BOUNDARY warning). Recommending it unconditionally in a
  served refusal propagates F-1 to the operator.
- **N-3** Only `AgentRegistryError` triggers compensation. A keep minted by this call is left silently on
  a transport fault, a `resolve_visible_keeps` fault, or a store rejection from `register` — the
  pre-existing SF-63-1 poison survives on those paths, unserved. (For the duplicate-CREATE rejection,
  leaving the keep is correct — the winner uses it.)
- **N-4** `_rows_stamped` raises after commit; the rows ARE stamped and a re-run reports backfilled 0.
  Loud is right; the message could say the write landed. The UPDATE also returns every stamped row in
  full over the wire (a `RETURN id` would count the same with less payload).
- **N-5 (MINOR)** E7 states a provenance ("registered by a pkt-62–63b image") the code does not derive,
  and "see amendment-1 E3" is an address the served reader (an agent / operator at cutover) cannot
  resolve (no path). Trust doctrine: prose should be derived from behaviour.
- **N-6** `minted_by_this_call` flag probe (2026-09-26, pydantic 2.13.4, real tree):
  `==` True vs an unflagged copy, `model_dump`/`model_dump_json` omit it, `model_copy` carries it, and
  `Keep.model_validate(flagged)` returns the SAME instance so it carries too. Docstring's claims
  CONFIRMED; the `model_validate` carry is unmentioned (harmless today — no caller re-validates).
  Instrument (verbatim):
  ```python
  from datetime import datetime, UTC
  from loremaster.keeps import Keep, minted_by_this_call, _MINTED_BY_THIS_CALL
  a = Keep(id='keep:x', keeper_id='p', type='session', name=None, created_at=datetime.now(UTC))
  b = a.model_copy(); object.__setattr__(a, _MINTED_BY_THIS_CALL, True)
  print(a == b, minted_by_this_call(a), minted_by_this_call(b))      # True True False
  print(a.model_dump(), a.model_dump_json())                          # no flag key
  print(minted_by_this_call(a.model_copy()), minted_by_this_call(Keep.model_validate(a)))  # True True
  ```
- **N-7** Hostile ids: newline/control chars neutralised by `sanitise_line` everywhere (ids, owners,
  senders, invalid table name). An id whose TEXT contains `", "` renders as extra list items; the
  stated `of N` count still discriminates, and agent ids are uuid5 hex, so reach is message ids /
  sender links written outside the send path only. Backticks are not neutralised by `sanitise_line`
  (not re-verified here) and the refusals use backticks as prose delimiters.
- **N-8** see F-8 (the stale "charset-ASSERTed" docstring in `inbox_awaiter.py`).
- **N-9** Citation law: `_agent_migration_preconditions` docstring cites "instrument in
  `REPORT-builder-63c-i-a-fix.md` §P" — a bare repo-root REPORT address, which CLAUDE.md bans
  (unresolvable once archived). Should cite the archived path.
- **N-10** Identity-literal claim re-checked: an awk sweep of `loremaster/loremaster/**/*.py` for
  SQL-keyword f-strings interpolating `name|session|agent|sender|…` found none; the one inlined literal
  (`inbox_awaiter.live_select_statement`) interpolates the uuid5 `agent_id`. Heuristic sweep (keyed on
  variable names — a bounded instrument, stated as such), supports the corrected threat model.

## 5. Test skim (AFTER §1–§4 were written) — which items no test covers

Files skimmed (names + targeted bodies only): `loremaster/tests/test_fixwave_a19_63c_i_a.py`,
`test_fixwave_a19a_63c_i_a.py`, `test_fixwave_a19b_63c_i_a.py`, `test_comms_send_scope_63b_ii_a.py`
(SF-63-1 foreign-register test). Not run (brief).

| Item | Covered? | Evidence |
|---|---|---|
| F-1 compensation strands an ADOPTING winner | **NO — and the existing race pin is monoculture on exactly the harmless value.** `test_fixwave_a19a…::test_the_RACE_compensation_deletes_only_a_keep_this_call_created` constructs the concurrent winner as `ctx.agent_registry.register("raced-agent", …)` — a direct, OWNERLESS, unscoped row, i.e. the one winner that never adopts the keep. It asserts the keep IS deleted, which is correct only for that value. A principal-bearing winner (the only kind that can pass SF-63-1 on a freshly minted keep besides tokenless) is never constructed. | CLAUDE.md "FIXTURES MUST DISCRIMINATE" axis 2 |
| F-2 foreign principal + EXISTING name (retired / role / spawned_by) | NO. `test_comms_send_scope_63b_ii_a…::test_a_foreign_principals_register_into_a_kept_session_denies_naming_the_remedy_not_the_keeper` uses a FRESH name (`bob_w1`) — the one case where preflight admits and the gate still speaks first. | — |
| F-3 agent/memory `backfilled` measured | NO for agent/memory; message only (`test_fixwave_a19b…::test_backfilled_is_the_rows_the_UPDATE_stamped_never_the_pre_count`). Agent-leg pins assert static counts (`backfilled == 2`, `== 1`) on quiescent stores, where pre-count ≡ stamped. Commit `40c188d`'s subject (ruling amendment 27, FORK-1 Reading B: "backfilled = measured stamped rows ∀ legs; ∀-legs byte-diff pin over _migrate_legs") says this is RULED — the build does not yet meet it (subject line only read; the amendment doc is withheld from me). | — |
| F-4 `INFO FOR DB` non-dict / keyless | NO (no test in the three fix-wave files names `INFO FOR DB`). | awk sweep |
| F-5 failed delete = `KeepNotFoundError` | NO — `test_a_FAILED_compensation_serves_the_teaching_plus_ONE_remedy_line` injects `KeepStoreError` only. | a19b §#4b |
| F-6 "no scan of the target table" prose | n/a (docstring); KP7a–c / `test_the_multi_principal_refusal_serves_no_unmeasured_count` pin the `None`s, not the reason. | — |
| F-7 sender-state race in message UPDATE | NO. | — |
| F-8 stale prose (inbox_awaiter, CLI help) | NO. | — |
| S3 refused-before-mint (blank role, cadence, hostile name) | YES — a19 `test_a_blank_role_credentialed_register_mints_no_keep…`, `…CONTROLS_a_hostile_name_mints_no_keep…`, a19b KP13, a19a `test_a_refused_credentialed_register_mints_no_keep…`. | — |
| K1 found / CAS-winner never compensated | YES — a19b KP1 + the `found-pre-existing` leg of the race pin. | — |
| M10–M12 message dangling / half-pairs / no restamp | YES — a19a dangling set incl. hostile id; a19b half-pair set; `test_a_scoped_but_ownerless_message_is_never_restamped`. | — |
| M1 invalid table zero I/O | YES — a19a `test_an_invalid_table_is_answered_not_supported_with_zero_store_io` (derived table list). | — |
| M2 memory refused on agent facts | YES — a19 `test_every_table_refuses_a_multi_principal_store_and_writes_nothing`, `test_all_four_tables_serve_the_SAME_teaching`. | — |
| no-agent-table store | UNCLEAR — not located by name in the skimmed files. | — |
| N-7 hostile ids | YES for newline forgery (a19 `test_a_hostile_stored_id_cannot_forge_a_line…`, a19a `test_a_hostile_dangling_id_cannot_forge_a_line`); comma-in-id not covered. | — |
