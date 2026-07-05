# lore-deploy — lifecycle step sequences

The authoritative per-verb behaviour. The dispatcher (`scripts/lore_deploy.py`)
implements this; this document is the spec it follows and the reference when a
step needs manual intervention.

## Shared facts

- **Image:** `localhost/lore:latest` (one shared image; never per-project).
- **Container name:** `lore-<slug>` (slug from `lore.yaml` `project.slug`).
- **Collections:** `lore_<slug>` (code/docs) + `lore_<slug>_memory` (project
  memory). Both `size=dim`, `distance=cosine`, with the base payload indexes
  (`tier`, `file_path`, `content_hash`, `chunk_type`).
- **Manifest:** `~/.local/state/lore/<slug>.db` (SQLite, WAL). The authority on
  per-file/per-tier index state. **Persists across stop/start** — it lives on
  the host and is bind-mounted into the container.
- **Snapshot dir (static tiers only):** `~/docker/mcp/lore-snapshot/<tier>/…`,
  bind-mounted `:ro` at `/source`. A bare single-live-tree project (like
  demand_intelligence) declares no static roots and needs no `/source` mount.
- **Secrets:** delivered via `--env-file`. The default is **per-slug**:
  `~/docker/mcp/lore-secrets/<slug>.env` (one file per project, resolved from the
  project dir name when `--env-file` is omitted). An explicit `--env-file` is
  honored verbatim. There is **no** shared project-agnostic `~/docker/mcp/lore.env`
  — relying on one resolved to a missing file and `podman run` exited 125. Required
  keys: the embedder bearer (`api_key_env`, default `LORE_TEI_KEY`), the SurrealDB
  root credentials (`SURREAL_USER` / `SURREAL_PASS`), and `ANTHROPIC_API_KEY`
  (resolved eagerly at server start). When auth is enabled, also `LORE_<SLUG>_KEY`.

## `setup` — once per project (idempotent; expensive parts no-op on re-run)

1. **Detect an existing deployment.** If `lore.yaml` exists AND the manifest
   (`~/.local/state/lore/<slug>.db`) is present → print
   `setup: already provisioned (no-op)` and exit 0. (Do NOT re-scaffold, do NOT
   re-index, do NOT touch the store.)
2. **Scaffold `lore.yaml`** (only if absent): slug from the dir name, `root: .`,
   the embedding block (tei / voyage-4-nano / dim 2048 / 8192 / batch 32 /
   concurrency 2 / `truncate: false` / `connect_timeout_s: 5` /
   `tokenizer: voyage-4-nano` / `api_key_env: LORE_TEI_KEY`), the surreal block
   (`ws://127.0.0.1:18500/rpc`, `namespace: lore`, `user_env: SURREAL_USER` /
   `password_env: SURREAL_PASS`), the REQUIRED anthropic block
   (`api_key_env: ANTHROPIC_API_KEY`, `yardstick_model: claude-sonnet-5`), a **free
   server port** (probe upward from 9201 for the first unbound port), include
   globs for the project's real file types, and `exclude_dirs` **seeded from the
   project `.gitignore`** (plus `.git`, `__pycache__`, `.pytest_cache`). The
   schema is `loremaster.config.LoreConfig`; validate it parses before writing.
3. **Verify env keys present.** Read the secrets env-file; STOP with a clear
   message if it is absent (the required keys are `LORE_TEI_KEY`, the SurrealDB
   root credentials `SURREAL_USER`/`SURREAL_PASS`, and `ANTHROPIC_API_KEY`).
4. **Hard-probe `/embed`** (`scripts/probe_embed.py`). STOP if unreachable
   (allow the fp32 warmup ~20–40 s — poll `/health` first) or if the observed
   dimension ≠ `config.dim`.
5. **Pre-flight the SurrealDB store** (inline `_probe_surreal`, stdlib-only).
   Confirm the unified store answers `/health` — an HTTP GET derived from
   `surreal.url` (`ws(s)://host:port/rpc` → `http(s)://host:port/health`, same
   host:port). If it does not answer **and** the `lore-surreal` container exists
   but is stopped, `podman start lore-surreal` and re-poll `/health` for a bounded
   budget (reboot recovery — the container's restart policy is `no`). Still
   unreachable, or no such container to start, **STOP** (`_EXIT_ERROR`, loud,
   naming the URL + the container). This gates on store **REACHABILITY only** —
   schema + embedding-dimension ownership (including the
   rebuild-on-fingerprint-change) lives in the server. The skill **never** creates,
   recreates, or removes the store container or touches its data dir;
   start-if-stopped is its only permitted mutation.
6. **Build the image if missing.** `podman image exists localhost/lore:latest`
   → if absent, `podman build --build-arg LORE_VERSION="$(git describe --tags --always --dirty)" -t localhost/lore:latest -f Containerfile .`
   from the lore workspace root — the `--build-arg` bakes the git-derived version
   the server advertises as `serverInfo.version`.
7. **Cold-index.** Run the batch indexer ONCE:
   `python -m loremaster.index --config <lore.yaml>` (in-container or against
   the workspace venv). This is the expensive step paid once.
8. **Merge `.mcp.json`** (`scripts/merge_mcp_json.py`).
9. Report status.

## `start` — launch for a working session (idempotent)

1. **Already running + current image?** `lore-<slug>` is `running` AND its baked
   image ID matches the current `localhost/lore:latest` tag → **probe the MCP
   port first** (see "Port-probe / wait-for-bind" below). If it's already
   ACCEPTING → no-op, re-merge `.mcp.json` (so wiring survives a reboot), and
   exit 0. No reconnect reminder — nothing changed. If it is NOT yet
   accepting (container up but still mid boot-reconcile), enter the
   wait-for-bind loop before declaring success — do NOT treat "running" alone
   as done.
1a. **Already running + STALE image?** `lore-<slug>` is `running` but its baked
   image ID differs from the current tag (the image was rebuilt) → **recreate**.
   `podman restart` reuses the same baked image, so only stop + rm + run picks up
   the new code. **Validate-before-teardown (outage guard):** verify EVERY launch
   precondition FIRST — the image is present (`podman image exists`) AND the
   resolved env-file exists. If any fails, STOP with `_EXIT_ERROR` and leave the
   running (stale) container **untouched** — a stale-but-serving container beats a
   dead one. Only once the preconditions are known good: `podman stop` → `podman rm`
   → relaunch. A relaunch (`podman run`) failure after teardown degrades gracefully
   (loud on stderr, `_EXIT_ERROR`), never an uncaught exception. On success,
   **wait for bind** (below), then re-merge `.mcp.json` and print the
   MCP-reconnect reminder.
2. **Pre-flight (not-running path):** hard-probe `/embed` (STOP if down/wrong dim);
   pre-flight the SurrealDB store's `/health` (`_probe_surreal` — STOP if
   unreachable, with the bounded start-if-stopped reboot recovery from `setup`
   step 5). `start` gates only on the store being **reachable** — it never
   inspects collection/dim state (the server owns schema + dim, including the
   rebuild-on-fingerprint-change).
3. **Launch the container** (see the run invocation below). On startup the
   server runs the **delta-reconcile**: walk included roots → mtime+size
   fast-path → re-index only the changed delta, purge deletions. No cold
   rebuild. This delta-reconcile runs BEFORE uvicorn binds the port, which is
   exactly why step 3a below exists — a launched container is not yet a
   reachable server.
3a. **Wait for bind.** Poll the MCP endpoint (POST a minimal MCP `initialize`
   request; any HTTP response — even non-2xx — counts as bound) every ~3s up
   to `--bind-timeout` seconds (default 600s; `--no-wait` skips this step
   entirely, fire-and-forget). Print a progress line every ~30s while
   waiting. On timeout: exit non-zero with a loud message including the tail
   of `podman logs`.
4. **Merge `.mcp.json`** (idempotent — re-merging the same entry is a no-op).
5. Report status.

### Port-probe / wait-for-bind (shared by `start` and `status`)

Neither verb may treat "container running" as "server reachable" — loremaster's
ASGI lifespan startup runs the boot-time delta-reconcile **before** uvicorn
binds the port, so a freshly-launched (or even long-running, if the reconcile
is still churning through embedder 429 backoff) container can refuse
connections for minutes. `lore_deploy.py` implements the probe itself
(`_probe_mcp_port` / `_wait_for_bind`, stdlib-only urllib/socket — no sibling
script, since both `status` and `start` need it inline):

- Reads `host` / `port` / `path` from the project's `lore.yaml` `server:` block.
- POSTs a minimal MCP `initialize` JSON-RPC request with
  `Content-Type: application/json` and `Accept: application/json, text/event-stream`.
- **Success = any HTTP response** — a 2xx counts as serving, but so does a
  non-2xx (e.g. a 400 from a malformed probe body): either one proves the
  port is bound and something is answering HTTP there. Only a connection
  refused / reset / timeout means "not accepting".
- Per-attempt timeout ~3s.

### Run invocation (the proven host pattern)

```
podman run -d --name lore-<slug> \
  --network=host \
  --userns=keep-id \
  --user $(id -u):$(id -g) \
  -e HOME=/home/lore \
  -v <project>:/workspace:ro \
  -v ~/.local/state/lore:/home/lore/.local/state/lore \
  [ -v <snapshot>:/source:ro ]            # only if lore.yaml declares a static root
  --env-file ~/docker/mcp/lore-secrets/<slug>.env \   # per-slug; explicit --env-file overrides
  -e LORE_CONFIG=/workspace/lore.yaml \
  localhost/lore:latest
```

- `--network=host` — the SurrealDB store is host-loopback-only
  (`127.0.0.1:18500`); the container reaches it (and the LAN TEI endpoint) only
  via the host netns.
- `--userns=keep-id` **+ `--user $(id -u):$(id -g)`** — pins the container
  process to the host `uid:gid`, which keep-id maps 1:1, so the bind-mounted
  manifest dir (owned by the host user) is **writable**. Bare `--userns=keep-id`
  alone runs as the image's `lore` user (UID 999) → `Permission denied` on the
  host bind. **VERIFIED empirically** on the demand_intelligence + lore deploys.
- `-e HOME=/home/lore` — loremaster resolves the manifest + `<slug>.graph.db`
  under `Path.home()/.local/state/lore`; this pins `$HOME` to the image's lore
  home so those land in the mounted state dir (not an unwritable/ephemeral path).
- `-v ~/.local/state/lore:/home/lore/.local/state/lore` — mounts the host state
  dir **exactly where loremaster reads it** (`$HOME/.local/state/lore`), so the
  container server reads the **same manifest + code-graph the host cold-index
  wrote**, and both persist across stop/start. (The old `/state` mount was wrong:
  the server never reads `/state`, so the graph tools came up empty and a restart
  lost the manifest.)

## `stop` — end the session (idempotent)

1. **Not running?** `podman container exists lore-<slug>` is false → print
   `stop: not running (no-op)` and exit 0.
2. **Stop + remove the container** (`podman stop lore-<slug>` then
   `podman rm lore-<slug>`). The collections and the manifest are untouched.
3. Optionally leave the `.mcp.json` entry in place (a stopped server's entry is
   harmless — the next `start` re-uses it). Report status.

## `status`

1. Container state: `podman container inspect lore-<slug>` → running / stopped /
   absent.
2. If running, report image currency (current vs. stale `localhost/lore:latest`).
3. If running, **probe the MCP port** (see "Port-probe / wait-for-bind" above —
   one attempt, ~3s timeout, no wait loop) and print a structured line:
   `status: mcp endpoint http://host:port/path = ACCEPTING` or
   `= NOT ACCEPTING (... likely boot delta-reconcile ...)`. Container state
   alone is NOT sufficient to call the server up — this is exactly the gap
   that let a "running, healthy-looking" `status` coexist with a refused MCP
   connection for ~4 minutes.
4. If running, query `index_status()` (via the MCP endpoint or the server's
   status command) for freshness: total points, in-flight (`dirty`/`embedding`)
   files, `files_failed`. Report `files_failed == 0` as healthy.
5. If stopped, report the last manifest state (read `~/.local/state/lore/
   <slug>.db` counts) so the user knows the index is preserved. **Skip the port
   probe entirely** — there is nothing to probe.

## Failure / STOP conditions (loud, never silent)

| Condition | Action |
|---|---|
| `/embed` unreachable after warmup poll | STOP — print the URL + remediation; do not start a server with no embedder. |
| probe dim ≠ `config.dim` | STOP — dimension mismatch; do not index. |
| SurrealDB store `/health` unreachable on `setup`/`start` | STOP — `_EXIT_ERROR`, loud on stderr naming `surreal.url` + the `lore-surreal` container. One recovery attempt: start-if-stopped (`podman start lore-surreal`) + a bounded re-poll; **never** create/recreate/remove the container or touch its data dir. Dim/schema is the server's concern, not the deploy's. |
| missing/empty secret env var | STOP — name the variable. |
| image missing on `start` | STOP — tell the user to run `setup` (which builds it). |
| recreate precondition unmet (image or env-file missing on the stale-image path) | STOP — `_EXIT_ERROR`, leave the running container untouched (never tear down before validating). |
| relaunch (`podman run`) fails after teardown on recreate | STOP — `_EXIT_ERROR`, loud on stderr; never propagate an uncaught `CalledProcessError`. |
| MCP port never accepts within `--bind-timeout` (default 600s) on `start` | STOP — `_EXIT_ERROR`, loud on stderr with the tail of `podman logs --tail 5`; skipped entirely by `--no-wait`. |
