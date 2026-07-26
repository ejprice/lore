# REPORT-blindreader-03b-2 — contract-blind diff read of the two 03b remediation waves

brief-base v6 read

> **Scope + date.** Contract-blind diff read of `git diff 84756b6..HEAD -- loremaster/loremaster/`
> (5 production files), performed **2026-07-25** at `HEAD = 0a0b38d` on branch
> `feat/surreal-unification`. **I read no tests, no design canon, no `REPORT-*.md`, and ran no
> pytest** — by brief. Every claim below is derived from production source at that SHA plus
> `docs/reference/surrealdb-31-capabilities.md`. Where a verdict needs the spec or a live store
> read, it is filed as a QUESTION, not a defect.

---

## SUMMARY BLOCK

- brief-base v6 read
- state: **done**
- deviations: none. (Tool honesty: I used `git`/`grep`/`Read` rather than the lore MCP for the
  whole read — see §0. The lore tools were loaded and available; grep was the correct instrument
  for a diff-shaped, textual-seam question, and I say so here as required.)
- decisions-needed:
  - **D1 is a live consumer loop** — a peek drain past 50 pending serves an instruction that
    cannot reach the tail. Fix now or ledger with a re-open trigger.
  - **Q1 gates the deploy** — the `trace_ts` "free window" is a claim about the PRODUCTION store,
    not about the code. Somebody must `SELECT count() FROM trace` on `:18500` before this ships.
    I am prohibited from container ops; I did not run it.
  - **Q2** — the same free-window question for the five new narrowing ASSERTs (`to.ack_note` is
    the sharp one: `to` edges are UPDATEd on every ack).
- receipt pointers: §1 defect list · §2 input-accounting table · §3 removed-behaviour inventory ·
  §4 error-path sweep · §5 residuals (individual verdicts) · §0 method.

**Overall read.** The two waves are careful and the reasoning written into them is unusually
good — but the diff repeats, in three places, the exact class it was fixing: *prose that describes
a mechanism the code no longer runs*. One of those is a live consumer-facing loop (D1); two are
docstrings that now contradict the code beneath and beside them (D2, D3). Separately, the wave
bounds four caller-controlled strings on the `message` path while leaving four caller-controlled
strings on the `trace` path unbounded (D4) — and the diff's own comment states the mechanism that
makes them reachable.

---

## 0. Method, and what I deliberately did not do

I read the diff first, in full, before forming any conclusion, and built the input-accounting and
removed-behaviour enumerations from the diff hunks alone. Only afterwards did I open the
surrounding production files to test each hypothesis.

**Tool honesty (brief-base §4).** The lore MCP tools were loaded (`lore_search`, `lore_get_symbol`,
`lore_impact`, `lore_read`) and I did **not** use them. The questions this role asks are
diff-shaped and textual — "what did these deleted lines DO", "does this prose still match this
code", "is this string bounded anywhere" — which is CLAUDE.md's fallback case (b), non-symbol
textual seams, plus (a) exhaustiveness where one missed site matters. The one structural question
I had (*does anything consume `awaiting_answer`?*) I answered with a bare, anchor-free grep over
`loremaster/**/*.py` minus tests, per the repo's sweep rule. Stating the fallback out loud is the
requirement; no friction row is warranted — the tool was not weak, it was not the right instrument.

Things I refused, per brief: any `loremaster/tests/**` file, the five design docs, every
`REPORT-*.md` including this packet's own, `/home/ejprice/scratch/**`, and pytest.

---

## 1. DEFECTS — substantiable from the code alone

Ranked by severity. Each carries a concrete failure scenario.

### D1 — HIGH · The drain elision's re-ask is still unreachable on a peek past the ceiling

`AppContext._render_comms_drain` (server.py) now computes:

```
reachable  = result.total_pending if result.peeked else remainder
next_limit = min(reachable, _MAX_DRAIN_LIMIT)          # _MAX_DRAIN_LIMIT = 50
```

and always renders `"+{more} more unread — re-run with limit={next_limit}"`.

**The fix is correct only while `total_pending <= 50`.** Above that, the `min()` collapses the peek
branch's honest value to the ceiling, and a peek **stamps nothing** — so obeying the instruction
re-reads the pending set from its oldest row and re-serves the identical head. The tail is
unreachable by **any** limit the dispatcher will honour.

**Failure scenario (concrete).** An agent holding 120 unread runs
`lore_comms action=drain peek=true limit=50`. It is served 50 rows and the line
`+70 more unread — re-run with limit=50`. It obeys. It is served the same 50 rows and the same
line. Forever. The off-by-one form is just as real: `total_pending = 51`, `limit = 50` →
`+1 more unread — re-run with limit=50` → row #51 is never reachable.

**Why this is a defect and not a spec question: the sibling the fix cites as its own precedent
already solves it, deliberately, and the fix copied only half of it.** The comment above the line
says the clamp is *"the exact rule `_MAX_FLEET_LIMIT`'s own comment states, and which the sibling
`_render_comms_fleet` obeys at this same line."* Open that sibling. `AppContext._render_comms_fleet`
carries **two** elision variants, and its docstring states the reason verbatim:

> *"while the display cap still has headroom (`len(shown) < _MAX_FLEET_LIMIT`), a re-ask naming a
> higher `limit=` is actionable. Once the display cap itself is what elides
> (`len(shown) == _MAX_FLEET_LIMIT`), that re-ask would be a **dead end** (re-running at the SAME
> already-maxed limit) — the cap-disclosure variant names the display cap instead."*

Its code branches accordingly: `if len(shown) == _MAX_FLEET_LIMIT:` →
`"+{more} more beyond the display cap ({cap})"` — **no re-ask at all**; else the `min()` re-ask.

The drain fix took the `min()` and left the dead-end guard behind. Note the fleet render's own
guard also has a structural constraint the drain must respect: the AST template-literal pin
requires `args[0]` to be an `ast.Constant`, which is why fleet uses two duplicated `render_line`
calls rather than a ternary — the same shape is available here.

**Aggravating detail.** For a peek the situation is *recoverable* only because the header line
above already reads `"peeked {shown} of {total} pending — nothing stamped; re-run without
peek=true to mark them seen"`. So the response contains both an escape and a trap, and the trap is
the one phrased as an instruction with a number in it. For a **non-peek** drain past the ceiling
the line is obeyable (stamped rows never re-serve, so `limit=50` does make progress) but it names
the limit the caller just used with no hint that further rounds are needed — the fleet render
would have disclosed the cap.

### D2 — MEDIUM · `_render_comms_drain`'s docstring now contradicts the code it documents

The same function's docstring still says:

> *"The elision's re-ask is the **REMAINDER in both slots**, because a non-peek drain stamps
> exactly the served window and stamped rows never re-serve — a `shown + more` re-ask would name
> rows that CANNOT come back."*

After this diff the peek branch's re-ask is `result.total_pending`, which **is** `shown + more` —
the precise value the sentence forbids — and both branches are then clamped to `_MAX_DRAIN_LIMIT`.
The `Args:` block compounds it: *"limit: The served window's cap; unused by the arithmetic (**the
honest re-ask is the remainder, never the cap**)"* — the arithmetic now involves a cap.

This is the repo's named class: a doc teaching a retired mechanism, which no gate catches. It sits
roughly forty lines above the code that falsifies it, inside the fix for a served-prose defect.

### D3 — MEDIUM · The refs render's stated rationale is now false

`AppContext._render_comms_drain_row`'s docstring:

> *"`refs` are capped at the SHARED `_COVERAGE_NAMES_CAP` with a counted remainder: **refs are
> uncapped at the ledger**, so an uncapped render is an unbounded dump in the subsystem's
> highest-volume surface."*

This diff capped refs at the ledger — `MESSAGE_REFS_MAX_COUNT = 20` entries, each
`MESSAGE_POINTER_MAX_CHARS = 256` chars, enforced in `MessageLedger._reject_oversize_pointers` and
backstopped by two schema ASSERTs. The render cap is still *correct* (5 « 20 is a display choice);
its stated *reason* is dead. A reader following the rationale would conclude the ledger is
unbounded and design accordingly.

Same class as D2, one file over, in a sibling the diff's own comment cross-references — i.e. the
retired-claim sweep did not run over the surfaces this change invalidated.

*(Checked and cleared while here: `safe_str(ref)` is `sanitise_line(str(ref))`, so refs ARE routed
through the shared sanitiser seam. `refs[*]` carries a length ASSERT but no charset ASSERT, so a
ref may legally contain newlines — the render handles it. Not a defect.)*

### D4 — MEDIUM · Four caller-controlled strings on the `trace` write path are unbounded, in the wave whose stated rationale is that unbounded pointers void a cap

The pointer-bound commit's own justification (`MESSAGE_POINTER_MAX_CHARS`'s comment):

> *"it refuses content-smuggling outright, because a 2000-char 'ref' is a BODY wearing a pointer's
> name. Without it the body cap is theatre."*

`trace` has no such bound anywhere. `_TRACE_FIELD_SPECS` declares
`tool` (`string`, no constraint), `agent` / `session` / `action` (`option<string>`, no constraint);
`SurrealStore.record_trace` applies none; `TracingFastMCP._record_tool_trace` applies none.

**And the diff itself supplies the reachability proof.** `AppContext._trace_summary`'s new comment:

> *"the group key is the DISPATCHED tool name, and an unknown name still reaches the seam (the
> dispatch fails INSIDE the funnel, so the row is written before the failure surfaces)"*

Confirmed in `TracingFastMCP.call_tool`: `name` is the raw MCP `params.name`, the write is in
`finally`, so a dispatch that raises for an unknown tool **still persists `tool=name` verbatim**.
`_TRACE_DECLARED_KEYS = ("agent", "session", "action")` are likewise stored plaintext — the
`_trace_params_hash` docstring was updated in this very diff to say so explicitly.

**Failure scenario.** A client calls a "tool" whose name is 100 KB of prose, with a 100 KB
`session` argument, repeatedly. Every call writes a full-size row. The new window + `_TRACE_BY_TOOL_CAP`
bound the **cardinality** of the served aggregate and nothing else: on a quiet instance the giant
name ranks inside the top 20 by calls and is served straight into the next consumer's `lore_index`
response as `by_tool[].tool`.

The read side was hardened in this wave; the write side was left open. That asymmetry is the
finding — I make no claim about which side the spec intends to bound.

### D5 — LOW-MED · `MessageLedger.send`'s own API contract under-documents the constraint it just gained

`send` now raises `MessagePointerError` (via `_reject_oversize_pointers`). Its `Raises:` block does
not list it. Its `Args:` block documents `body` as *"blank is rejected, over-cap is REJECTED (never
truncated)"* but documents `refs` as merely *"The message's pointer list, or `None` (⇒ `[]`)"*, and
`thread` / `task_id` with no bound at all. The ledger is the ONE writer and this is the contract a
non-tool caller reads.

The tool-schema layer was updated correctly and derives every number from the constants via
f-strings — the gap is only at the ledger's own docstring.

### D6 — LOW · `_comms_resolve_recipients`'s cost claim is not derived, and the hot case got more expensive

The new docstring's property 2:

> *"**The happy path costs ONE store read, not N.** The session's row-unlimited membership —
> already read for the broadcast branch — resolves every live name locally"*

`AgentRegistry.roster()` issues **two** queries: a `GROUP BY status` count, then
`SELECT * FROM agent WHERE session = $s`, row-unlimited by design. And the diff **hoisted** that
call above `if to:`, so the explicit-recipient path now pays it unconditionally — it previously
paid zero roster reads and `len(to)` `get_agent` reads.

| shape | before | after |
|---|---|---|
| `to=["alice"]` in a 200-agent session | 1 `get_agent` query | **2 queries, one pulling all 200 rows** |
| `to=[a,b]` | 2 queries | 2 queries + full membership scan |
| `to=[a…j]` (10) | 10 queries | 2 queries + scan ✅ |
| broadcast | 2 queries | 2 queries (unchanged) |

The cost scales with **session size**, not with `len(to)`. Property 1 (naming every bad name at
once) is real and valuable and I am not disputing it — only the arithmetic claim beside it. Per
this repo's law, prose describing behaviour must be derived from the behaviour.

*(Related, same function: the failure path re-reads the fleet. `_comms_enrich_unknown_agent` calls
`agent_registry.fleet(session=…, limit=_MAX_FLEET_LIMIT)` even though the caller is holding a
complete, row-unlimited `roster` it could enrich from. Third roster-shaped read on one failed send.)*

### D7 — LOW · Typo in a shipped comment

`config.py`, above `DEFAULT_TELEMETRY_WINDOW_DAYS`: *"so the read is windowed rather **thana** full-table
scan"*.

---

## 2. INPUT ACCOUNTING — every input reaching a changed seam, and its fate

Built from the diff. **The question answered per row is: can this input's bad value produce no
observable signal?**

### 2a. `lore_comms action=send`

| input | over-cap fate | blank fate | notes |
|---|---|---|---|
| `body` | ✅ `MessageBodyError`, teaching | ✅ rejected | unchanged |
| `refs` (count > 20) | ✅ `MessagePointerError` + schema `array::len` ASSERT | — | layers agree |
| `refs[i]` (len > 256) | ✅ `MessagePointerError` naming the INDEX + schema `refs[*]` ASSERT | ⚠ `""` accepted at both layers | Q8 |
| `task_id` (len > 256) | ✅ `MessagePointerError` + schema ASSERT | ⚠ `""` accepted | Q8 |
| `thread` **supplied**, len > 256 | ✅ `MessagePointerError` + schema ASSERT | ⚠ `""` accepted **and defeats the documented session default** | Q8 |
| `thread` **omitted** (`None`) | ⚠ **skips the ledger check entirely**; the stored value is `session`, checked only by the engine ASSERT → opaque failure, no teaching | — | **Q3** |
| `to` (list) | ⚠ **no count bound at any layer** — the only caller-supplied list in this surface without one | `[]` ⇒ broadcast (documented) | **Q6** |
| `to[i]` unknown | ✅ ALL bad names in one enriched error (improvement) | — | |
| `to[i]` retired | ✅ ALL retired names in one error | — | ordering: unknown wins over retired (new) |
| `to` = only the sender, broadcast | ✅ new `_EmptyRecipientSetError` with an honest first-agent teaching | — | improvement |

### 2b. `lore_comms action=ack`

| input | fate |
|---|---|
| `note` len > 2000 | ✅ `MessageBodyError` + `to.ack_note` schema ASSERT — layers agree |
| `note` when the CAS wins **nothing** | ⚠ **SILENCE.** Written nowhere; `_render_comms_ack` suppresses the note line on `not acked`. Caller gets zero signal that its note was discarded. **Q7** |
| `note` blank | accepted, stored as `""` on every won edge |
| `seqs=[]` with an over-cap `note` | now **raises** (validation moved above the early return) — see §3 |
| `seqs[i]` forged / not addressed | ✅ grouped and named per outcome (unchanged) |

### 2c. The trace seam (every tool call)

| input | fate |
|---|---|
| `name` (tool), any length | ⚠ **stored verbatim, unbounded**, even when the dispatch fails — **D4** |
| `arguments.agent/session/action`, any length | ⚠ **stored verbatim, unbounded** — **D4** |
| all other `arguments` | ✅ digested to 64 hex by `_trace_params_hash` |
| no request context | ✅ now `logger.debug("trace.emit.no_request_context")` (was silent) |
| context without `write_store` | ✅ `logger.warning("trace.emit.no_write_store")` (was silent) |
| context whose `write_store` is `None` | ⚠ guard REMOVED; now `AttributeError` → caught upstream → `trace.emit.failed`. Observable but mis-classified. **Q5** |
| write raises / times out | ✅ `logger.exception("trace.emit.failed")`; the tool's own outcome wins |
| write cancelled by a **raw asyncio** cancel | ⚠ **row lost AND the original exception replaced** — the shield covers anyio scopes only. **Q4a** |

### 2d. `trace_aggregates` / `TraceSummary`

| input | fate |
|---|---|
| `window_days` from config | ✅ `PositiveInt` |
| `window_days` passed directly (non-config caller) | ⚠ `0` or negative ⇒ empty result, served as a plausible quiet instance. No validation in the store method. **Q10** |
| rows > `_TRACE_BY_TOOL_CAP` | ✅ capped by CALLS desc, re-sorted by name, `tools_elided` disclosed, `total` stays true |
| `latest` = `NONE` for a group | ✅ `.get(...) is not None` guard — correct per store reference §10 (`time::max` returns NONE for empty groups) |
| `TraceSummary` constructed with no args | ⚠ serves `window_days: 14` — a claim about a config it never read. **Q9** |

---

## 3. REMOVED-BEHAVIOUR INVENTORY

Enumerated from the diff's `-` lines, independently, before reading any surrounding rationale.
One verdict per item.

| # | What the removed/replaced code DID | Verdict |
|---|---|---|
| R1 | `_comms_send`: per-name `get_agent` loop, **raising on the FIRST bad name** | **dropped deliberately** — replaced by all-at-once classification; strictly better teaching |
| R2 | ...and enriching **from the caught error** (`raise … from error`, message preserved) | ⚠ **silently lost.** The new code writes `except _UnknownAgentError:` with no binding and raises a synthesised error with no `from` — the registry's own message and the traceback chain are gone. Cosmetic today; a diagnostic regression. **Q13** |
| R3 | ...and calling `get_agent` for **every** name (uniform result TYPE) | **dropped deliberately**, with a latent edge: `resolved` now mixes `AgentRosterMember` and `Agent`. **Q12** |
| R4 | ...and reading the roster **only** on the broadcast branch | ⚠ **behaviour changed, undisclosed.** Explicit sends now always pay a two-query full-membership read, and now fail if that read fails. **D6** |
| R5 | Retired-recipient message *"recipient 'x' is retired"* (singular) | **preserved with pin** — pluralised, same teaching, same `ValueError` type |
| R6 | Ledger's generic `EmptyRecipientSetError` prose for a lone-agent broadcast (*"…is a caller error, not a broadcast"*) | **preserved-with-correction** — the server now pre-empts it with an honest first-agent message; the ledger's own text is intact for direct callers |
| R7 | `_trace_summary`: `total = sum(by_tool)` | **dropped deliberately** — now summed over ALL groups so the cap cannot shrink the total. Correct |
| R8 | `TraceSummary` docstring's *"only when nothing has ever been traced — a fresh store"* | **preserved-with-correction** — now says "in the window", with the ⚠ banner |
| R9 | `trace_aggregates`' unbounded `FROM trace GROUP BY tool` | **dropped deliberately.** But its `Returns:` promise *"One row per distinct tool that has EVER traced"* was a served-shape guarantee; correctly rewritten to "INSIDE THE WINDOW" |
| R10 | `_record_tool_trace`: `getattr(request_context, "lifespan_context", None)` | **dropped deliberately** — direct access; an absent attribute now surfaces as `trace.emit.failed` instead of a silent return |
| R11 | `_record_tool_trace`: `store = getattr(app_ctx, "write_store", None)` + `if store is None: return` | ⚠ **two behaviours collapsed into one.** The name lookup is now typed (good, and the stated point). The **`None`-valued** guard is gone with no replacement. **Q5** |
| R12 | Unshielded `await` in `finally` | **preserved-with-correction** — shielded + bounded; the residual raw-cancel leg is **Q4a** |
| R13 | Instructions: *"If a partial reply cleared your thread… re-establishes the debt. A question clears only when…"* | **dropped deliberately, and it is the best change in the diff** — it promised a mechanism nothing implements. **Verified independently:** `MessageLedger.awaiting_answer` has ZERO production consumers (bare grep over `loremaster/**/*.py` minus tests: definition + docstring/comment mentions only), so the replacement's *"lore does not report that state back to you yet"* is **true** |
| R14 | Ack render: unconditional `"acked {n} of {m}: {seqs}"` | **preserved-with-correction** — the empty-list colon is gone; the count still renders |
| R15 | `to` param description: *"a rejected send writes nothing at all"* | **preserved-with-correction** — *"writes no message and no delivery — all-or-nothing"* is more precise and matches `send`'s single-transaction shape |
| R16 | `_trace_params_hash` docstring: *"the digest is… the whole privacy boundary"* | **preserved-with-correction** — the over-claim is retracted and `_TRACE_DECLARED_KEYS`' plaintext storage is now stated. This is exactly right, and it is what makes **D4** legible |
| R17 | `send`: pointer validation inserted **before** the empty-recipient check | **behaviour changed, unremarked.** A call with both faults now reports the pointer fault. Benign |
| R18 | `ack`: note validation inserted **before** the `if not requested: return` early exit | **behaviour changed, unremarked.** `ack(seqs=[], note=<3000 chars>)` now RAISES where it previously returned an empty result. Defensible (validate before acting) but it is a new failure on a previously-succeeding call |
| R19 | `_MESSAGE_FIELD_SPECS`: `thread` with no constraint; `refs` with `DEFAULT []` only; `task_id` bare | **preserved-with-correction** — narrowing ASSERTs added. Migration verdict in **Q2** |
| R20 | `_TO_FIELD_SPECS`: `ack_note` bare | **preserved-with-correction** — same, and the sharp one for **Q2** because `to` edges are UPDATEd on every ack |

---

## 4. ERROR-PATH SWEEP — *"would anyone ever KNOW?"*

Every `except` / default-return / swallow in or adjacent to the diff.

| site | behaviour | would anyone know? |
|---|---|---|
| `TracingFastMCP.call_tool` → `except Exception` | logs `trace.emit.failed` with the tool name | ✅ server log. Caller correctly unaffected (ruled posture) |
| ...same, `BaseException` (`CancelledError` from a raw asyncio cancel) | **not caught**; row lost; **replaces the tool's in-flight exception** | ❌ nothing logs it, and the caller sees the wrong error. **Q4a** |
| ...same, `anyio.fail_after` timeout | raises builtin `TimeoutError` (an `OSError`, hence `Exception`) → caught and logged | ✅ verified by type hierarchy |
| `_record_tool_trace` → `except LookupError` | `logger.debug` + return | ✅ improvement (was silent). DEBUG is defensible: expected shape |
| `_record_tool_trace` → `except AttributeError` | `logger.warning` + return | ✅ loud — but the class-keyed catch cannot distinguish "no `write_store`" from "something inside `write_store` raised `AttributeError`". **Q5** |
| `_record_tool_trace`: `getattr(request_context, "request", None)` / `getattr(request, "headers", None)` | `transport_session=None` on any absent header | ⚠ **unchanged by this diff**, but it is #131's exact shape: an absent correlator is indistinguishable from a transport that has none, and nothing renders the field today |
| `_comms_resolve_recipients` → `except _UnknownAgentError` | appends to `unknown`, discards the error object | ✅ every name is reported; ❌ the original message + chain are lost (**R2/Q13**) |
| `_trace_summary`: `row.get("latest") is not None` | drops NONE-latest groups from the max | ✅ correct per store reference §10; `total`/`by_tool` unaffected |
| `_render_comms_ack`: `if note is not None and acked` | suppresses the note line | ❌ **the discard is silent — Q7** |
| `_trace_summary` / `trace_aggregates` raising | propagates and fails the whole `lore_index` call | ✅ loud. Unchanged posture |

**No `contextlib.suppress`, no bare `except:`, no `return None`-on-failure introduced by this
diff.** The two swallows that exist are both narrower and louder than what they replaced.

---

## 5. QUESTIONS THE SPEC (or a live store read) MUST ANSWER

Each is a fork I am deliberately not settling. Recommendation given where I have one.

### Q1 — HIGH · The `trace_ts` "free window" is a claim about the PRODUCTION STORE, and no test can see it

The new index ships with:

> *"the trace table is empty exactly once — now — and after this deploy it grows on EVERY tool
> call, so an index added later BUILDS, blocking, at every store's next boot."*

That argument is sound **iff** no production deploy has yet shipped `TracingFastMCP`. It has not
shipped *in this diff* — `84756b6` already contained the class; this diff only modifies it. So the
seam predates the base of the range I was given, and whether it reached `lore-surreal :18500` is a
**deploy fact**, not a code fact.

Store reference §1.5, vendor-quoted: *"Without `CONCURRENTLY`, `DEFINE INDEX` **blocks until the
index is fully built**."* `_plain_index` emits no `CONCURRENTLY`, and `ensure_ready()` runs at every
boot. If the production `trace` table is populated, the next boot blocks for the build.

This is §1.6 exactly — *a fixture that guarantees a clean slate can never test what only happens on
a dirty one.* **Required before deploy:** `SELECT count() FROM trace` and `SELECT count() FROM
message` against `:18500`. I am prohibited from container operations and did not run it.
Recommendation: run it; if non-zero, the free-window rationale in both commits needs rewriting and
the build cost needs measuring, not asserting.

### Q2 — MED · Five new NARROWING ASSERTs on tables that may already carry rows

New: `message.thread`, `message.task_id`, `message.refs` (count), `message.refs[*]` (length),
`to.ack_note` (length). All ride `_define_field` → `OVERWRITE`, which is **correct** per store
reference §1.1 and is exactly what makes them migrate (#107's lesson applied properly — this part
is right).

The residual is §1.4: a narrowing change *"converges the SCHEMA but never the DATA"* — violating
rows survive but are **write-poisoned**, and *"the whole record is re-validated on write."*

- `message` rows: I find no production `UPDATE` of `message`, so poisoning is inert there.
- **`to` edges are UPDATEd on every ack** (`UPDATE to SET acked_at = …, ack_note = … WHERE
  acked_at IS NONE …`). A pre-existing edge whose `ack_note` exceeds 2000 chars would make every
  future ack touching it RAISE.

Same free-window question as Q1, and the same instrument answers it.

### Q3 — MED · The defaulted `thread` is the one pointer that bypasses the teaching layer

`_reject_oversize_pointers` skips `thread=None`; `send` then stores `thread = session`. The engine
ASSERTs `thread <= 256`, but `message.session` carries **no** constraint. So the two layers
disagree about the same value depending on which column it lands in.

Today nothing fires, and the reason is a coincidence one table over: `agent.session` carries
`_IDENTIFIER_CHARSET_ASSERT` = `^[a-z0-9][a-z0-9_-]{0,63}$`, capping it at 64. Nothing in *this
diff* establishes that. A direct `MessageLedger.send(session=<300 chars>, thread=None, …)` gets an
opaque engine assert failure naming `thread`, with no teaching message.

Fork: (a) validate the RESOLVED thread (`thread if thread is not None else session`) — one-line,
and it makes the ledger's guarantee self-contained; or (b) give `message.session` the same bound;
or (c) rule it unreachable and pin the reasoning. I would take (a).

### Q4 — MED · Cancellation-safety residuals

**(a) The shield's reach is narrower than the docstring states.** `anyio.CancelScope(shield=True)`
protects against cancellation delivered **through anyio scopes**. A raw `asyncio.Task.cancel()` —
process shutdown, an ASGI server tearing down its task — still raises `CancelledError` inside the
shield. In that leg all three failures the docstring says the shield prevents are back: no row,
nothing logged (`CancelledError` is a `BaseException`), and the tool's in-flight exception
**replaced**. The docstring states the shield unconditionally: *"`anyio.CancelScope(shield=True)`
is what makes the `finally` true."* Is this the KNOWN BOUND already pinned, and does the docstring
need the qualifier? (Repo law: an unpinned known limitation is indistinguishable from an unknown
one — and a bound stated as an absolute is worse than an unstated one.)

**(b) Is 5.0 derived or chosen?** The comment claims it is *"comfortably above the shared retry
driver's own conflict deadline."* Measured from source: `_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS =
2.0`, so the claim is literally true for **one** budget. But a trace write that must bootstrap a
session composes a 2.0 s bootstrap budget **plus** a 2.0 s query budget, and the deadline may never
veto the guaranteed attempt FLOOR (`_MAX_TXN_CONFLICT_ATTEMPTS = 5`, ceiling 64). Worst case
approaches ~4 s + network under a 5 s guillotine — after which the row is lost to a log line, which
is precisely the *"healthy-but-contended write must not be cut short and silently lost"* case the
comment names. Recommend either deriving the constant from the txn constants or widening it.

**(c) Un-cancellable teardown.** The shield adds up to 5 s of non-interruptible work per in-flight
call during shutdown. Bounded by concurrency rather than by call count, so probably fine — but it
is asserted nowhere and is a real change to shutdown latency.

### Q5 — MED · `except AttributeError` is class-keyed, and the `None`-store guard is gone

Two sub-questions. (i) The catch cannot distinguish "the context carries no `write_store`" from
"`write_store` resolved but something inside it raised `AttributeError`" — the second is
misreported as an un-wiring. (ii) The old `if store is None: return` guard has no replacement:
a context whose `write_store` **is** `None` now dies at `store.record_trace` and is logged as the
generic `trace.emit.failed` rather than the specific `no_write_store`. Both are observable, so
neither is silent — the loss is classification. Verified: production `AppContext.write_store` is a
plain non-optional `SurrealStore` attribute assigned in `__init__`, so the `None` path is a harness
shape only. Deliberate?

### Q6 — MED · `to` is the one caller-supplied list with no count bound

In the wave that added `MESSAGE_REFS_MAX_COUNT`. `_comms_resolve_recipients` returns
`[resolved[name] for name in to]` — **not** deduped (the probe loop dedupes via `dict.fromkeys`,
the return does not; dedupe happens only later in `send._dedupe_by_identity`). So `to` with 100 000
repetitions of one valid name materialises a 100 000-element list and carries it through
`_reject_unknown_recipients` before collapsing to one recipient. Bounded work, unbounded
allocation, no cap at any layer. Deliberate, or does `to` want `MESSAGE_REFS_MAX_COUNT`'s treatment?

### Q7 — MED · A note on a batch that wins nothing has a silent fate

`_render_comms_ack`: `if note is not None and acked:`. When the CAS wins nothing, the note is
written nowhere **and** the render says nothing about it. The comment above the guard reasons the
other way — *"a note on a batch that won nothing was recorded NOWHERE — and saying nothing there
would imply that it had been"* — which reads as an argument FOR a disclosure line, while the code
chose suppression. Comment and code disagree about what silence means.

This is pre-existing, but the wave promoted `note` to a first-class validated input
(`_reject_oversize_note`), so its fate is now in frame: a caller can have its note **rejected** for
length but **discarded** without a word.

### Q8 — LOW · Blank pointers are accepted where blank bodies are rejected

`body` rejects blank. `refs=[""]`, `task_id=""`, `thread=""` are accepted at both layers. `thread=""`
additionally defeats the documented *"defaults to your session"* contract, because the default fires
only on `None` — so an empty-string thread is stored and becomes a distinct conversational thread
(and the drain row's `entry.thread != session` comparison will treat it as a *deliberate* thread
label, rendering `(thread )`). Intended? A pointer to nothing is the same class of junk the count
and length bounds exist to refuse.

### Q9 — LOW · `TraceSummary()`'s `window_days` default is a manufactured claim

`window_days: int = DEFAULT_TELEMETRY_WINDOW_DAYS` on the model, and
`IndexStatusSummary.traces: TraceSummary = Field(default_factory=TraceSummary)`. Any construction
that omits `traces` serves `window_days: 14` — a statement about a config it never read — beside
`total: 0`, which then reads as "a quiet 14 days" rather than "not measured". The single production
path (`AppContext.index_status`) always passes `traces`, so nothing is wrong today.

This is this repo's own law applied to a served field: *"Fixture factories must not default a
parameter the code branches on"* — and here a consumer branches on it. Options: drop the default and
require it, or default it to a sentinel that cannot be mistaken for a measurement.

### Q10 — LOW · `trace_aggregates(window_days=…)` does not validate its argument

`window_days=0` ⇒ `cutoff = now` ⇒ empty result ⇒ served `total: 0, window_days: 0`, which reads as
a plausible quiet instance rather than as a bad call. `PositiveInt` guards only the config path; the
store method is public and the docstring explains *why* the value is passed in rather than read
locally, so a second caller is anticipated.

### Q11 — LOW · `_MESSAGE_FIELD_SPECS` order is load-bearing and unstated

`refs` (the array) MUST be emitted before `refs[*]`, because `TYPE array<T>` **implicitly defines**
`<field>.*` (store reference §7) and `_message_statements` re-applies the whole spec list with
`OVERWRITE` on every `ensure_ready()`. Today the tuple order is correct. The comment explains at
length why the element row needs `OVERWRITE` and never says the pair is **order-dependent** — so a
future alphabetisation or reshuffle silently drops the per-entry ASSERT, with the array-level count
ASSERT still green and no gate the wiser. Is that ordering pinned?

### Q12 — LOW · Heterogeneous recipient types

`_comms_resolve_recipients`' `resolved` dict mixes `AgentRosterMember` (roster-resolved) and `Agent`
(probe-resolved). Both satisfy `_AgentRefLike` (`.id` / `.name`) today. A later change needing a
field only `Agent` carries breaks **only** for roster-resolved recipients — and any fixture where
every recipient is freshly probed cannot see it.

### Q13 — LOW · Exception chain dropped

Old: `raise await …_comms_enrich_unknown_agent(self, error, …) from error`. New: `except
_UnknownAgentError:` (unbound) and a synthesised error with no `from`. The registry's own message and
the traceback chain are gone.

### Q14 — LOW · `agent.task_id` remains unbounded while `message.task_id` gained a cap

The `task_id` tool description is shared between `register` and `send` and correctly scopes *"at
most 256 characters"* to `'send'` — so the prose is **honest**. But `_AGENT_FIELD_SPECS` declares
`task_id` as bare `option<string>`, leaving `register`'s copy of the same conceptual value
unbounded and caller-controlled. Same shape as D4, lower stakes.

---

## 6. RESIDUALS — individual verdict per row

*"All remaining are X" is banned; each row is adjudicated on its own.*

| # | Observation | Verdict |
|---|---|---|
| S1 | `refs[*]` DDL spelling and `OVERWRITE` requirement | **CORRECT** — matches store reference §7's probed ✅ column verbatim, including that the element row is always a re-definition |
| S2 | `_plain_index` stays `IF NOT EXISTS` for `trace_ts` | **CORRECT** per §1.1's INDEX row; the §8 "a later index change never migrates" residual is inherited, not introduced |
| S3 | Bare ASSERTs on `option<>` fields (no `$value = NONE OR` guard) | **CORRECT**, and correctly justified — §7's probed row says the ASSERT is not evaluated when the field is NONE, and that the guard is cruft that teaches a false requirement |
| S4 | `time::max()` retained under `GROUP BY` | **CORRECT** — §7 and §2; `math::max`/`array::max` return garbage silently |
| S5 | `row.get("latest")` vs `row["tool"]`/`row["calls"]` | **CORRECT but inconsistent.** `.get` is right for the NONE-empty-group case (§10); `[]` is safe for an explicit projection (§2). No defect; the asymmetry is unexplained |
| S6 | `int(self._config.telemetry.aggregate_window_days)` | **redundant** — `PositiveInt` is already `int`. Harmless |
| S7 | Cutoff computed per call, not cached | **CORRECT**, and the ⚠ note explaining why is the right kind of comment (a constraint the code cannot show) |
| S8 | `WHERE ts > $cutoff` — strictly greater | **immaterial** at datetime resolution |
| S9 | *"`WHERE ts > $cutoff` rides the `trace_ts` index"* | **UNVERIFIED as written.** Asserted as fact in a docstring; no `EXPLAIN` receipt is cited. §0 also notes 3.2.1 shipped an index-backed `COUNT` fix — worth one `EXPLAIN` |
| S10 | `TraceSummary`'s ⚠ WINDOWED banner lives in the class docstring, not in `Field(description=…)` | **acceptable** — pydantic v2 publishes a model's `__doc__` as the JSON-schema `description`, so it does reach the consumer's `$defs`. Google-style `Attributes:` text does **not** become per-field descriptions, so the per-attribute wording is developer-facing only. Matches the surrounding house idiom; noted because the honesty argument leans on it |
| S11 | `tools_elided` counts TOOLS, not the CALLS they represent | **acceptable** — elided calls are derivable as `total − sum(by_tool.calls)`, and the `total` docstring says so explicitly |
| S12 | Three separate over-cap check implementations (`body` inline in `send`, `_reject_oversize_note`, `_reject_oversize_pointers`) | **acceptable, but flagged.** The CONSTANTS are single-sourced (`surreal_schema` → re-exported through `messages`, imported by `server`), which is where drift would actually hurt. The *check* is cloned three times with deliberately different teaching. Per ONE IMPLEMENTATION this is a design call, not a coding one — recording it so it is met deliberately |
| S13 | `_reject_oversize_note`'s docstring cites *"the fake oracle CALLS it"* | **smell.** Production prose bound to a test artifact's structure; it will read as noise to anyone without that file |
| S14 | `_message_statements`' docstring enumerates the field specs and no longer mentions the pointer bounds or the `refs[*]` element row | **stale-adjacent.** The enumeration is illustrative rather than exhaustive, so it is not false — but it is the same surface class as D2/D3 and was in the diff's blast radius |
| S15 | `_reject_oversize_pointers` materialises `refs` twice (`list(refs)` in the check and again in `_send_fragment`) | **trivial** — bounded at 20 entries after this very change |
| S16 | `MessageLedger.awaiting_answer` has zero production consumers | **not a defect of this diff** — and it is what makes R13's new instructions sentence TRUE. Recorded so the next reader does not have to re-derive it: it is built and unwired |
| S17 | `safe_str(ref)` on rendered refs | **CLEARED.** `safe_str = sanitise_line(str(value))`, so refs route through the shared sanitiser seam like every other cell in that row. I checked this because refs carry a length ASSERT but no charset ASSERT — a ref may legally contain newlines |
| S18 | `_comms_resolve_recipients` checks `unknown` before `retired` | **behaviour change, benign.** Previously whichever bad name came first in `to` won; now unknown always wins. Only affects which teaching a doubly-bad call sees |
| S19 | `FleetRoster` imported under `TYPE_CHECKING` and used in a runtime signature | **CORRECT** — `server.py` carries `from __future__ import annotations` |
| S20 | `_EmptyRecipientSetError` raised by the server for the lone-agent broadcast | **CORRECT** — reuses the ledger's type rather than minting a second one, so callers keying on the type still work |

---

## 7. What I did NOT test, and what would close it

- **No test-suite run** (brief). Nothing here is a claim about green or red.
- **No live store read** (brief prohibits container ops). Q1 and Q2 are therefore open, and they are
  the two that a green suite structurally cannot answer — store reference §1.6.
- **No `EXPLAIN`** of the windowed aggregate (S9).
- **I did not read the contract, the design canon, or any sibling report** — by design. Where a
  finding above is already covered by a pin or a ruling I could not see, that is the expected cost
  of this role; the lead holds the canon and adjudicates.
