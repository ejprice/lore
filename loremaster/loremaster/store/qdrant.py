"""Async Qdrant store for a per-project ``lore_<slug>`` collection (tiered, C1).

The eventual lore MCP server is a single asyncio process, so the store is built
on :class:`~qdrant_client.AsyncQdrantClient`. The collection name (``lore_<slug>``)
is injected, never hard-coded, so one store class serves every project.

Amendment deltas:

* **C1 — ``tier`` is a payload + key dimension.** ``ensure_collection`` adds a
  KEYWORD index on ``tier`` (alongside ``file_path``/``content_hash``/
  ``chunk_type``), ``delete_by_file`` deletes by the ``(tier, file_path)`` pair
  (so a custom override and the community original of one path are independently
  purgeable), and a new ``delete_by_tier`` purges an entire tier — the per-tier
  rebuild primitive (loremaster's analog of odoo-code's ``preserve_tiers``).
* **Extension-declared payload indexes (seam 8).** Beyond the base fields, an
  extension may declare extra KEYWORD fields (e.g. ``model_name``) and/or BOOL
  fields (e.g. ``is_installed``) to index. These are created on the server in
  ``ensure_collection``.

The payload indexes are load-bearing against a real server: ``delete_by_file``
and ``delete_by_tier`` are filter-based deletes, which need the ``file_path`` and
``tier`` indexes to be efficient and correct. (They are no-ops in the in-memory
backend, which is exactly why the contract tests run against the real server.)
"""

from __future__ import annotations

import asyncio
import functools
import logging
from collections.abc import Awaitable, Callable, Sequence
from typing import TypeVar

import httpx
from qdrant_client import AsyncQdrantClient
from qdrant_client import models as qmodels
from qdrant_client.common.client_exceptions import ResourceExhaustedResponse
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse
from qdrant_client.models import ScoredPoint

from loremaster.index.records import Record

logger = logging.getLogger(__name__)

# Return type of a wrapped network op (each store method wraps its own client call).
_T = TypeVar("_T")

# An awaitable sleep used for backoff between retries; injected in tests so the
# suite never really waits. Mirrors ``loresigil.resilient.SleepFn``.
SleepFn = Callable[[float], Awaitable[None]]

# Exponential-backoff schedule, mirroring ``loresigil.resilient``: the delay
# before retry N is ``BACKOFF_BASE_S * BACKOFF_GROWTH ** N`` seconds, capped at
# ``BACKOFF_CAP_S`` so a long Qdrant outage doesn't produce absurd sleeps.
BACKOFF_BASE_S: float = 1.0
BACKOFF_GROWTH: float = 2.0
BACKOFF_CAP_S: float = 30.0

# Maximum attempts for a transient store op before the last error is re-raised.
_DEFAULT_MAX_RETRIES = 5

# The HTTP status floor at/above which an ``UnexpectedResponse`` is a TRANSIENT
# server-side error worth retrying; a status below it (a 4xx — bad request, dim
# mismatch) is PERMANENT and fails fast (never retried).
_HTTP_SERVER_ERROR_FLOOR = 500

# Prefix for every per-project collection name: ``lore_<slug>``.
_COLLECTION_PREFIX = "lore_"

# Base payload fields that always receive a KEYWORD index. ``tier`` powers
# delete-by-tier and tier filtering; ``file_path`` powers delete-by-file;
# ``content_hash`` and ``chunk_type`` power staleness checks and typed filtering.
_BASE_KEYWORD_INDEXED_FIELDS = ("tier", "file_path", "content_hash", "chunk_type")

# Payload keys the delete filters match on.
_TIER_KEY = "tier"
_FILE_PATH_KEY = "file_path"

# Default number of points per upsert request.
_DEFAULT_BATCH_SIZE = 64

# Default page size when scrolling EVERY point in a collection. A backfill
# sweep (FP-06) pages the whole memory collection; a moderate page bounds the
# per-call response size while keeping the round-trip count small for a typical
# project's memory count.
_DEFAULT_SCROLL_PAGE = 256


class QdrantStore:
    """Async wrapper over a single ``lore_<slug>`` Qdrant collection (tiered).

    Args:
        client: The (already-constructed) async Qdrant client. Injecting it lets
            tests pass a real-server client and the server pass its own.
        slug: The project slug; the collection is named ``lore_<slug>``.
        batch_size: Maximum points per upsert request.
        extra_keyword_indexes: Extension-declared extra KEYWORD payload fields to
            index (seam 8), on top of the base fields.
        extra_bool_indexes: Extension-declared extra BOOL payload fields to index.
        max_retries: Maximum attempts for a TRANSIENT (5xx / transport) failure of
            a network op before the last error is re-raised. Bounds the retry so a
            persistent outage fails cleanly instead of looping forever.
        sleep_fn: Awaitable backoff sleep between retries; defaults to
            :func:`asyncio.sleep` (injected in tests so retries don't block).
    """

    def __init__(
        self,
        *,
        client: AsyncQdrantClient,
        slug: str,
        batch_size: int = _DEFAULT_BATCH_SIZE,
        extra_keyword_indexes: Sequence[str] | None = None,
        extra_bool_indexes: Sequence[str] | None = None,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        sleep_fn: SleepFn | None = None,
    ) -> None:
        self._client = client
        self._collection_name = f"{_COLLECTION_PREFIX}{slug}"
        self._batch_size = batch_size
        self._extra_keyword_indexes = tuple(extra_keyword_indexes or ())
        self._extra_bool_indexes = tuple(extra_bool_indexes or ())
        # Resilience knobs (Layer 1): a transient Qdrant failure (5xx / transport
        # drop) is retried with capped exponential backoff up to ``max_retries``,
        # then the last error is re-raised; a permanent (4xx) failure fails fast.
        # ``sleep_fn`` is injectable so tests don't really sleep between retries.
        self._max_retries = max_retries
        self._sleep_fn: SleepFn = sleep_fn or asyncio.sleep

    @property
    def collection_name(self) -> str:
        """The injected collection name (``lore_<slug>``)."""
        return self._collection_name

    # -- transient-failure retry wrapper (Layer 1) -------------------------

    @staticmethod
    def _is_transient(error: BaseException) -> bool:
        """True iff ``error`` is a TRANSIENT Qdrant failure worth retrying.

        Transient (a momentary server/transport hiccup that a retry can clear):

        * ``UnexpectedResponse`` carrying a 5xx status (the cold-index crash was a
          ``500 Internal Server Error`` — "task panicked").
        * ``ResourceExhaustedResponse`` — qdrant-client raises THIS (a
          ``QdrantException``, NOT an ``UnexpectedResponse``) for a 429 that
          carries a ``Retry-After`` header: the textbook "server overloaded, back
          off and retry" signal — the MOST explicitly transient failure there is.
          Its ``retry_after_s`` tells us how long the server wants us to wait
          (honored by :meth:`_backoff_delay`). (A 429 WITHOUT ``Retry-After`` is a
          4xx ``UnexpectedResponse`` instead — permanent, below.)
        * ``httpx.ConnectError`` and any ``httpx.TimeoutException`` (read / pool /
          connect timeouts all subclass it) — a dropped or stalled connection.
        * ``ResponseHandlingException`` — the qdrant-client wrapper around a
          transport/parse failure.

        PERMANENT (never retried — a retry can only repeat the same outcome):

        * ``UnexpectedResponse`` with a 4xx status (bad request, dimension
          mismatch). These fail fast so a real client/data bug surfaces at once.
        """
        if isinstance(error, UnexpectedResponse):
            status = error.status_code
            return status is not None and status >= _HTTP_SERVER_ERROR_FLOOR
        return isinstance(
            error,
            (
                ResourceExhaustedResponse,
                httpx.ConnectError,
                httpx.TimeoutException,
                ResponseHandlingException,
            ),
        )

    @staticmethod
    def _backoff_delay(error: BaseException, attempt: int) -> float:
        """The seconds to wait before retrying ``error`` on a 0-based ``attempt``.

        When the server told us exactly how long to wait — a
        ``ResourceExhaustedResponse`` carries the 429 ``Retry-After`` value as
        ``retry_after_s`` — HONOR that (retrying sooner than permitted just earns
        another 429). Otherwise fall back to the capped exponential schedule
        (``BACKOFF_BASE_S * BACKOFF_GROWTH ** attempt``). Either way the result is
        clamped to ``BACKOFF_CAP_S`` so a hostile/huge ``Retry-After`` can't stall
        the indexer indefinitely.

        Args:
            error: The transient error that triggered the retry.
            attempt: The 0-based attempt index that just failed.

        Returns:
            The (capped) backoff delay in seconds.
        """
        if isinstance(error, ResourceExhaustedResponse):
            return min(float(error.retry_after_s), BACKOFF_CAP_S)
        return min(BACKOFF_BASE_S * (BACKOFF_GROWTH**attempt), BACKOFF_CAP_S)

    async def _with_retry(
        self, op_name: str, op: Callable[[], Awaitable[_T]]
    ) -> _T:
        """Run ``op``, retrying a TRANSIENT failure with capped exponential backoff.

        Every network op routes its leaf client call through here so a single
        transient Qdrant hiccup no longer kills a long batch index. A transient
        failure backs off (``BACKOFF_BASE_S * BACKOFF_GROWTH ** attempt`` seconds,
        capped at ``BACKOFF_CAP_S``) and retries up to ``max_retries`` attempts;
        the budget is bounded so a persistent outage re-raises the LAST error
        rather than looping forever. A PERMANENT (4xx) failure — or any
        non-Qdrant error — propagates immediately, unretried.

        Args:
            op_name: A short static label for the structured retry/giveup events
                (e.g. ``"upsert"``) — never carries payload or response data.
            op: A zero-argument coroutine performing exactly one client call.

        Returns:
            The op's result on the first success.

        Raises:
            BaseException: The last transient error after the budget is exhausted,
                or any permanent / non-transient error immediately.
        """
        for attempt in range(self._max_retries):
            try:
                return await op()
            except BaseException as error:  # noqa: BLE001 - re-raised below if not transient
                last_attempt = attempt == self._max_retries - 1
                if not self._is_transient(error) or last_attempt:
                    raise
                delay = self._backoff_delay(error, attempt)
                logger.warning(
                    "store.retry.backoff",
                    extra={"op": op_name, "attempt": attempt, "delay_s": delay},
                )
                await self._sleep_fn(delay)
        # Unreachable: ``max_retries >= 1`` always returns or raises in the loop.
        raise AssertionError(f"retry loop for {op_name!r} exited without result")

    async def ensure_collection(self, dim: int) -> None:
        """Create the collection (cosine, size=``dim``) and its payload indexes.

        Idempotent: if the collection already exists, this is a no-op for the
        collection itself; the payload-index calls are issued regardless and are
        themselves idempotent on a real server. Registers the base KEYWORD
        indexes plus every extension-declared extra KEYWORD/BOOL index.

        Args:
            dim: The vector dimensionality (must match the embedder + config).
        """
        if not await self._with_retry(
            "collection_exists",
            lambda: self._client.collection_exists(self._collection_name),
        ):
            await self._with_retry(
                "create_collection",
                lambda: self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=dim, distance=qmodels.Distance.COSINE
                    ),
                ),
            )
        for field_name in (*_BASE_KEYWORD_INDEXED_FIELDS, *self._extra_keyword_indexes):
            # functools.partial binds the loop variable eagerly (no late-binding
            # closure bug) and gives the retry wrapper a typed zero-arg callable.
            await self._with_retry(
                "create_payload_index",
                functools.partial(
                    self._client.create_payload_index,
                    collection_name=self._collection_name,
                    field_name=field_name,
                    field_schema=qmodels.PayloadSchemaType.KEYWORD,
                ),
            )
        for field_name in self._extra_bool_indexes:
            await self._with_retry(
                "create_payload_index",
                functools.partial(
                    self._client.create_payload_index,
                    collection_name=self._collection_name,
                    field_name=field_name,
                    field_schema=qmodels.PayloadSchemaType.BOOL,
                ),
            )

    async def collection_dim(self) -> int | None:
        """Return the collection's configured vector size, or ``None`` if absent.

        This is the input to the startup dim-coherence gate: the server compares
        it against ``config.dim`` and the live probe, refusing to start on a
        mismatch (never auto-recreating).

        Returns:
            The vector size, or ``None`` when the collection does not exist.
        """
        if not await self._with_retry(
            "collection_exists",
            lambda: self._client.collection_exists(self._collection_name),
        ):
            return None
        info = await self._with_retry(
            "get_collection",
            lambda: self._client.get_collection(self._collection_name),
        )
        vectors = info.config.params.vectors
        # A single (unnamed) vector config exposes ``.size`` directly; a named
        # multi-vector config would be a dict, which lore never uses.
        if isinstance(vectors, qmodels.VectorParams):
            return vectors.size
        raise TypeError(
            f"Collection {self._collection_name!r} uses named vectors; "
            f"lore expects a single unnamed vector."
        )

    async def count_points(self, tier: str | None = None) -> int:
        """Return the LIVE point count in the collection — the independent oracle.

        Reads the SERVER's count, NEVER the manifest. This is the count the
        store-divergence reconcile and the FP-10 empty-index decision must consult
        instead of trusting the manifest (which is precisely what lies when the
        collection is wiped). When ``tier`` is given the count is filtered on the
        ``tier`` payload keyword index (the per-tier divergence check); ``None``
        returns the grand total (the FP-10 empty check). Zero when the collection
        is absent or empty.

        Args:
            tier: The tier to count points for (filtered on the ``tier`` payload
                index); ``None`` returns the whole-collection total.

        Returns:
            The live point count from the server.
        """
        # An absent collection has nothing to count — the wiped-and-not-recreated
        # shape — so report 0 rather than letting the count call 404.
        if not await self._with_retry(
            "collection_exists",
            lambda: self._client.collection_exists(self._collection_name),
        ):
            return 0
        # A tier scope filters on the SAME ``tier`` payload keyword index that
        # delete_by_tier / search use (never a hand-copied key); ``None`` counts
        # the whole collection (the FP-10 grand total).
        count_filter = self._build_filter({_TIER_KEY: tier}) if tier is not None else None
        result = await self._with_retry(
            "count",
            functools.partial(
                self._client.count,
                collection_name=self._collection_name,
                count_filter=count_filter,
                exact=True,
            ),
        )
        return result.count

    async def upsert(self, records: Sequence[tuple[Record, list[float]]]) -> None:
        """Upsert ``(record, vector)`` pairs, batched to ``batch_size`` per call.

        The deterministic, tier-keyed point id means a re-upsert of an unchanged
        chunk overwrites in place rather than duplicating, and two tiers' copies
        of one path never collide.

        Args:
            records: ``(Record, vector)`` pairs to persist.
        """
        for start in range(0, len(records), self._batch_size):
            batch = records[start : start + self._batch_size]
            points = [
                qmodels.PointStruct(
                    id=record.point_id, vector=vector, payload=record.payload
                )
                for record, vector in batch
            ]
            if points:
                # ``partial`` binds this batch's points eagerly so a retry re-sends
                # exactly this batch (not a later loop iteration's points).
                await self._with_retry(
                    "upsert",
                    functools.partial(
                        self._client.upsert,
                        collection_name=self._collection_name,
                        points=points,
                    ),
                )

    async def search(
        self,
        vector: list[float],
        k: int,
        filters: dict[str, str] | None = None,
    ) -> list[ScoredPoint]:
        """Return the ``k`` nearest points to ``vector``, optionally filtered.

        Args:
            vector: The query vector.
            k: The maximum number of results.
            filters: Optional payload keyword filters (field → exact value); all
                supplied conditions must match (logical AND). Useful for a
                tier-scoped search (``{"tier": ...}``).

        Returns:
            The scored points, nearest first.
        """
        query_filter = self._build_filter(filters) if filters else None
        result = await self._with_retry(
            "query_points",
            lambda: self._client.query_points(
                collection_name=self._collection_name,
                query=vector,
                limit=k,
                query_filter=query_filter,
                with_payload=True,
            ),
        )
        return list(result.points)

    async def scroll(
        self,
        filters: dict[str, str],
        limit: int,
    ) -> list[qmodels.Record]:
        """Return up to ``limit`` points matching ``filters`` — a FILTER-ONLY lookup.

        Unlike :meth:`search` (a vector nearest-neighbour query), this is a pure
        payload-filter scroll with NO query vector — the primitive ``get_symbol``
        needs to find a symbol's chunk by its exact ``(identity, chunk_type)``
        without anything to embed. All supplied conditions must match (logical
        AND) against the KEYWORD payload indexes; payloads are returned (the
        caller reads ``source_text``/location off them).

        Args:
            filters: Payload keyword filters (field → exact value); AND-combined.
            limit: The maximum number of points to return.

        Returns:
            The matching points (payloads included), capped at ``limit``; ``[]``
            when nothing matches.
        """
        points, _next_page = await self._with_retry(
            "scroll",
            lambda: self._client.scroll(
                collection_name=self._collection_name,
                scroll_filter=self._build_filter(filters),
                limit=limit,
                with_payload=True,
                with_vectors=False,
            ),
        )
        return list(points)

    async def scroll_all(
        self, page_size: int = _DEFAULT_SCROLL_PAGE
    ) -> list[qmodels.Record]:
        """Return EVERY point in the collection (payloads included), unfiltered.

        Unlike :meth:`scroll` (a single bounded, FILTERED page), this pages the
        WHOLE collection by following the scroll cursor until it is exhausted —
        the primitive the FP-06 ledger backfill needs to read every pre-existing
        memory point's payload. An ABSENT collection has nothing to scroll, so it
        reports ``[]`` rather than letting the scroll call 404 (mirroring
        :meth:`count_points`). Vectors are NOT fetched (the backfill re-embeds
        from the payload's note text), keeping the response small.

        Args:
            page_size: The maximum points fetched per round-trip; the cursor is
                followed across pages until the collection is exhausted.

        Returns:
            Every point in the collection (payloads included); ``[]`` when the
            collection is absent or empty.
        """
        # An absent collection has nothing to scroll — the wiped-and-not-recreated
        # shape — so report an empty list rather than letting the scroll 404.
        if not await self._with_retry(
            "collection_exists",
            lambda: self._client.collection_exists(self._collection_name),
        ):
            return []
        all_points: list[qmodels.Record] = []
        # ``offset`` is Qdrant's opaque scroll cursor: ``None`` starts at the
        # beginning, and each page returns the cursor for the NEXT page (``None``
        # once the collection is exhausted).
        offset: qmodels.ExtendedPointId | None = None
        while True:
            points, next_offset = await self._with_retry(
                "scroll",
                functools.partial(
                    self._client.scroll,
                    collection_name=self._collection_name,
                    limit=page_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,
                ),
            )
            all_points.extend(points)
            if next_offset is None:
                break
            offset = next_offset
        return all_points

    async def delete_by_file(self, tier: str, file_path: str) -> None:
        """Purge every point matching ``(tier, file_path)`` exactly.

        Implemented as a :class:`FilterSelector` AND-matching both the ``tier``
        and ``file_path`` keyword indexes, so a custom override of a community
        file purges only the named tier's copy — the other tier's copy of the
        same path survives. A pair with no points is a harmless no-op.

        Args:
            tier: The tier whose copy of the file to purge.
            file_path: The payload ``file_path`` value to purge within that tier.
        """
        await self._with_retry(
            "delete_by_file",
            lambda: self._client.delete(
                collection_name=self._collection_name,
                points_selector=qmodels.FilterSelector(
                    filter=self._build_filter({_TIER_KEY: tier, _FILE_PATH_KEY: file_path})
                ),
            ),
        )

    async def delete_points(self, point_ids: Sequence[str]) -> None:
        """Purge exactly the named point ids — the upsert-before-purge enabler.

        A per-file update upserts the NEW chunks first (so a concurrent reader
        never sees a gap) and then purges only the STALE ids (the old point ids
        no longer produced by the file). Deleting by ``(tier, file_path)`` would
        purge the just-upserted new points too; deleting the explicit stale ids
        keeps the new content continuously visible. An empty list is a harmless
        no-op (the common "nothing went stale" case), issuing no request.

        Args:
            point_ids: The exact point ids to delete (typically ``old − new``).
        """
        if not point_ids:
            return
        await self._with_retry(
            "delete_points",
            lambda: self._client.delete(
                collection_name=self._collection_name,
                points_selector=qmodels.PointIdsList(points=list(point_ids)),
            ),
        )

    async def delete_by_tier(self, tier: str) -> None:
        """Purge every point belonging to ``tier`` — the per-tier rebuild primitive.

        A static tier's version-stamp bump rebuilds that tier without disturbing
        the others: ``delete_by_tier(X)`` then re-add. Implemented as a
        :class:`FilterSelector` on the ``tier`` keyword index. A tier with no
        points is a harmless no-op.

        Args:
            tier: The tier to purge entirely.
        """
        await self._with_retry(
            "delete_by_tier",
            lambda: self._client.delete(
                collection_name=self._collection_name,
                points_selector=qmodels.FilterSelector(
                    filter=self._build_filter({_TIER_KEY: tier})
                ),
            ),
        )

    @staticmethod
    def _build_filter(filters: dict[str, str]) -> qmodels.Filter:
        """Build an AND-combined keyword-match filter from a field→value mapping."""
        return qmodels.Filter(
            must=[
                qmodels.FieldCondition(key=key, match=qmodels.MatchValue(value=value))
                for key, value in filters.items()
            ]
        )
