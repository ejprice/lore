# Server-interface contract (live)

The loremaster MCP server is **built and serving** — verified live on the
demand_intelligence + lore deploys. This file documents the real contract the
deploy artifacts depend on; the running server is the source of truth.

## 1. The server entrypoint

`CMD ["python", "-m", "loremaster.server"]` is the live entrypoint. It:

- reads `LORE_CONFIG` (path to the mounted `lore.yaml`),
- configures lore-namespace structured logging (`LoggingConfig` / `LORE_LOG_LEVEL`),
- runs the **startup probe gate** (probe `/embed`; refuse to start on
  unreachable / dim ≠ `config.dim` / dim ≠ the stored SurrealDB index size —
  never auto-recreate; the server owns schema + dim, incl. the
  embedding-schema-fingerprint rebuild),
- runs the **startup delta-reconcile** + spawns the watcher (this heavy startup
  runs **once per process**, shared across MCP sessions — a ref-counted guard),
- serves FastMCP **streamable-http** on `config.server.{host,port,path}`
  (e.g. `127.0.0.1:9201/mcp`).

**Healthcheck rule (load-bearing):** "container up" + "the ledger says
provisioned" is NOT proof the endpoint serves — verify `/mcp` answers. A live MCP streamable-http
server returns **HTTP 406** to a bare `GET /mcp` (it wants a POST with an MCP
`Accept` header); 406 = alive. `start` must check the endpoint, not just that the
container is running. Under `--network=host` the real listening port is
`config.server.port`; `podman ps` shows only the image metadata, not the bound
port — confirm with `ss -ltn` or the `Uvicorn running on …` log line.

## 2. State-dir location (RESOLVED empirically)

Since P5 the index, its manifest and its code graph live in the SurrealDB store,
not on the host. The host state dir `Path.home()/.local/state/lore/` holds
`setup`'s ledger `<slug>.db` (the owning project path and the provisioned
marker; no index state), the server's `<slug>.memory.db`, and the calibration
cache. **The resolved, verified wiring** (from the live demand_intelligence +
lore deploys) is:

- `--user $(id -u):$(id -g)` (with `--userns=keep-id`) so the process runs as the
  host user and can write the host bind — bare keep-id runs as the image's `lore`
  user (UID 999) and hits `Permission denied`.
- `-e HOME=/home/lore` so `Path.home()` resolves to the image's lore home.
- `-v ~/.local/state/lore:/home/lore/.local/state/lore` — the host state dir
  mounted **exactly at `$HOME/.local/state/lore`**, where loremaster reads/writes
  it. The old `/state` mount was a dead path the server never reads. One state
  dir for both sides: the host `setup` writes its ledger there, and the container
  server keeps its state files there.

## 3. Index counts come from `lore_index()`, never from `status`

The index counts (files indexed / in-flight / failed, last sync and sweep ages)
live in the store and are served by the `lore_index()` MCP tool; with no
arguments it is a cheap status read that never sweeps. The skill's `status` verb
does not read them: it prints the ledger's owner path and provisioned marker and
names `lore_index()` as where the counts live. A **stopped** container has no MCP
endpoint, so its index counts are unavailable until `start`; the host ledger
holds none (a pre-P5 ledger's `files` table describes an index nothing has
written since P5, and `status` does not read it).

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

## 6. Secrets env-file (per-slug)

The container's secrets (the embedder bearer `LORE_TEI_KEY`, the SurrealDB root
credentials `SURREAL_USER` / `SURREAL_PASS`, `ANTHROPIC_API_KEY`, and — when auth
is on — `LORE_<SLUG>_KEY`) are passed
via `--env-file`. The path is **per-slug**: `~/docker/mcp/lore-secrets/<slug>.env`,
one file per project, resolved from the project dir name when `--env-file` is
omitted. An explicit `--env-file` is honored verbatim. There is **no** shared
project-agnostic `~/docker/mcp/lore.env` — it never existed on-host, so depending
on it resolved to a missing file and `podman run` exited 125 (verified: the
demand_intelligence secrets live at `~/docker/mcp/lore-secrets/demand_intelligence.env`).

## 5. Cold-index vs. start-time reconcile

`setup` cold-indexes on the host via
`<interpreter> -m loremaster.index --config <abs lore.yaml>` (the batch-indexer
CLI), where `<interpreter>` is `_loremaster_python()`: `$LORE_PYTHON`, else
`~/PycharmProjects/lore/.venv/bin/python`, else the dispatcher's own interpreter.
By hand, `uv run python -m loremaster.index --config <abs lore.yaml>` from the
lore repo root uses the same `.venv`. `start` relies on the **server's** startup
reconcile to bring the index current — it does NOT re-run the batch indexer. The
server owns the startup delta-reconcile (verified: a restart re-indexes only what
changed). Before launching, `start` only checks that every declared static tier
is materialised on the host (`SnapshotLayout.is_materialized`). If one is not,
it refuses and prints the cold-index command above as the remedy (see
lifecycle.md, "Snapshot dir").
