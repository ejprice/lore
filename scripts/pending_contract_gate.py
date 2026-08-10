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

**THE GATE SET IS DERIVED FROM ``scripts/gates.yaml``, AND THAT IS A MECHANISM,
NOT TIDINESS** (sidecar Ruling 7, operator-granted *"Close the gap"*). The first
draft of this module ran TWO of the three gates ``CLAUDE.md`` names and would have
served a verdict reading like a full-gate receipt — finding #306's own lesson
(*"a close-out that reports SOME gates green reads as ALL gates green"*)
reproduced inside the instrument built to pin #306. It surfaced only because
``ruff check .`` turned out to be RED at HEAD too, likewise unrecorded anywhere.
#312's remedy was *"remember to add it to ALL_LEGS in the same diff"* — a hope.
The remedy now is that **there is no ALL_LEGS**: the manifest is canonical, the
leg set derives from it, and a gate reaches the runner in the same edit or the
runner refuses to parse. ``is_deploy_receipt`` requires every manifested gate.

**AND THERE ARE TWO VERDICTS, NAMED APART.** ``--currency`` answers *"is every
CLAIMED gate green-or-owned at HEAD"* (``GREEN`` / ``RED_ADJUDICATED(owner,
trigger)`` / ``RED_ORPHANED``; only orphaned fails). The default run answers
*"may this ship"*. At HEAD today they DISAGREE — packet 39's red is owned, so
currency passes while the deploy receipt does not — which is exactly why
collapsing them would either block the deploy forever or ship over an unowned red.

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

    G=scripts/pending_contract_gate.py

    uv run python $G                      # every manifested gate — the DEPLOY RECEIPT
    uv run python $G --currency           # GATE CURRENCY — required at every close-out
    uv run python $G --legs typecheck,ruff   # a subset (NEVER a deploy receipt)
    uv run python $G --verify-registry    # registry + manifest only; runs no gates
    uv run python $G --derive             # re-derive the registry body
    uv run python $G --registry <p> --manifest <p>   # controls / what-if runs

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

DEFAULT_MANIFEST_PATH = REPO_ROOT / "scripts" / "gates.yaml"

# ⚠ THERE IS NO ``ALL_LEGS`` TUPLE HERE, AND ITS ABSENCE IS THE MECHANISM
# (sidecar Ruling 7.2; grounds #312). This module used to carry
# ``ALL_LEGS = (MYPY_LEG, RUFF_LEG, PYTEST_LEG)`` — a hand-maintained list whose
# first version was MISSING THE RUFF GATE, so the wrapper's receipt read as
# full-gate while a third of the set had never run. #312's own generalisation was
# *"any future gate must be added to ALL_LEGS in the same diff"* — which is a thing
# to REMEMBER, i.e. a hope with a filename.
#
# The leg set is now DERIVED from ``scripts/gates.yaml``. A gate reaches the runner
# in the same edit that adds it to the manifest, or the runner refuses to parse.
# The defect is not fixed; it is UNWRITABLE. Do not reintroduce a constant here.

# The JUNIT placeholder a pytest-shaped command must carry so the reader has a
# document to read.
JUNIT_PLACEHOLDER = "{junit_xml}"

# The registries permitted to OWN a red. A red class with no registry able to own
# it is a NEW adjudication citizen and a DESIGN question (falsifier 7.3), so an
# unknown name here is a parse failure rather than a builder improvisation.
ADJUDICATOR_PENDING_CONTRACTS = "pending-contracts"
ADJUDICATOR_NONE = "none"
ADJUDICATORS = (ADJUDICATOR_PENDING_CONTRACTS, ADJUDICATOR_NONE)

VERDICT_GREEN = "GREEN"
VERDICT_RED_ADJUDICATED = "RED_ADJUDICATED"
VERDICT_RED_ORPHANED = "RED_ORPHANED"
# ⚠ A FOURTH STATE THE RULING DID NOT NAME, ADDED BECAUSE A CONTROL CAUGHT THE
# RENDER OVER-CLAIMING. Ruling 7.3's verdict set is GREEN / RED_ADJUDICATED /
# RED_ORPHANED, and the first build mapped "claimed but not run" onto
# RED_ORPHANED. That FAILS correctly — a gate nobody ran cannot be shown
# green-or-owned — but it SAYS the gate is RED, which is a fact not in evidence.
# A served surface that over-claims is the one thing the trust doctrine forbids
# outright, so the state is named for what it is. It still fails; it just no
# longer lies about why. (Reported to the lead as a deviation from 7.3's set.)
VERDICT_NOT_RUN = "NOT_RUN"
FAILING_VERDICTS = (VERDICT_RED_ORPHANED, VERDICT_NOT_RUN)

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


class ManifestError(RuntimeError):
    """The gate manifest is malformed, vacuous, or names a gate the runner cannot run.

    Raised at PARSE time rather than at run time: a manifest naming a reader that
    does not exist must stop the runner starting, because the alternative is a
    gate that is claimed and silently never executed — #312 exactly.
    """


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

    # RENDERED by the currency mode; never restated in the manifest.
    ANTI_VACUITY_GUARDS = (
        "parsed error count == mypy's own `Found N errors` total",
        "every mypy leg accounts for itself with a Found/Success line",
        "a shellcheck verdict is present",
    )

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

    ANTI_VACUITY_GUARDS = (
        "`No Python files found` is a broken instrument, not a clean repo",
        "exit 0 must carry ruff's own all-clear line",
        "violation count == ruff's own `Found N errors.` total",
    )

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

    ANTI_VACUITY_GUARDS = (
        "zero collected tests is a broken instrument",
        "a failing testcase without a `file` attribute is refused (xunit2 drops it)",
    )

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
# The gate manifest — CANONICAL (sidecar Ruling 7.1)
# ---------------------------------------------------------------------------

# The ALLOWLISTED reader set. A manifest naming anything else fails to PARSE.
# Allowlist the SAFE — the forbidden set of "readers we have not written" is
# unbounded and unenumerable, which is the shape this repo has six receipts
# against.
READERS: dict[str, type] = {
    "typecheck_transcript": MypyOutputReader,
    "ruff": RuffOutputReader,
    "pytest_junit": JUnitReportReader,
}


class GateSpec(BaseModel):
    """One gate: what to run, who reads it, and who may own its reds."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    description: str
    command: tuple[str, ...]
    reader: str
    adjudicated_by: str

    @field_validator("command")
    @classmethod
    def _must_name_a_command(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise ValueError("a gate with no command is not a gate")
        return value

    @field_validator("reader")
    @classmethod
    def _reader_must_be_implemented(cls, value: str) -> str:
        if value not in READERS:
            raise ValueError(
                f"unknown reader {value!r} — the implemented set is "
                f"{sorted(READERS)}. A gate whose output nothing can read would be "
                "CLAIMED and never MEASURED, which is finding #312 exactly."
            )
        return value

    @field_validator("adjudicated_by")
    @classmethod
    def _adjudicator_must_exist(cls, value: str) -> str:
        if value not in ADJUDICATORS:
            raise ValueError(
                f"unknown adjudicator {value!r} — the known set is "
                f"{list(ADJUDICATORS)}. A red class with no registry able to own it "
                "is a NEW adjudication citizen and a DESIGN question, never a "
                "builder improvisation (falsifier 7.3)."
            )
        return value

    @property
    def anti_vacuity_guards(self) -> tuple[str, ...]:
        """The guards this gate's reader actually enforces, DERIVED from the reader.

        Rendered rather than restated in the manifest: prose that describes
        behaviour must be derived from the behaviour, or it becomes a served claim
        no gate checks.
        """
        return tuple(getattr(READERS[self.reader], "ANTI_VACUITY_GUARDS", ()))

    def resolved_command(self, junit_xml: Path | None) -> list[str]:
        """The argv with ``{junit_xml}`` substituted."""
        return [
            part.replace(JUNIT_PLACEHOLDER, str(junit_xml)) if junit_xml else part
            for part in self.command
        ]


class GateManifest(BaseModel):
    """The canonical gate set. CLAUDE.md's gate section is commentary on THIS."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: int
    gates: tuple[GateSpec, ...]

    @field_validator("gates")
    @classmethod
    def _must_be_neither_empty_nor_ambiguous(
        cls, value: tuple[GateSpec, ...]
    ) -> tuple[GateSpec, ...]:
        if not value:
            raise ValueError(
                "a manifest with NO gates makes the currency check vacuously true — "
                "it would answer 'every claimed gate is green' while claiming "
                "nothing. An empty gate set is a BROKEN INSTRUMENT, never a clean "
                "repo."
            )
        seen = Counter(spec.id for spec in value)
        duplicates = sorted(name for name, count in seen.items() if count > 1)
        if duplicates:
            raise ValueError(
                f"duplicate gate id(s) {duplicates} — a verdict keyed on a "
                "non-unique id names two different gates at once"
            )
        for spec in value:
            wants_junit = READERS[spec.reader] is JUnitReportReader
            has_placeholder = any(JUNIT_PLACEHOLDER in part for part in spec.command)
            if wants_junit and not has_placeholder:
                raise ValueError(
                    f"gate {spec.id!r} uses the junit reader but its command never "
                    f"asks for a document ({JUNIT_PLACEHOLDER} absent) — the reader "
                    "would have nothing to read"
                )
        return value

    @classmethod
    def load(cls, path: Path) -> GateManifest:
        try:
            raw = yaml.safe_load(path.read_text())
        except (OSError, yaml.YAMLError) as error:
            raise ManifestError(f"cannot read manifest {path}: {error}") from error
        if not isinstance(raw, dict):
            raise ManifestError(f"manifest {path} is not a mapping")
        try:
            return cls.model_validate(raw)
        except ValidationError as error:
            raise ManifestError(f"manifest {path} is invalid: {error}") from error

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(spec.id for spec in self.gates)

    def gate(self, gate_id: str) -> GateSpec:
        for spec in self.gates:
            if spec.id == gate_id:
                return spec
        raise ManifestError(
            f"no gate {gate_id!r} in the manifest; it names {list(self.ids)}"
        )


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


@dataclass(frozen=True)
class GateCurrency:
    """One gate's CURRENCY verdict — is it green, or owned, or orphaned?

    ⚠ Deliberately carries NO ``is_deploy_receipt`` field. Currency answers *"is
    every claimed gate green-or-owned at HEAD"*; the deploy receipt answers *"may
    this ship"*. They disagree at HEAD today — packet 39's red is OWNED, so
    currency passes while the deploy receipt does not — and a shared field is
    exactly how one verdict starts impersonating the other (Ruling 7.3 rider 3).
    """

    gate_id: str
    verdict: str
    owners: tuple[str, ...]
    orphans: tuple[str, ...]
    registered_count: int

    @property
    def ok(self) -> bool:
        """Red-and-owned is a ruled bound doing its job; red-and-orphaned is the
        disease #306 and #312 both were. ``NOT_RUN`` fails too — currency asks
        *"is EVERY claimed gate green-or-owned"*, and an unmeasured gate cannot
        answer it (that IS #312's half of the failure)."""
        return self.verdict not in FAILING_VERDICTS

    def render(self) -> str:
        if self.verdict == VERDICT_GREEN:
            return f"  {self.gate_id:<12} GREEN"
        if self.verdict == VERDICT_NOT_RUN:
            return f"  {self.gate_id:<12} NOT_RUN — claimed by the manifest, never executed"
        if self.verdict == VERDICT_RED_ADJUDICATED:
            return (
                f"  {self.gate_id:<12} RED_ADJUDICATED — {self.registered_count} "
                f"residual(s), owned by: {' · '.join(self.owners)}"
            )
        return (
            f"  {self.gate_id:<12} RED_ORPHANED — {len(self.orphans)} residual(s) "
            "with NO owner"
        )


def gate_currency(
    *,
    gate: PendingContractGate,
    gate_id: str,
    adjudicated_by: str,
    residuals: Sequence[str],
    expired: Sequence[str],
    registered_count: int = 0,
) -> GateCurrency:
    """Adjudicate ONE gate's result. The invariant is OWNERSHIP, not greenness.

    ``residuals`` are the unregistered lines the partition could not account for;
    ``expired`` are self-destruct findings (an adjudication that has outlived its
    premise). Both make a gate ORPHANED — rider 2: *an expired adjudication is
    RED_ORPHANED, not grandfathered.*

    A gate whose ``adjudicated_by`` is ``none`` cannot be adjudicated at all, so
    ANY red is orphaned regardless of what any registry names. That is the ruff
    case, and it is why this reads the gate's own POLICY rather than asking the
    registry whether it happens to mention the file.
    """
    orphans = tuple(residuals) + tuple(expired)
    if orphans:
        return GateCurrency(
            gate_id=gate_id,
            verdict=VERDICT_RED_ORPHANED,
            owners=(),
            orphans=orphans,
            registered_count=registered_count,
        )
    if registered_count == 0:
        return GateCurrency(
            gate_id=gate_id,
            verdict=VERDICT_GREEN,
            owners=(),
            orphans=(),
            registered_count=0,
        )
    if adjudicated_by == ADJUDICATOR_NONE:
        # Unreachable through the runner (a zero-tolerance gate can register
        # nothing), but stated rather than assumed: if it ever became reachable,
        # silently calling it adjudicated is the failure this function prevents.
        return GateCurrency(
            gate_id=gate_id,
            verdict=VERDICT_RED_ORPHANED,
            owners=(),
            orphans=(
                f"{registered_count} residual(s) on a ZERO-TOLERANCE gate "
                f"({gate_id}) — no registry may own these",
            ),
            registered_count=registered_count,
        )
    owners = tuple(
        f"{bound.id} (owner: {bound.owner.strip()}; trigger: "
        f"{bound.reopen_trigger.strip()})"
        for bound in gate.registry.bounds
    )
    return GateCurrency(
        gate_id=gate_id,
        verdict=VERDICT_RED_ADJUDICATED,
        owners=owners,
        orphans=(),
        registered_count=registered_count,
    )


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
            return ["typecheck    : NOT RUN"], []
        partition = self.partition_mypy(run)
        lines = [
            f"typecheck    : {len(run.errors)} errors · "
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


@dataclass(frozen=True)
class RawGateResult:
    """What a gate's process actually produced, before any reader sees it."""

    spec: GateSpec
    text: str
    exit_code: int


class GateRunner:
    """Invokes the gates the MANIFEST names. It reimplements none of them.

    There is no per-gate method here any more. A gate is executed from its
    manifest ``command``, so adding one is a manifest edit and forgetting one is
    not expressible — the #312 defect (a wrapper silently running a subset) has no
    place left to live.
    """

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def run(self, spec: GateSpec) -> RawGateResult:
        """Run one manifested gate and return its combined transcript + exit code.

        stderr is merged into stdout because ``typecheck.sh`` writes its
        ``typecheck: <leg> FAILED`` lines to fd 2 while mypy writes to fd 1, and
        the leg accounting depends on their ORDER. Capturing them separately
        destroys it.
        """
        needs_junit = READERS[spec.reader] is JUnitReportReader
        with tempfile.TemporaryDirectory() as work_dir:
            junit_xml = Path(work_dir) / "junit.xml" if needs_junit else None
            completed = subprocess.run(
                spec.resolved_command(junit_xml),
                cwd=self.repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            if not needs_junit:
                return RawGateResult(
                    spec=spec, text=completed.stdout, exit_code=completed.returncode
                )
            if completed.returncode not in (
                PYTEST_EXIT_ALL_PASSED,
                PYTEST_EXIT_TESTS_FAILED,
            ):
                raise BrokenInstrumentError(
                    f"gate {spec.id!r} exited {completed.returncode} — that is the "
                    "runner failing to BE a measurement (interrupted / internal "
                    "error / usage error / nothing collected), never a "
                    f"partitionable result. Its output was:\n{completed.stdout[-2000:]}"
                )
            if junit_xml is None or not junit_xml.exists():
                raise BrokenInstrumentError(
                    f"gate {spec.id!r} wrote no junit-xml document — no document, "
                    "no measurement."
                )
            return RawGateResult(
                spec=spec, text=junit_xml.read_text(), exit_code=completed.returncode
            )


def read_gate(raw: RawGateResult) -> MypyRun | RuffRun | PytestRun:
    """Hand a raw result to the reader its manifest entry names."""
    reader = READERS[raw.spec.reader]
    if reader is MypyOutputReader:
        return MypyOutputReader.read(raw.text)
    if reader is RuffOutputReader:
        return RuffOutputReader.read(raw.text, exit_code=raw.exit_code)
    return JUnitReportReader.read(raw.text)


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


def _split_legs(value: str) -> tuple[str, ...]:
    """Split ``--legs``. It is validated against the MANIFEST, not a constant —
    there is no constant, and that is the point (Ruling 7.2)."""
    legs = tuple(part.strip() for part in value.split(",") if part.strip())
    if not legs:
        raise argparse.ArgumentTypeError("--legs needs at least one gate id")
    return legs


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the gates named by scripts/gates.yaml and partition their output "
            "against the pending-contract registry. Deny by default."
        )
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY_PATH,
        help="registry file (default: scripts/pending_contracts.yaml)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="gate manifest — CANONICAL (default: scripts/gates.yaml)",
    )
    parser.add_argument(
        "--repo-root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--legs",
        type=_split_legs,
        default=None,
        help=(
            "which manifested gates to run (default: ALL of them, derived from the "
            "manifest). A subset NEVER yields a deploy receipt."
        ),
    )
    parser.add_argument(
        "--currency",
        action="store_true",
        help=(
            "GATE-CURRENCY MODE: is every claimed gate green-or-owned at HEAD? "
            "Renders GREEN / RED_ADJUDICATED(owner, trigger) / RED_ORPHANED per "
            "gate; ONLY RED_ORPHANED fails. Required at every wave close-out."
        ),
    )
    parser.add_argument(
        "--verify-registry",
        action="store_true",
        help="check the registry and the manifest only; run no gates",
    )
    parser.add_argument(
        "--derive",
        action="store_true",
        help="run the typecheck gate and print a derived registry body for review",
    )
    parser.add_argument(
        "pytest_args",
        nargs="*",
        help="extra arguments forwarded to the pytest gate",
    )
    return parser


def _emit(lines: Iterable[str]) -> None:
    for line in lines:
        print(line)


def _typecheck_gate(manifest: GateManifest) -> GateSpec:
    """The one gate whose reader is the typecheck transcript — DERIVED, not named.

    ``--derive`` needs mypy output specifically. Asking the manifest which gate
    produces it beats hardcoding an id, because the id is the manifest's to choose.
    """
    matches = [
        spec
        for spec in manifest.gates
        if READERS[spec.reader] is MypyOutputReader
    ]
    if len(matches) != 1:
        raise ManifestError(
            f"--derive needs EXACTLY ONE gate using the typecheck reader; the "
            f"manifest has {len(matches)} ({[s.id for s in matches]})"
        )
    return matches[0]


def _run_selected_gates(
    runner: GateRunner, manifest: GateManifest, legs: Sequence[str], pytest_args: Sequence[str]
) -> dict[str, MypyRun | RuffRun | PytestRun]:
    """Execute each selected manifested gate and read it. Keyed by gate id."""
    results: dict[str, MypyRun | RuffRun | PytestRun] = {}
    for gate_id in legs:
        spec = manifest.gate(gate_id)
        if pytest_args and READERS[spec.reader] is JUnitReportReader:
            spec = spec.model_copy(
                update={"command": (*spec.command, *pytest_args)}
            )
        results[gate_id] = read_gate(runner.run(spec))
    return results


def _currencies_for(
    gate: PendingContractGate,
    manifest: GateManifest,
    results: dict[str, MypyRun | RuffRun | PytestRun],
) -> list[GateCurrency]:
    """The per-gate CURRENCY verdicts, DERIVED from the manifest and the run results.

    Extracted from :func:`_render_currency` so the structured verdicts have ONE derivation
    that both the currency renderer here and ``wave_gate.main`` consume — the latter needs
    structured access to the pytest gate's verdict to render it SCOPED-not-GREEN in wave
    mode without re-deciding 'is this gate green-or-owned' (a second copy would be a private
    answer wearing the shared name — CLAUDE.md ONE IMPLEMENTATION).
    """
    expired = gate.registry_liveness_findings()
    currencies: list[GateCurrency] = []
    for spec in manifest.gates:
        result = results.get(spec.id)
        if result is None:
            currencies.append(
                GateCurrency(
                    gate_id=spec.id,
                    verdict=VERDICT_NOT_RUN,
                    owners=(),
                    orphans=(
                        f"gate {spec.id!r} is CLAIMED by the manifest and was NOT "
                        "RUN — a claimed-but-unrun gate is finding #312 exactly. "
                        "This says NOTHING about whether it would pass.",
                    ),
                    registered_count=0,
                )
            )
            continue
        residuals, registered = _residuals_for(gate, spec, result)
        gate_expired = (
            expired if spec.adjudicated_by == ADJUDICATOR_PENDING_CONTRACTS else []
        )
        currencies.append(
            gate_currency(
                gate=gate,
                gate_id=spec.id,
                adjudicated_by=spec.adjudicated_by,
                residuals=residuals,
                expired=gate_expired,
                registered_count=registered,
            )
        )
    return currencies


def _render_currency(
    gate: PendingContractGate,
    manifest: GateManifest,
    results: dict[str, MypyRun | RuffRun | PytestRun],
) -> tuple[list[str], bool]:
    """The close-out's gate enumeration, GENERATED from the manifest.

    #306's rule was *"any close-out claiming gates must enumerate WHICH gates it
    ran and state the verdict of EACH"*. Generating that list from the canonical
    manifest is what makes the omission class unwritable: a gate cannot be left
    out of a receipt it is enumerated into.
    """
    lines = [
        "GATE CURRENCY — is every CLAIMED gate green, or owned?",
        f"  manifest   : {manifest.ids} ({len(manifest.gates)} gates)",
    ]
    currencies = _currencies_for(gate, manifest, results)

    for currency in currencies:
        lines.append(currency.render())
        for orphan in currency.orphans:
            lines.append(f"      ORPHAN: {orphan}")
    ok = all(currency.ok for currency in currencies)
    if ok:
        lines.append("CURRENCY   : PASS — every claimed gate is GREEN or OWNED")
    else:
        unrun = [c.gate_id for c in currencies if c.verdict == VERDICT_NOT_RUN]
        orphaned = [c.gate_id for c in currencies if c.verdict == VERDICT_RED_ORPHANED]
        reasons = []
        if orphaned:
            reasons.append(f"RED with nobody's name on it: {', '.join(orphaned)}")
        if unrun:
            reasons.append(f"claimed but never run: {', '.join(unrun)}")
        lines.append(f"CURRENCY   : FAIL — {' · '.join(reasons)}")
    lines.append(
        "  (this is NOT the deploy receipt: it answers 'is every gate owned', "
        "never 'may this ship')"
    )
    return lines, ok


def _residuals_for(
    gate: PendingContractGate,
    spec: GateSpec,
    result: MypyRun | RuffRun | PytestRun,
) -> tuple[list[str], int]:
    """(unowned residual lines, registered count) for one gate's result."""
    if isinstance(result, MypyRun):
        partition = gate.partition_mypy(result)
        residuals = [
            f"{error.location}: {error.message}" for error in partition.unexpected
        ]
        if result.shellcheck != "OK":
            residuals.append(f"shellcheck reported {result.shellcheck!r}")
        residuals.extend(gate.transcript_self_destruct_findings(result))
        return residuals, len(partition.expected)
    if isinstance(result, RuffRun):
        return list(result.violations), 0
    pytest_partition = gate.partition_pytest(result)
    residuals = [
        f"{outcome.file} :: {outcome.test_id}" for outcome in pytest_partition.unexpected
    ]
    return residuals, len(pytest_partition.expected)


def _dispatch(arguments: argparse.Namespace) -> int:
    """The modes. Kept separate from :func:`main` so error handling lives in ONE
    place rather than being repeated at every early return."""
    runner = GateRunner(arguments.repo_root)
    manifest = GateManifest.load(arguments.manifest)

    legs = arguments.legs if arguments.legs is not None else manifest.ids
    unknown = [leg for leg in legs if leg not in manifest.ids]
    if unknown:
        raise ManifestError(
            f"--legs names {unknown}, which the manifest does not define. "
            f"It names {list(manifest.ids)}."
        )

    if arguments.derive:
        raw = runner.run(_typecheck_gate(manifest))
        print(derive_registry_body(MypyOutputReader.read(raw.text)))
        return 0

    registry = PendingContractRegistry.load(arguments.registry)
    gate = PendingContractGate(registry=registry, repo_root=arguments.repo_root)

    if arguments.verify_registry:
        findings = gate.registry_liveness_findings()
        coverage = gate.liveness_coverage
        _emit(
            [
                f"registry     : {arguments.registry}",
                f"manifest     : {arguments.manifest} → {list(manifest.ids)}",
                *[
                    f"               {spec.id}: {len(spec.anti_vacuity_guards)} "
                    f"anti-vacuity guard(s) — "
                    f"{'; '.join(spec.anti_vacuity_guards)}"
                    for spec in manifest.gates
                ],
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

    results = _run_selected_gates(runner, manifest, legs, arguments.pytest_args)

    if arguments.currency:
        lines, ok = _render_currency(gate, manifest, results)
        print("=" * 72)
        _emit(lines)
        return 0 if ok else 1

    verdict = gate.adjudicate(
        mypy_run=next((r for r in results.values() if isinstance(r, MypyRun)), None),
        pytest_run=next(
            (r for r in results.values() if isinstance(r, PytestRun)), None
        ),
        ruff_run=next((r for r in results.values() if isinstance(r, RuffRun)), None),
    )
    _emit(verdict.failures)
    print("=" * 72)
    _emit(verdict.lines)
    return 0 if verdict.ok else 1


def main(argv: Sequence[str] | None = None) -> int:
    """Exit 0 = accounted for · 1 = a failing verdict · 2 = a BROKEN INSTRUMENT.

    The three are distinguished because they demand different actions: 1 means
    read the residuals, 2 means the measurement itself did not happen.
    """
    arguments = _build_parser().parse_args(argv)
    try:
        return _dispatch(arguments)
    except ManifestError as error:
        print(f"MANIFEST ERROR: {error}", file=sys.stderr)
        return 2
    except RegistryError as error:
        print(f"REGISTRY ERROR: {error}", file=sys.stderr)
        return 2
    except BrokenInstrumentError as error:
        print(f"BROKEN INSTRUMENT: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
