# REPORT-probe-plain-allowlist-1

brief-base v9 read

## SUMMARY BLOCK

- **VERDICT: C-by-the-letter, but the letter mis-describes it — and finding #294's core
  prediction is CONFIRMED.** I hold **ZERO MCP tools**. ToolSearch is present and executes,
  but its searchable universe is **exactly my four granted tools** — there are no deferred
  tools of ANY kind, MCP or non-MCP. So the brief's B/C discriminator ("can it load non-MCP
  deferred tools?") returns *no* on both legs and cannot separate the two hypotheses.
- **A SHARPER INSTRUMENT REPLACED IT: the harness emits THREE DISTINCT error strings for
  absent tools, and the difference is the discriminator the brief wanted.** `mcp__*` names
  fail *bare* ("No such tool available: X" — nothing more), whereas `Edit`/`Agent`/`WebSearch`/
  `NotebookEdit`/`SendMessage` fail with "**X exists but is not enabled in this context**".
  The harness knows Edit is a real-but-disabled tool; it does not recognise
  `mcp__odoo-code__odoo_code_search` as a tool *at all*. That is grant-absence, not
  load-failure. See §4.
- state: **done**
- deviations: (1) `SendMessage` is ABSENT — I could not message the lead; report file is my
  only channel. (2) Two Bash commands were blocked by the auto-mode classifier; I did not work
  around either, and substituted an unauthenticated liveness check. (3) I wrote no tests, per brief.
- `Packages considered: none — no mechanism specified` (inventory probe; built no mechanism).
- decisions-needed: (1) `tdd-contract`'s allowlist names **Grep** and **Glob**, and I got
  NEITHER — so the definition is wrong about its own grant in two places beyond MCP. (2) The
  harness injected ~4 MCP servers' full instruction blocks into an agent holding zero MCP
  tools — teaching a contract I cannot execute. Both are operator calls.
- receipts: inventory §1 · verbatim ToolSearch responses §2 · positive control §3 · error
  taxonomy §4 · negative control §5 · server-liveness §6 · instruments §8.

Measured **2026-08-01T14:18:40-04:00**, at sha `fa12c11`, branch `feat/surreal-unification`,
Claude Code **2.1.220**, my PID **174231**. Agent definitions hashed in §7 so a later reader
can detect drift. All present-tense claims below are scoped to that instant.

---

## 0. Capability check (brief-base §4) — done first, as required

| demanded by my brief / prompt | what I actually have | what I did instead |
|---|---|---|
| Use `SendMessage` to talk to the team (my system prompt devotes a section to it) | **ABSENT** — "exists but is not enabled in this context" | Report file only. Lead must ground-truth the artifact, not expect a message. |
| Use `mcp__claude-in-chrome__*` (my system prompt devotes ~40 lines to browser automation) | **ABSENT**, all of them | Nothing — unusable instruction block. |
| Project CLAUDE.md: "lore-first for code-structure questions", `lore_findings` for friction | **ABSENT** — no `mcp__lore_lore__*` | Could not file this finding in lore. Lead must file it. |
| My own definition's `tools:` list promises `Grep` and `Glob` | **BOTH ABSENT** | Used `grep`/`find` via Bash. |

The last row is a genuine surprise the brief did not anticipate and is **not** an MCP issue —
see §5.2. Per brief-base §4 this is a defect in the agent definition or the harness, not a
failing of mine, and naming it is the point.

---

## 1. Complete tool inventory (exhaustive, verbatim)

### 1a. Tools declared up front as callable functions
The `<functions>` schema block visible to me at run start enumerated exactly **three**:

```
Read
Write
Bash
```

### 1b. Tools present but NOT in that declared list
**`ToolSearch`** — it is absent from the schema block above, yet it **executed successfully**
(§2). This is itself a datum: the up-front function list is *not* a complete inventory of
callable tools, so an agent that introspects only its schema block would under-report itself.

### 1c. Tools enumerated in any `<system-reminder>` as DEFERRED
**NONE. No system-reminder in this run enumerated a single deferred tool name.** The brief
called the presence-or-absence of such a block the key datum; it is **absent**.

Two system-reminders did arrive, and neither names a tool:

1. After my first `ToolSearch` call — names **servers**, not tools:

```
The following MCP servers are still connecting — their tools (typically named mcp__<server>__*)
are not yet available but will appear shortly:
claude-in-chrome
lore_lore
mezmo
odoo-code
odoo-dev

If the user's request might be served by one of these servers (even if they didn't name it
explicitly), call ToolSearch with a relevant keyword — ToolSearch will wait for connecting
servers and search their tools once available. Do not report a capability as unavailable
without first searching.
```

   ⚠ **"will appear shortly" did not happen.** I searched repeatedly over the following
   minutes (§2, §3) and no MCP tool ever appeared. The reminder also instructs *"Do not report
   a capability as unavailable without first searching"* — I complied, searched nine times,
   and am reporting unavailability on that evidence.

2. A `# MCP Server Instructions` block carrying **full usage instructions for `lore_lore`,
   `mezmo`, `odoo-code`, and `odoo-dev`** (two truncated by length). It taught me lore's
   tool ladder (`lore_map → lore_search → lore_get_symbol → lore_impact → lore_verify`),
   odoo-code's citation format and security boundaries, and odoo-dev's harness protocol —
   **for tools I cannot call.** This is a substantial, silent context tax on every agent in
   my class, and it actively misleads: an agent reading it would reasonably believe it holds
   these tools.

### 1d. The definitive grant set
Established independently in §3.2 by `ToolSearch`'s own `select:` behaviour, which loads a
name iff I hold it:

```
Read · Write · Bash · ToolSearch          ← exactly four; nothing else exists in my context
```

---

## 2. ToolSearch against CONNECTED servers — verbatim responses

Every response below is pasted exactly as returned.

| # | query | verbatim response |
|---|---|---|
| 1 | `select:mcp__odoo-code__odoo_code_search,mcp__odoo-code__odoo_list_modules` | `No matching deferred tools found` |
| 2 | `odoo code search modules` | `No matching deferred tools found` |
| 3 | `select:mcp__mezmo__list_log_fields` | `No matching deferred tools found` |

Brief step 3 ("if ToolSearch returns any schema, CALL the tool") is **vacuous** — no schema
was ever returned, so there was nothing to call. I nonetheless attempted the calls directly,
by name, rather than treating the absence as proof (§5.1). Proof by execution, as demanded.

---

## 3. POSITIVE CONTROL — is ToolSearch broken, or is my grant empty?

This was the brief's highest-value ask. The answer came in two parts, and the second part
is the one that matters.

### 3.1 Non-MCP deferred tools — also absent

| query | verbatim response |
|---|---|
| `select:WebFetch` | `No matching deferred tools found` |
| `select:TaskCreate` | `No matching deferred tools found` |
| `web fetch url contents` | `No matching deferred tools found` |
| `search code semantically in an indexed repository` | `No matching deferred tools found` |
| `read a file` | `No matching deferred tools found` |
| `mcp` | `No matching deferred tools found` |

`read a file` is the load-bearing one: it would match `Read` itself if `Read` were in the
deferred pool. It returns nothing. **The deferred pool is EMPTY, not filtered.**

By the brief's letters this reads as **C** — ToolSearch loads nothing. But C's parenthetical
("a broader breakage") is **wrong**, and I would have stopped at a false conclusion had I not
run the next probe.

### 3.2 The probe that actually discriminated — `select:` on tools I ALREADY hold

| query | verbatim response |
|---|---|
| `select:Read,Write,Bash,ToolSearch` | `[Tool references removed - tool search not enabled]` → then `Tool loaded.` |
| `select:Read` | `[Tool references removed - tool search not enabled]` → then `Tool loaded.` |
| `select:Bash,Write` | `[Tool references removed - tool search not enabled]` → then `Tool loaded.` |
| `select:Edit` | `No matching deferred tools found` |
| `select:Grep,Glob` | `No matching deferred tools found` |

Reproducible, three times, in both directions. **ToolSearch is NOT broken** — it resolves
every name I hold and reports `Tool loaded.`, and resolves nothing else. It also names the
mechanism itself: **`tool search not enabled`**.

**Therefore the two hypotheses separate cleanly after all:**
- *"ToolSearch is broken for me"* — **REFUTED.** It functions and succeeds on all four
  granted names.
- *"MCP tools are not in my grant"* — **SUPPORTED**, and corroborated independently by the
  error taxonomy in §4 and by the definition diff in §7.

The searchable universe is exactly the grant. There is no deferred layer in my context at
all, so nothing about MCP was ever *filtered out at load time* — it was **never present**.

---

## 4. THE ERROR TAXONOMY — three distinct strings, and why it is the best instrument here

Discovered by accident while running §5, and it turned out to be sharper than the B/C
discriminator the brief specified. The harness distinguishes three classes of absent tool:

| class | tools | verbatim error |
|---|---|---|
| **A** — disabled session-wide, with a workaround hint | `Grep`, `Glob` | `No such tool available: Grep. Grep is not available in this session — search file contents with `grep` via the Bash tool instead.` |
| **B** — known tool, withheld by grant | `Edit`, `Agent`, `WebSearch`, `NotebookEdit`, `SendMessage` | `No such tool available: Edit. Edit exists but is not enabled in this context. Use one of the available tools instead.` |
| **C** — name not recognised at all | every `mcp__*` | `No such tool available: mcp__odoo-code__odoo_code_search` *(bare — no second sentence)* |

**Why this is decisive.** Class B proves the harness maintains a notion of "this is a real
tool you were not granted" and says so explicitly. Every `mcp__*` name falls in class C
instead — the harness does not even place them in the known-but-withheld category. Combined
with §6 (the servers are *live* and their instructions reached my context), the only reading
consistent with all three observations is that **MCP tools were never enrolled into this
agent's tool set**, rather than being enrolled-then-denied or deferred-then-unloadable.

This taxonomy works even when the deferred pool is empty, which is exactly the condition that
defeated the brief's intended discriminator. I recommend it as the standing instrument for
this class of probe.

---

## 5. NEGATIVE CONTROL — was my allowlist enforced?

### 5.1 The four the brief named, plus every MCP call attempted

| tool | present? | verbatim error |
|---|---|---|
| `Edit` | **ABSENT** | `No such tool available: Edit. Edit exists but is not enabled in this context. Use one of the available tools instead.` |
| `Agent` | **ABSENT** | `No such tool available: Agent. Agent exists but is not enabled in this context. Use one of the available tools instead.` |
| `NotebookEdit` | **ABSENT** | `No such tool available: NotebookEdit. NotebookEdit exists but is not enabled in this context. Use one of the available tools instead.` |
| `WebSearch` | **ABSENT** | `No such tool available: WebSearch. WebSearch exists but is not enabled in this context. Use one of the available tools instead.` |
| `SendMessage` | **ABSENT** | `No such tool available: SendMessage. SendMessage exists but is not enabled in this context. Use one of the available tools instead.` |
| `mcp__odoo-code__odoo_code_search` | **ABSENT** | `No such tool available: mcp__odoo-code__odoo_code_search` |
| `mcp__odoo-code__odoo_list_modules` | **ABSENT** | `No such tool available: mcp__odoo-code__odoo_list_modules` |
| `mcp__mezmo__list_log_fields` | **ABSENT** | `No such tool available: mcp__mezmo__list_log_fields` |
| `mcp__claude-in-chrome__tabs_context_mcp` | **ABSENT** | `No such tool available: mcp__claude-in-chrome__tabs_context_mcp` |
| `mcp__lore_lore__lore_index` | **ABSENT** | `No such tool available: mcp__lore_lore__lore_index` |
| `mcp__lore_lore__lore_search` | **ABSENT** | `No such tool available: mcp__lore_lore__lore_search` |

**`Edit` — the sharpest test named by the brief — is ABSENT while `Write` works** (this file
was written with it). The allowlist **was enforced**. The result is **not void**; verdict D is
excluded.

### 5.2 An enforcement anomaly the brief did not predict — `Grep` and `Glob`

My definition grants six tools. I received **four**. `Grep` and `Glob` are in the allowlist and
are *not* available — but they fail with the **class A** string ("not available in this
session"), distinct from the class B grant-withholding string. So they appear to be disabled
session-wide or harness-wide, upstream of the allowlist, rather than denied to me specifically.

This matters for interpreting the whole experiment: **an allowlist entry does not guarantee the
tool**, so "it is in the `tools:` list" is not evidence of possession for any agent definition
in this repo. Only execution is. Flagging for the operator — it also means the comment in
`tdd-contract.md` justifying `ToolSearch` (citing finding #266) is only half-satisfied: the
tool is present, but it reaches nothing.

---

## 6. Server liveness — the absence is NOT connectivity

The brief warned that `lore_lore` was down at session start and that lore therefore proves
nothing. I tested `odoo-code` as instructed, and also re-checked lore.

```
-- odoo-code endpoint (no auth, liveness only):
HTTP 401 in 0.024215s
-- lore_lore endpoint (local, no auth):
HTTP 406 in 0.002177s
```

Both **responded** — 401 = up and demanding auth; 406 = up and demanding a different `Accept`
header. Neither is a refused connection or a timeout. Note lore is **up now**, whatever its
state at session start.

Corroborating, from the process table: `mcp-code` container running
`python -m code_mcp.server streamable-http` (PID 10711), plus multiple `odt-mcp` stdio
processes (odoo-dev). And most directly: **all four servers' instruction blocks were injected
into my context during this run** (§1c), which is first-party proof they completed connection
in *my* session.

**So: the servers are connected, their instructions reached me, and not one of their tools is
callable by me.** Connectivity is excluded as an explanation.

An authenticated `initialize` round-trip against odoo-code was **blocked by the auto-mode
classifier** (it required reading a bearer token out of `~/.claude.json`). I did not attempt
to work around it, per the denial's own instruction; the unauthenticated liveness check above
was substituted and is sufficient for the claim being made.

---

## 7. The controlled comparison — two probes, one variable

Both probes were spawned by the same parent, seconds apart, with identical flags except
`--agent-type` and `--model`. Full `argv` from `/proc/<pid>/cmdline`:

```
=== PID 173741 ===                    === PID 174231 ===
--agent-name  probe-literal-mcp-1     --agent-name  probe-plain-allowlist-1
--team-name   session-c9a2fd51        --team-name   session-c9a2fd51
--agent-type  odoo-consumer-scout     --agent-type  tdd-contract
--permission-mode auto                --permission-mode auto
--effort      xhigh                   --effort      xhigh
--model       sonnet                  --model       claude-opus-5
```

The definitions those types resolve to (frontmatter, verbatim):

```yaml
# ~/.claude/agents/tdd-contract.md          md5 aea9224fc27ed7f545fee85a2bd21699
name: tdd-contract
tools:
  - Read
  - Write
  - Bash
  # ToolSearch = the gateway to deferred MCP tools (lore_search / lore_findings / lore_comms).
  # Without it this agent cannot file the findings it produces, cannot reach project memory,
  # and cannot be reached mid-run. See lore finding #266.
  - ToolSearch
  - Grep
  - Glob
```

```yaml
# ~/.claude/agents/odoo-consumer-scout.md   md5 828b7a46c7eefe9c2ed6f8ec37d9afcf
name: odoo-consumer-scout
model: sonnet
tools:
  - Read
  - Bash
  - mcp__odoo-code__odoo_code_search
  - mcp__odoo-code__odoo_read_file
  - mcp__odoo-code__odoo_fields_get
  - mcp__odoo-code__odoo_list_modules
  - mcp__odoo-code__odoo_search_read
  - mcp__odoo-code__odoo_read
  - mcp__odoo-code__odoo_call_kw
```

My definition names **no MCP tool**; the sibling's names **seven**. That is the independent
variable. My leg returns **zero MCP tools**. Note the embedded comment in my own definition
asserts ToolSearch is *"the gateway to deferred MCP tools"* — **this run measures that claim
as FALSE**: ToolSearch is present, functional, and reaches no MCP tool whatsoever.

⚠ **Bound on this comparison, stated so it does not over-claim:** the two probes differ in
**two** variables, not one — `agent-type` *and* `model` (sonnet vs opus-5). I cannot exclude a
model-linked effect from my leg alone. Only the sibling's result can complete the inference,
and if the sibling reports MCP tools present, the residual model confound should be closed by
a third leg (`tdd-contract` on sonnet, or `odoo-consumer-scout` on opus-5) before the finding
is treated as settled.

---

## 8. Instruments (brief-base §1 — pasted verbatim, not lost to scratch)

No file was created other than this report. Every Bash-side claim above is regenerated by:

```bash
# (a) argv of every live agent process — proves agent-type / model / permission-mode
ps -eo pid,ppid,lstart,args | grep -F 'share/claude/versions' | grep -v grep
for p in <pids>; do echo "=== PID $p ==="; tr '\0' '\n' < /proc/$p/cmdline; echo; done

# (b) the allowlists actually on disk, with drift hashes
for f in ~/.claude/agents/tdd-contract.md ~/.claude/agents/odoo-consumer-scout.md; do
  echo "########## $f"; awk '/^---/{n++} n<2 || /^---/' "$f" | head -30; echo
done
md5sum ~/.claude/agents/tdd-contract.md ~/.claude/agents/odoo-consumer-scout.md

# (c) MCP server config (no secrets printed)
python3 -c "
import json
d=json.load(open('/home/ejprice/.claude.json'))
for k,v in d['mcpServers'].items(): print(k, v.get('type'), v.get('url') or v.get('command'))"

# (d) endpoint liveness WITHOUT credentials — a response code, any code, proves 'up'
curl -s -o /dev/null -w 'HTTP %{http_code} in %{time_total}s\n' --max-time 20 \
  https://mcp-dev.pricepaper.com/code/mcp -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"initialize"}'
curl -s -o /dev/null -w 'HTTP %{http_code} in %{time_total}s\n' --max-time 10 \
  http://127.0.0.1:9202/mcp -X POST -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"initialize"}'
```

The tool-side instrument is not a script — it is the probe sequence itself, and it is
reproducible from the tables in §2–§5: for each name, issue `ToolSearch select:<name>` and a
direct call, then classify the returned string against the §4 taxonomy.

---

## 9. Findings for the operator (I could not file these — no `lore_findings`)

1. **`tdd-contract` holds zero MCP tools** — finding #294 confirmed by execution, and by three
   independent lines of evidence (empty ToolSearch universe · class-C bare error shape · the
   definition diff). Every `tdd-contract` run to date that was required by project CLAUDE.md to
   "prefer the indexed code tool" was **structurally unable to comply, silently** — the exact
   shape brief-base §4 records as already having happened once.
2. **The `ToolSearch` comment in `tdd-contract.md` is false as written.** It claims ToolSearch
   is the gateway to `lore_search` / `lore_findings` / `lore_comms`. Measured: it reaches none
   of them. Adding `ToolSearch` did not fix #266; it produced the appearance of a fix. The
   remedy is naming the `mcp__lore_lore__*` tools in `tools:` explicitly, as
   `odoo-consumer-scout` does for odoo-code.
3. **An allowlist entry does not guarantee the tool** — `Grep` and `Glob` were granted and not
   delivered (§5.2), with a *different* error class implying a session-wide disablement above
   the allowlist. Any audit of agent capability that reads `tools:` lists rather than executing
   is unreliable. This is the "a fact that is written down and unread" hazard inverted: a fact
   written down and *false*.
4. **`SendMessage` is absent from `tdd-contract`** while the system prompt instructs its use at
   length. Agents in this class cannot answer the lead mid-run, cannot escalate a fork by
   message, and cannot register in a comms fleet. Report-file-only is the real contract.
5. **~4 MCP servers' full instruction blocks are injected into an agent holding zero MCP
   tools.** It is a recurring context tax and it teaches a capability contract the agent cannot
   execute — an agent that trusted it would report having searched lore when it had not.
6. **The "will appear shortly" system-reminder is misleading for allowlisted agents.** It
   asserts the MCP tools are merely *connecting*, and instructs the agent not to report a
   capability unavailable before searching. For an agent with no MCP grant this is
   unfalsifiable-looking waiting; only the §4 taxonomy resolves it.

---

## 10. Verdict, stated precisely

**Finding #294 is CONFIRMED: an agent definition with an explicit `tools:` allowlist containing
no MCP entry receives ZERO MCP tools, even from servers that are connected and healthy in the
same session.**

Against the brief's letters: **not A** (no MCP tool was reachable), **not D** (the allowlist was
enforced — `Edit` absent, `Write` present). Between B and C: the observation is **C by the
letter** — ToolSearch loaded no deferred tool of any kind — but C's parenthetical *"a broader
breakage"* is **false**, and B's premise (*"it CAN load non-MCP deferred tools"*) is
**untestable in my context**, because there is no deferred layer at all. Both letters were
written assuming a deferred pool exists to be filtered; mine is empty by construction.

The substantive answer the brief was reaching for — *"is ToolSearch broken for me, or are MCP
tools not in my grant?"* — is **not in my grant**, established by the §4 error taxonomy and the
§3.2 select-universe probe rather than by the intended discriminator.

**This leg is the CONTROL and it is clean.** Whatever the sibling `probe-literal-mcp-1` reports,
it has a measured zero to be compared against — subject to the two-variable bound in §7.
