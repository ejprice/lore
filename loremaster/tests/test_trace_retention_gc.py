"""RED contract for the trace-retention GC (finding #193, ruling DD-1.c).

Ruling: ``docs/plans/v2/03b-deferred-design-rulings.md`` §DD-1.c. Store law cited
inline, never re-transcribed: ``docs/reference/surrealdb-31-capabilities.md`` §2
(the ``ts < $cutoff`` range predicate is an IndexScan; ``string::starts_with`` is
a TableScan), §1.1 (the trace_ts INDEX ships ``IF NOT EXISTS``), §1.4 (a
long-lived store is a dirty store — every test mints a virgin DB, so a boot-purge
defect can only be seen by seeding rows BEFORE the boot under test).

WHAT THE BUILD MUST DO (DD-1.c), and where each pin lives:

  1. The window bound is LOAD-BEARING (∀): every row with ``ts < cutoff`` is
     deleted, every row with ``ts >= cutoff`` survives, the boundary row
     (``ts == cutoff``) survives (``<`` is strict).  -> TestPurgeRespectsTheWindow
  2. NEVER in boot: ``ensure_ready`` deletes no trace row; the purge is the
     reconcile tick's job.  -> TestBootNeverPurges (here) + the reconcile-wiring
     class in ``test_reconcile.py`` (``TestReconcilePurgesTraceRetention``).
  3. Rides ``trace_ts``: an EXPLAIN receipt on the real store proving the
     ``ts < $cutoff`` scan the batching SELECT issues is an IndexScan on
     ``trace_ts``, with a TableScan positive control.  -> TestPurgeRidesTraceTsIndex
  4. Config validator: ``trace_retention_days >= aggregate_window_days``
     (cross-field), default 90 >= 14.  -> TestTraceRetentionConfigValidator
  5. Batched: a first activation over N >> batch rows drains them ALL (no silent
     cap leaving a residual behind).  -> TestBatchedDrainLeavesNoResidual

THE INTERFACE THIS CONTRACT PINS (a contract-author design choice — the
alternatives, and one escalation on WHERE the purge runs, are in
``REPORT-contract-tracegc-06b.md``):

    # loremaster.store.surreal.SurrealStore
    async def purge_traces_before(self, *, cutoff: datetime,
                                  batch_size: int = ...) -> int
        # id-batched delete loop (DELETE ... LIMIT is a PARSE ERROR on 3.2.4 —
        # probe receipt in the report); returns the total rows deleted.

    # loremaster.config.TelemetryConfig
    trace_retention_days: PositiveInt = 90   # DEFAULT_TRACE_RETENTION_DAYS
    # + a model_validator(mode="after") asserting retention >= aggregate window.

Symbols the build must add (``trace_retention_days``, ``purge_traces_before``)
are referenced INSIDE test bodies, never at module import, so this file COLLECTS
on HEAD and each pin fails INDIVIDUALLY (a clean per-node RED set) rather than as
one collection error.

Live-store tests run against spike-surreal ``ws://127.0.0.1:18000`` ONLY (the
``_surreal_harness`` default; NEVER production ``:18500``), each on a throwaway
``unique_database()``. Run with ``-n auto``.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from _surreal_harness import (
    SurrealConnection,
    SurrealEnv,
    connect_admin,
    run,
    surreal_env,  # noqa: F401 - re-exported pytest fixture
)
from loremaster.config import TelemetryConfig
from loremaster.store.surreal import _TRACE_PURGE_ID_SELECT, SurrealStore
from loremaster.store.surreal_schema import (
    TRACE_TABLE,
    TRACE_TS_FIELD,
)
from pydantic import ValidationError

# The ruled starting value (DD-1.c) and the DD-1.b default window this contract
# pins the cross-field invariant against. Literals, not imports: a HEAD run must
# still COLLECT this module, and DEFAULT_TRACE_RETENTION_DAYS does not exist yet.
_EXPECTED_DEFAULT_RETENTION_DAYS = 90
_DEFAULT_AGGREGATE_WINDOW_DAYS = 14


# --------------------------------------------------------------------------- #
# Live-store scaffolding
# --------------------------------------------------------------------------- #
@pytest_asyncio.fixture()
async def gc_store(surreal_env: SurrealEnv) -> AsyncIterator[SurrealStore]:  # noqa: F811
    """A ready :class:`SurrealStore` on a fresh unique DB (mirrors test_surreal_store)."""
    live_store = SurrealStore(
        url=surreal_env.url,
        namespace=surreal_env.namespace,
        database=surreal_env.database,
        dim=surreal_env.dim,
        user=surreal_env.user,
        password=surreal_env.password,
    )
    await live_store.ensure_ready()
    try:
        yield live_store
    finally:
        await live_store.close()


async def _seed_trace(conn: SurrealConnection, *, ts: datetime, tool: str = "probe") -> None:
    """Write ONE trace row with an EXPLICIT ``ts`` (the schema's DEFAULT is overridable).

    ``ts`` is ``datetime DEFAULT time::now()`` with no READONLY/ASSERT
    (``surreal_schema._TRACE_FIELD_SPECS``), so a supplied value lands verbatim —
    the only way to place a row on a chosen side of a cutoff, since
    :meth:`SurrealStore.record_trace` always server-stamps ``ts`` to now.
    """
    await run(
        conn,
        f"CREATE {TRACE_TABLE} CONTENT "
        "{ tool: $tool, params_hash: $ph, latency_ms: $latency, ts: $ts }",
        {"tool": tool, "ph": "deadbeef", "latency": 1.0, "ts": ts},
    )


async def _remaining_ts(conn: SurrealConnection) -> set[datetime]:
    """The ``ts`` of every surviving trace row, as a set (order-independent)."""
    rows = await run(conn, f"SELECT VALUE {TRACE_TS_FIELD} FROM {TRACE_TABLE}")
    return set(rows)


async def _count_before(conn: SurrealConnection, cutoff: datetime) -> int:
    """How many rows still carry ``ts < cutoff`` — the residual the drain must reach 0."""
    result = await run(
        conn,
        f"SELECT count() AS n FROM {TRACE_TABLE} WHERE {TRACE_TS_FIELD} < $c GROUP ALL",
        {"c": cutoff},
    )
    return int(result[0]["n"]) if result else 0


# --------------------------------------------------------------------------- #
# Pin 4 — the cross-field config validator (pure, no store)
# --------------------------------------------------------------------------- #
class TestTraceRetentionConfigValidator:
    """``trace_retention_days`` exists, defaults to 90, and must be >= the window.

    Mutation-provable BOTH directions: below-window rejects, at/above validates.
    The reject case asserts the message names BOTH fields, so on HEAD (where the
    field does not exist and pydantic raises 'extra inputs not permitted' naming
    only ``trace_retention_days``) the pin is RED for the RIGHT reason rather than
    passing on the wrong error.
    """

    def test_default_retention_is_90_and_covers_the_default_window(self) -> None:
        config = TelemetryConfig()
        assert config.trace_retention_days == _EXPECTED_DEFAULT_RETENTION_DAYS
        assert config.aggregate_window_days == _DEFAULT_AGGREGATE_WINDOW_DAYS
        assert config.trace_retention_days >= config.aggregate_window_days

    def test_retention_equal_to_window_validates(self) -> None:
        # >= is inclusive: retention == window is legal (the window's data is
        # retained exactly, never longer than needed).
        config = TelemetryConfig(trace_retention_days=14, aggregate_window_days=14)
        assert config.trace_retention_days == 14

    def test_retention_above_window_validates(self) -> None:
        config = TelemetryConfig(trace_retention_days=90, aggregate_window_days=30)
        assert config.trace_retention_days == 90

    def test_retention_below_window_is_rejected_naming_both_fields(self) -> None:
        with pytest.raises(ValidationError) as excinfo:
            TelemetryConfig(trace_retention_days=5, aggregate_window_days=14)
        message = str(excinfo.value).lower()
        # The invariant, taught: the served aggregate window can never outlive its
        # retained data. The error must name both fields so it is actionable AND so
        # this pin cannot pass on HEAD's unrelated extra-field rejection.
        assert "trace_retention_days" in message
        assert "aggregate_window_days" in message


# --------------------------------------------------------------------------- #
# Pin 1 — the window bound is LOAD-BEARING (∀ over a SET straddling the cutoff)
# --------------------------------------------------------------------------- #
class TestPurgeRespectsTheWindow:
    """Every out-of-window row gone, every in-window row kept, boundary survives.

    Pinned over a SET with rows on BOTH sides of an EXPLICIT cutoff (the quantifier
    law: a ∀ property forced by a fixture, never asserted where the branch cannot
    fire). Discriminates every plausible wrong build: delete-all (recent gone),
    delete-none (old remain), ``<=`` for ``<`` (the boundary row wrongly deleted),
    window-ignored (deletes by some other criterion).
    """

    async def test_purge_deletes_strictly_older_and_keeps_the_rest(
        self, gc_store: SurrealStore, surreal_env: SurrealEnv  # noqa: F811
    ) -> None:
        conn = await connect_admin(surreal_env)
        try:
            cutoff = datetime(2026, 6, 1, tzinfo=UTC)
            older = {cutoff - timedelta(days=2), cutoff - timedelta(seconds=1)}
            at_or_after = {
                cutoff,  # exactly at the cutoff -> survives (strict <)
                cutoff + timedelta(seconds=1),
                cutoff + timedelta(days=2),
            }
            for ts in older | at_or_after:
                await _seed_trace(conn, ts=ts)

            deleted = await gc_store.purge_traces_before(cutoff=cutoff, batch_size=100)

            assert deleted == len(older)
            assert await _remaining_ts(conn) == at_or_after
        finally:
            await conn.close()


# --------------------------------------------------------------------------- #
# Pin 5 — batched, no silent cap: a first activation drains the WHOLE backlog
# --------------------------------------------------------------------------- #
class TestBatchedDrainLeavesNoResidual:
    """N >> batch old rows are ALL deleted across the internal batches; residual 0.

    The silent-truncation defect (delete one ``LIMIT`` batch and stop, reading as
    'covered everything') leaves a residual and under-counts the return — both RED.
    """

    async def test_first_activation_over_many_batches_drains_everything(
        self, gc_store: SurrealStore, surreal_env: SurrealEnv  # noqa: F811
    ) -> None:
        conn = await connect_admin(surreal_env)
        try:
            cutoff = datetime(2026, 6, 1, tzinfo=UTC)
            old_count = 25
            for day in range(1, old_count + 1):
                await _seed_trace(conn, ts=cutoff - timedelta(days=day), tool=f"old{day}")
            recent = {cutoff + timedelta(days=1), cutoff + timedelta(days=2), cutoff + timedelta(days=3)}
            for ts in recent:
                await _seed_trace(conn, ts=ts, tool="recent")

            # batch_size << old_count forces multiple internal batches (25 -> 10/10/5).
            deleted = await gc_store.purge_traces_before(cutoff=cutoff, batch_size=10)

            assert deleted == old_count
            assert await _count_before(conn, cutoff) == 0  # residual fully drained
            assert await _remaining_ts(conn) == recent  # in-window rows untouched
        finally:
            await conn.close()


# --------------------------------------------------------------------------- #
# Pin 2a — the boot path (ensure_ready) purges NOTHING
# --------------------------------------------------------------------------- #
class TestBootNeverPurges:
    """``ensure_ready`` is DDL-only: a re-boot over a DIRTY store deletes no row.

    Store law §1.4/§1.6: a long-lived deployment is a dirty store, and every test
    mints a virgin DB — so this seeds old+recent rows AFTER the first ensure_ready,
    then re-boots and asserts EVERY row survives. A wrong build that purges inside
    ``ensure_ready`` deletes the old rows -> RED. Paired with the reconcile-wiring
    class (which proves the purge DOES run on the reconcile tick), this is DD-1.c's
    'the reconcile tick, NEVER boot'.
    """

    async def test_re_ensure_ready_deletes_no_trace_rows(
        self, gc_store: SurrealStore, surreal_env: SurrealEnv  # noqa: F811
    ) -> None:
        conn = await connect_admin(surreal_env)
        try:
            far_past = datetime(2000, 1, 1, tzinfo=UTC)  # older than ANY plausible retention
            recent = datetime(2026, 6, 1, tzinfo=UTC)
            seeded = {far_past, recent}
            for ts in seeded:
                await _seed_trace(conn, ts=ts)

            # Re-boot the SAME store over the now-dirty database.
            await gc_store.ensure_ready()

            assert await _remaining_ts(conn) == seeded
        finally:
            await conn.close()


# --------------------------------------------------------------------------- #
# Pin 3 — EXPLAIN receipt: the ts<cutoff scan rides trace_ts (with a control)
# --------------------------------------------------------------------------- #
class TestPurgeRidesTraceTsIndex:
    """The purge's ACTUAL row-finding SELECT rides the ``trace_ts`` index.

    R1 tightening (adversary residual R1, lead-ruled): this EXPLAINs the store's
    OWN ``_TRACE_PURGE_ID_SELECT`` — the exact ``SELECT VALUE id FROM trace WHERE
    ts < $cutoff LIMIT n`` the id-batched drain issues — not a decoupled hand-written
    ``SELECT *`` proxy. The template is imported from the store, so a drain that
    changed its predicate off the index would redden this receipt (INSTRUMENT-0:
    observe the effect of the actual code, never a proxy). GREEN on HEAD too (the
    DD-1.a index already exists); it is the store-property RECEIPT DD-1.b/#193
    require. The ``tool`` predicate (no index) is the positive control proving the
    EXPLAIN reader discriminates rather than always reporting IndexScan.

    The purge's DELETE is ``DELETE ... WHERE id IN $ids`` — bounded by PRIMARY id,
    not the ts index — so it is deliberately NOT asserted here: DD-1.c requirement 3
    ("rides ``trace_ts``") is a property of the row-FINDING scan, and that is this
    SELECT. (The prior receipt EXPLAINed a hand-written ``DELETE ... WHERE ts < $c``
    the id-batched drain never issues — removed as a proxy for a nonexistent query.)
    """

    async def test_purge_id_select_is_an_index_scan_on_trace_ts(
        self, gc_store: SurrealStore, surreal_env: SurrealEnv  # noqa: F811
    ) -> None:
        conn = await connect_admin(surreal_env)
        try:
            cutoff = datetime(2026, 6, 1, tzinfo=UTC)
            await _seed_trace(conn, ts=cutoff - timedelta(days=1))

            # EXPLAIN the store's OWN batching SELECT (its exact template + $cutoff
            # param name), so this receipt tracks the purge's real query.
            purge_select_plan = json.dumps(
                await run(
                    conn,
                    _TRACE_PURGE_ID_SELECT.format(limit=100) + " EXPLAIN",
                    {"cutoff": cutoff},
                ),
                default=str,
            )
            index_name = f"{TRACE_TABLE}_ts"

            assert "IndexScan" in purge_select_plan
            assert index_name in purge_select_plan

            # Positive control: a predicate on an UNINDEXED field TableScans, so the
            # reader above is not just always seeing an IndexScan.
            control_plan = json.dumps(
                await run(
                    conn,
                    f"SELECT * FROM {TRACE_TABLE} WHERE tool = $t EXPLAIN",
                    {"t": "probe"},
                ),
                default=str,
            )
            assert "TableScan" in control_plan
        finally:
            await conn.close()
