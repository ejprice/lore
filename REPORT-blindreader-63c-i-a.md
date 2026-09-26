# REPORT — blindreader-63c-i-a (contract-blind diff read, wave 63c-i-a)

brief-base v16 read · brief project v7 read
- **State:** done (report-only; no edits outside this file, no tests run, no commits, `:18500` untouched).
- **Deviations:** read finding #470 (ledger row, not a withheld design doc) to learn what the new precondition claims — disclosed §0. Text sweeps via awk (grep hook-blocked); lore graph not used for the uncommitted tree — fallback declared §0.
- **Packages considered:** none — no mechanism specified (read-only grade).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none (no new symbols).
- **Graded:** working tree over `cb2a215` · HEAD-at-report: `1d1dfc3` · DIFFERENT (1 behind) — the only commit between is `REPORT-lead-63c.md` (+7 lines); production diffstat identical at both (agents 132 / principals 94 / server 24 / schema 106 / governed 6 / lorerunes 3). `scripts/probe_governed_63c.py` became modified mid-read — NOT graded.
- **Headline:** 1 MAJOR (conditional), 4 MINOR, 5 NOTE. No BLOCKER.
  - **F-2 MAJOR** — the diff redefines "un-migrated agent" as `scope IS NONE` and refuses owned-but-unscoped agents, but the UNCHANGED message leg's agent-first guard still keys on `owner_principal IS NONE`: on the exact store `--table agent` refuses as multi-principal, `--table message` proceeds and stamps foreign owners into the project keep. #470 quotes the ruling as "refuses ALL tables". Untested.
  - **F-1 / F-4 / F-8 / F-5 / F-9 MINOR** — served prose: wrong diagnosis for operator-owned unscoped rows; "nothing was written" false on the credentialed tool path (session keep minted + keeper claimed before a blank-role refusal); new lorerunes docstring re-teaches the WHERE-inlining threat model #219 refuted; `_owner_count` docstring stale; identity-refusal gloss restated (not derived) and omits the 64-char cap.
- **Decisions needed:** D-1 — is "refuses ALL tables on a foreign-owned agent" (#470's quote of ruling §6 item 6) in 63c-i-a's scope? If yes F-2 is a build defect (message leg guard must share the agent leg's migrated predicate + precondition); if deferred, name the wave. D-2 — F-4 fix locus: refuse blank role in the handler before the keep mint, or narrow the prose.
- **Receipt pointers:** inventory §2 (R/S/M/V/O rows); input-fate §3a–3d (F-2 scenario in §3d); findings §4; served-English §5; coverage §6.

---

## 0. Capability check
- Demanded: read the diff + HEAD bodies, register on lore_comms, no tests run, report + ledger pointer + one native message.
- Have: Bash/Read, lore MCP (loaded via `ToolSearch "+lore"`), `lore_comms register` OK (session `63c-20260924`, brief project v7 read).
- grep/rg: not used (hook-blocked per brief); every text sweep below was done with `awk` over `find` output. Structure questions (callers of `_owner_count`, agent-table writers) were answered by awk sweeps rather than `lore_impact` because the tree under review is UNCOMMITTED and lore indexes it only as fast as the watcher; a textual sweep was the honest instrument for an uncommitted diff (fallback declared, case (c) cross-cutting map).
- Withheld set honoured: no `REPORT-contract-*`/`adversary`/`builder`/`prosefix`/`coldaudit`, no `REPORT-lead-63c.md`, no `docs/design/*packet63c*`. Finding #470 (a ledger row, not a design doc) WAS read to learn what the new precondition claims to implement — disclosed here.

## 1. What changed (production), in one line each
| file | symbol | change |
|---|---|---|
| `lorerunes/lorerunes/identifiers.py` (NEW) | `AGENT_NAME_PATTERN`, `is_legal_identifier` | the charset pattern moves here; `fullmatch` predicate |
| `lorerunes/lorerunes/__init__.py` | exports | re-exports both |
| `loremaster/loremaster/agents.py` | module | own `re.compile` deleted; `AGENT_NAME_PATTERN` is now a re-export of the lorerunes object |
| `loremaster/loremaster/agents.py` | `AgentRegistry.register` | + `session_keep_id` kwarg; + pair refusal (`_refuse_an_inconsistent_provenance_pair`); + identity refusal (`_refuse_an_invalid_identity`, new `InvalidAgentIdentityError`) BEFORE `_select_row`; CREATE content gains `owner_agent` (= own id, always) and `scope` (= `keep_scope(session_keep_id)` or None) |
| `loremaster/loremaster/server.py` | `AppContext._is_comms_charset_legal` | body now calls `lorerunes.is_legal_identifier` (lazy import) |
| `loremaster/loremaster/server.py` | `AppContext` comms register handler (the `register` action) | declares `session_keep_bare=None` up front and passes it to `register(session_keep_id=...)` on every call |
| `loremaster/loremaster/store/surreal_schema.py` | `_AGENT_FIELD_SPECS` | `name`/`session`/`role` lose their ASSERTs (rows kept, empty constraint → OVERWRITE drops the stored ASSERT); `owner_principal` row removed from the tuple |
| `loremaster/loremaster/store/surreal_schema.py` | `_agent_statements` | governed triple + `agent_scope`/`agent_owner_principal` indexes now from `_governed_field_specs`/`_governed_index_statements`; `_AGENT_OWNER_PRINCIPAL_INDEX_FIELDS` deleted |
| `loremaster/loremaster/store/surreal_schema.py` | `_IDENTIFIER_CHARSET_PATTERN` | now `AGENT_NAME_PATTERN.pattern` (text identical; consumed by `brief.name` only) |
| `loremaster/loremaster/principals.py` | `_migrate_agent_owner` | predicate `owner_principal IS NONE` → `scope IS NONE`; NEW row precondition refusal (owned-but-unscoped rows); ONE UPDATE stamps owner_principal + owner_agent=id + scope=project keep; gains `keep_store` param; mints/gets the project keep |
| `loremaster/loremaster/principals.py` | `migrate_governed` | passes `keep_store` to the agent leg |
| `loremaster/loremaster/governed.py` | `LegacyMapping` | docstring only |

## 2. REMOVED-BEHAVIOUR INVENTORY (written before any test was read)

Legend — fate: **P** preserved · **C** changed · **D** dropped. Every row cites the new home.

### 2a. `AgentRegistry.register` (agents.py) + the store it writes
| # | OLD behaviour (HEAD `cb2a215`) | fate | NEW (working tree) |
|---|---|---|---|
| R1 | Illegal `name`/`session` on CREATE: refused by the STORE `ASSERT string::matches($value,'^[a-z0-9][a-z0-9_-]{0,63}$')` → engine rejection surfaced through `run_query` (not an `AgentRegistryError`); a `_select_row` read happened FIRST | C | refused in Python by `is_legal_identifier` → `InvalidAgentIdentityError(AgentRegistryError)` BEFORE `_select_row` (no store I/O). Regex semantics equal: Rust-regex `$` = end-of-text, Python `fullmatch` — both reject `"scout\n"`. |
| R2 | Illegal `name`/`session` (or blank role) on RE-register of an existing LEGACY VIOLATOR row (a dirty long-lived store — rows born before the ASSERT, which the test tree seeds deliberately): the re-register `UPDATE` and every `touch` `UPDATE` re-validate the stored ASSERT → engine failure on EVERY write to that row (DD-3.c poison) | C | re-register refused in Python (`InvalidAgentIdentityError`, no I/O); `touch` now SUCCEEDS (ASSERT gone). *(Corrected after the test skim: my first draft of this row said the population was unreachable — it is reachable on a dirty store.)* |
| R3 | Blank `role` on CREATE: refused by the store `ASSERT string::len(string::trim($value)) > 0` | C | refused by `lorerunes.is_blank` → `InvalidAgentIdentityError`. **Predicate is NARROWER than the dropped ASSERT**: Python `str.strip()` treats U+001C–U+001F as whitespace; Rust `str::trim` (White_Space property) does not — so role `"\x1f"` was ACCEPTED at HEAD and is REFUSED now. (Python set measured: `python3 -c '...isspace()'` lists `0x1c-0x1f`; the SurrealDB `string::trim`=Rust `str::trim` equivalence is **MEDIUM** — not probed.) See F-7. |
| R4 | Blank `role` on RE-register: `existing.role != role` → `AgentIdentityConflictError` ("already registered with role X … register a fresh name") | C | now `InvalidAgentIdentityError` ("role must not be blank") — different class + remedy text; both are `AgentRegistryError`. Improvement (the old remedy "register a fresh name" was wrong advice for a blank role). |
| R5 | `owner_principal` stamped on CREATE only, from `owner_principal_id` (RecordID link) or None | P | unchanged |
| R6 | Re-register never re-stamps owner | P | unchanged, and extended to `owner_agent`/`scope` (never written on the UPDATE branch — verified: the UPDATE SET list is unchanged) |
| R7 | CREATE row had NO `owner_agent`, NO `scope` field | C | `owner_agent = RecordID('agent', own id)` on EVERY create (incl. tokenless); `scope = keep_scope(session_keep_id)` or None |
| R8 | No constraint coupling owner and keep | C | NEW refusal: exactly one of `(owner_principal_id, session_keep_id)` set → `AgentRegistryError` before any I/O (F-4: wording/"nothing was written") |
| R9 | `capability = f"{name}:{secret}"` relied on name having no `:` — guaranteed by the store ASSERT (the CREATE would fail) | P | now guaranteed by the Python refusal, still BEFORE the CREATE. Only writer of agent rows = `AgentRegistry.register` (awk sweep of `loremaster/loremaster/**/*.py` for CREATE/UPSERT/INSERT/UPDATE on the agent table: `agents.py` CREATE (register) + 2 UPDATEs (re-register, touch) + `principals.py` migrate UPDATE; `scripts/probe_*` write agent rows in throwaway DBs only). |
| R10 | `_row_to_agent` maps explicit columns | P | unchanged — new columns never read back, so `Agent`'s shape is untouched |
| R11 | Defense-in-depth: a SECOND writer (future, or a stale-image container during a rolling cutover) was stopped by the store ASSERT | **D** | dropped deliberately per the diff's comment (DD-3.c poison risk on a populated table). Residual: any non-`register` write path is now unguarded at the store. See F-6. |
| R12 | `AGENT_NAME_PATTERN` was a module-local compiled object in agents.py; server imported it from agents | C | ONE object in lorerunes; `loremaster.agents.AGENT_NAME_PATTERN is lorerunes.AGENT_NAME_PATTERN` by `import … as …` re-export. Text identical. |

### 2b. Schema DDL (`_agent_statements`)
| # | OLD | fate | NEW |
|---|---|---|---|
| S1 | `DEFINE FIELD OVERWRITE name/session … ASSERT string::matches(...)` | C | `DEFINE FIELD OVERWRITE name/session TYPE string` — OVERWRITE full-replace drops the stored ASSERT on a long-lived store (the rows were KEPT with an empty constraint; deleting them would have left the old ASSERT live — correct per store-ref §1.2 as quoted in the diff comment) |
| S2 | `role` non-empty ASSERT | C | dropped, same mechanism |
| S3 | `status` closed domain ASSERT | P | kept |
| S4 | `owner_principal option<record<principal>>` via `_AGENT_FIELD_SPECS` | P | same type string, now from `_governed_field_specs` (`f"option<record<{PRINCIPAL_TABLE}>>"`) — byte-identical assuming `PRINCIPAL_TABLE=='principal'` (it is the lorerunes constant the old literal named) |
| S5 | `agent_owner_principal` plain IF NOT EXISTS index on `(owner_principal,)` | P | same name + fields via `_governed_index_statements` → no-op on a long-lived store |
| S6 | — | NEW | `owner_agent option<record<agent>>`, `scope option<string>`, index `agent_scope` (IF NOT EXISTS — a build over every existing agent row on first boot; agent table is small) |
| S7 | `brief.name` ASSERT literal `^[a-z0-9][a-z0-9_-]{0,63}$` | P | now `AGENT_NAME_PATTERN.pattern`, identical text |
| S8 | Statement ORDER: owner_principal field defined among the field specs, before the indexes | C | governed fields now defined AFTER the `(session,status)` and `name` indexes; each index still follows its own field. Benign. |

### 2c. `_migrate_agent_owner` (principals.py) — `lore-adm migrate-governed --table agent`
| # | OLD | fate | NEW |
|---|---|---|---|
| M1 | operator unresolved → refused, reason names principal/admin counts, scanned=0 | P | unchanged (runs first) |
| M2 | "unmigrated" = `owner_principal IS NONE`; "already" = `owner_principal IS NOT NONE` | C | `scope IS NONE` / `scope IS NOT NONE` (`_scope_count`) |
| M3 | unmigrated==0 → clean no-op result | P | same, on the new predicate |
| M4 | NO row-level precondition: an already-owned row was simply counted as migrated and left intact | C | NEW: any `scope IS NONE AND owner_principal IS NOT NONE` row → `refused=True`, 0 rows stamped, reason names full count + first ≤10 sorted ids (`_REFUSAL_ID_SAMPLE_SIZE`). **Fate of an owned-but-unscoped row flipped from "already migrated, left intact" to "blocks the whole agent leg".** See F-1. |
| M5 | UPDATE `SET owner_principal = operator WHERE owner_principal IS NONE` | C | `SET owner_principal = operator, owner_agent = id, scope = $project_scope WHERE scope IS NONE` (no `owner_principal IS NONE` re-check at write time — see F-3) |
| M6 | Agent leg did NOT touch keeps | C | now `get_or_create_keyed(PROJECT_KEEP_KEY, type="project", keeper_email=operator.email, name="lore")` — identical call to the memory/message legs (P for policy, new side effect for this leg; runs AFTER the precondition, so a refusal writes no keep — byte-inert as its comment claims) |
| M7 | `backfilled=unmigrated` (count read before the UPDATE) | P | same pre-read count (TOCTOU identical to HEAD) |
| M8 | `governed_exempt("migrate-governed", statement=…)` with function-local literal | P | same idiom |
| M9 | noun `"governed agent-owner backfill"` | C | `"governed agent backfill"` (log/err label text) |

### 2d. Server comms `register` path
| # | OLD | fate | NEW |
|---|---|---|---|
| V1 | link-0 `_validate_comms_identities` refuses illegal agent/session BEFORE any store touch (`lore_comms` dispatcher) | P | unchanged; `_is_comms_charset_legal` now delegates to lorerunes |
| V2 | SF-63-1: principal present → `get_or_create_keyed(session:<s>)` + household gate, BEFORE `registry.register` | P | unchanged; the SAME `session_keep_bare` the gate checks is now passed as `session_keep_id` (so stamped scope == gate-checked scope) |
| V3 | tokenless (α): no keep, owner None | P | `session_keep_id=None` passed explicitly → pair consistent |
| V4 | SKIP policy (`_comms_traffic_line`) uses the same predicate | P | now via lorerunes |

### 2e. `_owner_count` / message leg (untouched code whose MEANING the diff changed)
| # | OLD | fate | NEW |
|---|---|---|---|
| O1 | `_owner_count` docstring: "the agent leg counts NONE-owner agents to backfill, and the message leg reads it …" | C (stale) | agent leg no longer calls it; docstring now false in its first clause. F-5. |
| O2 | message leg's §2.6 agent-first guard = `agent.owner_principal IS NONE` count, which EQUALLED the agent leg's "unmigrated" predicate | C (divergent) | agent leg's "unmigrated" is now `scope IS NONE`; the message guard still asks `owner_principal IS NONE`. The two disagree exactly on the owned-but-unscoped population. F-2. |
| O3 | `report_unmigrated_governed_rows(agent)` = `scope IS NONE` count, which at HEAD disagreed with the owner-keyed agent migrate (agent had no scope field → every row counted) | C (fixed) | agent migrate and the report now agree on `scope IS NONE`. Improvement. |

## 3. INPUT-FATE TABLE (written before any test was read; §5 adds coverage)

### 3a. `lorerunes.is_legal_identifier` (and every consumer: registry refusal, server REFUSE, server SKIP, fake)
| input class | example | HEAD fate | now | silent change? |
|---|---|---|---|---|
| legal | `scout`, `a`, `0-x_y` | accept | accept | no |
| empty | `""` | reject (store regex needs ≥1 char; server `fullmatch`) | reject | no |
| cap (64) | `"a"*64` | accept | accept | no |
| cap+1 (65) | `"a"*65` | reject | reject | no |
| uppercase / leading `-`/`_` | `Scout`, `-x` | reject | reject | no |
| trailing newline | `"scout\n"` | reject (server `fullmatch`; store Rust-regex `$` = end of text) | reject | no |
| non-ASCII | `"scoüt"` | reject | reject | no |
| hostile free text (via `owner=`/`created_by=` SKIP path) | `"the release train"` | skipped, no error | skipped | no |
| non-`str` (programmatic caller only) | `None` | registry: store type error on CREATE | `TypeError` from `re.fullmatch` before I/O | yes, but unreachable from the MCP seam (typed `str`) — NOTE |

### 3b. `AgentRegistry.register`
| input class | HEAD fate | now | silent? |
|---|---|---|---|
| legal, tokenless, new | row: owner NONE, no owner_agent/scope | row: owner NONE, **owner_agent = self**, scope NONE | intended (R7) |
| legal, credentialed + keep, new | row: owner set, no scope | owner + owner_agent=self + scope=`keep_scope(keep)` | intended |
| owner without keep / keep without owner | owner stamped, no scope | `AgentRegistryError`, no I/O | intended (R8) |
| illegal name/session, new | store ASSERT rejection (engine error class), after one SELECT | `InvalidAgentIdentityError`, no I/O | class changed — callers catching the engine error class would miss it; the only production caller is the comms register handler, which charset-refuses earlier anyway |
| blank role `""`/`"  "`, new | store ASSERT rejection | `InvalidAgentIdentityError` | class changed (as above) |
| role of only U+001C–U+001F | **ACCEPTED** (Rust trim) — MEDIUM | **REFUSED** (`str.isspace`) | **yes — silent narrowing** (F-7) |
| blank role, re-register | `AgentIdentityConflictError` "register a fresh name" | `InvalidAgentIdentityError` "must not be blank" | improved |
| re-register of a legacy violator row | every UPDATE failed on the stored ASSERT | re-register refused app-side; touch succeeds | intended (R2) |
| re-register by a different householded principal | no re-stamp | no re-stamp (incl. owner_agent/scope) | no |
| retired row | `RetiredAgentError` | same (after the new refusals) | no |

### 3c. `migrate_governed(table="agent")`
| store shape | HEAD fate | now | silent? |
|---|---|---|---|
| no principals / ambiguous operator | refused | refused (unchanged, runs first) | no |
| all rows scope NONE, owner NONE (production today) | owner stamped only | owner + owner_agent=id + scope=project keep; project keep minted if absent | intended |
| owned+scoped rows (post-63c registers) | counted "already" (owner-keyed) | counted "already" (scope-keyed), byte-untouched | no |
| owned-but-unscoped rows, owner ≠ operator | counted "already", legacy rows stamped around them | **whole leg REFUSED**, 0 stamped, count + ≤10 sorted ids named | intended (#470) |
| owned-but-unscoped rows, owner **= operator** (HEAD-era register or HEAD-era migrate output) | counted "already" | **whole leg REFUSED** with the prose "multi-principal or half-applied store" | intended as a pinned KNOWN BOUND (measured empty on production 2026-09-24, per the test docstring) — but the SERVED diagnosis is wrong for this population (F-1) |
| legacy violator rows (hostile name, blank role) | UPDATE failed on stored ASSERT (after the DDL re-land: stamped) | stamped (ASSERTs dropped) | intended |
| legacy junk-status row | whole UPDATE fails | whole UPDATE fails (status ASSERT kept) → raises, not `refused=True` | no |
| re-run | backfills 0 | backfills 0 | no |

### 3d. `migrate_governed(table="message")` — code UNCHANGED, meaning CHANGED
| store shape | HEAD fate | now |
|---|---|---|
| agents all owned-but-unscoped (agent leg REFUSES), zero ownerless agents | n/a at HEAD (agent leg had no row precondition; "migrated agent" ≡ owned) | message leg's §2.6 guard (`_owner_count(agent, none=True) == 0`) PASSES → every legacy message is stamped `owner_principal = sender.owner_principal` (the non-operator owner) and `scope = project keep` — **on the exact store the agent leg just refused as multi-principal.** F-2. |

## 4. FINDINGS (severity · file:symbol)

**F-2 · MAJOR (conditional — see decision D-1) · `principals.py:_migrate_message_owner` (untouched) vs `principals.py:_migrate_agent_owner` (changed).**
The diff redefines "an un-migrated agent" as `scope IS NONE` and adds a row precondition that refuses owned-but-unscoped agents as a multi-principal / half-applied store. The message leg's agent-first guard still keys on the OLD definition (`owner_principal IS NONE`). On a store whose unscoped agents are all owned by a non-operator principal, `--table agent` refuses and `--table message` then proceeds, widening those agents' messages into the project keep under the foreign owner — the "never a silent partial widening of visibility" that `migrate_governed`'s own docstring promises. Finding #470 quotes the ruling's auditor attack as *"seed one foreign-owned agent → the verb refuses ALL tables and writes nothing"*; the build refuses one table. `memory` has no agent precondition at all. Failure scenario: seed agent `a` with `owner_principal=principal:foreign`, `scope NONE`, one message sent by `a` with NONE owner/scope; run `--table agent` → refused; run `--table message` → `refused=False, backfilled=1`, message `owner_principal=principal:foreign, scope=keep:<project>`. **Not covered by any test** (awk sweep of the three message-migrate test files and the 63c-i-a file: no test seeds an owned-but-unscoped agent and then runs the message leg). If the ruling scopes "refuses ALL tables" to a later wave, this downgrades to a NOTE carrying that wave's name.

**F-1 · MINOR · `principals.py:_migrate_agent_owner` refusal `reason`.** The served diagnosis *"a multi-principal or half-applied store (§2.1)"* is false for a population the test tree itself names — owner = the operator, scope NONE, produced by any pkt-62→63b image's credentialed register (the test docstring on `test_R_Q5_1_…`: *"neither multi-principal nor half-applied"*). The bound is pinned and measured empty (good), but on the day its re-open trigger fires the refusal will send the operator hunting for a second principal that does not exist. The remedy clause *"Adjudicate these rows by hand"* also names no mechanism, and no lore verb can fix such a row (re-register never stamps scope — MP-F). Cheap fix: derive the diagnosis — say whether the offending owners are the operator or not (the id read could also select `owner_principal`).

**F-4 · MINOR · `agents.py:AgentRegistry._refuse_an_invalid_identity` / `_refuse_an_inconsistent_provenance_pair` — "nothing was written".** On the credentialed comms path the handler has ALREADY run `keep_store.get_or_create_keyed(session:<s>)` (and auto-households the registrant as keeper) before `registry.register` refuses. A blank-role credentialed register (reachable: the wire requires `role` present, not non-blank; `_validate_comms_identities` checks charset only) therefore mints the session keep, makes the caller its keeper — so a later different principal's register into that session is DENIED by SF-63-1 — and is told *"nothing was written"*. The side effect predates this diff (HEAD's store ASSERT fired at the same point); the new prose is what over-claims. Fix options: refuse blank role in the handler before the keep mint (one more `is_blank` consumer), or scope the prose to "no agent row was written". No test drives a blank role through `AppContext.comms(action="register")` with a credential (awk sweep; multi-line calls could evade it — bound stated).

**F-8 · MINOR · `lorerunes/identifiers.py` module docstring + `agents.py` block comment above the re-export.** Both teach that identities are *"inlined as a literal into live WHERE clauses"*, which makes the charset *"a load-bearing injection guard"*. The repo already corrected that as FALSE (finding #219, quoted in `server.py:AppContext._validate_comms_charset`: *"every comms identity travels as a BOUND PARAMETER"*). My awk sweep of `loremaster/loremaster/**/*.py` for WHERE clauses interpolating `name`/`session`/`value` found only constant interpolations (status literals, table names) — the one inlined id (`inbox_awaiter.py` `LIVE SELECT … agent:\`<uuid5 hex>\``) is the derived uuid, not a name. The new shared module re-installs a refuted threat model at the address every future reader lands on first. Fix: copy #219's corrected rationale (render-safety, the trailing-newline twin, the cheap gate).

**F-5 · MINOR · `principals.py:_owner_count` docstring.** *"the agent leg counts NONE-owner agents to backfill"* — false since this diff (agent leg uses `_scope_count`). Its only remaining caller is the message leg (F-2).

**F-9 · MINOR · `agents.py:_refuse_an_invalid_identity` docstring vs message.** Docstring: *"The rule text is DERIVED from `AGENT_NAME_PATTERN` so a pattern change moves the message with it."* Only the regex text is derived; the English gloss *"(lowercase letters, digits, '_' or '-', starting with a letter or digit)"* is restated and would NOT move — and it omits the 64-character cap, so a 65-char name is refused with prose that doesn't say why (the regex `{0,63}` does, for a reader who parses it). The server's refusal for the same rule (`_validate_comms_charset`) uses different wording — two English statements of one rule. Fix: drop the gloss or mark it as the pattern's paraphrase including length.

**F-7 · NOTE · `agents.py:_refuse_an_invalid_identity` role leg.** `is_blank` (Python `str.isspace`) is strictly wider than the dropped `string::len(string::trim($value)) > 0` on U+001C–U+001F, so four previously-accepted one-char roles are now refused. Harmless in practice; recorded because the diff describes this as a MOVE of the ASSERT, and it is a narrowing. `brief.body`/`brief.created_by` keep the store's trim-based ASSERT, so "what is blank" now has two answers across tables until 63c-ii. Engine-side claim is **MEDIUM** (Rust `str::trim` semantics assumed for `string::trim`; not probed).

**F-3 · NOTE · `principals.py:_migrate_agent_owner` UPDATE.** `WHERE scope IS NONE` does not re-assert `owner_principal IS NONE`; a row that becomes owned-but-unscoped between the precondition read and the UPDATE would have its owner overwritten to the operator. The writer can no longer produce such a row (A3), so only an old-image writer during the cutover could. Adding `AND owner_principal IS NONE` would make the write self-guarding at no cost — but it changes the exempt-statement golden, so it is the lead's call.

**F-6 · NOTE · schema `_AGENT_FIELD_SPECS`.** Defense-in-depth dropped deliberately: any future second writer of `agent` rows is unguarded at the store. The diff's rationale (DD-3.c) is sound; recording the removed guard per the removed-behaviour law.

**F-10 · NOTE · `tests/_comms_fakes.py:FakeAgentRegistry._shared_identifier_predicate`.** The `| None` return and the caller's `is not None` branch are dead code, acknowledged in the docstring with a named collapse point ("at i-b (amendment 12)"). Fine as a ledgered deferral; noting that a dead `None` branch in a fake is exactly where a future guard could be silently re-added.

**F-11 · NOTE · unbounded echo.** `_refuse_an_invalid_identity` fences the full offending value with no length cap. Unreachable from MCP (the server's link-0 refusal fires first, with the same unbounded echo, pre-existing).

## 5. SERVED-ENGLISH CHECK (step 4) — every new served/behaviour-describing string
| string (site) | matches code? |
|---|---|
| identity refusal (`_refuse_an_invalid_identity`) | pattern: derived ✔; gloss: restated + omits length ✘ (F-9); "nothing was written": false on the credentialed tool path ✘ (F-4) |
| blank-role refusal | "nothing was written" ✘ on the credentialed tool path (F-4) |
| pair refusal (`_refuse_an_inconsistent_provenance_pair`) | "server-side caller bug; nothing was written" — true of the agent row; the handler minted the keep first (same F-4 caveat, only reachable by a caller bug) |
| migrate precondition refusal | counts DERIVED from one read ✔; "First N of M" uses `len(shown_ids)` ✔; diagnosis ✘ for the operator-owned population (F-1); remedy names no mechanism (F-1) |
| `_migrate_agent_owner` docstring | ✔ matches code |
| `_owner_count` docstring (untouched) | ✘ now stale (F-5) |
| `lorerunes/identifiers.py` docstring | "inlined as a literal into live WHERE" ✘ (F-8); consumer list ✔ (the three named consumers exist and call it) |
| `server.py:_is_comms_charset_legal` docstring | ✔ (names the mutation tests; not verified they exist beyond the awk hits — `test_agent_registry.py` names them) |
| `surreal_schema.py` comments (§1.2 OVERWRITE full-replace, IF NOT EXISTS index no-op) | ✔ consistent with store-ref as quoted; not independently probed |
| `governed.py:LegacyMapping` docstring | ✔ |
No served number is restated beside a constant; the one bound (`_REFUSAL_ID_SAMPLE_SIZE`) is read at call time and the prose states `len(shown_ids)`.

## 6. UNCOVERED ITEMS (after skimming `test_agent_governance_63c_i_a.py`, `test_agent_registry.py`, `test_message_migrate_63b_ii_a.py`, `test_message_migrate_dirty_store_63b_ii_b.py`, `test_governed_migration_63a.py`; awk-located, not exhaustive)
| item | covered? |
|---|---|
| F-2 message leg on an owned-but-unscoped agent store | **NO** |
| F-4 blank role through the credentialed comms tool (keep minted, "nothing was written") | **NO** found |
| F-7 U+001C–U+001F role narrowing | NO (not expected to be pinned; NOTE) |
| F-1 operator-owned unscoped rows refused | YES as a documented KNOWN BOUND in `test_R_Q5_1_…` docstring (trap rows deliberately non-operator); the served diagnosis text for that population is not pinned |
| F-3 TOCTOU owner overwrite | NO (NOTE) |
| R2 legacy violator re-register/touch | YES — `TestAHostileNamedLegacyAgentCannotReRegisterButStillTouches63cIA`, `TestAgentHeartbeatOnALegacyRoleRow63cIA` |
| M4 precondition count/sample/bound | YES — heavily (`test_R_Q5_1_…`, four populations incl. perturbed bound) |
| M5 governed rows untouched by migrate | YES — `test_a_store_with_governed_and_legacy_agents_migrates_only_the_legacy` |
| S1/S2 ASSERT drop on a dirty store + status kept | YES — `TestTheAgentAssertsDropFromADirtyStore63cIA` |
| R8 pair refusal both paths, no I/O | YES — `TestTheRegistryProvenanceSeam63cIA` |
| V2 stamped scope == gate-checked keep; unconditional kwarg | YES — `test_scope_is_THE_session_keep_across_two_sessions`, `test_the_tool_passes_session_keep_id_UNCONDITIONALLY` |
| shared-decision mutation (writer/server/fake move together) | YES per test names in `test_agent_registry.py` (not run — brief forbids) |
