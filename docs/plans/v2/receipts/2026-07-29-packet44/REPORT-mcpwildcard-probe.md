# REPORT-mcpwildcard-probe

**VERDICT: C** — `mcp__*` did NOT work: I hold exactly `Read`, `Bash`, `ToolSearch` and ZERO
`mcp__*` tools, and I hold NO tool my definition did not grant — so the allowlist WAS honoured
(ruling out B) and the `mcp__*` entry simply granted nothing.

## Complete tool inventory (verbatim, exhaustive)

Tools defined up front, as callable functions:
1. `Read`
2. `Bash`

Tools not in the up-front function list but demonstrably present (I invoked it 4×):
3. `ToolSearch`

Deferred tools named in any `<system-reminder>` block: **NONE**. No system-reminder in this
session enumerated a single deferred tool name. The only MCP-adjacent system output was
(a) a connecting-servers notice naming five SERVERS — `claude-in-chrome`, `lore_lore`,
`mezmo`, `odoo-code`, `odoo-dev` — and (b) after they connected, their server-level
INSTRUCTIONS text. Server instructions arrived; **server TOOLS never did.** Named servers is
not named tools; nothing became selectable.

That is the whole inventory. Three tools.

## Exact ToolSearch output

Query 1 — the specified load line:
`ToolSearch "select:mcp__lore_lore__lore_comms,mcp__lore_lore__lore_findings"`
→ `No matching deferred tools found`

Query 2 — keyword, to force a wait on connecting servers:
`ToolSearch "lore findings comms memory search code"`
→ `No matching deferred tools found`  (servers connected here; instructions pushed, tools not)

Query 3 — the specified load line again, POST-connection:
`ToolSearch "select:mcp__lore_lore__lore_comms,mcp__lore_lore__lore_findings"`
→ `No matching deferred tools found`

Query 4 — broad keyword, post-connection:
`ToolSearch "query findings ledger for a project code RAG"`
→ `No matching deferred tools found`

No schemas returned, ever.

## MCP call result

Not reachable. Nothing loaded, so `lore_findings action=query limit=1` was never invocable.
There is no "loads but cannot be invoked" case here — the schema never existed.

## The control — ungranted tools (the load-bearing evidence)

- `Edit`  — **NO**, not present.
- `Write` — **NO**, not present. (This file was written via `Bash` heredoc, the only writer I have.)
- `Glob`  — **NO**, not present.
- `Grep`  — **NO**, not present.
- `Agent` / `Task*` — **NO**, not present.
- Also absent: `WebFetch`, `WebSearch`, `NotebookEdit`, `TodoWrite`, `KillShell`, `BashOutput`.
- One ambiguity, stated rather than smoothed: the system prompt instructs me to use `SendMessage`,
  but `SendMessage` is NOT in my function list and I did not attempt it. If it is silently present
  it is a harness-injected teammate primitive, not something my `tools:` line granted — I flag it
  as unresolved, not as evidence either way.

Absence of `Edit`/`Write`/`Glob`/`Grep`/`Agent` is confirmed: the allowlist was enforced, not
discarded. This is outcome C, not a fallback-to-everything false positive.

## Bottom line

`mcp__*` as an allowlist entry is not a pattern the harness expands. It was accepted without
error and granted nothing — same end state the four `ToolSearch`-only agents measured, reached
by a different route. My grant behaved as `Read`, `Bash`, `ToolSearch`.
