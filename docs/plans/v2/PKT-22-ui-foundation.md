# PKT-22 — UI foundation: /ui app + JSON endpoints + dashboards
size ~0.30 wu · wave G · depends: PKT-20 (dashboards read deepened traces)
law: DESIGN-LAW §1 (humans see what agents see), §12 · spec: MASTER-PLAN §4 · DEPLOY: yes

## Mission
The mcp role serves `/ui` (same ASGI app, path-separated, stateless — replicas keep
working; Bearer/session auth per PKT-21's posture). Foundation only: endpoints, search/
symbol views, findings queue, trace dashboards. Graph explorer + chat are PKT-23.

## Scope IN
- loremaster/ui/: small SPA (one bundled page, no build-system sprawl) + JSON endpoints.
- **Search + symbol views** running the SAME store queries the tools use — citations,
  staleness flags, `(ai summary)` marks render identically to the tool surface.
- **Findings queue** (the friction/maintainer loop's landing page — kind/status
  filters, raise_issue button per PKT-16).
- **Dashboards**: query volume, zero-hit queries, latency, index health, snapshot
  timeline (PKT-20's aggregates are the data).
- Server-side input validation on every endpoint (house law — public surface).

## Scope OUT
- Graph viz, chat, diff overlays (PKT-23). MCP-resources file tree (v1.2 evaluation,
  unscheduled).

## Entry check
PKT-21's auth posture ruled (the UI inherits it); PKT-20's aggregates live.

## Exit
Full gates + cold audit; deploy BOTH; smoke: /ui renders search results byte-honest
with the MCP render for the same query; findings queue round-trips an acknowledge;
INDEX row + Log.
