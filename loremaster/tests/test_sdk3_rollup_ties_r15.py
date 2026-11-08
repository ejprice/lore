"""Contract — rollup rows that share one stamp are never skipped when ``limit`` cuts the group (#591).

Packet 66 fix wave R43, ``sidecar66/RULING-15.md`` §2 (verdict (c)) and §3 (its riders, P1-P6). RED at
``9f3922f`` (the paging helper is not built); GREEN on the build that adds RULING-15's ONE paging helper
under the three ``*_since`` legs.

THE PROPERTY. Each rollup leg pages by an EXCLUSIVE instant (``stamp > $since``). That is exact only if a
page never ENDS inside a group of rows that share one stamp: the served cursor is the last served stamp,
so the unserved remainder of the group is ``== cursor``, never ``> cursor``, and it is skipped for ever
while the next page reads ``no ledger activity since …`` — a false clear (#591, measured by the B1 tie
probe). RULING-15's rule: read ``limit + 1``; a cut inside a group SHRINKS the page to the rows strictly
below the boundary stamp; a HEAD group wider than ``limit`` is served ``limit`` rows wide, the cursor is
HELD at ``since``, and the leg header NAMES the group (``H1_HELD``) with its remedy (raise ``limit``).
The MESSAGE leg never feeds the rollup cursor (RULING-15 §4 Q1, option (ii)): its held group and its
elided tail are NAMED as not covered by the next cursor (``H2_MESSAGE_HELD`` / ``H2_MESSAGE_ELISION``),
and its remedy is a larger ``limit`` on the SAME call.

THE SERVED TEXT lives ONCE, in the four module constants below (``H1_HELD`` / ``H2_MESSAGE_HELD`` /
``H2_MESSAGE_ELISION`` / ``H3_OTHER_LEGS_RESERVE``; the strings agreed with the builder 2026-11-08), so
the wording is swapped in one place. ``{stamp}`` is the served nine-digit form
(``store._txn.served_instant_text``).

FIXTURE CHOICES, each answering "what wrong build would still pass this?":
- Every stamp is FORCED through admin DML (``SET <col> = <datetime> $stamp``, the B1 pin's idiom) and
  RE-READ through the ledger's own read: a forcing that silently no-opped would leave distinct
  ``time::now()`` / ``datetime.now(UTC)`` stamps, no tie, and every pin vacuously green.
- Tie groups are THREE rows wide under ``limit=1`` (N > limit, the held branch) and TWO wide under
  ``limit=2`` straddling the cut (P2, the shrink branch). The fake-store tie pins hold 2 tied rows under
  ``limit=20``, where neither branch is reachable (FIXTURES MUST DISCRIMINATE, axis 3: arithmetic
  alignment) — that is why they never saw #591.
- All three stamp-paged legs are pinned (tasks ``updated_at``, findings ``created_at``, messages
  ``created_at``): a helper wired under one leg while another keeps a private copy reddens here.
- P5 puts the served finding row ABOVE the held task group (``S_f > S``), so a build that "holds" by
  taking the max over every served row (or the min over truncated legs' last row) is visible.

Path driven: ``AppContext._rollup`` exactly as the ``lore_tasks`` dispatcher calls it, over LIVE ledgers on
a throwaway database (``test_rollup_extension._RollupCtx``; its stub admin Subject serves the governed
message leg). Stated bounds: the MCP wire wrapper above the dispatcher is not driven; the message leg's
read FILTER for a non-admin Subject is the read-governance contract's, not this file's.

Tests hit spike-surreal ``ws://127.0.0.1:18000`` ONLY; ``:18500`` is NEVER touched.
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator, Sequence
from typing import Any

import pytest_asyncio
from _governed_contract import PRINCIPAL_ALICE, PRINCIPAL_BOB, member, seed_message_legacy
from _surreal_harness import connect_admin, run, unique_database
from loremaster.agents import Agent
from loremaster.store._txn import parse_served_instant, served_instant_text
from loremaster.store.surreal_schema import FINDING_TABLE, MESSAGE_TABLE, TASK_TABLE
from surrealdb import RecordID
from test_rollup_extension import _SESSION, _RollupCtx

# --- THE SERVED TEXT, pinned ONCE (RULING-15 §3.3; swap the agreed strings here) -------------------

#: A task / finding head group wider than ``limit``: ``limit`` of its rows served, the cursor HELD.
H1_HELD = (
    "{label} (showing {shown} of {total} — {n} rows share the stamp {stamp}; limit {limit} cannot page"
    " past them, so this cursor does not advance — re-call with limit ≥ {n}):"
)
#: A message head group wider than ``limit``: the message leg never holds the cursor, so it says so.
H2_MESSAGE_HELD = (
    "messages activity (showing {shown} of {total} — {n} messages share the stamp {stamp}; limit {limit}"
    " cannot page past them, and the next cursor does not cover them — raise limit to ≥ {n} on THIS call):"
)
#: The truncated MESSAGE leg's header: its elided tail is not covered by the next cursor (§4 Q1).
H2_MESSAGE_ELISION = (
    "messages activity (showing {shown} of {total} — the elided messages are not covered by the next"
    " cursor; raise limit on THIS call to see them):"
)
#: A truncated task / finding leg's header: resume at the elision point; other legs re-serve (§4 Q2).
H3_OTHER_LEGS_RESERVE = (
    "{label} (showing {shown} of {total} — the next cursor resumes at the elision point, and the other"
    " legs re-serve their rows above it; re-call rollup with it, or raise limit):"
)

# --- fixture constants -----------------------------------------------------------------------------

_CREATOR = "rollup-ties-creator"
_OWNER = "rollup-ties-owner"
_TASK_LABEL = "tasks transitioned"
_FINDING_LABEL = "findings filed"

#: The caller's starting cursor, BELOW every forced stamp (and above every ``time::now()`` / Python-now
#: stamp the fixtures' own writes minted, which are all in 2026).
_SINCE = "2031-01-01T00:00:00.000000001Z"
#: The ONE stamp a tie group shares (a nine-digit engine text, so a microsecond codec cannot fake a tie).
_TIE_STAMP = "2031-05-06T07:08:09.186697518Z"
#: P5's finding row, strictly ABOVE the held task group.
_ABOVE_TIE_STAMP = "2031-05-06T07:08:10.000000007Z"
#: P2's three distinct stamps (S1 < S2 < S3); b and c share S2.
_SHRINK_S1 = "2031-05-06T07:08:09.100000001Z"
_SHRINK_S2 = "2031-05-06T07:08:09.200000002Z"
_SHRINK_S3 = "2031-05-06T07:08:09.300000003Z"
#: The h2 fixture's three distinct message stamps.
_DISTINCT_MESSAGE_STAMPS = (
    "2031-05-06T07:08:09.400000004Z",
    "2031-05-06T07:08:09.500000005Z",
    "2031-05-06T07:08:09.600000006Z",
)

_TIE_WIDTH = 3
_HELD_LIMIT = 1
_DEFAULT_PAGE_LIMIT = 20

_NEXT_CURSOR_LINE = re.compile(r"^next cursor: (?P<cursor>.+)$", re.MULTILINE)


def _served(text: str) -> str:
    """``text`` in the served nine-digit form (THE cursor codec, both ends)."""
    return served_instant_text(parse_served_instant(text))


def _held_line(label: str, shown: int, total: int, width: int, stamp_text: str, limit: int) -> str:
    return H1_HELD.format(
        label=label, shown=shown, total=total, n=width, stamp=_served(stamp_text), limit=limit
    )


def _message_held_line(shown: int, total: int, width: int, stamp_text: str, limit: int) -> str:
    return H2_MESSAGE_HELD.format(shown=shown, total=total, n=width, stamp=_served(stamp_text), limit=limit)


class _TieCtx(_RollupCtx):
    """The live rollup harness plus forced-stamp writers for all three stamp-paged legs."""

    async def _force(self, statement: str, params: dict[str, object]) -> None:
        connection = await connect_admin(self._env)
        try:
            await run(connection, statement, params)
        finally:
            await connection.close()

    async def forced_task(self, subject: str, stamp_text: str) -> str:
        """Create + claim a task, FORCE its ``updated_at`` to ``stamp_text``, prove the forcing landed."""
        task_id = await self.task_ledger.create_task(subject, "tie fixture", created_by=_CREATOR)
        await self.task_ledger.claim_task(task_id, _OWNER)
        await self._force(
            f"UPDATE type::record('{TASK_TABLE}', $id) SET updated_at = <datetime> $stamp",
            {"id": task_id, "stamp": stamp_text},
        )
        stored = (await self.task_ledger.get_task(task_id)).updated_at
        assert stored is not None and served_instant_text(stored) == _served(stamp_text), (
            f"fixture did not land: task {task_id} reads updated_at={stored!r}, forced {stamp_text}"
        )
        return task_id

    async def forced_finding(self, subject: str, stamp_text: str) -> int:
        """File a finding, FORCE its ``created_at`` to ``stamp_text``, prove it landed; returns its number."""
        result = await self.finding_ledger.report(
            subject, "tie fixture", area="rollup", category="bug", created_by=_CREATOR
        )
        await self._force(
            f"UPDATE type::record('{FINDING_TABLE}', $id) SET created_at = <datetime> $stamp",
            {"id": result.id, "stamp": stamp_text},
        )
        stored = (await self.finding_ledger.get(result.id)).created_at
        assert served_instant_text(stored) == _served(stamp_text), (
            f"fixture did not land: finding #{result.number} reads created_at={stored!r}, forced {stamp_text}"
        )
        return result.number

    async def forced_messages(self, stamps: Sequence[str]) -> list[int]:
        """Send one message per stamp, FORCE each ``created_at``, prove every forcing landed; returns seqs."""
        lead = await self.register("ties-lead")
        worker = await self.register("ties-worker")
        seqs = [await self._sent_seq(lead, worker, index) for index in range(len(stamps))]
        for seq, stamp_text in zip(seqs, stamps, strict=True):
            await self._force(
                f"UPDATE {MESSAGE_TABLE} SET created_at = <datetime> $stamp WHERE seq = $seq",
                {"seq": seq, "stamp": stamp_text},
            )
        window = await self.message_ledger.message_activity_since(
            parse_served_instant(_SINCE), limit=_DEFAULT_PAGE_LIMIT
        )
        stored = {message.seq: served_instant_text(message.created_at) for message in window.rows}
        assert stored == {seq: _served(text) for seq, text in zip(seqs, stamps, strict=True)}, (
            f"fixture did not land: messages read {stored!r}, forced {list(zip(seqs, stamps, strict=True))!r}"
        )
        return seqs

    async def _sent_seq(self, lead: Agent, worker: Agent, index: int) -> int:
        result = await self.message_ledger.send(
            sender=lead,
            session=_SESSION,
            body=f"tie fixture message {index}",
            grade="signal",
            recipients=[worker],
            thread=f"ties-thread-{index}",
        )
        return result.message.seq

    async def served_rollup(self, *, since: str, limit: int | None) -> str:
        """The rollup as the ``lore_tasks`` dispatcher calls it, WITH a capability (governed message leg)."""
        return await self.rollup(since=since, limit=limit)


def _served_cursor(rendered: str) -> str:
    """The ONE ``next cursor:`` value a rollup render served, as TEXT."""
    cursors = _NEXT_CURSOR_LINE.findall(rendered)
    assert len(cursors) == 1, f"expected exactly one 'next cursor:' line, got {cursors!r}"
    return str(cursors[0])


def _task_hits(rendered: str, task_id: str) -> int:
    return rendered.count(f"(id {task_id}, ")


def _finding_hits(rendered: str, number: int) -> int:
    return sum(1 for line in rendered.splitlines() if line.startswith(f"- [#{number} "))


def _message_hits(rendered: str, seq: int) -> int:
    return sum(1 for line in rendered.splitlines() if line.startswith(f"- #{seq} "))


def _idle_text(stamp_text: str) -> str:
    return f"no ledger activity since {_served(stamp_text)}"


@pytest_asyncio.fixture()
async def tie_ctx() -> AsyncIterator[_TieCtx]:
    ctx = _TieCtx(unique_database())
    await ctx.start()
    try:
        yield ctx
    finally:
        await ctx.stop()


class TestHeldTaskGroup:
    """P1 (#591 itself): a task group wider than ``limit`` holds the cursor and is named, never skipped."""

    async def test_task_group_wider_than_limit_is_held_named_then_served_whole(
        self, tie_ctx: _TieCtx
    ) -> None:
        tied = [await tie_ctx.forced_task(f"tied task {index}", _TIE_STAMP) for index in range(_TIE_WIDTH)]

        held_page = await tie_ctx.served_rollup(since=_SINCE, limit=_HELD_LIMIT)
        held_line = _held_line(_TASK_LABEL, 1, _TIE_WIDTH, _TIE_WIDTH, _TIE_STAMP, _HELD_LIMIT)
        assert held_line in held_page.splitlines(), (
            f"a {_TIE_WIDTH}-row task group at one stamp under limit={_HELD_LIMIT} must be NAMED "
            f"(H1_HELD); the page served instead:\n{held_page}"
        )
        assert H3_OTHER_LEGS_RESERVE.format(label=_TASK_LABEL, shown=1, total=_TIE_WIDTH) not in held_page, (
            f"a HELD leg must not also claim the cursor 'resumes at the elision point':\n{held_page}"
        )
        assert sum(_task_hits(held_page, task_id) for task_id in tied) == _HELD_LIMIT, held_page
        assert _served_cursor(held_page) == _served(_SINCE), (
            f"a held group must NOT advance the cursor past {_SINCE} (the unserved tied rows sit AT the "
            f"group stamp and an exclusive cursor there skips them for ever):\n{held_page}"
        )

        whole_page = await tie_ctx.served_rollup(since=_served_cursor(held_page), limit=_TIE_WIDTH)
        assert [_task_hits(whole_page, task_id) for task_id in tied] == [1] * _TIE_WIDTH, whole_page
        assert f"{_TASK_LABEL} ({_TIE_WIDTH}):" in whole_page.splitlines(), whole_page
        assert _served_cursor(whole_page) == _served(_TIE_STAMP), whole_page

        idle_page = await tie_ctx.served_rollup(since=_served_cursor(whole_page), limit=None)
        assert _idle_text(_TIE_STAMP) in idle_page.splitlines(), idle_page
        truth = await tie_ctx.task_ledger.updated_since(
            parse_served_instant(_TIE_STAMP), limit=_DEFAULT_PAGE_LIMIT
        )
        assert truth.total == 0, f"the idle header must now be TRUE; the store still holds {truth.rows!r}"

        # Walk receipt: every tied row reached; after the held page, each served exactly once.
        walked = [held_page, whole_page, idle_page]
        assert {task_id for task_id in tied if any(_task_hits(page, task_id) for page in walked)} == set(tied)
        assert [sum(_task_hits(page, task_id) for page in walked[1:]) for task_id in tied] == [1] * _TIE_WIDTH

    async def test_held_width_names_the_group_not_the_leg_total(self, tie_ctx: _TieCtx) -> None:
        """A row ABOVE the held group makes the leg total 4 while the group is 3 wide: H1 names 3."""
        for index in range(_TIE_WIDTH):
            await tie_ctx.forced_task(f"tied task {index}", _TIE_STAMP)
        above = await tie_ctx.forced_task("task above the group", _ABOVE_TIE_STAMP)

        held_page = await tie_ctx.served_rollup(since=_SINCE, limit=_HELD_LIMIT)
        total = _TIE_WIDTH + 1
        held_line = _held_line(_TASK_LABEL, 1, total, _TIE_WIDTH, _TIE_STAMP, _HELD_LIMIT)
        assert held_line in held_page.splitlines(), held_page
        assert _held_line(_TASK_LABEL, 1, total, total, _TIE_STAMP, _HELD_LIMIT) not in held_page, held_page
        assert _task_hits(held_page, above) == 0, held_page
        assert _served_cursor(held_page) == _served(_SINCE), held_page


class TestShrinkAtTheCut:
    """P2: a cut inside a group SHRINKS the page to the whole groups below it.

    Nothing skipped, and no page larger than ``limit``."""

    async def test_page_never_ends_inside_a_stamp_group(self, tie_ctx: _TieCtx) -> None:
        a_id = await tie_ctx.forced_task("a", _SHRINK_S1)
        b_id = await tie_ctx.forced_task("b", _SHRINK_S2)
        c_id = await tie_ctx.forced_task("c", _SHRINK_S2)
        d_id = await tie_ctx.forced_task("d", _SHRINK_S3)
        every = {a_id, b_id, c_id, d_id}
        limit = 2

        pages: list[str] = []
        since = _SINCE
        for _ in range(len(every) + 1):
            page = await tie_ctx.served_rollup(since=since, limit=limit)
            pages.append(page)
            since = _served_cursor(page)
        served_sets = [{task_id for task_id in every if _task_hits(page, task_id)} for page in pages]
        cursors = [_served_cursor(page) for page in pages]

        assert served_sets[:3] == [{a_id}, {b_id, c_id}, {d_id}], (
            f"pages must be {{a}}, {{b, c}}, {{d}} (b and c share {_SHRINK_S2}); got "
            f"{served_sets!r}\n" + "\n----\n".join(pages)
        )
        assert cursors[:3] == [_served(_SHRINK_S1), _served(_SHRINK_S2), _served(_SHRINK_S3)], cursors
        assert H3_OTHER_LEGS_RESERVE.format(label=_TASK_LABEL, shown=1, total=4) in pages[0].splitlines(), (
            f"the shrunk first page is a truncated leg and must say so (H3):\n{pages[0]}"
        )
        assert _idle_text(_SHRINK_S3) in pages[3].splitlines(), pages[3]
        assert all(sum(_task_hits(page, task_id) for task_id in every) <= limit for page in pages), pages
        # Set equality both ways over the walk: every row served, and served exactly once.
        assert [sum(_task_hits(page, task_id) for page in pages) for task_id in (a_id, b_id, c_id, d_id)] == [
            1,
            1,
            1,
            1,
        ], pages


class TestHeldFindingGroup:
    """P3: P1's shape on ``finding.created_at`` (Python-µs stamped: a same-µs ``report`` burst ties)."""

    async def test_finding_group_wider_than_limit_is_held_named_then_served_whole(
        self, tie_ctx: _TieCtx
    ) -> None:
        tied = [
            await tie_ctx.forced_finding(f"tied finding {index}", _TIE_STAMP) for index in range(_TIE_WIDTH)
        ]

        held_page = await tie_ctx.served_rollup(since=_SINCE, limit=_HELD_LIMIT)
        held_line = _held_line(_FINDING_LABEL, 1, _TIE_WIDTH, _TIE_WIDTH, _TIE_STAMP, _HELD_LIMIT)
        assert held_line in held_page.splitlines(), held_page
        assert (
            H3_OTHER_LEGS_RESERVE.format(label=_FINDING_LABEL, shown=1, total=_TIE_WIDTH) not in held_page
        ), held_page
        assert sum(_finding_hits(held_page, number) for number in tied) == _HELD_LIMIT, held_page
        assert _served_cursor(held_page) == _served(_SINCE), held_page

        whole_page = await tie_ctx.served_rollup(since=_served_cursor(held_page), limit=_TIE_WIDTH)
        assert [_finding_hits(whole_page, number) for number in tied] == [1] * _TIE_WIDTH, whole_page
        assert f"{_FINDING_LABEL} ({_TIE_WIDTH}):" in whole_page.splitlines(), whole_page
        assert _served_cursor(whole_page) == _served(_TIE_STAMP), whole_page

        idle_page = await tie_ctx.served_rollup(since=_served_cursor(whole_page), limit=None)
        assert _idle_text(_TIE_STAMP) in idle_page.splitlines(), idle_page
        truth = await tie_ctx.finding_ledger.filed_since(
            parse_served_instant(_TIE_STAMP), limit=_DEFAULT_PAGE_LIMIT
        )
        assert truth.total == 0, f"the idle header must now be TRUE; the store still holds {truth.rows!r}"

        walked = [held_page, whole_page, idle_page]
        assert {number for number in tied if any(_finding_hits(page, number) for page in walked)} == set(tied)
        assert [sum(_finding_hits(page, number) for page in walked[1:]) for number in tied] == [
            1
        ] * _TIE_WIDTH


class TestHeldMessageGroup:
    """P4: P1's shape on the GOVERNED message leg (``message.created_at``, Python-µs stamped).

    The message leg never feeds the rollup cursor (§4 Q1 (ii)), so its held group is named by
    ``H2_MESSAGE_HELD`` and its remedy is a larger ``limit`` on the SAME cursor."""

    async def test_message_group_wider_than_limit_is_held_named_then_served_whole(
        self, tie_ctx: _TieCtx
    ) -> None:
        tied = await tie_ctx.forced_messages([_TIE_STAMP] * _TIE_WIDTH)

        held_page = await tie_ctx.served_rollup(since=_SINCE, limit=_HELD_LIMIT)
        held_line = _message_held_line(1, _TIE_WIDTH, _TIE_WIDTH, _TIE_STAMP, _HELD_LIMIT)
        assert held_line in held_page.splitlines(), held_page
        assert H2_MESSAGE_ELISION.format(shown=1, total=_TIE_WIDTH) not in held_page.splitlines(), held_page
        assert sum(_message_hits(held_page, seq) for seq in tied) == _HELD_LIMIT, held_page
        assert _served_cursor(held_page) == _served(_SINCE), held_page

        # The remedy H2_MESSAGE_HELD names: raise limit on the SAME cursor — the whole group, each row once.
        whole_page = await tie_ctx.served_rollup(since=_served_cursor(held_page), limit=_TIE_WIDTH)
        assert [_message_hits(whole_page, seq) for seq in tied] == [1] * _TIE_WIDTH, whole_page
        assert f"messages activity ({_TIE_WIDTH}):" in whole_page.splitlines(), whole_page
        assert not any("share the stamp" in line for line in whole_page.splitlines()), whole_page

        # Every tied message reached over the walk.
        walked = [held_page, whole_page]
        assert {seq for seq in tied if any(_message_hits(page, seq) for page in walked)} == set(tied)

    async def test_held_message_group_is_named_as_uncovered_beside_a_served_task(
        self, tie_ctx: _TieCtx
    ) -> None:
        """``H2_MESSAGE_HELD``'s own claim ("the next cursor does not cover them") is TRUE: a task row ABOVE
        the held message group moves the cursor past it (the message leg never holds the cursor), and the
        page says so — the H1 text ("this cursor does not advance") there would be a false claim."""
        tied = await tie_ctx.forced_messages([_TIE_STAMP] * _TIE_WIDTH)
        task_id = await tie_ctx.forced_task("task above the held messages", _ABOVE_TIE_STAMP)

        held_page = await tie_ctx.served_rollup(since=_SINCE, limit=_HELD_LIMIT)
        held_line = _message_held_line(1, _TIE_WIDTH, _TIE_WIDTH, _TIE_STAMP, _HELD_LIMIT)
        assert held_line in held_page.splitlines(), held_page
        assert "this cursor does not advance" not in held_page, held_page
        assert _task_hits(held_page, task_id) == 1, held_page
        assert _served_cursor(held_page) == _served(_ABOVE_TIE_STAMP), (
            f"the message leg must not hold the rollup cursor (§4 Q1 (ii)); the task leg's served row at "
            f"{_ABOVE_TIE_STAMP} sets it:\n{held_page}"
        )
        # ... and exactly as named: the next cursor does not reach the tied messages.
        next_page = await tie_ctx.served_rollup(since=_served_cursor(held_page), limit=_TIE_WIDTH)
        assert [_message_hits(next_page, seq) for seq in tied] == [0] * _TIE_WIDTH, next_page
        # The named remedy — raise limit on THIS call (the held page's own cursor) — serves the whole group.
        remedy = await tie_ctx.served_rollup(since=_SINCE, limit=_TIE_WIDTH)
        assert [_message_hits(remedy, seq) for seq in tied] == [1] * _TIE_WIDTH, remedy

    async def test_truncated_message_leg_names_that_the_cursor_does_not_cover_its_tail(
        self, tie_ctx: _TieCtx
    ) -> None:
        seqs = await tie_ctx.forced_messages(_DISTINCT_MESSAGE_STAMPS)

        page = await tie_ctx.served_rollup(since=_SINCE, limit=_HELD_LIMIT)
        assert H2_MESSAGE_ELISION.format(shown=1, total=len(seqs)) in page.splitlines(), page
        assert [_message_hits(page, seq) for seq in seqs] == [1, 0, 0], page
        # H2's own claim, made true: the message leg does not move the cursor (no task/finding row here).
        assert _served_cursor(page) == _served(_SINCE), page


class _MemberTieCtx(_TieCtx):
    """The tie harness with a MEMBER Subject (alice), so the message leg's read filter is live."""

    async def _resolve_subject(self, capability: str | None) -> Any:
        _ = capability
        return member(PRINCIPAL_ALICE, "ag_a1")

    async def seeded_messages(self, scopes: Sequence[tuple[int, dict[str, Any]]], stamp_text: str) -> None:
        """Raw-seed one message per (seq, governed columns), FORCE every ``created_at`` to one stamp."""
        sender = await self.register("ties-governed-lead")
        connection = await connect_admin(self._env)
        try:
            for seq, governed_columns in scopes:
                await seed_message_legacy(
                    connection, sender_id=sender.id, session=_SESSION, seq=seq, **governed_columns
                )
                await run(
                    connection,
                    f"UPDATE {MESSAGE_TABLE} SET created_at = <datetime> $stamp WHERE seq = $seq",
                    {"seq": seq, "stamp": stamp_text},
                )
        finally:
            await connection.close()


@pytest_asyncio.fixture()
async def member_tie_ctx() -> AsyncIterator[_MemberTieCtx]:
    ctx = _MemberTieCtx(unique_database())
    await ctx.start()
    try:
        yield ctx
    finally:
        await ctx.stop()


class TestHeldGovernedMessageGroup:
    """The held group's WIDTH is counted over the caller-VISIBLE rows: a width over the whole table
    names, in ``H2_MESSAGE_HELD``, a message the caller may not know exists (the §9.4 existence leak,
    in a new door)."""

    async def test_held_width_counts_only_the_callers_visible_group(
        self, member_tie_ctx: _MemberTieCtx
    ) -> None:
        visible = [901, 902]
        invisible = 903
        await member_tie_ctx.seeded_messages(
            [
                (visible[0], {"scope": "server"}),
                (visible[1], {"scope": "server"}),
                (
                    invisible,
                    {"scope": "principal-private", "owner_principal": RecordID("principal", PRINCIPAL_BOB)},
                ),
            ],
            _TIE_STAMP,
        )
        since = parse_served_instant(_SINCE)
        unfiltered = await member_tie_ctx.message_ledger.message_activity_since(
            since, limit=_DEFAULT_PAGE_LIMIT
        )
        assert {(message.seq, served_instant_text(message.created_at)) for message in unfiltered.rows} == {
            (seq, _served(_TIE_STAMP)) for seq in [*visible, invisible]
        }, f"fixture did not land: {unfiltered.rows!r}"
        # CONTROL: the member filter really hides the foreign row (else the pin below is vacuous).
        subject = await member_tie_ctx._resolve_subject(None)
        filtered = await member_tie_ctx.message_ledger.message_activity_since(
            since, limit=_DEFAULT_PAGE_LIMIT, subject=subject
        )
        assert sorted(message.seq for message in filtered.rows) == visible, filtered.rows

        held_page = await member_tie_ctx.served_rollup(since=_SINCE, limit=_HELD_LIMIT)
        held_line = _message_held_line(1, len(visible), len(visible), _TIE_STAMP, _HELD_LIMIT)
        assert held_line in held_page.splitlines(), held_page
        assert f"{len(visible) + 1} messages share the stamp" not in held_page, (
            f"the held header counted the invisible message into the group width:\n{held_page}"
        )
        assert _message_hits(held_page, invisible) == 0, held_page
        assert _served_cursor(held_page) == _served(_SINCE), held_page

        whole_page = await member_tie_ctx.served_rollup(since=_SINCE, limit=len(visible))
        assert [_message_hits(whole_page, seq) for seq in [*visible, invisible]] == [1, 1, 0], whole_page
        assert f"messages activity ({len(visible)}):" in whole_page.splitlines(), whole_page


class TestCrossLegHold:
    """P5: a held task group holds the WHOLE cursor.

    The finding leg's served row is then re-served (at-least-once)."""

    async def test_held_task_group_holds_the_cursor_and_the_finding_row_is_reserved(
        self, tie_ctx: _TieCtx
    ) -> None:
        tied = [await tie_ctx.forced_task(f"tied task {index}", _TIE_STAMP) for index in range(_TIE_WIDTH)]
        number = await tie_ctx.forced_finding("finding above the held group", _ABOVE_TIE_STAMP)

        held_page = await tie_ctx.served_rollup(since=_SINCE, limit=_HELD_LIMIT)
        held_text = _held_line(_TASK_LABEL, 1, _TIE_WIDTH, _TIE_WIDTH, _TIE_STAMP, _HELD_LIMIT)
        assert held_text in held_page.splitlines(), held_page
        assert held_page.index(held_text) < held_page.index(_FINDING_LABEL), (
            f"the held header belongs to the TASK leg:\n{held_page}"
        )
        assert _finding_hits(held_page, number) == 1, held_page
        assert _served_cursor(held_page) == _served(_SINCE), (
            f"a held task group must hold the WHOLE cursor — the finding row at {_ABOVE_TIE_STAMP} must not "
            f"carry it past the unserved tied tasks at {_TIE_STAMP}:\n{held_page}"
        )

        again = await tie_ctx.served_rollup(since=_served_cursor(held_page), limit=_HELD_LIMIT)
        assert _finding_hits(again, number) == 1, (
            f"the finding row must be RE-SERVED (at-least-once):\n{again}"
        )
        assert _served_cursor(again) == _served(_SINCE), again

        drained = await tie_ctx.served_rollup(since=_served_cursor(again), limit=_TIE_WIDTH)
        assert [_task_hits(drained, task_id) for task_id in tied] == [1] * _TIE_WIDTH, drained
        assert _finding_hits(drained, number) == 1, drained
        assert _served_cursor(drained) == _served(_ABOVE_TIE_STAMP), drained
