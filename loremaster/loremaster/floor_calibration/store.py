"""The floor-calibration ledger (packet 11-i-a).

The names and signatures were FROZEN by the contract author (`contract-11ia-1`)
and are the interface packet 11-i-b cites; the bodies were built by
`builder-11ia-1` against that contract.

⚠ **THE SHAPE IS NOT A STYLE CHOICE.** This class owns ``_ensure_connection`` /
``_query`` / ``_drop_connection`` / ``close`` with the CONVENTIONAL ledger
signatures because ``tests/test_retry_seam.py`` discovers every class in the
package owning an ``async def _query`` and drives it against the real engine
under the runtime SDK guard. A bespoke seam shape falls OUT of that
enumeration and has to be hand-added to the observed-coverage drive list —
which is finding #120 with a fresh coat of paint (R2.2's coverage obligation).
``_query`` MUST delegate to ``store._txn.run_query`` and multi-statement work
MUST go through ``store._txn.execute_transaction``: no private retry, no
private backoff, no private jitter, and NO MATCH ON ENGINE MESSAGE TEXT
anywhere in this package (F8-C6).

Design of record: `docs/design/2026-07-24-floor-calibration.md` §7 + B4/B5 ·
Addendum F F4/F5/F6 · Addendum F-r2 R10.2 (the fence).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import SecretStr
from surrealdb import AsyncSurreal, RecordID

from loremaster.floor_calibration import domain as floor_domain
from loremaster.store._txn import (
    _CONNECTION_ERRORS,
    SurrealConnectionError,
    SurrealStoreError,
    TxnContentionExhaustedError,
    TxnFragment,
    _SurrealConnection,
    bootstrap_session,
    compose,
    execute_transaction,
    run_query,
    signin_credentials,
)
from loremaster.store.surreal_schema import (
    FLOOR_HEAD_ADOPTED_AT_COLUMN,
    FLOOR_HEAD_AXES_COLUMN,
    FLOOR_HEAD_MEASUREMENT_COLUMN,
    FLOOR_HEAD_REVISION_COLUMN,
    FLOOR_HEAD_TABLE,
    FLOOR_MEASUREMENT_COLUMNS,
    FLOOR_MEASUREMENT_CREATED_AT_COLUMN,
    FLOOR_MEASUREMENT_HEAD_IDENTITY_COLUMN,
    FLOOR_MEASUREMENT_HEAD_REVISION_COLUMN,
    FLOOR_MEASUREMENT_TABLE,
    FLOOR_NON_ADOPTION_CAUSES,
    FLOOR_STATES,
    LEASE_FENCE_EPOCH_COLUMN,
    LEASE_HOLDER_IDENTITY_COLUMN,
    LEASE_SINGLETON_ID,
    LEASE_TABLE,
    generate_floor_calibration_ddl,
)

logger = logging.getLogger(__name__)

# This seam's OWN canonical rejection event and raised-message noun. FROZEN by
# ruling O2 — ``test_retry_seam.py`` compares the observed values against two
# hand-written dicts as EXACT SETS, so a different spelling reddens node ids no
# production change can fix.
_QUERY_LABEL = "floor_calibration.query.rejected"
_QUERY_NOUN = "floor calibration query"

# The state §7 exempts from the mandatory ``note`` — the ONE state a healthy
# engine spends its life in.
_STATE_MEASURED = "measured"
# The ONE state F5's typed cause may appear on.
_STATE_MEASURED_NOT_ADOPTED = "measured_not_adopted"

# The measurement payload keys this ledger reads to validate the F4/F5/§7 domain.
# The rest of the payload is passed through UNTOUCHED — a ledger that filtered
# unknown keys would silently drop caller data, and the SCHEMAFULL table's own
# rejection of an undeclared column is the backstop that says so loudly.
_STATE_KEY = "state"
_CAUSE_KEY = "non_adoption_cause"
_NOTE_KEY = "note"

# Bound parameter names (producer-namespaced, per ``compose``'s collision rule).
_MEASUREMENT_ID_PARAM = "fc_measurement_id"
_HEAD_ID_PARAM = "fc_head_id"
_PAYLOAD_PARAM = "fc_payload"
_AXES_PARAM = "fc_axes"
_AXIS_PARAM_PREFIX = "fc_axis_"
_LEASE_ROW_PARAM = "fc_lease_row_id"
_FENCE_HOLDER_PARAM = "fc_fence_holder"
_FENCE_EPOCH_PARAM = "fc_fence_epoch"
_LIMIT_PARAM = "fc_limit"
# The LET variable the head mint publishes its new revision under, for the
# measurement CREATE that rides the SAME transaction to read.
_HEAD_REVISION_VAR = "fc_head_revision"

# ⚠ The fence guard's refusal text carries NO ``BEGIN``/``COMMIT`` WORD, in any
# case: ``compose``'s envelope-integrity check refuses a fragment statement whose
# text matches ``\b(BEGIN|COMMIT)\b`` case-INSENSITIVELY, so an English refusal
# mentioning "the commit" would raise ``TxnEnvelopeViolationError`` at build time.
# Nothing ever MATCHES this text — the lost-fence verdict is read from store
# STATE (see :meth:`FloorCalibrationStore._fence_verdict`); it exists only to
# abort the transaction.
_FENCE_REFUSAL_TEXT = "the lease fence moved: this run no longer holds it"


class FloorCalibrationError(SurrealStoreError):
    """Base for this ledger's typed domain failures."""


class FenceLostError(FloorCalibrationError):
    """The end-of-run commit was refused because the lease fence moved.

    A lapsed or superseded holder's commit fails LOUDLY and is discarded as a
    lost race (R10.2) — never retried, never silently swallowed, and never
    reported as :class:`~loremaster.store._txn.TxnContentionExhaustedError`
    (which means something entirely different: the shared driver's budget
    drained on a genuine write-write conflict).
    """


@dataclass(frozen=True)
class LeaseFence:
    """The immutable ``(holder_identity, fence_epoch)`` snapshot a run commits under."""

    holder_identity: str
    fence_epoch: int


@dataclass(frozen=True)
class AdoptedHead:
    """The head row a reader resolves for an axis mapping."""

    head_identity: str
    axes: Mapping[str, str]
    measurement_id: str
    revision: int
    adopted_at: datetime


@dataclass(frozen=True)
class MeasurementReceipt:
    """What a completed run's commit returns."""

    measurement_id: str
    head_identity: str
    adopted: bool
    head_revision: int | None


class FloorCalibrationStore:
    """The append-only measurement ledger + its head pointer (B4)."""

    def __init__(
        self,
        *,
        url: str,
        namespace: str,
        database: str,
        user: str,
        password: SecretStr,
    ) -> None:
        """Store the ledger's wiring. Does not open any connection yet.

        ⚠ IT OPENS NOTHING, deliberately: ``test_retry_seam.py`` CONSTRUCTS
        every discovered ``_query``-owning seam, and a constructor that dialed
        (or raised) would turn that shared pin RED for a reason that has nothing
        to do with this ledger. The socket is opened lazily, under a
        double-checked lock, by :meth:`_ensure_connection`.
        """
        self._url = url
        self._namespace = namespace
        self._database = database
        self._user = user
        self._password = password
        self._connection: _SurrealConnection | None = None
        # Guards the connect-time check-then-set so N concurrent first-callers
        # never each open their own socket (the double-checked lock every
        # connection owner in this package holds).
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
                "floor_calibration.connected",
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
            logger.debug("floor_calibration.close.already_closed")

    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        """Run a single statement on the (lazily opened) connection, self-healing.

        Delegates to :func:`~loremaster.store._txn.run_query` — the ONE shared
        attempt body: classify, signal, self-heal, log.

        ⚠ ``label`` and ``noun`` are FROZEN VALUES, not free choices:
        ``label="floor_calibration.query.rejected"`` and
        ``noun="floor calibration query"``. ``test_retry_seam.py`` compares the
        OBSERVED events and nouns against two HAND-WRITTEN dicts as exact sets,
        and the lead has authorised exactly these entries (ruling O2). A
        different spelling reddens three node ids no production change can fix.
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
        """Close the live connection (if any).

        Tolerant of a NEVER-CONNECTED ledger — pinned, because it is promised in
        prose and a build that raised would surface only as fixture-teardown
        noise attributed to whatever test happened to run last.
        """
        if self._connection is not None:
            await self._safe_close(self._connection)
            self._connection = None

    async def ensure_ready(self) -> None:
        """Apply the floor-calibration schema slice — idempotent, re-runnable.

        ⚠ **THIS SLICE ONLY.** It does NOT emit the lease slice, even though the
        fenced commit READS the lease row: ruling O3 rejected exactly that
        coupling as "an undisclosed cross-slice dependency no pin requires". The
        lease table is :class:`~loremaster.store.lease.SurrealLeaseStore`'s to
        create.

        The multi-statement DDL rides
        :func:`~loremaster.store._txn.execute_transaction`, which verifies EVERY
        statement's status; the SDK's plain ``query()`` validates statement[0]
        only (store reference §3).
        """
        await self._ensure_connection()
        ddl = generate_floor_calibration_ddl()
        await execute_transaction(
            f"BEGIN;\n{ddl}COMMIT;\n",
            {},
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )
        logger.debug("floor_calibration.schema.ready", extra={"database": self._database})

    async def record_measurement(
        self,
        *,
        axes: Mapping[str, str],
        measurement: Mapping[str, Any],
        adopt: bool,
        fence: LeaseFence | None = None,
    ) -> MeasurementReceipt:
        """Append one measurement row and, when ``adopt``, advance the head.

        ONE transaction (``execute_transaction``): the measurement CREATE plus,
        on adoption, the head UPSERT that bumps the head's monotonic
        ``revision``. THE HEAD IS A HOT ROW — every adopting run on every pod
        contends on it, and the ONE driver is ``_txn.retry_on_conflict``.

        ⚠ **THE FENCE GUARD LIVES INSIDE THAT TRANSACTION** (R10.2's
        ``WHERE fence_epoch = $mine``), never as a read-then-write pre-check. A
        TOCTOU pre-check is exactly the race a fencing token exists to close: a
        lapsed holder reads the lease, sees its own epoch, and commits after
        another pod has already seized. Measured — a pre-check build passed the
        entire contract at 143/0 before this was pinned (adversary W2).

        ⚠ **AND THE ROW CARRIES ``note``, WHICH IS NOT ``non_adoption_cause``**
        (lead ruling E5). ``note`` is FREE TEXT and follows §7's rule: mandatory
        unless the state is ``measured``. ``non_adoption_cause`` is F5's typed
        enum and appears ONLY on ``measured_not_adopted`` — a ``measuring`` row
        has not concluded, so fabricating a non-adoption cause for it is the
        same projection the two-degeneracy split exists to forbid.
        ⚠ Carried to 11-ii: ``note`` is STORED FREE TEXT. The day anything
        RENDERS it, it routes through the shared sanitiser seam and its tests
        carry a hostile fixture (newlines + a row-shaped forgery line + backtick
        runs). Nothing renders it in 11-i, which is why this is easy to lose.

        Args:
            axes: The head's axis mapping (see
                :func:`~loremaster.floor_calibration.domain.head_identity`).
            measurement: The row's payload.
            adopt: Whether this measurement becomes the head.
            fence: The lease snapshot to commit under. ``None`` means UNFENCED
                — legal only where no lease is held (the single-process lab
                path); a fenced run passes its own snapshot and the commit is
                refused if the fence has moved.

        Returns:
            The receipt naming the created row, its head, and the head's new
            revision (``None`` when ``adopt`` is false).

        Raises:
            FenceLostError: ``fence`` was supplied and no longer holds.
            ValueError: The row's state/cause/note fields violate the F4/F5/§7
                domain (an unknown state, an unknown cause, a
                ``measured_not_adopted`` row with no cause, an adopted row
                carrying one, or a non-``measured`` row with no ``note``).
        """
        self._validate_domain(measurement)
        # The head id is DERIVED, through the domain MODULE, on every write: one
        # implementation of the identity (F6). The column itself is REQUIRED
        # (ruling O7 — see the schema module's note), so this derivation is the
        # ergonomic layer and the store ASSERT is the backstop; neither is
        # redundant, and a caller cannot forge the value either (the computed key
        # wins inside ``object::extend``).
        head_identity = floor_domain.head_identity(axes)
        measurement_id = str(uuid4())
        params: dict[str, Any] = {
            _MEASUREMENT_ID_PARAM: measurement_id,
            _HEAD_ID_PARAM: head_identity,
            _PAYLOAD_PARAM: dict(measurement),
        }
        statements: list[str] = []
        if fence is not None:
            statements += self._fence_guard_statements()
            params[_LEASE_ROW_PARAM] = LEASE_SINGLETON_ID
            params[_FENCE_HOLDER_PARAM] = fence.holder_identity
            params[_FENCE_EPOCH_PARAM] = fence.fence_epoch
        if adopt:
            statements.append(self._head_mint_statement())
            params[_AXES_PARAM] = dict(axes)
            params.update(
                {f"{_AXIS_PARAM_PREFIX}{axis}": axes[axis] for axis in self._head_axis_columns()}
            )
        statements.append(self._measurement_create_statement(adopt=adopt))
        statement_text, merged_params = compose(
            TxnFragment(statements=statements, params=params)
        )
        try:
            await execute_transaction(
                statement_text,
                merged_params,
                acquire=self._ensure_connection,
                drop=self._drop_connection,
                url=self._url,
            )
        except (SurrealConnectionError, TxnContentionExhaustedError):
            # NEITHER is a fence verdict, and neither may be re-dressed as one: a
            # dead socket says nothing about who holds the lease, and exhausted
            # contention is a genuine write-write conflict the shared driver gave
            # up on. Both propagate UNTOUCHED (the stub's own warning: a
            # ``FenceLostError`` must never be confused with
            # ``TxnContentionExhaustedError``, which "means something entirely
            # different").
            raise
        except SurrealStoreError as error:
            if fence is None:
                raise
            verdict = await self._fence_verdict(error, fence)
            if verdict is error:
                # INTACT fence, or a confirming read that could not complete: the
                # original propagates with its own cause chain and traceback
                # untouched — a bare ``raise``, never a re-raise of the same
                # object, which would truncate both.
                raise
            raise verdict from error
        head_revision = await self._minted_head_revision(measurement_id) if adopt else None
        return MeasurementReceipt(
            measurement_id=measurement_id,
            head_identity=head_identity,
            adopted=adopt,
            head_revision=head_revision,
        )

    async def read_adopted_head(self, axes: Mapping[str, str]) -> AdoptedHead | None:
        """Resolve the adopted head for ``axes`` — ``None`` when unmeasured.

        Takes an AXES MAPPING, never positional arguments (F6).

        ``None`` covers both "no head row" and "a head row that names no adopted
        measurement": a fresh instance is ``unmeasured``, and a fabricated zero
        floor is exactly what 11-ii would serve as a real measurement.

        Raises:
            FloorCalibrationError: The head row NAMES an adopted measurement but
                carries no adoption timestamp. Every head this ledger writes sets
                both in ONE transaction, so that combination is a torn or foreign
                write — and a silent ``None`` there would read as "never
                measured" while an adopted pointer sits in the store.
        """
        head_identity = floor_domain.head_identity(axes)
        rows = _as_rows(
            await self._query(
                f"SELECT {FLOOR_HEAD_REVISION_COLUMN}, {FLOOR_HEAD_MEASUREMENT_COLUMN}, "
                f"{FLOOR_HEAD_ADOPTED_AT_COLUMN}, {FLOOR_HEAD_AXES_COLUMN} FROM "
                f"type::record('{FLOOR_HEAD_TABLE}', ${_HEAD_ID_PARAM})",
                {_HEAD_ID_PARAM: head_identity},
            )
        )
        if not rows:
            return None
        row = rows[0]
        measurement_id = _bare_record_id(row.get(FLOOR_HEAD_MEASUREMENT_COLUMN))
        if measurement_id is None:
            return None
        adopted_at = row.get(FLOOR_HEAD_ADOPTED_AT_COLUMN)
        if not isinstance(adopted_at, datetime):
            raise FloorCalibrationError(
                f"head {head_identity!r} names adopted measurement {measurement_id!r} but "
                f"carries no adoption timestamp ({FLOOR_HEAD_ADOPTED_AT_COLUMN}="
                f"{adopted_at!r}) — the pointer is torn, and reporting 'never measured' "
                f"would hide it"
            )
        stored_axes = row.get(FLOOR_HEAD_AXES_COLUMN)
        return AdoptedHead(
            head_identity=head_identity,
            # The stored mapping is the AUTHORITY (it is what the id was minted
            # from, so the two cannot disagree); the requested mapping is the
            # fallback for a row written by something that skipped the column.
            axes=dict(stored_axes) if isinstance(stored_axes, dict) else dict(axes),
            measurement_id=measurement_id,
            revision=int(row.get(FLOOR_HEAD_REVISION_COLUMN) or 0),
            adopted_at=adopted_at,
        )

    async def measurement_history(
        self, axes: Mapping[str, str], *, limit: int
    ) -> list[Mapping[str, Any]]:
        """The head's append-only history, newest first — the F6 tuning record.

        The projection is EXPLICIT (:data:`~loremaster.store.surreal_schema.FLOOR_MEASUREMENT_COLUMNS`
        plus the row's own id), never ``SELECT *``: store reference §2 records
        that ``SELECT *`` OMITS a ``NONE``-valued column entirely, so on a table
        whose columns are almost all ``option<>`` every reader of an unset column
        would take a ``KeyError``. Under an explicit projection an unset column
        reads ``None``, which is the shape a consumer can actually rely on.
        (``created_at`` is in the projection because it must be: ``ORDER BY`` a
        column absent from an explicit selection is a PARSE ERROR — store
        reference §7's 2026-07-25 probe, re-confirmed 2026-07-26.)

        Args:
            axes: The head whose history to read (F6's axis mapping).
            limit: The maximum number of rows, newest first.

        Returns:
            Up to ``limit`` rows, NEWEST FIRST — the order 11-i-b's tuning read
            depends on; an ascending build hands it the OLDEST rows while calling
            them the latest history.

        Raises:
            ValueError: ``limit`` is not positive — a caller asking for nothing
                is a caller bug, never an empty history.
        """
        if limit < 1:
            raise ValueError(f"measurement_history limit must be >= 1, got {limit}")
        head_identity = floor_domain.head_identity(axes)
        columns = ", ".join(("record::id(id) AS measurement_id", *FLOOR_MEASUREMENT_COLUMNS))
        rows = _as_rows(
            await self._query(
                f"SELECT {columns} FROM {FLOOR_MEASUREMENT_TABLE} "
                f"WHERE {FLOOR_MEASUREMENT_HEAD_IDENTITY_COLUMN} = ${_HEAD_ID_PARAM} "
                f"ORDER BY {FLOOR_MEASUREMENT_CREATED_AT_COLUMN} DESC LIMIT ${_LIMIT_PARAM}",
                {_HEAD_ID_PARAM: head_identity, _LIMIT_PARAM: limit},
            )
        )
        return list(rows)

    # -- the write's statements, and the fence verdict ----------------------

    @staticmethod
    def _head_axis_columns() -> tuple[str, ...]:
        """The head's always-serialised axes — the columns the mint writes.

        Read from the ONE registry
        (:data:`~loremaster.floor_calibration.domain.FLOOR_HEAD_ALWAYS_SERIALISED_AXES`),
        which is the same tuple ``surreal_schema._floor_head_statements`` emits a
        column for, so registering an axis moves the DDL and this write together.
        """
        return tuple(floor_domain.FLOOR_HEAD_ALWAYS_SERIALISED_AXES)

    @staticmethod
    def _fence_guard_statements() -> list[str]:
        """R10.2's guard — IN the commit transaction, never a read-then-write pre-check.

        A TOCTOU pre-check is the exact race a fencing token exists to close: a
        lapsed holder reads the lease, sees its own epoch, and commits after
        another pod has already seized. Measured — a pre-check build passed the
        entire contract at 143/0 (adversary W2).

        The guard is a SELECT bound to ``(holder, epoch)`` plus a ``THROW`` that
        aborts the whole transaction when it matches nothing, so the write can
        never land under a moved fence. The THROW's TEXT is never read by anything
        (the verdict comes from :meth:`_fence_verdict`'s state re-read); it only
        rolls the transaction back.
        """
        return [
            f"LET $fc_fence_held = (SELECT VALUE id FROM "
            f"type::record('{LEASE_TABLE}', ${_LEASE_ROW_PARAM}) "
            f"WHERE {LEASE_HOLDER_IDENTITY_COLUMN} = ${_FENCE_HOLDER_PARAM} "
            f"AND {LEASE_FENCE_EPOCH_COLUMN} = ${_FENCE_EPOCH_PARAM})",
            f"IF array::len($fc_fence_held) = 0 {{ THROW '{_FENCE_REFUSAL_TEXT}' }}",
        ]

    def _head_mint_statement(self) -> str:
        """The HOT-ROW head mint: bump the revision, point at this measurement.

        ONE ``UPSERT`` on the one row every adopting run on every pod contends on
        (B4). The revision is minted STORE-SIDE (``(revision ?? 0) + 1``, so the
        first adoption yields 1 on a row that does not exist yet) and published
        into a ``LET`` variable the measurement CREATE in the SAME transaction
        reads — which is what lets the receipt report the revision THIS commit
        minted rather than whatever a racer has since advanced the row to.
        Contention is the ONE shared driver's business
        (:func:`~loremaster.store._txn.retry_on_conflict`, via
        ``execute_transaction``): no private retry, no private backoff.
        """
        axis_assignments = "".join(
            f", {axis} = ${_AXIS_PARAM_PREFIX}{axis}" for axis in self._head_axis_columns()
        )
        return (
            f"LET ${_HEAD_REVISION_VAR} = (UPSERT "
            f"type::record('{FLOOR_HEAD_TABLE}', ${_HEAD_ID_PARAM}) SET "
            f"{FLOOR_HEAD_REVISION_COLUMN} = ({FLOOR_HEAD_REVISION_COLUMN} ?? 0) + 1, "
            f"{FLOOR_HEAD_MEASUREMENT_COLUMN} = "
            f"type::record('{FLOOR_MEASUREMENT_TABLE}', ${_MEASUREMENT_ID_PARAM}), "
            f"{FLOOR_HEAD_ADOPTED_AT_COLUMN} = time::now(), "
            f"{FLOOR_HEAD_AXES_COLUMN} = ${_AXES_PARAM}{axis_assignments} "
            f"RETURN AFTER)[0].{FLOOR_HEAD_REVISION_COLUMN}"
        )

    @staticmethod
    def _measurement_create_statement(*, adopt: bool) -> str:
        """The append-only measurement CREATE.

        ``object::extend($payload, {computed})`` is the ONE shape that mixes a
        BOUND payload with store-side/derived columns: ``CONTENT`` composes with
        neither ``SET`` nor ``MERGE`` (both are parse errors — store reference
        §2), and re-listing every column by hand would silently drop the next one
        somebody adds. The payload stays OPAQUE, so an undeclared key reaches the
        SCHEMAFULL table and is rejected LOUDLY rather than being filtered away
        behind the caller's back. The computed keys WIN over a caller-supplied
        key of the same name (probed 2026-07-26: ``object::extend``'s second
        object takes precedence), so a caller cannot forge ``head_identity``.
        """
        computed = f"{FLOOR_MEASUREMENT_HEAD_IDENTITY_COLUMN}: ${_HEAD_ID_PARAM}"
        if adopt:
            computed += (
                f", {FLOOR_MEASUREMENT_HEAD_REVISION_COLUMN}: ${_HEAD_REVISION_VAR}"
            )
        return (
            f"CREATE type::record('{FLOOR_MEASUREMENT_TABLE}', ${_MEASUREMENT_ID_PARAM}) "
            f"CONTENT object::extend(${_PAYLOAD_PARAM}, {{ {computed} }})"
        )

    async def _minted_head_revision(self, measurement_id: str) -> int:
        """Read back the head revision THIS commit minted, off its own row.

        The revision is read from the (IMMUTABLE, append-only) measurement row
        rather than from the head row, and that is the whole point: the head is a
        hot row, so a racer may already have advanced it by the time this read
        runs, and two adopting runs would then report the SAME revision — which
        is precisely what the contention pin's "N distinct consecutive revisions"
        invariant catches.

        Raises:
            FloorCalibrationError: The row vanished, or carries no minted
                revision — a torn commit, which must be loud rather than a
                ``None`` the receipt would report as "not adopted".
        """
        rows = _as_rows(
            await self._query(
                f"SELECT {FLOOR_MEASUREMENT_HEAD_REVISION_COLUMN} FROM "
                f"type::record('{FLOOR_MEASUREMENT_TABLE}', ${_MEASUREMENT_ID_PARAM})",
                {_MEASUREMENT_ID_PARAM: measurement_id},
            )
        )
        revision = rows[0].get(FLOOR_MEASUREMENT_HEAD_REVISION_COLUMN) if rows else None
        if revision is None:
            raise FloorCalibrationError(
                f"measurement {measurement_id!r} committed without a minted head revision — "
                f"the adopting transaction did not land as one unit"
            )
        return int(revision)

    async def _fence_verdict(self, error: SurrealStoreError, fence: LeaseFence) -> Exception:
        """Classify a rolled-back FENCED commit from store STATE, never from text.

        E2, and it is not a preference: repo law and F8-C6 forbid matching engine
        message text, and this repo has the receipts (#118 — a classifier greps
        for "assert" while the engine says "must conform to"; #111 — the
        retryable marker is still an English substring). A state re-read survives
        any rewording the engine ships.

        Three fates, all of them real:

        * the fence MOVED (or the row is gone) -> :class:`FenceLostError`, the
          original error chained;
        * the fence is INTACT -> the original error, untouched: a store rejection
          under a held fence keeps its own type, or every real defect on this
          path becomes an invisible "benign lost race";
        * the confirming read CANNOT COMPLETE -> the original error, untouched.
          A classifier must never report ``FenceLostError`` on the strength of
          evidence it failed to obtain (E2's rider), and it must never swallow
          the original either.

        Args:
            error: The rejection ``execute_transaction`` raised.
            fence: The snapshot the caller committed under.

        Returns:
            The exception the caller should see — ``FenceLostError`` only when the
            store SAYS the fence moved.
        """
        try:
            rows = _as_rows(
                await self._query(
                    f"SELECT {LEASE_HOLDER_IDENTITY_COLUMN}, {LEASE_FENCE_EPOCH_COLUMN} FROM "
                    f"type::record('{LEASE_TABLE}', ${_LEASE_ROW_PARAM})",
                    {_LEASE_ROW_PARAM: LEASE_SINGLETON_ID},
                )
            )
        except SurrealStoreError as read_error:
            logger.warning(
                "floor_calibration.fence.unconfirmable",
                extra={
                    "url": self._url,
                    "holder_identity": fence.holder_identity,
                    "fence_epoch": fence.fence_epoch,
                    "read_error": str(read_error),
                },
            )
            return error
        if rows:
            row = rows[0]
            holder = row.get(LEASE_HOLDER_IDENTITY_COLUMN)
            epoch = row.get(LEASE_FENCE_EPOCH_COLUMN)
            still_held = holder == fence.holder_identity and (
                epoch is not None and int(epoch) == fence.fence_epoch
            )
            if still_held:
                return error
        return FenceLostError(
            f"the fenced commit was refused: the lease no longer names "
            f"holder={fence.holder_identity!r} at fence_epoch={fence.fence_epoch} — "
            f"this run lost the race and its measurement is discarded"
        )

    @staticmethod
    def _validate_domain(measurement: Mapping[str, Any]) -> None:
        """Refuse an F4/F5/§7 domain violation BEFORE any I/O.

        The ledger is the ergonomic layer; the store's own ``ASSERT``s stay the
        backstop for any writer that skips it (the
        ``_require_non_empty_area_category`` precedent). Validating first is a
        STATE property, not a courtesy: a build that wrote the row and then
        raised would corrupt the append-only history 11-ii's exact-skip reads.

        The ``note`` / ``non_adoption_cause`` split is ruling E5: ``note`` is FREE
        TEXT, mandatory unless the state is ``measured``; the cause is F5's typed
        enum and appears ONLY on ``measured_not_adopted``. Conflating them would
        force a bogus enum value onto every in-progress row.

        Raises:
            ValueError: An unknown state, an unknown cause, a
                ``measured_not_adopted`` row with no cause, a cause on any other
                state, or a non-``measured`` row with no ``note``.
        """
        state = measurement.get(_STATE_KEY)
        if state not in FLOOR_STATES:
            raise ValueError(
                f"unknown floor state {state!r}: the domain is CLOSED — {list(FLOOR_STATES)}"
            )
        cause = measurement.get(_CAUSE_KEY)
        if cause is not None and cause not in FLOOR_NON_ADOPTION_CAUSES:
            raise ValueError(
                f"unknown non-adoption cause {cause!r}: the domain is CLOSED — "
                f"{list(FLOOR_NON_ADOPTION_CAUSES)}"
            )
        if state == _STATE_MEASURED_NOT_ADOPTED and cause is None:
            raise ValueError(
                f"a {_STATE_MEASURED_NOT_ADOPTED!r} row REQUIRES a typed "
                f"{_CAUSE_KEY!r} (F5): 11-ii cannot serve a distinction the row never recorded"
            )
        if cause is not None and state != _STATE_MEASURED_NOT_ADOPTED:
            raise ValueError(
                f"{_CAUSE_KEY!r}={cause!r} on a {state!r} row: F5's cause names why adoption "
                f"did NOT happen, so it appears ONLY on {_STATE_MEASURED_NOT_ADOPTED!r} "
                f"(ruling E5) — a row that has not concluded has no non-adoption cause"
            )
        note = measurement.get(_NOTE_KEY)
        if state != _STATE_MEASURED and not (isinstance(note, str) and note.strip()):
            raise ValueError(
                f"a {state!r} row REQUIRES a non-empty {_NOTE_KEY!r} (§7): every state but "
                f"{_STATE_MEASURED!r} must say, in free text, what happened"
            )


def _as_rows(result: Any) -> list[dict[str, Any]]:
    """Narrow a statement result to its list of dict rows."""
    if not isinstance(result, list):
        return []
    return [row for row in result if isinstance(row, dict)]


def _bare_record_id(value: Any) -> str | None:
    """The BARE id of a projected record link — ``None`` when the link is unset.

    Deliberately client-side rather than a ``record::id()`` projection: probed
    2026-07-26 on the 3.2.1 test store, ``record::id(NONE)`` RAISES
    (*"Argument 1 was the wrong type. Expected `record` but found `NONE`"*), so
    projecting it would turn an un-adopted head — a legitimate state — into an
    engine error.
    """
    if isinstance(value, RecordID):
        return str(value.id)
    return None
