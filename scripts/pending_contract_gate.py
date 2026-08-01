"""pending_contract_gate.py — run the canonical gates and PARTITION their output
against a registry of accepted, pending-build bounds. DENY BY DEFAULT.

**WHY THIS EXISTS (finding #306, ruled by packet 04b-2 wave C's design sidecar
§4, 2026-08-01).** ``./scripts/typecheck.sh`` is RED at HEAD and was red before
wave C touched anything: packet 39's hosted-security contract was committed
deliberately ahead of a build BLOCKED on operator decision **#296**, so its test
files reference symbols that do not exist yet. Measured at ``533d917``:
**198 mypy errors across 12 files**, plus packet 39's 444 designed-RED pins in
the suite.

``CLAUDE.md``'s standing gate is *"zero mypy errors including test trees"* and
the wave's deploy rule is *"full gates green"*. Read literally, 04b-2 could never
deploy until an unrelated packet's operator fork resolved.

**THE RULING, AND WHAT THIS IS NOT.** The gate DEFINITION does not move. There is
no ``type: ignore`` here, no mypy config override, no ``testpaths`` quarantine,
and not one packet-39 file is touched — they are operator-held territory pending
#296, after four INSUFFICIENT adversary passes. The red state is adjudicated as
an ACCEPTED BOUND of the out-of-authority shape, and this repo's standing law is
that **an accepted bound is PINNED, never prose**: *"an unpinned known limitation
is indistinguishable from an unknown one."* This file is that pin.

So this is NOT a narrowing of the gate. It is a SECOND, STRICTER gate on top of
it: the plain gates still run, unchanged, and every line they emit must now be
accounted for against a registry of stated FACTS.

**THE SHAPE, and why it is this shape.** ``CLAUDE.md``'s most expensive lesson is
that *"when you catch yourself enumerating what is FORBIDDEN, you have already
lost — the forbidden set is unbounded; the SAFE set is small and enumerable, so
allowlist the safe."* Six instruments in that table each died to the next name
their author had not thought of. Therefore:

* the registry enumerates the **SAFE** set — the errors we have already
  adjudicated — and **everything else fails loud**. A brand-new defect needs no
  entry in any forbidden list to be caught; it is caught by not being on the
  short list of things we have ruled on;
* the safe set is narrowed **per file AND per symbol**, not per file. A genuinely
  new defect inside a pending-contract file is UNEXPECTED, because the ruling's
  own falsifier (b) demanded per-symbol discrimination wherever mypy's output
  supports it;
* where mypy's output does NOT name a symbol (``no-any-unimported`` names a
  helper whose signature decayed, not a missing name), falsifier (b)'s fallback
  applies: a per-file, per-code allowance with a **declared exact count**. A cap
  is a pin; a bare code allowance is a category, and categories drift.

**AND IT SELF-DESTRUCTS.** A registry that outlives its premise is the stale
exemption this instrument exists to prevent, so five legs force its deletion:

1. a registered file that no longer exists on disk;
2. a registered file that produced **no** mypy errors — the build landed;
3. a registered **symbol** that matched no error line — half a build discharges
   half a claim, and the surviving half must shrink to match;
4. a registered symbol that now **imports successfully** — an INDEPENDENT,
   import-based leg that still fires when the mypy leg was not run at all;
5. an unsymboled-code allowance whose observed count differs from its declared
   one, in EITHER direction.

Two legs for the same property (2/3 read the transcript, 4 reads the interpreter)
because each is blind exactly where the other is strong.

**ALL THREE CANONICAL GATES, and this clause was learned the hard way.**
``CLAUDE.md`` names THREE commit gates — ``scripts/typecheck.sh``,
``uv run ruff check .``, and pytest. **The first draft of this module ran two of
them** and would have served a verdict reading like a full-gate receipt. That is
finding #306's own transferable lesson — *"a close-out that reports SOME gates
green reads as ALL gates green"* — reproduced inside the instrument built to pin
#306, and it surfaced only because ``ruff check .`` turned out to be RED at HEAD
too (2 violations in a committed file), likewise unrecorded anywhere. So
``is_deploy_receipt`` requires all three legs, ENFORCED rather than remembered.
The ruff leg is zero-tolerance: the registry can express a pending CONTRACT, and
a lint violation is never *"a name the build will add later"*.

**ANTI-VACUITY — the guards that stop this from becoming a green rubber stamp.**
*"If step N silently no-opped, would step N+1 still print something that reads as
success?"* Yes, in five places, so all five are checked:

* the parsed error count must equal mypy's own ``Found N errors`` total. If the
  regex stops matching production output, the partition sees nothing unexpected
  and the tail reads green over an unread error set;
* every mypy leg must account for itself with a ``Found``/``Success`` line.
  ``mypy: can't read file`` emits neither, and counting only what parsed reads as
  a pass;
* pytest reporting **zero collected tests** is a broken instrument, never a pass
  — this repo's documented ``no tests ran in 0.00s`` silent green;
* a junit document whose FAILING testcases carry no ``file`` attribute is refused
  outright. pytest's default ``junit_family=xunit2`` DROPS that attribute, and
  the partition would then attribute nothing while looking perfectly healthy —
  measured on a real 8779-test run, where 444 correctly-registered pins rendered
  as UNREGISTERED;
* ``ruff check`` over a path with **no Python files** prints a warning and then
  ``All checks passed!`` and exits 0 — byte-identical to a clean repo. Refused.

USAGE — ``uv run``, never barefoot. This module imports project dependencies
(pydantic, PyYAML), so it carries no shebang and no executable bit, exactly like
``snapshot_gc.py`` and ``token_survey.py``. A ``./scripts/…`` invocation would
die on ``ModuleNotFoundError: pydantic`` — measured, not assumed.

    uv run python scripts/pending_contract_gate.py                # all 3 legs — the deploy receipt
    uv run python scripts/pending_contract_gate.py --legs mypy,ruff  # static legs (NOT a deploy receipt)
    uv run python scripts/pending_contract_gate.py --verify-registry  # cheap: does the registry still hold?
    uv run python scripts/pending_contract_gate.py --derive       # re-derive the registry body
    uv run python scripts/pending_contract_gate.py --registry <path>  # controls / what-if runs

Exit 0 only when every gate line is accounted for AND no self-destruct leg fired.
Exit 1 is a partition failure; exit 2 is a BROKEN INSTRUMENT or a bad registry —
the two are distinguished because they demand different actions.

⚠ **BOUNDS, stated so the next reader meets them deliberately.**

* The registry's **owner** and **re-open trigger** fields cannot be derived from
  anything — they are ruling facts, hand-authored, and this script does not check
  them. Everything else in the registry body (files, symbols, code counts) IS
  derived, by ``--derive``, from a live run.
* Symbol discrimination rests on mypy quoting names in its messages. A future
  mypy whose phrasing drops the quotes would make every claim unmatchable —
  which fails LOUD (self-destruct leg 3), never silently.
* This wraps ``typecheck.sh``; it does not reimplement it. ``MEMBERS`` is a
  registration site ``CLAUDE.md`` names explicitly, and a second copy of it here
  would be exactly the ONE IMPLEMENTATION defect this repo has the most receipts
  against.
"""

from __future__ import annotations

import argparse
import importlib
import re
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY_PATH = REPO_ROOT / "scripts" / "pending_contracts.yaml"
# The canonical gate's path, RELATIVE to whatever repo root the runner is pointed
# at — so a test or a control can drive this against a scratch tree without the
# module's own location deciding which tree gets gated.
TYPECHECK_RUNNER_RELATIVE = Path("scripts") / "typecheck.sh"

MYPY_LEG = "mypy"
PYTEST_LEG = "pytest"
RUFF_LEG = "ruff"
# ``CLAUDE.md`` names exactly THREE commit gates. All three, or it is not a
# full-gate receipt — see the ruff section below for why that sentence is here.
ALL_LEGS = (MYPY_LEG, RUFF_LEG, PYTEST_LEG)

SHELLCHECK_LEG_NAME = "shellcheck"

# pytest's documented exit codes. 0/1 are measurements; anything above is the
# runner failing to BE a measurement, which must never be partitioned.
PYTEST_EXIT_ALL_PASSED = 0
PYTEST_EXIT_TESTS_FAILED = 1

# ⚠ ANCHOR-FREE + ``fullmatch``, NOT ``^…$`` + ``match`` (finding #210 — and this
# file's FIRST DRAFT was an offender, caught by this repo's own AST pin
# ``test_every_anchored_match_use_is_allowlisted``). Python's ``$`` also matches
# immediately BEFORE A TRAILING NEWLINE, so ``.match`` would accept
# ``"…  [attr-defined]\n"`` against a pattern that reads as closed — two different
# strings rendering identically. ``fullmatch`` is intent-revealing and stays correct
# if a later edit touches the anchors.
_ERROR_LINE = re.compile(
    r"(?P<path>[^:\s]+):(?:(?P<line>\d+):)?(?:\d+:)? error: (?P<message>.*)"
)
_ERROR_CODE = re.compile(r"\[(?P<code>[a-z][a-z0-9-]*)\]\s*$")
_FOUND_SUMMARY = re.compile(r"^Found (?P<count>\d+) errors? in \d+ files?\b")
_SUCCESS_SUMMARY = re.compile(r"^Success: no issues found in \d+ source files?\b")
_LEG_VERDICT = re.compile(r"^typecheck: (?P<name>\S+) (?P<verdict>OK|FAILED)\b")

# The message shapes mypy uses to name a missing symbol, most specific first.
# ``--derive`` reads these; the MATCHER below does not, deliberately — matching
# on a quoted-token pair is phrasing-independent, so a new mypy message shape
# costs a derivation, not a false clear.
_SYMBOL_SHAPES = (
    re.compile(r'Module "(?P<owner>[^"]+)" has no attribute "(?P<attribute>[^"]+)"'),
    re.compile(
        r'Module "(?P<owner>[^"]+)" does not explicitly export attribute '
        r'"(?P<attribute>[^"]+)"'
    ),
    re.compile(r'"(?P<owner>[^"]+)" has no attribute "(?P<attribute>[^"]+)"'),
    re.compile(
        r'Unexpected keyword argument "(?P<attribute>[^"]+)" for "(?P<owner>[^"]+)"'
    ),
)


class BrokenInstrumentError(RuntimeError):
    """The gate transcript is not a measurement.

    Raised rather than returned: a broken instrument must never flow into the
    partition, because a partition over unread output reads as a clean tree.
    """


class RegistryError(RuntimeError):
    """The registry is malformed, vacuous, or names a claim it cannot state."""


# ---------------------------------------------------------------------------
# The one symbol-matching policy. Every caller routes here — a second copy would
# be a private answer to "does this error name this symbol?" wearing the shared
# name (CLAUDE.md, ONE IMPLEMENTATION).
# ---------------------------------------------------------------------------


def error_names_symbol(message: str, symbol: str) -> bool:
    """Does ``message`` name ``symbol``, exactly?

    The match is on QUOTED tokens, never substrings: ``Posture`` is a proper
    substring of ``PostureRefusal``, so a naive containment test admits an
    unregistered symbol and cannot tell. A dotted ``owner.attribute`` symbol
    requires BOTH tokens, so the same attribute name on a different owner stays
    unexpected.
    """
    owner, _, attribute = symbol.rpartition(".")
    if owner and f'"{owner}"' not in message:
        return False
    return f'"{attribute}"' in message


def extract_symbol(message: str) -> str | None:
    """The ``owner.attribute`` a mypy message names, or ``None`` if it names no
    symbol at all (``no-any-unimported`` names a decayed signature, not a name).

    Used by ``--derive`` to build a registry body from a live run; the matcher
    above deliberately does not depend on it.
    """
    for shape in _SYMBOL_SHAPES:
        found = shape.search(message)
        if found is not None:
            return f"{found.group('owner')}.{found.group('attribute')}"
    return None


# ---------------------------------------------------------------------------
# Gate transcripts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MypyError:
    """One ``path:line: error: message  [code]`` line."""

    path: str
    line: int | None
    code: str | None
    message: str

    @property
    def location(self) -> str:
        return f"{self.path}:{self.line}" if self.line is not None else self.path


@dataclass(frozen=True)
class MypyRun:
    """A whole ``typecheck.sh`` transcript, verified to BE a measurement."""

    errors: tuple[MypyError, ...]
    declared_total: int
    legs: tuple[tuple[str, str], ...]
    shellcheck: str | None


class MypyOutputReader:
    """Reads ``typecheck.sh``'s combined transcript into a :class:`MypyRun`."""

    @classmethod
    def read(cls, text: str) -> MypyRun:
        errors: list[MypyError] = []
        legs: list[tuple[str, str]] = []
        shellcheck: str | None = None
        declared_total = 0
        pending_summary: int | None = None
        pending_seen = False

        for raw_line in text.splitlines():
            line = raw_line.rstrip()

            found = _FOUND_SUMMARY.match(line)
            if found is not None:
                pending_summary = int(found.group("count"))
                pending_seen = True
                continue
            if _SUCCESS_SUMMARY.match(line) is not None:
                pending_summary = 0
                pending_seen = True
                continue

            verdict_match = _LEG_VERDICT.match(line)
            if verdict_match is not None:
                name = verdict_match.group("name")
                verdict = verdict_match.group("verdict")
                if name == SHELLCHECK_LEG_NAME:
                    shellcheck = verdict
                    continue
                if not pending_seen:
                    raise BrokenInstrumentError(
                        f"typecheck leg {name!r} reported {verdict} with no mypy "
                        "summary line of its own. `mypy: can't read file` emits "
                        "neither `Found N errors` nor `Success:` — this transcript "
                        "is a BROKEN INSTRUMENT, not a clean tree."
                    )
                declared_total += pending_summary or 0
                legs.append((name, verdict))
                pending_summary = None
                pending_seen = False
                continue

            error_match = _ERROR_LINE.fullmatch(line)
            if error_match is not None:
                message = error_match.group("message")
                code_match = _ERROR_CODE.search(message)
                line_number = error_match.group("line")
                errors.append(
                    MypyError(
                        path=error_match.group("path"),
                        line=int(line_number) if line_number is not None else None,
                        code=code_match.group("code") if code_match else None,
                        message=message,
                    )
                )

        if not legs:
            raise BrokenInstrumentError(
                "no `typecheck: <leg> OK|FAILED` line in the transcript — the "
                "runner did not run. An empty transcript is never a pass."
            )
        if shellcheck is None:
            raise BrokenInstrumentError(
                "the shell leg reported no OK/FAILED verdict (it aborts loudly on "
                "a broken file enumeration) — the transcript is incomplete."
            )
        if len(errors) != declared_total:
            raise BrokenInstrumentError(
                f"parsed {len(errors)} error lines but mypy declared "
                f"{declared_total}. The parser and the gate disagree about what "
                "was measured, so the partition below would be over UNREAD "
                "output — which reads as a clean tree. This is a STOP."
            )
        return MypyRun(
            errors=tuple(errors),
            declared_total=declared_total,
            legs=tuple(legs),
            shellcheck=shellcheck,
        )


@dataclass(frozen=True)
class RuffRun:
    """The lint gate's result. ZERO-TOLERANCE: there is nothing to partition."""

    violations: tuple[str, ...]


class RuffOutputReader:
    """Reads ``uv run ruff check .`` — the THIRD canonical gate.

    ⚠ **WHY THIS EXISTS, and it is finding #306 reproduced inside #306's own
    instrument.** The first draft of this wrapper ran mypy and pytest and served
    a verdict that read like a full-gate receipt. ``CLAUDE.md`` names THREE
    commit gates. That is exactly #306's transferable lesson — *"a close-out that
    reports SOME gates green reads as ALL gates green"* — and it was caught only
    because ``ruff check .`` turned out to be RED at HEAD too (2 violations in a
    committed file), which nothing had recorded either.

    **The leg is ZERO-TOLERANCE, and that is a design decision worth overturning
    deliberately rather than inheriting.** The registry can express a pending
    CONTRACT — symbols a build will create, pins designed to be RED until then.
    No such thing exists for a lint violation: a lint error is never *"a name
    the build will add later"*. So ruff must simply be clean, and the registry
    has no say.
    """

    _COUNT = re.compile(r"Found (?P<count>\d+) errors?\.")
    _LOCATION = re.compile(r"-->\s*(?P<location>\S+)")
    _ALL_CLEAR = "All checks passed!"
    _NO_FILES = "No Python files found"

    @classmethod
    def read(cls, text: str, *, exit_code: int) -> RuffRun:
        if cls._NO_FILES in text:
            raise BrokenInstrumentError(
                "ruff reported `No Python files found under the given path(s)` "
                "and then `All checks passed!`, exiting 0 — MEASURED 2026-08-01. "
                "A wrong cwd or a moved tree renders BYTE-IDENTICAL to a clean "
                "repo, so an empty file set is a BROKEN INSTRUMENT, never a pass."
            )
        if exit_code == 0:
            if cls._ALL_CLEAR not in text:
                raise BrokenInstrumentError(
                    "ruff exited 0 without printing its all-clear line. An exit "
                    "code alone is not a measurement — this gate does not lean "
                    "on a third-party tool's exit convention."
                )
            return RuffRun(violations=())
        if exit_code != 1:
            raise BrokenInstrumentError(
                f"ruff exited {exit_code} — that is the runner failing to BE a "
                "measurement, never a partitionable result."
            )

        # ruff renders each violation as a RULE line followed by an `--> path:line:col`
        # line. Pair them rather than counting either alone: a rule line with no
        # location is a summary, and a location with no rule above it cannot exist.
        lines = text.splitlines()
        violations: list[str] = []
        for rule_line, location_line in zip(lines, lines[1:], strict=False):
            located = cls._LOCATION.search(location_line)
            if located is None or cls._LOCATION.search(rule_line) is not None:
                continue
            violations.append(f"{located.group('location')} — {rule_line.strip()}")
        declared = cls._COUNT.search(text)
        if declared is None:
            raise BrokenInstrumentError(
                "ruff reported violations but printed no `Found N errors.` "
                "summary — nothing to cross-check the reader against."
            )
        if len(violations) != int(declared.group("count")):
            raise BrokenInstrumentError(
                f"read {len(violations)} ruff violations but ruff declared "
                f"{declared.group('count')}. The reader and the gate disagree "
                "about what was measured — a silent zero here reads as clean."
            )
        return RuffRun(violations=tuple(violations))


@dataclass(frozen=True)
class PytestOutcome:
    """One failing or erroring test, with the file it lives in."""

    file: str
    test_id: str
    kind: str


@dataclass(frozen=True)
class PytestRun:
    total: int
    passed: int
    outcomes: tuple[PytestOutcome, ...]


class JUnitReportReader:
    """Reads pytest's own ``--junit-xml`` document.

    Structured output from the runner itself, rather than a regex over terminal
    prose: pytest already emits every failing test's FILE, which is precisely the
    field the partition needs, and a short-summary regex would be one more
    natural-language surface no gate checks.
    """

    @classmethod
    def read(cls, xml_text: str) -> PytestRun:
        try:
            root = ElementTree.fromstring(xml_text)
        except ElementTree.ParseError as error:
            raise BrokenInstrumentError(
                f"pytest's junit-xml document did not parse ({error}). No "
                "document means no measurement."
            ) from error

        suites = root.iter("testsuite")
        total = 0
        non_passing = 0
        outcomes: list[PytestOutcome] = []
        for suite in suites:
            total += int(suite.get("tests", "0"))
            non_passing += (
                int(suite.get("failures", "0"))
                + int(suite.get("errors", "0"))
                + int(suite.get("skipped", "0"))
            )
            for case in suite.iter("testcase"):
                for kind in ("failure", "error"):
                    if case.find(kind) is None:
                        continue
                    located = case.get("file")
                    if not located:
                        raise BrokenInstrumentError(
                            "a failing testcase carries no `file` attribute "
                            f"({case.get('classname', '')}::{case.get('name', '')}). "
                            "pytest's DEFAULT junit family (xunit2) drops `file`, "
                            "so the partition would have nothing to attribute a "
                            "failure to and every registered pin would render as "
                            "UNREGISTERED. Re-run with `-o junit_family=xunit1`. "
                            "Refusing to partition an unattributable document."
                        )
                    outcomes.append(
                        PytestOutcome(
                            file=located,
                            test_id=f"{case.get('classname', '')}::{case.get('name', '')}",
                            kind=kind,
                        )
                    )
                    break

        if total == 0:
            raise BrokenInstrumentError(
                "pytest collected ZERO tests. `no tests ran in 0.00s` is this "
                "repo's documented silent green — a green claim requires a "
                "passed-COUNT, so zero collected is a BROKEN INSTRUMENT."
            )
        return PytestRun(
            total=total, passed=total - non_passing, outcomes=tuple(outcomes)
        )


# ---------------------------------------------------------------------------
# The registry — a validated boundary (pydantic, extra="forbid")
# ---------------------------------------------------------------------------


class UnsymboledCodeAllowance(BaseModel):
    """A per-file, per-code residual for errors that name no symbol.

    Falsifier (b) of the ruling: where per-symbol discrimination is unbuildable
    from mypy's output, fall back to file-exact + code-exact **with the residual
    stated**. ``count`` is what makes it a pin rather than a category.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    count: int
    reason: str

    @field_validator("count")
    @classmethod
    def _must_be_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("an allowance of zero errors is not an allowance")
        return value


class PendingFile(BaseModel):
    """One file whose gate output is adjudicated as an accepted bound."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    missing_symbols: tuple[str, ...] = ()
    unsymboled_codes: tuple[UnsymboledCodeAllowance, ...] = ()

    def admits(self, error: MypyError) -> bool:
        if any(error_names_symbol(error.message, s) for s in self.missing_symbols):
            return True
        return any(allowance.code == error.code for allowance in self.unsymboled_codes)


class PendingBound(BaseModel):
    """A group of files sharing ONE owner and ONE re-open trigger.

    Grouped rather than repeated per file: the owner and the trigger are the same
    fact eleven times over, and eleven copies of a fact are eleven places for it
    to drift.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    owner: str
    reopen_trigger: str
    ruling: str
    rationale: str
    files: tuple[PendingFile, ...]

    @field_validator("files")
    @classmethod
    def _must_name_files(cls, value: tuple[PendingFile, ...]) -> tuple[PendingFile, ...]:
        if not value:
            raise ValueError(
                "a bound naming no files is a disclaimer, not a fact — "
                "delete it or name what it covers"
            )
        return value


class PendingContractRegistry(BaseModel):
    """The whole registry: the accepted bounds, as FACTS rather than prose."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: int
    bounds: tuple[PendingBound, ...]

    @field_validator("bounds")
    @classmethod
    def _entries_must_state_a_claim(
        cls, value: tuple[PendingBound, ...]
    ) -> tuple[PendingBound, ...]:
        for bound in value:
            for entry in bound.files:
                if not entry.missing_symbols and not entry.unsymboled_codes:
                    raise ValueError(
                        f"{entry.path} names neither a missing symbol nor a code "
                        "allowance — that degenerates to file-only matching, "
                        "which waves through a genuinely NEW defect in the file"
                    )
        return value

    @classmethod
    def load(cls, path: Path) -> PendingContractRegistry:
        try:
            raw = yaml.safe_load(path.read_text())
        except (OSError, yaml.YAMLError) as error:
            raise RegistryError(f"cannot read registry {path}: {error}") from error
        if not isinstance(raw, dict):
            raise RegistryError(f"registry {path} is not a mapping")
        try:
            return cls.model_validate(raw)
        except ValidationError as error:
            raise RegistryError(f"registry {path} is invalid: {error}") from error

    @property
    def registered_paths(self) -> set[str]:
        return {entry.path for bound in self.bounds for entry in bound.files}

    @property
    def symbol_count(self) -> int:
        return sum(
            len(entry.missing_symbols) for bound in self.bounds for entry in bound.files
        )

    def entry_for(self, path: str) -> tuple[PendingBound, PendingFile] | None:
        for bound in self.bounds:
            for entry in bound.files:
                if entry.path == path:
                    return bound, entry
        return None


# ---------------------------------------------------------------------------
# Adjudication
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Partition:
    expected: list[MypyError] = field(default_factory=list)
    unexpected: list[MypyError] = field(default_factory=list)


@dataclass(frozen=True)
class PytestPartition:
    expected: list[PytestOutcome] = field(default_factory=list)
    unexpected: list[PytestOutcome] = field(default_factory=list)


@dataclass(frozen=True)
class LivenessCoverage:
    """How much of the registry the import-based leg could actually check.

    Coverage is a CHECKED VARIABLE, not an assumption: a runtime guard is an
    invariant only over what it actually reaches, so the unchecked count is
    served rather than rounded away.
    """

    checked: int
    unchecked: int
    unchecked_symbols: tuple[str, ...]

    @property
    def unchecked_render(self) -> str:
        """The unchecked claims, DEDUPED with multiplicity.

        One symbol claimed by three files is three CLAIMS (so ``unchecked``
        stays 3 and the coverage arithmetic still closes) but one NAME — and a
        list repeating a name three times reads as a rendering bug to a consumer,
        which is a trust cost for no information.
        """
        counts = Counter(self.unchecked_symbols)
        return ", ".join(
            name if count == 1 else f"{name} \u00d7{count}"
            for name, count in sorted(counts.items())
        )


@dataclass(frozen=True)
class Verdict:
    ok: bool
    lines: tuple[str, ...]
    failures: tuple[str, ...]
    is_deploy_receipt: bool


class PendingContractGate:
    """Partitions gate output against the registry, DENY BY DEFAULT."""

    def __init__(self, registry: PendingContractRegistry, repo_root: Path) -> None:
        self.registry = registry
        self.repo_root = repo_root
        self._liveness: tuple[list[str], LivenessCoverage] | None = None

    # -- partitions --------------------------------------------------------

    def partition_mypy(self, run: MypyRun) -> Partition:
        partition = Partition()
        for error in run.errors:
            found = self.registry.entry_for(error.path)
            if found is not None and found[1].admits(error):
                partition.expected.append(error)
            else:
                partition.unexpected.append(error)
        return partition

    def partition_pytest(self, run: PytestRun) -> PytestPartition:
        partition = PytestPartition()
        registered = self.registry.registered_paths
        for outcome in run.outcomes:
            if outcome.file in registered:
                partition.expected.append(outcome)
            else:
                partition.unexpected.append(outcome)
        return partition

    # -- self-destruction ---------------------------------------------------

    def registry_liveness_findings(self) -> list[str]:
        """Leg 4: does a registered symbol now RESOLVE?

        Independent of any gate transcript — it asks the interpreter. A symbol
        whose owner cannot be imported is reported as UNCHECKED (see
        :attr:`liveness_coverage`), never silently assumed absent.
        """
        return self._compute_liveness()[0]

    @property
    def liveness_coverage(self) -> LivenessCoverage:
        return self._compute_liveness()[1]

    def _compute_liveness(self) -> tuple[list[str], LivenessCoverage]:
        if self._liveness is not None:
            return self._liveness
        findings: list[str] = []
        checked = 0
        unchecked: list[str] = []
        for bound in self.registry.bounds:
            for entry in bound.files:
                for symbol in entry.missing_symbols:
                    owner, _, attribute = symbol.rpartition(".")
                    module = self._import_or_none(owner)
                    if module is None:
                        unchecked.append(symbol)
                        continue
                    checked += 1
                    if hasattr(module, attribute):
                        findings.append(
                            f"SELF-DESTRUCT: registered symbol {symbol!r} "
                            f"({entry.path}, bound {bound.id!r}) now RESOLVES — the "
                            "bound is discharged. DELETE the entry with the fix."
                        )
        coverage = LivenessCoverage(
            checked=checked,
            unchecked=len(unchecked),
            unchecked_symbols=tuple(unchecked),
        )
        self._liveness = (findings, coverage)
        return self._liveness

    @staticmethod
    def _import_or_none(dotted: str) -> object | None:
        if not dotted:
            return None
        try:
            return importlib.import_module(dotted)
        except Exception:  # noqa: BLE001 - any import failure is "uncheckable"
            return None

    def transcript_self_destruct_findings(self, run: MypyRun) -> list[str]:
        """Legs 1-3 and 5: the registry read against a live mypy transcript."""
        findings: list[str] = []
        errors_by_path: dict[str, list[MypyError]] = {}
        for error in run.errors:
            errors_by_path.setdefault(error.path, []).append(error)

        for bound in self.registry.bounds:
            for entry in bound.files:
                if not (self.repo_root / entry.path).exists():
                    findings.append(
                        f"SELF-DESTRUCT: registered file {entry.path!r} (bound "
                        f"{bound.id!r}) does not exist — DELETE its registry entry."
                    )
                observed = errors_by_path.get(entry.path, [])
                if not observed:
                    findings.append(
                        f"SELF-DESTRUCT: registered file {entry.path!r} (bound "
                        f"{bound.id!r}) produced NO mypy errors — the bound is "
                        "discharged. DELETE its registry entry with the fix."
                    )
                    continue
                for symbol in entry.missing_symbols:
                    if not any(
                        error_names_symbol(error.message, symbol) for error in observed
                    ):
                        findings.append(
                            f"SELF-DESTRUCT: registered symbol {symbol!r} "
                            f"({entry.path}) matched NO error line — the claim is "
                            "discharged. DELETE the symbol from the registry."
                        )
                observed_codes = Counter(
                    error.code for error in observed if error.code is not None
                )
                for allowance in entry.unsymboled_codes:
                    unsymboled_seen = sum(
                        1
                        for error in observed
                        if error.code == allowance.code
                        and not any(
                            error_names_symbol(error.message, symbol)
                            for symbol in entry.missing_symbols
                        )
                    )
                    if unsymboled_seen != allowance.count:
                        findings.append(
                            f"SELF-DESTRUCT: {entry.path} declares {allowance.count} "
                            f"unsymboled {allowance.code!r} error(s); {unsymboled_seen} "
                            "observed. An allowance is a PIN, not a category — "
                            "re-adjudicate and update the count with the change. "
                            f"(all codes seen in this file: {dict(observed_codes)})"
                        )
        return findings

    # -- per-leg readers ----------------------------------------------------
    #
    # One method per gate, each returning (served lines, failures). Split out of
    # ``adjudicate`` so adding the ruff leg could not push the verdict method past
    # the branch ceiling — and so a FOURTH gate is a new method rather than
    # another elif in a function nobody wants to re-read.

    def _read_mypy_leg(self, run: MypyRun | None) -> tuple[list[str], list[str]]:
        if run is None:
            return ["mypy         : NOT RUN"], []
        partition = self.partition_mypy(run)
        lines = [
            f"mypy         : {len(run.errors)} errors · "
            f"{len(partition.expected)} registered · "
            f"{len(partition.unexpected)} UNREGISTERED"
        ]
        failures = [
            f"UNREGISTERED mypy error: {error.location}: {error.message}"
            for error in partition.unexpected
        ]
        if run.shellcheck != "OK":
            failures.append(
                f"shellcheck leg reported {run.shellcheck!r} — a shell defect is "
                "neither a registered symbol nor a registered test file, so it can "
                "only ever be a loud failure."
            )
        failures.extend(self.transcript_self_destruct_findings(run))
        return lines, failures

    def _read_ruff_leg(self, run: RuffRun | None) -> tuple[list[str], list[str]]:
        if run is None:
            return ["ruff         : NOT RUN"], []
        lines = [
            f"ruff         : {len(run.violations)} violation(s) "
            "(zero-tolerance — the registry has no say over lint)"
        ]
        return lines, [f"ruff violation: {v}" for v in run.violations]

    def _read_pytest_leg(self, run: PytestRun | None) -> tuple[list[str], list[str]]:
        if run is None:
            return ["pytest       : NOT RUN"], []
        partition = self.partition_pytest(run)
        lines = [
            f"pytest       : {run.passed} passed · "
            f"{len(partition.expected)} failed registered · "
            f"{len(partition.unexpected)} failed UNREGISTERED"
        ]
        failures = [
            f"UNREGISTERED pytest {outcome.kind}: "
            f"{outcome.file or '<no file>'} :: {outcome.test_id}"
            for outcome in partition.unexpected
        ]
        return lines, failures

    # -- the served verdict -------------------------------------------------

    def adjudicate(
        self,
        mypy_run: MypyRun | None,
        pytest_run: PytestRun | None,
        ruff_run: RuffRun | None = None,
    ) -> Verdict:
        failures: list[str] = []
        lines: list[str] = []

        bound_summary = " · ".join(
            f"{bound.id} ({len(bound.files)} files, "
            f"{sum(len(e.missing_symbols) for e in bound.files)} symbols)"
            for bound in self.registry.bounds
        )
        lines.append(f"registry     : {bound_summary or 'EMPTY'}")

        for leg_lines, leg_failures in (
            self._read_mypy_leg(mypy_run),
            self._read_ruff_leg(ruff_run),
            self._read_pytest_leg(pytest_run),
        ):
            lines.extend(leg_lines)
            failures.extend(leg_failures)

        failures.extend(self.registry_liveness_findings())
        coverage = self.liveness_coverage
        lines.append(
            f"self-destruct: {coverage.checked} symbol(s) import-checked absent · "
            f"{coverage.unchecked} UNCHECKED (owner not importable)"
        )
        if coverage.unchecked_symbols:
            lines.append(f"               unchecked: {coverage.unchecked_render}")

        # ALL THREE gates, per CLAUDE.md. Two-of-three rendering as a full
        # receipt IS finding #306's defect; it is enforced here, not remembered.
        is_full = (
            mypy_run is not None and pytest_run is not None and ruff_run is not None
        )
        ok = not failures
        if ok and is_full:
            lines.append(
                "VERDICT      : PASS — deploy receipt (mypy + ruff + pytest all run)"
            )
        elif ok:
            lines.append(
                "VERDICT      : PARTIAL-PASS — NOT a deploy receipt; a leg was "
                "not run, so this cannot discharge \"full gates green\"."
            )
        else:
            lines.append(f"VERDICT      : FAIL — {len(failures)} unaccounted item(s)")
        return Verdict(
            ok=ok,
            lines=tuple(lines),
            failures=tuple(failures),
            is_deploy_receipt=ok and is_full,
        )


# ---------------------------------------------------------------------------
# Running the real gates
# ---------------------------------------------------------------------------


class GateRunner:
    """Invokes the canonical gates. It does not reimplement them."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def run_mypy_leg(self) -> str:
        """Run ``scripts/typecheck.sh`` and return its combined transcript.

        stderr is merged into stdout so the ``typecheck: <leg> FAILED`` lines
        (which the runner writes to fd 2) stay in order relative to mypy's own
        output — the ordering the leg accounting depends on.
        """
        completed = subprocess.run(
            [str(self.repo_root / TYPECHECK_RUNNER_RELATIVE)],
            cwd=self.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return completed.stdout

    def run_ruff_leg(self) -> tuple[str, int]:
        """Run the lint gate exactly as ``CLAUDE.md`` names it."""
        completed = subprocess.run(
            ["uv", "run", "ruff", "check", "."],
            cwd=self.repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return completed.stdout, completed.returncode

    def run_pytest_leg(self, extra_args: Sequence[str]) -> str:
        """Run the suite and return its junit-xml document."""
        with tempfile.TemporaryDirectory() as work_dir:
            report = Path(work_dir) / "junit.xml"
            command = [
                "uv",
                "run",
                "pytest",
                "-q",
                "-n",
                "auto",
                # ⚠ `junit_family=xunit1` IS LOAD-BEARING, and this cost a full
                # 7-minute suite run to find. pytest's DEFAULT family is xunit2,
                # whose `_base` testcase attribute set is exactly
                # ``["classname", "name"]`` — `file` and `line` live in
                # `_base_legacy` and are FILTERED OUT (read in the installed
                # `_pytest/junitxml.py`: `record_testreport` sets `file`, and the
                # family then drops it). Under the default, every failure arrives
                # with NO file, so the partition cannot attribute ANY of them and
                # 444 correctly-registered pins render as unregistered.
                # Nothing about the run looks wrong; the tail just says the wrong
                # number. The guard in JUnitReportReader refuses that document
                # outright rather than partitioning it, so this flag cannot be
                # silently lost.
                "-o",
                "junit_family=xunit1",
                f"--junit-xml={report}",
                *extra_args,
            ]
            completed = subprocess.run(
                command, cwd=self.repo_root, text=True, check=False
            )
            if completed.returncode not in (
                PYTEST_EXIT_ALL_PASSED,
                PYTEST_EXIT_TESTS_FAILED,
            ):
                raise BrokenInstrumentError(
                    f"pytest exited {completed.returncode} — that is the runner "
                    "failing to BE a measurement (interrupted / internal error / "
                    "usage error / nothing collected), never a partitionable "
                    "result."
                )
            if not report.exists():
                raise BrokenInstrumentError(
                    "pytest wrote no junit-xml document — no document, no "
                    "measurement."
                )
            return report.read_text()


# ---------------------------------------------------------------------------
# Derivation — the registry body is DERIVED, never hand-listed
# ---------------------------------------------------------------------------


def derive_registry_body(run: MypyRun) -> str:
    """Render a registry body from a live transcript, as YAML.

    What this DERIVES: the file set, the per-file missing-symbol set, and the
    per-file unsymboled-code counts. What it CANNOT derive, and leaves as
    ``TODO`` for a human ruling: which bound a file belongs to, its owner, its
    re-open trigger, and the ruling that accepted it. Those are adjudications,
    not measurements, and a script that invented them would be manufacturing
    authority.
    """
    by_path: dict[str, list[MypyError]] = {}
    for error in run.errors:
        by_path.setdefault(error.path, []).append(error)

    entries: list[dict[str, object]] = []
    for path in sorted(by_path):
        symbols = sorted(
            {
                symbol
                for error in by_path[path]
                if (symbol := extract_symbol(error.message)) is not None
            }
        )
        unsymboled = Counter(
            error.code or "<no-code>"
            for error in by_path[path]
            if extract_symbol(error.message) is None
        )
        entry: dict[str, object] = {"path": path, "missing_symbols": symbols}
        if unsymboled:
            entry["unsymboled_codes"] = [
                {
                    "code": code,
                    "count": count,
                    "reason": "TODO — why this code names no symbol here",
                }
                for code, count in sorted(unsymboled.items())
            ]
        entries.append(entry)

    skeleton = {
        "version": 1,
        "bounds": [
            {
                "id": "TODO-bound-id",
                "owner": "TODO — the packet that owns the closure",
                "reopen_trigger": "TODO — the named decision point",
                "ruling": "TODO — the finding / receipt path that accepted it",
                "rationale": "TODO — why this is out-of-authority, not unfixed",
                "files": entries,
            }
        ],
    }
    return yaml.safe_dump(skeleton, sort_keys=False, width=88, allow_unicode=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_legs(value: str) -> tuple[str, ...]:
    legs = tuple(part.strip() for part in value.split(",") if part.strip())
    unknown = [leg for leg in legs if leg not in ALL_LEGS]
    if unknown or not legs:
        raise argparse.ArgumentTypeError(
            f"--legs takes a comma-separated subset of {','.join(ALL_LEGS)}"
        )
    return legs


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the canonical gates and partition their output against the "
            "pending-contract registry. Deny by default."
        )
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY_PATH,
        help="registry file (default: scripts/pending_contracts.yaml)",
    )
    parser.add_argument(
        "--repo-root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--legs",
        type=_parse_legs,
        default=ALL_LEGS,
        help=(
            "which gates to run (default: both). A subset NEVER yields a deploy "
            "receipt — it is for controls and scoped checks."
        ),
    )
    parser.add_argument(
        "--verify-registry",
        action="store_true",
        help="check the registry against the interpreter only; run no gates",
    )
    parser.add_argument(
        "--derive",
        action="store_true",
        help="run the mypy leg and print a derived registry body for review",
    )
    parser.add_argument(
        "pytest_args",
        nargs="*",
        help="extra arguments forwarded to pytest",
    )
    return parser


def _emit(lines: Iterable[str]) -> None:
    for line in lines:
        print(line)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _build_parser().parse_args(argv)
    runner = GateRunner(arguments.repo_root)

    if arguments.derive:
        try:
            print(derive_registry_body(MypyOutputReader.read(runner.run_mypy_leg())))
        except BrokenInstrumentError as error:
            print(f"BROKEN INSTRUMENT: {error}", file=sys.stderr)
            return 2
        return 0

    try:
        registry = PendingContractRegistry.load(arguments.registry)
    except RegistryError as error:
        print(f"REGISTRY ERROR: {error}", file=sys.stderr)
        return 2

    gate = PendingContractGate(registry=registry, repo_root=arguments.repo_root)

    if arguments.verify_registry:
        findings = gate.registry_liveness_findings()
        coverage = gate.liveness_coverage
        _emit(
            [
                f"registry     : {arguments.registry}",
                f"self-destruct: {coverage.checked} import-checked absent · "
                f"{coverage.unchecked} UNCHECKED (owner not importable)",
                *(
                    [f"               unchecked: {coverage.unchecked_render}"]
                    if coverage.unchecked_symbols
                    else []
                ),
                *findings,
            ]
        )
        return 1 if findings else 0

    mypy_run: MypyRun | None = None
    pytest_run: PytestRun | None = None
    ruff_run: RuffRun | None = None
    try:
        if MYPY_LEG in arguments.legs:
            mypy_run = MypyOutputReader.read(runner.run_mypy_leg())
        if RUFF_LEG in arguments.legs:
            ruff_text, ruff_exit = runner.run_ruff_leg()
            ruff_run = RuffOutputReader.read(ruff_text, exit_code=ruff_exit)
        if PYTEST_LEG in arguments.legs:
            pytest_run = JUnitReportReader.read(
                runner.run_pytest_leg(arguments.pytest_args)
            )
    except BrokenInstrumentError as error:
        print(f"BROKEN INSTRUMENT: {error}", file=sys.stderr)
        return 2

    verdict = gate.adjudicate(
        mypy_run=mypy_run, pytest_run=pytest_run, ruff_run=ruff_run
    )
    _emit(verdict.failures)
    print("=" * 72)
    _emit(verdict.lines)
    return 0 if verdict.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
