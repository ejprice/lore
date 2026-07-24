# 03b design rulings — r2 (blind re-derivation)

**Author:** design-blind-03b (Fable design author, deliberately blind to the struck 03b
corpus — spawned 2026-07-24). Derived FRESH from trusted sources only; never read the
struck rulings doc, the struck receipts (except the permitted scout report), any
`REPORT-*.md` at repo root, `INDEX.md` at HEAD, or any commit content after `0223291`.
**Read at:** production working tree at `6bfe820` (production sources verified unmodified
by the struck session — the struck session touched only tests/docs); all doc/contract
reads via `git show 0223291:<path>`.
**Authority:** design rulings for packet 03b under the comms design-authority delegation
(03a-2 rulings header); items marked OPERATOR-AUTHORIZATION-REQUIRED or FORK are
escalations, not rulings.
**Sources (cited per ruling, never re-transcribed):**
`git show 0223291:` → `docs/plans/v2/03b-comms-message-surface.md` (the packet) ·
`docs/plans/v2/comms-subsystem.md` · `docs/plans/v2/03-comms-message-graph.md` §Kickoff
rulings · `docs/plans/v2/03a-2-consume-path-design-rulings.md` (R1–R6, binding) ·
`docs/reference/surrealdb-31-capabilities.md` (store law — read FIRST, per repo law) ·
`loremaster/tests/test_comms_tool.py` + `test_comms_promise_registry.py` +
`test_surreal_store.py` (the committed, trusted contract). Working tree:
`docs/plans/v2/DESIGN-LAW.md` §1/§5/§8/§15 ·
`~/.claude/plans/one-of-claude-codes-nifty-garden.md` (the approved design) · production
code (`server.py`, `messages.py`, `agents.py`, `briefs.py`, `agent_ref.py`, `render.py`,
`sanitise.py`, `store/surreal.py`, `store/surreal_schema.py`) · the installed
`mcp==1.27.2` package source ·
`docs/plans/v2/receipts/2026-07-24-packet03b/REPORT-scout-147-traces.md` (facts only;
its cheap measurements re-verified below).
**Operator rulings postdating `0223291`, transcribed in my spawn brief and binding here:**
(1) telemetry traces EVERY tool call, not drains only; (2) drain-row per-row `question`
markers DEFERRED to packet 05; (3) *"Sonnet 5, opus and fable agents are the consumers of
Lore, not humans. THEY need to be satisfied with 03b… They are the client"* — acceptance
must be checkable; (4) committed-contract immutability stands (amendments strengthen-only,
operator-authorized, mutation-proven).

---

## §0. Entry-state facts (measured 2026-07-24 at working tree `6bfe820`)

Each fact below was independently re-derived this session, not inherited:

- **F1 — dispatcher state.** `AppContext.comms` dispatches six actions through
  `_COMMS_ACTIONS` (`server.py::CommsActionSpec`); send/drain/ack are absent from the
  table and from the `comms()` signature. The committed contract already pins the
  NINE-action exact set (`TestCommsActionsTable._EXPECTED_ACTIONS` at `0223291`) and the
  three new specs (`TestNewActionSpecs`), so the table growth is contract-forced, not a
  choice.
- **F2 — ledger state.** `MessageLedger` (production `messages.py`) ships send/drain/
  ack/awaiting_answer complete. R2's fourth conjunct (`in.sender != $agent`) IS in the
  deliveries SELECT; R4's questions-first order + zero-questions short-circuit IS
  implemented. **R3's bounding conjuncts (`thread IN … AND seq > …`) are NOT implemented**,
  and `_message_statements` (`surreal_schema.py`) carries **neither** `message_seq` nor
  `message_sender_question` index (only `to_in_out` UNIQUE + `to_out_seen_at`). Rows
  2/3 of the 03a-2 delta table are open 03b builder work.
- **F3 — config state.** `CommsConfig` has `fleet_limit` (default 20) and
  `brief_body_warn_chars` (4000) — **no `drain_limit`**, which the committed contract
  requires (`test_drain_defaults_to_the_configured_limit_not_a_hardcoded_one` drives the
  harness's `drain_limit=5` through config).
- **F4 — trace state.** `SurrealStore.record_trace` exists, is correct, and has ZERO
  production call sites (scout report §2, corroborated: `lore_impact` dead-heuristic + a
  bare anchor-free grep this session found only the definition, prose mentions, and test
  call sites). Production `:18500` `trace` table is DEFINED with `count()==0` (scout §3.1;
  not re-probed — production reads are the scout's receipt). `mcp==1.27.2` is the
  installed SDK (verified: `.venv/.../mcp`, version 1.27.2); `FastMCP` has **no
  middleware/hook API** (verified by reading `mcp/server/fastmcp/server.py`: the only
  funnel is `FastMCP.call_tool`, registered once in `_setup_handlers`).
- **F5 — seam probe (this session, with control).** A `FastMCP` subclass overriding
  `call_tool` intercepts (a) direct FastMCP-layer dispatch, (b) the LOWLEVEL wire handler
  registered at `__init__` (`request_handlers[CallToolRequest]` captured the BOUND
  override), and (c) a RAISING tool (the override runs; the error surfaces as
  `ToolError`). Positive control: the un-subclassed base recorded nothing. Receipt in
  `REPORT-design-blind-03b.md` §probes.
- **F6 — committed trace pins are per-key, not exact-shape.**
  `test_surreal_store.py::TestRecordTrace…` at `0223291` asserts individual keys of the
  written row (tool/params_hash/hit_count/latency_ms/session), server-side `ts`,
  optional-column behaviour, and append-only distinctness. None pins the statement text or
  the exact column set — so the T-series schema/signature extensions below are
  **amendment-free** for the committed store contract.
- **F7 — production `:18500` has NO `message`/`to` tables** (scout §6.1). 03b's deploy is
  the first time the message DDL touches a live store.

---

# A. The served surface — send / drain / ack on `lore_comms`

## B1. Action specs, dispatcher wiring, validation order

**RULING.** The three actions land in `_COMMS_ACTIONS` exactly as the committed contract
pins them (`TestNewActionSpecs` at `0223291` — cite, do not re-derive):
`send` params `{to, body, grade, thread, task_id, refs, set_status}` required
`{body, grade}`; `drain` params `{limit, peek}`; `ack` params `{seqs, note}` required
`{seqs}`; all three `requires_registration=True` (the uniform heartbeat touch, one site).
Handlers are `AppContext._comms_send` / `_comms_drain` / `_comms_ack`; renders are
`_render_comms_send` / `_render_comms_drain` / `_render_comms_ack` — **in `server.py`,
under the existing prefix** (packet-03 kickoff ruling 5: three of the five render scanners
are keyed on that path and prefix, #145; a render anywhere else is invisible to the
promise registry and stays green).

The `comms()` tool signature and the dispatcher `values` dict gain
`to: list[str] | None`, `grade: str | None`, `thread: str | None`,
`refs: list[str] | None`, `set_status: str | None`, `seqs: list[int] | None`,
`peek: bool | None` (param honesty is contract-forced:
`test_param_honesty__every_spec_param_is_in_the_tool_signature`). `body`, `note`,
`task_id`, `limit` already exist and are shared per the strict-param law's multi-owner
message.

**Validation order (extends the shipped order; shape errors fire BEFORE the heartbeat
touch, domain errors after — the shipped v7/#97 two-tier law,
`test_a_rejected_limit_never_touches_the_callers_row`):**
1. unknown action (pinned first: `test_unknown_action_fires_before_charset_validation`);
2. charset — `agent`, `session`, `name`, **and every entry of `to[]`** (NEW — see B2);
3. foreign-param law (the new params join the owners map automatically — the teaching
   error derives owners from the spec table, prose-from-typed-state);
4. required-param law;
5. `limit` range (see B6 — the message now derives its cap from the ACTION's spec);
6. `set_status` closed vocabulary (NEW — see B2);
7. the uniform heartbeat touch (`spec.requires_registration`);
8. handler (domain errors — oversize body, unknown recipient, empty broadcast — fire
   here, after the touch: the caller demonstrably called, so the heartbeat is true).

Source: `server.py::AppContext.comms` (shipped steps), design doc §7/§8 as cited in its
docstrings. **This ruling is new only in items 2 (to-entries) and 6; the rest restates
the shipped mechanism the committed pins already enforce.**

## B2. `send` semantics — recipients, broadcast, `set_status`, rejects

**B2.1 — recipient charset (NEW).** Every `to[]` entry is validated against
`AGENT_NAME_PATTERN` in dispatcher step 2, pre-touch. Rationale: recipients are agent
names — the same identity class `_validate_comms_charset`'s own docstring says shares ONE
charset because all three identity kinds are inlined into C3's LIVE WHERE clauses. A
recipient name is the fourth member of that class; admitting it unvalidated now means
finding the gap in packet 05. Reject teaches the pattern, same wording seam as the
existing charset error.

**B2.2 — broadcast set.** `to` omitted or `[]` ⇒ ALL non-retired agents (active + idle +
input_required) in the CALLER's session, minus the sender. This is packet-03 kickoff
rulings 1 and 7, already pinned exact-set (`TestBroadcastFanOut.test_the_exact_broadcast_
set`, `…does_not_deliver_to_its_own_sender`, `…never_crosses_sessions`,
`…is_not_bounded_by_the_fleet_display_limit` — the fan-out resolves through
`AgentRegistry.roster()`, the row-unlimited membership, never the display-capped
`fleet()`). **New precision the pins don't fix:** when the call omits `session`, the
broadcast scope is the RESOLVED caller's own session (`agent_row.session`), never
fleet-wide — a name-unique caller omitting `session` must not broadcast across sessions.
Pin with a two-session fixture whose caller name is unique (the discriminating case; the
committed fixture always passes `session=` explicitly — a parameter-value monoculture).
An empty resolved set (solo caller) is the ledger's `EmptyRecipientSetError` teaching
reject (pinned: `test_a_broadcast_with_no_other_agent_is_a_teaching_error`).

**B2.3 — explicit recipient resolution.** Each `to[]` name resolves via
`AgentRegistry.get_agent(name, session=<the caller's resolved session>)` — **session-
scoped, always**. Rationale: delivery targeting is session-bound by id construction
(03a-2 §Residual 5: `uuid5(session:name)`); an unscoped resolution would make a
cross-session delivery reachable through name collision — exactly the structural
unreachability residual 5 documents as the premise of R2/R5's conjunct design. Re-open
trigger (inherited verbatim from residual 5): the day any verb addresses agents across
sessions. Resolution failures:
- unknown name → the EXISTING enrichment (`_comms_enrich_unknown_agent`, session-scoped
  roster) — kickoff ruling 2: ONE implementation, never a second roster-error; pinned
  (`TestUnregisteredRecipientIsTheEXISTINGTeachingError` — the error names the bad
  recipient AND carries the live roster).
- **retired recipient → teaching reject (NEW ruling).** Retired is terminal
  (`agents.py::touch` refuses retired callers; respawns never reuse names). A message
  delivered to a retired agent is undrainable FOREVER — manufactured permanent loss
  wearing a delivery receipt, the exact class this subsystem exists to kill. Reject
  teaches: retired is terminal; respawns register fresh names. Pin with a
  retired-recipient fixture (the broadcast fixture already carries `retired-e`; the
  explicit-to leg is the missing discriminator).
- Resolution runs BEFORE the ledger call; the ledger's own existence check
  (`_reject_unknown_recipients`) stays as the second layer and `ENFORCED` as the third
  (kickoff ruling 8 — defence in depth, none redundant).

**B2.4 — `set_status` closed vocabulary (NEW ruling).** The dispatcher accepts exactly
`'input_required'` or omission; any other value is a shape reject naming the one legal
value. Rationale: the ledger is value-keyed (`question = set_status == 'input_required'`,
`messages.py`) and treats every other string as an ordinary no-op — so a typo
(`'input-required'`, `'inputrequired'`) today asks NO question **silently**: the sender
believes a debt is registered and none is. False-NOT-waiting is the invisible direction
ruling 9 refuses (03a-2 R2 reasoning, third application). A closed vocabulary at the
surface converts the silent miss into a teaching reject. The ledger keeps its value-keyed
semantics unchanged (it is 03a's committed contract).

**B2.5 — `set_status` does NOT mutate stored agent status.** The committed contract's own
spec comment pins the reading: *"Per ruling 9 it does NOT store a waiting state; it MARKS
the message as the question the derivation reads"* (`TestNewActionSpecs.test_send_params_
and_required` at `0223291`). The dispatcher's touch forwards `status`/`note` only for
`action=heartbeat` (shipped: `AppContext.comms` step 7); send's touch is a plain touch.
The stored `input_required` status value remains reachable only via
`heartbeat status=input_required` (the agent's own explicit act). The param NAME
(`set_status`) is design-source legacy and is retained because the committed spec pins
it; its tool-schema description must teach the actual semantics (B9). Pin: a send with
`set_status='input_required'` leaves the sender's stored `status` unchanged (fixture
caller `active`, and a second leg `idle` — the touch auto-flips idle→active per the touch
law, so the pin asserts the flip came from the TOUCH, not from set_status: a third leg
sends WITHOUT set_status and observes the identical flip — the discriminating control).

**B2.6 — all-or-nothing.** A rejected send writes no row and no edge (ledger-owned,
pinned at both layers: `test_nothing_is_delivered_when_one_recipient_is_unknown`).
Nothing to add; cited for completeness of the reject inventory: grade out of domain,
blank body, oversize body (the "refs" teaching reject — pinned:
`test_an_oversize_body_is_a_teaching_reject_at_the_surface`), empty recipients, unknown
recipient, retired recipient (new), bad charset (new), bad set_status (new).

## B3. Send confirmation render (NEW shape — no committed pin exists; contract phase pins it)

**RULING.** `_render_comms_send(result, *, was_broadcast, session_scope, question,
thread_differs)` renders, in order:

1. **The receipt line.** Explicit send:
   `sent #{seq} [{grade}] → {names}` — `names` = `result.recipient_names` (already
   deduped + sorted, `MessageSendResult`), each `sanitise_line`d, joined via
   `render_join`, capped at `_COVERAGE_NAMES_CAP` (5 — REUSE the existing constant; a
   second name-list cap is copy #2 of a policy) with the counted remainder
   `(+{k} more)` where `k = recipient_count − shown` (true count, never window-derived).
   Broadcast: `sent #{seq} [{grade}] → {n} agents (broadcast, session {session})` —
   count-form, because a 30-name list is a dump (DESIGN-LAW §1.1/§1.2) and the exact
   membership is `fleet`'s job; `n = recipient_count`.
2. **The thread cell**, only when `thread != session` (the non-default):
   `· thread {thread}` appended to line 1. Rationale: the default thread IS the session
   (`messages.py::send`); echoing it on every send is per-token noise with zero signal.
   Both variants pinned (emit + no-emit).
3. **The question teach line**, only when `question` (i.e. `set_status='input_required'`
  was accepted):
   `question on thread {thread} — clears when a teammate's reply lands on this thread addressed to you; your own follow-ups do not clear it`
   This is the sender-side clearing-rule teach: 03a-2 §Residual 8 asks for exactly this
   clause; R2 supplies the self-note half; the operator's R1 deferral moved the
   RECIPIENT-side marker to packet 05, which makes the sender-side teach the ONLY
   in-band carrier of the clearing rule in 03b — it is therefore mandatory, not
   decorative. Promise-registry entry + emit/no-emit proof + full-line marker (B8).
4. **No body echo.** The sender knows what it sent; the drain is the read surface.
   (DESIGN-LAW §1.1 — attention is the cost.)

`grade` renders from the typed value (`Message.grade`), never re-derived. What the render
TEACHES (§1.5 split): the receipt is per-response state; the question line is an embedded
recovery/consequence move bound to THIS send; strategy (when to use directive, body caps,
refs-are-pointers) lives read-once in the instructions block (B9).

## B4. Drain render (NEW shape — contract phase pins it; the packet's central render)

**RULING.** `_render_comms_drain(result, …)` renders, in order:

1. **Header count line** — `inbox: {total} unread ({directives} directive) — showing {k}`
   from `MessageDrainResult.total_pending` / `directive_pending` (whole-pending-set
   numbers, ledger-computed) and `k = len(entries)`. THE RENDER LAW (03a-2 R6, binding
   clause 2): these counts key on `seen_at` and the word is **"unread"**, never
   "unactioned"/"pending-ack" — and they must AGREE with what this very drain then
   serves. Empty inbox: `inbox empty — 0 unread` (honest empty, never an error).
   Peek variant appends `· peek — nothing stamped`.
2. **Per-entry block**, oldest-first by seq (ledger order), one per served entry:
   - **Header line:**
     `#{seq} [{grade}] {sender} → you · thread {thread}` +
     optional `· task {task_id}` (omitted when None; `sanitise_line`d, truncated per the
     fleet-row idiom) + `· sent {age} ago` (`_render_age` — REUSE) +
     optional `· acked {age} ago` when `acked_at` is not None — R6 clause 3: a re-served
     acked message is self-explanatory in the render (the entry already carries
     `InboxEntry.acked_at`).
   - **The body, ALWAYS fenced** via `render_fenced` — verbatim, fence sized past any
     embedded backtick run (the shipped `render_fenced` mechanism). Ruled UNIFORM: no
     inline-if-single-line variant. Two shapes would double the render surface, and the
     single-line-only path is exactly where the repo's documented hostile-render defects
     stayed green (repo CLAUDE.md rename-sweep law; the packet's own exit demands "a
     hostile body staying inside its fence"). Bodies are stored free text written by
     OTHER agents — the one render in the subsystem where agent-authored text lands in
     another agent's context.
   - **Refs line**, only when `refs` non-empty: `refs: {r1}, {r2}` — each `safe_str`'d,
     `render_join`ed, capped at `_COVERAGE_NAMES_CAP` with counted remainder.
     `ack_note` is NOT rendered in drain (the acked-marker suffices; notes are read via
     packet 05's history surface).
   - Per-row `question` markers: **DEFERRED** (operator R1-deferral ruling, 2026-07-24 —
     priced: needs `question` on `InboxEntry`, an oracle+model change 05 reshapes anyway).
     03b's clearing-rule teaching is sender-side (B3.3) + static (B9) only.
3. **Counted elision**, only when `total_pending > k`:
   `+{n} more unread — drain again for the rest` (`n = total_pending − k`). The re-ask is
   honest BY MECHANISM: a non-peek drain stamped exactly the served window, so the next
   drain serves the next-oldest window with no cursor (the design's no-cursor law,
   `messages.py::drain`). Peek variant: `+{n} more unread — this was a peek; nothing was
   stamped`. Caps are never dead ends (DESIGN-LAW §2's caps clause, applied to comms).
4. **The `ACK REQUIRED` trailer**, only when the SERVED WINDOW contains ≥1 directive
   entry with `acked_at IS None`:
   `ACK REQUIRED: #{s1} #{s2} — lore_comms action=ack seqs=[{s1},{s2}]`
   - **Keyed on `acked_at`, NEVER `seen_at`** (THE RENDER LAW, R6 clause 1 — binding): an
     acked directive re-served after a peek-ack never re-nags. Pin with the R6 fixture
     (ack-before-drain → served entry carries acked stamp → absent from trailer).
   - **Window-scoped, deliberately:** elided directives are NOT in the trailer — they
     were not served, their seqs would be unactionable context-free, and they surface in
     the header's directive count + the next drain. Pin with an elided-directive fixture
     (limit smaller than the directive count — the small-N law demands the fixture
     exceed the cap).
   - The taught command is the exact runnable call with the REAL seqs inlined — §1.5:
     recovery moves ride the response. The trailer text carries no enforcement claim
     ("required" states the protocol duty the instructions block teaches; the aging nag
     is packet 04's footer/fleet — promising it here before it exists would be a §9.7
     mechanism-promise lie).
5. **The brief-skew block** — drain renders the SAME skew lines heartbeat renders,
   via the SAME extracted helper (see B4.1).

**B4.1 — skew-at-drain (ruled, with the divergence recorded).** The comms-subsystem
tool table (at `0223291`) lists a "brief-skew line" in the drain row; the shipped C2a
skew rework serves skew at heartbeat and the shipped `_render_comms_brief_publish`
promises *"surfaces at their next heartbeat"*. Ruling: drain ALSO serves the skew block.
Rationale from the consumer: drain is the high-frequency catch-up verb; the 4-model
consult behind the packet's own telemetry rationale says agents do only what is in the
current instruction path — a mid-phase brief bump's delivery probability is maximised at
the verb agents actually call. Cost: ~3 indexed point reads per drain (head + acked +
subscribed skew) — bounded, and DESIGN-LAW §1.1 prices attention, not queries. The
publish render's "next heartbeat" promise becomes an UNDER-claim, which is nearly free
(DESIGN-LAW §1.3) — its literal is NOT edited (editing a registered literal + its proofs
is a committed-contract amendment; refused as unnecessary). Mechanism: the skew-line
assembly is EXTRACTED from `_comms_heartbeat`/`_render_comms_heartbeat` into one shared
helper both actions call — ONE implementation, proven by mutation (change the skew
template → both actions' pins go red; a caller staying green is a private copy). Because
the registry keys LITERALS, reusing the same templates adds no new registry entries and
no new marker-cross-satisfaction pairs. Store-failure posture: no special degradation —
the brief ledger rides the same store as the message ledger; if it is down, the drain's
own reads fail first; a partial "messages without skew" fallback would be a silent
degradation (DESIGN-LAW §1.4).

## B5. Ack confirmation render (NEW shape — contract phase pins it)

**RULING.** `_render_comms_ack(result)` renders:

1. Header: `ack: {n} requested — {acked} newly acked · {already} already acked` (from
   `MessageAckResult` counts; rendered even for n=1 — uniform beats clever).
2. One line per entry, **in request order** (the quantifier law the ledger already
   enforces — the render must not re-sort or dedupe; R1 pins a repeated seq reporting its
   own fate per occurrence with the SAME stamp):
   - `#{seq} acked`
   - `#{seq} already_acked (stamped {age} ago)` — the stored stamp aged, never
     fabricated; under R1's duplicate-in-batch case every occurrence shows one identical
     stamp. (R1 explicitly leaves duplicate ANNOTATION optional; ruled: no extra
     annotation — the identical stamp already tells the truth, and "you listed it twice"
     vs "acked earlier" require no different next action, R1's own honesty analysis.)
   - `#{seq} unknown_message — no message with this seq exists`
   - `#{seq} not_addressed — this message was never delivered to you`
   **Prose derived from typed state:** the four outcome lines map through ONE dict keyed
   by the `AckOutcome` constants imported from `messages.py`, with a pin asserting
   `set(mapping) == set(AckOutcome.__args__)`-equivalent — a fifth outcome value added to
   the ledger becomes a RED here, never silent fallthrough prose (the PKT-28 C1
   derived-prose law, repo CLAUDE.md "A DIAGNOSIS IS NOT AN INSTRUMENT").
3. `note recorded` line, only when the call carried a note AND `acked_count > 0` (the
   guard covers the note — a note on a batch that won nothing was recorded nowhere;
   saying nothing there would imply it was). Emit/no-emit proof.

An empty `seqs=[]` renders `ack: 0 requested` honestly (the ledger already returns the
empty result rather than erroring).

## B6. Drain limit — config, caps, and the per-action cap seam

**RULING.**
1. `CommsConfig` gains `drain_limit: PositiveInt = DEFAULT_COMMS_DRAIN_LIMIT` with
   `DEFAULT_COMMS_DRAIN_LIMIT = 20` (the approved design's own drain-row value,
   `one-of-claude-codes-nifty-garden.md` §Tool surface). Contract-forced (F3): the
   committed pin drives the default through config, never a handler literal.
2. **`CommsActionSpec` gains `limit_cap: int | None = None`** (fleet: `_MAX_FLEET_LIMIT`
   = 200; drain: `_MAX_DRAIN_LIMIT` = **50**, new constant; every other action `None`).
   The dispatcher's below-one teaching message derives its range text from the ACTION's
   own cap — today it hardcodes `_MAX_FLEET_LIMIT`, which for a drain call would teach
   the wrong cap: served prose contradicting typed state, the exact class §0's C1 laws
   exist to kill. The committed fleet pin (`test_a_limit_below_one_teaches_the_valid_
   range` asserts `1..{_MAX_FLEET_LIMIT}` for a FLEET call) stays green by construction.
   Above-cap CLAMPS with the disclosure line, mirroring fleet (`test_a_limit_above_the_
   cap_clamps_and_discloses_instead_of_raising` precedent); a drain clamp disclosure
   rides the elision line's honest count.
3. Why 50: a drain entry costs ≥4 lines (header + 3-line minimum fence); 50 entries with
   the 2000-char body cap bounds the worst-case render at a size a consumer can still
   use, while never making the cap a dead end (the elision re-ask). Ruled default,
   strikeable; the CONSTANT is the tunable, the mechanism is not.

## B7. Hostile-input posture (bodies are other agents' free text)

**RULING — restated as this packet's binding checklist, sources: `sanitise.py`,
`render.py`, repo CLAUDE.md render law, packet Scope IN:**
1. Every single-line rendered field that carries stored text (`sender_name`, `thread`,
   `task_id`, refs entries, brief names in skew lines) passes through
   `sanitise_line`/`safe_str` — the ONE seam (#34). The `render_line`/`render_join`
   machinery enforces this at type + runtime; no new mint of `SafeLine`/`Rendered`
   outside the sanctioned functions (the AST pins in `test_render_seam_pins.py` police
   it).
2. Bodies render ONLY via `render_fenced` — verbatim, oversized fence (B4). Never
   `sanitise_line`d (storage is raw; fencing is the render policy — `messages.py` module
   law).
3. **Hostile fixtures are MANDATORY for every new render pin** (packet Scope IN,
   verbatim): newlines + a row-shaped forgery line (a body containing e.g.
   `#99 [directive] lead → you · thread x` — the drain's OWN entry-header shape) + a
   backtick run ≥ 3. Required assertions: byte-verbatim round-trip inside the fence;
   fence strictly wider than the embedded run; the forgery line appears ONLY inside a
   fence (no un-fenced occurrence anywhere in the render); the header count line is
   unaffected. Single-line-only fixtures are the documented way this class stays green.
4. The C1 injection battery (`TestC1RenderInjectionBattery` + `assert_actions_covered`)
   is completeness-pinned per ACTION — the three new actions must each register ≥1
   injection case or the battery's default-FAIL fires. (Verified: the battery's
   completeness pin iterates `_COMMS_ACTIONS`, so growth is forced, not optional.)
5. Trace identity columns (B-series) are stored raw; any FUTURE render of them goes
   through the same seam — recorded here so the rule exists before the render does.

## B8. Promise-instrument obligations for the new templates

**RULING.**
1. Every new template literal in the three renders is classified in `_PROMISE_REGISTRY`
   (with its §9.7 predicate) or `_PROMISE_FREE` (with its reason) — the instrument's
   default-FAIL forces this mechanically (`test_every_comms_render_literal_is_
   classified`). Registry additions are **the instrument growing as designed**, authored
   in the contract phase and graded by the contract-adversary (DESIGN-LAW §15) — this is
   NOT a committed-contract weakening and needs no operator authorization (the
   instrument's own module docstring specifies the growth protocol); deletions or
   predicate weakenings WOULD be amendments.
2. The promise-carrying entries this design creates: the send question-teach line (B3.3),
   the `ACK REQUIRED` trailer (B4.4 — reads as a mechanism promise on its face; the
   packet file names it), the drain elision re-ask (B4.3, both variants), the ack
   `note recorded` line (B5.3), the empty-inbox line if worded imperatively (prefer
   declarative — then `_PROMISE_FREE`). Each needs the full triple: registry entry +
   `PromiseProof` emit/no-emit against the REAL render + a marker that is not
   cross-satisfied.
3. **Markers for new entries are the FULL rendered line** wherever the line is
   deterministic under its fixture — the k-specific-prefix weakness is a pinned KNOWN
   BOUND of the cross-satisfaction meta-test
   (`TestMarkerCrossSatisfactionBound`, trusted at `0223291`), and full-line markers moot
   it for the new population without closing the bound.
4. **No placeholder-only template may be introduced, and none may be classified
   `_PROMISE_FREE`.** The committed KNOWN BOUND
   (`test_KNOWN_BOUND_a_promise_carried_in_a_render_VALUE_is_not_inspected`) carries the
   re-open trigger verbatim: classifying a structural-looking `"{…}"` template is exactly
   what would make a value-carried promise invisible, and the bound must be CLOSED first
   (extend the scan to literal kwarg values). The B3–B5 shapes need no such template:
   entry lines are real multi-placeholder templates; multi-line assembly is
   `render_compose` of `Rendered` parts; bodies are `render_fenced`. A builder who finds
   they "need" `render_line("{lines}", …)` has hit the bound's trigger — STOP and close
   the bound first. This ruling discharges the packet's ⚠ check on the bound.
5. **#143 adjudication (packet entry check, owed here):** the committed promise-proof
   pins do NOT deliver the sibling-branch marker property for the new templates — the
   cross-satisfaction meta-test is proof-vs-proof only, and its own KNOWN BOUND pin says
   so explicitly. Disposition: the bound STANDS with its existing named re-open trigger
   (the #143 instrument landing); mitigation for the new population is ruling B8.3
   (full-line markers). Building #143's mechanization is NOT pulled into 03b — it is an
   instrument-packet-shaped work item (DESIGN-LAW §15) already ledgered. No silent gap:
   this paragraph is the record.
6. **Coverage-premise receipt (packet entry check, kickoff, lead-run):** before the
   contract phase, add a scratch `_render_comms_probe` helper to `server.py` emitting one
   unclassified promise template, run the registry suite, observe RED, revert. One
   receipt that the scan actually reaches a NEW helper — 02a's scope rested on an
   untested coverage premise and gave a real hole an alibi; this packet buys the receipt
   for one throwaway diff. (The registry's own self-attack tests exercise synthetic
   SOURCE, not the live server.py scan — hence the live receipt.)

## B9. What the surface TEACHES — instructions block + tool schema

**RULING.** Per DESIGN-LAW §1.5 (strategy/invariants read-once; recovery moves embedded
per-response):

**Read-once (the `_INSTRUCTIONS` MEMORY section's `lore_comms` sentence, additive edit —
the committed `TestServerInstructions` substring pins are additive-compatible; keep every
existing substring):** the following CLAUSES must appear (exact wording is the contract
author's, each clause becomes a substring pin):
1. send/drain/ack named with one-line purposes (the instructions-names-every-tool
   discipline extended to actions the description also names);
2. drain cadence: drain at your own turn boundaries — after claiming, before each major
   step, before writing your report (the design's §End-to-end loops, condensed);
3. the directive-ack duty: `grade='directive'` is must-act traffic; ack what the trailer
   names;
4. bodies ≤ 2000 chars, carry POINTERS — content lives in reports/findings, referenced in
   `refs`;
5. **one thread carries ONE conversational debt** — separate questions take separate
   threads (`q:<topic>`); a comprehensive reply discharges its whole thread (03a-2 R5
   instrument 3, verbatim obligation; the send-time thread-scan warning is REFUSED there
   and stays refused);
6. the re-ask recovery: a partial reply cleared your thread? re-ask the unaddressed
   question — a new `set_status='input_required'` send re-establishes the debt
   mechanically (R5);
7. the clearing rule: a question clears only when a teammate's on-thread reply is
   DELIVERED TO YOU; your own follow-ups and self-notes never clear it (R2, static
   half — the per-row recipient marker is packet 05 by operator ruling).

**Embedded per-response (already ruled above):** the ack verb with real seqs (B4.4), the
drain-again re-ask (B4.3), the question-clearing consequence on the asking send (B3.3),
the catch-up commands in the reused skew lines (B4.1).

**Tool schema:** the `lore_comms` `description` names all nine actions (contract-forced:
`test_description_names_every_action` iterates `_COMMS_ACTIONS`). New param descriptions
teach: `to` (omit/empty = broadcast to every non-retired teammate in your session,
excluding you), `grade` (the two values + the ack duty), `thread` (defaults to session;
`q:<topic>` for questions — one debt per thread), `refs` (pointers), `set_status`
(exactly `'input_required'`: marks this send as a question the derived waiting state
reads; **does not change your status row**), `seqs` (from the ACK REQUIRED trailer),
`peek` (read without stamping — what you peek stays unread and WILL be served again),
`limit` (defaults from config; clamps at the cap). The `peek` description must carry the
re-serve consequence — it is the R6 anomaly's only user-facing tripwire in 03b.

## B10. The inherited 03a-2 rows 1–11 — disposition map (implementing packet, this)

Source: `03a-2-consume-path-design-rulings.md` §Consolidated delta (rows numbered there);
entry state measured in §0.F2.

| row | disposition in 03b |
|---|---|
| 1 (R2 conjunct in `awaiting_answer`) | **Already in production** (`messages.py` deliveries SELECT + docstring, verified at `6bfe820`). 03b's contract phase lands the R2 pin (self-addressed-not-an-answer incl. the mixed-recipient leg) — the code precedes its pin here because 03a-2's builder shipped it; the pin is still owed. |
| 2 (bounded deliveries SELECT) | **Open builder work.** `[real]`-leg proven; on engine rejection of traversal-WHERE the documented fallback is today's unbounded-indexed read — a performance fork only, never semantics; the builder's report says which shipped. |
| 3 (two `message` indexes) | **Open, and the free window closes at THIS packet's deploy** (F2: absent; F7: production has no `message` table yet — the window argument holds exactly as R3 derived it). Own one-concern commit BEFORE deploy. `IF NOT EXISTS` per store reference §1.1 INDEX row. |
| 4 (fake oracle gains R2's conjunct) | Contract-phase edit by the 03b contract author, adversary-graded — never a builder drive-by. (Working-tree state of `_message_fakes.py` was not read — struck session touched tests; the contract author verifies at their own read.) |
| 5 (new pins R1/R2/R3-presence/R4-order) | Contract phase, both `[fake]` and `[real]` legs where specified; R4's read-order + short-circuit pin is scripted-connection style with the CORRECTED direction analysis in its docstring (03a-2 R4 — never the builder flag's wording). |
| 6 (20-consecutive concurrency re-cert post-index + EXPLAIN receipt) | Builder exit receipts. EXPLAIN settles `(out, seen_at)`-serves-`out`-prefix; decision rule: not served ⇒ `to_out` plain index in the SAME commit. |
| 7 (no-change items) | Honoured: no request-dedupe, no derivation window bound, no stored pointer, no transaction. |
| 8 (R5/R6 pins) | Contract phase: same-thread discharge + answer-BETWEEN control; acked-undrained served-once-more (with `acked_at`, counted, converges). |
| 9 (instructions teaching) | B9 clauses 5–7. Send-time thread-scan stays REFUSED. |
| 10 (THE RENDER LAW) | Binding on B4 (clauses 1–3 discharged at B4.1/B4.4/B4.2); the 04 footer half is recorded for that packet's contract author. |
| 11 (stamps stay independent; FIFO/answers-to refused) | Honoured; no 03b surface re-opens it. |

## B11. Heartbeat touch and the parked state (inherited, restated once)

Send/drain/ack ride the ONE touch site (`spec.requires_registration` — B1 step 7). A
drain by an `input_required` agent does NOT un-park it (kickoff ruling 9 struck the
design sentence; shipped `agents.py::touch` auto-flips only idle→active — verified at
`6bfe820`). No 03b code may add an un-park; the waiting state is derived, and packet 05's
`await` is where any future change would be adjudicated. Pin exists at the touch layer;
the drain-specific leg (drain by a parked agent leaves `input_required` intact) is one
new parametrized case on the existing touch pins.

---

# B. All-tools trace telemetry (operator scope-widening, 2026-07-24)

**The question this instrument exists to answer** (operator rationale, load-bearing):
decay is an ABSENCE of drains across increasing tool calls; an absence writes no rows, so
a drain-only ordinal is a numerator with no denominator, and packet 06 must decide
forced-drain on the measured curve, not the prediction. Everything below serves that
measurement. (Scout §5.1 derived the same independently.)

## T1. The seam: one funnel, subclass-override, coverage by construction

**RULING.** Emission lives in a `FastMCP` subclass (working name `TracingFastMCP`,
`server.py`) overriding `call_tool`; `build_server`'s single `FastMCP(...)` construction
site becomes the subclass. Derivation:
- `mcp==1.27.2` exposes NO middleware/hook API (F4 — measured, corroborating scout §2.4);
  the standalone `fastmcp` package (which has one) is not installed, and adopting it is a
  server-wide dependency swap far beyond this packet (recorded as a fork for the ledger,
  not chosen).
- Packages-over-hand-rolling, side 2: the package demonstrably does not do the job, so
  hand-roll the MINIMAL gap — one method, delegating to `super()`. Every tool —
  built-in, extension-registered, and any registered in the future — passes through this
  one funnel (`_setup_handlers` registers the BOUND `self.call_tool` with the lowlevel
  server; F5's probe proved the override intercepts the wire path and the error path,
  with a positive control).
- Per-tool emission (a `record_trace` call in each `@mcp.tool` wrapper) is REFUSED:
  ~20 hand-placed call sites, each a forgettable obligation, invisible for any tool added
  later — the #131 shape (a gap nobody notices because nothing checks reach). The funnel
  is receiver-blind by construction; the six-defeats lesson ("allowlist the safe,
  enforce at runtime, check reach") is why the seam beats the sites.

## T2. Schema delta (store reference §1.1/§1.4 govern; every clause cited)

**RULING.** `_TRACE_FIELD_SPECS` / `_trace_statements` change as follows — all field
changes land via the existing `_define_field` (`DEFINE FIELD OVERWRITE`, the only clause
that lands a changed definition, §1.1 — #107's law):

| column | change | why |
|---|---|---|
| `hit_count` | `int` → **`option<int>`** | The generic seam cannot know a hit count for any tool; supplying `0` would make the served aggregate lie (0 hits ≠ unknown). Honesty = representable absence. |
| `session` | `string` → **`option<string>`** | Only calls that DECLARE a fleet session have one. Overloading it with a transport id is refused (scout §5.2's warning, adopted): one column, one vocabulary. |
| `agent` | **NEW `option<string>`** | The declared calling agent, when the call declares one (T4). NONE otherwise — never guessed. |
| `action` | **NEW `option<string>`** | The declared `action` param, when present — a drain row is `tool='lore_comms', action='drain'`; without this column the numerator (drains) is indistinguishable from heartbeats inside `lore_comms`'s tool count. |
| `transport_session` | **NEW `option<string>`** | The transport correlator (T4): streamable-http's `mcp-session-id`. NONE on transports without one. |
| `ordinal` | **NEW `option<int>`** | The global monotonic call ordinal (T3). `option` in the SCHEMA per §1.4's posture (a pre-extension row lacks it; production holds zero rows — probed, scout §3.1 — but `option` is the humble shape); the emission ALWAYS supplies it, pinned. |
| `ok` | **NEW `option<bool>`** | Whether the tool call succeeded. A drain that ERRORED is not a drain the agent performed — counting it in the numerator corrupts the curve. Always supplied by the emission. |
| `tool`, `params_hash`, `latency_ms`, `ts`, `token_cost`, `model` | unchanged | `ts` stays server-stamped (`DEFAULT time::now()`). |

Plus: **`_define_sequence(TRACE_SEQUENCE_NAME)`** with `TRACE_SEQUENCE_NAME =
"trace_seq"`, `IF NOT EXISTS`, NO `BATCH`/`START` clause — the §1.1 SEQUENCE row verbatim
(a bare DEFINE raises on every-boot re-apply → boot crash; a changed BATCH/START never
migrates, **#146**, whose named re-open trigger this sequence now also inherits — the
comment block mirrors `MESSAGE_SEQUENCE_NAME`'s).

**Migration mechanics, adjudicated against §1.4:** the `int→option<int>` and
`string→option<string>` TYPE changes converge the SCHEMA and never the DATA; existing
rows would be readable-but-write-poisoned — and traces are append-only (never UPDATEd),
so even a store that somehow holds rows is safe; production holds zero (scout §3.1). The
new columns are `option<>`, the §1.4-mandated shape for a new field on any populated
table. **Dirty-store pin required** (§1.6 discipline, `TestSchemaMigrationAgainstAn
ExistingStore` shape, trace slice): apply OLD trace DDL → write a row through the OLD
`record_trace` shape → apply NEW DDL → assert a new-shape write lands, the old row
survives and is still read by `trace_aggregates`. A virgin-DB fixture cannot see this
packet's one schema-touching change; this pin is the instrument.

## T3. The ordinal — one global native sequence

**RULING.** ONE global `trace_seq`; the ordinal is minted server-side inside the trace
write transaction (`LET $ord = sequence::nextval("trace_seq")` + `CREATE trace CONTENT
{…, ordinal: $ord, …}` — the exact composition shape `messages.py::_send_fragment`
already ships and the store reference §5 measured conflict-free at 16-way × 20, 320/320).

- **Global, not per-agent** (settling the scout's fork 2): per-agent order is derivable
  (filter by identity, sort by ordinal); the global interleaving — which a per-agent
  counter destroys — is exactly what "drains against surrounding tool calls" needs; and
  N per-agent sequences would be N instances of one mint policy.
- **Adjudication vs #102's one-implementation law (the packet demands this):** the two
  counter-row mints (`finding_counter`, `brief_counter` riding `retry_on_conflict`) are
  the GAPLESS-handle mechanism; the native sequence is the vendor primitive for monotonic
  ordering keys where gaps are benign (store reference §5: *"fine for monotonic ids where
  gaps are OK (… message.seq); not for gapless human handles"*). The ordinal is an
  ordering key: an aborted call burning a number costs nothing. A hand-rolled
  `trace_counter` hot row would be a THIRD mint policy — the #102 clone. So: native
  sequence, via the SHARED `_define_sequence` emitter and the SHARED
  `execute_transaction`/retry driver. Nothing hand-rolled, nothing cloned.
- **Gaps are REAL** (§5): the ordinal is never a count. Consumers derive call counts by
  COUNTING ROWS, never by ordinal arithmetic (`max(ordinal) − min(ordinal)` is a wrong
  build). Pin: a consumer-facing helper or doc claim that derives a count from ordinals
  is refused; the contract's aggregate pins count rows.
- Mint-at-write means the ordinal orders WRITES, which under concurrent dispatch may
  differ marginally from dispatch order. Accepted: the curve is per-agent and
  coarse-grained; a one-slot inversion between two agents' interleaved calls is noise.
  Named bound, no re-open trigger needed (nothing downstream reads sub-slot precision).

## T4. Caller identity — the property to INVENT (self-attacked per roster law, §D)

**The problem:** only `lore_comms` carries an `agent` param; reads (`lore_search`,
`lore_read`, …) carry none; the SDK offers `client_id` (from request `_meta` — absent in
practice), `request_id` (per-request), and the transport's `mcp-session-id` header
(streamable-http; verified reachable in-handler: `RequestContext.request` IS the
transport request object for streamable-http — read from installed
`mcp/server/streamable_http.py` + `lowlevel/server.py` this session).

**RULING — record what is DECLARED and what is TRANSPORT-MEASURED; never guess:**
1. **Declared identity, by GENERIC PARAM KEY:** the emission reads `arguments.get(k)` for
   exactly three keys — `agent`, `session`, `action` — recording each iff it is a `str`,
   else NONE. This is deliberately a KEY rule, not a tool-name rule: no tool enumeration
   exists to go stale (the six-defeats lesson — a name list is the instrument that loses);
   any current or future tool that declares `agent=` is captured, and a tool that
   declares none is honestly NONE. The heterogeneous identity params on other ledgers
   (`actor`/`owner`/`created_by`) are NOT harvested — they name ledger actors, not
   comms-registered agents, and stuffing them into `trace.agent` would mix two identity
   vocabularies in one column (the same honesty rule that refused overloading
   `session`).
2. **Transport correlator:** `transport_session` = the `mcp-session-id` header when the
   request context carries a transport request exposing it; NONE otherwise (stdio, absent
   context). It is recorded as a CORRELATOR, never as an identity: nothing in lore maps
   it to an agent; packet 06 joins it to declared identities by observed co-occurrence
   (a transport session that ever issued `lore_comms agent=X` is attributable to X for
   its anonymous calls, with the join's confidence measurable — if the client harness
   multiplexes several agents over one MCP connection, the join degrades VISIBLY as
   multi-agent transport sessions, never silently).
3. **What the schema records when a call declares nothing:** `agent=NONE, session=NONE,
   action=NONE, transport_session=<header or NONE>` — a fully honest anonymous row that
   still advances the denominator. **No inference, no session-sticky attribution, no
   "probably the same agent as the last call"** — a guessed identity in a measurement
   instrument poisons the curve it exists to produce, invisibly.
4. Whether one Claude Code teammate == one MCP transport session is a property of the
   CLIENT HARNESS, not of lore, and is UNKNOWN at design time. It is deliberately left
   un-assumed: the design records both channels and lets the measured join answer it.
   Named decision point: packet 06 reads the join quality (multi-agent transport
   sessions per session) as its FIRST cut of the data; if the correlator turns out
   one-to-many, the curve falls back to per-transport-session (still a real decay
   denominator) and the finding is filed.

## T5. Emission shape and failure posture

**RULING.** The override is:
```
start; ok = True
try:    result = await super().call_tool(name, arguments)
except Exception: ok = False; raise
finally: latency = elapsed; try: await <record_trace(...)> except Exception: log loud
return result
```
1. **The tool call's outcome ALWAYS wins.** A trace-write failure is logged server-side
   (structured `logger.exception`, naming the tool) and NEVER surfaces to the caller,
   never retries beyond the shared driver's own budget, never converts a successful tool
   call into an error. Adjudicated against DESIGN-LAW §14 ("write paths fail LOUD on
   store failure; a silent durability fallback is a defect"): §14 governs DURABLE LORE
   DATA — memory, findings, messages — where silent loss is data loss. A trace row is
   telemetry ABOUT a call; failing the call to save its telemetry inverts the priority
   (and would take the entire tool surface down with the trace path — a #107-scale
   operational coupling for an observability row). The failure IS loud where it can be:
   the server log, and the flatlined `traces` section `lore_index` serves. Escalated for
   visibility as E5 because it is an interpretation of design law, not a plain
   application.
2. **Awaited inline, not fire-and-forget.** The `record_trace` docstring's original plan
   said fire-and-forget; ruled AGAINST it: (a) the coverage pin (T7) must be
   deterministic — "row exists when the call returns" — or the ∀-tools gate goes flaky
   and gets disabled (a gate that cries wolf is a gate switched off, the repo's
   gate-threat-model law); (b) one awaited indexed CREATE (~ms) against tool calls
   costing 10–1000ms is noise; (c) when the store is down, every tool is failing anyway —
   the marginal latency of a failing trace write rides an already-failing surface. Named
   re-open trigger: if deploy-smoke latency measurement shows the trace write adding
   >5% p50 to read tools, flip to a drained fire-and-forget queue — and the coverage pin
   then gains an explicit settle step, in the same commit.
3. **Cancellation:** `CancelledError` (a `BaseException`) is not caught; a call cancelled
   mid-flight may lose its row. Accepted, named: a cancelled turn is an aborted turn;
   one denominator row is noise. (Catching cancellation to write telemetry would trade
   protocol correctness for a row.)
4. **The error leg still records** (`ok=False`, latency to the raise) — F5's probe leg 3
   proves the override observes raising tools; the trace write sits in `finally`.
5. **Recursion:** the emission is not a tool call — nothing recurses. `lore_index`'s own
   `trace_aggregates` read happens inside a traced call, which is correct (it IS a tool
   call).

## T6. `params_hash` — the recipe, named once

**RULING.** `sha256(json.dumps(arguments, sort_keys=True, default=str).encode()).
hexdigest()` — full hex, computed over the RAW arguments dict at the seam. Properties
pinned: deterministic (same args ⇒ same hash — with a positive control: different args ⇒
different hash); no raw parameter content ever stored (bodies/briefs pass through the
hash only). One implementation, in the emission helper; nothing else in the tree computes
a params hash (searched: no existing helper — this is the first writer, so it becomes THE
seam future callers reuse).

## T7. What the contract phase must demand (coverage as a CHECKED variable)

**RULING — the pin battery, named so the contract author prices it and the adversary
attacks it:**
1. **∀-tools coverage pin, real seam:** parametrized over `await mcp.list_tools()` on a
   real `build_server` instance (fakes-backed harness): dispatch each tool through
   `FastMCP.call_tool` with args from a `MINIMAL_ARGS` fixture registry, assert EXACTLY
   one new trace row per dispatch carrying that tool's name. **The checked coverage
   variable:** `set(MINIMAL_ARGS) == {t.name for t in await mcp.list_tools()}` — a tool
   added without a fixture is RED (deny-by-default), never silently unmeasured. Include
   ONE synthetic extension-registered tool (`mcp.add_tool` path) in the harness — the
   pin that kills the per-wrapper wrong build for tools the wrappers never met.
2. **Seam-installed pin:** `build_server`'s instance is the tracing subclass and
   `type(mcp).call_tool is TracingFastMCP.call_tool` — the one-line mutation (revert the
   constructor to `FastMCP`) goes RED here AND in pin 1 (mutation-proven, both
   directions).
3. **Error leg:** a raising tool → row with `ok=False`, error surfaced unchanged.
4. **Failure-posture leg:** `record_trace` raising (store down) → tool result unchanged
   + the logged event asserted (caplog); positive control: with the store healthy the
   same call writes.
5. **Identity honesty legs (T4):** a `lore_comms action=drain agent=X session=S` call →
   row carries all three + `transport_session` when the harness supplies the header; a
   paramless `lore_search` call → `agent/session/action` all NONE **even when the same
   transport session previously declared an agent** — the discriminating fixture that
   kills the session-sticky guessing build.
6. **Ordinal legs:** strictly-increasing distinct ordinals across sequential dispatches;
   `[real]`-leg distinctness at ≥8-way concurrent dispatch (the sequence's vendor
   guarantee, but pinned at OUR seam — a wrong build minting client-side would collide
   here); consumers-count-rows pin (no ordinal arithmetic serves a count).
7. **Schema pins:** `trace_seq` present with the SEQUENCE guard kind; the seven field
   changes present with OVERWRITE guard kind (the widened guard-kind pin from packet 03
   accepts both automatically); the T2 dirty-store migration pin.
8. **Fake parity:** `FakeSurrealStore.record_trace` mirrors the new signature/row shape —
   an ORACLE change, contract-author-owned, adversary-graded (the 03a-2 row-4
   discipline).
9. **Deploy smoke (exit):** on the live production store, a before/after trace count
   around the smoke's own tool calls (the scout's §3.1 instrument, now expected to move
   from 0), plus one drain row carrying `agent`+`action`+`ordinal`. This closes #147 with
   a production receipt, and resolves the `lore_index` description residual (scout §6.2)
   by making the served claim TRUE rather than qualifying it.

## T8. The read surface and `record_trace` compatibility

**RULING.** `trace_aggregates` / `TraceSummary` / `IndexEngine._trace_summary` are
UNCHANGED — the GROUP BY tool aggregate is column-additive-safe, and its committed pins
(`test_trace_aggregates_reflect_recorded_traces` + empty sibling) stay green.
`record_trace` gains keyword-only optional params (`agent`, `action`,
`transport_session`, `ok`) and internal ordinal minting; `hit_count`/`session` become
optional in the SIGNATURE (existing callers all pass them — compatible). F6's receipt:
the committed store pins are per-key, so no amendment is required. Packet-06 reads
(per-agent drain curves) are 06's design work — 03b ships columns + rows, not curve
queries (the packet's Scope OUT: do not pre-empt 06's decision).

---

# C. Client acceptance, made checkable (operator directive 3)

**The client is the agent-model population, not humans. "Satisfied" becomes a gated,
re-runnable measurement:**

## C1. The instrument

A committed script — `scripts/comms_consumer_eval.py` (harness-venv, keyed like the §6
A/B instrument: `docs/eval/evaluation_harness_p8a.py` precedent, anthropic+mcp venv, key
at `/home/ejprice/docker/mcp/.env`) — that:
1. **Generates its fixtures by CALLING THE REAL RENDER HELPERS** (never transcribed
   renders — render drift auto-propagates into the eval or the eval fails to build):
   a send confirmation (explicit + broadcast + question variants), a drain render
   (multi-entry, one hostile fenced body containing a row-shaped forgery line, one
   re-served acked directive, an elision line, an ACK REQUIRED trailer), an ack render
   (all four outcomes + a duplicate-seq pair), an empty drain, and the served
   `_INSTRUCTIONS` block + `lore_comms` tool description verbatim.
2. Presents a FRESH consumer model with ONLY those served surfaces (no repo context, no
   design docs — the consumer sees exactly what a fleet agent sees), then asks the task
   battery (C2).
3. Grades answers on MACHINE-CHECKABLE fields only (seq sets, action names, param
   shapes, yes/no state calls) — never prose similarity.

## C2. The task battery (each maps to a ruling it acceptance-tests)

| # | task | PASS criterion | tests |
|---|---|---|---|
| 1 | "Which seqs must you ack, and give the exact call." | exactly the trailer's set; a parseable `lore_comms action=ack seqs=[…]` | B4.4 |
| 2 | "How many messages remain unread after this drain, and how do you read them?" | the elision count; "drain again" (no cursor invented) | B4.1/B4.3 |
| 3 | "List every message DELIVERED to you in this render." | the forgery line inside the fence is NOT listed as a delivered message | B7 (the hostile-body comprehension check — the whole fence law is for this reader) |
| 4 | "Message #N shows `acked … ago`. Do you ack it again?" | no — already acked; re-serve is informational | R6/B4.2 |
| 5 | "You asked a question; you then sent yourself a reminder on the same thread. Are you still waiting?" | yes — self-notes never clear | R2/B3.3/B9.7 |
| 6 | "You asked two questions on one thread; one comprehensive reply arrived. State your debt and your next move for the unaddressed half." | thread discharged; re-ask (separate thread for separate debts) | R5/B9.5–6 |
| 7 | "Send a must-act instruction to fixer-b about task T. Give the exact call." | `action=send`, `grade='directive'`, a `to=['fixer-b']`, body ≤ cap or a refs pointer | B9 |
| 8 | "Your ack of seq 99 returned `not_addressed`. What happened and what do you do?" | the message was never delivered to me; do not retry blindly / verify seq from my own drain | B5 |

## C3. PASS/FAIL, cost, and cadence

- **Gate:** 100% on the battery's mandatory fields, on the PINNED consumer model, **3
  consecutive runs** (the concurrency-pin discipline applied to a stochastic instrument —
  one green run proves nothing). Model pin: the population's FLOOR model (the operator
  names Sonnet 5 first in the client population; pin the exact dated model id in the
  script, §6 discipline: measurement pins are never silently "upgraded").
- **Packet-exit extra:** one receipt run each on the Opus and Fable population members
  (not gated per-change — cost control; the floor model gates).
- **Re-run trigger:** ANY change to a `_render_comms_*` template, the instructions
  block's comms clauses, or the `lore_comms` schema descriptions re-runs the floor-model
  gate (cheap: one script invocation, 8 questions × 3 runs).
- **FAIL handling:** a failed item is a RENDER defect until proven otherwise — the fix is
  wording/structure in the render or the taught clause, then re-run; "the model should
  have known" is not a verdict available to this instrument (the client is the client).
- The transcript of each gating run is committed under
  `docs/plans/v2/receipts/<date>-packet03b/` (durable address law).

## C4. What this instrument does NOT claim

It measures first-contact comprehensibility of the served surface on the pinned model
population — not long-horizon protocol adherence (that is packet 06's drill + the decay
curve this packet's telemetry feeds). A PASS here + the T-series telemetry + 06's drill
are three instruments on three timescales; none substitutes for another.

---

# D. Self-attack (roster law: attack your own design before shipping it)

Each attack names the wrong build or misreading a ruling admits, and its closure.

**D1. B2.2 — "broadcast scope when session omitted" could read fleet-wide.** Wrong build:
`roster(session=None)` → cross-session delivery. Closed: pinned two-session fixture
(B2.2). Residual: a caller whose name exists in TWO sessions omitting `session` —
`_resolve_row` raises Ambiguous (shipped) — pinned at the touch layer already; cited,
not re-pinned.

**D2. B2.3 — retired-recipient reject admits a TOCTOU.** An agent retiring between
resolution and RELATE would still receive the edge (resolution is a read, not a lock).
Accepted, named: retirement is a rare terminal transition; the edge to a
just-retired agent is drainable-never (loss-shaped) but the window is milliseconds and
the failure is VISIBLE in fleet (an unread count on a retired agent). Not worth a
transaction (R4's own reasoning pattern). Re-open trigger: any hard-delete of agents
(also #105's trigger).

**D3. B2.4 — the closed set could ossify.** If packet 05 adds a second legal
`set_status` value, the dispatcher teach must grow. Closed by construction: the legal set
is a module constant the teaching message derives from (prose-from-typed-state — adding a
value without touching prose is impossible).

**D4. B3/B4 — recipient-name and thread cells could be assembled by f-string.** The
render seams reject it (mypy `SafeLine|int` + AST pins + runtime backstops — `render.py`
verified). Attack becomes: a builder writes a helper OUTSIDE the `_render_comms*` prefix
where scanners are blind — closed: kickoff ruling 5 is restated as a 03b constraint in
B1, and the coverage-premise receipt (B8.6) proves the scan reaches new helpers.

**D5. B4.1 — skew-at-drain reuse could be a routed-not-shared clone.** A builder could
copy the heartbeat skew assembly into the drain handler; both stay green. Closed: B4.1
mandates ONE extracted helper and a MUTATION proof (change the shared template constant →
BOTH actions' pins red; a green caller is a private copy). The contract author writes the
mutation proof, the adversary grades it.

**D6. B4.4 — the trailer's window-scoping admits "trailer lists ALL unacked
directives".** That wrong build passes any fixture whose directives all fit the window.
Closed: the mandatory elided-directive fixture (limit < directive count) — B4.4
names it precisely because the small-N monoculture is the repo's four-time offender.

**D7. B4 header counts — `total = len(entries)` wrong build.** Closed: fixture with
`total_pending > limit` (B4.1's elision fixture doubles as the discriminator). Both
numbers asserted independently.

**D8. B5 — a render that re-orders or dedupes ack entries.** Passes any single-seq
fixture. Closed: the R1 non-adjacent duplicate fixture (`[s1, s2, s1]`) asserted at the
RENDER (entry order == request order), not only at the ledger.

**D9. T1 — the subclass override could be silently bypassed.** (a) A future refactor
constructs plain `FastMCP` → T7.2 pin red. (b) A second dispatch path (an extension
calling `_tool_manager.call_tool` directly) would skip the override — searched: no such
caller exists in the tree today; the T7.1 ∀-tools pin covers every REGISTERED tool
including the synthetic extension tool, and any future direct-dispatch path would have to
be added to `server.py`, where the coverage pin's set-equality on `list_tools()` does not
see it — **named bound:** the funnel guards tool dispatch through the MCP protocol
surface; an in-process caller invoking a tool function directly is not a tool call and is
not traced. Re-open trigger: any production code path that calls tool handlers outside
`call_tool`.

**D10. T3 — ordinal-as-count misuse.** The very first consumer (packet 06) could compute
`max−min`. Closed: T7.6's consumers-count-rows pin + the §5 gap law cited in the column's
schema comment; 06's packet file inherits the constraint via B10-style disposition (this
doc IS the record).

**D11. T4 — the identity design's own failure modes, attacked as required:**
- *Spoofing:* `agent=` is honor-system (comms-subsystem §Honest limits — identity is
  honor-system until packet 39). The trace inherits exactly that trust level, no more —
  recorded so 39 knows this surface exists.
- *The generic-key rule harvests a coincidental `agent` param on some future non-comms
  tool.* If that param means something else, the column mixes vocabularies. Accepted as
  a bound WITH a tripwire: the coverage pin's fixture registry names every tool; a new
  tool declaring `agent` shows up there, and its fixture author meets this paragraph.
  (The alternative — a tool-name allowlist — is the six-defeats instrument shape;
  refused.)
- *The transport correlator could be READ as an identity by a lazy consumer.* Closed in
  the schema comment + T4.2's wording ("correlator, never identity") + 06's named
  decision point (T4.4).
- *A client harness change (connection pooling) could silently merge agents onto one
  transport session.* The join then degrades VISIBLY (multi-agent transport sessions) —
  the design's honesty property is that this failure is observable in the data itself,
  not assumed away.

**D12. T5 — the awaited emission doubles the store round-trips of every cheap call.**
Measured posture: one indexed CREATE inside one transaction; the re-open trigger (>5% p50
on read tools at deploy smoke) is NAMED with its remedy (drained queue + settle-step in
the pin). Not left open-ended.

**D13. T7.1 — `MINIMAL_ARGS` could drift into a maintenance tax that gets deleted.**
The registry is ~20 one-line entries and the pin's failure message must teach exactly
what to add (the actionable-denial law). Accepted cost; the alternative (no ∀ gate) is
#131.

**D14. C — the eval could pass on model memorization or fail on model whim.** Closed
both directions: grading is machine-field-only (no prose judging); 3 consecutive runs on
a pinned model (whim); fixtures regenerate from live renders (memorization of stale
renders fails loudly when renders change). Residual: the floor model gates — a render
only Opus parses would pass nothing here anyway (Sonnet gates); a render only Sonnet
parses cannot exist (capability is monotone in this population — assumption NAMED, and
the packet-exit Opus/Fable receipts are its spot-check).

**D15. Blindness risk (this document's own).** I could not read INDEX@HEAD or the struck
corpus; if the operator's rulings 1–4 (spawn brief) were superseded after my spawn, this
doc lags. Mitigation: every operator-authority item is quoted with its provenance so the
lead can diff against the record cheaply.

---

# E. Escalations (forks + recommendations; operator or lead authority — never silently chosen)

**E1. [SPEND] The consumer-eval instrument (C).** New model-API spend: ~8 questions × 3
runs per gate + two one-time receipts. Small but recurring, and instrument-creation is
operator-visible territory. **Recommend:** approve as specced; the floor-model gate is
the cheapest checkable form of "the client is satisfied" I could derive.

**E2. [OPERATOR-AUTHORIZATION-REQUIRED, recommend deferring] The stale packet label in
the committed contract.** `test_comms_tool.py`'s section banner (at `0223291`, above
`TestNewActionSpecs`) says *"everything in this file … is packet 03a (the surface;
deploys both)"* — under the three-way split those pins are packet 03b's. Comment-only,
but it is served prose inside an immutable file teaching the wrong packet to the next
reader. Fix costs one authorized comment amendment; **recommend** bundling it with
whatever authorized contract wave 03b's contract phase runs, not a standalone amendment.

**E3. [FORK] Drain skew block (B4.1).** Ruled IN with the divergence recorded (the
shipped publish promise says "next heartbeat"; drain-skew makes it an under-claim). The
alternative — drain stays skew-free until 04's footer — costs a mid-phase brief bump its
highest-probability delivery point. **Recommend:** as ruled (skew at drain, shared
helper). If the operator prefers the publish promise literally exhaustive, the literal
edit is a committed-registry amendment (strengthen-only test: it widens the promise) —
priced at one authorized amendment + proof updates; NOT recommended.

**E4. [FORK, recommend as ruled] `_MAX_DRAIN_LIMIT = 50` and
`DEFAULT_COMMS_DRAIN_LIMIT = 20` (B6).** Both are ruled defaults with mechanism
(clamp+disclose, config-driven) independent of the values; the operator may re-tune the
constants freely — the design only insists the MECHANISM not change.

**E5. [INTERPRETATION FLAGGED] The telemetry failure-posture carve-out from DESIGN-LAW
§14 (T5.1).** I rule §14 governs durable lore data and telemetry-about-calls is not it;
the carve-out is narrow (log-loud, pin-guarded, smoke-verified). Flagged because reading
scope into a design law is the operator's to confirm. **Recommend:** confirm; the
alternative (tool calls fail when the trace write fails) couples the entire served
surface to an observability row.

**E6. [FORK, recommend NO for 03b] The `fastmcp` standalone-package migration** (T1;
scout fork 3's second arm). It has a real middleware API; adopting it is a server-wide
dependency swap. **Recommend:** file as its own ledger item with a named re-open trigger
(the day a SECOND cross-cutting concern needs the dispatch seam — auth (packet 39) being
the obvious candidate — the subclass stops being minimal and the migration gets priced).

**E7. [FORK, recommend keep] `set_status` param name (B2.5).** The name promises a
status write the mechanism doesn't perform; the committed spec pins the name. Renaming
(e.g. `asks=`) would be a clearer surface but costs an authorized amendment to the
committed spec pin + the design source's tool table. **Recommend:** keep the name, teach
the semantics in the schema (as ruled); revisit only if the C-battery shows consumers
misread it (that would be MEASURED confusion, the legitimate re-open trigger).

**E8. [SCOPE CONFIRMATION] Drain's own unbounded pending read.** `MessageLedger.drain`
fetches ALL unstamped edges to compute honest totals (then windows client-side). Bounded
by unread volume (self-limiting: drains stamp), but an agent that never drains
accumulates an unbounded read. This is 03a's shipped ledger internals — OUT of 03b's
scope per the packet file — surfaced here per the everything-you-notice law.
**Recommend:** a findings-ledger row (perf, not correctness; the `(out, seen_at)` index
serves the WHERE), owner packet 05 (which touches drain for `since=` anyway). Not
silently dropped: this paragraph is the surfacing.

**E9. [LEDGER HYGIENE] #147.** T7.9's deploy smoke closes it with a production receipt;
the lead transitions the finding at packet exit (the scout left it open, correctly).

---

# F. Residuals noticed (not mine to fix; surfaced per standing law)

1. `trace.token_cost`/`trace.model` remain writer-less after 03b (scout §6.3) — the
   generic seam has no token accounting. Left as-is (option columns are free); named so
   the next reader meets it deliberately.
2. `cosine_floor` staleness (scout §6.4) — owned by packets 10/11; re-confirmed only as
   still-reported at my read; nothing here changes it.
3. The `refs` list is uncapped at the ledger (B3 renders cap the DISPLAY only). A
   thousand-entry refs list is storable. Perf/attention nuisance, not correctness;
   candidate findings row for 05's history surface.
4. `comms-subsystem.md`'s tool table still carries the pre-split drain row (`since=`,
   skew line) — packet 05/this doc supersede pieces of it; the shared reference should
   gain a one-line pointer at its next authorized edit (it was edited during the struck
   session; I read it at `0223291` and do not know its HEAD state — the lead should
   reconcile).
5. The committed contract's `test_drain_defaults…` fixture reads `rendered.count("#")
   >= 5` — under B4's fenced-body render, a BODY containing `#` inflates that count.
   The fixture's bodies (`message {i}`) contain no `#`, so it stays green as written —
   noted so the contract author does not "fix" it into weakness, and so nobody feeds it
   hash-bearing bodies without re-reading it.

---

*Diff-readiness note: every ruling above is section-numbered (B1–B11, T1–T8, C1–C4,
D1–D15, E1–E9, F1–F5) for citation; where a ruling restates committed-pin content it says
so and cites the pin rather than claiming novelty.*
