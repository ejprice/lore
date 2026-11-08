"""Packet SDK3 contract, round 7 — R18 (tenacity used NATIVELY) as amended by R20 A1–A4: the
conflict-retry driver and scout's reconnect ladder pinned by what they DO, not by how they are spelled.

``docs/plans/v2/sdk3-rulings.md`` R18 retires the draw-COUNT pins and round 6's ``slept == drawn`` pin (tests
of the hand-rolled implementation that shaped production around tenacity) and replaces them with the
behaviour list below; R20 amends it (A1 no per-attempt log, A2 controls move to the sleep seam, A3 a
distribution pin, A4 ONE wait factory proven by mutation). Every pin observes a SLEEP — through
``loremaster/tests/_driver_sleeps.py`` (the ``asyncio.sleep`` seam) or scout's injected ``sleep`` — and never
names a tenacity class or a lore jitter function, except A4, whose whole subject is the one factory
``loresigil.backoff.full_jitter``.

| pin (class) | clause | the wrong build it turns RED |
|---|---|---|
| ``TestEverySleptBackoffLiesInItsWindow`` | R18 window | uncapped, flat or floor-lifted window; a sleep |
| | | after giving up |
| ``TestFullJitterReachesBothTailsOfTheWindow`` | R20 A3 | ``w/2 + d/2`` drift; ``uniform(0, w/2)`` |
| ``TestConcurrentRacersSleepDecorrelatedSequences`` | R18 ≥8-way | jitter derived from shared state |
| ``TestTheDriverLogsOnlyItsTerminalDisposition`` | R20 A1 / X22 | per-attempt logging hooks, any logger |
| ``TestANonConflictErrorIsNeverRetriedOrBackedOff`` | R18 | a ``retry=`` wider than the seam's signal |
| ``TestALambdaShapedCallerGetsTheAttemptsValue`` | R20 Leg 2 (iv) | the lambda handed to tenacity raw |
| ``TestTheOneWaitFactoryReachesEveryIn66Site`` | R20 A4 | a site constructing its own tenacity wait |
| ``TestTheSubscriberBacksOffBeforeEveryReconnect`` | scout ``run`` docstring | an immediate reconnect after |
| | | a drop; a ladder that never resets |

Packet 68 owns the other five retry loops, ``jittered_fixed`` and the fake-``RetryCallState`` shim; nothing
here pins them. Classifier sharing (R18 "a mutation of the seam's classifier reddens the retry path") is a
declared mutation proof (packet doc §ROUND 7), not a standing pin.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from collections.abc import Callable
from typing import Any

import pytest
from _driver_sleeps import (
    NO_DRIVER_SLEEP_HINT,
    DriverSleepRecorder,
    WaitFactoryMutation,
    mutate_the_wait_factory,
    record_driver_sleeps,
)
from loremaster.scout import CommandSubscriber
from loremaster.store import _txn
from tenacity import wait_exponential, wait_fixed

_REAL_SLEEP = asyncio.sleep

#: R20 A3: sleeps sampled at ONE attempt index. P(false red | full jitter) = 2·(7/8)^256 ≈ 3e-15.
_TAIL_SAMPLES = 256
#: R18: "≥8-way racers". Sixteen, the same degree as T2's live family.
_RACERS = 16
_CONFLICTS_PER_RACER = 4
#: A4's sentinel: no correct window produces it (the conflict cap is 0.1 s; scout's drive cap is 12 s).
_SENTINEL_WAIT_S = 1234.5
#: Scout drives use a window that is NOT scout's production default: a fixture reusing the module constant
#: cannot tell "the site forwards MY parameters" from "it ignores them and agrees with the default".
_SCOUT_BASE_S = 0.25
_SCOUT_CAP_S = 12.0
#: Scout's poll cadence in these drives, distinct from every backoff value, so a recorded scout sleep is
#: attributable to the ladder or to the poll loop by value.
_SCOUT_POLL_S = 0.0007


async def _no_sleep(_seconds: float, *_args: Any, **_kwargs: Any) -> None:
    await _REAL_SLEEP(0)


@pytest.fixture
def driver_sleeps(monkeypatch: pytest.MonkeyPatch) -> DriverSleepRecorder:
    """Silence ``asyncio.sleep`` (a 64-attempt exhaustion is then cheap); record the driver's sleeps."""
    monkeypatch.setattr(asyncio, "sleep", _no_sleep)
    return record_driver_sleeps(monkeypatch)


def _window(attempt_number: int) -> float:
    """The full-jitter window after the ``attempt_number``-th failed attempt (1-based), read live."""
    return float(
        min(
            _txn._TXN_CONFLICT_BACKOFF_CAP_SECONDS,
            _txn._TXN_CONFLICT_BACKOFF_BASE_SECONDS * 2 ** (attempt_number - 1),
        )
    )


class _ConflictsThenReturns:
    """An attempt body: ``conflicts`` retry signals (each chained from its own cause), then ``value``.

    ``conflicts=None`` conflicts forever."""

    def __init__(self, conflicts: int | None, value: object = "landed") -> None:
        self.conflicts = conflicts
        self.value = value
        self.calls = 0

    async def __call__(self) -> object:
        self.calls += 1
        if self.conflicts is None or self.calls <= self.conflicts:
            try:
                raise RuntimeError(f"engine conflict #{self.calls}")
            except RuntimeError as cause:
                raise _txn.RetryableConflictSignal() from cause
        return self.value


def _hint_if_empty(slept: list[float]) -> str:
    return "" if slept else NO_DRIVER_SLEEP_HINT


class TestEverySleptBackoffLiesInItsWindow:
    """R18: after the n-th failed attempt the driver sleeps ONCE, inside ``[0, min(cap, base·2^(n-1)))``."""

    async def test_every_retry_sleeps_once_inside_its_growing_window(
        self, driver_sleeps: DriverSleepRecorder
    ) -> None:
        body = _ConflictsThenReturns(conflicts=None)
        with pytest.raises(_txn.TxnContentionExhaustedError):
            await _txn.retry_on_conflict(body, deadline_seconds=1e9)

        ceiling = _txn._TXN_CONFLICT_ATTEMPT_CEILING
        assert body.calls == ceiling, f"premise: {body.calls} attempts, not the ceiling {ceiling}"
        slept = driver_sleeps.slept
        assert len(slept) == body.calls - 1, (
            f"{body.calls} attempts slept {len(slept)} backoffs: the driver backs off ONCE between "
            f"consecutive attempts and never after it gives up (a trailing sleep delays the typed error "
            f"by up to the cap). {_hint_if_empty(slept)}"
        )
        outside = [
            (attempt_number, delay, _window(attempt_number))
            for attempt_number, delay in enumerate(slept, start=1)
            if not 0.0 <= delay < _window(attempt_number)
        ]
        assert not outside, (
            f"(attempt n, slept, window) outside [0, min(cap, base·2^(n-1))): {outside[:6]} — an "
            f"uncapped or mis-indexed window, or jitter added ABOVE the window (equal jitter's floor)"
        )
        cap = _txn._TXN_CONFLICT_BACKOFF_CAP_SECONDS
        capped = [delay for number, delay in enumerate(slept, start=1) if _window(number) == cap]
        assert capped and max(capped) > cap / 2, (
            f"all {len(capped)} backoffs taken at the capped window stayed below cap/2 "
            f"(max {max(capped, default=None)}): the window does not GROW to the cap (a flat window "
            f"passes the bound check alone). P(false red | correct) = 2^-{len(capped)}."
        )


class TestFullJitterReachesBothTailsOfTheWindow:
    """R20 A3: at ONE attempt index, ≥256 slept values reach below w/8 AND above 7w/8.

    The window and decorrelation pins admit ``sleep = w/2 + drawn/2`` (in-window, decorrelated); this pin
    sees the LOWER tail full jitter exists for (#102: jitter around a floor is insufficient)."""

    async def test_the_first_backoff_reaches_both_tails_of_its_window(
        self, driver_sleeps: DriverSleepRecorder
    ) -> None:
        for _ in range(_TAIL_SAMPLES):
            assert await _txn.retry_on_conflict(_ConflictsThenReturns(conflicts=1)) == "landed"

        window = _window(1)
        slept = driver_sleeps.slept
        assert len(slept) == _TAIL_SAMPLES, (
            f"{_TAIL_SAMPLES} single-conflict calls slept {len(slept)} backoffs. {_hint_if_empty(slept)}"
        )
        lowest, highest = min(slept), max(slept)
        assert lowest < window / 8, (
            f"the lowest of {_TAIL_SAMPLES} first backoffs is {lowest:.6f}s, never below w/8 = "
            f"{window / 8:.6f}s: jitter AROUND A FLOOR (equal jitter, e.g. w/2 + d/2), not full jitter"
        )
        assert highest > 7 * window / 8, (
            f"the highest of {_TAIL_SAMPLES} first backoffs is {highest:.6f}s, never above 7w/8 = "
            f"{7 * window / 8:.6f}s: the draw does not span the window (e.g. uniform(0, w/2))"
        )


class TestConcurrentRacersSleepDecorrelatedSequences:
    """R18: ≥8-way racers retrying at the same instant must NOT sleep identical backoff sequences."""

    async def test_sixteen_racers_sleep_pairwise_distinct_sequences(
        self, driver_sleeps: DriverSleepRecorder
    ) -> None:
        barrier = asyncio.Barrier(_RACERS)

        async def _racer() -> object:
            await barrier.wait()
            body = _ConflictsThenReturns(conflicts=_CONFLICTS_PER_RACER)
            return await _txn.retry_on_conflict(body)

        results = await asyncio.gather(*(asyncio.create_task(_racer()) for _ in range(_RACERS)))
        assert results == ["landed"] * _RACERS

        sequences = [tuple(sequence) for sequence in driver_sleeps.by_task.values()]
        lengths = [len(sequence) for sequence in sequences]
        assert lengths == [_CONFLICTS_PER_RACER] * _RACERS, (
            f"premise: expected {_RACERS} racers x {_CONFLICTS_PER_RACER} backoffs, got {lengths}. "
            f"{_hint_if_empty(driver_sleeps.slept)}"
        )
        assert len(set(sequences)) == _RACERS, (
            f"{_RACERS} racers slept only {len(set(sequences))} distinct backoff sequences: racers that "
            f"collide together wake together and collide again (#102 — jitter derived from shared state)"
        )


class TestTheDriverLogsOnlyItsTerminalDisposition:
    """R20 A1 / X22: exhaustion logs EXACTLY ONE record (the last cause); a resolved conflict logs NOTHING —
    on ANY logger at ANY level (a ``before_sleep``/``after`` hook at DEBUG is still a per-attempt storm)."""

    async def test_exhaustion_emits_exactly_one_record_of_any_kind(
        self, driver_sleeps: DriverSleepRecorder, caplog: pytest.LogCaptureFixture
    ) -> None:
        body = _ConflictsThenReturns(conflicts=None)
        caplog.clear()
        with caplog.at_level(logging.DEBUG), pytest.raises(_txn.TxnContentionExhaustedError) as caught:
            await _txn.retry_on_conflict(body, deadline_seconds=1e9, label="sdk3.r7.a1", url="ws://r7")
        records = [(record.name, record.levelname, record.getMessage()) for record in caplog.records]
        assert records == [(_txn.__name__, "WARNING", "store.retry.exhausted")], (
            f"{len(records)} log records for one exhausted call (first: {records[:4]}): the driver logs "
            f"its terminal disposition ONCE and nothing per attempt (X22 — p50 is two attempts per mint)"
        )
        assert getattr(caplog.records[0], "engine_error", None) == f"engine conflict #{body.calls}", (
            "the one record must quote the LAST conflict's cause"
        )
        assert caught.value.attempts == body.calls

    async def test_a_resolved_conflict_emits_no_record_of_any_kind(
        self, driver_sleeps: DriverSleepRecorder, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            body = _ConflictsThenReturns(conflicts=3)
            assert await _txn.retry_on_conflict(body, label="sdk3.r7.a1") == "landed"
        assert driver_sleeps.slept, f"premise: the call retried. {NO_DRIVER_SLEEP_HINT}"
        logged = [(record.name, record.levelname, record.getMessage()) for record in caplog.records]
        assert not logged, (
            f"a conflict that RESOLVED logged {logged[:4]}: contention is the normal case, and silent"
        )


class TestANonConflictErrorIsNeverRetriedOrBackedOff:
    """R18: anything but the seam's signal propagates untouched after ONE attempt, with ZERO backoffs."""

    @pytest.mark.parametrize(
        "error",
        [
            _txn.SurrealConnectionError("transport (may have committed)"),
            _txn.SurrealStoreError("a definite rejection"),
            ValueError("a programming error"),
        ],
        ids=["transport", "store-error", "foreign"],
    )
    async def test_the_first_non_signal_error_propagates_unretried(
        self, driver_sleeps: DriverSleepRecorder, error: BaseException
    ) -> None:
        calls = [0]

        async def _raises() -> None:
            calls[0] += 1
            raise error

        with pytest.raises(type(error)) as caught:
            await _txn.retry_on_conflict(_raises)
        assert caught.value is error and calls[0] == 1 and not driver_sleeps.slept, (
            f"a {type(error).__name__} was retried ({calls[0]} attempts), wrapped, or backed off "
            f"({driver_sleeps.slept}): only the seam's RetryableConflictSignal is ever retried"
        )


class TestALambdaShapedCallerGetsTheAttemptsValue:
    """R20 Leg 2 (iv): 27 callers pass ``lambda: coroutine``. A driver that hands that lambda to tenacity
    raw returns the COROUTINE OBJECT — truthy, nothing executed, no error — the deadliest false clear in
    this packet (found by adversary round 2 as a reference bug)."""

    @pytest.mark.parametrize("conflicts", [0, 2], ids=["first-try", "after-two-conflicts"])
    async def test_the_driver_returns_the_attempts_own_value(
        self, driver_sleeps: DriverSleepRecorder, conflicts: int
    ) -> None:
        sentinel = object()
        body = _ConflictsThenReturns(conflicts=conflicts, value=sentinel)

        # The lambda IS the subject: production callers pass exactly this shape.
        result = await _txn.retry_on_conflict(lambda: body())  # noqa: PLW0108

        assert result is sentinel, (
            f"retry_on_conflict(lambda: …) returned {result!r}, not the attempt's value: an un-awaited "
            f"coroutine (the attempt never ran) — wrap the callable in an `async def` that awaits it"
        )
        assert body.calls == conflicts + 1


# --- R20 A4: ONE wait factory, proven by mutation ----------------------------------------------------------


def _mutate_the_factory(
    monkeypatch: pytest.MonkeyPatch, wait: Callable[[float, float], Any]
) -> WaitFactoryMutation:
    """R20 A4's mutation, from its one home (``_driver_sleeps.mutate_the_wait_factory``)."""
    return mutate_the_wait_factory(monkeypatch, wait)


def _sentinel_wait(_base_s: float, _cap_s: float) -> Any:
    return wait_fixed(_SENTINEL_WAIT_S)


def _window_edge_wait(base_s: float, cap_s: float) -> Any:
    """A DETERMINISTIC stand-in: sleeps the window's upper edge, so each value names its attempt index."""
    return wait_exponential(multiplier=base_s, max=cap_s)


class _RecordingSleep:
    """Scout's injected ``sleep``: records every value AND the module that called it, never waits.

    R29 rider 4 (landmine 1, scout sibling): a native ladder calls the injected sleep from tenacity's
    ``AsyncRetrying`` (``tenacity.asyncio``); a hand-rolled ladder calls it from ``loremaster.scout``."""

    def __init__(self) -> None:
        self.values: list[float] = []
        self.callers: list[str] = []

    async def __call__(self, delay: float) -> None:
        self.values.append(delay)
        if delay != _SCOUT_POLL_S:
            self.callers.append(str(sys._getframe(1).f_globals.get("__name__")))
        await _REAL_SLEEP(0)

    def assert_the_ladder_is_tenacitys(self) -> None:
        stray = sorted({caller for caller in self.callers if caller != "tenacity.asyncio"})
        assert self.callers and not stray, (
            f"scout's reconnect backoff was slept from {stray or 'nowhere'}, not by tenacity's "
            f"AsyncRetrying: the ladder is hand-rolled again (R11/R18 — port it to AsyncRetrying; never "
            f"widen this attribution)"
        )

    @property
    def backoffs(self) -> list[float]:
        """The ladder's sleeps (every sleep that is not the poll cadence)."""
        return [value for value in self.values if value != _SCOUT_POLL_S]


class _DroppingConnection:
    """A connection whose LIVE subscription fails with a transport error — scout's mid-serve drop."""

    async def query(self, *_args: Any, **_kwargs: Any) -> Any:
        raise ConnectionResetError("socket dropped mid-serve")

    async def close(self) -> None:
        return None


async def _run_scout(script: list[str]) -> tuple[_RecordingSleep, int]:
    """Drive ``CommandSubscriber.run`` through ``script`` ('ok' → a connection whose serve drops, 'fail' → a
    refused connect); the connect after the script stops the subscriber, so ``run()`` returns.

    Returns the recorded sleeps and the number of connects made."""
    sleep = _RecordingSleep()
    connects = [0]
    subscriber: CommandSubscriber

    async def _connect() -> Any:
        step = script[connects[0]] if connects[0] < len(script) else "stop"
        connects[0] += 1
        if step == "ok":
            return _DroppingConnection()
        if step == "stop":
            await subscriber.stop()
        raise ConnectionResetError(f"store unreachable ({step})")

    async def _handler(_row: dict[str, Any]) -> None:  # pragma: no cover - never dispatched
        return None

    subscriber = CommandSubscriber(
        connect=_connect,
        handler=_handler,
        poll_interval_s=_SCOUT_POLL_S,
        sleep=sleep,
        backoff_base_s=_SCOUT_BASE_S,
        max_backoff_s=_SCOUT_CAP_S,
    )
    await asyncio.wait_for(subscriber.run(), timeout=10)
    return sleep, connects[0]


class TestTheOneWaitFactoryReachesEveryIn66Site:
    """R20 A4: mutate ``full_jitter`` to ``wait_fixed(SENTINEL)`` ⇒ every in-66 site sleeps SENTINEL.

    In-66 sites (R11/R18; INDEX row 68 names the rest as packet 68's): the conflict driver
    ``_txn.retry_on_conflict`` (every single-statement seam and both transaction paths route through it;
    ``test_retry_seam``'s per-seam sharing pins hold each one to this same mutation) and scout's reconnect
    ladder ``CommandSubscriber.run``. Stated bound: the site set is DECLARED here, not derived — deriving it
    is a source scan, which needs operator approval (packet doc §R7 forks). Re-open trigger: packet 68
    moves its sites onto the factory."""

    async def test_the_conflict_driver_sleeps_the_factorys_wait(
        self, monkeypatch: pytest.MonkeyPatch, driver_sleeps: DriverSleepRecorder
    ) -> None:
        mutation = _mutate_the_factory(monkeypatch, _sentinel_wait)

        assert await _txn.retry_on_conflict(_ConflictsThenReturns(conflicts=3)) == "landed"

        assert driver_sleeps.slept == [_SENTINEL_WAIT_S] * 3, (
            f"with the ONE wait factory mutated to wait_fixed({_SENTINEL_WAIT_S}) the conflict driver "
            f"slept {driver_sleeps.slept}: it builds its own wait (a private copy of the policy, #102/#207)"
        )
        seam_window = (_txn._TXN_CONFLICT_BACKOFF_BASE_SECONDS, _txn._TXN_CONFLICT_BACKOFF_CAP_SECONDS)
        assert set(mutation.calls) == {seam_window}, (
            f"the driver asked the factory for {mutation.calls}, not the seam's own (base, cap)"
        )

    async def test_the_reconnect_ladder_sleeps_the_factorys_wait(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mutation = _mutate_the_factory(monkeypatch, _sentinel_wait)

        sleep, _connects = await _run_scout(["fail", "fail", "ok", "fail"])

        sleep.assert_the_ladder_is_tenacitys()
        assert sleep.backoffs and set(sleep.backoffs) == {_SENTINEL_WAIT_S}, (
            f"with the factory mutated, scout's ladder slept {sleep.backoffs}: it builds its own wait"
        )
        # The serve path's LIVE select rides the conflict driver too, so its (base, cap) may appear as well.
        assert (_SCOUT_BASE_S, _SCOUT_CAP_S) in mutation.calls, (
            f"scout asked the factory for {mutation.calls}, never for the subscriber's own (base, cap)"
        )


class TestTheSubscriberBacksOffBeforeEveryReconnect:
    """Scout ``run``'s docstring: a "bounded exponential backoff after any socket drop (whether the connect
    itself failed or the socket died mid-serve)". Preserved across R18's port of the ladder onto native
    tenacity: a mid-serve drop is backed off BEFORE the reconnect (a store blip drops every subscriber at
    once; an immediate reconnect is the storm), and a live connection RESETS the ladder (the next outage
    starts at the base window, not where the last one ended).

    Observed through the factory with a DETERMINISTIC window edge, so each value names its attempt index:
    ``base·2^(n-1)``."""

    async def test_a_drop_backs_off_before_reconnecting_and_a_live_connection_resets_the_ladder(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _mutate_the_factory(monkeypatch, _window_edge_wait)

        # ok → serve drops → [n=1] → fail → [n=2] → ok → serve drops → [n=1 again] → stop
        sleep, connects = await _run_scout(["ok", "fail", "ok"])

        expected = [_SCOUT_BASE_S, 2 * _SCOUT_BASE_S, _SCOUT_BASE_S]
        sleep.assert_the_ladder_is_tenacitys()
        assert sleep.backoffs == expected, (
            f"scout slept {sleep.backoffs} across ok/drop → fail → ok/drop → stop; expected {expected}: "
            f"a drop is backed off at the base window before reconnecting, a failed reconnect climbs one "
            f"step, a live connection resets the ladder, and a stopped subscriber sleeps nothing more"
        )
        assert connects == 4, f"premise: {connects} connects for a 3-step script plus the stopping one"
