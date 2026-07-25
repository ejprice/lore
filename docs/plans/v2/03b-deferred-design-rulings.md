# 03b deferred design rulings — the four blind-read items + Q1

**Author:** design-sidecar-03b-1 (Fable design consultant, spawned 2026-07-25). This doc
proposes; **the operator rules, the lead adjudicates** — every DD item below is a
recommendation with its fork stated, never a decision.
**Read at:** working tree at `8be70b7` (fix wave in flight — `_TRACE_BY_TOOL_CAP` and the
render cap already present in `AppContext._trace_summary` at my read; all claims dated
2026-07-25 unless cited otherwise).
**Sources (cited, never re-transcribed):** `docs/reference/surrealdb-31-capabilities.md`
(§1.1, §1.4, §1.5, §1.6, §2, §5, §10 — "the store reference" below) ·
`docs/plans/v2/03b-design-rulings-r2.md` (settled canon: §A-GRAFT, B4.1, B6, B8, B9, B12,
T2–T8, C2/C5, §E, §F — "r2" below) · `docs/plans/v2/03b-comms-message-surface.md` (the
packet; MP9, the scope-widening rationale, §OPERATOR GRANT) ·
`docs/plans/v2/05-comms-await-story.md` + `06-comms-protocol-drill.md` (the successor
scopes) · `REPORT-blindreader-03b-1.md` §D6/D7/D8/D11/Q1–Q9 + `REPORT-coldaudit-03b-1.md`
§8 R1/R2/R7/R10 (both committed at `f5258bf`) · production source read directly:
`server.py` (`TracingFastMCP`, `_record_tool_trace`, `_trace_params_hash`,
`AppContext._trace_summary`, `TraceSummary`, the `comms()` tool schema),
`store/surreal.py` (`record_trace`, `trace_aggregates`), `store/surreal_schema.py`
(`_TRACE_FIELD_SPECS`, `_MESSAGE_FIELD_SPECS`, `_TO_FIELD_SPECS`), `messages.py`
(`MessageLedger.drain`, `awaiting_answer`, `_row_to_inbox_entry`), `agents.py`
(`AGENT_NAME_PATTERN`), `memory/local.py` (the TTL read-filter precedent).
**Scope guard:** the nine fix-wave defects (blind D1–D5/D9, cold C1–C3) are NOT designed
here. Where a ruling below lands *in* the fix wave it is an ADDITIVE item flagged as such.

---

## DD-1 — Trace retention, the read path, and caller-controlled cardinality (blind D6 · Q6 · cold R3-adjacent)

### Facts (each re-derived this session)

- `trace` gains one row per tool call and **nothing in the tree deletes one** (the only
  `TRACE_TABLE` writers/readers are `record_trace`'s CREATE and `trace_aggregates`' GROUP
  BY — grep receipt, 2026-07-25).
- `SurrealStore.trace_aggregates` is `SELECT tool, count(), time::max(ts) FROM trace
  GROUP BY tool` — **no WHERE, no index on `tool` or `ts`** — and
  `AppContext._trace_summary` calls it on **every** `lore_index`.
- The fix wave has already landed the SERVE half: `_TRACE_BY_TOOL_CAP` with
  calls-descending selection, a true `total`, and a `tools_elided` disclosure
  (`_trace_summary`, read at `8be70b7`). **The scan and the growth are what remain.**
- There is **no row-GC anywhere in this codebase.** The only TTL precedent is the memory
  ledger's *read-time filter* (`expires_at IS NONE OR expires_at > time::now()` —
  `memory/local.py::_recall` WHERE assembly). A trace sweep would be the tree's FIRST
  actual deleter — so it is a design decision, not a chore (ONE IMPLEMENTATION: whatever
  ships becomes THE row-GC seam).
- The free window: production `trace` count is 0 (scout §3.1; cold audit R3 asks the
  deploy to confirm it read-only before DDL). **It closes at this packet's deploy.** A
  new index on the then-populated table builds BLOCKING at the next boot (store
  reference §1.5) — the exact argument r2 §T2.1 used to ship `trace_agent_ordinal` now.

### DD-1.a — RULING (recommended): ship a `trace_ts` plain index NOW, in the free window

`_plain_index(TRACE_TABLE, f"{TRACE_TABLE}_ts", ("ts",))` in `_trace_statements`,
`IF NOT EXISTS` (store reference §1.1 INDEX row), in the fix wave's pre-deploy
one-concern schema commit. It is r2 §T2.1's own argument one column over: shipped now it
is free once; shipped by a later packet it builds over weeks of all-tools rows at every
store's next boot. Its two designed consumers are DD-1.b's windowed read and DD-1.c's
eventual GC delete — unlike the `transport_session` index r2 §T2.1 deliberately withheld,
both consumers are named here, so the free-window argument is whole.
Rider (r2 §T2.1 verbatim): the schema pin parses the `FIELDS` clause, never substrings
the statement.
**Cost:** one statement + one schema pin. **Wrong build stopped:** none by itself — it is
the enabling line whose absence makes DD-1.b/DD-1.c permanently expensive.
**This is the one time-sensitive item in this doc.**

### DD-1.b — RULING (recommended): window the hot aggregate read

`trace_aggregates` gains `WHERE ts > $cutoff` (bound param; cutoff = now −
`telemetry aggregate window`, a new config value, **default 14 days** — the CONSTANT is
strikeable, the mechanism is not, the B6.3 pattern).

- **The scan becomes bounded:** a range predicate is an IndexScan (store reference §2's
  probed range-vs-starts_with row) over DD-1.a's `ts` index — in-window rows only,
  regardless of table age. Builder obligation: an **EXPLAIN receipt on the real store**
  proving the datetime range rides the index (the B10-row-6 discipline); if the planner
  refuses it, the window still bounds the GROUP's cardinality and the receipt says so
  honestly.
- **Served semantics change and must SAY so:** `TraceSummary.total`/`by_tool` become
  "calls in the last {window}" — the current docstring says "across EVERY tool" of an
  all-time count. The served Field descriptions and the docstring must **derive the
  window from the config value** (the derived-prose law; prose restated beside a
  mechanism is the PKT-28-C1 class). This also makes `trace_aggregates`' own "ONE
  bounded GROUP BY" docstring TRUE — today it is the over-claim blind residual 13 flags.
- **Cardinality falls out:** a typo-spamming client's junk `tool` names AGE OUT of the
  window; in-window distinct names are bounded by in-window call volume; the fix wave's
  render cap bounds the serve regardless. No write-side rejection of unknown tool names —
  an unknown-name dispatch is REAL traffic and a client-confusion signal worth keeping
  (the trust telemetry reading of D6.3); bounding the serve, not falsifying the record.
- **Adversary on my own design:** (wrong build 1) window the RENDER but not the QUERY —
  the scan stays unbounded with every number identical at small N. Stopped by the EXPLAIN
  receipt + a pin asserting the query text carries the `WHERE ts` conjunct (or a
  scripted-connection pin observing the bound param). (wrong build 2) window the numbers
  but keep the "every tool ever" prose — stopped by the derived-label pin: one fixture
  writes an out-of-window row and asserts it is EXCLUDED from `total` AND the served
  description names the window. (wrong build 3) compute the cutoff client-side once and
  cache it — stale cutoffs re-admit the scan; pin with two reads across a monkeypatched
  clock.
- **Committed-pin check (contract author owes this):** the two committed aggregate pins
  (`test_mcp_server.py::…trace_aggregates_reflect_recorded_traces` + empty sibling) write
  fresh rows and should stay green under a 14-day window; VERIFY rather than assume, and
  any amendment is strengthen-only under the packet's standing authorization.

**Cost:** ~one conjunct + config field + derived prose + 3 pins + an EXPLAIN receipt.
**Placement fork (operator):** fix wave (recommended — the wave is already inside this
file for D9/C3, and landing read+index together keeps one commit story) **vs** first
follow-up after deploy (acceptable — the table is EMPTY at deploy; the scan only grows
into a problem over weeks; only DD-1.a is deploy-gated).

### DD-1.c — RULING (recommended): row GC is DEFERRED TO PACKET 06 — with the mechanism specced and the decision point named

**Nothing may delete a trace row before packet 06 has read its curve.** The rows ARE the
instrument this packet was widened to build; a retention sweep shipped now is tuning
ahead of the measurement (the measure-then-tune deferral shape, with its structure):

- **What data:** the decay curve + the DD-5.b join-quality receipt, arriving at 06's
  drill/analysis.
- **Decided by whom, when:** packet 06's close-out rules `trace` retention (recommend
  **90 days** as the starting value — it covers any plausible re-analysis horizon while
  bounding the table at O(10⁵–10⁶) rows under realistic call rates) and lands the sweep.
- **The mechanism, specced now so 06 implements rather than invents:** a bounded
  `DELETE FROM trace WHERE ts < $cutoff` riding DD-1.a's index, executed on the periodic
  reconcile sweep tick (the ONE existing periodic loop, `config.reconcile_interval_s` /
  `index/reconcile.py`) — **never in `ensure_ready`** (boot stays DDL-only; a
  first-activation purge over months of rows must not block boot). First activation runs
  batched (builder verifies `DELETE … LIMIT`-or-equivalent against
  `lore_search(tier="surrealql-tests", …)` per the repo's engine-question order; fallback
  is id-batched deletes). Config validator: retention ≥ the DD-1.b aggregate window
  (cross-field, so the served window can never outlive its data).
- **Interim exposure, priced:** at O(10³–10⁴) calls/day × ~300 B/row the table grows
  ~0.3–3 MB/day against a 1.2 GB store — weeks of headroom; DD-1.a+b keep the hot read
  flat regardless of row count. **Escalation trigger if 06 slips:** any deploy smoke
  observing `SELECT count() FROM trace` > 1,000,000 goes to the operator as a fork.
- **The deferral is LEDGERED, not prose:** file a `lore_findings` row (category
  retention/perf, owner packet 06, citing this section) so the miss is pinned where the
  fleet looks, not only where this doc sits.

---

## DD-2 — The taught-but-unserved conversational-debt machine (blind D7 · Q9 folded)

### Facts

- `MessageLedger.awaiting_answer` + `WaitingOnAnswer` have **zero production consumers**
  (blind D7, re-confirmed by grep at `8be70b7`); `set_status` deliberately never touches
  the status row (r2 B2.5 — a ruling, not a gap); the `(sender, question)` index and the
  R3 deliveries-bound both serve the uncalled method.
- The fix wave is correcting the PROSE to teach only what is served — that half is
  handled and not re-designed here.
- Packet 05's Scope IN already carries the R1 deferral (recipient-side per-row `question`
  markers) **with a named decision point and a third-deferral escalation clause.**
- There are TWO waiting vocabularies and they must never conflate: stored
  `input_required` (self-declared via `heartbeat status=`, surfaced in `fleet`'s parked
  segment) and the DERIVED question-debt (`awaiting_answer`, surfaced nowhere).

### The mechanism, designed (so 05 implements rather than invents)

1. **The asker's surface — a `waiting` line on drain AND heartbeat, via ONE shared
   helper** (exactly the r2 B4.1 skew-block precedent: one extracted assembly, both
   verbs call it, sharing proven by mutation — change the template, both verbs' pins go
   red). Emit predicate: `awaiting_answer(agent_id) is not None`; template shape (exact
   wording is the 05 contract author's, promise-registry obligations per r2 B8 —
   registry entry, emit/no-emit proofs, full-line marker, battery case):
   `waiting: your question #{seq} on thread {thread} has no reply — asked {age} ago`.
   Prose derives from the typed `WaitingOnAnswer` (never a re-derived flag — the #104
   law). Cost per drain/heartbeat: two indexed reads (the `(sender, question)` index +
   the R3-bounded deliveries read) — the same order as the ~3 point reads B4.1 priced
   and accepted for skew-at-drain, and the read that finally makes the shipped index and
   the R3 narrowing LIVE rather than dead.
2. **The lead's surface — NOT a per-row fleet cell.** Deriving per agent inside `fleet`
   is an N×2-query N+1 at a 200-row cap. If 05 wants fleet visibility it designs a
   BATCHED derivation (one questions-by-sender read + one bounded deliveries read for
   the whole roster — a new ledger method, contract-author-owned, adversary-graded).
   Otherwise the lead reads debt through `story`/`await`.
3. **`await` is the natural first consumer:** an await that times out while the caller's
   own question is outstanding reports the waiting state in its honest-empty render
   ("timed out — still waiting on #{seq}, thread {thread}"). 05's mission statement is
   this mechanism's home.

### DD-2.a — RULING (recommended): ownership is packet 05, and the decision point WIDENS

This is 05 work, not fix-wave work: a new render line = promise-registry entries +
proofs + a battery case + a shared-helper extraction (r2 B8/B12 obligations) — contract-
author + adversary territory by law, and it would re-open the certified surface contract
mid-fix-wave. The 03b-ships-it alternative is priced for the operator: roughly one
template + one helper extraction + proofs + one battery case + a floor-model battery
re-run (C3's re-run trigger) — a small contract wave, NOT a drive-by. **Recommend NO for
03b.**

**The decision point 05 must carry (this widens the R1 clause already in 05's Scope
IN):** 05 must either **(a)** give `awaiting_answer` its first production consumer (the
waiting line and/or `await`'s timeout render, plus the re-adjudicated R1 per-row
markers), or **(b)** adjudicate the WHOLE mechanism for removal — method, model, the
`(sender, question)` index, and the R3 narrowing together (a dead mechanism wearing a
live index is D7's complaint with the prose fixed). A third deferral goes to the
operator as a fork — 05's own ⚠ clause already says this for R1; this ruling extends it
to the mechanism.

**Wrong build stopped (for 05's contract author):** a builder wiring the waiting line to
the STORED `input_required` status — the vocabulary conflation. Stopped by the
discriminating pair: an agent with stored `active` status + an unanswered question →
line renders; an agent with stored `input_required` + no outstanding question → no line.

### DD-2.b — RULING (recommended, fix-wave-eligible): pin the schema dependency Q9 found

`awaiting_answer`'s R3 bound (`in.thread IN $threads`) is a semantics-identical superset
**only because `message.thread` is a required, non-option `string`**
(`_MESSAGE_FIELD_SPECS`); a stored NONE would be silently dropped by `IN` and the agent
would read "waiting" forever (the safe direction, but a real divergence from the
"identical superset" comment). Pin it now: a schema pin asserting `thread`'s spec entry
is exactly `string` (never `option<string>`), with a docstring naming the
`awaiting_answer` IN-clause dependency as the reason. Additive, mechanical,
mutation-provable (flip the spec to `option<string>` → RED) — inside the standing
authorization's three conditions. **Cost:** one pin.

---

## DD-3 — `refs`/`thread`/`task_id`/`note` bounds — the body cap's own rationale, finished (blind D8 · Q8 folded)

### Facts

- `message.body`: bounded at BOTH layers — the ledger's teaching `MessageBodyError` and
  the store `ASSERT string::len($value) <= 2000` backstop. `refs`: `array<string>
  DEFAULT []` — **no count assert, no per-entry length assert**. `thread`: required
  `string`, unbounded. `task_id`: `option<string>`, unbounded. `ack_note`
  (`_TO_FIELD_SPECS`): `option<string>`, unbounded.
- The drain render serves up to 5 refs **verbatim** (`safe_str` collapses control chars,
  never truncates) plus the `{context}` cell. The sanitiser layer is CLEAN (blind D8
  verified it; this is a SIZE problem, not forgery).
- The served `refs` description currently RECOMMENDS the bypass: *"Bodies are capped;
  the content lives in what you name here."*
- The body cap's rationale is B6.3's render arithmetic: 50 rows × 2000-char bodies
  bounds the worst-case drain render. Unbounded refs void that arithmetic silently —
  five refs of arbitrary length per row make the cap theatre (cold R10's flagged claim
  becomes false through a side door).
- Free window: production has **no `message` table until this deploy** (r2 §0.F7), and
  message rows are never UPDATEd after create — so a narrowing ASSERT landed **before**
  the first deploy meets zero existing rows and zero §1.4 write-poisoning exposure.

### DD-3.a — RULING (recommended): a pointer-class length bound, ONE constant

`MESSAGE_POINTER_MAX_CHARS = 256`, applied to **each `refs` entry, `thread`, and
`task_id`**. Derivation of the value: the longest legitimate house pointer is a
receipts-path + section cite (~80–100 chars — e.g.
`docs/plans/v2/receipts/2026-07-24-packet03b/REPORT-scout-147-traces.md §5.1`); 256 is
that with headroom, and it refuses content-smuggling outright (a 2000-char "ref" is a
body wearing a pointer's name). One constant, one policy — three fields of the same
CLASS (pointers/labels), never three constants to drift.

### DD-3.b — RULING (recommended): a refs count bound

`MESSAGE_REFS_MAX_COUNT = 20`. The display already caps at `_COVERAGE_NAMES_CAP` (5)
with a counted remainder; 20 admits any real pointer batch; a thousand-entry list is
storage abuse (r2 §F.3's residual, closed here). Both constants strikeable; the
mechanism (bounded pointers, reject-never-truncate) is the ruling.

### DD-3.c — RULING (recommended): enforce at BOTH layers, mirroring `body` exactly

- **Ledger teaching reject** (the ONE writer — `MessageLedger.send` is where
  all-or-nothing lives, B2.6): a new teaching error naming the offending FIELD, the
  entry index (for refs), the measured length/count, the cap, and the fix ("put the
  content in a report/finding and point at it"). Policy lives at the ledger, not the
  dispatcher — a dispatcher-only check leaves every non-tool caller unbounded (ONE
  IMPLEMENTATION).
- **Store ASSERT backstop**, exactly as `body` carries one: `refs` gains a count ASSERT
  and a per-entry length ASSERT. **The syntax question is SETTLED — see DD-3.g** (probed
  2026-07-25 on 3.2.1 with controls): the ship shape is the element-path pair
  (`refs` + `refs[*]` rows), and `thread`/`task_id` take bare `string::len` ASSERTs —
  NONE is probed-exempt, so no NONE-guard is needed.
- **Migration:** `DEFINE FIELD OVERWRITE` lands the changed definitions (§1.1); landed
  in THIS deploy the narrowing meets an empty table (§0.F7). ~~Landed later it still
  cannot write-poison (message rows are never UPDATEd)~~ — but the window costs nothing
  to use. The message-slice dirty-store pin (§1.6 pattern) gains the narrowed-assert
  leg.
  > ⚠ **CORRECTION (lead, 2026-07-25) — THE STRUCK CLAUSE ABOVE IS FALSE, AND IT IS THE
  > MOST DANGEROUS SENTENCE IN THIS DOCUMENT.** *"Cannot write-poison (message rows are
  > never UPDATEd)"* is true of **`message`** and **FALSE of `to`**, where DD-3.f puts
  > `ack_note`. `MessageLedger.drain` UPDATEs `to` on EVERY call, and does so in ONE
  > guarded statement over the whole window
  > (`UPDATE to SET seen_at = … WHERE out = $agent AND in IN $message_ids AND seen_at IS NONE`).
  > SurrealDB re-validates the WHOLE record on write (store reference §1.4), so **a single
  > legacy edge carrying an over-cap `ack_note` fails that statement — and because it is one
  > statement over the window, the agent cannot drain ANY of its inbox. Total denial, not a
  > per-row rejection.**
  > **REPRODUCED** on spike-surreal `:18000` with a discriminating control set
  > (`REPORT-coldaudit-03b-2.md` §3.0): old-world edge accepted → new DDL applies OK → the
  > real whole-window stamp REJECTED → **control**: the same statement over the clean edge
  > alone ACCEPTED → the poisoned edge alone REJECTED naming `ack_note`. The control is what
  > makes the rejection a real negative rather than a broken probe.
  > **Production exposure at the 03b deploy is ZERO** — `message`/`to` have never been
  > deployed, which is exactly why the free window was used. What was wrong is the REASONING,
  > which any future narrowing on either table would have leaned on. **Any later narrowing of
  > a `to` field must treat existing edges as write-poisoning and plan a migration.**
  > **And note what would have caught it: the dirty-store rider THIS BULLET ITSELF SPECIFIES,
  > which was skipped.** The rider was not bureaucracy — it was the instrument. Skipping it is
  > why a false safety claim survived a design wave, a builder self-audit and two review rounds.

### DD-3.d — RULING (recommended): the description prose teaches the BOUNDED pattern

Rewrite the `refs` Field description to derive both constants (the derived-prose law):
pointers, at most {count}, each ≤ {chars} chars; *bodies carry prose, refs carry
ADDRESSES; content lives in reports/findings you point at — never inline here.* The
`thread` description gains its cap mention. Exact wording is the contract author's.
**Note the cost:** schema-description changes trip C3's battery re-run trigger (one
floor-model gate run — cheap, budgeted by FK-5).

### DD-3.e — RULING (settles Q8): NO charset validation on `thread` — length only

`thread` is a topic label, not an identity: it is a **bound param everywhere** (blind Q8
traced every site — no inlined WHERE), and the surface's own taught convention
`q:<topic>` contains `:`, which `AGENT_NAME_PATTERN` (`^[a-z0-9][a-z0-9_-]{0,63}$`)
forbids — applying the identity charset would REJECT the packet's own teaching. Named
re-open trigger: the day any verb inlines `thread` into a LIVE `WHERE` (packet 05's
`await` — LIVE WHERE params are IGNORED per store reference §10, so an inlined literal
needs charset-then-inline; **05's await design must consult this ruling before touching
thread in a LIVE clause**).

### DD-3.f — RULING (recommended): `note` caps at `MESSAGE_BODY_MAX_CHARS`

`note` is message-grade PROSE (recorded on won ack edges, served by 05's history
surface later), not a pointer — so it takes the BODY constant, both layers, same
pattern. Unbounded now is the same bypass one packet later, discovered by 05's render
instead of designed here.

### DD-3.g — the per-entry ASSERT syntax, SETTLED (probed 2026-07-25, spike-surreal 3.2.1, throwaway DB — appended post-acceptance at the lead's direction)

The DD-3.c verify-first caveat is discharged. Ruled order followed: **rung 1** (store
reference) — no direct answer, but §1.7's `chunk_hashes[*]` note + the house
`_define_field(SNAPSHOT_ENTRY_TABLE, "chunk_hashes[*].identity", …)` precedent supplied
the element-path lead; **rung 2** (`lore_search(tier="surrealql-tests")`) — element-path
TYPE coercion is spec-verified (`idiom/define_field_dot_star*.surql`) and `.all(|$x| …)`
closures are spec-verified (`functions/rand.surql`), but **no spec covers ASSERT in
element position or a closure inside an ASSERT** — the exact conjunction; **rung 3**
skipped with reasons (vendor prose could only re-supply the rung-2 lead and would need
the probe anyway — the open question was a parse/enforce conjunction only the engine
settles); **rung 4** — live probe, throwaway DB `probe_refs_*` on `ws://127.0.0.1:18000`,
`:18500` never touched, with the full control battery (legal ACCEPTED · over-length
REJECTED by the ASSERT — error text carries `must conform to`, so it is the ASSERT
firing, not a parse error · wrong-TYPE entry REJECTED for a DIFFERENT reason — a coerce
error naming the element index — proving assert-vs-coerce are distinguishable and the
probe cannot pass on parse noise).

**The verified DDL the builder writes — Shape A (element-path), recommended.** Two rows
in `_MESSAGE_FIELD_SPECS`, both emitted through the existing `_define_field`
(`OVERWRITE` — probed in exactly that clause):

```
("refs",    "array<string>", f"DEFAULT [] ASSERT array::len($value) <= {MESSAGE_REFS_MAX_COUNT}"),
("refs[*]", "string",        f"ASSERT string::len($value) <= {MESSAGE_POINTER_MAX_CHARS}"),
```

Probed behaviour, all six legs: the composed `DEFAULT [] ASSERT …` constraint parses and
BOTH clauses work (empty-omitted send stores `[]`); a legal list is accepted; an
over-count list rejects on the `refs` assert; an over-length ENTRY rejects on the
element assert with the error naming the element field and the offending VALUE —
`Found 'toolong-entry' for field ` + "`refs.*`" + ` … must conform to:
string::len($value) <= 8` — which is why Shape A beats the also-working Shape B (a
whole-array closure assert: `ASSERT array::len($value) <= N AND $value.all(|$r|
string::len($r) <= M)` — verified working, but its rejection dumps the entire array and
truncates the closure text; keep it as the known-good fallback, not the ship shape).

**Two riders the builder must know:**
1. **`thread`/`task_id` length ASSERTs need NO NONE-guard:** probed — an `option<string>`
   field's ASSERT is NOT evaluated on an omitted/NONE value (the omitted-`task_id` leg
   was ACCEPTED against a bare `string::len($value) <= N` assert; the over-length leg
   still rejected). So the DD-3.c sketch's `$value = NONE OR …` guard is unnecessary —
   write the bare assert on both fields.
2. **The engine NORMALISES the stored closure** (`|$r|` → `|$r: any|` in the error/INFO
   text). Any pin comparing `INFO FOR TABLE` output against the emitted DDL string will
   mismatch on Shape B; Shape A avoids closures entirely, but the warning stands for any
   future closure-bearing assert — pin the EMITTED statement (the house schema-pin
   idiom), never the engine's normalised echo.

### Adversary on my own design

- **Truncate-instead-of-reject** build: refused by inheritance — the body precedent is
  REJECT, never truncate; pin an over-cap ref → teaching reject naming index+length.
- **Ledger-only** build (store backstop skipped): a future writer bypasses silently;
  stopped by the schema pins on the ASSERT text.
- **Content displacement**: capping refs pushes payloads into… `thread`/`task_id`
  (capped, DD-3.a), `note` (capped, DD-3.f), or the body across MULTIPLE messages —
  volume is a rate concern outside this packet's controls; named, not silently absorbed.
- **Placement fork (operator):** fix wave (recommended: the schema free window + the
  description rewrite ride the same pre-deploy commit; every piece is additive and
  mutation-provable under the standing authorization) **vs** packet 05 (costs the free
  window and ships one deploy whose served description still teaches the bypass).

---

## DD-4 — `drain`'s at-most-once and the recovery story (blind D11 · Q5 folded · cold D3's ordering pin)

### The loss window, decomposed (the correction that reshapes the answer)

`MessageLedger.drain` stamps `seen_at` before returning; `_comms_drain` then renders.
But the legs are NOT equal:

1. **Post-stamp render raise** — the skew block is read BEFORE `drain` (cold audit D3
   adjudicated that ordering correct), and the render assembly after `drain` returns is
   **synchronous Python** — no await sits between the stamp and the return. A raise
   there is a code defect in a heavily pinned render, not an operational leg.
2. **Cancellation** — fires at await points; post-stamp code is sync until the return,
   so the cancellation-loss window is response transmission, same as leg 3.
3. **Transport drop** — the real leg, and no in-process reordering can close it (only
   an ack-of-read protocol can).

**And an honesty correction to D11's wording:** stamped rows are not DESTROYED — the
message rows and edges persist, `seen_at`-stamped. "Permanent" is a property of the
current VERB SET (nothing re-reads seen rows), not of the store. That is exactly the
gap packet 05's declared `since=`/paging surface exists to fill.

### DD-4.a — RULING (recommended): do NOT reshape `drain` in 03b

The candidate reshape (stamp-after-render, or a fetch/stamp split with the handler
orchestrating) buys ONLY leg 1 — the rare, pinned leg — and costs an oracle + ledger
reshape (contract-author + adversary + both consumer suites, the inherited row-6
measured law) plus a NEW race between fetch and stamp. Refused with reasons.

### DD-4.b — RULING (recommended, fix-wave-eligible): pin the minimal-window shape

A structural pin: `_comms_drain` performs **no awaited work after `ledger.drain()`
returns** — the skew read precedes it, the render is sync. This is cold audit D3's
requested ordering pin, WIDENED to cover the loss-window property, so a future refactor
cannot silently move an await (a brief re-read, a second store call) into the
stamp-to-return stretch and grow the loss window back. Additive, mechanical,
mutation-provable (insert an `await` after the drain call in a scratch copy → RED).

### DD-4.c — RULING (recommended): the recovery verb is 05's `since=` — with a REQUIREMENT attached

**05's history/`since=` surface MUST serve SEEN rows, keyed by seq.** That single
property converts "stamped but never received" from permanent to
recoverable-with-effort: the agent-side protocol (05's teach, not 03b's) is *track the
last seq you PROCESSED; after any drain whose response never reached you, re-read
`since=<last processed>`*. Named decision point: 05's design phase; **if 05's `since=`
serves only unseen rows, D11 remains open and returns to the operator as a fork** (the
same third-deferral clause shape 05 already carries for R1).

### DD-4.d — RULING (recommended): the exposure is MEASURED, not assumed

The shipped telemetry already counts the loss-candidate events: trace rows with
`tool='lore_comms'`, `action='drain'`, `ok=false` are precisely the drains that raised
or were cancelled (the D1 fix makes the cancelled leg's row land reliably). Packet 06
reads that count beside total drains as the loss-rate BOUND — labeled honestly as an
upper bound (a pre-stamp raise loses nothing, and the trace cannot see which side of
the stamp the failure fell on). **Re-open trigger for a heavier mechanism** (a
lease/at-least-once read, the Fork-D shape): measured `ok=false` drains above ~0.5% of
drains, or ANY confirmed lost-directive incident — either goes to the operator.

### DD-4.e — RULING (recommended): peek stays the manual mitigation; do NOT teach peek-first

A peek-then-act-then-stamp protocol is available TODAY with shipped verbs and is
genuinely at-least-once — and teaching it as default doubles read traffic and
reintroduces a remember-to-stamp obligation (the decay problem one level down, the
exact failure the telemetry exists to measure). The `peek` schema description already
carries the re-serve semantics; sufficient.

### Q5 folded — concurrent same-agent drains double-serve

Accepted KNOWN BOUND: it requires an agent racing ITSELF, which the one-process-per-
agent fleet shape does not produce; the CAS guard stamps every row exactly once; the
loser's "drained N of M" over-describes its own stamping (the safe direction — nothing
is lost, something is double-read). No single-flight machinery (it would tax every
drain for a non-occurring race). Fix-wave-eligible one-liner: the bound + its re-open
trigger (any client multiplexing ONE agent identity across concurrent processes) goes
in `drain`'s docstring. Related residual, ruled here so nobody trusts it: 05 either
makes `stamped_seqs` TRUE (return the UPDATE's actual stamped set) or deletes the field
when it touches drain for `since=` — blind residual 3 stands until then.

---

## DD-5 — Q1: does the telemetry answer packet 06's question? (the most consequential item)

### The honest answer

**Not in its ideal per-agent form — and the gap is closed by REFUSAL, deliberately.**
`_TRACE_DECLARED_KEYS` harvests only `agent`/`session`/`action` literally declared, so
`trace.agent` is populated by exactly 1 of 15 tools (`lore_comms` — blind Q1's AST
enumeration, re-confirmed). MP9 refuses server-side inference, and this doc **re-affirms
that refusal**: every side door below stays shut.

What the instrument CAN answer, stated precisely so 06 neither over-claims nor
"helpfully" adds inference:

- **Per-agent NUMERATOR: complete.** Every `lore_comms` call declares `agent` — drains,
  heartbeats, sends, acks per agent, each with `ts` + the global `ordinal`.
- **Per-agent DENOMINATOR: only via the transport-session join** (r2 T4.2), which works
  iff one agent ≈ one transport session. Claude Code teammates most plausibly share the
  lead process's ONE MCP connection, in which case the join degrades to one-to-many —
  **VISIBLY** (r2 T4.4 designed exactly this observability). Production runs
  streamable-http (the run-once guard's session-manager path), so the correlator will
  be present; stdio's honest NONE covers dev harnesses only.
- **Per-agent, inference-free, regardless of the join:** (a) drain cadence in
  wall-clock (ts deltas between agent X's drains) and in fleet-ordinal terms (global
  calls elapsed between X's consecutive comms calls — an activity-normalised gap);
  (b) the **register-then-never-drains population** (registered agents with zero drain
  rows — total decay, per agent, exact); (c) drains-per-heartbeat per agent, IF 06's
  protocol mandates heartbeat cadence (the confound — both decaying together — is
  itself visible as wall-clock heartbeat gaps).
- **The session-grain fallback** (r2 T4.4): per-transport-session decay pools the lead
  with its builders — a draining lead can mask a never-draining builder. Real, and
  stated.

### DD-5.a — RULING (recommended): no new mechanism in 03b; the side doors stay shut

Refused, each with its reason: **(i)** sticky attribution ("probably the same agent as
the last call") — MP9's refusal, re-affirmed; a guessed identity poisons the curve
invisibly. **(ii)** an `agent=` param on every read tool — a 15-signature tax the
client will not reliably pay, and a sometimes-filled identity param is WORSE than none
(it manufactures a biased join: diligent agents self-identify, decaying ones — the
population under study — do not; the instrument would measure diligence, not decay).
**(iii)** `client_id`/`_meta` plumbing — absent in practice (r2 T4), unverifiable.

### DD-5.b — RULING (recommended): 06 opens with the JOIN-QUALITY RECEIPT

06's entry check gains one instrument, run during the drill's first minutes: with ≥2
registered agents having made comms calls, ONE read over `trace` measuring (a) distinct
`transport_session` values per declared `agent` and (b) declared agents per
`transport_session`. It settles empirically the property r2 T4.4 deliberately left
un-assumed — whether the client harness multiplexes. One-to-one → the designed join
works and per-agent curves are live; one-to-many → 06 runs the fallback battery above
and states the decision's grain honestly in its close-out. **This line belongs in the
06 packet file** (a one-line lead edit; flagged in my report rather than made — the
packet file is outside my writable set).

### DD-5.c — RULING (recommended): the QUESTION is still answerable; say what is lost

The forced-drain question is *"does pull-based drain attention decay?"* Decay ⇒ per-
agent drain gaps grow and/or drains stop — both visible in the inference-free battery
(DD-5's (a)/(b)), whatever the join quality. What the fallback loses is per-call-
denominated RATE precision, not the phenomenon. So: **the instrument answers 06's
question; it may not deliver the ideal curve** — and that sentence, not a prettier one,
is what 06's brief should inherit. The wrong build this ruling stops is organisational:
a 06 author who, finding the curve coarse, quietly adds the inference MP9 refused to
get a smooth per-agent denominator.

---

## DD-6 — Folded small items, one verdict each

| item | verdict | placement |
|---|---|---|
| Q2 / cold R2 (`directive_pending` computed-and-discarded) | The whole-set directive count is the **counts family packet 04 owns** (r2 §A-GRAFT's B4.1 disposition routed it there). Leave the ledger field as 04's read; add nothing in 03b. | 04 |
| Q3 (`hit_count`/`token_cost`/`model` permanently NONE) | Affirm as-is — r2 §F.1 already names it; option columns cost nothing; `record_trace`'s docstring honestly describes caller-supplied semantics. No action. | none |
| Q5 (racing same-agent drains) | Ruled at DD-4 (KNOWN BOUND + docstring + `stamped_seqs` disposition). | fix wave (docstring) / 05 |
| Q7 / cold R3 (production `trace` count before DDL) | Affirm the deploy-gate step: read-only `SELECT count() FROM trace` AND `SELECT count() FROM message` on `:18500` BEFORE the DDL applies; non-zero → STOP and re-price the index builds (§1.5). | deploy runbook |
| Q8 (thread charset) | Settled at DD-3.e — length bound only; charset would reject the taught `q:<topic>` convention. | fix wave |
| Q9 (`awaiting_answer`'s schema dependency) | Settled at DD-2.b — pin `thread` as required non-option `string`. | fix wave |
| cold R1 (awaited trace write on the wire path) | **Affirm r2 T5.2's ruling** (awaited-inline; the reasons hold and the D1 shield adds a bounded timeout that also caps the latency a cancelled call pays). Two additions: (1) the docstring DISCLOSES the latency coupling — cold R1's "rule it, then say it" is half-done until the prose lands; (2) the >5%-p50 re-open trigger gets its INSTRUMENT: the deploy smoke TIMES a read-tool batch and commits the number in the receipts — this deploy's figure is the BASELINE, and the trigger arms at the next deploy's comparison. A trigger nobody measures is a hope, not a decision point. | fix wave (docstring) + deploy smoke |
| cold R7 / r2 E8 (drain's unbounded pending read) | Affirm the E8 disposition: findings row, owner 05 (which touches drain for `since=`). File it if not yet filed. | 05 |
| cold R10 (the 50 × 2000 "size a consumer can still use" claim) | Affirm as a ruled value — and CORRECT its re-open trigger honestly: the generic seam cannot see drains-at-the-cap (`hit_count` is NONE), so "telemetry shows drains at the cap" is an instrument that does not exist. The honest triggers: a client-battery drain fixture AT the cap (the C2 task-2/13 family), or a filed finding from fleet use. Do NOT add a drain-specific declared key to get it — the generic seam stays generic. | 06 battery / findings |

---

## Consolidated placement map

**Fix wave (pre-deploy, additive, each mutation-provable under the standing
authorization — operator confirms the batch):** DD-1.a (`trace_ts` index — **the one
deploy-gated item**) · DD-1.b (windowed aggregate — or first follow-up, operator's
fork) · DD-2.b (thread-required pin) · DD-3.a–f (pointer bounds + descriptions —
free-window argument) · DD-4.b (no-await-after-stamp pin) · DD-4/Q5 docstring lines ·
cold-R1's disclosure line.
**Packet 05 (decision points named in each section):** DD-2.a (the waiting-line
mechanism + the widened use-it-or-remove-it fork) · DD-4.c (`since=` must serve seen
rows) · `stamped_seqs` truth-or-delete · cold R7's findings row.
**Packet 06:** DD-1.c (retention + the sweep, after the curve is read) · DD-5.b
(join-quality receipt, first instrument) · DD-5.c's framing sentence in the brief ·
cold R10's honest triggers.
**Packet 04:** Q2's directive-count surfacing (already routed by r2).
**Deploy runbook:** Q7/R3's two read-only counts; cold-R1's p50 baseline measurement.

Nothing in this doc contradicts a settled r2 ruling; where it touches one (T5.2 —
affirmed; T4.4 — instrumented; §F.3 — closed by DD-3.b; E8 — affirmed) the section says
so explicitly.
