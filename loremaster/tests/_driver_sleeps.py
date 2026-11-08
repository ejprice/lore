"""The conflict-retry driver's SLEEP seam, observed — packet SDK3 contract round 7 (R18 as amended by R20 A2).

R18 retires every pin that counted DRAWS from a lore jitter function (``_txn_conflict_backoff_seconds``):
under native tenacity there is no draw to count, only what the driver SLEEPS. R20 A2 keeps the CONTROLS
those draw counts carried ("the run actually retried", "an empty claim did NOT back off") by moving them
onto the sleep itself. This module is that one instrument, so ``test_retry_seam`` and
``test_sdk3_native_retry`` cannot each grow a private copy of it.

How a sleep is attributed to the driver: :func:`record_driver_sleeps` wraps the module attribute
``asyncio.sleep`` (tenacity's default ``sleep`` looks it up at call time, and so did the hand-rolled loop it
replaces) and records a call only when its IMMEDIATE caller lives in one of
:data:`DRIVER_SLEEP_CALLER_MODULES`. Measured 2026-11-08 (``scratchpad/sdk3r7/probes/sleep_caller.py``): the
hand-rolled driver at ``0d9b8c2`` sleeps from ``loremaster.store._txn``; the native ``AsyncRetrying`` driver
sleeps from ``tenacity.asyncio``. Every other ``asyncio.sleep`` in the process (the SDK's own loops, harness
waits, a test's own pacing) passes through unrecorded, so a live contention run cannot credit itself with a
backoff the driver never took.

Stated bound: a driver that issues its sleep from a module outside that set records NOTHING here, so the
contention premises read "never retried" and go RED — a false red on an unusual build, never a false clear.
The failure text names this set so the fix is one line.

The wrapper DELEGATES to whatever ``asyncio.sleep`` was installed before it (the real one for the live pins; a
test's silencer for the fake-connection pins), so it never changes how long anything waits.
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

import pytest

#: The modules a conflict-driver backoff is issued from (the immediate caller of ``asyncio.sleep``).
DRIVER_SLEEP_CALLER_MODULES: frozenset[str] = frozenset({"loremaster.store._txn", "tenacity.asyncio"})


@dataclass
class DriverSleepRecorder:
    """Every backoff the conflict driver SLEPT, in order, plus the asyncio task that slept it."""

    slept: list[float] = field(default_factory=list)
    by_task: dict[int, list[float]] = field(default_factory=dict)

    def record(self, duration: float) -> None:
        """Record one driver backoff (also called directly by the anti-vacuity controls)."""
        self.slept.append(duration)
        task = asyncio.current_task() if _has_running_loop() else None
        self.by_task.setdefault(id(task), []).append(duration)

    def clear(self) -> None:
        """Forget everything recorded so far (a contention wave is judged on its own sleeps)."""
        self.slept.clear()
        self.by_task.clear()


def _has_running_loop() -> bool:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return False
    return True


def _issued_by_the_driver(caller_module: object) -> bool:
    return isinstance(caller_module, str) and caller_module in DRIVER_SLEEP_CALLER_MODULES


def record_driver_sleeps(monkeypatch: pytest.MonkeyPatch) -> DriverSleepRecorder:
    """Install the recorder over the CURRENT ``asyncio.sleep`` (silenced or real) and return it."""
    recorder = DriverSleepRecorder()
    downstream: Callable[..., Awaitable[Any]] = asyncio.sleep

    def _observing_sleep(delay: float, *args: Any, **kwargs: Any) -> Awaitable[Any]:
        if _issued_by_the_driver(sys._getframe(1).f_globals.get("__name__")):
            recorder.record(delay)
        return downstream(delay, *args, **kwargs)

    monkeypatch.setattr(asyncio, "sleep", _observing_sleep)
    return recorder


#: The message every "the driver never backed off" premise failure carries.
NO_DRIVER_SLEEP_HINT = (
    "the conflict driver slept NO backoff. Either the run never retried (a never-retrying driver serves "
    "byte-identical results on an uncontended run — the Leg-2 false clear R20 A2 keeps this control for), "
    f"or the driver now sleeps from a module outside "
    f"DRIVER_SLEEP_CALLER_MODULES={sorted(DRIVER_SLEEP_CALLER_MODULES)} "
    "(loremaster/tests/_driver_sleeps.py) — then extend that set, never delete the control."
)
