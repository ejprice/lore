"""Tests for the finding-#140 scratch-copy guard.

Covers ``scripts/scratch_copy.sh`` (the front door) and ``scripts/scratch_provenance.py``
(the decision rule it enforces).

The tool exists because a ``cp -a`` copy of this repo never runs its own production code:
the copied ``.venv``'s editable ``.pth`` files name ABSOLUTE ORIGINAL paths, so
``import loremaster`` inside the copy resolves to the original checkout.  Its ONE
load-bearing promise is therefore that it **fails loud** rather than hand back a poisoned
copy — a tool that laundered the defect it exists to prevent would be worse than no tool.

So the pins prove BOTH legs, not just the happy one:

* :func:`test_poisoned_copy_is_refused_loudly` — a tree wearing a ``.venv`` whose ``.pth``
  files name the original is REFUSED, non-zero, naming the original path.  The fixture is
  discriminating: the poisoned copy has its OWN ``loremaster`` source tree, so a guard that
  merely checked "does the copy contain a loremaster directory?" would wave it through.
* :func:`test_honest_copy_is_built_and_accepted` — the POSITIVE CONTROL: a genuinely-good
  copy is ACCEPTED (exit 0), which is what makes the refusal above evidence of
  discrimination rather than of a guard that always says no.

The pure-decision tests carry the boundary cases (namespace package, unimportable member)
without a 108M virtualenv in the loop; one end-to-end test builds a real copy.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# The tool lives in ``scripts/`` (not a package) — make it importable.  Mirrors
# ``scripts/test_snapshot_gc.py``.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest  # noqa: E402
from scratch_provenance import (  # type: ignore[import-not-found]  # noqa: E402  (scripts/ is not a package)
    MemberProvenance,
    ProvenanceGuard,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRATCH_COPY_TOOL = REPO_ROOT / "scripts" / "scratch_copy.sh"


def _run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    """Invoke the tool exactly as an agent would, and hand back both streams."""
    return subprocess.run(
        [str(SCRATCH_COPY_TOOL), *args],
        capture_output=True,
        text=True,
        check=False,
        # The poisoned-copy pin runs a python whose site-packages is the REAL venv (see
        # ``_poisoned_copy``).  Nothing here should ever write bytecode into it.
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


# ---------------------------------------------------------------------------
# The decision rule (no virtualenv in the loop)
# ---------------------------------------------------------------------------


def test_member_resolving_inside_the_scratch_tree_is_accepted(tmp_path: Path) -> None:
    """POSITIVE CONTROL for the rule: an honest provenance is not flagged."""
    guard = ProvenanceGuard(tmp_path)
    member = MemberProvenance(
        name="loremaster",
        module_file=str(tmp_path / "loremaster" / "loremaster" / "__init__.py"),
    )

    assert guard.verdict(member) is None


def test_member_resolving_to_the_original_checkout_is_rejected(tmp_path: Path) -> None:
    """The #140 defect itself: the copy's import lands in the ORIGINAL tree."""
    guard = ProvenanceGuard(tmp_path)
    member = MemberProvenance(
        name="loremaster",
        module_file=str(REPO_ROOT / "loremaster" / "loremaster" / "__init__.py"),
    )

    reason = guard.verdict(member)

    assert reason is not None
    assert "OUTSIDE the scratch tree" in reason
    assert str(REPO_ROOT) in reason


def test_namespace_package_import_is_rejected(tmp_path: Path) -> None:
    """``__file__ is None`` is a FAILURE, not a neutral value.

    Measured on this repo: a plain ``uv sync`` in a copy installs no workspace member, and
    ``import loremaster`` then succeeds *silently* as an implicit namespace package with
    ``__file__ is None`` — loading none of the production code.  A guard that only compared
    paths would crash or, worse, skip the member.
    """
    guard = ProvenanceGuard(tmp_path)

    reason = guard.verdict(MemberProvenance(name="loremaster", module_file=None))

    assert reason is not None
    assert "NAMESPACE PACKAGE" in reason
    assert "uv sync --all-packages" in reason


def test_unimportable_member_is_rejected(tmp_path: Path) -> None:
    guard = ProvenanceGuard(tmp_path)

    reason = guard.verdict(
        MemberProvenance(name="loresigil", import_error="ModuleNotFoundError: no loresigil")
    )

    assert reason is not None
    assert "NOT IMPORTABLE" in reason


def test_audit_reports_every_dishonest_member_not_just_the_first(tmp_path: Path) -> None:
    """A partial answer would let an agent fix one member and walk into the next surprise."""
    honest = str(tmp_path / "lorescribe" / "lorescribe" / "__init__.py")
    original = str(REPO_ROOT / "loremaster" / "loremaster" / "__init__.py")
    observed = {
        "loremaster": MemberProvenance(name="loremaster", module_file=original),
        "loresigil": MemberProvenance(name="loresigil", module_file=None),
        "lorescribe": MemberProvenance(name="lorescribe", module_file=honest),
    }

    failures, receipts = ProvenanceGuard(tmp_path).audit(lambda name: observed[name])

    assert len(failures) == 2
    assert [receipt.name for receipt in receipts] == ["lorescribe"]


# ---------------------------------------------------------------------------
# The tool: fail-loud pin + positive control
# ---------------------------------------------------------------------------


def _poisoned_copy(tmp_path: Path) -> Path:
    """A scratch dir that is EXACTLY what ``cp -a`` hands you, and looks complete.

    The poison IS the ``.venv``'s editable ``.pth`` files, whose contents are absolute
    ORIGINAL paths.  Symlinking the real ``.venv`` reproduces those bytes exactly, without
    copying 108M into every test run.

    The copy also gets its OWN ``loremaster/loremaster/__init__.py`` — because that is the
    trap: the source is right there, it is simply never what runs.  A guard that checked
    for the *presence* of the member source would pass this tree; only one that checks
    where the import ACTUALLY resolves catches it.
    """
    copy = tmp_path / "poisoned"
    (copy / "loremaster" / "loremaster").mkdir(parents=True)
    (copy / "loremaster" / "loremaster" / "__init__.py").write_text(
        '"""The copy\'s own source — which is never what runs."""\n'
    )
    (copy / ".venv").symlink_to(REPO_ROOT / ".venv")
    return copy


def test_poisoned_copy_is_refused_loudly(tmp_path: Path) -> None:
    """THE FAIL-LOUD PIN: a copy that grades the original tree is REFUSED, non-zero.

    And refused for the RIGHT REASON — the message must name the original path it actually
    resolved to, not merely fail somehow.
    """
    copy = _poisoned_copy(tmp_path)

    result = _run_tool("--verify-only", str(copy))

    combined = result.stdout + result.stderr
    assert result.returncode != 0, f"the tool BLESSED a poisoned copy:\n{combined}"
    assert "GRADING THE ORIGINAL TREE" in combined
    assert "OUTSIDE the scratch tree" in combined
    # The receipt names the tree it really loaded — the original, not the copy.
    assert str(REPO_ROOT / "loremaster" / "loremaster" / "__init__.py") in combined
    assert "VERIFIED" not in combined


def test_verify_only_refuses_a_tree_with_no_interpreter(tmp_path: Path) -> None:
    """No ``.venv`` at all is a refusal too — never a silent pass."""
    bare = tmp_path / "bare"
    bare.mkdir()

    result = _run_tool("--verify-only", str(bare))

    assert result.returncode != 0
    assert "no interpreter" in result.stderr


def test_honest_copy_is_built_and_accepted(tmp_path: Path) -> None:
    """END-TO-END POSITIVE CONTROL: the real tool, on a real copy, ACCEPTS it.

    This is what makes the refusal above discrimination rather than a guard that always
    says no.  It exercises the true mechanism: rsync (poison excluded) →
    ``uv sync --all-packages`` → provenance assertion.  Slow by nature (a real copy and a
    real install); everything else in this file is cheap.
    """
    dest = tmp_path / "honest"

    result = _run_tool(str(dest))

    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    assert "scratch copy READY" in result.stdout

    # 1. The import resolves INSIDE the copy — asserted by the tool, echoed as a receipt.
    member_source = dest / "loremaster" / "loremaster" / "__init__.py"
    assert member_source.exists()
    assert f"-> {member_source}" in result.stdout
    assert str(REPO_ROOT / "loremaster" / "loremaster" / "__init__.py") not in result.stdout

    # 2. The poison source really is excluded from the copied tree.  (The copy HAS a
    #    `.venv` — its own, minted by the tool; what must not exist is copied bytecode in
    #    the SOURCE tree, whose `co_filename` would name the ORIGINAL files.)
    copied_bytecode = [p for p in dest.rglob("__pycache__") if ".venv" not in p.parts]
    assert copied_bytecode == [], "copied __pycache__ carries ORIGINAL co_filenames"

    # 3. ...and the copy's OWN venv names the copy's OWN paths — the actual mechanism.
    editable_pth = list(dest.glob(".venv/lib/python*/site-packages/_editable_impl_loremaster.pth"))
    assert len(editable_pth) == 1
    assert editable_pth[0].read_text().strip() == str(dest / "loremaster")

    # 4. `.git` is kept — agents run `git diff` / `git status` in copies.
    assert (dest / ".git").exists()

    # 5. The verifier ACCEPTS this genuinely-good copy (the standalone re-check path).
    reverify = _run_tool("--verify-only", str(dest))
    assert reverify.returncode == 0, f"{reverify.stdout}\n{reverify.stderr}"
    assert "scratch copy VERIFIED" in reverify.stdout


# ---------------------------------------------------------------------------
# Guard rails on DEST
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("dest", "expected"),
    [
        ("relative/path", "must be an ABSOLUTE path"),
        (str(REPO_ROOT / "scratchpad" / "copy"), "must live OUTSIDE the repo"),
        (str(REPO_ROOT), "must live OUTSIDE the repo"),
        # An ancestor of the repo would have `--force` rsync --delete over it — i.e. the
        # tool would eat $HOME.  There is no legitimate scratch copy at an ancestor.
        (str(REPO_ROOT.parent), "CONTAINS the repo"),
        ("/", "must not be '/'"),
    ],
)
def test_unsafe_dest_is_refused(dest: str, expected: str) -> None:
    result = _run_tool(dest)

    assert result.returncode != 0
    assert expected in result.stderr


def test_force_over_a_stale_poisoned_venv_mints_a_fresh_one(tmp_path: Path) -> None:
    """A stale `.venv` in DEST must not SURVIVE a --force rebuild.

    rsync's `--exclude` *protects* an excluded path in DEST from `--delete`, so the poisoned
    `.venv` an agent already `cp -a`'d there would otherwise live on inside the "fresh" copy.
    """
    dest = tmp_path / "restale"
    dest.mkdir()
    stale = dest / ".venv" / "lib" / "python3.14" / "site-packages"
    stale.mkdir(parents=True)
    poison = stale / "_editable_impl_loremaster.pth"
    poison.write_text(f"{REPO_ROOT / 'loremaster'}\n")

    result = _run_tool("--force", str(dest))

    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    assert poison.read_text().strip() == str(dest / "loremaster"), "the STALE .pth survived"


def test_existing_dest_is_refused_without_force(tmp_path: Path) -> None:
    """An agent's in-progress work is never silently rsync --delete'd away."""
    dest = tmp_path / "occupied"
    dest.mkdir()
    (dest / "work.txt").write_text("hours of it\n")

    result = _run_tool(str(dest))

    assert result.returncode != 0
    assert "already exists" in result.stderr
    assert (dest / "work.txt").exists()
