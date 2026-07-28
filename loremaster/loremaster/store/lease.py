"""Leader election on the SurrealDB store (packet 11-i-a).

The names and signatures were FROZEN by the contract author (`contract-11ia-1`)
and are the interface packets 11-i-b and 11-ii cite; the bodies were built by
`builder-11ia-1` against that contract.

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

import asyncio
import json
import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any

from kubernetes.leaderelection import electionconfig
from kubernetes.leaderelection.leaderelectionrecord import LeaderElectionRecord
from pydantic import SecretStr
from surrealdb import AsyncSurreal

from loremaster.store._txn import (
    _CONNECTION_ERRORS,
    SurrealConnectionError,
    SurrealStoreError,
    TxnContentionExhaustedError,
    _SurrealConnection,
    bootstrap_session,
    execute_transaction,
    run_query,
    signin_credentials,
)
from loremaster.store.surreal_schema import (
    LEASE_FENCE_EPOCH_COLUMN,
    LEASE_HOLDER_IDENTITY_COLUMN,
    LEASE_REVISION_COLUMN,
    LEASE_SINGLETON_ID,
    LEASE_TABLE,
    generate_lease_ddl,
)

logger = logging.getLogger(__name__)

# This seam's OWN canonical rejection event and raised-message noun. FROZEN by
# ruling O2 — ``test_retry_seam.py`` compares the observed values against two
# hand-written dicts as EXACT SETS, so a different spelling reddens node ids no
# production change can fix.
_QUERY_LABEL = "lease.query.rejected"
_QUERY_NOUN = "lease query"

# The lease row's address, bound (never interpolated) at every call site.
_ROW_PARAM = "lease_row_id"
_HOLDER_PARAM = "lease_holder"
_DURATION_PARAM = "lease_duration"
_ACQUIRE_PARAM = "lease_acquire_time"
_RENEW_PARAM = "lease_renew_time"
_OBSERVED_REVISION_PARAM = "lease_observed_revision"
_FENCE_EPOCH_PARAM = "lease_fence_epoch"

# The columns one read of the lease row projects — EXPLICIT, never ``SELECT *``:
# store reference §2 records that ``SELECT *`` OMITS a ``NONE``-valued column
# entirely (so a released holder would raise ``KeyError``), while an explicit
# projection reads a missing column as ``None``, which is exactly the shape
# :class:`LeaseObservation` declares.
_OBSERVATION_COLUMNS: tuple[str, ...] = (
    LEASE_HOLDER_IDENTITY_COLUMN,
    "lease_duration",
    "acquire_time",
    "renew_time",
    LEASE_REVISION_COLUMN,
    LEASE_FENCE_EPOCH_COLUMN,
)

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

# What a SYNCHRONOUS lock call absorbs and reports as "this tick did not win".
# ONE tuple, not four clones: error classification is POLICY, and four hand-written
# copies of it are four places a future class can be added to three of.
#
# ⚠ ``asyncio.run_coroutine_threadsafe(...).result(timeout=)`` raises
# ``concurrent.futures.TimeoutError``, which **IS** the builtin ``TimeoutError`` — the
# same class object, not a subclass — since Python 3.11 (verified on this interpreter;
# this project's floor is ``requires-python = ">=3.14"``). Naming both, as all four
# sites did, reads as two distinct fates and is one. (Cold audit 11-i-a R10.)
_LOCK_CALL_ERRORS = (SurrealStoreError, TimeoutError)

# The lock's k8s-shaped coordinates. Our store has no namespaces in the k8s
# sense; the algorithm passes these straight back to the lock, so they are
# identity labels, not addressing.
LEASE_LOCK_NAME = "lore-maintenance"
LEASE_LOCK_NAMESPACE = "lore"


class LeaseError(SurrealStoreError):
    """Base for the lease adapter's typed failures.

    ⚠ **NOTHING RAISES THIS AS OF PACKET 11-i-a (2026-07-26), AND THAT IS A
    DELIBERATE KNOWN BOUND, NOT AN OVERSIGHT** (lead ruling on ``builder-11ia-1``'s
    escalation E-5, ``docs/plans/v2/receipts/2026-07-26-packet11i-build/``).
    :class:`SurrealLeaseStore` raises the shared ``_txn`` types directly
    (:class:`~loremaster.store._txn.SurrealConnectionError`,
    :class:`~loremaster.store._txn.TxnContentionExhaustedError`,
    :class:`~loremaster.store._txn.SurrealStoreError`) and
    :class:`SurrealLeaderLock` reports failure through the library's boolean /
    :class:`LockAbsent` channel, so no code path constructs this class today.

    It is kept because it is a member of the contract's FROZEN interface and
    because packet **11-ii**'s election thread is its intended raiser: that loop
    runs outside any caller's stack, so it needs a lease-specific type for a lease
    failure that belongs to no request.

    **NAMED RE-OPEN TRIGGER — if 11-ii ships without raising ``LeaseError``,
    DELETE it.** An unpinned known limitation is indistinguishable from an unknown
    one; worse, an unraised base class reads as a supported error contract, and a
    consumer that CATCHES this type would catch nothing while believing it had
    covered the lease.

    ⚠ **AND THE TRIGGER IS NOW MEASURED** —
    ``test_store_lease.TestLeaseErrorIsAKnownBoundNotAnAccident`` asserts, from the
    AST of this package, that nothing raises it and that it stays a
    ``SurrealStoreError`` subclass. Before that pin this class had ZERO test
    references of any kind: a frozen-interface member that could be DELETED with
    every gate green, carrying a re-open trigger nothing measured — "a trigger
    nobody measures is a hope" (cold audit 11-i-a F6c). The pin goes RED the day
    11-ii raises it, which is the day this docstring must be rewritten.

    (This paragraph deliberately does NOT spell the two-token catch clause: a bare,
    anchor-free grep for that clause is how this repo sweeps for real handler sites,
    and prose containing it makes the sweep return a hit in the very file whose
    receipt is "no such site exists anywhere" — cold audit 11-i-a R13, the
    retired-name-sweep trap pointed the other way.)
    """


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


def _as_rows(result: Any) -> list[dict[str, Any]]:
    """Narrow a statement result to its list of dict rows.

    The guarded ``CREATE`` returns ``None`` when its guard elides the write, and
    a CAS whose ``WHERE`` fails returns ``[]``; both are DEFINED empty results
    with a meaning (a lost race), never errors, so they collapse to ``[]`` here.
    """
    if not isinstance(result, list):
        return []
    return [row for row in result if isinstance(row, dict)]


def _optional_text(value: Any) -> str | None:
    """Coerce one projected record field to ``str | None`` (never ``"None"``)."""
    return None if value is None else str(value)


def _observation(row: dict[str, Any]) -> LeaseObservation:
    """Build a :class:`LeaseObservation` from one projected lease row.

    The two counters are read as ``int`` with a 0 floor rather than defensively
    defaulted to ``None``: the schema declares both ``int DEFAULT 0``, and a
    reader that tolerated a missing ``fence_epoch`` would silently turn every
    fenced commit UNGUARDED instead of loud.
    """
    return LeaseObservation(
        holder_identity=_optional_text(row.get(LEASE_HOLDER_IDENTITY_COLUMN)),
        lease_duration=_optional_text(row.get("lease_duration")),
        acquire_time=_optional_text(row.get("acquire_time")),
        renew_time=_optional_text(row.get("renew_time")),
        revision=int(row.get(LEASE_REVISION_COLUMN) or 0),
        fence_epoch=int(row.get(LEASE_FENCE_EPOCH_COLUMN) or 0),
    )


class SurrealLeaseStore:
    """The conventional ``_query``-owning seam under the lock.

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

        ⚠ IT OPENS NOTHING: ``test_retry_seam.py`` CONSTRUCTS every discovered
        ``_query``-owning seam, and a constructor that dialed (or raised) would
        redden that shared pin for a reason unrelated to this store. The socket is
        opened lazily, under a double-checked lock, by :meth:`_ensure_connection`.
        """
        self._url = url
        self._namespace = namespace
        self._database = database
        self._user = user
        self._password = password
        self._connection: _SurrealConnection | None = None
        # Guards the connect-time check-then-set so N concurrent first-callers
        # never each open their own socket (the double-checked lock every
        # connection owner in this package holds — pinned by
        # ``TestEveryConnectionOwnerOpensExactlyOneSocket``).
        self._connect_lock = asyncio.Lock()

    async def _ensure_connection(self) -> _SurrealConnection:
        """Return the live connection, opening + signing in on first use.

        The session bootstrap is :func:`~loremaster.store._txn.bootstrap_session`
        — the ONE shared implementation every connection owner calls. This
        method's own job is DISPOSITION (the F4 ruling): any bootstrap failure,
        transport fault OR exhausted contention alike, is wrapped as
        :class:`SurrealConnectionError` after the half-open socket is closed,
        because the connection never became usable whatever the reason.

        Raises:
            SurrealConnectionError: The server is unreachable, rejected auth, or
                the session bootstrap exhausted its retry budget.
        """
        if self._connection is not None:
            return self._connection
        async with self._connect_lock:
            if self._connection is not None:
                # A concurrent caller connected while this one waited; mypy cannot
                # model the cross-coroutine mutation across the ``await`` above.
                return self._connection  # type: ignore[unreachable]
            connection = AsyncSurreal(self._url)
            credentials = signin_credentials(user=self._user, password=self._password)
            try:
                await connection.signin(credentials)
                await bootstrap_session(connection, self._namespace, self._database, url=self._url)
            except TxnContentionExhaustedError as error:
                await self._safe_close(connection)
                raise SurrealConnectionError(
                    f"could not connect to SurrealDB at {self._url!r} "
                    f"(namespace={self._namespace!r}, database={self._database!r}): "
                    f"the session bootstrap exhausted its retry budget"
                ) from error
            except _CONNECTION_ERRORS as error:
                await self._safe_close(connection)
                raise SurrealConnectionError(
                    f"could not connect to SurrealDB at {self._url!r} "
                    f"(namespace={self._namespace!r}, database={self._database!r}): {error}"
                ) from error
            self._connection = connection
            logger.debug(
                "lease.connected",
                extra={"namespace": self._namespace, "database": self._database},
            )
            return connection

    async def _drop_connection(self, connection: _SurrealConnection) -> None:
        """Drop the cached handle so the NEXT call reconnects (the self-heal).

        A compare-and-swap: the cached handle is cleared only while ``connection``
        is STILL the cached one, so a late caller holding a stale reference can
        never wipe out a freshly-reconnected socket.
        """
        if self._connection is connection:
            self._connection = None
        await self._safe_close(connection)

    @staticmethod
    async def _safe_close(connection: _SurrealConnection) -> None:
        """Close ``connection``, swallowing an already-dead-socket failure."""
        try:
            await connection.close()
        except _CONNECTION_ERRORS:
            logger.debug("lease.close.already_closed")

    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        """Run a single statement on the (lazily opened) connection, self-healing.

        Delegates to :func:`~loremaster.store._txn.run_query` — the ONE shared
        attempt body: classify, signal, self-heal, log. No private retry, no
        private backoff, no private classification.

        ⚠ FROZEN VALUES (lead ruling O2): ``label="lease.query.rejected"`` and
        ``noun="lease query"``. ``test_retry_seam.py`` compares observed events
        and nouns against two hand-written dicts as exact sets.
        """
        return await run_query(
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
            noun=_QUERY_NOUN,
            label=_QUERY_LABEL,
            statement=statement,
            params=params or {},
            logger=logger,
        )

    async def close(self) -> None:
        """Close the live connection (if any); tolerant of never-connected."""
        if self._connection is not None:
            await self._safe_close(self._connection)
            self._connection = None

    async def ensure_ready(self) -> None:
        """Apply the lease schema slice — idempotent and safe to re-run.

        The multi-statement DDL rides
        :func:`~loremaster.store._txn.execute_transaction`, which verifies EVERY
        statement's status; the SDK's plain ``query()`` validates statement[0]
        only, which is how a silent partial schema apply happens (store
        reference §3).
        """
        await self._ensure_connection()
        ddl = generate_lease_ddl()
        await execute_transaction(
            f"BEGIN;\n{ddl}COMMIT;\n",
            {},
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )
        logger.debug("lease.schema.ready", extra={"database": self._database})

    async def read(self) -> LeaseObservation | None:
        """Read the lease row; ``None`` when it does not exist yet."""
        rows = _as_rows(
            await self._query(
                f"SELECT {', '.join(_OBSERVATION_COLUMNS)} FROM "
                f"type::record('{LEASE_TABLE}', ${_ROW_PARAM})",
                {_ROW_PARAM: LEASE_SINGLETON_ID},
            )
        )
        return _observation(rows[0]) if rows else None

    async def create_if_absent(
        self,
        *,
        holder_identity: str,
        lease_duration: str,
        acquire_time: str,
        renew_time: str,
    ) -> LeaseObservation | None:
        """Create the lease row iff it does not exist.

        Returns:
            The new observation, or ``None`` when the row already existed —
            a LOST RACE with a defined meaning, which is NEVER retried (the
            ``scout.CommandSubscriber._mark`` defined-empty-result discipline).

        Raises:
            SurrealStoreError: ANY other rejection. ⚠ Only a DUPLICATE-id
                rejection is a lost race. A build that reports every failure as
                one passed the whole contract at 143/0 (adversary W26) — and a
                run that silently "never leads" because its table is missing is
                indistinguishable from a run that legitimately lost.

        ⚠ **HOW "ONLY A DUPLICATE IS A LOST RACE" IS BUILT WITHOUT READING AN
        ENGINE MESSAGE** (F8-C6 bars matching engine text, and #118 is the
        receipt: a classifier greps for "assert" while the engine says "must
        conform to"). A bare ``CREATE`` on an existing row RAISES, which would
        force exactly that forbidden text match to tell a duplicate from a real
        rejection. So the existence test is a GUARD INSIDE the statement — ONE
        statement, therefore one implicit transaction, therefore atomic: an
        already-present row yields an EMPTY result (a value, never an error),
        while any genuine rejection of the CREATE still raises. A concurrent
        first-writer either loses the guard (empty) or collides retryably, and
        the ONE shared driver retries it (probed 2026-07-26 on the 3.2.1 test
        store: the guarded CREATE returns the row when absent and ``None`` when
        present).
        """
        rows = _as_rows(
            await self._query(
                f"IF array::len((SELECT VALUE id FROM "
                f"type::record('{LEASE_TABLE}', ${_ROW_PARAM}))) = 0 "
                f"{{ CREATE type::record('{LEASE_TABLE}', ${_ROW_PARAM}) CONTENT {{ "
                f"{LEASE_HOLDER_IDENTITY_COLUMN}: ${_HOLDER_PARAM}, "
                f"lease_duration: ${_DURATION_PARAM}, "
                f"acquire_time: ${_ACQUIRE_PARAM}, "
                f"renew_time: ${_RENEW_PARAM}, "
                f"{LEASE_REVISION_COLUMN}: 0, {LEASE_FENCE_EPOCH_COLUMN}: 0 }} }}",
                {
                    _ROW_PARAM: LEASE_SINGLETON_ID,
                    _HOLDER_PARAM: holder_identity,
                    _DURATION_PARAM: lease_duration,
                    _ACQUIRE_PARAM: acquire_time,
                    _RENEW_PARAM: renew_time,
                },
            )
        )
        return _observation(rows[0]) if rows else None

    async def compare_and_set(
        self,
        *,
        observed_revision: int,
        holder_identity: str,
        lease_duration: str,
        acquire_time: str,
        renew_time: str,
    ) -> LeaseObservation | None:
        """The CAS: ``WHERE revision = $observed_revision``, in ONE update.

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

        ⚠ **THE FENCE CLAUSE READS THE *STORED* HOLDER, AND THAT IS PROBED, NOT
        ASSUMED.** Every ``SET`` right-hand side evaluates against the row's
        BEFORE state regardless of clause order — probed 2026-07-26 on the 3.2.1
        test store with the ``holder_identity`` assignment placed FIRST: the
        fence still bumped, so the ``IF`` saw the OLD holder. The fence clause is
        nevertheless written first, because a build whose correctness depended on
        the opposite reading would be silently wrong in exactly one direction (a
        fence that never bumps hands a zombie a valid token forever).
        """
        rows = _as_rows(
            await self._query(
                f"UPDATE type::record('{LEASE_TABLE}', ${_ROW_PARAM}) SET "
                f"{LEASE_FENCE_EPOCH_COLUMN} = {LEASE_FENCE_EPOCH_COLUMN} + "
                f"(IF {LEASE_HOLDER_IDENTITY_COLUMN} = ${_HOLDER_PARAM} {{ 0 }} ELSE {{ 1 }}), "
                f"{LEASE_HOLDER_IDENTITY_COLUMN} = ${_HOLDER_PARAM}, "
                f"lease_duration = ${_DURATION_PARAM}, "
                f"acquire_time = ${_ACQUIRE_PARAM}, "
                f"renew_time = ${_RENEW_PARAM}, "
                f"{LEASE_REVISION_COLUMN} = {LEASE_REVISION_COLUMN} + 1 "
                f"WHERE {LEASE_REVISION_COLUMN} = ${_OBSERVED_REVISION_PARAM} RETURN AFTER",
                {
                    _ROW_PARAM: LEASE_SINGLETON_ID,
                    _HOLDER_PARAM: holder_identity,
                    _DURATION_PARAM: lease_duration,
                    _ACQUIRE_PARAM: acquire_time,
                    _RENEW_PARAM: renew_time,
                    _OBSERVED_REVISION_PARAM: observed_revision,
                },
            )
        )
        return _observation(rows[0]) if rows else None

    async def release_if_held(self, *, holder_identity: str, fence_epoch: int) -> bool:
        """Clear the holder iff ``(holder_identity, fence_epoch)`` still match.

        RULED DECISION 23. This port of the algorithm has NO ``release``
        (client-go does), so without it every rolling update waits out a full
        ``lease_duration`` before maintenance resumes anywhere.

        Returns:
            ``True`` when the holder was cleared; ``False`` when it was not
            ours to clear (the row is then left EXACTLY as it was).

        The guard carries the FENCE as well as the identity, which is what makes
        a zombie's ``finally`` harmless: a pod that held the lease, lost it and
        re-acquired under a NEW epoch must not clear the lease it no longer holds
        under the OLD one. ``revision`` advances (every successful write does);
        ``fence_epoch`` does NOT — releasing is not a holder CHANGE, and the next
        acquirer's own CAS is what bumps the fence.
        """
        rows = _as_rows(
            await self._query(
                f"UPDATE type::record('{LEASE_TABLE}', ${_ROW_PARAM}) SET "
                f"{LEASE_HOLDER_IDENTITY_COLUMN} = NONE, "
                f"{LEASE_REVISION_COLUMN} = {LEASE_REVISION_COLUMN} + 1 "
                f"WHERE {LEASE_HOLDER_IDENTITY_COLUMN} = ${_HOLDER_PARAM} "
                f"AND {LEASE_FENCE_EPOCH_COLUMN} = ${_FENCE_EPOCH_PARAM} RETURN AFTER",
                {
                    _ROW_PARAM: LEASE_SINGLETON_ID,
                    _HOLDER_PARAM: holder_identity,
                    _FENCE_EPOCH_PARAM: fence_epoch,
                },
            )
        )
        return bool(rows)


class SurrealLeaderLock:
    """The six-member resource lock the algorithm drives.

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
        the algorithm reads ``lock.identity`` / ``lock.name`` / ``lock.namespace``
        directly on every tick, not through an accessor — which is why they are
        plain attributes rather than properties.

        (This said "they are real even in the stub; the three METHOD members are
        stubbed below" long after the builder implemented ``get`` / ``create`` /
        ``update``. Nothing in this module is stubbed. Cold audit 11-i-a F5.)
        """
        self._store = store
        self._loop = loop
        self._call_timeout_seconds = call_timeout_seconds
        self.identity = identity
        self.name = name
        self.namespace = namespace
        # The optimistic-concurrency token THIS lock observed at its last
        # :meth:`get` — the CAS predicate, never re-read inside :meth:`update`
        # (an adapter that re-reads can never LOSE its CAS, which deletes the
        # token and re-opens the two-leaders window between get and update).
        self._observed_revision: int | None = None
        # The fence epoch of the last SUCCESSFUL WRITE (create, renew or seize).
        self._observed_fence_epoch: int | None = None
        # The cooperative poison (R10.3). The library ships no stop mechanism, so
        # a stopped lock makes its writes FAIL, which is what ends ``renew_loop``.
        self._stopped = False

    def _call(self, coroutine: Coroutine[Any, Any, Any]) -> Any:
        """Run ``coroutine`` on the adapter's loop FROM the calling thread.

        The library drives the lock synchronously from its own thread, while every
        store call here is async — so each one is submitted to the loop that owns
        the store's connection and waited on with the renew deadline as its
        timeout. That is what makes "no serving-path frame ever touches the
        lease" true BY CONSTRUCTION (R10.3): the election owns its own thread and
        its own store instance.
        """
        return asyncio.run_coroutine_threadsafe(coroutine, self._loop).result(
            timeout=self._call_timeout_seconds
        )

    def get(self, name: str, namespace: str) -> tuple[bool, Any]:
        """``(True, LeaderElectionRecord)`` when present; ``(False, LockAbsent)``.

        The record returned on the TRUE branch carries EXACTLY the library's
        four fields and nothing else — see the contract for why an extra
        attribute is a liveness bug rather than a cosmetic one.

        A row that EXISTS but names no holder (decision 23's released lease) is
        still ``(True, record)``: the algorithm's own next branch sees a ``None``
        field and goes straight to ``update_lock``, which is precisely the
        immediate handoff decision 23 exists to buy. Reporting it as ABSENT would
        send the candidate down the create path against a row that is already
        there, and nobody would ever acquire it.

        A store FAILURE is reported as a non-404 ``LockAbsent``, which is the
        library's own "error retrieving resource lock" channel: it logs and
        returns ``False`` for this tick WITHOUT attempting a create, and the
        election's own ``retry_period`` loop tries again. The election thread must
        survive a transient store fault — a raise here would end maintenance for
        the process's lifetime — and the swallow is LOUD in the log, never silent.
        """
        try:
            observation = self._call(self._store.read())
        except _LOCK_CALL_ERRORS as error:
            logger.warning(
                "lease.lock.read_failed",
                extra={"lock_identity": self.identity, "error": str(error)},
            )
            return False, _lock_unavailable(f"the lease row could not be read: {error}")
        if observation is None:
            return False, _lock_absent()
        self._observed_revision = observation.revision
        return True, LeaderElectionRecord(
            observation.holder_identity,
            observation.lease_duration,
            observation.acquire_time,
            observation.renew_time,
        )

    def create(self, name: str, namespace: str, election_record: Any) -> bool:
        """Create-if-absent. ⚠ The algorithm calls this with the KEYWORD
        ``election_record`` — the parameter name is part of the interface."""
        if self._stopped:
            return False
        try:
            observation = self._call(
                self._store.create_if_absent(
                    holder_identity=election_record.holder_identity,
                    lease_duration=election_record.lease_duration,
                    acquire_time=election_record.acquire_time,
                    renew_time=election_record.renew_time,
                )
            )
        except _LOCK_CALL_ERRORS as error:
            logger.warning(
                "lease.lock.create_failed",
                extra={"lock_identity": self.identity, "error": str(error)},
            )
            return False
        return self._record_write(observation)

    def update(self, name: str, namespace: str, updated_record: Any) -> bool:
        """The CAS against the revision observed by the last :meth:`get`.

        ⚠ It must CAS on the revision THIS lock observed at its last
        :meth:`get`, never on a freshly re-read one. An adapter that re-reads
        can never lose its CAS, which deletes the optimistic-concurrency token
        entirely and re-opens the two-leaders window between get and update —
        and it passed the whole contract at 143/0 (adversary W18).

        A lock that has never observed the row has no token to CAS against and so
        cannot write: that is ``False`` (this tick did not win), not an error.
        """
        if self._stopped:
            return False
        observed_revision = self._observed_revision
        if observed_revision is None:
            return False
        try:
            observation = self._call(
                self._store.compare_and_set(
                    observed_revision=observed_revision,
                    holder_identity=updated_record.holder_identity,
                    lease_duration=updated_record.lease_duration,
                    acquire_time=updated_record.acquire_time,
                    renew_time=updated_record.renew_time,
                )
            )
        except _LOCK_CALL_ERRORS as error:
            logger.warning(
                "lease.lock.update_failed",
                extra={"lock_identity": self.identity, "error": str(error)},
            )
            return False
        return self._record_write(observation)

    def _record_write(self, observation: LeaseObservation | None) -> bool:
        """Absorb a write's outcome: remember its counters, report its status.

        ``None`` is the DEFINED empty result — a lost race — and is never retried
        and never diagnosed in line: the algorithm's own next-tick ``get``
        re-observes ground truth. Both counters are refreshed on EVERY successful
        write, not only the first, because the fenced commit reads the epoch on
        every run and a stale one fences against an epoch nobody holds.
        """
        if observation is None:
            return False
        self._observed_revision = observation.revision
        self._observed_fence_epoch = observation.fence_epoch
        return True

    # -- the adapter-owned extras (NOT part of the library's surface) -------

    @property
    def fence_epoch(self) -> int | None:
        """The fence epoch observed at the last successful write, or ``None``.

        Updated after EVERY successful write — the first create, each renewal,
        and a seize — not only the first (adversary residual 7). The engine's
        fenced commit reads this on every run.
        """
        return self._observed_fence_epoch

    def release_if_held(self) -> bool:
        """Ruled decision 23's graceful handoff, from the election thread.

        ⚠ It must ACTUALLY release. A build returning ``False`` unconditionally
        passed the entire contract at 143/0 (adversary W29) while making
        decision 23 a no-op — and the symptom is invisible in tests and costs a
        full ``lease_duration`` of stalled maintenance on every rolling update.

        A lock that never wrote holds no fence, so it has nothing to release and
        reports ``False`` without touching the store.
        """
        fence_epoch = self._observed_fence_epoch
        if fence_epoch is None:
            return False
        try:
            released = self._call(
                self._store.release_if_held(
                    holder_identity=self.identity, fence_epoch=fence_epoch
                )
            )
        except _LOCK_CALL_ERRORS as error:
            logger.warning(
                "lease.lock.release_failed",
                extra={"lock_identity": self.identity, "error": str(error)},
            )
            return False
        return bool(released)

    def stop(self) -> None:
        """The cooperative poison: after this, ``create``/``update`` return
        ``False``, which ends the library's ``renew_loop`` within
        ``renew_deadline`` and fires ``onstopped_leading``. The library ships no
        stop mechanism of its own (R10.3)."""
        self._stopped = True


def _lock_absent() -> LockAbsent:
    """The ``404``-shaped FALSE-``get`` response that licenses a CREATE.

    The algorithm reads ``json.loads(record.body)['code']`` and compares it
    against :data:`~http.HTTPStatus.NOT_FOUND` BEFORE it will try to create the
    lock, so the code inside the body is the load-bearing part — see this
    module's docstring for the measured failure of both obvious alternatives.
    """
    return LockAbsent(
        body=json.dumps({"code": int(HTTPStatus.NOT_FOUND), "message": "lease row absent"}),
        reason="Not Found",
        status=int(HTTPStatus.NOT_FOUND),
    )


def _lock_unavailable(message: str) -> LockAbsent:
    """A NON-404 FALSE-``get`` response: the row's state is UNKNOWN this tick.

    Deliberately not 404: the algorithm treats any other code as "error
    retrieving resource lock", logs it and returns ``False`` WITHOUT creating —
    which is the correct disposition for a store we could not read. Reporting
    404 instead would invite a create against a row that may well exist.
    """
    return LockAbsent(
        body=json.dumps({"code": int(HTTPStatus.SERVICE_UNAVAILABLE), "message": message}),
        reason="Service Unavailable",
        status=int(HTTPStatus.SERVICE_UNAVAILABLE),
    )


def lease_election_config(
    *,
    lock: SurrealLeaderLock,
    on_started_leading: Callable[[], None],
    on_stopped_leading: Callable[[], None],
) -> Any:
    """Build the library ``Config`` at the L2 tunables.

    All three tunables are passed EXPLICITLY: ``Config`` has NO defaults (every
    one is a required positional), so "use the upstream defaults" means naming
    client-go's documented 15/10/2 — and it VALIDATES them by calling
    ``sys.exit``, i.e. an illegal triple raises ``SystemExit`` at construction,
    not ``ValueError``. Both callbacks are passed explicitly too: for a ``None``
    ``onstopped_leading``, ``Config`` silently substitutes its OWN
    ``on_stoppedleading_callback`` — which is not a no-op, it logs
    ``"stopped leading"`` at INFO on the library's ``leaderelection`` logger, and
    does nothing else (read out of the installed ``electionconfig.py``, kubernetes
    36.0.3, 2026-07-26). Operationally that is the same trap either way: a build
    that forgot to wire abdication looks identical, keeps running, and the run
    never LEARNS it lost the lease — only a log line nobody is alerting on says
    so. (Cold audit 11-i-a R10: the substitute was described as a no-op.)

    Returns:
        ``kubernetes.leaderelection.electionconfig.Config`` carrying
        :data:`LEASE_DURATION_SECONDS` / :data:`LEASE_RENEW_DEADLINE_SECONDS` /
        :data:`LEASE_RETRY_PERIOD_SECONDS`, all passed EXPLICITLY.
    """
    return electionconfig.Config(
        lock,
        LEASE_DURATION_SECONDS,
        LEASE_RENEW_DEADLINE_SECONDS,
        LEASE_RETRY_PERIOD_SECONDS,
        on_started_leading,
        on_stopped_leading,
    )
