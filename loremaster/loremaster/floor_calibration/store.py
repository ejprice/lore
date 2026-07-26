"""STUB SURFACE (packet 11-i-a) — the floor-calibration ledger.

WRITTEN BY THE CONTRACT AUTHOR (`contract-11ia-1`), NOT BY A BUILDER. Every
``NotImplementedError`` is a hole the 11-i-a builder fills; the names and
signatures are the FROZEN interface packet 11-i-b cites.

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

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import SecretStr

from loremaster.store._txn import SurrealStoreError


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
    """STUB (packet 11-i-a). The append-only measurement ledger + head pointer."""

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

        ⚠ REAL EVEN IN THE STUB, deliberately: ``test_retry_seam.py``
        CONSTRUCTS every discovered ``_query``-owning seam, and a constructor
        that raised would turn that shared pin RED for a reason that has
        nothing to do with this contract — a collection-shaped failure, which
        proves nothing about behaviour. The behaviour is stubbed below.
        """
        self._url = url
        self._namespace = namespace
        self._database = database
        self._user = user
        self._password = password
        self._connection: Any | None = None

    async def _ensure_connection(self) -> Any:
        """STUB. The lazily-opened, double-checked-locked connection."""
        raise NotImplementedError("packet 11-i-a: FloorCalibrationStore._ensure_connection")

    async def _drop_connection(self, connection: Any) -> None:
        """STUB. The compare-and-swap self-heal."""
        raise NotImplementedError("packet 11-i-a: FloorCalibrationStore._drop_connection")

    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        """STUB. Delegates to ``store._txn.run_query`` — the ONE shared attempt body.

        ⚠ ``label`` and ``noun`` are FROZEN VALUES, not free choices:
        ``label="floor_calibration.query.rejected"`` and
        ``noun="floor calibration query"``. ``test_retry_seam.py`` compares the
        OBSERVED events and nouns against two HAND-WRITTEN dicts as exact sets,
        and the lead has authorised exactly these entries (ruling O2). A
        different spelling reddens three node ids no production change can fix.
        """
        raise NotImplementedError("packet 11-i-a: FloorCalibrationStore._query")

    async def close(self) -> None:
        """STUB. Close the live connection (if any).

        Tolerant of a NEVER-CONNECTED ledger — pinned, because it is promised in
        prose and a build that raised would surface only as fixture-teardown
        noise attributed to whatever test happened to run last.
        """
        raise NotImplementedError("packet 11-i-a: FloorCalibrationStore.close")

    async def ensure_ready(self) -> None:
        """STUB. Apply the floor-calibration schema slice — idempotent, re-runnable."""
        raise NotImplementedError("packet 11-i-a: FloorCalibrationStore.ensure_ready")

    async def record_measurement(
        self,
        *,
        axes: Mapping[str, str],
        measurement: Mapping[str, Any],
        adopt: bool,
        fence: LeaseFence | None = None,
    ) -> MeasurementReceipt:
        """STUB. Append one measurement row and, when ``adopt``, advance the head.

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
        raise NotImplementedError("packet 11-i-a: FloorCalibrationStore.record_measurement")

    async def read_adopted_head(self, axes: Mapping[str, str]) -> AdoptedHead | None:
        """STUB. Resolve the adopted head for ``axes`` — ``None`` when unmeasured.

        Takes an AXES MAPPING, never positional arguments (F6).
        """
        raise NotImplementedError("packet 11-i-a: FloorCalibrationStore.read_adopted_head")

    async def measurement_history(
        self, axes: Mapping[str, str], *, limit: int
    ) -> list[Mapping[str, Any]]:
        """STUB. The head's append-only history, newest first — the F6 tuning record."""
        raise NotImplementedError("packet 11-i-a: FloorCalibrationStore.measurement_history")
