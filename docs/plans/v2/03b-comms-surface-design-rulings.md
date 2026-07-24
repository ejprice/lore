brief-base v6 read

# 03b surface design rulings — coverage-premise probe, #145 disposition, #143 adjudication, the served shapes, drain telemetry

**Authority:** design-comms-03b (long-running comms design sidecar, packet 03b — successor to
`design-comms`, whose `03a-2-consume-path-design-rulings.md` rulings R1–R6 remain binding and are
cited here as 03a2-R1…R6). These are RULINGS the packet lead implements and pins, not options.
**Read at:** working tree `6a66671` (clean), 2026-07-23. All probes below were executed read-only
against that tree on 2026-07-23; every "committed contract" claim is measured at that ref.
**Sources (cited, not re-derived):** `~/.claude/plans/one-of-claude-codes-nifty-garden.md` ·
`docs/plans/v2/comms-subsystem.md` (incl. its three data-model overrides) ·
`docs/plans/v2/03b-comms-message-surface.md` · `03a-2-consume-path-design-rulings.md` ·
DESIGN-LAW §1/§5/§8/§15 · `docs/reference/surrealdb-31-capabilities.md` (read FIRST; §1.1/§1.4
govern every DDL item below) · findings #143/#145/#147/#175 · the committed RED contract
(`test_comms_tool.py`, `test_comms_promise_registry.py`) and shipped `server.py`/`messages.py`/
`store/surreal.py`.
**Operator inputs needed: NONE for S1–S5.** One deliberate deferral carries a named decision point
(Residual 1); the lead may carry it to the operator if judged scope-relevant.
**Addendum 2026-07-24:** S6 was originally ruled against the packet-as-written (drain-only
telemetry). An operator scope widening (~00:50, 2026-07-24: **03b traces EVERY tool call**)
superseded its premise; S6 is re-ruled below (v2) and S7 (caller identity at the generic seam)
added. Corroborating instrument: an independent scout reached the same #147 diagnosis by a
different route with a positive control —
`docs/plans/v2/receipts/2026-07-24-packet03b/REPORT-scout-147-traces.md` (`6e175fd`), whose §5
seam analysis is adopted where cited. S1–S5 stand; the ONLY S1–S5 change the widening forces is
the removal of v1's drain-render telemetry-failure notice line (see S6v2 §failure-posture).

**The consumer, restated once:** the reader of every rendered line below is an LLM agent. It
learns the comms contract FROM the renders and the instructions block (DESIGN-LAW §1.5: strategy →
read-once instructions; recovery moves → embedded per-response). Prose describing behaviour must be
DERIVED from typed state, never re-stated beside it (#104; PKT-28 C1 class).

---

## S1 — Coverage-premise probe: EXECUTED, PASSES. The render-hygiene exclusion STANDS, conditional on S2's pins.

**The premise probed:** 03b's scope excludes render hygiene because packets 02/02a's promise
instruments cover any new render. INDEX law (operator-ruled 2026-07-19) demands a kickoff probe.

**The probe (executed 2026-07-23 at `6a66671`, read-only, in memory, against the REAL scanner
functions — `_scan_render_literals_over_tree` / `_scan_safe_str_source` imported from
`test_comms_promise_registry.py`, driven over the REAL `server.py` source):**

| leg | input | result |
|---|---|---|
| POSITIVE CONTROL (instrument alive) | unmodified `server.py` | **49 literals from 9 helpers** collected (≥30 floor holds; `_render_comms_fleet` present) |
| **THE PROBE** | real source + appended synthetic `_render_comms_probe_03b` emitting an unregistered promise literal | literal **collected under the new name** and **absent from `_classified()`** → `TestEveryCommsRenderLiteralIsClassified` would go RED. New renders ARE seen, default-FAIL. |
| f-string leg (02a closure) | same, template as f-string | canonicalised to `do the thing: probe {} now`, collected, unclassified |
| safe_str leg | synthetic `safe_str('…promise…')` in a comms helper | collected |
| NEGATIVE CONTROL (#145, the condition) | same helper named `_render_probe_03b` (no prefix) | **INVISIBLE** — exactly the documented bound |

**Pass criteria (met, all five):** probe literal collected under the new function name; absent
from the classified sets; positive-control floor ≥30; f-string and safe_str legs collected;
negative control invisible (proving the pass is conditional on location+prefix, not unconditional).

**VERDICT: the premise HOLDS — conditionally.** 02/02a's instruments cover every new 03b render
IFF the renders live in `server.py` under the `_render_comms*`/`_comms_*` prefix (packet 03
ruling 5). The scope exclusion is honoured; the CONDITION is converted from convention to gate by
S2. Had the probe failed, the ruling would have been STOP + re-scope render hygiene INTO 03b with
operator notification — recorded so the branch exists on paper.

**Permanent instrument (03b contract additions, cheap):**
1. The probe already exists in pinned form (`TestTheGuardActuallyCatchesViolations.
   test_catches_a_new_unclassified_promise_literal` uses a synthetic `_render_comms_new`) — no new
   pin needed for the probe itself.
2. **Extend `TestTheScanReachedEveryCommsRenderHelper`'s `expected` set** with
   `_render_comms_send`, `_render_comms_drain`, `_render_comms_ack` (defence-in-depth: today a
   prefix-rename is caught by `test_no_dead_registry_entries` going RED on the orphaned classified
   literals — triple coverage, but the reach set is the CHECKED-variable instrument and must not
   silently exclude the new surface).

**Entry-check corollary confirmed:** every `_render_comms*`/`_comms_*` def in the package lives in
`server.py` (package-wide grep, one file hit, 2026-07-23) — the #145 STOP condition ("renders have
moved") is not met.

---

## S2 — #145 disposition: ACCEPT the location constraint and GATE it (two pins); the scanner generalisation stays #145's own design work, bounded with a re-open trigger.

**RULING.** Option (a)+(c) hybrid. Option (b) — generalising the three path/prefix-keyed scanners —
is REFUSED inside 03b: #145 itself records that the real fix is design work ("stop enumerating
where renders are FORBIDDEN to live") and per the routing rule it must not reach a builder as
"make coverage general" mid-packet. What 03b ships is the loud gate that makes the convention
un-breakable silently:

- **Pin A (moved-file half):** package-wide `rglob` AST pin — NO function named
  `_render_comms*`/`_comms_*` exists outside `server.py`. Fails naming file:function. (Follows the
  `test_render_seam_pins.py` rglob idiom, which already walks the package.)
- **Pin B (renamed-helper half — coverage as a CHECKED variable):** build the module-local call
  graph of `server.py`; starting from every prefix-named function (the comms handlers and render
  helpers are all prefixed), any function transitively REACHABLE through local calls that itself
  contains a `render_line`/`render_join` call MUST carry the scanned prefix. A render-verb call
  reachable from the comms surface inside a non-prefixed function FAILS LOUD naming
  file:function:line. This closes the exact door the negative control in S1 demonstrates — at the
  only place it matters, reachability from the served surface — without a name-list of forbidden
  homes.
- **Both pins ship with synthetic self-attack controls** (drive each checker over violating source
  and assert it fires; positive control over compliant source — the 02a probe-needs-a-control
  idiom, and the checkers must delegate to ONE shared walker, never re-walk privately).

**The residual bound, recorded per PIN-THE-MISS:** a correctly-shaped comms render served by a
DIFFERENT tool's handler path (not reachable from a prefixed function) remains invisible to
Pin B — that is #145's true generalisation (type-keyed or runtime-tagged coverage) and stays
ledgered there. **Named re-open trigger:** the day a comms render legitimately needs to live
outside `server.py` (a server split, or a non-comms tool serving comms-graph content), the
generalisation lands FIRST — until then the constraint BINDS packets 04–06 as well (`_comms_footer`
in packet 04 is already prefix-named and must land in `server.py`; write that into 04's brief).

---

## S3 — #143 adjudication: the committed pins + the template vocabulary structurally exclude the 7b shape for every NEW registered promise. The bound STAYS OPEN with #143 as trigger; two cheap static strengthenings land in 03b; the bare-`{...}` trigger is never pulled because the composition idiom never needs it.

**RULING, part 1 — adjudication.** The 7b defect shape (finding #143) requires a fixture-value-
specific marker AND a sibling VARIANT of the same message family whose render under different
fixture values is textually disjoint. Adjudicated per new registered promise (markers read from
the committed `_PROOF_LIST` at `6a66671`):

| new promise | marker | sibling-variant hazard? |
|---|---|---|
| send directive trailer `recipients must ack: …` | full-line, seq-bearing | none — no variant family; no other template contains the prefix |
| peek header `peeked … nothing stamped …` | value-free suffix | sibling (`drained …` header) can never contain "peek" — structurally disjoint |
| drain elision `+{more} more unread — re-run with limit=` | **value-free** | none; `no unread messages` shares only the word "unread", not the marker |
| `ACK REQUIRED: {seqs} — …` | seq-bearing prefix `ACK REQUIRED: #71` | no sibling variant exists; no other template contains `ACK REQUIRED` |
| ack unknown-seq teach | value-free suffix | none |

The only same-family variant pairs in the new vocabulary (send receipt ± `(+{more} more)` /
broadcast; drain row ± refs) are **promise-FREE structural templates** — they carry no proofs,
hence no markers, hence no 7b surface. **The committed pins deliver; #143's general instrument is
NOT built in 03b.** `TestMarkerCrossSatisfactionBound` stays pinned as-is; #143 remains its named
re-open trigger.

**RULING, part 2 — two static strengthenings (03b contract, cheap, permanent):**
1. **Marker–vocabulary disjointness meta-test:** no proof's marker may be a substring of any OTHER
   classified template literal (registry ∪ free). Static, no rendering, converts the adjudication
   table above from a one-time analysis into a standing gate against future template additions
   that create overlap. (It does not replace #143's dynamic check — a marker could still match a
   sibling's INSTANTIATED render — but it kills the cheap textual half of the class.)
2. **Placeholder-only ∀-ban:** `assert all(_has_literal_text(t) for t in _classified())`. The
   existing value-carried-promise bound pin
   (`TestSafeStrLiteralCoverageBound.test_KNOWN_BOUND_a_promise_carried_in_a_render_VALUE_is_not_inspected`)
   asserts only `"{msg}" not in _classified()` while its docstring bans the whole placeholder-only
   CLASS — a message promising a check the assertion does not perform (the P2 false-gate class,
   found live in the committed contract; flagged as Residual 5). The ∀-form enforces the docstring.

**RULING, part 3 — the ordering question.** The bound must close (extend the scan to literal kwarg
VALUES) BEFORE any placeholder-only template is classified — and the correct move in 03b is that
**no such classification ever happens**: the drain/send/ack renders compose exactly as
`_render_comms_fleet` does — build a `list[Rendered]` of `render_line(...)` lines and join them —
which needs no bare `{...}` template anywhere (verified against the shipped fleet composition,
2026-07-23). The builder brief carries this as a constraint, part 2's ∀-pin makes a violation RED,
and the bound's re-open trigger is therefore never pulled in this packet. (Builder note, same
idiom: branch-selected templates use the duplicated-call form, never a ternary between two
literals — the template-literal AST pin requires `args[0]` to be an `ast.Constant`; see the
comment inside `_render_comms_fleet`.)

---

## S4 — THE SERVED SHAPES (binding; a builder must not improvise any of this)

The committed classified vocabulary at `6a66671` is CONFIRMED as the render law's concrete form —
the ack-nudge trailer is `acked_at`-keyed, queue counts are `seen_at`-keyed and say "unread"
(03a2-R6's render law, inherited delta row 4). Three additions close gaps between that vocabulary
and the inherited rulings; each addition is a contract-phase edit (new template + classification +
proof + hostile fixture + injection case where a caller-controlled field enters).

### S4.1 `send` confirmation (`_render_comms_send(result, *, broadcast, session)`)
- Receipt line (committed, promise-free): `sent #{seq} [{grade}] → {recipients}`; recipient names
  sanitised, comma-joined, capped at the SHARED names-list cap (`_COVERAGE_NAMES_CAP`, reused —
  ONE display-cap policy, mutation-shared: changing the constant must move both surfaces' pins);
  over-cap uses the committed `(+{more} more)` variant with the TRUE remainder. Broadcast uses the
  committed broadcast variant with the true fan-out count.
- Directive trailer (committed, registered): `recipients must ack: lore_comms action=ack
  seqs=[{seq}]` — emitted IFF `grade == "directive"`.
- **NEW — the question teach (this ruling):** one line, emitted IFF `result.message.question is
  True` (typed applicability — the flag the ledger already stores; never a `set_status` string
  comparison in the render):
  `awaiting an answer on thread '{thread}' — cleared by any teammate's on-thread reply delivered
  to you; your own sends never clear it`
  This is 03a2-R2's fourth conjunct and 03a2-residual-8's clearing-rule teach, served at the ONE
  moment it becomes true. Registered promise + emit/no-emit proof (emit: `question=True`; no-emit:
  `question=False`, same fixture otherwise). ⚠ It introduces `thread` (caller-supplied) into the
  send render → **a `send.thread` RenderCase is MANDATORY** in the injection battery (the
  committed battery has only `send.recipients`/`send.sender`).

### S4.2 `drain` (`_render_comms_drain(result, *, agent_name, limit)`)
Composed top-to-bottom: header · rows · trailers · elision. All lines joined as `Rendered`.
- **Header** (committed): stamping drain → `drained {shown} of {total} pending`; peek →
  `peeked {shown} of {total} pending — nothing stamped; re-run without peek=true to mark them
  seen`. `shown = len(entries)`, `total = total_pending` (seen-keyed; "pending" is ack-NEUTRAL
  wording and is ruled consistent with the render law — the banned word is "unactioned").
- **Rows** (committed): `#{seq} [{grade}] {sender}→you{context}: {body}` (+ refs variant). The
  `{context}` cell is SINGULAR with fixed precedence: `task_id` present → ` (task {task_id})`;
  else `thread != session` → ` (thread {thread})`; else empty. Body/sender/thread/refs all route
  through the shared sanitiser seam; hostile fixtures (newlines + row-shaped forgery + backtick
  runs) are mandatory per standing law and already committed as battery cases.
- **`ACK REQUIRED` trailer** (committed, registered — WITH A KEYING FIX): emitted IFF ≥1 SERVED
  row has `grade == "directive"` AND `acked_at is None`, and it lists ONLY those seqs. ⚠ **The
  committed proof fixtures are an acked_at monoculture (`acked_at=None` everywhere): a build
  keying on grade alone passes both proof legs.** The discriminating pin is MANDATORY: a served
  directive row with `acked_at` set → trailer absent (or that seq absent) — this is the render
  law's clause 1 ("an acked directive never re-nags") enforced on 03b's own surface, not just
  04's footer.
- **NEW — `ALREADY ACKED` trailer (this ruling):** `ALREADY ACKED: {seqs} — no action owed`,
  emitted IFF ≥1 served row has `acked_at is not None`. This is what makes 03a2-R6's accepted
  anomaly ("a re-served acked message is self-explanatory in the render") TRUE at the render
  layer — as committed it was true only of a MODEL field the consuming LLM never sees (over MCP
  the render IS the surface, DESIGN-LAW §1.6; predecessor correction, stated loudly: 03a2-R6
  clause 3 over-claimed). Registered promise + proof; marker full-line; textually disjoint from
  the ack receipt's lowercase `already acked: {seqs} — no new stamp` (S3 meta-test 1 will hold
  them apart permanently). The R6 convergence pin (inherited delta row 8) asserts this trailer,
  the row's presence, its counting in `total_pending`, and the stamp-on-serve convergence.
- **Elision** (committed, registered): `+{more} more unread — re-run with limit={next_limit}`
  with `more = total_pending − shown` and **`next_limit = more`** — NOT fleet's `shown + more`:
  stamped rows never re-serve, so the honest re-ask is the REMAINDER (a builder copying fleet's
  arithmetic ships a dishonest re-ask; pin the arithmetic with a docstring naming the contrast).
  No drain display-cap exists and none is added (the caller-set `limit` is the only bound; the
  committed vocabulary has no cap-disclosure variant, deliberately).
- **Peek rule (binding):** trailers (`ACK REQUIRED`, `ALREADY ACKED`) and the elision line render
  on STAMPING drains ONLY. A peek serves header + rows, nothing else — its header already
  discloses `shown of total`, and an ack demand on a peek MANUFACTURES the R6 peek→ack anomaly
  the render law exists to contain. Pin: a peek over a directive entry contains no `ACK REQUIRED`.
  (Consistent with the committed proofs — none drives a trailer under peek — and with the
  committed registry description, whose emission reason presumes stamping.)
- **Empty** (committed): `no unread messages`.

### S4.3 `ack` confirmation (`_render_comms_ack(result, *, agent_name)`)
Group-lines in FIXED order — acked · already-acked · not-addressed · unknown — seqs within each
group in REQUEST order (the ledger result is per-seq request-ordered; the render groups without
re-sorting). All four templates are committed:
`acked {acked} of {requested}: {seqs}` · `already acked: {seqs} — no new stamp` (this IS
03a2-R1's duplicate-occurrence teach — honestly undistinguished between listed-twice and
acked-earlier, per R1) · `not addressed to you: {seqs} — these messages carry no delivery to
{name}` · the registered unknown-seq teach. `note=` is accepted and stored; it gets NO
confirmation line (no committed template; the note lands on the edge and is story/packet-04
material — recorded as deliberate, not forgotten).

### S4.4 What 03b does NOT render (scope guard)
No unread counts on register/heartbeat renders, no `_comms_footer`, no fleet unread/directive
columns — the counts family is packet 04's, and the committed 03b contract demands none of them.
The render law rows (inherited delta row 10) bind 04's contract author when they land.

---

## S5 — the INSTRUCTIONS block (served text, ruled verbatim) + derived-teach pins

A new COMMS paragraph in `_INSTRUCTIONS` (the existing MEMORY paragraph keeps its current
lore_comms sentence for register/heartbeat/brief/fleet; teaching the message verbs there would
crowd it):

> COMMS: lore_comms is the fleet's durable mailbox. action=send delivers to named agents (to=[]
> broadcasts to all non-retired); grade=signal is fire-and-forget, grade=directive demands an ack;
> bodies cap at 2000 chars — put content in a report/finding and pass refs. action=drain pulls
> YOUR inbox and stamps what it serves as seen (peek=true looks without stamping); action=ack
> seqs=[...] discharges directives. Threads carry conversational debt: ONE thread carries ONE open
> question — any teammate's on-thread reply delivered to you discharges it, so separate questions
> take separate threads, and a partially-answered question is re-established by RE-ASKING on its
> thread. Your own sends never clear your own question.

This is inherited delta row 9 (one-thread-one-debt + re-ask recovery, taught STATICALLY — the
send-time thread-scan stays REFUSED per 03a2-R5) plus 03a2-R2's self-answer clause, phrased from
the ruled behaviour. Two pins:
1. **Mechanism-exists ∀-pin (derived, not prose-matched):** every `action=<x>` token in
   `_INSTRUCTIONS`' comms text names a key of `_COMMS_ACTIONS` — a retired or misspelled verb in
   served teaching goes RED mechanically (the
   `TestTheFirstVersionLineTeachesAnAckMechanismThatACTUALLYEXISTS` family, generalised).
2. One content pin asserting the thread-debt clause is present (exact-substring on the clause's
   stable core, e.g. `separate questions take separate threads`).

---

## S6 — telemetry, RE-RULED (v2, 2026-07-24) for the operator's all-tools widening: ONE seam, ONE writer, global sequence; the v1 comms-call counter is RETIRED.

> **v1 of this section (2026-07-23, drain-only) is SUPERSEDED — not wrong at the time, wrong
> premise now.** Its diagnosis of #147 STANDS and was independently corroborated (scout report
> above: same verdict via bare grep + the deployed artifact + a positive control writing 3 rows
> through the real `record_trace` on TEST `:18000` and reading them back through the real
> `trace_aggregates` — write and read sides both proven live). Three v1 items are RETIRED below
> with reasons: the `comms_calls` agent-row counter, the handler-side write, and the drain-render
> failure-notice line.

**Why v1's ordinal was insufficient (conceded, and the concession generalises):** a comms-call
ordinal freezes the moment the agent stops touching `lore_comms` at all — which is the PREDICTED
decay mode. It was the absence-writes-no-rows problem one level in: drain ordinals `[1,2,3]`
against a frozen counter cannot distinguish "3 drains in 5 tool calls" from "3 in 300". The
denominator must be the agent's WHOLE tool-call stream — hence all-tools tracing (operator-ruled;
the scout's §5.1 derivation is adopted).

**RULING — the v2 design:**

1. **ONE seam, receiver-blind:** subclass `FastMCP`, override `call_tool` (two-line SDK body,
   measured: `get_context()` + `_tool_manager.call_tool` delegate), delegate to `super()` inside
   a timed `try/finally`. One-line instantiation swap in `build_mcp_server` (`FastMCP(...)` →
   `TracingFastMCP(...)`). EVERY tool dispatch — current and future packets' — passes through by
   construction: coverage by seam, never by enumeration (the six-defeats frame). The installed
   `mcp` 1.27.2 has NO middleware API (scout, measured) — so hand-rolling this gap is the
   packages-rule's side 2 working as intended: minimal surface, delegating bridge, nothing
   re-implemented. **The standalone `fastmcp` migration (which has `on_call_tool` middleware) is
   REFUSED inside 03b** — a whole-transport dependency swap is its own ledger item; named
   triggers: an SDK bump breaks the override's seam, OR a second middleware-shaped need appears
   (two call sites needing one policy = the decision point).
2. **ONE writer — the seam.** Handlers never call `record_trace`. Every dispatch writes ONE row,
   awaited, AFTER the tool returns (errors included — `try/finally`; an errored pull is still a
   pull) and before the result is returned. Row fields from the seam: `tool` (the dispatched
   name), `caller` (S7's identity key), `seq` (below), `params_hash` (stable digest of the
   arguments dict — a HASH, so message bodies never enter the trace, private by construction),
   `latency_ms` (wall-to-wall around `super().call_tool`, render included — labelled as such).
3. **Domain enrichment via a request-scoped annotation channel, allowlist-keyed:** the seam mints
   a fresh annotation dict in a `ContextVar` per dispatch (reset by token in `finally`); the
   comms dispatcher — today's only annotator — contributes through ONE narrow helper whose key
   set is CLOSED: `agent` (str of the resolved agent RecordID), `session` (the explicit fleet
   session), `hit_count` (drain: served count), `pending` (drain: `total_pending`), `peeked`
   (drain). An unknown key RAISES (deny-by-default at the merge — never a silent placeholder,
   DESIGN-LAW §15). The seam folds annotations into the single row. This keeps ONE writer while
   letting the one tool with domain knowledge enrich — without a name-keyed "tools that
   self-record" exemption list, which would be the defeat class.
4. **`seq` (the packet's "monotonic call ordinal") = ONE GLOBAL native sequence:**
   `DEFINE SEQUENCE IF NOT EXISTS trace_seq` (bare DEFINE raises at boot — store reference §1.1
   SEQUENCE row; #146's BATCH/START migration residual: set neither), minted by
   `sequence::nextval("trace_seq")` INSIDE `record_trace`'s CREATE statement — every writer mints
   by construction, no drift possible. Global monotonic ⇒ per-agent monotonic by restriction, AND
   the global interleaving survives (a per-agent counter destroys it). Gaps are fine — `seq` is
   an ORDERING key, never a count (same law as `message.seq`); "calls between drains" is a row
   COUNT, not seq arithmetic. `ts` is not a substitute (ties, clock skew — scout, confirmed).
   **RETIRED: v1's `comms_calls` field on `agent`.** Under per-caller attribution it is not
   complementary but REDUNDANT — comms-relative position = filter the caller's attributed rows on
   the tool name and rank by `seq`, derivable at analysis time. A stored counter beside a
   derivable one is two numbers that must agree — the #102 clone shape. The `agent` schema is
   untouched by 03b.
5. **Schema delta (`_TRACE_FIELD_SPECS`; prod table EXISTS and holds ZERO rows — scout probed
   `:18500` read-only; every field lands via the house `DEFINE FIELD OVERWRITE` per §1.1):**
   - NEW: `caller option<string>` · `seq int` · `agent option<string>` · `pending option<int>` ·
     `peeked option<bool>`. The last three are comms/drain-only and their spec comments SAY SO
     (most rows will hold NONE — that is the design, not drift). `caller` is schema-`option` for
     the store layer's own probes but seam-written on EVERY row — presence is enforced by pin,
     not by the schema.
   - LOOSENED: `session` string → `option<string>` (generic calls carry no fleet session; ONLY an
     explicitly-known comms session is recorded — the caller key NEVER goes here, per the scout's
     no-overloading rule, adopted: `trace.session` stays the documented fleet identity).
     `hit_count` int → `option<int>` (the generic seam records NONE — an honest unknown; a
     seam-derived "content block count" proxy is REFUSED as a lying metric; drain annotates its
     true served count).
   - UNCHANGED + RULED KEPT: `token_cost`/`model` (zero writers — scout residual 3). Dropping
     them costs MORE than keeping: deleting spec lines does not remove the store's existing field
     definitions (`ensure_ready` has no REMOVE mechanism, and inventing one mid-packet is new
     migration machinery in #107 terrain) plus signature/test churn. They stay, UNWIRED, with a
     spec comment + `record_trace` docstring line: *zero writers by design (the P8d accounting
     phase was never wired); re-open trigger: the day per-call token accounting is wanted —
     `option<>` columns backfill-safe per §1.4.* Not wired in 03b.
   - NEW INDEX: `_plain_index(TRACE_TABLE, "trace_caller_seq", ("caller", "seq"))` — packet 06's
     per-caller ordered reads. The free-window argument applies HERE too and expires at 03b's
     deploy: the prod table is empty today; the same line shipped later builds over months of
     all-tools rows at boot (§1.5).
6. **Failure posture (uniform, replaces v1 item 3):** the seam AWAITS the write; on failure it
   catches, logs loudly server-side, and returns the tool result UNMODIFIED. **v1's drain-render
   notice line is STRUCK** — the seam writes after the handler returns and cannot reach into the
   render, and a seam that mutates arbitrary tool outputs would break every other tool's pinned
   render shapes. Never fail a call for telemetry; never fail silently — systemic failure is
   caught by the receipts below; a transient per-call gap is noise in a curve and is ACCEPTED as
   a named bound. REFUSED: fire-and-forget (re-creates #147's silent zero); REFUSED: telemetry
   inside the ledger's stamp transaction (a surface concern inside `messages.py`'s settled,
   frozen-contract semantics).
7. **Receipts (anti-#147/#131, all mandatory):**
   - **Coverage as a CHECKED VARIABLE** (scout §5.4's shape, CONFIRMED with refinements): a pin
     that derives the tool list from the server's OWN registration (never a hardcoded list),
     drives EVERY tool once through the real dispatch seam against fakes, and asserts
     observed-traced-names == registered-names as SET EQUALITY. Mutation-proven: remove the
     emission, watch it go RED. Plus an error-path leg (a raising tool still writes its row) and
     an annotation-leak control (two sequential calls; the second row is unannotated).
   - **[real]-leg row pin:** dispatcher drain → SELECT the trace row; `caller`/`seq`/`agent`/
     `pending`/`peeked`/`hit_count` all present and correct.
   - **Deploy smoke:** post-deploy, one live drain + one live search → `lore_index` serves
     `traces.total ≥ 2` with BOTH tools in `by_tool` — proving GENERIC coverage in the ARTIFACT,
     not just the comms leg (test-environment-is-a-fiction law). This also makes `lore_index`'s
     served *"per-tool trace-call aggregates"* description TRUE for the first time — the scout's
     residual 2 is resolved by the widening, no wording qualification needed.
8. **Scope fences (unchanged from v1):** no forced-drain logic, no decay analysis, no
   thresholds — packet 06 decides on the CURVE. **#175 exposure: NONE** (a trace CREATE is not an
   edge write; v1's agent-row UPDATE is retired). Retention is upgraded from "negligible" to a
   NAMED decision point — see Residual 4.

**#147 disposition:** resolve at 03b close citing the two independent diagnoses (this doc §S6 +
the scout report) and the receipts in item 7; the emission's first caller is the seam, covering
every tool.

---

## S7 — caller identity at the generic seam (the invented property), self-attacked

**The problem:** only `lore_comms` carries `agent=`; the generic seam sees no identity, and
without a per-caller key there is no per-agent denominator. Measured facts (scout §5.3.4 +
my own SDK reads, 2026-07-24): `Context` exposes `client_id` / `request_id` / `session` (the
`ServerSession` OBJECT — no plain id string); streamable-http carries an `mcp-session-id` header;
lore instantiates `FastMCP` WITHOUT `stateless_http` (default `False` — verified in
`build_mcp_server`), so the SDK retains ONE `ServerSession` per MCP session across its requests.
*(Both mentions in this doc originally said `build_server` — a wrong symbol, caught by the
contract author 2026-07-24 and corrected in place; the prose-vs-code class, in this doc.)*

**RULING — the key, the join, and their separation:**
1. **`caller` is a TRANSPORT-SESSION key, not an agent key** — the two concepts are kept apart
   and JOINED BY DATA. The key: a server-minted opaque uuid per `ServerSession` OBJECT, held in a
   `WeakKeyDictionary[ServerSession, str]`, minted on first sight in the seam. Object-keyed
   rather than header-keyed because it is transport-uniform (streamable-http AND stdio — the
   header does not exist on stdio) and server-minted (trusted charset by construction — never
   caller-supplied text, no injection surface; sanitise anyway at any future render).
2. **The join is derivable from the trace rows themselves — no binding table, no extra writes:**
   every comms row carries BOTH `caller` (seam) and `agent` (annotation), so caller↔agent
   binding falls out of the data; a caller's generic rows attribute to the agent its comms rows
   name. The register-first spawn protocol means a fleet agent's FIRST lore call binds its key.
3. **The measurement that selects the rung (a measurement under a stated rule — 03a2-R3's idiom,
   not a design delegation):** the builder proves against the REAL streamable-http transport
   (in-process test client): same session ⇒ same `caller` on consecutive calls; different
   sessions ⇒ different `caller`s. **If** the SDK turns out to mint the session object
   per-REQUEST (the one fact I could not settle read-only), the fallback rung is the
   `mcp-session-id` header read via `request_context` — same key semantics, streamable-http-only,
   with the stdio gap documented. Both rungs are designed here; the measurement selects; the
   contract pins whichever ships (with both a same-key and a different-key control).

**The self-attack (required by the routing law; run before shipping):**

| attack | outcome |
|---|---|
| key collides across sessions | uuid-minted per object / server-minted header — no collision path |
| key unstable WITHIN a session | the pin in (3) — RED if it ever regresses |
| reconnect fragments one agent across keys | HANDLED BY THE JOIN: the agent's next comms call re-binds the new key; orphaned unattributed tails are VISIBLE (rows with a caller no comms row names) and packet 06's analysis MUST report attribution coverage as a number — coverage as a checked variable at the analysis layer, so the gap can never be silent |
| one key carries MANY agents (Task-subagents sharing a parent process's connection) | comms rows stay EXACTLY attributed (explicit identity); generic rows pool at process level; the analysis flags multi-agent keys. The fleet pattern this subsystem serves (teammates = own processes = own connections) attributes cleanly; the pooled case is a stated bound, not a silent lie |
| someone flips `stateless_http=True` later (key degenerates to per-request) | the same-key pin from (3) goes RED — the guard is behavioural, not a config assert |
| the WeakKeyDictionary entry dies mid-session | the weak key dies only with the session object; if it ever did, the key would CHANGE (= fragmentation, handled above), never corrupt |
| a wrong build mints a fresh key every call | indistinguishable from stateless degeneration — caught by the SAME pin |

**REFUSED:** requiring `agent=` on every generic tool (a fleet-hostile API break far beyond 03b);
a server-side registry mapping keys to agents as a SECOND store surface (the join is already in
the rows; a mutable map is a cache that can lie); using `client_id` (client-declared, not
per-process-unique) or `request_id` (per-request) as the key.

**[SETTLED 2026-07-24, contract phase]:** the S7(3) measurement ran — `mcp` 1.27.2 mints ONE
`ServerSession` per MCP session → **rung 1 selected; the header fallback rung is retired
unused**, and the decision rule stands as a permanent pin that goes RED if an SDK bump changes
the retention.

---

## S8 — contract-phase escalation rulings (2026-07-24; E2/E3 routed here by the lead)

**E2 — the unknown-annotation-key raise happens at the `_annotate_trace` CALL (reading A),
CONFIRMING the author's pin. Zero pins re-authored.** The structural argument is decisive and is
hereby made part of S6v2 item 3's meaning: **the guard must live OUTSIDE the seam's
catch-log-serve envelope, or it swallows itself** — a merge-time raise (reading B) lands inside
item 6's telemetry-error catch and degrades deny-by-default to a log line, a green gate over a
dead mechanism. At the call site the raise surfaces as a TOOL-CALL failure — loud in every test
that exercises the handler, atomic (no partial annotation), and it names the offending line. The
threat model (stated per repo law): the HONEST DEVELOPER — e.g. a packet-04 author annotating
`unread_count` without extending the closed key set — who enters through the one documented
helper and is caught there. **The residual door, adjudicated rather than ignored:** code that
bypasses the helper and mutates the ContextVar dict directly is deliberately-unusual code — per
the gate-threat-model law it is LEDGERED as a bound, not paid for in false positives. The seam's
fold MAY additionally verify keys ⊆ allowlist as a second belt; that check is allowed to be
log-only precisely because it is the belt, not the guard. Re-open trigger: a second annotator
module (packet 04's footer) lands — re-verify the helper is its entry point.

**E3 — `seq int` (non-`option`) is UPHELD, overruling the lead's lean, with the bound the author
recorded now strengthened.** The lead's §1.4/#107 concern is legitimate and was weighed; it
loses on three grounds:
1. **The empty-table premise is CODE-DERIVED, not fixture-derived:** `record_trace` has had ZERO
   production callers in ANY shipped image, ever (scout §2, source + deployed artifact) — so no
   lore deployment ANYWHERE can hold organic trace rows. This is not a virgin-fixture fiction;
   it is archaeology over every writer that has ever existed.
2. **Even on a hypothetical dirty store the failure is bounded, non-destructive, and
   non-silent-at-write:** §1.4's poisoning bites only on UPDATE of an old row — and trace rows
   are append-only BY DOCUMENTED DESIGN (`record_trace` docstring), with the author's named
   re-open trigger ("the day anything UPDATEs a trace row, or any store is found carrying
   pre-03b trace rows") covering exactly that day.
3. **`int` buys a STANDING mechanical guard `option<>` cannot:** the schema rejects any FUTURE
   writer that omits the mint — guarding the TABLE including write paths nobody has written yet
   (the same argument the store reference makes for `ENFORCED`). A presence PIN guards only the
   paths it drives; the schema guards them all. Instrument over hope.
   **One strengthening, required:** the pin's docstring must also record that on a hypothetical
   dirty store, READS of old rows serve `seq = None` regardless of the schema (§2's
   silent-None-projection law — `TYPE int` does not retro-fill), so packet 06's analysis treats
   `seq is None` as "pre-03b row" defensively. That line makes the bound honest on the READ side
   too, which neither the `int` nor the `option` choice changes.

**Store-reference routing rule (for the author's new probed SurrealQL fact — the lead lands
it):** if the vendor documents the OPPOSITE of the probed behaviour → §6 (a new numbered
falsehood, + a one-line pointer from the practical section it affects); if the vendor is SILENT
→ the practical section (§2 DML / §5 concurrency / §7 syntax, wherever a user would look first)
tagged `[PROBED 2026-07-24, 3.2.1]`, PLUS a line in §6.6's "claims for which WE are the only
source" list. Either way it carries the engine version per §0's provenance-honesty note. A
probed fact that stays only in a report is how #107 happened — landing it is part of the wave,
not cleanup.

---

## Residuals & flags (everything surfaced; the lead owns disposition)

1. **Drain rows do not mark `question=true` messages** — an inbox row that ASKS renders like any
   other. The clearing-rule teach lands on the SENDER side (S4.1) and statically (S5); the
   recipient-side per-row marker needs `question` added to `InboxEntry` — an ORACLE + model
   change (two-suite blast radius per inherited delta row 6) for a teach packet 05's await/story
   work will re-shape anyway. **DEFERRED to packet 05 with a named decision point:** when 05
   designs `await`/`story`, it MUST re-adjudicate drain-row question visibility (this line is the
   pointer). Not silent scope-narrowing — a priced deferral; lead may carry to the operator.
2. **[RESOLVED 2026-07-24 by the operator's scope widening — not deferred.]** v1 flagged
   "`record_trace` stays unwired for every other tool" as a candidate follow-up; the operator
   ruled it IN 03b (all-tools tracing, S6v2). Kept for the record of how the scope moved.
3. **The ACK REQUIRED proof monoculture** (S4.2): committed emit/no-emit fixtures never set
   `acked_at` on a directive, so a grade-only build passes the committed proofs. Closed by the
   mandated discriminating pin. This is a fixture-monoculture instance FOUND in the committed
   contract — the contract-adversary's P2 fixture-perturbation should confirm the fix wave.
4. **Trace rows have no retention policy — UPGRADED under all-tools cadence (2026-07-24).** Every
   lore call now writes a row: a heavy session is O(10²–10³) rows; a year is plausibly O(10⁵–10⁶)
   — fine for RocksDB, but `trace_aggregates` is a full-table GROUP BY on a status surface. NOT
   built in 03b (no GC in scope). **Named decision point:** when `traces.total` crosses ~100k or
   `lore_index` latency becomes visible, the packet then touching observability rules retention
   (CHANGEFEED-style window, periodic prune, or rollup rows). Until then the growth is honest and
   bounded by call volume.
5. **The value-carried bound's pin under-enforces its own docstring** (`"{msg}"`-only assert vs a
   class-wide ban) — the P2 false-gate class, live in the committed contract; closed by S3's
   ∀-ban pin.
6. **The reach-pin `expected` set omits the three new helpers** — S1 instrument item 2.
7. **`send.thread` has no injection RenderCase** in the committed battery — mandatory with S4.1's
   question line (which puts `thread` into the send render for the first time).
8. **Global mypy-zero (36→0)** is structural: the errors are the RED contract's forward refs to
   `_render_comms_*`/`comms(...)` kwargs; building S4's surface pays them. Nothing to rule; named
   so it is not re-litigated.
9. **Heartbeat/register unread counts intentionally absent from 03b** (S4.4) — recorded so their
   absence reads as scope, not omission; packet 04 owns the counts family under the inherited
   render law.

## Consolidated implementation delta (for the lead's 03b briefs; rows 1–11 of 03a-2's table remain binding and are NOT repeated)

| # | where | change | ruling |
|---|---|---|---|
| A | 03b contract (`test_comms_promise_registry.py`) | reach-set + the two S2 gate pins (rglob no-stray-prefix · reachable-render-verb prefix check, both with self-attack controls) | S1/S2 |
| B | 03b contract (same file) | marker–vocabulary disjointness meta-test · placeholder-only ∀-ban (`_has_literal_text` over `_classified()`) | S3 |
| C | 03b contract + `server.py` | send question-teach line (registered + proof, emit-IFF `message.question`) · `send.thread` RenderCase | S4.1 |
| D | 03b contract + `server.py` | `ALREADY ACKED: {seqs} — no action owed` trailer (registered + proof) · ACK-REQUIRED acked_at-keyed discriminating pin · elision arithmetic pin (`next_limit == more`) · peek-serves-no-trailers pin · context-cell precedence | S4.2 |
| E | `server.py` `_INSTRUCTIONS` + contract | the COMMS paragraph verbatim · action-token ∀-pin · thread-debt content pin | S5 |
| F *(v2)* | `store/surreal_schema.py` `_TRACE_FIELD_SPECS` | + `caller`/`agent`/`pending`/`peeked` `option<>` + `seq int` · `session`/`hit_count` → `option<>` · `DEFINE SEQUENCE IF NOT EXISTS trace_seq` · `_plain_index(trace, "trace_caller_seq", ("caller","seq"))` (free window, expires at deploy) · `token_cost`/`model` KEPT with zero-writers-by-design comments · `agent` TABLE untouched (v1's `comms_calls` RETIRED) | S6v2 |
| G *(v2)* | `server.py` | `TracingFastMCP(FastMCP)` overriding `call_tool` (timed try/finally, awaited `record_trace`, catch→loud-log→serve-unmodified — NO render notice) · one-line instantiation swap · ContextVar annotation channel with CLOSED key set (`agent`/`session`/`hit_count`/`pending`/`peeked`, unknown key raises) · comms dispatcher annotates via the one helper · S7 caller-key ladder (WeakKeyDict-minted uuid per `ServerSession`; header fallback rung per the S7 measurement rule) | S6v2/S7 |
| H *(v2)* | 03b contract + deploy smoke | coverage-as-checked-variable pin (registered-set == traced-set, derived never hardcoded; mutation-proven; error-path leg; annotation-leak control) · same-key/different-key session pins (both controls) · `[real]`-leg drain row pin (all enrichment fields) · smoke: live drain + live search → `traces.total ≥ 2`, both tools in `by_tool` | S6v2/S7 |
| I | — | no change: no drain display cap · no ack-note confirmation line · no per-row question marker (→ packet 05, Residual 1) · no forced-drain anything (→ 06) · no `fastmcp` package migration (own ledger item, named triggers) · no retention/GC (Residual 4's decision point) | S4/S6v2 |

## Tool honesty

`lore_index()` freshness-checked first (branch/ref matched HEAD; sweep 5 min old). Findings read
via `lore_findings get`. File reads were spec-pointed (paths supplied by the brief). Greps were
used for: test-name/class maps, template-literal and marker locations, `record_trace` call-site
enumeration, and the package-wide prefix sweep — all non-symbol textual seams or
exhaustiveness-critical sweeps, the honest-grep categories; said so here. The S1 probe executed
the REAL scanner functions in memory (no file mutation, no suite run). No lore friction
encountered; nothing filed.
