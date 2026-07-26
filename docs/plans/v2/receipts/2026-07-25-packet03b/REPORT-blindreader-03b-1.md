brief-base v6 read

# REPORT — blindreader-03b-1 · contract-blind diff read of `f3971bd..84756b6`

## SUMMARY BLOCK

- `brief-base v6 read` · store reference `docs/reference/surrealdb-31-capabilities.md` read (§0, §1.1–§1.7, §2, §4, §5, §6) — CITED, not re-transcribed.
- state: **done** (read-only; no code edited, no pytest run, no container touched, no git state mutated).
- deviations: (1) lore MCP tools were loaded via ToolSearch but I did **not** use them — every question I had was a *diff*-scoped or *textual/exhaustiveness* question (deleted-line enumeration, "who calls this", constant values, dependency source), so I used `git diff`/`grep`/AST over the tree and read the installed `mcp` package directly. Saying so out loud per CLAUDE.md's dogfood protocol §3(a)/(c). (2) I ran one standalone `anyio` probe (with a positive control) to settle a runtime-semantics claim the diff makes in a docstring — no repo code, no test suite; output pasted inline in D1.
- decisions-needed: **D1 (cancelled calls write no trace row) and D2 (drain's elision re-ask is wrong on peek / unachievable past the cap) are the two I would block on.** D7 (instructions teach a state machine nothing serves) is a ruling, not a bug I can settle.
- receipt pointers: DEFECTS §D1–D11 · QUESTIONS §Q1–Q9 · input-accounting table §"INPUT ACCOUNTING" · removed-behaviour inventory §"REMOVED-BEHAVIOUR INVENTORY" · error-path sweep §"ERROR-PATH SWEEP" · residuals §"RESIDUALS".
- All claims dated **2026-07-25, at `84756b6`**.

---

## (a) DEFECTS — substantiable from the code alone

Ranked by severity.

### D1 — A CANCELLED TOOL CALL WRITES NO TRACE ROW, AND THE DOCSTRING CLAIMS THE OPPOSITE

`TracingFastMCP.call_tool`'s class docstring states, verbatim:

> "The write sits in `finally`, which is LOAD-BEARING and not style: an awaited write there COMPLETES when the surrounding task is cancelled, so the struggling-session population is recorded rather than silently dropped."

That is the entire justification for the `ok` latch's design (`ok` starts False, no `except` arm, "`CancelledError` … is the door it misses", "a timed-out drain counted as a performed one would corrupt the very numerator this instrument exists to produce").

**It does not hold under the cancellation mechanism MCP actually uses.**

1. MCP cancels a request through an **anyio cancel scope**: `RequestResponder.cancel` (`mcp/shared/session.py`) does `self._cancel_scope.cancel()`.
2. `FastMCP.call_tool` — and therefore `TracingFastMCP.call_tool` and its `finally` — executes *inside* that scope: `_setup_handlers` registers the bound `self.call_tool` with the lowlevel server (`mcp/server/fastmcp/server.py`, `_setup_handlers` → `self._mcp_server.call_tool(validate_input=False)(self.call_tool)`), and the lowlevel server runs `await handler(req)` inside the responder's scope.
3. anyio cancel scopes are **level-triggered**: once cancelled, *every subsequent await inside the scope* raises `CancelledError` immediately. A `finally` block is not exempt. There is no `anyio.CancelScope(shield=True)` anywhere in the diff.

Probe (standalone, not the repo suite), **with the positive control this repo's law requires**:

```
# cancelled leg — the finally's await, inside a cancelled anyio scope
TRACE WRITE ABORTED: CancelledError
--- positive control (uncancelled) ---
TRACE WRITE COMPLETED
```

The control proves the probe can observe a completed write, so the aborted result is a real negative and not a blind instrument.

Consequences, all silent:

- The cancellation/timeout population — precisely what `ok=False` exists to measure — produces **no row at all**, not an `ok=False` row. Packet 06's numerator is not merely wrong, it is missing the denominator's failure half.
- The `CancelledError` raised out of `_record_tool_trace` is a `BaseException`, so `except Exception:` does **not** catch it and `logger.exception("trace.emit.failed")` never fires. Nothing anywhere records that a trace was lost.
- That same `CancelledError`, raised from a `finally`, **replaces** whatever exception the tool was already unwinding.

Minimal fix shape (not mine to apply): wrap the emission in `with anyio.CancelScope(shield=True):`, with a bounded timeout so a shielded write cannot hang a cancelled request. Either that, or the docstring's claim must be struck and the `ok=False`-on-cancellation promise withdrawn.

*Honesty bound:* I verified (1)–(3) structurally from the installed `mcp` sources and demonstrated anyio's semantics in isolation. I did **not** drive a real cancelled tool call through the server (brief forbids suite runs), so the end-to-end reproduction is inferred from those three facts, not observed.

### D2 — `drain`'s ELISION RE-ASK IS WRONG ON A PEEK, AND UNACHIEVABLE WHEN THE REMAINDER EXCEEDS THE CAP

`AppContext._render_comms_drain` emits, outside the peek/non-peek branch:

```
"+{more} more unread — re-run with limit={next_limit}"   more=remainder, next_limit=remainder
```

**(a) On a peek it is arithmetically wrong.** The method's own docstring justifies using the remainder *because* "a non-peek drain stamps exactly the served window and stamped rows never re-serve". A peek stamps nothing (`MessageLedger.drain`, `if not peek and window:`), so the next drain re-reads `pending[:limit]` from the *start*. Peek 20 of 50 → the render says "+30 more unread — re-run with limit=30"; obeying it serves the same 20 again plus 10 new. The caller was told about 30 and can reach 10. The correct re-ask on a peek is `total_pending`, i.e. `shown + more` — the exact value the docstring rules out for the non-peek case.

**(b) Past the cap it names a limit that silently clamps.** `_comms_drain` does `display_limit = min(limit …, _MAX_DRAIN_LIMIT)` with `_MAX_DRAIN_LIMIT = 50`. With 200 pending and a 20-row window, the render says "re-run with limit=180" and the caller gets 50. The sibling precedent does exactly the opposite — `AppContext._render_comms_fleet` computes `next_limit = min(total, _MAX_FLEET_LIMIT)` and carries a second, cap-disclosing template for when the cap itself is what elides. `_MAX_DRAIN_LIMIT`'s own comment claims the mechanism is "never making the cap a dead end (the elision line's honest count is the re-ask)"; the count is honest, the re-ask is not.

Both are one-line fixes and both are served numbers, i.e. the trust-doctrine surface.

### D3 — A MULTI-RECIPIENT `send` NAMES ONLY THE FIRST BAD RECIPIENT; THE LEDGER'S "NAME EVERY UNKNOWN" GUARANTEE IS NOW UNREACHABLE

`AppContext._comms_send` resolves recipients in a Python loop, one `agent_registry.get_agent(name, …)` per name, and raises on the **first** failure — unknown (`_UnknownAgentError` → `_comms_enrich_unknown_agent`) or retired (the explicit `ValueError`). A caller sending to `["real", "typo1", "typo2"]` learns about `typo1` only, fixes it, and is rejected again.

`MessageLedger._reject_unknown_recipients` exists precisely to avoid that: its docstring says it raises "naming EVERY recipient id that is not a registered `agent` row … ONE query regardless of recipient count". By the time the dispatcher calls `send`, every recipient has already been individually resolved, so that method can now only fire on a race — its ergonomics are dead on the tool surface, and its query is a redundant round-trip on every send.

This is not a style point: the store reference §4 rejects `ENFORCED` as a *replacement* for the app-level check on exactly this ground — *"ONE bad endpoint per attempt … it does NOT replace an app-level check that names EVERY bad recipient BEFORE the write."* The new surface re-introduces the shape the reference says the app layer exists to avoid.

Secondary cost: N sequential store round-trips for N recipients, where the ledger already had a set-based one.

### D4 — A SOLO-AGENT BROADCAST FAILS WITH PROSE THAT BLAMES THE CALLER FOR A WELL-FORMED CALL

`_comms_send` with `to` omitted (or `[]`) resolves `roster(session=…).members` minus the sender. In a session whose only non-retired member is the sender, that is `[]`, and `MessageLedger.send` raises:

> "a send needs at least one recipient — the ledger never resolves a roster (broadcast is the dispatcher's concern), so an empty recipient set in session `'X'` is a caller error, not a broadcast"

The caller *did* broadcast, exactly as the tool schema instructs ("omit it (or pass []) to broadcast to every non-retired teammate in your session"). The error asserts the opposite of what happened and teaches a fix that does not exist. This is a first-boot / first-agent path, not an exotic one: the first agent to register in a session and broadcast hits it.

### D5 — `action=ack seqs=[]` PASSES THE REQUIRED-ARGUMENT GATE AND RENDERS A DEGENERATE RECEIPT

`AppContext.comms`'s required check is `if values.get(required_name) is None:` — an empty list is not `None`, so `seqs=[]` is accepted for an action whose schema says `seqs` is "REQUIRED". `MessageLedger.ack` honestly short-circuits (`if not requested: return MessageAckResult(entries=[], …)` — its docstring calls an empty list "nothing to do, reported honestly"), and `_render_comms_ack` then emits:

```
acked 0 of 0: 
```

— a dangling `": "` with an empty `render_join(", ", [])`. The same dangling separator appears on **every** call where nothing was acked (e.g. three already-acked seqs render `acked 0 of 3: ` followed by the `already acked:` line). A served line ending in a colon and nothing is exactly the shape an LLM consumer reads as truncation.

`to=[]` on `send` is the deliberate broadcast affordance and is documented; `seqs=[]` is not.

### D6 — THE `trace` TABLE INTRODUCES UNBOUNDED GROWTH **AND** CALLER-CONTROLLED CARDINALITY IN A SERVED AGGREGATE

Before this diff `trace` had zero writers in production — `git log -S"record_trace(" -- loremaster/loremaster/server.py` returns exactly one commit, `74863a7`, i.e. this packet. Three properties arrive together:

1. **No retention.** Nothing in `loremaster/loremaster/**` ever deletes a `trace` row (the only `TRACE_TABLE` references are the `CREATE` in `record_trace` and the `GROUP BY` in `trace_aggregates`). The table grows one row per tool call, forever.
2. **A full scan on a hot read.** `SurrealStore.trace_aggregates` is `SELECT … FROM trace GROUP BY tool` with **no `WHERE` and no index on `tool`**, and `AppContext._trace_summary` calls it on **every** `lore_index`. Its docstring calls it "ONE bounded `GROUP BY` aggregate" — the *result* is bounded (one row per tool); the *scan* is not, and it now grows without limit.
3. **The `tool` group key is caller-supplied.** An unknown tool name still reaches the seam: the lowlevel handler calls `func(tool_name, arguments)` unconditionally (`validate_input=False` for FastMCP), and `ToolManager.call_tool` raises `ToolError(f"Unknown tool: {name}")` *inside* `super().call_tool` — so the `finally` writes a row keyed on the bogus name. `TraceSummary.by_tool` is returned as **structured output with no display cap** (`lore_index` returns `IndexStatusSummary` directly). A client repeatedly calling `lore_serch` (typo) permanently adds a row to every future `lore_index` response.

(3) also violates the house rule that a served list is capped-and-counted — `by_tool` is the one list in this diff's blast radius with no cap.

### D7 — THE SERVED INSTRUCTIONS TEACH A "CONVERSATIONAL DEBT" STATE MACHINE THAT NO SURFACE EVER REPORTS

The new `_INSTRUCTIONS` paragraph — read by every agent, once, as strategy — says:

> "One thread carries ONE conversational debt: put separate questions on separate `q:<topic>` threads. If a partial reply cleared your thread, re-ask the unaddressed question: a new send with `set_status='input_required'` re-establishes the debt. A question clears only when a teammate's reply is delivered to you on that thread; your own follow-ups and self-notes never clear it."

Measured across `loremaster/loremaster/**`: **`MessageLedger.awaiting_answer` and `WaitingOnAnswer` have zero production consumers.** Nothing in `server.py` calls either. And `set_status` is documented, correctly, as *not* touching the status row — so `fleet`'s `input_required` "parked" segment does not surface it either. The only place the rule appears in-band is the one-shot `_render_comms_send` question line at send time.

So an agent is taught a debt state that (a) it can never query, (b) is never reported back to it or to its lead, and (c) no teammate can see. This is the packet-28-C1 class named in CLAUDE.md: *"three lines promising mechanisms that never run."*

Corroborating detail, same finding: the diff adds `message_sender_question` — a `(sender, question)` index whose stated purpose is "serves `awaiting_answer`'s questions read" — for a method with no caller. And the `messages.py` `−/+` hunk in this same diff is a *performance narrowing of that uncalled method*.

I cannot tell from the diff whether a later packet serves it. That is Q-material. What I can substantiate is that **the sentence is served now and the mechanism is not**.

### D8 — THE 2000-CHAR BODY CAP IS BYPASSABLE THROUGH `refs` / `thread` / `task_id`, AND THE SCHEMA TEACHES THE BYPASS

`message.body` carries a store-level `ASSERT string::len($value) <= MESSAGE_BODY_MAX_CHARS` (2000). Alongside it:

- `refs` is `array<string>` `DEFAULT []` — **no length assert, no count assert**.
- `thread` and `task_id` are plain/`option` strings — no length assert.
- `_comms_send` passes all three through untouched (only `to` is charset-validated).
- `_render_comms_drain_row` renders up to `_COVERAGE_NAMES_CAP` (= **5**) refs *verbatim* — `safe_str(ref)` collapses control characters but does **not truncate** — plus the thread/task cell.

So a sender capped at 2000 characters of `body` can deliver five arbitrarily long strings straight into a recipient's context. The served `refs` description makes the bypass the recommended pattern: *"Bodies are capped; the content lives in what you name here."* The cap is a per-token-cost control on a surface whose whole justification (`_MAX_DRAIN_LIMIT`'s comment) is bounding "the worst-case render at a size a consumer can still use".

(No render-safety hole here: `safe_str` = `sanitise_line(str(...))`, and `render_line` re-checks every value against `CONTROL_CHAR_PATTERN`, so a newline in a ref cannot forge a row — it would raise `RenderSafetyError` before it could. I checked that specifically; it is clean. The defect is *size*, not forgery.)

### D9 — TWO SILENT NO-OP RETURNS IN THE TRACE SEAM (#131's SHAPE)

`TracingFastMCP._record_tool_trace` has two `return` statements that emit nothing:

```python
except LookupError:
    return                      # no request context
...
store = getattr(app_context, "write_store", None)
if store is None:
    return                      # no store
```

Neither logs, counts, or is observable anywhere. The second is a **string-keyed reach into another object's attribute name**: rename `AppContext.write_store` and every trace disappears permanently, with mypy, ruff and every emission test still green (the tests drive the seam, not the attribute name). That is finding #131's exact shape — a swallowed absence whose only detector is a field somebody happens to look at.

Mitigating, and worth crediting: unlike #131 the field **is** rendered — `TraceSummary` reaches `lore_index` — and the new docstring says outright that "a long-lived deployment whose numbers stay flat is a SIGNAL (the emission is broken)". But that detector is *an agent reading a number*, not an instrument. A `logger.warning` on the `store is None` leg would cost one line, and an assertion that `lifespan_context` is an `AppContext` (rather than a `getattr` reach) would make the rename a type error.

### D10 — EVERY TOOL CALL NOW PAYS A SYNCHRONOUS STORE WRITE ON ITS OWN CRITICAL PATH

The emission is `await`ed inside `finally`, so it completes **before the tool's result reaches the caller**. `record_trace` → `SurrealStore._query` → the shared `run_query` / `retry_on_conflict` driver, which carries a retry floor, jitter and a wall-clock deadline (store reference §5). Therefore a degraded or contended store adds *the whole retry budget* to the latency of every served call, on every tool.

The class docstring's failure posture says "the tool call's outcome ALWAYS wins" — true of the returned **value**, not of the **latency**, and latency is what a coordination surface is judged on. The removed `record_trace` docstring described this as "the async fire-and-forget EMISSION"; the fire-and-forget half was dropped without a replacement or a note. Given D1 already argues the write must be shielded, the shield + a hard timeout would settle both.

### D11 — `drain` IS AT-MOST-ONCE WITH NO RECOVERY VERB

`MessageLedger.drain` stamps `seen_at` **before** the render is assembled and returned, and only `seen_at IS NONE` rows are ever served again. There is no "unread", "since", or "replay" verb in this packet. So any failure between the stamp and the caller actually receiving the bytes — transport drop, request cancellation (D1's mechanism), a raise in the render or in the composed skew block — **destroys those messages permanently**.

`peek=true` is the mitigation, but it is opt-in, the `_INSTRUCTIONS` block teaches the destructive form ("action=drain reads your inbox and marks what it serves"), and the peek path's own elision line is wrong (D2a). For a subsystem whose stated purpose is removing permanent message loss, the default read is lossy.

---

## (b) QUESTIONS THE SPEC MUST ANSWER

**Q1 — `trace.agent` is populated by exactly 1 of 15 tools.** `_TRACE_DECLARED_KEYS = ("agent", "session", "action")` harvests only arguments literally so named. An AST enumeration of every `@mcp.tool`-decorated function in `server.py` gives:

| declared key | tools declaring it |
|---|---|
| `agent` | `lore_comms` — **1 of 15** |
| `session` | `lore_comms` — 1 of 15 |
| `action` | `lore_tasks`, `lore_comms`, `lore_findings` — 3 of 15 |

The key-rule is honestly documented ("any current or FUTURE tool that declares `agent=` is captured and one that declares none is honestly NONE"). But the `(agent, ordinal)` index is justified as what "packet 06's per-agent decay curve reads", and on this reach that curve can only ever see `lore_comms` traffic — every `lore_search`, `lore_read`, `lore_map`, `lore_impact` records `agent = NONE`. Is packet 06's curve comms-only by design? If not, the enrichment does not reach the population it was built for, and `transport_session` (the intended later join key) is `None` under stdio and only present under streamable-http.

**Q2 — `directive_pending` and `stamped_seqs` are computed and discarded.** `MessageLedger.drain` computes `directive_pending` over the WHOLE pending set; `_render_comms_drain` derives its ACK REQUIRED trailer from the **window** only and never reads `directive_pending`. `stamped_seqs` is read by nothing. So an agent draining 20 of 200 with 30 elided directives sees an honest "+180 more unread" and **no indication that unacked directive debt exists past the window**. The window-scoping is argued in a comment ("an elided directive's seq would be unactionable without its context") — was suppressing the whole-set *count* also ruled, when the ledger already computes it?

**Q3 — `hit_count` / `token_cost` / `model` are now permanently NONE.** The ONE writer (`_record_tool_trace`) supplies none of them, and no served surface reads them. `record_trace`'s docstring still documents them as things "a caller" may supply. Deliberate for this packet, or a dropped requirement?

**Q4 — the ack receipt counts DISTINCT seqs.** `_render_comms_ack` builds `requested` as a `set`, so `seqs=[5,5,5]` renders `acked 1 of 1`. Documented as deliberate ("MEMBERSHIP, not multiplicity"), and the typed `MessageAckResult` keeps per-occurrence truth. But a consumer comparing `len(my_list)` to "of N" sees a mismatch with no explanation in-band. Ruled?

**Q5 — concurrent drains by the SAME agent double-serve.** `MessageLedger.drain` reads the pending set, then stamps with a `seen_at IS NONE` guard. Two concurrent drains both *render* the same rows; only one stamps. The rendered "drained N of M" of the loser describes rows it did not stamp. Acceptable, or does the surface need single-flight?

**Q6 — `trace` retention.** None exists (D6.1). Is a GC/rollup planned, or is unbounded growth accepted?

**Q7 — the "this table is empty exactly once — now" claim.** Both new index builds (`trace_agent_ordinal`, and `message_seq` / `message_sender_question`) are `DEFINE INDEX IF NOT EXISTS`, which per store reference §1.5 **builds, blocking**, at the first `ensure_ready` that carries them. The comments assert both tables are empty. I corroborated that structurally — `record_trace` has had no production caller until this commit, and `MessageLedger.ensure_ready()` is *wired by this diff*, so the `message`/`to` slice has never been applied by the deployed server. I did **not** read the production store to confirm. Does anyone want a read-only `SELECT count() FROM trace` against `lore-surreal :18500` before the deploy? It is the one instrument that closes the §1.6 blind spot for this change.

**Q8 — `thread` is not charset-validated while `agent`/`session`/`name`/`to` are.** `_validate_comms_identities` covers four identities on the ground that they "are inlined into live `WHERE` clauses". I traced `thread`: it is a **bound param** everywhere (`$thread` in `_send_fragment`, `$threads` in `awaiting_answer`), so I found no injection. Is the omission deliberate (thread is not an identity), or an oversight? Related: `thread`, `refs`, `note`, `task_id` carry no length bound at all (see D8).

**Q9 — the `messages.py` narrowing's equivalence rests on an unstated schema property.** The added conjuncts `AND in.thread IN $threads AND in.seq > $min_seq` are a true superset of the Python filter **only because `message.thread` is a required, non-null `string`** (`_MESSAGE_FIELD_SPECS`). The Python side maps an absent thread to `""` via `str(row.get("thread") or "")` and binds that same `""` into `$threads`; SurrealDB's `IN` would not match a stored `NONE`. If `thread` ever becomes `option<string>`, the bound silently drops NONE-threaded answers and the agent reads "waiting" forever — the *safe* direction (`awaiting_answer`'s own known-bound section says so), but a real divergence from the comment's "semantics-identical SUPERSET". Should that dependency be pinned? (Note it currently optimises a method with no caller — D7.)

---

## INPUT ACCOUNTING

Every input to every new/changed path, and its fate. **Silent** = a failure with no observable signal to anyone.

### `lore_comms action=send`

| input | fate |
|---|---|
| `agent`, `session`, `name` | charset-validated before any store touch → teaching reject. **Emitted/rejected-and-reported.** |
| each name in `to` | charset-validated (all of them, `_validate_comms_identities`); then resolved **one at a time** — first unknown or retired aborts. **Rejected-and-reported, but only the FIRST offender is named (D3).** |
| `to` omitted / `[]` | broadcast via `roster()` minus sender. Roster excludes retired (`AgentRegistry.roster`, `if agent.status != STATUS_RETIRED`) — matches the docstring. **Emitted.** Empty result → misleading reject (**D4**). |
| duplicate names in `to` | deduped by row id in `MessageLedger._dedupe_by_identity`, first-wins; count and names in the receipt derive from the deduped set. **Merged-and-reported** (the receipt shows the true `recipient_count`). |
| `body` blank / over 2000 | `MessageBodyError`, never truncated. **Rejected-and-reported.** |
| `grade` out of domain | `IllegalMessageGradeError` naming legal grades. **Rejected-and-reported.** |
| `set_status` ≠ `input_required` | dispatcher shape-reject naming the one legal value, **before** the heartbeat touch. **Rejected-and-reported.** Good. |
| `set_status = input_required` | sets `message.question = true`; rendered once in the send receipt; **thereafter observable by nothing** (**D7**). |
| `thread`, `task_id`, `refs` | stored verbatim, unvalidated, unbounded (**D8**). `refs` rendered capped-at-5-with-a-count on drain; `thread`/`task_id` rendered as the single `{context}` cell. |
| recipient names past `_COVERAGE_NAMES_CAP` | counted remainder derived from the true `recipient_count`, not the display window. **Merged-and-reported.** Correct. |
| the write itself | ONE `execute_transaction` (mint + CREATE + N×RELATE), all-or-nothing. **Emitted or rejected.** |

### `lore_comms action=drain`

| input | fate |
|---|---|
| `limit` < 1 | teaching reject citing the **action's own** cap. **Rejected-and-reported.** |
| `limit` > 50 | clamped silently at `min(…, _MAX_DRAIN_LIMIT)`; the tool schema discloses clamping. **Merged-and-disclosed** (schema-level). |
| config `comms.drain_limit` > 50 | also silently clamped; disclosed in the config docstring only. |
| each pending message inside the window | rendered (header + fenced body), stamped seen. **Emitted.** |
| each pending message **outside** the window | counted in `total_pending`, named by the elision line, left unstamped. **Reported** — but the re-ask value is wrong on peek and unachievable past 50 (**D2**). |
| an elided **directive** | its ack demand is **not** surfaced; `directive_pending` is computed and discarded (**Q2**). |
| a re-served acked row | listed under "re-served after ack", excluded from the ACK REQUIRED trailer. Correct. |
| a directive on a **peek** | trailer suppressed by design; peeked header teaches the re-run. Coherent. |
| brief-skew read failure | **no degraded fallback** — the whole drain fails loudly. Deliberate and, I think, right. |
| a served-but-undelivered window | **SILENT PERMANENT LOSS** — stamped before the render reaches the caller, no replay verb (**D11**). |

### `lore_comms action=ack`

| input | fate |
|---|---|
| `seqs` omitted / `None` | required-argument reject. **Rejected-and-reported.** |
| `seqs = []` | **accepted**; renders `acked 0 of 0: ` (**D5**). |
| each requested seq | the ledger walks the REQUEST (`_ack_entries`, quantifier law) so every seq gets a typed fate; the render groups them and **the coverage of the four outcomes is checked at import**, raising loudly if the ledger grows a fifth. **Emitted.** This is the best-guarded input path in the diff. |
| a seq repeated in one batch | ledger reports per occurrence; render dedupes within a group and counts distinct (**Q4**). |
| a seq in two groups | appears in both. Correct. |
| `note` when nothing was acked | explicitly *not* claimed as recorded — the guard is `note is not None and acked`. Correct and unusually careful. |

### The trace seam — every tool call

| input | fate |
|---|---|
| a normal dispatch | one row, `ok=True`. **Emitted.** |
| a raising dispatch | `ToolError` propagates out of `super().call_tool`; `ok` stays False; row written. **Emitted.** Verified: `Tool.run` re-raises as `ToolError`, it does not swallow. |
| a **cancelled** dispatch | **NO ROW. Silent.** (**D1**) |
| a dispatch with no request context | **NO ROW. Silent, unlogged.** (**D9**) |
| a dispatch when `write_store` is absent/renamed | **NO ROW. Silent, unlogged, permanently.** (**D9**) |
| a trace-write failure (`Exception`) | logged `trace.emit.failed`, caller unaffected. **Reported** (server-side). Correct posture. |
| a trace-write failure (`BaseException`, incl. `CancelledError`) | **not caught, not logged**, and it replaces the in-flight exception. **Silent.** |
| an unknown tool name | row written with the caller's arbitrary string as `tool` → unbounded served cardinality (**D6.3**). |
| arguments | digested via `sha256(json.dumps(sort_keys=True, default=str))`; empty dict digests to a real value (deliberate, and right — four tools take no arguments). Only the digest crosses. |
| a non-JSON-serialisable argument **key** | `json.dumps` raises `TypeError` (`default=` covers values, not keys) → caught by the outer `except Exception` → logged, row lost. **Reported.** Acceptable. |
| `agent`/`session`/`action` non-`str` | skipped by `isinstance(value, str)` — a future integer param cannot mint an identity. Correct. |
| `mcp-session-id` header | present under streamable-http (`ServerMessageMetadata(request_context=request)`), absent under stdio → honest `None`. |
| `ordinal` | minted store-side via `sequence::nextval("trace_seq")` inside the write. Gaps documented. No caller can supply one. Correct. |

---

## REMOVED-BEHAVIOUR INVENTORY

90 `-` lines. Built from the diff independently. Verdict per item.

| # | what the removed/changed code DID | verdict |
|---|---|---|
| 1 | `AppContext.comms`: four inline `_validate_comms_charset` calls (agent → session → name) | **preserved** — `_validate_comms_identities` performs the identical three in the identical order, then adds `to`. No guard lost. |
| 2 | limit-range reject text hardcoded `_MAX_FLEET_LIMIT` in both slots | **preserved-and-widened** — now `spec.limit_cap`. ⚠ The `else _MAX_FLEET_LIMIT` fallback is **currently unreachable**: the foreign-param loop rejects `limit` on any action whose `params` lack it, and every action that accepts `limit` sets `limit_cap`. Dead branch, harmless, but it is a fallback nobody can observe. |
| 3 | `_render_comms_heartbeat` built `lines = [heartbeat_line]`, appended skew lines, returned `render_compose(*lines)` | **preserved** — now `render_compose(heartbeat_line, *_render_comms_skew_lines(...))`. Same order, same templates, same cap behaviour. The extraction is real sharing (one assembly, two verbs), not routing. |
| 4 | `_TRACE_FIELD_SPECS`: `hit_count` **required** `int` | **dropped deliberately** (reason given: a generic seam cannot know a hit count; a fabricated `0` would make `trace_aggregates` lie). **But the store-level guarantee is gone**: nothing now prevents a writer omitting it, and the one writer always does (**Q3**). |
| 5 | `_TRACE_FIELD_SPECS`: `session` **required** `string` | same as #4. Every row is now session-less unless `lore_comms` declared one (**Q1**). |
| 6 | `record_trace(hit_count: int, session: str)` required params | **dropped deliberately**, same reason. Widening is migration-safe: `int → option<int>` and `string → option<string>` are widenings, `_define_field` emits `OVERWRITE` (store reference §1.1), and existing values stay conformant, so no row is write-poisoned (§1.4). |
| 7 | `record_trace`'s two explicit `if token_cost is not None` / `if model is not None` blocks | **preserved-and-generalised** into one loop over eight `(field, value)` pairs. Same omit-means-NONE semantics; no column can now be forgotten by pattern. |
| 8 | `CREATE trace CONTENT $content` (payload only) | **preserved**, wrapped in `object::extend($content, {ordinal: nextval})` — the only shape that composes a bound payload with a store-side mint (store reference §2: `CONTENT` composes with neither `SET` nor `MERGE`). Correct idiom, correctly cited. |
| 9 | `_trace_statements` emitted table + fields only | **preserved**, plus a sequence (`IF NOT EXISTS`, per §1.1's SEQUENCE row — a bare DEFINE is a boot crash) and a **plain** index (`IF NOT EXISTS`, per §1.1's INDEX row — `OVERWRITE` would rebuild and can hard-fail `ensure_ready`). Both clause choices are the ones the reference mandates. |
| 10 | `TraceSummary` docstring: "which is EVERY boot today, since no caller yet wires the emission" | **correctly retired** — the statement was true at `f3971bd` and false at `84756b6`. Replaced with a claim that is now true. This is the diff doing the prose-follows-code discipline properly. |
| 11 | `mcp: FastMCP = FastMCP(...)` | **replaced** by `TracingFastMCP(...)`. Behaviour added, nothing lost; `_setup_handlers` binding makes the override wire-path by construction. |
| 12 | `_COMMS_ACTIONS` comment "exactly six in C1; send/drain/ack/await/story are C2/C3 growth points" | **correctly retired** — three graduated, `await`/`story` remain named as growth points. |
| 13 | `awaiting_answer`'s unbounded deliveries read (`WHERE out = $agent AND in.sender != $agent`) | **narrowed**. The Python filter below is byte-identical and unchanged, which is what keeps the two in agreement — but the equivalence depends on `message.thread` being non-nullable (**Q9**). No behaviour lost on today's schema. |
| 14 | Tool-description sentences for `task_id` / `note` / `body` / `limit` / the action list | **preserved-and-extended** — every prior clause survives verbatim inside the widened text; `body` and `limit` now interpolate live constants (`_MESSAGE_BODY_MAX_CHARS`, `_MAX_FLEET_LIMIT`, `_MAX_DRAIN_LIMIT`) instead of restating them. This is the derived-prose law applied correctly. |
| 15 | `from mcp.types import ToolAnnotations` | **preserved**, widened to `ContentBlock, ToolAnnotations`. |
| 16 | `from loremaster.config import WATCH_LIVE, WATCH_STATIC, LoreConfig, load_config` (one line) | **preserved**, split so `DEFAULT_COMMS_DRAIN_LIMIT` can be re-exported without redeclaration. No symbol lost. |
| 17 | "PKT-28 C1: the two comms ledgers each own their OWN connection too" + the two `close()` calls | **preserved-and-extended** — `message_ledger.close()` added to the same ordered unwind. |

**Nothing in the −91 is a guard I can show was silently lost.** The two real subtractions (#4, #5) are required→optional store constraints, both argued, both migration-safe. The removed-behaviour risk in this diff is concentrated in #4/#5's *consequence* (Q3), not in the deletions themselves.

---

## ERROR-PATH SWEEP

Every `except` / suppress / default-on-failure in the diff, with a verdict on "would anyone ever KNOW?".

| site | shape | would anyone know? |
|---|---|---|
| `TracingFastMCP.call_tool` `except Exception: logger.exception("trace.emit.failed", extra={"tool": name})` | catch-and-log, caller unaffected | **YES** — server log. Correct posture, and the narrow carve-out from write-paths-fail-loud is argued rather than assumed. |
| the same `except Exception` vs a `BaseException` from the write | **not caught** | **NO** — and it replaces the in-flight exception (**D1**). |
| `_record_tool_trace` `except LookupError: return` | silent no-op | **NO** log; only a flat count in `lore_index` (**D9**). |
| `_record_tool_trace` `if store is None: return` | silent no-op, string-keyed `getattr` | **NO** (**D9**) — and survives a rename with every gate green. |
| `_comms_brief_skew_lines` `except _UnknownBriefError: head_version = None; acked_version = None` | narrows to "no standing brief exists yet" | **Acceptable.** The exception type is specific and the `None`/`None` pair is then *only* used by an `is not None` guard that suppresses the skew line — a first-boot state, not a swallowed failure. Not #131's shape. |
| `_comms_send`'s `except _UnknownAgentError` → enriched re-raise `from error` | re-raise with roster context | **YES** — loud and teaching. But only for the first offender (**D3**). |
| `_render_comms_ack`'s `if group is None: raise RuntimeError` + the import-time `_ACK_OUTCOME_ORDER` coverage check | fail-loud on an unmapped outcome | **YES** — both. This is the diff's strongest instrument: a fifth `AckOutcome` is an import-time crash, not a seq that silently vanishes. |
| `MessageLedger.drain`'s `stamped_seqs` assumed-stamped | not an except, but an unverified assumption (a racing drain may have stamped first) | **N/A to the served surface** — `stamped_seqs` is consumed by nothing (Q2). Flagging so it is not later trusted. |
| `_trace_params_hash`'s `default=str` | keeps an unserialisable **value** from taking the dispatch down | **YES**, indirectly — a bad *key* still raises and is logged by the outer handler. |

No `contextlib.suppress` and no bare `except:` anywhere in the diff.

---

## THE SCHEMA CHANGE — does it MIGRATE, or only work on a virgin store?

Checked against the store reference before forming a view, per this repo's #107 law.

- **Widened columns** (`hit_count int → option<int>`, `session string → option<string>`): `_define_field` emits `DEFINE FIELD OVERWRITE` (§1.1 FIELD row), so the definition **lands on a live store** — this is not #107's shape. Both are *widenings*, so existing `int`/`string` values remain conformant and no row is write-poisoned (§1.4's TYPE-change row applies to narrowing/incompatible changes; these are neither).
- **Five new columns**, all `option<>` — exactly §1.4's mandate for a new field on a possibly-populated table ("a required one poisons every existing row and a DEFAULT does not rescue it"). Correct, and the comment cites the rule rather than re-deriving it.
- **`DEFINE SEQUENCE IF NOT EXISTS trace_seq`** — §1.1's SEQUENCE row (a bare DEFINE raises on the every-boot re-apply → boot crash). Correct. Residual per §1.1/#146: a future `BATCH`/`START` change would never migrate. Not exercised here.
- **`DEFINE INDEX IF NOT EXISTS`** for all three new indexes — §1.1's INDEX row (`OVERWRITE` rebuilds over every row and can hard-fail `ensure_ready` at boot). Correct clause. The **build cost** is the live question: §1.5 — a define *builds*, blocking. The code's answer is "this table is empty exactly once — now", which I corroborated structurally but did not verify against the production store (**Q7**).
- **`SELECT *` vs projection**: every new `option<>` column means a reader must not assume presence (§2's `SELECT *` corollary). The only reader of these columns is `trace_aggregates`, which uses an explicit projection and reads none of them. Clean today; a landmine for the packet-06 reader.

**Verdict: the schema half of this diff is the part I have the fewest reservations about.** It reads like it was written with the reference open. My one unclosed item is Q7.

---

## CONCURRENCY

- **`trace.ordinal`**: `sequence::nextval("trace_seq")` inside a single `CREATE`, riding `_query` → `run_query` → `retry_on_conflict`. Store reference §5 measures `nextval` contention-free to 32-way and zero-conflict at 16-way when composed with a `CREATE`. Gaps are real and the comment says so, twice, and calls it an ordering key rather than a count — correct.
- **ONE global sequence, not one per agent**: the stated reason (global interleaving is the signal; a per-agent counter destroys it) is coherent, and it avoids a third mint policy competing with `finding_counter`/`brief_counter` (#102's clone defect). This is the diff obeying ONE IMPLEMENTATION correctly.
- **Concurrent `record_trace`**: many in-flight tool calls share one WS connection; §3 records that one connection multiplexes concurrent `query()` safely (uuid-keyed futures). Fine.
- **`send`**: mint + CREATE + N×RELATE in one `execute_transaction`; §5 measures the composed shape at 16-way × 20 with zero conflicts. Contention lives on the per-recipient CAS stamp, not the mint. Fine.
- **`ack`**: one guarded `UPDATE … WHERE acked_at IS NONE`, so losers write nothing and report the **stored** stamp. Every racer observes one `acked_at`. Fine.
- **`drain`**: read-then-stamp with a `seen_at IS NONE` guard. Two concurrent drains by the same agent **both render** the same rows (**Q5**).

---

## RESIDUALS — individual verdict per row, no wholesale classification

1. `else _MAX_FLEET_LIMIT` in the limit-range reject — **unreachable today** (see inventory #2). Harmless; note it so nobody "fixes" the wrong branch.
2. `_render_comms_drain`'s `del agent_name, limit` — two parameters accepted and discarded, documented as future-proofing. **Accepted**; but `limit` is the parameter the elision line would need to clamp against, so the discard is adjacent to D2.
3. `MessageDrainResult.stamped_seqs` — **computed, never consumed.** Also over-reports under a racing drain (it lists the whole window regardless of what the guarded UPDATE actually stamped). Do not let a later packet trust it without a fix.
4. `MessageDrainResult.directive_pending` — **computed, never consumed** (Q2).
5. `MessageLedger._reject_unknown_recipients` — **effectively unreachable** from the tool surface (D3); a redundant round-trip per send.
6. `MessageLedger.awaiting_answer` + `WaitingOnAnswer` — **zero production consumers** (D7), yet optimised by this diff and indexed by this diff.
7. `grade` field description renders `sorted(_MESSAGE_GRADES)` as `['directive', 'signal']` — Python list syntax in served prose. **Cosmetic**, but it is derived-from-typed-state, which is the property that matters. No action.
8. `thread=""` is storable (no non-blank check) and renders as `(thread )` in a drain row, since `"" != session`. **Cosmetic**, low likelihood.
9. `refs` entries pass through `safe_str`, so a newline in a ref cannot forge a row — `render_line`'s runtime `CONTROL_CHAR_PATTERN` check is the backstop. **Verified clean**; I chased this specifically because refs looked unsanitised at first read (`safe_str` rather than `sanitise_line`) and it is not — `safe_str` *is* `sanitise_line(str(...))`.
10. `render_fenced(entry.body)` sizes the fence past any embedded backtick run, so a body cannot escape its fence. **Verified clean.**
11. `_INSTRUCTIONS` never mentions `peek`, while the tool schema does. **Acceptable** — the instructions are the read-once strategy block; recovery moves ride the responses.
12. `lore_index`'s own trace row is written after `_trace_summary` reads, so a served total never counts the call serving it. **Honest**, worth knowing before someone calls it an off-by-one.
13. `trace_aggregates`'s docstring calls itself "ONE bounded `GROUP BY` aggregate over the whole `trace` table" — the *result* is bounded, the *scan* is not. **Mild over-claim**, now load-bearing because of D6.
14. `TracingFastMCP` reaches `lifespan_context` and `write_store` by `getattr` string name rather than by type. **Fragile** (D9); an `isinstance(app_context, AppContext)` narrowing would make a rename a type error instead of silence.
15. `_TRACE_DECLARED_KEYS` deliberately excludes `owner`/`actor`/`created_by` with a stated reason (two identity vocabularies in one column). **Correct call**, well argued — recording it so a later packet does not "helpfully" add them.

---

## WHAT I DID NOT LOOK AT

Per the brief's withheld list: no test file, no test name, no docstring under `loremaster/tests/`; no `03b-*`/`03a-2-*` design doc; no `REPORT-*.md` anywhere; no pytest run; nothing under `/home/ejprice/scratch/`; no `pkt03b-tainted-corpus`. Every enumeration above was built from the diff, the changed files' current and prior content, other production modules, the installed `mcp` package, and `docs/reference/surrealdb-31-capabilities.md`.
