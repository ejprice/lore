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
from pathlib import Path
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
from test_mcp_server import _config, _make_context, _slug, _surreal_test_env  # noqa: F401 - autouse env
from test_retry_seam import _MIN_KNOWN_BOOTSTRAP_OWNERS
from test_sdk3_index_batching import _BIG_FUNCTIONS, _TIER, _big_module_source
from test_sdk3_lifecycle import _close_owner, _construct_live_owner, _owner_classes, _probe_call

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

# Round 4 (MP2): READS in flight at a drop. A read-only transaction that runs long enough to be cut.
_SLOW_READ_TXN = "BEGIN;\nLET $wait = sleep(3s);\nSELECT VALUE id FROM probe;\nCOMMIT;"
_SLOW_READ = "RETURN sleep(3s)"

# Round 4 (MP3): the index-transaction leg holds the reply to the first request at least this large — a
# B1-sized file's one index transaction carries megabytes (one vector per chunk); every other request on
# the store's connection is far smaller.
_LARGE_REQUEST_BYTES = 256 * 1024

# The floor on owners whose startup DDL the hold OBSERVED (a broken hold or derivation would observe none).
_MIN_DDL_OWNERS_OBSERVED = 12

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
        except SurrealConnectionError as error:
            # Round 4 (R8 F14, MP2 sibling): the call waited, queued on the reconnect, and timed out — the
            # seam cannot tell a request that was never sent from one whose reply never came, so it is
            # outcome-unknown, like every other SDK transport failure on a request.
            unknown_type = _required("SurrealOutcomeUnknownError")
            assert isinstance(error, unknown_type), (
                f"a call that timed out waiting on a reconnect was raised as {type(error).__name__}, not "
                f"SurrealOutcomeUnknownError — F14: every SDK transport failure on a request is outcome-"
                f"unknown (the seam cannot tell queued from sent)"
            )
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


class TestAReadWhoseOutcomeIsUnknownIsRaisedAsUnknown:
    """Round 4 — MP2 (operator ruling R8 F14): EVERY SDK transport failure on a request maps to
    ``SurrealOutcomeUnknownError``, because the seam cannot tell a read from a write (nor a request that
    was sent from one queued on a reconnect). A build that raises outcome-unknown only for statements that
    LOOK like writes (a verb sniff) misses ``LET``-prefixed writes, ``RETURN (UPSERT …)`` and function
    calls, and reports them as "nothing happened". The single-statement read in flight at a drop is pinned
    in ``test_sdk3_lifecycle`` (L3, strengthened to the subclass); these are its siblings — the transaction
    path, and the timeout leg. COST: ~5 s and ~1 s."""

    async def test_a_read_only_transaction_in_flight_at_a_drop(
        self, proxied_owner: SurrealLeaseStore, proxy: StoreBounceProxy
    ) -> None:
        outcomes = await TestAWriteWhoseOutcomeIsUnknownIsRaisedAsUnknown()._drop_in_flight(
            proxied_owner, proxy, lambda index: _transact(proxied_owner, _SLOW_READ_TXN, {"key": f"r{index}"})
        )
        unknown_type = _required("SurrealOutcomeUnknownError")
        wrong = [outcome for outcome in outcomes if not isinstance(outcome, unknown_type)]
        assert not wrong, (
            f"{len(wrong)} of {len(outcomes)} read-only transactions in flight at a drop were not raised as "
            f"outcome-unknown: {[f'{type(item).__name__}: {item}' for item in wrong]!r} — the seam cannot "
            f"tell a read from a write (F14), so any narrower mapping is a statement sniff"
        )

    async def test_a_read_whose_reply_outlives_its_timeout(self, direct_owner: SurrealLeaseStore) -> None:
        unknown_type = _required("SurrealOutcomeUnknownError")
        # ``Any``: SDK 2.0's connection classes have no ``timeout`` (this pin is RED at HEAD by design).
        connection: Any = await direct_owner._ensure_connection()
        with connection.timeout(_SHORT_OVERRIDE_SECONDS), pytest.raises(unknown_type):
            await _call(direct_owner, _SLOW_READ)


def _ddl_owner_classes() -> list[tuple[str, type]]:
    """Every connection owner with a startup DDL (``ensure_ready``) — DERIVED from the AST-derived owner
    set (``test_sdk3_lifecycle._owner_classes``), never hand-listed."""
    return [(name, cls) for name, cls in _owner_classes() if callable(getattr(cls, "ensure_ready", None))]


class TestEveryNamedLongOperationOutlivesTheDefaultTimeout:
    """Round 4 — MP3 (operator ruling R5 F4b): EVERY known-long operation runs under its NAMED override —
    "startup DDL / ``ensure_ready``, ``REBUILD INDEX``, large index transactions". Round 3 pinned one owner
    (CF2, ``SurrealStore.ensure_ready``); the adversary's held-reply probe showed ``PrincipalStore.
    ensure_ready`` and an index ``apply`` timing out at the default on a build that passed CF2.

    * The startup DDL is quantified over the DERIVED set of owners that have ``ensure_ready``: one test,
      every owner on its own database and its own proxy, CONCURRENTLY (one held reply per owner, so the
      wall cost is one hold, not one per owner). The reach is a checked variable: an owner added to the
      package joins the set at collection, and each owner's leg asserts the hold was OBSERVED on its own
      traffic — an owner whose ensure_ready sends nothing, or whose reply was never the held one, is RED,
      never silently skipped. A floor guards the derivation itself.
    * The large index transaction: a B1-sized file (``test_sdk3_index_batching``'s fixture, > the retired
      5,000-statement cap in rows) indexed through the served indexer with the reply to its ONE large
      request held past the default.
    * ``REBUILD INDEX``: no site exists in the package (``rebuild_embeddings`` is the REMOVE/DEFINE dance,
      drop row C#26) — stated bound; the builder pins it if C#26 adopts ``REBUILD INDEX``.
    COST, stated: ~40 s wall each (the hold is the default + 2 s), the two tests parallel under ``-n``."""

    async def _one_owner_survives(
        self, name: str, owner_class: type, hold_seconds: float
    ) -> tuple[str, str | None]:
        """``(outcome, problem)``: outcome ``"held"`` (its startup traffic's first reply was held and it
        survived) or ``"connect-only"`` (its ensure_ready sent NOTHING after the warm call: no DDL of its own,
        so nothing to override; measured: DiffEngine, SnapshotStamper); problem is the failure text."""
        env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        setup_connection = await connect_admin(env)
        await setup_connection.close()
        bounce_proxy = StoreBounceProxy(upstream_url=env.url)
        await bounce_proxy.start()
        owner = _construct_live_owner(owner_class, dataclasses.replace(env, url=bounce_proxy.url))
        try:
            await _probe_call(owner, bounce_proxy.url)
            sent_before = bounce_proxy.to_store_bytes
            bounce_proxy.hold_next_response(hold_seconds)
            try:
                await owner.ensure_ready()
            except Exception as error:  # noqa: BLE001 - the failure IS the finding
                return "failed", (
                    f"{name}: ensure_ready failed under a {hold_seconds}s reply: "
                    f"{type(error).__name__}: {error}"
                )
            if bounce_proxy.to_store_bytes == sent_before:
                return "connect-only", None
            if bounce_proxy.held_total != 1:
                return "failed", f"{name}: it sent startup traffic, but the hold was never observed on it"
            return "held", None
        finally:
            try:
                await _close_owner(owner)
            finally:
                await bounce_proxy.close()
                await drop_database(env)

    async def test_every_owners_startup_ddl_survives_a_reply_slower_than_the_default_timeout(self) -> None:
        default_timeout = _required("SURREAL_REQUEST_TIMEOUT_SECONDS")
        owners = _ddl_owner_classes()
        assert len(owners) >= _MIN_KNOWN_BOOTSTRAP_OWNERS, (
            f"the derived set of owners with a startup DDL holds only {len(owners)} classes "
            f"({[name for name, _ in owners]}) — the derivation is broken, and this pin would pass vacuously"
        )
        hold = default_timeout + _HOLD_PAST_DEFAULT_SECONDS
        results = await asyncio.gather(*(self._one_owner_survives(name, cls, hold) for name, cls in owners))
        problems = [problem for _outcome, problem in results if problem is not None]
        held = [
            name for (name, _cls), (outcome, _p) in zip(owners, results, strict=True) if outcome == "held"
        ]
        assert len(held) >= _MIN_DDL_OWNERS_OBSERVED, (
            f"only {len(held)} owners' startup DDL was observed under the hold ({held}): the instrument or "
            f"the derivation is broken (measured 2026-11-07 at the round-4 reference: 15 of 17; the 2 "
            f"connect-only "
            f"owners send no DDL of their own)"
        )
        assert not problems, (
            f"{len(problems)} of {len(owners)} owners' startup DDL did not outlive one reply held {hold}s "
            f"(default request timeout {default_timeout}s) — R5 F4b: ensure_ready runs under a NAMED "
            f"override:\n  " + "\n  ".join(problems)
        )

    async def test_a_large_index_transaction_survives_a_reply_slower_than_the_default_timeout(
        self, tmp_path: Path, store_env: SurrealEnv, proxy: StoreBounceProxy
    ) -> None:
        default_timeout = _required("SURREAL_REQUEST_TIMEOUT_SECONDS")
        live_root = tmp_path / "live"
        (live_root / "pkg").mkdir(parents=True)
        config = _config(_slug(), live_root)
        config = config.model_copy(update={"surreal": config.surreal.model_copy(update={"url": proxy.url})})
        context = await _make_context(config=config, tmp_path=tmp_path)
        try:
            path = "pkg/big_module.py"
            source = _big_module_source(_BIG_FUNCTIONS, marker=False)
            (live_root / path).write_text(source, encoding="utf-8")
            proxy.hold_reply_to_large_request(
                min_bytes=_LARGE_REQUEST_BYTES, seconds=default_timeout + _HOLD_PAST_DEFAULT_SECONDS
            )
            outcome = await context.indexer.index_file(_TIER, path, source)
            assert proxy.held_total == 1, (
                "premise: the reply to the file's large index request was held (no request reached "
                f"{_LARGE_REQUEST_BYTES} bytes, or none was sent)"
            )
            assert outcome.state == "indexed", (
                f"a large index transaction whose reply took {default_timeout + _HOLD_PAST_DEFAULT_SECONDS}s "
                f"(default {default_timeout}s) ended {outcome.state!r} — R5 F4b: a large index transaction "
                f"runs under a NAMED override, so a slow store does not drop a file from the index"
            )
        finally:
            await context.aclose()
