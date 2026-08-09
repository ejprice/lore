"""Contract for ``scripts/wave_gate.py`` — INSTRUMENT G, the non-omittable gate
bundle (finding #344; design doc ``docs/plans/v2/design/2026-08-09-defect-class-
prevention.md`` §3 INSTRUMENT G + §4 F1).

⚠ **RED UNTIL BUILT.** ``scripts/wave_gate.py`` does not exist as of this
contract. Every test here errors at collection (``ModuleNotFoundError: wave_gate``)
until a builder creates the module with the surface this contract mandates. That is
the intended RED — a contract-first pin authored before the code.

──────────────────────────────────────────────────────────────────────────────
WHY THIS EXISTS (finding #344, measured 2026-08-09).
──────────────────────────────────────────────────────────────────────────────
05a-i reproduced #306/#312 a THIRD time: a build/adversary stage ran a HAND-LISTED
gate subset (typecheck + ruff + the 4 contract suites) and **omitted**
``pending_contract_gate.py --currency``. Eight RED_ORPHANED structural pins the diff
introduced went unseen for two cycles until a cold audit ran currency. Root cause:
*"the gates"* is a hand-list re-typed in each spawn brief, and hand-lists drift and
omit — the enumeration antipattern this repo has the most receipts against.

``scripts/gates.yaml`` is ALREADY the gate authority, and
``pending_contract_gate.py`` ALREADY derives its leg set from it and fails
``VERDICT_NOT_RUN`` on any omitted manifested gate. The gap #344 names is one level
up: there is no single ENTRYPOINT a brief can point at instead of re-listing gates,
and no posture that stays honest about pytest scope. ``wave_gate.py`` is that
entrypoint. No CI exists (#285), so the bundle IS the enforcement point.

──────────────────────────────────────────────────────────────────────────────
THE CONTRACT SURFACE THIS PINS (the seam a builder must satisfy).
──────────────────────────────────────────────────────────────────────────────
This contract mandates a small public surface on ``wave_gate``, chosen to mirror
``pending_contract_gate._render_currency`` (the machinery it wraps) so the wrapper
re-implements and re-lists nothing (ONE IMPLEMENTATION):

  * ``MODE_WAVE`` / ``MODE_CHECKPOINT`` — distinct non-empty str constants.
  * ``render_wave_receipt(gate, manifest, results, *, mode, pytest_selector=())``
        ``-> tuple[list[str], bool]`` — the pure, mode-aware currency renderer.
        ``results`` is keyed by gate id exactly as ``_run_selected_gates`` returns.
        Returns ``(lines, ok)`` exactly as ``_render_currency`` does. ``mode`` is
        KEYWORD-ONLY with NO DEFAULT — a stage cannot render a verdict without
        declaring its mode.
  * ``pytest_args_for(mode, pytest_selector) -> tuple[str, ...]`` — the scoping
        decision: the selector in ``--wave``, ``()`` (full) in ``--checkpoint``.
  * ``main(argv=None) -> int`` — the CLI entrypoint; mode is a REQUIRED argument.

These names are the contract's DEFINED seam; the builder implements to them. (Flagged
to the operator/lead in ``REPORT-contract-g.md`` — the architecture this presupposes
is IN-PROCESS composition of ``pending_contract_gate``'s machinery, not a stdout-
parsing subprocess wrapper, because the SCOPED-not-GREEN override needs structured
access to the pytest currency verdict.)

──────────────────────────────────────────────────────────────────────────────
⚠ WHAT WRONG BUILD WOULD STILL PASS THIS? — asked of every fixture, because a gate
bundle is exactly the shape that reads green while proving nothing (the #306/#312/
#344 class). Each discriminating case has a fixture that FAILS that wrong build:

  W1. **A hardcoded gate tuple** (``("typecheck", "ruff", "pytest")``) that does not
      track the manifest — #312's exact defect. Killed by
      ``test_no_hardcoded_gate_id_collection`` (source scan) AND
      ``test_render_enumerates_exactly_the_manifest_gates`` (a gate added to / dropped
      from the manifest changes the render; a hardcoded list cannot).
  W2. **A subset rendered as an unqualified pass** — a stage that omits a gate and
      reads green (the literal #344 event). Killed by
      ``test_claimed_gate_absent_from_results_is_not_run_and_fails``.
  W3. **A scoped pytest run rendered GREEN** — a wave receipt claiming a pytest
      currency clear from a ``-k`` subset. Killed by
      ``test_wave_pytest_scoped_never_green_and_echoes_selector``.
  W4. **The non-omittable core quietly scoped/skipped in wave mode** — typecheck or
      ruff treated as scopable. Killed by
      ``test_wave_core_gates_run_full_and_still_fail``.
  W5. **Scopability keyed on the literal id ``"pytest"``** rather than derived from
      the reader — drifts the moment the junit gate is renamed. Killed by
      ``test_scopable_gate_identified_by_reader_not_literal_id`` (junit gate named
      ``suite``).
  W6. **A verdict produced without a declared mode** — a defaulted/hidden mode.
      Killed by ``test_render_requires_mode_declared`` and
      ``test_cli_refuses_without_a_declared_mode``.
  W7. **A RED_ORPHANED currency waved through** — the whole point of #344. Killed by
      ``test_checkpoint_red_orphaned_fails``.

⚠ EVERY FIXTURE HERE IS CANNED DATA UNDER ``tmp_path``. Nothing shells out to the
real gates or reads the real ``gates.yaml``: a contract that depended on the live
tree would assert the WEATHER, not the INSTRUMENT, and go red every time an unrelated
packet landed (the same discipline ``test_pending_contract_gate.py`` states).
"""

from __future__ import annotations

import ast
import importlib
import os
import re
import sys
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# The machinery the bundle WRAPS — real, existing types. The contract builds its
# canned gate results with the same readers the runner uses in production, so a
# fixture cannot encode a shape mypy/ruff/pytest never emit.
import pending_contract_gate as _pcg  # noqa: E402  (module handle for from-import-reaching spies)
from pending_contract_gate import (  # noqa: E402
    READERS,
    GateManifest,
    GateRunner,
    JUnitReportReader,
    MypyOutputReader,
    MypyRun,
    PendingContractGate,
    PendingContractRegistry,
    PytestRun,
    RuffOutputReader,
    RuffRun,
    _render_currency,
)

_GateResults = dict[str, MypyRun | RuffRun | PytestRun]

# The module under contract. RED now: it does not exist, so this raises
# ``ModuleNotFoundError`` at collection — the intended contract-first RED. Acquired via
# ``importlib`` (not a static ``import wave_gate``) DELIBERATELY: a static import would
# need ``# type: ignore[import-not-found]`` today, and strict mypy's
# ``warn_unused_ignores`` would then redden that ignore as UNUSED the moment the builder
# creates the module — a latent orphaned red the contract must not plant. The dynamic
# form keeps the typecheck gate clean in BOTH states and couples the builder to nothing.
# Accessed as ``wave_gate.<name>`` per test so one missing attribute fails ONE test with
# a clear ``AttributeError`` rather than erroring the whole file.
wave_gate = importlib.import_module("wave_gate")


# ==========================================================================
# Canned gate output — real shapes. ``_attr_error`` / ``_mypy_output`` / ``_junit``
# mirror ``test_pending_contract_gate.py``'s builders (local test scaffolding, kept
# in step deliberately — a synthetic message shape is how a reader passes its tests
# and misses production output).
# ==========================================================================

_PROBE_FILE = "loremaster/tests/test_probe.py"


def _attr_error(path: str, line: int, owner: str, attribute: str) -> str:
    return (
        f'{path}:{line}: error: Module "{owner}" has no attribute '
        f'"{attribute}"  [attr-defined]'
    )


def _mypy_output(error_lines: list[str]) -> str:
    """A full ``typecheck.sh`` transcript wrapping ``error_lines``. The summary total
    is DERIVED from the lines so a fixture cannot accidentally encode a count
    mismatch the reader would reject."""
    body = "\n".join(error_lines)
    if error_lines:
        summary = (
            f"Found {len(error_lines)} errors in 1 file (checked 180 source files)\n"
            "typecheck: loremaster FAILED"
        )
    else:
        summary = "Success: no issues found in 180 source files\ntypecheck: loremaster OK"
    return f"{body}\n{summary}\n" "typecheck: shellcheck OK (7 tracked .sh)\n"


def _junit(cases: list[tuple[str, str, bool]]) -> str:
    """``cases`` are ``(file, test_name, failed)`` triples."""
    failures = sum(1 for _, _, failed in cases if failed)
    body = "".join(
        f'<testcase classname="c" name="{name}" file="{file}">'
        + ("<failure message='pin'>boom</failure>" if failed else "")
        + "</testcase>"
        for file, name, failed in cases
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?><testsuites><testsuite '
        f'name="pytest" tests="{len(cases)}" failures="{failures}" errors="0" '
        f'skipped="0">{body}</testsuite></testsuites>'
    )


_CLEAN_RUFF = "All checks passed!\n"
_DIRTY_RUFF = "F401 [*] `os` imported but unused\n --> some/x.py:1:8\nFound 1 error.\n"


# ==========================================================================
# Manifest / results / gate fixtures — canned, self-contained.
# ==========================================================================


def _manifest(
    path: Path,
    *,
    junit_id: str = "pytest",
    extra: bool = False,
    drop: str | None = None,
) -> GateManifest:
    """A ``gates.yaml``-shaped manifest written under ``path``.

    Parametrised so a single wrong build can be attacked from several angles:
    ``junit_id`` renames the scopable gate (W5), ``extra`` adds a fourth gate and
    ``drop`` removes one (W1 — the render must track BOTH directions).
    """
    gates: list[tuple[str, str, str, list[str]]] = [
        ("typecheck", "typecheck_transcript", "pending-contracts", ["./scripts/typecheck.sh"]),
        ("ruff", "ruff", "none", ["uv", "run", "ruff", "check", "."]),
        (
            junit_id,
            "pytest_junit",
            "pending-contracts",
            ["uv", "run", "pytest", "-q", "--junit-xml={junit_xml}"],
        ),
    ]
    if extra:
        gates.append(("extra", "ruff", "none", ["true"]))
    if drop is not None:
        gates = [gate for gate in gates if gate[0] != drop]
    data = {
        "version": 1,
        "gates": [
            {
                "id": gate_id,
                "description": f"{gate_id} gate",
                "command": command,
                "reader": reader,
                "adjudicated_by": adjudicated_by,
            }
            for gate_id, reader, adjudicated_by, command in gates
        ],
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return GateManifest.load(path)


def _results(
    manifest: GateManifest,
    *,
    mypy: str = "clean",
    ruff: str = "clean",
    junit: str = "clean",
    omit: tuple[str, ...] = (),
) -> dict[str, object]:
    """Canned per-gate results keyed by gate id, BY READER — so it works whatever the
    junit gate is named. ``omit`` drops a gate entirely (it was never run)."""
    out: dict[str, object] = {}
    for spec in manifest.gates:
        if spec.id in omit:
            continue
        reader = READERS[spec.reader]
        if reader is MypyOutputReader:
            lines = [] if mypy == "clean" else [_attr_error(_PROBE_FILE, 1, "lorerunes", "Ghost")]
            out[spec.id] = MypyOutputReader.read(_mypy_output(lines))
        elif reader is RuffOutputReader:
            text = _CLEAN_RUFF if ruff == "clean" else _DIRTY_RUFF
            out[spec.id] = RuffOutputReader.read(text, exit_code=0 if ruff == "clean" else 1)
        elif reader is JUnitReportReader:
            cases = (
                [(_PROBE_FILE, "test_ok", False)]
                if junit == "clean"
                else [(_PROBE_FILE, "test_bad", True)]
            )
            out[spec.id] = JUnitReportReader.read(_junit(cases))
    return out


@pytest.fixture()
def gate(tmp_path: Path) -> PendingContractGate:
    """An EMPTY-registry gate: every error is unregistered, so a clean tree renders
    GREEN and any injected defect renders RED_ORPHANED — the positive/negative
    controls the currency pins need, with no dependence on the live registry."""
    return PendingContractGate(
        registry=PendingContractRegistry(version=1, bounds=()),
        repo_root=tmp_path,
    )


# ==========================================================================
# Helpers for reading the rendered receipt.
# ==========================================================================


# The receipt's gate ROSTER header (``  manifest   : (...)``) repeats every gate id
# inside a tuple repr, so a per-gate lookup must skip it. It is excluded by its OWN
# SHAPE — a line whose first word is ``manifest`` — NOT by the mere presence of the
# word "manifest" anywhere on the line. R1 (adversary-g): ``GateCurrency.render()``'s
# own NOT_RUN text reads ``… claimed by the manifest, never executed`` — a builder who
# mirrors that machinery verbatim (the DRY-faithful choice the contract MANDATES) would
# have every NOT_RUN line silently filtered out by a bare "manifest"-substring test,
# failing W2 with an opaque ``assert None is not None``. Excluding by prefix keeps the
# roster out while letting a legitimate NOT_RUN line that names the manifest through.
_ROSTER_HEADER = re.compile(r"^\s*manifest\s*:")


def _verdict_line(lines: list[str], gate_id: str) -> str | None:
    """The receipt line that reports ``gate_id``'s verdict, or None.

    Excludes only the ``manifest : (...)`` roster header (matched by its prefix), so a
    per-gate assertion targets the gate's OWN line, not the roster — and a NOT_RUN line
    that legitimately mentions "manifest" is still returned (R1)."""
    word = re.compile(rf"(^|\s|:){re.escape(gate_id)}(\s|:|$)")
    matches = [ln for ln in lines if word.search(ln) and not _ROSTER_HEADER.match(ln)]
    return matches[0] if matches else None


# ==========================================================================
# 1. Contract surface
# ==========================================================================


def test_module_exposes_the_contract_surface() -> None:
    """One clear failure if the mandated seam is incomplete, rather than an opaque
    unpacking error three tests later."""
    for name in ("MODE_WAVE", "MODE_CHECKPOINT", "render_wave_receipt", "pytest_args_for", "main"):
        assert hasattr(wave_gate, name), f"wave_gate must expose {name!r}"


def test_mode_constants_are_distinct_nonempty_strings() -> None:
    assert isinstance(wave_gate.MODE_WAVE, str) and wave_gate.MODE_WAVE
    assert isinstance(wave_gate.MODE_CHECKPOINT, str) and wave_gate.MODE_CHECKPOINT
    assert wave_gate.MODE_WAVE != wave_gate.MODE_CHECKPOINT


# ==========================================================================
# 2. Mode is a REQUIRED, RECORDED argument (W6)
# ==========================================================================


def test_render_requires_mode_declared(gate: PendingContractGate, tmp_path: Path) -> None:
    """``mode`` is keyword-only with no default: a stage cannot produce a verdict
    without declaring its mode. Omitting it is a TypeError, not a defaulted run."""
    manifest = _manifest(tmp_path / "m.yaml")
    with pytest.raises(TypeError):
        wave_gate.render_wave_receipt(gate, manifest, _results(manifest))


def test_receipt_header_records_the_chosen_mode(
    gate: PendingContractGate, tmp_path: Path
) -> None:
    """The mode is a RECORDED fact in the receipt, not a hideable free choice — so a
    reader of the receipt can tell a wave posture from a checkpoint one."""
    manifest = _manifest(tmp_path / "m.yaml")
    wave_lines, _ = wave_gate.render_wave_receipt(
        gate, manifest, _results(manifest), mode=wave_gate.MODE_WAVE,
        pytest_selector=["-k", "test_probe"],
    )
    checkpoint_lines, _ = wave_gate.render_wave_receipt(
        gate, manifest, _results(manifest), mode=wave_gate.MODE_CHECKPOINT
    )
    assert wave_gate.MODE_WAVE in "\n".join(wave_lines)
    assert wave_gate.MODE_CHECKPOINT in "\n".join(checkpoint_lines)


def test_cli_refuses_without_a_declared_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI half of W6: ``wave_gate.py`` invoked with no mode must not run a
    verdict. A required argument makes argparse exit non-zero BEFORE any gate runs.

    The runner is stubbed to a loud failure so this stays SAFE AND DISCRIMINATING: a
    correct build exits at argparse (the stub is never reached → SystemExit); a WRONG
    build that defaulted the mode reaches the stub and raises AssertionError instead of
    SystemExit (→ this test fails, flagging the wrong build) — without ever launching
    the real gates. (Assumes the bundle reuses ``pending_contract_gate.GateRunner`` per
    the ONE-IMPLEMENTATION design; flagged in REPORT-contract-g.md.)"""

    def _boom(*args: object, **kwargs: object) -> object:
        raise AssertionError("gate execution reached — the bundle did not require a mode")

    monkeypatch.setattr(GateRunner, "run", _boom)
    with pytest.raises(SystemExit) as exc:
        wave_gate.main([])
    assert exc.value.code != 0


# ==========================================================================
# 3. The gate set is DERIVED from the manifest — no hand-list (W1)
# ==========================================================================


def _string_collection_literals(tree: ast.AST) -> list[list[str]]:
    """Every ``(...)`` / ``[...]`` / ``{...}`` literal whose elements are ALL string
    constants — the shape a hand-listed gate set takes."""
    found: list[list[str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            strings = [
                element.value
                for element in node.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            ]
            if strings and len(strings) == len(node.elts):
                found.append(strings)
    return found


def test_no_hardcoded_gate_id_collection() -> None:
    """#312's exact defect: a hand-maintained tuple of the gate set, which the first
    draft of ``pending_contract_gate`` itself shipped (missing its ruff leg). The
    bundle must name NO gate set of its own.

    BOUND (stated, not glossed): this catches a literal COLLECTION co-naming the
    canonical gate ids. The general 'render tracks the manifest' proof is behavioral
    (``test_render_enumerates_exactly_the_manifest_gates``); this structural pin is
    the belt to that braces, matching the ``test_anchored_pattern_seam`` AST idiom.
    """
    module_file = wave_gate.__file__
    assert module_file is not None, "wave_gate must be a real on-disk module"
    source = Path(module_file).read_text()
    canonical = {"typecheck", "ruff", "pytest"}
    offenders = [
        strings
        for strings in _string_collection_literals(ast.parse(source))
        if len(canonical.intersection(strings)) >= 2
    ]
    assert not offenders, (
        "wave_gate.py contains a literal collection of gate ids "
        f"{offenders} — that is #312's hand-list. Derive the gate set from the "
        "GateManifest; re-list nothing."
    )


def test_render_enumerates_exactly_the_manifest_gates(
    gate: PendingContractGate, tmp_path: Path
) -> None:
    """COVERAGE AS A CHECKED VARIABLE: the set of gates the receipt reports MUST equal
    the manifest's gate set — in BOTH directions. A gate added to the manifest gains a
    verdict line; a gate dropped loses one. A hardcoded list can do neither, so this
    is the mutation proof for W1.
    """
    three = _manifest(tmp_path / "three.yaml")
    lines3, _ = wave_gate.render_wave_receipt(
        gate, three, _results(three), mode=wave_gate.MODE_CHECKPOINT
    )
    for gate_id in three.ids:
        assert _verdict_line(lines3, gate_id) is not None, f"{gate_id} unreported"

    # A gate ADDED to the manifest appears in the receipt (a hardcoded 3-list cannot).
    four = _manifest(tmp_path / "four.yaml", extra=True)
    lines4, ok4 = wave_gate.render_wave_receipt(
        gate, four, _results(four, omit=("extra",)), mode=wave_gate.MODE_CHECKPOINT
    )
    assert _verdict_line(lines4, "extra") is not None, "a manifested gate went unreported"
    assert not ok4, "a claimed gate that did not run must fail the bundle (NOT_RUN)"

    # A gate DROPPED from the manifest gets no verdict line (a hardcoded list would
    # still report it).
    two = _manifest(tmp_path / "two.yaml", drop="ruff")
    lines2, _ = wave_gate.render_wave_receipt(
        gate, two, _results(two), mode=wave_gate.MODE_CHECKPOINT
    )
    assert _verdict_line(lines2, "ruff") is None, "an unmanifested gate was reported"
    assert _verdict_line(lines2, "typecheck") is not None


# ==========================================================================
# 4. Currency: the bundle fails on RED_ORPHANED and on NOT_RUN (W2, W7)
# ==========================================================================


def test_checkpoint_all_green_passes(gate: PendingContractGate, tmp_path: Path) -> None:
    """POSITIVE CONTROL: the instrument can say yes. A clean tree at ``--checkpoint``
    passes, names every gate, and renders pytest as a real GREEN currency clear (a
    full run) — NOT SCOPED."""
    manifest = _manifest(tmp_path / "m.yaml")
    lines, ok = wave_gate.render_wave_receipt(
        gate, manifest, _results(manifest), mode=wave_gate.MODE_CHECKPOINT
    )
    assert ok, "\n".join(lines)
    pytest_line = _verdict_line(lines, "pytest")
    assert pytest_line is not None
    assert "GREEN" in pytest_line.upper()
    assert "SCOPED" not in pytest_line.upper(), "checkpoint runs pytest FULL, never scoped"


def test_checkpoint_red_orphaned_fails(gate: PendingContractGate, tmp_path: Path) -> None:
    """W7 — the literal #344 concern. A RED_ORPHANED gate (an unowned lint violation,
    zero-tolerance) FAILS the bundle and is named. A wrong build that reads green over
    an orphaned pin is exactly the recurrence this instrument prevents."""
    manifest = _manifest(tmp_path / "m.yaml")
    lines, ok = wave_gate.render_wave_receipt(
        gate, manifest, _results(manifest, ruff="dirty"), mode=wave_gate.MODE_CHECKPOINT
    )
    assert not ok
    assert _verdict_line(lines, "ruff") is not None


def test_claimed_gate_absent_from_results_is_not_run_and_fails(
    gate: PendingContractGate, tmp_path: Path
) -> None:
    """W2 — the LITERAL #344 event: a stage ran a subset and omitted a gate. A gate
    the manifest claims but the run did not execute is ``NOT_RUN`` and FAILS the
    bundle — a subset can never read as an unqualified pass.
    """
    manifest = _manifest(tmp_path / "m.yaml")
    lines, ok = wave_gate.render_wave_receipt(
        gate, manifest, _results(manifest, omit=("ruff",)), mode=wave_gate.MODE_CHECKPOINT
    )
    assert not ok, "an omitted gate must fail the bundle"
    ruff_line = _verdict_line(lines, "ruff")
    assert ruff_line is not None, "the omitted gate must be named, not silently dropped"
    normalised = ruff_line.upper().replace(" ", "_")
    assert "NOT_RUN" in normalised or "NEVER" in normalised, (
        "the omitted gate must be reported as not-run — a subset can never read as a "
        f"pass. Got: {ruff_line!r}"
    )


# ==========================================================================
# 5. Wave posture: pytest scoped honestly; the core stays full (W3, W4, W5)
# ==========================================================================


def test_wave_pytest_scoped_never_green_and_echoes_selector(
    gate: PendingContractGate, tmp_path: Path
) -> None:
    """W3 — the honesty pin. In ``--wave``, the pytest line is marked SCOPED and
    echoes the exact selector, and is NEVER rendered GREEN, even though the scoped
    subset passed. A wave receipt can therefore never claim a pytest currency clear
    from a ``-k`` subset. The non-pytest core still passes for real, so the bundle
    exits ok (the negative control: passing without over-claiming)."""
    manifest = _manifest(tmp_path / "m.yaml")
    selector = ["-k", "test_changed_area"]
    lines, ok = wave_gate.render_wave_receipt(
        gate, manifest, _results(manifest), mode=wave_gate.MODE_WAVE,
        pytest_selector=selector,
    )
    assert ok, "\n".join(lines)
    pytest_line = _verdict_line(lines, "pytest")
    assert pytest_line is not None
    assert "SCOPED" in pytest_line.upper(), "wave pytest must be marked SCOPED"
    assert "GREEN" not in pytest_line.upper(), "a scoped subset must never read GREEN"
    tail = "\n".join(lines)
    assert "-k" in tail and "test_changed_area" in tail, "the exact selector must be echoed"


def test_wave_core_gates_run_full_and_still_fail(
    gate: PendingContractGate, tmp_path: Path
) -> None:
    """W4 — the non-omittable core. In wave mode, typecheck and ruff still run FULL and
    currency-check for real: a typecheck RED_ORPHANED fails the bundle even when the
    scoped pytest is clean, and the typecheck line is NOT marked SCOPED. A build that
    scoped or skipped the core in wave mode would pass a broken tree."""
    manifest = _manifest(tmp_path / "m.yaml")
    lines, ok = wave_gate.render_wave_receipt(
        gate, manifest, _results(manifest, mypy="dirty"), mode=wave_gate.MODE_WAVE,
        pytest_selector=["-k", "test_changed_area"],
    )
    assert not ok, "a real typecheck orphan must fail even a wave run"
    typecheck_line = _verdict_line(lines, "typecheck")
    assert typecheck_line is not None
    assert "SCOPED" not in typecheck_line.upper(), "typecheck is whole-tree, never scoped"


def test_wave_scoped_pytest_failure_fails_the_bundle(
    gate: PendingContractGate, tmp_path: Path
) -> None:
    """A scoped run is not a currency clear, but a FAILURE inside the scoped subset is
    still a real red — a wave run that swallowed its own scoped failures would be
    useless. (Reading flagged in REPORT-contract-g.md: the alternative — 'wave never
    fails on pytest' — would let a regression in the changed suite pass silently.)"""
    manifest = _manifest(tmp_path / "m.yaml")
    lines, ok = wave_gate.render_wave_receipt(
        gate, manifest, _results(manifest, junit="dirty"), mode=wave_gate.MODE_WAVE,
        pytest_selector=["-k", "test_changed_area"],
    )
    assert not ok, "an unregistered failure in the scoped subset must fail the bundle"


def test_scopable_gate_identified_by_reader_not_literal_id(
    gate: PendingContractGate, tmp_path: Path
) -> None:
    """W5 — the DISCRIMINATING fixture. The scopable gate is the one whose reader is
    the junit reader, DERIVED like ``pending_contract_gate._typecheck_gate`` finds the
    mypy gate — not the literal id ``"pytest"``. With the junit gate renamed ``suite``,
    a build keyed on ``id == "pytest"`` would fail to scope it (rendering it GREEN);
    this asserts the ``suite`` line is SCOPED."""
    manifest = _manifest(tmp_path / "m.yaml", junit_id="suite")
    lines, _ = wave_gate.render_wave_receipt(
        gate, manifest, _results(manifest), mode=wave_gate.MODE_WAVE,
        pytest_selector=["-k", "test_changed_area"],
    )
    suite_line = _verdict_line(lines, "suite")
    assert suite_line is not None
    assert "SCOPED" in suite_line.upper(), "the junit gate is scopable by READER, not name"
    assert "GREEN" not in suite_line.upper()


# ==========================================================================
# 6. The scoping decision: only wave scopes pytest (W4's run-side)
# ==========================================================================


def test_pytest_args_for_scopes_only_in_wave_mode() -> None:
    """``--wave`` forwards the selector to the pytest gate's argv; ``--checkpoint``
    forwards nothing (a FULL run). This is the run-side of 'only pytest is scopable':
    the selector reaches the pytest command in wave mode and never in checkpoint."""
    selector = ["-k", "test_changed_area"]
    assert tuple(wave_gate.pytest_args_for(wave_gate.MODE_WAVE, selector)) == tuple(selector)
    assert tuple(wave_gate.pytest_args_for(wave_gate.MODE_CHECKPOINT, selector)) == ()


# ==========================================================================
# 7. The ENTRYPOINT enforces · DRY (one manifest reader) · summary honesty ·
#    ∀ over (mode × gate) · monoculture  — the adversary-g missing pins
#    (MP-1..MP-5), applying design §9 (IDIOM 1/2/3 + companion laws).
#
# WHY THIS SECTION EXISTS. ``REPORT-adversary-g`` graded the sections above and
# found FIVE wrong builds that survive them, one a BLOCKER: a ``main`` that runs
# NO gates and returns 0 (MP-1) — the enforcement point that enforces NOTHING,
# the single worst failure for #344 ("no CI exists, so the bundle IS the
# enforcement point"). The pure renderer was over-tested; the CLI entrypoint,
# never driven on its happy path. These pins drive the REAL ``main`` through a
# gate-runner spy and assert the EFFECT (exit code / routed call), never a proxy.
# ==========================================================================


def _empty_registry() -> PendingContractRegistry:
    """A registry that owns nothing — so a clean tree renders GREEN and any red
    renders RED_ORPHANED, with no dependence on the live ``pending_contracts.yaml``
    (asserting the real registry's health would be asserting the WEATHER)."""
    return PendingContractRegistry(version=1, bounds=())


def _patch_loaders(
    monkeypatch: pytest.MonkeyPatch,
    manifest: GateManifest,
    registry: PendingContractRegistry,
) -> None:
    """Make ``main`` load a CANNED manifest + registry instead of the real
    ``gates.yaml`` / ``pending_contracts.yaml``.

    Patched on the CLASS (``GateManifest.load`` / ``PendingContractRegistry.load``)
    rather than on a module name: a classmethod lives on the shared class object, so
    one ``setattr`` reaches ``main`` whatever import spelling the builder chose — the
    from-import trap (§9.7) cannot bite a class-attribute patch."""
    monkeypatch.setattr(GateManifest, "load", staticmethod(lambda _path: manifest))
    monkeypatch.setattr(
        PendingContractRegistry, "load", staticmethod(lambda _path: registry)
    )


def _install_reader_spy(
    monkeypatch: pytest.MonkeyPatch,
    results_factory: Callable[[GateManifest], dict[str, object]],
) -> list[SimpleNamespace]:
    """Spy ``pending_contract_gate._run_selected_gates`` — the ONE derived leg
    reader (#344 DRY leg-5). Returns the recorded-call list; each call carries the
    ``manifest`` and ``legs`` ``main`` handed the reader, so a caller can assert
    ``main`` inherited the manifest's FULL id set exactly once.

    Installed in BOTH namespaces DELIBERATELY: a ``from pending_contract_gate import
    _run_selected_gates`` (the natural, reference spelling) binds the name into
    ``wave_gate``'s own module dict, which a patch on ``pending_contract_gate`` alone
    would NOT reach (the exact single-module-monkeypatch defect §9.7 names). Patching
    ``wave_gate`` reaches the from-import adopter; patching ``pending_contract_gate``
    reaches a ``pcg._run_selected_gates`` adopter; the SAME spy object records into one
    list either way, so the count is the true number of calls regardless of spelling."""
    calls: list[SimpleNamespace] = []

    def spy(
        runner: object,
        manifest: GateManifest,
        legs: Sequence[str],
        pytest_args: Sequence[str],
    ) -> dict[str, object]:
        calls.append(
            SimpleNamespace(
                manifest=manifest, legs=tuple(legs), pytest_args=tuple(pytest_args)
            )
        )
        return results_factory(manifest)

    monkeypatch.setattr(wave_gate, "_run_selected_gates", spy, raising=False)
    monkeypatch.setattr(_pcg, "_run_selected_gates", spy)
    return calls


def _results_injected(manifest: GateManifest, inject: dict[str, str]) -> dict[str, object]:
    """Canned results with an explicit per-reader injection (``{"ruff": "dirty"}`` …).
    Explicit keywords rather than ``**inject`` so the gate state is a typed choice, not
    an untyped splat mypy cannot check."""
    return _results(
        manifest,
        mypy=inject.get("mypy", "clean"),
        ruff=inject.get("ruff", "clean"),
        junit=inject.get("junit", "clean"),
    )


def _results_with_one_dirty(manifest: GateManifest, dirty_id: str) -> dict[str, object]:
    """Canned results where exactly the gate ``dirty_id`` is RED and the rest clean,
    keyed off the gate's READER so it works whatever the gate is named. (Base manifest
    gates each use a distinct reader, so this dirties exactly the one gate.)"""
    reader = READERS[manifest.gate(dirty_id).reader]
    if reader is MypyOutputReader:
        return _results(manifest, mypy="dirty")
    if reader is RuffOutputReader:
        return _results(manifest, ruff="dirty")
    return _results(manifest, junit="dirty")


# --------------------------------------------------------------------------
# MP-1 (BLOCKER) + MP-2 — the entrypoint enforces, via the ONE manifest reader.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "argv, inject, expect_zero",
    [
        pytest.param(["--checkpoint"], {}, True, id="checkpoint-clean-passes"),
        pytest.param(["--checkpoint"], {"ruff": "dirty"}, False, id="checkpoint-orphan-fails"),
        pytest.param(["--wave", "-k", "x"], {}, True, id="wave-clean-scoped-passes"),
        pytest.param(["--wave", "-k", "x"], {"junit": "dirty"}, False, id="wave-scoped-failure-fails"),
    ],
)
def test_main_exit_code_reflects_the_bundle_verdict(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    argv: list[str],
    inject: dict[str, str],
    expect_zero: bool,
) -> None:
    """MP-1 (BLOCKER) — the entrypoint is the enforcement point (#344: no CI), so it
    is driven on its HAPPY path and its EXIT CODE is asserted — never only the no-mode
    refusal door. A ``main`` that runs no gates and returns 0 unconditionally
    (W-main-noop) fails the orphan/scoped-failure rows: it returns 0 where the bundle
    must be red. The gate execution is a spy, so nothing shells out to the real gates.
    """
    manifest = _manifest(tmp_path / "m.yaml")
    _patch_loaders(monkeypatch, manifest, _empty_registry())
    _install_reader_spy(monkeypatch, lambda used: _results_injected(used, inject))
    code = wave_gate.main(argv)
    assert (code == 0) is expect_zero, (
        f"main({argv!r}) returned {code}; a bundle with inject={inject!r} must "
        f"{'pass' if expect_zero else 'FAIL'} — the entrypoint must enforce the "
        "verdict, not swallow it (MP-1)."
    )


def test_main_routes_through_the_one_manifest_reader(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """MP-2 (DRY leg-5, priority #1) — ``main`` inherits the manifest by routing
    through ``pending_contract_gate._run_selected_gates`` exactly ONCE with the FULL
    derived leg set (``manifest.ids``). A ``main`` that re-parses ``gates.yaml`` and
    builds its own leg list (W-DRY-reparse) never calls the reader — the spy records
    zero calls — and a ``main`` that runs no gates (W-main-noop) records zero too.
    Two readers of one manifest is the #102/#120 two-sources-of-truth trap."""
    manifest = _manifest(tmp_path / "m.yaml")
    _patch_loaders(monkeypatch, manifest, _empty_registry())
    calls = _install_reader_spy(monkeypatch, _results)
    code = wave_gate.main(["--checkpoint"])
    assert code == 0, "a clean canned tree must pass at checkpoint"
    assert len(calls) == 1, (
        f"main must route through the ONE manifest reader exactly once; the spy "
        f"recorded {len(calls)} call(s). Zero means main re-parsed the manifest "
        "itself or ran no gates (MP-2)."
    )
    assert calls[0].legs == tuple(manifest.ids), (
        "main must hand the reader the manifest's FULL id set (the derived leg set), "
        f"not a private subset; got {calls[0].legs!r} vs manifest {tuple(manifest.ids)!r}."
    )


def _is_yaml_load_call(node: ast.AST) -> bool:
    """A ``yaml.safe_load(...)`` / ``yaml.load(...)`` / ``yaml.full_load(...)`` call —
    the shape a second, private manifest reader takes."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr in {"safe_load", "load", "full_load", "unsafe_load"}
        and isinstance(func.value, ast.Name)
        and func.value.id == "yaml"
    )


def test_wave_gate_does_not_reparse_the_manifest_itself() -> None:
    """MP-2 belt — the spy above proves ``main`` CALLS the shared reader; this proves
    it does not ALSO hand-roll a second one. A ``yaml.safe_load`` of the manifest in
    ``wave_gate.py`` is a private reader that skips ``GateManifest.load``'s pydantic
    validation, the reader-allowlist and the anti-vacuity guards — #312's exact door,
    which the spy alone cannot see once a build routes correctly AND re-parses."""
    module_file = wave_gate.__file__
    assert module_file is not None, "wave_gate must be a real on-disk module"
    tree = ast.parse(Path(module_file).read_text())
    offenders = [node for node in ast.walk(tree) if _is_yaml_load_call(node)]
    assert not offenders, (
        f"wave_gate.py parses YAML directly ({len(offenders)} call(s)) — that is a "
        "SECOND manifest reader. Route through GateManifest.load / _run_selected_gates; "
        "re-parse nothing (MP-2, #102/#120/#312)."
    )


# --------------------------------------------------------------------------
# MP-3 — SUMMARY HONESTY (IDIOM 3): a scoped leg can never render an
# unqualified full-currency pass, at the SUMMARY, not just the per-gate line.
# --------------------------------------------------------------------------


def test_wave_scoped_summary_never_reads_as_a_full_currency_clear(
    gate: PendingContractGate, tmp_path: Path
) -> None:
    """MP-3 (TRUST, priority #2) — the #306/#312 false-clear reproduced at the SUMMARY.
    ``test_wave_pytest_scoped_never_green_and_echoes_selector`` pins only the per-gate
    pytest LINE; a build can relabel that line honestly SCOPED yet keep
    ``_render_currency``'s over-claiming summary (W-B, the path of least resistance).

    The forbidden token is DERIVED from the machinery, not hand-typed: whatever
    unqualified-pass line ``_render_currency`` emits on an all-green run is exactly what
    a wave-scoped receipt must NOT contain. Both directions are checked — a genuinely
    clean FULL run (checkpoint) IS allowed the unqualified clear (control), while a
    SCOPED wave run is not — so a build that always-omits fails the control and a build
    that always-includes (W-B) fails the pin."""
    manifest = _manifest(tmp_path / "m.yaml")

    # DERIVE the unqualified-pass token from the wrapped machinery's own all-green run.
    currency_lines, currency_ok = _render_currency(
        gate, manifest, cast(_GateResults, _results(manifest))
    )
    assert currency_ok, "the machinery's own all-green currency must pass (control)"
    pass_tokens = [
        line.strip()
        for line in currency_lines
        if "PASS" in line.upper() and "GREEN" in line.upper()
    ]
    assert pass_tokens, "expected an unqualified currency-PASS token to exist to forbid"
    over_claim = pass_tokens[0]

    # CONTROL — a full CHECKPOINT run legitimately reads as an unqualified pass.
    checkpoint_lines, checkpoint_ok = wave_gate.render_wave_receipt(
        gate, manifest, _results(manifest), mode=wave_gate.MODE_CHECKPOINT
    )
    assert checkpoint_ok
    assert any("every claimed gate is GREEN" in line for line in checkpoint_lines), (
        "a clean full checkpoint run must be ALLOWED to read as an unqualified "
        "currency clear — else this pin is a blanket ban, not an honesty check."
    )

    # THE PIN — a wave receipt with a SCOPED pytest can never carry that clear.
    wave_lines, wave_ok = wave_gate.render_wave_receipt(
        gate, manifest, _results(manifest), mode=wave_gate.MODE_WAVE,
        pytest_selector=["-k", "test_changed_area"],
    )
    assert wave_ok, "\n".join(wave_lines)  # core clean, scoped subset passed
    joined = "\n".join(wave_lines)
    assert over_claim not in joined, (
        f"the wave-scoped receipt over-claims: it carries {over_claim!r}, the "
        "machinery's unqualified full-currency clear, while pytest ran only a subset."
    )
    assert "every claimed gate is GREEN" not in joined, (
        "a wave-scoped receipt must never assert every gate is GREEN — pytest was "
        "SCOPED, so the full run is still owed (MP-3)."
    )


# --------------------------------------------------------------------------
# MP-4 — the fail-matrix ranges over EVERY (mode × gate) cell, DERIVED live
# from the manifest (IDIOM 1 ∀). The wave×ruff orphan cell currently slips.
# --------------------------------------------------------------------------


def _canonical_manifest_ids() -> tuple[str, ...]:
    """The gate-id surface, DERIVED live from the canned manifest the fixtures use —
    NOT a hand-typed list. A gate added to ``_manifest`` grows this automatically, so
    the parametrization below cannot silently under-cover (the §9.1 META-RECURSION: the
    ∀'s reach is a checked variable, re-derived from production truth, never a constant)."""
    with tempfile.TemporaryDirectory() as work_dir:
        return _manifest(Path(work_dir) / "surface.yaml").ids


_FAIL_MATRIX_GATES = _canonical_manifest_ids()


def test_fail_matrix_gate_set_equals_the_live_manifest(
    gate: PendingContractGate, tmp_path: Path
) -> None:
    """COVERAGE AS A CHECKED VARIABLE (both-direction diff, the ``_DECLARED_SITES``
    shape). The set of gates the fail-matrix drives MUST equal the manifest's gate set;
    grow the manifest and the matrix must grow or this reddens, and a matrix that names
    a gate the manifest does not have is a stale declaration. This is what stops the
    ∀ below from degenerating into a hand-list wearing a loop (§9.1)."""
    manifest = _manifest(tmp_path / "m.yaml")
    live = set(manifest.ids)
    declared = set(_FAIL_MATRIX_GATES)
    missing = live - declared
    undeclared = declared - live
    assert not missing, f"manifest gates the fail-matrix never drives: {sorted(missing)}"
    assert not undeclared, (
        f"fail-matrix cells for gates absent from the manifest: {sorted(undeclared)}"
    )
    assert declared, "the fail-matrix must not be empty (fail-closed)"


@pytest.mark.parametrize("dirty_id", _FAIL_MATRIX_GATES)
def test_every_mode_gate_cell_fails_on_a_red(
    gate: PendingContractGate, tmp_path: Path, dirty_id: str
) -> None:
    """MP-4 — ∀ over (mode × gate): a RED in ANY gate fails the bundle in EITHER mode,
    and a non-omittable CORE gate (anything but the scopable junit gate) is NEVER marked
    SCOPED. W4 above drives only the (wave, typecheck) cell; the (wave, ruff) cell slips,
    so a build that treats ruff as advisory/scopable in wave mode reads GREEN over an
    orphaned lint violation. Driving every cell closes that — the invariant is uniform:
    a dirty gate is a red, whether an orphaned core red or a scoped-subset failure."""
    manifest = _manifest(tmp_path / "m.yaml")
    results = _results_with_one_dirty(manifest, dirty_id)
    is_scopable = READERS[manifest.gate(dirty_id).reader] is JUnitReportReader
    for mode in (wave_gate.MODE_WAVE, wave_gate.MODE_CHECKPOINT):
        extra = {"pytest_selector": ["-k", "x"]} if mode == wave_gate.MODE_WAVE else {}
        lines, ok = wave_gate.render_wave_receipt(
            gate, manifest, results, mode=mode, **extra
        )
        assert not ok, (
            f"a red {dirty_id!r} in {mode!r} mode must FAIL the bundle — no gate is "
            "advisory, and the scopable gate's own subset failures still fail (MP-4)."
        )
        if not is_scopable:
            line = _verdict_line(lines, dirty_id)
            assert line is not None, f"{dirty_id} must be named in {mode} mode"
            assert "SCOPED" not in line.upper(), (
                f"{dirty_id!r} is non-omittable core — it runs FULL and is never "
                f"marked SCOPED, not even in wave mode. Got: {line!r}"
            )


# --------------------------------------------------------------------------
# MP-5 — the selector echo is proven with ≥2 DISTINCT values (P2 monoculture):
# a build that hardcodes the echoed selector cannot match a second value.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "selector_value",
    ["test_changed_area", "test_totally_different_area", "not (slow or flaky)"],
)
def test_wave_scoped_selector_echo_equals_the_source(
    gate: PendingContractGate, tmp_path: Path, selector_value: str
) -> None:
    """MP-5 — the receipt must echo the EXACT selector it was handed, proven with
    ≥2 distinct values. The existing echo pin uses one value (``test_changed_area``),
    so a build that HARDCODES ``-k test_changed_area`` in the SCOPED line passes it
    while LYING about which subset ran (W-echo). With a second, distinctive value the
    hardcode cannot match: ``echoed == source`` (§9.4 monoculture)."""
    manifest = _manifest(tmp_path / "m.yaml")
    selector = ["-k", selector_value]
    lines, _ = wave_gate.render_wave_receipt(
        gate, manifest, _results(manifest), mode=wave_gate.MODE_WAVE,
        pytest_selector=selector,
    )
    joined = "\n".join(lines)
    assert " ".join(selector) in joined, (
        f"the receipt must echo the exact selector {' '.join(selector)!r}; a hardcoded "
        f"echo cannot match this value. Receipt:\n{joined}"
    )
    assert selector_value in joined
