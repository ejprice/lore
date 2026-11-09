# memlen query set — FIXED 2026-11-09 before any recall result was observed

Written after reading the two subject texts (necessary to target one fact per point) and
before running any lore_recall or offline scoring. Phrased as an agent would ask, avoiding
the note's distinctive words where an agent would not know them.

## Subject A — 6d16f7f4-9a98-51d4-b4b9-bdb8824fd96e (agent `tools:` grant semantics, 3,025 chars)

| id | target point | query |
|---|---|---|
| A1 | (1) three definition shapes | If my subagent's definition lists only specific tools, can it still use ToolSearch to load MCP tools? |
| A2 | (2) literal fully-qualified names grant | If I write the full mcp__server__toolname names into an agent's frontmatter, does the agent get those tools, and are they callable immediately or deferred? |
| A3 | (3) bare `mcp__*` wildcard | Does putting a wildcard like mcp__* in an agent's tools list give it access to MCP servers? |
| A4 | (4) listed ≠ possessed | My agent definition lists Grep and Glob but the agent doesn't have them — why? |
| A5 | (5) failed-call taxonomy | How do I tell from the error message why a tool call says the tool is not available? |
| A6 | (6) fresh MCP binding at spawn | If the lead session connected while an MCP server was down, can a subagent spawned later still reach that server? |
| A7 | FIX paragraph (extra, not a numbered point) | Which of our agent definitions deliberately leave out the tools key, and why? |

## Subject B — d53e4404-74f5-58e7-af2b-b2a386292cb5 (lore-lore deploy, 2,147 chars)

| id | target point | query |
|---|---|---|
| B1 | (1) deploy = manual recreate, not lore-deploy | How do I redeploy the lore container that indexes this repo after changing loremaster code — can I just use the deploy skill? |
| B2 | (2) wedged conmon restart | podman shows the container as Up but exec says it is not running — how do I get it started again? |
| B3 | (3) PidsLimit ceiling | What resource limit could make the lore server container shut itself down? |
| B4 | (4) no restart policy | Will the lore-lore server come back on its own if it stops or the machine reboots? |
| B5 | (5) Claude-side MCP reconnect | How do I get my Claude session to reconnect to the lore MCP server without restarting Claude? |

## Distractors — should hit NEITHER subject

| id | query |
|---|---|
| D1 | Which numpy percentile method gives nearest-rank results? |
| D2 | What happens when DEFINE FIELD IF NOT EXISTS runs against a field that already exists? |
| D3 | How many pytest-xdist workers may a targeted test run use on this box? |

## Scoring rules (fixed now)

- LONG arm: the subject's rank (1-based) and served score in a k=10 recall; absent = "miss (>10)".
- ATOMIC arm: (a) rank/score of the BEST-ranked piece of that subject; (b) rank of the TARGET piece
  (the piece holding the asked-about point). A7 targets the FIX piece.
- hit@1 / hit@3: the subject (LONG) or any piece of it (ATOMIC-best) / the target piece (ATOMIC-target)
  at rank ≤1 / ≤3. Distractors: report the subject's rank if it appears at all.
