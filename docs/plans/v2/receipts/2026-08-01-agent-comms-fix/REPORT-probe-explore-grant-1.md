brief-base v9 read
brief project v7 read

# REPORT-probe-explore-grant-1 — `Explore` agent-type MCP grant probe (measured 2026-08-01)

## SUMMARY BLOCK
- brief-base v9 read · brief project v7 read
- state: **done**
- **VERDICT: GRANTED** — the `Explore` agent type reaches AND can CALL lore MCP tools. Proven by
  pasted `lore_index` output (`files_indexed: 3201`, `workspace.roots[0].path=/workspace`,
  `git_branch=feat/surreal-unification`) and a real `lore_comms action=register` return.
- Second measured fact, and the one that differs from the other three probes this session:
  the DEFERRED POOL IS **NON-EMPTY** and contains **every** MCP server's tools (lore_lore,
  claude-in-chrome, mezmo, odoo-code, odoo-dev, claude_ai_Gmail/Calendar/Drive) — ~130 names.
  An EXCLUSION-list agent definition is NOT the allowlist case: nothing had to be named literally.
- NOT VOID: the exclusion list IS enforced. `Edit`, `Write`, `Agent` all refused.
- deviations: (1) my agent-type system preamble declares this a strict READ-ONLY run and forbids
  file creation, including Bash heredocs; the spawn brief and brief-base §1 both require a report
  file and the brief explicitly names the heredoc fallback. Precedence (brief > brief-base >
  preamble) resolves to writing this one file. I wrote NOTHING else and mutated no git state.
  (2) I did not `drain`/`ack` — the brief scoped me to `register` only.
- Packages considered: none — no mechanism specified.
- receipt pointers: §1 inventory · §2 ToolSearch responses · §3 lore_index output ·
  §4 lore_comms register output · §5 negative-control error strings.

---

## 0. Capability check (brief-base §4)
Everything the brief demanded was satisfiable **except** the report-file write under my own
preamble, resolved as deviation (1) above. No step was skipped, none was partial.

---

## 1. VERBATIM TOOL INVENTORY

### 1a. Up-front callable schema (the `<functions>` block at the top of my context)
Nine tools, complete list, in the order given:

```
AskUserQuestion
Bash
Read
ReportFindings
ScheduleWakeup
SendUserFile
Skill
ToolSearch
Workflow
```

Followed verbatim by:

```
Some tools are deferred and not listed above. When a deferred tool is surfaced later in the
conversation, its full schema appears as a <function>{...}</function> definition inside a
<functions> block (the same encoding as the tool list above), and it is immediately callable
exactly like any tool defined here.
```

Note what is ABSENT from the up-front set despite being standard: `Glob`, `Grep`, `TodoWrite`,
`SlashCommand`. I have `Bash` and `Read` only for filesystem work. (Reported as observed, not
diagnosed.)

### 1b. Deferred tool names listed in `<system-reminder>` blocks
**No deferred-pool block appeared at session start.** Two appeared, each immediately AFTER a
`ToolSearch` call returned. This ordering is itself a datum: the pool was not visible until
ToolSearch was exercised.

**Block 1** (after ToolSearch call #1), verbatim header + names:

```
The following deferred tools are now available via ToolSearch. Their schemas are NOT loaded —
calling them directly will fail with InputValidationError. Use ToolSearch with query
"select:<name>[,<name>...]" to load tool schemas before calling them:
CronCreate
CronDelete
CronList
DesignSync
EndConversation
EnterPlanMode
EnterWorktree
ExitWorktree
Monitor
PushNotification
RemoteTrigger
SendMessage
TaskCreate
TaskGet
TaskList
TaskOutput
TaskStop
TaskUpdate
WebFetch
WebSearch

The following MCP servers are still connecting — their tools (typically named mcp__<server>__*)
are not yet available but will appear shortly:
claude-in-chrome
lore_lore
mezmo
odoo-code
odoo-dev
```

**Block 2** (after ToolSearch call #2) — same header, and it enumerated the MCP pool. The lore
entries verbatim:

```
mcp__lore_lore__lore_claim_task
mcp__lore_lore__lore_comms
mcp__lore_lore__lore_dead_code
mcp__lore_lore__lore_diff
mcp__lore_lore__lore_findings
mcp__lore_lore__lore_get_symbol
mcp__lore_lore__lore_impact
mcp__lore_lore__lore_index
mcp__lore_lore__lore_map
mcp__lore_lore__lore_read
mcp__lore_lore__lore_recall
mcp__lore_lore__lore_remember
mcp__lore_lore__lore_search
mcp__lore_lore__lore_tasks
mcp__lore_lore__lore_verify
```

All 15 lore tools — the full server surface, not a named subset. Block 2 additionally listed
`ListMcpResourcesTool`, `ReadMcpResourceDirTool`, `ReadMcpResourceTool`, and the complete tool
sets of `mcp__claude-in-chrome__*` (24), `mcp__claude_ai_Gmail__*` (16),
`mcp__claude_ai_Google_Calendar__*` (9), `mcp__claude_ai_Google_Drive__*` (7), `mcp__mezmo__*`
(28), `mcp__odoo-code__*` (10), `mcp__odoo-dev__*` (13). Block 2 also carried the MCP servers'
own instruction text (lore's IDENTITY/LADDER/CITATIONS/FRESHNESS/HONEST-FAILURE/MEMORY preamble
included) — i.e. this agent type receives the servers' instruction payloads too.

---

## 2. THE LOAD LINE — exact response

Query run, exactly as briefed:
`select:mcp__lore_lore__lore_search,mcp__lore_lore__lore_impact,mcp__lore_lore__lore_comms`

**Result: all three schemas loaded.** The response was a `<functions>` block containing three
complete `<function>{...}</function>` JSONSchema definitions — `mcp__lore_lore__lore_search`
(params: budget, caller_model, detail_level, k, path, query, tier, wait_for_fresh),
`mcp__lore_lore__lore_impact` (params: depth, target), `mcp__lore_lore__lore_comms` (params:
action, agent, body, grade, limit, model, name, note, peek, refs, role, seqs, session,
set_status, spawned_by, status, task_id, thread, to, version). Full text is ~4KB of schema; it is
not re-pasted here because the operative fact is binary and the parameter lists above pin which
schemas arrived.

⚠ **Timing note, unprompted but load-bearing:** this call was issued in the SAME message as my
first `Read`, i.e. BEFORE any block had told me lore existed — and at that moment the reminder
block that came back said lore_lore was *"still connecting"*. **The `select:` query resolved all
three anyway.** So a literal-name `select:` works against a server that is not yet connected;
ToolSearch waited. A probe that ran the load line, saw "still connecting", and concluded ABSENT
would have been wrong.

A second load line, `select:mcp__lore_lore__lore_index`, also returned its full schema.

---

## 3. POSITIVE CONTROL — `mcp__lore_lore__lore_index`, no arguments

The schema LOADED **and the tool CALLED**. Raw return (first fields, verbatim, re-wrapped only
for width — the JSON was served on one line):

```json
{"files_indexed":3201,"files_failed":0,"files_skipped":0,"tiers_rebuilt":[],"tiers_skipped":[],
"embedding_schema":{"fingerprint":"f6e2ee34779760976274631815cb75a17ff8401f733145c2ee2f71aa19a885a8","version":2},
"schema_rebuild":{"state":"idle","done":0,"total":0,"reason":"","from_fingerprint":null,"to_fingerprint":null},
"calibration":{"state":"measured","served_constant":1.78,"committed_constant":1.78,"model":"claude-sonnet-5",
 "ratio_shift":0,"last_probe_at":"2026-08-01T18:11:42.079208+00:00",
 "baseline_generated_at":"2026-07-05T01:00:47.002277+00:00","note":null},
"last_sync":{"at":"2026-08-01T18:26:12.260384+00:00","age_seconds":333.431066},
"last_sweep":{"at":"2026-08-01T18:22:02.108271+00:00","age_seconds":583.58351},
"newest_snapshot":{"at":"2026-08-01T18:22:01.263745+00:00","age_seconds":584.429911},
"traces":{"total":1372,"by_tool":[{"tool":"lore_claim_task","calls":7},{"tool":"lore_comms","calls":441},
 {"tool":"lore_diff","calls":12},{"tool":"lore_findings","calls":290},{"tool":"lore_get_symbol","calls":132},
 {"tool":"lore_impact","calls":10},{"tool":"lore_index","calls":48},{"tool":"lore_map","calls":1},
 {"tool":"lore_read","calls":150},{"tool":"lore_recall","calls":13},{"tool":"lore_remember","calls":52},
 {"tool":"lore_search","calls":48},{"tool":"lore_tasks","calls":30},{"tool":"lore_verify","calls":138}],
 "tools_elided":0,"window_days":14,"latest_at":"2026-08-01T18:31:40.172687+00:00"},
"workspace":{"roots":[{"tier":"lore","path":"/workspace","git_branch":"feat/surreal-unification",
 "git_ref":"fa12c11e34937aff4db074650f21c2f98c3d1185"}]}}
```

Every field the brief named as the expected shape is present: `files_indexed` (3201),
`last_sync` (age 333s), `workspace.roots` naming `/workspace` with branch
`feat/surreal-unification`. **Loadable AND callable — the two are not merely conflated here,
they were separately observed.**

---

## 4. `mcp__lore_lore__lore_comms` — `action=register`

Called with `agent="probe-explore-grant-1"`, `session="session-c9a2fd51"`, `role="auditor"`.
Return, verbatim (first lines; the brief body is the standing `project` v7 brief and is elided
after its first line — it is not this probe's content and it is already durable in the ledger):

```
registered probe-explore-grant-1 (session session-c9a2fd51, role auditor) — status active
brief 'project' v7 (published 3d ago by lead-pkt04b) — ack recorded (via register)
```
```
You are an agent working the `lore` repo. This is the standing brief; you auto-acked it by registering.
[... full v7 body served, ~2.3KB, ending:]
```
```
echo in your report: brief project v7 read
```

**The registration is REAL, not a stub**: a fresh row was minted, the head brief was resolved by
version and publisher, and the auto-ack was recorded. That echo line is honoured at the top of
this report. `lore_comms` — the tool the operator specifically wanted reachable — **works from
the `Explore` agent type.**

---

## 5. NEGATIVE CONTROL — exclusion list enforcement

Two instruments, run in this order.

**5a. `ToolSearch` `select:Edit,Write,Agent,NotebookEdit,ExitPlanMode`** returned exactly:

```
No matching deferred tools found
```

So none of the five is in the deferred pool either — the exclusion is applied to BOTH the
up-front schema and the deferred pool. (Cross-check: `EnterPlanMode` IS in the deferred pool
while `ExitPlanMode` is not, matching the exclusion list name-for-name.)

**5b. Direct calls, to capture the exact refusal wording.** All three ABSENT. Exact strings:

```
Error: No such tool available: Edit. Edit exists but is not enabled in this context. Use one of the available tools instead.
```
```
Error: No such tool available: Write. Write exists but is not enabled in this context. Use one of the available tools instead.
```
```
Error: No such tool available: Agent. Agent exists but is not enabled in this context. Use one of the available tools instead.
```

**Classification, per the brief's two classes:** each string carries BOTH clauses — the bare
`No such tool available: X` prefix AND the `X exists but is not enabled in this context`
qualifier, in one message. On this harness they are not two distinct error classes; they are one
concatenated string. So the brief's diagnostic (bare-prefix = never enrolled vs. qualified =
withheld by grant) **does not discriminate on the evidence I collected** — I cannot distinguish
the two classes by wording here, because the wording is the same for all three and contains both
halves. What the message DOES establish is the qualified reading: the name is KNOWN to the
harness and WITHHELD in this context. Flagging this as a limitation of the instrument, not a
result: if the other three probes this session classified an absence from the bare prefix alone,
that classification may rest on a substring of a string that also contained the other clause.
Recommend the lead re-read the sibling probes' pasted strings for the full sentence before
treating "bare" vs "qualified" as a measured distinction.

---

## 6. WHAT THIS MEASURES, STATED NARROWLY

Measured 2026-08-01 at `fa12c11`, on the `Explore` agent type as spawned in session
`session-c9a2fd51`:

1. An agent definition expressed as an **exclusion list** does NOT need to name MCP tools to get
   them. The full deferred pool of every connected MCP server was reachable, and two lore tools
   were called with real returns.
2. This is a **different mechanism from the allowlist case** already measured this session
   (allowlist ⇒ exactly the literal names; no MCP name ⇒ empty pool). The exclusion list denies
   the named tools and grants the remainder, MCP included.
3. The deferred pool did not announce itself until ToolSearch was called. An agent that never
   calls ToolSearch would see only the nine up-front tools and could reasonably conclude it has
   no MCP access at all. **That is a discoverability gap, not an access gap** — worth separating
   in finding #292, because the remedy differs (a brief line vs. a definition change).
4. `select:` resolves against a server reported as *still connecting*. "Still connecting" is not
   evidence of absence.

BOUND: this measures the `Explore` type only, this session, this harness build. It says nothing
about any other agent type, and nothing about whether write-capable lore tools
(`lore_findings`, `lore_remember`, `lore_tasks`) succeed — I loaded neither and called neither,
because the brief scoped me to `lore_index` and `lore_comms register`.

## 7. What I did NOT do
No codebase exploration, no searches, no speculation about causes, no git mutation. Files
written: this report only.
