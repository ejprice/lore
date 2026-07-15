"""Contract — packet 01a §C: the render-mypy meta-test opts out INSIDE the container.

``loremaster/tests/test_render_mypy_layer.py`` is a SOURCE-TYPE meta-test: it shells
``uv run mypy`` with the repo root as cwd to validate the render seam's annotations. That
is a dev-toolchain check, not an artifact-runtime check — and under the conformance
harness the repo is a ``:ro`` ``/workspace`` mount, so ``uv run`` cannot create its
project env and the test fails on an os-level write error that says nothing about the
shipped artifact.

The fix (design doc §C, "allowlist the safe" applied to the suite) is a VISIBLE, REASONED
opt-out marker on that module, keyed on the env var the harness sets
(``LORE_CONFORMANCE_IN_CONTAINER=1``). Its DEFAULT is "runs" — the host suite is
unaffected. This pin holds that contract:

* the marker exists and is a ``skipif`` (not a bare ``skip``, which would disable the
  seam's mypy layer on the dev host too — the very hole test_render_mypy_layer.py closed);
* it does NOT skip on a normal host (env unset) — the default is RUN;
* it DOES skip inside the conformance container (env == "1") — proving it keys on that
  exact env var and value;
* it carries a non-empty reason (a bare skip is indistinguishable from a broken test).

RED until the builder adds the marker.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

# The env var the conformance harness (conformance_run.sh) sets inside the container.
CONFORMANCE_ENV_KEY = "LORE_CONFORMANCE_IN_CONTAINER"

# The module under contract — a sibling in this same test directory.
TARGET = Path(__file__).resolve().parent / "test_render_mypy_layer.py"


def _load_target_fresh() -> ModuleType:
    """Execute the target module's body fresh, reading the CURRENT process env.

    The marker's condition (``os.environ.get(KEY) == "1"``) is evaluated at import time,
    so tests set the env, then load, to observe the resulting skip condition. The module
    is loaded under a synthetic name and NOT registered in ``sys.modules`` — every call
    re-executes, so a prior load's env cannot leak into the next.
    """
    spec = importlib.util.spec_from_file_location("_render_mypy_layer_under_probe", TARGET)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _skipif_marks(pytestmark: Any) -> list[Any]:
    """Every ``skipif`` MarkDecorator in a module-level ``pytestmark`` (single or list)."""
    marks = pytestmark if isinstance(pytestmark, (list, tuple)) else [pytestmark]
    return [
        mark
        for mark in marks
        if getattr(getattr(mark, "mark", None), "name", None) == "skipif"
    ]


def _require_skipif(module: ModuleType) -> Any:
    """Return the ONE ``skipif`` ``Mark`` on the module, or fail RED explaining what is missing."""
    pytestmark = getattr(module, "pytestmark", None)
    assert pytestmark is not None, (
        f"{TARGET.name} carries no module-level `pytestmark` — the builder must add a "
        f"`skipif` keyed on {CONFORMANCE_ENV_KEY} so this source-type mypy meta-test opts "
        f"out on the read-only conformance mount (packet 01a §C)"
    )
    skipifs = _skipif_marks(pytestmark)
    assert len(skipifs) == 1, (
        f"expected exactly one `skipif` marker on {TARGET.name}; found {len(skipifs)}"
    )
    return skipifs[0].mark


class TestConformanceOptOutMarker:
    """The render-mypy meta-test must opt out inside the container, and only there."""

    def test_module_defines_a_single_skipif_pytestmark(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A ``skipif`` marker exists (not a bare ``skip``, which would kill the dev-host run)."""
        monkeypatch.delenv(CONFORMANCE_ENV_KEY, raising=False)
        module = _load_target_fresh()

        # _require_skipif fails RED with a builder-facing message if the marker is absent
        # or is not a skipif.
        _require_skipif(module)

    def test_marker_does_not_skip_on_a_normal_dev_host(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """DEFAULT is RUN: with the conformance env UNSET the skip condition is falsy."""
        monkeypatch.delenv(CONFORMANCE_ENV_KEY, raising=False)
        module = _load_target_fresh()

        mark = _require_skipif(module)
        assert mark.args, "the skipif marker carries no condition argument"
        condition = mark.args[0]

        # Kills a build that skips unconditionally (e.g. `pytest.mark.skip`) or keys on the
        # wrong var — either would silently disable this seam's mypy layer on every host run.
        assert not condition, (
            f"the skipif condition is truthy with {CONFORMANCE_ENV_KEY} unset — the marker "
            f"must default to RUNNING on a dev host. (If the condition is a string rather "
            f"than an eagerly-evaluated bool, use the `os.environ.get(...) == '1'` form the "
            f"design doc specifies so 'unset' evaluates false.)"
        )

    def test_marker_skips_inside_the_conformance_container(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Inside the container (env == "1") the skip condition is truthy — the opt-out fires."""
        monkeypatch.setenv(CONFORMANCE_ENV_KEY, "1")
        module = _load_target_fresh()

        mark = _require_skipif(module)
        assert mark.args, "the skipif marker carries no condition argument"
        condition = mark.args[0]

        # Kills a build keyed on the wrong env var (or an inverted condition): only a marker
        # that keys on LORE_CONFORMANCE_IN_CONTAINER=='1' flips to truthy here.
        assert condition, (
            f"the skipif condition is falsy when {CONFORMANCE_ENV_KEY}=1 — the marker must "
            f"key on that env var and its '1' value so the mypy meta-test opts out on the "
            f":ro conformance mount"
        )

    def test_marker_carries_a_non_empty_reason(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A reason is mandatory — a bare skip is indistinguishable from a broken test."""
        monkeypatch.setenv(CONFORMANCE_ENV_KEY, "1")
        module = _load_target_fresh()

        mark = _require_skipif(module)
        reason = mark.kwargs.get("reason", "")

        assert isinstance(reason, str) and reason.strip(), (
            "the skipif marker must carry a non-empty `reason` so a reader knows WHY the "
            "source-type mypy meta-test is skipped inside the conformance container"
        )
