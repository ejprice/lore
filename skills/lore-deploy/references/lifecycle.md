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
- **Secrets:** delivered via `--env-file <secrets.env>`. Required keys: the
  embedder bearer (`api_key_env`, default `LORE_TEI_KEY`) and the Qdrant key
  (`QDRANT__SERVICE__API_KEY`). When auth is enabled, also `LORE_<SLUG>_KEY`.

## `setup` — once per project (idempotent; expensive parts no-op on re-run)

1. **Detect an existing deployment.** If `lore.yaml` exists AND the `lore_<slug>`
   collection exists AND the manifest has indexed rows → print
   `setup: already provisioned (no-op)` and exit 0. (Do NOT re-scaffold, do NOT
   re-index, do NOT touch the collection.)
2. **Scaffold `lore.yaml`** (only if absent): slug from the dir name, `root: .`,
   the embedding block (tei / voyage-4-nano / dim 2048 / 8192 / batch 32 /
   concurrency 2 / `truncate: false` / `connect_timeout_s: 5` /
   `tokenizer: voyage-4-nano` / `api_key_env: LORE_TEI_KEY`), the qdrant block
   (`http://127.0.0.1:16333`, `api_key_env: QDRANT__SERVICE__API_KEY`), a **free
   server port** (probe upward from 9201 for the first unbound port), include
   globs for the project's real file types, and `exclude_dirs` **seeded from the
   project `.gitignore`** (plus `.git`, `__pycache__`, `.pytest_cache`). The
   schema is `loremaster.config.LoreConfig`; validate it parses before writing.
3. **Verify env keys present.** Read the secrets env-file; STOP with a clear
   message if `LORE_TEI_KEY` or `QDRANT__SERVICE__API_KEY` is missing/empty.
4. **Hard-probe `/embed`** (`scripts/probe_embed.py`). STOP if unreachable
   (allow the fp32 warmup ~20–40 s — poll `/health` first) or if the observed
   dimension ≠ `config.dim`.
5. **Ensure collections** (`scripts/ensure_collections.py`). Creates
   `lore_<slug>` + `lore_<slug>_memory` at `size=dim`/cosine with payload
   indexes if absent. **STOP on a dim mismatch** between an existing collection
   and `config.dim` — never auto-recreate.
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

1. **Already running?** `podman container exists lore-<slug>` and it is in the
   `running` state → print `start: already running (no-op)` and exit 0.
2. **Pre-flight:** hard-probe `/embed` (STOP if down/wrong dim); confirm the
   collection exists (if not, tell the user to run `setup` first — do NOT
   silently cold-build on `start`).
3. **Launch the container** (see the run invocation below). On startup the
   server runs the **delta-reconcile**: walk included roots → mtime+size
   fast-path → re-index only the changed delta, purge deletions. No cold
   rebuild.
4. **Merge `.mcp.json`** (idempotent — re-merging the same entry is a no-op).
5. Report status.

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
  --env-file <secrets.env> \
  -e LORE_CONFIG=/workspace/lore.yaml \
  localhost/lore:latest
```

- `--network=host` — Qdrant is host-loopback-only (`127.0.0.1:16333`); the
  container reaches it (and the LAN TEI endpoint) only via the host netns.
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
2. If running, query `index_status()` (via the MCP endpoint or the server's
   status command) for freshness: total points, in-flight (`dirty`/`embedding`)
   files, `files_failed`. Report `files_failed == 0` as healthy.
3. If stopped, report the last manifest state (read `~/.local/state/lore/
   <slug>.db` counts) so the user knows the index is preserved.

## Failure / STOP conditions (loud, never silent)

| Condition | Action |
|---|---|
| `/embed` unreachable after warmup poll | STOP — print the URL + remediation; do not start a server with no embedder. |
| probe dim ≠ `config.dim` | STOP — dimension mismatch; do not index. |
| existing collection size ≠ `config.dim` | STOP — **never auto-recreate**; print remediation (the operator decides: recreate+reindex, or fix the config). |
| missing/empty secret env var | STOP — name the variable. |
| image missing on `start` | STOP — tell the user to run `setup` (which builds it). |
| collection missing on `start` | STOP — tell the user to run `setup` (cold index). |
