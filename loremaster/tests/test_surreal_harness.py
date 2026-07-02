"""Pins ``_surreal_harness.drop_database``'s teardown retry behaviour (task #18).

BUG: ``drop_database`` (the per-test ``REMOVE DATABASE IF EXISTS`` teardown every
store/manifest fixture uses) intermittently raised
``surrealdb.errors.QueryError: Transaction conflict: Resource busy. This
transaction can be retried`` — an ENGINE-FLAGGED RETRYABLE conflict racing
background RocksDB/index work on the shared dev server, not a real teardown
failure. It hit ~30-50% of standalone store-suite runs, turning a green suite
red on a different random test's teardown each time.

THE FIX mirrors the already-landed write-path handling in
``loremaster.store._txn`` (``_is_retryable_conflict`` /
``_RETRYABLE_CONFLICT_MARKER`` / ``_MAX_TXN_CONFLICT_ATTEMPTS``): a bounded
retry loop around the ``REMOVE DATABASE`` statement, retrying ONLY when the
engine's "can be retried" marker is present, raising every other error (and a
conflict on the final attempt) immediately.

WHY THIS TEST DOES NOT DEPEND ON THE LIVE RACE FIRING: the live conflict is a
genuine, rare race against background server work — a test that only passes
when that race happens to occur is not a real pin. Instead, this monkeypatches
the SDK connection factory (``_surreal_harness.AsyncSurreal``) with a fake
connection whose ``query`` is scripted to raise the EXACT engine error (or a
non-retryable one) on demand, so the retry/no-retry decision is pinned
deterministically, every run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import _surreal_harness
import pytest
from _surreal_harness import SurrealEnv
from surrealdb.errors import QueryError

# A fake connection target; the real topology is irrelevant since ``AsyncSurreal``
# itself is monkeypatched to return the fake below.
_FAKE_ENV = SurrealEnv(
    url="ws://127.0.0.1:19999/rpc",
    user="root",
    password="fake",
    namespace="lore_test",
    database="test_fake_db",
    dim=8,
)

# The exact live message reported in the bug (surrealdb.errors.QueryError,
# kind "Query") — the engine's own retryable-conflict marker is the substring
# ``_surreal_harness._RETRYABLE_CONFLICT_MARKER`` ("can be retried").
_CONFLICT_MESSAGE = "Transaction conflict: Resource busy. This transaction can be retried"

# A same-shaped ``QueryError`` that is emphatically NOT the retryable conflict —
# a genuine domain rejection teardown must never silently swallow.
_NON_RETRYABLE_MESSAGE = "Specified database does not exist"


def _conflict_error() -> QueryError:
    return QueryError("Query", _CONFLICT_MESSAGE)


def _non_retryable_error() -> QueryError:
    return QueryError("Query", _NON_RETRYABLE_MESSAGE)


@dataclass
class _FakeConnection:
    """Stand-in for the SDK connection ``drop_database`` drives.

    ``query_outcomes`` is consumed in order, one entry per ``query()`` call: a
    ``BaseException`` instance is raised, anything else is returned as the
    (unused) query result. ``query_calls`` records how many times ``query()``
    was actually invoked, so a test can assert the retry loop ran exactly as
    many times as intended — neither swallowing on the first try nor looping
    past a non-retryable error.
    """

    query_outcomes: list[BaseException | None]
    query_calls: int = field(default=0, init=False)
    closed: bool = field(default=False, init=False)

    async def signin(self, credentials: dict[str, Any]) -> None:
        return None

    async def use(self, namespace: str, database: str) -> None:
        return None

    async def query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        outcome = self.query_outcomes[self.query_calls]
        self.query_calls += 1
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    async def close(self) -> None:
        self.closed = True


def _patch_connection(monkeypatch: pytest.MonkeyPatch, fake: _FakeConnection) -> None:
    monkeypatch.setattr(_surreal_harness, "AsyncSurreal", lambda url: fake)


class TestDropDatabaseRetriesRetryableConflict:
    """A retryable engine conflict is retried, bounded, and never reaches the caller."""

    async def test_retries_past_conflicts_then_succeeds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Two retryable conflicts, then success on the third attempt — well
        # within the bound, so teardown must swallow all three and return.
        fake = _FakeConnection(query_outcomes=[_conflict_error(), _conflict_error(), None])
        _patch_connection(monkeypatch, fake)

        await _surreal_harness.drop_database(_FAKE_ENV)

        assert fake.query_calls == 3
        assert fake.closed is True

    async def test_exhausting_all_attempts_on_sustained_conflict_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A conflict on EVERY attempt (more than the retry ceiling can absorb)
        # must eventually raise — the bound is real, not an infinite loop.
        fake = _FakeConnection(query_outcomes=[_conflict_error() for _ in range(50)])
        _patch_connection(monkeypatch, fake)

        with pytest.raises(QueryError) as exc_info:
            await _surreal_harness.drop_database(_FAKE_ENV)

        assert _CONFLICT_MESSAGE in str(exc_info.value)
        # Bounded: some small ceiling, not 50.
        assert 1 < fake.query_calls < 10


class TestDropDatabasePropagatesNonRetryableErrors:
    """A non-retryable rejection propagates immediately — never retried, never swallowed."""

    async def test_propagates_on_first_attempt_without_retrying(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake = _FakeConnection(query_outcomes=[_non_retryable_error()])
        _patch_connection(monkeypatch, fake)

        with pytest.raises(QueryError) as exc_info:
            await _surreal_harness.drop_database(_FAKE_ENV)

        assert _NON_RETRYABLE_MESSAGE in str(exc_info.value)
        # Exactly one attempt: a non-retryable error is never retried.
        assert fake.query_calls == 1
