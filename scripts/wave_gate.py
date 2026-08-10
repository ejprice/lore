"""wave_gate.py — the NON-OMITTABLE gate bundle (finding #344), OPERATOR-SIMPLIFIED form.

Contract: ``scripts/test_wave_gate.py``. Design doc
``docs/plans/v2/design/2026-08-09-defect-class-prevention.md`` §13 (supersedes the retired
§11.8–§11.11 typed-WaveReceipt / conduit-equality / branch-coverage / per-axis byte-oracle
machinery).

WHY THIS EXISTS (finding #344). *"The gates"* was a hand-list re-typed in each spawn brief, and a
stage once ran a subset (typecheck + ruff + the contract suites) and OMITTED
``pending_contract_gate.py --currency`` — so eight RED_ORPHANED structural pins a diff introduced
went unseen for two cycles. ``gates.yaml`` is already the gate authority and
``pending_contract_gate.py`` already derives its leg set from it; the gap #344 names is one level
up — there was no single ENTRYPOINT a brief could point at instead of re-listing gates. This is
that entrypoint. No CI exists (#285), so the bundle IS the enforcement point.

BEHAVIOUR (design §13):
  * **No ``--wave``** → the FULL suite runs (default). typecheck + ruff + currency run FULL; pytest
    runs FULL (no selector).
  * **``--wave <selector…>`` (≥1)** → the non-omittable core (typecheck + ruff + currency over ALL
    gates) still runs FULL; ONLY the pytest leg is short-circuited to ``<selector>`` (pytest
    node-ids/paths, forwarded verbatim — no ``-k``). The receipt renders the pytest gate SCOPED
    (never GREEN) and carries an honest **"SCOPED RUN — ran … (N tests); does NOT certify the full
    gate"** flag echoing the exact args + the collected count. A scoped receipt can therefore never
    read as a full pass.
  * **``--wave`` with NO selector** → ERROR.
  * **``--wave <selector…>`` that collect ZERO tests** → ERROR (no silent scoped-pass over nothing —
    the #290 anti-vacuity class; it surfaces as a ``BrokenInstrumentError`` from the leg-runner,
    which the bundle must NOT swallow into a pass).

ONE IMPLEMENTATION (design priority #1): this wrapper NAMES NO GATES. It composes
``pending_contract_gate``'s machinery in-process — ``GateManifest.load`` /
``PendingContractRegistry.load`` for inputs, ``_run_selected_gates`` as the ONE derived leg-runner
(handed the manifest's FULL id set as legs), and ``_currencies_for`` for the per-gate verdicts.
The only thing it adds is the SCOPED-not-GREEN override on the pytest gate's verdict in wave mode,
which needs structured access to that verdict — hence the in-process composition rather than a
stdout-parsing subprocess wrapper.

BOUND / re-open trigger (design §13, F1): a wave-mode run does NOT clear pytest currency; a
diff-introduced pin in a suite the selector missed is caught only by a full run. Re-open trigger:
the day this repo gains CI (#285), a full run becomes CI's first job and the wave/full split
collapses into "every push runs full".

USAGE — ``uv run``, never barefoot (imports project deps via ``pending_contract_gate``):

    W=scripts/wave_gate.py
    uv run python $W                                   # FULL — the phase-checkpoint / pre-deploy run
    uv run python $W --wave loremaster/tests/test_x.py # WAVE — pytest scoped, core still full
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping, Sequence

import pending_contract_gate as pcg
from pending_contract_gate import (
    DEFAULT_MANIFEST_PATH,
    DEFAULT_REGISTRY_PATH,
    READERS,
    REPO_ROOT,
    VERDICT_GREEN,
    BrokenInstrumentError,
    GateCurrency,
    GateManifest,
    GateRunner,
    JUnitReportReader,
    ManifestError,
    PendingContractGate,
    PendingContractRegistry,
    PytestRun,
    RegistryError,
)


def _scopable_gate_id(manifest: GateManifest) -> str:
    """The ONE gate whose pytest leg ``--wave`` scopes — DERIVED (the junit-reader gate), never a
    hardcoded ``"pytest"``. A manifest with zero or several junit gates is a broken configuration
    the wrapper refuses rather than guesses at."""
    matches = [
        spec.id for spec in manifest.gates if READERS[spec.reader] is JUnitReportReader
    ]
    if len(matches) != 1:
        raise ManifestError(
            f"wave_gate needs EXACTLY ONE pytest (junit-reader) gate to scope; the manifest has "
            f"{len(matches)} ({matches}). --wave cannot decide which leg to short-circuit."
        )
    return matches[0]


def _scoped_pytest_line(gate_id: str, argument_render: str, test_count: int) -> str:
    """The pytest gate's currency line in WAVE mode: SCOPED, never GREEN. Rendered here rather than
    via ``GateCurrency.render()`` because a scoped subset must not read as a currency clear."""
    return (
        f"  {gate_id:<12} SCOPED — ran {argument_render} ({test_count} tests); NOT a currency "
        "clear (a subset; the full pytest run is owed at the phase checkpoint)"
    )


def _render(
    manifest: GateManifest,
    currencies: Sequence[GateCurrency],
    results: Mapping[str, object],
    *,
    wave: bool,
    selector: Sequence[str],
) -> tuple[list[str], bool]:
    """The receipt an LLM reads, plus the pass/fail. In wave mode the pytest gate's GREEN verdict
    renders SCOPED and a SCOPED-RUN flag is appended; the pass/fail is unchanged (a scoped GREEN
    still passes, a scoped RED_ORPHANED still fails — the honesty is in the render, never the
    exit)."""
    lines = [
        "GATE CURRENCY — is every CLAIMED gate green, or owned?",
        f"  manifest   : {manifest.ids} ({len(manifest.gates)} gates)",
    ]
    scopable_id = _scopable_gate_id(manifest) if wave else None
    argument_render = " ".join(selector)
    scoped_run = results.get(scopable_id) if scopable_id is not None else None
    test_count = scoped_run.total if isinstance(scoped_run, PytestRun) else 0

    for currency in currencies:
        if (
            wave
            and currency.gate_id == scopable_id
            and currency.verdict == VERDICT_GREEN
        ):
            lines.append(_scoped_pytest_line(currency.gate_id, argument_render, test_count))
        else:
            lines.append(currency.render())
            for orphan in currency.orphans:
                lines.append(f"      ORPHAN: {orphan}")

    ok = all(currency.ok for currency in currencies)
    if wave:
        lines.append(
            f"SCOPED RUN — ran {argument_render} ({test_count} tests); does NOT certify the full "
            "gate (typecheck + ruff + currency ran FULL; pytest ran only the named selector)"
        )
    if ok:
        lines.append("CURRENCY   : PASS — every claimed gate is GREEN or OWNED")
    else:
        lines.append("CURRENCY   : FAIL — a gate is RED_ORPHANED or NOT_RUN")
    return lines, ok


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the non-omittable gate bundle (finding #344). With no --wave, the FULL suite "
            "runs. --wave <selector…> scopes ONLY the pytest leg; the core (typecheck + ruff + "
            "currency) always runs full and a SCOPED-RUN flag makes the subset un-mistakable for "
            "a full pass."
        )
    )
    # ``nargs="+"`` makes ``--wave`` with no selector an argparse error (design §13): a scoped run
    # needs a selector, and silently running full would be a wrong build. The old ``--checkpoint``
    # mode is REMOVED — an unrecognised argument errors, so it cannot be silently accepted.
    parser.add_argument(
        "--wave",
        nargs="+",
        default=None,
        metavar="SELECTOR",
        help=(
            "pytest node-ids/paths to scope the pytest leg to (verbatim, no -k). The core still "
            "runs full. Omit --wave entirely to run the full suite."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """The CLI entrypoint AND the enforcement point. Exit 0 = every gate GREEN/OWNED (pytest SCOPED
    in wave mode); 1 = a gate is RED_ORPHANED or NOT_RUN; 2 = a BROKEN INSTRUMENT / bad config."""
    arguments = _build_parser().parse_args(argv)
    wave = arguments.wave is not None
    selector: tuple[str, ...] = tuple(arguments.wave) if wave else ()

    try:
        manifest = GateManifest.load(DEFAULT_MANIFEST_PATH)
        registry = PendingContractRegistry.load(DEFAULT_REGISTRY_PATH)
    except (ManifestError, RegistryError) as error:
        print(f"CONFIG ERROR: {error}", file=sys.stderr)
        return 2

    runner = GateRunner(REPO_ROOT)
    gate = PendingContractGate(registry=registry, repo_root=REPO_ROOT)

    # The non-omittable core always runs FULL — the runner is handed the manifest's FULL derived id
    # set as legs; ONLY pytest is scopable, and it is scoped by forwarding the selector as
    # ``pytest_args`` (the leg-runner appends them to the junit-reader gate's command alone).
    try:
        results = pcg._run_selected_gates(runner, manifest, manifest.ids, selector)
    except BrokenInstrumentError as error:
        # Zero-collection scoped run (#290 anti-vacuity), or any transcript that is not a
        # measurement. NEVER swallowed into a scoped pass just because pytest was scoped.
        print(f"BROKEN INSTRUMENT: {error}", file=sys.stderr)
        return 2
    except (ManifestError, RegistryError) as error:
        print(f"CONFIG ERROR: {error}", file=sys.stderr)
        return 2

    currencies = pcg._currencies_for(gate, manifest, results)
    lines, ok = _render(
        manifest, currencies, results, wave=wave, selector=selector
    )
    print("=" * 72)
    for line in lines:
        print(line)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
