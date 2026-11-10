"""Packet 58 contract r4 — amendment 12 §2 (R-3): the lease lock's four catch sites, evidence by EFFECT.

*Every claim in this file is scoped to the tree at ``a77dc00`` (branch ``feat/surreal-unification``),
2026-09-29, authored by ``contract-58-r4``.  "RED at HEAD" means RED at that commit.*

Spec: ``docs/design/2026-09-29-packet58-amendment-12.md`` @ ``5419448`` §2.  RULED ``named-isolation-served``:
the election library's interface is a bool per tick (``create`` / ``update`` / ``release_if_held``) or
``(bool, record)`` (``get``); each site logs ``lease.lock.<op>_failed`` at WARNING and serves the library's
own
fail-SAFE value; the library's ``retry_period`` loop tries again next tick.  It is NOT a #102 door — nothing
re-reads inside the handler and nothing retries the seam.  What the trust doctrine requires is that the record
be distinguishable from a genuine lost race IN THE LOG, so the WARNING's ``extra`` gains
``error_class: type(error).__name__`` (the rider — lead scope call: carried by 58's build).

The four ops are the lease module's in-domain catch sites, DERIVED from THE ONE walker
(``_catch_sites.production_catch_sites`` + ``test_exhaustion_fates.in_domain``) — the driver table must cover
exactly that set, both ways.  Per op, with exhausted contention injected at the lock's STORE:

1. the served value is the library's failure value (``False``; ``get``: ``(False, <non-404 LockAbsent>)`` —
the
   algorithm's "error retrieving" channel, so a failed ``get`` never proceeds to ``create`` in that tick);
2. a record ≥ WARNING names the op's failure event, carries the error text AND ``error_class ==
   "TxnContentionExhaustedError"``;
3. the store receives NO further call after the injection (``statements_after == 0``).

RED at HEAD: leg 2's ``error_class`` (the rider is unbuilt); legs 1 and 3 are GREEN (the sites are already
fail-safe and non-retrying).
"""

from __future__ import annotations

import asyncio
import logging
import threading
from collections.abc import Callable, Iterator
from http import HTTPStatus
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest
from _catch_sites import production_catch_sites
from loremaster.store._txn import TxnContentionExhaustedError
from loremaster.store.lease import LockAbsent, SurrealLeaderLock
from test_exhaustion_fates import derived_fate, in_domain

if TYPE_CHECKING:
    # ⚠ DISCHARGED 2026-11-10 (a77f72e): the build landed this symbol; bound packet-58-contract is deleted.
    # ⚠ packet 58's RULED, not-yet-built symbol named STATICALLY (the #461 shape): the ``error_class`` rider
    # is
    # carried by 58's BUILD (lead scope call, am-12 §6), so this file's RED@HEAD legs share the one
    # self-destructing owner ``packet-58-contract``.  Runtime-inert.
    from loremaster.tasks import TaskLedger

    _RULED_58: tuple[object, ...] = (TaskLedger._guarded_append_fragment,)

LEASE_FILE = "store/lease.py"


class _Store:
    """A lease store whose ``failing`` method raises the injected exhaustion; every call is recorded."""

    def __init__(self, failing: str, injected: BaseException) -> None:
        self.failing = failing
        self.injected = injected
        self.calls: list[str] = []
        self.after: list[str] = []

    def __getattr__(self, method: str) -> Callable[..., Any]:
        async def _call(**_kwargs: Any) -> Any:
            if self.calls and self.calls[-1] == self.failing:
                self.after.append(method)
            self.calls.append(method)
            if method == self.failing:
                raise self.injected
            return None

        return _call


_RECORD = SimpleNamespace(holder_identity="r4-lease", lease_duration=15, acquire_time=None, renew_time=None)

#: op (the lock method whose catch site is in the domain) → (the store method it calls, how to invoke it).
LEASE_OPS: dict[str, tuple[str, Callable[[SurrealLeaderLock], Any]]] = {
    "get": ("read", lambda lock: lock.get(lock.name, lock.namespace)),
    "create": (
        "create_if_absent",
        lambda lock: lock.create(lock.name, lock.namespace, election_record=_RECORD),
    ),
    "update": ("compare_and_set", lambda lock: lock.update(lock.name, lock.namespace, _RECORD)),
    "release_if_held": ("release_if_held", lambda lock: lock.release_if_held()),
}


#: op → the WARNING event its handler logs (read verbatim off ``store/lease.py``'s four handlers).
FAILURE_EVENTS = {
    "get": "lease.lock.read_failed",
    "create": "lease.lock.create_failed",
    "update": "lease.lock.update_failed",
    "release_if_held": "lease.lock.release_failed",
}


def derived_lease_ops() -> set[str]:
    """The lease module's in-domain, NON-derived catch sites' FUNCTIONS (the row-due ones — a PASSTHROUGH or
    TRANSLATE site such as ``_ensure_connection`` needs no row) — THE ONE walker's answer, never a list."""
    return {
        site.key.rpartition("::")[2]
        for site in production_catch_sites()
        if site.file == LEASE_FILE and in_domain(site) and derived_fate(site) is None
    }


@pytest.fixture
def lease_loop() -> Iterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    try:
        yield loop
    finally:
        loop.call_soon_threadsafe(loop.stop)
        thread.join(timeout=5)
        loop.close()


class TestTheLeaseDriverTableIsTheDerivedDomain:
    def test_the_driver_table_covers_exactly_the_lease_modules_in_domain_sites(self) -> None:
        assert derived_lease_ops() == set(LEASE_OPS), (sorted(derived_lease_ops()), sorted(LEASE_OPS))


class TestExhaustionAtTheLeaseStoreIsNamedByEffect:
    @pytest.mark.parametrize("op", sorted(LEASE_OPS))
    def test_the_fail_safe_value_is_served_the_WARNING_names_the_class_and_nothing_follows(
        self, op: str, lease_loop: asyncio.AbstractEventLoop, caplog: pytest.LogCaptureFixture
    ) -> None:
        store_method, invoke = LEASE_OPS[op]
        injected = TxnContentionExhaustedError(
            "injected-58r4 lease exhaustion", attempts=64, elapsed_seconds=2.0
        )
        store = _Store(store_method, injected)
        lock = SurrealLeaderLock(store=store, identity="r4-lease", loop=lease_loop, call_timeout_seconds=5.0)  # type: ignore[arg-type]
        lock._observed_fence_epoch = 1  # noqa: SLF001 - a lock that has written (release's precondition)
        lock._observed_revision = 1  # noqa: SLF001 - a lock that has observed (update's CAS token)
        caplog.set_level(logging.DEBUG)
        served = invoke(lock)
        assert store.calls and store.calls[-1] == store_method, (op, store.calls)
        if op == "get":
            ok, response = served
            assert ok is False and isinstance(response, LockAbsent), served
            assert response.status != HTTPStatus.NOT_FOUND, (
                f"a failed get served a 404 — the algorithm would proceed to CREATE this tick: {response}"
            )
        else:
            assert served is False, (
                f"lock.{op} served {served!r} for exhausted contention (the fail-safe is False)"
            )
        assert not store.after, f"lock.{op}: the store received {store.after} AFTER the exhaustion (a retry)"
        loud = [record for record in caplog.records if record.levelno >= logging.WARNING]
        named = [
            record
            for record in loud
            if record.getMessage() == FAILURE_EVENTS[op]
            and getattr(record, "error_class", None) == type(injected).__name__
            and str(injected) in str(getattr(record, "error", ""))
        ]
        assert len(named) == 1, (
            f"lock.{op}: exhausted contention must be distinguishable from a genuine lost race IN THE LOG — "
            "one "
            f"WARNING naming the failure event with `error_class` == {type(injected).__name__!r} and the "
            "error "
            f"(am-12 §2 rider).  Records ≥ WARNING: "
            f"{[(r.getMessage(), getattr(r, 'error_class', None)) for r in loud]}"
        )
