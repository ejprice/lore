"""THE stamp-group paging rule for the rollup's cursor-paged legs (RULING-15 / R44, finding #591).

The rollup pages three ledgers by a stamp column under ONE exclusive cursor (``col > $since``): tasks by
``updated_at``, findings and messages by ``created_at``. An exclusive instant cannot tell apart rows that
share a stamp, so a page that ENDS INSIDE a stamp group skips the rest of that group forever — the next
call's ``>`` passes over them, and the served bytes read like "no more rows" (#591). The rule here: a page
never ends inside a stamp group.

* Read ``limit + 1`` rows. If the overflow row's stamp differs from the boundary row's, the page is the
  first ``limit`` rows (unchanged). If it is the SAME stamp, SHRINK the page to the rows strictly below that
  stamp; the resume point is the last served stamp, and ``>`` is exact by construction.
* If shrinking leaves nothing (the head group alone is wider than ``limit``), serve its first ``limit`` rows,
  do NOT advance (resume at ``since``), and NAME the group (:class:`HeldStampGroup`: its stamp and size) so
  the render can say "re-call with limit ≥ N". ``limit`` has no ceiling, so that remedy always exists.

Stamps are compared with :func:`stamp_key` — never ``==``/``<`` on the values: SDK 3.0's ``PreciseDatetime``
ignores its nanoseconds in both (measured, build-66 R44), while the engine orders by them.

This module is THE one implementation of the rule (the three ``*_since`` legs call :func:`read_stamp_page`;
a fake store calls :func:`cut_stamp_page`). A second copy is the defect this exists to prevent.

RE-OPEN TRIGGERS → a compound ``(stamp, key)`` cursor (RULING-15 option (a)), recorded as ruled:
  1. the day ``limit`` gains a ceiling — a stamp group larger than the ceiling is then a true dead end;
  2. the day a production write door mints ties ROUTINELY (a task importer, a bulk reaper of a dead agent's
     claims, create-time stamping of many rows in one statement).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from loremaster.store._txn import required_datetime

#: The bound-parameter names this module adds to a leg's query. A caller's filter params must not use them.
_SINCE_PARAM = "stamp_page_since"
_LIMIT_PARAM = "stamp_page_limit"
_GROUP_PARAM = "stamp_page_group"
_RESERVED_PARAMS = frozenset({_SINCE_PARAM, _LIMIT_PARAM, _GROUP_PARAM})


class HeldStampGroup(BaseModel):
    """A head stamp group wider than the page: the cursor holds and the render names it.

    Attributes:
        stamp: The stamp every row of the group shares.
        rows: How many rows (visible to the caller) share it — the ``N`` of "re-call with limit ≥ N".
    """

    model_config = ConfigDict(extra="forbid")

    stamp: datetime
    rows: int


def stamp_key(value: datetime) -> tuple[datetime, int]:
    """The ENGINE's ordering of a stamp: the instant, then the nanoseconds a ``PreciseDatetime`` carries.

    ``PreciseDatetime.__eq__`` / ``__lt__`` compare to the microsecond only (two stamps 1 ns apart compare
    equal), so any decision about ties or order between stamps uses this key.
    """
    return (value, getattr(value, "nanosecond", 0))


@dataclass(frozen=True)
class StampCut[RowT]:
    """The page :func:`cut_stamp_page` chose.

    Attributes:
        rows: The rows to serve (at most ``limit``), never ending inside a stamp group unless ``held_stamp``.
        resume_at: The exact stamp the next page starts after: the last served stamp, or ``since`` when the
            leg served nothing or holds a group.
        held_stamp: The stamp of a head group wider than ``limit`` (the cursor holds), else ``None``.
    """

    rows: list[RowT]
    resume_at: datetime
    held_stamp: datetime | None


def cut_stamp_page[RowT](
    rows: Sequence[RowT], *, limit: int, since: datetime, stamp_of: Callable[[RowT], datetime]
) -> StampCut[RowT]:
    """Choose a leg's page from up to ``limit + 1`` rows ordered by stamp ascending (the pure rule).

    Args:
        rows: The leg's rows strictly after ``since``, stamp-ascending, at most ``limit + 1`` of them.
        limit: The page size (a positive int).
        since: The exclusive cursor the rows were read after.
        stamp_of: The row's stamp.

    Returns:
        The page, its exact resume point, and the held group's stamp when the head group is wider than
        ``limit``.
    """
    if len(rows) <= limit:
        return StampCut(rows=list(rows), resume_at=stamp_of(rows[-1]) if rows else since, held_stamp=None)
    boundary = stamp_key(stamp_of(rows[limit - 1]))
    if stamp_key(stamp_of(rows[limit])) != boundary:
        return StampCut(rows=list(rows[:limit]), resume_at=stamp_of(rows[limit - 1]), held_stamp=None)
    below = [row for row in rows[:limit] if stamp_key(stamp_of(row)) < boundary]
    if below:
        return StampCut(rows=below, resume_at=stamp_of(below[-1]), held_stamp=None)
    return StampCut(rows=list(rows[:limit]), resume_at=since, held_stamp=stamp_of(rows[limit - 1]))


@dataclass(frozen=True)
class StampPage:
    """One leg's page as read from the store by :func:`read_stamp_page`.

    Attributes:
        rows: The raw rows to serve (the caller maps them).
        total: The honest count of every row after ``since`` (visible to the caller's filter).
        resume_at: See :class:`StampCut`.
        held_group: The named head group wider than ``limit``, else ``None``.
    """

    rows: list[dict[str, Any]]
    total: int
    resume_at: datetime
    held_group: HeldStampGroup | None


async def read_stamp_page(  # noqa: PLR0913 - one leg's full description; every argument is required
    query: Callable[[str, dict[str, Any]], Awaitable[Any]],
    *,
    as_rows: Callable[[Any], list[dict[str, Any]]],
    group_count: Callable[[Any], int],
    table: str,
    column: str,
    projection: str,
    since: datetime,
    limit: int,
    filter_fragment: str = "",
    filter_params: Mapping[str, Any] | None = None,
) -> StampPage:
    """Read one cursor-paged rollup leg under THE stamp-group rule (module docstring).

    Runs ``SELECT <projection> FROM <table> WHERE <column> > $since [AND (<filter>)] ORDER BY <column> ASC
    LIMIT $limit+1`` and the honest ``count() … GROUP ALL`` over the same predicate; a held head group adds
    one more ``count()`` at that stamp, so its ``N`` describes the whole group. ``LIMIT`` rides a bound
    param (never interpolated).

    THE PREDICATE, stated once (R46 / RULING-17, finding #597): a leg reads the rows whose stamp is a
    ``datetime`` above the cursor. On 3.3.5, ``<column> > $since`` (``$since`` a datetime) EXCLUDES a stamp of
    type string, number, bool, null or duration — that row is outside every leg's rows AND its ``total`` —
    while an array, object, uuid or record stamp is admitted and refused loudly by :func:`required_datetime`
    (measured: servicer ``build66/r45/probe/order_probe.py``, datetime controls both sides). Every production
    write into these SCHEMAFULL ``datetime`` / ``option<datetime>`` columns is held to the type, so a
    non-datetime stamp is reachable ONLY through an admin retype of the column (store reference §1.4).
    KNOWN BOUND #597, pinned by ``test_sdk3_retirement_pins_66d::TestANonDatetimeStampIsOutsideEveryLeg``.
    Re-open triggers (any one): a migration that retypes a stamp column; a SCHEMALESS or ``TYPE any`` period
    on these tables; an import door writing untyped literals; ``option<datetime>`` found to admit NULL. The
    closing instrument named by the ruling is a once-per-boot integrity count in ``ensure_ready()``, not a
    per-call check here.

    Args:
        query: The ledger's single-statement seam (its ``_query``).
        as_rows: The ledger's narrowing of a ``SELECT`` result to dict rows.
        group_count: The ledger's narrowing of a ``count() … GROUP ALL`` result to an int.
        table: The table.
        column: The stamp column (an engine ``datetime``).
        projection: The ``SELECT`` projection; it must include ``column``.
        since: The exclusive cursor.
        limit: The page size (a positive int — the caller validates it).
        filter_fragment: An extra predicate ANDed into every statement (the message leg's read filter).
        filter_params: The fragment's bound params; their names must not collide with this module's.

    Returns:
        The leg's :class:`StampPage`.

    Raises:
        ValueError: ``filter_params`` reuses one of this module's parameter names.
        SurrealStoreError: A row's stamp is not a tz-aware datetime (:func:`required_datetime`'s refusal).
    """
    extra = dict(filter_params or {})
    clash = _RESERVED_PARAMS.intersection(extra)
    if clash:
        raise ValueError(f"filter params reuse the stamp-page parameter names {sorted(clash)}")
    where_extra = f" AND ({filter_fragment})" if filter_fragment else ""
    params: dict[str, Any] = {**extra, _SINCE_PARAM: since, _LIMIT_PARAM: limit + 1}
    rows = as_rows(
        await query(
            f"SELECT {projection} FROM {table} WHERE {column} > ${_SINCE_PARAM}{where_extra} "
            f"ORDER BY {column} ASC LIMIT ${_LIMIT_PARAM}",
            params,
        )
    )
    total = group_count(
        await query(
            f"SELECT count() FROM {table} WHERE {column} > ${_SINCE_PARAM}{where_extra} GROUP ALL", params
        )
    )

    def stamp_of(row: dict[str, Any]) -> datetime:
        # THE stamp check (R34): a corrupt stamp is refused with its row named, before any comparison.
        return required_datetime(row.get(column), table=table, row_id=row.get("id"), column=column)

    cut = cut_stamp_page(rows, limit=limit, since=since, stamp_of=stamp_of)
    held_group = None
    if cut.held_stamp is not None:
        group_params = {**extra, _GROUP_PARAM: cut.held_stamp}
        group_rows = group_count(
            await query(
                f"SELECT count() FROM {table} WHERE {column} = ${_GROUP_PARAM}{where_extra} GROUP ALL",
                group_params,
            )
        )
        held_group = HeldStampGroup(stamp=cut.held_stamp, rows=group_rows)
    return StampPage(rows=cut.rows, total=total, resume_at=cut.resume_at, held_group=held_group)
