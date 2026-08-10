"""The ``await`` verb's wait-machine — packet 05a-ii (design R-1).

``InboxAwaiter`` is a STANDALONE, bounded, snapshot-first inbox WAIT primitive: it
surfaces a caller's unseen ``lore_comms`` traffic *now*, or waits (up to a fixed budget)
for it to arrive, then returns an honest point-in-time snapshot. It is the bounded
one-shot sibling of :class:`loremaster.scout.CommandSubscriber` (the infinite
LIVE-primary/poll-fallback/reconnect command reader) and mirrors that house shape
deliberately: same injected ``connect`` factory, same "LIVE is a contentless wake, the
poll fallback carries the load" discipline (store reference §10), same SDK-await-boundary
error classification (the ONE shared ``store._txn._SDK_AWAIT_BOUNDARY_ERRORS`` — never a
private inline clone; ONE IMPLEMENTATION / #102). It is a legitimately DISTINCT structure
(bounded ≠ infinite), so it does NOT extract a shared loop with ``CommandSubscriber``
(that would force one lifecycle onto two) — it shares exactly the error-classification
POLICY, proven by the cross-suite mutation pins.

Decided forks (design §A + follow-up rulings, pinned by ``test_comms_await.py``):

* **F1 — PEEK, never stamp.** Every read is ``drain(peek=True)``; ``await`` stamps
  nothing, so it is idempotent and retry-safe. The caller CONSUMES via ``action=drain``.
* **F2 — fixed budget.** :data:`AWAIT_BUDGET_S` is a fixed constant strictly under the
  ~60s MCP tool-call ceiling — NOT a caller ``timeout=`` knob.
* **F3 — the LIVE-WHERE key is the agent-id literal ONLY**, never ``thread`` (``thread``
  is un-charset-gated caller free text — inlining it opens the DD-3.e injection door).
  ``thread?`` narrows the returned traffic CLIENT-SIDE on the authoritative snapshot.

The state machine (design §A.1): snapshot-first ``drain(peek=True)`` short-circuit →
establish the filtered LIVE-on-edge (best-effort) → wait, racing a LIVE wake against a
poll tick within the budget, re-draining (authoritative) on any wake → a FINAL snapshot
at the deadline → return the PEEK. LIVE only ever TRIGGERS a re-drain; it never supplies
the answer (store §10: "poll fallback is MANDATORY … contentless wake ONLY"). The
LIVE-wake + real socket-drop non-loss are proven against a REAL socket by the deploy-gated
build probe (design §A.6); the in-process pins prove this STATE MACHINE over injected
seams.
"""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import time
from collections.abc import Awaitable, Callable
from typing import Any

from loremaster.messages import MESSAGE_GRADE_DIRECTIVE, MessageDrainResult
from loremaster.store._txn import (
    _SDK_AWAIT_BOUNDARY_ERRORS,
    _SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION,
    RetryableConflictSignal,
    is_retryable_conflict_error,
    retry_on_conflict,
)
from loremaster.store.surreal_schema import TO_RELATION

# F2: the fixed wait budget (seconds). A FIXED named constant, NEVER a caller ``timeout=``
# knob — strictly under the ~60s MCP tool-call ceiling so the tool RETURNS a render (the
# honest-empty naming its bound) rather than being killed mid-wait, which would defeat the
# whole honest-empty contract. The exact value is builder latitude within "positive and
# strictly under the ceiling"; the PROPERTY is what the pin guards, per the
# enumerate-the-safe-set law (55 leaves ~5s of headroom for the render + transport).
AWAIT_BUDGET_S = 55.0

# The poll-fallback cadence (seconds). LIVE is best-effort (store §10: a poll fallback is
# MANDATORY, and it must carry the load ALONE); this floor guarantees progress even when
# LIVE never fires or silently drops. Several ticks fit inside AWAIT_BUDGET_S so a message
# landing in a poll gap is caught by the next tick or the final snapshot, never missed.
AWAIT_POLL_INTERVAL_S = 2.0


class InboxAwaiter:
    """A bounded, snapshot-first, LIVE-primary/poll-fallback inbox waiter (R-1).

    Constructed with injected seams (the ``CommandSubscriber`` idiom, so the wait logic is
    testable over fakes with NO real socket):

    Args:
        connect: An async factory returning a fresh signed-in SDK connection (the LIVE
            subscription owns its own socket, distinct from the ledger's drain connection).
        drain: The ledger's ``drain`` seam — called ``peek=True`` (F1: never stamps).
        sleep: The awaitable delay seam (injectable for tests); defaults to
            :func:`asyncio.sleep`.
        now: The monotonic clock seam (injectable for tests); defaults to
            :func:`time.monotonic`.
        budget_s: The fixed wait budget; defaults to :data:`AWAIT_BUDGET_S` (F2).
        poll_interval_s: The poll-fallback cadence; defaults to
            :data:`AWAIT_POLL_INTERVAL_S`.
    """

    def __init__(
        self,
        *,
        connect: Callable[[], Awaitable[Any]],
        drain: Callable[..., Awaitable[MessageDrainResult]],
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        now: Callable[[], float] = time.monotonic,
        budget_s: float = AWAIT_BUDGET_S,
        poll_interval_s: float = AWAIT_POLL_INTERVAL_S,
    ) -> None:
        self._connect = connect
        self._drain = drain
        self._sleep = sleep
        self._now = now
        self._budget_s = budget_s
        self._poll_interval_s = poll_interval_s

    # -- statement builder --------------------------------------------------- #

    def live_select_statement(self, agent_id: str) -> str:
        """The filtered LIVE-on-edge statement — the agent-id record literal ONLY (F3).

        ``LIVE SELECT * FROM to WHERE out = agent:`<uuid5-id>``` — the recipient's agent-id
        INLINED as a record literal (the SDK IGNORES a bound ``$param`` in a LIVE WHERE and
        delivers nothing; store §10), never ``thread`` and never any other caller
        substring. The id is a ``uuid5`` hash of charset-ASSERTed ``name``/``session`` — it
        carries ZERO caller free text, so the inlined literal is injection-safe BY
        CONSTRUCTION (§A.5), sidestepping DD-3.e's inline-``thread`` door entirely.

        The id is BACKTICK-quoted: a bare ``uuid5`` hex digest can begin with a digit or
        read as a number, and a hyphenated form would read its hyphens as subtraction —
        the backtick literal names the STRING-id record the SDK stored via
        ``RecordID(AGENT_TABLE, agent_id)`` (store reference §10 record-ids; the deploy
        build-probe confirms it PARSES and DISCRIMINATES on a real uuid5 id).
        """
        return f"LIVE SELECT * FROM {TO_RELATION} WHERE out = agent:`{agent_id}`"

    # -- the wait machine ---------------------------------------------------- #

    async def await_inbox(
        self, *, agent_id: str, limit: int, thread: str | None = None
    ) -> MessageDrainResult:
        """Surface this agent's unseen traffic now, or wait for it within the budget.

        Returns a PEEK-shaped :class:`MessageDrainResult` (F1: ``stamped_seqs`` empty,
        ``peeked=True``) — the caller consumes it via ``action=drain``. ``thread`` narrows
        the returned traffic CLIENT-SIDE (F3); it never reaches the LIVE WHERE.
        """
        # Step 1 — SNAPSHOT-FIRST. A caller with already-pending unseen traffic returns
        # IMMEDIATELY: no LIVE, no poll sleep. This is drain-WITH-a-wait, not only-new.
        snapshot = await self._drain(agent_id=agent_id, limit=limit, peek=True)
        narrowed = self._narrow(snapshot, thread)
        if narrowed.entries:
            return narrowed

        # Steps 2-4 — establish LIVE (best-effort), wait with the poll fallback, take a
        # FINAL snapshot at the deadline.
        deadline = self._now() + self._budget_s
        wake = asyncio.Event()
        connection: Any = None
        live_uuid: Any = None
        consume_task: asyncio.Task[None] | None = None
        try:
            connection = await self._connect()
            live_uuid, consume_task = await self._establish_live(connection, agent_id, wake)
            while self._now() < deadline:
                # Race a LIVE wake against a poll tick; re-drain on EITHER. LIVE only
                # triggers a re-read — the authoritative answer is always the drain.
                await self._wait_for_wake_or_tick(wake, deadline)
                snapshot = await self._drain(agent_id=agent_id, limit=limit, peek=True)
                narrowed = self._narrow(snapshot, thread)
                if narrowed.entries:
                    return narrowed
            # Step 4 — the FINAL snapshot AT the deadline (load-bearing): a message that
            # landed in the last poll gap is caught here, never lost to a stale wake read.
            final = await self._drain(agent_id=agent_id, limit=limit, peek=True)
            return self._narrow(final, thread)
        finally:
            await self._teardown(connection, live_uuid, consume_task)

    def _narrow(self, result: MessageDrainResult, thread: str | None) -> MessageDrainResult:
        """Narrow the snapshot to ``thread`` CLIENT-SIDE (F3), preserving the PEEK shape.

        ``thread is None`` returns the snapshot unchanged (the common case: wait on ALL of
        the agent's traffic). Otherwise the returned counts describe the THREAD-scoped view
        the caller asked for (``shown == total`` for that thread).
        """
        if thread is None:
            return result
        entries = [entry for entry in result.entries if entry.thread == thread]
        return MessageDrainResult(
            entries=entries,
            total_pending=len(entries),
            directive_pending=sum(1 for e in entries if e.grade == MESSAGE_GRADE_DIRECTIVE),
            stamped_seqs=[],
            peeked=True,
        )

    async def _live_query(self, connection: Any, statement: str) -> Any:
        """Run ONE statement on the LIVE connection through the SHARED retry driver.

        The awaiter owns no ``_query`` and takes its connection as a PARAMETER, so — exactly
        like ``scout._scout_query`` — the SDK ``query`` rides :func:`retry_on_conflict` (the
        ONE shared driver, never a private retry loop; ONE IMPLEMENTATION) with the SHARED
        classification (``is_retryable_conflict_error`` → ``RetryableConflictSignal``, both
        from ``store._txn``): a retryable conflict retries transparently, a genuine
        transport fault propagates RAW so the caller's boundary catch handles it. The
        ``connection.<method>`` receiver is lexically inside the driver's attempt body so the
        runtime SDK guard (test_retry_seam) SEES it seamed."""

        async def _attempt() -> Any:
            try:
                return await connection.query(statement)
            except _SDK_AWAIT_BOUNDARY_ERRORS as error:
                if is_retryable_conflict_error(error):
                    raise RetryableConflictSignal() from error
                raise

        return await retry_on_conflict(_attempt, label="inbox_awaiter.live.query")

    async def _establish_live(
        self, connection: Any, agent_id: str, wake: asyncio.Event
    ) -> tuple[Any, asyncio.Task[None] | None]:
        """Establish the filtered LIVE on an OPEN connection (BEST-EFFORT).

        A failure at the SDK-await boundary (the shared ``_SDK_AWAIT_BOUNDARY_ERRORS_WITH_
        CONTENTION``) means the LIVE is unavailable — the poll fallback carries the load
        (store §10), so it returns ``(None, None)`` rather than aborting the wait (the caller
        owns the connection and closes it in teardown).

        ⚠ The catch NAMES the shared module global (never an inline tuple): the cross-suite
        mutation pins rebind it, so a build holding a private clone would keep recovering
        after ``KeyError`` was dropped from the shared set and REDDEN. That is the
        "prove sharing by mutation" invariant — routing is not sharing (#102).
        """
        try:
            live_uuid = await self._live_query(connection, self.live_select_statement(agent_id))
        except _SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION:
            return None, None
        consume_task = asyncio.create_task(self._consume_live(connection, live_uuid, wake))
        return live_uuid, consume_task

    async def _consume_live(self, connection: Any, live_uuid: Any, wake: asyncio.Event) -> None:
        """Set ``wake`` on each LIVE notification — a CONTENTLESS wake (store §10: it only
        TRIGGERS the authoritative re-drain, never the source of truth). Establishing the
        subscription rides the SHARED retry driver (a retryable conflict retries); a
        dropped/orphaned subscription is swallowed at the shared boundary (the poll backstop
        keeps serving)."""

        async def _attempt() -> Any:
            try:
                subscription = connection.subscribe_live(live_uuid)
                if inspect.isawaitable(subscription):
                    subscription = await subscription
                return subscription
            except _SDK_AWAIT_BOUNDARY_ERRORS as error:
                if is_retryable_conflict_error(error):
                    raise RetryableConflictSignal() from error
                raise

        try:
            subscription = await retry_on_conflict(_attempt, label="inbox_awaiter.live.subscribe")
            async for _notification in subscription:
                wake.set()
        except _SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION:
            return

    async def _wait_for_wake_or_tick(self, wake: asyncio.Event, deadline: float) -> None:
        """Sleep ONE poll tick (bounded by the remaining budget), returning EARLY on a LIVE
        wake. The poll floor guarantees progress even if LIVE never fires; the wake only
        shortens the sleep so the common case returns well under the budget."""
        tick = min(self._poll_interval_s, deadline - self._now())
        if tick <= 0:
            return
        waker = asyncio.ensure_future(wake.wait())
        sleeper = asyncio.ensure_future(self._sleep(tick))
        try:
            await asyncio.wait({waker, sleeper}, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for pending in (waker, sleeper):
                if not pending.done():
                    pending.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await pending
        if wake.is_set():
            wake.clear()

    async def _safe_kill(self, connection: Any, live_uuid: Any) -> None:
        """Kill the LIVE query, swallowing a failure on an already-dead socket. The kill
        rides the SHARED retry driver (a retryable conflict retries) with the SHARED
        classification; this remains BEST-EFFORT cleanup, so a genuine transport fault OR
        sustained contention is swallowed at the boundary (mirrors
        ``CommandSubscriber._safe_kill``)."""

        async def _attempt() -> None:
            try:
                await connection.kill(live_uuid)
            except _SDK_AWAIT_BOUNDARY_ERRORS as error:
                if is_retryable_conflict_error(error):
                    raise RetryableConflictSignal() from error
                raise

        try:
            await retry_on_conflict(_attempt, label="inbox_awaiter.live.kill")
        except _SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION:
            pass

    async def _teardown(
        self, connection: Any, live_uuid: Any, consume_task: asyncio.Task[None] | None
    ) -> None:
        """Cancel the LIVE consumer, kill the subscription, close the connection — each
        swallowing an already-dead socket at the shared SDK-await boundary (``close`` is in
        the SDK guard's SAFE set; ``kill`` rides :meth:`_safe_kill`)."""
        if consume_task is not None:
            consume_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await consume_task
        if connection is None:
            return
        if live_uuid is not None:
            await self._safe_kill(connection, live_uuid)
        try:
            await connection.close()
        except _SDK_AWAIT_BOUNDARY_ERRORS:
            pass
