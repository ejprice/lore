# packet 63 — Governed-tool retrofit: comms + memory — design rulings

**Author:** design-sidecar-63 (Fable), 2026-08-28, working tree `8128c50` (branch
`feat/surreal-unification`).
**Nature:** design DOC + rulings with riders. I rule the four briefed forks within delegated
authority; the four SUB-FORKS of §7 were flagged CONFIRM for the operator and are **operator-CONFIRMED
2026-08-28 (every recommendation adopted; via lead-63 / AskUserQuestion, `lore_comms #8001`)**. The security-auditor is the named arbiter of §6; the
contract-adversary grades the contracts. I write NO code and NO tests.
**Status:** design, not yet contracted. Consumes 60/61/62 as CODE-COMPLETE (all commit-only;
deploy = the packet-65 joint cutover). **63 is COMMIT-ONLY**: nothing here reconfigures or
breaks the live dogfooding fleet, which keeps running the currently-deployed pre-retrofit image
until 65's atomic cutover (§2.6).

- `brief-base v14 read`
- `brief project v7 read`
- store reference read FIRST (this is store/schema/DDL/migration design):
  `docs/reference/surrealdb-31-capabilities.md` — cited by § below (§1.1 clause rule; §1.4
  option<>-on-populated-table + "a DEFAULT does not rescue an existing row" + the
  write-the-legacy-row-under-the-OLD-DDL fixture trap; §1.5 a DEFINE INDEX *builds*; §1.6 the
  dirty-store idiom; §1.8 UNIQUE over option<> = multiple NONE coexist; §2 `record<>` links do
  NOT auto-clean, `SELECT *` omits a NONE column, the #413 IN-inside-OR TableScan trap +
  composite-leading-column corollary; §3 statement[0]-only validation; §4 traversal is never
  index-served / field-through-hop is un-indexable). Never re-transcribed.
- `Graded: 8128c50 · HEAD-at-report: 8128c50 · SAME` (`lore_index()` watched root
  `/workspace` @ `8128c50`, branch `feat/surreal-unification`; index last_sweep 127 s old at
  read time).
- **Packages considered:** none new — this packet specifies no mechanism a package supplies
  beyond what 61/62 already adjudicated (the bespoke in-process PDP, authorization-model §11).
  The one candidate I checked: a migration framework (alembic-style) for the §2 row backfill —
  **bespoke**, because the backfill is two idempotent SurrealQL `UPDATE … WHERE … IS NONE`
  statements behind the house `execute_transaction` seam (store-ref §3), and no installed package
  targets SurrealQL DDL/DML (read: the `surrealdb` 2.0.0 SDK exposes no migration API —
  `surrealdb/__init__.py` exports connection classes only). A framework would be a second
  source of truth beside `ensure_ready()`'s declarative DDL.
- **Reuse ledger:** every symbol this doc names as NEW carries a DRY row in §8 (7 new symbols,
  all dispositioned: 4 EXTEND, 3 HAND-ROLLED with the query that proved the search).

---

## 0. Ruling summary (one line per fork) + the two facts that reshape the brief

- **(a) SPLIT SHAPE → RULED: three waves.** **63a = the shared governed SUBSTRATE + the MEMORY
  retrofit** (the substrate ships WITH its first real consumer, never as a guard over an empty
  set); **63b = the COMMS MESSAGE FAMILY** (`send/drain/ack/await/story` + rollup's message leg
  + the session-keep binding at `register`); **63c = the COMMS REMAINDER** (`brief_*` + `fleet`
  / the `agent` roster — SF-63-2). Each wave its own contract→adversary→build→cold-audit; a
  dedicated SECURITY-AUDITOR pass closes 63b (the wire-isolation headline, §6). 64 consumes the
  63a substrate UNCLONED (§3). Sizing triggers per wave in §1.4.
- **(b) MIGRATION → RULED per table, and the brief's premise is corrected first:** the
  authorization-model §7 sentence *"every existing row has a free-form `created_by`/`actor`/
  `agent` string"* is **per-table and FALSE for BOTH 63 tables** — verified this session against
  `_MEMORY_FIELD_SPECS` (no author column of any kind: `note_text/kind/labels/source/importance/
  …`) and `_MESSAGE_FIELD_SPECS` (`sender` is a REAL `record<agent>` link, not a string). So:
  **memory legacy rows → owner NONE/NONE (honest — no provenance exists to map; never
  fabricate the operator as author), scope = the canonical PROJECT keep. message legacy rows →
  `owner_agent = sender` (exact, resolvable), `owner_principal = sender.owner_principal` (NONE at
  HEAD for every legacy agent; BACKFILLED at the cutover to the operator's real principal under
  a guarded single-principal precondition), scope = the canonical PROJECT keep.** The
  grandfather scope value is `keep:<ulid>` of ONE canonical project keep, minted at the cutover
  migration, addressed by a NEW deterministic natural key `keep.key = 'project:lore'`
  (§2.2, SF-63-4). **BOTH** `option<>` columns (store-ref §1.4) **AND** an explicit idempotent
  backfill verb (`lore-adm migrate-governed`) — read-path tolerance alone would silently hide
  the fleet's own memory from the fleet (a NONE scope is admin-only BY CONSTRUCTION of the
  61 predicate — the fail-closed direction, §2.3).
- **(c) 63↔64 BOUNDARY → RULED: 63a EXPOSES six named seams + four parametrised pin families
  (§3); 64 adds rows to them and never clones.** The verb-routing coverage pin (#420) is built
  in 63a DERIVED from `partition_tools_by_population` × each tool's own dispatch table
  (`_COMMS_ACTIONS` is already a derivable verb table at `server.py`), with 63b/63c/64 legs
  RED_ADJUDICATED until each wave wires them.
- **(d) READ-FILTER STORE-LAW → RULED DDL: `owner_principal option<record<principal>>` +
  `owner_agent option<record<agent>>` + `scope option<string>` on `memory` and `message`, all
  via `_define_field` (OVERWRITE, §1.1); PLAIN `IF NOT EXISTS` indexes on `scope` AND
  `owner_principal` (the #413 fact-4 minimal read set); `owner_agent` NOT indexed at 63 (named
  trigger).** No arrow-traversal in any per-row WHERE (61 already pre-resolves `$my_keeps`;
  `ScopeInKeeps` expands to per-keep equalities). The `to`-edge inbox read is a TWO-STEP
  (recipient-edge pre-filter, then the ONE unqualified fragment on `message`) — never a
  hop-qualified second copy of the predicate (§4.3). **Probe: SPECIFIED for a `probe-63` wave,
  not run by me** (my brief forbids code; an instrument is a deliverable). The ONE genuinely
  unprobed delta is named: an `option<string>` `scope` column with NONE rows present, over the
  REAL `memory` DDL (HNSW co-resident) — 61b's oracle/probe used a non-option `scope string`
  on a bare fixture table (§4.4).
- **#425 → CLOSE in 63a** (collapse `stamp_owner`'s two reads to one). 63a introduces the
  packet's FIRST `owner_principal` UPDATE path (the cutover agent backfill, §2.1) and every
  governed write calls `stamp_owner` — #425's own re-open trigger fires inside 63; carrying it
  as a bound would be a deferral whose trigger the deferring packet itself pulls (§5).
- **§9 target (§6):** the hostile fixture is ≥2 principals × ≥2 agents each × EVERY read verb
  of both tools; the comms headline is **session admission is keeper-gated for a FOREIGN
  principal** (SF-63-1) — the hole a shared session STRING would otherwise open once hosted.

**The two facts that reshaped the brief (verified this session, cite-able):**

1. **At HEAD nothing in `server.py` calls `stamp_owner`, `verify_capability`, or
   `get_access_token`; `lore_comms` (`AppContext.comms`) has NO `capability=` parameter;
   `lore_remember`/`lore_recall` (`AppContext.remember`/`recall`) carry NO identity argument at
   all.** (grep `stamp_owner|get_access_token|capability` over `server.py`: only the
   `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` adjudication comments hit.) 62 built the seam; the
   ROUTING that makes any verb call it does not exist — #420 says so and 63 builds it. This
   makes Fork (a)'s substrate concrete: it is the missing `Subject`-resolution + verb-routing
   layer, not a refactor of an existing one.
2. **The tables differ in author provenance (above)**, which turns §7's generic "best-effort
   resolve the string" into two different, simpler, HONEST mappings — and surfaces a third
   table 63 owns that DOES carry a free-form string: `brief.created_by` (`_BRIEF_FIELD_SPECS`,
   an agent NAME with no session) — §2.1.

---

## 1. Fork (a) — the split shape

### 1.1 RULING: three waves, substrate-with-first-consumer, comms split by verb family

| wave | contents | why this boundary |
|---|---|---|
| **63a** | the SHARED SUBSTRATE (§1.2) **+ the memory retrofit** (`lore_remember`/`lore_recall` + the backend's `invalidate`/supersede write path) + #425 closure + the verb-routing coverage pin (#420) + the migration verb + the dirty-store pin family | memory is the SMALLEST real governed surface (one table, no author column, two tool verbs, one backend write seam `LocalMemoryBackend.remember/invalidate`) — the cheapest consumer that proves the substrate is REAL. *"A guard nobody runs is a hope with a filename"* (CLAUDE.md): a substrate wave with zero consumers cannot mutation-prove its own routing pin. |
| **63b** | the comms MESSAGE FAMILY: `message`+`to` columns, `send` (stamp + scope), `drain`/`ack`/`await` (two-step filtered inbox), `story` + rollup's message leg (filtered list reads + filtered COUNT), the `capability=` arg on `lore_comms`, `register`'s session-keep binding (SF-63-1), the message-row migration, the **dedicated security-auditor pass** | the isolation headline lives here; the session-keep binding is the one NEW mechanism in the packet and it belongs with the verbs that consume it |
| **63c** | the comms REMAINDER: `brief_get/brief_publish/brief_ack` (the `brief` table, scope = project keep) + `fleet` / `heartbeat` (the `agent` roster as a governed population — SF-63-2) | smaller, separable, and its population question (is the roster governed?) is an operator CONFIRM; **it MUST precede 65** — a hosted foreign principal reading briefs or the roster is an incomplete §9 |

**Order:** 63a → 63b → 63c. 64 may start after 63a (it needs only the substrate) and run
concurrently with 63b/63c on disjoint tables.

**Countermand stated:** the brief's alternative — comms and memory as two independent full
pipelines — is REJECTED because it manufactures exactly the #102 clone chain: the
Subject-resolution, the guarded-write, the read-filter splice, the migration idiom and the
dirty-store fixture would each exist twice before 64 arrives to make it four. ONE-IMPLEMENTATION
(CLAUDE.md §"ONE IMPLEMENTATION") says the policy is a function they call; the substrate IS that
function, and putting memory in the same wave is what makes it a function with a caller.

### 1.2 The substrate — what 63a builds, by name (the ONE-IMPLEMENTATION address for 64)

All in `loremaster` (store-reading orchestration — the ESC-1 split 62 ruled: `lorerunes` holds
predicates, `loremaster` holds entry points; nothing here goes to `lorerunes`). Symbol names are
proposals for the contract author; the SHAPES are the ruling.

1. **`loremaster.governed.resolve_subject(access_token, capability, *, registry, principal_store,
   keep_store) -> Subject`** — THE one place a `lorerunes.pdp.Subject` is constructed from a
   live call: `principal_id` + `role` from the token's principal (`PrincipalStore.get_by_email`
   on `access_token.subject`, which `token_verifier` sets to `principal.email` — verified), the
   agent via `stamp_owner` (62's seam, which after #425's closure returns the verified pair in
   ONE read), `visible_keep_ids` via `resolve_visible_keeps` (61b). Fail-closed: an absent/
   unverified capability, an unknown principal, or a `KeepStoreError` from the resolver → a
   typed `GovernedDenied` teaching error naming the missing step (`lore_comms action=register`
   mints the capability) — never an empty Subject, never a partial one (61 `Subject` already
   refuses empty ids, SEC-F3).
2. **`loremaster.governed.read_filter(subject, table) -> tuple[str, dict]`** — a thin wrapper
   over `authorize_filter(subject, Action.READ, table).to_surql()` whose ONE job is the splice
   contract: the fragment is self-contained (61 #416) and every consumer splices it as
   `AND ({fragment})` with the params MERGED under the PDP's content-addressed names
   (`_param_name`, collision-free by construction). The wrapper exists so the splice is one
   function, not a pattern.
3. **`loremaster.governed.guarded_write(subject, action, *, table, row_id, set_fragment,
   audit, store) -> GuardedWriteResult`** (`store` = the owning store's driver HANDLE — §10.6) — the single-row WRITE/DELETE/SET_SCOPE path: read the row's
   `(owner_principal, owner_agent, scope)` → build `Resource` → `authorize()` (deny → teaching
   error; `requires_audit` → compose `AuditStore.append_fragment` into the SAME transaction —
   61a built `append_fragment` for exactly *"what 63/64 compose"*) → execute the mutation as a
   GUARDED statement carrying `authorize_filter(action).to_surql()` in its WHERE and check the
   returned row count (0 rows = a concurrent scope/owner change between the read and the write
   → LOUD `GovernedConflict`, never a silent no-op). **This is the single-brain applied to
   writes:** the Python gate and the store guard are the SAME tree evaluated twice, so a write
   cannot land on a row the filter would exclude, and there is no read-then-write TOCTOU window
   on the governed columns.
4. **`surreal_schema._governed_field_specs()` + `_governed_index_statements(table)`** — ONE
   emitter for the three columns + the two indexes (§4.1), called by `_memory_statements`,
   `_message_statements`, and later `_task_statements`/`_finding_statements` (64) and
   `_brief_statements` (63c). Mutation proof: change the index set here → every governed
   table's schema pin moves.
5. **`lore-adm migrate-governed --table <t>`** (`principals.py` CLI family, the 60/61
   `lore-adm` precedent; ⚠ NO `--dry-run` and NO `dry_run=` — the operator STRUCK that paradigm
   from `lore-adm` on 2026-08-20 (*"Gate none. I hate that paradigm."*, packet-49 rulings), a
   ruling this line first shipped in ignorance of — corrected §10.7-W; the PREVIEW role is the
   separate READ verb `report-unmigrated --table <t>`) — the idempotent backfill verb, parametrised by a per-table
   `LegacyMapping` (§2.1) — ONE verb, N table rows, receipts-printing (rows scanned / backfilled
   / already-migrated / refused), exit non-zero on a precondition failure. Runs at the 65
   cutover, NEVER at boot (§2.3).
6. **The test substrate** (`loremaster/tests/_governed_contract.py` or a `conftest` family): the
   four parametrised pin families of §3.2, so a governed table's contract is a parametrisation,
   not a copy.

### 1.3 Riders — and pin/verify each like this

- **R-a.1 (substrate-with-consumer):** 63a's routing coverage pin (#420) is GREEN for
  `lore_remember`/`lore_recall` and RED_ADJUDICATED for every other governed verb, with owner +
  trigger per leg; the adversary's REACH ATTACK (P1c) must show the pin reds when a memory verb
  is un-routed (mutation: bypass `guarded_write` in `invalidate` → RED).
- **R-a.2 (no second Subject constructor):** an AST/structural pin that `Subject(` is
  constructed in production code ONLY inside `resolve_subject` (allowlist the ONE site;
  `lore_impact("lorerunes.pdp.Subject")` at 63a close must show exactly one production
  constructor). Fixture constructors in tests are exempt by tree.
- **R-a.3 (no second splice):** every production `SELECT` over a governed table that is a
  LIST read carries the fragment via `read_filter` — pinned by mutation (change `to_surql` of
  `ScopeEq` → every governed list-read's oracle moves; a read that stays green is a private copy).
- **R-a.4 (63b/63c order is a dependency, not a preference):** 63c's `brief`/`agent` scoping
  reuses 63b's session-keep binding; the contract for 63c cites 63b's shipped symbols by name.
- **R-a.5 (the 62 adjudication self-destructs per TOOL, the #420 pin per VERB):**
  `_GOVERNED_TOOLS_PENDING_OWNER_STAMP` loses `lore_remember`/`lore_recall` at 63a and
  `lore_comms` only at 63c close (the tool is routed when ALL its verbs are); the per-verb pin
  carries the finer adjudication. Two instruments, two granularities, both derived.

### 1.4 Sizing (the split law) + named triggers

63a ≈ 0.25–0.30 · 63b ≈ 0.25–0.30 · 63c ≈ 0.10–0.15. **Trigger:** if 63b's contract prices
> 0.30, split at the ONLY sound seam — **63b-i = session-keep binding + `register` + `send`**
(the write side + the mechanism) and **63b-ii = the filtered reads + migration + security-audit**
— never "mechanism without its security pins" (62 W2.5's rule, unchanged here).

---

## 2. Fork (b) — migration strategy per table (§7; the #107/#131 headline)

### 2.1 (i) The owner mapping — per table, honest, no fabrication

| table | legacy author provenance (verified) | `owner_agent` | `owner_principal` | disposition |
|---|---|---|---|---|
| `memory` | **NONE** — no author column; `source` is `{kind, ref, trust}`; migrated notes carry an `origin=claude_native_memory` label at most | NONE | NONE | **UNOWNED-LEGACY.** Readable + supersedable by the project keep's household (the WRITE keep disjunct needs no owner); hard-DELETE by admin only (the exact-owner DELETE predicate matches no NONE). Do NOT stamp the operator as author — provenance that was never recorded is not recovered by assumption. |
| `message` | `sender: record<agent>` — a REAL link; `agent.owner_principal` is `option<>` and NONE for every pre-62 agent | `= sender` (exact, resolvable, no heuristics) | `= sender.owner_principal` **after the agent backfill** (below); NONE if the agent is unresolvable (a dangling `sender` link — store-ref §2, links do not auto-clean — is a #105-class ghost: COUNT and REPORT it, leave NONE) | **OWNED-BY-LINK.** One `UPDATE message SET owner_agent = sender, owner_principal = sender.owner_principal WHERE scope IS NONE` — a field-through-hop on the WRITE side only (a one-shot migration, not a read predicate; §4's un-indexable-hop rule is a READ-path rule). |
| `agent` (the link target both depend on) | `owner_principal` NONE for all legacy rows | — | **backfill to the operator's real principal** (the 62 Fork-2 ruling: the local fleet IS the operator's principal, no sentinel) | **PRECONDITION-GUARDED.** The verb asserts, BEFORE writing, that EVERY legacy agent's `owner_principal` is NONE (`SELECT count() … WHERE owner_principal IS NOT NONE GROUP ALL` = 0). A store where any agent already carries a DIFFERENT owner is a multi-principal store → the verb REFUSES loud and names the rows; the operator adjudicates by hand. This is the single-principal-fleet premise turned into a checked precondition rather than a belief. |
| `brief` (63c) | `created_by: string` — an agent NAME with no session (`AppContext.comms` docstring: *"records `Brief.created_by` as the acting agent's own name"*) | NONE | NONE | **UNOWNED-LEGACY** — a bare name resolves to N agent rows across sessions (the registry id is `uuid5(session, name)`), so "best-effort" is a guess wearing a mapping. Do not guess. Briefs are project-wide standing instructions; the project keep's household reads + supersedes them (a new version is a new row, owned by its publisher). |

**Principal-DELETE disposition of `memory.owner_principal` (the FIFTH `record<principal>` link,
the first on a GOVERNED row — §10.7-Z, SF-63-5 **operator CONFIRMED 2026-08-30**):** ORPHAN-TO-NONE, AUDITED — never
cascade-delete (destroys household notes), never a silent dangle; REFUSE-loud meanwhile.

The **hard rule this table encodes:** a legacy row is owned by a LINK or by NOBODY. A string is
never promoted to an owner (§3.2.2 — identity never from a free-form value, and a migration is
just a very old write).

### 2.2 (ii) The grandfather scope — a concrete value, a mint, and a key

**RULING: the legacy scope value is `keep:<ulid>` of ONE canonical PROJECT keep** (type
`project`, name `lore`, keeper = the operator's principal), **minted by the migration verb at
the 65 cutover** (after 65 provisions the principal), **addressed by a NEW deterministic natural
key column `keep.key : option<string>` + `UNIQUE IF NOT EXISTS` index, with the value
`project:<lore.yaml slug>` = `project:lore`.** (SF-63-4 — this touches 60's shipped `keep`
table; additive, `option<>` per §1.4, `OVERWRITE` per §1.1, and §1.8 says the UNIQUE index
tolerates the many NONE keys manual keeps carry — exactly the fill-later shape 48 already relies
on for `principal.subject`.)

Why not the alternatives the brief names:
- **A sentinel scope string** (e.g. `legacy`) — REJECTED: 61's `_is_valid_scope` closes the
  domain to three fixed values + `keep:<id>`, and the READ predicate has no legacy disjunct. A
  sentinel means widening the IR (a lorerunes change 64 would also carry) for a value that
  exists only to mean "the project keep". Use the project keep.
- **"project" as a bare value** — it is a KEEP TYPE, not a scope (authorization-model §4;
  `SCOPE_*` constants in `lorerunes.pdp`). A scope is `keep:<id>`.
- **A config value naming the keep id** (`authz.project_keep_id`) — REJECTED as the PRIMARY
  address: a config carrying a store-minted ulid is a second source of truth that goes stale
  on any store restore. The natural key lives in the store; the write path resolves it by ONE
  indexed read (`KeepStore.get_by_key`), cached per-process at boot with a LOUD refusal if
  absent (a governed write with no project keep is a misconfigured deployment, not a silent
  fallback to `principal-private` — that would hide the fleet's notes from the fleet).
- **Minting the keep at boot** (`ensure_ready`) — REJECTED: a keep needs a keeper principal,
  and `ensure_ready` runs on every virgin test DB with no principal. The mint is a verb, run
  once, receipts-printing.

**The same key column serves 63b's SESSION keeps** (`key = 'session:<session>'`, type
`session`) — ONE mechanism (`KeepStore.get_or_create_keyed(key, *, type, keeper_email, name)`,
a CAS on the UNIQUE index per the store-ref §5 hot-row mint law: on a `UNIQUE` conflict from a
concurrent `register`, re-read and return the winner, never a second row). That is why the
column is `key` and not `project_slug`.

**How the fleet's CURRENT shared behaviour stays unbroken:** today every memory note and
every message is visible to every fleet agent. Post-migration every legacy row is
`keep:<project>`; every fleet agent's principal is the operator's (the agent backfill), and the
operator's principal is the project keep's keeper → auto-householded (60 Fork D) →
`ScopeInKeeps` matches → visible. New `lore_remember` rows default to the project keep (§10-N),
so a note saved after the cutover is still fleet-visible. Pin: a post-migration recall by a
fixture agent of the keeper principal returns the SAME row set as a pre-migration recall on the
seeded dirty store (byte-diff the served ids — Leg 2's healthy/degraded diff, applied to the
migration).

### 2.3 (iii) Backfill vs read-path tolerance — RULED: BOTH, with the roles fixed

- **The columns are `option<>` with NO DEFAULT** (store-ref §1.4 — a required field poisons
  every legacy row's next UPDATE and *"a DEFAULT does NOT rescue an existing row"*; the
  `status_set_at`/`declared_cadence`/`owner_principal` precedents on the populated `agent`
  table are the exact idiom). `ensure_ready` converges the SCHEMA on every boot via
  `_define_field` (OVERWRITE); it never touches DATA.
- **The read path tolerates absence BY CONSTRUCTION of the 61 predicate, and absence is
  FAIL-CLOSED:** a NONE `scope` matches no `scope = $x` disjunct in SurrealQL and `Resource`
  refuses a non-domain scope in Python, so a NONE-scope row is invisible to every member and
  visible to admin (`AllRows`) — precisely §7's *"an unowned-legacy marker that only admin
  sees"*, with no marker column. **RIDER (single-brain on the degraded row):** the substrate's
  Python leg must map a NONE-scope row to DENY (never raise on `Resource` construction, never
  skip it) so `authorize(row) ≡ filter.matches(row)` holds on dirty rows too — 61b's oracle F2
  bound (*"omits option<> NONE-owner rows"*) is CLOSED here by a dirty-row oracle leg over BOTH
  NONE-owner and NONE-scope rows. **Mechanism (contract-63a FORK 1, ruled §10.1): widen
  `lorerunes.pdp.Resource.scope` to `str | None` — `None` = the ABSENT (unmigrated legacy) scope,
  a named `lorerunes` touch; the empty-string forgery and every non-domain string still RAISE;
  `to_surql` never reads a `Resource`, so the emitted SurrealQL is byte-identical.**
- **Therefore the backfill is a FUNCTIONAL necessity, not a nicety:** without it the fleet
  loses sight of its own memory and history the moment the cutover boots. The verb (§1.2 item
  5) runs at the cutover; a forgotten run is LOUD in two places: (1) the deploy smoke's recall of
  a known legacy note returns nothing → the smoke fails; (2) a bounded boot-time
  `SELECT count() FROM <t> WHERE scope IS NONE GROUP ALL` per governed table, logged at
  WARNING with the count and the verb to run (the #131 lesson: a silent `(None, None)` for
  months is the failure shape; a count nobody renders is a hope). The count query is INDEX-SERVED on 3.2.4 (access `= NONE` on the `scope` index — probe-63 P5,
  lead-verified 2026-08-28), cheaper than a bounded TableScan; run ONCE per boot, and its plan
  is REPORTED in §4.4's probe (P5) so the claim stays measured, never believed.
- **The dirty-store pin family (§3.2 F1) seeds the legacy rows UNDER THE OLD DDL** — the
  store-ref §1.4 trap verbatim: *"a fixture that writes its legacy row after the migration
  cannot see this hazard at all."* Two seeds are required: (S1) a synthetic old-DDL seed for
  the unit pin; (S2) **a restore of the real production dump into a throwaway TEST-store
  database** (`/backups/lore/lore-prod-*.surql`, restored under `lore_test` on
  `ws://127.0.0.1:18000`, NEVER :18500) for the packet's dirty-store INTEGRATION pin — the
  fleet's own rows are the only fixture whose `sender`/`session`/`labels` distribution is
  real. The restore step is a committed script (brief-base §1: an instrument is a deliverable).

### 2.4 Scope on WRITE — defaults + the `scope=` argument's status

- **Defaults (authorization-model §10-N, realised):** `lore_remember` → `keep:<project>`;
  `lore_comms send` → `keep:<session keep>` (the session the sender registered in — SF-63-1);
  `brief_publish` (63c) → `keep:<project>`. Never `principal-private` by default for memory —
  that would silently privatise the fleet's shared notebook (the dogfood protocol's whole point).
- **An explicit `scope=` on `lore_remember` (and later on the other writers) is a
  PDP-VALIDATED REQUEST, not an identity claim** — admissible under 62's SF-1 reading exactly as
  the verified `capability=` is: the value is checked by the SAME `_grantable` predicate the
  SET_SCOPE action uses (61 D4(b): the fixed scopes + the caller's own keeps; a keep the caller
  is not householded in → DENY with a teaching error naming `lore-adm add-household`). ⚠ The
  authorization-model §3.2.3 sentence *"a member cannot mint a server-scoped row"* is
  SUPERSEDED by 61's ruled `_grantable` (server IS grantable by a member — §4.3's "freely, up
  or down, to any scope") — the code is the ruling; cite `lorerunes.pdp._grantable`, not §3.2.3.
- **The raw `owner=`/`as_agent=`/`created_by=` forms stay forbidden** (62 W2-R1 fuzz pin,
  extended per verb by §3.2 F4).

### 2.5 `SET_SCOPE` / `SET_OWNER` verbs in 63 — the narrowest useful set

`lore_remember(supersedes=…)` is a WRITE on the old row (close it) + a CREATE of the new one —
both route through `guarded_write`/the stamp. An explicit **re-scope verb for memory is NOT
built in 63** (a supersede with a different `scope=` achieves it, owned by the superseder); the
admin `set_owner` is NOT built in 63 either (no member-reachable need; 64's task/finding
ownership transfer is the first real consumer). Both DEFERRED with the named trigger *"the first
operator request to move a note between keeps without superseding it, or 64's ownership
transfer"*. The `Action` enum already carries both, so the PDP needs no change when they land.

### 2.6 The live fleet: what 63 must NOT do, and the 65 cutover order it must assume

63 is unserved; the deployed image is pre-retrofit; the fleet reads/writes comms+memory every
session against it. Nothing in 63 edits `.mcp.json`, the quadlets, the deployed container, or
the LIVE store. The design assumes 65 lands this sequence, atomically, fleet-quiescent:
(1) provision the operator principal + api-key (62 Fork 2 (b)/(c)); (2) rebuild+recreate → the
new DDL converges (the `DEFINE INDEX IF NOT EXISTS` on `scope`/`owner_principal` BUILDS over
every existing row ONCE at that boot, §1.5 — bounded, name the row counts in the smoke);
(3) `lore-adm migrate-governed` for `agent` → `memory` → `message` → `brief` in that ORDER
(agents first, because messages read `sender.owner_principal`); (4) the in-image conformance run
(#139) + the deploy smoke recalling a KNOWN legacy note through the new filter; (5) the fleet
re-brief: every governed call presents `capability=` (62 W2.6's orchestration obligation — a
post-cutover call without it DENIES with the teaching error, LOUD by design, never a silent
empty result). **63's contract pins (1)–(4) as a checked ORDER** (the verb refuses `message`
before `agent` has been migrated: it checks the agent NONE-count first).

---

## 3. Fork (c) — the 63↔64 boundary: what 63 EXPOSES, which pins land where

### 3.1 RULING: 63a is the substrate packet; 64 is a parametrisation of it

64 (tasks + findings) is the SAME retrofit over two tables whose legacy author IS a free-form
string (`task.owner`/`created_by`, `finding.created_by`, `actor`) — i.e. the one §7 case 63
does not exercise. So the substrate must be table-agnostic in exactly three places 64 will
stress: the `LegacyMapping` (§2.1 gets a fourth disposition for 64: **STRING-UNRESOLVABLE →
UNOWNED-LEGACY**, same as `brief` — a bare name is never promoted), the per-verb dispatch table
(64's `lore_tasks`/`lore_findings` carry `action=` dispatch like `_COMMS_ACTIONS`), and the
keep-scoped WRITE semantics (a Keep task is claimable by any household member — the WRITE
`keeps` disjunct 61 already emits; nothing new in the PDP).

**63 EXPOSES (the named seams 64 CALLS — §1.2 items 1–6, restated as a contract):**

| seam | 63a builds | 64 does | never |
|---|---|---|---|
| `governed.resolve_subject` | the one Subject constructor | calls it | constructs a `Subject` (R-a.2 pin reds) |
| `governed.read_filter` | the one splice | splices `AND ({fragment})` into `query`/`rollup` reads | writes `scope = $x` by hand |
| `governed.guarded_write` | the one guarded mutation + audit compose | routes `transition`/`claim`/`supersede`/`resolve`/`wontfix` through it | a bare `UPDATE task SET status=…` |
| `_governed_field_specs` + `_governed_index_statements` | the one DDL emitter | appends them in `_task_statements`/`_finding_statements` | re-declares the three columns |
| `lore-adm migrate-governed --table` + `LegacyMapping` | the verb + two mappings (link / unowned) | registers two more table mappings | a second migration script |
| the parametrised pin families (§3.2) | four families, parametrised by table + verb list | adds parametrisation rows | copies a test module |

**Coverage-as-a-checked-variable across the boundary (the #420 instrument, built in 63a):**
the routed-verb set is DERIVED as `partition_tools_by_population(live tools).governed` ×
each governed tool's OWN dispatch table (`_COMMS_ACTIONS` for `lore_comms`; the equivalent
`action` maps for `lore_tasks`/`lore_findings`; `lore_remember`/`lore_recall`/`lore_claim_task`
are single-verb tools whose verb is the tool). Each `(tool, verb)` is either OBSERVED routing
through `resolve_subject` + (`read_filter` | `guarded_write`) — observed at RUNTIME by
instrumenting the seams in the test (the CLAUDE.md instrument lesson: enforce at runtime,
check coverage as a variable — a `(tool, verb)` the test never exercised is RED, not green) —
or RED_ADJUDICATED in the `loremaster.server` constant `_GOVERNED_VERBS_PENDING_ROUTING:
dict[tuple[str, str], str]` (`(tool, verb) → trigger`, the direct sibling of 62's per-TOOL
`_GOVERNED_TOOLS_PENDING_OWNER_STAMP`) — NOT `scripts/pending_contracts.yaml`, whose
`extra="forbid"` schema is typecheck-bound (`PendingBound.files[].missing_symbols`) and cannot
carry a verb adjudication (contract-63a FORK 2, ruled §10.2). **The set REDS
when it grows and the observed set does not** (a new comms action, a new tool). 64's legs are
adjudicated *"packet 64 routes lore_tasks.<verb>"* at 63a close and self-destruct as 64 lands.

### 3.2 The four pin families that land in 63a as REUSABLE (parametrised, never cloned)

- **F1 — DIRTY-STORE MIGRATION** (`TestSchemaMigrationAgainstAnExistingStore` idiom,
  `test_surreal_store.py`/`test_principal_keys_schema.py` precedent, generalised): OLD DDL →
  seed legacy rows (owner-less, scope-less; for comms: with a real `sender` link to a legacy
  agent whose `owner_principal` is NONE) → NEW DDL (`ensure_ready`) → assert (i) the seed rows
  survive and are still UPDATE-able on an unrelated column (§1.4's poison check), (ii) BEFORE
  the verb runs the rows are invisible to a member Subject and visible to admin (the
  fail-closed leg), (iii) AFTER `migrate-governed` they are visible to the keeper's agents,
  carry the project keep scope, and the verb is IDEMPOTENT (second run: 0 backfilled, exit 0),
  (iv) the agent-first ORDER precondition refuses `--table message` on an unmigrated `agent`
  table. Parametrised by table + a seed function.
- **F2 — SINGLE-BRAIN ORACLE PER TABLE** (`test_pdp_oracle_61b.py` idiom, re-homed over the
  REAL table DDL instead of the bare `gov` fixture): for a fixture row set INCLUDING dirty rows
  (NONE owner, NONE scope, dangling `sender`), `{r : authorize(s,a,r).allowed}` ==
  `SELECT … WHERE <read_filter>` — byte-equal id sets, per action, per role. Parametrised by
  table.
- **F3 — CROSS-PRINCIPAL ISOLATION ∀ READ VERBS** (the §9 headline): ≥2 principals × ≥2 agents
  each; every read verb of the tool (memory: `recall` with and without `kind`/`labels`; comms:
  `drain`, `drain peek`, `await`, `story`, `rollup`'s message leg AND its count) returns ONLY the
  caller's visible set; the served COUNT equals the served set's size (trust-doctrine Leg 1 —
  a count over the unfiltered table beside a filtered listing is a false clear). Parametrised
  by tool + verb list; the verb list is DERIVED from the dispatch table so a new read verb
  joins the fixture or reds it (the quantifier law — ∀ verbs, forced per verb).
- **F4 — ANTI-INJECTION FUZZ PER WRITE VERB** (62 W2-R1 extended): for every governed write
  verb, hostile `owner_principal=`/`owner_agent=`/`as_agent=`/`created_by=`/`scope=<a keep the
  caller is not in>`/`scope=server` (the last two must DENY via `_grantable`, not be ignored)
  → the stamp is unchanged / the call is refused; only a VERIFIED `capability=` moves
  `owner_agent`. Parametrised by tool + write-verb list (derived).

**RIDER (and pin it like this):** sharing is proven by MUTATION at 63a close — change
`_governed_index_statements` (drop an index) → every governed table's schema pin reds; change
`read_filter`'s splice → every F3 row reds; rename a `LegacyMapping` disposition → every F1 row
reds. A family with a green consumer under mutation is a clone wearing the shared name.

### 3.3 What 63 does NOT do for 64 (explicit non-obligations)

- It does not add columns to `task`/`finding`, migrate their rows, or route their verbs.
- It does not decide 64's default scopes (`tasks → principal-private`, `findings → project`
  per §10-N) — 64 cites §10-N; 63's substrate takes the default as a parameter.
- It does not build `SET_OWNER`/admin re-own (§2.5) — 64 is its first consumer if needed.

---

## 4. Fork (d) — the read-filter store-law plan (§6) + the probe spec

### 4.1 The exact DDL ruled (per governed table, via the ONE emitter)

```
DEFINE FIELD OVERWRITE owner_principal ON <t> TYPE option<record<principal>>;
DEFINE FIELD OVERWRITE owner_agent     ON <t> TYPE option<record<agent>>;
DEFINE FIELD OVERWRITE scope           ON <t> TYPE option<string>;
DEFINE INDEX IF NOT EXISTS <t>_scope           ON <t> FIELDS scope;
DEFINE INDEX IF NOT EXISTS <t>_owner_principal ON <t> FIELDS owner_principal;
```

for `<t> ∈ {memory, message}` at 63a/63b (+ `brief` at 63c; + `task`, `finding` at 64), and on
`keep` (SF-63-4):

```
DEFINE FIELD OVERWRITE key ON keep TYPE option<string>;
DEFINE INDEX IF NOT EXISTS keep_key ON keep FIELDS key UNIQUE;
```

- Fields through `_define_field` (store-ref §1.1: OVERWRITE is the only clause that lands a
  changed definition); indexes through `_plain_index`/`_unique_index` (§1.1: an index
  OVERWRITE rebuilds and can hard-fail boot; §1.5). NO ASSERT on `scope` — an ASSERT on a
  populated table's new column would poison every legacy row's next UPDATE (§1.4); the domain is
  enforced at the WRITE seam (`Resource`/`_is_valid_scope`, one vocabulary in `lorerunes.pdp`).
  Re-open trigger for a store-side ASSERT: *"the day every row is migrated AND a write path
  outside `guarded_write` can reach the column"* — today the second condition is exactly what
  the routing pin forbids.
- **Why TWO indexes and not three:** #413 fact 4 (probed on 3.2.4): a composite is
  leading-column-only, and the READ predicate's disjuncts lead with `scope` (three of four)
  and `owner_principal` (the `principal-private` one) — `owner_agent` never LEADS a disjunct
  (it appears only ANDed under `scope='agent-private' AND owner_principal=…`), and the
  WRITE/DELETE paths are by-id (`type::record`). **`owner_agent` is NOT indexed at 63; named
  re-open trigger:** *"the first LIST read whose leading predicate is `owner_agent` (an
  agent-private-only listing verb), or a measured `agent-private` recall p50 regression
  attributable to the residual filter."* 61b's oracle fixture indexed all three; that was a
  probe-table convenience, not a ruling (Fork E named the composite question, the probe answered
  it: separate `scope` + `owner_principal`).
- **The index BUILD cost lands ONCE, at the 65 cutover boot** (§1.5: a define builds over
  every existing row; `IF NOT EXISTS` makes every later boot a no-op) — bounded by the two
  tables' row counts; the cutover smoke NAMES those counts.
- **No `to`-edge columns.** The delivery edge carries no owner/scope (§4.3) — ONE copy of the
  policy columns, on the `message` node.

### 4.2 The emitted predicate is index-served by construction (61b, cited not re-derived)

`_member_filter(READ)` emits `Or(And(scope=,op=,oa=), And(scope=,op=), scope=, (scope=k1 OR
scope=k2 …))` — a flat OR of equalities on indexed columns with the keep set EXPANDED (never
`IN`) and every node parenthesised (#413 + #416, both live-probed on 3.2.4 by
`scripts/probe_read_filter_61b.py`). Admin = `true` (AllRows) — a TableScan by definition, and
correct. No arrow-traversal anywhere: `$my_keeps` is pre-resolved by `resolve_visible_keeps`
(one leading-column IndexScan on `member_of`, 61 Fork F). 63 adds NOTHING to the predicate; the
re-probe in §4.4 exists because the COLUMN TYPES and the TABLES differ from 61b's fixture.

### 4.3 The `to`-edge inbox read — two steps, ONE fragment (ROUTING-IS-NOT-SHARING)

`drain`/`ack`/`await` read the recipient's `to` edges (`WHERE out = $agent …`, index
`to_out_seen_at`, leading `out`). The policy columns live on `message` (the edge's `in`), so
the tempting one-statement form `… AND in.scope = $k …` is a FIELD-THROUGH-HOP predicate — a
second, hop-qualified COPY of the fragment that `read_filter` cannot emit (the IR emits bare
column names by design) and that store-ref §4 says is un-indexable anyway. **RULED: two steps
in ONE transaction** — (1) the recipient-edge pre-filter as today (index-served, bounded by the
inbox), collecting the message ids; (2) `SELECT … FROM message WHERE id IN $ids AND
({read_filter fragment})` — the SAME unqualified fragment, index-served on `scope`. The CAS
stamp (`seen_at`/`acked_at`) is issued ONLY for the ids step (2) returned, so an invisible
message is neither served nor stamped. `await`'s wake count stays the RECIPIENT-EDGE count (a
contentless wake signal, not a served number — brief-base §5's own law); `drain`'s served
count is step (2)'s size. **Withheld deliveries are NOT rendered** (an "N withheld" line is an
existence leak); they ARE logged server-side at WARNING with the count. Given SF-63-1 (a
recipient is always in the session keep's household at send time) the withheld case arises only
after a later re-scope or on a legacy NONE-scope edge — rare, and loud where it can be.

### 4.4 The probe — SPECIFIED for a `probe-63` wave (63a), not run by me

My brief forbids code, and an instrument that establishes a load-bearing claim is a committed
deliverable (brief-base §1); a probe pasted into a design doc is the lesser form. So: a
`probe-63` agent COMMITS `scripts/probe_read_filter_63.py` (self-checking, exit 0 with positive
controls, throwaway `test_<pid>_<uuid4>` DB on `ws://127.0.0.1:18000` — NEVER :18500), mirroring
61b's probe, BEFORE 63a's contract is frozen. It must show, each with a pasted EXPLAIN:

| # | probe | over | expected / discovery |
|---|---|---|---|
| P1 | `WHERE scope = $s` | the REAL `_memory_statements` DDL (HNSW + FULLTEXT co-resident) with `scope option<string>` and ≥1 NONE-scope row present | IndexScan (`memory_scope`). **DISCOVERY — the one unprobed delta:** 61b probed a non-option `scope string` on a bare table. An `option<>` column's plain index over NONE rows is §1.8-adjacent territory the vendor is silent on. |
| P2 | the FULL `_member_filter(READ).to_surql()` for a member with 2 keeps | same | `UnionIndexScan` of `IndexScan` children, no `TableScan` of `memory` (#413 fact 3 re-confirmed on the real table) |
| P3 | P2 over the REAL `_message_statements` DDL | `message` with legacy rows (NONE owner/scope) + migrated rows | same verdict |
| P4 | the §4.3 step-(2) shape `WHERE id IN $ids AND (<fragment>)` | `message` | index-served (record-id `IN` + the fragment); report the plan — if the planner degrades to a TableScan under `id IN` + OR, the fallback is per-id `type::record` reads, and the probe says which |
| P5 | `WHERE scope IS NONE` (the §2.3 boot count) | both | **REPORTED, not required** — measured **IndexScan (`= NONE` on the `scope` index)** on 3.2.4 (probe-63, lead-verified 2026-08-28; a correction of this doc's earlier TableScan expectation — the P8d prose-currency class) |
| P6 | `WHERE key = $k` on `keep` after SF-63-4's UNIQUE index, with ≥2 NONE-key keeps present | `keep` | IndexScan; the two NONE rows coexist (§1.8 re-confirmed on THIS column) |
| C+ | positive controls | both | an un-indexed column equality → TableScan; `WHERE owner_agent = $a` alone → TableScan (proves the walker sees a TableScan AND documents the un-indexed `owner_agent` bound of §4.1) |

**RIDER (and pin it like this):** P1/P2/P3's verdicts become PINNED EXPLAINs in 63a/63b's
schema tests (the `test_keeps_schema.py::TestTheKeeperIndexFires` walker, not a re-written
one), each with its C+ control in the same test — a pin that cannot see a TableScan is not a
pin. The probe's exit status is a 63a gate receipt.

---

## 5. #425 — `stamp_owner` double-read TOCTOU: RULED CLOSE in 63a

**RULING: close it — collapse to ONE read.** `verify_capability` already PROJECTS
`owner_principal` (aliased `owner_email`) in its single verified SELECT and returns only the
agent id; `stamp_owner` then re-reads `owner_principal_of(agent_id)`. **Close it ADDITIVELY
(contract-63a FORK 3, ruled §10.3):** keep `verify_capability -> str | None` byte-compatible (13
shipped 62 call sites pin the bare id); move the four-condition check + the single SELECT into ONE
internal pair-yielding path that ALSO projects the bare owner id, have `verify_capability` return
its first element and `stamp_owner` consume the pair (ONE `_query` round-trip, the conditions
living ONCE — ROUTING-IS-NOT-SHARING); DELETE `owner_principal_of` —
`lore_impact` (2026-08-28 @ `8128c50`) shows `stamp_owner` as its ONLY production consumer
and zero covering tests (re-confirm at build time; the count is a heuristic).

**Why close rather than carry as a pinned bound:** the finding's own re-open trigger is *"63/64
introduces owner mutation (admin set_owner, or ANY `owner_principal` UPDATE)"* — and §2.1's
cutover backfill IS an `owner_principal` UPDATE on the `agent` table, introduced by THIS packet.
A bound whose trigger the bounding packet pulls is not a bound; it is a defect scheduled for
discovery. The fix is one projection + one return type (the finding names it), the deferral law's
*"if the next agent would just do what you could do now, do it now"* applies, and every governed
write in 63 calls the seam — the cheapest moment to close it is before the first consumer.

**RIDER:** the closure is pinned by the 62 security fixture re-run (36 exploits, 0 succeeded —
`receipts/2026-08-24-packet62/REPORT-secaudit-62w2.md`) plus ONE new leg: a concurrent
`owner_principal` re-stamp injected between what used to be the two reads must be unable to
change the stamped owner (there is no window to inject into — assert `stamp_owner` issues
exactly ONE store round-trip, counted via the `_query` seam).

---

## 6. The §9 security-auditor target for 63 — cross-principal isolation OVER THE WIRE

Stated so the auditor attacks a named target (CLAUDE.md: a gate needs a threat model).

**IN scope (must hold, over the MCP wire, on the REAL tables):**
1. **Cross-principal read isolation ∀ verbs** — principal B's agents never receive A's
   `principal-private`/`agent-private`/keep rows through `lore_recall`, `lore_comms
   drain/peek/await/story/rollup` (63b), `brief_get`/`fleet` (63c). Fixture: F3 (§3.2) — ≥2
   principals × ≥2 agents, keeps with disjoint households, one shared session.
2. **The served COUNT is over the served SET** — a rollup/drain count that includes withheld
   rows is a false clear (trust-doctrine Leg 1).
3. **Session admission is keeper-gated for a FOREIGN principal (SF-63-1)** — B `register`ing
   into A's session (knowing only the session STRING) is DENIED with a teaching error until A's
   keeper adds B's principal to the session keep's household; B cannot read A's session
   messages by guessing the string. This is THE comms headline.
4. **Anti-injection ∀ write verbs** — F4 (§3.2): no argument moves the stamp; `scope=` is
   PDP-validated (a non-householded keep or a foreign private scope DENIES).
5. **Single-brain on DIRTY rows** — F2 over NONE-owner, NONE-scope, and dangling-`sender` rows:
   no row is visible-but-unwritable-by-a-different-rule or writable-but-invisible.
6. **The migration cannot widen visibility** — the backfill's precondition (§2.1: refuse on a
   multi-principal `agent` table) is attacked: seed one foreign-owned agent → the verb refuses
   ALL tables and writes nothing.
7. **The guarded write has no TOCTOU** — a re-scope landing between `guarded_write`'s read
   and its UPDATE yields `GovernedConflict` (0 rows), never a write on the moved row.

**Leg-2 forgery table (the trust doctrine's derived failure set — dependencies × verbs; each
row's healthy vs degraded bytes must DIFFER, and the pin constructs the state):**

| dependency | stale | empty | wrong-instance | partial |
|---|---|---|---|---|
| `resolve_visible_keeps` | a keep the caller LEFT still in the set → construct: remove membership, recall → the keep's rows must vanish (no cache; one read per call) | member of no keep → recall serves ONLY private + server rows and the render NAMES the bound ("visible via 0 keeps") — never "no memories match" | keep store of another DB → `KeepStoreError` → DENY loud | resolver read fails mid-list → DENY, never a shorter set |
| `stamp_owner` | retired capability → DENY (62 W2-R3) | absent capability → DENY + teaching | capability of another principal's agent → binding DENY (62 W2-R2) | — (one read after #425) |
| the migration | half-run (agents migrated, messages not) → messages invisible to members, boot WARNING count ≠ 0, smoke fails | no project keep → governed write REFUSES (misconfigured deploy), never falls back to private | restored dump from another project → `key='project:<slug>'` mismatch → refuse | verb crashed mid-table → idempotent re-run completes; count query shows the remainder |
| the store | index absent (dirty pre-cutover) → P1–P3 pins red | table empty → served "0 visible" with the bound named | — | a `to` edge whose `in` message is filtered out → not served, not stamped, logged |

**ACCEPTED bounds (named, not defects):** (i) within ONE principal, every agent reads every
sibling's `principal-private` rows — the §4 table's ruling, not a leak; (ii) a session keep's
household is by-registration for the KEEPER's principal only — the keeper's own agents join by
knowing the session string, which is the spawn-brief's existing trust channel; (iii) admin sees
everything (§10-K); (iv) the `to`-edge count that wakes `await` may count an invisible delivery
— a contentless wake is benign by the comms design's own law.

---

## 7. Sub-forks — OPERATOR CONFIRMED 2026-08-28 (all four; every recommendation adopted)

- **SF-63-1 — the SESSION KEEP by registration (63b).** **operator CONFIRMED 2026-08-28 (recommendation adopted)** — ADOPT. RULE: `lore_comms register` gets-or-
  creates the keep `key='session:<session>'` (type `session`, keeper = the FIRST registrant's
  principal) and `send` stamps `scope = keep:<that id>`. The keeper's OWN principal's agents
  auto-join by registering (their `owner_principal` is already a household member — the
  keeper is auto-householded, 60 Fork D); a FOREIGN principal's register into an existing
  session keep is DENIED with a teaching error until the keeper `add-household`s that
  principal (60's verb). **Recommend ADOPT** — it realises §4 *"a thread/session channel = a
  keep-scoped set"* and §10-N *"comms → conversation-group"* with ZERO new PDP nodes, keeps the
  single-principal fleet byte-unchanged in behaviour, and closes the guessed-session-string
  hole before hosting. The one letter it changes: 60 Fork D's *"the keeper manages the
  household"* gains a pinned exception for the keeper's own principal on `type=session` keeps.
- **SF-63-2 — the `agent` roster + `brief` table as GOVERNED populations (63c).** **operator CONFIRMED 2026-08-28 (recommendation adopted)** — ADOPT. `fleet`
  renders every agent's `last_note`/`task_id`/`status` and `brief_get` serves standing
  instructions — both are per-principal data once hosted. RULE: `agent` rows are scoped to
  their session keep (owner = the row's own `(owner_principal, id)`), `brief` rows to the
  project keep (owner = publisher). **Recommend ADOPT**; the alternative (leave them
  shared-read) is a §9 gap 65 would ship. This adds two governed tables to the reach set —
  the growth pin will red until they are classified, which is the instrument working.
- **SF-63-3 — DM auto-creation on `send to=[…]` (§10-L) DEFERRED from 63** (overriding 60
  Fork E's *"auto-creation-on-send is packet 63"* hand-off). **operator CONFIRMED 2026-08-28 (recommendation adopted)** — DEFER, re-open trigger = the first cross-principal session. Reason: in the single-principal
  fleet a per-pair DM keep is DEGENERATE (a 1-principal keep), and the session keep already
  bounds every directed message to its session's household; today's reads that are NOT
  recipient-bound (`story`, rollup) become household-bound, which is the isolation that exists
  to be had. **Named re-open trigger:** *"the first cross-principal session (two principals in
  one session keep's household) — at which point a directed message inside that session needs
  recipient-only readability across `story`/rollup, and the 2-member `dm` keep is minted at
  send."* **Recommend DEFER** with that trigger pinned (a test that asserts `send` does NOT mint
  a keep, carrying the trigger in its message).
- **SF-63-4 — `keep.key option<string>` UNIQUE on 60's shipped `keep` table + a
  `KeepStore.get_or_create_keyed` CAS mint.** **operator CONFIRMED 2026-08-28 (recommendation adopted)** — ADOPT. Additive, §1.4/§1.8-compliant, pre-authorized as
  production-touching; a design decision because it ADDS a capability to a shipped substrate
  (60 Fork B deferred name-uniqueness with a trigger; this is a different column with a
  different job). **Recommend ADOPT** — the alternative addresses (a config ulid; a `(type,
  name)` lookup over a non-unique `name`) are both second sources of truth.

---

## 8. Reuse ledger (DRY — brief-base §6) + removed-behaviour inventory heads-up

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `governed.resolve_subject` | `lore_impact("lorerunes.pdp.Subject")` (run 2026-08-28 @ `8128c50`) | **1 prod / 12 test references** — the one production reference is the `lorerunes` package re-export, not a constructor; every constructor is a test/oracle fixture | **HAND-ROLLED** — the constructor 61 Fork D deferred to "62 fills, 63/64 produce Resources"; nothing to extend |
| `governed.read_filter` | `lore_get_symbol("authorize_filter")` | the PDP entry point, returns a `Predicate` | **EXTENDED** `authorize_filter` — a splice wrapper, not a re-implementation of the predicate |
| `governed.guarded_write` | `lore_get_symbol("AuditStore.append_fragment")` + `execute_transaction` | the composable audit fragment 61a built *"for what 63/64 compose"*; the verified txn seam | **EXTENDED** both — composes them; the guard is `authorize_filter().to_surql()` reused |
| `_governed_field_specs` / `_governed_index_statements` | grep `_define_field(\|_plain_index(` in `surreal_schema.py` | the per-table `_*_statements` idiom (Variant A/B, packet-48 memory) | **EXTENDED** the emitter idiom — one shared spec tuple consumed by N `_<table>_statements` |
| `lore-adm migrate-governed` + `LegacyMapping` | grep `migrate\|backfill` in `loremaster/` + `scripts/` | no data-migration verb exists (only DDL `REMOVE FIELD IF EXISTS` in `_memory_statements`) | **HAND-ROLLED** — the first row-backfill in the repo; the `lore-adm` CLI family is the home (60/61 precedent) |
| `KeepStore.get_or_create_keyed` | `lore_get_symbol("KeepStore.create_keep")` | non-idempotent `ulid()` create + keeper auto-household in one txn | **EXTENDED** `create_keep` — same txn shape + a UNIQUE-conflict CAS re-read (store-ref §5) |
| `verify_capability` → returns the pair (#425) | `lore_get_symbol` + `lore_impact("AgentRegistry.owner_principal_of")` (run 2026-08-28 @ `8128c50`) | a second read of a column the first SELECT already projects; **exactly 1 prod consumer (`loremaster.owner_stamp.stamp_owner`), 0 tests** | **EXTENDED** `verify_capability` ADDITIVELY (its return shape is unchanged; the shared pair-yielding path underneath is the extension — §10.3); `owner_principal_of` DELETED with the #425 closure (its only consumer stops calling it — re-confirm with `lore_impact` at build, the count is a heuristic) |

**Removed-behaviour inventory (the tdd Phase 0 / adversary P6b instrument — the builder
enumerates; these are the items I can already see):** (1) `lore_recall`/`lore_remember` today
answer with NO identity argument — post-cutover an identity-less call DENIES (dropped-
deliberately: §3.2.2; pinned as a teaching error, never a silent empty result); (2) `drain` is
today ONE statement (edge read + CAS) — becomes two steps in one txn (preserved-with-pin: the
served set and the stamped set are still equal, F3); (3) `rollup`'s message count is today
unfiltered (dropped-deliberately: Leg 1); (4) `register` today mints no keep (changed: SF-63-1;
the keeper-gated foreign-principal DENY is NEW behaviour, pinned); (5) `owner_principal_of`
(deleted with #425 if unconsumed — re-derive).

---

## 9. Riders roll-up — the "and pin it like this" list (contract / adversary / auditor)

1. **R-a.1–R-a.5** (§1.3): substrate-with-consumer coverage; ONE `Subject` constructor; ONE
   splice (mutation-proven); 63b→63c dependency; tool-level vs verb-level adjudication.
2. **Migration (§2):** F1 with the legacy row written UNDER THE OLD DDL (§1.4 trap); the
   single-principal PRECONDITION attacked (§6 item 6); agent-first ORDER refused out of order;
   idempotence (second run = 0 backfilled); the pre/post recall byte-diff on the restored prod
   dump (§2.2); the boot WARNING count present and non-zero on an unmigrated store (§2.3); NONE
   scope → member-invisible / admin-visible on BOTH legs (single-brain on dirty rows).
3. **Defaults (§2.4):** memory default = project keep (a fixture that asserts a fleet agent's
   recall sees a sibling's fresh note); `scope=` validated by `_grantable` (the SAME predicate
   — mutation: change `_grantable` → the write-time validation moves too).
4. **63↔64 (§3):** the routed-verb set DERIVED (tool population × dispatch table) and
   RUNTIME-observed (a verb the test never exercised is RED); 64's legs adjudicated by name;
   the four families mutation-proven shared at 63a close.
5. **Store law (§4):** the exact DDL through `_define_field`/`_plain_index`; two indexes, the
   `owner_agent` bound pinned with its trigger; P1–P3 as PINNED EXPLAINs with C+ controls in the
   same test; the two-step drain's served-set == stamped-set; `await`'s count is a wake, not a
   served number.
6. **#425 (§5):** exactly ONE store round-trip in `stamp_owner`, asserted at the `_query` seam;
   the 62 security fixture re-run green.
7. **§9 (§6):** F3 ∀ read verbs (derived verb list) + the served-count-equals-served-set pin;
   the foreign-principal session DENY (SF-63-1) with the positive control (the keeper's own
   second agent registers fine); the Leg-2 table's rows CONSTRUCTED, not reasoned.
8. **Renders (trust Leg 1):** every governed list-read render carries ONE line naming the bound
   it applied, DERIVED from the `Subject` (principal, agent, N keeps) — never hand-written
   prose; hostile fixture for any rendered stored text stays as standing law.
9. **Prose currency (P8d class):** at each wave close, a BARE grep for the retired premise
   *"free-form created_by"* / *"no governed tool routes"* / `owner_principal_of` across
   `loremaster/`, `docs/`, and the two tool descriptions; every hit gets a file + verdict.

---

## 10. Contract-phase rulings (2026-08-28, contract-63a — `lore_comms #8007`)

Five forks surfaced by the 63a RED contract (`REPORT-contract-63a.md` §ESCALATIONS; 52 RED / 12
GREEN, gate-clean). Each ruled here so the ruling lives in the committed artifact. **None is
MAJOR → operator**; the one candidate (10.1) is a minimal additive widening of a shared type that
the §2.3 rider ALREADY required, with every shipped pin green — a lorerunes touch is a
writable-set question for the lead, not a scope question for the operator.

### 10.1 FORK 1 — `Resource.scope: str | None` → RULED reading (1), a NAMED `lorerunes` touch
- **Ruling:** widen `lorerunes.pdp.Resource.scope` to `str | None`. `None` means ONE thing — an
  ABSENT (unmigrated legacy) scope. `__post_init__` keeps rejecting `""` (the forgery vector,
  SEC-F3) and every non-domain string (`_is_valid_scope` unchanged); only the literal `None`
  branch is new. Reading (2) — a NONE-scope short-circuit OUTSIDE `authorize` — is REJECTED: it is
  a second decision path, the #102 defect the single-brain exists to prevent.
- **Why not MAJOR:** the shipped 61 domain pin (`lorerunes/tests/test_pdp_core.py::
  test_resource_rejects_a_scope_outside_the_domain`, parametrised over `"public" "keep" "keep:"
  "private" "" "Server"`) does NOT name `None`, and `test_resource_has_no_default_for_scope`
  still holds (no default) — every shipped pin stays green; `to_surql` never reads a `Resource`,
  so §4.2's "63 adds nothing to the predicate" is literally true; and `matches` needs no change
  (`None == 'server'` is False, `None in keeps` is False, `AllRows` is True).
- **RIDERS — and pin it like this:** (i) a NEW lorerunes pin: `Resource(scope=None)` constructs;
  for every member `Subject`, READ/WRITE/SET_SCOPE `matches` is False and admin is True;
  `Resource(scope="")` still raises. (ii) ⚠ **DELETE is scope-INDEPENDENT (61 D4(a))** — an exact
  `(principal, agent)` owner CAN hard-delete its own NONE-scope row; the F2 dirty-row oracle
  leg MUST include `Action.DELETE` as the positive control that a NONE-scope row is not
  universally invisible (a fixture that only tests READ would pass a build that special-cases
  `None` to "deny everything"). (iii) the `Resource` docstring says `None` = legacy/unmigrated,
  never "any scope"; the 61 Fork D rider sentence in `2026-08-22-packet61-pdp-audit-rulings.md`
  is NOT edited (archived rulings stay as ruled — this doc supersedes it by citation). (iv) the
  lead names the `lorerunes` file in 63a's builder writable set explicitly (R-a.2's
  "one production `Subject` constructor" pin is untouched by this).

### 10.2 FORK 2 — the per-verb adjudication home → CONFIRMED `_GOVERNED_VERBS_PENDING_ROUTING`
- **Ruling:** `loremaster.server._GOVERNED_VERBS_PENDING_ROUTING: dict[tuple[str, str], str]`
  (`(tool, verb) → trigger`), sibling of 62's `_GOVERNED_TOOLS_PENDING_OWNER_STAMP`. §3.1 is
  corrected above; `scripts/pending_contracts.yaml` stays a typecheck-bound registry.
- **RIDERS:** (i) the STRUCTURAL half (`derived == routed ∪ pending`, `routed ∩ pending = ∅`,
  non-blank triggers) is admissible ONLY because each ROUTED entry has a BEHAVIOURAL leg — so a
  meta-pin asserts that the set of verbs with a behavioural routing test ⊇ `_GOVERNED_VERBS_ROUTED`
  (a verb declared routed with no observation is the hidden-constant reach defect, INSTRUMENT-0);
  (ii) the verb DERIVATION is fail-closed at the TOOL level: a governed tool with no recognised
  dispatch table contributes exactly ONE verb `(tool, tool)` — never zero (see 10.4).

### 10.3 FORK 3 — #425 → RULED the ADDITIVE close (§5 corrected above)
- **Ruling:** `verify_capability -> str | None` keeps its shape (13 shipped call sites pin the
  bare id — re-derived by grep this session; 12 in `test_agent_capability.py`, 1 in
  `test_agent_capability_seams.py`). The four admission conditions + the single SELECT move into
  ONE internal pair-yielding path (name for the builder: `_verify_capability_owner(presented,
  token) -> tuple[agent_id, owner_principal_id] | None`) that additionally projects the bare owner
  id; `verify_capability` returns its `[0]`; `stamp_owner` consumes the pair; `owner_principal_of`
  is DELETED (1 prod consumer, 0 tests — measured). Same one-read / no-TOCTOU property, zero
  breakage, and the conditions live ONCE.
- **RIDERS:** (i) mutation — alter ONE admission condition in the shared path → BOTH the 62
  `verify_capability` pins AND the 63a `stamp_owner` pins move (a `verify_capability` that
  stopped delegating would be a private copy wearing the shared name); (ii) `stamp_owner` issues
  exactly ONE `_query` (already pinned, form-agnostic — keep it so); (iii) ⚠ the contract's
  `FakeRegistry.verify_capability` currently returns `tuple[str, str] | None` — the LITERAL shape
  this ruling rejects. A fake whose signature differs from the real seam is a fake that cannot
  fail: rename it to the ruled pair-path name and keep `verify_capability`'s shape on the fake
  identical to the real one. The adversary checks fake-shape == real-shape.

### 10.4 FORK 4 — D1 (tool-level pin relaxed to `pending ⊆ governed`) → CONFIRMED, with a rider
- **Ruling:** the relaxation is legitimate — `lore_remember`/`lore_recall` leave the per-TOOL
  pending dict at 63a while staying governed, so exact equality cannot hold; orphan detection
  RELOCATES to the per-verb pin (`test_governed_routing_63a.py::
  test_every_governed_verb_is_routed_or_adjudicated`, `derived == routed ∪ pending`).
- **RIDER (the condition under which the relocation preserves what it claims):** a NEW governed
  TOOL is caught by the verb pin ONLY if it contributes ≥1 derived verb. So the verb derivation
  defaults a tool with no recognised dispatch table to the single verb `(tool, tool)`
  (fail-closed), and a discriminator pins it: a synthetic governed TOOL with no dispatch table
  reds the verb pin (the existing synthetic-VERB discriminator does not cover this case). Without
  that rider, D1 would have silently LOST tool-level orphan detection — the exact class the
  reach law names.

### 10.5 FORK 5 — the identity seam → CONFIRMED `capability=` at the TOOL, `subject=` at the BACKEND
- **Ruling:** two layers, one constructor, one error type. The MCP tool surface takes an
  OPTIONAL `capability=` (`lore_recall(capability=…)`, `lore_remember(capability=…)`), resolved to
  a `Subject` at the `AppContext` via `resolve_subject` (R-a.2 — the ONE constructor; the tool
  layer is the composition root that may read the token/registry). The BACKEND
  (`LocalMemoryBackend.recall/remember/invalidate`) takes an OPTIONAL typed `subject=` and NEVER a
  capability string (it must not read the environment). An absent identity at EITHER layer is
  `GovernedDenied` with a teaching message naming `lore_comms action=register` as the mint —
  never a `TypeError`, never a silent empty result (removed-behaviour 1).
- **RIDERS:** (i) the `capability=` parameter description is ONE shared constant across every
  governed tool (the packet-45 guarded `agent=` description idiom at `server.py` — never N
  copies of the teaching prose); (ii) the identity-less pins hold at BOTH layers (the contract's
  backend-level pins stand; add the tool-level twin); (iii) `_exercise_recall/_exercise_remember`
  stay the ONLY place the wiring is spelled, so this ruling is a one-function edit.
- **CLARIFICATION (2026-08-29, contract-63a-3 §FORK / `lore_comms #8012`) — Reading A CONFIRMED
  as the faithful §10.5 implementation; Reading B (the backend accepts `capability=` and resolves it
  internally) is REJECTED — it makes the backend read the environment (registry + token), the
  layering §10.5 forbids.** At `631701e` the `_exercise_*` seam still calls
  `backend.<verb>(…, capability=…)` (inherited from the pre-§10.5 contract), so on a compliant
  build the whole `retrofit_world` suite would `TypeError` — a latent C-DEF the adversary's
  satisfiability bound did not cover. The reshape is exactly rider (iii)'s one-function-family
  edit, and its SHAPE is ruled here so it is not improvised: (1) `_exercise_recall/_remember/
  _invalidate` play the TOOL-LAYER role — each resolves `capability → Subject` by calling the REAL
  `governed.resolve_subject(access_token(subject=<email>), capability, registry=…,
  principal_store=…, keep_store=…)` from `retrofit_world`, then calls
  `backend.<verb>(…, subject=subject)`; a test-side `Subject(...)` construction is FORBIDDEN (it
  would make the routing observation a fixture, not the production seam — R-a.2's spirit in the
  test tree). (2) The backend signature is `subject: Subject | None = None` and `None →
  GovernedDenied` (teaching), so the existing backend-level identity-less pins
  (`backend.recall("anything")`) survive UNCHANGED; the tool-level twin
  (`AppContext.recall(query)` with no `capability=` → `GovernedDenied`, never `TypeError`) is the
  separate pin rider (ii) already names. (3) `scope=` is the ONE wire argument that legitimately
  crosses into the backend beside `subject=` — it is a PDP-validated REQUEST (§2.4, `_grantable`
  against the Subject), not identity. (4) F4's hostile-ARGUMENT fuzz (`owner_*=`, `as_agent=`,
  `created_by=`) lives at the TOOL surface (the 62 input-schema pin + an unknown arg refused by
  the MCP layer); at the backend, with a typed `Subject`, a hostile kwarg is merely a `TypeError`
  and proves nothing — the backend-level F4 leg pins the EFFECT: the stored `(owner_principal,
  owner_agent)` equals the resolved Subject's, whatever else the call carried. (5) Sequencing: the
  reshape lands BEFORE the adversary re-grades (a re-graded seam is the baseline the builder
  builds to); the reshaper's writable set is `_exercise_*` + the capability fixtures ONLY.
- **Surfaced, not silently narrowed (adversary R1/R2, latent for 63b/64):** the
  `_dispatch_verbs` `{lore_comms → …}` map in `test_governed_routing_63a.py` is a hidden hand-list
  (the exact class 10.2 rider (ii) forbids), and the `@observes_routing` meta-pin observes a MARKER
  rather than the effect-for-that-verb. Acceptable at 63a ONLY as RED_ADJUDICATED bounds with the
  trigger *"63b derives `lore_comms` verbs from `_COMMS_ACTIONS` itself and keys the meta-pin on
  each verb's effect"* — the memory verbs' behavioural legs (F3/F4 effects) are what make the
  63a instance honest meanwhile.

---

### 10.6 BLOCKER 2 (adversary-63a-2, `lore_comms #8015`) — `guarded_write` reaches the store through the OWNER'S DRIVER HANDLE, injected
- **Ruling — option (c), a typed injection of the connection-OWNER triple; NOT a raw connection,
  NOT a single-statement `query=` seam, NOT a per-store method.** `guarded_write(..., store=)`
  takes ONE value carrying exactly what the shared driver seams already take — `acquire`,
  `drop`, `url` (`store/_txn.py::run_query` / `execute_transaction` signatures) — packaged as a
  small frozen `StoreHandle(acquire, drop, url)` in `loremaster/store/_txn.py` beside the seams
  (loremaster, not lorerunes: it carries connection callables). Every governed store exposes it
  through ONE accessor (`LocalMemoryBackend.handle` → its own `_ensure_connection` /
  `_drop_connection` / `_url`; 64's task/finding ledgers the same — they already own that triple,
  the packet-48 owner idiom). Inside `guarded_write`: the pre-read via `run_query(acquire=…,
  drop=…, url=…)`; the guarded mutation + the audit fragment via `compose(mutation, audit)` →
  `execute_transaction(…, acquire=…, drop=…, url=…)` — ONE verified multi-statement transaction
  (store-ref §3), every SDK call inside the retry/self-heal driver (#120/#108; the `_sdk_guard`
  runtime gate sees no escape).
- **Why the alternatives fail, each on a law:** (b) a method on the memory store makes 64 write a
  second copy per store — #102. (a-raw) a `connection=` param is an SDK escape past the driver —
  the R4 class the adversary itself flagged. (a-query) `query=self._query` is the SINGLE-statement
  seam (`run_query`): it cannot run the mutation AND the audit CREATE as one verified `BEGIN …
  COMMIT` — either two round-trips (a mutation without its audit row is exactly the §9 "compromised
  admin erases its trail" shape, from the other side) or a hand-rolled multi-statement string
  through the statement[0]-only `.query()` trap. The adversary's `query=` reference passed the
  pins only because no pin yet exercises audit ATOMICITY — a green measurement after a silent
  design gap (rider below).
- **Not MAJOR:** a table-agnostic substrate signature mirroring the shape every store already
  passes to the driver; changes 4 frozen substrate call sites + the retrofit backend (directly
  caused — a contract fix). 64 consumes it unchanged.
- **RIDERS — and pin it like this:** (i) **the FALSE-PASS vanished-conflict pin gets a REAL
  handle and a positive control in the SAME test:** the owner's guarded write on an existing row
  returns `row_count == 1` through that handle, THEN the row is deleted and the identical call
  raises `GovernedConflict` — so a no-handle / dead-seam build cannot pass (it fails leg one);
  `row_count` is read BACK from the guarded statement's `RETURN` (the `messages.py` ack-CAS
  precedent — the ACTUAL stamp, never a pre-read count). (ii) **audit atomicity, both legs:** an
  admin bypass write appends exactly +1 audit row (existing pin) AND a mutation the store REJECTS
  (a `set_fragment` violating an ASSERT) appends ZERO — before == after — proving the audit rides
  the same transaction, not a second round-trip. (iii) **the TOCTOU leg uses the injected
  handle as the instrument:** wrap `acquire` so a re-scope `UPDATE` lands between `guarded_write`'s
  pre-read and its mutation → `GovernedConflict`, the row untouched — deterministic, no 8-way race
  needed for THIS property. (iv) **mutation-prove the driver routing:** swap the handle's
  `acquire` for one that counts → every `guarded_write` pin observes ≥1 acquire; a build that
  bypasses the handle for any statement reds it. (v) **DRY:** the contract author runs
  `lore_search("connection owner acquire drop url handle")` before minting `StoreHandle` and
  records the row (the adversary's `run_governed_query(connection, …)` shim is the wrong
  direction — it takes a raw connection).
- **R4 — `migrate_governed` / `report_unmigrated_governed_rows` → RULED: the SAME `StoreHandle`,
  never a raw connection.** Production code in `governed.py` issues no `connection.query`; both
  route through `run_query` / `execute_transaction` over the injected handle. `lore-adm
  migrate-governed` builds the handle the way every store does (the shared `bootstrap_session`
  + the store's owner triple — borrow the target store's `handle`), so the verb and the tool
  path share one driver and one retry policy. Pin: an AST/`_sdk_guard` leg that `governed.py`
  contains no direct SDK call site.

---

### 10.7 build-63a forks (`lore_comms #8021`, build GREEN @ `a8c17c1`) — Y · Z · W

**10.7-Y — the tool layer: RULED "wire it, don't skip it" — RECOMMEND a bounded 63a-ii BEFORE the
cold audit; skip-with-trigger ACCEPTED only as the lead's sequencing call, with two riders.**
**⚠ OPERATOR CHOSE (A) — 63a-ii before the cold audit — 2026-08-30 (via lead-63 /
AskUserQuestion, `lore_comms #8023`); the skip-with-trigger alternative and its two riders are
MOOT. The cold audit grades the WHOLE 63a (`a8c17c1` + 63a-ii).**
- **The fork as posed (skip vs re-point 18 tests) is downstream of a scope narrowing I did not
  make:** R6 leaves the `AppContext` composition root UNWIRED, so the served `lore_recall` /
  `lore_remember` DENY every call — identity-bearing included. §1.1 named those two tools as 63a's
  retrofit and §10.5 ruled `capability=` at the tool surface resolved by the ONE constructor; a
  backend-only retrofit with a deny-all tool layer is fail-CLOSED (no leak, a teaching error — the
  designed degraded state, not a false clear) but it is NOT the retrofit 63a was scoped to ship.
  The build's own trigger says so: *"the deny will start FAILING them then"* — a skipped test is a
  hope with a filename (CLAUDE.md), and 18 of them is a hand-list of hopes.
- **Recommendation (A):** a bounded **63a-ii** wave (~0.05–0.10): ONE `AppContext._resolve_subject
  (capability)` helper (reads `get_access_token()`, calls `governed.resolve_subject` with the
  context's registry / principal store / keep store — the helper every governed handler in 63b/63c/
  64 then CALLS, never re-spells); `capability=` on the two memory tools (the shared parameter
  description, §10.5 rider (i)); the 18 `test_mcp_server` bodies RE-POINTED to the capability path
  (an `app_context` fixture that registers an agent, captures the minted capability, patches
  `get_access_token`) — not skipped. Then the cold audit grades a memory retrofit whose SERVED
  surface works. *"If the next agent would just do what you could do now, do it now."*
- **If the lead rules sequence (B — skip until 63b), two riders make the deferral honest:**
  (i) the #420 adjudication SPLITS the memory verbs' status — backend-ROUTED (green) vs tool-layer-
  WIRED (RED_ADJUDICATED, trigger "63a-ii / 63b wires the composition root") — so the currency gate
  shows the gap instead of a green "routed" over an unwired tool (coverage-as-a-checked-variable);
  (ii) the skip set is DERIVED, not enumerated: a pin asserts every `test_mcp_server` test carrying
  `_TOOL_LAYER_63A_SKIP` calls `AppContext.recall/remember`, and that no OTHER test does so
  un-skipped — a 19th silently-red tool-layer test cannot hide behind the 18.
- **FORK-D1 rider (surfaced, not narrowed):** `search.py::_recall_memory` now swallows
  `GovernedDenied` → `[]`. A silently-absent memory boost is the #131 shape (a feature empty for
  months, invisible). The `search_code` render NAMES the withheld boost in one derived line
  (*"memory boost withheld: identity-less call"*) until 63b threads the Subject — Leg 1, the bound
  is a fact in the response, never a silent `[]`.

**10.7-Z — `memory.owner_principal` delete disposition: RULED ORPHAN-TO-NONE, AUDITED; REFUSE-loud
until the mechanism lands (64) — SF-63-5 **operator CONFIRMED 2026-08-30 (ruling adopted:
orphan-to-NONE audited + refuse-loud interim + pin-the-miss; via lead-63, `lore_comms #8023`)**.**
- **Ruling:** on a hard principal-delete, every governed row the principal owns gets an ADMIN
  `SET_OWNER → NONE` (owner_principal AND owner_agent cleared) in the SAME transaction as the
  delete — each an audited load-bearing bypass (`_member_filter(SET_OWNER)` is `NoRows`, so
  `requires_audit` fires per row; the trail records who orphaned what). The rows then carry the
  §2.1 UNOWNED-LEGACY semantics ALREADY ruled: a keep-scoped note stays with its household, a
  `server` note stays visible, a `principal-private` note becomes admin-only by construction
  (`owner_principal = $p` matches nobody — invisible, never leaked). Nothing is destroyed, nothing
  dangles, nothing leaks.
- **Why not the alternatives:** CASCADE-DELETE vanishes keep-scoped notes other household
  members rely on (the FR-4 argument, on rows instead of keeps) — REJECTED. REFUSE-WHILE-OWNING
  makes every principal with one saved note undeletable until an admin re-owns each row — correct
  only as the INTERIM. A silent DANGLE is the `PrincipalStore.delete` docstring's own named
  anti-pattern (*"a governed row's owner, a LIVE dependency → cascade-or-refuse, NOT … dangle"*).
- **Sequencing (deferral with a RULING, an owner and a trigger — not an open question):** the
  orphaning mechanism is 64's admin `set_owner` (§2.5 already names 64 as its first consumer)
  applied over the derived set of governed tables; **meanwhile `PrincipalStore.delete` REFUSES**
  when `SELECT count() FROM memory WHERE owner_principal = $p GROUP ALL` > 0 (an IndexScan on the
  §4.1 index — free), naming the count and the 64 mechanism. PIN THE MISS: a test asserts the
  refusal with one owned memory row present and goes RED the day orphaning lands (delete the pin
  with the mechanism). The exact-set pin's class for this link becomes `ORPHAN-AUDITED (refuse
  meanwhile)`. Lands in 63a-ii if (A) above is taken; otherwise the first 63b fix-wave.
  Re-open trigger unchanged: the first principal-delete against a store holding an owned
  governed row.

**10.7-W — `--dry-run`: RULED the shipped operator ruling WINS; the design is corrected, the pin is
NOT exempted, and the `dry_run=` function parameter is DELETED.**
- §1.2 item 5 shipped `[--dry-run]` in ignorance of the 2026-08-20 operator ruling (*"Gate none. I
  hate that paradigm."* — no dry-run, no `--execute`, anywhere in `lore-adm`); my error, corrected
  in §1.2 above. Exempting `migrate-governed` from
  `test_principals_cli::test_source_contains_no_execute_flag_or_dry_run` is REJECTED — a pin
  exemption is how a struck paradigm creeps back one verb at a time.
- **The programmatic `migrate_governed(dry_run=)` param goes too:** the CLI cannot reach it, so it
  is an unreachable branch contradicting the ruling's spirit (a `lore_dead_code` candidate wearing a
  feature's name); `MigrateGovernedResult.dry_run` with it. **The PREVIEW role the design wanted is a
  READ verb** — `report_unmigrated_governed_rows` already exists; expose it as `lore-adm
  report-unmigrated --table <t>` (a read, exactly the class the operator's ruling allows —
  `list`/`list-keys`). Receipts stay: `migrate-governed` prints scanned / backfilled /
  already-migrated / refused AFTER executing, silent-on-success is NOT the idiom for a migration
  (it is a one-shot cutover verb whose counts ARE the receipt — loud by design, §2.3).
- **RIDERS:** a bare grep for `dry_run` / `dry-run` over `governed.py`, `principals.py`, and the 63a
  test modules → 0 hits (each residual gets a file + verdict); `lore_dead_code` shows no
  `MigrateGovernedResult.dry_run` residue.

---

*Every ruling above is within delegated authority; the four §7 sub-forks were CONFIRM items and are
now operator-CONFIRMED 2026-08-28 with every recommendation adopted (`lore_comms #8001`) — nothing in
this doc remains open for the operator. The security-auditor is the arbiter of §6; the
contract-adversary grades each wave's contract, with its REACH ATTACK pointed at §3.1's derived
verb set and its QUANTIFIER ATTACK at F3/F4's ∀-verbs. This doc consumes 60/61/62 as
CODE-COMPLETE and touches no code — I am the designer.*
