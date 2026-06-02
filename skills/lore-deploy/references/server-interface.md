# Server-interface contract (live)

The loremaster MCP server is **built and serving** — verified live on the
demand_intelligence + lore deploys. This file documents the real contract the
deploy artifacts depend on; the running server is the source of truth.

## 1. The server entrypoint

`CMD ["python", "-m", "loremaster.server"]` is the live entrypoint. It:

- reads `LORE_CONFIG` (path to the mounted `lore.yaml`),
- configures lore-namespace structured logging (`LoggingConfig` / `LORE_LOG_LEVEL`),
- runs the **startup probe gate** (probe `/embed`; refuse to start on
  unreachable / dim ≠ `config.dim` / dim ≠ collection size — never auto-recreate),
- runs the **startup delta-reconcile** + spawns the watcher (this heavy startup
  runs **once per process**, shared across MCP sessions — a ref-counted guard),
- serves FastMCP **streamable-http** on `config.server.{host,port,path}`
  (e.g. `127.0.0.1:9201/mcp`).

**Healthcheck rule (load-bearing):** "container up" + "manifest indexed=N" is NOT
proof the endpoint serves — verify `/mcp` answers. A live MCP streamable-http
server returns **HTTP 406** to a bare `GET /mcp` (it wants a POST with an MCP
`Accept` header); 406 = alive. `start` must check the endpoint, not just that the
container is running. Under `--network=host` the real listening port is
`config.server.port`; `podman ps` shows only the image metadata, not the bound
port — confirm with `ss -ltn` or the `Uvicorn running on …` log line.

## 2. Manifest + code-graph location (RESOLVED empirically)

The batch indexer and the server BOTH default the manifest to
`Path.home()/.local/state/lore/<slug>.db` and the code-graph to
`…/<slug>.graph.db` (`mkdir -p`'d). **The resolved, verified wiring** (from the
live demand_intelligence + lore deploys) is:

- `--user $(id -u):$(id -g)` (with `--userns=keep-id`) so the process runs as the
  host user and can write the host bind — bare keep-id runs as the image's `lore`
  user (UID 999) and hits `Permission denied`.
- `-e HOME=/home/lore` so `Path.home()` resolves to the image's lore home.
- `-v ~/.local/state/lore:/home/lore/.local/state/lore` — the host state dir
  mounted **exactly at `$HOME/.local/state/lore`**, where loremaster reads/writes
  it. The old `/state` mount was a dead path the server never reads (graph tools
  empty, manifest lost on restart). One source of truth for the state dir, both
  processes — the host cold-index and the container server share it.

## 3. `index_status()` exposure for `status` / healthcheck

The skill's `status` verb and the healthcheck want `index_status()` — total
points, in-flight (`dirty`/`embedding`) files, `files_failed`. This is a live MCP
tool on the server. For a **stopped** container `status` falls back to reading the
SQLite manifest directly (`~/.local/state/lore/<slug>.db`, table `files`, column
`state`) — the correct stopped-state path, since a stopped container has no MCP
endpoint to query.

## 4. `.mcp.json` transport + auth header

For the **local no-auth** default the skill writes a **headerless** `.mcp.json`
entry (the server has no auth middleware; a `Bearer ${UNSET}` would only mislead
and risk an unresolvable env-var expansion in the client):

```json
{"mcpServers": {"lore_<slug>": {
  "type": "http",
  "url": "http://127.0.0.1:<port>/mcp"
}}}
```

When the deferred Bearer-key auth (D9/A1.12) is enabled, run
`merge_mcp_json.py … --auth-key-env LORE_<SLUG>_KEY` to emit a
`headers: {"Authorization": "Bearer ${LORE_<SLUG>_KEY}"}` entry, set that env var,
and enable `auth` in `lore.yaml`. Confirm the mount path matches
`config.server.path` (default `/mcp`).

## 5. Cold-index vs. start-time reconcile

`setup` cold-indexes via `python -m loremaster.index --config <lore.yaml>` (the
batch-indexer CLI). `start` relies on the **server's** startup reconcile to bring
the index current — it does NOT re-run the batch indexer. The server owns the
startup delta-reconcile (verified: a restart re-indexes only what changed), so
`start` just launches the container.
