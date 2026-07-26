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
from loremaster.floor_calibration.domain import corpus_content_digest, head_identity
from loremaster.floor_calibration.store import (
    FenceLostError,
    FloorCalibrationStore,
    LeaseFence,
)
from loremaster.store.surreal import (
    CALIBRATION_POOL_COLUMNS,
    CalibrationPoolCountMismatchError,
    CalibrationPoolTruncatedError,
    SurrealStore,
)

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
    corpus_content_digest_value: str = "0" * 128,
    adopted_n: int = 200,
) -> dict[str, Any]:
    """A measurement payload.

    ⚠ ``state`` HAS NO DEFAULT-BY-ACCIDENT: it defaults to ``measured`` and
    every pin that cares passes its own value explicitly. Repo law — a fixture
    factory must not default a parameter the code BRANCHES on, because that is
    exactly how a render suite came to test only the one value for which its
    prose was true. ``non_adoption_cause`` has NO default value that is ever
    silently correct: ``None`` is meaningful (adopted) and each caller says so.
    """
    return {
        "floor": floor,
        "ci_low": floor - 0.01,
        "ci_high": floor + 0.01,
        "state": state,
        "non_adoption_cause": non_adoption_cause,
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

    async def test_ensure_ready_twice_does_not_raise(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        await floor_store.ensure_ready()
        await floor_store.ensure_ready()


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
                state="measured_not_adopted", non_adoption_cause="head_retained_overlap"
            ),
            adopt=False,
        )
        assert receipt.adopted is False
        assert receipt.head_revision is None

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
                    state="measured_not_adopted", non_adoption_cause="floor_looked_wrong"
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
                measurement=_measurement(state="measured_not_adopted", non_adoption_cause=None),
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

    ⚠ The property is pinned ∀: EVERY fate is forced by a fixture (fence held /
    fence moved / no fence at all), and the "nothing landed" leg checks BOTH the
    history and the head, because a build that appended the row and refused only
    the head advance would pass a raise-only pin while corrupting the record
    11-ii's exact-skip compares against.
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
        from loremaster.store.lease import SurrealLeaseStore  # noqa: PLC0415

        lease = SurrealLeaseStore(
            url=floor_env.url,
            namespace=floor_env.namespace,
            database=floor_env.database,
            user=floor_env.user,
            password=floor_env.password,
        )
        await lease.ensure_ready()
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
        from loremaster.store.lease import SurrealLeaseStore  # noqa: PLC0415

        lease = SurrealLeaseStore(
            url=floor_env.url,
            namespace=floor_env.namespace,
            database=floor_env.database,
            user=floor_env.user,
            password=floor_env.password,
        )
        await lease.ensure_ready()
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

    async def test_a_commit_with_NO_lease_row_at_all_is_refused_when_fenced(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        """A fence naming an epoch nothing holds must not be treated as "no
        fence to check". Silently succeeding here is how a fenced build degrades
        into an unfenced one without any diff."""
        with pytest.raises(FenceLostError):
            await floor_store.record_measurement(
                axes=POOLED,
                measurement=_measurement(state="measured"),
                adopt=True,
                fence=LeaseFence(holder_identity="pod-a", fence_epoch=7),
            )

    async def test_a_NON_fence_failure_keeps_its_OWN_type(
        self, floor_store: FloorCalibrationStore
    ) -> None:
        """The other direction, and the reason ``FenceLostError`` must be
        established from STORE STATE rather than from an engine message: a
        domain rejection under an INTACT fence must surface as itself, or every
        real defect on this path gets reported as a benign lost race.
        """
        with pytest.raises(ValueError):
            await floor_store.record_measurement(
                axes=POOLED,
                measurement=_measurement(state="nearly_measured"),
                adopt=True,
                fence=None,
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
