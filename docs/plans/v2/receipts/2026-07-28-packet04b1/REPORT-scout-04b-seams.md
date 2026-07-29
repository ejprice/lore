# REPORT-scout-04b-seams

brief-base v7 read

**Scope of every claim in this file: measured 2026-07-27 at `c4da1c3` (branch
`feat/surreal-unification`), read-only.** No test suite was run; neither SurrealDB store was
touched. Every "MEASURED" claim below is either an AST/DDL-generation run on this tree or a
quoted source span; every "INFERRED" claim is labelled as such at the point it is made.

---

## SUMMARY BLOCK

- state: **done**
- deviations: none (read-only scout; report is the only file written)
- `Packages considered:` **none — no mechanism specified** (read-only mapping scout; I specified
  and built nothing)
- **A1** — NO `blocks` relation exists (bare grep `blocks` over `loremaster/loremaster/**.py` +
  `BLOCKS_RELATION`: zero schema hits). Helper is `surreal_schema._define_relation_table`, **4
  call sites**, and DDL-generation MEASURES `briefed` + `to` **ENFORCED**, `refers` +
  `answers_to` **not** — ⚠ **the packet's #105 table is STALE: it marks `briefed` ❌.**
- **A2** — `blocked_by` is written at BIRTH ONLY, by ONE shaper `tasks.TaskLedger._new_task_content`,
  reached from exactly **2** verbs: `create_task` (a BARE `_query`, **not** a transaction) and
  `create_many` (N fragments, one txn). `supersede_task` passes `None` (successor is unblocked);
  `transition` never touches it. It is IMMUTABLE post-creation.
- **A3** — "blocked" is computed **client-side in Python** (`TaskLedger._is_blocked`, fed by an
  UNBOUNDED `SELECT * FROM task`), plus a server-side `array::len` CAS in `_claim_fragment`. Two
  renders name it. **No transitive/critical-path read exists anywhere.**
- **A4** — the ONLY cycle check is `AppContext._find_key_cycle`, over `create_many`'s **batch-local
  temp KEYS**. No acyclicity guard over persisted task ids; `create_task` has none at all.
- **B1** — `AppContext._comms_fleet` → `_render_comms_fleet` → `_render_comms_fleet_row` →
  `_render_comms_fleet_brief_cell`; headers quoted in §B1.
- **B2** — unread lives on the `to` edge's `seen_at IS NONE`. `MessageLedger.drain(peek=True)` is
  the only thing close; it is **per-agent and unbounded (#183)** — no batch/grouped equivalent of
  `acked_versions_for_ids` exists for messages.
- **B3** — TWO different "unacked directive" readings exist in code, with different symbols
  (`BriefLedger.acked_versions_for_ids` vs `MessageDrainResult.directive_pending`). **Spec
  ambiguity → escalated, §B3.**
- **B4** — the comms render's counting law is already built and explicit: counts come from the
  row-UNLIMITED `roster()`, never the capped `fleet()` window. Caps quoted in §B4:
  `_MAX_FLEET_LIMIT=200`, `_MAX_DRAIN_LIMIT=50`, `config.comms.fleet_limit`, `limit` slices.
- **C1** — `AppContext.findings` **8 returns**, `AppContext.claim_task` **1**, `AppContext.tasks`
  **6** → **15 total, not ~17** (the packet's figure is 2 high). All three `-> str`.
- **C2** — action tables + read/write labels in §C2. `findings.resolve_many`/`acknowledge_many` are
  **best-effort**, so "actually wrote" is per-ITEM — an all-failed batch writes nothing. Fork raised.
- **C3** — the three dispatchers are plain `str` + manual `safe_str`; `Rendered`/`SafeLine`/
  `render_line` live in `loremaster/render.py` and are used by the COMMS surface only. ⚠ **`Rendered`
  subclasses `str`, so mypy will NOT catch a `Rendered` appended to a `str`** — §C3.
- **C4** — no such computation exists, **and the three tools carry no caller identity at all**
  (`owner`/`actor`/`created_by` are bare free-text strings). §C4 — this is the packet's biggest
  unaddressed gap.
- **D1** — quoted verbatim in §D1; **four** prose sites, not two.
- **D2** — MEASURED by AST sweep over all 62 prod `.py` files (56 query-composition sites): **ZERO
  identities interpolated into query text anywhere** (not just comms). Every residual hit
  adjudicated individually in §D2 — 6 classes, each with file:SYMBOL + verdict. **#219 does NOT
  invert**, and its own body forbids deleting the guard (§G).
- **E1** — via `lore_comms action=send` the sender is **STORE-RESOLVED** (`agent_registry.touch`).
  At the LEDGER seam it is **caller-supplied and unvalidated**. §E1.
- **E2** — `("sender", "record<agent>", "")` — a record LINK with **no constraint**. §E2.
- **E3** — **No.** `sender` is a FIELD on `message`, not an edge endpoint; `to`'s `ENFORCED` cannot
  see it. INFERRED from schema; the door is MEASURED open by 04a's adversary (I13). §E3.
- **E4** — **No overlap.** None of blocks/fleet/footer/#219 touches `MessageLedger.send`,
  `_send_fragment` or `_comms_send`. The fleet column work opens `messages.py` but a different
  region. §E4.
- decisions-needed: **4** — (1) B3's two directive readings; (2) C2's per-item write for the
  best-effort batch actions; (3) C4's missing caller identity (the footer cannot be built as
  specified without one); (4) the packet's stale #105 table + stale "~17 return points".
- receipt POINTERS: §A1–§A4 · §B1–§B4 · §C1–§C4 · §D1–§D2 · §E1–§E4 · §F (flags) · §G (tool honesty)

---

# A. The `blocks` task-DAG edge

## A1 — no `blocks` relation exists; the helper and its four calls

**MEASURED — `blocks` does not exist.** Established by a BARE, anchor-free grep (repo law:
sweep greps for a name carry no structural anchor):

```
grep -rn "blocks" --include=*.py loremaster/loremaster/     # 11 hits, ALL prose/unrelated:
#   auth.py, scout.py, store/candidate.py, store/_txn.py, server.py:3391/3406/3407 (a local
#   `blocks: list[str]` of rendered TEXT blocks), server.py:4530/7565/9922, calibration/engine.py
grep -rn "BLOCKS_RELATION\|blocks_relation" --include=*.py .   # 0 hits
```

No schema constant, no DDL statement, no ledger method. There is also no `blocks` in
`_STRUCTURAL_TABLES` (the residual bare-table list, currently empty).

**The helper — `loremaster/loremaster/store/surreal_schema.py::_define_relation_table`.**
Signature and body, quoted verbatim:

```python
def _define_relation_table(
    name: str, in_table: str, out_table: str, *, enforced: bool = False
) -> str:
    ...
    enforced_clause = " ENFORCED" if enforced else ""
    return (
        f"DEFINE TABLE OVERWRITE {name} TYPE RELATION "
        f"IN {in_table} OUT {out_table}{enforced_clause} SCHEMAFULL"
    )
```

Its docstring already carries the migration law the packet restates (`OVERWRITE`, not
`IF NOT EXISTS`; "a MEASURED SILENT NO-OP on an existing edge table … #107's shape").

**Every current call — 4, exhaustive (AST-visible; all four are literal calls in this file):**

| # | owning symbol | call | `enforced` |
|---|---|---|---|
| 1 | `surreal_schema::_briefed_statements` | `_define_relation_table(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE, enforced=True)` | **True** |
| 2 | `surreal_schema::_message_statements` | `_define_relation_table(TO_RELATION, MESSAGE_TABLE, AGENT_TABLE, enforced=True)` | **True** |
| 3 | `surreal_schema::_refers_statements` | `_define_relation_table(REFERS_RELATION, CODE_NODE_TABLE, NAME_TABLE)` | False |
| 4 | `surreal_schema::_answers_to_statements` | `_define_relation_table(ANSWERS_TO_RELATION, CODE_NODE_TABLE, NAME_TABLE)` | False |

### ⚠ A1-FLAG — THE PACKET'S #105 TABLE IS STALE

**MEASURED by GENERATING the DDL, not by reading the call sites** (so the claim is about the
served statement, not the recipe):

```
$ uv run python -c "from loremaster.store import surreal_schema as s; ..."
[brief]   DEFINE TABLE OVERWRITE briefed TYPE RELATION IN agent OUT brief ENFORCED SCHEMAFULL;
[message] DEFINE TABLE OVERWRITE to      TYPE RELATION IN message OUT agent ENFORCED SCHEMAFULL;
[graph]   DEFINE TABLE OVERWRITE refers      TYPE RELATION IN code_node OUT name SCHEMAFULL;
[graph]   DEFINE TABLE OVERWRITE answers_to  TYPE RELATION IN code_node OUT name SCHEMAFULL;
```

The packet file (`docs/plans/v2/04-comms-blocks-footer.md`, the "#105 — THE `ENFORCED` SWEEP"
table) says **`briefed` ❌ … confirmed still a bare string**. That was true at 04b's *writing*;
**packet 04a landed the `briefed` flip** (`surreal_schema.py::_briefed_statements` docstring says
so verbatim: *"``ENFORCED`` since packet 04a (#105)"*, and `INDEX.md` row 04a says *"#105
**RESOLVED for `to`+`briefed`**"*). **So `TWO of four` are enforced, not one, and the remaining
gap is `refers` + `answers_to` only** — which `INDEX.md` routes to **packet 43**, not 04b. The
packet's own text has already been wrong once in this exact way (it warns that the previous
version *"was STALE and understated what packet 03 shipped"*); this is the same paragraph, stale
again, one packet later. **Re-derive before building.**

### A1-NOTE — where a `blocks` edge must be REGISTERED (a second, non-obvious site)

`generate_ddl()` is **NOT** the whole schema. MEASURED — it composes only:
`_chunk/_file/_file_text/_memory/_trace/_meta/_snapshot/_snapshot_entry/_command/_task/_finding/_finding_counter`.
The comms + graph tables ride separate generators (`generate_agent_ddl`, `generate_brief_ddl`,
`generate_message_ddl`, `generate_graph_ddl`) applied by their own ledgers' `ensure_ready`.

Consequence for `blocks`: a `blocks` edge belongs in `surreal_schema::_task_statements`, which is
consumed by **both** `generate_task_ddl` (applied by `TaskLedger.ensure_ready`) **and**
`generate_ddl`. Putting it anywhere else creates a table one path defines and the other does not.
`TaskLedger.ensure_ready` applies `generate_task_ddl()` inside ONE `BEGIN…COMMIT` via
`execute_transaction` (its docstring: *"which verifies EVERY statement's status (the SDK's plain
``query()`` inspects only the first)"*).

## A2 — where `blocked_by` is written and read

**MEASURED: `blocked_by` is written at BIRTH ONLY, and is IMMUTABLE afterwards.** The claim-path
docstring states it outright (`tasks.py::TaskLedger.claim_task`): *"``blocked_by`` never changes
after creation, so reading it here is consistent"*.

**ONE shaper.** `loremaster/loremaster/tasks.py::TaskLedger._new_task_content` is the sole place
the column's value is composed:

```python
_COL_BLOCKED_BY: list(dict.fromkeys(blocked_by or ())),
```

(order-preserving dedupe — its comment: *"a DUPLICATE id must not double-count against the claim
gate's ``array::len`` CAS"*.)

**Every WRITE path — 3 callers of that shaper, 2 of which can carry a non-empty list:**

| # | file:SYMBOL | txn shape | SurrealQL fragment (verbatim) | carries `blocked_by`? |
|---|---|---|---|---|
| W1 | `tasks.py::TaskLedger.create_task` | ⚠ **BARE `self._query(...)` — NOT a transaction, NOT a `TxnFragment`** | `f"CREATE type::record('{TASK_TABLE}', ${_ROW_ID_PARAM}) CONTENT ${_ROW_CONTENT_PARAM}"` | **yes** (caller arg) |
| W2 | `tasks.py::TaskLedger.create_many` | `TxnFragment` per spec, all in ONE `self._apply(fragments)` | `f"CREATE type::record('{TASK_TABLE}', ${id_param}) CONTENT ${content_param}"` | **yes** (`spec.blocked_by`) |
| W3 | `tasks.py::TaskLedger.supersede_task` → `_supersede_fragment` | 3 statements, one txn | `f"CREATE type::record('{TASK_TABLE}', ${_SUPERSEDE_NEW_ID_PARAM}) CONTENT ${_SUPERSEDE_CONTENT_PARAM}"` | **NO** — calls `self._new_task_content(subject, description, None, created_by, now)` |

**`transition` does NOT touch it.** `tasks.py::TaskLedger._transition_fragment` builds `set_parts`
from `{status, updated_at, provenance.events}` (+ `owner`/`claimed_at` on `release`, +
`summary`/`report_path` on `done`). `blocked_by` appears in no branch.

### ⚠ A2-FLAG (removed-behaviour inventory input, for the mirror)

1. **`create_task` is the ONLY blocked_by writer that is not already transactional.** Mirroring a
   `blocks` edge into "the existing write txn" is a no-op phrase for W1 — there is no txn. The
   builder must convert `create_task` to `self._apply([fragment])`, exactly as `create_many`
   already does, or the CREATE and the `RELATE` will not be atomic. **This is a real behaviour
   change on a live verb, and it is invisible from the packet text.**
2. **`supersede_task` silently DROPS the predecessor's dependencies** — the successor is born
   unblocked. Whether the mirrored edge should follow (successor gets no `blocks` in-edges) is
   spec-silent. It is *consistent* with today's row, so "mirror exactly" is the safe read, but the
   inventory must record it as `old-behaviour-preserved` deliberately, not accidentally.
3. **The dispatcher, not the ledger, resolves temp keys.** `server.py::AppContext._create_many`
   pre-mints every id and rewrites `blocked_by`:
   `blocked_by=[key_to_id.get(ref, ref) for ref in item.blocked_by]`, then passes `ids=` down. The
   ledger stays key-agnostic (its docstring says so). **A `blocks` edge minted in the LEDGER
   therefore sees already-resolved ids — but ids that may name NOTHING** (see A2-FLAG 4).
4. **`blocked_by` is FAIL-OPEN at write, fail-closed at read.** Nothing validates that a
   `blocked_by` entry names an existing task: `_is_blocked` treats an unknown id as UNRESOLVED and
   the claim CAS's `array::len` comparison likewise fails closed. **This is directly load-bearing
   for `ENFORCED`-from-birth on `blocks`:** an `ENFORCED` edge to a non-existent task will make the
   whole CREATE txn **roll back**, where today the task is created and simply never claimable.
   That is a behaviour change on `lore_tasks action=create` and `action=create_many`, of exactly
   the shape 04a measured for `briefed` (*"After the flip the txn rolls back and the publish is
   LOST"*). **It needs an app-level pre-check to teach, for the same reason the packet already
   states `ENFORCED` alone cannot teach.**

## A3 — where "blocked" is computed and served today

**Computed CLIENT-SIDE, in Python.** `tasks.py::TaskLedger._is_blocked(task, status_by_id)`:

```python
for blocker_id in task.blocked_by:
    blocker_status = status_by_id.get(blocker_id)
    if blocker_status is None or blocker_status not in TERMINAL_STATUSES:
        return True
return False
```

Its feeder is `tasks.py::TaskLedger.query_tasks`, whose FIRST statement is
**`f"SELECT * FROM {TASK_TABLE}"` — no `WHERE`, no `LIMIT`**. Every filter (`status`, `owner`,
`blocked`) is applied in a Python loop afterwards. Its docstring gives the reason for the
unbounded read: *"Blocker statuses are resolved against the full table so a blocker filtered OUT
by the ``status``/``owner`` filter still counts."*

**Server-side, inside the claim transaction only** — `tasks.py::TaskLedger._claim_fragment`:

```
LET $clm_resolved = (SELECT VALUE record::id(id) FROM task
                     WHERE record::id(id) IN $clm_blocked_by AND status IN $clm_terminal)
UPDATE type::record('task', $clm_id) SET ... WHERE ... AND array::len(blocked_by) = array::len($clm_resolved)
```

**Renders that say a task is blocked — 2:**

1. `server.py::AppContext._render_claim_result`:
   `reason = f"blocked_by {task.blocked_by} unresolved"` →
   `f"not claimed: task {task.id} is unowned but not claimable ({reason})"`.
   ⚠ Its own docstring already flags this line as a residual: *"The BLOCKED/UNOWNED branch below
   interpolates ``blocked_by``/``status``, not ``owner`` — out of this pull-forward's named scope
   … flagged as a residual gap for the PKT-03 tree-wide sweep."* **The blocker ids are rendered
   UNSANITISED.** They are ledger-minted `uuid4().hex` on the normal path — but `create_many`'s
   pass-through (`key_to_id.get(ref, ref)`) lets an arbitrary caller string reach this render.
2. `server.py::AppContext._render_task_rows` / `_task_status_marker` — the `action=query` rows.

**TRANSITIVE / CRITICAL-PATH READ: does not exist.** Established by (a) the absence of any
`blocks` edge at all (A1), so there is nothing to traverse, and (b) grep for `@.{`, `+collect`,
`->blocks`, `critical` across `loremaster/loremaster/**.py` — zero hits. Every blocked computation
above is exactly ONE hop deep.

## A4 — acyclicity

**MEASURED: exactly ONE cycle check exists, and it does not guard the persisted DAG.**

`server.py::AppContext._find_key_cycle(edges: dict[str, set[str]]) -> list[str] | None` — a DFS,
called once, from `server.py::AppContext._create_many`:

```python
edges = {item.key: {ref for ref in item.blocked_by if ref in key_index} for item in ...}
cycle = self._find_key_cycle(edges)
if cycle is not None:
    raise ValueError("create_many items contain a blocked_by cycle among batch keys: "
                     f"{' -> '.join(cycle)} — a cyclic batch can never be claimed; break the cycle")
```

Note the filter `if ref in key_index`: the graph is built **only over BATCH-LOCAL TEMP KEYS**. A
`blocked_by` entry naming a REAL, already-persisted task id is excluded from the edge set entirely.

**Therefore, today, all of these are accepted with no error:**
- `create_task(blocked_by=[<its own future id>])` — impossible in practice (the id is minted after),
  but `create_task` has **no cycle check of any kind**;
- a `create_many` batch whose items depend on persisted tasks that transitively depend back into
  the batch;
- any cycle formed across two separate `create_many` calls.

Grep receipt (exhaustive, `cycle|acyclic|Cycle`, excluding `lifecycle`/`recycl`, over `tasks.py` +
`server.py` + `surreal_schema.py`): 13 hits — 1 import-comment, 1 `FindingChainCycleError` mention
(the FINDINGS supersedes chain, a different graph), 1 module comment at `server.py:6375`, and 10
belonging to `_find_key_cycle` and its single call site. **Nothing else.**

---

# B. The fleet view's unread / unacked-directive columns

## B1 — the fleet render

**Four symbols, all in `loremaster/loremaster/server.py`:**

| symbol | role | return type |
|---|---|---|
| `AppContext._comms_fleet` | the handler: fetches roster + window + brief head + ack edges | `Rendered` |
| `AppContext._render_comms_fleet` | header + rows + elision + retired trailer | `Rendered` |
| `AppContext._render_comms_fleet_row` | ONE row, cells joined `" · "` | `Rendered` |
| `AppContext._render_comms_fleet_brief_cell` | the `project`-brief cell | `SafeLine \| None` |

Store side: `loremaster/loremaster/agents.py::AgentRegistry.fleet` (capped window) and
`AgentRegistry.roster` (row-UNLIMITED true counts).

**The header lines, quoted verbatim** (`_render_comms_fleet`, two variants):

```python
"fleet (session {session}): {total} non-retired agents — {parked} input_required, "
"{active} active, {idle} idle"
```
```python
"fleet: {total} non-retired agents — {parked} input_required, {active} active, "
"{idle} idle"
```

**The row shape, quoted verbatim** (`_render_comms_fleet_row`, two variants — deliberately
duplicated calls, not a ternary, because the AST template-literal pin requires `args[0]` to be an
`ast.Constant`):

```python
"- {name} [{status} ⚠ STALE] hb {age} · {cells}"
"- {name} [{status}] hb {age} · {cells}"
```

`{cells}` is `render_join(" · ", cells)` over, in order: `role <role>` (always), `model <model>`
(if set), `task <8-char-prefix>…` (if set), the brief cell (if a head exists), `note: <last_note>`
(if set). **New unread/directive columns land in this `cells` list** — which means they are
`SafeLine`, joined by a literal separator, and each is INDIVIDUALLY OMITTABLE (every existing cell
past the first is conditional).

Other lines: the elision (`"+{more} more beyond the display cap ({cap})"` OR
`"+{more} more — re-run with limit={next_limit}"`), the retired trailer (`"+{count} retired"`), and
the rowless variants (`"no agents registered"` / `"no agents registered (session {session})"`).

## B2 — where unread lives, and how a per-agent count would be computed

**Unread state lives on the `to` relation edge, as `seen_at IS NONE`.** Verbatim from
`messages.py::MessageLedger.drain`: *"Pending = every message carrying an UNSTAMPED
(``seen_at IS NONE``) ``to`` edge to ``agent_id``."*

**The ONE symbol that already computes it — `loremaster/loremaster/messages.py::MessageLedger.drain`:**

```python
rows = self._as_rows(await self._query(
    f"SELECT in.{_ID_KEY} AS message_id, in.seq AS seq, in.grade AS grade, "
    ... f"FROM {TO_RELATION} WHERE out = $agent AND seen_at IS NONE", {"agent": agent_rec}))
pending = sorted(rows, key=lambda row: int(row["seq"]))
total_pending = len(pending)
directive_pending = sum(1 for row in pending if row.get("grade") == MESSAGE_GRADE_DIRECTIVE)
```

Its docstring already states the counting law the packet wants:
*"``total_pending``/``directive_pending`` are computed over the WHOLE pending set, never the capped
window (a display cap bounds rows rendered, never the numbers beside them)."*

**But it is the WRONG SHAPE for a fleet column, three ways:**

1. **It is per-agent.** One call per displayed row = up to `_MAX_FLEET_LIMIT` (200) round-trips —
   exactly the N+1 `_comms_fleet`'s own comment says it refuses:
   *"the per-row ack/heartbeat-age lookups below walk exactly the rows about to be rendered … the
   N+1 an unbounded per-row loop over ``roster().members`` would be."*
2. **It has SIDE EFFECTS unless `peek=True`.** A stamping drain in a fleet render would mark
   another agent's inbox read.
3. **⚠ Its read is UNBOUNDED — ledgered as finding #183** (verbatim, `area=comms-messages`,
   status **acknowledged**): *"drain's pending read is unbounded — bound it when packet 05's
   ``since=``/paging work reshapes the read path"*. It SELECTs every unstamped edge row **with its
   full BODY** (`in.body AS body`) purely to `len()` the result. Doing that ×200 in one fleet
   render multiplies an already-ledgered unbounded read by the fleet size.

**The RIGHT-SHAPED precedent already exists — for briefs, not messages:**
`loremaster/loremaster/briefs.py::BriefLedger.acked_versions_for_ids(ids, *, name)`. `_comms_fleet`
calls it and comments: *"ONE grouped edge lookup for the whole displayed window (finding #94) —
never a per-row ``acked_version`` round-trip."* **No message-side equivalent exists** (grep over
`messages.py` for a method taking a plural `ids`/`agent_ids`: only `_resolve_message_ids(seqs)`,
which is message-keyed, not agent-keyed). **A new `MessageLedger` method is required**, and per
`_comms_fleet`'s own precedent it should be a single `GROUP BY out` aggregate, projecting only
`out` + `grade` — never `body`.

⚠ **`.get(row.id)` defaulting to `None` is load-bearing** in the existing pattern
(`_comms_fleet`: *"an agent absent from the mapping is unbriefed, and must still render (never
silently drop out of the fleet the way a naive inner-join would)"*). A grouped unread count MUST
default a zero-traffic agent to `0`, not drop its row.

## B3 — where "unacked directives" live — ⚠ TWO READINGS, ESCALATED

**Both exist in code today, with different symbols, and they answer different questions.** The
packet says only *"per-agent unread + unacked-directive counts"*. Per brief-base §2 I state both
rather than picking silently.

**Reading (a) — BRIEF directive ack (the "standing brief" sense).**
`loremaster/loremaster/briefs.py::BriefLedger.acked_versions_for_ids` (batch, already wired into
`_comms_fleet`), `BriefLedger.acked_version` (single), `BriefLedger.coverage`,
`BriefLedger.subscribed_name_skew`. **This is ALREADY RENDERED** as the fleet's `project` cell
(`_render_comms_fleet_brief_cell` → `"project unbriefed"` / `"project v{n}"` /
`"project v{acked} (head v{head})"`). A new "unacked directive" column under this reading would
partly duplicate an existing cell.

**Reading (b) — MESSAGE-grade directives (`grade == "directive"` on the `to` edge).** Two distinct
sub-states exist on the SAME edge and they are NOT the same thing:
- **`seen_at IS NONE`** → undelivered/unread. Counted by `MessageDrainResult.directive_pending`
  (`messages.py::MessageLedger.drain`).
- **`acked_at IS NONE`** → delivered but the directive was never DISCHARGED. Written by
  `messages.py::MessageLedger.ack` (`UPDATE to SET acked_at = $acked_at, ack_note = $ack_note
  WHERE acked_at IS NONE AND out = $agent AND in IN $message_ids`). **NOTHING counts this today** —
  `acked_at` is read only per-message inside `ack` and `_row_to_inbox_entry`.

**My recommendation: reading (b), `acked_at IS NONE`, restricted to `grade = 'directive'`.**
Rationale: (i) reading (a)'s information is already on the row, so a second column adds nothing;
(ii) the drain render's own test comment points here —
`loremaster/tests/test_comms_tool.py`, in `test_...elided_directives...`:
*"the elided directives must still surface — through the elision line and the next drain (§B4.4;
**the directive COUNT itself is packet 04's counts family**)"*; (iii) `seen_at`-based counting is
already fully covered by the plain unread column, so a directive column keyed on `seen_at` is just
a filtered restatement of its neighbour, whereas `acked_at` surfaces a genuinely invisible state
(a directive read and ignored). **This is the reading that requires new code; the other two are
restatements. That asymmetry is the tell, but it is the operator's call.**

## B4 — THE COUNTING LAW: every cap and window in the comms render

**MEASURED. This is the most important section for the new columns, and the good news is that the
law is already built, explicit, and defended by a prior audit finding.**

`server.py::AppContext._render_comms_fleet` docstring, verbatim:

> ``status_counts`` is a REQUIRED, TRUSTED true aggregate (e.g. ``AgentRegistry.roster().status_counts``
> — all four statuses present, zero-filled when a status has no rows): the header total, the
> per-status segments, the elision arithmetic, and the retired trailer are ALL derived from it,
> never re-derived from ``window`` (v4 audit D1 fix — ``window`` may be a display-capped listing
> that silently disagrees with the truth past ``_MAX_FLEET_LIMIT`` agents; **there is no
> ``len()``-derived fallback path here on purpose, so an omitted argument can never silently
> resurrect that defect**). ``window.rows`` is still the source for WHICH rows to render.

And `_comms_fleet`'s own comment:

> TRUE counts come from the row-unlimited roster (v4 audit D1 fix) — never from a display-capped
> ``fleet()`` window.

**Every cap and window, enumerated individually (no "the rest are X"):**

| # | site (file:SYMBOL) | cap / window | verdict for a new count |
|---|---|---|---|
| 1 | `server.py::_MAX_FLEET_LIMIT` | `= 200` — hard display ceiling | **row cap only.** `_comms_fleet`: `display_limit = min(limit if limit is not None else self.config.comms.fleet_limit, _MAX_FLEET_LIMIT)` |
| 2 | `config.comms.fleet_limit` | default display limit | row cap only |
| 3 | `agents.py::AgentRegistry.fleet` | `limited = non_retired[:limit]` — **the capped window** | ⚠ **NEVER count over `window.rows`.** Returns an honest `total_non_retired` beside it. |
| 4 | `agents.py::AgentRegistry.roster` | **NO `limit` PARAMETER, deliberately** — docstring: *"a regression that re-added one would silently reintroduce the exact cap-vs-truth confusion this method exists to close"* | **THE source of truth.** `SELECT status, count() AS count FROM agent GROUP BY status`. |
| 5 | `server.py::_render_comms_fleet` | `shown = ordered[:limit]` | row slice only; `remainder = total - len(shown)`, where `total` comes from `status_counts` |
| 6 | `server.py::_comms_fleet` → `acked_versions` | computed over `window.rows` ONLY | **per-ROW cell, not an aggregate — this is the CORRECT precedent for a per-agent unread cell.** Legal because each cell describes exactly its own row. |
| 7 | `server.py::_comms_fleet` → `heartbeat_age_seconds` | over `window.rows` ONLY | same — per-row cell |
| 8 | `server.py::_MAX_DRAIN_LIMIT` | `= 50` | drain's row cap. `messages.py::drain`: `window = pending[:limit]` bounds ROWS; `total_pending`/`directive_pending` are computed on `pending` BEFORE the slice. |
| 9 | `messages.py::MessageLedger.drain`'s pending SELECT | **NO `LIMIT` at all** (#183, acknowledged) | ⚠ the count is honest **because** the read is unbounded. A new batch count must stay honest WITHOUT inheriting that unbounded read. |
| 10 | `tasks.py::TaskLedger.query_tasks` | `SELECT * FROM task` — **NO `LIMIT`** | out of the comms render, but same shape: honest-because-unbounded |
| 11 | `findings.py::FindingLedger.query` / `filed_since`, `tasks.py::updated_since` | `LIMIT {limit}` interpolated | rollup windows; each pairs its capped rows with an HONEST `total` from a separate `SELECT count() … GROUP ALL` |

**The decision this section was asked for:** a per-agent unread/directive count is a **per-ROW
cell** (category 6/7), not an aggregate, so computing it over `window.rows` is CORRECT and does
NOT violate the counting law — *provided the count itself is over that agent's WHOLE pending set,
not a capped slice of it.* The instrument to copy is `acked_versions_for_ids`: one grouped query
keyed on the displayed ids, `.get(row.id)` defaulting to `0`.

⚠ **The trap:** if 04b also adds a fleet-HEADER aggregate (e.g. *"N unread across the fleet"*),
that number MUST come from a roster-wide read, not from summing the per-row cells — the per-row
cells only cover the ≤200 displayed rows. The existing header derives every segment from
`roster().status_counts` precisely to avoid this.

---

# C. The `_comms_footer` seam

## C1 — the three dispatchers, return types, and EXACT return counts

**MEASURED by AST** (walk of each `FunctionDef` inside `class AppContext` in
`loremaster/loremaster/server.py`, counting `ast.Return` nodes):

### `loremaster/loremaster/server.py::AppContext.findings` → `-> str` — **8 returns**, 2 raises

1. `return await self._resolve_or_acknowledge_many(action=..., items=..., actor=...)`
2. `return f'reported finding #{report.number} (id {report.id}, status open)'`
3. `return self._render_finding_rows(rows)`
4. `return self._render_finding_detail(finding)`
5. `return self._render_chain_head(head)`
6. `return self._render_finding_transition(acked, actor)`
7. `return self._render_finding_transition(resolved, actor)`
8. `return self._render_finding_transition(closed, actor)`

Carries `# noqa: PLR0911 - P8d rewrites this render; restructuring now would churn`.

### `loremaster/loremaster/server.py::AppContext.claim_task` → `-> str` — **1 return**, 0 raises

1. `return self._render_claim_result(result)`

**Already a single exit.** Its render `_render_claim_result` has 4 internal returns, but the
dispatcher itself is 1.

### `loremaster/loremaster/server.py::AppContext.tasks` → `-> str` — **6 returns**, 3 raises

1. `return await self._rollup(since=since, limit=limit)`
2. `return await self._create_many(items=items or [], created_by=_require_arg(created_by, 'created_by'))`
3. `return f'created task {new_id} (status open)'`
4. `return self._render_task_rows(rows)`
5. `return self._render_task_transition(task, actor)`
6. `return f'superseded task {task_id}; successor {successor_id} (status open)'`

Carries `# noqa: PLR0911 - a dispatch-on-action verb; splitting churns every action's own test`.

### ⚠ C1-FLAG — the packet's "~17 return points" is **15**

8 + 1 + 6 = **15**. The packet ruling says *"three independent `-> str` dispatchers with ~17
return points"*. The design conclusion is unaffected (15 clones is still 15 clones), but repo law
says re-derive every inherited number. **The real figure is 15, of which claim_task's 1 is already
collapsed — so the refactor is 8→1 and 6→1, i.e. 12 return statements removed.**

**Bonus for the collapse:** both `# noqa: PLR0911` suppressions become deletable once each
dispatcher has one return. That is a mechanical, ruff-visible receipt that the collapse landed.

**The contrast worth noting** — `loremaster/loremaster/server.py::AppContext.comms` → `-> Rendered`
has **1 return** and 6 raises, and it is the surface that ALREADY uses the typed render seam. The
footer refactor is making the three `str` dispatchers structurally resemble `comms`.

## C2 — action names, read vs write

`_TASK_ACTIONS` and `_FINDING_ACTIONS` MEASURED by import:

### `lore_tasks` — 6 actions

| action | dispatcher branch | R/W | footer under the ruled trigger? |
|---|---|---|---|
| `create` | `task_ledger.create_task` | **W** | **yes** |
| `create_many` | `AppContext._create_many` | **W** | **yes** (all-or-nothing — either the whole batch wrote or nothing did) |
| `transition` | `task_ledger.transition` | **W** | **yes** |
| `supersede` | `task_ledger.supersede_task` | **W** | **yes** |
| `query` | `task_ledger.query_tasks` | R | no |
| `rollup` | `AppContext._rollup` | R | no |

### `lore_findings` — 9 actions

| action | dispatcher branch | R/W | footer under the ruled trigger? |
|---|---|---|---|
| `report` | `finding_ledger.report` | **W** | **yes** |
| `acknowledge` | `finding_ledger.acknowledge` | **W** | **yes** |
| `resolve` | `finding_ledger.resolve` | **W** | **yes** |
| `wontfix` | `finding_ledger.wontfix` | **W** | **yes** |
| `resolve_many` | `_resolve_or_acknowledge_many` | **W\*** | ⚠ **AMBIGUOUS — see C2-FORK** |
| `acknowledge_many` | `_resolve_or_acknowledge_many` | **W\*** | ⚠ **AMBIGUOUS — see C2-FORK** |
| `query` | `finding_ledger.query` | R | no |
| `get` | `finding_ledger.get` | R | no |
| `chain_head` | `finding_ledger.chain_head` | R | no |

### `lore_claim_task` — 1 verb, 2 outcomes

| outcome | branch (`_render_claim_result`) | R/W | footer? |
|---|---|---|---|
| WIN (`result.claimed`) | `"claimed: task … is now owned by …"` | **W** | **yes** |
| LOSS, owned | `"not claimed: … already held by …"` | **R (writes nothing)** | **no** — the packet's ruling names this case |
| LOSS, superseded / blocked / other status | `"not claimed: … unowned but not claimable (…)"` | **R (writes nothing)** | **no** |

⚠ Note the trigger is not observable from the dispatcher's parameters: it must read
`ClaimResult.claimed`. Since `claim_task` already has one return, this is the cheapest of the three.

### ⚠ C2-FORK — the two BEST-EFFORT batch actions (decision needed)

`AppContext.findings`' docstring, verbatim: the batch actions are
*"BEST-EFFORT sequential batch transitions … rendering a per-item outcome (**never all-or-nothing —
one bad item never vetoes the rest**)"*. So `resolve_many` with 5 items may write 5, 3, or **0**.

The ruled trigger is *"per-ACTION-OUTCOME — only calls that actually WROTE"*. Two readings, both
producing different code:

- **(i) per-CALL**: a footer iff ≥1 item wrote. Requires `_resolve_or_acknowledge_many` to return
  a write-count alongside its rendered string (a signature change on an internal helper).
- **(ii) per-ACTION**: `resolve_many` is a writing action, so it always footers. Simpler; wrong on
  the all-items-failed case, which is exactly the LOSING-branch shape the ruling excluded for
  `claim_task`.

**I would pick (i)** — it is the same principle the ruling already applied to `claim_task`'s losing
branch, and picking (ii) means the ruling holds for one tool and not the other. But it is a spec
question and I am not entitled to settle it.

## C3 — the types at these seams

**`Rendered`, `SafeLine`, `render_line`, `render_join`, `render_fenced`, `render_compose` are
defined in `loremaster/loremaster/render.py`** (`SafeLine` itself and `safe_str`/`sanitise_line`
live in `loremaster/loremaster/sanitise.py` and are re-exported through `render.py`'s import).

**Which of the three dispatchers use them: NONE.** `render.py`'s own module docstring says why,
verbatim:

> This module is where every NEW agent-comms render (C1-C5) is assembled — **existing task/finding/
> rollup renders keep their manual ``sanitise_line``/``safe_str`` wraps for now** (PKT-03 retypes
> them onto this seam; see the ruling's §DEFERRED).

So the split at HEAD is:
- **comms surface** (`AppContext.comms` and every `_comms_*` handler/render) → `Rendered` /
  `SafeLine`, assembled only via `render_line`/`render_join`/`render_fenced`/`render_compose`.
- **tasks / claim_task / findings** → plain `str` f-strings with manual `safe_str(...)` wraps
  (e.g. `_render_claim_result`: `f"claimed: task {task.id} is now owned by {safe_str(task.owner)}"`).

### ⚠ C3-FLAG — MYPY WILL NOT CATCH THE BOUNDARY CROSSING THE PACKET WARNS ABOUT

`class Rendered(str)` and `class SafeLine(str)` are **`str` SUBCLASSES**. Therefore:

```python
return f"{body}\n{footer}"          # footer: Rendered  →  mypy: SILENT. Result: plain str.
return body + footer                 # footer: Rendered  →  mypy: SILENT. Result: plain str.
```

Both typecheck cleanly against `-> str`. **The packet's D2 warning ("a footer built as `Rendered`
and appended to a `str` crosses the render-safety boundary the wrong way") is real, and there is no
type-checker instrument standing behind it.** The four instruments `render.py` documents cover:
mypy on VALUE and RETURN legs, the AST template-literal pin, the runtime control-char assert, and
the AST mint-pin. **A `Rendered` demoted to `str` by concatenation defeats all four** — mint-pin
sees a legal mint, template pin sees a literal template, the runtime assert already ran and passed,
and mypy sees `str + str`.

The three shapes available, with what each actually buys:

1. **Bare f-string footer** (`-> str`). Cheapest. **Creates a NEW un-sanitised served surface** —
   if the footer ever interpolates a count it is safe (ints), but if it ever interpolates an
   identity (agent name, task id) it is forgeable, and nothing in the tree will notice.
2. **`Rendered` footer, then `str(...)` it explicitly at the append.** Honest about the demotion,
   and the explicit `str()` is greppable. Gets `render_line`'s runtime control-char assert for
   free.
3. **Retype all three dispatchers to `-> Rendered`** and use `render_compose`. This is what
   `render.py` says PKT-03 intends anyway. Largest diff (every caller and every existing test
   asserting a `str` return), but it is the only shape where the boundary is enforced rather than
   observed.

**I would pick (2)** for this packet: it gets the runtime assert, keeps the diff proportional, and
does not pre-empt PKT-03's retype. **But the packet explicitly says "Choose deliberately and say
which", so this is the builder's/operator's call, and the choice needs a pin either way.**

⚠ **Whichever is chosen, note the mutation proof the packet demands is about the footer TEXT, not
the type**: *"change the footer text and ALL THREE pins must go RED"*. A shared `_comms_footer`
that all three call satisfies that regardless of return type — so the mutation proof will NOT
detect a wrong type choice. That needs its own pin.

## C4 — ⚠ THE PACKET'S LARGEST UNADDRESSED GAP: there is no calling agent

**MEASURED: no "pending traffic for the calling agent" computation exists — and, more seriously,
the three tools do not know who is calling.**

Grep receipt over `server.py` for `total_pending|directive_pending|peek=True|awaiting_answer|pending`:
16 hits, ALL inside `_render_comms_drain`/`_comms_drain` (the drain surface) or unrelated
(`_settle_schema_rebuild`, a weak-match note, an asyncio warning comment). Nothing outside the
comms surface computes pending traffic.

**The blocking problem.** The tool-level signatures (MEASURED, `server.py` `@mcp.tool` registrations
at `name="lore_claim_task"`, `name="lore_tasks"`, `name="lore_findings"`) and their `AppContext`
dispatchers carry **no `agent` and no `session` parameter**:

- `AppContext.claim_task(self, task_id: str, owner: str) -> str`
- `AppContext.tasks(self, *, action, task_id, subject, description, created_by, actor, status, owner, blocked, blocked_by, since, limit, items, summary, report_path) -> str`
- `AppContext.findings(self, *, action, id_or_number, subject, body, area, category, created_by, kind, actor, note, status, limit, supersedes, items) -> str`

The only identity-ish fields are `owner` / `actor` / `created_by` — **bare, free-text `str`s that
are never resolved against the `agent` table and are not required to name a registered agent.**
Contrast `lore_comms`, which takes a REQUIRED `agent` and resolves it through
`self.agent_registry.touch(agent, session=session, ...)` before any handler runs.

**Therefore `_comms_footer` cannot compute "traffic pends for YOU" as specified without one of:**

- **(a)** resolving `owner`/`actor`/`created_by` via `AgentRegistry.get_agent(name, session=None)`
  — which is a store round-trip on every mutating call, can raise `AmbiguousAgentError` when a
  display name spans sessions (`agents.py::_resolve_row`), and silently finds nothing for the
  common case where the identity is not a registered agent at all;
- **(b)** adding an optional `agent`/`session` parameter to all three tools — a served-schema
  change, and every existing caller omits it, so the footer would be dark by default;
- **(c)** narrowing the footer to something agent-independent (e.g. *"N unacked directives exist in
  the fleet"*) — which is a different feature from what the packet describes.

**None of these is in the packet.** I am not entitled to pick. **This is the fork I would put in
front of the operator first**, because it decides whether the footer is buildable at all, and
neither (a) nor (b) is a small diff.

⚠ **Related: the `_INSTRUCTIONS` equality pin will fire.** The packet already warns about
`test_comms_tool.py::TestTheServedInstructions...::test_the_served_INSTRUCTIONS_are_EXACTLY_the_declared_paragraphs`.
Confirmed at HEAD — that pin's own docstring names this packet:

> 2. another packet legitimately edited ``_INSTRUCTIONS`` — then update
>    ``_DECLARED_NON_COMMS_PARAGRAPHS`` and move on. **That is not this pin misfiring; it is the
>    deliberate decision the pin exists to force**, and **packets 04 and 05 will both meet it**;

There is also a DEMOTED sibling gate (a `_COMMS_DUTY_VOCABULARY` word-list regression gate) whose
docstring says explicitly **"it must not be GROWN"** — so footer prose must go through the declared
paragraph allowlist, never by adding a word to that list.

---

# D. #219 — `_validate_comms_charset`

## D1 — the current prose, verbatim

**`loremaster/loremaster/server.py::AppContext._validate_comms_charset`**, full docstring:

```
Charset-validate a comms identity value BEFORE any store touch (§0/§7).

The SAME ``AGENT_NAME_PATTERN`` guards agent names, sessions, AND
brief names (design doc §0: "Brief names ... same class as
agent.name ... same injection posture") — all three are inlined into
C3's live WHERE clauses, so all three share one charset.

``fullmatch``, never ``match`` (finding #210): Python's ``$`` matches
at end-of-string OR immediately before a TRAILING NEWLINE, so
``.match`` accepted ``"scout\n"`` — a second identity that renders
identically to ``"scout"`` wherever a trailing newline is invisible.
``fullmatch`` states the intent in the CALL rather than leaning on an
anchor, so a later edit to the pattern cannot silently re-open it.

Raises:
    ValueError: ``value`` does not match ``AGENT_NAME_PATTERN``.
```

**The SERVED error message** (same symbol — this string reaches an agent):

```python
raise ValueError(
    f"{label} {value!r} does not match {AGENT_NAME_PATTERN.pattern} — "
    f"names are inlined into store queries and must stay in the safe charset"
)
```

**The false claim is: "inlined into C3's live WHERE clauses" / "names are inlined into store
queries".** Both are FALSE (see D2).

### ⚠ D1-FLAG — the defect has FOUR prose sites, not the two the packet names

Sites 3 and 4 are NOT named in the packet text. I found them by BARE, anchor-free grep for
`inlin` (per repo law — prose carries no structural anchor); the 04a scout independently reported
the same four (`docs/plans/v2/receipts/2026-07-27-packet04a/REPORT-scout-pkt04-seams.md` §S7), and
I confirmed each against source at HEAD:

3. **`server.py::AppContext._validate_comms_identities`** docstring — *"a recipient IS an agent
   name — the fourth member of the identity class :meth:`_validate_comms_charset`'s own docstring
   says shares ONE charset **because all of them are inlined into live ``WHERE`` clauses**."*
   It **cites site 1 as its authority**, so fixing site 1 alone leaves a dangling justification.
4. **`loremaster/loremaster/agents.py`, the module comment immediately above `AGENT_NAME_PATTERN`**
   — the DEFINITION site: *"every ``agent.name`` / ``agent.session`` is **inlined as a literal into
   C3's live WHERE clauses**, so the charset is enforced here … Configurability would make the
   inlining guarantee operator-breakable, so this stays a MODULE CONSTANT, never a config knob."*
   ⚠ **This one derives a RULING from the false premise.** Correcting the prose without supplying
   a replacement reason leaves "never a config knob" standing on nothing. The real reasons that
   survive: defence-in-depth behind the store's own field `ASSERT`s, and the id-recipe surface
   (`AgentRegistry._agent_id` / `BriefLedger._brief_id` hash the identity into a `uuid5`, and a
   charset that admits arbitrary text makes the id recipe's collision/normalisation story harder
   to reason about).

## D2 — THE RESIDUAL SWEEP: does ANY path inline an identity into query text?

**ANSWER: NO. Measured, and measured OVER THE WHOLE PACKAGE, not just comms. #219 does NOT
invert — the prose is wrong and the code is right.**

**Method (said out loud, per brief-base §4).** I did NOT grep for the word "inlined" — that finds
prose that *claims* inlining, which is the defect, not the behaviour. I ran an **AST sweep over
every `.py` file under `loremaster/loremaster/`** (62 files, `find … -name '*.py' -not -path
'*__pycache__*' | wc -l`) for three composition shapes, then adjudicated each hit by reading it:

1. every `ast.JoinedStr` (f-string) whose literal parts contain a SurrealQL keyword
   (`SELECT|WHERE|UPDATE|RELATE|CREATE|DELETE|INSERT|LET|DEFINE|REMOVE|RETURN|FROM|type::record`) —
   **54 sites with a non-constant interpolation**;
2. `str.format` / `%`-formatting / `+` concatenation / `+=` onto query-ish literals — **2 sites**;
3. cross-check: every `WHERE` clause in the four comms modules read individually.

This is a grep/AST fallback rather than a lore graph query, and I am saying so: lore's graph is
symbol-granular, and *"is this VALUE interpolated into this STRING"* is a non-symbol textual seam
(repo CLAUDE.md dogfood protocol, case (b)). lore was used for the definitions and spans.

**Every non-constant interpolation into query text, adjudicated INDIVIDUALLY. No hit is grouped.**

### Class 1 — a PARAM NAME (not a value) is interpolated; the value is bound. Verdict: **BOUND**, ×20

Each of these interpolates the *name* of a `$param` (or a table/column module constant) and binds
the value in the params dict.

| file:SYMBOL | interpolated | verdict |
|---|---|---|
| `messages.py::MessageLedger._send_fragment` | `endpoint_param` → `RELATE $msg_rec->to->${endpoint_param}`; `params[endpoint_param] = RecordID(AGENT_TABLE, ref.id)` | **bound** |
| `tasks.py::TaskLedger.create_many` | `id_param`, `content_param` | **bound** |
| `index/snapshots.py::_stamp_fragment` | `snapshot_key_param`, `snapshot_content_param`, `entry_content_param` | **bound** |
| `index/surreal_manifest.py::replace_fragment` | `id_key`, `sha_key`, `mtime_key`, `size_key`, `n_chunks_key`, `chunk_ids_key`, `state_key`, `updated_key` | **bound** |
| `index/surreal_manifest.py::delete_fragment` | `id_key` | **bound** |
| `memory/local.py::_upsert_fragment` | `id_param`, `content_param` | **bound** |
| `memory/local.py::_close_superseded_fragment` | `old_param`, `now_param`, `by_param` | **bound** |
| `store/surreal.py::replace_file_fragment` | `tier_param`, `file_param`, `id_param`, `content_param` | **bound** |
| `store/surreal.py::delete_file_fragment` | `tier_param`, `file_param` | **bound** |
| `store/surreal.py::file_text_fragment` | `id_param`, `content_param` | **bound** |
| `store/surreal.py::file_text_delete_fragment` | `id_param` | **bound** |
| `graph_surreal.py::_node_statements` | `id_key`, `kind_key`, `qname_key`, `bare_key`, `chunk_key`, `fqn_name_key`, `bare_name_key` | **bound** |
| `graph_surreal.py::_edge_statement` | `src_key`, `dst_key`, `kind_key`, `resolved_key` | **bound** |
| `floor_calibration/store.py::_head_mint_statement` | `axis_assignments` (`col = $param` pairs) | **bound** |
| `floor_calibration/store.py::_measurement_create_statement` | `computed` (`col: $param` pairs) | **bound** |
| `agent_existence.py::reject_unknown_agents` | `_ID_KEY`, `_AGENT_IDS_PARAM`; ids bound as `RecordID` list | **bound** |
| `agents.py::AgentRegistry.register` (CREATE + UPDATE) | `_ROW_ID_PARAM` + `_REG_*_PARAM` names | **bound** |
| `agents.py::AgentRegistry.touch` | `_TOUCH_*_PARAM` names | **bound** |
| `agents.py::AgentRegistry._select_row` / `_select_rows_by_name` | `_ROW_ID_PARAM` / `_NAME_LOOKUP_PARAM` | **bound** — ⚠ note `_select_rows_by_name` is THE agent-name lookup, and it is `WHERE name = $<param>` |
| `briefs.py::_publish_fragment`, `findings.py::_report_fragment`, `findings.py::_transition_fragment`, `tasks.py::_transition_fragment`, `scout.py::_mark`, `store/lease.py::read` | `', '.join(content_fields)` / `', '.join(set_parts)` / `', '.join(set_clauses)` / `', '.join(_OBSERVATION_COLUMNS)` — each element is `col = $param` or `col: $param` built from module constants | **bound** |

### Class 2 — a COLUMN/TABLE module constant is interpolated. Verdict: **structural, not a value**, ×11

`agents.py::fleet` (`WHERE {_COL_SESSION} = ${_SESSION_FILTER_PARAM}`), `agents.py::roster` (×2,
via `where_clause` built from the same two constants), `tasks.py::query_tasks`
(`SELECT * FROM {TASK_TABLE}`), `tasks.py::_claim_fragment`, `tasks.py::_supersede_fragment`,
`findings.py::query`/`filed_since`, `messages.py::drain`/`ack`/`awaiting_answer`/`_resolve_message_ids`,
`store/surreal.py::_vector_subquery`/`_fulltext_subquery`.
**Every one interpolates an ALL-CAPS module constant naming a table or column.** No caller value
reaches query text on any of them.

### Class 3 — a caller-supplied `limit` INT is interpolated. Verdict: **INTERPOLATED, but not an identity — guarded**, ×3

These are the only sites where a value that originates at the tool boundary reaches query TEXT.

| file:SYMBOL | fragment | guard | verdict |
|---|---|---|---|
| `findings.py::FindingLedger.query` | `f"SELECT * FROM {FINDING_TABLE}{where} ORDER BY {_COL_NUMBER} ASC LIMIT {limit}"` | `if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0: raise ValueError(...)` immediately above | **interpolated (int)** — carries its own comment: *"``limit`` is a validated positive int, so interpolating it is injection-safe (SurrealDB's ``LIMIT`` wants a literal count, not a bound param here)"* |
| `findings.py::FindingLedger.filed_since` | `f"… ORDER BY {_COL_CREATED_AT} ASC LIMIT {limit}"` | same positive-int check | **interpolated (int)** |
| `tasks.py::TaskLedger.updated_since` | `f"… ORDER BY {_COL_UPDATED_AT} ASC LIMIT {limit}"` | same positive-int check | **interpolated (int)** |

⚠ Note the inconsistency, reported not fixed: `store/surreal.py::scroll` DOES bind its limit
(`ORDER BY {_ID_KEY} LIMIT ${_LIMIT_PARAM}`), so the *"LIMIT wants a literal count, not a bound
param"* comment in `findings.py` is contradicted by the same repo's own working code. One of the
two is wrong about the engine. **Not an identity, so it does not invert #219 — but it is a
`ONE IMPLEMENTATION` smell (three clones of one hand-rolled positive-int limit guard) and a
prose-vs-behaviour mismatch of exactly #219's class.**

### Class 4 — a DDL IDENTIFIER is interpolated. Verdict: **INTERPOLATED, config-sourced, unavoidable**, ×10

SurrealQL DDL has no bound-parameter form for object names, so these are structural by necessity.

| file:SYMBOL | fragment | source of the value |
|---|---|---|
| `store/_txn.py::_define_namespace` (inner fn of the bootstrap) | `f"DEFINE NAMESPACE IF NOT EXISTS {namespace}"` | config (`LoreConfig`), never a request |
| `store/_txn.py::_define_database` | `f"DEFINE DATABASE IF NOT EXISTS {database}"` | config |
| `surreal_schema.py::_define_table` / `_define_schemaless_table` / `_define_sequence` / `_define_relation_table` / `_plain_index` / `_unique_index` / `_hnsw_index` / `_fulltext_index` / `_analyzer_statement` / `_remove_field` | table/index/field/analyzer names | module constants + `dim`/`analyzer_name` from config |

**Verdict: interpolated, and correctly so. No caller-supplied value reaches any of them.** Flagged
for completeness because the sweep must be honest about *every* interpolation, not only the ones
that would embarrass a docstring.

### Class 5 — a caller QUERY-TEXT value reaches a predicate. Verdict: **BOUND (tokens are params)**, ×2

`store/surreal.py::_build_fulltext_predicate` (via `hybrid_search`) and
`memory/local.py::_hybrid_search`: the analysed tokens of the user's query text become an OR-chain,
but each token is a **bound `$param`**, and the chain length is clamped
(`_MAX_QUERY_TOKENS`, derived from `_MAX_FULLTEXT_OR_CLAUSES`). `store/surreal.py::_build_where`
additionally **allowlists every filter KEY** against `_ALLOWED_FILTER_KEYS` before building any
clause — docstring: *"an unknown/hostile key raises … and never reaches a query — the SurrealQL
statement-injection defense. Values are always bound as parameters (safe as data, even when
hostile)."* **Bound.**

### Class 6 — identity → RECORD ID. Verdict: **HASHED, never inlined**, ×2

- `agents.py::AgentRegistry._agent_id(session, name)` → `uuid5(NAMESPACE_URL, f"lore://agent/{session}/{name}").hex`
- `briefs.py::BriefLedger._brief_id(name, version)` → the same recipe for `lore://brief/{name}/{version}`

The identity text is consumed by `uuid5`; only the 32-hex digest reaches a `RecordID`, which is
then **bound** (`type::record('agent', $row_id)` / `RecordID(AGENT_TABLE, agent_id)`). The identity
never appears in query text.

### The bottom line for #219

**Across 56 query-composition sites in the entire production package, the count of sites where an
IDENTITY (agent name, session, brief name, recipient name) is interpolated into query text is
ZERO.** Every identity-bearing `WHERE` in the four comms modules binds a parameter:
`agents.py::_select_rows_by_name` (`WHERE name = $…`), `agents.py::fleet`/`roster`
(`WHERE session = $…`), `briefs.py` (nine sites: `WHERE name = $…` ×6, `WHERE in = $…`,
`WHERE in IN $…`, `WHERE name IN $…`, `WHERE next = $…`), `messages.py` (seven sites:
`WHERE out = $agent AND seen_at IS NONE`, `WHERE out = $agent AND in IN $message_ids`,
`WHERE seq IN $seqs`, `WHERE question = true AND sender = $agent`, …).

**So #219 resolves in the NON-INVERTED direction: fix the prose (all four sites), and supply a real
reason for site 4's "never a config knob" ruling.** My sweep was run independently and only
afterwards compared with the 04a scout's §S7; the two agree on the four prose sites and on the
zero-inlined-identities verdict, and mine additionally enumerates the Class-3/4/5 residuals its
`inlin`-keyed prose grep structurally could not see.

---

# E. #247 — the message SENDER door

## E1 — where the sender identity comes from

**Two layers, and they differ. This is the whole finding.**

**Layer 1 — the TOOL path (`lore_comms action=send`): STORE-RESOLVED.**
`server.py::AppContext.comms` resolves the caller before dispatching to any handler:

```python
agent_row: Agent | None = None
if spec.requires_registration:
    ...
    agent_row = await self.agent_registry.touch(agent, session=session, status=..., note=...)
    # raises _UnknownAgentError -> enriched teaching error
return await spec.handler(self, agent=agent, session=session, agent_row=agent_row, ...)
```

`server.py::AppContext._comms_send` then passes that row straight through:

```python
result = await self.message_ledger.send(
    sender=agent_row,
    session=session_scope, ...)
```

`agent_row` is an `Agent` value object read back from the `agent` table by
`AgentRegistry.touch` → `_resolve_row`, which raises `UnknownAgentError` for an unregistered name.
**So through the served tool, a bogus sender cannot reach the ledger.**

**Layer 2 — the LEDGER seam (`MessageLedger.send`): CALLER-SUPPLIED and UNVALIDATED.**
`messages.py::MessageLedger.send(self, *, sender: AgentRefLike, ...)`. Its validation sequence is,
in order: grade domain → body blank/over-cap → pointer caps → empty-recipient →
`await self._reject_unknown_recipients(recipients)` → dedupe → write. **`sender` appears in NONE
of them.** The docstring's own words: *"**EVERY recipient** is validated to exist in the ``agent``
table BEFORE any edge is written"* — recipients, not the sender.

The write itself (`messages.py::MessageLedger._send_fragment`) simply constructs the link:

```python
"sender_rec": RecordID(AGENT_TABLE, sender.id),
...
"CREATE type::record('{MESSAGE_TABLE}', $msg_id) CONTENT "
"{ seq: $minted_seq, session: $msg_session, thread: $thread, sender: $sender_rec, ... }"
```

`AgentRefLike` is a structural protocol (`.id` / `.name`) — **any object with an `id` string
satisfies it**, and `RecordID(AGENT_TABLE, <anything>)` is constructed unconditionally.

**MEASURED, not inferred — the door-build receipt from packet 04a's adversary**
(`docs/plans/v2/receipts/2026-07-27-packet04a/REPORT-adversary-04a.md`, row I13):

> | I13 | no stored identity names a non-existent agent | **GUARDED** to recipients + `publish`'s
> `agent_id`. **The message SENDER is an unguarded door.** | ⛔ door-build receipt: on the CORRECT
> reference build, `send(sender=_Ref(UNREGISTERED_AGENT_ID,…), recipients=[registered])`
> **SUCCEEDS** (`1 passed`). Same bad outcome, different door. Escalated. |

It has now been escalated **three times** and never ruled: adversary R8, builder E-2
(`REPORT-builder-04a.md`), cold audit R-8 (`REPORT-coldaudit-04a.md`, which says explicitly:
*"**Operator's call: fix now (one line — pass the sender into the same shared call) vs. defer with
a finding number and a named re-open trigger.** A third pass-forward with no ledger row would be a
can-kick."*). It now HAS a ledger row (#247), and the packet routes it to 04b's kickoff.

## E2 — what `message.sender` is

**A record LINK, with NO existence constraint.** `surreal_schema.py`, the message field spec tuple:

```python
("sender", f"record<{AGENT_TABLE}>", ""),
```

Third element is the constraint clause — **empty**. Emitted as
`DEFINE FIELD OVERWRITE sender ON message TYPE record<agent>` with no `ASSERT`.

The module comment above it confirms the intent (verbatim):

> ``sender`` is a real ``record<agent>`` link (a delivery reader can dot-traverse ``in.sender.name``)

Corroborating reads that depend on it being a link, not a string:
`messages.py::MessageLedger.drain` projects `in.sender.name AS sender_name` (a graph dereference —
a plain string could not be dotted), and `messages.py::MessageLedger.awaiting_answer` filters
`WHERE question = true AND sender = $agent` with `$agent = RecordID(AGENT_TABLE, agent_id)`.

There is also an index over it: `_unique_index`-family call
`_plain_index(MESSAGE_TABLE, f"{MESSAGE_TABLE}_sender_question", ("sender", "question"))`, whose
comment notes *"``sender`` is the selective prefix"*.

⚠ **`record<agent>` constrains the TABLE, not the EXISTENCE of the row.** A `RecordID("agent",
"does-not-exist")` is a perfectly well-typed `record<agent>`. That is the door.

## E3 — would 04a's `to`-edge `ENFORCED` already block a bogus sender?

**NO. This is INFERRED from the schema (I did not probe — read-only brief), and I say so plainly.**

The reasoning, stated so it can be checked:

- `ENFORCED` is a clause on a `TYPE RELATION` **table**, and store reference §4 (cited, not
  re-transcribed) records that it validates **BOTH ENDPOINTS** — i.e. the edge row's `in` and `out`.
- The emitted statement is `DEFINE TABLE OVERWRITE to TYPE RELATION IN message OUT agent ENFORCED
  SCHEMAFULL` (MEASURED by DDL generation, §A1). Its `in` is the **`message` record** and its `out`
  is the **`agent` record (the RECIPIENT)**.
- **`message.sender` is a FIELD ON the `message` row, not an endpoint of the `to` edge.** `ENFORCED`
  inspects the two endpoint columns of the edge; it has no reach into a field of the record one
  endpoint points at.
- So `ENFORCED` on `to` validates: the message exists (it does — minted in the same fragment, and
  packet 04a's P5 measured that same-transaction endpoints resolve), and each recipient exists
  (already independently guarded by `_reject_unknown_recipients`). **The sender is checked by
  neither.**

**Measured vs inferred, explicitly:**
- **MEASURED:** the emitted `to` DDL text (§A1); the `sender` field spec with an empty constraint
  (§E2); the validation sequence of `MessageLedger.send` containing no sender check (§E1); the
  04a adversary's door-build showing `send(sender=<unregistered>)` **succeeds** on a correct build.
- **INFERRED:** that `ENFORCED`'s reach is endpoints-only and therefore cannot cover a field of the
  `in` record. I did not probe 3.2.1 for this. The inference rests on the store reference's §4 and
  on the door-build receipt above, which is itself an empirical demonstration that whatever
  `ENFORCED` does today, it does **not** stop a bogus sender — the send SUCCEEDED with `to` already
  `ENFORCED`. **That receipt is the strongest available evidence and it points the same way.**

**Corollary the packet already states for the recipient side applies verbatim to the sender:**
even if `ENFORCED` did reach it, it could not TEACH — the seam's error hygiene (ledger #31)
replaces the engine's message with *"statement N of M was rejected (unspecified rejection); see the
server log"*. **An app-level check is the only layer that can name the bad sender.**

**And the fix already has a home — it is a one-line reuse, not a new mechanism.**
`loremaster/loremaster/agent_existence.py::reject_unknown_agents(query, agents, *, error)` is the
SHARED policy 04a extracted precisely so `MessageLedger` and `BriefLedger` would not each own a
copy. Its docstring: *"The DECISION — which ids are unknown — is made HERE and only here."* It
takes a **sequence**, so the sender can simply join the recipients in the existing call, or be
passed in its own call with a `SenderNotRegisteredError` vocabulary. `messages.py::
MessageLedger._reject_unknown_recipients` is the pattern (it decides nothing; it only supplies the
error class). **A hand-rolled sender check would be exactly the copy-#2 that repo law forbids.**

⚠ **Removed-behaviour note if it is closed here:** `send`'s docstring lists its `Raises:` and would
gain one; and `_reject_unknown_recipients`' name/docstring would become inaccurate (it says
"recipients") — the #219 class, one packet later, in the fix for #247.

## E4 — does the sender path appear in 04b's likely diff?

**NO — no function overlap. MEASURED by enumerating 04b's four workstreams against the sender
path's three symbols.**

The sender path is exactly: `server.py::AppContext._comms_send` → `messages.py::MessageLedger.send`
→ `messages.py::MessageLedger._send_fragment` (+ the `sender` field spec in
`surreal_schema.py::_MESSAGE_FIELD_SPECS`).

| 04b workstream | symbols it must touch | touches the sender path? |
|---|---|---|
| `blocks` DAG edge | `surreal_schema.py::_define_relation_table` (new 5th call) + `_task_statements`; `tasks.py::create_task`, `create_many`, `_new_task_content`, `supersede_task`; a new transitive read; `server.py::AppContext.tasks` renders | **no** |
| fleet unread/directive columns | `server.py::_comms_fleet`, `_render_comms_fleet`, `_render_comms_fleet_row`; a **new** batch-count method in `messages.py`; possibly `agents.py::roster` | **no** — same MODULE (`messages.py`), different region; `send`/`_send_fragment` are untouched |
| `_comms_footer` | `server.py::AppContext.tasks`, `claim_task`, `findings` + a new `_comms_footer` helper | **no** |
| #219 prose | `server.py::_validate_comms_charset`, `_validate_comms_identities`; `agents.py` module comment | **no** |

**The only contact is a shared FILE (`messages.py`), never a shared function.** By the packet's own
stated ownership test (*"do the blocks/fleet/footer/#219 changes touch these same functions?"*),
**#247 is NOT owned by 04b's diff.**

**However — three arguments cut the other way, and the operator should weigh them:**

1. **The packet's own EXIT criterion names it.** *"a bogus-recipient publish/send teaches instead of
   dangling"*. The recipient half is done; a reader of that sentence in six months will reasonably
   read "send" as covering the send verb, sender included.
2. **It is a one-line reuse of a shared function that already exists** (§E3), plus the packet's own
   standard fixture trio (negative + positive control + no-row-written assertion) — the same three
   pins the packet already mandates for `publish`/`send`. The marginal cost is small **because 04a
   built the mechanism**.
3. **Three prior escalations, zero rulings.** Repo law (`Don't kick the can`) says a known defect
   in granted scope gets fixed in the session that finds it; deferral is legitimate only as
   measure-then-tune, out-of-authority, or capacity exhaustion — and this is shape 2
   (out-of-authority), which requires the fork be put to the operator **NOW with a recommendation**,
   not passed forward again.

**My recommendation: close it in 04b.** Not because it is in the diff — it is not — but because
the alternative is a fourth pass-forward of a measured, one-line-fixable hole whose mechanism is
already built and already tested, and because the packet's Exit sentence will otherwise ship
claiming more than it delivers (the #219 class). If the operator prefers to route it to 05, the
packet says the requirement is *"an operator-visible Log line — never silently"*, and the Exit
sentence should be narrowed to say **recipient** explicitly.

---

# F. FLAGS — everything I noticed, in priority order

Per scope law: I surface all of these; the operator decides. None is fixed.

1. **⛔ C4 — the footer cannot be built as specified.** The three tools carry no caller identity.
   Three ways out, none in the packet, all with real cost. **Decide before briefing a builder.**
2. **⚠ A1-FLAG — the packet's #105 table is STALE**: `briefed` IS `ENFORCED` (04a landed it,
   MEASURED by DDL generation). Only `refers`/`answers_to` remain, and `INDEX.md` routes those to
   **packet 43**. Building to the packet's table re-solves a solved problem — the exact mistake the
   packet's own text warns it made one revision earlier.
3. **⚠ A2-FLAG 1 — `create_task` is NOT transactional** (a bare `_query`, not `_apply`). "Mirror the
   edge inside the existing write txn" has no referent for it. Converting it is a real change on a
   live verb.
4. **⚠ A2-FLAG 4 — `ENFORCED`-from-birth on `blocks` changes `lore_tasks action=create` behaviour**:
   today a `blocked_by` naming a non-existent task creates an unclaimable task; after the flip the
   whole CREATE rolls back. Same shape 04a measured for `briefed`. Needs the app-level teach layer.
5. **⚠ B3 — two readings of "unacked directive"**, with different symbols and different code.
   Recommendation in §B3; the operator rules.
6. **⚠ C2-FORK — `resolve_many`/`acknowledge_many` are best-effort**, so "actually wrote" is
   per-ITEM. An all-failed batch writes nothing. Recommendation in §C2.
7. **⚠ C3-FLAG — mypy cannot catch a `Rendered` appended to a `str`** (`Rendered` subclasses `str`).
   All four render-safety instruments are blind to it. The packet's mandated mutation proof (footer
   text → 3 REDs) will not detect a wrong type choice; that needs its own pin.
8. **⚠ C1-FLAG — "~17 return points" is 15** (8 + 1 + 6). Collapsing also makes both
   `# noqa: PLR0911` suppressions deletable — a free ruff-visible receipt that the refactor landed.
9. **⚠ B2/#183 — `drain`'s pending read is unbounded and selects full BODIES** to `len()` them.
   A naive fleet column multiplies that by up to 200. Needs a grouped, projection-narrow aggregate.
10. **⚠ D1-FLAG — #219 has FOUR prose sites, not two**, and site 4 (`agents.py`, above
    `AGENT_NAME_PATTERN`) derives a RULING ("never a config knob") from the false premise. Fixing
    the prose without replacing the reason leaves a rule standing on nothing.
11. **⚠ D2 Class-3 residual — a `ONE IMPLEMENTATION` smell.** Three hand-rolled clones of the same
    positive-int limit guard (`findings.query`, `findings.filed_since`, `tasks.updated_since`), and
    the comment justifying literal-`LIMIT` interpolation (*"SurrealQL's LIMIT wants a literal count,
    not a bound param here"*) is **contradicted by `store/surreal.py::scroll`**, which binds
    `LIMIT $limit` successfully. One of the two is wrong about the engine. Not an identity, so it
    does not invert #219 — but it is #219's own class (prose that contradicts behaviour), in the
    packet whose job is fixing #219.
12. **⚠ A3 — `_render_claim_result`'s blocked branch renders `blocked_by` ids UNSANITISED**
    (`f"blocked_by {task.blocked_by} unresolved"`). Its own docstring flags this as a known
    residual "for the PKT-03 tree-wide sweep". Normally ledger-minted `uuid4` hex — but
    `create_many`'s pass-through (`key_to_id.get(ref, ref)`) lets an arbitrary caller string reach
    it. 04b touches this render's neighbourhood (the footer collapse in `claim_task`), so it is
    cheap to fix while there — **but it is outside the packet's named scope, so I am flagging, not
    proposing.**
13. **⚠ A4 — no acyclicity guard over persisted task ids.** Only `create_many`'s batch-local temp
    keys are checked. The packet's *"invariant tests pin edge≡blocked_by + acyclicity"* implies a
    guard that does not exist today for cross-call cycles — that is a NEW capability, not a mirror
    of an existing one, and it is a DESIGN question (what happens on a cycle: reject the create?
    accept and mark unclaimable? detect at read time?). Per repo law, a property to INVENT does not
    go to a builder as "figure out the general form".
14. **⚠ A2-FLAG 2 — `supersede_task` drops `blocked_by`** (successor is born unblocked). Spec-silent
    whether the mirrored edge should follow. Needs an inventory line, not a silent choice.
15. **⚠ B4 trap — a fleet-HEADER unread aggregate must NOT be summed from the per-row cells** (those
    cover only the ≤200 displayed rows). The existing header derives every segment from
    `roster().status_counts` for exactly this reason.

---

# G. TOOL HONESTY

- **lore was first choice and was used** for: index-currency check (`lore_index()` — `last_sync`
  age 456 s, root `/workspace` on branch `feat/surreal-unification` @ `c4d…` matching my `HEAD`, so
  graph answers are current for this tree), definition/span reads (`lore_read` for
  `surreal_schema.py`, `tasks.py`), and the findings ledger (`lore_findings action=query`).
- **I fell back to grep/AST, and here is why, per case:**
  - **§D2 (the whole residual sweep)** — *"is this VALUE interpolated into this STRING"* is a
    non-symbol textual seam (dogfood protocol case b). lore's graph is symbol-granular; it cannot
    answer it. AST was the right instrument and I wrote a purpose-built one.
  - **§A1 / §A4 (does `blocks` / an acyclicity check exist anywhere)** — an EXHAUSTIVENESS question
    where one missed site changes the answer from "absent" to "present" (case a). Bare, anchor-free
    patterns, per repo law.
  - **§C1 (exact return counts)** — a structural count over a specific function body; AST is exact
    where a graph query is not.
  - **§A1 ENFORCED verdict** — I did not read the call sites and infer; I **generated the DDL** and
    read the emitted statements, because the recipe is not the cake.
- **⚠ FRICTION, reportable — `lore_findings action=get` cannot resolve a finding NUMBER passed as
  a STRING.** Reproduced twice and characterised with a positive control (measured 2026-07-27):
  - `action=get id_or_number='219'` → `Error: no finding addressed by '219'`
  - `action=get id_or_number='247'` → `Error: no finding addressed by '247'`
  - **positive control** — `action=query area=comms limit=50` returns
    `[#219 acknowledged] _validate_comms_charset's docstring AND its served error message are
    FALSE …`, so the row exists and IS numbered 219;
  - **second positive control** — `action=get id_or_number='4f6d6bb07cc448c6a93b11bffb386265'`
    (the same finding's UUID) **succeeds** and serves the full body.
  So the `get` path works; only the number-as-string lane misses. Consistent with the string form
  not being coerced into the int number lane (`server.py::_require_finding_ref` →
  `FindingLedger.get`'s ref resolution). ⚠ The cost is real for an agent: the served error
  (`no finding addressed by '219'`) reads as *"that finding does not exist"* when it does — a
  teaching surface that is FALSE, i.e. #219's own class, in the tool being used to read #219.
  **I did not file it via `lore_findings action=report`** because my brief makes this report my
  only writable artifact and filing is a write to a shared ledger — **flagging for the lead to
  file**: area `lore_findings`, category `bug`, kind `friction`.
  (I also observed `action=query status='open' limit=200` → `(no findings matched this query)`
  while `status='acknowledged'` returns rows normally. **I could NOT establish whether that is a
  defect or simply a ledger with zero open rows**, so I make no claim about it — noting it only so
  the lead knows the observation exists.)
- **Relaying #219's own body, because it constrains the fix** (read via the UUID above):
  it says explicitly **"⚠ DO NOT 'FIX' IT BY DELETING THE GUARD … What is false is the RATIONALE,
  not the necessity"**, and names the replacement rationale: *"identity integrity: names must be
  unambiguous and comparable, and must not carry invisible characters that make two distinct
  identities render identically"*. It also states the exact residual my §D2 was sent to close:
  *"Whether any OTHER call path inlines an identity was not swept … if some path DOES inline, the
  message is right and the code is wrong, which is … inverts the fix."* **§D2 closes it: nothing
  inlines. The fix does NOT invert.**
- **I did not run the test suite and did not connect to either SurrealDB store**, per brief.
