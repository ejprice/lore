"""Contract for ``scripts/pending_contract_gate.py`` (finding #306).

**THE BOUND THIS EXISTS TO PIN.** ``./scripts/typecheck.sh`` is RED at HEAD, and
was RED before packet 04b-2 wave C touched anything: packet 39's hosted-security
contract was committed deliberately ahead of a build that is BLOCKED on operator
decision **#296**, so every one of its test files references symbols that do not
exist yet. ``CLAUDE.md``'s standing gate is *"zero mypy errors including test
trees"*, and the wave's deploy rule is *"full gates green"* — so read literally,
04b-2 can never deploy until an unrelated packet's operator fork resolves.

The ruling (``docs/plans/v2/receipts/`` — the wave-C design sidecar's §4, mirrored
into finding #306's body) is that **the gate definition does not move**. No
``type: ignore``, no mypy config override, no ``testpaths`` quarantine, and zero
packet-39 files touched. The red state is an ACCEPTED BOUND of the
out-of-authority shape, and per standing law an accepted bound is **PINNED, never
prose**. This module is that pin's contract.

⚠ **WHAT WRONG BUILD WOULD STILL PASS THIS?** — asked of every fixture here,
because a wrapper is exactly the shape that passes a green tree while proving
nothing. The discriminating cases, each with a test that fails without it:

1. **File-only matching.** A wrapper that admits any error in a registered file
   waves through a genuinely NEW defect in that file. Pinned by
   ``test_registered_file_with_unregistered_symbol_is_unexpected``.
2. **Substring symbol matching.** ``FixturePlaceholder`` is a substring of
   ``FixturePlaceholderRefusal``; a naive ``in`` test admits an unregistered symbol.
   Pinned by ``test_symbol_match_is_quoted_exact_not_substring``.
3. **No count cross-check.** If the error regex silently stops matching, a
   wrapper reports *zero unexpected errors* and exits 0 — a false clear wearing
   a green tail. Pinned by ``test_error_line_count_must_equal_mypys_own_total``.
4. **A leg that never ran.** ``mypy: can't read file`` emits no summary line at
   all; counting only what parsed reads as a pass. Pinned by
   ``test_leg_without_a_verdict_line_is_a_broken_instrument``.
5. **No self-destruct.** A registry that outlives its premise is the stale
   exemption this whole instrument exists to prevent. Pinned by the four
   ``test_self_destruct_*`` cases — file gone, file green, symbol green, symbol
   now importable.
6. **Vacuous pytest.** ``no tests ran`` behind a pipe is this repo's documented
   silent-green. Pinned by ``test_zero_collected_tests_is_a_broken_instrument``.

⚠ **EVERY FIXTURE HERE IS CANNED TEXT UNDER ``tmp_path``.** Nothing in this
module shells out to the real gates or reads the real registry: a contract that
depended on the live tree's error count would go red every time an unrelated
packet landed, and would be asserting the WEATHER rather than the INSTRUMENT.
The real-tree receipts live in the builder's report, not here.

The canned mypy text is transcribed from a REAL ``./scripts/typecheck.sh`` run at
``533d917`` (2026-08-01), not invented — a synthetic message shape is how a
parser passes its tests and misses production output.
"""

from __future__ import annotations

import os
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pending_contract_gate import (  # noqa: E402
    BrokenInstrumentError,
    JUnitReportReader,
    MypyOutputReader,
    MypyRun,
    PendingContractGate,
    PendingContractRegistry,
    RegistryError,
    RuffOutputReader,
)

# --------------------------------------------------------------------------
# Canned gate output — real shapes, transcribed from `533d917`.
# --------------------------------------------------------------------------
#
# ⚠ FIXTURE SYMBOL MUST NEVER RESOLVE (builder-39-w23, 2026-08-22). The example
# "missing symbol" the registry fixtures below register (``lorerunes.FixturePlaceholder``)
# MUST be a name no real member ever exports — the gate's liveness check imports the
# owner module and ``hasattr``s the attribute (pending_contract_gate.py:_compute_liveness),
# and a symbol that RESOLVES flips every "healthy verdict" fixture to a SELF-DESTRUCT. The
# original fixtures used ``lorerunes.Posture`` as a forward-reference placeholder; packet 39
# wave 2/3 BUILT ``lorerunes.Posture``, so it began resolving and reddened 4 self-tests.
# Use a permanently-synthetic name (``FixturePlaceholder``), never a real or planned symbol.
_REGISTERED_FILE = "lorerunes/tests/test_posture.py"
_OTHER_REGISTERED_FILE = "loremaster/tests/test_allowlist_roster.py"
_UNREGISTERED_FILE = "loremaster/tests/test_search.py"


def _mypy_output(error_lines: list[str], *, extra_legs: str = "") -> str:
    """A full ``typecheck.sh`` transcript wrapping ``error_lines``.

    The summary total is DERIVED from the lines passed in, so a fixture cannot
    accidentally encode the disagreement that :func:`test_error_line_count_must_
    equal_mypys_own_total` exists to detect — that test builds its own mismatch
    deliberately.
    """
    body = "\n".join(error_lines)
    if error_lines:
        summary = (
            f"Found {len(error_lines)} errors in 1 file (checked 180 source files)\n"
            "typecheck: loremaster FAILED"
        )
    else:
        summary = "Success: no issues found in 180 source files\ntypecheck: loremaster OK"
    return (
        f"{body}\n{summary}\n"
        f"{extra_legs}"
        "typecheck: shellcheck OK (7 tracked .sh)\n"
    )


def _attr_error(path: str, line: int, owner: str, attribute: str) -> str:
    return (
        f'{path}:{line}: error: Module "{owner}" has no attribute '
        f'"{attribute}"  [attr-defined]'
    )


# --------------------------------------------------------------------------
# Registry fixtures
# --------------------------------------------------------------------------

_REGISTRY_YAML = textwrap.dedent(
    f"""\
    version: 1
    bounds:
      - id: packet-39-pending-build
        owner: "packet 39 — hosted-security contract"
        reopen_trigger: "operator decision #296, or packet 39's build start"
        ruling: "finding #306"
        rationale: "contract committed ahead of a build blocked on #296"
        files:
          - path: {_REGISTERED_FILE}
            missing_symbols:
              - lorerunes.FixturePlaceholder
              - lorerunes.SCOPE_READ
            unsymboled_codes:
              - code: no-any-unimported
                count: 2
                reason: "downstream of the unfollowed import; names no symbol"
          - path: {_OTHER_REGISTERED_FILE}
            missing_symbols:
              - loremaster.config.resolve_posture
    """
)


@pytest.fixture()
def registry_path(tmp_path: Path) -> Path:
    path = tmp_path / "pending_contracts.yaml"
    path.write_text(_REGISTRY_YAML)
    return path


@pytest.fixture()
def repo_root(tmp_path: Path) -> Path:
    """A sandbox tree in which every registered file EXISTS.

    Registered files must exist on disk or the registry is stale — so the
    default fixture satisfies that, and the staleness test deletes one.
    """
    root = tmp_path / "tree"
    for relative in (_REGISTERED_FILE, _OTHER_REGISTERED_FILE):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# pending contract\n")
    return root


@pytest.fixture()
def gate(registry_path: Path, repo_root: Path) -> PendingContractGate:
    return PendingContractGate(
        registry=PendingContractRegistry.load(registry_path),
        repo_root=repo_root,
    )


# --------------------------------------------------------------------------
# 1. Registry loading — a validated boundary
# --------------------------------------------------------------------------


def test_registry_loads_bounds_files_and_symbols(registry_path: Path) -> None:
    registry = PendingContractRegistry.load(registry_path)
    assert [bound.id for bound in registry.bounds] == ["packet-39-pending-build"]
    assert registry.registered_paths == {_REGISTERED_FILE, _OTHER_REGISTERED_FILE}
    assert registry.symbol_count == 3


def test_registry_rejects_an_unknown_key(tmp_path: Path) -> None:
    """``extra='forbid'`` at the wire boundary — a typo'd key must not be a
    silently-ignored exemption that reads as present."""
    path = tmp_path / "bad.yaml"
    typoed = _REGISTRY_YAML.replace("    rationale:", "    rationalle:")
    assert typoed != _REGISTRY_YAML, "the fixture's own edit must actually land"
    path.write_text(typoed)
    with pytest.raises(RegistryError):
        PendingContractRegistry.load(path)


def test_registry_rejects_a_bound_with_no_files(tmp_path: Path) -> None:
    """A bound naming nothing is a disclaimer, not a fact. Facts or nothing."""
    path = tmp_path / "empty.yaml"
    path.write_text(
        textwrap.dedent(
            """\
            version: 1
            bounds:
              - id: nothing
                owner: nobody
                reopen_trigger: never
                ruling: none
                rationale: none
                files: []
            """
        )
    )
    with pytest.raises(RegistryError):
        PendingContractRegistry.load(path)


def test_registry_rejects_a_file_with_neither_symbols_nor_codes(tmp_path: Path) -> None:
    """A file entry with no claim at all degenerates to file-only matching —
    exactly the wrong build case 1 describes."""
    path = tmp_path / "loose.yaml"
    path.write_text(
        textwrap.dedent(
            f"""\
            version: 1
            bounds:
              - id: loose
                owner: nobody
                reopen_trigger: never
                ruling: none
                rationale: none
                files:
                  - path: {_REGISTERED_FILE}
                    missing_symbols: []
            """
        )
    )
    with pytest.raises(RegistryError):
        PendingContractRegistry.load(path)


# --------------------------------------------------------------------------
# 2. Mypy output reading — and its anti-vacuity guards
# --------------------------------------------------------------------------


def test_reads_error_path_code_and_message() -> None:
    run = MypyOutputReader.read(
        _mypy_output([_attr_error(_REGISTERED_FILE, 74, "lorerunes", "FixturePlaceholder")])
    )
    assert run.declared_total == 1
    assert len(run.errors) == 1
    error = run.errors[0]
    assert error.path == _REGISTERED_FILE
    assert error.line == 74
    assert error.code == "attr-defined"
    assert '"FixturePlaceholder"' in error.message


def test_notes_are_not_counted_as_errors() -> None:
    """mypy's ``Found N errors`` counts errors only; a parser that also counted
    notes would trip its own cross-check on any real run."""
    text = _mypy_output(
        [
            _attr_error(_REGISTERED_FILE, 74, "lorerunes", "FixturePlaceholder"),
            f"{_REGISTERED_FILE}:74: note: Did you mean something else?",
        ]
    )
    # The helper derived `Found 2` from two lines; correct that to the truth.
    text = text.replace("Found 2 errors", "Found 1 error")
    run = MypyOutputReader.read(text)
    assert len(run.errors) == 1


def test_error_line_count_must_equal_mypys_own_total() -> None:
    """THE CROSS-CHECK. If the regex stops matching production output, the
    partition sees nothing unexpected and the gate goes green over an unread
    error set. mypy states its own total; disagreeing with it is a STOP."""
    text = _mypy_output([_attr_error(_REGISTERED_FILE, 74, "lorerunes", "FixturePlaceholder")])
    text = text.replace("Found 1 errors", "Found 9 errors")
    with pytest.raises(BrokenInstrumentError, match="9"):
        MypyOutputReader.read(text)


def test_leg_without_a_verdict_line_is_a_broken_instrument() -> None:
    """``mypy: can't read file 'lorescribe'`` emits no ``Found``/``Success``
    line. Every mypy leg must account for itself or the transcript is not a
    measurement."""
    text = (
        "Success: no issues found in 27 source files\n"
        "typecheck: lorescribe OK\n"
        "mypy: can't read file 'loremaster': No such file or directory\n"
        "typecheck: loremaster FAILED\n"
        "typecheck: shellcheck OK (7 tracked .sh)\n"
    )
    with pytest.raises(BrokenInstrumentError, match="loremaster"):
        MypyOutputReader.read(text)


def test_transcript_with_no_legs_at_all_is_a_broken_instrument() -> None:
    """An empty transcript is a broken runner, never a clean tree — the same
    anti-vacuity rule ``typecheck.sh``'s own shell leg states."""
    with pytest.raises(BrokenInstrumentError):
        MypyOutputReader.read("")


def test_shellcheck_verdict_is_carried_through() -> None:
    run = MypyOutputReader.read(_mypy_output([]))
    assert run.shellcheck == "OK"


# --------------------------------------------------------------------------
# 3. The mypy partition — DENY BY DEFAULT
# --------------------------------------------------------------------------


def test_registered_file_and_symbol_is_expected(gate: PendingContractGate) -> None:
    run = MypyOutputReader.read(
        _mypy_output([_attr_error(_REGISTERED_FILE, 74, "lorerunes", "FixturePlaceholder")])
    )
    partition = gate.partition_mypy(run)
    assert len(partition.expected) == 1
    assert partition.unexpected == []


def test_unregistered_file_is_unexpected(gate: PendingContractGate) -> None:
    """CONTROL: an error outside the registry must never be waved through, even
    when its symbol happens to be a registered name."""
    run = MypyOutputReader.read(
        _mypy_output([_attr_error(_UNREGISTERED_FILE, 12, "lorerunes", "FixturePlaceholder")])
    )
    partition = gate.partition_mypy(run)
    assert partition.expected == []
    assert len(partition.unexpected) == 1
    assert partition.unexpected[0].path == _UNREGISTERED_FILE


def test_registered_file_with_unregistered_symbol_is_unexpected(
    gate: PendingContractGate,
) -> None:
    """CONTROL, and the case file-only matching waves through: a genuinely new
    defect inside a pending-contract file."""
    run = MypyOutputReader.read(
        _mypy_output(
            [_attr_error(_REGISTERED_FILE, 91, "lorerunes", "something_brand_new")]
        )
    )
    partition = gate.partition_mypy(run)
    assert partition.expected == []
    assert len(partition.unexpected) == 1
    assert "something_brand_new" in partition.unexpected[0].message


def test_symbol_match_is_quoted_exact_not_substring(gate: PendingContractGate) -> None:
    """``FixturePlaceholder`` is a proper substring of ``FixturePlaceholderRefusal``. A wrapper doing
    ``symbol in message`` admits an unregistered symbol and cannot tell."""
    run = MypyOutputReader.read(
        _mypy_output([_attr_error(_REGISTERED_FILE, 20, "lorerunes", "FixturePlaceholderRefusal")])
    )
    partition = gate.partition_mypy(run)
    assert partition.unexpected, (
        "FixturePlaceholderRefusal is not registered — must not match FixturePlaceholder"
    )


def test_dotted_symbol_requires_the_owner_module_too(gate: PendingContractGate) -> None:
    """``lorerunes.FixturePlaceholder`` is registered; the same attribute name on a
    DIFFERENT owner is a different claim and stays unexpected."""
    run = MypyOutputReader.read(
        _mypy_output([_attr_error(_REGISTERED_FILE, 20, "loremaster.config", "FixturePlaceholder")])
    )
    partition = gate.partition_mypy(run)
    assert partition.unexpected, "owner module must participate in the match"


def test_unsymboled_code_allowance_admits_exactly_its_declared_count(
    gate: PendingContractGate,
) -> None:
    """Falsifier (b) of the ruling: ``no-any-unimported`` names no symbol, so
    per-symbol discrimination is unbuildable for it. The residual is stated as a
    CAPPED per-file, per-code count rather than an open door."""
    unsymboled = (
        f"{_REGISTERED_FILE}:74: error: Return type becomes "
        f'"Any | None" due to an unfollowed import  [no-any-unimported]'
    )
    run = MypyOutputReader.read(_mypy_output([unsymboled, unsymboled]))
    partition = gate.partition_mypy(run)
    assert len(partition.expected) == 2
    assert partition.unexpected == []


def test_unsymboled_code_over_its_declared_count_fails(
    gate: PendingContractGate,
) -> None:
    """The allowance is a PIN, not a category. A third one is a change in the
    world and must be re-adjudicated, not absorbed."""
    unsymboled = (
        f"{_REGISTERED_FILE}:74: error: Return type becomes "
        f'"Any" due to an unfollowed import  [no-any-unimported]'
    )
    run = MypyOutputReader.read(_mypy_output([unsymboled] * 3))
    verdict = gate.adjudicate(mypy_run=run, pytest_run=None)
    assert not verdict.ok
    assert any("no-any-unimported" in reason for reason in verdict.failures)


def test_unsymboled_code_does_not_leak_to_another_registered_file(
    gate: PendingContractGate,
) -> None:
    """The allowance is scoped to the file that declared it."""
    unsymboled = (
        f"{_OTHER_REGISTERED_FILE}:9: error: Return type becomes "
        f'"Any" due to an unfollowed import  [no-any-unimported]'
    )
    run = MypyOutputReader.read(_mypy_output([unsymboled]))
    partition = gate.partition_mypy(run)
    assert partition.unexpected, "an unsymboled allowance is per-file, never global"


# --------------------------------------------------------------------------
# 3b. The ruff leg — the THIRD canonical gate, and the one this wrapper's first
#     draft silently omitted
# --------------------------------------------------------------------------
#
# ⚠ WHY THIS LEG EXISTS AT ALL. `CLAUDE.md` names THREE commit gates —
# `scripts/typecheck.sh`, `uv run ruff check .`, and pytest. The first draft of
# this wrapper ran two of them and would have served a verdict reading like a
# full-gate receipt. That is finding #306's defect EXACTLY — *"a close-out that
# reports SOME gates green reads as ALL gates green"* — reproduced inside the
# instrument built to pin #306. It was found because ruff was RED at HEAD too
# (2 violations in a committed file), which nothing had recorded either.
#
# The leg is ZERO-TOLERANCE by design: the registry can express a pending
# CONTRACT (missing symbols, designed-RED pins), and no such thing exists for a
# lint violation — a lint error is never "a symbol the build will create later".
# Stated as a design decision so a future reader can overturn it deliberately.


def test_ruff_clean_output_is_accepted() -> None:
    run = RuffOutputReader.read("All checks passed!\n", exit_code=0)
    assert run.violations == ()


def test_ruff_violations_are_read_with_their_locations() -> None:
    text = (
        "F401 [*] `subprocess` imported but unused\n"
        " --> scripts/lore_tool_name_currency.py:33:8\n"
        "PLW2901 `for` loop variable `line` overwritten by assignment target\n"
        " --> scripts/lore_tool_name_currency.py:148:9\n"
        "Found 2 errors.\n"
    )
    run = RuffOutputReader.read(text, exit_code=1)
    assert len(run.violations) == 2
    assert all("lore_tool_name_currency.py" in v for v in run.violations)


def test_ruff_violation_count_must_match_ruffs_own_total() -> None:
    """The same cross-check the mypy leg carries: if the reader stops matching
    ruff's output, a silent zero reads as clean."""
    text = (
        "F401 [*] `os` imported but unused\n"
        " --> a.py:1:8\n"
        "Found 7 errors.\n"
    )
    with pytest.raises(BrokenInstrumentError, match="7"):
        RuffOutputReader.read(text, exit_code=1)


def test_ruff_finding_no_python_files_is_a_broken_instrument() -> None:
    """MEASURED (2026-08-01): ``ruff check`` over a path with no Python files
    prints ``warning: No Python files found under the given path(s)`` **and then
    ``All checks passed!``, and exits 0.** A wrong cwd or a moved tree therefore
    renders byte-identical to a clean repo — the exact false clear
    ``typecheck.sh``'s own shell leg documents for ``git ls-files``."""
    with pytest.raises(BrokenInstrumentError, match="No Python files"):
        RuffOutputReader.read(
            "warning: No Python files found under the given path(s)\n"
            "All checks passed!\n",
            exit_code=0,
        )


def test_ruff_exit_zero_without_the_all_clear_line_is_a_broken_instrument() -> None:
    with pytest.raises(BrokenInstrumentError):
        RuffOutputReader.read("", exit_code=0)


def test_ruff_violations_fail_the_verdict_and_are_named_individually(
    gate: PendingContractGate,
) -> None:
    """ZERO TOLERANCE: the registry cannot excuse a lint violation, not even one
    inside a registered pending-contract file."""
    ruff_run = RuffOutputReader.read(
        f"F401 [*] `os` imported but unused\n --> {_REGISTERED_FILE}:1:8\n"
        "Found 1 error.\n",
        exit_code=1,
    )
    verdict = gate.adjudicate(
        mypy_run=_healthy_mypy_run(), pytest_run=None, ruff_run=ruff_run
    )
    assert not verdict.ok
    assert any(_REGISTERED_FILE in reason and "ruff" in reason.lower() for reason in verdict.failures)


def test_a_deploy_receipt_requires_ALL_THREE_legs(gate: PendingContractGate) -> None:
    """#306's transferable lesson, enforced rather than remembered: a run that
    skipped a gate may never render as the full-gate receipt."""
    pytest_run = JUnitReportReader.read(_junit([(_REGISTERED_FILE, "test_pin", True)]))
    clean_ruff = RuffOutputReader.read("All checks passed!\n", exit_code=0)

    two_legs = gate.adjudicate(
        mypy_run=_healthy_mypy_run(), pytest_run=pytest_run, ruff_run=None
    )
    assert two_legs.ok and not two_legs.is_deploy_receipt

    three_legs = gate.adjudicate(
        mypy_run=_healthy_mypy_run(), pytest_run=pytest_run, ruff_run=clean_ruff
    )
    assert three_legs.ok and three_legs.is_deploy_receipt


# --------------------------------------------------------------------------
# 4. The pytest partition
# --------------------------------------------------------------------------


def _junit(cases: list[tuple[str, str, bool]], *, total: int | None = None) -> str:
    """``cases`` are ``(file, test_name, failed)`` triples."""
    failures = sum(1 for _, _, failed in cases if failed)
    body = "".join(
        f'<testcase classname="c" name="{name}" file="{file}">'
        + ("<failure message='pin'>boom</failure>" if failed else "")
        + "</testcase>"
        for file, name, failed in cases
    )
    tests = len(cases) if total is None else total
    return (
        f'<?xml version="1.0" encoding="utf-8"?><testsuites><testsuite '
        f'name="pytest" tests="{tests}" failures="{failures}" errors="0" '
        f'skipped="0">{body}</testsuite></testsuites>'
    )


def test_junit_reader_counts_passed_and_failed() -> None:
    run = JUnitReportReader.read(
        _junit(
            [
                (_REGISTERED_FILE, "test_a", True),
                (_UNREGISTERED_FILE, "test_b", False),
            ]
        )
    )
    assert run.total == 2
    assert run.passed == 1
    assert len(run.outcomes) == 1


def test_zero_collected_tests_is_a_broken_instrument() -> None:
    """``no tests ran in 0.00s`` behind a pipe is this repo's documented silent
    green. Zero collected is never a pass."""
    with pytest.raises(BrokenInstrumentError):
        JUnitReportReader.read(_junit([], total=0))


def test_a_failure_with_no_file_attribute_is_a_broken_instrument() -> None:
    """MEASURED, and it cost a 7-minute suite run to find (2026-08-01).

    pytest's DEFAULT junit family is ``xunit2``, whose ``_base`` testcase
    attribute set is exactly ``["classname", "name"]`` — ``file`` and ``line``
    live in ``_base_legacy`` and are FILTERED OUT. Read in the installed
    ``_pytest/junitxml.py``: ``record_testreport`` DOES set ``file``, and the
    family then drops it.

    Consequence if this guard did not exist: every failure arrives with no file,
    the partition can attribute none of them, and 444 correctly-registered pins
    render as UNREGISTERED. **Nothing about the run looks wrong — the tail just
    says the wrong number.** So an unattributable document is refused outright
    rather than partitioned, which makes losing ``-o junit_family=xunit1``
    impossible to do silently.
    """
    xunit2_shaped = (
        '<?xml version="1.0" encoding="utf-8"?><testsuites><testsuite '
        'name="pytest" tests="1" failures="1" errors="0" skipped="0">'
        '<testcase classname="pkg.tests.test_thing" name="test_pin">'
        "<failure message='pin'>boom</failure></testcase>"
        "</testsuite></testsuites>"
    )
    with pytest.raises(BrokenInstrumentError, match="xunit1"):
        JUnitReportReader.read(xunit2_shaped)


def test_a_passing_testcase_needs_no_file_attribute() -> None:
    """The guard is scoped to FAILURES — the only rows the partition reads.
    Demanding it of every passing row would reject a perfectly usable document
    for a field nothing consumes."""
    run = JUnitReportReader.read(
        '<?xml version="1.0" encoding="utf-8"?><testsuites><testsuite '
        'name="pytest" tests="1" failures="0" errors="0" skipped="0">'
        '<testcase classname="pkg.tests.test_thing" name="test_ok"/>'
        "</testsuite></testsuites>"
    )
    assert run.passed == 1


def test_pytest_failure_inside_a_registered_file_is_expected(
    gate: PendingContractGate,
) -> None:
    run = JUnitReportReader.read(_junit([(_REGISTERED_FILE, "test_pin", True)]))
    partition = gate.partition_pytest(run)
    assert len(partition.expected) == 1
    assert partition.unexpected == []


def test_pytest_failure_outside_the_registry_is_unexpected(
    gate: PendingContractGate,
) -> None:
    """CONTROL: the 444 designed-RED pins are admitted; a real regression next
    door is not."""
    run = JUnitReportReader.read(_junit([(_UNREGISTERED_FILE, "test_real", True)]))
    partition = gate.partition_pytest(run)
    assert len(partition.unexpected) == 1


# --------------------------------------------------------------------------
# 5. SELF-DESTRUCTION — the registry may not outlive its premise
# --------------------------------------------------------------------------


def test_self_destruct_when_a_registered_file_no_longer_exists(
    gate: PendingContractGate, repo_root: Path
) -> None:
    (repo_root / _REGISTERED_FILE).unlink()
    run = MypyOutputReader.read(
        _mypy_output([_attr_error(_OTHER_REGISTERED_FILE, 3, "loremaster.config", "resolve_posture")])
    )
    verdict = gate.adjudicate(mypy_run=run, pytest_run=None)
    assert not verdict.ok
    assert any(_REGISTERED_FILE in reason for reason in verdict.failures)


def test_self_destruct_when_a_registered_file_stops_erroring(
    gate: PendingContractGate,
) -> None:
    """THE CORE SELF-DESTRUCT: the build started, the file went green, and the
    registry entry is now a stale exemption. The wrapper REFUSES until it is
    deleted with the fix."""
    run = MypyOutputReader.read(
        _mypy_output([_attr_error(_OTHER_REGISTERED_FILE, 3, "loremaster.config", "resolve_posture")])
    )
    verdict = gate.adjudicate(mypy_run=run, pytest_run=None)
    assert not verdict.ok
    assert any(
        _REGISTERED_FILE in reason and "delete" in reason.lower()
        for reason in verdict.failures
    )


def test_self_destruct_when_one_registered_symbol_stops_erroring(
    gate: PendingContractGate,
) -> None:
    """Per-SYMBOL, not merely per-file: half a build discharges half a claim,
    and the surviving half must shrink to match."""
    unsymboled = (
        f"{_REGISTERED_FILE}:74: error: Return type becomes "
        f'"Any" due to an unfollowed import  [no-any-unimported]'
    )
    run = MypyOutputReader.read(
        _mypy_output(
            [
                _attr_error(_REGISTERED_FILE, 74, "lorerunes", "FixturePlaceholder"),
                unsymboled,
                unsymboled,
                _attr_error(
                    _OTHER_REGISTERED_FILE, 3, "loremaster.config", "resolve_posture"
                ),
            ]
        )
    )
    verdict = gate.adjudicate(mypy_run=run, pytest_run=None)
    assert not verdict.ok
    assert any("SCOPE_READ" in reason for reason in verdict.failures)


def test_self_destruct_when_a_registered_symbol_becomes_importable(
    tmp_path: Path, repo_root: Path
) -> None:
    """The INDEPENDENT leg: import-based, not output-based. It answers "does the
    symbol exist now?" without asking the gate transcript, so it still fires
    when the mypy leg was not run at all."""
    path = tmp_path / "importable.yaml"
    path.write_text(
        textwrap.dedent(
            f"""\
            version: 1
            bounds:
              - id: discharged
                owner: nobody
                reopen_trigger: never
                ruling: none
                rationale: none
                files:
                  - path: {_REGISTERED_FILE}
                    missing_symbols:
                      - pathlib.Path
            """
        )
    )
    gate = PendingContractGate(
        registry=PendingContractRegistry.load(path), repo_root=repo_root
    )
    findings = gate.registry_liveness_findings()
    assert any("pathlib.Path" in finding for finding in findings)


def test_liveness_leg_reports_uncheckable_symbols_rather_than_assuming(
    gate: PendingContractGate,
) -> None:
    """A symbol whose owner cannot be imported is UNCHECKED, and the count is
    served. An unstated bound is the failure this instrument exists to name."""
    assert gate.registry_liveness_findings() == []
    assert gate.liveness_coverage.unchecked >= 0
    assert (
        gate.liveness_coverage.checked + gate.liveness_coverage.unchecked
        == gate.registry.symbol_count
    )


# --------------------------------------------------------------------------
# 6. The served verdict — partition counts, not a bare pass
# --------------------------------------------------------------------------


def _healthy_mypy_run() -> MypyRun:
    unsymboled = (
        f"{_REGISTERED_FILE}:74: error: Return type becomes "
        f'"Any" due to an unfollowed import  [no-any-unimported]'
    )
    return MypyOutputReader.read(
        _mypy_output(
            [
                _attr_error(_REGISTERED_FILE, 74, "lorerunes", "FixturePlaceholder"),
                _attr_error(_REGISTERED_FILE, 80, "lorerunes", "SCOPE_READ"),
                unsymboled,
                unsymboled,
                _attr_error(
                    _OTHER_REGISTERED_FILE, 3, "loremaster.config", "resolve_posture"
                ),
            ]
        )
    )


def test_healthy_run_passes_and_serves_partition_counts(
    gate: PendingContractGate,
) -> None:
    """CONTROL 3: the instrument can say yes. A probe never shown to pass is as
    useless as one never shown to fire."""
    pytest_run = JUnitReportReader.read(
        _junit(
            [
                (_REGISTERED_FILE, "test_pin", True),
                (_UNREGISTERED_FILE, "test_ok", False),
            ]
        )
    )
    verdict = gate.adjudicate(mypy_run=_healthy_mypy_run(), pytest_run=pytest_run)
    assert verdict.ok, verdict.failures
    tail = "\n".join(verdict.lines)
    assert "5" in tail and "0 UNREGISTERED" in tail
    assert "packet-39-pending-build" in tail


def test_verdict_names_every_unexpected_error_individually(
    gate: PendingContractGate,
) -> None:
    """*"All remaining hits are X" is banned output* — every residual gets its
    own ``file:line``."""
    run = MypyOutputReader.read(
        _mypy_output(
            [
                _attr_error(_UNREGISTERED_FILE, 11, "loremaster.config", "alpha"),
                _attr_error(_UNREGISTERED_FILE, 22, "loremaster.config", "beta"),
            ]
        )
    )
    verdict = gate.adjudicate(mypy_run=run, pytest_run=None)
    assert not verdict.ok
    tail = "\n".join(verdict.lines + verdict.failures)
    assert f"{_UNREGISTERED_FILE}:11" in tail
    assert f"{_UNREGISTERED_FILE}:22" in tail


def test_shellcheck_failure_is_never_partitionable(gate: PendingContractGate) -> None:
    """The registry speaks about mypy symbols and pytest files. A shell defect
    is neither, so it can only ever be a loud failure."""
    text = _mypy_output([]).replace(
        "typecheck: shellcheck OK (7 tracked .sh)", "typecheck: shellcheck FAILED"
    )
    run = MypyOutputReader.read(text)
    verdict = gate.adjudicate(mypy_run=run, pytest_run=None)
    assert not verdict.ok
    assert any("shellcheck" in reason for reason in verdict.failures)


def test_a_skipped_leg_is_never_served_as_a_deploy_receipt(
    gate: PendingContractGate,
) -> None:
    """``pytest_run=None`` means the suite did not run. The verdict may still be
    ok for a scoped check, but it must NOT read as the deploy gate's receipt."""
    verdict = gate.adjudicate(mypy_run=_healthy_mypy_run(), pytest_run=None)
    assert verdict.ok
    assert not verdict.is_deploy_receipt
    assert any("PARTIAL" in line for line in verdict.lines)


def test_an_EMPTY_registry_degrades_to_a_pass_through_over_the_plain_gates(
    tmp_path: Path, repo_root: Path
) -> None:
    """THE RULING'S FALSIFIER (c), PINNED — the clause after "and keep it".

    *"#296 resolving before this wave's deploy ⇒ the registry empties at the
    build and the wrapper degrades to a pass-through over the plain gates (keep
    it — 04b-3 and every future pending contract are its consumers)."*

    So an empty registry must be LEGAL (not a validation error) and must mean
    exactly ``CLAUDE.md``'s unmodified gate: zero mypy errors, full stop. Both
    directions are asserted, because "it accepts an empty file" alone would also
    be true of a build that ignored the registry entirely.
    """
    path = tmp_path / "empty.yaml"
    path.write_text("version: 1\nbounds: []\n")
    gate = PendingContractGate(
        registry=PendingContractRegistry.load(path), repo_root=repo_root
    )

    clean = MypyOutputReader.read(_mypy_output([]))
    assert gate.adjudicate(mypy_run=clean, pytest_run=None).ok

    one_error = MypyOutputReader.read(
        _mypy_output([_attr_error(_REGISTERED_FILE, 74, "lorerunes", "FixturePlaceholder")])
    )
    verdict = gate.adjudicate(mypy_run=one_error, pytest_run=None)
    assert not verdict.ok, "an empty registry must admit NOTHING"
    assert any("UNREGISTERED" in reason for reason in verdict.failures)


# ⚠ ``test_full_run_is_a_deploy_receipt`` USED TO LIVE HERE and asserted that
# mypy + pytest alone yielded a deploy receipt. It was TRUE of the two-leg draft
# and is FALSE now that the ruff leg exists — a test written before a semantic
# change certifying the OLD world, which this repo's law says to hunt for
# explicitly on any such change rather than leaving green. Deleted deliberately;
# ``test_a_deploy_receipt_requires_ALL_THREE_legs`` is its successor and asserts
# BOTH directions (two legs ⇒ not a receipt, three ⇒ receipt), so nothing was
# lost in the replacement.
