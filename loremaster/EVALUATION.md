# Evaluation suite (Phase 4)

`evaluation.xml` is the mcp-builder Phase-4 evaluation set for the **lore
(loremaster)** MCP server. Each `<qa_pair>` is independent, read-only, complex
(multi-tool exploration of this indexed repo), realistic, single-answer
verifiable, and stable (a fact about committed code/design, not a drifting count
or timestamp).

The questions are phrased as *tasks*, so the evaluation harness/model chooses the
tools. They do **not** depend on the exact tool names, so the suite is valid
whether the server ships the bare names (`search_code`, `get_symbol`, …) or the
`lore_`-prefixed v0.2.0 names.

## Prerequisites

- A live lore server indexing the lore monorepo itself (the `lore-lore`
  container). The reference endpoint is `http://127.0.0.1:9202/mcp`.
- The mcp-builder evaluation harness and its deps:
  ```sh
  pip install -r ~/.claude/skills/mcp-builder/scripts/requirements.txt
  export ANTHROPIC_API_KEY=...   # the harness drives a Claude agent
  ```

## Run

```sh
python ~/.claude/skills/mcp-builder/scripts/evaluation.py \
  -t http \
  -u http://127.0.0.1:9202/mcp \
  -o evaluation_report.md \
  loremaster/evaluation.xml
```

The harness connects over streamable HTTP, runs each question through a Claude
agent that may only use the server's tools, then string-compares the agent's
`<response>` to the ground-truth `<answer>`. The report summarises accuracy,
average tool calls per task, and the agent's per-task feedback on the tools.

## Re-verifying an answer by hand

Every answer here was derived by driving the live tools (not guessed). To
spot-check one, exercise the same tool chain a human would, e.g. confirming the
startup-gate exception class:

```sh
cd <this worktree> && uv run --frozen python - <<'PY'
import anyio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
async def main():
    async with streamablehttp_client("http://127.0.0.1:9202/mcp") as (rd, wr, _):
        async with ClientSession(rd, wr) as s:
            await s.initialize()
            r = await s.call_tool("get_symbol", {"qualified_name": "loremaster.server.ProbeGateError"})
            print(r.content[0].text)
anyio.run(main)
PY
```
