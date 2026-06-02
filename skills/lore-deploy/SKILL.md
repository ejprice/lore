---
name: lore-deploy
description: >-
  Deploy, start, stop, and check the per-project "lore" RAG MCP server (the
  loremaster container backed by the shared Qdrant pod + the self-hosted
  voyage-4-nano embedder). Use this whenever the user wants to set up lore for a
  project, spin lore up or down for a coding session, check whether lore is
  running / how fresh its index is, or wire a project's .mcp.json to its lore
  server. Trigger on phrases like "set up lore for <project>", "start lore",
  "stop lore", "is lore running", "lore status", "deploy the lore MCP",
  "index this project for lore", "turn on the code RAG for this repo", or any
  request to manage the lore/loremaster container lifecycle for a project. The
  lifecycle is ON-DEMAND and every verb is idempotent: lore runs only while a
  Claude session is actively working a project and is safe to start/stop
  repeatedly without rebuilding the index.
---

# lore-deploy — on-demand lifecycle for a project's lore RAG MCP

## What this is

`lore` (the `loremaster` MCP server) gives Claude Code a per-project semantic
index of code + docs, kept fresh by a live file watcher, plus a project memory
store. One **shared image** (`localhost/lore:latest`) runs as **N config-driven
containers** — one per project, each keyed to its own Qdrant collection. This
skill manages that container's lifecycle for one project.

The lifecycle is **on-demand, not always-on** (plan A1.11/D12): lore runs only
while ≥1 Claude is working the project and is stopped otherwise, so no idle
container holds the embedder pool. The expensive cold index is paid **once** at
`setup`; thereafter the Qdrant collections and the SQLite manifest **persist
across stop/start**, so a restart is a cheap delta-reconcile (re-index only what
changed since last run), never a cold rebuild.

**Every verb is idempotent and safe to re-run.** That is the whole contract:
running `setup` twice is a no-op; `start` on an already-running container is a
no-op; `stop` on a stopped container is a no-op.

## The four verbs

Drive everything through the dispatcher script — it encodes the idempotency
checks so you do not have to re-derive them:

```
python3 ~/.claude/skills/lore-deploy/scripts/lore_deploy.py <verb> --project <abs-project-dir> [options]
```

| Verb | What it does (idempotent) |
|---|---|
| `setup` | Once per project. Scaffold `lore.yaml`, verify env keys, **hard-probe `/embed`**, ensure both Qdrant collections, build the image if missing, **cold-index**, merge `.mcp.json`. Re-running detects the existing config + collection + manifest and **no-ops** (never re-scaffolds, never nukes the index). |
| `start` | Launch the container (delta-reconcile runs on startup) + merge `.mcp.json`. Already-running ⇒ no-op. |
| `stop` | Stop + remove the container. Collections + manifest **persist**. Not-running ⇒ no-op. |
| `status` | Report running/stopped + `index_status()` freshness (in-flight/failed files). For a stopped container it reads the manifest directly. |

Read `references/lifecycle.md` for the precise step sequence, the persistence
guarantees, and the failure/STOP conditions of each verb. Read
`references/server-interface.md` for the live server contract (entrypoint,
healthcheck, manifest/state layout, `.mcp.json` shape).

## Activating it in-session (read this — the #1 onboarding gotcha)

`start`/`setup` write the `lore_<slug>` server into the project's **`.mcp.json`**,
which Claude Code reads **at session start**. So a freshly-deployed lore does **not**
appear in `/mcp` in the current session — **reload the session to activate it**
(`claude --continue`, or restart Claude Code in the project), then approve the new
server. This is standard project-scoped-MCP behavior, not a lore quirk — but it's
the thing that confuses first-time operators, so tell the user explicitly after a
`setup`/`start`: *"lore is deployed; reload the session (claude --continue) to use
its tools."*

## Tools may load "deferred"

With several MCP servers connected, Claude Code can present a server's tools as
**deferred** — an agent must `ToolSearch` for `mcp__lore_<slug>__*` (or the tool by
name) to load the schemas before the first call. This is Claude Code's many-tools
behavior, not lore's; just budget for one `ToolSearch` before the first lore call in
a fresh agent.

## When to run which verb

- **First time on a project, or user says "set up lore for X":** `setup`.
- **Opening a session / "start lore" / "turn on the code RAG":** `start`.
- **Done for now / "stop lore" / no session remaining:** `stop`.
- **"Is lore running?" / "how fresh is the index?":** `status`.

`setup` is safe to run when unsure — it detects an existing deployment and
no-ops the expensive parts, so it doubles as a "make sure everything is wired"
check.

## Hard rules (why they matter)

- **Secrets are env-refs only.** `lore.yaml` carries the *name* of an
  environment variable (`api_key_env: LORE_TEI_KEY`), never the key itself. The
  container receives secrets via `--env-file`. Never inline a bearer token.
- **STOP on a dim mismatch — never auto-recreate.** If the live `/embed` probe
  dimension, `config.dim`, and an existing collection's vector size disagree,
  the deploy **stops with a remediation message**. Auto-recreating a collection
  silently nukes a real index — the one thing this skill must never do. The
  `ensure_collections.py` helper enforces this.
- **STOP if `/embed` is unreachable or returns the wrong dimension.** A RAG
  server with no embedder is useless; fail loud at `setup`/`start`, not later as
  an opaque error.
- **Collections + manifest persist across `stop`/`start`.** `stop` removes only
  the container. The `~/.local/state/lore/<slug>.db` manifest and the
  `lore_<slug>` / `lore_<slug>_memory` collections survive, which is what makes
  restart a cheap delta-reconcile.

## Deferred (do not attempt here)

The **cloud / OAuth path is deferred** (plan A1.12). This skill deploys the
**local, no-auth, localhost-single-user** server only. A multi-developer cloud
deployment (rotatable Bearer keys behind a TLS-terminating ingress, or the
OAuth 2.1 + Dynamic Client Registration verifier the Claude.ai web app needs) is
a separate future build. By default `start` writes a **headerless** `.mcp.json`
entry (the local server runs no-auth; an unresolved `Bearer ${...}` would only
mislead). To opt into Bearer auth later, regenerate the entry with
`merge_mcp_json.py … --auth-key-env LORE_<SLUG>_KEY` and enable `auth` in `lore.yaml`.

## How the tools work — read it FROM THE SERVER, not here

This skill is the OPERATOR's guide (deploy lifecycle). It deliberately does **not**
document how a consumer uses lore's tools — that guidance is now delivered **in-band by
the server itself**. The FastMCP server advertises a substantial `instructions` block
plus a behavioral description + per-parameter schema on every tool, covering: when to
use which of the ten tools, the `[SOURCE:file:line]` + stable `Key:` citation
convention, the freshness / read-your-writes model (live inotify watch ~seconds;
periodic reconcile ~10 min backstop; `search_code(..., wait_for_fresh=True)` for the
edit-then-query race; `reindex(tier=...)` to force a whole tier), and the
project-memory stance. A connecting agent gets all of that automatically — there is
nothing to relay from this skill.

Operator-relevant freshness note only: a `status` run surfaces `index_status()`
(indexed / in-flight / failed counts) so you can confirm a deploy's index is current
and healthy. Everything else about querying belongs to the consumer and lives in the
server's own `instructions`.

## Helper scripts

- `scripts/lore_deploy.py` — the verb dispatcher (the entrypoint above).
- `scripts/probe_embed.py` — hard-probe the `/embed` endpoint; prints the
  observed dimension or exits non-zero (unreachable / wrong dim / 5xx).
- `scripts/ensure_collections.py` — ensure both collections exist at the right
  dim/cosine with payload indexes, reusing the in-repo `QdrantStore`; **exits
  non-zero on a dim mismatch without recreating** anything.
- `scripts/merge_mcp_json.py` — idempotently merge the project's `.mcp.json`
  `mcpServers.lore_<slug>` entry (preserves every other server + key).

All scripts are stdlib + the loremaster venv only; they print nothing on
success beyond the structured status line and exit non-zero (loud) on failure.
