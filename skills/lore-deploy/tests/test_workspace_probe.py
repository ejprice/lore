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
        # Pointed at a SYNTHETIC workspace whose shipped code execs ``rg`` (never
        # ``git``), the deploy's required set must be ["rg"]. A hardcoded ["git"] — which
        # would agree with the real repo today, and so pass any real-repo comparison —
        # dies right here.
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "s"\nversion = "0"\n\n[tool.uv.workspace]\nmembers = ["alpha"]\n',
            encoding="utf-8",
        )
        package = tmp_path / "alpha" / "alpha"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "runner.py").write_text(
            'import subprocess\n\n\ndef go() -> None:\n    subprocess.run(["rg"], check=False)\n',
            encoding="utf-8",
        )

        assert lore_deploy.required_container_binaries(tmp_path) == ["rg"], (
            "the deploy's required-binary set must be DERIVED from the shipped source "
            "(loremaster.shellout.required_binaries) — a hand-kept list is a list someone "
            "must remember to update, which is exactly how the image lost git"
        )

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
