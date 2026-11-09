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
`setup`; thereafter the SurrealDB store's data (the index, its manifest and code
graph) and the host state dir `~/.local/state/lore/` (setup's `<slug>.db` ledger,
the server's `<slug>.memory.db`) **persist across stop/start**, so a restart is a
cheap delta-reconcile (re-index only what changed since last run), never a cold
rebuild.

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
| `setup` | Once per project. Scaffold `lore.yaml`, verify env keys, **hard-probe `/embed`**, **pre-flight the SurrealDB store's `/health`**, build the image if missing, **cold-index**, merge `.mcp.json`. Only a cold index that exits 0 writes the provisioned marker into the host ledger `~/.local/state/lore/<slug>.db`. Re-running **no-ops** when `lore.yaml` exists and the ledger carries that marker (never re-scaffolds, never nukes the index). A ledger without the marker (a failed index, or one written before #572) is not provisioned: setup cold-indexes again. |
| `start` | Launch the container (delta-reconcile runs on startup) + merge `.mcp.json`. It **refuses first, before any teardown**, when a declared static tier is unmaterialised on the host (absent, empty or not a directory), and prints the cold-index command to fix it. On success it **waits for the MCP port to actually accept connections** before declaring success — a "running" container can still be mid-boot delta-reconcile with the port unbound (see "Port-probe / wait-for-bind" below). Already-running-and-bound ⇒ fast no-op. |
| `stop` | Stop + remove the container. The store's data and the host state dir (ledger included) **persist**. Not-running ⇒ no-op. |
| `status` | Report running/stopped, the host ledger's recorded owner path and provisioned marker, AND **probes the live MCP port** to report `ACCEPTING`/`NOT ACCEPTING` — container state alone does not prove the server is reachable. It prints **no index count**: the index lives in the store, so it names the `lore_index()` MCP tool as where to read the counts (the server must be running). For a stopped container it skips the probe. |
| `conform` | **Post-build, NOT on `start`.** Runs the **baked** pytest inside the deployed image against this repo mounted `:ro`, gated by a provenance guard that asserts the members import the BAKED artifact, not the mount — the instrument for #139 (*the test env is a fiction*: a suite green on the dev host proves the source, never the deployed artifact). Takes **no `--project`** (it gates the IMAGE); `--image` overrides `localhost/lore:latest`. Run it after `podman build`, before deploying (~3 min). |

Read `references/lifecycle.md` for the precise step sequence, the persistence
guarantees, and the failure/STOP conditions of each verb. Read
`references/server-interface.md` for the live server contract (entrypoint,
healthcheck, state-dir layout, `.mcp.json` shape).

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
Claude Code harness auto-loads at session start. That flat file does not scale.
- **Only the first 200 lines or 25 KB of `MEMORY.md` load**, whichever comes first.
  Everything past that is **silently not loaded**.
- **Topic files beside it are never loaded at startup**; an agent reads them only if it
  happens to look.

So a growing store loses memory without any error: whatever sits past the limit, which is
the newest entries when they are appended at the end.
(Source: code.claude.com/docs/en/memory, checked 2026-11-09.) Storing project memory there
is the exact anti-pattern lore exists to kill — and a dogfood miss for any project on lore.

So `MEMORY.md` is a **one-line bootstrap**: the marker plus a pointer to lore, locked
immutable (operator, 2026-11-09). The **second-zero operational landmines live in lore
too**, as memories labelled `harness_type=landmine`. The project's `CLAUDE.md` tells each
session to recall them first (template below). Lore finding #607 will move that rule into
lore's served instructions. Everything else is recalled on demand.

**This is a lifecycle responsibility, not just documentation.** Run the checks below on
**every** `setup` and `start`. Each step is idempotent, and a step already satisfied is a
no-op.

### Where the native memory lives

The harness keeps a project's auto-memory at `~/.claude/projects/<ENC>/memory/`, where
`<ENC>` is the project's **absolute** path with **every non-alphanumeric character
replaced by `-`** (per character — no collapsing of runs, no lowercasing). Examples:

- `/home/ejprice/PycharmProjects/lore` → `-home-ejprice-PycharmProjects-lore`
- `/home/u/.config/x_y` → `-home-u--config-x-y` (`.` and `_` both become `-`)

**Derive this path, then assert the directory exists before trusting it.** If it does
not, do **not** conclude "no memory"; the derivation can be wrong for an edge-case path.
Run `ls ~/.claude/projects/ | grep <project-basename>`:
- **If it finds nothing,** the project has never had memory, so `mkdir -p` the derived path.
- **If it finds anything else,** have the operator name the right dir. A basename match
  can belong to a *different* project (`grep lore` matches `-…-dndlorescraper`).
  Adopting it would migrate that project's memories into this project's lore and lock its
  `MEMORY.md`. Never adopt a dir on a name match alone.

A wrong derivation silently migrates nothing.

The dir holds `MEMORY.md` plus one `<slug>.md` topic file per memory, each with YAML
frontmatter (`name` / `description` / `metadata.type`) and a body. It may also hold
`archived-*/` subdirectories from earlier migrations. **Those are already migrated:
every scan below is top-level only.**

### Classifying the project's memory state

Topic files means `find <memdir> -maxdepth 1 -name '*.md' ! -name MEMORY.md`.

**One-line form** means `MEMORY.md` is a single line that starts with the marker and has
nothing under it.
- It is **current** when its text equals the template below; the date may differ.
- It is **stale** when it has the one-line shape but different text. For example, an
  older pointer with the unlabelled recall.

Each state below lists **what you check**, and then **what you do when the check finds
work**. Check **Needs migration** first; it takes precedence over Done.

- **Needs migration** (defined below) — if any of its conditions hold, go there.
- **Done.**
  - *Checks:* one-line form, current; locked; `.claude/settings.local.json` has
    `autoMemoryEnabled: false`; the project `CLAUDE.md` carries the landmine rule.
    - On Linux, `lsattr` shows `i`.
    - On macOS, `ls -lO` shows `uchg`.
  - *If any check fails,* run only the part that's missing. There is nothing to
    migrate, so steps 1–5 do not apply. The one-line *shape* is what makes the protocol
    idempotent. The marker alone proves nothing.
    - *Stale text:* unlock, write the current template, then lock it and prove the lock
      (step 6's commands).
    - *Unlocked:* step 6's lock and its proof only.
    - *Settings:* step 7.
    - *Rule:* step 8.
- **Absent** (no `MEMORY.md`, no topic files).
  - *Checks:* none; there is nothing to migrate.
  - *Do (lore is not needed):* write the one-line template, lock it (step 6's lock and
    its proof), then run steps 7–8.
- **Needs migration.** Any one of:
  - legacy/flat: no marker, with index lines or topic files;
  - old-form bootstrap: the marker, plus landmine bullets or other lines under it;
  - stray topic files beside any `MEMORY.md`.

  ⚠ **The marker does NOT mean migrated.** Every entry (defined in step 2) and every
  topic file is a memory. Migrating needs the lore tools **in this session**. A freshly deployed lore
  only appears after a session reload (see "Activating it in-session").
  - *If the lore tools are not loaded:*
    - do **not** run steps 6–8;
    - **leave auto-memory on**, so the file keeps loading and its landmines stay in front
      of the next session;
    - record the pending migration durably by adding this section at the top of the
      project's `CLAUDE.md`:
      `## PENDING — lore memory migration: run the lore-deploy skill's memory protocol (steps 1–8) before any other work.`
    - tell the operator to reload.
  - *If the lore tools are loaded:* run steps 1–8, and delete that PENDING section at
    the end.

### The migration protocol

**Memory loss is unrecoverable — follow every step, skip none:**

1. **Back up first.** `cp -a <memdir> <memdir>.bak-<UTC-stamp>` before touching
   anything. Nothing below ever deletes this backup.
2. **Build the worklist** — the **union** of:
   - (a) every top-level topic file;
   - (b) every **entry** in `MEMORY.md`. An entry is an index line, or a bullet *together
     with its continuation lines*. Never split a bullet into its lines: a continuation
     line stored alone loses its subject. Headings, blank lines, the marker and the
     bootstrap's pointer prose are not entries.

   Reconcile the two. A topic file with no index entry is *still a memory* (migrate
   it). An index entry with no file is a one-line memory (migrate its text). Enumerate
   **both** sides, because one file may be referenced twice or not at all.

   **Mark each item `landmine` or not, now.**
   - Every bullet in an old-form "Operational landmines" section is a landmine.
   - In a legacy/flat store, mark the few facts that cause damage or wasted effort if
     unknown at second zero: store/port topology, "do not run X", forward-only
     migrations, where the plan of record lives.
   - List your landmine picks in the report, for the operator to adjust.
3. **Migrate each item** into lore:
   - Read the topic file and carry its body **verbatim** — a memory records what was true
     when written; do **not** summarise, "improve", or invent.
   - **Dedup — non-landmine items only.** Run
     `lore_recall(query=<the item's title/description>, k=5)`. If an existing memory (one
     *without* an `origin=claude_native_memory` label) already states the same fact,
     record it as "covered by `<id>`" and **skip the write**. When in doubt, **write**: a
     redundant memory is cheap, and a dropped fact violates no-loss.
   - **Landmine items are never dedup-skipped** against memories without the landmine
     label. Those memories don't load at session start, so skipping would drop the
     landmine from the second-zero load. Skip one only when a memory that already
     carries `harness_type=landmine` states it. Old-form landmine bullets often end with
     a `lore_recall("…")` pointer to a sibling memory; that pointer is exactly the case
     where you **still write**.
   - **Write:** `lore_remember(text=<verbatim body>, kind=<mapped>, trust=<mapped>,
     labels=["origin=claude_native_memory", "source_file=<name>", "harness_type=<type>"])`.
     Map the frontmatter `type` to a lore `kind`: `reference`→`fact` (`trust=authoritative`)
     · `feedback`→`decision` · `project`→`fact` · `user`→`fact` · anything else→`fact`.
     **A landmine item** is written with `kind=gotcha` and `harness_type=landmine`
     (`source_file=MEMORY.md` for an index line). **Never `ongoing`** — it carries a 7-day
     TTL and would silently **expire** the migrated memory. The labels keep every
     migrated memory traceable back to its source.
   - **Verify:** `lore_recall` the fact you just wrote and confirm it comes back.
4. **Account for every item.** Each worklist item is now either *written-and-verified* or
   *covered-by-existing*. No item unaccounted — this is the no-loss gate. Cross-check the
   count against step 2.
5. **Check the landmines in lore.** Run
   `lore_recall(query="operational landmines", labels=["harness_type=landmine"], k=50)`.
   It must return **every item step 2 marked `landmine`**; count against the worklist,
   not against what you wrote. **Bound:** the render prints no total match count. If it
   returns exactly 50, re-run with `k=100` (the maximum). If it still returns 100, say
   so: landmines past that are silently cut.
6. **Archive, don't delete — only after steps 4 AND 5 pass.**
   - Move the topic files into `<memdir>/archived-<stamp>/`. The step-1 backup stays
     regardless. (Archiving over deletion mirrors this repo's report-archival law: an
     address that resolves beats a clean tree.)
   - **If `MEMORY.md` is already the locked one-line form** (the stray-topic-files case),
     leave it in place and locked; you are done with this step.
   - **Otherwise:**
     - if the file is locked, unlock it first:
       - Linux: `lsattr` shows `i`, so run `sudo -n chattr -i <memdir>/MEMORY.md`;
       - macOS: `ls -lO` shows `uchg`, so run `sudo chflags nouchg <memdir>/MEMORY.md`;
     - move the old file in as `MEMORY.md.pre-oneline`;
     - write the one-line template;
     - lock it: `sudo -n chattr +i <memdir>/MEMORY.md`.
   - **Prove the lock:** `lsattr` shows `i`, and `: >> <memdir>/MEMORY.md` fails with
     "Operation not permitted". That command opens the file for append but writes
     nothing, so if the lock silently failed it does not add a junk line. Undo is
     `sudo chattr -i`.
   - **macOS:** lock with `sudo chflags uchg`, check with `ls -lO` (shows `uchg`), and
     undo with `sudo chflags nouchg`.
   - **If `sudo -n` is refused,** give the operator the exact command and report the file
     as **unlocked**. Never skip the step silently.
7. **Turn off the harness's file memory for this project, never globally:**
   ```bash
   f=<project>/.claude/settings.local.json; mkdir -p "$(dirname "$f")"; [ -f "$f" ] || echo '{}' > "$f"
   cp -a "$f" "$f.bak-<UTC-stamp>" && jq '.autoMemoryEnabled = false' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
   ```
   Never touch `~/.claude/settings.json`. `settings.local.json` is per-checkout, so other
   clones keep auto-memory until they run this skill. That is by design.

   **Why (MEDIUM — from the harness's own memory prompt, not tested):** while auto-memory
   is on, each session carries a built-in instruction to save memories as topic files in
   `<memdir>` and index them in `MEMORY.md`. The locked file cannot be indexed, so those
   files would sit where nothing reads them. **Expected effect (MEDIUM; confirm in a fresh
   session and report what you observed):** the built-in memory prompt goes away and
   `MEMORY.md` stops loading. Step 8 replaces both.
8. **Install the landmine rule** (template below) near the top of the project's
   `CLAUDE.md`. Create the file with just this section if there is none, and delete any
   PENDING migration section. `CLAUDE.md` is a tracked file: tell the operator it
   changed, and commit only when they ask. When #607 ships, this section is removed from
   **every** project that has it, not only lore.

### The bootstrap `MEMORY.md` template (one line, exactly)

```markdown
<!-- LORE-MEMORY-BOOTSTRAP --> Project memory lives in lore, not here: recall with lore_recall("<topic>"), landmines with lore_recall(query="operational landmines", labels=["harness_type=landmine"], k=50); save with lore_remember; this file is immutable (chattr +i) by operator order, <YYYY-MM-DD>.
```

### The `CLAUDE.md` landmine rule template

```markdown
## FIRST ACTION OF EVERY SESSION — load the landmines from lore
Every session and every spawned agent, before any other work, and again after a context
compaction. A spawned agent does its brief's mandated first action (e.g. reading
brief-base) first, then this. Exception: Haiku agents (`haiku-runner` / `haiku-worker`),
whose briefs are self-contained.
1. `ToolSearch "+lore", max_results 20` (lore's tools are deferred).
2. `lore_recall(query="operational landmines", labels=["harness_type=landmine"], k=50)`.
   If it returns exactly 50, re-run with `k=100`; the render prints no total. If that
   returns 100, say landmines may be cut off.

If lore is unreachable, say so in your first reply and never proceed as if there were no
landmines. Start it with
`python3 ~/.claude/skills/lore-deploy/scripts/lore_deploy.py start --project <abs-dir>`,
then reload the session (`claude --continue`) and recall. Save a new landmine with
`lore_remember(..., kind="gotcha", labels=["harness_type=landmine", ...])`; without that
label this recall does not load it.
```

### Writing memory going forward

Once bootstrapped, **do not add facts back into `MEMORY.md`**. The lock enforces this
where step 6 proved it. Write durable project memory with `lore_remember`, and recall it
with `lore_recall`. A new second-zero fact is a landmine: save it with
`harness_type=landmine` so the session-start recall loads it. The project's `CLAUDE.md`
carries this rule (step 8), so it survives when this skill is not in context.

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
- **The store + the host state dir persist across `stop`/`start`.** `stop`
  removes only the lore container. The SurrealDB store's data (the index, in the
  separate, always-on `lore-surreal` container) survives, which is what makes
  restart a cheap delta-reconcile; so does `~/.local/state/lore/` (setup's
  `<slug>.db` ledger, which holds no index state).

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
periodic reconcile ~10 min backstop; `lore_search(..., wait_for_fresh=True)` for the
edit-then-query race; `lore_index(reconcile=True, tier=...)` to force a whole tier), and the
project-memory stance. A connecting agent gets all of that automatically — there is
nothing to relay from this skill.

Operator-relevant freshness note only: `status` does not read index counts. Call the
`lore_index()` MCP tool (files indexed / in-flight / failed, last sync and sweep ages)
to confirm a deploy's index is current and healthy; `status` only names it. Everything else about querying belongs to the consumer and lives in the
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
