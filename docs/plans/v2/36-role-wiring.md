# 36 — Role wiring: all | mcp | scout + per-role creds (formerly PKT-07)
size ~0.30 wu →split at kickoff · wave S (re-waved 2026-07-14; cloud-for-Odoo track) · depends: none within the wave
law: DESIGN-LAW §12 · spec: MASTER-PLAN §1 (two-role decomposition, server-mode-everywhere) · DEPLOY: yes (single-node stays live)

## Mission
Wire the client/server split the store schema was built for: `scout` (write side,
runs where the repo lives), `mcp` (read side, stateless, cloud-hostable), `all`
(single-node, today's ergonomics). SurrealConfig gains per-role credentials. The tool
surface is FINAL at whatever the exact-set registration pin says (15 since comms C1 — this
file's old "14" was stale; the PIN is the authority, not any doc) — roles do not reopen
schemas or renders.

## Scope IN
- Role selection (config + entrypoint): `python -m loremaster.scout` runs watcher/
  reconcile/chunk/graph/embed/snapshot/command-subscriber with no FastMCP import;
  `mcp` runs tools + query-side embedding + memory/trace writes; `all` = both.
- SurrealConfig per-role creds (env-indirected per house resolve_secret style).
- Command-channel round-trip in split mode (reconcile command row: MCP inserts, scout
  consumes via LIVE SELECT with poll fallback — machinery exists from P5; wire + pin).
- **Per-role lore-deploy verbs** (regained from packet 19's 2026-07-14 trim): light up the
  role arg packet 19 left defaulting to `all`.
- Degraded-honesty when the peer role is absent (mcp with a dead scout serves with
  honest staleness ages; never silent).
- **#206 (slotted 2026-07-26; SECURITY):** the hand-rolled bearer auth silently DISABLES
  the MCP SDK's session-owner binding — any valid key can resume any other key's session.
  Dormant today (single key, LAN); per-role creds make it LIVE, so it is fixed HERE, in the
  same wave that mints the second credential. Packet 39's threat model MUST cite the fix
  (39 is REQUIRED before any off-LAN exposure).
- **Memory writes are store-only in every role (RULED 2026-07-11, DESIGN-LAW §14):**
  no ledger side-write anywhere — packet 18 retires it. The memory write path fails loud
  on store failure; there is no silent durability fallback to wire.

## Scope OUT
- Containerfile/topology drills (packets 37/38); hosted auth beyond current Bearer (packet 39).

## Entry check
Suite green at HEAD; grep/lore for any role stub left by P5 (scout entrypoint shipped
then — this packet finishes the wiring, it does not rebuild the daemon).

## Exit
Full gates + cold audit; single-node redeploy BOTH stays live (the only deploy this
packet owes); role matrix pinned by tests (each role imports/serves only its own
surface); INDEX row + Log.
