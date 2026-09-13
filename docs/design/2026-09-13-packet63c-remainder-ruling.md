# Packet 63c — the comms REMAINDER ruling: `brief_*` + the `agent` roster as governed populations (sidecar-63c, 2026-09-13)

brief-base v14 read · brief project v7 read

## Summary block (brief-base §1)

- **state:** done — six forks RULED (Q1–Q6), each with the wrong build it admits, a "pin it like this"
  rider and a named re-open trigger; standing by for the lead's follow-ups (long-running sidecar).
- **deviations:** none. Writable set honoured (this file only); no code, no tests, no store touched. The
  lead named HEAD `bb9ac1e`; HEAD at ruling is `109da9c` (one commit later — the probe-63c commit itself,
  nothing this ruling rests on moved).
- **Capability check (brief-base §4):** everything demanded was reachable — lore MCP (read side served
  every symbol; the write side dropped twice with the #468 `no close frame` shape and healed on retry),
  `Read`/`sed`/prefix-`awk`, `git` read-only. Text-search binaries are hook-blocked as the brief said;
  every textual sweep below is `awk` over an explicit file list and is SAID so where used.
- **Packages considered:** none — no NEW package mechanism is specified. Every mechanism ruled here is an
  EXTENSION of a shipped seam (`_governed_field_specs` / `_governed_index_statements`, `read_filter`,
  `resolve_subject`, `resolve_principal`, `report_unmigrated_governed_rows`, `migrate_governed`, the
  P2/P2-m parametrised DDL-text pin, the F5 substrate). Nothing a package supplies (row-level authorization
  over this repo's own PDP; the 61/62 bespoke-PDP verdict stands, cited not re-argued).
- **Reuse ledger:** 0 new production symbols RULED; every new symbol is the contract author's / builder's
  to name, with the DRY row they owe listed in §11 (four candidate extensions, each with the query I ran and
  the existing symbol it extends — none hand-rolled).
- **Graded:** `109da9c` · HEAD-at-report: `109da9c` · SAME.
- **decisions-needed:** **none for the operator** — every fork is HOW within the operator-CONFIRMED
  SF-63-2 (63-rulings §7). Three items are LEAD calls (orchestration, not design), each carrying my
  recommendation: **L1** wave split (§8: two waves, agent-first); **L2** where the tokenless-register +
  ungoverned-verb corpse lands (§4.4: with the enforcing wave, the ii-a D1 precedent); **L3** three
  findings to FILE (§10: the identifier-regex twin, the §2.1 row-level precondition not implemented, the
  served `fleet session=` prose contradiction).
- **receipt pointers:** §0 (rulings in one screen) · §1 (facts F1–F16, symbol-cited) · §2 Q1 · §3 Q2 ·
  §4 Q3 · §5 Q4 · §6 Q5 · §7 Q6 · §8 riders roll-up · §9 removed-behaviour inventory heads-up · §10 flags
  · §11 DRY + discipline.

---

## 0. The rulings in one screen

| # | fork | ruling |
|---|---|---|
| **Q1** | `agent` roster READ governance | **(c) — `agent` gets the SAME three governed columns + two indexes through the ONE emitter** (`_governed_field_specs` / `_governed_index_statements("agent")`, retiring `_agent_statements`' hand-rolled pkt-62 `owner_principal` row + index as a twin). A NEW register stamps `owner_principal = registrant's principal`, `owner_agent = the row's OWN id`, `scope = keep:<session keep>` (SF-63-2's letter, verbatim); the cutover backfill stamps legacy rows `owner_principal = operator` (§2.1, precondition-guarded), `owner_agent = id`, `scope = keep:<project>` (§2.2's grandfather). Then `read_filter(subject, "agent")` is the standard member filter — index-served by the SAME construction probe-63c measured on `brief` (D-brief-2). (a) is REJECTED (breaks the comms model: a householded second principal could not see — nor address — the session's roster); (b) is REJECTED (a second, table-special predicate beside `_member_filter` — single-brain broken; field-through-hop or a private `IN` expansion). §2 |
| **Q1 visible set** | who sees whom | A MEMBER sees every agent whose `scope` is a keep the member is householded in (its own session keeps → its own agents + every teammate in a shared session; the project keep → every LEGACY agent, for the operator's household); an ADMIN sees all (`AllRows`). `fleet`, `roster` (the true-count projection), `brief_get`/`brief_publish` coverage, `send`'s recipient resolution and the unknown-agent roster enrichment ALL read through that one filter; the served COUNT is the served set's size (Leg 1). `heartbeat` is a SELF-write by id (no read filter; identity is the gate) — its render carries the bound line because its waiting-line count is a governed read. §2.3 |
| **Q2** | Register reading | **β — a `register` that resolves NO principal DENIES** (`GovernedDenied`, three facts, no roster, no keeper). Under Q1 `register` IS the CREATE of a governed row; α would mint post-cutover rows indistinguishable from unmigrated legacy rows, which the `WHERE scope IS NONE` backfill would then OWN-STAMP to the operator — a fabricated owner one verb later (the exact thing α exists to forbid). The transport PRINCIPAL token is what β keys on; `capability=` stays a FOREIGN param on register (a first register cannot have one). Keeper rule unchanged (ii-a Q2). Corpse measured: 58 tokenless register sites in 4 files, ALL on harnesses that already carry the credentialed seam (§3.3). §3 |
| **Q3** | the birth-time ASSERTs | Per the §13 question (*"is every row this constraint would refuse a row the READER would refuse anyway?"*): **`agent.status` KEEP** (reader-aligned: `Agent(BaseModel).status: AgentStatus` Literal — a junk row RAISES in `_row_to_agent`, and `fleet`/`roster` decode EVERY row → one junk row = total roster denial; the §13 grade case with a wider blast radius). **`agent.name` / `agent.session` / `agent.role` / `brief.name` / `brief.created_by`: DROP + MOVE the predicate into the ONE writer** (at HEAD `AgentRegistry.register` and `BriefLedger.publish` carry NO charset/non-empty check — the store ASSERT is their ONLY enforcement, so a bare DROP would widen the writer; the MOVE makes the writer the one implementation and retires the DDL's second spelling of the regex). **`brief.body`: DROP** (a pure duplicate of the #257 token floor, which is stricter). Tally: agent 3 DROP / 1 KEEP · brief 3 DROP / 0 KEEP. Forward instrument: the shipped parametrised P2 pin gains `[agent]` + `[brief]` rows (birth set, birth-DEFAULT set, exemptions `{status}` / `∅`, floors) + a P-G2-style alignment pin for `status`. Backfills stay ONE statement (after the drops nothing but `status` re-validates; a junk-status legacy row is impossible via any writer and is pinned as a KNOWN BOUND with the §13.2 heal protocol). §4 |
| **Q4a** | #467 touch-before-deny | **Identity BEFORE effect, in the dispatcher, ONCE:** for every `requires_capability` verb `AppContext.comms` resolves the Subject FIRST (`_resolve_subject(capability)` — the ONE composition root), reads the caller's OWN row BY ID (`subject.agent_id`), checks the supplied `agent=` (and `session=` when given) against THAT row (mismatch → one teaching `GovernedDenied`, no lookup by the supplied name, ever), THEN touches that row by id, THEN dispatches with `subject=` + `agent_row=`. This collapses the five handler copies of `agent_row.id != subject.agent_id` (`server.py` at `109da9c`: send, drain, ack, story, await) into ONE site and closes #467-1 by ORDER: a denied call performs ZERO agent-table mutations. §5.1 |
| **Q4b** | #467 roster leak | The enrichment survives ONLY where a name lookup legitimately remains — `send`'s recipient resolution — and there it is (i) scoped to the CALLER's own resolved session (already, by `agent_row.session`) and (ii) filtered by the caller's `read_filter` (Q1). On every other governed verb the supplied `agent=` is a self-consistency CHECK, never a lookup key, so ghost-vs-foreign is unrepresentable: both deny with byte-identical text. `fleet(session=X)` for a foreign or nonexistent X renders byte-identically (0 visible + the bound line). §5.2 |
| **Q5** | `report_unmigrated` for agent | **DISSOLVES under Q1(c):** `agent` gains `scope`, and `scope IS NONE` IS the one unmigrated predicate ∀ governed tables (owner may legitimately stay NONE — UNOWNED-LEGACY). `report_unmigrated_governed_rows(store, "agent")` fits unchanged; the agent migrate leg becomes ONE statement `… WHERE scope IS NONE` that stamps all three columns, with a ROW-LEVEL precondition (`count WHERE scope IS NONE AND owner_principal IS NOT NONE` must be 0 → else REFUSE naming the rows) that ALSO implements §2.1's multi-principal refuse, which I found is NOT implemented at HEAD (§6, flag L3-b). §2.6 order unchanged (agent first; message still gates on `_owner_count(agent, none=True) == 0`). §6 |
| **Q6** | wave shape + flips | **Recommend TWO waves, agent first:** **63c-i** = the agent population (Q1 DDL + backfill, Q2 β, Q3's agent drops, Q4 dispatcher reorder, `fleet`/`heartbeat` flips, the roster filter seam every roster reader consumes, its corpse); **63c-ii** = the brief population (DDL, `publish` stamp + project-keep scope, filtered `get`/`ack`, the brief migrate leg, Q3's brief drops, the three `brief_*` flips). `requires_capability=True` lands per verb WITH its enforcing wave (ii-a §4); the five #420 legs go GREEN per verb; `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` loses `lore_comms` at 63c-ii close (R-a.5). ONE security-auditor pass at 63c close drives the #467 wire battery + F3 ∀ verbs over both tables. §7 |

**Where I CHOSE between two readings of a spec sentence (brief-base §2 — written down, not silent):**
1. 63-rulings §4.1 lists the governed-column DDL for `{memory, message} + brief + task, finding` and omits
   `agent`; §7 SF-63-2 (later, operator-CONFIRMED) says *"`agent` rows are scoped to their session keep
   (owner = the row's own `(owner_principal, id)`)"* — a SCOPE statement about agent rows. Reading A: §4.1's
   omission is deliberate and agent must be governed WITHOUT a scope column. Reading B: §4.1 enumerated the
   tables 63a/63b would touch and §7 is the authority on agent's population semantics. **I pick B** — §7 is
   the operator's confirmation and its letter names a scope; §4.1 predates the confirmation and its own
   "why two indexes" reasoning is written for exactly the column set Q1(c) adds. If the lead reads A, Q1's
   alternative is (b) and §2.5 says what it costs.
2. The served `lore_comms` description says *"for 'fleet' it additionally scopes the listing to one
   session"*; at HEAD a `session=` other than the caller's own errors at the dispatcher's touch
   (`_resolve_row(name, session)` → `UnknownAgentError`, enriched with THAT session's roster — #467-2). So
   "list another session" was never a working capability. I rule `session=` on a governed verb as an
   identity CHECK (must equal the Subject's row's session when given) — and inventory "list a foreign
   session" as never-a-behaviour (§9 item 5). Reading the prose as a promise to KEEP would require a
   second meaning for one parameter; rejected, and the prose is corrected (flag L3-c).

---

## 1. The facts this ruling rests on (read at `109da9c`; cited, not re-transcribed)

- **F1 — probe-63c (lead-verified), the store facts:** `agent`'s ASSERT-bearing columns are BIRTH-TIME
  (`name`/`session` charset, `role` non-empty, `status` closed domain); every post-birth column is
  `option<>` no-ASSERT; `agent` already carries `owner_principal option<record<principal>>` + plain index
  `agent_owner_principal` (hand-rolled in `_agent_statements`, pkt 62). `brief`'s ASSERT-bearing columns
  are birth-time (`name` charset, `body`/`created_by` non-empty) and it carries NONE of the governed
  columns. DD-3.c is REAL on both (Part C: whole-window backfill = total denial on one violator; single-row
  `touch` self-denies a poisoned row) and NIL for the current migration (no real row can violate a
  birth-time ASSERT). EXPLAINs (Part D): `brief` + the three columns + the two plain indexes →
  `UnionIndexScan`, no TableScan; `agent` WITHOUT `scope` → the member filter TableScans;
  `owner_principal =` and `session =` IndexScan.
- **F2 — the dispatcher order at HEAD** (`AppContext.comms`, `server.py`): shape checks → `if
  spec.requires_registration:` **touch by NAME** (`agent_registry.touch(agent, session=…)`) → on
  `UnknownAgentError`, `_comms_enrich_unknown_agent(session=<caller-supplied>)` → `spec.handler(...)`. The
  §4.D capability check lives INSIDE each handler. `_comms_enrich_unknown_agent` calls
  `agent_registry.fleet(session=session, limit=_MAX_FLEET_LIMIT)` — caller-supplied session, unfiltered;
  `session=None` spans every session (its own docstring says so).
- **F3 — five handler copies of the agent≡subject check** at `109da9c` (`awk 'subject\.agent_id'` over
  `server.py`, said so): `_comms_send` (`:7258`), `_comms_drain` (`:7453`), `_comms_ack` (`:7546`),
  `_comms_story` (`:7620`), `_comms_await` (`:7053`) — each `if agent_row.id != subject.agent_id: raise
  GovernedDenied(...)`. ONE policy, five sites — the #102 seam, live.
- **F4 — the verb spec table** (`_COMMS_ACTIONS`): `requires_capability=True` on exactly
  `{send, drain, ack, story, await}`; `False` (default) on `heartbeat`, `brief_get`, `brief_publish`,
  `brief_ack`, `fleet`; `register` has `requires_registration=False` and NO `capability` in its `params`.
  `_GOVERNED_VERBS_PENDING_ROUTING` carries the five 63c legs → `_ROUTE_63C_REMAINDER`.
- **F5 — the roster READERS at HEAD** (each an unfiltered `SELECT * FROM agent [WHERE session=$s]`):
  `AgentRegistry.fleet` (display window), `AgentRegistry.roster` (row-unlimited true counts + members) —
  consumed by `_comms_fleet` (both), `_comms_brief_get` (roster → coverage denominator),
  `_comms_brief_publish` (roster → `behind`), `_comms_send` (broadcast recipients), and
  `_comms_enrich_unknown_agent` (fleet). `_comms_resolve_recipients` resolves recipient NAMES in the
  caller's session (`session_scope = agent_row.session`).
- **F6 — the readers' decode models:** `Agent(BaseModel)` with `status: AgentStatus =
  Literal["active","idle","input_required","retired"]` — `_row_to_agent` constructs `Agent(...)` per row
  (pydantic-validated; the `cast` is for mypy only), `name`/`session`/`role` decode as `str(...)` (any
  value). `Brief(BaseModel)`: `name`/`body`/`created_by: str` (any value). So the ONLY reader-aligned
  store ASSERT on either table is `agent.status`.
- **F7 — the writers' app caps at HEAD:** `AgentRegistry.register` raises only identity-conflict /
  retired / vanished errors (`agents.py:744–814`, read) — NO charset check on `name`/`session`, NO
  non-empty check on `role`; the charset is enforced at the TOOL layer only (`_validate_comms_charset`,
  `AGENT_NAME_PATTERN`) and `role=""` passes the dispatcher's `is None` required-check. `BriefLedger.publish`
  enforces the #257 token floor on `body` (stricter than non-empty); NO charset check on `name`; NO check on
  `created_by` (the tool passes `agent_row.name`). `touch` validates `status` edges against the closed
  domain; `register` writes status from constants.
- **F8 — the identifier regex has TWO spellings** (`awk` over every `*.py` under `lorerunes/` +
  `loremaster/loremaster/`, pattern `a-z0-9_-]{0,63}`, said so): `agents.py:161 AGENT_NAME_PATTERN` and
  `surreal_schema.py:490 _IDENTIFIER_CHARSET_PATTERN`. No pin found that asserts the two are equal (flag
  L3-a).
- **F9 — `register` at HEAD** (`_comms_register`): `resolve_principal(get_access_token(), …)`; `None` →
  reading α (ownerless, no keep, render names the bound); else mint/join the session keep, the SF-63-1
  foreign gate, `agent_registry.register(..., owner_principal_id=…)`, the head-brief auto-ack
  (`brief_ledger.get_head` — an UNFILTERED brief read), the #262 liveness notice (`_holder_liveness_notice`
  — an unfiltered agent read by task id). `get_access_token` is `fastmcp.server.dependencies.get_access_token`
  (returns `None` off-request).
- **F10 — the migrate seams:** `principals.migrate_governed(table=…)` dispatches `memory` → `_migrate_memory_scope`,
  `agent` → `_migrate_agent_owner`, `message` → `_migrate_message_owner`; `brief` is refused with a teaching
  reason naming 63c. `_migrate_agent_owner`: `resolve_operator_principal` (refuses on principal-level
  ambiguity) → `_owner_count(agent, none=True/False)` → `UPDATE agent SET owner_principal =
  type::record('principal',$owner) WHERE owner_principal IS NONE` under `governed_exempt("migrate-governed")`.
  ⚠ **§2.1's ROW-level precondition (*"EVERY legacy agent's owner_principal is NONE … a store where any
  agent already carries a DIFFERENT owner → REFUSE loud and name the rows"*) is NOT implemented** — the leg
  refuses only when the OPERATOR is ambiguous, and stamps every NONE-owner row regardless of other rows'
  owners. `report_unmigrated_governed_rows(store, table)` is `WHERE scope IS NONE` (scope-keyed);
  `_owner_count` is the owner twin.
- **F11 — the shipped forward pin** `test_comms_schema.py::TestNoGovernedTableCarriesAConstraintALegacyRowCanViolate`
  is ONE parametrised pin over a `_ConstraintSpec(table_attr, birth, birth_defaults, exemptions, floor)`
  with rows `[to]` and `[message]` (exemptions `∅` / `{grade}`), deriving fields from `generate_message_ddl()`
  via `_overwrite_field_statements`; the exemption non-vacuity leg is present (ii-b §14.3 confirmed).
- **F12 — existing pins that certify the agent/brief ASSERTs (the DUAL's input; `awk 'ASSERT' over
  loremaster/tests/*.py`, said so):** `test_comms_schema.py:467/473` (agent charset + role non-empty DDL
  text), `:572/:582` (brief charset + non-empty DDL text), `:756` (live hostile-shape rejection on
  `agent.name`/`session`), `:803` (`brief.name` same class); `test_brief_ledger.py:746–767, 2205–2323`
  (blank body/created_by double-guard); `test_comms_wiring.py:265–290` (defense-in-depth prose);
  `test_agent_owns_principal_schema.py:173` (docstring naming the four agent ASSERTs); `_comms_fakes.py:707`
  (a fake that mirrors the blank-body schema rejection).
- **F13 — the tokenless-register corpse, measured** (`awk 'action="register"'` per test file + a
  credentialed/fake marker count, said so): `test_comms_wiring.py` **29** (real store via
  `build_app_context`, cred=0 — off-request token → `None`), `test_comms_tool.py` **20** (fakes; the autouse
  `_ACCESS_HOLDER` defaults to `subject=""` → `resolve_principal` → `None`, i.e. deliberately α),
  `test_comms_render_architecture.py` **5** (fakes, real `get_access_token` → `None`),
  `test_mcp_server.py` **4**. Total **58** — the same four files ii-a §8 counted; ii-a's D1 credentialed the
  SEND sites, not these. The remaining register sites (`test_comms_capability_63b_ii_a.py` 7,
  `test_comms_send_scope_63b_ii_a.py` 21, `test_comms_read_governance_63b_ii_b.py` 6,
  `test_message_enforcement_63b_ii_a.py` 1) are credentialed, with ONE deliberately tokenless pin (ii-a
  MP-6, the α bound) that β INVERTS.
- **F14 — the shared credentialed harness EXISTS** (`_governed_contract.py::credentialed_app_context`,
  `register_owned`, `store_handle`; ii-a §11.3 F-DUP, landed per ii-b §14.3), and `_comms_fakes.py`'s
  `FakeAgentRegistry` already carries `register(owner_principal_id=)` + `_verify_capability_owner` +
  `FakePrincipalStore`/`FakeKeepStore` (D1 landed). The β corpse is a FIXTURE SWAP, not new mechanism.
- **F15 — `Keep`/`KeepStore`:** `Keep` (id, keeper_id, type, name, created_at) does NOT expose `key`;
  `get_by_key` reads the UNIQUE `keep_key` index; `resolve_visible_keeps(keep_store, member_email)` →
  `frozenset[keep:<id>]` via `list_keeps_for_member`. There is NO `type` index on `keep`. (This is why
  Q1(b) needs either a new keep read per call or a field-through-hop — §2.5.)
- **F16 — the #467 wire repro is archived:**
  `docs/plans/v2/receipts/2026-09-12-packet63b-iii/REPORT-secaudit-63b-iii.md` §RESIDUALS (probe2 F1/F2,
  ≥2 principals, switchable token, over `:18000`). It is the instrument §5.4's wire leg re-runs.

---

## 2. Q1 — RULING: `agent` is governed by the standard three-column filter (option (c))

### 2.1 The DDL (through the ONE emitter — cite 63-rulings §4.1, store-ref §1.1/§1.4/§1.5)

`_agent_statements` appends `_governed_field_specs()` + `_governed_index_statements("agent")` exactly as
`_memory_statements`/`_message_statements` do — and DELETES its hand-rolled pkt-62 `owner_principal`
spec row + `agent_owner_principal` index line (a twin of the shared emitter; ONE IMPLEMENTATION). Net DDL:

```
DEFINE FIELD OVERWRITE owner_principal ON agent TYPE option<record<principal>>;   -- re-landed, byte-identical
DEFINE FIELD OVERWRITE owner_agent     ON agent TYPE option<record<agent>>;       -- NEW (self-link)
DEFINE FIELD OVERWRITE scope           ON agent TYPE option<string>;              -- NEW
DEFINE INDEX IF NOT EXISTS agent_scope           ON agent FIELDS scope;           -- NEW
DEFINE INDEX IF NOT EXISTS agent_owner_principal ON agent FIELDS owner_principal; -- same name → no-op (§1.1)
```

All `option<>`, no ASSERT, no DEFAULT (§1.4 — `agent` is the most populated comms table). The
`agent_owner_principal` index name is preserved so the existing index is a `IF NOT EXISTS` no-op rather
than a rebuild (§1.5). The pkt-62 pin that `owner_principal` carries NO ASSERT
(`test_agent_owns_principal_schema.py:259`) stays green and gains its siblings by the P2 row (§4.3).

**Wrong build admitted (each with its pin):** (W1-1) keeps the hand-rolled row beside the emitter call →
the emitter-mutation pin (change `_governed_index_statements` → every governed table's schema pin reds,
63-rulings §3.2 rider) stays GREEN for `agent` because the hand-rolled twin still emits the old line → **pin:
`_agent_statements`' emitted statements for the three columns are BYTE-EQUAL to
`_governed_field_specs()`'s, and the `owner_principal` line appears EXACTLY once**. (W1-2) adds the columns
with a DEFAULT → P2-agent's birth-DEFAULT leg reds (§4.3).

### 2.2 The stamps (write side)

| write | `owner_principal` | `owner_agent` | `scope` | seam |
|---|---|---|---|---|
| `register` (CREATE) | the registrant's admitted principal (β, §3) | **the row's own minted id** (SF-63-2: owner = `(owner_principal, id)`) | `keep:<session keep>` — the SF-63-1 keep `register` already mints/joins | inside `write_guard("register")`; the F5 allowlist's CREATE-OWNS-IT entry with evidence *"the id embeds `uuid5(session, name)` and the owner pair is server-derived from the transport principal — no argument moves it"* |
| re-register (UPDATE by id) | untouched (mint-once) | untouched | untouched | the same allowlist entry (self-row by id) |
| `heartbeat` / the dispatcher touch (UPDATE by id) | — | — | — | §5.1: the touched id IS `subject.agent_id`; allowlisted with that evidence pin; `write_guard("heartbeat")` / a per-verb label the dispatcher sets |
| cutover backfill | the operator (§2.1, precondition-guarded — §6) | `id` | `keep:<project>` (§2.2 grandfather) | `governed_exempt("migrate-governed")` as today |

**Why the project keep for legacy agents, not per-session keeps:** legacy sessions are finished sessions
(the fleet's `agent` table is mostly retired rows); minting a session keep per dead session is a keep per
corpse. The grandfather scope for EVERY 63 table is the project keep (§2.2), and the operator's household
sees them exactly as today. Re-open trigger: *"the first request to re-home a legacy session's agents into a
live session keep"* → `SET_SCOPE` (admin), not a backfill change.

**Why `owner_agent = self` and not NONE:** the WRITE/DELETE predicates need the exact pair; an agent row's
owner-agent is itself by SF-63-2's letter. It ALSO gives the F2 single-brain oracle a non-degenerate
`agent-private` case for free (a row whose owner_agent equals its id). NOT indexed (§4.1's `owner_agent`
bound + trigger apply unchanged).

**No `scope=` argument on any 63c verb.** `register`'s scope is the session keep by construction;
`brief_publish`'s is the project keep by construction (§7.2). Re-open trigger: *"the first keep-private brief
or the first cross-session agent listing request"*. (This keeps F4's fuzz set for 63c at
`owner_*=`/`as_agent=`/`created_by=`/`scope=` → all foreign-param refusals at the MCP layer.)

### 2.3 The visible set, and every reader that must honour it (∀ readers — the quantifier law)

Under the standard member READ predicate (`_member_filter`, cited) an agent row with `scope = keep:<k>` is
visible to a member iff `keep:<k> ∈ subject.visible_keep_ids`. Therefore:

- **a member sees:** its OWN agents (it is householded in every session keep it registered into — keeper or
  joined), every TEAMMATE in a session whose keep it is householded in (SF-63-1's admission predicate,
  re-applied at read), and every LEGACY agent iff it is householded in the project keep (the operator's
  household — the whole pre-65 fleet). A principal householded ONLY in a session keep sees that session's
  roster and nothing else — which is what a hosted foreign principal in a shared session legitimately
  needs (to address teammates) and nothing it must not (§6 item 1).
- **an admin sees all** (`AllRows`, §10-K).
- **the served COUNT is the served set's size** — `roster.status_counts`, `fleet`'s `total_non_retired`,
  `coverage.total_agents`, `send`'s broadcast set: every one is computed over the FILTERED rows. A count
  over the unfiltered table beside a filtered listing is the false clear Leg 1 forbids.

**The ONE seam, and its consumers (each row is a pin — F3's ∀-readers leg for `agent`):**

| reader | change | pin (RED on) |
|---|---|---|
| `AgentRegistry.fleet(*, session, limit, read_filter)` | keyword-only `read_filter: tuple[str, dict]` with NO default (the fixture-default law); splices `AND ({fragment})` with merged params | `fleet` from a member of no keep serves 0 rows + `total_non_retired == 0` while admin serves N; a build that filters `rows` but not `total` (a count over the unfiltered table) |
| `AgentRegistry.roster(*, session, read_filter)` | same splice on BOTH statements (the `GROUP BY status` count AND the members SELECT) | `status_counts` sums to the visible member count; a build filtering members but not the aggregate |
| `_comms_fleet` | resolves nothing itself (the dispatcher hands it `subject`); passes `read_filter(subject, AGENT_TABLE)` to both | the header's per-status segments equal the served set (Leg 1) |
| `_comms_brief_get` / `_comms_brief_publish` coverage | the roster is the VISIBLE roster; coverage's denominator = visible agents; `behind` names only visible agents | a foreign-principal agent never appears in `behind`; `total_agents` == visible count |
| `_comms_send` broadcast + `_comms_resolve_recipients` | the roster/lookup pass the caller's filter; an invisible recipient name → the SAME `UnknownRecipientError` as a ghost | naming a visible teammate delivers; naming a foreign-session agent renders byte-identically to a ghost |
| `_comms_enrich_unknown_agent` | takes `subject` (keyword-only, no default) and the CALLER's own session; the fleet read is filtered | the enriched roster ⊆ the caller's visible set (assert no foreign name appears, with a foreign agent SEEDED) |
| `_holder_liveness_notice` (register, #262) | the holder's agent read passes the read filter of the just-minted Subject (§3.5) | a holder in a session the registrant is not householded in → the notice is OMITTED (never "unknown holder" — that would be an oracle) |
| `heartbeat` | NO read filter on the touch (self-row by id); the `_comms_waiting_lines` count rides the ii-b-filtered inbox read with the Subject | the waiting-line count == the drain-visible count for the same Subject (mutation: make a directive invisible → both drop together) |

**Mutation proof of sharing (the rider):** change `ScopeEq.to_surql` (63-rulings R-a.3) → every row above
reds; a reader that stays green is a private copy wearing the shared name.

### 2.4 The EXPLAIN rider (probe-63c PART D, carried into a PINNED EXPLAIN)

The contract pins `read_filter(member, "agent").to_surql()` over the REAL post-63c `_agent_statements`
DDL as an `IndexScan`/`UnionIndexScan` with NO `agent` TableScan — the D-brief-2 verdict re-measured on the
table it now governs — with the C+ control in the same test (`WHERE role = $r` → TableScan) and a
NONE-scope legacy row present (§1.8 / ii-a P1). Reuse `probe_read_filter_63.py`'s `explain` harness (the
probe-63c precedent) — never a second walker. RED on: a plan containing a TableScan of `agent`.

### 2.5 The rejected candidates, each with the wrong world it blesses

- **(a) owner_principal-only** — index-served, but it answers "agents I own". Under SF-63-1 a keeper
  households principal B into a session; B's agent then cannot SEE the session's roster, cannot resolve a
  recipient by name (recipient resolution is a roster read), and `fleet` shows B only itself. That breaks
  the comms model the operator confirmed (a shared session is a keep-scoped SET) and contradicts SF-63-2's
  letter ("scoped to their session keep"). Blessed wrong world: a single-principal fixture (the F11
  monoculture ii-a named) passes every pin with the model broken for the second principal.
- **(b) resolved session-set** — semantically right but mechanically a SECOND predicate: `session IN
  $sessions OR owner_principal = $p` is not `_member_filter`'s tree, so `authorize(row)` (Python) and the
  store filter are two brains for one table (63-rulings §1.2 item 3's single-brain is the whole point);
  the `IN` inside the `OR` is the #413 TableScan trap unless privately expanded; and the session-string set
  needs a keep read per call that `Keep` does not expose (F15 — a new `list_session_keys_for_member` or a
  field-through-hop, §4). Legacy agents (no session keep) are invisible to every member until per-session
  keeps are minted. Blessed wrong world: a filter that IndexScans on a virgin DB and TableScans the moment
  a keep set is empty (`IN []` inside `OR`).
- **(c) is the standard filter** — one tree, one splice, index-served by the construction probe-63c
  measured; its only cost is the `scope` backfill, which §4 makes safe by construction (no ASSERT a legacy
  row can violate after the drops; `status` cannot be violated by any writer).

**Re-open trigger for Q1:** *"the day an agent must be visible across sessions it is NOT householded in
(an org-wide directory verb)"* → that is a `server`-scoped row or a `SET_SCOPE`, not a filter change.

---

## 3. Q2 — RULING: Register reading β (deny on absent principal)

### 3.1 Why β follows from Q1, not from taste

ii-a §3.2 ruled α with the trigger *"63c — when `agent` joins the population set, `register` IS a governed
write and deny-on-absent is its natural shape"*. The trigger has fired, and Q1 sharpens it into a
correctness argument, not a posture:

1. **α post-63c fabricates an owner one verb later.** An ownerless register writes a row with
   `owner_principal = NONE, scope = NONE` — byte-indistinguishable from an UNMIGRATED legacy row. The
   cutover backfill (`WHERE scope IS NONE`, §6) then stamps it `owner_principal = the operator`. A
   tokenless registrant's agent becomes the operator's, silently. pkt-62 Fork 2 (a) — *"NULL
   `owner_principal` unambiguously means genuinely-legacy … the two populations never collide"* — is
   FALSE the moment α coexists with a governed `agent` table. β is what keeps Fork 2 (a) true.
2. **α's "inert agent" is no longer inert.** Under 63c every non-register verb is `requires_capability`,
   so the row denies everything — but it EXISTS: it appears in admin `fleet`, it counts in the standing
   brief's `behind` list forever (it can never ack), and it is a row a later `migrate-governed` re-run
   would own. A row that can never act but forever skews served counts is served noise (Leg 1).
3. **W2.3's property is met by β exactly:** *"no OWNED agent without proof of the owner"* — and now no
   agent without an owner either, because a governed row without an owner is the UNOWNED-LEGACY class,
   which is reserved for rows written before identity existed (§2.1's hard rule).

### 3.2 The ruling, precisely (binding)

- In `_comms_register`, after `principal = await resolve_principal(get_access_token(), …)`:
  `if principal is None: raise GovernedDenied(<three facts>)` — BEFORE any keep read, BEFORE any agent
  row is written (#97: a rejected call has no side effect). The α branch (`ownerless=True`, the bound
  line) is DELETED from `_render_comms_register` (a render for a state that cannot occur is stale prose —
  P8d).
- **What β keys on is the transport PRINCIPAL token** (the pkt-49 api-key → `token_verifier` → `subject =
  principal.email` → `PrincipalStore.get_by_email`). It does NOT key on `capability=`: `register` MINTS the
  capability (ii-a §3.4) and `capability` stays OUT of `register`'s `params` (a caller passing it gets the
  existing foreign-param `ValueError`, pinned).
- **Keeper rule unchanged** (ii-a Q2 / SF-63-1): keeper = the registrant's principal via the ONE lifted
  `resolve_principal`; the foreign gate and the mint/join order stand verbatim (`_comms_register` steps 1–6
  minus the α branch). A presented-but-unadmitted principal keeps raising inside `resolve_principal`
  (unchanged).
- **The deny render states three FACTS and nothing else** (the promise registry proves it): (1) *the
  transport carried no principal* (no `subject` on the access token); (2) *what a register requires* — the
  fleet's principal credential on the transport (the pkt-49 api-key), NOT a `capability=` (a first
  register cannot hold one); (3) *the remedy* — present it and register again under the SAME name (nothing
  was written, so no fresh name is needed; mint-once-on-create is untouched). It names NO keeper, NO
  session household, NO roster (§6 existence-leak stance).

### 3.3 The corpse — measured (F13), and where it lands (lead call L2, my recommendation)

58 tokenless register sites in four files, every one of them on a harness that ALREADY carries the
credentialed seam (F14): `test_comms_tool.py`'s `_ACCESS_HOLDER` + `_credential_agent`,
`test_comms_wiring.py` (swap `_open_context` to `credentialed_app_context`), `test_comms_render_architecture.py`
(the fakes carry the seam; set the holder), `test_mcp_server.py` (the 63a-ii `app_context` fixture already
patches `get_access_token`). Plus the ii-a MP-6 α pin, INVERTED to β (§3.4). **Recommendation: land β and
its corpse in 63c-i as ONE reconciliation** — ii-a's D1 precedent, verbatim: a `requires_*` that a fixture
side-steps is a lying spec, and 58 `RED_ADJUDICATED` rows across a wave gap is a hand-list of hopes.

### 3.4 Pin it like this

| pin | fixture | RED on (the wrong build) |
|---|---|---|
| **R-β1** `test_a_tokenless_register_denies_and_writes_nothing` (send_scope, replacing MP-6) | `holder["email"] = None` AND the `get_access_token() → None` shape (drive both); register | any row for the name (`SELECT count() FROM agent WHERE name=$n` == 0), any keep for `session:<s>` (`get_by_key` is None), no `GovernedDenied`, or a deny text containing a keeper email / a roster name / the word "ownerless" |
| **R-β2** the three-facts render | same | the render omits any of the three facts, or names `capability=` as the remedy (the reading-confusion the brief warns of) |
| **R-β3** `register(capability=…)` is a FOREIGN param | credentialed register with `capability=<anything>` | anything but the existing foreign-param `ValueError` — proves β did not smuggle a capability requirement onto the mint verb |
| **R-β4** the Reading-A HYBRID is dead | monkeypatch `resolve_principal → None` on a harness whose `resolve_operator_principal` resolves an admin | a register that SUCCEEDS with the admin as owner/keeper (ii-a §11.2's fabrication build) |
| **R-β5** positive control | the credentialed register in a fresh session mints the keep, stamps the pair + the session-keep scope (§2.2 row 1) | — |
| **R-β6** the α render line is GONE | promise-registry sweep + a bare `awk` for `ownerless` over `server.py`/tests | a surviving α line (stale prose) |

**Re-open trigger for β:** *"a deployment whose transport cannot carry a principal credential"* — at which
point the answer is a credential on the transport, never α back.

### 3.5 Two register-internal reads become governed under Q1 + SF-63-2 (a consequence, ruled)

`_comms_register` performs two reads AFTER the mint that Q1 makes governed: the head-brief auto-ack
(`brief_ledger.get_head` — a `brief` read; under 63c-ii every brief is project-keep-scoped) and the #262
liveness notice (an `agent` read). RULING: when either read is needed, `register` resolves the freshly
minted Subject ONCE through the ONE constructor (`self._resolve_subject(result.capability)` — one extra
round trip, only on a first register that has a head brief or a `task_id`) and both reads take its
`read_filter`. Consequence, stated: a principal householded only in a session keep (never the project keep)
sees NO standing brief at register, acks nothing, and its render says *"no standing brief visible to your
principal"* — which is SF-63-2's letter (briefs are project-keep data) and the §6 isolation working as
confirmed, not a defect. Pin: a session-only principal's register writes NO `briefed` edge and its
`heartbeat` skew line names the bound, not a version number it cannot read.

---

## 4. Q3 — RULING: per-ASSERT verdicts, the forward pin, the backfill shape

### 4.1 The threat model, re-derived for `agent` and `brief` (a gate needs one)

Who are the ASSERTs for? The honest developer who adds a writer without the app cap. Who is hurt? (T1) an
honest NARROWING edit — shrinking the identifier length, forbidding `-`, retiring a status, tightening
"non-empty" to a token floor; under it every gate is green (virgin DBs, §1.6), and on the long-lived store:
every legacy `agent` row violating it self-denies its OWN heartbeat (Part C, bounded per agent — but that
agent cannot even `heartbeat status=retired` its way out), and the ONE-statement backfills refuse WHOLESALE
at the cutover. The same table as ii-b §2/§12.2, with `agent`'s per-agent heartbeat denial sitting between
`to`'s (every drain) and `message`'s (one cutover verb) in severity.

### 4.2 The per-ASSERT table (the §13 question, applied per constraint — read, not assumed)

| constraint (at `109da9c`) | reader rejects a violator? (F6) | app cap in the ONE writer? (F7) | verdict |
|---|---|---|---|
| `agent.status` `ASSERT $value IN ['active','idle','input_required','retired']` | **YES** — `Agent.status: AgentStatus` Literal, pydantic-validated per row in `_row_to_agent`; `fleet`/`roster` decode EVERY row → one junk row = total roster denial for every reader | YES — `touch` validates the edge; `register` writes constants; `AGENT_STATUSES` ≡ `get_args(AgentStatus)` | **KEEP** (reader-aligned; the §13 exemption rule verbatim, with a WIDER blast radius than `grade`). Exemption `{status}` in P2-agent + alignment pin P-A2 (§4.3). |
| `agent.name` charset | no (`str(...)`) | **NO** in `register` (tool-layer only, F7) | **DROP + MOVE**: `AgentRegistry.register` validates `name` AND `session` with `AGENT_NAME_PATTERN.fullmatch` (the SAME object `_validate_comms_charset` uses — sharing by construction) → a teaching `AgentRegistryError` subclass BEFORE any store I/O. The DDL row's constraint → `""`; `_IDENTIFIER_CHARSET_PATTERN` in `surreal_schema.py` loses its last consumer once `brief.name` drops too → DELETE it (F8's twin dies). |
| `agent.session` charset | no | NO | **DROP + MOVE** (same predicate call as `name`). |
| `agent.role` non-empty | no | **NO** — `role=""` passes the dispatcher's `is None` check and reaches the registry | **DROP + MOVE**: `register` rejects a blank `role` via `lorerunes.is_blank` (the shared blankness predicate, pkt 42 #222 — never a second `strip()`), teaching. |
| `brief.name` charset | no | NO in `publish` | **DROP + MOVE**: `BriefLedger.publish` validates `name` with `AGENT_NAME_PATTERN.fullmatch` (imported from `agents.py` — the ONE spelling; `briefs.py` already imports from `agents`). |
| `brief.body` non-empty | no | **YES** — the #257 token floor (`len(body.split()) < _MIN_BRIEF_BODY_TOKENS`) is STRICTER and fires FIRST | **DROP** (pure duplicate; `test_brief_ledger.py`'s "double-guarded" prose becomes single-guarded — D-B5). |
| `brief.created_by` non-empty | no | NO in `publish` (the tool passes `agent_row.name`, non-blank by the registry's new check — but the LEDGER accepts any string) | **DROP + MOVE**: `publish` rejects a blank `created_by` via `is_blank`, teaching. |

**Tally: agent 3 DROP / 1 KEEP · brief 3 DROP / 0 KEEP.** Every DROP is a `_define_field` `OVERWRITE`
re-land with an empty constraint (store-ref §1.2 — the FULL REPLACE drops the stored clause on `:18500`;
`ensure_ready` lands it at the pkt-65 boot BEFORE any backfill or heartbeat — no ordering to remember, ii-b
R17). Every row STAYS in its `_*_FIELD_SPECS` tuple (a deleted row leaves the stored ASSERT in place forever,
ii-b R10).

**Why MOVE rather than KEEP for the non-aligned five (right-sizing stated, not assumed):** the MOVE is one
predicate call in each of two writers using predicates that already exist (`AGENT_NAME_PATTERN`,
`is_blank`) — ~20 lines + their teaching pins; the payoff is that the ONE writer becomes the one
implementation (ONE IMPLEMENTATION), a second regex spelling dies (F8), a junk value is refused with a
TEACHING error instead of a laundered `(assert violation)` (the consumer frame), and the DD-3.c gun on
`agent`/`brief` is unloaded ∀ future narrowing edits rather than pinned as a miss. **If the lead prices the
MOVE out of 63c**, the honest fallback is NOT a bare DROP (that widens the writers): it is KEEP-ALL with the
P2 rows' exemption sets = the full birth ASSERT set, each labelled *"KNOWN BOUND — birth-time; a narrowing
edit is DD-3.c; re-open: the first narrowing edit or 63c-fix"*. I recommend the MOVE.

### 4.3 The forward instrument — P2 gains `[agent]` and `[brief]` (ONE parametrised pin, never a clone)

Extend `test_comms_schema.py::TestNoGovernedTableCarriesAConstraintALegacyRowCanViolate` (F11) with two
`_ConstraintSpec` rows. ⚠ The spec derives fields from `generate_message_ddl()`; `agent`/`brief` DDL comes
from their own emitters — the spec gains a `ddl: Callable[[], Sequence[str]]` member (or the pin derives from
`generate_ddl()`'s full statement list) so the derivation is by TABLE over the REAL emitter, never a
hand-copied statement list. Rows:

- **`[agent]`:** `birth` = the PKT-28 C1 field set — the contract author DERIVES it from `git log -S` on
  `_AGENT_FIELD_SPECS` (my read of probe-63c PART A gives the candidate: `{name, session, role, model,
  status, spawned_by, task_id, checkpoint, last_note, registered_at, heartbeat_at}`; post-birth =
  `{status_set_at (#304), declared_cadence (W1a), owner_principal, capability_hash,
  capability_expires_at (62), owner_agent, scope (63c)}` — a git-derived set, not my table);
  `birth_defaults = ∅`; `exemptions = {status}`; `floor ⊇ {name, status, owner_principal, scope}`.
- **`[brief]`:** `birth = {name, version, body, created_by, note, created_at}`; `birth_defaults =
  {created_at}`; `exemptions = ∅`; `floor ⊇ {body, created_by, owner_principal, scope}`.
- **The failure message** gains the `agent` wording: *"`agent` is UPDATE-hot per agent (`touch` re-validates
  the caller's whole row on every comms action) and UPDATE-able whole-window (the cutover backfill): a
  constraint here is DD-3.c — a legacy row violating it denies that agent's every heartbeat and refuses the
  whole backfill (63c ruling §4). The app cap in `AgentRegistry.register`/`touch` is the ONE implementation.
  Adding one DELIBERATELY? you owe (a) a heal that runs BEFORE the first heartbeat/backfill and (b) the
  §4.4 dirty-store pin inverted — then say so."*
- **P-A2 (the `status` alignment pin, the P-G2 twin):** the set inside the emitted `status` ASSERT (parsed
  from `_agent_statements`' text) `==` `set(AGENT_STATUSES)` `==` `set(get_args(AgentStatus))`. Mutation: add
  a status to the tuple only → RED. (Extend an existing status-domain pin if one holds two of the three
  legs; ONE pin.)
- **Mutation proofs (declared from `--collect-only`, diffed both ways):** re-add the `name` charset ASSERT →
  `[agent]` RED; add `("x", "string", "")` to `_AGENT_FIELD_SPECS` → RED (non-option post-birth); add
  `("y", "option<string>", "DEFAULT 'z'")` → RED; drop `status`'s ASSERT → the `[agent]` exemption
  non-vacuity leg RED + P-A2 RED; the same three shapes on `_BRIEF_FIELD_SPECS` → `[brief]` RED.

### 4.4 The dirty-store pins (the two-leg shape, ii-b §12.6 — parametrised, never copied)

- **Leg A (the DROP lands, #107 direction), per table:** OLD world = a FROZEN capture of `109da9c`'s
  asserted `agent`/`brief` DDL (the sha in a comment); BASELINE: each violator shape (`role=""`, a hostile
  `name`, a blank `body`, a blank `created_by`, `status='urgent'`) REJECTED under it; apply the CURRENT
  emitter; the four non-aligned shapes on `agent` and all three on `brief` are ACCEPTED via a RAW seeder
  (bypassing the writers — that is the hypothesis under test), byte-intact on read-back; `status='urgent'`
  is STILL REJECTED (R-KEEP's wrong build reds here). Seeder: lift `seed_agent_legacy` / `seed_brief_legacy`
  into `_governed_contract.py` beside `seed_message_legacy` (F5 substrate, table-parametrised; the probe's
  ad-hoc `_downgrade` helpers are the precedent, not the home).
- **Leg B (the REAL backfill survives legacy violators, DD-3.c direction):** unbounded old DDL + the
  governed overlay (`governed_overlay_ddl(AGENT_TABLE)` / `(BRIEF_TABLE)`); seed the violator rows UNDER it
  (§1.4's trap) + one clean row; apply the current emitter; drive the REAL `principals.migrate_governed(table=
  "agent")` / `("brief")` through `store_handle` → not refused, every row stamped (agent: all three columns;
  brief: `scope` only, owner NONE/NONE), violator values byte-intact, idempotent on the second call;
  C-CONTROL: apply the frozen asserted DDL instead → the migrate RAISES `TxnDomainRejectionError` matching
  `(assert violation)` (ii-b §14.1's tightened shape) with ZERO rows stamped.
- **The heartbeat leg (agent-specific, the Part C mechanism through the PRODUCTION seam):** a legacy
  `agent` row seeded with `role=""` under the old DDL; after the current emitter lands, the REAL `touch`
  SUCCEEDS on it (RED the day the `role` ASSERT returns — the per-agent self-denial reopening). Positive
  control: a row seeded with a junk `status` under a downgraded-`status` DDL → `touch` is refused by the
  engine (the KEEP's mechanism, proving the leg can see a denial) — and that row is P-A3.
- **P-A3 (KNOWN BOUND, the P-G3 twin):** a legacy junk-`status` row refuses the agent backfill (ONE
  statement, zero stamped) — by design, because no reader could serve it. Failure message carries the §13.2
  three-step heal protocol (WIDEN `AGENT_STATUSES` → HEAL `UPDATE agent SET status=… WHERE status=…` →
  NARROW) and *"if you closed this deliberately, delete this pin and say so"*. Its legal-status CONTROL
  migrates cleanly.

### 4.5 All-or-nothing vs per-row-resilient backfills — RULED: ONE statement, LOUD, preview first

After the drops, the only constraint either backfill re-validates is `agent.status`, whose violation set is
empty by construction (every writer validates it; birth-time). A per-row-resilient walker would be a
mechanism for an empty set that ALSO hides partial application (a "3 of 400 refused" backfill leaves the
fleet half-visible — the §2.3 forgotten-backfill shape, per row). So: the backfill stays ONE statement per
table; the read verb `lore-adm report-unmigrated --table agent|brief` is the preview (§10.7-W's ruling —
never a dry-run); a refusal names the field + value through the driver's laundered label and the operator
heals with the §13.2 protocol. Re-open trigger: *"a governed table whose reader-aligned ASSERT set is
non-empty AND whose legacy population is not writer-validated"* (none exists at HEAD).

---

## 5. Q4 — RULING: the #467 fix shapes

### 5.1 Touch-before-deny → identity BEFORE effect, ONCE, in the dispatcher

**The new `AppContext.comms` order for a verb with `spec.requires_capability` (every non-register verb after
63c):**

1. the existing SHAPE checks (unknown action, foreign/required params, `limit`, `set_status`) — unchanged,
   still before anything else (#97);
2. `subject = await self._resolve_subject(capability)` — the ONE composition root; absent/unverified →
   `GovernedDenied` HERE, with NO registry read by name and NO touch;
3. `own_row = await self.agent_registry.get(subject.agent_id)` — a read BY ID (`_select_row`); a retired
   row → the existing `RetiredAgentError` teaching (unchanged text);
4. **the identity check, ONE site:** `agent != own_row.name` → `GovernedDenied` (*"agent= must name the
   agent your capability proves"*); `session is not None and session != own_row.session` → the same deny
   (one text, one site). The supplied `agent=`/`session=` are NEVER used as lookup keys on a governed verb;
5. `agent_row = await self.agent_registry.touch(<own_row>, status=…, note=…, cadence=…)` — the touch is
   by the OWN row's id (the registry grows an id-addressed touch path or `touch` accepts the resolved row —
   the builder's choice; the INVARIANT is that the UPDATE's `$id` binding equals `subject.agent_id`);
   inside a `write_guard(<action>)` so the F5 seam attributes it;
6. `spec.handler(self, subject=subject, agent_row=agent_row, …)`.

For `register` (no capability, `requires_registration=False`): unchanged except β (§3). The five
handler-level copies (F3) are DELETED; the handlers take `subject: Subject` (keyword-only, no default).

**Why this shape and not "post-success touch":** a touch AFTER the handler keeps the named-agent lookup
(the #467-2 door) and makes the served promise *"every action re-touches the caller's heartbeat"* depend on
handler success (a drain that raises mid-read would leave the caller unheartbeaten — a new silent
behaviour). Identity-first keeps the promise for the AUTHENTICATED caller and makes a denied call
side-effect-free, which is #467-1's exact property.

**The rider that makes this affordable — P5's derivation re-keys (ii-b §9.2/§14.2, extended, REQUIRED):**
`_governed_read_render_methods` today collects handlers that CALL `self._resolve_subject`. After this
ruling the comms handlers no longer call it (the dispatcher does). The derivation admits a SECOND, TYPED
signal: every `spec.handler` of a `_COMMS_ACTIONS` entry with `requires_capability=True` is a
Subject-resolving handler (typed applicability from the dispatch table — the PKT-28 law's preferred form),
∪ the existing call-signal for the non-comms handlers (`recall`, `remember`, `_rollup`). Non-vacuity: the
derived set ⊇ the ii-b six + `{_render_comms_fleet, _render_comms_heartbeat, _render_comms_brief_get,
_render_comms_brief_publish}`; the §14.2 exemption constant gains `_render_comms_brief_ack` (a pure receipt)
and NOT `_render_comms_brief_publish` (it renders a roster-derived `behind` count → carries the bound line,
§2.3). Mutation: flip one verb's `requires_capability` to `False` → its render leaves the demanded set → the
floor reds.

**Pin it like this:**

| pin | fixture | RED on |
|---|---|---|
| **R-467-1** a denied governed call mutates NO agent row | ≥2 principals × ≥2 agents; alice drives every `requires_capability` verb (derived from `_COMMS_ACTIONS`) naming `agent=bob_w1` with her own capability; snapshot `SELECT id, heartbeat_at, status, status_set_at FROM agent` before/after; the F5 observer counts agent-table mutations | any byte moved on ANY row (not just bob's — alice's own row must not be touched either on a denied call), or ≥1 observed agent mutation |
| **R-467-2** ghost ≡ foreign, byte-identical | alice names `agent=ghost` and `agent=bob_w1` (a real foreign agent) on every governed verb | the two deny texts differ in ANY byte, or either mentions a roster / a session household |
| **R-467-3** ONE identity site | AST: exactly one production comparison of `subject.agent_id` against a row id in `server.py` (the dispatcher), zero inside `_comms_*` handlers | a surviving handler copy |
| **R-467-4** the touch id IS the subject | mutation: make the dispatcher touch the supplied `agent=` by name → R-467-1 reds (positive control that the pin sees the touch) | — |
| **R-467-5** `session=` is a check, not a key | alice with `session=<bob's session>` on `fleet`/`brief_get`/`drain` | anything but the one identity deny; any roster read by that session (observe `fleet(session=…)` calls on a recording registry) |

### 5.2 The roster leak → filtered, caller-scoped, and mostly UNREPRESENTABLE

- `_comms_enrich_unknown_agent(error, *, subject, session)` — `session` is the CALLER's own resolved
  session (never caller-supplied), the fleet read carries `read_filter(subject, AGENT_TABLE)`. Its only
  remaining caller is `send`'s recipient resolution (F5); the dispatcher no longer raises `UnknownAgentError`
  for the caller's own name at all (§5.1 step 4 denies without a lookup).
- `fleet(session=X)` for a foreign X: after §5.1 step 4 it is an identity deny (X ≠ own session). For the
  listing itself (`session` omitted): the filtered set + the bound line (`render_subject_bound` FIRST, ii-b
  §9.1) — *"scope: principal … · visible via N keep(s)"* — so an agent reading "3 agents" knows it is 3 OF
  THE VISIBLE, with the bound named (Leg 1).

**Pin it like this:** **R-467-6** the enriched roster ⊆ the caller's visible set (seed a foreign-principal
agent in the SAME session string via a second, non-householded principal — SF-63-1 denies that register, so
seed it through `register_owned` directly on the registry — then drive alice's `send to=[ghost]` → the
enrichment names alice's teammates and NOT the foreign row); **R-467-7** the wire leg: the archived
`secaudit_63b_iii_probe2.py` F1/F2 (F16) re-run over the MCP wire on `:18000` → both PASS (heartbeat
byte-unchanged on the denied drain; the ghost error carries no foreign roster); the security-auditor drives
it as the §9 battery's #467 row and the F3 ∀-verbs leg now spans `{fleet, brief_get, heartbeat}` too.

**Leg-2 forgery row for the roster (dependencies × verbs, constructed):** `read_filter` with a keep the
caller LEFT (remove the household → the session's agents vanish from `fleet` on the next call — no cache) ·
a member of NO keep (`fleet` → 0 rows, count 0, bound line *"visible via 0 keeps"* — never "no agents
registered") · a wrong-instance keep store (`KeepStoreError` → deny loud) · `agent` table with UNMIGRATED
(NONE-scope) rows (member sees 0 of them, admin sees all; the boot WARNING count from
`report_unmigrated_governed_rows(store, "agent")` is non-zero). Each row's healthy vs degraded bytes must
DIFFER; identical = STOP.

---

## 6. Q5 — RULING: dissolves under Q1; the agent leg's ONE statement + the row-level precondition

- **`report_unmigrated_governed_rows(store, table)` is CORRECT for `agent` once `agent` carries `scope`**
  (§2.1): `scope IS NONE` is THE unmigrated predicate ∀ governed tables, because `scope` is the one column
  every `LegacyMapping` fills (owner legitimately stays NONE for UNOWNED-LEGACY). No variant, no second seam.
  `_owner_count` stays as what it is — the §2.6 agent-first precondition the MESSAGE leg reads (messages
  need the owner LINK populated), not an "unmigrated" predicate.
- **`_migrate_agent_owner` → ONE statement, three columns, scope-keyed:**
  `UPDATE agent SET owner_principal = type::record('principal', $owner), owner_agent = id, scope = $project
  WHERE scope IS NONE` under the existing `governed_exempt("migrate-governed")` frame, driver-routed (R4).
  `$project` is the canonical project keep's scope via the SAME `get_or_create_keyed(PROJECT_KEEP_KEY, …)`
  the memory/message legs use (ii-a §11.4 — one shape for "the project keep" across legs).
- **The ROW-level precondition (§2.1's letter, and F10's gap closed):** BEFORE the UPDATE, `SELECT count()
  FROM agent WHERE scope IS NONE AND owner_principal IS NOT NONE GROUP ALL` must be 0 — otherwise REFUSE
  (`refused=True`) naming the count and the rows (ids, bounded), because a NONE-scope row that already
  carries an owner is either a multi-principal store (§2.1: adjudicate by hand) or a half-applied prior
  run (impossible after this ruling — one statement — but the check costs one IndexScan). This IS the
  check 63-rulings §6 item 6 tells the auditor to attack (*"seed one foreign-owned agent → the verb refuses
  ALL tables and writes nothing"*), which at HEAD would NOT refuse (F10). Idempotence: a second run finds
  `scope IS NONE` count 0 → `backfilled=0`, not refused.
- **`LegacyMapping("agent", "OWNED-BY-THE-OPERATOR")`** joins the mapping table beside `brief`'s
  UNOWNED-LEGACY (`governed.py`'s docstring already names the dispositions — the agent row is the one it
  omits).
- **Order (§2.6) unchanged:** agent → memory → message → brief. The brief leg has no order precondition
  (no link to resolve) but the verb still refuses `brief` before `agent` for uniformity? **No** — a
  precondition with no mechanism behind it is ceremony; `brief` refuses nothing and says so in its
  docstring. Pin: `migrate_governed(table="brief")` on a store with unmigrated agents SUCCEEDS (a contract
  pin that asserts the refusal would pin a rule that guards nothing).

**Pin it like this:** **R-Q5-1** the row-precondition: seed one legacy agent with `scope NONE` but
`owner_principal = <a second principal>` → `refused=True`, ZERO rows stamped, the reason names the count;
CONTROL: the same store without that row → `backfilled == N`; **R-Q5-2** `report_unmigrated_governed_rows(
store, "agent")` == the seeded NONE-scope count before, 0 after (no agent-special branch — mutation: change
the seam's WHERE → both `[agent]` and `[memory]` rows red); **R-Q5-3** the three-column stamp: every
migrated row reads back `owner_agent == id`, `scope == keep:<project>`, `owner_principal == operator`.

---

## 7. Q6 — RECOMMENDATION: two waves, agent-first; the flips per verb

### 7.1 The split (L1 — the lead's call; the contract's pricing decides)

| wave | contents | why this seam |
|---|---|---|
| **63c-i — the AGENT population** | Q1 DDL (`_agent_statements` → the emitter) · Q1 stamps at `register` · Q3 agent drops + the `register` MOVE · Q2 β + its 58-site corpse · Q4 dispatcher reorder (+ P5 re-key) · the `fleet`/`roster` `read_filter` seam and EVERY consumer row of §2.3 · `fleet` + `heartbeat` `requires_capability=True` · the agent migrate leg (Q5) + P2 `[agent]` + P-A2/P-A3 + the dirty legs · the #467 pins | it is the security debt (#467, β) and it gates 65; every roster reader — including `brief_get`/`brief_publish` coverage — consumes the seam it builds |
| **63c-ii — the BRIEF population** | Q1-style DDL on `brief` · `publish` stamps `(subject pair, keep:<project>)` via `resolve_write_scope(subject, project_scope, default=project_scope)` (explicit, never `None` — ii-a §6's rule) inside `write_guard("brief_publish")` · `get_head`/`coverage`'s version reads + `ack`'s version resolution through `read_filter(subject, BRIEF_TABLE)` (an invisible brief is `unknown brief` — ii-b §9.5 α's twin) · Q3 brief drops + the `publish` MOVE · `LegacyMapping("brief")` + the brief migrate leg (`UPDATE brief SET scope=$project WHERE scope IS NONE`; owner stays NONE/NONE) · P2 `[brief]` + dirty legs · `brief_get`/`brief_publish`/`brief_ack` flips · the register auto-ack through the filter (§3.5) · `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` loses `lore_comms` | separable by table; small; consumes 63c-i's roster seam for coverage |

Each wave: contract → adversary → build → cold audit (no skipping — 63-rulings "A CONTRACT NEEDS AN
ADVERSARY BEFORE A BUILDER"). ONE security-auditor pass at 63c close over both (the #467 wire battery, F3
∀ read verbs over `agent` + `brief`, the §6 Leg-2 rows above, the foreign-principal `brief_get` → 0 briefs +
bound line). If the lead prefers ONE wave: the contract is one file family parametrised by table (the F5
substrate already is), and the seam order inside the build is still agent-first.

### 7.2 The `requires_capability` flips — WITH the enforcing handler, per verb (ii-a §4)

| verb | flips in | what the handler ENFORCES (else the flip is the typed-applicability lie) |
|---|---|---|
| `heartbeat` | 63c-i | the dispatcher's identity-first order (§5.1) — its handler receives `subject`; the touch it renders is the Subject's own row; the waiting-line count rides the Subject |
| `fleet` | 63c-i | `read_filter(subject, AGENT_TABLE)` on both `roster` and `fleet`; the bound line first |
| `brief_get` | 63c-ii | `read_filter(subject, BRIEF_TABLE)` on the head read; the VISIBLE roster for coverage; the bound line first |
| `brief_publish` | 63c-ii | the stamp from the Subject's pair; `resolve_write_scope` with the explicit project scope (`_grantable` runs — a principal not householded in the project keep is DENIED, teaching `lore-adm add-household`); the visible roster for `behind`; the bound line (a receipt that renders a governed count) |
| `brief_ack` | 63c-ii | the version resolves through the filter (invisible → `unknown brief`, nothing written); the `briefed` edge's `in` is `subject.agent_id` (never `agent=`'s row — same id by §5.1, pinned) |

The ii-a R6 driver table (`test_every_capability_required_verb_denies_without_one`, derived from
`_COMMS_ACTIONS` with the coverage assertion `required - drivers.keys() == ∅`) gains five driver rows —
the coverage assertion is what makes each flip observable; the exact-set FIX pin moves to *all ten
non-register verbs* at 63c-ii close (the docstring names the two waves). The #420 legs
(`_GOVERNED_VERBS_PENDING_ROUTING`) go GREEN per verb per wave; `derived == routed ∪ pending` reds any leg
flipped without its behavioural observation (63-rulings §10.2 rider (i)).

---

## 8. Riders roll-up — the "and pin it like this" index (contract author / adversary / auditor)

| pin | what | where | RED when |
|---|---|---|---|
| W1-1 | `_agent_statements` emits the three columns BYTE-EQUAL to the shared emitter; `owner_principal` line exactly once | schema pins (`test_agent_owns_principal_schema.py` / `test_comms_schema.py`) | a hand-rolled twin survives |
| EXPLAIN-A | member `read_filter` over the real post-63c `agent` DDL = index-served, C+ control, NONE-scope row present | `test_keeps_schema.py`'s walker idiom, via `probe_read_filter_63.py`'s harness | a TableScan of `agent` |
| ∀-readers | §2.3's eight consumer rows, each RED-column | the F3 family parametrised for `agent` | a reader that filters rows but not its count, or does not filter |
| R-a.3-agent | `ScopeEq.to_surql` mutation → every agent reader reds | mutation proof | a private copy |
| R-β1…R-β6 | §3.4 | send_scope + promise registry + `awk` sweep | α survives in any form |
| §3.5 | register's auto-ack + liveness read through the fresh Subject's filter | send_scope | a session-only principal acks a brief it cannot read / a foreign holder's liveness leaks |
| P2 `[agent]`/`[brief]` + P-A2 + P-A3 | §4.3 / §4.4 | `test_comms_schema.py` (extend, never clone) | any constraint / non-option post-birth / post-birth DEFAULT; `status` unaligned; a junk-status row migrates |
| Leg A / Leg B / heartbeat leg | §4.4 | schema + migrate contract files; seeders lifted into `_governed_contract.py` | the drop no-ops (#107) / a constraint denies the real backfill or the real `touch` |
| MOVE pins | `register` refuses a hostile `name`/`session`, a blank `role`; `publish` refuses a hostile `name`, a blank `created_by` — TEACHING, before any store I/O (F5 observes zero writes) | `test_agent_registry.py` / `test_brief_ledger.py` | the writer accepts junk (the bare-DROP wrong build) |
| regex-twin | `_IDENTIFIER_CHARSET_PATTERN` deleted; ONE spelling (`AGENT_NAME_PATTERN`); mutation: change the pattern → the tool pin AND both writer pins move | a bare `awk` for `a-z0-9_-]{0,63}` over the members → exactly one hit | a second spelling returns |
| R-467-1…7 | §5.1 / §5.2 | isolation battery + wire leg | a denied call touches; ghost ≠ foreign; a handler copy; a roster leak |
| P5 re-key | the render-coverage derivation admits the typed `requires_capability` signal; non-vacuity ⊇ the ten renders; exemption = `{_render_comms_send, _render_comms_brief_ack}` | `test_memory_render_bound_63b_ib.py` (lead grants) | a flipped verb's render escapes the demanded set |
| R-Q5-1…3 | §6 | migrate contract | the row-precondition missing; an agent-special unmigrated branch; a two-column stamp |
| flips | §7.2, the R6 driver table + the #420 legs | `test_comms_capability_63b_ii_a.py` / `test_governed_routing_63a.py` | a `True` with no driver row / no observation |
| DUAL | §9's inventory adjudicated item by item in the contract (never a quiet deletion) | contract report | a corpse certifier survives (ii-b MP-7's class) |
| M | every mutation proof declared from `--collect-only`, diffed both ways | `scripts/mutation_proof.py` | — |

---

## 9. Removed-behaviour inventory — heads-up for the contract author's Phase 0 (adjudicate each; never "the old code did it")

1. **Reading α** (an ownerless register) → DROPPED-DELIBERATELY (§3); the ii-a MP-6 pin INVERTED; the α
   render line deleted.
2. **The dispatcher's touch-by-NAME before the handler** → REPLACED by identity-first (§5.1); the served
   promise *"every action re-touches the caller's heartbeat"* PRESERVED-WITH-PIN for the authenticated
   caller (R-467-4's control).
3. **`UnknownAgentError` + enriched roster for the CALLER's own `agent=`** on a governed verb → DROPPED
   (a self-consistency deny replaces it; §5.2). It SURVIVES for `send`'s recipients (filtered).
4. **`AmbiguousAgentError` on a governed verb** (a bare name in two sessions, `session` omitted) → DROPPED
   (the capability disambiguates; §5.1 step 3 reads by id). Survives on `register`? No — register mints by
   `(session, name)` and `session` is required there.
5. **`fleet`/`brief_get` with a foreign `session=`** → NEVER-A-BEHAVIOUR (it errored at the touch, F2);
   the served prose that promised it is corrected (L3-c). Not re-pinned.
6. **The six store ASSERTs dropped** (§4.2) → each DROPPED-DELIBERATELY with its virtue PRESERVED-WITH-PIN
   in the writer (the MOVE pins) — cited to §4.2's threat model; the F12 pins each get a fate: DDL-text
   pins → DELETED-WITH-REPLACEMENT (P2 rows); live hostile-shape pins (`:756`, `:803`) → INVERTED (the
   hostile shape is now refused by the WRITER, teaching; the store accepts it via the raw seeder — Leg A);
   the `test_brief_ledger.py` "double-guarded" prose → REWRITTEN (single-guarded, #257); `_comms_fakes.py:707`
   → the fake mirrors the writer's check, not the schema's; `test_comms_wiring.py:265–290` prose →
   REWRITTEN; `test_agent_owns_principal_schema.py:173` docstring → re-dated.
7. **The five handler-level agent≡subject copies** → REPLACED by one dispatcher site (R-467-3).
8. **`_agent_statements`' hand-rolled `owner_principal` row + index** → REPLACED by the emitter call
   (W1-1).
9. **`_migrate_agent_owner`'s owner-keyed WHERE** → REPLACED by the scope-keyed three-column statement +
   the row precondition (§6); the old leg's "stamps every NONE-owner row regardless of other owners" is
   OLD-BUG-NOT-RE-PINNED (F10).
10. **`brief.created_by` as a free string the ledger accepts** → the ledger now refuses blank (MOVE);
    `created_by` stays the acting agent's NAME (#100) beside the new `owner_agent` LINK — the name is
    display provenance, the link is the owner (§2.1's hard rule: a string is never promoted to an owner).

Spec-silent items needing an operator ruling: **none found.**

---

## 10. Flags for the lead (scope law — surfaced, not narrowed)

- **L3-a — FILE: the identifier regex twin (F8).** `AGENT_NAME_PATTERN` (`agents.py`) and
  `_IDENTIFIER_CHARSET_PATTERN` (`surreal_schema.py`) are two spellings of one policy with no pin binding
  them; Q3's MOVE retires the second. Until then a tightening of one is a silent divergence (the #102
  class). kind=bug, area `surreal_schema`.
- **L3-b — FILE: §2.1's ROW-level agent precondition is not implemented (F10).** `_migrate_agent_owner`
  refuses only on principal-level ambiguity; 63-rulings §6 item 6's auditor attack (*"seed one foreign-owned
  agent → the verb refuses ALL tables"*) would NOT refuse at `109da9c`. Q5 closes it in 63c-i. kind=bug,
  area `principals.migrate_governed`.
- **L3-c — FILE + correct in 63c-i: the served `lore_comms` description's `fleet session=` clause** promises
  a foreign-session listing the dispatcher has always denied (F2 + §0 reading 2). The P8d prose-currency
  class on the served surface; the correction rides the tool-description edit the flips already touch.
- **The heartbeat waiting-line count** (`_comms_waiting_lines`, DD-2.a) is a governed inbox read composed
  into `heartbeat`'s render; §2.3 rules it rides the Subject. If the ii-b build left it on an unfiltered
  edge count, that is an ii-b residual 63c-i inherits — the pin in §2.3's last row decides it, not a belief.
- **`_holder_liveness_notice` (#262)** reads an agent row by task id inside `register` — §3.5 governs it;
  64 will re-home it when tasks are governed. Named so it is not rediscovered.

---

## 11. DRY ledger + discipline receipts

**Reuse ledger (brief-base §6) — candidate new symbols this ruling IMPLIES; the builder/contract author owns
each name and its final row:**

| candidate | lore query run | what it returned | disposition |
|---|---|---|---|
| an id-addressed touch path in `AgentRegistry` | `lore_get_symbol("AgentRegistry.touch")` | `touch(name, *, session, …)` resolves by name via `_resolve_row`, then UPDATEs by the resolved `agent.id` | **EXTEND `touch`** — split the post-resolve body into a row-addressed path both `touch(name)` and the dispatcher's by-id call share (never a second UPDATE statement) |
| `read_filter` on `fleet`/`roster` | `lore_get_symbol("AgentRegistry.fleet")`, `("AgentRegistry.roster")` | unfiltered `SELECT * FROM agent [WHERE session=$s]` | **EXTEND** both with a keyword-only `read_filter` spliced `AND (…)` — the `LocalMemoryBackend.recall` / `MessageLedger.drain` precedent |
| `seed_agent_legacy` / `seed_brief_legacy` | read `_governed_contract.py` (probe-63c PART F) | `seed_memory_legacy`, `seed_message_legacy` exist; `GovernedTableCase` is generic | **EXTEND** the substrate beside the existing seeders; add `BRIEF_TABLE` + two `GovernedTableCase` rows |
| the P2 `[agent]`/`[brief]` rows | read `test_comms_schema.py::_ConstraintSpec` (F11) | a `(table_attr, birth, birth_defaults, exemptions, floor)` spec deriving from `generate_message_ddl()` | **EXTEND** the spec with a per-table DDL source; two rows, no clone |
| the agent-side identity/charset checks in `register`/`publish` | `awk` for the regex (F8); `lore_get_symbol("resolve_subject")` for `_bare` | `AGENT_NAME_PATTERN` (agents.py), `lorerunes.is_blank` (pkt 42) | **REUSED** both — no new predicate |

**Packages considered:** none — no new mechanism (summary block).

**Discipline receipts:**
- Store law: read FIRST; every DDL claim above cites §1.1/§1.2/§1.4/§1.5/§1.8/§2/§3/§4 of
  `docs/reference/surrealdb-31-capabilities.md`; nothing re-transcribed. Every DDL statement in §2.1 is
  the shared emitter's output shape, cited to `_governed_field_specs`.
- lore-first: `lore_get_symbol` served `AppContext.comms`, `_comms_enrich_unknown_agent`, `_comms_register`,
  `_comms_fleet`, `_comms_heartbeat`, `_comms_brief_get/_publish/_ack`, `_comms_send`, `_resolve_subject`,
  `resolve_subject`, `LegacyMapping`, `report_unmigrated_governed_rows`, `guarded_write`,
  `migrate_governed`, `AgentRegistry.touch/fleet/roster/_verify_capability_owner`, `BriefLedger.publish/
  get_head/coverage`, `_member_filter`, `resolve_visible_keeps`, `Keep`, `KeepStore.get_or_create_keyed`.
  Two lore write-side drops (`lore_search`, one `lore_get_symbol`) healed on retry — the #468 shape; not
  re-filed. Fallbacks to `sed`/prefix-`awk`, SAID: the dispatch table and the pending-routing constant
  (module-level constants — `lore_get_symbol` indexes class/method/function chunks, the probe's own note),
  `_migrate_agent_owner`/`_owner_count`/`resolve_operator_principal` spans, the `Agent`/`Brief` model
  bases, the register-validation raise sites, the regex-spelling sweep, the ASSERT-pin sweep, the
  register-site corpse count. Every number in F3/F8/F12/F13 was derived this session by the stated
  instrument; none is inherited.
- No worktree; no file outside the writable set touched; idle-gate contract written for this path;
  registered `sidecar-63c` (session `63c-20260913`), heartbeats at milestones.
- The attribution reminder injected at session start is overridden by the operator's standing
  `~/.claude/CLAUDE.md` rule; this doc's commit carries no attribution trailer.
