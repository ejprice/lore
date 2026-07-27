"""Contract — packet 11-i-a, the floor-calibration LEDGER and the C8 pool read.

Written by `contract-11ia-1` (2026-07-26) against the ruled design (B4/B5, §7,
F4/F5/F6, C8/C10, R10.2's fence). The builder builds FROM this.

WHAT THIS FILE DECIDES (the interface freeze 11-i-b cites) —
``loremaster.floor_calibration.store``::

    FloorCalibrationError(SurrealStoreError) · FenceLostError
    LeaseFence(holder_identity, fence_epoch)
    AdoptedHead(head_identity, axes, measurement_id, revision, adopted_at)
    MeasurementReceipt(measurement_id, head_identity, adopted, head_revision)
    FloorCalibrationStore(url, namespace, database, user, password)
        ensure_ready / record_measurement / read_adopted_head /
        measurement_history / _ensure_connection / _query / close

…and ``loremaster.store.surreal``::

    CALIBRATION_POOL_COLUMNS · CalibrationPool(rows, counted_total, limit)
    CalibrationPoolError · CalibrationPoolTruncatedError
                         · CalibrationPoolCountMismatchError
    SurrealStore.enumerate_calibration_pool() -> CalibrationPool

⚠ THE HEAD IS A HOT ROW (B4). ``_txn.retry_on_conflict`` is the ONE driver:
no private retry, no private backoff, no private jitter, and no match on engine
message text (F8-C6). Findings #102/#120 are the receipts for exactly that
going wrong twice, in two DIFFERENT wrong ways — and a build that routes
through the driver while classifying locally is a private copy wearing the
shared name, which is why the pins here are BEHAVIOURAL (lost-update counts
under contention) rather than "does it import the driver".

⚠ AND THE ADOPTION PIN THAT MATTERS MOST is
``test_a_NON_adopted_measurement_does_NOT_move_the_head``. Every other pin in
this file passes on a build that advances the head on every measurement — and
that build silently serves an unadopted floor, which is the whole failure the
adopted-N rule exists to prevent.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import AsyncIterator, Mapping
from typing import Any

import pytest
import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    chunk_record,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
    unit_vector,
)
from loremaster.floor_calibration import domain as floor_domain
from loremaster.floor_calibration import store as floor_store_module
from loremaster.floor_calibration.domain import corpus_content_digest, head_identity
from loremaster.floor_calibration.store import (
    FenceLostError,
    FloorCalibrationStore,
    LeaseFence,
)
from loremaster.store import surreal as surreal_module
from loremaster.store._txn import SurrealStoreError
from loremaster.store.surreal import (
    CALIBRATION_POOL_COLUMNS,
    CalibrationPoolCountMismatchError,
    CalibrationPoolTruncatedError,
    SurrealStore,
)
from loremaster.store.surreal_schema import (
    FLOOR_MEASUREMENT_COLUMNS,
    FLOOR_MEASUREMENT_CREATED_AT_COLUMN,
    FLOOR_MEASUREMENT_HEAD_IDENTITY_COLUMN,
)
from pydantic import SecretStr
from test_floor_calibration_domain import EXPECTED_FLOOR_STATES

POOLED: Mapping[str, str] = {"scope": "pooled", "statistic": "cosine_floor"}
TIER_SCOPED: Mapping[str, str] = {"scope": "tier:lore", "statistic": "cosine_floor"}

_HOT_ROW_RACERS = 8
_HOT_ROW_SCALE = (16, 32)
_ADOPTIONS_PER_RACER = 3


def _measurement(
    *,
    state: str = "measured",
    floor: float = 0.5,
    non_adoption_cause: str | None = None,
    note: str | None = None,
    corpus_content_digest_value: str = "0" * 128,
    adopted_n: int = 200,
) -> dict[str, Any]:
    """A measurement payload.

    ⚠ ``state`` HAS NO DEFAULT-BY-ACCIDENT: it defaults to ``measured`` and
    every pin that cares passes its own value explicitly. Repo law — a fixture
    factory must not default a parameter the code BRANCHES on, because that is
    exactly how a render suite came to test only the one value for which its
    prose was true.

    ``non_adoption_cause`` and ``note`` default to ``None``, and that default is
    CORRECT rather than convenient: F5's typed cause appears ONLY on
    ``measured_not_adopted``, and §7 makes ``note`` mandatory ONLY when the state
    is not ``measured`` — so ``None`` is the one legal value for the default
    state, and every call that departs from it says so.
    """
    return {
        "floor": floor,
        "ci_low": floor - 0.01,
        "ci_high": floor + 0.01,
        "state": state,
        "non_adoption_cause": non_adoption_cause,
        "note": note,
        "adopted_n": adopted_n,
        "instrument_version": "11-i-a-contract",
        "corpus_content_digest": corpus_content_digest_value,
        "embedding_schema_fingerprint": "f" * 64,
        "trigger": "manual",
    }


# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture()
async def floor_env() -> AsyncIterator[SurrealEnv]:
    """A fresh throwaway database on the TEST store (spike-surreal, :18000)."""
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    try:
        yield env
    finally:
        await drop_database(env)


@pytest_asyncio.fixture()
async def floor_store(floor_env: SurrealEnv) -> AsyncIterator[FloorCalibrationStore]:
    store = await _new_floor_store(floor_env)
    try:
        yield store
    finally:
        await store.close()


async def _new_floor_store(env: SurrealEnv) -> FloorCalibrationStore:
    """An INDEPENDENT ledger (its own connection) on the same database."""
    store = FloorCalibrationStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    await store.ensure_ready()
    return store


@pytest_asyncio.fixture()
async def chunk_store(floor_env: SurrealEnv) -> AsyncIterator[SurrealStore]:
    """A ready ``SurrealStore`` with the chunk schema applied, for the C8 pins."""
    store = SurrealStore(
        url=floor_env.url,
        namespace=floor_env.namespace,
        database=floor_env.database,
        user=floor_env.user,
        password=floor_env.password,
        dim=floor_env.dim,
    )
    await store.ensure_ready()
    try:
        yield store
    finally:
        await store.close()


async def _seed_chunks(store: SurrealStore, count: int, *, dim: int, tier: str = "lore") -> None:
    records = [
        (
            chunk_record(
                tier=tier,
                file_path=f"pkg/module_{index}.py",
                identity=f"Thing.method_{index}",
                source_text=f"def method_{index}():\n    return {index}\n",
            ),
            unit_vector(index % dim, dim),
        )
        for index in range(count)
    ]
    await store.upsert(records)




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


async def _lease_store(env: SurrealEnv) -> Any:
    """A ready lease store on the same database (its own connection)."""
    from loremaster.store.lease import SurrealLeaseStore  # noqa: PLC0415

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
# 1. THE SEAM ITSELF.
# =============================================================================


class TestTheLedgerIsAConventionalSeam:
    """B5 / R2.2's coverage obligation: a conventional ``_query``-owning ledger
    shape gets the retry-seam mutation proofs FREE; a bespoke shape has to be
    hand-added to the observed-coverage drive list, and the one that was not is
    finding #120.
    """

    def test_the_ledger_is_discovered_by_the_shared_seam_enumerator(self) -> None:
        from test_retry_seam import _discover_query_seams  # noqa: PLC0415

        assert "FloorCalibrationStore" in {
            seam.__name__ for _, seam in _discover_query_seams()
        }

    def test_the_ledger_constructs_from_the_shared_ctor_values(self) -> None:
        from test_retry_seam import _construct  # noqa: PLC0415

        assert _construct(FloorCalibrationStore) is not None

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

        assert "FloorCalibrationStore" in {name for _, name in _discover_socket_owners()}, (
            "FloorCalibrationStore is not in the socket-owner enumeration — its "
            "`_ensure_connection` must construct its own connection under a "
            "double-checked lock, like every other owner in the package"
        )

    async def test_ensure_ready_twice_does_not_raise(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        await floor_store.ensure_ready()
        await floor_store.ensure_ready()

    async def test_close_tolerates_a_NEVER_CONNECTED_ledger(
        self, floor_env: SurrealEnv
    ) -> None:
        """Promised in the stub's docstring and pinned by nothing (adversary
        residual 9). A build that raised here would surface only as teardown
        noise attributed to whichever test happened to run last — the hardest
        kind of failure to attribute."""
        store = FloorCalibrationStore(
            url=floor_env.url,
            namespace=floor_env.namespace,
            database=floor_env.database,
            user=floor_env.user,
            password=floor_env.password,
        )
        await store.close()  # never connected — must not raise
        await store.close()  # and twice


class TestNoPrivateRetryPolicyLivesInThisPackage:
    """#102/#120 + F8-C6. Keyed on the SAFE set, never on a forbidden name list."""

    @staticmethod
    def _source() -> str:
        from pathlib import Path  # noqa: PLC0415

        import loremaster.floor_calibration.store as module  # noqa: PLC0415

        return Path(module.__file__).read_text(encoding="utf-8")

    def test_the_engine_conflict_marker_appears_nowhere(self) -> None:
        assert "can be retried" not in self._source(), (
            "classification belongs to `_txn.is_retryable_conflict_error`; a local "
            "match is a private copy wearing the shared name, and a reworded engine "
            "message silently stops every such copy retrying"
        )

    def test_no_private_sleep_ladder(self) -> None:
        assert not self._sleep_calls(self._source())

    def test_the_sleep_scan_can_actually_see_a_sleep(self) -> None:
        """CONTROL. An AST walk that matched nothing would make the pin above
        green against a module full of private backoff."""
        assert len(self._sleep_calls("import asyncio\nasync def f():\n    await asyncio.sleep(1)\n")) == 1

    @staticmethod
    def _sleep_calls(source: str) -> list[object]:
        import ast  # noqa: PLC0415

        return [
            node
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "sleep"
        ]


# =============================================================================
# 2. APPEND-ONLY ROWS + THE HEAD POINTER.
# =============================================================================


class TestTheHeadIsAddressedByHeadIdentity:
    """F6: ONE identity function, and the store must USE it rather than mint an
    id of its own. Proven by MUTATION across the module boundary — the only
    test that distinguishes sharing from looks-like-sharing.
    """

    async def test_the_head_id_is_exactly_head_identity_of_the_axes(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        receipt = await floor_store.record_measurement(
            axes=POOLED, measurement=_measurement(state="measured"), adopt=True
        )
        assert receipt.head_identity == head_identity(POOLED)

    async def test_perturbing_head_identity_moves_the_stores_head_id(
        self, floor_store: FloorCalibrationStore, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PROVE SHARING BY MUTATION. If the store computes its own id — even by
        the same recipe — this pin stays green nowhere and the ONE-IMPLEMENTATION
        claim is false.
        """
        sentinel = "e" * 128
        monkeypatch.setattr(floor_domain, "head_identity", lambda axes: sentinel)
        receipt = await floor_store.record_measurement(
            axes=POOLED, measurement=_measurement(state="measured"), adopt=True
        )
        assert receipt.head_identity == sentinel, (
            "the ledger did not route through floor_calibration.domain.head_identity — "
            "a second implementation of the head id is a record-identity migration "
            "waiting to happen (F6)"
        )


class TestRowsAreAppendOnly:
    """B4: rows are append-only MEASUREMENTS; history carries the F6 tuning data."""

    async def test_a_second_measurement_does_not_overwrite_the_first(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        first = await floor_store.record_measurement(
            axes=POOLED, measurement=_measurement(state="measured", floor=0.40), adopt=True
        )
        second = await floor_store.record_measurement(
            axes=POOLED, measurement=_measurement(state="measured", floor=0.55), adopt=True
        )
        assert first.measurement_id != second.measurement_id
        history = await floor_store.measurement_history(POOLED, limit=10)
        assert len(history) == 2
        assert {round(float(row["floor"]), 2) for row in history} == {0.40, 0.55}

    async def test_history_honours_a_limit_BELOW_the_row_count(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        """⚠ M6 — PARAMETER-VALUE MONOCULTURE, measured. EVERY other
        ``measurement_history`` call in this contract passes a ``limit`` GREATER
        than the row count (``limit=10`` over ≤2 rows; ``limit=expected+10``), so
        a build that IGNORES ``limit`` entirely passed at 143 / 0. The code
        branches on ``limit``; at least one pin must use a value that
        discriminates.
        """
        for index in range(4):
            await floor_store.record_measurement(
                axes=POOLED,
                measurement=_measurement(state="measured", floor=0.40 + index / 100),
                adopt=True,
            )
        assert len(await floor_store.measurement_history(POOLED, limit=2)) == 2

    async def test_history_is_NEWEST_FIRST(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        """⚠ M6, second half. The order was unpinned, so an ASCENDING build
        passed — and combined with a working ``limit`` that hands 11-i-b's F6
        tuning read the OLDEST rows while calling them the latest history.
        """
        for index in range(3):
            await floor_store.record_measurement(
                axes=POOLED,
                measurement=_measurement(state="measured", floor=0.40 + index / 100),
                adopt=True,
            )
        floors = [round(float(row["floor"]), 2) for row in
                  await floor_store.measurement_history(POOLED, limit=3)]
        assert floors == [0.42, 0.41, 0.40], f"history is not newest-first: {floors}"

    async def test_history_is_scoped_to_its_OWN_head(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        """A build keying history on the TABLE rather than the head passes every
        single-head pin and mixes a tier's history into the pooled one."""
        await floor_store.record_measurement(
            axes=POOLED, measurement=_measurement(state="measured"), adopt=True
        )
        await floor_store.record_measurement(
            axes=TIER_SCOPED, measurement=_measurement(state="measured"), adopt=True
        )
        assert len(await floor_store.measurement_history(POOLED, limit=10)) == 1
        assert len(await floor_store.measurement_history(TIER_SCOPED, limit=10)) == 1


class TestTheRowPersistsTheFieldsTheDesignNAMES:
    """⚠ M9 — a payload key that reaches no column is silently dropped, and the
    lead's E4 ruling asserted ``adopted_n`` was "already pinned". It was not:
    it appeared only as a fixture kwarg, so a build that strips it before the
    write passed the whole contract at 143 / 0.

    F4.3 is explicit that the row records the **ACTUAL** adopted subsample size,
    never a nominal rung — which is exactly the number a dropped column loses.
    """

    async def test_adopted_n_round_trips(self, floor_store: FloorCalibrationStore) -> None:
        await floor_store.record_measurement(
            axes=POOLED,
            measurement=_measurement(state="measured", adopted_n=137),
            adopt=True,
        )
        row = (await floor_store.measurement_history(POOLED, limit=1))[0]
        assert int(row["adopted_n"]) == 137, (
            "adopted_n did not survive the write — F4.3's 'the ACTUAL adopted "
            "subsample, never a nominal rung' is unrecoverable once dropped"
        )

    async def test_adopted_n_is_NOT_snapped_to_a_ladder_rung(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        """The discriminating value: 137 is not a member of ``[50,100,200,400…]``.
        A build that normalised it to the nearest rung would pass a fixture using
        200 and lose exactly the fact F4.3 exists to preserve."""
        await floor_store.record_measurement(
            axes=POOLED,
            measurement=_measurement(state="measured", adopted_n=137),
            adopt=True,
        )
        row = (await floor_store.measurement_history(POOLED, limit=1))[0]
        assert int(row["adopted_n"]) not in (50, 100, 200, 400)

    async def test_the_note_round_trips_for_a_non_measured_state(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        """E5: ``note`` is a DISTINCT field from ``non_adoption_cause`` — free
        text following §7's rule, where the cause is F5's typed enum."""
        await floor_store.record_measurement(
            axes=POOLED,
            measurement=_measurement(
                state="measured_not_adopted",
                non_adoption_cause="catch_bar_unmet",
                note="catch 0.41 below the 0.60 bar at N=200",
            ),
            adopt=False,
        )
        row = (await floor_store.measurement_history(POOLED, limit=1))[0]
        assert row["note"] == "catch 0.41 below the 0.60 bar at N=200"
        assert row["non_adoption_cause"] == "catch_bar_unmet"
        assert row["note"] != row["non_adoption_cause"]


class TestTheAdoptedHead:
    """What ``read_adopted_head`` resolves — and, more importantly, what it must NOT."""

    async def test_an_unmeasured_head_reads_None(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        """A fresh instance boots ``unmeasured``. ``None`` — never a fabricated
        zero floor, which 11-ii would serve as a real measurement."""
        assert await floor_store.read_adopted_head(POOLED) is None

    async def test_an_adopted_measurement_becomes_the_head(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        receipt = await floor_store.record_measurement(
            axes=POOLED, measurement=_measurement(state="measured"), adopt=True
        )
        head = await floor_store.read_adopted_head(POOLED)
        assert head is not None
        assert head.measurement_id == receipt.measurement_id
        assert head.head_identity == head_identity(POOLED)

    async def test_a_NON_adopted_measurement_does_NOT_move_the_head(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        """⚠ THE PIN THAT MATTERS MOST IN THIS FILE.

        A build that advances the head on EVERY measurement passes every other
        pin here — append-only history, distinct ids, revisions advancing — and
        silently serves a floor the adoption rule refused. The adopted-N rule,
        the catch bar and the whole F5 cause enum exist to make that refusal
        meaningful; a head that moves anyway erases all of it.
        """
        adopted = await floor_store.record_measurement(
            axes=POOLED, measurement=_measurement(state="measured", floor=0.50), adopt=True
        )
        await floor_store.record_measurement(
            axes=POOLED,
            measurement=_measurement(
                state="measured_not_adopted",
                floor=0.90,
                non_adoption_cause="catch_bar_unmet",
                note="catch bar unmet at the evaluated rung",
            ),
            adopt=False,
        )
        head = await floor_store.read_adopted_head(POOLED)
        assert head is not None
        assert head.measurement_id == adopted.measurement_id
        assert len(await floor_store.measurement_history(POOLED, limit=10)) == 2

    async def test_a_non_adopted_receipt_carries_no_head_revision(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        receipt = await floor_store.record_measurement(
            axes=POOLED,
            measurement=_measurement(
                state="measured_not_adopted",
                non_adoption_cause="head_retained_overlap",
                note="fresh measurement not distinguishable from the adopted head",
            ),
            adopt=False,
        )
        assert receipt.adopted is False
        assert receipt.head_revision is None

    async def test_the_head_revision_does_NOT_move_across_a_REFUSED_measurement(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        """⚠ M3 — THE ARITHMETIC PIN THAT WAS FOOLED BY ITS OWN FIXTURE (W25).

        ``test_each_adoption_advances_the_head_revision_by_exactly_one`` runs
        THREE CONSECUTIVE ADOPTIONS, so "+1 per adoption" and "+1 per
        measurement" are the same number — the arithmetic-alignment class this
        repo has now hit five times. And the non-adopted-head pin checks
        ``measurement_id`` and the history length, never ``revision``. So a build
        whose head revision advances on EVERY measurement passed the whole
        contract at 143 / 0.

        ADOPT → REFUSE → ADOPT must move the revision by exactly ONE, and the
        refusal must sit BETWEEN the two adoptions: that is the only ordering in
        which the two readings differ.
        """
        first = await floor_store.record_measurement(
            axes=POOLED, measurement=_measurement(state="measured", floor=0.40), adopt=True
        )
        await floor_store.record_measurement(
            axes=POOLED,
            measurement=_measurement(
                state="measured_not_adopted",
                floor=0.91,
                non_adoption_cause="catch_bar_unmet",
                note="refused between two adoptions — the head must not move",
            ),
            adopt=False,
        )
        second = await floor_store.record_measurement(
            axes=POOLED, measurement=_measurement(state="measured", floor=0.41), adopt=True
        )
        assert first.head_revision is not None and second.head_revision is not None
        assert second.head_revision == first.head_revision + 1, (
            f"the head revision moved by {second.head_revision - first.head_revision} across "
            f"adopt→refuse→adopt; it counts MEASUREMENTS, not ADOPTIONS"
        )
        head = await floor_store.read_adopted_head(POOLED)
        assert head is not None and head.revision == second.head_revision

    async def test_a_LONE_refused_measurement_leaves_the_head_UNMEASURED(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        """M3's companion (the adversary's P2D perturbation): with no prior
        adoption there is no head to "retain", so a build that mints one anyway
        serves a floor that was never adopted at all."""
        await floor_store.record_measurement(
            axes=POOLED,
            measurement=_measurement(
                state="measured_not_adopted",
                non_adoption_cause="stability_gate_unmet",
                note="no qualifying rung",
            ),
            adopt=False,
        )
        assert await floor_store.read_adopted_head(POOLED) is None

    async def test_each_adoption_advances_the_head_revision_by_exactly_one(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        revisions: list[int] = []
        for _ in range(3):
            receipt = await floor_store.record_measurement(
                axes=POOLED, measurement=_measurement(state="measured"), adopt=True
            )
            assert receipt.head_revision is not None, (
                "an ADOPTED measurement must report the head revision it minted — "
                "a None here makes every downstream lost-update check unable to count"
            )
            revisions.append(receipt.head_revision)
        assert revisions == [revisions[0], revisions[0] + 1, revisions[0] + 2]

    async def test_two_axis_mappings_have_INDEPENDENT_heads(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        pooled = await floor_store.record_measurement(
            axes=POOLED, measurement=_measurement(state="measured", floor=0.40), adopt=True
        )
        tiered = await floor_store.record_measurement(
            axes=TIER_SCOPED, measurement=_measurement(state="measured", floor=0.70), adopt=True
        )
        pooled_head = await floor_store.read_adopted_head(POOLED)
        tiered_head = await floor_store.read_adopted_head(TIER_SCOPED)
        assert pooled_head is not None and tiered_head is not None
        assert pooled_head.measurement_id == pooled.measurement_id
        assert tiered_head.measurement_id == tiered.measurement_id

    async def test_a_head_reads_the_same_from_an_INDEPENDENT_connection(
        self, floor_env: SurrealEnv, floor_store: FloorCalibrationStore
    ) -> None:
        """The head is STORE state, not process state (the binding architecture
        ruling). A build caching it in the instance passes every pin above."""
        receipt = await floor_store.record_measurement(
            axes=POOLED, measurement=_measurement(state="measured"), adopt=True
        )
        other = await _new_floor_store(floor_env)
        try:
            head = await other.read_adopted_head(POOLED)
            assert head is not None and head.measurement_id == receipt.measurement_id
        finally:
            await other.close()


class TestTheStateAndCauseDomainIsValidatedBeforeAnyIo:
    """F4/F5's typed-cause pin, at the ledger — the store ASSERT stays the
    backstop for any non-ledger writer (the ``_require_non_empty_area_category``
    precedent).
    """

    async def test_an_unknown_state_is_refused(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        with pytest.raises(ValueError):
            await floor_store.record_measurement(
                axes=POOLED, measurement=_measurement(state="nearly_measured"), adopt=False
            )

    async def test_an_unknown_non_adoption_cause_is_refused(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        with pytest.raises(ValueError):
            await floor_store.record_measurement(
                axes=POOLED,
                measurement=_measurement(
                    state="measured_not_adopted",
                    non_adoption_cause="floor_looked_wrong",
                    note="an unknown cause must be refused whatever the note says",
                ),
                adopt=False,
            )

    async def test_measured_not_adopted_REQUIRES_a_typed_cause(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        """F5's whole reason for existing: the render cannot serve a distinction
        the row never recorded. A causeless ``measured_not_adopted`` row is a
        state 11-ii can only describe by guessing."""
        with pytest.raises(ValueError):
            await floor_store.record_measurement(
                axes=POOLED,
                measurement=_measurement(
                    state="measured_not_adopted", non_adoption_cause=None, note="no cause given"
                ),
                adopt=False,
            )

    async def test_an_ADOPTED_measured_row_must_NOT_carry_a_cause(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        """A NON-ADOPTION cause on an ADOPTED row is a contradiction — and
        11-ii's projection function maps causes to served sentences, so the
        contradiction would be rendered rather than caught."""
        with pytest.raises(ValueError):
            await floor_store.record_measurement(
                axes=POOLED,
                measurement=_measurement(
                    state="measured", non_adoption_cause="substrate_indiscriminate"
                ),
                adopt=True,
            )

    @pytest.mark.parametrize(
        "state", [state for state in EXPECTED_FLOOR_STATES if state != "measured"]
    )
    async def test_EVERY_non_measured_state_REQUIRES_a_note(
        self, floor_store: FloorCalibrationStore, state: str
    ) -> None:
        """⚠ E5's five owed pins, written ∀ over the state set rather than as a
        hand-list — so a state ADDED to the closed domain inherits the rule
        instead of quietly escaping it.

        ``note`` is FREE TEXT and is NOT ``non_adoption_cause``: §7 makes the
        note mandatory unless the state is ``measured``, while F5's typed cause
        appears only on ``measured_not_adopted``. Conflating them would force a
        bogus enum value onto every in-progress row — the same projection the
        two-degeneracy split exists to forbid.
        """
        cause = "catch_bar_unmet" if state == "measured_not_adopted" else None
        with pytest.raises(ValueError):
            await floor_store.record_measurement(
                axes=POOLED,
                measurement=_measurement(state=state, non_adoption_cause=cause, note=None),
                adopt=False,
            )

    async def test_a_measured_row_needs_NO_note(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        """The other side of §7's rule, and the reason the pin above is not just
        "every row needs a note": a build demanding one everywhere would reject
        the ONE state the engine spends its life in."""
        receipt = await floor_store.record_measurement(
            axes=POOLED, measurement=_measurement(state="measured", note=None), adopt=True
        )
        assert receipt.adopted is True

    async def test_a_refused_row_LANDS_NOTHING(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        """Validation before I/O, pinned as a state property rather than as
        "it raised": a build that wrote the row and then raised would pass the
        four pins above and corrupt the append-only history."""
        with pytest.raises(ValueError):
            await floor_store.record_measurement(
                axes=POOLED, measurement=_measurement(state="nearly_measured"), adopt=False
            )
        assert await floor_store.measurement_history(POOLED, limit=10) == []
        assert await floor_store.read_adopted_head(POOLED) is None


# =============================================================================
# 3. THE FENCE (R10.2).
# =============================================================================


class TestTheFencedCommit:
    """A lapsed or superseded holder's commit fails LOUDLY and is discarded as a
    lost race — never retried, never silently swallowed, and never confused with
    the retry driver's own exhaustion.

    ⚠ The property is pinned ∀: EVERY fate is forced by a fixture (no fence /
    fence held / fence moved / no lease ROW / no lease TABLE / a rollback under
    an intact fence / a fence that moves MID-COMMIT), and every "nothing landed"
    leg checks BOTH the history and the head, because a build that appended the
    row and refused only the head advance would pass a raise-only pin while
    corrupting the record 11-ii's exact-skip compares against.
    """

    async def test_an_UNFENCED_commit_lands(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        """The single-process lab path (R2's one-shot verb) holds no lease."""
        receipt = await floor_store.record_measurement(
            axes=POOLED, measurement=_measurement(state="measured"), adopt=True, fence=None
        )
        assert receipt.adopted is True

    async def test_a_commit_under_the_HELD_fence_lands(
        self, floor_env: SurrealEnv, floor_store: FloorCalibrationStore
    ) -> None:
        lease = await _lease_store(floor_env)
        try:
            observation = await lease.create_if_absent(
                holder_identity="pod-a", lease_duration="15", acquire_time="t", renew_time="t"
            )
            assert observation is not None
            receipt = await floor_store.record_measurement(
                axes=POOLED,
                measurement=_measurement(state="measured"),
                adopt=True,
                fence=LeaseFence(
                    holder_identity="pod-a", fence_epoch=observation.fence_epoch
                ),
            )
            assert receipt.adopted is True
        finally:
            await lease.close()

    async def test_a_commit_under_a_MOVED_fence_is_refused_and_lands_NOTHING(
        self, floor_env: SurrealEnv, floor_store: FloorCalibrationStore
    ) -> None:
        lease = await _lease_store(floor_env)
        try:
            observation = await lease.create_if_absent(
                holder_identity="pod-a", lease_duration="15", acquire_time="t", renew_time="t"
            )
            assert observation is not None
            # Another pod seizes: same row, fence advanced.
            seized = await lease.compare_and_set(
                observed_revision=observation.revision,
                holder_identity="pod-b",
                lease_duration="15",
                acquire_time="t2",
                renew_time="t2",
            )
            assert seized is not None and seized.fence_epoch != observation.fence_epoch

            with pytest.raises(FenceLostError):
                await floor_store.record_measurement(
                    axes=POOLED,
                    measurement=_measurement(state="measured"),
                    adopt=True,
                    fence=LeaseFence(
                        holder_identity="pod-a", fence_epoch=observation.fence_epoch
                    ),
                )
            assert await floor_store.measurement_history(POOLED, limit=10) == []
            assert await floor_store.read_adopted_head(POOLED) is None
        finally:
            await lease.close()

    async def test_a_commit_with_NO_lease_ROW_is_refused_when_fenced(
        self, floor_env: SurrealEnv, floor_store: FloorCalibrationStore
    ) -> None:
        """⚠ B2's FIXTURE DEFECT, fixed under ruling (b): the lease TABLE exists,
        the lease ROW does not — which is what the pin's own name claims.

        As written, this fixture gave the ledger no lease TABLE at all, and on
        SurrealDB 3.2.1 a read from an undeclared table RAISES
        (``NotFoundError: The table 'lease' does not exist``) rather than
        returning ``[]``. So E2's own rider — *"if the confirming read fails,
        re-raise the original untouched"* — CONTRADICTED this pin, and the only
        build that satisfied both had ``FloorCalibrationStore.ensure_ready()``
        silently emitting the LEASE slice: an undisclosed cross-slice coupling
        no pin required and nobody would have found later. The table-absence
        case is a real third fate and now has its own pin, below.

        A fence naming an epoch nothing holds must not be treated as "no fence
        to check": silently succeeding is how a fenced build degrades into an
        unfenced one with no diff.
        """
        lease = await _lease_store(floor_env)  # creates the TABLE, not the ROW
        try:
            assert await lease.read() is None
            with pytest.raises(FenceLostError):
                await floor_store.record_measurement(
                    axes=POOLED,
                    measurement=_measurement(state="measured"),
                    adopt=True,
                    fence=LeaseFence(holder_identity="pod-a", fence_epoch=7),
                )
            assert await floor_store.measurement_history(POOLED, limit=10) == []
            assert await floor_store.read_adopted_head(POOLED) is None
        finally:
            await lease.close()

    async def test_a_commit_whose_CONFIRMING_READ_CANNOT_COMPLETE_re_raises_untouched(
        self, floor_env: SurrealEnv, floor_store: FloorCalibrationStore
    ) -> None:
        """⚠ M5 — E2's THIRD FATE, and the rider that had no instrument.

        E2 rules that a lost fence is classified from STORE STATE (never from
        engine message text — #118 and #111 are the receipts). Its rider is the
        half that gets dropped: *"if the confirming read itself fails, re-raise
        the original error untouched — never report ``FenceLostError`` on the
        strength of a read it could not complete."* A classifier whose
        evidence-gathering step can fail silently is the same defect one level
        up.

        Forced by REMOVING the lease table after both slices are ready, so the
        confirming read raises rather than returning a row. The requirement is
        the DIRECTION: whatever surfaces, it must not be ``FenceLostError``, and
        it must not be swallowed.
        """
        lease = await _lease_store(floor_env)
        await lease.close()
        admin = await connect_admin(floor_env)
        try:
            await admin.query("REMOVE TABLE IF EXISTS lease")
        finally:
            await admin.close()

        with pytest.raises(Exception) as caught:  # noqa: B017 - the TYPE is the assertion
            await floor_store.record_measurement(
                axes=POOLED,
                measurement=_measurement(state="measured"),
                adopt=True,
                fence=LeaseFence(holder_identity="pod-a", fence_epoch=7),
            )
        assert not isinstance(caught.value, FenceLostError), (
            "a fenced commit whose confirming read CANNOT COMPLETE reported "
            "FenceLostError anyway — the classifier drew a conclusion from "
            "evidence it never obtained (E2's rider)"
        )
        assert await floor_store.measurement_history(POOLED, limit=10) == []

    @pytest.mark.parametrize(
        "payload,why",  # ASCII-only ids — see the note on the poison parametrise below
        [
            (
                {"not_a_declared_column": "x"},
                "undeclared-top-level-key"  # SCHEMAFULL tables RAISE — store ref section 1.7,
            ),
            (
                # ⚠ ``ci_low`` on purpose, NOT ``adopted_n``: the first version
                # of this leg poisoned ``adopted_n``, which M9 also asserts
                # round-trips — so a build that STRIPS payload keys reddened both
                # pins and a mutation proof's declared set had to name two
                # unrelated failures. Poisoning a column nothing else pins keeps
                # the two diagnoses independent.
                {"ci_low": "not-a-float"},
                "wrong-typed-float"  # a field-coercion rejection,
            ),
        ],
    )
    async def test_a_STORE_rejection_under_an_INTACT_fence_keeps_its_OWN_type(
        self,
        floor_env: SurrealEnv,
        floor_store: FloorCalibrationStore,
        payload: dict[str, Any],
        why: str,
    ) -> None:
        """⚠ M4 — THE PIN THAT NAMED THE DEFECT AND NEVER REACHED THE CODE.

        The previous version of this pin passed ``state="nearly_measured"``,
        which the ledger's own validator refuses BEFORE ANY I/O — so the fence
        classifier was never entered, and a build translating EVERY rollback into
        ``FenceLostError`` passed at 143 / 0 (adversary W31). Its docstring
        promised a check over the classifier; the assertion never got there. That
        is a false gate in the exact shape this repo instruments.

        Both cases here reach the STORE with the fence INTACT, and two levers
        rather than one on purpose: a build that silently strips unknown keys
        (itself a defect — it would drop caller data) still fails the coercion
        leg.
        """
        lease = await _lease_store(floor_env)
        try:
            observation = await lease.create_if_absent(
                holder_identity="pod-a", lease_duration="15", acquire_time="t", renew_time="t"
            )
            assert observation is not None
            fence = LeaseFence(holder_identity="pod-a", fence_epoch=observation.fence_epoch)
            measurement = {**_measurement(state="measured"), **payload}

            with pytest.raises(SurrealStoreError) as caught:
                await floor_store.record_measurement(
                    axes=POOLED, measurement=measurement, adopt=True, fence=fence
                )
            assert not isinstance(caught.value, FenceLostError), (
                f"a rollback caused by {why}, with the fence INTACT, was reported as a "
                f"benign lost race — every real defect on this path is now invisible"
            )
            # …and the fence really was intact throughout, so the verdict above
            # cannot be excused by a concurrent seize.
            after = await lease.read()
            assert after is not None and after.fence_epoch == observation.fence_epoch
        finally:
            await lease.close()

    async def test_a_fence_that_moves_MID_COMMIT_refuses_and_lands_NOTHING(
        self, floor_env: SurrealEnv, floor_store: FloorCalibrationStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """⚠ M1 — THE FENCE MUST BE ATOMIC, NOT A PRE-CHECK (adversary W2).

        R10.2 rules the guard is ``WHERE fence_epoch = $mine`` INSIDE the commit
        transaction. A read-then-write pre-check satisfies every outcome pin in
        this class — because those fixtures move the fence BEFORE the call — and
        it is exactly the race a fencing token exists to close: a lapsed holder
        reads the lease, sees its own epoch, and commits after another pod has
        already seized.

        **THE DISCRIMINATION, because the mechanism IS the pin.** A hook is armed
        to fire between the ledger's first and second store round-trips. Before
        seizing, it asks an INDEPENDENT connection one question: *has the
        measurement row landed yet?*

        * **Atomic build** — round-trip 1 IS the commit, so the row already
          exists when the hook looks. The commit completed while the fence was
          genuinely held, so landing is CORRECT and this pin says so.
        * **TOCTOU build** — round-trip 1 is the guard READ, so no row exists
          yet; the hook then seizes, and the unfenced write lands under a fence
          that has already moved. REFUSED.
        * **Read-then-fenced-transaction build** — the same window exists, but
          its transaction re-evaluates the guard and refuses, so it passes on
          the ``FenceLostError`` branch.

        The pin therefore admits every correct shape and no incorrect one, and
        asserts nothing about how the ledger is written.
        """
        lease = await _lease_store(floor_env)
        seizer = await _lease_store(floor_env)
        observer = await _new_floor_store(floor_env)
        try:
            observation = await lease.create_if_absent(
                holder_identity="pod-a", lease_duration="15", acquire_time="t", renew_time="t"
            )
            assert observation is not None
            fence = LeaseFence(holder_identity="pod-a", fence_epoch=observation.fence_epoch)

            row_existed_at_hook = False

            async def seize() -> None:
                nonlocal row_existed_at_hook
                row_existed_at_hook = bool(
                    await observer.measurement_history(POOLED, limit=1)
                )
                current = await seizer.read()
                assert current is not None
                await seizer.compare_and_set(
                    observed_revision=current.revision,
                    holder_identity="pod-b",
                    lease_duration="15",
                    acquire_time="t2",
                    renew_time="t2",
                )

            trips = _RoundTrips()
            connection = await floor_store._ensure_connection()
            trips.install(connection, monkeypatch, before_call_number=2, hook=seize)

            try:
                await floor_store.record_measurement(
                    axes=POOLED, measurement=_measurement(state="measured"), adopt=True,
                    fence=fence,
                )
                landed = True
            except FenceLostError:
                landed = False

            history = await observer.measurement_history(POOLED, limit=10)
            if not trips.hook_fired or row_existed_at_hook:
                # No window existed (the commit was already durable when the
                # fence moved), so the row is entitled to be there.
                assert landed and len(history) == 1
            else:
                assert not landed, (
                    "the fence moved BEFORE the ledger's write round-trip and the "
                    "commit LANDED ANYWAY — the guard is a TOCTOU pre-check, not "
                    "R10.2's in-transaction `WHERE fence_epoch = $mine`"
                )
                assert history == []
                assert await observer.read_adopted_head(POOLED) is None
        finally:
            await lease.close()
            await seizer.close()
            await observer.close()

    @pytest.mark.parametrize(
        "poison,which",  # ⚠ ASCII-ONLY ids: pytest ASCII-ESCAPES a non-ASCII
        # character in a parametrised id, so a node id typed from THIS source is
        # unmatchable and every mutation proof over it reports a spurious
        # two-way mismatch (measured — `§` became `\xa7`).
        [
            (
                "DEFINE FIELD OVERWRITE instrument_version ON floor_measurement "
                "TYPE option<string> ASSERT $value = NONE OR string::len($value) < 2",
                "the MEASUREMENT write",
            ),
            (
                "DEFINE FIELD OVERWRITE revision ON floor_head "
                "TYPE int DEFAULT 0 ASSERT $value < 1",
                "the HEAD advance",
            ),
        ],
    )
    async def test_an_adopting_commit_is_ATOMIC(
        self,
        floor_env: SurrealEnv,
        floor_store: FloorCalibrationStore,
        poison: str,
        which: str,
    ) -> None:
        """⚠ M11 — two transactions leave an ORPHAN on a crash (adversary W23b,
        which passed at 143 / 0).

        Pinned as ATOMICITY UNDER FAILURE rather than as a round-trip count,
        because a count cannot tell a legitimate trailing READ from a second
        WRITE — and both legs are needed because the two halves can be issued in
        either order: poisoning only the measurement lets a head-FIRST split
        build through, and poisoning only the head lets a measurement-first one
        through. With both, no split survives:

        * ONE transaction — whichever half is poisoned, the whole thing rolls
          back and NOTHING lands.
        * head-first split — the head advances, then the poisoned measurement
          fails, and a head now points at a measurement id that does not exist.
        * measurement-first split — the row lands with no head that references
          it: an orphan in the append-only history 11-ii's exact-skip reads.
        """
        admin = await connect_admin(floor_env)
        try:
            await admin.query(poison)
        finally:
            await admin.close()

        with pytest.raises(SurrealStoreError):
            await floor_store.record_measurement(
                axes=POOLED, measurement=_measurement(state="measured"), adopt=True
            )

        assert await floor_store.measurement_history(POOLED, limit=10) == [], (
            f"a commit whose {which} was rejected left a measurement row behind — "
            f"the CREATE and the head advance are not one transaction"
        )
        assert await floor_store.read_adopted_head(POOLED) is None, (
            f"a commit whose {which} was rejected left an adopted head behind — "
            f"the head now points at a measurement that does not exist"
        )


# =============================================================================
# 4. THE HOT-ROW HEAD MINT UNDER CONTENTION.
# =============================================================================


class TestTheHeadMintUnderContention:
    """THE HOT-ROW LAW (store reference §5): >= 8-way, on SEPARATE live
    connections, with OVERLAPPING racer lifetimes (repeated adoptions per racer
    — a start-line barrier synchronises Python, not the wire).

    ⚠ A single green run NEVER clears a concurrency test. Twenty consecutive
    greens are the BUILDER's obligation and belong in its report; this pin is
    the instrument, not the discharge. And a failing mint is a STOP — "flaky" is
    not a builder's verdict to render (the C1 mint failed ~4 runs in 5, was
    called flaky, and shipped).
    """

    @pytest.mark.parametrize("racers", [_HOT_ROW_RACERS, *_HOT_ROW_SCALE])
    async def test_no_adoption_is_lost_under_contention(
        self, floor_env: SurrealEnv, racers: int
    ) -> None:
        """The DISCRIMINATING invariant is arithmetic, not "it did not crash":
        the head's revision must equal the number of adoptions EXACTLY, and the
        history must hold exactly that many rows. A lost update leaves the
        revision LOW while every adoption still "succeeded"; a double-apply
        leaves it HIGH. Neither is visible in "the head points at something".
        """
        stores = [await _new_floor_store(floor_env) for _ in range(racers)]
        try:

            async def racer(store: FloorCalibrationStore, index: int) -> list[int]:
                revisions: list[int] = []
                for attempt in range(_ADOPTIONS_PER_RACER):
                    receipt = await store.record_measurement(
                        axes=POOLED,
                        measurement=_measurement(
                            state="measured", floor=0.40 + index / 1000 + attempt / 10000
                        ),
                        adopt=True,
                    )
                    assert receipt.head_revision is not None
                    revisions.append(receipt.head_revision)
                return revisions

            results = await asyncio.gather(
                *(racer(store, index) for index, store in enumerate(stores))
            )
            expected = racers * _ADOPTIONS_PER_RACER
            observed = [revision for batch in results for revision in batch]
            assert sorted(observed) == list(range(1, expected + 1)), (
                f"{racers}-way head mint did not produce {expected} distinct consecutive "
                f"revisions: got {sorted(observed)}"
            )

            head = await stores[0].read_adopted_head(POOLED)
            assert head is not None and head.revision == expected
            history = await stores[0].measurement_history(POOLED, limit=expected + 10)
            assert len(history) == expected
        finally:
            for store in stores:
                await store.close()

    async def test_concurrent_adoptions_on_DIFFERENT_heads_do_not_contend_wrongly(
        self, floor_env: SurrealEnv
    ) -> None:
        """Distinct axis mappings are distinct rows: a build that funnelled every
        head through ONE counter would still be "correct" here yet serialise
        every scope against every other, and F6 explicitly keeps the SINGLE-FLIGHT
        LEASE instance-global while the HEADS stay per-identity.
        """
        axis_sets = [
            {"scope": f"tier:t{index}", "statistic": "cosine_floor"}
            for index in range(_HOT_ROW_RACERS)
        ]
        stores = [await _new_floor_store(floor_env) for _ in axis_sets]
        try:
            receipts = await asyncio.gather(
                *(
                    store.record_measurement(
                        axes=axes, measurement=_measurement(state="measured"), adopt=True
                    )
                    for store, axes in zip(stores, axis_sets, strict=True)
                )
            )
            assert {receipt.head_identity for receipt in receipts} == {
                head_identity(axes) for axes in axis_sets
            }
            assert all(receipt.head_revision == 1 for receipt in receipts)
        finally:
            for store in stores:
                await store.close()


# =============================================================================
# 5. C8 — THE EXHAUSTIVE, PROVEN POOL ENUMERATION (ruled decision 8).
# =============================================================================


class TestTheCalibrationPoolIsExhaustiveAndProven:
    """C8. The inherited ``IDENTIFIER_SCROLL_LIMIT``-class cap is retired here
    because uuid record-id order makes a truncated set a QUASI-UNIFORM
    subsample: the floor stays plausible while "pool size" and the N-curve's
    "up to pool size" silently lie, and when the corpus crosses the cap between
    runs, WHICH rows survive changes — phantom drift, spurious disjoint-CI
    adoptions, and a broken determinism control, all attributed to the corpus.
    """

    async def test_an_empty_corpus_yields_an_empty_pool_not_an_error(
        self, chunk_store: SurrealStore
    ) -> None:
        pool = await chunk_store.enumerate_calibration_pool()
        assert pool.rows == ()
        assert pool.counted_total == 0

    async def test_every_chunk_is_returned(
        self, chunk_store: SurrealStore, floor_env: SurrealEnv
    ) -> None:
        await _seed_chunks(chunk_store, 25, dim=floor_env.dim)
        pool = await chunk_store.enumerate_calibration_pool()
        assert len(pool.rows) == 25
        assert pool.counted_total == 25

    async def test_the_limit_is_STRICTLY_greater_than_the_counted_total(
        self, chunk_store: SurrealStore, floor_env: SurrealEnv
    ) -> None:
        """The strictness is the whole instrument: at ``limit == count`` a full
        result is INDISTINGUISHABLE from a truncated one, so the truncation
        check below could never fire."""
        await _seed_chunks(chunk_store, 10, dim=floor_env.dim)
        pool = await chunk_store.enumerate_calibration_pool()
        assert pool.limit > pool.counted_total

    async def test_the_walk_is_in_ASCENDING_record_id_order(
        self, chunk_store: SurrealStore, floor_env: SurrealEnv
    ) -> None:
        """C10's digest is computed over THIS order; an engine-iteration order
        would make the exact-skip datum change with no corpus change at all."""
        await _seed_chunks(chunk_store, 20, dim=floor_env.dim)
        pool = await chunk_store.enumerate_calibration_pool()
        point_ids = [row["point_id"] for row in pool.rows]
        assert point_ids == sorted(point_ids)

    async def test_the_projection_is_NARROWED_and_declared(
        self, chunk_store: SurrealStore, floor_env: SurrealEnv
    ) -> None:
        await _seed_chunks(chunk_store, 3, dim=floor_env.dim)
        pool = await chunk_store.enumerate_calibration_pool()
        assert CALIBRATION_POOL_COLUMNS, "the projection constant is empty"
        for row in pool.rows:
            assert set(row) == set(CALIBRATION_POOL_COLUMNS), (
                f"row keys {sorted(row)} != declared projection "
                f"{sorted(CALIBRATION_POOL_COLUMNS)}"
            )

    async def test_the_heavy_embedding_never_crosses_the_wire(
        self, chunk_store: SurrealStore, floor_env: SurrealEnv
    ) -> None:
        """A full-corpus walk that carried a 2048-float vector per row is the
        reason "narrowed" is in the ruling at all."""
        await _seed_chunks(chunk_store, 3, dim=floor_env.dim)
        pool = await chunk_store.enumerate_calibration_pool()
        assert "embedding" not in CALIBRATION_POOL_COLUMNS
        assert all("embedding" not in row for row in pool.rows)

    async def test_the_digest_inputs_are_present_in_every_row(
        self, chunk_store: SurrealStore, floor_env: SurrealEnv
    ) -> None:
        """C10 computes from THIS walk — "no extra read" is a requirement, not a
        nicety, because a second read sees a different corpus."""
        await _seed_chunks(chunk_store, 3, dim=floor_env.dim)
        pool = await chunk_store.enumerate_calibration_pool()
        assert {"point_id", "content_hash"} <= set(CALIBRATION_POOL_COLUMNS)
        assert corpus_content_digest(pool.rows)

    async def test_a_TRUNCATED_scroll_raises_the_truncation_type(
        self, chunk_store: SurrealStore, floor_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Forced by making the COUNT lie low, which is exactly what a stale
        count or a mid-walk insertion does. ``returned == limit`` is
        ``measurement_failed`` territory (F8-C8)."""
        await _seed_chunks(chunk_store, 12, dim=floor_env.dim)

        async def undercount(tier: str | None = None) -> int:
            return 5

        monkeypatch.setattr(chunk_store, "count", undercount)
        with pytest.raises(CalibrationPoolTruncatedError):
            await chunk_store.enumerate_calibration_pool()

    async def test_a_COUNT_MISMATCH_raises_a_DIFFERENT_type(
        self, chunk_store: SurrealStore, floor_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ F8-C8's MODIFICATION, and it must not be collapsed into the pin
        above: a count/returned disagreement that did NOT hit the limit is a
        DISCARD-REQUEUE through the settled-index gate, while a real truncation
        is ``measurement_failed``. One exception type for both would make the
        engine file an incident for a corpus that merely moved.
        """
        await _seed_chunks(chunk_store, 12, dim=floor_env.dim)

        async def overcount(tier: str | None = None) -> int:
            return 40

        monkeypatch.setattr(chunk_store, "count", overcount)
        with pytest.raises(CalibrationPoolCountMismatchError):
            await chunk_store.enumerate_calibration_pool()

    async def test_the_two_refusals_are_DISTINCT_types(self) -> None:
        """Pinned directly, because "both subclass CalibrationPoolError" is
        exactly the shape a builder collapses under lint pressure."""
        truncated: type[Exception] = CalibrationPoolTruncatedError
        mismatched: type[Exception] = CalibrationPoolCountMismatchError
        assert truncated is not mismatched
        assert not issubclass(truncated, mismatched)
        assert not issubclass(mismatched, truncated)


class TestTheDigestOverARealCorpus:
    """C10 end-to-end: the datum 11-ii's exact-skip compares against."""

    async def test_an_unchanged_corpus_reproduces_its_digest(
        self, chunk_store: SurrealStore, floor_env: SurrealEnv
    ) -> None:
        """The DETERMINISM CONTROL's store half. The packet names this a
        must-prove pin; the EMBEDDER's bit-exactness is 11-i-b's leg and is
        explicitly allowed to fall back to "within-CI by construction" — this
        leg, over stored content, has no such excuse.
        """
        await _seed_chunks(chunk_store, 15, dim=floor_env.dim)
        first = corpus_content_digest((await chunk_store.enumerate_calibration_pool()).rows)
        second = corpus_content_digest((await chunk_store.enumerate_calibration_pool()).rows)
        assert first == second

    async def test_ADDING_one_chunk_changes_the_digest(
        self, chunk_store: SurrealStore, floor_env: SurrealEnv
    ) -> None:
        await _seed_chunks(chunk_store, 5, dim=floor_env.dim)
        before = corpus_content_digest((await chunk_store.enumerate_calibration_pool()).rows)
        await chunk_store.upsert(
            [
                (
                    chunk_record(
                        tier="lore",
                        file_path="pkg/extra.py",
                        identity="Extra.method",
                        source_text="def extra():\n    return 1\n",
                    ),
                    unit_vector(1, floor_env.dim),
                )
            ]
        )
        after = corpus_content_digest((await chunk_store.enumerate_calibration_pool()).rows)
        assert before != after

    async def test_EDITING_one_chunks_content_changes_the_digest(
        self, chunk_store: SurrealStore, floor_env: SurrealEnv
    ) -> None:
        """⚠ THE EDIT-BLINDNESS THE DIGEST EXISTS TO KILL — §1.3 names it the
        design's original sin. A count-based datum is IDENTICAL here."""
        record = chunk_record(
            tier="lore",
            file_path="pkg/edited.py",
            identity="Edited.method",
            source_text="def edited():\n    return 1\n",
        )
        await chunk_store.upsert([(record, unit_vector(2, floor_env.dim))])
        before_pool = await chunk_store.enumerate_calibration_pool()
        before = corpus_content_digest(before_pool.rows)

        edited = chunk_record(
            tier="lore",
            file_path="pkg/edited.py",
            identity="Edited.method",
            source_text="def edited():\n    return 2\n",  # SAME id, different content
        )
        await chunk_store.upsert([(edited, unit_vector(2, floor_env.dim))])
        after_pool = await chunk_store.enumerate_calibration_pool()

        assert after_pool.counted_total == before_pool.counted_total, (
            "the fixture must hold the COUNT fixed — otherwise a count-based "
            "datum would pass this pin too and it would prove nothing"
        )
        assert corpus_content_digest(after_pool.rows) != before


# =============================================================================
# THE DERIVATION PINS (closure wave, 2026-07-26).
#
# ``builder-11ia-1`` introduced four derivations, proved each with a MANUAL
# mutation receipt, and could not write the invariant — a builder pinning its own
# derivation is grading itself (escalation E-7). A fix without an invariant is
# half a fix, and the class WILL recur at the next column added. Derivation (a)
# (``floor_head``'s axis columns) lives in ``test_floor_calibration_schema.py``
# because it is DDL; the three below are the ledger's and the pool's statements.
#
# ⚠ THE TRAP EVERY ONE OF THESE IS BUILT AGAINST: "the emitted text moved" is
# satisfied by a build that merely INTERPOLATES the registry somewhere harmless
# while keeping a hand-typed list, and an ADD-only leg is satisfied by a build
# that appends the registry to a hardcoded one. So every pin below asserts the
# emitted structure EXACTLY, and every pin carries a REMOVE leg — with a
# hand-typed list, un-registering an entry changes nothing at all — plus an
# UNPATCHED control, so a broken parser cannot make the legs agree by accident.
#
# None of them dials: ``FloorCalibrationStore``/``SurrealStore`` constructors open
# nothing (that is itself contract, so ``test_retry_seam.py`` can construct every
# seam), and the seam that WOULD dial is monkeypatched out.
# =============================================================================

_NEVER_DIALLED_URL = "ws://127.0.0.1:1/rpc"  # port 1: a connect attempt is a loud bug
_PROBE_COLUMN = "probe_column"
_PROBE_AXIS = "probe_axis"


class _CapturedTransaction(Exception):
    """Carries a composed transaction out of a monkeypatched ``execute_transaction``.

    An exception rather than a list append: it aborts ``record_measurement``
    BEFORE the post-commit read-back, so the pin needs exactly one monkeypatch and
    cannot accidentally assert against a half-faked write path. It is deliberately
    NOT a ``SurrealStoreError`` — the ledger's own ``except`` ladder would
    otherwise swallow it into a fence verdict.
    """

    def __init__(self, statement: str, params: Mapping[str, Any]) -> None:
        super().__init__("transaction captured")
        self.statement = statement
        self.params = dict(params)


async def _capture_transaction(statement: str, params: Mapping[str, Any], **_: Any) -> None:
    raise _CapturedTransaction(statement, params)


def _offline_floor_store() -> FloorCalibrationStore:
    """A ledger wired to a port nothing listens on. Its constructor opens nothing."""
    return FloorCalibrationStore(
        url=_NEVER_DIALLED_URL,
        namespace="probe_ns",
        database="probe_db",
        user="probe_user",
        password=SecretStr("probe_pass"),
    )


def _select_list(statement: str) -> str:
    """The projection between ``SELECT`` and ``FROM`` — the list under test."""
    assert statement.count(" FROM ") == 1, f"ambiguous statement to parse: {statement!r}"
    return statement.split("SELECT ", 1)[1].split(" FROM ", 1)[0]


class TestTheHeadMintsAxisAssignmentsAreDerivedFromTheRegistry:
    """DERIVATION (b) — the head mint assigns EXACTLY the registered axes.

    Pinned on the COMPOSED TRANSACTION, not on the private statement builder, so
    the assignment and its BOUND PARAMETER are checked together: a build that
    derived the SET clause from the registry while binding params from a
    hand-typed list would emit ``$fc_axis_probe_axis`` with nothing bound to it —
    green under a statement-only pin, and a runtime error in production.
    """

    @staticmethod
    async def _captured(
        monkeypatch: pytest.MonkeyPatch,
        registry: tuple[str, ...],
        axes: Mapping[str, str],
    ) -> _CapturedTransaction:
        monkeypatch.setattr(floor_domain, "FLOOR_HEAD_ALWAYS_SERIALISED_AXES", registry)
        monkeypatch.setattr(floor_store_module, "execute_transaction", _capture_transaction)
        store = _offline_floor_store()
        with pytest.raises(_CapturedTransaction) as caught:
            await store.record_measurement(
                axes=axes, measurement=_measurement(), adopt=True
            )
        return caught.value

    @staticmethod
    def _axis_assignments(statement: str) -> dict[str, str]:
        """``{column: bound-param-suffix}`` for every axis assignment in the mint."""
        prefix = re.escape(floor_store_module._AXIS_PARAM_PREFIX)
        return {
            column: suffix
            for column, suffix in re.findall(
                rf"(\w+) = \${prefix}(\w+)", statement
            )
        }

    async def test_the_UNPATCHED_mint_assigns_exactly_the_registered_axes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The CONTROL — without it, a parser that finds nothing passes both legs."""
        registry = tuple(floor_domain.FLOOR_HEAD_ALWAYS_SERIALISED_AXES)
        captured = await self._captured(monkeypatch, registry, POOLED)
        assert self._axis_assignments(captured.statement) == {
            axis: axis for axis in registry
        }

    async def test_REGISTERING_an_axis_adds_its_assignment_AND_its_bound_param(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        registry = (*floor_domain.FLOOR_HEAD_ALWAYS_SERIALISED_AXES, _PROBE_AXIS)
        axes = {**POOLED, _PROBE_AXIS: "probe_value"}
        captured = await self._captured(monkeypatch, registry, axes)
        assert self._axis_assignments(captured.statement) == {
            axis: axis for axis in registry
        }, (
            "registering an always-serialised axis did not add its assignment to the "
            "head mint — the mint carries a hand-typed axis list, not a derivation of "
            "FLOOR_HEAD_ALWAYS_SERIALISED_AXES"
        )
        bound = f"{floor_store_module._AXIS_PARAM_PREFIX}{_PROBE_AXIS}"
        assert captured.params.get(bound) == "probe_value", (
            f"the mint references ${bound} but nothing bound it — the SET clause and "
            f"the parameter dict read from DIFFERENT lists"
        )

    async def test_UNREGISTERING_an_axis_removes_its_assignment_AND_its_param(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """THE LEG THAT DISCRIMINATES: a hardcoded list survives every ADD leg."""
        registry = floor_domain.FLOOR_HEAD_ALWAYS_SERIALISED_AXES[:1]
        dropped = floor_domain.FLOOR_HEAD_ALWAYS_SERIALISED_AXES[1:]
        assert registry and dropped, "the registry must hold >= 2 axes for this leg"
        axes = {axis: POOLED[axis] for axis in registry}
        captured = await self._captured(monkeypatch, registry, axes)
        assignments = self._axis_assignments(captured.statement)
        assert assignments == {axis: axis for axis in registry}, (
            f"un-registering {list(dropped)} left the mint's assignments unchanged "
            f"({assignments}) — they are hand-typed"
        )
        for axis in dropped:
            assert f"{floor_store_module._AXIS_PARAM_PREFIX}{axis}" not in captured.params


class TestTheHistoryProjectionIsDerivedFromTheColumnRegistry:
    """DERIVATION (c) — ``measurement_history`` projects FLOOR_MEASUREMENT_COLUMNS.

    The projection is EXPLICIT on purpose (store reference §2: ``SELECT *`` omits a
    ``NONE``-valued column entirely, so every ``option<>`` reader would take a
    ``KeyError``). That only holds if the list is DERIVED — a hand-typed twin
    silently stops projecting the next column somebody declares, and the consumer
    reads ``None`` for a column that is really populated.
    """

    @staticmethod
    async def _projection(
        monkeypatch: pytest.MonkeyPatch, columns: tuple[str, ...]
    ) -> str:
        monkeypatch.setattr(floor_store_module, "FLOOR_MEASUREMENT_COLUMNS", columns)
        store = _offline_floor_store()
        captured: list[str] = []

        async def _fake_query(statement: str, params: dict[str, Any] | None = None) -> Any:
            captured.append(statement)
            return []

        monkeypatch.setattr(store, "_query", _fake_query)
        assert await store.measurement_history(POOLED, limit=3) == []
        assert len(captured) == 1, f"expected ONE history read, got {captured}"
        return _select_list(captured[0])

    @staticmethod
    def _expected(columns: tuple[str, ...]) -> str:
        return ", ".join(("record::id(id) AS measurement_id", *columns))

    async def test_the_UNPATCHED_projection_matches_the_registry(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The CONTROL for the two legs below."""
        columns = tuple(FLOOR_MEASUREMENT_COLUMNS)
        assert await self._projection(monkeypatch, columns) == self._expected(columns)

    async def test_DECLARING_a_column_adds_it_to_the_projection(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        columns = (*FLOOR_MEASUREMENT_COLUMNS, _PROBE_COLUMN)
        assert await self._projection(monkeypatch, columns) == self._expected(columns), (
            "declaring a measurement column did not reach the history projection — it "
            "is a hand-typed twin of FLOOR_MEASUREMENT_COLUMNS, so the next column "
            "added would read None for every consumer while the store holds a value"
        )

    async def test_RETIRING_a_column_removes_it_from_the_projection(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """THE DISCRIMINATING LEG. The retired column is chosen structurally:
        ``head_identity`` is the WHERE key and ``created_at`` is the ORDER BY key,
        so dropping either would change the statement for a reason that has
        nothing to do with the projection."""
        structural = (
            FLOOR_MEASUREMENT_HEAD_IDENTITY_COLUMN,
            FLOOR_MEASUREMENT_CREATED_AT_COLUMN,
        )
        retired = next(
            column
            for column in FLOOR_MEASUREMENT_COLUMNS
            if column not in structural
        )
        columns = tuple(
            column
            for column in FLOOR_MEASUREMENT_COLUMNS
            if column != retired
        )
        projection = await self._projection(monkeypatch, columns)
        assert projection == self._expected(columns), (
            f"retiring {retired!r} left the history projection unchanged "
            f"({projection!r}) — it is hand-typed"
        )
        assert retired not in projection.split(", ")


class TestTheCalibrationPoolProjectionIsDerivedFromItsColumnRegistry:
    """DERIVATION (d) — the C8 walk projects CALIBRATION_POOL_COLUMNS.

    ``set(row) == set(CALIBRATION_POOL_COLUMNS)`` is asserted over LIVE rows
    elsewhere in this file, but that pin passes for a build whose statement and
    whose constant were BOTH hand-typed and happen to agree today — which is
    exactly the state 11-i-b walks into when it extends the constant and expects
    the read to follow. This pin is the one that makes "11-i-b extends THIS
    constant rather than issuing a second read" true rather than hoped.
    """

    @staticmethod
    def _offline_chunk_store() -> SurrealStore:
        return SurrealStore(
            url=_NEVER_DIALLED_URL,
            namespace="probe_ns",
            database="probe_db",
            dim=PRODUCTION_DIM,
            user="probe_user",
            password=SecretStr("probe_pass"),
        )

    @staticmethod
    async def _projection(
        monkeypatch: pytest.MonkeyPatch, columns: tuple[str, ...]
    ) -> str:
        monkeypatch.setattr(surreal_module, "CALIBRATION_POOL_COLUMNS", columns)
        store = TestTheCalibrationPoolProjectionIsDerivedFromItsColumnRegistry._offline_chunk_store()
        captured: list[str] = []

        async def _fake_query(statement: str, params: dict[str, Any] | None = None) -> Any:
            captured.append(statement)
            # An EMPTY corpus: the count read answers 0, so the walk's limit is 1
            # and its zero rows are neither a truncation nor a mismatch.
            return [{"count": 0}] if "count()" in statement else []

        monkeypatch.setattr(store, "_query", _fake_query)
        pool = await store.enumerate_calibration_pool()
        assert pool.counted_total == 0 and pool.rows == ()
        assert len(captured) == 2, f"expected a count read then a walk, got {captured}"
        return _select_list(captured[1])

    @staticmethod
    def _expected(columns: tuple[str, ...]) -> str:
        """The walk's projection, RESTATED independently of the production helper.

        ``record::id(id) AS point_id`` is spelled out here rather than read off
        ``surreal``'s own private constants on purpose: an expectation derived from
        the same source as the code under test agrees with it by construction and
        can never catch a change to it.
        """
        return ", ".join(
            "record::id(id) AS point_id" if column == "point_id" else column
            for column in columns
        )

    async def test_the_UNPATCHED_projection_matches_the_registry(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The CONTROL for the two legs below."""
        columns = tuple(surreal_module.CALIBRATION_POOL_COLUMNS)
        assert await self._projection(monkeypatch, columns) == self._expected(columns)

    async def test_DECLARING_a_pool_column_adds_it_to_the_walk(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        columns = (*surreal_module.CALIBRATION_POOL_COLUMNS, _PROBE_COLUMN)
        assert await self._projection(monkeypatch, columns) == self._expected(columns), (
            "extending CALIBRATION_POOL_COLUMNS did not extend the C8 walk's "
            "projection — 11-i-b's probe-derivation columns would be declared and "
            "never read"
        )

    async def test_RETIRING_a_pool_column_removes_it_from_the_walk(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """THE DISCRIMINATING LEG. ``point_id`` is kept because it is the walk's
        ORDER BY key (a column ordered by but not projected is a PARSE ERROR on
        3.2.1 — store reference §7), so retiring it would move the statement for a
        reason unrelated to the projection."""
        order_column = surreal_module._CALIBRATION_POOL_ORDER_COLUMN
        kept = (order_column,)
        retired = [
            column
            for column in surreal_module.CALIBRATION_POOL_COLUMNS
            if column != order_column
        ]
        assert retired, "the pool registry must hold more than its order column"
        projection = await self._projection(monkeypatch, kept)
        assert projection == self._expected(kept), (
            f"retiring {retired} left the C8 walk's projection unchanged "
            f"({projection!r}) — it is hand-typed"
        )
        for column in retired:
            assert column not in projection.split(", ")
