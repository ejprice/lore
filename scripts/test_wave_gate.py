"""Contract for ``scripts/wave_gate.py`` — the non-omittable gate bundle
(finding #344), in the OPERATOR-SIMPLIFIED form.

⚠ **RED UNTIL BUILT.** ``scripts/wave_gate.py`` does not exist as of this contract.
``importlib.import_module("wave_gate")`` below raises ``ModuleNotFoundError`` at
COLLECTION, so every test in this file errors until a builder creates the module.
That is the intended contract-first RED — the pin authored before the code.

──────────────────────────────────────────────────────────────────────────────
WHY THIS EXISTS (finding #344, measured 2026-08-09).
──────────────────────────────────────────────────────────────────────────────
05a-i reproduced #306/#312 a THIRD time: a stage ran a HAND-LISTED gate subset
(typecheck + ruff + the 4 contract suites) and **omitted**
``pending_contract_gate.py --currency``. Eight RED_ORPHANED structural pins the
diff introduced went unseen for two cycles until a cold audit ran currency. Root
cause: *"the gates"* is a hand-list re-typed in each spawn brief, and hand-lists
drift and omit — the enumeration antipattern this repo has the most receipts
against.

``scripts/gates.yaml`` is ALREADY the gate authority, and
``pending_contract_gate.py`` ALREADY derives its leg set from it and fails
``VERDICT_NOT_RUN`` on any omitted manifested gate. The gap #344 names is one
level up: there is no single ENTRYPOINT a brief can point at instead of
re-listing gates. ``wave_gate.py`` is that entrypoint. No CI exists (#285), so
the bundle IS the enforcement point.

──────────────────────────────────────────────────────────────────────────────
THE OPERATOR-SIMPLIFIED DESIGN (2026-08-10 — design doc §13; supersedes the
§11.8–§11.11 typed-WaveReceipt / conduit-equality / branch-coverage /
per-axis byte-oracle machinery, all RETIRED). ``wave_gate.py`` behaviour:
──────────────────────────────────────────────────────────────────────────────
  B1. **No ``--wave``** → the FULL suite runs (default). typecheck + ruff +
      currency run FULL; pytest runs FULL (no selector). ``--checkpoint`` is
      REMOVED — there is no second mode constant.
  B2. **``--wave <args>`` (≥1 arg)** → the non-omittable core (typecheck + ruff
      + currency) still runs FULL; ONLY the pytest leg is short-circuited to
      ``<args>`` (pytest node-ids / paths forwarded verbatim — no ``-k``). The
      receipt carries an honest **SCOPED-RUN flag** — "SCOPED RUN — ran {args}
      (N tests); does NOT certify the full gate" — echoing the EXACT args + the
      collected/passed COUNT, and the pytest currency line is marked SCOPED,
      never GREEN. A scoped receipt can therefore never read as a full pass.
  B3. **``--wave`` with NO args** → ERROR.
  B4. **``--wave <args>`` that collect ZERO tests** → ERROR (no silent
      scoped-pass over nothing — the #290 anti-vacuity class). Zero collection
      surfaces as a ``BrokenInstrumentError`` through the existing anti-vacuity
      (JUnitReportReader total==0 / GateRunner exit-5), which the bundle
      inherits and must NOT swallow into a pass.

Honesty here is the SCOPED-RUN flag + the two errors — NOT a byte-oracle
fortress. This contract asserts exactly the four behaviours, the non-omittable
core invariant, and the honest flag, then STOPS (operator: right-size).

──────────────────────────────────────────────────────────────────────────────
THE CONTRACT SURFACE (deliberately minimal). The one mandated public name:
──────────────────────────────────────────────────────────────────────────────
  * ``main(argv=None) -> int`` — the CLI entrypoint AND the enforcement point.
Everything else (how the mode is decided, how the receipt is rendered) is the
builder's to choose; the behaviours are observed through ``main`` + its served
receipt + a spy on the ONE gate reader it must route through.

The architecture this presupposes is IN-PROCESS composition of
``pending_contract_gate``'s machinery — ``GateManifest.load`` /
``PendingContractRegistry.load`` for inputs, ``_run_selected_gates`` as the ONE
derived leg-runner, and the currency verdict logic — NOT a stdout-parsing
subprocess wrapper, because the SCOPED-not-GREEN override needs structured
access to the pytest currency verdict (flagged to the lead in
REPORT-contract-g-simple.md).

──────────────────────────────────────────────────────────────────────────────
⚠ WHAT WRONG BUILD WOULD STILL PASS THIS? — asked of every fixture, because a
gate bundle is exactly the shape that reads green while proving nothing.

  W1. ``main`` runs NO gates and returns 0 (the enforcement point that enforces
      NOTHING — #344's single worst failure). Killed by
      ``test_main_routes_through_the_one_reader_full`` (the spy must record one
      call) + every ``test_main_fails_on_a_core_red`` row (a build that runs
      nothing returns 0 where the bundle must be red).
  W2. ``--wave`` scopes the CORE too (typecheck / ruff treated as scopable).
      Killed by ``test_wave_scopes_only_pytest_and_core_stays_full`` (the reader
      is handed the FULL manifest id set as legs, and the selector only ever
      reaches ``pytest_args``) + the WAVE-mode core-red rows.
  W3. A hardcoded gate tuple ``("typecheck","ruff","pytest")`` that does not
      track the manifest — #312's exact defect. Killed by
      ``test_no_hardcoded_gate_id_collection`` (AST) +
      ``test_wave_gate_inherits_the_full_manifest_id_set`` (a 4-gate manifest;
      a hardcoded 3-list cannot grow).
  W4. ``main`` re-parses ``gates.yaml`` itself — a second manifest reader that
      skips validation/allowlist/anti-vacuity. Killed by
      ``test_wave_gate_does_not_reparse_the_manifest``.
  W5. A scoped pytest rendered GREEN (over-claiming a currency clear from a
      subset). Killed by ``test_scoped_receipt_is_unmistakably_scoped`` +
      ``test_full_run_pytest_is_a_real_currency_clear`` (the paired control).
  W6. A scoped receipt with no flag / a hardcoded arg list / a hardcoded count
      (a scoped run that reads like a full pass, or lies about what it ran).
      Killed by ``test_scoped_flag_echoes_the_exact_args`` (two arg sets) and
      ``test_scoped_flag_echoes_the_actual_test_count`` (two counts).
  W7. A core red (RED_ORPHANED or NOT_RUN) treated as advisory in EITHER mode —
      the #344 disease AT the enforcement point. Killed by
      ``test_main_fails_on_a_core_red`` over (mode × gate × {dirty, omitted}).
  W8. ``--wave`` alone silently runs full; or a zero-collection scoped run
      silently passes; or the removed ``--checkpoint`` still works. Killed by
      ``test_wave_with_no_args_is_an_error`` / ``test_wave_zero_collection_is_
      an_error`` / ``test_removed_checkpoint_mode_is_rejected``.

⚠ EVERY FIXTURE HERE IS CANNED DATA. Nothing shells out to the real gates or
reads the real ``gates.yaml``: a contract that depended on the live tree would
assert the WEATHER, not the INSTRUMENT, and go red every time an unrelated
packet landed (the discipline ``test_pending_contract_gate.py`` states). Gate
EXECUTION is a spy on ``_run_selected_gates``; gate OUTPUT is built with the
real readers so a fixture cannot encode a shape mypy/ruff/pytest never emit.
"""

from __future__ import annotations

import ast
import importlib
import os
import sys
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# The machinery the bundle WRAPS — real, existing types. The contract builds its
# canned gate results with the same readers the runner uses in production, so a
# fixture cannot encode a shape the real readers never emit.
import pending_contract_gate as _pcg  # noqa: E402  (module handle for from-import-reaching spies)
from pending_contract_gate import (  # noqa: E402
    READERS,
    BrokenInstrumentError,
    GateManifest,
    JUnitReportReader,
    MypyOutputReader,
    PendingContractRegistry,
    RuffOutputReader,
)

# The module under contract. RED now: it does not exist, so this raises
# ``ModuleNotFoundError`` at collection — the intended contract-first RED.
# Acquired via ``importlib`` (not a static ``import wave_gate``) DELIBERATELY: a
# static import would need ``# type: ignore[import-not-found]`` today, and strict
# mypy's ``warn_unused_ignores`` would then redden that ignore as UNUSED the
# moment the builder creates the module — a latent orphaned red the contract must
# not plant. The dynamic form types every attribute as ``Any`` (measured), so it
# stays mypy-clean in BOTH states and couples the builder to nothing.
wave_gate = importlib.import_module("wave_gate")


# ==========================================================================
# Canned gate output — real reader shapes. ``_attr_error`` / ``_mypy_output`` /
# ``_junit`` mirror ``test_pending_contract_gate.py``'s builders (a synthetic
# message shape is how a reader passes its tests and misses production output).
# ==========================================================================

_PROBE_FILE = "loremaster/tests/test_probe.py"


def _attr_error(path: str, line: int, owner: str, attribute: str) -> str:
    return (
        f'{path}:{line}: error: Module "{owner}" has no attribute '
        f'"{attribute}"  [attr-defined]'
    )


def _mypy_output(error_lines: list[str]) -> str:
    """A full ``typecheck.sh`` transcript wrapping ``error_lines``. The summary
    total is DERIVED from the lines so a fixture cannot encode a count mismatch
    the reader would reject."""
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
# Manifest / results / registry fixtures — canned, self-contained.
# ==========================================================================


def _manifest(path: Path, *, extra: bool = False) -> GateManifest:
    """A ``gates.yaml``-shaped manifest written under ``path``.

    ``extra`` adds a fourth gate so a build that hardcodes a 3-list can be caught
    failing to grow (the manifest-derivation mutation proof, W3).
    """
    gates: list[tuple[str, str, str, list[str]]] = [
        ("typecheck", "typecheck_transcript", "pending-contracts", ["./scripts/typecheck.sh"]),
        ("ruff", "ruff", "none", ["uv", "run", "ruff", "check", "."]),
        (
            "pytest",
            "pytest_junit",
            "pending-contracts",
            ["uv", "run", "pytest", "-q", "--junit-xml={junit_xml}"],
        ),
    ]
    if extra:
        gates.append(("extra", "ruff", "none", ["true"]))
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
    junit_pass: int = 1,
    omit: tuple[str, ...] = (),
) -> dict[str, object]:
    """Canned per-gate results keyed by gate id, built BY READER — so it works
    whatever the junit gate is named. ``junit_pass`` sets the number of passing
    tests (so the SCOPED-RUN count can be driven); ``omit`` drops a gate entirely
    (it was never run → NOT_RUN)."""
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
            if junit == "clean":
                cases = [(_PROBE_FILE, f"test_ok_{index}", False) for index in range(junit_pass)]
            else:
                cases = [(_PROBE_FILE, "test_bad", True)]
            out[spec.id] = JUnitReportReader.read(_junit(cases))
    return out


def _results_with_one_dirty(manifest: GateManifest, dirty_id: str) -> dict[str, object]:
    """Canned results where exactly the gate ``dirty_id`` is RED and the rest
    clean, keyed off the gate's READER so it works whatever the gate is named.
    (The base manifest's three gates each use a distinct reader.)"""
    reader = READERS[manifest.gate(dirty_id).reader]
    if reader is MypyOutputReader:
        return _results(manifest, mypy="dirty")
    if reader is RuffOutputReader:
        return _results(manifest, ruff="dirty")
    return _results(manifest, junit="dirty")


def _empty_registry() -> PendingContractRegistry:
    """A registry that owns nothing — so a clean tree renders GREEN and any red
    renders RED_ORPHANED, with no dependence on the live ``pending_contracts.yaml``
    (asserting the real registry's health would be asserting the WEATHER)."""
    return PendingContractRegistry(version=1, bounds=())


# ==========================================================================
# Driving ``main`` against canned inputs, with a spy on the ONE gate reader.
# ==========================================================================


def _patch_loaders(
    monkeypatch: pytest.MonkeyPatch,
    manifest: GateManifest,
    registry: PendingContractRegistry,
) -> None:
    """Make ``main`` load a CANNED manifest + registry instead of the real
    ``gates.yaml`` / ``pending_contracts.yaml``.

    Patched on the CLASS (``GateManifest.load`` / ``PendingContractRegistry.load``)
    rather than a module name: a classmethod lives on the shared class object, so
    one ``setattr`` reaches ``main`` whatever import spelling the builder chose."""
    monkeypatch.setattr(GateManifest, "load", staticmethod(lambda _path: manifest))
    monkeypatch.setattr(
        PendingContractRegistry, "load", staticmethod(lambda _path: registry)
    )


def _install_reader_spy(
    monkeypatch: pytest.MonkeyPatch,
    results_factory: Callable[[GateManifest], dict[str, object]],
) -> list[SimpleNamespace]:
    """Spy ``pending_contract_gate._run_selected_gates`` — the ONE derived
    leg-runner (#344 DRY). Returns the recorded-call list; each call carries the
    ``legs`` and ``pytest_args`` ``main`` handed the runner, so a caller can
    assert the bundle inherited the manifest's FULL id set and scoped ONLY pytest.

    Installed in BOTH namespaces DELIBERATELY: a ``from pending_contract_gate
    import _run_selected_gates`` binds the name into ``wave_gate``'s own module
    dict, which a patch on ``pending_contract_gate`` alone would not reach.
    Patching ``wave_gate`` reaches the from-import adopter; patching
    ``pending_contract_gate`` reaches a ``pcg._run_selected_gates`` adopter; the
    SAME spy records into one list either way. The call is recorded BEFORE
    ``results_factory`` runs, so a factory that RAISES (the zero-collection case)
    still leaves a record."""
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


def _main_exit_code(argv: list[str]) -> int:
    """``main``'s effective exit code, whether it returns an int, argparse-exits
    (``SystemExit``), or propagates a ``BrokenInstrumentError`` (which the shell
    would see as a non-zero exit). Models what a caller of the script observes."""
    try:
        return int(wave_gate.main(argv))
    except SystemExit as exit_error:
        code = exit_error.code
        if code is None:
            return 0
        return code if isinstance(code, int) else 1
    except BrokenInstrumentError:
        return 2


# ``  manifest   : (...)`` repeats every gate id inside a tuple repr; a per-gate
# lookup must skip it. Excluded by its OWN SHAPE (leading word ``manifest``), not
# by the mere presence of the word anywhere on a line.
def _gate_line(lines: list[str], gate_id: str) -> str | None:
    """The receipt line reporting ``gate_id``'s verdict (its leading token is the
    gate id), or None. Skips the manifest roster header."""
    for line in lines:
        if line.lstrip().startswith("manifest"):
            continue
        parts = line.strip().split()
        if parts and parts[0].rstrip(":") == gate_id:
            return line
    return None


def _scoped_flag_line(lines: list[str]) -> str | None:
    """The SCOPED-RUN flag line, or None."""
    matches = [line for line in lines if "SCOPED RUN" in line.upper()]
    return matches[0] if matches else None


# ==========================================================================
# 0. Contract surface
# ==========================================================================


def test_module_exposes_main() -> None:
    """One clear failure if the mandated seam is absent, rather than an opaque
    error deeper in a driven test."""
    assert hasattr(wave_gate, "main"), "wave_gate must expose main(argv=None) -> int"


# ==========================================================================
# 1. DRY / non-omittable core: main routes through the ONE derived leg-runner,
#    handing it the FULL manifest id set; ONLY pytest is scopable (B1, B2, W1, W2)
# ==========================================================================


def test_main_routes_through_the_one_reader_full(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """B1 run-side + W1. With no ``--wave``, ``main`` runs the FULL suite: it
    routes through ``_run_selected_gates`` exactly ONCE, with the manifest's FULL
    derived id set as ``legs`` and an EMPTY ``pytest_args`` (a full pytest run,
    not a subset). A ``main`` that runs no gates records zero calls (W1); one that
    re-lists a private leg set hands the reader the wrong legs."""
    manifest = _manifest(tmp_path / "m.yaml")
    _patch_loaders(monkeypatch, manifest, _empty_registry())
    calls = _install_reader_spy(monkeypatch, _results)
    assert _main_exit_code([]) == 0, "a clean canned tree must pass in full mode"
    assert len(calls) == 1, (
        f"main must route through the ONE leg-runner exactly once; the spy "
        f"recorded {len(calls)} call(s). Zero means main ran no gates (W1)."
    )
    assert calls[0].legs == tuple(manifest.ids), (
        "main must hand the runner the manifest's FULL derived id set, not a "
        f"private subset; got {calls[0].legs!r} vs manifest {tuple(manifest.ids)!r}."
    )
    assert calls[0].pytest_args == (), "no --wave must run pytest FULL (no selector)"


def test_wave_scopes_only_pytest_and_core_stays_full(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """B2 run-side + W2 + the no-``-k`` pass-through. In ``--wave`` mode the core
    (typecheck + ruff + currency over ALL gates) still runs FULL — the runner is
    handed the manifest's FULL id set as ``legs`` — and the selector reaches ONLY
    ``pytest_args``, VERBATIM (node-ids/paths, no ``-k`` inserted). Because
    ``_run_selected_gates`` forwards ``pytest_args`` only to the junit-reader
    gate, this proves 'only pytest is scopable' without the bundle naming pytest."""
    manifest = _manifest(tmp_path / "m.yaml")
    _patch_loaders(monkeypatch, manifest, _empty_registry())
    calls = _install_reader_spy(monkeypatch, lambda used: _results(used, junit_pass=5))
    selector = ["loremaster/tests/test_changed.py", "loremaster/tests/test_area.py"]
    assert _main_exit_code(["--wave", *selector]) == 0
    assert len(calls) == 1
    assert calls[0].legs == tuple(manifest.ids), (
        "the non-omittable core must run FULL in wave mode: the runner gets the "
        f"whole manifest id set, not a scoped subset. Got {calls[0].legs!r}."
    )
    assert calls[0].pytest_args == tuple(selector), (
        "the selector must reach pytest_args VERBATIM (pass-through, no -k); got "
        f"{calls[0].pytest_args!r} vs {tuple(selector)!r}."
    )


def test_wave_gate_inherits_the_full_manifest_id_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """W3 behavioral mutation proof: a gate ADDED to the manifest reaches the
    runner. A build that hardcodes ``("typecheck","ruff","pytest")`` cannot grow;
    a build that derives ``legs`` from the manifest does."""
    manifest = _manifest(tmp_path / "four.yaml", extra=True)
    _patch_loaders(monkeypatch, manifest, _empty_registry())
    calls = _install_reader_spy(monkeypatch, _results)
    assert _main_exit_code([]) == 0
    assert calls[0].legs == tuple(manifest.ids)
    assert "extra" in calls[0].legs, "a manifested gate was dropped — legs is a hand-list (W3)"


# ==========================================================================
# 2. DRY structural belts: no hardcoded gate set, no second manifest reader
#    (W3, W4 — the #312 doors an AST scan closes that the spy alone cannot)
# ==========================================================================


def _string_collection_literals(tree: ast.AST) -> list[list[str]]:
    """Every ``(...)`` / ``[...]`` / ``{...}`` literal whose elements are ALL
    string constants — the shape a hand-listed gate set takes."""
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
    """W3 (#312's exact defect): a hand-maintained tuple of the gate set, which
    the first draft of ``pending_contract_gate`` itself shipped (missing its ruff
    leg). ``wave_gate`` must name NO gate set of its own — it derives from the
    manifest.

    BOUND: this catches a literal COLLECTION co-naming the canonical gate ids. The
    'legs tracks the manifest' proof is behavioral
    (``test_wave_gate_inherits_the_full_manifest_id_set``); this structural pin is
    the belt to that braces, matching the ``test_anchored_pattern_seam`` idiom.
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
        f"wave_gate.py contains a literal collection of gate ids {offenders} — "
        "that is #312's hand-list. Derive the gate set from the GateManifest."
    )


def _is_yaml_load_call(node: ast.AST) -> bool:
    """A ``yaml.safe_load(...)`` / ``yaml.load(...)`` / ``yaml.full_load(...)``
    call — the shape a second, private manifest reader takes."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr in {"safe_load", "load", "full_load", "unsafe_load"}
        and isinstance(func.value, ast.Name)
        and func.value.id == "yaml"
    )


def test_wave_gate_does_not_reparse_the_manifest() -> None:
    """W4 — the spy proves ``main`` CALLS the shared runner; this proves it does
    not ALSO hand-roll a second manifest reader. A ``yaml.safe_load`` of the
    manifest in ``wave_gate.py`` skips ``GateManifest.load``'s pydantic
    validation, the reader-allowlist and the anti-vacuity guards — #312's exact
    door, invisible to the spy once a build routes correctly AND re-parses."""
    module_file = wave_gate.__file__
    assert module_file is not None, "wave_gate must be a real on-disk module"
    tree = ast.parse(Path(module_file).read_text())
    offenders = [node for node in ast.walk(tree) if _is_yaml_load_call(node)]
    assert not offenders, (
        f"wave_gate.py parses YAML directly ({len(offenders)} call(s)) — that is a "
        "SECOND manifest reader. Route through GateManifest.load; re-parse nothing."
    )


# ==========================================================================
# 3. The enforcement point enforces: a core red fails in EITHER mode (W7)
#
# The non-omittable core, right-sized: a RED_ORPHANED (dirty) or NOT_RUN
# (omitted) on ANY manifested gate fails the bundle in BOTH full and wave mode.
# The gate axis is DERIVED live from the canned manifest (not a hand-typed list),
# so growing the manifest grows the matrix. In wave mode this is the headline
# #344 property: the core is never advisory just because pytest is scoped — a
# typecheck/ruff orphan still fails, AND a scoped pytest with real failures still
# fails (SCOPED downgrades GREEN, never a genuine red).
# ==========================================================================


def _canonical_manifest_ids() -> tuple[str, ...]:
    """The gate-id surface, DERIVED live from the canned manifest — not a
    hand-typed list. A gate added to ``_manifest`` grows this automatically."""
    with tempfile.TemporaryDirectory() as work_dir:
        return _manifest(Path(work_dir) / "surface.yaml").ids


_MATRIX_GATES = _canonical_manifest_ids()
_MATRIX_MODES: tuple[tuple[str, list[str]], ...] = (
    ("full", []),
    ("wave", ["--wave", "loremaster/tests/test_changed.py"]),
)
_FAILURE_MODES = ("dirty", "omitted")


@pytest.mark.parametrize("gate_id", _MATRIX_GATES)
@pytest.mark.parametrize("failure_mode", _FAILURE_MODES)
@pytest.mark.parametrize("mode_label, argv", _MATRIX_MODES)
def test_main_fails_on_a_core_red(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mode_label: str,
    argv: list[str],
    failure_mode: str,
    gate_id: str,
) -> None:
    """W7. Over (mode × gate × {dirty, omitted}): a red gate fails the bundle,
    in BOTH modes. ``dirty`` → RED_ORPHANED (an unowned residual, empty registry);
    ``omitted`` → NOT_RUN (a subset can never read as a pass). A build that treats
    a core red as advisory in either mode — or that swallows a scoped pytest
    failure — returns 0 and is caught here."""
    manifest = _manifest(tmp_path / "m.yaml")
    _patch_loaders(monkeypatch, manifest, _empty_registry())

    if failure_mode == "dirty":
        def factory(used: GateManifest) -> dict[str, object]:
            return _results_with_one_dirty(used, gate_id)
    else:
        def factory(used: GateManifest) -> dict[str, object]:
            return _results(used, omit=(gate_id,))
    _install_reader_spy(monkeypatch, factory)

    code = _main_exit_code(argv)
    assert code != 0, (
        f"main({argv!r}) with {gate_id!r} {failure_mode} returned {code}; a core "
        "red must fail the bundle in every mode — the enforcement point must "
        "enforce it, not swallow it (W7, #344)."
    )


@pytest.mark.parametrize("mode_label, argv", _MATRIX_MODES)
def test_main_passes_a_clean_tree(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mode_label: str, argv: list[str]
) -> None:
    """POSITIVE CONTROL: the instrument can say yes. A clean canned tree exits 0
    in both modes — in wave mode WITHOUT ever claiming a pytest currency clear
    (asserted by the scoped-flag pins below)."""
    manifest = _manifest(tmp_path / "m.yaml")
    _patch_loaders(monkeypatch, manifest, _empty_registry())
    _install_reader_spy(monkeypatch, lambda used: _results(used, junit_pass=4))
    assert _main_exit_code(argv) == 0


# ==========================================================================
# 4. The SCOPED-RUN honesty flag (B2) — a scoped run is un-mistakable for a full
#    pass; it echoes the exact args + the count; the pytest line is never GREEN.
#    Positive control + its paired negative control (full run) (W5, W6)
# ==========================================================================


def test_scoped_receipt_is_unmistakably_scoped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """B2 honesty (W5, W6) — the positive control. A clean ``--wave`` run passes
    (exit 0) but the receipt an LLM reads makes it un-mistakable for a full pass:
    a SCOPED-RUN flag echoing the exact args + the count, a disclaimer that it
    does NOT certify the full gate, and a pytest currency line that is NEVER
    GREEN. Passing WITHOUT over-claiming a pytest currency clear."""
    manifest = _manifest(tmp_path / "m.yaml")
    _patch_loaders(monkeypatch, manifest, _empty_registry())
    _install_reader_spy(monkeypatch, lambda used: _results(used, junit_pass=6))
    selector = ["loremaster/tests/test_changed.py"]
    code = _main_exit_code(["--wave", *selector])
    captured = capsys.readouterr()
    lines = (captured.out + captured.err).splitlines()

    assert code == 0, "\n".join(lines)
    flag = _scoped_flag_line(lines)
    assert flag is not None, "a scoped run must carry a SCOPED-RUN flag; found none"
    assert selector[0] in flag, "the flag must echo the exact args"
    assert "6" in flag, "the flag must echo the collected/passed count"
    assert "does not certify the full" in flag.lower(), (
        "the flag must state it does NOT certify the full gate — an LLM reading "
        "the tail must see what this run does not prove"
    )
    pytest_line = _gate_line(lines, "pytest")
    assert pytest_line is not None, "the pytest gate must still be reported in wave mode"
    assert "GREEN" not in pytest_line.upper(), (
        "a scoped pytest subset must NEVER render GREEN — that is a currency "
        f"clear it did not earn. Got: {pytest_line!r}"
    )


@pytest.mark.parametrize(
    "selector",
    [
        ["loremaster/tests/test_alpha.py"],
        ["loremaster/tests/test_beta.py", "loremaster/tests/test_gamma.py::test_x"],
    ],
)
def test_scoped_flag_echoes_the_exact_args(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    selector: list[str],
) -> None:
    """W6 — the flag echoes the ACTUAL args, not a hardcoded string. Two distinct
    selectors; a build that hardcodes one arg list fails the other."""
    manifest = _manifest(tmp_path / "m.yaml")
    _patch_loaders(monkeypatch, manifest, _empty_registry())
    _install_reader_spy(monkeypatch, lambda used: _results(used, junit_pass=3))
    _main_exit_code(["--wave", *selector])
    captured = capsys.readouterr()
    flag = _scoped_flag_line((captured.out + captured.err).splitlines())
    assert flag is not None, "a scoped run must carry a SCOPED-RUN flag"
    for arg in selector:
        assert arg in flag, f"the flag must echo the exact arg {arg!r}; got {flag!r}"


@pytest.mark.parametrize("count", [7, 42])
def test_scoped_flag_echoes_the_actual_test_count(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    count: int,
) -> None:
    """W6 — the flag echoes the ACTUAL collected/passed count, not a constant.
    Two distinct counts (chosen to avoid colliding with the 3-gate roster line);
    a build that hardcodes 'N tests' fails one of them."""
    manifest = _manifest(tmp_path / "m.yaml")
    _patch_loaders(monkeypatch, manifest, _empty_registry())
    _install_reader_spy(monkeypatch, lambda used: _results(used, junit_pass=count))
    _main_exit_code(["--wave", "loremaster/tests/test_changed.py"])
    captured = capsys.readouterr()
    flag = _scoped_flag_line((captured.out + captured.err).splitlines())
    assert flag is not None, "a scoped run must carry a SCOPED-RUN flag"
    assert str(count) in flag, (
        f"the flag must echo the actual count {count}; got {flag!r} — a hardcoded "
        "count fails one of the two parametrized runs"
    )


def test_full_run_pytest_is_a_real_currency_clear(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """NEGATIVE CONTROL for W5. A full run (no ``--wave``) renders pytest as a
    REAL GREEN currency clear and carries NO SCOPED-RUN flag — so a scoped receipt
    and a full receipt are never confusable, and the SCOPED marker is not falsely
    stamped on a full pass."""
    manifest = _manifest(tmp_path / "m.yaml")
    _patch_loaders(monkeypatch, manifest, _empty_registry())
    _install_reader_spy(monkeypatch, lambda used: _results(used, junit_pass=4))
    code = _main_exit_code([])
    captured = capsys.readouterr()
    lines = (captured.out + captured.err).splitlines()
    assert code == 0, "\n".join(lines)
    assert _scoped_flag_line(lines) is None, "a full run must not carry a SCOPED-RUN flag"
    pytest_line = _gate_line(lines, "pytest")
    assert pytest_line is not None
    assert "GREEN" in pytest_line.upper(), "a full run must render pytest as a real GREEN clear"
    assert "SCOPED" not in pytest_line.upper(), "a full run's pytest line is never SCOPED"


# ==========================================================================
# 5. The two errors (B3, B4) + the removed checkpoint mode (W8)
# ==========================================================================


def test_wave_with_no_args_is_an_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """B3 — ``--wave`` with no selector is an ERROR, not a silent full run.
    Loaders + spy are installed so a wrong build that PROCEEDS to run gates does
    not shell out; a wrong build that runs full and exits 0 is caught by the
    non-zero assertion."""
    manifest = _manifest(tmp_path / "m.yaml")
    _patch_loaders(monkeypatch, manifest, _empty_registry())
    _install_reader_spy(monkeypatch, _results)
    assert _main_exit_code(["--wave"]) != 0, (
        "`--wave` with no args must error — a scoped run needs a selector; "
        "silently running full is a wrong build"
    )


def test_wave_zero_collection_is_an_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """B4 (#290 anti-vacuity) — a scoped run that collects ZERO tests is an
    ERROR, never a silent pass. Zero collection surfaces as a
    ``BrokenInstrumentError`` from the leg-runner (JUnitReportReader total==0 /
    GateRunner exit-5); the bundle must NOT catch it and pass because 'pytest is
    scoped anyway'. Modeled by the leg-runner raising it — the bundle's exit must
    be non-zero (the spy still records the call, proving the run was attempted)."""
    manifest = _manifest(tmp_path / "m.yaml")
    _patch_loaders(monkeypatch, manifest, _empty_registry())

    def _zero_collection(_manifest: GateManifest) -> dict[str, object]:
        raise BrokenInstrumentError(
            "gate 'pytest' exited 5 — nothing collected (zero-collection scoped run)"
        )

    calls = _install_reader_spy(monkeypatch, _zero_collection)
    code = _main_exit_code(["--wave", "loremaster/tests/test_nonexistent.py"])
    assert calls, "the bundle must attempt the scoped run before it can be vacuous"
    assert code != 0, (
        "a scoped run that collects zero tests must ERROR — a silent scoped-pass "
        "over nothing is the #290 anti-vacuity class (B4)"
    )


def test_removed_checkpoint_mode_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """W8 — the old ``--checkpoint`` mode is REMOVED (design §13). It must not be
    silently accepted; a leftover checkpoint mode is the retired §11.8–§11.11
    machinery lingering. Loaders + spy guard against any shell-out."""
    manifest = _manifest(tmp_path / "m.yaml")
    _patch_loaders(monkeypatch, manifest, _empty_registry())
    _install_reader_spy(monkeypatch, _results)
    assert _main_exit_code(["--checkpoint"]) != 0, (
        "`--checkpoint` was removed in the simplified design — it must not be a "
        "recognised mode"
    )
