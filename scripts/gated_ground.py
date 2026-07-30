"""THE DERIVED, PER-AXIS GATED-GROUND INVARIANT — is every committed module under a gate?

Two legs, each quantified over INPUTS (the files git tracks), never over gate sets:

* **LEG A (types)** — every tracked ``.py`` is under a typecheck root, parsed live from the
  ``MEMBERS`` array of ``scripts/typecheck.sh``, or is exempt.
* **LEG B (execution)** — every tracked test-shaped file is one pytest ACTUALLY COLLECTS,
  measured by a ``--collect-only`` subprocess over the same tree, or is exempt.

The legs are SEPARATE because the instances that prompted this instrument were HALF-gaps —
covered on one axis and naked on the other (#188, #233, #261). The union of the two gate sets is
green over exactly those trees, so a guard that collapses the legs into one question is a wrong
build that ships green.

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
* ``inherited-pytest-environment``:
  The collector child inherits this environment, so an inherited PYTEST_ADDOPTS changes what it measures.
  Clearing it would mean reading the environment outside this repository's one secret-resolution
  entry point — a design decision, and not this guard's to take. The anti-vacuity leg is what
  keeps the consequence LOUD instead of a wrong verdict.
* ``gate-configuration-precedence``:
  A gate's configuration must be the pyproject.toml this guard reads, or it refuses.
  mypy searches ``mypy.ini`` / ``.mypy.ini`` before it, pytest searches four names before it, and
  the FIRST accepted candidate wins — so a committed sidecar means every setting read here is
  being ignored while the guard certifies a gate that is switched off. What is NOT modelled is
  the sidecar's CONTENT: presence alone is the refusal, because a model of another tool's
  precedence rules is a second place to be wrong.
* ``collector-memoisation``:
  The collector answer is memoised behind a fingerprint of its file inputs.
  The fingerprint covers the gate configuration files, every tracked ``.py`` and every ``.py``
  under a collection root — so a change it cannot see (an inherited PYTEST_ADDOPTS altered inside
  one process; an installed plugin, which cannot change mid-process) would serve a stale answer.
* ``collection-pattern-platform``:
  LEG B ports the POSIX branch of pytest's path matcher; the Windows branch is absent.
  Every path here comes from ``git ls-files``, which emits POSIX separators, and the port is
  pinned against the installed pytest as an oracle rather than argued.
"""

from __future__ import annotations

import fnmatch
import hashlib
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

#: Configuration filenames that OUTRANK :data:`MANIFEST_RELATIVE_PATH` for one of the two gate
#: tools — the first four of mypy's ``defaults.CONFIG_NAMES + SHARED_CONFIG_NAMES`` order and of
#: pytest's ``_pytest.config.findpaths.locate_config`` order, up to but not including the manifest.
#: Carried as a constant because this instrument imports the standard library and nothing else,
#: and RE-DERIVED against both installed tools by its contract on every gate run — a constant
#: nobody re-derives is an inherited number wearing an assertion, and this particular one decides
#: whether LEG A is a claim about the configuration the gate executes or about a file it ignores.
SHADOWING_CONFIGURATION_FILENAMES: tuple[str, ...] = (
    "mypy.ini",
    ".mypy.ini",
    "pytest.toml",
    ".pytest.toml",
    "pytest.ini",
    ".pytest.ini",
)

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

    Carries a ``door``: a STABLE IDENTITY for the refusal that raised it. The identity exists so
    that the FAILURE SET of this guard is DERIVABLE rather than written down — the contract AST-
    reads every door out of this module's source and demands a constructed broken state for each
    one, both ways. A hand-written list of doors was measured failing exactly the way every
    enumeration in this repository's lesson table fails: quantified over five named doors,
    blindness-monotonicity held for 6 states of 26, and a build honouring precisely those five
    served 17 false clears while passing every pin.
    """

    def __init__(self, door: str, message: str) -> None:
        super().__init__(message)
        self.door = door


class InvalidExemption(ValueError):
    """An exemption row lacks the evidence that would make it legitimate."""


class IncoherentVerdict(ValueError):
    """A verdict was constructed in a shape that describes no world.

    The only such shape is findings AND blind sources at once: the derivation refuses on the
    first input it cannot read, BEFORE it classifies anything, so a verdict can hold findings or
    name blind sources and never both. Refused at construction rather than left to a convention,
    because a partial answer is indistinguishable from a cleaner tree — and the served surface
    reads its whole verdict off this pair.
    """


def _blind(door: str, what: str) -> GuardIsBlind:
    """The ONE phrasing of a refusal, so every blind path says the same thing.

    The wording is load-bearing: a reader who sees no findings concludes the tree is clean, and
    the only way to stop that is to say which of the two this is.

    ``door`` is that refusal's stable identity — see :class:`GuardIsBlind`. It is a literal at
    every call site on purpose: a computed identity is invisible to the derivation that demands a
    probe for it, which would make this mechanism a name list again.
    """
    return GuardIsBlind(door, f"{what} — the GUARD is blind, not the tree clean")


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
        # ``fullmatch``, never ``match`` (#210): Python's ``$`` also matches immediately before a
        # TRAILING NEWLINE, so ``.match`` accepts "#188\n" against a pattern that reads as closed —
        # and a finding number carrying a line break is a row that injects a line into every
        # message rendering it. Measured before the fix: such a row constructed.
        if not _FINDING_NUMBER.fullmatch(self.finding):
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
                f"exemption root {self.root!r} widens to the whole repository, or escapes it: the "
                f"first turns the allowlist into an off switch for an entire axis, and the second "
                f"exempts ground this repository does not contain"
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
    StatedBound(
        identifier="inherited-pytest-environment",
        summary=(
            "The collector child inherits this environment, so an inherited PYTEST_ADDOPTS changes "
            "what it measures."
        ),
        reopen_trigger=(
            "the environment-read seam gains an evidence-backed entry for an operational knob, "
            "or pytest gains a flag that neutralises an inherited PYTEST_ADDOPTS"
        ),
    ),
    StatedBound(
        identifier="gate-configuration-precedence",
        summary=(
            "A gate's configuration must be the pyproject.toml this guard reads, or it refuses."
        ),
        reopen_trigger=(
            "mypy or pytest gains a supported way to report WHICH configuration file it read; "
            "then the file in force is measurable rather than derived from a precedence order"
        ),
        finding="#107",
    ),
    StatedBound(
        identifier="collector-memoisation",
        summary="The collector answer is memoised behind a fingerprint of its file inputs.",
        reopen_trigger=(
            "the collector gains a way to report the inputs it actually read, or the "
            "environment-read seam admits an operational knob for this guard; then the memo key "
            "can cover what this one cannot"
        ),
    ),
    StatedBound(
        identifier="collection-pattern-platform",
        summary=(
            "LEG B ports the POSIX branch of pytest's path matcher; the Windows branch is absent."
        ),
        reopen_trigger=(
            "this repository is ever gated on a Windows host; then the other branch of pytest's "
            "own matcher belongs in the port"
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
            "runner-unreadable",
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
        raise _blind(
            "members-declaration-absent", f"{RUNNER_RELATIVE_PATH} declares no MEMBERS array"
        )
    if len(declarations) > 1:
        raise _blind(
            "members-declaration-duplicated",
            f"{RUNNER_RELATIVE_PATH} carries more than one MEMBERS declaration, and the shell "
            f"hands the LAST one to the gate while a line-anchored search finds the FIRST: a "
            f"narrowed second declaration would certify as the wider first"
        )
    roots = shlex.split(str(declarations[0]))
    if not roots:
        raise _blind(
            "members-empty", f"the MEMBERS declaration in {RUNNER_RELATIVE_PATH} is empty"
        )
    for root in roots:
        if _widens_to_whole_tree(root):
            raise _blind(
                "members-entry-widens-to-the-whole-tree",
                f"MEMBERS entry {root!r} in {RUNNER_RELATIVE_PATH} widens to the whole tree, or "
                f"escapes the repository altogether: either way it would mark files covered that "
                f"this guard cannot reason about, and report no gap at all"
            )
        if not (repo_root / root).exists():
            raise _blind(
                "members-entry-names-nothing",
                f"MEMBERS entry {root!r} in {RUNNER_RELATIVE_PATH} names nothing in this "
                f"checkout, so the gate iterates a phantom and checks nothing, which reads as "
                f"coverage"
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
            "mypypath-declaration-duplicated",
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
            "manifest-unreadable",
            f"the guard could not read {MANIFEST_RELATIVE_PATH} at {manifest_path} ({error})",
        ) from error
    try:
        return tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise _blind(
            "manifest-unparseable",
            f"{MANIFEST_RELATIVE_PATH} at {manifest_path} does not parse ({error})",
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
        raise _blind(
            "declared-paths-not-a-list",
            f"{described_as} is {value!r}, which is not a list of paths",
        )
    entries: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise _blind(
                "declared-paths-entry-is-not-a-path",
                f"{described_as} carries {item!r}, which is not a path",
            )
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
            "declared-table-absent",
            f"{MANIFEST_RELATIVE_PATH} declares no [{table_name}] table, so {key} is unreadable",
        )
    if key not in section:
        raise _blind("declared-key-absent", f"{described_as} is not declared")
    entries = _string_list(section[key], described_as=described_as)
    if not entries:
        raise _blind("declared-paths-empty", f"{described_as} is empty")
    return entries


def pytest_testpaths(repo_root: Path) -> list[str]:
    """The execution gate's scope, parsed from the manifest pytest reads."""
    testpaths = _declared_paths(
        repo_root, table=("tool", "pytest", "ini_options"), key="testpaths"
    )
    for testpath in testpaths:
        if _widens_to_whole_tree(testpath):
            raise _blind(
                "testpath-widens-to-the-whole-tree",
                f"testpaths entry {testpath!r} in {MANIFEST_RELATIVE_PATH} widens to the whole "
                f"tree, or escapes the repository altogether: either way it would make "
                f"test-shaped files read as covered that this guard cannot reason about, and "
                f"report no execution gap at all"
            )
        if not (repo_root / testpath).is_dir():
            raise _blind(
                "testpath-is-not-a-directory",
                f"testpaths entry {testpath!r} declared in {MANIFEST_RELATIVE_PATH} is not a "
                f"directory in this checkout, so pytest collects nothing there and the execution "
                f"axis is satisfied by an empty tree"
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
        raise _blind(
            "python-files-empty",
            f"{described_as} is empty, so nothing is test-shaped and LEG B is vacuous",
        )
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
            "tracked-python-files-empty",
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
        raise _blind(
            "git-is-unexecutable", f"the guard could not execute git ({error})"
        ) from error
    if completed.returncode != _EXIT_CLEAN:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise _blind(
            "git-command-failed",
            f"git {' '.join(arguments)} failed under {repo_root} with status "
            f"{completed.returncode} ({detail})"
        )
    return completed.stdout.decode("utf-8", errors="surrogateescape")


#: The collector is the expensive input by three orders of magnitude — measured 2026-07-29 on this
#: checkout: **~6.0 s** for one subprocess against **~29 ms** for the fingerprint that keys this
#: memo, and the contract asks for the answer from over a hundred pins (129 s for one file's run,
#: uncached). Keyed on ``(repo_root, fingerprint)`` and NEVER on the root alone: a memo keyed on
#: identity serves a STALE answer to a tree that changed under it, and a stale HEALTHY answer is a
#: false clear — the one failure this instrument may not have. The invalidation is therefore part
#: of the contract, not an optimisation detail.
_COLLECTOR_MEMO: dict[tuple[str, str], frozenset[str]] = {}


def _collector_input_paths(repo_root: Path, testpaths: Sequence[str], tracked: Sequence[str]) -> list[Path]:
    """Every file whose CONTENT can change what the collector answers, in a stable order.

    Three populations, each for a reason read out of pytest's own source rather than guessed:

    * **the gate configuration files** — ``locate_config`` consults the invocation directory and
      its ANCESTORS only, never a subdirectory, so the candidates at ``repo_root`` are the whole
      set that can redirect collection;
    * **every tracked ``.py``** — a test module's content decides whether it contributes items at
      all, and a module it imports decides whether collection even succeeds;
    * **every ``.py`` under a collection root, tracked or not** — pytest collects UNTRACKED files,
      which is exactly why ``scripts/tree_fingerprint.sh`` cannot be reused here: it fingerprints
      the TRACKED tree (index blobs plus the unstaged diff) and by its own stated bound a
      brand-new untracked file does not move it.

    A non-``.py`` file under a collection root is excluded deliberately: pytest's python plugin
    turns ``.py`` files into modules and nothing else, so no other file can become a collected
    item — and hashing 29 MB of build artefacts (``__pycache__`` alone is most of it, and its
    mtimes move DURING a run) would thrash the memo it exists to key.
    """
    paths = {
        repo_root / filename
        for filename in (
            MANIFEST_RELATIVE_PATH,
            CONFTEST_FILENAME,
            *SHADOWING_CONFIGURATION_FILENAMES,
        )
    }
    paths.update(repo_root / relative for relative in tracked)
    for testpath in testpaths:
        for directory, subdirectories, filenames in os.walk(repo_root / testpath):
            subdirectories.sort()
            paths.update(
                Path(directory) / filename
                for filename in filenames
                if filename.endswith(".py")
            )
    return sorted(path for path in paths if path.is_file())


def _collector_input_fingerprint(
    repo_root: Path, testpaths: Sequence[str], tracked: Sequence[str]
) -> str:
    """A digest over the collector's inputs, refusing rather than hashing a partial answer.

    An unreadable input is a REFUSAL and not a skipped entry: a fingerprint computed over part of
    the inputs collides with the healthy one, which is a stale answer wearing a fresh receipt —
    the memo serving the very false clear it was cheap enough to avoid.

    ⚠ **WHICH HALF OF THE MEMO KEY IS LOAD-BEARING, measured rather than assumed.** The paths hashed
    here are ABSOLUTE, so this digest already distinguishes two byte-identical trees at different
    roots — and the ``repo_root`` component of the key is therefore redundant, kept as defence in
    depth. A wrong build blanking that component survived the whole contract, and it survived
    because it is not wrong: the property (no cross-tree collision) lives HERE, and it is pinned
    here. If this digest is ever changed to hash repo-relative paths, the key's root component
    becomes the only thing carrying that property and this note is the trigger to re-pin it.
    """
    digest = hashlib.blake2b()
    for path in _collector_input_paths(repo_root, testpaths, tracked):
        try:
            content = path.read_bytes()
        except OSError as error:
            raise _blind(
                "collector-inputs-unreadable",
                f"the guard could not read the collector input {path} ({error}), so the memo key "
                f"would cover only part of the tree it claims to describe",
            ) from error
        digest.update(str(path).encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return digest.hexdigest()


def collected_test_files(repo_root: Path) -> frozenset[str]:
    """The files pytest ACTUALLY collects items from, measured by a subprocess over ``repo_root``.

    A subprocess and not the live session's items: under ``xdist`` a worker sees only its shard,
    so a live reading would invent a finding for every file another worker holds.

    MEMOISED behind a fingerprint of the collector's inputs — see :data:`_COLLECTOR_MEMO` for the
    measurement that justifies it and the reason the key is not the root alone.

    The child INHERITS this process's environment untouched — see the
    ``inherited-pytest-environment`` bound. Neutralising ``PYTEST_ADDOPTS`` here would mean
    reading the environment outside this repository's one secret-resolution entry point, and an
    allowlist entry there is a DESIGN decision rather than a convenience for this guard. The same
    boundary bounds the memo: an inherited value that CHANGES inside one process moves what the
    collector would answer without moving this key (the ``collector-memoisation`` bound).
    """
    memo_key = (
        str(repo_root.resolve()),
        _collector_input_fingerprint(
            repo_root, pytest_testpaths(repo_root), tracked_python_files(repo_root)
        ),
    )
    memoised = _COLLECTOR_MEMO.get(memo_key)
    if memoised is not None:
        return memoised
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
    try:
        completed = subprocess.run(
            command, cwd=repo_root, capture_output=True, text=True, check=False
        )
    except OSError as error:
        raise _blind(
            "collector-is-unexecutable",
            f"the guard could not run the collector subprocess ({error})",
        ) from error
    if completed.returncode not in _COLLECTOR_TOLERATED_EXIT_CODES:
        raise _blind(
            "collector-exit-code",
            f"the collector subprocess exited {completed.returncode} under {repo_root}, so "
            f"'nothing was collected' would be a failed run wearing a clean answer\n"
            f"{completed.stdout.strip()}\n{completed.stderr.strip()}"
        )
    contributing = frozenset(
        line.split("::", 1)[0].strip() for line in completed.stdout.splitlines() if "::" in line
    )
    if completed.returncode == _EXIT_CLEAN and not contributing:
        raise _blind(
            "collector-output-is-not-the-shape-read",
            f"the collector subprocess exited zero under {repo_root} and named no collected item, "
            f"so its output is not the shape this guard reads"
        )
    _COLLECTOR_MEMO[memo_key] = contributing
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


def shadowing_configuration_files(repo_root: Path) -> list[str]:
    """Configuration files present in ``repo_root`` that OUTRANK the manifest this guard reads.

    **#107 VERBATIM, and the reason this reader exists.** That outage was a widened schema
    declaration that never migrated because the engine no-ops the statement it was written with:
    the guard read a DECLARATION THE TOOL DOES NOT EXECUTE. LEG A has the same shape available to
    it — mypy searches ``mypy.ini``, ``.mypy.ini``, ``pyproject.toml``, ``setup.cfg`` in that
    order and takes the FIRST that parses, so a committed ``mypy.ini`` means every
    ``[tool.mypy]`` key this guard reasons about is being ignored. Measured on trees otherwise
    fully gated: a ``mypy.ini`` carrying ``exclude`` for the only typecheck root, or a global
    ``ignore_errors``, left the guard serving bytes IDENTICAL to a healthy tree.

    **ALLOWLIST THE SAFE, again.** The safe set is one file — the manifest — so this refuses on
    the PRESENCE of any higher-precedence candidate rather than modelling what it contains. That
    is deliberately cruder than parsing them: a model of another tool's precedence rules is a
    second place to be wrong, and refusing is the direction that cannot certify a gate it does not
    read.

    **Why checking ``repo_root`` alone is sufficient, argued rather than assumed.** Both tools
    search upward from the invocation directory and stop at the first accepted candidate; the
    runner invokes mypy from the repository root and the collector runs with ``cwd=repo_root``. So
    once the manifest at the root IS accepted — which the guard guarantees by refusing when its
    modelled tables are absent — no ancestor and no user-level configuration is consulted at all.

    Names AFTER the manifest in each order (``setup.cfg``, ``tox.ini``) are lower precedence and
    therefore harmless under that same guarantee, so refusing on them would be a false positive —
    and a gate that refuses honest code is a gate that gets switched off.
    """
    return [
        f"{filename} is present in this checkout and OUTRANKS {MANIFEST_RELATIVE_PATH} in the "
        f"search order the gate's own tool declares, so every setting this guard read from the "
        f"manifest is being ignored; model {filename} or remove it"
        for filename in SHADOWING_CONFIGURATION_FILENAMES
        if (repo_root / filename).exists()
    ]


def unmodelled_mypy_configuration(repo_root: Path) -> list[str]:
    """Mypy settings this guard cannot model, each named with the two ways out.

    LEG A's verdict is path membership, so any setting that makes a REGISTERED file unchecked IN
    FACT would leave this guard certifying a tree it cannot see. Refusing to mis-model beats
    silently mis-modelling — and the answer is consulted by :func:`classify`, because a reader
    nobody calls is the same shape as a guard nobody runs.

    An ABSENT ``[tool.mypy]`` table is refused too, and for the same reason rather than a
    different one: with no table in the manifest, mypy's search does not stop there — it falls
    through to ``setup.cfg``, then to an ancestor directory, then to
    ``~/.config/mypy/config``. The configuration in force would then be a file outside this
    repository, and LEG A's model would be of a file nobody reads.
    """
    table = _section(_manifest(repo_root), "tool", "mypy")
    if table is None:
        return [
            f"{MANIFEST_RELATIVE_PATH} declares no [tool.mypy] table, so mypy's search does not "
            f"stop at the file this guard models and the configuration in force may be outside "
            f"this repository entirely; declare the table or extend this guard"
        ]
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


class VerdictState(Enum):
    """WHAT a verdict is — and the exit code it means, because the two are ONE thing here.

    The member's VALUE **is** the process exit code. There is deliberately no second table mapping
    state to code, because a second table is a place for the mapping to drift: a build serving
    ``BLIND`` with an exit of zero is not a bug this design can express.

    Three states, and no fourth: the derivation refuses on the first input it cannot read, so
    "some findings, and also blind" describes no world and :class:`IncoherentVerdict` refuses it at
    construction.
    """

    GATED_GROUND = _EXIT_CLEAN
    UNGATED_GROUND = _EXIT_UNGATED_GROUND
    BLIND = _EXIT_BLIND

    @property
    def exit_code(self) -> int:
        """This state, as the number a shell reads. Not a lookup — the member's own value."""
        return int(self.value)


@dataclass(frozen=True)
class Verdict:
    """The SERVED surface: what is ungated, and every input the guard could not derive.

    Blindness is a FIELD and not only an exception, because the seam a consumer reads is the only
    seam where trust lives: a non-empty ``blind_sources`` is never clean, never exits zero, and
    renders bytes a healthy tree cannot produce.

    **EVERY SERVED ANSWER IS DERIVED FROM ONE CLASSIFIER, and that is a structural claim rather
    than a convention.** ``state`` is the only place the two fields become a verdict about the
    tree; ``is_clean`` is an identity test against one of its members, ``exit_code`` is the
    member's own value, and ``render`` dispatches on it. A build in which those three could
    disagree passed 171 pins — serving one finding with ``is_clean=True``, ``exit_code=0`` and the
    clean sentence — which is a guard reporting a clean tree while holding a finding. Making the
    inconsistency UNREPRESENTABLE is cheaper than forbidding each way of expressing it, because
    the ways of expressing it are an open set and the classifier is one function.
    """

    findings: tuple[UngatedFile, ...]
    blind_sources: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.findings and self.blind_sources:
            raise IncoherentVerdict(
                f"a verdict cannot hold {len(self.findings)} finding(s) AND name "
                f"{len(self.blind_sources)} unreadable input(s): the derivation refuses before it "
                f"classifies, so this shape describes no tree. A partial answer looks exactly "
                f"like a cleaner one."
            )

    @property
    def state(self) -> VerdictState:
        """THE classifier. Every served answer below reads this and derives nothing privately.

        Blindness dominates a finding: it is a worse answer, never a better one, and a verdict
        that could not read an input has no standing to report what it found.
        """
        if self.blind_sources:
            return VerdictState.BLIND
        if self.findings:
            return VerdictState.UNGATED_GROUND
        return VerdictState.GATED_GROUND

    @property
    def is_clean(self) -> bool:
        """No ungated ground AND no input the guard failed to read. Both, or it is not clean."""
        return self.state is VerdictState.GATED_GROUND

    @property
    def exit_code(self) -> int:
        """The state, as a number. Blindness dominates because the state ordering says so."""
        return self.state.exit_code

    def render(self) -> str:
        """The bytes a consumer reads: distinct for clean, for findings, and for blind.

        ``match`` over the state rather than a chain of truthiness tests, so a fourth state added
        later is a TYPE ERROR here (mypy reports the missing return) instead of a silent fall
        through to the clean sentence — which is the direction that serves a false clear.
        """
        match self.state:
            case VerdictState.BLIND:
                return "\n\n".join(
                    [
                        "THE GUARD IS BLIND — no verdict about this tree was reached, so the "
                        "absence of findings below means nothing was measured:",
                        *self.blind_sources,
                    ]
                )
            case VerdictState.UNGATED_GROUND:
                return "\n\n".join(finding.message for finding in self.findings)
            case VerdictState.GATED_GROUND:
                return (
                    "GATED GROUND — every tracked module is registered with the type gate, and "
                    "every tracked test-shaped file is one the collector reaches."
                )


# ---------------------------------------------------------------------------
# The derivation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Scopes:
    """Everything the classification needs: all of it derived, none of it assumed."""

    repo_root: Path
    tracked: tuple[str, ...]
    typecheck_roots: tuple[str, ...]
    testpaths: tuple[str, ...]
    test_file_patterns: tuple[str, ...]
    collected: frozenset[str]


def _derive(repo_root: Path) -> _Scopes:
    """Derive every input, refusing on the first one that cannot be read.

    **EVERY READER WHOSE REFUSAL THIS GUARD DECLARES IS CONSULTED HERE**, including the ones whose
    RESULT the classification does not use — ``member_mypypath`` is called for its refusal alone.
    A reader nobody consults is the same shape as a guard nobody runs, and its door is one no
    consumer of the served surface could ever reach: the contract derives the door set from this
    module's source and demands that each one be reachable from a verdict, which is what forced
    this call to exist.

    The ORDER is load-bearing and not incidental:

    1. the tracked-file enumeration, so a wrong root fails as a wrong root rather than as a
       missing manifest;
    2. **configuration PRECEDENCE**, before anything is read out of a configuration file — a file
       the tool reads instead is #107's shape and makes every later read a claim about the wrong
       document;
    3. the runner, then the manifest's declarations, then the mypy model;
    4. the receipts anchor;
    5. the collector LAST, because it is the expensive input and there is no point paying for it
       to describe a tree whose configuration is already unreadable.
    """
    tracked = tracked_python_files(repo_root)

    shadowing = shadowing_configuration_files(repo_root)
    if shadowing:
        raise _blind(
            "gate-configuration-is-shadowed",
            "a gate's configuration is not the file this guard reads, so LEG A and LEG B would be "
            "claims about a document the tool ignores: " + "; ".join(shadowing),
        )

    roots = typecheck_roots(repo_root)
    member_mypypath(repo_root)
    testpaths = pytest_testpaths(repo_root)
    patterns = pytest_test_file_patterns(repo_root)

    unmodelled = unmodelled_mypy_configuration(repo_root)
    if unmodelled:
        raise _blind(
            "mypy-configuration-unmodelled",
            f"the type gate's configuration in {MANIFEST_RELATIVE_PATH} carries settings whose "
            f"effect on which files are checked this guard cannot model, so LEG A would be a "
            f"claim about a scope it cannot see: " + "; ".join(unmodelled),
        )

    if ARCHIVED_RECEIPTS_ROOT not in ruff_excluded_trees(repo_root):
        raise _blind(
            "receipts-root-is-not-lint-excluded",
            f"{ARCHIVED_RECEIPTS_ROOT} is not among the trees {MANIFEST_RELATIVE_PATH} declares "
            f"excluded from linting, so the archived-receipts exemption rests on nothing this "
            f"repository actually calls archived"
        )
    if not any(is_under(path, ARCHIVED_RECEIPTS_ROOT) for path in tracked):
        raise _blind(
            "receipts-class-matches-nothing",
            f"no tracked .py sits under {ARCHIVED_RECEIPTS_ROOT}, so the archived-receipts class "
            f"matches nothing and has been exempting nothing without anyone noticing"
        )

    return _Scopes(
        repo_root=repo_root,
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


def _matches_collection_pattern(pattern: str, absolute_path: PurePosixPath) -> bool:
    """pytest's OWN ``python_files`` matcher, ported from its source rather than approximated.

    **NOT** ``fnmatch.fnmatch(name, pattern)``. pytest matches through
    ``_pytest.pathlib.fnmatch_ex``, which is ``fnmatch`` wrapped in a DECISION: the BASENAME when
    the pattern carries no separator, the WHOLE PATH when it does — and for an absolute path
    against a relative pattern it prepends ``*/`` first, because the paths it is handed are
    absolute. The wrapper IS the semantics.

    **Three independent surveys of this seam recorded ``fnmatch`` as an exact replacement, all
    wrong the same way: none of them opened pytest's matcher.** Measured against the basename-only
    build, six committed test files under separator-bearing patterns came back
    ``guard=False / pytest=True`` — judged not-test-shaped and dropped out of LEG B entirely, which
    is the vanished-input direction and reports nothing at all. Pinned as an ORACLE against the
    installed pytest by the contract, in the same idiom as the ``python_files`` default drift guard.

    The Windows branch of ``fnmatch_ex`` is deliberately NOT ported — see the
    ``collection-pattern-platform`` bound. Every path this guard handles comes from ``git
    ls-files``, which emits POSIX separators.
    """
    if "/" not in pattern:
        candidate = absolute_path.name
    else:
        candidate = str(absolute_path)
        if absolute_path.is_absolute() and not pattern.startswith("/"):
            pattern = f"*/{pattern}"
    return fnmatch.fnmatch(candidate, pattern)


def _is_test_shaped(path: str, patterns: Sequence[str], *, repo_root: Path) -> bool:
    """Would pytest treat this committed file as a test module (or a conftest)?

    Takes ``repo_root`` because pytest's matcher is handed ABSOLUTE paths and branches on it: the
    answer for a separator-bearing pattern differs between ``loremaster/tests/x.py`` and
    ``/checkout/loremaster/tests/x.py``. Reconstructing the path pytest sees is what makes the
    oracle comparison meaningful — the collector runs with ``cwd=repo_root`` and no arguments, so
    that root is pytest's rootdir and the absolute path is exactly this.
    """
    if PurePosixPath(path).name == CONFTEST_FILENAME:
        return True
    absolute = PurePosixPath(str(repo_root.resolve())) / path
    return any(_matches_collection_pattern(pattern, absolute) for pattern in patterns)


def _execution_fate(path: str, *, scopes: _Scopes, exemptions: Sequence[Exemption]) -> Fate:
    """LEG B, where coverage is MEASURED rather than declared.

    A registered file the collector never reaches is ungated ground whatever silenced it. The one
    exception is a conftest, which contributes no collected item by design and is therefore
    bounded by registration — a stated bound, not an oversight.
    """
    if not _is_test_shaped(path, scopes.test_file_patterns, repo_root=scopes.repo_root):
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
