# lore

> **LORE** — *LORE Obviates Recall Errors.*

**A live, per-project code + docs RAG that plugs into your AI coding assistant as an
[MCP](https://modelcontextprotocol.io) server.**

Large repositories break AI coding assistants: as the working context fills, recall
degrades and the model starts hallucinating APIs, missing call sites, and inventing
file paths. `lore` fixes that by giving the assistant a **fresh, precise, per-project
index** to retrieve from — semantic search over code *and* docs, exact symbol lookup,
a real dependency graph, code↔test links, and a persistent project memory — so it
grounds answers in your actual repository instead of guessing.

Point it at a project; it serves MCP tools that an assistant like Claude Code calls
directly.

## Why lore

- 🔎 **Semantic search over code *and* docs** — ranked `[SOURCE:file:line]` citations with stable keys; summarized, never raw dumps.
- 🧬 **A typed code graph** — `what_imports` / `blast_radius` ("who breaks if I change this?"), `tests_for` (covering tests), `get_symbol` (exact signature). Answers grounded in real edges, not vibes.
- ⚡ **Always fresh** — an inotify watcher re-indexes on save (sub-second); a startup + periodic reconcile heals anything missed during downtime, tracked by a SHA-512 manifest.
- 🧠 **Per-project memory** — `save_memory` / `recall_memory`, so corrections and notes survive across sessions.
- 🧩 **One image, N projects** — a single container image, one config-driven container per project, each keyed to its own vector collection. Never a per-project image.
- 🛠️ **An extensible framework** — `loremaster` is a generic RAG out of the box, *or* the base for a domain-specific server built by subclassing one `Extension` ABC. It never forks the core.
- 🔒 **Correctness-first** — a hard embedder probe-gate, transient-error resilience, and a strict test suite gate every change (pydantic v2, mypy-strict, ruff).

## Packages

A [`uv`](https://docs.astral.sh/uv/)-workspace monorepo (Python 3.14+):

| Package | Role |
|---|---|
| **`lorescribe`** | Language-aware chunkers (Python AST, Markdown, SQL, XML, JavaScript, CSS, text) emitting identity-stamped chunks. |
| **`loresigil`** | A swappable embedder abstraction — self-hosted [TEI](https://github.com/huggingface/text-embeddings-inference) `voyage-4-nano` (dim 2048) with local token counting and resilient batching. |
| **`loremaster`** | The MCP server + extension framework — orchestrates chunkers + embedder into a [Qdrant](https://qdrant.tech) index, a SQLite manifest, and a code-graph; serves the MCP. |

## MCP tools

`search_code` · `read_file` · `get_symbol` · `what_imports` · `blast_radius` ·
`tests_for` · `save_memory` · `recall_memory` · `reindex` · `index_status`

### Freshness & read-your-writes

The inotify watcher re-indexes an edited file within ~seconds; a periodic reconcile
sweep (default ~10 min) is the backstop for any events the watcher missed (not the
normal freshness path). If an agent edits a file and *immediately* re-queries, use
`search_code(..., wait_for_fresh=True)` — it bounded-waits for in-flight files before
returning (and serves stale-with-a-flag on timeout, never hangs). `reindex(tier=...)`
forces a full tier reconcile.

### lore memory vs. your assistant's memory

`save_memory` / `recall_memory` is **project-scoped, embedded, semantically recalled,
and shared across every agent working that project** (and it survives container
restarts). Use it for facts and corrections any agent on *this project* should retrieve
— "the champion curve is served from `get_forecast_v2`, not the backtest." That is
distinct from an assistant's own cross-project/global memory (e.g. Claude Code's), which
holds *your* working context across all your work. Rule of thumb: a durable fact about
**this repo** → lore memory; a fact about **how you work** → the assistant's memory.

## Quickstart

**Prerequisites:** a [Qdrant](https://qdrant.tech) instance, an embedding backend (a
self-hosted TEI endpoint serving `voyage-4-nano` at dim 2048 is the reference; the
embedder is config-swappable), and a container runtime. The run command below is the
rootless-Podman reference on Linux — adapt the flags for Docker.

1. **Configure** — copy the annotated template and edit it for your project:
   ```sh
   cp lore.yaml.sample <your-project>/lore.yaml   # set the slug, include globs, your embedding endpoint + Qdrant URL
   ```
2. **Build the shared image:**
   ```sh
   podman build -t localhost/lore:latest -f Containerfile .
   ```
3. **Run one container per project** (secrets via `--env-file` — never inlined):
   ```sh
   podman run -d --name lore-<slug> \
     --network=host --userns=keep-id --user $(id -u):$(id -g) -e HOME=/home/lore \
     -v <your-project>:/workspace:ro \
     -v ~/.local/state/lore:/home/lore/.local/state/lore \
     --env-file <secrets.env> \
     -e LORE_CONFIG=/workspace/lore.yaml \
     localhost/lore:latest
   ```
4. **Wire it into your assistant** — add an `http` MCP server entry to the project's
   `.mcp.json` pointing at the configured port; the assistant then has the tools above
   against that project.

The included `lore-deploy` helper wraps this as idempotent `setup` / `start` / `stop` /
`status` verbs; collections + the manifest persist across restarts, so a restart is a
cheap delta-reconcile, not a cold rebuild.

## Configuration

Each project carries a `lore.yaml` at its root: project slug, embedding backend
(dim + secrets via `*_env`), Qdrant URL, source roots (live-watched vs version-stamped
static tiers), include/exclude globs, the chunker map, watcher, server, and optional
Bearer auth + structured logging. **Secrets are only ever environment-variable
references**, never inlined. See **`lore.yaml.sample`** for an annotated template.

## Extending

`loremaster` is a framework: build a domain-specific MCP by subclassing one `Extension`
ABC and registering it — `LoreServer.from_config(...).register_extension(...).run()` —
without forking the core. See **`loremaster/EXTENDING.md`** (the eleven seams) and
**`lorescribe/EXTENDING.md`** (writing chunkers / schema profiles).

## Development

```sh
uv sync --all-packages
uv run --frozen pytest -q
uv run --frozen mypy loremaster      # strict; run per package
uv run --frozen ruff check .
```

## License

[GPL-3.0-or-later](LICENSE). Copyright © the lore authors.
