# PKT-07 — Role wiring: all | mcp | scout + per-role creds
size ~0.30 wu · wave D · depends: none within the wave
law: DESIGN-LAW §12 · spec: MASTER-PLAN §1 (two-role decomposition, server-mode-everywhere) · DEPLOY: yes (single-node stays live)

## Mission
Wire the client/server split the store schema was built for: `scout` (write side,
runs where the repo lives), `mcp` (read side, stateless, cloud-hostable), `all`
(single-node, today's ergonomics). SurrealConfig gains per-role credentials. The
14-tool surface is FINAL — roles do not reopen schemas or renders.

## Scope IN
- Role selection (config + entrypoint): `python -m loremaster.scout` runs watcher/
  reconcile/chunk/graph/embed/snapshot/command-subscriber with no FastMCP import;
  `mcp` runs tools + query-side embedding + memory/trace writes; `all` = both.
- SurrealConfig per-role creds (env-indirected per house resolve_secret style).
- Command-channel round-trip in split mode (reconcile command row: MCP inserts, scout
  consumes via LIVE SELECT with poll fallback — machinery exists from P5; wire + pin).
- Degraded-honesty when the peer role is absent (mcp with a dead scout serves with
  honest staleness ages; never silent).
- **Memory writes are store-only in every role (RULED 2026-07-11, DESIGN-LAW §14):**
  no ledger side-write anywhere — PKT-24 retires it. The memory write path fails loud
  on store failure; there is no silent durability fallback to wire.

## Scope OUT
- Containerfile/topology drills (PKT-08/10); hosted auth beyond current Bearer (PKT-21).

## Entry check
Suite green at HEAD; grep/lore for any role stub left by P5 (scout entrypoint shipped
then — this packet finishes the wiring, it does not rebuild the daemon).

## Exit
Full gates + cold audit; single-node redeploy BOTH stays live (the only deploy this
packet owes); role matrix pinned by tests (each role imports/serves only its own
surface); INDEX row + Log.
