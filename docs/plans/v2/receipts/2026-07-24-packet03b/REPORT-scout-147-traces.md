# REPORT-scout-147-traces — diagnosis of finding #147 (trace path records nothing)

brief-base v6 read

- state: **done** — #147 diagnosed, verdict CONFIRMED, reading **(c)-shaped but precisely: the write function exists, is correct, and is NEVER CALLED.**
- Q1 write path: `SurrealStore.record_trace` (`loremaster/loremaster/store/surreal.py`) → `CREATE trace CONTENT $content`; table `trace`, 8 columns (`_TRACE_FIELD_SPECS` in `store/surreal_schema.py`).
- Q2 called?: **NO. Zero production call sites — in source AND in the deployed artifact.** Missing seam = `FastMCP.call_tool` (the single funnel; `mcp` 1.27.2 has no middleware hook) and every `@mcp.tool` handler body.
- Q3 does it land?: **PRODUCTION `:18500` (READ-ONLY probe, 2026-07-24): `trace` table DEFINED, `count() = 0`, aggregate `[]`.** Re-read after this session's ~10 lore tool calls: still 0.
- Q4 read vs write: **READ SIDE IS FINE — proven by positive control.** On TEST `:18000` I wrote 3 rows via the real `record_trace` and the real `trace_aggregates` returned them correctly. Nothing is written; nothing is misread.
- Q5 recommendation: **ride the existing trace path, EXTENDED — do not mint a second observability table.** But see the LOAD-BEARING FINDING below: a drain-only ordinal **cannot measure decay** (no denominator). 03b must trace *every* tool call or packet 06 still ships on opinion.
- decisions-needed (3): (1) drain-only vs all-tools tracing — I recommend all-tools; (2) ordinal scope GLOBAL-sequence vs PER-AGENT (packet wording admits both readings); (3) how to key the denominator by agent, since only `lore_comms` carries an `agent` param.
- deviation: none. Read-only honoured. The only writes I made were to a throwaway namespace `lore_probe147` on the **TEST** store `:18000`, removed at the end. `:18500` saw SELECT/INFO only.
- flagged (out of #147's scope, surfaced not fixed): production DB has **no `message` / `to` tables** — the 03/03a comms ledger schema is undeployed; 03b "DEPLOYS BOTH" so this is expected but must not surprise its deploy step.
- receipt pointers: §1 (write path) · §2 (call-chain) · §3 (live store probes) · §4 (positive control) · §5 (recommendation + forks) · §6 (residuals).

---

## 0. Method + tool honesty

lore-first: `lore_index()` (freshness — `git_ref 6a66671`, matching HEAD, so the graph is current for
this session; I edited nothing), `lore_findings action=get id_or_number=147`, `lore_search`,
`lore_get_symbol`, `lore_impact`.

**Grep fallbacks, said out loud (all three are the sanctioned cases):**
1. **Exhaustiveness** — `lore_impact` returned `record_trace` as `dead (heuristic)` with an explicit
   astroid-bounds caveat *and* a bare-name-channel caveat (it may be a UNION with
   `FakeSurrealStore.record_trace`). A "dead" verdict is a lead, never proof, so I corroborated with a
   **bare, anchor-free** grep for `record_trace` (no `await` anchor, no call-paren anchor) across
   `*.py`/`*.md`/`*.yaml`/`*.toml`. This is CLAUDE.md's rename-sweep rule applied to a liveness
   question, and it is what let me classify the two production hits as PROSE, not calls.
2. **Non-symbol textual seams** — the served tool description and the docstrings that describe the
   trace mechanism are string literals; no graph query can reach them.
3. **The deployed artifact** — a graph over the source tree cannot answer "does the running image
   call it". That needed `podman exec` + grep inside the container (§2.3).

Store law: `docs/reference/surrealdb-31-capabilities.md` read before interpreting any store behaviour
(the "READ THIS BEFORE YOU TOUCH THE STORE" box, §1.1 the DDL decision rule, §1.4 schema-converges/
data-does-not, §6 where the vendor docs are false). Cited in §5; not re-transcribed.

Citations are SYMBOLS, not line numbers, per brief-base §1.

---

## 1. Q1 — Where is the trace write path?

| element | address |
|---|---|
| write method | `loremaster.store.surreal.SurrealStore.record_trace` |
| statement | `CREATE {TRACE_TABLE} CONTENT $content` — one `_query` call |
| table | `trace` (`TRACE_TABLE` in `loremaster.store.surreal_schema`) |
| columns | `_TRACE_FIELD_SPECS`: `tool` string · `params_hash` string · `hit_count` int · `latency_ms` number · `session` string · `ts` datetime `DEFAULT time::now()` · `token_cost` `option<int>` · `model` `option<string>` |
| DDL emitter | `loremaster.store.surreal_schema._trace_statements` (called from `generate_ddl`) |
| read method | `loremaster.store.surreal.SurrealStore.trace_aggregates` — `SELECT tool, count() AS calls, time::max(ts) AS latest FROM trace GROUP BY tool` |
| render | `loremaster.server.IndexEngine._trace_summary` → `loremaster.server.TraceSummary` / `ToolTraceCount`, surfaced in `IndexStatusSummary.traces` |

The write is well-built and its constraints are documented in place: `CONTENT` (not `SET`) because
`session` is a SurrealDB **protected variable** — the store reference's DML section (§2) is the
authority for that idiom, and `record_trace`'s docstring cites it. `ts` is server-stamped. Each call
appends a DISTINCT row (append-only event, never keyed/deduped).

**The gap is DOCUMENTED IN THE SOURCE ITSELF, in two places** — this is not a hidden bug, it is an
unfinished wiring that nobody closed:

- `SurrealStore.record_trace` docstring: *"The async fire-and-forget EMISSION that schedules these
  writes, and the aggregates over the rows, are a later serving-layer phase (P8d)."* — the aggregates
  half of that sentence WAS built (`trace_aggregates`, "P8d Wave 3"); the **emission half was not**.
- `loremaster.server.TraceSummary` docstring: *"`total`/`by_tool`/`latest_at` are `0`/`[]`/`None`
  when nothing has ever been traced — **which is EVERY boot today, since no caller yet wires the
  per-invocation `record_trace` emission**."*

So #147's three candidate readings resolve as: **not (b)** (nothing is written elsewhere), **not (a)
in its literal form** (tracing is not "wired for search/read tools only" — it is wired for *nothing*),
and **(c) in a specific shape**: the write path is present, correct and tested, but has **no caller at
all**. The aggregate that reads it is real and working.

---

## 2. Q2 — Is it ever CALLED? **No.**

### 2.1 Graph verdict
`lore_impact(target="record_trace")` → `verdict: dead (heuristic)`, **0 production references / 15
test references**, `direct_consumers: []`. Carries the standard astroid caveat, hence §2.2.

### 2.2 Bare grep corroboration (source tree, HEAD 6a66671)
Every hit outside `loremaster/tests/` is PROSE, individually adjudicated — no "all remaining hits are
X" wholesale classification:

| file:symbol | verdict |
|---|---|
| `store/surreal.py::SurrealStore.record_trace` | the DEFINITION |
| `store/surreal.py::SurrealStore.trace_aggregates` (docstring) | prose — cross-reference |
| `server.py::TraceSummary` (docstring) | prose — **and it states the gap outright** |
| `store/surreal_schema.py` (comment above `_TRACE_FIELD_SPECS`) | prose — one-source-of-truth note |
| `docs/reference/surrealdb-31-capabilities.md` (DML section) | prose — cites it as the CONTENT idiom exemplar |
| `LORE_EXTERNAL_REVIEW.md` | prose — external review note |
| all others (`loremaster/tests/**`) | TEST call sites (15) |

**Zero call sites in `loremaster/loremaster/**`.**

### 2.3 The DEPLOYED ARTIFACT says the same thing
Per CLAUDE.md's "THE TEST ENVIRONMENT IS A FICTION" law, source agreement is not artifact agreement.
Grep inside the running production container (`lore-lore`, `LORE_VERSION=v0.4-236-g2b69616`),
package root `/app/loremaster/loremaster`:

```
/app/loremaster/loremaster/server.py:1641:    per-invocation :meth:`...SurrealStore.record_trace`
/app/loremaster/loremaster/store/surreal.py:731:    async def record_trace(
/app/loremaster/loremaster/store/surreal.py:799:        Wave 3 — the "later serving-layer phase" ...
/app/loremaster/loremaster/store/surreal.py:812:        :meth:`record_trace` writes); ``[]`` for an empty trace table
/app/loremaster/loremaster/store/surreal_schema.py:534:# ``record_trace`` CONTENT keys and this DDL ...
```
Definition + four prose mentions. **The image ships zero callers.** (Line numbers quoted here are
container-artifact output, not source citations.)

### 2.4 The seam where the call is missing
Every `lore_*` tool is registered as a separate `@mcp.tool(...)`-decorated async function in
`loremaster.server.build_server`, each a thin passthrough of the shape
`return await _app_context(context).<method>(...)`. **No telemetry is emitted in any of them, and there
is no shared wrapper around them.** (`build_server`'s `mcp.add_tool` path exists only for
extension-registered tools; the ASGI interceptor near `_drive_lifespan` handles the *lifespan* scope
and explicitly passes HTTP scopes straight through — it is not a request seam.)

The **one** funnel every tool call passes through — built-ins and extension tools alike — is the SDK's:

```
mcp.server.fastmcp.server.FastMCP._setup_handlers:
    self._mcp_server.call_tool(validate_input=False)(self.call_tool)

FastMCP.call_tool(name, arguments) -> self._tool_manager.call_tool(name, arguments, context=..., convert_result=True)
```

That is the seam where a per-invocation `record_trace` emission belongs and does not exist.

**⚠ Constraint the packet must know: the installed SDK offers no supported hook there.** Measured:
`mcp==1.27.2`; the standalone `fastmcp` package is **NOT installed**; `hasattr(FastMCP,
"add_middleware") is False` and `[a for a in dir(FastMCP) if "middle" in a or "hook" in a] == []`.
See §5.3 for the packages-vs-hand-roll fork this creates.

---

## 3. Q3 — Does the write land? Live store probes

All probes 2026-07-24, engine `surrealdb-3.2.1` on both stores.

### 3.1 PRODUCTION `lore-surreal ws://127.0.0.1:18500/rpc`, ns `lore` / db `lore` — **READ ONLY**
Statements issued: `INFO FOR DB`, `SELECT count() … GROUP ALL`, and the verbatim `trace_aggregates`
SQL. **No write of any kind touched `:18500`.**

```
tables (20): agent, answers_to, brief, brief_counter, briefed, chunk, code_node, command,
             file, file_text, finding, finding_counter, memory, meta, name, refers,
             snapshot, snapshot_entry, task, trace
'trace' table DEFINED: True
SELECT count() AS n FROM trace GROUP ALL            -> [{'n': 0}]
SELECT tool, count() AS calls, time::max(ts) AS latest FROM trace GROUP BY tool -> []
```

Re-read **after** this session's own lore MCP traffic (~10 calls: `lore_index`, `lore_findings`,
`lore_search` ×3, `lore_get_symbol` ×2, `lore_impact`, `lore_read` ×2): **still `[{'n': 0}]`.**
That is the live contradiction #147 reported, reproduced with a before/after pair.

**The schema IS deployed** (`trace` is one of the 20 defined tables) — so this is emphatically not a
migration failure of the #107 class. The table is there, correctly defined, and empty.

### 3.2 TEST `spike-surreal ws://127.0.0.1:18000/rpc`
Root creds are `root` / `spikeroot` (per `loremaster/tests/_surreal_harness.py`, `DEFAULT_URL`), NOT
the `lore` creds the production store uses — a first probe with `SURREAL_USER`/`SURREAL_PASS` returned
`NotAllowedError`. Noted so the next agent does not lose the same five minutes.

---

## 4. Q4 — Read side or write side? **Neither is broken. Nothing is written. (Positive control.)**

A negative result needs a control (CLAUDE.md: *"a probe needs a control — the auditor's instrument can
lie the same way the author's did"*). "The aggregate returns `[]`" is worthless until I have shown the
same aggregate returning rows on a store I know has rows.

**Control, run on the TEST store only** (throwaway ns `lore_probe147`, db `test_<pid>_<uuid4>` per the
harness's `unique_database()` law):

1. Applied the project's **own** trace DDL — `surreal_schema._trace_statements()`, 9 statements — not
   hand-rolled DDL.
2. Wrote 3 rows through the **real** `SurrealStore.record_trace` (2 × `lore_search`, 1 × `lore_index`).
3. Read through the **real** `SurrealStore.trace_aggregates`:

```
trace_aggregates -> [{'calls': 1, 'latest': datetime(2026,7,24,0,41,35,894024, tzinfo=utc), 'tool': 'lore_index'},
                     {'calls': 2, 'latest': datetime(2026,7,24,0,41,35,890555, tzinfo=utc), 'tool': 'lore_search'}]
```

Correct counts, correct per-tool `time::max(ts)`, correct tz-aware datetimes. The probe demonstrably
*can* see rows — so `[]` on production means **an empty table**, not a blind read.

Discrimination check ("what wrong build would this still pass?"): a build with a broken *write* would
have returned `[]` here too; a build with a broken *read* would have returned `[]` or wrong counts
despite the writes. It returned the exact expected shape, so both halves are live.

Namespace `lore_probe147` was removed from `:18000` afterwards. The render layer above
`trace_aggregates` (`IndexEngine._trace_summary` → `TraceSummary`) is pinned by
`loremaster/tests/test_mcp_server.py::test_trace_aggregates_reflect_recorded_traces` (total=3,
by_tool `{lore_search:2, lore_impact:1}`, `latest_at is not None`) and its empty sibling
`test_trace_aggregates_empty_when_none_recorded`; I did not re-run those, and say so rather than imply
I did.

**Verdict: the write side is a working function with no caller; the read side works and is honestly
reporting an empty table.** #147 is not a data bug, an aggregation bug, a filter bug, or a time-window
bug. It is an unbuilt emission.

---

## 5. Q5 — What would drain telemetry need? **Recommendation**

### 5.1 ⚠ THE LOAD-BEARING FINDING: a drain-only ordinal cannot measure decay
Packet 03b (`docs/plans/v2/03b-comms-message-surface.md`, §"Scope IN", DRAIN TELEMETRY bullet) asks
that *"every drain records the calling agent and a monotonic call ordinal, so drain frequency is
derivable against turn index"*, so packet 06 can *"decide forced-drain on that CURVE, not on the
prediction."*

**Instrumenting drains alone gives you a numerator with no denominator.** Decay is the hypothesis that
an agent *stops* draining as its task proceeds — i.e. it is an **ABSENCE of drains across an
increasing number of turns**. A row is written only when a drain *happens*, so a long silent stretch
produces no rows at all and is indistinguishable from "the agent stopped working". To place drains
against turn index you must also know **how many tool calls that agent made in between** — which is
exactly what the generic per-invocation trace at the `FastMCP.call_tool` seam (§2.4) would provide.

Concretely: drain ordinals `[1, 2, 3]` are equally consistent with "3 drains in 5 tool calls" (no
decay) and "3 drains in 300 tool calls" (total decay). One is the null result, the other is the
finding packet 06 hangs on. **If 03b instruments drain only, packet 06 still ships on opinion — the
precise outcome the packet's own rationale exists to prevent.** I recommend the lead treat "trace
every tool call" as *in scope for 03b*, or explicitly rule it out of scope with that consequence
acknowledged. This is a scope decision and it is the operator's, not mine.

### 5.2 Recommendation: RIDE the existing trace path, extended. Do not mint a second table.
**Recommend (A): wire `record_trace` and add two `option` columns to `_TRACE_FIELD_SPECS`.**

Why, not a survey:
- **Everything except the caller already exists, is tested, and is deployed.** The write seam, its
  error classification (`SurrealConnectionError` vs `SurrealStoreError` through the self-healing
  `_query`), the protected-`session` CONTENT idiom, the server-side `ts`, the `GROUP BY` aggregate,
  the render, and — verified live in §3.1 — the `trace` table itself on the production store. A drain
  telemetry that writes its own table re-derives all of that.
- **A second observability write is copy #2 of one policy**, which CLAUDE.md's ONE IMPLEMENTATION law
  forbids outright ("duplication is a DESIGN decision — escalate; never quietly write copy #2"). The
  first drift would be the retry/error-classification rules — the exact #102/#120 shape.
- **The extension is migration-safe and the hazards are already ruled.** Adding `agent` /
  `ordinal` columns to a table that exists on a live store is precisely the #107 trap; the store
  reference's DDL decision rule (§1.1) settles it: **fields use `DEFINE FIELD OVERWRITE`** — which
  `surreal_schema._define_field` already emits — while tables/indexes/analyzers stay `IF NOT EXISTS`.
  §1.4's "schema converges, DATA does not" back-fill hazard is nil here because production holds
  **zero** trace rows (§3.1) — but the new columns must be `option<…>` regardless, so a non-drain
  trace can legitimately omit them.
- **The ordinal has an existing shared mechanism — use it, don't hand-roll a counter.** The store
  already mints monotonic ordinals natively: `surreal_schema._define_sequence` /
  `MESSAGE_SEQUENCE_NAME` backing `message.seq` (`DEFINE SEQUENCE IF NOT EXISTS` — never a bare
  `DEFINE SEQUENCE`, which raises on an existing store; see #146 and the store reference §1.1's
  SEQUENCE row). A hand-rolled `trace_counter` hot row would be a third mint policy competing with
  `finding_counter` and `brief_counter` — the #102 pattern-cloning defect, again.
- **`ts` is NOT a substitute for an ordinal.** It is a wall-clock stamp; under concurrency it gives no
  reliable per-agent call order, and equal-microsecond ties are unresolvable. The packet asked for a
  monotonic ordinal for a reason.
- **Identity is already in hand at the drain call site.** `lore_comms` requires `agent` on every
  action and accepts `session` (see the `comms` tool registration and `AppContext.comms` in
  `loremaster/loremaster/server.py`). No new plumbing for the drain leg.
- **Do NOT overload `trace.session` with the agent name.** That column is documented as *"the
  fleet/session identity that issued the call"*; stuffing an agent name into it makes the served
  aggregate lie and collides with any future generic tracing. A distinct `option<string> agent` column
  is the honest shape.

### 5.3 Forks I am NOT settling — each admits two readings that produce different code
1. **Scope: drain-only vs all-tools tracing.** §5.1. My recommendation: **all-tools**, because
   drain-only cannot produce the curve the packet is built to produce. Operator's call.
2. **Ordinal scope: ONE global sequence vs one per agent.** "a monotonic call ordinal" reads both
   ways. A single global `DEFINE SEQUENCE` still yields per-agent ordering (filter by `agent`, sort by
   `ordinal`) at one-sequence cost, and additionally gives a *global* interleaving that a per-agent
   counter destroys. My recommendation: **one global sequence.** Operator's call.
3. **Where the generic trace hooks, if fork 1 goes "all-tools".** The installed `mcp` 1.27.2 has **no
   middleware API** (§2.4, measured). Two shapes, and the packages-over-hand-rolling rule cuts both
   ways here:
   - **Subclass `FastMCP` and override `call_tool`** — the package does *not* do this job, so
     hand-rolling the gap is the rule working as intended: minimal surface (one method, delegating to
     `super()`), maximal verifiability (a pin that asserts every registered tool name appears in the
     trace table after a dispatch — a *coverage-as-a-checked-variable* gate, not a name-list, per
     CLAUDE.md's six-defeats table).
   - **Migrate to the standalone `fastmcp` package**, which does have a `Middleware` API with an
     `on_call_tool` hook. That is a dependency swap across the entire server surface — a design
     decision far larger than 03b, and I flag it rather than recommend it.
   My recommendation: **subclass + override**, and file the `fastmcp` migration as a separate
   ledger item so the trade is met deliberately rather than rediscovered.
4. **How to key the denominator by AGENT.** Only `lore_comms` carries an `agent` param; `lore_search`,
   `lore_read` etc. carry none, so a generic trace at the `call_tool` seam has no agent identity. The
   SDK `Context` exposes `client_id`, `request_id`, `request_context`, and `session` (the
   `ServerSession` object) — but **no plain session-id string**; streamable-http carries an
   `mcp-session-id` header. Deriving a stable per-agent key from that, and joining it to the
   `lore_comms register` identity, is real design work and **is not a builder task** (CLAUDE.md: a
   property to INVENT escalates; it does not go to a builder as "figure out the general form"). I
   recommend the lead route this to the Fable design sidecar before any contract is written.

### 5.4 And ship the INSTRUMENT with the fix
This defect is *"a status surface reporting a field nobody consumes, so nobody notices it is dead"* —
#131's shape, named as such in #147's own body. A fix that only wires the caller leaves the class
open. The invariant to ship alongside: **a pin that dispatches a tool through the real server seam and
asserts a `trace` row exists for it** — mutation-proven (remove the emission, watch it go RED), and
enumerating tool names as a *checked coverage variable* rather than asserting one hardcoded name.
Without that, the next refactor silently un-wires the emission and `traces.total` returns to 0 with
every gate green.

---

## 6. Residuals — surfaced, not repaired, not scoped away

1. **Production has NO `message` / `to` tables.** The 20-table `INFO FOR DB` in §3.1 lists neither.
   The comms ledger schema from packets 03/03a is not on the production store. 03b's INDEX row says it
   **DEPLOYS BOTH**, so this is presumably expected — but it means 03b's deploy is the *first* time
   `message`/`to` DDL touches a live store, and the store reference §1.5's warning applies (indexes
   must stay `IF NOT EXISTS`; flipping them turns a silent no-op into a **boot-time crash**). The
   inherited "both `message` indexes BEFORE its deploy — free window expires here" item from
   `03a-2-consume-path-design-rulings.md` is exactly this window. Worth an explicit pre-deploy check
   rather than an assumption.
2. **`lore_index`'s served tool description promises "per-tool trace-call aggregates"** (in the
   `lore_index` registration's `description` in `loremaster/loremaster/server.py`). It is not *false*
   — it does serve the aggregate — but every caller since P8d has received `0/[]/null` while the
   description reads as though the surface were live. This is the render-honesty half of #147's
   reading (a), and it is CLAUDE.md's "served English has no mechanical guard" class. Whether to
   qualify the description or simply make it true by wiring the emission is a packet decision; if
   fork 1 lands "drain-only", the description becomes actively misleading and **must** be qualified.
3. **The `trace.token_cost` / `trace.model` columns have zero writers.** Grep (bare) finds them only
   in the schema, the `record_trace` signature, and tests. They were built for per-call token
   accounting that, like the emission, was never wired. Not a defect — but if 03b touches this table,
   the lead should decide whether they stay, since an unwritten `option` column is free but an
   unexplained one invites the next agent to rediscover this same question.
4. **`cosine_floor` is stale** — `lore_index()` reports `state: "stale"`, measured over 214 files
   against 2929 now, and an embedding-schema fingerprint change. Already owned by packets 10/11 and
   already named in #147's body; re-confirmed here as still stale at HEAD 6a66671 on 2026-07-24, so the
   lead knows it did not quietly resolve itself. **Two of `lore_index`'s served measurements are
   currently non-functional** — the same pattern, twice, on one surface.
5. **Ledger hygiene:** #147 is still `open`. I filed nothing (read-only mandate; a duplicate finding
   would be noise). The lead may want to append this diagnosis to #147 and transition it —
   `acknowledged` if 03b will fix it, since the diagnosis it asked for is now complete.
