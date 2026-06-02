"""Regression tests for the lore-deploy verb dispatcher's run invocation.

The deployed-by-hand pattern proved that a bare ``--userns=keep-id`` (no
``--user``), a missing ``HOME``, and a ``/state`` manifest mount make the
container run as UID 999 and write the manifest/graph to an ephemeral path the
host cold-index never sees — so ``search``/``index_status`` worked but the graph
tools were empty and a restart lost the manifest. These tests pin the verified
working invocation so that regression cannot recur silently.
"""

from __future__ import annotations

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
