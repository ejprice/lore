"""Contract — the rollup ``next cursor`` survives the SERVED-TEXT round trip (finding #590).

Packet 66 fix wave R43, item B1 (``sidecar66/RULING-14.md`` §B1; the cold audit's probe
``audit66/probe_rollup_cursor_test.py``, converted here into a pin). RED before the B1 build
commit that follows ``dabc671``; GREEN on that commit.

THE PROPERTY. ``lore_tasks action=rollup`` serves ``next cursor: <text>`` and documents it as
the EXCLUSIVE cursor to pass back as ``since``. ``TaskLedger.updated_since`` binds it as
``updated_at > $since``, which is exact only when the cursor carries the SAME precision as the
stored stamp: the engine stamps ``time::now()`` to the nanosecond. So the pin drives the path
every agent uses: rollup -> the served TEXT -> ``AppContext._parse_rollup_since`` -> rollup
again. Rendering the cursor at microsecond precision (``datetime.isoformat()``), or parsing it
back at microsecond precision (``datetime.fromisoformat`` silently truncates nine digits to
six), floors the boundary below the row it came from, and the next page re-serves that row.

WHY THE OLD PINS STAYED GREEN. ``test_task_ledger.py::TestUpdatedSince::test_boundary_is_exclusive``
re-binds the in-process ``PreciseDatetime`` (nanoseconds intact across CBOR). That leg is kept
here as the CONTROL, so a red in this file names the text codec, not the store.

FIXTURE CHOICES, each answering "what wrong build would still pass this?":
- The stamps are FORCED through admin DML (``<datetime>`` cast on the engine's own nine-digit
  text), never left to ``time::now()``: a clock tick that happened to land on ``nanosecond ==
  0`` would make a microsecond codec look exact. Each test re-reads the stamp and asserts the
  forced tail landed (a forcing that silently no-opped would leave the pin vacuous).
- The LATER row sits in the SAME microsecond as the cursor row (``…697518`` then ``…697900``).
  A build that "fixes" the re-serve by rounding the cursor UP (the retired +1 µs ceiling, or
  round-to-nearest on ``…697518`` -> ``…698``) excludes the cursor row but SKIPS the later row
  for ever; the second pin catches that direction, the first catches the floor direction.
- ``limit=1`` truncates the first page so the cursor is the FIRST row's stamp while a later
  row is still unserved (the next cursor of a truncated leg is its last served stamp).

Path driven: ``AppContext._rollup`` exactly as the ``lore_tasks`` dispatcher calls it
(``AppContext._rollup(self, since=since, limit=limit)``, tokenless), over LIVE ledgers on a
throwaway database (the ``test_rollup_extension._RollupCtx`` harness). Stated bound: the MCP
wire wrapper above the dispatcher is not driven; it forwards ``since`` as the same ``str``.

Tests hit spike-surreal ``ws://127.0.0.1:18000`` ONLY; ``:18500`` is NEVER touched.
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from typing import cast

import pytest_asyncio
from _surreal_harness import connect_admin, run, unique_database
from loremaster.server import AppContext
from loremaster.store.surreal_schema import TASK_TABLE
from test_rollup_extension import _RollupCtx

_CREATOR = "rollup-cursor-creator"
_OWNER = "rollup-cursor-owner"

# The cursor row's forced stamp and a LATER row inside the SAME microsecond. Engine text form
# (nine fraction digits, ``Z``) — the form ``time::now()`` stores.
_CURSOR_ROW_STAMP = "2031-05-06T07:08:09.186697518Z"
_CURSOR_ROW_TAIL_NS = 518
_SAME_MICROSECOND_LATER_STAMP = "2031-05-06T07:08:09.186697900Z"
_LATER_ROW_TAIL_NS = 900

_NEXT_CURSOR_LINE = re.compile(r"^next cursor: (?P<cursor>.+)$", re.MULTILINE)


class _CursorCtx(_RollupCtx):
    """The live rollup harness plus a forced-stamp writer and the dispatcher-shaped rollup call."""

    async def forced_task(self, subject: str, stamp_text: str, tail_ns: int) -> str:
        """Create + claim a task, then FORCE its ``updated_at`` to ``stamp_text`` via admin DML.

        Asserts the forced nanosecond tail is what the ledger now reads back, so a forcing
        that silently no-opped cannot leave a pin passing for a fixture reason.
        """
        task_id = await self.task_ledger.create_task(subject, "cursor fixture", created_by=_CREATOR)
        await self.task_ledger.claim_task(task_id, _OWNER)
        connection = await connect_admin(self._env)
        try:
            await run(
                connection,
                f"UPDATE type::record('{TASK_TABLE}', $id) SET updated_at = <datetime> $stamp",
                {"id": task_id, "stamp": stamp_text},
            )
        finally:
            await connection.close()
        stored = (await self.task_ledger.get_task(task_id)).updated_at
        assert stored is not None
        assert getattr(stored, "nanosecond", None) == tail_ns, (
            f"fixture did not land: {task_id} reads updated_at={stored!r}, "
            f"expected the forced tail {tail_ns} ns of {stamp_text}"
        )
        return task_id

    async def served_rollup(self, *, since: str | None, limit: int | None = None) -> str:
        """The rollup exactly as the ``lore_tasks`` dispatcher calls it (tokenless)."""
        return await AppContext._rollup(cast(AppContext, self), since=since, limit=limit)


def _served_cursor(rendered: str) -> str:
    """The ONE ``next cursor:`` value a rollup render served, as TEXT."""
    cursors = _NEXT_CURSOR_LINE.findall(rendered)
    assert len(cursors) == 1, f"expected exactly one 'next cursor:' line, got {cursors!r}"
    return str(cursors[0])


def _serves(rendered: str, task_id: str) -> bool:
    """Whether a rollup render lists ``task_id`` as a transitioned-task row."""
    return f"(id {task_id}, " in rendered


@pytest_asyncio.fixture()
async def cursor_ctx() -> AsyncIterator[_CursorCtx]:
    ctx = _CursorCtx(unique_database())
    await ctx.start()
    try:
        yield ctx
    finally:
        await ctx.stop()


class TestServedRollupCursorRoundTrip:
    """#590: the cursor an agent is SERVED, handed back as text, must not re-serve its own row."""

    async def test_served_cursor_text_does_not_reserve_its_own_row(self, cursor_ctx: _CursorCtx) -> None:
        task_id = await cursor_ctx.forced_task("cursor row", _CURSOR_ROW_STAMP, _CURSOR_ROW_TAIL_NS)
        first_page = await cursor_ctx.served_rollup(since=None)
        assert _serves(first_page, task_id), first_page
        cursor_text = _served_cursor(first_page)

        # The server's own `since` parser over the served text, bound straight into leg 1.
        parsed = AppContext._parse_rollup_since(cursor_text)
        window = await cursor_ctx.task_ledger.updated_since(parsed, limit=20)
        assert task_id not in {task.id for task in window.rows}, (
            f"served cursor {cursor_text!r} parses to {parsed!r}, which re-serves the row "
            f"stamped {_CURSOR_ROW_STAMP} it was read from"
        )

        # And end to end: the next page, requested with that text, does not list the row.
        second_page = await cursor_ctx.served_rollup(since=cursor_text)
        assert not _serves(second_page, task_id), (
            f"rollup since={cursor_text!r} re-served task {task_id} (stamped "
            f"{_CURSOR_ROW_STAMP}), the row that cursor was read from:\n{second_page}"
        )

    async def test_served_cursor_keeps_a_later_row_in_the_same_microsecond(
        self, cursor_ctx: _CursorCtx
    ) -> None:
        cursor_row = await cursor_ctx.forced_task("cursor row", _CURSOR_ROW_STAMP, _CURSOR_ROW_TAIL_NS)
        later_row = await cursor_ctx.forced_task(
            "later row, same microsecond", _SAME_MICROSECOND_LATER_STAMP, _LATER_ROW_TAIL_NS
        )
        first_page = await cursor_ctx.served_rollup(since=None, limit=1)
        assert _serves(first_page, cursor_row) and not _serves(first_page, later_row), first_page
        cursor_text = _served_cursor(first_page)

        second_page = await cursor_ctx.served_rollup(since=cursor_text)
        served = {
            "cursor row": _serves(second_page, cursor_row),
            "later row": _serves(second_page, later_row),
        }
        assert served == {"cursor row": False, "later row": True}, (
            f"rollup since={cursor_text!r}: the cursor row ({_CURSOR_ROW_STAMP}) must be "
            f"excluded and the later row ({_SAME_MICROSECOND_LATER_STAMP}) still served; "
            f"got {served}:\n{second_page}"
        )


class TestInProcessCursorControl:
    """CONTROL: the in-process bind (the pre-#590 pins' shape) is exact at both boundaries, so a
    red above is the served-text codec, never the store's comparison."""

    async def test_in_process_stamp_bind_is_exact_at_the_boundary(self, cursor_ctx: _CursorCtx) -> None:
        cursor_row = await cursor_ctx.forced_task("cursor row", _CURSOR_ROW_STAMP, _CURSOR_ROW_TAIL_NS)
        later_row = await cursor_ctx.forced_task(
            "later row, same microsecond", _SAME_MICROSECOND_LATER_STAMP, _LATER_ROW_TAIL_NS
        )
        stamp = (await cursor_ctx.task_ledger.get_task(cursor_row)).updated_at
        assert stamp is not None
        window = await cursor_ctx.task_ledger.updated_since(stamp, limit=20)
        assert {task.id for task in window.rows} == {later_row}
