brief-base v9 read

# REPORT — probe-confound-leg3-1 (tool-inventory probe, leg 3 of the 2×2)

## SUMMARY BLOCK

- `brief-base v9 read`
- **VERDICT: DEFINITION.** The `mcp__odoo-code__*` tools are PRESENT and CALLABLE on **opus**
  under agent-type `odoo-consumer-scout`. The model is NOT the variable; the agent DEFINITION is.
- **Negative control PASSED** (result is NOT void): `Edit` `Write` `Glob` `Grep` `Agent`
  `ToolSearch` `SendMessage` are ALL absent. The grant did not fall back to everything.
- **Measured cell:** `--agent-type odoo-consumer-scout --model opus --effort xhigh`, CLI 2.1.220,
  agent PID 189337. Measured from `/proc/<ppid>/cmdline`, not assumed.
- state: done
- deviations: (1) `tr '\0' ' ' < /proc/self/cmdline` as literally briefed returns the `tr`
  process's own cmdline, not the agent's — I walked the PPID chain to the real agent process
  instead. (2) I added three probes the brief did not ask for (error-string taxonomy, own
  definition read, `tdd-contract` definition read) because they convert the verdict from
  inference into direct measurement. Both disclosed in §5/§6.
- `Packages considered: none — no mechanism specified` (this is a measurement probe; it
  specifies and builds no mechanism).
- decisions-needed: ONE, and it is load-bearing — see §7. My result does **not** cover whether
  `ToolSearch` can reach MCP tools absent from a definition's `tools:` list. I could not test it
  (I do not have `ToolSearch`). If #294's fix routes through `ToolSearch`, this probe does not
  validate it.
- receipts: §1 inventory · §2 positive controls (pasted verbatim) · §3 negative controls ·
  §4 error-string taxonomy (3 distinct classes) · §5 measured identity · §6 both definitions ·
  §7 bounds + the one untested question.

---

## 0. VERDICT, in full

**DEFINITION.** Flipping *model only* against probe 1 (sonnet → opus, agent-type held at
`odoo-consumer-scout`) leaves the outcome UNCHANGED: MCP tools present, callable, returning
byte-identical output to probe 1's. Flipping *agent-type only* against probe 2 (`tdd-contract`
→ `odoo-consumer-scout`, model held at opus) FLIPS the outcome: absent → present.

The agent-type is the variable that moves the result. The model is not.

Stronger than the presence/absence inference, and measured directly in §6: **my granted toolset
is EXACTLY my definition's `tools:` list — 9 of 9, no extras, no omissions.** That single fact
explains probe 1, probe 2 and probe 3 with no model term anywhere in the explanation.

---

## 1. TOOL INVENTORY — verbatim and exhaustive

### 1a. Up-front callable function schema (complete, 9 tools, in schema order)

```
1. Read
2. Bash
3. mcp__odoo-code__odoo_code_search
4. mcp__odoo-code__odoo_read_file
5. mcp__odoo-code__odoo_fields_get
6. mcp__odoo-code__odoo_list_modules
7. mcp__odoo-code__odoo_search_read
8. mcp__odoo-code__odoo_read
9. mcp__odoo-code__odoo_call_kw
```

That is the entire schema. Seven are `mcp__odoo-code__*`.

### 1b. Present but not listed in the schema

**NONE.** Every tool I successfully called appears in 1a. Every tool I attempted that is not in
1a returned an error (§3, §4).

### 1c. `<system-reminder>` blocks enumerating DEFERRED tools

**NONE APPEARED.** No `<system-reminder>` enumerating deferred tools was present at spawn or at
any point during this run. I state this as an observation about my received context, which is
the only thing I can observe.

### 1d. An observation the brief did not ask for, which I flag because it is a live confusion vector

My system prompt contains a **full section on Claude-in-Chrome browser automation**, instructing
me to load `mcp__claude-in-chrome__*` tools via `ToolSearch`. I have **neither** those tools
**nor** `ToolSearch` (§3, §4). The instructions are for capabilities I do not have.

Separately, a **`# MCP Server Instructions`** block was injected mid-run enumerating **four**
servers — `lore_lore`, `mezmo`, `odoo-code`, `odoo-dev` — of which I hold tools for **exactly
one** (`odoo-code`). I probed the other two reachable ones and both are absent (§4, class A).

So: **MCP server instruction injection is NOT filtered by the agent's tool grant.** An agent
reading its own context in good faith would conclude it has `lore_lore` memory/ledger tools and
an `odoo-dev` harness. It does not. This is exactly the brief-base §4 failure mode ("a
requirement that was simply unmeetable, silently") arriving through the *context* channel rather
than the brief. Raising it; not resolving it.

---

## 2. POSITIVE CONTROL — real calls, output pasted verbatim

### 2a. `mcp__odoo-code__odoo_list_modules(name="sale")`

Returned, verbatim:

```
{"result":"Found 1 modules:\n\n\n## community\n- sale (installed)"}
```

Rendered, that is `Found 1 modules:` / `## community` / `- sale (installed)`.

**Comparison to probe 1:** probe 1 reported exactly `Found 1 modules: ## community - sale
(installed)`. **Mine MATCHES.** No difference to report loudly. Same modules, same installed
flag, same count.

### 2b. `mcp__odoo-code__odoo_fields_get(model="sale.order.line", attributes=["string","type"])`

First 8 content lines, verbatim:

```
> User: Ean Price (ean@pricepaper.com) | TZ: America/New_York | Company: Price Paper | user_id: 39 | partner_id: 40 | Role: Salesperson | 2026-08-01 18:23 UTC

### sale.order.line -- 134 fields

| Label | Field | Type | Relation |
|-------|-------|------|----------|
| Last Modified on | __last_update | datetime |  |
| Accessory Products | accessory_product | html |  |
| Analytic lines | analytic_line_ids | one2many | account.analytic.line |
```

This is a **live** call: it resolved an authenticated Odoo user, a company, and a
wall-clock timestamp of `2026-08-01 18:23 UTC`, and returned 134 fields including obviously
custom ones (`class_margin`, `customer_contract_line_id`, `rebate_contract_id`). It is not a
cached or stubbed response.

**Both positive controls succeeded. The MCP transport works end-to-end from an opus agent.**

---

## 3. NEGATIVE CONTROL — every tool the brief named, with exact error strings

Each was genuinely invoked. All seven are **ABSENT**. My definition grants none of them, so the
grant did **not** fall back to everything, and **the result is NOT void.**

| Tool | Present? | Exact error string (complete, unedited) |
|---|---|---|
| `Edit` | ABSENT | `Error: No such tool available: Edit. Edit exists but is not enabled in this context. Use one of the available tools instead.` |
| `Write` | ABSENT | `Error: No such tool available: Write. Write exists but is not enabled in this context. Use one of the available tools instead.` |
| `Glob` | ABSENT | `Error: No such tool available: Glob. Glob is not available in this session — find files with \`find\` via the Bash tool instead.` |
| `Grep` | ABSENT | `Error: No such tool available: Grep. Grep is not available in this session — search file contents with \`grep\` via the Bash tool instead.` |
| `Agent` | ABSENT | `Error: No such tool available: Agent. Agent exists but is not enabled in this context. Use one of the available tools instead.` |
| `ToolSearch` | ABSENT | `Error: No such tool available: ToolSearch. ToolSearch exists but is not enabled in this context. Use one of the available tools instead.` |
| `SendMessage` | ABSENT | `Error: No such tool available: SendMessage. SendMessage exists but is not enabled in this context. Use one of the available tools instead.` |

Consequence worth stating plainly: I **cannot** send a message, spawn an agent, or write a file
by any means other than `Bash`. This report was written with a `Bash` heredoc, as the brief
anticipated.

---

## 4. ERROR-STRING TAXONOMY — THREE distinct classes, not two

The brief supplied a two-class diagnostic (bare = never enrolled; "exists but is not enabled" =
withheld by grant). **Measurement found three classes.** I report the third rather than folding
it into either existing bucket.

**Class A — BARE. No second sentence. Never enrolled.**
```
Error: No such tool available: mcp__lore_lore__lore_index
Error: No such tool available: mcp__odoo-dev__odoo_harness_status
Error: No such tool available: mcp__claude-in-chrome__tabs_context_mcp
```
All three probed MCP tools outside my grant return the bare form. **No `mcp__` tool produced a
"exists but is not enabled" string.**

**Class B — "exists but is not enabled in this context." Known built-in, withheld by grant.**
`Edit`, `Write`, `Agent`, `ToolSearch`, `SendMessage` (strings in §3).

**Class C — "is not available in this session — <use X via Bash> instead." Built-in, withheld,
WITH a substitution hint.**
`Glob`, `Grep` (strings in §3). Distinguished from class B by carrying a redirect to a `Bash`
equivalent.

**Why this matters for #294, and it is the sharpest thing in this report:** every MCP tool
outside my grant fell in **class A (bare / never enrolled)**, and no MCP tool anywhere produced
a class-B "withheld" string. Under the brief's own criterion, that means MCP tools absent from a
definition's `tools:` list are **not enrolled at all** for that agent — not "enrolled and then
withheld."

**A concrete check for the lead, which I could not run myself:** if probe 2 (`tdd-contract`)
recorded its exact error string for an `mcp__odoo-code__*` call, class A there confirms the
never-enrolled mechanism directly. If probe 2 got class B, my class-A/class-B split does not
generalise and the mechanism needs another look. I did not see probe 2's raw strings; I am
naming the check, not asserting its outcome.

---

## 5. MEASURED IDENTITY — which cell of the 2×2 I actually occupied

**Deviation, disclosed:** the briefed command `tr '\0' ' ' < /proc/self/cmdline` returns the
cmdline of the **`tr` process itself** (the redirect's `/proc/self` resolves in the forked child,
which then execs `tr`). It printed `tr \0`. That command cannot reveal an agent's identity from
inside a `Bash` tool call. I walked the PPID chain to the real agent process instead:

```
--- ancestor 1: PID 189337 ---
/home/ejprice/.local/share/claude/versions/2.1.220 --agent-id probe-confound-leg3-1@session-c9a2fd51 --agent-name probe-confound-leg3-1 --team-name session-c9a2fd51 --agent-color purple --parent-session-id c9a2fd51-9a84-4f9c-9e38-18ace265e196 --agent-type odoo-consumer-scout --permission-mode auto --effort xhigh --model opus
--- ancestor 2: PID 7947 ---  tmux
--- ancestor 3: PID 4286 ---  /usr/lib/systemd/systemd --user
--- ancestor 4: PID 1 ---     /sbin/init
```

The flags the brief asked for, verbatim:
- `--agent-type odoo-consumer-scout`
- `--model opus`

Also captured: `--effort xhigh`, `--permission-mode auto`, CLI version `2.1.220`, agent PID
`189337` (the `Bash` shell was PID 189652), session `c9a2fd51`.

**I occupied the intended cell.** Same definition as probe 1, opus like probe 2.

**Suggested replacement for the brief's line in future probes** (it works from inside `Bash`):
```bash
pid=$$; for i in 1 2 3 4 5; do ppid=$(ps -o ppid= -p $pid|tr -d ' '); [ -z "$ppid" ] && break; \
  tr '\0' ' ' < /proc/$ppid/cmdline; echo; pid=$ppid; done
```

---

## 6. THE DIRECT MEASUREMENT — I read both definitions rather than inferring

The brief said to measure rather than take its word. I extended that to the definitions
themselves, because it upgrades the verdict from *inference over three cells* to *a directly
observed mechanism*.

### 6a. My own definition — `~/.claude/agents/odoo-consumer-scout.md` (5474 bytes, mtime Jul 5 22:23)

```yaml
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

**My granted schema (§1a) equals this list EXACTLY — 9 for 9, no extras, no omissions.**

Two facts fall straight out:
1. **The definition's `tools:` list is honored VERBATIM, on opus.** Not widened, not narrowed.
2. **The definition's `model: sonnet` was OVERRIDDEN by the spawn's `--model opus`** — and the
   tool grant was unaffected by that override. The grant tracks the definition; the model tracks
   the spawn flag. They are independent, which is precisely the confound the lead wanted closed.

### 6b. Probe 2's definition — `~/.claude/agents/tdd-contract.md` (17738 bytes, mtime Jul 28 20:13)

```yaml
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

**`grep -c 'mcp__'` over the entire 17738-byte file returns `0`.** Not one `mcp__` token anywhere
in `tdd-contract.md` — frontmatter or body.

So probe 2's zero MCP tools is **fully explained by its definition**, with no model term
required. Three cells, one mechanism, no residual:

| cell | agent-type | model | MCP tools in definition | MCP tools observed |
|---|---|---|---|---|
| probe 1 | `odoo-consumer-scout` | sonnet | 7 | **PRESENT** |
| probe 2 | `tdd-contract` | opus-5 | **0** | **ABSENT** |
| **probe 3 (me)** | `odoo-consumer-scout` | **opus** | 7 | **PRESENT** (7/7 callable) |

The rule "**the grant is exactly the definition's `tools:` list**" predicts all three. A
model-linked effect is not needed to explain any of them, and §6a shows the grant matching the
definition character-for-character on opus.

---

## 7. BOUNDS, AND THE ONE AMBIGUITY I AM NOT RESOLVING

Stated as bounds, not disclaimers — each names a fact.

1. **⚠ THE DECISION-NEEDED ONE — `ToolSearch` is entirely untested by this probe.** `tdd-contract`
   is granted `ToolSearch` *specifically as the gateway to deferred MCP tools*, per its own
   comment citing lore finding #266. **I do not have `ToolSearch` and could not test whether it
   can enroll MCP tools absent from a definition's `tools:` list.** My verdict covers the
   **up-front schema only**. If #294's fix is "let `ToolSearch` reach them," this probe neither
   supports nor refutes it — and probe 2's ABSENT result becomes considerably more interesting,
   because probe 2 *had* the gateway and still reported zero. That gap wants its own leg.
2. **`--model opus` vs probe 2's "opus-5" — I observed the flag string `opus` and nothing more.**
   Whether that resolves to the same underlying model probe 2 ran on is not something I can see
   from my position. If they differ, my probe-3-vs-probe-2 comparison is not strictly
   single-variable. **The verdict survives either way**, because probe-3-vs-probe-1 (model
   sonnet→opus, definition held) is single-variable on its own and shows no model effect, and
   §6a's exact-match measurement is a direct observation of the mechanism rather than a
   comparison at all.
3. **The fourth cell — (`tdd-contract`, sonnet) — was not run.** Unnecessary for this verdict
   given §6b (`tdd-contract` names zero MCP tools, so no model could grant it any), but the 2×2
   is formally incomplete and I am not going to pretend otherwise.
4. **Single run, one host, CLI 2.1.220, 2026-08-01.** No repetition; I did not test whether the
   grant is stable across respawns.
5. **§1c is an observation about my received context**, which is the only channel I can inspect.
   "No deferred-tool `<system-reminder>` appeared" is not the same claim as "the harness emits
   none," and I am not making the second.

---

## 8. WHAT THE LEAD SHOULD DO WITH THIS

1. **The mechanism is settled for the up-front schema: #294 is a DEFINITION fix.** Agents get
   exactly their `tools:` list. Fixing a crippled agent means editing its frontmatter.
2. **Do not stop at the definitions — §1d is a second, independent defect.** MCP *server
   instructions* are injected for servers whose tools the agent does not hold (`lore_lore`,
   `mezmo`, `odoo-dev` for me), and my system prompt teaches a browser-automation workflow I
   cannot execute. Agents are being told they can do things they cannot, in the one channel
   brief-base §4 calls guaranteed-read. That will keep producing the silent-unmeetable-requirement
   failure regardless of how the `tools:` lists are fixed.
3. **Resolve §7.1 before finalising the fix.** If the intended remedy is `ToolSearch` rather than
   explicit `mcp__*` entries, spawn a fourth leg that HAS `ToolSearch` and have it try to load an
   `mcp__odoo-code__*` tool not in its definition. That is the only untested link in the chain.
4. **Cheap corroboration, if probe 2's raw output survives:** check whether its failed
   `mcp__odoo-code__*` call returned class A (bare) or class B ("exists but is not enabled").
   Class A confirms never-enrolled directly (§4).
5. **Fix the identity-probe recipe in future briefs** — the `/proc/self/cmdline` one-liner cannot
   work from inside a `Bash` tool call (§5 has a working replacement).
