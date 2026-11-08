"""The in-memory fakes' bridge to THE stamp-group paging rule (R44 / RULING-15, finding #591).

The three rollup legs' fakes (``_task_fakes.FakeTaskLedger.updated_since``,
``_finding_fakes.FakeFindingLedger.filed_since``, ``_message_fakes.FakeMessageLedger.
message_activity_since``) keep their OWN filter, sort and honest total over ``self.db`` (so a
fake can still fail a wrong build), but they do NOT re-implement the page-cut rule: they call
production's pure :func:`~loremaster.store.stamp_paging.cut_stamp_page`, exactly as that module's
docstring names ("a fake store calls :func:`cut_stamp_page`"). The one thing a store does that the
pure cut does not — counting the WHOLE held head group for :class:`~loremaster.store.stamp_paging.
HeldStampGroup` — is done here once, over the fake's already-filtered rows, with production's
:func:`~loremaster.store.stamp_paging.stamp_key` as the tie test.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime

from loremaster.store.stamp_paging import HeldStampGroup, cut_stamp_page, stamp_key


@dataclass(frozen=True)
class FakeStampPage[RowT]:
    """One fake leg's page: the fields every ``*ActivityWindow`` carries.

    Attributes:
        rows: The served rows (at most ``limit``; whole stamp groups unless held).
        total: The honest count of every matching row after ``since``.
        resume_at: The cut's exact resume stamp (last served stamp, or ``since``).
        held_group: The held head group (its stamp and WHOLE size), else ``None``.
    """

    rows: list[RowT]
    total: int
    resume_at: datetime
    held_group: HeldStampGroup | None


def fake_stamp_page[RowT](
    matching: Sequence[RowT], *, limit: int, since: datetime, stamp_of: Callable[[RowT], datetime]
) -> FakeStampPage[RowT]:
    """Page a fake leg's matching rows under production's stamp-group rule.

    Args:
        matching: EVERY row the leg's predicate admits (strictly after ``since``), stamp-ascending.
        limit: The page size (the caller has validated it is a positive int).
        since: The exclusive cursor.
        stamp_of: The row's stamp.

    Returns:
        The page: the cut's rows and ``resume_at``, ``total = len(matching)``, and — when the head
        group is wider than ``limit`` — a :class:`HeldStampGroup` naming the WHOLE group's size.
    """
    cut = cut_stamp_page(list(matching[: limit + 1]), limit=limit, since=since, stamp_of=stamp_of)
    held_group = None
    if cut.held_stamp is not None:
        held_key = stamp_key(cut.held_stamp)
        group_rows = sum(1 for row in matching if stamp_key(stamp_of(row)) == held_key)
        held_group = HeldStampGroup(stamp=cut.held_stamp, rows=group_rows)
    return FakeStampPage(
        rows=cut.rows, total=len(matching), resume_at=cut.resume_at, held_group=held_group
    )
