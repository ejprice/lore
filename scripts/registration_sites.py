#!/usr/bin/env python3
"""registration_sites.py — DERIVE every place a workspace member must be registered.

**WHY THIS EXISTS, and it is the only honest form of the answer (lore #251).**

``CLAUDE.md`` carries a numbered list of "the places a new workspace member must be
registered". That list has been wrong **three times, each time while the law about it was
being written**: it shipped with five entries (``mypy_path`` missed), was corrected to six
(``scratch_provenance.py`` missed), and was corrected to seven while two ∀ scanners
(``test_backoff_seam.py``, ``test_anchored_pattern_seam.py``) were still silently narrower
than the workspace they claimed to govern.

That is not carelessness. It is ``CLAUDE.md``'s own instrument lesson operating exactly as
predicted: **an enumeration of places to look is the artifact this repo has the most
receipts against.** Six instruments in that table were each defeated by the next name their
author had not thought of. A list of registration sites is the same shape.

So this script does not hold a list. **It derives one**, from a property that is true of a
registration site and false of ordinary code:

    A REGISTRATION SITE IS A PLACE WHERE TWO OR MORE MEMBER NAMES CO-OCCUR.

An ordinary consumer names ONE member (``from lorescribe.models import Chunk``). A registry
— a tuple, a ``mypy_path``, a ``MEMBERS=()``, consecutive ``COPY`` lines, a ``testpaths``
block, a sentence of prose listing the packages — names SEVERAL, because its job is to
enumerate them. That distinction is mechanical, it needs no list of file names, and it finds
sites nobody has thought of yet, which is the entire point.

Prose hits are NOT filtered out, deliberately: a docstring or a comment listing three of four
members is a served-English defect this packet was bitten by twice
(``test_conformance_provenance.py``'s module docstring, ``test_backoff_seam.py``'s scope
paragraph). A site that enumerates members goes stale whether it is code or English.

USAGE

    ./scripts/registration_sites.py            # report every site; exit 1 if any is INCOMPLETE
    ./scripts/registration_sites.py --all      # include sites that already name every member

Exit 0 means every co-occurrence site in the tree names every declared workspace member.
Exit 1 means at least one site is missing at least one member — with its ``file:line`` and
the missing names, which is the actionable form.

⚠ **THIS IS A DETECTOR, NOT A PROOF, AND ITS BOUNDS ARE MEASURED.** Stated so the next
reader meets them deliberately rather than discovering them:

* **It cannot see a registry that has fallen TWO members behind** — the threshold is
  three distinct names (:data:`_MIN_MEMBERS_FOR_A_SITE`), because two co-occurring names
  is ordinary prose and flagging it produced 82 hits nobody would read.
* **A construct wider than the window splits into two clusters**, and a half may fall
  under the threshold. Measured: ``test_secret_typing.py::_SCANNED_MEMBERS`` reports as
  stale for exactly this reason — its fifth entry sits fifteen commented lines below its
  first. **That is a FALSE POSITIVE of this tool, not a defect in that file.**
* **"Missing a member" is not always wrong.** A member's own ``pyproject.toml`` correctly
  does not depend on itself; ``LORE_NAMESPACES`` is a deliberate subset (``lorerunes``
  emits no logs). The output is a WORKLIST requiring judgement, never a verdict.

Its verdict is *"look at these"*, never *"there are no other sites"*. Use it to find
work, not to certify its absence.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tomllib
from collections import defaultdict
from pathlib import Path

#: Lines within this distance of each other count as one site. Multi-line tuples,
#: consecutive ``COPY`` lines and a ``members = [...]`` block all span a few lines;
#: two unrelated single-member mentions rarely sit this close.
_WINDOW_LINES = 4

#: A site must name at least this many DISTINCT members to be a registry rather than an
#: ordinary consumer. TWO would be the smallest number that distinguishes "enumerates"
#: from "imports one thing" — and it was measured too noisy to read (82 hits, mostly
#: ordinary prose naming a pair of members), so the threshold is THREE. That is the
#: trade recorded in this module's docstring under "cannot see a registry that has
#: fallen TWO members behind": raising the floor buys a readable worklist and pays for
#: it with a blind spot, deliberately.
_MIN_MEMBERS_FOR_A_SITE = 3

#: Trees whose hits are archived records rather than live registrations. Receipts are
#: preserved byte-faithful by repo law, so a stale member list inside one is evidence of
#: what was true then, not a site to update.
_EXCLUDED = (
    ":!docs/plans/v2/receipts",
    ":!docs/eval",
    ":!REPORT-*.md",
    ":!uv.lock",
)

_EXIT_OK = 0
_EXIT_INCOMPLETE = 1


def declared_members(repo_root: Path) -> list[str]:
    """The workspace members, read from the one file that defines them."""
    manifest = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    members: list[str] = manifest["tool"]["uv"]["workspace"]["members"]
    return sorted(members)


def _is_a_module_reference(text: str, member: str) -> bool:
    """Is this line REFERRING to the member's code rather than REGISTERING its name?

    ⚠ **THIS PREDICATE IS THE WHOLE INSTRUMENT, and its first version was useless.**
    Co-occurrence alone flagged **178 of 196** sites — nearly every import block in the
    repo, because a module that imports from two members mentions two members. A gate
    that fires on 178 honest sites is a gate that gets switched off, which is the one
    outcome worse than no gate (``CLAUDE.md``: *a gate that refuses honest code is a gate
    that gets SWITCHED OFF*).

    The discriminator is what the name is being used AS:

    * ``from lorescribe.models import Chunk`` — the member is a **module path**. It is a
      consumer. Nothing about it goes stale when a fifth member is added.
    * ``("loremaster", "loresigil")`` / ``lorescribe/lorescribe`` / ``COPY lorescribe/``
      / ``MEMBERS=(lorerunes …)`` — the member is **bare data**: a string, a path
      component, a shell word. That is an enumeration, and an enumeration is what goes
      stale.

    So a mention is dropped when the line is an ``import``/``from`` statement, or when the
    name is immediately followed by ``.`` (a dotted attribute/module path).
    """
    stripped = text.lstrip()
    if stripped.startswith(("import ", "from ")):
        return True
    index = text.find(member)
    while index != -1:
        after = text[index + len(member) : index + len(member) + 1]
        if after != ".":
            return False
        index = text.find(member, index + 1)
    return True


def _grep_member(repo_root: Path, member: str) -> list[tuple[str, int]]:
    """Every ``(path, line)`` REGISTERING ``member``, from ``git grep`` (tracked files only).

    Module references are filtered out by :func:`_is_a_module_reference`.
    """
    completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
        ["git", "grep", "-n", "-I", "--fixed-strings", member, "--", ".", *_EXCLUDED],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    hits: list[tuple[str, int]] = []
    for line in completed.stdout.splitlines():
        path, _, rest = line.partition(":")
        number, _, text = rest.partition(":")
        if number.isdigit() and not _is_a_module_reference(text, member):
            hits.append((path, int(number)))
    return hits


def find_sites(repo_root: Path, members: list[str]) -> list[tuple[str, int, set[str]]]:
    """Every co-occurrence site, as ``(path, first_line, members_named_there)``.

    Two mentions belong to the same site when they are in the same file and within
    :data:`_WINDOW_LINES` of each other.
    """
    by_file: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for member in members:
        for path, line in _grep_member(repo_root, member):
            by_file[path].append((line, member))

    sites: list[tuple[str, int, set[str]]] = []
    for path, mentions in sorted(by_file.items()):
        cluster_start = 0
        previous_line = 0
        named: set[str] = set()
        for line, member in sorted(mentions):
            if named and line - previous_line > _WINDOW_LINES:
                if len(named) >= _MIN_MEMBERS_FOR_A_SITE:
                    sites.append((path, cluster_start, named))
                named, cluster_start = set(), line
            elif not named:
                cluster_start = line
            named.add(member)
            previous_line = line
        if len(named) >= _MIN_MEMBERS_FOR_A_SITE:
            sites.append((path, cluster_start, named))
    return sites


def main(argv: list[str] | None = None) -> int:
    """Report registration sites; return an exit code (0 all complete, 1 some stale)."""
    parser = argparse.ArgumentParser(
        prog="registration_sites.py",
        description="Derive every place a workspace member must be registered (lore #251).",
    )
    parser.add_argument(
        "--all", action="store_true", help="also list sites that already name every member"
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent
    members = declared_members(repo_root)
    sites = find_sites(repo_root, members)

    incomplete = [(path, line, named) for path, line, named in sites if set(members) - named]

    print(f"declared workspace members ({len(members)}): {', '.join(members)}")
    print(f"co-occurrence sites found: {len(sites)}  ·  incomplete: {len(incomplete)}\n")

    # ANTI-VACUITY. A detector that silently finds nothing reports a clean tree in
    # exactly the same words as a clean tree does. This repo's registries are numerous
    # and stable, so zero sites means the grep or the filter broke, never that the
    # workspace has no registrations.
    if not sites:
        print(
            "NO SITES FOUND AT ALL — this tool is broken, not the tree. Either `git grep` "
            "returned nothing (wrong cwd? not a repo?) or _is_a_module_reference is now "
            "filtering everything. Do NOT read this as a clean result.",
            file=sys.stderr,
        )
        return _EXIT_INCOMPLETE

    if args.all:
        for path, line, named in sites:
            if not set(members) - named:
                print(f"  ok  {path}:{line}  names every member")
        print()

    for path, line, named in incomplete:
        missing = sorted(set(members) - named)
        print(f"  STALE  {path}:{line}  missing: {', '.join(missing)}")

    if incomplete:
        print(
            "\nEach line above enumerates workspace members and does not name them all. "
            "Some are registries a new member MUST join; some are prose that has gone "
            "stale; a few are deliberate SUBSETS (e.g. a logger-namespace list a "
            "non-logging member correctly stays out of). This script cannot tell those "
            "apart — it tells you where to look, and the judgement is yours. A deliberate "
            "subset should say so where it is written, so the next run of this script is "
            "read rather than re-derived."
        )
    return _EXIT_INCOMPLETE if incomplete else _EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
