# REPORT-scout-pkt04-seams — packet 04 seam map

brief-base v7 read

**All findings below were derived 2026-07-26 against `feat/surreal-unification` @ `e4cfc6e`**
(clean tree; lore index `last_sync` 20s, watched root `/workspace` on the same branch/ref —
checked via `lore_index()` before any graph-derived claim). Every present-tense statement in this
report describes THAT tree. Read-only run: no tests, no probes, no store connections; one file
written (this one).

---

## SUMMARY BLOCK

- state: **done**
- deviations: none
- `Packages considered:` **one** — a result-transform hook for the S3 footer. Library evaluated:
  `mcp` (the pinned SDK) vs standalone `fastmcp`. What I READ: the `TracingFastMCP` class docstring
  in `loremaster.server`, which records the prior evaluation verbatim — *"`mcp` exposes no
  middleware or hook API, and the standalone `fastmcp` package that does is a server-wide dependency
  swap far beyond this change"* — and the `TracingFastMCP.call_tool` body that implements the
  minimum hand-roll. Verdict: **`keep_with_trigger`** — keep the existing `call_tool` override;
  trigger to revisit = the day the repo migrates to standalone `fastmcp`. ⚠ I did **not**
  independently re-read the `mcp` package source to re-verify "no hook API"; I am relaying a
  recorded evaluation, not a measurement I made.
- decisions-needed: **3** — (D1) S3 has **no** shared render seam inside `AppContext`; the only
  ONE-IMPLEMENTATION candidate is `TracingFastMCP.call_tool`, which is a *content-block* seam, not a
  string seam (§S3). (D2) `_render_task_*` / `_render_finding_*` return **bare `str`**, not
  `Rendered` — a footer appended there escapes the render-safety type discipline (§S3). (D3) an
  in-transaction `RELATE` onto an `ENFORCED` edge whose endpoint was `CREATE`d/`UPSERT`ed in an
  EARLIER statement of the SAME transaction is **unverified on 3.2.1** — this decides whether the
  `refers`/`answers_to` flip is safe at all (§S6, §WHAT I COULD NOT DETERMINE).
- S1 — task writes go through `TaskLedger._apply` (one `execute_transaction`); a `blocks` edge must
  be mirrored inside `_claim_fragment`'s sibling seams: `create_task` (a bare `_query`, **not**
  `_apply` — the odd one out), `_supersede_fragment`, and `create_many`.
- S2 — `AppContext._comms_fleet` → `AppContext._render_comms_fleet`; columns are built in
  `_render_comms_fleet_row`; the whole-set/slice split is already correct today (`roster()` unlimited
  for counts, `fleet()` capped for rows) and the drain path already shows the counting law obeyed.
- S3 — **NO shared render seam exists.** `tasks`/`claim_task`/`findings` are three independent
  `-> str` dispatchers with ~17 return points between them. Candidates named in §S3; this is a
  design finding.
- S4 — the idiom is `test_surreal_store.py::TestSchemaMigrationAgainstAnExistingStore` (+ the
  `migration_db` fixture and `_apply_ddl`) and `test_comms_schema.py::TestThePointerBoundsMigrateA
  DIRTYStore`. It does **not** call `ensure_ready` — it applies OLD DDL then NEW DDL through the
  production emitters.
- S5 — 1 production consumer (`AppContext._comms_brief_publish`); real-symbol coverage **derived**:
  55 test functions / 58 call sites, of which the `agent_id` (edge-writing) path is exercised by
  exactly **8** test functions through ONE helper (§S5).
- S6 — `_define_relation_table` confirmed as briefed; the real `#105` exposure is **`briefed` only**
  — `refers`/`answers_to` create both endpoints in the same fragment, `briefed` takes a bare string
  from a caller.
- S7 — **defect CONFIRMED and it has FOUR prose sites, not two.** Every WHERE clause in
  `agents.py` / `briefs.py` / `messages.py` uses bound `$params`; agent ids are `uuid5` hex.
- receipt POINTERS: §S1–§S7 below; derivation scripts are inline in the body (AST attribution, run
  read-only against the tree at `e4cfc6e`).

**Tool honesty (brief-base §4, repo CLAUDE.md dogfood protocol).** lore was first choice and was
used for: freshness (`lore_index`), semantic where-is (`lore_search` ×3), the S5 consumer/coverage
profile (`lore_impact`), and the #105 ledger row (`lore_findings`). **I fell back to grep/AST for
five things, and say so:** (a) the exhaustive `blocked_by` site list — rename-exhaustiveness, where
one missed site compiles-but-breaks; (b) module symbol outlines of `tasks.py` / `server.py` /
`surreal_schema.py` — cross-cutting maps; (c) the "inlined into WHERE clauses" prose sweep — a
non-symbol textual seam living in comments and f-strings; (d) `RELATE`/`WHERE` statement
construction — string literals, not symbols; (e) the S5 coverage disambiguation, because
`lore_impact`'s own honesty notice said its profile was a bare-name union (see §S5 — the tool told
me it could not answer, which is the tool working, not failing). None of these five is a lore
weakness worth a friction row: (a)/(c)/(d) are the three cases repo law already assigns to grep, and
(e) is `lore_impact` correctly declining to over-claim.

---

## S1 — the task write path

**Where task rows are written.** `loremaster/loremaster/tasks.py`, class `TaskLedger`. Four write
verbs and one batch verb:

| verb | seam it writes through | fragment builder | atomic? |
|---|---|---|---|
| `TaskLedger.create_task` | **`TaskLedger._query`** (a bare `CREATE … CONTENT`) | — (`_new_task_content`) | single statement, **not** a txn |
| `TaskLedger.claim_task` | `TaskLedger._apply` | `TaskLedger._claim_fragment` | ✅ `BEGIN…COMMIT` |
| `TaskLedger.transition` | `TaskLedger._apply` | `TaskLedger._transition_fragment` | ✅ |
| `TaskLedger.supersede_task` | `TaskLedger._apply` | `TaskLedger._supersede_fragment` | ✅ |
| `TaskLedger.create_many` | `TaskLedger._apply` | N inline `TxnFragment`s (`cm<i>_id`/`cm<i>_content`) | ✅ all-or-nothing |

**THE transaction seam a `blocks` edge must be mirrored inside.** `TaskLedger._apply(fragments)` —
it calls `compose(*fragments)` then `execute_transaction(...)` from `loremaster.store._txn`. Every
fragment builder above returns a `TxnFragment(statements=[...], params={...})`, so a `blocks`
`RELATE` is appended as an EXTRA STATEMENT in the SAME fragment — the exact idiom
`BriefLedger._publish_fragment` already uses for its self-ack `briefed` edge (docstring: *"appended
as a SECOND statement in this SAME fragment — never a separate fragment or a second `_apply`
call"*). That is the pattern to follow, and it is a pattern in the DRY sense only because there is
no policy to share; the composition is `compose`'s job already.

⚠ **`create_task` is the odd one out and it is where a `blocks` mirror would silently break
atomicity.** It does NOT go through `_apply`; it issues one `CREATE` via `_query`. `blocked_by` is
written at **birth** (`_new_task_content`), so the `blocks` edges for a `create_task` call must ride
the same statement group — which means `create_task` has to be converted to `_apply` with a fragment,
or the edge lands in a second, separately-failable write. `create_many` already uses `_apply` and is
fine. Flag this to the contract author explicitly: a contract that only pins `create_many` will miss
it.

⚠ **`blocked_by` is documented as IMMUTABLE after creation** — `claim_task`'s own comment: *"
`blocked_by` never changes after creation, so reading it here is consistent"*. There is **no verb
that mutates `blocked_by`**. So `edge ≡ blocked_by` is an invariant with exactly TWO mint points
(`create_task`, `create_many`) and zero update points — and `supersede_task`'s successor is created
with `blocked_by=None` (`_new_task_content(subject, description, None, created_by, now)`), i.e. a
successor inherits NO dependencies. That is a behavioural fact the invariant test must not
contradict.

### Every site that reads or writes `task.blocked_by`

Derived by grep over `--include=*.py` (rename-exhaustiveness ⇒ honest grep) and attributed to
enclosing symbols by an AST pass. 61 mentions across 7 files.

**Schema (1 site, the definition):**
- `loremaster/loremaster/store/surreal_schema.py::_task_statements` — `("blocked_by",
  "array<string>", "DEFAULT []")`. Emitted through `_define_field` ⇒ `DEFINE FIELD OVERWRITE`.

**Production ledger — `loremaster/loremaster/tasks.py`:**
- module scope: `_COL_BLOCKED_BY = "blocked_by"` (the one literal).
- **WRITE** `TaskLedger._new_task_content` — the only writer. Dedupes order-preservingly
  (`list(dict.fromkeys(...))`). Called by `create_task`, `create_many`, `supersede_task`.
- **READ** `Task.blocked_by` (the pydantic model field), `TaskSpec.blocked_by`,
  `TaskSpecLike.blocked_by` (the structural Protocol).
- **READ** `TaskLedger._row_to_task` — row → value object.
- **READ** `TaskLedger.claim_task` — pre-reads the column off `_select_row` to bind
  `$clm_blocked_by`.
- **READ (server-side)** `TaskLedger._claim_fragment` — the CAS guard
  `array::len(blocked_by) = array::len($clm_resolved)`. **This is the fail-closed gate**: a
  never-minted blocker id is simply absent from `$clm_resolved`, counts differ, claim fails closed.
- **READ** `TaskLedger._is_blocked(task, status_by_id)` — the client-side partition used by
  `query_tasks`, fail-closed on a missing blocker.
- **READ** `TaskLedger.query_tasks` — resolves blocker statuses over the WHOLE table, not the
  filtered subset.
- **READ** `TaskLedger.create_many` — `spec.blocked_by` per spec.

**Production dispatcher — `loremaster/loremaster/server.py`:**
- `TaskSpecItem.blocked_by: list[str] = Field(default_factory=list)` — the wire model.
- `AppContext.tasks` — the `blocked_by` kwarg, forwarded to `create_task`.
- `AppContext._create_many` — **the interesting one**: builds `edges: dict[str, set[str]]` from
  `item.blocked_by ∩ key_index`, runs `AppContext._find_key_cycle(edges)`, rejects an intra-batch
  cycle client-side BEFORE any write, then resolves temp keys → pre-minted `uuid4().hex` ids. **The
  acyclicity check the packet wants already exists here, but only over BATCH-LOCAL KEYS** — it
  cannot see a cycle formed against an already-persisted task.
- `AppContext._render_claim_result` — renders `blocked_by {task.blocked_by} unresolved` on the
  unowned-not-claimable branch. ⚠ Its own docstring says this branch is a *"residual gap"* for
  render sanitisation (interpolates `blocked_by`/`status` by bare f-string, not through `safe_str`).
- `AppContext._render_task_rows` — the query render.
- `_register_tools` — the `lore_tasks` tool parameter description prose.

**Tests that pin it:** `test_task_ledger.py`, `_task_fakes.py` (the fake carries its OWN
`_is_blocked` — a parallel implementation of the fail-closed rule, deliberately, per its docstring),
`test_mcp_server.py`, `test_anchored_pattern_seam.py`.

---

## S2 — the fleet view

**Producer:** `AppContext._comms_fleet` (dispatched from `AppContext.comms` via
`_COMMS_ACTIONS[_COMMS_ACTION_FLEET]` → `CommsActionSpec(limit_cap=_MAX_FLEET_LIMIT)`).
**Render:** `AppContext._render_comms_fleet` → per row `AppContext._render_comms_fleet_row` → cell
helper `AppContext._render_comms_fleet_brief_cell`.

**Columns that exist today** (`_render_comms_fleet_row`, cells joined `" · "`):
`- {name} [{status}]` (or `[{status} ⚠ STALE]`) · `hb {age}` · `role <role>` · `model <model>`
(omitted if `None`) · `task <id[:8]>…` (omitted if `None`) · the project-brief cell
(`project unbriefed` / `project v<n>` / `project v<a> (head v<h>)`; omitted entirely when no
standing brief exists) · `note: <last_note>` (omitted if `None`).

Header: `fleet[ (session X)]: {total} non-retired agents — {parked} input_required, {active} active,
{idle} idle`. Trailers: an elision line (two variants) and `+{count} retired`.

**Where per-agent unread / unacked-directive counts would be computed.** In `_comms_fleet`, beside
the two existing per-row lookups, and they must follow the SAME shape:

```
roster  = await self.agent_registry.roster(session=session)      # row-UNLIMITED — the true counts
window  = await self.agent_registry.fleet(session=session, limit=display_limit)  # display-capped rows
heartbeat_age_seconds = {row.id: … for row in window.rows}       # per-row, over the SHOWN rows
acked_versions        = await self.brief_ledger.acked_versions_for_ids(
                            [row.id for row in window.rows], name=STANDING_BRIEF)   # ONE grouped query
```

The house idiom to clone — or rather, **to call** — is `BriefLedger.acked_versions_for_ids`: ONE
grouped edge query over a list of ids, bounded query count independent of `len(agent_ids)`, with the
documented *absent-key-means-zero/unbriefed* convention (finding #94: never a per-row round-trip).
There is **no equivalent on `MessageLedger` today** — its only per-agent read is
`MessageLedger.drain(agent_id=…)`, which is per-agent AND mutating unless `peek=True`. So packet 04
must add a new grouped read to `MessageLedger` (e.g. `pending_counts_for_ids`). Two mechanics the
contract author needs:
- the pending predicate lives on the `to` edge: `WHERE out = $agent AND seen_at IS NONE`;
- **`grade` is NOT on the `to` edge** — `drain` reads it as `in.grade`, so a grouped
  unacked-directive count must traverse into the `message` node (`in.grade = 'directive'`) and use
  the `to` edge's `acked_at IS NONE`.

### ⚠ The slice-vs-label hazard, stated precisely

**There is no such defect in the fleet path today**, and the reason is worth quoting because it is
the trap: `_render_comms_fleet`'s docstring records that `status_counts` is a *"REQUIRED, TRUSTED
true aggregate"* from `roster()`, that the header total / per-status segments / elision arithmetic /
retired trailer are ALL derived from it, and — load-bearing — that *"there is no `len()`-derived
fallback path here on purpose, so an omitted argument can never silently resurrect that defect"*
(the v4 audit D1 finding). `AgentRegistry.roster` refuses a `limit` parameter for the same reason.

So the hazard for packet 04 is specific and nameable:
1. **A per-row cell is fine over `window.rows`** — `heartbeat_age_seconds` and `acked_versions`
   already are, because a per-row value describes only its own row.
2. **Any fleet-LEVEL total** ("N unread across the fleet") derived from `window.rows` would be
   the D1 defect resurrected. It must come from the row-unlimited `roster.members`, or carry a label
   that names the slice.
3. The existing correct precedent for the counting law is `MessageLedger.drain`, whose docstring
   states it outright: *"`total_pending`/`directive_pending` are computed over the WHOLE pending set,
   never the capped window (a display cap bounds rows rendered, never the numbers beside them)."*
   `drain` implements it as `total_pending = len(pending)` / `directive_pending = sum(...)` computed
   BEFORE `window = pending[:limit]`. Clone that ORDER, and note the fixture hazard it implies: a
   fixture where `len(pending) <= limit` cannot discriminate a whole-set count from a window count.

---

## S3 — the mutation footer · **DESIGN FINDING: no shared seam exists**

**Where the three tools build their output.** All three MCP tool functions in `_register_tools` are
one-line pass-throughs (`return await _app_context(context).X(...)`). The rendering happens in
`AppContext`, and all three return **bare `str`**:

| tool | `AppContext` method | return points | renders via |
|---|---|---|---|
| `lore_claim_task` | `AppContext.claim_task` | 1 | `AppContext._render_claim_result` (3 branches, bare f-strings) |
| `lore_tasks` | `AppContext.tasks` | 6 + 1 raise | `_rollup`, `_create_many`, inline f-string (`create`), `_render_task_rows`, `_render_task_transition`, inline f-string (`supersede`) |
| `lore_findings` | `AppContext.findings` | 9 + 1 raise | `_resolve_or_acknowledge_many`, inline f-string (`report`), `_render_finding_rows`, `_render_finding_detail`, `_render_chain_head`, `_render_finding_transition` ×3 |

**There is NO single seam through which all three (or even all of one tool's actions) pass on the
way out.** ~17 distinct `return` statements. Saying this plainly, per the brief: **appending a
`_comms_footer` at the render sites would be sixteen-plus clones of one policy — precisely the
`#102` shape repo law forbids.**

### Candidates, ranked

1. **`TracingFastMCP.call_tool` — the ONE funnel that already exists, and the only true one.**
   `loremaster.server.TracingFastMCP` overrides `FastMCP.call_tool`; its docstring records *why*
   this seam and not per-tool wrappers: *"`_setup_handlers` registers the BOUND `self.call_tool`
   with the lowlevel server, so overriding the method puts the emission on the WIRE path by
   construction: every tool — built-in, extension-registered, and any registered later — passes
   through this one funnel. Per-tool emission would be ~20 forgettable obligations, invisible for
   any tool nobody remembered to wrap."* That argument transfers verbatim to a footer.
   **Costs, all real:**
   - Its return type is `Sequence[ContentBlock] | dict[str, Any]`, **not `str`** — a footer here
     appends to a rendered content block, after the `str` has already been packed. That is a
     different and messier surgery than appending to a string.
   - It is a **global** funnel: `lore_search`, `lore_read`, everything. Restricting to the three
     mutation tools means a `name in {...}` check inside it — which is a **tool-NAME allowlist**,
     and the class docstring's own `_TRACE_DECLARED_KEYS` comment brags about being *"a KEY rule,
     deliberately — never a tool-name rule: no tool enumeration exists to go stale."* A footer keyed
     on a tool-name set would introduce exactly the staleness that seam was designed to avoid. (It
     is a *safe*-set allowlist, so it fails closed — a new tool gets no footer — which is the
     acceptable direction, but say it out loud rather than inherit it silently.)
   - Its failure posture is ruled: *"the tool call's outcome ALWAYS wins"* — telemetry never
     surfaces to the caller. A footer is the opposite: it is served output. Reusing the seam means
     reusing a shield/timeout whose whole point is to swallow failures. **Do not append the footer
     inside the shielded `finally`.**
2. **A shared helper called from the three `AppContext` methods' single exit.** Requires collapsing
   each dispatcher to one return (or wrapping the call): `AppContext.claim_task` is already
   1-return; `tasks` and `findings` are not. This is one function (`_comms_footer(...)`) with three
   call sites — DRY-legal, mypy-visible, `str`-typed, and mutation-provable (change the footer text
   ⇒ all three pins go red). **My recommendation**, with the caveat that it needs a small refactor
   of two dispatchers and an explicit rule for which ACTIONS count as mutations (`query`/`get`/
   `chain_head`/`rollup` presumably do not — and `claim_task`'s LOSING branch writes nothing, so
   "mutation" is a per-outcome question, not a per-tool one).
3. **A decorator on the three `@mcp.tool` functions.** Rejected: the tool functions are
   `Annotated`-parameter-heavy and FastMCP introspects their signatures to build the schema; a
   wrapper risks the schema. Also it is three decorations = three forgettable obligations, the exact
   objection `TracingFastMCP`'s docstring already litigated.

### Two more things the contract author must know

- **⚠ D2 — the type mismatch.** The comms surface renders through `Rendered` / `SafeLine` /
  `render_line` / `render_join` / `render_compose` / `sanitise_line` (see every `_render_comms_*`).
  `tasks` / `claim_task` / `findings` return **plain `str` built by f-string**. A `_comms_footer`
  built as `Rendered` and appended to a plain `str` crosses the render-safety boundary in the wrong
  direction, and a footer built as a plain f-string is a NEW un-sanitised served surface. Decide
  which, deliberately. (`_render_claim_result`'s docstring already flags its own `blocked_by`/
  `status` branch as an unsanitised *"residual gap"* — packet 04 will be touching that render.)
- **⚠ The served `_INSTRUCTIONS` document is pinned BY EQUALITY.** `test_comms_tool.py` carries
  `test_the_served_INSTRUCTIONS_are_EXACTLY_the_declared_paragraphs` (CL3, RULED — an allowlist over
  the whole served document) plus a demoted regression gate
  `test_the_comms_block_is_the_ONLY_paragraph_claiming_a_comms_DUTY`. That second test's docstring
  **names packet 04 by name**: *"packets 04 (`_comms_footer`) and 05 (await/story) both add to this
  block, and a general 'fleet etiquette' paragraph is exactly what a later author writes."* Any
  teaching prose the footer adds to `_INSTRUCTIONS` will turn those pins RED and must be landed
  through the declared-paragraph allowlist, not around it.

---

## S4 — the dirty-store pin idiom · **highest-value item, and the brief's framing needs one correction**

**The brief asks how a test "re-runs `ensure_ready`". It does not.** The existing pins re-apply the
DDL through the production GENERATORS/EMITTERS, never through `SurrealStore.ensure_ready` — and the
`migration_db` fixture's docstring says why in as many words: *"they need a bare connection, NOT a
`SurrealStore` that has already applied today's schema at `ensure_ready`."* Calling `ensure_ready`
would apply the CURRENT schema before the test could install the OLD one, destroying the very
condition under test. Build the packet-04 pins the same way.

### The canonical instrument — `loremaster/tests/test_surreal_store.py`

**Fixture:** `migration_db` — mints `unique_database()`, `connect_admin(env)`, yields
`(connection, env)`, drops the DB on exit. Uses `_MIGRATION_DIM = 8` (a tiny embedding width; these
pins exercise DDL, not recall).

**Applier:** `_apply_ddl(connection, ddl, *, url)` — wraps the DDL in `BEGIN;…COMMIT;` and runs it
through `loremaster.store._txn.execute_transaction`, **not** a bare `connection.query(ddl)`. Its
docstring is the reason and it is load-bearing: *"the SDK inspects only the FIRST statement's
status, so a later DDL statement's rejection would roll the whole schema back server-side while
`query()` raised nothing at all… A migration pin that applied its DDL the lax way could report a
green migration over a schema the engine had just silently discarded."* Its `drop` callback
`_never_drop` raises `AssertionError` — a DDL rejection must never be mistaken for a dead socket.

**The five-step shape** (`TestSchemaMigrationAgainstAnExistingStore`):
1. apply the **OLD** definition (built through the production emitters `_define_table` /
   `_define_field`, never hand-written SurrealQL — *"the defect lives in the EMITTER, so a pin that
   wrote its own `DEFINE FIELD` string would test a copy of the code and pass while production
   stayed broken"*);
2. **DIRTY THE STORE** — write a row legal under the OLD definition;
3. apply the **NEW** definition through the same emitters;
4. assert the change **LANDED** — a value legal only under the new definition is accepted;
5. assert the **POSITIVE CONTROL** — `test_the_migrated_field_still_rejects_an_out_of_domain_value`:
   a value in NEITHER set is still rejected, **and rejected BY THE ASSERT** (the assertion checks
   the offending value AND the field name appear in the error, so *"a probe that passes for the
   wrong reason"* is caught).

Plus three siblings you should copy wholesale: `test_the_pre_existing_row_survives_the_migration`
(data survives AND stays writable), `test_reapplying_an_unchanged_definition_is_still_an_idempotent_
no_op` (because `ensure_ready` re-applies every boot), and
`test_the_whole_schema_migrates_an_existing_populated_store` — the blast-radius pin that seeds one
row per table, re-applies EVERY slice, and demands every row survives.

**The old-world DDL derivation trick, and it is the best thing in the file.**
`_brief_ddl_before_the_via_widening()` does not hand-copy the old DDL — it **derives** it from the
current generator by removing the widened value, and **raises** if the removal is a no-op:
*"if removing the value stops changing the DDL (because the vocabulary moved on), this raises rather
than handing back an 'old' DDL identical to the new one, which would leave the pin passing while
testing nothing at all."* **For packet 04's `ENFORCED` flip the analogue is trivial and should be
mandatory:** derive the old relation-table DDL as
`_define_relation_table(REL, IN, OUT, enforced=False)` — i.e. call the production emitter with the
old argument — and assert it differs from `enforced=True`. A hand-written old DDL string is how this
pin rots.

### The packet-03/03b instrument — `loremaster/tests/test_comms_schema.py`

Same shape, different fixture: `admin_db` (imported from `_surreal_harness`) + `run(connection,
ddl)`. Two classes:
- `TestThePointerBoundsMigrateADIRTYStore` — `_old_message_ddl()` (a hand-written OLD DDL, the
  weaker form; note it uses `DEFINE FIELD OVERWRITE` so the old world really lands), `_dirty_old_
  world()` writes a row the new bounds would refuse, then four tests: **BASELINE** (`test_BASELINE_
  the_old_world_really_accepts_an_oversize_pointer` — *"without this, 'the bound is live after
  migrating' could be true because it was ALWAYS live"*), the migration leg, the row-survival leg,
  and the idempotence leg.
- `TestTheAckNoteNarrowingAgainstADIRTYDeliveryEdge` — the `to`-edge half, added after the round-2
  cold audit reproduced the write-poisoning consequence the design doc had wrongly called
  impossible. This is the class whose absence is the packet-03b "rider dropped" receipt.

**⚠ Gap I noticed, surfaced not resolved (scope law).** The blast-radius pin
`test_the_whole_schema_migrates_an_existing_populated_store` applies exactly four slices —
`generate_ddl(dim=…)`, `generate_graph_ddl()`, `generate_agent_ddl()`, `generate_brief_ddl()`. It
does **not** apply `generate_message_ddl()`, which packet 03 added (it is the slice carrying the one
already-`ENFORCED` `to` edge). So the whole-schema migration pin does not currently cover the
message/`to` slice. Operator/lead call whether packet 04 widens it; it is one line plus a seed row.

---

## S5 — `BriefLedger.publish(agent_id: str | None)`

**Signature (confirmed, still a bare string):**
`BriefLedger.publish(name, body, *, created_by: str, note: str | None = None, agent_id: str | None = None) -> BriefPublishResult`.

**What it does with `agent_id`.** Nothing at all when `None`. When given, `BriefLedger._publish_
fragment` appends a SECOND statement to the SAME `TxnFragment` as the brief `CREATE`:

```
RELATE $ack_from->briefed->$ack_to SET via = $ack_via, at = $ack_at
params: $ack_from = RecordID(AGENT_TABLE, agent_id)   # ← the bare string, unvalidated
        $ack_to   = RecordID(BRIEF_TABLE, brief_id)
        $ack_via  = "publish"
```

**Edge written:** `agent -> briefed -> brief`, `via='publish'`. It rides ONE
`execute_transaction` with the `CREATE`, so a rejected create rolls the edge back; on
`SurrealStoreError` the handler calls `_release_version` and re-raises untouched.

**The sibling writer of the same edge** (not asked for, but it is the other `briefed` door):
`BriefLedger._relate_briefed(agent_id=…, brief_id=…, via=…)`, called from `BriefLedger.ack`. Same
`RecordID(AGENT_TABLE, agent_id)` construction, same lack of existence checking. It treats a
UNIQUE(in,out) rejection as the idempotent re-ack signal, and it is one of the FOUR guarded-CAS
doors pinned by `test_retry_seam.py::TestNoGuardedCasHandlerReinterpretsExhaustedContention`.

**Production consumers: exactly ONE.** `AppContext._comms_brief_publish` —
`await self.brief_ledger.publish(name, body, created_by=agent_row.name, note=note,
agent_id=agent_row.id)`. `agent_row` is the dispatcher-resolved live agent row, so the id exists at
call time. (`lore_impact` agrees: `direct_consumers: ["loremaster.server.AppContext._comms_brief_
publish"]`, `production_references: 1`.)

### Covering tests — the disambiguation, and the derived count

`lore_impact` served `54 test references` / `tests: 1060` and **told me itself** that the profile
*"rode the bare-name fallback channel — it may be a UNION with `loremaster.tests._comms_fakes.
FakeBriefLedger.publish`, `loremaster.tests.test_comms_tool._CoverageSkewSpyBriefLedger.publish`'s
own references"*. **I am not reporting that number.** I derived my own by AST-attributing every
`.publish(` call to its enclosing test function and classifying the receiver:

| file | `.publish(` sites | receiver | real symbol? | test funcs |
|---|---|---|---|---|
| `test_brief_ledger.py` | 53 | `BriefLedger(...)` constructed in-file (7 sites) | ✅ | **51** (of 67 in the file; 34 call it directly, the rest via `_publish_as` / `_publish_versions` / two `_query_count` helpers) |
| `test_retry_seam.py` | 4 | `_ledger_on(connection) -> BriefLedger` | ✅ (real ledger, fake connection) | **3** |
| `test_comms_wiring.py` | 1 | `ctx.brief_ledger` where `ctx: AppContext` | ✅ (real, live schema) | **1** |
| `test_comms_render_architecture.py` | 5 | `_harness() -> (…, FakeBriefLedger)` | ❌ fake | 0 |
| `test_comms_tool.py` | 10 | `FakeBriefLedger` / `_CoverageSkewSpyBriefLedger` | ❌ fake/spy | 0 |

**Defensible count: 58 call sites across 55 test functions exercise the REAL
`BriefLedger.publish`.** The 15 call sites in `test_comms_render_architecture.py` and
`test_comms_tool.py` belong to the two doubles and are what inflated the union.

**And the number that actually matters for packet 04 — the `agent_id` path:** across the whole tree
there are exactly **TWO** `publish()` call sites that pass `agent_id=`: production
`AppContext._comms_brief_publish`, and the single test helper
`test_brief_ledger.py::_publish_as` (whose own docstring says it is *"the ONE call site of the new
`agent_id` kwarg, so the contract's demanded signature change is stated in exactly one place"*).
**Eight** test functions reach it, all in `test_brief_ledger.py`:
`TestPublishSelfAcksItsAuthor::{test_publish_writes_the_authors_briefed_edge_at_the_published_
version, test_the_self_ack_edge_records_via_publish, test_the_author_is_current_and_only_the_others_
are_behind, test_an_author_explicitly_acking_its_own_version_is_an_idempotent_no_op, test_a_
republish_by_a_different_author_leaves_the_prior_author_at_its_old_version, test_every_one_of_eight_
concurrent_publishers_self_acks_exactly_its_own_version}` and
`TestPublishSelfAckIsWrittenInTheSameTransaction::{test_the_row_and_the_edge_ride_ONE_execute_
transaction, test_a_rejected_create_rolls_back_the_edge_too_and_burns_no_version}`.

⚠ **Consequence for the negative fixture (FIXTURES MUST DISCRIMINATE).** All eight pass a
`agent_id` for an agent the fixture registered. **No existing test passes a NON-EXISTENT
`agent_id`** — which is exactly finding #105's own note: *"the audit could not make the RELATE fail
with a bad `agent_id` at all — it had to poison the `via` param instead to test rollback. That
inability IS the finding."* The packet's mandated negative fixture is genuinely new territory.

---

## S6 — the `ENFORCED` flip surface

**Confirmed as briefed.** `loremaster/loremaster/store/surreal_schema.py::_define_relation_table`:

```python
def _define_relation_table(name: str, in_table: str, out_table: str, *, enforced: bool = False) -> str:
    enforced_clause = " ENFORCED" if enforced else ""
    return (f"DEFINE TABLE OVERWRITE {name} TYPE RELATION "
            f"IN {in_table} OUT {out_table}{enforced_clause} SCHEMAFULL")
```

Already `OVERWRITE` (its docstring cites store reference §1.1 and records the 3.2.1 re-probe:
*"the flip lands `ENFORCED`+`IN`/`OUT` on an existing untyped edge table"*). **Four consumers,
confirmed:**

| caller | edge | endpoints | `enforced=` today |
|---|---|---|---|
| `_briefed_statements` | `briefed` | `agent` → `brief` | *(default)* `False` |
| `_message_statements` | `to` | `message` → `agent` | **`True`** ✅ |
| `_refers_statements` | `refers` | `code_node` → `name` | `False` |
| `_answers_to_statements` | `answers_to` | `code_node` → `name` | `False` |

Slice generators: `generate_brief_ddl` (briefed), `generate_message_ddl` (to),
`generate_graph_ddl` (refers + answers_to).

### What ELSE changes — the RELATE paths, and where the real exposure is

I enumerated every `RELATE` / `INSERT RELATION` in `loremaster/loremaster/` (grep over string
literals — a non-symbol textual seam, honest fallback). There are **five** RELATE construction
sites, on four edges:

| # | site | edge | `in` endpoint source | `out` endpoint source | caller-supplied / possibly-nonexistent? |
|---|---|---|---|---|---|
| 1 | `BriefLedger._publish_fragment` | `briefed` | `RecordID(AGENT_TABLE, agent_id)` — **a bare `str \| None` parameter** | `RecordID(BRIEF_TABLE, brief_id)` — created in the same txn | ⚠ **YES — this is the #105 exposure** |
| 2 | `BriefLedger._relate_briefed` (from `ack`) | `briefed` | `RecordID(AGENT_TABLE, agent_id)` — bare `str` param | `brief_id` read from a live `SELECT` | ⚠ **YES, same shape** |
| 3 | `MessageLedger._send_fragment` | `to` | `$msg_rec` — minted in the same txn | `$to_<i>` per recipient | already `ENFORCED`; **and** app-checked by `MessageLedger._reject_unknown_recipients` |
| 4 | `SurrealCodeGraph._node_statements` | `answers_to` | `$<n>_id` — the `code_node` CREATEd 1 statement earlier in the SAME fragment | `$<n>_fqn_name` / `$<n>_bare_name` — `name` rows UPSERTed EARLIER in the same fragment | **no caller input** |
| 5 | `SurrealCodeGraph._edge_statement` | `refers` | `$<n>_src` — a `code_node` CREATEd in the same fragment | `$<n>_dst` — a `name` row UPSERTed in the same fragment | **no caller input** |

**THE REAL #105 EXPOSURE IS `briefed`, AND ONLY `briefed`.** Both its RELATE sites take an
`agent_id` bare string from a caller and construct a `RecordID` from it without any existence check.
`BriefLedger.publish`'s `agent_id` is *optional* and *untyped beyond `str`*, so any ledger-level
caller can pass anything — finding #105 says exactly this: *"note `BriefLedger.publish(agent_id=…)`
is deliberately OPTIONAL and takes a BARE STRING, so any ledger-level caller can pass anything."*

**`refers` and `answers_to` carry NO caller-supplied endpoint.** `SurrealCodeGraph.build_file_graph_
fragment` composes, in order: (1) `_purge_statements()` — three tier+file-scoped DELETEs;
(2) an `UPSERT` per distinct name (*"so an edge to a not-yet-defined name never dangles
(order-independence)"*); (3) `_node_statements` — `CREATE` the `code_node` then its two
`answers_to` RELATEs; (4) `_edge_statement` per reference. Every endpoint of every RELATE is minted
by an earlier statement of the same fragment, from astroid-derived values, never from a tool
parameter. The `name` table is never purged, so the `out` side of both edges can never vanish.

**⚠ Therefore the `refers`/`answers_to` flip is either free or fatal, and which one is UNVERIFIED
(decision D3).** It buys ~nothing on the exposure axis — but it turns on a validation that must
resolve endpoints **created earlier in the same uncommitted transaction**. If SurrealDB 3.2.1
validates `ENFORCED` against COMMITTED state, `generate_graph_ddl` + `ENFORCED` would break every
file index, 100%, on the first write — the #107 shape with a different mechanism. I could not probe
this (read-only brief). **This must be the first thing packet 04 measures**, and the same question
applies to `briefed` (its `out` endpoint, the `brief` row, is CREATEd one statement earlier in
`_publish_fragment`) and would have applied to `to` — which is already `ENFORCED` and whose `in`
endpoint is likewise minted in the same transaction. **That last fact is a strong hint the answer is
"same-transaction is fine", since packet 03 shipped and smoked it — but a hint from a shipped
neighbour is not a measurement, and P2/§4's own history is that the vendor docs lie.**

**Also in scope of "what else changes":** `MessageLedger` keeps an app-level `_reject_unknown_
recipients` (a raw `SELECT` over `agent`) ALONGSIDE `ENFORCED` on `to`. The packet's ruling says the
app check stays as the ergonomic layer for the three new edges too — so `briefed` needs an
equivalent app-level pre-check that names EVERY bad id before the write, which does not exist today
in `briefs.py`.

---

## S7 — #219 · **CONFIRMED, and the defect has FOUR prose sites**

**The claim, quoted verbatim.**

1. **Docstring** — `AppContext._validate_comms_charset`:
   > *"The SAME ``AGENT_NAME_PATTERN`` guards agent names, sessions, AND brief names (design doc §0:
   > "Brief names ... same class as agent.name ... same injection posture") — all three are inlined
   > into C3's live WHERE clauses, so all three share one charset."*

2. **SERVED error message** — the `ValueError` raised by the same method (this string reaches an
   agent):
   > `f"{label} {value!r} does not match {AGENT_NAME_PATTERN.pattern} — names are inlined into store queries and must stay in the safe charset"`

3. ⚠ **Docstring — `AppContext._validate_comms_identities`** (NOT named in the packet text, same
   false claim, and it *cites* site 1 as its authority):
   > *"a recipient IS an agent name — the fourth member of the identity class
   > :meth:`_validate_comms_charset`'s own docstring says shares ONE charset because all of them are
   > inlined into live ``WHERE`` clauses."*

4. ⚠ **Module comment — `loremaster.agents`, immediately above `AGENT_NAME_PATTERN`** (NOT named in
   the packet text; this is the DEFINITION site, so it is arguably the source the other three
   inherited from):
   > *"# The load-bearing injection guard (design doc §0/§4): every ``agent.name`` /
   > ``agent.session`` is inlined as a literal into C3's live WHERE clauses, so the charset is
   > enforced here … Configurability would make the inlining guarantee operator-breakable, so this
   > stays a MODULE CONSTANT, never a config knob."*

   Note this one carries a *consequence* — the "never a config knob" ruling is justified BY the
   false premise. Fixing the prose without noticing that leaves a rule whose stated reason has
   evaporated. (I am not proposing the knob; I am flagging that the fix must supply the real reason —
   defence-in-depth against the store's own `ASSERT`, and the `RecordID`/id-recipe surface — rather
   than silently deleting the justification.)

**The bound-parameter claim, verified by reading the actual query construction.** Every `WHERE`
clause that touches an identity in the three comms modules binds a `$param`:

- `agents.py`: `AgentRegistry` resolution — `SELECT * FROM agent WHERE name = $<name-lookup>`;
  roster/fleet scoping — `WHERE session = $<session-filter>`. Two `WHERE` sites, both bound.
- `briefs.py`: nine `WHERE` sites — `WHERE name = $<name-lookup>` (×6),
  `WHERE in = $<edge-in>` / `WHERE in IN $<roster>` (the `briefed` edge reads),
  `WHERE name IN $<skew-names>`, `WHERE next = $<mint-version>`. All bound.
- `messages.py`: seven `WHERE` sites — `WHERE out = $agent AND seen_at IS NONE`,
  `WHERE out = $agent AND in IN $message_ids …`, `WHERE seq IN $seqs`,
  `WHERE question = true AND sender = $agent`, etc. All bound.

**No identity is interpolated into any WHERE clause anywhere in the comms subsystem.** Nor into a
record id: `AgentRegistry._agent_id(session, name)` returns
`uuid5(NAMESPACE_URL, f"lore://agent/{session}/{name}").hex` — the identity text is hashed, and only
the 32-hex digest reaches a `RecordID`. `BriefLedger._brief_id` does the same for
`lore://brief/{name}/{version}`.

**For completeness (the honest residual, per repo law that "all remaining hits are X" is banned).**
My grep for `inlin` across `loremaster/loremaster/` returned 20 hits. Individually adjudicated, the
ones NOT part of this defect: `logging_setup.py` (a naming note) — unrelated; `auth.py:189`,
`config.py` ×5 (secrets *"never inlined"*) — unrelated, and TRUE; `diff.py:396`,
`graph_surreal.py:53/647/673`, `messages.py:648`, `index/watcher.py:752`, `index/cli.py:108`,
`search.py:788`, `memory/local.py:16` — all about code organisation, unrelated. **`scout.py:254` and
`scout.py:306` DO describe a genuine inlined literal** — `LiveSelect.live_select_statement` builds a
filtered subscription with the *status* value inlined — but that is a closed-vocabulary status, not
an identity, so it neither supports nor is touched by the comms charset claim. That leaves the four
sites listed above as the complete set of FALSE inlining claims.

---

## WHAT I COULD NOT DETERMINE

1. **Whether `ENFORCED` resolves an endpoint created earlier in the SAME uncommitted transaction
   (3.2.1).** This decides whether the `refers`/`answers_to`/`briefed` flip is safe at all, and it
   is the single highest-risk unknown in the packet. I could not probe (read-only). Circumstantial
   evidence that it works: `to` is already `ENFORCED` and `MessageLedger._send_fragment` RELATEs
   onto a `message` node minted in the same fragment, and packet 03 deployed and smoked. That is a
   hint, not a measurement.
2. **Whether the packet's P1 (dangling edge = first-class member vs `[]`) still holds on 3.2.1.** I
   read that store reference §6.4 calls the vendor claim FALSE on 3.1.5 and that the refutation
   predates the upgrade. I did not re-derive it and did not consult `tier="surrealql-tests"` — the
   packet assigns those probes to the build, not to this scout.
3. **How many dangling `briefed` ghosts actually exist in the production store.** Nobody has
   measured it; the packet says so and rules cleanup OUT as #236. I did not connect to a store.
4. **The exact set of ACTIONS that count as "a mutation" for the footer.** `lore_claim_task`'s
   losing branch writes nothing; `lore_tasks action=query|rollup` and
   `lore_findings action=query|get|chain_head` are reads. The packet says *"mutations append one
   line when traffic pends"* — which of the ~17 return points that covers is a spec question I am
   not entitled to settle. **Both readings produce different code**, so per brief-base §2 I state
   them: (a) per-TOOL — every call to the three tools gets a footer, simple and stale-proof;
   (b) per-ACTION-OUTCOME — only calls that actually wrote. **I would pick (b)**, because a footer on
   a read is noise on the highest-frequency path and the packet's own word is "mutations" — but it
   makes the footer decision per-return-point, which is precisely what argues AGAINST the
   `TracingFastMCP.call_tool` seam and FOR candidate 2 in §S3.
5. **Whether `test_comms_wiring.py`'s single real-ledger `publish` call is meaningfully "covering"
   `publish`.** It asserts the schema's non-empty-body ASSERT fires; it exercises the symbol but
   pins the schema. I counted it in the 55 because it does execute the real code path, and I am
   flagging the judgement rather than burying it.
6. **Whether `AgentRegistry` has any hard-delete path.** I checked `agents.py` for `DELETE` and found
   none (retire is a status change, matching finding #105's stated assumption), but I did not sweep
   the whole tree, test helpers, or the reconcile/GC paths for a delete that reaches the `agent`
   table. #105 says the defect *"goes live the day anything hard-deletes an agent row (a GC pass, a
   purge verb, an admin tool, a test-cleanup helper reaching production)"* — establishing that no
   such path exists today would need its own sweep.
