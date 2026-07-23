---
name: lore-deploy
description: >-
  Deploy, start, stop, and check the per-project "lore" RAG MCP server (the
  loremaster container backed by the shared SurrealDB store + the self-hosted
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
containers** — one per project, each keyed to its own per-slug database in the
shared SurrealDB store (the always-on `lore-surreal` container). This skill
manages that container's lifecycle for one project.

The lifecycle is **on-demand, not always-on** (plan A1.11/D12): lore runs only
while ≥1 Claude is working the project and is stopped otherwise, so no idle
container holds the embedder pool. The expensive cold index is paid **once** at
`setup`; thereafter the SurrealDB store's data and the SQLite manifest **persist
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
| `setup` | Once per project. Scaffold `lore.yaml`, verify env keys, **hard-probe `/embed`**, **pre-flight the SurrealDB store's `/health`**, build the image if missing, **cold-index**, merge `.mcp.json`. Re-running detects the existing config + manifest and **no-ops** (never re-scaffolds, never nukes the index). |
| `start` | Launch the container (delta-reconcile runs on startup) + merge `.mcp.json`, then **waits for the MCP port to actually accept connections** before declaring success — a "running" container can still be mid-boot delta-reconcile with the port unbound (see "Port-probe / wait-for-bind" below). Already-running-and-bound ⇒ fast no-op. |
| `stop` | Stop + remove the container. Collections + manifest **persist**. Not-running ⇒ no-op. |
| `status` | Report running/stopped + `index_status()` freshness (in-flight/failed files), AND **probes the live MCP port** to report `ACCEPTING`/`NOT ACCEPTING` — container state alone does not prove the server is reachable. For a stopped container it reads the manifest directly and skips the probe. |
| `conform` | **Post-build, NOT on `start`.** Runs the **baked** pytest inside the deployed image against this repo mounted `:ro`, gated by a provenance guard that asserts the members import the BAKED artifact, not the mount — the instrument for #139 (*the test env is a fiction*: a suite green on the dev host proves the source, never the deployed artifact). Takes **no `--project`** (it gates the IMAGE); `--image` overrides `localhost/lore:latest`. Run it after `podman build`, before deploying (~3 min). |

Read `references/lifecycle.md` for the precise step sequence, the persistence
guarantees, and the failure/STOP conditions of each verb. Read
`references/server-interface.md` for the live server contract (entrypoint,
healthcheck, manifest/state layout, `.mcp.json` shape).

## Port-probe / wait-for-bind — "running" ≠ "accepting connections"

**A running container is not proof the MCP endpoint is reachable.**
loremaster's ASGI lifespan startup runs a boot-time delta-reconcile
(re-indexing changed files, subject to embedder 429 backoff) **before**
uvicorn binds the port. An incident on 2026-07-03 saw a "running" container,
a `status` that reported healthy, and an operator's MCP client refused for
~4 minutes — because neither verb ever probed the live port.

Both `status` and `start` now POST a minimal MCP `initialize` JSON-RPC request
to the configured `server:` host/port/path. Any HTTP response — even a
non-2xx one — counts as **ACCEPTING** (the port is bound and serving); a
connection-refused or timeout counts as **NOT ACCEPTING**.

- `status` (running container only): probes once (~3s timeout) and prints
  `status: mcp endpoint http://host:port/path = ACCEPTING` or
  `= NOT ACCEPTING (... likely boot delta-reconcile ...)`. A stopped
  container skips the probe entirely.
- `start`: every path that ends with a running container — fresh launch,
  stale-image recreate, **and** the already-running no-op path — polls the
  probe (every ~3s) until it accepts or a budget elapses (default 600s,
  `--bind-timeout <seconds>` to override, `--no-wait` to skip waiting
  entirely). It prints a progress line every ~30s while waiting. On timeout
  it exits non-zero with the tail of `podman logs`. The already-running path
  probes first and only enters the wait loop if not yet accepting, so the
  common case (already running and already bound) stays a fast no-op.

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

## Project memory lives in lore — `MEMORY.md` is only a bootstrap

lore is a RAG whose whole purpose is preserving context, so a project's **durable
memory belongs in lore** — the SurrealDB `memory` table, written with `lore_remember`
and recalled with `lore_recall` — **not** accumulated in the flat `MEMORY.md` that the
Claude Code harness auto-loads into every session. That flat file does not scale: it is
loaded *in full* every session, so it has a hard size ceiling, and past it you pay
context for memory you may never touch. Storing project memory there is the exact
anti-pattern lore exists to kill — and a dogfood miss for any project on lore.

So `MEMORY.md` must be a **thin bootstrap**: a one-paragraph pointer plus a handful of
second-zero operational landmines. Everything else is recalled on demand.

**This is a lifecycle responsibility, not just documentation.** When you run this skill
for a project: once lore is up, locate the native memory dir, and **if `MEMORY.md` is a
legacy flat store, migrate it** into lore and slim it to the bootstrap.

### Where the native memory lives

The harness keeps a project's auto-memory at `~/.claude/projects/<ENC>/memory/`, where
`<ENC>` is the project's **absolute** path with **every non-alphanumeric character
replaced by `-`** (per character — no collapsing of runs, no lowercasing). Examples:

- `/home/ejprice/PycharmProjects/lore` → `-home-ejprice-PycharmProjects-lore`
- `/home/u/.config/x_y` → `-home-u--config-x-y` (`.` and `_` both become `-`)

**Derive this path, then assert the directory exists before trusting it.** If it does
not, do **not** conclude "no memory" — the derivation can be wrong for an edge-case path.
STOP and find the real dir (`ls ~/.claude/projects/ | grep <project-basename>`), or have
the operator name it. A wrong derivation silently migrates nothing.

The dir holds `MEMORY.md` (the auto-loaded index/store) plus one `<slug>.md` topic file
per memory — each with YAML frontmatter (`name` / `description` / `metadata.type`) and a
body.

### Detecting a legacy flat `MEMORY.md`

`MEMORY.md` is already a thin bootstrap **iff** it carries the marker
`<!-- LORE-MEMORY-BOOTSTRAP -->` near the top. Absent that marker (and with topic files
or index entries present), it is **legacy/flat** and must be migrated. The marker makes
the whole protocol **idempotent** — a re-run on a bootstrapped file is a no-op.

### The migration protocol (run once lore is up)

Migration **writes to lore, so lore must be running** (after `start`). On `setup` (lore
not yet up) do only the file side: write the thin bootstrap if `MEMORY.md` is absent; if
it is legacy, say so loudly and defer the migration to after `start`.

**Memory loss is unrecoverable — follow every step, skip none:**

1. **Back up first.** `cp -a <memdir> <memdir>.bak-<UTC-stamp>` before touching
   anything. Nothing below ever deletes this backup.
2. **Build the worklist** — the **union** of (a) every `*.md` topic file except
   `MEMORY.md`, and (b) every entry line in `MEMORY.md`. Reconcile the two: a topic file
   with no index entry is *still a memory* (migrate it); an index entry with no file is a
   one-line memory (migrate its text). This union is your completeness checklist — a file
   referenced twice, or not at all, is exactly why you enumerate **both** sides.
3. **Migrate each item** into lore:
   - Read the topic file and carry its body **verbatim** — a memory records what was true
     when written; do **not** summarise, "improve", or invent.
   - **Dedup:** `lore_recall(query=<the item's title/description>, k=5)`. If an existing
     memory (one *without* an `origin=claude_native_memory` label) already states the same
     fact, record it as "covered by `<id>`" and **skip the write**. When in doubt, **write**
     — a redundant memory is cheap; a dropped fact violates no-loss.
   - **Write:** `lore_remember(text=<verbatim body>, kind=<mapped>, trust=<mapped>,
     labels=["origin=claude_native_memory", "source_file=<name>", "harness_type=<type>"])`.
     Map the frontmatter `type` to a lore `kind`: `reference`→`fact` (`trust=authoritative`)
     · `feedback`→`decision` · `project`→`fact` · `user`→`fact` · anything else→`fact`.
     **Never `ongoing`** — it carries a 7-day TTL and would silently **expire** the
     migrated memory. The labels preserve the original type and make every migrated memory
     traceable back to its source file.
   - **Verify:** `lore_recall` the fact you just wrote and confirm it comes back.
4. **Account for every item.** Each worklist item is now either *written-and-verified* or
   *covered-by-existing*. No item unaccounted — this is the no-loss gate. Cross-check the
   count against step 2.
5. **Rewrite `MEMORY.md` as the bootstrap** (template below): the marker, the pointer
   directive, and a **small curated set** of second-zero operational landmines — the facts
   an agent needs before it can even work safely, **not** a table of contents. Everything
   else now recalls from lore.
6. **Archive, don't delete, the topic files** — move them into
   `<memdir>/archived-<stamp>/`, only after step 4 passes. The step-1 backup stays
   regardless. (Archiving over deletion mirrors this repo's report-archival law: an
   address that resolves beats a clean tree.)

### The bootstrap `MEMORY.md` template

```markdown
# Project Memory — <project>

<!-- LORE-MEMORY-BOOTSTRAP -->

**Durable project memory lives in LORE, not in this file.** Call
`lore_recall("<topic>")` to retrieve it; write new durable facts with `lore_remember(...)`.
Do NOT accumulate memory here — this file is auto-loaded into every session, so it must
stay small. It holds only this pointer plus the second-zero landmines below.

## Operational landmines (know these before you touch anything)
- <curated fact 1>
- <curated fact 2>
```

Curate the landmines **per project**: the pointer, plus the few facts that cause damage
or wasted effort if unknown at second zero — store/port topology, "do not run X",
forward-only migrations, where the plan of record lives. Keep it under a page.

### Writing memory going forward

Once bootstrapped, **do not add facts back into `MEMORY.md`.** Write durable project
memory with `lore_remember`; recall it with `lore_recall`. The bootstrap's own directive
says this — honor it, and so should every other agent on the project (the project's
`CLAUDE.md` should carry the same instruction so it is not lost when this skill is not in
context).

## Hard rules (why they matter)

- **Secrets are env-refs only.** `lore.yaml` carries the *name* of an
  environment variable (`api_key_env: LORE_TEI_KEY`), never the key itself. The
  container receives secrets via `--env-file`. Never inline a bearer token.
- **STOP if the SurrealDB store is unreachable.** `setup`/`start` pre-flight the
  unified store's `/health` (a plain HTTP GET derived from `surreal.url`) and
  **stop with a remediation message** if it does not answer — fail loud at
  `setup`/`start`, not later as an opaque error. The one mutation the skill may
  make is **start-if-stopped reboot recovery** (`podman start lore-surreal` when
  the container exists but sits Exited after a host reboot); it **never creates,
  recreates, or removes** that container or touches its data dir. **Schema +
  embedding-dimension ownership lives in the server, not here** — the loremaster
  server provisions the SurrealDB schema (threading `config.dim` into every
  index) and reconciles any dim/schema change via its embedding-schema-fingerprint
  rebuild. The deploy no longer gates on dim or recreates any store object.
- **STOP if `/embed` is unreachable or returns the wrong dimension.** A RAG
  server with no embedder is useless; fail loud at `setup`/`start`, not later as
  an opaque error.
- **The store + manifest persist across `stop`/`start`.** `stop` removes only
  the lore container. The `~/.local/state/lore/<slug>.db` manifest and the
  SurrealDB store's data (the separate, always-on `lore-surreal` container)
  survive, which is what makes restart a cheap delta-reconcile.

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

- `scripts/lore_deploy.py` — the verb dispatcher (the entrypoint above). Also
  where the MCP port-probe / wait-for-bind logic lives (`_probe_mcp_port` /
  `_wait_for_bind`, stdlib-only) **and** the SurrealDB store `/health` pre-flight
  (`_probe_surreal`, stdlib-only) — both inline rather than sibling scripts
  because the verbs that need them (`status`/`start`, `setup`/`start`) do not
  shell out for them.
- `scripts/probe_embed.py` — hard-probe the `/embed` endpoint; prints the
  observed dimension or exits non-zero (unreachable / wrong dim / 5xx).
- `scripts/merge_mcp_json.py` — idempotently merge the project's `.mcp.json`
  `mcpServers.lore_<slug>` entry (preserves every other server + key).
- `scripts/conformance_run.sh` — the `conform` verb's bash harness: runs the baked
  pytest inside the deployed image against this repo `:ro`, provenance-gated (#139).
- `scripts/conformance_provenance.py` — the provenance guard: asserts every workspace
  member imports the BAKED artifact, not the `:ro` `/workspace` mount (the inverse of
  `scripts/scratch_provenance.py`).

All scripts are stdlib + the loremaster venv only; they print nothing on
success beyond the structured status line and exit non-zero (loud) on failure.
