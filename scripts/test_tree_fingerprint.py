"""Contract for ``scripts/tree_fingerprint.sh`` (finding #192).

The helper's whole value is that an EMPTY diff across a gate run means the tree
did not move. Two properties have to hold for that to be worth anything, and both
get a POSITIVE CONTROL — a fingerprint that cannot detect a change is decoration,
and one that reports a change for everything is noise nobody reads.

⚠ **EVERY MUTATING TEST RUNS IN A THROWAWAY GIT REPO, NEVER IN THIS CHECKOUT, AND
THAT IS NOT TIDINESS — IT IS THE FINDING APPLYING TO ITSELF.** The obvious way to
prove "a tracked-file edit moves the tree hash" is to edit a tracked file here and
hash before/after. That test would spoil every concurrent fingerprint in the tree,
including the ones it exists to certify: an agent running gates while it executes
would see the tree hash change with HEAD unchanged — precisely the ONE combination
the helper documents as "an uncommitted edit to code under test, mid-run", i.e.
the spoiling shape. The instrument would manufacture its own failure mode,
intermittently and only under concurrency, which is the hardest kind of flake to
attribute. Same lesson as ``scratch_copy.sh``: an instrument that mutates the tree
it is measuring is not isolated, and NOTHING tells you.

:func:`test_the_helper_is_READ_ONLY_against_the_real_repo` closes the other half —
running the helper here must not perturb what it reports. A fingerprint tool that
perturbs the fingerprint should be impossible rather than merely unlikely.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

_HELPER = Path(__file__).resolve().parent / "tree_fingerprint.sh"


def _run(*args: str, cwd: Path) -> str:
    """Run the helper in ``cwd`` and return its stdout."""
    result = subprocess.run(
        [str(_HELPER), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _field(output: str, key: str) -> str:
    for line in output.splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1]
    raise AssertionError(f"{key} missing from fingerprint output:\n{output}")


@pytest.fixture()
def throwaway_repo(tmp_path: Path) -> Path:
    """A real git repo with one tracked file — never this checkout."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=tmp_path, check=True)
    (tmp_path / "tracked.txt").write_text("original\n")
    subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=tmp_path, check=True)
    return tmp_path


class TestTheFingerprintDetectsWhatItClaimsTo:
    """Both directions, in a throwaway repo — the detector must fire, and it must
    distinguish the benign case from the spoiling one."""

    def test_a_TRACKED_file_edit_MOVES_the_tree_hash(self, throwaway_repo: Path) -> None:
        """The spoiling shape: an uncommitted edit to a tracked file. HEAD does
        NOT move, so the tree hash is the only thing that can catch it — which is
        exactly why the detector is the whole tracked set and not a name list."""
        before = _run(cwd=throwaway_repo)
        (throwaway_repo / "tracked.txt").write_text("edited\n")
        after = _run(cwd=throwaway_repo)
        assert _field(before, "TRACKED_TREE_MD5") != _field(after, "TRACKED_TREE_MD5"), (
            "an uncommitted edit to a TRACKED file did not move the tree hash — the detector "
            "cannot see the one shape that actually spoils a gate receipt"
        )
        assert _field(before, "HEAD") == _field(after, "HEAD"), (
            "fixture check: HEAD must NOT move here, or this is not the shape under test"
        )

    def test_an_UNTRACKED_file_moves_the_status_count_and_NOT_the_tree_hash(
        self, throwaway_repo: Path
    ) -> None:
        """The BENIGN sibling-report case, and it must be DISTINGUISHABLE from the
        one above — a detector that fired on both would make every audit artifact
        look like a spoiled run, and an instrument that cries wolf gets ignored."""
        before = _run(cwd=throwaway_repo)
        (throwaway_repo / "REPORT-sibling.md").write_text("an audit landing mid-run\n")
        after = _run(cwd=throwaway_repo)
        assert int(_field(after, "STATUS_LINES")) > int(_field(before, "STATUS_LINES")), (
            "an untracked file did not move the status count — then nothing sees it at all, "
            "since `git ls-files` covers tracked files only"
        )
        assert _field(before, "TRACKED_TREE_MD5") == _field(after, "TRACKED_TREE_MD5"), (
            "an untracked file moved the TRACKED tree hash — the benign case is now "
            "indistinguishable from an edit to code under test"
        )

    def test_a_COMMIT_moves_HEAD(self, throwaway_repo: Path) -> None:
        """The third shape: a sibling commits mid-run. Without HEAD, a commit whose
        content happens to leave the working tree identical is invisible."""
        before = _run(cwd=throwaway_repo)
        (throwaway_repo / "tracked.txt").write_text("committed change\n")
        subprocess.run(["git", "commit", "-qam", "sibling"], cwd=throwaway_repo, check=True)
        after = _run(cwd=throwaway_repo)
        assert _field(before, "HEAD") != _field(after, "HEAD")

    def test_an_UNCHANGED_repo_fingerprints_IDENTICALLY(self, throwaway_repo: Path) -> None:
        """The control that makes every leg above evidence of DISCRIMINATION
        rather than of an output that simply varies — a fingerprint containing a
        timestamp would 'detect' every run."""
        assert _run(cwd=throwaway_repo) == _run(cwd=throwaway_repo)


class TestTheDiagnosisHalfNamesFilesWithoutBeingTheDetector:
    def test_named_paths_are_hashed_and_reported(self, throwaway_repo: Path) -> None:
        output = _run("tracked.txt", cwd=throwaway_repo)
        assert "tracked.txt" in output
        assert any(len(part) == 32 for part in output.split()), (
            "no md5 appears for the named path — the diagnosis half emits nothing"
        )

    def test_a_MISSING_named_path_is_reported_not_fatal(self, throwaway_repo: Path) -> None:
        """A named file that does not exist must be SAID, not crash the capture:
        the fingerprint is usually taken around a run whose failure is the thing
        being diagnosed, and an instrument that dies there is useless exactly when
        it is needed."""
        output = _run("no-such-file.txt", cwd=throwaway_repo)
        assert "MISSING" in output and "no-such-file.txt" in output

    def test_the_tree_hash_IGNORES_which_paths_were_named(self, throwaway_repo: Path) -> None:
        """The detector must not depend on the caller's list — that is the whole
        'detect on the closed set, diagnose with the list' split."""
        bare = _field(_run(cwd=throwaway_repo), "TRACKED_TREE_MD5")
        named = _field(_run("tracked.txt", cwd=throwaway_repo), "TRACKED_TREE_MD5")
        assert bare == named


class TestTheHelperIsReadOnly:
    def test_the_helper_is_READ_ONLY_against_the_real_repo(self) -> None:
        """⚠ Run against THIS checkout on purpose — it is the one test here that
        may, because it asserts the helper changes nothing. Every caller depends
        on that: a fingerprint tool that perturbs the fingerprint would corrupt
        the receipts it exists to produce, and would do so invisibly."""
        repo_root = Path(__file__).resolve().parents[1]
        before = _run(cwd=repo_root)
        after = _run(cwd=repo_root)
        assert before == after, (
            "the helper's own invocation changed what it reports — it is not read-only, and "
            "every receipt taken with it is suspect"
        )

    def test_help_states_the_BOUNDS(self) -> None:
        """The bounds are load-bearing, so they must be readable from the tool
        rather than remembered: tracked-only, untracked lands in the status count,
        a mid-run commit moves HEAD. An instrument that hides its own bound is how
        'unproven' silently becomes 'proven'."""
        repo_root = Path(__file__).resolve().parents[1]
        text = _run("--help", cwd=repo_root)
        for expected in ("TRACKED files only", "STATUS_LINES", "HEAD", "NONE alone is sufficient"):
            assert expected in text, f"--help does not state the bound {expected!r}:\n{text}"
