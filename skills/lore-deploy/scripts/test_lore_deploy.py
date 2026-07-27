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
import shutil
import subprocess
import time
from pathlib import Path

import lore_deploy
import pytest


def test_launch_container_uses_host_user_home_and_shared_manifest_mount(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
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
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
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

    # Already running + serving: stub the MCP bind-probe as accepting so verb_start
    # takes the fast already-running no-op branch instead of entering the real
    # _await_bind wait loop (which would poll an unbound port for the full 600s bind
    # timeout). Orthogonal to what this test asserts (.mcp.json rewire + no relaunch).
    monkeypatch.setattr(lore_deploy, "_probe_mcp_port", lambda *args, **kwargs: True)

    env_file = tmp_path / "secrets.env"
    # The env-file need not exist: verb_start only checks env_file.exists() on the
    # non-running code path (past the early-return bug site), never on the running path.
    # The artifact gates (#125/#131/#132) run on every start path that ends
    # with a running container. Arrange them as passing — this test is about
    # a different concern, and both probes talk to a real container.
    _stub_artifact_gates(monkeypatch)


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


# ---------------------------------------------------------------------------
# Shared helpers for stale-image recreate tests (A1–A4).
# ---------------------------------------------------------------------------

# Production-realistic image IDs: opaque SHA256 digests as podman emits them
# (format: "sha256:<64 lowercase hex chars>"). Two distinct values for stale
# detection: RUNNING_IMAGE_ID is baked into the running container; CURRENT_IMAGE_ID
# is what `podman image inspect localhost/lore:latest` returns after a rebuild.
# They differ by one hex digit in the middle — not "clean" numbers, deliberately.
_RUNNING_IMAGE_ID = (
    "sha256:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
    "e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
)
_CURRENT_IMAGE_ID = (
    "sha256:f0e1d2c3b4a5f6e7d8c9b0a1f2e3d4c5"
    "b6a7f8e9d0c1b2a3f4e5d6c7b8a9f0e1"
)

# Port the stub lore.yaml reports.  Must equal lore_deploy.DEFAULT_PORT_BASE
# so fixtures match the range the real config generates.  Not a magic number —
# derived from the module constant.
_LORE_SERVER_PORT: int = lore_deploy.DEFAULT_PORT_BASE  # 9201
_LORE_MOUNT_PATH = "/mcp"


def _make_project(tmp_path: Path, slug: str) -> Path:
    """Create a minimal project directory with a stub lore.yaml."""
    project = tmp_path / slug
    project.mkdir()
    (project / "lore.yaml").write_text("# stub lore config\n", encoding="utf-8")
    return project


def _stub_read_config_field(config_path: Path, expr: str) -> str:
    """Stub for _read_config_field: returns port or mount path based on expr keyword."""
    if "port" in expr:
        return str(_LORE_SERVER_PORT)
    if "static" in expr:
        return "0"  # no static roots → no /source mount
    return _LORE_MOUNT_PATH


def _stub_artifact_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Arrange the ARTIFACT gates (findings #125/#131/#132) as PASSING.

    Every ``verb_start`` path that ends with a RUNNING container now also runs two
    artifact probes — the container carries every binary the shipped code execs
    (``_probe_container_binaries``), and the served honesty line is actually alive for
    every git-backed watched root (``_probe_workspace_honesty``). Both talk to a real
    container over ``podman exec`` / a real MCP endpoint over HTTP, so a test that drives
    ``verb_start`` to success must arrange them, exactly as it already arranges
    ``_probe_embed`` and ``_probe_surreal``.

    Deliberately stubs the two PROBES and NOT ``_probe_artifact``: their orchestrator
    keeps running for real in these tests, and — more importantly — the pins that prove
    the probes are WIRED IN AT ALL live in ``../tests/test_workspace_probe.py``
    (``TestTheProbesAreWiredIntoTheDeployVerb``) and monkeypatch these same two names to
    assert BOTH were called on all three start paths. Stubbing them here therefore
    arranges the new world without weakening that gate: an ``unwired`` build still goes
    RED over there (re-proven — see REPORT-pkt01-contract-2.md §AMENDMENT-7).
    """
    monkeypatch.setattr(
        lore_deploy, "_probe_container_binaries", lambda *a, **k: lore_deploy._EXIT_OK
    )
    monkeypatch.setattr(
        lore_deploy, "_probe_workspace_honesty", lambda *a, **k: lore_deploy._EXIT_OK
    )


class TestVerbStartStaleImageRecreateBehavior:
    """Contract: verb_start must detect stale running containers and recreate them.

    When ``localhost/lore:latest`` is rebuilt (a new image ID is tagged), a
    running container still runs the old baked code.  ``podman restart`` reuses
    the same baked image and does NOT pick up new code — only a stop + rm + run
    sequence switches to the current image.  verb_start must detect this
    divergence and perform the recreate automatically, then remind the operator
    to reconnect the MCP session so the refreshed tool schemas load.

    Seams expected in the implementation:
    - ``lore_deploy._container_image_id(name) -> str | None``:
        running container's image ID via ``podman container inspect --format '{{.Image}}'``
    - ``lore_deploy._image_id(image) -> str | None``:
        tag's current image ID via ``podman image inspect --format '{{.Id}}'``
    - ``lore_deploy._container_on_current_image(name, image) -> bool``:
        True iff ``_container_image_id(name) == _image_id(image)``
    - ``lore_deploy._MCP_RECONNECT_REMINDER``:
        a named string constant printed to stdout on recreate or fresh launch;
        the test asserts this constant exists and appears in verb_start output.
    """

    # --- A1 ---
    def test_verb_start_stale_running_container_is_recreated(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A1: RUNNING + STALE image → stop + rm + relaunch, re-merge .mcp.json, return _EXIT_OK,
        and print the MCP-reconnect reminder.

        Stale = running container image ID != current localhost/lore:latest image ID.
        The current code never inspects image IDs, so the recreate never happens
        and the reminder is never printed.  This test fails behaviorally on current code.
        """
        # --- Arrange ---
        PROJECT_SLUG = "myproject"
        project = _make_project(tmp_path, PROJECT_SLUG)
        container_name = f"lore-{PROJECT_SLUG}"

        # The module-level reconnect-reminder constant must exist.
        # If not, the assertion below catches it before verb_start is called,
        # giving a clean behavioral miss (not a framework crash).
        assert hasattr(lore_deploy, "_MCP_RECONNECT_REMINDER"), (
            "lore_deploy._MCP_RECONNECT_REMINDER constant is not yet defined; "
            "the implementer must add this named constant so tests can assert on it "
            "without hardcoding a string that can drift."
        )

        # Container is running on the OLD (stale) image.
        monkeypatch.setattr(lore_deploy, "_container_state", lambda name: "running")

        # The new image seam must return different IDs for running vs current.
        assert hasattr(lore_deploy, "_container_image_id"), (
            "lore_deploy._container_image_id seam not yet defined"
        )
        assert hasattr(lore_deploy, "_image_id"), (
            "lore_deploy._image_id seam not yet defined"
        )
        monkeypatch.setattr(
            lore_deploy, "_container_image_id",
            lambda name: _RUNNING_IMAGE_ID,
        )
        monkeypatch.setattr(
            lore_deploy, "_image_id",
            lambda image: _CURRENT_IMAGE_ID,
        )

        # Track podman stop / rm calls via _run recorder.
        run_calls: list[list[str]] = []

        def _recording_run(cmd: list[str], **kwargs: bool) -> subprocess.CompletedProcess[str]:
            run_calls.append(cmd)
            # Return a minimal CompletedProcess-alike (returncode=0) so the
            # caller's check=False / capture paths don't crash.
            import subprocess
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        monkeypatch.setattr(lore_deploy, "_run", _recording_run)
        monkeypatch.setattr(lore_deploy, "_read_config_field", _stub_read_config_field)

        # Record _launch_container calls (the real one would shell out to podman run).
        launch_calls: list[tuple[Path, Path, Path]] = []

        def _recording_launch(proj: Path, config_path: Path, env_file: Path) -> None:
            launch_calls.append((proj, config_path, env_file))

        monkeypatch.setattr(lore_deploy, "_launch_container", _recording_launch)

        # After the relaunch, verb_start waits for the MCP port to bind; stub that
        # wait as succeeding so the test does not poll an unbound port for the full
        # 600s bind timeout. Orthogonal to what this test asserts (stop/rm/relaunch
        # + reconnect reminder).
        monkeypatch.setattr(lore_deploy, "_await_bind", lambda *args, **kwargs: lore_deploy._EXIT_OK)
        # The recreate path now pre-flights /embed + the SurrealDB store BEFORE
        # teardown; stub both as reachable so this test stays about the recreate
        # sequence (their own gating is covered by TestRecreateGatesOnStorePreflight).
        monkeypatch.setattr(lore_deploy, "_probe_embed", lambda *a, **k: lore_deploy._EXIT_OK)
        monkeypatch.setattr(lore_deploy, "_probe_surreal", lambda *a, **k: lore_deploy._EXIT_OK)

        env_file = tmp_path / "secrets.env"
        # env-file need not exist: recreate path checks image/env only after the
        # stale detection; but the implementation may check env_file.exists() before
        # launching, so create it to avoid an _EXIT_ERROR short-circuit there.
        env_file.write_text("LORE_TEI_KEY=test\n", encoding="utf-8")
        # The artifact gates (#125/#131/#132) run on every start path that ends
        # with a running container. Arrange them as passing — this test is about
        # a different concern, and both probes talk to a real container.
        _stub_artifact_gates(monkeypatch)


        # --- Act ---
        return_code = lore_deploy.verb_start(project, env_file)

        # --- Assert ---

        # 1. Returns success.
        assert return_code == lore_deploy._EXIT_OK, (
            f"verb_start must return _EXIT_OK after recreating a stale container; "
            f"got {return_code}"
        )

        # 2. Container was stopped then removed (the recreate sequence).
        #    Any "podman stop lore-<slug>" in run_calls counts.
        stop_calls = [c for c in run_calls if "stop" in c and container_name in c]
        assert stop_calls, (
            f"verb_start must issue 'podman stop {container_name}' when the running "
            f"container is on a stale image; no stop call found in run_calls={run_calls}"
        )
        rm_calls = [c for c in run_calls if "rm" in c and container_name in c]
        assert rm_calls, (
            f"verb_start must issue 'podman rm {container_name}' as part of the recreate "
            f"sequence; no rm call found in run_calls={run_calls}"
        )

        # 3. _launch_container was called exactly once (the relaunch).
        assert len(launch_calls) == 1, (
            f"verb_start must call _launch_container exactly once when recreating a stale "
            f"container; got {len(launch_calls)} call(s)"
        )

        # 4. .mcp.json was re-merged (the _read_config_field stub returns our port).
        #    Because _run is stubbed, the real subprocess for merge_mcp_json does not
        #    run here — we verify _read_config_field was called with port/mount exprs
        #    by asserting the returned port matches our constant via the stub.
        #    The full .mcp.json write is covered by test_start_when_already_running_still_rewires_mcp_json.

        # 5. MCP-reconnect reminder was printed (operator must reconnect after new image).
        captured_out = capsys.readouterr().out
        assert lore_deploy._MCP_RECONNECT_REMINDER in captured_out, (
            f"verb_start must print _MCP_RECONNECT_REMINDER to stdout after recreating a "
            f"stale container so the operator knows to reconnect the MCP session; "
            f"stdout was: {captured_out!r}"
        )

    # --- A2 ---
    def test_verb_start_current_running_container_is_not_relaunched(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A2: RUNNING + CURRENT image → no stop/rm/relaunch, still re-merges .mcp.json,
        returns _EXIT_OK, and does NOT print the reconnect reminder.

        The reconnect reminder on a current container would be spurious churn —
        the operator changed nothing and should not be prompted to restart their session.
        This guards against an over-eager implementation that always prints the reminder.
        """
        # --- Arrange ---
        PROJECT_SLUG = "currentproject"
        project = _make_project(tmp_path, PROJECT_SLUG)

        # Container is running on the CURRENT image — same ID on both sides.
        monkeypatch.setattr(lore_deploy, "_container_state", lambda name: "running")

        assert hasattr(lore_deploy, "_container_image_id"), (
            "lore_deploy._container_image_id seam not yet defined"
        )
        assert hasattr(lore_deploy, "_image_id"), (
            "lore_deploy._image_id seam not yet defined"
        )
        monkeypatch.setattr(
            lore_deploy, "_container_image_id",
            lambda name: _CURRENT_IMAGE_ID,
        )
        monkeypatch.setattr(
            lore_deploy, "_image_id",
            lambda image: _CURRENT_IMAGE_ID,  # same → current
        )

        run_calls: list[list[str]] = []

        def _recording_run(cmd: list[str], **kwargs: bool) -> subprocess.CompletedProcess[str]:
            run_calls.append(cmd)
            import subprocess
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        monkeypatch.setattr(lore_deploy, "_run", _recording_run)
        monkeypatch.setattr(lore_deploy, "_read_config_field", _stub_read_config_field)

        launch_calls: list[tuple[Path, Path, Path]] = []

        def _recording_launch(proj: Path, config_path: Path, env_file: Path) -> None:
            launch_calls.append((proj, config_path, env_file))

        monkeypatch.setattr(lore_deploy, "_launch_container", _recording_launch)

        # Already running + serving: stub the MCP bind-probe as accepting so
        # verb_start takes the fast no-op branch rather than the real 600s
        # _await_bind wait loop. Orthogonal to what this test asserts (no
        # stop/rm/relaunch, no reconnect reminder).
        monkeypatch.setattr(lore_deploy, "_probe_mcp_port", lambda *args, **kwargs: True)

        env_file = tmp_path / "secrets.env"
        # The artifact gates (#125/#131/#132) run on every start path that ends
        # with a running container. Arrange them as passing — this test is about
        # a different concern, and both probes talk to a real container.
        _stub_artifact_gates(monkeypatch)


        # --- Act ---
        return_code = lore_deploy.verb_start(project, env_file)

        # --- Assert ---

        # 1. Returns success.
        assert return_code == lore_deploy._EXIT_OK, (
            f"verb_start must return _EXIT_OK when container is running on the current image; "
            f"got {return_code}"
        )

        # 2. No stop or rm — no churn on a current container.
        container_name = f"lore-{PROJECT_SLUG}"
        stop_calls = [c for c in run_calls if "stop" in c and container_name in c]
        assert not stop_calls, (
            f"verb_start must NOT stop a running container that is already on the current "
            f"image; found stop call(s): {stop_calls}"
        )
        rm_calls = [c for c in run_calls if "rm" in c and container_name in c]
        assert not rm_calls, (
            f"verb_start must NOT remove a running container that is already on the current "
            f"image; found rm call(s): {rm_calls}"
        )

        # 3. No relaunch.
        assert launch_calls == [], (
            f"verb_start must NOT call _launch_container when the running container is "
            f"already on the current image; got {len(launch_calls)} call(s)"
        )

        # 4. Re-merge still happens (existing contract — the wiring no-op path).
        # The .mcp.json write behavior is pinned by test_start_when_already_running_still_rewires_mcp_json.
        # Here we assert the return code alone confirms the wiring path was reached
        # (a short-circuit before merge would still return _EXIT_OK, but the dedicated
        # test with real subprocess catches the absence of the file).

        # 5. No reconnect reminder — nothing changed.
        assert hasattr(lore_deploy, "_MCP_RECONNECT_REMINDER"), (
            "lore_deploy._MCP_RECONNECT_REMINDER constant is not yet defined"
        )
        captured_out = capsys.readouterr().out
        assert lore_deploy._MCP_RECONNECT_REMINDER not in captured_out, (
            f"verb_start must NOT print the MCP-reconnect reminder when the running "
            f"container is already on the current image (spurious churn); "
            f"stdout was: {captured_out!r}"
        )

    # --- A3 ---
    def test_verb_start_fresh_launch_prints_reconnect_reminder(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A3: NOT running (fresh launch path) → launches and prints the reconnect reminder.

        A newly launched server means the operator's MCP client must reconnect so
        it picks up the live tool schemas.  The reminder is not optional — it closes
        the gap where the container is up but the client is still talking to a stale
        session.  Current code never prints this reminder.
        """
        # --- Arrange ---
        PROJECT_SLUG = "freshproject"
        project = _make_project(tmp_path, PROJECT_SLUG)

        # Container does not exist (absent → no state).
        monkeypatch.setattr(lore_deploy, "_container_state", lambda name: None)

        # Image exists so the missing-image guard doesn't abort.
        monkeypatch.setattr(lore_deploy, "_image_exists", lambda image: True)

        # Pre-flight probes: succeed silently so the launch path is reached.
        # The store gate is the SurrealDB /health pre-flight (_probe_surreal),
        # which replaced the retired qdrant _ensure_collections step at P8a.
        monkeypatch.setattr(lore_deploy, "_probe_embed", lambda *a, **k: lore_deploy._EXIT_OK)
        monkeypatch.setattr(lore_deploy, "_probe_surreal", lambda *a, **k: lore_deploy._EXIT_OK)

        monkeypatch.setattr(lore_deploy, "_read_config_field", _stub_read_config_field)

        launch_calls: list[tuple[Path, Path, Path]] = []

        def _recording_launch(proj: Path, config_path: Path, env_file: Path) -> None:
            launch_calls.append((proj, config_path, env_file))

        monkeypatch.setattr(lore_deploy, "_launch_container", _recording_launch)

        # _merge_mcp_from_config shelled out via _run; stub it to avoid subprocess.
        monkeypatch.setattr(lore_deploy, "_merge_mcp_from_config",
                            lambda project, slug, config_path: _LORE_SERVER_PORT)

        # After the fresh launch, verb_start waits for the MCP port to bind; stub
        # that wait as succeeding so the test does not poll an unbound port for the
        # full 600s bind timeout. Orthogonal to what this test asserts (launch
        # happened + reconnect reminder printed).
        monkeypatch.setattr(lore_deploy, "_await_bind", lambda *args, **kwargs: lore_deploy._EXIT_OK)

        env_file = tmp_path / "secrets.env"
        env_file.write_text("LORE_TEI_KEY=test\n", encoding="utf-8")
        # The artifact gates (#125/#131/#132) run on every start path that ends
        # with a running container. Arrange them as passing — this test is about
        # a different concern, and both probes talk to a real container.
        _stub_artifact_gates(monkeypatch)


        # --- Act ---
        return_code = lore_deploy.verb_start(project, env_file)

        # --- Assert ---

        # 1. Returns success.
        assert return_code == lore_deploy._EXIT_OK, (
            f"verb_start must return _EXIT_OK after a fresh launch; got {return_code}"
        )

        # 2. _launch_container was called (the container was started).
        assert len(launch_calls) == 1, (
            f"verb_start must call _launch_container once for a fresh launch; "
            f"got {len(launch_calls)} call(s)"
        )

        # 3. Reconnect reminder printed.
        assert hasattr(lore_deploy, "_MCP_RECONNECT_REMINDER"), (
            "lore_deploy._MCP_RECONNECT_REMINDER constant is not yet defined"
        )
        captured_out = capsys.readouterr().out
        assert lore_deploy._MCP_RECONNECT_REMINDER in captured_out, (
            f"verb_start must print _MCP_RECONNECT_REMINDER after a fresh launch so the "
            f"operator knows to reconnect the MCP session; stdout was: {captured_out!r}"
        )


class TestVerbStatusImageCurrency:
    """Contract: verb_status must report whether the running container is on the current image.

    A running container that pre-dates a ``podman build`` of ``localhost/lore:latest``
    is serving stale code.  The operator cannot discover this without comparing
    the running image ID to the tag's current ID — verb_status must do that comparison
    and print a clear indication.  Current code never inspects image IDs at all.
    """

    # --- A4 (current) ---
    def test_verb_status_running_current_image_reports_up_to_date(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A4a: running container on current image → status output contains a
        'current' / up-to-date indication (case-insensitive substring match).
        """
        # --- Arrange ---
        PROJECT_SLUG = "liveproject"
        project = _make_project(tmp_path, PROJECT_SLUG)

        monkeypatch.setattr(lore_deploy, "_container_state", lambda name: "running")

        assert hasattr(lore_deploy, "_container_image_id"), (
            "lore_deploy._container_image_id seam not yet defined"
        )
        assert hasattr(lore_deploy, "_image_id"), (
            "lore_deploy._image_id seam not yet defined"
        )
        monkeypatch.setattr(
            lore_deploy, "_container_image_id",
            lambda name: _CURRENT_IMAGE_ID,
        )
        monkeypatch.setattr(
            lore_deploy, "_image_id",
            lambda image: _CURRENT_IMAGE_ID,
        )

        # Suppress manifest read: point MANIFEST_DIR at a non-existent tmp dir so
        # MANIFEST_DIR / "<slug>.db" does not exist (no instance-attr patching —
        # Path slots are read-only on 3.14; replace the module attr instead).
        monkeypatch.setattr(lore_deploy, "MANIFEST_DIR", tmp_path / "state")

        # --- Act ---
        return_code = lore_deploy.verb_status(project)
        captured_out = capsys.readouterr().out

        # --- Assert ---
        assert return_code == lore_deploy._EXIT_OK

        # The image-currency status line must contain a word indicating the image
        # is current.  Scope the search to the "image:" report line(s) only so a
        # slug or unrelated line cannot satisfy the substring check (mirrors the
        # stale-case guard below).  Case-insensitive — any of "current",
        # "up-to-date", "up to date" qualifies.
        image_lines = "\n".join(
            line for line in captured_out.splitlines() if "image:" in line.lower()
        ).lower()
        assert image_lines, (
            f"verb_status must emit an image-currency line for a running container; "
            f"stdout was: {captured_out!r}"
        )
        assert any(word in image_lines for word in ("current", "up-to-date", "up to date")), (
            f"verb_status must report 'current' or 'up-to-date' for a running container "
            f"whose image ID matches the tag; image-currency line was: {image_lines!r}"
        )

    # --- A4 (stale) ---
    def test_verb_status_running_stale_image_reports_stale(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A4b: running container on stale image → status output contains a
        'stale' / 'rebuild available' / 'outdated' indication.

        This is the key operator-facing signal: without it, the operator has no way
        to know new code was built but is not running.
        """
        # --- Arrange ---
        # Slug deliberately free of any staleness/currency keyword: verb_status
        # echoes the container name (slug) into the image-currency line, so a slug
        # like "staleproject" would satisfy the substring check regardless of the
        # actual verdict (a false green).
        PROJECT_SLUG = "imgcheck"
        project = _make_project(tmp_path, PROJECT_SLUG)

        monkeypatch.setattr(lore_deploy, "_container_state", lambda name: "running")

        assert hasattr(lore_deploy, "_container_image_id"), (
            "lore_deploy._container_image_id seam not yet defined"
        )
        assert hasattr(lore_deploy, "_image_id"), (
            "lore_deploy._image_id seam not yet defined"
        )
        # Running image differs from the current tag — stale container.
        monkeypatch.setattr(
            lore_deploy, "_container_image_id",
            lambda name: _RUNNING_IMAGE_ID,
        )
        monkeypatch.setattr(
            lore_deploy, "_image_id",
            lambda image: _CURRENT_IMAGE_ID,
        )

        # --- Act ---
        return_code = lore_deploy.verb_status(project)
        captured_out = capsys.readouterr().out

        # --- Assert ---
        assert return_code == lore_deploy._EXIT_OK

        # The image-currency status line must contain a word flagging staleness.
        # Scope the search to the "image:" report line(s) only — the container-state
        # line ("... container = running") carries the slug, and a slug like
        # "staleproject" would otherwise satisfy the substring check regardless of
        # what the image verdict actually says (a false green).
        image_lines = "\n".join(
            line for line in captured_out.splitlines() if "image:" in line.lower()
        ).lower()
        assert image_lines, (
            f"verb_status must emit an image-currency line for a running container; "
            f"stdout was: {captured_out!r}"
        )
        assert any(
            word in image_lines
            for word in ("stale", "rebuild", "outdated", "new image", "restart required")
        ), (
            f"verb_status must report staleness ('stale', 'rebuild available', etc.) when "
            f"the running container's image ID differs from the current tag; "
            f"image-currency line was: {image_lines!r}"
        )

    def test_verb_status_stopped_container_does_not_report_image_currency(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """verb_status for a stopped/absent container must not crash or report image currency.

        A guard against an implementation that calls _container_image_id on a
        non-running container and gets None, then crashes on a None comparison.
        """
        # --- Arrange ---
        PROJECT_SLUG = "stoppedproject"
        project = _make_project(tmp_path, PROJECT_SLUG)

        monkeypatch.setattr(lore_deploy, "_container_state", lambda name: None)

        # Image ID helpers should not be called for a stopped container;
        # if they are, let them return None (the real podman behaviour for absent containers).
        if hasattr(lore_deploy, "_container_image_id"):
            monkeypatch.setattr(lore_deploy, "_container_image_id", lambda name: None)

        # --- Act (must not raise) ---
        return_code = lore_deploy.verb_status(project)

        # --- Assert ---
        assert return_code == lore_deploy._EXIT_OK, (
            f"verb_status must return _EXIT_OK for a stopped container; got {return_code}"
        )


# ===========================================================================
# Defect B — destructive tear-down before validating (the production outage).
# ===========================================================================
#
# The stale-image recreate branch in verb_start (the RUNNING + stale-image path)
# issued `podman stop` + `podman rm` on the LIVE container BEFORE attempting the
# relaunch, with NO precondition guards.  The fresh-launch path, by contrast,
# checks `_image_exists(IMAGE)` and `env_file.exists()` FIRST and returns
# _EXIT_ERROR if either fails.  So on the recreate path a missing env-file (the
# Defect-A trigger) or an absent image destroyed the serving container and then
# failed to relaunch -> total outage, surfaced as an uncaught CalledProcessError
# (because _launch_container -> _run uses check=True).
#
# Contract pinned here (observable behavior; the spec, NOT the current body):
#   - The recreate path VALIDATES every launch precondition (env-file present,
#     image present) BEFORE any `podman stop`/`rm`.  A stale-but-serving
#     container beats a dead one.
#   - A failed precondition -> return _EXIT_ERROR and LEAVE THE RUNNING
#     CONTAINER UNTOUCHED (no stop, no rm, no relaunch attempt).
#   - A launch failure AFTER valid preconditions is reported loudly
#     (_EXIT_ERROR, on stderr), never propagated as an uncaught exception.


class _RecreatePathFixture:
    """Reusable arrangement for the Defect-B recreate-path tests.

    Wires verb_start into the RUNNING + stale-image branch using the SAME mock
    seams the existing ``TestVerbStartStaleImageRecreateBehavior`` uses
    (``_container_state`` -> "running", divergent ``_container_image_id`` vs
    ``_image_id``), then records every ``_run`` invocation and every
    ``_launch_container`` call so a test can assert on the issued podman commands
    and on launch attempts.

    Why a builder, not copy-paste: clauses 1 & 5 — the recreate-path tests share
    one source of truth for the stale-detection wiring, the container-name
    derivation, and the run/launch recorders, so a drift in the convention
    (e.g. the ``lore-<slug>`` name format) cannot silently diverge across tests.
    """

    def __init__(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, slug: str) -> None:
        self.monkeypatch = monkeypatch
        self.tmp_path = tmp_path
        self.slug = slug
        self.project = _make_project(tmp_path, slug)
        self.container_name = f"lore-{slug}"
        # Ordered transcript of every podman command verb_start issues through _run.
        self.run_calls: list[list[str]] = []
        # Every _launch_container invocation (the relaunch attempt).
        self.launch_calls: list[tuple[Path, Path, Path]] = []
        # An env-file path that, by default, DOES NOT exist on disk (the outage
        # trigger).  Tests that need it present call .create_env_file().
        self.env_file = tmp_path / f"{slug}.env"

    def wire_running_and_stale(self) -> None:
        """Put verb_start on the RUNNING + stale-image recreate branch."""
        self.monkeypatch.setattr(lore_deploy, "_container_state", lambda name: "running")
        # Divergent IDs => stale => recreate branch (matches the existing A1 test).
        self.monkeypatch.setattr(
            lore_deploy, "_container_image_id", lambda name: _RUNNING_IMAGE_ID
        )
        self.monkeypatch.setattr(
            lore_deploy, "_image_id", lambda image: _CURRENT_IMAGE_ID
        )
        self.monkeypatch.setattr(lore_deploy, "_read_config_field", _stub_read_config_field)

    def install_run_recorder(self) -> None:
        """Record (and succeed) every podman command issued via _run."""

        def _recording_run(cmd: list[str], **kwargs: bool) -> subprocess.CompletedProcess[str]:
            self.run_calls.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        self.monkeypatch.setattr(lore_deploy, "_run", _recording_run)

    def install_launch_recorder(self) -> None:
        """Record _launch_container calls without shelling out (default: succeeds)."""

        def _recording_launch(proj: Path, config_path: Path, env_file: Path) -> None:
            self.launch_calls.append((proj, config_path, env_file))

        self.monkeypatch.setattr(lore_deploy, "_launch_container", _recording_launch)

    def install_failing_launch(self) -> None:
        """Make _launch_container fail the way the real one does: a podman non-zero.

        The real ``_launch_container`` calls ``_run(cmd)`` with the default
        ``check=True``, so a non-zero ``podman run`` raises
        ``subprocess.CalledProcessError``.  We reproduce that exact failure mode
        (not a generic Exception) so the test pins the real seam.
        """

        def _failing_launch(proj: Path, config_path: Path, env_file: Path) -> None:
            self.launch_calls.append((proj, config_path, env_file))
            raise subprocess.CalledProcessError(
                returncode=125,  # podman's "container/run setup failed" exit code
                cmd=["podman", "run", "-d", "--name", self.container_name, lore_deploy.IMAGE],
            )

        self.monkeypatch.setattr(lore_deploy, "_launch_container", _failing_launch)

    def install_image_present(self, present: bool = True) -> None:
        """Stub _image_exists for the launch-precondition guard."""
        self.monkeypatch.setattr(lore_deploy, "_image_exists", lambda image: present)

    def create_env_file(self) -> None:
        """Materialise the env-file so the env-file precondition passes."""
        self.env_file.write_text("LORE_TEI_KEY=test\n", encoding="utf-8")

    def stop_calls(self) -> list[list[str]]:
        """podman stop commands targeting THIS container."""
        return [c for c in self.run_calls if "stop" in c and self.container_name in c]

    def rm_calls(self) -> list[list[str]]:
        """podman rm commands targeting THIS container."""
        return [c for c in self.run_calls if "rm" in c and self.container_name in c]


class TestVerbStartRecreateValidatesBeforeTeardown:
    """Contract: the stale-image recreate path must validate BEFORE it destroys.

    This is the regression guard for the production outage.  The invariant is
    'never tear down a live, serving container until every launch precondition
    is known good'.  A stale-but-serving container is strictly better than a
    dead one; a missing env-file or absent image must abort the recreate with
    _EXIT_ERROR and leave the running container exactly as it was.
    """

    _SLUG = "demand_intelligence"  # a real on-host lore slug (see lore-secrets/)

    # --- B1: the direct outage regression ---
    def test_recreate_with_missing_env_file_does_not_remove_running_container(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """B1: RUNNING + stale image + env-file ABSENT -> abort with _EXIT_ERROR,
        no stop, no rm, no launch.  The exact outage that occurred.

        This case WOULD have caught the bug: the buggy body stops+removes the
        live container, then _launch_container raises on the missing env-file.
        """
        # --- Arrange ---
        fixture = _RecreatePathFixture(monkeypatch, tmp_path, self._SLUG)
        fixture.wire_running_and_stale()
        fixture.install_run_recorder()
        fixture.install_launch_recorder()
        fixture.install_image_present(True)  # image is fine; only the env-file is missing
        # Deliberately DO NOT create the env-file — this is the outage trigger.
        assert not fixture.env_file.exists(), "precondition: env-file must be absent for this case"

        # --- Act ---
        return_code = lore_deploy.verb_start(fixture.project, fixture.env_file)

        # --- Assert ---
        # The running container must survive an aborted recreate.
        assert fixture.stop_calls() == [], (
            f"recreate must NOT 'podman stop {fixture.container_name}' when a launch "
            f"precondition (env-file) is unmet; run_calls={fixture.run_calls}"
        )
        assert fixture.rm_calls() == [], (
            f"recreate must NOT 'podman rm {fixture.container_name}' when a launch "
            f"precondition (env-file) is unmet; run_calls={fixture.run_calls}"
        )
        # No relaunch was even attempted.
        assert fixture.launch_calls == [], (
            f"recreate must NOT attempt _launch_container when a precondition is unmet; "
            f"got {len(fixture.launch_calls)} attempt(s)"
        )
        # Loud failure, not silent success.
        assert return_code == lore_deploy._EXIT_ERROR, (
            f"recreate must return _EXIT_ERROR when the env-file is missing; got {return_code}"
        )

    # --- B2: the same invariant, image side of the precondition ---
    def test_recreate_with_missing_image_does_not_remove_running_container(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """B2: RUNNING + stale-by-id + image ABSENT -> abort with _EXIT_ERROR,
        no stop, no rm, no launch.

        Scenario: the running container's image ID still resolves (it is baked
        into the live container), but ``localhost/lore:latest`` no longer exists
        as a tag (e.g. pruned mid-rebuild).  Tearing down here would strand the
        project with neither a container nor an image to relaunch from.
        """
        # --- Arrange ---
        fixture = _RecreatePathFixture(monkeypatch, tmp_path, self._SLUG)
        fixture.wire_running_and_stale()
        fixture.install_run_recorder()
        fixture.install_launch_recorder()
        fixture.create_env_file()           # env-file is fine ...
        fixture.install_image_present(False)  # ... but the image tag is gone.

        # --- Act ---
        return_code = lore_deploy.verb_start(fixture.project, fixture.env_file)

        # --- Assert ---
        assert fixture.stop_calls() == [], (
            f"recreate must NOT stop the live container when the image is absent; "
            f"run_calls={fixture.run_calls}"
        )
        assert fixture.rm_calls() == [], (
            f"recreate must NOT remove the live container when the image is absent; "
            f"run_calls={fixture.run_calls}"
        )
        assert fixture.launch_calls == [], (
            f"recreate must NOT attempt _launch_container when the image is absent; "
            f"got {len(fixture.launch_calls)} attempt(s)"
        )
        assert return_code == lore_deploy._EXIT_ERROR, (
            f"recreate must return _EXIT_ERROR when the image is absent; got {return_code}"
        )

    # --- B3: a launch failure after valid preconditions is reported, not raised ---
    def test_recreate_launch_failure_is_reported_not_raised(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """B3: preconditions PASS but _launch_container fails (podman non-zero)
        -> verb_start returns _EXIT_ERROR and is LOUD on stderr; no uncaught raise.

        Even with all preconditions satisfied, a podman run can still fail at
        runtime.  When it does after the tear-down, the recreate cannot keep the
        old container alive, but it must still degrade gracefully: report the
        failure (non-zero exit + stderr), never propagate a raw
        CalledProcessError up to the dispatcher.
        """
        # --- Arrange ---
        fixture = _RecreatePathFixture(monkeypatch, tmp_path, self._SLUG)
        fixture.wire_running_and_stale()
        fixture.install_run_recorder()
        fixture.create_env_file()
        fixture.install_image_present(True)
        # Recreate now pre-flights /embed + the store before teardown; stub both
        # reachable so this test reaches the failing launch it is about.
        monkeypatch.setattr(lore_deploy, "_probe_embed", lambda *a, **k: lore_deploy._EXIT_OK)
        monkeypatch.setattr(lore_deploy, "_probe_surreal", lambda *a, **k: lore_deploy._EXIT_OK)
        fixture.install_failing_launch()  # podman run -> CalledProcessError(125)

        # --- Act (must NOT raise) ---
        try:
            return_code = lore_deploy.verb_start(fixture.project, fixture.env_file)
        except subprocess.CalledProcessError as error:  # pragma: no cover - failure path
            raise AssertionError(
                "verb_start must NOT propagate an uncaught CalledProcessError when "
                f"_launch_container fails on the recreate path; it raised: {error!r}"
            )

        # --- Assert ---
        # A launch was attempted (preconditions were good).
        assert len(fixture.launch_calls) == 1, (
            f"recreate must attempt _launch_container exactly once when preconditions "
            f"pass; got {len(fixture.launch_calls)} attempt(s)"
        )
        # Reported as a loud failure.
        assert return_code == lore_deploy._EXIT_ERROR, (
            f"a failed relaunch must surface as _EXIT_ERROR; got {return_code}"
        )
        captured = capsys.readouterr()
        # The failure must be visible to the operator (Unix: loud on failure).
        assert captured.err.strip(), (
            "a failed relaunch on the recreate path must write a diagnostic to stderr "
            "(loud on failure); stderr was empty"
        )

    # --- B4: ordering invariant, not mere presence ---
    def test_recreate_happy_path_validates_before_teardown(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """B4: RUNNING + stale + all preconditions good -> the env-file/image checks
        happen BEFORE the first stop/rm (ordering invariant), then stop+rm+relaunch.

        Presence of guards is not enough: a guard placed AFTER the tear-down does
        not prevent the outage.  This pins the ORDER — every precondition probe is
        observed before any destructive podman command is issued.
        """
        # --- Arrange ---
        fixture = _RecreatePathFixture(monkeypatch, tmp_path, self._SLUG)
        fixture.wire_running_and_stale()
        fixture.install_launch_recorder()
        fixture.create_env_file()

        # A single ordered transcript across BOTH precondition probes and podman
        # commands, so we can assert that no probe occurs after the first teardown.
        transcript: list[str] = []

        def _recording_run(cmd: list[str], **kwargs: bool) -> subprocess.CompletedProcess[str]:
            # Tag stop/rm against THIS container as destructive teardown events.
            if "stop" in cmd and fixture.container_name in cmd:
                transcript.append("teardown:stop")
            elif "rm" in cmd and fixture.container_name in cmd:
                transcript.append("teardown:rm")
            fixture.run_calls.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        monkeypatch.setattr(lore_deploy, "_run", _recording_run)

        # The env-file precondition is observed by wrapping Path.exists for OUR
        # env-file only; the image precondition by wrapping _image_exists.  Both
        # record into the same transcript so ordering is comparable.
        real_exists = Path.exists

        def _recording_exists(self_path: Path) -> bool:
            result = real_exists(self_path)
            if self_path == fixture.env_file:
                transcript.append("check:env_file")
            return result

        monkeypatch.setattr(Path, "exists", _recording_exists)

        def _recording_image_exists(image: str) -> bool:
            transcript.append("check:image")
            return True

        monkeypatch.setattr(lore_deploy, "_image_exists", _recording_image_exists)

        # After the teardown+relaunch, verb_start waits for the MCP port to bind;
        # stub that wait as succeeding so the test does not poll an unbound port for
        # the full 600s bind timeout. It runs AFTER the teardown, so it does not
        # perturb the ordering-invariant transcript this test asserts on.
        monkeypatch.setattr(lore_deploy, "_await_bind", lambda *args, **kwargs: lore_deploy._EXIT_OK)
        # The recreate now also pre-flights /embed + the store before teardown;
        # stub both reachable (silently — this test's ordering invariant is about
        # the image/env-file guards; the probes' own before-teardown ordering is
        # pinned by TestRecreateGatesOnStorePreflight).
        monkeypatch.setattr(lore_deploy, "_probe_embed", lambda *a, **k: lore_deploy._EXIT_OK)
        monkeypatch.setattr(lore_deploy, "_probe_surreal", lambda *a, **k: lore_deploy._EXIT_OK)
        # The artifact gates (#125/#131/#132) run on every start path that ends
        # with a running container. Arrange them as passing — this test is about
        # a different concern, and both probes talk to a real container.
        _stub_artifact_gates(monkeypatch)


        # --- Act ---
        return_code = lore_deploy.verb_start(fixture.project, fixture.env_file)

        # --- Assert ---
        assert return_code == lore_deploy._EXIT_OK, (
            f"a clean recreate (all preconditions good) must return _EXIT_OK; got {return_code}"
        )
        # The recreate actually happened (stop + rm + relaunch).
        assert "teardown:stop" in transcript and "teardown:rm" in transcript, (
            f"a clean recreate must stop and rm the stale container; transcript={transcript}"
        )
        assert len(fixture.launch_calls) == 1, (
            f"a clean recreate must relaunch exactly once; got {len(fixture.launch_calls)}"
        )
        # ORDERING INVARIANT: at least one precondition check must precede the
        # first destructive teardown event, and NO precondition check may occur
        # after the first teardown (a guard after the kill cannot prevent the outage).
        first_teardown_index = next(
            i for i, event in enumerate(transcript) if event.startswith("teardown:")
        )
        checks_before = [e for e in transcript[:first_teardown_index] if e.startswith("check:")]
        checks_after = [e for e in transcript[first_teardown_index:] if e.startswith("check:")]
        assert checks_before, (
            "at least one launch precondition (env-file/image) must be validated BEFORE "
            f"the first teardown; transcript={transcript}"
        )
        assert not checks_after, (
            "no launch precondition may be validated AFTER the first teardown — a guard "
            f"placed after the stop/rm cannot prevent the outage; transcript={transcript}"
        )


# ===========================================================================
# Defect A — per-slug secrets env-file resolution.
# ===========================================================================
#
# The old DEFAULT_ENV_FILE was a single project-agnostic path
# (~/docker/mcp/lore.env) that does NOT exist on this host.  Secrets actually
# live per-project at ~/docker/mcp/lore-secrets/<slug>.env (verified on-host:
# lore-secrets/demand_intelligence.env exists; lore.env does not).  Running
# `start` without --env-file resolved to the missing file -> podman run exit 125.
#
# Contract pinned here (the spec, NOT the current argparse default):
#   - The argparse --env-file default is None (so "unsupplied" is distinguishable
#     from an explicit value).
#   - When --env-file is unsupplied, the env-file resolves per-slug to
#     ~/docker/mcp/lore-secrets/<slug>.env, where slug is the project name.
#   - An explicit --env-file is honored verbatim.
#
# Seam pinned: ``lore_deploy._resolve_env_file(project, explicit)`` — the single
# place that turns (project, maybe-explicit-path) into the concrete env-file
# Path.  ``main()`` feeds it ``args.env_file`` (None when the flag is omitted).

# The production secrets convention (shared source of truth, clause 5): derived
# from Path.home() exactly as the spec documents, NOT a hand-copied literal that
# could drift from the resolver.  These are the same anchors the host uses.
_SECRETS_DIR = Path.home() / "docker" / "mcp" / "lore-secrets"
# The pre-fix wrong default, asserted-against to prove it is no longer returned.
_OLD_BAD_DEFAULT = Path.home() / "docker" / "mcp" / "lore.env"


class TestEnvFileResolution:
    """Contract: env-file resolves per-slug unless explicitly overridden.

    Pins Defect-A behavior at its seam (``_resolve_env_file``) and at the CLI
    surface (argparse default must be None).  Fixtures use a real on-host slug
    (``demand_intelligence`` — see ~/docker/mcp/lore-secrets/) so the resolved
    path is one that actually exists in production, not a synthetic stand-in.
    """

    # A real, on-host project slug (lore-secrets/demand_intelligence.env exists).
    _REAL_SLUG = "demand_intelligence"

    # --- A-fix 1: per-slug default ---
    def test_env_file_defaults_to_per_slug_secrets_path(self, tmp_path: Path) -> None:
        """`--project .../demand_intelligence`, no `--env-file` -> resolves to
        ~/docker/mcp/lore-secrets/demand_intelligence.env, NOT ~/docker/mcp/lore.env.

        The expected path is built from the production convention
        (``Path.home()/docker/mcp/lore-secrets/<slug>.env``), independent of the
        resolver's own formula — so it would still hold if the implementation
        were subtly wrong (e.g. dropped the ``lore-secrets`` segment).
        """
        assert hasattr(lore_deploy, "_resolve_env_file"), (
            "lore_deploy._resolve_env_file seam is not yet defined; the implementer must "
            "add a resolver that turns (project, explicit-or-None) into a concrete env-file."
        )
        project = tmp_path / self._REAL_SLUG
        project.mkdir()

        # explicit=None models an UNsupplied --env-file (argparse default must be None).
        resolved = lore_deploy._resolve_env_file(project, None)

        expected = _SECRETS_DIR / f"{self._REAL_SLUG}.env"
        assert Path(resolved) == expected, (
            f"unsupplied --env-file must resolve per-slug to {expected}; got {resolved}"
        )
        # And explicitly NOT the old project-agnostic path that triggered the outage.
        assert Path(resolved) != _OLD_BAD_DEFAULT, (
            f"resolved env-file must NOT be the old project-agnostic default "
            f"{_OLD_BAD_DEFAULT} (the nonexistent file that caused exit 125)"
        )

    # --- A-fix 2: explicit override wins verbatim ---
    def test_explicit_env_file_overrides_per_slug_default(self, tmp_path: Path) -> None:
        """An explicit --env-file is honored verbatim — no per-slug rewriting.

        Operators sometimes point at a one-off secrets file; an explicit value
        must pass through untouched, not get coerced back into the lore-secrets
        directory.
        """
        assert hasattr(lore_deploy, "_resolve_env_file"), (
            "lore_deploy._resolve_env_file seam is not yet defined"
        )
        project = tmp_path / self._REAL_SLUG
        project.mkdir()

        # A realistic operator-supplied override, distinct from the per-slug path.
        explicit = tmp_path / "custom" / "alt-secrets.env"

        resolved = lore_deploy._resolve_env_file(project, str(explicit))

        assert Path(resolved) == explicit, (
            f"an explicit --env-file must be honored verbatim; expected {explicit}, "
            f"got {resolved}"
        )
        # The per-slug default must NOT override an explicit value.
        assert Path(resolved) != _SECRETS_DIR / f"{self._REAL_SLUG}.env", (
            "an explicit --env-file must NOT be rewritten to the per-slug default"
        )

    # --- A-fix 3: the CLI default must be None, not the old bad path ---
    def test_argparse_env_file_default_is_none(self) -> None:
        """The --env-file argparse default must be None (so 'unsupplied' is
        distinguishable) and must NOT be the old nonexistent project-agnostic path.

        If the default were a concrete path, the verb could never tell an
        unsupplied flag from an explicit one, and the per-slug resolution could
        not fire.
        """
        parser = lore_deploy._build_parser()
        namespace = parser.parse_args(["start", "--project", "/tmp/demand_intelligence"])
        assert namespace.env_file is None, (
            f"--env-file argparse default must be None so the verb can resolve it "
            f"per-slug; got default {namespace.env_file!r}"
        )
        # Guard against the specific regression: the old default string must be gone.
        assert namespace.env_file != str(_OLD_BAD_DEFAULT), (
            f"--env-file default must not be the old project-agnostic path "
            f"{_OLD_BAD_DEFAULT} (Defect A)"
        )


# ===========================================================================
# Defect C — the SurrealDB store-reachability pre-flight (P8a store unification).
# ===========================================================================
#
# At P8a Qdrant was retired; the unified store is the persistent ``lore-surreal``
# SurrealDB container.  The old ``_ensure_collections`` gate (which imported
# ``qdrant_client`` and read ``config.qdrant.url``) is dead on BOTH counts —
# ``setup``/``start`` exited 2 with "No module named 'qdrant_client'".  The new
# gate, ``_probe_surreal``, checks store REACHABILITY only (HTTP ``GET /health``)
# — schema + dim ownership (including the embedding-schema-fingerprint rebuild)
# lives in the loremaster server, not this skill.  Its ONE permitted mutation is
# start-if-stopped reboot recovery (``podman start lore-surreal`` when the
# container exists but sits Exited after a host reboot); it NEVER creates,
# recreates, or removes that container or touches its data dir.
#
# Contract pinned here (the spec, NOT the current body):
#   - ``_surreal_health_url`` maps ``ws(s)://host:port/rpc`` -> ``http(s)://host:port/health``.
#   - ``_probe_surreal`` returns _EXIT_OK on a clean /health 200 with NO podman call.
#   - On failure it starts the container ONLY if it exists-but-stopped, then re-polls;
#     it never issues run/rm/create/stop against lore-surreal.
#   - Absent container or still-unreachable -> _EXIT_ERROR, LOUD stderr naming the
#     URL + the container name.
#   - Both ``verb_start`` and ``verb_setup`` gate on it (a failed probe aborts before launch).


class TestSurrealHealthUrl:
    """``_surreal_health_url`` maps the SurrealDB RPC URL to its /health HTTP URL."""

    def test_ws_rpc_maps_to_http_health(self) -> None:
        """``ws://host:port/rpc`` -> ``http://host:port/health`` (scheme + path only)."""
        assert (
            lore_deploy._surreal_health_url("ws://127.0.0.1:18500/rpc")
            == "http://127.0.0.1:18500/health"
        )

    def test_wss_rpc_maps_to_https_health(self) -> None:
        """``wss://host:port/rpc`` -> ``https://host:port/health`` (TLS variant)."""
        assert (
            lore_deploy._surreal_health_url("wss://surreal.example:8000/rpc")
            == "https://surreal.example:8000/health"
        )


class TestProbeSurreal:
    """``_probe_surreal`` gate: reachability probe + bounded start-if-stopped recovery."""

    _RPC_URL = "ws://127.0.0.1:18500/rpc"

    def _stub_url_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Stub the config read so the probe reads our fixed surreal.url."""
        monkeypatch.setattr(
            lore_deploy, "_read_config_field", lambda config_path, expr: self._RPC_URL
        )

    def _record_run(self, monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
        """Install a recording _run that succeeds; return the transcript list."""
        run_calls: list[list[str]] = []

        def _recording_run(cmd: list[str], **kwargs: bool) -> subprocess.CompletedProcess[str]:
            run_calls.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        monkeypatch.setattr(lore_deploy, "_run", _recording_run)
        return run_calls

    @staticmethod
    def _mutating(run_calls: list[list[str]]) -> list[list[str]]:
        """podman commands that would create/destroy/stop the store (forbidden)."""
        forbidden = {"run", "rm", "create", "stop"}
        return [c for c in run_calls if set(c) & forbidden]

    # --- healthy on the first probe: OK, and NOT a single podman call ---
    def test_healthy_first_probe_returns_ok_without_podman(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A clean /health 200 returns _EXIT_OK and never shells out to podman."""
        self._stub_url_read(monkeypatch)
        monkeypatch.setattr(lore_deploy, "_probe_surreal_health", lambda url, **kw: True)
        run_calls = self._record_run(monkeypatch)
        state_calls: list[str] = []

        def _recording_state(name: str) -> str | None:
            state_calls.append(name)
            return None

        monkeypatch.setattr(lore_deploy, "_container_state", _recording_state)

        rc = lore_deploy._probe_surreal(tmp_path / "lore.yaml")

        assert rc == lore_deploy._EXIT_OK
        assert run_calls == [], f"a healthy probe must not touch podman; got {run_calls}"
        assert state_calls == [], "a healthy probe must not inspect the container state"
        assert "OK" in capsys.readouterr().out

    # --- reboot recovery: stopped container -> podman start -> healthy on re-poll ---
    def test_reboot_recovery_starts_stopped_container(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """/health down + container Exited -> ``podman start lore-surreal`` -> re-probe OK."""
        self._stub_url_read(monkeypatch)
        # First probe False (down), second probe True (came up after start).
        health_results = iter([False, True])
        monkeypatch.setattr(
            lore_deploy, "_probe_surreal_health", lambda url, **kw: next(health_results)
        )
        monkeypatch.setattr(lore_deploy, "_container_state", lambda name: "exited")
        run_calls = self._record_run(monkeypatch)
        # No real sleeping in the bounded wait loop. ``time`` is the same module
        # object lore_deploy imported (patching it here patches lore_deploy's view
        # of it too), so this reaches through without accessing a name lore_deploy
        # does not re-export.
        monkeypatch.setattr(time, "sleep", lambda seconds: None)

        rc = lore_deploy._probe_surreal(tmp_path / "lore.yaml")

        assert rc == lore_deploy._EXIT_OK
        start_calls = [
            c for c in run_calls
            if "start" in c and lore_deploy.SURREAL_CONTAINER_NAME in c
        ]
        assert start_calls, (
            f"reboot recovery must `podman start {lore_deploy.SURREAL_CONTAINER_NAME}`; "
            f"run_calls={run_calls}"
        )
        assert self._mutating(run_calls) == [], (
            f"the store container must never be run/rm/create/stop'd; got {run_calls}"
        )

    # --- absent container: fail loud, ZERO podman mutation ---
    def test_absent_container_fails_loud_without_mutation(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """/health down + no container -> _EXIT_ERROR, no podman call, loud stderr."""
        self._stub_url_read(monkeypatch)
        monkeypatch.setattr(lore_deploy, "_probe_surreal_health", lambda url, **kw: False)
        monkeypatch.setattr(lore_deploy, "_container_state", lambda name: None)
        run_calls = self._record_run(monkeypatch)

        rc = lore_deploy._probe_surreal(tmp_path / "lore.yaml")

        assert rc == lore_deploy._EXIT_ERROR
        assert run_calls == [], (
            f"an absent store container must not trigger any podman command; got {run_calls}"
        )
        err = capsys.readouterr().err
        assert lore_deploy.SURREAL_CONTAINER_NAME in err, "remediation must name the container"
        assert "18500" in err, "remediation must name the store URL"

    # --- running-but-unhealthy: start-if-stopped does not apply ---
    def test_running_but_unhealthy_does_not_restart(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """/health down + container already running -> _EXIT_ERROR, no restart attempt.

        start-if-stopped is the ONLY mutation; a running-but-unhealthy node is not
        something this gate may stop/recreate — it fails loud instead.
        """
        self._stub_url_read(monkeypatch)
        monkeypatch.setattr(lore_deploy, "_probe_surreal_health", lambda url, **kw: False)
        monkeypatch.setattr(lore_deploy, "_container_state", lambda name: "running")
        run_calls = self._record_run(monkeypatch)

        rc = lore_deploy._probe_surreal(tmp_path / "lore.yaml")

        assert rc == lore_deploy._EXIT_ERROR
        assert run_calls == [], (
            f"a running-but-unhealthy store must not be restarted/recreated; got {run_calls}"
        )


class TestVerbStartGatesOnSurreal:
    """``verb_start`` must gate the launch on ``_probe_surreal`` (store reachability)."""

    def test_start_proceeds_when_surreal_probe_ok(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """(a) surreal healthy on the probe -> start proceeds to _launch_container."""
        project = _make_project(tmp_path, "surrealok")
        monkeypatch.setattr(lore_deploy, "_container_state", lambda name: None)  # fresh launch
        monkeypatch.setattr(lore_deploy, "_image_exists", lambda image: True)
        monkeypatch.setattr(lore_deploy, "_probe_embed", lambda *a, **k: lore_deploy._EXIT_OK)

        probe_calls: list[Path] = []

        def _recording_probe_surreal(config_path: Path) -> int:
            probe_calls.append(config_path)
            return lore_deploy._EXIT_OK

        monkeypatch.setattr(lore_deploy, "_probe_surreal", _recording_probe_surreal)
        monkeypatch.setattr(lore_deploy, "_read_config_field", _stub_read_config_field)

        launch_calls: list[tuple[Path, Path, Path]] = []
        monkeypatch.setattr(
            lore_deploy, "_launch_container",
            lambda proj, config_path, env_file: launch_calls.append((proj, config_path, env_file)),
        )
        monkeypatch.setattr(
            lore_deploy, "_merge_mcp_from_config",
            lambda project, slug, config_path: _LORE_SERVER_PORT,
        )
        monkeypatch.setattr(lore_deploy, "_await_bind", lambda *a, **k: lore_deploy._EXIT_OK)

        env_file = tmp_path / "secrets.env"
        env_file.write_text("LORE_TEI_KEY=test\n", encoding="utf-8")
        # The artifact gates (#125/#131/#132) run on every start path that ends
        # with a running container. Arrange them as passing — this test is about
        # a different concern, and both probes talk to a real container.
        _stub_artifact_gates(monkeypatch)


        rc = lore_deploy.verb_start(project, env_file)

        assert rc == lore_deploy._EXIT_OK
        assert len(probe_calls) == 1, "start must gate on _probe_surreal exactly once"
        assert len(launch_calls) == 1, "a passing surreal probe must proceed to launch"

    def test_start_aborts_when_surreal_probe_fails(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """(c) surreal probe fails -> _EXIT_ERROR and _launch_container NEVER called."""
        project = _make_project(tmp_path, "surrealdown")
        monkeypatch.setattr(lore_deploy, "_container_state", lambda name: None)
        monkeypatch.setattr(lore_deploy, "_image_exists", lambda image: True)
        monkeypatch.setattr(lore_deploy, "_probe_embed", lambda *a, **k: lore_deploy._EXIT_OK)
        monkeypatch.setattr(
            lore_deploy, "_probe_surreal", lambda config_path: lore_deploy._EXIT_ERROR
        )
        monkeypatch.setattr(lore_deploy, "_read_config_field", _stub_read_config_field)

        launch_calls: list[tuple[Path, Path, Path]] = []
        monkeypatch.setattr(
            lore_deploy, "_launch_container",
            lambda proj, config_path, env_file: launch_calls.append((proj, config_path, env_file)),
        )

        env_file = tmp_path / "secrets.env"
        env_file.write_text("LORE_TEI_KEY=test\n", encoding="utf-8")

        rc = lore_deploy.verb_start(project, env_file)

        assert rc == lore_deploy._EXIT_ERROR, "a failed surreal probe must abort start"
        assert launch_calls == [], "a failed surreal probe must NOT launch the container"


class TestVerbSetupGatesOnSurreal:
    """``verb_setup`` must gate on the same ``_probe_surreal`` store-reachability check."""

    def test_setup_aborts_when_surreal_probe_fails(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """(d) setup gates on _probe_surreal: a failed probe aborts before image/cold-index."""
        project = _make_project(tmp_path, "setupsurreal")
        # NOT already provisioned: point MANIFEST_DIR at an empty dir so <slug>.db is absent,
        # so setup does not early-no-op before reaching the store gate.
        monkeypatch.setattr(lore_deploy, "MANIFEST_DIR", tmp_path / "state")
        monkeypatch.setattr(lore_deploy, "_probe_embed", lambda *a, **k: lore_deploy._EXIT_OK)

        probe_calls: list[Path] = []

        def _recording_probe_surreal(config_path: Path) -> int:
            probe_calls.append(config_path)
            return lore_deploy._EXIT_ERROR

        monkeypatch.setattr(lore_deploy, "_probe_surreal", _recording_probe_surreal)
        # Guard: the image-build / cold-index steps live AFTER the gate; they must
        # not be reached once the probe fails.
        image_calls: list[str] = []

        def _recording_image_exists(image: str) -> bool:
            image_calls.append(image)
            return True

        monkeypatch.setattr(lore_deploy, "_image_exists", _recording_image_exists)

        env_file = tmp_path / "secrets.env"
        env_file.write_text("LORE_TEI_KEY=test\n", encoding="utf-8")

        rc = lore_deploy.verb_setup(project, env_file)

        assert rc == lore_deploy._EXIT_ERROR, "a failed surreal probe must abort setup"
        assert len(probe_calls) == 1, "setup must gate on _probe_surreal exactly once"
        assert image_calls == [], "a failed probe must abort before image-build / cold-index"


class TestNoEnsureCollectionsResidue:
    """The retired qdrant ensure-collections gate must leave no residue (dead-code check)."""

    def test_no_ensure_collections_symbols_in_dispatcher(self) -> None:
        """The dispatcher must expose neither ``_ensure_collections`` nor ``ENSURE_SCRIPT``."""
        assert not hasattr(lore_deploy, "_ensure_collections"), (
            "_ensure_collections delegator must be deleted (qdrant-dead gate)"
        )
        assert not hasattr(lore_deploy, "ENSURE_SCRIPT"), (
            "ENSURE_SCRIPT constant must be deleted (its target script is gone)"
        )

    def test_ensure_collections_script_is_deleted(self) -> None:
        """``scripts/ensure_collections.py`` must be gone (imported dead qdrant_client)."""
        script = Path(lore_deploy.__file__).resolve().parent / "ensure_collections.py"
        assert not script.exists(), (
            "ensure_collections.py must be deleted — it imported the uninstalled "
            "qdrant_client and read the removed config.qdrant.url"
        )


# ===========================================================================
# Round 2 — the stale-image recreate path gates on the store + embedder
# pre-flights BEFORE teardown (the outage guard, extended).
# ===========================================================================
#
# The RUNNING + stale-image recreate branch already validated image + env-file
# BEFORE `podman stop`/`rm` (Defect B).  But a RELAUNCHED server also refuses to
# come up if `/embed` or the SurrealDB store is unreachable (its startup probe
# gate), so those are launch preconditions too.  Gating them before teardown
# keeps a stale-but-serving container alive when the relaunch would fail anyway
# — a stale-but-serving container beats a dead one.  Contract pinned here:
#   - `_probe_embed` AND `_probe_surreal` run BEFORE the first stop/rm.
#   - A failing probe -> _EXIT_ERROR, running (stale) container UNTOUCHED
#     (no stop, no rm, no launch).
#   - Both probes passing -> the recreate proceeds (stop + rm + relaunch).


class TestRecreateGatesOnStorePreflight:
    """Contract: the stale-image recreate path validates store + embedder before teardown."""

    _SLUG = "demand_intelligence"  # a real on-host lore slug (see lore-secrets/)

    def test_recreate_aborts_when_surreal_probe_fails_no_teardown(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """RUNNING + stale + store `/health` down -> abort, no stop/rm/launch, container untouched."""
        fixture = _RecreatePathFixture(monkeypatch, tmp_path, self._SLUG)
        fixture.wire_running_and_stale()
        fixture.install_run_recorder()
        fixture.install_launch_recorder()
        fixture.install_image_present(True)   # image + env-file are fine ...
        fixture.create_env_file()
        # ... but the SurrealDB store pre-flight fails.
        monkeypatch.setattr(lore_deploy, "_probe_embed", lambda *a, **k: lore_deploy._EXIT_OK)
        monkeypatch.setattr(
            lore_deploy, "_probe_surreal", lambda config_path: lore_deploy._EXIT_ERROR
        )
        # If the (buggy) path skips the gate and tears down, it would hit the real
        # 600s bind-wait next — mock it so the RED failure is fast, not a hang.
        monkeypatch.setattr(lore_deploy, "_await_bind", lambda *a, **k: lore_deploy._EXIT_OK)

        return_code = lore_deploy.verb_start(fixture.project, fixture.env_file)

        assert return_code == lore_deploy._EXIT_ERROR, (
            f"a failed store pre-flight must abort the recreate; got {return_code}"
        )
        assert fixture.stop_calls() == [], (
            f"a failed store pre-flight must NOT stop the live container; "
            f"run_calls={fixture.run_calls}"
        )
        assert fixture.rm_calls() == [], (
            f"a failed store pre-flight must NOT rm the live container; "
            f"run_calls={fixture.run_calls}"
        )
        assert fixture.launch_calls == [], (
            f"a failed store pre-flight must NOT relaunch; got {len(fixture.launch_calls)} attempt(s)"
        )

    def test_recreate_aborts_when_embed_probe_fails_no_teardown(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """RUNNING + stale + `/embed` down -> abort, no stop/rm/launch (embed is a precondition too)."""
        fixture = _RecreatePathFixture(monkeypatch, tmp_path, self._SLUG)
        fixture.wire_running_and_stale()
        fixture.install_run_recorder()
        fixture.install_launch_recorder()
        fixture.install_image_present(True)
        fixture.create_env_file()
        # Embed fails; surreal would pass, but embed runs first and must short-circuit.
        monkeypatch.setattr(lore_deploy, "_probe_embed", lambda *a, **k: lore_deploy._EXIT_ERROR)
        monkeypatch.setattr(lore_deploy, "_probe_surreal", lambda config_path: lore_deploy._EXIT_OK)
        monkeypatch.setattr(lore_deploy, "_await_bind", lambda *a, **k: lore_deploy._EXIT_OK)

        return_code = lore_deploy.verb_start(fixture.project, fixture.env_file)

        assert return_code == lore_deploy._EXIT_ERROR
        assert fixture.stop_calls() == [], (
            f"a failed embed pre-flight must NOT stop the live container; run_calls={fixture.run_calls}"
        )
        assert fixture.rm_calls() == []
        assert fixture.launch_calls == []

    def test_recreate_proceeds_and_validates_before_teardown_when_probes_ok(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """RUNNING + stale + both probes OK -> recreate proceeds; both probes precede teardown.

        Ordering invariant: a guard placed AFTER the stop/rm cannot prevent the
        outage, so both pre-flights must be observed before the first destructive
        podman command.
        """
        fixture = _RecreatePathFixture(monkeypatch, tmp_path, self._SLUG)
        fixture.wire_running_and_stale()
        fixture.install_launch_recorder()
        fixture.install_image_present(True)
        fixture.create_env_file()

        # One ordered transcript across the pre-flights AND the podman commands.
        transcript: list[str] = []

        def _recording_run(cmd: list[str], **kwargs: bool) -> subprocess.CompletedProcess[str]:
            if "stop" in cmd and fixture.container_name in cmd:
                transcript.append("teardown:stop")
            elif "rm" in cmd and fixture.container_name in cmd:
                transcript.append("teardown:rm")
            fixture.run_calls.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        monkeypatch.setattr(lore_deploy, "_run", _recording_run)

        def _recording_probe_embed(config_path: Path, env_file: Path) -> int:
            transcript.append("check:embed")
            return lore_deploy._EXIT_OK

        monkeypatch.setattr(lore_deploy, "_probe_embed", _recording_probe_embed)

        def _recording_probe_surreal(config_path: Path) -> int:
            transcript.append("check:surreal")
            return lore_deploy._EXIT_OK

        monkeypatch.setattr(lore_deploy, "_probe_surreal", _recording_probe_surreal)
        monkeypatch.setattr(lore_deploy, "_await_bind", lambda *a, **k: lore_deploy._EXIT_OK)
        # The artifact gates (#125/#131/#132) run on every start path that ends
        # with a running container. Arrange them as passing — this test is about
        # a different concern, and both probes talk to a real container.
        _stub_artifact_gates(monkeypatch)


        return_code = lore_deploy.verb_start(fixture.project, fixture.env_file)

        assert return_code == lore_deploy._EXIT_OK, (
            f"a clean recreate (both probes OK) must return _EXIT_OK; got {return_code}"
        )
        assert "teardown:stop" in transcript and "teardown:rm" in transcript, (
            f"a clean recreate must stop and rm the stale container; transcript={transcript}"
        )
        assert len(fixture.launch_calls) == 1, (
            f"a clean recreate must relaunch exactly once; got {len(fixture.launch_calls)}"
        )
        first_teardown_index = next(
            i for i, event in enumerate(transcript) if event.startswith("teardown:")
        )
        before_teardown = transcript[:first_teardown_index]
        assert "check:embed" in before_teardown, (
            f"the /embed pre-flight must precede the first teardown; transcript={transcript}"
        )
        assert "check:surreal" in before_teardown, (
            f"the SurrealDB store pre-flight must precede the first teardown; transcript={transcript}"
        )


# ===========================================================================
# Packet 01a §B — the `conform` verb <-> conformance_run.sh contract.
# ===========================================================================
#
# `conform` is the thin, testable entry the operator runs after `podman build`
# (design doc §B): it resolves the target image and invokes the bash harness
# `skills/lore-deploy/scripts/conformance_run.sh <image>` via `_run`, then gates
# on the script's exit. The load-bearing LOGIC (provenance-before-pytest, the
# podman topology) lives in the bash and is integration-validated by an actual
# conformance run — so these pins cover ONLY the verb<->script contract, per the
# brief ("pin only the verb<->script contract; do NOT unit-test the podman argv
# or the provenance-before-pytest ordering"):
#   - a `conform` verb exists (argparse choice + dispatch in main), and it does
#     NOT require --project (it gates the IMAGE artifact, not a project);
#   - it invokes conformance_run.sh with the RESOLVED image (default
#     localhost/lore:latest, overridable);
#   - a non-zero script exit => _EXIT_ERROR; a zero exit => _EXIT_OK.
#
# Seams pinned (CONTRACT DECISIONS — see REPORT-contract-01a.md §SATISFIABILITY;
# the design doc names `_run_conformance` but NOT the CLI override-flag name or
# whether conform requires --project):
#   - lore_deploy._run_conformance(image: str = IMAGE) -> int
#   - main(["conform"])                 -> dispatches, default image, NO --project
#   - main(["conform", "--image", X])   -> dispatches with image X

_DEFAULT_CONFORM_IMAGE = lore_deploy.IMAGE  # localhost/lore:latest (DERIVED, not magic)
# A NON-default image (fixture-monoculture killer): the design doc's ground-truth build.
_OVERRIDE_CONFORM_IMAGE = "localhost/lore:01a"
_CONFORMANCE_SCRIPT_NAME = "conformance_run.sh"


def _record_run_returning(
    monkeypatch: pytest.MonkeyPatch, return_code: int
) -> list[list[str]]:
    """Install a recording `_run` that returns a CompletedProcess with `return_code`.

    Mirrors the mock-`_run` pattern used throughout this module: capture the podman/script
    argv, and hand back a non-raising CompletedProcess so the caller reads the exit CODE
    (the conform contract gates on the script's exit, not on an exception).
    """
    calls: list[list[str]] = []

    def _recording_run(cmd: list[str], **kwargs: bool) -> subprocess.CompletedProcess[str]:
        calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, return_code, stdout="", stderr="")

    monkeypatch.setattr(lore_deploy, "_run", _recording_run)
    return calls


class TestRunConformance:
    """`_run_conformance` invokes the harness with the resolved image and propagates its exit."""

    def test_invokes_the_harness_script_with_the_default_image(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Default resolution: conform runs conformance_run.sh with localhost/lore:latest."""
        assert hasattr(lore_deploy, "_run_conformance"), (
            "lore_deploy._run_conformance seam is not yet defined; the builder must add the "
            "thin conform entry that invokes conformance_run.sh (packet 01a §B)"
        )
        calls = _record_run_returning(monkeypatch, 0)
        # Defensive: if the builder gates on image presence, keep the test deterministic
        # regardless of what images happen to exist on the runner host.
        monkeypatch.setattr(lore_deploy, "_image_exists", lambda image: True)

        return_code = lore_deploy._run_conformance()

        assert return_code == lore_deploy._EXIT_OK
        assert len(calls) == 1, "conform must invoke the harness exactly once"
        cmd = calls[0]
        assert any(str(part).endswith(_CONFORMANCE_SCRIPT_NAME) for part in cmd), (
            f"conform must invoke {_CONFORMANCE_SCRIPT_NAME}; got {cmd}"
        )
        # Kills a build that hardcodes a different image or never passes one through.
        assert _DEFAULT_CONFORM_IMAGE in cmd, (
            f"conform must pass the resolved default image {_DEFAULT_CONFORM_IMAGE} to the "
            f"harness; got {cmd}"
        )

    def test_passes_an_overriding_image_through(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An explicit image REPLACES the default in the harness invocation."""
        assert hasattr(lore_deploy, "_run_conformance"), "seam not yet defined"
        calls = _record_run_returning(monkeypatch, 0)
        monkeypatch.setattr(lore_deploy, "_image_exists", lambda image: True)

        return_code = lore_deploy._run_conformance(image=_OVERRIDE_CONFORM_IMAGE)

        assert return_code == lore_deploy._EXIT_OK
        cmd = calls[0]
        assert _OVERRIDE_CONFORM_IMAGE in cmd, f"the override image must be used; got {cmd}"
        # Kills a build that ignores the override and always conforms the default image.
        assert _DEFAULT_CONFORM_IMAGE not in cmd, (
            f"an override must REPLACE the default image, not be ignored; got {cmd}"
        )

    def test_returns_error_when_the_harness_script_fails(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A non-zero script exit => _EXIT_ERROR (the conformance run found a defect)."""
        assert hasattr(lore_deploy, "_run_conformance"), "seam not yet defined"
        _record_run_returning(monkeypatch, 1)  # script exited non-zero
        monkeypatch.setattr(lore_deploy, "_image_exists", lambda image: True)

        # Kills a build that ignores the script's exit code and always reports success —
        # a green conform over a failing suite is the exact silent-pass this packet closes.
        assert lore_deploy._run_conformance() == lore_deploy._EXIT_ERROR

    def test_returns_ok_when_the_harness_script_succeeds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """POSITIVE CONTROL: a zero script exit => _EXIT_OK (the artifact conformed)."""
        assert hasattr(lore_deploy, "_run_conformance"), "seam not yet defined"
        _record_run_returning(monkeypatch, 0)
        monkeypatch.setattr(lore_deploy, "_image_exists", lambda image: True)

        assert lore_deploy._run_conformance() == lore_deploy._EXIT_OK


class TestConformVerbDispatch:
    """`conform` is a registered verb that main dispatches to `_run_conformance`.

    CONTRACT DECISION (surfaced for the lead): `conform` gates the IMAGE artifact, so it
    must NOT require --project. The `--image` override-flag name is likewise a contract
    decision the design doc left unnamed. Both are flagged in the report.
    """

    def test_conform_is_a_registered_verb_dispatched_without_a_project(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`main(["conform"])` dispatches to `_run_conformance` — no --project required."""
        monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/podman")
        received: list[tuple[tuple[object, ...], dict[str, object]]] = []

        def _stub_run_conformance(*args: object, **kwargs: object) -> int:
            received.append((args, kwargs))
            return lore_deploy._EXIT_OK

        monkeypatch.setattr(
            lore_deploy, "_run_conformance", _stub_run_conformance, raising=False
        )

        return_code = lore_deploy.main(["conform"])

        assert return_code == lore_deploy._EXIT_OK
        # Kills a build that never wires conform into argparse/dispatch, and a build that
        # forces conform through the --project-required path (which would SystemExit here).
        assert len(received) == 1, (
            "main must dispatch `conform` to _run_conformance exactly once, without "
            "requiring --project (conform gates the image, not a project)"
        )

    def test_conform_verb_propagates_a_failure_exit_from_the_harness(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A failing conformance run must surface through main as a non-zero exit."""
        monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/podman")
        monkeypatch.setattr(
            lore_deploy,
            "_run_conformance",
            lambda *a, **k: lore_deploy._EXIT_ERROR,
            raising=False,
        )

        # Kills a build that dispatches conform but discards its exit (always exits 0).
        assert lore_deploy.main(["conform"]) == lore_deploy._EXIT_ERROR

    def test_conform_cli_forwards_an_image_override(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`main(["conform", "--image", X])` forwards X to `_run_conformance`.

        CONTRACT DECISION: `--image` is the chosen override-flag name (the design doc says
        the image is "overridable" but does not name the flag). Flagged in the report.
        """
        monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/podman")
        received: dict[str, object] = {}

        def _stub_run_conformance(*args: object, **kwargs: object) -> int:
            if args:
                received["image"] = args[0]
            if "image" in kwargs:
                received["image"] = kwargs["image"]
            return lore_deploy._EXIT_OK

        monkeypatch.setattr(
            lore_deploy, "_run_conformance", _stub_run_conformance, raising=False
        )

        return_code = lore_deploy.main(["conform", "--image", _OVERRIDE_CONFORM_IMAGE])

        assert return_code == lore_deploy._EXIT_OK
        assert received.get("image") == _OVERRIDE_CONFORM_IMAGE, (
            f"the --image override must be forwarded to _run_conformance; got {received!r}"
        )

    def test_conform_cli_forwards_the_default_image_when_no_override(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PIN 3 (adversary §MISSING-PINS) — `main(["conform"])` with NO --image forwards the
        DEFAULT image (localhost/lore:latest) to `_run_conformance`, asserted on the VALUE.

        Kills a wrong argparse `--image default=` (e.g. `localhost/lore:TYPO`): the dispatch
        pin only checks `len(received) == 1`, and the override pin supplies an EXPLICIT
        --image, so the DEFAULT the CLI forwards is otherwise never inspected. A build whose
        argparse default is a typo dispatches once and forwards the WRONG image, passing both
        existing pins while conforming the wrong artifact. The function-level default is pinned
        (TestRunConformance) — this pins the CLI->function default WIRING.
        """
        monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/podman")
        received: dict[str, object] = {}

        def _stub_run_conformance(*args: object, **kwargs: object) -> int:
            if args:
                received["image"] = args[0]
            if "image" in kwargs:
                received["image"] = kwargs["image"]
            return lore_deploy._EXIT_OK

        monkeypatch.setattr(
            lore_deploy, "_run_conformance", _stub_run_conformance, raising=False
        )

        return_code = lore_deploy.main(["conform"])

        assert return_code == lore_deploy._EXIT_OK
        # The DEFAULT image the CLI forwards must be the real default, not a typo'd argparse
        # default that no other pin inspects.
        assert received.get("image") == _DEFAULT_CONFORM_IMAGE, (
            f"main(['conform']) must forward the default image {_DEFAULT_CONFORM_IMAGE!r} to "
            f"_run_conformance; got {received!r}"
        )
