"""Regression tests for the lore-deploy verb dispatcher's run invocation.

The deployed-by-hand pattern proved that a bare ``--userns=keep-id`` (no
``--user``), a missing ``HOME``, and a ``/state`` manifest mount make the
container run as UID 999 and write the manifest/graph to an ephemeral path the
host cold-index never sees — so ``search``/``index_status`` worked but the graph
tools were empty and a restart lost the manifest. These tests pin the verified
working invocation so that regression cannot recur silently.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import lore_deploy


def test_launch_container_uses_host_user_home_and_shared_manifest_mount(
    monkeypatch, tmp_path: Path
) -> None:
    """The run invocation must run as the host user, set HOME, and share the manifest dir.

    * ``--user <uid>:<gid>`` so (with keep-id) the container process maps 1:1 to
      the host user and the bind-mounted manifest dir is writable.
    * ``-e HOME=/home/lore`` so loremaster's ``Path.home()`` resolves to where the
      manifest + ``<slug>.graph.db`` are mounted.
    * the host manifest dir mounts to ``$HOME/.local/state/lore`` — NOT ``/state`` —
      so the container server reads the exact manifest + graph the host cold-index
      wrote (the graph tools depend on this).
    """
    captured: dict[str, list[str]] = {}
    monkeypatch.setattr(lore_deploy, "_run", lambda cmd, **kw: captured.setdefault("cmd", cmd))
    # No static roots → no /source mount; keeps this test about the user/home/manifest wiring.
    monkeypatch.setattr(lore_deploy, "_read_config_field", lambda *a, **k: "0")

    project = tmp_path / "demo_project"
    project.mkdir()
    lore_deploy._launch_container(project, project / "lore.yaml", tmp_path / "secrets.env")

    cmd = captured["cmd"]
    assert "--user" in cmd, "container must pin --user to the host uid:gid"
    assert f"{os.getuid()}:{os.getgid()}" in cmd, "must run as the host user (keep-id 1:1)"
    assert "HOME=/home/lore" in cmd, "HOME must point at the image's lore home"

    manifest_mounts = [c for c in cmd if c.endswith(":/home/lore/.local/state/lore")]
    assert manifest_mounts, "manifest dir must mount to $HOME/.local/state/lore"
    assert not any(c.endswith(":/state") for c in cmd), "the broken /state mount must be gone"


def test_start_when_already_running_still_rewires_mcp_json(
    monkeypatch, tmp_path: Path
) -> None:
    """``verb_start`` must write/refresh ``.mcp.json`` even when the container is already running.

    The bug: when ``_container_state`` returned ``"running"``, ``verb_start``
    short-circuited with a no-op print and returned ``_EXIT_OK`` BEFORE the
    ``_merge_mcp`` call — so a project whose ``.mcp.json`` was missing or stale
    was never wired after a reboot or after an out-of-band container restart.
    The desired behavior mirrors ``verb_setup``'s already-provisioned branch,
    which re-merges ``.mcp.json`` on its no-op path (lines 301-303 of
    lore_deploy.py).

    This test exercises the REAL ``_merge_mcp`` → real subprocess call →
    real ``.mcp.json`` write, so the assertion is on the written file, not on a
    mock interaction.  That makes it behavioral (not a tautology).

    Contract (from the spec, NOT reverse-engineered from verb_start's body):
    1. Returns _EXIT_OK (== 0).
    2. <project>/.mcp.json exists and contains the correct no-auth lore_<slug> entry.
    3. _launch_container is NOT called (already running must not relaunch).
    """
    # --- project slug and expected MCP entry shape ---
    # Slug is project.name.  No-auth entry shape is defined in the merge script's
    # spec: {"type": "http", "url": "http://127.0.0.1:<port>/mcp"} with NO "headers".
    # Port 9201 is the real DEFAULT_PORT_BASE in lore_deploy — used here as the
    # stub value that the config field reader would return from a real lore.yaml
    # (the production range is [9201, 9201+N]).  Named constant below; NOT magic.
    LORE_SERVER_PORT = 9201
    LORE_MOUNT_PATH = "/mcp"
    PROJECT_SLUG = "demoproj"
    EXPECTED_SERVER_KEY = f"lore_{PROJECT_SLUG}"
    EXPECTED_URL = f"http://127.0.0.1:{LORE_SERVER_PORT}{LORE_MOUNT_PATH}"

    # --- Arrange ---
    project = tmp_path / PROJECT_SLUG
    project.mkdir()
    # verb_start pre-flight: returns _EXIT_ERROR if lore.yaml is absent.
    # Contents are irrelevant — _read_config_field is stubbed below.
    (project / "lore.yaml").write_text("# stub lore config\n", encoding="utf-8")

    # Simulate the already-running container state (the bug's trigger condition).
    monkeypatch.setattr(lore_deploy, "_container_state", lambda name: "running")

    # Stub the config field reader so no subprocess into the loremaster venv runs.
    # Dispatches on the ``expr`` string as the real _read_config_field would.
    def _stub_read_config_field(config_path: Path, expr: str) -> str:
        if "port" in expr:
            return str(LORE_SERVER_PORT)  # must be int-parseable; same unit as server.port
        return LORE_MOUNT_PATH  # mount path must start with "/"

    monkeypatch.setattr(lore_deploy, "_read_config_field", _stub_read_config_field)

    # Record (do NOT call) _launch_container so we can assert it was NOT invoked.
    # The already-running path must never re-launch/recreate the container.
    launch_calls: list[tuple[Path, Path, Path]] = []

    def _recording_launch_container(proj: Path, config_path: Path, env_file: Path) -> None:
        launch_calls.append((proj, config_path, env_file))

    monkeypatch.setattr(lore_deploy, "_launch_container", _recording_launch_container)

    env_file = tmp_path / "secrets.env"
    # The env-file need not exist: verb_start only checks env_file.exists() on the
    # non-running code path (past the early-return bug site), never on the running path.

    # --- Act ---
    return_code = lore_deploy.verb_start(project, env_file)

    # --- Assert ---

    # 1. Return success.
    assert return_code == lore_deploy._EXIT_OK, (
        f"verb_start must return _EXIT_OK (0) when container is already running; "
        f"got {return_code}"
    )

    # 2. The .mcp.json was written with the correct no-auth entry.
    #    We assert on the REAL file produced by the REAL merge subprocess.
    mcp_json_path = project / ".mcp.json"
    assert mcp_json_path.exists(), (
        ".mcp.json must be written by verb_start even when the container is already running "
        "(the missing-wiring regression)"
    )
    mcp_document = json.loads(mcp_json_path.read_text(encoding="utf-8"))
    assert "mcpServers" in mcp_document, ".mcp.json must have a top-level mcpServers key"
    assert EXPECTED_SERVER_KEY in mcp_document["mcpServers"], (
        f"mcpServers must contain the {EXPECTED_SERVER_KEY!r} entry after start"
    )
    lore_entry = mcp_document["mcpServers"][EXPECTED_SERVER_KEY]

    # URL must be the exact no-auth localhost shape from the merge spec.
    assert lore_entry.get("url") == EXPECTED_URL, (
        f"lore entry URL must be {EXPECTED_URL!r} (no-auth local server); "
        f"got {lore_entry.get('url')!r}"
    )
    # No-auth default: "headers" must be absent (a Bearer ${UNSET_VAR} would
    # imply auth that isn't there and risk an unresolvable env-var expansion).
    assert "headers" not in lore_entry, (
        "no-auth deploy must not emit an Authorization header in .mcp.json; "
        "pass --auth-key-env explicitly to opt in"
    )
    # Sanity: the entry type must be "http" (not "stdio" or anything else).
    assert lore_entry.get("type") == "http", (
        f"lore entry type must be 'http'; got {lore_entry.get('type')!r}"
    )

    # 3. _launch_container was NOT called — already-running must not relaunch.
    assert launch_calls == [], (
        f"_launch_container must not be called when the container is already running; "
        f"was called {len(launch_calls)} time(s)"
    )
