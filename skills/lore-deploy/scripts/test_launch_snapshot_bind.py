"""Contract: lore-deploy binds the static snapshot where the SERVER reads it (lore #165).

The served lore container reads its static-tier snapshot from exactly one place:
``loremaster.server._DEFAULT_SNAPSHOT_ROOT`` (``Path.home()/docker/mcp/lore-snapshot``,
evaluated with ``HOME=/home/lore`` inside the container). Its boot guard
(``Indexer._snapshot_materialized``) reads False for any tier whose snapshot is not
there, re-acquires, and crashes boot. Binding the host snapshot anywhere else (the
retired ``/source``) is the same as not binding it.

Pins (PLAN-165-fix.md §Contract, receipts dir ``docs/plans/v2/receipts/2026-10-31-165/``):

1. Derived target. With >=1 static root, exactly one snapshot bind, at the container
   path DERIVED from ``loremaster.server._DEFAULT_SNAPSHOT_ROOT`` (never retyped), and
   read-only. No bind targets ``/source``.
2. Artifact pin. The exact command the REAL ``_launch_container`` builds over the REAL
   repo ``lore.yaml``, run as a one-shot against the REAL image, makes the REAL guard
   read True for every static tier. Control: the same guard over an unbound path reads
   False. Missing podman / image / host snapshot FAILS, never skips.
3. No static roots -> no snapshot bind of any kind, and the launch still happens.
4. Static roots + host snapshot absent -> the launch is refused with a teaching error
   naming the missing host path and the cold-index remedy; no podman command is issued.
   Placement per RULING-F1-pin4.md (same receipts dir): (c)(i) ``_launch_container``
   raises ``RuntimeError``; (c)(ii) ``verb_start`` refuses on BOTH start paths before any
   stop/rm/launch, returning ``_EXIT_ERROR`` with the teaching text on stderr; R1 one
   shared launch-precondition check decides both levels (pinned as agreement over a
   cell matrix); R2 a config-read failure aborts the recreate before teardown.

Config fixtures are DERIVED from the real repo ``lore.yaml`` (roots filtered), and
``_read_config_field`` runs for real over them, so the static-root count crosses the
real host->loremaster seam instead of a stubbed expression string.

Follow-up round (RULING-A1-A8-T1.md, same receipts dir):

- A1: after the recreate's teardown, EVERY failure type ``_launch_container`` documents
  (``RuntimeError`` from the re-check or the config read, ``CalledProcessError`` from
  ``podman run``) degrades to ``_EXIT_ERROR`` with the error's own text on stderr.
- A8: the remedy names the interpreter lore-deploy itself uses for loremaster
  (``_loremaster_python()``), never bare ``python``; every test here runs under a
  DISTINCT interpreter spelling so a build that types any other interpreter fails.
- T1: tiers and dirs are matched as whole tokens / path components, so a tier that is a
  prefix of another (``surrealdb`` vs ``surrealdb-docs``) can neither false-fail the
  healthy check nor vacuously satisfy the failing check.
"""

from __future__ import annotations

import json
import re
import shlex
import shutil
import subprocess
import textwrap
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import Any, cast

import lore_deploy
import pytest
import yaml
from loremaster.config import LoreConfig
from loremaster.index.indexer import Indexer
from loremaster.source.snapshot import TIER_SUBDIRS, SnapshotLayout

import loremaster
from loremaster import server

# --- Shared conventions, from the same source of truth as production -------------

# The workspace root that ships the loremaster under test (derived from the package
# location, so it also holds when this file runs from a scratch copy of the skill).
REPO_ROOT = Path(loremaster.__file__).resolve().parents[2]
REPO_CONFIG = REPO_ROOT / "lore.yaml"

# Where the server reads the snapshot INSIDE the container: the container's HOME plus
# the server default root's path under the host HOME. Derived, never retyped, so this
# moves when the server's default moves.
CONTAINER_SNAPSHOT_TARGET = str(
    PurePosixPath(lore_deploy.CONTAINER_HOME)
    / server._DEFAULT_SNAPSHOT_ROOT.relative_to(Path.home()).as_posix()
)
# The retired target (#165): zero readers in the server; binding there is a silent miss.
RETIRED_SNAPSHOT_TARGET = "/source"

# Artifact-pin knobs.
PROBE_TIMEOUT_S = 240
# A path no lore-deploy command binds: the control leg of the in-image guard.
UNBOUND_CONTROL_ROOT = "/nonexistent-snapshot-control-165"
CONTAINER_PYTHON = "/app/.venv/bin/python"

_REAL_RUN = lore_deploy._run


def _cold_index_command(config_path: Path) -> str:
    """The paste-ready cold-index remedy for THIS config (amendment r2 item 3, amended by A8).

    The interpreter is the one lore-deploy itself runs loremaster with, read from
    production ``_loremaster_python()`` and never retyped: bare ``python`` is not
    guaranteed to import loremaster on the operator's shell (RULING-A1-A8-T1 A8).
    """
    return f"{lore_deploy._loremaster_python()} -m loremaster.index --config {config_path}"


@pytest.fixture(autouse=True)
def _distinct_loremaster_interpreter(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Run every test under a loremaster interpreter spelled unlike any default (A8).

    ``LORE_PYTHON`` is production's documented override. It points at a wrapper that
    execs the interpreter ``_loremaster_python()`` resolved BEFORE this fixture (so a
    scratch copy's own ``LORE_PYTHON`` still wins), which keeps the real config reader
    working while making the path differ from ``sys.executable``, from the workspace
    ``.venv`` default and from bare ``python``. A remedy built from any of those, rather
    than from ``_loremaster_python()``, then fails the remedy assertions.
    """
    resolved_interpreter = lore_deploy._loremaster_python()
    wrapper = tmp_path / "loremaster-interpreter" / "lore-python"
    wrapper.parent.mkdir()
    wrapper.write_text(f'#!/bin/sh\nexec {shlex.quote(resolved_interpreter)} "$@"\n', encoding="utf-8")
    wrapper.chmod(0o755)
    monkeypatch.setenv("LORE_PYTHON", str(wrapper))
    return wrapper


# Where a named path or tier ENDS in served prose: end of text, whitespace, a list or
# quote delimiter, or a sentence-final period. ``-``, ``/``, ``.`` + word char and word
# characters continue the name, so ``<root>/surrealdb`` is not named by
# ``<root>/surrealdb-docs`` (T1).
_NAME_END = r"(?=$|[\s;,:'\"`)\]]|\.(?:\s|$))"
_NAME_START = r"(?<![\w./-])"


def _names_path(text: str, path: str) -> bool:
    """True iff ``text`` names ``path`` as a whole path, never as a prefix of a longer one."""
    return re.search(f"{_NAME_START}{re.escape(path)}{_NAME_END}", text) is not None


def _names_tier(text: str, tier: str) -> bool:
    """True iff ``text`` names ``tier`` as a standalone token (not inside a path or a longer tier)."""
    return re.search(f"{_NAME_START}{re.escape(tier)}{_NAME_END}", text) is not None


# --- Helpers ----------------------------------------------------------------------


def _repo_config_document() -> dict[str, Any]:
    """Load the real repo lore.yaml (fail loud if absent; never skip)."""
    if not REPO_CONFIG.is_file():
        pytest.fail(f"real repo config {REPO_CONFIG} is absent; the contract derives fixtures from it")
    document: dict[str, Any] = yaml.safe_load(REPO_CONFIG.read_text(encoding="utf-8"))
    return document


def _static_tiers(document: dict[str, Any]) -> list[str]:
    """Static tier names declared in a lore.yaml document (independent of loremaster)."""
    return [root["tier"] for root in document["roots"] if root.get("watch") == "static"]


def _write_derived_project(tmp_path: Path, static_root_count: int) -> tuple[Path, Path]:
    """Create a project whose lore.yaml is the REAL config with only N static roots kept.

    Returns ``(project_dir, config_path)``. The live root is always kept, so
    ``static_root_count == 0`` is a realistic live-only project.
    """
    document = _repo_config_document()
    live_roots = [root for root in document["roots"] if root.get("watch") != "static"]
    static_roots = [root for root in document["roots"] if root.get("watch") == "static"]
    assert len(static_roots) >= static_root_count, (
        f"repo lore.yaml declares {len(static_roots)} static roots; fixture wants {static_root_count}"
    )
    document["roots"] = live_roots + static_roots[:static_root_count]
    project = tmp_path / "lore"
    project.mkdir()
    config_path = project / "lore.yaml"
    config_path.write_text(yaml.safe_dump(document), encoding="utf-8")
    return project, config_path


def _make_host_snapshot(tmp_path: Path, tiers: list[str]) -> Path:
    """A host snapshot root shaped like the real one: one non-empty dir per static tier."""
    snapshot_root = tmp_path / "docker" / "mcp" / "lore-snapshot"
    for tier in tiers:
        # Placed where the PRODUCTION layout puts the tier, never a retyped ``root/tier``.
        tier_dir = SnapshotLayout(snapshot_root).materialization_dir(tier)
        tier_dir.mkdir(parents=True)
        (tier_dir / "index.mdx").write_text("# materialised\n", encoding="utf-8")
    return snapshot_root


def _install_podman_recorder(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Record every podman command ``_run`` is asked to execute; pass others through.

    Non-podman calls (the real ``_read_config_field`` subprocess into the loremaster
    venv) run for real, so the static-root count crosses the real seam.
    """
    podman_calls: list[list[str]] = []

    def _recording_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if cmd and cmd[0] == "podman":
            podman_calls.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return _REAL_RUN(cmd, **kwargs)

    monkeypatch.setattr(lore_deploy, "_run", _recording_run)
    return podman_calls


def _bind_mounts(cmd: list[str]) -> list[tuple[str, str, str]]:
    """Every bind mount in a podman argv as ``(host, target, options)``.

    Accepts ``-v X`` / ``--volume X`` / ``-v=X`` / ``--volume=X`` and
    ``--mount type=bind,source=..,target=..[,readonly]`` so the pins hold on the
    mount's MEANING, not on which podman spelling the build chose.
    """
    mounts: list[tuple[str, str, str]] = []
    index = 0
    while index < len(cmd):
        token = cmd[index]
        value: str | None = None
        kind = ""
        for flag, flag_kind in (("-v", "volume"), ("--volume", "volume"), ("--mount", "mount")):
            if token == flag and index + 1 < len(cmd):
                value, kind = cmd[index + 1], flag_kind
                index += 1
            elif token.startswith(f"{flag}="):
                value, kind = token[len(flag) + 1 :], flag_kind
        if value is not None and kind == "volume":
            parts = value.split(":")
            host, target = parts[0], parts[1] if len(parts) > 1 else ""
            mounts.append((host, target, ":".join(parts[2:])))
        elif value is not None and kind == "mount":
            fields = dict(
                item.partition("=")[::2] if "=" in item else (item, "true") for item in value.split(",")
            )
            host = fields.get("source", fields.get("src", ""))
            target = fields.get("target", fields.get("destination", fields.get("dst", "")))
            options = "ro" if fields.get("readonly", fields.get("ro")) in ("true", "1") else ""
            mounts.append((host, target, options))
        index += 1
    return mounts


def _single_launch(podman_calls: list[list[str]]) -> list[str]:
    """The one ``podman run`` command a launch issued."""
    runs = [call for call in podman_calls if call[:2] == ["podman", "run"]]
    assert len(runs) == 1, f"a launch must issue exactly one `podman run`; got {podman_calls}"
    return runs[0]


def _snapshot_binds(cmd: list[str], host_snapshot: Path) -> list[tuple[str, str, str]]:
    """Binds that carry the snapshot: sourced from the host snapshot, or aimed at a snapshot target."""
    snapshot_targets = {CONTAINER_SNAPSHOT_TARGET, RETIRED_SNAPSHOT_TARGET}
    return [
        mount
        for mount in _bind_mounts(cmd)
        if Path(mount[0]) == host_snapshot or mount[1].rstrip("/") in snapshot_targets
    ]


def _launch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    static_root_count: int,
    snapshot_present: bool,
) -> tuple[Callable[[], None], list[list[str]], Path, Path]:
    """Arrange a derived project + host snapshot; return (act, podman_calls, snapshot, config)."""
    project, config_path = _write_derived_project(tmp_path, static_root_count)
    tiers = _static_tiers(yaml.safe_load(config_path.read_text(encoding="utf-8")))
    if snapshot_present:
        host_snapshot = _make_host_snapshot(tmp_path, tiers or ["surrealdb-docs"])
    else:
        host_snapshot = tmp_path / "docker" / "mcp" / "lore-snapshot"
        assert not host_snapshot.exists()
    monkeypatch.setattr(lore_deploy, "SNAPSHOT_ROOT", host_snapshot)
    podman_calls = _install_podman_recorder(monkeypatch)
    env_file = tmp_path / "lore.env"
    env_file.write_text("", encoding="utf-8")

    def act() -> None:
        lore_deploy._launch_container(project, config_path, env_file)

    return act, podman_calls, host_snapshot, config_path


# --- Pin 1: derived target ----------------------------------------------------------


class TestStaticRootsBindSnapshotAtServerDefaultRoot:
    """With >=1 static root, the snapshot is bound once, read-only, where the server reads it."""

    @pytest.mark.parametrize("static_root_count", [1, 3])
    def test_static_roots_bind_host_snapshot_once_at_server_default_root(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, static_root_count: int
    ) -> None:
        """1 (the boundary) and 3 (the real repo) static roots: one bind, derived target, ro."""
        act, podman_calls, host_snapshot, _ = _launch(
            monkeypatch, tmp_path, static_root_count=static_root_count, snapshot_present=True
        )

        act()

        cmd = _single_launch(podman_calls)
        binds = _snapshot_binds(cmd, host_snapshot)
        assert len(binds) == 1, (
            f"exactly one snapshot bind expected with {static_root_count} static root(s); got {binds}"
        )
        host, target, options = binds[0]
        assert Path(host) == host_snapshot, (
            f"the bind must carry the host snapshot {host_snapshot}; got {host}"
        )
        assert target.rstrip("/") == CONTAINER_SNAPSHOT_TARGET, (
            f"the snapshot must land where loremaster.server reads it ({CONTAINER_SNAPSHOT_TARGET}); "
            f"got {target!r}"
        )
        # The snapshot is host-owned (the host cold index writes it); the container only reads.
        assert "ro" in options.split(","), f"the snapshot bind must be read-only; options={options!r}"

    def test_no_bind_targets_the_retired_source_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """REPLACED, not supplemented (operator ruling): nothing is bound at /source."""
        act, podman_calls, _, _ = _launch(monkeypatch, tmp_path, static_root_count=3, snapshot_present=True)

        act()

        cmd = _single_launch(podman_calls)
        retired = [
            mount
            for mount in _bind_mounts(cmd)
            if mount[1].rstrip("/") == RETIRED_SNAPSHOT_TARGET
            or mount[1].startswith(f"{RETIRED_SNAPSHOT_TARGET}/")
        ]
        assert retired == [], (
            f"no bind may target {RETIRED_SNAPSHOT_TARGET} (0 server readers); got {retired}"
        )


# --- Pin 3: no static roots -> no snapshot bind ---------------------------------------


class TestLiveOnlyProjectHasNoSnapshotBind:
    """A live-only project launches with no snapshot bind, whether or not a host snapshot exists."""

    @pytest.mark.parametrize("snapshot_present", [True, False])
    def test_live_only_project_launches_without_any_snapshot_bind(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, snapshot_present: bool
    ) -> None:
        """Zero static roots: one podman run, no bind of the snapshot or at a snapshot target.

        The ``snapshot_present=False`` leg also pins that pin 4's refusal is scoped to
        static roots: a live-only project on a host with no snapshot still launches.
        """
        act, podman_calls, host_snapshot, _ = _launch(
            monkeypatch, tmp_path, static_root_count=0, snapshot_present=snapshot_present
        )

        act()

        cmd = _single_launch(podman_calls)
        assert _snapshot_binds(cmd, host_snapshot) == [], (
            f"a live-only project must carry no snapshot bind; got {_snapshot_binds(cmd, host_snapshot)}"
        )


# --- Pin 4: static roots + missing host snapshot -> refused ---------------------------


class TestMissingHostSnapshotRefusesLaunch:
    """Static roots with no host snapshot would boot-crash; refuse before any podman call.

    Level (c)(i) of RULING-F1-pin4.md: ``_launch_container`` raises ``RuntimeError``, the
    type it already raises via ``_read_config_field``.
    """

    def test_static_roots_with_absent_host_snapshot_refuse_without_podman(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Raises, names the missing host path and the cold-index remedy, issues no podman command."""
        act, podman_calls, host_snapshot, config_path = _launch(
            monkeypatch, tmp_path, static_root_count=3, snapshot_present=False
        )

        with pytest.raises(RuntimeError) as refusal:
            act()

        message = str(refusal.value)
        assert str(host_snapshot) in message, f"the refusal must name the missing host path; got {message!r}"
        _assert_teaches_every_failing_tier(message, config_path, host_snapshot, failing=None)
        assert podman_calls == [], f"a refused launch must issue no podman command; got {podman_calls}"


# --- Pin 4 (c)(ii), R1, R2: verb_start refuses BEFORE any teardown or launch ------------


class _VerbStartArrangement:
    """verb_start on a derived project, with the REAL config reader and every network probe stubbed.

    Reuses ``test_lore_deploy._RecreatePathFixture`` for the stale-image wiring and the
    launch recorder (one source of truth for the recreate-path seams), then restores the
    REAL ``_read_config_field`` (the fixture stubs it to "0 static roots") and records
    podman commands through a pass-through ``_run`` so the reader's subprocess runs.
    The bind-wait, artifact gates and .mcp.json merge are stubbed so that a build that
    wrongly proceeds to launch returns quickly instead of polling a port for 600s.
    """

    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        *,
        path: str,
        static_root_count: int,
        snapshot_state: str,
    ) -> None:
        from test_lore_deploy import _RecreatePathFixture  # reuse, never clone, the recreate seams

        self.fixture = _RecreatePathFixture(monkeypatch, tmp_path, "lore")
        if path == "recreate":
            self.fixture.wire_running_and_stale()
        else:
            monkeypatch.setattr(lore_deploy, "_container_state", lambda name: None)
        monkeypatch.setattr(lore_deploy, "_read_config_field", _REAL_READ_CONFIG_FIELD)
        document = _repo_config_document()
        live = [root for root in document["roots"] if root.get("watch") != "static"]
        static = [root for root in document["roots"] if root.get("watch") == "static"]
        document["roots"] = live + static[:static_root_count]
        self.config_path = self.fixture.project / "lore.yaml"
        self.config_path.write_text(yaml.safe_dump(document), encoding="utf-8")
        self.host_snapshot = _arrange_snapshot_state(
            tmp_path, _static_tiers(document) or ["surrealdb-docs"], snapshot_state
        )
        monkeypatch.setattr(lore_deploy, "SNAPSHOT_ROOT", self.host_snapshot)
        self.fixture.create_env_file()
        self.fixture.install_image_present(True)
        self.fixture.install_launch_recorder()

        def _recording_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            if cmd and cmd[0] == "podman":
                self.fixture.run_calls.append(list(cmd))
                return subprocess.CompletedProcess(cmd, 0, "", "")
            return _REAL_RUN(cmd, **kwargs)

        monkeypatch.setattr(lore_deploy, "_run", _recording_run)
        for probe in ("_probe_embed", "_probe_surreal", "_await_bind", "_gate_artifact"):
            monkeypatch.setattr(lore_deploy, probe, lambda *a, **k: lore_deploy._EXIT_OK)
        monkeypatch.setattr(
            lore_deploy, "_merge_mcp_from_config", lambda *a, **k: lore_deploy.DEFAULT_PORT_BASE
        )

    def run_verb_start(self) -> int:
        """Act; a raise out of verb_start is itself a contract failure (outage-guard shape)."""
        try:
            return lore_deploy.verb_start(self.fixture.project, self.fixture.env_file, no_wait=True)
        except RuntimeError as error:
            pytest.fail(
                f"verb_start must refuse with _EXIT_ERROR, not raise; raised {error!r} after "
                f"podman calls {self.fixture.run_calls} and launches {self.fixture.launch_calls}"
            )

    def podman_runs(self) -> list[list[str]]:
        """``podman run`` commands issued."""
        return [call for call in self.fixture.run_calls if call[:2] == ["podman", "run"]]


_REAL_READ_CONFIG_FIELD = lore_deploy._read_config_field


def _arrange_snapshot_state(tmp_path: Path, tiers: list[str], snapshot_state: str) -> Path:
    """Arrange the host snapshot root in one named state.

    ``present`` (every tier materialised, real shape) · ``absent`` (no root) · ``file`` (a
    regular file at the root, S2) · ``tier_absent`` / ``tier_empty`` (root present, the FIRST
    static tier's materialisation dir missing / empty, S1).
    """
    host_snapshot = tmp_path / "docker" / "mcp" / "lore-snapshot"
    if snapshot_state in ("present", "tier_absent", "tier_empty"):
        _make_host_snapshot(tmp_path, tiers)
        first_tier_dir = SnapshotLayout(host_snapshot).materialization_dir(tiers[0])
        if snapshot_state != "present":
            shutil.rmtree(first_tier_dir)
        if snapshot_state == "tier_empty":
            first_tier_dir.mkdir()
    elif snapshot_state == "file":
        host_snapshot.parent.mkdir(parents=True)
        host_snapshot.write_text("not a snapshot dir\n", encoding="utf-8")
    elif snapshot_state != "absent":
        raise ValueError(f"unknown snapshot state {snapshot_state!r}")
    return host_snapshot


def _assert_teaches_every_failing_tier(
    text: str, config_path: Path, host_snapshot: Path, *, failing: list[str] | None
) -> None:
    """The refusal names each failing tier and its HOST dir, and the paste-ready remedy (RULING-S1-S2).

    ``failing=None`` means every static tier the config declares. Healthy tiers' dirs must
    NOT be named: a refusal that lists everything teaches nothing about which tier is broken.
    """
    tiers = _static_tiers(yaml.safe_load(config_path.read_text(encoding="utf-8")))
    failing_tiers = tiers if failing is None else failing
    layout = SnapshotLayout(host_snapshot)
    # Whole-token / whole-path matching (T1): a substring test false-fails the healthy
    # check, and vacuously passes the failing check, whenever one tier prefixes another.
    for tier in failing_tiers:
        tier_dir = str(layout.materialization_dir(tier))
        assert _names_tier(text, tier) and _names_path(text, tier_dir), (
            f"refusal must name failing tier {tier} at {tier_dir}; got {text!r}"
        )
    for tier in set(tiers) - set(failing_tiers):
        healthy_dir = str(layout.materialization_dir(tier))
        assert not _names_path(text, healthy_dir), (
            f"refusal must not name healthy tier dir {healthy_dir}; got {text!r}"
        )
    assert _cold_index_command(config_path) in text, (
        f"refusal must carry the paste-ready remedy `{_cold_index_command(config_path)}`; got {text!r}"
    )


def _server_guard_reads_materialised(config_path: Path, snapshot_root: Path, tier: str) -> bool:
    """The REAL server boot guard ``Indexer._snapshot_materialized``, through the real ``Indexer.__init__``.

    ``__init__`` only stores its collaborators, and the guard reads none of them but the
    snapshot layout, so placeholders stand in for the store, embedder, manifest and registry.
    """
    config = LoreConfig.model_validate(yaml.safe_load(config_path.read_text(encoding="utf-8")))
    placeholder = cast(Any, None)
    indexer = Indexer(
        store=placeholder,
        embedder=placeholder,
        manifest=placeholder,
        registry=placeholder,
        source_providers=[],
        config=config,
        snapshot_root=snapshot_root,
    )
    return indexer._snapshot_materialized(tier)


class TestVerbStartRefusesMissingSnapshotBeforeTeardown:
    """(c)(ii): the snapshot precondition is checked with the other pre-teardown preconditions."""

    @pytest.mark.parametrize("path", ["fresh", "recreate"])
    def test_static_roots_with_absent_snapshot_return_error_with_no_destructive_podman(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str], path: str
    ) -> None:
        """Both start paths: _EXIT_ERROR, teaching stderr, no stop/rm, no launch, no podman run."""
        arrangement = _VerbStartArrangement(
            monkeypatch, tmp_path, path=path, static_root_count=3, snapshot_state="absent"
        )

        return_code = arrangement.run_verb_start()

        assert return_code == lore_deploy._EXIT_ERROR, f"{path}: must return _EXIT_ERROR; got {return_code}"
        # The outage guard (B1/B2 shape): a refused recreate leaves the serving container alone.
        assert arrangement.fixture.stop_calls() == [], f"{path}: no stop; got {arrangement.fixture.run_calls}"
        assert arrangement.fixture.rm_calls() == [], f"{path}: no rm; got {arrangement.fixture.run_calls}"
        assert arrangement.fixture.launch_calls == [], (
            f"{path}: no launch attempt; got {arrangement.fixture.launch_calls}"
        )
        assert arrangement.podman_runs() == [], f"{path}: no podman run; got {arrangement.podman_runs()}"
        stderr = capsys.readouterr().err
        assert str(arrangement.host_snapshot) in stderr, (
            f"{path}: stderr must name the missing path; got {stderr!r}"
        )
        _assert_teaches_every_failing_tier(
            stderr, arrangement.config_path, arrangement.host_snapshot, failing=None
        )

    def test_recreate_with_snapshot_present_still_proceeds(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Control: the new precondition does not block a healthy recreate (stop, rm, one launch)."""
        arrangement = _VerbStartArrangement(
            monkeypatch, tmp_path, path="recreate", static_root_count=3, snapshot_state="present"
        )

        return_code = arrangement.run_verb_start()

        assert return_code == lore_deploy._EXIT_OK, f"healthy recreate must succeed; got {return_code}"
        assert arrangement.fixture.stop_calls() and arrangement.fixture.rm_calls(), (
            f"healthy recreate must still stop+rm the stale container; got {arrangement.fixture.run_calls}"
        )
        assert len(arrangement.fixture.launch_calls) == 1, (
            f"one relaunch; got {arrangement.fixture.launch_calls}"
        )


class TestOneLaunchPreconditionDecidesBothLevels:
    """R1: _launch_container and verb_start refuse in EXACTLY the same cells.

    One shared launch-precondition check decides "a static tier is not materialised on the
    host" for both levels; a cloned condition that drifts at one site shows up as
    disagreement in some cell. Every cell is also ANCHORED to its ruled verdict: refuse iff
    static roots exist and the snapshot state is not ``present``. That includes the ``file``
    cell (S2: a regular file at the root is refused) and the per-tier cells (S1).
    """

    @pytest.mark.parametrize(
        ("static_root_count", "snapshot_state"),
        [
            (0, "absent"),
            (0, "present"),
            (1, "absent"),
            (1, "present"),
            (3, "absent"),
            (3, "present"),
            (3, "file"),
            (3, "tier_absent"),
            (3, "tier_empty"),
        ],
    )
    def test_launch_and_verb_start_agree_on_refusal(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, static_root_count: int, snapshot_state: str
    ) -> None:
        """Same fixture, both levels: refused-at-launch iff refused-at-verb_start."""
        arrangement = _VerbStartArrangement(
            monkeypatch,
            tmp_path,
            path="fresh",
            static_root_count=static_root_count,
            snapshot_state=snapshot_state,
        )
        # Level (c)(i): the real _launch_container over the same config + snapshot state.
        launch_calls_before = list(arrangement.fixture.run_calls)
        monkeypatch.setattr(lore_deploy, "_launch_container", _REAL_LAUNCH_CONTAINER)
        try:
            lore_deploy._launch_container(
                arrangement.fixture.project, arrangement.config_path, arrangement.fixture.env_file
            )
            launch_refused = False
        except RuntimeError:
            launch_refused = True
        launch_podman = arrangement.fixture.run_calls[len(launch_calls_before) :]
        assert launch_refused == (launch_podman == []), (
            f"_launch_container must either refuse with no podman call or launch; podman={launch_podman}"
        )
        # Level (c)(ii): verb_start, with the launch recorded so its OWN check must decide.
        arrangement.fixture.run_calls.clear()
        arrangement.fixture.install_launch_recorder()
        verb_refused = arrangement.run_verb_start() == lore_deploy._EXIT_ERROR

        assert launch_refused == verb_refused, (
            f"static_roots={static_root_count} snapshot={snapshot_state}: _launch_container "
            f"refused={launch_refused} but verb_start refused={verb_refused} — the two levels "
            f"must share ONE launch-precondition decision (RULING-F1-pin4 R1)"
        )
        # Anchor every cell to its ruled verdict, so agreement cannot come from both levels being wrong.
        expected = static_root_count > 0 and snapshot_state != "present"
        assert verb_refused == expected, (
            f"static_roots={static_root_count} snapshot={snapshot_state}: refusal must be {expected}"
        )


class TestDeployPreconditionAgreesWithServerGuard:
    """S1 pin 2: the deploy refuses a tier iff the SERVER's boot guard reads it unmaterialised.

    Both verdicts come from ONE fixture set, never each from its own: the first static
    tier's host dir is absent / empty / non-empty / a regular file, the others are healthy.
    The server side is the real ``Indexer._snapshot_materialized``; the deploy side is the
    real ``_launch_container`` precondition. A deploy-side copy of the rule (``exists()``
    instead of ``is_dir()``, presence without the non-empty leg) disagrees in some cell.
    """

    @pytest.mark.parametrize("tier_state", ["absent", "empty", "non_empty", "file"])
    def test_deploy_refuses_a_tier_iff_server_guard_reads_it_unmaterialised(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, tier_state: str
    ) -> None:
        """Agreement per tier, plus the refusal naming exactly the failing tier."""
        project, config_path = _write_derived_project(tmp_path, static_root_count=3)
        tiers = _static_tiers(yaml.safe_load(config_path.read_text(encoding="utf-8")))
        host_snapshot = _make_host_snapshot(tmp_path, tiers)
        probed_dir = SnapshotLayout(host_snapshot).materialization_dir(tiers[0])
        shutil.rmtree(probed_dir)
        if tier_state == "empty":
            probed_dir.mkdir()
        elif tier_state == "non_empty":
            probed_dir.mkdir()
            (probed_dir / "index.mdx").write_text("# materialised\n", encoding="utf-8")
        elif tier_state == "file":
            probed_dir.write_text("not a tier dir\n", encoding="utf-8")
        monkeypatch.setattr(lore_deploy, "SNAPSHOT_ROOT", host_snapshot)
        podman_calls = _install_podman_recorder(monkeypatch)
        env_file = tmp_path / "lore.env"
        env_file.write_text("", encoding="utf-8")
        server_unmaterialised = [
            tier for tier in tiers if not _server_guard_reads_materialised(config_path, host_snapshot, tier)
        ]
        # The fixture really exercised its case: the server disagrees about the probed tier only.
        assert server_unmaterialised == ([] if tier_state == "non_empty" else [tiers[0]]), (
            f"fixture/server mismatch ({tier_state}): server reads {server_unmaterialised} unmaterialised"
        )

        try:
            lore_deploy._launch_container(project, config_path, env_file)
            refusal_text: str | None = None
        except RuntimeError as refusal:
            refusal_text = str(refusal)

        assert (refusal_text is not None) == bool(server_unmaterialised), (
            f"state {tier_state}: deploy refused={refusal_text is not None} but the server guard reads "
            f"{server_unmaterialised} unmaterialised; one predicate must decide both (RULING-S1-S2)"
        )
        if refusal_text is not None:
            assert podman_calls == [], f"a refused launch issues no podman command; got {podman_calls}"
            _assert_teaches_every_failing_tier(
                refusal_text, config_path, host_snapshot, failing=server_unmaterialised
            )

    def test_deploy_reads_the_server_layout_not_a_retyped_root_slash_tier(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A tier whose layout dir differs from its name is judged where SnapshotLayout puts it.

        The tier is chosen from production ``TIER_SUBDIRS`` (first entry whose dir differs
        from its name), so a deploy check that hand-builds ``<root>/<tier>`` refuses a tier
        the server serves.
        """
        divergent = next((tier for tier, subdirs in TIER_SUBDIRS.items() if subdirs[0] != tier), None)
        if divergent is None:
            pytest.fail(
                "TIER_SUBDIRS has no tier whose dir differs from its name; this pin no longer discriminates"
            )
        document = _repo_config_document()
        live = [root for root in document["roots"] if root.get("watch") != "static"]
        static_root = dict(next(root for root in document["roots"] if root.get("watch") == "static"))
        static_root["tier"] = divergent
        document["roots"] = [*live, static_root]
        project = tmp_path / "lore"
        project.mkdir()
        config_path = project / "lore.yaml"
        config_path.write_text(yaml.safe_dump(document), encoding="utf-8")
        host_snapshot = _make_host_snapshot(tmp_path, [divergent])
        assert not (host_snapshot / divergent).exists(), "fixture must not also satisfy a root/tier clone"
        assert _server_guard_reads_materialised(config_path, host_snapshot, divergent), (
            f"server guard must read {divergent} materialised at its layout dir"
        )
        monkeypatch.setattr(lore_deploy, "SNAPSHOT_ROOT", host_snapshot)
        podman_calls = _install_podman_recorder(monkeypatch)
        env_file = tmp_path / "lore.env"
        env_file.write_text("", encoding="utf-8")

        lore_deploy._launch_container(project, config_path, env_file)

        assert len(podman_calls) == 1, f"a tier the server serves must not be refused; podman={podman_calls}"


_REAL_LAUNCH_CONTAINER = lore_deploy._launch_container


class TestMalformedConfigAbortsRecreateBeforeTeardown:
    """R2: a config the reader rejects aborts the recreate BEFORE stop/rm (pinned once)."""

    def test_malformed_config_on_recreate_path_leaves_container_and_reports(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An operator typo (``watch: statc``) fails schema validation: no stop, no rm, _EXIT_ERROR."""
        arrangement = _VerbStartArrangement(
            monkeypatch, tmp_path, path="recreate", static_root_count=3, snapshot_state="present"
        )
        document = yaml.safe_load(arrangement.config_path.read_text(encoding="utf-8"))
        static_root = next(root for root in document["roots"] if root.get("watch") == "static")
        static_root["watch"] = "statc"
        arrangement.config_path.write_text(yaml.safe_dump(document), encoding="utf-8")

        return_code = arrangement.run_verb_start()

        assert return_code == lore_deploy._EXIT_ERROR, (
            f"malformed config must return _EXIT_ERROR; got {return_code}"
        )
        assert arrangement.fixture.stop_calls() == [], (
            f"no stop on a malformed config; got {arrangement.fixture.run_calls}"
        )
        assert arrangement.fixture.rm_calls() == [], (
            f"no rm on a malformed config; got {arrangement.fixture.run_calls}"
        )
        assert arrangement.fixture.launch_calls == [], f"no launch; got {arrangement.fixture.launch_calls}"
        stderr = capsys.readouterr().err
        # The reader's error names the config it failed on; the operator must see it.
        assert str(arrangement.config_path) in stderr, (
            f"stderr must carry the config read error; got {stderr!r}"
        )


class TestRecreateLaunchFailureCarriesTheErrorText:
    """R3 (amendment r2 item 4): a failed relaunch reports the podman error's OWN text."""

    def test_called_process_error_exit_code_and_command_reach_stderr(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Recreate + relaunch raises CalledProcessError: stderr carries its exit code and its command."""
        arrangement = _VerbStartArrangement(
            monkeypatch, tmp_path, path="recreate", static_root_count=3, snapshot_state="present"
        )
        # podman's "container setup failed" exit, on the argv shape a real launch issues.
        launch_error = subprocess.CalledProcessError(
            returncode=125,
            cmd=["podman", "run", "-d", "--name", arrangement.fixture.container_name, lore_deploy.IMAGE],
        )

        def _failing_launch(project: Path, config_path: Path, env_file: Path) -> None:
            raise launch_error

        monkeypatch.setattr(lore_deploy, "_launch_container", _failing_launch)

        return_code = arrangement.run_verb_start()

        assert return_code == lore_deploy._EXIT_ERROR, (
            f"failed relaunch must return _EXIT_ERROR; got {return_code}"
        )
        stderr = capsys.readouterr().err
        assert str(launch_error.returncode) in stderr, f"stderr must carry the exit code; got {stderr!r}"
        # The generic hint names the container and "podman exit"; only the failed command names the image.
        assert lore_deploy.IMAGE in stderr, f"stderr must carry the failed command; got {stderr!r}"


# --- A1: after teardown, every documented launch failure degrades to _EXIT_ERROR ---------

# The doors through which the REAL ``_launch_container`` fails AFTER the recreate has
# already stopped and removed the serving container, each with the type
# ``_launch_container``'s docstring documents for it (RULING-A1-A8-T1 A1, ∀ over types):
# - the host snapshot is wiped in the window (a concurrent cold-index re-materialise, or
#   an operator ``rm``): the launch's own precondition re-check raises RuntimeError;
# - the config turns unreadable in the window (an operator edit): the config read raises
#   RuntimeError;
# - ``podman run`` exits non-zero: ``_run(check=True)`` raises CalledProcessError.
_POST_TEARDOWN_DOORS: dict[str, type[Exception]] = {
    "snapshot_vanishes": RuntimeError,
    "config_unreadable": RuntimeError,
    "podman_run_fails": subprocess.CalledProcessError,
}
# podman's "container setup failed" exit, with the stderr shape podman prints.
PODMAN_SETUP_FAILED_EXIT = 125
PODMAN_SETUP_FAILED_STDERR = (
    "Error: crun: cannot open `/home/lore`: Permission denied: OCI permission denied\n"
)


class TestRecreateFailureAfterTeardownDegradesToExitError:
    """A1: once the stale container is gone, no launch failure may escape verb_start raw.

    The property is pinned over the failure TYPES ``_launch_container`` documents, each
    forced through the REAL ``_launch_container`` (only podman is recorded), never over
    the one door that was found first. Each cell first proves the teardown happened and
    the forced error was really raised, so a green cell cannot come from the failure
    never firing.
    """

    @pytest.mark.parametrize("door", sorted(_POST_TEARDOWN_DOORS))
    def test_post_teardown_launch_failure_returns_exit_error_with_its_text(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str], door: str
    ) -> None:
        """Recreate, healthy preconditions, failure forced after ``podman rm``: _EXIT_ERROR + error text."""
        arrangement = _VerbStartArrangement(
            monkeypatch, tmp_path, path="recreate", static_root_count=3, snapshot_state="present"
        )
        tiers = _static_tiers(yaml.safe_load(arrangement.config_path.read_text(encoding="utf-8")))
        first_tier_dir = SnapshotLayout(arrangement.host_snapshot).materialization_dir(tiers[0])
        raised: list[Exception] = []

        def _observed_real_launch(project: Path, config_path: Path, env_file: Path) -> None:
            # The REAL launch; only observed, so the test can name the error it raised.
            try:
                _REAL_LAUNCH_CONTAINER(project, config_path, env_file)
            except Exception as error:
                raised.append(error)
                raise

        monkeypatch.setattr(lore_deploy, "_launch_container", _observed_real_launch)
        recorded_run = lore_deploy._run

        def _run_opening_the_door(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            result = recorded_run(cmd, **kwargs)
            if cmd[:2] == ["podman", "rm"] and door == "snapshot_vanishes":
                shutil.rmtree(first_tier_dir)
            elif cmd[:2] == ["podman", "rm"] and door == "config_unreadable":
                document = yaml.safe_load(arrangement.config_path.read_text(encoding="utf-8"))
                next(root for root in document["roots"] if root.get("watch") == "static")["watch"] = "statc"
                arrangement.config_path.write_text(yaml.safe_dump(document), encoding="utf-8")
            elif cmd[:2] == ["podman", "run"] and door == "podman_run_fails":
                raise subprocess.CalledProcessError(
                    PODMAN_SETUP_FAILED_EXIT, cmd, output="", stderr=PODMAN_SETUP_FAILED_STDERR
                )
            return result

        monkeypatch.setattr(lore_deploy, "_run", _run_opening_the_door)

        try:
            return_code = lore_deploy.verb_start(
                arrangement.fixture.project, arrangement.fixture.env_file, no_wait=True
            )
        except Exception as escaped:
            pytest.fail(
                f"{door}: a launch failure after teardown must return _EXIT_ERROR, not raise; "
                f"raised {escaped!r} after podman calls {arrangement.fixture.run_calls}"
            )

        # The cell really is post-teardown, and the forced failure really fired.
        assert arrangement.fixture.stop_calls() and arrangement.fixture.rm_calls(), (
            f"{door}: the failure must be forced AFTER stop+rm; got {arrangement.fixture.run_calls}"
        )
        assert len(raised) == 1 and isinstance(raised[0], _POST_TEARDOWN_DOORS[door]), (
            f"{door}: the real _launch_container must raise {_POST_TEARDOWN_DOORS[door].__name__}; "
            f"got {raised}"
        )
        assert return_code == lore_deploy._EXIT_ERROR, f"{door}: must return _EXIT_ERROR; got {return_code}"
        stderr = capsys.readouterr().err
        assert str(raised[0]) in stderr, (
            f"{door}: stderr must carry the launch error's own text {str(raised[0])!r}; got {stderr!r}"
        )


# --- A8: the remedy runs as pasted -------------------------------------------------------

# The remedy is the one backticked command in the refusal.
_BACKTICKED_COMMAND = re.compile(r"`([^`]*\s-m\s[^`]*)`")


class TestRefusalRemedyRunsAsPasted:
    """A8: the refusal's remedy names an interpreter that resolves the cold-index module."""

    def test_remedy_interpreter_is_the_deploy_interpreter_and_resolves_the_cold_index_module(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, _distinct_loremaster_interpreter: Path
    ) -> None:
        """Parse the pasted command; run ITS interpreter; the cold-index module must resolve there."""
        act, _, _, config_path = _launch(monkeypatch, tmp_path, static_root_count=3, snapshot_present=False)

        with pytest.raises(RuntimeError) as refusal:
            act()

        commands = _BACKTICKED_COMMAND.findall(str(refusal.value))
        assert len(commands) == 1, f"the refusal must carry one paste-ready command; got {commands}"
        argv = shlex.split(commands[0])
        # Derived from production, never retyped: the interpreter lore-deploy itself uses.
        assert argv[0] == lore_deploy._loremaster_python() == str(_distinct_loremaster_interpreter), (
            f"the remedy must name lore-deploy's loremaster interpreter "
            f"{lore_deploy._loremaster_python()}; got {argv[0]!r}"
        )
        assert argv[1:] == ["-m", "loremaster.index", "--config", str(config_path)], (
            f"the remedy must cold-index THIS config; got {argv}"
        )
        # Runs as pasted: the named interpreter really resolves the module the remedy runs.
        find_spec_probe = (
            "import importlib.util, sys; sys.exit(importlib.util.find_spec(sys.argv[1]) is None)"
        )
        resolves = subprocess.run(
            [argv[0], "-c", find_spec_probe, argv[2]],
            check=False,
            capture_output=True,
            text=True,
        )
        assert resolves.returncode == 0, (
            f"{argv[0]} cannot resolve {argv[2]}; the pasted remedy would fail: {resolves.stderr[-1000:]}"
        )


# --- T1: a tier that prefixes another cannot misfire the naming checks -------------------

# A realistic prefix pair: the shipped SurrealDB docs tier, and a sibling corpus whose name
# is its prefix. Both fall back to ``<root>/<tier>`` in production ``SnapshotLayout``.
PREFIX_TIER = "surrealdb"
PREFIXED_TIER = "surrealdb-docs"


class TestRefusalNamesTiersByWholePathComponent:
    """T1: with ``surrealdb`` and ``surrealdb-docs`` both static, the refusal names only the failing one."""

    @pytest.mark.parametrize("failing_tier", [PREFIX_TIER, PREFIXED_TIER])
    def test_prefix_pair_refusal_names_only_the_failing_tier(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, failing_tier: str
    ) -> None:
        """Either orientation: the healthy tier's dir is not named, the failing one is."""
        document = _repo_config_document()
        live = [root for root in document["roots"] if root.get("watch") != "static"]
        static = [root for root in document["roots"] if root.get("watch") == "static"]
        assert len(static) >= 2, f"{REPO_CONFIG} must declare two static roots to derive the pair"
        document["roots"] = [
            *live,
            {**static[0], "tier": PREFIXED_TIER},
            {**static[1], "tier": PREFIX_TIER},
        ]
        project = tmp_path / "lore"
        project.mkdir()
        config_path = project / "lore.yaml"
        config_path.write_text(yaml.safe_dump(document), encoding="utf-8")
        host_snapshot = _make_host_snapshot(tmp_path, [PREFIXED_TIER, PREFIX_TIER])
        shutil.rmtree(SnapshotLayout(host_snapshot).materialization_dir(failing_tier))
        layout = SnapshotLayout(host_snapshot)
        # The pair really is a prefix pair on disk, so the fixture exercises T1.
        assert str(layout.materialization_dir(PREFIXED_TIER)).startswith(
            str(layout.materialization_dir(PREFIX_TIER))
        ), "fixture must place one tier dir as a string prefix of the other"
        assert [
            tier
            for tier in (PREFIXED_TIER, PREFIX_TIER)
            if not _server_guard_reads_materialised(config_path, host_snapshot, tier)
        ] == [failing_tier], f"fixture must leave only {failing_tier} unmaterialised for the server guard"
        monkeypatch.setattr(lore_deploy, "SNAPSHOT_ROOT", host_snapshot)
        podman_calls = _install_podman_recorder(monkeypatch)
        env_file = tmp_path / "lore.env"
        env_file.write_text("", encoding="utf-8")

        with pytest.raises(RuntimeError) as refusal:
            lore_deploy._launch_container(project, config_path, env_file)

        assert podman_calls == [], f"a refused launch issues no podman command; got {podman_calls}"
        _assert_teaches_every_failing_tier(
            str(refusal.value), config_path, host_snapshot, failing=[failing_tier]
        )


# --- Pin 2: the artifact pin ----------------------------------------------------------

# Runs INSIDE the image. Imports the image's loremaster (asserted not the /workspace
# mount), resolves the server's real default root, and evaluates the real, unpatched
# Indexer._snapshot_materialized per static tier of the config the command wires in
# (LORE_CONFIG). Prints one JSON line. Instrument lineage: REPORT-source-trace-165-r3
# §Execution probe (archived under docs/plans/v2/receipts/2026-10-31-165/).
_IN_IMAGE_PROBE = textwrap.dedent(
    f"""
    import json, os
    from pathlib import Path
    import yaml
    import loremaster
    from loremaster import server
    from loremaster.config import LoreConfig
    from loremaster.index.indexer import Indexer
    from loremaster.source.snapshot import SnapshotLayout

    def guard(root, tier):
        # Indexer.__init__ needs a live store; the guard reads only _snapshot_layout,
        # assigned exactly as __init__ assigns it.
        indexer = Indexer.__new__(Indexer)
        indexer._snapshot_layout = SnapshotLayout(Path(root))
        return Indexer._snapshot_materialized(indexer, tier)

    config_path = Path(os.environ["LORE_CONFIG"])
    config = LoreConfig.model_validate(yaml.safe_load(config_path.read_text(encoding="utf-8")))
    tiers = [r.tier for r in config.effective_roots if r.watch == "static"]
    print(json.dumps({{
        "loremaster_file": str(Path(loremaster.__file__).resolve()),
        "default_root": str(server._DEFAULT_SNAPSHOT_ROOT),
        "static_tiers": tiers,
        "guard_default_root": {{t: guard(server._DEFAULT_SNAPSHOT_ROOT, t) for t in tiers}},
        "guard_unbound_control": {{t: guard({UNBOUND_CONTROL_ROOT!r}, t) for t in tiers}},
    }}))
    """
)


def _as_one_shot_probe(launch_cmd: list[str]) -> list[str]:
    """Turn the captured launch command into a one-shot, network-less probe run.

    Only the run MODE changes: ``-d``/``--detach`` and ``--name`` go (the live
    ``lore-<slug>`` container may be running), the network becomes ``none``, ``--rm``
    is added, and the probe replaces the image's default command. Every bind, env,
    user and userns flag the launch builds is kept byte-for-byte.
    """
    assert launch_cmd[:2] == ["podman", "run"], f"not a podman run: {launch_cmd}"
    assert launch_cmd[-1] == lore_deploy.IMAGE, (
        f"launch must end with the image {lore_deploy.IMAGE}: {launch_cmd}"
    )
    kept: list[str] = []
    index = 2
    body = launch_cmd[:-1]
    while index < len(body):
        token = body[index]
        if token in ("-d", "--detach"):
            index += 1
            continue
        if token in ("--name", "--network", "--net"):
            index += 2
            continue
        if token.startswith(("--name=", "--network=", "--net=")):
            index += 1
            continue
        kept.append(token)
        index += 1
    probe = [
        "podman",
        "run",
        "--rm",
        "--network=none",
        *kept,
        lore_deploy.IMAGE,
        CONTAINER_PYTHON,
        "-c",
        _IN_IMAGE_PROBE,
    ]
    # Step-N-no-op guard: the probe's mode is checked on the RESULT, not trusted from the loop.
    flags = probe[: probe.index(lore_deploy.IMAGE)]
    assert "-d" not in flags and "--detach" not in flags, f"probe must not detach: {flags}"
    assert not any(f == "--name" or f.startswith("--name=") for f in flags), (
        f"probe must not be named: {flags}"
    )
    networks = [f for f in flags if f.startswith(("--network", "--net"))]
    assert networks == ["--network=none"], f"probe must be network-less; got {networks}"
    return probe


class TestLaunchCommandBootsTheGuardTrueInTheRealImage:
    """The exact launch command, run against the real image, satisfies the real boot guard."""

    def _preflight(self) -> None:
        """Fail LOUD, naming the missing piece. This pin never skips (PLAN-165 pin 2)."""
        if shutil.which("podman") is None:
            pytest.fail("artifact pin needs podman on PATH; it is missing")
        image = subprocess.run(
            ["podman", "image", "exists", lore_deploy.IMAGE], check=False, capture_output=True, text=True
        )
        if image.returncode != 0:
            pytest.fail(
                f"artifact pin needs the image {lore_deploy.IMAGE}; `podman image exists` says it is absent"
            )
        if not lore_deploy.SNAPSHOT_ROOT.is_dir():
            pytest.fail(
                f"artifact pin needs the host snapshot dir {lore_deploy.SNAPSHOT_ROOT}; it is absent "
                f"(cold-index it: python -m loremaster.index --config {REPO_CONFIG})"
            )

    def test_launch_command_makes_guard_true_for_every_static_tier(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Real _launch_container + real lore.yaml + real image: guard True ×N, control False ×N."""
        self._preflight()
        expected_tiers = _static_tiers(_repo_config_document())
        assert expected_tiers, f"{REPO_CONFIG} declares no static tier; the pin would be vacuous"
        # Keep the probe off the live manifest/graph state dir; this bind is not under test.
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        monkeypatch.setattr(lore_deploy, "MANIFEST_DIR", state_dir)
        podman_calls = _install_podman_recorder(monkeypatch)
        env_file = tmp_path / "empty.env"
        env_file.write_text("", encoding="utf-8")

        lore_deploy._launch_container(REPO_ROOT, REPO_CONFIG, env_file)

        probe_cmd = _as_one_shot_probe(_single_launch(podman_calls))
        try:
            result = subprocess.run(
                probe_cmd, check=False, capture_output=True, text=True, timeout=PROBE_TIMEOUT_S
            )
        except subprocess.TimeoutExpired:
            pytest.fail(f"in-image probe exceeded {PROBE_TIMEOUT_S}s")
        assert result.returncode == 0, (
            f"in-image probe failed (exit {result.returncode}); stderr tail:\n{result.stderr[-2000:]}"
        )
        report = json.loads(result.stdout.strip().splitlines()[-1])

        # Provenance: the IMAGE's loremaster, never the /workspace source mount.
        assert not report["loremaster_file"].startswith("/workspace"), (
            f"probe graded the mount, not the artifact: {report['loremaster_file']}"
        )
        assert report["default_root"] == CONTAINER_SNAPSHOT_TARGET, (
            f"in-image server root {report['default_root']} != derived target {CONTAINER_SNAPSHOT_TARGET}"
        )
        assert report["static_tiers"] == expected_tiers, (
            f"in-image static tiers {report['static_tiers']} != lore.yaml's {expected_tiers}"
        )
        # Control: the guard CAN read False in this container, so True below is not a constant.
        assert report["guard_unbound_control"] == {tier: False for tier in expected_tiers}, (
            f"control guard over unbound {UNBOUND_CONTROL_ROOT} must be False for every tier; "
            f"got {report['guard_unbound_control']}"
        )
        assert report["guard_default_root"] == {tier: True for tier in expected_tiers}, (
            f"the boot guard must read every static tier as materialised under the launch command; "
            f"got {report['guard_default_root']} (False = boot re-acquires and crashes, #165)"
        )
