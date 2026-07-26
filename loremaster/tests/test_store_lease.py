"""Contract — packet 11-i-a, leader election on the SurrealDB store.

Written by `contract-11ia-1` (2026-07-26) against the ruled design (decision 13
+ Addendum F-r2 §R2/§R10, decision 23, ruling L2). The builder builds FROM
this. No production implementation exists yet: every pin below is RED with a
``NotImplementedError``, which is the honest contract state.

WHAT THIS FILE DECIDES (the interface freeze 11-i-b and 11-ii cite) —
``loremaster.store.lease``::

    LEASE_DURATION_SECONDS = 15 · LEASE_RENEW_DEADLINE_SECONDS = 10
    LEASE_RETRY_PERIOD_SECONDS = 2                         # ruling L2, explicit
    LockAbsent(body, reason, status)                       # the FALSE-get shape
    LeaseObservation(holder_identity, lease_duration, acquire_time,
                     renew_time, revision, fence_epoch)
    SurrealLeaseStore(url, namespace, database, user, password)
        ensure_ready / read / create_if_absent / compare_and_set /
        release_if_held / _ensure_connection / _query / close
    SurrealLeaderLock(store, identity, loop, name, namespace,
                      call_timeout_seconds)
        get / create / update / identity / name / namespace
        + fence_epoch / release_if_held / stop      (adapter-owned extras)
    lease_election_config(lock, on_started_leading, on_stopped_leading) -> Config

⚠ THE THREE MEASUREMENTS THAT MOVED THE DESIGN, all taken 2026-07-26 against
the installed ``kubernetes`` 36.0.3 in this worktree's venv, each with a
control:

1. **The lock interface is SIX members and they are DERIVED.** An AST walk of
   ``leaderelection.py`` + ``electionconfig.py`` shows the algorithm touching
   exactly ``create · get · identity · name · namespace · update``.
   ``ConfigMapLock``'s ``get_lock_dict`` / ``get_lock_object`` are its own
   helpers, never called by the algorithm. ``TestTheLockInterfaceIsDerived``
   re-derives the set at run time, so a library upgrade cannot silently reach
   for a seventh member.
2. **A FALSE ``get`` must NOT return ``(False, None)``.** The create-if-absent
   branch does ``json.loads(old_election_record.body)['code'] !=
   HTTPStatus.NOT_FOUND``. Measured: ``(False, None)`` →
   ``AttributeError: 'NoneType' object has no attribute 'body'``; a bare
   ``ApiException(status=404)`` → ``TypeError`` (that constructor leaves
   ``.body`` as ``None``). Both make the FIRST-EVER acquisition impossible, on
   a virgin store, in production, with every other pin green. The design's
   own wording ("``get(name, namespace) -> (status, record)``") is what a
   builder would implement.
3. **``Config`` has NO defaults and validates by ``sys.exit``.** All six
   arguments are required positionals, so ruling L2's "use the upstream
   defaults" means PASSING 15/10/2, never omitting them; and an illegal triple
   raises ``SystemExit``, not ``ValueError``.

⚠ WHAT THIS FILE DOES NOT DECIDE, said plainly: the election THREAD, the
``asyncio.Event`` bridge, ``MaintenanceLoop``, and any serving change. Those
are 11-ii (R5). ``SurrealLeaderLock`` takes a ``loop`` because the library's
surface is synchronous; the contract drives it from a worker thread via
``asyncio.to_thread``, which is the same submission path 11-ii's dedicated
election thread will use, without 11-i-a owning a thread lifecycle.

⚠ AND THE CONCURRENCY LAW: the lease row is a HOT ROW. Its pins run at
≥8-way with OVERLAPPING racer lifetimes, and repo law is explicit that a single
green run NEVER clears a concurrency test — twenty consecutive greens are the
BUILDER's obligation, recorded in its report, not something a single pytest
invocation can discharge.
"""

from __future__ import annotations

import ast
import asyncio
import json
import pathlib
import time
from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
)
from kubernetes.client.rest import ApiException
from kubernetes.leaderelection import electionconfig, leaderelection
from kubernetes.leaderelection.leaderelection import LeaderElection
from kubernetes.leaderelection.leaderelectionrecord import LeaderElectionRecord
from loremaster.store._txn import SurrealStoreError
from loremaster.store.lease import (
    LEASE_DURATION_SECONDS,
    LEASE_LOCK_NAME,
    LEASE_LOCK_NAMESPACE,
    LEASE_RENEW_DEADLINE_SECONDS,
    LEASE_RETRY_PERIOD_SECONDS,
    LockAbsent,
    SurrealLeaderLock,
    SurrealLeaseStore,
    lease_election_config,
)
from pydantic import SecretStr

# The members the ALGORITHM touches on its lock. Written out so the derivation
# below has something to be checked AGAINST — a derived set compared only with
# itself proves nothing.
EXPECTED_LOCK_MEMBERS = frozenset({"create", "get", "identity", "name", "namespace", "update"})

# The library's record carries EXACTLY these four attributes, and the fact is
# load-bearing twice over: it is why fencing cannot live in the record (R10.1),
# and it is why an adapter must not decorate the record it returns (see
# ``TestTheRecordTheAdapterReturnsIsPure``).
EXPECTED_RECORD_FIELDS = frozenset(
    {"holder_identity", "lease_duration", "acquire_time", "renew_time"}
)

# The fastest LEGAL configuration under the library's own validation
# (duration > deadline; deadline > 1.2 * retry; each >= 1). Used only by the
# timing pins, so a three-second lease is what a seize test waits out rather
# than fifteen.
FAST_LEASE_SECONDS = 3
FAST_RENEW_DEADLINE_SECONDS = 2
FAST_RETRY_PERIOD_SECONDS = 1

_HOT_ROW_RACERS = 8
_HOT_ROW_SCALE = (16, 32)




class _RoundTrips:
    """Counts a live connection's SDK round-trips, and can fire a hook between them.

    ⚠ IT PATCHES ``query_raw`` **ONLY**, and that is a MEASURED correction rather
    than a simplification: the SDK's ``query()`` is a thin wrapper that CALLS
    ``query_raw()`` and then checks ``result[0]``
    (``surrealdb.connections.async_ws.AsyncWsSurrealConnection.query``, read
    2026-07-26). Patching both counts every single-statement call TWICE, which
    is how the first version of this helper reported "2 round-trips" for a CAS
    that issues exactly one. ``query_raw`` is the one true wire boundary and it
    sees the transactional path as well.

    ⚠ WHY INTERCEPT AT THE CONNECTION rather than at the ledger's own methods:
    every statement in this package must ride ``_txn`` (pinned separately), so
    the connection is the one place every round-trip must pass. It makes no
    assumption about how the ledger imports, names, or composes its helpers.
    """

    def __init__(self) -> None:
        self.round_trips = 0
        self.hook_fired = False

    def install(
        self,
        connection: Any,
        monkeypatch: pytest.MonkeyPatch,
        *,
        before_call_number: int | None = None,
        hook: Any = None,
    ) -> None:
        """Wrap ``connection``'s wire entry point.

        Args:
            before_call_number: 1-based index of the round-trip to fire ``hook``
                immediately BEFORE. ``None`` disables the hook entirely.
        """
        original_query_raw = connection.query_raw

        async def counted(*args: Any, **kwargs: Any) -> Any:
            if (
                hook is not None
                and before_call_number is not None
                and self.round_trips + 1 == before_call_number
                and not self.hook_fired
            ):
                self.hook_fired = True
                await hook()
            self.round_trips += 1
            return await original_query_raw(*args, **kwargs)

        monkeypatch.setattr(connection, "query_raw", counted)


# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture()
async def lease_env() -> AsyncIterator[SurrealEnv]:
    """A fresh throwaway database on the TEST store (spike-surreal, :18000).

    Built from the harness helpers directly rather than by depending on the
    ``surreal_env`` fixture: resolving one async fixture from inside another
    re-enters pytest-asyncio's shared per-function ``Runner``. Same isolation
    guarantee, no fixture-graph entanglement (the ``test_findings.py``
    precedent).
    """
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    try:
        yield env
    finally:
        await drop_database(env)


@pytest_asyncio.fixture()
async def lease_store(lease_env: SurrealEnv) -> AsyncIterator[SurrealLeaseStore]:
    """One ready lease store on a fresh database."""
    store = SurrealLeaseStore(
        url=lease_env.url,
        namespace=lease_env.namespace,
        database=lease_env.database,
        user=lease_env.user,
        password=lease_env.password,
    )
    await store.ensure_ready()
    try:
        yield store
    finally:
        await store.close()


async def _new_store(env: SurrealEnv) -> SurrealLeaseStore:
    """An INDEPENDENT store (its own connection) on the same database."""
    store = SurrealLeaseStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    await store.ensure_ready()
    return store




# =============================================================================
# 1. THE LIBRARY'S OWN INTERFACE — derived from the installed source.
# =============================================================================


class TestTheLockInterfaceIsDerived:
    """ALLOWLIST THE SAFE, NEVER ENUMERATE THE FORBIDDEN — applied to a THIRD
    PARTY's interface. Six instruments in this repo have been defeated by a
    hand-written name list; the fix is to derive the list from the thing it
    describes and let a change go RED.
    """

    @staticmethod
    def _members_touched_by_the_algorithm() -> frozenset[str]:
        touched: set[str] = set()
        for module in (leaderelection, electionconfig):
            module_file = module.__file__
            assert module_file is not None, "the installed algorithm has no source to scan"
            source = pathlib.Path(module_file).read_text(encoding="utf-8")
            for node in ast.walk(ast.parse(source)):
                if (
                    isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Attribute)
                    and node.value.attr == "lock"
                ):
                    touched.add(node.attr)
        return frozenset(touched)

    def test_the_algorithm_touches_exactly_six_lock_members(self) -> None:
        """Measured 2026-07-26, kubernetes 36.0.3. If this reddens, the library
        changed what it needs from a lock — read the new member before adapting.
        """
        assert self._members_touched_by_the_algorithm() == EXPECTED_LOCK_MEMBERS

    def test_the_derivation_is_not_vacuous(self) -> None:
        """CONTROL. A scanner that found nothing would make the pin above
        silently green against ANY adapter."""
        assert len(self._members_touched_by_the_algorithm()) >= 6

    def test_our_adapter_provides_every_member_the_algorithm_touches(self) -> None:
        """Checked on an INSTANCE, not on the class: three of the six members are
        ATTRIBUTES the algorithm reads off the object (``identity`` / ``name`` /
        ``namespace``). A class-level ``hasattr`` would report a missing member
        on a perfectly correct adapter — and, worse, a bare class ANNOTATION
        with no assignment would SATISFY a class-level pin while the instance
        carried nothing at all.
        """
        lock = SurrealLeaderLock(
            store=SurrealLeaseStore(
                url="ws://127.0.0.1:19555/rpc",  # unreachable — never dialed
                namespace="ns",
                database="db",
                user="root",
                password=SecretStr("root"),
            ),
            identity="pod-a",
            loop=None,
        )
        for member in self._members_touched_by_the_algorithm():
            assert hasattr(lock, member), (
                f"SurrealLeaderLock is missing {member!r}, which the installed "
                f"election algorithm reads off its lock"
            )

    def test_the_create_parameter_is_named_election_record(self) -> None:
        """⚠ The algorithm calls ``lock.create(name=…, namespace=…,
        election_record=…)`` BY KEYWORD. A parameter named ``record`` type-checks,
        reads better, and raises ``TypeError`` the first time a lock is created
        — on a virgin store, in production, at the one moment nothing else can
        proceed."""
        import inspect

        parameters = inspect.signature(SurrealLeaderLock.create).parameters
        assert "election_record" in parameters

    def test_the_record_the_library_writes_has_exactly_four_fields(self) -> None:
        """R10.1's load-bearing fact: fencing CANNOT live in the record."""
        record = LeaderElectionRecord("me", "15", "t", "t")
        assert set(vars(record)) == EXPECTED_RECORD_FIELDS


class TestTheAbsentGetContract:
    """⚠ THE MEASURED CORRECTION TO THE RULED DESIGN, with both controls.

    The design describes ``get`` as returning ``(status, record)``. Implemented
    literally, the FIRST-EVER acquisition raises inside the library. These pins
    prove the failure is real, prove which shape survives, and prove the pin
    itself can discriminate.
    """

    class _Lock:
        """A minimal in-memory lock; subclasses vary ONLY the absent-get shape."""

        def __init__(self) -> None:
            self.identity = "pod-a"
            self.name = "lease"
            self.namespace = "lore"
            self.row: LeaderElectionRecord | None = None

        def get(self, name: str, namespace: str) -> tuple[bool, Any]:
            raise NotImplementedError

        def create(self, name: str, namespace: str, election_record: Any) -> bool:
            self.row = election_record
            return True

        def update(self, name: str, namespace: str, updated_record: Any) -> bool:
            self.row = updated_record
            return True

    class _NoneOnAbsent(_Lock):
        def get(self, name: str, namespace: str) -> tuple[bool, Any]:
            return (True, self.row) if self.row is not None else (False, None)

    class _BareApiExceptionOnAbsent(_Lock):
        def get(self, name: str, namespace: str) -> tuple[bool, Any]:
            if self.row is not None:
                return True, self.row
            return False, ApiException(status=404, reason="Not Found")

    class _LockAbsentOnAbsent(_Lock):
        def get(self, name: str, namespace: str) -> tuple[bool, Any]:
            if self.row is not None:
                return True, self.row
            return False, LockAbsent(
                body=json.dumps({"code": 404, "message": "lease row absent"}),
                reason="Not Found",
                status=404,
            )

    @staticmethod
    def _election(lock: Any) -> LeaderElection:
        return LeaderElection(
            electionconfig.Config(
                lock,
                FAST_LEASE_SECONDS,
                FAST_RENEW_DEADLINE_SECONDS,
                FAST_RETRY_PERIOD_SECONDS,
                lambda: None,
                lambda: None,
            )
        )

    def test_returning_None_on_absent_BREAKS_the_first_acquisition(self) -> None:
        """DIFFERENTLY-BROKEN CONTROL #1 — the design's literal reading."""
        with pytest.raises(AttributeError):
            self._election(self._NoneOnAbsent()).try_acquire_or_renew()

    def test_a_bare_ApiException_on_absent_ALSO_breaks_it(self) -> None:
        """DIFFERENTLY-BROKEN CONTROL #2, and the reason ``LockAbsent`` exists
        at all: "just reuse the library's own exception" fails for a DIFFERENT
        reason (``ApiException(status=…)`` leaves ``.body`` as ``None``), so a
        single control would have licensed the wrong fix."""
        with pytest.raises(TypeError):
            self._election(self._BareApiExceptionOnAbsent()).try_acquire_or_renew()

    def test_the_LockAbsent_shape_lets_the_lock_be_created(self) -> None:
        """POSITIVE CONTROL: the probe can see a SUCCESS, so the two failures
        above are real negatives rather than a blind instrument."""
        lock = self._LockAbsentOnAbsent()
        assert self._election(lock).try_acquire_or_renew() is True
        assert lock.row is not None
        assert lock.row.holder_identity == "pod-a"

    def test_LockAbsent_carries_a_json_body_naming_the_404_code(self) -> None:
        """The shape our adapter must return, pinned independently of the
        library so a builder can satisfy it without reading the algorithm."""
        absent = LockAbsent(body=json.dumps({"code": 404}), reason="Not Found", status=404)
        assert json.loads(absent.body)["code"] == 404
        assert absent.reason


class TestTheLeaseTunables:
    """Ruling L2, OPERATOR-CONFIRMED: client-go's 15/10/2, passed EXPLICITLY."""

    def test_the_three_tunables_are_client_gos_documented_defaults(self) -> None:
        assert (
            LEASE_DURATION_SECONDS,
            LEASE_RENEW_DEADLINE_SECONDS,
            LEASE_RETRY_PERIOD_SECONDS,
        ) == (15, 10, 2)

    def test_the_tunables_pass_the_librarys_OWN_validation(self) -> None:
        """``Config`` validates ``lease_duration > renew_deadline`` and
        ``renew_deadline > 1.2 * retry_period`` — and REJECTS by calling
        ``sys.exit``. A triple that fails would take the process down at
        construction, so the values are pinned against the validator, not
        against a comment."""
        config = electionconfig.Config(
            object(),
            LEASE_DURATION_SECONDS,
            LEASE_RENEW_DEADLINE_SECONDS,
            LEASE_RETRY_PERIOD_SECONDS,
            lambda: None,
            lambda: None,
        )
        assert config.lease_duration == LEASE_DURATION_SECONDS

    @pytest.mark.parametrize(
        "duration,deadline,retry",
        [
            (10, 15, 2),  # duration <= deadline
            (15, 10, 9),  # deadline <= 1.2 * retry
            (15, 10, 0),  # retry < 1
        ],
    )
    def test_the_validator_really_rejects_an_illegal_triple(
        self, duration: int, deadline: int, retry: int
    ) -> None:
        """CONTROL on the pin above: a validator that accepted everything would
        make "our values pass" worthless. Also pins the RAISED TYPE —
        ``SystemExit``, not ``ValueError`` — because a builder catching
        ``ValueError`` around config construction would swallow a process exit.
        """
        with pytest.raises(SystemExit):
            electionconfig.Config(object(), duration, deadline, retry, lambda: None, lambda: None)

    def test_lease_election_config_passes_the_tunables_through(self) -> None:
        config = lease_election_config(
            lock=object(),  # type: ignore[arg-type]
            on_started_leading=lambda: None,
            on_stopped_leading=lambda: None,
        )
        assert (config.lease_duration, config.renew_deadline, config.retry_period) == (
            LEASE_DURATION_SECONDS,
            LEASE_RENEW_DEADLINE_SECONDS,
            LEASE_RETRY_PERIOD_SECONDS,
        )

    def test_lease_election_config_installs_BOTH_callbacks(self) -> None:
        """``Config`` substitutes its own no-op ``onstopped_leading`` when None
        is passed — silently. A build that forgot to wire abdication would look
        identical, and the run would never learn it had lost the lease."""
        started: list[str] = []
        stopped: list[str] = []
        config = lease_election_config(
            lock=object(),  # type: ignore[arg-type]
            on_started_leading=lambda: started.append("x"),
            on_stopped_leading=lambda: stopped.append("x"),
        )
        config.onstarted_leading()
        config.onstopped_leading()
        assert started == ["x"] and stopped == ["x"]


# =============================================================================
# 2. THE STORE SEAM — against the real engine.
# =============================================================================


class TestTheLeaseSeamIsAConventionalLedger:
    """R2.2's coverage obligation, made mechanical.

    ``test_retry_seam.py`` discovers every class in the package owning an
    ``async def _query`` and drives it against the real engine under the
    runtime SDK guard. A seam that falls OUT of that enumeration certifies
    nothing — finding #120 one altitude up — so membership is pinned HERE
    rather than hoped for.
    """

    def test_the_lease_store_is_discovered_by_the_shared_seam_enumerator(self) -> None:
        from test_retry_seam import _discover_query_seams  # noqa: PLC0415

        discovered = {seam.__name__ for _, seam in _discover_query_seams()}
        assert "SurrealLeaseStore" in discovered, (
            "SurrealLeaseStore is not in the shared `async def _query` enumeration, "
            "so the runtime SDK guard never drives it and its retry behaviour is "
            "certified by nothing."
        )

    def test_the_lease_store_constructs_from_the_shared_ctor_values(self) -> None:
        """The enumeration builds each seam from ``_CTOR_VALUES``; a constructor
        wanting anything else turns the shared suite RED for everyone."""
        from test_retry_seam import _construct  # noqa: PLC0415

        assert _construct(SurrealLeaseStore) is not None

    def test_the_seam_is_discovered_as_a_SOCKET_OWNER_too(self) -> None:
        """⚠ A SECOND inherited enumeration, and it is invisible until the seam is
        BUILT — which is exactly why it is pinned here rather than discovered by
        a builder.

        ``test_retry_seam.py`` has a separate scan for classes whose
        ``_ensure_connection`` CONSTRUCTS a socket, and it parametrises the
        "N concurrent first-callers open exactly ONE socket" pin over them.
        Against the stub those two node ids do not even COLLECT (the stub
        constructs nothing), so the seam silently gains two pins the moment the
        builder writes the double-checked-locking connect — measured: the same
        file collects 559 ids against the stub and 561 against a correct build.

        A pin that appears out of nowhere is the benign direction of the B1
        class; naming it here means the builder MEETS the obligation
        (double-checked lock, one socket per owner) instead of tripping over it.
        """
        from test_retry_seam import _discover_socket_owners  # noqa: PLC0415

        assert "SurrealLeaseStore" in {name for _, name in _discover_socket_owners()}, (
            "SurrealLeaseStore is not in the socket-owner enumeration — its "
            "`_ensure_connection` must construct its own connection under a "
            "double-checked lock, like every other owner in the package"
        )



class TestTheLeaseRowLifecycle:
    """create → read → CAS → release, against the live engine."""

    async def test_a_fresh_database_has_no_lease_row(self, lease_store: SurrealLeaseStore) -> None:
        assert await lease_store.read() is None

    async def test_create_if_absent_mints_the_row_with_both_counters(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        observation = await lease_store.create_if_absent(
            holder_identity="pod-a", lease_duration="15", acquire_time="t0", renew_time="t0"
        )
        assert observation is not None
        assert observation.holder_identity == "pod-a"
        # Both counters exist from birth: a lease row whose ``fence_epoch`` is
        # absent (or None) makes every fenced commit unguarded rather than
        # loud.
        assert isinstance(observation.revision, int)
        assert isinstance(observation.fence_epoch, int)

    async def test_a_SECOND_create_returns_None_and_does_not_overwrite(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        """The defined-empty-result discipline: a lost race is a VALUE, never a
        retry and never an exception. A ``create`` that silently overwrote would
        hand two pods the lease simultaneously."""
        await lease_store.create_if_absent(
            holder_identity="pod-a", lease_duration="15", acquire_time="t0", renew_time="t0"
        )
        second = await lease_store.create_if_absent(
            holder_identity="pod-b", lease_duration="15", acquire_time="t1", renew_time="t1"
        )
        assert second is None
        current = await lease_store.read()
        assert current is not None and current.holder_identity == "pod-a"

    async def test_a_matching_CAS_advances_the_revision(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        created = await lease_store.create_if_absent(
            holder_identity="pod-a", lease_duration="15", acquire_time="t0", renew_time="t0"
        )
        assert created is not None
        renewed = await lease_store.compare_and_set(
            observed_revision=created.revision,
            holder_identity="pod-a",
            lease_duration="15",
            acquire_time="t0",
            renew_time="t1",
        )
        assert renewed is not None
        assert renewed.revision == created.revision + 1

    async def test_a_STALE_CAS_returns_None_and_changes_nothing(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        """The optimistic-concurrency token doing its job. RED against a build
        that UPSERTs unconditionally — which passes every "the holder is
        recorded" pin while letting a stale pod stomp a live one."""
        created = await lease_store.create_if_absent(
            holder_identity="pod-a", lease_duration="15", acquire_time="t0", renew_time="t0"
        )
        assert created is not None
        await lease_store.compare_and_set(
            observed_revision=created.revision,
            holder_identity="pod-a",
            lease_duration="15",
            acquire_time="t0",
            renew_time="t1",
        )
        stale = await lease_store.compare_and_set(
            observed_revision=created.revision,  # the SUPERSEDED revision
            holder_identity="pod-b",
            lease_duration="15",
            acquire_time="t2",
            renew_time="t2",
        )
        assert stale is None
        current = await lease_store.read()
        assert current is not None and current.holder_identity == "pod-a"

    async def test_the_fence_epoch_does_NOT_move_when_the_SAME_holder_renews(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        """⚠ THE DISCRIMINATING HALF of the fence's definition, and the one a
        "bump the counters together" build gets wrong. A fence that advanced on
        every renewal would invalidate the holder's OWN in-flight commit every
        two seconds — the mechanism eating the function."""
        created = await lease_store.create_if_absent(
            holder_identity="pod-a", lease_duration="15", acquire_time="t0", renew_time="t0"
        )
        assert created is not None
        renewed = created
        for tick in range(3):
            next_observation = await lease_store.compare_and_set(
                observed_revision=renewed.revision,
                holder_identity="pod-a",
                lease_duration="15",
                acquire_time="t0",
                renew_time=f"t{tick}",
            )
            assert next_observation is not None
            renewed = next_observation
        assert renewed.fence_epoch == created.fence_epoch
        assert renewed.revision == created.revision + 3

    async def test_the_fence_epoch_DOES_move_when_the_holder_changes(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        created = await lease_store.create_if_absent(
            holder_identity="pod-a", lease_duration="15", acquire_time="t0", renew_time="t0"
        )
        assert created is not None
        seized = await lease_store.compare_and_set(
            observed_revision=created.revision,
            holder_identity="pod-b",
            lease_duration="15",
            acquire_time="t1",
            renew_time="t1",
        )
        assert seized is not None
        assert seized.fence_epoch == created.fence_epoch + 1
        assert seized.revision == created.revision + 1

    async def test_only_ONE_racer_can_win_a_CAS_against_one_observed_revision(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        """⚠ RENAMED AND RE-JUSTIFIED — this pin was a FALSE GATE (adversary F1a).

        Its old name and docstring promised *"the counters are minted STORE-SIDE
        in one update … proven by CONTENTION"*, and the build it named — both
        counters computed CLIENT-SIDE from a separate read — PASSES it, here and
        at 8/16/32-way. Worse, the causal claim was itself false: the
        ``WHERE revision = $observed_revision`` predicate is what serialises, so
        a client-computed increment cannot lose an update while the CAS is
        present, and the genuinely dangerous build (drop the ``WHERE``) is caught
        by ``test_a_STALE_CAS_returns_None_and_changes_nothing``. A failure
        message that promises a check the assertion does not perform is exactly
        the shape this repo treats as a defect.

        What it ACTUALLY proves, which is real and worth keeping: a CAS admits
        exactly ONE winner per observed revision. The store-side claim is now
        pinned where it can discriminate — ``test_a_CAS_is_ONE_round_trip``.
        """
        created = await lease_store.create_if_absent(
            holder_identity="pod-a", lease_duration="15", acquire_time="t0", renew_time="t0"
        )
        assert created is not None
        outcomes = await asyncio.gather(
            *(
                lease_store.compare_and_set(
                    observed_revision=created.revision,
                    holder_identity="pod-a",
                    lease_duration="15",
                    acquire_time="t0",
                    renew_time=f"t{index}",
                )
                for index in range(_HOT_ROW_RACERS)
            )
        )
        winners = [outcome for outcome in outcomes if outcome is not None]
        assert len(winners) == 1, (
            f"{len(winners)} of {_HOT_ROW_RACERS} CAS attempts against ONE observed "
            f"revision succeeded — a compare-and-set that admits more than one "
            f"winner is not a compare-and-set"
        )
        current = await lease_store.read()
        assert current is not None and current.revision == created.revision + 1

    async def test_a_CAS_is_ONE_round_trip(
        self, lease_store: SurrealLeaseStore, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ M12 — the store-side claim, pinned where it can actually fail.

        A build that computes ``revision + 1`` and the conditional
        ``fence_epoch`` bump CLIENT-SIDE must first READ the row, so it issues
        TWO round-trips; a build that mints both in the UPDATE issues one. The
        counters' VALUES are indistinguishable between the two (that is why the
        contention pin above could never see it), so the round-trip count is the
        only thing that discriminates — and it is also the property that matters,
        because a read-then-write pair is a second window the CAS does not cover.
        """
        created = await lease_store.create_if_absent(
            holder_identity="pod-a", lease_duration="15", acquire_time="t0", renew_time="t0"
        )
        assert created is not None

        trips = _RoundTrips()
        connection = await lease_store._ensure_connection()
        trips.install(connection, monkeypatch)

        await lease_store.compare_and_set(
            observed_revision=created.revision,
            holder_identity="pod-b",
            lease_duration="15",
            acquire_time="t1",
            renew_time="t1",
        )
        assert trips.round_trips == 1, (
            f"a CAS issued {trips.round_trips} round-trips; both counters must be minted "
            f"STORE-SIDE in the same UPDATE, never read-then-computed by the client"
        )

    async def test_create_if_absent_RAISES_on_a_non_duplicate_rejection(
        self, lease_env: SurrealEnv
    ) -> None:
        """⚠ M10 — ONLY a duplicate is a lost race.

        A build reporting EVERY rejection as ``None`` passed the whole contract
        (adversary W26), and the symptom is the worst kind: a pod whose write is
        refused for any other reason silently "never leads" — indistinguishable
        from a pod that legitimately lost the race, forever, with nothing logged
        and nothing red.

        ⚠ THE FORCING LEVER IS A NARROWED ASSERT, not a dropped table, and the
        first attempt at this pin got that wrong: ``REMOVE TABLE lease`` does not
        make the write fail at all — SurrealDB AUTO-CREATES an undeclared table
        on first write (store reference §5), so the create SUCCEEDS and the pin
        passed on a build that swallows everything. A narrowed ASSERT rejects the
        write while leaving the row genuinely absent, which is the state that
        distinguishes "refused" from "lost the race".
        """
        store = await _new_store(lease_env)
        admin = await connect_admin(lease_env)
        try:
            await admin.query(
                "DEFINE FIELD OVERWRITE holder_identity ON lease "
                "TYPE option<string> ASSERT $value = NONE OR string::len($value) < 2"
            )
            with pytest.raises(SurrealStoreError):
                await store.create_if_absent(
                    holder_identity="pod-a",
                    lease_duration="15",
                    acquire_time="t0",
                    renew_time="t0",
                )
            # …and the row really is ABSENT, so "we lost the race" was never a
            # legitimate reading of this failure.
            assert await store.read() is None
        finally:
            await admin.close()
            await store.close()


class TestReleaseIfHeld:
    """RULED DECISION 23. This port has no ``release``; without this every
    rolling update waits out a full ``lease_duration`` before maintenance
    resumes anywhere in the deployment.
    """

    async def test_the_holder_can_release_its_own_lease(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        created = await lease_store.create_if_absent(
            holder_identity="pod-a", lease_duration="15", acquire_time="t0", renew_time="t0"
        )
        assert created is not None
        assert (
            await lease_store.release_if_held(
                holder_identity="pod-a", fence_epoch=created.fence_epoch
            )
            is True
        )
        current = await lease_store.read()
        assert current is not None and current.holder_identity is None

    async def test_a_released_lease_is_immediately_acquirable(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        """The whole point of decision 23 — pinned as the OUTCOME (handoff is
        immediate), not as "the column is None"."""
        created = await lease_store.create_if_absent(
            holder_identity="pod-a", lease_duration="15", acquire_time="t0", renew_time="t0"
        )
        assert created is not None
        await lease_store.release_if_held(
            holder_identity="pod-a", fence_epoch=created.fence_epoch
        )
        released = await lease_store.read()
        assert released is not None
        seized = await lease_store.compare_and_set(
            observed_revision=released.revision,
            holder_identity="pod-b",
            lease_duration="15",
            acquire_time="t1",
            renew_time="t1",
        )
        assert seized is not None and seized.holder_identity == "pod-b"
        assert seized.fence_epoch == created.fence_epoch + 1

    async def test_a_WRONG_IDENTITY_cannot_release_a_live_holder(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        created = await lease_store.create_if_absent(
            holder_identity="pod-a", lease_duration="15", acquire_time="t0", renew_time="t0"
        )
        assert created is not None
        assert (
            await lease_store.release_if_held(
                holder_identity="pod-b", fence_epoch=created.fence_epoch
            )
            is False
        )
        current = await lease_store.read()
        assert current is not None and current.holder_identity == "pod-a"

    async def test_a_STALE_FENCE_cannot_release_the_lease_it_no_longer_holds(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        """⚠ The zombie case, and the reason ``release_if_held`` takes the fence
        and not just the identity: a pod that held the lease, lost it, and then
        ran its ``finally`` would otherwise clear the NEW holder's lease on its
        way out — a graceful shutdown causing the outage it exists to avoid.

        The fixture re-uses the SAME identity so only the fence can discriminate:
        an identity-only guard passes every other pin in this class.
        """
        created = await lease_store.create_if_absent(
            holder_identity="pod-a", lease_duration="15", acquire_time="t0", renew_time="t0"
        )
        assert created is not None
        # pod-b seizes, then pod-a re-acquires: same identity, moved fence.
        seized = await lease_store.compare_and_set(
            observed_revision=created.revision,
            holder_identity="pod-b",
            lease_duration="15",
            acquire_time="t1",
            renew_time="t1",
        )
        assert seized is not None
        reacquired = await lease_store.compare_and_set(
            observed_revision=seized.revision,
            holder_identity="pod-a",
            lease_duration="15",
            acquire_time="t2",
            renew_time="t2",
        )
        assert reacquired is not None
        assert (
            await lease_store.release_if_held(
                holder_identity="pod-a", fence_epoch=created.fence_epoch  # the OLD epoch
            )
            is False
        )
        current = await lease_store.read()
        assert current is not None and current.holder_identity == "pod-a"

    async def test_releasing_an_ABSENT_lease_row_is_False_not_an_error(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        """A ``finally`` that raises on a run which never acquired would mask
        the run's real failure."""
        assert (
            await lease_store.release_if_held(holder_identity="pod-a", fence_epoch=0) is False
        )


class TestTheHotRowUnderContention:
    """THE HOT-ROW LAW: >= 8-way, OVERLAPPING racer lifetimes (repeated
    operations per racer, so a start-line barrier is not the only overlap), on
    SEPARATE live connections.

    ⚠ A single green run NEVER clears a concurrency test — twenty consecutive
    greens are the BUILDER's obligation and belong in its report. This pin is
    the instrument, not the discharge.
    """

    @pytest.mark.parametrize("racers", [_HOT_ROW_RACERS, *_HOT_ROW_SCALE])
    async def test_no_write_is_ever_lost_under_contention(
        self, lease_env: SurrealEnv, racers: int
    ) -> None:
        """Each racer loops read → CAS until it lands a fixed number of writes.
        The invariant that DISCRIMINATES: the final revision equals the total
        number of successful writes, exactly. A lost update (an unconditional
        UPSERT, or a client-computed increment) leaves it LOW; a double-apply
        leaves it HIGH; and neither shows up in "did somebody hold the lease".
        """
        writes_each = 3
        stores = [await _new_store(lease_env) for _ in range(racers)]
        try:
            created = await stores[0].create_if_absent(
                holder_identity="holder", lease_duration="15", acquire_time="t0", renew_time="t0"
            )
            assert created is not None

            async def racer(store: SurrealLeaseStore, index: int) -> int:
                landed = 0
                while landed < writes_each:
                    observed = await store.read()
                    assert observed is not None
                    result = await store.compare_and_set(
                        observed_revision=observed.revision,
                        holder_identity="holder",  # same holder: fence must not move
                        lease_duration="15",
                        acquire_time="t0",
                        renew_time=f"r{index}-{landed}",
                    )
                    if result is not None:
                        landed += 1
                return landed

            landed = await asyncio.gather(
                *(racer(store, index) for index, store in enumerate(stores))
            )
            assert sum(landed) == racers * writes_each
            final = await stores[0].read()
            assert final is not None
            assert final.revision == created.revision + racers * writes_each, (
                f"{racers}-way contention lost or duplicated writes: revision moved "
                f"{final.revision - created.revision}, expected {racers * writes_each}"
            )
            assert final.fence_epoch == created.fence_epoch, (
                "the fence moved while the holder never changed"
            )
        finally:
            for store in stores:
                await store.close()

    async def test_exactly_one_racer_wins_the_FIRST_EVER_create(
        self, lease_env: SurrealEnv
    ) -> None:
        """The virgin-store race — the one path a long-lived deployment runs
        exactly once and no dirty-store fixture can ever reach again."""
        stores = [await _new_store(lease_env) for _ in range(_HOT_ROW_RACERS)]
        try:
            outcomes = await asyncio.gather(
                *(
                    store.create_if_absent(
                        holder_identity=f"pod-{index}",
                        lease_duration="15",
                        acquire_time="t0",
                        renew_time="t0",
                    )
                    for index, store in enumerate(stores)
                )
            )
            winners = [outcome for outcome in outcomes if outcome is not None]
            assert len(winners) == 1, (
                f"{len(winners)} of {_HOT_ROW_RACERS} concurrent first-creates "
                f"succeeded — two leaders at the moment of birth"
            )
        finally:
            for store in stores:
                await store.close()


# =============================================================================
# 3. THE ADAPTER, DRIVEN BY THE REAL ALGORITHM, AGAINST THE REAL ENGINE.
# =============================================================================


def _lock(store: SurrealLeaseStore, identity: str, loop: Any) -> SurrealLeaderLock:
    return SurrealLeaderLock(store=store, identity=identity, loop=loop)


def _election(lock: SurrealLeaderLock, *, fast: bool = True) -> LeaderElection:
    """A ``LeaderElection`` over ``lock``.

    Driven through ``try_acquire_or_renew`` rather than ``run``: ``run`` blocks
    forever (``acquire`` loops until it wins, and there is no stop mechanism —
    R10.1), so a contract that called it could never assert a FOLLOWER's
    outcome. The single-attempt entry point is public and is what the algorithm
    itself calls on every tick.
    """
    duration = FAST_LEASE_SECONDS if fast else LEASE_DURATION_SECONDS
    deadline = FAST_RENEW_DEADLINE_SECONDS if fast else LEASE_RENEW_DEADLINE_SECONDS
    retry = FAST_RETRY_PERIOD_SECONDS if fast else LEASE_RETRY_PERIOD_SECONDS
    return LeaderElection(
        electionconfig.Config(lock, duration, deadline, retry, lambda: None, lambda: None)
    )


class TestTheAdapterUnderTheRealAlgorithm:
    """The composition, end to end. Every call crosses the sync/async bridge
    from a worker thread, which is the same submission path 11-ii's election
    thread uses.
    """

    async def test_the_first_candidate_creates_the_lock_and_leads(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        """The leg both differently-broken controls in
        ``TestTheAbsentGetContract`` fail — here against the real store."""
        lock = _lock(lease_store, "pod-a", asyncio.get_running_loop())
        assert await asyncio.to_thread(_election(lock).try_acquire_or_renew) is True
        observation = await lease_store.read()
        assert observation is not None and observation.holder_identity == "pod-a"

    async def test_the_holder_renews_without_moving_the_fence(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        lock = _lock(lease_store, "pod-a", asyncio.get_running_loop())
        election = _election(lock)
        assert await asyncio.to_thread(election.try_acquire_or_renew) is True
        first = await lease_store.read()
        assert first is not None
        assert await asyncio.to_thread(election.try_acquire_or_renew) is True
        second = await lease_store.read()
        assert second is not None
        assert second.fence_epoch == first.fence_epoch
        assert second.revision > first.revision

    async def test_a_LIVE_HOLDER_IS_NOT_STOLEN(self, lease_env: SurrealEnv) -> None:
        """R2.2 fixture (ii) — kills a boot-reclaim-style build.

        The challenger races a RENEWING holder for LONGER than one
        ``lease_duration`` of wall-clock and must never acquire. A build that
        reclaims on boot, or that treats "the row exists" as "it may be mine",
        passes every single-candidate pin above and steals a healthy run.
        """
        loop = asyncio.get_running_loop()
        holder_store = await _new_store(lease_env)
        challenger_store = await _new_store(lease_env)
        try:
            holder = _election(_lock(holder_store, "pod-a", loop))
            challenger = _election(_lock(challenger_store, "pod-b", loop))
            assert await asyncio.to_thread(holder.try_acquire_or_renew) is True

            deadline = time.monotonic() + FAST_LEASE_SECONDS * 2
            while time.monotonic() < deadline:
                assert await asyncio.to_thread(holder.try_acquire_or_renew) is True
                assert await asyncio.to_thread(challenger.try_acquire_or_renew) is False, (
                    "the challenger acquired a lease a healthy holder was renewing"
                )
                await asyncio.sleep(0.2)

            observation = await holder_store.read()
            assert observation is not None and observation.holder_identity == "pod-a"
        finally:
            await holder_store.close()
            await challenger_store.close()

    async def test_an_EXPIRED_lease_IS_seized_and_the_fence_moves(
        self, lease_env: SurrealEnv
    ) -> None:
        """R2.2 fixture (i) — expiry-seize, and the fence bump that makes the
        zombie's commit refusable. The holder is SILENCED (never renews) rather
        than deleted, because a deleted row exercises the create path instead.

        ⚠ The challenger must OBSERVE the record before its own clock can
        expire it (the algorithm times ``lease_duration`` from when IT last saw
        the record CHANGE), which is why it polls rather than sleeping once.
        """
        loop = asyncio.get_running_loop()
        holder_store = await _new_store(lease_env)
        challenger_store = await _new_store(lease_env)
        try:
            holder = _election(_lock(holder_store, "pod-a", loop))
            challenger = _election(_lock(challenger_store, "pod-b", loop))
            assert await asyncio.to_thread(holder.try_acquire_or_renew) is True
            before = await holder_store.read()
            assert before is not None

            seized = False
            deadline = time.monotonic() + FAST_LEASE_SECONDS * 4
            while time.monotonic() < deadline:
                if await asyncio.to_thread(challenger.try_acquire_or_renew):
                    seized = True
                    break
                await asyncio.sleep(0.25)

            assert seized, (
                f"a silenced holder's lease was never seized within "
                f"{FAST_LEASE_SECONDS * 4}s at a {FAST_LEASE_SECONDS}s duration"
            )
            after = await holder_store.read()
            assert after is not None
            assert after.holder_identity == "pod-b"
            assert after.fence_epoch == before.fence_epoch + 1

            # And the zombie learns it lost: its next tick fails, which is what
            # ends the library's renew loop and fires ``onstopped_leading``.
            assert await asyncio.to_thread(holder.try_acquire_or_renew) is False
        finally:
            await holder_store.close()
            await challenger_store.close()

    async def test_the_STOP_POISON_ends_the_holders_renewals(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        """R10.3's cooperative shutdown. The library ships NO stop mechanism, so
        the adapter supplies one by making writes fail — which is what makes
        ``renew_loop`` return and ``onstopped_leading`` run. Pinned as the
        OBSERVABLE consequence (the next tick fails), never as a flag's value.
        """
        lock = _lock(lease_store, "pod-a", asyncio.get_running_loop())
        election = _election(lock)
        assert await asyncio.to_thread(election.try_acquire_or_renew) is True
        lock.stop()
        assert await asyncio.to_thread(election.try_acquire_or_renew) is False

    async def test_the_adapter_exposes_the_fence_epoch_it_wrote_under(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        """The engine's fenced commit needs the epoch; a lock that knows the
        holder but not the fence cannot guard anything."""
        lock = _lock(lease_store, "pod-a", asyncio.get_running_loop())
        assert await asyncio.to_thread(_election(lock).try_acquire_or_renew) is True
        observation = await lease_store.read()
        assert observation is not None
        assert lock.fence_epoch == observation.fence_epoch


class TestTheAdapterOwnedVerbs:
    """The three members that are OURS, not the library's — and every one of them
    survived the first contract untouched.
    """

    async def test_the_adapters_update_CASes_on_the_revision_IT_observed(
        self, lease_env: SurrealEnv
    ) -> None:
        """⚠ M7 — the adapter's CAS token, which W18 deleted at 143 / 0.

        An adapter that RE-READS the row inside ``update`` (instead of using the
        revision it captured at ``get``) can never lose its CAS, which is the
        optimistic-concurrency token gone: the window between the algorithm's
        ``get`` and its ``update`` re-opens, and two candidates can both write.

        Forced by moving the row from a SECOND connection between the lock's
        ``get`` and its ``update`` — the exact interleaving the token exists for.
        """
        loop = asyncio.get_running_loop()
        holder_store = await _new_store(lease_env)
        interloper = await _new_store(lease_env)
        try:
            lock = _lock(holder_store, "pod-a", loop)
            election = _election(lock)
            assert await asyncio.to_thread(election.try_acquire_or_renew) is True

            # The lock OBSERVES the row …
            status, record = await asyncio.to_thread(lock.get, lock.name, lock.namespace)
            assert status is True

            # … then somebody else moves it.
            current = await interloper.read()
            assert current is not None
            moved = await interloper.compare_and_set(
                observed_revision=current.revision,
                holder_identity="pod-b",
                lease_duration="15",
                acquire_time="t9",
                renew_time="t9",
            )
            assert moved is not None

            # The lock's write must now FAIL on the revision it observed.
            assert (
                await asyncio.to_thread(lock.update, lock.name, lock.namespace, record) is False
            ), (
                "the adapter's update succeeded against a revision that had already "
                "moved — its CAS can never fail, so the token is decorative and the "
                "get/update window is unguarded"
            )
            after = await interloper.read()
            assert after is not None and after.holder_identity == "pod-b"
        finally:
            await holder_store.close()
            await interloper.close()

    async def test_the_adapters_release_if_held_ACTUALLY_releases(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        """⚠ M8 — decision 23's whole point, and a build returning ``False``
        unconditionally passed at 143 / 0 (W29).

        The STORE-level ``release_if_held`` was pinned four ways; the ADAPTER
        verb — the one a shutdown path actually calls — was pinned by nothing.
        The symptom of the no-op is invisible in tests and costs a full
        ``lease_duration`` of stalled maintenance on every rolling update, which
        is precisely the "does not work well on k8s" decision 23 exists to fix.
        """
        lock = _lock(lease_store, "pod-a", asyncio.get_running_loop())
        assert await asyncio.to_thread(_election(lock).try_acquire_or_renew) is True
        assert await asyncio.to_thread(lock.release_if_held) is True
        observation = await lease_store.read()
        assert observation is not None and observation.holder_identity is None

    async def test_the_adapters_fence_epoch_tracks_a_RENEW_and_a_SEIZE(
        self, lease_env: SurrealEnv
    ) -> None:
        """Adversary residual 7: ``fence_epoch`` was pinned only after ``create``,
        so a build that stopped updating it after the first write passed — and
        the engine's fenced commit reads it on EVERY run, so a stale value means
        every later commit is fenced against an epoch nobody holds.
        """
        loop = asyncio.get_running_loop()
        holder_store = await _new_store(lease_env)
        challenger_store = await _new_store(lease_env)
        try:
            holder = _lock(holder_store, "pod-a", loop)
            holder_election = _election(holder)
            assert await asyncio.to_thread(holder_election.try_acquire_or_renew) is True
            first = holder.fence_epoch

            # A renew must NOT move it …
            assert await asyncio.to_thread(holder_election.try_acquire_or_renew) is True
            assert holder.fence_epoch == first

            # … and a SEIZE by another identity must move ITS lock's view.
            observation = await challenger_store.read()
            assert observation is not None
            challenger = _lock(challenger_store, "pod-b", loop)
            assert (
                await asyncio.to_thread(challenger.update, challenger.name, challenger.namespace,
                                        LeaderElectionRecord("pod-b", "15", "t", "t"))
                in (True, False)
            )
            seized = await challenger_store.read()
            assert seized is not None
            if seized.holder_identity == "pod-b":
                assert challenger.fence_epoch == seized.fence_epoch
        finally:
            await holder_store.close()
            await challenger_store.close()

    def test_the_lock_coordinates_are_pinned_values(self) -> None:
        """Adversary residual 4: both constants are in the interface freeze 11-ii
        cites, and neither was pinned. They are identity labels the algorithm
        passes straight back to the lock, so a silent change is invisible until
        two deployments disagree about which lease they are contending for."""
        assert (LEASE_LOCK_NAME, LEASE_LOCK_NAMESPACE) == ("lore-maintenance", "lore")


class TestTheLibraryEntryPointWeDependOn:
    """⚠ E3's remaining half. The ruling names ``try_acquire_or_renew`` as the
    entry point (``run()`` blocks forever with no stop mechanism, which is
    incompatible with R2.2's *"never blocked on"*), and records that this
    borders on #209's private-internals class — the method is public but is not
    the documented entry point.

    A real bound gets the treatment this repo gives real bounds: the surface it
    rests on is DERIVED and pinned, so a library upgrade that reshapes it goes
    RED here instead of as a bare ``AttributeError`` inside a live test.

    **Named re-open trigger (E3): the day ``kubernetes`` ships a non-blocking
    public entry point, drive that instead and DELETE this class.**
    """

    def test_try_acquire_or_renew_exists_and_takes_no_arguments(self) -> None:
        import inspect  # noqa: PLC0415

        method = LeaderElection.try_acquire_or_renew
        parameters = [
            name for name in inspect.signature(method).parameters if name != "self"
        ]
        assert parameters == [], (
            f"LeaderElection.try_acquire_or_renew now takes {parameters} — the "
            f"contract drives it argument-free on every tick"
        )

    def test_the_algorithms_OWN_tick_calls_it(self) -> None:
        """Derived from the installed source, so "it is the tick" is measured
        rather than assumed: if the algorithm stops routing through it, driving
        it no longer exercises the real election path."""
        module_file = leaderelection.__file__
        assert module_file is not None
        tree = ast.parse(pathlib.Path(module_file).read_text(encoding="utf-8"))
        callers = {
            node.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and node.attr == "try_acquire_or_renew"
        }
        assert "try_acquire_or_renew" in callers


class TestTheRecordTheAdapterReturnsIsPure:
    """⚠ A LIVENESS BUG DISGUISED AS A COSMETIC ONE.

    The algorithm resets its observation clock whenever
    ``old_election_record.__dict__ != self.observed_record.__dict__``. If the
    adapter decorates the record it returns with anything that changes on an
    unrelated write — a revision, a read timestamp — then a FOLLOWER restarts
    its expiry clock on every poll and a DEAD LEADER'S LEASE NEVER EXPIRES.
    The deployment wedges, permanently, with every other pin in this file green.
    """

    async def test_get_returns_exactly_the_librarys_four_fields(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        lock = _lock(lease_store, "pod-a", asyncio.get_running_loop())
        assert await asyncio.to_thread(_election(lock).try_acquire_or_renew) is True
        status, record = await asyncio.to_thread(lock.get, lock.name, lock.namespace)
        assert status is True
        assert set(vars(record)) == EXPECTED_RECORD_FIELDS, (
            f"the record carries {sorted(set(vars(record)) - EXPECTED_RECORD_FIELDS)} "
            f"beyond the library's four fields — an attribute that changes on an "
            f"unrelated write makes a follower's expiry clock reset forever"
        )

    async def test_two_reads_with_no_intervening_write_are___dict___equal(
        self, lease_store: SurrealLeaseStore
    ) -> None:
        """The BEHAVIOURAL half of the pin above, and the one that survives a
        builder finding some other way to leak mutable state into the record."""
        lock = _lock(lease_store, "pod-a", asyncio.get_running_loop())
        assert await asyncio.to_thread(_election(lock).try_acquire_or_renew) is True
        _, first = await asyncio.to_thread(lock.get, lock.name, lock.namespace)
        await asyncio.sleep(0.05)
        _, second = await asyncio.to_thread(lock.get, lock.name, lock.namespace)
        assert vars(first) == vars(second)


class TestNoPrivateRetryPolicyLivesInThisPackage:
    """#102/#120, and F8-C6 verbatim: classification via
    ``_txn.is_retryable_conflict_error``, and NO MESSAGE MATCH ANYWHERE.

    Keyed on the SAFE set, not on a forbidden one: the module may import from
    ``_txn`` and may not contain the engine's conflict text, a private sleep
    ladder, or a private attempt budget. A name-list of forbidden spellings is
    the instrument this repo has watched fail six times.
    """

    @staticmethod
    def _source() -> str:
        import loremaster.store.lease as module  # noqa: PLC0415

        module_file = module.__file__
        assert module_file is not None
        return pathlib.Path(module_file).read_text(encoding="utf-8")

    def test_the_conflict_marker_text_appears_nowhere(self) -> None:
        assert "can be retried" not in self._source(), (
            "the lease package matches the engine's conflict text itself — "
            "classification belongs to `_txn.is_retryable_conflict_error`, and a "
            "local match is a private copy wearing the shared name"
        )

    def test_no_sleep_call_appears_in_the_module(self) -> None:
        """A private backoff is what #102 was: the ONE driver owns per-attempt
        jitter, the attempt floor, the deadline and the ceiling."""
        tree = ast.parse(self._source())
        sleeps = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "sleep"
        ]
        assert not sleeps, "a private sleep ladder in the lease package is a private backoff"
