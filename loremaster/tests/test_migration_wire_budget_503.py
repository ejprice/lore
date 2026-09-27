"""Contract (#503) — the heavy wire harness waits long enough for its OWN start; the default does not move.

Session ``297217bd``, tdd-light. Author: ``contract-503`` (TESTS ONLY). Operator ruling 2026-09-26 ("All 4
recs"), item 1: a per-caller startup budget of 60 s goes in ``test_migration_wire._serve_migration_wire``
ONLY; ``loopback.DEFAULT_STARTUP_TIMEOUT_S`` stays 15 s.

EVIDENCE (``docs/plans/v2/receipts/2026-09-26-466-503/REPORT-measure-503.md``, committed ``388c604``, measured
2026-09-26 at code ``4ddb913``): n=551
heavy ``_serve_migration_wire`` starts under fleet load — p99 9.85 s, max 10.04 s, 99.4 % inside
``build_app_context`` and store-bound; light ``serve_asgi`` callers p50 0.02 s, max 0.50 s. The #503 failure
(a heavy start > 15 s under CPU oversubscription) was OUTSIDE that envelope, so the ruled budget is ~6x the
measured max (60 / 10.04 = 5.98x; exactly 4x the 15 s default) rather than a tuned p99.

CLASS: every server start of the heavy composition in the wire-fixture home is given the heavy budget, by
NAME. Domain: every ``serve_asgi`` call in ``test_migration_wire.py`` (AST-derived — a second call site
added later is covered or reddens). A LIGHT caller keeps the default (the control: the default pin).

INTERFACE this contract DEFINES (does not exist at HEAD ``884ca63`` — see
docs/plans/v2/receipts/2026-09-26-466-503/REPORT-contract-503.md §Stub):
``test_migration_wire.MIGRATION_WIRE_STARTUP_TIMEOUT_S`` — a module-level named constant (its derivation and
re-open trigger in a comment beside it), passed as ``serve_asgi(..., startup_timeout_s=<that name>)``.

RED dating: everything here is dated to HEAD ``884ca63``; a reader after the build must re-derive.
"""

from __future__ import annotations

import ast
import asyncio
import inspect
import time
from pathlib import Path
from typing import Any

import loremaster.server as server_module
import loremaster.testing.loopback as loopback_module
import pytest
import test_migration_wire as migration_wire_module
from loremaster.testing.loopback import DEFAULT_STARTUP_TIMEOUT_S, ServerStartupTimeout

# The operator's rulings (2026-09-26), written here as INDEPENDENT expected values — never read back from
# the module under test, or the pin would certify whatever value the builder typed.
OPERATOR_RULED_HEAVY_STARTUP_BUDGET_S = 60.0
OPERATOR_RULED_DEFAULT_STARTUP_BUDGET_S = 15.0
# docs/plans/v2/receipts/2026-09-26-466-503/REPORT-measure-503.md (388c604) §Legs / §Light callers: the
# measured maxima the budgets are judged against.
MEASURED_HEAVY_START_MAX_S = 10.04
MEASURED_LIGHT_START_MAX_S = 0.50
# The derived-output sanity band (realism clause 4): a budget below 3x the measured max leaves the heavy
# harness one bad minute from #503 again; the default below 3x the light max would time light callers out.
BUDGET_HEADROOM_FACTOR = 3.0

# The slow-start leg: an extra delay injected INTO the heavy lifespan start, so the start exceeds the
# DEFAULT budget by a clear margin but stays far inside the ruled heavy one even at the measured heavy max.
SLOW_HEAVY_START_EXTRA_S = DEFAULT_STARTUP_TIMEOUT_S + 5.0

_MIGRATION_WIRE_SOURCE = Path(inspect.getfile(migration_wire_module))
_SERVE_ASGI_NAME = loopback_module.serve_asgi.__name__
_STARTUP_BUDGET_PARAMETER = "startup_timeout_s"


class _ServeCaptured(Exception):  # noqa: N818 — a control-flow sentinel, not an error
    """Raised by the ``serve_asgi`` spy once it has recorded the call — nothing heavy is ever served."""


def _serve_asgi_calls_in_the_wire_fixture_home() -> list[ast.Call]:
    """Every call to ``serve_asgi`` in ``test_migration_wire.py`` — bare name or attribute form alike."""
    tree = ast.parse(_MIGRATION_WIRE_SOURCE.read_text(encoding="utf-8"))
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        callee = node.func
        called_name = callee.id if isinstance(callee, ast.Name) else getattr(callee, "attr", None)
        if called_name == _SERVE_ASGI_NAME:
            calls.append(node)
    return calls


class TestTheDefaultStartupBudgetIsUnchanged:
    """Ruling item 1, second half: the LIGHT callers' budget is untouched. The heavy fix is per-caller."""

    def test_the_default_startup_budget_stays_at_the_ruled_value(self) -> None:
        assert DEFAULT_STARTUP_TIMEOUT_S == OPERATOR_RULED_DEFAULT_STARTUP_BUDGET_S, (
            f"DEFAULT_STARTUP_TIMEOUT_S is {DEFAULT_STARTUP_TIMEOUT_S}; the operator ruled it STAYS "
            f"{OPERATOR_RULED_DEFAULT_STARTUP_BUDGET_S} (2026-09-26, #503) — the heavy budget is per-caller. "
            "Re-open only with a new light-caller measurement."
        )
        # Sanity band: the default still has headroom over the measured LIGHT starts it bounds.
        assert DEFAULT_STARTUP_TIMEOUT_S >= BUDGET_HEADROOM_FACTOR * MEASURED_LIGHT_START_MAX_S


class TestTheHeavyWireFixtureUsesTheHeavyBudget:
    """Ruling item 1, first half: ``_serve_migration_wire`` starts the heavy composition under a NAMED
    budget of 60 s — named, passed, and effective."""

    def test_the_heavy_budget_constant_has_the_ruled_value(self) -> None:
        heavy_budget = migration_wire_module.MIGRATION_WIRE_STARTUP_TIMEOUT_S
        assert heavy_budget == OPERATOR_RULED_HEAVY_STARTUP_BUDGET_S
        assert heavy_budget > DEFAULT_STARTUP_TIMEOUT_S
        assert heavy_budget >= BUDGET_HEADROOM_FACTOR * MEASURED_HEAVY_START_MAX_S

    def test_every_serve_asgi_call_in_the_fixture_home_passes_the_budget_by_name(self) -> None:
        # Generated over the file: a second serve of the heavy composition added later is covered too.
        calls = _serve_asgi_calls_in_the_wire_fixture_home()
        assert calls, f"no {_SERVE_ASGI_NAME} call found in {_MIGRATION_WIRE_SOURCE.name} — the scan is blind"
        for call in calls:
            budget = next(
                (keyword.value for keyword in call.keywords if keyword.arg == _STARTUP_BUDGET_PARAMETER), None
            )
            where = f"{_MIGRATION_WIRE_SOURCE.name}:{call.lineno}"
            assert budget is not None, (
                f"{where} starts the heavy composition with NO {_STARTUP_BUDGET_PARAMETER} — it inherits the "
                f"{DEFAULT_STARTUP_TIMEOUT_S}s light default, which #503 measured heavy starts overrunning"
            )
            assert isinstance(budget, ast.Name), (
                f"{where} passes {_STARTUP_BUDGET_PARAMETER}={ast.unparse(budget)} — a bare value, not the "
                "named constant whose comment carries the derivation and re-open trigger"
            )
            assert budget.id == "MIGRATION_WIRE_STARTUP_TIMEOUT_S", (
                f"{where} passes {budget.id}, not MIGRATION_WIRE_STARTUP_TIMEOUT_S"
            )

    async def test_the_fixture_actually_hands_the_heavy_budget_to_the_server_start(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        _inert_calibration_counter: None,
    ) -> None:
        # The RUNTIME half of the AST pin: what serve_asgi RECEIVED, bound against its real signature (so a
        # default counts as what it is). The spy stops the start before anything heavy is served; the
        # fixture's store setup still runs against the TEST store and its database is dropped in its finally.
        real_signature = inspect.signature(loopback_module.serve_asgi)
        received: list[float] = []

        def _spy_serve_asgi(*args: Any, **kwargs: Any) -> Any:
            bound = real_signature.bind(*args, **kwargs)
            bound.apply_defaults()
            received.append(bound.arguments[_STARTUP_BUDGET_PARAMETER])
            raise _ServeCaptured

        # Both bindings: the fixture's module-level name, and the module attribute a refactor might call.
        monkeypatch.setattr(migration_wire_module, _SERVE_ASGI_NAME, _spy_serve_asgi)
        monkeypatch.setattr(loopback_module, _SERVE_ASGI_NAME, _spy_serve_asgi)
        with pytest.raises(_ServeCaptured):
            async with migration_wire_module._serve_migration_wire(  # noqa: SLF001
                tmp_path, monkeypatch, allowed_hosts_env=None
            ):
                pytest.fail("the spy let a server start — it is not on the fixture's path")
        assert len(received) == 1, f"the fixture started {len(received)} servers; expected exactly one"
        assert received[0] == OPERATOR_RULED_HEAVY_STARTUP_BUDGET_S, (
            f"_serve_migration_wire handed serve_asgi startup_timeout_s={received[0]}; the heavy composition "
            f"must start under {OPERATOR_RULED_HEAVY_STARTUP_BUDGET_S}s (#503)"
        )

    async def test_a_heavy_start_slower_than_the_default_budget_is_served(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        _inert_calibration_counter: None,
    ) -> None:
        # The behavioural pin, receiver-blind: HOW the budget reaches the start does not matter — a real
        # heavy start that takes longer than the default must be SERVED, not reported as #503's timeout.
        # The delay is injected into the first heavy-startup primitive (the probe gate, awaited inside
        # build_app_context), which the fixture wraps with its own once-per-process counter.
        assert (
            SLOW_HEAVY_START_EXTRA_S + MEASURED_HEAVY_START_MAX_S < OPERATOR_RULED_HEAVY_STARTUP_BUDGET_S
        ), "the injected delay plus a measured-max start must fit the ruled budget, or a correct build fails"
        real_probe_gate = server_module.run_probe_gate
        delayed_starts: list[float] = []

        async def _slow_probe_gate(**kwargs: Any) -> int:
            delayed_starts.append(time.monotonic())
            await asyncio.sleep(SLOW_HEAVY_START_EXTRA_S)
            return await real_probe_gate(**kwargs)

        monkeypatch.setattr(server_module, "run_probe_gate", _slow_probe_gate)
        entered = time.monotonic()
        try:
            async with migration_wire_module._serve_migration_wire(  # noqa: SLF001
                tmp_path, monkeypatch, allowed_hosts_env=None
            ) as wire:
                start_took_s = time.monotonic() - entered
                server_info = await wire.server_info()
        except ServerStartupTimeout as timeout:
            pytest.fail(
                f"a heavy start of >{SLOW_HEAVY_START_EXTRA_S}s was reported as a startup timeout "
                f"({timeout.startup_timeout_s}s budget) — the #503 failure: {timeout}"
            )
        # Non-vacuity: the delay really ran, once, INSIDE the start the budget bounds.
        assert len(delayed_starts) == 1, f"the delayed probe gate ran {len(delayed_starts)} times"
        assert start_took_s >= SLOW_HEAVY_START_EXTRA_S > DEFAULT_STARTUP_TIMEOUT_S, (
            f"the start took {start_took_s:.1f}s — the injected delay was not inside the awaited start"
        )
        assert server_info.version, f"the slow-started server did not serve an initialize: {server_info!r}"
