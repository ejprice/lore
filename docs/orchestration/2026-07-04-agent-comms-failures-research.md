# Solutions Report — Multi-Agent Comms Failures in Claude Code Orchestration

**Prepared:** 2026-07-04 · **For:** team-lead orchestrating teammates via the Agent tool (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`), CLI, Linux.
**Recency:** all sources 2026, verified against primaries (raw CHANGELOG, code.claude.com docs, `anthropics/claude-code` GitHub issues via `gh`, project repos). Claude Code changelog band **2.1.178 → 2.1.201** (≈ June–early July 2026; 2.1.196 ≈ 2026-06-30). **The changelog has no calendar dates — only version numbers.**

**Scope:** failure **1 (inbox half-processing / drop to busy agents)** and failure **2 (ambiguous idle)**. Permission stalls (failure 3) excluded per brief.

> ### The headline finding (this reframes everything below)
> The busy-agent message-drop is a **real, currently-OPEN, maintainer-UNACKNOWLEDGED bug** in Claude Code as of 2026-07-04 — not something an upgrade fixes. The canonical thread is **[#50779](https://github.com/anthropics/claude-code/issues/50779)** (open since 2026-04-19; issues #57487 and #58180 were closed as duplicates of it), and fresh reports land on the very latest builds: **[#73489](https://github.com/anthropics/claude-code/issues/73489)** (v2.1.198), **[#74113](https://github.com/anthropics/claude-code/issues/74113)** / **[#74112](https://github.com/anthropics/claude-code/issues/74112)** (v2.1.200), **[#70087](https://github.com/anthropics/claude-code/issues/70087)** (v2.1.183). **No Anthropic maintainer has commented on any of them** (verified comment-authorship: every human commenter is association `NONE`; only bots otherwise). **Do not wait for an upstream fix, and do not expect `claude update` to solve it.** The fix must live in *your* orchestration layer. The entire affected community has converged on the same answer: **stop trusting push delivery; use a durable pull channel + explicit acks.**

---

## Root cause — why mid-flight inbox delivery is unreliable for busy agents

Two layers. Community reverse-engineering (with JSONL-transcript receipts) nails Layer A; your own "item 3 but not 1–2" observation is Layer B.

### Layer A — the harness gates inbox→context injection on `stop_reason=end_turn` (OPEN bug)
The mailbox has **no documented delivery, ordering, or acknowledgment guarantee**. The agent-teams doc only says *"Automatic message delivery: when teammates send messages, they're delivered automatically to recipients. The lead doesn't need to poll for updates."* — silent on the busy case. (Source: https://code.claude.com/docs/en/agent-teams.)

The community-verified mechanism, from **#50779** (commenter `ericonuki`, 2026-04-19, verbatim): *"the `<teammate-message>` blocks never reach the lead's conversation at all while the assistant is in a `stop_reason=tool_use` chain… The harness *does* poll the inbox file on schedule (verified: `"read": false → true` flips at the polling interval) but the next layer — turning a `read:true` inbox entry into a `<teammate-message>` user turn — is gated on the assistant emitting `stop_reason=end_turn`."* He proved it with transcript ordering: three queued messages flush only after an `end_turn`, and **keystrokes/user input do NOT flush them — only `end_turn` does.**

Three consequences, each independently corroborated:
1. **A busy agent (in a `tool_use` chain) never hits the `end_turn` boundary, so its inbox never drains.** This is exactly why idle/standing-by agents receive fine and busy ones don't — the split you observed. Also confirmed for the user→agent direction in **#73118** ("long agent turns block queued user messages… pending messages lost on disconnect").
2. **Delivery is best-effort in-memory and races the turn-boundary context snapshot** (**#70087**, `kcarriedo`, verbatim): *"If delivery is best-effort in-memory and the recipient is at a turn boundary when the send happens, the body can arrive after the context snapshot for that turn was already assembled."* → the message (or just its *body*) is lost.
3. **`SendMessage` returns success unconditionally** even when the body didn't land (**#70087**, **#71429**, **#74113**) — so the sender gets *no lossy-delivery signal*. This is what makes it read as silent half-processing rather than an error. **#71429** is an open enhancement request for exactly the missing piece: transport-level `sent_at` / `seq` / `message_id` + delivery receipts + dedup.

The named CHANGELOG fixes (below) each patched *one specific window* of this bug but **not the core `end_turn` gate** — which is why drops persist on 2.1.198–2.1.200.

### Layer B — absorption-layer partial processing (your "item 3, not 1–2"; model behavior, not delivery)
Even when a multi-item message *is* delivered (at the next `end_turn`), it lands deep in a long working context and the model may act on only part of it. **This precise per-item partial-absorption symptom does not appear in any public issue** (the delegated search for "partially processed"/"half-processed"/"only acted on part" came up empty) — it is your own observation (matches your MEMORY.md "agent-inbox half-processing" note), unreported upstream. It is **not** fixed by a version bump; it is a prompt/context-salience problem, which is why your single-item-pings discipline is correct. The fix is to make each directive atomic and to move the *guarantee* into an ack/ledger layer.

### What upgrading does and doesn't do
The CHANGELOG closed specific drop windows — worth having, but **not a cure**:
- **2.1.178** — *"messages sent while it finishes its turn are no longer dropped"* (the turn-*completion* instant, a subset of Layer A).
- **2.1.198** — *"messaging a stuck teammate wakes it to retry immediately"* + *"a teammate that dies on an API error now reports 'failed' to the lead."*
- **2.1.199** — *"Fixed `SendMessage` silently misrouting when a re-spawned agent reuses a previous agent's name."*
- **2.1.77** — *"`SendMessage` now auto-resumes stopped agents in the background instead of returning an error."*
- History of the same bug family: **2.1.162** (deep `$TMPDIR` broke SendMessage), **2.1.105** (*"inbound channel notifications silently dropped after the first message"*), **2.1.76** (rapid messages queued one-at-a-time), **2.1.33** (tmux teammates couldn't send/receive at all).

But open reports on 2.1.198–2.1.200 (#73489, #74113, #74112) prove the **core gate is unfixed**. Upgrade for the named-window fixes and the 199 misroute *detection*; do not treat it as the solution.

---

## Ranked candidate solutions (best-fit first)

### 1. Durable store-and-forward + transcript-as-truth (the community-converged fix; defeats the open gate)
- **What:** Stop trusting push delivery for anything that must not be lost. Route it through a **durable channel the recipient pulls on its own schedule**, and treat the **recipient's own record** — its JSONL transcript, or a ledger row it wrote — as the authoritative "delivered/processed" signal, **never** the inbox `read` flag or a `SendMessage` success return.
- **Source/maturity:** Convergent across **every** affected thread — #50779, #70087, #71429, #74113 all independently recommend store-and-forward via files ("write to a location the receiver controls, read at a time of the receiver's choosing") and/or reading the recipient's JSONL transcript as the ground-truth delivered signal. `Butanium` shipped a concrete local version in #50779 (2026-05-12): an **MCP `fetch_unread` tool that reads the recipient's transcript** instead of the flaky inbox flag. **Maturity: documented community pattern with a working reference implementation.**
- **Maps to failure 1 (root cause):** the recipient pulls at *its* turn boundary, so the `end_turn` gate is irrelevant — there is nothing "in flight" to race or drop. Removes the unconditional-success blind spot because "processed" is proven by the recipient's own artifact.
- **Best-fit for you:** you already run a durable MCP ledger for fleet coordination — **make it the sole channel for must-not-lose signals** (authorizations, scope changes, GO). Lead writes a directive row; the agent reads it when it next reaches a boundary and writes back a completion/ack row. You're 80% here; the change is *policy* (never authorize via SendMessage text) plus using the ledger row — not the mailbox flag — as proof.

### 2. Ack-required protocol (make lossy delivery *detectable*, then re-ping once)
- **What:** Since SendMessage reports success even on loss, add the missing receipt yourself: every must-deliver directive gets `state=sent`; recipient flips it to `state=ack` then `done` via a tool call; a lead-side check flags any `sent` row older than a phase-appropriate threshold and re-pings **exactly once**.
- **Source/maturity:** The gap is explicitly documented upstream (**#71429**, open enhancement for transport-level ack/seq/message_id). Ready-made if you'd rather not hand-roll: **MCP Agent Mail** — Rust MCP server, MIT, © 2026 Jeffrey Emanuel, `cargo install mcp_agent_mail_rust` (https://github.com/Dicklesworthstone/mcp_agent_mail_rust) — ships **`ack_required=true` with the server surfacing "overdue acknowledgments to operators,"** project-scoped inboxes (`resource://inbox/{Agent}`), 34 MCP tools, TTL file reservations. (Primary page verified 2026-07-04.) The **Message Bus Claude Code skill** (https://mcpmarket.com/tools/skills/message-bus-coordination) offers file-queue + ack-tracking + heartbeats (page 429'd on fetch; treat as documented-pattern, verify). **Maturity: community shipped (Agent Mail, MIT) / documented pattern.**
- **Maps to failure 1:** converts silent loss into a visible, retryable "ack overdue" event — no more ground-truthing every completion by hand. Also directly counters the documented *"Task status can lag"* limitation.
- **Adoption sketch:** add an `ack`/`acked_at` column to your existing ledger (cheapest — no new server). Reserve MCP Agent Mail for if/when you scale to the 40–50-agent regime it targets.

### 3. `git log`/filesystem check → exactly one re-ping, on any bare idle (recovers dropped reports)
- **What:** Codify the recovery SOP that the field reports say works: on a bare idle notification with no content, **verify the agent's real output first** (git log / filesystem / ledger), *then* send **exactly one** re-ping — this recovers the withheld report "in nearly every case."
- **Source/maturity:** **#74113** author's standing SOP, verbatim: *"on any bare idle notification, verify the agent's actual output via `git log`/filesystem first, then send exactly one re-ping"* (recovers the full report "in nearly every case … the agent produced the report content; only the final delivery was dropped"). Guard against re-ping spam with `Butanium`'s **PreToolUse hook on SendMessage that blocks defensive re-pings until an `end_turn` flush** (#50779). **Maturity: documented community practice + reference hook.**
- **Maps to failure 1 (recovery) + failure 2:** turns a dropped-report idle into a one-shot recovery instead of a lost result; the mandatory ground-truth-first step is also your failure-2 disambiguation.
- **Note:** this is partly your current practice — the additions are (a) the *exactly one* re-ping rule and (b) the PreToolUse guard so agents/lead don't spam re-pings that themselves get dropped.

### 4. Upgrade to ≥ 2.1.199 (2.1.201) + never reuse teammate names — necessary hygiene, not sufficient
- **What:** `claude update`; confirm `claude --version` ≥ 2.1.199. Give every respawn a **fresh unique name**; continue an agent via `SendMessage({to: <agentId>})`, never a reused human name.
- **Source/version:** CHANGELOG 2.1.178 / 2.1.198 / 2.1.199 / 2.1.77 (verbatim above). Name-reuse misroute is **2.1.199**; `resume` param removed in **2.1.77**; **2.1.69** fixed teammates accidentally nesting via the `name` param — names are load-bearing and collision-prone. **Maturity: shipped fixes + practice.**
- **Maps to failure 1:** closes the *named* windows and — critically for your **respawn-with-consolidated-brief** pattern — pre-2.1.199 SendMessage silently misrouted to a reused-name's *dead* mailbox, a textbook match for "3 messages, zero effect." Fresh names fix this even on old builds; upgrading makes the misroute a visible "retarget" error.
- **Reality check:** open issues on 2.1.198–2.1.200 prove this does **not** fix the core busy-agent gate. Do it, but layer #1–#3 on top.

### 5. `TeammateIdle` hook as an idle-gate + ground-truth probe (failure 2; works headless)
- **What:** Register a `TeammateIdle` hook (Command or Agent type) that runs **at the moment a teammate is about to idle** and executes your ground-truth check. If a ledger item is still open or a background process is live, **`exit 2` with feedback** to keep it working / force a status report; otherwise allow idle. Makes "idle" *mean* "verified done."
- **Source/version:** CHANGELOG **2.1.33** (event added), **2.1.69** (*"Fixed `TeammateIdle` and `TaskCompleted` hooks to support `{"continue": false, "stopReason": "..."}` to stop the teammate"*); agent-teams doc: *"`TeammateIdle`: runs when a teammate is about to go idle. Exit with code 2 to send feedback and keep the teammate working."* **Maturity: shipped feature.**
- **Maps to failure 2:** automates, at the exact idle boundary, the disambiguation the lead does by hand — a teammate can't silently settle into ambiguous "available" without your check running. Unlike #6, it doesn't depend on the agent-view being open.
- **Caveat:** the `TeammateIdle` JSON payload schema (does it name *which* teammate / *why*) is **not documented** in the primary pages; it carries the common `agent_id` field, so key your lookup off `agent_id` + your ledger, not a hoped-for "reason" field.
- **Adoption sketch:** settings.json `TeammateIdle` → Command hook: read `agent_id` from stdin JSON, look up its open ledger tasks; any unfinished → `exit 2` with `"Ledger task <id> still open — confirm done or report blocker"`; else exit 0.

### 6. `Notification` hook: `agent_needs_input` vs `agent_completed` (failure 2 — but verify the caveat)
- **What:** `Notification` hook matching `agent_needs_input` and `agent_completed`, routed to a lead-visible signal/ledger row.
- **Source/version:** CHANGELOG **2.1.198** — *"Added background agent notifications in `claude agents` — sessions that need input or finish now fire the `Notification` hook (`agent_needs_input` / `agent_completed`)."* Matcher values also confirmed in the primary hooks doc matcher table (https://code.claude.com/docs/en/hooks). **Maturity: shipped feature.**
- **Maps to failure 2:** *directly* splits the undifferentiated "available" into **needs-input (blocked/waiting)** vs **completed-or-failed (done)** — the distinction `idleReason` can't make.
- **⚠️ Load-bearing caveat — TEST BEFORE RELYING:** a hooks-guide (secondary) states these two matchers **"fire only while the agent view is open"** (require v2.1.198+). I could **not** confirm that firing-condition in the *primary* hooks page (it lists the matchers but omits per-value conditions). **If true, this likely won't fire for a headless/background orchestrator** — so probe it empirically (spawn a teammate, block it on input, watch for `agent_needs_input`). If it doesn't fire headless, use #5 instead. Note also that the underlying idle signal is known-imperfect: upstream **#67165** (open, exact match for your ambiguity) requests enriching `idleReason` into `available | waiting-on-background-task | waiting-on-wakeup`, and **#60199** notes the substantive reply *sometimes* rides in the idle notification's `summary` field inconsistently, while **#74112** reports duplicate/stale idle notifications — so treat any single idle signal as advisory, cross-checked against the ledger (#1).

### 7. Heartbeat / watchdog — the third state: STALLED vs busy-on-background
- **What:** Long-running agents touch a heartbeat (file mtime or ledger row) every N tool calls; a lead-side watchdog compares against a `stale_after_seconds` threshold → STALE / MISSING / COMPLETED. Fresh heartbeat = live-but-busy (leave alone); stale = stalled (respawn).
- **Source/maturity:** Community, current: **ARIS** `watchdog.py` (liveness by state-file mtime vs `stale_after_seconds`; `iteration_log.py` forces a structural pivot at `stale_count ≥ 2`, human escalation at `≥ 4`) — https://github.com/wanshuiyin/auto-claude-code-research-in-sleep ; **Siigari/claude-heartbeat** (heartbeat hook + inbox/outbox) — https://github.com/Siigari/claude-heartbeat ; Message Bus skill's worker-heartbeats (#2). **Different-scope built-in:** CHANGELOG **2.1.196** *"The streaming idle watchdog is now on by default … aborts and retries when a response stream produces no events for 5 minutes"* (`CLAUDE_ENABLE_STREAM_WATCHDOG=0`) — catches **stream stalls**, not semantic idle-ambiguity. **Maturity: community pattern + partial built-in.**
- **Maps to failure 2:** supplies the STALLED state that #67165 says `idleReason: "available"` conflates with done/waiting. Reuse your ledger for the heartbeat row; adopt the ARIS framework only if you want its pivot/escalation counters.

---

## Comparative / transferable (patterns only — not "switch platforms")

- **LangGraph 1.2** (LangChain, **2026-05-11**): an agent run is **durable graph execution** — checkpoints state to SQLite/Postgres **after every node**; `interrupt`/resume persists state and resumes from the exact point on input; `Command` objects do explicit agent-to-agent handoff. **Transferable lesson (you're already living it):** put coordination state in a durable store and make handoffs *explicit resume points*, not fire-and-forget messages — precisely #1/#2. The durable store, not the chat channel, is the source of truth. Sources: https://docs.langchain.com/oss/python/langgraph/overview , https://github.com/langchain-ai/langgraph.
- **Maildir-style file mailbox with atomic-move ack** (`avivsinai/agent-message-queue`, https://github.com/avivsinai/agent-message-queue): message-per-file queue where the atomic file move *is* the delivery/ack state — the minimal, dependency-free shape of #1/#2 if you'd rather not run an MCP server or extend the ledger. Verify recency before adopting.

---

## Not viable / stale (examined and rejected)

- **Waiting for an upstream fix to the busy-agent drop** — the core bug (#50779) is open since 2026-04-19 with **zero maintainer comment** and fresh dupes on the latest builds; not a plan.
- **Relying on `claude update` alone to fix failure 1** — open reports on 2.1.198–2.1.200 prove the core `end_turn` gate is unfixed. Necessary hygiene, not a solution (see #4).
- **Trusting the inbox `read` flag or a `SendMessage` success return as "delivered"** — both flip/return positive even when the body never lands in context (#50779, #70087); use the recipient's transcript/ledger row instead (#1).
- **Polling the mailbox from the lead** — docs say the lead "doesn't need to poll," but automatic delivery is the unreliable thing; poll the **ledger**, not the mailbox.
- **`TeamCreate` / `TeamDelete` tools** — *removed in 2.1.178*; any "create a team first" guide is stale (one implicit team per session now).
- **`teammateMode: "auto"` as default** — default became `"in-process"` in 2.1.179; split-pane-by-default tutorials are stale.
- **Relaying authority / GO through another teammate** — hardened out in **2.1.166**: relayed SendMessage carries no user authority; auto mode treats relayed approval as untrusted. Don't build a workaround on teammate-to-teammate authority relay.
- **`Agent`-tool `resume: true`** — removed in 2.1.77; use `SendMessage({to: agentId})`.
- **Treating `idle_prompt` as a done-signal** — it fires "Claude is done and waiting for your next prompt," i.e. it *is* the ambiguous signal, not a fix.
- **SendMessage-to-idle to "wake" an agent expecting reliable resume** — #45684 ("spawns a new instance instead of waking it") was closed **NOT_PLANNED**; and #54463 (resumed-lead never delivers teammate messages) also **NOT_PLANNED** — so post-restart delivery is a known non-goal; rebuild the team after `/resume` (matches the doc's stated limitation).

---

## Upstream issues worth subscribing to / +1'ing (all open, 2026, maintainer-unacknowledged)
- **#50779** — canonical `end_turn`-gating root cause (busy agents don't drain inbox).
- **#74113** / **#74112** — dropped final report + duplicate/stale idle floods (v2.1.200).
- **#70087** — teammate↔teammate body not delivered (in-memory race).
- **#71429** — request for transport-level ack + seq + message_id (the missing guarantee).
- **#67165** — enrich `idleReason` to disambiguate done / waiting / stalled (exact match for failure 2).
- **#73489** — lead can't read teammate messages, marked a regression (v2.1.198).
- **#73118** — long turns block queued user messages; lost on disconnect.

---

## Sources (all fetched/verified 2026-07-04)
- CHANGELOG (raw, primary): https://raw.githubusercontent.com/anthropics/claude-code/refs/heads/main/CHANGELOG.md — highest version 2.1.201; **no calendar dates**.
- Agent teams doc: https://code.claude.com/docs/en/agent-teams (states "as of v2.1.178").
- Hooks reference: https://code.claude.com/docs/en/hooks (Notification matcher table incl. `agent_needs_input`/`agent_completed`).
- Agent SDK: https://code.claude.com/docs/en/agent-sdk/overview , .../hooks.
- GitHub issues (primary, via `gh`): #50779, #57487, #58180, #70087, #71429, #73118, #73489, #74112, #74113, #67165, #60199, #45684, #54463 — `anthropics/claude-code`.
- MCP Agent Mail: https://mcpagentmail.com/ , https://github.com/Dicklesworthstone/mcp_agent_mail_rust (MIT, © 2026).
- Message Bus skill: https://mcpmarket.com/tools/skills/message-bus-coordination (429 on fetch; search-index description).
- ARIS watchdog: https://github.com/wanshuiyin/auto-claude-code-research-in-sleep · claude-heartbeat: https://github.com/Siigari/claude-heartbeat · agent-message-queue: https://github.com/avivsinai/agent-message-queue.
- LangGraph: https://docs.langchain.com/oss/python/langgraph/overview , https://github.com/langchain-ai/langgraph (1.2 released 2026-05-11).
- Stream watchdog default-on: 2.1.196 (~2026-06-30), https://therouter.ai/news/claude-code-2196-org-default-models-stream-watchdog-routing/.
