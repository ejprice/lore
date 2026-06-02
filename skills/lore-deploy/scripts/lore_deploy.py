#!/usr/bin/env python3
"""lore-deploy verb dispatcher: idempotent on-demand lifecycle (A1.11).

One entrypoint for the four verbs — ``setup`` / ``start`` / ``stop`` /
``status`` — each idempotent and safe to re-run (the whole contract). The
heavy/strict steps delegate to the sibling scripts (``probe_embed.py``,
``ensure_collections.py``, ``merge_mcp_json.py``) so the logic lives in one
place per concern.

The container runs the SHARED image ``localhost/lore:latest`` with the project
identity supplied entirely at run time (``-v <project>:/workspace:ro`` +
``--env-file`` + ``-e LORE_CONFIG``). Collections + the SQLite manifest persist
on the host across stop/start, so ``start`` is a cheap delta-reconcile, never a
cold rebuild.

Unix philosophy: structured status line on stdout, loud (non-zero exit) on
failure. See ``../references/lifecycle.md`` for the per-verb spec and
``../references/server-interface.md`` for the not-yet-final server assumptions.

Most steps shell out to ``podman``/``python`` so this dispatcher itself needs
only the standard library; the steps that import loremaster (config parse,
collection ensure) are run with ``--python <interp>`` pointing at the loremaster
venv (the dispatcher resolves a sensible default).
"""

from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants (no hardcoded magic scattered through the logic).
# ---------------------------------------------------------------------------
IMAGE = "localhost/lore:latest"
SCRIPT_DIR = Path(__file__).resolve().parent
PROBE_SCRIPT = SCRIPT_DIR / "probe_embed.py"
ENSURE_SCRIPT = SCRIPT_DIR / "ensure_collections.py"
MERGE_SCRIPT = SCRIPT_DIR / "merge_mcp_json.py"

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
# Default secret env-file location (mirrors odoo-code's ~/docker/mcp/.env).
DEFAULT_ENV_FILE = Path.home() / "docker" / "mcp" / "lore.env"

_EXIT_OK = 0
_EXIT_ERROR = 2

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


def _loremaster_python() -> str:
    """Resolve an interpreter that can import loremaster (config parse, ensure step).

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


# ---------------------------------------------------------------------------
# Config parsing via the loremaster venv (one source of truth for the schema).
# ---------------------------------------------------------------------------
def _read_config_field(config_path: Path, expr: str) -> str:
    """Read a single field from a lore.yaml via the loremaster config model.

    ``expr`` is a Python expression over the loaded ``c`` (e.g.
    ``c.project.slug``). Returns the stringified value. Raises on a parse error
    so a malformed config fails loud.
    """
    code = (
        "import sys;from loremaster.config import load_config;"
        f"c=load_config({str(config_path)!r});print({expr})"
    )
    result = _run([_loremaster_python(), "-c", code], check=False, capture=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"failed to read {expr!r} from {config_path}: {result.stderr.strip()}"
        )
    return result.stdout.strip()


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

qdrant:
  url: http://127.0.0.1:16333
  api_key_env: QDRANT__SERVICE__API_KEY

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
    # Fail loud if the scaffold does not parse against the real model.
    _read_config_field(config_path, "c.project.slug")


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
def verb_setup(project: Path, env_file: Path) -> int:
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

    # 5. Ensure collections (STOP on dim mismatch; never auto-recreate).
    if (rc := _ensure_collections(config_path, env_file)) != _EXIT_OK:
        return rc

    # 6. Build the image if missing.
    if not _image_exists(IMAGE):
        print(f"setup: image {IMAGE} missing — build it from the lore workspace root "
              f"(podman build -t {IMAGE} -f Containerfile .) before continuing.", file=sys.stderr)
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


def verb_start(project: Path, env_file: Path) -> int:
    """``start`` — launch the container (delta-reconcile) + merge .mcp.json (idempotent).

    Three paths based on the container's current state and image currency:
    - RUNNING + current image  → no-op, re-merge .mcp.json (no reminder, nothing changed).
    - RUNNING + stale image    → stop + rm + relaunch, re-merge .mcp.json, print reminder.
    - NOT running              → standard launch path, re-merge .mcp.json, print reminder.
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
            print(f"start: {container_name} already running — no-op.")
            # Re-merge .mcp.json (cheap, idempotent) so wiring stays current even
            # after a reboot or out-of-band container restart — mirrors verb_setup's
            # already-provisioned no-op branch.
            _merge_mcp_from_config(project, slug, config_path)
            return _EXIT_OK
        else:
            # Container is running on a stale image (localhost/lore:latest was rebuilt).
            # podman restart reloads the SAME baked image — only stop+rm+run picks up
            # new code, so we perform the full recreate sequence.
            print(f"start: {container_name} is running a stale image — recreating.")
            _run(["podman", "stop", container_name], check=False)
            _run(["podman", "rm", container_name], check=False)
            _launch_container(project, config_path, env_file)
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

    # Pre-flight: embedder reachable + the collection exists (no silent cold-build on start).
    if (rc := _probe_embed(config_path, env_file)) != _EXIT_OK:
        return rc
    if (rc := _ensure_collections(config_path, env_file)) != _EXIT_OK:
        return rc

    _launch_container(project, config_path, env_file)
    port = _merge_mcp_from_config(project, slug, config_path)
    print(f"start: {container_name} launched (delta-reconcile on startup) on port {port}.")
    # Always remind the operator to reconnect after a fresh launch so the MCP client
    # picks up the live tool schemas from the newly-started server.
    print(_MCP_RECONNECT_REMINDER)
    return _EXIT_OK


def verb_stop(project: Path) -> int:
    """``stop`` — stop + remove the container (collections + manifest persist; idempotent)."""
    slug = project.name
    state = _container_state(f"lore-{slug}")
    if state is None:
        print(f"stop: lore-{slug} not running — no-op.")
        return _EXIT_OK
    _run(["podman", "stop", f"lore-{slug}"], check=False)
    _run(["podman", "rm", f"lore-{slug}"], check=False)
    print(f"stop: lore-{slug} stopped (collections + manifest preserved).")
    return _EXIT_OK


def verb_status(project: Path) -> int:
    """``status`` — running/stopped + index freshness from the manifest.

    For a running container, also reports whether it is on the current
    ``localhost/lore:latest`` image or is running stale code.
    """
    slug = project.name
    container_name = f"lore-{slug}"
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


def _ensure_collections(config_path: Path, env_file: Path) -> int:
    """Run ensure_collections.py under the loremaster venv + the env-file's secrets."""
    result = _run(
        ["env", *_env_file_kv(env_file), _loremaster_python(), str(ENSURE_SCRIPT),
         "--config", str(config_path)],
        check=False, capture=True,
    )
    sys.stderr.write(result.stderr)
    if result.returncode == _EXIT_OK:
        print("ensure: collections present at the configured dim.")
    return result.returncode


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

    Only used to hand secrets to the child probe/ensure processes — the values
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
        "--env-file", default=str(DEFAULT_ENV_FILE),
        help=f"Secrets env-file (default: {DEFAULT_ENV_FILE}).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Dispatch a verb. Pre-checks podman availability for the container verbs."""
    args = _build_parser().parse_args(argv)
    project = Path(args.project).resolve()
    env_file = Path(args.env_file)

    if not project.is_dir():
        print(f"lore_deploy: --project {project} is not a directory.", file=sys.stderr)
        return _EXIT_ERROR
    if shutil.which("podman") is None:
        print("lore_deploy: podman not found on PATH.", file=sys.stderr)
        return _EXIT_ERROR

    if args.verb == "setup":
        return verb_setup(project, env_file)
    if args.verb == "start":
        return verb_start(project, env_file)
    if args.verb == "stop":
        return verb_stop(project)
    return verb_status(project)


if __name__ == "__main__":
    sys.exit(main())
