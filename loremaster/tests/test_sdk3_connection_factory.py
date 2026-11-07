"""Packet SDK3 contract, round 3 — operator ruling R5 (as amended by R7): reconnect forever, FINITE
timeouts with NAMED overrides, and a write whose outcome the client cannot know is raised AS unknown.

``docs/plans/v2/sdk3-rulings.md`` R5/R7. ONE shared connection factory (``ReconnectOptions(attempts=-1,
retry_delay=0.5, retry_delay_max=2.0)``) replaces the 18 per-owner self-heals; a finite default request
timeout (SDK 3.0's 30 s until measured) plus a named override, applied with ``with db.timeout(N):``, for
each known-long operation. Riders, each pinned here or in ``test_sdk3_lifecycle``:

* a call during an outage fails within its bound — ``TestACallDuringAnOutageFailsWithinItsBound``;
* a call after the store returns answers within ~2 s (L6) — ``test_sdk3_lifecycle``
  ``TestRecoveryLatencyAfterALongOutage``, quantified over EVERY owner (an owner that bypasses the shared
  factory keeps the SDK default backoff and fails it);
* a long DDL under its override survives past 30 s — ``TestALongOperationOutlivesTheDefaultTimeout``
  (COST, stated per the rider: ~35 s for the pin + ~32 s for its control);
* a timed-out or in-flight-dropped WRITE is raised as "outcome unknown" — the R7 measurement CONFIRMED it
  (SDK streaming + timeout → stream cancel, nothing committed; ``streaming=False`` + timeout → the engine
  KEEPS RUNNING AND COMMITS): ``TestAWriteWhoseOutcomeIsUnknownIsRaisedAsUnknown``;
* R7: "the shared factory sets streaming EXPLICITLY, pinned" — the VALUE is not ruled (packet doc §5 fork
  F11). ``TestATimedOutWriteUnderTheFactoryCommitsNothing`` pins the RECOMMENDED reading (streaming on:
  a timed-out write is cancelled). Ruling ``streaming=False`` inverts its final assertion.

Names this contract FIXES for the builder (packet doc §4.R5): ``store._txn.SURREAL_REQUEST_TIMEOUT_SECONDS``
(the finite default) and ``store._txn.SurrealOutcomeUnknownError`` (a ``SurrealConnectionError`` subclass,
so every existing transport handler still catches it while a caller that must not re-apply a write can
tell it apart). Both are read with ``getattr`` so a build lacking them fails each pin on its own
assertion rather than failing the whole module at import.
"""

from __future__ import annotations

import asyncio
import dataclasses
import logging
import math
import time
from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
from _sdk3_proxy import StoreBounceProxy
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.store import _txn
from loremaster.store._txn import SurrealConnectionError, execute_transaction, run_query
from loremaster.store.lease import SurrealLeaseStore
from loremaster.store.surreal import SurrealStore

logger = logging.getLogger(__name__)

# How long past its own bound a call during an outage may take to fail (scheduling slack).
_OUTAGE_FAILURE_SLACK_SECONDS = 10.0

# How far past the default timeout the slow-store hold delays a reply.
_HOLD_PAST_DEFAULT_SECONDS = 2.0

# The in-flight write pins: writes in flight at the cut (concurrency law: >= 8), and how long each
# write runs undisturbed (an embedded ``sleep`` — probed on 3.3.5: the write takes it and commits).
_IN_FLIGHT_WRITES = 8
_SLOW_WRITE = "CREATE type::record('probe', $key) SET n = 1, slow = sleep(3s)"
_SLOW_TXN = "BEGIN;\nCREATE type::record('probe', $key) SET n = 1;\nLET $wait = sleep(3s);\nCOMMIT;"
_IN_FLIGHT_SETTLE_SECONDS = 0.5
_RACING_FAILURE_BOUND_SECONDS = 20.0

# The timed-out write pin: a scoped override far shorter than the write, and how long to wait before
# reading whether the write landed (past the write's own duration).
_SHORT_OVERRIDE_SECONDS = 1.0
_AFTER_WRITE_WOULD_HAVE_FINISHED_SECONDS = 4.0


def _required(name: str) -> Any:
    """A name this contract fixes on ``store._txn``; a build lacking it fails the calling pin."""
    value = getattr(_txn, name, None)
    assert value is not None, (
        f"store._txn.{name} does not exist — packet doc §4.R5 fixes it as part of the shared connection "
        f"factory's contract"
    )
    return value


@pytest_asyncio.fixture()
async def store_env() -> AsyncIterator[SurrealEnv]:
    """A fresh database on the TEST store, created directly."""
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    try:
        await run(setup_connection, "DEFINE TABLE IF NOT EXISTS probe SCHEMALESS")
    finally:
        await setup_connection.close()
    try:
        yield env
    finally:
        await drop_database(env)


@pytest_asyncio.fixture()
async def proxy(store_env: SurrealEnv) -> AsyncIterator[StoreBounceProxy]:
    bounce_proxy = StoreBounceProxy(upstream_url=store_env.url)
    await bounce_proxy.start()
    try:
        yield bounce_proxy
    finally:
        await bounce_proxy.close()


def _lease_owner(env: SurrealEnv) -> SurrealLeaseStore:
    return SurrealLeaseStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )


@pytest_asyncio.fixture()
async def proxied_owner(store_env: SurrealEnv, proxy: StoreBounceProxy) -> AsyncIterator[SurrealLeaseStore]:
    owner = _lease_owner(dataclasses.replace(store_env, url=proxy.url))
    try:
        yield owner
    finally:
        await owner.close()


@pytest_asyncio.fixture()
async def direct_owner(store_env: SurrealEnv) -> AsyncIterator[SurrealLeaseStore]:
    owner = _lease_owner(store_env)
    try:
        yield owner
    finally:
        await owner.close()


async def _call(owner: Any, statement: str, params: dict[str, Any] | None = None) -> Any:
    return await run_query(
        acquire=owner._ensure_connection,
        drop=owner._drop_connection,
        url=owner._url,
        noun="sdk3 factory probe",
        label="sdk3.factory.probe",
        statement=statement,
        params=params,
        logger=logger,
    )


async def _transact(owner: Any, statement: str, params: dict[str, Any]) -> None:
    await execute_transaction(
        statement, params, acquire=owner._ensure_connection, drop=owner._drop_connection, url=owner._url
    )


class TestACallDuringAnOutageFailsWithinItsBound:
    """R5 rider (3a). With reconnect-forever, a request made while the store is down waits on the
    reconnect — bounded ONLY by the request timeout (SDK source, ``_await_reconnect``). So the default
    must be FINITE (R5 rejected ``timeout=None``: with infinite reconnect it hangs a call forever) and a
    call during a permanent outage must fail, typed as transport, within it.
    COST: ~``SURREAL_REQUEST_TIMEOUT_SECONDS`` (30 s at the ruled default)."""

    async def test_a_call_while_the_store_stays_down_fails_typed_within_the_default_timeout(
        self, proxied_owner: SurrealLeaseStore, proxy: StoreBounceProxy
    ) -> None:
        default_timeout = _required("SURREAL_REQUEST_TIMEOUT_SECONDS")
        assert (
            isinstance(default_timeout, int | float)
            and math.isfinite(default_timeout)
            and default_timeout > 0
        ), f"the default request timeout must be a finite number of seconds, got {default_timeout!r}"
        await _call(proxied_owner, "RETURN 1")
        await proxy.go_down()

        started = time.monotonic()
        try:
            await asyncio.wait_for(
                _call(proxied_owner, "RETURN 1"), default_timeout + _OUTAGE_FAILURE_SLACK_SECONDS
            )
        except TimeoutError:
            pytest.fail(
                f"a call during an outage was still waiting "
                f"{default_timeout + _OUTAGE_FAILURE_SLACK_SECONDS}s "
                f"later — the store is down and the call is parked on a reconnect with no bound"
            )
        except SurrealConnectionError:
            pass
        else:
            pytest.fail("a call against a store that is DOWN returned a value")
        assert time.monotonic() - started <= default_timeout + _OUTAGE_FAILURE_SLACK_SECONDS


class TestALongOperationOutlivesTheDefaultTimeout:
    """R5 rider (3c). A known-long operation runs under its NAMED override, so it survives a reply
    slower than the default request timeout. The store is made slow WITHOUT a slow statement: the proxy
    holds the store's next reply past the default (``StoreBounceProxy.hold_next_response``), and the
    reply that is held is the first one the startup DDL (``SurrealStore.ensure_ready``) waits for.
    The control shows the same hold DOES time out an ordinary call — so the pin is not passing because
    the hold is shorter than the default, or because nothing was held.
    COST, stated per the rider: the pin ~35 s, the control ~32 s."""

    async def _warm_store(self, env: SurrealEnv) -> SurrealStore:
        store = SurrealStore(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            dim=env.dim,
            user=env.user,
            password=env.password,
        )
        await _call(store, "RETURN 1")
        return store

    async def test_the_startup_ddl_survives_a_reply_slower_than_the_default_timeout(
        self, store_env: SurrealEnv, proxy: StoreBounceProxy
    ) -> None:
        default_timeout = _required("SURREAL_REQUEST_TIMEOUT_SECONDS")
        store = await self._warm_store(dataclasses.replace(store_env, url=proxy.url))
        try:
            proxy.hold_next_response(default_timeout + _HOLD_PAST_DEFAULT_SECONDS)
            try:
                await store.ensure_ready()
            except SurrealConnectionError as error:
                pytest.fail(
                    f"the startup DDL failed when one reply took "
                    f"{default_timeout + _HOLD_PAST_DEFAULT_SECONDS}s "
                    f"(default request timeout {default_timeout}s): it does not run under a longer, named "
                    f"override ({type(error).__name__}: {error})"
                )
            assert proxy.held_total == 1, "premise: the hold delayed one of the DDL's replies"
        finally:
            await store.close()

    async def test_control_the_same_hold_times_out_an_ordinary_call(
        self, store_env: SurrealEnv, proxy: StoreBounceProxy
    ) -> None:
        default_timeout = _required("SURREAL_REQUEST_TIMEOUT_SECONDS")
        store = await self._warm_store(dataclasses.replace(store_env, url=proxy.url))
        try:
            proxy.hold_next_response(default_timeout + _HOLD_PAST_DEFAULT_SECONDS)
            with pytest.raises(SurrealConnectionError):
                await asyncio.wait_for(
                    _call(store, "RETURN 1"), default_timeout + _HOLD_PAST_DEFAULT_SECONDS + 10.0
                )
            assert proxy.held_total == 1, "premise: the hold delayed the ordinary call's reply"
        finally:
            await store.close()


class TestAWriteWhoseOutcomeIsUnknownIsRaisedAsUnknown:
    """R5 rider (2), CONFIRMED by R7's measurement. A write the client sent and never heard back about —
    the socket dropped while it was in flight, or its reply outlived the timeout — may or may not have
    committed. It is raised as ``SurrealOutcomeUnknownError``, never as a plain failure a caller would
    read as "nothing happened" and re-apply. Both driver paths: the single-statement seam and the
    transaction seam."""

    async def _drop_in_flight(
        self, owner: SurrealLeaseStore, proxy: StoreBounceProxy, send: Any
    ) -> list[Any]:
        await _call(owner, "RETURN 1")
        in_flight = [asyncio.create_task(send(index)) for index in range(_IN_FLIGHT_WRITES)]
        await asyncio.sleep(_IN_FLIGHT_SETTLE_SECONDS)
        assert not any(task.done() for task in in_flight), "premise: the writes are in flight at the cut"
        await proxy.go_down()
        await proxy.come_up()
        return await asyncio.wait_for(
            asyncio.gather(*in_flight, return_exceptions=True), _RACING_FAILURE_BOUND_SECONDS
        )

    def _assert_all_unknown(self, outcomes: list[Any], path: str) -> None:
        unknown_type = _required("SurrealOutcomeUnknownError")
        assert issubclass(unknown_type, SurrealConnectionError), (
            "SurrealOutcomeUnknownError must remain a SurrealConnectionError, so every transport handler "
            "in the tree still catches it"
        )
        wrong = [outcome for outcome in outcomes if not isinstance(outcome, unknown_type)]
        assert not wrong, (
            f"{len(wrong)} of {len(outcomes)} {path} writes in flight at a drop were not raised as outcome-"
            f"unknown: {[f'{type(item).__name__}: {item}' for item in wrong]!r} — the commit may have "
            f"happened server-side, so a plain failure invites a double apply"
        )

    async def test_a_single_statement_write_in_flight_at_a_drop(
        self, proxied_owner: SurrealLeaseStore, proxy: StoreBounceProxy
    ) -> None:
        outcomes = await self._drop_in_flight(
            proxied_owner, proxy, lambda index: _call(proxied_owner, _SLOW_WRITE, {"key": f"s{index}"})
        )
        self._assert_all_unknown(outcomes, "single-statement")

    async def test_a_transaction_in_flight_at_a_drop(
        self, proxied_owner: SurrealLeaseStore, proxy: StoreBounceProxy
    ) -> None:
        outcomes = await self._drop_in_flight(
            proxied_owner, proxy, lambda index: _transact(proxied_owner, _SLOW_TXN, {"key": f"t{index}"})
        )
        self._assert_all_unknown(outcomes, "transactional")

    async def test_a_write_whose_reply_outlives_its_timeout(self, direct_owner: SurrealLeaseStore) -> None:
        unknown_type = _required("SurrealOutcomeUnknownError")
        # ``Any``: SDK 2.0's connection classes have no ``timeout`` (this pin is RED at HEAD by design).
        connection: Any = await direct_owner._ensure_connection()
        with connection.timeout(_SHORT_OVERRIDE_SECONDS), pytest.raises(unknown_type):
            await _call(direct_owner, _SLOW_WRITE, {"key": "timed_out"})


class TestATimedOutWriteUnderTheFactoryCommitsNothing:
    """**Fork F11 (packet doc §5) — pins the RECOMMENDED reading; the value is the operator's.** R7: "the
    shared factory sets streaming EXPLICITLY, pinned". Measured by the 4.0 scout on both engines: with
    streaming ON (SDK default) a timed-out request is cancelled by a stream cancel and NOTHING commits;
    with streaming OFF the engine keeps running and COMMITS. This pins the consequence of streaming ON for
    a factory-built connection on the production write path. If the operator rules streaming OFF, invert
    the final assertion (the row then lands, and outcome-unknown is the only honest report).
    Bound, stated: a commit racing the cancel is not constructed (R7); the write sleeps 3 s against a 1 s
    timeout, far from that race."""

    async def test_the_timed_out_write_never_lands(self, direct_owner: SurrealLeaseStore) -> None:
        unknown_type = _required("SurrealOutcomeUnknownError")
        # ``Any``: SDK 2.0's connection classes have no ``timeout`` (this pin is RED at HEAD by design).
        connection: Any = await direct_owner._ensure_connection()
        with connection.timeout(_SHORT_OVERRIDE_SECONDS), pytest.raises(unknown_type):
            await _call(direct_owner, _SLOW_WRITE, {"key": "cancelled"})
        await asyncio.sleep(_AFTER_WRITE_WOULD_HAVE_FINISHED_SECONDS)
        landed = await _call(direct_owner, "SELECT VALUE id FROM probe WHERE n = 1")
        assert landed == [], (
            f"a write whose request timed out COMMITTED anyway ({landed!r}) — the factory's connection is "
            f"not streaming, so the engine finished the statement after the client gave up (R7 measurement)"
        )
