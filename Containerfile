# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------
# lore — single shared image, N config-driven containers (one per project).
#
# The image bundles every uv-workspace member (lorerunes, lorescribe, loresigil,
# loremaster) and runs the loremaster MCP server. A project supplies its
# identity entirely at RUN time: a read-only bind of the project tree at
# /workspace, an optional read-only snapshot of static tiers at /source,
# an env-file of secrets, and LORE_CONFIG pointing at the mounted lore.yaml.
# Never per-project images — see the run invocation at the bottom of this file.
#
# Base: python:3.14-slim. The whole dependency stack installs binary-only on
# CPython 3.14 (audited: pydantic-core cp314 wheel, numpy, scipy, scikit-learn,
# watchdog, tokenizers, mcp, sqlglot, langchain-text-splitters, defusedxml,
# pyyaml — zero source builds), so no compiler toolchain is needed in the image.
# ⚠ This list is PROSE beside code and nothing gates it — corrected 2026-07-28
# (found by scout-11ib-1): it still named `qdrant-client`, retired at `04879f7`,
# and omitted numpy/scipy/scikit-learn, adopted at `38c9774` and by far the most
# wheel-fragile members of the stack. Re-audit it whenever a dependency lands.
# ---------------------------------------------------------------------------
FROM python:3.14-slim

# git is the ONE external binary the shipped code execs — the capture_git_identity
# seam (loremaster/loremaster/index/snapshots.py), which powers the honesty line
# (finding #125) and every snapshot's git_ref (finding #131).
# loremaster/loremaster/shellout.py DERIVES that requirement from the shipped source,
# and the deploy skill's Layer 2 probe fails loud if a DERIVED binary goes missing
# from the image (see loremaster.shellout.required_binaries).

# curl is NOT derived and therefore NOT gated: the derived set only ever contains
# binaries the shipped PYTHON execs, and no shipped code execs curl. Keeping it is a
# deliberate, declared exemption — never a silent one.
# lore-ungated-binary: curl — kept for in-container debugging and a future healthcheck; no shipped code execs it, so no derived gate can cover it

# tini is the PID-1 INIT declared by the ENTRYPOINT below — it forwards signals
# (SIGTERM/SIGINT) to the server and reaps zombies, so `podman stop` shuts the
# process down gracefully instead of the 10s-then-SIGKILL a bare-Python PID 1 gets.
# Like curl it is NOT a binary the shipped Python execs, so it is NOT derived and
# no derived-binary gate covers it — a deliberate, declared exemption, never silent.
# lore-ungated-binary: tini — PID-1 init that forwards signals and reaps zombies for the server; no shipped code execs it, so no derived gate can cover it
RUN apt-get update -qq \
    && apt-get install -y -qq --no-install-recommends curl git tini \
    && rm -rf /var/lib/apt/lists/*

# uv drives the install: it resolves the workspace members against the pinned
# uv.lock so the container's dependency set is identical to the developer's.
RUN pip install --no-cache-dir uv

WORKDIR /app

# ---------------------------------------------------------------------------
# Install every workspace member from the build context (NOT a host
# editable path — the image must be self-contained and reproducible).
#
# The workspace ROOT pyproject.toml + uv.lock are copied alongside the members:
# a member that depends on a sibling declares it as `<sibling> = { workspace =
# true }` (stated as a shape, not an enumeration — the enumeration that used to
# sit here named two members and went stale the moment packet 42 added a
# fourth), which uv can ONLY resolve when the install runs inside a uv workspace
# — i.e. with the root pyproject's `[tool.uv.workspace] members = [...]` present
# at the install CWD. Installing the members in isolation (no root) fails with
# "references a workspace ... but is not a workspace member". Copying the root +
# uv.lock makes the install workspace-aware; `uv sync --locked` (below) then
# installs the EXACT locked dependency set — the developer's `uv sync`, byte for
# byte — and fails the build if the lock is stale.
#
# Layer ordering: metadata first so the heavy `uv sync` layer caches across
# source-only edits. The shared modules' pinned tokenizer
# (loresigil/loresigil/data/voyage4_tokenizer.json, 2.2 MB) ships in the
# loresigil package — no runtime HuggingFace/network fetch.
# ---------------------------------------------------------------------------
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock        /app/uv.lock
COPY lorerunes/  /app/lorerunes/
COPY lorescribe/ /app/lorescribe/
COPY loresigil/  /app/loresigil/
COPY loremaster/ /app/loremaster/

# `uv sync --locked` mirrors the developer's own `uv sync` EXACTLY: it installs
# the full LOCKED dependency closure (uv.lock) plus the workspace members and the
# dev group (pytest, pytest-asyncio, pytest-xdist, mypy, ruff, type stubs) into
# /app/.venv. Two reasons, one instrument:
#   1. FIDELITY (#141): the old `uv pip install ./members` resolved dependencies
#      FRESH from the index and DRIFTED from the lock (measured 2026-07-15:
#      mcp/starlette/uvicorn/sqlglot shipped NEWER than uv.lock — versions the
#      suite never tested). `--locked` FAILS the build if uv.lock is out of date,
#      so the image can never again silently diverge from the tested closure.
#   2. CONFORMANCE (#139 / packet 01a): baking the pinned test runner makes the
#      deployed image itself runnable by the in-image conformance suite — no
#      run-time dependency install, and conformance tests the LITERAL artifact.
# --all-packages installs every workspace member (loremaster depends on its
# siblings via `workspace = true`; this documents + guarantees ALL members are
# present, including any that no sibling declares a dependency on yet).
RUN uv sync --locked --all-packages

# The sync installs into /app/.venv; put it first on PATH so `python`, `pytest`
# and `python -m loremaster.{server,index}` all resolve to the locked interpreter.
ENV PATH="/app/.venv/bin:${PATH}"

# Run as a non-root, no-login service account. With `podman --userns=keep-id`
# this UID is remapped to the invoking host user so the :ro bind mounts at
# /workspace and /source remain readable. The SQLite manifest persists OUTSIDE
# the container on a host bind (see run invocation) so it survives stop/start.
RUN useradd -r -s /bin/false lore
USER lore

# No EXPOSE: the server binds 127.0.0.1:<server.port> from lore.yaml, and the
# containers run with --network=host, which ignores published/exposed ports. A
# hardcoded EXPOSE only made `podman ps` show the same `<n>/tcp` for EVERY
# container regardless of its real port (e.g. lore-lore serves 9202), falsely
# implying a port collision.

# LORE_CONFIG is injected at run time and points at the bind-mounted lore.yaml.
# A sane default keeps the entrypoint declarative; the run invocation overrides
# it explicitly.
ENV LORE_CONFIG=/workspace/lore.yaml

# The lore release version, BAKED at image-build time from the host's git state
# (`git describe --tags --always --dirty`) passed via `--build-arg LORE_VERSION`.
# The server's `_resolve_version` reads this env and advertises it as the MCP
# `serverInfo.version` (left unset, the SDK would advertise its OWN version). Placed
# AFTER the heavy `uv pip install` layer so bumping the version never busts the
# dependency cache. Defaults to `unknown` when the build-arg is omitted.
ARG LORE_VERSION=unknown
ENV LORE_VERSION=${LORE_VERSION}

# ---------------------------------------------------------------------------
# Entrypoint — tini (PID 1) wrapping the always-the-same MCP server process.
#
# ENTRYPOINT runs tini as PID 1; it execs the CMD below as its child, forwards
# signals to it (so `podman stop` is a graceful SIGTERM rather than a 10s wait
# then SIGKILL), and reaps any zombies. A bare-Python PID 1 does neither — this
# session hit exactly that (a wedged conmon on a graceless shutdown), which is
# why tini was added. tini is transparent to a command override, so the
# conformance run's `sh -c ...` still runs correctly — just as tini's child.
#
# `python -m loremaster.server` reads LORE_CONFIG, configures structured logging,
# runs the embedder probe-gate, and serves the FastMCP streamable-http app via
# uvicorn on config.server host/port/path (the heavy startup — probe-gate /
# reconcile / watcher — runs once per process, shared across MCP sessions).
# The batch indexer is a SEPARATE entrypoint — `python -m loremaster.index
# --config <lore.yaml>` — invoked by the skill's `setup` (cold index) and each
# `start` (delta-reconcile), independent of this CMD.
# ---------------------------------------------------------------------------
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/.venv/bin/python", "-m", "loremaster.server"]

# ---------------------------------------------------------------------------
# Build (bake the version from git so the server advertises it):
#   podman build --build-arg LORE_VERSION="$(git describe --tags --always --dirty)" \
#       -t localhost/lore:latest -f Containerfile .
# (run from the workspace root so the build context contains all three members.)
#
# Conformance (packet 01a, finding #139) — POST-BUILD, before deploying the image:
#   python skills/lore-deploy/scripts/lore_deploy.py conform                       # localhost/lore:latest
#   python skills/lore-deploy/scripts/lore_deploy.py conform --image localhost/lore:<tag>
# Runs the BAKED pytest inside the freshly-built image against this repo mounted :ro, so
# the run tests the ARTIFACT (the cake), not the dev-host source (the recipe). A provenance
# guard asserts the members import the baked code, not the mount. It is NOT on `start` (it
# adds ~3 min); see skills/lore-deploy/scripts/conformance_run.sh + conformance_provenance.py.
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
