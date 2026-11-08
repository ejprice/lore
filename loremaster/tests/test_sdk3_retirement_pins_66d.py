"""Packet 66 (SDK3) — REQ-D retirement pins for drop-list rows #8, #9, #15 and the teardown-kill bound.

Operator ruling R1's rider (packet doc ``docs/plans/v2/sdk3-python-sdk-3-migration.md`` §3.2): a
retired workaround ships with a pin that is GREEN on the SDK-3 build and goes RED under a DECLARED
mutation that re-introduces the retired workaround or its symptom. The mutations are run through
``scripts/mutation_proof.py``; their anchors and expected-RED sets live in the REQ-D report, not here.

* **D1 — drop list #9** (commit ``480ae72``): ``websockets.exceptions.WebSocketException`` left
  ``_txn._CONNECTION_ERRORS`` (and so its alias ``_SDK_AWAIT_BOUNDARY_ERRORS``). A raw
  ``websockets.exceptions.ConnectionClosedError`` raised from an SDK await now PROPAGATES as itself —
  it is not classified as transport, not dropped-and-wrapped as ``SurrealConnectionError``, and not
  swallowed by best-effort teardown. Reach: the ONE failure ladder's two drivers (``run_query`` — every
  seam's single statement — and ``execute_transaction`` → ``_txn_query_raw``) plus both best-effort
  LIVE kills (``CommandSubscriber._safe_kill``, ``InboxAwaiter._safe_kill``). Each leg carries a
  positive control: the SAME fake raising the SDK's own typed ``ConnectionUnavailableError`` is still
  classified (wrapped / swallowed), so a leg cannot pass because the fake never reached the ladder.
* **D2 — drop list #15** (commit ``ead3356``): ``_SDK_PARSE_FAILURES`` dropped ``AttributeError``
  because SDK 3.0.0's ``parse_rpc_error`` answers a non-dict ``cause`` with a typed ``InternalError``.
  A per-statement ``ERR`` entry whose ``cause`` is a string is TYPED by ``_parse_failed_statement``
  (and by its consumer ``_failed_statements``), carries the string as its ``__cause__``, and logs no
  ``store.transaction.untypeable_err_entry``.
* **D3 — the teardown-kill bound** (commit ``480ae72``, ``TEARDOWN_KILL_TIMEOUT_SECONDS``): on SDK 3.0 a
  ``kill()`` on a dropped socket PARKS on the factory's reconnect until the request timeout. Both
  ``_safe_kill`` sites, and the ``await`` verb that tears its LIVE down through one of them, return
  within the bound. Two worlds: a deterministic fake whose ``kill()`` parks FOREVER (the parking shape,
  strictly harder than the SDK's 30 s park), and the REAL SDK 3.0 connection through the store-bounce
  proxy with the store down (the shape ``build66/probes/probe_teardown_kill.py`` measured: 2.00 s
  bounded vs 30.00 s unbounded). Every leg bounds its OWN wait, so a regression fails with a message
  instead of hanging the run.
* **D4 — drop list #8** (commit ``ead3356``): the six ``_to_aware_utc`` coercers were deleted; the
  corrupt-row guard that survives is ``_txn.required_datetime`` / ``stored_datetime`` (check, never
  coerce). A required datetime column holding a non-datetime is REFUSED with a ``SurrealStoreError``
  naming the row and the column — over the validators directly, and over a REAL dirty row (a legacy
  string stamp that a later ``DEFINE FIELD OVERWRITE … TYPE datetime`` does not re-validate, measured
  by ``build66/reqD/probes/probe_d4_corrupt_row.py``) served by two ledgers with different stamping
  idioms (``task.created_at`` ledger-stamped, ``finding.created_at`` ``DEFAULT time::now()``).
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, NoReturn

import pytest
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
from loremaster.findings import FindingLedger
from loremaster.inbox_awaiter import InboxAwaiter
from loremaster.messages import MessageDrainResult, MessageLedger
from loremaster.scout import CommandSubscriber, _open_command_connection
from loremaster.store._txn import (
    TEARDOWN_KILL_TIMEOUT_SECONDS,
    SurrealConnectionError,
    SurrealOutcomeUnknownError,
    SurrealStoreError,
    _failed_statements,
    _parse_failed_statement,
    bootstrap_session,
    execute_transaction,
    open_surreal_connection,
    required_datetime,
    run_query,
    signin_credentials,
    stored_datetime,
)
from loremaster.tasks import TaskLedger
from sdk3_shape_fakes import SdkRequestTimeoutMixin
from surrealdb import RecordID
from surrealdb.errors import ConnectionUnavailableError, InternalError, QueryError
from websockets.exceptions import ConnectionClosedError

logger = logging.getLogger(__name__)

_URL = "ws://fake.invalid/rpc"
_LIVE_ID = "live-66d"

# D3: slack above the kill bound for scheduling, cancellation and ``close()`` (the bounded leg measured
# 2.00 s against a 2.0 s bound; the unbounded control measured 30.00 s, so slack below ~25 s discriminates).
_BOUND_SLACK_SECONDS = 1.5
# D3: a kill that PARKED waited at least this fraction of the bound (a premise check: a leg whose kill
# answered at once would pass bounded or not, so it would prove nothing).
_PARKED_FRACTION = 0.9
# D3 live legs: how long the SDK is left reconnecting before the kill (the probe's 3 s), the await verb's
# shortened budget and poll tick (a tick must fall inside the budget so the store goes down mid-wait).
_RECONNECTING_SETTLE_SECONDS = 3.0
_LIVE_AWAIT_BUDGET_SECONDS = 4.0
_LIVE_AWAIT_POLL_SECONDS = 0.5
_FAKE_AWAIT_BUDGET_SECONDS = 0.3
_FAKE_AWAIT_POLL_SECONDS = 0.1

# D2: the per-statement ERR entry SDK 2.0 could not type (its parse_rpc_error called ``raw.get`` on a str).
_STRING_CAUSE_TEXT = "a bare string cause"
_STRING_CAUSE_ENTRY: dict[str, Any] = {
    "status": "ERR",
    "kind": "Query",
    "result": "statement rejected",
    "cause": _STRING_CAUSE_TEXT,
}
_UNTYPEABLE_EVENT = "store.transaction.untypeable_err_entry"

# D4: the dirty value a legacy row carries — the exact ISO text the deleted coercers would have parsed.
_LEGACY_STAMP_TEXT = "2026-11-08T00:00:00Z"


def _raw_websockets_drop() -> ConnectionClosedError:
    """The raw ``websockets`` error SDK 2.0 leaked from a dead socket (``no close frame received``)."""
    return ConnectionClosedError(None, None)


def _typed_sdk_drop() -> ConnectionUnavailableError:
    """The SDK 3.0 typed transport error for the same event (packet doc §3 P1) — the positive control."""
    return ConnectionUnavailableError("connection unavailable (66d control)")


def _empty_peek() -> MessageDrainResult:
    """An authoritative drain that finds nothing — the await verb runs its whole budget."""
    return MessageDrainResult(entries=[], total_pending=0, directive_pending=0, stamped_seqs=[], peeked=True)


class _RaisingConnection(SdkRequestTimeoutMixin):
    """A connection whose every SDK await raises ``error`` — the one place a test injects an SDK failure."""

    def __init__(self, error: BaseException) -> None:
        self._error = error
        self.calls: list[str] = []

    async def query(self, statement: str, params: Any = None) -> NoReturn:
        self.calls.append("query")
        raise self._error

    async def query_raw(self, statement: str, params: Any = None) -> NoReturn:
        self.calls.append("query_raw")
        raise self._error

    def check_response_for_error(self, response: Any, method: str) -> None:
        self.calls.append("check_response_for_error")

    async def kill(self, live_uuid: Any) -> NoReturn:
        self.calls.append("kill")
        raise self._error


class _ParkingLiveConnection(SdkRequestTimeoutMixin):
    """SDK 3.0's parking shape on a dropped socket: ``kill()`` never answers (the SDK waits on its reconnect
    until the 30 s request timeout; this fake waits FOREVER — strictly harder). ``query`` hands back a LIVE
    id, the subscription yields nothing, ``close`` returns at once."""

    def __init__(self) -> None:
        self.kill_started = asyncio.Event()
        self.closed = False

    async def query(self, statement: str, params: Any = None) -> list[Any]:
        return [_LIVE_ID]

    async def subscribe_live(self, live_uuid: Any) -> AsyncIterator[dict[str, Any]]:
        async def _never() -> AsyncIterator[dict[str, Any]]:
            await asyncio.Event().wait()
            yield {}

        return _never()

    async def kill(self, live_uuid: Any) -> None:
        self.kill_started.set()
        await self.park_like_the_sdk()  # forever with no budget; the SDK's typed timeout inside one

    async def close(self) -> None:
        self.closed = True


class _DropRecorder:
    """The owner's self-heal seam: records every connection the ladder dropped."""

    def __init__(self) -> None:
        self.dropped: list[Any] = []

    async def __call__(self, connection: Any) -> None:
        self.dropped.append(connection)


def _acquire_of(connection: Any) -> Callable[[], Awaitable[Any]]:
    async def acquire() -> Any:
        return connection

    return acquire


async def _single_statement(connection: Any, drop: _DropRecorder) -> Any:
    return await run_query(
        acquire=_acquire_of(connection),
        drop=drop,
        url=_URL,
        noun="66d probe",
        label="sdk3.66d.probe",
        statement="RETURN 1",
        logger=logger,
    )


async def _transaction(connection: Any, drop: _DropRecorder) -> None:
    await execute_transaction(
        "BEGIN; CREATE t:a; COMMIT;",
        {},
        acquire=_acquire_of(connection),
        drop=drop,
        url=_URL,
    )


def _awaiter(
    connect: Callable[[], Awaitable[Any]],
    drain: Callable[..., Awaitable[MessageDrainResult]],
    *,
    budget_s: float,
    poll_interval_s: float,
) -> InboxAwaiter:
    return InboxAwaiter(connect=connect, drain=drain, budget_s=budget_s, poll_interval_s=poll_interval_s)


async def _no_traffic(**_kwargs: Any) -> MessageDrainResult:
    return _empty_peek()


async def _awaiter_safe_kill(connection: Any, live_uuid: Any) -> None:
    await _awaiter(
        _acquire_of(connection),
        _no_traffic,
        budget_s=_FAKE_AWAIT_BUDGET_SECONDS,
        poll_interval_s=_FAKE_AWAIT_POLL_SECONDS,
    )._safe_kill(connection, live_uuid)


#: Both best-effort LIVE kills, by the name a failure message prints.
_SAFE_KILLS: dict[str, Callable[[Any, Any], Awaitable[None]]] = {
    "CommandSubscriber._safe_kill": CommandSubscriber._safe_kill,
    "InboxAwaiter._safe_kill": _awaiter_safe_kill,
}


async def _elapsed_within(awaitable: Awaitable[Any], *, ceiling: float, what: str) -> float:
    """Await ``awaitable`` under ``ceiling`` seconds; a breach FAILS (never hangs) and names ``what``."""
    started = time.monotonic()
    try:
        await asyncio.wait_for(awaitable, ceiling)
    except TimeoutError:
        pytest.fail(
            f"{what} did not return within {ceiling:.1f}s — the teardown kill is no longer bounded by "
            f"TEARDOWN_KILL_TIMEOUT_SECONDS={TEARDOWN_KILL_TIMEOUT_SECONDS}s (SDK 3.0 parks a kill on a "
            f"dropped socket until its 30 s request timeout)"
        )
    return time.monotonic() - started


# ======================================================================================================
# D1 — drop list #9: a raw websockets error is no longer transport.
# ======================================================================================================


class TestARawWebsocketsErrorPropagatesThroughTheFailureLadder:
    """``_CONNECTION_ERRORS`` no longer holds ``WebSocketException``: through BOTH drivers of the one
    failure ladder a raw ``ConnectionClosedError`` escapes AS ITSELF — the handle is not dropped and the
    error is not wrapped as ``SurrealConnectionError`` (which is what re-adding the arm would do)."""

    @pytest.mark.parametrize(
        "driver", [_single_statement, _transaction], ids=["run_query", "execute_transaction"]
    )
    async def test_a_raw_connection_closed_error_escapes_unclassified(self, driver: Any) -> None:
        connection = _RaisingConnection(_raw_websockets_drop())
        drop = _DropRecorder()
        with pytest.raises(ConnectionClosedError) as raised:
            await driver(connection, drop)
        assert type(raised.value) is ConnectionClosedError, f"wrapped as {type(raised.value).__name__}"
        assert not isinstance(raised.value, SurrealStoreError)
        assert drop.dropped == [], (
            "a raw websockets error was classified as transport (the handle was dropped)"
        )
        assert connection.calls, "the fake never reached the SDK await — the leg proves nothing"

    @pytest.mark.parametrize(
        "driver", [_single_statement, _transaction], ids=["run_query", "execute_transaction"]
    )
    async def test_control_the_sdks_typed_drop_is_still_transport(self, driver: Any) -> None:
        connection = _RaisingConnection(_typed_sdk_drop())
        drop = _DropRecorder()
        with pytest.raises(SurrealOutcomeUnknownError) as raised:
            await driver(connection, drop)
        assert isinstance(raised.value, SurrealConnectionError)
        assert isinstance(raised.value.__cause__, ConnectionUnavailableError)
        assert drop.dropped == [connection]


class TestARawWebsocketsErrorIsNotSwallowedByTheBestEffortKill:
    """The await-boundary alias ``_SDK_AWAIT_BOUNDARY_ERRORS`` shares the retirement: a best-effort LIVE
    kill swallows the SDK's own transport errors but no longer a raw ``websockets`` one."""

    @pytest.mark.parametrize("site", sorted(_SAFE_KILLS))
    async def test_a_raw_connection_closed_error_from_kill_propagates(self, site: str) -> None:
        connection = _RaisingConnection(_raw_websockets_drop())
        with pytest.raises(ConnectionClosedError):
            await _SAFE_KILLS[site](connection, _LIVE_ID)
        assert connection.calls == ["kill"]

    @pytest.mark.parametrize("site", sorted(_SAFE_KILLS))
    async def test_control_the_sdks_typed_drop_from_kill_is_swallowed(self, site: str) -> None:
        connection = _RaisingConnection(_typed_sdk_drop())
        await _SAFE_KILLS[site](connection, _LIVE_ID)
        assert connection.calls == ["kill"]


# ======================================================================================================
# D2 — drop list #15: a non-dict cause is typed by the SDK, never "untypeable".
# ======================================================================================================


class TestAStringCauseIsTypedBySdk3:
    """SDK 3.0.0's ``parse_rpc_error`` answers a non-dict ``cause`` with a typed ``InternalError`` (SDK 2.0
    raised ``AttributeError``, which ``_SDK_PARSE_FAILURES`` used to catch). The ONE parse types the entry
    and keeps the string as its cause; nothing is logged as untypeable."""

    def test_the_one_parse_returns_the_sdks_typed_error(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.DEBUG)
        typed = _parse_failed_statement(0, dict(_STRING_CAUSE_ENTRY))
        assert isinstance(typed, QueryError), f"untyped: {typed!r}"
        assert str(typed) == _STRING_CAUSE_ENTRY["result"]
        assert isinstance(typed.__cause__, InternalError)
        assert _STRING_CAUSE_TEXT in str(typed.__cause__)
        assert [r for r in caplog.records if r.getMessage() == _UNTYPEABLE_EVENT] == []

    def test_the_rollback_reader_carries_the_typed_entry(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.DEBUG)
        ok_entry = {"status": "OK", "result": []}
        failed = _failed_statements({"result": [ok_entry, dict(_STRING_CAUSE_ENTRY)]})
        assert [entry.index for entry in failed] == [1]
        assert isinstance(failed[0].typed, QueryError)
        assert [r for r in caplog.records if r.getMessage() == _UNTYPEABLE_EVENT] == []

    def test_control_an_unhashable_kind_is_still_untypeable_and_logged(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.DEBUG)
        typed = _parse_failed_statement(3, {"status": "ERR", "kind": ["Query"], "result": "x"})
        assert typed is None
        assert [r.getMessage() for r in caplog.records].count(_UNTYPEABLE_EVENT) == 1


# ======================================================================================================
# D3 — the teardown-kill bound.
# ======================================================================================================


class TestTheBestEffortKillIsBoundedWhenKillParks:
    """Deterministic world: ``kill()`` parks forever. Both ``_safe_kill`` sites return within the bound."""

    @pytest.mark.parametrize("site", sorted(_SAFE_KILLS))
    async def test_a_parked_kill_returns_within_the_bound(self, site: str) -> None:
        connection = _ParkingLiveConnection()
        elapsed = await _elapsed_within(
            _SAFE_KILLS[site](connection, _LIVE_ID),
            ceiling=TEARDOWN_KILL_TIMEOUT_SECONDS + _BOUND_SLACK_SECONDS,
            what=site,
        )
        assert connection.kill_started.is_set(), "the kill was never issued — the leg proves nothing"
        assert elapsed >= TEARDOWN_KILL_TIMEOUT_SECONDS * _PARKED_FRACTION, (
            f"returned in {elapsed:.2f}s without waiting the bound"
        )


class TestTheAwaitVerbNeverOverrunsItsBudgetByMoreThanTheKillBound:
    """The SERVED half (deterministic world): ``await_inbox`` with no traffic runs its budget, then tears
    its LIVE down; the parked kill costs at most the bound, and the connection is still closed."""

    async def test_await_inbox_returns_within_budget_plus_bound(self) -> None:
        connection = _ParkingLiveConnection()
        awaiter = _awaiter(
            _acquire_of(connection),
            _no_traffic,
            budget_s=_FAKE_AWAIT_BUDGET_SECONDS,
            poll_interval_s=_FAKE_AWAIT_POLL_SECONDS,
        )
        elapsed = await _elapsed_within(
            awaiter.await_inbox(agent_id="agent-66d", limit=10),
            ceiling=_FAKE_AWAIT_BUDGET_SECONDS + TEARDOWN_KILL_TIMEOUT_SECONDS + _BOUND_SLACK_SECONDS,
            what="InboxAwaiter.await_inbox",
        )
        assert elapsed >= _FAKE_AWAIT_BUDGET_SECONDS, f"returned in {elapsed:.2f}s, before its budget"
        assert connection.kill_started.is_set(), "the LIVE was never torn down — the leg proves nothing"
        assert connection.closed, "teardown did not reach close() after the bounded kill"


@pytest_asyncio.fixture()
async def store_env() -> AsyncIterator[SurrealEnv]:
    """A fresh database on the TEST store (``ws://127.0.0.1:18000``), dropped after."""
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    try:
        yield env
    finally:
        await drop_database(env)


@pytest_asyncio.fixture()
async def proxy(store_env: SurrealEnv) -> AsyncIterator[StoreBounceProxy]:
    """The store-bounce proxy in front of the TEST store."""
    bounce_proxy = StoreBounceProxy(upstream_url=store_env.url)
    await bounce_proxy.start()
    try:
        yield bounce_proxy
    finally:
        await bounce_proxy.close()


async def _factory_connection(env: SurrealEnv, url: str) -> Any:
    """A connection opened by the production factory (its reconnect policy is what parks the kill)."""
    connection = open_surreal_connection(url)
    await connection.signin(signin_credentials(user=env.user, password=env.password))
    await bootstrap_session(connection, env.namespace, env.database, url=url)
    return connection


class TestTheBestEffortKillIsBoundedOnTheRealSdk:
    """Real world: a LIVE on a factory connection through the proxy; the store goes down and the SDK is left
    reconnecting; each ``_safe_kill`` returns within the bound (the unbounded kill measured 30 s)."""

    @pytest.mark.parametrize("site", sorted(_SAFE_KILLS))
    async def test_a_kill_with_the_store_down_returns_within_the_bound(
        self, site: str, store_env: SurrealEnv, proxy: StoreBounceProxy
    ) -> None:
        connection = await _factory_connection(store_env, proxy.url)
        try:
            await connection.query("DEFINE TABLE IF NOT EXISTS t66d SCHEMALESS")
            live_uuid = (await connection.query("LIVE SELECT * FROM t66d"))[0]
            await proxy.go_down()
            await asyncio.sleep(_RECONNECTING_SETTLE_SECONDS)
            elapsed = await _elapsed_within(
                _SAFE_KILLS[site](connection, live_uuid),
                ceiling=TEARDOWN_KILL_TIMEOUT_SECONDS + _BOUND_SLACK_SECONDS,
                what=f"{site} (real SDK, store down)",
            )
            assert elapsed >= TEARDOWN_KILL_TIMEOUT_SECONDS * _PARKED_FRACTION, (
                f"PREMISE: the SDK answered the kill in {elapsed:.2f}s instead of parking on its reconnect — "
                f"this leg no longer exercises the bound (if SDK fails fast now, re-measure and re-rule it)"
            )
        finally:
            await proxy.come_up()
            try:
                await asyncio.wait_for(
                    connection.close(), TEARDOWN_KILL_TIMEOUT_SECONDS + _BOUND_SLACK_SECONDS
                )
            except Exception:  # noqa: BLE001 - best-effort cleanup of a socket the test severed
                logger.debug("sdk3.66d.close_failed")


class TestTheAwaitVerbOnTheRealSdkWithTheStoreDown:
    """The SERVED half, real world, wired as ``server`` wires it: the LIVE rides scout's shared opener
    (``_open_command_connection``) through the proxy, the authoritative re-drain is the real
    ``MessageLedger.drain`` on its own (unproxied) connection. The LIVE socket's store goes down at the first
    poll tick (the LIVE is established by then — the real message schema declares ``to``; without it the LIVE
    never establishes, no kill is issued, and the leg would prove nothing: measured by
    ``build66/reqD/probes/probe_d3_await_kill.py``) and stays down; the verb still returns within its budget
    plus the kill bound."""

    async def test_await_inbox_returns_within_budget_plus_bound(
        self, store_env: SurrealEnv, proxy: StoreBounceProxy
    ) -> None:
        ledger = MessageLedger(**_ledger_kwargs(store_env))
        await ledger.ensure_ready()
        drains = 0
        kills: list[Any] = []

        async def drain(**kwargs: Any) -> MessageDrainResult:
            nonlocal drains
            drains += 1
            if drains == 2:
                await proxy.go_down()
            return await ledger.drain(**kwargs)

        async def connect() -> Any:
            connection = await _open_command_connection(
                url=proxy.url,
                namespace=store_env.namespace,
                database=store_env.database,
                user=store_env.user,
                password=store_env.password,
            )
            real_kill = connection.kill

            async def recorded_kill(live_uuid: Any) -> Any:
                kills.append(live_uuid)
                return await real_kill(live_uuid)

            connection.kill = recorded_kill
            return connection

        awaiter = _awaiter(
            connect, drain, budget_s=_LIVE_AWAIT_BUDGET_SECONDS, poll_interval_s=_LIVE_AWAIT_POLL_SECONDS
        )
        try:
            elapsed = await _elapsed_within(
                awaiter.await_inbox(agent_id="agent-66d", limit=10),
                ceiling=_LIVE_AWAIT_BUDGET_SECONDS + TEARDOWN_KILL_TIMEOUT_SECONDS + _BOUND_SLACK_SECONDS,
                what="InboxAwaiter.await_inbox (real SDK, store down)",
            )
            assert drains >= 2, "the store never went down mid-wait — the leg proves nothing"
            assert len(kills) == 1, (
                "the LIVE was never established, so no kill was issued — the leg proves nothing"
            )
            assert elapsed >= _LIVE_AWAIT_BUDGET_SECONDS + TEARDOWN_KILL_TIMEOUT_SECONDS * _PARKED_FRACTION, (
                f"PREMISE: returned in {elapsed:.2f}s — the teardown kill did not park on the SDK's "
                f"reconnect, so this leg no longer exercises the bound (re-measure and re-rule it)"
            )
        finally:
            await proxy.come_up()
            await ledger.close()


# ======================================================================================================
# D4 — drop list #8: a non-datetime in a required datetime column is refused, never coerced.
# ======================================================================================================


# The values the deleted coercers would have ACCEPTED (an ISO string parsed; a naive datetime made UTC) and
# the ones they refused or nulled — every one is now a refusal naming row and column — each with what the
# refusal must say the column HELD (R34: the type's name, or "a naive datetime").
_NOT_A_TZ_AWARE_DATETIME: dict[str, tuple[object, str]] = {
    "iso-string": (_LEGACY_STAMP_TEXT, "str"),
    "naive-datetime": (datetime(2026, 11, 8, 0, 0, 0), "a naive datetime"),  # noqa: DTZ001 - the corrupt value
    "unparseable-string": ("not a date", "str"),
    "integer": (1_762_560_000, "int"),
    "missing": (None, "NoneType"),
}

# D4 (R34): the row the refusal names. A DIGIT-LED key, so the SDK's ``str(RecordID)`` brackets it
# (``widget:⟨66d…⟩``) while the R7 (d) parts form does not — a build rendering ``str(row_id)`` is RED here.
_D4_TABLE = "widget66d"
_D4_ROW_ID = RecordID(_D4_TABLE, "66dwidget")
_D4_ROW_TEXT = "widget66d:66dwidget"


def _d4_refusal(*, row_text: str, column: str, held: str) -> str:
    """The ONE served refusal text (R34 / sidecar RULING-11 rider 3), spelled out here as the spec."""
    return (
        f"{_D4_TABLE} {row_text} is unreadable: column {column!r} holds {held}, a tz-aware datetime was "
        f"required — a store-integrity fault (report it with lore_findings); other rows are unaffected"
    )


class TestARequiredDatetimeColumnIsCheckedNeverCoerced:
    """The surviving guard over its whole input set: a tz-aware datetime passes through as the SAME object;
    anything else is a ``SurrealStoreError`` whose text is the R34 served refusal — table, the row's id in
    its parts form, the column, what it held, and the store-integrity advice — pinned EXACTLY, once, here."""

    @pytest.mark.parametrize("label", sorted(_NOT_A_TZ_AWARE_DATETIME))
    def test_a_non_datetime_is_refused_naming_row_and_column(self, label: str) -> None:
        value, held = _NOT_A_TZ_AWARE_DATETIME[label]
        with pytest.raises(SurrealStoreError) as raised:
            required_datetime(value, table=_D4_TABLE, row_id=_D4_ROW_ID, column="stamped_at66d")
        assert str(raised.value) == _d4_refusal(row_text=_D4_ROW_TEXT, column="stamped_at66d", held=held)

    @pytest.mark.parametrize("label", sorted(k for k in _NOT_A_TZ_AWARE_DATETIME if k != "missing"))
    def test_an_optional_column_refuses_the_same_values(self, label: str) -> None:
        value, held = _NOT_A_TZ_AWARE_DATETIME[label]
        with pytest.raises(SurrealStoreError) as raised:
            stored_datetime(value, table=_D4_TABLE, row_id=_D4_ROW_ID, column="expires_at66d")
        assert str(raised.value) == _d4_refusal(row_text=_D4_ROW_TEXT, column="expires_at66d", held=held)

    def test_a_row_with_no_id_is_still_refused_and_says_so(self) -> None:
        with pytest.raises(SurrealStoreError) as raised:
            required_datetime(_LEGACY_STAMP_TEXT, table=_D4_TABLE, row_id=None, column="stamped_at66d")
        assert str(raised.value) == _d4_refusal(row_text="(id unknown)", column="stamped_at66d", held="str")

    def test_control_an_aware_datetime_is_returned_unchanged_and_an_unset_option_is_none(self) -> None:
        aware = datetime(2026, 11, 8, 12, 0, 0, tzinfo=UTC)
        assert required_datetime(aware, table=_D4_TABLE, row_id=_D4_ROW_ID, column="stamped_at66d") is aware
        assert stored_datetime(aware, table=_D4_TABLE, row_id=_D4_ROW_ID, column="expires_at66d") is aware
        assert stored_datetime(None, table=_D4_TABLE, row_id=_D4_ROW_ID, column="expires_at66d") is None


async def _corrupt_created_at(env: SurrealEnv, table: str) -> None:
    """Give every ``table`` row a legacy STRING ``created_at``, then restore the column's declared type: the
    engine does not re-validate existing rows on ``DEFINE FIELD OVERWRITE`` (probed on 3.3.5), so the row
    stays dirty under the current schema — the state a long-lived store can hold and a virgin DB cannot."""
    admin = await connect_admin(env)
    try:
        await admin.query(f"DEFINE FIELD OVERWRITE created_at ON {table} TYPE any")
        await admin.query(
            f"UPDATE {table} SET created_at = $stamp RETURN NONE", {"stamp": _LEGACY_STAMP_TEXT}
        )
        await admin.query(f"DEFINE FIELD OVERWRITE created_at ON {table} TYPE datetime")
        raw = await admin.query(f"SELECT VALUE created_at FROM {table}")
        assert raw == [[_LEGACY_STAMP_TEXT]], f"the dirty row was not written: {raw!r}"
    finally:
        await admin.close()


def _ledger_kwargs(env: SurrealEnv) -> dict[str, Any]:
    return {
        "url": env.url,
        "namespace": env.namespace,
        "database": env.database,
        "user": env.user,
        "password": env.password,
    }


class TestADirtyRowIsRefusedWhereItIsServed:
    """A real legacy row read back through a ledger: refused naming the row and the column, never served
    with a coerced stamp. Each leg reads the healthy row first (the control), then corrupts it."""

    async def test_a_task_with_a_string_created_at_is_refused(self, store_env: SurrealEnv) -> None:
        ledger = TaskLedger(**_ledger_kwargs(store_env))
        await ledger.ensure_ready()
        try:
            task_id = await ledger.create_task(subject="s66d", description="d66d", created_by="reqd-pins-66")
            assert isinstance((await ledger.get_task(task_id)).created_at, datetime)
            await _corrupt_created_at(store_env, "task")
            with pytest.raises(SurrealStoreError) as raised:
                await ledger.get_task(task_id)
            assert "task" in str(raised.value)
            assert "created_at" in str(raised.value)
        finally:
            await ledger.close()

    async def test_a_finding_with_a_string_created_at_is_refused(self, store_env: SurrealEnv) -> None:
        ledger = FindingLedger(**_ledger_kwargs(store_env))
        await ledger.ensure_ready()
        try:
            filed = await ledger.report(
                "s66d", "b66d", area="sdk3", category="retirement_pin", created_by="reqd-pins-66"
            )
            assert isinstance((await ledger.get(filed.number)).created_at, datetime)
            await _corrupt_created_at(store_env, "finding")
            with pytest.raises(SurrealStoreError) as raised:
                await ledger.get(filed.number)
            assert "finding" in str(raised.value)
            assert "created_at" in str(raised.value)
        finally:
            await ledger.close()
