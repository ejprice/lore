"""Contract — finding #125, "the honesty line": ``lore_index`` must surface the
tree it is ACTUALLY indexing (the watched root paths + their git branches).

The defect this closes: an agent working in a sibling git WORKTREE queries lore,
silently receives answers indexed from the MAIN checkout, and never learns the two
differ. Both auditors in the #102 DRY wave had to INFER that. The fix is not to
index worktrees (that is packets 17/23) — it is HONESTY: the status read names the
watched path and the branch, so a caller in a different tree sees the mismatch
immediately.

The contract this file pins (the shape a builder must satisfy):

* ``loremaster.server.WatchedRoot`` — one live root: ``tier`` / ``path`` (ABSOLUTE)
  / ``git_branch`` / ``git_ref`` (both ``None``-defaulted).
* ``loremaster.server.WorkspaceStatus`` — the typed section: ``roots: list[WatchedRoot]``
  with a ``default_factory`` empty default (the F3 additive-schema shape
  :class:`~loremaster.server.IndexStatusSummary`'s own docstring prescribes for the
  NEXT field addition — never a bare required field).
* ``IndexStatusSummary.workspace: WorkspaceStatus`` — defaulted, so every existing
  construction site keeps validating untouched.
* ``loremaster.server.build_workspace_status(config) -> WorkspaceStatus`` — the pure
  builder over :attr:`~loremaster.config.LoreConfig.effective_roots`, which reads git
  identity by CALLING the pre-existing shared seam
  :func:`~loremaster.index.snapshots.capture_git_identity` (repo standing law, "ONE
  IMPLEMENTATION": a second git reader in ``server.py`` is a defect, not an
  implementation — :class:`TestSharesTheGitSeam` proves the sharing BY MUTATION).
* ``AppContext._build_index_status`` populates it, so ``lore_index()`` actually SERVES
  it (:class:`TestServedEndToEnd` — a model and a helper nothing CALLS is exactly the
  #94 archetype).

Design decisions taken here, and why (raised in REPORT-pkt01-contract-1.md):

1. A LIST, not a single path. A config may declare several live roots (multi-tier
   deploys do), so a single ``workspace_path`` field would be a LIE the moment there
   are two. ``TestBuildWorkspaceStatusFates::test_every_live_root_carries_its_own_branch``
   uses TWO live roots on DIFFERENT branches precisely so a build that reads git once
   and reuses the answer, or serves only ``effective_roots[0]``, goes RED.
2. STATIC roots are excluded: they are BATCH-indexed and frozen, never watched, so
   listing one would be a freshness lie in the section whose job is not lying. The
   exclusion keys on the watch POLICY (``watch != live``) and NOT on the proxy "it
   declares no path" — a static root MAY legally declare a ``path`` (the validator
   only ADDS source/version/provider requirements for static; it never forbids a
   path — verified), and mypy actively pushes a builder toward the proxy filter,
   because ``root.path`` is ``str | None`` and must be narrowed before use.
   ``test_a_static_root_that_DECLARES_a_path_is_still_not_watched`` is the pin that
   tells the two apart.
3. The served ``path`` is ABSOLUTE. A config may say ``path: .`` (the documented
   single-tree style); serving "." back to a caller in another tree is not an honesty
   line, it is noise. The git identity is read from the SAME tree that is reported —
   pinned in :meth:`TestSharesTheGitSeam.test_git_is_read_from_the_tree_that_is_reported`.

Fixture-value discipline (this repo's #1 repeat defect — monoculture): NO fixture in
this file uses this repo's own path or its ``feat/surreal-unification`` branch. Every
git fixture is a throwaway repo under ``tmp_path`` on a deliberately foreign branch
name, so a build that hardcodes either fails.

How to run:
    uv run pytest loremaster/tests/test_workspace_status.py -n auto -q
(The live-store class needs the spike-surreal dev server on ws://127.0.0.1:18000 —
NEVER :18500, which is production.)
"""

from __future__ import annotations

import ast
import asyncio
import os
import subprocess
import time
import uuid
from collections.abc import AsyncIterator, Callable, Mapping
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import loremaster.index.snapshots as snapshots_module
import loremaster.server as server_module
import pytest
import pytest_asyncio
from _surreal_harness import (
    TEST_NAMESPACE,
    make_env,
    surreal_password,
    surreal_url,
    surreal_user,
)
from _surreal_harness import (
    drop_database as drop_surreal_database,
)
from loremaster.config import LoreConfig
from loremaster.sanitise import SafeLine, safe_str
from loremaster.server import (
    IndexStatusSummary,
    LoreServer,
    WatchedRoot,
    WorkspaceStatus,
    build_app_context,
    build_mcp_server,
    build_workspace_status,
)
from loresigil.testing import FakeEmbedder
from pydantic import ValidationError

# The production embedding dimensionality (every FakeEmbedder here uses it).
_DIM = 2048
_SURREAL_USER_ENV = "SURREAL_USER"
_SURREAL_PASS_ENV = "SURREAL_PASS"

# Branch names deliberately UNLIKE this repo's own (``feat/surreal-unification``):
# a build that hardcodes the host repo's branch must fail every pin below.
_BRANCH_A = "spike/honesty-line"
_BRANCH_B = "wt/second-tree"

# A hostile directory name: a newline, a backtick run, and a ROW-SHAPED FORGERY line
# mimicking lore's own table output. A branch name cannot carry a control char (git's
# ``check-ref-format`` refuses it — verified), but a PATH on disk can: this exact
# directory is creatable on ext4/ZFS and ``git init`` works inside it (both verified
# before this contract was written), so it is a REAL value the served surface can meet.
_HOSTILE_DIR_NAME = "tree\n| tier | path | branch |\n```\n- forged: yes"

# The same shape, as a hostile value arriving THROUGH the git seam (a corrupted ref,
# a future git that stops quoting, a hand-rolled reader that splits wrong). Reached by
# patching the seam, since real git will not mint such a branch.
_HOSTILE_BRANCH = "main\n| tier | path | branch |\n``` forged"

# Git invocations run with the ambient user/system config NEUTRALISED (a global
# ``commit.gpgsign``, hook path, or ``init.defaultBranch`` on the host must not decide
# what this contract observes) and an explicit identity, so the fixtures are hermetic.
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
    """Run one git command rooted at ``repo``; return its stripped stdout."""
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
        env=_GIT_ENV,
    )
    return result.stdout.strip()


def _make_git_repo(path: Path, *, branch: str, commit: bool = True) -> str | None:
    """Create a git repo at ``path`` on ``branch``; return its HEAD sha (or ``None``).

    ``commit=False`` leaves a freshly-``init``ed repo with NO commits — a real state in
    which ``git rev-parse HEAD`` fails, so the shared seam returns ``(None, None)``.
    """
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-b", branch)
    if not commit:
        return None
    (path / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(path, "add", "module.py")
    _git(path, "commit", "-m", "seed")
    return _git(path, "rev-parse", "HEAD")


def _root(tier: str, path: Path) -> dict[str, Any]:
    """A live root declaration for :func:`_config`."""
    return {"tier": tier, "watch": "live", "path": str(path), "include": ["**/*.py"]}


def _config(
    *,
    slug: str,
    roots: list[dict[str, Any]],
    project_root: str = ".",
) -> LoreConfig:
    """A validated :class:`LoreConfig` with the given roots (no store contact)."""
    payload: dict[str, Any] = {
        "schema_version": 1,
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
        "project": {"slug": slug, "root": project_root},
        "embedding": {
            "backend": "tei",
            "base_url": "http://localhost:8080",
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": _DIM,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": "LORE_TEI_KEY",
            "tokenizer": "voyage-4-nano",
        },
        # No explicit ``database`` — it derives from the (uuid4-unique) slug, so every
        # test owns a throwaway SurrealDB database (reaped by ``_surreal_test_env``).
        "surreal": {"url": surreal_url(), "namespace": TEST_NAMESPACE},
        "roots": roots,
        "include": ["**/*.py"],
        "exclude_dirs": [".git"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": False,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9241},
    }
    return LoreConfig.model_validate(payload)


_pending_surreal_slugs: list[str] = []


def _slug() -> str:
    """A unique per-test slug — also the throwaway SurrealDB database name."""
    slug = f"test_{uuid.uuid4().hex}"
    _pending_surreal_slugs.append(slug)
    return slug


@pytest_asyncio.fixture(autouse=True)
async def _surreal_test_env(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[None]:
    """Export the harness root credentials; reap every database this module minted."""
    monkeypatch.setenv(_SURREAL_USER_ENV, surreal_user())
    monkeypatch.setenv(_SURREAL_PASS_ENV, surreal_password().get_secret_value())
    try:
        yield
    finally:
        for slug in _pending_surreal_slugs:
            await drop_surreal_database(make_env(database=slug, dim=_DIM))
        _pending_surreal_slugs.clear()


def _identity_spy(
    answers: Mapping[str, tuple[str | None, str | None]],
    calls: list[Path],
) -> Callable[[Path], tuple[str | None, str | None]]:
    """A stand-in for the shared git seam: records its calls, answers per RESOLVED path.

    Deliberately answers a DIFFERENT value per root, so a build that reads git once and
    reuses the answer across roots cannot pass.
    """

    def _capture(repo_root: Path) -> tuple[str | None, str | None]:
        resolved = Path(repo_root).resolve()
        calls.append(resolved)
        return answers.get(str(resolved), (None, None))

    return _capture


# --------------------------------------------------------------------------- #
# The section models — shape + the F3 additive-schema guarantee
# --------------------------------------------------------------------------- #
class TestWorkspaceStatusModels:
    """``WatchedRoot`` / ``WorkspaceStatus`` / the ``IndexStatusSummary`` section."""

    def test_watched_root_defaults_the_git_identity_to_none(self) -> None:
        # A root whose git identity is unknowable (a non-git tree) is still a root worth
        # naming — the path alone already reveals a worktree mismatch.
        root = WatchedRoot(tier="custom", path="/srv/checkout")
        assert root.tier == "custom"
        assert root.path == "/srv/checkout"
        assert root.git_branch is None
        assert root.git_ref is None

    def test_workspace_status_defaults_to_no_roots(self) -> None:
        assert WorkspaceStatus().roots == []

    def test_index_status_summary_carries_the_workspace_section(self) -> None:
        summary = IndexStatusSummary(
            files_indexed=3,
            files_failed=0,
            files_skipped=0,
            tiers_rebuilt=[],
            tiers_skipped=[],
            outcomes=[],
            workspace=WorkspaceStatus(
                roots=[
                    WatchedRoot(
                        tier="custom",
                        path="/srv/checkout",
                        git_branch=_BRANCH_A,
                        git_ref="0" * 40,
                    )
                ]
            ),
        )
        assert [root.path for root in summary.workspace.roots] == ["/srv/checkout"]
        assert summary.workspace.roots[0].git_branch == _BRANCH_A
        # Still an IndexSummary subclass — the base fields read straight through.
        assert summary.files_indexed == 3

    def test_index_status_summary_validates_with_only_the_base_fields(self) -> None:
        # The F3 additive-schema pin (the class docstring's own prescription): adding
        # ``workspace`` must NOT force every existing construction site to change in
        # lockstep. A REQUIRED field here would fail this test.
        bare = IndexStatusSummary(
            files_indexed=0,
            files_failed=0,
            files_skipped=0,
            tiers_rebuilt=[],
            tiers_skipped=[],
            outcomes=[],
        )
        assert bare.workspace == WorkspaceStatus()
        assert bare.workspace.roots == []

    def test_the_new_sections_stay_strict_on_the_wire(self) -> None:
        # extra="forbid" everywhere else on this wire; a section that silently absorbs
        # unknown keys is how a typo'd field ships as an invisible no-op.
        with pytest.raises(ValidationError):
            WatchedRoot(tier="custom", path="/srv", bogus="x")  # type: ignore[call-arg]
        with pytest.raises(ValidationError):
            WorkspaceStatus(bogus="x")  # type: ignore[call-arg]


# --------------------------------------------------------------------------- #
# Every fate of the git read is FORCED by a fixture (the quantifier law)
# --------------------------------------------------------------------------- #
class TestBuildWorkspaceStatusFates:
    """``build_workspace_status`` over every reachable state of a live root.

    Each fate is a separate fixture: a named branch, a detached HEAD, a commit-less
    repo, a non-git directory, and a missing git binary. A build that is honest only on
    the happy path fails here; a build that CRASHES on any of the others fails here.
    """

    def test_a_live_root_on_a_named_branch_surfaces_branch_and_ref(
        self, tmp_path: Path
    ) -> None:
        repo = tmp_path / "checkout"
        sha = _make_git_repo(repo, branch=_BRANCH_A)
        config = _config(slug="s", roots=[_root("custom", repo)])

        status = build_workspace_status(config)

        assert status.roots == [
            WatchedRoot(
                tier="custom",
                path=str(repo.resolve()),
                git_branch=_BRANCH_A,
                git_ref=sha,
            )
        ]
        # The full, un-abbreviated sha (the seam's own contract) — never --short.
        assert status.roots[0].git_ref is not None
        assert len(status.roots[0].git_ref or "") == 40

    def test_a_detached_head_surfaces_the_ref_with_no_branch(self, tmp_path: Path) -> None:
        # HONEST, not a lie and not a crash: there IS no branch, so ``git_branch`` is
        # None — but the commit is known, so ``git_ref`` still names it. A build that
        # served git's own "HEAD" sentinel as a branch name would fail here.
        repo = tmp_path / "detached"
        sha = _make_git_repo(repo, branch=_BRANCH_A)
        _git(repo, "checkout", "--detach", "HEAD")
        config = _config(slug="s", roots=[_root("custom", repo)])

        status = build_workspace_status(config)

        assert status.roots == [
            WatchedRoot(tier="custom", path=str(repo.resolve()), git_branch=None, git_ref=sha)
        ]

    def test_a_git_repo_with_no_commits_is_honest_not_a_crash(self, tmp_path: Path) -> None:
        # ``git rev-parse HEAD`` FAILS in a freshly-init'ed repo (verified) — the seam
        # returns (None, None). The status read must survive it and still name the path.
        repo = tmp_path / "uncommitted"
        _make_git_repo(repo, branch=_BRANCH_A, commit=False)
        config = _config(slug="s", roots=[_root("custom", repo)])

        status = build_workspace_status(config)

        assert status.roots == [
            WatchedRoot(tier="custom", path=str(repo.resolve()), git_branch=None, git_ref=None)
        ]

    def test_a_live_root_that_does_not_EXIST_is_named_not_hidden(self, tmp_path: Path) -> None:
        # A REAL misconfiguration (a lore.yaml pointing at a path that is not there —
        # e.g. a container mount that never landed). This is precisely where an honesty
        # line earns its keep: the caller must SEE the watched path lore believes in,
        # even — especially — when nothing is there. A build that filters out
        # non-existent roots hides the very failure the caller is hunting.
        missing = tmp_path / "never-mounted"
        config = _config(slug="s", roots=[_root("custom", missing)])

        status = build_workspace_status(config)

        assert status.roots == [
            WatchedRoot(
                tier="custom", path=str(missing.resolve()), git_branch=None, git_ref=None
            )
        ]

    def test_a_non_git_live_root_still_surfaces_its_path(self, tmp_path: Path) -> None:
        plain = tmp_path / "not-a-repo"
        plain.mkdir()
        config = _config(slug="s", roots=[_root("vendor_live", plain)])

        status = build_workspace_status(config)

        assert status.roots == [
            WatchedRoot(
                tier="vendor_live", path=str(plain.resolve()), git_branch=None, git_ref=None
            )
        ]

    def test_a_missing_git_binary_is_honest_not_a_crash(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The real subprocess-failure fate, forced at the REAL seam (no fakes): with git
        # off PATH the launch raises OSError inside the seam, which swallows it and
        # returns (None, None). The status read must not propagate it.
        repo = tmp_path / "checkout"
        _make_git_repo(repo, branch=_BRANCH_A)
        empty_bin = tmp_path / "empty-bin"
        empty_bin.mkdir()
        monkeypatch.setenv("PATH", str(empty_bin))
        config = _config(slug="s", roots=[_root("custom", repo)])

        status = build_workspace_status(config)

        assert status.roots == [
            WatchedRoot(tier="custom", path=str(repo.resolve()), git_branch=None, git_ref=None)
        ]

    def test_every_live_root_carries_its_own_branch(self, tmp_path: Path) -> None:
        # The anti-monoculture, anti-single-root pin. TWO live roots on DIFFERENT
        # branches: a build that serves only effective_roots[0], or reads git ONCE and
        # reuses the answer, or returns a set/dict that loses order, goes RED here.
        first = tmp_path / "first"
        second = tmp_path / "second"
        sha_first = _make_git_repo(first, branch=_BRANCH_A)
        sha_second = _make_git_repo(second, branch=_BRANCH_B)
        config = _config(
            slug="s", roots=[_root("custom", first), _root("sidecar", second)]
        )

        status = build_workspace_status(config)

        assert status.roots == [
            WatchedRoot(
                tier="custom", path=str(first.resolve()), git_branch=_BRANCH_A, git_ref=sha_first
            ),
            WatchedRoot(
                tier="sidecar",
                path=str(second.resolve()),
                git_branch=_BRANCH_B,
                git_ref=sha_second,
            ),
        ]

    def test_static_roots_are_not_reported_as_watched(self, tmp_path: Path) -> None:
        # A static root is BATCH-indexed, never watched — a build that listed it would
        # be claiming to watch a frozen snapshot tier. Only the live root is watched.
        #
        # NOTE (adversary A4): this fixture declares NO ``path``, so on its own it
        # CANNOT discriminate ``watch != live`` (correct) from ``path is None`` (wrong).
        # ``test_a_static_root_that_DECLARES_a_path_is_still_not_watched`` below is the
        # pin that does. This one is kept because it kills a different wrong build (one
        # that crashes or invents a path when a static root has none).
        live = tmp_path / "live"
        sha = _make_git_repo(live, branch=_BRANCH_B)
        config = _config(
            slug="s",
            roots=[
                {
                    "tier": "vendored",
                    "watch": "static",
                    "source": "/opt/vendor",
                    "version": "15.0",
                    "provider": "local_dir",
                },
                _root("custom", live),
            ],
        )

        status = build_workspace_status(config)

        assert status.roots == [
            WatchedRoot(
                tier="custom", path=str(live.resolve()), git_branch=_BRANCH_B, git_ref=sha
            )
        ]

    def test_a_static_root_that_DECLARES_a_path_is_still_not_watched(
        self, tmp_path: Path
    ) -> None:
        # THE POLICY-vs-PROXY PIN (adversary A4 — a wrong build passed 24/24 without it).
        #
        # A static root MAY legally declare a ``path``: the config validator only ADDS
        # source/version/provider requirements for ``watch: static``; it never forbids a
        # path (verified — the payload below validates). And mypy actively pushes a
        # builder toward the WRONG filter, because ``root.path`` is ``str | None`` and
        # must be narrowed before ``Path(root.path)``:
        #
        #     if root.watch != WATCH_LIVE: continue    # correct — filters on the POLICY
        #     if root.path is None:        continue    # wrong   — filters on a PROXY
        #
        # Both pass every OTHER pin in this file. Only a static root that HAS a path
        # tells them apart. The wrong build serves a frozen, batch-indexed, never-watched
        # snapshot tier as a WATCHED root: a freshness lie, in the one section whose
        # entire job is not lying.
        vendored = tmp_path / "vendored-snapshot"
        _make_git_repo(vendored, branch="vendor/frozen")
        live = tmp_path / "live"
        sha = _make_git_repo(live, branch=_BRANCH_A)
        config = _config(
            slug="s",
            roots=[
                {
                    "tier": "vendored",
                    "watch": "static",
                    "source": "/opt/vendor",
                    "version": "15.0",
                    "provider": "local_dir",
                    # LEGAL — and the validator accepts it (that is the whole point).
                    "path": str(vendored),
                },
                _root("custom", live),
            ],
        )

        status = build_workspace_status(config)

        assert [root.tier for root in status.roots] == ["custom"], (
            "a STATIC root was served as a WATCHED root. The exclusion must key on the "
            "watch POLICY (watch != 'live'), never on the proxy 'it declares no path' — "
            "a static root may legally declare one, and then lore claims to watch a "
            "frozen, batch-indexed snapshot it never watches (finding #125: the honesty "
            "line telling its own kind of lie)"
        )
        assert status.roots == [
            WatchedRoot(
                tier="custom", path=str(live.resolve()), git_branch=_BRANCH_A, git_ref=sha
            )
        ]

    def test_an_all_static_config_serves_no_roots_and_does_not_crash(
        self, tmp_path: Path
    ) -> None:
        # Adversary RESIDUAL-1. A legal config with ZERO live roots (everything batch
        # indexed) must serve an EMPTY list — not crash. A build that reaches for
        # ``roots[0]`` after filtering (to serve "the" workspace as a scalar) dies here
        # rather than in a caller's status read.
        config = _config(
            slug="s",
            roots=[
                {
                    "tier": "vendored",
                    "watch": "static",
                    "source": "/opt/vendor",
                    "version": "15.0",
                    "provider": "local_dir",
                    "path": str(tmp_path / "frozen"),
                }
            ],
        )

        status = build_workspace_status(config)

        assert status.roots == []

    def test_two_live_roots_with_the_SAME_path_are_both_served(
        self, tmp_path: Path
    ) -> None:
        # Adversary RESIDUAL-2. A legal config: one tree, indexed under TWO tiers (e.g.
        # different include globs). A build that de-dupes by path — a "sensible" tidy-up —
        # silently drops a tier the caller configured, so the honesty line under-reports
        # what lore is watching. Order + multiplicity are the contract.
        shared = tmp_path / "one-tree"
        sha = _make_git_repo(shared, branch=_BRANCH_A)
        config = _config(
            slug="s", roots=[_root("custom", shared), _root("docs", shared)]
        )

        status = build_workspace_status(config)

        assert status.roots == [
            WatchedRoot(
                tier="custom", path=str(shared.resolve()), git_branch=_BRANCH_A, git_ref=sha
            ),
            WatchedRoot(
                tier="docs", path=str(shared.resolve()), git_branch=_BRANCH_A, git_ref=sha
            ),
        ], (
            "two live roots sharing a path must BOTH be served (a de-dup by path drops a "
            "configured tier from the honesty line)"
        )

    def test_a_relative_root_path_is_served_absolute(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # ``path: .`` is the documented single-tree style. Serving "." back to a caller
        # in ANOTHER tree is not an honesty line — it is noise. A build that passes the
        # configured string straight through fails here.
        repo = tmp_path / "relative-checkout"
        sha = _make_git_repo(repo, branch=_BRANCH_B)
        monkeypatch.chdir(repo)
        config = _config(slug="s", roots=[_root("custom", Path("."))])

        status = build_workspace_status(config)

        assert status.roots == [
            WatchedRoot(
                tier="custom", path=str(repo.resolve()), git_branch=_BRANCH_B, git_ref=sha
            )
        ]
        assert Path(status.roots[0].path).is_absolute()

    def test_a_single_tree_config_with_no_roots_surfaces_the_synthesised_root(
        self, tmp_path: Path
    ) -> None:
        # The other documented deploy style: no ``roots:`` at all, one live root
        # SYNTHESISED at project.root. A build keyed on ``config.roots`` (rather than
        # ``config.effective_roots``) serves an empty list here — silence where the
        # honesty line belongs.
        repo = tmp_path / "single-tree"
        sha = _make_git_repo(repo, branch=_BRANCH_A)
        config = _config(slug="s", roots=[], project_root=str(repo))

        status = build_workspace_status(config)

        assert len(status.roots) == 1
        assert status.roots[0].path == str(repo.resolve())
        assert status.roots[0].git_branch == _BRANCH_A
        assert status.roots[0].git_ref == sha


# --------------------------------------------------------------------------- #
# FRESH ON EVERY READ — a cached honesty line is a CONFIDENTLY WRONG one
# --------------------------------------------------------------------------- #
class TestFreshOnEveryRead:
    """The section describes the watched tree **NOW**, not at boot (adversary A1).

    The server process is long-lived — the heavy startup runs ONCE per process and the
    container runs for days — and the watched root is a LIVE bind mount. A branch switch
    in that tree is not an edge case: **it is the entire scenario #125 exists for.** A
    build that computes the section once and caches it per-process passed all 24 of the
    original pins (no fixture read the status TWICE), and then lies after the first
    checkout — a confidently wrong answer to the one question the section answers, which
    is strictly worse than no answer at all.

    Two pins, at two altitudes, because a cache can live at either:
    the pure builder (below) and the SERVED status read (:class:`TestServedEndToEnd`).
    """

    def test_the_branch_is_re_read_on_every_call(self, tmp_path: Path) -> None:
        repo = tmp_path / "checkout"
        first_sha = _make_git_repo(repo, branch=_BRANCH_A)
        config = _config(slug="s", roots=[_root("custom", repo)])

        # The boot-time read (the long-lived server's first status call).
        first = build_workspace_status(config)
        assert first.roots[0].git_branch == _BRANCH_A
        assert first.roots[0].git_ref == first_sha

        # The watched tree MOVES — a checkout in the live bind mount.
        _git(repo, "checkout", "-b", _BRANCH_B)
        (repo / "module.py").write_text("VALUE = 2\n", encoding="utf-8")
        _git(repo, "add", "module.py")
        _git(repo, "commit", "-m", "second")
        second_sha = _git(repo, "rev-parse", "HEAD")
        assert second_sha != first_sha

        # The next status read must describe the tree as it is NOW.
        second = build_workspace_status(config)

        assert second.roots[0].git_branch == _BRANCH_B, (
            "the honesty line went STALE: it is still serving the branch the tree was on "
            "at the FIRST status read. The section must be re-derived on every call — a "
            "cached branch is a confidently WRONG answer to the only question this "
            "section exists to answer (finding #125)"
        )
        assert second.roots[0].git_ref == second_sha


# --------------------------------------------------------------------------- #
# ONE IMPLEMENTATION — the git read routes through the EXISTING shared seam
# --------------------------------------------------------------------------- #
class TestSharesTheGitSeam:
    """Repo standing law: if two call sites need the same POLICY it is a FUNCTION THEY
    CALL, never a pattern they clone. ``capture_git_identity`` already exists (and
    already handles non-git / detached / subprocess-failure); a second git reader in
    ``server.py`` is a defect, not an implementation.

    Proved BY MUTATION (the only test that distinguishes DRY from looks-DRY): patch the
    seam, and every served value must follow it. A build with its own ``subprocess.run``
    keeps returning the REAL branch and goes RED.
    """

    def test_the_server_reuses_the_snapshots_seam_object(self) -> None:
        # Read through the module __dict__, not attribute access: mypy's
        # no_implicit_reexport makes ``server.capture_git_identity`` a type error to
        # touch from outside, and the name's PRESENCE in server's namespace is exactly
        # what this pin is about (a module-level import of the shared seam — which is
        # also what makes the mutation pin below patchable).
        seam = server_module.__dict__.get("capture_git_identity")
        assert seam is not None, (
            "server.py must import the shared capture_git_identity from "
            "loremaster.index.snapshots at module level"
        )
        assert seam is snapshots_module.capture_git_identity, (
            "server.py must reuse the SHARED capture_git_identity object — not define, "
            "wrap, or copy its own git reader (ONE IMPLEMENTATION)"
        )

    def test_the_served_identity_follows_the_seam(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # THE MUTATION PIN. Two live roots, each answered a DISTINCT sentinel by the
        # patched seam. A hand-rolled git call inside server.py ignores the patch and
        # serves the real branches (_BRANCH_A / _BRANCH_B) — RED, by name, right here.
        first = tmp_path / "first"
        second = tmp_path / "second"
        _make_git_repo(first, branch=_BRANCH_A)
        _make_git_repo(second, branch=_BRANCH_B)
        answers = {
            str(first.resolve()): ("a" * 40, "sentinel/first"),
            str(second.resolve()): ("b" * 40, "sentinel/second"),
        }
        calls: list[Path] = []
        monkeypatch.setattr(
            server_module, "capture_git_identity", _identity_spy(answers, calls)
        )
        config = _config(
            slug="s", roots=[_root("custom", first), _root("sidecar", second)]
        )

        status = build_workspace_status(config)

        assert [(root.git_branch, root.git_ref) for root in status.roots] == [
            ("sentinel/first", "a" * 40),
            ("sentinel/second", "b" * 40),
        ]
        assert len(calls) == 2, "the shared seam must be called once per live root"

    @pytest.mark.parametrize(
        ("seam_answer", "expected_ref", "expected_branch"),
        [
            pytest.param((None, None), None, None, id="seam_says_it_does_not_know"),
            pytest.param(("a" * 40, None), "a" * 40, None, id="seam_says_detached"),
            pytest.param(
                ("b" * 40, "sentinel/from-the-seam"),
                "b" * 40,
                "sentinel/from-the-seam",
                id="seam_says_a_branch",
            ),
        ],
    )
    def test_the_seam_is_the_SOLE_authority_for_the_git_identity(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        seam_answer: tuple[str | None, str | None],
        expected_ref: str | None,
        expected_branch: str | None,
    ) -> None:
        """ROUTING IS NOT SHARING — the pin that kills the *fallback* build DELIBERATELY.

        The adversary built the build a well-informed builder actually writes once they
        learn git was missing from the image: it CALLS ``capture_git_identity`` — so the
        import pin, the AST pin, the spy pin and the tree-read pin all stay GREEN — and
        then hand-rolls the DECISION underneath it, falling back to a private
        ``.git/HEAD`` reader whenever the seam answers ``(None, None)``. It passed 22 of
        the original 24 pins; only two degradation FATES caught it, incidentally.

        That is a private git reader wearing the shared name (repo law, finding #102),
        and it is a real defect, not a style quibble: the seam owns the POLICY — the
        5-second timeout, the OSError swallowing, the detached-HEAD rule, "no commits
        yet" — and a second reader beneath it silently re-decides all of them, on its
        own terms, for exactly the inputs the seam declared unknowable.

        The pin: whatever the SEAM says, verbatim, is what gets SERVED — over the seam's
        whole output range, including the one answer a fallback exists to override. The
        fixture is a REAL git repo on a REAL branch with a perfectly readable
        ``.git/HEAD``: any private reader WILL find ``spike/honesty-line`` there and
        serve it, and that is precisely the RED.
        """
        repo = tmp_path / "checkout"
        _make_git_repo(repo, branch=_BRANCH_A)
        # Belt and braces: the private reader's own input is READABLE and TRUE, so a
        # fallback build cannot fail this pin for an incidental reason (a missing file).
        # It fails it for the one reason that matters: it did not obey the seam.
        head_file = repo / ".git" / "HEAD"
        assert head_file.is_file()
        assert _BRANCH_A in head_file.read_text(encoding="utf-8")

        calls: list[Path] = []
        monkeypatch.setattr(
            server_module,
            "capture_git_identity",
            _identity_spy({str(repo.resolve()): seam_answer}, calls),
        )
        config = _config(slug="s", roots=[_root("custom", repo)])

        status = build_workspace_status(config)

        assert status.roots == [
            WatchedRoot(
                tier="custom",
                path=str(repo.resolve()),
                git_branch=expected_branch,
                git_ref=expected_ref,
            )
        ], (
            "the served git identity did not follow the SHARED seam. server.py must "
            "serve exactly what capture_git_identity returns — it may not second-guess "
            "it, fill in a gap from a private .git/HEAD reader, or derive a branch from "
            "the ref. A build that routes through the seam and then hand-rolls the "
            "DECISION underneath it is a private copy wearing the shared name "
            "(ROUTING IS NOT SHARING — repo standing law, finding #102)"
        )
        assert len(calls) == 1, "the shared seam must be consulted once per live root"

    def test_git_is_read_from_the_tree_that_is_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Reporting path X while reading git from Y is the very lie #125 is about. The
        # tree handed to the seam must resolve to the tree named in the served row.
        repo = tmp_path / "checkout"
        _make_git_repo(repo, branch=_BRANCH_A)
        calls: list[Path] = []
        monkeypatch.setattr(
            server_module,
            "capture_git_identity",
            _identity_spy({str(repo.resolve()): ("c" * 40, "sentinel/only")}, calls),
        )
        config = _config(slug="s", roots=[_root("custom", repo)])

        status = build_workspace_status(config)

        assert [str(path) for path in calls] == [root.path for root in status.roots]
        assert status.roots[0].git_branch == "sentinel/only"

    def test_the_server_module_never_shells_out_to_git(self) -> None:
        # Defence in depth behind the mutation pin: ``server.py`` carries NO subprocess
        # dependency today (verified) and must not grow one to re-read git. The seam owns
        # the invocation — including its timeout and its OSError swallowing.
        source = Path(server_module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported += [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module.split(".")[0])
        assert "subprocess" not in imported, (
            "server.py must not import subprocess — the git read belongs to "
            "loremaster.index.snapshots.capture_git_identity (ONE IMPLEMENTATION)"
        )
        rev_parse_literals = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and "rev-parse" in node.value
        ]
        assert rev_parse_literals == [], (
            f"server.py hand-rolls a git invocation: {rev_parse_literals!r}"
        )


# --------------------------------------------------------------------------- #
# Hostile values — a path and a branch are ENVIRONMENT input, not lore's own
# --------------------------------------------------------------------------- #
class TestHostileValues:
    """A watched path and a branch name come from OUTSIDE lore. A directory name can
    carry a newline, a backtick run, and a line shaped exactly like one of lore's own
    output rows (verified creatable, and ``git init`` works inside it).

    The ruling this class pins (reasoning in REPORT-pkt01-contract-1.md): the value is
    served VERBATIM — never sanitised at construction. Sanitising it here would be its
    own lie (an honesty line that prints a branch/path that does not exist is worse than
    useless), and the wire is JSON, where the encoder escapes control characters, so the
    hostile value CANNOT forge a row or a fence. The tests below prove both halves:
    exactness, and non-forgeability. The guard for any FUTURE text render is the type
    system — ``render_line`` accepts only ``SafeLine`` (test_render_mypy_layer.py row 1
    pins a raw ``str`` as an ``[arg-type]`` error), so a rendered surface is forced
    through ``safe_str``/``sanitise_line``, whose neutralisation is pinned below.
    """

    def test_a_hostile_root_path_is_served_verbatim(self, tmp_path: Path) -> None:
        hostile_dir = tmp_path / _HOSTILE_DIR_NAME
        sha = _make_git_repo(hostile_dir, branch=_BRANCH_B)
        config = _config(slug="s", roots=[_root("custom", hostile_dir)])

        status = build_workspace_status(config)

        assert status.roots == [
            WatchedRoot(
                tier="custom",
                path=str(hostile_dir.resolve()),
                git_branch=_BRANCH_B,
                git_ref=sha,
            )
        ]
        # Exactness is the point: a mangled path would name a tree that does not exist.
        assert "\n" in status.roots[0].path

    def test_a_hostile_value_cannot_forge_structure_on_the_wire(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Both hostile surfaces at once: a forged PATH (real dir) and a forged BRANCH
        # (through the patched seam — real git refuses control chars in a ref name).
        hostile_dir = tmp_path / _HOSTILE_DIR_NAME
        _make_git_repo(hostile_dir, branch=_BRANCH_B)
        monkeypatch.setattr(
            server_module,
            "capture_git_identity",
            _identity_spy({str(hostile_dir.resolve()): ("d" * 40, _HOSTILE_BRANCH)}, []),
        )
        config = _config(slug="s", roots=[_root("custom", hostile_dir)])

        summary = IndexStatusSummary(
            files_indexed=0,
            files_failed=0,
            files_skipped=0,
            tiers_rebuilt=[],
            tiers_skipped=[],
            outcomes=[],
            workspace=build_workspace_status(config),
        )
        payload = summary.model_dump_json()

        # 1. Verbatim: the honest value survives the round trip byte for byte.
        restored = IndexStatusSummary.model_validate_json(payload)
        assert restored.workspace.roots[0].git_branch == _HOSTILE_BRANCH
        assert restored.workspace.roots[0].path == str(hostile_dir.resolve())
        # 2. Non-forgeable: the JSON encoder escaped every control character, so the
        # served text is ONE line — the forged row cannot become a row, and the backtick
        # run cannot open a fence.
        assert "\n" not in payload
        assert "\r" not in payload

    def test_the_render_seam_neutralises_a_hostile_value_if_it_is_ever_rendered(
        self,
    ) -> None:
        # The forward guard for the ruling above: the day someone renders this section
        # into a line-oriented surface, the value goes through the shared sanitiser (the
        # only way past ``render_line``'s SafeLine-typed parameters), and THAT is where
        # the newline dies. Pinned here so the ruling is a mechanism, not a memo.
        safe = safe_str(_HOSTILE_BRANCH)
        assert isinstance(safe, SafeLine)
        assert "\n" not in safe
        assert "\r" not in safe


# --------------------------------------------------------------------------- #
# The served prose — a caller must be TOLD the honesty line exists
# --------------------------------------------------------------------------- #
class TestLoreIndexDescription:
    """This repo's audited defect history: green-at-gate defects cluster in served
    natural-language surfaces. ``lore_index``'s description ENUMERATES what it returns
    ("files indexed … trace-call aggregates"); shipping the section while that sentence
    still omits it means no agent ever knows to look — the finding stays open in
    practice while the code says it is closed.
    """

    async def test_the_description_names_the_watched_root_and_the_branch(
        self, tmp_path: Path
    ) -> None:
        config = _config(slug=_slug(), roots=[_root("custom", tmp_path / "live")])
        mcp = build_mcp_server(LoreServer(config))
        tools = {tool.name: tool for tool in await mcp.list_tools()}

        description = (tools["lore_index"].description or "").lower()

        assert "branch" in description, (
            "lore_index's description must tell a caller the status read names the git "
            "BRANCH of the tree it indexes (finding #125 — the honesty line)"
        )
        assert "watched" in description or "root" in description, (
            "lore_index's description must tell a caller the status read names the "
            "WATCHED PATH it indexes"
        )


# --------------------------------------------------------------------------- #
# END TO END — lore_index() actually SERVES it (a helper nothing calls is #94)
# --------------------------------------------------------------------------- #
class TestServedEndToEnd:
    """The pin that a model + a builder function cannot satisfy on their own.

    Finding #94's archetype: every pin tested a new method that NOTHING required the
    code to CALL, so the contract went green with the defect fully intact. This drives
    the REAL path — ``build_app_context`` → ``AppContext.index()`` →
    ``_build_index_status`` — against a live SurrealDB (spike-surreal, :18000) and a
    live root that is a REAL git repo on a foreign branch.
    """

    async def test_lore_index_serves_the_watched_root_and_branch(
        self, tmp_path: Path
    ) -> None:
        repo = tmp_path / "indexed-tree"
        sha = _make_git_repo(repo, branch=_BRANCH_B)
        config = _config(slug=_slug(), roots=[_root("custom", repo)])
        ctx = await build_app_context(
            server=LoreServer(config),
            embedder=FakeEmbedder(dim=_DIM),
            manifest_path=tmp_path / "m.db",
            snapshot_root=tmp_path / "snap",
            start_tasks=False,
        )
        try:
            summary = await ctx.index()
        finally:
            await ctx.aclose()

        assert summary.workspace.roots == [
            WatchedRoot(
                tier="custom",
                path=str(repo.resolve()),
                git_branch=_BRANCH_B,
                git_ref=sha,
            )
        ], (
            "lore_index() must SERVE the watched path + branch it is actually indexing "
            "(finding #125): a caller in a sibling worktree sees the mismatch here or "
            "nowhere"
        )

    async def test_the_served_status_re_reads_the_branch_on_every_call(
        self, tmp_path: Path
    ) -> None:
        # THE OTHER ALTITUDE (adversary A1). ``TestFreshOnEveryRead`` proves the pure
        # BUILDER re-reads; it cannot see a cache one level up — a build that computes
        # the section once in ``build_app_context`` / on first ``_build_index_status``
        # and stores it on the context passes that pin and still serves a boot-time
        # branch forever. This drives the REAL served path twice, across a real checkout
        # in the watched tree: the second status read must name the NEW branch.
        #
        # ``index(reconcile=False)`` is the pure status read the caller actually makes
        # (a "cheap health read" — it never sweeps), so this is exactly the sequence a
        # long-lived server sees when an agent checks the tree after switching branches.
        repo = tmp_path / "moving-tree"
        first_sha = _make_git_repo(repo, branch=_BRANCH_A)
        config = _config(slug=_slug(), roots=[_root("custom", repo)])
        ctx = await build_app_context(
            server=LoreServer(config),
            embedder=FakeEmbedder(dim=_DIM),
            manifest_path=tmp_path / "m.db",
            snapshot_root=tmp_path / "snap",
            start_tasks=False,
        )
        try:
            first = await ctx.index()
            assert first.workspace.roots[0].git_branch == _BRANCH_A
            assert first.workspace.roots[0].git_ref == first_sha

            _git(repo, "checkout", "-b", _BRANCH_B)
            (repo / "module.py").write_text("VALUE = 2\n", encoding="utf-8")
            _git(repo, "add", "module.py")
            _git(repo, "commit", "-m", "second")
            second_sha = _git(repo, "rev-parse", "HEAD")

            second = await ctx.index()
        finally:
            await ctx.aclose()

        assert second.workspace.roots == [
            WatchedRoot(
                tier="custom",
                path=str(repo.resolve()),
                git_branch=_BRANCH_B,
                git_ref=second_sha,
            )
        ], (
            "the SERVED honesty line went stale: lore_index() is still reporting the "
            "branch the watched tree was on at the first status read. The server process "
            "is long-lived and the tree is a live bind mount — a cached section serves a "
            "confidently WRONG branch forever after the first checkout (finding #125)"
        )


# --------------------------------------------------------------------------- #
# FIX WAVE / F5 — R2: a BLOCKING subprocess inside the async event loop
# --------------------------------------------------------------------------- #
class TestTheGitReadDoesNotBlockTheEventLoop:
    """``build_workspace_status`` runs ``subprocess.run`` — TWO git calls, each with a 10s
    timeout, PER LIVE ROOT — and ``_build_index_status`` calls it straight from the
    coroutine. Today that costs ~5-10ms and nobody notices.

    The exposure is not the average, it is the TAIL. A wedged git (an ``index.lock`` left by
    a crashed process, an NFS stall, a filesystem hang) blocks the ONE event loop for up to
    20 SECONDS PER ROOT — and an event loop is not per-caller. Every MCP session on that
    server — every search, every read, every heartbeat, from every agent — stops dead, for a
    status read that one agent asked for. The section that exists to keep the server honest
    would take the server down with it.

    The fix is one line (``await asyncio.to_thread(build_workspace_status, self._config)``).
    The pin is the part worth thinking about: it must DISCRIMINATE. A pin that measures how
    long ``index()`` took, or that simply asserts it returned, passes cheerfully on the
    blocking build — decoration. So this measures the ONE thing that differs: whether the
    LOOP kept running while the git read was in flight.

    Instrument: a heartbeat coroutine ticking every ``_TICK_S`` records the gap between its
    own wakeups. A gap is how long the loop was unavailable. If the git read blocks the loop,
    exactly one gap swells to the read's whole duration.
    """

    # The (patched) git seam blocks this long per live root — standing in for a wedged git.
    _BLOCK_S = 0.75
    # The heartbeat's period: the resolution at which loop unavailability is visible.
    _TICK_S = 0.01
    # The largest stall a HEALTHY loop may show. Sits 2.5× below one root's block, so the
    # verdict is never a photo-finish (this suite runs under `-n auto` on a busy box).
    _MAX_STALL_S = 0.30

    async def _watch_the_loop(self, gaps: list[float]) -> None:
        """Tick forever; record how late each wakeup was. A big gap == a blocked loop."""
        previous = time.monotonic()
        while True:
            await asyncio.sleep(self._TICK_S)
            now = time.monotonic()
            gaps.append(now - previous)
            previous = now

    @asynccontextmanager
    async def _loop_stall_watch(self) -> AsyncIterator[list[float]]:
        """Measure loop unavailability across the block. ONE instrument, both legs.

        The DRAIN in the ``finally`` is load-bearing and was found by this pin's own
        control: a stall is only RECORDED when the heartbeat next resumes, and the last
        statement of ``_build_index_status`` is the git read — so cancelling the watcher the
        instant ``index()`` returns throws away the very gap being measured. The first draft
        did exactly that and passed on the BLOCKING build: a probe that could not see the
        thing it existed to see. Both legs now share this context manager precisely so they
        cannot diverge again (the control must exercise the identical instrument, or it is
        not a control).
        """
        gaps: list[float] = []
        watcher = asyncio.create_task(self._watch_the_loop(gaps))
        await asyncio.sleep(self._TICK_S * 2)  # let the heartbeat settle before measuring
        try:
            yield gaps
        finally:
            await asyncio.sleep(self._TICK_S * 3)  # DRAIN: let it resume and RECORD the gap
            watcher.cancel()

    async def test_the_instrument_can_SEE_a_blocked_loop(self) -> None:
        # A PROBE NEEDS A CONTROL — and the auditor's instrument can lie the same way the
        # author's did. Before trusting "the loop was never stalled", prove this harness can
        # actually SEE a stall: block the loop deliberately, for the same duration, through
        # the same context manager, and watch the gap appear. Without this leg, a heartbeat
        # that never got to record anything would report "no stalls" and pass the pin below
        # on ANY build — which is exactly what the first draft of this pin did.
        async with self._loop_stall_watch() as gaps:
            time.sleep(self._BLOCK_S)  # a blocking call, made from inside the loop

        assert gaps, "the heartbeat never ran — the instrument measures nothing"
        assert max(gaps) >= self._BLOCK_S * 0.8, (
            f"the harness could not see a {self._BLOCK_S}s block of its own making "
            f"(largest gap: {max(gaps):.3f}s). The pin below would then pass on a build "
            f"that stalls the whole server, which is the probe passing for the wrong reason"
        )
        assert max(gaps) > self._MAX_STALL_S, (
            "the control's stall must exceed the threshold the real pin uses, or the two "
            "legs are not measuring the same thing"
        )

    async def test_a_slow_git_does_not_stall_the_whole_server(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # THE PIN. Two live roots, and a git seam that BLOCKS — a wedged git, exactly the
        # tail this defends. The status read must still complete, must still serve what the
        # seam returned (a build that "fixes" the stall by not reading git is not a fix), and
        # the loop must have stayed alive throughout.
        first = tmp_path / "first"
        second = tmp_path / "second"
        _make_git_repo(first, branch=_BRANCH_A)
        _make_git_repo(second, branch=_BRANCH_B)
        calls: list[Path] = []

        def _wedged_git(repo_root: Path) -> tuple[str | None, str | None]:
            calls.append(Path(repo_root))
            time.sleep(self._BLOCK_S)
            return ("c" * 40, "sentinel/from-a-wedged-git")

        monkeypatch.setattr(server_module, "capture_git_identity", _wedged_git)
        config = _config(
            slug=_slug(), roots=[_root("custom", first), _root("sidecar", second)]
        )
        ctx = await build_app_context(
            server=LoreServer(config),
            embedder=FakeEmbedder(dim=_DIM),
            manifest_path=tmp_path / "m.db",
            snapshot_root=tmp_path / "snap",
            start_tasks=False,
        )

        try:
            async with self._loop_stall_watch() as gaps:
                summary = await ctx.index()
        finally:
            await ctx.aclose()

        # The git read really happened — this is not a stall dodged by dropping the feature.
        assert len(calls) == 2, f"the seam must be read once per live root (got {calls})"
        assert [root.git_branch for root in summary.workspace.roots] == [
            "sentinel/from-a-wedged-git",
            "sentinel/from-a-wedged-git",
        ]

        assert gaps, "the heartbeat never ran — the measurement is empty"
        assert max(gaps) < self._MAX_STALL_S, (
            f"the event loop was UNAVAILABLE for {max(gaps):.2f}s while the status read did "
            f"its git work. That is not the caller's latency — it is the whole server's: "
            f"every other MCP session on this process (searches, reads, heartbeats, every "
            f"other agent) was frozen for the duration, and a genuinely wedged git holds it "
            f"for up to 20s PER ROOT. The git read is blocking I/O and must not run in the "
            f"coroutine — hand it to a thread (asyncio.to_thread) so the loop stays alive "
            f"(audit residual R2)"
        )
