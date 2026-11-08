"""Packet SDK3 contract — CONNECTION LIFECYCLE across a store bounce (finding #576).

Contract index, rationale and expected state at HEAD: ``docs/plans/v2/sdk3-python-sdk-3-migration.md``
§3. This file pins BEHAVIOUR only — what a caller of a connection owner sees — never how the SDK is
spelled or configured. The store is bounced through :class:`_sdk3_proxy.StoreBounceProxy`, never
restarted: the shared TEST store (``:18000``) and production are untouched.

The global lifecycle rule, leg by leg:

* DEGRADATION — the store goes away under a live owner; a call RACING the drop fails LOUD and TYPED
  (:class:`SurrealConnectionError`), never silently, never as a domain rejection, never a hang.
* RECOVERY — once the store is back, the next call succeeds; for an IDLE owner it succeeds on the
  FIRST call (#576: at HEAD every long-lived owner fails exactly one call after any restart).
* STATE LEAKAGE / STALE HANDLES — a dropped or closed connection never comes back to life behind the
  owner's back (no zombie reconnect, no second socket), and every test builds its own proxy, owners
  and database, closing all three.

The owner set is DERIVED (``test_retry_seam._discover_bootstrap_owners``: every class in the package
owning an ``async def _ensure_connection``), never hand-listed, and a control asserts it is not
silently small.
"""

from __future__ import annotations

import asyncio
import dataclasses
import functools
import importlib
import inspect
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

import pytest
import pytest_asyncio
from _sdk3_proxy import SeverMode, StoreBounceProxy
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
)
from loremaster.scout import _open_command_connection
from loremaster.store import _txn
from loremaster.store._txn import SurrealConnectionError, run_query
from loremaster.store.lease import SurrealLeaseStore
from test_retry_seam import (
    _CTOR_VALUES,
    _MIN_KNOWN_BOOTSTRAP_OWNERS,
    _discover_bootstrap_owners,
)

logger = logging.getLogger(__name__)

# How long the store stays down in an ordinary bounce (a container restart measured 0.3-0.5s to
# /health on 3.3.5, research doc §D-4).
_SHORT_OUTAGE_SECONDS = 0.5

# How long an owner sits idle after the store is back before its next call. #576's case is the
# owner that was NOT busy when the store restarted; research §D-4 measured SDK 3.0 succeeding on
# call 1 at 3 s and 8 s idle. 5 s is past the SDK's first reconnect attempt (~2 s) with margin.
_IDLE_AFTER_BOUNCE_SECONDS = 5.0

# The racing-call pins: how many calls are in flight when the store drops (concurrency law: >= 8),
# how long each would run if undisturbed, and the hard bound on how long their failure may take.
_IN_FLIGHT_CALLS = 8
_IN_FLIGHT_STATEMENT = "RETURN sleep(3s)"
_IN_FLIGHT_SETTLE_SECONDS = 0.5
_RACING_FAILURE_BOUND_SECONDS = 20.0

# The long-outage pin (operator ruling R5, F2b): an outage longer than a short bounce, and the bound,
# measured from the moment the store returns, within which every owner's first call must answer: the
# factory's reconnect delay is capped at 2.0 s (+10% SDK jitter = 2.2 s), plus the handshake and session
# replay. "~2 s" in the ruling; 3.0 s here.
# Round 4 (RS2): the outage must OUTLAST a finite attempt budget, or "reconnect forever" is pinned only up
# to the horizon. Factory delays (SDK ``ReconnectOptions.delay``): attempt 1 waits ~1.0 s, every later one
# 1.8-2.0 s (capped at 2.0, jitter 10%), so ``attempts=20`` gives up after 35.2-39.1 s; 45 s kills every
# budget <= 22 attempts (the adversary's surviving ``attempts=20``). BOUND, stated: a finite budget whose
# give-up time exceeds 45 s (>= ~25 attempts) survives — "forever" is unpinnable by any finite outage;
# raising the outage buys ~0.5 attempts per second of run time.
_LONG_OUTAGE_SECONDS = 45.0
_FIRST_CALL_AFTER_LONG_OUTAGE_BOUND_SECONDS = 3.0

# How long the no-zombie pins watch the proxy for a socket nobody should be opening. It covers the
# SDK's first two reconnect attempts (~2 s and ~6 s after a drop).
_ZOMBIE_WATCH_SECONDS = 7.0

# The statement a lifecycle probe call runs: cheap, side-effect free, valid on every database.
_PROBE_STATEMENT = "RETURN 1"
_PROBE_LABEL = "sdk3.lifecycle.probe"


def _owner_classes() -> list[tuple[str, type]]:
    """Every connection-owner class, derived from the package (never a hand-list)."""
    return [
        (class_name, getattr(importlib.import_module(module_path), class_name))
        for module_path, class_name in _discover_bootstrap_owners()
    ]


async def _ignore_command(command: dict[str, Any]) -> None:
    """Scout's command handler, for a subscriber that only ever runs probe calls."""
    del command


# Scout's poll cadence for a subscriber constructed here (its poll loop is never started).
_SUBSCRIBER_POLL_INTERVAL_SECONDS = 60.0


def _construct_live_owner(owner_class: type, env: SurrealEnv) -> Any:
    """Build ``owner_class`` against ``env``, supplying only its REQUIRED parameters.

    ``test_retry_seam._construct_live`` with one more value: scout's ``CommandSubscriber`` takes
    its connection FACTORY (``connect``) rather than a URL, and production hands it the ONE shared
    opener (``scout._open_command_connection``), so that is what it gets here — plus a no-op command
    ``handler`` and a poll cadence, since only its connection lifecycle is exercised.
    """
    values = dict(_CTOR_VALUES)
    values.update(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
        dim=env.dim,
        handler=_ignore_command,
        poll_interval_s=_SUBSCRIBER_POLL_INTERVAL_SECONDS,
        connect=functools.partial(
            _open_command_connection,
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            user=env.user,
            password=env.password,
        ),
    )
    required = [
        name
        for name, parameter in inspect.signature(owner_class).parameters.items()
        if name != "self" and parameter.default is inspect.Parameter.empty
    ]
    return owner_class(**{name: values[name] for name in required})


def _drop_of(owner: Any) -> Callable[[Any], Awaitable[None]]:
    """The owner's self-heal in the driver's ``drop(connection)`` shape.

    Every store owner's ``_drop_connection`` takes the failed connection (a compare-and-swap);
    scout's ``CommandSubscriber._drop_connection`` takes none (it holds exactly one socket).
    """
    if len(inspect.signature(owner._drop_connection).parameters) == 0:

        async def _drop_held(connection: Any) -> None:
            del connection
            await owner._drop_connection()

        return _drop_held
    drop: Callable[[Any], Awaitable[None]] = owner._drop_connection
    return drop


async def _probe_call(owner: Any, url: str, statement: str = _PROBE_STATEMENT) -> Any:
    """One single-statement call through THE production driver, on ``owner``'s own lifecycle.

    ``run_query`` is the seam every owner's ``_query`` delegates to; handing it the owner's own
    ``_ensure_connection`` / ``_drop_connection`` exercises exactly the acquire → classify → drop
    path a production call takes, on the connection the owner itself constructed.
    """
    return await run_query(
        acquire=owner._ensure_connection,
        drop=_drop_of(owner),
        url=url,
        noun="sdk3 lifecycle probe",
        label=_PROBE_LABEL,
        statement=statement,
        logger=logger,
    )


async def _close_owner(owner: Any) -> None:
    """Close an owner through its public ``close`` (every owner but scout's subscriber has one)."""
    close: Callable[[], Awaitable[None]] | None = getattr(owner, "close", None)
    if close is not None:
        await close()
        return
    connection = getattr(owner, "_connection", None)
    if connection is not None:
        await _drop_of(owner)(connection)


async def _settled(predicate: Callable[[], bool], *, timeout: float = 3.0) -> bool:
    """Poll ``predicate`` until it holds or ``timeout`` passes (socket teardown is asynchronous)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        await asyncio.sleep(0.05)
    return predicate()


@pytest_asyncio.fixture()
async def store_env() -> AsyncIterator[SurrealEnv]:
    """A fresh database on the TEST store, created DIRECTLY (not through the proxy)."""
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    try:
        yield env
    finally:
        await drop_database(env)


@pytest_asyncio.fixture()
async def proxy(store_env: SurrealEnv) -> AsyncIterator[StoreBounceProxy]:
    """A started proxy in front of the TEST store; closed (every socket severed) at teardown."""
    bounce_proxy = StoreBounceProxy(upstream_url=store_env.url)
    await bounce_proxy.start()
    try:
        yield bounce_proxy
    finally:
        await bounce_proxy.close()


@pytest.fixture()
def proxied_env(store_env: SurrealEnv, proxy: StoreBounceProxy) -> SurrealEnv:
    """``store_env`` with its URL pointed through the proxy."""
    return dataclasses.replace(store_env, url=proxy.url)


@pytest_asyncio.fixture()
async def every_owner(proxied_env: SurrealEnv) -> AsyncIterator[dict[str, Any]]:
    """One live instance of EVERY connection owner, all reaching the store through the proxy."""
    owners = {name: _construct_live_owner(cls, proxied_env) for name, cls in _owner_classes()}
    try:
        yield owners
    finally:
        for owner in owners.values():
            try:
                await _close_owner(owner)
            except Exception:  # noqa: BLE001 - teardown must close every owner even if one fails
                logger.exception("sdk3.lifecycle.teardown_close_failed")


@pytest_asyncio.fixture()
async def lease_owner(proxied_env: SurrealEnv) -> AsyncIterator[SurrealLeaseStore]:
    """One production owner with the simplest constructor, through the proxy."""
    owner = SurrealLeaseStore(
        url=proxied_env.url,
        namespace=proxied_env.namespace,
        database=proxied_env.database,
        user=proxied_env.user,
        password=proxied_env.password,
    )
    try:
        yield owner
    finally:
        await owner.close()


async def _call_each(owners: dict[str, Any], url: str) -> dict[str, BaseException]:
    """One concurrent probe call per owner; returns ``{owner: exception}`` for every failure."""
    names = list(owners)
    outcomes = await asyncio.gather(
        *(_probe_call(owners[name], url) for name in names), return_exceptions=True
    )
    return {
        name: outcome
        for name, outcome in zip(names, outcomes, strict=True)
        if isinstance(outcome, BaseException)
    }


def _describe(failures: dict[str, BaseException]) -> str:
    return "\n  ".join(f"{name}: {type(error).__name__}: {error}" for name, error in sorted(failures.items()))


class TestTheOwnerSetIsNotSilentlySmall:
    """The control on the reach of every ∀-owner pin below: an empty or shrunken owner list would
    make them vacuously green."""

    def test_the_owner_scan_finds_at_least_the_known_owners(self) -> None:
        owners = _owner_classes()
        assert len(owners) >= _MIN_KNOWN_BOOTSTRAP_OWNERS, (
            f"the derived owner set holds only {len(owners)} classes "
            f"({[name for name, _ in owners]}); test_retry_seam's floor is "
            f"{_MIN_KNOWN_BOOTSTRAP_OWNERS}. Every lifecycle pin in this file quantifies over it."
        )


class TestAnIdleOwnerServesItsFirstCallAfterAStoreBounce:
    """RECOVERY, #576's own case. At HEAD (SDK 2.0) every owner's cached socket is dead after a
    restart and its first call fails; the owner heals only on the call after. The property: an owner
    that was idle while the store bounced serves its next call — the first one — successfully."""

    @pytest.mark.parametrize("mode", [SeverMode.ABORT, SeverMode.CLOSE_FRAME], ids=lambda mode: mode.value)
    async def test_every_owner_answers_its_first_call_after_a_bounce(
        self, every_owner: dict[str, Any], proxy: StoreBounceProxy, mode: SeverMode
    ) -> None:
        warm_failures = await _call_each(every_owner, proxy.url)
        assert not warm_failures, (
            f"premise: every owner must work BEFORE the bounce:\n  {_describe(warm_failures)}"
        )
        assert proxy.live_pipes >= len(every_owner), (
            f"premise: each of the {len(every_owner)} owners must hold a socket THROUGH the proxy "
            f"(saw {proxy.live_pipes}) — otherwise the bounce below cuts nothing it is meant to cut"
        )
        accepted_before = proxy.accepted_total

        severed = await proxy.bounce(down_seconds=_SHORT_OUTAGE_SECONDS, mode=mode)
        assert severed >= len(every_owner), f"premise: the bounce severed only {severed} sockets"
        await asyncio.sleep(_IDLE_AFTER_BOUNCE_SECONDS)

        failures = await _call_each(every_owner, proxy.url)
        assert not failures, (
            f"{len(failures)} of {len(every_owner)} idle owner(s) FAILED their first call after the store "
            f"bounced ({mode.value}) and came back {_IDLE_AFTER_BOUNCE_SECONDS}s ago — finding #576: a "
            f"long-lived connection must not spend a caller's call discovering that the store "
            f"restarted:\n  {_describe(failures)}"
        )
        assert proxy.accepted_total - accepted_before >= len(every_owner), (
            "the recovered calls did not reach the store over NEW sockets — they cannot have been "
            "served by the store at all"
        )

    async def test_an_owner_recovers_from_two_bounces_in_a_row(
        self, lease_owner: SurrealLeaseStore, proxy: StoreBounceProxy
    ) -> None:
        """A reconnect that works once and leaves its machinery spent (an exhausted attempt
        counter, a sticky 'gave up' state) passes the single-bounce pin; this one catches it."""
        await _probe_call(lease_owner, proxy.url)
        for bounce_number in (1, 2):
            await proxy.bounce(down_seconds=_SHORT_OUTAGE_SECONDS)
            await asyncio.sleep(_IDLE_AFTER_BOUNCE_SECONDS)
            try:
                await _probe_call(lease_owner, proxy.url)
            except Exception as error:  # noqa: BLE001 - the failure IS the finding
                pytest.fail(
                    f"the first call after bounce #{bounce_number} failed: {type(error).__name__}: {error}"
                )


class TestACallRacingTheDropFailsLoudAndTyped:
    """DEGRADATION. Calls in flight when the store drops cannot succeed. Each must fail LOUD, with the
    one transport type every caller in the tree handles (``SurrealConnectionError``) — never a
    silent success, never a domain rejection (which would tell a caller the write was ILLEGAL), never
    a raw SDK or ``KeyError``, never a hang."""

    async def test_the_in_flight_calls_succeed_when_nothing_is_cut(
        self, lease_owner: SurrealLeaseStore, proxy: StoreBounceProxy
    ) -> None:
        """Positive control for the pin below: the same calls, undisturbed, all succeed."""
        await _probe_call(lease_owner, proxy.url)
        outcomes = await asyncio.wait_for(
            asyncio.gather(
                *(_probe_call(lease_owner, proxy.url, _IN_FLIGHT_STATEMENT) for _ in range(_IN_FLIGHT_CALLS)),
                return_exceptions=True,
            ),
            _RACING_FAILURE_BOUND_SECONDS,
        )
        errors = [outcome for outcome in outcomes if isinstance(outcome, BaseException)]
        assert not errors, f"control: undisturbed in-flight calls failed: {errors!r}"

    async def test_every_call_in_flight_at_the_drop_raises_SurrealConnectionError(
        self, lease_owner: SurrealLeaseStore, proxy: StoreBounceProxy
    ) -> None:
        await _probe_call(lease_owner, proxy.url)
        in_flight = [
            asyncio.create_task(_probe_call(lease_owner, proxy.url, _IN_FLIGHT_STATEMENT))
            for _ in range(_IN_FLIGHT_CALLS)
        ]
        await asyncio.sleep(_IN_FLIGHT_SETTLE_SECONDS)
        assert not any(task.done() for task in in_flight), (
            "premise: the calls must still be in flight at the cut"
        )

        await proxy.go_down()
        await proxy.come_up()
        done, pending = await asyncio.wait(in_flight, timeout=_RACING_FAILURE_BOUND_SECONDS)
        for task in pending:
            task.cancel()
        assert not pending, (
            f"{len(pending)} of {_IN_FLIGHT_CALLS} calls in flight at the drop were still waiting "
            f"{_RACING_FAILURE_BOUND_SECONDS}s later — a drop must fail a call, not park it"
        )
        outcomes = [task.exception() if task.exception() is not None else task.result() for task in done]
        wrong = [outcome for outcome in outcomes if not isinstance(outcome, SurrealConnectionError)]
        assert not wrong, (
            f"{len(wrong)} of {_IN_FLIGHT_CALLS} calls in flight when the store dropped did NOT raise "
            f"SurrealConnectionError: {[f'{type(item).__name__}: {item}' for item in wrong]!r}. A value "
            f"means a call silently 'succeeded' across a drop; any other type misclassifies a transport "
            f"fault (a domain rejection tells the caller its write was illegal)."
        )
        # Round 4 — MP2 (operator ruling R8 F14): these are READS (``RETURN sleep(3s)``), and the seam cannot
        # tell a read from a write, so a request in flight at a drop is outcome-unknown WHATEVER its text.
        # A build that maps only write-looking statements to outcome-unknown fails here.
        unknown_type = getattr(_txn, "SurrealOutcomeUnknownError", None)
        assert unknown_type is not None, "store._txn.SurrealOutcomeUnknownError does not exist (R5 rider 2)"
        not_unknown = [outcome for outcome in outcomes if not isinstance(outcome, unknown_type)]
        assert not not_unknown, (
            f"{len(not_unknown)} of {_IN_FLIGHT_CALLS} READS in flight at the drop were raised as "
            f"{sorted({type(item).__name__ for item in not_unknown})}, not SurrealOutcomeUnknownError — F14: "
            f"every SDK transport failure on a request is outcome-unknown; a narrower mapping is a statement "
            f"sniff that reports a LET-prefixed or RETURN (UPSERT …) write as 'nothing happened'"
        )

    async def test_after_the_racing_failure_the_next_call_succeeds_and_no_stale_socket_survives(
        self, lease_owner: SurrealLeaseStore, proxy: StoreBounceProxy
    ) -> None:
        """RECOVERY + NO STALE HANDLE after a degradation. The dropped connection must be gone for
        good: one live socket for the one owner, and no second one opened behind its back."""
        await _probe_call(lease_owner, proxy.url)
        in_flight = [
            asyncio.create_task(_probe_call(lease_owner, proxy.url, _IN_FLIGHT_STATEMENT))
            for _ in range(_IN_FLIGHT_CALLS)
        ]
        await asyncio.sleep(_IN_FLIGHT_SETTLE_SECONDS)
        await proxy.go_down()
        await proxy.come_up()
        await asyncio.wait(in_flight, timeout=_RACING_FAILURE_BOUND_SECONDS)
        for task in in_flight:
            if not task.done():
                task.cancel()
            elif not task.cancelled():
                task.exception()  # retrieved: the previous pin owns their type

        try:
            await _probe_call(lease_owner, proxy.url)
        except Exception as error:  # noqa: BLE001 - the failure IS the finding
            pytest.fail(
                f"the first call after a racing drop (store back) failed: {type(error).__name__}: {error}"
            )
        await asyncio.sleep(_ZOMBIE_WATCH_SECONDS)
        assert await _settled(lambda: proxy.live_pipes == 1), (
            f"one owner, one connection: the proxy holds {proxy.live_pipes} live sockets after the "
            f"recovery. A connection the owner dropped is reconnecting on its own (a zombie the owner "
            f"no longer references), or the owner holds two."
        )


class TestAClosedOwnerStaysClosed:
    """STATE LEAKAGE: ``close()`` ends the connection for good. A closed connection that keeps a
    background reconnect alive leaks a socket per owner per store restart, forever."""

    async def test_close_then_bounce_opens_no_new_socket(
        self, lease_owner: SurrealLeaseStore, proxy: StoreBounceProxy
    ) -> None:
        await _probe_call(lease_owner, proxy.url)
        assert proxy.live_pipes == 1, f"premise: one owner, one socket (saw {proxy.live_pipes})"
        await lease_owner.close()
        assert await _settled(lambda: proxy.live_pipes == 0), (
            f"close() left {proxy.live_pipes} socket(s) open"
        )
        accepted_after_close = proxy.accepted_total

        await proxy.bounce(down_seconds=_SHORT_OUTAGE_SECONDS)
        await asyncio.sleep(_ZOMBIE_WATCH_SECONDS)
        assert proxy.accepted_total == accepted_after_close, (
            f"a CLOSED owner's connection opened {proxy.accepted_total - accepted_after_close} new "
            f"socket(s) after the store bounced — close() did not stop it reconnecting"
        )


class TestRecoveryLatencyAfterALongOutage:
    """RECOVERY under a longer outage — operator ruling R5 (F2b): ONE shared connection factory with
    ``ReconnectOptions(attempts=-1, retry_delay=0.5, retry_delay_max=2.0)``, so "a call after the server
    returns answers within ~2 s (L6)". Round 3 quantifies it over EVERY owner (derived, never hand-listed):
    an owner that bypasses the factory keeps the SDK default (5 attempts, backoff to 60 s — after a 15 s
    outage its next attempt is ~15 s away), and one with the factory's delays but a finite attempt count
    gives up before the outage ends and never comes back; both fail this pin (round 4, RS2: the outage is
    45 s, past ``attempts=20``'s ~39 s give-up). The calls are issued the moment the store returns, so the
    bound measures the reconnect cadence itself.
    RED at HEAD (SDK 2.0 never reconnects: the first call fails outright). COST: ~50 s."""

    async def test_every_owner_answers_promptly_once_the_store_returns(
        self, every_owner: dict[str, Any], proxy: StoreBounceProxy
    ) -> None:
        warm_failures = await _call_each(every_owner, proxy.url)
        assert not warm_failures, (
            f"premise: every owner works before the outage:\n  {_describe(warm_failures)}"
        )
        await proxy.go_down()
        await asyncio.sleep(_LONG_OUTAGE_SECONDS)
        await proxy.come_up()
        returned_at = time.monotonic()

        async def _timed(name: str) -> tuple[str, float | BaseException]:
            try:
                await asyncio.wait_for(
                    _probe_call(every_owner[name], proxy.url), _FIRST_CALL_AFTER_LONG_OUTAGE_BOUND_SECONDS
                )
            except BaseException as error:  # noqa: BLE001 - the failure IS the finding
                return name, error
            return name, time.monotonic() - returned_at

        outcomes = dict(await asyncio.gather(*(_timed(name) for name in every_owner)))
        late = {
            name: outcome
            for name, outcome in outcomes.items()
            if isinstance(outcome, BaseException) or outcome > _FIRST_CALL_AFTER_LONG_OUTAGE_BOUND_SECONDS
        }
        assert not late, (
            f"{len(late)} of {len(every_owner)} owners did not answer within "
            f"{_FIRST_CALL_AFTER_LONG_OUTAGE_BOUND_SECONDS}s of the store returning after a "
            f"{_LONG_OUTAGE_SECONDS}s outage (an MCP tool call parked on a reconnect backoff, or an owner "
            f"whose reconnect gave up): "
            + "; ".join(
                f"{name}: {type(o).__name__}: {o}" if isinstance(o, BaseException) else f"{name}: {o:.1f}s"
                for name, o in sorted(late.items())
            )
        )
