# 41 — UI graph explorer + Agent-SDK chat (MASTER-PLAN §8.8 closes here) (formerly PKT-23)
size ~0.35 wu · wave G, LAST · depends: packet 39, packet 40
law: DESIGN-LAW §2 (map semantics govern what the explorer shows), §12 · spec: MASTER-PLAN §4 · DEPLOY: yes

## Mission
The remaining UI: dependency/impact graph visualization and the dogfooding chat.

## Scope IN
- **Graph explorer** over code_node+refs: module collapse, reverse-edge focus,
  dead-code and diff_status overlays, snapshot slider. Rendering via a lightweight
  vendored lib (cytoscape.js candidate — verify the vendoring against the
  no-build-sprawl rule before committing to it).
- **Chat**: Claude Agent SDK session server-side, wired to THIS project's own lore MCP
  (the exact tool surface agents get; ANTHROPIC_API_KEY on the mcp host; model per
  config). Auth per packet 39's posture — chat is an outward-facing surface.
- **§8.8 UI smoke** (the last unclosed MASTER-PLAN §8 item): graph renders the real
  project; chat answers a repo question using lore tools end-to-end; dashboards show
  live traces.

## Scope OUT
- Vector-side enrichment embedding (evaluated at this phase per plan; separate ruling).
- Any new MCP tool for the UI's benefit.

## Entry check
packet 40's endpoints live; packet 39 posture allows the chat exposure planned.

## Exit
Full gates + cold audit; deploy BOTH; §8.8 receipts committed; INDEX row + Log.
**The MASTER-PLAN's phase ladder is complete here.**
