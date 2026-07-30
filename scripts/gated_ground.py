"""THE DERIVED, PER-AXIS GATED-GROUND INVARIANT — is every committed module under a gate?

Two legs, each quantified over INPUTS (the files git tracks), never over gate sets:

* **LEG A (types)** — every tracked ``.py`` is under a typecheck root, parsed live from the
  ``MEMBERS`` array of ``scripts/typecheck.sh``, or is exempt.
* **LEG B (execution)** — every tracked test-shaped file is one pytest ACTUALLY COLLECTS,
  measured by a ``--collect-only`` subprocess over the same tree, or is exempt.

The legs are SEPARATE because three of the four historical instances of this defect class were
HALF-gaps — covered on one axis and naked on the other. The union of the two gate sets is green
over exactly those trees, so a guard that collapses the legs into one question is a wrong build
that ships green.

LEG B asks the COLLECTOR rather than parsing pytest's exclusion surface, because that surface
includes arbitrary code in a ``conftest.py`` (``collect_ignore``, ``collect_ignore_glob``) — an
open set no parser can close. A registered file that contributes no collected item is ungated
ground whatever silenced it, including mechanisms nobody has invented yet. The subprocess is
load-bearing: under ``xdist`` a live session's items are one worker's shard, so reading them
would manufacture findings for every file another worker holds.

BLIND IS NOT CLEAN. Every input this guard cannot derive raises :class:`GuardIsBlind`, because a
silent empty parse marks the whole tree covered and reports nothing — which prints exactly like a
clean tree. The served surface carries that state as DATA: a :class:`Verdict` names its
``blind_sources``, a non-empty set is never ``is_clean`` and never exits zero, and its rendered
bytes therefore differ from a healthy tree's. A correct reader behind an entry point that
swallows the refusal is a guard that cannot fail.

THREAT MODEL
------------
This gate is for the HONEST ENGINEER who commits a load-bearing module into a tree that no gate
— or only half the gates — covers, believing the repository's gates see it. It is NOT a security
boundary: anyone who can commit here can delete the instrument that checks this. So a
deliberately disguised file is out of scope and not a defect of this gate, while a new directory
of honest Python is exactly in scope — and a false positive on honest archived receipts would get
this gate switched off, which is why that class is exempted by a law-backed address.

STATED BOUNDS
-------------
Each bound is also declared in :data:`STATED_BOUNDS` with a named re-open trigger, so a reader
meets it deliberately instead of inheriting it silently. An unpinned known limitation is
indistinguishable from an unknown one.

* ``registration-not-execution``:
  This proves REGISTRATION in the gates' configuration, never that mypy or pytest ran or passed.
* ``execution-axis-covers-test-shaped-files-only``:
  LEG B quantifies over test-shaped files and conftest only, never over library modules.
  Execution coverage of library code is a coverage-measurement problem this does not claim.
* ``collection-convention``:
  A file of asserts named outside pytest's collection convention is invisible to pytest.
  That is a different defect class from an unregistered tree, and no gate scope can fix it.
* ``lore-index-axis``:
  The project index is a third gate direction this instrument does not model at all.
* ``conftest-collection-hooks``:
  A conftest contributes no collected item by design, so its reach stays bounded by registration.
  Every OTHER silencing mechanism is caught by construction, because LEG B measures collection.
* ``untracked-ground``:
  Untracked ground is outside the threat model: the derivation walks only the paths git tracks.
* ``file-types-modelled``:
  Only .py is modelled here; committed shell scripts are type-gated by the shellcheck leg.
  Their open hole is the execution axis alone.
* ``exemption-scope``:
  An exemption claims REGISTRATION on one axis, never that the exempted tree is correct.
"""

from __future__ import annotations

import fnmatch
import os
import re
import shlex
import subprocess
import sys
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from types import MappingProxyType

# ---------------------------------------------------------------------------
# Addresses and law-backed constants
# ---------------------------------------------------------------------------

#: The canonical type-check runner. Its ``MEMBERS`` array IS the type gate's scope: a tree absent
#: from it is checked by nothing, whatever any document says about it.
RUNNER_RELATIVE_PATH = "scripts/typecheck.sh"

#: The workspace manifest. pytest, ruff, mypy and uv all read their scope from it.
MANIFEST_RELATIVE_PATH = "pyproject.toml"

#: ONE law-backed address, deliberately a single string rather than a collection: archived
#: receipts are preserved byte-faithful because a reformatted receipt is no longer evidence of the
#: run it documents, so linting or re-typing them would falsify them. A collection here would
#: GROW, and a growing list of trees nobody gates is what this instrument exists to find.
ARCHIVED_RECEIPTS_ROOT = "docs/plans/v2/receipts"

#: pytest's OWN declared default for ``python_files``, as declared by
#: ``_pytest.python.pytest_addoption``. Carried as a constant because this instrument imports the
#: standard library and nothing else — and re-derived against the installed pytest by its contract
#: on every gate run, since a constant nobody re-derives is an inherited number wearing an
#: assertion.
PYTEST_DEFAULT_TEST_FILE_PATTERNS: tuple[str, ...] = ("test_*.py", "*_test.py")

#: pytest loads a conftest regardless of ``python_files``, so LEG B's scope includes it.
CONFTEST_FILENAME = "conftest.py"

#: A phrase, not a token. This is the mechanical property available for prose, and it is the one
#: that refuses a placeholder while admitting an honest sentence.
_MINIMUM_PHRASE_WORDS = 2

#: ``0`` is a successful collection; ``5`` is ``NO_TESTS_COLLECTED``, which is a RESULT about a
#: tree rather than a failure of the instrument. Treating it as blindness makes an honest tree
#: whose patterns match nothing report as unreadable — a false positive, and a gate that refuses
#: honest code is a gate that gets switched off.
_COLLECTOR_TOLERATED_EXIT_CODES = frozenset({0, 5})

_EXIT_CLEAN = 0
_EXIT_UNGATED_GROUND = 1
_EXIT_BLIND = 2

#: The first line of every finding. Fixed so a gate tail is scannable, and so a committed path
#: carrying a forged header line is detectable by counting headers against findings.
_MESSAGE_HEADER = "UNGATED GROUND"

#: Anchored at the start of a line, because a ``MEMBERS=(…)`` mention inside a comment is prose.
_MEMBERS_DECLARATION = re.compile(r"^MEMBERS=\((?P<body>[^)]*)\)[ \t]*$", re.MULTILINE)

#: The runner's per-root ``MYPYPATH`` map, read only inside its own declaration block.
_MYPYPATH_BLOCK = re.compile(
    r"^declare[ \t]+-A[ \t]+MEMBER_MYPYPATH=\((?P<body>[^)]*)\)[ \t]*$",
    re.MULTILINE,
)
_MYPYPATH_ENTRY = re.compile(r'\[(?P<member>[^\]]+)\]="(?P<extra_path>[^"]*)"')

#: A finding number, not prose and not a bare integer: the sigil is what makes it findable.
_FINDING_NUMBER = re.compile(r"^#\d+$")


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------


class GuardIsBlind(RuntimeError):
    """An input could not be derived, so no verdict about the tree is available.

    Raised rather than returned, and never caught inside a reader, because every silent no-op
    upstream of this guard produces the SAME output as a clean tree: an empty file list, empty
    parsed roots and an empty collection all report zero findings.
    """


class InvalidExemption(ValueError):
    """An exemption row lacks the evidence that would make it legitimate."""


def _blind(what: str) -> GuardIsBlind:
    """The ONE phrasing of a refusal, so every blind path says the same thing.

    The wording is load-bearing: a reader who sees no findings concludes the tree is clean, and
    the only way to stop that is to say which of the two this is.
    """
    return GuardIsBlind(f"{what} — the GUARD is blind, not the tree clean")


# ---------------------------------------------------------------------------
# Axes and fates
# ---------------------------------------------------------------------------


class GateAxis(Enum):
    """The two gates a committed file can be registered with, judged separately."""

    TYPES = "types"
    EXECUTION = "execution"

    @property
    def label(self) -> str:
        """The label the specification uses, so a message and a ruling name the same thing."""
        return "LEG A — types" if self is GateAxis.TYPES else "LEG B — execution"


class Fate(Enum):
    """What became of one file on one axis. Exactly one fate per file per axis."""

    COVERED = "covered by a scope the gate itself declares"
    EXEMPT_TABLE = "exempt by a pinned row"
    EXEMPT_ARCHIVED_RECEIPTS = "exempt as archived receipts"
    NOT_APPLICABLE = "not applicable on this axis"
    UNGATED = "ungated"


# ---------------------------------------------------------------------------
# Exemptions — deny by default, allowlist the safe
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Exemption:
    """One evidence-backed, axis-scoped exemption carrying a named re-open trigger.

    The validation is the durable part. A row is a DESIGN decision requiring a ruling, and these
    rules are what a future row meets instead of a blank page: a finding number so the reasoning
    is findable, a trigger that cites it so the row can be retired, a reason that is a phrase
    rather than a measurement (a count in a row is an inherited number that drifts silently while
    still reading as measured), and a root that is a real relative subtree rather than the whole
    repository.
    """

    root: str
    axis: GateAxis
    finding: str
    reason: str
    reopen_trigger: str

    def __post_init__(self) -> None:
        self._validate_root()
        if not _FINDING_NUMBER.match(self.finding):
            raise InvalidExemption(
                f"exemption for {self.root!r} carries finding {self.finding!r}, which is not a "
                f"finding number: without one, the reasoning behind the row is unfindable"
            )
        self._validate_reason()
        self._validate_reopen_trigger()

    def _validate_root(self) -> None:
        if not self.root.strip():
            raise InvalidExemption("an exemption names no root, so it is a claim about nothing")
        if _widens_to_whole_tree(self.root):
            raise InvalidExemption(
                f"exemption root {self.root!r} widens to the whole repository, which turns the "
                f"allowlist into an off switch for an entire axis"
            )

    def _validate_reason(self) -> None:
        if len(self.reason.split()) < _MINIMUM_PHRASE_WORDS:
            raise InvalidExemption(
                f"exemption for {self.root!r} gives reason {self.reason!r}, which is not a phrase "
                f"a later reader can act on"
            )
        if any(character.isdigit() for character in self.reason):
            raise InvalidExemption(
                f"exemption for {self.root!r} gives reason {self.reason!r}, which carries a "
                f"numeral: a count or a date in a row is an inherited number that drifts silently "
                f"while the row still reads as measured. Put it in a dated comment instead"
            )

    def _validate_reopen_trigger(self) -> None:
        if len(self.reopen_trigger.split()) < _MINIMUM_PHRASE_WORDS:
            raise InvalidExemption(
                f"exemption for {self.root!r} gives re-open trigger {self.reopen_trigger!r}, "
                f"which names no condition — a trigger nobody can recognise is a hope"
            )
        if self.finding not in self.reopen_trigger:
            raise InvalidExemption(
                f"exemption for {self.root!r} gives re-open trigger {self.reopen_trigger!r}, "
                f"which does not cite {self.finding}: a trigger detached from its finding cannot "
                f"be watched by whoever closes that finding"
            )


#: EMPTY, and the emptiness is a fact about the TREE: every committed module sits under a typecheck
#: root and every committed test-shaped file is one the collector reaches, so there is nothing left
#: to exempt. A row here is a design decision requiring a ruling — and read the history before
#: proposing a tree-root one, because a whole-tree row is an enumeration of an OPEN set whose
#: staleness is silent, which is why resolving the debt was ruled better than exempting it.
EXEMPTIONS: tuple[Exemption, ...] = ()


# ---------------------------------------------------------------------------
# Stated bounds
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StatedBound:
    """A limitation met deliberately, with the condition that re-opens it.

    A bound may legitimately cite no ledger finding, so ``finding`` is optional: demanding one
    would refuse honest bounds, and a gate that refuses honest content gets switched off.
    """

    identifier: str
    summary: str
    reopen_trigger: str
    finding: str | None = None


STATED_BOUNDS: tuple[StatedBound, ...] = (
    StatedBound(
        identifier="registration-not-execution",
        summary=(
            "This proves REGISTRATION in the gates' configuration, never that mypy or pytest ran "
            "or passed."
        ),
        reopen_trigger=(
            "a gate starts emitting a machine-readable record of what it actually checked; then "
            "coverage is derivable from that record instead of from configuration"
        ),
    ),
    StatedBound(
        identifier="execution-axis-covers-test-shaped-files-only",
        summary=(
            "LEG B quantifies over test-shaped files and conftest only, never over library "
            "modules."
        ),
        reopen_trigger=(
            "a coverage measurement lands in the standard gate; then LEG B can quantify over "
            "every module rather than over the test-shaped ones alone"
        ),
    ),
    StatedBound(
        identifier="collection-convention",
        summary=(
            "A file of asserts named outside pytest's collection convention is invisible to "
            "pytest."
        ),
        reopen_trigger=(
            "the tree adopts a second collection convention; then the patterns in force must be "
            "read from wherever pytest itself reads them"
        ),
    ),
    StatedBound(
        identifier="lore-index-axis",
        summary=(
            "The project index is a third gate direction this instrument does not model at all."
        ),
        reopen_trigger=(
            "#260 lands and the index becomes a gate with a declared scope; then a third leg is "
            "derivable the same way these two are"
        ),
        finding="#260",
    ),
    StatedBound(
        identifier="conftest-collection-hooks",
        summary=(
            "A conftest contributes no collected item by design, so its reach stays bounded by "
            "registration."
        ),
        reopen_trigger=(
            "pytest gains a supported way to report which conftest files it loaded; then conftest "
            "reach becomes measurable rather than merely registered"
        ),
    ),
    StatedBound(
        identifier="untracked-ground",
        summary=(
            "Untracked ground is outside the threat model: the derivation walks only the paths "
            "git tracks."
        ),
        reopen_trigger=(
            "a gate begins reading files that are not committed; then this enumeration has to "
            "widen past the index"
        ),
    ),
    StatedBound(
        identifier="file-types-modelled",
        summary=(
            "Only .py is modelled here; committed shell scripts are type-gated by the shellcheck "
            "leg."
        ),
        reopen_trigger=(
            "the shellcheck leg gains an execution-axis analogue; then a shell leg belongs in "
            "this instrument beside these two"
        ),
    ),
    StatedBound(
        identifier="exemption-scope",
        summary=(
            "An exemption claims REGISTRATION on one axis, never that the exempted tree is "
            "correct."
        ),
        reopen_trigger=(
            "a row is ever proposed for a tree a gate does read; then the row is the wrong "
            "instrument and the gate's scope is the right one"
        ),
    ),
)

#: Stated IN the instrument, not beside it. Three audits of a previous gate each rendered a
#: different verdict because nobody had written down who the gate is for; that absence cost two
#: fix waves. With the model stated, the verdicts follow mechanically.
THREAT_MODEL = (
    "This gate is for the HONEST ENGINEER who commits a load-bearing module into a tree that no "
    "gate\n— or only half the gates — covers, believing the repository's gates see it. It is NOT "
    "a security\nboundary: anyone who can commit here can delete the instrument that checks this. "
    "So a\ndeliberately disguised file is out of scope and not a defect of this gate, while a new "
    "directory\nof honest Python is exactly in scope — and a false positive on honest archived "
    "receipts would get\nthis gate switched off, which is why that class is exempted by a "
    "law-backed address."
)


# ---------------------------------------------------------------------------
# Membership — path-component-wise, at every call site
# ---------------------------------------------------------------------------


def is_under(path: str, tree: str) -> bool:
    """Is ``path`` inside ``tree``, component-wise?

    ``str.startswith`` is the wrong instrument, and the difference is not hypothetical: it hands a
    sibling directory one character away from a real scope both the gate and the exemption. This
    helper being correct is not enough — it has to be the thing every site CALLS.
    """
    return PurePosixPath(path).is_relative_to(PurePosixPath(tree))


def _widens_to_whole_tree(entry: str) -> bool:
    """Would this scope entry silently cover the entire repository, or escape it?

    The nastiest silent no-op in the set: a scope that widens to the tree root marks every file
    covered and reports zero gaps, which is a false clear wearing a clean bill of health.
    """
    if not entry.strip():
        return True
    candidate = PurePosixPath(entry)
    return candidate.is_absolute() or candidate.parts == () or ".." in candidate.parts


# ---------------------------------------------------------------------------
# Readers — every input parsed from the configuration the gates actually execute
# ---------------------------------------------------------------------------


def _read_runner(repo_root: Path) -> str:
    runner_path = repo_root / RUNNER_RELATIVE_PATH
    try:
        return runner_path.read_text(encoding="utf-8")
    except OSError as error:
        raise _blind(
            f"the guard could not read the MEMBERS declaration in {RUNNER_RELATIVE_PATH} at "
            f"{runner_path} ({error})"
        ) from error


def typecheck_roots(repo_root: Path) -> list[str]:
    """The type gate's scope, parsed from the runner's single ``MEMBERS`` declaration.

    A root may be a directory or a single file — the finest grain of a root — but it must NAME
    SOMETHING: mypy's answer to a phantom entry is ``Cannot read file``, so the runner then exits
    non-zero for a reason unrelated to type errors while this guard calls the phantom's tree
    covered.
    """
    runner_text = _read_runner(repo_root)
    declarations = [match.group("body") for match in _MEMBERS_DECLARATION.finditer(runner_text)]
    if not declarations:
        raise _blind(f"{RUNNER_RELATIVE_PATH} declares no MEMBERS array")
    if len(declarations) > 1:
        raise _blind(
            f"{RUNNER_RELATIVE_PATH} carries more than one MEMBERS declaration, and the shell "
            f"hands the LAST one to the gate while a line-anchored search finds the FIRST: a "
            f"narrowed second declaration would certify as the wider first"
        )
    roots = shlex.split(str(declarations[0]))
    if not roots:
        raise _blind(f"the MEMBERS declaration in {RUNNER_RELATIVE_PATH} is empty")
    for root in roots:
        if _widens_to_whole_tree(root):
            raise _blind(
                f"MEMBERS entry {root!r} widens to the whole tree, which would mark every file "
                f"covered and report no gap at all"
            )
        if not (repo_root / root).exists():
            raise _blind(
                f"MEMBERS entry {root!r} names nothing in this checkout, so the gate iterates a "
                f"phantom and checks nothing, which reads as coverage"
            )
    return roots


def member_mypypath(repo_root: Path) -> dict[str, str]:
    """The runner's per-root ``MYPYPATH`` additions, exactly as the runner declares them.

    A root whose modules import siblings resolves them only with this addition, so the map is part
    of the gate's real scope. Fabricating it would answer a question about the RUNNER with this
    guard's own opinion; a runner declaring no map gets an empty answer.
    """
    runner_text = _read_runner(repo_root)
    blocks = [match.group("body") for match in _MYPYPATH_BLOCK.finditer(runner_text)]
    if not blocks:
        return {}
    if len(blocks) > 1:
        raise _blind(
            f"{RUNNER_RELATIVE_PATH} carries more than one MEMBER_MYPYPATH declaration, so the "
            f"map this guard reads is not the map the gate uses"
        )
    declared: dict[str, str] = {}
    for entry in _MYPYPATH_ENTRY.finditer(str(blocks[0])):
        declared[str(entry.group("member"))] = str(entry.group("extra_path"))
    return declared


def _manifest(repo_root: Path) -> Mapping[str, object]:
    manifest_path = repo_root / MANIFEST_RELATIVE_PATH
    try:
        raw = manifest_path.read_bytes()
    except OSError as error:
        raise _blind(
            f"the guard could not read {MANIFEST_RELATIVE_PATH} at {manifest_path} ({error})"
        ) from error
    try:
        return tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise _blind(
            f"{MANIFEST_RELATIVE_PATH} at {manifest_path} does not parse ({error})"
        ) from error


def _section(manifest: Mapping[str, object], *keys: str) -> Mapping[str, object] | None:
    """One nested table of the manifest, or ``None`` when it is absent."""
    current: Mapping[str, object] = manifest
    for key in keys:
        value = current.get(key)
        if not isinstance(value, Mapping):
            return None
        current = value
    return current


def _string_list(value: object, *, described_as: str) -> list[str]:
    if not isinstance(value, list):
        raise _blind(f"{described_as} is {value!r}, which is not a list of paths")
    entries: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise _blind(f"{described_as} carries {item!r}, which is not a path")
        entries.append(item)
    return entries


def _declared_paths(repo_root: Path, *, table: tuple[str, ...], key: str) -> list[str]:
    """A declared list of paths from one manifest table, refusing every empty answer.

    ONE reader for four declarations, so the refusal policy cannot drift between them: an absent
    table, an absent key and an empty list are all the same silent no-op wearing three faces.
    """
    table_name = ".".join(table)
    described_as = f"[{table_name}] {key} in {MANIFEST_RELATIVE_PATH}"
    section = _section(_manifest(repo_root), *table)
    if section is None:
        raise _blind(
            f"{MANIFEST_RELATIVE_PATH} declares no [{table_name}] table, so {key} is unreadable"
        )
    if key not in section:
        raise _blind(f"{described_as} is not declared")
    entries = _string_list(section[key], described_as=described_as)
    if not entries:
        raise _blind(f"{described_as} is empty")
    return entries


def pytest_testpaths(repo_root: Path) -> list[str]:
    """The execution gate's scope, parsed from the manifest pytest reads."""
    testpaths = _declared_paths(
        repo_root, table=("tool", "pytest", "ini_options"), key="testpaths"
    )
    for testpath in testpaths:
        if _widens_to_whole_tree(testpath):
            raise _blind(
                f"testpaths entry {testpath!r} widens to the whole tree, which would make every "
                f"test-shaped file read as covered and report no execution gap at all"
            )
        if not (repo_root / testpath).is_dir():
            raise _blind(
                f"testpaths entry {testpath!r} is not a directory in this checkout, so pytest "
                f"collects nothing there and the execution axis is satisfied by an empty tree"
            )
    return testpaths


def workspace_members(repo_root: Path) -> list[str]:
    """The workspace members the manifest declares — the type gate's floor, not its ceiling."""
    return _declared_paths(repo_root, table=("tool", "uv", "workspace"), key="members")


def ruff_excluded_trees(repo_root: Path) -> list[str]:
    """The trees this repository declares excluded from linting.

    Read because the archived-receipts exemption is anchored in a line someone actually committed
    rather than in this guard's opinion: if that declaration moves, the guard would be exempting a
    tree nothing calls archived.
    """
    return _declared_paths(repo_root, table=("tool", "ruff"), key="extend-exclude")


def pytest_test_file_patterns(repo_root: Path) -> list[str]:
    """The ``python_files`` patterns in force, from the same manifest pytest reads.

    A hardcoded pattern list is the two-name enumeration the lesson table says loses: a committed
    file using the other default shape walks straight through it, and a configured override makes
    the hardcoded answer wrong in the opposite direction.
    """
    section = _section(_manifest(repo_root), "tool", "pytest", "ini_options")
    if section is None or "python_files" not in section:
        return list(PYTEST_DEFAULT_TEST_FILE_PATTERNS)
    described_as = f"[tool.pytest.ini_options] python_files in {MANIFEST_RELATIVE_PATH}"
    patterns = _string_list(section["python_files"], described_as=described_as)
    if not patterns:
        raise _blind(f"{described_as} is empty, so nothing is test-shaped and LEG B is vacuous")
    return patterns


def tracked_python_files(repo_root: Path) -> list[str]:
    """Every ``.py`` git tracks, NUL-separated so a hostile path survives intact.

    git quotes and backslash-escapes unusual paths on its line-oriented output and emits them raw
    only under NUL separation, so a reader that splits lines returns a path that is not the path —
    and every membership test on it is then meaningless.
    """
    records = _git(repo_root, "ls-files", "-z").split("\0")
    tracked = sorted(record for record in records if record.endswith(".py"))
    if not tracked:
        raise _blind(
            f"git tracks no .py at all under {repo_root}, which is a wrong root or a wrong "
            f"invocation rather than a repository with no Python in it"
        )
    return tracked


def _git(repo_root: Path, *arguments: str) -> str:
    """One git invocation, with both failure modes named rather than swallowed.

    The missing-binary path is not hypothetical: a deployed image without git turned an OSError
    into a silent empty result for months, invisible on every host that HAS git.
    """
    command = ["git", "-C", str(repo_root), *arguments]
    try:
        completed = subprocess.run(command, capture_output=True, check=False)
    except OSError as error:
        raise _blind(f"the guard could not execute git ({error})") from error
    if completed.returncode != _EXIT_CLEAN:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise _blind(
            f"git {' '.join(arguments)} failed under {repo_root} with status "
            f"{completed.returncode} ({detail})"
        )
    return completed.stdout.decode("utf-8", errors="surrogateescape")


def collected_test_files(repo_root: Path) -> frozenset[str]:
    """The files pytest ACTUALLY collects items from, measured by a subprocess over ``repo_root``.

    A subprocess and not the live session's items: under ``xdist`` a worker sees only its shard,
    so a live reading would invent a finding for every file another worker holds. The
    environment's own ``PYTEST_ADDOPTS`` is cleared because this asks one specific question and an
    inherited option can change the shape of the answer.
    """
    command = [
        sys.executable,
        "-m",
        "pytest",
        "--collect-only",
        "-q",
        "--no-header",
        "-p",
        "no:cacheprovider",
        "-p",
        "no:randomly",
    ]
    environment = {**os.environ, "PYTEST_ADDOPTS": ""}
    try:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )
    except OSError as error:
        raise _blind(f"the guard could not run the collector subprocess ({error})") from error
    if completed.returncode not in _COLLECTOR_TOLERATED_EXIT_CODES:
        raise _blind(
            f"the collector subprocess exited {completed.returncode} under {repo_root}, so "
            f"'nothing was collected' would be a failed run wearing a clean answer\n"
            f"{completed.stdout.strip()}\n{completed.stderr.strip()}"
        )
    contributing = frozenset(
        line.split("::", 1)[0].strip() for line in completed.stdout.splitlines() if "::" in line
    )
    if completed.returncode == _EXIT_CLEAN and not contributing:
        raise _blind(
            f"the collector subprocess exited zero under {repo_root} and named no collected item, "
            f"so its output is not the shape this guard reads"
        )
    return contributing


# ---------------------------------------------------------------------------
# Mypy configuration this guard does not model
# ---------------------------------------------------------------------------

#: ALLOWLIST THE SAFE. The forbidden set is unbounded — a relaxation invented after this guard
#: defeats any list of names — while the set of settings whose effect on WHICH FILES ARE CHECKED
#: is understood here is small and enumerable. Every key below is one this guard has reasoned
#: about: none of them can make a registered file unchecked.
_MODELLED_MYPY_TABLE_KEYS = frozenset(
    {
        "python_version",
        "strict",
        "plugins",
        "warn_unreachable",
        "disallow_any_unimported",
        "mypy_path",
        "explicit_package_bases",
        "namespace_packages",
    }
)

#: The same allowlist for a per-module override block. ``module`` names the scope; the rest widen
#: what mypy tolerates FROM an import without exempting the named module from being checked.
_MODELLED_MYPY_OVERRIDE_KEYS = frozenset(
    {
        "module",
        "ignore_missing_imports",
        "follow_untyped_imports",
        "disallow_any_unimported",
    }
)

_MYPY_OVERRIDES_KEY = "overrides"


def unmodelled_mypy_configuration(repo_root: Path) -> list[str]:
    """Mypy settings this guard cannot model, each named with the two ways out.

    LEG A's verdict is path membership, so any setting that makes a REGISTERED file unchecked IN
    FACT would leave this guard certifying a tree it cannot see. Refusing to mis-model beats
    silently mis-modelling — and the answer is consulted by :func:`classify`, because a reader
    nobody calls is the same shape as a guard nobody runs.
    """
    table = _section(_manifest(repo_root), "tool", "mypy")
    if table is None:
        return []
    refusals = [
        f"[tool.mypy] {key} = {table[key]!r} is a mypy setting this guard does not model, so a "
        f"registered file could be unchecked in fact; extend it or remove the {key}"
        for key in sorted(table)
        if key not in _MODELLED_MYPY_TABLE_KEYS and key != _MYPY_OVERRIDES_KEY
    ]
    refusals.extend(_unmodelled_override_settings(table.get(_MYPY_OVERRIDES_KEY)))
    return refusals


def _unmodelled_override_settings(overrides: object) -> list[str]:
    if not isinstance(overrides, list):
        return []
    refusals: list[str] = []
    for override in overrides:
        if not isinstance(override, Mapping):
            continue
        modules = _override_modules(override)
        refusals.extend(
            f"[[tool.mypy.overrides]] {key} = {override[key]!r} for {modules} is a mypy setting "
            f"this guard does not model, so a registered file could be unchecked in fact; extend "
            f"it or remove the {key}"
            for key in sorted(override)
            if key not in _MODELLED_MYPY_OVERRIDE_KEYS
        )
    return refusals


def _override_modules(override: Mapping[str, object]) -> str:
    declared = override.get("module")
    if isinstance(declared, str):
        return declared
    if isinstance(declared, list):
        return ", ".join(str(module) for module in declared)
    return "an override naming no module"


# ---------------------------------------------------------------------------
# The verdict objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FileVerdict:
    """One tracked file's fate on EVERY axis. An unjudged axis is an axis nothing guards."""

    path: str
    fates: Mapping[GateAxis, Fate]


@dataclass(frozen=True)
class UngatedFile:
    """One (file, axis) pair no gate reads, with the message a reader will act on."""

    path: str
    axis: GateAxis
    message: str


@dataclass(frozen=True)
class Verdict:
    """The SERVED surface: what is ungated, and every input the guard could not derive.

    Blindness is a FIELD and not only an exception, because the seam a consumer reads is the only
    seam where trust lives: a non-empty ``blind_sources`` is never clean, never exits zero, and
    renders bytes a healthy tree cannot produce.
    """

    findings: tuple[UngatedFile, ...]
    blind_sources: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        """No ungated ground AND no input the guard failed to read. Both, or it is not clean."""
        return not self.findings and not self.blind_sources

    @property
    def exit_code(self) -> int:
        """Blindness dominates: it is a worse answer than a finding, never a better one."""
        if self.blind_sources:
            return _EXIT_BLIND
        return _EXIT_UNGATED_GROUND if self.findings else _EXIT_CLEAN

    def render(self) -> str:
        """The bytes a consumer reads: distinct for clean, for findings, and for blind."""
        if self.blind_sources:
            return "\n\n".join(
                [
                    "THE GUARD IS BLIND — no verdict about this tree was reached, so the absence "
                    "of findings below means nothing was measured:",
                    *self.blind_sources,
                ]
            )
        if self.findings:
            return "\n\n".join(finding.message for finding in self.findings)
        return (
            "GATED GROUND — every tracked module is registered with the type gate, and every "
            "tracked test-shaped file is one the collector reaches."
        )


# ---------------------------------------------------------------------------
# The derivation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Scopes:
    """Everything the classification needs: all of it derived, none of it assumed."""

    tracked: tuple[str, ...]
    typecheck_roots: tuple[str, ...]
    testpaths: tuple[str, ...]
    test_file_patterns: tuple[str, ...]
    collected: frozenset[str]


def _derive(repo_root: Path) -> _Scopes:
    """Derive every input, refusing on the first one that cannot be read.

    The two checks that are not readers — the receipts anchor and the mypy model — sit here rather
    than in a caller, because a reader nobody consults is the same shape as a guard nobody runs.
    The collector is derived LAST: it is the expensive input, and there is no point paying for it
    to describe a tree whose configuration is already unreadable.
    """
    tracked = tracked_python_files(repo_root)
    roots = typecheck_roots(repo_root)
    testpaths = pytest_testpaths(repo_root)
    patterns = pytest_test_file_patterns(repo_root)

    unmodelled = unmodelled_mypy_configuration(repo_root)
    if unmodelled:
        raise _blind(
            "the type gate's configuration carries settings whose effect on which files are "
            "checked this guard cannot model, so LEG A would be a claim about a scope it cannot "
            "see: " + "; ".join(unmodelled)
        )

    if ARCHIVED_RECEIPTS_ROOT not in ruff_excluded_trees(repo_root):
        raise _blind(
            f"{ARCHIVED_RECEIPTS_ROOT} is not among the trees {MANIFEST_RELATIVE_PATH} declares "
            f"excluded from linting, so the archived-receipts exemption rests on nothing this "
            f"repository actually calls archived"
        )
    if not any(is_under(path, ARCHIVED_RECEIPTS_ROOT) for path in tracked):
        raise _blind(
            f"no tracked .py sits under {ARCHIVED_RECEIPTS_ROOT}, so the archived-receipts class "
            f"matches nothing and has been exempting nothing without anyone noticing"
        )

    return _Scopes(
        tracked=tuple(tracked),
        typecheck_roots=tuple(roots),
        testpaths=tuple(testpaths),
        test_file_patterns=tuple(patterns),
        collected=collected_test_files(repo_root),
    )


def _exempting_row(
    path: str, axis: GateAxis, exemptions: Sequence[Exemption]
) -> Exemption | None:
    """The pinned row that exempts this file ON THIS AXIS, if any.

    Axis-scoped deliberately: a row is never an exemption from the whole guard, so a test file in
    a tree exempted on types is still reported when no gate run collects it.
    """
    for row in exemptions:
        if row.axis is axis and is_under(path, row.root):
            return row
    return None


def _types_fate(path: str, *, scopes: _Scopes, exemptions: Sequence[Exemption]) -> Fate:
    """LEG A. Every committed ``.py`` is type-gateable, so this axis has no NOT_APPLICABLE.

    COVERED beats an exemption on purpose: a row whose tree became gated is stale, and precedence
    is what makes it visible instead of letting it hide behind itself.
    """
    if any(is_under(path, root) for root in scopes.typecheck_roots):
        return Fate.COVERED
    if is_under(path, ARCHIVED_RECEIPTS_ROOT):
        return Fate.EXEMPT_ARCHIVED_RECEIPTS
    if _exempting_row(path, GateAxis.TYPES, exemptions) is not None:
        return Fate.EXEMPT_TABLE
    return Fate.UNGATED


def _is_test_shaped(path: str, patterns: Sequence[str]) -> bool:
    name = PurePosixPath(path).name
    return name == CONFTEST_FILENAME or any(
        fnmatch.fnmatch(name, pattern) for pattern in patterns
    )


def _execution_fate(path: str, *, scopes: _Scopes, exemptions: Sequence[Exemption]) -> Fate:
    """LEG B, where coverage is MEASURED rather than declared.

    A registered file the collector never reaches is ungated ground whatever silenced it. The one
    exception is a conftest, which contributes no collected item by design and is therefore
    bounded by registration — a stated bound, not an oversight.
    """
    if not _is_test_shaped(path, scopes.test_file_patterns):
        return Fate.NOT_APPLICABLE
    if PurePosixPath(path).name == CONFTEST_FILENAME:
        if any(is_under(path, testpath) for testpath in scopes.testpaths):
            return Fate.COVERED
    elif path in scopes.collected:
        return Fate.COVERED
    if is_under(path, ARCHIVED_RECEIPTS_ROOT):
        return Fate.EXEMPT_ARCHIVED_RECEIPTS
    if _exempting_row(path, GateAxis.EXECUTION, exemptions) is not None:
        return Fate.EXEMPT_TABLE
    return Fate.UNGATED


def _classify(scopes: _Scopes, exemptions: Sequence[Exemption]) -> list[FileVerdict]:
    """One verdict per tracked file, in the enumeration's own (sorted) order."""
    return [
        FileVerdict(
            path=path,
            fates=MappingProxyType(
                {
                    GateAxis.TYPES: _types_fate(path, scopes=scopes, exemptions=exemptions),
                    GateAxis.EXECUTION: _execution_fate(
                        path, scopes=scopes, exemptions=exemptions
                    ),
                }
            ),
        )
        for path in scopes.tracked
    ]


def classify(
    repo_root: Path, *, exemptions: Sequence[Exemption] = EXEMPTIONS
) -> list[FileVerdict]:
    """Every tracked ``.py`` with exactly one fate per axis — the whole accounting, in one place.

    Raises :class:`GuardIsBlind` rather than returning a partial answer: a file that vanishes from
    this list is a file nothing reports, and a shorter list looks exactly like a cleaner tree.
    """
    return _classify(_derive(repo_root), exemptions)


# ---------------------------------------------------------------------------
# The served surface
# ---------------------------------------------------------------------------


def _types_message(path: str, scopes: _Scopes) -> str:
    return (
        f"{_MESSAGE_HEADER} ({GateAxis.TYPES.label}): {path!r} is a committed .py under no "
        f"typecheck root.\n"
        f"It is outside every root {RUNNER_RELATIVE_PATH} declares in MEMBERS: "
        f"{', '.join(scopes.typecheck_roots)}.\n"
        f"This pins REGISTRATION in the gates' configuration — it does not prove that mypy ran, "
        f"or passed; the gate's own exit code proves that.\n"
        f"Fix: add its tree to the MEMBERS array in {RUNNER_RELATIVE_PATH}, or ESCALATE — there "
        f"is no exemption mechanism, deliberately. Do not widen the receipts class to admit it."
    )


def _execution_message(path: str, scopes: _Scopes) -> str:
    return (
        f"{_MESSAGE_HEADER} ({GateAxis.EXECUTION.label}): {path!r} is a committed test-shaped .py "
        f"that no gate run collects.\n"
        f"It is outside every testpaths entry {MANIFEST_RELATIVE_PATH} declares, or inside one "
        f"that collects nothing from it: {', '.join(scopes.testpaths)}.\n"
        f"This pins REGISTRATION in the gates' configuration — it does not prove that pytest "
        f"ran, or passed; the gate's own exit code proves that.\n"
        f"Fix: add its tree to testpaths in {MANIFEST_RELATIVE_PATH} and check the collector "
        f"reaches it, or ESCALATE — there is no exemption mechanism, deliberately. Do not widen "
        f"the receipts class to admit it."
    )


def _finding(path: str, axis: GateAxis, scopes: _Scopes) -> UngatedFile:
    """One finding, with the path rendered UNAMBIGUOUSLY.

    A committed path is stored text this guard interpolates into structured output, and a path may
    carry a newline: rendered raw, one carrying a line shaped like this header would parse as a
    second, fabricated finding.
    """
    if axis is GateAxis.TYPES:
        return UngatedFile(path=path, axis=axis, message=_types_message(path, scopes))
    return UngatedFile(path=path, axis=axis, message=_execution_message(path, scopes))


def ungated_ground(
    repo_root: Path, *, exemptions: Sequence[Exemption] = EXEMPTIONS
) -> Verdict:
    """The served verdict: what is ungated, or what the guard could not see.

    This is the only place a :class:`GuardIsBlind` is caught, and it is caught in order to carry
    it OUTWARD as data — never to continue past it. A build that swallowed it here and served a
    clean verdict would be a guard that cannot fail, which is why blindness is monotone to this
    surface and byte-diffed against a healthy tree by the contract.
    """
    try:
        scopes = _derive(repo_root)
    except GuardIsBlind as blindness:
        return Verdict(findings=(), blind_sources=(str(blindness),))
    findings = tuple(
        _finding(verdict.path, axis, scopes)
        for verdict in _classify(scopes, exemptions)
        for axis in GateAxis
        if verdict.fates[axis] is Fate.UNGATED
    )
    return Verdict(findings=findings, blind_sources=())
