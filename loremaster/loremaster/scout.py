"""The write-role scout daemon (P5-C6, ledger #27).

The scout is the SINGLE-WRITER process for a project's unified SurrealDB index.
It composes the FULL write stack (store / manifest / code-graph /
snapshot-stamper / indexer / reconcile-engine / live-watcher) from ``lore.yaml``,
runs the eager initial sweep + live watch + periodic reconcile, and services an
out-of-band ``command`` table (LIVE-primary, poll-fallback) so an operator can
nudge it. It is deliberately SEPARATE from the read-side MCP server: importing
this module must NOT drag in FastMCP (the daemon has no HTTP surface), so the
only collaborator that touches ``loremaster.server`` — :meth:`Scout.from_config`
— imports it LAZILY, inside the method body.

Three public pieces plus the argparse entrypoint:

* :class:`Scout` — the driveable daemon: :meth:`start` readies the four write
  backends, runs the eager initial sweep, then (when the watcher is enabled)
  brings up the live observer + the periodic reconcile loop; the command channel
  runs in BOTH the enabled and the sweep-only modes. :meth:`run` wraps that
  lifecycle with SIGTERM/SIGINT handlers for a clean, signal-driven teardown.
* :class:`CommandSubscriber` — the LIVE-primary + poll-fallback + reconnect
  command reader. The LIVE query is a FILTERED ``LIVE SELECT … WHERE status =
  'pending'`` with the status INLINED as a literal (the SDK silently ignores a
  bound ``$param`` in a LIVE WHERE — it would deliver nothing), NEVER the
  whole-table ``.live(table)`` (which re-fires on every done/failed transition).
  A socket drop is recovered by RECONNECT + a poll-reconcile of the gap, so a
  command inserted while the socket was down is still dispatched EXACTLY once
  (idempotence by processed-count: a marked-done row leaves the pending set).
* :class:`UnknownCommandError` — raised by :meth:`Scout.handle_command` on an
  unrecognised ``kind``.

The command ``status`` domain is the schema's OWN ``{pending, done, failed}``
constants (imported from :mod:`loremaster.store.surreal_schema`), so a status
write can never drift from the schema's ``ASSERT``.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import inspect
import logging
import signal
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from surrealdb import AsyncSurreal

from loremaster.config import (
    LoreConfig,
    load_config,
    resolve_secret,
)
from loremaster.embedding import make_embedder_from_config
from loremaster.graph_surreal import SurrealCodeGraph
from loremaster.index.indexer import Indexer, graph_roots
from loremaster.index.reconcile import ReconcileEngine
from loremaster.index.snapshots import SnapshotStamper
from loremaster.index.surreal_manifest import SurrealManifest
from loremaster.index.watcher import LiveWatcher
from loremaster.store._txn import (
    _CONNECTION_ERRORS,
    RetryableConflictSignal,
    TxnContentionExhaustedError,
    bootstrap_session,
    is_retryable_conflict_error,
    retry_on_conflict,
)
from loremaster.store.surreal import (
    _SIGNIN_PASS_KEY,
    _SIGNIN_USER_KEY,
    SurrealStore,
)
from loremaster.store.surreal_schema import (
    _COMMAND_STATUS_DONE,
    _COMMAND_STATUS_FAILED,
    _COMMAND_STATUS_PENDING,
    COMMAND_TABLE,
)

logger = logging.getLogger(__name__)

# The command ``kind`` the requirement names for "run a reconcile sweep now"
# (ledger #27, deliverable 4a). A single named constant so the dispatch policy
# and any future producer share one vocabulary rather than a scattered literal.
_RECONCILE_COMMAND_KIND = "reconcile"

# The command-channel poll cadence (seconds) the composition root wires when it
# builds the subscriber. LIVE is the primary path; this is the REQUIRED backstop
# that carries the load whenever the live subscription is unavailable.
_DEFAULT_COMMAND_POLL_INTERVAL_S = 5.0

# The reconnect backoff bounds (seconds): a bounded exponential backoff so a
# brief store outage does not permanently wedge the command channel, and a
# transient blip recovers quickly.
_DEFAULT_BACKOFF_BASE_S = 0.5
_DEFAULT_MAX_BACKOFF_S = 30.0

# The two signals a long-lived daemon must tear down cleanly on: a container
# ``SIGTERM`` (orchestrator stop) and an interactive ``SIGINT`` (Ctrl-C).
_SHUTDOWN_SIGNALS = (signal.SIGTERM, signal.SIGINT)

# Default static-tier snapshot root — kept in sync with the batch indexer CLI and
# the server so the scout, the CLI, and the server share one snapshot location
# for a slug (plan D8 / the staleness-engine ledger).
_DEFAULT_SNAPSHOT_ROOT = Path.home() / "docker" / "mcp" / "lore-snapshot"


class UnknownCommandError(Exception):
    """Raised by :meth:`Scout.handle_command` on an unrecognised command ``kind``.

    The message NAMES the offending kind so an operator (and the command row's
    ``error`` column, when a subscriber marks it failed) can see exactly which
    unrecognised command was enqueued.
    """


# ---------------------------------------------------------------------------
# THE ONE RETRY SEAM FOR SCOUT'S QUERIES (findings #108/#120). Scout owns no
# ``_query`` and takes its connection as a PARAMETER (not ``self``), so its
# ``query()``-shaped call sites — the bootstrap DDL, the pending-command
# drain, the command CAS, and establishing the LIVE subscription — share ONE
# module-level attempt body rather than a private copy each. Routing every
# one of them through the SAME function means driving any ONE of them
# exercises the SAME call site every other one uses — the property the
# runtime SDK guard's coverage pin depends on
# (``TestNoSdkCallEscapesTheDriverAtRuntime.test_every_production_sdk_call_site_was_OBSERVED_by_the_guard``
# in ``test_retry_seam.py``): a call site nothing drives is a call site the
# guard certifies NOTHING about, and `_drain_pending` shipping finding #120
# alive through an unwatched site is exactly how this session's fifth
# instrument was defeated. (``use()``, ``kill()`` and ``subscribe_live()``
# are each already directly exercised by their own caller — the bootstrap,
# ``_safe_kill``, ``_consume_live`` — so they keep their own NAMED attempt
# closures rather than sharing this one; a shared body would have to accept
# an arbitrary bound method, which the AST lint's connection-receiver pattern
# cannot see through a parameter indirection.)
#
# This helper does NOT wrap a transport fault as ``SurrealConnectionError``
# the way the ten ledgers do. Scout must NOT: its reconnect ladder in
# :meth:`CommandSubscriber.run` is built on the RAW SDK types, and
# ``SurrealConnectionError`` is a ``RuntimeError`` outside that tuple —
# wrapping it would fly a socket drop straight past the ladder and kill
# scout's reconnect. Transport is not contention: a conflict means "the write
# did not land, try again"; a dead socket means "reconnect", and only the
# former is this function's business.
# ---------------------------------------------------------------------------


async def _scout_query_once(
    connection: Any, statement: str, params: dict[str, Any] | None = None
) -> Any:
    """One SDK ``query()`` call, classifying a retryable conflict into the
    shared signal. Everything else — a transport fault, a domain rejection,
    an empty CAS (a lost race, not an error) — propagates RAW and UNTOUCHED.
    """
    try:
        if params is None:
            return await connection.query(statement)
        return await connection.query(statement, params)
    except (*_CONNECTION_ERRORS, KeyError) as error:
        if is_retryable_conflict_error(error):
            raise RetryableConflictSignal() from error
        raise


async def _scout_query(
    connection: Any, statement: str, params: dict[str, Any] | None = None
) -> Any:
    """Every scout QUERY rides the ONE retry seam."""
    # Attributed by LABEL ONLY (finding #151, operator ruling R4): the exhaustion record
    # names WHICH seam and WHAT THE ENGINE SAID, but NOT which server — `_scout_query` takes
    # a bare `connection` and `CommandSubscriber` holds a `connect` callable rather than a
    # url, so full url attribution here is a design change to scout's connection ownership, a
    # separate wave. The partial attribution is pinned in both directions in test_retry_seam.py.
    return await retry_on_conflict(
        lambda: _scout_query_once(connection, statement, params),
        label="command_subscriber.query.rejected",
    )


async def _open_command_connection(
    *, url: str, namespace: str, database: str, user: str, password: str
) -> Any:
    """Open a raw signed-in SDK connection bound to ``namespace`` + ``database``.

    The session bootstrap is :func:`~loremaster.store._txn.bootstrap_session` —
    the ONE shared implementation every connection owner in the package calls
    (blindreader F3). This function used to carry the ELEVENTH hand-rolled copy
    of the same three BARE, UNRETRIED inline ``await`` statements (no closures,
    no shared anything — audit-polish-1 P1) — invisible to any scan keyed on
    ``_query``, since scout owns none — a module-level function instead of a
    method. Used as the :class:`CommandSubscriber`'s ``connect`` factory so the
    command channel speaks to the SAME per-project database as the rest of the
    write stack.

    Args:
        url: The SurrealDB RPC URL.
        namespace: The namespace the project's database lives under.
        database: The per-project database name.
        user: The root/username to sign in with.
        password: The password to sign in with.

    Returns:
        A live, signed-in SDK connection bound to ``namespace``/``database``.

    Deliberately UNWRAPPED (adversary P-1, ``W1-SCOUTKILL``): unlike the ten
    store/manifest/ledger seams, this function does NOT translate a bootstrap
    failure — including exhausted contention — into
    :class:`~loremaster.store._txn.SurrealConnectionError`. The caller's own
    reconnect ladder (:meth:`CommandSubscriber.run`) catches RAW SDK types
    (and :class:`~loremaster.store._txn.TxnContentionExhaustedError` directly)
    to back off and retry the whole connect — a wrap here would fly straight
    past that ladder and kill the command channel dead, with no backoff and no
    reconnect.

    It DOES self-heal the half-open socket on a failed bootstrap
    (blindreader-dry-2 F7 / audit-fix-1 B1): every one of the ten ledger seams
    closes theirs on a failed connect; this function used to close nothing,
    leaking one socket per failed connect — unbounded in a long-running
    process under sustained store contention, now that the bootstrap can take
    seconds instead of failing in milliseconds. **Closed AND raw, or
    neither** — a bare ``except Exception: close(); raise`` re-raises the
    SAME exception object, unmodified, so this cleanup can never become a
    second, accidental wrap.
    """
    connection = AsyncSurreal(url)
    credentials: dict[str, Any] = {_SIGNIN_USER_KEY: user, _SIGNIN_PASS_KEY: password}
    try:
        await connection.signin(credentials)
        await bootstrap_session(connection, namespace, database, url=url)
    except Exception:
        try:
            await connection.close()
        except _CONNECTION_ERRORS:
            logger.debug("scout.connect.close_after_failed_bootstrap.already_closed")
        raise
    return connection


class CommandSubscriber:
    """LIVE-primary, poll-fallback, reconnecting reader of the ``command`` table.

    Owns a single lazily-opened connection (from the injected ``connect``
    factory) and dispatches every ``pending`` command to ``handler`` exactly
    once, marking it ``done`` (or ``failed``, with the error recorded) against
    the schema's OWN status domain.

    Transport design (the ledger #27 hard constraints):

    * **Filtered LIVE, inlined literal.** :meth:`live_select_statement` builds a
      ``LIVE SELECT … WHERE status = 'pending'`` with the status as a LITERAL —
      the SDK silently ignores a bound ``$param`` in a LIVE WHERE (delivers
      nothing) — and NEVER the whole-table ``.live(table)`` (which re-fires on
      every done/failed transition → a re-dispatch storm).
    * **Poll fallback is REQUIRED.** LIVE is best-effort; whenever the live
      subscription is unavailable the poll loop (:meth:`process_pending_once`
      every ``poll_interval_s``) carries the load, because the SDK never replays
      a dropped live queue.
    * **Reconnect + gap reconcile.** A socket drop closes the handle, backs off
      (bounded exponential), reconnects, re-establishes LIVE, and poll-reconciles
      the gap — so a command inserted while the socket was down is recovered
      EXACTLY once (a marked-done row leaves the pending set, so a re-poll never
      re-dispatches it).

    Args:
        connect: An async factory returning a fresh signed-in connection.
        handler: The async dispatcher a pending command row is handed to.
        poll_interval_s: The poll-fallback cadence, in seconds.
        sleep: The awaitable delay seam (injectable for tests); defaults to
            :func:`asyncio.sleep`.
        backoff_base_s: The base of the bounded exponential reconnect backoff.
        max_backoff_s: The ceiling on the reconnect backoff.
    """

    def __init__(
        self,
        *,
        connect: Callable[[], Awaitable[Any]],
        handler: Callable[[dict[str, Any]], Awaitable[None]],
        poll_interval_s: float,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        backoff_base_s: float = _DEFAULT_BACKOFF_BASE_S,
        max_backoff_s: float = _DEFAULT_MAX_BACKOFF_S,
    ) -> None:
        self._connect = connect
        self._handler = handler
        self._poll_interval_s = poll_interval_s
        self._sleep = sleep
        self._backoff_base_s = backoff_base_s
        self._max_backoff_s = max_backoff_s
        # The single cached connection; ``None`` means "not connected / closed".
        self._connection: Any = None
        # ``run``'s continue/stop flag.
        self._running = False
        # Serialises the poll path and the live-notification path so a concurrent
        # LIVE + poll can never double-dispatch the same pending row.
        self._drain_lock = asyncio.Lock()

    # -- statement builders ------------------------------------------------- #

    def live_select_statement(self) -> str:
        """The FILTERED live subscription statement (status inlined as a literal).

        A ``LIVE SELECT … WHERE status = 'pending'`` targeting the command table,
        with the pending status INLINED (never a bound ``$param`` — the SDK
        ignores params in a LIVE WHERE) and using the schema's OWN pending
        constant so the filter can never drift from the schema's status domain.
        """
        return (
            f"LIVE SELECT * FROM {COMMAND_TABLE} "
            f"WHERE status = '{_COMMAND_STATUS_PENDING}'"
        )

    def _pending_select_statement(self) -> str:
        """The poll-fallback SELECT of outstanding work (ordered oldest-first).

        Backed by the ``command_status`` index on the ``status`` column; ordered
        by ``created_at`` so commands are drained in enqueue order.
        """
        return (
            f"SELECT * FROM {COMMAND_TABLE} "
            f"WHERE status = '{_COMMAND_STATUS_PENDING}' ORDER BY created_at"
        )

    # -- connection lifecycle ---------------------------------------------- #

    async def _ensure_connection(self) -> Any:
        """Return the cached connection, opening it on first use via ``connect``."""
        if self._connection is None:
            self._connection = await self._connect()
        return self._connection

    async def _drop_connection(self) -> None:
        """Close and forget the cached connection so the NEXT call reconnects."""
        connection = self._connection
        self._connection = None
        if connection is not None:
            await self._safe_close(connection)

    @staticmethod
    async def _safe_close(connection: Any) -> None:
        """Close ``connection``, swallowing an already-dead-socket failure."""
        try:
            await connection.close()
        except (*_CONNECTION_ERRORS, KeyError):
            logger.debug("command_subscriber.close.already_closed")

    # -- draining / dispatch ------------------------------------------------ #

    async def process_pending_once(self) -> int:
        """Dispatch every currently-``pending`` command exactly once.

        Selects the pending rows, hands each to ``handler``, and marks it
        ``done`` — or ``failed`` (recording the error) when the handler raises.
        A degenerate empty queue is a no-op that returns ``0``. Serialised on the
        drain lock so it never races the live-notification drain.

        Returns:
            The number of pending commands processed this pass.
        """
        connection = await self._ensure_connection()
        return await self._drain_pending(connection)

    async def _drain_pending(self, connection: Any) -> int:
        """Select + dispatch + stamp every pending command under the drain lock.

        The pending SELECT routes through :func:`_scout_query` (finding #120:
        this is the FIRST statement of every poll — an unretried conflict here
        raised a raw SDK error straight out of the drain, which kills the
        subscriber). A genuine transport fault is reclassified nowhere: it
        propagates in its RAW SDK type, exactly as before, so :meth:`run`'s
        reconnect ladder (built on the raw types) still catches it.
        """
        async with self._drain_lock:
            result = await _scout_query(connection, self._pending_select_statement())
            processed = 0
            for row in self._rows(result):
                await self._dispatch(connection, row)
                processed += 1
            return processed

    async def _dispatch(self, connection: Any, row: dict[str, Any]) -> None:
        """Run one command's handler, then stamp its terminal status.

        A handler exception (an unknown kind, or a genuine mid-flight failure)
        marks the command ``failed`` with the error recorded and is otherwise
        swallowed — one bad command must never kill the loop.
        """
        command_id = row["id"]
        try:
            await self._handler(row)
        except Exception as error:  # noqa: BLE001 - a bad command is failed, not fatal
            await self._mark(connection, command_id, _COMMAND_STATUS_FAILED, error=str(error))
            logger.warning(
                "command.failed", extra={"command_id": str(command_id), "error": str(error)}
            )
        else:
            await self._mark(connection, command_id, _COMMAND_STATUS_DONE)

    async def _mark(
        self, connection: Any, command_id: Any, status: str, *, error: str | None = None
    ) -> None:
        """Conditionally stamp one command row's terminal status (a CAS claim).

        Marking a row out of ``pending`` is what makes a re-poll idempotent: the
        row leaves the pending set, so it is never dispatched a second time. The
        UPDATE is a conditional CLAIM — ``WHERE status = 'pending' RETURN
        BEFORE`` — so two scout instances racing the SAME command (a deploy
        overlap) can never BOTH succeed: only the FIRST mark matches a still-
        ``pending`` row and claims it (the returned BEFORE snapshot proves the
        claim); a later attempt against an already-terminal row matches nothing
        and returns an empty result. An empty claim means ANOTHER instance
        already completed this command — logged LOUDLY as a duplicate
        completion (never an error, since the row already reached a terminal
        state; the schema's own status ASSERT still ``{pending, done, failed}``
        is untouched by this cycle). This narrows — but, across truly
        concurrent instances, does not eliminate — the double-DISPATCH window;
        exactly-once dispatch is scoped to a SINGLE-instance deployment (the
        module's own single-writer architecture), matching a redundant sweep's
        existing idempotence.

        The CAS routes through :func:`_scout_query` (finding #120/#108): a
        RETRYABLE conflict on the claim is retried transparently — never an
        EMPTY result, which is a lost race with a defined meaning (another
        instance already completed this command) and must NEVER be retried.
        A genuine transport fault propagates in its RAW SDK type, so
        :meth:`run`'s reconnect ladder still catches it.
        """
        params: dict[str, Any] = {
            "command_id": command_id,
            "status": status,
            "pending_status": _COMMAND_STATUS_PENDING,
        }
        set_clauses = ["status = $status", "processed_at = time::now()"]
        if error is not None:
            set_clauses.append("error = $error")
            params["error"] = error
        statement = (
            f"UPDATE $command_id SET {', '.join(set_clauses)} "
            f"WHERE status = $pending_status RETURN BEFORE"
        )
        result = await _scout_query(connection, statement, params)
        if not self._rows(result):
            logger.info(
                "command.duplicate_completion",
                extra={"command_id": str(command_id), "status": status},
            )

    @staticmethod
    def _rows(result: Any) -> list[dict[str, Any]]:
        """Launder a SELECT result into the list of row dicts it carries."""
        if isinstance(result, list):
            return [row for row in result if isinstance(row, dict)]
        return []

    # -- run / stop --------------------------------------------------------- #

    async def run(self) -> None:
        """Serve the command channel until :meth:`stop`, reconnecting on a drop.

        Connects, establishes the filtered LIVE subscription, and runs the poll
        backstop — reconnecting with a bounded exponential backoff after any
        socket drop (whether the connect itself failed or the socket died
        mid-serve), so a transient store outage never permanently wedges the
        channel.

        The ladder ALSO catches :class:`~loremaster.store._txn.TxnContentionExhaustedError`
        (finding #108's removed-behaviour preservation): pre-#108, ANY
        ``SurrealError`` out of a command claim reached this ladder (it is a
        member of :data:`~loremaster.store._txn._CONNECTION_ERRORS`), so
        sustained contention backed off and reconnected same as a transport
        fault. The typed exhaustion error is a ``RuntimeError``, not a member
        of that tuple, so without this it would fly straight past the ladder
        and kill the subscriber where it used to recover.
        """
        self._running = True
        attempt = 0
        try:
            while self._running:
                try:
                    connection = await self._ensure_connection()
                except (*_CONNECTION_ERRORS, KeyError, TxnContentionExhaustedError):
                    # The connect itself failed — back off (bounded) and retry.
                    logger.debug("command_subscriber.connect_failed", exc_info=True)
                    await self._backoff(attempt)
                    attempt += 1
                    continue
                attempt = 0  # a live connection resets the backoff ladder
                try:
                    await self._serve(connection)
                except (*_CONNECTION_ERRORS, KeyError, TxnContentionExhaustedError):
                    # The socket dropped mid-serve, OR sustained contention on a
                    # command claim exhausted the shared seam's retry budget —
                    # reconnect + poll-reconcile the gap (a command inserted
                    # during the drop is recovered exactly once by the re-read
                    # of pending on the new socket).
                    logger.debug("command_subscriber.socket_dropped", exc_info=True)
                    await self._drop_connection()
                    # ``stop()`` flips ``self._running`` from ANOTHER coroutine —
                    # mypy narrows the attribute to ``True`` from the loop guard and
                    # cannot model that cross-coroutine mutation, so it flags this
                    # shutdown-during-drop break as unreachable. It IS reachable at
                    # runtime; keep the guard so a stop mid-reconnect exits at once
                    # rather than sleeping out a backoff first.
                    if not self._running:
                        break  # type: ignore[unreachable]
                    await self._backoff(attempt)
                    attempt += 1
                    continue
                # ``_serve`` returned because ``_running`` went False → shut down.
                break
        finally:
            await self._drop_connection()

    async def _serve(self, connection: Any) -> None:
        """Establish LIVE (best-effort) + run the REQUIRED poll backstop loop.

        Establishing the filtered LIVE subscription re-uses a connection error to
        signal a dead socket (it propagates to :meth:`run`'s reconnect). The live
        notification stream is consumed best-effort in a background task; when it
        is unavailable, the poll loop alone carries the load.

        The establishing SELECT routes through :func:`_scout_query` — the SAME
        call site the pending-command drain and the command CAS use, so
        driving any one of the three watches all three: a RETRYABLE conflict
        is retried transparently; a genuine transport fault propagates in its
        RAW SDK type, unchanged, so :meth:`run`'s reconnect ladder still
        catches it exactly as before.
        """
        live_uuid = await _scout_query(connection, self.live_select_statement())
        live_task = asyncio.create_task(self._consume_live(connection, live_uuid))
        try:
            while self._running:
                await self._drain_pending(connection)
                await self._sleep(self._poll_interval_s)
        finally:
            live_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await live_task
            await self._safe_kill(connection, live_uuid)

    async def _consume_live(self, connection: Any, live_uuid: Any) -> None:
        """Drain pending on each live notification; swallow a subscription drop.

        LIVE is best-effort: an unavailable or dropped subscription is caught
        here (the poll backstop keeps serving) rather than crashing the loop.
        A RETRYABLE conflict on establishing the subscription routes through
        the shared :func:`~loremaster.store._txn.retry_on_conflict` driver;
        sustained contention there is likewise best-effort and falls back to
        "unavailable" rather than crashing the loop.
        """
        try:

            async def _attempt() -> Any:
                try:
                    # ``subscribe_live`` is a COROUTINE returning an async
                    # iterator in the installed SDK, but an async-generator
                    # FUNCTION under the test fake; await the former, iterate
                    # either. ``inspect.isawaitable`` is False for an async
                    # generator (it exposes ``__aiter__``, not ``__await__``).
                    subscription = connection.subscribe_live(live_uuid)
                    if inspect.isawaitable(subscription):
                        subscription = await subscription
                    return subscription
                except (*_CONNECTION_ERRORS, KeyError) as error:
                    if is_retryable_conflict_error(error):
                        raise RetryableConflictSignal() from error
                    raise

            subscription = await retry_on_conflict(_attempt)
            async for _notification in subscription:
                # A pending insert fired — reconcile via the (idempotent) poll
                # path so the live and poll routes can never double-dispatch.
                await self._drain_pending(connection)
        except (*_CONNECTION_ERRORS, KeyError, TxnContentionExhaustedError):
            logger.debug("command_subscriber.live_unavailable", exc_info=True)

    @staticmethod
    async def _safe_kill(connection: Any, live_uuid: Any) -> None:
        """Kill the live query, swallowing a failure on an already-dead socket.

        The kill routes through the shared
        :func:`~loremaster.store._txn.retry_on_conflict` driver so a
        RETRYABLE conflict is retried transparently; this remains BEST-EFFORT
        cleanup, so a genuine transport fault OR sustained contention is
        swallowed the same way (never crashes the caller).
        """

        async def _attempt() -> None:
            try:
                await connection.kill(live_uuid)
            except (*_CONNECTION_ERRORS, KeyError) as error:
                if is_retryable_conflict_error(error):
                    raise RetryableConflictSignal() from error
                raise

        try:
            await retry_on_conflict(_attempt)
        except (*_CONNECTION_ERRORS, KeyError, TxnContentionExhaustedError):
            logger.debug("command_subscriber.kill.already_closed")

    async def _backoff(self, attempt: int) -> None:
        """Sleep a bounded exponential backoff before the next reconnect attempt."""
        delay = min(self._backoff_base_s * (2**attempt), self._max_backoff_s)
        await self._sleep(delay)

    async def stop(self) -> None:
        """Stop the run loop and close the cached connection (idempotent)."""
        self._running = False
        await self._drop_connection()


class Scout:
    """The single-writer daemon: ready the write stack, sweep, watch, serve.

    Fully dependency-injected (the collaborators are constructed by
    :meth:`from_config` in production and by the tests directly) so the startup /
    shutdown / dispatch policy is drivable without a socket.

    Args:
        config: The validated project configuration.
        store: The unified :class:`~loremaster.store.surreal.SurrealStore`.
        manifest: The :class:`~loremaster.index.surreal_manifest.SurrealManifest`.
        code_graph: The :class:`~loremaster.graph_surreal.SurrealCodeGraph`.
        snapshot_stamper: The :class:`~loremaster.index.snapshots.SnapshotStamper`.
        indexer: The composed :class:`~loremaster.index.indexer.Indexer`.
        reconcile_engine: The :class:`~loremaster.index.reconcile.ReconcileEngine`.
        watcher: The :class:`~loremaster.index.watcher.LiveWatcher` whose
            ``run_sweep`` (single-writer-locked) both the initial sweep and a
            reconcile command drive.
        command_subscriber: The :class:`CommandSubscriber` serving the out-of-band
            command channel.
        sleep: The awaitable delay seam for the periodic reconcile loop
            (injectable for tests); defaults to :func:`asyncio.sleep`.
    """

    def __init__(
        self,
        *,
        config: LoreConfig,
        store: Any,
        manifest: Any,
        code_graph: Any,
        snapshot_stamper: Any,
        indexer: Any,
        reconcile_engine: Any,
        watcher: Any,
        command_subscriber: Any,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._config = config
        self._store = store
        self._manifest = manifest
        self._code_graph = code_graph
        self._snapshot_stamper = snapshot_stamper
        # Public: the composition-root test reads ``indexer._snapshot_stamper`` /
        # ``reconcile_engine._snapshot_stamper`` to prove the stamper is wired.
        self.indexer = indexer
        self.reconcile_engine = reconcile_engine
        self._watcher = watcher
        self._command_subscriber = command_subscriber
        self._sleep = sleep
        # Background-task handles + lifecycle flags.
        self._subscriber_task: asyncio.Task[None] | None = None
        self._reconcile_task: asyncio.Task[None] | None = None
        self._watcher_started = False
        self._shutdown_event: asyncio.Event | None = None

    # -- composition root --------------------------------------------------- #

    @classmethod
    def from_config(
        cls, config: LoreConfig, *, snapshot_root: Path, embedder: Any
    ) -> Scout:
        """Compose the FULL write stack from ``config`` (construction only — no I/O).

        Builds the store / manifest / code-graph / snapshot-stamper / indexer /
        reconcile-engine / live-watcher and the command subscriber, injecting the
        ONE snapshot stamper into BOTH the indexer and the reconcile engine (the
        C4-audit #2 wiring — an unwired stamper stamps nothing). Readiness is
        :meth:`start`'s job, so nothing here opens a socket.

        ``loremaster.server`` (which imports FastMCP) is imported LAZILY here so
        merely importing this module never drags in the read-side server stack.

        Args:
            config: The validated project configuration.
            snapshot_root: The static-tier snapshot root.
            embedder: The active embedder to inject into the indexer.

        Returns:
            The fully-wired :class:`Scout`.
        """
        # Lazy imports: the composed chunker registry + source providers live in
        # ``loremaster.server`` / ``loremaster.index.cli``, which pull FastMCP.
        # Importing them here (not at module top) keeps ``import loremaster.scout``
        # FastMCP-free — the scout has no HTTP surface.
        from loremaster.index.cli import _source_providers
        from loremaster.server import LoreServer

        surreal_user = resolve_secret(config.surreal.user_env)
        surreal_password = resolve_secret(config.surreal.password_env)
        database = config.effective_surreal_database
        project_root = Path(config.project.root)

        store = SurrealStore(
            url=config.surreal.url,
            namespace=config.surreal.namespace,
            database=database,
            dim=config.embedding.dim,
            user=surreal_user,
            password=surreal_password,
        )
        manifest = SurrealManifest(
            url=config.surreal.url,
            namespace=config.surreal.namespace,
            database=database,
            user=surreal_user,
            password=surreal_password,
        )
        tier_roots, project_roots = graph_roots(config, snapshot_root)
        code_graph = SurrealCodeGraph(
            url=config.surreal.url,
            namespace=config.surreal.namespace,
            database=database,
            user=surreal_user,
            password=surreal_password,
            tier_roots=tier_roots,
            project_roots=project_roots,
        )
        # ONE stamper, injected into BOTH write paths below (C4-audit #2).
        snapshot_stamper = SnapshotStamper(
            url=config.surreal.url,
            namespace=config.surreal.namespace,
            database=database,
            user=surreal_user,
            password=surreal_password,
            store=store,
            manifest=manifest,
            project_root=project_root,
        )
        server = LoreServer(config)
        indexer = Indexer(
            store=store,
            embedder=embedder,
            manifest=manifest,
            registry=server.registry,
            source_providers=_source_providers(server, config),
            config=config,
            snapshot_root=snapshot_root,
            code_graph=code_graph,
            snapshot_stamper=snapshot_stamper,
        )
        reconcile_engine = ReconcileEngine(
            indexer=indexer,
            manifest=manifest,
            store=store,
            config=config,
            code_graph=code_graph,
            snapshot_stamper=snapshot_stamper,
        )
        watcher = LiveWatcher(
            indexer=indexer,
            manifest=manifest,
            store=store,
            config=config,
            loop=asyncio.get_running_loop(),
            reconcile_engine=reconcile_engine,
            code_graph=code_graph,
        )
        # The command subscriber dispatches to the not-yet-constructed scout's
        # ``handle_command`` via a late-bound forwarder (the scout owns the
        # dispatch policy; the subscriber owns the transport).
        holder: dict[str, Scout] = {}

        async def _dispatch(command: dict[str, Any]) -> None:
            await holder["scout"].handle_command(command)

        command_subscriber = CommandSubscriber(
            connect=lambda: _open_command_connection(
                url=config.surreal.url,
                namespace=config.surreal.namespace,
                database=database,
                user=surreal_user,
                password=surreal_password,
            ),
            handler=_dispatch,
            poll_interval_s=_DEFAULT_COMMAND_POLL_INTERVAL_S,
        )
        scout = cls(
            config=config,
            store=store,
            manifest=manifest,
            code_graph=code_graph,
            snapshot_stamper=snapshot_stamper,
            indexer=indexer,
            reconcile_engine=reconcile_engine,
            watcher=watcher,
            command_subscriber=command_subscriber,
        )
        holder["scout"] = scout
        return scout

    # -- the four write backends, in ready/close order ---------------------- #

    def _write_backends(self) -> tuple[Any, ...]:
        """The four write backends in READY order (close reverses this)."""
        return (self._store, self._manifest, self._code_graph, self._snapshot_stamper)

    # -- startup ------------------------------------------------------------ #

    async def start(self) -> None:
        """Ready the write stack, run the eager initial sweep, then go live.

        Readies all four write backends BEFORE the first sweep (a sweep against
        an un-readied store would query a schemaless database); a mid-startup
        ready failure closes every backend already opened and re-raises the typed
        error, so a failed startup leaks no live connection. The command channel
        starts in BOTH the enabled and the sweep-only modes; only when the
        watcher is enabled do the live observer and the periodic reconcile loop
        start.

        Raises:
            SurrealConnectionError: A backend was unreachable at ready time (the
                typed error the store raises, surfaced unchanged).
        """
        readied: list[Any] = []
        try:
            for backend in self._write_backends():
                await backend.ensure_ready()
                readied.append(backend)
        except BaseException:
            # Close what opened, newest-first, before re-raising the typed error.
            for backend in reversed(readied):
                with contextlib.suppress(Exception):
                    await backend.close()
            raise

        # Eager initial sweep: a fresh start after offline edits delta-indexes NOW
        # (via the single-writer ``run_sweep``), not after the periodic interval.
        await self._watcher.run_sweep()

        # The command channel serves in BOTH modes (enabled + sweep-only).
        self._subscriber_task = asyncio.create_task(self._command_subscriber.run())

        # The live observer + periodic reconcile run ONLY when the watcher is
        # enabled; a ``watcher: {enabled: false}`` corpus is indexed once above
        # but never live-watched (no inotify observer, no periodic reconcile).
        if self._config.watcher.enabled:
            await self._watcher.start()
            self._watcher_started = True
            self._reconcile_task = asyncio.create_task(self._periodic_reconcile())

    async def _periodic_reconcile(self) -> None:
        """Run a reconcile sweep every ``reconcile_interval_s`` SECONDS.

        Sleeps the interval FIRST (the eager sweep already ran at start), then
        reconciles under the watcher's single-writer lock — the downtime /
        ``IN_Q_OVERFLOW`` backstop. A transient sweep failure is swallowed +
        logged so one blip cannot permanently kill the backstop; the next
        interval retries over the self-healed connection.
        """
        interval_s = self._config.watcher.reconcile_interval_s
        while True:
            await self._sleep(interval_s)
            try:
                await self._watcher.run_sweep()
            except Exception:  # noqa: BLE001 - one blip must not kill the backstop
                logger.exception("scout.periodic_reconcile.sweep_failed")

    # -- command dispatch policy -------------------------------------------- #

    async def handle_command(self, command: dict[str, Any]) -> None:
        """Map a command's ``kind`` to an action under the writer lock.

        ``reconcile`` runs a real reconcile sweep via the watcher's
        single-writer ``run_sweep`` — so a command sweep never races the periodic
        sweep (both serialise on the watcher's lock). Any other kind is an
        :class:`UnknownCommandError` that NAMES the offending kind.

        Args:
            command: The command row (``kind`` + ``payload``).

        Raises:
            UnknownCommandError: The ``kind`` is not a recognised command.
        """
        kind = command.get("kind")
        if kind == _RECONCILE_COMMAND_KIND:
            await self._watcher.run_sweep()
            return
        raise UnknownCommandError(f"unknown command kind: {kind!r}")

    # -- shutdown ----------------------------------------------------------- #

    async def stop(self) -> None:
        """Settle background work: periodic loop, command channel, watcher.

        Stopping the watcher settles its spawned overflow tasks (the #16
        contract) and the command subscriber is cancelled — so no scout-spawned
        task outlives ``stop`` to touch a soon-to-be-closed connection.
        """
        if self._reconcile_task is not None:
            self._reconcile_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reconcile_task
            self._reconcile_task = None

        await self._command_subscriber.stop()
        if self._subscriber_task is not None:
            self._subscriber_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._subscriber_task
            self._subscriber_task = None

        if self._watcher_started:
            await self._watcher.stop()
            self._watcher_started = False

    async def aclose(self) -> None:
        """Close every write connection (newest-readied first). Idempotent."""
        for backend in reversed(self._write_backends()):
            with contextlib.suppress(Exception):
                await backend.close()

    # -- process lifecycle -------------------------------------------------- #

    def request_shutdown(self) -> None:
        """Unblock :meth:`run` (a signal handler / an explicit teardown request)."""
        if self._shutdown_event is not None:
            self._shutdown_event.set()

    async def run(self) -> None:
        """The process lifecycle: start → await a shutdown signal → stop + aclose.

        Installs a clean shutdown on BOTH SIGTERM and SIGINT (via
        ``loop.add_signal_handler``), starts the daemon, and blocks until a
        signal (or :meth:`request_shutdown`) fires — then tears the daemon down
        (settle background work + close every connection) and removes the
        handlers.
        """
        loop = asyncio.get_running_loop()
        self._shutdown_event = asyncio.Event()
        for sig in _SHUTDOWN_SIGNALS:
            # Signal registration is unavailable off the main thread / on some
            # platforms; a daemon that cannot self-install still runs (an
            # explicit ``request_shutdown`` tears it down).
            with contextlib.suppress(NotImplementedError, ValueError, RuntimeError):
                loop.add_signal_handler(sig, self.request_shutdown)
        try:
            await self.start()
            await self._shutdown_event.wait()
        finally:
            for sig in _SHUTDOWN_SIGNALS:
                with contextlib.suppress(NotImplementedError, ValueError, RuntimeError):
                    loop.remove_signal_handler(sig)
            await self.stop()
            await self.aclose()


def build_parser() -> argparse.ArgumentParser:
    """Build the ``python -m loremaster.scout`` argparse parser.

    Returns:
        The configured parser. ``--config`` (required) is the path to
        ``lore.yaml``; ``--snapshot-root`` (optional, default ``None``) overrides
        the static-tier snapshot root, the impl substituting its own default when
        omitted.
    """
    parser = argparse.ArgumentParser(
        prog="loremaster.scout",
        description="Run the single-writer scout daemon over a project's lore index.",
    )
    parser.add_argument(
        "--config", required=True, help="Path to the project lore.yaml configuration."
    )
    parser.add_argument(
        "--snapshot-root",
        default=None,
        help="Static-tier snapshot root (default: ~/docker/mcp/lore-snapshot).",
    )
    return parser


async def _run_scout(config: LoreConfig, snapshot_root: Path) -> None:
    """Compose the scout inside the running loop and run it until shutdown.

    ``from_config`` builds the live watcher (which binds to the running loop), so
    it is called HERE — under :func:`asyncio.run` — not before the loop exists.
    Tolerant of a sync OR async ``from_config``.
    """
    embedder = make_embedder_from_config(config.embedding)
    built = Scout.from_config(config, snapshot_root=snapshot_root, embedder=embedder)
    scout = await built if inspect.isawaitable(built) else built
    await scout.run()


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint: parse args, compose the scout, run it until shutdown.

    Args:
        argv: Optional explicit argument vector (for tests); defaults to
            ``sys.argv[1:]``.

    Returns:
        Process exit code (``0`` on a clean, signal-driven shutdown).
    """
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    snapshot_root = Path(args.snapshot_root) if args.snapshot_root else _DEFAULT_SNAPSHOT_ROOT
    asyncio.run(_run_scout(config, snapshot_root))
    return 0


# The ``__main__`` guard MUST be the LAST top-level statement in this module: run
# as ``python -m loremaster.scout`` it fires ``sys.exit(main())``, and ANY
# module-level def/binding placed AFTER it never executes in the running process.
# ``TestScoutMainGuard.test_main_guard_is_last_top_level_statement`` enforces it.
if __name__ == "__main__":
    import sys

    sys.exit(main())
