"""Packet SDK3 contract, round 2 — the RETIREMENT pins of operator ruling R1.

``docs/plans/v2/sdk3-rulings.md`` R1: an inventory row whose underlying SDK defect is GONE on SDK
3.0.0 + engine 3.3.5 is retired (its workaround deleted), and ships with a pin that FAILS if the
workaround is still needed — the formerly-broken case driven through the plain SDK path, asserting
the correct behaviour — plus a mutation proof that re-introducing the defect's symptom reddens it
(packet doc §3.2). Each pin here is therefore RED on SDK 2.0 (the defect is present at HEAD) and
GREEN on SDK 3.0; that is the evidence the workaround can go.

Rows (packet doc §3): I-1 KeyError-as-transport · I-2 raw ``websockets`` errors and a dead socket
staying dead · I-6 the bare ``"TransactionConflict"`` literal (#111) · I-7 #576's per-owner
self-heal for an IDLE owner (simplified, not deleted).

The raw SDK error is read as the ``__cause__`` of what the production driver raised (the
``test_fixwave_a28b_63c_i_a`` known-bound idiom), so every SDK call still runs inside the driver.
"""

from __future__ import annotations

import asyncio
import dataclasses
import logging
from collections.abc import AsyncIterator
from typing import Any

import pytest_asyncio
from _sdk3_proxy import StoreBounceProxy
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
)
from loremaster.store._txn import (
    RetryableConflictSignal,
    SurrealConnectionError,
    retry_on_conflict,
    run_query,
)
from surrealdb.errors import SurrealError, parse_query_error

logger = logging.getLogger(__name__)

# Calls in flight at the drop (concurrency law: >= 8), and the statement that keeps them in flight.
_IN_FLIGHT_CALLS = 8
_IN_FLIGHT_STATEMENT = "RETURN sleep(3s)"
_IN_FLIGHT_SETTLE_SECONDS = 0.5
_RACING_FAILURE_BOUND_SECONDS = 20.0

# The idle-bounce leg: outage and idle time (packet doc §4 L1 explains both values).
_SHORT_OUTAGE_SECONDS = 0.5
_IDLE_AFTER_BOUNCE_SECONDS = 5.0

# The conflict-typing leg: racers and statements per racer (research §D-1: 16-way contention on one
# row conflicts on both paths on 3.3.5; probe P6 measured 29 per-statement conflict entries at 16x5).
_RACERS = 16
_UPDATES_PER_RACER = 20
_TRANSACTIONS_PER_RACER = 5
_CONFLICT_DETAIL_KIND = "TransactionConflict"
_TXN_INCREMENT = "BEGIN; LET $c = (SELECT VALUE n FROM ONLY hot:row); UPDATE hot:row SET n = $c + 1; COMMIT;"


@pytest_asyncio.fixture()
async def store_env() -> AsyncIterator[SurrealEnv]:
    """A fresh database on the TEST store, created directly."""
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    try:
        yield env
    finally:
        await drop_database(env)


@pytest_asyncio.fixture()
async def proxy(store_env: SurrealEnv) -> AsyncIterator[StoreBounceProxy]:
    """A proxy in front of the TEST store (packet doc §4: a restart as the client sees it)."""
    bounce_proxy = StoreBounceProxy(upstream_url=store_env.url)
    await bounce_proxy.start()
    try:
        yield bounce_proxy
    finally:
        await bounce_proxy.close()


@pytest_asyncio.fixture()
async def proxied_connection(store_env: SurrealEnv, proxy: StoreBounceProxy) -> AsyncIterator[Any]:
    """A plain signed-in SDK connection (the harness opener) that reaches the store through the proxy."""
    connection = await connect_admin(dataclasses.replace(store_env, url=proxy.url))
    try:
        yield connection
    finally:
        try:
            await connection.close()
        except Exception:  # noqa: BLE001 - a socket the test severed may already be gone
            logger.debug("sdk3.retirement.close_failed")


async def _on(connection: Any, url: str, statement: str) -> Any:
    """One statement through the production driver on a FIXED plain connection that is never dropped,
    so the SDK alone decides what the next call on it sees."""

    async def acquire() -> Any:
        return connection

    async def keep(failed: Any) -> None:
        del failed

    return await run_query(
        acquire=acquire,
        drop=keep,
        url=url,
        noun="sdk3 retirement probe",
        label="sdk3.retirement.probe",
        statement=statement,
        logger=logger,
    )


class TestAnInFlightDropIsATypedSdkTransportError:
    """I-1 / I-2. SDK 2.0 failed an in-flight request with a raw ``builtins.KeyError(<request uuid>)``
    and then a raw ``websockets`` ``ConnectionClosedError`` on every later call, which is why the
    drivers catch ``KeyError`` and ``WebSocketException`` (store reference §3). Retiring those arms
    needs the SDK itself to raise its own typed transport error."""

    async def test_every_call_in_flight_at_a_drop_has_a_typed_sdk_cause(
        self, proxied_connection: Any, proxy: StoreBounceProxy
    ) -> None:
        await _on(proxied_connection, proxy.url, "RETURN 1")
        in_flight = [
            asyncio.create_task(_on(proxied_connection, proxy.url, _IN_FLIGHT_STATEMENT))
            for _ in range(_IN_FLIGHT_CALLS)
        ]
        await asyncio.sleep(_IN_FLIGHT_SETTLE_SECONDS)
        assert not any(task.done() for task in in_flight), "premise: the calls are in flight at the cut"
        await proxy.go_down()
        await proxy.come_up()
        outcomes = await asyncio.wait_for(
            asyncio.gather(*in_flight, return_exceptions=True), _RACING_FAILURE_BOUND_SECONDS
        )

        assert all(isinstance(outcome, SurrealConnectionError) for outcome in outcomes), (
            f"premise: the driver classified every in-flight failure as transport: {outcomes!r}"
        )
        untyped = [
            f"{type(outcome.__cause__).__module__}.{type(outcome.__cause__).__name__}"
            for outcome in outcomes
            if not isinstance(outcome.__cause__, SurrealError)
        ]
        assert not untyped, (
            f"{len(untyped)} of {_IN_FLIGHT_CALLS} in-flight calls failed with an UNTYPED SDK error "
            f"{sorted(set(untyped))} — the driver's KeyError / websockets arms are still needed"
        )


class TestAnIdleConnectionComesBackOnItsOwn:
    """I-2 / I-7 (#576). SDK 2.0 left a socket dead after any restart: every later call raised the raw
    ``websockets`` error until lore dropped the handle. Simplifying the per-owner self-heal needs the SDK
    to reconnect AND replay the session (auth, namespace, database) without the caller's help."""

    async def test_the_same_connection_serves_an_authenticated_call_in_its_session_after_a_bounce(
        self, proxied_connection: Any, proxy: StoreBounceProxy, store_env: SurrealEnv
    ) -> None:
        await _on(proxied_connection, proxy.url, "RETURN 1")
        await proxy.bounce(down_seconds=_SHORT_OUTAGE_SECONDS)
        await asyncio.sleep(_IDLE_AFTER_BOUNCE_SECONDS)

        try:
            session = await _on(proxied_connection, proxy.url, "RETURN [session::ns(), session::db()]")
            tables = await _on(proxied_connection, proxy.url, "INFO FOR DB")
        except SurrealConnectionError as error:
            cause = error.__cause__
            raise AssertionError(
                f"the connection did not come back on its own after the bounce: "
                f"{type(cause).__module__}.{type(cause).__name__}: {cause}"
            ) from error
        assert session == [store_env.namespace, store_env.database], (
            f"the reconnected session lost its namespace/database: {session!r}"
        )
        assert isinstance(tables, dict), f"the reconnected session is not signed in: {tables!r}"


class TestTheSdkTypesALiveTransactionConflict:
    """I-6 (#111). SDK 2.0 shipped no conflict predicate, so ``_txn`` keys on a bare
    ``"TransactionConflict"`` literal of its own. Retiring it needs the SDK's
    ``QueryError.is_transaction_conflict`` to say yes on every LIVE conflict, on BOTH paths: the raised
    single-statement error and the parsed per-statement entry of a transaction."""

    async def test_every_live_conflict_is_typed_by_the_sdk_on_both_paths(self, store_env: SurrealEnv) -> None:
        racers = [await connect_admin(store_env) for _ in range(_RACERS)]
        raised: list[BaseException] = []
        parsed: list[BaseException] = []
        try:

            async def bump(connection: Any) -> None:
                async def attempt() -> Any:
                    try:
                        return await connection.query("UPDATE hot:row SET n += 1")
                    except SurrealError as error:
                        details = getattr(error, "details", None)
                        if isinstance(details, dict) and details.get("kind") == _CONFLICT_DETAIL_KIND:
                            raised.append(error)
                            raise RetryableConflictSignal() from error
                        raise

                for _ in range(_UPDATES_PER_RACER):
                    await retry_on_conflict(attempt, label="sdk3.retirement.single")

            async def transact(connection: Any) -> None:
                async def attempt() -> Any:
                    response = await connection.query_raw(_TXN_INCREMENT, {})
                    conflicts = [
                        entry
                        for entry in response.get("result") or []
                        if entry.get("status") == "ERR"
                        and (entry.get("details") or {}).get("kind") == _CONFLICT_DETAIL_KIND
                    ]
                    if conflicts:
                        parsed.extend(parse_query_error(entry) for entry in conflicts)
                        raise RetryableConflictSignal()
                    return response

                for _ in range(_TRANSACTIONS_PER_RACER):
                    await retry_on_conflict(attempt, label="sdk3.retirement.txn")

            async def first_write() -> Any:
                return await racers[0].query("UPSERT hot:row SET n = 0")

            await retry_on_conflict(first_write, label="sdk3.retirement.seed")
            await asyncio.gather(*(bump(connection) for connection in racers))
            await asyncio.gather(*(transact(connection) for connection in racers))
        finally:
            for connection in racers:
                await connection.close()

        assert parsed, "premise: 16-way transactions on one row produced no conflict entry to classify"
        untyped = [
            error
            for error in [*raised, *parsed]
            if getattr(error, "is_transaction_conflict", None) is not True
        ]
        assert not untyped, (
            f"{len(untyped)} of {len(raised) + len(parsed)} live conflicts (raised {len(raised)}, "
            f"per-statement {len(parsed)}) are not typed by the SDK's own `is_transaction_conflict` — "
            f"the bare literal is still needed: {[type(error).__name__ for error in untyped][:5]}"
        )
