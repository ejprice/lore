"""Subprocess-mypy meta-test (PKT-28 Phase 0 fix-wave, ruling v2 §BUILD-NOW
item 9 / cold audit REPORT-phase0-audit-1.md §REMEDIATION item 4).

NOTE: the "ruling v2" cited above is UNRECOVERABLE (a per-session ``/tmp``
scratch file, gone from disk — see ``test_render.py``'s module docstring), so
its §-references are unverified provenance. This module's own substance below
does not depend on it.

The cold audit's headline finding: the render-safety seam's mypy layer was
NEVER TESTED -- test_render.py's v1 docstring declared "this module cannot
drive a real mypy failure from inside pytest" and skipped failure-matrix
rows 1-4 entirely. That declaration was false (it can, via ``subprocess``),
and it is EXACTLY why row 3 (a hostile, non-literal template) shipped green
at every gate: nothing ever ran mypy against the seam's own value/return/
template contracts and inspected the actual output. `typing.LiteralString`
is PARSED by mypy 2.1.0 but never actually CHECKED (PEP 675 enforcement is a
pyright-only feature) -- the ruling's v1 "strict-mode enforced" claim was
wrong, and no gate could have caught it without this instrument.

This module closes that hole PERMANENTLY: it shells out to the repo's own
``mypy`` (same command shape as ``scripts/typecheck.sh`` -- ``uv run mypy``,
repo root as ``cwd`` so the repo's own ``pyproject.toml`` config resolves,
not a bespoke one) against the five committed fixture files below and
asserts EXACTLY what the ruling's failure matrix claims: rows 1/2/4 fire
with their documented error codes, row 0 (the sanctioned idiom) is clean,
and row 3 (the hostile template) is mypy-SILENT -- pinning the refuted claim
as an OBSERVED, re-verified fact rather than a restated assumption, so this
seam's mypy layer can never again ship unverified. If a future mypy version
ships PEP 675 enforcement, row 3's assertions below will start FAILING
loudly (the fixture's straightforward hostile template would then be
rejected) -- that failure is the intended signal to correct render.py's
docstrings and reconsider whether the AST template-literal pin
(test_render_seam_pins.py) can step back from primary guard to redundant
defense-in-depth, not a regression to silently paper over.

Fixtures are copied byte-for-byte (extension changed only) from the cold
audit's own probes (REPORT-phase0-audit-1.md §PROBE-A,
``scratchpad/audit1/row{0-4}_*.py``) into
``loremaster/tests/render_mypy_fixtures/`` -- committed here rather than
left in the session-ephemeral scratchpad, so this pin is durable across
sessions. Stored with a ``.py.fixture`` extension, deliberately NOT ``.py``:
``scripts/typecheck.sh`` runs ``uv run mypy loremaster``, a RECURSIVE
directory scan with no per-file excludes configured in ``pyproject.toml``
(verified empirically while authoring this module -- copying row1 in as a
real ``.py`` file produced a genuine ``[arg-type]`` error under that exact
invocation). Fixtures 1/2/4 are DELIBERATELY mistyped; a real ``.py`` copy
sitting in the scanned tree would break the canonical "zero mypy errors,
including test trees" gate on every single commit. Each fixture is copied to
a fresh ``tmp_path`` with its original ``.py`` name before mypy ever sees
it, so mypy checks content byte-identical to the audit's own probes --
only the committed on-disk artifact's extension differs, never its content.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

# Packet 01a §C (#139): this is a SOURCE-TYPE meta-test — it shells `uv run mypy` with the
# repo root as cwd. Under the conformance harness the repo is a :ro /workspace mount, so
# `uv run` cannot create its project env and the test fails on an os-level write error that
# says nothing about the shipped artifact. Opt out inside the container (the harness sets
# LORE_CONFORMANCE_IN_CONTAINER=1); the DEFAULT is RUN, so the host gate is unaffected.
pytestmark = pytest.mark.skipif(
    os.environ.get("LORE_CONFORMANCE_IN_CONTAINER") == "1",
    reason=(
        "source-type meta-test: invokes the mypy dev-toolchain via `uv run`, needs a "
        "writable uv project env (the conformance mount is :ro); validates SOURCE "
        "annotations, not the shipped artifact's runtime (the shipped code never runs mypy)"
    ),
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FIXTURES_DIR = Path(__file__).resolve().parent / "render_mypy_fixtures"

# (fixture stem, expected mypy error-code substring, or None for "must be
# mypy-silent"). Order doubles as the module-scoped fixture's copy order.
_ROWS: list[tuple[str, str | None]] = [
    ("row0_control_clean", None),
    ("row1_raw_str_value", "[arg-type]"),
    ("row2_fstring_return", "[return-value]"),
    ("row3_nonliteral_template", None),  # v2's pinned reality: mypy-SILENT
    ("row4_join_demotion", "[arg-type]"),
]


@pytest.fixture(scope="module")
def _mypy_output(tmp_path_factory: pytest.TempPathFactory) -> str:
    """Run mypy ONCE over all five fixtures (mind runtime cost -- one
    invocation, not one per test) and return its combined stdout+stderr.

    Each ``.py.fixture`` is copied to a fresh ``.py`` file in a throwaway
    tmp_path dir first (see the module docstring for why the committed
    on-disk copies are not real ``.py`` files), then ``uv run mypy`` is
    invoked with the REPO ROOT as ``cwd`` (mirrors ``scripts/typecheck.sh``'s
    own invocation shape) so mypy discovers and applies the repo's own
    ``pyproject.toml`` config (``strict = true``, the pydantic plugin, the
    ``mypy_path`` entries that resolve ``loremaster.render``/
    ``loremaster.sanitise``) -- the SAME config every other gate in this
    repo runs under. A dedicated ``--cache-dir`` under ``tmp_path`` keeps
    this probe fully isolated from the repo's own ``.mypy_cache`` (mirrors
    the audit's own per-probe cache-dir isolation, ``scratchpad/audit1/
    .mypy_probe_cache*``).
    """
    work_dir = tmp_path_factory.mktemp("render_mypy_layer")
    fixture_paths: list[Path] = []
    for stem, _expected in _ROWS:
        source = (_FIXTURES_DIR / f"{stem}.py.fixture").read_text(encoding="utf-8")
        fixture_path = work_dir / f"{stem}.py"
        fixture_path.write_text(source, encoding="utf-8")
        fixture_paths.append(fixture_path)
    cache_dir = work_dir / ".mypy_cache"
    result = subprocess.run(
        ["uv", "run", "mypy", f"--cache-dir={cache_dir}", *(str(p) for p in fixture_paths)],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    return result.stdout + result.stderr


class TestSeamMypyLayer:
    """Pins exactly which failure-matrix rows mypy enforces and which it
    doesn't -- the process fix for the cold audit's headline finding."""

    @pytest.mark.parametrize("stem,expected_code", _ROWS, ids=[row[0] for row in _ROWS])
    def test_row_matches_the_documented_mypy_verdict(
        self, _mypy_output: str, stem: str, expected_code: str | None
    ) -> None:
        file_lines = [line for line in _mypy_output.splitlines() if f"{stem}.py:" in line]
        if expected_code is None:
            assert not file_lines, (
                f"{stem} was expected to be mypy-SILENT but produced output:\n"
                + "\n".join(file_lines)
            )
        else:
            assert any(expected_code in line for line in file_lines), (
                f"{stem} was expected to produce a {expected_code!r} error; got:\n"
                + "\n".join(file_lines)
            )

    def test_row3_silence_is_the_pinned_v2_reality_not_an_oversight(self, _mypy_output: str) -> None:
        """Explicit, standalone pin of the audit's headline finding (kept
        separate from the parametrized sweep above so it reads as a
        deliberate, prominent claim, not one row among five): mypy 2.1.0
        parses ``typing.LiteralString`` but never enforces it (PEP 675 is a
        pyright-only feature) -- a hostile, value-derived template is
        SILENTLY ACCEPTED. If a future mypy version starts flagging this,
        THIS assertion fails first and loudly -- the intended signal to
        revisit render.py's docstrings and this pin's framing, never a
        regression to silently work around.
        """
        row3_lines = [
            line for line in _mypy_output.splitlines() if "row3_nonliteral_template.py:" in line
        ]
        assert not row3_lines, (
            "row3_nonliteral_template is no longer mypy-silent -- a future mypy "
            "release may have shipped LiteralString/PEP 675 enforcement. This is "
            "GOOD NEWS, not a bug: update render.py's docstrings and this "
            "test's framing, do not just adjust the assertion.\n" + "\n".join(row3_lines)
        )

    def test_control_fixture_produces_no_errors_anywhere_in_the_run(self, _mypy_output: str) -> None:
        """A false positive on the SANCTIONED idiom (row0) would mean this
        meta-test's own fixture/config setup is wrong, not that render.py's
        API is unsound -- checked before trusting rows 1/2/4's positive
        results at all."""
        row0_lines = [line for line in _mypy_output.splitlines() if "row0_control_clean.py:" in line]
        assert not row0_lines, "the sanctioned idiom is not mypy-clean:\n" + "\n".join(row0_lines)
