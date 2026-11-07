"""Packet SDK3 contract — RESULT SHAPES at every SDK seam lore reads, on a live store.

Contract index and expected state at HEAD: ``docs/plans/v2/sdk3-python-sdk-3-migration.md`` §3.
SDK 3.0 changes what a call hands back: ``query()`` returns one entry PER STATEMENT (2.0 returned the
first statement's result), datetimes decode as ``PreciseDatetime``, ``RecordID`` renders and hashes
differently in corners, and ``query_raw`` streams on a >=3.3 server. Each pin below states what a
LORE caller relies on and drives it through the production seam that serves it:

* ``run_query`` (every owner's single-statement ``_query``): a statement's rows, a scalar, and —
  load-bearing for every compare-and-set in the tree — an EMPTY result for a lost CAS, never a
  truthy wrapper around one;
* ``execute_read_transaction``: each statement's result at the position the caller composed;
* datetimes: equality, ordering, ISO and pydantic JSON round trips;
* record ids: moved to ``test_sdk3_record_ids`` (round 3, ruling R7 — ids are values, served text is the
  engine's);
* the LIVE wake (``InboxAwaiter``): a notification wakes the waiter long before its poll would.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.inbox_awaiter import InboxAwaiter
from loremaster.scout import _open_command_connection
from loremaster.store._txn import execute_read_transaction, run_query
from loremaster.store.lease import SurrealLeaseStore
from pydantic import BaseModel, ConfigDict
from surrealdb import RecordID
from test_comms_await import _peek_empty, _peek_traffic

logger = logging.getLogger(__name__)

# The compare-and-set race degree (concurrency law: >= 8).
_CAS_RACERS = 8

# Datetimes with microseconds, out of order, spanning a DST-free UTC range — the ordering pin sorts
# them in Python and in the engine and requires the same answer.
_WRITTEN_DATETIMES = [
    datetime(2026, 11, 7, 13, 52, 52, 123456, tzinfo=UTC),
    datetime(2026, 1, 1, 0, 0, 0, 1, tzinfo=UTC),
    datetime(2026, 11, 7, 13, 52, 52, 123455, tzinfo=UTC),
    datetime(2030, 6, 30, 23, 59, 59, 999999, tzinfo=UTC),
    datetime(2026, 11, 7, 13, 52, 52, 123457, tzinfo=UTC),
]

# How many server-stamped rows the precision pin writes: one engine stamp has a ~1/1000 chance of a
# zero sub-microsecond remainder, so requiring ALL of them keeps a truncating build from passing by luck.
_SERVER_STAMPS = 5

# The LIVE-wake pin: the awaiter's budget, a poll cadence it will never reach, how long to let the
# LIVE subscription establish, and the bound within which a notification must wake it.
_AWAIT_BUDGET_SECONDS = 10.0
_NEVER_POLL_SECONDS = 600.0
_LIVE_ESTABLISH_SECONDS = 1.5
_LIVE_WAKE_BOUND_SECONDS = 4.0


class _Stamped(BaseModel):
    """A served model with a datetime field, validated the way lore's wire models are."""

    model_config = ConfigDict(extra="forbid")

    at: datetime


@pytest_asyncio.fixture()
async def store_env() -> AsyncIterator[SurrealEnv]:
    """A fresh database on the TEST store."""
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    try:
        yield env
    finally:
        await drop_database(env)


def _lease_owner(env: SurrealEnv) -> SurrealLeaseStore:
    return SurrealLeaseStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )


@pytest_asyncio.fixture()
async def owner(store_env: SurrealEnv) -> AsyncIterator[SurrealLeaseStore]:
    """One production owner on the fresh database."""
    lease_store = _lease_owner(store_env)
    try:
        yield lease_store
    finally:
        await lease_store.close()


async def _query(owner: SurrealLeaseStore, statement: str, params: dict[str, Any] | None = None) -> Any:
    return await run_query(
        acquire=owner._ensure_connection,
        drop=owner._drop_connection,
        url=owner._url,
        noun="sdk3 shape probe",
        label="sdk3.shape.probe",
        statement=statement,
        params=params,
        logger=logger,
    )


class TestTheSingleStatementDriverReturnsTheStatementsOwnResult:
    """``run_query`` returns what the ONE statement returned — every ``_query`` caller indexes,
    iterates and truth-tests that value directly."""

    async def test_a_select_returns_its_rows(self, owner: SurrealLeaseStore) -> None:
        for n in (3, 1, 2):
            await _query(owner, "CREATE shape SET n = $n", {"n": n})
        rows = await _query(owner, "SELECT n FROM shape ORDER BY n")
        assert rows == [{"n": 1}, {"n": 2}, {"n": 3}]

    async def test_a_scalar_return_is_the_scalar(self, owner: SurrealLeaseStore) -> None:
        assert await _query(owner, "RETURN 42") == 42

    async def test_a_lost_compare_and_set_is_empty_and_a_won_one_is_one_row(
        self, owner: SurrealLeaseStore
    ) -> None:
        await _query(owner, "CREATE shape:one SET v = 1")
        lost = await _query(owner, "UPDATE shape:one SET v = 2 WHERE v = 999")
        assert lost == [], f"a CAS whose WHERE failed must read as EMPTY (lost), got {lost!r}"
        assert not lost, "a lost CAS must be FALSY: every guarded write in the tree truth-tests it"
        won = await _query(owner, "UPDATE shape:one SET v = 2 WHERE v = 1")
        assert isinstance(won, list) and len(won) == 1 and won[0]["v"] == 2, (
            f"a won CAS must read as its one updated row, got {won!r}"
        )

    async def test_exactly_one_of_eight_racing_claims_wins(self, store_env: SurrealEnv) -> None:
        racers = [_lease_owner(store_env) for _ in range(_CAS_RACERS)]
        try:
            await _query(racers[0], "CREATE claim:one SET holder = NONE")
            outcomes = await asyncio.gather(
                *(
                    _query(racer, "UPDATE claim:one SET holder = $me WHERE holder = NONE", {"me": index})
                    for index, racer in enumerate(racers)
                )
            )
            winners = [index for index, outcome in enumerate(outcomes) if outcome]
            assert len(winners) == 1, (
                f"{len(winners)} of {_CAS_RACERS} racers believe they won one claim "
                f"(outcomes {outcomes!r}) — a lost CAS read as a win runs the claimed work twice"
            )
            holder = await _query(racers[0], "SELECT VALUE holder FROM claim:one")
            assert holder == [winners[0]]
        finally:
            for racer in racers:
                await racer.close()


class TestTheReadTransactionReturnsEachStatementAtItsPosition:
    """``execute_read_transaction`` hands back one result per statement, by the position the caller
    composed — the shape SDK 3.0's streamed ``query_raw`` must rebuild exactly."""

    async def test_results_line_up_with_the_composed_statements(self, owner: SurrealLeaseStore) -> None:
        results = await execute_read_transaction(
            "BEGIN;\nCREATE shape:a SET n = 1;\nLET $ignored = 7;\nSELECT n FROM shape:a;\nCOMMIT;",
            {},
            acquire=owner._ensure_connection,
            drop=owner._drop_connection,
            url=owner._url,
        )
        select_rows = [entry for entry in results if entry == [{"n": 1}]]
        assert len(select_rows) == 1, f"the SELECT's rows are not in the result list: {results!r}"
        create_index = next(
            index
            for index, entry in enumerate(results)
            if isinstance(entry, list) and entry and isinstance(entry[0], dict) and "id" in entry[0]
        )
        assert results.index([{"n": 1}]) == create_index + 2, (
            f"the statements' results are not in composed order (CREATE, LET, SELECT): {results!r}"
        )


class TestDatetimesSurviveTheRoundTrip:
    """lore stores, compares, sorts, serialises and re-parses datetimes it reads back."""

    async def test_a_written_datetime_reads_back_equal_ordered_and_serialisable(
        self, owner: SurrealLeaseStore
    ) -> None:
        for index, written in enumerate(_WRITTEN_DATETIMES):
            await _query(owner, "CREATE stamp CONTENT $row", {"row": {"i": index, "at": written}})
        rows = await _query(owner, "SELECT i, at FROM stamp ORDER BY at")
        read_back = [row["at"] for row in rows]

        assert read_back == sorted(_WRITTEN_DATETIMES), "engine order and Python order disagree"
        by_index = {row["i"]: row["at"] for row in rows}
        for index, written in enumerate(_WRITTEN_DATETIMES):
            read = by_index[index]
            assert isinstance(read, datetime)
            assert read == written, f"wrote {written!r}, read back {read!r}"
            assert read.utcoffset() == timedelta(0), f"read back {read!r} is not tz-aware UTC"
            assert datetime.fromisoformat(read.isoformat()) == written
            assert _Stamped.model_validate_json(_Stamped(at=read).model_dump_json()).at == written

    async def test_a_server_stamped_datetime_matches_its_own_row_when_bound_back(
        self, owner: SurrealLeaseStore
    ) -> None:
        """**Operator fork F3** (packet doc §5). The engine stamps nanoseconds; SDK 2.0 truncates them
        on read, so a stamp read back and bound as a parameter no longer equals the stored value
        (a cursor or CAS keyed on it misses its own row). RED at HEAD; GREEN on a build that keeps
        the precision the engine sent."""
        for _ in range(_SERVER_STAMPS):
            await _query(owner, "CREATE served SET at = time::now()")
        rows = await _query(owner, "SELECT id, at FROM served")
        assert len(rows) == _SERVER_STAMPS
        misses = []
        for row in rows:
            matched = await _query(owner, "SELECT VALUE id FROM served WHERE at = $at", {"at": row["at"]})
            if matched != [row["id"]]:
                misses.append((row["at"], matched))
        assert not misses, (
            f"{len(misses)} of {_SERVER_STAMPS} server-stamped datetimes, read back and bound as a "
            f"parameter, did not match their own row: {misses!r}"
        )


class TestALiveNotificationWakesTheInboxAwaiter:
    """The awaiter's LIVE subscription (``LIVE SELECT`` via ``query()``, then ``subscribe_live`` on the
    id it returned) is how ``await`` answers in milliseconds instead of at its next poll. Its poll is
    set beyond the budget here, so only a LIVE wake can end the wait early."""

    async def _await_with(self, env: SurrealEnv, *, relate: bool) -> tuple[float, float | None]:
        """Run one await; returns (seconds the await took, seconds from the edge write to wake)."""
        agent_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"sdk3-{env.database}"))
        traffic_ready = asyncio.Event()

        async def drain(*, agent_id: str, limit: int, peek: bool = False, since: int | None = None) -> Any:
            del agent_id, limit, peek, since
            return _peek_traffic(1) if traffic_ready.is_set() else _peek_empty()

        awaiter = InboxAwaiter(
            connect=functools.partial(
                _open_command_connection,
                url=env.url,
                namespace=env.namespace,
                database=env.database,
                user=env.user,
                password=env.password,
            ),
            drain=drain,
            budget_s=_AWAIT_BUDGET_SECONDS,
            poll_interval_s=_NEVER_POLL_SECONDS,
        )
        admin = await connect_admin(env)
        try:
            await run(admin, "DEFINE TABLE IF NOT EXISTS to TYPE RELATION")
            started = time.monotonic()
            waiting = asyncio.create_task(awaiter.await_inbox(agent_id=agent_id, limit=10))
            await asyncio.sleep(_LIVE_ESTABLISH_SECONDS)
            traffic_ready.set()
            written_at = time.monotonic()
            if relate:
                await run(
                    admin,
                    "RELATE $message->to->$agent",
                    {"message": RecordID("message", "m1"), "agent": RecordID("agent", agent_id)},
                )
            result = await waiting
            finished = time.monotonic()
        finally:
            await admin.close()
        assert result.entries, "the await returned no traffic although traffic was ready"
        return finished - started, (finished - written_at) if relate else None

    async def test_a_relate_to_the_waiting_agent_wakes_it_within_seconds(self, store_env: SurrealEnv) -> None:
        _, woke_after = await self._await_with(store_env, relate=True)
        assert woke_after is not None and woke_after < _LIVE_WAKE_BOUND_SECONDS, (
            f"the awaiter answered {woke_after:.1f}s after the edge was written (budget "
            f"{_AWAIT_BUDGET_SECONDS}s, poll {_NEVER_POLL_SECONDS}s): the LIVE notification never "
            f"woke it — the subscription is not attached to the live query the statement created"
        )

    async def test_control_without_a_notification_the_awaiter_waits_out_its_budget(
        self, store_env: SurrealEnv
    ) -> None:
        """The control that makes the pin above mean something: with traffic ready but NO edge
        written (so no LIVE notification), the same awaiter does not answer early."""
        took, _ = await self._await_with(store_env, relate=False)
        assert took >= _AWAIT_BUDGET_SECONDS, (
            f"with no LIVE notification the awaiter still answered after {took:.1f}s — something other "
            f"than LIVE ends the wait early, so the pin above cannot attribute its wake to LIVE"
        )
