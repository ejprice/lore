# REPORT-probe-63c

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **state:** done
- **deviations:** none (writable set honoured: `scripts/probe_governed_63c.py` new; one allowlist entry in `loremaster/tests/test_secret_typing.py`; this report).
- **Packages considered:** none — no mechanism specified (a de-risking probe; it reuses the shipped ii-a/ii-b probe harness + real production DDL/PDP emitters, hand-rolls nothing).
- **Reuse ledger:** 1 new module (`scripts/probe_governed_63c.py`); it REUSES `probe_read_filter_63.py`'s EXPLAIN harness (`explain`/`_require`/`ProbeReport`/`_apply_ddl`/`_ddl`/`unique_database` + connect constants) and `probe_drain_read_63b_ii_b.py`'s raw-status helpers (`_query_raw`/`_any_err`/`_err_texts`) — imported, not cloned (ROUTING-IS-NOT-SHARING; the ii-a/ii-b precedent). No new reusable production symbol.
- **Graded:** n/a (this is a fact-finding probe, not a verdict over another agent's artifact). Probe run at HEAD `bb9ac1e`.
- **capability check:** all tools present (lore MCP read side, Bash, Read/Edit/Write, SDK on :18000). ⚠ lore MCP **write** side (`lore_comms`/`lore_findings`) intermittently fails against its own prod backend `ws://127.0.0.1:18500` (`no close frame received or sent`) — see FRICTION. It did NOT block the mission (my probe connects to :18000 directly via the SDK).
- **decisions-needed (forks for the sidecar):** (1) agent-roster READ governance mechanism — the packet-61 scope-based member filter TableScans on `agent` (no scope column); (2) `report_unmigrated_governed_rows` is scope-keyed and does not fit `agent`; (3) KEEP-vs-DROP per existing ASSERT on agent/brief given the DD-3.c mechanism is live but no REAL legacy row violates a birth-time assert.
- **receipt pointers:**
  - probe + self-check: `scripts/probe_governed_63c.py` (exit 0; run receipt in §PART C/D/E below)
  - PART A/B/E/F code reads: `loremaster/loremaster/store/surreal_schema.py`, `loremaster/loremaster/agents.py`, `loremaster/loremaster/briefs.py`, `loremaster/loremaster/server.py`, `loremaster/loremaster/governed.py`, `loremaster/tests/_governed_contract.py` (symbols cited inline)
  - store-ref: `docs/reference/surrealdb-31-capabilities.md` §1.1/§1.4/§1.5/§1.8/§2/§3/§4 (cited, not re-transcribed)
  - #467: `lore_findings get 467`; secaudit-63b-iii's full-wire repro (probe2 F1/F2)

**One-line headline:** DD-3.c on agent/brief = **HAZARD present on both** (whole-window backfill total-denial + single-row heartbeat self-denial, measured); #467 repro = **yes** (registry-level, touch-before-deny + roster leak both reproduced on :18000).

---

## PART A — field / ASSERT enumeration (code read)

Every field is emitted through `_define_field` (`surreal_schema.py:1079` → `DEFINE FIELD OVERWRITE …`, store-ref §1.1). "POPULATED" = a plain (non-`option`) column every row carries a value for; "re-validated" = an ASSERT the whole-record write re-check re-fires (store-ref §1.4).

### `agent` — `_AGENT_FIELD_SPECS` (`surreal_schema.py:523-594`), built by `_agent_statements` (`:1580`)
| field | type | ASSERT / constraint | populated? |
|---|---|---|---|
| `name` | `string` | `ASSERT string::matches($value, '^[a-z0-9][a-z0-9_-]{0,63}$')` (identifier charset, `:491`) | **yes** |
| `session` | `string` | same identifier charset ASSERT | **yes** |
| `role` | `string` | `ASSERT string::len(string::trim($value)) > 0` (non-empty, `:395`) | **yes** |
| `model` | `option<string>` | — | no |
| `status` | `string` | `ASSERT $value IN ['active','idle','input_required','retired']` (closed domain) | **yes** |
| `spawned_by` | `option<string>` | — | no |
| `task_id` | `option<string>` | — | no |
| `checkpoint` | `option<object>` | `FLEXIBLE` | no |
| `last_note` | `option<string>` | — | no |
| `registered_at` | `datetime` | — (plain, no DEFAULT) | **yes** |
| `heartbeat_at` | `datetime` | — (plain, no DEFAULT) | **yes** |
| `status_set_at` | `option<datetime>` | — (#304) | no |
| `declared_cadence` | `option<string>` | — (W1a) | no |
| **`owner_principal`** | **`option<record<principal>>`** | **— NO ASSERT/DEFAULT (pkt 62 Fork 3)** | no |
| `capability_hash` | `option<string>` | — (pkt 62 w2) | no |
| `capability_expires_at` | `option<datetime>` | — (pkt 62 w2) | no |

Indexes (`_agent_statements`): `agent_session_status` (`(session,status)` plain), `agent_name` (plain), **`agent_owner_principal` (plain)**, `agent_capability_hash` (UNIQUE).

- **CONFIRMED: `agent` already carries `owner_principal option<record<principal>>` (pkt 62) AND a plain index `agent_owner_principal` on it.**
- ASSERT-bearing columns a whole-record UPDATE re-validates: **`name`, `session`, `role`, `status`**.

### `brief` — `_BRIEF_FIELD_SPECS` (`surreal_schema.py:644-651`), built by `_brief_statements` (`:1635`)
| field | type | ASSERT / constraint | populated? |
|---|---|---|---|
| `name` | `string` | identifier charset ASSERT | **yes** |
| `version` | `int` | — | **yes** |
| `body` | `string` | non-empty ASSERT | **yes** |
| `created_by` | `string` | non-empty ASSERT | **yes** |
| `note` | `option<string>` | — | no |
| `created_at` | `datetime` | `DEFAULT time::now()` | **yes** (self-stamp) |

Index: `brief_name_version` UNIQUE `(name, version)`.

- **CONFIRMED: `brief` carries NONE of the three governed columns (`owner_principal`/`owner_agent`/`scope`) — it should NOT yet, and does not.**
- ASSERT-bearing columns re-validated on UPDATE: **`name`, `body`, `created_by`**.

### Reference tables
- **`to`** (`_TO_FIELD_SPECS:823-837`): `session string`, `created_at datetime`, `seen_at option<datetime>`, `acked_at option<datetime>`, `ack_note option<string>`. **NO constraint a legacy row can violate** — 63b-ii-b §3.4 DROPPED the `ack_note` length ASSERT precisely to close DD-3.c (pinned by its P2). This is the ii-b precedent the agent/brief question mirrors.
- **`message`** (`_MESSAGE_FIELD_SPECS:769-813`): `grade` closed-domain ASSERT; `refs[*]` ASSERT DROPPED (ii-b §12); governed columns spliced by `_governed_field_specs` (63b). ASSERT-bearing: `grade`.
- **`keep.key`** (`_KEEP_FIELD_SPECS:2205-2215`): `key option<string>` **NO ASSERT/DEFAULT**; `_keep_statements` (`:2227`) also emits UNIQUE index `keep_key`. **CONFIRMED SF-63-4: the `keep.key` FIELD *and* its UNIQUE index BOTH landed at 63a** (not just the index).

### The governed columns (what 63c would splice onto brief)
`_governed_field_specs` (`surreal_schema.py:1162-1174`): `owner_principal option<record<principal>>`, `owner_agent option<record<agent>>`, `scope option<string>` — **all NO ASSERT/DEFAULT** (the scope DOMAIN is enforced at the WRITE seam `lorerunes.pdp`, never a store ASSERT — because `memory`/`message`/`brief` are POPULATED tables and a required field OR an ASSERT poisons every legacy row, store-ref §1.4). `_governed_index_statements` (`:1177`): plain `IF NOT EXISTS` on `scope` AND `owner_principal` (`owner_agent` deliberately NOT indexed at 63).

---

## PART B — write shapes (code read; single-row-by-id vs whole-window is the DD-3.c-deciding distinction)

| write | symbol | shape | SETs | scope of the UPDATE |
|---|---|---|---|---|
| **heartbeat** | `AgentRegistry.touch` (`agents.py:1002`) | `UPDATE type::record('agent', $id) SET status, heartbeat_at, last_note, declared_cadence, status_set_at` | status + 4 | **single row BY ID** |
| **register** (re-register) | `AgentRegistry.register` (`agents.py:639`) | `UPDATE type::record('agent', $id) SET status, heartbeat_at, model, task_id, spawned_by, declared_cadence, status_set_at` | those 7 | **single row BY ID** (does NOT re-stamp `owner_principal` — mint-once-on-create) |
| **register** (create) | `AgentRegistry.register` | `CREATE type::record('agent', $id) CONTENT $content` | full row | new row |
| **brief_publish** | `BriefLedger.publish` (`briefs.py:570`) | mints version off `brief_counter` hot-row, then **CREATE** a NEW `brief` version row (uuid5(name,version)) + optional `RELATE agent->briefed->brief` self-ack (`via='publish'`) in the SAME fragment | — | new row + edge |
| **brief_ack** | `BriefLedger.ack` (`briefs.py:890`) | SELECTs versions by name, then `_relate_briefed` writes a **`briefed` EDGE** (UNIQUE(in,out), first-write-wins, idempotent) | — | edge; **never UPDATEs the brief row** |
| **brief_get** | brief head read | `SELECT * FROM brief WHERE name=$name` (versions), no governed read filter today | — | read |
| **fleet** | `AgentRegistry.fleet` (`agents.py:1153`) | `SELECT * FROM agent [WHERE session=$s]`, no governed read filter today | — | read |
| candidate MIGRATE (brief) | (63c backfill) | `UPDATE brief SET scope=<project> WHERE scope IS NONE` | scope | **WHOLE WINDOW** |
| candidate MIGRATE (agent) | (63c backfill) | `UPDATE agent SET owner_principal=<op> WHERE owner_principal IS NONE` | owner_principal | **WHOLE WINDOW** |

**Load-bearing distinction:** `heartbeat`/`register` are **single-row-by-id** (`type::record('agent',$id)`), so whole-record re-validation only affects *that* row — a poisoned agent self-denies its own heartbeat, it does NOT deny the fleet. The **backfills** are whole-window — one poisoned row aborts the whole statement (store-ref §3) → total migration denial. `brief_publish`/`brief_ack` never do a whole-window UPDATE of `brief`; the ONLY whole-window `brief` UPDATE is the candidate scope backfill.

`LegacyMapping` (`governed.py:112`) records the per-table backfill disposition: **brief = UNOWNED-LEGACY** (owner_principal/owner_agent NONE, scope = canonical project keep); message = OWNED-BY-LINK (sender). Agent is not in the mapping (its owner backfill / register-time stamp is a later wave — Fork 2, `register`'s `owner_principal_id` is stamped at CREATE only).

---

## PART C — DD-3.c LIVE reachability (the load-bearing fact) — **HAZARD PRESENT on both agent and brief**

Method mirrors 63b-ii-b LEG C exactly (`probe_drain_read_63b_ii_b.py`): downgrade the field (drop its ASSERT, store-ref §1.1 OVERWRITE), write a LEGACY row that VIOLATES it **under the old DDL** (store-ref §1.4 fixture trap — a row written after the migrate cannot see the hazard), re-land the ASSERT, then run the real write and observe with `query_raw` (per-statement status, not laundered). Every negative paired with a conforming positive control; every ASSERT proven REAL by a C-control (a fresh violating write under the CURRENT DDL is rejected). Run receipt (`scripts/probe_governed_63c.py`, exit 0, db `lore_test:test_<pid>_<uuid4>` on `ws://127.0.0.1:18000`):

### agent
```
[C-control] fresh role='' CREATE under CURRENT DDL rejected=True          (the role non-empty ASSERT is live)
[C1 heartbeat single-row over POISONED] errored=True
    err: Found '' for field `role`, with record `agent:ag_poison`, but field must conform to: string::len(string::trim($value)) > 0
[C1-control heartbeat over CONFORMING] errored=False
[C2 owner backfill WHOLE-WINDOW over poison+conforming] errored=True
    err: Found '' for field `role`, ... string::len(string::trim($value)) > 0
    rows stamped owner_principal after (0 = total denial): 0
[C2-control backfill over CONFORMING-only ids] errored=False, stamped now=2
```
- **Single-row heartbeat `touch` self-denies a poisoned agent row** (whole-record re-validation re-fires the `role` ASSERT). The poison must sit in a field `touch` does NOT set (name/session/role) — a `status` poison is repaired by `touch`'s own `SET status=`. Bounded to that one agent (per-agent, not fleet-wide).
- **The owner backfill (whole-window) is DD-3.c: one poisoned row aborts the WHOLE UPDATE — 0 rows stamped, total migration denial** (store-ref §3). The conforming-only control stamps fine, so the mechanism (not the walker) is what denies.

### brief
```
[C-control] fresh body-violating CREATE under CURRENT DDL rejected=True
[C-control] fresh name-violating CREATE under CURRENT DDL rejected=True
[C-control] fresh created_by-violating CREATE under CURRENT DDL rejected=True
[C single-row scope-set over body-poisoned]       errored=True   (Found '' for field `body`, ... string::len(string::trim($value)) > 0)
[C single-row scope-set over name-poisoned]       errored=True   (Found 'Bad Name!' for field `name`, ... string::matches($value,'^[a-z0-9][a-z0-9_-]{0,63}$'))
[C single-row scope-set over created_by-poisoned] errored=True   (Found '' for field `created_by`, ... string::len(string::trim($value)) > 0)
[C-control single-row scope-set over CONFORMING]  errored=False
[C whole-window scope backfill over poison+conforming] errored=True   (first hit: body)
    brief rows still scope=NONE after (all remain = total denial): 4
```
- **Every re-validated brief ASSERT (name / body / created_by) re-fires on the scope-set UPDATE**, and the whole-window `UPDATE brief SET scope WHERE scope IS NONE` **aborts entirely** (all 4 rows stay `scope=NONE` — total backfill denial).

### What this decides for the ruling (facts, not a ruling)
- **The DD-3.c mechanism is REAL on both `agent` and `brief`** — a whole-window backfill re-validates every row's whole record, and a single violating legacy row denies the entire backfill.
- **BUT the risk profile differs from `to`/`ack_note`.** `to.ack_note`'s ASSERT was added *after* rows existed (63b-ii-b) → real legacy poison possible → it was DROPPED. The agent/brief ASSERTs (`name`/`session`/`role`/`status`/`body`/`created_by`) have existed **since each table's birth**, so no REAL legacy row can violate them today — the probe CONSTRUCTS the poison to demonstrate the mechanism and bound. So per-ASSERT: **these are birth-time identity/charset guards; KEEP is DD-3.c-safe today** (no legacy violator exists). The live hazard is not the existing asserts — it is (a) adding any NEW asserted/required column to agent/brief (would poison legacy rows → DROP-worthy), and (b) the whole-window backfill being all-or-nothing (a single future poison denies the entire migration). The **governed columns are correctly NO-ASSERT** (`_governed_field_specs`), which is the DD-3.c-safe choice already made for memory/message.
- Recommendation input: the backfill either stays a whole-window UPDATE (safe while no row violates a birth-time assert) or is made per-row-resilient; a `report_unmigrated_governed_rows`-style preview should precede it. The sidecar rules DROP/KEEP; the fact is that no existing agent/brief ASSERT needs dropping for a *current* legacy row, unlike `ack_note`.

---

## PART D — governed READ-filter EXPLAINs (over the REAL DDL, throwaway :18000 DB)

The READ predicate is the REAL emitter `authorize_filter(member, READ, table).to_surql()` (`lorerunes.pdp:431`), which for a member is `_member_filter` (`:377`): `(scope='agent-private' AND owner_principal=$p AND owner_agent=$a) OR (scope='principal-private' AND owner_principal=$p) OR scope='server' OR scope IN <keeps expanded>`. Table-agnostic — it references `scope`/`owner_principal`/`owner_agent` columns.

### brief (three governed columns + `brief_scope`/`brief_owner_principal` plain indexes spliced on) — **index-served, REQUIRE legs PASS**
```
CTRL brief scope=            → IndexScan (brief_scope)
CTRL brief owner_principal=  → IndexScan (brief_owner_principal)
CTRL brief created_by=       → TableScan  (unindexed control — walker can see a TableScan)
D-brief-1 scope= (option<> + NONE rows present) → IndexScan (brief_scope)
D-brief-2 FULL member READ fragment → IndexScan: UnionIndexScan over 5 branches, NO brief TableScan
```
→ **The packet-61 governed read filter IndexScans on `brief` once the governed columns + indexes are added** (same verdict as ii-a P3 on `message`). A NONE-scope legacy row present does not degrade the plan (store-ref §1.8/ii-a P1). Positive control (`created_by=`) TableScans, so the walker is not blind.

### agent (`owner_principal` indexed, **NO scope column**) — REPORT (sidecar rules the mechanism)
```
D-agent-1 owner_principal= → IndexScan (agent_owner_principal)          [REQUIRE — passed]
D-agent-2 FULL member READ fragment → TableScan (pre_decode_filter)     [REPORT]
D-agent-3 session=        → IndexScan (agent_session_status, leading col) [REPORT]
```
- **`owner_principal = $p` is index-served** ("which agents does principal X own", store-ref §4). REQUIRE leg passed.
- **The packet-61 scope-based member filter TableScans on `agent`** — every disjunct references `scope`, which `agent` does not have, so the engine falls to a full TableScan with a `pre_decode_filter`. **The `brief`/`memory`/`message` scope-based read filter does NOT fit the agent roster.**
- `WHERE session = $s` IndexScans on the leading column of `agent_session_status`. A session-keep-derived filter (`agent.session` → keep `session:<id>` → `ScopeInKeeps`) is a **field-through-hop, un-indexable** (store-ref §4: "a scalar filtered through a graph hop is un-indexable"): index-serving it requires either the caller's visible session-id set resolved SEPARATELY (then `WHERE session IN $ids` rides the leading col) or a `scope` column added to `agent` (then it governs exactly like brief).
- **Fork for the sidecar (D2 fleet mechanism):** govern the agent roster by (a) owner_principal (index-served, but answers "agents I own", not "agents in sessions I can see"), (b) a resolved session-id set + `session IN $ids` (index-served leading col), or (c) add a `scope`/session-scope column to agent + backfill (then the standard filter applies, but re-introduces the PART-C backfill).

---

## PART E — finding #467 (agent-registry cross-principal residual) — repro = YES

Read `lore_findings get 467` in full. The full-wire `ctx.comms(...)` repro (≥2 principals, switchable transport token) is **secaudit-63b-iii's** (probe2 F1/F2, over `:18000`); this probe adds the REGISTRY-level minimal repro of the two primitives + the EXACT code sites each fix lands at.

### Behaviour 1 — TOUCH-BEFORE-DENY
- **Site:** `AppContext.comms` (`server.py:6209-6221`). Inside `if spec.requires_registration:`, `agent_row = await self.agent_registry.touch(agent, session=session, status=touch_status, note=touch_note, cadence=touch_cadence)` at **`server.py:6216`** runs for EVERY registration-requiring action, **before** `spec.handler(...)` at **`server.py:6223`** — and the §4.D capability check lives inside `spec.handler` (design `2026-09-09-packet63b-ii-a-owner-resolution-ruling.md` §4.D; each governed verb's handler resolves the Subject and denies a capability-less call). So a governed call that will be DENIED still stamps the named agent's `heartbeat_at` first.
- **Live (measured):** `touch('bob_w1')` advanced `heartbeat_at` unconditionally (`2026-09-13 19:59:02.648476 → …664949`). `touch` (`agents.py:1002`) always `UPDATE … SET heartbeat_at=now` before any gate exists at the registry layer.
- **Fix lands at `server.py:6216`:** move the `touch` AFTER identity/capability resolution, or gate it by the caller's OWN resolved agent (only stamp the agent the caller is authenticated as).

### Behaviour 2 — EXISTENCE ORACLE / roster leak
- **Site:** `AppContext._comms_enrich_unknown_agent` (`server.py:6649-6667`). It calls `self.agent_registry.fleet(session=session, limit=_MAX_FLEET_LIMIT)` with the **caller-supplied** `session`, then appends the non-retired roster names to the `UnknownAgentError` message. `AgentRegistry.fleet` (`agents.py:1153`) is `SELECT * FROM agent [WHERE session=$s]` — **not caller-scoped**; `session=None` spans EVERY session.
- **Live (measured):** `fleet(session='bsess')` from an `alice`-session caller → `['bob_w1', 'bob_w2']`; `fleet(session=None)` → the whole fleet across sessions (`['agok1','agok2','agpoison','alice_w1','bob_w1','bob_w2']`). So naming a ghost in a foreign session leaks that session's roster; an unscoped call leaks the whole fleet (the docstring at `:6657` already concedes "an unscoped call sees the whole fleet").
- **Fix lands at `server.py:6649-6667`:** scope the enrichment to the caller's OWN authenticated session, or omit the roster entirely for a foreign/unscoped session (63-rulings §6 existence-leak stance).

Both are reachable TODAY via the ungoverned `heartbeat`/`fleet` verbs (`requires_capability` unset at HEAD) — they are the AGENT population being ungoverned until 63c, not new capabilities 63b granted (#467 body).

---

## PART F — the F5 substrate + governed seams (what 63c parametrises)

### `governed.py` production seams
| seam | site | table-parametrised? | note for brief/agent |
|---|---|---|---|
| `resolve_subject(access_token, capability, *, registry, principal_store, keep_store)` | `:179` | identity-level (n/a) | THE one Subject constructor; unchanged by 63c |
| `read_filter(subject, table)` | `:242` | **YES** (thin wrapper over `authorize_filter(READ, table)`) | brief passes `"brief"`; agent's scope filter TableScans (PART D) |
| `resolve_write_scope(subject, scope, *, default)` | `:156` | scope-domain (shared) | the write-scope grant predicate |
| `authorize_guarded` / `guarded_write(subject, action, *, table, row_id, set_fragment, audit, store)` | `:452` / `:518` | **YES** (`table`, `row_id`) | THE single-row guarded write; brief/agent single-row writes route here |
| `report_unmigrated_governed_rows(store, table)` | `:595` | **YES but SCOPE-KEYED** (`… WHERE scope IS NONE …`) | **does NOT fit `agent`** (no scope column — agent's unmigrated predicate is `owner_principal IS NONE`). Fork. |
| `MigrateGovernedResult` / `LegacyMapping` | `:95` / `:112` | per-table | brief disposition = UNOWNED-LEGACY (NONE/NONE, scope=project keep) |
| `write_guard`/`active_write_guard`; `governed_exempt`/`active_exempt`/`ExemptToken` | `:280`/`:273`; `:358`/`:341`/`:322` | runtime attribution | the F5 write-attribution + admin-exempt (migrate backfill) contexts |

### `loremaster/tests/_governed_contract.py` F5 substrate
| element | site | table-parametrised? | a brief/agent parametrisation needs |
|---|---|---|---|
| `GovernedTableCase` (seed one governed row w/ owner/scope\|None) | `:275` | abstraction is generic | brief/agent `GovernedTableCase` entries |
| `governed_table_raw_mutation_sites(source, table, *, table_const_hint="MEMORY_TABLE")` | `:1088` | **YES** (`table` + `table_const_hint`) | pass `BRIEF_TABLE`/`AGENT_TABLE` hints |
| `MutationSite`, `_statement_shape`, `_raw_mutation_of_table`, `_enclosing_functions`, `_docstring_node_ids`, `call_name` | `:970`+ | scanner internals (generic) | — |
| `derive_surrealql_statement_keywords_from_corpus` | `:912` | runtime L2 guard corpus | — |
| credentialed harness: `credentialed_app_context`, `register_owned`, `store_handle`, `build_memory_backend`, `build_principal_and_keep_stores` | `:669`/`:747`/`:762`/`:584`/`:607` | generic | wire brief/agent stores into the fixtures |
| seeds: `seed_memory_legacy`/`seed_memory_governed`, `seed_message_legacy` | `:315`/`:327`/`:367` | memory + message ONLY | **add `seed_brief_legacy`/`seed_brief_governed` + `seed_agent_legacy`/`seed_agent_governed`** |
| table constants `MEMORY_TABLE`/`MESSAGE_TABLE`/`_PRINCIPAL_TABLE`/`_AGENT_TABLE` | `:297-300` | — | **add `BRIEF_TABLE`** (AGENT_TABLE present) |
| `governed_overlay_ddl(table)`; `frozen_asserted_message_ddl`/`unbounded_message_ddl` | `:508`/`:526`/`:559` | overlay generic; DD-3.c DDL is message-specific | brief/agent DD-3.c tests need analogous old/new DDL pairs (this probe builds them ad hoc via `_downgrade`) |

### `_GOVERNED_VERBS_PENDING_ROUTING` (`server.py:11241`) — the 63c-owned RED_ADJUDICATED legs
```
("lore_comms", "brief_get")     -> _ROUTE_63C_REMAINDER
("lore_comms", "brief_publish") -> _ROUTE_63C_REMAINDER
("lore_comms", "brief_ack")     -> _ROUTE_63C_REMAINDER
("lore_comms", "fleet")         -> _ROUTE_63C_REMAINDER
("lore_comms", "heartbeat")     -> _ROUTE_63C_REMAINDER
```
(63b owns `register`/`send`/`drain`/`ack`/`await`/`story` → `_ROUTE_63B_MESSAGE`; 64 owns lore_tasks/lore_findings/lore_claim_task.)

**Summary of what a parametrisation needs:**
- **brief** — fully scope-based like `message`: add `BRIEF_TABLE` + a `GovernedTableCase` + `seed_brief_legacy`/`_governed`; the `read_filter`/`guarded_write`/`report_unmigrated_governed_rows` seams are already table-generic; `LegacyMapping('brief', UNOWNED-LEGACY)` exists in intent.
- **agent** — NOT scope-based (no scope column): `read_filter` and `report_unmigrated_governed_rows` do NOT fit as-is (both scope-keyed). Agent governance is `owner_principal`-based (index-served) or session-set-based. **This is the design fork the sidecar must rule** before the contract can parametrise the agent population.

---

## GATES (all four + the probe, run at HEAD `bb9ac1e` + this session's edits, 2026-09-13)
- `uv run ruff check .` → **All checks passed!** (clean)
- `./scripts/typecheck.sh` → **GREEN** (zero mypy, incl. test trees; via the currency gate's typecheck leg)
- `uv run python scripts/pending_contract_gate.py --currency` → **CURRENCY : PASS** — manifest `('typecheck','ruff','pytest')` all GREEN, 0 RED_ORPHANED. (First run flagged 2 RED_ORPHANED F401s in the probe's imports — `_statuses`, `ScanObservation` — both removed; re-run PASS.)
- `uv run pytest -n 12 -q` (run ALONE, #466) → **11242 passed, 62 skipped, 3 xfailed, 7 warnings in 511.44s**, exit 0. Zero failures — the `test_secret_typing.py` allowlist edit is validated in-suite; no failures unrelated to scope.
- `python scripts/probe_governed_63c.py` → **exit 0** (self-check: all controls held, each ASSERT real, every poisoned-row UPDATE aborted with its conforming control passing, brief read-filter IndexScanned, agent owner_principal IndexScanned).

## FRICTION
- **lore MCP write side intermittently unreachable** — `lore_comms`/`lore_index` (heartbeat, register-side writes) failed twice this session with `SurrealDB … failed against 'ws://127.0.0.1:18500/rpc': no close frame received or sent` (lore's own PROD backend). The read side (`lore_search`/`lore_get_symbol`/`lore_read`) worked throughout. Did not block the mission (the probe uses `:18000` via the SDK directly). **Every failure HEALED on the immediate retry** (the lead message landed #13000 on the 2nd send) — the store-ref §3 in-flight-drop shape (raw KeyError/ConnectionClosedError normalises on the NEXT call). Registration succeeded at session start (brief v7 acked). **Filed as finding #468.** Intermittent + self-healing on retry, not a hard outage — but a caller with no retry loop around the MCP surface silently loses the write.

## Sweep / fallback honesty
- Used lore (`lore_get_symbol`/`lore_search`/`lore_read`) as first choice for all code-structure reads. Fell back to **simple prefix-match `awk`** (no regex) only to locate module-level CONSTANTS (`_AGENT_FIELD_SPECS` etc.) and `def`/`class` line numbers, which `lore_get_symbol` cannot resolve (it indexes class/method/function chunks, not module constants). Said so here per the dogfood protocol; `rg`/`grep` are hook-blocked in this checkout and were not used.
