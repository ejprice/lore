"""Packet SDK3 contract, round 5 — R11 (every hand-rolled retry goes onto tenacity) as amended by R12 F22: the
retry DRIVER's behaviour, pinned so a port to tenacity's ``AsyncRetrying`` must keep it.

``docs/plans/v2/sdk3-rulings.md`` R11 rider: "Removed-behaviour inventory covers the deadline, the rollback
log
per attempt, and the attempt-count/exhaustion fate". The conflict-retry pins that already exist (T1/T2 in
``test_sdk3_txn_classification``, RP3, the whole of ``test_retry_seam``) stay green UNCHANGED on the tenacity
reference (packet doc §ROUND 5); these pins add what a port can lose without any of them noticing:

* the exhaustion FATE — tenacity's own ``RetryError`` is never what a caller sees; the seam raises
  ``TxnContentionExhaustedError`` (a ``SurrealStoreError``) carrying the attempt count, and logs EXACTLY ONE
  ``store.retry.exhausted`` record quoting the LAST conflict's cause (each attempt's cause differs here, so a
  build quoting the first, or logging per attempt, fails);
* the DEADLINE is PER CALL — a build that constructs one retry object (or one stop policy) and reuses it
across
  calls carries the first call's deadline into the next; alternating a zero deadline and a huge one shows each
  call reading its own, both inside the attempt FLOOR (zero deadline → exactly the floor) and up to the
  CEILING;
* the attempt count each fate reports equals the attempts actually made (counted by the attempt body itself).

No pin here names tenacity: they drive ``_txn.retry_on_conflict`` and observe what it raises, logs and calls.
Sleep is silenced (``asyncio.sleep`` → no-op), as ``test_retry_seam`` does, so a 64-attempt exhaustion is
cheap.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import pytest
from loremaster.store import _txn

_REAL_SLEEP = asyncio.sleep


async def _no_sleep(_seconds: float) -> None:
    await _REAL_SLEEP(0)


class _AlwaysConflicting:
    """An attempt body that raises the seam's retry signal every time, each chained from a DIFFERENT cause."""

    def __init__(self) -> None:
        self.calls = 0

    async def __call__(self) -> Any:
        self.calls += 1
        try:
            raise RuntimeError(f"engine conflict #{self.calls}")
        except RuntimeError as cause:
            raise _txn.RetryableConflictSignal() from cause


@pytest.fixture(autouse=True)
def _silenced_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(asyncio, "sleep", _no_sleep)


class TestTheExhaustionFateIsTheSeamsTypedError:
    """X22/X23 (R4.8): the terminal disposition of a conflict that never resolves."""

    async def test_exhaustion_raises_the_typed_error_and_logs_only_the_last_cause(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        body = _AlwaysConflicting()
        with caplog.at_level(logging.WARNING, logger=_txn.__name__):
            with pytest.raises(_txn.SurrealStoreError) as caught:
                await _txn.retry_on_conflict(
                    body, deadline_seconds=1e9, label="sdk3.r5.exhaustion.probe", url="ws://sdk3-r5"
                )
        error = caught.value
        assert type(error) is _txn.TxnContentionExhaustedError, (
            f"an exhausted conflict surfaced as {type(error).__module__}.{type(error).__name__}: the seam's "
            f"typed "
            f"fate (TxnContentionExhaustedError) is the contract — a retry library's own error must never "
            f"leak"
        )
        ceiling = _txn._TXN_CONFLICT_ATTEMPT_CEILING
        assert body.calls == ceiling and error.attempts == ceiling, (
            f"made {body.calls} attempts, reported {error.attempts}; with an unreachable deadline the "
            f"CEILING "
            f"({ceiling}) is the only stop"
        )
        exhausted = [record for record in caplog.records if record.getMessage() == "store.retry.exhausted"]
        assert len(exhausted) == 1, (
            f"{len(exhausted)} 'store.retry.exhausted' records: the disposition is logged ONCE (never per "
            f"attempt)"
        )
        record = exhausted[0]
        assert getattr(record, "engine_error", None) == f"engine conflict #{ceiling}", (
            f"the exhaustion record quotes {getattr(record, 'engine_error', None)!r}; it must quote the LAST "
            f"conflict's cause (engine conflict #{ceiling})"
        )
        assert getattr(record, "attempts", None) == ceiling and getattr(record, "label", None) == (
            "sdk3.r5.exhaustion.probe"
        ), f"the exhaustion record lost its attempt count or the caller's label: {record.__dict__!r}"

    async def test_a_conflict_that_resolves_returns_the_value_and_logs_nothing(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        calls = [0]

        async def _resolves_on_the_third() -> str:
            calls[0] += 1
            if calls[0] < 3:
                raise _txn.RetryableConflictSignal()
            return "landed"

        with caplog.at_level(logging.WARNING, logger=_txn.__name__):
            assert await _txn.retry_on_conflict(_resolves_on_the_third, label="sdk3.r5.resolve") == "landed"
        assert calls[0] == 3
        assert not [record for record in caplog.records if record.getMessage() == "store.retry.exhausted"]

    async def test_anything_but_the_signal_propagates_untouched_after_one_attempt(self) -> None:
        calls = [0]
        sentinel = _txn.SurrealConnectionError("transport (may have committed)")

        async def _transport() -> None:
            calls[0] += 1
            raise sentinel

        with pytest.raises(_txn.SurrealConnectionError) as caught:
            await _txn.retry_on_conflict(_transport)
        assert caught.value is sentinel and calls[0] == 1, (
            "a non-conflict error is never retried, never wrapped"
        )


class TestTheDeadlineIsReadPerCall:
    """X21 (R4.8): ``deadline_seconds`` bounds THIS call's retries once the attempt FLOOR is met."""

    async def test_alternating_deadlines_each_govern_their_own_call(self) -> None:
        floor, ceiling = _txn._MAX_TXN_CONFLICT_ATTEMPTS, _txn._TXN_CONFLICT_ATTEMPT_CEILING
        observed = []
        for deadline in (0.0, 1e9, 0.0):
            body = _AlwaysConflicting()
            with pytest.raises(_txn.TxnContentionExhaustedError) as caught:
                await _txn.retry_on_conflict(body, deadline_seconds=deadline)
            observed.append((deadline, body.calls, caught.value.attempts))
        assert observed == [(0.0, floor, floor), (1e9, ceiling, ceiling), (0.0, floor, floor)], (
            f"(deadline, attempts made, attempts reported) = {observed}; a zero deadline stops at the FLOOR "
            f"({floor}) and an unreachable one at the CEILING ({ceiling}), each call by its OWN deadline"
        )

    async def test_the_default_deadline_is_read_at_call_time(self, monkeypatch: pytest.MonkeyPatch) -> None:
        floor = _txn._MAX_TXN_CONFLICT_ATTEMPTS
        monkeypatch.setattr(_txn, "_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS", 0.0)
        body = _AlwaysConflicting()
        with pytest.raises(_txn.TxnContentionExhaustedError):
            await _txn.retry_on_conflict(body)
        assert body.calls == floor, (
            f"with the module default repointed to 0 s the call made {body.calls} attempts, not the floor "
            f"{floor}: "
            f"the default deadline was frozen at import or at construction"
        )
