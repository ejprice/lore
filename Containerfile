# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------
# lore — single shared image, N config-driven containers (one per project).
#
# The image bundles the three uv-workspace members (lorescribe, loresigil,
# loremaster) and runs the loremaster MCP server. A project supplies its
# identity entirely at RUN time: a read-only bind of the project tree at
# /workspace, an optional read-only snapshot of static tiers at /source,
# an env-file of secrets, and LORE_CONFIG pointing at the mounted lore.yaml.
# Never per-project images — see the run invocation at the bottom of this file.
#
# Base: python:3.14-slim. The whole dependency stack installs binary-only on
# CPython 3.14 (audited: pydantic-core cp314 wheel, qdrant-client, watchdog,
# tokenizers, mcp, sqlglot, langchain-text-splitters, defusedxml, pyyaml — zero
# source builds), so no compiler toolchain is needed in the image.
# ---------------------------------------------------------------------------
FROM python:3.14-slim

# curl is used by the container healthcheck to poll the MCP server's HTTP
# endpoint; it is the only apt package added (mirrors odoo-code's image).
RUN apt-get update -qq \
    && apt-get install -y -qq --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# uv drives the install: it resolves the workspace members against the pinned
# uv.lock so the container's dependency set is identical to the developer's.
RUN pip install --no-cache-dir uv

WORKDIR /app

# ---------------------------------------------------------------------------
# Install the three workspace members from the build context (NOT a host
# editable path — the image must be self-contained and reproducible).
#
# The workspace ROOT pyproject.toml + uv.lock are copied alongside the members:
# loremaster/pyproject.toml declares its intra-repo deps as
# `lorescribe = { workspace = true }` / `loresigil = { workspace = true }`, which
# uv can ONLY resolve when the install runs inside a uv workspace — i.e. with the
# root pyproject's `[tool.uv.workspace] members = [...]` present at the install
# CWD. Installing the members in isolation (no root) fails with
# "references a workspace ... but is not a workspace member". Copying the root +
# uv.lock makes the install workspace-aware and pins the exact locked dependency
# set (identical to the developer's `uv sync`).
#
# Layer ordering: metadata first so the heavy `uv pip install` layer caches
# across source-only edits. The shared modules' pinned tokenizer
# (loresigil/loresigil/data/voyage4_tokenizer.json, 2.2 MB) ships in the
# loresigil package — no runtime HuggingFace/network fetch.
# ---------------------------------------------------------------------------
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock        /app/uv.lock
COPY lorescribe/ /app/lorescribe/
COPY loresigil/  /app/loresigil/
COPY loremaster/ /app/loremaster/

# Install each member with --system into the image's interpreter, FROM the
# workspace root (WORKDIR /app holds the root pyproject) so `workspace = true`
# resolves. Order is shared-modules-before-consumer; uv resolves the closure
# either way, but it documents the dependency direction.
RUN uv pip install --system \
        ./lorescribe \
        ./loresigil \
        ./loremaster

# Run as a non-root, no-login service account. With `podman --userns=keep-id`
# this UID is remapped to the invoking host user so the :ro bind mounts at
# /workspace and /source remain readable. The SQLite manifest persists OUTSIDE
# the container on a host bind (see run invocation) so it survives stop/start.
RUN useradd -r -s /bin/false lore
USER lore

# The MCP server binds inside the container; with --network=host the port is
# the host port from lore.yaml's `server.port`. Documented for clarity only —
# --network=host ignores published ports.
EXPOSE 9201

# LORE_CONFIG is injected at run time and points at the bind-mounted lore.yaml.
# A sane default keeps the entrypoint declarative; the run invocation overrides
# it explicitly.
ENV LORE_CONFIG=/workspace/lore.yaml

# ---------------------------------------------------------------------------
# Entrypoint — the always-the-same MCP server process.
#
# `python -m loremaster.server` reads LORE_CONFIG, configures structured logging,
# runs the embedder probe-gate, and serves the FastMCP streamable-http app via
# uvicorn on config.server host/port/path (the heavy startup — probe-gate /
# reconcile / watcher — runs once per process, shared across MCP sessions).
# The batch indexer is a SEPARATE entrypoint — `python -m loremaster.index
# --config <lore.yaml>` — invoked by the skill's `setup` (cold index) and each
# `start` (delta-reconcile), independent of this CMD.
# ---------------------------------------------------------------------------
CMD ["python", "-m", "loremaster.server"]

# ---------------------------------------------------------------------------
# Build:
#   podman build -t localhost/lore:latest -f Containerfile .
# (run from the workspace root so the build context contains all three members.)
#
# Run (one container per project; never a per-project image):
#   podman run -d --name lore-<slug> \
#     --network=host \
#     --userns=keep-id --user $(id -u):$(id -g) -e HOME=/home/lore \
#     -v <project>:/workspace:ro \
#     [ -v <snapshot>:/source:ro ]   # only if lore.yaml declares a static root
#     -v ~/.local/state/lore:/home/lore/.local/state/lore \
#     --env-file <secrets.env> \
#     -e LORE_CONFIG=/workspace/lore.yaml \
#     localhost/lore:latest
#
#   --network=host    Qdrant is host-loopback-only (127.0.0.1:16333); the
#                     container reaches it (and the LAN TEI endpoint) only via
#                     the host network namespace. host.containers.internal does
#                     NOT work for Qdrant.
#   --userns=keep-id --user $(id -u):$(id -g) -e HOME=/home/lore
#                     run as the host uid:gid (keep-id maps it 1:1) so the
#                     bind-mounted state dir is WRITABLE, and pin $HOME to the
#                     image's lore home where loremaster reads/writes the manifest
#                     + <slug>.graph.db. Bare keep-id alone runs as the image's lore
#                     user (UID 999) → Permission denied on the bind. VERIFIED on
#                     the demand_intelligence + lore deploys.
#   -v <project>:/workspace:ro
#                     the live project tree, read-only. lore.yaml lives here.
#   -v <snapshot>:/source:ro
#                     static-tier snapshot dir (~/docker/mcp/lore-snapshot),
#                     read-only — only needed when lore.yaml declares static
#                     roots; omit for a bare single-live-tree project like
#                     demand_intelligence.
#   -v ~/.local/state/lore:/home/lore/.local/state/lore
#                     the SQLite manifest + <slug>.graph.db persist on the HOST so
#                     they survive stop/start (A1.11). Mounted EXACTLY at
#                     $HOME/.local/state/lore (HOME=/home/lore) where loremaster
#                     reads/writes them — so the host cold-index and the container
#                     server share one manifest+graph. (The old /state mount was a
#                     dead path the server never reads.)
#   --env-file        secrets only (LORE_TEI_KEY, QDRANT__SERVICE__API_KEY, and
#                     any LORE_<SLUG>_KEY when auth is enabled). Never inlined in
#                     lore.yaml — the config carries only *_env names.
#
# On SELinux hosts the binds need :Z (or :z for shared) — e.g.
#   -v <project>:/workspace:ro,Z
# This box runs AppArmor (per `podman info`), so :Z is harmless but unneeded;
# the odoo-code quadlet uses :ro,Z defensively. Add it if a deploy target
# enables SELinux.
# ---------------------------------------------------------------------------
