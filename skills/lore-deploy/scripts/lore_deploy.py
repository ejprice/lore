#!/usr/bin/env python3
"""lore-deploy verb dispatcher: idempotent on-demand lifecycle (A1.11).

One entrypoint for the four verbs — ``setup`` / ``start`` / ``stop`` /
``status`` — each idempotent and safe to re-run (the whole contract). The
heavy/strict steps delegate to the sibling scripts (``probe_embed.py``,
``merge_mcp_json.py``) so the logic lives in one place per concern; the
SurrealDB store-reachability pre-flight is inline (a stdlib-only ``/health``
probe), since the deploy gates only on the store being REACHABLE — schema and
embedding-dimension ownership now live entirely in the loremaster server.

The container runs the SHARED image ``localhost/lore:latest`` with the project
identity supplied entirely at run time (``-v <project>:/workspace:ro`` +
``--env-file`` + ``-e LORE_CONFIG``). The SurrealDB store data + the SQLite
manifest persist on the host across stop/start, so ``start`` is a cheap
delta-reconcile, never a cold rebuild.

Unix philosophy: structured status line on stdout, loud (non-zero exit) on
failure. See ``../references/lifecycle.md`` for the per-verb spec and
``../references/server-interface.md`` for the not-yet-final server assumptions.

Most steps shell out to ``podman``/``python`` so this dispatcher itself needs
only the standard library; the step that imports loremaster (a schema-only
config parse) is run with ``--python <interp>`` pointing at the loremaster venv
(the dispatcher resolves a sensible default).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants (no hardcoded magic scattered through the logic).
# ---------------------------------------------------------------------------
IMAGE = "localhost/lore:latest"
SCRIPT_DIR = Path(__file__).resolve().parent
PROBE_SCRIPT = SCRIPT_DIR / "probe_embed.py"
MERGE_SCRIPT = SCRIPT_DIR / "merge_mcp_json.py"

# The lore workspace root (skills/lore-deploy/scripts -> skills/lore-deploy -> skills
# -> repo root) — where the uv-workspace pyproject.toml lives, so the shell-out
# derivation (see the ARTIFACT-gates block below) scans the SAME tree the image is
# built from.
REPO_ROOT = SCRIPT_DIR.parent.parent.parent

# The persistent SurrealDB backing-store container — the unified store since P8a
# (chunks, search, memory, the code graph and the task ledger all live in it).
# The deploy gates only on this container's REACHABILITY: it NEVER creates,
# recreates, or removes it, and never touches its data dir. start-if-stopped
# (reboot recovery — the box was rebooted and the container, restart policy
# "no", sits Exited) is the ONLY mutation this skill is permitted to make.
# Schema + embedding-dimension ownership — including the
# embedding-schema-fingerprint rebuild — belongs to the loremaster server.
SURREAL_CONTAINER_NAME = "lore-surreal"

MANIFEST_DIR = Path.home() / ".local" / "state" / "lore"
SNAPSHOT_ROOT = Path.home() / "docker" / "mcp" / "lore-snapshot"

# The image's non-root ``lore`` user HOME. loremaster writes the manifest +
# ``<slug>.graph.db`` under ``$HOME/.local/state/lore`` (Path.home()), so the host
# manifest dir must mount THERE — not ``/state`` — for the container server to read
# the same manifest + code-graph the host cold-index wrote.
CONTAINER_HOME = "/home/lore"
CONTAINER_STATE_DIR = f"{CONTAINER_HOME}/.local/state/lore"

# Free-port search for a fresh scaffold starts here (the plan's example port).
DEFAULT_PORT_BASE = 9201
# Per-slug secrets live here: ``~/docker/mcp/lore-secrets/<slug>.env`` (one file per
# project, NOT a single project-agnostic ``lore.env``). The old shared default did
# not exist on-host, so an unsupplied ``--env-file`` resolved to a missing file and
# ``podman run`` exited 125. The resolver below turns (project, maybe-explicit) into
# the concrete per-slug path.
LORE_SECRETS_DIR = Path.home() / "docker" / "mcp" / "lore-secrets"

_EXIT_OK = 0
_EXIT_ERROR = 2

# ---------------------------------------------------------------------------
# Port-probe / wait-for-bind constants.
#
# A "running" container is NOT the same as "accepting MCP connections" —
# loremaster's ASGI lifespan startup runs a boot-time delta-reconcile (walking
# + re-indexing changed files, subject to embedder 429 backoff) BEFORE uvicorn
# binds the port. The incident this closes: `status` reported healthy and
# `start` declared success purely from container state + the manifest file,
# while the real MCP endpoint refused connections for ~4 minutes.
# ---------------------------------------------------------------------------
_PROBE_TIMEOUT_S = 3.0
_DEFAULT_BIND_TIMEOUT_S = 600.0
_BIND_POLL_INTERVAL_S = 3.0
_BIND_PROGRESS_INTERVAL_S = 30.0

# ---------------------------------------------------------------------------
# SurrealDB store-reachability pre-flight (setup/start) constants.
#
# The gate is a single short ``GET /health`` against the store; on failure it
# may perform ONE bounded start-if-stopped reboot recovery (podman start), then
# re-poll /health for a short window while the node's storage engine comes ready.
# ---------------------------------------------------------------------------
_SURREAL_PROBE_TIMEOUT_S = 3.0
_SURREAL_START_BUDGET_S = 15.0
_SURREAL_START_POLL_INTERVAL_S = 1.0

# ---------------------------------------------------------------------------
# Workspace-honesty artifact-gate constants (findings #125/#131/#132).
# ---------------------------------------------------------------------------
_WORKSPACE_PROBE_TIMEOUT_S = 30.0

# A minimal, well-formed MCP `initialize` JSON-RPC request. The probe's success
# criterion doesn't care about the reply shape (any HTTP response — even a
# non-2xx one — proves the port is bound), but sending a genuine MCP request
# means a real MCP server gets a well-formed probe rather than a throwaway GET.
_MCP_INITIALIZE_BODY = json.dumps(
    {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "lore-deploy-probe", "version": "1.0"},
        },
    }
).encode("utf-8")

# Printed to stdout whenever a container is freshly launched or recreated on a new
# image so the operator knows to reconnect their MCP client (e.g. restart Claude Code
# via `claude --continue`) to load the refreshed tool schemas.
_MCP_RECONNECT_REMINDER = (
    "ACTION REQUIRED: reconnect the MCP session so the refreshed tool schemas load. "
    "Restart Claude Code (e.g. `claude --continue`) or re-attach your MCP client."
)


# ---------------------------------------------------------------------------
# Small process / podman helpers.
# ---------------------------------------------------------------------------
def _run(cmd: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess[str]:
    """Run a subprocess, returning the completed process (text mode)."""
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        capture_output=capture,
    )


def _container_state(name: str) -> str | None:
    """Return a container's state string (e.g. ``running``/``exited``) or ``None`` if absent."""
    result = _run(
        ["podman", "container", "inspect", "--format", "{{.State.Status}}", name],
        check=False,
        capture=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _image_exists(image: str) -> bool:
    """Return whether the named image is present locally."""
    return _run(["podman", "image", "exists", image], check=False).returncode == 0


def _container_image_id(name: str) -> str | None:
    """Return the image ID baked into the running container, or ``None`` on failure.

    Uses ``podman container inspect --format '{{.Image}}'`` which returns the
    full SHA256 digest of the image the container was started from.  Returns
    ``None`` whenever podman exits non-zero (container absent, podman not found,
    etc.) so callers can distinguish "unknown" from a real digest.
    """
    result = _run(
        ["podman", "container", "inspect", "--format", "{{.Image}}", name],
        check=False,
        capture=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _image_id(image: str) -> str | None:
    """Return the current image ID for a tag, or ``None`` on failure.

    Uses ``podman image inspect --format '{{.Id}}'`` which returns the SHA256
    digest of the locally-tagged image.  Returns ``None`` whenever podman exits
    non-zero (image absent, podman not found, etc.).
    """
    result = _run(
        ["podman", "image", "inspect", "--format", "{{.Id}}", image],
        check=False,
        capture=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _container_on_current_image(name: str, image: str) -> bool:
    """Fail-safe predicate: return False (stale) ONLY when both IDs are known AND differ.

    The fail-safe direction is True (treat as current) whenever either ID is
    undeterminable.  This prevents a spurious stop+rm+run when podman is
    unavailable, the container is absent, or the image tag doesn't exist yet —
    i.e. uncertainty must never trigger a destructive recreate.

    Returns False (stale → recreate) iff:
      - ``_container_image_id(name)`` is non-None, AND
      - ``_image_id(image)`` is non-None, AND
      - the two IDs differ.
    In every other case returns True (treat as current — no recreate).
    """
    running_id = _container_image_id(name)
    current_id = _image_id(image)
    # Both IDs must be determinable to conclude staleness.
    if running_id is None or current_id is None:
        return True  # undeterminable → treat as current (fail-safe)
    return running_id == current_id


def _free_port(base: int) -> int:
    """Return the first bindable TCP port at or above ``base`` on 127.0.0.1."""
    port = base
    while port < base + 1000:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("127.0.0.1", port))
                return port
            except OSError:
                port += 1
    raise RuntimeError(f"no free port found in [{base}, {base + 1000})")


def _probe_mcp_port(host: str, port: int, path: str, *, timeout_s: float = _PROBE_TIMEOUT_S) -> bool:
    """Return True iff ``(host, port, path)`` is bound and speaking HTTP right now.

    POSTs a minimal MCP ``initialize`` JSON-RPC request. Deliberately loose
    success criterion: ANY HTTP response — including a non-2xx status —
    proves the port is bound and serving, which is the only thing a caller
    needs to know (vs. connection-refused/timeout, meaning nothing is
    listening there yet — e.g. loremaster's boot-time delta-reconcile still
    holding the port unbound before uvicorn binds). Never raises; a transport
    failure just means "not yet".
    """
    url = f"http://{host}:{port}{path}"
    request = urllib.request.Request(
        url,
        data=_MCP_INITIALIZE_BODY,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s):
            return True
    except urllib.error.HTTPError:
        return True  # a real HTTP response, even an error one, proves the port is bound
    except OSError:
        return False  # connection refused / timed out / reset — nothing listening (yet)


def _wait_for_bind(
    host: str,
    port: int,
    path: str,
    *,
    timeout_s: float,
    poll_interval_s: float = _BIND_POLL_INTERVAL_S,
    progress_interval_s: float = _BIND_PROGRESS_INTERVAL_S,
    on_progress: Callable[[float], None] | None = None,
) -> bool:
    """Poll ``_probe_mcp_port`` until it accepts connections or ``timeout_s`` elapses.

    Returns True the moment a probe succeeds; False once the budget is
    exhausted with no bind ever observed. Calls ``on_progress(elapsed_s)``
    roughly every ``progress_interval_s`` while still waiting, so a caller can
    print a "still waiting" line without this helper owning stdout.
    """
    start = time.monotonic()
    last_progress = start
    while True:
        if _probe_mcp_port(host, port, path, timeout_s=min(poll_interval_s, _PROBE_TIMEOUT_S)):
            return True
        now = time.monotonic()
        elapsed = now - start
        if elapsed >= timeout_s:
            return False
        if on_progress is not None and (now - last_progress) >= progress_interval_s:
            on_progress(elapsed)
            last_progress = now
        time.sleep(poll_interval_s)


def _surreal_health_url(rpc_url: str) -> str:
    """Map a SurrealDB ``ws(s)://host:port/rpc`` RPC URL to its ``/health`` HTTP URL.

    SurrealDB serves the HTTP ``/health`` route on the SAME host:port as the
    WebSocket ``/rpc`` endpoint, so only the scheme and the path change:
    ``ws`` → ``http``, ``wss`` → ``https`` (any other scheme is left untouched),
    and the path becomes ``/health``. stdlib-only (``urllib.parse``).
    """
    parts = urllib.parse.urlsplit(rpc_url)
    scheme = {"ws": "http", "wss": "https"}.get(parts.scheme, parts.scheme)
    return urllib.parse.urlunsplit((scheme, parts.netloc, "/health", "", ""))


def _probe_surreal_health(health_url: str, *, timeout_s: float = _SURREAL_PROBE_TIMEOUT_S) -> bool:
    """Return True iff ``GET health_url`` answers HTTP 200 right now.

    SurrealDB's ``/health`` returns 200 only when the node is up and its storage
    engine is ready. So — unlike the MCP bind-probe, where ANY HTTP response
    proves the port is bound — this gate requires a clean 200: a non-2xx status
    or any transport failure (connection refused / reset / timeout) is False.
    Never raises; a failure just means "not reachable (yet)".
    """
    request = urllib.request.Request(health_url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            # bool(): urlopen's response is loosely typed, so ``.status == 200``
            # is inferred as Any; coerce to the declared bool return.
            return bool(response.status == 200)
    except urllib.error.HTTPError:
        return False  # a non-2xx /health means the node is not ready
    except OSError:
        return False  # connection refused / timed out / reset — nothing serving there


def _wait_for_surreal_health(
    health_url: str,
    *,
    timeout_s: float,
    poll_interval_s: float,
) -> bool:
    """Poll ``_probe_surreal_health`` until it answers 200 or ``timeout_s`` elapses.

    Used only after a reboot-recovery ``podman start lore-surreal`` to give the
    node a bounded window to bring its storage engine ready. Returns True the
    moment /health answers 200; False once the budget is exhausted.
    """
    start = time.monotonic()
    while True:
        if _probe_surreal_health(health_url):
            return True
        if time.monotonic() - start >= timeout_s:
            return False
        time.sleep(poll_interval_s)


def _loremaster_python() -> str:
    """Resolve an interpreter that can import loremaster (schema-only config parse).

    Preference order: an explicit ``LORE_PYTHON`` env override; the lore
    workspace ``.venv`` if discoverable next to the worktree; otherwise the
    current interpreter (the dispatcher may itself be run under the venv).
    """
    override = os.environ.get("LORE_PYTHON")
    if override:
        return override
    # The worktree/workspace .venv, relative to where the skill is typically run.
    for candidate in (
        Path.home() / "PycharmProjects" / "lore" / ".venv" / "bin" / "python",
    ):
        if candidate.exists():
            return str(candidate)
    return sys.executable


def _resolve_env_file(project: Path, explicit: str | None) -> Path:
    """Resolve the secrets env-file for ``project`` (per-slug unless overridden).

    An explicit ``--env-file`` (any non-None value) is honored verbatim — the
    operator may point at a one-off secrets file and it must pass through
    untouched. When unsupplied (``explicit is None``), the file resolves
    per-slug to ``~/docker/mcp/lore-secrets/<slug>.env`` where the slug is the
    project directory name. This is the single seam that turns
    (project, maybe-explicit) into the concrete env-file Path, called from
    :func:`main` once the project is known — never at argparse time, so an
    unsupplied flag (default ``None``) stays distinguishable from an explicit one.
    """
    if explicit is not None:
        # Honor an operator-supplied path verbatim — no per-slug rewriting.
        return Path(explicit)
    slug = project.name
    return LORE_SECRETS_DIR / f"{slug}.env"


# ---------------------------------------------------------------------------
# Config parsing via the loremaster venv (one source of truth for the schema).
# ---------------------------------------------------------------------------
def _schema_load_snippet(config_path: Path) -> str:
    """Return a Python snippet binding ``c`` to the schema-validated ``LoreConfig``.

    Schema-only by design: it constructs the model via ``LoreConfig.model_validate``
    (NOT :func:`load_config`), so it NEVER resolves a secret from the environment.
    Every consumer here reads config FIELD values — a slug, a port, or the *name*
    of a secret's env-var — never a resolved secret VALUE, so requiring
    ``ANTHROPIC_API_KEY`` to be exported just to read the server port (what
    ``load_config``'s EAGER resolution forced) was wrong: it broke
    ``setup`` / ``start`` / ``status`` on any host where that key is not exported.
    Secret presence is a boot concern (``load_config`` fails loud at server start,
    naming the variable), not a config-field-read concern.
    """
    return (
        "import yaml;from pathlib import Path;"
        "from loremaster.config import LoreConfig;"
        f"c=LoreConfig.model_validate(yaml.safe_load("
        f"Path({str(config_path)!r}).read_text(encoding='utf-8')))"
    )


def _read_config_field(config_path: Path, expr: str) -> str:
    """Read a single field VALUE from a lore.yaml via the loremaster config model.

    ``expr`` is a Python expression over the schema-validated ``c`` (e.g.
    ``c.project.slug``). Returns the stringified value. Validation is SCHEMA-ONLY
    (see :func:`_schema_load_snippet`): the helper reads field values, never a
    resolved secret, so it must not — and does not — require any secret env-var to
    be set. Raises ``RuntimeError`` on a parse/validation error so a malformed
    config fails loud.
    """
    code = f"{_schema_load_snippet(config_path)};print({expr})"
    result = _run([_loremaster_python(), "-c", code], check=False, capture=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"failed to read {expr!r} from {config_path}: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def _validate_config_schema(config_path: Path) -> None:
    """Validate a lore.yaml's SHAPE against the real ``LoreConfig`` — schema only.

    Runs ``LoreConfig.model_validate`` (NOT :func:`load_config`) in the loremaster
    venv (see :func:`_schema_load_snippet`), so the written template is checked for
    structural validity WITHOUT resolving any secret. This is deliberate and is the
    smallest honest scaffold check: the scaffold emits env-var *names* only (never a
    secret), so whether ``ANTHROPIC_API_KEY`` happens to be exported in the
    operator's shell at scaffold time is irrelevant to whether the emitted file is
    well-formed. Secret presence is a boot concern — ``setup`` checks the env-file
    separately and ``load_config`` resolves ``anthropic.api_key_env`` eagerly at
    server start (failing loud, naming the variable). Raises ``RuntimeError`` —
    naming the pydantic error — when the shape is invalid, so a bad scaffold fails
    loud.
    """
    result = _run(
        [_loremaster_python(), "-c", _schema_load_snippet(config_path)],
        check=False,
        capture=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"scaffolded {config_path} failed schema validation: {result.stderr.strip()}"
        )


def _read_server_block(config_path: Path) -> tuple[str, int, str]:
    """Read the ``server:`` block (host, port, path) a project's lore.yaml declares."""
    host = _read_config_field(config_path, "c.server.host")
    port = int(_read_config_field(config_path, "c.server.port"))
    path = _read_config_field(config_path, "c.server.path")
    return host, port, path


def _await_bind(
    container_name: str,
    host: str,
    port: int,
    path: str,
    *,
    timeout_s: float,
    no_wait: bool,
) -> int:
    """Wait for the MCP endpoint to accept connections, or fail loud.

    Every ``start`` path that ends with a running container calls this before
    declaring success — a "running" container can still be mid-boot
    delta-reconcile with the port unbound (the incident this closes). Skips
    the wait entirely when ``no_wait`` (fire-and-forget, operator's call). On
    timeout, prints a loud stderr message with the tail of ``podman logs`` and
    returns ``_EXIT_ERROR`` — the caller must not print an unqualified success
    line afterward.
    """
    url = f"http://{host}:{port}{path}"
    if no_wait:
        print(f"start: --no-wait set — not confirming {url} is accepting connections.")
        return _EXIT_OK

    def _progress(elapsed: float) -> None:
        print(
            f"start: still waiting for {container_name} to accept MCP connections at "
            f"{url} ({elapsed:.0f}s elapsed) — likely the boot-time delta-reconcile is "
            f"still holding the port unbound; continuing to poll."
        )

    print(f"start: waiting for {container_name} to accept MCP connections at {url}…")
    if _wait_for_bind(host, port, path, timeout_s=timeout_s, on_progress=_progress):
        print(f"start: {url} is accepting connections.")
        return _EXIT_OK

    tail = _run(["podman", "logs", "--tail", "5", container_name], check=False, capture=True)
    print(
        f"start: TIMEOUT — {container_name} did not accept MCP connections at {url} "
        f"within {timeout_s:.0f}s. Last `podman logs --tail 5 {container_name}`:\n"
        f"{tail.stdout}{tail.stderr}",
        file=sys.stderr,
    )
    return _EXIT_ERROR


# ---------------------------------------------------------------------------
# Scaffolding (setup only) — free port + .gitignore-seeded excludes.
# ---------------------------------------------------------------------------
def _gitignore_dir_names(project: Path) -> list[str]:
    """Extract directory-name excludes from the project .gitignore.

    Lines ending in ``/`` (or bare names that look like dirs) become
    ``exclude_dirs`` basenames; the walk prunes by basename. We keep only the
    final path segment (the walk prune is name-based) and skip negations/globs.
    """
    gitignore = project / ".gitignore"
    names: list[str] = []
    if not gitignore.exists():
        return names
    for raw in gitignore.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        if "*" in line or "?" in line:
            continue  # a glob, not a dir name → handled by exclude_globs
        name = line.rstrip("/").strip("/").split("/")[-1]
        if name and name not in names:
            names.append(name)
    return names


def _scaffold_lore_yaml(project: Path, config_path: Path) -> None:
    """Write a fresh lore.yaml for ``project`` (called only when absent).

    Seeds the slug from the directory name, a free server port, and
    ``exclude_dirs`` from the project .gitignore (plus the always-prune set).
    The include globs default to the common code/docs surface; the operator
    should review them for the project's real layout. Validated by parsing the
    written file through the real LoreConfig before returning.
    """
    slug = project.name
    port = _free_port(DEFAULT_PORT_BASE)
    always_prune = [".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"]
    excludes = always_prune + [n for n in _gitignore_dir_names(project) if n not in always_prune]
    excludes_yaml = "\n".join(f"  - {name}" for name in excludes)

    content = f"""# Auto-scaffolded by lore-deploy setup. Review the include globs for this
# project's real layout before the first index. Secrets are env-refs only.
schema_version: 1

project:
  slug: {slug}
  root: .

embedding:
  backend: tei
  base_url: http://localhost:8080         # CUSTOMIZE — your TEI endpoint (voyage-4-nano)
  endpoint: /embed
  model: voyageai/voyage-4-nano
  dim: 2048
  truncate: false
  max_input_tokens: 8192
  max_batch_texts: 32
  concurrency: 2
  connect_timeout_s: 5
  api_key_env: LORE_TEI_KEY
  tokenizer: voyage-4-nano

# Anthropic API (REQUIRED): api_key_env is the env-var NAME only, never the key
# itself. load_config resolves it EAGERLY at server start — export
# ANTHROPIC_API_KEY (e.g. in this project's lore-secrets env-file) before `start`,
# or boot fails loud naming the variable. yardstick_model is the token-calibration
# baseline (generation-anchored to claude-sonnet-5).
anthropic:
  api_key_env: ANTHROPIC_API_KEY
  yardstick_model: claude-sonnet-5

# Unified store (SurrealDB): chunks, search, memory, the code graph and the task
# ledger all live here; the database name defaults to the slug. Credentials are
# env-var NAMES only (SURREAL_USER / SURREAL_PASS). CUSTOMIZE the url to your
# lore-surreal RPC endpoint.
surreal:
  url: ws://127.0.0.1:18500/rpc           # CUSTOMIZE — your SurrealDB /rpc endpoint
  namespace: lore
  user_env: SURREAL_USER
  password_env: SURREAL_PASS

roots: []

include:
  - "**/*.py"
  - "**/*.md"
  - "**/*.sql"

exclude_dirs:
{excludes_yaml}

exclude_globs:
  - "**/*.parquet"
  - "**/*.min.js"
  - "**/*.min.css"
  - "uv.lock"

chunkers:
  ".py":  {{chunker: python_ast}}
  ".md":  {{chunker: markdown}}
  ".sql": {{chunker: sql, dialect: postgres}}

watcher:
  enabled: true
  observer: inotify
  debounce_ms: 1500
  reconcile_interval_s: 600

server:
  host: 127.0.0.1
  path: /mcp
  port: {port}
"""
    config_path.write_text(content, encoding="utf-8")
    # Fail loud if the scaffold does not parse against the real model. Schema-only
    # (LoreConfig.model_validate, NOT load_config): the scaffold emits env-var
    # *names*, never secrets, so validation must not require ANTHROPIC_API_KEY to
    # be exported — that eager key resolution is a boot concern (see setup's
    # env-file check + load_config's fail-fast at server start).
    _validate_config_schema(config_path)


# ---------------------------------------------------------------------------
# Run invocation.
# ---------------------------------------------------------------------------
def _launch_container(project: Path, config_path: Path, env_file: Path) -> None:
    """Launch the lore container for ``project`` (the proven host pattern).

    Runs as the host ``uid:gid`` (with ``--userns=keep-id`` that maps 1:1, so the
    bind-mounted manifest dir is writable) and sets ``HOME`` to the image's lore
    home, so loremaster's manifest + code-graph land in the mounted state dir and
    survive stop/start. Adds the ``/source`` snapshot bind only when the config
    declares a ``static`` root (a bare single-live-tree project does not need it).
    """
    slug = project.name
    cmd = [
        "podman", "run", "-d", "--name", f"lore-{slug}",
        "--network=host",
        "--userns=keep-id",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "-e", f"HOME={CONTAINER_HOME}",
        "-v", f"{project}:/workspace:ro",
        "-v", f"{MANIFEST_DIR}:{CONTAINER_STATE_DIR}",
        "--env-file", str(env_file),
        "-e", "LORE_CONFIG=/workspace/lore.yaml",
    ]
    # Only a STATIC root needs the read-only snapshot mount (live roots are served
    # straight from /workspace). Count static roots specifically — a live-only
    # project has roots but no snapshot to mount.
    static_root_count = _read_config_field(
        config_path, "sum(1 for r in c.roots if r.watch == 'static')"
    )
    if static_root_count not in ("", "0") and SNAPSHOT_ROOT.exists():
        cmd += ["-v", f"{SNAPSHOT_ROOT}:/source:ro"]
    cmd.append(IMAGE)
    _run(cmd)


# ---------------------------------------------------------------------------
# Verbs.
# ---------------------------------------------------------------------------
def verb_setup(project: Path, env_file: Path) -> int:  # noqa: PLR0911 - P8e reworks this skill
    """``setup`` — idempotent one-time provisioning (expensive parts no-op on re-run)."""
    config_path = project / "lore.yaml"
    slug = project.name

    # 1. Detect an existing deployment → no-op the expensive parts.
    already = config_path.exists() and (MANIFEST_DIR / f"{slug}.db").exists()
    if already:
        print(f"setup: {slug} already provisioned (config + manifest present) — no-op.")
        # Still re-merge the .mcp.json (cheap, idempotent) so wiring is current.
        _merge_mcp_from_config(project, slug, config_path)
        return _EXIT_OK

    # 2. Scaffold lore.yaml (only if absent).
    if not config_path.exists():
        _scaffold_lore_yaml(project, config_path)
        print(f"setup: scaffolded {config_path} — REVIEW its include globs.")

    # 3. Verify env-file present.
    if not env_file.exists():
        print(f"setup: secrets env-file {env_file} not found; create it first.", file=sys.stderr)
        return _EXIT_ERROR

    # 4. Hard-probe /embed (STOP on unreachable / wrong dim).
    if (rc := _probe_embed(config_path, env_file)) != _EXIT_OK:
        return rc

    # 5. Pre-flight the unified SurrealDB store (STOP if unreachable). The skill
    #    gates only on store REACHABILITY; schema + dim ownership (including the
    #    rebuild-on-fingerprint-change) lives in the loremaster server.
    if (rc := _probe_surreal(config_path)) != _EXIT_OK:
        return rc

    # 6. Build the image if missing.
    if not _image_exists(IMAGE):
        print(f"setup: image {IMAGE} missing — build it from the lore workspace root "
              f"(podman build --build-arg LORE_VERSION=\"$(git describe --tags --always --dirty)\" "
              f"-t {IMAGE} -f Containerfile .) before continuing.", file=sys.stderr)
        return _EXIT_ERROR

    # 7. Cold-index (the expensive step, paid once).
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    print(f"setup: cold-indexing {slug} (this is the one expensive step)…")
    cold = _run(
        [_loremaster_python(), "-m", "loremaster.index", "--config", str(config_path)],
        check=False,
        capture=True,
    )
    print(cold.stdout.strip())
    if cold.returncode != 0:
        print(f"setup: cold index reported failures:\n{cold.stderr.strip()}", file=sys.stderr)
        return _EXIT_ERROR

    # 8. Merge .mcp.json.
    _merge_mcp_from_config(project, slug, config_path)
    print(f"setup: {slug} provisioned. Run `start` to launch the server.")
    return _EXIT_OK


def verb_start(  # noqa: PLR0911, PLR0912, PLR0915 - P8e reworks this skill
    project: Path,
    env_file: Path,
    *,
    bind_timeout_s: float = _DEFAULT_BIND_TIMEOUT_S,
    no_wait: bool = False,
) -> int:
    """``start`` — launch the container (delta-reconcile) + merge .mcp.json (idempotent).

    Three paths based on the container's current state and image currency:
    - RUNNING + current image  → no-op, re-merge .mcp.json (no reminder, nothing changed).
    - RUNNING + stale image    → stop + rm + relaunch, re-merge .mcp.json, print reminder.
    - NOT running              → standard launch path, re-merge .mcp.json, print reminder.

    Every path that ends with a running container additionally waits for the
    MCP port to actually ACCEPT connections before declaring success (see
    ``_await_bind``) — a "running" container can still be mid-boot
    delta-reconcile with the port unbound. ``bind_timeout_s``/``no_wait`` are
    the ``--bind-timeout``/``--no-wait`` CLI knobs.

    Every one of those same three paths then runs the ARTIFACT gates
    (``_gate_artifact`` / ``_probe_artifact`` — findings #125/#131/#132) before declaring
    success: the required binaries must be present in the container AND the served honesty
    line must actually be alive for every git-backed watched root. A runtime gate is an
    invariant only over code it actually RUNS, so this is wired into every path that ends
    with a running container, not documented as a should-run-this smoke step. The gates run
    against the MCP endpoint, so ``_gate_artifact`` SKIPS them (loudly, on stdout) whenever
    ``--no-wait`` meant the endpoint was never confirmed up — gating a socket we ourselves
    declined to wait for can only fail, and fails blaming the image. When the endpoint WAS
    independently confirmed (the already-running fast path), ``--no-wait`` had no effect and
    the gates still run: "do not wait" is not "do not check".
    """
    config_path = project / "lore.yaml"
    slug = project.name
    container_name = f"lore-{slug}"
    if not config_path.exists():
        print(f"start: no {config_path}; run `setup` first.", file=sys.stderr)
        return _EXIT_ERROR

    state = _container_state(container_name)
    if state == "running":
        if _container_on_current_image(container_name, IMAGE):
            # Container is running on the current image — no recreate needed.
            # Probe FIRST and only enter the wait loop if not yet accepting —
            # the common case (already running + already bound) stays a fast no-op.
            host, port, mount = _read_server_block(config_path)
            url = f"http://{host}:{port}{mount}"
            if _probe_mcp_port(host, port, mount, timeout_s=_PROBE_TIMEOUT_S):
                print(f"start: {container_name} already running — no-op.")
                # The endpoint ANSWERED: --no-wait declined nothing, so the gates run.
                endpoint_confirmed = True
            else:
                print(
                    f"start: {container_name} already running but {url} is not yet "
                    f"accepting connections — waiting for bind."
                )
                if (rc := _await_bind(
                    container_name, host, port, mount,
                    timeout_s=bind_timeout_s, no_wait=no_wait,
                )) != _EXIT_OK:
                    return rc
                endpoint_confirmed = not no_wait
            # The artifact gates (findings #125/#131/#132): the container is up and
            # accepting connections, so prove the honesty line is actually alive in
            # THIS image before declaring success.
            if (rc := _gate_artifact(
                container_name, host, port, mount,
                endpoint_confirmed=endpoint_confirmed,
            )) != _EXIT_OK:
                return rc
            # Re-merge .mcp.json (cheap, idempotent) so wiring stays current even
            # after a reboot or out-of-band container restart — mirrors verb_setup's
            # already-provisioned no-op branch.
            _merge_mcp_from_config(project, slug, config_path)
            return _EXIT_OK
        else:
            # Container is running on a stale image (localhost/lore:latest was rebuilt).
            # podman restart reloads the SAME baked image — only stop+rm+run picks up
            # new code, so we perform the full recreate sequence.
            #
            # OUTAGE GUARD (validate BEFORE teardown): a stale-but-serving container
            # beats a dead one. Verify EVERY launch precondition (image present,
            # env-file present) FIRST and bail with _EXIT_ERROR — leaving the running
            # container UNTOUCHED — if any fails. Only after the preconditions are
            # known good do we stop + rm + relaunch. A guard placed AFTER the stop/rm
            # cannot prevent the outage, so the ORDER here is load-bearing.
            if not _image_exists(IMAGE):
                print(
                    f"start: image {IMAGE} missing; refusing to recreate "
                    f"{container_name} (leaving the running container untouched). "
                    f"Run `setup` (which builds it).",
                    file=sys.stderr,
                )
                return _EXIT_ERROR
            if not env_file.exists():
                print(
                    f"start: secrets env-file {env_file} not found; refusing to "
                    f"recreate {container_name} (leaving the running container "
                    f"untouched).",
                    file=sys.stderr,
                )
                return _EXIT_ERROR
            # The embedder + the SurrealDB store are launch preconditions too: a
            # relaunched server refuses to come up if `/embed` or the store is
            # unreachable (its startup probe gate). Validating them BEFORE teardown
            # keeps the stale-but-serving container alive when a relaunch would fail
            # anyway — same outage-guard logic as the image/env-file checks above,
            # same order the not-running launch path uses (embed then store).
            if (rc := _probe_embed(config_path, env_file)) != _EXIT_OK:
                return rc
            if (rc := _probe_surreal(config_path)) != _EXIT_OK:
                return rc

            print(f"start: {container_name} is running a stale image — recreating.")
            _run(["podman", "stop", container_name], check=False)
            _run(["podman", "rm", container_name], check=False)
            # A podman run failure must degrade gracefully (loud on stderr, _EXIT_ERROR)
            # rather than propagate a raw CalledProcessError up to the dispatcher —
            # the old container is already gone, so an uncaught raise is the worst case.
            try:
                _launch_container(project, config_path, env_file)
            except subprocess.CalledProcessError as error:
                print(
                    f"start: relaunch of {container_name} failed "
                    f"(podman exit {error.returncode}); the stale container was "
                    f"already removed — inspect podman logs and retry `start`.",
                    file=sys.stderr,
                )
                return _EXIT_ERROR
            host, port, mount = _read_server_block(config_path)
            if (rc := _await_bind(
                container_name, host, port, mount,
                timeout_s=bind_timeout_s, no_wait=no_wait,
            )) != _EXIT_OK:
                return rc
            if (rc := _gate_artifact(
                container_name, host, port, mount, endpoint_confirmed=not no_wait,
            )) != _EXIT_OK:
                return rc
            _merge_mcp_from_config(project, slug, config_path)
            print(_MCP_RECONNECT_REMINDER)
            return _EXIT_OK

    if state is not None:  # exists but not running (e.g. exited) — remove the stale one.
        _run(["podman", "rm", "-f", container_name], check=False)

    if not _image_exists(IMAGE):
        print(f"start: image {IMAGE} missing; run `setup` (which builds it).", file=sys.stderr)
        return _EXIT_ERROR
    if not env_file.exists():
        print(f"start: secrets env-file {env_file} not found.", file=sys.stderr)
        return _EXIT_ERROR

    # Pre-flight: embedder reachable + the unified SurrealDB store reachable.
    # Schema + dim ownership (including rebuild-on-fingerprint-change) lives in
    # the server; the deploy gates only on store REACHABILITY (surreal /health).
    if (rc := _probe_embed(config_path, env_file)) != _EXIT_OK:
        return rc
    if (rc := _probe_surreal(config_path)) != _EXIT_OK:
        return rc

    _launch_container(project, config_path, env_file)
    host, port, mount = _read_server_block(config_path)
    if (rc := _await_bind(
        container_name, host, port, mount,
        timeout_s=bind_timeout_s, no_wait=no_wait,
    )) != _EXIT_OK:
        return rc
    if (rc := _gate_artifact(
        container_name, host, port, mount, endpoint_confirmed=not no_wait,
    )) != _EXIT_OK:
        return rc
    merged_port = _merge_mcp_from_config(project, slug, config_path)
    print(f"start: {container_name} launched (delta-reconcile on startup) on port {merged_port}.")
    # Always remind the operator to reconnect after a fresh launch so the MCP client
    # picks up the live tool schemas from the newly-started server.
    print(_MCP_RECONNECT_REMINDER)
    return _EXIT_OK


def verb_stop(project: Path) -> int:
    """``stop`` — stop + remove the container (store data + manifest persist; idempotent)."""
    slug = project.name
    state = _container_state(f"lore-{slug}")
    if state is None:
        print(f"stop: lore-{slug} not running — no-op.")
        return _EXIT_OK
    _run(["podman", "stop", f"lore-{slug}"], check=False)
    _run(["podman", "rm", f"lore-{slug}"], check=False)
    print(f"stop: lore-{slug} stopped (store data + manifest preserved).")
    return _EXIT_OK


def verb_status(project: Path) -> int:
    """``status`` — running/stopped + index freshness from the manifest.

    For a running container, also reports whether it is on the current
    ``localhost/lore:latest`` image or is running stale code, AND probes the
    live MCP port — "running" is container state, not proof the server is
    actually accepting connections (loremaster's boot-time delta-reconcile can
    hold the port unbound for minutes after the container starts). A stopped
    container skips the probe (nothing to probe).
    """
    slug = project.name
    container_name = f"lore-{slug}"
    config_path = project / "lore.yaml"
    state = _container_state(container_name)
    manifest = MANIFEST_DIR / f"{slug}.db"
    running = state == "running"
    print(f"status: {container_name} container = {state or 'absent'}")
    if running:
        # Report image currency so the operator can tell whether a `start` is needed
        # to pick up a rebuilt localhost/lore:latest.
        if _container_on_current_image(container_name, IMAGE):
            print(f"status: {container_name} image: current")
        else:
            print(
                f"status: {container_name} image: STALE — newer {IMAGE} exists; "
                f"run `start` to recreate"
            )
    if manifest.exists():
        counts = _manifest_counts(manifest)
        print(f"status: manifest {manifest} → {counts}")
    else:
        print(f"status: no manifest at {manifest} (not yet set up).")
    if running:
        if config_path.exists():
            try:
                host, port, mount = _read_server_block(config_path)
            except RuntimeError as error:
                print(
                    f"status: could not read the server block from {config_path} to "
                    f"probe the MCP endpoint: {error}",
                    file=sys.stderr,
                )
            else:
                url = f"http://{host}:{port}{mount}"
                if _probe_mcp_port(host, port, mount, timeout_s=_PROBE_TIMEOUT_S):
                    print(f"status: mcp endpoint {url} = ACCEPTING")
                else:
                    print(
                        f"status: mcp endpoint {url} = NOT ACCEPTING (container "
                        f"running — likely boot delta-reconcile still holding the "
                        f"port unbound; re-check shortly)"
                    )
        print("status: query the MCP index_status() tool for live freshness "
              "(see server-interface.md — the live path lands with the server build).")
    return _EXIT_OK


# ---------------------------------------------------------------------------
# Step delegators.
# ---------------------------------------------------------------------------
def _probe_embed(config_path: Path, env_file: Path) -> int:
    """Run probe_embed.py with the config's embedding params under the env-file's secrets."""
    base_url = _read_config_field(config_path, "c.embedding.base_url")
    endpoint = _read_config_field(config_path, "c.embedding.endpoint")
    api_key_env = _read_config_field(config_path, "c.embedding.api_key_env")
    dim = _read_config_field(config_path, "c.embedding.dim")
    result = _run(
        ["env", *_env_file_kv(env_file), sys.executable, str(PROBE_SCRIPT),
         "--base-url", base_url, "--endpoint", endpoint,
         "--api-key-env", api_key_env, "--expect-dim", dim],
        check=False, capture=True,
    )
    if result.returncode != _EXIT_OK:
        sys.stderr.write(result.stderr)
        return result.returncode
    print(f"probe: /embed OK, dim {result.stdout.strip()}.")
    return _EXIT_OK


def _probe_surreal(config_path: Path) -> int:
    """Pre-flight the unified SurrealDB store: it must answer ``/health`` before we launch.

    The store is the persistent ``lore-surreal`` container (SurrealDB, RocksDB
    data bind-mounted on the host). This gate confirms REACHABILITY only —
    schema and embedding-dimension ownership (including the
    embedding-schema-fingerprint rebuild) lives in the loremaster server, not in
    this skill, so the skill never creates, recreates, or removes the store
    container and never touches its data dir.

    Reads ``surreal.url`` (a ``ws(s)://host:port/rpc`` endpoint) from the config
    and probes the sibling ``http(s)://host:port/health`` route (SurrealDB serves
    HTTP on the same port as the WebSocket RPC). On a clean ``GET /health`` → 200
    it returns :data:`_EXIT_OK`. Otherwise it attempts a single
    **reboot-recovery**: if a container named ``lore-surreal`` exists but is not
    running (its restart policy is ``no``, so a host reboot leaves it Exited), it
    runs ``podman start lore-surreal`` and re-polls ``/health`` for a bounded
    budget. Still unreachable — or no such container to start — returns
    :data:`_EXIT_ERROR` with a loud stderr remediation naming both the URL and
    the container. No secret is needed (an unauthenticated ``GET /health``), so —
    unlike the retired collection-ensure step — this delegator takes no env-file.
    """
    rpc_url = _read_config_field(config_path, "c.surreal.url")
    health_url = _surreal_health_url(rpc_url)

    if _probe_surreal_health(health_url):
        print("probe: surreal /health OK.")
        return _EXIT_OK

    # Not answering. The ONLY mutation allowed is start-if-stopped: a container
    # that exists but sits Exited (e.g. after a host reboot). A running-but-sick
    # node or an absent container is not something this gate may recreate.
    state = _container_state(SURREAL_CONTAINER_NAME)
    if state is not None and state != "running":
        print(
            f"probe: surreal /health not answering and {SURREAL_CONTAINER_NAME} is "
            f"{state} — starting it (reboot recovery)…"
        )
        _run(["podman", "start", SURREAL_CONTAINER_NAME], check=False)
        if _wait_for_surreal_health(
            health_url,
            timeout_s=_SURREAL_START_BUDGET_S,
            poll_interval_s=_SURREAL_START_POLL_INTERVAL_S,
        ):
            print(f"probe: {SURREAL_CONTAINER_NAME} auto-started; surreal /health OK.")
            return _EXIT_OK

    print(
        f"probe: SurrealDB store unreachable at {health_url} (from surreal.url "
        f"{rpc_url!r}). The unified store must be serving before setup/start. Start "
        f"it with `podman start {SURREAL_CONTAINER_NAME}` — this skill never creates, "
        f"recreates, or removes that container or its data dir; if the container does "
        f"not exist, provision it out-of-band first.",
        file=sys.stderr,
    )
    return _EXIT_ERROR


# ---------------------------------------------------------------------------
# The ARTIFACT gates (findings #125 / #131 / #132).
#
# The repo-local suites prove the honesty line is COMPUTED and SERVED correctly.
# Neither can see the environment the image actually runs in: the deployed image
# had no ``git`` binary, so the correct code served ``git_branch: null`` — and
# every snapshot's ``git_ref`` was silently ``None`` — while every test on a
# git-having host stayed green. These two probes gate the CAKE, not the recipe.
#
# Layer 2: every binary the shipped code can exec is present in the container.
#   The set is DERIVED (loremaster.shellout.required_binaries), never a list
#   someone must remember to update.
# Layer 3: for every root lore_index() SERVES, if that root's tree carries a
#   ``.git`` then its ``git_branch`` must be non-null. This is the only layer
#   that can see a git that is present but REFUSING (dubious-ownership exit 128,
#   #132) — layer 2 would be green over it.
#
# Both assert RELATIVE facts and run against the RUNNING container.
# ---------------------------------------------------------------------------
def required_container_binaries(repo_root: Path | None = None) -> list[str]:
    """The external binaries the image MUST carry, derived from the shipped source.

    Delegates to the ONE derivation (``loremaster.shellout.required_binaries``) through
    the loremaster interpreter — this dispatcher stays stdlib-only, and there is no
    second scanner to drift (ONE IMPLEMENTATION, repo standing law, finding #102).
    """
    root = REPO_ROOT if repo_root is None else repo_root
    snippet = (
        "import json, sys\n"
        "from pathlib import Path\n"
        "from loremaster.shellout import required_binaries\n"
        "print(json.dumps(sorted(required_binaries(Path(sys.argv[1])))))\n"
    )
    result = _run(
        [_loremaster_python(), "-c", snippet, str(root)], check=False, capture=True
    )
    if result.returncode != _EXIT_OK:
        raise RuntimeError(
            f"could not derive the required-binary set from {root}: {result.stderr.strip()}"
        )
    return [str(binary) for binary in json.loads(result.stdout.strip())]


def _exec_in_container(
    container_name: str, argv: list[str]
) -> subprocess.CompletedProcess[str]:
    """Run ``argv`` INSIDE the container — the one container-exec seam both probes use.

    The predicates below are about the container's filesystem and PATH, never the host's:
    the served root path (``/workspace``) does not exist here, so a host-side check would
    find nothing, skip itself, and report success over a dead feature.
    """
    return _run(["podman", "exec", container_name, *argv], check=False, capture=True)


def _probe_container_binaries(container_name: str) -> int:
    """Layer 2 — every DERIVED binary must exist in the running container."""
    try:
        required = required_container_binaries()
    except RuntimeError as error:
        print(
            f"probe: cannot derive the binaries {container_name} must carry: {error}. "
            f"Refusing to deploy on a required set the scan will not vouch for — an "
            f"unknown set is not an empty one (findings #125/#131).",
            file=sys.stderr,
        )
        return _EXIT_ERROR
    missing = [
        binary
        for binary in required
        if _exec_in_container(
            container_name, ["sh", "-c", f"command -v {binary} >/dev/null 2>&1"]
        ).returncode
        != _EXIT_OK
    ]
    if missing:
        print(
            f"probe: container {container_name} is MISSING binaries the shipped code "
            f"execs: {', '.join(missing)}. The image must install them (Containerfile) — "
            f"without them the git-derived fields (lore_index()'s watched-root branch, "
            f"every snapshot's git_ref) are a silent null in production "
            f"(findings #125/#131).",
            file=sys.stderr,
        )
        return _EXIT_ERROR
    if not required:
        print(
            "probe: container binaries OK — the shipped code execs no external binary, so "
            "there is nothing to require of the image. (An empty set the derivation VOUCHED "
            "for; the causes that would make it a lie — no modules scanned, or a spawn site "
            "it cannot read — both raise, and are handled above.)"
        )
        return _EXIT_OK
    print(f"probe: container binaries OK ({', '.join(required)}).")
    return _EXIT_OK


class _EndpointUnreachable(RuntimeError):
    """The MCP endpoint did not answer at all.

    A DIFFERENT world from "the image predates the honesty line", and it must never wear
    that diagnosis: the cure for a mid-boot server is to wait, and the cure for an old image
    is a 10-minute rebuild. One message for both sends half the readers to fix a thing that
    was never broken (audit R1 — the mechanism that made DEFECT-1 misdiagnose).
    """


def _sse_payload(raw: str) -> dict[str, Any]:
    """The JSON object carried by an SSE ``data:`` line (FastMCP's streamable transport)."""
    for line in raw.splitlines():
        if line.startswith("data: "):
            parsed: dict[str, Any] = json.loads(line[len("data: ") :])
            return parsed
    return {}


def _served_workspace_roots(host: str, port: int, path: str) -> list[dict[str, Any]] | None:
    """The watched roots the RUNNING server SERVES from ``lore_index()``.

    Returns the served rows, or ``None`` when a LIVE server's response carries no
    ``workspace`` section at all (a container running an image that predates the honesty
    line). ``None`` is NOT an empty list: "the field is missing" must never read as "there
    is nothing to check" — and it is NOT "the endpoint did not answer" either, which raises
    :class:`_EndpointUnreachable` instead. Three causes, three outcomes.
    """
    url = f"http://{host}:{port}{path}"
    session_id: str | None = None

    def _post(body: dict[str, Any]) -> dict[str, Any]:
        nonlocal session_id
        request = urllib.request.Request(  # noqa: S310 - fixed http scheme, localhost
            url, data=json.dumps(body).encode("utf-8"), method="POST"
        )
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json, text/event-stream")
        if session_id is not None:
            request.add_header("mcp-session-id", session_id)
        with urllib.request.urlopen(  # noqa: S310
            request, timeout=_WORKSPACE_PROBE_TIMEOUT_S
        ) as response:
            served_session = response.headers.get("mcp-session-id")
            if served_session:
                session_id = served_session
            raw = response.read().decode("utf-8")
        return _sse_payload(raw)

    try:
        _post(
            {
                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "lore-deploy-probe", "version": "1.0"},
                },
            }
        )
        _post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        answer = _post(
            {
                "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": "lore_index", "arguments": {}},
            }
        )
    except (urllib.error.URLError, OSError, ValueError) as error:
        raise _EndpointUnreachable(str(error)) from error

    structured = answer.get("result", {}).get("structuredContent")
    if not isinstance(structured, dict):
        return None
    workspace = structured.get("workspace")
    if not isinstance(workspace, dict):
        return None
    roots = workspace.get("roots")
    if not isinstance(roots, list):
        return None
    return [root for root in roots if isinstance(root, dict)]


def _probe_workspace_honesty(container_name: str, host: str, port: int, path: str) -> int:
    """Layer 3 — a served root whose tree carries a ``.git`` must name its branch.

    The RELATIVE fact: ``.git`` present ⇒ ``git_branch`` non-null. A project whose tree is
    not a git checkout legitimately has no branch, and a flat "the branch is not null"
    gate would false-fail it (commit c06c3ac: entry checks assert relative facts).

    ``.git`` is a FILE in a linked git WORKTREE and a DIRECTORY in a normal checkout — and
    worktrees are the entire point of #125 — so the predicate is "exists", never "is a
    directory".
    """
    try:
        roots = _served_workspace_roots(host, port, path)
    except _EndpointUnreachable as error:
        print(
            f"probe: the MCP endpoint http://{host}:{port}{path} could not be reached "
            f"({error}) — lore_index() never answered, so nothing is known about what "
            f"{container_name} serves. This is NOT a verdict on the image: a just-launched "
            f"server holds the port unbound through its startup reconcile (~150s). Wait for "
            f"the bind (raise --bind-timeout), or read `podman logs {container_name}`.",
            file=sys.stderr,
        )
        return _EXIT_ERROR
    if roots is None:
        print(
            f"probe: lore_index() on {container_name} ANSWERED, and served NO workspace "
            f"section — the container is running an image that predates the honesty line. "
            f"Rebuild the image and recreate the container (finding #125).",
            file=sys.stderr,
        )
        return _EXIT_ERROR

    dishonest: list[str] = []
    stranded: dict[str, str] = {}
    for root in roots:
        root_path = str(root.get("path", ""))
        if not root_path:
            continue
        carries_git = _exec_in_container(
            container_name, ["sh", "-c", 'test -e "$1/.git"', "_", root_path]
        ).returncode == _EXIT_OK
        if not carries_git or root.get("git_branch") is not None:
            continue
        gitdir = _unreachable_worktree_gitdir(container_name, root_path)
        if gitdir is None:
            dishonest.append(root_path)
        else:
            stranded[root_path] = gitdir

    if stranded:
        print(
            f"probe: {container_name} serves a NULL git_branch for linked git WORKTREE "
            f"root(s) whose gitdir is OUTSIDE the mount: "
            f"{', '.join(f'{root} -> {gitdir}' for root, gitdir in stranded.items())}. A "
            f"worktree's .git is a FILE naming an absolute host path inside the PARENT "
            f"repo's .git/worktrees/ — and only the worktree itself is bind-mounted, so that "
            f"path does not exist in the container, git exits 128, and the branch is null. "
            f"Git is present and the tree is readable; the image and the uid mapping are "
            f"not at fault. Cures: bind-mount the parent repo's gitdir alongside the "
            f"worktree, point GIT_DIR at it, or `git worktree repair` a checkout that "
            f"resolves. Deploying lore against a worktree is finding #134 (packets 17/23).",
            file=sys.stderr,
        )
    if dishonest:
        print(
            f"probe: {container_name} serves a NULL git_branch for watched root(s) that "
            f"ARE git trees: {', '.join(dishonest)}. The honesty line is dead in the "
            f"deployed image — either the git binary is missing, or git refuses the tree "
            f"(dubious ownership: run the container with --userns=keep-id --user $(id -u), "
            f"finding #132). Findings #125/#131.",
            file=sys.stderr,
        )
    if stranded or dishonest:
        return _EXIT_ERROR
    print(f"probe: workspace honesty OK ({len(roots)} watched root(s) served).")
    return _EXIT_OK


def _unreachable_worktree_gitdir(container_name: str, root_path: str) -> str | None:
    """The gitdir a linked worktree's ``.git`` FILE names, when it is NOT in the container.

    ``None`` when the root is a normal checkout (``.git`` is a directory), or when it is a
    worktree whose gitdir DOES resolve inside the mount — a healthy git tree, whose null
    branch means what it has always meant (a missing or refusing git). The predicate keys on
    the gitdir being UNREACHABLE, never on ``.git`` being a FILE: keying on the shape would
    prescribe the worktree cures to a worktree that is already fine, which is the wrong
    diagnosis wearing the right word.
    """
    read = _exec_in_container(
        container_name, ["sh", "-c", 'cat "$1/.git" 2>/dev/null || true', "_", root_path]
    )
    for line in read.stdout.splitlines():
        if not line.startswith("gitdir:"):
            continue
        gitdir = line.split(":", 1)[1].strip()
        if not gitdir:
            continue
        reachable = _exec_in_container(
            container_name, ["sh", "-c", 'test -e "$1"', "_", gitdir]
        ).returncode == _EXIT_OK
        return None if reachable else gitdir
    return None


def _gate_artifact(
    container_name: str, host: str, port: int, path: str, *, endpoint_confirmed: bool
) -> int:
    """The artifact gates, run ONLY against an endpoint we actually confirmed is up.

    ``--no-wait`` is the operator declining to confirm the bind (fire-and-forget). Layer 3
    reads what the SERVER SERVED — it HTTP-POSTs that very endpoint — so running it after
    declining to wait is a gate pointed at a socket we ourselves guaranteed would refuse:
    it can only fail, and it fails blaming the image ("predates the honesty line"). That is
    the regression this closes; ``--no-wait`` was documented, wired, and DEAD.

    A skipped gate is ANNOUNCED, never silently dropped: an operator who sees the deploy's
    success line must not believe the artifact was checked when it was not.

    Note what is NOT skipped: when the endpoint IS confirmed up (the already-running path,
    where the port probe answers before ``_await_bind`` is ever reached), ``--no-wait`` had
    no effect and both gates run. "Do not wait" is not "do not check" — turning the flag
    into a global off-switch for the #125/#131 instrument would re-open the hole this packet
    exists to close, for everyone who habitually passes it.
    """
    if endpoint_confirmed:
        return _probe_artifact(container_name, host, port, path)
    print(
        f"start: --no-wait set — the MCP endpoint was never confirmed, so the artifact "
        f"gates (required container binaries, served honesty line) were SKIPPED for "
        f"{container_name}. The image is UNVERIFIED: re-run `start` without --no-wait "
        f"once the server is up to gate it (findings #125/#131)."
    )
    return _EXIT_OK


def _probe_artifact(container_name: str, host: str, port: int, path: str) -> int:
    """Both artifact gates, in cause-localising order (binary present, then feature alive).

    Wired into every ``verb_start`` path that ends with a running container — a runtime
    gate is an invariant only over code it actually RUNS (repo standing law).
    """
    if (result := _probe_container_binaries(container_name)) != _EXIT_OK:
        return result
    return _probe_workspace_honesty(container_name, host, port, path)


def _merge_mcp(project: Path, slug: str, port: int, mount_path: str) -> None:
    """Run merge_mcp_json.py against the project .mcp.json."""
    _run(
        [sys.executable, str(MERGE_SCRIPT), "--mcp-json", str(project / ".mcp.json"),
         "--slug", slug, "--port", str(port), "--path", mount_path],
        check=False,
    )


def _merge_mcp_from_config(project: Path, slug: str, config_path: Path) -> int:
    """Read the server port + mount path from the config, then merge the .mcp.json entry.

    Wraps the read-port / read-mount / :func:`_merge_mcp` triple that both
    ``setup`` and ``start`` run on every code path (provisioned no-op, fresh
    provision, already-running no-op, fresh launch). Keeps the wiring step in one
    place so the no-auth localhost entry shape stays identical across all callers.
    Returns the resolved port so a caller can report it without re-reading config.
    """
    port = _read_config_field(config_path, "c.server.port")
    mount = _read_config_field(config_path, "c.server.path")
    _merge_mcp(project, slug, int(port), mount)
    return int(port)


def _env_file_kv(env_file: Path) -> list[str]:
    """Read a KEY=VALUE env-file into ``KEY=VALUE`` args for ``env`` (secrets stay out of argv logs).

    Only used to hand secrets to the child embed-probe process — the values
    are read from the file, never from this script's own argv.
    """
    pairs: list[str] = []
    if not env_file.exists():
        return pairs
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        pairs.append(line)
    return pairs


def _manifest_counts(manifest: Path) -> str:
    """Summarise the manifest's per-state file counts (read-only, safe when stopped)."""
    import sqlite3

    try:
        connection = sqlite3.connect(f"file:{manifest}?mode=ro", uri=True)
        try:
            rows = connection.execute(
                "SELECT state, COUNT(*) FROM files GROUP BY state"
            ).fetchall()
        finally:
            connection.close()
    except sqlite3.Error as error:
        return f"(unreadable: {error})"
    if not rows:
        return "no files indexed yet"
    return ", ".join(f"{state}={count}" for state, count in sorted(rows))


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    """Build the top-level verb dispatcher parser."""
    parser = argparse.ArgumentParser(
        prog="lore_deploy",
        description="Idempotent on-demand lifecycle for a project's lore RAG MCP server.",
    )
    parser.add_argument("verb", choices=("setup", "start", "stop", "status"))
    parser.add_argument(
        "--project", required=True,
        help="Absolute path to the project directory (its name is the slug).",
    )
    parser.add_argument(
        "--env-file", default=None,
        help=(
            "Secrets env-file. Defaults per-slug to "
            "~/docker/mcp/lore-secrets/<slug>.env when omitted; an explicit value "
            "is honored verbatim."
        ),
    )
    parser.add_argument(
        "--bind-timeout", type=float, default=_DEFAULT_BIND_TIMEOUT_S,
        help=(
            "`start` only: seconds to wait for the MCP port to accept connections "
            f"after launching/recreating/confirming the container (default "
            f"{_DEFAULT_BIND_TIMEOUT_S:.0f}s). Ignored by setup/stop/status."
        ),
    )
    parser.add_argument(
        "--no-wait", action="store_true",
        help=(
            "`start` only: skip waiting for the MCP port to accept connections "
            "(fire-and-forget). Ignored by setup/stop/status."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Dispatch a verb. Pre-checks podman availability for the container verbs."""
    args = _build_parser().parse_args(argv)
    project = Path(args.project).resolve()
    # Resolve the env-file AFTER the project is known so an unsupplied --env-file
    # (default None) resolves per-slug; an explicit value passes through verbatim.
    env_file = _resolve_env_file(project, args.env_file)

    if not project.is_dir():
        print(f"lore_deploy: --project {project} is not a directory.", file=sys.stderr)
        return _EXIT_ERROR
    if shutil.which("podman") is None:
        print("lore_deploy: podman not found on PATH.", file=sys.stderr)
        return _EXIT_ERROR

    if args.verb == "setup":
        return verb_setup(project, env_file)
    if args.verb == "start":
        return verb_start(
            project, env_file, bind_timeout_s=args.bind_timeout, no_wait=args.no_wait,
        )
    if args.verb == "stop":
        return verb_stop(project)
    return verb_status(project)


if __name__ == "__main__":
    sys.exit(main())
