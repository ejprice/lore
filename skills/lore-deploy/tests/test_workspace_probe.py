"""Contract — findings #125 / #131, LAYERS 2 and 3: the deploy gates the ARTIFACT.

``loremaster/tests/test_workspace_status.py`` pins the RECIPE — that the honesty line is
computed correctly and served through ``lore_index()``. Nothing there can see the CAKE:
the deployed image has no ``git`` binary, so the CORRECT build serves ``git_branch: null``
in the only environment the feature exists for. A builder can satisfy every one of those
pins and ship a feature that is a ``null`` in production. (Same root cause as #131 —
every production snapshot's ``git_ref`` has been silently ``None``.)

So the gate lives HERE, in the deploy verb, where the artifact actually runs:

* **Layer 2 — the binary is IN the image.** For every binary the shipped code can exec
  (DERIVED, not enumerated — see ``loremaster/tests/test_shellout_allowlist.py``),
  ``command -v <binary>`` must succeed inside the running container.
* **Layer 3 — the feature actually WORKS in the image (the load-bearing one).** For every
  root ``lore_index()`` SERVES: if that root's tree carries a ``.git``, its ``git_branch``
  must be non-null. Layer 2 cannot see a git that is PRESENT but REFUSING (git's
  dubious-ownership exit 128 → the seam swallows it → the same silent null: finding #132).
  Layer 3 can, because it reads what the server actually served.

Two design rules the pins below enforce, both learned the hard way:

1. **The check runs INSIDE the container, on the SERVED path.** The served path is the
   container's (``/workspace``), which does not exist on the host — so a probe that stats
   it host-side finds no ``.git``, skips its own check, and reports success over a dead
   feature. Every fixture here serves ``/workspace`` and simulates the container exec, so
   a host-side stat sees nothing and goes RED.
2. **``.git`` is a FILE in a git WORKTREE, not a directory** — and worktrees are the
   entire point of #125. A predicate written with ``test -d`` / ``is_dir()`` skips exactly
   the case the feature exists for. ``test_a_git_WORKTREE_whose_dot_git_is_a_FILE_is_gated``
   builds a REAL worktree and fails any such build.

The gate asserts a RELATIVE fact (``.git`` present ⇒ branch non-null), never the absolute
"the branch is not null" — that would false-fail a legitimate project whose tree is not a
git checkout (commit c06c3ac: entry checks assert relative facts).

Seams this pins in ``lore_deploy`` (the builder lands them):

* ``required_container_binaries(repo_root=None) -> list[str]`` — the derived safe set,
  obtained from the ONE derivation (``loremaster.shellout.required_binaries``). Never a
  second scanner, never a hand-kept list.
* ``_exec_in_container(container, argv) -> CompletedProcess`` — the single container-exec
  seam (``podman exec``). Both probes route through it.
* ``_probe_container_binaries(container) -> int`` — layer 2.
* ``_served_workspace_roots(host, port, path) -> list[dict] | None`` — reads the SERVED
  ``lore_index()`` payload over MCP. ``None`` ⇒ no workspace section at all (an image that
  predates the feature) — which is a LOUD failure, not an empty list.
* ``_probe_workspace_honesty(container, host, port, path) -> int`` — layer 3.
* both probes WIRED INTO ``verb_start`` on every path that ends with a running container
  (a runtime gate is an invariant only over code it RUNS).

Run:
    cd skills/lore-deploy/scripts && uv run python -m pytest -q . ../tests
"""

from __future__ import annotations

import http.server
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import lore_deploy  # noqa: E402  (path must be extended before this import)

# The real repo root: skills/lore-deploy/tests/<this file>.
REPO_ROOT = Path(__file__).resolve().parents[3]

# The path the CONTAINER serves. It deliberately does NOT exist on this host, so a probe
# that stats the served path host-side finds nothing, skips its check, and goes RED.
_CONTAINER_WORKSPACE = "/workspace"
_CONTAINER_NAME = "lore-testproject"
_HOST = "127.0.0.1"
_MOUNT_PATH = "/mcp"

# Deliberately NOT this repo's own branch (fixture monoculture is this repo's #1 defect).
_BRANCH = "spike/honesty-line"

# --------------------------------------------------------------------------- #
# FIX WAVE (packet 01, cold audit REPORT-pkt01-audit-1.md §D/§R) — the vocabulary the
# DIAGNOSES are graded against.
#
# These are SEMANTIC token sets, never exact strings: the pins below constrain what a
# message MEANS — which cause it blames, which cure it prescribes — and leave the
# wording free. That distinction is the point. This repo's audited defect class is
# served English that describes a mechanism the code does not run, and the answer to it
# is a guard on MEANING; a forbidden-phrase list is the name-list losing again.
# --------------------------------------------------------------------------- #

# "The endpoint did not answer" — the cause when the server is mid-boot, and the cause
# the operator CHOOSES when passing --no-wait (we declined to confirm the bind).
_UNREACHABLE_TOKENS = (
    "unreachable", "could not be reached", "not reachable", "refused", "not accepting",
    "no response", "could not be read", "did not respond", "connect", "did not answer",
)
# "The image predates the honesty line" — the cause when a LIVE server answers and its
# lore_index() payload carries no ``workspace`` section at all. The cure is a rebuild.
_OLD_IMAGE_TOKENS = ("predates", "rebuild")
# The CURE for a linked worktree whose gitdir is not inside the mount. A diagnosis's
# actionable payload is its CURE — prescribing the wrong one is the entire defect.
_WORKTREE_CURE_TOKENS = ("gitdir", "git_dir", "worktree repair", "parent")
# The cures for a git that is MISSING or REFUSING. Correct for a normal checkout —
# actively misleading for a worktree whose gitdir was never mounted (neither the binary
# nor the ownership is the problem there, and following them fixes nothing).
_REFUSING_GIT_CURE_TOKENS = ("keep-id", "dubious", "binary")

# An announced gate-skip names WHAT did not run (a gate word) and SAYS it did not run.
_GATE_WORDS = ("artifact", "gate", "probe", "honesty", "binaries")
_SKIP_WORDS = (
    "skip", "not run", "did not run", "not verified", "unverified", "deferred",
    "not confirm", "cannot verify", "could not verify", "no confirmation",
)


def _hits(text: str, tokens: tuple[str, ...]) -> list[str]:
    """Which of ``tokens`` the case-folded ``text`` contains."""
    lowered = text.lower()
    return [token for token in tokens if token in lowered]


def _dead_port() -> int:
    """A port nothing is listening on — a mid-boot MCP endpoint, exactly.

    Bind, read the kernel-assigned port, close. The port is then free and UNSERVED, so a
    connect against it is refused — which is precisely what ``_served_workspace_roots``
    meets on a fresh launch the deploy declined to wait for (``--no-wait``).
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((_HOST, 0))
        port = int(probe.getsockname()[1])
    return port


def _break_the_worktree_gitdir(worktree: Path) -> str:
    """Make a REAL worktree's gitdir unreachable — the CONTAINER's view of a worktree.

    In a linked worktree ``.git`` is a FILE holding ``gitdir: <absolute host path>``. Only
    the worktree itself is bind-mounted at ``/workspace``; the parent repo's
    ``.git/worktrees/<name>`` directory that line points at is NOT inside the mount, so
    inside the container that absolute path does not exist and git exits 128 (verified:
    ``fatal: not a git repository``) — the served branch is null, and the tree is a git
    tree, so layer 3 fires. This rewrite reproduces that state faithfully on the host: the
    ``.git`` file still EXISTS and is still a FILE; only its target is gone.

    Returns the unreachable gitdir path it wrote.
    """
    gitdir = "/nonexistent-host-gitdir/lore/.git/worktrees/sibling"
    (worktree / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")
    assert (worktree / ".git").is_file()
    assert not Path(gitdir).exists()
    return gitdir


# --------------------------------------------------------------------------- #
# A faithful CONTAINER simulation: the served path is /workspace (absent on the
# host); the exec seam maps it onto a real tree and runs the REAL argv.
# --------------------------------------------------------------------------- #
class _FakeContainer:
    """Runs the probe's own argv locally, with ``/workspace`` mapped to a real tree.

    Deliberately executes the argv the implementation chose rather than matching it: the
    predicate under test (``does <root>/.git exist``) is then a REAL filesystem question
    asked of a REAL tree, so ``test -d`` vs ``test -e`` is settled by the filesystem —
    not by whether a stub happened to recognise the flag.
    """

    def __init__(self, tree: Path, *, path_env: str | None = None) -> None:
        self.tree = tree
        self.path_env = path_env
        self.calls: list[list[str]] = []

    def __call__(self, container: str, argv: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(argv))
        translated = [arg.replace(_CONTAINER_WORKSPACE, str(self.tree)) for arg in argv]
        env = dict(os.environ)
        if self.path_env is not None:
            env["PATH"] = self.path_env
        try:
            return subprocess.run(  # noqa: S603 - the probe's own argv, run locally
                translated, capture_output=True, text=True, check=False, env=env
            )
        except OSError:
            # ``podman exec`` never raises for a binary the container lacks — it exits
            # non-zero (127, the shell's command-not-found). Faithful simulation.
            return subprocess.CompletedProcess(translated, 127, "", "not found")

    def saw_path(self, needle: str) -> bool:
        """Did any exec the probe issued mention ``needle`` (e.g. the served root)?"""
        return any(needle in arg for call in self.calls for arg in call)


_GIT_ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
    "GIT_AUTHOR_NAME": "lore test",
    "GIT_AUTHOR_EMAIL": "test@example.invalid",
    "GIT_COMMITTER_NAME": "lore test",
    "GIT_COMMITTER_EMAIL": "test@example.invalid",
}


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(  # noqa: S603
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=True, env=_GIT_ENV,
    ).stdout.strip()


def _make_git_repo(path: Path, *, branch: str = _BRANCH) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-b", branch)
    (path / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(path, "add", "module.py")
    _git(path, "commit", "-m", "seed")
    return path


def _make_git_worktree(main: Path, worktree: Path, *, branch: str = "wt/second-tree") -> Path:
    """A REAL linked worktree — its ``.git`` is a FILE, not a directory."""
    _git(main, "worktree", "add", "-b", branch, str(worktree))
    assert (worktree / ".git").is_file(), "a linked worktree's .git must be a FILE"
    assert not (worktree / ".git").is_dir()
    return worktree


def _root(path: str = _CONTAINER_WORKSPACE, *, branch: str | None, tier: str = "custom") -> dict[str, Any]:
    """One served ``WatchedRoot`` row, as it arrives in lore_index()'s payload."""
    return {"tier": tier, "path": path, "git_branch": branch, "git_ref": None if branch is None else "0" * 40}


# --------------------------------------------------------------------------- #
# A stub MCP server that answers lore_index() exactly as FastMCP does (verified
# against the live container: SSE body, mcp-session-id header, structuredContent).
# --------------------------------------------------------------------------- #
class _StubMCPServer:
    """Serves one canned ``lore_index()`` payload over streamable HTTP."""

    def __init__(self, structured: dict[str, Any] | None) -> None:
        self.structured = structured
        self.tool_calls: list[str] = []
        stub = self

        class _Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802 (stdlib override name)
                length = int(self.headers.get("Content-Length", 0))
                request = json.loads(self.rfile.read(length) or b"{}")
                method = request.get("method", "")
                if method.startswith("notifications/"):
                    self.send_response(202)
                    self.end_headers()
                    return
                if method == "initialize":
                    result: dict[str, Any] = {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {"listChanged": False}},
                        "serverInfo": {"name": "stub", "version": "0"},
                    }
                elif method == "tools/call":
                    stub.tool_calls.append(request.get("params", {}).get("name", ""))
                    result = {
                        "content": [{"type": "text", "text": json.dumps(stub.structured)}],
                        "structuredContent": stub.structured,
                    }
                else:
                    result = {}
                body = json.dumps({"jsonrpc": "2.0", "id": request.get("id"), "result": result})
                payload = f"event: message\ndata: {body}\n\n".encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("mcp-session-id", "stub-session")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *args: Any) -> None:  # silence the stdlib access log
                return

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind((_HOST, 0))
            self.port = probe.getsockname()[1]
        self._server = http.server.HTTPServer((_HOST, self.port), _Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def __enter__(self) -> _StubMCPServer:
        self._thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


def _index_payload(roots: list[dict[str, Any]] | None) -> dict[str, Any]:
    """A lore_index() structuredContent payload, with or without the workspace section."""
    payload: dict[str, Any] = {"files_indexed": 3, "files_failed": 0, "files_skipped": 0}
    if roots is not None:
        payload["workspace"] = {"roots": roots}
    return payload


@pytest.fixture
def gitless_path_dir(tmp_path: Path) -> Iterator[str]:
    """A PATH with a SHELL but no ``git`` — the deployed image's actual state.

    Faithful, deliberately: the real image (python:3.14-slim + curl) has ``sh`` and
    ``curl`` and no ``git``. Emptying PATH entirely would remove the shell too and prove
    only that the probe dies when it cannot run at all — a different, easier failure.
    """
    fake_bin = tmp_path / "gitless-bin"
    fake_bin.mkdir()
    for present in ("sh", "curl"):
        real = shutil.which(present)
        if real is not None:
            (fake_bin / present).symlink_to(real)
    assert (fake_bin / "sh").exists(), "the fixture needs a shell to be a fair simulation"
    assert not (fake_bin / "git").exists()
    yield str(fake_bin)


def _install_fake_container(
    monkeypatch: pytest.MonkeyPatch, tree: Path, *, path_env: str | None = None
) -> _FakeContainer:
    """Swap the ONE container-exec seam for the faithful local simulation."""
    fake = _FakeContainer(tree, path_env=path_env)
    monkeypatch.setattr(lore_deploy, "_exec_in_container", fake)
    return fake


# --------------------------------------------------------------------------- #
# LAYER 2a — the required set IS the derived set (never a hand-kept list)
# --------------------------------------------------------------------------- #
class TestRequiredBinariesAreDerived:
    """ONE IMPLEMENTATION: the deploy asks the derivation; it does not keep a list."""

    def test_the_required_set_is_derived_from_the_source_not_hardcoded(
        self, tmp_path: Path
    ) -> None:
        # Pointed at a SYNTHETIC workspace whose shipped code execs ``rg`` (never ``git``),
        # the deploy's required set must be ["rg"]. A hardcoded ["git"] — which would agree
        # with the real repo today, and so pass any real-repo comparison — dies right here.
        #
        # The exec site is placed at the SANCTIONED seam's path (the sanctioned-seam
        # architecture: no shipped module may reach a spawner except the allowlist, and the
        # allowlist is keyed on the repo-relative PATH). That is load-bearing here in a second
        # way: ``required_container_binaries`` takes no ``sanctioned`` keyword and must not —
        # it walks through the DEFAULT allowlist, exactly as production does. A build that let
        # the deploy widen its own safe set would have a door the contract never sees.
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "s"\nversion = "0"\n\n'
            '[tool.uv.workspace]\nmembers = ["loremaster"]\n',
            encoding="utf-8",
        )
        seam = tmp_path / "loremaster" / "loremaster" / "index" / "snapshots.py"
        seam.parent.mkdir(parents=True)
        (seam.parent.parent / "__init__.py").write_text("", encoding="utf-8")
        (seam.parent / "__init__.py").write_text("", encoding="utf-8")
        seam.write_text(
            'import subprocess\n\n\ndef go() -> None:\n    subprocess.run(["rg"], check=False)\n',
            encoding="utf-8",
        )

        assert lore_deploy.required_container_binaries(tmp_path) == ["rg"], (
            "the deploy's required-binary set must be DERIVED from the shipped source "
            "(loremaster.shellout.required_binaries) — a hand-kept list is a list someone "
            "must remember to update, which is exactly how the image lost git"
        )

    def test_a_shipped_module_OUTSIDE_the_seam_stops_the_deploy(self, tmp_path: Path) -> None:
        # The other half of the sanctioned-seam architecture, at the DEPLOY layer: a shipped
        # module that reaches a process spawner without being sanctioned must make the deploy
        # REFUSE, not quietly derive a smaller set. The derivation raises; the deploy's
        # wrapper turns that into a RuntimeError, and ``_probe_container_binaries`` turns THAT
        # into _EXIT_ERROR (pinned by test_a_derivation_that_cannot_vouch_stops_the_deploy).
        #
        # Byte-identical code to the fixture above. Only the PATH differs — and that is the
        # whole architecture.
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "s"\nversion = "0"\n\n'
            '[tool.uv.workspace]\nmembers = ["loremaster"]\n',
            encoding="utf-8",
        )
        package = tmp_path / "loremaster" / "loremaster"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "not_the_seam.py").write_text(
            'import subprocess\n\n\ndef go() -> None:\n    subprocess.run(["rg"], check=False)\n',
            encoding="utf-8",
        )

        with pytest.raises(RuntimeError, match="not_the_seam"):
            lore_deploy.required_container_binaries(tmp_path)

    def test_the_required_set_for_this_repo_is_what_the_shipped_code_execs(self) -> None:
        # And on the REAL repo it agrees with the ONE derivation — no second scanner.
        from loremaster.shellout import required_binaries

        assert set(lore_deploy.required_container_binaries()) == set(
            required_binaries(REPO_ROOT)
        ), (
            "lore_deploy and loremaster must not disagree about what the image needs — "
            "there is ONE derivation and the deploy CALLS it"
        )

    def test_the_deploy_delegates_to_the_shared_derivation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # PROVE SHARING BY MUTATION (the only test that distinguishes DRY from looks-DRY):
        # shadow ``loremaster.shellout`` with a stub that answers a sentinel, and the
        # deploy's answer MUST follow it. A cloned scanner in lore_deploy.py keeps
        # returning ["git"] and dies here.
        stub_root = tmp_path / "stub-site"
        package = stub_root / "loremaster"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "shellout.py").write_text(
            "from pathlib import Path\n"
            "\n"
            "\n"
            "class UnresolvedExecSiteError(RuntimeError):\n"
            "    pass\n"
            "\n"
            "\n"
            "def required_binaries(repo_root: Path) -> frozenset[str]:\n"
            '    return frozenset({"sentinel-binary"})\n',
            encoding="utf-8",
        )
        monkeypatch.setenv("PYTHONPATH", str(stub_root))

        assert lore_deploy.required_container_binaries() == ["sentinel-binary"], (
            "the deploy did not follow the shared derivation when it changed — it either "
            "clones the scan (a private copy wearing the shared name: ROUTING IS NOT "
            "SHARING, finding #102) or resolves loremaster once at import time rather "
            "than through the loremaster interpreter seam this skill is built on"
        )


# --------------------------------------------------------------------------- #
# LAYER 2b — the binary is actually IN the running container
# --------------------------------------------------------------------------- #
class TestProbeContainerBinaries:
    """The gate that would have caught a git-less image on the day it shipped."""

    def test_a_missing_binary_fails_the_probe_and_names_it(
        self,
        tmp_path: Path,
        gitless_path_dir: str,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # The DEPLOYED IMAGE's actual state, probed today by the adversary: no git.
        fake = _install_fake_container(monkeypatch, tmp_path, path_env=gitless_path_dir)

        result = lore_deploy._probe_container_binaries(_CONTAINER_NAME)

        assert result == lore_deploy._EXIT_ERROR, (
            "a container missing a binary the shipped code EXECS must fail the deploy — "
            "this is the gate that was missing when the image shipped without git "
            "(findings #125/#131: a feature that is null in the only environment it "
            "exists for)"
        )
        assert "git" in capsys.readouterr().err, "the failure must NAME the missing binary"
        assert fake.calls, "the probe must actually exec something in the container"

    def test_a_present_binary_passes_the_probe(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # THE POSITIVE CONTROL: the same probe, an unmodified PATH (this host HAS git).
        # Without this leg, the pin above would be satisfied by a probe that refuses
        # everything — a gate that always fails is not a gate.
        _install_fake_container(monkeypatch, tmp_path)

        assert lore_deploy._probe_container_binaries(_CONTAINER_NAME) == lore_deploy._EXIT_OK

    def test_the_repo_root_the_deploy_derives_from_IS_the_workspace_root(self) -> None:
        # The derivation is only as good as the tree it is pointed at. A mis-resolved root
        # yields NO members, hence an EMPTY required set, hence a gate that iterates over
        # nothing and passes — the failure this whole instrument exists to prevent, with a
        # reassuring "OK" printed over it. (Found live: running these pins against the
        # reference build in a scratch copy did exactly this.)
        assert (lore_deploy.REPO_ROOT / "pyproject.toml").is_file(), (
            f"lore_deploy.REPO_ROOT ({lore_deploy.REPO_ROOT}) is not the lore workspace "
            f"root — the binary derivation would scan nothing and the gate would pass "
            f"vacuously"
        )
        assert "[tool.uv.workspace]" in (
            lore_deploy.REPO_ROOT / "pyproject.toml"
        ).read_text(encoding="utf-8")

    def test_a_derivation_that_cannot_vouch_for_the_set_STOPS_the_deploy(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # The scan raises when it cannot vouch for the set (an unreadable exec site, a
        # spawner it does not understand, a root with no packages). The probe must convert
        # that into a LOUD deploy failure — never swallow it into an empty list and pass.
        def _cannot_vouch(*args: object, **kwargs: object) -> list[str]:
            raise RuntimeError("the scan cannot vouch for the required set")

        monkeypatch.setattr(lore_deploy, "required_container_binaries", _cannot_vouch)
        _install_fake_container(monkeypatch, tmp_path)

        assert lore_deploy._probe_container_binaries(_CONTAINER_NAME) == lore_deploy._EXIT_ERROR, (
            "the deploy proceeded on a required-binary set the derivation refused to "
            "vouch for — 'I don't know what this image needs' must stop a deploy, not "
            "become an empty set that gates nothing"
        )
        assert capsys.readouterr().err, "the failure must be loud (stderr), per the skill's contract"

    def test_every_required_binary_is_probed_not_just_the_first(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # COVERAGE IS A CHECKED VARIABLE: a probe that checks required[0] and stops is a
        # gate over one binary and a blind spot over the rest. Both must be exec'd.
        #
        # FIXTURE DISCRIMINATION (this pin's first draft failed to fire, and the mutation
        # caught it): the second binary must be a name that CANNOT appear in the probe's
        # own argv by accident. Named it "sh" the first time — and every `sh -c ...` the
        # probe issues contains "sh", so a build that checked only required[0] passed.
        # The canary below exists nowhere except on the PATH this test builds.
        canary = "zzz-probe-canary"
        container_bin = tmp_path / "bin"
        container_bin.mkdir()
        for present in ("sh", "git"):
            real = shutil.which(present)
            assert real is not None
            (container_bin / present).symlink_to(real)
        (container_bin / canary).write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        (container_bin / canary).chmod(0o755)

        monkeypatch.setattr(
            lore_deploy, "required_container_binaries", lambda *a, **k: ["git", canary]
        )
        fake = _install_fake_container(
            monkeypatch, tmp_path, path_env=str(container_bin)
        )

        assert lore_deploy._probe_container_binaries(_CONTAINER_NAME) == lore_deploy._EXIT_OK
        assert fake.saw_path("git"), "the probe never looked for 'git'"
        assert fake.saw_path(canary), (
            "the probe checked only the FIRST required binary — every binary in the "
            "derived set must be probed, or the set may as well be a comment"
        )


# --------------------------------------------------------------------------- #
# LAYER 3 — the SERVED branch is non-null wherever a .git exists (the cake)
# --------------------------------------------------------------------------- #
class TestProbeWorkspaceHonesty:
    """Reads what the server SERVED. The only layer that can see a git that REFUSES."""

    def _probe(
        self, monkeypatch: pytest.MonkeyPatch, port: int, container_tree: Path
    ) -> tuple[int, _FakeContainer]:
        fake = _install_fake_container(monkeypatch, container_tree)
        result = lore_deploy._probe_workspace_honesty(
            _CONTAINER_NAME, _HOST, port, _MOUNT_PATH
        )
        return result, fake

    def test_a_git_root_served_with_a_null_branch_fails_the_deploy(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # THE LOAD-BEARING PIN. This is production, exactly as it stands today: the tree
        # IS a git checkout, and the served branch is null (no git binary — or a git that
        # exits 128 on dubious ownership, #132, which layer 2 cannot see).
        tree = _make_git_repo(tmp_path / "checkout")
        with _StubMCPServer(_index_payload([_root(branch=None)])) as stub:
            result, fake = self._probe(monkeypatch, stub.port, tree)

        assert result == lore_deploy._EXIT_ERROR, (
            "the deploy accepted a container whose watched tree is a git checkout but "
            "whose SERVED git_branch is null — the feature is dead in the only "
            "environment it exists for, and nothing noticed (findings #125/#131/#132)"
        )
        assert _CONTAINER_WORKSPACE in capsys.readouterr().err, (
            "the failure must NAME the offending root"
        )
        assert fake.saw_path(_CONTAINER_WORKSPACE), (
            "the .git check must run INSIDE THE CONTAINER, against the SERVED path: the "
            "served path does not exist on the host, so a host-side stat finds no .git, "
            "skips its own check, and reports success over a dead feature"
        )

    def test_a_non_git_root_served_with_a_null_branch_is_ACCEPTED(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # THE RELATIVE FACT (commit c06c3ac: entry checks assert relative facts). A
        # project whose tree is not a git checkout legitimately has no branch. A flat
        # "the branch must not be null" gate false-fails it — and would be a gate that
        # forces every lore user to use git.
        plain = tmp_path / "not-a-repo"
        plain.mkdir()
        with _StubMCPServer(_index_payload([_root(branch=None)])) as stub:
            result, _ = self._probe(monkeypatch, stub.port, plain)

        assert result == lore_deploy._EXIT_OK, (
            "a root with no .git legitimately has no branch — the gate asserts the "
            "RELATIVE fact (.git present ⇒ branch non-null), never an absolute one"
        )

    def test_a_git_WORKTREE_whose_dot_git_is_a_FILE_is_gated(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # THE CASE THE FEATURE EXISTS FOR. In a linked git worktree ``.git`` is a FILE,
        # not a directory — so a predicate written ``test -d`` / ``.is_dir()`` skips
        # precisely the scenario #125 was raised about (an agent in a sibling worktree
        # trusting answers indexed from the main checkout) and the gate reports success
        # over the dead feature. The fixture is a REAL worktree, so the filesystem — not
        # a stub's opinion — settles it.
        main = _make_git_repo(tmp_path / "main")
        worktree = _make_git_worktree(main, tmp_path / "sibling")
        with _StubMCPServer(_index_payload([_root(branch=None)])) as stub:
            result, _ = self._probe(monkeypatch, stub.port, worktree)

        assert result == lore_deploy._EXIT_ERROR, (
            "a git WORKTREE was waved through: its .git is a FILE, not a directory, so a "
            "`test -d` / `.is_dir()` predicate skips it — and worktrees are the entire "
            "point of finding #125. The predicate is 'exists as a file OR a directory'"
        )
        assert _CONTAINER_WORKSPACE in capsys.readouterr().err

    def test_a_git_root_served_WITH_a_branch_passes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # THE POSITIVE CONTROL for the whole layer: a healthy container passes. Without
        # it, an always-failing probe would satisfy every pin above.
        tree = _make_git_repo(tmp_path / "checkout")
        with _StubMCPServer(_index_payload([_root(branch=_BRANCH)])) as stub:
            result, _ = self._probe(monkeypatch, stub.port, tree)

        assert result == lore_deploy._EXIT_OK

    def test_every_served_root_is_checked_not_just_the_first(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # ∀ over the served roots: a probe that inspects roots[0] and stops is blind to a
        # multi-root deploy (which is exactly why the section is a LIST).
        tree = _make_git_repo(tmp_path / "checkout")
        payload = _index_payload(
            [
                _root(tier="docs", branch=_BRANCH),
                _root(tier="custom", branch=None),  # the broken one, SECOND
            ]
        )
        with _StubMCPServer(payload) as stub:
            result, _ = self._probe(monkeypatch, stub.port, tree)

        assert result == lore_deploy._EXIT_ERROR, (
            "only the FIRST served root was checked — every root the server names must "
            "be gated, or a second live tree can serve a null branch unnoticed"
        )

    def test_an_all_static_config_serving_no_roots_passes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A legal config with zero LIVE roots serves an empty list. That is not a failure
        # — it is a project with nothing watched. (Distinct from the case below.)
        tree = _make_git_repo(tmp_path / "checkout")
        with _StubMCPServer(_index_payload([])) as stub:
            result, _ = self._probe(monkeypatch, stub.port, tree)

        assert result == lore_deploy._EXIT_OK

    def test_an_image_that_serves_NO_workspace_section_fails_loud(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # The #94 archetype at the deploy layer: a container running an image that
        # predates the honesty line serves NO ``workspace`` key at all. Treating "absent"
        # as "no roots to check" makes the gate pass over an image that does not have the
        # feature — green over nothing. Absent must be LOUD, and it must be
        # distinguishable from the legitimately-empty case above.
        tree = _make_git_repo(tmp_path / "checkout")
        with _StubMCPServer(_index_payload(None)) as stub:
            result, _ = self._probe(monkeypatch, stub.port, tree)

        assert result == lore_deploy._EXIT_ERROR, (
            "lore_index() served no workspace section at all (an image that predates the "
            "honesty line) and the deploy accepted it — 'the field is missing' is not "
            "'there is nothing to check'"
        )
        assert capsys.readouterr().err, "the failure must say what is wrong"

    def test_the_roots_are_read_from_the_LIVE_served_payload(self) -> None:
        # The probe must read what the RUNNING SERVER serves — not recompute the section
        # locally from lore.yaml (which would be green on a container that serves nulls).
        with _StubMCPServer(_index_payload([_root(branch=_BRANCH)])) as stub:
            roots = lore_deploy._served_workspace_roots(_HOST, stub.port, _MOUNT_PATH)
            assert stub.tool_calls == ["lore_index"], (
                "the probe must obtain the workspace section by CALLING lore_index() on "
                "the running server (the served surface), not by any local computation"
            )

        assert roots is not None
        assert [root["git_branch"] for root in roots] == [_BRANCH]

    def test_a_missing_workspace_section_reads_as_None_not_an_empty_list(
        self, tmp_path: Path
    ) -> None:
        with _StubMCPServer(_index_payload(None)) as stub:
            assert lore_deploy._served_workspace_roots(_HOST, stub.port, _MOUNT_PATH) is None

    def test_an_empty_roots_list_reads_as_an_empty_list_not_None(self, tmp_path: Path) -> None:
        # The discrimination that makes the two pins above mean anything.
        with _StubMCPServer(_index_payload([])) as stub:
            assert lore_deploy._served_workspace_roots(_HOST, stub.port, _MOUNT_PATH) == []


# --------------------------------------------------------------------------- #
# THE WIRING — a runtime gate is an invariant only over code it actually RUNS
# --------------------------------------------------------------------------- #
class TestTheProbesAreWiredIntoTheDeployVerb:
    """Not a line in a doc saying "run the smoke". Every start path that ends with a
    running container runs both probes, and a failure STOPS the deploy."""

    def _arrange(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, state: str | None,
        current_image: bool = True,
    ) -> tuple[Path, Path, list[str]]:
        project = tmp_path / "testproject"
        project.mkdir()
        (project / "lore.yaml").write_text("# stub\n", encoding="utf-8")
        env_file = tmp_path / "secrets.env"
        env_file.write_text("LORE_TEI_KEY=test\n", encoding="utf-8")

        monkeypatch.setattr(lore_deploy, "_container_state", lambda name: state)
        monkeypatch.setattr(lore_deploy, "_container_on_current_image", lambda n, i: current_image)
        monkeypatch.setattr(lore_deploy, "_image_exists", lambda image: True)
        monkeypatch.setattr(lore_deploy, "_probe_embed", lambda *a, **k: lore_deploy._EXIT_OK)
        monkeypatch.setattr(lore_deploy, "_probe_surreal", lambda *a, **k: lore_deploy._EXIT_OK)
        monkeypatch.setattr(lore_deploy, "_probe_mcp_port", lambda *a, **k: True)
        monkeypatch.setattr(lore_deploy, "_await_bind", lambda *a, **k: lore_deploy._EXIT_OK)
        monkeypatch.setattr(lore_deploy, "_launch_container", lambda *a, **k: None)
        monkeypatch.setattr(lore_deploy, "_merge_mcp_from_config", lambda *a, **k: 9201)
        monkeypatch.setattr(lore_deploy, "_run", lambda cmd, **kw: None)
        monkeypatch.setattr(
            lore_deploy, "_read_server_block", lambda config_path: (_HOST, 9201, _MOUNT_PATH)
        )
        monkeypatch.setattr(lore_deploy, "_read_config_field", lambda c, e: "0")

        ran: list[str] = []
        monkeypatch.setattr(
            lore_deploy, "_probe_container_binaries",
            lambda *a, **k: (ran.append("binaries"), lore_deploy._EXIT_OK)[1],
        )
        monkeypatch.setattr(
            lore_deploy, "_probe_workspace_honesty",
            lambda *a, **k: (ran.append("honesty"), lore_deploy._EXIT_OK)[1],
        )
        return project, env_file, ran

    @pytest.mark.parametrize(
        ("state", "current_image", "path_name"),
        [
            pytest.param(None, True, "fresh launch", id="fresh_launch"),
            pytest.param("running", True, "already running, current image", id="already_running"),
            pytest.param("running", False, "stale image → recreate", id="stale_recreate"),
        ],
    )
    def test_every_start_path_runs_both_probes(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
        state: str | None, current_image: bool, path_name: str,
    ) -> None:
        project, env_file, ran = self._arrange(
            monkeypatch, tmp_path, state=state, current_image=current_image
        )

        assert lore_deploy.verb_start(project, env_file) == lore_deploy._EXIT_OK

        assert ran == ["binaries", "honesty"], (
            f"the {path_name} path of verb_start ended with a RUNNING container but did "
            f"not run both artifact gates (ran: {ran}). A gate is an invariant only over "
            f"the code it actually RUNS — an unwired probe is a comment"
        )

    def test_a_failing_binary_probe_stops_the_deploy(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        project, env_file, _ = self._arrange(monkeypatch, tmp_path, state=None)
        monkeypatch.setattr(
            lore_deploy, "_probe_container_binaries", lambda *a, **k: lore_deploy._EXIT_ERROR
        )

        assert lore_deploy.verb_start(project, env_file) == lore_deploy._EXIT_ERROR, (
            "a container missing a required binary must FAIL the deploy loudly — a "
            "warning nobody reads is how the image shipped without git"
        )

    def test_a_failing_honesty_probe_stops_the_deploy(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        project, env_file, _ = self._arrange(monkeypatch, tmp_path, state=None)
        monkeypatch.setattr(
            lore_deploy, "_probe_workspace_honesty", lambda *a, **k: lore_deploy._EXIT_ERROR
        )

        assert lore_deploy.verb_start(project, env_file) == lore_deploy._EXIT_ERROR, (
            "the served honesty line was dead (null branch on a git tree) and the deploy "
            "reported success — the ONE thing this whole instrument exists to prevent"
        )

    # ----------------------------------------------------------------------- #
    # FIX WAVE / F1 — DEFECT-1: ``--no-wait`` is DEAD (a REGRESSION this diff shipped)
    # ----------------------------------------------------------------------- #
    def _arrange_real_gates(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        *,
        state: str | None,
        port: int,
        container_tree: Path,
        current_image: bool = True,
        bound: bool | None = None,
    ) -> tuple[Path, Path]:
        """``verb_start`` with the ARTIFACT GATES LEFT REAL — only the world is faked.

        The wiring pins above stub both probes to record that they RAN. That cannot see
        DEFECT-1, because the defect is not "a probe was skipped" — it is "a REAL probe
        was pointed at an endpoint we deliberately declined to confirm, and it did the
        only thing it can do: fail." So here ``_probe_artifact`` /
        ``_probe_container_binaries`` / ``_probe_workspace_honesty`` /
        ``_served_workspace_roots`` / ``_await_bind`` are all the REAL functions, the
        container exec seam is the faithful local simulation, and the MCP endpoint is a
        DEAD port — a fresh launch's server, mid-boot.
        """
        project = tmp_path / "testproject"
        project.mkdir()
        (project / "lore.yaml").write_text("# stub\n", encoding="utf-8")
        env_file = tmp_path / "secrets.env"
        env_file.write_text("LORE_TEI_KEY=test\n", encoding="utf-8")

        monkeypatch.setattr(lore_deploy, "_container_state", lambda name: state)
        monkeypatch.setattr(lore_deploy, "_container_on_current_image", lambda n, i: current_image)
        monkeypatch.setattr(lore_deploy, "_image_exists", lambda image: True)
        monkeypatch.setattr(lore_deploy, "_probe_embed", lambda *a, **k: lore_deploy._EXIT_OK)
        monkeypatch.setattr(lore_deploy, "_probe_surreal", lambda *a, **k: lore_deploy._EXIT_OK)
        monkeypatch.setattr(lore_deploy, "_launch_container", lambda *a, **k: None)
        monkeypatch.setattr(lore_deploy, "_merge_mcp_from_config", lambda *a, **k: 9201)
        # ``podman`` is neutered; every OTHER _run passes through to the REAL one. The
        # derivation (``required_container_binaries``) shells out through this same seam to
        # the loremaster interpreter, and layer 2 is one of the things under test here —
        # stubbing _run wholesale would hand it a None and fail the probe on an
        # AttributeError instead of on the defect. (Caught by the positive control below,
        # which is exactly what a positive control is for.)
        real_run = lore_deploy._run

        def _no_podman(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            if cmd and cmd[0] == "podman":
                return subprocess.CompletedProcess(cmd, 0, "", "")
            return real_run(cmd, **kwargs)

        monkeypatch.setattr(lore_deploy, "_run", _no_podman)
        monkeypatch.setattr(
            lore_deploy, "_read_server_block", lambda config_path: (_HOST, port, _MOUNT_PATH)
        )
        monkeypatch.setattr(lore_deploy, "_read_config_field", lambda c, e: "0")
        if bound is not None:
            monkeypatch.setattr(lore_deploy, "_probe_mcp_port", lambda *a, **k: bound)
        _install_fake_container(monkeypatch, container_tree)
        return project, env_file

    @pytest.mark.parametrize(
        ("state", "current_image", "bound", "path_name"),
        [
            pytest.param(None, True, None, "fresh launch", id="fresh_launch"),
            pytest.param("running", False, None, "stale image → recreate", id="stale_recreate"),
            pytest.param(
                "running", True, False, "already running, port not yet bound",
                id="already_running_unbound",
            ),
        ],
    )
    def test_no_wait_does_not_gate_an_endpoint_it_declined_to_confirm(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        state: str | None,
        current_image: bool,
        bound: bool | None,
        path_name: str,
    ) -> None:
        """THE REGRESSION PIN (DEFECT-1). ``--no-wait`` is documented, wired into argparse
        (``lore_deploy.py:1371``), described in ``SKILL.md:82`` — and DEAD.

        ``_await_bind(no_wait=True)`` deliberately declines to confirm the endpoint is up
        ("fire-and-forget, operator's call"). ``_probe_artifact`` is then called
        UNCONDITIONALLY on all three start paths and immediately HTTP-POSTs that very
        endpoint. On a fresh launch the server is mid-boot (~150s), so the connect is
        refused, layer 3 reads ``None``, and ``verb_start`` returns ``_EXIT_ERROR`` —
        blaming a stale image for a wait the operator asked us not to do.

        ZERO tests drove ``no_wait`` through ``verb_start``: 5435 green tests sail over a
        dead flag, which is exactly why the absence IS the defect.

        The invariant: a gate may not be run against an endpoint whose liveness we
        DECLINED to establish. Whether the (container-local, endpoint-independent) binary
        probe still runs is deliberately NOT pinned here — see
        ``test_a_confirmed_endpoint_is_gated_even_under_no_wait`` and the report's F1 fork.
        """
        tree = _make_git_repo(tmp_path / "checkout")
        project, env_file = self._arrange_real_gates(
            monkeypatch, tmp_path, state=state, current_image=current_image,
            bound=bound, port=_dead_port(), container_tree=tree,
        )

        result = lore_deploy.verb_start(project, env_file, no_wait=True)

        assert result == lore_deploy._EXIT_OK, (
            f"the {path_name} path FAILED the deploy under --no-wait. The operator asked "
            f"us NOT to wait for the endpoint; we then ran a gate that HTTP-POSTs that "
            f"endpoint, met the refusal we ourselves guaranteed, and reported 'the "
            f"container is running an image that predates the honesty line'. Skip (or "
            f"defer) the artifact gates when the bind was never confirmed, and SAY SO on "
            f"stdout — the way _await_bind announces its own skip (DEFECT-1)"
        )

    @pytest.mark.parametrize(
        ("state", "current_image", "bound", "path_name"),
        [
            pytest.param(None, True, None, "fresh launch", id="fresh_launch"),
            pytest.param("running", False, None, "stale image → recreate", id="stale_recreate"),
            pytest.param(
                "running", True, False, "already running, port not yet bound",
                id="already_running_unbound",
            ),
        ],
    )
    def test_the_skipped_gate_is_ANNOUNCED_not_silently_dropped(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        state: str | None,
        current_image: bool,
        bound: bool | None,
        path_name: str,
    ) -> None:
        """A gate that silently does not run is worse than one that fails: the deploy
        prints its success line and the operator believes the artifact was checked.

        ``_arrange`` stubs ``_await_bind``, so ITS "--no-wait set" line cannot print here
        — any skip announcement in this stdout is ``verb_start``'s own, and today there is
        none. Both probes are stubbed to RECORD, so the pin also proves they did not run.
        """
        project, env_file, ran = self._arrange(
            monkeypatch, tmp_path, state=state, current_image=current_image
        )
        if bound is not None:
            monkeypatch.setattr(lore_deploy, "_probe_mcp_port", lambda *a, **k: bound)

        assert lore_deploy.verb_start(project, env_file, no_wait=True) == lore_deploy._EXIT_OK

        out = capsys.readouterr().out
        assert "honesty" not in ran, (
            f"the {path_name} path ran the SERVED-honesty gate against an endpoint it "
            f"declined to confirm (ran: {ran}) — the gate can only fail there, and it "
            f"blames the image for it (DEFECT-1)"
        )
        assert "binaries" in ran, (
            f"the {path_name} path skipped the required-BINARY gate under --no-wait too "
            f"(ran: {ran}). Layer 2 is a `podman exec`: it needs a running CONTAINER, not a "
            f"bound PORT — the endpoint has nothing to do with it. Skipping it disarms the "
            f"ONE check that would have caught the git-less image for three months (#131), "
            f"for a reason that does not apply to it. Only layer 3 reads the endpoint; only "
            f"layer 3 may be excused by an unconfirmed one (NEW-2)"
        )
        announcement = [
            line for line in out.splitlines()
            if _hits(line, _GATE_WORDS) and _hits(line, _SKIP_WORDS)
        ]
        assert announcement, (
            f"the {path_name} path skipped an artifact gate SILENTLY and still printed a "
            f"success line. Announce it on stdout — name the gate that did not run — so "
            f"the operator knows the artifact is UNVERIFIED, not verified. Got:\n{out}"
        )
        assert "no-wait" in out.lower(), (
            f"the skip announcement must name the FLAG that caused it (--no-wait), so the "
            f"operator can connect the missing gate to their own choice. Got:\n{out}"
        )

    def test_a_confirmed_endpoint_is_gated_even_under_no_wait(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """THE ANTI-REGRESSION PIN for the over-broad fix (and the F1 fork — see report).

        On the already-running path the deploy PROBES the port FIRST and only waits if it
        is not yet accepting. When that probe succeeds, the endpoint is CONFIRMED UP and
        ``_await_bind`` is never reached: ``--no-wait`` never took effect, so nothing was
        declined and both gates can and must run.

        A fix that reads "no_wait ⇒ skip the gates" (three paths, unconditionally) silently
        disarms the #125/#131 artifact gate for the single most common invocation there is
        — ``start`` against an already-running container — for anyone who habitually passes
        the flag. That re-opens the hole this whole packet closed, and no other pin sees it.
        GREEN on today's code (the gates run); RED on the over-broad fix.
        """
        project, env_file, ran = self._arrange(
            monkeypatch, tmp_path, state="running", current_image=True
        )
        monkeypatch.setattr(lore_deploy, "_probe_mcp_port", lambda *a, **k: True)

        assert lore_deploy.verb_start(project, env_file, no_wait=True) == lore_deploy._EXIT_OK

        assert ran == ["binaries", "honesty"], (
            f"the endpoint was PROVEN up (the port probe answered) and --no-wait therefore "
            f"never took effect — yet the artifact gates were skipped anyway (ran: {ran}). "
            f"'Do not wait' is not 'do not check': skipping a gate we CAN run turns "
            f"--no-wait into a global off-switch for the #125/#131 instrument"
        )

    @pytest.mark.parametrize(
        ("state", "current_image", "bound", "path_name"),
        [
            pytest.param(None, True, None, "fresh launch", id="fresh_launch"),
            pytest.param("running", False, None, "stale image → recreate", id="stale_recreate"),
            pytest.param(
                "running", True, False, "already running, port not yet bound",
                id="already_running_unbound",
            ),
        ],
    )
    def test_the_BINARY_gate_still_STOPS_the_deploy_under_no_wait(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        state: str | None,
        current_image: bool,
        bound: bool | None,
        path_name: str,
    ) -> None:
        """NEW-2's payload. The pin above proves layer 2 RUNS under ``--no-wait``; this one
        proves its verdict still BITES.

        A build that runs the binary probe and then ignores its exit code satisfies "binaries"
        in ``ran`` perfectly — and ships the git-less image anyway. **Running a gate and
        heeding a gate are two different claims**, and this repo has shipped the first while
        believing the second (finding #102: "ROUTING IS NOT SHARING — a caller that calls the
        shared driver but hand-rolls the decision underneath it is a private copy wearing the
        shared name"). So: force layer 2 to FAIL, and require the deploy to STOP.
        """
        project, env_file, _ = self._arrange(
            monkeypatch, tmp_path, state=state, current_image=current_image
        )
        if bound is not None:
            monkeypatch.setattr(lore_deploy, "_probe_mcp_port", lambda *a, **k: bound)
        monkeypatch.setattr(
            lore_deploy, "_probe_container_binaries", lambda *a, **k: lore_deploy._EXIT_ERROR
        )

        assert lore_deploy.verb_start(project, env_file, no_wait=True) == lore_deploy._EXIT_ERROR, (
            f"the {path_name} path found a container MISSING a binary the shipped code execs "
            f"and reported SUCCESS, because --no-wait was set. The binary gate does not need "
            f"the endpoint and must not be excused by it — this is the exact failure (#131) "
            f"the whole packet exists to close, surviving inside the flag (NEW-2)"
        )

    @pytest.mark.parametrize(
        ("state", "current_image", "bound", "path_name"),
        [
            pytest.param(None, True, None, "fresh launch", id="fresh_launch"),
            pytest.param("running", False, None, "stale image → recreate", id="stale_recreate"),
            pytest.param(
                "running", True, False, "already running, port not yet bound",
                id="already_running_unbound",
            ),
        ],
    )
    def test_the_skip_announcement_does_not_claim_the_BINARY_gate_was_skipped(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        state: str | None,
        current_image: bool,
        bound: bool | None,
        path_name: str,
    ) -> None:
        """SERVED ENGLISH — this repo's most expensive defect class, guarded mechanically.

        Today the announcement reads *"the artifact gates (required container binaries, served
        honesty line) were SKIPPED"*. Once layer 2 always runs, that sentence is a LIE in the
        one direction that matters: it tells an operator the binary check did not happen when
        it did, so they will re-run the deploy to get a check they already have — or, worse,
        distrust a gate that is in fact protecting them.

        The repo's law (CLAUDE.md, "A DIAGNOSIS IS NOT AN INSTRUMENT"): prose that describes
        behaviour must be DERIVED from the behaviour, not restated beside it. There is no
        derivation available for a print() string, so this pin is the instrument: the skip
        announcement must name the HONESTY LINE, and must not put the word "binaries" inside a
        sentence that says something was skipped.
        """
        project, env_file, ran = self._arrange(
            monkeypatch, tmp_path, state=state, current_image=current_image
        )
        if bound is not None:
            monkeypatch.setattr(lore_deploy, "_probe_mcp_port", lambda *a, **k: bound)

        assert lore_deploy.verb_start(project, env_file, no_wait=True) == lore_deploy._EXIT_OK
        out = capsys.readouterr().out

        # Scoped to the SENTENCE, not the line — and that granularity is load-bearing. The
        # announcement is one long print(), so a line-scoped pin cannot tell "the binary gate
        # was skipped" (a lie) from "the honesty line was skipped; the binaries WERE checked"
        # (the truth, and MORE informative than saying nothing). The first draft of this pin
        # was line-scoped and went RED against a correct build — the probe firing for the
        # wrong reason, which is the failure mode the repo's own law warns about.
        sentences = [
            sentence for sentence in re.split(r"(?<=[.!?])\s+", out) if sentence.strip()
        ]
        skipped = [sentence for sentence in sentences if _hits(sentence, _SKIP_WORDS)]
        assert skipped, f"the {path_name} path announced no skip at all. Got:\n{out}"

        lying = [sentence for sentence in skipped if "binar" in sentence.lower()]
        assert not lying, (
            f"a sentence tells the operator the required-BINARY gate was skipped, and it was "
            f"not — layer 2 ran (ran: {ran}). A gate that runs while the deploy says it did "
            f"not is a false NEGATIVE: the operator re-runs to obtain a check they already "
            f"have, or stops trusting the one thing that IS protecting them. Name the honesty "
            f"line, which really was skipped. (Saying the binaries WERE checked, in a sentence "
            f"of its own, is fine — better than fine.)\nSentence(s): {lying}"
        )
        assert any("honest" in sentence.lower() for sentence in skipped), (
            f"the skip announcement must name WHICH gate did not run — the served honesty "
            f"line (layer 3), the only gate that reads the endpoint. 'The artifact gates' is "
            f"the sentence that is now wrong. Got:\n{out}"
        )

    def test_an_unreachable_endpoint_STILL_fails_when_no_wait_is_NOT_set(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """THE POSITIVE CONTROL for every F1 pin above — and the one that kills the lazy fix.

        A build that simply DELETES the artifact gates, or that swallows an unreachable
        endpoint everywhere, passes all four pins above. It dies here: with ``--no-wait``
        UNSET, ``_await_bind`` says the endpoint is up, the real gate then finds it dead —
        and that contradiction must STOP the deploy, exactly as it does today.
        """
        tree = _make_git_repo(tmp_path / "checkout")
        project, env_file = self._arrange_real_gates(
            monkeypatch, tmp_path, state=None, port=_dead_port(), container_tree=tree,
        )
        monkeypatch.setattr(lore_deploy, "_await_bind", lambda *a, **k: lore_deploy._EXIT_OK)

        assert lore_deploy.verb_start(project, env_file, no_wait=False) == lore_deploy._EXIT_ERROR, (
            "the deploy waited for the bind, was told the endpoint was up, then could not "
            "read lore_index() from it — and shipped anyway. Without --no-wait an "
            "unreachable endpoint is a HARD failure; the F1 fix must narrow the gate to "
            "the case the operator opted out of, never remove it"
        )


# --------------------------------------------------------------------------- #
# FIX WAVE / F2 — DEFECT-2(a) + R1: three causes, three DISTINCT diagnoses
# --------------------------------------------------------------------------- #
class TestTheDiagnosisNamesTheRealCause:
    """A WRONG diagnosis is worse than none: it sends the reader to fix something that was
    never broken, and it hides the thing that was.

    Today ``_probe_workspace_honesty`` collapses THREE different worlds into two messages:

    1. the endpoint was UNREACHABLE (mid-boot, or ``--no-wait``) ─┐ both print "the
    2. the image genuinely lacks the ``workspace`` field ─────────┘ container is running
       an image that predates the honesty line … Rebuild the image" — so cause (1) is
       answered with a rebuild that fixes nothing;
    3. a git WORKTREE mount, whose ``.git`` FILE names an absolute host gitdir that is NOT
       inside ``/workspace``: git exits 128, the branch is null — and the message blames a
       missing git binary or a missing ``--userns=keep-id``, NEITHER of which is the cause,
       and names none of the real cures.

    The pins are SYMMETRIC — every "must not blame X" is paired with a case that MUST blame
    X. A build that swaps one blanket message for another blanket message fails both halves.

    Scope (operator ruling, brief §F2): this fixes the DIAGNOSIS. Making worktree deploys
    actually WORK is finding #134, ledgered to packets 17/23 — no pin here asks for it.
    """

    def _probe(
        self, monkeypatch: pytest.MonkeyPatch, port: int, container_tree: Path
    ) -> int:
        _install_fake_container(monkeypatch, container_tree)
        return lore_deploy._probe_workspace_honesty(
            _CONTAINER_NAME, _HOST, port, _MOUNT_PATH
        )

    def test_an_unreachable_endpoint_is_not_diagnosed_as_a_stale_image(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # CAUSE 1. Nothing is listening: the server is mid-boot (or --no-wait declined to
        # wait for it). The image is FINE. Telling the operator to rebuild and recreate it
        # is a 150-second wait answered with a 10-minute rebuild — and the real cause
        # (wait, or raise --bind-timeout) is never named.
        tree = _make_git_repo(tmp_path / "checkout")

        result = self._probe(monkeypatch, _dead_port(), tree)

        assert result == lore_deploy._EXIT_ERROR, "an unreadable endpoint is still a failure"
        err = capsys.readouterr().err
        assert _hits(err, _UNREACHABLE_TOKENS), (
            f"the endpoint could not be reached and the message never says so. Got:\n{err}"
        )
        assert not _hits(err, _OLD_IMAGE_TOKENS), (
            f"a connect error was diagnosed as 'the container is running an image that "
            f"predates the honesty line — rebuild the image'. The image is not the "
            f"problem; nothing answered the socket. A wrong diagnosis is worse than none "
            f"(blamed: {_hits(err, _OLD_IMAGE_TOKENS)}). Got:\n{err}"
        )

    def test_an_image_without_the_workspace_field_is_not_diagnosed_as_unreachable(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # CAUSE 2 — and the POSITIVE CONTROL for the pin above. A LIVE server ANSWERS; its
        # payload carries no ``workspace`` section, because the image predates the honesty
        # line. Here the rebuild IS the cure — and blaming the endpoint would send the
        # operator to poll a port that is answering perfectly.
        tree = _make_git_repo(tmp_path / "checkout")
        with _StubMCPServer(_index_payload(None)) as stub:
            result = self._probe(monkeypatch, stub.port, tree)

        assert result == lore_deploy._EXIT_ERROR
        err = capsys.readouterr().err
        assert _hits(err, _OLD_IMAGE_TOKENS), (
            f"a live server served a payload with NO workspace section — the image "
            f"predates the honesty line and must be rebuilt — and the message does not "
            f"say so. Got:\n{err}"
        )
        assert not _hits(err, _UNREACHABLE_TOKENS), (
            f"the endpoint answered perfectly and the message still blames it for being "
            f"unreadable ({_hits(err, _UNREACHABLE_TOKENS)}). These are two different "
            f"worlds with two different cures; one message for both is a coin flip that "
            f"the operator has to debug. Got:\n{err}"
        )

    def test_a_worktree_whose_gitdir_is_outside_the_mount_says_so(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # CAUSE 3 (DEFECT-2). The tree at /workspace is a linked git WORKTREE — the very
        # topology #125 is named after. Its ``.git`` is a FILE naming an ABSOLUTE HOST path
        # (``…/lore/.git/worktrees/<name>``) that is NOT inside the mount, so git inside the
        # container exits 128 and the served branch is null. The tree HAS a .git, so layer 3
        # correctly fires — and then tells the operator to check the git binary and to add
        # ``--userns=keep-id``. Both are already fine. The real cures (mount the parent
        # gitdir, set GIT_DIR, `git worktree repair`) are named NOWHERE.
        main = _make_git_repo(tmp_path / "main")
        worktree = _make_git_worktree(main, tmp_path / "sibling")
        _break_the_worktree_gitdir(worktree)

        with _StubMCPServer(_index_payload([_root(branch=None)])) as stub:
            result = self._probe(monkeypatch, stub.port, worktree)

        assert result == lore_deploy._EXIT_ERROR, (
            "a worktree mount whose gitdir is outside /workspace serves a null branch on a "
            "tree that HAS a .git — layer 3 must still fire (finding #134 makes it WORK; "
            "this pin only makes it TELL THE TRUTH)"
        )
        err = capsys.readouterr().err
        assert "worktree" in err.lower(), (
            f"the root is a linked git worktree whose gitdir is not inside the mount, and "
            f"the diagnosis never says the word. Got:\n{err}"
        )
        assert _hits(err, _WORKTREE_CURE_TOKENS), (
            f"the diagnosis names no CURE the operator can act on. A worktree's gitdir "
            f"lives outside the mounted tree: the fixes are to mount the parent gitdir, to "
            f"set GIT_DIR, or to run `git worktree repair`. A diagnosis without a cure is "
            f"a shrug with a stack trace. Got:\n{err}"
        )
        assert not _hits(err, _REFUSING_GIT_CURE_TOKENS), (
            f"the message blames a missing git binary / dubious ownership / --userns="
            f"keep-id ({_hits(err, _REFUSING_GIT_CURE_TOKENS)}) — NONE of which is the "
            f"cause here (git is present, the uid maps fine, and the tree is readable). "
            f"Following that advice changes nothing and hides the real fault. Got:\n{err}"
        )

    def test_a_normal_checkout_served_null_keeps_the_missing_git_diagnosis(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # POSITIVE CONTROL for the worktree pin. A NORMAL checkout (``.git`` is a directory,
        # perfectly resolvable) served with a null branch means what it has always meant:
        # the git binary is missing from the image (#131) or git is REFUSING the tree
        # (dubious ownership, #132). That diagnosis — and those cures — must SURVIVE the
        # fix. Without this leg, "say worktree" could be satisfied by saying worktree
        # everywhere, which is the same blanket-message defect with new prose.
        tree = _make_git_repo(tmp_path / "checkout")
        with _StubMCPServer(_index_payload([_root(branch=None)])) as stub:
            result = self._probe(monkeypatch, stub.port, tree)

        assert result == lore_deploy._EXIT_ERROR
        err = capsys.readouterr().err
        assert _hits(err, _REFUSING_GIT_CURE_TOKENS), (
            f"a plain git checkout serving a null branch lost its diagnosis: the causes "
            f"are a missing git binary (#131) or a git refusing the tree (#132), and the "
            f"cures must still be named. Got:\n{err}"
        )
        assert "worktree" not in err.lower(), (
            f"a NORMAL checkout was diagnosed as a worktree problem — the blanket message "
            f"defect, re-shipped with different words. Got:\n{err}"
        )

    def test_a_HEALTHY_worktree_is_not_blamed_on_its_gitdir(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # THE FIXTURE THAT KILLS THE NAME-LIST FIX. The cheap way to satisfy the worktree
        # pin is ``if .git is a FILE: print the worktree message`` — keyed on the SHAPE.
        # But a worktree whose gitdir IS reachable (properly mounted, or repaired) is a
        # perfectly healthy git tree: if IT serves a null branch, the cause is a missing or
        # refusing git, and prescribing `git worktree repair` sends the operator to fix a
        # thing that already works. The predicate must key on the gitdir being UNREACHABLE,
        # never on ``.git`` being a file.
        main = _make_git_repo(tmp_path / "main")
        worktree = _make_git_worktree(main, tmp_path / "sibling")
        assert (worktree / ".git").is_file()
        assert _git(worktree, "rev-parse", "--abbrev-ref", "HEAD"), "the gitdir must RESOLVE"

        with _StubMCPServer(_index_payload([_root(branch=None)])) as stub:
            result = self._probe(monkeypatch, stub.port, worktree)

        assert result == lore_deploy._EXIT_ERROR
        err = capsys.readouterr().err
        assert not _hits(err, _WORKTREE_CURE_TOKENS), (
            f"this worktree's gitdir RESOLVES — git works here. The null branch means the "
            f"binary is missing or git is refusing the tree, yet the message prescribes the "
            f"outside-the-mount cures ({_hits(err, _WORKTREE_CURE_TOKENS)}). The diagnosis "
            f"must key on the gitdir being UNREACHABLE, not on `.git` being a FILE — "
            f"keying on the shape is the name-list, one level down. Got:\n{err}"
        )
        assert _hits(err, _REFUSING_GIT_CURE_TOKENS), (
            f"the real causes for a resolvable tree serving a null branch (missing git "
            f"binary, refusing git) went unnamed. Got:\n{err}"
        )


# --------------------------------------------------------------------------- #
# FIX WAVE / F6 — R3: an empty required set is REPORTED, never rendered as "OK ()"
# --------------------------------------------------------------------------- #
class TestTheEmptySetIsReportedHonestly:
    """``probe: container binaries OK ()`` is the shape of a vacuous gate.

    The set can be legitimately empty — shipped packages that exec nothing require no
    binary, and ``test_shipped_packages_that_exec_NOTHING_are_a_legitimate_empty_answer``
    pins exactly that. The DANGEROUS empties (a scan over no modules; a module whose spawn
    sites the scan cannot resolve) already RAISE, and are converted here into a loud deploy
    failure. So the empty set that reaches this line is a real answer — and it must READ
    like one, not like a gate that forgot its arguments.
    """

    def test_an_empty_required_set_reads_as_NO_binaries_not_an_empty_group(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(lore_deploy, "required_container_binaries", lambda *a, **k: [])
        _install_fake_container(monkeypatch, tmp_path)

        assert lore_deploy._probe_container_binaries(_CONTAINER_NAME) == lore_deploy._EXIT_OK, (
            "shipped packages that exec nothing require no binary — a legitimate empty "
            "answer, vouched for by the derivation, and not a failure"
        )
        out = capsys.readouterr().out
        assert "()" not in out, (
            f"the probe printed an empty group — the visual signature of a gate that "
            f"iterated over nothing. Say it in words: the shipped code execs no external "
            f"binary, so there is nothing to require. Got:\n{out}"
        )
        assert _hits(out, ("no external", "none", "no binaries", "nothing")), (
            f"the empty answer must be STATED, so an operator reading the log can tell "
            f"'the scan found nothing to require' from 'the scan found nothing'. Got:\n{out}"
        )

    def test_a_NON_empty_set_still_names_every_binary(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # POSITIVE CONTROL: the ordinary path must keep naming what it checked, or the pin
        # above could be satisfied by a probe that prints nothing useful at all.
        canary = "zzz-probe-canary"
        container_bin = tmp_path / "bin"
        container_bin.mkdir()
        real_sh = shutil.which("sh")
        assert real_sh is not None
        (container_bin / "sh").symlink_to(real_sh)
        (container_bin / canary).write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        (container_bin / canary).chmod(0o755)
        monkeypatch.setattr(lore_deploy, "required_container_binaries", lambda *a, **k: [canary])
        _install_fake_container(monkeypatch, tmp_path, path_env=str(container_bin))

        assert lore_deploy._probe_container_binaries(_CONTAINER_NAME) == lore_deploy._EXIT_OK
        assert canary in capsys.readouterr().out, (
            "the probe must name the binaries it actually checked"
        )
