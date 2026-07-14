# 40 — UI foundation: /ui app + JSON endpoints + dashboards (formerly PKT-22)
size ~0.30 wu · wave G · depends: packet 35 (dashboards read deepened traces)
law: DESIGN-LAW §1 (humans see what agents see), §12 · spec: MASTER-PLAN §4 · DEPLOY: yes

## Mission
The mcp role serves `/ui` (same ASGI app, path-separated, stateless — replicas keep
working; Bearer/session auth per packet 39's posture). Foundation only: endpoints, search/
symbol views, findings queue, trace dashboards. Graph explorer + chat are packet 41.

## Scope IN
- loremaster/ui/: small SPA (one bundled page, no build-system sprawl) + JSON endpoints.
- **Search + symbol views** running the SAME store queries the tools use — citations,
  staleness flags, `(ai summary)` marks render identically to the tool surface.
- **Findings queue** (the friction/maintainer loop's landing page — kind/status
  filters, raise_issue button per packet 31).
- **Dashboards**: query volume, zero-hit queries, latency, index health, snapshot
  timeline (packet 35's aggregates are the data).
- Server-side input validation on every endpoint (house law — public surface).

## Scope OUT
- Graph viz, chat, diff overlays (packet 41). MCP-resources file tree (v1.2 evaluation,
  unscheduled).

## Entry check
packet 39's auth posture ruled (the UI inherits it); packet 35's aggregates live.

## Exit
Full gates + cold audit; deploy BOTH; smoke: /ui renders search results byte-honest
with the MCP render for the same query; findings queue round-trips an acknowledge;
INDEX row + Log.
