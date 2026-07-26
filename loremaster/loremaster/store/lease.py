"""STUB SURFACE (packet 11-i-a) — leader election on the SurrealDB store.

WRITTEN BY THE CONTRACT AUTHOR (`contract-11ia-1`), NOT BY A BUILDER. Every
``NotImplementedError`` is a hole the 11-i-a builder fills; the names and
signatures are the FROZEN interface packet 11-i-b and 11-ii cite.

**THE ALGORITHM IS NOT OURS AND MUST NOT BECOME OURS** (ruled decision 13,
Addendum F-r2 §R10; operator directive P1). ``kubernetes.leaderelection``
ships the election: 183 LOC, ZERO kubernetes-client imports, and an expiry test
that is OBSERVER-RELATIVE — each candidate times ``lease_duration`` on its OWN
clock from when IT last saw the record CHANGE — which is skew-immune without
any clock authority. What is genuinely missing, and therefore hand-rolled here
as a MINIMAL bridge rather than a parallel implementation, is (a) a resource
lock backed by our store and (b) the fencing token the library's four-field
``LeaderElectionRecord`` structurally cannot carry.

⚠ **THE LOCK INTERFACE IS SIX MEMBERS, AND IT IS DERIVED, NEVER HAND-LISTED.**
An AST walk of the installed ``leaderelection.py`` + ``electionconfig.py``
(measured 2026-07-26, kubernetes 36.0.3) shows the algorithm touching exactly
``create · get · identity · name · namespace · update`` on the lock object —
``ConfigMapLock``'s ``get_lock_dict`` / ``get_lock_object`` are its OWN
helpers, which the algorithm never calls. A pin re-derives that set from the
installed source, so a library upgrade that reaches for a seventh member goes
RED instead of silently taking a code path our adapter cannot serve.

⚠ **AND THE FALSE ``get`` RETURN IS NOT ``(False, None)``** — measured
2026-07-26 against kubernetes 36.0.3 with a differently-broken control. The
algorithm's create-if-absent branch does
``json.loads(old_election_record.body)['code'] != HTTPStatus.NOT_FOUND``, so
the second element of a FALSE ``get`` must be an object carrying ``.body``
(a JSON string with a ``code`` key) and ``.reason``. An adapter built to the
design's literal words — "``get(name, namespace) -> (status, record)``" —
raises ``AttributeError: 'NoneType' object has no attribute 'body'`` and the
lock can NEVER be created; a bare ``ApiException(status=404)`` raises
``TypeError`` instead, because that constructor leaves ``.body`` as ``None``.
:class:`LockAbsent` exists for exactly this, and the contract pins all three
legs.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import SecretStr

from loremaster.store._txn import SurrealStoreError

# --- L2: the lease tunables, OPERATOR-CONFIRMED 2026-07-25 -------------------
#
# client-go's documented defaults, passed EXPLICITLY. The library's ``Config``
# has NO defaults at all — every one of the three is a required positional —
# so "use the upstream defaults" means naming these values, never omitting the
# argument. ``Config`` also VALIDATES them (``lease_duration > renew_deadline``
# and ``renew_deadline > jitter_factor * retry_period``, jitter_factor 1.2),
# and rejects by calling ``sys.exit`` — i.e. it raises ``SystemExit``, not a
# ``ValueError``. Re-open trigger (L2): a measured renewal-failure rate under
# real store latency.
LEASE_DURATION_SECONDS = 15
LEASE_RENEW_DEADLINE_SECONDS = 10
LEASE_RETRY_PERIOD_SECONDS = 2

# The lock's k8s-shaped coordinates. Our store has no namespaces in the k8s
# sense; the algorithm passes these straight back to the lock, so they are
# identity labels, not addressing.
LEASE_LOCK_NAME = "lore-maintenance"
LEASE_LOCK_NAMESPACE = "lore"


class LeaseError(SurrealStoreError):
    """Base for the lease adapter's typed failures."""


@dataclass(frozen=True)
class LockAbsent:
    """The ApiException-SHAPED response a FALSE ``get`` must return.

    Not decoration: the algorithm reads ``.body`` as JSON and compares its
    ``code`` against ``HTTPStatus.NOT_FOUND`` before it will try to create the
    lock. See this module's docstring for the measured failure of both obvious
    alternatives.
    """

    body: str
    reason: str
    status: int


@dataclass(frozen=True)
class LeaseObservation:
    """One read of the lease row: the library's four fields plus our two counters.

    ``revision`` is the optimistic-concurrency token (the role k8s
    ``resourceVersion`` plays for ``ConfigMapLock``): bumped on EVERY
    successful write, and the CAS predicate is ``WHERE revision = $observed``.
    ``fence_epoch`` is §R2's fencing token: bumped ONLY when the holder
    changes, so a run's end-of-run commit can be guarded against a lease it no
    longer holds. Both are minted store-side in the SAME update.
    """

    holder_identity: str | None
    lease_duration: str | None
    acquire_time: str | None
    renew_time: str | None
    revision: int
    fence_epoch: int


class SurrealLeaseStore:
    """STUB (packet 11-i-a). The conventional ``_query``-owning seam under the lock.

    Split out from :class:`SurrealLeaderLock` on purpose: the lock's surface is
    SYNCHRONOUS (the library calls it from its own thread), while every store
    call in this package is async and must ride ``_txn.run_query`` /
    ``_txn.execute_transaction``. Keeping the async half in a conventional
    ledger shape is what puts it inside ``test_retry_seam.py``'s automatic seam
    enumeration instead of requiring a hand-added coverage entry.
    """

    def __init__(
        self,
        *,
        url: str,
        namespace: str,
        database: str,
        user: str,
        password: SecretStr,
    ) -> None:
        """Store the wiring. Does not open any connection yet.

        ⚠ REAL EVEN IN THE STUB: ``test_retry_seam.py`` CONSTRUCTS every
        discovered ``_query``-owning seam, and a raising constructor would
        redden that shared pin for a reason unrelated to this contract.
        """
        self._url = url
        self._namespace = namespace
        self._database = database
        self._user = user
        self._password = password
        self._connection: Any | None = None

    async def _ensure_connection(self) -> Any:
        """STUB. The lazily-opened, double-checked-locked connection."""
        raise NotImplementedError("packet 11-i-a: SurrealLeaseStore._ensure_connection")

    async def _drop_connection(self, connection: Any) -> None:
        """STUB. The compare-and-swap self-heal."""
        raise NotImplementedError("packet 11-i-a: SurrealLeaseStore._drop_connection")

    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        """STUB. Delegates to ``store._txn.run_query`` — the ONE shared attempt body."""
        raise NotImplementedError("packet 11-i-a: SurrealLeaseStore._query")

    async def close(self) -> None:
        """STUB. Close the live connection (if any)."""
        raise NotImplementedError("packet 11-i-a: SurrealLeaseStore.close")

    async def ensure_ready(self) -> None:
        """STUB. Apply the lease schema slice — idempotent, re-runnable."""
        raise NotImplementedError("packet 11-i-a: SurrealLeaseStore.ensure_ready")

    async def read(self) -> LeaseObservation | None:
        """STUB. Read the lease row; ``None`` when it does not exist yet."""
        raise NotImplementedError("packet 11-i-a: SurrealLeaseStore.read")

    async def create_if_absent(
        self,
        *,
        holder_identity: str,
        lease_duration: str,
        acquire_time: str,
        renew_time: str,
    ) -> LeaseObservation | None:
        """STUB. Create the lease row iff it does not exist.

        Returns:
            The new observation, or ``None`` when the row already existed —
            a LOST RACE with a defined meaning, which is NEVER retried (the
            ``scout.CommandSubscriber._mark`` defined-empty-result discipline).
        """
        raise NotImplementedError("packet 11-i-a: SurrealLeaseStore.create_if_absent")

    async def compare_and_set(
        self,
        *,
        observed_revision: int,
        holder_identity: str,
        lease_duration: str,
        acquire_time: str,
        renew_time: str,
    ) -> LeaseObservation | None:
        """STUB. The CAS: ``WHERE revision = $observed_revision``, in ONE update.

        Bumps ``revision`` always and ``fence_epoch`` ONLY when
        ``holder_identity`` differs from the stored one — both store-side, in
        the same statement, so no reader can ever observe a half-applied pair.

        Returns:
            The new observation, or ``None`` on an empty result. The empty
            result is FOUR-WAY AMBIGUOUS (lost race / row absent / stale
            observation / a swallowed-statement class) and the adapter makes
            that harmless BY CONSTRUCTION: empty ⇒ status ``False``, never
            retried, never diagnosed in line — the algorithm's own next-tick
            ``get`` re-observes ground truth (R10.2).
        """
        raise NotImplementedError("packet 11-i-a: SurrealLeaseStore.compare_and_set")

    async def release_if_held(self, *, holder_identity: str, fence_epoch: int) -> bool:
        """STUB. Clear the holder iff ``(holder_identity, fence_epoch)`` still match.

        RULED DECISION 23. This port of the algorithm has NO ``release``
        (client-go does), so without it every rolling update waits out a full
        ``lease_duration`` before maintenance resumes anywhere.

        Returns:
            ``True`` when the holder was cleared; ``False`` when it was not
            ours to clear (the row is then left EXACTLY as it was).
        """
        raise NotImplementedError("packet 11-i-a: SurrealLeaseStore.release_if_held")


class SurrealLeaderLock:
    """STUB (packet 11-i-a). The six-member resource lock the algorithm drives.

    Bridges the library's SYNCHRONOUS lock surface onto :class:`SurrealLeaseStore`
    by submitting each coroutine to ``loop`` from the calling thread — the
    election runs in its own thread with its own store connection, which is
    what makes "no serving-path frame ever touches the lease" true BY
    CONSTRUCTION rather than by convention (R10.3).
    """

    def __init__(
        self,
        *,
        store: SurrealLeaseStore,
        identity: str,
        loop: Any,
        name: str = LEASE_LOCK_NAME,
        namespace: str = LEASE_LOCK_NAMESPACE,
        call_timeout_seconds: float = float(LEASE_RENEW_DEADLINE_SECONDS),
    ) -> None:
        """Wire the lock. ``identity`` is this process's per-run uuid4.

        The three ATTRIBUTE members of the six-member interface are set here —
        the algorithm reads ``lock.identity`` / ``lock.name`` /
        ``lock.namespace`` directly on every tick — so they are real even in
        the stub; the three METHOD members are stubbed below.
        """
        self._store = store
        self._loop = loop
        self._call_timeout_seconds = call_timeout_seconds
        self.identity = identity
        self.name = name
        self.namespace = namespace

    def get(self, name: str, namespace: str) -> tuple[bool, Any]:
        """STUB. ``(True, LeaderElectionRecord)`` when present; ``(False, LockAbsent)``.

        The record returned on the TRUE branch carries EXACTLY the library's
        four fields and nothing else — see the contract for why an extra
        attribute is a liveness bug rather than a cosmetic one.
        """
        raise NotImplementedError("packet 11-i-a: SurrealLeaderLock.get")

    def create(self, name: str, namespace: str, election_record: Any) -> bool:
        """STUB. Create-if-absent. ⚠ The algorithm calls this with the KEYWORD
        ``election_record`` — the parameter name is part of the interface."""
        raise NotImplementedError("packet 11-i-a: SurrealLeaderLock.create")

    def update(self, name: str, namespace: str, updated_record: Any) -> bool:
        """STUB. The CAS against the revision observed by the last :meth:`get`."""
        raise NotImplementedError("packet 11-i-a: SurrealLeaderLock.update")

    # -- the adapter-owned extras (NOT part of the library's surface) -------

    @property
    def fence_epoch(self) -> int | None:
        """STUB. The fence epoch observed at the last successful write, or ``None``."""
        raise NotImplementedError("packet 11-i-a: SurrealLeaderLock.fence_epoch")

    def release_if_held(self) -> bool:
        """STUB. Ruled decision 23's graceful handoff, from the election thread."""
        raise NotImplementedError("packet 11-i-a: SurrealLeaderLock.release_if_held")

    def stop(self) -> None:
        """STUB. The cooperative poison: after this, ``create``/``update`` return
        ``False``, which ends the library's ``renew_loop`` within
        ``renew_deadline`` and fires ``onstopped_leading``. The library ships no
        stop mechanism of its own (R10.3)."""
        raise NotImplementedError("packet 11-i-a: SurrealLeaderLock.stop")


def lease_election_config(
    *,
    lock: SurrealLeaderLock,
    on_started_leading: Callable[[], None],
    on_stopped_leading: Callable[[], None],
) -> Any:
    """STUB (packet 11-i-a). Build the library ``Config`` at the L2 tunables.

    Returns:
        ``kubernetes.leaderelection.electionconfig.Config`` carrying
        :data:`LEASE_DURATION_SECONDS` / :data:`LEASE_RENEW_DEADLINE_SECONDS` /
        :data:`LEASE_RETRY_PERIOD_SECONDS`, all passed EXPLICITLY.
    """
    raise NotImplementedError("packet 11-i-a: lease_election_config")
